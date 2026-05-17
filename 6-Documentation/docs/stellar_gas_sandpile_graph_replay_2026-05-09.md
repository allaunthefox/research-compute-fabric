# Stellar Gas Sandpile Graph Replay

Status: `GRAPH_TOPPLING_PROXY`

Decision: `ADMIT_GRAPH_TOPPLING_PROXY_HOLD_PHYSICAL_SANDPILE_SIMULATION`

This hardening pass turns the sandpile metaphor into a reproducible graph
diagnostic. Nodes are sky/redshift cells. Edges are defined by sky-sector
neighbors plus adjacent redshift bins. Grain and toppling values are diagnostic
proxies derived from the existing cell-level toppling index.

Claim boundary: this is not a physical sandpile simulation, not a stellar-gas
mechanism proof, not direct stellar mass, not gas density inference, and not a
cosmology fit.

## Replay Receipt

```json
{
  "avalanche_sizes": [
    {
      "avalanche_size_cells": 10,
      "seed_cell": "ra02_north__z_008_plus",
      "terminated": true,
      "topple_events": 21
    },
    {
      "avalanche_size_cells": 10,
      "seed_cell": "ra02_south__z_008_plus",
      "terminated": true,
      "topple_events": 21
    },
    {
      "avalanche_size_cells": 10,
      "seed_cell": "ra03_north__z_008_plus",
      "terminated": true,
      "topple_events": 21
    },
    {
      "avalanche_size_cells": 10,
      "seed_cell": "ra03_south__z_008_plus",
      "terminated": true,
      "topple_events": 21
    },
    {
      "avalanche_size_cells": 10,
      "seed_cell": "ra04_north__z_008_plus",
      "terminated": true,
      "topple_events": 21
    }
  ],
  "created": "2026-05-10T04:07:14+00:00",
  "decision": "ADMIT_GRAPH_TOPPLING_PROXY_HOLD_PHYSICAL_SANDPILE_SIMULATION",
  "edge_count": 45,
  "graph_hash": "fdfc686a022b726f550f73ad663cd9e222122a1048193dd22dafee0d891c62af",
  "node_count": 25,
  "receipt_type": "stellar_gas_sandpile_graph_replay_receipt",
  "replay_hash": "95e938b7f6ed3a3c64af0fdaec45e9296316ae9e77b6b937aaa9ee16f7665393",
  "seed_avalanche_cell_count": 5,
  "seed_candidate_object_count": 911,
  "validated_outputs": [
    "shared-data/data/stellar_gas_observation/stellar_gas_sandpile_graph_replay.json",
    "shared-data/data/stellar_gas_observation/stellar_gas_sandpile_graph_replay_receipt.json",
    "6-Documentation/docs/stellar_gas_sandpile_graph_replay_2026-05-09.md",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Sandpile Graph Replay.tid"
  ]
}
```

## Seed Evidence

```text
avalanche cells:      5
candidate objects:    911
graph nodes:          25
graph edges:          45
graph hash:           fdfc686a022b726f550f73ad663cd9e222122a1048193dd22dafee0d891c62af
replay hash:          95e938b7f6ed3a3c64af0fdaec45e9296316ae9e77b6b937aaa9ee16f7665393
```

## Toppling Threshold Table

