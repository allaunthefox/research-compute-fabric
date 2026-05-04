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
import csv
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, cast

from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "passive_macro_record.schema.json"

# Canonical symbols consumed by downstream modeling.
DEFAULT_SYMBOLS: Dict[str, List[str]] = {
    "equity": ["^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225", "000300.SS"],
    "rates": ["^TNX", "^FVX", "^IRX", "^TYX"],
    "commodity": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F"],
    "fx": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCNY=X"],
}

# Conservative bps tolerances per class for source consensus.
CONSENSUS_BPS_BY_CLASS: Dict[str, float] = {
    "equity": 60.0,
    "rates": 35.0,
    "commodity": 90.0,
    "fx": 25.0,
}

STOOQ_SYMBOL_MAP: Dict[str, str] = {
    "^GSPC": "^spx",
    "^DJI": "^dji",
    "^IXIC": "^ixic",
    "^FTSE": "^ukx",
    "^N225": "^nkx",
    "000300.SS": "000300",
    "GC=F": "gold",
    "SI=F": "silver",
    "CL=F": "cl.f",
    "NG=F": "ng.f",
    "HG=F": "hg.f",
    "EURUSD=X": "eurusd",
    "GBPUSD=X": "gbpusd",
    "USDJPY=X": "usdjpy",
    "AUDUSD=X": "audusd",
    "USDCNY=X": "usdcny",
}

FRED_SERIES_MAP: Dict[str, str] = {
    "^TNX": "DGS10",
    "^FVX": "DGS5",
    "^IRX": "DGS3MO",
    "^TYX": "DGS30",
    "GC=F": "GOLDAMGBD228NLBM",
    "SI=F": "SLVPRUSD",
    "CL=F": "DCOILWTICO",
    "NG=F": "DHHNGSP",
    "HG=F": "PCOPPUSDM",
    "EURUSD=X": "DEXUSEU",
    "GBPUSD=X": "DEXUSUK",
    "USDJPY=X": "DEXJPUS",
    "AUDUSD=X": "DEXUSAL",
    "USDCNY=X": "DEXCHUS",
    "^GSPC": "SP500",
}


