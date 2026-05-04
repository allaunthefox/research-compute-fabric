#!/usr/bin/env python3
"""Run an A/B compression comparison and emit a combined comparison report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_benchmark(
    *,
    input_path: Path,
    label: str,
    compress: str,
    decompress: str | None,
    results_dir: Path,
    run_stamp: str,
    derive_baseline: bool,
    single_lane: bool,
    execution_substrate: str,
    cpu_affinity: str | None,
    thread_cap: int,
) -> dict[str, object]:
    benchmark_script = Path(__file__).resolve().parent / "benchmark.py"
    cmd = [
        sys.executable,
        str(benchmark_script),
        "--input",
        str(input_path),
        "--compress",
        compress,
        "--label",
        label,
        "--results-dir",
        str(results_dir),
        "--run-stamp",
        run_stamp,
    ]
    if decompress:
        cmd.extend(["--decompress", decompress])
    if derive_baseline:
        cmd.append("--derive-baseline")
    if single_lane:
        cmd.append("--single-lane")
    cmd.extend(["--execution-substrate", execution_substrate, "--thread-cap", str(thread_cap)])
    if cpu_affinity:
        cmd.extend(["--cpu-affinity", cpu_affinity])

    completed = subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the source file.")
    parser.add_argument("--label-a", required=True, help="Label for variant A.")
    parser.add_argument("--compress-a", required=True, help="Compression template for variant A.")
    parser.add_argument("--decompress-a", help="Decompression template for variant A.")
    parser.add_argument("--label-b", required=True, help="Label for variant B.")
    parser.add_argument("--compress-b", required=True, help="Compression template for variant B.")
    parser.add_argument("--decompress-b", help="Decompression template for variant B.")
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory where JSON results will be written.",
    )
    parser.add_argument(
        "--derive-baseline",
        action="store_true",
        help="Also emit the deterministic baseline program and validation receipt for each run.",
    )
    parser.add_argument(
        "--single-lane",
        action="store_true",
        help="Apply the single-lane execution contract to both variants.",
    )
    parser.add_argument(
        "--execution-substrate",
        default="unspecified",
        help="Execution substrate label shared by both variants unless overridden elsewhere.",
    )
    parser.add_argument(
        "--cpu-affinity",
        help="Optional CPU affinity request passed through to both variants.",
    )
    parser.add_argument(
        "--thread-cap",
        type=int,
        default=1,
        help="Requested thread cap when --single-lane is enabled. Defaults to 1.",
    )
    return parser.parse_args()


def choose_winner(a: dict[str, object], b: dict[str, object]) -> dict[str, object]:
    a_size = a.get("compressed_size_bytes")
    b_size = b.get("compressed_size_bytes")
    a_time = ((a.get("compress") or {}).get("seconds")) if isinstance(a.get("compress"), dict) else None
    b_time = ((b.get("compress") or {}).get("seconds")) if isinstance(b.get("compress"), dict) else None

    winner_size = None
    if isinstance(a_size, int) and isinstance(b_size, int):
        if a_size < b_size:
            winner_size = a["label"]
        elif b_size < a_size:
            winner_size = b["label"]
        else:
            winner_size = "tie"

    winner_speed = None
    if isinstance(a_time, (int, float)) and isinstance(b_time, (int, float)):
        if a_time < b_time:
            winner_speed = a["label"]
        elif b_time < a_time:
            winner_speed = b["label"]
        else:
            winner_speed = "tie"

    return {
        "smaller_output": winner_size,
        "faster_compress": winner_speed,
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    results_dir = Path(args.results_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_label = f"{args.label_a}_vs_{args.label_b}"
    safe_batch = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in batch_label)
    comparison_path = results_dir / f"{run_stamp}_{safe_batch}.comparison.json"

    result_a = run_benchmark(
        input_path=input_path,
        label=args.label_a,
        compress=args.compress_a,
        decompress=args.decompress_a,
        results_dir=results_dir,
        run_stamp=run_stamp,
        derive_baseline=args.derive_baseline,
        single_lane=args.single_lane,
        execution_substrate=args.execution_substrate,
        cpu_affinity=args.cpu_affinity,
        thread_cap=args.thread_cap,
    )
    result_b = run_benchmark(
        input_path=input_path,
        label=args.label_b,
        compress=args.compress_b,
        decompress=args.decompress_b,
        results_dir=results_dir,
        run_stamp=run_stamp,
        derive_baseline=args.derive_baseline,
        single_lane=args.single_lane,
        execution_substrate=args.execution_substrate,
        cpu_affinity=args.cpu_affinity,
        thread_cap=args.thread_cap,
    )

    comparison = {
        "schema": "hutter_ab_comparison_v1",
        "run_stamp_utc": run_stamp,
        "input_path": str(input_path),
        "input_sha256": result_a["input_sha256"],
        "variant_a": {
            "label": result_a["label"],
            "result_path": str(results_dir / f"{run_stamp}_{args.label_a}.json"),
            "execution_substrate": (result_a.get("execution_contract") or {}).get("execution_substrate"),
            "compressed_size_bytes": result_a.get("compressed_size_bytes"),
            "compression_ratio": result_a.get("compression_ratio"),
            "compress_seconds": (result_a.get("compress") or {}).get("seconds"),
            "roundtrip_ok": result_a.get("roundtrip_ok"),
        },
        "variant_b": {
            "label": result_b["label"],
            "result_path": str(results_dir / f"{run_stamp}_{args.label_b}.json"),
            "execution_substrate": (result_b.get("execution_contract") or {}).get("execution_substrate"),
            "compressed_size_bytes": result_b.get("compressed_size_bytes"),
            "compression_ratio": result_b.get("compression_ratio"),
            "compress_seconds": (result_b.get("compress") or {}).get("seconds"),
            "roundtrip_ok": result_b.get("roundtrip_ok"),
        },
        "winner": choose_winner(result_a, result_b),
    }

    comparison_path.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(comparison, indent=2))
    print(f"Wrote comparison: {comparison_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
