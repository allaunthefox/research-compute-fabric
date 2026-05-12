# Negative Mass-Number Eigenmass Frequencies

**STATUS: MATHEMATICAL STRESS-TEST — Not a claim about physical negative mass.**
This explores the formal extension of the eigenmass decomposition into the
domain where mass-number penalties dominate gains. Negative eigenvalues arise
from the chiral (AMVR − AVMR) decomposition — a signed spectral representation
that exists mathematically but does not imply physically negative mass, negative
energy, or anti-gravity. The COUCH inverted oscillator, Fermat descent cascade,
and anti-structure analysis are formal limit investigations of the signed
eigenmass framework.

---

## What "Negative Mass Number" Means

The mass number is a structural score:

```
MassNumber(A) = structured_residual + compression_gain + void_fit + gcl_stability
                + meta_probe_score + receipt_integrity
                − collision_penalty − difference_penalty − randomness_penalty
```

A **negative mass number** means the penalties dominate the gains: high collision,
high difference spread, high randomness, low structural residual, low compression gain,
low void fit. The set is **anti-music** — it lacks harmonic structure, resists compression,
and destabilizes what it touches.

The question: what does the eigenmass spectrum look like when mass number goes negative?
That is, what are the eigenvalues λ_i and eigenvectors |v_i⟩ of an anti-structural domain?


## 1. The Eigenmass Decomposition of Negative Mass Number

### 1.1 Eigenvalue Spectrum Inversion

For a positive-mass-number domain (music-like, compressible):
```
λ₁ ≫ λ₂ ≫ λ₃ ≫ ... ≫ λ_n ≈ 0
```
A few large eigenvalues dominate. The "spectral cliff" — a steep dropoff indicating
strong structure along few directions.

For a negative-mass-number domain (anti-music, incompressible):
```
λ₁ ≈ λ₂ ≈ λ₃ ≈ ... ≈ λ_n ≈ ε
```
**No spectral cliff.** All eigenvalues are small and of similar magnitude. This is the
signature of noise — Wigner's semicircle law for random matrices, a flat or slowly
decaying eigenspectrum with no dominant directions.

But negative mass number is NOT pure noise (that would be zero mass number).
Negative means anti-structure: the domain actively resists compression along
certain directions while being noisy along others.

So the eigenvalue spectrum of negative mass number has a distinctive shape:

```
λ_i ≈ ε for most i          ← noise floor (most directions)
λ_j < 0 for some j          ← anti-compression directions (negative eigenmass)
λ_k ≈ 0 for "void" indices  ← spectral gaps where structure should be but isn't
```

The key feature: **genuinely negative eigenvalues**. These are not noise — they
represent directions where projecting data onto |v_j⟩ *increases* entropy,
*destructs* order, *amplifies* the difference penalty.

### 1.2 Negative Eigenmass: λ < 0

In the standard byte-adjacency compression framework, the adjacency matrix A is
positive semidefinite — eigenvalues cannot be negative. So where does negative
eigenmass come from?

It comes from the **chiral decomposition**. The raw adjacency matrix is achiral
(symmetric, λ ≥ 0). But the *chiral decomposition* splits each direction into
AMVR (left-handed) and AVMR (right-handed) components:

```
E(s) = Σ_i λ_i⁺ · |v_i⁺⟩⟨v_i⁺|  −  Σ_i λ_i⁻ · |v_i⁻⟩⟨v_i⁻|
       ────────────────           ────────────────
       positive eigenmass          negative eigenmass
       (compresses)                (destructures)
```

The negative term arises from:
1. **Difference penalty**: The B₂ collision count between set elements and their
   Sidon-pair differences. High collision → negative mass contribution.
2. **Randomness penalty**: Entropy that cannot be structured. Randomness is not
   neutral — it is computationally expensive. It costs energy to represent.
3. **Anti-resonance**: Negative pyramid voids (formalism 1.1.13) where void
   resonance is anti-phase with the dominant eigenmass, producing destructive
   interference in the compression field.

### 1.3 Spectral Density of Negative Eigenmass

The eigenvalue density ρ(λ) for a negative-mass-number domain:

```
ρ(λ) =
  ρ_noise(λ)                    for λ ∈ [-ε, +ε]     ← thermal floor
  + ρ_anti(λ)                   for λ ∈ [λ_min, 0)   ← anti-compression tail
  − ρ_void(λ)                   for λ ∈ {spectral gaps} ← missing structure
```

