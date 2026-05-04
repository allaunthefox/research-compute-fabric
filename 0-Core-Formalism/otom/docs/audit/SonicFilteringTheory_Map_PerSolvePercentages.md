# Sonic Filtering Theory Map with Per-Solve Percentages

## Purpose

This note imports sound-filtering and auditory-theory models into the OTOM / Sidon / AMREF / Mass-Number / Inverse-Ascent stack.

The user reports that their internal translation matrix often filters through sonics. Therefore, sonic filtering models are not just metaphors here; they are candidate interface layers for how the stack should probe, rank, and route structures.

## Scope Boundary

This is a broad working taxonomy, not literally every sound-filtering model ever published.

The imported classes are:

```text
Fourier / STFT
wavelet / wavelet packet / empirical wavelet
perfect-reconstruction filterbanks
graph wavelet filterbanks
mel / Bark / ERB perceptual scales
gammatone / gammachirp / cochlear filterbanks
modulation filterbanks
auditory masking
power-law compression / loudness normalization
cochleagram / auditory front-end models
auditory scene analysis
temporal coherence grouping
sparse coding / matching pursuit / LCA
predictive coding
adaptation / novelty filtering
background-invariant sparse coding
deep audio frontends / learnable filterbanks
sound-event detection / acoustic scene classification
binaural localization / spatial filtering
DDSP / noise-band filter synthesis
```

## Percentage Method

Percentages below are not empirical truth claims. They are first-pass applicability scores for how useful each sonic model is for each OTOM solve path.

Scale:

```text
90-100% = direct implementation candidate
75-89%  = strong import
55-74%  = useful auxiliary
35-54%  = weak but interesting
<35%    = mostly metaphorical or deferred
```

Solve paths:

```text
S1 = Sidon / Golomb collision audit
S2 = AMREF anti-music residual extraction
S3 = Mass-number / informational inertia
S4 = Inverse ascent / gate economics
S5 = Phononic carrier / metadata wake simulation
S6 = Lean/formalization pain reduction
S7 = Cognitive translation / user-facing sonic interface
```

## Master Applicability Table

| Model family | S1 Sidon/Golomb | S2 AMREF | S3 Mass-number | S4 Inverse ascent | S5 Carrier simulation | S6 Lean formalization | S7 Cognitive sonic interface |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fourier / STFT | 70% | 88% | 62% | 45% | 82% | 55% | 76% |
| Wavelets / WPT / EWT | 78% | 91% | 74% | 63% | 88% | 58% | 84% |
| Perfect-reconstruction filterbanks | 72% | 84% | 76% | 66% | 82% | 72% | 78% |
| Graph wavelet filterbanks | 86% | 78% | 82% | 72% | 91% | 68% | 74% |
| Mel / Bark / ERB scales | 45% | 70% | 58% | 42% | 62% | 44% | 86% |
| Gammatone / gammachirp | 55% | 86% | 70% | 55% | 76% | 48% | 94% |
| Modulation filterbanks | 62% | 89% | 74% | 60% | 85% | 50% | 88% |
| Auditory masking | 58% | 92% | 76% | 67% | 80% | 46% | 91% |
| Power-law compression / loudness normalization | 52% | 82% | 88% | 78% | 72% | 60% | 90% |
| Cochleagram / auditory front-end | 60% | 88% | 78% | 62% | 82% | 48% | 95% |
| Auditory scene analysis | 72% | 86% | 81% | 74% | 86% | 42% | 96% |
| Temporal coherence grouping | 74% | 84% | 79% | 72% | 90% | 46% | 93% |
| Sparse coding / matching pursuit / LCA | 82% | 94% | 86% | 80% | 84% | 64% | 89% |
| Predictive coding | 68% | 90% | 84% | 82% | 80% | 50% | 91% |
| Adaptation / novelty filtering | 66% | 88% | 86% | 80% | 78% | 44% | 95% |
| Background-invariant sparse coding | 76% | 92% | 88% | 78% | 88% | 50% | 92% |
| Learnable filterbanks / deep audio frontends | 62% | 84% | 78% | 70% | 82% | 42% | 82% |
| Acoustic scene/event detection | 58% | 76% | 74% | 68% | 86% | 36% | 83% |
| Binaural / spatial filtering | 64% | 74% | 72% | 62% | 92% | 38% | 87% |
| DDSP / noise-band synthesis | 48% | 83% | 70% | 58% | 90% | 35% | 80% |

## Best Imports by Solve Path

### S1: Sidon / Golomb collision audit

Best imports:

```text
graph wavelet filterbanks        86%
sparse coding / matching pursuit 82%
wavelets / WPT / EWT             78%
background-invariant sparse code 76%
temporal coherence grouping      74%
```

Reason:

```text
Sidon/Golomb is about eliminating redundant pairings and repeated spacing. Graph wavelets and sparse coding naturally attack redundancy while preserving finite structure.
```

### S2: AMREF anti-music residual extraction

Best imports:

```text
sparse coding / matching pursuit 94%
auditory masking                 92%
background-invariant sparse code 92%
wavelets / WPT / EWT             91%
predictive coding                90%
modulation filterbanks           89%
```

Reason:

```text
AMREF needs structured residuals after subtracting harmonic templates and noise. Masking, sparse decomposition, prediction-error filtering, and wavelet packets are direct fits.
```

