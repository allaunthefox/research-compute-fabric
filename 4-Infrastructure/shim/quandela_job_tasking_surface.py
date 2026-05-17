#!/usr/bin/env python3
"""Quandela/Perceval job tasking surface with Triangle-in-Square pruning.

This creates a dry-run queue for photonic quantum simulation/QPU tasking. It
does not install Perceval, save tokens, submit remote jobs, or execute circuits.
The point is to make the job membrane explicit before any cloud or QPU surface
is touched.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
PERCEVAL = REPO / "5-Applications" / "tools-scripts" / "external" / "quantum" / "perceval"
NOISE_RECEIPT = REPO / "4-Infrastructure" / "hardware" / "noise_stability_sim_receipt.json"
EIGEN_TRAJECTORY = REPO / "4-Infrastructure" / "hardware" / "eigenvalue_trajectory.png"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_git(path: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(path), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def perceval_available() -> dict[str, Any]:
    spec = importlib.util.find_spec("perceval")
    if spec is None:
        return {"installed": False, "version": None}
    try:
        import perceval as pcvl  # type: ignore

        return {"installed": True, "version": getattr(pcvl, "__version__", None)}
    except Exception as exc:
        return {"installed": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}


def triangle_square_fit(triangle: dict[str, float], square: dict[str, float]) -> dict[str, Any]:
    ratios = {}
    overflow = {}
    for key, value in triangle.items():
        capacity = max(float(square.get(key, 0.0)), 1e-9)
        ratios[key] = min(1.0, float(value) / capacity)
        overflow[key] = max(0.0, float(value) - capacity)
    fit_score = sum(ratios.values()) / (len(ratios) or 1)
    residual_mass = sum(overflow.values())
    fits_square = residual_mass == 0.0
    return {
        "fit_score": fit_score,
        "residual_mass": residual_mass,
        "fits_square": fits_square,
        "ratios": ratios,
        "overflow": overflow,
        "rule": "Route only the residual that does not fit the local square; do not submit broad unpruned jobs.",
    }


def load_stochastic_crc_source() -> dict[str, Any]:
    if not NOISE_RECEIPT.exists():
        return {
            "available": False,
            "path": str(NOISE_RECEIPT.relative_to(REPO)),
            "receipt_hash": None,
            "crc32_hex": None,
            "payload_sha256": None,
            "eigen_trajectory_hash": file_hash(EIGEN_TRAJECTORY),
        }
    receipt = json.loads(NOISE_RECEIPT.read_text(encoding="utf-8"))
    crc = receipt.get("micro_gain", {}).get("stochastic_crc", {})
    return {
        "available": True,
        "path": str(NOISE_RECEIPT.relative_to(REPO)),
        "receipt_hash": receipt.get("receipt_hash_preimage_sha256"),
        "crc32_hex": crc.get("crc32_hex"),
        "payload_sha256": crc.get("payload_sha256"),
        "byte_length": crc.get("byte_length"),
        "eigen_trajectory": str(EIGEN_TRAJECTORY.relative_to(REPO)),
        "eigen_trajectory_hash": file_hash(EIGEN_TRAJECTORY),
        "claim_boundary": crc.get("claim_boundary"),
    }


def build_jobs() -> list[dict[str, Any]]:
    stochastic_crc = load_stochastic_crc_source()
    local_square = {
        "modes": 8,
        "photons": 4,
        "depth": 24,
        "shots": 1000,
    }
    cloud_square = {
        "modes": 32,
        "photons": 12,
        "depth": 128,
        "shots": 100000,
    }
    candidates = [
        {
            "job_id": "pcvl_local_triangle_smoke",
            "intent": "minimal photonic circuit simulation smoke",
            "target": "local_perceval_simulator",
            "triangle": {"modes": 4, "photons": 2, "depth": 8, "shots": 100},
            "square": local_square,
        },
        {
            "job_id": "pcvl_compression_kernel_probe",
            "intent": "compression/eigenvector kernel probe after classical pruning",
            "target": "local_perceval_simulator",
            "triangle": {"modes": 8, "photons": 4, "depth": 24, "shots": 1000},
            "square": local_square,
        },
        {
            "job_id": "quandela_remote_residual_hold",
            "intent": "remote QPU/cloud residual candidate after Triangle-in-Square pruning",
            "target": "quandela_cloud_remote_job",
            "triangle": {"modes": 16, "photons": 8, "depth": 64, "shots": 10000},
            "square": cloud_square,
        },
        {
            "job_id": "quandela_stochastic_crc_photonic_probe_hold",
            "intent": "photonic/noisy sampler probe for stochastic CRC replay witness over the braided-field eigen-noise lane",
            "target": "quandela_cloud_remote_job",
            "triangle": {"modes": 8, "photons": 4, "depth": 32, "shots": 4096},
            "square": cloud_square,
            "source_artifacts": stochastic_crc,
            "expected_contract": {
                "input": "stochastic_crc_lane_v1 payload hash plus eigenvalue trajectory witness",
                "remote_output": "sample/count distribution or failed/degraded packet candidate",
                "local_acceptance": "accepted only if local replay maps result to the same canonical CRC witness or an explicitly classified degradation",
            },
        },
    ]
    jobs = []
    for candidate in candidates:
        fit = triangle_square_fit(candidate["triangle"], candidate["square"])
        target = candidate["target"]
        if target == "quandela_cloud_remote_job":
            activation = "held_requires_token_provider_budget_and_manual_submit"
            lawful_to_run_now = False
        elif fit["fits_square"]:
            activation = "dry_run_queue_only_until_perceval_installed"
            lawful_to_run_now = False
        else:
            activation = "prune_before_queue"
            lawful_to_run_now = False
        job = {
            **candidate,
            "fit": fit,
            "activation": activation,
            "lawful_to_run_now": lawful_to_run_now,
            "claim_boundary": "Job spec only. No Perceval execution, no token storage, no cloud submission, and no QPU time is consumed.",
            "job_hash": sha256_text(json.dumps(candidate, sort_keys=True, ensure_ascii=False)),
        }
        jobs.append(job)
    return jobs


def build_receipt() -> dict[str, Any]:
    readme = PERCEVAL / "README.md"
    pyproject = PERCEVAL / "pyproject.toml"
    jobs = build_jobs()
    installed = perceval_available()
    queue_hash = sha256_text(json.dumps(jobs, sort_keys=True, ensure_ascii=False))
    return {
        "schema": "quandela_job_tasking_surface_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "surface_id": "quandela_perceval_job_tasking",
        "claim_boundary": "Quandela/Perceval is enabled only as a dry-run job-tasking surface. Remote execution requires explicit credential, provider, budget, and manual-submit receipts.",
        "perceval_reference": {
            "path": str(PERCEVAL.relative_to(REPO)),
            "remote": run_git(PERCEVAL, "remote", "get-url", "origin"),
            "commit": run_git(PERCEVAL, "rev-parse", "HEAD"),
            "readme_hash": file_hash(readme),
            "pyproject_hash": file_hash(pyproject),
            "installed": installed,
            "source_claims": [
                "Perceval is a Python framework for photonic quantum circuits and simulations.",
                "Perceval interfaces with available QPUs on Quandela cloud.",
                "Perceval runtime exposes local and remote job abstractions.",
            ],
        },
        "stochastic_crc_source": load_stochastic_crc_source(),
        "triangle_in_square_hole": {
            "definition": "A routing/pruning primitive where the triangle is the smallest constrained problem kernel and the square hole is the available execution surface. Only residual mismatch may be queued for heavier simulation/QPU tasking.",
            "purpose": "Cut work before quantum/cloud submission by fitting the classical kernel into local capacity first.",
            "required_receipts": ["triangle_shape", "square_capacity", "fit_score", "residual_mass", "job_hash", "claim_boundary"],
        },
        "jobs": jobs,
        "queue_hash": queue_hash,
        "job_count": len(jobs),
        "held_remote_jobs": sum(1 for job in jobs if job["target"] == "quandela_cloud_remote_job"),
        "runnable_now": sum(1 for job in jobs if job["lawful_to_run_now"]),
        "lawful": True,
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a Quandela/Perceval job-tasking router. Return compact JSON and never submit jobs without receipts."
    records = []
    for job in receipt["jobs"]:
        prompt = {
            "task": "route_quandela_job",
            "job_id": job["job_id"],
            "intent": job["intent"],
            "target": job["target"],
            "fit": job["fit"],
            "activation": job["activation"],
            "claim_boundary": job["claim_boundary"],
        }
        answer = {
            "selected": False,
            "use_as": "quandela_job_tasking_prior",
            "job_id": job["job_id"],
            "target": job["target"],
            "activation": job["activation"],
            "job_hash": job["job_hash"],
            "source_path": receipt["perceval_reference"]["path"],
            "source_hash": receipt["perceval_reference"]["readme_hash"],
            "claim_boundary": receipt["claim_boundary"],
            "receipt_rule": "Require triangle/square fit receipt, credential pointer, provider, budget, and manual-submit approval before execution.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    return records


def write_wiki(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "created: 20260507000000000",
        "modified: 20260507000000000",
        "tags: ResearchStack Quandela Perceval Quantum TriangleSquare JobTasking",
        "title: Quandela Job Tasking Surface",
        "type: text/vnd.tiddlywiki",
        "",
        "! Quandela Job Tasking Surface",
        "",
        "This surface queues dry-run Perceval/Quandela job specs behind the Triangle-in-a-Square-Hole pruning primitive.",
        "",
        "Durable source: `4-Infrastructure/shim/quandela_job_tasking_surface.py`",
        "",
        "Receipt: `4-Infrastructure/shim/quandela_job_tasking_surface_receipt.json`",
        "",
        "Curriculum: `4-Infrastructure/shim/quandela_job_tasking_surface_curriculum.jsonl`",
        "",
        f"Perceval snapshot: `{receipt['perceval_reference']['path']}`",
        f"Perceval commit: `{receipt['perceval_reference']['commit']}`",
        "",
        "!! Stochastic CRC Photonic Probe",
        "",
        "The braid-field noise lane is now queued as a held photonic/noisy sampler candidate.",
        "",
        f"Noise receipt: `{receipt['stochastic_crc_source']['path']}`",
        f"Noise receipt hash: `{receipt['stochastic_crc_source']['receipt_hash']}`",
        f"CRC32 witness: `{receipt['stochastic_crc_source']['crc32_hex']}`",
        f"CRC payload hash: `{receipt['stochastic_crc_source']['payload_sha256']}`",
        "",
        "Remote output is never accepted directly. It must be replayed locally against the stochastic CRC witness and classified as recovered, degraded, or failed.",
        "",
        "!! Triangle In A Square Hole",
        "",
        receipt["triangle_in_square_hole"]["definition"],
        "",
        "!! Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "!! Jobs",
        "",
    ]
    for job in receipt["jobs"]:
        lines.append(f"* `{job['job_id']}` -> {job['target']}; activation `{job['activation']}`; residual `{job['fit']['residual_mass']}`")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[MCP Bus Live Safe Probe]]",
            "* [[MCP Surface Catalog]]",
            "* [[OpenClaw Shared Bus Surface]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=SHIM / "quandela_job_tasking_surface_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "quandela_job_tasking_surface_curriculum.jsonl")
    parser.add_argument("--wiki", type=Path, default=WIKI / "Quandela Job Tasking Surface.tid")
    args = parser.parse_args()
    receipt = build_receipt()
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_wiki(receipt, args.wiki)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
