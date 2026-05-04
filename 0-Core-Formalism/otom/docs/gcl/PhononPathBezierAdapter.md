# Phonon Path Bezier Adapter

Status: HOLD / adapter specification
Authority: external-source anchored design pattern; not physical proof
Related:

- `docs/gcl/GCLCombinedCodingSurface.md`
- `docs/gcl/GeometricCompressionWorkspace.md`
- `data/cff/provenance-database.yml`
- `https://github.com/allaunthefox/bezier-kit`

## Purpose

The Phonon Path Bezier Adapter defines a GCL-compatible workspace for using Bezier geometry as low-dimensional candidate routes for phonon, shock, thermal, pressure-wave, optical, chemical-gradient, framework-nucleic-acid, or multimodal energy/signal transport through a simulated medium.

The goal is not to draw curves. The goal is to discover whether controllable geometry can reveal stable path families through medium-specific damping, scattering, reflection, strain, impedance, local potential gradients, post-processing stability constraints, and valency-controlled signal placement.

```text
Bezier curve candidate
  -> medium / material / framework simulator
  -> energy or signal response field
  -> attenuation / scattering / residence-time / valency audit
  -> stabilization or lock-in challenge
  -> Delta-Phi-Gamma-Lambda receipt
  -> Warden status
```

## Core doctrine

```text
The curve proposes.
The medium disposes.
The lock-in step proves whether the path survives processing.
The valency layer proves whether the signal count and placement are controlled.
Warden receipts what survives.
```

A Bezier path is a control hypothesis, not a physical transport proof. A path claim is promoted only if the simulator reports declared material parameters, boundary conditions, bounded attenuation, stable arrival or shielding function, baseline comparison, repeatable receipts, stabilization/failure condition, and—where biomolecular scaffolds are used—a valency receipt.

## External source tetrad

This adapter is now anchored by four external source surfaces. Each source has a CFF-style provenance record in `data/cff/provenance-database.yml`.

| Source | CFF provenance id | Imported role | Authority boundary |
|---|---|---|---|
| Flandy et al., Advanced Materials 2026, complementary nanotubes-polymer shielding | `flandy-2026-complementary-nanotubes-polymer-multimodal-shielding` | geometry-programmable multimodal attenuation | external precedent for geometry-dependent shielding, not proof of phonon routing |
| Sur et al., RSC Advances 2025, UV-induced PDA crosslinking | `sur-2025-uv-induced-polydiacetylene-crosslinking-solvent-resistance` | crosslink lock-in and multilayer stability | external precedent for preserving morphology under sequential processing, not proof of GCL |
| Kim, Ji, Choi, and Nam, Advanced Materials 2026, plasmonic nanomachines | `kim-2026-plasmonic-nanomachines-local-potential-gradients` | local potential gradients and optically addressable motion | external precedent for optical/thermal/chemical gradient-driven nanoscale actuation, not proof of Bezier transport |
| Liu et al., Angewandte Chemie International Edition 2018, valency-controlled framework nucleic acid signal amplifiers | `liu-2018-valency-controlled-framework-nucleic-acid-signal-amplifiers` | scaffold valency, placement-controlled amplification, and staircase signal response | external precedent for programmable biomolecular signal geometry, not proof of GCL compression |

Together, they produce the combined adapter doctrine:

```text
1. Geometry changes energy response.
2. Crosslinking can lock a morphology through processing.
3. Local potential gradients can turn energy localization into motion.
4. Framework valency can control how many signal units are recruited to a scaffold.

Therefore:
  find the path,
  test the path through a medium,
  lock the path,
  place the signal units with declared valency,
  then ask whether localized gradients can actuate or probe it.
```

## Source 1: geometry-programmable multimodal attenuation

```text
Flandy, Kun Kim, Jaehyoung Ko, Daeun Kim, Daekwon Lee, Heesuk Rho,
Sang Seok Lee, Dong Su Lee, Se Gyu Jang, Seokhoon Ahn, Seung-Yeol Jeon,
Dae-Young Jeon, and Yongho Joo.
"Ultrathin, Stretchable, and 3D-Printable Complementary Nanotubes-Polymer
Composites for Multimodal Radiation Shielding in Extreme Environments."
Advanced Materials 38:e13805, 2026.
DOI: 10.1002/adma.202513805
CFF id: flandy-2026-complementary-nanotubes-polymer-multimodal-shielding
```

