# Projectable Geometry Compressor Spec

Status: draft v0.1
Date: 2026-05-08
Scope: compression architecture, symbolic geometry, reversible accounting
Primary claim boundary: this is not a physics theory, biological claim, financial claim, or proof of optimal compression. It is a receipt-gated compressor design for projectable geometry with explicit residual accounting.

## 1. Purpose

The compressor exists to edge the compression decimal by turning large structured objects into:

```text
shared projectable geometry
+ compact carrier symbols
+ bounded residual sidecars
+ exact rehydration receipts
```

The core objective is not to discover true physics. The core objective is:

```text
project -> preserve -> improve
```

Where:

```text
project:
  map a large object into a lower-dimensional control basis

preserve:
  track every displaced coordinate in a residual lane

improve:
  reduce per-instance cost once the shared model is amortized over a corpus
```

For a single object, the model cost may dominate. For a corpus, the test is:

```text
K(model) + K(residuals | model) < K(raw objects)
```

No compression claim is promoted until that inequality is benchmarked against baselines.

## 2. Provenance

This spec is grounded in the receipt chain built from the Standard Model Lagrangian term-family probe:

```text
equation wall
  -> 12D term-family source plane
  -> exact rational centroid
  -> signed 16-axis envelope
  -> 4D primitive keel
  -> 12D residual lane
  -> genus-3 residual boat
  -> force-regime model
  -> DNA carrier substitution
  -> absurd genetics stress
  -> extension failure boundary
```

Relevant receipt-bearing runners:

```text
4-Infrastructure/hardware/standard_model_lagrangian_exact_average.py
4-Infrastructure/hardware/standard_model_12_to_4_reduction.py
4-Infrastructure/hardware/standard_model_genus3_residual_boat.py
4-Infrastructure/hardware/standard_model_force_regime_model.py
4-Infrastructure/hardware/standard_model_dna_substitution_alignment.py
4-Infrastructure/hardware/standard_model_absurd_genetics_stress.py
4-Infrastructure/hardware/standard_model_extension_failure_probe.py
```

The design rule extracted from those receipts is:

```text
anything weird is allowed if it is reversible, conserved, and receipted
```

Reference Lean gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/ProjectableGeometryCanonical.lean
```

The Lean gate encodes the canonical dimensional representation and executable
negative witnesses for broken residual and unresolved-shell cases.

## 3. Core Objects

### 3.0 Canonical Dimensional Representation

The current canonical representation is:

```text
16D signed envelope
  -> 12D source/residual plane
  -> 4D primitive keel
  -> genus-3 residual boat
  -> 0D closure
```

Expanded accounting:

```text
16D signed envelope:
  12 exact source axes
  + 4 meta/control axes

12D source plane:
  unreduced canonical source coordinates

4D primitive keel:
  field / shear / packet / spectral

12D residual lane:
  source_12D - lift(project(source_12D))

genus-3 residual boat:
  three handle vectors carrying the residual lane

0D closure:
  no unresolved mass debt
```

The representation law is:

```text
source_12D =
  lift(project(source_12D))
  + residual_12D
```

The genus-3 residual carrier law is:

```text
packet_local
+ shear_torsion
+ spectral_field
= residual_12D
```

The dimensional shell closure prior prices the representation in twelfths:

```text
visible_4d = 4/12
shadow_3d  = 3/12
closure_0d = 1/12
lawbound   = 4/12
unresolved = 0/12
total      = 12/12
```

Promotion requires:

```text
axis counts match 16 -> 12 -> 4 -> 3 -> 0
shell mass closes with unresolved = 0
three residual handles sum to residual_12D
lifted_4D + residual_12D reconstructs source_12D
source hash is present
receipt hash is present
```

Failure cases:

```text
broken residual handle sum -> reject
unresolved shell mass debt -> reject
16D axes without typed semantics -> reject
genus-3 carrier without exact residual replay -> reject
```

Claim boundary:

```text
16D is a typed routing/witness envelope.
12D is a source/residual accounting plane.
4D is a compact primitive control keel.
3D is a three-handle residual carrier.
0D is closure, not deletion.
```

### 3.1 Source Plane

The source plane is the unreduced coordinate system for the current object family.

Example:

```text
12D source plane = twelve symbolic equation term-family axes
```

Requirements:

```text
source axes must be named
source vector must be canonicalized
source vector must have a stable hash
source vector must support exact or bounded numeric representation
```

### 3.2 Primitive Keel

The primitive keel is the compact control vector.

Current four-primitives basis:

```text
field
shear
packet
spectral
```

Interpretation:

```text
field:
  density/value surface coordinate

shear:
  gradient, coupling, torsion, transformation coordinate

packet:
  localized event, witness, claim, or receipt coordinate

spectral:
  eigenmode, covariance, resonance, and residual-spectrum coordinate
