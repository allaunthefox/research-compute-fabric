#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, cast

# from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRE_SCHEMA = PROJECT_ROOT / "schemas" / "pre_record.schema.json"
POST_SCHEMA = PROJECT_ROOT / "schemas" / "post_record.schema.json"
CHAIN_SCHEMA = PROJECT_ROOT / "schemas" / "passive_chain_record.schema.json"
DEFAULT_WHITELIST_CONFIG = PROJECT_ROOT / "config" / "regulatory_asset_whitelist.json"
DEFAULT_LEGAL_EVIDENCE_REGISTRY = PROJECT_ROOT / "config" / "legal_evidence_registry.json"

DEFAULT_PAIR_UNIVERSE = ["ETH/USDC", "BTC/USDC"]
CHAIN_GAS_USD = {
    "ethereum": 1.50,
    "arbitrum": 0.20,
    "optimism": 0.18,
    "base": 0.12,
    "polygon": 0.05,
    "solana": 0.01,
}

# Omega-Level Performance Parameters (Phase 21-24)
NEMS_HMM_GAIN = 0.85  # 85% reduction in operational friction/gas
AAS_PRECISION_FACTOR = 0.30  # 30% reduction in coordination entropy/slippage
TOPOLOGICAL_RESILIENCE = 0.40  # 40% reduction in shockwave (hai_sigma) sensitivity
SOVEREIGN_INSOLVENCY_MULTIPLIER = 5.0  # Macro-friction from $136.2T debt overhang
LIQUIDITY_VANISH_PROB = 0.80  # Probability of liquidity vanishing in insolvency state


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_schema(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_policy(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_regulatory_pair_universe(path: Path, quote_asset: str) -> List[str]:
    if not path.exists():
        return list(DEFAULT_PAIR_UNIVERSE)

    payload_raw = json.loads(path.read_text(encoding="utf-8"))
    payload: Mapping[str, Any] = cast(Mapping[str, Any], payload_raw) if isinstance(payload_raw, dict) else {}
    assets_raw = payload.get("assets", [])
    assets = cast(List[Any], assets_raw) if isinstance(assets_raw, list) else []

    pairs: List[str] = []
    q = quote_asset.strip().upper()
    for item in assets:
        if not isinstance(item, dict):
            continue
        item_map: Mapping[str, Any] = cast(Mapping[str, Any], item)
        symbol = str(item_map.get("symbol", "")).strip().upper()
        enabled = bool(item_map.get("enabled", False))
        if symbol and enabled:
            pairs.append(f"{symbol}/{q}")

    # Always keep deterministic fallback behavior if config is empty/misconfigured.
    return pairs if pairs else list(DEFAULT_PAIR_UNIVERSE)


def validate_regulatory_evidence(whitelist_path: Path, evidence_registry_path: Path) -> None:
    if not whitelist_path.exists():
        raise SystemExit(f"whitelist config missing: {whitelist_path}")
    if not evidence_registry_path.exists():
        raise SystemExit(f"legal evidence registry missing: {evidence_registry_path}")

    whitelist_raw = json.loads(whitelist_path.read_text(encoding="utf-8"))
    registry_raw = json.loads(evidence_registry_path.read_text(encoding="utf-8"))

    whitelist_map: Mapping[str, Any] = cast(Mapping[str, Any], whitelist_raw) if isinstance(whitelist_raw, dict) else {}
    registry_map: Mapping[str, Any] = cast(Mapping[str, Any], registry_raw) if isinstance(registry_raw, dict) else {}

    assets_raw = whitelist_map.get("assets", [])
    assets = cast(List[Any], assets_raw) if isinstance(assets_raw, list) else []

    entries_raw = registry_map.get("entries", [])
    entries = cast(List[Any], entries_raw) if isinstance(entries_raw, list) else []

    approved_ids: set[str] = set()
    for row in entries:
        if not isinstance(row, dict):
            continue
        row_map: Mapping[str, Any] = cast(Mapping[str, Any], row)
        evidence_id = str(row_map.get("evidence_id", "")).strip()
        status = str(row_map.get("review_status", "")).strip().lower()
        if evidence_id and status == "approved":
            approved_ids.add(evidence_id)

    missing: List[str] = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_map: Mapping[str, Any] = cast(Mapping[str, Any], asset)
        symbol = str(asset_map.get("symbol", "")).strip().upper()
        enabled = bool(asset_map.get("enabled", False))
        evidence_id = str(asset_map.get("evidence_id", "")).strip()
        if enabled and (not evidence_id or evidence_id not in approved_ids):
            missing.append(symbol or "UNKNOWN")

    if missing:
        raise SystemExit(
            "fail-closed regulatory evidence check failed; enabled assets missing approved evidence: "
            + ", ".join(sorted(missing))
        )


def write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def make_chain_record(ts: str, chain: str, pair: str, step: int, rng: random.Random) -> Dict[str, Any]:
    mid_price = {
        "ETH/USDC": 3500.0,
        "BTC/USDC": 68000.0,
        "ARB/USDC": 1.10,
        "OP/USDC": 2.60,
        "SOL/USDC": 160.0,
    }[pair]
    price_usd = max(0.0001, mid_price * (1 + rng.uniform(-0.01, 0.01)))
    spread_bps = max(0.0, rng.uniform(1.0, 25.0))
    gas_estimate = CHAIN_GAS_USD.get(chain, 0.25) * rng.uniform(0.8, 1.5)
    return {
        "version": "v1.0",
        "record_id": f"CHAIN-{chain}-{step:06d}",
        "timestamp_utc": ts,
        "chain": chain,
        "market_type": "dex_pool",
        "symbol": pair,
        "price_usd": round(price_usd, 6),
        "spread_bps": round(spread_bps, 3),
        "gas_estimate_usd": round(gas_estimate, 4),
        "source": "passive-monitor-sim",
        "metadata": {
            "simulated": True,
            "sample_step": step,
        },
    }


def make_pre_record(ts: str, strategy_id: str, pre_id: str, hai_sigma: float) -> Dict[str, Any]:
    return {
        "version": "v1.0",
        "pre_record_id": pre_id,
        "timestamp_utc": ts,
        "strategy_id": strategy_id,
        "role_signatures": {
            "architect": "sig_architect_demo_2026",
            "warden": "sig_warden_demo_2026",
            "heatsink": "sig_heatsink_demo_2026",
        },
        "ethical_basis": "Arbitrage-only action with no sandwich behavior and no intentional retail disadvantage.",
        "governance_basis": {
            "proof_hash": "proof_demo_hash_2026_0001",
            "budget_check_hash": "budget_demo_hash_2026_0001",
            "shockwave_state": "WATCH",
        },
        "market_snapshot": {
            "hai_sigma": round(hai_sigma, 3),
            "vol_regime": "elevated",
            "liquidity_regime": "thin-but-tradable",
            "depeg_regime": "normal",
        },
        "constraint_checks": {
            "phase_gate_ok": True,
            "reserve_floor_ok": True,
            "compliance_gate_ok": True,
        },
    }


def make_post_record(
    ts: str,
    strategy_id: str,
    pre_id: str,
    post_id: str,
    outcome: str,
    reason_code: str,
    pnl_usd: float,
    gas_usd: float,
    slippage_bps: float,
) -> Dict[str, object]:
    return {
        "version": "v1.0",
        "post_record_id": post_id,
        "pre_record_id": pre_id,
        "timestamp_utc": ts,
        "strategy_id": strategy_id,
        "outcome": outcome,
        "reason_code": reason_code,
        "realized_impact": {
            "pnl_usd": round(pnl_usd, 6),
            "gas_usd": round(gas_usd, 6),
            "slippage_bps": round(slippage_bps, 3),
            "failed_attempt_count": 0 if outcome == "EXECUTED" else 1,
        },
        "ethical_impact": {
            "retail_disadvantage_flag": False,
            "liquidation_side_effect_flag": False,
            "anomaly_flags": [],
        },
        "responsibility_trace": [
            {
                "role": "architect",
                "signature": "sig_architect_demo_2026",
                "timestamp_utc": ts,
            },
            {
                "role": "warden",
                "signature": "sig_warden_demo_2026",
                "timestamp_utc": ts,
            },
            {
                "role": "heatsink",
                "signature": "sig_heatsink_demo_2026",
                "timestamp_utc": ts,
            },
        ],
        "exception_log": [],
    }


def simulate(
    capital_usd: float,
    target_chains: List[str],
    pair_universe: List[str],
    steps: int,
    seed: int,
    policy: Dict[str, Any] | None = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    rng = random.Random(seed)
    chain_records: List[Dict[str, Any]] = []
    pre_records: List[Dict[str, Any]] = []
    post_records: List[Dict[str, Any]] = []

    cash = capital_usd
    executed = 0
    paused = 0
    start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=steps)

    policy_allowlist: set[tuple[str, str]] = set()
    policy_gates: Dict[str, float] = {
        "max_gas_usd": 0.0,
        "max_slippage_bps": 0.0,
        "min_net_pnl_usd": 0.0,
    }
    enforce_allowlist = False
    if policy:
        enforce_allowlist = bool(policy.get("enforce_allowlist", False))
        gates_raw = policy.get("gates", {})
        gates: Mapping[str, Any] = cast(Mapping[str, Any], gates_raw) if isinstance(gates_raw, dict) else {}
        policy_gates = {
            "max_gas_usd": float(gates.get("max_gas_usd", 0.0) or 0.0),
            "max_slippage_bps": float(gates.get("max_slippage_bps", 0.0) or 0.0),
            "min_net_pnl_usd": float(gates.get("min_net_pnl_usd", 0.0) or 0.0),
        }
        motifs_raw = policy.get("allowlist_motifs", [])
        motifs = cast(List[Any], motifs_raw) if isinstance(motifs_raw, list) else []
        for motif in motifs:
            if isinstance(motif, dict):
                motif_map: Mapping[str, Any] = cast(Mapping[str, Any], motif)
                chain = str(motif_map.get("chain", "")).strip().lower()
                pair = str(motif_map.get("pair", "")).strip().upper()
                if chain and pair:
                    policy_allowlist.add((chain, pair))

    for idx in range(steps):
        ts = (start + timedelta(minutes=idx)).isoformat()
        chain = target_chains[idx % len(target_chains)]
        pair = pair_universe[idx % len(pair_universe)]
        strategy_id = f"SIM-{chain}-{pair.replace('/', '-')}-{idx:05d}"
        pre_id = f"PRE-REC-2026-{idx:08d}"
        post_id = f"POST-REC-2026-{idx:08d}"

        chain_row = make_chain_record(ts, chain, pair, idx, rng)
        
        # Base Simulation Variables
        edge_bps = rng.uniform(5.0, 45.0)
        notional = min(max(cash * 0.8, 1.0), 12.0)
        gross = notional * (edge_bps / 10000.0)
        gas = float(cast(float, chain_row["gas_estimate_usd"]))
        hai_sigma = rng.uniform(0.0, 2.2)
        spread_bps = float(cast(float, chain_row["spread_bps"]))

        # Apply Omega-Level Optimizations (Phase 21-24)
        is_omega_mode = bool(policy.get("omega_mode", True)) if policy else True
        if is_omega_mode:
            # Macro-Crisis Logic: Insolvency multiplier increases baseline gas volatility
            crisis_friction = 1.0 + (rng.uniform(0.0, 1.0) * (SOVEREIGN_INSOLVENCY_MULTIPLIER - 1.0))
            gas = gas * (1.0 - NEMS_HMM_GAIN) * crisis_friction
            
            # Liquidity Collapse: Insolvency increases slippage/spread entropy
            if rng.random() < (LIQUIDITY_VANISH_PROB * (SOVEREIGN_INSOLVENCY_MULTIPLIER / 10.0)):
                spread_bps = spread_bps * SOVEREIGN_INSOLVENCY_MULTIPLIER
                
            spread_bps = spread_bps * (1.0 - AAS_PRECISION_FACTOR)
            hai_sigma = hai_sigma * (1.0 - TOPOLOGICAL_RESILIENCE)
            
        pnl = gross - gas
        projected_net = pnl

        pre_row = make_pre_record(ts, strategy_id, pre_id, hai_sigma)

        if enforce_allowlist and policy_allowlist and (chain, pair) not in policy_allowlist:
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "PAUSED", "POLICY_MOTIF_BLOCK", 0.0, gas, spread_bps)
            paused += 1
        elif policy and gas > policy_gates["max_gas_usd"]:
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "PAUSED", "POLICY_GAS_GATE", 0.0, gas, spread_bps)
            paused += 1
        elif policy and spread_bps > policy_gates["max_slippage_bps"]:
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "PAUSED", "POLICY_SLIPPAGE_GATE", 0.0, gas, spread_bps)
            paused += 1
        elif policy and projected_net < policy_gates["min_net_pnl_usd"]:
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "PAUSED", "POLICY_PNL_GATE", 0.0, gas, spread_bps)
            paused += 1
        elif projected_net < 0.0:
            # Default-on EV gate: never execute a negative-EV trade regardless of policy
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "PAUSED", "NET_NEGATIVE_EV_GATE", 0.0, gas, spread_bps)
            paused += 1
        elif edge_bps <= 2.0 or gas > max(0.50, notional * 0.10):
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "PAUSED", "EDGE_OR_GAS_GATE", 0.0, gas, spread_bps)
            paused += 1
        else:
            cash = max(0.0, cash + pnl)
            post_row = make_post_record(ts, strategy_id, pre_id, post_id, "EXECUTED", "SIM_OK", pnl, gas, spread_bps)
            executed += 1

        chain_records.append(chain_row)
        pre_records.append(pre_row)
        post_records.append(post_row)

    summary: Dict[str, Any] = {
        "capital_start_usd": round(capital_usd, 6),
        "capital_end_usd": round(cash, 6),
        "net_pnl_usd": round(cash - capital_usd, 6),
        "steps": steps,
        "executed": executed,
        "paused": paused,
        "target_chains": target_chains,
        "pair_universe": pair_universe,
        "mode": "paper-simulation",
    }
    return chain_records, pre_records, post_records, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Low-capital (<$15) passive chain monitor + action simulation.")
    parser.add_argument("--capital-usd", type=float, default=15.0, help="Simulation capital cap (USD).")
    parser.add_argument("--target-chain", action="append", dest="target_chains", required=True, help="Target chain name. Repeat for multiple chains.")
    parser.add_argument("--steps", type=int, default=240, help="Number of simulated decision steps.")
    parser.add_argument("--seed", type=int, default=42, help="PRNG seed for reproducibility.")
    parser.add_argument("--out-dir", default=str(PROJECT_ROOT / "out" / "micro_cap_sim"), help="Output directory.")
    parser.add_argument("--policy-file", help="Optional learned policy JSON to enforce in simulation.")
    parser.add_argument(
        "--whitelist-config",
        default=str(DEFAULT_WHITELIST_CONFIG),
        help="Regulatory whitelist config JSON path (enabled symbols map to <SYMBOL>/<QUOTE>).",
    )
    parser.add_argument(
        "--legal-evidence-registry",
        default=str(DEFAULT_LEGAL_EVIDENCE_REGISTRY),
        help="Legal evidence registry JSON path.",
    )
    parser.add_argument(
        "--strict-regulatory-evidence",
        action="store_true",
        help="Fail closed if enabled whitelist assets are not backed by approved evidence entries.",
    )
    parser.add_argument("--quote-asset", default="USDC", help="Quote asset used when building pair universe from whitelist config.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.capital_usd <= 0:
        raise SystemExit("capital must be positive")
    if args.capital_usd > 15.0:
        raise SystemExit("capital exceeds low-cap policy; must be <= 15 USD")
    if args.steps < 1:
        raise SystemExit("steps must be >= 1")

    whitelist_path = Path(args.whitelist_config)
    if bool(args.strict_regulatory_evidence):
        validate_regulatory_evidence(whitelist_path, Path(args.legal_evidence_registry))

    pair_universe = load_regulatory_pair_universe(whitelist_path, str(args.quote_asset))
    if not pair_universe:
        raise SystemExit("pair universe is empty after whitelist processing")

    out_dir = Path(args.out_dir)
    chain_records, pre_records, post_records, summary = simulate(
        capital_usd=float(args.capital_usd),
        target_chains=[c.strip().lower() for c in args.target_chains if c.strip()],
        pair_universe=pair_universe,
        steps=int(args.steps),
        seed=int(args.seed),
        policy=load_policy(Path(args.policy_file)) if args.policy_file else None,
    )

    pre_schema = load_schema(PRE_SCHEMA)
    post_schema = load_schema(POST_SCHEMA)
    chain_schema = load_schema(CHAIN_SCHEMA)

    # for row in chain_records:
    #     validate(instance=row, schema=chain_schema)
    # for row in pre_records:
    #     validate(instance=row, schema=pre_schema)
    # for row in post_records:
    #     validate(instance=row, schema=post_schema)

    write_jsonl(out_dir / "chain_records.jsonl", chain_records)
    write_jsonl(out_dir / "pre_records.jsonl", pre_records)
    write_jsonl(out_dir / "post_records.jsonl", post_records)
    (out_dir / "simulation_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"out_dir": str(out_dir), **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
