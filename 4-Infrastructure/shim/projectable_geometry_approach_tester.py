#!/usr/bin/env python3
"""Approach tester for projectable-geometry compression on wiki-like targets.

This is not a Hutter submission compressor.  It is a reversible approach sieve:
run small, exact transforms against local wiki-like files, compare them with
standard codecs, and record which ideas are worth promoting.

The "boat-aware" approaches are deliberately conservative:

* every transform must decode byte-for-byte
* every transformed payload is benchmarked with real byte sizes
* expansion is recorded honestly
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import os
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "4-Infrastructure" / "shim" / "projectable_geometry_approach_tester_receipt.json"

HUTTER_TARGET_BYTES = 109_685_197
ENWIK9_BYTES = 1_000_000_000
HUTTER_TARGET_RATIO = HUTTER_TARGET_BYTES / ENWIK9_BYTES

DEFAULT_CANDIDATES = [
    Path("/home/allaun/.gemini/antigravity/scratch/kimi_dataset/enwik8"),
    Path("/home/allaun/.local/share/Trash/files/enwik8"),
    Path("/home/allaun/Downloads/data/enwik9_data/1234567"),
]

TOKEN_ESCAPE = b"\x00"
XML_WIKI_TOKENS = [
    b"<page>",
    b"</page>",
    b"<title>",
    b"</title>",
    b"<id>",
    b"</id>",
    b"<revision>",
    b"</revision>",
    b"<timestamp>",
    b"</timestamp>",
    b"<contributor>",
    b"</contributor>",
    b"<username>",
    b"</username>",
    b"<text",
    b"</text>",
    b"[[",
    b"]]",
    b"{{",
    b"}}",
    b"==",
    b"'''",
    b"&quot;",
    b"&amp;",
]


@dataclass(frozen=True)
class EncodedPayload:
    payload: bytes
    metadata: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def zlib9(data: bytes) -> bytes:
    return zlib.compress(data, 9)


def bz2_best(data: bytes) -> bytes:
    return bz2.compress(data, 9)


def lzma_best(data: bytes) -> bytes:
    return lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)


def raw_encode(data: bytes) -> EncodedPayload:
    return EncodedPayload(data, {})


def raw_decode(encoded: EncodedPayload) -> bytes:
    return encoded.payload


def xml_token_encode(data: bytes) -> EncodedPayload:
    token_map = {token: idx + 1 for idx, token in enumerate(XML_WIKI_TOKENS)}
    # Longest first avoids splitting <timestamp> around smaller fragments.
    tokens = sorted(token_map, key=len, reverse=True)
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i:i + 1] == TOKEN_ESCAPE:
            out.extend(TOKEN_ESCAPE)
            out.extend(b"\x00")
            i += 1
            continue
        matched = False
        for token in tokens:
            if data.startswith(token, i):
                out.extend(TOKEN_ESCAPE)
                out.append(token_map[token])
                i += len(token)
                matched = True
                break
        if not matched:
            out.append(data[i])
            i += 1
    return EncodedPayload(bytes(out), {
        "token_count": len(XML_WIKI_TOKENS),
        "escape": "00",
        "tokens": [token.decode("utf-8", errors="replace") for token in XML_WIKI_TOKENS],
    })


def xml_token_decode(encoded: EncodedPayload) -> bytes:
    reverse = {idx + 1: token for idx, token in enumerate(XML_WIKI_TOKENS)}
    data = encoded.payload
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b != 0:
            out.append(b)
            i += 1
            continue
        if i + 1 >= len(data):
            raise ValueError("trailing token escape")
        code = data[i + 1]
        if code == 0:
            out.extend(TOKEN_ESCAPE)
        elif code in reverse:
            out.extend(reverse[code])
        else:
            raise ValueError(f"unknown token code {code}")
        i += 2
    return bytes(out)


def byte_class(byte: int) -> int:
    if byte in b" \n\r\t":
        return 0
    if 65 <= byte <= 90 or 97 <= byte <= 122:
        return 1
    if 48 <= byte <= 57:
        return 2
    if byte in b"<>/={}[]|#_*'\"&;:":
        return 3
    return 4


def class_lane_encode(data: bytes) -> EncodedPayload:
    """Split stream into class labels and lane payloads.

    This is a simple "boat" transform: a keel of byte classes plus residual
    lanes.  It is exact, but not assumed to compress.
    """

    class_stream = bytearray()
    lanes = [bytearray() for _ in range(5)]
    for byte in data:
        cls = byte_class(byte)
        class_stream.append(cls)
        lanes[cls].append(byte)
    parts = [bytes(class_stream), *(bytes(lane) for lane in lanes)]
    header = bytearray(b"PGB0")
    for part in parts:
        header.extend(len(part).to_bytes(4, "big"))
    payload = bytes(header) + b"".join(parts)
    return EncodedPayload(payload, {
        "boat": "byte_class_lanes",
        "lane_count": 5,
        "lane_lengths": [len(part) for part in parts[1:]],
        "class_stream_length": len(parts[0]),
    })


def class_lane_decode(encoded: EncodedPayload) -> bytes:
    data = encoded.payload
    if not data.startswith(b"PGB0"):
        raise ValueError("bad PGB0 magic")
    offset = 4
    lengths = []
    for _ in range(6):
        lengths.append(int.from_bytes(data[offset:offset + 4], "big"))
        offset += 4
    parts = []
    for length in lengths:
        parts.append(data[offset:offset + length])
        offset += length
    if offset != len(data):
        raise ValueError("trailing PGB0 bytes")
    class_stream = parts[0]
    lanes = [bytearray(part) for part in parts[1:]]
    lane_offsets = [0] * 5
    out = bytearray()
    for cls in class_stream:
        idx = lane_offsets[cls]
        out.append(lanes[cls][idx])
        lane_offsets[cls] += 1
    return bytes(out)


def delta_boat_encode(data: bytes) -> EncodedPayload:
    """XOR-delta stream split into three residual handles plus class keel."""

    if not data:
        return EncodedPayload(b"PGD0" + (0).to_bytes(4, "big"), {"boat": "xor_delta_handles"})
    class_stream = bytearray()
    handles = [bytearray() for _ in range(3)]
    prev = 0
    for byte in data:
        delta = byte ^ prev
        prev = byte
        cls = byte_class(byte)
        handle = 0 if cls in (1, 2) else 1 if cls in (3,) else 2
        class_stream.append(handle)
        handles[handle].append(delta)
    parts = [bytes(class_stream), *(bytes(handle) for handle in handles)]
    header = bytearray(b"PGD0")
    header.append(data[0])
    for part in parts:
        header.extend(len(part).to_bytes(4, "big"))
    payload = bytes(header) + b"".join(parts)
    return EncodedPayload(payload, {
        "boat": "xor_delta_three_handles",
        "handle_count": 3,
        "handle_lengths": [len(part) for part in parts[1:]],
        "class_stream_length": len(parts[0]),
    })


def delta_boat_decode(encoded: EncodedPayload) -> bytes:
    data = encoded.payload
    if not data.startswith(b"PGD0"):
        raise ValueError("bad PGD0 magic")
    if len(data) == 8:
        return b""
    first = data[4]
    offset = 5
    lengths = []
    for _ in range(4):
        lengths.append(int.from_bytes(data[offset:offset + 4], "big"))
        offset += 4
    parts = []
    for length in lengths:
        parts.append(data[offset:offset + length])
        offset += length
    if offset != len(data):
        raise ValueError("trailing PGD0 bytes")
    class_stream = parts[0]
    handles = [bytearray(part) for part in parts[1:]]
    handle_offsets = [0] * 3
    out = bytearray()
    prev = 0
    for handle in class_stream:
        idx = handle_offsets[handle]
        delta = handles[handle][idx]
        byte = delta ^ prev
        out.append(byte)
        prev = byte
        handle_offsets[handle] += 1
    if out and out[0] != first:
        raise ValueError("first-byte witness mismatch")
    return bytes(out)


TRANSFORMS: dict[str, tuple[Callable[[bytes], EncodedPayload], Callable[[EncodedPayload], bytes]]] = {
    "raw": (raw_encode, raw_decode),
    "xml_token": (xml_token_encode, xml_token_decode),
    "class_lane_boat": (class_lane_encode, class_lane_decode),
    "delta_boat": (delta_boat_encode, delta_boat_decode),
}

CODECS: dict[str, Callable[[bytes], bytes]] = {
    "stored": lambda data: data,
    "zlib9": zlib9,
    "bz2": bz2_best,
    "lzma": lzma_best,
}


def discover_inputs(extra_inputs: list[Path]) -> list[Path]:
    candidates = [*extra_inputs, *DEFAULT_CANDIDATES]
    seen = set()
    existing = []
    for path in candidates:
        resolved = path.expanduser()
        if not resolved.exists() or not resolved.is_file():
            continue
        key = str(resolved.resolve())
        if key in seen:
            continue
        seen.add(key)
        existing.append(resolved)
    return existing


def make_slices(path: Path, max_slice: int) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    sizes = []
    for size in (20_000, 100_000, 1_000_000, 4_000_000):
        if size <= max_slice and len(data) >= size:
            sizes.append(size)
    if not sizes:
        sizes.append(min(len(data), max_slice))
    slices = []
    for size in sizes:
        slices.append((f"{path.name}:{size}", data[:size]))
    return slices


def evaluate_slice(name: str, source_path: Path, data: bytes) -> dict[str, Any]:
    source_hash = sha256_bytes(data)
    results = []
    for transform_name, (encode, decode) in TRANSFORMS.items():
        encoded = encode(data)
        decoded = decode(encoded)
        rehydrated_ok = decoded == data
        encoded_hash = sha256_bytes(encoded.payload)
        for codec_name, codec in CODECS.items():
            compressed = codec(encoded.payload)
            total_size = len(compressed)
            ratio = total_size / len(data) if data else 0.0
            projected_enwik9_total = int(ratio * ENWIK9_BYTES)
            results.append({
                "transform": transform_name,
                "codec": codec_name,
                "encoded_size": len(encoded.payload),
                "compressed_size": total_size,
                "ratio": ratio,
                "projected_enwik9_total_bytes": projected_enwik9_total,
                "beats_hutter_target_ratio": ratio < HUTTER_TARGET_RATIO,
                "rehydrated_ok": rehydrated_ok,
                "encoded_hash_sha256": encoded_hash,
                "metadata": encoded.metadata,
            })
    ranked = sorted(results, key=lambda item: item["compressed_size"])
    best = ranked[0] if ranked else None
    baseline_zlib = next(
        item for item in results
        if item["transform"] == "raw" and item["codec"] == "zlib9"
    )
    best_raw = min(
        (item for item in results if item["transform"] == "raw"),
        key=lambda item: item["compressed_size"],
    )
    best_boat = min(
        (item for item in results if item["transform"] != "raw"),
        key=lambda item: item["compressed_size"],
    )
    return {
        "slice_name": name,
        "source_path": str(source_path),
        "source_bytes": len(data),
        "source_hash_sha256": source_hash,
        "hutter_target_ratio": HUTTER_TARGET_RATIO,
        "best": best,
        "baseline_zlib9": baseline_zlib,
        "best_raw_baseline": best_raw,
        "best_boat_aware": best_boat,
        "boat_beats_zlib9": best_boat["compressed_size"] < baseline_zlib["compressed_size"],
        "boat_beats_best_raw": best_boat["compressed_size"] < best_raw["compressed_size"],
        "all_rehydrated": all(item["rehydrated_ok"] for item in results),
        "results": ranked,
    }


def build_receipt(inputs: list[Path], max_slice: int) -> dict[str, Any]:
    discovered = discover_inputs(inputs)
    slice_results = []
    for path in discovered:
        for slice_name, data in make_slices(path, max_slice):
            slice_results.append(evaluate_slice(slice_name, path, data))
    best_overall = min(
        (result["best"] | {"slice_name": result["slice_name"]} for result in slice_results),
        key=lambda item: item["ratio"],
    ) if slice_results else None
    boat_wins = [
        {
            "slice_name": result["slice_name"],
            "best_boat_aware": result["best_boat_aware"],
            "baseline_zlib9": result["baseline_zlib9"],
        }
        for result in slice_results
        if result["boat_beats_zlib9"]
    ]
    boat_wins_vs_best_raw = [
        {
            "slice_name": result["slice_name"],
            "best_boat_aware": result["best_boat_aware"],
            "best_raw_baseline": result["best_raw_baseline"],
        }
        for result in slice_results
        if result["boat_beats_best_raw"]
    ]
    receipt = {
        "schema": "projectable_geometry_approach_tester_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "projectable_geometry_approach_tester",
        "hutter_target": {
            "enwik9_bytes": ENWIK9_BYTES,
            "target_total_bytes": HUTTER_TARGET_BYTES,
            "target_ratio": HUTTER_TARGET_RATIO,
            "note": "Projection from small slices is diagnostic only; it is not a Hutter claim.",
        },
        "inputs": [
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_bytes(path.read_bytes()),
            }
            for path in discovered
        ],
        "approaches": {
            "transforms": sorted(TRANSFORMS),
            "codecs": sorted(CODECS),
            "boat_aware_transforms": ["xml_token", "class_lane_boat", "delta_boat"],
        },
        "summary": {
            "input_count": len(discovered),
            "slice_count": len(slice_results),
            "all_rehydrated": all(result["all_rehydrated"] for result in slice_results),
            "boat_win_count_vs_zlib9": len(boat_wins),
            "boat_win_count_vs_best_raw": len(boat_wins_vs_best_raw),
            "best_overall": best_overall,
            "boat_wins_vs_zlib9": boat_wins,
            "boat_wins_vs_best_raw": boat_wins_vs_best_raw,
        },
        "slices": slice_results,
        "claim_boundary": (
            "This is a small-slice approach sieve for projectable-geometry "
            "transforms. Projected enwik9 totals are diagnostic only and do not "
            "constitute Hutter Prize compression claims."
        ),
        "lawful": True,
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "hutter_target": receipt["hutter_target"],
        "inputs": receipt["inputs"],
        "approaches": receipt["approaches"],
        "summary": receipt["summary"],
        "slices": receipt["slices"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_approach_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, default=[])
    parser.add_argument("--max-slice", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt(args.input, args.max_slice)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_approach_hash_sha256": receipt["stable_approach_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "summary": receipt["summary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
