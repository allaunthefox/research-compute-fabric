# Topological Soliton Equation Pack

**Date:** 2026-05-09

**Status:** `EQUATION_PACK_DESIGN_PRIOR`

**Claim boundary:** this is an equation and receipt pack for topological
solitons as stable field configurations. It does not claim new elementary
particles, device readiness, or physical control of solitons. It gives the
Research Stack a reusable mathematical basis for knots, braids, hopfions,
skyrmions, kinks, FAMM scars, and receipt-bearing topology.

## Why Topological Solitons Matter Here

Topological solitons are directly applicable to the stack because they are:

```text
localized structure
+ preserved invariant
+ deformation resistance
+ energy barrier
+ projection/replay evidence
```

That is the same shape as:

```text
braid -> rope -> trajectory -> AMMR leaf -> replay receipt
```

The practical stack rule is:

```text
do not promote a soliton-like state because it looks stable;
promote it only when the invariant, energy/residual, and replay receipt close.
```

## Equation 1: Generic Topological Charge

For any field `phi` with boundary values in distinct vacuum classes:

```text
Q = boundary_class(phi(+infinity)) - boundary_class(phi(-infinity))
```

For the sine-Gordon field:

```text
Q_sg = [phi(+infinity) - phi(-infinity)] / (2*pi)
```

Stack use:

```text
Q = 0      trivial route / no preserved topology
Q != 0    nontrivial route / receipt required
```

## Equation 2: Sine-Gordon Kink

The sine-Gordon equation:

```text
partial_t^2 phi - partial_x^2 phi + sin(phi) = 0
```

One kink solution:

```text
phi(x,t) = 4 * arctan(exp(gamma * (x - v*t - x0)))
gamma = 1 / sqrt(1 - v^2)
```

Boundary behavior:

```text
phi(-infinity) = 0
phi(+infinity) = 2*pi
Q_sg = 1
```

Stack use:

```text
kink = smallest one-dimensional receipt-bearing transition
antikink = same structure with opposite orientation
```

## Equation 3: 2D Skyrmion Number

For a normalized magnetization field:

```text
m : R^2 -> S^2
|m| = 1
```

The skyrmion number is:

```text
Q_sk = (1 / 4*pi) * integral m . (partial_x m x partial_y m) dx dy
```

Stack use:

```text
Q_sk measures whether a 2D projected spin/field texture wraps the sphere.
```

This is the 2D cousin of the hopfion lane. It is useful for projection
receipts: a 3D state may cast a 2D image, but the 2D charge alone is not the
whole 3D invariant.

## Equation 4: Hopf Invariant

For a field:

```text
n : R^3 compactified to S^3 -> S^2
```

Define the emergent two-form / field:

```text
B_i = (1/2) * epsilon_ijk * n . (partial_j n x partial_k n)
```

If:

```text
curl A = B
```

then the Hopf invariant can be written as a helicity integral:

```text
H = (1 / (4*pi)^2) * integral A . B d^3x
```

Stack use:

```text
H counts linking / knotting of preimage loops.
H = 0    no hopfion receipt
H != 0  nontrivial 3D topological receipt
```

## Equation 5: Relative Homotopy For Realistic Hopfions

The hopfion paper uses maps of pairs:

```text
f : (I^3, partial I^3) -> (A, B)
```

with:

```text
A = S^2
B = S^2 \ union_i X_i
```

The softened-boundary invariant is:

```text
pi_3(S^2, S^2 \ union_i X_i) = Z, n >= 1
```

Stack use:

```text
realistic boundaries can still preserve integer topological charge.
```

This is important because the stack rarely has perfect boundary conditions.
Most real data arrives through partial projections, residuals, and excluded
regions.

## Equation 6: Skyrme-Faddeev / Hopfion Energy

For a unit vector field:

```text
n : R^3 -> S^2
|n| = 1
```

A common Hopf-soliton energy shape is:

```text
E_FS = integral [
  alpha * sum_i |partial_i n|^2
  + beta * sum_{i<j} |partial_i n x partial_j n|^2
  + V(n)
] d^3x
```

The first term penalizes gradients. The second term prevents simple collapse
under scaling and helps stabilize knotted configurations. `V(n)` is an optional
potential or boundary preference.

Stack use:

