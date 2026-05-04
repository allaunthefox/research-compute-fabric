import csv, json, os
from collections import defaultdict

# Read MATH_MODEL_MAP.tsv
os.chdir('/home/allaun/Documents/Research Stack/3-Mathematical-Models')
with open('MATH_MODEL_MAP.tsv', 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    data = list(reader)

# Group families with their equations, purposes, variables
fam_info = defaultdict(lambda: {'eqs': [], 'vars': [], 'purposes': [], 'binds': []})
for r in data:
    fam = r.get('Family', '')
    if fam and fam != 'None':
        eq = r.get('Equation', '')
        var = r.get('Variables', '')
        purp = r.get('Purpose', '')
        bind = r.get('Bind_Class', '')
        if eq: fam_info[fam]['eqs'].append(eq[:100])
        if var: fam_info[fam]['vars'].append(var[:80])
        if purp: fam_info[fam]['purposes'].append(purp[:120])
        if bind: fam_info[fam]['binds'].append(bind)

# Map each family to a domain kind
family_to_domain = {}

# Comprehensive domain mapping
domains_map = {
    'mathematics': ['Number Theory', 'Combinatorial Analysis', 'Geometry Verifier', 'Non-Euclidean Geometry',
                    'ClassicalEuclideanGeometry', 'Chaotic Dynamics', 'Dynamical Systems', 'ScaleSpace',
                    'Topology', 'Making_It_Rigorous', 'PhinaryNumberSystem', 'Quaternion Algebra',
                    'Fixed-Point Arithmetic', 'Unit Conversion', 'SidonSet'],
    'physics': ['Physics', 'Quantum Geometry', 'Nonlinear PDEs', 'Stochastic PDEs', 'BurgersPDE',
                'Burgers2DPDE', 'Burgers3DPDE', 'ColeHopfTransform', 'StochasticBurgersPDE',
                'Fluid Dynamics', 'Aerodynamics', 'Thermodynamics', 'Thermodynamic', 'KDA Physics',
                'QCL Energy', 'ElectrostaticsMetaprobe', 'ElectromagneticSpectrum', 'CasimirMetaprobe',
                'Desalination', 'Manifold Evolution', 'FEA Semi-Truck', 'Theta-TaN Phonon Physics'],
    'biology': ['Biology', 'Biophysics', 'Molecular Biology', 'Cell Biology', 'Genetics',
                'Population Genetics', 'Microbiology', 'Evolutionary Biology', 'Evolutionary Dynamics',
                'Developmental Biology', 'Botany', 'Plant Physiology', 'Mycology', 'Marine Biology',
                'Oceanography', 'Ecology', 'Biogeochemistry', 'Agriculture',
                'Epigenetics', 'Quantum Biology', 'Radiation Biology', 'Synthetic Biology',
                'Immunology', 'Oncology', 'Gerontology', 'Life History', 'Chronobiology',
                'Circadian Biology', 'Metabolism', 'Neural Development', 'Biomechanics',
                'Physiology', 'Cardiac Physiology', 'Biophotonics', 'BiologicalRegulation',
                'BiologicalControl', 'BiologicalExergy', 'CancerMetabolic', 'CardiacYield',
                'CellularSignaling', 'ConstrainedEnergy', 'ConstructalMuscle', 'CorticalScaling',
                'GenomicStoichiometric', 'LocomotionMuscle', 'AdvancedBio'],
    'chemistry': ['Chemistry', 'Chemical Physics', 'Chemical Ecology'],
    'computation': ['Computation Profile', 'Compression', 'CompressionControl', 'CompressionEvidence',
                    'CompressionLossComparison', 'CompressionMaximization', 'CompressionMechanics',
                    'CompressionMechanicsBridge', 'DeltaGCL Compression', 'DeltaGCLCompression',
                    'DeltaGCL', 'Huffman', 'Cache Sieve', 'CacheSieve', 'StringStar',
                    'Information Theory', 'MI Signal', 'MISignal', 'Encoder'],
    'cognition': ['Cognitive Load', 'Cognitive Load', 'CognitiveAcoustic', 'CognitiveLearning',
                  'CognitiveLoad', 'Homeostatic Control', 'Neuroscience',
                  'Neurodivergent', 'Social Neuroscience', 'Psychology'],
    'language': ['Speech Science', 'Perception', 'Acoustic', 'AuditoryMasking',
                 'AuditoryMechanicsLaws', 'AuditoryPerceptionLaws', 'Vision Science'],
    'social': ['Social Science', 'Behavioral Dynamics', 'Game Theory', 'Foraging Theory'],
    'cryptography': ['Cryptography', 'GaloisRing', 'SBox', 'AngrySphinxPolicy', 'CooperativeLUT',
                     'BitcoinMetaprobe', 'BitcoinMetaprobeEval', 'BitcoinRGFlow', 'EthereumRGFlow',
                     'Crypto', 'PostQuantumEscrow'],
    'engineering': ['Engineering', 'FPGA Signal', 'FaultTolerance', 'ASICTopology',
                    'AngrySphinx', 'Hardware', 'DspErasureCoding', 'TopologyOptimization',
                    'VideoPhysics'],
    'machine_learning': ['Machine Learning', 'Time Series', 'AffineMappingLTSF', 'Metric Learning',
                         'CodonPeptideConsistency', 'PeptideMoE', 'CrossModalCompression',
                         'ExperienceCompression', 'DistributedTraining', 'SwarmMoERewiring',
                         'EtaMoE'],
    'topology': ['Topology', 'Braid Topology', 'Braid Field Theory', 'BraidBracket',
                 'BraidField', 'BraidCross', 'BraidStrand', 'BoundaryDynamics',
                 'BracketShellCount', 'BracketedCalculus', 'Manifold Networking',
                 'Manifold Routing', 'Manifold Networking Test', 'ManifoldNetworking',
                 'Non-Euclidean UV QUBO', 'Topological Encoder', 'TopologicalAwareness',
                 'TopologicalPersistence', 'AdversarialTopologyTest'],
    'information_theory': ['Information Theory', 'MI Signal', 'Encoding System',
                           'Cartesian System', 'Emoji Machine', 'PBACS Signal',
                           'Combined System'],
    'quantum': ['Quantum Geometry', 'Quantum Chaos', 'Quantum Biology', 'ElectronOrbitalConstraint',
                'QuantumManifoldGeometry', 'QuantumAwareLean', 'QuantizationMetaprobe'],
    'neural': ['Neuroscience', 'Neural Development', 'Neurodivergent', 'SpikingDynamics',
               'MorphicNeuralNetwork', 'CognitiveAcoustic', 'CognitiveLearning',
               'STDP', 'SpikeTimingShifter', 'STDPShifter'],
    'swarm_theory': ['Swarm Coordination', 'Swarm Analysis', 'SwarmCompetition', 'SwarmDesignReview',
                     'SwarmCodeGeneration', 'SwarmCodeReview', 'SwarmQueryAPI', 'SwarmRGFlow',
                     'SwarmTopology', 'SwarmENEMiddleware', 'SwarmMoERewiring'],
    'control_theory': ['Control Theory', 'Waveprobe Control', 'Waveprobe QUBO', 'KDA Control',
                       'Homeostatic Control', 'WaveformWaveprobePipeline', 'Waveprobe'],
    'semantics': ['Semantics', 'S3C', 'S3CGeometry', 'S3CResonance', 'S3CManifoldMetaprobe',
                  'S3CManifoldGeometryMetaprobe', 'S3CUnifiedMetaprobe', 'SemanticMass',
                  'SemanticRGFlow', 'SpectralField', 'Atoms', 'Bind', 'Bounded Hierarchical Cryptographic Space'],
    'scaling': ['ScaleSpace', 'Allometry', 'CorticalScaling', 'ConstructalMuscle', 'CardiacYield'],
    'grammar': ['WitnessGrammar', 'Prohibited', 'Constitution', 'EpistemicHonesty',
                'TriumvirateEnforcer'],
    'routing': ['Routing', 'Manifold Routing', 'Manifold Networking', 'HotPathColdPath',
                'RouteCost', 'AbelianSandpileRouting', 'ManifoldNetworking'],
    'genomic': ['Genomic Compression', 'GenomicStoichiometric', 'SyntheticGeneticCoding',
                'CodonPeptideConsistency', 'CodonOTOM', 'FibonacciEncoding'],
    'compression_systems': ['Compression', 'DeltaGCL Compression', 'DeltaGCLCompression',
                            'CrossModalCompression', 'StreamCompression', 'CompressionControl',
                            'CompressionEvidence', 'CompressionLossComparison',
                            'CompressionMaximization', 'CompressionMechanics', 'CompressionMechanicsBridge',
                            'YangMillsCompression', 'YangMillsCompressionBounds', 'YangMillsLattice',
                            'YangMillsLatticeSizing', 'YangMillsPerformance',
                            'PhiShellEncoding', 'VoxelEncoding', 'CR = U_size / C_size'],
    'biology_detail': ['Phonon Graph', 'Hormone Derivation', 'Cephalopod Distributed',
                       'Morpholino', 'miRNA_Shifter', 'TranscriptionShifter',
                       'TranslationShifter', 'HachimojiShifter', 'AEGISShifter',
                       'NaturalDNAShifter', 'PNAShifter', 'LNAShifter', 'SplicingShifter',
                       'PrionShifter', 'SpiegelmerShifter'],
    'chaos': ['Chaotic Dynamics', 'Logistic Map', 'LogisticMapShifter', 'DSE',
              'DeterministicStochasticEngine', 'Stochastic Processes', 'MasterEquation',
              'PopulationChaosDynamics'],
    'geometry': ['GWL Riemannian Geometry', 'GWL Rotation', 'GWL Temporal', 'GWL State Space',
                 'GWL Throat', 'GWL Connection', 'GWL Coordinate Charts', 'GWL Geodesic Integration',
                 'GWL Geodesic Integration (Integrated)', 'GWL Chiral Interaction', 'GWL Ternary State',
                 'Geometric Algebra', 'PIST', 'Dyson Swarm Geodesics', 'Virtual Alcubierre',
                 'Non-Euclidean UV QUBO', 'Manifold Dynamics', 'Constraint Geometry'],
    'verification': ['Verification', 'BaselineTest', 'ConservationTest', 'CostEffectiveVerification',
                     'GPUVerificationMetaprobe', 'Lean4ImprovementProofs', 'AVMRProofs',
                     'AVMRTheorems', 'AVMRFrameworkMetaprobe', 'AVMRInformation', 'AVMR',
                     'AgenticTheorems', 'Constitution', 'CasimirMetaprobe', 'DiffusionSNRBias',
                     'DSPTranslation', 'CrossDimensionalFilter', 'EnergyGradientSignal',
                     'MISignal', 'HotPathColdPath', 'Adaptation Theory', 'Dynamic Canal Theory',
                     'ManifoldNetworking', 'CalibratedKernel'],
    'network': ['Network Theory', 'Manifold Networking', 'CooperativeLUT', 'SIMDBranchPrediction',
                'TopologyResilience', 'TopologyFractalEncoding', 'TopologyGoldenSpiral',
                'TopologyPhinary', 'TopologyDlessScalar', 'TopologyDomainAlignment',
                'TopologyNode', 'DomainKernel', 'DomainModelIntegration', 'DomainRegistryAlignment',
                'DomainState', 'ConflictResolution', 'ExternalConnectors'],
    'algorithms': ['Algorithms', 'SolitonSearch', 'SolitonTensor', 'Search', 'SwarmCompetition',
                   'TileFlipConsensus'],
    'stochastic': ['Stochastic Processes', 'Stochastic PDEs', 'MasterEquation', 'PopulationChaosDynamics'],
    'n_body': ['N-Space Dynamics', 'NKCoupling', 'CoulombComplexity', 'CellSnowballConstraint',
               'ElectrostaticsMetaprobe'],
    'origin': ['Origin', 'Emergence System', 'UniverseCollisionConsensus', 'BHOCS', 'HybridTSMPISTTorus'],
    'NES': ['NES', 'AnalogDSP', 'VideoSynth', 'TemporalSuperSample', 'VirtualDisplay',
            'VoltageMath', 'MinimalOISC', 'OISC', 'CartridgeOISC', 'NanoKernel',
            'Metaprobe', 'UnifiedMath'],
    'genetic_encoding': ['HachimojiShifter', 'AEGISShifter', 'NaturalDNAShifter',
                         'TranscriptionShifter', 'TranslationShifter', 'PNAShifter',
                         'LNAShifter', 'SplicingShifter', 'PrionShifter',
                         'SpiegelmerShifter', 'miRNA_Shifter', 'MorpholinoShifter',
                         'SyntheticGeneticCoding', 'CodonPeptideConsistency', 'CodonOTOM'],
    'thermodynamics': ['Thermodynamic', 'Thermodynamics', 'Informatic Stress', 'KDA Physics',
                       'QCL Energy', 'BEA Thermo Bridge', 'ThermodynamicSort'],
    'protein': ['Protein Folding', 'BioRxivFormalization', 'ProteinTemplate',
                'Protein Binding'],
    'epidemiology': ['Epidemiology', 'Epidemiological', 'EpidemiologicalTrophic'],
    'oceanography': ['Oceanography', 'Marine Biology', 'Fluid Dynamics', 'Desalination'],
}

# Now build domain -> family list
domain_to_families = defaultdict(list)
assigned = set()
for domain, fams in domains_map.items():
    for f in fams:
        domain_to_families[domain].append(f)
        assigned.add(f)

# Also build a reverse mapping for output
print("// DOMAIN EXPANSION MAP —", len(assigned), "families assigned to", len(domain_to_families), "domains")
print()

for dom in sorted(domain_to_families.keys()):
    fams = domain_to_families[dom]
    print(f"  // {dom} — {len(fams)} families")
    for f in sorted(fams):
        info = fam_info.get(f, {'purposes': ['N/A']})
        purp = info['purposes'][0][:80] if info['purposes'] else 'N/A'
        print(f"  //   {f}")
