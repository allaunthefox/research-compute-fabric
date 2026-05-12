#!/usr/bin/env python3
"""Review TiddlyWiki tool surfaces for tuning opportunities.

The wiki has many cards that describe tools, compilers, probes, sidecars,
gateways, and harnesses. This probe gives them a receipt-bearing tuning review:
classify tool-like tiddlers, detect whether they point to runners/receipts, and
rank concrete next tuning actions.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
TIDDLERS = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
OUT_DIR = REPO / "shared-data" / "data" / "wiki_tool_tuning_review"
PAYLOAD_JSON = OUT_DIR / "wiki_tool_tuning_review.json"
SUMMARY = OUT_DIR / "wiki_tool_tuning_review.md"
RECEIPT = OUT_DIR / "wiki_tool_tuning_review_receipt.json"
TIDDLER = TIDDLERS / "Wiki Tool Tuning Review.tid"
GENERATED_TIDDLERS = {
    "Wiki Tool Tuning Review.tid",
    "Wiki Tool Maturation Pass.tid",
}

TOOL_KEYWORDS = [
    "tool",
    "probe",
    "compiler",
    "harness",
    "runner",
    "bridge",
    "plugin",
    "router",
    "search",
    "cache",
    "trace",
    "sidecar",
    "codec",
    "compression",
    "decoder",
    "eigen",
    "baseline",
    "tuning",
    "optimization",
    "verifier",
    "receipt",
    "gate",
    "adapter",
    "pipeline",
    "viewer",
    "famm",
    "waveprobe",
    "parquet",
    "logogram",
    "cad",
    "fpga",
]

MATURATION_BEGIN = "<!-- WIKI_TOOL_MATURATION_BEGIN -->"
MATURATION_END = "<!-- WIKI_TOOL_MATURATION_END -->"

CATEGORY_KEYWORDS = {
    "compression_logogram": ["compression", "hutter", "logogram", "codec", "decoder", "parquet", "tokenbook", "dictionary"],
    "compiler_receipt": ["compiler", "gccl", "receipt", "verifier", "gate", "lean", "proof", "typechecker"],
    "search_route_memory": ["search", "route", "famm", "cache", "trace", "hnsw", "graph", "semantic"],
    "geometry_cad": ["cad", "geometry", "mesh", "viewer", "force", "projectable", "stl", "step"],
    "hardware_signal": ["fpga", "hardware", "waveprobe", "hdmi", "uart", "asic", "signal", "sdr", "tang9k"],
    "ene_wiki_infra": ["ene", "tiddlywiki", "plugin", "ingest", "substrate", "fts", "wiki"],
    "external_prior": ["prior", "external", "literature", "model", "transcriptformer", "alphafold", "typst", "quandela"],
}

NEXT_ACTIONS = {
    "compression_logogram": "run corpus matrix: raw/parquet/logogram/hybrid sidecar, then eigenprobe the loss axes",
    "compiler_receipt": "add replay fixtures and negative controls for each promotion gate before widening candidate classes",
    "search_route_memory": "measure cache-hit, trace replay gain, stale penalty, and route-frustration updates on one shared fixture",
    "geometry_cad": "pair mesh/source/render hashes with bounded residual metrics and rollback receipts",
    "hardware_signal": "separate simulation receipts from device receipts; add smoke fixtures for timing, packet, and recovery gates",
    "ene_wiki_infra": "feed reviewed tiddlers through scan/dry-run/ingest/verify and compare ENE index coverage",
    "external_prior": "turn prior cards into adapter fixtures with source hashes, license/provenance, baseline, and leakage controls",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def parse_tiddler(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    analysis_text = re.sub(
        rf"\n?!! Maturation Status\n\n{re.escape(MATURATION_BEGIN)}.*?{re.escape(MATURATION_END)}\n?",
        "\n",
        text,
        flags=re.DOTALL,
    )
    fields: dict[str, str] = {}
    body_start = 0
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            body_start = index + 1
            break
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    title = fields.get("title", path.stem)
    tags = fields.get("tags", "")
    lower = analysis_text.lower()
    keyword_hits = {keyword: lower.count(keyword) for keyword in TOOL_KEYWORDS if lower.count(keyword)}
    category_scores = {
        category: sum(lower.count(keyword) for keyword in keywords)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    categories = [category for category, score in category_scores.items() if score > 0]
    receipt_paths = sorted(set(re.findall(r"(?:shared-data/data|4-Infrastructure|6-Documentation|docs|0-Core-Formalism|5-Applications)[^`\s)]+receipt[^`\s)]*", analysis_text)))
    runner_paths = sorted(set(re.findall(r"(?:4-Infrastructure|5-Applications|scripts|tools|0-Core-Formalism)[^`\s)]*\.(?:py|rs|lean|js|mjs|sh|v|sv)", analysis_text)))
    decision_count = len(re.findall(r"\b(?:HOLD|ACCEPT|REJECT|QUARANTINE|CANDIDATE|ADMIT)\b", analysis_text))
    receipt_count = lower.count("receipt")
    exact_replay_count = lower.count("exact replay") + lower.count("decode(") + lower.count("round-trip")
    baseline_count = lower.count("baseline") + lower.count("negative control")
    tool_score = (
        sum(keyword_hits.values())
        + 3 * len(runner_paths)
        + 2 * len(receipt_paths)
        + receipt_count
        + baseline_count
    )
    maturity = "UNRECEIPTED_TOOL_SURFACE"
    if runner_paths and receipt_paths and baseline_count:
        maturity = "TUNABLE_WITH_BASELINE"
    elif runner_paths and receipt_paths:
        maturity = "RECEIPTED_RUNNER"
    elif receipt_paths:
        maturity = "RECEIPTED_PRIOR"
    elif runner_paths:
        maturity = "RUNNER_WITHOUT_VISIBLE_RECEIPT"
    if tool_score < 3:
        maturity = "LOW_TOOL_SIGNAL"
    return {
        "path": rel(path),
        "title": title,
        "tags": tags,
        "body_lines": max(0, len(lines) - body_start),
        "sha256": sha256_bytes(text.encode("utf-8")),
        "tool_score": tool_score,
        "keyword_hits": keyword_hits,
        "categories": categories,
        "category_scores": {k: v for k, v in category_scores.items() if v},
        "receipt_count": receipt_count,
        "decision_count": decision_count,
        "exact_replay_signal": exact_replay_count,
        "baseline_signal": baseline_count,
        "receipt_paths": receipt_paths,
        "runner_paths": runner_paths,
        "maturity": maturity,
    }


def tuning_priority(entry: dict[str, Any]) -> float:
    category_bonus = 1.5 * len(entry["categories"])
    receipt_bonus = 2.0 if entry["receipt_paths"] else 0.0
    runner_bonus = 2.0 if entry["runner_paths"] else 0.0
    weak_baseline_penalty = 4.0 if entry["tool_score"] > 20 and entry["baseline_signal"] == 0 else 0.0
    return round(entry["tool_score"] + category_bonus + receipt_bonus + runner_bonus + weak_baseline_penalty, 3)


def recommended_next(entry: dict[str, Any]) -> list[str]:
    actions = [NEXT_ACTIONS[category] for category in entry["categories"] if category in NEXT_ACTIONS]
    if entry["maturity"] == "RUNNER_WITHOUT_VISIBLE_RECEIPT":
        actions.insert(0, "emit a receipt JSON/MD/tiddler for the existing runner")
    if entry["maturity"] == "RECEIPTED_PRIOR":
        actions.insert(0, "bind the prior to a minimal executable fixture")
    if entry["baseline_signal"] == 0 and entry["tool_score"] > 15:
        actions.append("add a baseline/negative-control lane before tuning coefficients")
    if entry["exact_replay_signal"] == 0 and any(cat in entry["categories"] for cat in ["compression_logogram", "compiler_receipt"]):
        actions.append("add exact replay or round-trip evidence to keep the byte-law gate honest")
    return list(dict.fromkeys(actions))[:4]


def build_payload() -> dict[str, Any]:
    entries = [
        parse_tiddler(path)
        for path in sorted(TIDDLERS.glob("*.tid"))
        if not path.name.startswith("$__") and path.name not in GENERATED_TIDDLERS
    ]
    tool_entries = [entry for entry in entries if entry["tool_score"] >= 6]
    for entry in tool_entries:
        entry["tuning_priority"] = tuning_priority(entry)
        entry["recommended_next"] = recommended_next(entry)
    ranked = sorted(tool_entries, key=lambda entry: entry["tuning_priority"], reverse=True)
    category_rollup = {}
    for category in CATEGORY_KEYWORDS:
        members = [entry for entry in tool_entries if category in entry["categories"]]
        category_rollup[category] = {
            "count": len(members),
            "top": [
                {"title": item["title"], "priority": item["tuning_priority"], "maturity": item["maturity"]}
                for item in sorted(members, key=lambda entry: entry["tuning_priority"], reverse=True)[:8]
            ],
            "next_action": NEXT_ACTIONS[category],
        }
    maturity_rollup = {
        maturity: sum(1 for entry in tool_entries if entry["maturity"] == maturity)
        for maturity in sorted({entry["maturity"] for entry in tool_entries})
    }
    quick_wins = [
        entry
        for entry in ranked
        if entry["runner_paths"] and entry["receipt_paths"] and entry["maturity"] in {"RECEIPTED_RUNNER", "TUNABLE_WITH_BASELINE"}
    ][:12]
    baseline_debt = [
        entry
        for entry in ranked
        if entry["tool_score"] >= 20 and entry["baseline_signal"] == 0
    ][:12]
    payload = {
        "schema": "wiki_tool_tuning_review_v1",
        "claim_boundary": (
            "Wiki review only. Tuning priority is a heuristic over local tiddler text, "
            "runner references, receipt references, exact-replay signals, and baseline "
            "signals. It ranks where to inspect next; it does not validate any theory or tool."
        ),
        "inputs": {
            "tiddler_dir": rel(TIDDLERS),
            "tiddler_count": len(entries),
            "tool_like_count": len(tool_entries),
        },
        "category_rollup": category_rollup,
        "maturity_rollup": maturity_rollup,
        "top_tuning_targets": ranked[:24],
        "quick_wins": quick_wins,
        "baseline_debt": baseline_debt,
        "finding": (
            "The wiki has multiple tunable tool surfaces. The strongest immediate targets "
            "are compression/logogram byte-law probes, Rainbow/GCCL receipt gates, "
            "decision-diagram route search, ENE/wiki ingestion, CAD residual loops, and "
            "shared fixture matrices, exact replay, negative controls, and eigen/baseline "
            "diagnostics per tool family."
        ),
        "decision": "ADMIT_WIKI_TOOL_TUNING_REVIEW_AS_HOLD_ROADMAP",
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "wiki_tool_tuning_review_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "aggregates": {
            **payload["inputs"],
            "category_count": len(payload["category_rollup"]),
            "maturity_rollup": payload["maturity_rollup"],
        },
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def entry_line(entry: dict[str, Any]) -> str:
    cats = ", ".join(entry["categories"][:3]) or "uncategorized"
    return f"| [[{entry['title']}]] | {entry['tuning_priority']} | {entry['maturity']} | {cats} |"


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Wiki Tool Tuning Review",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Finding",
        "",
        payload["finding"],
        "",
        "## Rollup",
        "",
        f"- Tiddlers scanned: `{payload['inputs']['tiddler_count']}`",
        f"- Tool-like tiddlers: `{payload['inputs']['tool_like_count']}`",
        f"- Maturity rollup: `{payload['maturity_rollup']}`",
        "",
        "## Top Tuning Targets",
        "",
        "| Tiddler | Priority | Maturity | Categories |",
        "|---|---:|---|---|",
    ]
    for entry in payload["top_tuning_targets"][:18]:
        lines.append(entry_line(entry))
    lines.extend(["", "## Quick Wins", "", "| Tiddler | Priority | Maturity | Categories |", "|---|---:|---|---|"])
    for entry in payload["quick_wins"][:10]:
        lines.append(entry_line(entry))
    lines.extend(["", "## Baseline Debt", "", "| Tiddler | Priority | Maturity | Categories |", "|---|---:|---|---|"])
    for entry in payload["baseline_debt"][:10]:
        lines.append(entry_line(entry))
    lines.extend(["", "## Category Next Actions", ""])
    for category, rollup in payload["category_rollup"].items():
        lines.append(f"- `{category}` ({rollup['count']}): {rollup['next_action']}")
    lines.extend(["", "## Receipt", "", f"`{rel(RECEIPT)}`"])
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "title: Wiki Tool Tuning Review",
        "tags: ResearchStack TiddlyWiki ToolTuning Review HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! Wiki Tool Tuning Review",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "!! Finding",
        "",
        payload["finding"],
        "",
        "!! Counts",
        "",
        f"* Tiddlers scanned: `{payload['inputs']['tiddler_count']}`",
        f"* Tool-like tiddlers: `{payload['inputs']['tool_like_count']}`",
        f"* Maturity rollup: `{payload['maturity_rollup']}`",
        "",
        "!! Top Tuning Targets",
        "",
        "| Tiddler | Priority | Maturity | Categories |h",
    ]
    for entry in payload["top_tuning_targets"][:18]:
        lines.append(entry_line(entry))
    lines.extend(["", "!! Quick Wins", "", "| Tiddler | Priority | Maturity | Categories |h"])
    for entry in payload["quick_wins"][:10]:
        lines.append(entry_line(entry))
    lines.extend(["", "!! Baseline Debt", "", "| Tiddler | Priority | Maturity | Categories |h"])
    for entry in payload["baseline_debt"][:10]:
        lines.append(entry_line(entry))
    lines.extend(["", "!! Category Next Actions", ""])
    for category, rollup in payload["category_rollup"].items():
        lines.append(f"* `{category}` ({rollup['count']}): {rollup['next_action']}")
    lines.extend(
        [
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            "!! Links",
            "",
            "* [[Parquet Logogram Eigenprobe]]",
            "* [[Combined Approach Equation Surface]]",
            "* [[Rainbow Raccoon Compiler]]",
            "* [[Decision Diagram Compression Tuning Prior]]",
            "* [[TiddlyWiki ENE Bridge Plugin]]",
            "",
            f"Receipt: `{rel(RECEIPT)}`",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
