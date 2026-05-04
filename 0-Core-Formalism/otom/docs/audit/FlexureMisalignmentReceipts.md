# Flexure Misalignment Receipt Checklist

## Purpose

A flexure implies a deliberately misaligned local point: a controlled compliance defect inserted into a stiffer geometry. That defect may be useful because it localizes bending, creates anisotropic tension, and routes snap-through energy into a measurable dissipation path.

This note turns that idea into a receipt checklist for engineering validation.

## Core Statement

```text
flexure -> controlled misaligned point -> anisotropic local stress -> biased snap path -> measurable energy drainage
```

In the broader audit stack:

```text
misaligned point       -> transfer index
flexure                -> compliant gate
unbalanced tension     -> anisotropic stress witness
snap-through           -> shock/alignment transition
hysteresis/damping     -> energy drainage witness
FEA/prototype evidence -> engineering proof receipts
```

## Required Receipts

### 1. GeometryReceipt

The geometry must explicitly define the flexure and the misaligned point.

Minimum fields:

```text
transfer_index
nominal_axis
actual_axis
misalignment
hinge_thickness
hinge_length
slot_depth or beam_length if applicable
fillet_radius if applicable
```

Pass condition:

```text
misalignment > 0
hinge_thickness > 0
hinge_length > 0
```

### 2. MaterialModelReceipt

The material model must define enough parameters to evaluate stress and fatigue.

Minimum fields:

```text
elastic_modulus
yield_strength
fatigue_limit
damping_coefficient
poisson_ratio
material_name
```

Pass condition:

```text
all major material parameters are present and physically positive
```

### 3. FEASimulationReceipt

Simulation must show that the flexure creates a controlled imbalance without exceeding safety constraints.

Minimum outputs:

```text
max_von_mises_stress
stress_margin
displacement_delta
reaction_force_delta
tension_imbalance
strain_energy
mesh_refinement_near_flexure
solver_type
boundary_conditions
```

Pass condition:

```text
stress_margin > 0
tension_imbalance > 0
mesh and boundary conditions documented
```

### 4. PrototypeMeasurementReceipt

A physical prototype should confirm that the simulated flexure behavior appears in the real mechanism.

Minimum measurements:

```text
measured_strain
measured_deflection
measured_force_delta
measured_snap_load
measured_recovery
instrumentation_method
```

Pass condition:

```text
measured strain, deflection, and force difference are nonzero and match simulation within tolerance
```

### 5. EnergyDissipationReceipt

Energy drainage must be measured, not assumed.

Minimum measurements:

```text
force_displacement_curve
loading_work
unloading_work
hysteresis_area
damping_loss
snap_event_energy_drop
```

Pass condition:

```text
hysteresis_area > 0
or measured damping / snap energy drop is positive
```

### 6. FatigueSafetyReceipt

The flexure must survive the expected number of snap cycles.

Minimum fields:

```text
tested_cycles
safe_cycles
crack_detection_method
post_test_geometry_check
maximum_strain_per_cycle
```

Pass condition:

```text
tested_cycles <= safe_cycles
no unacceptable crack growth or plastic drift
```

## Audit Gate

```text
Receipt: FlexureMisalignmentReceipts
Gate: U_scope until all six receipts are supplied
```

Promotion condition:

```text
GeometryReceipt
+ MaterialModelReceipt
+ FEASimulationReceipt
+ PrototypeMeasurementReceipt
+ EnergyDissipationReceipt
+ FatigueSafetyReceipt
=> Engineering V_scope
```

## Important Boundary

This flexure receipt stack validates an engineering mechanism only. It does not prove the Sidon theorem, the compact density target, or the Burgers-Ruzsa arithmetic lock.

Correct dependency chain:

```text
FlexureMisalignmentReceipts
  -> validates mechanical snap/dissipation plausibility
ShockBurgersCoupling
  -> validates transport/alignment model
BurgersRuzsaDecoupling
  -> separates selector from arithmetic lock
NonseparableEncodingReceipt
  -> required for global Sidon pair-sum injectivity
CompactDensityReceipt
  -> required for sigma = 1
```
