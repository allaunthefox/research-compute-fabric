# Stellar Gas Line Ratio Diagnostics

**Date:** 2026-05-09

**Decision:** `ADMIT_LINE_RATIO_DIAGNOSTIC_SURFACE`

**Claim boundary:** line-ratio proxy only. This does not prove a
physical shock, AGN, stellar breakout, or ionization mechanism.

## What Changed

The 35-element MaNGA emission-line arrays now have named channels, so
physics can propagate through line ratios instead of anonymous vector
positions.

```text
rows seen:             43128
valid ratio rows:      42450
shock proxy support:   0.531801
shock proxy gate:      ADMIT_LINE_RATIO_SHOCK_PROXY_SUPPORT
```

## Aggregate Ratios

| Ratio | Count | Mean | Median | P90 |
|---|---:|---:|---:|---:|
| `log_nii_ha` | 42357 | -0.308976 | -0.338542 | 0.0904 |
| `log_sii_ha` | 42266 | -0.271433 | -0.353311 | 0.096763 |
| `log_oi_ha` | 42253 | -0.943352 | -1.152453 | -0.049001 |
| `log_oiii_hb` | 42278 | -0.009821 | -0.014188 | 0.467312 |
| `balmer_decrement` | 42308 | 59.793473 | 3.44199 | 4.852172 |
| `gas_sigma_1re_kms` | 42110 | 154.899503 | 77.729897 | 414.167969 |
| `shock_lier_score` | 43128 | 0.48278 | 0.35 | 1.0 |

## Proxy Classes

```json
{
  "bpt_proxy_classes": {
    "agn_liner_or_shock_proxy": 12417,
    "star_forming_proxy": 19567,
    "composite_proxy": 10228,
    "unclassified": 916
  },
  "shock_lier_proxy_classes": {
    "shock_lier_proxy": 18154,
    "partial_shock_proxy": 9563,
    "no_shock_proxy": 15411
  }
}
```

## Physics Propagation

- Saha/ionization now has line-ratio support, but still needs electron density and temperature.
- Radiative transfer now has named flux and Balmer-decrement lanes, but still needs an attenuation model.
- Shock excitation now has SII/Ha, OI/Ha, OIII/Hb, NII/Ha, and H-alpha sigma proxy support.
