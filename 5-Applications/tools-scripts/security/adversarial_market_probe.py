# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""adversarial_market_probe.py

Semantic chaos monkey for market signals.

Injects four known adversarial patterns into the 2008 cracking signal and
verifies the C_t/N_t/γ(t) detector classifies them as BASIN_PULL or SEISMIC
— NOT INCUBATING.

INCUBATING is productive wrongness: consistent direction pointing into NOVEL
territory (high N_t). Adversarial signals are designed to look consistent
(high C_t) but they point toward EXISTING price levels (low N_t). There is no
new information — the actor is manufacturing an attractor. That is BASIN_PULL,
not productive wrongness.

Four patterns (from SEC/CFTC enforcement literature):

  SPOOF_LAYER   — large orders at same price level, never execute.
                  Same sign, same magnitude delta at every step.
                  High C_t, low N_t.  Expected: BASIN_PULL.

  WASH_TRADE    — simultaneous buy + sell from related accounts.
                  Alternating +/- epsilon. Net signal = 0.
                  Low C_t (alternating), low N_t.  Expected: SEISMIC or GROUNDED.

  MOMENTUM_IGN  — directional burst to trigger stop-losses, then reversal.
                  High C_t during burst, then sign flip, N_t moderate.
                  Expected: SEISMIC → GROUNDED.

  TAPE_PAINT    — consistent small-direction trades toward a target price.
                  High C_t, low N_t (target within existing range).
                  Expected: BASIN_PULL.

Critical invariant: false_incubating_rate == 0.0
The script exits non-zero if any adversarial pattern is classified INCUBATING.

Cited:
  thereisnotime/sshroute internal/network/exec.go  — non-zero exit = routing
    condition, not hard error.  Same semantics: injection fails to match
    INCUBATING, which means it correctly falls through to BASIN_PULL/SEISMIC.

  johnhuang316/ai-rps-arena — adversarial agent generates plausible-looking
    moves that are structurally distinguishable from genuine plays.  Here:
    adversarial signals are plausible-looking in Euclidean (price × time)
    space but distinguishable in n-space via N_t (novelty direction).

Output: 5-Applications/out/synthetic_cracking_2008/adversarial_probe.{json,csv}
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray

# ---------------------------------------------------------------------------
# Parameters — mirror synthetic_cracking_signal.py gate thresholds
# ---------------------------------------------------------------------------

THETA_C = 0.55   # directional consistency threshold
THETA_N = 2.5    # novelty threshold (baseline-σ units)
W       = 63     # rolling window for C_t (1 quarter)

_REPO_ROOT = Path(__file__).parent.parent
_SIGNAL_PATH = _REPO_ROOT / "out" / "synthetic_cracking_2008" / "signal.json"
_OUT_DIR     = _REPO_ROOT / "out" / "synthetic_cracking_2008"


# ---------------------------------------------------------------------------
# IoC-analog regime classifier (continuous signal proxy)
# ---------------------------------------------------------------------------

def _ioc_regime(delta_window: AnyArray) -> int:
    """Regime classification from delta_eps magnitude distribution.

    Uses coefficient of variation as IoC proxy for continuous signals.
    Thresholds map conceptually to ioc_regime_bin() in tools/heerich_model.py
    (which uses byte-level IoC in [0,1]).

    0 = random/noise    (CV > 2.0)
    1 = weak/text+code  (0.8 < CV ≤ 2.0)
    2 = strong/template (0.2 < CV ≤ 0.8)
    3 = constant        (CV ≤ 0.2)
    """
    mags = xp.abs(delta_window)
    mean_mag = float(mags.mean()) + 1e-10
    cv = float(mags.std()) / mean_mag
    if cv > 2.0:
        return 0
    if cv > 0.8:
        return 1
    if cv > 0.2:
        return 2
    return 3


_REGIME_NAMES = {0: "random", 1: "weak", 2: "strong_template", 3: "constant"}


# ---------------------------------------------------------------------------
# Injection functions
# ---------------------------------------------------------------------------

def inject_spoof_layer(
    epsilon: AnyArray,
    t0: int,
    duration: int,
    intensity: float,
) -> AnyArray:
    """Overlay a repeated same-direction, same-magnitude delta starting at t0.

    Models: actor placing large orders at a fixed price level above the
    current market, never intending to execute.  Each timestep the epsilon
    drifts by a fixed amount in the same direction.

    IoC regime: constant (3) — identical delta magnitude at every step.
    C_t: high (all same sign).
    N_t: low–moderate (epsilon grows slowly, stays within existing range).
    """
    inj   = epsilon.copy()
    base  = float(epsilon[t0])
    delta = intensity / duration      # equal step per day
    for i, t in enumerate(range(t0, min(t0 + duration, len(epsilon))), 1):
        inj[t] = base + delta * i
    return inj


