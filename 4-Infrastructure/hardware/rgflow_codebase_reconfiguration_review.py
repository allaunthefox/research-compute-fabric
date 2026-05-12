#!/usr/bin/env python3
"""Review the live codebase with a reconfigured RGFlow prune equation.

The older RGFlow codebase filter answers a broad question:
  does this artifact remain lawful under scale flow?

For repo hygiene and route promotion, that is not sharp enough. This review
adds a codebase-specific prune equation over the live git surface:

  review_pressure =
    generatedness
    + churn_pressure
    + promotion_risk
    + unpriced_debt
    - evidence_strength
    - source_anchor

The runner writes a receipt and never deletes files.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RGFLOW_PATH = REPO / "5-Applications/scripts/rgflow_codebase_filter.py"
MAX_TEXT_BYTES = 1_000_000

GENERATED_PATH_PATTERNS = (
    "/obj_dir/",
    "/__pycache__/",
)

GENERATED_SUFFIXES = (
    ".pyc",
    ".o",
    ".d",
    ".fs",
    "_pnr.json",
    ".stl",
    ".png",
    ".log",
    ".agdai",
)

CHURN_PATTERNS = (
    ".changes/",
    "/concrete-history/",
    "/edits-history/",
    "batch_lean_checker_",
)

SOURCE_EXTENSIONS = {
    ".py",
    ".lean",
    ".v",
    ".sv",
    ".cpp",
    ".c",
    ".h",
    ".md",
    ".tid",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


@dataclass
class ReviewVector:
    generatedness: int = 0
    churn_pressure: int = 0
    promotion_risk: int = 0
    unpriced_debt: int = 0
    evidence_strength: int = 0
    source_anchor: int = 0

    @property
    def review_pressure(self) -> int:
        return (
            self.generatedness
            + self.churn_pressure
            + self.promotion_risk
            + self.unpriced_debt
            - self.evidence_strength
            - self.source_anchor
        )


def load_rgflow_filter() -> Any:
    sys.path.insert(0, str(REPO / "5-Applications"))
    spec = importlib.util.spec_from_file_location("rgflow_codebase_filter", RGFLOW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load RGFlow filter from {RGFLOW_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RGFlowCodebaseFilter(root_path=str(REPO))


def git_status_paths() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    rows: list[dict[str, str]] = []
    entries = proc.stdout.decode("utf-8", errors="ignore").split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:]
        if status.startswith("R") or status.startswith("C"):
            if i < len(entries):
                path = entries[i]
                i += 1
        rows.append({"status": status, "path": path})
    return rows


def read_text_if_small(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    if path.stat().st_size > MAX_TEXT_BYTES:
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def score_item(rel: str, status: str, text: str) -> tuple[ReviewVector, list[str]]:
    vector = ReviewVector()
    reasons: list[str] = []
    suffix = Path(rel).suffix
    semantic_text_surface = suffix in {".json", ".jsonl", ".tid", ".md"}

    if any(pattern in rel for pattern in GENERATED_PATH_PATTERNS) or rel.endswith(GENERATED_SUFFIXES):
        vector.generatedness += 3
        reasons.append("generated_or_binary_artifact")

    if any(pattern in rel for pattern in CHURN_PATTERNS):
        vector.churn_pressure += 3
        reasons.append("editor_or_checker_churn")

    if semantic_text_surface and "diagnostic_only" in text:
        vector.promotion_risk += 2
        reasons.append("diagnostic_only_marker")

    if semantic_text_surface and "hold_for_route_trial" in text:
        vector.promotion_risk += 2
        reasons.append("route_trial_hold")

    if semantic_text_surface and "metadata_cost_proxy" in text and "not byte-priced" in text:
        vector.unpriced_debt += 3
        reasons.append("unpriced_metadata_debt")

    if rel.endswith("_receipt.json"):
        vector.evidence_strength += 2
        reasons.append("receipt_evidence")

    if semantic_text_surface and ("exact_rehydration" in text or "byte_rehydration_hash" in text):
        vector.evidence_strength += 1
        reasons.append("exactness_marker")

    if suffix in SOURCE_EXTENSIONS and not any(pattern in rel for pattern in CHURN_PATTERNS):
        vector.source_anchor += 1
        reasons.append("source_or_wiki_anchor")

    if status.strip() == "M":
        vector.source_anchor += 1
        reasons.append("tracked_modified_artifact")

    if not reasons:
        reasons.append("low_information_status_entry")

    return vector, reasons


def choose_action(vector: ReviewVector, reasons: list[str]) -> str:
    if "editor_or_checker_churn" in reasons:
        return "prune_from_git_surface"
    if "generated_or_binary_artifact" in reasons and vector.source_anchor <= 0:
        return "prune_from_git_surface"
    if "diagnostic_only_marker" in reasons and "route_trial_hold" not in reasons:
        return "prune_from_promotion_path"
    if "route_trial_hold" in reasons or "unpriced_metadata_debt" in reasons:
        return "hold_for_route_trial"
    if vector.review_pressure >= 3:
        return "review_before_tracking"
    if vector.evidence_strength >= 2:
        return "retain_as_evidence"
    return "retain"


def rgflow_for_path(rgflow: Any, rel: str) -> dict[str, Any] | None:
    path = REPO / rel
    if not path.exists() or not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
        return None
    try:
        result = rgflow.analyze_file(path)
    except Exception as exc:  # noqa: BLE001 - receipt should record failure.
        return {"error": str(exc)}
    return {
        "lawful_now": bool(result.lawful_now),
        "lawful_under_flow": bool(result.lawful_under_flow),
        "reaches_attractor": bool(result.reaches_attractor),
        "flows_to_noise": bool(result.flows_to_noise),
        "flows_to_sabotage": bool(result.flows_to_sabotage),
        "stability_margin": float(result.stability_margin),
        "rg_depth": int(result.rg_depth),
        "attractor_id": int(result.attractor_id),
        "failure_mask": int(result.failure_mask),
    }


def normalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: normalize_for_hash(v)
            for k, v in value.items()
            if k not in {"receipt_hash", "bytes", "stability_margin"}
        }
    if isinstance(value, list):
        return [normalize_for_hash(v) for v in value]
    return value


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        normalize_for_hash(payload), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    rgflow = load_rgflow_filter()
    rows = git_status_paths()
    analyses: list[dict[str, Any]] = []

    for row in rows:
        rel = row["path"]
        path = REPO / rel
        text = read_text_if_small(path)
        vector, reasons = score_item(rel, row["status"], text)
        action = choose_action(vector, reasons)
        rg = rgflow_for_path(rgflow, rel)
        if rg and rg.get("lawful_under_flow") is False:
            action = "prune_from_promotion_path"
            reasons.append("rgflow_unlawful_under_flow")
        analyses.append(
            {
                "status": row["status"],
                "path": rel,
                "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                "vector": {
                    "generatedness": vector.generatedness,
                    "churn_pressure": vector.churn_pressure,
                    "promotion_risk": vector.promotion_risk,
                    "unpriced_debt": vector.unpriced_debt,
                    "evidence_strength": vector.evidence_strength,
                    "source_anchor": vector.source_anchor,
                    "review_pressure": vector.review_pressure,
                },
                "action": action,
                "reasons": reasons,
                "rgflow": rg,
            }
        )

    action_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for item in analyses:
        action_counts[item["action"]] = action_counts.get(item["action"], 0) + 1
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

    top_prune_candidates = [
        {
            "path": item["path"],
            "status": item["status"],
            "action": item["action"],
            "review_pressure": item["vector"]["review_pressure"],
            "reasons": item["reasons"],
        }
        for item in sorted(
            analyses,
            key=lambda x: (
                x["action"] not in {"prune_from_git_surface", "review_before_tracking"},
                -x["vector"]["review_pressure"],
                x["path"],
            ),
        )[:40]
    ]

    receipt: dict[str, Any] = {
        "runner": "rgflow_codebase_reconfiguration_review.py",
        "reconfigured_equation": (
            "review_pressure = generatedness + churn_pressure + promotion_risk "
            "+ unpriced_debt - evidence_strength - source_anchor"
        ),
        "scope": "live git status surface, not ignored files and not destructive cleanup",
        "rgflow_source": str(RGFLOW_PATH.relative_to(REPO)),
        "summary": {
            "reviewed_count": len(analyses),
            "status_counts": status_counts,
            "action_counts": action_counts,
            "prune_from_git_surface_count": action_counts.get("prune_from_git_surface", 0),
            "prune_from_promotion_path_count": action_counts.get("prune_from_promotion_path", 0),
            "hold_for_route_trial_count": action_counts.get("hold_for_route_trial", 0),
            "review_before_tracking_count": action_counts.get("review_before_tracking", 0),
        },
        "top_prune_candidates": top_prune_candidates,
        "analyses": analyses,
        "claim_boundary": (
            "This review classifies codebase pressure. It does not delete files, "
            "prove compression, or replace build/test review."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)

    out = Path(__file__).with_name("rgflow_codebase_reconfiguration_review_receipt.json")
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    print(f"receipt: {out}")
    print(f"receipt_hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
