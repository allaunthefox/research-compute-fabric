#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Rank HDC experiment runs from CSV ledger by key metrics.

Reads the ledger emitted by simulate/sweep scripts and prints top-N runs
by query_lift or broadcast_delta for quick decisioning.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER_PATH = ROOT / "out" / "hdc_experiment_ledger.csv"


def parse_float(value: str) -> float:
    try:
        return float((value or "").strip())
    except (TypeError, ValueError):
        return 0.0


def load_rows(ledger_path: Path) -> List[Dict[str, str]]:
    if not ledger_path.exists():
        raise SystemExit(f"ledger not found: {ledger_path}")
    with ledger_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for r in reader]
    if not rows:
        raise SystemExit("ledger has no rows")
    return rows


def filter_rows(rows: List[Dict[str, str]], label_contains: str, subnet_contains: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    label_filter = (label_contains or "").strip().lower()
    subnet_filter = (subnet_contains or "").strip().lower()

    for row in rows:
        label = str(row.get("label") or "")
        subnet = str(row.get("subnet") or "")
        if label_filter and label_filter not in label.lower():
            continue
        if subnet_filter and subnet_filter not in subnet.lower():
            continue
        out.append(row)
    return out


def sort_rows(rows: List[Dict[str, str]], metric: str, descending: bool) -> List[Dict[str, str]]:
    key = metric
    return sorted(rows, key=lambda r: parse_float(str(r.get(key) or "0")), reverse=descending)


def render_table(rows: List[Dict[str, str]], metric: str, top_n: int) -> str:
    other_metric = "broadcast_delta" if metric == "query_lift" else "query_lift"
    headers = ["rank", "label", "subnet", metric, other_metric, "generated_utc"]
    picks = rows[: max(1, top_n)]

    body: List[List[str]] = []
    for idx, row in enumerate(picks, start=1):
        body.append([
            str(idx),
            str(row.get("label") or ""),
            str(row.get("subnet") or ""),
            str(row.get(metric) or "0"),
            str(row.get(other_metric) or "0"),
            str(row.get("generated_utc") or ""),
        ])

    widths = [len(h) for h in headers]
    for row in body:
        for i, cell in enumerate(row):
            if len(cell) > widths[i]:
                widths[i] = len(cell)

    def fmt(parts: List[str]) -> str:
        return " | ".join(parts[i].ljust(widths[i]) for i in range(len(parts)))

    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt(headers), sep]
    lines.extend(fmt(r) for r in body)
    return "\n".join(lines)


def render_one_line_rows(rows: List[Dict[str, str]], metric: str, top_n: int, delim: str = "|") -> str:
    d = delim if delim else "|"
    other_metric = "broadcast_delta" if metric == "query_lift" else "query_lift"
    picks = rows[: max(1, top_n)]
    lines: List[str] = []
    for idx, row in enumerate(picks, start=1):
        parts = [
            str(idx),
            str(row.get("label") or ""),
            str(row.get("subnet") or ""),
            str(row.get(metric) or "0"),
            str(row.get(other_metric) or "0"),
            str(row.get("generated_utc") or ""),
        ]
        lines.append(d.join(parts))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH), help="Path to hdc_experiment_ledger.csv")
    ap.add_argument("--metric", choices=["query_lift", "broadcast_delta"], default="query_lift", help="Metric used for ranking")
    ap.add_argument("--top-n", type=int, default=10, help="Number of rows to print")
    ap.add_argument("--ascending", action="store_true", help="Sort ascending (default is descending)")
    ap.add_argument("--label-contains", default="", help="Optional substring filter on label")
    ap.add_argument("--subnet-contains", default="", help="Optional substring filter on subnet")
    ap.add_argument("--one-line", action="store_true", help="Emit one line per ranked row for pipe-friendly chaining")
    ap.add_argument("--one-line-delim", default="|", help="Delimiter for --one-line output (default: |)")
    args = ap.parse_args()

    if int(args.top_n) <= 0:
        raise SystemExit("invalid --top-n: must be > 0")

    rows = load_rows(Path(str(args.ledger_path)))
    rows = filter_rows(rows, str(args.label_contains), str(args.subnet_contains))
    if not rows:
        raise SystemExit("no rows matched the requested filters")

    ranked = sort_rows(rows, metric=str(args.metric), descending=not bool(args.ascending))
    if args.one_line:
        print(render_one_line_rows(ranked, metric=str(args.metric), top_n=int(args.top_n), delim=str(args.one_line_delim)))
        return
    print(render_table(ranked, metric=str(args.metric), top_n=int(args.top_n)))


if __name__ == "__main__":
    main()
