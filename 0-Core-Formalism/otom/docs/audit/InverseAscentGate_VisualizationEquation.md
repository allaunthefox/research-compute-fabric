# Inverse Ascent Gate Visualization Equation

## Purpose

This note records the visualization form of the Anti-Music / Mass-Number / Inverse Ascent gate.

The graph is a compact conceptual model for how collision debt, aliasing, randomness, and missing receipts reduce available promotion energy.

## Screenshot Equation

The conceptual plot uses:

```text
AvailableEnergy(x) = 12 - x^2
AscentThreshold = 5
```

where:

```text
x = normalized audit debt
  = collision debt + alias debt + randomness debt + receipt debt
```

The gate crossing is:

```text
12 - x^2 = 5
x^2 = 7
x = sqrt(7) ≈ 2.646
```

So:

```text
PASS region: x <= sqrt(7)
HOLD/REJECT region: x > sqrt(7)
```

The point:

```text
(3.16, 2)
```

lies below the threshold because:

```text
12 - 3.16^2 ≈ 2.0144 < 5
```

This is a correctly rejected candidate: the debt load is too high for promotion.

## Audit-Debt Variable

Define normalized audit debt:

```text
x(A) =
    a_B2 * norm(C_B2(A))
  + a_D  * norm(C_D(A))
  + a_N  * norm(Omega_rand(A))
  + a_T  * norm(T_unctrl(A))
  + a_G  * norm(Delta_GCL(A, baseline))
  + a_X  * norm(MissingReceiptPenalty(A))
```

## Available Energy Curve

The visual curve is:

```text
E_avail(x) = E_0 - alpha * x^2
```

For the screenshot:

```text
E_0 = 12
alpha = 1
```

The quadratic term means debt is superlinear: small collision debt may be survivable, but stacked debt rapidly collapses promotion energy.

## Ascent Gate

```text
CanAscend(A) iff
  E_avail(x(A)) >= theta_ascent
  and RequiredReceipts(A) pass
```

For the screenshot:

```text
theta_ascent = 5
```

Therefore:

```text
CanAscend(A) iff
  12 - x(A)^2 >= 5
  and RequiredReceipts(A) pass
```

Equivalent:

```text
x(A) <= sqrt(7)
```

## Field Interpretation

```text
Anti-Music Residual -> creates structured promotion energy
Mass-Number         -> stores audited informational inertia
Collision Debt      -> subtracts promotion energy
Inverse Ascent      -> blocks unfunded rank promotion
```

## Why the Curve Should Be Concave Down

A concave-down available-energy curve is appropriate because audit debt compounds:

```text
one weak receipt is manageable
one Sidon collision is local debt
many weak receipts plus collisions produce nonlinear collapse
```

This matches the intended model:

```text
The system should not be linearly forgiving when multiple independent failure modes stack.
```

## Stronger General Form

```text
E_avail(A) =
    eta_AM * M_AM_star(A)
  + eta_CR * ValidCompressionGain(A)
  + eta_V  * VoidFit(A)
  + eta_G  * GCLStability(A)
  + eta_P  * MetaProbeScore(P,A)
  + eta_Q  * ReceiptIntegrity(A)
  - alpha * x(A)^2
```

```text
CanAscend(A) iff
  E_avail(A) >= theta_ascent
  and C_B2(A) = 0 for classical Sidon promotion
  and RequiredReceipts(A) pass
```

## Hard Boundary

The visualization does not replace the hard Sidon audit.

```text
C_B2(A)=0
```

remains required for classical Sidon promotion.

The curve only visualizes the larger FAM-gated promotion economy.

## Boundary

Allowed use:

```text
synthetic carrier simulation
finite mathematical probe design
privacy-preserving signal-integrity auditing
defensive robustness testing
```

Do not use or describe this as:

```text
source-localization proof
network attack method
transaction tracing workflow
de-anonymization implementation
```

## Audit Classification

```text
Receipt: InverseAscentGate_VisualizationEquation
Status: VISUAL_MODEL_RECEIPT
Gate: U_scope
Reason: useful visualization of the gate economy; requires calibrated metrics, synthetic examples, and Lean predicates before theorem promotion.
```