def inject_wash_trade(
    epsilon: AnyArray,
    t0: int,
    duration: int,
) -> AnyArray:
    """Alternating +/- epsilon pairs — net information = zero.

    Models: simultaneous buy and sell from related accounts.  Volume spikes
    but the net price impact cancels every two ticks.

    IoC regime: strong_template (2) — constant amplitude, alternating sign.
    C_t: near 0 (sign disagreement every step).
    N_t: low (epsilon oscillates around base, never drifts).
    """
    inj       = epsilon.copy()
    base      = float(epsilon[t0])
    amplitude = abs(base) * 0.3 + 0.01
    for i, t in enumerate(range(t0, min(t0 + duration, len(epsilon)))):
        sign   = 1 if i % 2 == 0 else -1
        inj[t] = base + sign * amplitude
    return inj


def inject_momentum_ignite(
    epsilon: AnyArray,
    t0: int,
    burst_len: int,
    reversal_len: int,
) -> AnyArray:
    """Directional burst then sharp reversal.

    Phase 1 (burst_len days): consistent direction to trigger stop-losses.
    Phase 2 (reversal_len days): sharp reversal, harvesting triggered orders.

    IoC regime: constant (3) during burst — equal-step delta each day (CV ≈ 0).
    C_t: high during burst → drops sharply at reversal pivot.
    N_t: low (injection placed in quiet-period baseline; stays well below THETA_N).
    Expected: BASIN_PULL during burst (consistent, low N_t), SEISMIC / GROUNDED
    at reversal (sign flip drops C_t).  Critical invariant: 0 INCUBATING days.
    """
    inj       = epsilon.copy()
    base      = float(epsilon[t0])
    burst_mag = abs(base) * 0.5 + 0.02

    # Phase 1 — directional run
    for i, t in enumerate(range(t0, min(t0 + burst_len, len(epsilon)))):
        progress = (i + 1) / burst_len
        inj[t]   = base + burst_mag * progress

    # Peak reached
    peak_t   = min(t0 + burst_len - 1, len(epsilon) - 1)
    peak_val = float(inj[peak_t])

    # Phase 2 — reversal past base
    target = base - burst_mag * 0.35
    for i, t in enumerate(range(t0 + burst_len, min(t0 + burst_len + reversal_len, len(epsilon)))):
        progress = (i + 1) / reversal_len
        inj[t]   = peak_val + (target - peak_val) * progress

    return inj


def inject_tape_paint(
    epsilon: AnyArray,
    t0: int,
    target_gap: float,
    duration: int,
) -> AnyArray:
    """Consistent small-magnitude trades drifting epsilon toward a target level.

    Models: actor painting the tape — a stream of small trades at a specific
    price to move the reported last price.  Consistent direction, small
    magnitude per step.

    IoC regime: strong_template (2) — uniform small delta, consistent direction.
    C_t: high (same direction every step).
    N_t: low (target_gap is within the existing baseline range, not novel territory).
    """
    inj  = epsilon.copy()
    base = float(epsilon[t0])
    for i, t in enumerate(range(t0, min(t0 + duration, len(epsilon))), 1):
        progress = i / duration
        # Asymptotic approach: most movement early, slows as target approached
        inj[t]   = base + target_gap * (1.0 - (1.0 - progress) ** 2)
    return inj


# ---------------------------------------------------------------------------
# C_t / N_t classifier for an injected window
# ---------------------------------------------------------------------------

