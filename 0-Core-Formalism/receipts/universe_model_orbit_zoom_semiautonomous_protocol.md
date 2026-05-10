# Universe Model Orbit-Zoom Semiautonomous Protocol

Status: `DRAFT_RECEIPT_PROTOCOL`

Claim boundary: this is a navigation, routing, and receipt protocol for mapping local problems into the nearest mathematical continent. It does not claim that the universe model uniquely proves the target math. It defines how to zoom from coarse structure to checkable local laws while preserving the distinction between assigned constants and derived consequences.

## Core Doctrine

The universe model is allowed to classify and route. It is not allowed to smuggle assigned constants into derived consequences.

```text
Orbit view classifies the continent.
Zoom view checks the law.
Receipts separate assigned constants from derived consequences.
No theorem may be claimed from metaphor alone.
```

## Semiautonomous Stack

```text
phi-PrimeBeat ping
  -> soft prime-kernel collision
  -> torsional-fluid response
  -> witness packet
  -> Equation Sniffer classification
  -> BHOCS if stable
  -> FAMM if unresolved or scarred
  -> Underverse if excluded, failed, unpaid, or residual
  -> Warden receipt check
  -> ADMIT, HOLD, or QUARANTINE
```

This permits semiautonomous navigation because the system can propose next local laws and inspection targets from typed receipts, but it may not promote a route into a theorem without replayable evidence.

## Orbit Equation

```text
Omega(n, theta, alpha)
  = Psi [ B(theta) tensor C(n, alpha) ]
  + Delta(n, theta, alpha)
  + K(n, theta, alpha)
```

Where:

- `Psi [B tensor C]` is the projected basis-context interaction.
- `Delta` is the ordinary residual.
- `K` is the cantankerous / obstruction field: useful wrongness only when bounded, typed, and replayable.

Useful obstruction:

```text
K_useful = K * admissibility * closure_nearness * receipt_validity
```

Bad obstruction:

```text
unbounded K or missing receipt -> QUARANTINE
```

## Phi-PrimeBeat Probe

The phi-filtered sine wave supplies irrational pressure; primes supply collision points; the residual beat tells FAMM where the manifold may be hiding structure.

```text
phi = (1 + sqrt(5)) / 2
s_phi(n) = sin(omega*n + theta) * W_phi(n)
W_phi(n) = cos(2*pi*n/phi)
I_phi(n) = s_phi(n) * P(n)
```

For adjacent probing near known equations, use a soft prime kernel rather than a hard prime-only comb:

```text
K_sigma(n) = sum_p log(p) * exp(-(n - p)^2 / (2*sigma^2))
a_phi(n) = A * sin(2*pi*n/phi + theta) * K_sigma(n)
```

## Torsional Fluid Baseline

Assigned initial values:

```text
q1 = Quaternion.one
q2 = Quaternion.one
q3 = Quaternion.one
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

Canonical baseline statement:

```text
E0      = 0 assigned
v0      = 0 assigned
eta0    = 1 assigned
tau0    = 0 derived from symmetry
DeltaE0 = 0 derived from the beta-step law
```

The baseline is fixed point / equilibrium + zero-torque manifold + Lyapunov candidate surface. It does not land in turbulence, shock, or FAMM recovery until symmetry breaks.

## First Break Conditions

```text
q1 != q2                         -> basis split / torsional stress
q3 != 0.5 * (q1 + q2)             -> product/residual mismatch / beta-step correction
velocity != 0                     -> dynamics / damping
energy > 0                        -> stored deformation / Lyapunov descent or instability
energy grows over steps            -> FAMM or turbulence recovery
receipt missing                    -> HOLD
assigned value presented as derived -> QUARANTINE
metaphor presented as theorem       -> QUARANTINE
```

## Adjacent Ping Near TorsionalPIST

Known area:

```text
TorsionalPIST / RGFlow / zero-torque equilibrium
```

Adjacent perturbation:

```text
q1 = 1
q2 = 1 + delta
q3 = 1
eta = 1

