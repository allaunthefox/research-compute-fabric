#!/usr/bin/env python3
"""Unified nanokernel/metaprobe/compression route selector.

This is a bounded Python shim for the revised GCL path:

    payload -> MS3C/S3C codon -> metaprobe/RGFlow -> LUT route -> compressor

It does not authorize execution. It returns the smallest useful route-prior
decision for the GCL nanokernel to admit/refuse.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import zlib
from dataclasses import asdict, dataclass
from typing import Any

try:
    from .gcl_motif_lut import MOTIFS
    from .matroska_s3c_reduction_gear import make_codon
    from .possibility_space_probe import evaluate
    from .sequence_surface_lut import SURFACES, normalize_sequence, pack_sequence
except ImportError:
    from gcl_motif_lut import MOTIFS
    from matroska_s3c_reduction_gear import make_codon
    from possibility_space_probe import evaluate
    from sequence_surface_lut import SURFACES, normalize_sequence, pack_sequence


@dataclass(frozen=True)
class PayloadProbe:
    raw_bytes: int
    zlib_bytes: int
    zlib_ratio: float
    byte_diversity: float
    entropy: float
    integer_seed: int
    sequence_surface: str | None


@dataclass(frozen=True)
class RouteDecision:
    surface: str
    motif: str
    witness: str
    compressor: str
    rg_lawful: bool
    score: float
    reason: str


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts: dict[int, int] = {}
    for byte in data:
        counts[byte] = counts.get(byte, 0) + 1
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def detect_sequence_surface(text: str) -> str | None:
    clean = "".join(ch for ch in text.upper() if not ch.isspace())
    if not clean:
        return None
    for name in ("dna", "rna", "mrna", "hachimoji", "xna"):
        surface = SURFACES[name]
        try:
            normalize_sequence(surface, clean)
        except ValueError:
            continue
        return name
    return None


def probe_payload(data: bytes) -> PayloadProbe:
    compressed = zlib.compress(data, level=6)
    unique = len(set(data))
    seed = int.from_bytes(data[:8].ljust(8, b"\0"), "big") if data else 0
    text = data.decode("utf-8", errors="ignore")
    return PayloadProbe(
        raw_bytes=len(data),
        zlib_bytes=len(compressed),
        zlib_ratio=round(len(compressed) / max(1, len(data)), 6),
        byte_diversity=round(unique / 256.0, 6),
        entropy=round(shannon_entropy(data), 6),
        integer_seed=seed,
        sequence_surface=detect_sequence_surface(text),
    )


def motif_candidate(name: str):
    motif = MOTIFS[name]
    try:
        from .possibility_space_probe import SurfaceCandidate
    except ImportError:
        from possibility_space_probe import SurfaceCandidate

    return SurfaceCandidate(
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


def choose_route(data: bytes, workload: str = "auto") -> dict[str, Any]:
    probe = probe_payload(data)
    ms3c = make_codon(probe.integer_seed)

    if workload == "recovery" or probe.raw_bytes <= 4:
        decision = RouteDecision(
            surface="binary_control_lane",
            motif="gcl_recovery",
            witness="informaton_bind",
            compressor="none",
            rg_lawful=True,
            score=0.95,
            reason="tiny recovery/control payload",
        )
    elif probe.sequence_surface:
        surface = SURFACES[probe.sequence_surface]
        text = data.decode("utf-8", errors="ignore")
        packed = pack_sequence(surface, text)
        motif = "gcl_compression" if len(packed) < probe.zlib_bytes else "gcl_admission"
        eval_result = evaluate(motif_candidate(motif), window_symbols=max(1, len(text)), steps=4)
        decision = RouteDecision(
            surface=probe.sequence_surface,
            motif=motif,
            witness="informaton_bind",
            compressor=f"{probe.sequence_surface}_bitpack",
            rg_lawful=eval_result.lawful_under_flow,
            score=eval_result.score,
            reason="sequence surface detected by finite alphabet",
        )
    elif probe.zlib_ratio < 0.8 and workload not in {"ms3c", "topology"}:
        eval_result = evaluate(motif_candidate("gcl_compression"), window_symbols=max(1, probe.raw_bytes), steps=4)
        decision = RouteDecision(
            surface="byte_payload",
            motif="gcl_compression",
            witness="informaton_bind",
            compressor="zlib_test_then_delta_gcl",
            rg_lawful=eval_result.lawful_under_flow,
            score=eval_result.score,
            reason="payload has ordinary compression structure",
        )
    elif ms3c.shear >= 144:
        eval_result = evaluate(motif_candidate("ms3c_reduction_gear"), window_symbols=max(1, probe.raw_bytes), steps=4)
        decision = RouteDecision(
            surface="ms3c_shell_codon",
            motif="ms3c_reduction_gear",
            witness="informaton_genome",
            compressor="ms3c_route_prior_then_delta_gcl",
            rg_lawful=eval_result.lawful_under_flow,
            score=eval_result.score,
            reason="high shell shear route-prior",
        )
    else:
        eval_result = evaluate(motif_candidate("gcl_admission"), window_symbols=max(1, probe.raw_bytes), steps=4)
        decision = RouteDecision(
            surface="byte_payload",
            motif="gcl_admission",
            witness="informaton_bind",
            compressor="delta_gcl",
            rg_lawful=eval_result.lawful_under_flow,
            score=eval_result.score,
            reason="default admission before expansion",
        )

    return {
        "v": "unified-compression-route-0.1",
        "claim_status": "route_selection_not_execution_authority",
        "workload": workload,
        "probe": asdict(probe),
        "ms3c_codon": asdict(ms3c),
        "decision": asdict(decision),
        "nanokernel_tuple": {
            "surface": decision.surface,
            "motif": decision.motif,
            "witness": decision.witness,
            "compressor": decision.compressor,
        },
        "gcl_required_gate": [
            "OBSERVE",
            "BIND",
            "ROUTE",
            "SIGMA_CHECK",
            "POLICY_CHECK",
            "DAG_CHECK",
            "VERIFY",
            "RECEIPT",
        ],
    }


def parse_payload(args: argparse.Namespace) -> bytes:
    if args.b64:
        return base64.b64decode(args.b64)
    if args.file:
        return args.file.read()
    return args.payload.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", nargs="?", default="")
    parser.add_argument("--file", type=argparse.FileType("rb"))
    parser.add_argument("--b64")
    parser.add_argument("--workload", default="auto")
    args = parser.parse_args()
    data = parse_payload(args)
    print(json.dumps(choose_route(data, args.workload), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
