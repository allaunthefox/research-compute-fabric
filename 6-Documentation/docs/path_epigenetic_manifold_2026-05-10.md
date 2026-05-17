# Path-Epigenetic Manifold Regulation

Status: `LEAN_RECEIPT_SURFACE`

Claim boundary: this is a finite state model for a 1D routed carrier path that
regulates a 16D manifold through explicit markers. It does not claim biological
equivalence, nanometer fabrication readiness, ASIC readiness, compression gain,
or physical circuit validation.

## Core Idea

A 1D circuit/logogram path can act like an epigenetic control strand:

```text
stable 1D carrier path + mutable regulatory markers -> selected 16D expression
```

The path itself is not rewritten every time behavior changes. Instead, local
markers on the path decide which dimensions of the 16D manifold are expressed,
damped, witnessed, or routed to quarantine.

```text
path change   != manifold rewrite
marker change = expression rewrite
```

## Folded-Point Source

This surface can be fed by the folded-point model:

```text
apparent 0D point
  -> folded interior dimensional witness
  -> torsion potential
  -> 1D regulatory carrier path
  -> 16D manifold expression
```

So the path does not need to contain the whole 16D manifold directly. It can be
the regulatory carrier that selects which folded degrees of freedom become
active.

## 16D Packet

The first Lean surface declares these addressable dimensions:

| Dimension | Meaning |
|---|---|
| `identity` | Symbol or packet identity. |
| `route` | Carrier-route expression. |
| `scale` | Declared scale band. |
| `phase` | Local phase expression. |
| `torsion` | Twist/chirality/load expression. |
| `curvature` | Route/manifold bending expression. |
| `energy` | Normalized work/load value. |
| `velocity` | Normalized change-rate value. |
| `residual` | Scar, error, or repair residue. |
| `semanticMass` | SMN-style semantic load. |
| `confidence` | Gate confidence or admissibility weight. |
| `density` | Local occupancy/compression-density hint. |
| `topology` | Topology class or closure expression. |
| `witness` | Receipt/replay closure expression. |
| `underverse` | Quarantine/complement accounting lane. |
| `time` | Version, rotation, or update index. |

All first-pass dimensions are Q0.16 normalized expression levels.

## Marker Actions

Each 1D site carries one finite marker:

| Action | Meaning |
|---|---|
| `activate` | Set a target dimension to the marker strength. |
| `damp` | Set a target dimension to zero. |
| `gateWitness` | Close the witness dimension when the marker receipt is present. |
| `quarantine` | Route strength into `underverse` and `residual`. |

Layout failure also routes into `underverse` and `residual`, because a physical
or geometric route violation is not allowed to silently mutate the manifold.

## Decision Gate

```text
layout violation or explicit quarantine marker -> QUARANTINE
layout clear but missing marker receipt         -> HOLD
all markers receipted and layout-clear          -> ADMIT
```

This keeps the model from treating a pretty path as a valid transition. The
path has to be layout-clear and receipted before it can alter manifold
expression.

## Lean Surface

```text
0-Core-Formalism/lean/Semantics/Semantics/Core/PathEpigeneticManifold.lean
```

Executable fixtures:

```text
admittedPath       -> torsion activates and witness closes
holdPath           -> missing receipt leaves torsion unchanged and emits HOLD
quarantinePath     -> layout violation routes residual/underverse and emits QUARANTINE
```

## Design Rule

The circuit-path analogy becomes useful when the logogram is treated as a routed
cell:

```text
stroke/path segment -> route
width/spacing       -> scale/layout gate
bend/crossing       -> torsion/curvature
loop closure        -> witness
defect              -> residual and Underverse
```

The current implementation is a finite semantic/layout gate, not a fabrication
DRC. A future hardware lane can lower these fields into a real layout checker
only after physical spacing, units, process rules, and test receipts exist.

## Non-Claims

- This does not prove a biological epigenetic equivalence.
- This does not claim DNA, hachimoji, or molecular execution.
- This does not claim nanometer circuit manufacturability.
- This does not claim ASIC readiness.
- This does not claim compression improvement.
- This does not claim physical routing correctness beyond the finite Lean gate.
