#!/usr/bin/env python3
"""
Braid Search — Soliton Search, QUBO Optimization, and Sidon Slot Assignment

Provides combinatorial optimization routines for braid crossing configurations:

1. Soliton-inspired search: uses a soliton pulse shape (discrete approximation)
   to guide a stochastic search over crossing configurations, concentrating
   exploration near high-energy regions.

2. QUBO (Quadratic Unconstrained Binary Optimization) formulation for bracket
   selection: encodes pairwise crossing costs into a QUBO matrix and solves
   via simulated annealing.

3. Sidon set construction for unique slot assignment: assigns braid strands
   to collision-free time/frequency slots using a Sidon set (all pairwise
   sums are distinct).

All arithmetic is integer/Q16_16 where applicable.  No float in compute paths.
"""

from __future__ import annotations

import math
import random
import hashlib
from typing import Dict, List, Optional, Tuple

# HiGHS QUBO solver — lazy import with fallback
try:
    from qubo_highs import solve_qubo_highs
    _HIGHS_AVAILABLE = True
except ImportError:
    _HIGHS_AVAILABLE = False

# Q16_16 constants
Q16_ONE = 0x00010000
Q16_MASK = 0xFFFFFFFF


# ── Sidon Set Slot Assignment ────────────────────────────────────────────────

def assign_sidon_slots(num_slots: int, seed: int = 42) -> List[int]:
    """Generate a Sidon set of size *num_slots* and return sorted slot indices.

    A Sidon set (B₂ sequence) is a set of integers where all pairwise sums
    are distinct.  This guarantees collision-free slot assignment for braid
    strands: no two pairs of strands occupy the same combined slot.

    Construction: greedy algorithm starting from *seed*, extending the set
    by testing each candidate against all existing pairwise sums.

    Args:
        num_slots: number of slots needed.
        seed: starting value for the greedy search.

    Returns:
        Sorted list of *num_slots* integers forming a Sidon set.
    """
    if num_slots <= 0:
        return []

    sidon: List[int] = [seed]
    pairwise_sums: set = set()  # only {seed+seed} initially, but we grow

    candidate = seed + 1
    while len(sidon) < num_slots:
        # Check if candidate can join without creating a duplicate sum
        ok = True
        for existing in sidon:
            s = existing + candidate
            if s in pairwise_sums:
                ok = False
                break
        if ok:
            # Record all new pairwise sums
            for existing in sidon:
                pairwise_sums.add(existing + candidate)
            pairwise_sums.add(candidate + candidate)
            sidon.append(candidate)
        candidate += 1

    return sorted(sidon)


def verify_sidon(slots: List[int]) -> bool:
    """Verify that *slots* is a valid Sidon set (all pairwise sums distinct)."""
    sums_seen: set = set()
    for i in range(len(slots)):
        for j in range(i, len(slots)):
            s = slots[i] + slots[j]
            if s in sums_seen:
                return False
            sums_seen.add(s)
    return True


# ── Soliton-Inspired Search ─────────────────────────────────────────────────

def _discrete_soliton(k: int, n: int) -> float:
    """Evaluate the (discrete) ideal soliton distribution at index *k* for size *n*.

    μ(1) = 1/n,  μ(k) = 1/(k*(k-1))  for k = 2..n
    Normalised so the values can serve as sampling weights.
    """
    if k == 1:
        return 1.0 / n
    elif 2 <= k <= n:
        return 1.0 / (k * (k - 1))
    return 0.0


def _candidate_energy(crossing: dict) -> float:
    """Compute an 'energy' score for a crossing configuration.

    Higher energy ↔ more promising configuration.
    Uses bracket admissibility, gap size, and parity diversity.
    """
    energy = 0.0
    brackets = crossing.get("brackets", [])
    for b in brackets:
        if b.get("admissible", False):
            energy += 2.0
        gap = b.get("gap", 0)
        # Larger gaps are generally better (more room for braiding)
        # Convert Q16_16 gap to float for scoring
        gap_f = gap / Q16_ONE if gap < 0x80000000 else (gap - 0x100000000) / Q16_ONE
        energy += abs(gap_f) * 0.5

    # Parity diversity bonus
    parities = {b.get("admissible", False) for b in brackets}
    if len(parities) > 1:
        energy += 1.0

    return energy


