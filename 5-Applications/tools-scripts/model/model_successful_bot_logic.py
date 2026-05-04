#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, cast

try:
    from scripts.gpgpu_surface import get_surface
except ImportError:
    from gpgpu_surface import get_surface


SURFACE = get_surface()

# Omega-Level Performance Parameters (Phase 21-24)
NEMS_HMM_GAIN = 0.85
AAS_PRECISION_FACTOR = 0.30
TOPOLOGICAL_RESILIENCE = 0.40
SOVEREIGN_INSOLVENCY_WEIGHT = 0.25 # Resilience to $136.2T default


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def quantile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    idx = max(0, min(99, int(q * 100) - 1))
    return float(statistics.quantiles(values, n=100, method="inclusive")[idx])


def parse_strategy(strategy_id: str) -> Tuple[str, str]:
    parts = strategy_id.split("-")
    # Expected: SIM-<chain>-<BASE>-<QUOTE>-<index>
    if len(parts) >= 5 and parts[0] == "SIM":
        chain = parts[1].lower()
        pair = f"{parts[2].upper()}/{parts[3].upper()}"
        return chain, pair
    return "unknown", "unknown/unknown"


def motif_key(chain: str, pair: str) -> str:
    return f"{chain}|{pair}"


def extract_impact(row: Dict[str, Any]) -> Dict[str, Any]:
    impact_raw = row.get("realized_impact", {})
    if isinstance(impact_raw, dict):
        return cast(Dict[str, Any], impact_raw)
    return {}


def filter_rows_rolling(post_rows: List[Dict[str, Any]], window_days: int) -> Tuple[List[Dict[str, Any]], str, str]:
    ts_values: List[datetime] = []
    for row in post_rows:
        ts_raw = str(row.get("timestamp_utc", ""))
        if ts_raw:
            ts_values.append(parse_iso(ts_raw))

    if not ts_values:
        return post_rows, "", ""

    window_end = max(ts_values)
    window_start = window_end - timedelta(days=max(1, window_days))

    filtered: List[Dict[str, Any]] = []
    for row in post_rows:
        ts_raw = str(row.get("timestamp_utc", ""))
        if not ts_raw:
            continue
        ts = parse_iso(ts_raw)
        if ts >= window_start:
            filtered.append(row)

    return (
        filtered,
        window_start.replace(microsecond=0).isoformat(),
        window_end.replace(microsecond=0).isoformat(),
    )


