# Quantum Foam Boundary

Status: `HOLD_FLUCTUATION_BOUNDARY`

Claim boundary: quantum foam is modeled here as a fluctuation/noise boundary
around `U0`. It does not promote a physical quantum-gravity theory, spacetime
engineering, Planck-scale access, cosmology fit, compression result, or hardware
claim.

## Role In The Stack

`U0` remains exact accounting closure:

```text
U0 closes iff O_visible + U_under + U_sink = 0
```

Quantum foam is the messy boundary case where the recomputed net charge is near
zero but not exact, or where a measurement floor/jitter band is being invoked.
It must never silently replace `U0`.

```text
exact U0:
  net_charge = 0
  replay_receipt_present = true

foam HOLD:
  abs(net_charge) <= declared_jitter_bound
  replay_receipt_present may be false

reject:
  abs(net_charge) > declared_jitter_bound
```

## Folded-Point Refinement

The model now distinguishes an observer-frame `0D` point from an empty point:

```text
0D in observer frame != zero internal structure
```

Quantum foam can therefore be held as an apparent-0D boundary while a separate
folded-point receipt declares whether it carries higher-dimensional interior
structure.

```text
apparent 0D point
  + internalDim witness
  + neutral closure
  + replay receipt
  + torsion potential
  -> folded-point candidate
```

This prevents two opposite errors:

```text
foam is nothing          -- too destructive
foam proves everything   -- too permissive
```

The finite Lean surface for this refinement is:

```text
0-Core-Formalism/lean/Semantics/Semantics/Core/FoldedPointManifold.lean
```

The stronger loopback rule is also there: after apparent `0D` resolution loss,
a receipted folded `16D` interior may be treated as a permeable return surface
only when `permeabilityDeclared = true`.

## Lanes

| Lane | Terminal | Use |
|---|---|---|
| `U_QFOAM_BOUNDARY` | `HOLD_QFOAM_BOUNDARY` | Net charge is inside a declared jitter or measurement band, but exact `U0` replay is absent. |
| `U_QFOAM_SCALE_UNDECLARED` | `HOLD_QFOAM_SCALE` | Foam language was used without a scale band, tolerance, or measurement floor. |
| `U_QFOAM_REJECT_MACRO_PROMOTION` | `REJECT_QFOAM_MACRO_PROMOTION` | Planck/sub-resolution fluctuation was promoted to a macro claim without renormalized evidence. |

## Lean Surface

```text
0-Core-Formalism/lean/Semantics/Semantics/Core/QuantumFoamBoundary.lean
```

Fixtures:

```text
exactZeroFixture   -> exactClosure
foamJitterFixture  -> holdFoam
outOfBandFixture   -> rejectClaim
```

## Working Rule

Quantum foam may explain why a local zero claim is noisy. It may not admit the
zero claim. Admission still requires exact `U0` replay, or a separate declared
renormalization/measurement model with its own receipt.

## Non-Claims

- No claim of direct Planck-scale measurement.
- No claim of quantum-gravity proof.
- No claim of spacetime engineering.
- No claim that foam creates usable energy or information.
- No cosmology, compression, or hardware promotion.
