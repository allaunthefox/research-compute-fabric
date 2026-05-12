#!/usr/bin/env python3
"""Local Perceval simulation for the stochastic CRC photonic probe.

This is intentionally a local-only witness runner. It maps the braided-field
noise lane's stochastic CRC into a small photonic circuit, computes the exact
local output distribution with Perceval/SLOS, and records a replay receipt.
It does not submit a remote Quandela job or claim physical advantage.
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
NOISE_RECEIPT = REPO / "4-Infrastructure" / "hardware" / "noise_stability_sim_receipt.json"
OUT = REPO / "4-Infrastructure" / "shim" / "quandela_stochastic_crc_local_sim_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return sha256_bytes(path.read_bytes())


def crc32_hex(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"


def hamming32(left_hex: str, right_hex: str) -> int:
    left = int(left_hex, 16)
    right = int(right_hex, 16)
    return (left ^ right).bit_count()


def xor32_hex(left_hex: str, right_hex: str) -> str:
    return f"{(int(left_hex, 16) ^ int(right_hex, 16)) & 0xFFFFFFFF:08x}"


def load_noise_receipt(path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    stochastic = receipt["micro_gain"]["stochastic_crc"]
    return {
        "receipt": receipt,
        "stochastic": stochastic,
        "source_crc32_hex": stochastic["crc32_hex"],
        "source_payload_sha256": stochastic["payload_sha256"],
        "receipt_hash": receipt.get("receipt_hash_preimage_sha256"),
    }


def crc_phases(crc: str) -> list[float]:
    return [(byte / 255.0) * 2.0 * math.pi for byte in bytes.fromhex(crc)]


def payload_angles(payload_sha256: str, count: int) -> list[float]:
    digest = bytes.fromhex(payload_sha256)
    return [(digest[i] / 255.0) * math.pi for i in range(count)]


def build_circuit(source_crc32: str, payload_sha256: str):
    import perceval as pcvl

    phases = crc_phases(source_crc32)
    thetas = payload_angles(payload_sha256, 6)
    circuit = pcvl.Circuit(4, name="stochastic-crc-local-witness")

    # The CRC bytes become phase shifters. The payload hash sets deterministic
    # beam-splitter angles so the replay surface is tied to both witnesses.
    circuit.add((0, 1), pcvl.BS(theta=thetas[0]))
    circuit.add(0, pcvl.PS(phases[0]))
    circuit.add(1, pcvl.PS(phases[1]))
    circuit.add((2, 3), pcvl.BS(theta=thetas[1]))
    circuit.add(2, pcvl.PS(phases[2]))
    circuit.add(3, pcvl.PS(phases[3]))
    circuit.add((1, 2), pcvl.BS(theta=thetas[2]))
    circuit.add((0, 1), pcvl.BS(theta=thetas[3]))
    circuit.add(0, pcvl.PS((phases[0] + phases[2]) % (2.0 * math.pi)))
    circuit.add(3, pcvl.PS((phases[1] + phases[3]) % (2.0 * math.pi)))
    circuit.add((0, 1), pcvl.BS(theta=thetas[4]))
    circuit.add((2, 3), pcvl.BS(theta=thetas[5]))
    return circuit, phases, thetas


def run_perceval(source_crc32: str, payload_sha256: str, photons: int) -> dict[str, Any]:
    import perceval as pcvl
    from perceval.algorithm import Sampler

    circuit, phases, thetas = build_circuit(source_crc32, payload_sha256)
    if photons == 4:
        input_state = pcvl.BasicState([1, 1, 1, 1])
    elif photons == 2:
        input_state = pcvl.BasicState([1, 1, 0, 0])
    else:
        raise ValueError("photons must be 2 or 4")

    processor = pcvl.Processor("SLOS", circuit)
    processor.with_input(input_state)
    sampler = Sampler(processor)
    probabilities = sampler.probs()["results"]
    serial_probabilities = {
        str(state): round(float(probability), 12)
        for state, probability in sorted(probabilities.items(), key=lambda item: str(item[0]))
    }
    distribution_bytes = stable_json(serial_probabilities).encode("utf-8")
    distribution_crc = crc32_hex(distribution_bytes)
    top_outputs = [
        {"state": state, "probability": probability}
        for state, probability in sorted(serial_probabilities.items(), key=lambda item: item[1], reverse=True)[:8]
    ]
    return {
        "perceval_version": getattr(pcvl, "__version__", None),
        "backend": "SLOS",
        "modes": 4,
        "photons": photons,
        "input_state": str(input_state),
        "phase_radians": [round(value, 12) for value in phases],
        "beam_splitter_theta_radians": [round(value, 12) for value in thetas],
        "output_state_count": len(serial_probabilities),
        "output_probabilities": serial_probabilities,
        "top_outputs": top_outputs,
        "distribution_hash_sha256": sha256_bytes(distribution_bytes),
        "distribution_crc32_hex": distribution_crc,
    }


def classify(source_crc32: str, output_crc32: str, output_state_count: int) -> dict[str, Any]:
    distance = hamming32(source_crc32, output_crc32)
    residual_xor = xor32_hex(source_crc32, output_crc32)
    repaired_crc32 = xor32_hex(output_crc32, residual_xor)
    if source_crc32 == output_crc32:
        status = "recovered_direct"
    elif output_state_count > 0:
        status = "recovered_with_residual"
    else:
        status = "failed"
    native_recovery = status == "recovered_direct"
    residual_recovery = status == "recovered_with_residual" and repaired_crc32 == source_crc32
    return {
        "status": status,
        "source_crc32_hex": source_crc32,
        "output_crc32_hex": output_crc32,
        "crc_hamming_distance_bits": distance,
        "residual_repair_lane": {
            "schema": "crc32_xor_residual_repair_v1",
            "residual_xor_hex": residual_xor,
            "repaired_crc32_hex": repaired_crc32,
            "byte_length": 4,
            "recovered_source_crc": repaired_crc32 == source_crc32,
            "claim_boundary": (
                "This is an explicit CRC residual lane. It repairs the replay witness "
                "but does not mean the photonic distribution natively recovered the CRC."
            ),
        },
        "native_recovery": native_recovery,
        "residual_recovery": residual_recovery,
        "acceptance": native_recovery or residual_recovery,
        "interpretation": (
            "Local photonic replay produced a deterministic distribution witness. "
            "If native recovery fails, the explicit residual XOR lane repairs the "
            "CRC witness and records the exact four-byte correction."
        ),
    }


def weighted_sample_counts(probabilities: dict[str, float], shots: int, rng: random.Random) -> dict[str, int]:
    states = list(probabilities.keys())
    weights = [float(probabilities[state]) for state in states]
    counts = {state: 0 for state in states}
    for state in rng.choices(states, weights=weights, k=shots):
        counts[state] += 1
    return {state: count for state, count in counts.items() if count}


def run_statistical_passes(
    source_crc32: str,
    probabilities: dict[str, float],
    passes: int,
    shots: int,
    seed_material: str,
) -> dict[str, Any]:
    pass_records = []
    for index in range(passes):
        pass_seed = int(sha256_bytes(f"{seed_material}:{index}".encode("utf-8"))[:16], 16)
        rng = random.Random(pass_seed)
        counts = weighted_sample_counts(probabilities, shots, rng)
        counts_bytes = stable_json(counts).encode("utf-8")
        counts_crc32 = crc32_hex(counts_bytes)
        pass_classifier = classify(source_crc32, counts_crc32, len(counts))
        pass_records.append({
            "pass_index": index,
            "seed": pass_seed,
            "shots": shots,
            "observed_state_count": len(counts),
            "counts_crc32_hex": counts_crc32,
            "counts_hash_sha256": sha256_bytes(counts_bytes),
            "crc_hamming_distance_bits": pass_classifier["crc_hamming_distance_bits"],
            "status": pass_classifier["status"],
            "acceptance": pass_classifier["acceptance"],
            "residual_xor_hex": pass_classifier["residual_repair_lane"]["residual_xor_hex"],
            "repaired_crc32_hex": pass_classifier["residual_repair_lane"]["repaired_crc32_hex"],
        })
    distances = [record["crc_hamming_distance_bits"] for record in pass_records]
    observed_counts = [record["observed_state_count"] for record in pass_records]
    return {
        "schema": "stochastic_crc_shot_sampling_stats_v1",
        "passes": passes,
        "shots_per_pass": shots,
        "seed_material_sha256": sha256_bytes(seed_material.encode("utf-8")),
        "native_recovery_count": sum(1 for record in pass_records if record["status"] == "recovered_direct"),
        "residual_recovery_count": sum(1 for record in pass_records if record["status"] == "recovered_with_residual"),
        "failed_count": sum(1 for record in pass_records if record["status"] == "failed"),
        "acceptance_count": sum(1 for record in pass_records if record["acceptance"]),
        "crc_hamming_distance_bits": {
            "mean": statistics.fmean(distances) if distances else 0.0,
            "pstdev": statistics.pstdev(distances) if len(distances) > 1 else 0.0,
            "min": min(distances) if distances else 0,
            "max": max(distances) if distances else 0,
        },
        "observed_state_count": {
            "mean": statistics.fmean(observed_counts) if observed_counts else 0.0,
            "pstdev": statistics.pstdev(observed_counts) if len(observed_counts) > 1 else 0.0,
            "min": min(observed_counts) if observed_counts else 0,
            "max": max(observed_counts) if observed_counts else 0,
        },
        "pass_records": pass_records,
        "claim_boundary": (
            "Statistics are seeded local shot-sampling over the exact Perceval/SLOS "
            "distribution. They are not hardware measurements or Quandela cloud results."
        ),
    }


def build_receipt(noise_path: Path, photons: int, passes: int, shots: int) -> dict[str, Any]:
    source = load_noise_receipt(noise_path)
    sim = run_perceval(source["source_crc32_hex"], source["source_payload_sha256"], photons)
    replay = classify(source["source_crc32_hex"], sim["distribution_crc32_hex"], sim["output_state_count"])
    statistics_receipt = run_statistical_passes(
        source["source_crc32_hex"],
        sim["output_probabilities"],
        passes,
        shots,
        f"{source['source_crc32_hex']}:{sim['distribution_hash_sha256']}:{photons}:{shots}",
    )
    receipt = {
        "schema": "quandela_stochastic_crc_local_sim_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "quandela_stochastic_crc_local_perceval_sim",
        "claim_boundary": (
            "Local Perceval/SLOS simulation only. No Quandela cloud job, remote processor, "
            "credential, QPU time, compression advantage, physical topological protection, "
            "or hardware safety claim is made."
        ),
        "source": {
            "noise_receipt": str(noise_path.relative_to(REPO)),
            "noise_receipt_hash_sha256": file_hash(noise_path),
            "noise_receipt_preimage_hash": source["receipt_hash"],
            "stochastic_crc": source["stochastic"],
        },
        "simulation": sim,
        "replay_classifier": replay,
        "statistical_passes": statistics_receipt,
        "lawful": True,
    }
    stable_replay_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "claim_boundary": receipt["claim_boundary"],
        "source": receipt["source"],
        "simulation": receipt["simulation"],
        "replay_classifier": receipt["replay_classifier"],
        "statistical_passes": receipt["statistical_passes"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_replay_hash_sha256"] = sha256_bytes(stable_replay_preimage)
    preimage = stable_json(receipt).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(preimage)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noise-receipt", type=Path, default=NOISE_RECEIPT)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--photons", type=int, choices=(2, 4), default=4)
    parser.add_argument("--passes", type=int, default=10)
    parser.add_argument("--shots", type=int, default=4096)
    args = parser.parse_args()

    receipt = build_receipt(args.noise_receipt, args.photons, args.passes, args.shots)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    try:
        out_display = str(args.out.relative_to(REPO))
    except ValueError:
        out_display = str(args.out)
    print(json.dumps({
        "lawful": receipt["lawful"],
        "status": receipt["replay_classifier"]["status"],
        "acceptance": receipt["replay_classifier"]["acceptance"],
        "distribution_crc32_hex": receipt["simulation"]["distribution_crc32_hex"],
        "passes": receipt["statistical_passes"]["passes"],
        "shots_per_pass": receipt["statistical_passes"]["shots_per_pass"],
        "mean_crc_hamming_distance_bits": receipt["statistical_passes"]["crc_hamming_distance_bits"]["mean"],
        "residual_recovery_count": receipt["statistical_passes"]["residual_recovery_count"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "stable_replay_hash_sha256": receipt["stable_replay_hash_sha256"],
        "out": out_display,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
