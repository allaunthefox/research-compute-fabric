#!/usr/bin/env python3
"""
braid_event_sidon_addressing.py
================================

Two-layer cross-check: do the events emitted by `compute_event` admit
Sidon-style relational addressing (per Two_Layer_Kinetic_Sidon_Lattice_v0_1.md
Gate 2 — Sidon uniqueness)?

For each candidate pair-signature σ(i, j) over the 175-event population from
braid_event_delta_gcl.py:

  - count nontrivial pair collisions  (σ(i,j) == σ(k,l)  with  {i,j} ≠ {k,l})
  - report fraction of pairs that are uniquely addressable
  - generate the smallest greedy Sidon set that labels all events
  - compare: kinetic-formula-derived signatures  vs  Sidon-set-derived signatures

This is the empirical "Gate 2" for the two-layer lattice spec: the kinetic layer
generates events; the Sidon layer is supposed to give them a non-aliasing address
space. We measure the gap.

Stdlib only.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

# Reuse the canonicalized event generator from the sibling module.
from braid_event_delta_gcl import compute_event_v2, BraidEventParams


# =============================================================================
# 1. Candidate pair-signature functions
# =============================================================================

def sig_mass_sum(ei: dict, ej: dict) -> tuple:
    return ("mass_sum", ei["mass"] + ej["mass"])

def sig_polarity_sum(ei: dict, ej: dict) -> tuple:
    return ("polarity_sum", ei["polarity"] + ej["polarity"])

def sig_interaction_sum(ei: dict, ej: dict) -> tuple:
    return ("interaction_sum", round(ei["interaction"] + ej["interaction"], 6))

def sig_n_sum(ei: dict, ej: dict) -> tuple:
    """The classical Sidon-set signature: σ(i,j) = n_i + n_j."""
    return ("n_sum", ei["n"] + ej["n"])

def sig_phase_codon(ei: dict, ej: dict) -> tuple:
    """Pure quantized signature: only the phase + codon survive."""
    return ("phase_codon", tuple(sorted([(ei["phase"], ei["et"]),
                                         (ej["phase"], ej["et"])])))

def sig_kinetic_full(ei: dict, ej: dict) -> tuple:
    """Composite kinetic signature: every quantity that compute_event outputs."""
    return ("kinetic_full",
            (round(ei["mass"] + ej["mass"], 6),
             round(ei["polarity"] + ej["polarity"], 6),
             round(ei["interaction"] + ej["interaction"], 6),
             tuple(sorted([ei["et"], ej["et"]]))))


SIGNATURES = [
    sig_mass_sum,
    sig_polarity_sum,
    sig_n_sum,
    sig_interaction_sum,
    sig_phase_codon,
    sig_kinetic_full,
]


# =============================================================================
# 2. Collision counter
# =============================================================================

def collision_report(events: list[dict], sig_fn) -> dict:
    """For unordered pairs (i, j) with i < j, count colliding signatures."""
    seen: dict = {}  # signature → list of (i, j)
    n = len(events)
    pair_count = n * (n - 1) // 2
    for i, j in itertools.combinations(range(n), 2):
        s = sig_fn(events[i], events[j])
        seen.setdefault(s, []).append((i, j))
    distinct_sigs = len(seen)
    collisions = sum(len(v) - 1 for v in seen.values() if len(v) > 1)
    colliding_classes = sum(1 for v in seen.values() if len(v) > 1)
    return {
        "signature_name": sig_fn.__name__,
        "pair_count": pair_count,
        "distinct_signatures": distinct_sigs,
        "collision_count": collisions,
        "colliding_equivalence_classes": colliding_classes,
        "uniqueness_ratio": distinct_sigs / max(1, pair_count),
        "passes_sidon_gate": collisions == 0,
    }


# =============================================================================
# 3. Greedy Sidon set generator (mirrors SidonSet.lean)
# =============================================================================

def is_sidon(values: list[int]) -> bool:
    sums = set()
    for i, a in enumerate(values):
        for b in values[i:]:
            s = a + b
            if s in sums:
                return False
            sums.add(s)
    return True


def generate_sidon(target_size: int, fuel: int = 1_000_000) -> list[int]:
    out = [1]
    candidate = 2
    used_sums = {2}  # 1 + 1
    while len(out) < target_size:
        if fuel <= 0:
            raise RuntimeError(f"fuel exhausted at size {len(out)}")
        new_sums = {candidate + x for x in out} | {candidate + candidate}
        if not (new_sums & used_sums) and len(new_sums) == len({candidate + x for x in out + [candidate]}):
            out.append(candidate)
            used_sums |= new_sums
        candidate += 1
        fuel -= 1
    return out


# =============================================================================
# 4. Main
# =============================================================================

def main():
    out_dir = Path(__file__).resolve().parents[3] / "shared-data" / "artifacts" / "formula_optimization"
    out_dir.mkdir(parents=True, exist_ok=True)

    N = 2000
    params = BraidEventParams()
    events = [e for n in range(N + 1) if (e := compute_event_v2(n, params)) is not None]
    print(f"event population: {len(events)} events from n ∈ [0, {N}]\n")

    # ---- candidate kinetic signatures ----
    print("Sidon Gate 2 — pair-signature collision counts:")
    print(f"{'signature':<25} {'pairs':>6} {'distinct':>9} {'collisions':>11} {'uniq%':>7}  passes?")
    print("-" * 75)
    sig_reports = []
    for fn in SIGNATURES:
        r = collision_report(events, fn)
        sig_reports.append(r)
        print(f"{r['signature_name']:<25} {r['pair_count']:>6} "
              f"{r['distinct_signatures']:>9} {r['collision_count']:>11} "
              f"{r['uniqueness_ratio']*100:>6.2f}%  {r['passes_sidon_gate']}")

    # ---- Sidon address layer: generate one large enough to label all events ----
    target = len(events)
    print(f"\nGenerating greedy Sidon set of size {target}...")
    try:
        sidon = generate_sidon(target)
        print(f"  smallest greedy Sidon set: head={sidon[:5]}  tail={sidon[-3:]}  "
              f"max_element={max(sidon)}")
        print(f"  is_sidon(set)? {is_sidon(sidon)}")
        # Build the Sidon-relabeled events and re-test "n_sum" on relabeled n
        relabeled = []
        for ev, s_addr in zip(events, sidon):
            ev2 = dict(ev)
            ev2["n"] = s_addr  # replace n with its Sidon address
            relabeled.append(ev2)
        r = collision_report(relabeled, sig_n_sum)
        print(f"  n_sum on Sidon-relabeled events: collisions={r['collision_count']} "
              f"passes_sidon_gate={r['passes_sidon_gate']}")
        sidon_relabel_report = r
    except RuntimeError as exc:
        print(f"  failed: {exc}")
        sidon = []
        sidon_relabel_report = {"error": str(exc)}

    bundle = {
        "n_max": N,
        "event_count": len(events),
        "kinetic_signature_reports": sig_reports,
        "sidon_address_set": {
            "size": len(sidon),
            "head": sidon[:10],
            "tail": sidon[-3:] if sidon else [],
            "max_element": max(sidon) if sidon else None,
            "is_sidon": is_sidon(sidon) if sidon else None,
        },
        "sidon_relabeled_n_sum_report": sidon_relabel_report,
    }
    out_json = out_dir / "braid_event_sidon_addressing_bundle.json"
    out_json.write_text(json.dumps(bundle, indent=2))
    print(f"\nwrote bundle: {out_json}")


if __name__ == "__main__":
    main()
