# Predictive Harmony Social Synchrony Prior

Status: `EXTERNAL_NEUROACOUSTIC_ROUTE_PRIOR`

Source:

```text
PsyPost summary:
https://www.psypost.org/scientists-show-how-common-chord-progressions-unlock-social-bonding-in-the-brain/

Primary study:
Watts, Allsop, Compton, Zhang, Noah, Hirsch.
"Listening to a Consonant Chord Progression during Live Face-to-Face Gaze
Enhances Neural Activity in Social Systems."
Journal of Neuroscience, 2026.
DOI: 10.1523/JNEUROSCI.1116-25.2026
```

## Claim Boundary

This source is admitted as a neuroacoustic route prior:

```text
predictable harmonic structure + live mutual gaze
-> increased social-system activity and cross-brain synchrony in dyads
```

It is not admitted as:

- proof that any chord progression causes bonding in all settings
- a clinical therapy claim
- a social-control mechanism
- a payload authority for the logogram layer
- evidence that music notation alone certifies reconstruction

## Useful Signal Primitive

The useful primitive is not "music makes people bond." The useful primitive is:

```text
shared predictable temporal structure can reduce coordination uncertainty
when paired with a live social alignment channel.
```

In stack language:

```text
harmonic predictability = route prior
live gaze              = mutual-attention gate
dyad synchrony         = cross-agent alignment witness
subjective connection  = reported outcome, not proof
```

## Candidate Equation Shape

Use a bounded gate, not an unbounded claim:

```text
S_harmony = P_chord * G_live * A_cross
```

Where:

```text
P_chord = predictability / consonance / structured-progression score
G_live  = live face-to-face gaze gate, 0 or 1 in the minimal fixture
A_cross = cross-agent temporal alignment witness
```

Admission requires all three axes:

```text
predictable chord progression
+ declared live/mutual attention channel
+ cross-agent synchrony receipt
```

If the same notes are scrambled, the condition is a negative control:

```text
same notes + unstructured timing -> HOLD_OR_NEGATIVE_CONTROL
```

## Compression / Decompression Use

For a decompressor or logogram system, this suggests a useful routing pattern:

```text
predictable harmonic skeleton
-> lower cognitive route load
-> better shared replay alignment
-> smaller residual for timing/social-channel annotations
```

But the decompressor must still verify the payload:

```text
music chart      = route hint
timing/gaze gate = synchronization sidecar
receipt          = replay authority
```

## Encoder Implication

The encoder-side implication is stronger than the decoder-side implication.
The encoder can use predictable harmony as a sidecar for grouping and timing:

```text
event stream
-> harmonic skeleton / cadence lane
-> shared-clock or mutual-attention gate
-> timing residual
-> replay receipt
```

Useful packet fields:

| Field | Purpose |
|---|---|
| `harmony_skeleton_id` | declared chord/cadence template |
| `predictability_score_q0_16` | bounded structured-progression score |
| `attention_gate` | live/shared-context gate, or `0` for absent |
| `alignment_receipt_hash` | measured or simulated synchrony witness |
| `scrambled_control_hash` | same note/event multiset in unstructured order |
| `timing_residual_hash` | residual needed for byte-exact replay |

Encoder admission:

```text
ADMIT_ENCODER_SIDECAR
  if skeleton is declared
  and timing residual exists
  and negative control exists
  and payload hash is independent of the music chart
```

## Gates

```text
ADMIT_ROUTE_PRIOR
  if chord structure is declared
  and live/mutual attention condition is declared
  and synchrony witness exists
  and payload/replay claims stay separate

ADMIT_ENCODER_SIDECAR
  if skeleton, residual, negative control, and independent payload hash exist

HOLD_NO_SYNCHRONY_RECEIPT
  if only subjective connection is reported

HOLD_NO_NEGATIVE_CONTROL
  if no scrambled/unstructured comparator exists

HOLD_THERAPY_CLAIM
  if clinical benefit is claimed without a clinical trial receipt

QUARANTINE_SOCIAL_CONTROL
  if the pattern is framed as manipulation or coercive entrainment
```

## Stack Placement

This belongs under:

- Phonon Music Logogram Layer
- Cognitive Acoustic Dynamics
- Cognitive Load route selection
- BMVR/BVMR synchrony gates
- Social/signal alignment priors

The immediate useful next fixture is a tiny paired-sequence test:

```text
structured progression sidecar
scrambled progression sidecar
same note multiset
same drum grid
different temporal predictability
compare route-load and replay residual
```
