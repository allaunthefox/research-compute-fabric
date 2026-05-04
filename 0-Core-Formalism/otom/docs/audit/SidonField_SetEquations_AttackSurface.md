# Sidon Field Set Equations and Attack Surface

## Purpose

This note states the finite field-set equations for the Sidon/GCL-diff/compression/metaprobe stack and defines what the stack is attacking.

The target is not an infinite ideal. The target is a finite candidate field that can be audited, compressed, perturbed, diffed, and either promoted, held, scarred, quarantined, or routed into virtual nonseparable encoding.

## 0. Finite Universe

Work inside a finite interval:

```text
U_N = {0, 1, ..., N-1}
```

Candidate set:

```text
A = {a_1, ..., a_m} subset U_N
```

Indicator field:

```text
chi_A(n) = 1 if n in A, else 0
```

Density:

```text
rho_A = |A| / N
```

Sidon-normalized density:

```text
sigma_N(A) = |A| / sqrt(N)
```

The finite target is high `sigma_N(A)` with zero pair-sum collisions.

## 1. Classical Sidon / B2 Collision Field

Unordered pair-sum multiplicity:

```text
mu_+(s; A) = |{(a,b) in A x A : a <= b and a + b = s}|
```

Pair-sum collision field:

```text
K_+(s; A) = max(0, mu_+(s; A) - 1)
```

Total B2 collision energy:

```text
C_B2(A) = sum_s K_+(s; A)
```

Classical Sidon condition:

```text
A is Sidon iff C_B2(A) = 0
```

Attack target:

```text
Kill all duplicate unordered pair sums without collapsing |A|.
```

## 2. Difference / Golomb Collision Field

Difference multiplicity:

```text
mu_D(d; A) = |{(a,b) in A x A : a > b and a - b = d}|
```

Difference collision field:

```text
K_D(d; A) = max(0, mu_D(d; A) - 1)
```

Total difference collision energy:

```text
C_D(A) = sum_d K_D(d; A)
```

Golomb condition:

```text
A is Golomb iff C_D(A) = 0
```

Attack target:

```text
Kill repeated spacing echoes that create spectral aliases and mechanical ringing.
```

## 3. Spectral Field

Fourier fingerprint:

```text
S_A(k) = sum_{a in A} w_a exp(2*pi*i*k*a/N)
```

Power spectrum:

```text
P_A(k) = |S_A(k)|^2
```

Autocorrelation relation:

```text
P_A(k) is the Fourier transform of the difference multiset A - A
```

Important boundary:

```text
P_A probes differences, not pair sums directly.
Pair-sum uniqueness still requires C_B2(A) = 0.
```

Spectral void alignment:

```text
V_A = sum_k W_void(k) * P_A(k)
```

where `W_void(k)` weights spectral voids, defect bands, or admissible acoustic corridors.

Attack target:

```text
Find A whose spectral mass sits in survivable voids while avoiding repeated spacing aliases.
```

## 4. AMREF Residual Field

Carrier:

```text
f_N[n] = sin(2*pi*f0*n/Fs + phi0)
```

Set perturbation:

```text
P_A[n] = sum_{a in A} w_a sin(2*pi*a*n/N + phi_a)
```

Operated signal:

```text
g_N[n; epsilon, A] = f_N[n] + epsilon * P_A[n]
```

FFT:

```text
F_N[k; epsilon, A] = FFT(g_N[n; epsilon, A])
```

Music-filtered remainder:

```text
R_N[k; epsilon, A] = (1 - H_music[k]) * F_N[k; epsilon, A]
```

Residual energy:

```text
E_R(A, epsilon) = sum_k |R_N[k; epsilon, A]|^2
```

AMREF score:

```text
AMREF(A, epsilon) =
    lambda_R * E_R(A, epsilon)
  + lambda_V * V_A
  + lambda_T * T_ctrl(A)
  - lambda_M * M_music(A)
  - lambda_Omega * Omega_rand(A)
```

B2-hardened AMREF:

```text
AMREF_B2(A, epsilon) = AMREF(A, epsilon) - lambda_B2 * C_B2(A)
```

Attack target:

```text
Separate structured inverse-resonance from ordinary harmony, white noise, and arithmetic collision.
```

## 5. GCL Law-Profile Field

Let GCL mean a finite law profile, provisionally:

```text
GCL = Geometric / Cognitive / Compression Law profile
```

Candidate profile:

```text
GCL(A) = (
  G_geo(A),
  G_comp(A),
  G_load(A),
  G_spec(A),
  G_topo(A),
  G_arith(A)
)
```

Diff between candidates:

```text
Delta_GCL(A,B) =
    w_geo  * d_geo(G_geo(A), G_geo(B))
  + w_comp * d_comp(G_comp(A), G_comp(B))
  + w_load * d_load(G_load(A), G_load(B))
  + w_spec * d_spec(G_spec(A), G_spec(B))
  + w_topo * d_topo(G_topo(A), G_topo(B))
  + w_arith * d_arith(G_arith(A), G_arith(B))
```

GCL stability:

```text
Stab_GCL(A) = exp(-Delta_GCL(A, Perturb(A)))
```

Attack target:

```text
Detect candidates that look good only because representation, windowing, encoding, or metric choice changed.
```

## 6. Compression Field

Canonical encoding:

```text
enc(A) = canonical finite representation of A
```

Compression ratio, SI-style:

```text
CR(A) = original_size(enc(A)) / compressed_size(enc(A))
```

Compression delta:

```text
Delta_CR(A -> B) = CR(B) - CR(A)
```

Valid compression gain:

