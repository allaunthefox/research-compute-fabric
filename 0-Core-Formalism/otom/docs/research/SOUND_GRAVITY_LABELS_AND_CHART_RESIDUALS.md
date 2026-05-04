# Sound Gravity Labels and Chart Residuals

Status: BEAUTIFUL_PROVISIONAL
Date: 2026-05-03

## Core thesis

Culture should not be modeled only as a set of separate networks. A culture can be modeled as a gravity basin over embodied meaning: an attractor landscape that pulls rhythm, ritual, language, movement, market behavior, identity, and stress response into patterned orbits.

Music is one of the highest-resolution observables of this basin because it exposes timing structure: pulse, repetition, voice, affect, gesture, synchrony, platform loopability, and memory.

> Culture bends sound into orbit, and stress reveals the curvature.

## From music to Sound Gravity Labels

The category `music` is too narrow. The observable should include all labeled acoustic-social artifacts.

A Sound Gravity Label (SGL) is any repeatable acoustic, rhythmic, vocal, textual, gestural, or platform-mediated pattern that communities recognize, transmit, imitate, monetize, ritualize, or use for affect regulation.

Examples:

- conventional genres: pop, trap, reggaeton, amapiano, country, gospel, K-pop, J-pop, Bollywood, funk carioca, dancehall;
- microgenres: phonk, drift phonk, pluggnb, rage rap, hyperpop, nightcore, sped-up pop, slowed + reverb, Jersey club, sigilkore, krushclub, lofi hip hop;
- functional labels: lullaby, work song, military cadence, protest chant, sports chant, religious chant, mourning song, wedding music, funeral music, school song, national anthem, advertising jingle, nursery rhyme, sea shanty, DJ drop, producer tag, rave build/drop, alarm, siren, notification sound;
- platform labels: TikTok sound, remix template, fan chant, meme loop, sample-pack tag, producer watermark.

## Chart residual theory

The `Top 10` is not culture itself. It is a low-rank market projection of a high-dimensional cultural sound manifold.

The true cultural sound field contains local rituals, microgenres, private listening, dance trends, mourning songs, religious sounds, regional scenes, algorithmic playlists, memes, remixes, language clusters, diaspora circuits, stress states, identity markers, and market incentives.

A public chart compresses this field through:

```text
streams + sales + radio + platform weightings + reporting rules = ranked list
```

A chart hit is therefore a compression artifact: a sound object that retained enough affective density, rhythmic accessibility, platform compatibility, and identity resonance to remain visible after dimensional collapse.

Strictly, the Top 10 are projected extrema or dominant components, while the hidden residual is everything the projection fails to reconstruct. As a working metaphor, they are residual survivors of dimensional collapse.

Formal sketch:

```text
X = high-dimensional cultural sound-label field
P = platform-market projection operator
Y = P(X)
TopK(Y) = ranked chart-visible attractors
R = X - X_hat(TopK)
```

Where `R` contains hidden cultural mass: underground scenes, regional gravity wells, ritual music, protest sound, grief songs, micro-label acceleration, non-market music, platform-suppressed genres, local language basins, diasporic subfields, and family/faith/community soundforms.

> Charts show the peaks. Residuals show the terrain.

## Culture as a gravity basin

A culture basin can be represented as a state vector:

```text
C_t = { r_t, m_t, l_t, g_t, e_t, s_t, p_t }
```

Where:

- `r_t` = rhythm / pulse distribution;
- `m_t` = melodic and tonal conventions;
- `l_t` = language / lyrical-symbolic field;
- `g_t` = gesture / dance / embodied motion;
- `e_t` = emotional valence-arousal distribution;
- `s_t` = social synchronization density;
- `p_t` = platform / market propagation layer.

The basin is the attractor landscape over that state:

```text
B(C) = -grad V(C)
```

Where `V(C)` is a cultural potential landscape. A culture has gravity when certain rhythms, stories, gestures, and emotional postures are easier to fall into, repeat, monetize, remember, and transmit than others.

## SGL schema

```text
SGL {
  label: String
  scale: Macro | Meso | Micro | Nano | Functional | Ritual | Platform
  origin_region: Optional Region
  carrier: Audio | Voice | Rhythm | Gesture | Text | PlatformLoop | Hybrid
  bpm_raw_range: Range
  bpm_felt_range: Range
  affect_vector: {valence, arousal, dominance}
  synchrony_mode: Solo | Dyadic | Group | Crowd | Networked
  ritual_function: Optional Function
  stress_function: Optional Function
  transmission_mode: Oral | Radio | Streaming | TikTok | Live | Worship | Protest | Family | Meme
  identity_markers: Set
  perceptual_features: PsychoacousticFeatureVector
  scene_features: AuditorySceneFeatureVector
  basin_mass: Float
  basin_curvature: Float
  escape_velocity: Float
  half_life: Duration
}
```

