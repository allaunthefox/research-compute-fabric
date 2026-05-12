# Multi-Domain Adaptive Cognitive Load Functions

## Overview

The Φ-scaling response-family framework enables adaptive cognitive load functions across multiple information domains. Instead of fixed linear coefficients, each domain selects its optimal response family (log, Hill, Michaelis-Menten, low-exponent power) based on measured error, complexity penalty, and held-out validation.

## 2026-05-08 Reweighting: Connectome Protection + Historical Bandwidth Overflow

This revision treats the overflow mechanism as a **model hypothesis** about preserving working graph stability under overload, not as a proven biological claim. Emotional offload is not free load deletion: it is a separate channel with its own energy barrier, residual stress term, and validation burden.

The primary use is historical / civilizational modeling of cognitive overload under accelerated information transfer. Trauma remains one local energy-cost modifier, but the broader historical variable is bandwidth overflow: information transfer rate exceeding assimilation capacity.

Bandwidth overflow:

```
B_overflow =
  max(0, transfer_bandwidth - assimilation_bandwidth)
  / assimilation_bandwidth
```

Historical threshold:

```
L_threshold_hist =
  L_threshold_eff · exp(-rho_B · B_overflow)
```

Historical emotional barrier and temperature:

```
DeltaE_emotional_hist =
  DeltaE_emotional_eff + chi_B · B_overflow

kT_emotional_hist =
  kT_emotional_eff / (1 + psi_B · B_overflow)
```

Historical offload efficiency:

```
eta_offload_hist =
  eta_offload_eff · exp(-omega_B · B_overflow)
```

Interpretation:

```
accelerated information transfer can lower effective assimilation threshold
accelerated information transfer can raise emotional/institutional regulation barriers
accelerated information transfer can reduce clean offload efficiency
accelerated information transfer can increase residual social/emotional stress
```

Psychohistory analogy:

```
Harry Seldon's model is a useful fictional analogue for the population-scale
version of this equation:

  not individual prediction
  but aggregate phase-pressure modeling
  from bandwidth, assimilation lag, institutional response,
  and emotional overflow dynamics
```

Boundary:

```
psychohistory is a structural metaphor here, not evidence.
It helps name the shape: population-scale cognitive load under accelerated
information transfer.
```

In the trauma-aware local version, trauma is modeled as an energy-landscape modifier:

```
L_threshold_eff =
  L_threshold · exp(-rho_T · T_trauma)

DeltaE_emotional_eff =
  DeltaE_emotional + chi_T · T_trauma

kT_emotional_eff =
  kT_emotional / (1 + psi_T · T_trauma)

eta_offload_eff =
  eta_offload · exp(-omega_T · T_trauma)
```

Interpretation:

```
trauma can lower the effective cognitive threshold
trauma can raise the emotional regulation barrier
trauma can reduce offload efficiency
trauma can increase residual stress after overflow
```

Claim boundary:

```
T_trauma is not a scalar diagnosis of a person.
It is a model-side stress / exposure proxy that requires consent,
privacy boundaries, and empirical calibration before any real use.

B_overflow is not a single-cause theory of history.
It requires source anchors such as archive volume, media speed,
literacy/education capacity, institutional response lag, infrastructure
reach, or other measured transfer/assimilation proxies.
```

## Multi-Domain Cognitive Load Equation

```
Cognitive_Load(domain, complexity) =
  C_domain(domain)
  · response_family(complexity; θ_domain)
  · lambda_phi^{D_f}
  · B_gate(domain, constraints)
  · overflow_gate(domain, L_cognitive, L_threshold)
```

where:
- `domain` = information type (text, code, visual, audio, multimodal)
- `C_domain(domain)` = domain normalization constant
- `response_family` = selected per domain (log, Hill, Michaelis-Menten, low-exponent)
- `θ_domain` = fitted response parameters for domain
- `lambda_phi^{D_f}` = fractal gain (4 if lambda_phi = Φ², 2 if lambda_phi = Φ)
- `B_gate(domain, constraints)` = binding/admissibility gate for domain constraints
- `overflow_gate` = connectome-protective overflow to emotional processing

## Connectome-Protective Overflow Mechanism

### Hypothesis

**To protect its connectome, cognitive overflow is shifted to emotional processing.**

