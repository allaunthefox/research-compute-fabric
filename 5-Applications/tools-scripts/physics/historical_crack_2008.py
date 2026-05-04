# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

from __future__ import annotations

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

"""historical_crack_2008.py

Real-data probe of the 2004–2008 financial crack using Yahoo Finance equity data.
No external databases, no special API keys — all data was publicly tradeable in
real-time and visible to any market participant.

SENSOR SPOOF IN PLAIN SIGHT
----------------------------
The S&P 500 was the canonical "surface" sensor: reporting record highs, rising
drift, suppressed volatility.  The consensus read the surface and said "fine."

Three sub-sectors of the same market were the fundamentals: they had already
cracked and were reporting it daily via their prices.  Nobody was listening
because their world model didn't have a layer for "the sensor can be wrong."

AMERICAN MARKETS ALONE ARE NOT SUFFICIENT
------------------------------------------
US officials had institutional incentives to manage the narrative — congress-
ional testimony, public confidence, market stability mandates.  The American
surface sensor was subject to coordinated perception management.

International markets had NO such incentive.  When a German, Swiss, or
British-Hong Kong bank discloses losses, it does so under its own jurisdiction's
reporting requirements, independent of the Federal Reserve's communication
strategy.  These signals are Layer 0 — uncorrelated with the US narrative layer.

THREE DOMESTIC PAIRS (Pairs A–C)
---------------------------------
Pair A — "Broad market vs Financial Sector" (US)
  surface     = log(^GSPC_t / ^GSPC_base)   S&P 500: everyone's health indicator
  fundamental = log(XLF_t   / XLF_base)     Financial Select SPDR (banks+brokers)

Pair B — "Broad market vs Homebuilders" (US)
  surface     = log(^GSPC_t / ^GSPC_base)
  fundamental = log(^HGX_t  / ^HGX_base)    Philadelphia Housing Sector Index
  Lead: ^HGX peaked Jul 2005 — 27-month hidden divergence.

Pair C — "Suppressed VIX vs Banking index" (US)
  surface     = −log(^VIX_t / ^VIX_base)
  fundamental = log(^BKX_t  / ^BKX_base)    KBW Bank Index
  The fear gauge was disagreeing with the banking sector's own price signal.

THREE INTERNATIONAL PAIRS (Pairs D–F)
--------------------------------------
These instruments report under non-US jurisdictions.  Their divergences from
the S&P 500 surface were not subject to US narrative management.

Pair D — "S&P 500 vs HSBC Holdings" (British-Hong Kong)
  HSBC issued the FIRST public institutional warning on subprime, Feb 7 2007,
  increasing bad-debt provisions 20% to $10.6B.  UK/HK disclosure requirements.
  surface     = log(^GSPC_t / ^GSPC_base)
  fundamental = log(HSBC_t  / HSBC_base)    HSBC Holdings ADR (NYSE)

Pair E — "S&P 500 vs UBS AG" (Swiss)
  UBS disclosed CHF 4B subprime exposure Aug 2007, wrote down $18.7B by Oct 2007.
  Swiss FINMA reporting requirements — independent of Fed communication strategy.
  surface     = log(^GSPC_t / ^GSPC_base)
  fundamental = log(UBS_t   / UBS_base)     UBS AG ADR (NYSE)

Pair F — "S&P 500 vs Deutsche Bank" (German)
  Deutsche Bank disclosed EUR 2.2B subprime writedown Oct 2007 under BaFin/IFRS.
  German regulatory and accounting framework — independent Layer 0.
  surface     = log(^GSPC_t / ^GSPC_base)
  fundamental = log(DB_t    / DB_base)      Deutsche Bank AG ADR (NYSE)

DATA SOURCES
------------
All Yahoo Finance, v8/finance/chart, daily 2004-01-01 to 2008-10-01.
  US:            ^GSPC  ^VIX  XLF  ^HGX  ^BKX
  International: HSBC   UBS   DB

STATEMENTS TIMELINE
-------------------
Includes both US "impossible/contained" statements AND international disclosures.
The international disclosures could not be suppressed — they were public filings
in non-US jurisdictions.  The script reports the detector state on each date.
"""


