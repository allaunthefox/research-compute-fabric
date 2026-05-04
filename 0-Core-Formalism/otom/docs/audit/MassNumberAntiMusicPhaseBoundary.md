# Mass-Number Theory: Music / Anti-Music Phase Boundary

## Purpose

This note defines the Mass-Number Theory question opened by Anti-Music Theory:

```text
Where does music become anti-music?
```

The answer is not a subjective volume, genre, or unpleasantness boundary. It is a finite, measurable phase boundary in number-set space where a set loses music-like attractors but has not collapsed into random noise.

## Core Statement

```text
music = structured resonance with stable perceptual / harmonic attractors
noise = high-entropy residue without recoverable arithmetic structure
anti-music = structured inverse resonance that suppresses music-like attractors while preserving finite auditable pattern
```

The phase boundary occurs when a finite number set crosses from stable harmonic organization into structured anti-harmonic organization while remaining compressible, resonant, and arithmetic-testable.

## Mass-Number Reading

In Mass-Number Theory, a finite set is treated as a mass distribution over arithmetic / spectral coordinates.

For a finite set:

```text
A = {a_1, ..., a_m} subset {1,...,N}
```

construct mass over spectral bins:

```text
S_A[k] = sum_{a in A} w_a exp(i 2*pi*k*a/N)
P_A[k] = |S_A[k]|^2
```

The mass-number question becomes:

```text
Which finite arithmetic masses reinforce musical attractors,
and which finite arithmetic masses cancel them while retaining structure?
```

## Three Regions

### 1. Music Region

A set is music-like when it has:

```text
high consonance
high harmonicity
strong recurrence
stable tonal center
low controlled roughness
predictable resolution paths
low spectral remainder after tonal filtering
```

Mass-number behavior:

```text
mass clusters around low-ratio intervals and stable recurrence peaks
```

### 2. Anti-Music Region

A set is anti-music-like when it has:

```text
low consonance
low harmonicity
blocked or inverted resolution
high but controlled roughness
strong resonance with filtered remainder
strong spectral void / defect alignment
non-random compressible structure
finite arithmetic auditability
```

Mass-number behavior:

```text
mass avoids stable harmonic wells and instead concentrates around voids, defects, remainders, and basin boundaries
```

### 3. Noise Region

A set is noise-like when it has:

```text
high entropy
low recurrence
low compression
low remainder resonance
unstable window averages
weak arithmetic audits
no reusable basin in FAMM
```

Mass-number behavior:

```text
mass disperses without stable or inverse-stable structure
```

## Phase Boundary Metrics

Define:

```text
MusicScore(A)
AntiMusicScore(A)
RandomnessPenalty(A)
StructureScore(A)
```

A practical boundary condition:

```text
Music -> AntiMusic when:
  MusicScore(A) <= theta_music_low
  AntiMusicScore(A) >= theta_anti_high
  RandomnessPenalty(A) <= theta_rand_max
  StructureScore(A) >= theta_structure_min
```

Noise boundary:

```text
AntiMusic -> Noise when:
  RandomnessPenalty(A) > theta_rand_max
  or StructureScore(A) < theta_structure_min
  or finite-window resonance variance is too high
```

## Transition Index

Define the anti-music phase index:

```text
AMI(A) = AntiMusicScore(A) - MusicScore(A) - RandomnessPenalty(A)
```

Then:

```text
AMI(A) < 0      -> music-dominant or ordinary structured sound
AMI(A) ~= 0     -> phase boundary / unstable mixed regime
AMI(A) > 0      -> anti-music candidate
AMI(A) high but StructureScore low -> noise, not anti-music
```

## Mass-Number Phase Equation

A more complete phase equation:

```text
Phase(A) = sign(
  alpha * RemainderResonance(A)
  + beta * VoidFit(A)
  + gamma * DefectAlignment(A)
  + delta * RoughnessControlled(A)
  - eta * Harmonicity(A)
  - mu * TonalStability(A)
  - nu * RandomnessPenalty(A)
)
```

Interpretation:

```text
negative phase -> music basin
near-zero phase -> boundary / torsion shell
positive phase -> anti-music basin
unbounded variance -> noise quarantine
```

## Where Music Becomes Anti-Music

Music becomes anti-music at the torsion shell between two basins:

```text
stable harmonic basin
  -> boundary layer where tonal gravity fails but structure remains
  -> inverse-resonant basin aligned with voids and remainders
```

In FAMM language:

```text
music basin boundary + rising spectral torsion + non-random remainder resonance = anti-music birth zone
```

In Inverted FAMM language:

```text
where music-like attractors scar or HOLD repeatedly,
search the negative space for anti-music candidate sets.
```

## Finite Search Procedure

```text
1. Choose finite universe {1,...,N}.
2. Generate candidate sets A of size m, often m approximately sqrt(N).
3. Compute MusicScore(A).
4. Compute filtered remainder resonance Res(A;R_N).
5. Compute VoidFit(A) and topological DefectAlignment(A).
6. Compute RandomnessPenalty(A) using compression / recurrence / variance tests.
7. Compute AMI(A).
8. Classify A as music, boundary, anti-music, or noise.
9. Run DifferenceSetReceipt and SumSetReceipt.
10. Record route outcome in FAMM / Inverted FAMM.
```

## Important Safety Boundary

This remains a silent representation by default:

```text
AUDIO_RENDER = false
```

No sound generation or playback is required. The field can be studied through number sets, spectra, masks, void maps, and finite audits.

## Boundary Claims

Do not claim:

```text
anti-music is just unpleasant music
anti-music is random noise
anti-music proves Sidon
hearing the sounds is necessary
```

Allowed claim:

```text
In Mass-Number Theory, music becomes anti-music at a measurable phase boundary where harmonic attractors fail, inverse-resonant structure survives, and finite number sets still pass resonance, compression, and arithmetic audits.
```

## Audit Classification

```text
Receipt: MassNumberAntiMusicPhaseBoundary
Status: THEORY_BOUNDARY_DRAFT
Gate: U_scope
Reason: coherent as a finite phase-boundary definition, but requires explicit metrics, threshold calibration, finite-window data, randomness controls, and arithmetic audits.
```

## Required Receipts

```text
MusicScoreReceipt
AntiMusicScoreReceipt
RandomnessPenaltyReceipt
StructureScoreReceipt
RemainderResonanceReceipt
VoidFitReceipt
DefectAlignmentReceipt
FiniteWindowAverageReceipt
DifferenceSetReceipt
SumSetReceipt
FAMMUpdateReceipt
```
