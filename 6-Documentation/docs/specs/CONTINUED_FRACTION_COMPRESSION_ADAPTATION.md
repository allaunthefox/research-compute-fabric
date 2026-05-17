# Continued Fraction Compression Adaptation

Status: Draft v0.1
Date: 2026-05-08
Scope: adapting ratio-heavy Research Stack math to exact continued-fraction carriers for compression
Claim state: formal scaffold and adaptation map; not a global compression benchmark, optimality proof, or floating-point numerical claim

## 1. Purpose

Continued fractions are useful for this stack when a value is naturally a ratio,
threshold, scaling law, phase increment, or calibration constant.

The compression opportunity is:

```text
rational value
  -> finite partial quotients
  -> compact integer stream
  -> exact replay to numerator / denominator
  -> residual if an approximation was chosen
  -> receipt
```

Lean anchor:

```text
0-Core-Formalism/lean/Semantics/Semantics/ContinuedFractionCompression.lean
```

The design stays vectorless and integer-only. It does not use embedding
similarity, floats, or decimal string parsing in the law layer.

## 2. Adaptable Math Surfaces

The repo already has several math lanes that can use continued fractions.

| Surface | Existing Shape | CF Adaptation |
|---|---|---|
| Fibonacci / phi ratios | `FibonacciEncoding.lean`, phi/golden scaling notes | all-ones partial quotients encode Fibonacci convergents |
| Golden-angle phase sampling | `GoldenAngleEncoding.lean` | approximate phase steps as rational carriers with byte-cost receipts |
| Recursive branch-cut ratios | `recursive_branch_cut_self_similarity.md` | scale ratios become partial-quotient streams instead of decimal prose |
| Fixed-point thresholds | Q0.16/Q16.16 gates and calibration constants | thresholds can be stored as `(partial_quotients, residual_bound)` |
| Sidecar byte law | logogram payload plus residual plus receipt accounting | CF route promotes only when encoded quotient stream beats baseline |
| Holographic boundary/bulk split | boundary descriptor plus exact residual | boundary ratio can be a compact CF descriptor with exact residual replay |

## 3. Core Equation

Finite continued fraction:

```text
[a0; a1, a2, ..., an]
```

Replay recurrence:

```text
evalCf([])        = 0 / 1
evalCf([a])       = a / 1
evalCf(a :: rest) =
  let n / d = evalCf(rest)
  (a*n + d) / n
```

Admission:

```text
partial quotients admissible
+ exact replay to target numerator / denominator
+ byte-sized quotient stream
+ residual and receipt bytes counted
+ encoded bytes < baseline bytes
```

## 4. Byte Law

For a continued-fraction packet:

```text
B(partial_quotients)
+ B(residual)
+ B(receipt)
< B(baseline numerator/denominator or decimal form)
```

If the inequality fails, the continued fraction can remain an inspection
surface, but it is not a compression promotion.

Important negative case:

```text
[1000] = 1000 / 1
```

This is exact but not one-byte quotient-sized. The current Lean witness rejects
it for the first hardware-friendly path.

## 5. Current Lean Witnesses

Verified examples:

```text
[1, 1, 1, 1, 1]     -> 8 / 5
[2, 1, 1, 1, 1]     -> 13 / 5
[10, 2]             -> 21 / 2
```

Witness outcomes:

```text
phiFivePacket                  promotable
phiSquaredPacket               promotable
tenPointFivePacket             promotable
largeQuotientPacket            not promotable
aestheticCfPacket              not promotable
promotable_cf_reconstructs     theorem
promotable_cf_satisfies_byte_law theorem
```

These witnesses prove the gate shape:

```text
compression promotion -> exact rational replay
compression promotion -> byte law satisfied
```

## 6. Where This Helps Most

### Phi / Fibonacci Surfaces

Your phi-heavy math is the cleanest match. The all-ones continued fraction:

```text
[1; 1, 1, 1, ...]
```

generates Fibonacci convergents:

```text
1/1, 2/1, 3/2, 5/3, 8/5, 13/8, ...
```

That gives a compact route for:

- phi/golden scale prompts
- golden-angle approximants
- recursive branch-cut candidate ratios
- dictionary thresholds that drift toward Fibonacci ratios

### Recursive Branch-Cut Ratios

The branch-cut document already says the ratios are not constant and cluster by
regime. Continued fractions are useful here because they make this explicit:

```text
ratio cluster
  -> exact rational carrier
  -> partial quotient pattern
  -> regime label
  -> residual for mismatch
```

This avoids pretending `Phi^2` is always the true scale factor. A ratio can be
stored exactly if known, or approximated with a declared residual.

### Logogram Sidecars

The sidecar path can use continued fractions for compact thresholds and local
ratio metadata:

```text
candidate dictionary route
  -> phrase length / residual size ratio
  -> CF packet
  -> sidecar decision
```

This is especially useful for corpus-trained agents that need to carry small
integer model parameters without vectors.

## 7. Compiler Integration

Proposed pipeline:

