#!/usr/bin/env python3
"""Ingest and run the enwiki9 logogram targeter bundle.

The input bundle is a slice-targeting harness, not an enwiki9 corpus. This
wrapper records the bundle hash, runs its demo, optionally runs the available
local enwiki9-like sample, and writes a stable top-level receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = Path("/home/allaun/Documents/ingest/enwiki9_logogram_target.zip")
DEFAULT_SAMPLE = Path("/home/allaun/Downloads/data/enwik9_data/1234567")
OUT_DIR = REPO / "shared-data" / "data" / "enwiki9_logogram_targeter"
RECEIPT = OUT_DIR / "enwiki9_logogram_targeter_receipt.json"
SUMMARY = OUT_DIR / "enwiki9_logogram_targeter_receipt.md"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_bundle(bundle: Path, extract_dir: Path) -> Path:
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)
    with zipfile.ZipFile(bundle) as zf:
        zf.extractall(extract_dir)
    script = extract_dir / "enwiki9_logogram_target" / "enwiki9_slice_targeter.py"
    if not script.exists():
        raise FileNotFoundError(script)
    return script


def run_targeter(script: Path, out_dir: Path, args: list[str]) -> dict[str, Any]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    command = [sys.executable, str(script), "--out", str(out_dir), *args]
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return {
        "command": command,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "summary": rel(out_dir / "summary.json"),
        "manifest": rel(out_dir / "slice_manifest.json"),
        "summary_payload": load_json(out_dir / "summary.json"),
    }


def output_hashes(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        records.append(
            {
                "path": rel(item),
                "bytes": item.stat().st_size,
                "sha256": sha256_file(item),
            }
        )
    return records


def write_summary(receipt: dict[str, Any]) -> None:
    demo = receipt["runs"]["demo"]["summary_payload"]
    sample = receipt["runs"].get("sample_20532", {}).get("summary_payload")
    lines = [
        "# enwiki9 Logogram Targeter Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Bundle",
        "",
        f"- Zip: `{receipt['bundle']['path']}`",
        f"- Zip bytes: `{receipt['bundle']['bytes']}`",
        f"- Zip hash: `{receipt['bundle']['sha256']}`",
        "",
        "## Demo Run",
        "",
        f"- Slices: `{demo['num_slices']}`",
        f"- Round trip: `{demo['all_roundtrip_ok']}`",
        f"- Raw bytes: `{demo['total_raw_len']}`",
        f"- Core bytes: `{demo['total_core_len']}`",
        f"- Packet estimate bytes: `{demo['total_local_packet_estimate']}`",
    ]
    if sample:
        lines.extend(
            [
                "",
                "## Local Sample Run",
                "",
                f"- Sample: `{receipt['sample']['path']}`",
                f"- Sample bytes: `{receipt['sample']['bytes']}`",
                f"- Slices: `{sample['num_slices']}`",
                f"- Round trip: `{sample['all_roundtrip_ok']}`",
                f"- Raw bytes: `{sample['total_raw_len']}`",
                f"- Core bytes: `{sample['total_core_len']}`",
                f"- Packet estimate bytes: `{sample['total_local_packet_estimate']}`",
            ]
        )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_receipt(bundle: Path, sample: Path | None, slice_size: int, stride: int) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    script = extract_bundle(bundle, OUT_DIR / "bundle")
    demo_run = run_targeter(script, OUT_DIR / "demo", ["--demo"])
    runs: dict[str, Any] = {"demo": demo_run}

    sample_payload = None
    if sample and sample.exists():
        sample_run = run_targeter(
            script,
            OUT_DIR / "sample_20532",
            ["--input", str(sample), "--slice-size", str(slice_size), "--stride", str(stride)],
        )
        runs["sample_20532"] = sample_run
        sample_payload = {"path": str(sample), "bytes": sample.stat().st_size, "sha256": sha256_file(sample)}

    receipt = {
        "schema": "enwiki9_logogram_targeter_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle": {
            "path": str(bundle),
            "bytes": bundle.stat().st_size,
            "sha256": sha256_file(bundle),
            "extracted_script": rel(script),
            "extracted_script_sha256": sha256_file(script),
        },
        "sample": sample_payload,
        "runs": runs,
        "output_hashes": output_hashes(OUT_DIR),
        "decision": "HOLD",
        "claim_boundary": (
            "Imported enwiki9 logogram targeter bundle and local sample run only. "
            "The bundle is not the canonical enwik9 corpus, the available local "
            "sample is 20,532 bytes rather than 1,000,000,000 bytes, and no "
            "Hutter/LTCB benchmark or compression-competitiveness claim is made."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc", "output_hashes"}}).encode("utf-8")
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the enwiki9 logogram targeter bundle and write a stable receipt.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--slice-size", type=int, default=4096)
    parser.add_argument("--stride", type=int, default=4096)
    args = parser.parse_args()

    receipt = build_receipt(args.bundle, args.sample, args.slice_size, args.stride)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "demo_roundtrip": receipt["runs"]["demo"]["summary_payload"]["all_roundtrip_ok"],
                "sample_roundtrip": receipt["runs"].get("sample_20532", {}).get("summary_payload", {}).get("all_roundtrip_ok"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
