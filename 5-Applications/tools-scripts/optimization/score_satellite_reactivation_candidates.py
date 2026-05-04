#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Score satellite reactivation candidates with measurable gates and thresholds.

Input: CSV with fields from data_baselines/satellite_candidate_template.csv
Output:
- scored CSV with gate failures, score, and decision
- summary JSON with counts and top candidates
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_INPUT = Path("data_baselines/satellite_candidate_template.csv")
DEFAULT_OUTPUT = Path("5-Applications/out/satellite_reactivation_scored.csv")
DEFAULT_SUMMARY = Path("5-Applications/out/satellite_reactivation_summary.json")


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float((value or "").strip())
    except (TypeError, ValueError):
        return default


def to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def score_band(x: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return clamp01((x - low) / (high - low))


def inverse_band(x: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return clamp01((high - x) / (high - low))


def gate_failures(row: Dict[str, str]) -> List[str]:
    fails: List[str] = []

    if not to_bool(row.get("command_authority_verified", "")):
        fails.append("no_command_authority")
    if not to_bool(row.get("license_path_clear", "")):
        fails.append("license_path_unclear")
    if to_float(row.get("rx_beacon_snr_db", "0")) < 6.0:
        fails.append("rx_beacon_snr_below_6db")
    if to_float(row.get("uplink_ack_rate_pct", "0")) < 20.0:
        fails.append("uplink_ack_below_20pct")
    if to_float(row.get("power_margin_w", "0")) <= 0.0:
        fails.append("non_positive_power_margin")
    if to_float(row.get("telemetry_frame_success_pct", "0")) < 70.0:
        fails.append("telemetry_success_below_70pct")

    # User-defined usable field requirement mapped to measurable proxy.
    # Requires coherent, tunable EM phase behavior above minimum floor.
    if to_float(row.get("phase_coherence_score", "0")) < 0.60:
        fails.append("phase_coherence_below_0_60")
    if to_float(row.get("tunable_em_band_hz", "0")) < 300000.0:
        fails.append("tunable_em_band_below_300khz")
    if to_float(row.get("coherent_link_uptime_pct", "0")) < 75.0:
        fails.append("coherent_link_uptime_below_75pct")

    return fails


def compute_score(row: Dict[str, str]) -> Tuple[float, Dict[str, float]]:
    legal = 1.0 if (to_bool(row.get("command_authority_verified", "")) and to_bool(row.get("license_path_clear", ""))) else 0.0

    link = 0.45 * score_band(to_float(row.get("rx_beacon_snr_db", "0")), 6.0, 18.0)
    link += 0.35 * score_band(to_float(row.get("uplink_ack_rate_pct", "0")), 20.0, 90.0)
    link += 0.20 * score_band(to_float(row.get("telemetry_frame_success_pct", "0")), 70.0, 99.0)

    power = 0.50 * score_band(to_float(row.get("power_margin_w", "0")), 0.0, 25.0)
    power += 0.30 * score_band(to_float(row.get("battery_health_pct", "0")), 40.0, 95.0)
    power += 0.20 * score_band(to_float(row.get("thermal_margin_c", "0")), 3.0, 25.0)

    stability = 0.45 * inverse_band(to_float(row.get("tumble_rate_deg_s", "99")), 0.0, 3.0)
    stability += 0.35 * inverse_band(to_float(row.get("pointing_error_deg", "99")), 0.0, 5.0)
    stability += 0.20 * (1.0 if to_bool(row.get("detumble_capability", "")) else 0.0)

    recovery = 0.35 * score_band(to_float(row.get("reboot_success_pct", "0")), 50.0, 98.0)
    recovery += 0.35 * score_band(to_float(row.get("safe_mode_entry_success_pct", "0")), 60.0, 99.0)
    recovery += 0.30 * score_band(to_float(row.get("watchdog_recovery_success_pct", "0")), 60.0, 99.0)

    pcec = 0.45 * score_band(to_float(row.get("phase_coherence_score", "0")), 0.60, 0.95)
    pcec += 0.25 * score_band(to_float(row.get("tunable_em_band_hz", "0")), 300000.0, 3000000.0)
    pcec += 0.15 * inverse_band(to_float(row.get("phase_lock_error_deg", "180")), 0.0, 20.0)
    pcec += 0.15 * score_band(to_float(row.get("coherent_link_uptime_pct", "0")), 75.0, 95.0)

    cost_eff = 0.60 * inverse_band(to_float(row.get("acquisition_cost_usd", "0")), 50000.0, 2000000.0)
    cost_eff += 0.40 * inverse_band(to_float(row.get("estimated_refurb_cost_usd", "0")), 100000.0, 5000000.0)

    weighted = (
        0.20 * legal
        + 0.18 * link
        + 0.16 * power
        + 0.14 * stability
        + 0.12 * recovery
        + 0.14 * pcec
        + 0.06 * cost_eff
    )

    score_100 = round(weighted * 100.0, 2)
    components = {
        "legal": round(legal * 100.0, 2),
        "link": round(link * 100.0, 2),
        "power": round(power * 100.0, 2),
        "stability": round(stability * 100.0, 2),
        "recovery": round(recovery * 100.0, 2),
        "pcec": round(pcec * 100.0, 2),
        "cost_eff": round(cost_eff * 100.0, 2),
    }
    return score_100, components


def decide(score: float, fails: List[str]) -> str:
    if fails:
        return "NO_GO"
    if score >= 75.0:
        return "GO"
    if score >= 60.0:
        return "WATCH"
    return "NO_GO"


def load_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def write_rows(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    go = [r for r in rows if r.get("decision") == "GO"]
    watch = [r for r in rows if r.get("decision") == "WATCH"]
    no_go = [r for r in rows if r.get("decision") == "NO_GO"]
    ranked = sorted(rows, key=lambda r: to_float(str(r.get("reactivation_score", "0"))), reverse=True)
    top = ranked[:10]
    return {
        "candidate_count": len(rows),
        "go_count": len(go),
        "watch_count": len(watch),
        "no_go_count": len(no_go),
        "top_candidates": [
            {
                "candidate_id": r.get("candidate_id", ""),
                "score": r.get("reactivation_score", "0"),
                "decision": r.get("decision", "NO_GO"),
                "gate_failures": r.get("gate_failures", ""),
            }
            for r in top
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=str(DEFAULT_INPUT), help="Input candidate CSV")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Scored candidate CSV")
    ap.add_argument("--summary", default=str(DEFAULT_SUMMARY), help="Summary JSON")
    args = ap.parse_args()

    in_path = Path(str(args.input))
    if not in_path.exists():
        raise SystemExit(f"input not found: {in_path}")

    rows = load_rows(in_path)
    if not rows:
        raise SystemExit("input CSV has no rows")

    scored: List[Dict[str, Any]] = []
    for row in rows:
        score, components = compute_score(row)
        fails = gate_failures(row)
        decision = decide(score, fails)
        out: Dict[str, Any] = dict(row)
        out["reactivation_score"] = score
        out["decision"] = decision
        out["gate_failures"] = ";".join(fails)
        out["component_legal"] = components["legal"]
        out["component_link"] = components["link"]
        out["component_power"] = components["power"]
        out["component_stability"] = components["stability"]
        out["component_recovery"] = components["recovery"]
        out["component_pcec"] = components["pcec"]
        out["component_cost_eff"] = components["cost_eff"]
        scored.append(out)

    fieldnames = list(scored[0].keys())
    write_rows(Path(str(args.output)), scored, fieldnames)

    summary = summarize(scored)
    summary_path = Path(str(args.summary))
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "output_csv": str(Path(str(args.output))),
        "summary_json": str(summary_path),
        "go": summary["go_count"],
        "watch": summary["watch_count"],
        "no_go": summary["no_go_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
