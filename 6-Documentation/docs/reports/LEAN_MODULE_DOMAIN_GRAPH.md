# Lean Module Domain Graph

Generated inventory of repo-local Lean modules under `0-Core-Formalism/lean`, excluding `.lake` package dependencies.

## Outputs

- `shared-data/data/lean_module_graph/modules.jsonl`
- `shared-data/data/lean_module_graph/import_edges.csv`
- `shared-data/data/lean_module_graph/domain_edges.csv`
- `shared-data/data/lean_module_graph/domains.csv`
- `shared-data/data/lean_module_graph/lean_module_domain_graph.graphml`

## Summary

- Local Lean modules scanned: 910
- Local import edges resolved: 1745
- Domain buckets: 21
- HOLD-review modules: 292
- Total literal `sorry` occurrences: 69

## Domain Counts

| Domain | Modules | HOLD? |
|---|---:|---|
| ExternalReference | 146 | 0 review |
| GenomicsBiology | 132 | 30 review |
| MathFormal | 113 | 40 review |
| KernelCore | 112 | 83 review |
| GeometryTopology | 84 | 32 review |
| PhysicsPDE | 51 | 19 review |
| CompressionGCCL | 42 | 28 review |
| TestingVerification | 42 | 0 review |
| InformationTheory | 38 | 23 review |
| ExtensionScaffold | 36 | 0 review |
| ReviewUnclassified | 20 | 20 review |
| HardwareSparkle | 17 | 5 review |
| ControlRouting | 15 | 1 review |
| AgentsSwarm | 14 | 2 review |
| ENEIntegration | 13 | 0 review |
| AddressingMemory | 12 | 0 review |
| RuntimeEntrypoints | 10 | 5 review |
| NetworkProtocol | 4 | 1 review |
| AncillaryHolding | 3 | 0 review |
| QuantumInformation | 3 | 2 review |
| RRCAndOmindirection | 3 | 1 review |

## HOLD Samples

HOLD means the classifier assigned a primary graph domain, but the module needs human review because the signal was missing or conflicting. It is not a build failure.

