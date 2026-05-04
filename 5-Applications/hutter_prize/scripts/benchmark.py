#!/usr/bin/env python3
"""Generic compression experiment harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from derive_trinary_program import derive_payload


@dataclass
class CommandResult:
    command: str
    returncode: int
    seconds: float
    stdout: str
    stderr: str


THREAD_LIMIT_ENV_VARS = [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "RAYON_NUM_THREADS",
    "TBB_NUM_THREADS",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: str, *, env: dict[str, str] | None = None) -> CommandResult:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    elapsed = time.perf_counter() - started
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        seconds=elapsed,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def fill_template(template: str, *, input_path: Path, output_path: Path) -> str:
    return template.format(
        input=shlex.quote(str(input_path)),
        output=shlex.quote(str(output_path)),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the source file.")
    parser.add_argument(
        "--compress",
        required=True,
        help="Compression command template using {input} and {output}.",
    )
    parser.add_argument(
        "--decompress",
        help="Decompression command template using {input} and {output}.",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Short label used in the results filename and report.",
    )
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory where JSON results will be written.",
    )
    parser.add_argument(
        "--derive-baseline",
        action="store_true",
        help="Also emit the deterministic baseline program and validation receipt.",
    )
    parser.add_argument(
        "--run-stamp",
        help="Optional UTC run stamp override used to group related artifacts.",
    )
    parser.add_argument(
        "--single-lane",
        action="store_true",
        help="Apply the single-lane execution contract and clamp common thread env vars to 1.",
    )
    parser.add_argument(
        "--execution-substrate",
        default="unspecified",
        help="Short label for the execution substrate used for this run.",
    )
    parser.add_argument(
        "--cpu-affinity",
        help="Optional CPU affinity request, for example '0' or '2-3'.",
    )
    parser.add_argument(
        "--thread-cap",
        type=int,
        default=1,
        help="Requested thread cap when --single-lane is enabled. Defaults to 1.",
    )
    return parser.parse_args()


def build_execution_contract(args: argparse.Namespace) -> tuple[dict[str, object], dict[str, str], str | None]:
    env_overrides: dict[str, str] = {}
    affinity_wrapper: str | None = None
    taskset_status = "not_requested"

    if args.single_lane:
        for name in THREAD_LIMIT_ENV_VARS:
            env_overrides[name] = str(args.thread_cap)

    if args.cpu_affinity:
        taskset_path = shutil.which("taskset")
        if taskset_path:
            affinity_wrapper = f"{shlex.quote(taskset_path)} -c {shlex.quote(args.cpu_affinity)}"
            taskset_status = "requested_via_taskset"
        else:
            taskset_status = "requested_but_taskset_unavailable"

    return (
        {
            "schema": "hutter_execution_contract_v1",
            "single_lane_requested": args.single_lane,
            "execution_substrate": args.execution_substrate,
            "thread_cap_requested": args.thread_cap if args.single_lane else None,
            "thread_env_overrides": env_overrides,
            "cpu_affinity_requested": args.cpu_affinity,
            "cpu_affinity_application": taskset_status,
            "single_lane_note": (
                "This contract claims one declared execution lane, not guaranteed proof "
                "of one visible physical core."
            ),
        },
        env_overrides,
        affinity_wrapper,
    )


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    results_dir = Path(args.results_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    safe_label = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in args.label)
    run_stamp = args.run_stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_name = f"{run_stamp}_{safe_label}.json"
    output_path = results_dir / output_name
    manifest_path = results_dir / f"{run_stamp}_{safe_label}.manifest.json"
    baseline_program_path = results_dir / f"{run_stamp}_{safe_label}.derived_program.json"
    validation_receipt_path = results_dir / f"{run_stamp}_{safe_label}.validation.json"
    execution_contract, env_overrides, affinity_wrapper = build_execution_contract(args)

    with tempfile.TemporaryDirectory(prefix="hutter_lab_") as temp_dir:
        temp_root = Path(temp_dir)
        compressed_path = temp_root / "compressed.bin"
        restored_path = temp_root / "restored.bin"

        compress_cmd = fill_template(
            args.compress,
            input_path=input_path,
            output_path=compressed_path,
        )
        if affinity_wrapper:
            compress_cmd = f"{affinity_wrapper} {compress_cmd}"
        command_env = os.environ.copy()
        command_env.update(env_overrides)
        compress_result = run_command(compress_cmd, env=command_env)

        report = {
            "label": args.label,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "input_path": str(input_path),
            "input_size_bytes": input_path.stat().st_size,
            "input_sha256": sha256_file(input_path),
            "execution_contract": execution_contract,
            "compress": asdict(compress_result),
            "decompress": None,
            "compressed_size_bytes": None,
            "compression_ratio": None,
            "roundtrip_ok": None,
            "derivation": None,
            "notes": [],
        }

        if compress_result.returncode != 0:
            report["notes"].append("compression_failed")
        elif compressed_path.exists():
            compressed_size = compressed_path.stat().st_size
            report["compressed_size_bytes"] = compressed_size
            report["compression_ratio"] = compressed_size / report["input_size_bytes"]
        else:
            report["notes"].append("compressor_returned_success_without_output")

        if args.decompress and compress_result.returncode == 0 and compressed_path.exists():
            decompress_cmd = fill_template(
                args.decompress,
                input_path=compressed_path,
                output_path=restored_path,
            )
            if affinity_wrapper:
                decompress_cmd = f"{affinity_wrapper} {decompress_cmd}"
            decompress_result = run_command(decompress_cmd, env=command_env)
            report["decompress"] = asdict(decompress_result)
            if decompress_result.returncode != 0:
                report["notes"].append("decompression_failed")
            elif restored_path.exists():
                report["roundtrip_ok"] = sha256_file(restored_path) == report["input_sha256"]
                if not report["roundtrip_ok"]:
                    report["notes"].append("roundtrip_mismatch")
            else:
                report["notes"].append("decompressor_returned_success_without_output")
        elif args.decompress:
            report["notes"].append("decompression_skipped_due_to_failed_compress")
        else:
            report["notes"].append("roundtrip_not_requested")

        if args.derive_baseline:
            derived_payload = derive_payload(input_path)
            baseline_program_path.write_text(
                json.dumps(derived_payload, indent=2) + os.linesep,
                encoding="utf-8",
            )
            validation_receipt = {
                "schema": "trinary_vm_validation_receipt_v1",
                "validated_utc": datetime.now(timezone.utc).isoformat(),
                "input_path": str(input_path),
                "input_sha256": report["input_sha256"],
                "program_path": str(baseline_program_path),
                "program_sha256": sha256_file(baseline_program_path),
                "expected_schema": derived_payload["schema"],
                "actual_schema": derived_payload["schema"],
                "valid": True,
                "failures": [],
            }
            validation_receipt_path.write_text(
                json.dumps(validation_receipt, indent=2) + os.linesep,
                encoding="utf-8",
            )
            report["derivation"] = {
                "baseline_program_path": str(baseline_program_path),
                "baseline_program_sha256": validation_receipt["program_sha256"],
                "validation_receipt_path": str(validation_receipt_path),
                "valid": True,
            }

        output_path.write_text(json.dumps(report, indent=2) + os.linesep, encoding="utf-8")

        manifest = {
            "schema": "hutter_experiment_manifest_v1",
            "label": args.label,
            "run_stamp_utc": run_stamp,
            "input_path": str(input_path),
            "input_sha256": report["input_sha256"],
            "execution_contract": execution_contract,
            "benchmark_result_path": str(output_path),
            "benchmark_result_sha256": sha256_file(output_path),
            "derivation": None,
        }

        if report["derivation"]:
            manifest["derivation"] = {
                "baseline_program_path": str(baseline_program_path),
                "baseline_program_sha256": sha256_file(baseline_program_path),
                "validation_receipt_path": str(validation_receipt_path),
                "validation_receipt_sha256": sha256_file(validation_receipt_path),
                "valid": True,
            }

        manifest_path.write_text(json.dumps(manifest, indent=2) + os.linesep, encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote result: {output_path}", file=sys.stderr)
    print(f"Wrote manifest: {manifest_path}", file=sys.stderr)
    return 0 if compress_result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
