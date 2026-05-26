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
  "top_axes": ["projection_declared", "negative_control_strength"],
  "status": "CANDIDATE",
  "promotion": "not_promoted",
  "source": "pist_receipt_density_injector_v1",
  "receipt_hash": "...",
  "warnings": []
}
```

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

## Next integration step

Once the JSON output is inspected, the next safe step is an explicit DB writer guarded by a flag such as:

```bash
--write-rds
```

That writer should upsert only these fields:

```text
receipt_density
receipt_density_source
receipt_density_hash
receipt_density_status
receipt_density_warnings
```

and should not alter theorem truth, promotion state, or claim ladder status.

---

## Keeper phrase

```text
PIST stops being just a repair engine when its classifications become receipt density for the RRC corpus.
```