When cognitive load exceeds a protective threshold, this model shifts excess cognitive demand into an emotional offload channel. The defensible version is that this may preserve working graph stability by preventing overload propagation in cognitive processing routes. It does not prove structural damage prevention.

### Overflow Gate Function

```
overflow_gate(domain, L_cognitive, L_threshold) =
  if L_cognitive ≤ L_threshold_hist:
    1.0 (no overflow)
  else:
    exp(-gamma · (L_cognitive - L_threshold_hist) / kT_emotional_hist)
```

where:
- `L_cognitive` = current cognitive load (L_I + L_E + L_G + L_R + L_M)
- `L_threshold_hist` = trauma-and-bandwidth-adjusted protective threshold
- `gamma` = overflow coefficient
- `kT_emotional_hist` = trauma-and-bandwidth-adjusted emotional processing energy scale

### Emotional Offloading

When overflow occurs, excess cognitive load is shifted to emotional processing:

```
L_emotional_offload = max(0, L_cognitive - L_threshold_hist) · eta_offload_hist
```

**Emotional Load Response**:
```
L_emotional = C_emotional · response_family(L_emotional_offload; θ_emotional) · lambda_phi^{D_f} · B_gate_emotional
```

**Response Family**: `low_exponent_power` (emotional regulation limits)
```
L_emotional = C_emotional · (L_emotional_offload)^{α_emotional} · lambda_phi^{D_f} · B_gate_emotional
```

where:
- `α_emotional` = 0.3-0.5 (low exponent, emotional regulation capacity)
- `C_emotional` = emotional normalization constant
- `B_gate_emotional` = emotional offloading gate (social support, coping mechanisms)

### Connectome Protection Mechanism

**Threshold Selection**:
```
L_threshold = C_threshold · lambda_phi^{D_f} · B_gate_threshold
```

where:
- `C_threshold` = threshold normalization constant
- `B_gate_threshold` = individual threshold gate (baseline cognitive capacity)

**Protection Mechanism**:
1. Cognitive load increases with information complexity
2. When L_cognitive > L_threshold_hist, overflow activates
3. Excess load shifts into an emotional processing / salience channel
4. Cognitive graph routes are protected from overload propagation in the model
5. Emotional processing regulates offloaded load through emotional regulation mechanisms
6. If offload is inefficient, residual stress remains and must be counted

### Updated Total Load with Emotional Offloading

```
L_total = L_cog_eff + L_emotional + L_residual_stress
```

where:
- `L_cog_eff` = cognitive load after overflow suppression
- `L_emotional` = emotional offload response
- `L_residual_stress` = unresolved excess load after offload inefficiency

### Emotional Regulation Gate

```
B_gate_emotional = exp(-gamma_emotional · DeltaE_emotional_hist / kT_emotional_hist)
```

where:
- `DeltaE_emotional_hist` = trauma-and-bandwidth-adjusted emotional regulation barrier
- `gamma_emotional` = emotional regulation coefficient
- Offloading reduces emotional load through:
  - Social support
  - Coping mechanisms
  - Emotional regulation strategies
  - Stress reduction

### Domain-Specific Emotional Offloading

**Text Processing**:
```
L_emotional_text = C_emotional_text · log(1 + β_emotional_text · L_emotional_offload_text) · lambda_phi^{D_f} · B_gate_emotional_text
```

**Code Processing**:
```
L_emotional_code = C_emotional_code · (L_emotional_offload_code / (K_emotional + L_emotional_offload_code))^{hill_emotional} · lambda_phi^{D_f} · B_gate_emotional_code
```

**Visual Processing**:
```
L_emotional_visual = C_emotional_visual · (V_max_emotional · L_emotional_offload_visual) / (K_M_emotional + L_emotional_offload_visual) · lambda_phi^{D_f} · B_gate_emotional_visual
```

**Audio Processing**:
```
L_emotional_audio = C_emotional_audio · (L_emotional_offload_audio)^{α_emotional} · lambda_phi^{D_f} · B_gate_emotional_audio
```

**Multimodal**:
```
L_emotional_multi = Σ w_d · L_emotional_d
```

## Domain-Specific Response Families

### Text Processing Domain

