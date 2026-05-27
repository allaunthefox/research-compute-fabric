# PIST Receipt Density Backfill v1

**Status:** CALIBRATED_ENGINEERING_DELTA  
**Scope:** RRC equation corpus routing evidence backfill  
**Script:** `4-Infrastructure/shim/pist_receipt_density_injector.py`

---

## Purpose

This backfill converts existing RRC equation classification rows plus optional PIST spectral/classifier outputs into explicit `receipt_density` records.

It is a routing-evidence population pass, not a promotion pass.

```text
receipt_density populated != theorem proved
receipt_density populated != claim promoted
receipt_density populated == route has structural/witness evidence for RRC use
```

---

## Phase 2.1 verification sequence

Run the local regression harness first:

```bash
python3 4-Infrastructure/shim/test_pist_receipt_density_injector.py
```

Expected result: all tests print `PASS`.

Then emit the audit JSON only:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py
```

Inspect:

```text
shared-data/rrc_receipt_density_backfill.json
```

Only after inspection, run the guarded sidecar write:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py --write-rds
```

Finally validate the sidecar table:

```bash
python3 4-Infrastructure/shim/validate_receipt_density_sidecar.py
```

Optional validation report:

```bash
python3 4-Infrastructure/shim/validate_receipt_density_sidecar.py \
  --out shared-data/rrc_receipt_density_sidecar_validation.json
```

The validator fails if:

```text
sidecar table is empty
any row has promotion != not_promoted
any density/confidence is null or outside [0, 1]
any receipt hash/source is missing
any receipt_density_status is not CANDIDATE or HOLD
```

---

## Phase 2.2 shape-alignment calibration

After classifier-backed density has been generated, run the alignment pass:

```bash
python3 4-Infrastructure/shim/rrc_pist_shape_alignment.py \
  --fail-on-raw-disagreement
```

Then inspect:

```bash
jq '.summary.shape_alignment_counts, .summary.warning_counts' \
  shared-data/rrc_receipt_density_backfill.json
```

Expected transition for the current corpus:

```text
pist_shape_disagreement -> removed
structural_semantic_label_divergence -> present for compatible PIST/RRC label-space divergence
shape_alignment_counts.compatible_structural_projection -> most or all records
```

Reason:

```text
PIST exact/proxy label = structural/spectral morphology
RRC shape label        = semantic/domain routing class
```

So a row like:

```text
PIST exact label: LogogramProjection
RRC shape: CognitiveLoadField
```

is not necessarily an error. It can mean PIST sees a symbolic/logogram surface while RRC supplies the semantic routing class.

After alignment, rerun the guarded RDS sidecar write and readback validator:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py --write-rds
python3 4-Infrastructure/shim/validate_receipt_density_sidecar.py
```

Commit the aligned JSON artifacts after validation.

---

## Default inputs

```text
6-Documentation/docs/rrc_equation_classification.md
shared-data/rrc_pist_exact_validation.json
```

The first file provides equation IDs, RRC shape hints, status, and declared axes.

The second file provides optional PIST spectral/classifier outputs such as:

```text
proxy_pred
exact_pred
matrix_hash
canonical_hash
spectral_gap
rank_estimate
laplacian_zero_count
```

The injector explicitly filters Markdown table header/separator rows such as `Equation` and `---`, which older validation passes could accidentally treat as equations.

---

## Default output

```text
shared-data/rrc_receipt_density_backfill.json
```

Optional JSONL output for later DB/RDS import:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py \
  --jsonl-out shared-data/rrc_receipt_density_backfill.jsonl
```

---

## Run command

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py
```

Strict mode, useful for CI:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py --fail-on-missing-pist
```

Custom input/output:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py \
  --rrc-file 6-Documentation/docs/rrc_equation_classification.md \
  --pist-report shared-data/rrc_pist_exact_validation.json \
  --out shared-data/rrc_receipt_density_backfill.json
