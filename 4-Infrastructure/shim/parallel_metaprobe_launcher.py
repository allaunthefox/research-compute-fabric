#!/usr/bin/env python3
"""Launch a bounded parallel metaprobe sweep.

This runner coordinates existing receipt-generating probes. It does not ingest
external corpora, prove claims, or promote any route. Each lane writes a local
receipt, stdout, stderr, and a master launcher receipt records what ran.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
MASS_PARQUET = REPO / "3-Mathematical-Models" / "equations_parquet_tagged" / "mass_equations_unified.parquet"


@dataclass(frozen=True)
class Lane:
    name: str
    cmd: list[str]
    receipt: Path | None = None
    curriculum: Path | None = None
    claim_boundary: str = "route-prior-only"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def lane_set(out_dir: Path, include_rrc: bool) -> list[Lane]:
    lanes = [
        Lane(
            name="nspace_bulk_dataset_route_registry",
            cmd=[sys.executable, str(SHIM / "nspace_bulk_dataset_route_registry.py")],
            receipt=REPO / "shared-data" / "data" / "nspace_bulk_routes" / "nspace_bulk_dataset_route_receipt.json",
            claim_boundary="external-dataset-route-registry-only",
        ),
        Lane(
            name="decoder_reconstruction_core_prior",
            cmd=[sys.executable, str(SHIM / "decoder_reconstruction_core_prior.py")],
            receipt=REPO / "shared-data" / "data" / "decoder_reconstruction_core" / "decoder_reconstruction_core_prior_receipt.json",
            claim_boundary="architecture-prior-only",
        ),
        Lane(
            name="parallel_stage_domain_route_prior",
            cmd=[sys.executable, str(SHIM / "parallel_stage_domain_route_prior.py")],
            receipt=SHIM / "parallel_stage_domain_route_prior_receipt.json",
            curriculum=SHIM / "parallel_stage_domain_route_prior_curriculum.jsonl",
            claim_boundary="parallel-domain-route-prior-only",
        ),
        Lane(
            name="pde_model_prior_metaprobe",
            cmd=[
                sys.executable,
                str(SHIM / "pde_model_prior_metaprobe.py"),
                "--receipt",
                str(out_dir / "pde_model_prior_receipt.json"),
                "--curriculum",
                str(out_dir / "pde_model_prior_curriculum.jsonl"),
            ],
            receipt=out_dir / "pde_model_prior_receipt.json",
            curriculum=out_dir / "pde_model_prior_curriculum.jsonl",
            claim_boundary="pde-model-prior-only",
        ),
        Lane(
            name="math_prover_prior_metaprobe",
            cmd=[
                sys.executable,
                str(SHIM / "math_prover_prior_metaprobe.py"),
                "--no-live-search",
                "--receipt",
                str(out_dir / "math_prover_prior_metaprobe_receipt.json"),
                "--curriculum",
                str(out_dir / "math_prover_prior_curriculum.jsonl"),
            ],
            receipt=out_dir / "math_prover_prior_metaprobe_receipt.json",
            curriculum=out_dir / "math_prover_prior_curriculum.jsonl",
            claim_boundary="math-prover-prior-no-live-search",
        ),
        Lane(
            name="molecular_domain_prior_metaprobe",
            cmd=[
                sys.executable,
                str(SHIM / "molecular_domain_prior_metaprobe.py"),
                "--receipt",
                str(out_dir / "molecular_domain_prior_receipt.json"),
                "--curriculum",
                str(out_dir / "molecular_domain_prior_curriculum.jsonl"),
            ],
            receipt=out_dir / "molecular_domain_prior_receipt.json",
            curriculum=out_dir / "molecular_domain_prior_curriculum.jsonl",
            claim_boundary="molecular-domain-prior-only",
        ),
        Lane(
            name="genomic_sequence_prior_metaprobe",
            cmd=[
                sys.executable,
                str(SHIM / "genomic_sequence_prior_metaprobe.py"),
                "--receipt",
                str(out_dir / "genomic_sequence_prior_receipt.json"),
                "--curriculum",
                str(out_dir / "genomic_sequence_prior_curriculum.jsonl"),
            ],
            receipt=out_dir / "genomic_sequence_prior_receipt.json",
            curriculum=out_dir / "genomic_sequence_prior_curriculum.jsonl",
            claim_boundary="genomic-sequence-prior-only",
        ),
        Lane(
            name="llm_compression_architecture_prior_metaprobe",
            cmd=[
                sys.executable,
                str(SHIM / "llm_compression_architecture_prior_metaprobe.py"),
                "--receipt",
                str(out_dir / "llm_compression_architecture_prior_receipt.json"),
                "--curriculum",
                str(out_dir / "llm_compression_architecture_prior_curriculum.jsonl"),
            ],
            receipt=out_dir / "llm_compression_architecture_prior_receipt.json",
            curriculum=out_dir / "llm_compression_architecture_prior_curriculum.jsonl",
            claim_boundary="llm-compression-architecture-prior-only",
        ),
        Lane(
            name="moving_sofa_nspace_prior_metaprobe",
            cmd=[
                sys.executable,
                str(SHIM / "moving_sofa_nspace_prior_metaprobe.py"),
                "--receipt",
                str(out_dir / "moving_sofa_nspace_prior_receipt.json"),
                "--curriculum",
                str(out_dir / "moving_sofa_nspace_prior_curriculum.jsonl"),
            ],
            receipt=out_dir / "moving_sofa_nspace_prior_receipt.json",
            curriculum=out_dir / "moving_sofa_nspace_prior_curriculum.jsonl",
            claim_boundary="moving-sofa-route-prior-only",
        ),
        Lane(
            name="mass_equation_distill_receipt",
            cmd=[
                sys.executable,
                str(SHIM / "mass_equation_distill_receipt.py"),
                "--receipt",
                str(out_dir / "mass_equations_unified_receipt.json"),
                "--summary",
                str(out_dir / "mass_equations_unified_receipt.md"),
            ],
            receipt=out_dir / "mass_equations_unified_receipt.json",
            claim_boundary="mass-equation-coverage-receipt-only",
        ),
    ]
    if include_rrc:
        lanes.append(
            Lane(
                name="rrc_mass_equation_projection",
                cmd=[
                    sys.executable,
                    str(SHIM / "rrc_equation_classifier.py"),
                    "--mass-parquet",
                    str(MASS_PARQUET),
                    "--mass-only",
                    "--receipt-detail-limit",
                    "1000",
                    "--out",
                    str(out_dir / "mass_equations_rrc_projection_receipt.json"),
                    "--summary",
                    str(out_dir / "mass_equations_rrc_projection_receipt.md"),
                    "--curriculum",
                    str(out_dir / "mass_equations_rrc_projection_curriculum.jsonl"),
                    "--table",
                    str(out_dir / "mass_equations_rrc_projection_table.csv"),
                ],
                receipt=out_dir / "mass_equations_rrc_projection_receipt.json",
                curriculum=out_dir / "mass_equations_rrc_projection_curriculum.jsonl",
                claim_boundary="rrc-route-atlas-not-proof-atlas",
            )
        )
    return lanes


def run_lane(lane: Lane, out_dir: Path, timeout: int) -> dict[str, Any]:
    started = time.time()
    stdout_path = out_dir / f"{lane.name}.stdout.txt"
    stderr_path = out_dir / f"{lane.name}.stderr.txt"
    try:
        proc = subprocess.run(
            lane.cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout_path.write_text(proc.stdout, encoding="utf-8", errors="replace")
        stderr_path.write_text(proc.stderr, encoding="utf-8", errors="replace")
        status = "PASS" if proc.returncode == 0 else "FAIL"
        error = None
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8", errors="replace")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8", errors="replace")
        status = "TIMEOUT"
        error = f"timeout after {timeout}s"
        returncode = None

    receipt_exists = lane.receipt.exists() if lane.receipt else False
    receipt_hash = None
    if receipt_exists and lane.receipt:
        receipt_hash = sha256_text(lane.receipt.read_text(encoding="utf-8", errors="replace"))
    return {
        "name": lane.name,
        "status": status,
        "returncode": returncode,
        "elapsed_s": round(time.time() - started, 3),
        "cmd": lane.cmd,
        "receipt": rel(lane.receipt),
        "receipt_exists": receipt_exists,
        "receipt_file_sha256": receipt_hash,
        "curriculum": rel(lane.curriculum),
        "stdout": rel(stdout_path),
        "stderr": rel(stderr_path),
        "claim_boundary": lane.claim_boundary,
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=min(6, os.cpu_count() or 2))
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--out-dir", type=Path, default=SHIM / "parallel_metaprobe_runs" / timestamp())
    parser.add_argument("--skip-rrc", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    lanes = lane_set(args.out_dir, include_rrc=not args.skip_rrc)

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(run_lane, lane, args.out_dir, args.timeout): lane for lane in lanes}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({"lane": result["name"], "status": result["status"], "elapsed_s": result["elapsed_s"]}, sort_keys=True))

    results.sort(key=lambda item: item["name"])
    receipt = {
        "schema": "parallel_metaprobe_launcher_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workers": args.workers,
        "timeout_s": args.timeout,
        "lane_count": len(results),
        "status_counts": {status: sum(1 for item in results if item["status"] == status) for status in sorted({item["status"] for item in results})},
        "lanes": results,
        "decision": "HOLD",
        "claim_boundary": (
            "Parallel metaprobe launch receipt only. These lanes generate route priors, "
            "coverage receipts, and negative-control surfaces; no lane promotes a theorem, "
            "dataset ingest, compression benchmark, or byte-law win without separate replay."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    receipt_path = args.out_dir / "parallel_metaprobe_launcher_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": rel(receipt_path), "receipt_hash": receipt["receipt_hash"], "status_counts": receipt["status_counts"]}, indent=2, sort_keys=True))
    return 0 if receipt["status_counts"].get("FAIL", 0) == 0 and receipt["status_counts"].get("TIMEOUT", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