## Psychoacoustic sensor layer

Psychoacoustics supplies the sensor layer for the SGL model. Anthropology and ethnomusicology describe social function; psychoacoustics describes how acoustic structure becomes perceptible, salient, affective, and streamable by the nervous system.

The revised pipeline is:

```text
physical acoustic field
→ psychoacoustic feature extraction
→ auditory scene analysis
→ affective appraisal
→ cultural labeling
→ basin attraction
→ platform-market projection
→ chart-visible residue
```

This means an SGL should not only store cultural labels. It should also store measurable perceptual descriptors.

### PsychoacousticFeatureVector

```text
PsychoacousticFeatureVector {
  loudness: Distribution
  tempo: Range
  felt_pulse: Range
  temporal_envelope: Descriptor
  attack_sharpness: Float
  spectral_centroid: Distribution
  spectral_flux: Distribution
  roughness: Float
  sharpness: Float
  harmonicity: Float
  noisiness: Float
  dynamic_range: Range
  tonality: Float
  fluctuation_strength: Float
  salience: Float
  expectation_strength: Float
}
```

Candidate evidence channels:

- rhythmic entrainment: perceptual, autonomic, motor, and social entrainment;
- musical rhythm networks: auditory-motor coupling, beat perception, basal ganglia / SMA / cerebellar involvement;
- timbre and affect: spectral envelope, noisiness, dynamic range, temporal envelope, and enculturation effects;
- consonance / scale perception: harmonicity, roughness, slow beating, fast beating, and timbre-dependent interval preference;
- soundscape psychoacoustics: loudness, sharpness, roughness, fluctuation strength, tonality, pleasantness, eventfulness, calmness, vibrancy;
- acoustic emotion cues shared by speech and music: loudness, tempo/speech rate, melody/prosody contour, spectral centroid, spectral flux, sharpness, and roughness.

### AuditorySceneFeatureVector

```text
AuditorySceneFeatureVector {
  stream_separability: Float
  foreground_background_contrast: Float
  timbre_distance: Float
  masking_load: Float
  attention_capture: Float
  repetition_index: Float
  predictability: Float
  source_legibility: Float
  semantic_referentiality: Float
  binaural_spatiality: Float
}
```

Auditory scene analysis is a dimensional reduction step before cultural labeling. The listener must organize a physical mixture into perceptual streams. This implies that chart projection is not the first compression stage; it is a late market-facing stage after acoustic, neural, affective, social, and platform compression.

```text
physical mixture
→ auditory scene segregation / integration
→ attended stream
→ affective interpretation
→ label assignment
→ social transmission
```

## Feature-to-basin mapping

Psychoacoustic features should be interpreted as inputs to basin dynamics, not as direct causes of culture.

| Feature family | Possible basin role |
|---|---|
| Loudness / dynamic range | arousal, urgency, dominance, vigilance |
| Tempo / felt pulse | motor entrainment, movement grammar, social synchrony |
| Temporal envelope / attack | timing precision, groove lock, impact, perceived urgency |
| Spectral centroid / sharpness | brightness, tension, strain, attention capture |
| Roughness / noisiness | aggression, instability, danger, excitement, dysphoria |
| Harmonicity / consonance | stability, tonal gravity, scale-system affinity |
| Spectral flux | motion, novelty, eventfulness |
| Tonality | pitch-center stability, chantability, memory compression |
| Fluctuation strength | pulsing, modulation salience, annoyance or groove depending on context |
| Salience | probability of attention capture and meme extraction |
| Expectation strength | predictability, release, surprise, reward timing |
| Stream separability | source legibility, mix clarity, identity extraction |
| Masking load | cognitive load, density, fatigue, dissociation potential |
| Semantic referentiality | source recognition, social meaning, compensatory interpretation |

## Psychoacoustic guardrails

- Do not reduce culture to sound metrics. Acoustic features are basin inputs, not total explanations.
- Do not infer stress physiology directly from BPM, loudness, or roughness without physiological or behavioral data.
- Treat valence as more culture-dependent than arousal unless a specific study shows otherwise.
- Separate perceived emotion from felt emotion when possible.
- Track context: ritual, platform, domestic space, club, street, worship, protest, commute, study, mourning, and performance settings may invert the meaning of the same acoustic feature.
- Specify computation methods for psychoacoustic indicators; otherwise cross-study comparison becomes weak.
- Prefer distributions and percentiles over single scalar means for loudness, sharpness, tempo, and salience.

## Basin metrics

### Basin mass

How much attention, identity, and synchronization a label can hold.

```text
basin_mass = replay_volume
           + social_imitation
           + identity_density
           + ritual_frequency
           + market_conversion
           + cross-platform_persistence
           + perceptual_salience
           + affective_utility
```

### Basin curvature

How strongly the label pulls variants back toward its signature.

