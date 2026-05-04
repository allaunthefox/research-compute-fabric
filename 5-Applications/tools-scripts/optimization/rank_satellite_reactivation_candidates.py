#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Rank scored satellite reactivation candidates.

Three views:
  --go          top-N GO candidates by score (default N=10)
  --watch       top-N WATCH candidates by lowest component gap
  --gates       gate-failure frequency breakdown across all rows

All three views can be shown in one pass with --all.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_SCORED = Path("5-Applications/out/satellite_reactivation_scored.csv")

COMPONENTS = [
    "component_legal",
    "component_link",
    "component_power",
    "component_stability",
    "component_recovery",
    "component_pcec",
    "component_cost_eff",
]

COMPONENT_SHORT = {
    "component_legal": "legal",
    "component_link": "link",
    "component_power": "power",
    "component_stability": "stability",
    "component_recovery": "recovery",
    "component_pcec": "pcec",
    "component_cost_eff": "cost_eff",
}


def to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(str(v or "").strip())
    except (TypeError, ValueError):
        return default


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        print(f"ERROR: scored CSV not found: {path}", file=sys.stderr)
        sys.exit(1)
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def weakest_component(row: Dict[str, str]) -> Tuple[float, str]:
    """Return (min_score, component_short_name) for a row."""
    scores = {col: to_float(row.get(col, "0")) for col in COMPONENTS}
    worst_col = min(scores, key=lambda c: scores[c])
    return scores[worst_col], COMPONENT_SHORT[worst_col]


# ── view 1: top-N GO ──────────────────────────────────────────────────────────

def view_go(rows: List[Dict[str, str]], top_n: int, one_line: bool, delim: str) -> None:
    go_rows = [r for r in rows if r.get("decision") == "GO"]
    go_rows.sort(key=lambda r: to_float(r.get("reactivation_score")), reverse=True)
    candidates = go_rows[:top_n]

    if not candidates:
        if one_line:
            print(f"go_count{delim}0")
        else:
            print("[GO] No GO candidates found.")
        return

    if one_line:
        for rank, r in enumerate(candidates, 1):
            parts = [
                str(rank),
                r.get("candidate_id", ""),
                r.get("orbit_regime", ""),
                r.get("reactivation_score", ""),
                r.get("component_pcec", ""),
                r.get("component_link", ""),
                r.get("component_power", ""),
            ]
            print(delim.join(parts))
        return

    # Table mode
    hdr = f"{'#':>3}  {'candidate_id':<16}  {'orbit':<6}  {'score':>6}  {'pcec':>6}  {'link':>6}  {'power':>6}  {'stability':>9}  {'recovery':>8}"
    print(f"\n── TOP-{top_n} GO CANDIDATES ──")
    print(hdr)
    print("-" * len(hdr))
    for rank, r in enumerate(candidates, 1):
        print(
            f"{rank:>3}  {r.get('candidate_id',''):<16}  "
            f"{r.get('orbit_regime',''):<6}  "
            f"{to_float(r.get('reactivation_score')):>6.2f}  "
            f"{to_float(r.get('component_pcec')):>6.2f}  "
            f"{to_float(r.get('component_link')):>6.2f}  "
            f"{to_float(r.get('component_power')):>6.2f}  "
            f"{to_float(r.get('component_stability')):>9.2f}  "
            f"{to_float(r.get('component_recovery')):>8.2f}"
        )
    print()


# ── view 2: top-N WATCH by weakest component ─────────────────────────────────

