import Semantics.Bind
import Semantics.ProvenanceSource
import Semantics.Forgejo
import Semantics.Github
import Semantics.Hutter
import Semantics.Transition
import Semantics.Metatype
import Semantics.Autobalance
import Semantics.OmniNetwork
import Semantics.Protocol
import Semantics.FuzzyAssociation
import Semantics.Curvature
import Semantics.Testing.StructuralAttestation
import Semantics.MechanicalLogic
import Semantics.FlagSort
import Semantics.ThermodynamicSort
import Semantics.FieldSolver
import ExtensionScaffold.Compression.CellCore
import ExtensionScaffold.Compression.SignalPolicy
import ExtensionScaffold.Compression.Metatyping
import Semantics.SLUQ
import Semantics.DSPTranslation
import Semantics.CacheSieve
import Semantics.RelationMaskTrainer
import Semantics.CognitiveLoad
import Semantics.MISignal
import Semantics.HormoneDeriv
import Semantics.NonEuclideanGeometry
import Semantics.VoxelEncoding
import Semantics.Atoms
import Semantics.Lemmas
import Semantics.Decomposition
import Semantics.Projections
import Semantics.Graph
import Semantics.Path
import Semantics.Witness
import Semantics.Diagnostics
import Semantics.Universality
import Semantics.Substrate
import Semantics.Canon
import Semantics.Pbacs
import Semantics.Orchestrate
import Semantics.Evolution
import Semantics.ScalarCollapse
import Semantics.Constitution
import Semantics.Prohibited
import Semantics.Physics
import Semantics.Spectrum
import Semantics.GeneticCode
import Semantics.ShellModel
import Semantics.SpectralField
import Semantics.CodonOTOM
import Semantics.CodonPeptideConsistency
import Semantics.VecState
import Semantics.PrimeLut
import PIST
import PistBridge
-- PistSimulation imported via Semantics.TreeDIATKruskal; bare import removed
-- to avoid double-import collision with Semantics.PistSimulation in the glob build.

import Semantics.Tape
import Semantics.DynamicCanal
import Semantics.Functions.BracketedCalculus
import Semantics.LocalDerivative
import Semantics.SolitonTensor
import Semantics.CanonicalInterval
import Semantics.MetricCore
import Semantics.ComputationProfile
import Semantics.RaycastField
import Semantics.HyperFlow
import Semantics.Surface
import Semantics.BraidBracket
import Semantics.BraidStrand
import Semantics.BraidCross
import Semantics.Q0_2
import Semantics.BraidEigensolid
import Semantics.MasterEquation
import ExtensionScaffold.Physics.VideoWeirdMachine
import Semantics.OrderedFieldTokens
-- TODO(lean-port): EntropyMeasures is quarantined from the main build until
-- its remaining `sorry` proof holes are eliminated.
-- import Semantics.EntropyMeasures
import Semantics.DiffusionSNRBias
import Semantics.LaviGen
import Semantics.ExperienceCompression
import Semantics.HumanNeuralCompressionVerification
import Semantics.AbelianSandpileRouting
import Semantics.CouchFilterNormalization
import Semantics.GradientPathMap
import Semantics.SpatialEvo
import Semantics.VLsIPartition
import Semantics.HybridConvergence
import Semantics.SubagentOrchestrator
import Semantics.SwarmQueryAPI
import Semantics.SwarmCodeReview
import Semantics.NextGenAgentDesign
import Semantics.GeneBytecodeJIT
import Semantics.Functions.MathDebate
import Semantics.SwarmCompetition
import Semantics.SwarmTopology
import Semantics.TopologyOptimization
import Semantics.NonStandardInterfaces
import Semantics.TSMEfficiency
import Semantics.Testing.VirtualGPUBenchmark
import Semantics.Testing.WorkloadTestbench
import Semantics.Testing.VirtualGPUTestbench
import Semantics.VirtualGPUTopology
import Semantics.ResourceLayers
import Semantics.NetworkCapacity
import Semantics.EfficiencyAnalysis
import Semantics.ENEApi
import Semantics.MoECache
import Semantics.ASCIIArtCompetition
import Semantics.ASCIIArtStore
import Semantics.SwarmENEMiddleware
import Semantics.HyperbolicEncoding
import Semantics.GemmaIntegration
import Semantics.ENECredentialEnvelope
import Semantics.ENEDistributedNode
import Semantics.TopologyNode
import Semantics.GeometricTopology
import Semantics.ManyWorldsAddress
import Semantics.CrossDimensionalFilter
import Semantics.TopologyResilience
import Semantics.GeneticGroundUp
import Semantics.Testing.GeneticGroundUpBenchmark
import Semantics.Testing.ErdosHarness
import Semantics.Testing.ErdosSurface
import Semantics.OTOMOntology
import Semantics.Connectors
import Semantics.SLUG3
import Semantics.PeptideMoE
import Semantics.PeptideMoEExamples
import Semantics.PeptideMoEFailure
import Semantics.PeptideMoERepair
import Semantics.GCLTopologyRevision
import Semantics.SparkleBridge
import Semantics.HydrogenicPhiTorsionBraid
import Semantics.NUVMATH
import Semantics.AVM
import Semantics.SidonAVM
import Semantics.BurgersPDE
import Semantics.StochasticBurgersPDE
import Semantics.KdVBurgersPDE
import Semantics.Burgers2DPDE
import Semantics.Burgers3DPDE
import Semantics.ColeHopfTransform
import Semantics.LawfulLoss
import Semantics.Core.MassNumber
import Semantics.RRCLogogramProjection
import Semantics.PIST.Spectral
import Semantics.PIST.Repair
import Semantics.PIST.Motif
import Semantics.ThresholdVector
import Semantics.LogogramRotationLoop
import Semantics.CompressionYield
import Semantics.WaveformTeleport
import Semantics.TreeDIATKruskal