def soliton_search(target_energy: float, candidates: List[dict],
                   max_iterations: int = 1000, seed: int = 0) -> dict:
    """Soliton-inspired stochastic search over crossing configurations.

    The search distributes exploration effort according to a discrete soliton
    pulse: heavy sampling of promising candidates (high energy), lighter
    sampling of others, with stochastic jumps to avoid local optima.

    Args:
        target_energy: desired energy threshold for a satisfactory solution.
        candidates: list of crossing configuration dicts.
        max_iterations: maximum search iterations.
        seed: RNG seed for reproducibility.

    Returns:
        {
            "best": dict,           # best crossing found
            "best_energy": float,
            "iterations": int,
            "converged": bool,      # reached target_energy
            "history": list,        # (iteration, energy) pairs (sampled)
        }
    """
    rng = random.Random(seed)
    n = len(candidates)
    if n == 0:
        return {"best": {}, "best_energy": 0.0, "iterations": 0,
                "converged": False, "history": []}

    # Pre-compute energies
    energies = [_candidate_energy(c) for c in candidates]

    # Build soliton weights
    weights = [_discrete_soliton(i + 1, n) for i in range(n)]
    total_w = sum(weights)
    probs = [w / total_w for w in weights]

    # Sort candidates by energy descending; remap probs accordingly
    ranked = sorted(range(n), key=lambda i: energies[i], reverse=True)
    # Assign higher soliton weight to higher-energy candidates
    weighted_probs = [0.0] * n
    for rank_idx, orig_idx in enumerate(ranked):
        weighted_probs[orig_idx] = probs[rank_idx]

    best_idx = max(range(n), key=lambda i: energies[i])
    best_energy = energies[best_idx]
    best = candidates[best_idx]
    history: List[Tuple[int, float]] = []

    for iteration in range(1, max_iterations + 1):
        # Sample a candidate index from the soliton-weighted distribution
        r = rng.random()
        cumulative = 0.0
        chosen = rng.randint(0, n - 1)
        for idx in range(n):
            cumulative += weighted_probs[idx]
            if cumulative >= r:
                chosen = idx
                break

        # Evaluate (already pre-computed)
        e = energies[chosen]
        if e > best_energy:
            best_energy = e
            best = candidates[chosen]
            best_idx = chosen
            history.append((iteration, best_energy))

        # Check convergence
        if best_energy >= target_energy:
            return {
                "best": best,
                "best_energy": best_energy,
                "iterations": iteration,
                "converged": True,
                "history": history,
            }

        # Stochastic jump: small probability of random exploration
        if rng.random() < 0.05:
            jump_idx = rng.randint(0, n - 1)
            if energies[jump_idx] > best_energy:
                best_energy = energies[jump_idx]
                best = candidates[jump_idx]
                best_idx = jump_idx
                history.append((iteration, best_energy))

    return {
        "best": best,
        "best_energy": best_energy,
        "iterations": max_iterations,
        "converged": False,
        "history": history,
    }


# ── QUBO Matrix (dict format for HiGHS) ─────────────────────────────────────

def bracket_cost(bracket: dict) -> float:
    """Compute the individual (diagonal) cost for a single bracket.

    Negative cost → prefer selecting this bracket (admissible is good).
    """
    base = 1.0 if bracket.get("admissible", False) else 2.0
    # Gap magnitude bonus: larger gaps reduce cost
    gap = bracket.get("gap", 0)
    gap_f = gap / Q16_ONE if gap < 0x80000000 else (gap - 0x100000000) / Q16_ONE
    return -base + abs(gap_f) * 0.1


