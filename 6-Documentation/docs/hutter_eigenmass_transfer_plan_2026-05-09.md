# Hutter Eigenmass Transfer Plan

Status: `TRANSFER_PROTOCOL_HOLD_HUTTER_CLAIM`

Decision: `ADMIT_TRANSFER_PROTOCOL_HOLD_HUTTER_CLAIM`

This document ports the DESI/MaNGA multiscale eigenmass pattern into the Hutter
compression lane as a tuning protocol. It is a method-transfer receipt, not a
compression benchmark.

Claim boundary: no enwik9 run, no compression-gain claim, no Hutter Prize claim,
and no FPGA/ASIC promotion is made here.

## Imported Signal

```text
DESI/MaNGA tracer cosine:       0.702922832
DESI/MaNGA sharpening factor:   1.784206501
```

Only the evidence-sharpening pattern transfers. Astronomy values do not become
compression scores.

## Hutter Feature Basis After Tuning

- `byte_offset_phase`
- `symbol_class`
- `local_context_hash_class`
- `long_range_recurrence_distance`
- `prediction_cache_hit`
- `ram_trace_reuse`
- `residual_entropy_proxy`
- `oisc_instruction_density`
- `ammr_receipt_depth`
- `replay_delta_cost`

## Transfer Ladder

- DESI `literal row surface` -> Hutter `raw corpus windows`; gate `WINDOW_FIXTURE_ONLY_UNTIL_CANONICAL_ENWIK9`
- DESI `joined gas/shock constrained cells` -> Hutter `byte-exact replay fixtures constrained by Rust OISC closure`; gate `LEAN_RUST_REPLAY_REQUIRED`
- DESI `constraint sharpening factor` -> Hutter `compression candidate must sharpen prediction/replay axes without losing byte-exact closure`; gate `SHARPENING_WITH_EXACT_REPLAY_ONLY`
- DESI `multiscale cosine alignment` -> Hutter `candidate feature direction must align across raw windows, token/logogram windows, and OISC replay receipts`; gate `MULTISCALE_ALIGNMENT_BEFORE_PROMOTION`

## JPEG XL Starfield First Sweep

Add a non-claim visual sidecar:

```text
Hutter text fixture
  -> byte/window projection
  -> JPEG XL sidecar image
  -> pixel-density pattern collections
  -> eigenprobe over density groups
  -> "grouped stars" observation receipt
```

This is not a classifier and not a compression claim. It only asks whether a
projected pixel-density field shows grouped starfield-like patches worth
returning to the byte fixture for replay checks.

Allowed decisions:

```text
OBSERVE_GROUPING
OBSERVE_NO_GROUPING
HOLD_PROJECTION_NOISE
QUARANTINE_MISSING_PROVENANCE
```

Receipt: `shared-data/data/stack_solidification/hutter_jxl_starfield_eigenprobe_first_sweep_receipt.json`

## Minimum Receipt Shape

```json
{
  "corpus_id": "canonical hash or fixture label",
  "window_id": "byte offset + length + hash",
  "baseline_sizes": "raw, zlib/lzma, current candidate if available",
  "candidate_features": [
    "byte_offset_phase",
    "symbol_class",
    "local_context_hash_class",
    "long_range_recurrence_distance",
    "prediction_cache_hit",
    "ram_trace_reuse",
    "residual_entropy_proxy",
    "oisc_instruction_density",
    "ammr_receipt_depth",
    "replay_delta_cost"
  ],
  "eigenmass": "dominant eigenvalue + explained share + feature vector",
  "replay": "input hash + output hash + instruction count + decision",
  "decision": "ADMIT_FIXTURE / HOLD / QUARANTINE"
}
```

## Promotion Gates

- `canonical_enwik9_sha256_or_fixture_label_required`
- `raw_baseline_required`
- `candidate_wire_format_required`
- `byte_exact_decompressor_receipt_required`
- `negative_controls_required`
- `eigenmass_sharpening_required`
- `no_competitive_hutter_claim_without_full_prize_envelope`

## Holds

- `HOLD_CANONICAL_ENWIK9`
- `HOLD_FULL_CORPUS_RUN`
- `HOLD_COMPETITIVE_COMPRESSION_CLAIM`
- `HOLD_PRODUCTION_DECOMPRESSOR`
- `HOLD_FPGA_ASIC_PROMOTION`

## Receipt

```text
plan hash: 85f1daf7bb2a7ae5236904937d77f10bcdda2d5b97b2acf25ee3ae763dfbe22e
```

## Receipt Backlinks

- Receipt: `shared-data/data/stack_solidification/hutter_eigenmass_transfer_plan_receipt.json`
- Source multiscale receipt: `shared-data/data/stellar_gas_observation/stellar_gas_multiscale_eigenmass_alignment_receipt.json`
- Data: `shared-data/data/stack_solidification/hutter_eigenmass_transfer_plan.json`
- Tiddler: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Eigenmass Transfer Plan.tid`
- JPEG XL first-sweep tiddler: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter JPEG XL Starfield Eigenprobe First Sweep.tid`