```

The primitive keel must be canonical and normalized for the target family:

```text
sum(primitive_keel) = 1
```

### 3.3 Projection Matrix

The projection matrix maps source axes into the primitive keel.

Minimum law:

```text
P : source_n -> primitive_4
rows(P) sum to 1
```

Projection is allowed to be lossy. Loss is lawful only if the residual lane is emitted.

### 3.4 Lift

The lift is the deterministic low-cost reconstruction from the primitive keel back into source coordinates.

The lift is not expected to recover the original source by itself.

```text
lift(project(source)) != source
```

Instead, the compressor must emit:

```text
residual = source - lift(project(source))
```

### 3.5 Residual Lane

The residual lane carries all displaced information required for exact rehydration.

Law:

```text
lift(project(source)) + residual = source
```

Acceptance:

```text
rehydration_l1_error = 0
```

For lossy modes, the receipt must explicitly mark the loss budget and the irreversible boundary.

### 3.6 Genus-3 Residual Boat

The genus-3 residual boat is the current structured residual bucket. It has three handle vectors:

```text
packet_local
shear_torsion
spectral_field
```

Law:

```text
packet_local + shear_torsion + spectral_field = residual
```

Metrics:

```text
hull_capacity_l1 = ||residual||_1
handle_l1
dominant_handle
zero_drift
closure_l1_error
```

Acceptance:

```text
three_handles_sum_to_residual = true
closure_l1_error = 0
zero_drift = true
```

The genus-3 boat is a residual carrier, not a cosmological topology claim.

### 3.7 Signed Envelope

The signed envelope records positive, negative, and origin/control coordinates.

Current test envelope:

```text
12 exact mirror axes
+ 4 meta/control axes
= 16 signed axes
```

Purpose:

```text
make projection distance navigable
record mirror closure
separate exact axes from measurement or residual axes
```

## 4. Carrier Alphabets

The compressor must separate the mathematical basis from the carrier alphabet.

Current compatible carrier:

```text
A -> field
T -> shear
G -> packet
C -> spectral
```

The carrier may be:

```text
binary tags
packed structs
glyphs
DNA-like bases
hachimoji-style extensions
Typst/logogram symbols
virtual baud symbols
```

Carrier substitution is lawful only when it preserves accounting.

## 5. Carrier Laws

### 5.1 Primitive Conservation

Decoded carrier vector must equal the primitive keel.

```text
decode(encode(primitive_keel)) = primitive_keel
```

Failure:

```text
primitive_roundtrip_error
```

### 5.2 Normalized Keel

Carrier mass must preserve the normalized primitive total.

```text
sum(carrier_keel) = 1
```

Failure:

```text
keel_total_not_one
```

### 5.3 Decode Completeness

Every active carrier symbol must have a decode rule.

Failure:

```text
nonzero_unmapped_extension_mass
missing_core_base_decode
```

### 5.4 Primitive Coverage

Every primitive must remain representable.

Failure:

```text
primitive_coverage_failure
primitive_loss
```

### 5.5 Residual Closure

Residual sidebands must close.

```text
sum(residual_sideband) = 0
```

unless explicitly carried as rehydration payload.

Failure:

```text
residual_drift
```

### 5.6 Fail Closed

Ambiguity must reject instead of silently decoding.

Failure:

```text
primitive collision
ambiguous aliasing
unknown primitive target
checksum/hash mismatch
```

## 6. Extension Boundary

Extra carrier bases or symbols are permissible only in three cases:

```text
inert:
  extra symbol carries zero mass

decoded split:
  extra symbol carries mass but maps back to an existing primitive exactly

balanced sideband:
  extra residual sideband carries signed mass but sums to zero
```

Forbidden extension behavior:

```text
untracked extension mass
primitive collisions
missing decode rules
residual drift
primitive loss
ambiguous aliasing
```

This boundary is receipt-backed by:

```text
4-Infrastructure/hardware/standard_model_extension_failure_probe.py
```

## 7. Virtual Baud Reconstruction Layer

The decompressor should be treated as a signal reconstruction path.

Pipeline:

```text
compressed archive
  -> framing decoder
  -> virtual baud reconstruction layer
  -> control-bit interpreter
  -> glyph/kernel dispatch
  -> primitive keel reconstruction
  -> residual boat replay
  -> exact output
```

Lanes:

```text
DATA:
  carrier symbols, literals, glyph/eigen descriptors

CTRL:
  mode switches, kernel dispatch, page/domain framing

CLOCK:
  frame/tick boundaries, phase buckets, resync points

REPAIR:
  residual bytes, correction vectors, patch ops

WITNESS:
  hashes, type witnesses, closure checks, receipts
