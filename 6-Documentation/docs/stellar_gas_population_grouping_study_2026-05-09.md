# Stellar Gas Population Grouping Study

**Date:** 2026-05-09

**Decision:** `ADMIT_POPULATION_GROUPING_SURFACE`

**Claim boundary:** MaNGA stellar-gas population grouping only. A coarse
DESI/MaNGA cell join now exists; object-level crossmatch remains `HOLD`.
Proxy classes do not prove physical shock, AGN, or gas mechanism.

## Population Surface

```text
rows seen, all DAP types: 43128
unique Plate-IFU count:   10782
selected population:      10782
preferred DAPTYPE:        HYB10-MILESHC-MASTARSSP
```

## Aggregate

```json
{
  "bpt_proxy_classes": {
    "agn_liner_or_shock_proxy": 2740,
    "star_forming_proxy": 5029,
    "composite_proxy": 2883,
    "unclassified": 130
  },
  "shock_lier_proxy_classes": {
    "shock_lier_proxy": 4589,
    "partial_shock_proxy": 2458,
    "no_shock_proxy": 3735
  },
  "partial_or_full_shock_fraction": 0.653589,
  "gas_sigma_summary": {
    "count": 10609,
    "min": 0.384927,
    "max": 929.010071,
    "mean": 157.969176,
    "median": 77.881104,
    "p90": 420.896637
  },
  "stellar_sigma_summary": {
    "count": 10297,
    "min": 3.115719,
    "max": 765.25354,
    "mean": 118.838681,
    "median": 94.604462,
    "p90": 233.339722
  }
}
```

## Redshift Bins

| Bin | Count | Shock+Partial Fraction | Gas Sigma Median | Stellar Sigma Median |
|---|---:|---:|---:|---:|
| `z_002_004` | 4838 | 0.619678 | 55.327721 | 72.146851 |
| `z_004_006` | 2415 | 0.57764 | 78.61245 | 101.009289 |
| `z_008_plus` | 1250 | 0.896 | 284.684052 | 230.705811 |
| `z_000_002` | 1241 | 0.635778 | 30.074999 | 52.191267 |
| `z_006_008` | 1038 | 0.717726 | 157.058464 | 172.332016 |

## DESI-Ready Sky/Redshift Cells

These are population cells for the existing coarse DESI/MaNGA cell join. They
are not object-level DESI/MaNGA crossmatches and not DESI environment classes
yet.

| Cell | Count | Shock+Partial Fraction | Main BPT Counts |
|---|---:|---:|---|
| `ra03_north__z_002_004` | 1622 | 0.676326 | `{'star_forming_proxy': 811, 'agn_liner_or_shock_proxy': 342, 'composite_proxy': 437, 'unclassified': 32}` |
| `ra02_north__z_002_004` | 1289 | 0.584174 | `{'agn_liner_or_shock_proxy': 222, 'composite_proxy': 286, 'star_forming_proxy': 781}` |
| `ra04_north__z_002_004` | 960 | 0.60625 | `{'agn_liner_or_shock_proxy': 219, 'composite_proxy': 257, 'star_forming_proxy': 483, 'unclassified': 1}` |
| `ra02_north__z_004_006` | 684 | 0.554094 | `{'composite_proxy': 188, 'star_forming_proxy': 319, 'agn_liner_or_shock_proxy': 174, 'unclassified': 3}` |
| `ra03_north__z_004_006` | 531 | 0.572505 | `{'star_forming_proxy': 246, 'composite_proxy': 152, 'agn_liner_or_shock_proxy': 131, 'unclassified': 2}` |
| `ra00_north__z_000_002` | 450 | 0.72 | `{'star_forming_proxy': 214, 'agn_liner_or_shock_proxy': 79, 'composite_proxy': 117, 'unclassified': 40}` |
| `ra04_north__z_004_006` | 420 | 0.6 | `{'agn_liner_or_shock_proxy': 128, 'star_forming_proxy': 159, 'composite_proxy': 133}` |
| `ra03_north__z_006_008` | 374 | 0.754011 | `{'star_forming_proxy': 83, 'agn_liner_or_shock_proxy': 164, 'composite_proxy': 127}` |
| `ra02_north__z_008_plus` | 364 | 0.881868 | `{'agn_liner_or_shock_proxy': 163, 'composite_proxy': 143, 'star_forming_proxy': 58}` |
| `ra03_north__z_008_plus` | 305 | 0.918033 | `{'composite_proxy': 130, 'star_forming_proxy': 43, 'agn_liner_or_shock_proxy': 129, 'unclassified': 3}` |
| `ra03_north__z_000_002` | 279 | 0.670251 | `{'agn_liner_or_shock_proxy': 40, 'star_forming_proxy': 188, 'unclassified': 14, 'composite_proxy': 37}` |
| `ra02_north__z_000_002` | 270 | 0.581481 | `{'star_forming_proxy': 210, 'composite_proxy': 30, 'agn_liner_or_shock_proxy': 28, 'unclassified': 2}` |

## What This Gives Us

- A population baseline over unique MaNGA Plate-IFU rows.
- Grouped shock/LIER and BPT proxy counts by redshift and sky cell.
- DESI-ready cells now used by the coarse DESI/MaNGA cell join.
- Residual target: cells whose local gas state diverges from later DESI environment priors.

## Receipt

`shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study_receipt_*.json`

## Receipt Backlinks

- Coarse cell join receipt: `shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join_receipt.json`
- Tiddler: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Population Grouping Study.tid`
