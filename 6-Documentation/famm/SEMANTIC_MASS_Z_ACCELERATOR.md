# Semantic Mass Z-Domain Accelerator

## Purpose

Apply the Z-transform to Semantic Mass Numbers so repeated semantic-history scans can be replaced by compact recurrence receipts.

The core move:

```text
semantic mass stream
→ Z-domain recurrence
→ pole / ROC / residual receipt
→ low-cost state update
```

This turns Semantic Mass from a per-event scalar into a transfer object.

## Canonical sequence

Let a routed object, chat thread, proof route, token lane, or signal path emit a typed semantic mass stream:

```math
\mu[k]
=
w_H H[k]
+
w_L L[k]
+
w_I I[k]
+
w_R R[k]
+
w_C C[k]
```

Where the lanes may represent entropy/load, Landauer or compute cost, invariant pressure, residual scar, and closure/context cost.

The one-sided Z-transform is:

```math
M(z)=\sum_{k=0}^{\infty}\mu[k]z^{-k}
```

## Recurrence compression

Instead of carrying the full history, fit a causal recurrence:

```math
\mu[k]
=
\sum_{i=1}^{p}a_i\mu[k-i]
+
\sum_{j=0}^{q}b_j u[k-j]
+
r[k]
```

or in transfer form:

```math
H_\mu(z)
=
\frac{M(z)}{U(z)}
=
\frac{B(z)}{A(z)}
```

with:

```math
A(z)=1-\sum_{i=1}^{p}a_i z^{-i}
```

The stored object becomes:

```text
coefficients + state vector + residual seal
```

not the entire history.

## Acceleration rule

Naive history carry:

```text
O(n) scan of semantic history
```

Z-domain carry:

```text
O(p+q) recurrence update
```

This is the same compression doctrine as `DELTA_MEM`, but for Semantic Mass Numbers.

## ROC / stability gate

The poles of `A(z)` are semantic memory scars.

| Pole behavior | FAMM meaning | Route action |
|---|---|---|
| all `|p_i| < 1` | stable semantic memory | carry recurrence |
| pole near unit circle | long-memory / high inertia | use DELTA_MEM or seal |
| pole outside unit circle | unstable route | quarantine / closure test |
| repeated poles | strong recurrence basin | promote as eigensolid candidate |

The ROC is the admissible chart region.

## Integration with existing shortcuts

| Existing shortcut | Z-domain role |
|---|---|
| `DELTA_MEM` | stores online recurrence state instead of full history |
| `HESSIAN_EIGEN` | decides whether recurrence basin is stiff, flat, or saddle-like |
| `E_TAIL_BOUND` | seals bounded residual tails |
| `SYSTEM_CLOSURE` | tests whether bad poles mean missing boundary/context |
| `OISC` | executes recurrence using load/delay/accumulate/branch |
| Coulomb compression boundary | stops pressing when recurrence residual is cheaper to seal |

## FAMM object

```math
\mathfrak C_{\mathrm{MassZ}}
=
A_{16}(u_{\mu})
\otimes
[
\Sigma_{\mu}
+
\Sigma_{Z}
+
\Sigma_{\mathrm{pole}}
+
\Sigma_{\mathrm{ROC}}
+
\Sigma_{\mathrm{rec}}
+
\Sigma_{\mathrm{resid}}
+
\epsilon_{\mathrm{fit}}
]
```

Where:

- `Σ_mu` = typed semantic mass sequence.
- `Σ_Z` = Z-domain transform.
- `Σ_pole` = recurrence pole structure.
- `Σ_ROC` = admissible convergence chart.
- `Σ_rec` = recurrence coefficients/state.
- `Σ_resid` = residual seal.
- `ε_fit` = fit/model uncertainty.

## Updated compression spine

```text
SEMANTIC_MASS
→ Z_DOMAIN_GATE
→ DELTA_MEM
→ HESSIAN_EIGEN
→ E_TAIL_BOUND
→ SYSTEM_CLOSURE
```

## Project sentence

Semantic Mass Numbers become faster when treated as a Z-domain recurrence: store the pole/ROC law and residual seal, not every historical mass sample.
