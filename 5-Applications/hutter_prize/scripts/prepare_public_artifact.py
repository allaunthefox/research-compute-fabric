#!/usr/bin/env python3
"""Prepare a public-facing artifact with smoothing, receipts, and hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_mode(path: Path, explicit_mode: str) -> str:
    if explicit_mode != "auto":
        return explicit_mode
    if path.suffix.lower() == ".json":
        return "json"
    return "text"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source artifact to prepare.")
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Directory for the prepared public artifact bundle.",
    )
    parser.add_argument(
        "--label",
        help="Optional label for the output filenames. Defaults to the input stem.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "text", "json"),
        default="auto",
        help="Smoothing mode passed through to universal_smoother.py.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    mode = detect_mode(input_path, args.mode)
    label = args.label or input_path.stem
    safe_label = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in label)

    suffix = input_path.suffix or (".json" if mode == "json" else ".txt")
    smoothed_path = out_dir / f"{safe_label}.public{suffix}"
    report_path = out_dir / f"{safe_label}.smoothing.json"
    manifest_path = out_dir / f"{safe_label}.manifest.json"

    smoother = Path(__file__).resolve().parent / "universal_smoother.py"
    cmd = [
        sys.executable,
        str(smoother),
        "--input",
        str(input_path),
        "--output",
        str(smoothed_path),
        "--report",
        str(report_path),
        "--mode",
        mode,
    ]
    completed = subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    json.loads(completed.stdout)

    smoothed_name = smoothed_path.name
    receipt_name = report_path.name
    bundle_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "label": safe_label,
                "mode": mode,
                "input_name": input_path.name,
                "input_sha256": sha256_file(input_path),
                "smoothed_artifact_name": smoothed_name,
                "smoothed_artifact_sha256": sha256_file(smoothed_path),
                "smoothing_receipt_name": receipt_name,
                "smoothing_receipt_sha256": sha256_file(report_path),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    manifest = {
        "schema": "hutter_public_artifact_manifest_v1",
        "label": safe_label,
        "input_name": input_path.name,
        "input_sha256": sha256_file(input_path),
        "mode": mode,
        "smoothed_artifact_name": smoothed_name,
        "smoothed_artifact_sha256": sha256_file(smoothed_path),
        "smoothing_receipt_name": receipt_name,
        "smoothing_receipt_sha256": sha256_file(report_path),
        "bundle_fingerprint": bundle_fingerprint,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    print(f"Wrote public artifact manifest: {manifest_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