```

One virtual baud tick is:

```text
one admissible reconstruction event
```

Examples:

```text
emit literal
switch carrier alphabet
apply primitive projection
replay residual handle
verify frame hash
resync stream
```

The baud layer is architectural only if it constrains parsing and recovery. If it merely names a metaphor, it is not part of the codec.

## 8. Packet Shape

The general packet shape is:

```text
PGC1 packet =
  magic/version
  family id
  source basis id
  projection id
  carrier alphabet id
  primitive keel payload
  residual boat payload
  extension sideband payload
  witness/checksum/hash trailer
```

The current finance-claim harness uses `FCL1/FCS1` for a narrower payload family. `PGC1` is the proposed general projectable geometry compressor envelope. It should not replace `FCL1/FCS1` until it can reproduce or improve those receipts.

## 9. Compression Gain Test

A candidate packet is accepted only if its expected gain is positive after decoder cost.

```text
gain =
  baseline_size
  - (
      model_reference_cost
      + projection_payload_size
      + carrier_payload_size
      + residual_payload_size
      + witness_payload_size
      + amortized_decoder_cost
    )
```

Accept:

```text
gain > 0
```

Keep but mark exploratory:

```text
gain <= 0
and structural receipts pass
```

Reject:

```text
rehydration fails
carrier laws fail
baseline comparison missing
claim boundary missing
```

## 10. Codec Baselines

Every benchmark receipt should compare:

```text
canonical JSON or canonical source bytes
zlib
CBOR when available
MessagePack when available
Protobuf/Nanopb-style schema when available
FlatBuffers-style schema when available
packed-struct/custom bitpack
projectable geometry packet
```

Missing optional libraries are skipped, not failures.

No competitive claim is allowed until the corpus is larger than a toy sample set.

## 11. Receipts

Every compressor run emits a JSON audit envelope even if the wire format is binary.

Required receipt fields:

```text
schema
generated_utc
surface_id
source hashes
basis ids
projection ids
carrier alphabet ids
primitive keel
residual lane
residual boat
extension sidebands
closure checks
roundtrip checks
benchmark table
claim boundary
stable hash
timestamped receipt hash
lawful
```

Stable hashes exclude timestamp-only fields. Timestamped receipt hashes include the generated timestamp.

## 12. Failure Codes

Minimum failure vocabulary:

```text
bad_magic
unsupported_version
bad_checksum
unknown_basis
unknown_projection
unknown_carrier
missing_decode_rule
primitive_roundtrip_error
keel_total_not_one
nonzero_unmapped_extension_mass
primitive_coverage_failure
primitive_loss
residual_drift
residual_closure_error
rehydration_l1_error
baseline_missing
gain_not_positive
claim_boundary_missing
```

Failures that affect exactness must fail closed.

## 13. Implementation Phases

### Phase 0: Freeze Laws

Deliverables:

```text
this spec
wiki tiddler
failure vocabulary
receipt schema draft
```

### Phase 1: General Harness

Build a projectable geometry compressor harness that can read a source vector, projection matrix, carrier map, and residual policy.

Commands:

```text
encode
decode
verify
bench
stress-carrier
stress-extension
```

### Phase 2: Binary Envelope

Define `PGC1` as a compact binary envelope.

Required tests:

```text
bit flip rejects
unknown carrier rejects
missing residual rejects
extension mass leak rejects
exact rehydration passes
```

### Phase 3: Corpus Benchmarks

Run over multiple object families:

```text
FinancialClaimPacket
symbolic equation graphs
DNA/base sequence surfaces
Typst/logogram render packets
```

### Phase 4: Optimization

Optimize projection matrices and carrier alphabets:

```text
local search
H200 burst optimizer dry-run, then optional rented run
noisy recovery simulator
virtual baud decoder profiling
```

### Phase 5: Committee Evidence

Export:

```text
Jupyter Book chapter
receipt bundle
benchmark tables
failure-mode appendix
claim-boundary appendix
```

## 14. Acceptance Gates

A compressor candidate is lawful only if:

```text
source canonical hash is recorded
projection rows satisfy stated laws
primitive keel roundtrips
residual lane rehydrates exactly
genus/residual carrier closes
carrier alphabet is bijective or explicitly extended lawfully
extension sidebands are inert, decoded, or balanced
bad mappings fail closed
benchmark baselines are present or explicitly skipped
claim boundary is present
```

The current known positive evidence:

```text
12D -> 4D reduction closes with exact residual rehydration
genus-3 residual boat closes with zero drift
DNA carrier substitution aligns exactly
absurd genetics lawful cases survive
broken non-bijective carrier fails closed
extension failure boundary is identified
```

The current known limitation:

```text
This has not yet demonstrated competitive compression over a large corpus.
It has demonstrated structural stability and exact accounting under carrier recoding.
```

## 15. Non-Claims

This spec does not claim:

```text
new physics
genomic physics
biological implementation
financial correctness
legal/audit validity
compression superiority
Kolmogorov optimality
Hutter Prize competitiveness
```

It claims only a design:

```text
projectable geometry with explicit residual accounting can be made carrier-stable
and fail-closed under known extension failures.
```