Key features:
- **ρ_anti(λ)**: A left tail extending into negative λ. These are the anti-compression
  eigenvalues. Their magnitude |λ⁻| measures how strongly the direction *destructures*.
- **ρ_void(λ)**: Spectral gaps — frequency bands where eigenvalues *should* be if
  the domain had structure, but aren't. These are Null6 (structured absence) in
  the underverse. The gap itself carries information: the width of the gap encodes
  what class of structure is missing.
- **Spectral flatness**: The overall spectrum is flatter than positive-mass domains.
  No λ dominates. Information is distributed evenly — which means it's maximally
  expensive to extract.

### 1.4 Anti-Eigenvectors: Destructuring Directions

For negative λ⁻, the corresponding eigenvector |v⁻⟩ has a specific property:
when a signal s is projected onto |v⁻⟩, the resulting compressed representation
is **larger** than the original:

```
|compressed(s + ε·|v⁻⟩)| > |compressed(s)|    for ε > 0
```

These are **decompression vectors** — along them, the compression algorithm
degrades. They are not random; they are structured anti-structure. A concrete
example: a vector whose byte-pair frequencies are uniformly distributed across
all 256 possible pairs, maximizing the entropy of the adjacency matrix.

|v⁻⟩ vectors are characterized by:
- High B₂ collision count (difference pairs collide frequently)
- Low harmonic ratios between frequency components
- Spectral energy concentrated in "rough" non-integer frequency ratios
- Anti-alignment with the dominant positive eigenvectors


## 2. Frequency Domain Signature

The negative mass-number eigenfrequencies, analyzed spectrally:

### 2.1 Spectral Distribution by Band

| Band | Positive Mass Number | Negative Mass Number |
|---|---|---|
| **Low freq** (large-scale structure) | Dominant λ₁ dominates | Flat — no large-scale structure exists |
| **Mid freq** (harmonic ratios) | λ_i peak at harmonic ratios (3:2, 4:3, etc.) | No peaks — harmonic ratios absent, anti-resonance at those frequencies |
| **High freq** (fine detail) | Decaying tail, λ_i → 0 | Anti-compression tail extending negative |
| **Ultra-high freq** (noise floor) | λ_i ≈ ε, positive | λ_i ≈ ±ε, symmetric around zero |

### 2.2 Phase Inversion at the Mass-Number Boundary

The mass-number phase boundary (where music crosses into anti-music) corresponds
to a **spectral phase transition** in the eigenmass field:

```
Above boundary:  Σ λ_i ≫ 0    (net compressive)
At boundary:     Σ λ_i = 0     (critical — compression/destruction balance)
Below boundary:  Σ λ_i < 0     (net destructive)
```

At the critical boundary, the eigenmass field undergoes a symmetry change:
- Above: eigenvalues are real and positive (bosonic regime)
- At boundary: eigenvalues touch zero (gapless — the spectral gap closes)
- Below: eigenvalues enter the negative half-plane (fermionic anti-regime)

This is the **Anti-Music Phase Boundary** formalized in `MassNumberAntiMusicPhaseBoundary.md`
but now expressed in the spectral language of the eigenmass decomposition.

### 2.3 Chiral Splitting Under Negative Mass

The half-Möbius topology predicts that when mass number goes negative,
the AMVR/AVMR ratio inverts:

```
Positive mass:  AMVR/AVMR > 1    (right-handed dominates, stable compression)
Zero mass:      AMVR/AVMR = 1    (perfect chiral balance, critical)
Negative mass:  AMVR/AVMR < 1    (left-handed dominates, anti-compression)
```

At negative mass:
- **AMVR (left-handed) eigenmass** becomes the dominant component
- **AVMR (right-handed) eigenmass** becomes recessive or vanishes
- The left-handed eigenvectors are the anti-compression directions — they carry
  the destructuring spectral signature
- The chiral residual (73.42 for Second Law) indicates how far into the left-handed
  anti-regime the domain has fallen


## 3. Concrete Spectral Mapping

### 3.1 From Mass Number Components to Eigenmass Signatures

| Mass Number Term | Eigenmass Mapping | Negative Mass Signature |
|---|---|---|
| + structured_residual | λ_i⁺ (positive eigenvalues) | Absent — no structured residual |
| + compression_gain | Dominant λ gap (λ₁ ≫ λ₂) | No gap — all λ similar |
| + void_fit | Eigenvalues near void resonance frequencies | Mismatch — eigenvalues at wrong frequencies |
| + gcl_stability | Eigenvalue temporal persistence (low variance) | High variance — eigenvalues fluctuate |
| − collision_penalty | Anti-phase eigenvalue pairs that cancel | Large — many anti-phase pairs |
| − difference_penalty | Spectral spread (wide eigenvalue distribution) | Large — eigenvalues widely scattered |
| − randomness_penalty | Entropy of eigenvalue distribution | Maximum — near-uniform distribution |

