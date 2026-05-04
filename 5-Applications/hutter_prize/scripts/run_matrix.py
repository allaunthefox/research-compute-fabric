#!/usr/bin/env python3
"""Run a config-driven compression experiment matrix."""

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
    parser.add_argument(
        "--config",
        required=True,
        help="Path to an experiment config JSON file.",
    )
    parser.add_argument(
        "--input",
        help="Optional override for the input path declared in the config.",
    )
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
        help="Apply the single-lane execution contract to every matrix variant.",
    )
    parser.add_argument(
        "--execution-substrate",
        default="unspecified",
        help="Default execution substrate label used for matrix variants unless overridden in config.",
    )
    parser.add_argument(
        "--cpu-affinity",
        help="Optional CPU affinity request passed through to every matrix variant.",
    )
    parser.add_argument(
        "--thread-cap",
        type=int,
        default=1,
        help="Requested thread cap when --single-lane is enabled. Defaults to 1.",
    )
    return parser.parse_args()


def summarize_variant(result: dict[str, object], *, results_dir: Path, run_stamp: str) -> dict[str, object]:
    label = str(result["label"])
    result_path = results_dir / f"{run_stamp}_{label}.json"
    return {
        "label": label,
        "result_path": str(result_path),
        "execution_substrate": (result.get("execution_contract") or {}).get("execution_substrate"),
        "compressed_size_bytes": result.get("compressed_size_bytes"),
        "compression_ratio": result.get("compression_ratio"),
        "compress_seconds": (result.get("compress") or {}).get("seconds"),
        "roundtrip_ok": result.get("roundtrip_ok"),
        "notes": result.get("notes", []),
    }


def sort_variants(variants: list[dict[str, object]]) -> list[dict[str, object]]:
    def key_fn(item: dict[str, object]) -> tuple[float, float, str]:
        size = item.get("compressed_size_bytes")
        seconds = item.get("compress_seconds")
        safe_size = float(size) if isinstance(size, int) else float("inf")
        safe_seconds = float(seconds) if isinstance(seconds, (int, float)) else float("inf")
        return (safe_size, safe_seconds, str(item["label"]))

    return sorted(variants, key=key_fn)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))

    input_path = Path(args.input).resolve() if args.input else Path(config["input"]).resolve()
    results_dir = Path(args.results_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = str(config.get("name", config_path.stem))
    safe_name = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in name)
    summary_path = results_dir / f"{run_stamp}_{safe_name}.matrix.json"

    results = []
    for variant in config["variants"]:
        results.append(
            run_benchmark(
                input_path=input_path,
                label=variant["label"],
                compress=variant["compress"],
                decompress=variant.get("decompress"),
                results_dir=results_dir,
                run_stamp=run_stamp,
                derive_baseline=args.derive_baseline,
                single_lane=args.single_lane,
                execution_substrate=variant.get("execution_substrate", args.execution_substrate),
                cpu_affinity=args.cpu_affinity,
                thread_cap=args.thread_cap,
            )
        )

    summarized = [summarize_variant(result, results_dir=results_dir, run_stamp=run_stamp) for result in results]
    ranked = sort_variants(summarized)

    summary = {
        "schema": "hutter_experiment_matrix_v1",
        "name": name,
        "run_stamp_utc": run_stamp,
        "config_path": str(config_path),
        "input_path": str(input_path),
        "input_sha256": results[0]["input_sha256"] if results else None,
        "variants": summarized,
        "ranked_by_size_then_speed": ranked,
        "winner": ranked[0]["label"] if ranked else None,
    }

    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote matrix summary: {summary_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