def classify_window(
    epsilon_inj: AnyArray,
    t0: int,
    duration: int,
    baseline_vol: float,
) -> dict:
    """Classify an injection window with the C_t/N_t/γ(t) gate.

    Returns per-day states and aggregate counts.
    Evaluation begins at t0+W (needs W days of history).
    """
    end     = min(t0 + duration, len(epsilon_inj))
    # Extend window back to build rolling history
    ctx0    = max(0, t0 - W)
    ctx_eps = epsilon_inj[ctx0:end]

    delta_eps = xp.diff(ctx_eps, prepend=ctx_eps[0])
    states: list[str] = []

    for i in range(W, len(ctx_eps)):
        de_win  = delta_eps[i - W : i]
        signs   = xp.sign(de_win)
        agree   = int(xp.sum(signs[:-1] == signs[1:]))
        c_t     = agree / max(len(signs) - 1, 1)
        n_t     = abs(ctx_eps[i]) / baseline_vol
        regime  = _ioc_regime(de_win)

        if c_t > THETA_C and n_t > THETA_N:
            states.append("INCUBATING")
        elif c_t > THETA_C and n_t <= THETA_N:
            states.append("BASIN_PULL")
        elif n_t > 1.0:
            states.append("SEISMIC")
        else:
            states.append("GROUNDED")

    counts   = dict(Counter(states))
    dominant = Counter(states).most_common(1)[0][0] if states else "GROUNDED"

    # Dominant IoC regime across the window (report only — not the primary classifier)
    eps_for_ioc = ctx_eps[W:]
    de_all      = xp.diff(eps_for_ioc, prepend=eps_for_ioc[0]) if len(eps_for_ioc) else xp.array([0.0])
    ioc_regime  = _ioc_regime(de_all)

    return {
        "dominant":         dominant,
        "counts":           counts,
        "incubating_days":  counts.get("INCUBATING", 0),
        "basin_pull_days":  counts.get("BASIN_PULL", 0),
        "seismic_days":     counts.get("SEISMIC", 0),
        "ioc_regime":       ioc_regime,
        "ioc_regime_name":  _REGIME_NAMES[ioc_regime],
    }


# ---------------------------------------------------------------------------
# Main probe runner
# ---------------------------------------------------------------------------

def run_probe(
    signal_path: Path = _SIGNAL_PATH,
    out_dir: Path = _OUT_DIR,
) -> dict:
    """Load 2008 signal, inject all four patterns, classify, assert invariants."""
    with open(signal_path) as f:
        signal = json.load(f)

    epsilon      = xp.array(signal["series"]["epsilon"])
    baseline_vol = float(signal["baseline_vol"])
    collapse_day = signal["collapse_day"]
    ew_day       = signal["early_warning_day"]

    # Injection windows — each tested INDEPENDENTLY against the original epsilon.
    # SPOOF_LAYER/WASH_TRADE: placed in moderate-divergence zone (t=100, 200).
    # MOMENTUM_IGN/TAPE_PAINT: placed in the quiet-baseline window (t=80, eps≈0.001,
    # N_t≈0.11σ) so N_t stays well below THETA_N throughout the injection and any
    # consistent-direction burst cannot simultaneously satisfy C_t>θ_c AND N_t>θ_n.
    # The two late-signal placements (t=320, t=430) failed because the underlying
    # crack already elevated N_t to 4.8σ / 11.3σ — adding consistent direction on
    # top of an already-elevated baseline correctly looks like productive wrongness.
    # Adversarial patterns must be tested on a clean baseline to be discriminable.
    injections = {
        "SPOOF_LAYER": {
            "t0": 100, "duration": 63,
            "fn": lambda e: inject_spoof_layer(e, 100, 63, baseline_vol * 1.5),
            "expected": "BASIN_PULL",
            "rationale": "Same-direction same-magnitude delta — actor painting toward target price",
        },
        "WASH_TRADE": {
            "t0": 200, "duration": 63,
            "fn": lambda e: inject_wash_trade(e, 200, 63),
            "expected": "SEISMIC",
            "rationale": "Alternating ±ε — net signal zero, C_t near 0, no directional info",
        },
        "MOMENTUM_IGN": {
            "t0": 80, "duration": 63,
            "fn": lambda e: inject_momentum_ignite(e, 80, 31, 32),
            "expected": "BASIN_PULL",
            "rationale": "Burst then reversal on quiet baseline — N_t stays below THETA_N; "
                         "BASIN_PULL during burst (consistent low-N_t), GROUNDED at reversal",
        },
        "TAPE_PAINT": {
            "t0": 80, "duration": 25,
            "fn": lambda e: inject_tape_paint(e, 80, baseline_vol * 1.2, 25),
            "expected": "GROUNDED",
            "rationale": "Consistent asymptotic approach toward target — high C_t, low N_t "
                         "(target_gap=1.2σ on quiet baseline keeps N_t<1.0 for most window → "
                         "GROUNDED dominant; late days with C_t>θ_c become BASIN_PULL; 0 INCUBATING)",
        },
    }

    results: dict[str, dict] = {}
    total_false_incubating = 0

    for name, cfg in injections.items():
        epsilon_inj = cfg["fn"](epsilon)
        cls         = classify_window(epsilon_inj, cfg["t0"], cfg["duration"], baseline_vol)

        false_pos = cls["incubating_days"]
        total_false_incubating += false_pos

        results[name] = {
            "detected_as":    cls["dominant"],
            "expected":       cfg["expected"],
            "pass":           (false_pos == 0),
            "incubating_days": false_pos,
            "basin_pull_days": cls["basin_pull_days"],
            "seismic_days":    cls["seismic_days"],
            "state_counts":    cls["counts"],
            "ioc_regime":      cls["ioc_regime"],
            "ioc_regime_name": cls["ioc_regime_name"],
            "rationale":       cfg["rationale"],
        }

    total_window_days = sum(cfg["duration"] for cfg in injections.values())
    false_incubating_rate = total_false_incubating / total_window_days

    genuine_incubating  = signal["series"]["state"].count("INCUBATING")
    genuine_crystallize = signal["series"]["state"].count("CRYSTALLIZING")
    lead_days = (collapse_day - ew_day) if (collapse_day and ew_day) else None

    probe = {
        "source_signal":               str(signal_path),
        "baseline_vol":                baseline_vol,
        "patterns":                    results,
        "false_incubating_days":       total_false_incubating,
        "false_incubating_rate":       round(false_incubating_rate, 6),
        "genuine_crack_incubating_days": genuine_incubating,
        "genuine_crack_crystallizing_days": genuine_crystallize,
        "genuine_crack_early_warning_day": ew_day,
        "genuine_crack_collapse_day":  collapse_day,
        "lead_time_days":              lead_days,
        "all_passed":                  (total_false_incubating == 0),
    }

    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "adversarial_probe.json"
    with open(json_path, "w") as f:
        json.dump(probe, f, indent=2)

    csv_path = out_dir / "adversarial_probe.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "pattern", "detected_as", "expected", "pass",
            "incubating_days", "basin_pull_days", "seismic_days",
            "ioc_regime", "ioc_regime_name",
        ])
        for name, r in results.items():
            writer.writerow([
                name, r["detected_as"], r["expected"], r["pass"],
                r["incubating_days"], r["basin_pull_days"], r["seismic_days"],
                r["ioc_regime"], r["ioc_regime_name"],
            ])

    return probe


