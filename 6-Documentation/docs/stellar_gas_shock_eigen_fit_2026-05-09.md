# Stellar Gas Shock Eigen Fit

**Date:** 2026-05-09

**Decision:** `ADMIT_NONZERO_PHYSICAL_SHOCK_SUPPORT`

**Claim boundary:** observation-proxy fit only. This does not claim
astrophysical validation, stellar shock breakout detection, or causality.

## What Changed

The physical shock eigen axis now has a nonzero observation-backed proxy
from SDSS DR17 MaNGA DAPall gas and velocity columns.

```text
prior strength:      0.000000
proxy mean:          0.461376
nonzero fraction:    0.992236
refined strength:    0.647177
support delta:       0.647177
```

## Observable Proxies

| Observable | Count | Mean | Median | P90 |
|---|---:|---:|---:|---:|
| `gas_velocity_span_kms` | 42811 | 397.187875 | 311.291389 | 822.890198 |
| `stellar_velocity_span_kms` | 42602 | 193.236817 | 173.686531 | 349.935837 |
| `velocity_contrast` | 42477 | 3.331742 | 1.379355 | 7.966636 |
| `gas_sigma_1re_kms` | 42296 | 154.21832 | 77.279633 | 413.750671 |
| `stellar_sigma_1re_kms` | 41752 | 118.104428 | 93.785969 | 232.383652 |
| `emline_rchi2_1re` | 42689 | 1.206166 | 1.012547 | 1.433319 |
| `snr_med_mean` | 43019 | 12.062023 | 9.551437 | 22.979785 |
| `shock_proxy_score` | 43019 | 0.461376 | 0.373522 | 0.861038 |

## Gate

```text
if admitted_proxy_rows == 0:
  HOLD_NO_OBSERVATION_SUPPORT
elif refined_strength > 0:
  ADMIT_NONZERO_PHYSICAL_SHOCK_SUPPORT
else:
  HOLD_RESIDUAL_CONTEXT
```

## Next Work

1. Add emission-line index metadata so the 35-element MaNGA arrays become
   named H-alpha, H-beta, OIII, NII, and SII lanes.
2. Replace the current proxy with line-ratio diagnostics and uncertainties.
3. Compare high-score rows against Rankine-Hugoniot / Sedov-Taylor receipt
   gates only after source-specific physical context is present.
