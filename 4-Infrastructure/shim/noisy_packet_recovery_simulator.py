#!/usr/bin/env python3
"""Local noisy recovery simulator for the FCL1/FCS1 promotion ladder.

This deliberately stays local. Quandela remains a manually gated remote noisy
probe; this script establishes the fail-closed behaviors first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import finance_claim_lut_harness as harness


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"


def with_recomputed_crc(blob: bytes) -> bytes:
    body = blob[:-4]
    return body + harness.crc32_bytes(body).to_bytes(4, "big")


def decode_status(fcl1: bytes, fcs1: bytes, symbol_lut: dict[str, Any], codebook: dict[str, int]) -> dict[str, Any]:
    try:
        sidecar = harness.decode_fcs1(fcs1)
        packet = harness.decode_fcl1(fcl1, sidecar, symbol_lut, codebook)
        return {"ok": True, "canonical_hash": harness.sha256_bytes(harness.canonical_bytes(packet)), "error": None}
    except Exception as exc:
        return {"ok": False, "canonical_hash": None, "error": str(exc)}


def run_simulation(samples: list[dict[str, Any]], out: Path) -> dict[str, Any]:
    symbol_lut = harness.build_symbol_lut()
    type_lut = harness.build_typesetting_lut(symbol_lut)
    codebook = harness.symbol_codebook(symbol_lut)
    sample = samples[0]
    encoded = harness.encode_packet(sample)
    fcl1 = harness.encode_fcl1(encoded["compressed"], codebook)
    fcs1 = harness.encode_fcs1(encoded["sidecar"])
    canonical_hash = harness.sha256_bytes(harness.canonical_bytes(sample))

    cases: list[dict[str, Any]] = []

    mutated = bytearray(fcl1)
    mutated[8] ^= 0x01
    cases.append({"case": "fcl1_bit_flip_without_crc_repair", "expected": "reject", "result": decode_status(bytes(mutated), fcs1, symbol_lut, codebook)})

    mutated = bytearray(fcs1)
    mutated[-8] ^= 0x01
    cases.append({"case": "fcs1_literal_byte_flip_without_crc_repair", "expected": "reject", "result": decode_status(fcl1, bytes(mutated), symbol_lut, codebook)})

    mutated = bytearray(fcs1)
    mutated[5] = max(0, mutated[5] - 1)
    mutated = bytearray(with_recomputed_crc(bytes(mutated)))
    cases.append({"case": "fcs1_missing_literal_lane_with_recomputed_outer_crc", "expected": "reject", "result": decode_status(fcl1, bytes(mutated), symbol_lut, codebook)})

    mutated = bytearray(fcl1)
    mutated[8] = 0xFF
    mutated = bytearray(with_recomputed_crc(bytes(mutated)))
    cases.append({"case": "fcl1_enum_code_mutation_with_recomputed_crc", "expected": "reject", "result": decode_status(bytes(mutated), fcs1, symbol_lut, codebook)})

    original_orientation_hash = harness.sha256_bytes(json.dumps(type_lut, sort_keys=True).encode("utf-8"))
    mutated_type_lut = json.loads(json.dumps(type_lut))
    first_symbol = sorted(mutated_type_lut["entries"])[0]
    mutated_type_lut["entries"][first_symbol]["orientation_code"] ^= 0x10
    mutated_type_lut["entries"][first_symbol]["orientation"] = harness.unpack_orientation(mutated_type_lut["entries"][first_symbol]["orientation_code"])
    mutated_orientation_hash = harness.sha256_bytes(json.dumps(mutated_type_lut, sort_keys=True).encode("utf-8"))
    cases.append(
        {
            "case": "orientation_byte_mutation",
            "expected": "record_hash_mismatch",
            "result": {
                "ok": original_orientation_hash != mutated_orientation_hash,
                "original_typesetting_hash": original_orientation_hash,
                "mutated_typesetting_hash": mutated_orientation_hash,
                "mutated_symbol": first_symbol,
            },
        }
    )

    unknown = dict(sample)
    unknown["currency"] = "ZZZ"
    unknown_encoded = harness.encode_packet(unknown)
    cases.append(
        {
            "case": "unknown_enum_sidecar_fallback",
            "expected": "fallback",
            "result": {
                "ok": any(
                    item["field_symbol_id"] == harness.FIELD_SYMBOLS["currency"][0] and item["value"]["type"] == "literal_ref"
                    for item in unknown_encoded["compressed"]["fields"]
                ),
                "field": "currency",
                "value": "ZZZ",
            },
        }
    )

    receipt = {
        "schema": "noisy_packet_recovery_simulator_receipt_v1",
        "sample_id": sample["id"],
        "canonical_hash": canonical_hash,
        "case_count": len(cases),
        "cases": cases,
        "lawful": all(case["result"].get("ok") is (case["expected"] in {"fallback", "record_hash_mismatch"}) or (not case["result"].get("ok") and case["expected"] == "reject") for case in cases),
        "claim_boundary": "local perturbation simulator only; not Quandela execution or measured noisy-substrate recovery",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path)
    parser.add_argument("--out", type=Path, default=SHIM / "noisy_packet_recovery_simulator_receipt.json")
    args = parser.parse_args()
    print(json.dumps(run_simulation(harness.load_samples(args.samples), args.out), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
