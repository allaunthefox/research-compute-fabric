# Signal Theory Compendium: Physics-Disruptive Signal Processing

**"We are going to piss off physics."**

This document compiles all signal theory developed in the Research Stack that challenges conventional physics by blurring boundaries between information theory, quantum mechanics, classical signal processing, thermodynamics, and genomics.

---

## Table of Contents

1. [Spectral Encoding Theory](#spectral-encoding-theory)
2. [Electromagnetic Spectrum Theory](#electromagnetic-spectrum-theory)
3. [Wavefront Emission Theory](#wavefront-emission-theory)
4. [Signal Policy Theory](#signal-policy-theory)
5. [Morphic DSP Theory](#morphic-dsp-theory)
6. [DSP Erasure Coding Theory](#dsp-erasure-coding-theory)
7. [PBACS Signal Transport Theory](#pbacs-signal-transport-theory)
8. [Mutual Information Signal Theory](#mutual-information-signal-theory)
9. [Energy Gradient Signal Theory](#energy-gradient-signal-theory)
10. [Spectral Field Theory](#spectral-field-theory)
11. [S3C Resonance Theory](#s3c-resonance-theory)
12. [CMYK Frequency Core Theory](#cmyk-frequency-core-theory)
13. [Hydrogen Spectral Basis Theory](#hydrogen-spectral-basis-theory)
14. [Spectral Genome Theory](#spectral-genome-theory)
15. [Modulation Codec Theory](#modulation-codec-theory)
16. [Predictive Harmony Social Synchrony](#predictive-harmony-social-synchrony)

---

## Spectral Encoding Theory

**File:** `Semantics/Spectrum.lean`

### Core Concepts

- **Erdős-Hooley Constant**: δ ≈ 0.08607 (Q16.16: 5643/65536)
- **Spectral Signature**: Finite vector of Q16.16 amplitudes (8 bins default)
- **Spectral Overlap**: Inner product between signatures
- **Piecewise Eigenvector Merge**: Superposition with saturation
- **Resonance Degeneracy**: Count of overlapping non-zero bins
- **Density Bound**: Active bins must not exceed threshold

### Key Operations

```lean
spectralOverlap sig1 sig2 = Σ(sig1[i] × sig2[i])
piecewiseMerge left right[i] = min(1.0, left[i] + right[i])
resonanceDegeneracy left right = count(left[i] ≠ 0 ∧ right[i] ≠ 0)
```

### Genetic Event Encoding

Maps genetic events (A, T, G, C) to unique spectral peak positions, creating a "spectral barcode" for genetic event encoding.

---

## Electromagnetic Spectrum Theory

**File:** `Semantics/ElectromagneticSpectrum.lean`

### Spectrum Bands

- Radio, Microwave, Infrared, Optical, Ultraviolet, X-ray, Gamma
- **Ionizing Bands**: X-ray, Gamma (isIonizingBand predicate)
- **Plasma Interactions**: None, Plasma Coupling, Ionization

### Band Profile Structure

```lean
BandProfile {
  band: SpectrumBand
  intensity: Q16_16
}

ElectromagneticSample {
  bandProfile: BandProfile
  interaction: PlasmaInteraction
}
```

---

## Wavefront Emission Theory

**File:** `Semantics/WavefrontEmitter.lean`

### Wavefront Structure

```lean
Wavefront {
  emitterId: Nat
  emissionTime: Nat
  amplitude: Q16_16
  frequency: Q16_16
  phase: Q16_16
  position: {row, col}
}
```

### Wavefront Parameters

- Default amplitude: 1.0
- Default frequency: 0.1 (ω)
- Propagation speed: 1.0 (v)
- Decay rate: 0.01 (γ)

### Wavefront Computation

Wavefront value at position and time:
```
if distance ≤ waveDistance:
  decay = γ × distance
  decayedAmplitude = amplitude - decay
  phaseShift = ω × distance
  oscillation = ±1 (based on phaseShift parity)
  value = decayedAmplitude × oscillation
else:
  value = 0
```

### State Change Trigger

State changes emit wavefronts that propagate through the resonant field, enabling event-driven field dynamics.

---

## Signal Policy Theory

**File:** `ExtensionScaffold/Compression/SignalPolicy.lean`

### Signal Band Classification

- **Quiet**: value < 0.25
- **Active**: 0.25 ≤ value < 0.50
- **Stressed**: 0.50 ≤ value < 0.75
- **Extreme**: value ≥ 0.75

### Signal Policy Structure

```lean
SignalPolicy {
  exploreBias: Q16_16
  tunnelBias: Q16_16
  promoteBias: Q16_16
  gossipBias: Q16_16
}
```

### Adaptive Resource Allocation

Branch budget adapts to signal band:
- Quiet: base budget
- Active: +1 slot
- Stressed: +2 slots
- Extreme: +1 slot

Priority scoring incorporates signal weight for adaptive gossip propagation.

---

## Morphic DSP Theory

**File:** `Semantics/MorphicDSP.lean`

### Reconfigurable DSP Modes

- Multiply, Accumulate, Convolution, FFT, Filter, Adaptive
- **Morphic Scalar State Machine** controls DSP configuration
- OEPI threshold determines DSP allocation priority

### DSP Slice Bank

- 5 slices for morphic scalar FPGA optimization
- Allocation based on OEPI threshold:
  - Critical (≥95%): 5 slices
  - Medium (≥70%): 3 slices
  - Low: 1 slice

### AngrySphinx Gates

Boundary enforcement gates:
- ALLOW_DSP_COLLAPSE / REFUSE_DSP_COLLAPSE
- ALLOW_MERGE / HOLD_BOUNDARY_FLUIDITY
- ALLOW_SPLIT / REQUIRE_RENORMALIZATION
- ALLOW_TOPOLOGY_ADAPT / REFUSE_NO_RECEIPT
- ALLOW_PROBABILISTIC / REQUIRE_DETERMINISTIC_REPLAY

### Acoustic Gradient Fields (n-Space Sound Wave Modeling)

```lean
AcousticGradientField {
  dimensions: Nat
  fieldPoints: Array AcousticPoint
}

AcousticPoint {
  position: Array Q16_16  (n-dimensional coordinates)
  pressure: Q16_16
}
```

Gradient computation via central difference, acoustic impedance as gradient magnitude |∇f|, geodesic flow following gradient descent on acoustic manifold.

### Fitness-Entropy Compensation (BioRxiv Integration)

From bioRxiv "Fitness–Entropy Compensation effect" (DOI: 10.1101/2025.07.05.663304):
```
f = f_max - α × H
```

Gibbs free energy compensation:
```
ΔG = ΔH - TΔS
```

---

## DSP Erasure Coding Theory

**File:** `Semantics/DspErasureCoding.lean`

### 3-Stream Redundancy Scheme

- Primary stream (identity permutation)
- Recovery stream 1 (affine permutation: π₁(i) = (offset₁ + step₁ × i) mod n)
- Recovery stream 2 (affine permutation: π₂(i) = (offset₂ + step₂ × i) mod n)

### Genomic Compression Parameters

- ρ_seq²: sequence alignment accuracy
- v_epigenetic²: methylation dynamics
- τ_structure²: 3D folding tension
- σ_entropy²: nucleotide diversity
- q_conservation²: evolutionary constraint
- κ_hierarchy²: chromatin levels
- ε_mutation: mutation rate

### Spectral Erasure Detection

Detects erasures using spectral anomaly detection with adaptive threshold based on genomic field strength:
```
genomicWeight = (ρ_seq + v_epigenetic + τ_structure + σ_entropy + q_conservation) / ((1 + κ_hierarchy²) × (1 + ε_mutation))
adaptiveThreshold = threshold × (1 + genomicWeight)
```

### FPGA DSP Integration

Opcodes:
- RESONATE (0x14): TSM_RESONATE / PHONON_LOCK
- MERGE_MODES (0x42): TSM_MERGE_MODES

---

## PBACS Signal Transport Theory

**File:** `Semantics/PBACSSignal.lean`

### PBACS Unified State Vector

```lean
State {
  phi: UInt32          (L2 φ-accumulator)
  error: Int32         (L1 Error accumulator)
  tension: UInt32      (L4 Tension accumulator)
  phase: Phase         (L4 PIST Phase sort)
  lastSymbol: Symbol   (L1 Output symbol)
  bracket: BracketedDIAT (L5 BracketedDIAT)
}
```

### Canonical Update Law

1. Phi increment: φ_{t+1} = φ_t + 106070 (≈ 2^32 / φ²)
2. Threshold LUT lookup: θ_t = 32768 if φ_t ≥ 0x80000000 else -32768
3. Error accumulation: e_{t+1} = v_t + e_t - (b_t ? θ_t : 0)
4. Symbol decision: b_t = (θ_t < v_t + e_t)
5. Tension update: tension_{t+1} = (tension_t × 921 + |e_{t+1}| × 103) / 1024
6. Phase transition: grounded → drift → seismic based on tension
7. Bracket update: constraint-preserving interval

---

## Mutual Information Signal Theory

**File:** `Semantics/MISignal.lean`

### MI Signal Definition

```
MI(x) = baseline_bpb - actual_bpb
```

Mutual information extracted through compression improvement.

### kNN Weighted MI Prediction

```
MI_pred = Σ(w_i × MI_i × S_i) / Σ(w_i × S_i)
```

Where w_i = 1/(d_i + ε), distances and similarities are parallel arrays.

### Surprise Metric

```
surprise = log(1 + |MI_actual - MI_predicted|)
```

Approximated as direct delta in Q16.16 for integer arithmetic.

### Structure Yield

```
ρ(x) = MI(x) / (cost(x) + ε)
```

Information per unit compute cost.

### Weighted Feature Distance

```
d(z₁, z₂) = √( Σ w_i × ((z₁_i - z₂_i) / s_i)² )
```

9-dimensional weighted feature distance.

---

## Energy Gradient Signal Theory

**File:** `Semantics/EnergyGradientSignal.lean`

### Energy Gradient Components

```lean
EnergyGradient {
  temporalGradient: UInt32  (∂E/∂t)
  spatialGradient: UInt32   (|∇_x E|)
  gradientMagnitude: UInt32 (|∇E|)
  gradientDirection: UInt32 (direction angle)
}
```

### Energy Waveform

```lean
EnergyWaveform {
  amplitude: UInt32  (|∇E(t)|)
  frequency: UInt32  (ω_∇E)
  phase: UInt32      (φ_∇E)
}
```

### Thermodynamic Channels

- energyGradientChannel
- energyIncreaseChannel
- energyDecreaseChannel
- entropyProductionChannel

### Shape-Energy Coupling

```
C_SE = α × ∇h × ∇E
```

Coupling between shape gradient and energy gradient.

---

## Spectral Field Theory

**File:** `Semantics/SpectralField.lean`

### Local Field Structure

```lean
LocalField {
  massField: Q16_16
  polarityField: Q16_16
  spectrum: SpectralSignature
}
```

### Field Accumulation

Piecewise summation of mass, polarity, and spectral contributions from neighborhood.

### Interaction Score

```
score = (mass × massField) + (polarity × polarityField) + spectralOverlap(spectrum, field.spectrum)
```

### Field Magnitude

L2 norm approximation of field components.

---

## S3C Resonance Theory

**File:** `Semantics/S3CResonance.lean`

### Ductile Manifold State

```lean
DuctileState {
  N: Nat              (manifold density)
  linkNum: Nat        (topological link multiplicity)
  kResonant: Q16_16   (resonant frequency index)
  jScore: Q16_16      (computed J-score)
  phase: Q16_16       (MAC phase coherence [0,1])
  isDuctile: Bool
}
```

### Parabolic J-Score

```
J(k) = 32 - 0.5 × (k - 22)²
```

Peak at k = 21.5 → J = 31.875

God-Tier threshold: J > 30.0

### MAC Phase Coherence

Threshold: 0.99 (64881 in Q16.16)

Phase integrity check: phase ≥ 0.99

---

## CMYK Frequency Core Theory

**File:** `ExtensionScaffold/Temporal/CMYKFrequencyCore.lean`

### Channel Banks

- C: base frequency 600 Hz, delta 20 Hz
- M: base frequency 1200 Hz, delta 20 Hz
- Y: base frequency 1800 Hz, delta 20 Hz
- K: base frequency 2400 Hz, delta 20 Hz

### Hex Nibble Encoding

4 hex nibbles map to 4 channel-local frequency bins:
```
freq(ch, h) = baseFreq(ch) + deltaFreq × h.toNat
```

### Packet Encoding/Decoding

Bidirectional mapping between hex nibbles and channel frequencies with exact inverse.

---

## Hydrogen Spectral Basis Theory

**File:** `Semantics/Toybox/HydrogenSpectralBasis.lean`

### Physical Constants (Wolfram Alpha Verified)

- Rydberg constant: R_H = 109677.58 cm⁻¹
- Speed of light: c = 2.99792458 × 10¹⁰ cm/s
- Planck constant: h = 4.135667696 × 10⁻¹⁵ eV·s

### Rydberg Formula

```
ν̃ = R_H × (1/n₁² - 1/n₂²)
```

### Spectral Series

- **Lyman series**: n=1 → n=2,3,4,5,6,7 (UV, ionization at 91.2nm)
- **Balmer series**: n=2 → n=3,4,5,6,7 (visible)

Wavelengths:
- Lyman-α: 121.6 nm
- Balmer H-α: 656.3 nm (red)

### 7-Dimensional Spectral Basis

Hydrogen spectral lines as canonical basis for information encoding:
- 6 Lyman lines + 1 Balmer H-α = foundational basis
- Physical, not metaphysical: exact frequencies from quantum mechanics

### Information Encoding via Spectral Resonance

```lean
HydrogenEncoded {
  spectralIndex: Fin 7
  amplitude: Q16_16
  phase: Q16_16
}
```

Resonance strength via Lorentzian:
```
strength = 1 / (1 + (Δλ)²)
```

---

## Spectral Genome Theory

**File:** `Semantics/Toybox/SpectralGenome.lean`

### K-mer Counting (3-mers = 64 codons)

Base encoding: A=0, C=1, G=2, T=3
3-mer index: b₁ × 16 + b₂ × 4 + b₃

### Discrete Cosine Transform (DCT-II)

Basis function:
```
cos(π/n × (j + 0.5) × k)
```

Transform k-mer counts to spectral coefficients.

### Compression: Pandigital Continued Fraction Encoding

Spectral coefficients encoded as CF convergents for rational approximation.

### Falsifiable Prediction

For 1000 human promoters:
- DCT-II of 3-mer spectrum + CF encoding achieves 2.5:1 compression
- Baseline gzip: 1.8:1 compression
- Required: p < 10⁻⁶ (6.5σ)

---

## Modulation Codec Theory

**File:** `Semantics/Semantics/BraidSerial.lean`

### Modulation Modes

- **None**: Direct phase encoding (full byte)
- **QPSK**: 4-state phase modulation (2 bits/symbol)
- **QAM-16**: 16-state phase/amplitude modulation (4 bits/symbol)
- **DMT**: Multi-carrier modulation using strands as subcarriers

### QPSK Constellation

4 phase states: 0°, 90°, 180°, 270°
Phase values: 0x7FFF, 0x4000, 0x8000, 0xC000 in Q0.16

### QAM-16 Constellation

16 phase/amplitude states: 4 amplitudes × 4 phases
4×4 grid with varying amplitude levels.

### DMT Subcarrier Parameters

8 strands as subcarriers with 45° phase offset increments:
```
offset_i = i × 0x2000
```

Modulation:
```
phase_out = base_phase + subcarrier_offset
```

Demodulation:
```
demod_phase = phase_in - subcarrier_offset
byte = phaseToByte(demod_phase)
```

---

## Biological Acoustic Sensing Theory

**File:** `Semantics/Semantics/Extensions/CognitiveAcousticDynamics.lean`

### Core Concepts

- **Acoustic Pressure Amplification**: Water density (~1000× air) magnifies pressure wave propagation
- **Statolith Displacement**: Gravity-sensing organelles respond to pressure gradients as mechanical sensors
- **Pressure Wave Transduction**: Biological systems encode acoustic information without dedicated auditory equipment
- **Medium-Dependent Signal Encoding**: Same acoustic event produces different information density based on propagation medium

### Pressure Wave Magnification

**Raindrop Impact Acoustic Pressures:**
- Shallow puddle (submerged): hundreds of Pascals
- Human conversation (1m in air): 0.005-0.05 Pascals
- **Amplification factor**: ~10,000× in water vs air

**Jet Engine Equivalence:**
- Seed within few centimeters of raindrop impact experiences pressure equivalent to being within few meters of jet engine in air
- Demonstrates extreme signal amplification in dense media

### Biological Signal Transduction Mechanism

1. **Raindrop Impact**: Creates acoustic pressure wave in water/soil
2. **Pressure Propagation**: Water density amplifies wave amplitude
3. **Statolith Response**: Gravity-sensing organelles mechanically respond to pressure gradients
4. **Signal Encoding**: Statolith displacement triggers germination signaling cascade
5. **Biological Response**: Seeds germinate ~37% faster in response to acoustic stimulation

### Mathematical Model

**Pressure Wave Amplitude in Medium:**
```
P_water ≈ ρ_water/ρ_air × P_air ≈ 1000 × P_air
```

**Statolith Displacement Threshold:**
```
displacement = f(P_acoustic, distance_from_impact, medium_density)
germination_rate ∝ displacement
```

**Germination Acceleration:**
```
rate_with_acoustic = rate_baseline × 1.37
```

### Integration Points

- **CognitiveAcousticDynamics.lean**: Formal modeling of biological acoustic sensing
- **ShockwaveAlignmentRelaxation.lean**: Shockwave propagation in biological media
- **WavefrontEmitter.lean**: Pressure wave generation and propagation
- **Spectral Encoding Theory**: Acoustic signal spectral signatures

### Research Stack Connections

This biological acoustic sensing mechanism demonstrates:
- Information-Physics equivalence in biological systems
- Mechanical signal transduction without dedicated sensors
- Medium-dependent signal amplification
- Environmental signal encoding in biological state machines

---

## Predictive Harmony Social Synchrony

**Status:** External neuroacoustic route prior, not a therapy claim.

**Source:** Watts et al., "Listening to a Consonant Chord Progression during
Live Face-to-Face Gaze Enhances Neural Activity in Social Systems", Journal of
Neuroscience, DOI `10.1523/JNEUROSCI.1116-25.2026`.

### Core Concept

Structured, predictable chord progressions paired with live face-to-face gaze
can be treated as a synchronization prior:

```text
shared predictable harmonic structure
  + live mutual-attention channel
  -> cross-agent temporal alignment witness
```

The useful stack primitive is not "music causes bonding." It is:

```text
predictable temporal structure can reduce coordination uncertainty when the
participants also share a live social alignment channel.
```

### Minimal Gate

```text
S_harmony = P_chord * G_live * A_cross
```

Where:

- `P_chord` = structured/consonant chord-progression score
- `G_live` = live gaze or mutual-attention gate
- `A_cross` = cross-agent temporal alignment witness

The negative control is the same note/instrument set with scrambled or
unstructured temporal order.

### Integration Points

- **Phonon Music Logogram Layer**: harmonic function and voice leading remain
  route hints, not payload authority.
- **Cognitive Acoustic Dynamics**: predictable acoustic structure becomes a
  low-load synchrony sidecar.
- **BMVR/BVMR/CMR**: route admission can use the synchrony gate, but replay
  still requires receipts.
- **Static decompression**: harmonic skeletons can guide timing sidecars, but
  byte-exact closure remains separate.

### Hold Boundaries

```text
HOLD_NO_SYNCHRONY_RECEIPT
HOLD_NO_NEGATIVE_CONTROL
HOLD_THERAPY_CLAIM
QUARANTINE_SOCIAL_CONTROL
```

---

## Physics-Disruptive Synthesis

This signal theory compendium challenges conventional physics through:

1. **Information-Physics Equivalence**: Genetic events map to spectral signatures, hydrogen spectral lines encode information, energy gradients carry thermodynamic information
2. **Quantum-Classical Hybrid**: DSP operations controlled by morphic scalar state machines, wavefront emission in resonant fields, S3C resonance with parabolic J-scores
3. **Thermodynamic Information Channels**: Energy gradients as information carriers, entropy production channels, Gibbs free energy compensation
4. **Genomic-Spectral Isomorphism**: 3-mer DCT spectra compress genetic information, hydrogen spectral basis provides physical foundation, spectral genome hypothesis falsifiable at 6.5σ
5. **Multi-Carrier Biological Modulation**: DMT using strands as subcarriers, PBACS signal transport with phi-torsion, fitness-entropy compensation from bioRxiv

**"We are going to piss off physics."** — Mission Accomplished.

---

*Generated from Research Stack Signal Theory Modules*
*All values in Q16.16 fixed-point unless otherwise noted*