def http_get_text(url: str, timeout: float = 20.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "macro-market-collector/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_get_json(url: str, timeout: float = 20.0) -> Any:
    return json.loads(http_get_text(url, timeout=timeout))


def load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def iso_from_unix(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).replace(microsecond=0).isoformat()


def iso_from_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    return dt.isoformat()


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def safe_symbol_token(symbol: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in symbol)
    return token.strip("_")[:40] or "UNKNOWN"


def bps_spread(prices: List[float]) -> float:
    if len(prices) < 2:
        return 0.0
    mean_px = sum(prices) / len(prices)
    if mean_px <= 0:
        return 0.0
    return ((max(prices) - min(prices)) / mean_px) * 10000.0


def nearest_price(points: List[Tuple[datetime, float]], ts: datetime, max_align_seconds: int) -> Optional[float]:
    if not points:
        return None
    idx = min(range(len(points)), key=lambda i: abs((points[i][0] - ts).total_seconds()))
    dt = abs((points[idx][0] - ts).total_seconds())
    if dt > max_align_seconds:
        return None
    return float(points[idx][1])


def fetch_yahoo_series(symbol: str, interval: str, lookback_range: str) -> List[Tuple[datetime, float]]:
    encoded = urllib.parse.quote(symbol, safe="")
    query = urllib.parse.urlencode({"interval": interval, "range": lookback_range})
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?{query}"

    payload = http_get_json(url)
    payload_map: Mapping[str, Any] = cast(Mapping[str, Any], payload) if isinstance(payload, dict) else {}
    chart_raw = payload_map.get("chart", {})
    chart_map: Mapping[str, Any] = cast(Mapping[str, Any], chart_raw) if isinstance(chart_raw, dict) else {}

    result_raw = chart_map.get("result", [])
    result_list: List[Any] = cast(List[Any], result_raw) if isinstance(result_raw, list) else []
    if not result_list:
        return []

    first = cast(Mapping[str, Any], result_list[0]) if isinstance(result_list[0], dict) else {}
    ts_raw = first.get("timestamp", [])
    timestamps: List[Any] = cast(List[Any], ts_raw) if isinstance(ts_raw, list) else []

    indicators_raw = first.get("indicators", {})
    indicators: Mapping[str, Any] = cast(Mapping[str, Any], indicators_raw) if isinstance(indicators_raw, dict) else {}
    quote_raw = indicators.get("quote", [])
    quote_list: List[Any] = cast(List[Any], quote_raw) if isinstance(quote_raw, list) else []
    if not quote_list:
        return []

    q0 = cast(Mapping[str, Any], quote_list[0]) if isinstance(quote_list[0], dict) else {}
    closes_raw = q0.get("close", [])
    closes: List[Any] = cast(List[Any], closes_raw) if isinstance(closes_raw, list) else []

    out: List[Tuple[datetime, float]] = []
    for i, ts in enumerate(timestamps):
        if i >= len(closes):
            break
        if not isinstance(ts, int | float):
            continue
        px_raw = closes[i]
        if not isinstance(px_raw, int | float):
            continue
        px = float(px_raw)
        if px <= 0:
            continue
        out.append((datetime.fromtimestamp(int(ts), tz=UTC), px))
    return out


def fetch_stooq_series(symbol: str) -> List[Tuple[datetime, float]]:
    stooq_symbol = STOOQ_SYMBOL_MAP.get(symbol)
    if not stooq_symbol:
        return []
    url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(stooq_symbol)}&i=d"
    text = http_get_text(url)

    out: List[Tuple[datetime, float]] = []
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        date_str = str(row.get("Date", "")).strip()
        close_str = str(row.get("Close", "")).strip()
        if not date_str or not close_str:
            continue
        try:
            px = float(close_str)
        except ValueError:
            continue
        if px <= 0:
            continue
        out.append((parse_iso(iso_from_date(date_str)), px))
    return out


def fetch_fred_series(symbol: str) -> List[Tuple[datetime, float]]:
    series_id = FRED_SERIES_MAP.get(symbol)
    if not series_id:
        return []

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={urllib.parse.quote(series_id)}"
    text = http_get_text(url)

    out: List[Tuple[datetime, float]] = []
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        date_str = str(row.get("DATE", "")).strip()
        value_str = str(row.get(series_id, "")).strip()
        if not date_str or not value_str or value_str == ".":
            continue
        try:
            px = float(value_str)
        except ValueError:
            continue
        if px <= 0:
            continue
        out.append((parse_iso(iso_from_date(date_str)), px))
    return out


def iter_targets(args: argparse.Namespace) -> Iterable[Tuple[str, str]]:
    if args.symbol:
        for item in args.symbol:
            left, right = item.split(":", 1) if ":" in item else ("", "")
            market_class = left.strip().lower()
            symbol = right.strip()
            if market_class in DEFAULT_SYMBOLS and symbol:
                yield market_class, symbol
        return

    for market_class, symbols in DEFAULT_SYMBOLS.items():
        for symbol in symbols:
            yield market_class, symbol


