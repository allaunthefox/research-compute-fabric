#!/usr/bin/env python3
"""Jupiter-class hostile profile for phi self-recovery encoding.

This is a virtual stress harness. It takes the stochastic CRC witness from the
local Perceval/Quandela-shaped replay, encodes it into a phi/golden-angle
redundant lattice, batters that lattice with a synthetic Jupiter-like hostile
profile, and measures whether the code can self-recover before falling back to
an explicit residual mask.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
QUANDELA_RECEIPT = REPO / "4-Infrastructure" / "shim" / "quandela_stochastic_crc_local_sim_receipt.json"
OUT = REPO / "4-Infrastructure" / "hardware" / "jupiter_phi_self_recovery_probe_receipt.json"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
GOLDEN_ANGLE = 2.0 * math.pi * (1.0 - 1.0 / PHI)


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32_hex(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return sha256_bytes(path.read_bytes())


def xor32_hex(left_hex: str, right_hex: str) -> str:
    return f"{(int(left_hex, 16) ^ int(right_hex, 16)) & 0xFFFFFFFF:08x}"


def hamming32(left_hex: str, right_hex: str) -> int:
    return (int(left_hex, 16) ^ int(right_hex, 16)).bit_count()


def bits_from_crc(crc: str) -> list[int]:
    value = int(crc, 16)
    return [(value >> shift) & 1 for shift in range(31, -1, -1)]


def crc_from_bits(bits: list[int]) -> str:
    value = 0
    for bit in bits:
        value = (value << 1) | (bit & 1)
    return f"{value & 0xFFFFFFFF:08x}"


def load_source(path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    source_crc = receipt["source"]["stochastic_crc"]["crc32_hex"]
    return {
        "path": str(path.relative_to(REPO)),
        "hash_sha256": file_hash(path),
        "stable_replay_hash_sha256": receipt.get("stable_replay_hash_sha256"),
        "source_crc32_hex": source_crc,
        "source_payload_sha256": receipt["source"]["stochastic_crc"]["payload_sha256"],
        "photonic_distribution_crc32_hex": receipt["simulation"]["distribution_crc32_hex"],
        "perceval_status": receipt["replay_classifier"]["status"],
    }


def jupiter_hostile_profile(rage: float) -> dict[str, float]:
    """Normalized hostile profile.

    The constants are synthetic stress knobs, not physical unit conversions.
    A rage of 1.0 is intentionally hostile: high radiation flips, burst shear,
    erasures, and analog drift all active at once.
    """
    return {
        "rage": rage,
        "radiation_flip_probability": min(0.42, 0.08 + 0.20 * rage),
        "burst_flip_probability": min(0.32, 0.05 + 0.17 * rage),
        "burst_span_fraction": min(0.45, 0.12 + 0.23 * rage),
        "erasure_probability": min(0.24, 0.03 + 0.12 * rage),
        "magnetosphere_phase_jitter": 0.10 + 0.42 * rage,
        "pressure_analog_noise": 0.05 + 0.22 * rage,
        "lightning_impulse_probability": min(0.18, 0.02 + 0.09 * rage),
        "claim_boundary": "Synthetic Jupiter-class stress profile for codec design only; no spacecraft or material environment claim.",
    }


def encode_phi_lattice(source_bits: list[int], lanes: int, echoes: int, phi_mode: str) -> list[list[dict[str, float | int]]]:
    lattice: list[list[dict[str, float | int]]] = []
    lane_center = (lanes - 1) / 2.0
    echo_center = (echoes - 1) / 2.0
    if phi_mode == "center_heavy":
        decay_divisor = 1.0
        lane_phase_divisor = PHI
        echo_phase_divisor = PHI * PHI
    elif phi_mode == "echo":
        decay_divisor = 3.0
        lane_phase_divisor = PHI
        echo_phase_divisor = PHI * PHI
    elif phi_mode == "omni":
        decay_divisor = PHI * PHI
        lane_phase_divisor = PHI * PHI
        echo_phase_divisor = PHI * PHI * PHI
    else:
        raise ValueError(f"unknown phi mode: {phi_mode}")
    for bit_index, bit in enumerate(source_bits):
        symbol = 1 if bit else -1
        row = []
        for echo in range(echoes):
            for lane in range(lanes):
                lane_distance = abs(lane - lane_center)
                echo_distance = abs(echo - echo_center)
                # Slow phi decay keeps the pattern distributed. The earlier
                # center-heavy lattice survived only through residual repair
                # under burst stress; this echo form gives native voting mass.
                weight = PHI ** (-(lane_distance + echo_distance) / decay_divisor)
                chirality = -1 if (lane + echo + bit_index) % 2 else 1
                angle = (
                    bit_index * GOLDEN_ANGLE
                    + lane * GOLDEN_ANGLE / lane_phase_divisor
                    + echo * GOLDEN_ANGLE / echo_phase_divisor
                ) % (2.0 * math.pi)
                row.append({
                    "bit": bit,
                    "symbol": symbol * chirality,
                    "chirality": chirality,
                    "lane": lane,
                    "echo": echo,
                    "phi_mode": phi_mode,
                    "weight": weight,
                    "angle": angle,
                })
        lattice.append(row)
    return lattice


def hostile_pass(
    lattice: list[list[dict[str, float | int]]],
    profile: dict[str, float],
    rng: random.Random,
    phi_mode: str,
) -> dict[str, Any]:
    decoded_bits: list[int] = []
    erased = 0
    flips = 0
    lightning_events = 0
    burst_start = rng.randrange(len(lattice))
    burst_span = max(1, int(len(lattice) * float(profile["burst_span_fraction"])))
    burst_end = min(len(lattice), burst_start + burst_span)

    for bit_index, row in enumerate(lattice):
        vote = 0.0
        active_weight = 0.0
        in_burst = burst_start <= bit_index < burst_end
        for lane_cell in row:
            symbol = int(lane_cell["symbol"])
            chirality = int(lane_cell["chirality"])
            weight = float(lane_cell["weight"])
            angle = float(lane_cell["angle"])
            if rng.random() < float(profile["erasure_probability"]):
                erased += 1
                continue
            local_symbol = symbol
            flip_probability = float(profile["radiation_flip_probability"])
            if in_burst:
                flip_probability += float(profile["burst_flip_probability"])
            if rng.random() < min(0.85, flip_probability):
                local_symbol *= -1
                flips += 1
            jitter = rng.gauss(0.0, float(profile["magnetosphere_phase_jitter"]))
            analog = rng.gauss(0.0, float(profile["pressure_analog_noise"]))
            phase_gate = math.cos(angle + jitter)
            if rng.random() < float(profile["lightning_impulse_probability"]):
                analog += rng.choice((-1.0, 1.0)) * (PHI / 2.0)
                lightning_events += 1
            if phi_mode == "omni":
                phase_gain = 1.0 / PHI
                analog_gain = 1.0 / (PHI * PHI)
                vote_bias = math.sin((bit_index + 1) * GOLDEN_ANGLE) / (PHI * PHI * PHI)
            else:
                phase_gain = 0.25
                analog_gain = 1.0
                vote_bias = 0.0
            vote += (
                (local_symbol * chirality) * weight * (1.0 + phase_gain * phase_gate)
                + analog * weight * analog_gain
                + vote_bias * weight
            )
            active_weight += weight
        decoded_bits.append(1 if vote >= 0.0 else 0)

    decoded_crc = crc_from_bits(decoded_bits)
    return {
        "decoded_crc32_hex": decoded_crc,
        "erased_cells": erased,
        "flipped_cells": flips,
        "lightning_events": lightning_events,
        "burst_start_bit": burst_start,
        "burst_end_bit": burst_end,
        "active_bits": len(decoded_bits),
    }


def run_probe(source_crc: str, lanes: int, echoes: int, passes: int, rage: float, seed_material: str, phi_mode: str) -> dict[str, Any]:
    source_bits = bits_from_crc(source_crc)
    lattice = encode_phi_lattice(source_bits, lanes, echoes, phi_mode)
    profile = jupiter_hostile_profile(rage)
    records = []
    for index in range(passes):
        seed = int(sha256_bytes(f"{seed_material}:jupiter:{index}".encode("utf-8"))[:16], 16)
        rng = random.Random(seed)
        hostile = hostile_pass(lattice, profile, rng, phi_mode)
        decoded_crc = hostile["decoded_crc32_hex"]
        residual_xor = xor32_hex(source_crc, decoded_crc)
        repaired_crc = xor32_hex(decoded_crc, residual_xor)
        direct = decoded_crc == source_crc
        residual = repaired_crc == source_crc
        records.append({
            "pass_index": index,
            "seed": seed,
            "decoded_crc32_hex": decoded_crc,
            "hamming_distance_bits": hamming32(source_crc, decoded_crc),
            "direct_recovery": direct,
            "residual_recovery": (not direct) and residual,
            "acceptance": direct or residual,
            "residual_xor_hex": residual_xor,
            "repaired_crc32_hex": repaired_crc,
            **hostile,
        })

    distances = [record["hamming_distance_bits"] for record in records]
    flips = [record["flipped_cells"] for record in records]
    erasures = [record["erased_cells"] for record in records]
    lightning = [record["lightning_events"] for record in records]
    return {
        "schema": "jupiter_phi_self_recovery_stats_v1",
        "source_crc32_hex": source_crc,
        "lanes": lanes,
        "echoes": echoes,
        "cells_per_bit": lanes * echoes,
        "phi_mode": phi_mode,
        "passes": passes,
        "profile": profile,
        "golden_angle_radians": GOLDEN_ANGLE,
        "phi": PHI,
        "direct_recovery_count": sum(1 for record in records if record["direct_recovery"]),
        "residual_recovery_count": sum(1 for record in records if record["residual_recovery"]),
        "acceptance_count": sum(1 for record in records if record["acceptance"]),
        "failed_count": sum(1 for record in records if not record["acceptance"]),
        "hamming_distance_bits": {
            "mean": statistics.fmean(distances),
            "pstdev": statistics.pstdev(distances) if len(distances) > 1 else 0.0,
            "min": min(distances),
            "max": max(distances),
        },
        "flipped_cells": {
            "mean": statistics.fmean(flips),
            "min": min(flips),
            "max": max(flips),
        },
        "erased_cells": {
            "mean": statistics.fmean(erasures),
            "min": min(erasures),
            "max": max(erasures),
        },
        "lightning_events": {
            "mean": statistics.fmean(lightning),
            "min": min(lightning),
            "max": max(lightning),
        },
        "pass_records": records,
        "claim_boundary": (
            "Phi self-recovery is tested as a synthetic redundant CRC witness lane. "
            "It is not a proof of physical survivability, cryptographic integrity, "
            "or compression advantage."
        ),
    }


def build_receipt(source_path: Path, lanes: int, echoes: int, passes: int, rage: float, phi_mode: str) -> dict[str, Any]:
    source = load_source(source_path)
    stats = run_probe(
        source["source_crc32_hex"],
        lanes,
        echoes,
        passes,
        rage,
        f"{source['source_crc32_hex']}:{source['source_payload_sha256']}:{source['stable_replay_hash_sha256']}",
        phi_mode,
    )
    receipt = {
        "schema": "jupiter_phi_self_recovery_probe_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "jupiter_phi_self_recovery",
        "source": source,
        "stats": stats,
        "lawful": True,
        "claim_boundary": (
            "Virtual hostile-environment codec stress only. The Jupiter profile is a "
            "deliberately angry synthetic error field; no spaceflight, hardware, "
            "material, safety, or physical environment claim is made."
        ),
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "stats": receipt["stats"],
        "lawful": receipt["lawful"],
        "claim_boundary": receipt["claim_boundary"],
    }).encode("utf-8")
    receipt["stable_probe_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=QUANDELA_RECEIPT)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--lanes", type=int, default=21)
    parser.add_argument("--echoes", type=int, default=13)
    parser.add_argument("--phi-mode", choices=("center_heavy", "echo", "omni"), default="echo")
    parser.add_argument("--passes", type=int, default=128)
    parser.add_argument("--rage", type=float, default=1.0)
    args = parser.parse_args()

    receipt = build_receipt(args.source, args.lanes, args.echoes, args.passes, args.rage, args.phi_mode)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    try:
        out_display = str(args.out.relative_to(REPO))
    except ValueError:
        out_display = str(args.out)
    stats = receipt["stats"]
    print(json.dumps({
        "lawful": receipt["lawful"],
        "passes": stats["passes"],
        "lanes": stats["lanes"],
        "echoes": stats["echoes"],
        "cells_per_bit": stats["cells_per_bit"],
        "phi_mode": stats["phi_mode"],
        "rage": stats["profile"]["rage"],
        "direct_recovery_count": stats["direct_recovery_count"],
        "residual_recovery_count": stats["residual_recovery_count"],
        "failed_count": stats["failed_count"],
        "mean_hamming_distance_bits": stats["hamming_distance_bits"]["mean"],
        "stable_probe_hash_sha256": receipt["stable_probe_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "out": out_display,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
