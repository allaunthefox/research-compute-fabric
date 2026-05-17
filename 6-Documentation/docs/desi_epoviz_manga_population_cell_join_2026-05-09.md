# DESI Epoviz to MaNGA Population Cell Join

Status: `COARSE_CELL_PRIOR`

Decision: `ADMIT_COARSE_CELL_PRIOR_HOLD_OBJECT_CROSSMATCH`

This note uses the DESI EDR epoviz visualization/outreach VAC as a lightweight
population prior and compares it with the local MaNGA stellar-gas grouping study
by shared sky/redshift cells.

Claim boundary: this is not an object-level crossmatch, not a direct gas-density
map, and not a cosmology fit. It is a population-shape prior for deciding where
the stellar-gas model has local support and where it should stay in `HOLD`.

## Source

- DESI EDR epoviz CSV: `shared-data/artifacts/stellar_gas_observation/desi_epoviz/EDR-Viz-Outreach-VAC.csv.gz`
- DESI source hash: `83a4c4c4c4e8eb309e6a71459b3e6087113b82ef03edeeb09752ce368443b6d6`
- DESI documentation: https://data.desi.lbl.gov/doc/releases/edr/vac/epoviz/
- MaNGA grouping study: `shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study.json`

## DESI Population

Rows read: `669377`

Tracer counts:

- `BGS`: 228630
- `ELG`: 261489
- `LRG`: 125174
- `QSO`: 54084

Local redshift bins used for MaNGA overlap:

- `z_000_002`: 580
- `z_002_004`: 4313
- `z_004_006`: 3729
- `z_006_008`: 7017
- `z_008_plus`: 653738

Redshift summary:

```json
{
  "count": 669377,
  "min": 0.010233,
  "max": 3.499648,
  "mean": 0.765852
}
```

## Coarse Join

Join key:

```text
raXX_north_or_south__z_000_002/z_002_004/z_004_006/z_006_008/z_008_plus
```

Joined cells: `25` out of `56` MaNGA cells.

Top joined cells:

- `ra03_north__z_008_plus`: DESI 315331, MaNGA 305, shock proxy 0.918033
- `ra04_north__z_008_plus`: DESI 181621, MaNGA 219, shock proxy 0.922374
- `ra02_north__z_008_plus`: DESI 44035, MaNGA 364, shock proxy 0.881868
- `ra03_north__z_002_004`: DESI 2439, MaNGA 1622, shock proxy 0.676326
- `ra03_north__z_006_008`: DESI 3456, MaNGA 374, shock proxy 0.754011
- `ra04_north__z_002_004`: DESI 1177, MaNGA 960, shock proxy 0.60625
- `ra03_south__z_008_plus`: DESI 100231, MaNGA 8, shock proxy 1.0
- `ra03_north__z_004_006`: DESI 1401, MaNGA 531, shock proxy 0.572505

## Holds

- `HOLD_OBJECT_LEVEL_CROSSMATCH`
- `HOLD_DIRECT_GAS_DENSITY_INFERENCE`
- `HOLD_SELECTION_FUNCTION_FIT`
- `HOLD_COSMOLOGY_FIT`

## Receipt Backlinks

- Receipt: `shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join_receipt.json`
- Data: `shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join.json`
- Tiddler: `6-Documentation/tiddlywiki-local/wiki/tiddlers/DESI Epoviz MaNGA Population Cell Join.tid`
