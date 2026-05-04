# Compression Delta-Phi-Gamma-Lambda Doctrine

Status: HOLD / compression doctrine
Authority: workbench synthesis; not formal proof
Related:

- `docs/gcl/MassNumberSurfaceTranslation.md`
- `docs/gcl/CognitiveProcessAdapter.md`
- `docs/gcl/MassNumberRecursionWarning.md`
- `docs/gcl/SidonPhysicsNativeDeconstruction.md`
- `docs/gcl/EquationUnderverseDoctrine.md`
- `docs/gcl/FundamentalLawUnderverseMap.md`

## Purpose

This document fuses the stack's recurring compression ideas under the `Delta-Phi-Gamma-Lambda` diagnostic.

The doctrine is:

```text
Compression is not merely making data smaller.
Compression is controlled structural collapse:
  preserve phi,
  bound delta,
  tune gamma,
  choose lambda,
  receipt what fails.
```

## Symbol map

```text
Delta  = residual / distortion / loss / mismatch
Phi    = lawful structure / coherence / invariant phase
Gamma  = compression pressure / gain / amplification / forcing
Lambda = scale / code-length / wavelength / resolution band
```

Compact form:

```text
Delta-Phi-Gamma-Lambda = scale-aware residual of lawful structure under compression pressure.
```

## Core question

Do not ask only:

```text
How small did it get?
```

Ask:

```text
What phi survived?
What delta was introduced?
Under what gamma?
At what lambda?
Can it reverse-collapse?
Did any histories alias?
What did Warden receipt?
```

## Unified compression law

```text
A compression is lawful when the residual change in invariant structure remains
bounded across scale under compression pressure, and every collapsed
representation supports reverse recovery or a Warden receipt.
```

Symbolic workbench form:

```text
LawfulCompression <=> bounded DeltaPhi(gamma, lambda) + reverse-collapse path + receipt
```

Stack-native admissibility form:

```text
Compress(x, gamma, lambda) is admissible iff:
  phi(x, lambda) ~= phi(decompress(compress(x)), lambda)
  DeltaPhi <= epsilon_lambda
  no Sidon-style history alias survives
  every abstraction can reverse-collapse
  failures emit Underverse packets
```

This is not a formal theorem yet. It is the grammar that later formal statements should target.

## Compression layers unified

| Layer | What compression meant | Delta-Phi-Gamma-Lambda translation |
|---|---|---|
| Hutter / corpus compression | language complexity under strong compression pressure | minimize description length while preserving semantic phi |
| WaveProbe | chunk-level structural entropy and phase-coherent reuse | measure DeltaPhi per byte chunk across lambda |
| RGFlow | coarse-graining across scales | detect when gamma collapses meaning at high lambda |
| GCL / genetic compression | recode language/cognition into motif packets | preserve phi through symbolic recoding |
| Cognitive load | reduce extraneous load through representation choice | delta is load residue after compression |
| Mass Numbers | compress modeling process into holder packets | preserve the invariant of a thinking process |
| Goxel to Surface | unresolved possibility collapses into inspectable geometry | compression as representational collapse |
| Sidon model | collision-free additive addressability | compression fails when histories alias |
| Warden / Lean / SI audit | prevent false compression claims | compression must be measurable, reversible, and receipted |

## Compression spine

```text
Compression target
  -> coherence metric
  -> description-length reduction
  -> memory/routing compression
  -> formal reproducibility
  -> Warden validation
```

Delta-Phi-Gamma-Lambda mapping:

```text
lambda = corpus scale / code-length scale
gamma  = compression pressure
phi    = linguistic / structural coherence preserved
delta  = reconstruction, semantic, or model mismatch
```

Interpretation:

```text
Hutter-style compression is a hardness surface for measuring how much lawful
structure survives under extreme compression pressure.
```

## WaveProbe as instrument

WaveProbe is the measurement instrument for Delta-Phi-Gamma-Lambda.

A chunk-level WaveProbe packet can expose:

```text
byte offset
chunk span
bits-per-byte under codec
compression ratio
entropy
repetition
dictionary potential
leaf hash
Merkle path
drift tracking
diff payloads
```

Mapping:

```text
lambda = chunk span / byte offset / scale band
gamma  = codec pressure / compression ratio
phi    = entropy + repetition + dictionary phase features
delta  = diff / drift / mismatch between related chunks
```