Imported lesson:

```text
material composition
  + nanotube interface geometry
  + printable macro-architecture
  -> changed energy residence, scattering, attenuation, and survivability
```

## Source 2: crosslink lock-in and multilayer stability

```text
Amit K. Sur, Audithya Nyayachavadi, Piumi Kulatunga, Nien-Jung Li,
Yu-Cheng Chiu, and Simon Rondeau-Gagné.
"Engineering solvent resistance in semiconducting polymer films through
UV-induced polydiacetylene crosslinking."
RSC Advances 15, 24142-24149, 2025.
DOI: 10.1039/D5RA02367J
CFF id: sur-2025-uv-induced-polydiacetylene-crosslinking-solvent-resistance
```

Imported lesson:

```text
dynamic polymer film
  + UV-induced topochemical PDA crosslinking
  + preserved morphology
  + increased mechanical robustness
  -> solvent-resistant multilayer-compatible state
```

## Source 3: local potential gradients and nanoscale motion

```text
Yoonhee Kim, Soohyun Ji, Donghyun Choi, and Jwa-Min Nam.
"Plasmonic Nanomachines: Creating Local Potential Gradients and Motions."
Advanced Materials e73247, 2026.
DOI: 10.1002/adma.73247
CFF id: kim-2026-plasmonic-nanomachines-local-potential-gradients
```

Imported lesson:

```text
light-addressable plasmonic material
  + optical / thermal / chemical local potential gradient
  + geometric or energetic asymmetry
  -> rectilinear, rotational, or twisting nanoscale motion
```

## Source 4: framework nucleic acid valency and signal amplification

```text
Qi Liu, Zhilei Ge, Xiuhai Mao, Guobao Zhou, Xiaolei Zuo, Juwen Shen,
Jiye Shi, Jiang Li, Lihua Wang, Xiaoqing Chen, and Chunhai Fan.
"Valency-Controlled Framework Nucleic Acid Signal Amplifiers."
Angewandte Chemie International Edition 57(24):7131-7135, 2018.
DOI: 10.1002/anie.201802701
CFF id: liu-2018-valency-controlled-framework-nucleic-acid-signal-amplifiers
```

Use of this paper in GCL is conservative:

```text
Allowed:
  framework nucleic acids as an external source precedent for controlled valency
  tetrahedral DNA / FNA scaffolds as an analogy for placement-controlled signal units
  staircase-like amplification as an audit pattern for discrete signal-count response

Blocked:
  claiming GCL is literal biology
  claiming FNA signal amplification proves geometric compression
  treating biomolecular scaffold performance as proof of Bezier path transport
```

Imported lesson:

```text
framework nucleic acid scaffold
  + fixed number of addressable binding sites
  + purified aggregation-free building blocks
  + valency-controlled signal molecules
  -> monotonic / staircase-like signal amplification
```

GCL translation:

```text
candidate path or scaffold
  -> declared address sites
  -> controlled valency assignment
  -> signal-unit recruitment
  -> amplification audit
  -> Warden receipt
```

## Combined physical lesson imported into GCL

```text
geometry-programmed medium
  + crosslinkable / stabilizable morphology
  + local potential-gradient actuator
  + valency-controlled signal placement
  -> testable path family for energy response, motion, and amplification
```

This is a source-anchored design hypothesis, not a proof.

## GCL translation

```text
Bezier-kit:
  proposes low-dimensional candidate paths, lattices, seams, and spline skeletons

Fluid / material simulator:
  attacks those candidates with pressure, shock, temperature, flow, damping,
  scattering, impedance, stochasticity, and boundary conditions

Lock-in layer:
  tests whether the candidate morphology survives processing, solvent challenge,
  multilayer deposition, strain, or other post-processing perturbation

Potential-gradient layer:
  tests whether optical, thermal, or chemical local gradients can actuate,
  steer, probe, or destabilize the stabilized candidate

Valency layer:
  tests whether addressable sites, signal units, and amplification count remain
  discrete, controlled, and auditable rather than smeared into an unbounded field

Phonon-path layer:
  estimates travel, delay, attenuation, reflection, leakage, residence time,
  mode conversion, and Brownian/stochastic failure where applicable

Warden:
  records whether the candidate path is stable, useful, failed, overclaimed,
  uncontrolled, or merely pretty
```

