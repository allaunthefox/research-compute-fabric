# Sine Wave Anti-Music Probe

## Purpose

This note defines the simplest silent test signal for Anti-Music Theory and the Mass-Number music / anti-music phase boundary.

The baseline is not an audible tone by default. It is a finite sampled sine wave used as a mathematical carrier for spectral filtering, remainder extraction, and candidate number-set resonance.

```text
AUDIO_RENDER = false
```

## Core Statement

A pure sine wave is the most stable possible musical carrier:

```text
one frequency
one phase
one clean spectral peak
minimal harmonic ambiguity
maximal local predictability
```

Therefore it is a good first substrate for anti-music perturbation. If Anti-Music cannot destabilize a pure sine carrier in a finite, measurable way, the perturbation is not strong enough or not aligned to the correct metric.

## Finite Baseline Signal

Use a finite sampled sine wave:

```text
f_N[n] = sin(2*pi*f0*n/Fs + phi0), 0 <= n < N
```

where:

```text
N   = finite sample count
Fs  = sample rate, symbolic or numeric
f0  = carrier frequency
phi0 = initial phase
```

No infinite waveform is allowed. All tests use finite windows.

## Optional Multi-Window Form

For window index `j`:

```text
f_{N,j}[n] = sin(2*pi*f0*(n+jH)/Fs + phi_j)
```

where:

```text
H = hop size
j = finite window index
```

This supports finite-window averaging:

```text
AvgRes(A) = (1/J) * sum_{j=1}^{J} Res(A; R_{N,j})
```

## Anti-Music Perturbation

Given a finite candidate number set:

```text
A = {a_1,...,a_m}
```

construct a silent perturbation:

```text
P_A[n] = sum_{a in A} w_a sin(2*pi*a*n/N + phi_a)
```

Apply bounded perturbation:

```text
g_N[n] = f_N[n] + epsilon * P_A[n]
```

with:

```text
0 <= epsilon <= epsilon_max
```

## Filtered Remainder

Compute:

```text
F_N[k] = FFT(g_N[n])
```

Remove the known carrier and known noise bands:

```text
F_filtered[k] = H_music[k] F_N[k]
R_N[k] = F_N[k] - F_filtered[k]
```

where `R_N` is the anti-music candidate remainder.

## Candidate Set Resonance

For the same set `A`, compute its spectral fingerprint:

```text
S_A[k] = sum_{a in A} w_a exp(i*2*pi*k*a/N)
P_A[k] = |S_A[k]|^2
```

Score resonance:

```text
Res(A;R_N) = <normalize(P_A), normalize(|R_N|^2)>
```

High resonance means the candidate set explains the residual energy left after removing the stable sine carrier.

## Anti-Music Transition Test

Use:

```text
AMI(A) = AntiMusicScore(A) - MusicScore(A) - RandomnessPenalty(A)
```

The sine-wave carrier test should classify:

```text
Music basin:
  epsilon small, carrier dominates, AMI(A) < 0

Boundary shell:
  residual grows, carrier remains recoverable, AMI(A) ~= 0

Anti-music candidate:
  structured residual survives filtering, AMI(A) > 0, StructureScore high

Noise quarantine:
  residual grows but structure score collapses or variance explodes
```

## Minimal Starting Candidate Sets

Use small finite sets first:

```text
A_music_like = {1,2,3,4,5}
A_sidon_like = {1,2,5,10,17}
A_prime_like = {2,3,5,7,11}
A_anti_candidate = search result maximizing AntiMusicScore(A)
```

The set `{1,2,5,10,17}` is useful because it was already used as a finite spectral-void example and has sparse nonuniform spacing.

## Arithmetic Audit

After resonance discovery, run:

```text
DifferenceSetReceipt:
  |{ |a_i-a_j| : i<j }| = m(m-1)/2

SumSetReceipt:
  |{ a_i+a_j : i<=j }| = m(m+1)/2
```

The sine wave only provides the carrier and residual. It does not prove Sidon.

## Minimal Pseudocode

```text
input: N, Fs, f0, epsilon, candidate set A
f = sine(N, Fs, f0)
P = sum_sines_from_A(A, N)
g = f + epsilon * P
F = FFT(g)
R = F - H_music * F
score = resonance(power_fingerprint(A), abs(R)^2)
audit A with difference and sum-set tests
```

## Why This Is the Correct First Probe

A sine wave gives a maximally stable baseline. Anti-Music is then forced to prove it can create structured remainder rather than hiding inside preexisting complexity.

```text
pure sine = stable music basin
anti-music perturbation = controlled destabilizer
filtered remainder = measurable inverse structure
finite average = stability receipt
arithmetic audit = proof boundary
```

## Boundary

Do not claim:

```text
sine perturbation proves anti-music
hearing the tone is required
audio rendering is needed
resonance score proves Sidon
```

Allowed claim:

```text
A finite sampled sine wave is the cleanest silent carrier for testing whether anti-music number sets create structured, auditable residuals after tonal filtering.
```

## Audit Classification

```text
Receipt: SineWaveAntiMusicProbe
Status: BASELINE_SIGNAL_DRAFT
Gate: U_scope
Reason: defines a finite test carrier and perturbation procedure, but requires actual finite data runs, thresholds, resonance statistics, and arithmetic audits.
```

## Required Receipts

```text
FiniteSignalReceipt
CarrierDefinitionReceipt
PerturbationBoundReceipt
FFTFilterReceipt
RemainderDefinitionReceipt
RemainderResonanceReceipt
FiniteWindowAverageReceipt
RandomnessPenaltyReceipt
DifferenceSetReceipt
SumSetReceipt
ValidatorReceipt
```