import Semantics.Toolkit
import Semantics.DomainDetector
import Semantics.HonestParameterReport
import Semantics.FractionScan
import Semantics.ExperimentTracker
import Semantics.CrossDomainOneOverN
import Semantics.BaselineComparison
import Semantics.ParameterSensitivity
import Semantics.DimensionalConsistency
-- QUARANTINE: Probe stubs (files not yet written). Removed from root to keep
-- lake build non-crashing. TODO(lean-port): implement and re-enable.
-- import Semantics.AtomicTimescaleProbe
-- import Semantics.CosmologicalTimescaleProbe
-- import Semantics.SpacetimeStretchingProbe
-- import Semantics.BigBangTemporalAnchor
-- import Semantics.EinsteinFrameDragProbe
-- import Semantics.GeminiThreePathsProbe
-- import Semantics.ProtonDecayAnchor
-- import Semantics.ShortestObservableTime
-- import Semantics.LandauerShannonProbe
-- import Semantics.ImaginarySemanticTime
-- import Semantics.AdiabaticInvariantProbe
-- import Semantics.CalculusIntegralProbe
-- import Semantics.AdiabaticCalculusProbe
-- import Semantics.PadicCalculusProbe
-- import Semantics.GapSpaceProbe
-- import Semantics.ArakelovAdeleProbe
-- import Semantics.AdelicStringProbe
-- import Semantics.MengerUniversalProbe
-- import Semantics.Genus1MengerEmbedding
-- import Semantics.GeneticFieldEquation
-- import Semantics.CivilizationalPulseProbe
-- import Semantics.SingularityPulseProbe
-- import Semantics.MediaTransferProbe
-- import Semantics.LanguageTransferProbe
-- import Semantics.LanguageZoologyProbe
-- import Semantics.EcologicalPeriodDataProbe
-- import Semantics.ThermodynamicLanguageProbe
-- import Semantics.GeneticThermodynamicLimitProbe
-- import Semantics.ExpandedGeneticAlphabetProbe
-- import Semantics.GeneticSignalTransformProbe
-- import Semantics.SemanticBasinOverflowProbe
-- import Semantics.GeneticErrorMinimizationProbe
-- import Semantics.InformationBottleneckLanguageProbe
-- import Semantics.CrossModalGeneticLanguageProbe
-- import Semantics.LandauerGeneticClockProbe
import Semantics.FAMM
import Semantics.HCMMR.Core
import Semantics.HCMMR.Kernels.FAMMScarMemory
import Semantics.MMRFAMMUnification
import Semantics.CGAVersorAddress
import Semantics.FAMMCoChain
import Semantics.Goxel

namespace Semantics

def version := "2.0.0-Cambrian-Bind"

end Semantics
