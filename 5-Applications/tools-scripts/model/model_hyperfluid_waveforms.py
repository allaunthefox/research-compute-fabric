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
import statistics
# import subprocess (REMOVED BY WARDEN)
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def parse_strategy(strategy_id: str) -> Tuple[str, str]:
    parts = strategy_id.split("-")
    if len(parts) >= 5 and parts[0] == "SIM":
        chain = parts[1].lower()
        pair = f"{parts[2].upper()}/{parts[3].upper()}"
        return chain, pair
    return "unknown", "unknown/unknown"


def extract_impact(row: Dict[str, Any]) -> Dict[str, Any]:
    impact = row.get("realized_impact", {})
    return cast(Dict[str, Any], impact) if isinstance(impact, dict) else {}


def clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def safe_fmean(vals: Sequence[float]) -> float:
    return statistics.fmean(vals) if vals else 0.0


def sign(v: float) -> int:
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    mx = statistics.fmean(x)
    my = statistics.fmean(y)
    sx = statistics.pstdev(x)
    sy = statistics.pstdev(y)
    if sx == 0.0 or sy == 0.0:
        return 0.0
    cov = statistics.fmean([(a - mx) * (b - my) for a, b in zip(x, y)])
    return cov / (sx * sy)


# ---------------------------------------------------------------------------
# Qutrit layer — interference-based causal pressure
# ---------------------------------------------------------------------------
QutritState = Tuple[float, float, float]  # (a0, a1, a2) real amplitudes; sum of squares = 1


def encode_qutrit(v: float) -> QutritState:
    """Encode scalar v ∈ [-1, 1] as a normalised real qutrit amplitude vector.

    |0⟩ = bearish, |1⟩ = neutral, |2⟩ = bullish.
    Amplitudes are real non-negative; |a0|² + |a1|² + |a2|² = 1.
    """
    v = max(-1.0, min(1.0, v))
    neg = max(0.0, -v)
    pos = max(0.0, v)
    neu = 1.0 - neg - pos  # = 1 - |v| ≥ 0
    return (math.sqrt(neg), math.sqrt(neu), math.sqrt(pos))


def gate_12_swap(state: QutritState) -> QutritState:
    """π rotation on the |1⟩↔|2⟩ subspace.

    Models PSI subtraction as interference: the neutral and bullish amplitudes
    are exchanged, so a negative shock's neutral component is redirected to
    bullish rather than being transmitted at full negative amplitude.
    """
    a0, a1, a2 = state
    return (a0, a2, a1)


def qutrit_superpose(states: List[QutritState], weights: List[float]) -> QutritState:
    """Weighted amplitude superposition with renormalisation.

    Each state contributes amplitude proportional to sqrt(|weight| / sum_weights).
    """
    total = sum(abs(w) for w in weights)
    if total <= 0.0:
        return (0.0, 1.0, 0.0)
    out = [0.0, 0.0, 0.0]
    for state, w in zip(states, weights):
        amp = math.sqrt(abs(w) / total)
        out[0] += amp * state[0]
        out[1] += amp * state[1]
        out[2] += amp * state[2]
    norm = math.sqrt(out[0] * out[0] + out[1] * out[1] + out[2] * out[2])
    if norm > 1e-12:
        out = [x / norm for x in out]
    return (out[0], out[1], out[2])


def collapse_qutrit(state: QutritState, s_wt: float) -> Tuple[float, float]:
    """Measurement: extract (qutrit_pressure, qutrit_confidence).

    pressure   = s_wt × (p2 − p0)  where pi = amplitude_i²
    confidence = |p2 − p0| × (1 − p1)        penalises neutral-dominant states
    """
    a0, a1, a2 = state
    p0 = a0 * a0
    p1 = a1 * a1
    p2 = a2 * a2
    charge = p2 - p0
    return s_wt * charge, clamp(abs(charge) * (1.0 - p1), 0.0, 1.0)


def compute_qutrit_pressure(hpi: float, mti: float, psi: float, s_wt: float) -> Tuple[float, float]:
    """Qutrit causal pressure via amplitude interference of HPI/MTI/PSI.

    HPI (+0.55) and MTI (+0.65) encode directly.
    PSI (−0.80) enters via the |1⟩↔|2⟩ gate: its neutral amplitude is rotated
    to bullish before superposition, creating partial destructive interference
    that absorbs the shock rather than transmitting it at full classical weight.
    Returns (qutrit_pressure, qutrit_confidence).
    """
    q_hpi = encode_qutrit(hpi)
    q_mti = encode_qutrit(mti)
    q_psi = gate_12_swap(encode_qutrit(psi))
    q_final = qutrit_superpose([q_hpi, q_mti, q_psi], [0.55, 0.65, 0.80])
    return collapse_qutrit(q_final, s_wt)


def nearest_row(chain_rows: List[Dict[str, Any]], chain: str, pair: str, ts: datetime) -> Optional[Dict[str, Any]]:
    candidates: List[Tuple[float, Dict[str, Any]]] = []
    for row in chain_rows:
        if str(row.get("chain", "")).lower() != chain:
            continue
        if str(row.get("symbol", "")).upper() != pair:
            continue
        rts = parse_iso(str(row.get("timestamp_utc", "1970-01-01T00:00:00+00:00")))
        candidates.append((abs((rts - ts).total_seconds()), row))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def build_global_series(chain_rows: List[Dict[str, Any]]) -> Dict[str, List[Tuple[datetime, float]]]:
    by_symbol_ts: Dict[str, Dict[str, List[float]]] = {}
    for row in chain_rows:
        symbol = str(row.get("symbol", "")).upper()
        ts = str(row.get("timestamp_utc", ""))
        price = float(row.get("price_usd", 0.0) or 0.0)
        if not symbol or not ts or price <= 0.0:
            continue
        by_symbol_ts.setdefault(symbol, {}).setdefault(ts, []).append(price)

    out: Dict[str, List[Tuple[datetime, float]]] = {}
    for symbol, ts_map in by_symbol_ts.items():
        pts = [(parse_iso(ts), statistics.fmean(vals)) for ts, vals in ts_map.items()]
        pts.sort(key=lambda x: x[0])
        out[symbol] = pts
    return out


