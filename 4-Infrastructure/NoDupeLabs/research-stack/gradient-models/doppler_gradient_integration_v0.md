# Doppler Gradient Integration v0

## Status

```yaml
status: HOLD
source_type: visual_external_reference
source_uri: https://cf.v.redd.it/xv9gi3fv7rxg1/CMAF_1080.m3u8
authority_scope: visual_motif_to_model_requirement
proof_status: not_evidence
route_signature: gradient/doppler-shift/torsion/v0
```

## Core observation

The linked reference should be treated as a geometry cue, not evidence. The usable requirement is:

```text
Gradient models need explicit blue-shift / red-shift dynamics.
```

The visual-math translation is:

```text
descending into a narrowing basin → local frequency increases → blue shift
escaping / relaxing outward → local frequency decreases → red shift
collision / phase boundary crossing → flash event
persistent angular path distortion → torsion accumulation
```

## Why this belongs in the gradient models

Existing Research Stack material already has the right scaffold:

- `SSMS_nD.lean` defines variable-dimension manifolds and selects dimension by potential minimization, so the system already treats dimension choice as an energy descent process.
- `SSMS.lean` includes scalar nodes, Q16.16 hot-path arithmetic, recurrent state, ternary dot products, Betti Swoosh Hamiltonian, and ACI preservation.
- The Ricci-flow/turbulence notes define turbulence as unresolved metric/equivalence stress and identify Ricci flow as a metric-update engine.
- The HyperFabric route defines anisotropic torsional gradient flow, phase fields, locking, and stored torsional stress.
- The pulsar marble-jar route adds multiscale clocks, angular momentum conservation, glitch flashes, Doppler/beaming trace, and accessible phase-volume contraction.

This note connects those routes into one gradient requirement:

```text
Every gradient step should track not only position and energy,
but also local frequency shift relative to the current basin metric.
```

## Minimal equations

### 1. Loss-basin potential

```text
E(x,t) = potential / free energy / routing cost
```

Descent still follows the existing rule:

```text
x_{t+1} = x_t - η ∇E(x_t)
```

But the step is now instrumented by a shift factor.

### 2. Doppler-like shift proxy

For a gradient trajectory with velocity `v_t` along a local view direction `n_t`:

```text
β_t = <v_t, n_t> / c_eff
```

```text
shift_t = sqrt((1 + β_t) / (1 - β_t))
```

Interpretation:

```text
shift_t > 1  → blue-shifted descent / compression / impact approach
shift_t < 1  → red-shifted retreat / relaxation / diffusion away
shift_t ≈ 1  → neutral drift
```

`c_eff` is not physical light speed unless the model is explicitly physical. In Research Stack it is an effective propagation limit or route-speed bound.

### 3. Gravitational-potential approximation

For basin-depth-only models:

```text
Δf / f ≈ -ΔΦ / c_eff^2
```

Where:

```text
Φ = basin potential
ΔΦ < 0 while falling inward → blue shift
ΔΦ > 0 while climbing outward → red shift
```

### 4. Torsion-coupled shift

```text
shift*_t = shift_t · (1 + κ τ_t)
```

Where:

```text
τ_t = torsion proxy / shell mismatch / angular route stress
κ   = torsion coupling weight
```

This keeps the old chandelier/pulsar insight:

```text
narrowing basin raises torsion;
raised torsion sharpens the frequency shift;
frequency shift marks phase-boundary pressure.
```

### 5. Flash / phase boundary detector

A flash event occurs when the model crosses a combined shift/torsion threshold:

```text
flash_t = (shift*_t > θ_blue and τ_t > θ_torsion)
       or (abs(Δphase_t) > θ_phase)
       or (route_changes_basin_t = true)
```

This should be logged as a phase event, not promoted to truth.

## Required trace fields

Every gradient simulation that uses this route should emit:

```text
time
state_id
basin_id
energy
energy_delta
gradient_norm
velocity_norm
torsion_proxy
accessible_phase_volume
beta_eff
doppler_shift
red_blue_label
flash_event
phase_boundary_id
route_weight_before
route_weight_after
```

## Forest-map integration

```text
visual cue
→ geometry requirement
→ Doppler gradient trace
→ torsion/phase flash detector
→ FAMM memory update
→ future routing bias
```

## Authority boundary

```text
TV / video imagery     → intuition only
Doppler equations      → borrowed mathematical structure
model trace            → engineering evidence
Lean theorem           → proof only if assumptions compile
real physical claim    → requires independent data
```

## Outcome

```text
Add Doppler-aware gradient instrumentation.
Do not treat the linked visual as proof.
Keep the route HOLD until code and validator exist.
```
