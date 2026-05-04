#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from scripts.gpgpu_surface import get_surface
except ImportError:
    from gpgpu_surface import get_surface


SURFACE = get_surface()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def mean(values: List[float]) -> float:
    return SURFACE.mean(values)


def std(values: List[float]) -> float:
    return SURFACE.std(values)


def zscore(value: float, values: List[float]) -> float:
    sigma = std(values)
    if sigma == 0.0:
        return 0.0
    return (value - mean(values)) / sigma


def infer_chain_from_strategy_id(strategy_id: str) -> str:
    # Expected simulation format: SIM-<chain>-<pair>-<index>
    parts = strategy_id.split("-")
    if len(parts) >= 3 and parts[0] == "SIM":
        return parts[1].lower()
    return "unknown"


def realized_volatility(prices: List[float]) -> float:
    if len(prices) < 2:
        return 0.0
    rets: List[float] = []
    for idx in range(1, len(prices)):
        prev = prices[idx - 1]
        cur = prices[idx]
        if prev > 0:
            rets.append((cur - prev) / prev)
    if not rets:
        return 0.0
    return float(std(rets))


def build_chain_metrics(
    chain_rows: List[Dict[str, Any]],
    post_rows: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    prices_by_chain: Dict[str, List[float]] = {}
    gas_by_chain: Dict[str, List[float]] = {}
    spread_by_chain: Dict[str, List[float]] = {}

    for row in chain_rows:
        chain = str(row.get("chain", "unknown")).lower()
        prices_by_chain.setdefault(chain, []).append(float(row.get("price_usd", 0.0)))
        gas_by_chain.setdefault(chain, []).append(float(row.get("gas_estimate_usd", 0.0)))
        spread_by_chain.setdefault(chain, []).append(float(row.get("spread_bps", 0.0)))

    decision_counts: Dict[str, int] = {}
    pause_counts: Dict[str, int] = {}
    for row in post_rows:
        strategy_id = str(row.get("strategy_id", ""))
        chain = infer_chain_from_strategy_id(strategy_id)
        decision_counts[chain] = decision_counts.get(chain, 0) + 1
        if str(row.get("outcome", "")).upper() == "PAUSED":
            pause_counts[chain] = pause_counts.get(chain, 0) + 1

    metrics: Dict[str, Dict[str, float]] = {}
    for chain in sorted(prices_by_chain.keys()):
        decisions = decision_counts.get(chain, 0)
        pauses = pause_counts.get(chain, 0)
        pause_rate = (pauses / decisions) if decisions else 0.0
        metrics[chain] = {
            "avg_gas_usd": mean(gas_by_chain.get(chain, [])),
            "median_spread_bps": sorted(spread_by_chain.get(chain, [0.0]))[len(spread_by_chain.get(chain, [0.0])) // 2],
            "realized_volatility": realized_volatility(prices_by_chain.get(chain, [])),
            "pause_rate": pause_rate,
            "sample_count": float(len(prices_by_chain.get(chain, []))),
        }
    return metrics


def rank_chains(metrics: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    chains = sorted(metrics.keys())
    gas_vec = [metrics[c]["avg_gas_usd"] for c in chains]
    spread_vec = [metrics[c]["median_spread_bps"] for c in chains]
    vol_vec = [metrics[c]["realized_volatility"] for c in chains]
    pause_vec = [metrics[c]["pause_rate"] for c in chains]

    ranked: List[Dict[str, Any]] = []
    gas_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(gas_vec))}
    spread_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(spread_vec))}
    vol_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(vol_vec))}
    pause_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(pause_vec))}

    for chain in chains:
        gas_z = gas_z_map[chain]
        spread_z = spread_z_map[chain]
        vol_z = vol_z_map[chain]
        pause_z = pause_z_map[chain]

        # Lower is better: friction score approximates chain "physics" drag.
        friction_score = (
            0.40 * gas_z
            + 0.30 * spread_z
            + 0.20 * vol_z
            + 0.10 * pause_z
        )

        # Convert to a bounded opportunity score in [0, 100].
        opportunity_score = 100.0 * (1.0 - SURFACE.sigmoid(friction_score))

        ranked.append(
            {
                "chain": chain,
                "friction_score": round(friction_score, 6),
                "opportunity_score": round(opportunity_score, 4),
                **{k: round(v, 8) for k, v in metrics[chain].items()},
            }
        )

    ranked.sort(key=lambda row: row["friction_score"])
    return ranked


def write_markdown(path: Path, ranked: List[Dict[str, Any]]) -> None:
    lines: List[str] = []
    lines.append("# Chain Physics Friction Ranking")
    lines.append("")
    lines.append("Lower friction score means lower execution drag and better accumulation conditions.")
    lines.append("")
    lines.append("| Rank | Chain | Friction Score | Opportunity Score | Avg Gas USD | Median Spread bps | Realized Volatility | Pause Rate | Samples |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for idx, row in enumerate(ranked, start=1):
        lines.append(
            "| "
            + f"{idx} | {row['chain']} | {row['friction_score']} | {row['opportunity_score']} | "
            + f"{row['avg_gas_usd']} | {row['median_spread_bps']} | {row['realized_volatility']} | "
            + f"{row['pause_rate']} | {int(row['sample_count'])} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Model chain physics and rank lowest-friction accumulation targets.")
    parser.add_argument("--chain-records", required=True, help="Path to chain_records.jsonl")
    parser.add_argument("--post-records", help="Optional path to post_records.jsonl for pause-rate signal")
    parser.add_argument("--out-json", required=True, help="Output ranking JSON path")
    parser.add_argument("--out-md", required=True, help="Output ranking markdown path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chain_rows = load_jsonl(Path(args.chain_records))
    post_rows = load_jsonl(Path(args.post_records)) if args.post_records else []

    if not chain_rows:
        print(json.dumps({"error": "no_chain_records"}, indent=2))
        return 2

    metrics = build_chain_metrics(chain_rows, post_rows)
    ranked = rank_chains(metrics)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"backend": SURFACE.backend, "ranking": ranked}, indent=2) + "\n", encoding="utf-8")

    write_markdown(Path(args.out_md), ranked)

    print(json.dumps({"backend": SURFACE.backend, "chains_ranked": len(ranked), "best_chain": ranked[0]["chain"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
