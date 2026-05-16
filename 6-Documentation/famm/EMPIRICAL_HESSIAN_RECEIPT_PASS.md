# Empirical Hessian Receipt Pass

## Purpose

This implementation turns the Hessian-basis recompute from a heuristic routing table into measured curvature receipts.

It uses `hessian-eigenthings` as the matrix-free curvature backend. The project rule is:

```text
do not materialize the full Hessian;
query directional pressure via HVP/matvec;
emit receipts for stiffness, flatness, saddle risk, and residual quality.
```

## Added files

| Path | Purpose |
|---|---|
| `5-Applications/tools-scripts/famm/hessian_receipt_runner.py` | CLI receipt runner around `hessian-eigenthings`. |
| `shared-data/schemas/famm_hessian_curvature_receipt.schema.json` | Receipt schema. |
| `shared-data/examples/famm_hessian_receipt_config.example.json` | Smoke-test config using a diagonal operator. |

## Route rule

The receipt runner maps measured curvature into route actions:

| Curvature signal | Route action |
|---|---|
| negative eigenvalues | `probe_saddle_scar` |
| dominant eigenvalue above threshold | `protect_or_seal_stiff_invariant` |
| enough near-zero eigenvalues | `press_flat_gauge` |
| high trace | `seal_high_total_curvature` |
| otherwise | `continue_measured_probe` |

## Command

```bash
pip install hessian-eigenthings

python3 5-Applications/tools-scripts/famm/hessian_receipt_runner.py \
  --config shared-data/examples/famm_hessian_receipt_config.example.json \
  --out shared-data/hessian-receipts/example_receipt.json
```

## Receipt role

The output is not a proof. It is a computational witness that can update:

```text
proof priority
compression priority
scar-probe priority
closure priority
```

## No-drift boundary

A Hessian receipt can route work, rank scars, and justify pressure gates. It cannot replace exact Lean/Fraction/OISC proof receipts.
