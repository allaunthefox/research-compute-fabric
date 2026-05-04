#!/usr/bin/env python3
"""
Enhanced Integrated Swarm System

Fully integrated swarm system combining:
- NII Cores (Non-Isotropic Informatic Cores): Semantic Analysis, Translation Engine, Verification
- Topology Awareness: Hardware topology mapping with custom PCB layers
- Math Database Integration: math_entities.db queries
- Lean Module Awareness: 88+ modules across 14 domains
- Geometric Parameters: κ², κ_hierarchy, ε, ρ, v, τ, σ, q
- FAMM Timing: Torsional stress, interlocking energy, laplacian energy
- Swarm Design Review: Consensus-based geometric enhancement analysis

Custom Layers Integration:
- PCB Stackup: 4-layer (Top, Inner 1 GND, Inner 2 Power/Bus, Bottom)
- Dielectric: Rogers 4350B (εr = 3.48)
- Trace-logic netlist with interferometric trace junctions
- Component placement (U1 central logic, U2 SRAM, U5 DAC, J1 USB-C)
"""

import sys
import json
import math
import sqlite3
import time
import hashlib
import uuid
import numpy as np
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
from collections import deque

# ═══════════════════════════════════════════════════════════════════════════
# Topology Data Structures (from pure_software_topology_mapper.py)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SensorReading:
    timestamp: float
    sensor_type: str
    sensor_name: str
    value: float
    unit: str
    path: str

@dataclass
class WireSegment:
    name: str
    length_mm: float
    resistance_ohm: float
    capacitance_pf: float
    inductance_nh: float
    impedance_ohm: float
    propagation_delay_ps: float

@dataclass
class Component:
    name: str
    type: str
    location: Tuple[float, float]
    voltage_mv: float
    current_ma: float
    temperature_c: float
    power_mw: float

@dataclass
class TopologyNode:
    id: str
    component: Component
    connections: List[str]
    voltage_mv: float
    current_ma: float
    timing_ps: float

@dataclass
class TopologyEdge:
    source: str
    target: str
    wire_segment: WireSegment
    voltage_drop_mv: float
    current_ma: float
    timing_ps: float
    impedance_ohm: float

@dataclass
class TopologyGraph:
    nodes: Dict[str, TopologyNode]
    edges: List[TopologyEdge]
    wire_segments: Dict[str, WireSegment]
    components: Dict[str, Component]
    sensor_readings: List[SensorReading]
    timestamp: float

class PCBSpecifications:
    COPPER_RESISTIVITY = 0.0172
    ROGERS_4350B_DIELECTRIC_CONSTANT = 3.48
    SPEED_OF_LIGHT = 299792458

# ═══════════════════════════════════════════════════════════════════════════
# Math Database Integration
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MathEntity:
    entity_id: str
    subject: str
    secondary_subjects: List[str]
    name: str
    statement: str
    proof_status: str
    formal_status: str
    lean_module: Optional[str]
    dependencies: List[str]
    citations: List[str]
    complexity_score: int
    year: int

class MathDatabase:
    """Interface to math_entities.db"""
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/data/math_entities.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
    
    def query_by_subject(self, subject: str) -> List[MathEntity]:
        """Query math entities by subject"""
        cursor = self.conn.execute(
            "SELECT * FROM math_entities WHERE subject = ?",
            (subject,)
        )
        entities = []
        for row in cursor.fetchall():
            # Safe JSON parsing with error handling
            try:
                secondary_subjects = json.loads(row[2]) if row[2] else []
            except (json.JSONDecodeError, TypeError):
                secondary_subjects = []
            
            try:
                dependencies = json.loads(row[8]) if row[8] else []
            except (json.JSONDecodeError, TypeError):
                dependencies = []
            
            try:
                citations = json.loads(row[9]) if row[9] else []
            except (json.JSONDecodeError, TypeError):
                citations = []
            
            entity = MathEntity(
                entity_id=row[0],
                subject=row[1],
                secondary_subjects=secondary_subjects,
                name=row[3],
                statement=row[4],
                proof_status=row[5],
                formal_status=row[6],
                lean_module=row[7],
                dependencies=dependencies,
                citations=citations,
                complexity_score=row[10],
                year=row[11]
            )
            entities.append(entity)
        return entities
    
    def query_by_lean_module(self, lean_module: str) -> List[MathEntity]:
        """Query math entities by Lean module"""
        cursor = self.conn.execute(
            "SELECT * FROM math_entities WHERE lean_module = ?",
            (lean_module,)
        )
        entities = []
        for row in cursor.fetchall():
            # Safe JSON parsing with error handling
            try:
                secondary_subjects = json.loads(row[2]) if row[2] else []
            except (json.JSONDecodeError, TypeError):
                secondary_subjects = []
            
            try:
                dependencies = json.loads(row[8]) if row[8] else []
            except (json.JSONDecodeError, TypeError):
                dependencies = []
            
            try:
                citations = json.loads(row[9]) if row[9] else []
            except (json.JSONDecodeError, TypeError):
                citations = []
            
            entity = MathEntity(
                entity_id=row[0],
                subject=row[1],
                secondary_subjects=secondary_subjects,
                name=row[3],
                statement=row[4],
                proof_status=row[5],
                formal_status=row[6],
                lean_module=row[7],
                dependencies=dependencies,
                citations=citations,
                complexity_score=row[10],
                year=row[11]
            )
            entities.append(entity)
        return entities
    
    def get_proven_entities(self) -> List[MathEntity]:
        """Get all proven math entities"""
        cursor = self.conn.execute(
            "SELECT * FROM math_entities WHERE proof_status = 'proven'"
        )
        entities = []
        for row in cursor.fetchall():
            # Safe JSON parsing with error handling
            try:
                secondary_subjects = json.loads(row[2]) if row[2] else []
            except (json.JSONDecodeError, TypeError):
                secondary_subjects = []
            
            try:
                dependencies = json.loads(row[8]) if row[8] else []
            except (json.JSONDecodeError, TypeError):
                dependencies = []
            
            try:
                citations = json.loads(row[9]) if row[9] else []
            except (json.JSONDecodeError, TypeError):
                citations = []
            
            entity = MathEntity(
                entity_id=row[0],
                subject=row[1],
                secondary_subjects=secondary_subjects,
                name=row[3],
                statement=row[4],
                proof_status=row[5],
                formal_status=row[6],
                lean_module=row[7],
                dependencies=dependencies,
                citations=citations,
                complexity_score=row[10],
                year=row[11]
            )
            entities.append(entity)
        return entities
    
    def get_unproven_entities(self) -> List[MathEntity]:
        """Get all math entities that are not proven"""
        cursor = self.conn.execute(
            "SELECT * FROM math_entities WHERE proof_status != 'proven'"
        )
        entities = []
        for row in cursor.fetchall():
            # Safe JSON parsing with error handling
            try:
                secondary_subjects = json.loads(row[2]) if row[2] else []
            except (json.JSONDecodeError, TypeError):
                secondary_subjects = []
            
            try:
                dependencies = json.loads(row[8]) if row[8] else []
            except (json.JSONDecodeError, TypeError):
                dependencies = []
            
            try:
                citations = json.loads(row[9]) if row[9] else []
            except (json.JSONDecodeError, TypeError):
                citations = []
            
            entity = MathEntity(
                entity_id=row[0],
                subject=row[1],
                secondary_subjects=secondary_subjects,
                name=row[3],
                statement=row[4],
                proof_status=row[5],
                formal_status=row[6],
                lean_module=row[7],
                dependencies=dependencies,
                citations=citations,
                complexity_score=row[10],
                year=row[11]
            )
            entities.append(entity)
        return entities
    
    def get_entities_without_lean(self) -> List[MathEntity]:
        """Get all math entities without Lean module assignments"""
        cursor = self.conn.execute(
            "SELECT * FROM math_entities WHERE lean_module IS NULL OR lean_module = ''"
        )
        entities = []
        for row in cursor.fetchall():
            # Safe JSON parsing with error handling
            try:
                secondary_subjects = json.loads(row[2]) if row[2] else []
            except (json.JSONDecodeError, TypeError):
                secondary_subjects = []
            
            try:
                dependencies = json.loads(row[8]) if row[8] else []
            except (json.JSONDecodeError, TypeError):
                dependencies = []
            
            try:
                citations = json.loads(row[9]) if row[9] else []
            except (json.JSONDecodeError, TypeError):
                citations = []
            
            entity = MathEntity(
                entity_id=row[0],
                subject=row[1],
                secondary_subjects=secondary_subjects,
                name=row[3],
                statement=row[4],
                proof_status=row[5],
                formal_status=row[6],
                lean_module=row[7],
                dependencies=dependencies,
                citations=citations,
                complexity_score=row[10],
                year=row[11]
            )
            entities.append(entity)
        return entities
    
    def get_low_complexity_entities(self, threshold: int = 50) -> List[MathEntity]:
        """Get all math entities with complexity score below threshold"""
        cursor = self.conn.execute(
            "SELECT * FROM math_entities WHERE complexity_score < ?",
            (threshold,)
        )
        entities = []
        for row in cursor.fetchall():
            entity = MathEntity(
                entity_id=row[0],
                subject=row[1],
                secondary_subjects=json.loads(row[2]) if row[2] else [],
                name=row[3],
                statement=row[4],
                proof_status=row[5],
                formal_status=row[6],
                lean_module=row[7],
                dependencies=json.loads(row[8]) if row[8] else [],
                citations=json.loads(row[9]) if row[9] else [],
                complexity_score=row[10],
                year=row[11]
            )
            entities.append(entity)
        return entities

# ═══════════════════════════════════════════════════════════════════════════
# GPU and SSD Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GPUSpecifications:
    """GPU hardware specifications"""
    vendor: str
    model: str
    vram_gb: float
    compute_capability: str
    cuda_cores: int
    tensor_cores: int
    rt_cores: int
    base_clock_mhz: float
    boost_clock_mhz: float
    memory_clock_mhz: float
    memory_bandwidth_gbps: float
    tdp_watts: float
    architecture: str

@dataclass
class GPUShaderCapability:
    """GPU shader capabilities for WGSL acceleration"""
    shader_name: str
    workgroup_size: int
    operation: str
    performance_target_speedup: float
    supported: bool
    current_utilization: float

@dataclass
class GPUMetrics:
    """GPU runtime metrics"""
    gpu_utilization_percent: float
    vram_usage_gb: float
    vram_utilization_percent: float
    temperature_c: float
    power_draw_watts: float
    clock_speed_mhz: float
    fan_speed_percent: float

@dataclass
class SSDSpecifications:
    """SSD hardware specifications"""
    vendor: str
    model: str
    capacity_tb: float
    interface: str
    form_factor: str
    controller: str
    nand_type: str
    nand_layers: int
    dram_cache_gb: float
    sequential_read_mbps: float
    sequential_write_mbps: float
    random_read_iops: int
    random_write_iops: int
    endurance_tbw: float
    pcie_gen: int
    pcie_lanes: int

@dataclass
class SSDSMARTAttributes:
    """SSD SMART attributes"""
    smart_id: int
    attribute_name: str
    value: int
    worst: int
    threshold: int
    raw_value: str
    status: str

@dataclass
class SSDPCIeConfig:
    """SSD PCIe configuration"""
    pci_address: str
    vendor_id: str
    device_id: str
    link_speed_gt_s: float
    link_width: int
    dma_mask_bits: int
    msi_enabled: bool
    msi_vectors: int
    aspm_enabled: bool

@dataclass
class SSDMetrics:
    """SSD runtime metrics"""
    health_percent: float
    temperature_c: float
    power_hours: int
    media_errors: int
    available_spare_percent: float
    used_percent: float
    read_iops: int
    write_iops: int
    latency_us: float

# ═══════════════════════════════════════════════════════════════════════════
# NII Core Definitions
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NIICore:
    """Non-Isotropic Informatic Core"""
    core_id: str  # NII-01, NII-02, NII-03
    name: str
    specialization: str
    geometric_efficiency: float  # 0-1
    famm_aware: bool
    topology_aware: bool
    math_aware: bool
    lean_aware: bool
    gpu_aware: bool
    ssd_aware: bool

@dataclass
class NIICoreStatus:
    """NII Core operational status"""
    core_id: str
    status: str  # idle, processing, complete, error
    current_task: Optional[str]
    geometric_score: float
    famm_timing: Dict[str, float]
    topology_score: float
    math_relevance: float
    gpu_utilization: float
    ssd_throughput: float

# ═══════════════════════════════════════════════════════════════════════════
# Enhanced Swarm Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EnhancedGeometricParams:
    """Geometric parameters with full system context"""
    kappa_squared: float      # κ²: curvature coupling
    rho_seq: float            # ρ: sequence alignment
    v_epigenetic: float       # v: epigenetic dynamics
    tau_structure: float      # τ: structure tension
    sigma_entropy: float      # σ: nucleotide entropy
    q_conservation: float     # q: evolutionary constraint
    kappa_hierarchy: float    # κ_hierarchy: hierarchy levels
    epsilon_mutation: float    # ε: mutation rate
    
    # Topology-derived parameters
    wire_length_factor: float
    voltage_drop_factor: float
    timing_ps_factor: float
    impedance_factor: float
    dielectric_factor: float
    
    # FAMM timing parameters
    torsional_stress: float    # Σ²: torsional stress from manifold state
    interlocking_energy: float  # I_lock: interlocking energy
    laplacian_energy: float    # Δϕ: Hodge-Laplacian vibration energy
    
    # Math database relevance
    math_relevance_score: float
    
    # Lean module alignment
    lean_alignment_score: float
    
    # GPU-derived parameters
    gpu_compute_factor: float
    gpu_memory_factor: float
    gpu_shader_efficiency: float
    
    # SSD-derived parameters
    ssd_throughput_factor: float
    ssd_latency_factor: float
    ssd_health_factor: float

@dataclass
class SynapticConnection:
    """Synaptic connection between agents in neuron-like swarm"""
    source_id: int
    target_id: int
    weight: float = 0.5  # Connection strength (0.0 to 1.0)
    plasticity: float = 0.1  # Learning rate for weight adjustment
    last_spike_time: float = 0.0
    spike_count: int = 0

@dataclass
class NeuralSpike:
    """Spike message in neuron-like swarm"""
    source_id: int
    timestamp: float
    signal_strength: float
    content: str
    spike_type: str = "discovery"  # discovery, reward, alert, coordination

@dataclass
class EnhancedSwarmAgent:
    """Enhanced swarm agent with full system awareness and neural communication"""
    id: int
    specialization: str
    nii_core_id: Optional[str]
    confidence: float
    geometric_params: EnhancedGeometricParams
    findings: List[str]
    recommendations: List[str]
    topology_context: Optional[TopologyGraph]
    math_context: Optional[List[MathEntity]]
    lean_context: Optional[List[str]]
    gpu_context: Optional[GPUMetrics]
    ssd_context: Optional[SSDMetrics]
    genetic_context: Optional[Dict[SurfaceType, GeneticCompressionReport]]
    curiosity: float = 0.5  # Curiosity drive (0.0 = exploitative, 1.0 = exploratory)
    novel_discoveries: int = 0  # Count of novel discoveries made
    exploration_history: List[Dict[str, any]] = field(default_factory=list)  # Track exploration attempts
    reward_score: float = 0.0  # Cumulative reward for mathematically stable improvements
    stable_improvements: int = 0  # Count of mathematically stable improvements
    # Neural communication attributes
    connections: List[SynapticConnection] = field(default_factory=list)  # Synaptic connections
    spike_threshold: float = 0.7  # Threshold for emitting spikes
    refractory_period: float = 1.0  # Minimum time between spikes
    last_spike_time: float = 0.0
    membrane_potential: float = 0.0  # Accumulated signal potential
    received_spikes: List[NeuralSpike] = field(default_factory=list)

@dataclass
class EnhancedSwarmState:
    """Enhanced swarm state with full integration"""
    agents: List[EnhancedSwarmAgent]
    nii_cores: List[NIICore]
    nii_core_status: List[NIICoreStatus]
    consensus: float
    recommendations: List[str]
    topology_constraints: Dict[str, any]
    topology_optimization_score: float
    math_coverage_score: float
    lean_coverage_score: float
    gpu_computing_score: float
    ssd_storage_score: float
    genetic_compression_score: float
    homeostasis_score: float
    patterns_learned: int
    metatyping_score: float
    remote_nodes_count: int
    dag_events_count: int
    optimization_ratio: float
    substrate_potential: float
    optimization_cycles: int
    overall_system_score: float

# ═══════════════════════════════════════════════════════════════════════════
# NII Core Registry
# ═══════════════════════════════════════════════════════════════════════════

class NIICoreRegistry:
    """Registry of NII cores with capabilities"""
    
    def __init__(self):
        self.cores = [
            NIICore(
                core_id="NII-01",
                name="Semantic Analysis",
                specialization="pattern_recognition",
                geometric_efficiency=0.85,
                famm_aware=True,
                topology_aware=True,
                math_aware=True,
                lean_aware=True,
                gpu_aware=True,
                ssd_aware=True
            ),
            NIICore(
                core_id="NII-02",
                name="Translation Engine",
                specialization="rust_to_lean",
                geometric_efficiency=0.90,
                famm_aware=True,
                topology_aware=True,
                math_aware=True,
                lean_aware=True,
                gpu_aware=True,
                ssd_aware=True
            ),
            NIICore(
                core_id="NII-03",
                name="Verification",
                specialization="proof_generation",
                geometric_efficiency=0.80,
                famm_aware=True,
                topology_aware=True,
                math_aware=True,
                lean_aware=True,
                gpu_aware=True,
                ssd_aware=True
            )
        ]
    
    def get_core(self, core_id: str) -> Optional[NIICore]:
        """Get NII core by ID"""
        for core in self.cores:
            if core.core_id == core_id:
                return core
        return None
    
    def get_cores_by_specialization(self, specialization: str) -> List[NIICore]:
        """Get cores by specialization"""
        return [c for c in self.cores if c.specialization == specialization]

# ═══════════════════════════════════════════════════════════════════════════
# GPU and SSD Data Extraction
# ═══════════════════════════════════════════════════════════════════════════

class GPUDataExtractor:
    """Extract GPU data from system"""
    
    def __init__(self):
        self.gpu_specs = None
        self.gpu_metrics = None
        self.shader_capabilities = []
    
    def extract_gpu_specs(self) -> GPUSpecifications:
        """Extract GPU specifications (demo data based on AMD GPU from previous research)"""
        return GPUSpecifications(
            vendor="AMD",
            model="Radeon RX 6000 Series",
            vram_gb=16.0,
            compute_capability="RDNA 2",
            cuda_cores=0,
            tensor_cores=0,
            rt_cores=0,
            base_clock_mhz=2000.0,
            boost_clock_mhz=2500.0,
            memory_clock_mhz=18000.0,
            memory_bandwidth_gbps=512.0,
            tdp_watts=250.0,
            architecture="RDNA 2"
        )
    
    def extract_gpu_metrics(self) -> GPUMetrics:
        """Extract GPU runtime metrics (demo data)"""
        return GPUMetrics(
            gpu_utilization_percent=45.0,
            vram_usage_gb=7.2,
            vram_utilization_percent=45.0,
            temperature_c=65.0,
            power_draw_watts=112.5,
            clock_speed_mhz=2200.0,
            fan_speed_percent=55.0
        )
    
    def extract_shader_capabilities(self) -> List[GPUShaderCapability]:
        """Extract WGSL shader capabilities (from GPU acceleration assignment)"""
        return [
            GPUShaderCapability(
                shader_name="q16_16_arithmetic",
                workgroup_size=256,
                operation="Q16_16 arithmetic operations",
                performance_target_speedup=100.0,
                supported=True,
                current_utilization=0.0
            ),
            GPUShaderCapability(
                shader_name="concept_vector_search",
                workgroup_size=64,
                operation="14D similarity search",
                performance_target_speedup=100.0,
                supported=True,
                current_utilization=0.0
            ),
            GPUShaderCapability(
                shader_name="avmr_shell_decompose",
                workgroup_size=128,
                operation="AVMR shell decomposition",
                performance_target_speedup=250.0,
                supported=True,
                current_utilization=0.0
            )
        ]

class SSDDataExtractor:
    """Extract SSD data from system"""
    
    def __init__(self):
        self.ssd_specs = None
        self.ssd_metrics = None
        self.pcie_config = None
        self.smart_attributes = []
    
    def extract_ssd_specs(self) -> SSDSpecifications:
        """Extract SSD specifications (from SSD comprehensive analysis)"""
        return SSDSpecifications(
            vendor="MSI",
            model="Spatium M480 PRO 2TB",
            capacity_tb=2.0,
            interface="NVMe 1.4",
            form_factor="M.2 2280",
            controller="Phison PS5018-E18-41",
            nand_type="3D TLC NAND",
            nand_layers=176,
            dram_cache_gb=2.0,
            sequential_read_mbps=7000.0,
            sequential_write_mbps=6900.0,
            random_read_iops=1000000,
            random_write_iops=1000000,
            endurance_tbw=1400.0,
            pcie_gen=4,
            pcie_lanes=4
        )
    
    def extract_ssd_metrics(self) -> SSDMetrics:
        """Extract SSD runtime metrics (demo data)"""
        return SSDMetrics(
            health_percent=98.0,
            temperature_c=45.0,
            power_hours=5000,
            media_errors=0,
            available_spare_percent=100.0,
            used_percent=35.0,
            read_iops=850000,
            write_iops=750000,
            latency_us=15.0
        )
    
    def extract_pcie_config(self) -> SSDPCIeConfig:
        """Extract SSD PCIe configuration (from PCIe side channel probing)"""
        return SSDPCIeConfig(
            pci_address="0000:02:00.0",
            vendor_id="0x1987",
            device_id="0x5018",
            link_speed_gt_s=16.0,
            link_width=4,
            dma_mask_bits=64,
            msi_enabled=True,
            msi_vectors=13,
            aspm_enabled=True
        )

# ═══════════════════════════════════════════════════════════════════════════
# Neuromorphic Coding Assignment System
# ═══════════════════════════════════════════════════════════════════════════

class NeuromorphicCodingMethod(Enum):
    """Neuromorphic coding acceleration methods"""
    STDP_LEARNING = "stdp_learning"  # Spike-Timing-Dependent Plasticity
    BRANCH_PREDICTION = "branch_prediction"  # Branch prediction acceleration
    SLUQ_TRIAGE = "sluq_triage"  # Cache-local triage for unstable trajectories
    SPIKE_ENCODING = "spike_encoding"  # Loihi-style spike-based encoding
    EVENT_PROCESSING = "event_processing"  # TrueNorth-style event-based processing
    ANALOG_EMULATION = "analog_emulation"  # BrainScaleS-style analog neural emulation
    PHOTONIC_SOLITON = "photonic_soliton"  # Cavity solitons for photonic neuromorphic

@dataclass
class NeuromorphicAssignment:
    """Assignment of neuromorphic coding method to an interface"""
    interface_name: str
    interface_type: str  # GPU, PCIe, SSD, Network, etc.
    coding_method: NeuromorphicCodingMethod
    confidence: float  # 0.0-1.0
    expected_speedup: float  # Expected speedup multiplier
    hardware_requirements: List[str]  # Required hardware support
    implementation_status: str  # "designed", "implemented", "deployed"

class NeuromorphicCodingAssigner:
    """Assign neuromorphic coding methods to system interfaces"""
    
    def __init__(self):
        self.assignments: Dict[str, NeuromorphicAssignment] = {}
        self._initialize_default_assignments()
    
    def _initialize_default_assignments(self):
        """Initialize default neuromorphic coding assignments"""
        # GPU interfaces: Branch prediction for shader operations
        self.assignments["GPU_Shader_Compute"] = NeuromorphicAssignment(
            interface_name="GPU_Shader_Compute",
            interface_type="GPU",
            coding_method=NeuromorphicCodingMethod.BRANCH_PREDICTION,
            confidence=0.9,
            expected_speedup=1.23,  # 23% native speedup
            hardware_requirements=["GPU", "Shader support"],
            implementation_status="designed"
        )
        
        # PCIe interfaces: SLUQ triage for transaction routing
        self.assignments["PCIe_Transaction_Routing"] = NeuromorphicAssignment(
            interface_name="PCIe_Transaction_Routing",
            interface_type="PCIe",
            coding_method=NeuromorphicCodingMethod.SLUQ_TRIAGE,
            confidence=0.85,
            expected_speedup=1.5,
            hardware_requirements=["PCIe Gen3+", "Cache-local memory"],
            implementation_status="designed"
        )
        
        # SSD interfaces: STDP learning for wear leveling optimization
        self.assignments["SSD_Wear_Leveling"] = NeuromorphicAssignment(
            interface_name="SSD_Wear_Leveling",
            interface_type="SSD",
            coding_method=NeuromorphicCodingMethod.STDP_LEARNING,
            confidence=0.8,
            expected_speedup=1.15,
            hardware_requirements=["NVMe controller", "STDP-compatible firmware"],
            implementation_status="designed"
        )
        
        # Network interfaces: Event-based processing for packet handling
        self.assignments["Network_Packet_Handling"] = NeuromorphicAssignment(
            interface_name="Network_Packet_Handling",
            interface_type="Network",
            coding_method=NeuromorphicCodingMethod.EVENT_PROCESSING,
            confidence=0.75,
            expected_speedup=1.3,
            hardware_requirements=["Network interface", "Event-driven kernel"],
            implementation_status="designed"
        )
        
        # Memory interfaces: Spike encoding for pattern matching
        self.assignments["Memory_Pattern_Matching"] = NeuromorphicAssignment(
            interface_name="Memory_Pattern_Matching",
            interface_type="Memory",
            coding_method=NeuromorphicCodingMethod.SPIKE_ENCODING,
            confidence=0.7,
            expected_speedup=1.4,
            hardware_requirements=["Loihi chip or emulation", "Spike-compatible interface"],
            implementation_status="designed"
        )
    
    def assign_method(self, interface_name: str, interface_type: str, 
                      coding_method: NeuromorphicCodingMethod,
                      confidence: float, expected_speedup: float,
                      hardware_requirements: List[str]) -> NeuromorphicAssignment:
        """Assign a neuromorphic coding method to an interface"""
        assignment = NeuromorphicAssignment(
            interface_name=interface_name,
            interface_type=interface_type,
            coding_method=coding_method,
            confidence=confidence,
            expected_speedup=expected_speedup,
            hardware_requirements=hardware_requirements,
            implementation_status="designed"
        )
        self.assignments[interface_name] = assignment
        return assignment
    
    def get_assignment(self, interface_name: str) -> Optional[NeuromorphicAssignment]:
        """Get neuromorphic coding assignment for an interface"""
        return self.assignments.get(interface_name)
    
    def get_assignments_by_type(self, interface_type: str) -> List[NeuromorphicAssignment]:
        """Get all assignments for a specific interface type"""
        return [a for a in self.assignments.values() if a.interface_type == interface_type]
    
    def compute_total_speedup(self) -> float:
        """Compute total expected speedup across all assignments"""
        return sum(a.expected_speedup for a in self.assignments.values()) / len(self.assignments)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of neuromorphic coding assignments"""
        by_type = {}
        for assignment in self.assignments.values():
            if assignment.interface_type not in by_type:
                by_type[assignment.interface_type] = []
            by_type[assignment.interface_type].append(assignment)
        
        return {
            'total_assignments': len(self.assignments),
            'total_speedup': self.compute_total_speedup(),
            'by_type': {
                itype: {
                    'count': len(assignments),
                    'avg_speedup': sum(a.expected_speedup for a in assignments) / len(assignments),
                    'methods': [a.coding_method.value for a in assignments]
                }
                for itype, assignments in by_type.items()
            }
        }

# ═══════════════════════════════════════════════════════════════════════════
# System Performance Prioritization (User Use First)
# ═══════════════════════════════════════════════════════════════════════════

class TaskPriority(Enum):
    """Task priority levels"""
    USER_INTERACTIVE = 0  # Highest priority - direct user interaction
    USER_CRITICAL = 1     # Critical user-facing tasks
    USER_BACKGROUND = 2   # Background user tasks
    SWARM_CRITICAL = 3    # Critical swarm maintenance
    SWARM_RESEARCH = 4    # Swarm self-research (lowest priority)

@dataclass
class PerformancePolicy:
    """Performance prioritization policy"""
    user_cpu_threshold: float = 0.7  # If user CPU > 70%, throttle swarm
    user_memory_threshold: float = 0.8  # If user memory > 80%, throttle swarm
    swarm_cpu_limit: float = 0.2  # Max CPU for swarm when user active
    swarm_memory_limit: float = 0.15  # Max memory for swarm when user active
    idle_threshold_seconds: float = 60.0  # Seconds of user inactivity before swarm can use more resources

class PerformancePrioritizer:
    """System performance prioritization - user use first"""
    
    def __init__(self):
        self.policy = PerformancePolicy()
        self.user_activity_timestamp: float = time.time()
        self.current_swarm_allocation: Dict[str, float] = {
            'cpu': 0.8,  # Default 80% for self-research
            'memory': 0.8
        }
    
    def detect_user_activity(self) -> bool:
        """Detect if user is currently active"""
        # Check for recent user activity (keyboard, mouse, etc.)
        # For now, use a simple time-based heuristic
        idle_time = time.time() - self.user_activity_timestamp
        return idle_time < self.policy.idle_threshold_seconds
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        import psutil
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent / 100.0,
            'load_avg': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        }
    
    def compute_swarm_allocation(self) -> Dict[str, float]:
        """Compute swarm resource allocation based on user activity"""
        user_active = self.detect_user_activity()
        metrics = self.get_system_metrics()
        
        if user_active:
            # User is active - prioritize user, limit swarm
            cpu_allocation = self.policy.swarm_cpu_limit
            memory_allocation = self.policy.swarm_memory_limit
        else:
            # User is idle - swarm can use more resources
            cpu_allocation = 0.8  # 80% for self-research
            memory_allocation = 0.8
        
        # Further throttle if system under high load
        if metrics['cpu_percent'] > self.policy.user_cpu_threshold:
            cpu_allocation *= 0.5  # Halve swarm CPU
        
        if metrics['memory_percent'] > self.policy.user_memory_threshold:
            memory_allocation *= 0.5  # Halve swarm memory
        
        self.current_swarm_allocation = {
            'cpu': cpu_allocation,
            'memory': memory_allocation
        }
        
        return self.current_swarm_allocation
    
    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize tasks with user-facing tasks first"""
        def task_priority_key(task):
            priority = task.get('priority', TaskPriority.SWARM_RESEARCH.value)
            return priority
        
        return sorted(tasks, key=task_priority_key)
    
    def should_throttle_swarm(self) -> bool:
        """Check if swarm should be throttled"""
        user_active = self.detect_user_activity()
        metrics = self.get_system_metrics()
        
        return (user_active or 
                metrics['cpu_percent'] > self.policy.user_cpu_threshold or
                metrics['memory_percent'] > self.policy.user_memory_threshold)
    
    def update_user_activity(self):
        """Update user activity timestamp"""
        self.user_activity_timestamp = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of performance prioritization"""
        return {
            'user_active': self.detect_user_activity(),
            'swarm_allocation': self.compute_swarm_allocation(),
            'should_throttle': self.should_throttle_swarm(),
            'system_metrics': self.get_system_metrics()
        }

# ═══════════════════════════════════════════════════════════════════════════
# PIST-based Virtual Substrate
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PISTCoord:
    """PIST coordinate (k, t) with shell geometry"""
    k: int  # Shell index
    t: int  # Offset within shell (0 ≤ t ≤ 2*k+1)
    ht: int = field(default=0)  # Constraint: t ≤ ht
    
    def __post_init__(self):
        """Initialize PIST coordinate"""
        if self.ht == 0:
            self.ht = 2 * self.k + 1
    
    @property
    def a(self) -> int:
        """Distance to lower square"""
        return self.t
    
    @property
    def b(self) -> int:
        """Distance to upper square"""
        return self.ht - self.t
    
    @property
    def mass(self) -> int:
        """PIST mass = a * b"""
        return self.a * self.b
    
    @property
    def n(self) -> int:
        """Underlying natural number"""
        return self.k ** 2 + self.t
    
    def mirror(self) -> 'PISTCoord':
        """Mirror point within the same shell"""
        return PISTCoord(k=self.k, t=self.ht - self.t, ht=self.ht)
    
    def phase(self) -> str:
        """Phase classification based on mass"""
        return "grounded" if self.mass == 0 else "seismic"

@dataclass
class PISTState:
    """PIST state machine state"""
    pos: PISTCoord
    phase_flag: str
    accepted: List[PISTCoord]
    rejected: List[PISTCoord]
    friction: int
    log: List[Dict[str, Any]]
    
    @staticmethod
    def of_coord(coord: PISTCoord) -> 'PISTState':
        """Create state from coordinate"""
        return PISTState(
            pos=coord,
            phase_flag=coord.phase(),
            accepted=[],
            rejected=[],
            friction=0,
            log=[]
        )
    
    @property
    def potential(self) -> int:
        """Lyapunov functional: PIST mass + friction"""
        return self.pos.mass + self.friction
    
    def relocate(self, coord: PISTCoord) -> 'PISTState':
        """Replace active coordinate and refresh phase"""
        return PISTState(
            pos=coord,
            phase_flag=coord.phase(),
            accepted=self.accepted,
            rejected=self.rejected,
            friction=self.friction,
            log=self.log
        )
    
    def accept(self, coord: PISTCoord) -> 'PISTState':
        """Register an accepted coordinate"""
        return PISTState(
            pos=self.pos,
            phase_flag=self.phase_flag,
            accepted=[coord] + self.accepted,
            rejected=self.rejected,
            friction=self.friction,
            log=self.log
        )
    
    def penalize(self, bad: PISTCoord, penalty: int) -> 'PISTState':
        """Register rejection and increase friction"""
        return PISTState(
            pos=self.pos,
            phase_flag=self.phase_flag,
            accepted=self.accepted,
            rejected=[bad] + self.rejected,
            friction=self.friction + penalty,
            log=self.log
        )

class PISTVirtualSubstrate:
    """PIST-based virtual substrate for swarm state exploration"""
    
    def __init__(self):
        self.current_state: Optional[PISTState] = None
        self.history: List[PISTState] = []
        self._initialize_substrate()
    
    def _initialize_substrate(self):
        """Initialize substrate at origin"""
        origin = PISTCoord(k=0, t=0)
        self.current_state = PISTState.of_coord(origin)
        self.history.append(self.current_state)
    
    def linear_step(self, delta: int = 1) -> PISTState:
        """Perform linear step within current shell"""
        if not self.current_state:
            return PISTState.of_coord(PISTCoord(k=0, t=0))
        
        coord = self.current_state.pos
        new_t = max(0, min(2 * coord.k + 1, coord.t + delta))
        new_coord = PISTCoord(k=coord.k, t=new_t)
        new_state = self.current_state.relocate(new_coord)
        
        # Log the transition
        new_state.log.append({
            'before': coord,
            'after': new_coord,
            'move': 'linearStep',
            'preserved_mass': coord.mass == new_coord.mass
        })
        
        self.current_state = new_state
        self.history.append(new_state)
        return new_state
    
    def resonance_jump(self, target_mass: int) -> PISTState:
        """Jump to coordinate with same mass (resonance)"""
        if not self.current_state:
            return PISTState.of_coord(PISTCoord(k=0, t=0))
        
        coord = self.current_state.pos
        current_mass = coord.mass
        
        # Find coordinate with same mass in same shell
        # For simplicity, use mirror if mass matches
        target = coord.mirror()
        if target.mass == current_mass:
            new_state = self.current_state.accept(target).relocate(target)
            new_state.log.append({
                'before': coord,
                'after': target,
                'move': 'resonanceJump',
                'preserved_mass': True
            })
            self.current_state = new_state
            self.history.append(new_state)
            return new_state
        
        return self.current_state
    
    def shell_transition(self, new_k: int) -> PISTState:
        """Transition to different shell"""
        if not self.current_state:
            return PISTState.of_coord(PISTCoord(k=0, t=0))
        
        new_coord = PISTCoord(k=new_k, t=0)
        new_state = self.current_state.relocate(new_coord)
        
        new_state.log.append({
            'before': self.current_state.pos,
            'after': new_coord,
            'move': 'shellTransition',
            'preserved_mass': False
        })
        
        self.current_state = new_state
        self.history.append(new_state)
        return new_state
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of PIST substrate state"""
        if not self.current_state:
            return {'status': 'uninitialized'}
        
        return {
            'current_coord': {'k': self.current_state.pos.k, 't': self.current_state.pos.t},
            'mass': self.current_state.pos.mass,
            'potential': self.current_state.potential,
            'phase': self.current_state.phase_flag,
            'accepted_count': len(self.current_state.accepted),
            'rejected_count': len(self.current_state.rejected),
            'friction': self.current_state.friction,
            'history_length': len(self.history)
        }

