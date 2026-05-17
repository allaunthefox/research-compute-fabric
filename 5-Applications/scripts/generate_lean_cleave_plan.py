#!/usr/bin/env python3
"""Generate a cleaving plan from the Lean module domain graph."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "shared-data" / "data" / "lean_module_graph"
OUT_CSV = GRAPH / "cleave_plan.csv"
OUT_JSONL = GRAPH / "cleave_plan.jsonl"
OUT_MD = ROOT / "6-Documentation" / "docs" / "reports" / "LEAN_MODULE_CLEAVE_PLAN.md"

BUILD_ROOTS = ["Semantics", "PIST", "PistBridge", "PistSimulation"]


def load_modules() -> list[dict]:
    return [json.loads(line) for line in (GRAPH / "modules.jsonl").read_text().splitlines()]


def load_local_edges() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with (GRAPH / "import_edges.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["target_local"] == "true":
                rows.append((row["source"], row["target"]))
    return rows


def reachable(modules: list[dict], edges: list[tuple[str, str]]) -> set[str]:
    known = {m["module"] for m in modules}
    adj: dict[str, list[str]] = {m["module"]: [] for m in modules}
    for src, dst in edges:
        adj.setdefault(src, []).append(dst)
    seen: set[str] = set()
    stack = [root for root in BUILD_ROOTS if root in known]
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        stack.extend(adj.get(mod, []))
    return seen


def cleave_class(mod: dict, is_reachable: bool) -> tuple[str, str]:
    path = mod["path"]
    domain = mod["domain"]
    review = mod["review_status"]
    if "/Ancillary/" in path or domain == "AncillaryHolding":
        return ("ANCILLARY_HOLDING", "Already cleaved out of required core; keep with receipt until promoted or archived.")
    if "/legacy/" in path or "/Quarantine/" in path or domain == "LegacyQuarantine":
        return ("LEGACY_OR_QUARANTINE", "Do not delete blindly; archive/receipt or exclude from main surface.")
    if "/external/" in path or "/LeanGPT/" in path or domain == "ExternalReference":
        return ("EXTERNAL_REFERENCE", "Keep as reference-only material; do not treat as owned core.")
    if is_reachable:
        if review == "HOLD":
            return ("REQUIRED_HOLD_REVIEW", "Reachable from aggregate build but taxonomy is ambiguous; review before moving.")
        return ("REQUIRED_AGGREGATE", "Reachable from aggregate Lean build roots.")
    if "ExtensionScaffold" in path or domain == "ExtensionScaffold":
        return ("OPTIONAL_EXTENSION_SCAFFOLD", "Scaffold/extension surface; keep modular unless promoted.")
    if domain == "RuntimeEntrypoints":
        return ("RUNTIME_ENTRYPOINT", "Executable or service entrypoint; keep outside core proof taxonomy.")
    if review == "HOLD":
        return ("UNREACHED_HOLD_REVIEW", "Not reached by aggregate build and taxonomy is ambiguous; inspect before import/move/archive.")
    if domain == "ReviewUnclassified":
        return ("UNREACHED_UNCLASSIFIED", "No strong classifier signal; needs owner/domain assignment.")
    return ("UNREACHED_DOMAIN_CANDIDATE", "Local module not reached by aggregate build; candidate for optional import, extension bundle, or archive.")


def main() -> None:
    modules = load_modules()
    edges = load_local_edges()
    seen = reachable(modules, edges)
    rows: list[dict] = []
    for mod in modules:
        cls, action = cleave_class(mod, mod["module"] in seen)
        rows.append({
            "module": mod["module"],
            "path": mod["path"],
            "domain": mod["domain"],
            "review_status": mod["review_status"],
            "reachable_from_aggregate": "true" if mod["module"] in seen else "false",
            "cleave_class": cls,
            "recommended_action": action,
            "sorry_count": mod["sorry_count"],
            "line_count": mod["line_count"],
            "sha256": mod["sha256"],
        })
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    class_counts = Counter(row["cleave_class"] for row in rows)
    domain_by_class: dict[str, Counter[str]] = {}
    for row in rows:
        domain_by_class.setdefault(row["cleave_class"], Counter())[row["domain"]] += 1
    lines = [
        "# Lean Module Cleave Plan",
        "",
        "This report classifies the local Lean module graph into required, optional, legacy, external, and review surfaces.",
        "",
        "## Roots",
        "",
        "Reachability roots:",
        "",
        *[f"- `{root}`" for root in BUILD_ROOTS],
        "",
        "## Summary",
        "",
        f"- Local Lean modules: {len(rows)}",
        f"- Reachable from aggregate roots: {sum(1 for row in rows if row['reachable_from_aggregate'] == 'true')}",
        f"- Not reachable from aggregate roots: {sum(1 for row in rows if row['reachable_from_aggregate'] == 'false')}",
        "",
        "## Cleave Classes",
        "",
        "| Class | Modules | Default action |",
        "|---|---:|---|",
    ]
    action_by_class = {row["cleave_class"]: row["recommended_action"] for row in rows}
    for cls, count in class_counts.most_common():
        lines.append(f"| {cls} | {count} | {action_by_class[cls]} |")
    lines.extend(["", "## Domain Mix By Cleave Class", ""])
    for cls, counter in class_counts.most_common():
        lines.extend([f"### {cls}", "", "| Domain | Modules |", "|---|---:|"])
        for domain, count in domain_by_class[cls].most_common(12):
            lines.append(f"| {domain} | {count} |")
        lines.append("")
    lines.extend([
        "## First Review Queue",
        "",
        "Start with reachable HOLD modules, then unreached HOLD modules. Those are the places where moving files before review is most likely to break or mislabel the graph.",
        "",
        "| Module | Class | Domain | Path |",
        "|---|---|---|---|",
    ])
    priority = [row for row in rows if row["cleave_class"] in ("REQUIRED_HOLD_REVIEW", "UNREACHED_HOLD_REVIEW", "UNREACHED_UNCLASSIFIED")]
    priority.sort(key=lambda row: (row["cleave_class"], row["domain"], row["module"]))
    for row in priority[:80]:
        lines.append(f"| `{row['module']}` | {row['cleave_class']} | {row['domain']} | `{row['path']}` |")
    lines.extend([
        "",
        "## Claim Boundary",
        "",
        "This is a cleaving plan, not an automatic folder move. Required means reachable from the current aggregate Lean roots. Unreached does not mean useless; it means optional, scaffold, external, legacy, or not currently wired into the aggregate surface.",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "modules": len(rows),
        "reachable": sum(1 for row in rows if row["reachable_from_aggregate"] == "true"),
        "unreachable": sum(1 for row in rows if row["reachable_from_aggregate"] == "false"),
        "classes": dict(class_counts),
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "jsonl": str(OUT_JSONL.relative_to(ROOT)),
        "report": str(OUT_MD.relative_to(ROOT)),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
