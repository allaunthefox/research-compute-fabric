#!/usr/bin/env python3
"""Build an admissible-prior index from the local math model map.

This does not claim the listed equations are formal proofs. It classifies local
model-map entries into evidence tiers so compression/logogram/FPGA searches can
try known solved or implemented shapes first, then fall back to wider search.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_MODEL_MAP = Path("3-Mathematical-Models/MATH_MODEL_MAP.tsv")


def evidence_tier(row: dict[str, str]) -> str:
    implemented = row.get("Implemented", "")
    status = row.get("Status", "")
    location = row.get("Location", "")
    purpose = row.get("Purpose", "")
    haystack = " ".join([implemented, status, location, purpose]).lower()

    if "lean" in haystack and "✅" in status:
        return "formal_or_lean_backed"
    if any(token in haystack for token in ["verilog", "fpga", "hardware"]) and "✅" in status:
        return "hardware_or_hdl_backed"
    if any(token in implemented.lower() for token in ["python", "rust", "c++", "6502", "subl"]) and "✅" in status:
        return "implemented_local"
    if implemented.lower() == "spec" and "✅" in status:
        return "spec_admissible"
    if implemented.lower() == "documented" and "✅" in status:
        return "documented_reference"
    if "✅" in status:
        return "indexed_admissible"
    return "unverified_or_pending"


def tier_rank(tier: str) -> int:
    ranks = {
        "formal_or_lean_backed": 0,
        "hardware_or_hdl_backed": 1,
        "implemented_local": 2,
        "spec_admissible": 3,
        "documented_reference": 4,
        "indexed_admissible": 5,
        "unverified_or_pending": 6,
    }
    return ranks.get(tier, 9)


def row_score(row: dict[str, str], tier: str) -> int:
    score = 100 - tier_rank(tier) * 10
    domain = row.get("Domain_Type", "")
    bind = row.get("Bind_Class", "")
    family = row.get("Family", "")
    purpose = row.get("Purpose", "")
    text = " ".join([domain, bind, family, purpose]).lower()
    for token in ("compression", "encoding", "signal", "control", "routing", "hardware", "fpga"):
        if token in text:
            score += 3
    if row.get("Location", "").startswith(("http://", "https://")):
        score -= 5
    return score


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for row in reader:
            clean = {}
            for key, value in row.items():
                if key is None:
                    if value:
                        clean["Extra"] = " ".join(str(part) for part in value)
                    continue
                clean[key] = str(value or "")
            rows.append(clean)
        return rows


def matches_query(row: dict[str, str], query: str) -> bool:
    if not query:
        return True
    q = query.lower()
    return q in " ".join(row.values()).lower()


def build_index(rows: list[dict[str, str]], query: str, include_documented: bool) -> dict[str, Any]:
    entries = []
    for row in rows:
        if not matches_query(row, query):
            continue
        tier = evidence_tier(row)
        if tier == "unverified_or_pending":
            continue
        if not include_documented and tier == "documented_reference":
            continue
        entry = {
            "id": row.get("#", ""),
            "model_name": row.get("Model_Name", ""),
            "family": row.get("Family", ""),
            "equation": row.get("Equation", ""),
            "variables": row.get("Variables", ""),
            "purpose": row.get("Purpose", ""),
            "location": row.get("Location", ""),
            "implemented": row.get("Implemented", ""),
            "status": row.get("Status", ""),
            "domain_type": row.get("Domain_Type", ""),
            "bind_class": row.get("Bind_Class", ""),
            "evidence_tier": tier,
            "pruning_score": row_score(row, tier),
        }
        entries.append(entry)

    entries.sort(key=lambda item: (-item["pruning_score"], tier_rank(item["evidence_tier"]), item["model_name"]))

    by_tier = Counter(entry["evidence_tier"] for entry in entries)
    by_domain = Counter(entry["domain_type"] for entry in entries if entry["domain_type"])
    by_bind = Counter(entry["bind_class"] for entry in entries if entry["bind_class"])
    return {
        "schema": "solved_math_pruning_surface_v1",
        "claim_boundary": "Rows are admissible search priors, not theorem claims unless their evidence tier says Lean/formal.",
        "source": str(DEFAULT_MODEL_MAP),
        "query": query,
        "include_documented": include_documented,
        "entry_count": len(entries),
        "summary": {
            "by_evidence_tier": dict(by_tier),
            "top_domain_types": by_domain.most_common(12),
            "top_bind_classes": by_bind.most_common(12),
        },
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-map", type=Path, default=DEFAULT_MODEL_MAP)
    parser.add_argument("--query", default="")
    parser.add_argument("--include-documented", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows = load_rows(args.model_map)
    index = build_index(rows, args.query, args.include_documented)
    index["source"] = str(args.model_map)
    if args.limit >= 0:
        index["entries"] = index["entries"][: args.limit]
    text = json.dumps(index, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
