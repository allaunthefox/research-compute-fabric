# Sidon Field Probe: GCL Diff / Compression / Metaprobe Integration

## Purpose

This note returns to the Sidon-field stack and combines it with the newer FAM-gated ascent machinery plus the GCL diff / compression / metaprobe probe family.

The goal is to use Sidon fields as finite candidate structures and then probe them through:

```text
GCL diff        -> local/global change signal between candidate states
compression     -> nonredundancy and explanatory efficiency test
metaprobe       -> second-order probe that tests whether the probe itself is lawful
FAM ascent      -> energy/receipt gate for promotion
FAMM/IFAMM      -> route memory and missing-receipt search
```

I did not find a canonical file defining `GCL` in the connected repos/Drive search, so this note treats GCL as a project-local probe term to be wired to the intended implementation later. Suggested expansion here: `Geometric/Cognitive/Compression Law` diff, depending on the exact module you want to bind.

## Core Statement

A Sidon field becomes useful when it is not just a set with unique pair sums, but a finite structure that survives multiple independent probes:

```text
pair-sum audit
spectral/remainder resonance
compression delta
GCL diff stability
metaprobe self-consistency
FAM-gated ascent
```

The central rule:

```text
A Sidon candidate may ascend only if it is arithmetically nonredundant,
compressively useful, geometrically stable under diff, and probe-stable under metaprobe.
```

## Sidon Field Object

For a finite candidate set:

```text
A = {a_1, ..., a_m} subset {1, ..., N}
```

Classical Sidon receipt:

```text
C_B2(A) = sum_s max(0, mult_{A+A}(s)-1)
A is Sidon iff C_B2(A) = 0
```

Difference/Golomb receipt:

```text
C_D(A) = sum_d max(0, mult_{|A-A|}(d)-1)
A is Golomb iff C_D(A) = 0
```

Spectral fingerprint:

```text
S_A[k] = sum_{a in A} w_a exp(i * 2*pi*k*a/N)
P_A[k] = |S_A[k]|^2
```

Reminder:

```text
P_A exposes A-A directly. A+A still needs explicit B2 audit.
```

## GCL Diff Layer

Let `GCL(A)` be the finite law-profile of candidate `A`.

A generic law-profile can include:

```text
GCL(A) = {
  graph_geometry(A),
  compression_profile(A),
  cognitive_load_profile(A),
  spectral_void_profile(A),
  topological_defect_profile(A),
  arithmetic_collision_profile(A)
}
```

Given two states `A` and `B`, define:

```text
GCLDiff(A,B) = distance(GCL(A), GCL(B))
```

Decomposed:

```text
GCLDiff(A,B) =
    w_geo  * GeometryDiff(A,B)
  + w_comp * CompressionDiff(A,B)
  + w_load * CognitiveLoadDiff(A,B)
  + w_spec * SpectralDiff(A,B)
  + w_topo * TopologyDiff(A,B)
  + w_arith * ArithmeticDiff(A,B)
```

Interpretation:

```text
low GCLDiff under admissible perturbation -> stable field candidate
high GCLDiff with receipt-preserving improvement -> useful transition
high GCLDiff with receipt loss -> scar/quarantine candidate
```

## Compression Layer

Compression is the anti-flatness test.

For a finite encoding `enc(A)`:

```text
CR(A) = original_size(A) / compressed_size(enc(A))
```

Standardized SI-style convention:

```text
higher CR is better
compression_percentage = (original - compressed) / original * 100
```

Compression delta across candidate transformation:

```text
DeltaCR(A -> B) = CR(B) - CR(A)
```

Use compression as evidence only if it preserves receipts:

```text
ValidCompressionGain(A -> B) iff
  DeltaCR(A -> B) > theta_CR
  and C_B2(B) = 0
  and required_receipts(B) pass
  and no boundary conditions were deleted
```

Compression cannot fund ascent if it works by erasing the constraints that made the problem hard.

## Metaprobe Layer

The metaprobe tests the probe, not just the set.

For a probe `P` applied to set `A`:

```text
ProbeResult = P(A)
```

Metaprobe asks:

```text
MetaProbe(P,A) = {
  stability_under_windowing,
  stability_under_permutation,
  stability_under_noise_floor,
  invariance_under_encoding,
  receipt_preservation,
  counterexample_yield
}
```

Metaprobe score:

```text
MetaProbeScore(P,A) =
    u_w * WindowStability(P,A)
  + u_p * PermutationStability(P,A)
  + u_e * EncodingInvariance(P,A)
  + u_r * ReceiptPreservation(P,A)
  + u_c * CounterexampleYield(P,A)
  - u_n * NoiseSensitivity(P,A)
```

A probe is trusted only if:

```text
MetaProbeScore(P,A) >= theta_meta
```

## Combined Sidon Probe Score

Define:

```text
SidonFieldScore(A) =
    alpha_B2   * (1 - normalize(C_B2(A)))
  + alpha_D    * (1 - normalize(C_D(A)))
  + alpha_R    * RemainderResonance(A)
  + alpha_V    * VoidFit(A)
  + alpha_CR   * CompressionGain(A)
  + alpha_GCL  * GCLStability(A)
  + alpha_meta * MetaProbeScore(P,A)
  - alpha_rand * RandomnessPenalty(A)
  - alpha_tors * UncontrolledTorsion(A)
```