```text
ValidCompressionGain(A -> B) iff
  Delta_CR(A -> B) > theta_CR
  and C_B2(B) = 0
  and receipts(B) complete
  and no boundary conditions were deleted
```

Attack target:

```text
Reject fake compression that wins by deleting constraints, hiding collisions, or laundering randomness.
```

## 7. Metaprobe Field

Probe result:

```text
P(A) = result of a finite probe family on A
```

Metaprobe vector:

```text
Meta(P,A) = (
  WindowStability(P,A),
  PermutationStability(P,A),
  EncodingInvariance(P,A),
  NoiseRobustness(P,A),
  ReceiptPreservation(P,A),
  CounterexampleYield(P,A)
)
```

Metaprobe score:

```text
M_meta(P,A) =
    u_w * WindowStability(P,A)
  + u_p * PermutationStability(P,A)
  + u_e * EncodingInvariance(P,A)
  + u_n * NoiseRobustness(P,A)
  + u_r * ReceiptPreservation(P,A)
  + u_c * CounterexampleYield(P,A)
```

Attack target:

```text
Stop bad probes from certifying bad sets. Test the measuring instrument, not just the object measured.
```

## 8. FAM-Gated Ascent Field

For a route `r : A -> B`:

```text
EnergyAvailable(r) =
    eta_CR * ValidCompressionGain(r)
  + eta_R  * ResidualGain(r)
  + eta_V  * VoidFitGain(r)
  + eta_M  * MetaProbeSurplus(r)
  + eta_B  * BasinSupport(r)
  + eta_Q  * ReceiptIntegrity(r)
```

```text
AscentCost(r) =
    lambda_B2 * C_B2(B)
  + lambda_D  * C_D(B)
  + lambda_G  * Delta_GCL(A,B)
  + lambda_N  * Omega_rand(B)
  + lambda_T  * T_unctrl(B)
  + lambda_X  * MissingReceiptPenalty(B)
```

Ascent gate:

```text
CanAscend(A -> B) iff
  rank(B) > rank(A)
  and EnergyAvailable(A -> B) >= AscentCost(A -> B)
  and RequiredReceipts(B) pass
```

Attack target:

```text
Block unfunded promotion. A better-looking set must pay its arithmetic, compression, probe, and receipt costs.
```

## 9. Unified Sidon Field Score

```text
Score_SF(A) =
    alpha_B2   * (1 - norm(C_B2(A)))
  + alpha_D    * (1 - norm(C_D(A)))
  + alpha_R    * norm(E_R(A, epsilon))
  + alpha_V    * norm(V_A)
  + alpha_CR   * norm(CR(A))
  + alpha_GCL  * Stab_GCL(A)
  + alpha_meta * norm(M_meta(P,A))
  - alpha_rand * Omega_rand(A)
  - alpha_tors * T_unctrl(A)
```

Hard gate overrides:

```text
ClassicalSidonGate(A) iff C_B2(A) = 0
GolombGate(A) iff C_D(A) = 0
ProbeTrusted(P,A) iff M_meta(P,A) >= theta_meta
CompressionTrusted(A) iff compression preserves receipts
```

## 10. Virtual Sidon Escape Hatch

If classical Sidon fails:

```text
C_B2(A) > 0
```

route to nonseparable pair-state encoding:

```text
S_N(a,b) = Phi_N(a) + Phi_N(b) + Lambda_N(a,b)
```

Virtual Sidon injectivity:

```text
S_N(a,b) = S_N(c,d) -> {a,b} = {c,d}
```

Attack target:

```text
Do not pretend a colliding set is Sidon. Either reject it or lift it into a higher-dimensional nonseparable pair-state that proves injectivity.
```

## What We Are Attacking

### Primary enemy: pair-sum degeneracy

```text
a_i + a_j = a_k + a_l with {i,j} != {k,l}
```

This destroys classical Sidon uniqueness.

### Secondary enemy: spacing aliasing

```text
a_i - a_j = a_k - a_l with {i,j} != {k,l}
```

This creates repeated spectral echoes and fake stability.

### Tertiary enemy: harmonic collapse

```text
A relaxes into ordinary musical/harmonic structure
```

This means the candidate is not anti-music/inverse-resonant; it has fallen into a stable expected basin.

### Quaternary enemy: white-noise collapse

```text
A wins only by being random, not structured
```

This kills compressibility, lawfulness, and reuse.

### Quinary enemy: compression spoofing

```text
CR improves because constraints, receipts, or boundary conditions were deleted
```

This is fake ascent.

### Senary enemy: probe overfitting

```text
P certifies A only under one window, one encoding, or one metric choice
```

This means the probe is not trustworthy.

### Final enemy: unfunded ascent

```text
rank(B) > rank(A) but EnergyAvailable(A -> B) < AscentCost(A -> B)
```

This is the FAM failure mode: promotion without work.

## Minimal Implementation Targets

```text
sidon_collision.py       -> C_B2 and C_D counters
sidon_fingerprint.py     -> S_A, P_A, V_A
sidon_amref.py           -> R_N and AMREF_B2
sidon_gcl_diff.py        -> GCL(A), Delta_GCL(A,B)
sidon_compression.py     -> enc(A), CR(A), Delta_CR
sidon_metaprobe.py       -> M_meta(P,A)
SidonFieldGate.lean      -> gate predicates and finite theorem skeleton
```

## Audit Classification

```text
Receipt: SidonField_SetEquations_AttackSurface
Status: FIELD_EQUATION_DRAFT
Gate: U_scope
Reason: equations are finite and auditable, but require implementation, threshold calibration, and validator receipts before theorem promotion.
```