def view_watch(rows: List[Dict[str, str]], top_n: int, one_line: bool, delim: str) -> None:
    watch_rows = [r for r in rows if r.get("decision") == "WATCH"]
    # sort by weakest component score ascending (worst gap first)
    watch_rows.sort(key=lambda r: weakest_component(r)[0])
    candidates = watch_rows[:top_n]

    if not candidates:
        if one_line:
            print(f"watch_count{delim}0")
        else:
            print("[WATCH] No WATCH candidates found.")
        return

    if one_line:
        for rank, r in enumerate(candidates, 1):
            score_val, comp_name = weakest_component(r)
            parts = [
                str(rank),
                r.get("candidate_id", ""),
                r.get("orbit_regime", ""),
                r.get("reactivation_score", ""),
                comp_name,
                f"{score_val:.2f}",
                r.get("component_pcec", ""),
            ]
            print(delim.join(parts))
        return

    # Table mode
    hdr = f"{'#':>3}  {'candidate_id':<16}  {'orbit':<6}  {'score':>6}  {'weakest_component':<18}  {'weak_score':>10}  {'pcec':>6}"
    print(f"\n── TOP-{top_n} WATCH — LOWEST COMPONENT GAP FIRST ──")
    print(hdr)
    print("-" * len(hdr))
    for rank, r in enumerate(candidates, 1):
        weak_score, weak_name = weakest_component(r)
        print(
            f"{rank:>3}  {r.get('candidate_id',''):<16}  "
            f"{r.get('orbit_regime',''):<6}  "
            f"{to_float(r.get('reactivation_score')):>6.2f}  "
            f"{weak_name:<18}  "
            f"{weak_score:>10.2f}  "
            f"{to_float(r.get('component_pcec')):>6.2f}"
        )
    print()


# ── view 3: gate-failure frequency ───────────────────────────────────────────

def view_gates(rows: List[Dict[str, str]], one_line: bool, delim: str) -> None:
    counter: Counter[str] = Counter()
    total = len(rows)
    rows_with_failures = 0

    for r in rows:
        raw = r.get("gate_failures", "").strip()
        if raw:
            failures = [f.strip() for f in raw.split("|") if f.strip()]
            if failures:
                rows_with_failures += 1
                counter.update(failures)

    if not counter:
        if one_line:
            print(f"gate_failures{delim}none{delim}total_candidates{delim}{total}")
        else:
            print("[GATES] No gate failures found across all candidates.")
        return

    ranked = counter.most_common()

    if one_line:
        for gate, count in ranked:
            pct = 100.0 * count / total if total > 0 else 0.0
            print(f"{gate}{delim}{count}{delim}{pct:.1f}pct")
        return

    # Table mode
    hdr = f"{'gate_failure_code':<38}  {'count':>5}  {'% of candidates':>15}"
    print(f"\n── GATE-FAILURE FREQUENCY (total candidates: {total}, with failures: {rows_with_failures}) ──")
    print(hdr)
    print("-" * len(hdr))
    for gate, count in ranked:
        pct = 100.0 * count / total if total > 0 else 0.0
        print(f"{gate:<38}  {count:>5}  {pct:>14.1f}%")
    print()


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=str(DEFAULT_SCORED), metavar="PATH",
                    help="Scored candidate CSV (default: %(default)s)")
    ap.add_argument("--top-n", type=int, default=10, metavar="N",
                    help="Rows per view (default: %(default)s)")
    ap.add_argument("--all", action="store_true",
                    help="Show all three views (go + watch + gates)")
    ap.add_argument("--go", action="store_true",
                    help="Show top-N GO candidates")
    ap.add_argument("--watch", action="store_true",
                    help="Show top-N WATCH candidates by weakest component")
    ap.add_argument("--gates", action="store_true",
                    help="Show gate-failure frequency breakdown")
    ap.add_argument("--one-line", action="store_true",
                    help="Pipe-friendly one-line-per-row output")
    ap.add_argument("--one-line-delim", default=";", metavar="CHAR",
                    help="Delimiter for --one-line mode (default: %(default)r)")
    args = ap.parse_args()

    show_go = args.go or args.all
    show_watch = args.watch or args.all
    show_gates = args.gates or args.all

    if not (show_go or show_watch or show_gates):
        ap.print_help()
        sys.exit(0)

    rows = load_rows(Path(args.input))

    if show_go:
        view_go(rows, args.top_n, args.one_line, args.one_line_delim)
    if show_watch:
        view_watch(rows, args.top_n, args.one_line, args.one_line_delim)
    if show_gates:
        view_gates(rows, args.one_line, args.one_line_delim)


if __name__ == "__main__":
    main()
