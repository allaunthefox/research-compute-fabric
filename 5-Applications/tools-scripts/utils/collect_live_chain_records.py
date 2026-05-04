# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, cast

from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAIN_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "passive_chain_record.schema.json"

COINGECKO_ID_BY_SYMBOL = {
    "ETH": "ethereum",
    "BTC": "bitcoin",
    "ARB": "arbitrum",
    "OP": "optimism",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "BNB": "binancecoin",
    "MATIC": "polygon-ecosystem-token",
}

CHAIN_NATIVE_SYMBOL = {
    "ethereum": "ETH",
    "arbitrum": "ETH",
    "base": "ETH",
    "optimism": "ETH",
    "polygon": "MATIC",
    "solana": "SOL",
    "avalanche": "AVAX",
    "bsc": "BNB",
}

LLAMA_CHAIN_NAME = {
    "ethereum": "Ethereum",
    "arbitrum": "Arbitrum",
    "base": "Base",
    "optimism": "Optimism",
    "polygon": "Polygon",
    "solana": "Solana",
    "avalanche": "Avalanche",
    "bsc": "BSC",
}

# Approximate gas units for a basic swap-like action per chain.
SWAP_GAS_UNITS = {
    "ethereum": 180000,
    "arbitrum": 140000,
    "base": 140000,
    "optimism": 140000,
    "polygon": 160000,
    "avalanche": 160000,
    "bsc": 160000,
}

