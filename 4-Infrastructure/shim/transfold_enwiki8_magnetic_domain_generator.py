#!/usr/bin/env python3
"""Generate a transfold adaptation from an enwiki8 slice into magnetic-domain equations.

The generator treats byte-stream statistics as a signal surface and maps them
into a magnetic-domain analogue:

    information pressure -> applied field H
    byte-transition structure -> susceptibility chi
    repeated-state memory -> remanence R
    threshold overflow -> hysteresis / heat-loss channel

This is a stress-test generator, not a compressor and not a physics claim.  It
is meant to make the cross-domain response-family framework executable on a
real or enwiki8-like byte slice and leave a receipt for later comparison.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "transfold_enwiki8_magnetic_domain_generator_receipt.json"
CURRICULUM = SHIM / "transfold_enwiki8_magnetic_domain_generator_curriculum.jsonl"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
D_F = math.log(2.0) / math.log(PHI)
PHI_GAIN = PHI**D_F


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def transition_rate(data: bytes) -> float:
    if len(data) < 2:
        return 0.0
    changes = sum(1 for a, b in zip(data, data[1:]) if a != b)
    return changes / (len(data) - 1)


def repetition_rate(data: bytes, ngram: int = 4) -> float:
    if len(data) < ngram:
        return 0.0
    total = len(data) - ngram + 1
    counts: dict[bytes, int] = collections.Counter(
        data[i : i + ngram] for i in range(total)
    )
    repeated = sum(c - 1 for c in counts.values() if c > 1)
    return repeated / total


def printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    printable = sum(1 for b in data if b in (9, 10, 13) or 32 <= b <= 126)
    return printable / len(data)


def chunk_bytes(data: bytes, chunk_size: int, limit: int | None) -> list[bytes]:
    chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]
    if limit is not None:
        chunks = chunks[:limit]
    return [c for c in chunks if c]


def local_fallback_bytes(target_bytes: int) -> tuple[bytes, dict[str, Any]]:
    """Build a deterministic text fallback when enwiki8 is not present locally."""
    candidates = [
        REPO / "docs" / "rainbow_raccoon_compiler_integration.md",
        REPO / "docs" / "compression_signal_shaping_synthesis.md",
        REPO
        / "6-Documentation"
        / "tiddlywiki-local"
        / "wiki"
        / "tiddlers"
        / "Transfolding.tid",
        REPO / "4-Infrastructure" / "shim" / "multi_domain_adaptive_cognitive_load.md",
    ]
    parts: list[bytes] = []
    used: list[dict[str, Any]] = []
    for path in candidates:
        if path.exists():
            data = path.read_bytes()
            parts.append(data)
            used.append({"path": rel(path), "bytes": len(data), "sha256": sha256_bytes(data)})
    seed = b"\n\n".join(parts) or (
        b"enwiki8-like fallback text: transfold response family overflow magnetic domain\n"
    )
    repeats = max(1, math.ceil(target_bytes / len(seed)))
    data = (seed * repeats)[:target_bytes]
    return data, {
        "source_mode": "fallback_local_text_not_enwiki8",
        "claim_boundary": "Stress-test exercised byte-slice path; not a real enwiki8 measurement.",
        "fallback_sources": used,
    }


def find_default_source() -> Path | None:
    candidates = [
        REPO / "enwiki8",
        REPO / "data" / "enwiki8",
        REPO / "shared-data" / "enwiki8",
        REPO / "5-Applications" / "hutter_prize" / "data" / "enwiki8",
        REPO / "5-Applications" / "hutter_prize" / "enwiki8",
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def read_source(path: Path | None, slice_bytes: int) -> tuple[bytes, dict[str, Any]]:
    if path is None:
        default = find_default_source()
        path = default
    if path is None:
        return local_fallback_bytes(slice_bytes)
    data = path.read_bytes()[:slice_bytes]
    return data, {
        "source_mode": "real_file",
        "path": rel(path),
        "available_bytes": path.stat().st_size,
        "slice_bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def response_family(x: float, family: str, theta: dict[str, float]) -> float:
    x = max(0.0, x)
    if family == "logarithmic":
        return math.log1p(theta.get("beta", 1.0) * x)
    if family == "hill":
        k = max(theta.get("k", 1.0), 1e-9)
        n = max(theta.get("n", 2.0), 1e-9)
        return (x**n) / (k**n + x**n)
    if family == "michaelis_menten":
        vmax = theta.get("vmax", 1.0)
        km = max(theta.get("km", 1.0), 1e-9)
        return (vmax * x) / (km + x)
    if family == "power":
        return x ** theta.get("alpha", 0.5)
    raise ValueError(f"unknown response family: {family}")


def overflow_gate(load: float, threshold: float, gamma: float, thermal_scale: float) -> float:
    if load <= threshold:
        return 1.0
    return math.exp(-gamma * (load - threshold) / max(thermal_scale, 1e-9))


def magnetic_domain_projection(
    chunk: bytes,
    index: int,
    capacity_threshold: float,
    coercive_threshold: float,
) -> dict[str, Any]:
    entropy_bits = shannon_entropy(chunk)
    normalized_entropy = entropy_bits / 8.0
    transitions = transition_rate(chunk)
    repeats = repetition_rate(chunk)
    printable = printable_ratio(chunk)

    # Load is a bounded signal-pressure prior.  Entropy is demand, transitions
    # are field agitation, and repeated n-grams are memory/remanence.
    information_load = (
        response_family(normalized_entropy, "logarithmic", {"beta": 2.0})
        + response_family(transitions, "michaelis_menten", {"vmax": 1.0, "km": 0.35})
        + response_family(1.0 - repeats, "power", {"alpha": 0.6})
    ) * PHI_GAIN

    gate = overflow_gate(information_load, capacity_threshold, gamma=1.25, thermal_scale=0.9)
    overflow = max(0.0, information_load - capacity_threshold)

    h_field = information_load
    chi_susceptibility = response_family(transitions, "hill", {"k": 0.55, "n": 2.0})
    remanence = response_family(repeats, "michaelis_menten", {"vmax": 1.0, "km": 0.08})
    coercive_loss = max(0.0, h_field - coercive_threshold)
    magnetization = sigmoid(
        (chi_susceptibility * h_field + remanence - 0.5 * coercive_loss) * gate
    )
    heat_loss = overflow * (1.0 - gate)
    domain_wall_pressure = abs(transitions - repeats) * PHI_GAIN

    return {
        "chunk_index": index,
        "bytes": len(chunk),
        "sha256": sha256_bytes(chunk),
        "features": {
            "entropy_bits_per_byte": entropy_bits,
            "normalized_entropy": normalized_entropy,
            "transition_rate": transitions,
            "repetition_rate_4gram": repeats,
            "printable_ratio": printable,
        },
        "magnetic_domain": {
            "information_load": information_load,
            "overflow_gate": gate,
            "overflow": overflow,
            "H_field": h_field,
            "chi_susceptibility": chi_susceptibility,
            "remanence": remanence,
            "coercive_loss": coercive_loss,
            "domain_wall_pressure": domain_wall_pressure,
            "magnetization_M": magnetization,
            "heat_loss": heat_loss,
        },
        "equation_instance": (
            "M_i = sigmoid(((chi_i * H_i) + R_i - 0.5 * C_loss_i) * G_over_i); "
            "H_i = L_info_i; "
            "L_info_i = phi^D_f * (log(1+2H_entropy_i) + MM(T_i;1,0.35) + P(1-R4_i;0.6))"
        ),
        "status": "overflow" if overflow > 0 else "within_capacity",
    }


def aggregate(chunks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(chunks)
    if not rows:
        return {}
    fields = [
        "information_load",
        "overflow_gate",
        "overflow",
        "H_field",
        "chi_susceptibility",
        "remanence",
        "coercive_loss",
        "domain_wall_pressure",
        "magnetization_M",
        "heat_loss",
    ]
    out: dict[str, Any] = {"chunk_count": len(rows)}
    for field in fields:
        values = [float(r["magnetic_domain"][field]) for r in rows]
        out[field] = {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
        }
    out["overflow_chunk_count"] = sum(1 for r in rows if r["status"] == "overflow")
    out["within_capacity_chunk_count"] = len(rows) - out["overflow_chunk_count"]
    return out


def threshold_sweep(
    projections: list[dict[str, Any]], thresholds: list[float], thermal_scale: float = 0.9
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    loads = [float(row["magnetic_domain"]["information_load"]) for row in projections]
    for threshold in thresholds:
        gates = [overflow_gate(load, threshold, gamma=1.25, thermal_scale=thermal_scale) for load in loads]
        overflows = [max(0.0, load - threshold) for load in loads]
        heat = [overflow * (1.0 - gate) for overflow, gate in zip(overflows, gates)]
        rows.append(
            {
                "capacity_threshold": threshold,
                "overflow_chunk_count": sum(1 for value in overflows if value > 0),
                "mean_overflow": sum(overflows) / len(overflows) if overflows else 0.0,
                "mean_overflow_gate": sum(gates) / len(gates) if gates else 1.0,
                "mean_heat_loss": sum(heat) / len(heat) if heat else 0.0,
            }
        )
    return rows


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    source_path = Path(args.input).expanduser().resolve() if args.input else None
    data, source = read_source(source_path, args.slice_bytes)
    chunks = chunk_bytes(data, args.chunk_size, args.max_chunks)
    projections = [
        magnetic_domain_projection(c, i, args.capacity_threshold, args.coercive_threshold)
        for i, c in enumerate(chunks)
    ]

    receipt: dict[str, Any] = {
        "schema": "transfold_enwiki8_magnetic_domain_generator_v1",
        "runner": rel(Path(__file__).resolve()),
        "purpose": (
            "Stress-test the transfold adaptation framework by converting a byte "
            "slice into magnetic-domain equation instances with response-family "
            "selection and threshold overflow."
        ),
        "source": source,
        "parameters": {
            "slice_bytes_requested": args.slice_bytes,
            "chunk_size": args.chunk_size,
            "max_chunks": args.max_chunks,
            "capacity_threshold": args.capacity_threshold,
            "coercive_threshold": args.coercive_threshold,
            "D_f": D_F,
            "lambda_phi": PHI,
            "phi_gain": PHI_GAIN,
        },
        "transfold_map": {
            "source_domain": "byte_stream_signal",
            "target_domain": "magnetic_domain_equation",
            "field_mapping": {
                "entropy": "field demand / information pressure",
                "byte_transition_rate": "domain agitation / susceptibility driver",
                "repeated_4grams": "remanence / memory channel",
                "capacity_overflow": "hysteresis heat-loss channel",
            },
            "core_equations": {
                "signal_load": (
                    "L_info_i = phi^D_f * (log(1 + 2 h_i) + MM(t_i;1,0.35) + "
                    "(1 - r_i)^0.6)"
                ),
                "overflow_gate": (
                    "G_over_i = 1 if L_info_i <= L_threshold else "
                    "exp(-1.25 * (L_info_i - L_threshold) / 0.9)"
                ),
                "magnetic_projection": (
                    "M_i = sigmoid(((chi_i H_i) + R_i - 0.5 C_loss_i) * G_over_i)"
                ),
                "heat_loss": "Q_i = max(0, L_info_i - L_threshold) * (1 - G_over_i)",
            },
        },
        "chunk_projections": projections,
        "aggregate": aggregate(projections),
        "stress_sweep": threshold_sweep(
            projections,
            [
                max(0.0, args.capacity_threshold - 0.75),
                args.capacity_threshold,
                args.capacity_threshold + 0.75,
                args.capacity_threshold + 1.25,
                args.capacity_threshold + 2.0,
            ],
        ),
        "claim_boundary": (
            "This receipt maps byte-signal statistics into a magnetic-domain analogue. "
            "It is a stress-test and routing prior, not a claim that text data is a "
            "literal magnetic material."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "transfold_byte_signal_to_magnetic_domain",
            "input": "enwiki8 byte chunk statistics",
            "target": "H, chi, remanence, magnetization, overflow, heat_loss",
        },
        {
            "task": "detect_capacity_overflow",
            "input": "information_load and capacity_threshold",
            "target": "overflow_gate plus hysteresis heat-loss channel",
        },
        {
            "task": "preserve_claim_boundary",
            "input": receipt["source"]["source_mode"],
            "target": receipt["claim_boundary"],
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to enwiki8 or another byte corpus slice.")
    parser.add_argument("--slice-bytes", type=int, default=65536)
    parser.add_argument("--chunk-size", type=int, default=4096)
    parser.add_argument("--max-chunks", type=int, default=16)
    parser.add_argument("--capacity-threshold", type=float, default=3.25)
    parser.add_argument("--coercive-threshold", type=float, default=2.6)
    parser.add_argument("--out", type=Path, default=OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    receipt = build_receipt(args)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(args.out),
                "curriculum": rel(CURRICULUM),
                "receipt_hash": receipt["receipt_hash"],
                "source_mode": receipt["source"]["source_mode"],
                "chunk_count": receipt["aggregate"]["chunk_count"],
                "overflow_chunk_count": receipt["aggregate"]["overflow_chunk_count"],
                "mean_magnetization": receipt["aggregate"]["magnetization_M"]["mean"],
                "mean_heat_loss": receipt["aggregate"]["heat_loss"]["mean"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
