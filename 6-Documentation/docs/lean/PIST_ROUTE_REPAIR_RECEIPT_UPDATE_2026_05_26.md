# PIST Route-Repair + Receipt Semantics Update

**Date:** 2026-05-26  
**Status:** CALIBRATED_ENGINEERING_DELTA  
**Scope:** PIST route repair, quaternion fixed-point receipt semantics, genus-0 projection demo, archive hygiene

---

## Executive summary

This update records the current state of the PIST route-repair pipeline and the associated Lean/Q16.16 cleanup pass.

The project now has three related but distinct layers:

1. **Route-Repair v1.4 / v1.4a** — theorem-shape-driven proof repair with charted 16D → 4D → 3D routing.
2. **Q16.16 quaternion receipt semantics** — approximate quaternion operations now carry an explicit `wf_unit : Bool` receipt instead of pretending to prove exact unit norm.
3. **Genus-0 sphere-shell witness demo** — the base projection spaces are contractible, so higher-genus signatures belong to residual/stress graphs, not the control manifold itself.

The net architectural correction is:

```text
Base control geometry: R^16 -> Delta^4 -> R^3_+
Topology: contractible / genus-0
Residual topology: graph/cycle/branch debt may carry higher-genus signatures
```

---

## Route-Repair status

The route-repair line progressed through the following ablation ladder:

| Version | Method | Result / role |
|---|---|---|
| v1.1 | spectral-only repair | degenerate one-step traces collapsed; unsuitable alone |
| v1.2 | hybrid text fallback | text/goal-state fallback recovered a useful baseline |
| v1.3a | NUVMAP ranking | preserved baseline; ranked address-space candidates |
| v1.3b | multi-step theorem-shape templates | fixed case/bridge failures; moved repair from flat tactic list to proof surgery |
| v1.4 | charted repair manifold | 16D modifier -> 4D repair axis -> 3D patch embedding; pushed recovery materially higher |
| v1.4a | residual closure | targeted destructuring, contradiction, and invalid-goal detection |

The useful interpretation is:

```text
failed theorem
-> parsed theorem shape
-> 16D modifier
-> 4D repair chart
-> 3D ranked Lean patch
-> retry
-> receipt
```

The important implementation lesson is that **NUVMAP ranking alone does not repair a theorem**. It becomes useful when multiple candidate motifs/patches compete. The winning pattern is:

```text
classification gives a route prior
NUVMAP/chart geometry ranks candidate repairs
multi-step theorem-shape templates perform the actual proof surgery
```

---

## Genus correction

Earlier genus-language can easily overreach. The corrected model is:

```text
R^16 modifier       : contractible vector space
Delta^4 axis        : convex probability simplex
R^3_+ patch embed   : convex positive orthant
S^2 shell witness   : genus-0 rendered witness
```

Therefore the base repair/control geometry is **genus 0**.

Higher genus belongs to residual or stress structure, for example:

- proof transition graphs with cycle rank,
- branch debt after failed `cases` / `constructor`,
- rewrite loops / equality cycles,
- obstruction graphs from failed patch attempts,
- topology witnesses in actual rendered or simulated surfaces.

Operational rule:

```text
Use genus as residual topology, not as a base-space claim.
```

---

## Q16.16 quaternion receipt correction

The quaternion Lean stack previously stored exact unit-norm proofs for values produced by approximate Q16.16 operations. That was too strong.

The corrected model in `Semantics.UnitQuaternion` is:

```lean
structure UnitQuaternion where
  w : Q16_16
  x : Q16_16
  y : Q16_16
  z : Q16_16
  wf_unit : Bool
```

`wf_unit` is now a **receipt bit**, not a theorem claiming exact equality:

```lean
w*w + x*x + y*y + z*z = one
```

This better matches the fixed-point doctrine:

```text
exactness belongs to receipts, witnesses, residual bounds, or future real/quaternion bridge proofs;
approximate hot-path operations should not fabricate exact algebraic invariants.
```

Updated theorem style:

```lean
identityCarriesUnitWitness
conjugatePreservesWitness
mulWitness
stochasticEvolutionPreservesUnitWitness
sluqQuaternionOptimizationPreservesUnitWitness
```

This is a correctness improvement, not a downgrade: it removes false exactness and makes the invariant boundary explicit.

---

## Genus-0 sphere-shell witness demo

The demo script is:

```text
4-Infrastructure/shim/genus0_sphere_shell_demo.py
```

It emits a JSON receipt for:

```text
R^16 -> Delta^4 -> R^3_+ -> S^2 shell witness
```

The rendered shell uses the existing sphere/fBm concept:

```text
signed-distance sphere shell
+ embedded normal
+ deterministic 3D fBm-like sampling
+ genus-0 topological certificate
```

The intended use is explanatory and diagnostic:

- visual proof that the base projection is genus-0,
- clean boundary between control topology and residual/stress topology,
- portable example of “16D state, 4D axis, 3D witness.”

---

## Archive hygiene

The duplicate search-space copy of `PISTMachine.lean` was archived because the canonical active module is:

```text
0-Core-Formalism/lean/Semantics/Semantics/PISTMachine.lean
```

Archived copy:

```text
archive/2026-05-26/PISTMachine.lean.archived
```

Rationale:

```text
Avoid two active copies of the same namespace/module drifting apart.
```

---

## Current caution flags

1. **Build verification still required.** These updates were made through the GitHub connector; a local or CI `lake build` should still be run.
2. **Receipt semantics are intentional.** Do not reintroduce exact unit-norm theorem fields into the Q16.16 hot path unless a real normalization proof bridge exists.
3. **Genus-3 remains valid only at the residual/deep-topology layer.** The current 16D/4D/3D repair control spaces are genus-0.
4. **Do not bulk-delete documentation hits for `sorry` or `TODO`.** Many are audit history, UI labels, external code, or intentionally named tooling.

---

## Next recommended work

1. Run `lake build` for the affected Lean workspace.
2. Add a small CI/audit script that distinguishes:
   - active Lean proof holes,
   - documentation mentions of `sorry`,
   - UI routes named `sorry`,
   - quarantined files,
   - archive files.
3. Extend route-repair output receipts with:
   - `primary_obstruction`,
   - `secondary_obstruction`,
   - `chart_axis_4d`,
   - `patch_embed_3d`,
   - `residual_topology_signature`,
   - `invalid_goal_suspected`.
4. Keep the genus-0 sphere-shell demo as the canonical visual bridge for the control manifold.

---

## Keeper phrases

```text
The base repair manifold is genus 0; genus belongs to residual topology.
```

```text
Q16.16 quaternion operations carry unit receipts, not fake exact unit-norm proofs.
```

```text
Route repair works when theorem shape generates local proof surgery, not when ranking merely reorders flat tactic guesses.
```
