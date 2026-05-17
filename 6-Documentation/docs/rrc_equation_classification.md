# RRC Equation Projection

This is a Rainbow Raccoon Compiler projection pass over local equation surfaces.
It records nearest lawful shapes, projection axes, and admissibility holds; it is not a proof of the equations.

Receipt hash: `37818bcb1a029408bd9fe3984a1fca9936cd7312e78aecf16ec88d394b6f35c8`
Equation count: `278`

## Counts By RRC Shape

| RRC shape | Count |
|---|---:|
| `CadForceProbeReceipt` | 2 |
| `CognitiveLoadField` | 77 |
| `LogogramProjection` | 126 |
| `ProjectableGeometryTopology` | 37 |
| `SignalShapedRouteCompiler` | 36 |

## Missing Axes

| Axis | Count |
|---|---:|
| `receipt_density` | 235 |

## Witness Schema

- `scale_witness`: declares the routing scale band, unit hint, threshold policy, tolerance policy, and budget policy.
- `negative_control_witness`: declares fail-closed controls such as empty-equation invalidation, label-shuffle baseline, missing-receipt HOLD, and domain-specific HOLD boundaries.


## Sample Projections

| Equation | RRC shape | Status | Top axes |
|---|---|---|---|
| `bandwidth_adjusted_threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `bandwidth_overflow` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `effective_cognitive_load` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `emotional_gate` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `emotional_load` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, scale_band_declared, shape_closure, negative_control_strength` |
| `emotional_offload` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `historical_emotional_barrier` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `historical_emotional_temperature` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `historical_offload_efficiency` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `overflow_gate` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `raw_cognitive_load` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, scale_band_declared, shape_closure, negative_control_strength` |
| `residual_stress` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, negative_control_strength, witness_declared` |
| `threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, scale_band_declared, shape_closure, negative_control_strength` |
| `total_protective_load` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, negative_control_strength, witness_declared` |
| `trauma_adjusted_emotional_barrier` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `trauma_adjusted_emotional_temperature` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `trauma_adjusted_offload_efficiency` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `trauma_adjusted_threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `core_equations` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `field_mapping` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `source_domain` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `target_domain` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `heat_loss` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `magnetic_projection` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |

## Claim Boundary

RRC equation projection is an admissibility and routing pass. Human labels are non-authoritative hints only; CANDIDATE means suitable for next-stage checking, not mathematically proved.
