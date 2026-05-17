# Hutter JPEG XL Starfield Eigenprobe First Sweep

Status: `FIRST_SWEEP_OBSERVATION_PROTOCOL_REPLAY_VERIFIED`

Claim boundary: this is not a classifier, not a compressor, not a JPEG XL
performance claim, and not a Hutter Prize claim. It is a visual/eigenprobe
sidecar for asking:

```text
huh, do these projected density patches look grouped like stars?
```

## Core Idea

Use the existing eigenprobe logic on a JPEG XL-style image projection of a
Hutter fixture. The image is not the payload authority. It is a temporary
projection surface for grouping structure.

```text
Hutter text fixture
  -> predetermined PIST map
  -> byte/window projection
  -> JPEG XL sidecar image
  -> pixel-density pattern collections
  -> eigenprobe over density groups
  -> "grouped stars" observation receipt
```

The analogy is to the stellar-gas work:

```text
astronomy rows/cells -> eigenmass grouping
pixel-density cells  -> starfield-like grouping
```

The result is only a routing hint. If a density group looks meaningful, the
next step is to return to the byte fixture and ask whether the original bytes,
window hashes, and replay receipts support the grouping.

## Predetermined PIST Map

The projection must use a predetermined PIST map before any density grouping is
interpreted. This prevents the eigenprobe from inventing coordinates after
seeing the pixels.

```text
byte window
  -> fixed PIST coordinate
  -> fixed image cell / texel address
  -> pixel-density observation
```

The PIST map is the coordinate contract:

| PIST field | First-sweep role |
|---|---|
| `shell` | coarse radial/grouping band |
| `offset` | local position inside shell |
| `mass` / SMN sidecar | expected semantic-load pressure |
| `mirror` / resonance relation | symmetry check for paired density patches |
| `source_window_hash` | byte provenance for the projected cell |

Required map properties:

```text
map_is_declared_before_projection
map_hash_recorded
every_density_component_links_to_pist_cells
unknown_or_unmapped_pixels_do_not_vote
observed_grouping_replays_against_byte_window_hashes
```

If a pixel-density component has no valid PIST map backlink, it is not evidence
of a pattern. It is either projection noise or quarantine.

## Why JPEG XL Is Useful Here

JPEG XL is useful as a sidecar because it is image-native and supports high
fidelity transforms. For this protocol, that matters only as a projection
surface:

```text
not "JXL compresses Hutter better"
but "JXL-like projection gives us a pixel-density field to inspect"
```

No compression claim is allowed from this step.

## Feature Surface

Minimum first-sweep features:

| Feature | Meaning |
|---|---|
| `pixel_density` | local non-background occupancy or intensity |
| `density_gradient` | local change in density |
| `connected_density_component` | grouped patch candidate |
| `component_area` | size of density group |
| `component_centroid` | projected location |
| `nearest_neighbor_distance` | cluster spacing |
| `local_contrast` | group separability |
| `pist_cell_id` | predetermined PIST coordinate for the density cell |
| `pist_map_hash` | hash of the fixed map used before projection |
| `source_window_hash` | byte-window provenance |

## Eigenprobe Question

The first eigenprobe should ask:

```text
Does the dominant direction describe density neighborhoods that are useful as
byte-window replay suggestions, or only projection noise?
```

Allowed observations:

```text
OBSERVE_DENSITY_SUGGESTIONS
OBSERVE_NO_GROUPING
HOLD_PROJECTION_NOISE
QUARANTINE_MISSING_PROVENANCE
```

Forbidden observations:

```text
CLASSIFIER_SUCCESS
COMPRESSION_GAIN
HUTTER_PROGRESS
JXL_SUPERIORITY
BYTE_SEMANTICS_PROVEN_BY_PIXELS
SORTING_SUCCESS
COMPONENT_RANKING_AUTHORITY
```

## Enwik8 First Sweep Result

Receipt:

```text
shared-data/data/stack_solidification/hutter_jxl_starfield/hutter_jxl_starfield_enwik8_first_sweep_receipt.json
```

Fixture:

