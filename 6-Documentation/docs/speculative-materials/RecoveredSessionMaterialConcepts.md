# Recovered Session Material Concepts

Status: recovered candidate notes

Source: local recovered session
`5-Applications/audit/exploit-audit/sessions/chat-geometry-rip-organoid-lambda-20260404.jsonl`

Purpose: preserve material-science concepts that appeared in the recovered
session but were not yet promoted into durable Research Stack material docs.

## Recovery Summary

The recovered session contains two material clusters:

1. **2D conductive sheets that become 1D routes**: MXene nanoscrolls, scroll
   radius/thickness ratios, surface chemistry imbalance, ion/redox gating, and
   curvature-controlled transport.
2. **Self-attesting structural materials**: SLS tubules, conductive/ferrite
   doped matrices, magnetoelectric laminates, piezo alerts, magnetic labyrinths,
   and SDR-readable resonant voids.

These should be treated as material analogues and test targets, not as proven
device claims.

## Material Primitives

| Primitive | Neutral interpretation | Stack value | Current status |
|---|---|---|---|
| **MXene Nanoscroll** | 2D conductive sheet curled into a 1D tubular transport surface. | Physical analogy for DynamicCanal curl, 2D-to-1D route formation, and curvature-gated flow. | Recovered from session; needs external prior-art refresh before citation. |
| **MXene Charge-Flow Shaping** | Bias, strain, ion concentration, adsorbate loading, pH, or redox state changes surface transport. | Candidate finite-state material gate for routing charge/flow instead of claiming free morphing. | Recovered test-matrix name; detail mostly absent. |
| **Scroll Radius/Thickness Ratio** | Geometry ratio controlling curl, accessible surface, and path length. | Useful ratio primitive for PHI-style or MassNumber-style geometry checks, if measured. | Candidate; do not assume golden ratio optimum. |
| **SLS Resonant Tubule Lattice** | Additively manufactured hollow tubules that carry compressive load and act as RF cavities/waveguides. | Structural shape doubles as SDR-readable proof-of-state. | Strong recovered concept; needs CAD/test coupon. |
| **Conductive Valence Matrix** | Polymer/SLS body doped with carbon nanotubes or ferrite particles near a percolation threshold. | Strain-to-conductivity trip surface: deformation changes whether a route conducts. | Candidate; percolation threshold must be calibrated. |
| **Magnetic Labyrinth** | Internal geometry routes magnetic flux in a healthy state and reroutes it under damage or misalignment. | Geometry-as-logic gate and passive structural attestation. | Candidate patent-support surface. |
| **Magnetoelectric Laminate Capsule** | Magnetostrictive plus piezoelectric or ME laminate converts magnetic/mechanical change into voltage/acoustic alert. | Passive failure pulse / self-powered warning primitive. | Candidate; material stack must be specified by real parts. |
| **Piezo Alert Layer** | Piezo element turns mechanical or ME pulse into audible/electrical alarm. | Output receipt for structural eFuse. | Practical primitive, low speculation. |
| **Ferrite/Carbon SLS Doping** | Doped print media creates lossy, magnetic, or semi-conductive routes inside a structural body. | Lets material geometry carry both load and signal. | Candidate; needs printability and fatigue receipts. |
| **SDR Resonant Void Readout** | Tubule or cavity geometry produces a repeatable RF echo under SDR sweep. | Non-contact hash/proof surface for mechanical state. | Candidate; first test can be cheap. |

## Structural eFuse Model

The self-attesting semi-jack direction collapses to a finite passive gate:

```text
healthy_geometry
  -> balanced_flux
  -> no piezo pulse
```

```text
overload_or_misalignment
  -> tubule buckling or labyrinth shift
  -> flux imbalance / conductivity jump
  -> ME or piezo pulse
  -> alert receipt
```

Define:

```text
StructuralFuseState =
  load_path
  + resonant_void_signature
  + flux_balance
  + percolation_margin
  + piezo_receipt
```

Trip condition:

```text
trip iff
  buckling_margin <= buckling_floor
  or abs(flux_delta) >= flux_delta_floor
  or conductivity_ratio >= conductivity_trip_ratio
```

The useful point is not "smart material magic." It is a geometry-and-material
threshold that changes a measurable signal when the structure enters an unsafe
state.