```text
numeric ratio / threshold / phase increment
  -> normalize to numerator / denominator
  -> continued fraction expansion
  -> choose quotient byte policy
  -> compute residual if truncated
  -> emit CF packet
  -> verify exact replay or declared residual
  -> promote only if byte law wins
```

For exact values, replay must recover the numerator and denominator byte-for-byte.

For approximate values:

```text
source rational
  -> convergent
  -> residual bound
  -> receipt
```

The approximation is lawful only when the residual is declared and replay can
recover either the original rational or the explicit residual sidecar.

## 8. LadderLUT: B-Adic Enumerative Shortcut

The `1 / 998001` pattern is useful as a design witness for a deterministic
enumerative LUT kernel:

```text
998001 = (1000 - 1)^2
1 / 998001 = 0.000001002003004005...
```

The decimal expansion is not the codec. It is the human-visible handle for this
family:

```text
base = radix^block_width
denominator = (base - 1)^2
emit fixed-width blocks by counting upward
```

Reference Lean gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/LadderLUT.lean
```

Canonical packet:

```text
LadderLUT =
  family
  radix
  block_width
  base
  start
  length
  generator_bytes
  residual_bytes
  receipt_bytes
```

Replay:

```text
value_i = (start + i) mod base
```

Admission:

```text
radix > 1
+ block_width > 0
+ base = radix^block_width
+ length > 0
+ generator_bytes + residual_bytes + receipt_bytes
   < length * block_width
```

The decimal witness:

```text
radix = 10
block_width = 3
base = 1000
denominator = 998001
replay starts 000,001,002,003,004,005,006,007,008,009
```

The compression-native version should usually be byte-based:

```text
radix = 256
block_width = 3
base = 256^3 = 16777216
```

Use cases:

- dictionary indices
- glyph IDs
- page-local token IDs
- table rows
- citation numbers
- ordered offset ladders
- semantic basin IDs
- Mass Number registry slots
- O-AVMR lane IDs

The carry behavior of the infinite decimal expansion is not promoted as a
codec rule. Carry-disturbed, skipped, permuted, or wrapped entries require a
declared residual stream.

## 9. HexLogogram Atlas: Seeded Grouping Shortcut

The hex version is stronger than a byte stream generator. A hexcode can seed a
deterministic logogram grouping field:

```text
hex seed
  -> grouping law
  -> Mass Number / type witness coordinates
  -> generated logogram group IDs
  -> residual exceptions
```

The seed does not store the words, glyphs, or semantic truth. It stores a
replayable law for assigning typed token coordinates into reusable logogram
groups.

Reference Lean gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/HexLogogramAtlas.lean
```

Canonical packet:

```text
HexLogogramAtlas =
  hex_seed
  hex_digit_width
  block_base = 16^hex_digit_width
  grouping_law
  registry_id
  mass_basin
  mass_weight
  chart_id
  type_witness
  group_count
  token_domain
  start_index
  length
  stride
  window
  assignment_bytes
  seed_bytes
  law_bytes
  registry_bytes
  residual_bytes
  receipt_bytes
```

Replay:

```text
raw_j = grouping_law(hex_seed, start_index + j, mass_basin, chart_id, type_witness)
group_j = raw_j mod group_count
```

Admission:

```text
hex_digit_width > 0
+ block_base = 16^hex_digit_width
+ registry_id > 0
+ group_count > 0
+ token_domain > 0
+ length > 0
+ stride > 0
+ window > 0
+ assignment_bytes > 0
+ seed_bytes + law_bytes + registry_bytes + residual_bytes + receipt_bytes
   < length * assignment_bytes
```

This promotes only when a seed-generated atlas beats the explicit
token-to-logogram assignment table.

Supported first-pass grouping laws:

| Law | Meaning |
|---|---|
| `atlasIdentity` | seed plus coordinate |
| `affineMass` | seed plus Mass basin, stride, and type witness |
| `windowedMass` | seed plus windowed coordinate and Mass/type fields |
| `stridedChart` | seed plus stride and chart witness |

Use cases:

- generated logogram group families
- page-local logogram clusters
- Mass Number basin grouping
- chart/type-witness lanes
- deterministic registry assignment maps
- substitution-table compression
- Hutter control-plane IDs

Residual policy is mandatory. If the generated grouping assigns a token to the
wrong logogram group, the exception must be carried in the residual stream. If
exceptions cost more than the explicit assignment table, the atlas stays HOLD.

## 10. Claim Boundary

## 10. OMCF / PIST Lift

The Mass-Gaussian lift turns continued fractions into a typed field carrier:

```text
z = R + iαM
```

where:

```text
R = structural carrier
    ratio, offset, recurrence, byte-law phase, numeric projection

M = Mass Number carrier
    semantic basin, topology class, glyph/domain class

α = Mass gauge
    scale factor that keeps semantic mass from dominating structure
```

The continued-fraction quotients live over Gaussian integers:

```text
a_j = x_j + i y_j,  a_j in Z[i]
```

with:

```text
x_j = structural quotient / braid twist count
y_j = Mass Number quotient / imaginary grouping motion
```

This gives the field object:

```text
OMCF<T> = (R + iαM, A, β, DEP, τ, Ω, ε)
```

where:

