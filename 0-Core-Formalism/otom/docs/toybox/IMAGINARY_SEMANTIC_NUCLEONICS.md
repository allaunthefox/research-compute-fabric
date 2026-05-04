# ToyBox: Imaginary Semantic Nucleonics

Status: `BEAUTIFUL_PROVISIONAL / TOYBOX_SPECIFICATION`

This page preserves the current ToyBox ruleset for **Imaginary Semantic Nucleonics**: a claim-bounded coordinate system for structured undefinedness, split-word addressing, POISC projection, mirrored-π calibration fields, prime-mass diagnostic nuclides, and KTT mirror-π mass-field modulation.

## Claim boundary

Safe claims:

- This is a toy-model rule system for testing structured undefinedness.
- Semantic mass is a dimensionless address/provenance quantity, not physical mass.
- Mirrored π is a deterministic calibration stream, not a replacement for ordinary π.
- `PROJECT_SORT` proposes witness behavior; verifiers decide admissibility.
- KTT is a phonetic-phase toy operator applied to a deterministic mirror-π carrier, not hidden mathematics in a song.

Unsafe claims:

- π literally changes, turns, or has physical orientation.
- Semantic mass is SI physical mass.
- Superposition searches all memory for free.
- Collapse sorting solves arbitrary problems.
- Quantum behavior is solved or explained away.
- The Shikanoko / koshitantan lyric contains intentional trigonometric content.

## Canonical stack

```text
Underverse shell history H
→ Semantic Nuclide {}^{A(H)}_Z C_φ
→ ConceptMassNumber lane
→ POISC split-word address
→ PROJECT_SORT
→ VirtualSubstrate / GeometryShaver
→ harmonic selection / collapse sorting
→ residual witness Ω
→ AVMR receipt
→ LawfulnessFunctional Φ
```

## Semantic Nuclide

Canonical form:

```text
{}^{A(H)}_Z C_φ
```

Meaning:

- `Z` = identity anchor / nucleus interface
- `A(H)` = semantic mass number / carried invariant-load from history `H`
- `φ` = phase, residue, curvature, valence, or local interaction signature
- `C` = concept family

Example:

```text
{}^{A(H)}_4 Π_13 ⇔ ...7654.13
```

Definition:

> A Semantic Nuclide is a POISC-addressable concept atom: its anchor `Z` defines identity, its mass number `A(H)` compresses Underverse history, its phase `φ` defines local interaction, and AVMR records whether projection preserves, transforms, or quarantines that concept isotope.

## POISC

Expanded name:

```text
POISC = Projection-Oriented One Instruction Set Computer
P-POISC = Photonic Projection-Oriented One Instruction Set Computer
```

Canonical instruction:

```text
PROJECT_SORT W, P, S, N -> (A, Ω, H_digest, F)
```

Operands:

- `W` = split word
- `P` = projection / substrate program
- `S` = collapse-sort schema
- `N` = shot count or sample budget

Outputs:

- `A` = accepted state
- `Ω` = residual / exhaust witness
- `H_digest` = histogram or witness digest
- `F` = flags

Execution:

```text
θ = encode(W)
U = load_projection(P, θ)
Y = sample_or_project(U, N)
B = collapse_sort(Y, S)
Ω = residual_mass(B)
H_digest = digest(Y, B)
F = flags(B, Ω)
```

Flags:

```text
ACCEPT
EXHAUST
COLLISION
SATURATED
LOW_CONFIDENCE
QUARANTINE
REPLAY_REQUIRED
```

## Split-word harmonic selection

Split-word principle:

```text
Left word  = History / Mass / Address / Context
Right word = Phase / Result / Local Observable
Anchor     = active gate / identity interface
```

Generic state:

```text
|Ψ⟩ = Σ_i α_i |History_i, Anchor_i, Phase_i⟩
```

Acceptance rule:

```text
accept(W) iff resonance(Phase(W), History(W), Anchor(W), Program) ≥ threshold
```

This is a validation relation, not a fixed arithmetic law.

## NaN fields and undefined concept carriers

A NaN field is not absence of value. It is a structured object whose directional components are lawful but whose scalar projection is invalid.

Undefined Concept Carrier:

```text
{}^{A(H)}_Z C_{φ}^{NaN}
```

Meaning:

> A concept anchored at `Z`, carrying history mass `A(H)`, emitting phase `φ`, and preserving a structured NaN witness.

Collapse bins for undefined concepts:

```text
DEFINED
PARTIALLY_DEFINED
BILATERAL_NaN
CONTEXT_DEPENDENT
SELF_CONTRADICTORY
REQUIRES_HISTORY
QUARANTINE
```

## Field squeezing

Field Squeezing treats impossible scalar results as diagnostics of the field, not merely failures of the object.

Protocol:

```text
impossible result
→ detect scalar-collapse failure
→ preserve NaN witness
→ squeeze/expand/rebase/invert/fold/shear number field
→ retry projection
→ classify as lawful, unstable, divergent, or quarantine
```

Formal rule:

```text
Given object X and field F:

if project_F(X) = NaN:
    emit Ω_NaN
    try F' = transform(F)
    classify project_F'(X)
```

Receipt invariant:

```text
Every field transformation must preserve a receipt.
```

## Mirrored π as deterministic calibration field

Mirrored π is useful because it is a defined digit stream. It gives a deterministic calibration object for scalar-invalid but field-valid states.

Canonical indexed object:

```text
Π_NaN(p) = reverse(π_tail up to p) ⊕ pivot(p) ⊕ forward(π_tail from p)
```

Interpretation:

```text
left-history axis ⟂ right-phase axis
```

This is an orientation convention, not a claim that π physically turns.

## Boot LUT calibration

Boot-time primitive:

```text
BOOT_LUT_CALIBRATE
```