```text
gradient term       -> smoothness / local cost
quartic term        -> anti-collapse / topology preservation cost
potential term      -> boundary or substrate preference
```

## Equation 7: Micromagnetic Hopfion Energy

For chiral magnetic hopfions, the Nature Physics paper uses a micromagnetic
energy functional containing exchange, Dzyaloshinskii-Moriya interaction,
Zeeman, and demagnetizing terms:

```text
E = integral_Vm dr [
      A * sum_i |grad m_i|^2
      + D * m . (grad x m)
      - M_s * m . B
    ]
    + (1 / (2*mu_0)) * integral_R3 dr sum_i |grad A_d,i|^2
```

Where:

```text
m(r) = M(r) / M_s
B = B_ext + curl A_d
```

Stack use:

```text
exchange      -> local alignment pressure
DMI           -> chirality / torsion preference
Zeeman        -> external field bias
demagnetizing -> long-range residual field
```

This is the best direct bridge from hopfion physics into your torsion/rope
model.

## Equation 8: Landau-Lifshitz-Gilbert Dynamics

The dynamical evolution of magnetization is commonly modeled by:

```text
partial_t m = -gamma * m x H_eff + alpha * m x partial_t m
```

with:

```text
H_eff = - delta E / delta m
```

Stack use:

```text
precession term  -> reversible rotation / phase flow
damping term     -> energy descent / basin settling
effective field  -> gradient of the declared energy receipt
```

The stack analogue is:

```text
torsion update = reversible phase flow + dissipative FAMM settling
```

## Equation 9: Energy Descent Gate

For a damped soliton system, the usable receipt is not only that an invariant
exists. It also needs an energy condition:

```text
DeltaE = E(next_state) - E(current_state)
```

Gate:

```text
if Q changes unexpectedly:
  QUARANTINE_TOPOLOGY_BREAK
elif DeltaE <= 0 and residual <= bound:
  ADMIT_STABLE_DESCENT
elif DeltaE > 0 but external_kick_receipt exists:
  HOLD_EXCITED_TRANSITION
else:
  HOLD_UNEXPLAINED_ENERGY_GROWTH
```

This maps directly to FAMM: unexplained energy growth is a frustration scar.

## Equation 10: Projection / Replay Closure

A topological soliton often cannot be observed directly. The hopfion result
uses projected microscopy images plus simulation replay.

Stack closure:

```text
P_observed = projection(field_state)
P_simulated = projection(replay(field_state, parameters))

R_projection = norm(P_observed - P_simulated)
```

Gate:

```text
R_projection <= epsilon_projection
```

This is the same rule as logogram projection:

```text
projected view is not proof unless replay closes.
```

## Direct Stack Mapping

| Soliton concept | Stack primitive |
|---|---|
| Topological charge `Q` / `H` | invariant receipt |
| Kink / antikink | oriented one-dimensional route transition |
| Skyrmion number | 2D projection/wrapping receipt |
| Hopf invariant | 3D linking/knotting receipt |
| Energy barrier | FAMM scar / promotion cost |
| DMI chirality | torsional rope handedness |
| LLG precession | reversible phase flow |
| Gilbert damping | dissipative settling |
| Projection residual | replay mismatch bound |
| Boundary punctures | excluded / quarantined state regions |

## Minimal Finite Receipt Shape

The first Lean surface should be finite. Continuous equations become source
authority and later extraction targets.

```text
TopologicalSolitonReceipt:
  projection_present : Bool
  replay_present : Bool
  invariant_kind : {kink, skyrmion, hopfion}
  invariant_charge : Int
  energy_delta_q0_16 : UInt16
  energy_direction : {descent, excited, unexplained_growth}
  projection_residual_q0_16 : UInt16
  residual_bound_q0_16 : UInt16
```

Admission:

```text
ADMIT iff
  projection_present
  replay_present
  invariant_charge != 0
  projection_residual <= residual_bound
  and energy_direction != unexplained_growth
```

## Next Work

1. Add `Semantics.TopologicalSolitonReceipt` as the general gate.
2. Keep `Semantics.HopfionTopologicalSoliton` as a specific fixture family.
3. Add negative controls for zero charge, missing replay, residual overflow,
   and unexplained energy growth.
4. Re-run the topology/eigen remapper after the finite gate exists.