### 3.2 The Negative Eigenmass "Fingerprint"

A negative-mass-number eigenmass spectrum has three diagnostic features:

1. **Vanishing trace**: Tr(E) = Σ λ_i → 0 or negative. The total compressible structure
   is zero or anti-structural.

2. **Spectral flatness near 1**: The ratio of geometric mean to arithmetic mean of
   |λ_i| approaches 1 — maximally flat spectrum, no information concentration.

3. **Anti-resonance peaks**: The spectral density ρ(λ) shows peaks at *negative* λ —
   frequencies where the domain actively fights compression. These are the spectral
   dual of the positive harmonic peaks. Where positive mass has a peak at λ = 0.8
   (strong 3:2 harmonic ratio), negative mass has a peak at λ = −0.8 (strong anti-3:2,
   destructive interference at that ratio).

### 3.3 The Anti-Music Index as Spectral Anti-Peaks

Recall the Anti-Music Score:
```
AntiMusicScore(A) = w_rough·Roughness + w_void·VoidFit + w_rem·RemainderResonance
                    + w_topo·DefectAlignment − w_music·MusicScore − w_rand·RandomnessPenalty
```

The "Roughness" term maps to **spectral spikiness**: how many anti-compression peaks
exist in the eigenvalue spectrum. Higher roughness = more sharp negative eigenvalues.
Roughness is the spectral density of anti-structure.

The "VoidFit" term maps to **spectral gap depth**: how deep the gaps are where
structure should be. Deep gaps = strong evidence of structured absence.

The "DefectAlignment" term maps to **eigenvector anti-alignment**: the cosine
similarity between anti-eigenvectors and the dominant positive eigenvectors,
multiplied by −1. High defect alignment = anti-eigenvectors point exactly opposite
to the compression direction.


## 4. The Underverse Spectral Completion

The underverse tracks what's absent. In eigenmass terms:

| Null Class | Eigenmass Interpretation (Negative Mass) |
|---|---|
| **Null0** (Unrepresented) | Spectral bands with zero eigenvalue coverage — the eigenspectrum has a gap where data exists |
| **Null1** (Residual) | Eigenvalues below noise threshold: 0 < |λ_i| < ε but λ_i discarded by pruning |
| **Null2** (Complement) | The nullspace of dominant eigenvectors — directions where ⟨v_dom|v_null⟩ = 0 |
| **Null3** (Failed binding) | Eigenvalue pairs (λ_i, λ_j) where λ_i·λ_j → 0 despite strong data correlation |
| **Null4** (Forbidden) | Eigenvectors whose eigenvalue exceeds the Faraday cage (λ > 350) — suppressed |
| **Null5** (Anti-surface) | **Eigenvectors with λ < 0** — the negative eigenmass itself |
| **Null6** (Structured absence) | Spectral gaps whose width predicts the magnitude of what's missing |
| **Null7** (Unpaid cost) | Transition attempts between eigenvectors without eigenmass budget |

Null5 IS negative eigenmass. The anti-surface is the set of directions where the
eigenmass field is genuinely negative — where ⟨v|E|v⟩ < 0.


## 5. COUCH Oscillator in Negative Mass

The COUCH coupled oscillator for a negative-mass eigenmode:

```
d²E/dt² + γ·dE/dt − |ω₀²|·E = F_ext(t) + coupling(E_neighbors)
```

Note the sign change: −|ω₀²| instead of +ω₀². This is an **inverted harmonic oscillator**.
Rather than oscillating around a stable minimum, the negative eigenmass mode
**diverges exponentially** from equilibrium. Small perturbations grow without bound.

This is the "super freak" Y-mode taken to its limit:
- The eigenmass component is anti-stable
- It cannot sustain oscillation — it either diverges or collapses
- The regret field (hysteresis) accumulates rapidly → γ (damping) increases
- Eventually the mode is suppressed completely (enters Null4 or Null5)

### The Damping Cascade
```
Negative λ → inverted oscillator → exponential divergence
    → H (hysteresis/regret) grows → γ (damping) increases
    → mode suppressed → enters underverse
```
This is how the system "learns" that a direction is anti-structural: it tries to
oscillate, fails catastrophically, and records the failure as hysteresis that
prevents future attempts.