## Adapter contract

```ts
type PhononPathBezierAdapter = {
  adapter_id: string;
  claim_state: "HOLD" | "CANDIDATE" | "BLOCK" | "REVIEWED";

  source_geometry: {
    control_points_q0_64: string[];
    bezier_degree: number;
    curve_family: "quadratic" | "cubic" | "piecewise" | "rational" | "lattice" | "framework_scaffold";
    projection_receipt: string;
  };

  medium_profile: {
    material_name: string;
    density?: string;
    stiffness?: string;
    viscosity?: string;
    damping?: string;
    conductivity?: string;
    thermal_diffusivity?: string;
    impedance_model?: string;
    scattering_model?: string;
    source_receipts: string[];
  };

  boundary_conditions: {
    domain: string;
    source_event: string;
    target_region: string;
    frequency_band?: string;
    thermal_gradient?: string;
    strain_state?: string;
    radiation_or_wave_load?: string;
    solvent_challenge?: string;
    optical_thermal_or_chemical_gradient?: string;
    target_analyte_or_signal?: string;
  };

  stabilization_profile: {
    lock_in_operator?: string;
    morphology_preserved: boolean;
    multilayer_safe?: boolean;
    solvent_resistant?: boolean;
    post_processing_residue: string[];
    source_receipts: string[];
  };

  potential_gradient_profile: {
    gradient_type?: "optical" | "thermal" | "chemical" | "mixed";
    asymmetry_source?: "material" | "geometry" | "energy" | "environment" | "mixed";
    expected_motion?: "rectilinear" | "rotational" | "twisting" | "none" | "unknown";
    stochasticity_model?: string;
    source_receipts: string[];
  };

  valency_profile: {
    scaffold_type?: "mono_TDN" | "di_TDN" | "tri_TDN" | "framework" | "none" | "unknown";
    declared_binding_sites?: number;
    observed_signal_units?: number;
    valency_staircase_observed?: boolean;
    purification_receipt?: string;
    aggregation_check?: string;
    source_receipts: string[];
  };

  simulated_response: {
    travel_time?: string;
    attenuation?: string;
    reflection_hotspots: string[];
    scattering_residue: string[];
    energy_residence_time?: string;
    mode_conversion_score?: string;
    signal_amplification_ratio?: string;
    stable_arrival: boolean;
    baseline_comparison: string;
  };

  delta_phi_gamma_lambda_audit: {
    delta: string;
    phi: string;
    gamma: string;
    lambda: string;
    audit_passed: boolean;
  };

  warden_receipt: {
    status: "HOLD" | "CANDIDATE" | "BLOCK" | "REVIEWED";
    notes: string[];
    blocked_usages: string[];
  };
};
```

## Delta-Phi-Gamma-Lambda mapping

```text
Delta:
  lost energy, path deviation, scattering residue, leakage, failed arrival,
  morphology drift, solvent damage, unstable gradient response, Brownian loss,
  uncontrolled valency, aggregation, signal-count error, unbounded local heating,
  or unreceipted mode conversion

Phi:
  preserved transport invariant: coherent route, target arrival, bounded
  attenuation, retained shielding function, stable geometry-response relation,
  morphology preservation, retained actuation/probe response, or controlled
  discrete signal valency

Gamma:
  forcing pressure: wave amplitude, shock intensity, thermal gradient, strain,
  solvent challenge, UV exposure, optical forcing, chemical gradient,
  target/analyte concentration, enzymatic amplification pressure, Brownian
  stochasticity, or simulator load

Lambda:
  scale band: molecular crosslink, oligonucleotide sequence, TDN vertex,
  framework nucleic acid scaffold, polymer chain, nanotube interface, printed
  filament, honeycomb cell, nanomachine body, device layer, full shield,
  or rendered inspection surface
```

