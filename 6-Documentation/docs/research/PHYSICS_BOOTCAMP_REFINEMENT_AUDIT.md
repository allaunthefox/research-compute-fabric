# Physics Bootcamp Refinement Audit

Status: EXTERNAL_REFERENCE
Date ingested: 2026-05-20
Source: https://www.physicsbootcamp.org/
Primary index surface: https://www.physicsbootcamp.org/fundamentals-bootcamp.html

## Claim Boundary

Physics Bootcamp is used here as a curriculum coverage index, not as an
authority for new physical claims. The stack already has broad physics equation
coverage and several Lean physics surfaces; this audit identifies refinement
gaps where the stack would benefit from explicit receipts, examples, or
coverage tracking.

Do not import prose or implementation from the site. Use the topic map as an
external checklist.

## Local Coverage Snapshot

Existing stack surfaces already cover:

```text
Hamiltonian dimensions and dimensional homogeneity:
  0-Core-Formalism/lean/Semantics/Semantics/HamiltonianFormal.lean

SI constants and unit conversion:
  0-Core-Formalism/lean/Semantics/Semantics/SIConstants.lean
  0-Core-Formalism/lean/Semantics/Semantics/UnitConversion.lean

Mechanics, thermodynamics, E&M, and quantum equation map:
  3-Mathematical-Models/physics_eqs_mapped.md

Physical-semantics boundary:
  6-Documentation/docs/physics/PHYSICAL_SEMANTICS_PARADIGM.md

Electromagnetic and electrostatic Lean surfaces:
  Semantics.ElectromagneticSpectrum
  Semantics.ElectrostaticsMetaprobe
```

## Missing Or Underweighted Refinements

### 1. Measurement Receipt Layer

Bootcamp starts with uncertainty, precision, accuracy, significant figures,
absolute/relative uncertainty, propagation of uncertainty, order of magnitude,
and dimensional analysis.

Current stack has dimensions and units, but measurement quality is scattered
across residual/error terms. Add a first-class measurement receipt:

```text
MeasuredQuantity = value + unit + absoluteUncertainty + relativeUncertainty
MeasurementReceipt = dimensional_ok + sigfig_policy + propagation_rule
```

Suggested future Lean module:

```text
Semantics.MeasurementReceipt
```

This should be Q16_16/Q0_16 based and avoid floats in compute paths.

### 2. Curriculum Coverage Matrix

Bootcamp is useful because it is sequential: mechanics -> fluids/waves ->
thermal physics -> E&M -> optics -> relativity/quantum/atomic/nuclear topics.

The stack has many advanced and speculative surfaces but no simple matrix that
answers:

```text
topic -> local module -> receipt type -> verified examples -> gaps
```

Suggested artifact:

```text
6-Documentation/docs/physics/PHYSICS_COVERAGE_MATRIX.md
```

This should prevent over-investing in high-level physics while missing basic
receipts such as frame transforms, units, and measurement propagation.

### 3. Noninertial Frame Receipts

Bootcamp explicitly separates accelerating frames, rotating frames, Earth-frame
physics, and Coriolis force.

The stack mentions Coriolis in equation maps, but should expose a finite
receipt surface:

```text
InertialFrame
UniformlyAcceleratingFrame
UniformlyRotatingFrame
CoriolisTermReceipt
```

This belongs near rotation, torsion, and shell/PIST frame work. It should be a
coordinate-transform receipt, not a new physics claim.

### 4. Rigid-Body Tensor Receipts

Bootcamp separates fixed-axis rotation, moment of inertia, principal axes,
gyroscope behavior, and kinetic energy about center of mass.

The stack has rotation/quaternion/torsion machinery, but the classical rigid
body interface should have a simple tensor audit:

```text
InertiaTensorReceipt
PrincipalAxesReceipt
ParallelAxisReceipt
RotationalEnergyReceipt
```

This is a good bridge between `UnitQuaternion`, GWL/toroidal shells, and
hardware attitude/control surfaces.

### 5. Thermal Transport Before Thermodynamic Abstractions

Bootcamp separates thermal expansion, calorimetry, conduction, convection,
radiation, Newton cooling, black-body radiation, first law, entropy, and kinetic
theory.

The stack has strong entropy and thermodynamic language, but it should keep
transport receipts separate from global entropy claims:

```text
ThermalConductionReceipt
ConvectionBoundaryReceipt
RadiationBalanceReceipt
CalorimetryBalanceReceipt
MeanFreePathReceipt
```

This matters for hardware, materials, AngrySphinx compute-cost heat budgets, and
any donated-cycle defense work.

### 6. E&M Boundary Receipts

Bootcamp proceeds through charge conservation, Coulomb force, potentials,
conductors as boundaries, method of images, dielectrics, circuits, AC complex
impedance, displacement current, Maxwell equations, and EM waves.

Current stack has EM surfaces, but the boundary-condition receipts should be
made explicit:

```text
ConductorBoundaryReceipt
DielectricResponseReceipt
ImageChargeReceipt
ContinuityEquationReceipt
MaxwellPointFormReceipt
ComplexImpedanceReceipt
```

These are especially useful because they give cheap, checkable examples for
semantic boundary laws.

### 7. Optics As A Routing/Projection Testbed

Bootcamp covers Fermat's principle, Snell/refraction, lenses, optical
instruments, Fresnel equations, polarization, birefringence, interference, and
interferometers.

The stack already has optics references and EM spectra, but optics should be
treated as a clean projection/routing testbed:

```text
FermatPathReceipt
SnellBoundaryReceipt
FresnelPolarizationReceipt
ThinFilmInterferenceReceipt
InterferometerPhaseReceipt
```

This is directly relevant to semantic routing: least-time path selection,
boundary impedance mismatch, phase accounting, and projection loss.

## Priority Order

```text
P0 MeasurementReceipt
P1 PhysicsCoverageMatrix
P2 FrameTransformReceipt
P3 ThermalTransportReceipt
P4 BoundaryConditionReceipt
P5 OpticsRoutingReceipt
```

## Integration Rule

Use Bootcamp as a checklist for missing receipts, not as a new theory source.
Every promoted refinement must land as one of:

```text
Lean theorem
Lean #eval receipt
Q16_16/Q0_16 checker
coverage matrix row with HOLD status
```

The likely highest-value next implementation is `MeasurementReceipt`: it would
connect units, uncertainty propagation, significant figures, and dimensional
analysis into a single gate before physics formulas enter the stack.