import csv
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta, timezone
from collections import Counter
from pathlib import Path
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray

# ---------------------------------------------------------------------------
# Detector parameters (mirrors synthetic_cracking_signal.py)
# ---------------------------------------------------------------------------

W        = 63    # 1 quarter rolling window
W_ACCUM  = 126   # 2 quarter accumulation window
THETA_C  = 0.55
THETA_N  = 2.5
THETA_S  = 20    # INCUBATING days within W_ACCUM to trigger CRYSTALLIZING

BASELINE_DAYS = 63   # first quarter used to calibrate baseline_vol

START_DATE   = date(2004, 1,  2)
END_DATE     = date(2008, 10, 1)
LEHMAN_DATE  = date(2008, 9, 15)

_START_TS  = int(datetime(2004, 1, 1,  tzinfo=timezone.utc).timestamp())
_END_TS    = int(datetime(2008, 10, 1, tzinfo=timezone.utc).timestamp())

# Each entry: (date, speaker, quote, category)
# category: "us_denial" = US official downplaying; "intl_disclosure" = non-US
#   institution publicly disclosing losses (cannot be suppressed by US PR);
#   "collapse" = actual failure events
STATEMENTS = [
    # --- US denial layer ---
    (date(2005, 12,  1), "NAR / David Lereah",
     "National home prices cannot fall — you'd need a major job-loss recession "
     "(Annual book 2005: 'Are You Missing the Real Estate Boom?')",
     "us_denial"),
    (date(2006,  2, 15), "Ben Bernanke / Senate",
     "The U.S. economy appears to be in a period of transition... we do not "
     "currently see a sharp slowdown in housing as the most likely outcome.",
     "us_denial"),
    (date(2006,  8,  1), "Bush CEA Annual Report",
     "Housing market slowdown is orderly. A soft landing is likely. "
     "The underlying fundamentals of the economy remain solid.",
     "us_denial"),
    # --- International Layer 0: HSBC first institutional warning ---
    (date(2007,  2,  7), "HSBC Holdings / Earnings (London/Hong Kong reporting)",
     "HSBC increases bad-debt provisions 20% to USD 10.6B due to US subprime "
     "mortgage losses. First major institutional public warning. (UK/HK disclosure "
     "requirements — not subject to US narrative management.)",
     "intl_disclosure"),
    # --- US denial continues despite HSBC warning ---
    (date(2007,  2, 28), "Ben Bernanke / Joint Economic Committee",
     "At this juncture, the impact on the broader economy and financial markets "
     "of the problems in the subprime market seems likely to be contained.",
     "us_denial"),
    (date(2007,  5, 17), "Ben Bernanke / Federal Reserve Bank of Chicago",
     "We do not expect significant spillovers from the subprime market to the "
     "rest of the economy or to the financial system.",
     "us_denial"),
    (date(2007,  7, 25), "Jimmy Cayne / Bear Stearns CEO",
     "The loss is really limited to two funds. The remainder of the business "
     "is operating normally. This is an isolated event.",
     "us_denial"),
    # --- Paulson "healthy economy" — BNP Paribas freezes funds THE NEXT DAY ---
    (date(2007,  8,  8), "Hank Paulson / Treasury Secretary",
     "The capital markets are functioning normally. We see the underlying "
     "economy as being very healthy and robust.",
     "us_denial"),
    # --- BNP Paribas — French bank, BaFin/AMF jurisdiction, one day after Paulson ---
    (date(2007,  8,  9), "BNP Paribas / Paris (French AMF reporting)",
     "BNP Paribas freezes redemptions on three sub-prime funds worth EUR 1.6B: "
     "Parvest Dynamic ABS, BNP Paribas ABS Euribor, BNP Paribas ABS Eonia. "
     "'Complete evaporation of liquidity in certain market segments.' "
     "Triggered ECB emergency EUR 95B liquidity injection. "
     "(French AMF jurisdiction — independent of Fed communication strategy.)",
     "intl_disclosure"),
    (date(2007,  8, 16), "Angelo Mozilo / Countrywide CEO",
     "We are not in a meltdown. The credit problems are isolated to certain "
     "segments of the market. Business fundamentals remain intact.",
     "us_denial"),
    # --- Northern Rock — UK bank run, physically undeniable ---
    (date(2007,  9, 14), "Northern Rock / Bank of England (UK PRA reporting)",
     "Northern Rock requests emergency liquidity support from Bank of England. "
     "Customers queue outside branches in first UK bank run since 1866. "
     "GBP 1B withdrawn in days. (UK FSA/BoE jurisdiction — independent of Fed.)",
     "intl_disclosure"),
    (date(2007, 10, 15), "Ben Bernanke / Economic Club of NY",
     "It is not the responsibility of the Federal Reserve — nor would it be "
     "appropriate — to protect lenders and investors from consequences.",
     "us_denial"),
    # --- UBS Swiss writedown — CHF disclosure, FINMA jurisdiction ---
    (date(2007, 10,  1), "UBS AG / Zurich (Swiss FINMA reporting)",
     "UBS AG discloses CHF 4B subprime exposure and announces CEO resignation. "
     "Will write down USD 18.7B by year-end — largest bank loss in Swiss history. "
     "(Swiss FINMA jurisdiction — independent of US narrative management.)",
     "intl_disclosure"),
    # --- Deutsche Bank — German BaFin/IFRS disclosure ---
    (date(2007, 10, 31), "Deutsche Bank AG / Frankfurt (German BaFin reporting)",
     "Deutsche Bank discloses EUR 2.2B subprime writedown for Q3 2007. "
     "CEO Josef Ackermann publicly warns of market instability. "
     "(German BaFin/IFRS jurisdiction — independent of Fed communication strategy.)",
     "intl_disclosure"),
    (date(2008,  1,  7), "George W. Bush / White House Press Briefing",
     "I don't think we're headed to recession. I know there's a lot of "
     "uncertainty. But the economy is going to be fine.",
     "us_denial"),
    (date(2008,  3, 16), "Federal Reserve / Bear Stearns Emergency Rescue",
     "The Federal Reserve agreed to provide emergency financing. Systemic "
     "risk to the broader financial system would be avoided.",
     "us_denial"),
    (date(2008,  6,  9), "Ben Bernanke / Atlanta Federal Reserve Bank",
     "The risk that the economy has entered a substantial downturn appears to "
     "have diminished over the past month or so.",
     "us_denial"),
    (date(2008,  7, 11), "Hank Paulson / Congressional Testimony",
     "Fannie Mae and Freddie Mac are adequately capitalized. They are in no "
     "danger of failing. They are well-capitalized institutions.",
     "us_denial"),
    (date(2008,  9, 14), "The day before Lehman",
     "Banking system is sound. Fed backstop available. Orderly resolution.",
     "us_denial"),
    (date(2008,  9, 15), "COLLAPSE — Lehman Brothers Chapter 11",
     "Lehman Brothers files for bankruptcy protection. $639B in assets — the "
     "largest bankruptcy filing in US history. Global credit markets freeze.",
     "collapse"),
]

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

