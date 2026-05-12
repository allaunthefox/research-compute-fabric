#!/usr/bin/env python3
"""Run substitution auditing over a bounded corpus slice."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import math_logogram_substitution_audit as audit


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
DEFAULT_CORPUS = REPO / "shared-data" / "corpora" / "enwik8"
DEFAULT_RECEIPT = SHIM / "math_logogram_enwik8_slice_substitution_receipt.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chunks(text: str, chunk_chars: int, limit: int) -> list[str]:
    out: list[str] = []
    cursor = 0
    while cursor < len(text) and len(out) < limit:
        piece = text[cursor : cursor + chunk_chars].strip()
        cursor += chunk_chars
        if piece:
            out.append(piece)
    return out


def summarize(tests: list[dict[str, Any]]) -> dict[str, Any]:
    raw_bytes = sum(int(test["compression"]["raw_bytes"]) for test in tests)
    canonical_bytes = sum(int(test["compression"]["canonical_bytes"]) for test in tests)
    payload_bytes = sum(int(test["compression"]["surface_payload_bytes"]) for test in tests)
    json_sidecar = sum(int(test["compression"]["sidecar_bytes_json_compact"]) for test in tests)
    packed_sidecar = sum(int(test["compression"]["sidecar_bytes_packed_estimate"]) for test in tests)
    total_packed = payload_bytes + packed_sidecar
    return {
        "sample_count": len(tests),
        "raw_bytes": raw_bytes,
        "canonical_bytes": canonical_bytes,
        "payload_bytes": payload_bytes,
        "json_sidecar_bytes": json_sidecar,
        "packed_sidecar_estimate_bytes": packed_sidecar,
        "payload_plus_packed_sidecar_estimate_bytes": total_packed,
        "compression_ratio_raw_to_payload": raw_bytes / payload_bytes if payload_bytes else None,
        "compression_ratio_raw_to_payload_plus_packed_sidecar_estimate": (
            raw_bytes / total_packed if total_packed else None
        ),
        "accept_count": sum(test["decision"] == "ACCEPT" for test in tests),
        "hold_count": sum(test["decision"] == "HOLD" for test in tests),
        "quarantine_count": sum(test["decision"] == "QUARANTINE" for test in tests),
        "payload_only_round_trip_count": sum(
            test["round_trip"]["payload_only"] for test in tests
        ),
        "sidecar_round_trip_count": sum(
            test["round_trip"]["with_display_cell_sidecar"] for test in tests
        ),
    }


def build_receipt(corpus: Path, slice_bytes: int, chunk_chars: int, max_chunks: int) -> dict[str, Any]:
    raw = corpus.read_bytes()[:slice_bytes]
    text = raw.decode("utf-8", errors="replace")
    tests = [
        audit.audit_fixture(
            {
                "id": f"enwik8_slice_{index:04d}",
                "kind": "corpus_text",
                "source": chunk,
            }
        )
        for index, chunk in enumerate(chunks(text, chunk_chars, max_chunks))
    ]
    receipt = {
        "schema": "math_logogram_corpus_substitution_benchmark_v1",
        "corpus": str(corpus.relative_to(REPO) if corpus.is_relative_to(REPO) else corpus),
        "corpus_slice_bytes": len(raw),
        "corpus_slice_sha256": sha256_bytes(raw),
        "chunk_chars": chunk_chars,
        "max_chunks": max_chunks,
        "summary": summarize(tests),
        "tests": tests,
        "claim_boundary": (
            "Bounded corpus slice measurement only. This is not a Hutter Prize "
            "submission, not an enwik8 full-corpus result, and not a proof of "
            "compression competitiveness."
        ),
    }
    receipt["receipt_hash"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark logogram substitution on a corpus slice.")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--slice-bytes", type=int, default=8192)
    parser.add_argument("--chunk-chars", type=int, default=160)
    parser.add_argument("--max-chunks", type=int, default=64)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()

    receipt = build_receipt(args.corpus, args.slice_bytes, args.chunk_chars, args.max_chunks)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
