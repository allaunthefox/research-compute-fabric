#!/usr/bin/env python3
"""Autonomous Speedrun Harness Gate.

Scores autonomous experiment records for Builder/Judge/Warden viability and emits
a FAMM-compatible receipt. This is benchmark-agnostic: nanoGPT speedrun is the
reference pattern, but the schema applies to any autonomous research loop.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload=json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def score_experiment(exp: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    metric = exp.get("metric", {})
    judge = exp.get("judge", {})
    warden = exp.get("warden", {})
    compute = exp.get("compute", {})

    target = float(cfg.get("target_metric", metric.get("target", 0.0)))
    value = float(metric.get("value", target))
    mode = cfg.get("metric_mode", "lower_is_better")
    margin = (target - value) if mode == "lower_is_better" else (value - target)

    noise_floor = float(judge.get("noise_floor", cfg.get("noise_floor", 0.0)))
    seeds = int(judge.get("seeds", 1))
    rule_pass = bool(judge.get("rule_pass", False))
    reproducible = bool(judge.get("reproducible", False))
    statistical_pass = rule_pass and reproducible and margin >= noise_floor and seeds >= int(cfg.get("min_seeds", 1))

    stale_hours = float(warden.get("source_stale_hours", 0.0))
    stale_limit = float(cfg.get("source_refresh_hours", 12.0))
    local_loop = float(warden.get("local_loop_score", 0.0))
    overfit = float(warden.get("overfit_risk", 0.0))
    invalid = 1.0 if not rule_pass else 0.0
    warden_penalty = clamp01(0.35*(stale_hours/stale_limit) + 0.30*local_loop + 0.25*overfit + 0.10*invalid)

    cost_hours = float(compute.get("gpu_hours", 0.0))
    token_cost = float(compute.get("tokens", 0.0)) / 1e9
    cost_pressure = math.log1p(max(0.0, cost_hours) + token_cost) / 10.0

    promise = clamp01(0.5 + margin / max(1.0, abs(target)))
    receipt_strength = clamp01(0.25*float(rule_pass) + 0.25*float(reproducible) + 0.25*min(1.0, seeds/max(1,int(cfg.get("min_seeds",1)))) + 0.25*(1.0-warden_penalty))

    decision = "PROMOTE" if statistical_pass and warden_penalty < float(cfg.get("warden_threshold", 0.45)) else "SCAR_OR_COARSEN"

    result = {
        "experiment_id": exp.get("id", sha256_json(exp)[:12]),
        "idea_hash": sha256_json(exp.get("idea", {})),
        "patch_hash": sha256_json(exp.get("patch", {})),
        "config_hash": sha256_json(exp.get("config", {})),
        "run_hash": sha256_json(exp.get("run", {})),
        "margin": margin,
        "statistical_pass": statistical_pass,
        "warden_penalty": warden_penalty,
        "cost_pressure": cost_pressure,
        "promise": promise,
        "receipt_strength": receipt_strength,
        "decision": decision,
        "coarsening_agent": None if decision == "PROMOTE" else {
            "type": "failed_experiment_basin",
            "action": "downweight_fine_search_until_source_refresh_or_new_evidence",
            "reasons": [k for k,v in {
                "below_noise_floor": margin < noise_floor,
                "insufficient_seeds": seeds < int(cfg.get("min_seeds",1)),
                "rule_or_repro_fail": not (rule_pass and reproducible),
                "source_stale": stale_hours > stale_limit,
                "local_loop": local_loop > 0.5,
                "overfit_risk": overfit > 0.5,
            }.items() if v]
        }
    }
    result["delta_edge_hash"] = sha256_json(result)
    return result


def run(config: dict[str, Any]) -> dict[str, Any]:
    experiments = config.get("experiments", [])
    scored = [score_experiment(e, config) for e in experiments]
    promoted = [s for s in scored if s["decision"] == "PROMOTE"]
    scarred = [s for s in scored if s["decision"] != "PROMOTE"]

    harness = config.get("harness", {})
    nuvmap = {
        "goal_hash": sha256_json(harness.get("goal", {})),
        "agents_hash": sha256_json(harness.get("agents", {})),
        "plan_hash": sha256_json(harness.get("plan", {})),
        "thread_hash": sha256_json(harness.get("thread", {})),
        "source_refresh_hash": sha256_json(harness.get("source_refresh", {})),
        "delta_edge_hashes": [s["delta_edge_hash"] for s in scored],
    }
    nuvmap["frontier_hash"] = sha256_json(nuvmap)

    receipt = {
        "receipt_type": "famm_autonomous_speedrun_harness_receipt",
        "schema_version": "0.1.0",
        "source_pattern": "Prime Intellect auto-nanoGPT autonomous speedrun harness",
        "harness": harness,
        "config": {k:v for k,v in config.items() if k not in {"experiments", "harness"}},
        "scored_experiments": scored,
        "summary": {
            "experiment_count": len(scored),
            "promoted_count": len(promoted),
            "scarred_or_coarsened_count": len(scarred),
        },
        "nuvmap": nuvmap,
        "no_drift_boundary": "This is a harness/receipt layer for autonomous research loops, not a claim that agents discover truth without external verification.",
    }
    receipt["receipt_hash"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args=parser.parse_args()
    config=json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt=run(config)
    out=Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Experiments: {receipt['summary']['experiment_count']}")
    print(f"Promoted: {receipt['summary']['promoted_count']}")
    print(f"Scarred/coarsened: {receipt['summary']['scarred_or_coarsened_count']}")
    print(f"Frontier hash: {receipt['nuvmap']['frontier_hash']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")

if __name__ == "__main__":
    main()
