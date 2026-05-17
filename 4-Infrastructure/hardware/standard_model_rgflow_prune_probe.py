#!/usr/bin/env python3
"""Scoped RGFlow prune probe for the Standard Model route slice.

This runner keeps the existing RGFlow codebase filter as the first pass, then
adds route-pruning semantics for generated build products and promotion holds.
It does not delete files.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RGFLOW_PATH = REPO / "5-Applications/scripts/rgflow_codebase_filter.py"

FOCUS_TARGETS = [
    "4-Infrastructure/hardware/standard_model_residual_accounting_probe.py",
    "4-Infrastructure/hardware/standard_model_residual_accounting_probe_receipt.json",
    "4-Infrastructure/hardware/standard_model_projection_sensitivity_probe.py",
    "4-Infrastructure/hardware/standard_model_projection_sensitivity_probe_receipt.json",
    "4-Infrastructure/hardware/standard_model_w_conservation_guard.py",
    "4-Infrastructure/hardware/standard_model_w_conservation_guard_receipt.json",
    "4-Infrastructure/hardware/standard_model_connectome_reconfiguration_runner.py",
    "4-Infrastructure/hardware/standard_model_connectome_reconfiguration_receipt.json",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Standard Model Lagrangian Eigen Probe.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Semantic Basin Partition Fairness Prior.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Classical Signal Roots Quantum Translation Program.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Root Lift Semantic Collider.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Decision Diagram Compression Tuning Prior.tid",
]


def load_rgflow_filter() -> Any:
    sys.path.insert(0, str(REPO / "5-Applications"))
    spec = importlib.util.spec_from_file_location("rgflow_codebase_filter", RGFLOW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load RGFlow filter from {RGFLOW_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RGFlowCodebaseFilter(root_path=str(REPO))


def git_untracked_hardware() -> list[str]:
    proc = subprocess.run(
        [
            "git",
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            "4-Infrastructure/hardware",
        ],
        cwd=REPO,
        check=True,
        text=True,
        capture_output=True,
    )
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith("?? "):
            paths.append(line[3:])
    return paths


def classify_path(path: str, text: str) -> dict[str, Any]:
    reasons: list[str] = []
    action = "retain"

    if "/obj_dir/" in path or path.startswith("4-Infrastructure/hardware/obj_dir/"):
        action = "prune_from_git_surface"
        reasons.append("verilator_generated_obj_dir")

    if path.endswith(".fs") or path.endswith("_pnr.json"):
        action = "prune_from_git_surface"
        reasons.append("fpga_build_product")

    if "diagnostic_only" in text:
        action = "prune_from_promotion_path"
        reasons.append("diagnostic_only_marker")

    if "hold_for_route_trial" in text:
        action = "hold_for_route_trial"
        reasons.append("route_trial_required")

    if "metadata_cost_proxy" in text and "not byte-priced" in text:
        if action == "retain":
            action = "hold_for_route_trial"
        reasons.append("unpriced_metadata_cost")

    if path.endswith("_receipt.json"):
        reasons.append("receipt_evidence")
        if action == "retain":
            action = "retain_as_evidence"

    if not reasons:
        reasons.append("no_prune_signal")

    return {"action": action, "reasons": reasons}


def analyze_path(rgflow: Any, rel: str) -> dict[str, Any]:
    path = REPO / rel
    if not path.exists():
        return {"path": rel, "missing": True, "action": "missing"}

    text = path.read_text(encoding="utf-8", errors="ignore")
    rg = rgflow.analyze_file(path)
    semantic = classify_path(rel, text)

    action = semantic["action"]
    reasons = list(semantic["reasons"])
    if not rg.lawful_under_flow:
        action = "prune_from_promotion_path"
        reasons.append("rgflow_unlawful_under_flow")
    if rg.flows_to_noise:
        reasons.append("rgflow_flows_to_noise")
    if rg.flows_to_sabotage:
        reasons.append("rgflow_flows_to_sabotage")

    return {
        "path": rel,
        "bytes": path.stat().st_size,
        "rgflow": {
            "lawful_now": bool(rg.lawful_now),
            "lawful_under_flow": bool(rg.lawful_under_flow),
            "reaches_attractor": bool(rg.reaches_attractor),
            "flows_to_noise": bool(rg.flows_to_noise),
            "flows_to_sabotage": bool(rg.flows_to_sabotage),
            "adaptation_cost": float(rg.adaptation_cost),
            "stability_margin": float(rg.stability_margin),
            "rg_depth": int(rg.rg_depth),
            "attractor_id": int(rg.attractor_id),
            "failure_mask": int(rg.failure_mask),
        },
        "action": action,
        "reasons": reasons,
    }


def normalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: normalize_for_hash(v)
            for k, v in value.items()
            if k not in {"generated_at_utc", "receipt_hash", "bytes"}
        }
    if isinstance(value, list):
        return [normalize_for_hash(v) for v in value]
    return value


def stable_hash(payload: dict[str, Any]) -> str:
    stable = normalize_for_hash(payload)
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    rgflow = load_rgflow_filter()
    hardware_untracked = git_untracked_hardware()
    generated_targets = [
        p
        for p in hardware_untracked
        if "/obj_dir/" in p
        or p.endswith(".fs")
        or p.endswith("_pnr.json")
    ]
    targets = list(dict.fromkeys(FOCUS_TARGETS + generated_targets))
    analyses = [analyze_path(rgflow, rel) for rel in targets]

    actions: dict[str, int] = {}
    for item in analyses:
        actions[item["action"]] = actions.get(item["action"], 0) + 1

    receipt: dict[str, Any] = {
        "runner": "standard_model_rgflow_prune_probe.py",
        "rgflow_source": str(RGFLOW_PATH.relative_to(REPO)),
        "target_count": len(targets),
        "summary": {
            "all_focus_targets_rgflow_lawful": all(
                item.get("rgflow", {}).get("lawful_under_flow", False)
                for item in analyses
                if item["path"] in FOCUS_TARGETS
            ),
            "action_counts": actions,
            "prune_from_git_surface_count": actions.get("prune_from_git_surface", 0),
            "prune_from_promotion_path_count": actions.get("prune_from_promotion_path", 0),
            "hold_for_route_trial_count": actions.get("hold_for_route_trial", 0),
        },
        "prune_boundary": (
            "prune means remove from git or promotion/evaluator path; this runner "
            "does not delete local files"
        ),
        "analyses": analyses,
    }
    receipt["receipt_hash"] = stable_hash(receipt)

    out = Path(__file__).with_name("standard_model_rgflow_prune_probe_receipt.json")
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    print(f"receipt: {out}")
    print(f"receipt_hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
