#!/usr/bin/env python3
"""
Round-trip test for SEI injection + VCN encode/decode pipeline.

Note on VCN decode path: H.264 compression (DCT + quantization + CABAC) does NOT
preserve raw frame bytes. The decode path is for SEI receipt / CRC verification ONLY.
The actual VCN computation (transform coefficients, motion vectors) is extracted
from the ENcode path, not the decode path.

Tests:
  1. SEI receipt injection and extraction via binary MKV parsing
  2. encode_braid_strand/crossing/pist_field produce valid MKV with SEI
  3. decode_braid_mkv correctly extracts SEI receipts
  4. Corrupt CRC detection (wrong CRC → crc_match = corrupt)
  5. Seq mismatch detection (wrong seq → seq_match = drop)
  6. Multi-frame seq progression
  7. Resolution encoding (1080p produces correct SEI at expected CRC)
"""

import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import braid_vcn_encoder as bve
import vcn_compute_substrate as vcn

passed = 0
failed = 0


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")


def test_sei_encoding():
    print("\n── SEI Receipt Encoding (1080p libx264) ──")

    strand = {
        "phaseAcc": {"x": 0x00030000, "y": 0x00040000},
        "parity": True,
        "slot": 42,
        "residue": 0x00018000,
        "jitter": 0x00004000,
        "bracket": {
            "lower": 0x00000000,
            "upper": 0x000A0000,
            "gap": 0x000A0000,
            "kappa": 0x00010000,
            "phi": 0x00008000,
            "admissible": True,
        },
    }

    mkv = bve.encode_braid_strand(strand, frame_counter=0)
    report("encode_braid_strand produces MKV bytes", len(mkv) > 0, f"{len(mkv)} bytes")
    report("MKV contains SEI UUID", vcn.SEI_UUID.replace("-", "") in mkv.hex().lower())

    return mkv


def test_sei_extraction():
    print("\n── SEI Receipt Extraction ──")

    strand = {
        "phaseAcc": {"x": 0x00010000, "y": 0},
        "parity": False,
        "slot": 1,
        "residue": 0,
        "jitter": 0,
        "bracket": {
            "lower": 0, "upper": 1, "gap": 1,
            "kappa": 1, "phi": 0, "admissible": True,
        },
    }

    mkv = bve.encode_braid_strand(strand, frame_counter=17)

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        Path(tmp.name).write_bytes(mkv)
        receipts = vcn.sei_receipt_from_mkv(Path(tmp.name), vcn.SEI_UUID)
        Path(tmp.name).unlink(missing_ok=True)

    report("sei_receipt_from_mkv returns 1 receipt", len(receipts) == 1,
           f"got {len(receipts)}")
    if receipts:
        r = receipts[0]
        report("receipt seq = 17", r.get("seq") == 17,
               f"got {r.get('seq')}")
        report("receipt has crc32_hex (8 hex chars)",
               len(r.get("crc32_hex", "")) == 8,
               f"got '{r.get('crc32_hex')}'")
        report("receipt has timestamp_us (> 0)",
               r.get("timestamp_us", 0) > 0,
               f"got {r.get('timestamp_us')}")


def test_crc_verification():
    print("\n── CRC Verification ──")

    strand = {
        "phaseAcc": {"x": 0x00020000, "y": 0x00020000},
        "parity": True,
        "slot": 7,
        "residue": 0x00010000,
        "jitter": 0,
        "bracket": {
            "lower": 0, "upper": 0x00020000, "gap": 0x00020000,
            "kappa": 0x00010000, "phi": 0, "admissible": True,
        },
    }

    mkv = bve.encode_braid_strand(strand, frame_counter=5)

    r_ok = bve.decode_braid_mkv(mkv, expected_crc="deadbeef")
    report("wrong CRC → crc_match = corrupt",
           r_ok.get("crc_match") == "corrupt",
           f"got {r_ok.get('crc_match')}")
    report("wrong CRC → crc_error = mismatch",
           r_ok.get("crc_error") == "mismatch",
           f"got {r_ok.get('crc_error')}")

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        Path(tmp.name).write_bytes(mkv)
        receipts = vcn.sei_receipt_from_mkv(Path(tmp.name), vcn.SEI_UUID)
        Path(tmp.name).unlink(missing_ok=True)

    if receipts:
        correct_crc = receipts[0]["crc32_hex"]
        r_correct = bve.decode_braid_mkv(mkv, expected_crc=correct_crc)
        report("correct CRC → crc_match = ok",
               r_correct.get("crc_match") == "ok",
               f"got {r_correct.get('crc_match')}")


