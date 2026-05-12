#!/usr/bin/env python3
"""Noise-environment residual shaver for Quandela/Perceval tasking.

This does not submit quantum jobs or claim quantum advantage. It classifies
residuals from dry-run job specs into components that a noisy photonic sampling
environment might help reduce, versus components that should stay classical or
blocked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"


NOISE_HELPFUL_COMPONENTS = {
    "sampling_variance",
    "symmetry_ambiguity",
    "collision_surface",
    "interference_search",
}

NOISE_HARMFUL_COMPONENTS = {
    "coherent_model_bias",
    "hardware_loss",
    "calibration_gap",
    "credential_gap",
    "theorem_gap",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_job_receipt(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def inferred_residual_components(job: dict[str, Any]) -> list[dict[str, Any]]:
    """Attach a conservative latent residual model to a dry-run job spec."""
    job_id = job.get("job_id", "")
    target = job.get("target", "")
    if job_id == "pcvl_local_triangle_smoke":
        return [
            {"kind": "sampling_variance", "mass": 0.03},
            {"kind": "calibration_gap", "mass": 0.02},
        ]
    if job_id == "pcvl_compression_kernel_probe":
        return [
            {"kind": "symmetry_ambiguity", "mass": 0.08},
            {"kind": "collision_surface", "mass": 0.06},
            {"kind": "coherent_model_bias", "mass": 0.04},
        ]
    if target == "quandela_cloud_remote_job":
        if job_id == "quandela_stochastic_crc_photonic_probe_hold":
            return [
                {"kind": "interference_search", "mass": 0.10},
                {"kind": "sampling_variance", "mass": 0.10},
                {"kind": "symmetry_ambiguity", "mass": 0.06},
                {"kind": "collision_surface", "mass": 0.04},
                {"kind": "hardware_loss", "mass": 0.06},
                {"kind": "credential_gap", "mass": 0.05},
                {"kind": "calibration_gap", "mass": 0.04},
            ]
        return [
            {"kind": "interference_search", "mass": 0.12},
            {"kind": "sampling_variance", "mass": 0.08},
            {"kind": "hardware_loss", "mass": 0.08},
            {"kind": "credential_gap", "mass": 0.05},
            {"kind": "theorem_gap", "mass": 0.03},
        ]
    return [{"kind": "coherent_model_bias", "mass": 0.01}]


def classify_component(component: dict[str, Any]) -> dict[str, Any]:
    kind = component["kind"]
    mass = float(component["mass"])
    if kind in NOISE_HELPFUL_COMPONENTS:
        return {
            **component,
            "noise_alignment": 1.0,
            "route": "candidate_for_noise_shaving",
            "reason": "Residual is stochastic, symmetry-like, collision-like, or sampling-distribution shaped.",
        }
    if kind in NOISE_HARMFUL_COMPONENTS:
        return {
            **component,
            "noise_alignment": 0.0,
            "route": "do_not_promote_to_noise",
            "reason": "Residual is model bias, hardware debt, access gating, or proof debt; noise will not make it true.",
        }
    return {
        **component,
        "noise_alignment": 0.25,
        "route": "hold_for_manual_classification",
        "reason": "Residual class is unknown.",
    }


def shave_job(job: dict[str, Any]) -> dict[str, Any]:
    components = [classify_component(component) for component in inferred_residual_components(job)]
    total_mass = sum(float(component["mass"]) for component in components)
    helpful_mass = sum(
        float(component["mass"]) * float(component["noise_alignment"])
        for component in components
        if component["route"] == "candidate_for_noise_shaving"
    )
    harmful_mass = sum(
        float(component["mass"])
        for component in components
        if component["route"] == "do_not_promote_to_noise"
    )
    shave_score = helpful_mass / total_mass if total_mass else 0.0
    post_noise_residual_floor = max(0.0, total_mass - helpful_mass)

    if job.get("target") == "quandela_cloud_remote_job":
        activation = "held_remote_noise_candidate_requires_token_provider_budget_manual_submit"
        promotable_now = False
    elif shave_score >= 0.55 and harmful_mass <= helpful_mass:
        activation = "local_sim_noise_sweep_candidate_after_perceval_install"
        promotable_now = False
    else:
        activation = "keep_classical_or_hold"
        promotable_now = False

    payload = {
        "job_id": job.get("job_id"),
        "target": job.get("target"),
        "job_hash": job.get("job_hash"),
        "activation": activation,
        "promotable_now": promotable_now,
        "residual_components": components,
        "residual_total_mass": total_mass,
        "noise_helpful_mass": helpful_mass,
        "noise_harmful_mass": harmful_mass,
        "noise_shave_score": shave_score,
        "post_noise_residual_floor": post_noise_residual_floor,
        "claim_boundary": (
            "Noise shaving is a routing prior only. It may reduce sampling-shaped residuals in simulation, "
            "but it does not repair model bias, hardware loss, proof gaps, or cloud authorization gates."
        ),
    }
    payload["shave_hash"] = sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return payload


def build_receipt(job_receipt_path: Path) -> dict[str, Any]:
    source = load_job_receipt(job_receipt_path)
    shaves = [shave_job(job) for job in source.get("jobs", [])]
    total = len(shaves) or 1
    candidate_count = sum(1 for item in shaves if "candidate" in item["activation"])
    held_remote_count = sum(1 for item in shaves if item["activation"].startswith("held_remote"))
    return {
        "schema": "quandela_noise_residual_shaver_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "surface_id": "quandela_noise_residual_shaver",
        "source_job_receipt": str(job_receipt_path),
        "source_queue_hash": source.get("queue_hash"),
        "source_job_count": source.get("job_count"),
        "principle": (
            "Use the photonic noise environment as a residual shaver only for uncertainty that is already "
            "sampling-distribution shaped; block residuals that are proof debt, model bias, or access control."
        ),
        "triangle_square_extension": {
            "triangle": "smallest constrained problem kernel",
            "square": "available local/cloud execution surface",
            "noise_skin": "stochastic photonic sampler layer over the square surface",
            "rule": "Only the triangle residual that aligns with the noise skin may be promoted; everything else is classical debt.",
        },
        "shaves": shaves,
        "noise_candidate_count": candidate_count,
        "held_remote_noise_candidates": held_remote_count,
        "promotable_now": sum(1 for item in shaves if item["promotable_now"]),
        "average_noise_shave_score": sum(item["noise_shave_score"] for item in shaves) / total,
        "claim_boundary": (
            "Dry-run routing receipt only. No Perceval execution, no Quandela cloud job, no token handling, "
            "no QPU usage, and no theorem/solver claim."
        ),
        "lawful": True,
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a quantum-noise residual router. Return compact JSON and preserve claim boundaries."
    records = []
    for item in receipt["shaves"]:
        prompt = {
            "task": "classify_noise_residual_shaving",
            "job_id": item["job_id"],
            "target": item["target"],
            "components": item["residual_components"],
            "noise_shave_score": item["noise_shave_score"],
        }
        answer = {
            "selected": "candidate" in item["activation"],
            "use_as": "noise_residual_routing_prior",
            "job_id": item["job_id"],
            "activation": item["activation"],
            "noise_shave_score": item["noise_shave_score"],
            "post_noise_residual_floor": item["post_noise_residual_floor"],
            "shave_hash": item["shave_hash"],
            "claim_boundary": item["claim_boundary"],
            "receipt_rule": "Require component-level residual class, source queue hash, shave hash, and explicit no-submit boundary.",
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
        "tags: ResearchStack Quandela Perceval Quantum Noise Residuals TriangleSquare",
        "title: Quandela Noise Residual Shaver",
        "type: text/vnd.tiddlywiki",
        "",
        "! Quandela Noise Residual Shaver",
        "",
        "This tiddler records the dry-run rule for treating a noisy photonic environment as a residual-shaving skin over the Quandela tasking surface.",
        "",
        "Durable source: `4-Infrastructure/shim/quandela_noise_residual_shaver.py`",
        "",
        "Receipt: `4-Infrastructure/shim/quandela_noise_residual_shaver_receipt.json`",
        "",
        "Curriculum: `4-Infrastructure/shim/quandela_noise_residual_shaver_curriculum.jsonl`",
        "",
        "!! Principle",
        "",
        receipt["principle"],
        "",
        "!! Stochastic CRC Lane",
        "",
        "The `quandela_stochastic_crc_photonic_probe_hold` job routes the braided-field micro-noise CRC witness into a held photonic/noisy sampler candidate.",
        "",
        "The useful contract is:",
        "",
        "```",
        "seeded noise lane -> photonic/noisy sample candidate -> local CRC replay classifier",
        "```",
        "",
        "The remote output is a recovery/degradation signal only. It is not a proof and is not accepted without local replay.",
        "",
        "!! Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "!! Jobs",
        "",
    ]
    for item in receipt["shaves"]:
        lines.append(
            f"* `{item['job_id']}` -> activation `{item['activation']}`; "
            f"score `{item['noise_shave_score']:.4f}`; floor `{item['post_noise_residual_floor']:.4f}`"
        )
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[Quandela Job Tasking Surface]]",
            "* [[MCP Bus Live Safe Probe]]",
            "* [[OpenClaw Shared Bus Surface]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=Path, default=SHIM / "quandela_job_tasking_surface_receipt.json")
    parser.add_argument("--receipt", type=Path, default=SHIM / "quandela_noise_residual_shaver_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "quandela_noise_residual_shaver_curriculum.jsonl")
    parser.add_argument("--wiki", type=Path, default=WIKI / "Quandela Noise Residual Shaver.tid")
    args = parser.parse_args()

    receipt = build_receipt(args.jobs)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_wiki(receipt, args.wiki)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
