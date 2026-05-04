# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""synthetic_cracking_signal.py

Generates a synthetic pre-2008-like market signal where the sensor reports
normal operation while the fundamental is cracking.

TWO-LAYER STRUCTURE
-------------------
Surface layer   — VIX-suppressed, slight positive drift, low volatility.
                  Models what participants and regulators were measuring.
                  Parameterized from S&P 500 2004-2007:
                    daily drift  ~+0.05%  (≈12% annualized)
                    daily vol    ~0.6%    (VIX ≈10-12, annualized ≈9.5%)

Fundamental layer — Slow consistent deterioration with accelerating drift.
                  Models underlying credit quality / delinquency accumulation.
                  Parameterized from ABX 2006-2 AAA + Case-Shiller HPI decay:
                    initial daily drift  -0.025%
                    drift acceleration   +0.3%/day (compounding)
                    daily vol            0.1%  (smooth, not noisy)

THE SENSOR SPOOF
----------------
The surface layer has weak coupling to the fundamental (λ=0.002).
This means it is very slowly being pulled toward reality, but the
lag is long enough that the gap widens for most of the signal lifetime.
The sensor (any agent measuring only the surface) reports "operating as
expected" during the entire INCUBATING phase.

DETECTION VIA PRODUCTIVE WRONGNESS GATE
-----------------------------------------
ε_t  = surface_t − fundamental_t            (scalar error, gap between layers)
C_t  = directional consistency of δε over a W-day rolling window  [0,1]
N_t  = |ε_t| / baseline_vol                 (novelty in baseline-σ units)

γ(t) correction gate:
  GROUNDED     — C_t ≤ θ_c  OR  N_t ≤ 1.0         → correct now
  SEISMIC      — C_t ≤ θ_c  AND  N_t > 1.0         → re-attest, random noise
  BASIN_PULL   — C_t > θ_c  AND  N_t ≤ θ_n         → correct now (spoof/manipulation signature)
  INCUBATING   — C_t > θ_c  AND  N_t > θ_n         → hold correction, accumulate
  CRYSTALLIZING — INCUBATING support ≥ θ_s OR collapse trigger → burst update

OPTIMALITY CLAIM
----------------
Long-term gain (F_j) from detecting the INCUBATING → CRYSTALLIZING transition
early exceeds short-term accumulated error during the INCUBATING window,
whenever the misrouting cost of treating productive wrongness as noise exceeds
the incubation cost.  Here: surface treated as ground truth for ~18 months
before collapse = the cost of NOT having the INCUBATING detector.