# Conservative fallback if RPC unavailable.
FALLBACK_GAS_USD = {
    "ethereum": 1.60,
    "arbitrum": 0.20,
    "base": 0.12,
    "optimism": 0.18,
    "polygon": 0.06,
    "solana": 0.01,
    "avalanche": 0.28,
    "bsc": 0.22,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def http_get_json(url: str, timeout: float = 20.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "passive-chain-collector/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def post_json(url: str, payload: Dict[str, Any], timeout: float = 20.0) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "passive-chain-collector/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def load_schema() -> Dict[str, Any]:
    return json.loads(CHAIN_SCHEMA_PATH.read_text(encoding="utf-8"))


def parse_pair(symbol: str) -> Tuple[str, str]:
    parts = symbol.strip().upper().split("/")
    if len(parts) != 2:
        raise ValueError(f"invalid symbol pair: {symbol}")
    return parts[0], parts[1]


def fetch_coin_data(ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not ids:
        return {}
    q = urllib.parse.urlencode({
        "vs_currency": "usd",
        "ids": ",".join(ids),
        "order": "market_cap_desc",
        "per_page": str(max(10, len(ids))),
        "page": "1",
        "sparkline": "false",
        "price_change_percentage": "24h",
    })
    url = f"https://api.coingecko.com/api/v3/coins/markets?{q}"
    rows = http_get_json(url)
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rows, list):
        rows_list = cast(List[Any], rows)
        for row_obj in rows_list:
            row = cast(Dict[str, Any], row_obj) if isinstance(row_obj, dict) else {}
            coin_id = str(row.get("id", ""))
            if coin_id:
                out[coin_id] = row
    return out


def rpc_url_for_chain(chain: str) -> Optional[str]:
    key = f"RPC_URL_{chain.upper()}"
    return os.environ.get(key)


def fetch_evm_gas_price_wei(rpc_url: str) -> Optional[int]:
    try:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice", "params": []}
        data = post_json(rpc_url, payload)
        data_map: Mapping[str, Any] = cast(Mapping[str, Any], data) if isinstance(data, dict) else {}
        raw = data_map.get("result")
        if isinstance(raw, str) and raw.startswith("0x"):
            return int(raw, 16)
    except (ValueError, TypeError, OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    return None


def estimate_gas_usd(chain: str, native_price_usd: float) -> Tuple[float, str]:
    chain_l = chain.lower()
    if chain_l == "solana":
        return FALLBACK_GAS_USD["solana"], "fallback-solana"

    rpc_url = rpc_url_for_chain(chain_l)
    if rpc_url:
        gas_price_wei = fetch_evm_gas_price_wei(rpc_url)
        if gas_price_wei is not None:
            gas_units = SWAP_GAS_UNITS.get(chain_l, 150000)
            gas_native = (gas_price_wei * gas_units) / 1_000_000_000_000_000_000
            return max(0.0, gas_native * native_price_usd), "rpc-eth_gasPrice"

    return FALLBACK_GAS_USD.get(chain_l, 0.25), "fallback-static"


def spread_proxy_bps(high_24h: float, low_24h: float, price: float) -> float:
    if price <= 0:
        return 0.0
    if high_24h <= 0 or low_24h <= 0:
        return 0.0
    half_range = max(0.0, (high_24h - low_24h) / 2.0)
    return (half_range / price) * 10000.0


def fetch_chain_tvl_map() -> Dict[str, float]:
    url = "https://api.llama.fi/v2/chains"
    rows = http_get_json(url)
    out: Dict[str, float] = {}
    if isinstance(rows, list):
        for row_obj in cast(List[Any], rows):
            row = cast(Dict[str, Any], row_obj) if isinstance(row_obj, dict) else {}
            name = str(row.get("name", ""))
            tvl = float(row.get("tvl", 0.0) or 0.0)
            if name and tvl > 0:
                out[name] = tvl
    return out


def liquidity_adjustment_factor(chain: str, tvl_map: Dict[str, float], target_chains: List[str]) -> float:
    llama_name = LLAMA_CHAIN_NAME.get(chain, chain.title())
    chain_tvl = tvl_map.get(llama_name, 0.0)
    peer_tvls = [
        tvl_map.get(LLAMA_CHAIN_NAME.get(c, c.title()), 0.0)
        for c in target_chains
        if tvl_map.get(LLAMA_CHAIN_NAME.get(c, c.title()), 0.0) > 0
    ]
    if chain_tvl <= 0 or not peer_tvls:
        return 1.0
    median_tvl = sorted(peer_tvls)[len(peer_tvls) // 2]
    if median_tvl <= 0:
        return 1.0
    factor = (median_tvl / chain_tvl) ** 0.2
    return max(0.6, min(1.8, factor))


def append_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def collect_once(chains: List[str], symbols: List[str], source_label: str, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    base_assets = sorted({parse_pair(sym)[0] for sym in symbols})
    coin_ids = sorted({COINGECKO_ID_BY_SYMBOL[a] for a in base_assets if a in COINGECKO_ID_BY_SYMBOL})
    coin_data = fetch_coin_data(coin_ids)
    tvl_map = fetch_chain_tvl_map()

    ts = utc_now_iso()
    records: List[Dict[str, Any]] = []
    idx = 0
    for chain in chains:
        native_symbol = CHAIN_NATIVE_SYMBOL.get(chain, "ETH")
        native_coin_id = COINGECKO_ID_BY_SYMBOL.get(native_symbol, "ethereum")
        native_price = float(coin_data.get(native_coin_id, {}).get("current_price", 0.0) or 0.0)
        gas_usd, gas_source = estimate_gas_usd(chain, native_price)
        liq_factor = liquidity_adjustment_factor(chain, tvl_map, chains)

        for symbol in symbols:
            base, _quote = parse_pair(symbol)
            coin_id = COINGECKO_ID_BY_SYMBOL.get(base)
            if not coin_id:
                continue
            row = coin_data.get(coin_id)
            if not row:
                continue

            price = float(row.get("current_price", 0.0) or 0.0)
            if price <= 0:
                # Skip malformed/empty quote rows to preserve schema validity.
                continue
            high_24h = float(row.get("high_24h", 0.0) or 0.0)
            low_24h = float(row.get("low_24h", 0.0) or 0.0)
            spread_bps = spread_proxy_bps(high_24h, low_24h, price)
            spread_bps_adj = spread_bps * liq_factor

            record: Dict[str, Any] = {
                "version": "v1.0",
                "record_id": f"LIVE-{chain}-{idx:08d}-{int(time.time())}",
                "timestamp_utc": ts,
                "chain": chain,
                "market_type": "spot",
                "symbol": symbol,
                "price_usd": round(price, 8),
                "spread_bps": round(spread_bps_adj, 6),
                "gas_estimate_usd": round(float(gas_usd), 8),
                "source": source_label,
                "metadata": {
                    "collector": "collect_live_chain_records.py",
                    "price_provider": "coingecko",
                    "liquidity_provider": "defillama",
                    "gas_source": gas_source,
                    "liquidity_adjustment_factor": round(liq_factor, 8),
                },
            }
            validate(instance=record, schema=schema)
            records.append(record)
            idx += 1

    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only live passive market collector for chain_records schema.")
    parser.add_argument("--target-chain", action="append", dest="target_chains", required=True, help="Target chain. Repeatable.")
    parser.add_argument("--symbol", action="append", dest="symbols", required=True, help="Pair symbol like ETH/USDC. Repeatable.")
    parser.add_argument("--out", default=str(PROJECT_ROOT / "out" / "micro_cap_sim" / "chain_records.jsonl"), help="Output chain_records.jsonl path.")
    parser.add_argument("--source", default="passive-monitor-live", help="Source label for records.")
    parser.add_argument("--interval-seconds", type=int, default=0, help="Optional interval for repeated collection. 0 runs once.")
    parser.add_argument("--iterations", type=int, default=1, help="Number of iterations when interval-seconds > 0.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chains = [c.strip().lower() for c in args.target_chains if c.strip()]
    symbols = [s.strip().upper() for s in args.symbols if s.strip()]
    schema = load_schema()
    out_path = Path(args.out)

    iterations = int(args.iterations) if args.interval_seconds > 0 else 1
    total_written = 0

    for n in range(iterations):
        try:
            records = collect_once(chains, symbols, args.source, schema)
        except urllib.error.URLError as exc:
            print(json.dumps({"error": "network_fetch_failed", "detail": str(exc)}, indent=2))
            return 2
        except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
            print(json.dumps({"error": "collection_failed", "detail": str(exc)}, indent=2))
            return 2

        append_jsonl(out_path, records)
        total_written += len(records)

        print(json.dumps({"iteration": n + 1, "records_written": len(records), "out": str(out_path)}, indent=2))

        if args.interval_seconds > 0 and n < iterations - 1:
            time.sleep(max(1, int(args.interval_seconds)))

    print(json.dumps({"total_written": total_written, "out": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