**Response Family**: `log_mutations` (Weber-Fechner perception)

```
L_text = C_text · log(1 + β_text · word_count) · lambda_phi^{D_f} · B_gate_text
```

**Parameters**:
- `β_text` = 0.316 (fitted to reading comprehension data)
- `C_text` = domain normalization (fitted)
- `B_gate_text` = attentional capacity gate

**Load Components**:
- `L_I_text = C_I_text · log(1 + β_I · semantic_complexity)`
- `L_E_text = C_E_text · log(1 + β_E · formatting_complexity)`
- `L_G_text = C_G_text · log(1 + β_G · vocabulary_novelty)`
- `L_R_text = C_R_text · log(1 + β_R · discourse_structure)`
- `L_M_text = C_M_text · log(1 + β_M · working_memory_demand)`
- `L_emotional_text = C_emotional_text · log(1 + β_emotional_text · L_emotional_offload_text) · lambda_phi^{D_f} · B_gate_emotional_text`

**Adaptive Behavior**: Logarithmic scaling matches Weber-Fechner perception of text length and complexity. Emotional offloading activates when cognitive load exceeds threshold.

### Code Processing Domain

**Response Family**: `hill_saturation` (working memory limits)

```
L_code = C_code · (complexity / (K_code + complexity))^{hill_code} · lambda_phi^{D_f} · B_gate_code
```

**Parameters**:
- `K_code` = 200 (half-saturation constant)
- `hill_code` = 0.5 (Hill coefficient)
- `C_code` = domain normalization (fitted)
- `B_gate_code` = syntax/semantic gate

**Load Components**:
- `L_I_code = C_I_code · (lines / (K_I + lines))^{hill_I}`
- `L_E_code = C_E_code · (nesting / (K_E + nesting))^{hill_E}`
- `L_G_code = C_G_code · (abstractions / (K_G + abstractions))^{hill_G}`
- `L_R_code = C_R_code · (dependencies / (K_R + dependencies))^{hill_R}`
- `L_M_code = C_M_code · (variables / (K_M + variables))^{hill_M}`
- `L_emotional_code = C_emotional_code · (L_emotional_offload_code / (K_emotional + L_emotional_offload_code))^{hill_emotional} · lambda_phi^{D_f} · B_gate_emotional_code`

**Adaptive Behavior**: Hill saturation captures working memory limits for holding code context. Emotional offloading activates when cognitive load exceeds threshold, reducing overload propagation from coding frustration in the model.

### Visual Processing Domain

**Response Family**: `michaelis_menten` (feature extraction saturation)

```
L_visual = C_visual · (V_max · visual_complexity) / (K_M + visual_complexity) · lambda_phi^{D_f} · B_gate_visual
```

**Parameters**:
- `V_max` = maximum cognitive capacity
- `K_M` = Michaelis constant (half-saturation)
- `C_visual` = domain normalization (fitted)
- `B_gate_visual` = visual attention gate

**Load Components**:
- `L_I_visual = C_I_visual · (V_max_I · features) / (K_M_I + features)`
- `L_E_visual = C_E_visual · (V_max_E · clutter) / (K_M_E + clutter)`
- `L_G_visual = C_G_visual · (V_max_G · patterns) / (K_M_G + patterns)`
- `L_R_visual = C_R_visual · (V_max_R · saccades) / (K_M_R + saccades)`
- `L_M_visual = C_M_visual · (V_max_M · objects) / (K_M_M + objects)`
- `L_emotional_visual = C_emotional_visual · (V_max_emotional · L_emotional_offload_visual) / (K_M_emotional + L_emotional_offload_visual) · lambda_phi^{D_f} · B_gate_emotional_visual`

**Adaptive Behavior**: Michaelis-Menten captures feature extraction saturation in visual processing. Emotional offloading activates when visual cognitive load exceeds threshold, reducing overload propagation from visual overload in the model.

### Audio Processing Domain

**Response Family**: `low_exponent_power` (speech comprehension)

```
L_audio = C_audio · (audio_complexity)^{α_audio} · lambda_phi^{D_f} · B_gate_audio
```

**Parameters**:
- `α_audio` = 0.3 (low exponent, < 1)
- `C_audio` = domain normalization (fitted)
- `B_gate_audio` = auditory working memory gate

