#!/usr/bin/env python3
"""Regression gate for the wiki/topology receipt review fixes.

This is intentionally narrow. It protects the issues found in the fine-tooth
review: overclaim wording, generated-wiki self-inclusion, vacuous replay gates,
input-hash trust, x86 live-source drift, and maturation non-idempotence.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]

SCOPED_TEXT_FILES = [
    REPO / "shared-data" / "network_topology_database.json",
    REPO / "3-Mathematical-Models" / "fiber_optic_vibrational_tensor" / "Fundamental_Network_Topology_Equation.md",
    REPO / "6-Documentation" / "wiki" / "Network-Topology-Theory.md",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Fundamental Network Topology Equation.tid",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Network Topology Theory.tid",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "X86 Emulator Eigen Baseline.tid",
]

FORBIDDEN_PATTERNS = [
    r"ultimate_validation",
    r"ultimate validation",
    r"\bvalidates\b",
    r"validated_by_",
    r"highest validation",
    r"R_harvest",
    r"8 converging",
    r"C\(N\)\s*=\s*\(E_actual/E_theoretical\)",
    r"0\.77 is the overall methodology convergence score",
    r'"validated"\s*:\s*true',
    r'"validation_source"',
    r"high_validation",
    r"live_unpinned_raw_urls",
]

RECEIPTS = {
    "wiki_review": REPO / "shared-data" / "data" / "wiki_tool_tuning_review" / "wiki_tool_tuning_review_receipt.json",
    "wiki_maturation": REPO / "shared-data" / "data" / "wiki_tool_maturation_pass" / "wiki_tool_maturation_pass_receipt.json",
    "parquet_efficiency": REPO / "shared-data" / "data" / "parquet_logogram_efficiency" / "parquet_logogram_efficiency_receipt.json",
    "parquet_eigen": REPO / "shared-data" / "data" / "parquet_logogram_eigenprobe" / "parquet_logogram_eigenprobe_receipt.json",
    "x86": REPO / "shared-data" / "data" / "x86_emulator_eigen_baseline" / "x86_emulator_eigen_baseline_receipt.json",
    "modly_smoke": REPO / "shared-data" / "data" / "modly_text_to_cad_bridge" / "smoke" / "modly_text_to_cad_bridge_smoke_receipt.json",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def check_forbidden_patterns() -> list[str]:
    hits: list[str] = []
    for path in SCOPED_TEXT_FILES:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO)
        for pattern in FORBIDDEN_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                hits.append(f"{rel}: forbidden `{pattern}` matched `{match.group(0)}`")
    return hits


def load_review_module() -> Any:
    module_path = REPO / "4-Infrastructure" / "shim" / "wiki_tool_tuning_review_probe.py"
    spec = importlib.util.spec_from_file_location("wiki_tool_tuning_review_probe", module_path)
    if spec is None or spec.loader is None:
        fail(f"unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_wiki_generated_exclusion() -> None:
    module = load_review_module()
    payload = module.build_payload()
    path_fields = []
    for key in ("top_tuning_targets", "quick_wins", "baseline_debt"):
        path_fields.extend(entry.get("path") for entry in payload.get(key, []))
    for category in payload.get("category_rollup", {}).values():
        path_fields.extend(entry.get("path") for entry in category.get("top", []))
    paths = {path for path in path_fields if path}
    generated = {
        "6-Documentation/tiddlywiki-local/wiki/tiddlers/Wiki Tool Tuning Review.tid",
        "6-Documentation/tiddlywiki-local/wiki/tiddlers/Wiki Tool Maturation Pass.tid",
    }
    leaked = sorted(paths & generated)
    if leaked:
        fail(f"generated wiki tiddlers leaked into review payload: {leaked}")
    if payload["inputs"]["tool_like_count"] <= 0:
        fail("wiki review tool_like_count is empty")


def check_receipts() -> dict[str, dict[str, Any]]:
    receipts = {}
    missing = [name for name, path in RECEIPTS.items() if not path.exists()]
    if missing:
        fail(f"missing receipts: {missing}")
    for name, path in RECEIPTS.items():
        receipts[name] = load_json(path)
    return receipts


def check_parquet_eigen_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("input_payload_hash_recomputes") is not True:
        fail("parquet eigenprobe input payload hash does not recompute")
    if receipt.get("input_receipt_hash_recomputes") is not True:
        fail("parquet eigenprobe input receipt hash does not recompute")
    if receipt.get("decision") != "ADMIT_PARQUET_LOGOGRAM_EIGENPROBE_AS_HOLD_DIAGNOSTIC":
        fail(f"unexpected parquet eigenprobe decision: {receipt.get('decision')}")


def check_x86_receipt(receipt: dict[str, Any]) -> None:
    aggregates = receipt.get("aggregates", {})
    if aggregates.get("fetched_source_count") != aggregates.get("source_count"):
        fail(f"x86 source fetch/cache incomplete: {aggregates}")
    if aggregates.get("source_mode") != "local_cache_preferred_live_fetch_on_cache_miss":
        fail(f"x86 source mode is not cache-preferred: {aggregates.get('source_mode')}")
    cache_dir = REPO / aggregates.get("source_cache_dir", "")
    cached_count = len(list(cache_dir.glob("*"))) if cache_dir.exists() else 0
    if cached_count != aggregates.get("source_count"):
        fail(f"x86 source cache count {cached_count} != source_count {aggregates.get('source_count')}")


def check_maturation_idempotence() -> None:
    script = REPO / "4-Infrastructure" / "shim" / "wiki_tool_maturation_apply.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    receipt = json.loads(result.stdout)
    if receipt["aggregates"]["tiddlers_changed"] != 0:
        fail(f"maturation pass is not idempotent: {receipt['aggregates']}")
    if receipt["aggregates"]["tool_entries_seen"] != receipt["aggregates"]["matured_block_count"]:
        fail(f"maturation count mismatch: {receipt['aggregates']}")


def main() -> int:
    forbidden_hits = check_forbidden_patterns()
    if forbidden_hits:
        fail("forbidden overclaim patterns found:\n" + "\n".join(forbidden_hits))
    check_wiki_generated_exclusion()
    receipts = check_receipts()
    check_parquet_eigen_receipt(receipts["parquet_eigen"])
    check_x86_receipt(receipts["x86"])
    check_maturation_idempotence()
    print(
        json.dumps(
            {
                "decision": "PASS_REVIEW_FIX_REGRESSION_GATE",
                "checked_receipts": sorted(RECEIPTS),
                "forbidden_patterns": len(FORBIDDEN_PATTERNS),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
