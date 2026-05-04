# Hydrogenic Phi-Torsion Braid

Status: FORMING

## Purpose

This spec formalizes the hydrogenic Phi-torsion braid as a parametric manifold:

```text
Fibonacci spine -> hydrogenic 2s constraint groove -> Phi torsion -> stair/event trace
```

The object is not a literal atom simulation. It is a generation surface that exposes how a scale-delayed mass-number event cell was produced.

## Parameters

```text
theta       continuous state/evolution parameter
phi         (1 + sqrt(5)) / 2
r0          initial radius
a0          Bohr-radius-like scale
R_tube      torsion amplitude
k           logarithmic growth constant
```

There are two useful growth gauges:

```text
k_code       = (2 / pi) * ln(phi)
k_steep      = (pi / 2) * ln(phi)
```

`k_code` matches the original Python generator. `k_steep` matches the steeper derivation form and climbs faster. Treat this as a gauge choice, not a hidden correction.

## 1. Base Fibonacci Expansion

```text
r_base(theta) = r0 * exp(k * theta)
```

This is the unconstrained manifold expansion.

## 2. Hydrogenic 2s Constraint Groove

Normalize the base radius into hydrogenic scale:

```text
rho(theta) = r_base(theta) / a0
```

Use the topology-shape form of the 2s radial wavefunction:

```text
psi_2s(rho) = (2 - rho) * exp(-rho / 2)
D_topology(rho) = psi_2s(rho)^2
                = (2 - rho)^2 * exp(-rho)
```

The node is:

```text
rho = 2
r_base = 2a0
```

The constrained radius is:

```text
R_c(theta) = r_base(theta) * normalize(D_topology(rho(theta)))
```

If physical radial probability is desired instead of topology shape:

```text
D_radial(rho) = r_base(theta)^2 * psi_2s(rho)^2
```

The current braid uses `D_topology` because it makes the node act as a hard geometric groove.

## 3. Planar Spine

```text
x_spine(theta) = R_c(theta) * cos(theta)
y_spine(theta) = R_c(theta) * sin(theta)
```

## 4. Phi Torsion

The canonical torsion phase is:

```text
gamma(theta) = phi * theta
```

The UI/generalized generator can split this into:

```text
gamma(theta)       = radial_torsion * theta
alpha(theta)       = angular_torsion * theta
```

Canonical mode sets:

```text
radial_torsion = phi
angular_torsion = 1
```

The screenshot/user-control mode used:

```text
radial_torsion = 5
angular_torsion = 3
```

## 5. Final Position Vector

Canonical equation:

```text
P(theta) =
[
  R_c(theta) * cos(theta) + R_tube * cos(phi * theta) * cos(theta),
  R_c(theta) * sin(theta) + R_tube * cos(phi * theta) * sin(theta),
  R_tube * sin(phi * theta)
]
```

Generalized UI equation:

```text
P(theta) =
[
  R_c(theta) * cos(theta) + R_tube * cos(gamma(theta)) * cos(alpha(theta)),
  R_c(theta) * sin(theta) + R_tube * cos(gamma(theta)) * sin(alpha(theta)),
  R_tube * sin(gamma(theta))
]
```

## 6. Stair/Event Lift

For the FPGA/event-cell trace, keep a second z channel:

```text
stair_period = (2pi) / stair_divisions
stair_index(theta) = floor((gamma(theta) - gamma(0)) / stair_period)
z_stair(theta) = R_tube * sin(gamma(theta)) + stair_index(theta) * stair_rise
```

The bounded channel `z_torsion` preserves the braid. The monotonic channel `z_stair` exposes the climb.

## 7. Generation Trace Fields

The generated data should retain:

```text
theta
r_base
rho
D_topology
D_radial
R_c
gamma
alpha
stair_index
stair_phase
strain = abs(gradient(R_c, theta))
emitted_amplitude = abs(gradient(z_stair, theta)) * selected_constraint
P(theta)
P_stair(theta)
```

These fields are the bridge from visual manifold to fixed-point FPGA event cells.

## 8. Color Rope Mapping

The braid can be combined with the CMYK rope concept by treating each color
channel as a typed load path through the generated equation trace:

```text
C = constraint / monitor channel
M = evidence / verification channel
Y = residual / prune channel
K = admissible action / stable axis channel
```

For hard-math triage:

```text
C <- orbital groove constraint
M <- attached evidence mass
Y <- residual risk + proof debt
K <- admissible mass + lattice pressure
```

This turns a visual braid into a color-coded routing object. If `Y` dominates,
the rope is fraying and the state should remain residue or be pruned. If
`C + M + K` dominates `Y`, the state may be eligible for promotion, provided
the fracture and evidence thresholds also pass.

## 9. Fractionalized Tensegrity Configuration

The core equation should be split into load-bearing members:

```text
fibonacciSpine
orbitalGroove
planarSpine
phiTorsion
stairLift
strainField
emissionPacket
colorRope
```

The default tensegrity skeleton uses pull/compression edges:

```text
fibonacciSpine --tension--> orbitalGroove
orbitalGroove --compression--> phiTorsion
phiTorsion --tension--> stairLift
stairLift --tension--> strainField
strainField --compression--> emissionPacket
emissionPacket --tension--> colorRope
```

Each member carries a Q0.16-style load. Each edge compares its current load
difference or compression average against a rest length. Total strain becomes
the sieve's structural stress signal.

This is the hard-math use: do not ask whether a whole problem is solved. Split
the problem into typed members, let the members strain each other, and route the
state as:

```text
stable signal
residue
quarantine
no-CFD route
```

## Why It Does Not Close

When `radial_torsion = phi`, the torsion phase is irrational relative to the spine phase:

```text
cos(phi * theta) does not synchronize with cos(theta)
```

The result is an unclosed braid: bounded by the hydrogenic constraint groove, but not periodic in the ordinary spine frame.