**Load Components**:
- `L_I_audio = C_I_audio · (duration)^{α_I}`
- `L_E_audio = C_E_audio · (noise)^{α_E}`
- `L_G_audio = C_G_audio · (vocabulary)^{α_G}`
- `L_R_audio = C_R_audio · (speakers)^{α_R}`
- `L_M_audio = C_M_audio · (tempo)^{α_M}`
- `L_emotional_audio = C_emotional_audio · (L_emotional_offload_audio)^{α_emotional} · lambda_phi^{D_f} · B_gate_emotional_audio`

**Adaptive Behavior**: Low-exponent power captures speech comprehension scaling. Emotional offloading activates when audio cognitive load exceeds threshold, reducing overload propagation from auditory overload in the model.

### Multimodal Domain

**Response Family**: `adaptive_mixture` (cross-domain integration)

```
L_multimodal = C_multi · Σ w_d · response_family_d(complexity_d; θ_d) · lambda_phi^{D_f} · B_gate_multi
```

**Parameters**:
- `w_d` = domain weights (text, code, visual, audio)
- `response_family_d` = domain-specific response family
- `θ_d` = domain-specific parameters
- `C_multi` = domain normalization (fitted)
- `B_gate_multi` = cross-modal integration gate

**Load Components**:
- `L_I_multi = Σ w_d · L_I_d` (intrinsic load across modalities)
- `L_E_multi = Σ w_d · L_E_d` (extraneous load across modalities)
- `L_G_multi = Σ w_d · L_G_d` (germane load across modalities)
- `L_R_multi = Σ w_d · L_R_d` (routing load across modalities)
- `L_M_multi = Σ w_d · L_M_d` (memory load across modalities)
- `L_emotional_multi = Σ w_d · L_emotional_d` (emotional offloading across modalities)

**Adaptive Behavior**: Adaptive mixture captures cross-modal integration and interference. Emotional offloading activates when multimodal cognitive load exceeds threshold, reducing overload propagation from cross-modal overload in the model.

## Adaptive Function Selection Mechanism

### Selection Criteria

**Measured Error**: Fit response families to domain-specific cognitive load data, compute average error.

**Complexity Penalty**: Apply Occam's razor penalty for model complexity (number of parameters).

**Held-Out Validation**: Cross-validate on held-out data to prevent overfitting.

**Selection Score**:

```
Score(domain, response_family) =
  error(domain, response_family)
  + λ_complexity · complexity(response_family)
  + λ_validation · validation_error(domain, response_family)
```

where:
- `λ_complexity` = complexity penalty weight
- `λ_validation` = validation penalty weight

### Adaptive Selection Algorithm

```
1. For each domain:
   a. Fit all response families (log, Hill, Michaelis-Menten, low-exponent)
   b. Compute selection score for each family
   c. Select family with minimum score

2. For each load component within domain:
   a. Fit all response families
   b. Compute selection score
   c. Select family with minimum score

3. For cross-domain integration:
   a. Fit mixture weights
   b. Compute selection score
   c. Select optimal mixture
```

## Cross-Domain Transfer Learning

### Shared Fractal Dimension

All domains share the same fractal dimension:

```
D_f = log(2)/log(Φ) ≈ 1.44042
```

This enables:
- Transfer of fractal scaling knowledge across domains
- Unified topological prior for all information types
- Consistent compression ratios across domains

### Domain-Specific Adaptation

Each domain adapts:
- Response family selection (log vs Hill vs Michaelis-Menten vs low-exponent)
- Response parameters (K, hill, α, β)
- Domain normalization (C_domain)
- Binding gates (B_gate)

### Hierarchical Adaptation

**Level 1**: Domain-level response family selection
**Level 2**: Component-level response family selection (intrinsic, extraneous, etc.)
**Level 3**: Cross-domain mixture adaptation

## Adaptive Cognitive Load Examples

### Example 1: Text Code Review

**Domain**: Code processing
**Response Family**: Hill saturation
**Complexity**: 500 lines of code

```
L_code = C_code · (500 / (200 + 500))^{0.5} · 4 · B_gate_code
      = C_code · (0.714)^{0.5} · 4 · B_gate_code
      = C_code · 0.845 · 4 · B_gate_code
      = 3.38 · C_code · B_gate_code
```

