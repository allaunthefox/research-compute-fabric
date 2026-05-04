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


def infer_chain(strategy_id: str) -> str:
    parts = strategy_id.split("-")
    if len(parts) >= 3 and parts[0] == "SIM":
        return parts[1].lower()
    return "unknown"


def realized_vol(prices: List[float]) -> float:
    if len(prices) < 2:
        return 0.0
    rets: List[float] = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        cur = prices[i]
        if prev > 0:
            rets.append((cur - prev) / prev)
    return std(rets) if rets else 0.0


def build_axes(chain_rows: List[Dict[str, Any]], post_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prices: Dict[str, List[float]] = {}
    gas: Dict[str, List[float]] = {}
    spread: Dict[str, List[float]] = {}
    decisions: Dict[str, int] = {}
    pauses: Dict[str, int] = {}

    for row in chain_rows:
        c = str(row.get("chain", "unknown")).lower()
        prices.setdefault(c, []).append(float(row.get("price_usd", 0.0)))
        gas.setdefault(c, []).append(float(row.get("gas_estimate_usd", 0.0)))
        spread.setdefault(c, []).append(float(row.get("spread_bps", 0.0)))

    for row in post_rows:
        c = infer_chain(str(row.get("strategy_id", "")))
        decisions[c] = decisions.get(c, 0) + 1
        if str(row.get("outcome", "")).upper() == "PAUSED":
            pauses[c] = pauses.get(c, 0) + 1

    chains = sorted(prices.keys())
    gas_mean = {c: mean(gas.get(c, [])) for c in chains}
    spread_med = {c: sorted(spread.get(c, [0.0]))[len(spread.get(c, [0.0])) // 2] for c in chains}
    # Use gas-cost series volatility as a chain-physics stress proxy.
    vol = {c: realized_vol(gas.get(c, [])) for c in chains}
    pause_rate = {c: (pauses.get(c, 0) / decisions.get(c, 1)) if decisions.get(c, 0) else 0.0 for c in chains}

    gas_vec = [gas_mean[c] for c in chains]
    spread_vec = [spread_med[c] for c in chains]
    vol_vec = [vol[c] for c in chains]
    pause_vec = [pause_rate[c] for c in chains]

    out: List[Dict[str, Any]] = []
    gas_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(gas_vec))}
    spread_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(spread_vec))}
    vol_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(vol_vec))}
    pause_z_map = {c: z for c, z in zip(chains, SURFACE.zscores(pause_vec))}

    for c in chains:
        gas_z = gas_z_map[c]
        spread_z = spread_z_map[c]
        vol_z = vol_z_map[c]
        pause_z = pause_z_map[c]

        friction = 0.40 * gas_z + 0.30 * spread_z + 0.20 * vol_z + 0.10 * pause_z
        opportunity = 100.0 * (1.0 - SURFACE.sigmoid(friction))

        out.append(
            {
                "chain": c,
                "axis_point": {
                    "gas_drag_z": round(gas_z, 8),
                    "spread_drag_z": round(spread_z, 8),
                    "vol_drag_z": round(vol_z, 8),
                    "pause_drag_z": round(pause_z, 8),
                },
                "friction_score": round(friction, 8),
                "opportunity_score": round(opportunity, 8),
                "pause_rate": round(pause_rate[c], 8),
                "sample_count": len(prices.get(c, [])),
            }
        )

    out.sort(key=lambda x: float(x["friction_score"]))
    return out


def stability_mean(ranked: List[Dict[str, Any]]) -> Dict[str, Any]:
    friction_values = [float(r["friction_score"]) for r in ranked]
    if not friction_values:
        return {
            "stability_chain_count": 0,
            "average_mean_opportunity": 0.0,
            "selected_chains": [],
        }

    mu = mean(friction_values)
    sigma = std(friction_values)
    threshold = mu + (0.35 * sigma)

    stable = [
        r for r in ranked
        if float(r["friction_score"]) <= threshold and float(r["pause_rate"]) < 0.65
    ]

    stable_opportunity = [float(r["opportunity_score"]) for r in stable]
    average_mean_opportunity = mean(stable_opportunity) if stable_opportunity else 0.0

    return {
        "friction_mean": round(mu, 8),
        "friction_std": round(sigma, 8),
        "stability_threshold": round(threshold, 8),
        "stability_chain_count": len(stable),
        "average_mean_opportunity": round(average_mean_opportunity, 8),
        "selected_chains": [str(r["chain"]) for r in stable],
    }


def write_markdown(path: Path, ranked: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# Precomputed Chain Axis Points")
    lines.append("")
    lines.append("Each chain is represented as a 4D axis point: gas drag, spread drag, volatility drag, and pause drag.")
    lines.append("")
    lines.append("## Stability-Safe Mean")
    lines.append("")
    lines.append(f"- Friction mean: {summary['friction_mean']}")
    lines.append(f"- Friction std: {summary['friction_std']}")
    lines.append(f"- Stability threshold: {summary['stability_threshold']}")
    lines.append(f"- Stable chain count: {summary['stability_chain_count']}")
    lines.append(f"- Average mean opportunity (stable set): {summary['average_mean_opportunity']}")
    lines.append(f"- Stable chains: {', '.join(summary['selected_chains']) if summary['selected_chains'] else 'none'}")
    lines.append("")
    lines.append("## Axis Table")
    lines.append("")
    lines.append("| Rank | Chain | Gas z | Spread z | Vol z | Pause z | Friction | Opportunity |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for i, row in enumerate(ranked, start=1):
        a = row["axis_point"]
        lines.append(
            f"| {i} | {row['chain']} | {a['gas_drag_z']} | {a['spread_drag_z']} | {a['vol_drag_z']} | {a['pause_drag_z']} | {row['friction_score']} | {row['opportunity_score']} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Precompute chain axis dimensional points and stability-safe average mean.")
    parser.add_argument("--chain-records", required=True, help="Path to chain_records.jsonl")
    parser.add_argument("--post-records", help="Optional path to post_records.jsonl")
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    parser.add_argument("--out-md", required=True, help="Output markdown path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chain_rows = load_jsonl(Path(args.chain_records))
    post_rows = load_jsonl(Path(args.post_records)) if args.post_records else []

    if not chain_rows:
        print(json.dumps({"error": "no_chain_records"}, indent=2))
        return 2

    ranked = build_axes(chain_rows, post_rows)
    summary = stability_mean(ranked)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"backend": SURFACE.backend, "summary": summary, "ranking": ranked}, indent=2) + "\n", encoding="utf-8")

    write_markdown(Path(args.out_md), ranked, summary)

    print(json.dumps({"backend": SURFACE.backend, "chains_ranked": len(ranked), "stable_chain_count": summary["stability_chain_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
