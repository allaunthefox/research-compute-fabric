# Lean Module Cleave Plan

This report classifies the local Lean module graph into required, optional, legacy, external, and review surfaces.

## Roots

Reachability roots:

- `Semantics`
- `PIST`
- `PistBridge`
- `PistSimulation`

## Summary

- Local Lean modules: 910
- Reachable from aggregate roots: 202
- Not reachable from aggregate roots: 708

## Cleave Classes

| Class | Modules | Default action |
|---|---:|---|
| UNREACHED_DOMAIN_CANDIDATE | 329 | Local module not reached by aggregate build; candidate for optional import, extension bundle, or archive. |
| UNREACHED_HOLD_REVIEW | 193 | Not reached by aggregate build and taxonomy is ambiguous; inspect before import/move/archive. |
| EXTERNAL_REFERENCE | 147 | Keep as reference-only material; do not treat as owned core. |
| REQUIRED_AGGREGATE | 106 | Reachable from aggregate Lean build roots. |
| REQUIRED_HOLD_REVIEW | 96 | Reachable from aggregate build but taxonomy is ambiguous; review before moving. |
| OPTIONAL_EXTENSION_SCAFFOLD | 28 | Scaffold/extension surface; keep modular unless promoted. |
| RUNTIME_ENTRYPOINT | 8 | Executable or service entrypoint; keep outside core proof taxonomy. |
| ANCILLARY_HOLDING | 3 | Already cleaved out of required core; keep with receipt until promoted or archived. |

## Domain Mix By Cleave Class

### UNREACHED_DOMAIN_CANDIDATE

| Domain | Modules |
|---|---:|
| GenomicsBiology | 100 |
| MathFormal | 60 |
| TestingVerification | 35 |
| GeometryTopology | 35 |
| KernelCore | 18 |
| InformationTheory | 14 |
| HardwareSparkle | 12 |
| PhysicsPDE | 11 |
| AddressingMemory | 10 |
| ControlRouting | 9 |
| CompressionGCCL | 9 |
| AgentsSwarm | 8 |

### UNREACHED_HOLD_REVIEW

| Domain | Modules |
|---|---:|
| KernelCore | 48 |
| GeometryTopology | 23 |
| GenomicsBiology | 23 |
| MathFormal | 23 |
| CompressionGCCL | 21 |
| InformationTheory | 18 |
| ReviewUnclassified | 17 |
| PhysicsPDE | 12 |
| HardwareSparkle | 3 |
| QuantumInformation | 2 |
| AgentsSwarm | 1 |
| NetworkProtocol | 1 |

### EXTERNAL_REFERENCE

| Domain | Modules |
|---|---:|
| ExternalReference | 146 |
| MathFormal | 1 |

### REQUIRED_AGGREGATE

| Domain | Modules |
|---|---:|
| PhysicsPDE | 20 |
| GeometryTopology | 17 |
| MathFormal | 12 |
| KernelCore | 11 |
| ExtensionScaffold | 9 |
| ENEIntegration | 7 |
| TestingVerification | 7 |
| ControlRouting | 5 |
| CompressionGCCL | 5 |
| AgentsSwarm | 4 |
| GenomicsBiology | 2 |
| RRCAndOmindirection | 2 |

### REQUIRED_HOLD_REVIEW

| Domain | Modules |
|---|---:|
| KernelCore | 35 |
| MathFormal | 17 |
| GeometryTopology | 9 |
| GenomicsBiology | 7 |
| CompressionGCCL | 7 |
| PhysicsPDE | 7 |
| InformationTheory | 5 |
| ReviewUnclassified | 3 |
| HardwareSparkle | 2 |
| RuntimeEntrypoints | 2 |
| AgentsSwarm | 1 |
| RRCAndOmindirection | 1 |

### OPTIONAL_EXTENSION_SCAFFOLD

| Domain | Modules |
|---|---:|
| ExtensionScaffold | 27 |
| PhysicsPDE | 1 |

### RUNTIME_ENTRYPOINT