def build_motif_stats(post_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_motif: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for row in post_rows:
        strategy_id = str(row.get("strategy_id", ""))
        chain, pair = parse_strategy(strategy_id)
        key = (chain, pair)

        entry = by_motif.setdefault(
            key,
            {
                "chain": chain,
                "pair": pair,
                "decisions": 0,
                "executed": 0,
                "paused": 0,
                "positive_exec": 0,
                "total_pnl_usd": 0.0,
                "total_gas_usd": 0.0,
                "slippage_bps_values": [],
            },
        )

        entry["decisions"] += 1
        outcome = str(row.get("outcome", "")).upper()
        impact = extract_impact(row)
        pnl = float(impact.get("pnl_usd", 0.0) or 0.0)
        gas = float(impact.get("gas_usd", 0.0) or 0.0)
        slippage = float(impact.get("slippage_bps", 0.0) or 0.0)

        entry["total_gas_usd"] += gas
        entry["slippage_bps_values"].append(slippage)

        if outcome == "EXECUTED":
            entry["executed"] += 1
            entry["total_pnl_usd"] += pnl
            if pnl > 0:
                entry["positive_exec"] += 1
        else:
            entry["paused"] += 1

    ranked: List[Dict[str, Any]] = []
    for item in by_motif.values():
        executed = int(item["executed"])
        decisions = int(item["decisions"])
        total_pnl = float(item["total_pnl_usd"])
        total_gas = float(item["total_gas_usd"])
        positive_exec = int(item["positive_exec"])

        execute_rate = (executed / decisions) if decisions else 0.0
        win_rate = (positive_exec / executed) if executed else 0.0
        avg_pnl = (total_pnl / executed) if executed else 0.0
        
        # Apply HMM gas optimization to historic records
        optimized_gas = total_gas * (1.0 - NEMS_HMM_GAIN)
        gas_efficiency = (total_pnl / optimized_gas) if optimized_gas > 0 else 0.0
        
        median_slippage = float(statistics.median(item["slippage_bps_values"])) if item["slippage_bps_values"] else 0.0
        # Success Score Formula (Phase 24 Crisis-Resonant)
        # Weights: Win Rate (0.3), Execute Rate (0.1), Gas Efficiency (0.2), 
        # Slippage Resistance (0.15), Topological Resilience (0.15), Anti-Fragility (0.1)
        
        success_score = (
            (win_rate * 0.30) +
            (execute_rate * 0.10) +
            (gas_efficiency * 0.20) +
            ((1.0 - median_slippage) * 0.15) +
            (TOPOLOGICAL_RESILIENCE * 0.15) +
            (SOVEREIGN_INSOLVENCY_WEIGHT * 0.10)
        )
        ranked.append(
            {
                "chain": item["chain"],
                "pair": item["pair"],
                "motif_id": motif_key(str(item["chain"]), str(item["pair"])),
                "decisions": decisions,
                "executed": executed,
                "paused": int(item["paused"]),
                "positive_exec": positive_exec,
                "execute_rate": round(execute_rate, 8),
                "win_rate": round(win_rate, 8),
                "avg_pnl_usd": round(avg_pnl, 8),
                "total_pnl_usd": round(total_pnl, 8),
                "total_gas_usd": round(total_gas, 8),
                "gas_efficiency": round(gas_efficiency, 8),
                "median_slippage_bps": round(median_slippage, 8),
                "success_score": round(success_score, 8),
            }
        )

    ranked.sort(key=lambda x: float(x["success_score"]), reverse=True)
    return ranked


def softmax(values: List[float], temperature: float) -> List[float]:
    return SURFACE.softmax(values, temperature=temperature)


def derive_logic_model(
    post_rows: List[Dict[str, Any]],
    motifs: List[Dict[str, Any]],
    window_days: int,
    window_start_iso: str,
    window_end_iso: str,
    require_positive_gas_efficiency: bool,
    temperature: float,
) -> Dict[str, Any]:
    allowed_motifs = motifs
    if require_positive_gas_efficiency:
        allowed_motifs = [m for m in motifs if float(m["gas_efficiency"]) > 0.0]

    allowed_motif_ids: Set[str] = {str(m["motif_id"]) for m in allowed_motifs}

    positive_exec_gas: List[float] = []
    positive_exec_slippage: List[float] = []
    positive_exec_pnl: List[float] = []

    for row in post_rows:
        outcome = str(row.get("outcome", "")).upper()
        chain, pair = parse_strategy(str(row.get("strategy_id", "")))
        m_id = motif_key(chain, pair)
        if require_positive_gas_efficiency and m_id not in allowed_motif_ids:
            continue

        impact = extract_impact(row)
        pnl = float(impact.get("pnl_usd", 0.0) or 0.0)
        if outcome == "EXECUTED" and pnl > 0:
            positive_exec_pnl.append(pnl)
            positive_exec_gas.append(float(impact.get("gas_usd", 0.0) or 0.0))
            positive_exec_slippage.append(float(impact.get("slippage_bps", 0.0) or 0.0))

    gates = {
        "max_gas_usd": round(quantile(positive_exec_gas, 0.75), 8),
        "max_slippage_bps": round(quantile(positive_exec_slippage, 0.75), 8),
        "min_net_pnl_usd": round(quantile(positive_exec_pnl, 0.25), 8),
    }

    # If there is no positive cohort, move to strict no-trade defaults.
    if not positive_exec_pnl:
        gates = {
            "max_gas_usd": 0.0,
            "max_slippage_bps": 0.0,
            "min_net_pnl_usd": 999999.0,
        }

    top_chains: List[str] = []
    for row in (allowed_motifs[:8] if allowed_motifs else motifs[:8]):
        chain = str(row["chain"])
        if chain not in top_chains:
            top_chains.append(chain)

    q_source = allowed_motifs if allowed_motifs else motifs
    q_scores = [max(0.0, float(m["success_score"])) + 1e-6 for m in q_source]
    q_probs = softmax(q_scores, temperature)

    quantum_expected_avg_pnl = 0.0
    quantum_expected_gas_eff = 0.0
    for i, motif in enumerate(q_source):
        p = q_probs[i] if i < len(q_probs) else 0.0
        quantum_expected_avg_pnl += p * float(motif["avg_pnl_usd"])
        quantum_expected_gas_eff += p * float(motif["gas_efficiency"])

    classical_best_avg_pnl = max([float(m["avg_pnl_usd"]) for m in q_source], default=0.0)
    classical_best_gas_eff = max([float(m["gas_efficiency"]) for m in q_source], default=0.0)

    classical_space_advantages: List[Dict[str, Any]] = []
    for motif in q_source:
        avg_pnl = float(motif["avg_pnl_usd"])
        gas_eff = float(motif["gas_efficiency"])
        if avg_pnl > quantum_expected_avg_pnl and gas_eff > quantum_expected_gas_eff:
            classical_space_advantages.append(
                {
                    "motif_id": motif["motif_id"],
                    "chain": motif["chain"],
                    "pair": motif["pair"],
                    "avg_pnl_usd": motif["avg_pnl_usd"],
                    "gas_efficiency": motif["gas_efficiency"],
                }
            )

    model: Dict[str, Any] = {
        "model_name": "successful_bot_logic_v2",
        "compute_backend": SURFACE.backend,
        "selection_basis": "rolling-window historical motif ranking from post_records",
        "rolling_window": {
            "window_days": window_days,
            "window_start_utc": window_start_iso,
            "window_end_utc": window_end_iso,
        },
        "constraints": {
            "require_positive_gas_efficiency": require_positive_gas_efficiency,
            "allowed_motif_count": len(allowed_motifs),
            "blocked_motif_count": max(0, len(motifs) - len(allowed_motifs)),
            "allowed_motifs": [
                {
                    "motif_id": m["motif_id"],
                    "chain": m["chain"],
                    "pair": m["pair"],
                    "gas_efficiency": m["gas_efficiency"],
                    "avg_pnl_usd": m["avg_pnl_usd"],
                }
                for m in allowed_motifs
            ],
        },
        "top_priority_chains": top_chains,
        "gates": gates,
        "quantum_classical_efficiency": {
            "temperature": temperature,
            "quantum_expected_avg_pnl_usd": round(quantum_expected_avg_pnl, 8),
            "quantum_expected_gas_efficiency": round(quantum_expected_gas_eff, 8),
            "classical_best_avg_pnl_usd": round(classical_best_avg_pnl, 8),
            "classical_best_gas_efficiency": round(classical_best_gas_eff, 8),
            "classical_space_advantages": classical_space_advantages[:20],
        },
        "execution_policy": [
            "Allow only motifs with positive rolling gas efficiency when enabled.",
            "Prefer chains in top_priority_chains ordered by current friction rank.",
            "Pause when gas exceeds max_gas_usd gate.",
            "Pause when projected slippage exceeds max_slippage_bps gate.",
            "Only execute when projected net PnL >= min_net_pnl_usd.",
            "Recompute model weekly from latest records (rolling window).",
        ],
    }
    return model


def write_markdown(path: Path, motifs: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# Successful Bot Logic Model")
    lines.append("")
    lines.append("This report ranks strategy motifs from historical records and derives an execution logic model.")
    lines.append("")
    lines.append("## Rolling Window")
    lines.append("")
    rw = model["rolling_window"]
    lines.append(f"- window_days: {rw['window_days']}")
    lines.append(f"- window_start_utc: {rw['window_start_utc']}")
    lines.append(f"- window_end_utc: {rw['window_end_utc']}")
    lines.append("")
    lines.append("## Derived Gates")
    lines.append("")
    gates = model["gates"]
    lines.append(f"- max_gas_usd: {gates['max_gas_usd']}")
    lines.append(f"- max_slippage_bps: {gates['max_slippage_bps']}")
    lines.append(f"- min_net_pnl_usd: {gates['min_net_pnl_usd']}")
    lines.append(f"- top_priority_chains: {', '.join(model['top_priority_chains'])}")
    lines.append("")
    lines.append("## Quantum vs Classical")
    lines.append("")
    qc = model["quantum_classical_efficiency"]
    lines.append(f"- quantum_expected_avg_pnl_usd: {qc['quantum_expected_avg_pnl_usd']}")
    lines.append(f"- quantum_expected_gas_efficiency: {qc['quantum_expected_gas_efficiency']}")
    lines.append(f"- classical_best_avg_pnl_usd: {qc['classical_best_avg_pnl_usd']}")
    lines.append(f"- classical_best_gas_efficiency: {qc['classical_best_gas_efficiency']}")
    lines.append("")
    lines.append("## Top Motifs")
    lines.append("")
    lines.append("| Rank | Chain | Pair | Success Score | Win Rate | Execute Rate | Avg PnL USD | Gas Efficiency |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for i, row in enumerate(motifs[:20], start=1):
        lines.append(
            f"| {i} | {row['chain']} | {row['pair']} | {row['success_score']} | {row['win_rate']} | {row['execute_rate']} | {row['avg_pnl_usd']} | {row['gas_efficiency']} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review successful bot history and derive logic model.")
    parser.add_argument("--post-records", required=True, help="Path to post_records.jsonl")
    parser.add_argument("--window-days", type=int, default=30, help="Rolling analysis window in days.")
    parser.add_argument("--temperature", type=float, default=0.35, help="Quantum softmax temperature.")
    parser.add_argument("--allow-nonpositive-gas-efficiency", action="store_true", help="Disable positive gas-efficiency motif filter.")
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    parser.add_argument("--out-md", required=True, help="Output markdown path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    post_rows = load_jsonl(Path(args.post_records))
    if not post_rows:
        print(json.dumps({"error": "no_post_records"}, indent=2))
        return 2

    filtered_rows, window_start_iso, window_end_iso = filter_rows_rolling(post_rows, int(args.window_days))
    if not filtered_rows:
        print(json.dumps({"error": "no_rows_in_window", "window_days": int(args.window_days)}, indent=2))
        return 2

    motifs = build_motif_stats(filtered_rows)
    model = derive_logic_model(
        filtered_rows,
        motifs,
        window_days=int(args.window_days),
        window_start_iso=window_start_iso,
        window_end_iso=window_end_iso,
        require_positive_gas_efficiency=not bool(args.allow_nonpositive_gas_efficiency),
        temperature=float(args.temperature),
    )

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"model": model, "motifs": motifs}, indent=2) + "\n", encoding="utf-8")

    write_markdown(Path(args.out_md), motifs, model)

    print(
        json.dumps(
            {
                "backend": SURFACE.backend,
                "rows_in_window": len(filtered_rows),
                "motifs_ranked": len(motifs),
                "allowed_motif_count": model["constraints"]["allowed_motif_count"],
                "top_chain": model["top_priority_chains"][0] if model["top_priority_chains"] else None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