| Module | Reason | Path |
|---|---|---|
| `BindServer` | tie: KernelCore,PhysicsPDE,RuntimeEntrypoints | `0-Core-Formalism/lean/Semantics/BindServer.lean` |
| `Core.BindAxioms` | tie: KernelCore,MathFormal | `0-Core-Formalism/lean/Semantics/Core/BindAxioms.lean` |
| `Core.InformationManifold` | tie: GenomicsBiology,GeometryTopology,InformationTheory,MathFormal | `0-Core-Formalism/lean/Semantics/Core/InformationManifold.lean` |
| `Core.T1_Coherence` | tie: GeometryTopology,MathFormal | `0-Core-Formalism/lean/Semantics/Core/T1_Coherence.lean` |
| `EvolutionaryTransfold` | tie: GenomicsBiology,MathFormal | `0-Core-Formalism/lean/Semantics/EvolutionaryTransfold.lean` |
| `EvolutionaryTransfoldExpanded` | tie: GenomicsBiology,MathFormal | `0-Core-Formalism/lean/Semantics/EvolutionaryTransfoldExpanded.lean` |
| `ExtremeParameterTestEval` | tie: KernelCore,PhysicsPDE | `0-Core-Formalism/lean/Semantics/ExtremeParameterTestEval.lean` |
| `ManifoldCompressionAgnostic` | tie: CompressionGCCL,GeometryTopology | `0-Core-Formalism/lean/Semantics/ManifoldCompressionAgnostic.lean` |
| `MetaManifoldLanguageMerging` | tie: GeometryTopology,InformationTheory | `0-Core-Formalism/lean/Semantics/MetaManifoldLanguageMerging.lean` |
| `MinimumNeuralCompression` | tie: CompressionGCCL,ExternalReference | `0-Core-Formalism/lean/Semantics/MinimumNeuralCompression.lean` |
| `OpenWormBenchmark` | tie: ENEIntegration,InformationTheory,TestingVerification | `0-Core-Formalism/lean/Semantics/OpenWormBenchmark.lean` |
| `QuizTest` | tie: ControlRouting,KernelCore,MathFormal | `0-Core-Formalism/lean/Semantics/QuizTest.lean` |
| `Semantics.ASCIIGen` | tie: CompressionGCCL,GenomicsBiology,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/ASCIIGen.lean` |
| `Semantics.AVMRClassification` | tie: ControlRouting,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AVMRClassification.lean` |
| `Semantics.AVMRCore` | tie: ControlRouting,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AVMRCore.lean` |
| `Semantics.AVMRFrameworkMetaprobe` | tie: ControlRouting,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AVMRFrameworkMetaprobe.lean` |
| `Semantics.AVMRProofs` | tie: ControlRouting,InformationTheory | `0-Core-Formalism/lean/Semantics/Semantics/AVMRProofs.lean` |
| `Semantics.AVMRTheorems` | tie: ControlRouting,GenomicsBiology,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AVMRTheorems.lean` |
| `Semantics.AbelianSandpileRouting` | tie: AddressingMemory,ControlRouting,GenomicsBiology,MathFormal,NetworkProtocol | `0-Core-Formalism/lean/Semantics/Semantics/AbelianSandpileRouting.lean` |
| `Semantics.Adaptation` | tie: AgentsSwarm,GenomicsBiology | `0-Core-Formalism/lean/Semantics/Semantics/Adaptation.lean` |
| `Semantics.AgenticCore` | tie: AgentsSwarm,ControlRouting,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AgenticCore.lean` |
| `Semantics.AgenticOrchestration` | tie: AgentsSwarm,HardwareSparkle | `0-Core-Formalism/lean/Semantics/Semantics/AgenticOrchestration.lean` |
| `Semantics.AgenticOrchestrationField` | tie: AgentsSwarm,InformationTheory,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AgenticOrchestrationField.lean` |
| `Semantics.AnalysisFoundations` | tie: MathFormal,PhysicsPDE | `0-Core-Formalism/lean/Semantics/Semantics/AnalysisFoundations.lean` |
| `Semantics.AngrySphinx` | tie: ControlRouting,GeometryTopology,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/AngrySphinx.lean` |
| `Semantics.Atoms` | tie: GenomicsBiology,GeometryTopology,HardwareSparkle | `0-Core-Formalism/lean/Semantics/Semantics/Atoms.lean` |
| `Semantics.BHOCS` | no classifier signal | `0-Core-Formalism/lean/Semantics/Semantics/BHOCS.lean` |
| `Semantics.Basic` | tie: GenomicsBiology,HardwareSparkle | `0-Core-Formalism/lean/Semantics/Semantics/Basic.lean` |
| `Semantics.BindEngine` | tie: CompressionGCCL,KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/BindEngine.lean` |
| `Semantics.Biology.QuaternionGenomic` | tie: GenomicsBiology,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/Biology/QuaternionGenomic.lean` |
| `Semantics.BitcoinMetaprobe` | tie: ControlRouting,GeometryTopology,HardwareSparkle,KernelCore,NetworkProtocol | `0-Core-Formalism/lean/Semantics/Semantics/BitcoinMetaprobe.lean` |
| `Semantics.BitcoinMetaprobeEval` | tie: KernelCore,NetworkProtocol,TestingVerification | `0-Core-Formalism/lean/Semantics/Semantics/BitcoinMetaprobeEval.lean` |
| `Semantics.BitcoinRGFlow` | tie: InformationTheory,KernelCore,MathFormal,NetworkProtocol | `0-Core-Formalism/lean/Semantics/Semantics/BitcoinRGFlow.lean` |
| `Semantics.BracketShellCount` | tie: CompressionGCCL,ControlRouting,GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/BracketShellCount.lean` |
| `Semantics.BraidCross` | tie: ControlRouting,GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/BraidCross.lean` |
| `Semantics.BraidStrand` | tie: ControlRouting,GeometryTopology | `0-Core-Formalism/lean/Semantics/Semantics/BraidStrand.lean` |
| `Semantics.BraidedFieldPaths` | tie: GeometryTopology,InformationTheory,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/BraidedFieldPaths.lean` |
| `Semantics.CacheSieve` | tie: AddressingMemory,KernelCore,LegacyQuarantine,TestingVerification | `0-Core-Formalism/lean/Semantics/Semantics/CacheSieve.lean` |
| `Semantics.CalibratedKernel` | tie: CompressionGCCL,TestingVerification | `0-Core-Formalism/lean/Semantics/Semantics/CalibratedKernel.lean` |
| `Semantics.Canon` | tie: AddressingMemory,KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/Canon.lean` |
| `Semantics.CanonAdapters` | tie: ENEIntegration,KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/CanonAdapters.lean` |
| `Semantics.CanonSerialization` | tie: ENEIntegration,KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/CanonSerialization.lean` |
| `Semantics.CellSnowballConstraint` | no classifier signal | `0-Core-Formalism/lean/Semantics/Semantics/CellSnowballConstraint.lean` |
| `Semantics.ClassicalEuclideanGeometry` | tie: GeometryTopology,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/ClassicalEuclideanGeometry.lean` |
| `Semantics.CodonOTOM` | tie: AddressingMemory,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/CodonOTOM.lean` |
| `Semantics.CognitiveLoad` | tie: AgentsSwarm,KernelCore | `0-Core-Formalism/lean/Semantics/Semantics/CognitiveLoad.lean` |
| `Semantics.CognitiveMorphemics` | tie: AddressingMemory,AgentsSwarm,ControlRouting,KernelCore,MathFormal,TestingVerification | `0-Core-Formalism/lean/Semantics/Semantics/CognitiveMorphemics.lean` |
| `Semantics.CollectiveManifoldInterface` | tie: GeometryTopology,KernelCore,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/CollectiveManifoldInterface.lean` |
| `Semantics.Components.Bind` | tie: KernelCore,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/Components/Bind.lean` |
| `Semantics.Components.Composition` | tie: KernelCore,MathFormal | `0-Core-Formalism/lean/Semantics/Semantics/Components/Composition.lean` |

## Claim Boundary

This graph is an inventory and routing surface. It does not prove that each module is architecturally correct, imported by the aggregate build, or assigned to its final permanent domain. Ambiguous modules are deliberately marked HOLD for human review.