| cell | degree | threshold |
| --- | ---: | ---: |
| `ra02_north__z_000_002` | 3 | 4 |
| `ra02_north__z_002_004` | 4 | 5 |
| `ra02_north__z_004_006` | 4 | 5 |
| `ra02_north__z_006_008` | 4 | 5 |
| `ra02_north__z_008_plus` | 3 | 4 |
| `ra02_south__z_000_002` | 3 | 4 |
| `ra02_south__z_002_004` | 4 | 5 |
| `ra02_south__z_004_006` | 4 | 5 |
| `ra02_south__z_006_008` | 4 | 5 |
| `ra02_south__z_008_plus` | 3 | 4 |
| `ra03_north__z_000_002` | 4 | 5 |
| `ra03_north__z_002_004` | 5 | 6 |
| `ra03_north__z_004_006` | 5 | 6 |
| `ra03_north__z_006_008` | 5 | 6 |
| `ra03_north__z_008_plus` | 4 | 5 |
| `ra03_south__z_000_002` | 3 | 4 |
| `ra03_south__z_002_004` | 4 | 5 |
| `ra03_south__z_004_006` | 4 | 5 |
| `ra03_south__z_006_008` | 4 | 5 |
| `ra03_south__z_008_plus` | 3 | 4 |
| `ra04_north__z_000_002` | 2 | 3 |
| `ra04_north__z_002_004` | 3 | 4 |
| `ra04_north__z_004_006` | 3 | 4 |
| `ra04_north__z_006_008` | 3 | 4 |
| `ra04_north__z_008_plus` | 2 | 3 |

## Initial Grain Table

| cell | initial grains | index z proxy | seed objects |
| --- | ---: | ---: | ---: |
| `ra02_north__z_000_002` | 0 | -0.949257801 | 0 |
| `ra02_north__z_002_004` | 0 | -0.553842296 | 0 |
| `ra02_north__z_004_006` | 0 | -0.41882282 | 0 |
| `ra02_north__z_006_008` | 2 | 0.228692003 | 0 |
| `ra02_north__z_008_plus` | 7 | 1.638406841 | 364 |
| `ra02_south__z_000_002` | 0 | -1.463289664 | 0 |
| `ra02_south__z_002_004` | 0 | -0.737986126 | 0 |
| `ra02_south__z_004_006` | 0 | -0.194645543 | 0 |
| `ra02_south__z_006_008` | 5 | 0.953489356 | 0 |
| `ra02_south__z_008_plus` | 7 | 1.64578653 | 15 |
| `ra03_north__z_000_002` | 0 | -0.368783497 | 0 |
| `ra03_north__z_002_004` | 0 | -0.100706818 | 0 |
| `ra03_north__z_004_006` | 0 | -0.372968233 | 0 |
| `ra03_north__z_006_008` | 3 | 0.353320701 | 0 |
| `ra03_north__z_008_plus` | 9 | 1.754659087 | 305 |
| `ra03_south__z_000_002` | 0 | -1.161555303 | 0 |
| `ra03_south__z_002_004` | 0 | -0.731256364 | 0 |
| `ra03_south__z_004_006` | 0 | -1.186176214 | 0 |
| `ra03_south__z_006_008` | 0 | -0.039293889 | 0 |
| `ra03_south__z_008_plus` | 7 | 1.726607707 | 8 |
| `ra04_north__z_000_002` | 0 | -1.291360152 | 0 |
| `ra04_north__z_002_004` | 0 | -0.333483573 | 0 |
| `ra04_north__z_004_006` | 0 | -0.226002461 | 0 |
| `ra04_north__z_006_008` | 1 | 0.115968267 | 0 |
| `ra04_north__z_008_plus` | 6 | 1.71250026 | 219 |

## Avalanche Sizes

| seed cell | size cells | topple events | terminated |
| --- | ---: | ---: | --- |
| `ra02_north__z_008_plus` | 10 | 21 | `True` |
| `ra02_south__z_008_plus` | 10 | 21 | `True` |
| `ra03_north__z_008_plus` | 10 | 21 | `True` |
| `ra03_south__z_008_plus` | 10 | 21 | `True` |
| `ra04_north__z_008_plus` | 10 | 21 | `True` |

## Holds

- `HOLD_PHYSICAL_SANDPILE_SIMULATION`
- `HOLD_STELLAR_GAS_MECHANISM_PROOF`
- `HOLD_DIRECT_STELLAR_MASS`
- `HOLD_DIRECT_GAS_DENSITY_INFERENCE`
- `HOLD_COSMOLOGY_FIT`