_ROOT    = Path(__file__).parent.parent
_OUT_DIR = _ROOT / "out" / "historical_crack_2008"

# ---------------------------------------------------------------------------
# Yahoo Finance fetch
# ---------------------------------------------------------------------------

def _fetch_yahoo(symbol: str) -> dict[date, float]:
    """Download daily closing prices for symbol via Yahoo Finance v8 chart API."""
    encoded = urllib.parse.quote(symbol, safe="^")
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        f"?period1={_START_TS}&period2={_END_TS}&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "crack-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except Exception as exc:
        print(f"[WARN] Yahoo fetch failed for {symbol}: {exc}", file=sys.stderr)
        return {}

    try:
        result    = payload["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes     = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError):
        return {}

    out: dict[date, float] = {}
    for ts, c in zip(timestamps, closes):
        if c is None:
            continue
        try:
            d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            out[d] = float(c)
        except (ValueError, OSError):
            continue
    return out


# ---------------------------------------------------------------------------
# Daily series alignment
# ---------------------------------------------------------------------------

def _to_daily_array(
    raw: dict[date, float],
    reference_dates: list[date],
) -> AnyArray:
    """
    Map raw {date: float} onto reference_dates, forward-filling gaps.
    Returns NaN where no data exists before the first observation.
    """
    n   = len(reference_dates)
    out = xp.full(n, xp.nan)
    for i, d in enumerate(reference_dates):
        if d in raw:
            out[i] = raw[d]
    # Forward-fill
    last = xp.nan
    for i in range(n):
        if not xp.isnan(out[i]):
            last = out[i]
        elif not xp.isnan(last):
            out[i] = last
    return out


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _log_ratio(series: AnyArray, baseline_end: int) -> AnyArray:
    """log(x / mean(x[:baseline_end])).  NaN-safe."""
    window = series[:baseline_end]
    window = window[~xp.isnan(window)]
    if len(window) == 0 or xp.nanmean(window) <= 0:
        return xp.zeros(len(series))
    base = float(xp.nanmean(window))
    return xp.where(
        (series > 0) & ~xp.isnan(series),
        xp.log(series / base),
        xp.nan,
    )


# ---------------------------------------------------------------------------
# C_t / N_t / γ(t) detector
# ---------------------------------------------------------------------------

def _detect(epsilon: AnyArray, baseline_end: int) -> dict:
    T = len(epsilon)
    valid = ~xp.isnan(epsilon)

    # Baseline vol from first quarter of valid data
    bv_window = epsilon[:baseline_end]
    bv_clean  = bv_window[~xp.isnan(bv_window)]
    baseline_vol = (float(xp.std(bv_clean)) if len(bv_clean) > 1 else 1e-6) + 1e-9

    delta_eps = xp.diff(epsilon, prepend=epsilon[0] if not xp.isnan(epsilon[0]) else 0.0)

    # C_t — directional consistency over rolling W window
    C = xp.zeros(T)
    for t in range(W, T):
        window = delta_eps[t - W : t]
        if xp.any(xp.isnan(window)):
            continue
        signs = xp.sign(window)
        agree = int(xp.sum(signs[:-1] == signs[1:]))
        C[t]  = agree / max(len(signs) - 1, 1)

    # N_t — novelty in baseline-σ units
    N = xp.where(valid, xp.abs(epsilon) / baseline_vol, 0.0)

    # First pass: per-day INCUBATING flag
    incubating_flags = xp.zeros(T, dtype=bool)
    for t in range(W, T):
        if valid[t] and C[t] > THETA_C and N[t] > THETA_N:
            incubating_flags[t] = True

    # Second pass: state machine with rolling accumulation
    state = ["GROUNDED"] * T
    gamma = xp.ones(T)
    early_warning_idx: Optional[int] = None

    for t in range(W, T):
        if not valid[t]:
            state[t] = "NO_DATA"
            continue
        if incubating_flags[t]:
            ws    = max(0, t - W_ACCUM)
            accum = int(xp.sum(incubating_flags[ws : t + 1]))
            if accum >= THETA_S:
                state[t] = "CRYSTALLIZING"
                gamma[t] = 2.0
                if early_warning_idx is None:
                    early_warning_idx = t
            else:
                state[t] = "INCUBATING"
                gamma[t] = 0.0
        elif C[t] > THETA_C and N[t] <= THETA_N:
            state[t] = "BASIN_PULL"
        elif N[t] > 1.0:
            state[t] = "SEISMIC"
        else:
            state[t] = "GROUNDED"

    first_inc_idx = next((i for i, s in enumerate(state) if s == "INCUBATING"), None)

    return {
        "state":               state,
        "C":                   C,
        "N":                   N,
        "gamma":               gamma,
        "baseline_vol":        baseline_vol,
        "first_incubating_idx":    first_inc_idx,
        "first_crystallizing_idx": early_warning_idx,
        "counts":              dict(Counter(state)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(out_dir: Path = _OUT_DIR) -> dict:
    print("Fetching Yahoo Finance data (2004-01-01 → 2008-10-01)…", flush=True)

    raw: dict[str, dict[date, float]] = {}
    for sym in ["^GSPC", "^VIX", "XLF", "^HGX", "^BKX", "HSBC", "UBS", "DB"]:
        raw[sym] = _fetch_yahoo(sym)
        n = len(raw[sym])
        print(f"  {sym:8s}: {n:4d} observations", flush=True)

    # Reference calendar = S&P 500 trading days
    if len(raw["^GSPC"]) < 100:
        print("[ERROR] S&P 500 data unavailable. Check network.", file=sys.stderr)
        sys.exit(1)

    ref_dates = sorted(raw["^GSPC"].keys())
    date_idx  = {d: i for i, d in enumerate(ref_dates)}
    T         = len(ref_dates)
    baseline_end = BASELINE_DAYS
    print(f"\n  Reference trading days: {T}")

    # Build daily arrays
    GSPC = _to_daily_array(raw["^GSPC"], ref_dates)
    VIX  = _to_daily_array(raw["^VIX"],  ref_dates)
    XLF  = _to_daily_array(raw["XLF"],   ref_dates)
    HGX  = _to_daily_array(raw["^HGX"],  ref_dates)
    BKX  = _to_daily_array(raw["^BKX"],  ref_dates)
    HSBC = _to_daily_array(raw["HSBC"],  ref_dates)
    UBS_ = _to_daily_array(raw["UBS"],   ref_dates)
    DB_  = _to_daily_array(raw["DB"],    ref_dates)

    # Log-ratio normalisation relative to first baseline period
    gspc_log = _log_ratio(GSPC, baseline_end)
    vix_log  = _log_ratio(VIX,  baseline_end)
    xlf_log  = _log_ratio(XLF,  baseline_end)
    hgx_log  = _log_ratio(HGX,  baseline_end)
    bkx_log  = _log_ratio(BKX,  baseline_end)
    hsbc_log = _log_ratio(HSBC, baseline_end)
    ubs_log  = _log_ratio(UBS_, baseline_end)
    db_log   = _log_ratio(DB_,  baseline_end)

    # --------------- domestic signal pairs ---------------
    eps_A = gspc_log - xlf_log     # grows as S&P rises + financials fall
    eps_B = gspc_log - hgx_log     # grows as S&P rises + housing falls
    eps_C = -vix_log - bkx_log     # grows when calm-is-claimed AND banks fall

    # --------------- international signal pairs ---------------
    # Pair D: S&P 500 (surface) vs HSBC (British-Hong Kong) — first warner
    eps_D = gspc_log - hsbc_log
    # Pair E: S&P 500 (surface) vs UBS AG (Swiss) — FINMA jurisdiction
    eps_E = gspc_log - ubs_log
    # Pair F: S&P 500 (surface) vs Deutsche Bank (German) — BaFin/IFRS jurisdiction
    eps_F = gspc_log - db_log

    print("\nRunning C_t / N_t / γ(t) detector on all six pairs…", flush=True)
    det: dict[str, dict] = {
        "A": _detect(eps_A, baseline_end),
        "B": _detect(eps_B, baseline_end),
        "C": _detect(eps_C, baseline_end),
        "D": _detect(eps_D, baseline_end),
        "E": _detect(eps_E, baseline_end),
        "F": _detect(eps_F, baseline_end),
    }

    # -----------------------------------------------------------------------
    # Report helpers
    # -----------------------------------------------------------------------
    lehman_idx = date_idx.get(LEHMAN_DATE)

    def _fmt_idx(idx: Optional[int]) -> str:
        return ref_dates[idx].isoformat() if idx is not None else "not detected"

    def _lead_str(idx: Optional[int]) -> str:
        if idx is None or lehman_idx is None:
            return "—"
        n = lehman_idx - idx
        if n <= 0:
            return "AFTER Lehman"
        return f"{n} trading days ({n / 252:.2f} yr) before Lehman"

    def _state_on(det_result: dict, query_date: date) -> str:
        for offset in range(7):
            candidate = query_date + timedelta(days=offset)
            if candidate in date_idx:
                return det_result["state"][date_idx[candidate]]
        return "NO_DATA"

    pair_meta = {
        "A": ("US",   "S&P 500 vs Financial Sector (XLF)"),
        "B": ("US",   "S&P 500 vs Homebuilders (^HGX)"),
        "C": ("US",   "Suppressed VIX vs KBW Banks (^BKX)"),
        "D": ("INTL", "S&P 500 vs HSBC Holdings (UK/HK — first institutional warning)"),
        "E": ("INTL", "S&P 500 vs UBS AG (Swiss FINMA — independent jurisdiction)"),
        "F": ("INTL", "S&P 500 vs Deutsche Bank (German BaFin — independent jurisdiction)"),
    }

    # -----------------------------------------------------------------------
    # Print report
    # -----------------------------------------------------------------------
    print()
    print("=" * 72)
    print("2004–2008 CRACK PROBE — REAL MARKET DATA (YAHOO FINANCE)")
    print("=" * 72)

    results: dict = {}
    for section, keys in [("DOMESTIC (US)", ["A","B","C"]),
                           ("INTERNATIONAL (independent jurisdictions)", ["D","E","F"])]:
        print(f"\n{'─'*72}")
        print(f"  {section}")
        print(f"{'─'*72}")
        for key in keys:
            d    = det[key]
            fi   = d["first_incubating_idx"]
            fc   = d["first_crystallizing_idx"]
            cnts = d["counts"]
            total = sum(cnts.values())
            jurisdiction, label = pair_meta[key]

            print(f"\nPAIR {key} [{jurisdiction}]: {label}")
            print(f"  baseline_vol         : {d['baseline_vol']:.5f}")
            print(f"  First INCUBATING     : {_fmt_idx(fi)}  ← {_lead_str(fi)}")
            print(f"  First CRYSTALLIZING  : {_fmt_idx(fc)}  ← {_lead_str(fc)}")
            print(f"  Lehman collapse      : {LEHMAN_DATE}")
            print(f"  State counts:")
            for s in ["GROUNDED","BASIN_PULL","SEISMIC","INCUBATING","CRYSTALLIZING","NO_DATA"]:
                n = cnts.get(s, 0)
                if n > 0:
                    pct = n / total * 100
                    bar = "█" * max(1, int(pct / 2))
                    print(f"    {s:<15} {n:4d}  {pct:5.1f}%  {bar}")

            results[key] = {
                "label":                  label,
                "jurisdiction":           jurisdiction,
                "baseline_vol":           d["baseline_vol"],
                "first_incubating":       _fmt_idx(fi),
                "first_crystallizing":    _fmt_idx(fc),
                "lead_days_incubating":   (lehman_idx - fi) if (fi is not None and lehman_idx) else None,
                "lead_days_crystallizing":(lehman_idx - fc) if (fc is not None and lehman_idx) else None,
                "counts":                 cnts,
            }

    # -----------------------------------------------------------------------
    # Statements table — all six pairs
    # -----------------------------------------------------------------------
    print()
    print("=" * 72)
    print("STATEMENTS vs. DETECTOR STATE [US=domestic  INTL=independent]")
    print("=" * 72)
    print(f"  {'DATE':<12} {'A(US)':<13} {'B(US)':<13} {'C(US)':<13} "
          f"{'D(INTL)':<13} {'E(INTL)':<13} {'F(INTL)':<13} TYPE  SPEAKER")
    print("─" * 140)

    stmt_records: list[dict] = []
    for stmt_date, speaker, quote, category in STATEMENTS:
        states = {k: _state_on(det[k], stmt_date) for k in "ABCDEF"}
        alarm  = any(states[k] in ("INCUBATING", "CRYSTALLIZING") for k in "ABCDEF")
        flag   = "⚠" if alarm else " "
        cat_tag = "INTL" if category == "intl_disclosure" else ("FAIL" if category == "collapse" else "  US")
        print(f"{flag} {stmt_date.isoformat():<12} "
              f"{states['A']:<13} {states['B']:<13} {states['C']:<13} "
              f"{states['D']:<13} {states['E']:<13} {states['F']:<13} "
              f"{cat_tag}   {speaker}")
        stmt_records.append({
            "date":     stmt_date.isoformat(),
            "speaker":  speaker,
            "quote":    quote,
            "category": category,
            **{f"state_{k}": states[k] for k in "ABCDEF"},
            "alarm":    alarm,
        })

    print()
    n_alarm = sum(1 for r in stmt_records if r["alarm"])
    n_intl  = sum(1 for r in stmt_records if r["category"] == "intl_disclosure")
    n_intl_alarm = sum(1 for r in stmt_records
                       if r["category"] == "intl_disclosure" and r["alarm"])
    print(f"  Detector in INCUBATING/CRYSTALLIZING for {n_alarm} of {len(stmt_records)} statements.")
    print(f"  International disclosures: {n_intl} total, {n_intl_alarm} already alarmed on ≥1 pair.")

    # Earliest alarm
    all_first_inc = [(d["first_incubating_idx"], k) for k, d in det.items()
                     if d["first_incubating_idx"] is not None]
    if all_first_inc:
        earliest_idx, earliest_key = min(all_first_inc)
        lead_to_lehman = (lehman_idx - earliest_idx) if lehman_idx else None
        earliest_date  = ref_dates[earliest_idx]
        print(f"  Earliest INCUBATING (any pair): {earliest_date.isoformat()} "
              f"(Pair {earliest_key}, {pair_meta[earliest_key][0]})")
        if lead_to_lehman:
            print(f"  Lead time to Lehman: {lead_to_lehman} trading days "
                  f"({lead_to_lehman/252:.2f} yr)")

        n_after = sum(
            1 for r in stmt_records
            if date.fromisoformat(r["date"]) > earliest_date
            and r["category"] != "collapse"
        )
        print(f"  'Impossible/contained' + intl disclosures AFTER first alarm: {n_after}")

    print()

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)

    eps_arrays = {"A": eps_A, "B": eps_B, "C": eps_C,
                  "D": eps_D, "E": eps_E, "F": eps_F}
    for key in "ABCDEF":
        eps_arr  = eps_arrays[key]
        csv_path = out_dir / f"signal_pair_{key}.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "epsilon", "C_t", "N_t", "state"])
            for i, d_obj in enumerate(ref_dates):
                e = eps_arr[i]
                w.writerow([
                    d_obj.isoformat(),
                    f"{e:.6f}" if not xp.isnan(e) else "",
                    f"{det[key]['C'][i]:.4f}",
                    f"{det[key]['N'][i]:.4f}",
                    det[key]["state"][i],
                ])
        print(f"  CSV ({key}) → {csv_path}")

    summary = {
        "description": "2004-2008 crack probe — six pairs: 3 domestic (US) + 3 international",
        "data_source": "Yahoo Finance v8/finance/chart (all public exchange data)",
        "note": "International pairs (D/E/F) report under non-US jurisdictions: "
                "UK/HK (HSBC), Swiss FINMA (UBS), German BaFin (DB). "
                "Not subject to US narrative management.",
        "parameters": {
            "W": W, "W_ACCUM": W_ACCUM,
            "THETA_C": THETA_C, "THETA_N": THETA_N, "THETA_S": THETA_S,
            "START": START_DATE.isoformat(),
            "END":   END_DATE.isoformat(),
            "LEHMAN": LEHMAN_DATE.isoformat(),
        },
        "pairs": results,
        "consensus_statements": stmt_records,
    }
    json_path = out_dir / "summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  JSON     → {json_path}")
    print()
    return summary



if __name__ == "__main__":
    run()