delta = A * sin(2*pi*n/phi + theta) * K_sigma(n)
```

Derived response:

```text
target = 1 + delta/2
error = delta/2
attractForce = delta
correctionTorque = delta/2
dimensionalTorque = delta
nextEnergy = 1.5 * abs(delta)
```

Interpretation:

```text
zero-torque equilibrium
  -> small torsional stress
  -> beta-step correction candidate
  -> Lyapunov descent check
```

If beta-step dissipates energy and receipts replay, ADMIT_LOCAL_CORRECTION. If the residual forms a bounded stable scar, HOLD_AS_SCAR and route to FAMM. If energy grows unbounded, receipt is missing, or an assigned value is treated as derived, QUARANTINE.

## Equation Sniffer Routing

The phi-prime probe pings the Equation Forest, but the Equation Sniffers decide what kind of trail the ping produced.

```text
PrimeBeat Probe: creates the ping
Torsional Fluid: carries the twist response
Witness Hierarchy: packets the measurable reaction
Equation Sniffers: classify the scent trail
BHOCS: stores stable witnesses
FAMM: follows unresolved scars
Underverse: accounts for excluded / failed / unpaid reaction
Warden: validates the receipt
```

Sniffer roles:

- CarrierSniffer: dominant route such as TorsionalPIST, RGFlow, PrimeFold.
- TextureSniffer: residual motifs such as phi-beats, prime-gap scars, composite scars.
- BasinSniffer: local continent drift.
- AdapterSniffer: bridges between nearby equation regions.
- MonsterSniffer: symmetry-heavy anomalies that are useful but dangerous.
- MarketSniffer: shared behavioral operators across domains.

## Underverse and Inverse Fermat Gate

The Underverse is the existing negative ledger for residuals, complements, forbidden states, failed bindings, unpaid cost, and unrepresented structure.

```text
U(E) = residual(E) + complement(E) + forbidden(E) + failed(E) + unrepresented(E)
```

Dimensional ascent is gated by the Inverse Fermat payment rule:

```text
DimensionalAscentAllowed iff

front_charge
+ evidence_energy
+ compression_gain
+ basin_support

>=

torsion_cost
+ translation_loss
+ instability_penalty
+ receipt_gap
+ underverse_debt
```

If the inequality fails, the dimension is not promoted. The reaction bleeds into the Underverse, a FAMM scar is recorded, and a receipt is emitted.

## Minimum Receipt

```json
{
  "protocol": "phi_prime_adjacent_ping_v0",
  "known_area": "TorsionalPIST_zero_torque_equilibrium",
  "query_kind": "adjacent_soft_prime_kernel",
  "claim_boundary": "navigation_not_proof",
  "assigned": {
    "q1": "1",
    "q2": "1 + delta",
    "q3": "1",
    "eta": "1",
    "energy": "0",
    "velocity": "0",
    "delta": "A * sin(2*pi*n/phi + theta) * K_sigma(n)"
  },
  "derived": {
    "target": "1 + delta/2",
    "error": "delta/2",
    "attractForce": "delta",
    "correctionTorque": "delta/2",
    "dimensionalTorque": "delta",
    "nextEnergy": "1.5 * abs(delta)"
  },
  "orbit_class": "torsional_stress_adjacent_to_fixed_point",
  "first_local_tool": "beta_step_correction",
  "gate": "HOLD_UNTIL_REPLAY"
}
```

## Semiautonomous Safety Rule

Semiautonomous means the system may propose pings, local tools, routing targets, and FAMM inspection candidates from receipts. It may not self-admit a theorem, erase Underverse debt, promote a dimension without Inverse Fermat payment, or treat metaphor as proof.

```text
ADMIT only when assigned/derived separation is preserved and the receipt replays.
HOLD when a required receipt, provenance, or derivation is missing.
QUARANTINE when an assigned value is presented as derived, a metaphor is used as a theorem, or residual growth is unbounded.
```

Keeper phrase:

```text
The primes are the depth charges.
The torsional fluid is the medium.
The phi-wave supplies irrational pressure.
The Equation Sniffers classify the scent.
The Underverse gets the bill.
FAMM follows the scar.
Warden checks the receipt.
```