def build_macro_series(macro_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Tuple[datetime, float]]]]:
    by_class_symbol_ts: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    for row in macro_rows:
        market_class = str(row.get("market_class", "")).lower()
        symbol = str(row.get("symbol", "")).upper()
        ts = str(row.get("timestamp_utc", ""))
        price = float(row.get("price_usd", 0.0) or 0.0)
        if not market_class or not symbol or not ts or price <= 0.0:
            continue
        by_class_symbol_ts.setdefault(market_class, {}).setdefault(symbol, {}).setdefault(ts, []).append(price)

    out: Dict[str, Dict[str, List[Tuple[datetime, float]]]] = {}
    for market_class, sym_map in by_class_symbol_ts.items():
        out[market_class] = {}
        for symbol, ts_map in sym_map.items():
            pts = [(parse_iso(ts), statistics.fmean(vals)) for ts, vals in ts_map.items()]
            pts.sort(key=lambda x: x[0])
            out[market_class][symbol] = pts
    return out


def state_from_series(series: List[Tuple[datetime, float]], ts: datetime, lookback: int = 8) -> Dict[str, float]:
    if not series:
        return {"price": 0.0, "momentum": 0.0, "vol": 0.0}

    idx = min(range(len(series)), key=lambda i: abs((series[i][0] - ts).total_seconds()))
    price = float(series[idx][1])
    start = max(1, idx - lookback)

    rets: List[float] = []
    for i in range(start, idx + 1):
        p0 = float(series[i - 1][1])
        p1 = float(series[i][1])
        if p0 > 0.0:
            rets.append((p1 - p0) / p0)

    return {
        "price": price,
        "momentum": safe_fmean(rets),
        "vol": statistics.pstdev(rets) if len(rets) > 1 else 0.0,
    }


def market_state_at(
    macro_series: Dict[str, Dict[str, List[Tuple[datetime, float]]]],
    ts: datetime,
    class_focus: Dict[str, List[str]],
) -> Dict[str, float]:
    class_moms: List[float] = []
    class_vols: List[float] = []
    class_spread: List[float] = []

    for market_class, symbols in class_focus.items():
        series_map = macro_series.get(market_class, {})
        states: List[Dict[str, float]] = []
        for sym in symbols:
            st = state_from_series(series_map.get(sym.upper(), []), ts)
            if st["price"] > 0.0:
                states.append(st)

        if states:
            moms = [s["momentum"] for s in states]
            vols = [s["vol"] for s in states]
            class_moms.append(statistics.fmean(moms))
            class_vols.append(statistics.fmean(vols))
            class_spread.append(max(moms) - min(moms) if len(moms) > 1 else 0.0)

    return {
        "momentum": safe_fmean(class_moms),
        "vol": safe_fmean(class_vols),
        "dispersion": safe_fmean(class_spread),
    }


def session_weight(ts: datetime) -> float:
    h = ts.hour
    if 0 <= h < 7:
        return 0.95
    if 7 <= h < 12:
        return 1.10
    if 12 <= h < 17:
        return 1.25
    if 17 <= h < 21:
        return 1.05
    return 0.85


@dataclass
class PolicyEvent:
    ts: datetime
    source: str
    event_type: str
    impact: float
    confidence: float


DEFAULT_POLICY_SOURCE_WEIGHTS: Dict[str, float] = {
    "federalreserve": 1.0,
    "ecb": 0.9,
    "bankofengland": 0.85,
    "sec": 0.8,
    "cftc": 0.95,
    "unknown": 0.6,
}


@dataclass
class EventRow:
    chain: str
    pair: str
    ts: datetime
    pnl: float
    gas: float
    spread_bps: float
    efficiency: float
    executed: bool
    reason_code: str


@dataclass
class CausalPoint:
    row: EventRow
    crypto_momentum: float
    crypto_vol: float
    macro_momentum: float
    macro_vol: float
    macro_dispersion: float
    policy_event_shock: float
    session_weight: float
    hpi: float
    mti: float
    psi: float
    causal_pressure: float
    qutrit_pressure: float
    qutrit_confidence: float


def load_policy_events(path: str) -> List[PolicyEvent]:
    if not path:
        return []

    rows = load_jsonl(Path(path))
    out: List[PolicyEvent] = []
    for row in rows:
        ts_raw = str(row.get("timestamp_utc", "")).strip()
        if not ts_raw:
            continue
        source = str(row.get("source", "unknown")).strip() or "unknown"
        event_type = str(row.get("event_type", "unknown")).strip() or "unknown"
        impact = clamp(float(row.get("impact", 0.0) or 0.0), -1.0, 1.0)
        conf = clamp(float(row.get("confidence", 0.5) or 0.5), 0.0, 1.0)

        try:
            ts = parse_iso(ts_raw)
        except ValueError:
            continue

        out.append(PolicyEvent(ts=ts, source=source, event_type=event_type, impact=impact, confidence=conf))

    out.sort(key=lambda e: e.ts)
    return out