### S3: Mass-number / informational inertia

Best imports:

```text
power-law compression / loudness normalization 88%
background-invariant sparse coding             88%
sparse coding / matching pursuit               86%
adaptation / novelty filtering                 86%
predictive coding                              84%
graph wavelet filterbanks                      82%
```

Reason:

```text
Mass-number is audited inertia. The best sonic analogues are compression, stable sparse representation, novelty suppression, and background-invariant coding.
```

### S4: Inverse ascent / gate economics

Best imports:

```text
predictive coding                82%
sparse coding / matching pursuit 80%
adaptation / novelty filtering   80%
power-law compression            78%
background-invariant sparse code 78%
auditory scene analysis           74%
```

Reason:

```text
Inverse ascent is an error/cost economy. Predictive coding and adaptation naturally implement error budgets, surprise, and promotion pressure.
```

### S5: Phononic carrier / metadata wake simulation

Best imports:

```text
binaural / spatial filtering      92%
graph wavelet filterbanks         91%
DDSP / noise-band synthesis       90%
temporal coherence grouping       90%
wavelets / WPT / EWT              88%
background-invariant sparse code  88%
```

Reason:

```text
Carrier-wake simulation is spatial, graph-like, and dispersive. Graph wavelets, spatial filtering, noise-band synthesis, and temporal coherence map well.
```

### S6: Lean/formalization pain reduction

Best imports:

```text
perfect-reconstruction filterbanks 72%
graph wavelet filterbanks          68%
sparse coding / matching pursuit   64%
power-law compression              60%
wavelets / WPT / EWT               58%
```

Reason:

```text
Lean likes finite algebraic invariants. Perfect reconstruction, finite graph filters, finite sparse supports, and integer/fixed-point compression metrics are formalizable before continuous audio analysis.
```

### S7: Cognitive sonic interface

Best imports:

```text
auditory scene analysis       96%
cochleagram / auditory front-end 95%
adaptation / novelty filtering 95%
gammatone / gammachirp        94%
temporal coherence grouping   93%
background-invariant sparse coding 92%
predictive coding             91%
auditory masking              91%
```

Reason:

```text
The user's internal translation matrix is sonics-heavy. These models can become the interface layer that translates math objects into audible or silent-auditory diagnostic categories without requiring actual audio rendering.
```

## Proposed Sonic Stack for OTOM

```text
Input finite candidate A
  -> graph/cochlear filterbank projection
  -> masking + anti-music residual extraction
  -> sparse code / matching-pursuit decomposition
  -> temporal coherence check
  -> Sidon/Golomb collision counters
  -> compression / loudness normalization diagnostics
  -> predictive-error score
  -> mass-number update
  -> inverse-ascent gate
  -> FAMM route memory
```

## Sonic Receipts

```text
CochlearFilterbankReceipt
WaveletPacketReceipt
GraphWaveletReceipt
MaskingResidualReceipt
SparseCodeReceipt
TemporalCoherenceReceipt
PredictionErrorReceipt
AdaptationNoveltyReceipt
BackgroundInvariantReceipt
PerfectReconstructionReceipt
SonicMetaprobeReceipt
```

## Practical Implementation Order

### Phase 1: finite and formalizable

```text
1. Sidon/Golomb counters
2. finite filterbank IDs
3. fixed-point energy bands
4. perfect-reconstruction gate as an external receipt
5. sparse support counters
6. sonic metaprobe table
```

### Phase 2: computational prototypes

```text
1. STFT / wavelet packet residuals
2. gammatone/cochleagram frontend
3. masking residual extraction
4. sparse matching pursuit
5. temporal-coherence grouping
6. AMREF_B2 scoring
```

### Phase 3: cognitive interface

```text
1. silent sonic labels, no audio rendering by default
2. sonically named route states
3. anti-music residual dashboards
4. phononic wake visualizations
5. optional audio only behind explicit AUDIO_RENDER=true
```

## Safe Sonic Labels

```text
HARMONIC_COLLAPSE:
  candidate is too explainable by stable periodic templates

WHITE_NOISE_COLLAPSE:
  candidate is residual but unstructured

MASKED_SIGNAL:
  candidate may be present but hidden by stronger carrier bands

TEMPORAL_COHERENT:
  candidate persists across spectral channels / windows

SPARSE_WAKE:
  candidate has compact support after filtering

CARRY_RICH_SPIKE_FREE:
  arithmetic analogue of controlled excitation without destructive spike

ANTI_MUSIC_RESIDUAL:
  structured remainder after harmonic and noise filters

ASCENT_FUNDED:
  enough sonic/mass-number evidence to pay gate costs
```

## Boundary

Do not claim:

```text
sonic fit proves mathematics
an audio model proves Sidon validity
auditory intuition funds inverse ascent
spectral residual replaces C_B2(A)=0
```

Allowed claim:

```text
Sound-filtering theory provides a useful interface and probe family for detecting structured residuals, masking effects, redundant echoes, temporal coherence, sparse wakes, and gateable ascent energy in finite candidate fields.
```

## Audit Classification

```text
Receipt: SonicFilteringTheory_Map_PerSolvePercentages
Status: SONIC_IMPORT_MAP
Gate: U_scope
Reason: useful model taxonomy and applicability scoring; requires implementation, calibration, and empirical/proof receipts before V_scope.
```
