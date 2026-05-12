#!/usr/bin/env python3
"""Pack math logogram substitution sidecars into a deterministic binary stream."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SHIM = Path(__file__).resolve().parent
DEFAULT_AUDIT = SHIM / "math_logogram_substitution_audit_receipt.json"
DEFAULT_BIN = SHIM / "math_logogram_sidecar_stream.bin"
DEFAULT_RECEIPT = SHIM / "math_logogram_sidecar_packer_receipt.json"

OPCODES = {
    "select_candidate": 0x01,
    "literal_token": 0x02,
    "append_truncated_cell": 0x03,
}

KIND_CODES = {
    "command": 0x01,
    "identifier": 0x02,
    "number": 0x03,
    "symbol": 0x04,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def byte_value(value: int, field: str) -> int:
    if value < 0 or value > 255:
        raise ValueError(f"{field} out of one-byte range: {value}")
    return value


def token_bytes(token: str) -> bytes:
    data = token.encode("utf-8")
    if len(data) > 255:
        raise ValueError(f"token too long for v1 sidecar entry: {token[:40]!r}")
    return data


def pack_entry(entry: dict[str, Any]) -> bytes:
    op = str(entry["op"])
    opcode = OPCODES[op]
    index = byte_value(int(entry["index"]), "index")
    glyph = byte_value(int(entry.get("glyph_id", 0)), "glyph_id")
    token = str(entry.get("token", ""))
    encoded_token = token_bytes(token)

    if op == "select_candidate":
        candidates = [str(item) for item in entry.get("candidates", [])]
        try:
            candidate_index = candidates.index(token)
        except ValueError:
            candidate_index = 255
        return bytes([opcode, index, glyph, byte_value(candidate_index, "candidate_index")])

    if op == "literal_token":
        return bytes([opcode, index, len(encoded_token)]) + encoded_token

    if op == "append_truncated_cell":
        kind = KIND_CODES.get(str(entry.get("kind", "symbol")), 0)
        depth = byte_value(int(entry.get("depth", 0)), "depth")
        return bytes([opcode, index, glyph, (kind << 4) | min(depth, 0x0F), len(encoded_token)]) + encoded_token

    raise ValueError(f"unsupported sidecar op: {op}")


def pack_audit(audit: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:
    chunks: list[bytes] = []
    index_rows: list[dict[str, Any]] = []
    for test in audit.get("tests", []):
        sidecar = test.get("residual_sidecar")
        if not sidecar:
            continue
        start = sum(len(chunk) for chunk in chunks)
        entries = list(sidecar.get("entries", []))
        packed_entries = [pack_entry(entry) for entry in entries]
        for packed in packed_entries:
            chunks.append(packed)
        length = sum(len(packed) for packed in packed_entries)
        index_rows.append(
            {
                "sample_id": test["id"],
                "decision": test["decision"],
                "entry_count": len(entries),
                "offset": start,
                "length": length,
                "sha256": sha256_bytes(b"".join(packed_entries)),
            }
        )
    return b"".join(chunks), index_rows


def build_receipt(audit_path: Path, bin_path: Path) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    packed, index_rows = pack_audit(audit)
    bin_path.write_bytes(packed)
    raw_bytes = int(audit.get("summary", {}).get("raw_bytes", 0))
    payload_bytes = int(audit.get("summary", {}).get("payload_bytes", 0))
    total = payload_bytes + len(packed)
    receipt: dict[str, Any] = {
        "schema": "math_logogram_sidecar_packer_v1",
        "source_audit": str(audit_path),
        "packed_stream": str(bin_path),
        "opcodes": OPCODES,
        "kind_codes": KIND_CODES,
        "stream_bytes": len(packed),
        "stream_sha256": sha256_bytes(packed),
        "index": index_rows,
        "summary": {
            "sample_count": len(audit.get("tests", [])),
            "sidecar_sample_count": len(index_rows),
            "raw_bytes": raw_bytes,
            "payload_bytes": payload_bytes,
            "packed_sidecar_bytes": len(packed),
            "payload_plus_packed_sidecar_bytes": total,
            "compression_ratio_raw_to_payload_plus_packed_sidecar": (
                raw_bytes / total if total else None
            ),
        },
        "claim_boundary": (
            "This is a deterministic sidecar stream prototype. It does not "
            "prove corpus compression or hardware timing."
        ),
    }
    receipt["receipt_hash"] = hashlib.sha256(stable_json(receipt).encode("utf-8")).hexdigest()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack math logogram sidecars.")
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--bin", type=Path, default=DEFAULT_BIN)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()

    receipt = build_receipt(args.audit, args.bin)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