## Scroll / Canal Model

The MXene-scroll thread is useful because it gives a grounded physical pattern:

```text
flat sheet
  -> surface chemistry / strain imbalance
  -> curl
  -> tube / channel
  -> changed transport
```

Research Stack analogue:

```text
flat route field
  -> stress / mismatch / pressure imbalance
  -> DynamicCanal curl
  -> throat / channel
  -> changed route capacity
```

Candidate score:

```text
ScrollRouteScore =
  surface_access
  * conductivity_or_flow
  * curvature_stability
  / (1 + transport_resistance + heat + hysteresis)
```

Promotion requires a measured or simulated receipt for at least one term. A
pretty scroll analogy alone does not promote.

## Percolation Gate

Conductive or ferrite doping pays rent if it gives a measurable threshold:

```text
PercolationMargin =
  abs(strain - strain_trip)
  / (1 + temperature_noise + print_variance + fatigue)
```

```text
conductive_route_ok iff
  PercolationMargin <= margin_window
  and heat <= heat_ceiling
  and repeatability >= repeatability_floor
```

This is directly applicable to:

- Waveprobe: route selection under thresholded local state.
- COUCH: hysteretic forcing surface.
- FAMM: failed trip or false trip becomes a scar.
- FPGA/GPU verification: GPU proposes a material-state classifier; FPGA checks
  the finite threshold receipt.

## SDR Void Hash

For tubule lattices and magnetic labyrinths, the readout can be an RF signature:

```text
VoidHash =
  hash(
    resonant_peaks,
    peak_widths,
    echo_delay,
    attenuation,
    temperature
  )
```

Healthy state:

```text
distance(VoidHash_live, VoidHash_baseline) <= tolerance
```

Failure state:

```text
distance(VoidHash_live, VoidHash_baseline) > tolerance
```

This gives the material a reason to exist inside the stack: the same geometry
that bears load also becomes a verification surface.

## Cross-Application Targets

| Target | Application |
|---|---|
| DynamicCanal | Curl, throat, rupture, and capacity can borrow the scroll model. |
| Waveprobe/QUBO | Select tubule, tile, or material states under adhesion/release/heat/fatigue constraints. |
| COUCH | Percolation and magnetic-labyrinth trip points are hysteretic forcing surfaces. |
| Charged-Mass Braid Sieve | Contact, flux, or conductivity routes accumulate admissible gain and residual scar. |
| Morphic DSP | Physical cells change local mode while the controller preserves receipts. |
| FPGA verification | Finite thresholds and hashes are small enough for hardware Warden checks. |
| Patent/CAD work | Tubule load paths, magnetic null, and SDR readout are claim-support surfaces. |

## Failure Modes

| Risk | Why it matters | Receipt needed |
|---|---|---|
| false trip | Alarm fires under safe load. | Load/temperature sweep. |
| missed trip | Structure fails but signal does not cross threshold. | Destructive coupon test. |
| fatigue drift | Baseline changes over cycles. | Cycle-count signature drift. |
| print variance | SLS doping/tubules vary across builds. | Batch calibration. |
| heat | Conductive paths or eddy currents overheat. | Thermal ceiling. |
| contamination | Tubules or contact surfaces foul. | Environmental test. |
| over-analogy | Math docs overclaim material behavior. | Explicit status/gate labels. |

## What Not To Claim

Do not claim:

- MXene or graphene scrolls are already validated as robot skin.
- Ferrite/carbon SLS doping automatically gives reliable logic.
- A magnetic labyrinth is a topological insulator in the rigorous condensed
  matter sense unless independently proven.
- SDR echoes are cryptographic proof by themselves.
- The material changes state with no energy, heat, hysteresis, or fatigue.

Allowed claim:

```text
microstructured and doped materials can provide finite, measurable transition
surfaces where geometry, strain, conductivity, flux, and RF response become
jointly inspectable routing or safety signals
```

## First Cheap Tests

1. Simulate tubule resonance across a small set of diameters and lengths.
2. Print or model a simple tubule coupon and estimate buckling margin.
3. Build a JSONL `material_state` schema for load, RF signature, flux, and
   conductivity.
4. Run a Waveprobe-style classifier over healthy vs damaged synthetic states.
5. Add a MassNumber receipt for each proposed material transition.