Output: 5-Applications/out/synthetic_cracking_2008/signal.{json,csv}
"""

import csv
import json
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray

# ---------------------------------------------------------------------------
# Parameters — calibrated to 2004-2007 S&P 500 / ABX / Case-Shiller ranges
# ---------------------------------------------------------------------------

SEED              = 2008
T                 = 756            # 3 trading years (252/yr)

# Surface (VIX-suppressed S&P analog)
# Calibrated to S&P 500 2004-2007: ~+13%/yr, VIX ≈10-12
MU_S              =  0.0003        # daily drift  (+7.6%/yr)
SIGMA_S           =  0.005         # daily vol    (VIX ≈10-12)
LAMBDA_NORMAL     =  0.002         # weak pull toward fundamental
LAMBDA_COLLAPSE   =  0.15          # fast pull after crack

# Fundamental (subprime / HPI crack analog)
# Calibrated to ABX 2006-2 AAA + Case-Shiller decay: slow start, accelerating
MU_F_INIT         = -0.00008       # initial daily drift (barely visible, -2%/yr)
DRIFT_ACCEL       =  1.0008        # daily multiplier — doubles in ~2.4 years
SIGMA_F           =  0.001         # smooth, low noise

# Detection window and thresholds
W                 = 63             # 1 quarter rolling window for C_t / N_t
W_ACCUM           = 126            # 2 quarter accumulation window for INCUBATING count
THETA_C           = 0.55           # directional consistency threshold
THETA_N           = 2.5            # novelty threshold (baseline-σ units)
THETA_S           = 20             # INCUBATING days within W_ACCUM to trigger CRYSTALLIZING

# Collapse trigger — gap at which surface mean-reverts hard
# Calibrated: actual 2007 S&P/credit-quality divergence ≈ 20-25%
COLLAPSE_GAP      = 0.22           # gap magnitude that forces rapid reversion


# ---------------------------------------------------------------------------
# Signal generation
# ---------------------------------------------------------------------------

def generate(seed: int = SEED) -> dict:
    rng = xp.random.default_rng(seed)

    surface      = xp.zeros(T)
    fundamental  = xp.zeros(T)
    surface[0]   = 0.0
    fundamental[0] = 0.0

    mu_f = MU_F_INIT
    collapsed    = False
    collapse_day = None

    for t in range(1, T):
        mu_f *= DRIFT_ACCEL
        gap   = surface[t - 1] - fundamental[t - 1]

        if not collapsed and abs(gap) >= COLLAPSE_GAP:
            collapsed    = True
            collapse_day = t

        lam = LAMBDA_COLLAPSE if collapsed else LAMBDA_NORMAL

        surface[t] = (
            surface[t - 1]
            + MU_S * (0.1 if collapsed else 1.0)   # drift dies at collapse
            + SIGMA_S * rng.standard_normal()
            - lam * gap
        )
        fundamental[t] = (
            fundamental[t - 1]
            + mu_f
            + SIGMA_F * rng.standard_normal()
        )

    # -----------------------------------------------------------------------
    # Error signal: gap between sensor (surface) and reality (fundamental)
    # -----------------------------------------------------------------------
    epsilon   = surface - fundamental
    delta_eps = xp.diff(epsilon, prepend=epsilon[0])

    # Baseline vol estimated from the first quarter (quiescent period)
    baseline_vol = float(xp.std(epsilon[:63])) + 1e-8

    # -----------------------------------------------------------------------
    # C_t — directional consistency of δε over rolling window W
    # For scalar signals: cos(a,b) = sign(a*b), so C_t = fraction of
    # consecutive delta pairs that agree in sign (trend persistence).
    # -----------------------------------------------------------------------
    C = xp.zeros(T)
    for t in range(W, T):
        window   = delta_eps[t - W : t]
        signs    = xp.sign(window)
        # fraction of consecutive pairs with same sign
        agree    = xp.sum(signs[:-1] == signs[1:])
        C[t]     = agree / max(len(signs) - 1, 1)

    # -----------------------------------------------------------------------
    # N_t — novelty: gap in baseline-σ units
    # -----------------------------------------------------------------------
    N = xp.abs(epsilon) / baseline_vol

    # -----------------------------------------------------------------------
    # γ(t) correction gate + state machine
    # Uses rolling W_ACCUM window to count INCUBATING days — productive
    # wrongness doesn't need to be consecutive to accumulate into a framework.
    # -----------------------------------------------------------------------
    state             = ['GROUNDED'] * T
    gamma             = xp.ones(T)
    incubating_flags  = xp.zeros(T, dtype=bool)   # per-day INCUBATING signal
    early_warning_day = None

    # First pass: classify each day independently
    for t in range(W, T):
        if C[t] > THETA_C and N[t] > THETA_N:
            incubating_flags[t] = True

    # Second pass: apply state machine with rolling accumulation
    for t in range(W, T):
        if collapsed and collapse_day is not None and t >= collapse_day:
            state[t]  = 'CRYSTALLIZING'
            gamma[t]  = 2.0
        elif incubating_flags[t]:
            # Count INCUBATING days in rolling W_ACCUM window
            window_start = max(0, t - W_ACCUM)
            accum = int(xp.sum(incubating_flags[window_start:t + 1]))
            if accum >= THETA_S:
                state[t]  = 'CRYSTALLIZING'
                gamma[t]  = 2.0
                if early_warning_day is None:
                    early_warning_day = t
            else:
                state[t]  = 'INCUBATING'
                gamma[t]  = 0.0        # hold correction
        elif C[t] > THETA_C and N[t] <= THETA_N:
            # BASIN_PULL: consistent direction BUT toward existing attractor (low novelty).
            # Spoof / manipulation signature — correct immediately against actuarial baseline,
            # not the spoofed current level. γ=η_base (not 0, not burst).
            state[t]  = 'BASIN_PULL'
            gamma[t]  = 1.0
        elif N[t] > 1.0:
            state[t]  = 'SEISMIC'
            gamma[t]  = 1.0
        else:
            state[t]  = 'GROUNDED'
            gamma[t]  = 1.0

    # -----------------------------------------------------------------------
    # Cost comparison: what the sensor-spoofed agent paid vs. gated agent
    # -----------------------------------------------------------------------
    # Naive: treats surface as ground truth, no correction held
    naive_cumulative_error = float(xp.cumsum(xp.abs(epsilon))[-1])

    # Gated: only accumulates error when γ > 0
    gated_error = xp.abs(epsilon) * (gamma > 0)
    gated_cumulative_error = float(xp.cumsum(gated_error)[-1])

    return {
        'params': {
            'seed': seed, 'T': T,
            'MU_S': MU_S, 'SIGMA_S': SIGMA_S,
            'LAMBDA_NORMAL': LAMBDA_NORMAL, 'LAMBDA_COLLAPSE': LAMBDA_COLLAPSE,
            'MU_F_INIT': MU_F_INIT, 'DRIFT_ACCEL': DRIFT_ACCEL, 'SIGMA_F': SIGMA_F,
            'W': W, 'W_ACCUM': W_ACCUM,
            'THETA_C': THETA_C, 'THETA_N': THETA_N, 'THETA_S': THETA_S,
            'COLLAPSE_GAP': COLLAPSE_GAP,
            'analog': '2004-2007 S&P500 surface / ABX-2006-2-AAA fundamental crack',
        },
        'collapse_day':       collapse_day,
        'early_warning_day':  early_warning_day,
        'baseline_vol':       baseline_vol,
        'naive_cumulative_error':  naive_cumulative_error,
        'gated_cumulative_error':  gated_cumulative_error,
        'series': {
            't':           list(range(T)),
            'surface':     surface.tolist(),
            'fundamental': fundamental.tolist(),
            'epsilon':     epsilon.tolist(),
            'C':           C.tolist(),
            'N':           N.tolist(),
            'gamma':       gamma.tolist(),
            'state':       state,
        },
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save(data: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON — full fidelity
    json_path = out_dir / 'signal.json'
    with open(json_path, 'w') as f:
        json.dump(data, f)

    # CSV — flat time series for EventCrossIndex / external tools
    csv_path = out_dir / 'signal.csv'
    s = data['series']
    rows = zip(s['t'], s['surface'], s['fundamental'],
               s['epsilon'], s['C'], s['N'], s['gamma'], s['state'])
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t', 'surface', 'fundamental', 'epsilon', 'C', 'N', 'gamma', 'state'])
        for row in rows:
            w.writerow([row[0]] + [f'{v:.6f}' if isinstance(v, float) else v
                                   for v in row[1:]])

    return json_path, csv_path


def report(data: dict) -> None:
    s         = data['series']
    states    = s['state']
    cd        = data['collapse_day']
    wd        = data['early_warning_day']
    T_        = data['params']['T']

    counts = {k: states.count(k) for k in ('GROUNDED', 'SEISMIC', 'BASIN_PULL', 'INCUBATING', 'CRYSTALLIZING')}

    pre_collapse = cd or T_
    lead_days    = (cd - wd) if (cd and wd) else None

    print()
    print('=== SYNTHETIC CRACKING SIGNAL — 2008 ANALOG ===')
    print(f'  T = {T_} days  ({T_/252:.1f} trading years)')
    print()
    print('PHASE TRANSITIONS')
    print(f'  First INCUBATING detection : day {min((i for i,s in enumerate(states) if s=="INCUBATING"), default="—")}')
    print(f'  First CRYSTALLIZING (early): day {wd}  ({f"{wd/252:.2f} yr" if wd else "—"})')
    print(f'  Hard collapse trigger      : day {cd}  ({f"{cd/252:.2f} yr" if cd else "—"})')
    if lead_days:
        print(f'  Lead time (warning → crack): {lead_days} trading days  ({lead_days/252:.2f} yr)')
    print()
    print('STATE DISTRIBUTION')
    for k, v in counts.items():
        pct = v / T_ * 100
        bar = '█' * int(pct / 2)
        print(f'  {k:<15} {v:>4} days  {pct:5.1f}%  {bar}')
    print()
    print('ERROR BUDGET')
    print(f'  Naive (sensor-spoofed) cumulative |ε| : {data["naive_cumulative_error"]:.4f}')
    print(f'  Gated (INCUBATING held)  cumulative |ε|: {data["gated_cumulative_error"]:.4f}')
    ratio = data['naive_cumulative_error'] / max(data['gated_cumulative_error'], 1e-9)
    print(f'  Ratio naive/gated                      : {ratio:.2f}×  (gated carries less error mass)')
    print()
    print('SIGNAL EXTREMES')
    eps = s['epsilon']
    C   = s['C']
    N   = s['N']
    print(f'  Max gap ε          : {max(abs(e) for e in eps):.4f}')
    print(f'  Max C_t            : {max(C):.3f}  (consistency threshold θ_c = {data["params"]["THETA_C"]})')
    print(f'  Max N_t            : {max(N):.2f}σ  (novelty threshold θ_n = {data["params"]["THETA_N"]}σ)')
    print()


if __name__ == '__main__':
    data = generate()
    out_dir = Path(__file__).parent.parent / 'out' / 'synthetic_cracking_2008'
    jp, cp = save(data, out_dir)
    report(data)
    print(f'  JSON → {jp}')
    print(f'  CSV  → {cp}')
