# Mass Equation Distill Receipt

Schema: `mass_equation_distill_receipt_v1`
Decision: `COVERAGE_RECEIPT_ONLY`
Receipt hash: `4981f6580f70f36813b97bcc0e1dac414bef2608d534685d598a51734bdaf538`

## Claim Boundary

Mass-equation distill coverage receipt. This records extracted/tagged equation surfaces and structural features for routing, compression, and candidate-law selection. It is not a theorem verification result, not a complete all-mathematics corpus claim, not a benchmark result, and not a claim that every row is semantically a physical mass law.

## Primary Artifact

- Path: `3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified.parquet`
- Rows: `106380`
- Bytes: `21076276`
- SHA256: `19feda5d417b016f40cf651e69f7aa90edab98a5d12f83474eb4e9d05f0e8300`

## Coverage Snapshot

Top domains:
- `unknown`: 55089
- `physics`: 25025
- `mathematics`: 18950
- `machine_learning`: 4068
- `computation`: 3248

Top categories:
- ``: 55089
- `math.NT`: 18950
- `math-ph`: 18804
- `hep-th`: 5698
- `cs.LG`: 4068
- `cs.AI`: 3248
- `cond-mat`: 523

Feature counts:
- `has_operator`: 105372
- `has_derivative`: 72456
- `has_integral`: 87
- `has_sum`: 1294
- `has_product`: 561
- `has_fraction`: 284
- `has_matrix`: 851
- `has_vector`: 6190
- `has_function_call`: 28870
- `has_subscript`: 2376
- `has_superscript`: 366
- `has_sqrt`: 4038
- `is_short`: 30947
- `is_medium`: 60404
- `is_long`: 15029

## Related Artifacts

- Timestamped parquet: `3-Mathematical-Models/equations_parquet_tagged/mass_equations_20260504_134248.parquet` (38279 rows)
- Compressed artifact: `3-Mathematical-Models/equations_compressed/mass_equations_20260504_134248.compressed`

## Exclusions

- No proof replay or Lean build was run by this receipt.
- No byte-exact compression benchmark is claimed.
- Rows are extracted/tagged equation surfaces, not authoritative mathematical truth.
- The source coverage observed here is arXiv-only for the unified parquet.
- Domain value 'unknown' remains unresolved and must not be promoted as typed coverage.
- The compressed artifact is an older timestamped mass-equation artifact, not a compressed form of every unified row unless a separate replay receipt proves it.
