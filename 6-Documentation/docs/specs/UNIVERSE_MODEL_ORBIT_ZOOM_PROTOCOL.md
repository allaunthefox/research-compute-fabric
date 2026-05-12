# Universe Model Orbit-Zoom Protocol

Status: `DRAFT_RECEIPT_PROTOCOL`

Claim boundary: this is a navigation and receipt protocol for mapping a local
problem into the nearest mathematical continent. It does not claim that the
universe model uniquely proves the target math. It only defines how to zoom from
coarse structure to checkable local laws without losing the distinction between
assigned constants and derived consequences.

## Orbit View

Use the unified equation as the orbital map:

```text
Omega(n, theta, alpha) = Psi [ B(theta) tensor C(n, alpha) ] plus Delta(n, theta, alpha)
```

At orbit height, do not solve the problem. Classify it.

| Signal seen from orbit | Likely continent | First local tool |
|---|---|---|
| Symmetric basis, no residual | fixed point / equilibrium | invariant check |
| Basis mismatch | torsional stress / gradient flow | beta-step correction |
| Context changes faster than basis | dynamical systems | velocity / damping law |
| Residual grows | instability / turbulence / FAMM | recovery gate |
| Residual shrinks | Lyapunov descent | energy monotonicity witness |
| Repeated structures preserve shape | algebra / topology | isomorphism witness |
| Many small states fold into receipts | Merkle/MMR/AMMR | replay proof |

## Zoom Ladder

Every descent layer must answer one question before the next zoom is trusted.

```text
L0 Orbit:      What continent of math is this?
L1 Region:     Which local law family applies?
L2 State:      What variables are assigned?
L3 Derivation: What follows from the state?
L4 Receipt:    What can be replayed or refuted?
L5 Gate:       ADMIT, HOLD, or QUARANTINE
```

The most important distinction is:

```text
assigned value != derived value
```

Assigned values are initial conditions, coefficients, capacities, or declared
measurement scales. Derived values are consequences of the local law.

## Torsional Fluid Baseline

Current repo anchors:

```text
2-Search-Space/PIST/TorsionalPIST.lean
2-Search-Space/simulations/Newtonian-Superfluid-Simulation/custom_stack/superfluid_semantic_adapter.py
```

Assigned initial values:

```text
q1 = 1
q2 = 1
q3 = 1
eta = 1.0 Q16.16 = 0x00010000
energy = 0
velocity = 0
```

Derived local values:

```text
target = 0.5 * (q1 + q2) = 1
error = target - q3 = 0
attractForce = q2 - q1 = 0
correctionTorque = eta * error = 0
dimensionalTorque = eta * attractForce = 0
nextEnergy = norm(q1 - q2) + norm(error) = 0
```

So the correct baseline statement is:

```text
E0 = 0        assigned
v0 = 0        assigned
eta0 = 1      assigned
tau0 = 0      derived from symmetry
DeltaE0 = 0   derived from the beta-step law
```

## Continent Map For The Baseline

The torsional-fluid baseline lands in:

```text
fixed point / equilibrium
+ zero-torque manifold
+ Lyapunov candidate surface
+ dynamical-systems stability check
```

It does not land in turbulence, shock, or FAMM recovery until symmetry breaks.

## Pre-Fuzz Resolution

Before fuzz, the stack has two relevant resolution floors.

The arithmetic floor is the fixed-point lattice:

```text
Q16.16 epsilon = 1 raw unit = 1 / 65536 ≈ 0.0000152587890625
Q16.16 one     = 0x00010000 = 65536 raw units
```

That is the smallest representable Q16.16 perturbation. Any claimed change
smaller than one raw unit is below the deterministic lattice and must be treated
as fuzz, interpolation, or an external measurement prior.

The torsional convergence floor currently used by `TorsionalPIST_rgFlow` is:

```text
energy threshold = 0x00000100 = 256 raw units
                 = 256 / 65536
                 = 1 / 256
                 ≈ 0.00390625
```

So the pre-fuzz resolution is:

```text
numeric resolution:       1 / 65536
torsional settle gate:    1 / 256
```

Interpretation:

```text
0                         exact symmetric baseline
1 raw unit                smallest deterministic Q16.16 nudge
256 raw units             current torsional settle / no-more-zoom gate
anything below 1 raw unit fuzz-only
anything between 1 and 255 raw units deterministic but below current settle gate
anything at/above 256 raw units visible to the current torsional RG gate
```

This keeps fuzz honest. Fuzz is not allowed to invent a new baseline; it can
only probe below, around, or above a declared resolution gate.

## First Break Conditions

Use these as the first zoom-in tests:

| Condition | Meaning | Next math continent |
|---|---|---|
| `q1 != q2` | basis split | torsional stress |
| `q3 != 0.5 * (q1 + q2)` | product/residual mismatch | beta-step correction |
| `velocity != 0` | state is moving | dynamics / damping |
| `energy > 0` | stored deformation exists | Lyapunov descent or instability |
| `energy grows over steps` | correction is not settling | FAMM / turbulence recovery |
| `receipt missing` | cannot replay claim | HOLD |

## Receipt Shape

Minimum orbit-zoom receipt:

```json
{
  "protocol": "universe_model_orbit_zoom_v0",
  "orbit_class": "fixed_point_equilibrium",
  "local_law": "TorsionalPIST_torsionalBetaStep",
  "assigned": {
    "q1": "Quaternion.one",
    "q2": "Quaternion.one",
    "q3": "Quaternion.one",
    "eta_q16": "0x00010000",
    "energy_q16": "0",
    "velocity": "zero"
  },
  "derived": {
    "error": "0",
    "attractForce": "0",
    "correctionTorque": "0",
    "dimensionalTorque": "0",
    "nextEnergy": "0"
  },
  "decision": "ADMIT_BASELINE"
}
```

## Working Rule

The universe model is successful at orbit height if it can say:

```text
this belongs to this continent of math,
these are the assigned constants,
these values are derived,
these receipts are missing,
and this is the next local law to test.
```

It is not successful if it skips directly from metaphor to claimed theorem.