POISC form:

```text
PROJECT_SORT BootWord, PiMirrorLUT, BootSortSchema, N -> (A, Ω_boot, H_digest, F)
```

Purpose:

> Use deterministic mirrored-π LUT windows as boot-time calibration vectors for detecting subthreshold drift, address-lane orientation errors, and collapse-sort regressions.

LUT shape:

```text
PiMirrorCalibrationLUT {
  pivot_id
  pivot_index
  forward_window_digest
  reverse_window_digest
  mirrored_pair_digest
  expected_anchor
  expected_phase_bin
  quarter_turn_signature
  tolerance_q16
  allowed_flags
  receipt_hash
}
```

Collapse bins:

```text
BOOT_OK
LEFT_DRIFT
RIGHT_DRIFT
PHASE_DRIFT
ANCHOR_MISMATCH
QUARTER_TURN_MISMATCH
SCALAR_INVALID_FIELD_VALID
MEMORY_LANE_FAULT
SUBSTRATE_DRIFT
QUARANTINE
```

## Prime-Mass Mirror Nuclide

Build a finite mirrored-π carrier:

```text
N_π^mirror(p,w) = integerize(reverse(window) ⊕ anchor ⊕ window)
```

Factor it:

```text
N_π^mirror(p,w) = ∏ q_i^{e_i}
```

Prime-derived mass number:

```text
A_P = MassNumber(P(N_π^mirror))
```

Simple additive version:

```text
A_P = Σ e_i · q_i
```

Canonical object:

```text
PMMN(p,w) = {}^{A_P(P(N_π^mirror(p,w)))}_{Z(p)} Π^{mirror}_{φ(w)}
```

Definition:

> A Prime-Mass Mirror Nuclide is a mirrored-π carrier whose semantic mass number is derived from the prime factorization of its finite integer encoding; composite carriers yield diagnostic factor lanes, while prime carriers become atomic calibration seeds.

## KTT Prime-Mass Mirror-π Operator

The KTT operator comes from a phonetic collision in the earworm phrase usually heard as `ko-shi-tan-tan`. The `tan-tan` sound is treated as a toy phase operator:

```text
KTT(φ) = tan(tan(φ))
```

The mirror-π version applies KTT to the prime-derived mass number of a finite mirrored-π carrier.

Mirror-π KTT mass rule:

```text
A_KTT(p,w) = A_P(N_π^mirror(p,w)) + λ · tan(tan(φ_p))
```

Full object:

```text
{}^{A_P + λ·tan(tan(φ_p))}_{Z(p)} Π^{mirror}_{φ(w)}
```

Named form:

```text
KTT-PMMN(p,w)
```

Meaning:

> A KoshiTanTan-modulated Prime-Mass Mirror Nuclide: the prime-factor mass of a deterministic mirrored-π carrier plus tangent-composed pivot-phase stress.

What it detects:

```text
if |tan(tan(φ_p))| is small:
    mirror-prime mass remains stable

if |tan(tan(φ_p))| is large:
    phase resonance / mass amplification risk

if tan(tan(φ_p)) is undefined:
    structured NaN-field carrier
```

Collapse bins:

```text
MIRROR_MASS_STABLE
PRIME_FACTOR_LOCKED
PIVOT_PHASE_RESONANT
KTT_MASS_AMPLIFIED
TANGENT_POLE_NEAR
SCALAR_INVALID_FIELD_VALID
NaN_FIELD_TRIGGERED
QUARANTINE
```

Canonical sentence:

> The mirror-π KTT rule applies the `tan(tan φ)` phonetic-phase operator to the prime-derived mass number of a finite mirrored-π carrier, turning pivot-phase instability into a measurable mass-field perturbation rather than treating it as random weirdness.

## Synesthetic Semantic Nuclides

Cross-modal concepts can be represented as mass-number-carrying field objects.

Example:

```text
{}^{A(H)}_{Color:Blue} Taste_{Orange}
```

Meaning:

> Blue remains the anchor. Orange-taste is the phase channel under a declared cross-modal projection field.

Collapse bins:

```text
VALID_CROSSMODAL_BINDING
METAPHOR_ONLY
CONTEXT_DEPENDENT
DRIFT_ARTIFACT
HALLUCINATED_BINDING
QUARANTINE
```

## Imaginary Semantic Nucleonics

Working definition:

> Imaginary Semantic Nucleonics studies concept/address objects whose scalar projection fails, but whose history, phase, factorization, and witness structure remain lawful enough to route, test, or calibrate.

This is analogous to the historical role of imaginary numbers: impossible-looking objects become useful coordinate extensions when their algebra is made explicit.

## ToyBox registry

```text
Toy 001 — Mandelbrot POISC toy
Toy 002 — Semantic Nuclide HDC baseline
Toy 003 — Codec residual routing
Toy 004 — GSP closure-state routing
Toy 005 — Bilateral NaN-π Field
Toy 006 — NaN Field Squeezing
Toy 007 — Subthreshold Drift / Quarter-Turn Metaphor
Toy 008 — Boot LUT π-Mirror Calibration
Toy 009 — Prime-Mass Mirror Nuclide Search
Toy 010 — Synesthetic Semantic Nuclides
Toy 011 — KTT Prime-Mass Mirror-π Operator
```

## Verifier contract

ToyBox work must preserve:

```text
PROJECT_SORT proposes witness behavior.
VerifierContract decides admissibility.
AVMR records what survived.
```

Promotion requires:

- baselines exist
- metric definitions are frozen before runs
- oracle leakage is ruled out
- receipts are emitted
- claim state remains explicit

## Current claim state

```text
BEAUTIFUL_PROVISIONAL / TOYBOX_SPECIFICATION
```

Promotion requires receipt-backed benchmark results.