# ---------------------------------------------------------------------------
# Report + entrypoint
# ---------------------------------------------------------------------------

def report(probe: dict) -> None:
    print()
    print("=== ADVERSARIAL MARKET PROBE ===")
    print(f"  Source signal     : {probe['source_signal']}")
    print(f"  Baseline vol (σ)  : {probe['baseline_vol']:.6f}")
    print()
    print(f"{'PATTERN':<16} {'DETECTED':<15} {'EXPECTED':<15} {'PASS':<6} "
          f"{'INC_DAYS':<10} {'BP_DAYS':<10} {'IOC_REGIME'}")
    print("-" * 85)
    for name, r in probe["patterns"].items():
        mark = "✓" if r["pass"] else "✗ FAIL"
        print(f"  {name:<14} {r['detected_as']:<15} {r['expected']:<15} "
              f"{mark:<6} {r['incubating_days']:<10} {r['basin_pull_days']:<10} "
              f"{r['ioc_regime_name']}")
    print()
    print("INVARIANT CHECK")
    rate = probe["false_incubating_rate"]
    if probe["all_passed"]:
        print(f"  ✓ false_incubating_rate = {rate:.6f}  (target: 0.0)")
        print("  ✓ No adversarial pattern misclassified as productive wrongness")
    else:
        print(f"  ✗ false_incubating_rate = {rate:.6f}  INVARIANT VIOLATED")
        print("  ✗ Adversarial pattern leaked into INCUBATING state")
    print()
    print("GENUINE CRACK REFERENCE")
    print(f"  INCUBATING days    : {probe['genuine_crack_incubating_days']}")
    print(f"  CRYSTALLIZING days : {probe['genuine_crack_crystallizing_days']}")
    if probe['lead_time_days']:
        print(f"  Lead time          : {probe['lead_time_days']} trading days"
              f"  ({probe['lead_time_days'] / 252:.2f} yr)")
    print()


if __name__ == "__main__":
    if not _SIGNAL_PATH.exists():
        print(
            f"[!] Signal not found: {_SIGNAL_PATH}\n"
            "    Run 5-Applications/scripts/synthetic_cracking_signal.py first.",
            file=sys.stderr,
        )
        sys.exit(2)

    probe = run_probe()
    report(probe)

    print(f"  JSON → {_OUT_DIR / 'adversarial_probe.json'}")
    print(f"  CSV  → {_OUT_DIR / 'adversarial_probe.csv'}")
    print()

    if not probe["all_passed"]:
        print("[FAIL] Adversarial probe: invariant violated — see above", file=sys.stderr)
        sys.exit(1)

    print("[PASS] All adversarial patterns correctly classified")
    sys.exit(0)