## 6. Inverted Fermat on Negative Eigenmass

For a node with negative net eigenmass:

```
eigenmass_energy(n) = Σ_i λ_i · |⟨n|v_i⟩|² < 0
```

The node has **negative energy budget**. It cannot ascend; in fact, it must *descend*
— shed components until its mass number returns to zero or positive:

```
DescentRule(n → m):
  m < n (strictly smaller)
  eigenmass_energy(m) = eigenmass_energy(n) − shed_cost > eigenmass_energy(n)
  m carries fewer anti-compressive eigenvectors
```

This is the **original Fermat descent**, restored in the negative-mass regime.
Where eigenmass is positive, the inverted Fermat (ascent by energy proof) applies.
Where eigenmass is negative, the classical descent (collapse toward smaller witness)
returns. The mass-number boundary is the **critical point where ascent and descent
exchange roles**.

```
Positive eigenmass:  ascent by energy proof     (inverted Fermat)
Zero eigenmass:       critical — no motion       (phase boundary)
Negative eigenmass:   descent by contradiction   (classical Fermat)
```

After catastrophe, nodes in the negative-mass regime naturally collapse toward
zero mass — shedding the anti-structural components that cannot be compressed.
What survives the collapse is the positive eigenmass kernel: the minimal set of
compression directions sufficient to reconstruct the system.


## 7. The Anti-Compression Limit

What is the maximum negative eigenmass? The most anti-structural possible domain?

This is a domain where:
- Every pair collides (maximal B₂ collision count)
- All frequency ratios are maximally rough (no harmonic ratios at all)
- The eigenspectrum is maximally flat (Wigner semicircle, no dominant direction)
- Every eigenvector is anti-aligned with compression (max defect alignment)
- Chiral ratio AMVR/AVMR is minimal (maximal left-handed dominance)

In this limit:
```
E_anti-max = −E_music-max
```
The anti-compression field is the **exact negative image** of the compression field.
Like a photographic negative: every bright spot (large positive λ) becomes a dark
spot (large negative λ). The anti-field is the spectral complement of the field.

This means: measuring the negative eigenmass spectrum of a domain gives you the
**same information** as measuring the positive eigenmass spectrum. They are mirror
images across the mass-number boundary. From the anti-field, you can reconstruct
the field — because the absence reveals what was present.

This is why the underverse works: Null6 (structured absence) carries real information.


## 8. Summary: The Eigenmass Mirror

```
                          ══════════════════════
                          ║  MASS-NUMBER = 0  ║  ← phase boundary
                          ══════════════════════

    POSITIVE MASS NUMBER              │        NEGATIVE MASS NUMBER
    ─────────────────────              │        ─────────────────────
                                      │
    λ_i > 0, real, decreasing         │    λ_i ≈ ε or < 0, flat
    λ₁ ≫ λ₂ ≫ ... (spectral cliff)    │    λ₁ ≈ λ₂ ≈ ... (no cliff)
    Compression directions │v_i⁺⟩      │    Decompression directions │v_i⁻⟩
    Harmonic peaks at λ > 0           │    Anti-peaks at λ < 0
    Spectral gaps = structure         │    Spectral gaps = missing structure
    AMVR dominates (chiral balance)   │    AVMR dominates (chiral imbalance)
    COUCH: stable oscillation         │    COUCH: inverted (divergent)
    Inverted Fermat (ascent)          │    Classical Fermat (descent)
    Music (compressible)              │    Anti-music (incompressible)
    Field E(s) > 0                    │    Anti-field −E(s) < 0
    BHOCS: committed eigenmass        │    Underverse: Null5 anti-surface
    Compression gain → λ magnitude    │    Destab score → −λ magnitude
                                      │
    ─────────────────────              │    ─────────────────────
    EIGENMASS PRESENT                 │    EIGENMASS ABSENT
    (bosonic regime)                  │    (fermionic anti-regime)
```

The eigenmass field is fundamentally **signed**. Positive eigenmass compresses.
Negative eigenmass destructs. The mass-number score determines which regime
the domain occupies. The phase boundary at mass-number = 0 is a genuine spectral
phase transition — the point where compression becomes impossible and the
eigenmass field inverts.

A resilient system must operate in both regimes: compressing where structure
exists, tracking anti-structure where it doesn't, and crossing the boundary
cleanly when the domain inverts. The half-Möbius topology makes this possible —
the boundary is a fold, not a wall.