| Domain | Modules |
|---|---:|
| RuntimeEntrypoints | 8 |

### ANCILLARY_HOLDING

| Domain | Modules |
|---|---:|
| AncillaryHolding | 3 |

## First Review Queue

Start with reachable HOLD modules, then unreached HOLD modules. Those are the places where moving files before review is most likely to break or mislabel the graph.

| Module | Class | Domain | Path |
|---|---|---|---|
| `Semantics.Lemmas` | REQUIRED_HOLD_REVIEW | AgentsSwarm | `0-Core-Formalism/lean/Semantics/Semantics/Lemmas.lean` |
| `Semantics.ContinuedFractionCompression` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/ContinuedFractionCompression.lean` |
| `Semantics.HumanNeuralCompressionVerification` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/HumanNeuralCompressionVerification.lean` |
| `Semantics.HybridConvergence` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/HybridConvergence.lean` |
| `Semantics.LadderLUT` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/LadderLUT.lean` |
| `Semantics.LogogramSubstitution` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/LogogramSubstitution.lean` |
| `Semantics.ReceiptCore` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/ReceiptCore.lean` |
| `Semantics.ThermodynamicSort` | REQUIRED_HOLD_REVIEW | CompressionGCCL | `0-Core-Formalism/lean/Semantics/Semantics/ThermodynamicSort.lean` |
| `Semantics.AbelianSandpileRouting` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/AbelianSandpileRouting.lean` |
| `Semantics.Atoms` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/Atoms.lean` |
| `Semantics.CouchFilterNormalization` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/CouchFilterNormalization.lean` |
| `Semantics.DomainState` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/DomainState.lean` |
| `Semantics.GeneticGroundUp` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/GeneticGroundUp.lean` |
| `Semantics.Genome18` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/Genome18.lean` |
| `Semantics.PeptideMoERepair` | REQUIRED_HOLD_REVIEW | GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/PeptideMoERepair.lean` |
| `Semantics.BraidCross` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/BraidCross.lean` |
| `Semantics.BraidStrand` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/BraidStrand.lean` |
| `Semantics.GpuDutyAssignment` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/GpuDutyAssignment.lean` |
| `Semantics.Graph` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/Graph.lean` |
| `Semantics.NUVMATH` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/NUVMATH.lean` |
| `Semantics.Projections` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/Projections.lean` |
| `Semantics.S3C` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/S3C.lean` |
| `Semantics.SwarmTopology` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/SwarmTopology.lean` |
| `Semantics.TopologyOptimization` | REQUIRED_HOLD_REVIEW | GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/TopologyOptimization.lean` |
| `Semantics.NeurodivergentPatternLUT` | REQUIRED_HOLD_REVIEW | HardwareSparkle | `0-Core-Formalism/lean/Semantics/Semantics/NeurodivergentPatternLUT.lean` |
| `Semantics.SparkleBridge` | REQUIRED_HOLD_REVIEW | HardwareSparkle | `0-Core-Formalism/lean/Semantics/Semantics/SparkleBridge.lean` |
| `Semantics.MetadataSurfaceComputation` | REQUIRED_HOLD_REVIEW | InformationTheory | `0-Core-Formalism/lean/Semantics/Semantics/MetadataSurfaceComputation.lean` |
| `Semantics.PeptideMoE` | REQUIRED_HOLD_REVIEW | InformationTheory | `0-Core-Formalism/lean/Semantics/Semantics/PeptideMoE.lean` |
| `Semantics.PeptideMoEExamples` | REQUIRED_HOLD_REVIEW | InformationTheory | `0-Core-Formalism/lean/Semantics/Semantics/PeptideMoEExamples.lean` |
| `Semantics.PeptideMoEFailure` | REQUIRED_HOLD_REVIEW | InformationTheory | `0-Core-Formalism/lean/Semantics/Semantics/PeptideMoEFailure.lean` |
| `Semantics.TSMEfficiency` | REQUIRED_HOLD_REVIEW | InformationTheory | `0-Core-Formalism/lean/Semantics/Semantics/TSMEfficiency.lean` |
| `Semantics.CacheSieve` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/CacheSieve.lean` |
| `Semantics.Canon` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Canon.lean` |
| `Semantics.CanonSerialization` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/CanonSerialization.lean` |
| `Semantics.CognitiveLoad` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/CognitiveLoad.lean` |
| `Semantics.Constitution` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Constitution.lean` |
| `Semantics.Curvature` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Curvature.lean` |
| `Semantics.DSPTranslation` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/DSPTranslation.lean` |
| `Semantics.ENEDistributedNode` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/ENEDistributedNode.lean` |
| `Semantics.Errors` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Errors.lean` |
| `Semantics.Evolution` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Evolution.lean` |
| `Semantics.FieldSolver` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/FieldSolver.lean` |
| `Semantics.FlagSort` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/FlagSort.lean` |
| `Semantics.Forgejo` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Forgejo.lean` |
| `Semantics.FuzzyAssociation` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/FuzzyAssociation.lean` |
| `Semantics.GeneBytecodeJIT` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/GeneBytecodeJIT.lean` |
| `Semantics.Github` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Github.lean` |
| `Semantics.HormoneDeriv` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/HormoneDeriv.lean` |
| `Semantics.Hutter` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Hutter.lean` |
| `Semantics.HydrogenicPhiTorsionBraid` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/HydrogenicPhiTorsionBraid.lean` |
| `Semantics.JsonLSurfaceConnector` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/JsonLSurfaceConnector.lean` |
| `Semantics.MISignal` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/MISignal.lean` |
| `Semantics.MechanicalLogic` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/MechanicalLogic.lean` |
| `Semantics.MorphicNeuralNetwork` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/MorphicNeuralNetwork.lean` |
| `Semantics.NonEuclideanGeometry` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/NonEuclideanGeometry.lean` |
| `Semantics.OmniNetwork` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/OmniNetwork.lean` |
| `Semantics.Orchestrate` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Orchestrate.lean` |
| `Semantics.Pbacs` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Pbacs.lean` |
| `Semantics.Physics` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Physics.lean` |
| `Semantics.Physics.BindPhysics` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Physics/BindPhysics.lean` |
| `Semantics.ProjectableGeometryCanonical` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/ProjectableGeometryCanonical.lean` |
| `Semantics.Protocol` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Protocol.lean` |
| `Semantics.ScalarCollapse` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/ScalarCollapse.lean` |
| `Semantics.Tape` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Tape.lean` |
| `Semantics.VoxelEncoding` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/VoxelEncoding.lean` |
| `Semantics.Witness` | REQUIRED_HOLD_REVIEW | KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Witness.lean` |
| `Semantics.CodonOTOM` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/CodonOTOM.lean` |
| `Semantics.ComputationProfile` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/ComputationProfile.lean` |
| `Semantics.ENEApi` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/ENEApi.lean` |
| `Semantics.ENECredentialEnvelope` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/ENECredentialEnvelope.lean` |
| `Semantics.GemmaIntegration` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/GemmaIntegration.lean` |
| `Semantics.GradientPathMap` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/GradientPathMap.lean` |
| `Semantics.LaviGen` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/LaviGen.lean` |
| `Semantics.MoECache` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/MoECache.lean` |
| `Semantics.NetworkCapacity` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/NetworkCapacity.lean` |
| `Semantics.NonStandardInterfaces` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/NonStandardInterfaces.lean` |
| `Semantics.PassiveComputation` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/PassiveComputation.lean` |
| `Semantics.SolitonTensor` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/SolitonTensor.lean` |
| `Semantics.SpatialEvo` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/SpatialEvo.lean` |
| `Semantics.SwarmCodeReview` | REQUIRED_HOLD_REVIEW | MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/SwarmCodeReview.lean` |

## Claim Boundary

This is a cleaving plan, not an automatic folder move. Required means reachable from the current aggregate Lean roots. Unreached does not mean useless; it means optional, scaffold, external, legacy, or not currently wired into the aggregate surface.
