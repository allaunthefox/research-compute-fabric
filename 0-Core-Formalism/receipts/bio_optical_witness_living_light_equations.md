# Bio-Optical Witness: Living-Light Material Equations

Status: `DRAFT_RECEIPT_PROTOCOL`

Claim boundary: this file extracts quantitative relations and stack-level equations from the public CU Boulder / Science Advances report on chemically sustained bioluminescence in living-light materials. It is not a wet-lab protocol, culture protocol, or claim that biological light is free energy. It treats living bioluminescent material as a slow optical witness surface: chemical/material state in, optical receipt out.

Primary source spine:

- CU Boulder Today, "Light without electricity? Glowing algae could make it possible" (2026-05-06).
- EurekAlert release for the peer-reviewed Science Advances article, DOI `10.1126/sciadv.aee3907`.
- Preprint/public abstract record for "Chemical Stimulation Sustains Bioluminescence of Living Light Materials", DOI `10.1101/2025.07.16.664986`.
- IUPAC Gold Book definition of pH.

## Extracted Source Facts

```text
organism: Pyrocystis lunula
material: 3D-printed ionically crosslinked alginate / naturally derived hydrogel scaffold
trigger_acidic: pH = 4
trigger_basic: pH = 10
acidic_response: bright, localized, persistent emission up to 25 minutes
basic_response: diffuse, shorter-lived / biphasic stress-like emission
longitudinal_retention: ~75% brightness after 4 weeks under acidic triggering
application frame: living sensors, soft robotics, dark-environment autonomous systems, environmental monitoring
```

## 1. pH Gate

Use the IUPAC activity definition as the canonical chemical input gate:

```text
pH = -log10(a_H+)
```

where `a_H+` is hydrogen-ion activity.

For dilute/engineering approximations:

```text
[H+] ≈ 10^(-pH)
```

The reported acidic and basic triggers become:

```text
[H+]_acid ≈ 10^-4
[H+]_base ≈ 10^-10
[H+]_acid / [H+]_base ≈ 10^6
```

Receipt interpretation:

```text
pH 4 and pH 10 are not symmetric perturbations.
They differ by approximately six orders of magnitude in hydrogen-ion activity.
```

## 2. Chemical-Light Response Gate

Define a categorical pH response gate for living-light material:

```text
G_pH(pH) =
  ACID_EMIT      if pH ≈ 4
  BASE_STRESS    if pH ≈ 10
  HOLD_UNKNOWN   otherwise
```

Stack interpretation:

```text
ACID_EMIT    -> ADMIT optical witness, localized persistent glow
BASE_STRESS  -> HOLD/FAMM, diffuse or stress-like glow signature
HOLD_UNKNOWN -> require calibration receipt before classification
```

## 3. Bio-Optical Witness Signal

Let:

```text
L(x, t) = emitted optical intensity at surface coordinate x and time t
C(x, t) = chemical trigger field, e.g. pH/stimulus concentration
M(x, t) = material viability / living-cell reactivity field
S(x, t) = mechanical stimulation field
```

Then a stack-level witness equation is:

```text
L(x,t) = M(x,t) · B( C(x,t), S(x,t), t ) + ε_opt(x,t)
```

where:

```text
B = bioluminescent response kernel
ε_opt = optical noise / camera / scattering residual
```

For the chemistry-only gate:

```text
L_chem(x,t) = M(x,t) · B_pH(pH(x,t), t) + ε_opt(x,t)
```

## 4. Persistence Window

The acidic response is reported as persistent up to 25 minutes. Treat this as a bounded emission horizon:

```text
T_acid ≤ 25 min
```

A minimal decay model for local optical witness intensity:

```text
L_acid(t) = L0 · exp(-t / τ_acid) · 1[0 ≤ t ≤ T_acid]
```

with receipt constraint:

```text
T_acid_observed ≤ 25 min
```

Do not assign `τ_acid` from the article alone; it must be fitted from time-series intensity data.

## 5. Longitudinal Brightness Retention

The public report states that acid-triggered 3D-printed living-light structures retained about 75% brightness after four weeks.

```text
R_B(4 weeks) = L_week4 / L_initial ≈ 0.75
```