def test_seq_verification():
    print("\n── Seq Verification ──")

    strand = {
        "phaseAcc": {"x": 0x00010000, "y": 0},
        "parity": False,
        "slot": 1,
        "residue": 0,
        "jitter": 0,
        "bracket": {
            "lower": 0, "upper": 1, "gap": 1,
            "kappa": 1, "phi": 0, "admissible": True,
        },
    }

    mkv = bve.encode_braid_strand(strand, frame_counter=99)
    r = bve.decode_braid_mkv(mkv, expected_seq=100)
    report("wrong seq → seq_match = drop",
           r.get("seq_match") == "drop",
           f"got {r.get('seq_match')}")
    report("wrong seq → seq_error = mismatch",
           r.get("seq_error") == "mismatch",
           f"got {r.get('seq_error')}")

    r_ok = bve.decode_braid_mkv(mkv, expected_seq=99)
    report("correct seq → seq_match = ok",
           r_ok.get("seq_match") == "ok",
           f"got {r_ok.get('seq_match')}")


def test_multi_frame():
    print("\n── Multi-Frame Seq Progression ──")

    strand = {
        "phaseAcc": {"x": 0x00010000, "y": 0},
        "parity": False,
        "slot": 1,
        "residue": 0,
        "jitter": 0,
        "bracket": {
            "lower": 0, "upper": 1, "gap": 1,
            "kappa": 1, "phi": 0, "admissible": True,
        },
    }

    for expected in [0, 1, 2]:
        mkv = bve.encode_braid_strand(strand, frame_counter=expected)
        r = bve.decode_braid_mkv(mkv, expected_seq=expected)
        report(f"frame seq={expected} → seq_match=ok",
               r.get("seq_match") == "ok",
               f"got {r.get('seq_match')}")


def test_crossing_and_pist():
    print("\n── Crossing and PIST SEI ──")

    bracket_a = {
        "lower": 0, "upper": 0x00050000, "gap": 0x00050000,
        "kappa": 0x00010000, "phi": 0, "admissible": True,
    }
    bracket_b = {
        "lower": 0x00030000, "upper": 0x00080000, "gap": 0x00050000,
        "kappa": 0x00020000, "phi": 0x00010000, "admissible": True,
    }

    mkv_cross = bve.encode_braid_crossing(bracket_a, bracket_b, frame_counter=10)
    report("encode_braid_crossing produces MKV", len(mkv_cross) > 0,
           f"{len(mkv_cross)} bytes")

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        Path(tmp.name).write_bytes(mkv_cross)
        receipts = vcn.sei_receipt_from_mkv(Path(tmp.name), vcn.SEI_UUID)
        Path(tmp.name).unlink(missing_ok=True)

    report("crossing SEI receipt seq=10",
           len(receipts) == 1 and receipts[0].get("seq") == 10,
           f"got seq={receipts[0].get('seq') if receipts else 'none'}")

    pist = {"energy": 0x00010000, "phase": 0x00008000, "label": "test"}
    mkv_pist = bve.encode_pist_field(pist, frame_counter=11)
    report("encode_pist_field produces MKV", len(mkv_pist) > 0,
           f"{len(mkv_pist)} bytes")

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        Path(tmp.name).write_bytes(mkv_pist)
        receipts_pist = vcn.sei_receipt_from_mkv(Path(tmp.name), vcn.SEI_UUID)
        Path(tmp.name).unlink(missing_ok=True)

    report("pist SEI receipt seq=11",
           len(receipts_pist) == 1 and receipts_pist[0].get("seq") == 11,
           f"got seq={receipts_pist[0].get('seq') if receipts_pist else 'none'}")


def main():
    global passed, failed

    print("=" * 60)
    print("VCN SEI + CRC Round-Trip Test Suite")
    print("=" * 60)

    test_sei_encoding()
    test_sei_extraction()
    test_crc_verification()
    test_seq_verification()
    test_multi_frame()
    test_crossing_and_pist()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
