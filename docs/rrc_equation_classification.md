# RRC Equation Projection

This is a Rainbow Raccoon Compiler projection pass over local equation surfaces.
It records nearest lawful shapes, projection axes, and admissibility holds; it is not a proof of the equations.

Receipt hash: `c758aadb2bf11922a805d695d5b7bafa477ad426e60ea8e925490f14ccba497c`
Equation count: `278`

## Counts By RRC Shape

| RRC shape | Count |
|---|---:|
| `CadForceProbeReceipt` | 2 |
| `CognitiveLoadField` | 77 |
| `HoldForUnlawfulOrUnderspecifiedShape` | 125 |
| `LogogramProjection` | 1 |
| `ProjectableGeometryTopology` | 37 |
| `SignalShapedRouteCompiler` | 36 |

## Missing Axes

| Axis | Count |
|---|---:|
| `negative_control_strength` | 39 |
| `scale_band_declared` | 249 |

## Sample Projections

| Equation | RRC shape | Status | Top axes |
|---|---|---|---|
| `bandwidth_adjusted_threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, semantic_entropy` |
| `bandwidth_overflow` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `effective_cognitive_load` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `emotional_gate` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `emotional_load` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, semantic_entropy` |
| `emotional_offload` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, semantic_entropy` |
| `historical_emotional_barrier` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `historical_emotional_temperature` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `historical_offload_efficiency` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `overflow_gate` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, semantic_entropy` |
| `raw_cognitive_load` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, semantic_entropy` |
| `residual_stress` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, decoder_declared, witness_declared` |
| `threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, scale_band_declared` |
| `total_protective_load` | `CognitiveLoadField` | `HOLD` | `projection_declared, shape_closure, decoder_declared, witness_declared` |
| `trauma_adjusted_emotional_barrier` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `trauma_adjusted_emotional_temperature` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `trauma_adjusted_offload_efficiency` | `CognitiveLoadField` | `HOLD` | `projection_declared, witness_declared, shape_closure, residual_risk` |
| `trauma_adjusted_threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, residual_risk` |
| `core_equations` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, semantic_entropy, shape_closure, witness_declared` |
| `field_mapping` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, compression_pressure` |
| `source_domain` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, compression_pressure` |
| `target_domain` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, compression_pressure` |
| `heat_loss` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, compression_pressure` |
| `magnetic_projection` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, compression_pressure` |

## Claim Boundary

RRC equation projection is an admissibility and routing pass. Human labels are non-authoritative hints only; CANDIDATE means suitable for next-stage checking, not mathematically proved.