def load_policy_source_weights(path: str) -> Dict[str, float]:
    if not path:
        return dict(DEFAULT_POLICY_SOURCE_WEIGHTS)

    payload: Dict[str, Any]
    raw = path.strip()
    if raw.startswith("{"):
        try:
            payload = cast(Dict[str, Any], json.loads(raw))
        except json.JSONDecodeError:
            return dict(DEFAULT_POLICY_SOURCE_WEIGHTS)
    else:
        file_path = Path(raw)
        if not file_path.exists():
            return dict(DEFAULT_POLICY_SOURCE_WEIGHTS)
        try:
            payload = cast(Dict[str, Any], json.loads(file_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            return dict(DEFAULT_POLICY_SOURCE_WEIGHTS)

    out = dict(DEFAULT_POLICY_SOURCE_WEIGHTS)
    for k, v in payload.items():
        if not isinstance(v, int | float):
            continue
        out[k.strip().lower()] = clamp(float(v), 0.0, 3.0)
    return out


def load_policy_reliability_multipliers(path: str) -> Dict[str, float]:
    file_path = Path(path.strip()) if path.strip() else Path("5-Applications/out/micro_cap_sim/policy_source_reliability.json")
    if not file_path.exists():
        return {}

    try:
        payload = cast(Dict[str, Any], json.loads(file_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return {}

    sources_raw = payload.get("sources", {})
    sources = cast(Dict[str, Any], sources_raw) if isinstance(sources_raw, dict) else {}

    multipliers: Dict[str, float] = {}
    for source, data_raw in sources.items():
        data = cast(Dict[str, Any], data_raw) if isinstance(data_raw, dict) else {}
        mult = float(data.get("ema_recommended_weight_multiplier", data.get("recommended_weight_multiplier", 1.0)) or 1.0)
        multipliers[source.strip().lower()] = clamp(mult, 0.25, 2.0)
    return multipliers


def build_effective_policy_source_weights(base: Dict[str, float], multipliers: Dict[str, float]) -> Dict[str, float]:
    keys = sorted(set(base.keys()) | set(multipliers.keys()))
    out: Dict[str, float] = {}
    for k in keys:
        b = float(base.get(k, base.get("unknown", 0.6)))
        m = float(multipliers.get(k, 1.0))
        out[k] = clamp(b * m, 0.0, 3.0)
    return out


def policy_shock_at(
    ts: datetime,
    events: List[PolicyEvent],
    lookback_hours: float,
    half_life_hours: float,
    source_weights: Dict[str, float],
) -> float:
    if not events:
        return 0.0
    if lookback_hours <= 0 or half_life_hours <= 0:
        return 0.0

    shock = 0.0
    for ev in events:
        age_hours = abs((ts - ev.ts).total_seconds()) / 3600.0
        if age_hours > lookback_hours:
            continue
        decay = 0.5 ** (age_hours / half_life_hours)
        weight = source_weights.get(ev.source.lower(), source_weights.get("unknown", 0.6))
        shock += ev.impact * ev.confidence * weight * decay

    return clamp(shock, -2.0, 2.0)


def build_events(post_rows: List[Dict[str, Any]], chain_rows: List[Dict[str, Any]]) -> List[EventRow]:
    out: List[EventRow] = []
    for row in post_rows:
        strategy_id = str(row.get("strategy_id", ""))
        chain, pair = parse_strategy(strategy_id)
        if chain == "unknown":
            continue

        ts = parse_iso(str(row.get("timestamp_utc", "1970-01-01T00:00:00+00:00")))
        impact = extract_impact(row)
        pnl = float(impact.get("pnl_usd", 0.0) or 0.0)
        gas = float(impact.get("gas_usd", 0.0) or 0.0)
        efficiency = pnl / gas if gas > 0.0 else 0.0
        outcome = str(row.get("outcome", "")).upper()

        nearest = nearest_row(chain_rows, chain, pair, ts)
        spread_bps = float(nearest.get("spread_bps", impact.get("slippage_bps", 0.0)) if nearest else impact.get("slippage_bps", 0.0) or 0.0)

        out.append(
            EventRow(
                chain=chain,
                pair=pair,
                ts=ts,
                pnl=pnl,
                gas=gas,
                spread_bps=spread_bps,
                efficiency=efficiency,
                executed=(outcome == "EXECUTED"),
                reason_code=str(row.get("reason_code", "")),
            )
        )

    out.sort(key=lambda e: e.ts)
    return out


def rolling_execution_sentiment(events: List[EventRow], idx: int, window: int = 8) -> float:
    start = max(0, idx - window + 1)
    subset = events[start : idx + 1]
    if not subset:
        return 0.0
    exec_rate = sum(1.0 for e in subset if e.executed) / len(subset)
    eff = safe_fmean([e.efficiency for e in subset])
    return clamp((exec_rate - 0.5) * 1.4 + (eff * 2.5))


def build_causal_points(
    events: List[EventRow],
    global_series: Dict[str, List[Tuple[datetime, float]]],
    macro_series: Dict[str, Dict[str, List[Tuple[datetime, float]]]],
    policy_events: List[PolicyEvent],
    policy_source_weights: Dict[str, float],
    psi_lookback_hours: float,
    psi_half_life_hours: float,
) -> List[CausalPoint]:
    focus_symbols = ["BTC/USDC", "ETH/USDC", "SOL/USDC", "BNB/USDC", "MATIC/USDC", "AVAX/USDC"]
    macro_focus = {
        "equity": ["^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225", "000300.SS"],
        "rates": ["^TNX", "^FVX", "^IRX", "^TYX"],
        "commodity": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F"],
        "fx": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCNY=X"],
    }

    points: List[CausalPoint] = []
    for i, event in enumerate(events):
        ts = event.ts

        crypto_states: List[Dict[str, float]] = []
        for sym in focus_symbols:
            st = state_from_series(global_series.get(sym, []), ts)
            if st["price"] > 0.0:
                crypto_states.append(st)

        crypto_momentum = safe_fmean([s["momentum"] for s in crypto_states])
        crypto_vol = safe_fmean([s["vol"] for s in crypto_states])

        mstate = market_state_at(macro_series, ts, macro_focus)
        macro_momentum = float(mstate["momentum"])
        macro_vol = float(mstate["vol"])
        macro_dispersion = float(mstate["dispersion"])
        event_shock = policy_shock_at(
            ts,
            policy_events,
            lookback_hours=psi_lookback_hours,
            half_life_hours=psi_half_life_hours,
            source_weights=policy_source_weights,
        )

        s_weight = session_weight(ts)
        sentiment = rolling_execution_sentiment(events, i, window=8)

        hpi_raw = (0.55 * crypto_momentum) + (0.35 * sentiment) - (0.15 * crypto_vol)
        hpi = clamp(hpi_raw * 8.0)

        mti_raw = (0.70 * macro_momentum) - (0.45 * macro_vol) - (0.25 * macro_dispersion)
        mti = clamp(mti_raw * 12.0)

        psi_raw = (0.65 * macro_vol) + (0.35 * macro_dispersion) - (0.20 * macro_momentum) + (0.90 * event_shock)
        psi = clamp(psi_raw * 10.0)

        causal_pressure = s_weight * ((0.55 * hpi) + (0.65 * mti) - (0.80 * psi))
        qutrit_pressure, qutrit_confidence = compute_qutrit_pressure(hpi, mti, psi, s_weight)

        points.append(
            CausalPoint(
                row=event,
                crypto_momentum=crypto_momentum,
                crypto_vol=crypto_vol,
                macro_momentum=macro_momentum,
                macro_vol=macro_vol,
                macro_dispersion=macro_dispersion,
                policy_event_shock=event_shock,
                session_weight=s_weight,
                hpi=hpi,
                mti=mti,
                psi=psi,
                causal_pressure=causal_pressure,
                qutrit_pressure=qutrit_pressure,
                qutrit_confidence=qutrit_confidence,
            )
        )

    return points


def future_mean_eff(points: List[CausalPoint], idx: int, horizon: int) -> float:
    nxt = points[idx + 1 : idx + 1 + horizon]
    if not nxt:
        return 0.0
    return safe_fmean([p.row.efficiency for p in nxt])


def optimize_lag_on_subset(subset: List[CausalPoint], horizon: int, lag_min: int, lag_max: int) -> Dict[str, Any]:
    if len(subset) < max(8, horizon + 2):
        return {"best_lag": 0, "best_corr": 0.0, "sample_count": len(subset)}

    best_lag = 0
    best_corr = 0.0

    for lag in range(lag_min, lag_max + 1):
        x: List[float] = []
        y: List[float] = []
        for i in range(len(subset)):
            j = i + lag
            if j < 0 or j >= len(subset):
                continue
            target = future_mean_eff(subset, i, horizon=horizon)
            x.append(subset[j].causal_pressure)
            y.append(target)

        corr = pearson(x, y)
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag

    return {"best_lag": best_lag, "best_corr": round(best_corr, 8), "sample_count": len(subset)}


def optimize_lag_for_chain(points: List[CausalPoint], chain: str, horizon: int, lag_min: int, lag_max: int) -> Dict[str, Any]:
    subset = [p for p in points if p.row.chain == chain]
    return optimize_lag_on_subset(subset=subset, horizon=horizon, lag_min=lag_min, lag_max=lag_max)


def shifted_pressure(subset: List[CausalPoint], idx: int, lag: int) -> float:
    j = idx + lag
    if j < 0 or j >= len(subset):
        return 0.0
    return subset[j].causal_pressure


def confidence_from_signal(causal_pressure: float, lag_corr: float, horizon: int) -> float:
    base = abs(causal_pressure) * 0.30 + abs(lag_corr) * 0.55 + (1.0 / max(1, horizon)) * 0.15
    return clamp(base, 0.0, 1.0)


def backtest_chain(subset: List[CausalPoint], lag: int, lag_corr: float, horizon: int) -> Dict[str, Any]:
    reactive_hits = 0
    predictive_hits = 0
    qutrit_hits = 0
    reactive_trades = 0
    predictive_trades = 0
    qutrit_trades = 0
    reactive_pnl = 0.0
    predictive_pnl = 0.0
    qutrit_pnl = 0.0

    preds: List[Dict[str, Any]] = []

    for i, p in enumerate(subset):
        target = future_mean_eff(subset, i, horizon=horizon)
        reactive_signal = p.crypto_momentum - p.crypto_vol
        predictive_signal = shifted_pressure(subset, i, lag)

        reactive_side = sign(reactive_signal)
        predictive_side = sign(predictive_signal)
        target_side = sign(target)

        reactive_correct = reactive_side != 0 and reactive_side == target_side
        predictive_correct = predictive_side != 0 and predictive_side == target_side

        if reactive_side != 0:
            reactive_trades += 1
            if reactive_correct:
                reactive_hits += 1
            reactive_pnl += reactive_side * target

        if predictive_side != 0:
            predictive_trades += 1
            if predictive_correct:
                predictive_hits += 1
            predictive_pnl += predictive_side * target

        qutrit_side = sign(p.qutrit_pressure)
        qutrit_correct = qutrit_side != 0 and qutrit_side == target_side
        if qutrit_side != 0:
            qutrit_trades += 1
            if qutrit_correct:
                qutrit_hits += 1
            qutrit_pnl += qutrit_side * target

        expected_delta_pressure = predictive_signal
        conf = confidence_from_signal(expected_delta_pressure, lag_corr=lag_corr, horizon=horizon)

        preds.append(
            {
                "timestamp_utc": p.row.ts.replace(microsecond=0).isoformat(),
                "pair": p.row.pair,
                "hpi": round(p.hpi, 8),
                "mti": round(p.mti, 8),
                "psi": round(p.psi, 8),
                "policy_event_shock": round(p.policy_event_shock, 8),
                "session_weight": round(p.session_weight, 8),
                "expected_delta_pressure_horizon": round(expected_delta_pressure, 8),
                "confidence": round(conf, 8),
                "reactive_signal": round(reactive_signal, 8),
                "future_target_efficiency": round(target, 8),
                "predictive_correct": predictive_correct,
                "qutrit_pressure": round(p.qutrit_pressure, 8),
                "qutrit_confidence": round(p.qutrit_confidence, 8),
                "qutrit_correct": qutrit_correct,
            }
        )

    return {
        "predictions": preds,
        "reactive": {
            "trades": reactive_trades,
            "hit_rate": round((reactive_hits / reactive_trades), 8) if reactive_trades > 0 else 0.0,
            "simulated_alpha": round(reactive_pnl, 8),
        },
        "predictive": {
            "trades": predictive_trades,
            "hit_rate": round((predictive_hits / predictive_trades), 8) if predictive_trades > 0 else 0.0,
            "simulated_alpha": round(predictive_pnl, 8),
        },
        "qutrit": {
            "trades": qutrit_trades,
            "hit_rate": round((qutrit_hits / qutrit_trades), 8) if qutrit_trades > 0 else 0.0,
            "simulated_alpha": round(qutrit_pnl, 8),
        },
    }


def calibration_curve(predictions: List[Dict[str, Any]], bins: int) -> List[Dict[str, Any]]:
    bucket_count = max(2, bins)
    sums: Dict[int, Dict[str, float]] = {}

    for p in predictions:
        conf = float(p.get("confidence", 0.0) or 0.0)
        correct = 1.0 if bool(p.get("predictive_correct", False)) else 0.0
        idx = min(bucket_count - 1, int(conf * bucket_count))

        state = sums.setdefault(idx, {"n": 0.0, "conf": 0.0, "acc": 0.0})
        state["n"] += 1.0
        state["conf"] += conf
        state["acc"] += correct

    curve: List[Dict[str, Any]] = []
    for i in range(bucket_count):
        lo = i / bucket_count
        hi = (i + 1) / bucket_count
        st = sums.get(i, {"n": 0.0, "conf": 0.0, "acc": 0.0})
        n = int(st["n"])
        avg_conf = (st["conf"] / st["n"]) if st["n"] > 0 else 0.0
        emp_acc = (st["acc"] / st["n"]) if st["n"] > 0 else 0.0
        curve.append(
            {
                "bin": i,
                "confidence_range": [round(lo, 6), round(hi, 6)],
                "count": n,
                "avg_confidence": round(avg_conf, 8),
                "empirical_accuracy": round(emp_acc, 8),
                "calibration_gap": round(avg_conf - emp_acc, 8),
            }
        )
    return curve


def walk_forward_backtest_chain(
    subset: List[CausalPoint],
    horizon: int,
    lag_min: int,
    lag_max: int,
    train_size: int,
    test_size: int,
) -> Dict[str, Any]:
    if len(subset) < max(train_size + test_size, horizon + 6):
        return {
            "windows": [],
            "summary": {
                "window_count": 0,
                "predictive_hit_rate": 0.0,
                "reactive_hit_rate": 0.0,
                "predictive_alpha": 0.0,
                "reactive_alpha": 0.0,
                "alpha_lift": 0.0,
            },
        }

    windows: List[Dict[str, Any]] = []
    total_pred_trades = 0
    total_react_trades = 0
    weighted_pred_hit = 0.0
    weighted_react_hit = 0.0
    total_pred_alpha = 0.0
    total_react_alpha = 0.0

    start = train_size
    while start < len(subset) - horizon:
        train = subset[start - train_size : start]
        test = subset[start : min(len(subset), start + test_size)]
        if len(test) < max(2, horizon):
            break

        lag_info = optimize_lag_on_subset(train, horizon=horizon, lag_min=lag_min, lag_max=lag_max)
        bt = backtest_chain(test, lag=int(lag_info["best_lag"]), lag_corr=float(lag_info["best_corr"]), horizon=horizon)

        pred = cast(Dict[str, Any], bt.get("predictive", {}))
        react = cast(Dict[str, Any], bt.get("reactive", {}))
        pred_trades = int(pred.get("trades", 0) or 0)
        react_trades = int(react.get("trades", 0) or 0)
        pred_hit = float(pred.get("hit_rate", 0.0) or 0.0)
        react_hit = float(react.get("hit_rate", 0.0) or 0.0)
        pred_alpha = float(pred.get("simulated_alpha", 0.0) or 0.0)
        react_alpha = float(react.get("simulated_alpha", 0.0) or 0.0)

        total_pred_trades += pred_trades
        total_react_trades += react_trades
        weighted_pred_hit += pred_hit * pred_trades
        weighted_react_hit += react_hit * react_trades
        total_pred_alpha += pred_alpha
        total_react_alpha += react_alpha

        windows.append(
            {
                "train_start_utc": train[0].row.ts.replace(microsecond=0).isoformat(),
                "train_end_utc": train[-1].row.ts.replace(microsecond=0).isoformat(),
                "test_start_utc": test[0].row.ts.replace(microsecond=0).isoformat(),
                "test_end_utc": test[-1].row.ts.replace(microsecond=0).isoformat(),
                "lag": lag_info["best_lag"],
                "lag_corr": lag_info["best_corr"],
                "predictive_hit_rate": round(pred_hit, 8),
                "reactive_hit_rate": round(react_hit, 8),
                "predictive_alpha": round(pred_alpha, 8),
                "reactive_alpha": round(react_alpha, 8),
                "alpha_lift": round(pred_alpha - react_alpha, 8),
            }
        )

        start += test_size

    pred_hit_rate = (weighted_pred_hit / total_pred_trades) if total_pred_trades > 0 else 0.0
    react_hit_rate = (weighted_react_hit / total_react_trades) if total_react_trades > 0 else 0.0

    return {
        "windows": windows,
        "summary": {
            "window_count": len(windows),
            "predictive_hit_rate": round(pred_hit_rate, 8),
            "reactive_hit_rate": round(react_hit_rate, 8),
            "predictive_alpha": round(total_pred_alpha, 8),
            "reactive_alpha": round(total_react_alpha, 8),
            "alpha_lift": round(total_pred_alpha - total_react_alpha, 8),
        },
    }


def auto_manifest_pipeline(out_json: Path, manifest_dir: Path, chunk_size: int) -> Dict[str, Any]:
    manifest_script = Path(__file__).with_name("file_manifest_builder.py")
    manifest_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = manifest_dir / f"{out_json.stem}.manifest.json"
    rebuilt_path = manifest_dir / f"{out_json.stem}.rebuilt{out_json.suffix}"
    chunk_store = manifest_dir / "chunk_store"

    build_cmd = [
        sys.executable,
        str(manifest_script),
        "build",
        "--input",
        str(out_json),
        "--manifest-out",
        str(manifest_path),
        "--chunk-size-bytes",
        str(max(1, chunk_size)),
        "--chunk-store",
        str(chunk_store),
    ]
    verify_cmd = [
        sys.executable,
        str(manifest_script),
        "verify",
        "--manifest",
        str(manifest_path),
        "--file",
        str(out_json),
    ]
    rebuild_cmd = [
        sys.executable,
        str(manifest_script),
        "rebuild",
        "--manifest",
        str(manifest_path),
        "--chunk-store",
        str(chunk_store),
        "--out-file",
        str(rebuilt_path),
    ]

    build_run = subprocess.run(build_cmd, check=False, capture_output=True, text=True)
    verify_run = subprocess.run(verify_cmd, check=False, capture_output=True, text=True)
    rebuild_run = subprocess.run(rebuild_cmd, check=False, capture_output=True, text=True)

    return {
        "manifest": str(manifest_path),
        "rebuilt": str(rebuilt_path),
        "chunk_store": str(chunk_store),
        "build_exit_code": build_run.returncode,
        "verify_exit_code": verify_run.returncode,
        "rebuild_exit_code": rebuild_run.returncode,
        "build_stdout": build_run.stdout.strip(),
        "verify_stdout": verify_run.stdout.strip(),
        "rebuild_stdout": rebuild_run.stdout.strip(),
    }


def export_calibration_curves_csv(calibration: Dict[str, List[Dict[str, Any]]], out_dir: Path) -> List[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[str] = []

    for chain, rows in calibration.items():
        fp = out_dir / f"{chain}_calibration_curve.csv"
        with fp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["chain", "bin", "confidence_lo", "confidence_hi", "count", "avg_confidence", "empirical_accuracy", "calibration_gap"])
            for row in rows:
                conf_range_raw = row.get("confidence_range", [0.0, 0.0])
                conf_range = cast(List[Any], conf_range_raw) if isinstance(conf_range_raw, list) else [0.0, 0.0]
                lo = float(conf_range[0]) if len(conf_range) >= 1 and isinstance(conf_range[0], int | float) else 0.0
                hi = float(conf_range[1]) if len(conf_range) >= 2 and isinstance(conf_range[1], int | float) else 0.0
                writer.writerow(
                    [
                        chain,
                        int(row.get("bin", 0) or 0),
                        lo,
                        hi,
                        int(row.get("count", 0) or 0),
                        float(row.get("avg_confidence", 0.0) or 0.0),
                        float(row.get("empirical_accuracy", 0.0) or 0.0),
                        float(row.get("calibration_gap", 0.0) or 0.0),
                    ]
                )
        paths.append(str(fp))

    return sorted(paths)


def build_report(
    post_rows: List[Dict[str, Any]],
    chain_rows: List[Dict[str, Any]],
    macro_rows: Optional[List[Dict[str, Any]]],
    policy_events: List[PolicyEvent],
    policy_source_weights: Dict[str, float],
    horizon: int,
    lag_min: int,
    lag_max: int,
    psi_lookback_hours: float,
    psi_half_life_hours: float,
    walk_forward_train_size: int,
    walk_forward_test_size: int,
    calibration_bins: int,
    base_policy_source_weights: Dict[str, float],
    policy_reliability_multipliers: Dict[str, float],
) -> Dict[str, Any]:
    events = build_events(post_rows, chain_rows)
    global_series = build_global_series(chain_rows)
    macro_series = build_macro_series(macro_rows or [])
    points = build_causal_points(
        events=events,
        global_series=global_series,
        macro_series=macro_series,
        policy_events=policy_events,
        policy_source_weights=policy_source_weights,
        psi_lookback_hours=psi_lookback_hours,
        psi_half_life_hours=psi_half_life_hours,
    )

    chains = sorted(set(p.row.chain for p in points))
    lag_table: Dict[str, Dict[str, Any]] = {}
    chain_backtests: Dict[str, Dict[str, Any]] = {}
    chain_walk_forward: Dict[str, Dict[str, Any]] = {}
    confidence_calibration: Dict[str, List[Dict[str, Any]]] = {}

    hpi_all: List[float] = []
    mti_all: List[float] = []
    psi_all: List[float] = []
    pressure_all: List[float] = []
    qutrit_pressure_all: List[float] = []
    eff_all: List[float] = []

    for chain in chains:
        chain_points = [p for p in points if p.row.chain == chain]
        lag_info = optimize_lag_for_chain(points, chain, horizon=horizon, lag_min=lag_min, lag_max=lag_max)
        lag_table[chain] = lag_info

        bt = backtest_chain(
            chain_points,
            lag=int(lag_info["best_lag"]),
            lag_corr=float(lag_info["best_corr"]),
            horizon=horizon,
        )
        chain_backtests[chain] = bt

        predictions_raw = bt.get("predictions", [])
        predictions = cast(List[Dict[str, Any]], predictions_raw) if isinstance(predictions_raw, list) else []
        confidence_calibration[chain] = calibration_curve(predictions, bins=calibration_bins)

        chain_walk_forward[chain] = walk_forward_backtest_chain(
            chain_points,
            horizon=horizon,
            lag_min=lag_min,
            lag_max=lag_max,
            train_size=max(6, walk_forward_train_size),
            test_size=max(2, walk_forward_test_size),
        )

        for cp in chain_points:
            hpi_all.append(cp.hpi)
            mti_all.append(cp.mti)
            psi_all.append(cp.psi)
            pressure_all.append(cp.causal_pressure)
            qutrit_pressure_all.append(cp.qutrit_pressure)
            eff_all.append(cp.row.efficiency)

    corr = {
        "eff_vs_hpi": round(pearson(eff_all, hpi_all), 8),
        "eff_vs_mti": round(pearson(eff_all, mti_all), 8),
        "eff_vs_psi": round(pearson(eff_all, psi_all), 8),
        "eff_vs_pressure": round(pearson(eff_all, pressure_all), 8),
        "eff_vs_qutrit_pressure": round(pearson(eff_all, qutrit_pressure_all), 8),
    }

    leaderboard: List[Dict[str, Any]] = []
    for chain in chains:
        bt = chain_backtests[chain]
        pr = cast(Dict[str, Any], bt.get("predictive", {}))
        re = cast(Dict[str, Any], bt.get("reactive", {}))
        qt = cast(Dict[str, Any], bt.get("qutrit", {}))
        wf_summary = cast(Dict[str, Any], chain_walk_forward[chain].get("summary", {}))
        wf_lift = float(wf_summary.get("alpha_lift", 0.0) or 0.0)

        leaderboard.append(
            {
                "chain": chain,
                "lag": lag_table[chain]["best_lag"],
                "lag_corr": lag_table[chain]["best_corr"],
                "predictive_hit_rate": pr.get("hit_rate", 0.0),
                "reactive_hit_rate": re.get("hit_rate", 0.0),
                "qutrit_hit_rate": qt.get("hit_rate", 0.0),
                "predictive_alpha": pr.get("simulated_alpha", 0.0),
                "reactive_alpha": re.get("simulated_alpha", 0.0),
                "qutrit_alpha": qt.get("simulated_alpha", 0.0),
                "alpha_lift": round(float(pr.get("simulated_alpha", 0.0)) - float(re.get("simulated_alpha", 0.0)), 8),
                "qutrit_lift": round(float(qt.get("simulated_alpha", 0.0)) - float(re.get("simulated_alpha", 0.0)), 8),
                "walk_forward_alpha_lift": round(wf_lift, 8),
            }
        )

    leaderboard.sort(key=lambda r: float(r["walk_forward_alpha_lift"]), reverse=True)

    return {
        "summary": {
            "events": len(points),
            "chains": len(chains),
            "macro_rows_used": len(macro_rows or []),
            "policy_events_used": len(policy_events),
            "prediction_horizon_steps": horizon,
            "lag_search": {"min": lag_min, "max": lag_max},
            "psi_event_model": {
                "lookback_hours": psi_lookback_hours,
                "half_life_hours": psi_half_life_hours,
                "source_weights": policy_source_weights,
                "base_source_weights": base_policy_source_weights,
                "reliability_multipliers": policy_reliability_multipliers,
            },
            "walk_forward": {
                "train_size": walk_forward_train_size,
                "test_size": walk_forward_test_size,
            },
            "calibration_bins": calibration_bins,
            "correlations": corr,
            "objective": "causal-first HPI/MTI/PSI pressure forecasting with evidence-aware PSI, lag optimization, walk-forward backtesting, and calibrated confidence",
        },
        "lag_optimizer": lag_table,
        "chain_backtests": chain_backtests,
        "chain_walk_forward": chain_walk_forward,
        "confidence_calibration": confidence_calibration,
        "predictive_leaderboard": leaderboard,
    }


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    summary = cast(Dict[str, Any], payload.get("summary", {}))
    corr = cast(Dict[str, Any], summary.get("correlations", {}))

    lines.append("# Hyperfluid Causal Pressure Report")
    lines.append("")
    lines.append("Causal-first model with HPI (human pressure), MTI (market transmission), PSI (policy shock), session weighting, rolling lag optimization, walk-forward backtesting, and confidence calibration.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- events: {summary.get('events', 0)}")
    lines.append(f"- chains: {summary.get('chains', 0)}")
    lines.append(f"- macro_rows_used: {summary.get('macro_rows_used', 0)}")
    lines.append(f"- policy_events_used: {summary.get('policy_events_used', 0)}")
    lines.append(f"- prediction_horizon_steps: {summary.get('prediction_horizon_steps', 0)}")
    lines.append("")
    lines.append("## Correlations")
    lines.append("")
    lines.append(f"- eff_vs_hpi: {corr.get('eff_vs_hpi', 0)}")
    lines.append(f"- eff_vs_mti: {corr.get('eff_vs_mti', 0)}")
    lines.append(f"- eff_vs_psi: {corr.get('eff_vs_psi', 0)}")
    lines.append(f"- eff_vs_pressure: {corr.get('eff_vs_pressure', 0)}")
    lines.append("")

    lines.append("## Predictive Leaderboard")
    lines.append("")
    lines.append("| Chain | Lag | Lag Corr | Predictive Hit | Reactive Hit | Predictive Alpha | Reactive Alpha | Walk-Forward Lift |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in payload.get("predictive_leaderboard", []):
        lines.append(
            "| {chain} | {lag} | {lag_corr} | {predictive_hit_rate} | {reactive_hit_rate} | {predictive_alpha} | {reactive_alpha} | {walk_forward_alpha_lift} |".format(
                chain=row.get("chain", ""),
                lag=row.get("lag", 0),
                lag_corr=row.get("lag_corr", 0.0),
                predictive_hit_rate=row.get("predictive_hit_rate", 0.0),
                reactive_hit_rate=row.get("reactive_hit_rate", 0.0),
                predictive_alpha=row.get("predictive_alpha", 0.0),
                reactive_alpha=row.get("reactive_alpha", 0.0),
                walk_forward_alpha_lift=row.get("walk_forward_alpha_lift", 0.0),
            )
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Causal-first hyperfluid model with evidence-aware PSI ingestion, walk-forward backtesting, confidence calibration, and auto-manifest outputs.")
    parser.add_argument("--post-records", required=True, help="Path to post_records.jsonl")
    parser.add_argument("--chain-records", required=True, help="Path to chain_records.jsonl")
    parser.add_argument("--macro-records", required=False, default="", help="Optional path to macro_records.jsonl")
    parser.add_argument("--policy-events", required=False, default="", help="Optional path to policy_events.jsonl")
    parser.add_argument("--policy-source-weights", required=False, default="", help="Optional JSON file path or inline JSON for source trust weights used in PSI event shock.")
    parser.add_argument("--policy-reliability", required=False, default="5-Applications/out/micro_cap_sim/policy_source_reliability.json", help="Optional reliability JSON path from policy collector to auto-adjust source weights.")
    parser.add_argument("--horizon-steps", type=int, default=3, help="Prediction horizon in steps.")
    parser.add_argument("--lag-min", type=int, default=-6, help="Minimum lag (steps).")
    parser.add_argument("--lag-max", type=int, default=6, help="Maximum lag (steps).")
    parser.add_argument("--psi-lookback-hours", type=float, default=72.0, help="Policy-event lookback horizon for PSI event shock.")
    parser.add_argument("--psi-half-life-hours", type=float, default=18.0, help="Half-life for policy-event decay in PSI event shock.")
    parser.add_argument("--walk-forward-train-size", type=int, default=18, help="Walk-forward rolling training window size (events per chain).")
    parser.add_argument("--walk-forward-test-size", type=int, default=6, help="Walk-forward rolling test window size (events per chain).")
    parser.add_argument("--calibration-bins", type=int, default=10, help="Confidence calibration bin count.")
    parser.add_argument("--calibration-csv-dir", default="5-Applications/out/micro_cap_sim/calibration_curves", help="Directory to export per-chain calibration curve CSV files.")
    parser.add_argument("--export-calibration-csv", dest="export_calibration_csv", action="store_true", help="Export calibration curves to CSV files for dashboards.")
    parser.add_argument("--no-export-calibration-csv", dest="export_calibration_csv", action="store_false", help="Disable calibration CSV export.")
    parser.set_defaults(export_calibration_csv=True)
    parser.add_argument("--auto-manifest", dest="auto_manifest", action="store_true", help="Automatically build/verify/rebuild report manifests after run.")
    parser.add_argument("--no-auto-manifest", dest="auto_manifest", action="store_false", help="Disable automatic manifest pipeline.")
    parser.set_defaults(auto_manifest=True)
    parser.add_argument("--manifest-dir", default="5-Applications/out/manifests", help="Manifest output directory (used when auto-manifest is enabled).")
    parser.add_argument("--manifest-chunk-size-bytes", type=int, default=65536, help="Chunk size for manifest chunk-store generation.")
    parser.add_argument("--out-json", required=True, help="Output report JSON path")
    parser.add_argument("--out-md", required=True, help="Output report markdown path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    post_rows = load_jsonl(Path(args.post_records))
    chain_rows = load_jsonl(Path(args.chain_records))
    macro_rows = load_jsonl(Path(args.macro_records)) if args.macro_records else []
    policy_events = load_policy_events(args.policy_events)
    base_policy_source_weights = load_policy_source_weights(args.policy_source_weights)
    policy_reliability_multipliers = load_policy_reliability_multipliers(args.policy_reliability)
    policy_source_weights = build_effective_policy_source_weights(base_policy_source_weights, policy_reliability_multipliers)

    if not post_rows or not chain_rows:
        print(json.dumps({"error": "missing_input_data", "post_records": len(post_rows), "chain_records": len(chain_rows)}, indent=2))
        return 2

    payload = build_report(
        post_rows=post_rows,
        chain_rows=chain_rows,
        macro_rows=macro_rows,
        policy_events=policy_events,
        policy_source_weights=policy_source_weights,
        horizon=max(1, int(args.horizon_steps)),
        lag_min=int(args.lag_min),
        lag_max=int(args.lag_max),
        psi_lookback_hours=max(1.0, float(args.psi_lookback_hours)),
        psi_half_life_hours=max(0.1, float(args.psi_half_life_hours)),
        walk_forward_train_size=max(6, int(args.walk_forward_train_size)),
        walk_forward_test_size=max(2, int(args.walk_forward_test_size)),
        calibration_bins=max(2, int(args.calibration_bins)),
        base_policy_source_weights=base_policy_source_weights,
        policy_reliability_multipliers=policy_reliability_multipliers,
    )

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    write_markdown(Path(args.out_md), payload)

    if bool(args.export_calibration_csv):
        csv_paths = export_calibration_curves_csv(
            cast(Dict[str, List[Dict[str, Any]]], payload.get("confidence_calibration", {})),
            out_dir=Path(args.calibration_csv_dir),
        )
        payload["summary"]["calibration_csv_export"] = {
            "enabled": True,
            "dir": str(Path(args.calibration_csv_dir)),
            "files": csv_paths,
        }
        out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        payload["summary"]["calibration_csv_export"] = {"enabled": False}
        out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    manifest_result: Dict[str, Any] = {}
    if bool(args.auto_manifest):
        manifest_result = auto_manifest_pipeline(
            out_json=out_json,
            manifest_dir=Path(args.manifest_dir),
            chunk_size=int(args.manifest_chunk_size_bytes),
        )
        payload["summary"]["manifest_pipeline"] = {
            "enabled": True,
            "manifest": manifest_result.get("manifest", ""),
            "rebuilt": manifest_result.get("rebuilt", ""),
            "build_exit_code": manifest_result.get("build_exit_code", -1),
            "verify_exit_code": manifest_result.get("verify_exit_code", -1),
            "rebuild_exit_code": manifest_result.get("rebuild_exit_code", -1),
        }
        out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        payload["summary"]["manifest_pipeline"] = {"enabled": False}
        out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    top_raw = payload.get("predictive_leaderboard", [])
    top = cast(List[Dict[str, Any]], top_raw) if isinstance(top_raw, list) else []
    top_row: Optional[Dict[str, Any]] = top[0] if top else None

    print(
        json.dumps(
            {
                "events": payload["summary"]["events"],
                "policy_events_used": payload["summary"]["policy_events_used"],
                "top_chain": top_row,
                "manifest_pipeline": payload["summary"].get("manifest_pipeline", {}),
                "calibration_csv_export": payload["summary"].get("calibration_csv_export", {}),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
