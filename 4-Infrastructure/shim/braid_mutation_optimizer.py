#!/usr/bin/env python3
"""
braid_mutation_optimizer.py — Multi-core Parallel Genetic Optimizer for Braid/Tree Math

Simulates 8-strand braid state dynamics (State8, crossStep, fammGate) from BraidTreeDIATPIST.lean
and performs multi-core mutation-based genetic optimization to find stable eigensolids.

Optimizes:
  1. Initial phase vector components (psi_raw, kappa_raw).
  2. Strand slot assignments using a Sidon set.
  3. Crossing weight w_raw.

Goal:
  Maximise convergence speed to a stable eigensolid (fixed point) under crossStep,
  minimise accumulated residuals (residue_raw), avoid FAMM scars, and maximise Sidon slack.

Compute path uses ONLY integer / Q16_16 / Q0_2 arithmetic. No float in core logic.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass, asdict
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Tuple, Optional

# Q16_16 and Q0_2 scaling
Q16_SCALE = 65536
Q0_2_MAX = 49152  # 0.75 in Q0_2 / Q16_16 scale

# ── Braid Simulation Math (Integer Only) ─────────────────────────────────────

@dataclass
class PhaseVec:
    psi_raw: int
    kappa_raw: int

@dataclass
class Strand:
    phase: PhaseVec
    slot: int
    residue_raw: int

@dataclass
class State8:
    strands: List[Strand]
    k: int

def q0_2_raw_add(a: int, b: int) -> int:
    return a + b

def q0_2_raw_mul(a: int, b: int) -> int:
    return (a * b) // 65536

def is_admissible(strand: Strand) -> bool:
    return strand.phase.kappa_raw <= Q0_2_MAX

def check_slots_unique(strands: List[Strand]) -> bool:
    slots = [s.slot for s in strands]
    return len(slots) == len(set(slots))

def famm_gate_check(strands: List[Strand]) -> bool:
    """Check if the state passes the FAMM admissibility filter."""
    for i, s in enumerate(strands):
        if not is_admissible(s):
            return False
        # Check slot uniqueness against others
        for j, other in enumerate(strands):
            if i != j and s.slot == other.slot:
                return False
    return True

def cross_strands(si: Strand, sj: Strand, w_raw: int) -> Strand:
    psi_sum = si.phase.psi_raw + sj.phase.psi_raw + \
              (w_raw * (si.phase.kappa_raw + sj.phase.kappa_raw)) // 65536
    kappa = si.phase.kappa_raw
    eps = q0_2_raw_add(si.residue_raw, sj.residue_raw)
    return Strand(
        phase=PhaseVec(psi_raw=psi_sum, kappa_raw=kappa),
        slot=si.slot,
        residue_raw=eps
    )

def cross_step(s: State8, w_raw: int) -> State8:
    """Applies crossStep to the 8-strand braid state as defined in Lean."""
    # Even-round crossing: (0,1), (2,3), (4,5), (6,7)
    crossed_0_1 = cross_strands(s.strands[0], s.strands[1], w_raw)
    crossed_1_0 = cross_strands(s.strands[1], s.strands[0], w_raw)
    crossed_2_3 = cross_strands(s.strands[2], s.strands[3], w_raw)
    crossed_3_2 = cross_strands(s.strands[3], s.strands[2], w_raw)
    crossed_4_5 = cross_strands(s.strands[4], s.strands[5], w_raw)
    crossed_5_4 = cross_strands(s.strands[5], s.strands[4], w_raw)
    crossed_6_7 = cross_strands(s.strands[6], s.strands[7], w_raw)
    crossed_7_6 = cross_strands(s.strands[7], s.strands[6], w_raw)

    new_strands = [
        crossed_0_1, crossed_1_0,
        crossed_2_3, crossed_3_2,
        crossed_4_5, crossed_5_4,
        crossed_6_7, crossed_7_6
    ]
    # In Lean, fammGate determines if scars are added, but it returns the state s1.
    return State8(strands=new_strands, k=s.k + 1)

def strands_equal(s1: State8, s2: State8) -> bool:
    for i in range(8):
        st1 = s1.strands[i]
        st2 = s2.strands[i]
        if st1.phase.psi_raw != st2.phase.psi_raw:
            return False
        if st1.phase.kappa_raw != st2.phase.kappa_raw:
            return False
        if st1.slot != st2.slot:
            return False
        if st1.residue_raw != st2.residue_raw:
            return False
    return True

# ── Genetic Algorithm Optimization ───────────────────────────────────────────

@dataclass
class Chromosome:
    w_raw: int
    initial_psi: List[int]
    initial_kappa: List[int]
    slots: List[int]

def evaluate_chromosome(c: Chromosome, max_steps: int = 50) -> int:
    """Evaluate chromosome fitness (higher is better, integer return).
    
    Fitness components:
      - Maximize convergence (1000000 bonus if converged).
      - Penalise steps taken to converge (fewer steps -> higher score).
      - Penalise FAMM gate failure (scars).
      - Penalise large accumulated residues.
      - Reward non-triviality (variance/absolute sum of psi_raw).
      - Reward Sidon slack.
    """
    # Build initial State8
    strands = []
    for i in range(8):
        strands.append(Strand(
            phase=PhaseVec(psi_raw=c.initial_psi[i], kappa_raw=c.initial_kappa[i]),
            slot=c.slots[i],
            residue_raw=0
        ))
    state = State8(strands=strands, k=0)

    converged = False
    famm_passes = True
    steps = 0
    
    current = state
    for step in range(1, max_steps + 1):
        # Check FAMM gate
        if not famm_gate_check(current.strands):
            famm_passes = False
            
        nxt = cross_step(current, c.w_raw)
        steps = step
        if strands_equal(nxt, current):
            converged = True
            current = nxt
            break
        current = nxt

    # Compute fitness score entirely with integer arithmetic
    score = 0
    if converged:
        score += 2000000
        score += (max_steps - steps) * 20000
    else:
        score += steps * 1000  # Some small credit for surviving without infinite loop

    if famm_passes:
        score += 500000
    else:
        score -= 200000

    # Total accumulated residue penalty (Q16_16 units)
    total_residue = sum(abs(st.residue_raw) for st in current.strands)
    score -= total_residue // 4

    # Reward phase amplitude (non-triviality)
    total_psi = sum(abs(st.phase.psi_raw) for st in current.strands)
    # Clip psi reward to prevent unbounded scaling to infinity
    score += min(100000, total_psi // 8)

    # Sidon slack reward: 128 - maxSlot
    max_slot = max(c.slots)
    score += (128 - max_slot) * 1000

    return score

# ── Evolution Helpers ────────────────────────────────────────────────────────

def create_random_chromosome(sidon_set: List[int]) -> Chromosome:
    w_raw = random.choice([0, 16384, 32768, 49152])
    initial_kappa = [random.randint(0, Q0_2_MAX) for _ in range(8)]
    
    # 50% chance to initialize directly on the algebraic eigensolid manifold
    if random.random() < 0.5:
        initial_psi = [0] * 8
        for p in range(4):
            idx1 = p * 2
            idx2 = idx1 + 1
            # Eigensolid condition: psi_1 = psi_2 = - w_raw * (kappa_1 + kappa_2) // 65536
            offset = - (w_raw * (initial_kappa[idx1] + initial_kappa[idx2])) // 65536
            initial_psi[idx1] = offset
            initial_psi[idx2] = offset
    else:
        initial_psi = [random.randint(-50000, 50000) for _ in range(8)]

    # Shuffle Sidon set to assign unique slots
    slots = list(sidon_set)
    random.shuffle(slots)
    return Chromosome(w_raw=w_raw, initial_psi=initial_psi, initial_kappa=initial_kappa, slots=slots)

def mutate(c: Chromosome, sidon_set: List[int], mutation_rate: float = 0.2) -> Chromosome:
    w_raw = c.w_raw
    if random.random() < mutation_rate:
        w_raw = random.choice([0, 16384, 32768, 49152])

    initial_kappa = list(c.initial_kappa)
    for i in range(8):
        if random.random() < mutation_rate:
            initial_kappa[i] = max(0, min(Q0_2_MAX, initial_kappa[i] + random.randint(-5000, 5000)))

    initial_psi = list(c.initial_psi)
    # Guided mutation: project towards algebraic eigensolid manifold
    if random.random() < 0.3:
        for p in range(4):
            idx1 = p * 2
            idx2 = idx1 + 1
            offset = - (w_raw * (initial_kappa[idx1] + initial_kappa[idx2])) // 65536
            initial_psi[idx1] = offset
            initial_psi[idx2] = offset
    else:
        for i in range(8):
            if random.random() < mutation_rate:
                initial_psi[i] += random.randint(-10000, 10000)

    slots = list(c.slots)
    if random.random() < mutation_rate:
        # Swap slots of two random strands to maintain uniqueness
        idx1, idx2 = random.sample(range(8), 2)
        slots[idx1], slots[idx2] = slots[idx2], slots[idx1]

    return Chromosome(w_raw=w_raw, initial_psi=initial_psi, initial_kappa=initial_kappa, slots=slots)

def crossover(p1: Chromosome, p2: Chromosome) -> Chromosome:
    # Blend w_raw
    w_raw = random.choice([p1.w_raw, p2.w_raw])
    
    # Single point crossover on lists
    cp = random.randint(1, 7)
    initial_psi = p1.initial_psi[:cp] + p2.initial_psi[cp:]
    initial_kappa = p1.initial_kappa[:cp] + p2.initial_kappa[cp:]
    
    # For slots, to preserve uniqueness, we use PMX-like approach or just take parents' slots
    slots = p1.slots
    if random.random() < 0.5:
        slots = p2.slots

    return Chromosome(w_raw=w_raw, initial_psi=initial_psi, initial_kappa=initial_kappa, slots=slots)

# ── Parallel Task Worker ─────────────────────────────────────────────────────

def _eval_worker(c: Chromosome) -> int:
    return evaluate_chromosome(c)

def run_generation_parallel(population: List[Chromosome], pool: Pool) -> List[int]:
    return pool.map(_eval_worker, population)

# ── Main Optimization Run ────────────────────────────────────────────────────

def optimize(
    generations: int,
    pop_size: int,
    threads: int,
    sidon_method: str
) -> Dict:
    # Determine Sidon slots
    if sidon_method == "powers_of_2":
        sidon_set = [1, 2, 4, 8, 16, 32, 64, 128]
    else:
        # Greedy optimal Mian-Chowla sequence for n=8
        sidon_set = [1, 3, 7, 12, 20, 30, 44, 65]

    print(f"[*] Starting GA Optimization with Sidon Set: {sidon_set}")
    print(f"[*] Population size: {pop_size}, Generations: {generations}, Workers: {threads}")

    population = [create_random_chromosome(sidon_set) for _ in range(pop_size)]
    
    best_chromosome = population[0]
    best_fitness = -99999999
    history = []

    t0 = time.time()
    
    with Pool(processes=threads) as pool:
        for gen in range(1, generations + 1):
            fitnesses = run_generation_parallel(population, pool)
            
            # Find best
            for idx, fit in enumerate(fitnesses):
                if fit > best_fitness:
                    best_fitness = fit
                    best_chromosome = population[idx]
            
            # Print status periodically
            if gen % 10 == 0 or gen == 1:
                print(f"  [Gen {gen:04d}] Best Fitness: {best_fitness}")
                history.append({"generation": gen, "best_fitness": best_fitness})
                
            # Selection & Crossover to form next generation
            new_pop = []
            
            # Elitist preservation
            elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:pop_size // 10]
            for idx in elite_indices:
                new_pop.append(population[idx])
                
            while len(new_pop) < pop_size:
                # Tournament selection
                t_size = 5
                p1_cand = random.sample(range(pop_size), t_size)
                p1 = population[max(p1_cand, key=lambda idx: fitnesses[idx])]
                
                p2_cand = random.sample(range(pop_size), t_size)
                p2 = population[max(p2_cand, key=lambda idx: fitnesses[idx])]
                
                child = crossover(p1, p2)
                child = mutate(child, sidon_set)
                new_pop.append(child)
                
            population = new_pop

    elapsed = time.time() - t0
    print(f"[+] Optimization finished in {elapsed:.2f} seconds.")
    print(f"[+] Best fitness achieved: {best_fitness}")
    
    # Run full simulation check on the best chromosome to extract convergence profile
    strands = []
    for i in range(8):
        strands.append(Strand(
            phase=PhaseVec(psi_raw=best_chromosome.initial_psi[i], kappa_raw=best_chromosome.initial_kappa[i]),
            slot=best_chromosome.slots[i],
            residue_raw=0
        ))
    state = State8(strands=strands, k=0)
    
    trace = []
    current = state
    for step in range(1, 51):
        trace.append({
            "step": step,
            "total_residue": sum(abs(st.residue_raw) for st in current.strands),
            "max_psi": max(abs(st.phase.psi_raw) for st in current.strands)
        })
        nxt = cross_step(current, best_chromosome.w_raw)
        if strands_equal(nxt, current):
            current = nxt
            break
        current = nxt

    # Build output dict
    result = {
        "best_chromosome": {
            "w_raw": best_chromosome.w_raw,
            "initial_psi": best_chromosome.initial_psi,
            "initial_kappa": best_chromosome.initial_kappa,
            "slots": best_chromosome.slots
        },
        "best_fitness": best_fitness,
        "converged": len(trace) < 50,
        "steps_to_converge": len(trace),
        "history": history,
        "trace": trace,
        "elapsed_seconds": elapsed,
        "sidon_set": sidon_set
    }
    
    return result

# ── Main Entry ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Braid Eigensolid Mutation Optimizer")
    parser.add_argument("--generations", type=int, default=100, help="Number of GA generations")
    parser.add_argument("--pop-size", type=int, default=200, help="Population size")
    parser.add_argument("--threads", type=int, default=cpu_count(), help="Number of concurrent worker threads")
    parser.add_argument("--sidon-method", choices=["powers_of_2", "greedy_optimal"], default="greedy_optimal")
    parser.add_argument("--output", default="braid_mutation_optimization_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    res = optimize(
        generations=args.generations,
        pop_size=args.pop_size,
        threads=args.threads,
        sidon_method=args.sidon_method
    )
    
    # Save receipt
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
    print(f"[+] Output receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