Operational question:

```text
At scale lambda, under forcing gamma, which Bezier-guided or scaffold-guided
geometry preserves phi while minimizing delta through the declared medium,
lock-in protocol, and valency program?
```

## Geometry families to test

```text
1. straight control path
2. quadratic Bezier path
3. cubic Bezier path
4. piecewise spline path
5. honeycomb cell skeleton
6. gyroid-inspired projected skeleton
7. rectilinear grid skeleton
8. random / unstructured baseline
9. asymmetric Janus-like path family
10. rotational/twisting path family
11. mono-TDN / di-TDN / tri-TDN scaffold family
12. valency-controlled signal staircase family
```

Each family must be tested against the same medium, source event, and declared scale band before any geometry benefit is claimed.

## Simulator outputs required

```text
travel_time
attenuation_ratio
reflection_hotspots
scattering_residue
energy_residence_time
boundary_failure_points
mode_conversion_score
morphology_preservation_score
post_processing_residue
potential_gradient_response
valency_count_error
signal_amplification_ratio
aggregation_or_purity_check
baseline_comparison
repeatability_seed
Warden receipt
```

## Warden rules

```text
if path is rendered but no simulator response exists:
  emit UnderversePacket.projection_proof_confusion
  block promotion
```

```text
if material parameters are omitted:
  mark HOLD
  require MaterialProfileReceipt
```

```text
if boundary conditions are omitted:
  mark HOLD
  require BoundaryConditionReceipt
```

```text
if lock-in or post-processing stability is claimed without a stabilization receipt:
  mark HOLD
  require StabilizationReceipt
```

```text
if local potential-gradient actuation is claimed without declaring optical,
thermal, chemical, or mixed gradient type:
  emit UnderversePacket.gradient_type_missing
  block promotion
```

```text
if nanoscale directed motion is claimed and Brownian/stochastic dynamics are not
considered at the declared lambda scale:
  emit UnderversePacket.nanoscale_stochasticity_ignored
  block promotion
```

```text
if valency-controlled amplification is claimed without declared binding sites,
purification/aggregation check, and observed signal-unit count:
  emit UnderversePacket.valency_receipt_missing
  block promotion
```

```text
if biological scaffold language is used as literal proof of GCL:
  emit UnderversePacket.biological_overclaim
  downgrade to analogy-bounded external reference surface
```

```text
if Bezier path beats no baseline:
  mark HOLD
  require BaselineComparisonReceipt
```

```text
if geometry effect is claimed without scale band lambda:
  emit UnderversePacket.lambda_missing
  block promotion
```

```text
if phonon, EMI, neutron, thermal, optical, chemical-gradient, biomolecular,
electrochemical, and pressure-wave behavior are collapsed into one carrier
without declared mode-conversion rules:
  emit UnderversePacket.mode_confusion
  block promotion
```

## Phonon-specific boundary

The external source tetrad does not directly prove phonon routing.

```text
Nanotube shielding source:
  external precedent for geometry-dependent multimodal energy response

Crosslinking source:
  external precedent for morphology lock-in and multilayer survivability

Plasmonic nanomachine source:
  external precedent for local potential gradients producing nanoscale force and motion

FNA signal-amplifier source:
  external precedent for controlled scaffold valency and discrete signal amplification

Phonon path claim:
  separate hypothesis requiring material dynamics, acoustic/thermal model,
  boundary conditions, validation receipt, and baseline comparison
```

## First implementation target

```text
PhononPathBezierAdapter v0:
  input Bezier control points from bezier-kit
  sample candidate curve into Q0_64-coded points
  embed points into a fluid/material/framework grid
  run simple attenuation + scattering proxy
  run a lock-in / perturbation survival proxy
  run an optional local-potential-gradient probe proxy
  run an optional valency/signal-count audit proxy
  compare against straight-path, random-path, and uncontrolled-valency baselines
  emit Delta-Phi-Gamma-Lambda audit and Warden receipt
```

## Compact doctrine

```text
A path is not a curve.
A path is a curve surviving a medium.
A useful path is a surviving curve that can be stabilized, addressed, and probed.
```