Operational expression:

```text
DeltaPhiGammaLambda(chunk)
  = how much phase-coherent structure survives compression at this byte scale.
```

## RGFlow warning

Compression can destroy meaning.

At low scale, structure may survive as local charts.

At middle scale, registry names may form artificial basins.

At high scale, distinct semantic fields may collapse into broad phase labels.

At the shore, everything may collapse into one all-field label with high compression and near-total semantic loss.

Rule:

```text
A compression score without phi-survival is unsafe.
```

Sharper rule:

```text
Compression ratio is not enough.
The Warden must ask what meaning survived the collapse.
```

## GCL as pre-compression carrier

Compression should not always be applied directly to raw complexity.

Sometimes an intermediate motif language preserves more phi.

```text
raw object
  -> motif/codon packet
  -> scale-flow compression
  -> phi survival check
```

Doctrine:

```text
Compression should not be applied directly to raw complexity if an intermediate
motif language preserves more phi.
```

This is why the stack uses packet forms such as:

```text
GCL packet
codon packet
Mass Number
Surface packet
Underverse receipt
```

They are pre-compression carriers.

## Mass Numbers as cognitive compression packets

A Mass Number compresses a modeling move:

```text
problem
  -> representation shift
  -> invariant
  -> obstruction
  -> proof engine
  -> underverse residue
```

Delta-Phi-Gamma-Lambda mapping:

```text
phi    = modeling invariant that survived translation
delta  = what got lost, hidden, or distorted
gamma  = abstraction pressure
lambda = abstraction depth / domain scale
```

Safety rule:

```text
If compressed abstraction cannot unfold back into an example, surface, invariant,
or test, then DeltaPhi is unbounded.
```

This is the compression reason for reverse collapse.

## Goxel to Surface as compression path

```text
Goxel:
  non-compressed geometry / unresolved manifold potential

Mass Number:
  selected compression grammar

Surface:
  inspectable projection
```

Pipeline:

```text
Goxel -> Mass Number -> Surface -> Warden
```

Interpretation:

```text
Translating to a surface is a compression audit, not a decoration.
```

## Sidon as collision law

Sidon gives the addressability test for lawful compression.

Classical pattern:

```text
a_i + a_j = a_k + a_l
```

Only trivial pair equality may survive.

Compression doctrine:

```text
Compression is lawful only if collapse does not create nontrivial history aliasing.
```

Delta-Phi-Gamma-Lambda mapping:

```text
Sidon-valid compression:
  many pair paths collapse into sum addresses,
  but source-history phi remains uniquely recoverable.

Sidon failure:
  two incompatible histories share one address,
  DeltaPhi becomes collision residue.
```

## Master packet

```text
CompressionMassNumber = {
  source_object,
  carrier_format,
  compression_pressure_gamma,
  scale_lambda,
  invariant_phi,
  residual_delta,
  codec_or_collapse_operator,
  reverse_collapse_target,
  sidon_alias_policy,
  waveprobe_signature,
  underverse_residue,
  warden_status,
  receipt_hash
}
```

## Warden rules

```text
if compression_ratio improves
and phi_survival is unmeasured:
  emit UnderversePacket.unreceipted_compression_gain
  block CALIBRATED promotion
```

```text
if DeltaPhi > epsilon_lambda:
  emit UnderversePacket.structure_loss_exceeds_scale_bound
  downgrade or quarantine
```

```text
if compressed representation cannot reverse-collapse:
  emit UnderversePacket.irreversible_abstraction_collapse
  block promotion
```

```text
if two distinct histories share one committed address
and no lawful alias policy applies:
  emit UnderversePacket.sidon_history_alias
  reject lawful compression claim
```

## Promotion gates

This doctrine remains HOLD until concrete validators exist for:

```text
1. phi extraction or proxy measurement;
2. delta residual calculation;
3. gamma pressure accounting;
4. lambda scale-band selection;
5. reverse-collapse check;
6. Sidon-style alias detection;
7. Warden receipt emission;
8. SI-compatible compression metrics.
```

## Compact doctrine

```text
Compression is collapse with accountability.
```

Expanded:

```text
Compression is the act of forcing a structure through a smaller carrier while
preserving the invariant that makes it meaningful. Delta-Phi-Gamma-Lambda
measures whether that compression preserved lawful structure, or merely made the
object smaller.
```