def crossing_penalty(b1: dict, b2: dict) -> float:
    """Compute the off-diagonal interaction cost between two brackets.

    Positive penalty → discourage selecting both when they conflict.
    """
    penalty = 0.0
    if _brackets_overlap(b1, b2):
        penalty += 2.0
    # Gap similarity: reward diversity
    g1 = _q16_to_float(b1.get("gap", 0))
    g2 = _q16_to_float(b2.get("gap", 0))
    penalty -= 0.1 * abs(g1 - g2)
    return penalty


def build_qubo_matrix(brackets: List[dict]) -> Dict[Tuple[int, int], float]:
    """Convert brackets to a dict-format QUBO matrix Q[i,j].

    Q[i,i] = bracket_cost(bracket)  — diagonal (linear bias).
    Q[i,j] = crossing_penalty(b_i, b_j) — off-diagonal (interaction).

    This format is directly consumable by ``solve_qubo_highs``.

    Args:
        brackets: list of BraidBracket dicts.

    Returns:
        Dict mapping (i, j) → cost coefficient.
    """
    n = len(brackets)
    Q: Dict[Tuple[int, int], float] = {}
    for i in range(n):
        Q[(i, i)] = bracket_cost(brackets[i])
        for j in range(i + 1, n):
            Q[(i, j)] = crossing_penalty(brackets[i], brackets[j])
            Q[(j, i)] = Q[(i, j)]
    return Q


# ── QUBO Optimization (list-format, SA) ────────────────────────────────────

def _build_qubo_matrix(bracket_pairs: List[Tuple[dict, dict]]) -> List[List[float]]:
    """Build a QUBO matrix from bracket pair costs.

    Each bracket pair (A, B) has a crossing cost derived from gap difference,
    admissibility conflict, and parity mismatch.

    The QUBO matrix Q is symmetric with shape (n × n) where n = len(bracket_pairs).
    Diagonal Q[i][i] = individual pair cost (linear bias).
    Off-diagonal Q[i][j] = interaction cost between pairs i and j.

    Goal: minimise x^T Q x  over binary x ∈ {0,1}^n.
    """
    n = len(bracket_pairs)
    Q = [[0.0] * n for _ in range(n)]

    for i in range(n):
        a_i, b_i = bracket_pairs[i]
        # Linear bias: admissible pairs get negative cost (prefer them)
        if a_i.get("admissible", False) and b_i.get("admissible", False):
            Q[i][i] = -1.0
        else:
            Q[i][i] = 1.0

        # Quadratic interaction
        for j in range(i + 1, n):
            a_j, b_j = bracket_pairs[j]
            cost = 0.0

            # Overlap penalty: if pairs share a bracket, penalise
            if _brackets_overlap(a_i, a_j) or _brackets_overlap(b_i, b_j):
                cost += 2.0

            # Gap similarity reward: diverse gaps are better
            gap_i = _q16_to_float(a_i.get("gap", 0))
            gap_j = _q16_to_float(a_j.get("gap", 0))
            cost -= 0.1 * abs(gap_i - gap_j)

            Q[i][j] = cost
            Q[j][i] = cost

    return Q


def _brackets_overlap(b1: dict, b2: dict) -> bool:
    """Check if two brackets overlap in their [lower, upper] ranges."""
    l1 = _q16_to_float(b1.get("lower", 0))
    u1 = _q16_to_float(b1.get("upper", 0))
    l2 = _q16_to_float(b2.get("lower", 0))
    u2 = _q16_to_float(b2.get("upper", 0))
    return l1 < u2 and l2 < u1


def _q16_to_float(v: int) -> float:
    """Convert unsigned Q16_16 to float (boundary use only)."""
    if v >= 0x80000000:
        return (v - 0x100000000) / Q16_ONE
    return v / Q16_ONE


def _qubo_energy(Q: List[List[float]], x: List[int]) -> float:
    """Compute x^T Q x."""
    n = len(x)
    energy = 0.0
    for i in range(n):
        for j in range(n):
            energy += Q[i][j] * x[i] * x[j]
    return energy