```

Guarded RDS sidecar write:

```bash
python3 4-Infrastructure/shim/pist_receipt_density_injector.py \
  --write-rds \
  --rds-table ene.rrc_receipt_density
```

The writer uses:

```text
4-Infrastructure/shim/rds_connect.py
```

so connection parameters resolve through the shared RDS path:

```text
DATABASE_URL
RDS_* env vars
IAM token / boto3 / AWS CLI
password fallback
```

---

## Record schema

Each record has the form:

```json
{
  "receipt_version": "pist-receipt-density-v1",
  "equation_id": "bandwidth_adjusted_threshold",
  "rrc_shape": "CognitiveLoadField",
  "domain": "analysis",
  "source_status": "CANDIDATE",
  "receipt_density": 0.7125,
  "confidence": 0.6842,
  "density_components": {
    "status_score": 0.45,
    "axis_score": 1.0,
    "spectral_quality": 0.73,
    "shape_agreement": 0.82
  },
  "shape_prediction": {
    "ground_truth_hint": "CognitiveLoadField",
    "proxy_pred": "...",
    "exact_pred": "...",
    "matrix_hash": "...",
    "canonical_hash": "...",
    "spectral_gap": 0.42,
    "rank_estimate": 8,
    "laplacian_zero_count": 1
  },
  "shape_alignment": {
    "alignment_version": "rrc-pist-shape-alignment-v1",
    "alignment_status": "compatible_structural_projection",
    "alignment_confidence": 0.72,
    "label_space_model": "PIST=morphology; RRC=semantic routing"
  },
  "top_axes": ["projection_declared", "negative_control_strength"],
  "status": "CANDIDATE",
  "promotion": "not_promoted",
  "source": "pist_receipt_density_injector_v1",
  "receipt_hash": "...",
  "warnings": ["structural_semantic_label_divergence"]
}
```

---

## RDS sidecar schema

The guarded writer creates or upserts into:

```text
ene.rrc_receipt_density
```

Fields:

```text
equation_id
rrc_shape
domain
source_status
receipt_density
receipt_density_source
receipt_density_hash
receipt_density_status
receipt_density_warnings
confidence
top_axes
shape_prediction
density_components
promotion
payload
updated_at
```

The table has a check constraint:

```sql
promotion = 'not_promoted'
```

This makes promotion drift fail at the database boundary.

---

## Density calculation

The density score is computed from four bounded components:

```text
status_score
axis_score
spectral_quality
shape_agreement
```

Current weighting:

```text
receipt_density =
  0.26 * status_score
+ 0.24 * axis_score
+ 0.26 * spectral_quality
+ 0.24 * shape_agreement
```

Confidence is slightly more classifier-weighted:

```text
confidence =
  0.20 * status_score
+ 0.20 * axis_score
+ 0.28 * spectral_quality
+ 0.32 * shape_agreement
```

This is intentionally conservative. A missing PIST prediction can still produce a low-density record from declared RRC axes, but the record receives a `missing_pist_prediction` warning.

---

## Claim boundary

The script writes every record as:

```json
"promotion": "not_promoted"
```

This is the central anti-drift boundary.

The generated density says:

```text
This equation has routing evidence.
```

It does not say:

```text
This equation is true.
This equation is proved.
This equation is promoted to REVIEWED.
```

Promotion still requires external receipts, Lean/kernel verification where applicable, or human/adversarial review depending on the claim class.

---

## CI candidate

A minimal CI step should run:

```bash
python3 4-Infrastructure/shim/test_pist_receipt_density_injector.py
python3 4-Infrastructure/shim/pist_receipt_density_injector.py --fail-on-missing-pist
python3 4-Infrastructure/shim/rrc_pist_shape_alignment.py --fail-on-raw-disagreement
```

The sidecar validator should run only in environments with RDS credentials.

---

## Keeper phrase

```text
PIST stops being just a repair engine when its classifications become receipt density for the RRC corpus.
```

```text
PIST is seeing morphology; RRC is naming semantics.
```
