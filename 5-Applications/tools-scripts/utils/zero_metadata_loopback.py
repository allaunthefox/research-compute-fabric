#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple


MAGIC = b"SVSC1\x00"
HEADER_STRUCT = struct.Struct("<6s32sQQ")


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def smooth_bytes_delta(data: bytes) -> bytes:
    out = bytearray(len(data))
    prev = 0
    for index, value in enumerate(data):
        out[index] = (value - prev) & 0xFF
        prev = value
    return bytes(out)


def unsmooth_bytes_delta(data: bytes) -> bytes:
    out = bytearray(len(data))
    prev = 0
    for index, value in enumerate(data):
        out[index] = (prev + value) & 0xFF
        prev = out[index]
    return bytes(out)


def rle_encode(data: bytes) -> bytes:
    if not data:
        return b""
    out = bytearray()
    run_value = data[0]
    run_len = 1
    for value in data[1:]:
        if value == run_value and run_len < 255:
            run_len += 1
            continue
        out.extend((run_len, run_value))
        run_value = value
        run_len = 1
    out.extend((run_len, run_value))
    return bytes(out)


def rle_decode(data: bytes) -> bytes:
    if len(data) % 2 != 0:
        raise ValueError("Invalid RLE stream length.")
    out = bytearray()
    for index in range(0, len(data), 2):
        run_len = data[index]
        run_value = data[index + 1]
        out.extend(bytes([run_value]) * run_len)
    return bytes(out)


def smooth_bytes(data: bytes) -> bytes:
    return rle_encode(smooth_bytes_delta(data))


def unsmooth_bytes(data: bytes) -> bytes:
    return unsmooth_bytes_delta(rle_decode(data))


def file_digest(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
    }


def build_payload(primary_json_path: Path, evidence_paths: List[Path]) -> Dict[str, Any]:
    primary = json.loads(primary_json_path.read_text(encoding="utf-8"))
    files = [file_digest(primary_json_path)]
    files.extend(file_digest(path) for path in evidence_paths)
    return {
        "schema": "zero-metadata-loopback/v1",
        "algorithm": {
            "canonical": "json-sort-utf8",
            "signal_smooth": "delta-byte+rle",
            "compression": "zlib-9",
        },
        "primary_attestation": primary,
        "evidence_files": files,
    }


def pack_loopback(payload: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
    canonical = canonical_json_bytes(payload)
    canonical_hash = hashlib.sha256(canonical).digest()
    smoothed = smooth_bytes(canonical)
    compressed = zlib.compress(smoothed, level=9)
    header = HEADER_STRUCT.pack(MAGIC, canonical_hash, len(canonical), len(smoothed))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(header + compressed)

    return {
        "output": str(output_path),
        "container_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "canonical_sha256": canonical_hash.hex(),
        "canonical_size": len(canonical),
        "smoothed_size": len(smoothed),
        "compressed_size": len(compressed),
    }


def unpack_loopback(input_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    blob = input_path.read_bytes()
    if len(blob) < HEADER_STRUCT.size:
        raise ValueError("Invalid loopback container: too small.")

    magic, expected_hash, canonical_size, smoothed_size = HEADER_STRUCT.unpack(blob[: HEADER_STRUCT.size])
    if magic != MAGIC:
        raise ValueError("Invalid loopback container: bad magic header.")

    compressed = blob[HEADER_STRUCT.size :]
    smoothed = zlib.decompress(compressed)
    if len(smoothed) != smoothed_size:
        raise ValueError("Smoothed size mismatch.")

    canonical = unsmooth_bytes(smoothed)
    if len(canonical) != canonical_size:
        raise ValueError("Canonical size mismatch.")

    observed_hash = hashlib.sha256(canonical).digest()
    if observed_hash != expected_hash:
        raise ValueError("Canonical hash mismatch.")

    payload = json.loads(canonical.decode("utf-8"))
    metrics = {
        "input": str(input_path),
        "container_sha256": hashlib.sha256(blob).hexdigest(),
        "canonical_sha256": observed_hash.hex(),
        "canonical_size": canonical_size,
        "smoothed_size": smoothed_size,
        "compressed_size": len(compressed),
    }
    return payload, metrics


def verify_payload_files(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for item in payload.get("evidence_files", []):
        path = Path(item["path"])
        if not path.exists():
            findings.append({"path": str(path), "status": "missing"})
            continue
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        findings.append(
            {
                "path": str(path),
                "status": "ok" if observed == item.get("sha256") else "mismatch",
                "expected": item.get("sha256"),
                "observed": observed,
            }
        )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and verify a zero-metadata loopback forensic container.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pack_parser = subparsers.add_parser("pack", help="Pack attestation evidence into a loopback container.")
    pack_parser.add_argument(
        "--primary",
        default="5-Applications/out/trace_attestation.json",
        help="Primary attestation JSON path.",
    )
    pack_parser.add_argument(
        "--evidence",
        action="append",
        default=["5-Applications/out/demo_trace.sqlite3", "5-Applications/out/clusters.csv", "5-Applications/out/timeline.json"],
        help="Evidence file path. Repeatable.",
    )
    pack_parser.add_argument("--out", default="5-Applications/out/spyvsspy_audit.svsc", help="Output SVS-CDR container path.")

    unpack_parser = subparsers.add_parser("unpack", help="Unpack a loopback container to JSON.")
    unpack_parser.add_argument("input", help="Loopback container file path.")
    unpack_parser.add_argument("--out", default="5-Applications/out/zero_metadata_loopback_payload.json", help="Output JSON path.")

    verify_parser = subparsers.add_parser("verify", help="Verify container integrity and embedded evidence hashes.")
    verify_parser.add_argument("input", help="Loopback container file path.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "pack":
        primary = Path(args.primary)
        evidence = [Path(path) for path in args.evidence]
        payload = build_payload(primary, evidence)
        result = pack_loopback(payload, Path(args.out))
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "unpack":
        payload, metrics = unpack_loopback(Path(args.input))
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({**metrics, "payload_output": str(out_path)}, indent=2))
        return 0

    if args.command == "verify":
        payload, metrics = unpack_loopback(Path(args.input))
        findings = verify_payload_files(payload)
        ok = all(item["status"] == "ok" for item in findings)
        print(json.dumps({**metrics, "files": findings, "verified": ok}, indent=2))
        return 0 if ok else 3

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