def collect_records(args: argparse.Namespace, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    idx = 0
    now_epoch = int(time.time())

    for market_class, symbol in iter_targets(args):
        source_series: Dict[str, List[Tuple[datetime, float]]] = {}

        try:
            source_series["yahoo"] = fetch_yahoo_series(symbol=symbol, interval=args.interval, lookback_range=args.lookback_range)
        except (urllib.error.URLError, json.JSONDecodeError, ValueError, TypeError, OSError):
            source_series["yahoo"] = []

        try:
            source_series["stooq"] = fetch_stooq_series(symbol=symbol)
        except (urllib.error.URLError, ValueError, TypeError, OSError):
            source_series["stooq"] = []

        try:
            source_series["fred"] = fetch_fred_series(symbol=symbol)
        except (urllib.error.URLError, ValueError, TypeError, OSError):
            source_series["fred"] = []

        # Anchor on Yahoo timestamps when present; otherwise use whichever source has data.
        anchor_series = source_series["yahoo"]
        if not anchor_series:
            for src_name in ("stooq", "fred"):
                if source_series[src_name]:
                    anchor_series = source_series[src_name]
                    break
        if not anchor_series:
            continue

        tol_bps = CONSENSUS_BPS_BY_CLASS.get(market_class, 80.0)

        for ts, anchor_px in anchor_series:
            aligned: Dict[str, float] = {}
            for src_name, series in source_series.items():
                px = nearest_price(series, ts, max_align_seconds=int(args.max_align_seconds))
                if px is not None and px > 0:
                    aligned[src_name] = float(px)

            if not aligned:
                continue

            values = list(aligned.values())
            consensus_px = sum(values) / len(values)
            spread_bps = bps_spread(values)
            consensus_ok = len(values) >= 2 and spread_bps <= tol_bps

            record: Dict[str, Any] = {
                "version": "v1.0",
                "record_id": f"MACRO-{market_class}-{safe_symbol_token(symbol)}-{idx:08d}-{now_epoch}",
                "timestamp_utc": ts.replace(microsecond=0).isoformat(),
                "market_class": market_class,
                "symbol": symbol,
                "price_usd": round(consensus_px, 8),
                "source": "multi-source-consensus",
                "metadata": {
                    "collector": "collect_macro_market_records.py",
                    "interval": args.interval,
                    "range": args.lookback_range,
                    "source_prices": {k: round(v, 8) for k, v in aligned.items()},
                    "source_count": len(aligned),
                    "consensus_ok": consensus_ok,
                    "max_source_deviation_bps": round(spread_bps, 6),
                    "consensus_tolerance_bps": round(tol_bps, 6),
                    "source_priority": ["yahoo", "stooq", "fred"],
                },
            }
            validate(instance=record, schema=schema)
            records.append(record)
            idx += 1

    return records


def write_jsonl(path: Path, rows: List[Dict[str, Any]], append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect worldwide macro feeds with redundancy (Yahoo/Stooq/FRED) and source-consensus checks.")
    parser.add_argument("--symbol", action="append", help="Optional override in the form market_class:SYMBOL. Repeatable.")
    parser.add_argument("--interval", default="5m", help="Yahoo chart interval, e.g. 1m, 5m, 15m, 1h, 1d.")
    parser.add_argument("--lookback-range", default="5d", help="Yahoo chart range, e.g. 1d, 5d, 1mo.")
    parser.add_argument("--max-align-seconds", type=int, default=43200, help="Maximum timestamp alignment distance across sources.")
    parser.add_argument("--out", default=str(PROJECT_ROOT / "out" / "micro_cap_sim" / "macro_records.jsonl"), help="Output macro records JSONL path.")
    parser.add_argument("--append", action="store_true", help="Append to output instead of overwrite.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = load_schema()
    rows = collect_records(args, schema)
    write_jsonl(Path(args.out), rows, append=bool(args.append))

    by_class: Dict[str, int] = {"equity": 0, "rates": 0, "commodity": 0, "fx": 0}
    source_count_hist: Dict[str, int] = {"1": 0, "2": 0, "3": 0}
    consensus_ok = 0

    for row in rows:
        cls = str(row.get("market_class", ""))
        if cls in by_class:
            by_class[cls] += 1

        metadata = row.get("metadata", {}) if isinstance(row.get("metadata", {}), dict) else {}
        sc = int(metadata.get("source_count", 0) or 0)
        if sc in (1, 2, 3):
            source_count_hist[str(sc)] += 1
        if bool(metadata.get("consensus_ok", False)):
            consensus_ok += 1

    print(
        json.dumps(
            {
                "rows_written": len(rows),
                "by_class": by_class,
                "source_count_hist": source_count_hist,
                "consensus_ok_rows": consensus_ok,
                "out": args.out,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
