# Rainbow Raccoon Compiler Integration

Date: 2026-05-08

Status: integration shim with one proof-backed fixed-point lowering lane.

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
3507d55ae2d6e40a76a36b44466fe69a312c16e8110a3f65fdd815f053487759
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

## Proof-Backed Fixed-Point Lowering Lane

The first proof-backed RRC compiler lane is the MetaManifoldProver Q16_16
fixed-point lowering certificate:

```text
0-Core-Formalism/lean/Semantics/Semantics/MetaManifoldProver.lean
2-Search-Space/FAMM/docs/lemma_proof_space_mapping.md
```

This lane lets RRC treat the following lowering rules as proof-bearing compiler
facts rather than heuristic rewrite hints:

```text
weighted_term_bounded:
  (E * alpha) / 65536 <= E

shiftRight_eq_div:
  x >>> 16 = x / 65536

shiftRight_monotone:
  a <= b -> a >>> 16 <= b >>> 16

div_le_div_of_lt:
  x >= 0, a > b, b > 0 -> x / a <= x / b
```

Compiler interpretation:

```text
Q16_16 expression
-> fixed-point lowering certificate
-> shift/division rewrite
-> bounded weighted-term rewrite
-> monotone projection witness
-> invariant receipt
```

Boundary:

```text
The Lean proof closes only the named Q16_16 arithmetic surface.
It does not prove arbitrary RRC projections, geometry claims, compression gains,
or network topology claims.
```

## Canonical Projectable Geometry Representation

For projectable-geometry objects, the RRC route should treat the 16-axis vector
as the signed routing/witness envelope over a lower-dimensional replay chain:

```text
16D signed envelope
  -> 12D source/residual plane
  -> 4D primitive keel
  -> genus-3 residual boat
  -> 0D closure
```

The RRC projection is lawful only when it preserves the replay equations:

```text
source_12D =
  lift(project(source_12D))
  + residual_12D
```

and:

```text
packet_local
+ shear_torsion
+ spectral_field
= residual_12D
```

The shell closure prior is priced in twelfths:

```text
visible_4d = 4/12
shadow_3d  = 3/12
closure_0d = 1/12
lawbound   = 4/12
unresolved = 0/12
```

RRC must emit `HOLD` when the 16D axes are untyped, the residual handles do not
sum to the 12D residual, or the shell leaves unresolved mass debt.  The
reference Lean gate is:

```text
0-Core-Formalism/lean/Semantics/Semantics/ProjectableGeometryCanonical.lean
```

## Lawful Shape Prototypes

The initial lawful-shape set is:

```text
SignalShapedRouteCompiler
ProjectableGeometryTopology
CognitiveLoadField
CadForceProbeReceipt
LogogramProjection
LanguageSetManifoldGraph
FixedPointLoweringCertificate
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
  distance: 0.07146
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
  distance: 0.101187
  status: CANDIDATE

rrc_obj_cad_force_probe
  label: CAD Force Probe Experiment Matrix Receipt
  shape: CadForceProbeReceipt
  distance: 0.165749
  status: HOLD
  reason: scale_band_declared is weak

rrc_obj_underspecified
  label: Underspecified raw object negative control
  shape: HoldForUnlawfulOrUnderspecifiedShape
  distance: 0.240924
  status: HOLD
  reason: projection, witness, and scale are weak

rrc_obj_language_set_ithkuil
  label: Ithkuil Language Set Manifold Graph Typing
  shape: LanguageSetManifoldGraph
  distance: 0.051138
  status: HOLD
  reason: scale_band_declared is weak

rrc_obj_q16_16_lowering_certificate
  label: MetaManifoldProver Q16_16 Fixed-Point Lowering Certificate
  shape: FixedPointLoweringCertificate
  distance: 0.093118
  status: CANDIDATE
  lean_boundary: proved_by_MetaManifoldProver
  reason: no weak required axes
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

Language-set manifold graph:

```text
language_set -> category_inventory -> typed_graph -> surface_views
admit iff graph schema, replay law, residual policy, negative controls, and scale band close
```

Fixed-point lowering certificate:

```text
Q16_16 lowering admits iff shift-right/division, weighted-term bounds,
shift monotonicity, and denominator antitonicity close in Lean
```

## Promotion Rules

```text
CANDIDATE is not a Lean proof; it is only admissible for next-stage proving.
HOLD is emitted when projection, witness, decoder, residual, or scale is weak.
No object may be promoted as lawful without a replayable invariant receipt.
Compression gain must still count residual, witness, decoder, sidecar, and container bytes.
Geometry or force claims require calibrated physical measurement receipts.
Fixed-point lowering claims may cite MetaManifoldProver only for the closed Q16_16 arithmetic lemmas.
```

## Next Integration Steps

```text
1. Add a Lean RRCShape enum and witness-gate theorem surface.
2. Wire RRC classifications into the compression route classifier from E1/E2.
3. Use RRC HOLD status as a fail-closed gate for semantic tokenbook merges.
4. Map CAD force-probe receipts through RRC before four-force geometry claims.
5. Add calibrated scale-band metadata to release CAD and compression holds.
6. Keep [[RRC Logogram Projection Bridge]] as the projection gate for logogram surfaces.
7. Type whole language sets as `LanguageSetManifoldGraph` objects before using them as compression surfaces.
8. Use the Q16_16 lowering certificate as the first proof-backed RRC compiler lane.
```

## Claim Boundary

RRC is now an executable integration boundary.  It is not yet a verified
compiler.  The current value is that it turns abstract type-shape language into
a receipt-bearing, inspectable pipeline with explicit `CANDIDATE` and `HOLD`
states.