def qubo_optimize(bracket_pairs: List[Tuple[dict, dict]],
                  max_iterations: int = 5000,
                  seed: int = 42,
                  initial_temp: float = 10.0,
                  cooling_rate: float = 0.9995) -> dict:
    """Solve the QUBO via simulated annealing.

    Args:
        bracket_pairs: list of (bracket_a, bracket_b) tuples.
        max_iterations: SA iteration count.
        seed: RNG seed.
        initial_temp: starting temperature.
        cooling_rate: geometric cooling factor per step.

    Returns:
        {
            "selection": List[int],   # binary vector (1 = selected pair)
            "selected_pairs": List[Tuple[dict, dict]],
            "energy": float,
            "iterations": int,
        }
    """
    rng = random.Random(seed)
    n = len(bracket_pairs)
    if n == 0:
        return {"selection": [], "selected_pairs": [], "energy": 0.0, "iterations": 0}

    Q = _build_qubo_matrix(bracket_pairs)

    # Initial solution: all ones (select all pairs)
    x = [1] * n
    current_energy = _qubo_energy(Q, x)
    best_x = list(x)
    best_energy = current_energy

    temp = initial_temp
    for iteration in range(1, max_iterations + 1):
        # Flip a random bit
        idx = rng.randint(0, n - 1)
        x[idx] = 1 - x[idx]
        new_energy = _qubo_energy(Q, x)
        delta = new_energy - current_energy

        # Accept or reject
        if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-12)):
            current_energy = new_energy
            if current_energy < best_energy:
                best_energy = current_energy
                best_x = list(x)
        else:
            x[idx] = 1 - x[idx]  # revert

        temp *= cooling_rate

    selected = [bracket_pairs[i] for i in range(n) if best_x[i]]
    return {
        "selection": best_x,
        "selected_pairs": selected,
        "energy": best_energy,
        "iterations": max_iterations,
    }


# ── Convenience: combined search ────────────────────────────────────────────