A conservative viability/brightness decay model:

```text
R_B(t) = exp(-k_B t)
```

Solving from the reported four-week retention:

```text
k_B ≈ -ln(0.75) / 4 weeks
k_B ≈ 0.0719 week^-1
```

Half-brightness extrapolation under the same simple model:

```text
t_1/2 = ln(2) / k_B ≈ 9.64 weeks
```

Claim boundary: this half-life is a model extrapolation, not a source claim.

## 6. Integrated Optical Receipt

For camera-readable witness telemetry, the useful value is often total emitted light over a bounded read window:

```text
I_emit(x; T) = ∫_0^T L(x,t) dt
```

For a full witness tile region `Ω_tile`:

```text
I_tile(T) = ∫_{Ω_tile} ∫_0^T L(x,t) dt dx
```

For digital receipt extraction:

```text
packet = DecodeCamera( L_frame(x,t), calibration, threshold )
```

## 7. Synergy Gate: Chemical + Mechanical Stimulation

The public abstract reports that coupling chemical and mechanical stimulation yields synergistic enhancement of amplitude and duration.

Define:

```text
L_chem = response to chemical stimulus alone
L_mech = response to mechanical stimulus alone
L_combo = response to combined chemical + mechanical stimulus
```

Synergy witness:

```text
Σ_syn = L_combo - (L_chem + L_mech)
```

or for integrated light:

```text
Σ_syn(T) = I_combo(T) - [ I_chem(T) + I_mech(T) ]
```

Classification:

```text
Σ_syn > 0  -> synergistic enhancement
Σ_syn = 0  -> additive response
Σ_syn < 0  -> antagonistic / stress / inhibition response
```

Do not assign numeric synergy without source time-series or amplitude data.

## 8. Living-Light Receipt Surface

Canonical receipt transform:

```text
chemical/material event
  -> living-light emission
  -> camera observation
  -> optical packet
  -> Sniffer classification
  -> BVMR gate
  -> CMR receipt
  -> FAMM if abnormal / scarred
  -> Underverse if excluded, failed, unpaid, or residual
  -> Warden replay check
```

Minimum event vector:

```json
{
  "protocol": "bio_optical_witness_tile_v0",
  "source": "chemical_stimulation_sustains_bioluminescence_living_light_materials",
  "organism": "Pyrocystis_lunula",
  "substrate": "3D_printed_alginate_hydrogel",
  "stimulus": {
    "pH": "assigned_or_measured",
    "mechanical_stimulation": "present_or_absent"
  },
  "observed": {
    "emission_pattern": "localized | diffuse | biphasic | none",
    "emission_duration": "measured_seconds",
    "integrated_intensity": "I_tile(T)",
    "brightness_retention": "optional_longitudinal_R_B"
  },
  "decision": "ADMIT | HOLD | FAMM | QUARANTINE",
  "claim_boundary": "slow_living_sensor_not_general_lighting"
}
```

## 9. No-Free-Light Accounting

Biological light is not free energy. The electrical bill may be reduced at the emitting surface, but the payment moves into metabolic, photosynthetic, chemical, material-maintenance, and readout costs.

```text
E_total = E_photo_input + E_metabolic + E_chemical_trigger + E_material_maintenance + E_camera_readout + E_decode
```

For stack accounting:

```text
optical_output <= paid_biochemical_energy + stored_material_state - losses
```

Receipt rule:

```text
No emitted-light claim without energy/payment lane.
No optical packet without calibration/residual lane.
No living material claim without viability/retention lane.
```

## 10. Stack Integration

Name:

```text
Bio-Optical Witness Material
Living-Light Receipt Surface
```

Keeper phrase:

```text
This is not free light; it is biology paying the optical bill.
Chemical state enters, living material emits, camera reads, receipts classify.
```

Connection to existing semiautonomous stack:

```text
Bio-optical tile = slow optical witness surface
Equation Sniffers = classify optical/chemical scent trail
BVMR = gate event vector
AVMR = combine surviving witness vectors
CMR = receipt combined optical event
FAMM = inspect abnormal scars
Underverse = account excluded or failed material/light response
Warden = replay/calibration check
```