Hard gates should override score:

```text
if C_B2(A) != 0 and claim is classical Sidon:
  reject or route to virtual nonseparable encoding

if RandomnessPenalty(A) > theta_rand:
  quarantine as noise

if MetaProbeScore(P,A) < theta_meta:
  hold; probe is not trusted
```

## FAM-Gated Ascent Integration

Use the previously defined ascent law:

```text
CanAscend(r) iff
  rank(y) > rank(x)
  and EnergyAvailable(r) >= AscentCost(r)
  and RequiredReceipts(r) pass
```

For Sidon fields:

```text
EnergyAvailable(A -> B) =
    ValidCompressionGain(A -> B)
  + RemainderResonanceGain(A -> B)
  + VoidFitGain(A -> B)
  + MetaProbeSurplus(A -> B)
  + BasinSupport(A -> B)
```

```text
AscentCost(A -> B) =
    lambda_B2 * C_B2(B)
  + lambda_D * C_D(B)
  + GCLDiffPenalty(A,B)
  + RandomnessPenalty(B)
  + UncontrolledTorsion(B)
  + MissingReceiptPenalty(B)
```

Promotion rule:

```text
B can become a basin candidate only if:
  C_B2(B) = 0
  EnergyAvailable(A -> B) >= AscentCost(A -> B)
  MetaProbeScore(P,B) >= theta_meta
  receipts(B) complete for the requested gate
```

## Virtual Sidon Escape Hatch

If `C_B2(A) > 0`, the candidate is not classical Sidon. It may still be tested as a virtual Sidon object via nonseparable encoding:

```text
S_N(a,b) = Phi_N(a) + Phi_N(b) + Lambda_N(a,b)
```

Virtual injectivity receipt:

```text
S_N(a,b) = S_N(c,d) -> {a,b} = {c,d}
```

This creates:

```text
ClassicalSidonGate
VirtualSidonGate
QuarantineNoiseGate
```

## Pipeline

```text
1. Generate or import finite candidate A.
2. Run SumSetReceipt: compute C_B2(A).
3. Run DifferenceSetReceipt: compute C_D(A).
4. Compute spectral fingerprint P_A.
5. Compare against filtered remainder R_N.
6. Compute GCL(A) law profile.
7. Apply GCLDiff against baseline or previous candidate.
8. Encode/compress A and compute valid compression delta.
9. Run metaprobe on the probe family.
10. Apply FAM-gated ascent.
11. Route outcome to FAMM / Inverted FAMM.
```

## FAMM Outcomes

```text
PASS:
  arithmetic receipts pass, compression gain valid, metaprobe stable, ascent funded

HOLD:
  candidate is coherent but missing receipts or has unresolved GCL torsion

SCAR:
  repeated collision, compression spoofing, or invariant obstruction

QUARANTINE:
  randomness collapse, deleted constraints, probe instability, or adversarial shortcut

MISSING:
  no finite witness yet; create a task rather than evidence
```

## Minimal Implementation Targets

```text
sidon_collision.py       -> C_B2 and C_D counters
sidon_fingerprint.py     -> S_A and P_A spectra
sidon_gcl_diff.py        -> law-profile diff
sidon_compression.py     -> canonical encoding and CR/DeltaCR
sidon_metaprobe.py       -> probe-stability checks
SidonFieldGate.lean      -> finite gate predicates
```

## Minimal Lean Shape

```lean
structure SidonProbeState where
  cB2 : UInt32
  cD : UInt32
  compressionGainQ16 : UInt32
  gclStabilityQ16 : UInt32
  metaProbeQ16 : UInt32
  randomnessPenaltyQ16 : UInt32
  receiptsComplete : Bool

inductive SidonGate where
  | classicalSidon
  | virtualSidon
  | hold
  | scar
  | quarantine

def ClassicalSidonReady (s : SidonProbeState) : Bool :=
  s.cB2 == 0 &&
  s.metaProbeQ16 >= 0x00008000 &&
  s.randomnessPenaltyQ16 <= 0x00004000 &&
  s.receiptsComplete
```

## Boundary

Do not claim:

```text
compression proves Sidon
GCL diff proves Sidon
metaprobe proves Sidon
spectral fingerprint proves pair-sum uniqueness
```

Allowed claim:

```text
GCL diff, compression, and metaprobe layers provide independent finite probes that help decide whether a Sidon-field candidate is worth promoting, holding, quarantining, or routing into virtual nonseparable encoding.
```

## Audit Classification

```text
Receipt: SidonField_GCLDiffCompressionMetaprobe
Status: PROBE_INTEGRATION_DRAFT
Gate: U_scope
Reason: coherent integration of arithmetic, compression, diff, and metaprobe layers; requires implementation of finite counters, encoders, thresholds, and Lean gate before promotion.
```

## Required Receipts

```text
SumSetReceipt
DifferenceSetReceipt
SpectralFingerprintReceipt
GCLProfileReceipt
GCLDiffReceipt
CompressionEncodingReceipt
CompressionGainReceipt
MetaProbeReceipt
RandomnessPenaltyReceipt
FAMAscentReceipt
FAMMUpdateReceipt
LeanGateReceipt
```