**Adaptive Behavior**: Hill saturation captures working memory limits for code review.

### Example 2: Multimodal Learning

**Domain**: Multimodal (text + visual)
**Response Family**: Adaptive mixture
**Complexity**: 1000 words + 10 images

```
L_multimodal = C_multi · (w_text · L_text + w_visual · L_visual) · 4 · B_gate_multi

L_text = C_text · log(1 + 0.316 · 1000) · 4 · B_gate_text
       = C_text · log(317) · 4 · B_gate_text
       = C_text · 5.76 · 4 · B_gate_text
       = 23.04 · C_text · B_gate_text

L_visual = C_visual · (V_max · 10) / (K_M + 10) · 4 · B_gate_visual
        = C_visual · (V_max · 10) / (K_M + 10) · 4 · B_gate_visual

L_multimodal = C_multi · (w_text · 23.04 · C_text · B_gate_text
                      + w_visual · L_visual) · 4 · B_gate_multi
```

**Adaptive Behavior**: Adaptive mixture captures cross-modal integration and interference.

## Key Capabilities

### 1. Domain-Aware Scaling
Different information types use different response families based on empirical validation.

### 2. Component-Level Adaptation
Each load component (intrinsic, extraneous, germane, routing, memory) can use different response families.

### 3. Cross-Modal Integration
Multimodal domains use adaptive mixtures of domain-specific response families.

### 4. Transfer Learning
Shared fractal dimension D_f = 1.44042 across domains.

### 5. Hierarchical Adaptation
Multi-level adaptation from domain to component to cross-domain integration.

### 6. Receipt-Based Selection
Response families selected by measured error, complexity penalty, and held-out validation.

### 7. Connectome-Protective Overflow
Cognitive overflow shifted to emotional processing when load exceeds threshold, protecting neural network topology.

### 8. Emotional Regulation Gates
Emotional offloading regulated through social support, coping mechanisms, and emotional regulation strategies.

### 9. Adaptive Threshold Selection
Individualized connectome-protective thresholds based on baseline cognitive capacity.

### 10. Dynamic Load Balancing
Real-time shifting of cognitive load to emotional processing to prevent connectome damage.

## Implementation Requirements

### Data Collection
- Cognitive load measurements for each domain
- Complexity metrics for each information type
- Cross-domain interaction data
- Emotional load measurements during cognitive overflow
- Connectome-protective threshold measurements
- Trauma / stress proxy only when consent, privacy, and calibration boundaries are explicit
- Historical bandwidth-transfer proxies and assimilation-capacity proxies for historical modeling

### Model Fitting
- Fit response families to domain-specific data
- Compute selection scores
- Validate on held-out data
- Fit emotional offloading parameters
- Calibrate connectome-protective thresholds

### Adaptive Runtime
- Select optimal response family per domain
- Adapt parameters based on new data
- Update cross-domain mixture weights
- Monitor cognitive load vs threshold
- Trigger emotional offloading when threshold exceeded
- Apply trauma-aware threshold, barrier, and residual-stress modifiers when calibrated
- Apply bandwidth-overflow threshold, barrier, and residual-stress modifiers when calibrated
- Regulate emotional load through coping mechanisms

## Conclusion

The Φ-scaling response-family framework enables adaptive cognitive load functions across multiple information domains. Each domain selects its optimal response family based on empirical validation, enabling domain-aware scaling, component-level adaptation, cross-modal integration, and transfer learning. This provides a unified mathematical framework for cognitive load across text, code, visual, audio, and multimodal information processing.

The connectome-protective overflow mechanism adds a biological, computational, and historical hypothesis: when cognitive load exceeds a protective threshold, excess load is shifted into emotional processing / salience handling to preserve working graph stability. In the historical bandwidth-overflow reweighting, accelerated information transfer can lower effective assimilation thresholds, raise regulation barriers, reduce offload efficiency, and increase residual stress. Trauma is one local case of exceeded energy cost; accelerated information transfer is the broader historical mechanism.

This framework integrates cognitive load theory, emotional regulation, and connectome protection into a unified mathematical model with response-family selection, enabling adaptive cognitive load management across diverse information processing domains.
