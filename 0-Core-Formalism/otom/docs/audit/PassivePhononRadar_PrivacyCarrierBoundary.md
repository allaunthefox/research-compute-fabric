# Passive Phonon Radar: Privacy-Carrier Boundary

## Purpose

This note records the bounded version of the Monero-like phononic carrier analogy under the Sidon/Golomb/AMREF/GCL/FAM stack.

The useful model is a signal-integrity and privacy-resilience audit over finite carrier-mediated propagation fields.

The unsafe/overstrong model is deterministic source localization or transaction de-anonymization.

## Core Correction

Do not claim:

```text
If C_B2(A)=0 and C_D(A)=0, the probability density collapses to the true origin node.
```

Allowed claim:

```text
If C_B2(A)=0 and C_D(A)=0, one class of arithmetic ambiguity and repeated-spacing aliasing has been removed from the finite candidate field. This may improve signal separability, but it does not by itself identify a real-world source.
```

The Sidon/Golomb receipts are collision audits, not attribution proofs.

## Bounded Carrier Model

Let the carrier domain be a finite abstract medium:

```text
M_N = {x_0, x_1, ..., x_{N-1}}
```

Background carrier field:

```text
Phi_0(x,t)
```

Injected perturbation field:

```text
psi_A(x,t) = sum_{a in A} w_a exp(i(k_a · x - omega(k_a)t + phi_a))
```

Total observable field:

```text
Psi(x,t) = Phi_0(x,t) + epsilon * psi_A(x,t) + eta(x,t)
```

where `eta(x,t)` is measurement noise, background randomness, or unmodeled carrier traffic.

## Dispersion Model

Use a generic phononic/metamaterial-style dispersion relation:

```text
omega(k) = c_s |k| + gamma |k|^3
```

Interpretation:

```text
c_s    -> baseline propagation speed / latency scale
gamma  -> nonlinear dispersion / torsion / obfuscation-like spreading
```

This is an analogy layer, not a validated network law.

## Finite Active Set

From the field, define a finite active set:

```text
A_t(theta) = { i in M_N : |grad Psi(i,t)| >= theta }
```

This set becomes the object audited by Sidon/Golomb probes:

```text
A := A_t(theta)
```

## Collision Audits

Pair-sum multiplicity:

```text
mu_+(s;A) = |{(a,b) in A x A : a <= b and a+b=s}|
```

Sidon collision energy:

```text
C_B2(A) = sum_s max(0, mu_+(s;A)-1)
```

Difference multiplicity:

```text
mu_D(d;A) = |{(a,b) in A x A : a > b and a-b=d}|
```

Golomb collision energy:

```text
C_D(A) = sum_d max(0, mu_D(d;A)-1)
```

Interpretation:

```text
C_B2(A) > 0 -> additive ambiguity among active-cell combinations
C_D(A) > 0  -> repeated-spacing echoes, aliases, or range-like ambiguity
```

## B2-Hardened AMREF Operator

Rather than treating AMREF as a literal quantum observable, treat it as a finite scoring operator:

```text
AMREF_B2(A, epsilon) =
    lambda_R * E_R(A, epsilon)
  + lambda_V * V_A
  + lambda_T * T_ctrl(A)
  - lambda_M * M_music(A)
  - lambda_Omega * Omega_rand(A)
  - lambda_B2 * C_B2(A)
```

The operator does not subtract a scalar collision count from a wavefunction. It scores finite candidate fields and penalizes collision debt.

## Reverse-Filter Score

A bounded reverse-filter score can be written as:

```text
P_score(x0,t0) =
  V_A * | sum_k H_safe(k) * S_hat(Psi)(k) * exp(i(omega(k)t0 - k·x0)) |^2
```

where:

```text
H_safe(k)       -> admissible filter mask
S_hat(Psi)(k)   -> filtered/smoothed spectral observation
V_A             -> spectral void alignment score
```

This is a score over model states, not a deterministic source claim.

## FAM-Gated Promotion

A route from observation to claim has the form:

```text
Observation -> Candidate Active Set -> Stable Propagation Pattern -> Claim
```

Promotion requires:

```text
CanAscend(r) iff
  EnergyAvailable(r) >= AscentCost(r)
  and C_B2(A) is audited
  and C_D(A) is audited
  and MetaProbeScore(P,A) >= theta_meta
  and RequiredReceipts(A) pass
```

with:

```text
AscentCost(r) =
    lambda_B2 * C_B2(A)
  + lambda_D  * C_D(A)
  + lambda_N  * Omega_rand(A)
  + lambda_G  * Delta_GCL(A, baseline)
  + lambda_X  * MissingReceiptPenalty(A)
```

## Correct Gate Outcomes

```text
PASS:
  finite signal-integrity hypothesis survives collision, alias, compression, GCL, and metaprobe audits

HOLD:
  candidate is coherent but not attribution-grade

SCAR:
  repeated ambiguity or metric failure recurs across windows

QUARANTINE:
  model overclaims, deletes uncertainty, or converts weak metadata into deterministic identity
```

## What This Model Attacks

```text
additive ambiguity
repeated spacing echoes
spectral aliasing
ordinary carrier behavior mistaken for perturbation
white-noise collapse
compression spoofing
single-window overfit
unfunded inference from metadata to identity
```

## Boundary

This note does not provide:

```text
network attack methods
traffic capture procedures
node placement strategies
de-anonymization workflows
transaction tracing instructions
operational source localization
```

Allowed use:

```text
privacy-preserving simulation, defensive signal-integrity auditing, synthetic phononic/metamaterial modeling, and finite mathematical probe design.
```

## Audit Classification

```text
Receipt: PassivePhononRadar_PrivacyCarrierBoundary
Status: BOUNDED_MODEL_CORRECTION
Gate: U_scope
Reason: useful finite signal-integrity analogy, but deterministic source localization is not justified by Sidon/Golomb receipts and is outside the safe/validated claim boundary.
```
