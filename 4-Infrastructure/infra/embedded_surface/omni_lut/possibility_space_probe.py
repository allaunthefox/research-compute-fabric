#!/usr/bin/env python3
"""Metaprobe + RGFlow pass over sequence-surface possibility spaces.

The sequence LUT should not be chosen by taste. This probe enumerates compact
candidate surfaces, extracts a small metaprobe signature, then keeps candidates
whose usefulness persists under coarse RG flow.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path
from typing import Iterable

try:
    from .sequence_surface_lut import (
        OP_COMPLEMENT,
        OP_MUTATE,
        OP_ROUTE,
        OP_TRANSCRIBE,
        OP_TRANSLATE_HINT,
        ROLE_ARCHIVAL,
        ROLE_CATALYTIC,
        ROLE_EXPANDED,
        ROLE_MESSENGER,
        ROLE_SYNTHETIC,
        SURFACES,
        SequenceSurface,
    )
    from .gcl_motif_lut import MOTIFS
except ImportError:
    from sequence_surface_lut import (
        OP_COMPLEMENT,
        OP_MUTATE,
        OP_ROUTE,
        OP_TRANSCRIBE,
        OP_TRANSLATE_HINT,
        ROLE_ARCHIVAL,
        ROLE_CATALYTIC,
        ROLE_EXPANDED,
        ROLE_MESSENGER,
        ROLE_SYNTHETIC,
        SURFACES,
        SequenceSurface,
    )
    from gcl_motif_lut import MOTIFS


ROLE_MASKS = {
    "archival": ROLE_ARCHIVAL,
    "catalytic": ROLE_CATALYTIC,
    "messenger": ROLE_MESSENGER,
    "synthetic": ROLE_SYNTHETIC,
    "expanded": ROLE_EXPANDED,
}

OP_MASKS = {
    "complement": OP_COMPLEMENT,
    "transcribe": OP_TRANSCRIBE,
    "translate_hint": OP_TRANSLATE_HINT,
    "mutate": OP_MUTATE,
    "route": OP_ROUTE,
}


@dataclass(frozen=True)
class SurfaceCandidate:
    name: str
    family: str
    alphabet_size: int
    bits_per_symbol: int
    role_flags: int
    op_flags: int
    complement_closed: bool
    closure_kind: str
    known_surface: bool


@dataclass(frozen=True)
class ProbeSignature:
    compactness: float
    closure: float
    operation_density: float
    role_density: float
    degeneracy: float
    frame_efficiency: float
    combinatorial_capacity: float


@dataclass(frozen=True)
class RGState:
    mu_bin: int
    rho_bin: int
    c_bin: int
    m_bin: int
    ne_bin: int
    sig_bin: int


@dataclass(frozen=True)
class ProbeResult:
    candidate: SurfaceCandidate
    signature: ProbeSignature
    initial_state: RGState
    final_state: RGState
    lawful_now: bool
    lawful_under_flow: bool
    rg_depth: int
    score: float
    verdict: str


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def bin8(value: float) -> int:
    return int(clamp(value, 0.0, 0.999999) * 8.0)


def bit_count(value: int) -> int:
    return value.bit_count()


def bits_for_alphabet(alphabet_size: int) -> int:
    return max(1, math.ceil(math.log2(alphabet_size)))


def known_candidates() -> Iterable[SurfaceCandidate]:
    for surface in SURFACES.values():
        yield SurfaceCandidate(
            name=surface.name,
            family="sequence",
            alphabet_size=len(surface.symbols),
            bits_per_symbol=surface.bits_per_symbol,
            role_flags=surface.role_flags,
            op_flags=surface.op_flags,
            complement_closed=bool(surface.op_flags & OP_COMPLEMENT),
            closure_kind="complement" if surface.op_flags & OP_COMPLEMENT else "none",
            known_surface=True,
        )


def motif_candidates() -> Iterable[SurfaceCandidate]:
    for motif in MOTIFS.values():
        yield SurfaceCandidate(
            name=motif.name,
            family="gcl_motif",
            alphabet_size=motif.alphabet_size,
            bits_per_symbol=motif.bits_per_symbol,
            role_flags=motif.role_flags,
            op_flags=motif.op_flags,
            complement_closed=False,
            closure_kind=motif.closure_kind,
            known_surface=True,
        )


def synthetic_candidates(max_alphabet: int) -> Iterable[SurfaceCandidate]:
    role_options = [
        ROLE_ARCHIVAL,
        ROLE_CATALYTIC,
        ROLE_MESSENGER,
        ROLE_SYNTHETIC,
        ROLE_ARCHIVAL | ROLE_EXPANDED,
        ROLE_SYNTHETIC | ROLE_EXPANDED,
        ROLE_CATALYTIC | ROLE_MESSENGER,
    ]
    op_options = [
        OP_ROUTE | OP_MUTATE,
        OP_ROUTE | OP_COMPLEMENT,
        OP_ROUTE | OP_COMPLEMENT | OP_MUTATE,
        OP_ROUTE | OP_COMPLEMENT | OP_TRANSCRIBE,
        OP_ROUTE | OP_TRANSLATE_HINT | OP_MUTATE,
        OP_ROUTE | OP_COMPLEMENT | OP_TRANSCRIBE | OP_TRANSLATE_HINT | OP_MUTATE,
    ]
    for alphabet_size, role_flags, op_flags in product(range(2, max_alphabet + 1), role_options, op_options):
        complement_closed = bool(op_flags & OP_COMPLEMENT) and alphabet_size % 2 == 0
        yield SurfaceCandidate(
            name=f"a{alphabet_size:02d}_r{role_flags:02x}_o{op_flags:02x}",
            family="synthetic",
            alphabet_size=alphabet_size,
            bits_per_symbol=bits_for_alphabet(alphabet_size),
            role_flags=role_flags,
            op_flags=op_flags,
            complement_closed=complement_closed,
            closure_kind="complement" if complement_closed else "partial" if op_flags & OP_COMPLEMENT else "none",
            known_surface=False,
        )


def metaprobe(candidate: SurfaceCandidate, window_symbols: int) -> ProbeSignature:
    compactness = 1.0 / candidate.bits_per_symbol
    messenger_exec = bool(candidate.role_flags & ROLE_MESSENGER) and bool(
        candidate.op_flags & OP_TRANSLATE_HINT
    )
    if candidate.complement_closed:
        closure = 1.0
    elif candidate.closure_kind in {
        "rgflow",
        "codec_roundtrip",
        "hash_manifest",
        "hash_chain",
        "last_good",
        "rg_address",
        "invariant_witness",
        "route_prior_geometry",
    }:
        closure = 0.9
    elif candidate.closure_kind in {"finite_codon", "topology_route"}:
        closure = 0.8
    elif messenger_exec:
        closure = 0.65
    elif candidate.op_flags & OP_COMPLEMENT:
        closure = 0.35
    else:
        closure = 0.0
    operation_density = bit_count(candidate.op_flags) / len(OP_MASKS)
    role_density = bit_count(candidate.role_flags) / len(ROLE_MASKS)
    degeneracy = clamp(math.log2(candidate.alphabet_size) / candidate.alphabet_size, 0.0, 1.0)
    payload_bits = window_symbols * candidate.bits_per_symbol
    framed_bits = payload_bits + 32
    ascii_bits = window_symbols * 8
    frame_efficiency = 1.0 - (framed_bits / ascii_bits)
    combinatorial_capacity = math.log2(candidate.alphabet_size) * window_symbols / framed_bits
    return ProbeSignature(
        compactness=compactness,
        closure=closure,
        operation_density=operation_density,
        role_density=role_density,
        degeneracy=degeneracy,
        frame_efficiency=frame_efficiency,
        combinatorial_capacity=combinatorial_capacity,
    )


def signature_to_rg_state(signature: ProbeSignature) -> RGState:
    mutation_freedom = 1.0 - signature.closure
    return RGState(
        mu_bin=bin8(mutation_freedom),
        rho_bin=bin8(signature.combinatorial_capacity),
        c_bin=bin8(signature.operation_density),
        m_bin=bin8(signature.frame_efficiency),
        ne_bin=bin8(signature.role_density),
        sig_bin=bin8((signature.closure + signature.degeneracy) / 2.0),
    )


def locally_lawful(state: RGState) -> bool:
    low_mutation_pressure = state.mu_bin <= 4
    enough_capacity = state.rho_bin + state.ne_bin >= 4
    useful_complexity = 1 <= state.c_bin <= 6
    stable_signature = state.sig_bin >= 2
    efficient_frame = state.m_bin >= 2
    return low_mutation_pressure and enough_capacity and useful_complexity and stable_signature and efficient_frame


def coarse_step(state: RGState) -> RGState:
    return RGState(
        mu_bin=max(0, state.mu_bin - 1),
        rho_bin=max(0, min(7, state.rho_bin + (1 if state.sig_bin >= 3 else 0))),
        c_bin=max(0, state.c_bin - (1 if state.c_bin > 5 else 0)),
        m_bin=max(0, min(7, state.m_bin + 1)),
        ne_bin=max(0, min(7, state.ne_bin + 1)),
        sig_bin=max(0, min(7, state.sig_bin + (1 if state.mu_bin <= 3 else 0))),
    )


def rgflow(state: RGState, steps: int) -> tuple[bool, RGState, int]:
    current = state
    depth = 0
    for _ in range(steps):
        if not locally_lawful(current):
            return False, current, depth
        depth += 1
        current = coarse_step(current)
    return locally_lawful(current), current, depth


def score(signature: ProbeSignature, lawful_under_flow: bool, depth: int) -> float:
    base = (
        0.24 * signature.frame_efficiency
        + 0.20 * signature.closure
        + 0.18 * signature.combinatorial_capacity
        + 0.16 * signature.operation_density
        + 0.12 * signature.degeneracy
        + 0.10 * signature.role_density
    )
    return round(base + (0.05 * depth if lawful_under_flow else 0.0), 6)


def evaluate(candidate: SurfaceCandidate, window_symbols: int, steps: int) -> ProbeResult:
    signature = metaprobe(candidate, window_symbols)
    initial_state = signature_to_rg_state(signature)
    lawful_now = locally_lawful(initial_state)
    lawful_under_flow, final_state, depth = rgflow(initial_state, steps)
    usefulness = score(signature, lawful_under_flow, depth)
    if lawful_under_flow and usefulness >= 0.75:
        verdict = "lut_candidate"
    elif lawful_under_flow:
        verdict = "admissible_surface"
    else:
        verdict = "reject_noise_or_bad_tradeoff"
    return ProbeResult(
        candidate=candidate,
        signature=signature,
        initial_state=initial_state,
        final_state=final_state,
        lawful_now=lawful_now,
        lawful_under_flow=lawful_under_flow,
        rg_depth=depth,
        score=usefulness,
        verdict=verdict,
    )


def result_to_dict(result: ProbeResult) -> dict[str, object]:
    return {
        "candidate": asdict(result.candidate),
        "signature": asdict(result.signature),
        "initial_state": asdict(result.initial_state),
        "final_state": asdict(result.final_state),
        "lawful_now": result.lawful_now,
        "lawful_under_flow": result.lawful_under_flow,
        "rg_depth": result.rg_depth,
        "score": result.score,
        "verdict": result.verdict,
    }


def run(max_alphabet: int, window_symbols: int, steps: int, include_synthetic: bool) -> list[ProbeResult]:
    candidates = list(known_candidates())
    candidates.extend(motif_candidates())
    if include_synthetic:
        candidates.extend(synthetic_candidates(max_alphabet))
    results = [evaluate(candidate, window_symbols, steps) for candidate in candidates]
    return sorted(results, key=lambda item: (item.score, item.rg_depth), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-alphabet", type=int, default=16)
    parser.add_argument("--window-symbols", type=int, default=256)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--known-only", action="store_true")
    parser.add_argument("--top", type=int, default=16)
    parser.add_argument("--jsonl", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.max_alphabet < 2 or args.max_alphabet > 64:
        parser.error("--max-alphabet must be in 2..64")
    if args.window_symbols < 1:
        parser.error("--window-symbols must be positive")
    if args.steps < 1 or args.steps > 16:
        parser.error("--steps must be in 1..16")

    results = run(args.max_alphabet, args.window_symbols, args.steps, not args.known_only)
    selected = results[: args.top]
    rows = [result_to_dict(result) for result in selected]

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            if args.jsonl:
                for row in rows:
                    handle.write(json.dumps(row, separators=(",", ":")) + "\n")
            else:
                json.dump(rows, handle, indent=2)

    if args.jsonl:
        for row in rows:
            print(json.dumps(row, separators=(",", ":")))
    else:
        print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
