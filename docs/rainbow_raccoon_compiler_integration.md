# Rainbow Raccoon Compiler Integration

Date: 2026-05-08

Status: integration shim, not a formal Lean proof.

Runner:

```text
4-Infrastructure/shim/rainbow_raccoon_compiler.py
```

Receipt:

```text
4-Infrastructure/shim/rainbow_raccoon_compiler_receipt.json
```

Curriculum:

```text
4-Infrastructure/shim/rainbow_raccoon_compiler_curriculum.jsonl
```

Receipt hash:

```text
5edf7a533f7994233f075e171a984760525301e0f66040c8ac882d1172928f2a
```

## Primary Read

The Rainbow Raccoon Compiler is now represented as a small manifold-indexed
type-checker boundary for the current stack:

```text
object
-> manifold projection
-> nearest lawful shape
-> type witness
-> field equation
-> invariant receipt
```

This first pass is intentionally conservative.  It emits `CANDIDATE` only when
the object has enough declared projection, witness, and scale evidence to be
admissible for a next-stage proof.  It emits `HOLD` when the object is
underspecified or has weak receipt axes.

## Manifold Axes

The shim projects each object into a 16-axis vector:

```text
semantic_entropy
geometric_mass
compression_pressure
topology_torsion
receipt_density
field_energy
hardware_affinity
proof_readiness
residual_risk
shape_closure
history_depth
negative_control_strength
projection_declared
decoder_declared
witness_declared
scale_band_declared
```

These axes are not proof terms yet.  They are a routing surface for deciding
which proof, receipt, or hold policy should apply next.

## Lawful Shape Prototypes

The initial lawful-shape set is:

```text
SignalShapedRouteCompiler
ProjectableGeometryTopology
CognitiveLoadField
CadForceProbeReceipt
LogogramProjection
HoldForUnlawfulOrUnderspecifiedShape
```

Each shape has a prototype vector and a field equation.  The compiler compares
the projected object to these prototypes and records the nearest shape plus the
distance.

## Current Compile Results

```text
rrc_obj_signal_route_compiler
  label: Compression Signal Shaping Synthesis
  shape: SignalShapedRouteCompiler
  distance: 0.070321
  status: HOLD
  reason: scale_band_declared is weak

rrc_obj_projectable_geometry
  label: Projectable Geometry Topology Receipt
  shape: ProjectableGeometryTopology
  distance: 0.107275
  status: CANDIDATE

rrc_obj_cognitive_load
  label: Connectome Protective Cognitive Load Receipt
  shape: CognitiveLoadField
  distance: 0.103050
  status: CANDIDATE

rrc_obj_cad_force_probe
  label: CAD Force Probe Experiment Matrix Receipt
  shape: CadForceProbeReceipt
  distance: 0.167641
  status: HOLD
  reason: scale_band_declared is weak

rrc_obj_underspecified
  label: Underspecified raw object negative control
  shape: HoldForUnlawfulOrUnderspecifiedShape
  distance: 0.240924
  status: HOLD
  reason: projection, witness, and scale are weak
```

The current pass uses both manifold-feature distance and a declared-kind prior.
That keeps geometry receipts in geometry type-space even when their text also
contains route/cost language.

## Field Equations

Signal-shaped route compiler:

```text
r* = argmin_r LB(r | phi_signal(c), semantic_regime(c), history_state)
promote iff exact decode hash closes and total bytes beat incumbent
```

Projectable geometry topology:

```text
close iff mass_delta_q == 0 and horizon_hash matches and nan0_flag == 0
```

Cognitive load field:

```text
L_total = C_domain * response_family(S; theta) * phi_gain * B_gate * overflow_gate
```

CAD force-probe receipt:

```text
sum_j q_ij * (x_i - x_j) + p_i = 0
residual must stay under declared tolerance
```

Hold shape:

```text
HOLD iff projection, decoder, witness, scale, or residual accounting is missing
```

Logogram projection:

```text
logogram_cell -> canonical_hash -> glyph_payload -> projection_lane
admit iff cell hash, payload bound, substitution receipt, and regime guard close
```

## Promotion Rules

```text
CANDIDATE is not a Lean proof; it is only admissible for next-stage proving.
HOLD is emitted when projection, witness, decoder, residual, or scale is weak.
No object may be promoted as lawful without a replayable invariant receipt.
Compression gain must still count residual, witness, decoder, sidecar, and container bytes.
Geometry or force claims require calibrated physical measurement receipts.
```

## Next Integration Steps

```text
1. Add a Lean RRCShape enum and witness-gate theorem surface.
2. Wire RRC classifications into the compression route classifier from E1/E2.
3. Use RRC HOLD status as a fail-closed gate for semantic tokenbook merges.
4. Map CAD force-probe receipts through RRC before four-force geometry claims.
5. Add calibrated scale-band metadata to release CAD and compression holds.
6. Keep [[RRC Logogram Projection Bridge]] as the projection gate for logogram surfaces.
```

## Claim Boundary

RRC is now an executable integration boundary.  It is not yet a verified
compiler.  The current value is that it turns abstract type-shape language into
a receipt-bearing, inspectable pipeline with explicit `CANDIDATE` and `HOLD`
states.