```text
curvature = recognizability_after_variation
          + return_to_core_pulse
          + production_template_stability
          + dance_or_gesture_consistency
          + timbre_signature_stability
          + envelope_signature_stability
```

High-curvature examples: reggaeton dembow, amapiano log drum, Jersey club kick pattern, drill hi-hat/sliding bass grammar, national anthem cadence, Gregorian-style chant, marching cadence.

### Escape velocity

How hard it is for the label to break out of its native basin.

```text
escape_velocity = local_context_dependency
                + language_dependency
                + ritual_dependency
                + platform_penalty
                + timbre_unfamiliarity
                + scene_analysis_difficulty
                - bodily_universality
                - memeability
                - diaspora_bridge
                - perceptual_salience
```

## Stress-response classes

| Stress response class | Common SGLs | Likely psychoacoustic tendency |
|---|---|---|
| Downregulation | lofi, ambient, lullaby, ballads, devotional chant | lower sharpness, predictable envelopes, lower arousal |
| Mobilization | protest chant, punk, drill, rage rap, military cadence | strong attacks, chantability, high repetition, high dominance |
| Dissociation | slowed + reverb, vaporwave, ambient drone, shoegaze | blurred attacks, high reverb, low source separability |
| Acceleration | nightcore, sped-up pop, hyperpop, phonk, J-pop/anime | high tempo/felt pulse, bright spectra, high event density |
| Collective repair | gospel, group singing, folk revival, festival music | vocal salience, synchrony affordance, repetition |
| Identity hardening | national anthem, regional music, country, corridos, metal | stable motifs, source-recognizable timbre, high semantic density |
| Body reconnection | reggaeton, Afrobeats, amapiano, dancehall, funk carioca | strong groove, mid-tempo entrainment, clear pulse hierarchy |
| Nostalgia stabilization | retro synth-pop, oldies revival, samples, remixes | familiar timbres, predictable harmonic/melodic contours |
| Platform entrainment | TikTok sounds, meme songs, producer tags, loop edits | short hook windows, high salience, rapid source legibility |

## Species-level stressor hypothesis

During species-level stressors, populations do not randomly select songs or soundforms. They fall toward attractors that let them continue functioning.

A defensible hypothesis:

> Global hit songs and high-propagation sound labels during species-level stressors function as mass-scale affect-regulation artifacts. Their tempo, groove, voice, repetition, familiarity, psychoacoustic salience, and platform loopability provide distributed timing scaffolds through which individuals regulate emotion, simulate social connection, and maintain embodied continuity under disruption.

COVID-era examples should be treated as suggestive, not proof: chart-visible hits are low-dimensional outputs and must be interpreted alongside hidden residual fields.

## Research program

1. Build a dataset of macro, meso, micro, functional, ritual, and platform sound labels.
2. For each SGL, estimate raw BPM range, felt pulse range, affect vector, synchrony mode, transmission mode, identity markers, psychoacoustic feature vector, auditory-scene feature vector, basin mass, curvature, escape velocity, and half-life.
3. Compare chart-visible TopK outputs against micro-label and ritual residual fields.
4. Measure projection error: what does the Top 10 fail to reconstruct?
5. Test whether major stressors increase the propagation of specific SGL classes: downregulation, mobilization, dissociation, acceleration, collective repair, identity hardening, body reconnection, nostalgia stabilization, or platform entrainment.
6. Test whether psychoacoustic variables predict propagation differently by context: domestic listening, club, worship, protest, study, driving, grief ritual, exercise, TikTok, radio, and concert/festival settings.
7. Track perceptual residuals: cases where acoustic features predict attention but not meaning, or cultural labels predict meaning despite low acoustic salience.

## Minimal dataset columns

```text
label
scale
origin_region
carrier
bpm_raw_min
bpm_raw_max
bpm_felt_min
bpm_felt_max
loudness_percentiles
spectral_centroid_mean
spectral_flux_mean
roughness
sharpness
harmonicity
noisiness
dynamic_range
tonality
fluctuation_strength
salience
expectation_strength
stream_separability
masking_load
semantic_referentiality
affect_valence
affect_arousal
affect_dominance
synchrony_mode
ritual_function
stress_function
transmission_mode
identity_markers
basin_mass
basin_curvature
escape_velocity
half_life
evidence_sources
claim_state
```

## Guardrails

- Do not claim BPM directly causes cultural behavior.
- Do not treat chart data as direct culture measurement.
- Treat Top 10 tracks as projected extrema, not the full manifold.
- Use anthropology, ethnomusicology, psychoacoustics, streaming behavior, platform studies, and ritual studies as separate evidence channels.
- Keep psychoacoustic features as measurable sensor inputs, not metaphysical causes.
- Keep claims at BEAUTIFUL_PROVISIONAL until dataset, baselines, and statistical tests exist.