| Field | Meaning |
|---|---|
| `A` | Gaussian continued-fraction quotient list |
| `β` | braid / continuant path |
| `DEP` | deterministic expansion packet |
| `τ` | RRC type witness |
| `Ω` | O-AMVR or O-AVMR receipt |
| `ε` | semantic and byte residual repair |

PIST is the surface-transform operator family over this carrier:

```text
PIST_OMCF<T> = (z, A, β, Π, C, DEP, τ, Ω, ε)
```

where:

```text
Π = PIST transform operator
C = local SSROC/SROC operator cell, when used
```

PIST is not promoted because it is elegant. It is promoted only when its
operator ID, cell seed, expansion law, receipt, and residual cost pay for
themselves under the byte law.

## 11. Decoder-Facing Reconstruction Core

The compressed representation emitted by this family is not assembly language,
source code, or ordinary human-readable bytecode.

Canonical phrase:

```text
This is not assembly. It is a lawful reconstruction core.
```

The core is a decoder-facing representation whose validity is established by:

```text
deterministic replay
residual repair
receipts
byte-exact output
```

Direct readability of the internal representation is not a validity criterion.
This is not anti-inspection. Inspection moves to:

```text
codec specification
replay rules
receipts
residuals
hashes
benchmarks
reconstructed bytes
```

Related spec:

```text
6-Documentation/docs/specs/DECODER_FACING_RECONSTRUCTION_CORE.md
```

## 12. Control Filters

The OMCF/PIST reconstruction candidate is guarded by control filters:

| Filter | Function |
|---|---|
| `LoC/NES Monster` | rejects fake pattern, mirage, or overfit |
| `FYC Gate` | rejects impossible constrained-manifold traversal |
| `COUCH` | rejects unstable hysteresis or chaotic route dynamics |
| `Tree Fiddy` | bounds recursion, retries, and refinement depth |
| `BHOCS` | commits only bounded, replayable survivors |
| `FAMM` | carries delay/frustration-addressed memory pressure |

Admission sketch:

```text
Admit(X) =
  replay_valid(X)
  ∧ byte_gain(X) > 0
  ∧ residual_declared(X)
  ∧ LoC_NES_pass(X)
  ∧ FYC_pass(X)
  ∧ COUCH_stable(X)
  ∧ TreeFiddy_bounded(X)
  ∧ BHOCS_verified(X)
```

## 13. One-Symbol LUT Fuzzer

Formal power series and recurrence generators can fuzz the compression ratio by
collapsing a structured array into one replay law:

```text
array[n] = generator_law(n, parameters)
```

This is the "one symbol, massive array" route. It is lawful only when the
symbol is a declared generator, not a hidden copy of the array.

Receipt generator:

```text
4-Infrastructure/shim/one_symbol_lut_fuzzer_prior.py
```

First-pass generator families:

| Family | Generating Function / Law | Fuzz Role |
|---|---|---|
| arithmetic ladder | `x / (1 - x)^2` | carry-swallow and missing-coordinate stress |
| triangular ladder | `x / (1 - x)^3` | second-order acceleration stress |
| squares | `x(1+x) / (1 - x)^3` | curvature / distance-field stress |
| cubes | `x(1+4x+x^2) / (1 - x)^4` | volume-like coordinate stress |
| geometric | `1 / (1 - kx)` | exponential slot-overlap stress |
| Fibonacci | `x / (1 - x - x^2)` | recurrence / branching stress |
| Lucas mutation | `(2 - x) / (1 - x - x^2)` | recurrence-basin mutation stress |
| cyclic prime | `digits(1 / p)` | rotation-invariant window stress |
| repunit repeat | `c / (B - 1)` | obvious repetition baseline |
| Champernowne decoy | `123456789101112...` | pseudo-normal decoy from a tiny law |

Admission:

```text
B(generator_law)
+ B(parameters)
+ B(residual_exceptions)
+ B(receipt)
< B(explicit_array)
```

If the target array is random, the generator numerator, exception list, or
residual grows until it costs as much as the array. That is the entropy wall.

## 14. Claim Boundary

This adaptation does not prove that continued fractions improve full-corpus
compression. It identifies where the math is compatible:

```text
ratio-heavy
+ recurrence-heavy
+ threshold-heavy
+ integer-replay-friendly
```

The next empirical step is a corpus-side audit that measures whether CF packets
reduce sidecar/model-parameter bytes compared with raw numerators,
denominators, decimals, or fixed-point constants.

Likewise, LadderLUT does not prove that ordered IDs compress a corpus by
themselves. It promotes only when the deterministic generator plus residual and
receipt bytes beats the explicit fixed-width LUT.

Likewise, HexLogogramAtlas does not prove that a hex seed can recover all
semantic grouping. It is a deterministic grouping representative admitted only
when replay plus residual reconstructs the explicit logogram assignment table
more cheaply than storing that table directly.

Manifold Boundary Atlas applies the same seed-generated route to RRC boundary
candidate surfaces. It is not a proof of a manifold tear. It only emits
candidate coordinates for RRC to identify, and it promotes only when the
boundary seed plus residual and receipt bytes beats an explicit boundary list.