```text
dataset alias: wikien8_normalized_to_enwik8
source bytes: 63,569,920
slice bytes: 1,048,576
slice sha256: 4fb5efa9f35df431737731bf3c8f38a467b69731940ff82a4ee0e218aae58834
```

Projection:

```text
PIST map: pist_byte_window_nibble_shell_map_v0
projection: 128 x 128 deterministic density field
JPEG XL sidecar: encoded lossless with cjxl
```

Observed density/eigenprobe:

```text
suggested density neighborhoods: 691
components with PIST backlinks: 691
dominant share: 0.347477737176
residual_l2: 9.5e-11
decision: OBSERVE_DENSITY_SUGGESTIONS
ordering policy: scan order, not ranked
promotion policy: byte-window replay required and now satisfied for stored hints
```

Replay verification:

```text
verifier: 4-Infrastructure/shim/hutter_jxl_starfield_replay_verify.py
replay receipt: shared-data/data/stack_solidification/hutter_jxl_starfield/hutter_jxl_starfield_enwik8_first_sweep_replay_receipt.json
unique byte-window hints extracted: 255
verified: 255
mismatches: 0
errors: 0
gate: REPLAY_VERIFIED
```

Controls:

| Control | Components | Dominant share | Residual |
|---|---:|---:|---:|
| shuffled pixel cells | 1223 | 0.328761054432 | 2.1762e-07 |
| randomized PIST cell assignment | 1227 | 0.338212725353 | 8.5e-10 |
| uniform density synthetic | 1 | 0.0 | n/a |
| phase-shifted projection | 682 | 0.349323129954 | 1e-10 |

Interpretation:

```text
The enwik8 slice produced density neighborhoods under the predetermined PIST
projection. Density is only a suggestion surface. This is not a classifier, not
a compression result, not a sorting result, not a byte-semantics proof, and not
Hutter progress. The stored density neighborhoods now have byte-window
provenance for their 255 unique source-window hints. This verifies provenance
only; it does not promote the suggestions into compression, sorting, semantic
classification, or Hutter progress.
```

## Receipt Shape

```json
{
  "protocol": "hutter_jxl_starfield_eigenprobe_first_sweep_v0",
  "fixture": {
    "fixture_id": "string",
    "source_path": "path",
    "source_sha256": "sha256",
    "byte_length": 0
  },
  "projection": {
    "projection_kind": "jpeg_xl_sidecar",
    "projection_tool": "declared_or_hold",
    "projection_hash": "sha256",
    "width": 0,
    "height": 0
  },
  "pist_map": {
    "map_id": "string",
    "map_hash": "sha256",
    "cell_count": 0,
    "unmapped_pixel_policy": "ignore_or_quarantine"
  },
  "density": {
    "cell_count": 0,
    "component_count": 0,
    "components_with_pist_backlinks": 0,
    "density_table_hash": "sha256",
    "component_table_hash": "sha256"
  },
  "eigenprobe": {
    "method": "power_iteration_or_declared",
    "dominant_share": 0,
    "residual_l2": 0,
    "converged": false,
    "dominant_vector_hash": "sha256"
  },
  "gate": {
    "decision": "OBSERVE_DENSITY_SUGGESTIONS|OBSERVE_NO_GROUPING|HOLD_PROJECTION_NOISE|QUARANTINE_MISSING_PROVENANCE",
    "claim_boundary": "not_classifier_not_compression_claim"
  }
}
```

## Next Fixture Gate

Current gate status:

1. The byte fixture has source path, byte length, and SHA-256.
2. The PIST map is declared before projection and hashed.
3. The projection has a hash and deterministic generation command.
4. Density components backlink to PIST cells and source windows.
5. The eigenprobe has negative controls:
   - shuffled pixel cells
   - randomized source-window mapping
   - randomized PIST cell assignment
   - uniform-density synthetic image
   - phase-shifted projection
6. The stored source-window hints were checked against byte-level replay
   receipts: `255/255` verified.

Decision:

```text
ADMIT_FIRST_SWEEP_PROTOCOL_REPLAY_VERIFIED
```