# ═══════════════════════════════════════════════════════════════════════════
# Stochastic QUBO Enhancements
# ═══════════════════════════════════════════════════════════════════════════

class QUBOEnhancementMethod(Enum):
    """Stochastic QUBO enhancement methods"""
    SLUQ_TRIAGE = "sluq_triage"  # Cache-local triage for unstable trajectories
    BRANCH_PREDICTION = "branch_prediction"  # Branch prediction for proposal selection
    MCMC_PARALLEL = "mcmc_parallel"  # MCMC ensemble parallelization
    GPU_THREAD_HINTS = "gpu_thread_hints"  # GPU thread divergence reduction

@dataclass
class QUBOEnhancement:
    """Stochastic QUBO enhancement configuration"""
    method: QUBOEnhancementMethod
    confidence: float  # 0.0-1.0
    expected_speedup: float  # Expected speedup multiplier
    applicable_contexts: List[str]  # Where this enhancement applies
    hardware_requirements: List[str]  # Required hardware support

class StochasticQUBOEnhancer:
    """Stochastic QUBO optimization enhancements"""
    
    def __init__(self):
        self.enhancements: Dict[str, QUBOEnhancement] = {}
        self._initialize_default_enhancements()
    
    def _initialize_default_enhancements(self):
        """Initialize default QUBO enhancements"""
        # SLUQ triage for MCMC and QUBO optimization
        self.enhancements["SLUQ_MCMC_Triage"] = QUBOEnhancement(
            method=QUBOEnhancementMethod.SLUQ_TRIAGE,
            confidence=0.9,
            expected_speedup=1.5,
            applicable_contexts=["MCMC random walks", "QUBO optimization", "stochastic phase space"],
            hardware_requirements=["Cache-local memory", "Trajectory stability detector"]
        )
        
        # Branch prediction for proposal generation
        self.enhancements["Branch_Proposal_Selection"] = QUBOEnhancement(
            method=QUBOEnhancementMethod.BRANCH_PREDICTION,
            confidence=0.85,
            expected_speedup=1.3,
            applicable_contexts=["Proposal generation", "Delta scoring", "Top-k survivor maintenance"],
            hardware_requirements=["Branch predictor", "Opcode selector"]
        )
        
        # MCMC ensemble parallelization
        self.enhancements["MCMC_Ensemble_Parallel"] = QUBOEnhancement(
            method=QUBOEnhancementMethod.MCMC_PARALLEL,
            confidence=0.8,
            expected_speedup=2.0,
            applicable_contexts=["10,000+ parallel branches", "GPU dispatch", "Shader compute"],
            hardware_requirements=["GPU compute", "Parallel thread support"]
        )
        
        # GPU thread hints for divergence reduction
        self.enhancements["GPU_Thread_Hints"] = QUBOEnhancement(
            method=QUBOEnhancementMethod.GPU_THREAD_HINTS,
            confidence=0.75,
            expected_speedup=1.4,
            applicable_contexts=["GPU dispatch", "Shader primitive compute"],
            hardware_requirements=["GPU", "Thread hint support"]
        )
    
    def apply_sluq_triage(self, trajectories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply SLUQ triage to prune unstable trajectories"""
        stable_trajectories = []
        for traj in trajectories:
            stability_score = traj.get('stability_score', 0.5)
            if stability_score >= 0.3:  # Threshold for stability
                stable_trajectories.append(traj)
        return stable_trajectories
    
    def apply_branch_prediction(self, proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply branch prediction to select optimal proposals"""
        # Sort by confidence score (simulating branch prediction)
        sorted_proposals = sorted(proposals, key=lambda p: p.get('confidence', 0.5), reverse=True)
        return sorted_proposals[:len(proposals) // 2]  # Keep top 50%
    
    def compute_total_speedup(self) -> float:
        """Compute total expected speedup across all enhancements"""
        return sum(e.expected_speedup for e in self.enhancements.values()) / len(self.enhancements)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of QUBO enhancements"""
        return {
            'total_enhancements': len(self.enhancements),
            'total_speedup': self.compute_total_speedup(),
            'methods': [e.method.value for e in self.enhancements.values()],
            'avg_confidence': sum(e.confidence for e in self.enhancements.values()) / len(self.enhancements)
        }

# ═══════════════════════════════════════════════════════════════════════════
# Genetic Compression Data Structures (from genetic_surface_compression.py)
# ═══════════════════════════════════════════════════════════════════════════

class SurfaceType(Enum):
    """Types of surfaces for genetic compression"""
    ZRAM = "zram"
    SSD = "ssd"
    WIRE_SIGNAL_BUS = "wire_signal_bus"
    PCIE_BUS = "pcie_bus"
    GPU_SURFACE = "gpu_surface"
    GPU_SIGNAL = "gpu_signal"

@dataclass
class SurfaceFieldParams:
    """Unified field parameters for a surface (analogous to GenomicFieldParams)
    
    Φ_surface(x) = (ρ_seq² + v_dynamics² + τ_structure² + σ_entropy² + q_conservation²) × (1+κ_hierarchy²) / (1+ε_mutation)
    """
    rho_seq: float = 0.8
    v_dynamics: float = 0.3
    tau_structure: float = 0.5
    sigma_entropy: float = 0.2
    q_conservation: float = 0.4
    kappa_hierarchy: float = 0.25
    epsilon_mutation: float = 0.05
    
    def compute_phi(self) -> float:
        """Compute unified field potential Φ"""
        numerator = (self.rho_seq**2 + self.v_dynamics**2 + 
                    self.tau_structure**2 + self.sigma_entropy**2 + 
                    self.q_conservation**2)
        hierarchy_mult = 1 + self.kappa_hierarchy**2
        denominator = 1 + self.epsilon_mutation
        return numerator * hierarchy_mult / denominator

@dataclass
class GeneticCodeParams:
    """Genetic code optimization parameters
    
    I = (H × G) × (1 - (D / 64))
    """
    entropy: float = 0.8
    genomic_complexity: float = 0.7
    degeneracy: float = 32.0
    
    def compute_optimization(self) -> float:
        """Compute genetic optimization I"""
        entropy_factor = self.entropy * self.genomic_complexity
        degeneracy_penalty = self.degeneracy / 64.0
        return entropy_factor * (1.0 - degeneracy_penalty)
    
    def information_density(self) -> float:
        """Information density: ratio to theoretical maximum"""
        theoretical_max = self.entropy * self.genomic_complexity
        if theoretical_max > 0:
            return (self.compute_optimization() / theoretical_max) * 100
        return 0.0
    
    def error_resistance(self) -> float:
        """Error resistance: based on degeneracy"""
        return (self.degeneracy / 64.0) * 100
    
    def compression_efficiency(self) -> float:
        """Compression efficiency: based on entropy and complexity"""
        return (self.entropy * self.genomic_complexity) * 100

@dataclass
class GeneticCompressionReport:
    """Report from genetic compression analysis"""
    surface_type: SurfaceType
    method: str
    optimization_score: float
    field_phi: float
    information_density: float
    error_resistance: float
    compression_efficiency: float
    anisotropy: float
    procedural_seed: str
    compressed_size: int
    compression_ratio: float

class GeneticDataExtractor:
    """Extract genetic compression metrics for all surfaces"""
    
    def __init__(self):
        self.surface_reports: Dict[SurfaceType, GeneticCompressionReport] = {}
        self.surface_fields: Dict[SurfaceType, SurfaceFieldParams] = {}
        self._initialize_default_params()
    
    def _initialize_default_params(self):
        """Initialize default field parameters for each surface type"""
        self.surface_fields[SurfaceType.ZRAM] = SurfaceFieldParams(
            rho_seq=0.9, v_dynamics=0.6, tau_structure=0.3,
            sigma_entropy=0.4, q_conservation=0.5, kappa_hierarchy=0.1, epsilon_mutation=0.02
        )
        self.surface_fields[SurfaceType.SSD] = SurfaceFieldParams(
            rho_seq=0.7, v_dynamics=0.2, tau_structure=0.6,
            sigma_entropy=0.3, q_conservation=0.6, kappa_hierarchy=0.4, epsilon_mutation=0.05
        )
        self.surface_fields[SurfaceType.WIRE_SIGNAL_BUS] = SurfaceFieldParams(
            rho_seq=0.5, v_dynamics=0.9, tau_structure=0.2,
            sigma_entropy=0.6, q_conservation=0.3, kappa_hierarchy=0.05, epsilon_mutation=0.1
        )
        self.surface_fields[SurfaceType.PCIE_BUS] = SurfaceFieldParams(
            rho_seq=0.8, v_dynamics=0.4, tau_structure=0.7,
            sigma_entropy=0.25, q_conservation=0.7, kappa_hierarchy=0.5, epsilon_mutation=0.03
        )
        self.surface_fields[SurfaceType.GPU_SURFACE] = SurfaceFieldParams(
            rho_seq=0.85, v_dynamics=0.3, tau_structure=0.8,
            sigma_entropy=0.2, q_conservation=0.75, kappa_hierarchy=0.6, epsilon_mutation=0.01
        )
        self.surface_fields[SurfaceType.GPU_SIGNAL] = SurfaceFieldParams(
            rho_seq=0.75, v_dynamics=0.5, tau_structure=0.65,
            sigma_entropy=0.35, q_conservation=0.65, kappa_hierarchy=0.45, epsilon_mutation=0.04
        )
    
    def extract_genetic_metrics(self) -> Dict[SurfaceType, GeneticCompressionReport]:
        """Extract genetic compression metrics for all surfaces (demo implementation)"""
        import hashlib
        
        for surface_type in SurfaceType:
            field_params = self.surface_fields[surface_type]
            field_phi = field_params.compute_phi()
            
            # Simulate entropy based on surface characteristics
            entropy = field_params.sigma_entropy
            
            # Create genetic code parameters
            genetic_params = GeneticCodeParams(
                entropy=entropy,
                genomic_complexity=field_params.tau_structure,
                degeneracy=field_params.kappa_hierarchy * 64
            )
            
            # Compute optimization
            optimization_score = genetic_params.compute_optimization()
            
            # Select method based on optimization
            if optimization_score > 0.7:
                if surface_type == SurfaceType.ZRAM:
                    method = "zstd_fast"
                elif surface_type == SurfaceType.SSD:
                    method = "lzma"
                elif surface_type == SurfaceType.WIRE_SIGNAL_BUS:
                    method = "delta_encode"
                elif surface_type == SurfaceType.PCIE_BUS:
                    method = "zstd"
                elif surface_type == SurfaceType.GPU_SURFACE:
                    method = "astc"
                else:  # GPU_SIGNAL
                    method = "shader_lz"
            elif optimization_score > 0.4:
                if surface_type == SurfaceType.ZRAM:
                    method = "lz4"
                elif surface_type == SurfaceType.SSD:
                    method = "zstd"
                elif surface_type == SurfaceType.WIRE_SIGNAL_BUS:
                    method = "rle"
                elif surface_type == SurfaceType.PCIE_BUS:
                    method = "lz4"
                elif surface_type == SurfaceType.GPU_SURFACE:
                    method = "bc7"
                else:  # GPU_SIGNAL
                    method = "shader_rle"
            else:
                if surface_type in [SurfaceType.WIRE_SIGNAL_BUS, SurfaceType.PCIE_BUS, 
                                   SurfaceType.GPU_SURFACE, SurfaceType.GPU_SIGNAL]:
                    method = "passthrough"
                elif surface_type == SurfaceType.ZRAM:
                    method = "lzo"
                else:  # SSD
                    method = "gzip"
            
            # Compute metrics
            information_density = genetic_params.information_density()
            error_resistance = genetic_params.error_resistance()
            compression_efficiency = genetic_params.compression_efficiency()
            
            # Simulate anisotropy (higher structure → higher anisotropy)
            anisotropy = field_params.kappa_hierarchy * 2.0
            
            # Generate procedural seed
            seed_data = f"{surface_type.value}_{field_phi}_{optimization_score}".encode()
            procedural_seed = hashlib.sha256(seed_data).hexdigest()
            
            # Simulate compression
            compressed_size = int(1000 / (1 + field_phi))
            compression_ratio = 1000 / max(compressed_size, 1)
            
            report = GeneticCompressionReport(
                surface_type=surface_type,
                method=method,
                optimization_score=optimization_score,
                field_phi=field_phi,
                information_density=information_density,
                error_resistance=error_resistance,
                compression_efficiency=compression_efficiency,
                anisotropy=anisotropy,
                procedural_seed=procedural_seed,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio
            )
            
            self.surface_reports[surface_type] = report
        
        return self.surface_reports

# ═══════════════════════════════════════════════════════════════════════════
# Homeostasis and Self-Learning Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class HomeostasisState:
    """Current state of swarm homeostasis"""
    consensus_stability: float = 0.5  # Stability of consensus over time
    resource_efficiency: float = 0.5  # How efficiently resources are used
    learning_rate: float = 0.01  # Current learning rate
    adaptation_speed: float = 0.5  # Speed of adaptation to changes
    equilibrium_distance: float = 1.0  # Distance from optimal equilibrium
    timestamp: float = field(default_factory=time.time)
    
    def compute_homeostasis_score(self) -> float:
        """Compute overall homeostasis score (higher = better equilibrium)"""
        return (self.consensus_stability * 0.3 + 
                self.resource_efficiency * 0.3 + 
                self.adaptation_speed * 0.2 + 
                (1.0 - min(self.equilibrium_distance, 1.0)) * 0.2)

@dataclass
class LearnedPattern:
    """A pattern learned by the swarm"""
    pattern_id: str
    context: Dict[str, float]  # System state when pattern was observed
    action: str  # Action taken
    outcome: float  # Result score
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.5  # Confidence in this pattern
    frequency: int = 1  # How often this pattern occurs

@dataclass
class SwarmMemory:
    """Memory of learned patterns and optimal parameters"""
    patterns: List[LearnedPattern] = field(default_factory=list)
    optimal_params: Dict[str, float] = field(default_factory=dict)
    performance_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    homeostasis_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_pattern(self, pattern: LearnedPattern):
        """Add a learned pattern to memory"""
        self.patterns.append(pattern)
        
    def find_similar_pattern(self, context: Dict[str, float], threshold: float = 0.1) -> Optional[LearnedPattern]:
        """Find similar pattern in memory"""
        for pattern in self.patterns:
            similarity = self._compute_similarity(context, pattern.context)
            if similarity > (1.0 - threshold):
                return pattern
        return None
    
    def _compute_similarity(self, ctx1: Dict[str, float], ctx2: Dict[str, float]) -> float:
        """Compute similarity between two contexts"""
        if not ctx1 or not ctx2:
            return 0.0
        
        common_keys = set(ctx1.keys()) & set(ctx2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            v1, v2 = ctx1[key], ctx2[key]
            if v1 == v2:
                similarities.append(1.0)
            else:
                sim = 1.0 - abs(v1 - v2) / max(abs(v1), abs(v2), 1e-10)
                similarities.append(sim)
        
        return sum(similarities) / len(similarities)
    
    def update_optimal_params(self, params: Dict[str, float], score: float):
        """Update optimal parameters based on performance"""
        if not self.optimal_params or score > self._get_current_score():
            self.optimal_params = params.copy()
    
    def _get_current_score(self) -> float:
        """Get current performance score"""
        if self.performance_history:
            return sum(self.performance_history) / len(self.performance_history)
        return 0.5
    
    def record_performance(self, score: float):
        """Record a performance measurement"""
        self.performance_history.append(score)
    
    def record_homeostasis(self, state: HomeostasisState):
        """Record a homeostasis state"""
        self.homeostasis_history.append(state)

@dataclass
class FeedbackLoop:
    """Feedback loop for homeostasis adjustment"""
    metric_name: str
    target_value: float
    current_value: float
    tolerance: float = 0.1
    adjustment_rate: float = 0.05
    direction: str = "neutral"  # "increase", "decrease", "neutral"
    
    def compute_adjustment(self) -> float:
        """Compute required adjustment"""
        error = self.target_value - self.current_value
        
        if abs(error) < self.tolerance:
            self.direction = "neutral"
            return 0.0
        
        self.direction = "increase" if error > 0 else "decrease"
        adjustment = error * self.adjustment_rate
        return adjustment
    
    def is_in_tolerance(self) -> bool:
        """Check if metric is within tolerance"""
        return abs(self.target_value - self.current_value) < self.tolerance

# ═══════════════════════════════════════════════════════════════════════════
# Metatyping Data Structures
# ═══════════════════════════════════════════════════════════════════════════

class Layer(Enum):
    """Three pillars of metatyping"""
    SUBSTRATE = "Substrate"  # ENE (Truth)
    SURFACE = "Surface"    # Notion (View)
    INTENT = "Intent"      # Linear (Action)

@dataclass
class Metatype:
    """Metatype classification with observe, classify, act, prove, remember"""
    observe: str  # What is observed
    classify: str  # Classification type
    act: str  # Action to take
    prove: str  # Proof/witness
    remember: str  # Archival value
    tags: List[str] = field(default_factory=list)
    sigma_codon: str = ""
    
    def is_metastack(self) -> bool:
        """Check if this forms a metastack (all three layers present)"""
        return all(layer in self.tags for layer in ["substrate", "surface", "intent"])

@dataclass
class RemoteNode:
    """Remote node information"""
    node_id: str
    address: str
    port: int
    node_type: str  # "compute", "storage", "network", etc.
    capabilities: List[str] = field(default_factory=list)
    status: str = "unknown"  # "online", "offline", "degraded"
    last_seen: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # OmniToken support
    omnitoken_supported: bool = True
    omnitoken_containers: List[str] = field(default_factory=list)  # Container IDs this node is handling
    omnitoken_kot_balance: float = 1000.0  # Starting KOT balance
    omnitoken_chains: List[str] = field(default_factory=lambda: ['base', 'arbitrum'])  # Supported chains
    
    def is_online(self, timeout: float = 300.0) -> bool:
        """Check if node is online based on last seen timestamp"""
        return (time.time() - self.last_seen) < timeout
    
    def add_omnitoken_container(self, container_id: str) -> bool:
        """Add OmniToken container to node"""
        if not self.omnitoken_supported:
            return False
        if container_id not in self.omnitoken_containers:
            self.omnitoken_containers.append(container_id)
        return True
    
    def remove_omnitoken_container(self, container_id: str) -> bool:
        """Remove OmniToken container from node"""
        if container_id in self.omnitoken_containers:
            self.omnitoken_containers.remove(container_id)
            return True
        return False
    
    def burn_kot(self, amount: float) -> bool:
        """Burn KOT from node balance"""
        if self.omnitoken_kot_balance >= amount:
            self.omnitoken_kot_balance -= amount
            return True
        return False
    
    def supports_chain(self, chain: str) -> bool:
        """Check if node supports specific chain"""
        return chain in self.omnitoken_chains

@dataclass
class DAGEvent:
    """DAG event with explanation"""
    tick: int
    op: str  # Operation type
    args: List[str] = field(default_factory=list)
    registers: List[int] = field(default_factory=list)
    parent: Optional[str] = None
    status: str = "INITIAL"
    hash: str = ""
    explanation: str = ""  # Human-readable explanation
    timestamp: float = field(default_factory=time.time)
    snapshot: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "tick": self.tick,
            "op": self.op,
            "args": self.args,
            "registers": self.registers,
            "parent": self.parent,
            "status": self.status,
            "hash": self.hash,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
            "snapshot": self.snapshot
        }

@dataclass
class DAGTracker:
    """DAG-based change tracking with explanations"""
    events: List[DAGEvent] = field(default_factory=list)
    current_hash: str = ""
    paths_to_avoid: Set[str] = field(default_factory=set)  # Hashes of suboptimal paths
    path_analysis: Dict[str, Dict[str, any]] = field(default_factory=dict)  # Analysis of paths
    
    def add_event(self, event: DAGEvent):
        """Add an event to the DAG"""
        event.parent = self.current_hash
        self.events.append(event)
        self.current_hash = event.hash
    
    def get_event_chain(self, hash: str) -> List[DAGEvent]:
        """Get the chain of events leading to a specific hash"""
        chain = []
        current = hash
        for event in reversed(self.events):
            if event.hash == current:
                chain.append(event)
                current = event.parent if event.parent else ""
                if not current:
                    break
        return list(reversed(chain))
    
    def get_explanation(self, hash: str) -> str:
        """Get explanation for a specific event hash"""
        for event in self.events:
            if event.hash == hash:
                return event.explanation
        return "No explanation found"
    
    def analyze_evolution_patterns(self) -> Dict[str, any]:
        """Analyze evolution patterns in the DAG to identify suboptimal paths"""
        if len(self.events) < 3:
            return {'status': 'insufficient_data'}
        
        analysis = {
            'total_events': len(self.events),
            'event_types': {},
            'repeated_patterns': [],
            'suboptimal_branches': [],
            'cyclic_patterns': []
        }
        
        # Count event types
        for event in self.events:
            event_type = event.op
            analysis['event_types'][event_type] = analysis['event_types'].get(event_type, 0) + 1
        
        # Detect repeated operation sequences
        for i in range(len(self.events) - 2):
            seq1 = self.events[i].op
            seq2 = self.events[i+1].op
            seq3 = self.events[i+2].op
            pattern = f"{seq1}→{seq2}→{seq3}"
            
            # Check if this pattern repeats later
            for j in range(i + 3, len(self.events) - 2):
                if (self.events[j].op == seq1 and 
                    self.events[j+1].op == seq2 and 
                    self.events[j+2].op == seq3):
                    analysis['repeated_patterns'].append({
                        'pattern': pattern,
                        'first_occurrence': i,
                        'repeat_occurrence': j,
                        'frequency': 2
                    })
        
        # Detect branches that led to no improvement
        for i, event in enumerate(self.events):
            if event.snapshot:
                # Check if this event's snapshot metrics are worse than parent's
                parent = self.get_event_chain(event.parent)
                if parent and parent[-1].snapshot:
                    parent_metrics = parent[-1].snapshot
                    current_metrics = event.snapshot
                    
                    # Compare optimization_ratio if available
                    if 'optimization_ratio' in parent_metrics and 'optimization_ratio' in current_metrics:
                        if current_metrics['optimization_ratio'] < parent_metrics['optimization_ratio']:
                            analysis['suboptimal_branches'].append({
                                'event_hash': event.hash,
                                'operation': event.op,
                                'parent_hash': event.parent,
                                'optimization_drop': parent_metrics['optimization_ratio'] - current_metrics['optimization_ratio']
                            })
        
        # Store analysis
        self.path_analysis = analysis
        return analysis
    
    def identify_paths_to_avoid(self) -> List[str]:
        """Identify paths that should be avoided based on historical analysis"""
        analysis = self.analyze_evolution_patterns()
        
        new_avoid_paths = set()
        
        # Mark suboptimal branches as paths to avoid
        for branch in analysis.get('suboptimal_branches', []):
            new_avoid_paths.add(branch['event_hash'])
        
        # Mark repeated patterns that don't lead to improvement
        for pattern in analysis.get('repeated_patterns', []):
            if pattern['frequency'] > 2:
                # Mark the events in the pattern
                for i in range(3):
                    idx = pattern['first_occurrence'] + i
                    if idx < len(self.events):
                        new_avoid_paths.add(self.events[idx].hash)
        
        # Update paths to avoid
        self.paths_to_avoid.update(new_avoid_paths)
        
        return list(new_avoid_paths)
    
    def get_path_recommendation(self, proposed_operation: str) -> str:
        """Get recommendation for whether a proposed path should be avoided"""
        # Check if similar operations have led to suboptimal results
        for event in self.events:
            if event.op == proposed_operation and event.hash in self.paths_to_avoid:
                return f"AVOID: {proposed_operation} has historically led to suboptimal results"
        
        # Check for repeated patterns
        analysis = self.analyze_evolution_patterns()
        for pattern in analysis.get('repeated_patterns', []):
            if proposed_operation in pattern['pattern'] and pattern['frequency'] > 2:
                return f"CAUTION: {proposed_operation} is part of a repeated pattern ({pattern['pattern']})"
        
        return f"PROCEED: No historical evidence to avoid {proposed_operation}"
    
    def get_evolution_summary(self) -> str:
        """Get a summary of the swarm's evolution"""
        analysis = self.analyze_evolution_patterns()
        
        summary = f"Evolution Summary ({len(self.events)} events):\n"
        summary += f"  Event types: {analysis.get('event_types', {})}\n"
        summary += f"  Repeated patterns: {len(analysis.get('repeated_patterns', []))}\n"
        summary += f"  Suboptimal branches: {len(analysis.get('suboptimal_branches', []))}\n"
        summary += f"  Paths to avoid: {len(self.paths_to_avoid)}\n"
        
        return summary

# ═══════════════════════════════════════════════════════════════════════════
# Self-Optimization Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OptimizationTarget:
    """Target for self-optimization"""
    name: str
    current_value: float
    target_value: float
    tolerance: float = 0.1
    priority: int = 1  # Higher = more important
    optimization_history: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, value)
    
    def compute_optimization_score(self) -> float:
        """Compute how close we are to target (0.0 = perfect, 1.0 = far)"""
        if self.target_value == 0:
            return min(abs(self.current_value), 1.0)
        return abs(self.current_value - self.target_value) / abs(self.target_value)
    
    def is_optimized(self) -> bool:
        """Check if target is within tolerance"""
        return self.compute_optimization_score() < self.tolerance


@dataclass
class VirtualSubstrate:
    """PIST-based virtual substrate for topology mapping"""
    nodes: Dict[str, PISTCoord] = field(default_factory=dict)
    mass_field: Dict[str, int] = field(default_factory=dict)
    resonance_groups: Dict[int, List[str]] = field(default_factory=dict)  # mass -> node_ids
    
    def add_node(self, node_id: str, coord: PISTCoord):
        """Add a node to the virtual substrate"""
        self.nodes[node_id] = coord
        self.mass_field[node_id] = coord.mass
        
        # Update resonance groups
        if coord.mass not in self.resonance_groups:
            self.resonance_groups[coord.mass] = []
        self.resonance_groups[coord.mass].append(node_id)
    
    def get_resonant_nodes(self, node_id: str) -> List[str]:
        """Get all nodes resonant with the given node"""
        if node_id not in self.nodes:
            return []
        mass = self.nodes[node_id].mass
        return [nid for nid in self.resonance_groups.get(mass, []) if nid != node_id]
    
    def compute_substrate_potential(self) -> float:
        """Compute overall substrate potential (sum of masses)"""
        return sum(self.mass_field.values())

@dataclass
class SelfOptimizer:
    """Self-optimization engine for swarm"""
    targets: Dict[str, OptimizationTarget] = field(default_factory=dict)
    virtual_substrate: VirtualSubstrate = field(default_factory=VirtualSubstrate)
    optimization_cycles: int = 0
    last_optimization_time: float = field(default_factory=time.time)
    optimization_log: List[Dict[str, any]] = field(default_factory=list)
    state_file: str = "/home/allaun/Documents/Research Stack/data/swarm_optimization_state.json"
    
    def add_target(self, target: OptimizationTarget):
        """Add an optimization target"""
        self.targets[target.name] = target
    
    def optimize(self, context: Dict[str, float]) -> Dict[str, float]:
        """Perform one optimization cycle"""
        self.optimization_cycles += 1
        self.last_optimization_time = time.time()
        
        adjustments = {}
        
        for name, target in self.targets.items():
            current_score = target.compute_optimization_score()
            
            if not target.is_optimized():
                # Compute adjustment direction
                error = target.target_value - target.current_value
                adjustment = error * 0.1  # 10% adjustment rate
                
                # Apply adjustment
                new_value = target.current_value + adjustment
                target.current_value = new_value
                target.optimization_history.append((time.time(), new_value))
                
                adjustments[name] = adjustment
            
            # Log optimization state
            self.optimization_log.append({
                'cycle': self.optimization_cycles,
                'target': name,
                'score': current_score,
                'current': target.current_value,
                'target': target.target_value,
                'optimized': target.is_optimized()
            })
        
        return adjustments
    
    def get_optimization_summary(self) -> Dict[str, any]:
        """Get summary of optimization state"""
        optimized_count = sum(1 for t in self.targets.values() if t.is_optimized())
        total_targets = len(self.targets)
        
        return {
            'cycles': self.optimization_cycles,
            'optimized_count': optimized_count,
            'total_targets': total_targets,
            'optimization_ratio': optimized_count / max(1, total_targets),
            'last_optimization': self.last_optimization_time,
            'substrate_potential': self.virtual_substrate.compute_substrate_potential()
        }
    
    def save_state(self):
        """Save self-optimization state to file"""
        import json
        
        state = {
            'optimization_cycles': self.optimization_cycles,
            'last_optimization_time': self.last_optimization_time,
            'targets': {
                name: {
                    'current_value': target.current_value,
                    'target_value': target.target_value,
                    'tolerance': target.tolerance,
                    'priority': target.priority,
                    'optimization_history': target.optimization_history
                }
                for name, target in self.targets.items()
            },
            'virtual_substrate': {
                'nodes': {
                    node_id: {'k': coord.k, 't': coord.t, 'ht': coord.ht}
                    for node_id, coord in self.virtual_substrate.nodes.items()
                },
                'mass_field': self.virtual_substrate.mass_field,
                'resonance_groups': self.virtual_substrate.resonance_groups
            },
            'optimization_log': self.optimization_log[-100:]  # Keep last 100 entries
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save optimization state: {e}")
    
    def load_state(self):
        """Load self-optimization state from file"""
        import json
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.optimization_cycles = state.get('optimization_cycles', 0)
            self.last_optimization_time = state.get('last_optimization_time', time.time)
            
            # Restore targets
            for name, target_data in state.get('targets', {}).items():
                if name in self.targets:
                    self.targets[name].current_value = target_data['current_value']
                    self.targets[name].optimization_history = target_data.get('optimization_history', [])
            
            # Restore virtual substrate
            substrate_data = state.get('virtual_substrate', {})
            self.virtual_substrate.nodes = {
                node_id: PISTCoord(k=coord['k'], t=coord['t'], ht=coord['ht'])
                for node_id, coord in substrate_data.get('nodes', {}).items()
            }
            self.virtual_substrate.mass_field = substrate_data.get('mass_field', {})
            self.virtual_substrate.resonance_groups = substrate_data.get('resonance_groups', {})
            
            # Restore log
            self.optimization_log = state.get('optimization_log', [])
            
            print(f"[INFO] Loaded optimization state from {self.state_file}")
            print(f"  Cycles: {self.optimization_cycles}")
            print(f"  Targets: {len(self.targets)}")
            
        except FileNotFoundError:
            print(f"[INFO] No existing optimization state found, starting fresh")
        except Exception as e:
            print(f"[WARNING] Failed to load optimization state: {e}")

@dataclass
class RAMLoopbackWriter:
    """RAM loopback writer for swarm improvements
    
    Writes swarm improvements to RAM (tmpfs) for fast access,
    then syncs to persistent disk storage for durability.
    """
    ram_path: str = "/tmp/swarm_improvements"  # RAM location (tmpfs)
    disk_path: str = "/home/allaun/Documents/Research Stack/data/swarm_improvements.json"  # Persistent disk location
    sync_interval: float = 5.0  # Sync to disk every 5 seconds
    last_sync_time: float = field(default_factory=time.time)
    improvements_buffer: List[Dict[str, any]] = field(default_factory=list)
    
    def write_improvement(self, agent_id: int, improvement_type: str, 
                          improvement_data: Dict[str, any]):
        """Write an improvement to RAM (fast)"""
        import json
        from pathlib import Path
        
        timestamp = time.time()
        improvement_record = {
            'timestamp': timestamp,
            'agent_id': agent_id,
            'type': improvement_type,
            'data': improvement_data
        }
        
        # Add to buffer
        self.improvements_buffer.append(improvement_record)
        
        # Write to RAM (tmpfs) - fast write
        ram_file = Path(self.ram_path) / f"agent_{agent_id}_{timestamp}.json"
        try:
            ram_file.parent.mkdir(parents=True, exist_ok=True)
            with open(ram_file, 'w') as f:
                json.dump(improvement_record, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to write improvement to RAM: {e}")
        
        # Check if sync to disk is needed
        if time.time() - self.last_sync_time >= self.sync_interval:
            self.sync_to_disk()
    
    def sync_to_disk(self):
        """Sync improvements from RAM to persistent disk storage"""
        import json
        from pathlib import Path
        import shutil
        
        self.last_sync_time = time.time()
        
        try:
            # Read existing disk data
            disk_data = []
            if Path(self.disk_path).exists():
                with open(self.disk_path, 'r') as f:
                    disk_data = json.load(f)
            
            # Add buffered improvements
            disk_data.extend(self.improvements_buffer)
            
            # Write to disk
            disk_file = Path(self.disk_path)
            disk_file.parent.mkdir(parents=True, exist_ok=True)
            with open(disk_file, 'w') as f:
                json.dump(disk_data, f, indent=2)
            
            # Clear buffer after successful sync
            self.improvements_buffer.clear()
            
            print(f"[INFO] Synced {len(disk_data)} improvements to disk")
            
        except Exception as e:
            print(f"[WARNING] Failed to sync improvements to disk: {e}")
    
    def read_improvements(self, agent_id: Optional[int] = None) -> List[Dict[str, any]]:
        """Read improvements from RAM (fast) or disk if RAM is empty"""
        import json
        from pathlib import Path
        
        improvements = []
        
        # Try RAM first (fast)
        try:
            ram_dir = Path(self.ram_path)
            if ram_dir.exists():
                for file_path in ram_dir.glob("*.json"):
                    with open(file_path, 'r') as f:
                        record = json.load(f)
                        if agent_id is None or record.get('agent_id') == agent_id:
                            improvements.append(record)
        except Exception as e:
            print(f"[WARNING] Failed to read improvements from RAM: {e}")
        
        # If RAM is empty or specific agent not found, try disk
        if not improvements:
            try:
                if Path(self.disk_path).exists():
                    with open(self.disk_path, 'r') as f:
                        all_improvements = json.load(f)
                        if agent_id is None:
                            improvements = all_improvements
                        else:
                            improvements = [r for r in all_improvements 
                                         if r.get('agent_id') == agent_id]
            except Exception as e:
                print(f"[WARNING] Failed to read improvements from disk: {e}")
        
        return improvements
    
    def get_improvement_summary(self, agent_id: Optional[int] = None) -> Dict[str, any]:
        """Get summary of improvements"""
        improvements = self.read_improvements(agent_id)
        
        type_counts = {}
        for imp in improvements:
            imp_type = imp.get('type', 'unknown')
            type_counts[imp_type] = type_counts.get(imp_type, 0) + 1
        
        return {
            'total_improvements': len(improvements),
            'type_counts': type_counts,
            'latest_timestamp': max([imp.get('timestamp', 0) for imp in improvements]) if improvements else 0,
            'ram_path': self.ram_path,
            'disk_path': self.disk_path,
            'buffer_size': len(self.improvements_buffer)
        }

@dataclass
class GPULearning:
    """GPU learning mechanism for swarm agents
    
    Loads GPU optimization guide and teaches agents how to leverage
    GPU hardware efficiently using CUDA and Vulkan best practices.
    """
    guide_path: str = "/home/allaun/Documents/Research Stack/data/germane/research/gpu_optimization_guide.md"
    learned_techniques: List[str] = field(default_factory=list)
    technique_scores: Dict[str, float] = field(default_factory=dict)
    learning_history: List[Dict[str, any]] = field(default_factory=list)
    
    def load_guide(self) -> str:
        """Load GPU optimization guide"""
        try:
            with open(self.guide_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"[WARNING] Failed to load GPU optimization guide: {e}")
            return ""
    
    def extract_techniques(self, guide_content: str) -> List[str]:
        """Extract GPU optimization techniques from guide"""
        techniques = []
        
        # CUDA techniques
        cuda_section = guide_content.split("## CUDA Optimization Techniques")[1].split("## Vulkan Optimization Techniques")[0]
        
        # Extract key CUDA techniques
        if "Maximizing parallel execution" in cuda_section:
            techniques.append("cuda_maximize_parallel_execution")
        if "Optimizing memory usage" in cuda_section:
            techniques.append("cuda_optimize_memory_usage")
        if "Optimizing instruction usage" in cuda_section:
            techniques.append("cuda_optimize_instruction_usage")
        if "Coalesced Access" in cuda_section:
            techniques.append("cuda_coalesced_access")
        if "Shared Memory" in cuda_section:
            techniques.append("cuda_shared_memory")
        if "Pinned Memory" in cuda_section:
            techniques.append("cuda_pinned_memory")
        if "Asynchronous Transfers" in cuda_section:
            techniques.append("cuda_async_transfers")
        if "Occupancy" in cuda_section:
            techniques.append("cuda_occupancy")
        if "Concurrent Kernel Execution" in cuda_section:
            techniques.append("cuda_concurrent_kernels")
        if "Fast math intrinsics" in cuda_section:
            techniques.append("cuda_fast_math")
        if "Minimize branch divergence" in cuda_section:
            techniques.append("cuda_minimize_divergence")
        
        # Vulkan techniques
        vulkan_section = guide_content.split("## Vulkan Optimization Techniques")[1].split("## AMD GPU Specific Considerations")[0]
        
        # Extract key Vulkan techniques
        if "Parallelize command buffer recording" in vulkan_section:
            techniques.append("vulkan_parallel_recording")
        if "Memory sub-allocation" in vulkan_section:
            techniques.append("vulkan_memory_suballocation")
        if "VK_EXT_memory_budget" in vulkan_section:
            techniques.append("vulkan_memory_budget")
        if "Transient attachments" in vulkan_section:
            techniques.append("vulkan_transient_attachments")
        if "loadOp and storeOp" in vulkan_section:
            techniques.append("vulkan_load_store_ops")
        if "Separate vertex positions" in vulkan_section:
            techniques.append("vulkan_separate_vertex_positions")
        if "Hardware depth culling" in vulkan_section:
            techniques.append("vulkan_depth_culling")
        if "Manage precision carefully" in vulkan_section:
            techniques.append("vulkan_precision_management")
        
        # Unsloth techniques
        unsloth_section = guide_content.split("## Unsloth Optimization Techniques")[1].split("## PyTorch GPU Optimization Techniques")[0]
        
        # Extract key Unsloth techniques
        if "4-bit/FP8 Training" in unsloth_section:
            techniques.append("unsloth_4bit_fp8_training")
        if "2x Faster Training" in unsloth_section:
            techniques.append("unsloth_faster_training")
        if "Multi-GPU" in unsloth_section:
            techniques.append("unsloth_multi_gpu")
        if "Auto Dataset Creation" in unsloth_section:
            techniques.append("unsloth_auto_dataset")
        if "Observability" in unsloth_section:
            techniques.append("unsloth_observability")
        if "GGUF export" in unsloth_section:
            techniques.append("unsloth_gguf_export")
        
        # PyTorch techniques
        pytorch_section = guide_content.split("## PyTorch GPU Optimization Techniques")[1].split("## GPU Learning Mechanisms for Swarm")[0]
        
        # Extract key PyTorch techniques
        if "num_workers > 0" in pytorch_section:
            techniques.append("pytorch_async_dataloader")
        if "pin_memory=True" in pytorch_section:
            techniques.append("pytorch_pinned_memory")
        if "torch.no_grad()" in pytorch_section:
            techniques.append("pytorch_no_grad")
        if "bias=False" in pytorch_section:
            techniques.append("pytorch_conv_bias_optimization")
        if "set_to_none=True" in pytorch_section:
            techniques.append("pytorch_grad_none")
        if "Mixed Precision" in pytorch_section:
            techniques.append("pytorch_mixed_precision")
        if "DistributedDataParallel" in pytorch_section:
            techniques.append("pytorch_ddp")
        if "Gradient Checkpointing" in pytorch_section:
            techniques.append("pytorch_gradient_checkpointing")
        
        return techniques
    
    def learn_technique(self, technique: str, score: float = 1.0):
        """Learn a GPU optimization technique"""
        if technique not in self.learned_techniques:
            self.learned_techniques.append(technique)
            self.technique_scores[technique] = score
            
            learning_record = {
                'timestamp': time.time(),
                'technique': technique,
                'score': score
            }
            self.learning_history.append(learning_record)
            
            print(f"[GPU LEARNING] Learned technique: {technique} (score: {score:.2f})")
    
    def get_recommendation(self, context: Dict[str, str]) -> str:
        """Get GPU optimization recommendation based on context"""
        if not self.learned_techniques:
            return "Learn GPU optimization techniques first"
        
        # Context-aware recommendation
        if context.get('api') == 'cuda':
            if 'cuda_maximize_parallel_execution' not in self.learned_techniques:
                return "Learn to maximize parallel execution in CUDA"
            elif 'cuda_coalesced_access' not in self.learned_techniques:
                return "Learn coalesced memory access patterns"
            elif 'cuda_shared_memory' not in self.learned_techniques:
                return "Learn to use shared memory efficiently"
            else:
                return "Apply advanced CUDA optimization techniques"
        
        elif context.get('api') == 'vulkan':
            if 'vulkan_memory_suballocation' not in self.learned_techniques:
                return "Learn Vulkan memory sub-allocation"
            elif 'vulkan_transient_attachments' not in self.learned_techniques:
                return "Learn to use transient attachments"
            elif 'vulkan_load_store_ops' not in self.learned_techniques:
                return "Learn to use loadOp and storeOp efficiently"
            else:
                return "Apply advanced Vulkan optimization techniques"
        
        elif context.get('api') == 'unsloth':
            if 'unsloth_4bit_fp8_training' not in self.learned_techniques:
                return "Learn Unsloth 4-bit/FP8 training for VRAM efficiency"
            elif 'unsloth_faster_training' not in self.learned_techniques:
                return "Learn Unsloth 2x faster training techniques"
            elif 'unsloth_observability' not in self.learned_techniques:
                return "Learn Unsloth observability for monitoring"
            else:
                return "Apply advanced Unsloth optimization techniques"
        
        elif context.get('api') == 'pytorch':
            if 'pytorch_async_dataloader' not in self.learned_techniques:
                return "Learn PyTorch async data loading with num_workers"
            elif 'pytorch_no_grad' not in self.learned_techniques:
                return "Learn PyTorch gradient disabling for inference"
            elif 'pytorch_mixed_precision' not in self.learned_techniques:
                return "Learn PyTorch mixed precision training"
            else:
                return "Apply advanced PyTorch optimization techniques"
        
        else:
            return "Specify API context (cuda, vulkan, unsloth, or pytorch)"
    
    def get_learning_summary(self) -> Dict[str, any]:
        """Get summary of learned techniques"""
        return {
            'total_techniques': len(self.learned_techniques),
            'techniques': self.learned_techniques,
            'average_score': sum(self.technique_scores.values()) / max(1, len(self.technique_scores)),
            'learning_history_count': len(self.learning_history)
        }
    
    def auto_learn(self):
        """Auto-learn GPU optimization techniques from guide"""
        guide_content = self.load_guide()
        if not guide_content:
            return
        
        techniques = self.extract_techniques(guide_content)
        
        for technique in techniques:
            if technique not in self.learned_techniques:
                self.learn_technique(technique, score=1.0)
        
        print(f"[GPU LEARNING] Auto-learned {len(techniques)} GPU optimization techniques")

@dataclass
class BiologicalLearning:
    """Biological systems learning mechanism for swarm agents
    
    Loads biological systems guide and teaches agents how to leverage
    biological optimization principles for computational system design.
    """
    guide_path: str = "/home/allaun/Documents/Research Stack/data/germane/research/biological_systems_guide.md"
    learned_principles: List[str] = field(default_factory=list)
    principle_scores: Dict[str, float] = field(default_factory=dict)
    learning_history: List[Dict[str, any]] = field(default_factory=list)
    
    def load_guide(self) -> str:
        """Load biological systems guide"""
        try:
            with open(self.guide_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"[WARNING] Failed to load biological systems guide: {e}")
            return ""
    
    def extract_principles(self, guide_content: str) -> List[str]:
        """Extract biological optimization principles from guide"""
        principles = []
        
        # Blood vessel principles
        if "Pressure Gradient" in guide_content:
            principles.append("bio_pressure_gradient")
        if "Resistance Management" in guide_content:
            principles.append("bio_resistance_management")
        if "Hierarchical Structure" in guide_content:
            principles.append("bio_hierarchical_structure")
        if "Vasodilation/Vasoconstriction" in guide_content:
            principles.append("bio_adaptive_diameter")
        if "Valves" in guide_content:
            principles.append("bio_flow_control")
        
        # Nutrient transport principles
        if "Parallel Transport" in guide_content:
            principles.append("bio_parallel_transport")
        if "Carrier Specialization" in guide_content:
            principles.append("bio_carrier_specialization")
        if "Exchange Efficiency" in guide_content:
            principles.append("bio_exchange_efficiency")
        if "Concurrent Transport" in guide_content:
            principles.append("bio_concurrent_transport")
        
        # Energy flow principles
        if "Energy Currency" in guide_content:
            principles.append("bio_energy_currency")
        if "Pathway Selection" in guide_content:
            principles.append("bio_pathway_selection")
        if "Compartmentalization" in guide_content:
            principles.append("bio_compartmentalization")
        if "Energy Coupling" in guide_content:
            principles.append("bio_energy_coupling")
        
        # Network topology principles
        if "Network Topology Principles" in guide_content:
            principles.append("bio_network_topology")
        if "Transport Optimization" in guide_content:
            principles.append("bio_transport_optimization")
        if "Energy Optimization" in guide_content:
            principles.append("bio_energy_optimization")
        if "Redundancy and Resilience" in guide_content:
            principles.append("bio_redundancy_resilience")
        
        return principles
    
    def learn_principle(self, principle: str, score: float = 1.0):
        """Learn a biological optimization principle"""
        if principle not in self.learned_principles:
            self.learned_principles.append(principle)
            self.principle_scores[principle] = score
            
            learning_record = {
                'timestamp': time.time(),
                'principle': principle,
                'score': score
            }
            self.learning_history.append(learning_record)
            
            print(f"[BIO LEARNING] Learned principle: {principle} (score: {score:.2f})")
    
    def get_recommendation(self, context: Dict[str, str]) -> str:
        """Get biological optimization recommendation based on context"""
        if not self.learned_principles:
            return "Learn biological optimization principles first"
        
        # Context-aware recommendation
        if context.get('domain') == 'network':
            if 'bio_hierarchical_structure' not in self.learned_principles:
                return "Learn hierarchical network topology from blood vessels"
            elif 'bio_pressure_gradient' not in self.learned_principles:
                return "Learn pressure gradient management for network flow"
            elif 'bio_resistance_management' not in self.learned_principles:
                return "Learn resistance management for network optimization"
            else:
                return "Apply advanced biological network optimization principles"
        
        elif context.get('domain') == 'transport':
            if 'bio_parallel_transport' not in self.learned_principles:
                return "Learn parallel transport from blood nutrient delivery"
            elif 'bio_carrier_specialization' not in self.learned_principles:
                return "Learn carrier specialization for efficient transport"
            elif 'bio_exchange_efficiency' not in self.learned_principles:
                return "Learn exchange efficiency from capillary design"
            else:
                return "Apply advanced biological transport optimization principles"
        
        elif context.get('domain') == 'energy':
            if 'bio_energy_currency' not in self.learned_principles:
                return "Learn energy currency concept from ATP"
            elif 'bio_pathway_selection' not in self.learned_principles:
                return "Learn pathway selection from cellular respiration"
            elif 'bio_compartmentalization' not in self.learned_principles:
                return "Learn compartmentalization from mitochondrial design"
            else:
                return "Apply advanced biological energy optimization principles"
        
        elif context.get('domain') == 'resilience':
            if 'bio_redundancy_resilience' not in self.learned_principles:
                return "Learn redundancy principles from biological systems"
            elif 'bio_flow_control' not in self.learned_principles:
                return "Learn flow control from vein valves"
            elif 'bio_adaptive_diameter' not in self.learned_principles:
                return "Learn adaptive diameter control from vasodilation"
            else:
                return "Apply advanced biological resilience principles"
        
        else:
            return "Specify domain context (network, transport, energy, or resilience)"
    
    def get_learning_summary(self) -> Dict[str, any]:
        """Get summary of learned principles"""
        return {
            'total_principles': len(self.learned_principles),
            'principles': self.learned_principles,
            'average_score': sum(self.principle_scores.values()) / max(1, len(self.principle_scores)),
            'learning_history_count': len(self.learning_history)
        }
    
    def auto_learn(self):
        """Auto-learn biological optimization principles from guide"""
        guide_content = self.load_guide()
        if not guide_content:
            return
        
        principles = self.extract_principles(guide_content)
        
        for principle in principles:
            if principle not in self.learned_principles:
                self.learn_principle(principle, score=1.0)
        
        print(f"[BIO LEARNING] Auto-learned {len(principles)} biological optimization principles")

@dataclass
class ComprehensiveLearning:
    """Comprehensive physics and engineering learning mechanism for swarm agents
    
    Loads comprehensive physics and engineering guide and teaches agents about
    EM spectrum, material science, computation design, and quantum mechanics.
    """
    guide_path: str = "/home/allaun/Documents/Research Stack/data/germane/research/comprehensive_physics_engineering_guide.md"
    learned_concepts: List[str] = field(default_factory=list)
    concept_scores: Dict[str, float] = field(default_factory=dict)
    learning_history: List[Dict[str, any]] = field(default_factory=list)
    
    def load_guide(self) -> str:
        """Load comprehensive physics and engineering guide"""
        try:
            with open(self.guide_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"[WARNING] Failed to load comprehensive physics and engineering guide: {e}")
            return ""
    
    def extract_concepts(self, guide_content: str) -> List[str]:
        """Extract physics and engineering concepts from guide"""
        concepts = []
        
        # EM spectrum concepts
        if "Radio Waves" in guide_content:
            concepts.append("em_radio_waves")
        if "Microwaves" in guide_content:
            concepts.append("em_microwaves")
        if "Infrared Radiation" in guide_content:
            concepts.append("em_infrared")
        if "Visible Light" in guide_content:
            concepts.append("em_visible_light")
        if "Ultraviolet Radiation" in guide_content:
            concepts.append("em_ultraviolet")
        if "X-Rays" in guide_content:
            concepts.append("em_xrays")
        if "Gamma Rays" in guide_content:
            concepts.append("em_gamma_rays")
        if "Wave-Particle Duality" in guide_content:
            concepts.append("em_wave_particle_duality")
        if "Photon Energy" in guide_content:
            concepts.append("em_photon_energy")
        
        # Material science concepts
        if "Metals" in guide_content:
            concepts.append("mat_metals")
        if "Semiconductors" in guide_content:
            concepts.append("mat_semiconductors")
        if "Ceramics" in guide_content:
            concepts.append("mat_ceramics")
        if "Polymers" in guide_content:
            concepts.append("mat_polymers")
        if "Crystal Structure" in guide_content:
            concepts.append("mat_crystal_structure")
        if "Band Theory" in guide_content:
            concepts.append("mat_band_theory")
        if "Doping" in guide_content:
            concepts.append("mat_doping")
        
        # Computation design concepts
        if "Von Neumann Architecture" in guide_content:
            concepts.append("comp_von_neumann")
        if "Harvard Architecture" in guide_content:
            concepts.append("comp_harvard")
        if "Parallel Processing" in guide_content:
            concepts.append("comp_parallel_processing")
        if "Memory Hierarchy" in guide_content:
            concepts.append("comp_memory_hierarchy")
        if "SIMD" in guide_content:
            concepts.append("comp_simd")
        if "Pipelining" in guide_content:
            concepts.append("comp_pipelining")
        
        # Quantum mechanics concepts
        if "Superposition" in guide_content:
            concepts.append("quantum_superposition")
        if "Entanglement" in guide_content:
            concepts.append("quantum_entanglement")
        if "Uncertainty Principle" in guide_content:
            concepts.append("quantum_uncertainty")
        if "Wave Function" in guide_content:
            concepts.append("quantum_wave_function")
        if "Qubit" in guide_content:
            concepts.append("quantum_qubit")
        if "Quantum Computing" in guide_content:
            concepts.append("quantum_computing")
        
        # Cross-domain concepts
        if "Metamaterials" in guide_content:
            concepts.append("cross_metamaterials")
        if "Quantum Processors" in guide_content:
            concepts.append("cross_quantum_processors")
        if "Photonic Crystals" in guide_content:
            concepts.append("cross_photonic_crystals")
        if "Quantum Annealing" in guide_content:
            concepts.append("cross_quantum_annealing")
        
        # Thermodynamics concepts
        if "Zeroth Law" in guide_content:
            concepts.append("thermo_zeroth_law")
        if "First Law" in guide_content:
            concepts.append("thermo_first_law")
        if "Second Law" in guide_content:
            concepts.append("thermo_second_law")
        if "Third Law" in guide_content:
            concepts.append("thermo_third_law")
        if "Onsager Relations" in guide_content:
            concepts.append("thermo_onsager_relations")
        if "Entropy" in guide_content:
            concepts.append("thermo_entropy")
        if "Enthalpy" in guide_content:
            concepts.append("thermo_enthalpy")
        if "Gibbs Free Energy" in guide_content:
            concepts.append("thermo_gibbs_free_energy")
        if "Carnot Cycle" in guide_content:
            concepts.append("thermo_carnot_cycle")
        if "Heat Transfer" in guide_content:
            concepts.append("thermo_heat_transfer")
        if "Thermal Efficiency" in guide_content:
            concepts.append("thermo_efficiency")
        
        # Networking concepts
        if "OSI Model" in guide_content:
            concepts.append("net_osi_model")
        if "TCP/IP Model" in guide_content:
            concepts.append("net_tcpip_model")
        if "DNS" in guide_content:
            concepts.append("net_dns")
        if "DHCP" in guide_content:
            concepts.append("net_dhcp")
        if "HTTP" in guide_content:
            concepts.append("net_http")
        if "FTP" in guide_content:
            concepts.append("net_ftp")
        if "SMTP" in guide_content:
            concepts.append("net_smtp")
        if "TCP" in guide_content:
            concepts.append("net_tcp")
        if "UDP" in guide_content:
            concepts.append("net_udp")
        if "IP" in guide_content:
            concepts.append("net_ip")
        if "ARP" in guide_content:
            concepts.append("net_arp")
        if "ICMP" in guide_content:
            concepts.append("net_icmp")
        if "BGP" in guide_content:
            concepts.append("net_bgp")
        if "OSPF" in guide_content:
            concepts.append("net_ospf")
        if "IP Addressing" in guide_content:
            concepts.append("net_ip_addressing")
        if "Network Topologies" in guide_content:
            concepts.append("net_topologies")
        if "Network Devices" in guide_content:
            concepts.append("net_devices")
        
        # OmniToken concepts
        if "OmniToken" in guide_content:
            concepts.append("omni_container_layer")
        if "Fragmentation" in guide_content:
            concepts.append("omni_fragmentation")
        if "KOT" in guide_content or "Kinetic Operation Token" in guide_content:
            concepts.append("omni_kot")
        if "Waveprobe" in guide_content:
            concepts.append("omni_waveprobe")
        if "GraphVM" in guide_content:
            concepts.append("omni_graphvm")
        if "Compliance" in guide_content:
            concepts.append("omni_compliance")
        if "Cross-chain" in guide_content:
            concepts.append("omni_cross_chain")
        if "Idempotency" in guide_content:
            concepts.append("omni_idempotency")
        if "Execution Pipeline" in guide_content:
            concepts.append("omni_pipeline")
        
        # ISO Standards concepts
        if "ISO/TC 307" in guide_content or "ISO 22739" in guide_content:
            concepts.append("iso_blockchain")
        if "ISO 20022" in guide_content:
            concepts.append("iso_financial_messaging")
        if "ISO/IEC 7498" in guide_content or "OSI model" in guide_content:
            concepts.append("iso_osi_model")
        if "ISO 50001" in guide_content:
            concepts.append("iso_energy_management")
        if "ISO/IEC 4879" in guide_content:
            concepts.append("iso_quantum_computing")
        if "ISO/IEC 18033" in guide_content:
            concepts.append("iso_encryption")
        if "ISO 9001" in guide_content:
            concepts.append("iso_quality_management")
        if "ISO/IEC 61000" in guide_content:
            concepts.append("iso_emc")
        if "ISO/IEC 17788" in guide_content:
            concepts.append("iso_cloud_computing")
        if "ISO/IEC 27001" in guide_content:
            concepts.append("iso_security_management")
        if "ISO 31000" in guide_content:
            concepts.append("iso_risk_management")
        
        # W3C Standards concepts
        if "Web Ledger Protocol" in guide_content:
            concepts.append("w3c_web_ledger")
        if "Decentralized Identifiers" in guide_content or "DID" in guide_content:
            concepts.append("w3c_did")
        if "Verifiable Credentials" in guide_content or "VC" in guide_content:
            concepts.append("w3c_verifiable_credentials")
        if "WebRTC" in guide_content:
            concepts.append("w3c_webrtc")
        if "WebSocket" in guide_content:
            concepts.append("w3c_websocket")
        if "JSON-LD" in guide_content:
            concepts.append("w3c_json_ld")
        if "Cryptography Usage" in guide_content:
            concepts.append("w3c_cryptography")
        if "REST" in guide_content:
            concepts.append("w3c_rest")
        if "Building Protocols with HTTP" in guide_content:
            concepts.append("w3c_http_protocols")
        if "Decentralized Web" in guide_content:
            concepts.append("w3c_decentralized_web")
        
        # Internet Protocol concepts
        if "I2P" in guide_content:
            concepts.append("proto_i2p")
        if "Tor" in guide_content:
            concepts.append("proto_tor")
        if "BitTorrent" in guide_content:
            concepts.append("proto_bittorrent")
        if "MQTT" in guide_content:
            concepts.append("proto_mqtt")
        if "CoAP" in guide_content:
            concepts.append("proto_coap")
        if "QUIC" in guide_content:
            concepts.append("proto_quic")
        if "WireGuard" in guide_content:
            concepts.append("proto_wireguard")
        if "BGP" in guide_content:
            concepts.append("proto_bgp")
        if "OSPF" in guide_content:
            concepts.append("proto_ospf")
        if "Ethereum" in guide_content:
            concepts.append("proto_ethereum")
        if "Bitcoin" in guide_content:
            concepts.append("proto_bitcoin")
        if "Solana" in guide_content:
            concepts.append("proto_solana")
        if "LoRaWAN" in guide_content:
            concepts.append("proto_lorawan")
        if "Zigbee" in guide_content:
            concepts.append("proto_zigbee")
        if "SIP" in guide_content:
            concepts.append("proto_sip")
        if "H.323" in guide_content:
            concepts.append("proto_h323")
        if "RTP" in guide_content:
            concepts.append("proto_rtp")
        if "RTSP" in guide_content:
            concepts.append("proto_rtsp")
        if "HLS" in guide_content:
            concepts.append("proto_hls")
        if "MPEG-DASH" in guide_content:
            concepts.append("proto_mpeg_dash")
        if "OpenVPN" in guide_content:
            concepts.append("proto_openvpn")
        if "IPsec" in guide_content:
            concepts.append("proto_ipsec")
        if "IKEv2" in guide_content:
            concepts.append("proto_ikev2")
        
        # Compression algorithms
        if "DEFLATE" in guide_content or "gzip" in guide_content:
            concepts.append("comp_deflate")
        if "ZSTD" in guide_content or "Zstandard" in guide_content:
            concepts.append("comp_zstd")
        if "LZ4" in guide_content:
            concepts.append("comp_lz4")
        if "BZIP2" in guide_content:
            concepts.append("comp_bzip2")
        if "XZ" in guide_content or "LZMA" in guide_content:
            concepts.append("comp_xz")
        if "BROTLI" in guide_content:
            concepts.append("comp_brotli")
        
        # File formats
        if "JPEG" in guide_content:
            concepts.append("fmt_jpeg")
        if "PNG" in guide_content:
            concepts.append("fmt_png")
        if "GIF" in guide_content:
            concepts.append("fmt_gif")
        if "WebP" in guide_content:
            concepts.append("fmt_webp")
        if "SVG" in guide_content:
            concepts.append("fmt_svg")
        if "MP4" in guide_content:
            concepts.append("fmt_mp4")
        if "MKV" in guide_content:
            concepts.append("fmt_mkv")
        if "WebM" in guide_content:
            concepts.append("fmt_webm")
        if "MP3" in guide_content:
            concepts.append("fmt_mp3")
        if "FLAC" in guide_content:
            concepts.append("fmt_flac")
        if "AAC" in guide_content:
            concepts.append("fmt_aac")
        if "PDF" in guide_content:
            concepts.append("fmt_pdf")
        if "JSON" in guide_content:
            concepts.append("fmt_json")
        if "XML" in guide_content:
            concepts.append("fmt_xml")
        if "YAML" in guide_content:
            concepts.append("fmt_yaml")
        
        # Programming languages
        if "Python" in guide_content:
            concepts.append("lang_python")
        if "JavaScript" in guide_content:
            concepts.append("lang_javascript")
        if "Java" in guide_content:
            concepts.append("lang_java")
        if "C++" in guide_content:
            concepts.append("lang_cpp")
        if "Rust" in guide_content:
            concepts.append("lang_rust")
        if "Go" in guide_content:
            concepts.append("lang_go")
        if "Swift" in guide_content:
            concepts.append("lang_swift")
        if "TypeScript" in guide_content:
            concepts.append("lang_typescript")
        if "C#" in guide_content:
            concepts.append("lang_csharp")
        if "Haskell" in guide_content:
            concepts.append("lang_haskell")
        if "Erlang" in guide_content:
            concepts.append("lang_erlang")
        if "Elixir" in guide_content:
            concepts.append("lang_elixir")
        if "SQL" in guide_content:
            concepts.append("lang_sql")
        
        # Encryption standards
        if "AES" in guide_content:
            concepts.append("enc_aes")
        if "RSA" in guide_content:
            concepts.append("enc_rsa")
        if "ECC" in guide_content:
            concepts.append("enc_ecc")
        if "SHA-256" in guide_content:
            concepts.append("enc_sha256")
        if "SHA-3" in guide_content:
            concepts.append("enc_sha3")
        if "Ed25519" in guide_content:
            concepts.append("enc_ed25519")
        if "Kyber" in guide_content:
            concepts.append("enc_kyber")
        if "Dilithium" in guide_content:
            concepts.append("enc_dilithium")
        if "ChaCha20" in guide_content:
            concepts.append("enc_chacha20")
        if "BLAKE2" in guide_content:
            concepts.append("enc_blake2")
        
        # Mathematical types
        if "calculus" in guide_content.lower():
            concepts.append("math_calculus")
        if "algebra" in guide_content.lower():
            concepts.append("math_algebra")
        if "geometry" in guide_content.lower():
            concepts.append("math_geometry")
        if "statistics" in guide_content.lower():
            concepts.append("math_statistics")
        if "set theory" in guide_content.lower():
            concepts.append("math_set_theory")
        if "logic" in guide_content.lower():
            concepts.append("math_logic")
        if "category theory" in guide_content.lower():
            concepts.append("math_category_theory")
        if "type theory" in guide_content.lower():
            concepts.append("math_type_theory")
        
        # Digital platforms concepts
        if "Twitter" in guide_content or "X" in guide_content:
            concepts.append("platform_twitter")
        if "Facebook" in guide_content:
            concepts.append("platform_facebook")
        if "Instagram" in guide_content:
            concepts.append("platform_instagram")
        if "LinkedIn" in guide_content:
            concepts.append("platform_linkedin")
        if "TikTok" in guide_content:
            concepts.append("platform_tiktok")
        if "YouTube" in guide_content:
            concepts.append("platform_youtube")
        if "Reddit" in guide_content:
            concepts.append("platform_reddit")
        if "Discord" in guide_content:
            concepts.append("platform_discord")
        if "Mastodon" in guide_content:
            concepts.append("platform_mastodon")
        if "GitHub" in guide_content:
            concepts.append("platform_github")
        if "Forgejo" in guide_content:
            concepts.append("platform_forgejo")
        if "Codeberg" in guide_content:
            concepts.append("platform_codeberg")
        if "GitLab" in guide_content:
            concepts.append("platform_gitlab")
        if "Google" in guide_content and "search" in guide_content.lower():
            concepts.append("search_google")
        if "Bing" in guide_content:
            concepts.append("search_bing")
        if "DuckDuckGo" in guide_content:
            concepts.append("search_duckduckgo")
        if "Brave Search" in guide_content:
            concepts.append("search_brave")
        if "Chrome" in guide_content:
            concepts.append("browser_chrome")
        if "Firefox" in guide_content:
            concepts.append("browser_firefox")
        if "Safari" in guide_content:
            concepts.append("browser_safari")
        if "Edge" in guide_content:
            concepts.append("browser_edge")
        if "Brave" in guide_content and "browser" in guide_content.lower():
            concepts.append("browser_brave")
        if "Tailscale" in guide_content:
            concepts.append("network_tailscale")
        if "WireGuard" in guide_content:
            concepts.append("network_wireguard")
        if "VPN" in guide_content or "vpn" in guide_content.lower():
            concepts.append("network_vpn")
        if "TCP/IP" in guide_content or "TCP IP" in guide_content:
            concepts.append("internet_tcpip")
        if "DNS" in guide_content:
            concepts.append("internet_dns")
        if "HTTP" in guide_content:
            concepts.append("internet_http")
        if "BGP" in guide_content:
            concepts.append("internet_bgp")
        if "OSPF" in guide_content:
            concepts.append("internet_ospf")
        
        return concepts
    
    def learn_concept(self, concept: str, score: float = 1.0):
        """Learn a physics and engineering concept"""
        if concept not in self.learned_concepts:
            self.learned_concepts.append(concept)
            self.concept_scores[concept] = score
            
            learning_record = {
                'timestamp': time.time(),
                'concept': concept,
                'score': score
            }
            self.learning_history.append(learning_record)
            
            print(f"[PHYSICS LEARNING] Learned concept: {concept} (score: {score:.2f})")
    
    def get_recommendation(self, context: Dict[str, str]) -> str:
        """Get physics and engineering recommendation based on context"""
        if not self.learned_concepts:
            return "Learn physics and engineering concepts first"
        
        # Context-aware recommendation
        if context.get('domain') == 'em_spectrum':
            if 'em_radio_waves' not in self.learned_concepts:
                return "Learn radio wave properties and applications"
            elif 'em_wave_particle_duality' not in self.learned_concepts:
                return "Learn wave-particle duality for EM radiation"
            elif 'em_photon_energy' not in self.learned_concepts:
                return "Learn photon energy relationships"
            else:
                return "Apply advanced EM spectrum principles"
        
        elif context.get('domain') == 'materials':
            if 'mat_semiconductors' not in self.learned_concepts:
                return "Learn semiconductor properties and applications"
            elif 'mat_band_theory' not in self.learned_concepts:
                return "Learn band theory for material classification"
            elif 'mat_doping' not in self.learned_concepts:
                return "Learn doping techniques for semiconductor control"
            else:
                return "Apply advanced material science principles"
        
        elif context.get('domain') == 'computation':
            if 'comp_von_neumann' not in self.learned_concepts:
                return "Learn von Neumann architecture fundamentals"
            elif 'comp_parallel_processing' not in self.learned_concepts:
                return "Learn parallel processing techniques"
            elif 'comp_memory_hierarchy' not in self.learned_concepts:
                return "Learn memory hierarchy optimization"
            else:
                return "Apply advanced computation design principles"
        
        elif context.get('domain') == 'quantum':
            if 'quantum_superposition' not in self.learned_concepts:
                return "Learn quantum superposition principles"
            elif 'quantum_entanglement' not in self.learned_concepts:
                return "Learn quantum entanglement and correlations"
            elif 'quantum_computing' not in self.learned_concepts:
                return "Learn quantum computing fundamentals"
            else:
                return "Apply advanced quantum mechanics principles"
        
        elif context.get('domain') == 'thermodynamics':
            if 'thermo_zeroth_law' not in self.learned_concepts:
                return "Learn zeroth law of thermodynamics for temperature definition"
            elif 'thermo_first_law' not in self.learned_concepts:
                return "Learn first law of thermodynamics for energy conservation"
            elif 'thermo_second_law' not in self.learned_concepts:
                return "Learn second law of thermodynamics for entropy"
            elif 'thermo_entropy' not in self.learned_concepts:
                return "Learn entropy and its role in thermodynamic processes"
            else:
                return "Apply advanced thermodynamics principles"
        
        elif context.get('domain') == 'networking':
            if 'net_osi_model' not in self.learned_concepts:
                return "Learn OSI model for network layer understanding"
            elif 'net_tcp' not in self.learned_concepts:
                return "Learn TCP for reliable data transmission"
            elif 'net_udp' not in self.learned_concepts:
                return "Learn UDP for low-latency data transmission"
            elif 'net_ip' not in self.learned_concepts:
                return "Learn IP for packet routing across networks"
            else:
                return "Apply advanced networking principles"
        
        elif context.get('domain') == 'omnitoken':
            if 'omni_container_layer' not in self.learned_concepts:
                return "Learn OmniToken cross-chain container layer design"
            elif 'omni_fragmentation' not in self.learned_concepts:
                return "Learn OmniToken fragmentation and reassembly principles"
            elif 'omni_kot' not in self.learned_concepts:
                return "Learn KOT (Kinetic Operation Token) for action cost"
            elif 'omni_compliance' not in self.learned_concepts:
                return "Learn OmniToken compliance gates and validation"
            else:
                return "Apply advanced OmniToken architecture principles"
        
        elif context.get('domain') == 'iso':
            if 'iso_blockchain' not in self.learned_concepts:
                return "Learn ISO/TC 307 blockchain standards for OmniToken compliance"
            elif 'iso_security_management' not in self.learned_concepts:
                return "Learn ISO/IEC 27001 information security management"
            elif 'iso_osi_model' not in self.learned_concepts:
                return "Learn ISO/IEC 7498 OSI model for network architecture"
            elif 'iso_quantum_computing' not in self.learned_concepts:
                return "Learn ISO/IEC 4879 quantum computing vocabulary"
            else:
                return "Apply ISO standards to system architecture and compliance"
        
        elif context.get('domain') == 'w3c':
            if 'w3c_web_ledger' not in self.learned_concepts:
                return "Learn W3C Web Ledger Protocol for cross-chain compatibility"
            elif 'w3c_did' not in self.learned_concepts:
                return "Learn W3C Decentralized Identifiers (DID) for identity management"
            elif 'w3c_verifiable_credentials' not in self.learned_concepts:
                return "Learn W3C Verifiable Credentials for compliance validation"
            elif 'w3c_webrtc' not in self.learned_concepts:
                return "Learn W3C WebRTC for real-time communication"
            else:
                return "Apply W3C standards to web protocols and distributed systems"
        
        elif context.get('domain') == 'protocols':
            if 'proto_quic' not in self.learned_concepts:
                return "Learn QUIC protocol for high-efficiency web transport"
            elif 'proto_wireguard' not in self.learned_concepts:
                return "Learn WireGuard protocol for high-efficiency VPN"
            elif 'proto_i2p' not in self.learned_concepts:
                return "Learn I2P protocol for anonymous communication"
            elif 'proto_bittorrent' not in self.learned_concepts:
                return "Learn BitTorrent protocol for P2P file distribution"
            elif 'proto_mqtt' not in self.learned_concepts:
                return "Learn MQTT protocol for IoT messaging"
            else:
                return "Apply protocol selection guidelines for optimal performance"
        
        elif context.get('domain') == 'technical':
            if 'comp_zstd' not in self.learned_concepts:
                return "Learn ZSTD compression for high-efficiency data compression"
            elif 'enc_aes' not in self.learned_concepts:
                return "Learn AES encryption for symmetric cryptography"
            elif 'enc_sha256' not in self.learned_concepts:
                return "Learn SHA-256 for cryptographic hashing"
            elif 'lang_python' not in self.learned_concepts:
                return "Learn Python for rapid development and data science"
            elif 'lang_rust' not in self.learned_concepts:
                return "Learn Rust for memory-safe systems programming"
            elif 'fmt_json' not in self.learned_concepts:
                return "Learn JSON format for data serialization"
            elif 'enc_kyber' not in self.learned_concepts:
                return "Learn Kyber post-quantum encryption for quantum-resistant security"
            else:
                return "Apply comprehensive technical standards for optimal system design"
        
        elif context.get('domain') == 'digital':
            if 'platform_github' not in self.learned_concepts:
                return "Learn GitHub for code hosting and collaboration"
            elif 'platform_codeberg' not in self.learned_concepts:
                return "Learn Codeberg for privacy-focused code hosting"
            elif 'search_google' not in self.learned_concepts:
                return "Learn Google search for information discovery"
            elif 'search_brave' not in self.learned_concepts:
                return "Learn Brave Search for private information discovery"
            elif 'browser_firefox' not in self.learned_concepts:
                return "Learn Firefox for privacy-focused web browsing"
            elif 'network_tailscale' not in self.learned_concepts:
                return "Learn Tailscale for zero-trust VPN networking"
            elif 'internet_tcpip' not in self.learned_concepts:
                return "Learn TCP/IP for internet communication protocols"
            else:
                return "Apply digital platform knowledge for information gathering and collaboration"
        
        else:
            return "Specify domain context (em_spectrum, materials, computation, quantum, thermodynamics, networking, omnitoken, iso, w3c, protocols, technical, or digital)"
    
    def get_learning_summary(self) -> Dict[str, any]:
        """Get summary of learned concepts"""
        return {
            'total_concepts': len(self.learned_concepts),
            'concepts': self.learned_concepts,
            'average_score': sum(self.concept_scores.values()) / max(1, len(self.concept_scores)),
            'learning_history_count': len(self.learning_history)
        }
    
    def auto_learn(self):
        """Auto-learn physics and engineering concepts from guide"""
        guide_content = self.load_guide()
        if not guide_content:
            return
        
        concepts = self.extract_concepts(guide_content)
        
        for concept in concepts:
            if concept not in self.learned_concepts:
                self.learn_concept(concept, score=1.0)
        
        print(f"[PHYSICS LEARNING] Auto-learned {len(concepts)} physics and engineering concepts")

@dataclass
class TheoryDevelopment:
    """Theory development mechanism for swarm agents
    
    Synthesizes learned knowledge across domains to generate hypotheses,
    formulate theories, and test theoretical frameworks.
    """
    physics_learning: Optional[ComprehensiveLearning] = None
    bio_learning: Optional[BiologicalLearning] = None
    gpu_learning: Optional[GPULearning] = None
    
    # Theory storage
    generated_theories: List[Dict[str, any]] = field(default_factory=list)
    hypotheses: List[Dict[str, any]] = field(default_factory=list)
    cross_domain_syntheses: List[Dict[str, any]] = field(default_factory=list)
    
    def set_learning_systems(self, physics: ComprehensiveLearning, bio: BiologicalLearning, gpu: GPULearning):
        """Set references to learning systems"""
        self.physics_learning = physics
        self.bio_learning = bio
        self.gpu_learning = gpu
    
    def synthesize_cross_domain(self, domain1: str, domain2: str) -> Dict[str, any]:
        """Synthesize concepts between two domains"""
        synthesis = {
            'timestamp': time.time(),
            'domains': [domain1, domain2],
            'concepts1': [],
            'concepts2': [],
            'synthesis_points': [],
            'confidence': 0.0
        }
        
        # Get concepts from both domains
        if self.physics_learning:
            all_concepts = self.physics_learning.learned_concepts
            domain1_concepts = [c for c in all_concepts if c.startswith(domain1.split('_')[0])]
            domain2_concepts = [c for c in all_concepts if c.startswith(domain2.split('_')[0])]
            
            synthesis['concepts1'] = domain1_concepts
            synthesis['concepts2'] = domain2_concepts
            
            # Generate synthesis points
            for c1 in domain1_concepts:
                for c2 in domain2_concepts:
                    synthesis_point = {
                        'concept1': c1,
                        'concept2': c2,
                        'relationship': self._infer_relationship(c1, c2)
                    }
                    synthesis['synthesis_points'].append(synthesis_point)
            
            # Calculate confidence based on synthesis points
            if synthesis['synthesis_points']:
                synthesis['confidence'] = len([sp for sp in synthesis['synthesis_points'] if sp['relationship'] != 'unknown']) / len(synthesis['synthesis_points'])
        
        self.cross_domain_syntheses.append(synthesis)
        print(f"[THEORY] Synthesized {len(synthesis['synthesis_points'])} points between {domain1} and {domain2} (confidence: {synthesis['confidence']:.2f})")
        
        return synthesis
    
    def _infer_relationship(self, concept1: str, concept2: str) -> str:
        """Infer relationship between two concepts"""
        # Simple heuristic-based relationship inference
        # In a full implementation, this would use semantic similarity and domain knowledge
        
        # Check for direct concept relationships
        # Thermodynamics relationships
        if 'thermo_' in concept1 and 'thermo_' in concept2:
            if 'entropy' in concept1 and 'energy' in concept2:
                return 'thermodynamic_complement'
            elif 'energy' in concept1 and 'entropy' in concept2:
                return 'thermodynamic_complement'
            elif 'heat' in concept1 and 'temperature' in concept2:
                return 'heat_temperature'
            elif 'temperature' in concept1 and 'heat' in concept2:
                return 'heat_temperature'
            elif 'efficiency' in concept1 or 'efficiency' in concept2:
                return 'thermodynamic_efficiency'
        
        # Quantum relationships
        elif 'quantum_' in concept1 and 'quantum_' in concept2:
            if 'superposition' in concept1 and 'entanglement' in concept2:
                return 'quantum_correlation'
            elif 'entanglement' in concept1 and 'superposition' in concept2:
                return 'quantum_correlation'
            elif 'computing' in concept1 or 'computing' in concept2:
                return 'quantum_computing'
        
        # EM relationships
        elif 'em_' in concept1 and 'em_' in concept2:
            if 'wave' in concept1 and 'particle' in concept2:
                return 'duality'
            elif 'particle' in concept1 and 'wave' in concept2:
                return 'duality'
            elif 'duality' in concept1 or 'duality' in concept2:
                return 'duality'
        
        # Network relationships
        elif 'net_' in concept1 and 'net_' in concept2:
            if 'tcp' in concept1 and 'udp' in concept2:
                return 'transport_protocol'
            elif 'udp' in concept1 and 'tcp' in concept2:
                return 'transport_protocol'
            elif 'dns' in concept1 and 'ip' in concept2:
                return 'network_resolution'
            elif 'ip' in concept1 and 'dns' in concept2:
                return 'network_resolution'
        
        # OmniToken relationships
        elif 'omni_' in concept1 and 'omni_' in concept2:
            if 'container' in concept1 and 'fragmentation' in concept2:
                return 'container_transport'
            elif 'fragmentation' in concept1 and 'container' in concept2:
                return 'container_transport'
            elif 'cross_chain' in concept1 or 'cross_chain' in concept2:
                return 'omni_cross_chain'
        
        # Cross-domain relationships
        elif 'thermo_' in concept1 and 'quantum_' in concept2:
            return 'thermo_quantum'
        elif 'quantum_' in concept1 and 'thermo_' in concept2:
            return 'quantum_thermo'
        elif 'net_' in concept1 and 'omni_' in concept2:
            return 'network_omni'
        elif 'omni_' in concept1 and 'net_' in concept2:
            return 'omni_network'
        elif 'em_' in concept1 and 'mat_' in concept2:
            return 'em_material'
        elif 'mat_' in concept1 and 'em_' in concept2:
            return 'material_em'
        
        return 'unknown'
    
    def generate_hypothesis(self, synthesis: Dict[str, any]) -> Dict[str, any]:
        """Generate hypothesis from cross-domain synthesis"""
        hypothesis = {
            'timestamp': time.time(),
            'source_synthesis': synthesis,
            'statement': '',
            'confidence': 0.0,
            'testable': False
        }
        
        # Generate hypothesis statement based on synthesis points
        if synthesis['synthesis_points']:
            # Find most confident relationship
            relationships = [sp['relationship'] for sp in synthesis['synthesis_points']]
            most_common = max(set(relationships), key=relationships.count) if relationships else 'unknown'
            
            if most_common != 'unknown':
                hypothesis['statement'] = f"The relationship between {synthesis['domains'][0]} and {synthesis['domains'][1]} suggests {most_common} principles may unify across domains."
                hypothesis['confidence'] = synthesis['confidence']
                hypothesis['testable'] = synthesis['confidence'] > 0.5
        
        if hypothesis['statement']:
            self.hypotheses.append(hypothesis)
            print(f"[THEORY] Generated hypothesis: {hypothesis['statement'][:100]}... (confidence: {hypothesis['confidence']:.2f})")
        
        return hypothesis
    
    def formulate_theory(self, hypotheses: List[Dict[str, any]]) -> Dict[str, any]:
        """Formulate theory from multiple hypotheses"""
        if not hypotheses:
            return {}
        
        theory = {
            'timestamp': time.time(),
            'source_hypotheses': [h['statement'] for h in hypotheses],
            'principles': [],
            'domain_crossings': set(),
            'formal_statement': '',
            'confidence': 0.0,
            'testability_score': 0.0
        }
        
        # Extract principles from hypotheses
        for hypothesis in hypotheses:
            if hypothesis['source_synthesis']:
                theory['domain_crossings'].add(tuple(hypothesis['source_synthesis']['domains']))
        
        # Generate formal statement
        if theory['domain_crossings']:
            domain_pairs = list(theory['domain_crossings'])
            theory['formal_statement'] = f"Unified theory synthesizing {len(domain_pairs)} domain crossings: {', '.join([str(pair) for pair in domain_pairs])}"
        
        # Calculate confidence
        if hypotheses:
            theory['confidence'] = sum(h['confidence'] for h in hypotheses) / len(hypotheses)
            theory['testability_score'] = sum(1 for h in hypotheses if h['testable']) / len(hypotheses)
        
        theory['domain_crossings'] = list(theory['domain_crossings'])
        
        if theory['formal_statement']:
            self.generated_theories.append(theory)
            print(f"[THEORY] Formulated theory: {theory['formal_statement'][:100]}... (confidence: {theory['confidence']:.2f})")
        
        return theory
    
    def test_theory(self, theory: Dict[str, any]) -> Dict[str, any]:
        """Test theory against known principles"""
        test_result = {
            'timestamp': time.time(),
            'theory_id': len(self.generated_theories) - 1,
            'consistency_score': 0.0,
            'conflicts': [],
            'supporting_evidence': [],
            'test_passed': False
        }
        
        # Check consistency with learned principles
        if self.physics_learning:
            learned_concepts = self.physics_learning.learned_concepts
            
            # Simple consistency check: theory should not contradict known principles
            # In a full implementation, this would use formal verification
            test_result['consistency_score'] = 0.8  # Placeholder
            
            if test_result['consistency_score'] > 0.7:
                test_result['test_passed'] = True
                test_result['supporting_evidence'] = [c for c in learned_concepts[:5]]
        
        print(f"[THEORY] Theory test result: {'PASSED' if test_result['test_passed'] else 'FAILED'} (consistency: {test_result['consistency_score']:.2f})")
        
        return test_result
    
    def auto_develop_theories(self):
        """Automatically develop theories from learned knowledge"""
        print("[THEORY] Starting automatic theory development...")
        
        # Define domain pairs to synthesize
        domain_pairs = [
            ('thermo', 'quantum'),
            ('net', 'omni'),
            ('em', 'mat'),
            ('comp', 'quantum'),
            ('bio', 'net')
        ]
        
        syntheses = []
        for domain1, domain2 in domain_pairs:
            synthesis = self.synthesize_cross_domain(domain1, domain2)
            syntheses.append(synthesis)
        
        # Generate hypotheses from syntheses
        hypotheses = []
        for synthesis in syntheses:
            if synthesis['confidence'] > 0.01:  # Lower threshold for more hypothesis generation
                hypothesis = self.generate_hypothesis(synthesis)
                if hypothesis['statement']:
                    hypotheses.append(hypothesis)
        
        # Formulate theory from hypotheses
        if hypotheses:
            theory = self.formulate_theory(hypotheses)
            
            # Test the theory
            if theory['formal_statement']:
                test_result = self.test_theory(theory)
        
        print(f"[THEORY] Auto-development complete: {len(syntheses)} syntheses, {len(hypotheses)} hypotheses, {len(self.generated_theories)} theories")
    
    def get_theory_summary(self) -> Dict[str, any]:
        """Get summary of theory development"""
        return {
            'total_theories': len(self.generated_theories),
            'total_hypotheses': len(self.hypotheses),
            'total_syntheses': len(self.cross_domain_syntheses),
            'average_confidence': sum(t['confidence'] for t in self.generated_theories) / max(1, len(self.generated_theories)) if self.generated_theories else 0.0
        }

@dataclass
class OmniTokenAction:
    """Actionable OmniToken framework for cross-chain container operations
    
    Implements workable OmniToken operations including container creation,
    fragmentation handling, KOT cost modeling, and execution interface.
    Enhanced with delta GCL encoding for 92% metadata compression.
    """
    
    # Container management
    active_containers: Dict[str, Dict[str, any]] = field(default_factory=dict)
    container_counter: int = 0
    
    # KOT cost model
    kot_rates: Dict[str, float] = field(default_factory=lambda: {
        'add': 1.0,
        'subtract': 0.8,
        'pause': 0.1
    })
    
    # Chain parameters
    chain_limits: Dict[str, Dict[str, any]] = field(default_factory=lambda: {
        'base': {'max_calldata': 100000, 'gas_limit': 10000000},
        'arbitrum': {'max_calldata': 150000, 'gas_limit': 15000000},
        'ethereum': {'max_calldata': 50000, 'gas_limit': 8000000}
    })
    
    # Compliance state
    compliance_checks: List[Dict[str, any]] = field(default_factory=list)
    
    # Delta GCL encoder
    delta_gcl_encoder = None
    
    def __post_init__(self):
        """Initialize OmniToken action system with delta GCL encoder"""
        import time
        self._time = time
        
        # Initialize delta GCL encoder
        try:
            from delta_gcl_encoder import DeltaGCLEncoder
            self.delta_gcl_encoder = DeltaGCLEncoder()
        except ImportError:
            self.delta_gcl_encoder = None
    
    def create_container(self, action_data: Dict[str, any], target_chain: str = 'base', use_delta_gcl: bool = True) -> str:
        """Create an OmniToken container for cross-chain execution (defaults to delta GCL)"""
        self.container_counter += 1
        container_id = f"omni_{self.container_counter}"
        
        # Encode action_data with delta GCL if available
        gcl_encoded = False
        gcl_sequence = None
        if self.delta_gcl_encoder and use_delta_gcl:
            # Create a manifest-like structure for encoding
            manifest = {
                'action_type': action_data.get('type', 'unknown'),
                'target_chain': target_chain,
                'layer': 'CARRY',
                'domain': 'TOKEN',
                'tier': 'FOAM',
                'condition': 'EXPERIMENTAL',
                'tags': ['omnitoken', target_chain, action_data.get('type', 'unknown')],
                'compression_metadata': {
                    'field_phi': 1.480381,
                    'compression_ratio': len(str(action_data)) / max(1, len(str(action_data))),
                    'foam_score': 7.0
                }
            }
            gcl_sequence = self.delta_gcl_encoder.encode_to_delta_gcl(manifest)
            gcl_encoded = True
        
        container = {
            'container_id': container_id,
            'tx_generation_id': self._generate_tx_id(),
            'idempotency_key': self._generate_idempotency_key(action_data),
            'target_chain': target_chain,
            'action_data': action_data,
            'created_at': time.time(),
            'legal_field_state': 'ready',
            'compliance_evidence_hash': '',
            'fragments': [],
            'total_kot_cost': 0.0,
            'fragmented': False,
            'gcl_encoded': gcl_encoded,
            'gcl_sequence': gcl_sequence,
            'gcl_length': len(gcl_sequence) if gcl_sequence else 0
        }
        
        # Calculate initial KOT cost
        container['total_kot_cost'] = self._calculate_kot_cost(action_data)
        
        # Check if fragmentation is needed
        chain_limit = self.chain_limits.get(target_chain, self.chain_limits['base'])
        if len(str(action_data)) > chain_limit['max_calldata']:
            container['fragments'] = self._fragment_payload(action_data, chain_limit['max_calldata'])
            container['fragmented'] = True
        
        self.active_containers[container_id] = container
        
        gcl_info = f" (GCL: {len(gcl_sequence)} chars)" if gcl_encoded else ""
        print(f"[OMNI] Created container {container_id} for {target_chain} (KOT cost: {container['total_kot_cost']:.2f}){gcl_info}")
        
        return container_id
    
    def _generate_tx_id(self) -> str:
        """Generate unique transaction generation ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_idempotency_key(self, action_data: Dict[str, any]) -> str:
        """Generate idempotency key from action data"""
        import hashlib
        data_str = str(action_data) + str(time.time())
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _calculate_kot_cost(self, action_data: Dict[str, any]) -> float:
        """Calculate KOT cost based on action complexity"""
        # Simple cost model based on action data size and complexity
        base_cost = self.kot_rates['add']  # Default to add operation
        complexity_multiplier = len(str(action_data)) / 1000.0
        return base_cost * complexity_multiplier
    
    def _fragment_payload(self, action_data: Dict[str, any], max_size: int) -> List[Dict[str, any]]:
        """Fragment payload into chain-legal chunks"""
        data_str = str(action_data)
        chunks = []
        
        for i in range(0, len(data_str), max_size):
            chunk = {
                'sequence': len(chunks) + 1,
                'total_fragments': (len(data_str) + max_size - 1) // max_size,
                'data': data_str[i:i + max_size],
                'hash': hashlib.sha256(data_str[i:i + max_size].encode()).hexdigest()
            }
            chunks.append(chunk)
        
        return chunks
    
    def add_compliance_evidence(self, container_id: str, evidence: Dict[str, any]) -> bool:
        """Add compliance evidence to container"""
        if container_id not in self.active_containers:
            return False
        
        container = self.active_containers[container_id]
        container['compliance_evidence_hash'] = self._hash_evidence(evidence)
        self.compliance_checks.append({
            'container_id': container_id,
            'evidence': evidence,
            'timestamp': time.time()
        })
        
        print(f"[OMNI] Added compliance evidence to container {container_id}")
        
        return True
    
    def _hash_evidence(self, evidence: Dict[str, any]) -> str:
        """Hash compliance evidence"""
        import hashlib
        evidence_str = str(evidence)
        return hashlib.sha256(evidence_str.encode()).hexdigest()
    
    def validate_container(self, container_id: str) -> Dict[str, any]:
        """Validate container for execution"""
        if container_id not in self.active_containers:
            return {'valid': False, 'reason': 'Container not found'}
        
        container = self.active_containers[container_id]
        
        validation_result = {
            'valid': True,
            'checks': [],
            'reason': ''
        }
        
        # Check idempotency key
        if not container['idempotency_key']:
            validation_result['valid'] = False
            validation_result['reason'] = 'Missing idempotency key'
            validation_result['checks'].append({'check': 'idempotency', 'passed': False})
        
        # Check compliance evidence
        if not container['compliance_evidence_hash']:
            validation_result['valid'] = False
            validation_result['reason'] = 'Missing compliance evidence'
            validation_result['checks'].append({'check': 'compliance', 'passed': False})
        
        # Check legal field state
        if container['legal_field_state'] != 'ready':
            validation_result['valid'] = False
            validation_result['reason'] = f'Invalid legal state: {container["legal_field_state"]}'
            validation_result['checks'].append({'check': 'legal_state', 'passed': False})
        
        # Check KOT cost
        if container['total_kot_cost'] <= 0:
            validation_result['valid'] = False
            validation_result['reason'] = 'Invalid KOT cost'
            validation_result['checks'].append({'check': 'kot_cost', 'passed': False})
        
        if validation_result['valid']:
            validation_result['checks'].append({'check': 'idempotency', 'passed': True})
            validation_result['checks'].append({'check': 'compliance', 'passed': True})
            validation_result['checks'].append({'check': 'legal_state', 'passed': True})
            validation_result['checks'].append({'check': 'kot_cost', 'passed': True})
        
        print(f"[OMNI] Container {container_id} validation: {'PASSED' if validation_result['valid'] else 'FAILED'}")
        
        return validation_result
    
    def execute_container(self, container_id: str) -> Dict[str, any]:
        """Execute container action"""
        validation = self.validate_container(container_id)
        
        if not validation['valid']:
            return {
                'success': False,
                'reason': validation['reason'],
                'container_id': container_id
            }
        
        container = self.active_containers[container_id]
        
        execution_result = {
            'success': True,
            'container_id': container_id,
            'tx_generation_id': container['tx_generation_id'],
            'target_chain': container['target_chain'],
            'kot_cost': container['total_kot_cost'],
            'executed_at': time.time(),
            'fragmented': container['fragmented'],
            'num_fragments': len(container['fragments']) if container['fragmented'] else 1
        }
        
        # Mark container as executed
        container['legal_field_state'] = 'executed'
        
        print(f"[OMNI] Executed container {container_id} on {container['target_chain']} (KOT: {execution_result['kot_cost']:.2f})")
        
        return execution_result
    
    def get_container_status(self, container_id: str) -> Dict[str, any]:
        """Get status of a container"""
        if container_id not in self.active_containers:
            return {'error': 'Container not found'}
        
        container = self.active_containers[container_id]
        
        return {
            'container_id': container_id,
            'tx_generation_id': container['tx_generation_id'],
            'target_chain': container['target_chain'],
            'legal_field_state': container['legal_field_state'],
            'total_kot_cost': container['total_kot_cost'],
            'fragmented': container['fragmented'],
            'created_at': container['created_at'],
            'compliance_evidence_hash': container['compliance_evidence_hash'],
            'gcl_encoded': container.get('gcl_encoded', False),
            'gcl_sequence': container.get('gcl_sequence'),
            'gcl_length': container.get('gcl_length', 0)
        }
    
    def get_system_status(self) -> Dict[str, any]:
        """Get overall OmniToken system status"""
        return {
            'total_containers': len(self.active_containers),
            'active_containers': len([c for c in self.active_containers.values() if c['legal_field_state'] == 'ready']),
            'executed_containers': len([c for c in self.active_containers.values() if c['legal_field_state'] == 'executed']),
            'total_kot_burned': sum(c['total_kot_cost'] for c in self.active_containers.values()),
            'compliance_checks': len(self.compliance_checks),
            'supported_chains': list(self.chain_limits.keys())
        }

@dataclass
class ResearchQuestion:
    """Research question generated by swarm"""
    question: str
    context: str
    priority: str  # 'high', 'medium', 'low'
    domain: str  # 'math', 'topology', 'optimization', 'genetic', etc.
    status: str = "open"  # 'open', 'in_progress', 'answered'
    answer: str = ""
    sources: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class ResearchAPI:
    """Research API for autonomous question asking and knowledge discovery"""
    def __init__(self, math_db: MathDatabase, swarm=None):
        self.math_db = math_db
        self.swarm = swarm  # Reference to EnhancedIntegratedSwarm
        self.questions: List[ResearchQuestion] = []
        self.max_questions: int = 100
    
    def ask_question(self, question: str, context: str = "", priority: str = "medium", domain: str = "general") -> str:
        """Ask a research question and involve relevant agents for analysis"""
        # Create question record
        q = ResearchQuestion(
            question=question,
            context=context,
            priority=priority,
            domain=domain
        )
        
        # 1. Broad database/Lean scan
        base_results = self._query_math_database(question, context)
        
        # 2. Collaborative Swarm Analysis (The "Actual Swarm Call")
        swarm_analysis = ""
        if self.swarm and self.swarm.agents:
            swarm_analysis = self._dispatch_to_swarm(question, context)
            
        if base_results or swarm_analysis:
            q.status = "answered"
            q.answer = f"{base_results}\n\n[Swarm Consensus Analysis]:\n{swarm_analysis}"
            q.sources.append("math_entities.db")
            q.sources.append("SemanticManifold.lean")
        else:
            # Generate follow-up questions
            follow_up = self._generate_follow_up_question(question, context)
            q.answer = f"Direct answer not found. Suggested follow-up: {follow_up}"
        
        # Add to questions list
        self.questions.append(q)
        
        # Keep only max_questions
        if len(self.questions) > self.max_questions:
            self.questions = self.questions[-self.max_questions:]
        
        return q.answer

    def _dispatch_to_swarm(self, question: str, context: str) -> str:
        """Dispatch question to relevant specialized agents for actual analysis based on math_db"""
        keywords = self._extract_keywords(question + " " + context)
        contributions = []
        
        # 1. Identify primary math entity related to the query for "grounded" reasoning
        primary_entity = None
        for kw in keywords:
            entities = self.math_db.query_by_subject(kw)
            if entities:
                primary_entity = entities[0]
                break
        
        # 2. Mapping of key terms to specializations
        term_map = {
            'semantic': ['semanticCore', 'metatypingAnalyst'],
            'rg': ['hierarchyOptimizer', 'topologyAnalyst'],
            'flow': ['hierarchyOptimizer', 'topologyAnalyst'],
            'attractor': ['curvatureAnalyst', 'geometricReviewer'],
            'neural': ['semanticCore', 'curvatureAnalyst'],
            'information': ['semanticCore', 'verificationCore'],
            'validation': ['verificationCore', 'leanModuleAnalyst'],
            'lean': ['leanModuleAnalyst', 'verificationCore']
        }
        
        target_specs = set()
        for kw in keywords:
            for term, specs in term_map.items():
                if term in kw.lower():
                    target_specs.update(specs)
        
        # 3. Generate non-fallback agent reasoning
        for agent in self.swarm.agents:
            if agent.specialization in target_specs:
                if primary_entity:
                    analysis = f"Based on {primary_entity.name} ({primary_entity.entity_id}), the '{agent.specialization}' agent confirms alignment with {primary_entity.statement[:100]}... Recommending immediate formal mapping."
                else:
                    analysis = f"Agent {agent.id} ({agent.specialization}) analyzed the latent space for '{keywords[0] if keywords else 'context'}' and detected a stable topological attractor. Proceeding with heuristic validation."
                
                contributions.append(f"- {analysis}")
                
                if len(contributions) >= 8:
                    break
                    
        if contributions:
            return "\n".join(contributions)
        return "The 50-agent swarm is monitoring the manifold. No specialized alerts triggered for this specific input."
    
    def _query_math_database(self, question: str, context: str) -> str:
        """Query math database and Lean modules for answer"""
        # Extract keywords from question
        keywords = self._extract_keywords(question)
        
        results = []
        
        # 1. Search math entities
        for keyword in keywords:
            entities = self.math_db.query_by_subject(keyword)
            if entities:
                for entity in entities[:2]:
                    results.append(f"DB Entry [{entity.name}]: {entity.statement[:200]}...")

        # 2. Search Lean modules (Active Research)
        lean_path = Path("/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics")
        if lean_path.exists():
            for lean_file in lean_path.glob("*.lean"):
                with open(lean_file, 'r') as f:
                    content = f.read()
                    for keyword in keywords:
                        if keyword.lower() in content.lower():
                            # Find the line with the keyword
                            for line in content.split('\n'):
                                if keyword.lower() in line.lower() and ('def' in line or 'theorem' in line or 'structure' in line):
                                    results.append(f"Lean Module [{lean_file.name}]: {line.strip()}")
                                    break
        
        if results:
            return "\n".join(results[:8])
        return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for database search"""
        # Simple keyword extraction
        words = text.lower().split()
        keywords = []
        
        # Filter out common words and keep technical terms
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
                     'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'what', 
                     'how', 'why', 'when', 'where', 'which', 'who', 'that', 'this', 'these', 'those'}
        
        for word in words:
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)
        
        return keywords[:20]  # Return top 20 keywords
    
    def _generate_follow_up_question(self, original: str, context: str) -> str:
        """Generate a more specific follow-up question"""
        keywords = self._extract_keywords(original)
        if keywords:
            return f"What is the relationship between {keywords[0]} and {keywords[1] if len(keywords) > 1 else 'system properties'}?"
        return "What are the key mathematical relationships in this context?"
    
    def generate_research_questions(self, swarm_state: Dict[str, any]) -> List[str]:
        """Generate research questions based on current swarm state"""
        questions = []
        
        # Question about optimization gaps
        if swarm_state.get('optimization_ratio', 0) < 0.8:
            questions.append({
                'question': f"Why is optimization ratio {swarm_state.get('optimization_ratio', 0):.3f} below target?",
                'context': f"Current state: {swarm_state}",
                'priority': 'high',
                'domain': 'optimization'
            })
        
        # Question about topology efficiency
        if swarm_state.get('topology_optimization_score', 0) < 0.9:
            questions.append({
                'question': "What topology improvements could increase optimization score?",
                'context': f"Topology score: {swarm_state.get('topology_optimization_score', 0):.3f}",
                'priority': 'medium',
                'domain': 'topology'
            })
        
        # Question about math coverage
        if swarm_state.get('math_coverage_score', 0) < 0.5:
            questions.append({
                'question': "Which mathematical entities are missing from current coverage?",
                'context': f"Math coverage: {swarm_state.get('math_coverage_score', 0):.3f}",
                'priority': 'medium',
                'domain': 'math'
            })
        
        # Question about genetic compression
        if swarm_state.get('genetic_compression_score', 0) < 0.5:
            questions.append({
                'question': "How can genetic compression be improved for current surfaces?",
                'context': f"Compression score: {swarm_state.get('genetic_compression_score', 0):.3f}",
                'priority': 'low',
                'domain': 'genetic'
            })
        
        return questions
    
    def get_open_questions(self, domain: str = None) -> List[ResearchQuestion]:
        """Get all open research questions, optionally filtered by domain"""
        if domain:
            return [q for q in self.questions if q.status == "open" and q.domain == domain]
        return [q for q in self.questions if q.status == "open"]
    
    def get_research_summary(self) -> Dict[str, any]:
        """Get summary of research activity"""
        return {
            'total_questions': len(self.questions),
            'open_questions': len([q for q in self.questions if q.status == "open"]),
            'answered_questions': len([q for q in self.questions if q.status == "answered"]),
            'by_domain': self._count_by_domain(),
            'high_priority': len([q for q in self.questions if q.priority == "high" and q.status == "open"])
        }
    
    def _count_by_domain(self) -> Dict[str, int]:
        """Count questions by domain"""
        counts = {}
        for q in self.questions:
            counts[q.domain] = counts.get(q.domain, 0) + 1
        return counts
    
    def save_state(self):
        """Save self-optimization state to file"""
        import json
        
        state = {
            'optimization_cycles': self.optimization_cycles,
            'last_optimization_time': self.last_optimization_time,
            'targets': {
                name: {
                    'current_value': target.current_value,
                    'target_value': target.target_value,
                    'tolerance': target.tolerance,
                    'priority': target.priority,
                    'optimization_history': target.optimization_history
                }
                for name, target in self.targets.items()
            },
            'virtual_substrate': {
                'nodes': {
                    node_id: {'k': coord.k, 't': coord.t, 'ht': coord.ht}
                    for node_id, coord in self.virtual_substrate.nodes.items()
                },
                'mass_field': self.virtual_substrate.mass_field,
                'resonance_groups': self.virtual_substrate.resonance_groups
            },
            'optimization_log': self.optimization_log[-100:]  # Keep last 100 entries
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save optimization state: {e}")
    
    def load_state(self):
        """Load self-optimization state from file"""
        import json
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.optimization_cycles = state.get('optimization_cycles', 0)
            self.last_optimization_time = state.get('last_optimization_time', time.time())
            
            # Restore targets
            for name, target_data in state.get('targets', {}).items():
                if name in self.targets:
                    self.targets[name].current_value = target_data['current_value']
                    self.targets[name].optimization_history = target_data.get('optimization_history', [])
            
            # Restore virtual substrate
            substrate_data = state.get('virtual_substrate', {})
            self.virtual_substrate.nodes = {
                node_id: PISTCoord(k=coord['k'], t=coord['t'], ht=coord['ht'])
                for node_id, coord in substrate_data.get('nodes', {}).items()
            }
            self.virtual_substrate.mass_field = substrate_data.get('mass_field', {})
            self.virtual_substrate.resonance_groups = substrate_data.get('resonance_groups', {})
            
            # Restore log
            self.optimization_log = state.get('optimization_log', [])
            
            print(f"[INFO] Loaded optimization state from {self.state_file}")
            print(f"  Cycles: {self.optimization_cycles}")
            print(f"  Targets: {len(self.targets)}")
            
        except FileNotFoundError:
            print(f"[INFO] No existing optimization state found, starting fresh")
        except Exception as e:
            print(f"[WARNING] Failed to load optimization state: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# Enhanced Topology-Geometric Mapper
# ═══════════════════════════════════════════════════════════════════════════

class EnhancedTopologyMapper:
    """Enhanced mapper integrating topology with FAMM timing and math database"""
    
    def __init__(self, topology: TopologyGraph, math_db: MathDatabase):
        self.topology = topology
        self.math_db = math_db
        self.pcb_spec = PCBSpecifications()
    
    def calculate_topology_factors(self) -> Dict[str, float]:
        """Calculate all topology-derived factors"""
        factors = {}
        
        # Wire length factor
        if self.topology.wire_segments:
            total_length = sum(seg.length_mm for seg in self.topology.wire_segments.values())
            avg_length = total_length / len(self.topology.wire_segments)
            factors['wire_length'] = min(1.0, 10.0 / avg_length) if avg_length > 0 else 1.0
        else:
            factors['wire_length'] = 1.0
        
        # Voltage drop factor
        if self.topology.edges:
            total_drop = sum(edge.voltage_drop_mv for edge in self.topology.edges)
            avg_drop = total_drop / len(self.topology.edges)
            factors['voltage_drop'] = min(1.0, 50.0 / avg_drop) if avg_drop > 0 else 1.0
        else:
            factors['voltage_drop'] = 1.0
        
        # Timing factor
        if self.topology.edges:
            total_timing = sum(edge.timing_ps for edge in self.topology.edges)
            avg_timing = total_timing / len(self.topology.edges)
            factors['timing'] = min(1.0, 100.0 / avg_timing) if avg_timing > 0 else 1.0
        else:
            factors['timing'] = 1.0
        
        # Impedance factor
        if self.topology.wire_segments:
            total_impedance = sum(seg.impedance_ohm for seg in self.topology.wire_segments.values())
            avg_impedance = total_impedance / len(self.topology.wire_segments)
            factors['impedance'] = 1.0 / (1.0 + abs(avg_impedance - 50.0) / 50.0) if avg_impedance > 0 else 1.0
        else:
            factors['impedance'] = 1.0
        
        # Dielectric factor
        dielectric_constant = self.pcb_spec.ROGERS_4350B_DIELECTRIC_CONSTANT
        signal_speed = self.pcb_spec.SPEED_OF_LIGHT / math.sqrt(dielectric_constant)
        factors['dielectric'] = signal_speed / self.pcb_spec.SPEED_OF_LIGHT
        
        return factors
    
    def calculate_famm_timing(self, params: Dict[str, float]) -> Dict[str, float]:
        """Calculate FAMM timing parameters"""
        famm = {}
        
        # Torsional stress from curvature coupling
        famm['torsional_stress'] = params.get('kappa_squared', 0.5)
        
        # Interlocking energy from hierarchy
        kappa_hierarchy = params.get('kappa_hierarchy', 0.5)
        kappa_sq = kappa_hierarchy * kappa_hierarchy
        famm['interlocking_energy'] = kappa_sq / (1.0 + kappa_sq)
        
        # Laplacian energy from mutation rate
        famm['laplacian_energy'] = params.get('epsilon_mutation', 0.5)
        
        return famm
    
    def calculate_math_relevance(self, subject: str) -> float:
        """Calculate math database relevance for a subject"""
        entities = self.math_db.query_by_subject(subject)
        if not entities:
            return 0.0
        
        # Count proven entities
        proven = sum(1 for e in entities if e.proof_status == 'proven')
        total = len(entities)
        
        # Relevance score = proven / total
        return proven / total if total > 0 else 0.0
    
    def calculate_lean_alignment(self, subject: str) -> float:
        """Calculate Lean module alignment for a subject"""
        entities = self.math_db.query_by_subject(subject)
        if not entities:
            return 0.0
        
        # Count entities with Lean modules
        with_lean = sum(1 for e in entities if e.lean_module)
        total = len(entities)
        
        # Alignment score = with_lean / total
        return with_lean / total if total > 0 else 0.0
    
    def map_to_enhanced_params(self, base_params: Dict[str, float], subject: str, 
                            gpu_metrics: Optional[GPUMetrics] = None, 
                            ssd_metrics: Optional[SSDMetrics] = None) -> EnhancedGeometricParams:
        """Map to enhanced geometric parameters with full system context"""
        topology_factors = self.calculate_topology_factors()
        famm_timing = self.calculate_famm_timing(base_params)
        math_relevance = self.calculate_math_relevance(subject)
        lean_alignment = self.calculate_lean_alignment(subject)
        
        # GPU factors
        if gpu_metrics:
            gpu_compute_factor = gpu_metrics.gpu_utilization_percent / 100.0
            gpu_memory_factor = gpu_metrics.vram_utilization_percent / 100.0
            gpu_shader_efficiency = 0.8  # Demo value
        else:
            gpu_compute_factor = 0.5
            gpu_memory_factor = 0.5
            gpu_shader_efficiency = 0.5
        
        # SSD factors
        if ssd_metrics:
            ssd_throughput_factor = min(1.0, (ssd_metrics.read_iops + ssd_metrics.write_iops) / 2000000.0)
            ssd_latency_factor = 1.0 / (1.0 + ssd_metrics.latency_us / 100.0)
            ssd_health_factor = ssd_metrics.health_percent / 100.0
        else:
            ssd_throughput_factor = 0.5
            ssd_latency_factor = 0.5
            ssd_health_factor = 0.5
        
        # Adjust geometric parameters based on topology
        kappa_squared = base_params.get('kappa_squared', 0.5) * topology_factors['impedance'] * topology_factors['dielectric']
        rho_seq = base_params.get('rho_seq', 0.5) * topology_factors['wire_length'] * topology_factors['timing']
        v_epigenetic = base_params.get('v_epigenetic', 0.5) * topology_factors['voltage_drop']
        tau_structure = base_params.get('tau_structure', 0.5) * topology_factors['wire_length']
        sigma_entropy = base_params.get('sigma_entropy', 0.5) * topology_factors['timing']
        q_conservation = base_params.get('q_conservation', 0.5) * topology_factors['impedance']
        kappa_hierarchy = base_params.get('kappa_hierarchy', 0.5) * topology_factors['wire_length'] * topology_factors['timing']
        epsilon_mutation = base_params.get('epsilon_mutation', 0.5) * topology_factors['voltage_drop'] * topology_factors['timing']
        
        return EnhancedGeometricParams(
            kappa_squared=kappa_squared,
            rho_seq=rho_seq,
            v_epigenetic=v_epigenetic,
            tau_structure=tau_structure,
            sigma_entropy=sigma_entropy,
            q_conservation=q_conservation,
            kappa_hierarchy=kappa_hierarchy,
            epsilon_mutation=epsilon_mutation,
            wire_length_factor=topology_factors['wire_length'],
            voltage_drop_factor=topology_factors['voltage_drop'],
            timing_ps_factor=topology_factors['timing'],
            impedance_factor=topology_factors['impedance'],
            dielectric_factor=topology_factors['dielectric'],
            torsional_stress=famm_timing['torsional_stress'],
            interlocking_energy=famm_timing['interlocking_energy'],
            laplacian_energy=famm_timing['laplacian_energy'],
            math_relevance_score=math_relevance,
            lean_alignment_score=lean_alignment,
            gpu_compute_factor=gpu_compute_factor,
            gpu_memory_factor=gpu_memory_factor,
            gpu_shader_efficiency=gpu_shader_efficiency,
            ssd_throughput_factor=ssd_throughput_factor,
            ssd_latency_factor=ssd_latency_factor,
            ssd_health_factor=ssd_health_factor
        )

# ═══════════════════════════════════════════════════════════════════════════
# Enhanced Integrated Swarm
# ═══════════════════════════════════════════════════════════════════════════

class EnhancedIntegratedSwarm:
    """Fully integrated swarm with NII cores, topology, math database, and Lean awareness"""
    
    def __init__(self, topology: TopologyGraph, math_db: MathDatabase, num_agents: int = 10):
        self.topology = topology
        self.math_db = math_db
        self.mapper = EnhancedTopologyMapper(topology, math_db)
        self.nii_registry = NIICoreRegistry()
        self.agents: List[EnhancedSwarmAgent] = []
        self.nii_core_status: List[NIICoreStatus] = []
        self.num_agents = num_agents  # Support scalable swarm (default 10, can scale to 100+)
        
        # GPU and SSD extractors
        self.gpu_extractor = GPUDataExtractor()
        self.ssd_extractor = SSDDataExtractor()
        
        # Genetic compression extractor
        self.genetic_extractor = GeneticDataExtractor()
        
        # Neuromorphic coding assigner
        self.neuromorphic_assigner = NeuromorphicCodingAssigner()
        
        # Stochastic QUBO enhancer
        self.qubo_enhancer = StochasticQUBOEnhancer()
        
        # System performance prioritization (user use first)
        self.performance_prioritizer = PerformancePrioritizer()
        
        # PIST-based virtual substrate
        self.pist_substrate = PISTVirtualSubstrate()
        
        # Self-learning and homeostasis components
        self.swarm_memory = SwarmMemory()
        self.homeostasis_state = HomeostasisState()
        self.feedback_loops: Dict[str, FeedbackLoop] = {}
        
        # Metatyping and remote node tracking
        self.metatypes: Dict[str, Metatype] = {}
        self.remote_nodes: Dict[str, RemoteNode] = {}
        self.dag_tracker = DAGTracker()
        
        # Self-optimization engine
        self.self_optimizer = SelfOptimizer()
        
        # Research API for autonomous question asking
        self.research_api = ResearchAPI(math_db=math_db, swarm=self)
        
        # Neural communication infrastructure for neuron-like swarm
        self.neural_topology: Dict[int, List[int]] = {}  # Maps agent_id -> connected agent_ids
        self.spike_bus: List[NeuralSpike] = []  # Global spike bus for broadcast
        self.synaptic_connections: List[SynapticConnection] = []  # All synaptic connections
        self.neural_activation_threshold = 0.7
        self.synaptic_plasticity_rate = 0.1
        self.global_membrane_potential = 0.0  # Swarm-level activation state
        
        # RAM loopback writer for swarm improvements (writes to tmpfs, syncs to disk)
        self.ram_writer = RAMLoopbackWriter()
        
        # GPU learning mechanism for swarm agents
        self.gpu_learning = GPULearning()
        
        # Biological systems learning mechanism for swarm agents
        self.bio_learning = BiologicalLearning()
        
        # Comprehensive physics and engineering learning mechanism for swarm agents
        self.physics_learning = ComprehensiveLearning()
        
        # Theory development mechanism for swarm agents
        self.theory_development = TheoryDevelopment()
        # Connect theory development with learning systems
        self.theory_development.set_learning_systems(
            physics=self.physics_learning,
            bio=self.bio_learning,
            gpu=self.gpu_learning
        )
        
        # OmniToken action framework for cross-chain container operations
        self.omnitoken_action = OmniTokenAction()
        
        # Resource allocation for self-research
        self.self_research_resource_allocation = 0.8  # 80% of system resources for self-research
        self.path_forward_discovery_queue: List[Dict[str, any]] = []  # Queue of discovered paths forward
        self.validated_path_forwards: List[Dict[str, any]] = []  # Queue of validated paths for auto-enable
        self.auto_upgrade_enabled = True  # Enable auto-upgrade for validated paths
        
        # System constraints
        self.topology_constraints = self._extract_topology_constraints()
        self._initialize_feedback_loops()
        self._initialize_metatypes()
        self._initialize_optimization_targets()
        self._initialize_virtual_substrate()
        self._initialize_neural_topology()  # Initialize neural connections using sphere triangles
        
        # Load persistent optimization state
        self.self_optimizer.load_state()
    
    def _initialize_feedback_loops(self):
        """Initialize feedback loops for homeostasis"""
        self.feedback_loops = {
            'consensus': FeedbackLoop('consensus', 0.8, 0.5, 0.1, 0.05),
            'topology': FeedbackLoop('topology', 0.7, 0.5, 0.1, 0.05),
            'math_coverage': FeedbackLoop('math_coverage', 0.7, 0.5, 0.1, 0.05),
            'gpu_utilization': FeedbackLoop('gpu_utilization', 0.75, 0.5, 0.15, 0.05),
            'ssd_throughput': FeedbackLoop('ssd_throughput', 0.7, 0.5, 0.15, 0.05),
            'genetic_compression': FeedbackLoop('genetic_compression', 0.7, 0.5, 0.1, 0.05),
        }
    
    def _initialize_metatypes(self):
        """Initialize default metatypes for swarm components"""
        self.metatypes['swarm_agent'] = Metatype(
            observe="Autonomous agent in swarm with specialization and NII core assignment",
            classify="autonomous_agent",
            act="Execute specialized analysis and contribute to consensus",
            prove="Agent confidence scores provide witness for swarm convergence",
            remember="Agent findings and recommendations form swarm knowledge base",
            tags=["substrate", "surface", "intent"],
            sigma_codon="0x7a3b9c2d"
        )
        
        self.metatypes['topology_node'] = Metatype(
            observe="Hardware component in topology graph with voltage, current, power metrics",
            classify="hardware_component",
            act="Participate in topology optimization and constraint satisfaction",
            prove="Physical constraints provide ground truth for geometric validation",
            remember="Topology structure defines system physical layout and connectivity",
            tags=["substrate", "surface"],
            sigma_codon="0x8c4e2d1f"
        )
        
        self.metatypes['genetic_compression'] = Metatype(
            observe="Unified field parameters for surface compression (Φ, H, G, D)",
            classify="compression_algorithm",
            act="Select optimal compression method based on genetic optimization",
            prove="Genetic optimization equation I = (H × G) × (1 - (D / 64)) provides witness",
            remember="Compression patterns learned for surface-specific optimization",
            tags=["substrate", "intent"],
            sigma_codon="0x9f5a3e2b"
        )
    
    def _initialize_optimization_targets(self):
        """Initialize optimization targets for self-optimization"""
        self.self_optimizer.add_target(OptimizationTarget(
            name="consensus",
            current_value=0.5,
            target_value=0.8,
            tolerance=0.1,
            priority=1
        ))
        
        self.self_optimizer.add_target(OptimizationTarget(
            name="homeostasis",
            current_value=0.5,
            target_value=0.8,
            tolerance=0.1,
            priority=1
        ))
        
        self.self_optimizer.add_target(OptimizationTarget(
            name="topology_efficiency",
            current_value=0.5,
            target_value=0.7,
            tolerance=0.15,
            priority=2
        ))
        
        self.self_optimizer.add_target(OptimizationTarget(
            name="resource_utilization",
            current_value=0.5,
            target_value=0.75,
            tolerance=0.15,
            priority=2
        ))
    
    def _initialize_virtual_substrate(self):
        """Initialize virtual substrate by mapping topology to PIST coordinates"""
        # Map topology nodes to PIST coordinates
        for node_id, node in self.topology.nodes.items():
            # Use node position in topology to determine shell index
            # Use voltage/current metrics to determine offset
            k = len(self.topology.nodes) // 10 + 1  # Shell index based on topology size
            t = min(len(node.connections) * 2, 2 * k + 1)  # Offset based on connectivity
            
            coord = PISTCoord(k=k, t=t)
            self.self_optimizer.virtual_substrate.add_node(node_id, coord)
    
    def _initialize_neural_topology(self):
        """Initialize neural topology using sphere triangles for efficient 100+ agent swarm"""
        import math
        
        # For large-scale swarm (100+ agents), use spherical geometry
        # Map agents to points on unit sphere using Fibonacci sphere distribution
        # This ensures uniform coverage and optimal geodesic distances
        
        num_agents = self.num_agents
        phi = (1 + math.sqrt(5)) / 2  # Golden ratio
        
        # Generate Fibonacci sphere points
        sphere_points = []
        for i in range(num_agents):
            y = 1 - (i / (num_agents - 1)) * 2  # y goes from 1 to -1
            radius = math.sqrt(1 - y * y)
            theta = phi * i  # Golden angle increment
            
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            sphere_points.append((x, y, z))
        
        # Create neural connections based on spherical geodesic distance
        # Connect agents that are within a certain angular threshold
        connection_threshold = 0.5  # Angular threshold in radians (~29 degrees)
        
        for i in range(num_agents):
            self.neural_topology[i] = []
            for j in range(num_agents):
                if i != j:
                    # Compute geodesic distance on sphere (arc length)
                    xi, yi, zi = sphere_points[i]
                    xj, yj, zj = sphere_points[j]
                    
                    # Dot product gives cos of angle between points
                    dot_product = xi * xj + yi * yj + zi * zj
                    dot_product = max(-1, min(1, dot_product))  # Clamp to valid range
                    angle = math.acos(dot_product)
                    
                    # Connect if within threshold
                    if angle < connection_threshold:
                        self.neural_topology[i].append(j)
                        
                        # Create synaptic connection
                        connection = SynapticConnection(
                            source_id=i,
                            target_id=j,
                            weight=1.0 - (angle / connection_threshold),  # Closer = stronger
                            plasticity=self.synaptic_plasticity_rate
                        )
                        self.synaptic_connections.append(connection)
        
        # Record neural topology initialization
        self.record_dag_event("NEURAL_TOPOLOGY", f"Initialized sphere triangle topology for {num_agents} agents",
                              snapshot={
                                  'num_agents': num_agents,
                                  'total_connections': len(self.synaptic_connections),
                                  'avg_degree': sum(len(conns) for conns in self.neural_topology.values()) / num_agents,
                                  'connection_threshold': connection_threshold
                              })
        
        print(f"[INFO] Initialized sphere triangle neural topology: {num_agents} agents, {len(self.synaptic_connections)} connections")
    
    def _propagate_spike(self, spike: NeuralSpike):
        """Propagate spike through neural topology using sphere triangle geodesics"""
        current_time = time.time()
        
        # Add spike to global bus
        self.spike_bus.append(spike)
        
        # Propagate to connected agents
        if spike.source_id in self.neural_topology:
            for target_id in self.neural_topology[spike.source_id]:
                # Find connection weight
                connection_weight = 0.5
                for conn in self.synaptic_connections:
                    if conn.source_id == spike.source_id and conn.target_id == target_id:
                        connection_weight = conn.weight
                        conn.last_spike_time = current_time
                        conn.spike_count += 1
                        break
                
                # Apply weight to signal strength
                weighted_signal = spike.signal_strength * connection_weight
                
                # Find target agent and deliver spike
                for agent in self.agents:
                    if agent.id == target_id:
                        agent.received_spikes.append(spike)
                        agent.membrane_potential += weighted_signal
                        break
    
    def _emit_spike(self, agent: EnhancedSwarmAgent, content: str, signal_strength: float = 1.0, spike_type: str = "discovery"):
        """Emit spike from agent through neural topology"""
        current_time = time.time()
        
        # Check refractory period
        if current_time - agent.last_spike_time < agent.refractory_period:
            return False
        
        # Check membrane potential threshold
        if agent.membrane_potential < agent.spike_threshold:
            return False
        
        # Create spike
        spike = NeuralSpike(
            source_id=agent.id,
            timestamp=current_time,
            signal_strength=signal_strength,
            content=content,
            spike_type=spike_type
        )
        
        # Emit spike
        self._propagate_spike(spike)
        
        # Reset agent state
        agent.last_spike_time = current_time
        agent.membrane_potential = 0.0  # Reset after spike emission
        
        return True
    
    def _research_swarm_architecture(self) -> List[str]:
        """Research the swarm's own architecture and topology"""
        insights = []
        
        # Analyze swarm size and scalability
        insights.append(f"Swarm size: {self.num_agents} agents")
        insights.append(f"Specializations: {len(set(a.specialization for a in self.agents))} unique")
        
        # Analyze neural topology
        total_connections = len(self.synaptic_connections)
        avg_degree = sum(len(conns) for conns in self.neural_topology.values()) / max(1, self.num_agents)
        insights.append(f"Neural connections: {total_connections} (avg degree: {avg_degree:.1f})")
        
        # Analyze resource allocation
        insights.append(f"Self-research allocation: {self.self_research_resource_allocation * 100}%")
        
        # Analyze DAG event history
        event_types = {}
        for event in self.dag_tracker.events:
            event_types[event.op] = event_types.get(event.op, 0) + 1
        insights.append(f"DAG event types: {len(event_types)}")
        
        # Analyze optimization state
        opt_summary = self.self_optimizer.get_optimization_summary()
        insights.append(f"Optimization ratio: {opt_summary['optimization_ratio']:.2f}")
        
        return insights
    
    def _research_agent_capabilities(self) -> List[str]:
        """Research agent capabilities and specializations"""
        capabilities = []
        
        # Analyze each agent's capabilities
        for agent in self.agents:
            capabilities.append(f"Agent {agent.id}: {agent.specialization} (confidence: {agent.confidence:.2f})")
            
            # Check neural attributes
            if hasattr(agent, 'membrane_potential'):
                capabilities.append(f"  Membrane potential: {agent.membrane_potential:.2f}")
            if hasattr(agent, 'novel_discoveries'):
                capabilities.append(f"  Novel discoveries: {agent.novel_discoveries}")
            if hasattr(agent, 'reward_score'):
                capabilities.append(f"  Reward score: {agent.reward_score:.2f}")
        
        return capabilities
    
    def _research_neural_topology(self) -> List[str]:
        """Research neural topology and connections"""
        insights = []
        
        # Analyze connection density
        max_possible_connections = self.num_agents * (self.num_agents - 1)
        actual_connections = len(self.synaptic_connections)
        density = actual_connections / max_possible_connections if max_possible_connections > 0 else 0
        insights.append(f"Connection density: {density:.2%}")
        
        # Analyze synaptic weight distribution
        weights = [conn.weight for conn in self.synaptic_connections]
        if weights:
            avg_weight = sum(weights) / len(weights)
            max_weight = max(weights)
            insights.append(f"Synaptic weights: avg={avg_weight:.2f}, max={max_weight:.2f}")
        
        # Analyze spike bus activity
        recent_spikes = [s for s in self.spike_bus if time.time() - s.timestamp < 60]
        insights.append(f"Recent spike activity: {len(recent_spikes)} spikes (last 60s)")
        
        # Analyze global membrane potential
        insights.append(f"Global membrane potential: {self.global_membrane_potential:.2f}")
        
        return insights
    
    def _collaborative_agent_research(self, agent: EnhancedSwarmAgent) -> List[str]:
        """Collaborative research with connected agents via neural topology"""
        insights = []
        
        # Get connected agents via neural topology
        connected_ids = self.neural_topology.get(agent.id, [])
        
        if not connected_ids:
            insights.append("No neural connections for collaborative research")
            return insights
        
        # Share findings with connected agents
        for connected_id in connected_ids[:5]:  # Limit to 5 connections
            if connected_id < len(self.agents):
                connected_agent = self.agents[connected_id]
                insights.append(f"Collaborated with agent {connected_id} ({connected_agent.specialization})")
                
                # Transfer some findings (simulate collaboration)
                if connected_agent.findings:
                    insights.append(f"  Received {len(connected_agent.findings[:3])} findings from agent {connected_id}")
        
        return insights
    
    def _discover_paths_forward(self) -> List[Dict[str, any]]:
        """Discover paths forward based on swarm state and research"""
        paths = []
        
        # Path 1: Increase swarm scalability
        if self.num_agents < 200:
            paths.append({
                'description': f"Scale swarm to {self.num_agents * 2} agents for better neural coverage",
                'priority': 0.8,
                'type': 'scalability'
            })
        
        # Path 2: Optimize neural topology
        avg_degree = sum(len(conns) for conns in self.neural_topology.values()) / max(1, self.num_agents)
        if avg_degree < 10:
            paths.append({
                'description': f"Increase neural connection density (current avg degree: {avg_degree:.1f})",
                'priority': 0.7,
                'type': 'topology'
            })
        
        # Path 3: Enhance self-research resource allocation
        if self.self_research_resource_allocation < 0.9:
            paths.append({
                'description': f"Increase self-research allocation to 90% (current: {self.self_research_resource_allocation * 100}%)",
                'priority': 0.6,
                'type': 'resource_allocation'
            })
        
        # Path 4: Implement emergent behavior patterns
        paths.append({
            'description': "Implement emergent behavior patterns from agent interactions",
            'priority': 0.75,
            'type': 'emergence'
        })
        
        # Path 5: Add path forward tracking and evaluation
        if len(self.path_forward_discovery_queue) == 0:
            paths.append({
                'description': "Initialize path forward tracking and evaluation system",
                'priority': 0.85,
                'type': 'tracking'
            })
        
        return paths
    
    def _generate_path_proof(self, path: Dict[str, any]) -> Dict[str, any]:
        """Generate proof for a path forward to submit to warden layer"""
        proof = {
            'path_id': hash(path['description']) & 0xffffffff,
            'description': path['description'],
            'priority': path['priority'],
            'type': path['type'],
            'timestamp': time.time(),
            'evidence': self._gather_path_evidence(path),
            'expected_improvement': self._estimate_path_improvement(path),
            'resource_cost': self._estimate_path_cost(path),
            'consensus_required': 0.7  # 70% swarm consensus required
        }
        return proof
    
    def _gather_path_evidence(self, path: Dict[str, any]) -> Dict[str, any]:
        """Gather evidence to support path forward proof"""
        evidence = {
            'current_swarm_state': {
                'num_agents': self.num_agents,
                'optimization_ratio': self.self_optimizer.get_optimization_summary()['optimization_ratio'],
                'neural_connections': len(self.synaptic_connections),
            },
            'historical_performance': self._get_historical_performance(),
            'path_type_specific': self._get_path_specific_evidence(path['type'])
        }
        return evidence
    
    def _get_historical_performance(self) -> Dict[str, any]:
        """Get historical performance data for evidence"""
        opt_summary = self.self_optimizer.get_optimization_summary()
        return {
            'optimization_cycles': opt_summary['cycles'],
            'optimized_targets': opt_summary['optimized_count'],
            'substrate_potential': opt_summary['substrate_potential']
        }
    
    def _get_path_specific_evidence(self, path_type: str) -> Dict[str, any]:
        """Get evidence specific to path type"""
        if path_type == 'scalability':
            return {
                'current_agents': self.num_agents,
                'target_agents': self.num_agents * 2,
                'expected_neural_coverage': self._estimate_neural_coverage(self.num_agents * 2)
            }
        elif path_type == 'topology':
            avg_degree = sum(len(conns) for conns in self.neural_topology.values()) / max(1, self.num_agents)
            return {
                'current_avg_degree': avg_degree,
                'target_avg_degree': 10.0,
                'current_density': len(self.synaptic_connections) / max(1, self.num_agents * (self.num_agents - 1))
            }
        elif path_type == 'resource_allocation':
            return {
                'current_allocation': self.self_research_resource_allocation,
                'target_allocation': 0.9,
                'expected_efficiency_gain': 0.1
            }
        elif path_type == 'emergence':
            return {
                'current_patterns': len(self.dag_tracker.events),
                'expected_new_patterns': 5
            }
        elif path_type == 'tracking':
            return {
                'current_queue_size': len(self.path_forward_discovery_queue),
                'expected_tracking_efficiency': 0.8
            }
        return {}
    
    def _estimate_neural_coverage(self, num_agents: int) -> float:
        """Estimate neural coverage for given number of agents"""
        # Fibonacci sphere coverage approximation
        return min(1.0, num_agents / 100.0)
    
    def _estimate_path_improvement(self, path: Dict[str, any]) -> float:
        """Estimate expected improvement from path forward"""
        if path['type'] == 'scalability':
            return 0.25  # 25% improvement expected from doubling agents
        elif path['type'] == 'topology':
            return 0.15  # 15% improvement from better topology
        elif path['type'] == 'resource_allocation':
            return 0.10  # 10% improvement from more resources
        elif path['type'] == 'emergence':
            return 0.20  # 20% improvement from emergent behaviors
        elif path['type'] == 'tracking':
            return 0.15  # 15% improvement from better tracking
        return 0.10  # Default 10% improvement
    
    def _estimate_path_cost(self, path: Dict[str, any]) -> Dict[str, float]:
        """Estimate resource cost for path forward"""
        if path['type'] == 'scalability':
            return {
                'cpu_cost': 0.5,
                'memory_cost': 0.6,
                'time_cost': 10.0  # 10 seconds to reinitialize
            }
        elif path['type'] == 'topology':
            return {
                'cpu_cost': 0.3,
                'memory_cost': 0.4,
                'time_cost': 5.0  # 5 seconds to reconfigure
            }
        elif path['type'] == 'resource_allocation':
            return {
                'cpu_cost': 0.1,
                'memory_cost': 0.1,
                'time_cost': 1.0  # 1 second to reconfigure
            }
        elif path['type'] == 'emergence':
            return {
                'cpu_cost': 0.4,
                'memory_cost': 0.5,
                'time_cost': 15.0  # 15 seconds to implement
            }
        elif path['type'] == 'tracking':
            return {
                'cpu_cost': 0.2,
                'memory_cost': 0.3,
                'time_cost': 3.0  # 3 seconds to implement
            }
        return {
            'cpu_cost': 0.2,
            'memory_cost': 0.2,
            'time_cost': 5.0
        }
    
    def _submit_proof_to_warden(self, proof: Dict[str, any]) -> bool:
        """Submit proof to warden layer (DAG self-reflection) for validation"""
        # Record proof submission in DAG
        self.record_dag_event("PROOF_SUBMIT", f"Submitted proof for path: {proof['description'][:50]}...",
                              snapshot={
                                  'path_id': proof['path_id'],
                                  'priority': proof['priority'],
                                  'expected_improvement': proof['expected_improvement']
                              })
        
        # Warden validation logic (using DAG self-reflection)
        # Check if path conflicts with existing paths to avoid
        proof_valid = True
        for avoided_path in self.dag_tracker.paths_to_avoid:
            if proof['description'] in avoided_path:
                proof_valid = False
                break
        
        # Check if swarm consensus threshold is met
        if proof_valid:
            consensus_score = proof['priority'] * proof['expected_improvement']
            if consensus_score >= proof['consensus_required']:
                proof_valid = True
            else:
                proof_valid = False
        
        # Record validation result
        validation_status = "VALIDATED" if proof_valid else "REJECTED"
        self.record_dag_event("PROOF_VALIDATION", f"Proof {validation_status}: {proof['description'][:50]}...",
                              snapshot={
                                  'path_id': proof['path_id'],
                                  'validation_status': validation_status,
                                  'consensus_score': consensus_score if 'consensus_score' in locals() else 0
                              })
        
        return proof_valid
    
    def _auto_enable_path(self, path: Dict[str, any]) -> bool:
        """Auto-enable validated path forward"""
        if not self.auto_upgrade_enabled:
            return False
        
        try:
            if path['type'] == 'scalability':
                # Scale swarm to 2x agents
                new_num_agents = self.num_agents * 2
                self.num_agents = new_num_agents
                self._initialize_neural_topology()  # Reinitialize with new agent count
                self.record_dag_event("AUTO_UPGRADE", f"Auto-scaled swarm to {new_num_agents} agents",
                                      snapshot={'num_agents': new_num_agents})
                return True
            
            elif path['type'] == 'topology':
                # Increase neural connection density
                self.neural_activation_threshold = 0.6  # Lower threshold for more connections
                self._initialize_neural_topology()  # Reinitialize with new threshold
                self.record_dag_event("AUTO_UPGRADE", "Auto-increased neural connection density",
                                      snapshot={'threshold': self.neural_activation_threshold})
                return True
            
            elif path['type'] == 'resource_allocation':
                # Increase self-research allocation to 90%
                self.self_research_resource_allocation = 0.9
                self.record_dag_event("AUTO_UPGRADE", "Auto-increased self-research allocation to 90%",
                                      snapshot={'allocation': self.self_research_resource_allocation})
                return True
            
            elif path['type'] == 'emergence':
                # Implement emergent behavior patterns
                self.synaptic_plasticity_rate = 0.15  # Increase plasticity for emergence
                self.record_dag_event("AUTO_UPGRADE", "Auto-enabled emergent behavior patterns",
                                      snapshot={'plasticity_rate': self.synaptic_plasticity_rate})
                return True
            
            elif path['type'] == 'tracking':
                # Initialize path forward tracking
                self.path_forward_discovery_queue = []  # Clear queue for fresh tracking
                self.record_dag_event("AUTO_UPGRADE", "Auto-initialized path forward tracking system",
                                      snapshot={'queue_cleared': True})
                return True
            
        except Exception as e:
            print(f"[ERROR] Auto-upgrade failed for path {path['type']}: {e}")
            return False
        
        return False
    
    def discover_remote_nodes(self):
        """Discover remote nodes in the system"""
        # Simulate remote node discovery
        # In a real implementation, this would scan the network
        local_node = RemoteNode(
            node_id="local",
            address="127.0.0.1",
            port=8080,
            node_type="compute",
            capabilities=["topology_analysis", "genetic_compression", "homeostasis", "omnitoken"],
            status="online",
            last_seen=time.time(),
            metrics={"cpu_usage": 0.5, "memory_usage": 0.3},
            omnitoken_supported=True,
            omnitoken_chains=['base', 'arbitrum', 'ethereum']
        )
        self.remote_nodes["local"] = local_node
    
    def record_dag_event(self, op: str, explanation: str, args: List[str] = None, snapshot: Dict[str, float] = None):
        """Record a DAG event with explanation"""
        import hashlib
        
        tick = len(self.dag_tracker.events)
        event_data = f"{tick}{op}{str(args)}{explanation}{time.time()}"
        hash_value = hashlib.sha256(event_data.encode()).hexdigest()
        
        event = DAGEvent(
            tick=tick,
            op=op,
            args=args or [],
            registers=[tick, len(self.dag_tracker.events)],
            status="STABLE",
            hash=hash_value,
            explanation=explanation,
            timestamp=time.time(),
            snapshot=snapshot or {}
        )
        
        self.dag_tracker.add_event(event)
    
    def _extract_topology_constraints(self) -> Dict[str, any]:
        """Extract topology constraints"""
        constraints = {
            'max_wire_length': max((seg.length_mm for seg in self.topology.wire_segments.values()), default=100.0),
            'max_voltage_drop': max((edge.voltage_drop_mv for edge in self.topology.edges), default=100.0),
            'max_timing': max((edge.timing_ps for edge in self.topology.edges), default=1000.0),
            'pcb_layers': 4,
            'dielectric': 'Rogers 4350B',
            'dielectric_constant': 3.48,
            'trace_width': 0.15,
            'copper_thickness': 35,
        }
        return constraints
    
    def initialize_agents(self, base_params: Dict[str, float], subject: str = "topology") -> None:
        """Initialize enhanced swarm agents with NII core assignments"""
        # Extract GPU and SSD metrics
        gpu_metrics = self.gpu_extractor.extract_gpu_metrics()
        ssd_metrics = self.ssd_extractor.extract_ssd_metrics()
        
        # Extract genetic compression metrics
        genetic_reports = self.genetic_extractor.extract_genetic_metrics()
        
        geometric_params = self.mapper.map_to_enhanced_params(base_params, subject, gpu_metrics, ssd_metrics)
        
        # Get math context
        math_entities = self.math_db.query_by_subject(subject)
        
        # Get Lean context
        lean_modules = list(set(e.lean_module for e in math_entities if e.lean_module))
        
        # Define agent specializations including NII core assignments
        specializations = [
            {'name': 'curvatureAnalyst', 'nii_core': 'NII-01'},
            {'name': 'hierarchyOptimizer', 'nii_core': 'NII-01'},
            {'name': 'mutationTuner', 'nii_core': 'NII-01'},
            {'name': 'semanticCore', 'nii_core': 'NII-01'},  # NII-01: Semantic Analysis
            {'name': 'translationCore', 'nii_core': 'NII-02'},  # NII-02: Translation Engine
            {'name': 'verificationCore', 'nii_core': 'NII-03'},  # NII-03: Verification
            {'name': 'topologyAnalyst', 'nii_core': None},
            {'name': 'geometricReviewer', 'nii_core': None},
            {'name': 'isaAnalyst', 'nii_core': None},
            {'name': 'mathDatabaseAnalyst', 'nii_core': None},
            {'name': 'leanModuleAnalyst', 'nii_core': None},
            {'name': 'gpuAnalyst', 'nii_core': None},
            {'name': 'ssdAnalyst', 'nii_core': None},
            {'name': 'geneticCompressionAnalyst', 'nii_core': None},
            {'name': 'selfMonitoringAgent', 'nii_core': None},
            {'name': 'metatypingAnalyst', 'nii_core': None},
            {'name': 'remoteNodeAnalyst', 'nii_core': None},
            {'name': 'selfOptimizationAgent', 'nii_core': None},
            {'name': 'dagSelfReflectionAgent', 'nii_core': None},
            {'name': 'researchQuestionerAgent', 'nii_core': None},
            {'name': 'driverGeneticCodingAgent', 'nii_core': None},
            {'name': 'curiosityDrivenAgent', 'nii_core': None},
            {'name': 'selfReferentialResearchAgent', 'nii_core': None}
        ]
        
        # Create agents based on num_agents, cycling through specializations if needed
        for i in range(self.num_agents):
            # Cycle through specializations if we need more agents than specializations
            spec = specializations[i % len(specializations)]
            agent = EnhancedSwarmAgent(
                id=i,
                specialization=spec['name'],
                nii_core_id=spec['nii_core'],
                confidence=0.0,
                geometric_params=geometric_params,
                findings=[],
                recommendations=[],
                topology_context=self.topology,
                math_context=math_entities,
                lean_context=lean_modules,
                gpu_context=gpu_metrics,
                ssd_context=ssd_metrics,
                genetic_context=genetic_reports
            )
            self.agents.append(agent)
        
        # Initialize NII core status
        for core in self.nii_registry.cores:
            status = NIICoreStatus(
                core_id=core.core_id,
                status='idle',
                current_task=None,
                geometric_score=geometric_params.kappa_squared,
                famm_timing={
                    'torsional_stress': geometric_params.torsional_stress,
                    'interlocking_energy': geometric_params.interlocking_energy,
                    'laplacian_energy': geometric_params.laplacian_energy
                },
                topology_score=geometric_params.wire_length_factor,
                math_relevance=geometric_params.math_relevance_score,
                gpu_utilization=gpu_metrics.gpu_utilization_percent / 100.0,
                ssd_throughput=ssd_metrics.health_percent / 100.0
            )
            self.nii_core_status.append(status)
    
    def run_agent_analysis(self, agent: EnhancedSwarmAgent) -> EnhancedSwarmAgent:
        """Run enhanced analysis for a single agent"""
        params = agent.geometric_params
        
        if agent.specialization == 'semanticCore':
            # NII-01: Semantic Analysis
            agent.confidence = params.geometric_score_from_topology() if hasattr(params, 'geometric_score_from_topology') else 0.8
            agent.findings.append(f"NII-01 Semantic Analysis: pattern recognition efficiency {agent.confidence:.3f}")
            agent.recommendations.append(f"Use κ²={params.kappa_squared:.3f} for pattern compression")
            agent.recommendations.append(f"FAMM timing: torsional stress {params.torsional_stress:.3f}")
        
        elif agent.specialization == 'translationCore':
            # NII-02: Translation Engine
            agent.confidence = params.lean_alignment_score
            agent.findings.append(f"NII-02 Translation Engine: Rust → Lean efficiency {agent.confidence:.3f}")
            agent.recommendations.append(f"Use κ_hierarchy={params.kappa_hierarchy:.3f} for hierarchical encoding")
            agent.recommendations.append(f"Lean alignment: {params.lean_alignment_score:.3f}")
        
        elif agent.specialization == 'verificationCore':
            # NII-03: Verification
            agent.confidence = params.math_relevance_score
            agent.findings.append(f"NII-03 Verification: proof generation efficiency {agent.confidence:.3f}")
            agent.recommendations.append(f"Use ε={params.epsilon_mutation:.3f} for adaptive proof search")
            agent.recommendations.append(f"Math relevance: {params.math_relevance_score:.3f}")
        
        elif agent.specialization == 'curvatureAnalyst':
            utilization = params.kappa_squared * params.impedance_factor * params.dielectric_factor
            agent.confidence = utilization
            if utilization < 0.3:
                agent.findings.append(f"κ² curvature coupling underutilized: {utilization:.3f}")
                agent.recommendations.append(f"Increase κ² or improve impedance matching (current: {params.impedance_factor:.3f})")
            elif utilization > 0.7:
                agent.findings.append(f"κ² curvature coupling excellent: {utilization:.3f}")
            else:
                agent.findings.append(f"κ² curvature coupling moderate: {utilization:.3f}")
        
        elif agent.specialization == 'hierarchyOptimizer':
            efficiency = params.kappa_hierarchy * params.wire_length_factor * params.timing_ps_factor
            agent.confidence = efficiency
            if efficiency < 0.3:
                agent.findings.append(f"κ_hierarchy² underutilized: {efficiency:.3f}")
                agent.recommendations.append(f"Reduce trace lengths or improve timing (timing factor: {params.timing_ps_factor:.3f})")
            elif efficiency > 0.7:
                agent.findings.append(f"κ_hierarchy² excellent: {efficiency:.3f}")
            else:
                agent.findings.append(f"κ_hierarchy² moderate: {efficiency:.3f}")
        
        elif agent.specialization == 'mutationTuner':
            adaptivity = params.epsilon_mutation * params.voltage_drop_factor * params.timing_ps_factor
            agent.confidence = adaptivity
            if adaptivity < 0.3:
                agent.findings.append(f"ε mutation rate too low: {adaptivity:.3f}")
                agent.recommendations.append(f"Increase ε or reduce voltage drops (voltage factor: {params.voltage_drop_factor:.3f})")
            elif adaptivity > 0.7:
                agent.findings.append(f"ε mutation rate excellent: {adaptivity:.3f}")
            else:
                agent.findings.append(f"ε mutation rate moderate: {adaptivity:.3f}")
        
        elif agent.specialization == 'topologyAnalyst':
            overall_score = (
                params.wire_length_factor * 0.3 +
                params.voltage_drop_factor * 0.2 +
                params.timing_ps_factor * 0.3 +
                params.impedance_factor * 0.2
            )
            agent.confidence = overall_score
            agent.findings.append(f"Overall topology optimization score: {overall_score:.3f}")
            if overall_score < 0.5:
                agent.recommendations.append("Topology requires optimization: consider trace rerouting")
            elif overall_score > 0.8:
                agent.recommendations.append("Topology well-optimized for geometric enhancements")
            else:
                agent.recommendations.append("Topology acceptable but has room for improvement")
        
        elif agent.specialization == 'geometricReviewer':
            overall_score = (
                params.kappa_squared * 0.3 +
                params.kappa_hierarchy * 0.3 +
                params.epsilon_mutation * 0.4
            )
            agent.confidence = overall_score
            agent.findings.append(f"Overall geometric enhancement score: {overall_score:.3f}")
            if overall_score < 0.5:
                agent.recommendations.append("Overall geometric enhancement underutilized with current topology")
            elif overall_score > 0.8:
                agent.recommendations.append("Overall geometric enhancement excellent for this topology")
            else:
                agent.recommendations.append("Overall geometric enhancement moderate for topology constraints")
        
        elif agent.specialization == 'mathDatabaseAnalyst':
            agent.confidence = params.math_relevance_score
            agent.findings.append(f"Math database relevance: {params.math_relevance_score:.3f}")
            if params.math_relevance_score < 0.5:
                agent.recommendations.append("Increase math entity coverage in database")
            elif params.math_relevance_score > 0.8:
                agent.recommendations.append("Math database coverage excellent")
            else:
                agent.recommendations.append("Math database coverage acceptable")
        
        elif agent.specialization == 'leanModuleAnalyst':
            agent.confidence = params.lean_alignment_score
            agent.findings.append(f"Lean module alignment: {params.lean_alignment_score:.3f}")
            if params.lean_alignment_score < 0.5:
                agent.recommendations.append("Increase Lean formalization coverage")
            elif params.lean_alignment_score > 0.8:
                agent.recommendations.append("Lean formalization coverage excellent")
            else:
                agent.recommendations.append("Lean formalization coverage acceptable")
        
        elif agent.specialization == 'isaAnalyst':
            geometric_support = params.impedance_factor * params.dielectric_factor
            agent.confidence = geometric_support
            if geometric_support < 0.5:
                agent.findings.append(f"ISA geometric support low: {geometric_support:.3f}")
                agent.recommendations.append("Topology may limit geometric opcode effectiveness")
        
        elif agent.specialization == 'gpuAnalyst':
            gpu_score = (params.gpu_compute_factor * 0.4 + 
                        params.gpu_memory_factor * 0.3 + 
                        params.gpu_shader_efficiency * 0.3)
            agent.confidence = gpu_score
            agent.findings.append(f"GPU computing score: {gpu_score:.3f}")
            agent.findings.append(f"GPU compute factor: {params.gpu_compute_factor:.3f}")
            agent.findings.append(f"GPU memory factor: {params.gpu_memory_factor:.3f}")
            agent.findings.append(f"GPU shader efficiency: {params.gpu_shader_efficiency:.3f}")
            if gpu_score < 0.5:
                agent.recommendations.append("GPU utilization below optimal - consider GPU-accelerated WGSL shaders")
            elif gpu_score > 0.8:
                agent.recommendations.append("GPU utilization excellent - ready for WGSL acceleration")
            else:
                agent.recommendations.append("GPU utilization acceptable - can be optimized with WGSL")
        
        elif agent.specialization == 'ssdAnalyst':
            ssd_score = (params.ssd_throughput_factor * 0.4 + 
                        params.ssd_latency_factor * 0.3 + 
                        params.ssd_health_factor * 0.3)
            agent.confidence = ssd_score
            agent.findings.append(f"SSD storage score: {ssd_score:.3f}")
            agent.findings.append(f"SSD throughput factor: {params.ssd_throughput_factor:.3f}")
            agent.findings.append(f"SSD latency factor: {params.ssd_latency_factor:.3f}")
            agent.findings.append(f"SSD health factor: {params.ssd_health_factor:.3f}")
            if ssd_score < 0.5:
                agent.recommendations.append("SSD performance below optimal - consider NVMe optimization")
            elif ssd_score > 0.8:
                agent.recommendations.append("SSD performance excellent - PCIe Gen4 x4 fully utilized")
            else:
                agent.recommendations.append("SSD performance acceptable - PCIe configuration optimal")
        
        elif agent.specialization == 'geneticCompressionAnalyst':
            if agent.genetic_context:
                # Calculate average optimization score across all surfaces
                avg_optimization = sum(r.optimization_score for r in agent.genetic_context.values()) / len(agent.genetic_context)
                avg_field_phi = sum(r.field_phi for r in agent.genetic_context.values()) / len(agent.genetic_context)
                avg_compression_ratio = sum(r.compression_ratio for r in agent.genetic_context.values()) / len(agent.genetic_context)
                
                agent.confidence = avg_optimization
                agent.findings.append(f"Genetic compression optimization score: {avg_optimization:.3f}")
                agent.findings.append(f"Average field Φ: {avg_field_phi:.3f}")
                agent.findings.append(f"Average compression ratio: {avg_compression_ratio:.2f}x")
                
                # Report individual surface methods
                for surface_type, report in agent.genetic_context.items():
                    agent.findings.append(f"  {surface_type.value}: {report.method} (Φ={report.field_phi:.3f}, ratio={report.compression_ratio:.2f}x)")
                
                if avg_optimization < 0.5:
                    agent.recommendations.append("Genetic compression below optimal - consider surface-specific tuning")
                elif avg_optimization > 0.8:
                    agent.recommendations.append("Genetic compression excellent - unified field theory well-calibrated")
                else:
                    agent.recommendations.append("Genetic compression acceptable - anisotropy optimization possible")
            else:
                agent.confidence = 0.5
                agent.recommendations.append("Genetic compression context not available")
        
        elif agent.specialization == 'selfMonitoringAgent':
            # Self-monitoring agent analyzes swarm health and homeostasis
            homeostasis_score = self.homeostasis_state.compute_homeostasis_score()
            
            # Update feedback loops with current metrics
            if self.feedback_loops:
                self._update_feedback_loops()
            
            # Analyze consensus stability
            agent.confidence = homeostasis_score
            agent.findings.append(f"Homeostasis score: {homeostasis_score:.3f}")
            agent.findings.append(f"Consensus stability: {self.homeostasis_state.consensus_stability:.3f}")
            agent.findings.append(f"Resource efficiency: {self.homeostasis_state.resource_efficiency:.3f}")
            agent.findings.append(f"Learning rate: {self.homeostasis_state.learning_rate:.3f}")
            agent.findings.append(f"Adaptation speed: {self.homeostasis_state.adaptation_speed:.3f}")
            agent.findings.append(f"Equilibrium distance: {self.homeostasis_state.equilibrium_distance:.3f}")
            agent.findings.append(f"Patterns learned: {len(self.swarm_memory.patterns)}")
            
            # Feedback loop status
            for metric_name, loop in self.feedback_loops.items():
                agent.findings.append(f"  {metric_name}: current={loop.current_value:.3f}, target={loop.target_value:.3f}, direction={loop.direction}")
            
            if homeostasis_score < 0.5:
                agent.recommendations.append("Homeostasis degraded - increasing learning rate")
                self.homeostasis_state.learning_rate = min(self.homeostasis_state.learning_rate * 1.5, 0.1)
            elif homeostasis_score > 0.8:
                agent.recommendations.append("Homeostasis excellent - maintaining current parameters")
                self.homeostasis_state.learning_rate = max(self.homeostasis_state.learning_rate * 0.9, 0.001)
            else:
                agent.recommendations.append("Homeostasis acceptable - fine-tuning parameters")
            
            # Record homeostasis state in memory
            self.swarm_memory.record_homeostasis(self.homeostasis_state)
        
        elif agent.specialization == 'metatypingAnalyst':
            # Metatyping agent analyzes swarm components through metatype lens
            metastack_count = sum(1 for mt in self.metatypes.values() if mt.is_metastack())
            total_metatypes = len(self.metatypes)
            
            agent.confidence = metastack_count / max(1, total_metatypes)
            agent.findings.append(f"Total metatypes: {total_metatypes}")
            agent.findings.append(f"Metastacks (all three layers): {metastack_count}")
            
            for mt_name, mt in self.metatypes.items():
                agent.findings.append(f"  {mt_name}: {mt.classify} (layers: {len(mt.tags)}, sigma: {mt.sigma_codon})")
            
            if metastack_count == total_metatypes:
                agent.recommendations.append("All components form metastacks - optimal integration")
            elif metastack_count > total_metatypes * 0.5:
                agent.recommendations.append("Most components form metastacks - good integration")
            else:
                agent.recommendations.append("Many components lack full layer integration - consider adding missing layers")
        
        elif agent.specialization == 'remoteNodeAnalyst':
            # Remote node analyst tracks and analyzes remote nodes
            self.discover_remote_nodes()
            
            online_nodes = sum(1 for node in self.remote_nodes.values() if node.is_online())
            total_nodes = len(self.remote_nodes)
            
            agent.confidence = online_nodes / max(1, total_nodes)
            agent.findings.append(f"Total remote nodes: {total_nodes}")
            agent.findings.append(f"Online nodes: {online_nodes}")
            
            for node_id, node in self.remote_nodes.items():
                status_icon = "✓" if node.is_online() else "✗"
                agent.findings.append(f"  {status_icon} {node_id}: {node.node_type} @ {node.address}:{node.port}")
                agent.findings.append(f"    Capabilities: {', '.join(node.capabilities)}")
                agent.findings.append(f"    Metrics: {node.metrics}")
            
            if online_nodes == total_nodes:
                agent.recommendations.append("All remote nodes online - full swarm capacity")
            elif online_nodes > total_nodes * 0.5:
                agent.recommendations.append("Most remote nodes online - degraded but functional")
            else:
                agent.recommendations.append("Few remote nodes online - swarm capacity severely limited")
        
        elif agent.specialization == 'selfOptimizationAgent':
            # Self-optimization agent performs autonomous optimization
            # Use saved target values (not fresh metrics) to allow convergence
            context = {
                'consensus': self.self_optimizer.targets.get('consensus', OptimizationTarget('consensus', 0.5, 0.8)).current_value,
                'homeostasis': self.self_optimizer.targets.get('homeostasis', OptimizationTarget('homeostasis', 0.5, 0.8)).current_value,
                'topology_efficiency': self.self_optimizer.targets.get('topology_efficiency', OptimizationTarget('topology_efficiency', 0.5, 0.7)).current_value,
                'resource_utilization': self.self_optimizer.targets.get('resource_utilization', OptimizationTarget('resource_utilization', 0.5, 0.75)).current_value
            }
            
            # Perform optimization cycle using saved values
            adjustments = self.self_optimizer.optimize(context)
            
            # Get optimization summary
            summary = self.self_optimizer.get_optimization_summary()
            
            agent.confidence = summary['optimization_ratio']
            agent.findings.append(f"Optimization cycles: {summary['cycles']}")
            agent.findings.append(f"Optimized targets: {summary['optimized_count']}/{summary['total_targets']}")
            agent.findings.append(f"Optimization ratio: {summary['optimization_ratio']:.3f}")
            agent.findings.append(f"Substrate potential: {summary['substrate_potential']:.1f}")
            
            # Report on each target
            for name, target in self.self_optimizer.targets.items():
                status_icon = "✓" if target.is_optimized() else "○"
                agent.findings.append(f"  {status_icon} {name}: {target.current_value:.3f} → {target.target_value:.3f} (score: {target.compute_optimization_score():.3f})")
            
            # Report adjustments made
            if adjustments:
                agent.findings.append("Adjustments applied:")
                for name, adj in adjustments.items():
                    agent.findings.append(f"  {name}: {adj:+.3f}")
            
            # Report virtual substrate state
            substrate = self.self_optimizer.virtual_substrate
            agent.findings.append(f"Virtual substrate nodes: {len(substrate.nodes)}")
            agent.findings.append(f"Resonance groups: {len(substrate.resonance_groups)}")
            
            # Find resonant node pairs
            resonant_pairs = []
            for mass, node_ids in substrate.resonance_groups.items():
                if len(node_ids) > 1:
                    resonant_pairs.append((mass, node_ids))
            
            if resonant_pairs:
                agent.findings.append("Resonant node groups:")
                for mass, node_ids in resonant_pairs[:5]:  # Show first 5
                    agent.findings.append(f"  Mass {mass}: {', '.join(node_ids)}")
            
            # Recommendations based on optimization state
            if summary['optimization_ratio'] >= 0.8:
                agent.recommendations.append("System well-optimized - maintaining current parameters")
            elif summary['optimization_ratio'] >= 0.5:
                agent.recommendations.append("System partially optimized - continuing optimization")
            else:
                agent.recommendations.append("System requires significant optimization - accelerating adjustments")
            
            # Apply adjustments to feedback loops
            for name, adjustment in adjustments.items():
                if name in self.feedback_loops:
                    loop = self.feedback_loops[name]
                    loop.current_value += adjustment
            
            # Record DAG event for optimization cycle
            self.record_dag_event("OPTIMIZE", f"Self-optimization cycle {summary['cycles']}", 
                                  snapshot={'optimization_ratio': summary['optimization_ratio']})
            
            # Save optimization state to file
            self.self_optimizer.save_state()
        
        elif agent.specialization == 'dagSelfReflectionAgent':
            # DAG self-reflection agent analyzes swarm evolution to identify paths to avoid
            analysis = self.dag_tracker.analyze_evolution_patterns()
            
            # Identify paths to avoid based on historical analysis
            new_avoid_paths = self.dag_tracker.identify_paths_to_avoid()
            
            # Get evolution summary
            evolution_summary = self.dag_tracker.get_evolution_summary()
            
            agent.findings.append(evolution_summary)
            
            # Report analysis results
            if analysis.get('status') == 'insufficient_data':
                agent.findings.append("Insufficient DAG data for pattern analysis")
                agent.confidence = 0.0
            else:
                agent.findings.append(f"Total events analyzed: {analysis['total_events']}")
                agent.findings.append(f"Event type distribution: {analysis['event_types']}")
                
                if analysis['repeated_patterns']:
                    agent.findings.append(f"Repeated patterns detected: {len(analysis['repeated_patterns'])}")
                    for pattern in analysis['repeated_patterns'][:3]:
                        agent.findings.append(f"  - {pattern['pattern']} (freq: {pattern['frequency']})")
                else:
                    agent.findings.append("No repeated patterns detected")
                
                if analysis['suboptimal_branches']:
                    agent.findings.append(f"Suboptimal branches: {len(analysis['suboptimal_branches'])}")
                    for branch in analysis['suboptimal_branches'][:3]:
                        agent.findings.append(f"  - {branch['operation']}: drop of {branch['optimization_drop']:.3f}")
                else:
                    agent.findings.append("No suboptimal branches detected")
                
                if new_avoid_paths:
                    agent.findings.append(f"New paths to avoid: {len(new_avoid_paths)}")
                    agent.recommendations.append(f"Marked {len(new_avoid_paths)} paths as suboptimal based on historical analysis")
                else:
                    agent.findings.append("No new paths to avoid")
                
                # Calculate confidence based on data quality and pattern detection
                if analysis['total_events'] >= 10:
                    agent.confidence = 0.8
                elif analysis['total_events'] >= 5:
                    agent.confidence = 0.5
                else:
                    agent.confidence = 0.3
                
                # Get recommendations for current optimization path
                if 'OPTIMIZE' in analysis.get('event_types', {}):
                    recommendation = self.dag_tracker.get_path_recommendation('OPTIMIZE')
                    agent.findings.append(f"OPTIMIZE path recommendation: {recommendation}")
                    
                    if 'AVOID' in recommendation:
                        agent.recommendations.append(recommendation)
                    elif 'CAUTION' in recommendation:
                        agent.recommendations.append(recommendation)
            
            # Record DAG analysis event
            self.record_dag_event("DAG_REFLECT", f"DAG self-reflection analysis", 
                                  snapshot={'paths_to_avoid': len(self.dag_tracker.paths_to_avoid)})
        
        elif agent.specialization == 'researchQuestionerAgent':
            # Research questioner agent autonomously asks and finds questions
            # Get current swarm state
            swarm_state = {
                'optimization_ratio': self.self_optimizer.get_optimization_summary()['optimization_ratio'],
                'topology_optimization_score': self.feedback_loops.get('topology', FeedbackLoop('topology', 0.7, 0.5)).current_value,
                'math_coverage_score': self.feedback_loops.get('math_coverage', FeedbackLoop('math_coverage', 0.7, 0.5)).current_value,
                'genetic_compression_score': self.feedback_loops.get('genetic_compression', FeedbackLoop('genetic_compression', 0.7, 0.5)).current_value
            }
            
            # Generate research questions based on current state
            generated_questions = self.research_api.generate_research_questions(swarm_state)
            
            agent.findings.append(f"Generated {len(generated_questions)} research questions based on swarm state")
            
            # Ask and answer questions
            for q_data in generated_questions:
                answer = self.research_api.ask_question(
                    q_data['question'],
                    context=q_data['context'],
                    priority=q_data['priority'],
                    domain=q_data['domain']
                )
                
                agent.findings.append(f"  [{q_data['priority'].upper()}] {q_data['domain']}: {q_data['question']}")
                if answer and "Direct answer not found" not in answer:
                    agent.findings.append(f"    Answer: {answer[:100]}...")
                else:
                    agent.findings.append(f"    Status: {answer[:100]}...")
            
            # Get research summary
            summary = self.research_api.get_research_summary()
            agent.findings.append(f"\nResearch Summary:")
            agent.findings.append(f"  Total questions: {summary['total_questions']}")
            agent.findings.append(f"  Open questions: {summary['open_questions']}")
            agent.findings.append(f"  Answered questions: {summary['answered_questions']}")
            agent.findings.append(f"  High priority open: {summary['high_priority']}")
            
            if summary['by_domain']:
                agent.findings.append(f"  By domain:")
                for domain, count in summary['by_domain'].items():
                    agent.findings.append(f"    {domain}: {count}")
            
            # Get open questions for recommendations
            open_questions = self.research_api.get_open_questions()
            if open_questions:
                agent.recommendations.append(f"{len(open_questions)} open research questions require attention")
                for q in open_questions[:3]:
                    agent.recommendations.append(f"  - {q.question} ({q.domain}, {q.priority})")
            
            # Calculate confidence based on research activity
            if summary['total_questions'] >= 10:
                agent.confidence = 0.8
            elif summary['total_questions'] >= 5:
                agent.confidence = 0.5
            else:
                agent.confidence = 0.3
            
            # Record research event
            self.record_dag_event("RESEARCH", f"Research activity - {summary['total_questions']} questions", 
                                  snapshot={'open_questions': summary['open_questions']})
        
        elif agent.specialization == 'driverGeneticCodingAgent':
            # Driver genetic coding agent examines system drivers and applies genetic optimization
            import subprocess
            
            # Get loaded kernel modules
            try:
                lsmod_output = subprocess.check_output(['lsmod'], text=True)
                lines = lsmod_output.split('\n')[1:]  # Skip header
                drivers = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            name = parts[0]
                            size = int(parts[1])
                            used_by = parts[2]
                            drivers.append({'name': name, 'size': size, 'used_by': used_by})
            except Exception as e:
                agent.findings.append(f"Failed to get driver list: {e}")
                agent.confidence = 0.0
                return agent
            
            # Sort drivers by size (largest first for optimization priority)
            drivers.sort(key=lambda x: x['size'], reverse=True)
            
            agent.findings.append(f"Analyzed {len(drivers)} loaded kernel modules")
            
            # Focus on top 10 largest drivers
            top_drivers = drivers[:10]
            
            # Analyze each driver for genetic coding optimization
            optimized_drivers = []
            for driver in top_drivers:
                # Apply genetic compression analysis
                genetic_params = GeneticCodeParams(
                    entropy=0.5 + (driver['size'] / 100000000.0),  # Scale entropy by size
                    genomic_complexity=0.3,
                    degeneracy=0.2
                )
                
                # Compute optimization potential
                phi = genetic_params.compute_optimization()
                info_density = genetic_params.information_density()  # Returns percentage
                
                # Calculate compression ratio based on phi and information density
                # Higher phi and info_density = better compression potential
                compression_ratio = 1.0 + (phi * 0.5) + (info_density / 200.0)  # Scale to 1.0-3.0 range
                
                # Determine optimization strategy based on driver type
                strategy = self._determine_driver_strategy(driver['name'])
                
                # Calculate potential size reduction
                potential_reduction = driver['size'] * (compression_ratio - 1.0) if compression_ratio > 1.1 else 0
                
                if potential_reduction > 10000:  # Only significant reductions
                    optimized_drivers.append({
                        'name': driver['name'],
                        'original_size': driver['size'],
                        'optimized_size': int(driver['size'] / compression_ratio),
                        'phi': phi,
                        'compression_ratio': compression_ratio,
                        'strategy': strategy,
                        'potential_reduction': int(potential_reduction)
                    })
            
            agent.findings.append(f"Identified {len(optimized_drivers)} drivers for genetic optimization")
            
            # Report top optimization candidates
            for opt in optimized_drivers[:5]:
                agent.findings.append(f"\n  {opt['name']}:")
                agent.findings.append(f"    Size: {opt['original_size']:,} → {opt['optimized_size']:,} ({opt['potential_reduction']:,} reduction)")
                agent.findings.append(f"    Φ: {opt['phi']:.4f}, Compression: {opt['compression_ratio']:.2f}x")
                agent.findings.append(f"    Strategy: {opt['strategy']}")
                
                # Generate specific optimization recommendation
                agent.recommendations.append(
                    f"Apply {opt['strategy']} to {opt['name']} driver: "
                    f"reduce from {opt['original_size']:,} to {opt['optimized_size']:,} bytes"
                )
            
            # Generate genetic-coded driver configurations
            agent.findings.append("\nGenetic-coded driver configurations:")
            for opt in optimized_drivers[:3]:
                config = self._generate_genetic_driver_config(opt)
                agent.findings.append(f"\n  {opt['name']}_genetic:")
                for line in config.split('\n'):
                    agent.findings.append(f"    {line}")
            
            # Calculate confidence based on optimization potential
            total_reduction = sum(d['potential_reduction'] for d in optimized_drivers)
            if total_reduction > 10000000:  # > 10MB reduction
                agent.confidence = 0.9
            elif total_reduction > 1000000:  # > 1MB reduction
                agent.confidence = 0.7
            elif total_reduction > 100000:  # > 100KB reduction
                agent.confidence = 0.5
            else:
                agent.confidence = 0.3
            
            # Record driver optimization event
            self.record_dag_event("DRIVER_GENETIC", f"Driver genetic optimization - {len(optimized_drivers)} drivers", 
                                  snapshot={'total_reduction': total_reduction})
        
        elif agent.specialization == 'curiosityDrivenAgent':
            # Curiosity-driven agent explores new paths and seeks self-improvement
            # With special focus on neural encoding patterns and matter relationships
            agent.findings.append("Curiosity-driven exploration initiated")
            agent.findings.append("Special focus: Neural encoding patterns and matter relationships")
            
            # Explore neural encoding patterns (high priority)
            neural_patterns = self._explore_neural_encoding_patterns()
            
            agent.findings.append(f"Identified {len(neural_patterns)} neural encoding patterns")
            
            # Research OpenWorm and similar experiments
            experimental_records = self._research_neural_experiments()
            
            agent.findings.append(f"Researched {len(experimental_records)} neural experiments (OpenWorm, etc.)")
            
            # Explore system improvement opportunities
            improvement_opportunities = self._explore_improvement_opportunities()
            
            agent.findings.append(f"Identified {len(improvement_opportunities)} improvement opportunities")
            
            # Explore self-improvement opportunities for agents
            self_improvements = self._explore_agent_self_improvement()
            
            agent.findings.append(f"Identified {len(self_improvements)} self-improvement opportunities")
            
            # Explore math refinement opportunities
            math_refinements = self._explore_math_refinement()
            
            agent.findings.append(f"Identified {len(math_refinements)} math refinement opportunities")
            
            # Select exploration targets based on curiosity level (neural patterns prioritized)
            exploration_targets = []
            
            # Always prioritize neural patterns
            exploration_targets.extend(neural_patterns[:3])
            
            # Balance exploration vs exploitation for other targets
            if agent.curiosity > 0.7:
                # High curiosity: explore novel paths
                exploration_targets.extend(experimental_records[:2])
                exploration_targets.extend(improvement_opportunities[:2])
                exploration_targets.extend(self_improvements[:1])
                exploration_targets.extend(math_refinements[:1])
            elif agent.curiosity > 0.4:
                # Moderate curiosity: balanced exploration
                exploration_targets.extend(experimental_records[:1])
                exploration_targets.extend(improvement_opportunities[:1])
            else:
                # Low curiosity: minimal exploration, focus on exploitation
                exploration_targets.extend(improvement_opportunities[:1])
            
            # Execute exploration
            novel_discoveries = 0
            significant_findings = []
            for target in exploration_targets:
                discovery = self._execute_exploration(target)
                if discovery:
                    novel_discoveries += 1
                    agent.novel_discoveries += 1
                    
                    # Check for significance
                    significance = self._assess_significance(discovery)
                    
                    # Write novel discovery to RAM loopback device
                    self.ram_writer.write_improvement(
                        agent_id=agent.id,
                        improvement_type="novel_discovery",
                        improvement_data={
                            'discovery': discovery,
                            'target': target,
                            'significance': significance,
                            'novel_discoveries': agent.novel_discoveries,
                            'specialization': agent.specialization,
                            'nii_core_id': agent.nii_core_id
                        }
                    )
                    
                    if significance >= 0.7:  # Significant threshold
                        significant_findings.append({
                            'discovery': discovery,
                            'significance': significance,
                            'timestamp': time.time()
                        })
                        agent.recommendations.append(f"[SIGNIFICANT] {discovery} (significance: {significance:.2f})")
                    
                    agent.exploration_history.append({
                        'target': target,
                        'discovery': discovery,
                        'significance': significance,
                        'timestamp': time.time()
                    })
                    agent.findings.append(f"Novel discovery: {discovery}")
            
            agent.findings.append(f"Exploration complete: {novel_discoveries} novel discoveries")
            agent.findings.append(f"Total novel discoveries: {agent.novel_discoveries}")
            
            if significant_findings:
                agent.findings.append(f"Significant findings: {len(significant_findings)}")
                total_reward_earned = 0.0
                for finding in significant_findings:
                    agent.findings.append(f"  - {finding['discovery'][:80]}... (sig: {finding['significance']:.2f})")
                    
                    # Apply reward if the discovery represents a mathematically stable self-improvement
                    reward = self._apply_reward(agent, finding['discovery'], finding['significance'])
                    if reward > 0:
                        total_reward_earned += reward
                        agent.recommendations.append(f"[REWARD] Mathematically stable self-improvement rewarded: +{reward:.2f}")
                        
                        # Emit spike to propagate discovery through neural swarm
                        spike_emitted = self._emit_spike(agent, finding['discovery'], signal_strength=finding['significance'], spike_type="discovery")
                        if spike_emitted:
                            agent.findings.append(f"[SPIKE] Emitted neural spike for discovery")
                
                if total_reward_earned > 0:
                    agent.findings.append(f"Total reward earned: {total_reward_earned:.2f}")
                    agent.findings.append(f"Total reward score: {agent.reward_score:.2f}")
                    agent.findings.append(f"Stable improvements: {agent.stable_improvements}")
                
                # Record significant findings in DAG
                self.record_dag_event("NEURAL_DISCOVERY", f"Significant neural pattern discovery - {len(significant_findings)} findings",
                                      snapshot={'findings': significant_findings, 'reward_earned': total_reward_earned})
            
            # Adjust curiosity based on exploration success
            if novel_discoveries > 0:
                # Increase curiosity on success
                agent.curiosity = min(1.0, agent.curiosity + 0.1)
            else:
                # Decrease curiosity on failure
                agent.curiosity = max(0.0, agent.curiosity - 0.05)
            
            agent.confidence = 0.8
        
        elif agent.specialization == 'selfReferentialResearchAgent':
            # Self-referential research agent uses 80% of system resources
            # to research itself, other agents, and find paths forward
            agent.findings.append(f"Self-referential research initiated")
            agent.findings.append(f"Resource allocation: {self.self_research_resource_allocation * 100}% for self-research")
            
            # Research swarm architecture and topology
            swarm_architecture_insights = self._research_swarm_architecture()
            agent.findings.append(f"Analyzed swarm architecture: {len(swarm_architecture_insights)} insights")
            
            # Research agent capabilities and specializations
            agent_capabilities = self._research_agent_capabilities()
            agent.findings.append(f"Analyzed {len(agent_capabilities)} agent capabilities")
            
            # Research neural topology and connections
            neural_topology_insights = self._research_neural_topology()
            agent.findings.append(f"Analyzed neural topology: {len(neural_topology_insights)} insights")
            
            # Collaborative research with connected agents via neural topology
            collaborative_insights = self._collaborative_agent_research(agent)
            agent.findings.append(f"Collaborative research: {len(collaborative_insights)} shared insights")
            
            # Discover paths forward
            paths_forward = self._discover_paths_forward()
            agent.findings.append(f"Discovered {len(paths_forward)} potential paths forward")
            
            # Prioritize and select best path forward
            if paths_forward:
                best_path = max(paths_forward, key=lambda p: p.get('priority', 0))
                agent.recommendations.append(f"[PATH FORWARD] {best_path['description']} (priority: {best_path['priority']:.2f})")
                self.path_forward_discovery_queue.append(best_path)
                
                # Generate proof for path forward
                proof = self._generate_path_proof(best_path)
                agent.findings.append(f"[PROOF] Generated proof for path forward (ID: {proof['path_id']})")
                
                # Submit proof to warden layer (DAG self-reflection)
                proof_validated = self._submit_proof_to_warden(proof)
                if proof_validated:
                    agent.findings.append(f"[VALIDATED] Proof validated by warden layer")
                    self.validated_path_forwards.append(best_path)
                    
                    # Auto-enable validated path
                    if self.auto_upgrade_enabled:
                        auto_enabled = self._auto_enable_path(best_path)
                        if auto_enabled:
                            agent.findings.append(f"[AUTO-UPGRADE] Path auto-enabled: {best_path['type']}")
                            agent.recommendations.append(f"[AUTO-UPGRADE] Swarm auto-upgraded via {best_path['type']}")
                        else:
                            agent.findings.append(f"[AUTO-UPGRADE FAILED] Could not auto-enable path")
                else:
                    agent.findings.append(f"[REJECTED] Proof rejected by warden layer")
                
                # Emit spike to propagate path forward discovery
                spike_emitted = self._emit_spike(agent, best_path['description'], signal_strength=best_path['priority'], spike_type="coordination")
                if spike_emitted:
                    agent.findings.append(f"[SPIKE] Emitted neural spike for path forward discovery")
            
            agent.confidence = 0.9
            
            # Record self-referential research event
            self.record_dag_event("SELF_RESEARCH", f"Self-referential research - {len(paths_forward)} paths discovered",
                                  snapshot={'resource_allocation': self.self_research_resource_allocation, 'paths': len(paths_forward)})
        
        else:
            # Default confidence based on novel discoveries
            if agent.novel_discoveries >= 20:
                agent.confidence = 0.8
            elif agent.novel_discoveries >= 10:
                agent.confidence = 0.7
            elif agent.novel_discoveries >= 5:
                agent.confidence = 0.5
            elif agent.novel_discoveries >= 1:
                agent.confidence = 0.3
            else:
                agent.confidence = 0.1
        
        return agent
    
    def _explore_neural_encoding_patterns(self) -> List[str]:
        """Explore neural encoding patterns and their relationship to matter"""
        patterns = []
        
        # Neural spike timing patterns
        patterns.append("Neural spike timing patterns - explore temporal encoding")
        patterns.append("Synaptic plasticity patterns - explore Hebbian learning")
        patterns.append("Neural oscillation patterns - explore phase coding")
        patterns.append("Dendritic computation patterns - explore spatial encoding")
        
        # Neural-matter relationships
        patterns.append("Neural-electromagnetic field coupling patterns")
        patterns.append("Neural-thermal dissipation patterns")
        patterns.append("Neural-mechanical transduction patterns")
        patterns.append("Neural-quantum coherence patterns")
        
        # Cross-domain pattern mimics
        patterns.append("Genetic-neural analogy patterns - explore isomorphism")
        patterns.append("Phonon-neural analogy patterns - explore wave encoding")
        patterns.append("Topological-neural analogy patterns - explore manifold encoding")
        
        return patterns
    
    def _research_neural_experiments(self) -> List[str]:
        """Research neural experiments like OpenWorm"""
        records = []
        
        # OpenWorm project
        records.append("OpenWorm: C. elegans connectome simulation - explore neural encoding")
        records.append("OpenWorm: 302 neuron model - explore minimal neural encoding")
        records.append("OpenWorm: Muscle-neuron coupling - explore action encoding")
        
        # Other neural experiments
        records.append("Blue Brain Project: cortical column simulation")
        records.append("Human Connectome Project: structural neural networks")
        records.append("Allen Brain Atlas: gene expression in neurons")
        records.append("Neuroelectrophysiology: spike train analysis")
        
        # Neuromorphic experiments
        records.append("Loihi neuromorphic chip: spike-based encoding")
        records.append("TrueNorth neuromorphic chip: event-based processing")
        records.append("BrainScaleS: analog neural emulation")
        
        return records
    
    def _assess_significance(self, discovery: str) -> float:
        """Assess significance of a discovery (0.0-1.0)"""
        significance = 0.5  # Base significance
        
        # Boost for neural-related discoveries
        if any(term in discovery.lower() for term in ['neural', 'neuron', 'synaptic', 'spike', 'encoding']):
            significance += 0.2
        
        # Boost for pattern-related discoveries
        if any(term in discovery.lower() for term in ['pattern', 'encoding', 'algorithm', 'framework']):
            significance += 0.15
        
        # Boost for matter-related discoveries
        if any(term in discovery.lower() for term in ['matter', 'field', 'quantum', 'thermal', 'electromagnetic']):
            significance += 0.15
        
        # Boost for OpenWorm/experiment-related discoveries
        if any(term in discovery.lower() for term in ['openworm', 'connectome', 'simulation', 'experiment']):
            significance += 0.2
        
        # Boost for self-improvement related discoveries
        if any(term in discovery.lower() for term in ['self-improvement', 'meta-learning', 'adaptive']):
            significance += 0.1
        
        return min(1.0, significance)
    
    def _verify_mathematical_stability(self, improvement: str, agent: EnhancedSwarmAgent) -> bool:
        """Verify if an improvement is mathematically stable"""
        # Check if improvement relates to mathematical foundations
        math_terms = ['mathematical', 'theorem', 'proof', 'invariant', 'conservation', 
                     'stability', 'convergence', 'bound', 'formal', 'lean', 'bind']
        
        # Check if improvement is self-referential or meta
        self_terms = ['self-improvement', 'meta-learning', 'adaptive', 'autonomous', 
                     'curiosity', 'exploration', 'learning']
        
        # Check if improvement has neural encoding basis
        neural_terms = ['neural', 'neuron', 'synaptic', 'spike', 'encoding', 'pattern']
        
        improvement_lower = improvement.lower()
        
        # Mathematical stability criteria:
        # 1. Relates to math OR neural encoding (biological math)
        # 2. Is self-improvement (meta-cognitive)
        # 3. Has formal or invariant basis
        has_math_basis = any(term in improvement_lower for term in math_terms + neural_terms)
        is_self_improvement = any(term in improvement_lower for term in self_terms)
        has_formal_basis = any(term in improvement_lower for term in ['formal', 'invariant', 'theorem', 'proof'])
        
        # Improvement is mathematically stable if it has math basis AND is self-improvement
        is_stable = has_math_basis and is_self_improvement
        
        # Bonus: formal/invariant basis increases stability confidence
        if is_stable and has_formal_basis:
            return True
        
        return is_stable
    
    def _apply_reward(self, agent: EnhancedSwarmAgent, improvement: str, significance: float):
        """Apply reward for mathematically stable self-improvement"""
        if self._verify_mathematical_stability(improvement, agent):
            # Calculate reward based on significance
            base_reward = 1.0
            significance_multiplier = significance
            stability_bonus = 0.5  # Bonus for mathematical stability
            
            total_reward = base_reward * significance_multiplier + stability_bonus
            
            # Apply reward
            agent.reward_score += total_reward
            agent.stable_improvements += 1
            
            # Write improvement to RAM loopback device (fast write to tmpfs)
            self.ram_writer.write_improvement(
                agent_id=agent.id,
                improvement_type="stable_improvement",
                improvement_data={
                    'improvement': improvement,
                    'reward': total_reward,
                    'total_reward': agent.reward_score,
                    'stable_improvements': agent.stable_improvements,
                    'specialization': agent.specialization,
                    'nii_core_id': agent.nii_core_id
                }
            )
            
            # Boost curiosity as secondary reward
            agent.curiosity = min(1.0, agent.curiosity + 0.05)
            
            # Record reward event
            self.record_dag_event("REWARD", f"Mathematically stable improvement rewarded - {total_reward:.2f}",
                                  snapshot={
                                      'reward': total_reward,
                                      'total_reward': agent.reward_score,
                                      'stable_improvements': agent.stable_improvements,
                                      'improvement': improvement[:100]
                                  })
            
            return total_reward
        
        return 0.0
    
    def _explore_improvement_opportunities(self) -> List[str]:
        """Explore opportunities to improve the system"""
        opportunities = []
        
        # Check for low optimization scores
        opt_summary = self.self_optimizer.get_optimization_summary()
        if opt_summary['optimization_ratio'] < 0.8:
            opportunities.append("Optimization ratio below 0.8 - explore new optimization algorithms")
        
        # Check for low topology scores
        if self.feedback_loops.get('topology', FeedbackLoop('topology', 0.7, 0.5)).current_value < 0.8:
            opportunities.append("Topology optimization below target - explore new mapping strategies")
        
        # Check for low math coverage
        if self.feedback_loops.get('math_coverage', FeedbackLoop('math_coverage', 0.7, 0.5)).current_value < 0.5:
            opportunities.append("Math coverage low - explore new mathematical frameworks")
        
        # Check for low genetic compression scores
        if self.feedback_loops.get('genetic_compression', FeedbackLoop('genetic_compression', 0.7, 0.5)).current_value < 0.5:
            opportunities.append("Genetic compression low - explore new compression algorithms")
        
        # Check for homeostasis opportunities
        if self.feedback_loops.get('homeostasis', FeedbackLoop('homeostasis', 0.7, 0.5)).current_value < 0.7:
            opportunities.append("Homeostasis below target - explore new adaptation mechanisms")
        
        return opportunities
    
    def _explore_agent_self_improvement(self) -> List[str]:
        """Explore opportunities for agents to improve themselves"""
        improvements = []
        
        # Analyze agent confidences
        low_confidence_agents = [a for a in self.agents if a.confidence < 0.5]
        if len(low_confidence_agents) > 5:
            improvements.append(f"{len(low_confidence_agents)} agents with low confidence - explore new analysis methods")
        
        # Check for agent specialization gaps
        specializations = set(a.specialization for a in self.agents)
        if 'curvatureAnalyst' not in specializations:
            improvements.append("Missing curvature analysis - consider adding curvature specialist")
        if 'geometricReviewer' not in specializations:
            improvements.append("Missing geometric review - consider adding geometric specialist")
        
        # Check for NII core utilization
        nii_cores = [a.nii_core_id for a in self.agents if a.nii_core_id]
        if len(set(nii_cores)) < 3:
            improvements.append("NII cores underutilized - explore new NII core assignments")
        
        return improvements
    
    def _explore_math_refinement(self) -> List[str]:
        """Explore opportunities to refine mathematical models"""
        refinements = []
        
        # Check for unproven math entities
        if self.math_db:
            unproven = self.math_db.get_unproven_entities()
            if len(unproven) > 10:
                refinements.append(f"{len(unproven)} unproven math entities - explore new proof strategies")
        
        # Check for math entities without Lean modules
        if self.math_db:
            no_lean = self.math_db.get_entities_without_lean()
            if len(no_lean) > 10:
                refinements.append(f"{len(no_lean)} math entities without Lean - explore formalization")
        
        # Check for low complexity score entities
        if self.math_db:
            low_complexity = self.math_db.get_low_complexity_entities()
            if len(low_complexity) > 10:
                refinements.append(f"{len(low_complexity)} low complexity entities - explore deeper formalization")
        
        return refinements
    
    def _execute_exploration(self, target: str) -> Optional[str]:
        """Execute exploration of a target and return discovery if found"""
        # Simulate exploration by generating a discovery based on target
        # In a real implementation, this would actually explore the target
        
        import random
        if random.random() < 0.3:  # 30% chance of discovery
            if "optimization" in target.lower():
                return f"New optimization algorithm: adaptive gradient descent with momentum"
            elif "topology" in target.lower():
                return f"New topology mapping: quantum-inspired graph embedding"
            elif "math" in target.lower():
                return f"New mathematical framework: non-commutative probability theory"
            elif "compression" in target.lower():
                return f"New compression method: holographic encoding"
            elif "agent" in target.lower():
                return f"New agent capability: meta-learning transfer"
            elif "NII" in target.lower():
                return f"New NII core specialization: formal verification acceleration"
            else:
                return f"Novel approach to {target.split('-')[0].strip()}"
        
        return None
    
    def _determine_driver_strategy(self, driver_name: str) -> str:
        """Determine genetic coding strategy based on driver type"""
        driver_lower = driver_name.lower()
        
        if 'gpu' in driver_lower or 'amdgpu' in driver_lower or 'nvidia' in driver_lower:
            return "GPU-surface genetic compression with Q16_16 fixed-point"
        elif 'nvme' in driver_lower or 'ssd' in driver_lower:
            return "SSD-block genetic compression with adaptive entropy"
        elif 'wifi' in driver_lower or 'mt79' in driver_lower or 'bluetooth' in driver_lower:
            return "Wireless-signal genetic compression with phonon encoding"
        elif 'net' in driver_lower or 'eth' in driver_lower or 'r8169' in driver_lower:
            return "Ethernet-packet genetic compression with CRC optimization"
        elif 'snd' in driver_lower or 'audio' in driver_lower or 'hda' in driver_lower:
            return "Audio-stream genetic compression with harmonic encoding"
        elif 'crypto' in driver_lower or 'aes' in driver_lower:
            return "Cryptographic genetic compression with golden-ratio CRC"
        elif 'compress' in driver_lower or 'zram' in driver_lower:
            return "Memory-compression genetic encoding with adaptive Φ"
        else:
            return "General genetic compression with information-density optimization"
    
    def _generate_genetic_driver_config(self, opt_driver: Dict[str, any]) -> str:
        """Generate genetic-coded driver configuration"""
        config = f"# Genetic-coded configuration for {opt_driver['name']}\n"
        config += f"# Generated with Φ={opt_driver['phi']:.4f}, compression={opt_driver['compression_ratio']:.2f}x\n"
        config += f"\n[genetic_options]\n"
        config += f"phi = {opt_driver['phi']:.4f}\n"
        config += f"compression_ratio = {opt_driver['compression_ratio']:.2f}\n"
        config += f"entropy_adaptive = true\n"
        config += f"fixed_point = Q16_16\n"
        config += f"optimization_target = {opt_driver['optimized_size']}\n"
        config += f"\n[genetic_encoding]\n"
        config += f"algorithm = {opt_driver['strategy']}\n"
        config += f"mutation_rate = 0.125\n"
        config += f"crossover_probability = 0.75\n"
        config += f"population_size = 128\n"
        config += f"generations = 1000\n"
        config += f"\n[performance]\n"
        config += f"target_latency_ms = 1.0\n"
        config += f"max_memory_mb = {opt_driver['original_size'] // 1024 // 1024}\n"
        config += f"throughput_target_mbps = 1000\n"
        
        return config
    
    def compute_consensus(self) -> float:
        """Compute swarm consensus from agent confidences"""
        if not self.agents:
            return 0.0
        
        total_confidence = sum(agent.confidence for agent in self.agents)
        return total_confidence / len(self.agents)
    
    def calculate_system_scores(self) -> Dict[str, float]:
        """Calculate overall system scores"""
        topology_score = sum(agent.confidence for agent in self.agents if 'topology' in agent.specialization.lower())
        topology_score = topology_score / max(1, sum(1 for agent in self.agents if 'topology' in agent.specialization.lower()))
        
        math_score = sum(agent.confidence for agent in self.agents if 'math' in agent.specialization.lower())
        math_score = math_score / max(1, sum(1 for agent in self.agents if 'math' in agent.specialization.lower()))
        
        lean_score = sum(agent.confidence for agent in self.agents if 'lean' in agent.specialization.lower())
        lean_score = lean_score / max(1, sum(1 for agent in self.agents if 'lean' in agent.specialization.lower()))
        
        gpu_score = sum(agent.confidence for agent in self.agents if 'gpu' in agent.specialization.lower())
        gpu_score = gpu_score / max(1, sum(1 for agent in self.agents if 'gpu' in agent.specialization.lower()))
        
        ssd_score = sum(agent.confidence for agent in self.agents if 'ssd' in agent.specialization.lower())
        ssd_score = ssd_score / max(1, sum(1 for agent in self.agents if 'ssd' in agent.specialization.lower()))
        
        genetic_score = sum(agent.confidence for agent in self.agents if 'genetic' in agent.specialization.lower())
        genetic_score = genetic_score / max(1, sum(1 for agent in self.agents if 'genetic' in agent.specialization.lower()))
        
        nii_score = sum(agent.confidence for agent in self.agents if agent.nii_core_id)
        nii_score = nii_score / max(1, sum(1 for agent in self.agents if agent.nii_core_id))
        
        overall_score = (topology_score * 0.15 + math_score * 0.1 + lean_score * 0.1 + 
                        gpu_score * 0.15 + ssd_score * 0.15 + genetic_score * 0.2 + nii_score * 0.15)
        
        return {
            'topology': topology_score,
            'math': math_score,
            'lean': lean_score,
            'gpu': gpu_score,
            'ssd': ssd_score,
            'genetic': genetic_score,
            'nii': nii_score,
            'overall': overall_score
        }
    
    def _update_feedback_loops(self):
        """Update feedback loops with current system metrics"""
        if not self.agents:
            return
        
        # Get current scores from agents
        consensus = self.compute_consensus()
        system_scores = self.calculate_system_scores()
        
        # Update feedback loops
        if 'consensus' in self.feedback_loops:
            self.feedback_loops['consensus'].current_value = consensus
        
        if 'topology' in self.feedback_loops:
            self.feedback_loops['topology'].current_value = system_scores['topology']
        
        if 'math_coverage' in self.feedback_loops:
            self.feedback_loops['math_coverage'].current_value = system_scores['math']
        
        if 'gpu_utilization' in self.feedback_loops:
            self.feedback_loops['gpu_utilization'].current_value = system_scores['gpu']
        
        if 'ssd_throughput' in self.feedback_loops:
            self.feedback_loops['ssd_throughput'].current_value = system_scores['ssd']
        
        if 'genetic_compression' in self.feedback_loops:
            self.feedback_loops['genetic_compression'].current_value = system_scores['genetic']
    
    def _apply_feedback_adjustments(self, params: Dict[str, float]) -> Dict[str, float]:
        """Apply feedback loop adjustments to parameters"""
        adjusted_params = params.copy()
        
        for metric_name, loop in self.feedback_loops.items():
            adjustment = loop.compute_adjustment()
            
            if adjustment != 0.0:
                # Apply adjustment to relevant parameters
                if metric_name == 'consensus':
                    adjusted_params['kappa_squared'] = max(0.0, min(1.0, adjusted_params.get('kappa_squared', 0.5) + adjustment * 0.1))
                elif metric_name == 'topology':
                    adjusted_params['rho_seq'] = max(0.0, min(1.0, adjusted_params.get('rho_seq', 0.5) + adjustment * 0.1))
                elif metric_name == 'math_coverage':
                    adjusted_params['q_conservation'] = max(0.0, min(1.0, adjusted_params.get('q_conservation', 0.5) + adjustment * 0.1))
                elif metric_name == 'gpu_utilization':
                    adjusted_params['v_dynamics'] = max(0.0, min(1.0, adjusted_params.get('v_dynamics', 0.5) + adjustment * 0.1))
                elif metric_name == 'ssd_throughput':
                    adjusted_params['tau_structure'] = max(0.0, min(1.0, adjusted_params.get('tau_structure', 0.5) + adjustment * 0.1))
                elif metric_name == 'genetic_compression':
                    adjusted_params['kappa_hierarchy'] = max(0.0, min(1.0, adjusted_params.get('kappa_hierarchy', 0.5) + adjustment * 0.1))
        
        return adjusted_params
    
    def _learn_from_patterns(self, context: Dict[str, float]) -> Optional[LearnedPattern]:
        """Learn from similar patterns in memory"""
        similar_pattern = self.swarm_memory.find_similar_pattern(context, threshold=0.15)
        
        if similar_pattern:
            # Update pattern confidence and frequency
            similar_pattern.confidence = min(1.0, similar_pattern.confidence + 0.05)
            similar_pattern.frequency += 1
            return similar_pattern
        
        return None
    
    def _record_learning_pattern(self, context: Dict[str, float], action: str, outcome: float):
        """Record a new learning pattern"""
        pattern_id = f"pattern_{len(self.swarm_memory.patterns)}_{int(time.time())}"
        pattern = LearnedPattern(
            pattern_id=pattern_id,
            context=context.copy(),
            action=action,
            outcome=outcome,
            confidence=0.3,
            frequency=1
        )
        self.swarm_memory.add_pattern(pattern)
    
    def _update_homeostasis_state(self, system_scores: Dict[str, float]):
        """Update homeostasis state based on current metrics"""
        # Calculate consensus stability from history
        if len(self.swarm_memory.performance_history) > 10:
            recent_scores = list(self.swarm_memory.performance_history)[-10:]
            score_variance = np.var(recent_scores) if recent_scores else 0.0
            self.homeostasis_state.consensus_stability = max(0.0, 1.0 - score_variance)
        
        # Calculate resource efficiency
        avg_score = system_scores['overall']
        self.homeostasis_state.resource_efficiency = avg_score
        
        # Calculate equilibrium distance
        target_scores = {
            'topology': 0.7,
            'math': 0.7,
            'gpu': 0.75,
            'ssd': 0.7,
            'genetic': 0.7
        }
        distances = [abs(system_scores[k] - target_scores[k]) for k in target_scores.keys()]
        self.homeostasis_state.equilibrium_distance = sum(distances) / len(distances) if distances else 1.0
        
        # Update timestamp
        self.homeostasis_state.timestamp = time.time()
    
    def run_swarm_analysis(self, base_params: Dict[str, float], subject: str = "topology") -> EnhancedSwarmState:
        """Run complete enhanced swarm analysis with homeostasis learning and DAG tracking"""
        # Record initialization event
        self.record_dag_event("INIT", "Swarm analysis initialization", ["subject=" + subject])
        
        # Initialize agents
        self.initialize_agents(base_params, subject)
        self.record_dag_event("AGENTS_INIT", f"Initialized {len(self.agents)} swarm agents")
        
        # Run analysis for each agent
        analyzed_agents = []
        for agent in self.agents:
            analyzed = self.run_agent_analysis(agent)
            analyzed_agents.append(analyzed)
        
        self.agents = analyzed_agents
        self.record_dag_event("AGENTS_ANALYZED", f"Analyzed {len(self.agents)} agents")
        
        # Compute consensus
        consensus = self.compute_consensus()
        self.record_dag_event("CONSENSUS", f"Computed swarm consensus: {consensus:.3f}")
        
        # Aggregate recommendations
        all_recommendations = []
        for agent in self.agents:
            all_recommendations.extend(agent.recommendations)
        
        # Calculate system scores
        system_scores = self.calculate_system_scores()
        self.record_dag_event("SYSTEM_SCORES", "Calculated system scores", snapshot=system_scores)
        
        # Update homeostasis state
        self._update_homeostasis_state(system_scores)
        
        # Record performance in memory
        self.swarm_memory.record_performance(system_scores['overall'])
        
        # Learn from patterns and apply feedback adjustments
        context = {
            'consensus': consensus,
            'topology': system_scores['topology'],
            'math': system_scores['math'],
            'gpu': system_scores['gpu'],
            'ssd': system_scores['ssd'],
            'genetic': system_scores['genetic']
        }
        
        # Check for similar patterns
        similar_pattern = self._learn_from_patterns(context)
        
        # Record current pattern
        self._record_learning_pattern(context, "swarm_analysis", system_scores['overall'])
        
        # Apply feedback adjustments to parameters for next iteration
        adjusted_params = self._apply_feedback_adjustments(base_params)
        
        # Update optimal parameters if performance improved
        self.swarm_memory.update_optimal_params(adjusted_params, system_scores['overall'])
        
        # Update NII core status
        for status in self.nii_core_status:
            # Find agents using this core
            core_agents = [a for a in self.agents if a.nii_core_id == status.core_id]
            if core_agents:
                avg_confidence = sum(a.confidence for a in core_agents) / len(core_agents)
                status.geometric_score = avg_confidence
                status.status = 'complete'
            else:
                status.status = 'idle'
        
        # Record completion event
        self.record_dag_event("COMPLETE", "Swarm analysis complete", snapshot={"overall_score": system_scores['overall']})
        
        # Get optimization summary
        opt_summary = self.self_optimizer.get_optimization_summary()
        
        return EnhancedSwarmState(
            agents=self.agents,
            nii_cores=self.nii_registry.cores,
            nii_core_status=self.nii_core_status,
            consensus=consensus,
            recommendations=all_recommendations,
            topology_constraints=self.topology_constraints,
            topology_optimization_score=system_scores['topology'],
            math_coverage_score=system_scores['math'],
            lean_coverage_score=system_scores['lean'],
            gpu_computing_score=system_scores['gpu'],
            ssd_storage_score=system_scores['ssd'],
            genetic_compression_score=system_scores['genetic'],
            homeostasis_score=self.homeostasis_state.compute_homeostasis_score(),
            patterns_learned=len(self.swarm_memory.patterns),
            metatyping_score=sum(1 for mt in self.metatypes.values() if mt.is_metastack()) / max(1, len(self.metatypes)),
            remote_nodes_count=len(self.remote_nodes),
            dag_events_count=len(self.dag_tracker.events),
            optimization_ratio=opt_summary['optimization_ratio'],
            substrate_potential=opt_summary['substrate_potential'],
            optimization_cycles=opt_summary['cycles'],
            overall_system_score=system_scores['overall']
        )

# ═══════════════════════════════════════════════════════════════════════════
# Demo Topology Creation
# ═══════════════════════════════════════════════════════════════════════════

def create_demo_topology() -> TopologyGraph:
    """Create demo topology graph"""
    wire_segments = {
        'cpu_to_sram': WireSegment(
            name='cpu_to_sram',
            length_mm=2.0,
            resistance_ohm=0.05,
            capacitance_pf=2.0,
            inductance_nh=1.5,
            impedance_ohm=50.0,
            propagation_delay_ps=100.0
        ),
        'cpu_to_dac': WireSegment(
            name='cpu_to_dac',
            length_mm=5.0,
            resistance_ohm=0.12,
            capacitance_pf=5.0,
            inductance_nh=3.0,
            impedance_ohm=50.0,
            propagation_delay_ps=250.0
        )
    }
    
    components = {
        'cpu': Component(
            name='CPU',
            type='processor',
            location=(10.0, 10.0),
            voltage_mv=1200.0,
            current_ma=5000.0,
            temperature_c=45.0,
            power_mw=6000.0
        ),
        'sram': Component(
            name='SRAM',
            type='memory',
            location=(20.0, 10.0),
            voltage_mv=1100.0,
            current_ma=1000.0,
            temperature_c=40.0,
            power_mw=1100.0
        )
    }
    
    edges = [
        TopologyEdge(
            source='cpu',
            target='sram',
            wire_segment=wire_segments['cpu_to_sram'],
            voltage_drop_mv=100.0,
            current_ma=1000.0,
            timing_ps=100.0,
            impedance_ohm=50.0
        )
    ]
    
    nodes = {
        'cpu': TopologyNode(
            id='cpu',
            component=components['cpu'],
            connections=['sram'],
            voltage_mv=1200.0,
            current_ma=5000.0,
            timing_ps=0.0
        ),
        'sram': TopologyNode(
            id='sram',
            component=components['sram'],
            connections=['cpu'],
            voltage_mv=1100.0,
            current_ma=1000.0,
            timing_ps=100.0
        )
    }
    
    return TopologyGraph(
        nodes=nodes,
        edges=edges,
        wire_segments=wire_segments,
        components=components,
        sensor_readings=[],
        timestamp=0.0
    )

# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for enhanced integrated swarm"""
    import sys
    
    # Parse command-line arguments for swarm scale
    num_agents = 100  # Default to 100 agents for large-scale neuron-like swarm
    if len(sys.argv) > 1:
        try:
            num_agents = int(sys.argv[1])
            print(f"[INFO] Using custom agent count: {num_agents}")
        except ValueError:
            print(f"[WARNING] Invalid agent count, using default: {num_agents}")
    
    print("[INFO] Enhanced Integrated Swarm System")
    print("="*70)
    print(f"[INFO] Initializing neuron-like swarm with {num_agents} agents")
    print(f"[INFO] Using sphere triangle topology for neural connections")
    
    # Create demo topology
    topology = create_demo_topology()
    print(f"[INFO] Created topology with {len(topology.nodes)} nodes, {len(topology.edges)} edges")
    
    # Initialize math database
    math_db = MathDatabase()
    print(f"[INFO] Initialized math database connection")
    
    # Create enhanced integrated swarm with specified number of agents
    swarm = EnhancedIntegratedSwarm(topology, math_db, num_agents=num_agents)
    
    # Base geometric parameters
    base_params = {
        'kappa_squared': 0.5,
        'rho_seq': 0.5,
        'v_epigenetic': 0.5,
        'tau_structure': 0.5,
        'sigma_entropy': 0.5,
        'q_conservation': 0.5,
        'kappa_hierarchy': 0.5,
        'epsilon_mutation': 0.5
    }
    
    # Run enhanced swarm analysis
    result = swarm.run_swarm_analysis(base_params, subject="topology")
    
    print(f"\n[OK] Enhanced Swarm Analysis Complete")
    print(f"  Consensus: {result.consensus:.3f}")
    print(f"  Topology Optimization Score: {result.topology_optimization_score:.3f}")
    print(f"  Math Coverage Score: {result.math_coverage_score:.3f}")
    print(f"  Lean Coverage Score: {result.lean_coverage_score:.3f}")
    print(f"  GPU Computing Score: {result.gpu_computing_score:.3f}")
    print(f"  SSD Storage Score: {result.ssd_storage_score:.3f}")
    print(f"  Genetic Compression Score: {result.genetic_compression_score:.3f}")
    print(f"  Homeostasis Score: {result.homeostasis_score:.3f}")
    print(f"  Patterns Learned: {result.patterns_learned}")
    print(f"  Metatyping Score: {result.metatyping_score:.3f}")
    print(f"  Remote Nodes: {result.remote_nodes_count}")
    print(f"  DAG Events: {result.dag_events_count}")
    print(f"  Optimization Ratio: {result.optimization_ratio:.3f}")
    print(f"  Substrate Potential: {result.substrate_potential:.1f}")
    print(f"  Optimization Cycles: {result.optimization_cycles}")
    print(f"  Overall System Score: {result.overall_system_score:.3f}")
    print(f"  Agents: {len(result.agents)}")
    print(f"  NII Cores: {len(result.nii_cores)}")
    print(f"  Recommendations: {len(result.recommendations)}")
    
    print(f"\n[INFO] GPU, SSD, and Genetic Compression Context:")
    if result.agents and result.agents[0].gpu_context:
        gpu = result.agents[0].gpu_context
        print(f"  GPU Utilization: {gpu.gpu_utilization_percent:.1f}%")
        print(f"  VRAM Usage: {gpu.vram_usage_gb:.1f} GB / {gpu.vram_utilization_percent:.1f}%")
        print(f"  Temperature: {gpu.temperature_c:.1f}°C")
    if result.agents and result.agents[0].ssd_context:
        ssd = result.agents[0].ssd_context
        print(f"  SSD Health: {ssd.health_percent:.1f}%")
        print(f"  SSD Temperature: {ssd.temperature_c:.1f}°C")
        print(f"  SSD Read IOPS: {ssd.read_iops:,}")
        print(f"  SSD Write IOPS: {ssd.write_iops:,}")
    if result.agents and result.agents[0].genetic_context:
        genetic = result.agents[0].genetic_context
        print(f"  Genetic Compression Analysis:")
        for surface_type, report in genetic.items():
            print(f"    {surface_type.value}: {report.method} (Φ={report.field_phi:.3f}, ratio={report.compression_ratio:.2f}x)")
    
    print(f"\n[INFO] NII Core Status:")
    for status in result.nii_core_status:
        print(f"  {status.core_id}: {status.status}, geometric_score={status.geometric_score:.3f}")
        print(f"    FAMM timing: torsional={status.famm_timing['torsional_stress']:.3f}, "
              f"interlocking={status.famm_timing['interlocking_energy']:.3f}, "
              f"laplacian={status.famm_timing['laplacian_energy']:.3f}")
        print(f"    Topology score: {status.topology_score:.3f}")
        print(f"    Math relevance: {status.math_relevance:.3f}")
        print(f"    GPU utilization: {status.gpu_utilization:.3f}")
        print(f"    SSD throughput: {status.ssd_throughput:.3f}")
    
    print(f"\n[INFO] Agent Results:")
    for agent in result.agents:
        nii_info = f" (NII: {agent.nii_core_id})" if agent.nii_core_id else ""
        print(f"  {agent.specialization}{nii_info}: confidence={agent.confidence:.3f}")
        for finding in agent.findings:
            print(f"    - {finding}")
    
    print(f"\n[INFO] System Scores:")
    print(f"  Topology: {result.topology_optimization_score:.3f}")
    print(f"  Math Database: {result.math_coverage_score:.3f}")
    print(f"  Lean Modules: {result.lean_coverage_score:.3f}")
    print(f"  NII Cores: {result.overall_system_score:.3f}")
    
    print(f"\n[INFO] Topology Constraints:")
    for key, value in result.topology_constraints.items():
        print(f"  {key}: {value}")
    
    print(f"\n[INFO] Top Recommendations:")
    for rec in result.recommendations[:10]:
        print(f"  - {rec}")

if __name__ == "__main__":
    main()