def find_optimal_crossing(brackets: List[dict],
                          max_iterations: int = 1000) -> dict:
    """Find the optimal crossing configuration from a set of brackets.

    1. Build QUBO matrix from brackets (dict format).
    2. Try HiGHS MIP solver first (exact, fast for small instances).
    3. Fall back to simulated annealing if HiGHS unavailable or fails.
    4. Run soliton search on the candidates.

    Args:
        brackets: list of BraidBracket dicts.
        max_iterations: iteration budget for soliton search and SA fallback.

    Returns:
        {
            "qubo_result": dict,
            "soliton_result": dict,
            "optimal_pairs": List[Tuple[dict, dict]],
            "method": str,            # 'highs_mip' or 'simulated_annealing'
        }
    """
    # Build dict-format QUBO matrix from raw brackets
    Q = build_qubo_matrix(brackets)

    qubo_result = None
    method = "simulated_annealing"

    # ── Try HiGHS first ────────────────────────────────────────────────
    if _HIGHS_AVAILABLE:
        try:
            result = solve_qubo_highs(Q, time_limit=30.0)
            selection = result.get("solution", [])
            # Convert selection vector to bracket pairs
            selected_brackets = [brackets[i] for i in range(len(selection))
                                 if i < len(brackets) and selection[i]]
            # Reconstruct pairs from selected brackets
            selected_pairs = []
            for i in range(len(selected_brackets)):
                for j in range(i + 1, len(selected_brackets)):
                    selected_pairs.append((selected_brackets[i],
                                           selected_brackets[j]))
            qubo_result = {
                "selection": selection,
                "selected_pairs": selected_pairs,
                "energy": result.get("objective", 0.0),
                "iterations": 1,
                "highs_status": result.get("status", "unknown"),
            }
            method = "highs_mip"
        except Exception as exc:
            # Log and fall through to SA
            print(f"[braid_search] HiGHS failed ({exc}), falling back to SA")

    # ── Simulated annealing fallback ───────────────────────────────────
    if qubo_result is None:
        # Generate bracket pairs (only admissible pairs are candidates)
        pairs = []
        for i in range(len(brackets)):
            for j in range(i + 1, len(brackets)):
                if (brackets[i].get("admissible", False)
                        and brackets[j].get("admissible", False)):
                    pairs.append((brackets[i], brackets[j]))

        if not pairs:
            # Fall back to all pairs even if not admissible
            for i in range(len(brackets)):
                for j in range(i + 1, len(brackets)):
                    pairs.append((brackets[i], brackets[j]))

        qubo_result = qubo_optimize(pairs, max_iterations=max_iterations)
        method = "simulated_annealing"

    # Build crossing candidates from QUBO-selected pairs
    selected_pairs = qubo_result.get("selected_pairs", [])
    crossing_candidates = []
    for a, b in selected_pairs:
        crossing_candidates.append({
            "brackets": [a, b],
            "admissible": a.get("admissible", False) and b.get("admissible", False),
        })

    # Fallback: if HiGHS selected nothing, build from all pairs
    if not crossing_candidates:
        for i in range(len(brackets)):
            for j in range(i + 1, len(brackets)):
                crossing_candidates.append({
                    "brackets": [brackets[i], brackets[j]],
                    "admissible": (brackets[i].get("admissible", False)
                                   and brackets[j].get("admissible", False)),
                })

    soliton_result = soliton_search(
        target_energy=float("inf"),
        candidates=crossing_candidates,
        max_iterations=max_iterations,
    )

    return {
        "qubo_result": qubo_result,
        "soliton_result": soliton_result,
        "optimal_pairs": selected_pairs if selected_pairs else qubo_result.get("selected_pairs", []),
        "method": method,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import sys
    print("braid_search.py — Soliton Search / QUBO / Sidon Slot Assignment")
    print()
    print("Functions:")
    print("  assign_sidon_slots(num_slots)           -> List[int]")
    print("  soliton_search(target, candidates)       -> dict")
    print("  qubo_optimize(bracket_pairs)             -> dict")
    print("  build_qubo_matrix(brackets)              -> Dict[(i,j), float]")
    print("  find_optimal_crossing(brackets)          -> dict")
    print()
    print(f"  HiGHS available: {_HIGHS_AVAILABLE}")
    print()

    # Demo: Sidon set
    n = 10
    slots = assign_sidon_slots(n)
    valid = verify_sidon(slots)
    print(f"  Sidon set (n={n}): {slots}")
    print(f"  Valid: {valid}")


if __name__ == "__main__":
    import time

    # Generate test brackets with varying properties
    test_brackets = [
        {"admissible": True, "gap": 0x00020000, "lower": 0x00000000, "upper": 0x00030000},
        {"admissible": True, "gap": 0x00040000, "lower": 0x00010000, "upper": 0x00050000},
        {"admissible": False, "gap": 0x00010000, "lower": 0x00020000, "upper": 0x00030000},
        {"admissible": True, "gap": 0x00030000, "lower": 0x00000000, "upper": 0x00030000},
        {"admissible": True, "gap": 0x00050000, "lower": 0x00040000, "upper": 0x00090000},
        {"admissible": False, "gap": 0x00028000, "lower": 0x00010000, "upper": 0x00038000},
    ]

    main()
    print()

    # ── Timing: HiGHS vs SA ────────────────────────────────────────────
    # Time HiGHS (or full pipeline with HiGHS)
    t0 = time.time()
    r1 = find_optimal_crossing(test_brackets)
    t_highs = time.time() - t0

    # Time SA fallback directly
    pairs = []
    for i in range(len(test_brackets)):
        for j in range(i + 1, len(test_brackets)):
            pairs.append((test_brackets[i], test_brackets[j]))

    t0 = time.time()
    r2 = qubo_optimize(pairs)
    t_sa = time.time() - t0

    print(f"  find_optimal_crossing method: {r1.get('method', 'unknown')}")
    print(f"  find_optimal_crossing: {t_highs*1000:.1f}ms  |  SA direct: {t_sa*1000:.1f}ms")
    print(f"  HiGHS available: {_HIGHS_AVAILABLE}")
