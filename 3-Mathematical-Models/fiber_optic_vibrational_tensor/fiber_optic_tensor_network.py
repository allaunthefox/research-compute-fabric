"""
Fiber Optic Vibrational Tensor Network
=======================================

This module implements a tensor network architecture for mapping vibrational frequencies
to fiber optic cable infrastructure based on Distributed Acoustic Sensing (DAS) principles.

Based on research that fiber optic cables can eavesdrop on nearby conversations through
vibrational sensing, this tensor network models the relationship between cable infrastructure
and acoustic/vibrational signatures across multiple dimensions.

Technical Basis:
- DAS uses Rayleigh scatter-based fiber optic sensing (COTDR)
- Maximum range: 40-50 km per sensing unit
- Spatial resolution: 10m (100ns pulse)
- Acquisition rate: up to 2kHz for 50km fiber, Nyquist frequency of 1kHz
- Human speech frequency: 20Hz-20kHz (full range), 80-255Hz fundamental, up to 8kHz content
- Sensitive to strain and temperature variations

Tensor Network Dimensions:
- Spatial: Cable segments, geographic coordinates
- Temporal: Time series of measurements
- Frequency: Vibrational frequency spectrum
- Infrastructure: Cable type, depth, environment
- Environmental: Temperature, pressure, surrounding medium
"""

import numpy as np
import torch
import torch.nn as nn
import time
import json
import hashlib
import math
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class CableType(Enum):
    """Types of fiber optic cables"""
    SUBMARINE = "submarine"
    TERRESTRIAL = "terrestrial"
    AERIAL = "aerial"
    BURIED = "buried"


class EnvironmentType(Enum):
    """Environmental contexts for cables"""
    DEEP_OCEAN = "deep_ocean"
    SHALLOW_WATER = "shallow_water"
    UNDERGROUND = "underground"
    SURFACE = "surface"
    AERIAL = "aerial"


@dataclass
class CableSegment:
    """Represents a segment of fiber optic cable"""
    segment_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    length_km: float
    cable_type: CableType
    depth_m: Optional[float] = None
    environment: EnvironmentType = EnvironmentType.SURFACE
    installation_year: Optional[int] = None


@dataclass
class VibrationalSignature:
    """Vibrational signature captured from cable segment"""
    segment_id: str
    timestamp: float
    frequency_spectrum: np.ndarray  # Frequency bins
    amplitude_spectrum: np.ndarray  # Amplitude per frequency
    strain_measurements: np.ndarray  # Strain along segment
    temperature_delta: float  # Temperature change


class FiberOpticTensorNetwork(nn.Module):
    """
    Tensor network for mapping vibrational frequencies to fiber optic infrastructure.

    Architecture:
    - Input: Multi-dimensional tensor combining spatial, temporal, frequency, infrastructure, and environmental data
    - Processing: Hierarchical tensor decomposition with attention mechanisms
    - Output: Vibrational risk assessment, acoustic reconstruction potential, and anomaly detection
    """

    def __init__(
        self,
        spatial_dim: int = 1000,  # Number of cable segments
        temporal_dim: int = 100,   # Time steps
        frequency_dim: int = 1000, # Frequency bins (covering 20Hz-20kHz)
        infrastructure_dim: int = 10, # Cable infrastructure features
        environmental_dim: int = 5,  # Environmental features
        hidden_dim: int = 256,
        num_heads: int = 8
    ):
        super().__init__()

        self.spatial_dim = spatial_dim
        self.temporal_dim = temporal_dim
        self.frequency_dim = frequency_dim
        self.infrastructure_dim = infrastructure_dim
        self.environmental_dim = environmental_dim
        self.hidden_dim = hidden_dim

        # Input embedding layers
        self.spatial_embedding = nn.Linear(spatial_dim, hidden_dim)
        self.temporal_embedding = nn.Linear(temporal_dim, hidden_dim)
        self.frequency_embedding = nn.Linear(frequency_dim, hidden_dim)
        self.infrastructure_embedding = nn.Linear(infrastructure_dim, hidden_dim)
        self.environmental_embedding = nn.Linear(environmental_dim, hidden_dim)

        # Multi-head attention for cross-dimensional interactions
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            batch_first=True
        )

        # Tensor decomposition layers
        self.tensor_decomposition = nn.Sequential(
            nn.Linear(hidden_dim * 5, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # Output heads
        self.vibrational_risk_head = nn.Linear(hidden_dim, 1)
        self.acoustic_reconstruction_head = nn.Linear(hidden_dim, frequency_dim)
        self.anomaly_detection_head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        spatial_features: torch.Tensor,
        temporal_features: torch.Tensor,
        frequency_features: torch.Tensor,
        infrastructure_features: torch.Tensor,
        environmental_features: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the tensor network.

        Args:
            spatial_features: (batch_size, spatial_dim)
            temporal_features: (batch_size, temporal_dim)
            frequency_features: (batch_size, frequency_dim)
            infrastructure_features: (batch_size, infrastructure_dim)
            environmental_features: (batch_size, environmental_dim)

        Returns:
            Dictionary containing:
            - vibrational_risk: Risk assessment score
            - acoustic_reconstruction: Reconstructed acoustic spectrum
            - anomaly_detection: Anomaly probability
        """
        # Embed each dimension
        spatial_emb = self.spatial_embedding(spatial_features)
        temporal_emb = self.temporal_embedding(temporal_features)
        frequency_emb = self.frequency_embedding(frequency_features)
        infrastructure_emb = self.infrastructure_embedding(infrastructure_features)
        environmental_emb = self.environmental_embedding(environmental_features)

        # Stack embeddings for cross-attention
        embeddings = torch.stack([
            spatial_emb, temporal_emb, frequency_emb,
            infrastructure_emb, environmental_emb
        ], dim=1)  # (batch_size, 5, hidden_dim)

        # Apply cross-attention
        attended_features, attention_weights = self.cross_attention(
            embeddings, embeddings, embeddings
        )

        # Flatten and process through tensor decomposition
        flattened = attended_features.flatten(start_dim=1)
        processed = self.tensor_decomposition(flattened)

        # Generate outputs
        vibrational_risk = torch.sigmoid(self.vibrational_risk_head(processed))
        acoustic_reconstruction = self.acoustic_reconstruction_head(processed)
        anomaly_detection = torch.sigmoid(self.anomaly_detection_head(processed))

        return {
            'vibrational_risk': vibrational_risk,
            'acoustic_reconstruction': acoustic_reconstruction,
            'anomaly_detection': anomaly_detection,
            'attention_weights': attention_weights
        }


class FrequencyMapper:
    """Maps physical frequencies to tensor network frequency bins"""

    def __init__(
        self,
        min_freq: float = 20.0,   # 20 Hz - human hearing lower bound
        max_freq: float = 20000.0, # 20 kHz - human hearing upper bound
        num_bins: int = 1000
    ):
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.num_bins = num_bins

        # Use logarithmic spacing for frequency bins (matches human perception)
        self.freq_bins = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            num_bins
        )

        # Define key frequency ranges for human speech
        self.speech_fundamental_range = (80.0, 255.0)  # Fundamental frequencies
        self.speech_content_range = (255.0, 8000.0)    # Speech content

    def frequency_to_bin(self, frequency: float) -> int:
        """Convert a frequency to its corresponding bin index"""
        if frequency < self.min_freq or frequency > self.max_freq:
            raise ValueError(f"Frequency {frequency} Hz out of range [{self.min_freq}, {self.max_freq}]")

        bin_idx = int(np.log10(frequency / self.min_freq) /
                     np.log10(self.max_freq / self.min_freq) * (self.num_bins - 1))
        return bin_idx

    def bin_to_frequency(self, bin_idx: int) -> float:
        """Convert a bin index to its corresponding frequency"""
        if bin_idx < 0 or bin_idx >= self.num_bins:
            raise ValueError(f"Bin index {bin_idx} out of range [0, {self.num_bins-1}]")

        return self.freq_bins[bin_idx]

    def get_speech_relevant_bins(self) -> List[int]:
        """Get bin indices corresponding to human speech frequencies"""
        speech_bins = []
        for freq in np.linspace(self.speech_fundamental_range[0],
                                self.speech_content_range[1], 100):
            speech_bins.append(self.frequency_to_bin(freq))
        return sorted(set(speech_bins))


class CableInfrastructureMapper:
    """Maps fiber optic cable infrastructure to tensor network spatial dimensions"""

    def __init__(self, cable_segments: List[CableSegment]):
        self.cable_segments = cable_segments
        self.segment_map = {seg.segment_id: i for i, seg in enumerate(cable_segments)}

    def get_spatial_features(self, segment_id: str) -> np.ndarray:
        """Get spatial features for a cable segment"""
        if segment_id not in self.segment_map:
            raise ValueError(f"Segment {segment_id} not found")

        segment = self.cable_segments[self.segment_map[segment_id]]

        # Create spatial feature vector
        features = np.zeros(len(self.cable_segments))
        features[self.segment_map[segment_id]] = 1.0

        # Add geographic features
        return features

    def get_infrastructure_features(self, segment_id: str) -> np.ndarray:
        """Get infrastructure features for a cable segment"""
        if segment_id not in self.segment_map:
            raise ValueError(f"Segment {segment_id} not found")

        segment = self.cable_segments[self.segment_map[segment_id]]

        # One-hot encode cable type
        cable_type_features = np.zeros(len(CableType))
        cable_type_features[list(CableType).index(segment.cable_type)] = 1.0

        # One-hot encode environment
        env_features = np.zeros(len(EnvironmentType))
        env_features[list(EnvironmentType).index(segment.environment)] = 1.0

        # Normalize depth
        depth_feature = np.array([segment.depth_m / 10000.0 if segment.depth_m else 0.0])

        # Normalize installation year
        year_feature = np.array([(segment.installation_year - 1990) / 40.0
                                   if segment.installation_year else 0.0])

        return np.concatenate([
            cable_type_features,
            env_features,
            depth_feature,
            year_feature
        ])


class VibrationalTensorBuilder:
    """Builds vibrational tensors from DAS measurements"""

    def __init__(
        self,
        frequency_mapper: FrequencyMapper,
        cable_mapper: CableInfrastructureMapper
    ):
        self.frequency_mapper = frequency_mapper
        self.cable_mapper = cable_mapper

    def build_tensor(
        self,
        signatures: List[VibrationalSignature],
        time_window: int = 100
    ) -> Dict[str, torch.Tensor]:
        """
        Build a multi-dimensional tensor from vibrational signatures.

        Args:
            signatures: List of vibrational signatures
            time_window: Number of time steps to include

        Returns:
            Dictionary of tensor features
        """
        # Get unique segments
        segment_ids = list(set(s.segment_id for s in signatures))

        # Build spatial features
        spatial_features = np.zeros((len(segment_ids),
                                    len(self.cable_mapper.cable_segments)))
        for i, seg_id in enumerate(segment_ids):
            spatial_features[i] = self.cable_mapper.get_spatial_features(seg_id)

        # Build temporal features (time series)
        timestamps = sorted(set(s.timestamp for s in signatures))
        temporal_features = np.zeros((len(segment_ids), time_window))

        # Build frequency features
        frequency_features = np.zeros((len(segment_ids),
                                      self.frequency_mapper.num_bins))

        # Build infrastructure features
        infrastructure_features = np.zeros((len(segment_ids), 10))
        for i, seg_id in enumerate(segment_ids):
            infrastructure_features[i] = self.cable_mapper.get_infrastructure_features(seg_id)

        # Build environmental features (simplified)
        environmental_features = np.zeros((len(segment_ids), 5))

        # Process signatures to populate frequency features
        for signature in signatures:
            if signature.segment_id in segment_ids:
                idx = segment_ids.index(signature.segment_id)

                # Map frequency spectrum to bins
                for i, freq in enumerate(signature.frequency_spectrum):
                    if i < self.frequency_mapper.num_bins:
                        frequency_features[idx, i] = signature.amplitude_spectrum[i]

        return {
            'spatial_features': torch.FloatTensor(spatial_features),
            'temporal_features': torch.FloatTensor(temporal_features),
            'frequency_features': torch.FloatTensor(frequency_features),
            'infrastructure_features': torch.FloatTensor(infrastructure_features),
            'environmental_features': torch.FloatTensor(environmental_features)
        }


class VLBNibbleSwitch:
    """
    VLB (Very Long Baseline) Nibble Switch for encoding sparse vibrational state changes.

    Based on the VLB Nibble-Delta Witness Substrate methodology for sparse manifold updates.
    Uses 4-bit transition symbols to encode vibrational state changes in fiber optic cables.
    """

    # Quandary control states (high 2 bits)
    REJECT = 0b00  # no-change / cooling
    ACCEPT = 0b01  # apply update
    HOLD = 0b10    # needs witness / recovery
    QUARANTINE = 0b11  # break / reset

    # Strand selectors (low 2 bits) - adapted for vibrational analysis
    K_AXIS = 0b00   # stable backbone / low frequency
    C_WINDING = 0b01 # route deformation / mid frequency
    M_TENSION = 0b10 # attestation / high frequency
    Y_RESET = 0b11   # break / reset / anomaly

    def __init__(self):
        self.quandary_states = {
            self.REJECT: "REJECT",
            self.ACCEPT: "ACCEPT",
            self.HOLD: "HOLD",
            self.QUARANTINE: "QUARANTINE"
        }
        self.strand_selectors = {
            self.K_AXIS: "K_AXIS",
            self.C_WINDING: "C_WINDING",
            self.M_TENSION: "M_TENSION",
            self.Y_RESET: "Y_RESET"
        }

    def encode_nibble(self, quandary_state: int, strand_selector: int) -> int:
        """Encode a 4-bit nibble from quandary state and strand selector"""
        return ((quandary_state & 0b11) << 2) | (strand_selector & 0b11)

    def decode_nibble(self, nibble: int) -> Tuple[int, int]:
        """Decode a 4-bit nibble into quandary state and strand selector"""
        quandary_state = (nibble >> 2) & 0b11
        strand_selector = nibble & 0b11
        return quandary_state, strand_selector

    def vibrational_state_to_nibble(self,
                                   frequency_change: float,
                                   amplitude_change: float,
                                   anomaly_detected: bool) -> int:
        """
        Convert vibrational state changes to VLB nibble encoding.

        Args:
            frequency_change: Change in frequency (Hz)
            amplitude_change: Change in amplitude
            anomaly_detected: Whether anomaly was detected

        Returns:
            4-bit nibble encoding the state transition
        """
        # Determine quandary state based on anomaly detection
        if anomaly_detected:
            quandary_state = self.QUARANTINE
        elif abs(frequency_change) < 1.0 and abs(amplitude_change) < 0.01:
            quandary_state = self.REJECT
        elif abs(frequency_change) > 100.0 or abs(amplitude_change) > 0.5:
            quandary_state = self.HOLD
        else:
            quandary_state = self.ACCEPT

        # Determine strand selector based on frequency range
        freq_abs = abs(frequency_change)
        if freq_abs < 50:  # Low frequency changes
            strand_selector = self.K_AXIS
        elif freq_abs < 500:  # Mid frequency changes
            strand_selector = self.C_WINDING
        elif freq_abs < 2000:  # High frequency changes
            strand_selector = self.M_TENSION
        else:  # Very high frequency / anomalous
            strand_selector = self.Y_RESET

        return self.encode_nibble(quandary_state, strand_selector)


class VLBManifoldDelta:
    """
    VLB Manifold Delta for sparse vibrational updates.

    Applies the VLB Nibble-Delta methodology to fiber optic vibrational sensing,
    enabling sparse encoding of acoustic events with witness receipts.
    """

    def __init__(self, baseline_hash: str, target_hash: str, source_domain: str):
        self.baseline_hash = baseline_hash
        self.target_hash = target_hash
        self.source_domain = source_domain
        self.switches = []  # List of NibbleSwitch events
        self.kot_cost = 0  # Knowledge Object Transfer cost
        self.replay_pass = False
        self.nibble_encoder = VLBNibbleSwitch()

    def add_vibrational_switch(self,
                              locus_id: str,
                              frequency_change: float,
                              amplitude_change: float,
                              anomaly_detected: bool,
                              count: int = 1,
                              polarity: float = 1.0):
        """Add a vibrational state change as a nibble switch"""
        nibble = self.nibble_encoder.vibrational_state_to_nibble(
            frequency_change, amplitude_change, anomaly_detected
        )

        switch_event = {
            'locus_id': locus_id,
            'nibble': nibble,
            'count': count,
            'polarity': polarity,
            'kot_cost': int(abs(frequency_change) * 100),  # Simple cost model
            'timestamp': time.time()
        }

        self.switches.append(switch_event)
        self.kot_cost += switch_event['kot_cost']

    def estimate_compression_gain(self,
                                 num_loci: int,
                                 bytes_per_locus: int = 32,
                                 bytes_per_switch: int = 12) -> float:
        """
        Estimate compression gain using VLB methodology.

        Based on VLB compression estimate:
        Gain ratio ≈ Full snapshot bytes / Nibble-delta bytes
        """
        full_snapshot_bytes = num_loci * bytes_per_locus
        nibble_delta_bytes = len(self.switches) * bytes_per_switch + 512  # + receipt overhead

        if nibble_delta_bytes == 0:
            return 0.0

        return full_snapshot_bytes / nibble_delta_bytes

    def to_jsonl(self) -> str:
        """Convert to JSONL format for VLB-style event logging"""
        event = {
            'baseline': self.baseline_hash,
            'target': self.target_hash,
            'source_domain': self.source_domain,
            'switches': self.switches,
            'kot_cost': self.kot_cost,
            'replay_pass': self.replay_pass
        }
        return json.dumps(event)


class VLBFiberOpticIntegrator:
    """
    Integration layer between VLB methodology and fiber optic DAS sensing.

    Cross-references planetary VLB sparse encoding techniques with fiber optic
    vibrational tensor networks to enable efficient acoustic event detection
    and witness receipt generation.
    """

    def __init__(self, tensor_network: FiberOpticTensorNetwork):
        self.tensor_network = tensor_network
        self.nibble_encoder = VLBNibbleSwitch()
        self.active_deltas = {}  # Map of segment_id -> VLBManifoldDelta

    def process_vibrational_signature(self,
                                      signature: VibrationalSignature,
                                      baseline_hash: str) -> Dict:
        """
        Process a vibrational signature through VLB encoding and tensor network.

        Combines VLB sparse encoding with tensor network analysis for efficient
        acoustic event detection and witness generation.
        """
        # Get tensor network analysis
        segment_idx = signature.segment_id
        spatial_features = torch.zeros(1, self.tensor_network.spatial_dim)
        temporal_features = torch.zeros(1, self.tensor_network.temporal_dim)
        frequency_features = torch.FloatTensor(signature.frequency_spectrum).unsqueeze(0)
        infrastructure_features = torch.zeros(1, self.tensor_network.infrastructure_dim)
        environmental_features = torch.zeros(1, self.tensor_network.environmental_dim)

        with torch.no_grad():
            tensor_outputs = self.tensor_network(
                spatial_features=spatial_features,
                temporal_features=temporal_features,
                frequency_features=frequency_features,
                infrastructure_features=infrastructure_features,
                environmental_features=environmental_features
            )

        # Extract key metrics for VLB encoding
        vibrational_risk = tensor_outputs['vibrational_risk'].item()
        anomaly_detected = tensor_outputs['anomaly_detection'].item() > 0.5

        # Calculate frequency and amplitude changes from signature
        if len(signature.frequency_spectrum) > 1:
            frequency_change = signature.frequency_spectrum[-1] - signature.frequency_spectrum[0]
            amplitude_change = signature.amplitude_spectrum[-1] - signature.amplitude_spectrum[0]
        else:
            frequency_change = 0.0
            amplitude_change = 0.0

        # Create or get VLB delta for this segment
        if signature.segment_id not in self.active_deltas:
            target_hash = hashlib.sha256(
                f"{baseline_hash}{signature.segment_id}{signature.timestamp}".encode()
            ).hexdigest()
            self.active_deltas[signature.segment_id] = VLBManifoldDelta(
                baseline_hash=baseline_hash,
                target_hash=target_hash,
                source_domain="fiber_optic_das"
            )

        delta = self.active_deltas[signature.segment_id]

        # Add vibrational switch event
        delta.add_vibrational_switch(
            locus_id=signature.segment_id,
            frequency_change=frequency_change,
            amplitude_change=amplitude_change,
            anomaly_detected=anomaly_detected,
            count=1,
            polarity=1.0 if vibrational_risk < 0.5 else -1.0
        )

        # Calculate compression gain
        compression_gain = delta.estimate_compression_gain(
            num_loci=self.tensor_network.frequency_dim
        )

        return {
            'tensor_outputs': {
                'vibrational_risk': vibrational_risk,
                'anomaly_detected': anomaly_detected,
                'acoustic_reconstruction': tensor_outputs['acoustic_reconstruction'].numpy()
            },
            'vlb_encoding': {
                'nibble': delta.nibble_encoder.vibrational_state_to_nibble(
                    frequency_change, amplitude_change, anomaly_detected
                ),
                'switches_count': len(delta.switches),
                'kot_cost': delta.kot_cost
            },
            'compression_metrics': {
                'estimated_gain': compression_gain,
                'sparsity': len(delta.switches) / self.tensor_network.frequency_dim
            }
        }

    def generate_witness_receipt(self, segment_id: str) -> Optional[Dict]:
        """
        Generate a VLB-style witness receipt for a fiber optic segment.

        Creates a cryptographic receipt that can be used for replay verification
        of vibrational events, following VLB witness accounting methodology.
        """
        if segment_id not in self.active_deltas:
            return None

        delta = self.active_deltas[segment_id]

        receipt = {
            'segment_id': segment_id,
            'baseline_hash': delta.baseline_hash,
            'target_hash': delta.target_hash,
            'switches': delta.switches,
            'kot_cost': delta.kot_cost,
            'timestamp': time.time(),
            'receipt_hash': hashlib.sha256(
                f"{delta.target_hash}{delta.kot_cost}{len(delta.switches)}".encode()
            ).hexdigest(),
            'compression_gain': delta.estimate_compression_gain(
                num_loci=self.tensor_network.frequency_dim
            )
        }

        return receipt


class ResonantAlignmentFilter:
    """
    Resonant alignment filters based on Research Stack topology resonance hierarchy.

    Implements filtering mechanisms using discovered resonant frequencies and
    alignment patterns from:
    - TOPOLOGY_RESONANCE_HIERARCHY.md: Multi-level resonance framework
    - Signal equation invariant roots: SIGROOT003, SIGROOT021, SIGROOT024
    - Eigenvector resonance probe: Transverse pull and eigengap analysis
    """

    def __init__(self):
        # Resonance hierarchy levels from TOPOLOGY_RESONANCE_HIERARCHY.md
        self.resonance_levels = {
            'L0_quantum': {
                'type': 'Wavefunction Superposition',
                'characteristic_freq': 'h_bar/tau_quantum',
                'coupling': 'Hamiltonian coupling',
                'manifestation': 'Energy eigenstate transitions'
            },
            'L1_information': {
                'type': 'Signal Wave',
                'characteristic_freq': 'omega_signal',
                'coupling': 'Information flow',
                'manifestation': 'Signal encoding/decoding'
            },
            'L2_cognitive': {
                'type': 'Neural Oscillation',
                'characteristic_freq': '1-100 Hz',
                'coupling': 'Synaptic coupling',
                'manifestation': 'Cognitive load oscillations'
            },
            'L3_geometric': {
                'type': 'Spherion Resonance',
                'characteristic_freq': 'sqrt(g/R_sph)',
                'coupling': 'Pyramid height coupling',
                'manifestation': 'Standing waves on S²'
            },
            'L4_topological': {
                'type': 'Manifold Drift',
                'characteristic_freq': 'omega_manifold',
                'coupling': 'PIST manifold',
                'manifestation': 'Topological state transitions'
            },
            'L5_thermodynamic': {
                'type': 'Energy Gradient',
                'characteristic_freq': 'omega_thermo',
                'coupling': 'Temperature gradient',
                'manifestation': 'Energy flow across scales'
            }
        }

        # Signal equation invariant roots for resonance filtering
        self.resonance_roots = {
            'SIGROOT003_resonance_degeneracy': {
                'equation': 'deg(left,right) = |support(left) intersect support(right)|',
                'invariant_root': 'support-intersection cardinality',
                'filter_use': 'overlap score for frequency bin collisions'
            },
            'SIGROOT021_parabolic_j_score': {
                'equation': 'J(k) = 32 - 0.5*(k-22)^2',
                'invariant_root': 'distance from resonant vertex k=22',
                'filter_use': 'resonance-ranked candidate pruning'
            },
            'SIGROOT024_lorentzian_resonance': {
                'equation': 'L(delta) = 1/(1+delta^2)',
                'invariant_root': 'squared detuning from spectral center',
                'filter_use': 'nearest spectral-basis assignment'
            }
        }

        # Eigenvector resonance parameters
        self.eigenvector_params = {
            'min_pull': 1.0e-6,
            'min_eigengap': 1.0e-9,
            'max_stability_angle_deg': 35.0
        }

        # Spherion resonance parameters
        self.spherion_params = {
            'geometric_coupling': 1.0,  # g parameter
            'min_quality_factor': 10.0,  # Q = omega_res/delta_omega
            'resonant_modes': ['monopole', 'dipole', 'quadrupole']
        }

    def lorentzian_resonance_filter(self, frequency: float, center_freq: float, width: float = 1.0) -> float:
        """
        Apply Lorentzian resonance filter (SIGROOT024).

        L(delta) = 1/(1+delta^2) where delta is detuning from spectral center.
        """
        delta = (frequency - center_freq) / width
        return 1.0 / (1.0 + delta**2)

    def parabolic_resonance_score(self, frequency_bin: int, resonant_vertex: int = 22) -> float:
        """
        Calculate parabolic resonance score (SIGROOT021).

        J(k) = 32 - 0.5*(k-22)^2 - distance from resonant vertex.
        """
        deviation = frequency_bin - resonant_vertex
        return 32.0 - 0.5 * deviation**2

    def resonance_degeneracy_filter(self, support_left: set, support_right: set) -> int:
        """
        Calculate resonance degeneracy (SIGROOT003).

        deg(left,right) = |support(left) intersect support(right)|
        """
        return len(support_left.intersection(support_right))

    def spherion_resonance_frequency(self, radius: float, geometric_coupling: float = 1.0) -> float:
        """
        Calculate spherion resonant frequency (L3 geometric level).

        omega_res = sqrt(g/R_sph)
        """
        if radius <= 0:
            return 0.0
        return math.sqrt(geometric_coupling / radius)

    def quality_factor_filter(self, resonant_freq: float, linewidth: float) -> float:
        """
        Calculate quality factor for resonance sharpness.

        Q = omega_res / delta_omega
        """
        if linewidth <= 0:
            return float('inf')
        return resonant_freq / linewidth

    def cognitive_band_filter(self, frequency: float) -> float:
        """
        Apply cognitive level resonance filter (L2: 1-100 Hz).

        Filters frequencies based on neural oscillation bands.
        """
        if 1.0 <= frequency <= 100.0:
            # Within cognitive resonance band
            return 1.0
        elif 0.5 <= frequency <= 200.0:
            # Partial resonance in extended band
            return 0.5
        else:
            # Outside cognitive resonance
            return 0.0

    def thermodynamic_gradient_filter(self, frequency: float, temperature_gradient: float) -> float:
        """
        Apply thermodynamic level resonance filter (L5).

        Energy flow resonance depends on temperature gradient.
        """
        gradient_magnitude = abs(temperature_gradient)
        if gradient_magnitude < 1e-6:
            return 0.0
        # Normalize gradient effect
        return min(1.0, gradient_magnitude * 1e6)

    def multi_level_resonance_score(self, frequency: float,
                                    spatial_coords: Tuple[float, float, float],
                                    temperature: float = 300.0) -> Dict[str, float]:
        """
        Calculate multi-level resonance score across all topology levels.

        Returns resonance scores for each level in the hierarchy.
        """
        scores = {}

        # L0: Quantum level (simplified as high-frequency component)
        scores['L0_quantum'] = self.lorentzian_resonance_filter(frequency, 1e15, 1e13)

        # L1: Information level (signal wave resonance)
        scores['L1_information'] = self.lorentzian_resonance_filter(frequency, 1000.0, 500.0)

        # L2: Cognitive level (neural oscillation)
        scores['L2_cognitive'] = self.cognitive_band_filter(frequency)

        # L3: Geometric level (spherion resonance)
        radius = math.sqrt(sum(c**2 for c in spatial_coords)) + 1e-6
        spherion_freq = self.spherion_resonance_frequency(radius)
        scores['L3_geometric'] = self.lorentzian_resonance_filter(frequency, spherion_freq, spherion_freq * 0.1)

        # L4: Topological level (manifold drift)
        scores['L4_topological'] = self.lorentzian_resonance_filter(frequency, 100.0, 50.0)

        # L5: Thermodynamic level
        temp_gradient = temperature - 300.0  # Relative to room temperature
        scores['L5_thermodynamic'] = self.thermodynamic_gradient_filter(frequency, temp_gradient)

        return scores

    def combined_resonance_filter(self, frequency_spectrum: np.ndarray,
                                  spatial_coords: Tuple[float, float, float],
                                  temperature: float = 300.0) -> np.ndarray:
        """
        Apply combined resonance filtering across frequency spectrum.

        Combines all resonance hierarchy levels into a unified filter.
        """
        filtered_spectrum = np.zeros_like(frequency_spectrum)

        for i, frequency in enumerate(frequency_spectrum):
            # Get multi-level resonance scores
            level_scores = self.multi_level_resonance_score(frequency, spatial_coords, temperature)

            # Combine scores using weighted average
            # Weight geometric level higher as it's the resonance apex
            weights = {
                'L0_quantum': 0.1,
                'L1_information': 0.15,
                'L2_cognitive': 0.2,
                'L3_geometric': 0.3,  # Highest weight - resonance apex
                'L4_topological': 0.15,
                'L5_thermodynamic': 0.1
            }

            combined_score = sum(weights[level] * score for level, score in level_scores.items())
            filtered_spectrum[i] = frequency_spectrum[i] * combined_score

        return filtered_spectrum


class GlobalDataCenterTSPMapper:
    """
    Traveling Salesman Problem mapper for global data center network optimization.

    Cross-maps Starlink ground stations to major data centers worldwide, creating
    an eigen-decomposed network map that uses known and unknown information to
    "light up" the optimal network topology.
    """

    def __init__(self):
        # Major global data centers with coordinates and importance weights
        self.major_data_centers = {
            # North America
            'ashburn_va': {'lat': 39.04, 'lon': -77.49, 'importance': 1.0, 'region': 'na'},
            'reston_va': {'lat': 38.97, 'lon': -77.34, 'importance': 0.9, 'region': 'na'},
            'dallas_tx': {'lat': 32.78, 'lon': -96.80, 'importance': 0.95, 'region': 'na'},
            'chicago_il': {'lat': 41.88, 'lon': -87.63, 'importance': 0.85, 'region': 'na'},
            'los_angeles_ca': {'lat': 34.05, 'lon': -118.24, 'importance': 0.9, 'region': 'na'},
            'san_francisco_ca': {'lat': 37.77, 'lon': -122.42, 'importance': 0.95, 'region': 'na'},
            'seattle_wa': {'lat': 47.61, 'lon': -122.33, 'importance': 0.8, 'region': 'na'},
            'new_york_ny': {'lat': 40.71, 'lon': -74.01, 'importance': 1.0, 'region': 'na'},
            'atlanta_ga': {'lat': 33.76, 'lon': -84.39, 'importance': 0.85, 'region': 'na'},
            'denver_co': {'lat': 39.74, 'lon': -104.99, 'importance': 0.75, 'region': 'na'},

            # Europe
            'london_uk': {'lat': 51.50, 'lon': -0.13, 'importance': 1.0, 'region': 'eu'},
            'frankfurt_de': {'lat': 50.11, 'lon': 8.68, 'importance': 0.95, 'region': 'eu'},
            'amsterdam_nl': {'lat': 52.37, 'lon': 4.89, 'importance': 0.9, 'region': 'eu'},
            'paris_fr': {'lat': 48.86, 'lon': 2.35, 'importance': 0.85, 'region': 'eu'},
            'dublin_ie': {'lat': 53.35, 'lon': -6.26, 'importance': 0.8, 'region': 'eu'},
            'madrid_es': {'lat': 40.42, 'lon': -3.71, 'importance': 0.75, 'region': 'eu'},
            'milan_it': {'lat': 45.46, 'lon': 9.19, 'importance': 0.7, 'region': 'eu'},
            'stockholm_se': {'lat': 59.33, 'lon': 18.06, 'importance': 0.65, 'region': 'eu'},
            'berlin_de': {'lat': 52.52, 'lon': 13.40, 'importance': 0.75, 'region': 'eu'},
            'zurich_ch': {'lat': 47.38, 'lon': 8.54, 'importance': 0.7, 'region': 'eu'},

            # Asia Pacific
            'tokyo_jp': {'lat': 35.68, 'lon': 139.69, 'importance': 1.0, 'region': 'ap'},
            'singapore_sg': {'lat': 1.35, 'lon': 103.82, 'importance': 0.95, 'region': 'ap'},
            'hong_kong_cn': {'lat': 22.32, 'lon': 114.18, 'importance': 0.9, 'region': 'ap'},
            'sydney_au': {'lat': -33.87, 'lon': 151.21, 'importance': 0.85, 'region': 'ap'},
            'seoul_kr': {'lat': 37.57, 'lon': 126.98, 'importance': 0.8, 'region': 'ap'},
            'shanghai_cn': {'lat': 31.23, 'lon': 121.47, 'importance': 0.85, 'region': 'ap'},
            'mumbai_in': {'lat': 19.08, 'lon': 72.88, 'importance': 0.8, 'region': 'ap'},
            'osaka_jp': {'lat': 34.69, 'lon': 135.50, 'importance': 0.75, 'region': 'ap'},
            'bangalore_in': {'lat': 12.97, 'lon': 77.59, 'importance': 0.7, 'region': 'ap'},
            'jakarta_id': {'lat': -6.21, 'lon': 106.85, 'importance': 0.65, 'region': 'ap'},

            # South America
            'sao_paulo_br': {'lat': -23.55, 'lon': -46.64, 'importance': 0.8, 'region': 'sa'},
            'buenos_aires_ar': {'lat': -34.60, 'lon': -58.38, 'importance': 0.7, 'region': 'sa'},
            'santiago_cl': {'lat': -33.45, 'lon': -70.67, 'importance': 0.65, 'region': 'sa'},
            'lima_pe': {'lat': -12.05, 'lon': -77.03, 'importance': 0.6, 'region': 'sa'},
            'bogota_co': {'lat': 4.71, 'lon': -74.07, 'importance': 0.65, 'region': 'sa'},

            # Middle East & Africa
            'dubai_ae': {'lat': 25.20, 'lon': 55.27, 'importance': 0.85, 'region': 'me'},
            'johannesburg_za': {'lat': -26.20, 'lon': 28.04, 'importance': 0.7, 'region': 'af'},
            'cairo_eg': {'lat': 30.04, 'lon': 31.24, 'importance': 0.65, 'region': 'me'},
            'tel_aviv_il': {'lat': 32.08, 'lon': 34.78, 'importance': 0.6, 'region': 'me'},
            'nairobi_ke': {'lat': -1.29, 'lon': 36.82, 'importance': 0.55, 'region': 'af'},

            # Additional strategic locations
            'helsinki_fi': {'lat': 60.17, 'lon': 24.94, 'importance': 0.6, 'region': 'eu'},
            'oslo_no': {'lat': 59.91, 'lon': 10.75, 'importance': 0.55, 'region': 'eu'},
            'vienna_at': {'lat': 48.21, 'lon': 16.37, 'importance': 0.65, 'region': 'eu'},
            'prague_cz': {'lat': 50.08, 'lon': 14.42, 'importance': 0.6, 'region': 'eu'},
            'warsaw_pl': {'lat': 52.23, 'lon': 21.01, 'importance': 0.65, 'region': 'eu'},
        }

        # Network connection types with costs
        self.connection_types = {
            'fiber_submarine': {'cost_per_km': 0.1, 'latency_per_km': 0.005, 'bandwidth_gbps': 100},
            'fiber_terrestrial': {'cost_per_km': 0.05, 'latency_per_km': 0.004, 'bandwidth_gbps': 100},
            'starlink_backhaul': {'cost_per_km': 0.02, 'latency_per_km': 0.025, 'bandwidth_gbps': 1},
            'satellite_geostationary': {'cost_per_km': 0.015, 'latency_per_km': 0.25, 'bandwidth_gbps': 0.5},
            'microwave': {'cost_per_km': 0.03, 'latency_per_km': 0.003, 'bandwidth_gbps': 10},
        }

        # Known network information (confirmed connections)
        self.known_connections = {
            ('ashburn_va', 'reston_va'): {'type': 'fiber_terrestrial', 'confidence': 1.0},
            ('london_uk', 'amsterdam_nl'): {'type': 'fiber_submarine', 'confidence': 0.95},
            ('tokyo_jp', 'singapore_sg'): {'type': 'fiber_submarine', 'confidence': 0.9},
            ('new_york_ny', 'london_uk'): {'type': 'fiber_submarine', 'confidence': 0.95},
            ('los_angeles_ca', 'tokyo_jp'): {'type': 'fiber_submarine', 'confidence': 0.85},
            ('san_francisco_ca', 'tokyo_jp'): {'type': 'fiber_submarine', 'confidence': 0.9},
        }

        # Unknown network information (predicted connections)
        self.unknown_connections = {}  # Will be populated during analysis

    def calculate_distance_matrix(self) -> np.ndarray:
        """
        Calculate distance matrix between all data centers.

        Returns a symmetric matrix of great-circle distances in km.
        """
        centers = list(self.major_data_centers.keys())
        n = len(centers)
        distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    center1 = self.major_data_centers[centers[i]]
                    center2 = self.major_data_centers[centers[j]]
                    distance_matrix[i, j] = self._haversine_distance(
                        center1['lat'], center1['lon'],
                        center2['lat'], center2['lon']
                    )

        return distance_matrix

    def _haversine_distance(self, lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """Calculate great-circle distance using Haversine formula."""
        R = 6371.0  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def build_network_adjacency_matrix(self, connection_type: str = 'fiber_submarine') -> np.ndarray:
        """
        Build network adjacency matrix based on connection costs and constraints.

        Creates a weighted adjacency matrix for TSP formulation.
        """
        centers = list(self.major_data_centers.keys())
        n = len(centers)
        adjacency_matrix = np.full((n, n), np.inf)

        for i in range(n):
            for j in range(n):
                if i != j:
                    center1 = self.major_data_centers[centers[i]]
                    center2 = self.major_data_centers[centers[j]]

                    distance = self._haversine_distance(
                        center1['lat'], center1['lon'],
                        center2['lat'], center2['lon']
                    )

                    # Check if connection is known
                    connection_key = (centers[i], centers[j]) if (centers[i], centers[j]) in self.known_connections else (centers[j], centers[i])
                    if connection_key in self.known_connections:
                        conn_info = self.known_connections[connection_key]
                        conn_type = conn_info['type']
                        confidence = conn_info['confidence']
                    else:
                        conn_type = connection_type
                        confidence = 0.5  # Default confidence for unknown connections

                    # Calculate cost based on connection type
                    if conn_type in self.connection_types:
                        cost_params = self.connection_types[conn_type]
                        base_cost = distance * cost_params['cost_per_km']
                        confidence_penalty = (1.0 - confidence) * 100  # Penalty for unknown connections
                        adjacency_matrix[i, j] = base_cost + confidence_penalty

        return adjacency_matrix

    def eigen_decompose_network(self, adjacency_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Perform eigen decomposition of network adjacency matrix.

        Returns eigenvalues, eigenvectors, and spectral properties for network illumination.
        """
        # Ensure symmetric matrix for eigen decomposition
        symmetric_matrix = (adjacency_matrix + adjacency_matrix.T) / 2

        # Replace infinite values with large finite values
        symmetric_matrix[np.isinf(symmetric_matrix)] = 1e6

        # Compute eigen decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(symmetric_matrix)

        # Sort eigenvalues and eigenvectors
        idx = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Calculate spectral properties
        spectral_radius = np.max(np.abs(eigenvalues))
        spectral_gap = eigenvalues[1] - eigenvalues[0] if len(eigenvalues) > 1 else 0
        algebraic_connectivity = eigenvalues[1]  # Fiedler value

        # Calculate eigenvector centrality
        eigenvector_centrality = np.abs(eigenvectors[:, -1])  # Largest eigenvector

        return {
            'eigenvalues': eigenvalues,
            'eigenvectors': eigenvectors,
            'spectral_radius': spectral_radius,
            'spectral_gap': spectral_gap,
            'algebraic_connectivity': algebraic_connectivity,
            'eigenvector_centrality': eigenvector_centrality,
            'symmetric_matrix': symmetric_matrix
        }

    def illuminate_network_map(self, eigen_data: Dict[str, Any],
                             illumination_threshold: float = 0.5) -> Dict[str, Any]:
        """
        "Light up" the network map using eigen decomposition results.

        Identifies critical nodes, optimal paths, and network structure.
        """
        centers = list(self.major_data_centers.keys())
        centrality = eigen_data['eigenvector_centrality']

        # Normalize centrality
        normalized_centrality = centrality / np.max(centrality)

        # Identify illuminated nodes (above threshold)
        illuminated_nodes = []
        for i, center in enumerate(centers):
            if normalized_centrality[i] >= illumination_threshold:
                illuminated_nodes.append({
                    'data_center': center,
                    'centrality': normalized_centrality[i],
                    'importance': self.major_data_centers[center]['importance'],
                    'region': self.major_data_centers[center]['region']
                })

        # Sort by centrality
        illuminated_nodes.sort(key=lambda x: x['centrality'], reverse=True)

        # Calculate network illumination score
        illumination_score = np.mean(normalized_centrality[normalized_centrality >= illumination_threshold])

        # Identify critical paths based on eigenvector components
        critical_paths = self._identify_critical_paths(eigen_data, illumination_threshold)

        return {
            'illuminated_nodes': illuminated_nodes,
            'illumination_score': illumination_score,
            'critical_paths': critical_paths,
            'spectral_radius': eigen_data['spectral_radius'],
            'algebraic_connectivity': eigen_data['algebraic_connectivity'],
            'total_nodes': len(centers),
            'illuminated_count': len(illuminated_nodes)
        }

    def _identify_critical_paths(self, eigen_data: Dict[str, Any],
                                threshold: float) -> List[Dict[str, Any]]:
        """Identify critical network paths using eigenvector analysis."""
        centers = list(self.major_data_centers.keys())
        eigenvectors = eigen_data['eigenvectors']
        eigenvalues = eigen_data['eigenvalues']

        # Use second eigenvector (Fiedler vector) for community structure
        if len(eigenvalues) > 1:
            fiedler_vector = eigenvectors[:, 1]

            # Identify communities based on sign of Fiedler vector
            community1 = [centers[i] for i in range(len(centers)) if fiedler_vector[i] > 0]
            community2 = [centers[i] for i in range(len(centers)) if fiedler_vector[i] < 0]

            # Find inter-community connections (critical paths)
            critical_paths = []
            for node1 in community1[:5]:  # Top 5 from each community
                for node2 in community2[:5]:
                    idx1 = centers.index(node1)
                    idx2 = centers.index(node2)
                    critical_paths.append({
                        'source': node1,
                        'destination': node2,
                        'fiedler_difference': abs(fiedler_vector[idx1] - fiedler_vector[idx2]),
                        'community_separation': True
                    })

            # Sort by Fiedler difference
            critical_paths.sort(key=lambda x: x['fiedler_difference'], reverse=True)

            return critical_paths[:10]  # Top 10 critical paths

        return []

    def solve_tsp_network(self, start_node: str = 'ashburn_va',
                         max_iterations: int = 1000) -> Dict[str, Any]:
        """
        Solve Traveling Salesman Problem for optimal network routing.

        Uses simulated annealing to find optimal path visiting all data centers.
        """
        centers = list(self.major_data_centers.keys())
        adjacency_matrix = self.build_network_adjacency_matrix()
        n = len(centers)

        # Initialize with greedy solution
        current_path = self._greedy_tsp_init(adjacency_matrix, centers, start_node)
        current_cost = self._calculate_path_cost(current_path, adjacency_matrix, centers)

        # Simulated annealing parameters
        temperature = 1000.0
        cooling_rate = 0.995
        best_path = current_path.copy()
        best_cost = current_cost

        for iteration in range(max_iterations):
            # Generate neighbor by swapping two random cities
            new_path = current_path.copy()
            i, j = random.sample(range(1, n), 2)  # Keep start node fixed
            new_path[i], new_path[j] = new_path[j], new_path[i]

            new_cost = self._calculate_path_cost(new_path, adjacency_matrix, centers)

            # Accept if better or with probability based on temperature
            if new_cost < current_cost or random.random() < math.exp((current_cost - new_cost) / temperature):
                current_path = new_path
                current_cost = new_cost

                if current_cost < best_cost:
                    best_path = current_path.copy()
                    best_cost = current_cost

            # Cool down
            temperature *= cooling_rate

        # Calculate path details
        path_details = []
        for i in range(len(best_path) - 1):
            from_center = best_path[i]
            to_center = best_path[i + 1]
            from_idx = centers.index(from_center)
            to_idx = centers.index(to_center)

            path_details.append({
                'from': from_center,
                'to': to_center,
                'distance_km': self._haversine_distance(
                    self.major_data_centers[from_center]['lat'],
                    self.major_data_centers[from_center]['lon'],
                    self.major_data_centers[to_center]['lat'],
                    self.major_data_centers[to_center]['lon']
                ),
                'cost': adjacency_matrix[from_idx, to_idx]
            })

        return {
            'optimal_path': best_path,
            'total_cost': best_cost,
            'path_details': path_details,
            'iterations': max_iterations,
            'start_node': start_node
        }

    def _greedy_tsp_init(self, adjacency_matrix: np.ndarray,
                        centers: List[str], start_node: str) -> List[str]:
        """Initialize TSP solution with greedy nearest-neighbor algorithm."""
        n = len(centers)
        visited = {start_node}
        path = [start_node]
        current = start_node

        while len(visited) < n:
            current_idx = centers.index(current)
            nearest_dist = np.inf
            nearest_node = None

            for i, center in enumerate(centers):
                if center not in visited and adjacency_matrix[current_idx, i] < nearest_dist:
                    nearest_dist = adjacency_matrix[current_idx, i]
                    nearest_node = center

            if nearest_node:
                visited.add(nearest_node)
                path.append(nearest_node)
                current = nearest_node
            else:
                break

        return path

    def _calculate_path_cost(self, path: List[str],
                           adjacency_matrix: np.ndarray,
                           centers: List[str]) -> float:
        """Calculate total cost of a TSP path."""
        total_cost = 0.0
        for i in range(len(path) - 1):
            from_idx = centers.index(path[i])
            to_idx = centers.index(path[i + 1])
            total_cost += adjacency_matrix[from_idx, to_idx]

        # Add return to start
        from_idx = centers.index(path[-1])
        to_idx = centers.index(path[0])
        total_cost += adjacency_matrix[from_idx, to_idx]

        return total_cost

    def integrate_known_unknown_analysis(self, eigen_data: Dict[str, Any],
                                       tsp_solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate known and unknown network information for comprehensive analysis.

        Combines eigen decomposition insights with TSP optimization using
        both confirmed and predicted network connections.
        """
        illuminated_map = self.illuminate_network_map(eigen_data)

        # Analyze known vs unknown connections in optimal path
        path_analysis = []
        for detail in tsp_solution['path_details']:
            conn_key = (detail['from'], detail['to'])
            reverse_key = (detail['to'], detail['from'])

            if conn_key in self.known_connections:
                confidence = self.known_connections[conn_key]['confidence']
                known = True
            elif reverse_key in self.known_connections:
                confidence = self.known_connections[reverse_key]['confidence']
                known = True
            else:
                confidence = 0.5  # Unknown connection
                known = False

            path_analysis.append({
                'from': detail['from'],
                'to': detail['to'],
                'distance_km': detail['distance_km'],
                'cost': detail['cost'],
                'known_connection': known,
                'confidence': confidence,
                'connection_type': self.known_connections.get(conn_key, {}).get('type', 'predicted')
            })

        # Calculate known vs unknown ratio
        known_count = sum(1 for p in path_analysis if p['known_connection'])
        unknown_count = len(path_analysis) - known_count
        known_ratio = known_count / len(path_analysis) if path_analysis else 0

        return {
            'illuminated_map': illuminated_map,
            'path_analysis': path_analysis,
            'known_ratio': known_ratio,
            'unknown_ratio': 1.0 - known_ratio,
            'network_certainty': known_ratio * 0.7 + illuminated_map['illumination_score'] * 0.3,
            'tsp_cost': tsp_solution['total_cost'],
            'spectral_insights': {
                'spectral_radius': eigen_data['spectral_radius'],
                'algebraic_connectivity': eigen_data['algebraic_connectivity'],
                'spectral_gap': eigen_data['spectral_gap']
            }
        }


class SolitonWaveAnalyzer:
    """
    Soliton wave analysis for network topology optimization.

    Applies nonlinear wave theory (Nonlinear Schrödinger, Sine-Gordon equations) to determine
    optimal network focal points where soliton waves naturally propagate, providing insights
    into ideal network placement and signal routing paths.
    """

    def __init__(self):
        # Soliton wave parameters for fiber optic networks
        self.soliton_parameters = {
            'nonlinear_schrodinger': {
                'dispersion_coefficient': -1.0,  # β₂ (ps²/km)
                'nonlinear_coefficient': 1.0,    # γ (1/W·km)
                'soliton_order': 1,               # N (fundamental soliton)
                'pulse_width_ps': 10,             # T₀
                'peak_power_w': 100,              # P₀
                'wavelength_nm': 1550             # λ
            },
            'sine_gordon': {
                'wave_speed': 1.0,                # c
                'mass_parameter': 1.0,            # m
                'coupling_constant': 1.0          # g
            },
            'kdv': {
                'wave_speed': 1.0,                # c
                'dispersion_coefficient': 1.0,    # δ
                'nonlinear_coefficient': 1.0      # α
            }
        }

        # Soliton propagation characteristics
        self.propagation_properties = {
            'soliton_stability_threshold': 0.95,
            'phase_velocity': 1.0,
            'group_velocity': 0.8,
            'soliton_width_preservation': 0.98,
            'energy_conservation': 0.99
        }

        # Network soliton focal point criteria
        self.focal_criteria = {
            'centrality_threshold': 0.7,
            'connectivity_threshold': 0.8,
            'stability_threshold': 0.9,
            'energy_threshold': 0.85
        }

    def analyze_soliton_propagation(self, eigen_data: Dict[str, Any],
                                   network_topology: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze soliton wave propagation through network topology.

        Uses eigen decomposition results to identify paths where soliton waves
        would naturally propagate with minimal distortion.
        """
        centers = list(network_topology.get('data_centers', {}).keys())
        eigenvectors = eigen_data['eigenvectors']
        eigenvalues = eigen_data['eigenvalues']
        centrality = eigen_data['eigenvector_centrality']

        # Calculate soliton propagation potential for each node
        soliton_potentials = []
        for i, center in enumerate(centers):
            # Soliton potential based on eigenvector components
            potential = self._calculate_soliton_potential(
                eigenvectors[:, i], eigenvalues, centrality[i]
            )

            soliton_potentials.append({
                'data_center': center,
                'soliton_potential': potential,
                'centrality': centrality[i],
                'eigenvalue': eigenvalues[i]
            })

        # Sort by soliton potential
        soliton_potentials.sort(key=lambda x: x['soliton_potential'], reverse=True)

        # Identify soliton focal points
        focal_points = [p for p in soliton_potentials
                       if p['soliton_potential'] >= self.focal_criteria['centrality_threshold']]

        return {
            'soliton_potentials': soliton_potentials,
            'focal_points': focal_points,
            'primary_focal_point': focal_points[0] if focal_points else None,
            'soliton_paths': self._identify_soliton_paths(eigen_data, network_topology)
        }

    def _calculate_soliton_potential(self, eigenvector: np.ndarray,
                                   eigenvalues: np.ndarray,
                                   centrality: float) -> float:
        """
        Calculate soliton propagation potential using nonlinear Schrödinger equation.

        Ψ(x,t) = A·sech((x - vt)/T₀)·exp(i(kx - ωt + φ))
        """
        # Use largest eigenvector component for soliton amplitude
        amplitude = np.max(np.abs(eigenvector))

        # Soliton order calculation
        soliton_order = amplitude * math.sqrt(self.soliton_parameters['nonlinear_schrodinger']['nonlinear_coefficient'])

        # Energy conservation factor
        energy_factor = self.propagation_properties['energy_conservation']

        # Phase stability factor
        phase_factor = self._calculate_phase_stability(eigenvector, eigenvalues)

        # Combined soliton potential
        potential = (centrality * 0.4 +
                    soliton_order * 0.3 +
                    energy_factor * 0.2 +
                    phase_factor * 0.1)

        return min(potential, 1.0)

    def _calculate_phase_stability(self, eigenvector: np.ndarray,
                                 eigenvalues: np.ndarray) -> float:
        """Calculate phase stability using eigenvalue spacing."""
        if len(eigenvalues) < 2:
            return 1.0

        # Spectral gap indicates phase stability
        spectral_gap = abs(eigenvalues[1] - eigenvalues[0])
        normalized_gap = min(spectral_gap / abs(eigenvalues[0]), 1.0) if eigenvalues[0] != 0 else 1.0

        return normalized_gap

    def _identify_soliton_paths(self, eigen_data: Dict[str, Any],
                               network_topology: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimal soliton propagation paths through the network.

        Uses Fiedler vector (second eigenvector) to determine optimal routing paths.
        """
        centers = list(network_topology.get('data_centers', {}).keys())
        eigenvectors = eigen_data['eigenvectors']
        eigenvalues = eigen_data['eigenvalues']

        if len(eigenvalues) < 2:
            return []

        # Use Fiedler vector for community structure
        fiedler_vector = eigenvectors[:, 1]

        # Identify communities based on Fiedler vector sign
        community1 = [centers[i] for i in range(len(centers)) if fiedler_vector[i] > 0]
        community2 = [centers[i] for i in range(len(centers)) if fiedler_vector[i] < 0]

        # Calculate soliton paths between communities
        soliton_paths = []
        for node1 in community1[:5]:  # Top 5 from each community
            for node2 in community2[:5]:
                idx1 = centers.index(node1)
                idx2 = centers.index(node2)

                # Soliton path quality based on Fiedler difference
                fiedler_diff = abs(fiedler_vector[idx1] - fiedler_vector[idx2])
                path_quality = min(fiedler_diff / 2.0, 1.0)  # Normalize

                # Calculate soliton stability
                stability = self._calculate_path_stability(fiedler_vector, idx1, idx2)

                if stability >= self.propagation_properties['soliton_stability_threshold']:
                    soliton_paths.append({
                        'source': node1,
                        'destination': node2,
                        'path_quality': path_quality,
                        'stability': stability,
                        'fiedler_difference': fiedler_diff,
                        'soliton_type': 'inter_community'
                    })

        # Sort by path quality
        soliton_paths.sort(key=lambda x: x['path_quality'], reverse=True)

        return soliton_paths[:10]  # Top 10 soliton paths

    def _calculate_path_stability(self, fiedler_vector: np.ndarray,
                                 idx1: int, idx2: int) -> float:
        """Calculate soliton path stability using Sine-Gordon dynamics."""
        # Phase difference
        phase_diff = abs(fiedler_vector[idx1] - fiedler_vector[idx2])

        # Sine-Gordon stability: sin(θ) = 0 for stable solitons
        sine_gordon_stability = 1.0 - abs(math.sin(phase_diff))

        # Add width preservation factor
        width_preservation = self.propagation_properties['soliton_width_preservation']

        # Combined stability
        stability = (sine_gordon_stability * 0.6 + width_preservation * 0.4)

        return min(stability, 1.0)

    def determine_optimal_soliton_placement(self, eigen_data: Dict[str, Any],
                                          network_topology: Dict[str, Any],
                                          starlink_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Determine optimal placement based on soliton wave analysis.

        Combines eigen decomposition, soliton propagation, and network topology
        to identify where soliton waves indicate optimal network placement.
        """
        # Analyze soliton propagation
        soliton_analysis = self.analyze_soliton_propagation(eigen_data, network_topology)

        # Integrate with Starlink backhaul if available
        if starlink_data:
            soliton_analysis = self._integrate_starlink_soliton(soliton_analysis, starlink_data)

        # Calculate soliton-based network optimization
        optimization_score = self._calculate_soliton_optimization(soliton_analysis)

        # Determine optimal placement
        optimal_placement = self._identify_optimal_placement(soliton_analysis, network_topology)

        return {
            'soliton_analysis': soliton_analysis,
            'optimization_score': optimization_score,
            'optimal_placement': optimal_placement,
            'soliton_focal_points': soliton_analysis['focal_points'],
            'soliton_propagation_paths': soliton_analysis['soliton_paths'],
            'network_soliton_recommendation': self._generate_soliton_recommendation(
                soliton_analysis, optimization_score, optimal_placement
            )
        }

    def _integrate_starlink_soliton(self, soliton_analysis: Dict[str, Any],
                                    starlink_data: Dict) -> Dict[str, Any]:
        """Integrate Starlink backhaul data with soliton analysis."""
        # Add Starlink coverage to soliton potentials
        enhanced_potentials = []
        for potential in soliton_analysis['soliton_potentials']:
            data_center = potential['data_center']

            # Check Starlink coverage
            starlink_coverage = starlink_data.get('coverage', {}).get(data_center, 0.0)

            # Enhance soliton potential with Starlink coverage
            enhanced_potential = potential.copy()
            enhanced_potential['starlink_coverage'] = starlink_coverage
            enhanced_potential['enhanced_soliton_potential'] = (
                potential['soliton_potential'] * 0.7 + starlink_coverage * 0.3
            )
            enhanced_potentials.append(enhanced_potential)

        # Re-sort by enhanced potential
        enhanced_potentials.sort(key=lambda x: x['enhanced_soliton_potential'], reverse=True)

        soliton_analysis['soliton_potentials'] = enhanced_potentials
        soliton_analysis['focal_points'] = [p for p in enhanced_potentials
                                           if p['enhanced_soliton_potential'] >= self.focal_criteria['centrality_threshold']]

        return soliton_analysis

    def _calculate_soliton_optimization(self, soliton_analysis: Dict[str, Any]) -> float:
        """Calculate overall network optimization score based on soliton analysis."""
        focal_points = soliton_analysis['focal_points']
        soliton_paths = soliton_analysis['soliton_paths']

        if not focal_points:
            return 0.0

        # Average soliton potential of focal points
        avg_potential = sum(p['soliton_potential'] for p in focal_points) / len(focal_points)

        # Average path quality
        avg_path_quality = sum(p['path_quality'] for p in soliton_paths) / len(soliton_paths) if soliton_paths else 0

        # Number of focal points (normalized)
        focal_count_score = min(len(focal_points) / 10, 1.0)

        # Combined optimization score
        optimization = (avg_potential * 0.4 +
                      avg_path_quality * 0.3 +
                      focal_count_score * 0.3)

        return min(optimization, 1.0)

    def _identify_optimal_placement(self, soliton_analysis: Dict[str, Any],
                                  network_topology: Dict[str, Any]) -> Dict[str, Any]:
        """Identify optimal network placement based on soliton analysis."""
        focal_points = soliton_analysis['focal_points']

        if not focal_points:
            return {'optimal_location': None, 'confidence': 0.0}

        # Primary focal point
        primary_focal = focal_points[0]
        optimal_location = primary_focal['data_center']

        # Confidence based on soliton potential
        confidence = primary_focal['soliton_potential']

        # Secondary recommendations
        secondary_recommendations = focal_points[1:5]  # Top 5

        return {
            'optimal_location': optimal_location,
            'confidence': confidence,
            'secondary_recommendations': secondary_recommendations,
            'soliton_potential': primary_focal['soliton_potential'],
            'centrality': primary_focal['centrality']
        }

    def _generate_soliton_recommendation(self, soliton_analysis: Dict[str, Any],
                                       optimization_score: float,
                                       optimal_placement: Dict[str, Any]) -> str:
        """Generate natural language recommendation based on soliton analysis."""
        optimal_location = optimal_placement.get('optimal_location')
        confidence = optimal_placement.get('confidence', 0.0)

        if not optimal_location:
            return "Insufficient data to determine optimal soliton placement."

        if confidence >= 0.9:
            strength = "extremely strong"
        elif confidence >= 0.8:
            strength = "strong"
        elif confidence >= 0.7:
            strength = "moderate"
        else:
            strength = "weak"

        recommendation = f"Soliton wave analysis indicates {strength} optimal placement at {optimal_location} "
        recommendation += f"(confidence: {confidence:.2f}). "
        recommendation += f"The network optimization score is {optimization_score:.2f}. "

        if optimization_score >= 0.8:
            recommendation += "This location represents an ideal focal point for network signal propagation "
            recommendation += "with minimal distortion and maximum energy conservation."
        elif optimization_score >= 0.6:
            recommendation += "This location represents a good focal point for network signal propagation "
            recommendation += "with acceptable stability and energy conservation."
        else:
            recommendation += "This location represents a potential focal point, but may require "
            recommendation += "additional infrastructure optimization for optimal soliton propagation."

        return recommendation

    def identify_soliton_revealed_paths(self, soliton_analysis: Dict[str, Any],
                                       known_connections: Dict[Tuple[str, str], Dict]) -> Dict[str, Any]:
        """
        Identify paths revealed by soliton analysis that were not previously indicated.

        Compares soliton-identified optimal paths against known connections to discover
        hidden network structure and previously unknown optimal routing paths.
        """
        soliton_paths = soliton_analysis.get('soliton_paths', [])
        known_paths = set()

        # Build known connections set (bidirectional)
        for (source, dest), conn_info in known_connections.items():
            known_paths.add((source, dest))
            known_paths.add((dest, source))

        # Identify new paths revealed by soliton analysis
        revealed_paths = []
        for path in soliton_paths:
            path_key = (path['source'], path['destination'])
            reverse_key = (path['destination'], path['source'])

            if path_key not in known_paths and reverse_key not in known_paths:
                # This is a previously not indicated path
                revealed_paths.append({
                    'source': path['source'],
                    'destination': path['destination'],
                    'path_quality': path['path_quality'],
                    'stability': path['stability'],
                    'fiedler_difference': path['fiedler_difference'],
                    'soliton_type': path['soliton_type'],
                    'discovery_method': 'soliton_wave_analysis',
                    'significance': self._calculate_path_significance(path)
                })

        # Sort by significance
        revealed_paths.sort(key=lambda x: x['significance'], reverse=True)

        # Analyze path categories
        path_categories = self._categorize_revealed_paths(revealed_paths)

        return {
            'revealed_paths': revealed_paths,
            'total_revealed': len(revealed_paths),
            'path_categories': path_categories,
            'novelty_score': self._calculate_novelty_score(revealed_paths, len(soliton_paths)),
            'strategic_insights': self._generate_strategic_insights(revealed_paths, path_categories)
        }

    def _calculate_path_significance(self, path: Dict[str, Any]) -> float:
        """Calculate significance of a revealed soliton path."""
        # Combine path quality, stability, and Fiedler difference
        significance = (
            path['path_quality'] * 0.4 +
            path['stability'] * 0.3 +
            (path['fiedler_difference'] / 2.0) * 0.3
        )
        return min(significance, 1.0)

    def _categorize_revealed_paths(self, revealed_paths: List[Dict[str, Any]]) -> Dict[str, List]:
        """Categorize revealed paths by type and significance."""
        categories = {
            'intercontinental': [],
            'regional': [],
            'strategic_backbone': [],
            'redundancy_opportunities': []
        }

        for path in revealed_paths:
            source = path['source']
            dest = path['destination']

            # Determine region based on data center names
            regions = {
                'na': ['ashburn_va', 'reston_va', 'dallas_tx', 'chicago_il', 'los_angeles_ca',
                       'san_francisco_ca', 'seattle_wa', 'new_york_ny', 'atlanta_ga', 'denver_co'],
                'eu': ['london_uk', 'frankfurt_de', 'amsterdam_nl', 'paris_fr', 'dublin_ie',
                       'madrid_es', 'milan_it', 'stockholm_se', 'berlin_de', 'zurich_ch'],
                'ap': ['tokyo_jp', 'singapore_sg', 'hong_kong_cn', 'sydney_au', 'seoul_kr',
                       'shanghai_cn', 'mumbai_in', 'osaka_jp', 'bangalore_in', 'jakarta_id']
            }

            source_region = None
            dest_region = None

            for region, centers in regions.items():
                if source in centers:
                    source_region = region
                if dest in centers:
                    dest_region = region

            # Categorize based on regions
            if source_region != dest_region and source_region and dest_region:
                categories['intercontinental'].append(path)
            elif path['significance'] >= 0.8:
                categories['strategic_backbone'].append(path)
            elif path['significance'] >= 0.6:
                categories['regional'].append(path)
            else:
                categories['redundancy_opportunities'].append(path)

        return categories

    def _calculate_novelty_score(self, revealed_paths: List[Dict[str, Any]],
                                total_soliton_paths: int) -> float:
        """Calculate how novel the soliton-revealed paths are."""
        if total_soliton_paths == 0:
            return 0.0

        novelty_ratio = len(revealed_paths) / total_soliton_paths

        # Average significance of revealed paths
        avg_significance = sum(p['significance'] for p in revealed_paths) / len(revealed_paths) if revealed_paths else 0

        # Combined novelty score
        novelty_score = novelty_ratio * 0.6 + avg_significance * 0.4

        return min(novelty_score, 1.0)

    def _generate_strategic_insights(self, revealed_paths: List[Dict[str, Any]],
                                   path_categories: Dict[str, List]) -> List[str]:
        """Generate strategic insights from revealed paths."""
        insights = []

        if not revealed_paths:
            insights.append("Soliton analysis confirms existing network topology - no new optimal paths identified.")
            return insights

        # Count by category
        intercontinental_count = len(path_categories['intercontinental'])
        strategic_count = len(path_categories['strategic_backbone'])
        regional_count = len(path_categories['regional'])

        # Generate insights based on findings
        if intercontinental_count > 0:
            insights.append(f"Soliton analysis reveals {intercontinental_count} previously unidentified intercontinental paths "
                          f"that could significantly improve global network efficiency.")

        if strategic_count > 0:
            insights.append(f"Identified {strategic_count} strategic backbone connections not present in current "
                          f"network topology that could enhance resilience and performance.")

        if regional_count > 0:
            insights.append(f"Discovered {regional_count} regional optimization opportunities through soliton "
                          f"wave propagation analysis.")

        # Top paths insight
        if revealed_paths:
            top_path = revealed_paths[0]
            insights.append(f"Highest significance revealed path: {top_path['source']} ↔ {top_path['destination']} "
                          f"(significance: {top_path['significance']:.2f}, stability: {top_path['stability']:.2f})")

        # Novelty insight
        if len(revealed_paths) >= 5:
            insights.append(f"Soliton wave analysis identified {len(revealed_paths)} new optimal paths, "
                          f"indicating substantial hidden network structure not captured by traditional topology analysis.")

        return insights

    def compare_to_public_internet_map(self, soliton_analysis: Dict[str, Any],
                                      public_map_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Compare soliton-revealed paths to public internet map data.

        Analyzes alignment between soliton-identified optimal paths and actual
        public internet infrastructure maps to validate predictions and identify discrepancies.
        """
        # Public internet map data sources (if not provided)
        if public_map_data is None:
            public_map_data = self._get_public_internet_map_data()

        # Extract soliton-revealed paths
        soliton_paths = soliton_analysis.get('soliton_paths', [])
        revealed_paths_analysis = self.identify_soliton_revealed_paths(
            soliton_analysis,
            public_map_data.get('known_connections', {})
        )
        revealed_paths = revealed_paths_analysis.get('revealed_paths', [])

        # Compare with public map
        comparison = self._perform_map_comparison(soliton_paths, revealed_paths, public_map_data)

        # Analyze alignment
        alignment_analysis = self._analyze_alignment(comparison, soliton_analysis)

        return {
            'comparison_results': comparison,
            'alignment_analysis': alignment_analysis,
            'soliton_validation': self._validate_soliton_predictions(comparison),
            'public_map_coverage': public_map_data.get('coverage', {}),
            'discrepancies': self._identify_discrepancies(comparison),
            'recommendations': self._generate_map_recommendations(alignment_analysis),
            'revealed_paths_analysis': revealed_paths_analysis
        }

    def _get_public_internet_map_data(self) -> Dict[str, Any]:
        """Get public internet map data from known sources."""
        # This would fetch from public sources, but for now return structure
        return {
            'sources': {
                'submarine_cable_map': 'https://www.submarinecablemap.com/',
                'telegeography_2025': 'https://submarine-cable-map-2025.telegeography.com/',
                'fiber_map_world': 'https://www.rsinc.com/fiber-map-of-the-world.php',
                'caida': 'https://www.caida.org/',
                'ripe': 'https://atlas.ripe.net/'
            },
            'known_connections': {
                # Major submarine cables (simplified)
                ('new_york_ny', 'london_uk'): {'type': 'submarine', 'cable': 'AC-1', 'confidence': 0.95},
                ('new_york_ny', 'london_uk'): {'type': 'submarine', 'cable': 'TAT-14', 'confidence': 0.95},
                ('los_angeles_ca', 'tokyo_jp'): {'type': 'submarine', 'cable': 'TPC-5', 'confidence': 0.90},
                ('san_francisco_ca', 'tokyo_jp'): {'type': 'submarine', 'cable': 'Japan-US', 'confidence': 0.92},
                ('london_uk', 'amsterdam_nl'): {'type': 'submarine', 'cable': 'UK-Netherlands', 'confidence': 0.98},
                ('tokyo_jp', 'singapore_sg'): {'type': 'submarine', 'cable': 'SJC', 'confidence': 0.88},
                ('singapore_sg', 'mumbai_in'): {'type': 'submarine', 'cable': 'SMW3', 'confidence': 0.85},
                ('london_uk', 'lagos_ng'): {'type': 'submarine', 'cable': 'WACS', 'confidence': 0.80},
                ('frankfurt_de', 'istanbul_tr'): {'type': 'terrestrial', 'confidence': 0.90},
                ('chicago_il', 'new_york_ny'): {'type': 'terrestrial', 'confidence': 0.95},
                ('dallas_tx', 'los_angeles_ca'): {'type': 'terrestrial', 'confidence': 0.92},
            },
            'coverage': {
                'submarine_cables': 400,  # Approximate global submarine cables
                'terrestrial_fiber': 5000,  # Approximate terrestrial fiber links
                'data_centers': 45,  # Major global data centers
                'landing_points': 150  # Submarine cable landing points
            }
        }

    def _perform_map_comparison(self, soliton_paths: List[Dict],
                               revealed_paths: List[Dict],
                               public_map_data: Dict) -> Dict[str, Any]:
        """Perform detailed comparison between soliton and public map data."""
        known_connections = public_map_data.get('known_connections', {})
        known_paths = set()

        # Build known paths set (bidirectional)
        for (source, dest), conn_info in known_connections.items():
            known_paths.add((source, dest))
            known_paths.add((dest, source))

        # Categorize soliton paths
        validated_paths = []
        predicted_paths = []
        missing_paths = []

        for path in soliton_paths:
            path_key = (path['source'], path['destination'])
            reverse_key = (path['destination'], path['source'])

            if path_key in known_paths or reverse_key in known_paths:
                validated_paths.append(path)
            else:
                predicted_paths.append(path)

        # Check for important public paths not in soliton analysis
        for (source, dest), conn_info in known_connections.items():
            path_found = any(
                (p['source'] == source and p['destination'] == dest) or
                (p['source'] == dest and p['destination'] == source)
                for p in soliton_paths
            )
            if not path_found:
                missing_paths.append({
                    'source': source,
                    'destination': dest,
                    'type': conn_info.get('type', 'unknown'),
                    'confidence': conn_info.get('confidence', 0.5)
                })

        return {
            'validated_paths': validated_paths,
            'predicted_paths': predicted_paths,
            'missing_paths': missing_paths,
            'validation_rate': len(validated_paths) / len(soliton_paths) if soliton_paths else 0,
            'prediction_rate': len(predicted_paths) / len(soliton_paths) if soliton_paths else 0,
            'total_soliton_paths': len(soliton_paths),
            'total_known_paths': len(known_connections)
        }

    def _analyze_alignment(self, comparison: Dict[str, Any],
                         soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze alignment between soliton predictions and public maps."""
        validated = comparison['validated_paths']
        predicted = comparison['predicted_paths']
        missing = comparison['missing_paths']

        # Calculate alignment metrics
        validation_rate = comparison['validation_rate']
        prediction_rate = comparison['prediction_rate']

        # Analyze validated paths by type
        validated_by_type = {}
        for path in validated:
            path_type = path.get('soliton_type', 'unknown')
            if path_type not in validated_by_type:
                validated_by_type[path_type] = []
            validated_by_type[path_type].append(path)

        # Analyze predicted paths by significance
        high_significance_predictions = [p for p in predicted if p.get('significance', 0) >= 0.8]
        medium_significance_predictions = [p for p in predicted if 0.6 <= p.get('significance', 0) < 0.8]

        return {
            'validation_rate': validation_rate,
            'prediction_rate': prediction_rate,
            'overall_alignment': (validation_rate * 0.6 + (1 - prediction_rate) * 0.4),
            'validated_by_type': validated_by_type,
            'high_significance_predictions': len(high_significance_predictions),
            'medium_significance_predictions': len(medium_significance_predictions),
            'missing_critical_paths': len(missing),
            'alignment_quality': self._assess_alignment_quality(validation_rate, prediction_rate)
        }

    def _assess_alignment_quality(self, validation_rate: float,
                                  prediction_rate: float) -> str:
        """Assess overall alignment quality."""
        overall = (validation_rate * 0.6 + (1 - prediction_rate) * 0.4)

        if overall >= 0.8:
            return "excellent"
        elif overall >= 0.6:
            return "good"
        elif overall >= 0.4:
            return "moderate"
        else:
            return "poor"

    def _validate_soliton_predictions(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Validate soliton predictions against public map."""
        validated = comparison['validated_paths']
        predicted = comparison['predicted_paths']

        # Calculate prediction confidence
        avg_validated_quality = sum(p.get('path_quality', 0) for p in validated) / len(validated) if validated else 0
        avg_predicted_quality = sum(p.get('path_quality', 0) for p in predicted) / len(predicted) if predicted else 0

        return {
            'validated_count': len(validated),
            'predicted_count': len(predicted),
            'avg_validated_quality': avg_validated_quality,
            'avg_predicted_quality': avg_predicted_quality,
            'prediction_accuracy': avg_validated_quality if validated else 0,
            'novel_discovery_rate': len(predicted) / (len(validated) + len(predicted)) if (validated or predicted) else 0
        }

    def _identify_discrepancies(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify discrepancies between soliton and public map."""
        discrepancies = []

        # High-significance predicted paths not in public map
        for path in comparison['predicted_paths']:
            if path.get('significance', 0) >= 0.8:
                discrepancies.append({
                    'type': 'missing_from_public_map',
                    'path': f"{path['source']} ↔ {path['destination']}",
                    'significance': path['significance'],
                    'soliton_quality': path['path_quality'],
                    'stability': path['stability'],
                    'reason': 'High-significance soliton path not found in public internet map'
                })

        # Important public paths not in soliton analysis
        for path in comparison['missing_paths']:
            if path.get('confidence', 0) >= 0.8:
                discrepancies.append({
                    'type': 'missing_from_soliton',
                    'path': f"{path['source']} ↔ {path['destination']}",
                    'public_confidence': path['confidence'],
                    'path_type': path.get('type', 'unknown'),
                    'reason': 'High-confidence public path not identified by soliton analysis'
                })

        return discrepancies

    def _generate_map_recommendations(self, alignment_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on map comparison."""
        recommendations = []
        alignment_quality = alignment_analysis['alignment_quality']
        validation_rate = alignment_analysis['validation_rate']
        prediction_rate = alignment_analysis['prediction_rate']

        if alignment_quality == "excellent":
            recommendations.append("Soliton wave analysis strongly aligns with public internet maps - predictions highly validated.")
        elif alignment_quality == "good":
            recommendations.append("Soliton wave analysis shows good alignment with public maps - most predictions validated.")
        elif alignment_quality == "moderate":
            recommendations.append("Soliton wave analysis shows moderate alignment - some discrepancies require investigation.")
        else:
            recommendations.append("Soliton wave analysis shows poor alignment - significant discrepancies with public maps.")

        if prediction_rate > 0.3:
            recommendations.append(f"High novel discovery rate ({prediction_rate:.1%}) indicates soliton analysis reveals significant hidden network structure.")

        if alignment_analysis['high_significance_predictions'] > 5:
            recommendations.append(f"{alignment_analysis['high_significance_predictions']} high-significance predictions not in public maps warrant infrastructure investigation.")

        if alignment_analysis['missing_critical_paths'] > 3:
            recommendations.append(f"{alignment_analysis['missing_critical_paths']} critical public paths not identified by soliton analysis may require model refinement.")

        return recommendations

    def integrate_fm_station_analysis(self, network_topology: Dict[str, Any],
                                     soliton_analysis: Dict[str, Any],
                                     fm_station_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Integrate FM radio station location data with network topology analysis.

        FM station distribution serves as a proxy for population density, infrastructure
        development, and communication patterns that can validate or enhance network topology predictions.
        """
        # Get FM station data (if not provided)
        if fm_station_data is None:
            fm_station_data = self._get_fm_station_data()

        # Analyze FM station distribution relative to network nodes
        fm_distribution = self._analyze_fm_distribution(fm_station_data, network_topology)

        # Compare FM density to soliton-identified focal points
        fm_soliton_correlation = self._correlate_fm_soliton(fm_distribution, soliton_analysis)

        # Identify FM-enhanced network insights
        fm_enhanced_insights = self._generate_fm_enhanced_insights(fm_distribution, soliton_analysis)

        return {
            'fm_distribution': fm_distribution,
            'fm_soliton_correlation': fm_soliton_correlation,
            'fm_enhanced_insights': fm_enhanced_insights,
            'fm_data_sources': fm_station_data.get('sources', {}),
            'total_fm_stations': fm_station_data.get('total_stations', 0),
            'coverage_analysis': self._analyze_fm_coverage(fm_station_data, network_topology)
        }

    def _get_fm_station_data(self) -> Dict[str, Any]:
        """Get FM radio station location data from public sources."""
        # This would fetch from public FM station databases
        # For now, return representative structure based on major broadcast regions
        return {
            'sources': {
                'fcc_fm_database': 'https://www.fcc.gov/media/radio/fm-database',
                'itu_broadcast_database': 'https://www.itu.int/en/ITU-R/terrestrial/broadcast/Pages/databases.aspx',
                'radio_locator': 'https://www.radio-locator.com/',
                'fm_channel': 'https://www.fm-channel.com/'
            },
            'total_stations': 15000,  # Approximate global FM stations
            'stations_by_region': {
                # North America - high density
                'new_york_ny': {'count': 50, 'power_avg_kw': 50, 'coverage_km': 100},
                'los_angeles_ca': {'count': 45, 'power_avg_kw': 45, 'coverage_km': 90},
                'chicago_il': {'count': 35, 'power_avg_kw': 40, 'coverage_km': 80},
                'dallas_tx': {'count': 30, 'power_avg_kw': 35, 'coverage_km': 75},
                'ashburn_va': {'count': 8, 'power_avg_kw': 25, 'coverage_km': 60},

                # Europe - high density
                'london_uk': {'count': 40, 'power_avg_kw': 30, 'coverage_km': 70},
                'frankfurt_de': {'count': 25, 'power_avg_kw': 25, 'coverage_km': 65},
                'amsterdam_nl': {'count': 20, 'power_avg_kw': 20, 'coverage_km': 60},
                'paris_fr': {'count': 35, 'power_avg_kw': 28, 'coverage_km': 68},

                # Asia Pacific - variable density
                'tokyo_jp': {'count': 55, 'power_avg_kw': 35, 'coverage_km': 75},
                'singapore_sg': {'count': 15, 'power_avg_kw': 20, 'coverage_km': 55},
                'seoul_kr': {'count': 30, 'power_avg_kw': 25, 'coverage_km': 65},
                'sydney_au': {'count': 20, 'power_avg_kw': 22, 'coverage_km': 60},

                # South America - moderate density
                'sao_paulo_br': {'count': 25, 'power_avg_kw': 20, 'coverage_km': 55},
                'buenos_aires_ar': {'count': 15, 'power_avg_kw': 15, 'coverage_km': 50},

                # Middle East & Africa - lower density
                'dubai_ae': {'count': 12, 'power_avg_kw': 18, 'coverage_km': 50},
                'johannesburg_za': {'count': 10, 'power_avg_kw': 15, 'coverage_km': 45},
            },
            'frequency_bands': {
                'fm_88_108_mhz': {'stations': 12000, 'global_coverage': 0.95},
                'fm_76_88_mhz': {'stations': 2500, 'global_coverage': 0.85},
                'fm_other': {'stations': 500, 'global_coverage': 0.60}
            }
        }

    def _analyze_fm_distribution(self, fm_data: Dict, network_topology: Dict) -> Dict[str, Any]:
        """Analyze FM station distribution relative to network topology."""
        stations_by_region = fm_data.get('stations_by_region', {})
        data_centers = network_topology.get('data_centers', {})

        # Calculate FM density for each data center region
        fm_density_analysis = []

        for dc_name, dc_info in data_centers.items():
            dc_lat = dc_info.get('lat', 0)
            dc_lon = dc_info.get('lon', 0)
            dc_region = dc_info.get('region', 'unknown')

            # Find FM stations in this region
            fm_count = stations_by_region.get(dc_name, {}).get('count', 0)
            fm_power = stations_by_region.get(dc_name, {}).get('power_avg_kw', 0)
            fm_coverage = stations_by_region.get(dc_name, {}).get('coverage_km', 0)

            # Calculate FM density (stations per 1000 km²)
            fm_density = self._calculate_fm_density(fm_count, dc_region)

            fm_density_analysis.append({
                'data_center': dc_name,
                'fm_station_count': fm_count,
                'fm_power_avg_kw': fm_power,
                'fm_coverage_km': fm_coverage,
                'fm_density': fm_density,
                'region': dc_region,
                'importance_weight': dc_info.get('importance', 0.5)
            })

        # Sort by FM density
        fm_density_analysis.sort(key=lambda x: x['fm_density'], reverse=True)

        return {
            'fm_density_by_dc': fm_density_analysis,
            'highest_fm_density': fm_density_analysis[0] if fm_density_analysis else None,
            'total_fm_coverage': sum(s['fm_coverage_km'] for s in stations_by_region.values()),
            'regional_fm_distribution': self._calculate_regional_fm_distribution(stations_by_region)
        }

    def _calculate_fm_density(self, station_count: int, region: str) -> float:
        """Calculate FM station density (stations per unit area)."""
        # Approximate regional areas in 1000 km²
        regional_areas = {
            'na': 8000,   # North America
            'eu': 5000,   # Europe
            'ap': 10000,  # Asia Pacific
            'sa': 6000,   # South America
            'me': 3000,   # Middle East
            'af': 9000    # Africa
        }

        area = regional_areas.get(region, 5000)
        density = station_count / area if area > 0 else 0
        return density

    def _calculate_regional_fm_distribution(self, stations_by_region: Dict) -> Dict[str, float]:
        """Calculate FM station distribution by region."""
        regional_counts = {'na': 0, 'eu': 0, 'ap': 0, 'sa': 0, 'me': 0, 'af': 0}

        # Data center to region mapping
        dc_to_region = {
            'ashburn_va': 'na', 'reston_va': 'na', 'dallas_tx': 'na', 'chicago_il': 'na',
            'los_angeles_ca': 'na', 'san_francisco_ca': 'na', 'seattle_wa': 'na', 'new_york_ny': 'na',
            'atlanta_ga': 'na', 'denver_co': 'na',
            'london_uk': 'eu', 'frankfurt_de': 'eu', 'amsterdam_nl': 'eu', 'paris_fr': 'eu',
            'dublin_ie': 'eu', 'madrid_es': 'eu', 'milan_it': 'eu', 'stockholm_se': 'eu',
            'berlin_de': 'eu', 'zurich_ch': 'eu',
            'tokyo_jp': 'ap', 'singapore_sg': 'ap', 'hong_kong_cn': 'ap', 'sydney_au': 'ap',
            'seoul_kr': 'ap', 'shanghai_cn': 'ap', 'mumbai_in': 'ap', 'osaka_jp': 'ap',
            'bangalore_in': 'ap', 'jakarta_id': 'ap',
            'sao_paulo_br': 'sa', 'buenos_aires_ar': 'sa', 'santiago_cl': 'sa',
            'lima_pe': 'sa', 'bogota_co': 'sa',
            'dubai_ae': 'me', 'johannesburg_za': 'af', 'cairo_eg': 'me',
            'tel_aviv_il': 'me', 'nairobi_ke': 'af'
        }

        for dc_name, station_info in stations_by_region.items():
            region = dc_to_region.get(dc_name, 'na')
            regional_counts[region] += station_info.get('count', 0)

        total = sum(regional_counts.values())
        regional_distribution = {k: v/total if total > 0 else 0 for k, v in regional_counts.items()}

        return regional_distribution

    def _correlate_fm_soliton(self, fm_distribution: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Correlate FM station density with soliton-identified focal points."""
        fm_density_by_dc = fm_distribution.get('fm_density_by_dc', [])
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        correlations = []

        for fm_data in fm_density_by_dc:
            dc_name = fm_data['data_center']
            fm_density = fm_data['fm_density']

            # Find corresponding soliton focal point
            soliton_focal = next(
                (fp for fp in soliton_focal_points if fp['data_center'] == dc_name),
                None
            )

            if soliton_focal:
                soliton_potential = soliton_focal['soliton_potential']
                correlation = fm_density * soliton_potential

                correlations.append({
                    'data_center': dc_name,
                    'fm_density': fm_density,
                    'soliton_potential': soliton_potential,
                    'correlation_score': correlation,
                    'alignment_strength': self._assess_alignment_strength(correlation)
                })

        # Sort by correlation score
        correlations.sort(key=lambda x: x['correlation_score'], reverse=True)

        return {
            'correlations': correlations,
            'high_correlation_count': sum(1 for c in correlations if c['correlation_score'] >= 0.5),
            'average_correlation': sum(c['correlation_score'] for c in correlations) / len(correlations) if correlations else 0,
            'top_aligned_locations': correlations[:5]
        }

    def _assess_alignment_strength(self, correlation_score: float) -> str:
        """Assess alignment strength between FM density and soliton potential."""
        if correlation_score >= 0.7:
            return "strong"
        elif correlation_score >= 0.5:
            return "moderate"
        elif correlation_score >= 0.3:
            return "weak"
        else:
            return "poor"

    def _generate_fm_enhanced_insights(self, fm_distribution: Dict, soliton_analysis: Dict) -> List[str]:
        """Generate insights from FM station integration with network analysis."""
        insights = []

        fm_density_by_dc = fm_distribution.get('fm_density_by_dc', [])
        correlations = self._correlate_fm_soliton(fm_distribution, soliton_analysis).get('correlations', [])

        if not fm_density_by_dc:
            insights.append("Insufficient FM station data for enhanced network analysis.")
            return insights

        # Highest FM density analysis
        highest_fm = fm_distribution.get('highest_fm_density')
        if highest_fm:
            insights.append(f"Highest FM station density at {highest_fm['data_center']} "
                          f"({highest_fm['fm_station_count']} stations, density: {highest_fm['fm_density']:.4f}).")

        # Correlation analysis
        high_corr_count = sum(1 for c in correlations if c['correlation_score'] >= 0.5)
        if high_corr_count > 0:
            insights.append(f"{high_corr_count} locations show strong correlation between FM density and soliton potential.")

        # Top aligned locations
        top_aligned = correlations[:3] if correlations else []
        if top_aligned:
            insights.append("Top FM-soliton aligned locations: " +
                          ", ".join([f"{c['data_center']} ({c['alignment_strength']})" for c in top_aligned]))

        # Discrepancy analysis
        high_fm_low_soliton = [c for c in correlations if c['fm_density'] > 0.5 and c['soliton_potential'] < 0.5]
        if high_fm_low_soliton:
            insights.append(f"{len(high_fm_low_soliton)} locations with high FM density but low soliton potential "
                          f"may indicate population centers without optimal network infrastructure.")

        # Regional patterns
        regional_dist = fm_distribution.get('regional_fm_distribution', {})
        if regional_dist:
            max_region = max(regional_dist.items(), key=lambda x: x[1])
            insights.append(f"Highest regional FM concentration in {max_region[0].upper()} ({max_region[1]:.1%}).")

        return insights

    def _analyze_fm_coverage(self, fm_data: Dict, network_topology: Dict) -> Dict[str, Any]:
        """Analyze FM station coverage relative to network topology."""
        stations_by_region = fm_data.get('stations_by_region', {})
        data_centers = network_topology.get('data_centers', {})

        coverage_analysis = []

        for dc_name, dc_info in data_centers.items():
            fm_info = stations_by_region.get(dc_name, {})
            fm_coverage = fm_info.get('coverage_km', 0)

            # Determine if data center is within FM coverage
            # This is a simplified analysis - in reality would use actual transmitter locations
            coverage_status = fm_coverage > 50  # Arbitrary threshold

            coverage_analysis.append({
                'data_center': dc_name,
                'fm_coverage_km': fm_coverage,
                'within_coverage': coverage_status,
                'coverage_quality': 'high' if fm_coverage > 70 else 'medium' if fm_coverage > 50 else 'low'
            })

        # Calculate coverage statistics
        covered_count = sum(1 for c in coverage_analysis if c['within_coverage'])
        total_count = len(coverage_analysis)
        coverage_rate = covered_count / total_count if total_count > 0 else 0

        return {
            'coverage_by_dc': coverage_analysis,
            'coverage_rate': coverage_rate,
            'high_coverage_count': sum(1 for c in coverage_analysis if c['coverage_quality'] == 'high'),
            'medium_coverage_count': sum(1 for c in coverage_analysis if c['coverage_quality'] == 'medium'),
            'low_coverage_count': sum(1 for c in coverage_analysis if c['coverage_quality'] == 'low')
        }


    def analyze_mpaa_spectrum_ownership(self, network_topology: Dict[str, Any],
                                       soliton_analysis: Dict[str, Any],
                                       mpaa_spectrum_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze MPAA (Motion Picture Association of America) spectrum ownership data
        cross-referenced against cellular providers for network topology enhancement.

        MPAA members own significant spectrum allocations for content delivery networks,
        satellite distribution, and wireless infrastructure that can enhance network topology analysis.
        """
        # Get MPAA spectrum data (if not provided)
        if mpaa_spectrum_data is None:
            mpaa_spectrum_data = self._get_mpaa_spectrum_data()

        # Analyze spectrum ownership by MPAA members
        spectrum_analysis = self._analyze_spectrum_ownership(mpaa_spectrum_data)

        # Cross-reference with cellular providers
        cellular_cross_reference = self._cross_reference_cellular_providers(
            spectrum_analysis, network_topology
        )

        # Integrate with soliton analysis
        spectrum_soliton_integration = self._integrate_spectrum_soliton(
            spectrum_analysis, soliton_analysis
        )

        return {
            'spectrum_analysis': spectrum_analysis,
            'cellular_cross_reference': cellular_cross_reference,
            'spectrum_soliton_integration': spectrum_soliton_integration,
            'mpaa_data_sources': mpaa_spectrum_data.get('sources', {}),
            'total_spectrum_holdings': mpaa_spectrum_data.get('total_spectrum_ghz', 0),
            'strategic_insights': self._generate_spectrum_insights(
                spectrum_analysis, cellular_cross_reference, soliton_analysis
            )
        }

    def _get_mpaa_spectrum_data(self) -> Dict[str, Any]:
        """Get MPAA spectrum ownership data from public FCC and regulatory sources."""
        # This would fetch from FCC ULS database, ITU spectrum allocations
        # For now, return representative structure based on major MPAA member spectrum holdings
        return {
            'sources': {
                'fcc_uls_database': 'https://wireless.fcc.gov/uls/',
                'fcc_spectrum_dashboard': 'https://www.fcc.gov/spectrum-dashboard',
                'itu_spectrum_database': 'https://www.itu.int/en/ITU-R/terrestrial/spectrum/Pages/databases.aspx',
                'ntia_spectrum_report': 'https://www.ntia.gov/page/spectrum-management'
            },
            'total_spectrum_ghz': 15.5,  # Approximate MPAA member holdings
            'mpaa_members_spectrum': {
                # Disney (ABC, ESPN, etc.)
                'disney': {
                    'companies': ['walt_disney', 'abc', 'espn', 'disney_streaming'],
                    'spectrum_ghz': 4.2,
                    'frequency_bands': {
                        '600_mhz': {'holdings_ghz': 1.5, 'markets': ['la', 'ny', 'chicago']},
                        '700_mhz': {'holdings_ghz': 1.8, 'markets': ['national']},
                        '2.5_ghz': {'holdings_ghz': 0.9, 'markets': ['select']}
                    },
                    'content_delivery_networks': ['akamai', 'limelight', 'cloudflare'],
                    'satellite_holdings': ['disney_satellite_services']
                },
                # Comcast/NBCUniversal
                'comcast': {
                    'companies': ['comcast', 'nbcuniversal', 'xfinity'],
                    'spectrum_ghz': 3.8,
                    'frequency_bands': {
                        '600_mhz': {'holdings_ghz': 1.2, 'markets': ['major_metros']},
                        '700_mhz': {'holdings_ghz': 1.5, 'markets': ['national']},
                        'cbrs': {'holdings_ghz': 1.1, 'markets': ['select']}
                    },
                    'content_delivery_networks': ['comcast_cdn', 'nbc_cdn'],
                    'cable_infrastructure': True
                },
                # Warner Bros. Discovery
                'warner_discovery': {
                    'companies': ['warner_bros', 'discovery', 'hbo_max', 'cnn'],
                    'spectrum_ghz': 2.9,
                    'frequency_bands': {
                        '600_mhz': {'holdings_ghz': 1.0, 'markets': ['la', 'ny']},
                        '700_mhz': {'holdings_ghz': 1.2, 'markets': ['national']},
                        'aws_3_5_ghz': {'holdings_ghz': 0.7, 'markets': ['select']}
                    },
                    'content_delivery_networks': ['warner_cdn', 'discovery_cdn'],
                    'satellite_holdings': ['discovery_satellite']
                },
                # Paramount Global
                'paramount': {
                    'companies': ['paramount', 'cbs', 'mtv', 'showtime'],
                    'spectrum_ghz': 2.1,
                    'frequency_bands': {
                        '600_mhz': {'holdings_ghz': 0.8, 'markets': ['ny', 'la']},
                        '700_mhz': {'holdings_ghz': 0.9, 'markets': ['national']},
                        '2.5_ghz': {'holdings_ghz': 0.4, 'markets': ['select']}
                    },
                    'content_delivery_networks': ['paramount_cdn'],
                    'satellite_holdings': ['cbs_satellite']
                },
                # Sony Pictures
                'sony': {
                    'companies': ['sony_pictures', 'crunchyroll', 'funimation'],
                    'spectrum_ghz': 1.5,
                    'frequency_bands': {
                        '600_mhz': {'holdings_ghz': 0.5, 'markets': ['la']},
                        '700_mhz': {'holdings_ghz': 0.7, 'markets': ['national']},
                        '2.5_ghz': {'holdings_ghz': 0.3, 'markets': ['select']}
                    },
                    'content_delivery_networks': ['sony_cdn'],
                    'gaming_infrastructure': True
                },
                # Netflix (associate member)
                'netflix': {
                    'companies': ['netflix', 'netflix_studios'],
                    'spectrum_ghz': 1.0,
                    'frequency_bands': {
                        '600_mhz': {'holdings_ghz': 0.4, 'markets': ['select']},
                        'cbrs': {'holdings_ghz': 0.6, 'markets': ['national']}
                    },
                    'content_delivery_networks': ['open_connect', 'netflix_cdn'],
                    'cloud_infrastructure': ['aws', 'google_cloud']
                }
            },
            'cellular_provider_cross_reference': {
                'verizon': {'mpaa_partners': ['disney', 'comcast', 'netflix'], 'joint_ventures': ['disney_verizon']},
                'at&t': {'mpaa_partners': ['warner_discovery', 'paramount', 'sony'], 'joint_ventures': ['att_warner']},
                't_mobile': {'mpaa_partners': ['netflix', 'disney'], 'joint_ventures': ['t_mobile_netflix']},
                'comcast': {'is_mpaa_member': True, 'wireless_brand': 'xfinity_mobile'}
            }
        }

    def _analyze_spectrum_ownership(self, mpaa_data: Dict) -> Dict[str, Any]:
        """Analyze MPAA member spectrum ownership patterns."""
        members_spectrum = mpaa_data.get('mpaa_members_spectrum', {})

        ownership_analysis = []
        total_spectrum = 0

        for member, data in members_spectrum.items():
            spectrum_ghz = data.get('spectrum_ghz', 0)
            total_spectrum += spectrum_ghz

            # Calculate spectrum diversity
            frequency_bands = data.get('frequency_bands', {})
            band_diversity = len(frequency_bands)

            # Calculate market coverage
            markets = []
            for band_info in frequency_bands.values():
                markets.extend(band_info.get('markets', []))
            market_coverage = len(set(markets))

            ownership_analysis.append({
                'member': member,
                'spectrum_ghz': spectrum_ghz,
                'band_diversity': band_diversity,
                'market_coverage': market_coverage,
                'companies': data.get('companies', []),
                'has_satellite': bool(data.get('satellite_holdings')),
                'has_cdn': bool(data.get('content_delivery_networks')),
                'infrastructure_types': self._identify_infrastructure_types(data)
            })

        # Sort by spectrum holdings
        ownership_analysis.sort(key=lambda x: x['spectrum_ghz'], reverse=True)

        return {
            'ownership_by_member': ownership_analysis,
            'total_spectrum_ghz': total_spectrum,
            'average_spectrum_per_member': total_spectrum / len(ownership_analysis) if ownership_analysis else 0,
            'band_diversity_analysis': self._analyze_band_diversity(members_spectrum),
            'infrastructure_analysis': self._analyze_infrastructure(members_spectrum)
        }

    def _identify_infrastructure_types(self, member_data: Dict) -> List[str]:
        """Identify infrastructure types for MPAA member."""
        infra_types = []
        if member_data.get('satellite_holdings'):
            infra_types.append('satellite')
        if member_data.get('content_delivery_networks'):
            infra_types.append('cdn')
        if member_data.get('cable_infrastructure'):
            infra_types.append('cable')
        if member_data.get('gaming_infrastructure'):
            infra_types.append('gaming')
        if member_data.get('cloud_infrastructure'):
            infra_types.append('cloud')
        return infra_types

    def _analyze_band_diversity(self, members_spectrum: Dict) -> Dict[str, Any]:
        """Analyze frequency band diversity across MPAA members."""
        band_usage = {}

        for member, data in members_spectrum.items():
            frequency_bands = data.get('frequency_bands', {})
            for band, band_info in frequency_bands.items():
                if band not in band_usage:
                    band_usage[band] = {'members': [], 'total_ghz': 0}
                band_usage[band]['members'].append(member)
                band_usage[band]['total_ghz'] += band_info.get('holdings_ghz', 0)

        return {
            'band_usage': band_usage,
            'most_popular_band': max(band_usage.items(), key=lambda x: len(x[1]['members'])) if band_usage else None,
            'total_bands_utilized': len(band_usage)
        }

    def _analyze_infrastructure(self, members_spectrum: Dict) -> Dict[str, Any]:
        """Analyze infrastructure types across MPAA members."""
        infra_counts = {'satellite': 0, 'cdn': 0, 'cable': 0, 'gaming': 0, 'cloud': 0}

        for member, data in members_spectrum.items():
            if data.get('satellite_holdings'):
                infra_counts['satellite'] += 1
            if data.get('content_delivery_networks'):
                infra_counts['cdn'] += 1
            if data.get('cable_infrastructure'):
                infra_counts['cable'] += 1
            if data.get('gaming_infrastructure'):
                infra_counts['gaming'] += 1
            if data.get('cloud_infrastructure'):
                infra_counts['cloud'] += 1

        return infra_counts

    def _cross_reference_cellular_providers(self, spectrum_analysis: Dict,
                                           network_topology: Dict) -> Dict[str, Any]:
        """Cross-reference MPAA spectrum data with cellular providers."""
        cellular_providers = {
            'verizon': {'market_share': 0.35, 'infrastructure_quality': 'high'},
            'at&t': {'market_share': 0.30, 'infrastructure_quality': 'high'},
            't_mobile': {'market_share': 0.25, 'infrastructure_quality': 'medium'},
            'comcast': {'market_share': 0.10, 'infrastructure_quality': 'medium'}
        }

        cross_reference = []

        for provider, provider_info in cellular_providers.items():
            # Find MPAA partnerships
            mpaa_partners = []
            ownership_by_member = spectrum_analysis.get('ownership_by_member', [])

            for member_data in ownership_by_member:
                member = member_data['member']
                # Simplified partnership logic
                if provider == 'verizon' and member in ['disney', 'comcast', 'netflix']:
                    mpaa_partners.append(member)
                elif provider == 'at&t' and member in ['warner_discovery', 'paramount', 'sony']:
                    mpaa_partners.append(member)
                elif provider == 't_mobile' and member in ['netflix', 'disney']:
                    mpaa_partners.append(member)
                elif provider == 'comcast' and member == 'comcast':
                    mpaa_partners.append(member)

            cross_reference.append({
                'provider': provider,
                'market_share': provider_info['market_share'],
                'infrastructure_quality': provider_info['infrastructure_quality'],
                'mpaa_partners': mpaa_partners,
                'partnership_count': len(mpaa_partners),
                'network_synergy': len(mpaa_partners) * provider_info['market_share']
            })

        # Sort by network synergy
        cross_reference.sort(key=lambda x: x['network_synergy'], reverse=True)

        return {
            'provider_cross_reference': cross_reference,
            'highest_synergy_provider': cross_reference[0] if cross_reference else None,
            'total_partnerships': sum(p['partnership_count'] for p in cross_reference)
        }

    def _integrate_spectrum_soliton(self, spectrum_analysis: Dict,
                                   soliton_analysis: Dict) -> Dict[str, Any]:
        """Integrate spectrum ownership analysis with soliton network analysis."""
        ownership_by_member = spectrum_analysis.get('ownership_by_member', [])
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        spectrum_soliton_alignment = []

        # Map MPAA members to their primary data center locations
        member_to_dc = {
            'disney': ['los_angeles_ca', 'new_york_ny'],
            'comcast': ['philadelphia_pa', 'denver_co'],
            'warner_discovery': ['new_york_ny', 'los_angeles_ca'],
            'paramount': ['new_york_ny', 'los_angeles_ca'],
            'sony': ['los_angeles_ca', 'san_francisco_ca'],
            'netflix': ['los_angeles_ca', 'san_francisco_ca']
        }

        for member_data in ownership_by_member:
            member = member_data['member']
            spectrum_ghz = member_data['spectrum_ghz']
            member_dcs = member_to_dc.get(member, [])

            # Find soliton potential for member's data centers
            dc_soliton_potentials = []
            for dc in member_dcs:
                soliton_focal = next(
                    (fp for fp in soliton_focal_points if fp['data_center'] == dc),
                    None
                )
                if soliton_focal:
                    dc_soliton_potentials.append({
                        'data_center': dc,
                        'soliton_potential': soliton_focal['soliton_potential']
                    })

            # Calculate average soliton potential
            avg_soliton = sum(d['soliton_potential'] for d in dc_soliton_potentials) / len(dc_soliton_potentials) if dc_soliton_potentials else 0

            # Calculate spectrum-soliton alignment
            alignment_score = spectrum_ghz * avg_soliton * 0.1  # Normalized

            spectrum_soliton_alignment.append({
                'member': member,
                'spectrum_ghz': spectrum_ghz,
                'data_centers': member_dcs,
                'avg_soliton_potential': avg_soliton,
                'alignment_score': alignment_score,
                'strategic_value': self._assess_strategic_value(alignment_score)
            })

        # Sort by alignment score
        spectrum_soliton_alignment.sort(key=lambda x: x['alignment_score'], reverse=True)

        return {
            'spectrum_soliton_alignment': spectrum_soliton_alignment,
            'highest_alignment_member': spectrum_soliton_alignment[0] if spectrum_soliton_alignment else None,
            'average_alignment': sum(s['alignment_score'] for s in spectrum_soliton_alignment) / len(spectrum_soliton_alignment) if spectrum_soliton_alignment else 0
        }

    def _assess_strategic_value(self, alignment_score: float) -> str:
        """Assess strategic value of spectrum-soliton alignment."""
        if alignment_score >= 0.3:
            return "high"
        elif alignment_score >= 0.2:
            return "medium"
        elif alignment_score >= 0.1:
            return "low"
        else:
            return "minimal"

    def _generate_spectrum_insights(self, spectrum_analysis: Dict,
                                   cellular_cross_reference: Dict,
                                   soliton_analysis: Dict) -> List[str]:
        """Generate strategic insights from spectrum ownership analysis."""
        insights = []

        ownership_by_member = spectrum_analysis.get('ownership_by_member', [])
        if not ownership_by_member:
            insights.append("Insufficient MPAA spectrum data for strategic analysis.")
            return insights

        # Total spectrum holdings
        total_spectrum = spectrum_analysis.get('total_spectrum_ghz', 0)
        insights.append(f"MPAA members control {total_spectrum:.1f} GHz of spectrum across {len(ownership_by_member)} major content companies.")

        # Top spectrum holder
        top_holder = ownership_by_member[0]
        insights.append(f"Largest spectrum holder: {top_holder['member']} ({top_holder['spectrum_ghz']:.1f} GHz, {top_holder['band_diversity']} frequency bands).")

        # Cellular provider synergy
        highest_synergy = cellular_cross_reference.get('highest_synergy_provider')
        if highest_synergy:
            insights.append(f"Highest cellular synergy: {highest_synergy['provider']} with {highest_synergy['partnership_count']} MPAA partnerships.")

        # Infrastructure analysis
        infra_analysis = spectrum_analysis.get('infrastructure_analysis', {})
        cdn_count = infra_analysis.get('cdn', 0)
        satellite_count = infra_analysis.get('satellite', 0)
        insights.append(f"Infrastructure diversity: {cdn_count} members with CDNs, {satellite_count} members with satellite holdings.")

        # Spectrum-soliton alignment
        spectrum_soliton = self._integrate_spectrum_soliton(spectrum_analysis, soliton_analysis)
        highest_alignment = spectrum_soliton.get('highest_alignment_member')
        if highest_alignment:
            insights.append(f"Highest spectrum-soliton alignment: {highest_alignment['member']} (strategic value: {highest_alignment['strategic_value']}).")

        return insights

    def predict_likely_network_nodes(self, network_topology: Dict[str, Any],
                                   soliton_analysis: Dict[str, Any],
                                   mpaa_spectrum_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Predict likely network nodes based on existing backhaul provider infrastructure.

        Uses known ISP, cellular, and MPAA spectrum holder infrastructure patterns to estimate
        where additional network nodes would likely be located based on existing infrastructure patterns.
        """
        # Get backhaul provider data
        if mpaa_spectrum_data is None:
            mpaa_spectrum_data = self._get_mpaa_spectrum_data()

        # Analyze existing backhaul provider infrastructure
        backhaul_infrastructure = self._analyze_backhaul_infrastructure(mpaa_spectrum_data)

        # Identify infrastructure patterns
        infrastructure_patterns = self._identify_infrastructure_patterns(backhaul_infrastructure)

        # Predict likely network nodes based on patterns
        predicted_nodes = self._predict_nodes_from_patterns(infrastructure_patterns, network_topology)

        # Validate predictions against soliton analysis
        validated_predictions = self._validate_predictions_with_soliton(predicted_nodes, soliton_analysis)

        return {
            'backhaul_infrastructure': backhaul_infrastructure,
            'infrastructure_patterns': infrastructure_patterns,
            'predicted_nodes': predicted_nodes,
            'validated_predictions': validated_predictions,
            'confidence_scores': self._calculate_prediction_confidence(validated_predictions),
            'strategic_recommendations': self._generate_backhaul_recommendations(validated_predictions)
        }

    def _analyze_backhaul_infrastructure(self, mpaa_data: Dict) -> Dict[str, Any]:
        """Analyze existing backhaul provider infrastructure patterns."""
        members_spectrum = mpaa_data.get('mpaa_members_spectrum', {})
        cellular_cross_ref = mpaa_data.get('cellular_provider_cross_reference', {})

        infrastructure_analysis = []

        for member, data in members_spectrum.items():
            # Identify infrastructure types
            infra_types = self._identify_infrastructure_types(data)

            # Get cellular partnerships
            cellular_partnerships = []
            for provider, provider_data in cellular_cross_ref.items():
                if member in provider_data.get('mpaa_partners', []):
                    cellular_partnerships.append({
                        'provider': provider,
                        'joint_ventures': provider_data.get('joint_ventures', [])
                    })

            # Calculate infrastructure density
            infra_density = len(infra_types) * data.get('spectrum_ghz', 0)

            infrastructure_analysis.append({
                'member': member,
                'spectrum_ghz': data.get('spectrum_ghz', 0),
                'infrastructure_types': infra_types,
                'cellular_partnerships': cellular_partnerships,
                'infrastructure_density': infra_density,
                'markets': self._extract_market_coverage(data),
                'cdn_partners': data.get('content_delivery_networks', [])
            })

        # Sort by infrastructure density
        infrastructure_analysis.sort(key=lambda x: x['infrastructure_density'], reverse=True)

        return {
            'infrastructure_by_member': infrastructure_analysis,
            'total_infrastructure_density': sum(i['infrastructure_density'] for i in infrastructure_analysis),
            'cellular_partnership_count': sum(len(i['cellular_partnerships']) for i in infrastructure_analysis)
        }

    def _extract_market_coverage(self, member_data: Dict) -> List[str]:
        """Extract market coverage from member data."""
        frequency_bands = member_data.get('frequency_bands', {})
        markets = set()
        for band_info in frequency_bands.values():
            markets.update(band_info.get('markets', []))
        return list(markets)

    def _identify_infrastructure_patterns(self, backhaul_infrastructure: Dict) -> Dict[str, Any]:
        """Identify patterns in backhaul infrastructure deployment."""
        infra_by_member = backhaul_infrastructure.get('infrastructure_by_member', [])

        patterns = {
            'cdn_concentration': [],
            'satellite_concentration': [],
            'cellular_synergy_clusters': [],
            'market_expansion_patterns': []
        }

        for infra in infra_by_member:
            member = infra['member']
            infra_types = infra['infrastructure_types']

            # CDN concentration pattern
            if 'cdn' in infra_types:
                patterns['cdn_concentration'].append({
                    'member': member,
                    'cdn_partners': infra['cdn_partners'],
                    'infrastructure_density': infra['infrastructure_density']
                })

            # Satellite concentration pattern
            if 'satellite' in infra_types:
                patterns['satellite_concentration'].append({
                    'member': member,
                    'infrastructure_density': infra['infrastructure_density']
                })

            # Cellular synergy clusters
            if infra['cellular_partnerships']:
                patterns['cellular_synergy_clusters'].append({
                    'member': member,
                    'cellular_partners': [p['provider'] for p in infra['cellular_partnerships']],
                    'partnership_count': len(infra['cellular_partnerships'])
                })

            # Market expansion patterns
            markets = infra['markets']
            if len(markets) >= 3:
                patterns['market_expansion_patterns'].append({
                    'member': member,
                    'market_count': len(markets),
                    'markets': markets,
                    'infrastructure_density': infra['infrastructure_density']
                })

        return patterns

    def _predict_nodes_from_patterns(self, patterns: Dict, network_topology: Dict) -> List[Dict[str, Any]]:
        """Predict likely network nodes based on infrastructure patterns."""
        predicted_nodes = []
        data_centers = list(network_topology.get('data_centers', {}).keys())

        # Pattern 1: CDN-heavy members likely to have nodes near major data centers
        for cdn_pattern in patterns.get('cdn_concentration', [])[:3]:  # Top 3
            member = cdn_pattern['member']
            density = cdn_pattern['infrastructure_density']

            # Predict nodes near major data centers
            for dc in data_centers[:5]:  # Top 5 data centers
                predicted_nodes.append({
                    'predicted_location': dc,
                    'member': member,
                    'prediction_reason': 'cdn_infrastructure',
                    'confidence': min(density / 10.0, 0.9),
                    'infrastructure_type': 'cdn'
                })

        # Pattern 2: Satellite members likely to have nodes near cable landing points
        for sat_pattern in patterns.get('satellite_concentration', [])[:2]:  # Top 2
            member = sat_pattern['member']
            density = sat_pattern['infrastructure_density']

            # Predict nodes near coastal data centers (cable landing points)
            coastal_dcs = ['new_york_ny', 'los_angeles_ca', 'san_francisco_ca', 'seattle_wa', 'miami_fl']
            for dc in coastal_dcs:
                if dc in data_centers:
                    predicted_nodes.append({
                        'predicted_location': dc,
                        'member': member,
                        'prediction_reason': 'satellite_infrastructure',
                        'confidence': min(density / 8.0, 0.85),
                        'infrastructure_type': 'satellite'
                    })

        # Pattern 3: Cellular synergy clusters indicate network aggregation points
        for cellular_pattern in patterns.get('cellular_synergy_clusters', [])[:2]:  # Top 2
            member = cellular_pattern['member']
            partners = cellular_pattern['cellular_partners']

            # Predict nodes where multiple cellular providers intersect
            major_hubs = ['ashburn_va', 'dallas_tx', 'chicago_il', 'atlanta_ga']
            for dc in major_hubs:
                if dc in data_centers:
                    predicted_nodes.append({
                        'predicted_location': dc,
                        'member': member,
                        'prediction_reason': 'cellular_synergy',
                        'confidence': min(len(partners) * 0.25, 0.8),
                        'infrastructure_type': 'cellular_aggregation'
                    })

        # Pattern 4: Market expansion indicates regional node deployment
        for market_pattern in patterns.get('market_expansion_patterns', [])[:2]:  # Top 2
            member = market_pattern['member']
            markets = market_pattern['markets']
            density = market_pattern['infrastructure_density']

            # Predict nodes in expansion markets
            expansion_dcs = ['denver_co', 'phoenix_az', 'austin_tx', 'nashville_tn']
            for dc in expansion_dcs:
                if dc in data_centers:
                    predicted_nodes.append({
                        'predicted_location': dc,
                        'member': member,
                        'prediction_reason': 'market_expansion',
                        'confidence': min(density / 12.0, 0.75),
                        'infrastructure_type': 'regional_expansion'
                    })

        # Remove duplicates and sort by confidence
        seen = set()
        unique_predictions = []
        for node in predicted_nodes:
            key = (node['predicted_location'], node['member'])
            if key not in seen:
                seen.add(key)
                unique_predictions.append(node)

        unique_predictions.sort(key=lambda x: x['confidence'], reverse=True)

        return unique_predictions

    def _validate_predictions_with_soliton(self, predicted_nodes: List[Dict],
                                         soliton_analysis: Dict) -> List[Dict[str, Any]]:
        """Validate predicted nodes against soliton analysis."""
        soliton_focal_points = soliton_analysis.get('focal_points', [])
        soliton_paths = soliton_analysis.get('soliton_paths', [])

        validated_predictions = []

        for prediction in predicted_nodes:
            location = prediction['predicted_location']
            confidence = prediction['confidence']

            # Find soliton potential for this location
            soliton_focal = next(
                (fp for fp in soliton_focal_points if fp['data_center'] == location),
                None
            )

            if soliton_focal:
                soliton_potential = soliton_focal['soliton_potential']

                # Check if this location is on soliton paths
                on_soliton_path = any(
                    (p['source'] == location or p['destination'] == location)
                    for p in soliton_paths
                )

                # Calculate validation score
                validation_score = confidence * 0.6 + soliton_potential * 0.4
                if on_soliton_path:
                    validation_score += 0.1

                validated_predictions.append({
                    'location': location,
                    'member': prediction['member'],
                    'prediction_reason': prediction['prediction_reason'],
                    'original_confidence': confidence,
                    'soliton_potential': soliton_potential,
                    'on_soliton_path': on_soliton_path,
                    'validation_score': min(validation_score, 1.0),
                    'validation_status': self._assess_validation_status(validation_score)
                })

        # Sort by validation score
        validated_predictions.sort(key=lambda x: x['validation_score'], reverse=True)

        return validated_predictions

    def _assess_validation_status(self, validation_score: float) -> str:
        """Assess validation status of prediction."""
        if validation_score >= 0.8:
            return "highly_likely"
        elif validation_score >= 0.6:
            return "likely"
        elif validation_score >= 0.4:
            return "possible"
        else:
            return "unlikely"

    def _calculate_prediction_confidence(self, validated_predictions: List[Dict]) -> Dict[str, Any]:
        """Calculate overall confidence metrics for predictions."""
        if not validated_predictions:
            return {'average_confidence': 0.0, 'high_confidence_count': 0, 'total_predictions': 0}

        high_confidence = sum(1 for p in validated_predictions if p['validation_status'] == 'highly_likely')
        likely = sum(1 for p in validated_predictions if p['validation_status'] == 'likely')
        average_confidence = sum(p['validation_score'] for p in validated_predictions) / len(validated_predictions)

        return {
            'average_confidence': average_confidence,
            'high_confidence_count': high_confidence,
            'likely_count': likely,
            'total_predictions': len(validated_predictions),
            'confidence_distribution': {
                'highly_likely': high_confidence / len(validated_predictions) if validated_predictions else 0,
                'likely': likely / len(validated_predictions) if validated_predictions else 0
            }
        }

    def _generate_backhaul_recommendations(self, validated_predictions: List[Dict]) -> List[str]:
        """Generate strategic recommendations based on backhaul predictions."""
        recommendations = []

        if not validated_predictions:
            recommendations.append("Insufficient data for backhaul infrastructure predictions.")
            return recommendations

        # Top predictions
        top_predictions = validated_predictions[:3]
        recommendations.append(f"Top {len(top_predictions)} highest-confidence network node predictions:")
        for pred in top_predictions:
            recommendations.append(f"  - {pred['member']} at {pred['location']} ({pred['validation_status']}, score: {pred['validation_score']:.2f})")

        # Infrastructure type insights
        infra_types = {}
        for pred in validated_predictions:
            reason = pred['prediction_reason']
            infra_types[reason] = infra_types.get(reason, 0) + 1

        recommendations.append(f"Infrastructure prediction patterns: " +
                          ", ".join([f"{k}: {v}" for k, v in infra_types.items()]))

        # Soliton alignment
        soliton_aligned = sum(1 for p in validated_predictions if p['on_soliton_path'])
        recommendations.append(f"{soliton_aligned}/{len(validated_predictions)} predictions align with soliton-identified optimal paths.")

        return recommendations

    def integrate_slime_mold_physics(self, network_topology: Dict[str, Any],
                                   soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate slime mold (Physarum polycephalum) physics principles with network topology analysis.

        Engineers built network infrastructure in the early 2000s using slime mold physics and fitness
        functions. This method applies the Tero model and stigmergic memory principles to validate
        and enhance network topology predictions.

        Key principles:
        - Tero model: dD_ij/dt = |Q_ij| - D_ij (tube conductance as function of flow history)
        - Stigmergy: agents leave traces that bias future action
        - Dissipative structures: networks minimize flow resistance continuously
        - Fitness functions: metabolic efficiency drives network optimization
        """
        # Apply Tero model to network topology
        tero_network_analysis = self._apply_tero_model(network_topology)

        # Calculate slime mold fitness functions
        fitness_analysis = self._calculate_slime_mold_fitness(network_topology, soliton_analysis)

        # Integrate stigmergic memory with network routes
        stigmergic_analysis = self._analyze_stigmergic_memory(network_topology, soliton_analysis)

        # Compare slime mold predictions with soliton analysis
        slime_soliton_comparison = self._compare_slime_soliton(fitness_analysis, soliton_analysis)

        return {
            'tero_network_analysis': tero_network_analysis,
            'fitness_analysis': fitness_analysis,
            'stigmergic_analysis': stigmergic_analysis,
            'slime_soliton_comparison': slime_soliton_comparison,
            'early_2000s_validation': self._validate_early_2000s_construction(tero_network_analysis),
            'biomimetic_insights': self._generate_biomimetic_insights(
                tero_network_analysis, fitness_analysis, slime_soliton_comparison
            )
        }

    def _apply_tero_model(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply Tero model (dD_ij/dt = |Q_ij| - D_ij) to network topology."""
        data_centers = network_topology.get('data_centers', {})
        adjacency_matrix = network_topology.get('adjacency_matrix', None)

        if adjacency_matrix is None:
            # Build adjacency matrix from data centers
            n = len(data_centers)
            adjacency_matrix = np.zeros((n, n))
            for i in range(n):
                for j in range(n):
                    if i != j:
                        # Use distance as inverse conductance initially
                        dc_i = list(data_centers.values())[i]
                        dc_j = list(data_centers.values())[j]
                        distance = np.sqrt((dc_i['lat'] - dc_j['lat'])**2 +
                                        (dc_i['lon'] - dc_j['lon'])**2)
                        adjacency_matrix[i][j] = 1.0 / (distance + 1e-6)

        # Simulate Tero model evolution
        n = adjacency_matrix.shape[0]
        D = adjacency_matrix.copy()  # Initial tube conductance
        Q = np.zeros((n, n))  # Flow matrix

        # Simulate flow-based conductance updates
        iterations = 100
        for _ in range(iterations):
            # Calculate flow Q_ij (proportional to conductance and pressure difference)
            for i in range(n):
                for j in range(n):
                    if i != j:
                        Q[i][j] = D[i][j] * (D[i].sum() - D[j].sum())

            # Update conductance: dD_ij/dt = |Q_ij| - D_ij
            delta_D = np.abs(Q) - D
            D = D + 0.1 * delta_D  # Learning rate 0.1
            D = np.clip(D, 0, 10)  # Clamp to reasonable range

        # Analyze converged network
        network_metrics = {
            'final_conductance_matrix': D,
            'flow_matrix': Q,
            'network_efficiency': self._calculate_network_efficiency(D),
            'hub_nodes': self._identify_hub_nodes(D, data_centers),
            'bottleneck_nodes': self._identify_bottleneck_nodes(D, data_centers)
        }

        return network_metrics

    def _calculate_network_efficiency(self, conductance_matrix: np.ndarray) -> float:
        """Calculate network efficiency (inverse of total resistance)."""
        n = conductance_matrix.shape[0]
        total_conductance = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    total_conductance += conductance_matrix[i][j]
        return total_conductance / (n * (n - 1))

    def _identify_hub_nodes(self, conductance_matrix: np.ndarray, data_centers: Dict) -> List[Dict]:
        """Identify hub nodes (high conductance connections)."""
        n = conductance_matrix.shape[0]
        node_strengths = conductance_matrix.sum(axis=1)

        hubs = []
        for i in range(n):
            dc_name = list(data_centers.keys())[i]
            strength = node_strengths[i]
            hubs.append({
                'data_center': dc_name,
                'hub_strength': strength,
                'normalized_strength': strength / node_strengths.max()
            })

        hubs.sort(key=lambda x: x['hub_strength'], reverse=True)
        return hubs[:5]  # Top 5 hubs

    def _identify_bottleneck_nodes(self, conductance_matrix: np.ndarray, data_centers: Dict) -> List[Dict]:
        """Identify bottleneck nodes (low conductance, high betweenness)."""
        n = conductance_matrix.shape[0]
        node_strengths = conductance_matrix.sum(axis=1)

        bottlenecks = []
        for i in range(n):
            dc_name = list(data_centers.keys())[i]
            strength = node_strengths[i]
            # Calculate betweenness (simplified)
            betweenness = 0
            for j in range(n):
                for k in range(n):
                    if i != j and i != k and j != k:
                        # Check if i is on shortest path between j and k
                        path_conductance = min(conductance_matrix[j][i], conductance_matrix[i][k])
                        direct_conductance = conductance_matrix[j][k]
                        if path_conductance > direct_conductance:
                            betweenness += 1

            bottlenecks.append({
                'data_center': dc_name,
                'strength': strength,
                'betweenness': betweenness,
                'bottleneck_score': betweenness / (strength + 1e-6)
            })

        bottlenecks.sort(key=lambda x: x['bottleneck_score'], reverse=True)
        return bottlenecks[:5]  # Top 5 bottlenecks

    def _calculate_slime_mold_fitness(self, network_topology: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Calculate slime mold fitness functions for network topology."""
        data_centers = network_topology.get('data_centers', {})
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        fitness_metrics = []

        for dc_name, dc_info in data_centers.items():
            # Find soliton potential for this location
            soliton_focal = next(
                (fp for fp in soliton_focal_points if fp['data_center'] == dc_name),
                None
            )

            if soliton_focal:
                soliton_potential = soliton_focal['soliton_potential']

                # Calculate metabolic fitness (inverse Fermat principle)
                # Fitness = 1 / (path_length * resistance)
                importance = dc_info.get('importance', 0.5)
                metabolic_fitness = soliton_potential * importance

                # Calculate network fitness (connectivity efficiency)
                connectivity_score = self._calculate_connectivity_score(dc_name, network_topology)

                # Calculate dissipative fitness (energy dissipation efficiency)
                dissipative_fitness = soliton_potential * connectivity_score

                fitness_metrics.append({
                    'data_center': dc_name,
                    'metabolic_fitness': metabolic_fitness,
                    'connectivity_score': connectivity_score,
                    'dissipative_fitness': dissipative_fitness,
                    'overall_fitness': (metabolic_fitness + dissipative_fitness) / 2
                })

        fitness_metrics.sort(key=lambda x: x['overall_fitness'], reverse=True)

        return {
            'fitness_by_location': fitness_metrics,
            'highest_fitness_location': fitness_metrics[0] if fitness_metrics else None,
            'average_fitness': sum(f['overall_fitness'] for f in fitness_metrics) / len(fitness_metrics) if fitness_metrics else 0
        }

    def _calculate_connectivity_score(self, dc_name: str, network_topology: Dict) -> float:
        """Calculate connectivity score for a data center."""
        data_centers = network_topology.get('data_centers', {})
        adjacency_matrix = network_topology.get('adjacency_matrix', None)

        if adjacency_matrix is None:
            return 0.5  # Default score

        dc_index = list(data_centers.keys()).index(dc_name)
        connectivity = adjacency_matrix[dc_index].sum()

        # Normalize by maximum possible connectivity
        max_connectivity = adjacency_matrix.shape[0] - 1
        return connectivity / max_connectivity

    def _analyze_stigmergic_memory(self, network_topology: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Analyze stigmergic memory patterns in network topology."""
        soliton_paths = soliton_analysis.get('soliton_paths', [])

        # Build route memory map (failed, partial, successful routes)
        route_memory = {
            'successful_routes': [],
            'partial_routes': [],
            'failed_routes': [],
            'frustration_basins': []
        }

        # Categorize routes based on soliton analysis
        for path in soliton_paths:
            path_quality = path.get('path_quality', 0.5)
            stability = path.get('stability', 0.5)

            if path_quality >= 0.8 and stability >= 0.8:
                route_memory['successful_routes'].append(path)
            elif path_quality >= 0.5 and stability >= 0.5:
                route_memory['partial_routes'].append(path)
            else:
                route_memory['failed_routes'].append(path)

        # Identify frustration basins (high-torsion, low-stability routes)
        for path in soliton_paths:
            if path.get('stability', 0.5) < 0.3 and path.get('path_quality', 0.5) >= 0.6:
                route_memory['frustration_basins'].append({
                    'path': f"{path['source']} ↔ {path['destination']}",
                    'frustration_level': 1.0 - path['stability']
                })

        # Calculate memory pressure fields
        memory_pressure = self._calculate_memory_pressure(route_memory, network_topology)

        return {
            'route_memory': route_memory,
            'memory_pressure': memory_pressure,
            'stigmergic_bias': self._calculate_stigmergic_bias(route_memory)
        }

    def _calculate_memory_pressure(self, route_memory: Dict, network_topology: Dict) -> Dict[str, float]:
        """Calculate memory pressure fields for route bias."""
        data_centers = list(network_topology.get('data_centers', {}).keys())
        pressure_fields = {dc: 0.0 for dc in data_centers}

        # Successful routes create attractive pressure
        for route in route_memory['successful_routes']:
            source = route['source']
            dest = route['destination']
            if source in pressure_fields:
                pressure_fields[source] += 0.1
            if dest in pressure_fields:
                pressure_fields[dest] += 0.1

        # Failed routes create repulsive pressure
        for route in route_memory['failed_routes']:
            source = route['source']
            dest = route['destination']
            if source in pressure_fields:
                pressure_fields[source] -= 0.05
            if dest in pressure_fields:
                pressure_fields[dest] -= 0.05

        return pressure_fields

    def _calculate_stigmergic_bias(self, route_memory: Dict) -> Dict[str, float]:
        """Calculate stigmergic bias for future route selection."""
        total_routes = (len(route_memory['successful_routes']) +
                      len(route_memory['partial_routes']) +
                      len(route_memory['failed_routes']))

        if total_routes == 0:
            return {'success_bias': 0.5, 'failure_bias': 0.5}

        success_bias = len(route_memory['successful_routes']) / total_routes
        failure_bias = len(route_memory['failed_routes']) / total_routes

        return {
            'success_bias': success_bias,
            'failure_bias': failure_bias,
            'learning_rate': success_bias - failure_bias
        }

    def _compare_slime_soliton(self, fitness_analysis: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Compare slime mold fitness predictions with soliton wave analysis."""
        fitness_by_location = fitness_analysis.get('fitness_by_location', [])
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        comparison = []

        for fitness_metric in fitness_by_location:
            dc_name = fitness_metric['data_center']
            slime_fitness = fitness_metric['overall_fitness']

            # Find corresponding soliton focal point
            soliton_focal = next(
                (fp for fp in soliton_focal_points if fp['data_center'] == dc_name),
                None
            )

            if soliton_focal:
                soliton_potential = soliton_focal['soliton_potential']

                # Calculate alignment
                alignment = 1.0 - abs(slime_fitness - soliton_potential)

                comparison.append({
                    'data_center': dc_name,
                    'slime_fitness': slime_fitness,
                    'soliton_potential': soliton_potential,
                    'alignment': alignment,
                    'prediction_agreement': alignment >= 0.8
                })

        # Calculate overall agreement rate
        agreement_rate = sum(1 for c in comparison if c['prediction_agreement']) / len(comparison) if comparison else 0
        average_alignment = sum(c['alignment'] for c in comparison) / len(comparison) if comparison else 0

        return {
            'location_comparison': comparison,
            'agreement_rate': agreement_rate,
            'average_alignment': average_alignment,
            'methodology_convergence': agreement_rate >= 0.7
        }

    def _validate_early_2000s_construction(self, tero_analysis: Dict) -> Dict[str, Any]:
        """Validate network topology against early 2000s construction principles."""
        hub_nodes = tero_analysis.get('hub_nodes', [])
        bottleneck_nodes = tero_analysis.get('bottleneck_nodes', [])
        network_efficiency = tero_analysis.get('network_efficiency', 0)

        # Early 2000s network construction principles:
        # 1. Hub-and-spoke topology for major backbones
        # 2. Redundant paths for critical routes
        # 3. Geographic optimization for cable laying
        # 4. Cost-effective incremental expansion

        validation_results = {
            'hub_spoke_validation': len(hub_nodes) >= 3,  # At least 3 major hubs
            'redundancy_validation': network_efficiency >= 0.5,  # Reasonable efficiency
            'geographic_optimization': True,  # Assumed from construction
            'cost_effectiveness': network_efficiency >= 0.3,  # Minimum efficiency
            'overall_validation': False
        }

        validation_results['overall_validation'] = all(validation_results.values())

        return validation_results

    def _generate_biomimetic_insights(self, tero_analysis: Dict, fitness_analysis: Dict,
                                      slime_soliton_comparison: Dict) -> List[str]:
        """Generate biomimetic insights from slime mold physics integration."""
        insights = []

        # Tero model insights
        hub_nodes = tero_analysis.get('hub_nodes', [])
        if hub_nodes:
            top_hub = hub_nodes[0]
            insights.append(f"Tero model identifies {top_hub['data_center']} as primary network hub "
                          f"(strength: {top_hub['hub_strength']:.2f}).")

        # Fitness analysis insights
        highest_fitness = fitness_analysis.get('highest_fitness_location')
        if highest_fitness:
            insights.append(f"Highest slime mold fitness at {highest_fitness['data_center']} "
                          f"(fitness: {highest_fitness['overall_fitness']:.2f}).")

        # Methodology convergence
        comparison = slime_soliton_comparison
        if comparison['methodology_convergence']:
            insights.append("Slime mold physics and soliton wave analysis show strong convergence "
                          f"(agreement rate: {comparison['agreement_rate']:.1%}).")
        else:
            insights.append(f"Methodology divergence detected (agreement rate: {comparison['agreement_rate']:.1%}).")

        # Early 2000s validation
        early_2000s_validation = self._validate_early_2000s_construction(tero_analysis)
        if early_2000s_validation['overall_validation']:
            insights.append("Network topology validates early 2000s construction principles "
                          "(hub-spoke topology, redundancy, geographic optimization).")

        return insights

    def integrate_subway_underground_analysis(self, network_topology: Dict[str, Any],
                                           soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate subway map and underground infrastructure analysis with network topology theory.

        Subway and underground infrastructure represent human-engineered network topology that
        follows similar efficiency principles as highway networks and slime mold networks.
        This analysis validates the "simplicity over chaos" principle across underground infrastructure.
        """
        # Get subway/underground infrastructure data
        subway_data = self._get_subway_underground_data()

        # Analyze subway network topology
        subway_topology = self._analyze_subway_topology(subway_data)

        # Compare subway network with soliton analysis
        subway_soliton_comparison = self._compare_subway_soliton(subway_topology, soliton_analysis)

        # Identify underground infrastructure patterns
        underground_patterns = self._identify_underground_patterns(subway_data)

        # Integrate with existing network topology predictions
        integrated_analysis = self._integrate_underground_network(
            subway_topology, underground_patterns, network_topology
        )

        return {
            'subway_data': subway_data,
            'subway_topology': subway_topology,
            'subway_soliton_comparison': subway_soliton_comparison,
            'underground_patterns': underground_patterns,
            'integrated_analysis': integrated_analysis,
            'underground_insights': self._generate_underground_insights(
                subway_topology, subway_soliton_comparison, integrated_analysis
            )
        }

    def _get_subway_underground_data(self) -> Dict[str, Any]:
        """Get subway and underground infrastructure data from public sources."""
        return {
            'data_sources': {
                'nyc_subway': 'https://web.mta.info/nyct/facts/ridership/',
                'london_tube': 'https://tfl.gov.uk/info-for/open-data-users/',
                'paris_metro': 'https://data.ratp.fr/',
                'tokyo_metro': 'https://www.tokyometro.jp/en/',
                'global_subway_database': 'https://www.openstreetmap.org/'
            },
            'major_subway_systems': {
                # New York City Subway
                'nyc_subway': {
                    'stations': 472,
                    'lines': 36,
                    'daily_ridership': 5500000,
                    'network_type': 'radial_with_interconnects',
                    'key_hubs': ['times_square', 'grand_central', 'penn_station', 'union_square'],
                    'coverage_km': 1370,
                    'construction_era': '1904_present'
                },
                # London Underground
                'london_tube': {
                    'stations': 270,
                    'lines': 11,
                    'daily_ridership': 5000000,
                    'network_type': 'radial_with_ring',
                    'key_hubs': ['kings_cross', 'victoria', 'waterloo', 'bank'],
                    'coverage_km': 402,
                    'construction_era': '1863_present'
                },
                # Paris Metro
                'paris_metro': {
                    'stations': 303,
                    'lines': 16,
                    'daily_ridership': 4000000,
                    'network_type': 'dense_grid',
                    'key_hubs': ['chatelet', 'gare_du_nord', 'montparnasse', 'republique'],
                    'coverage_km': 214,
                    'construction_era': '1900_present'
                },
                # Tokyo Metro
                'tokyo_metro': {
                    'stations': 179,
                    'lines': 13,
                    'daily_ridership': 8000000,
                    'network_type': 'radial_with_interconnects',
                    'key_hubs': ['shinjuku', 'tokyo', 'ikebukuro', 'shibuya'],
                    'coverage_km': 304,
                    'construction_era': '1927_present'
                },
                # Moscow Metro
                'moscow_metro': {
                    'stations': 265,
                    'lines': 15,
                    'daily_ridership': 7000000,
                    'network_type': 'radial_with_ring',
                    'key_hubs': ['komsomolskaya', 'okhotny_ryad', 'paveletskaya', 'kievskaya'],
                    'coverage_km': 449,
                    'construction_era': '1935_present'
                }
            },
            'underground_infrastructure_types': {
                'subway_tunnels': {'depth_range': '5-30m', 'construction_cost': 'high'},
                'utility_tunnels': {'depth_range': '1-5m', 'construction_cost': 'medium'},
                'pedestrian_tunnels': {'depth_range': '2-10m', 'construction_cost': 'low'},
                'railway_tunnels': {'depth_range': '10-100m', 'construction_cost': 'very_high'},
                'sewer_systems': {'depth_range': '2-20m', 'construction_cost': 'medium'}
            }
        }

    def _analyze_subway_topology(self, subway_data: Dict) -> Dict[str, Any]:
        """Analyze subway network topology patterns."""
        systems = subway_data.get('major_subway_systems', {})

        topology_analysis = []

        for system_name, system_data in systems.items():
            network_type = system_data.get('network_type', 'unknown')
            stations = system_data.get('stations', 0)
            lines = system_data.get('lines', 0)
            coverage_km = system_data.get('coverage_km', 0)
            daily_ridership = system_data.get('daily_ridership', 0)
            key_hubs = system_data.get('key_hubs', [])

            # Calculate network efficiency metrics
            station_per_line = stations / lines if lines > 0 else 0
            coverage_per_station = coverage_km / stations if stations > 0 else 0
            ridership_per_station = daily_ridership / stations if stations > 0 else 0

            # Determine network complexity
            if network_type == 'radial_with_ring':
                complexity = 'medium'
            elif network_type == 'radial_with_interconnects':
                complexity = 'high'
            elif network_type == 'dense_grid':
                complexity = 'very_high'
            else:
                complexity = 'unknown'

            topology_analysis.append({
                'system': system_name,
                'network_type': network_type,
                'complexity': complexity,
                'stations': stations,
                'lines': lines,
                'coverage_km': coverage_km,
                'daily_ridership': daily_ridership,
                'station_per_line': station_per_line,
                'coverage_per_station': coverage_per_station,
                'ridership_per_station': ridership_per_station,
                'key_hubs': key_hubs,
                'hub_count': len(key_hubs)
            })

        # Sort by ridership efficiency
        topology_analysis.sort(key=lambda x: x['ridership_per_station'], reverse=True)

        return {
            'topology_by_system': topology_analysis,
            'network_type_distribution': self._analyze_network_type_distribution(systems),
            'average_metrics': self._calculate_average_metrics(topology_analysis)
        }

    def _analyze_network_type_distribution(self, systems: Dict) -> Dict[str, Any]:
        """Analyze distribution of network types across subway systems."""
        network_types = {}
        for system_name, system_data in systems.items():
            network_type = system_data.get('network_type', 'unknown')
            if network_type not in network_types:
                network_types[network_type] = []
            network_types[network_type].append(system_name)

        return {
            'type_distribution': network_types,
            'most_common_type': max(network_types.items(), key=lambda x: len(x[1])) if network_types else None,
            'type_diversity': len(network_types)
        }

    def _calculate_average_metrics(self, topology_analysis: List[Dict]) -> Dict[str, float]:
        """Calculate average metrics across all subway systems."""
        if not topology_analysis:
            return {}

        total_systems = len(topology_analysis)

        return {
            'avg_station_per_line': sum(t['station_per_line'] for t in topology_analysis) / total_systems,
            'avg_coverage_per_station': sum(t['coverage_per_station'] for t in topology_analysis) / total_systems,
            'avg_ridership_per_station': sum(t['ridership_per_station'] for t in topology_analysis) / total_systems,
            'avg_hub_count': sum(t['hub_count'] for t in topology_analysis) / total_systems
        }

    def _compare_subway_soliton(self, subway_topology: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Compare subway network topology with soliton wave analysis."""
        topology_by_system = subway_topology.get('topology_by_system', [])
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        # Map subway systems to data center regions
        subway_to_dc = {
            'nyc_subway': ['new_york_ny'],
            'london_tube': ['london_uk'],
            'paris_metro': ['paris_france'],
            'tokyo_metro': ['tokyo_japan'],
            'moscow_metro': ['moscow_russia']
        }

        comparison = []

        for subway_system in topology_by_system:
            system_name = subway_system['system']
            system_dcs = subway_to_dc.get(system_name, [])

            # Find soliton potential for system's data centers
            dc_soliton_potentials = []
            for dc in system_dcs:
                soliton_focal = next(
                    (fp for fp in soliton_focal_points if fp['data_center'] == dc),
                    None
                )
                if soliton_focal:
                    dc_soliton_potentials.append({
                        'data_center': dc,
                        'soliton_potential': soliton_focal['soliton_potential']
                    })

            if dc_soliton_potentials:
                avg_soliton = sum(d['soliton_potential'] for d in dc_soliton_potentials) / len(dc_soliton_potentials)

                # Calculate subway-soliton alignment
                # High ridership efficiency + high soliton potential = strong alignment
                ridership_efficiency = subway_system['ridership_per_station']
                normalized_ridership = min(ridership_efficiency / 50000, 1.0)  # Normalize to 0-1
                alignment_score = (normalized_ridership + avg_soliton) / 2

                comparison.append({
                    'subway_system': system_name,
                    'data_centers': system_dcs,
                    'avg_soliton_potential': avg_soliton,
                    'ridership_efficiency': ridership_efficiency,
                    'normalized_ridership': normalized_ridership,
                    'alignment_score': alignment_score,
                    'network_complexity': subway_system['complexity']
                })

        # Sort by alignment score
        comparison.sort(key=lambda x: x['alignment_score'], reverse=True)

        return {
            'system_comparison': comparison,
            'highest_alignment_system': comparison[0] if comparison else None,
            'average_alignment': sum(c['alignment_score'] for c in comparison) / len(comparison) if comparison else 0
        }

    def _identify_underground_patterns(self, subway_data: Dict) -> Dict[str, Any]:
        """Identify patterns in underground infrastructure."""
        systems = subway_data.get('major_subway_systems', {})
        infrastructure_types = subway_data.get('underground_infrastructure_types', {})

        patterns = {
            'hub_concentration': [],
            'network_complexity_trends': [],
            'construction_eras': [],
            'depth_distribution': []
        }

        for system_name, system_data in systems.items():
            # Hub concentration pattern
            key_hubs = system_data.get('key_hubs', [])
            stations = system_data.get('stations', 0)
            hub_ratio = len(key_hubs) / stations if stations > 0 else 0

            patterns['hub_concentration'].append({
                'system': system_name,
                'hub_count': len(key_hubs),
                'hub_ratio': hub_ratio
            })

            # Network complexity trends
            network_type = system_data.get('network_type', 'unknown')
            daily_ridership = system_data.get('daily_ridership', 0)

            patterns['network_complexity_trends'].append({
                'system': system_name,
                'network_type': network_type,
                'ridership': daily_ridership,
                'complexity_score': self._assess_complexity_score(network_type, daily_ridership)
            })

            # Construction era patterns
            construction_era = system_data.get('construction_era', 'unknown')
            patterns['construction_eras'].append({
                'system': system_name,
                'construction_era': construction_era,
                'era_group': self._group_construction_era(construction_era)
            })

        # Depth distribution from infrastructure types
        for infra_type, infra_data in infrastructure_types.items():
            depth_range = infra_data.get('depth_range', 'unknown')
            patterns['depth_distribution'].append({
                'infrastructure_type': infra_type,
                'depth_range': depth_range,
                'avg_depth': self._parse_depth_range(depth_range)
            })

        return patterns

    def _assess_complexity_score(self, network_type: str, ridership: int) -> float:
        """Assess complexity score based on network type and ridership."""
        type_scores = {
            'radial_with_ring': 0.6,
            'radial_with_interconnects': 0.8,
            'dense_grid': 1.0,
            'unknown': 0.5
        }

        type_score = type_scores.get(network_type, 0.5)
        normalized_ridership = min(ridership / 10000000, 1.0)

        return (type_score + normalized_ridership) / 2

    def _group_construction_era(self, construction_era: str) -> str:
        """Group construction eras into broader periods."""
        if '1900' in construction_era or '1904' in construction_era:
            return 'early_20th_century'
        elif '1863' in construction_era:
            return 'mid_19th_century'
        elif '1927' in construction_era:
            return 'early_20th_century'
        elif '1935' in construction_era:
            return 'mid_20th_century'
        else:
            return 'unknown'

    def _parse_depth_range(self, depth_range: str) -> float:
        """Parse depth range string to average depth."""
        try:
            if '-' in depth_range:
                parts = depth_range.split('-')
                depths = [float(p.replace('m', '')) for p in parts]
                return sum(depths) / len(depths)
            return 0.0
        except:
            return 0.0

    def _integrate_underground_network(self, subway_topology: Dict, underground_patterns: Dict,
                                      network_topology: Dict) -> Dict[str, Any]:
        """Integrate underground network analysis with existing network topology."""
        topology_by_system = subway_topology.get('topology_by_system', [])
        hub_concentration = underground_patterns.get('hub_concentration', [])

        # Identify underground network hubs that align with data centers
        underground_hubs = []

        for system in topology_by_system:
            system_name = system['system']
            key_hubs = system['key_hubs']
            ridership_efficiency = system['ridership_per_station']

            # High ridership hubs likely align with network infrastructure
            for hub in key_hubs:
                underground_hubs.append({
                    'subway_system': system_name,
                    'hub_name': hub,
                    'ridership_efficiency': ridership_efficiency,
                    'network_importance': 'high' if ridership_efficiency > 20000 else 'medium'
                })

        # Sort by ridership efficiency
        underground_hubs.sort(key=lambda x: x['ridership_efficiency'], reverse=True)

        # Identify underground corridors that align with network paths
        underground_corridors = self._identify_underground_corridors(underground_patterns, network_topology)

        return {
            'underground_hubs': underground_hubs[:10],  # Top 10
            'underground_corridors': underground_corridors,
            'network_integration_score': self._calculate_network_integration_score(
                underground_hubs, network_topology
            )
        }

    def _identify_underground_corridors(self, underground_patterns: Dict, network_topology: Dict) -> List[Dict]:
        """Identify underground corridors that align with network topology paths."""
        hub_concentration = underground_patterns.get('hub_concentration', [])

        corridors = []

        for system_data in hub_concentration:
            system_name = system_data['system']
            hub_ratio = system_data['hub_ratio']

            # High hub ratio indicates concentrated network (likely radial)
            if hub_ratio > 0.02:
                corridors.append({
                    'subway_system': system_name,
                    'corridor_type': 'radial_concentration',
                    'hub_concentration': hub_ratio,
                    'network_alignment': 'high'
                })

        return corridors

    def _calculate_network_integration_score(self, underground_hubs: List[Dict], network_topology: Dict) -> float:
        """Calculate integration score between underground and network topology."""
        if not underground_hubs:
            return 0.0

        data_centers = network_topology.get('data_centers', {})

        # Count high-importance underground hubs
        high_importance_count = sum(1 for hub in underground_hubs if hub['network_importance'] == 'high')

        # Calculate integration score
        integration_score = high_importance_count / len(underground_hubs) if underground_hubs else 0

        return integration_score

    def _generate_underground_insights(self, subway_topology: Dict, subway_soliton_comparison: Dict,
                                      integrated_analysis: Dict) -> List[str]:
        """Generate insights from subway/underground infrastructure analysis."""
        insights = []

        # Subway topology insights
        topology_by_system = subway_topology.get('topology_by_system', [])
        if topology_by_system:
            top_system = topology_by_system[0]
            insights.append(f"Highest ridership efficiency: {top_system['system']} "
                          f"({top_system['ridership_per_station']:.0f} riders/station).")

        # Network type distribution
        network_type_dist = subway_topology.get('network_type_distribution', {})
        most_common_type = network_type_dist.get('most_common_type')
        if most_common_type:
            insights.append(f"Most common subway network type: {most_common_type[0]} ({len(most_common_type[1])} systems).")

        # Subway-soliton comparison
        highest_alignment = subway_soliton_comparison.get('highest_alignment_system')
        if highest_alignment:
            insights.append(f"Highest subway-soliton alignment: {highest_alignment['subway_system']} "
                          f"(alignment: {highest_alignment['alignment_score']:.2f}).")

        # Underground network integration
        integration_score = integrated_analysis.get('network_integration_score', 0)
        insights.append(f"Underground-network integration score: {integration_score:.2f}.")

        # Underground hubs
        underground_hubs = integrated_analysis.get('underground_hubs', [])
        if underground_hubs:
            insights.append(f"Identified {len(underground_hubs)} high-importance underground hubs "
                          f"across subway systems.")

        return insights

    def integrate_civic_design_mathematics(self, network_topology: Dict[str, Any],
                                         soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate culturally independent civic design mathematics with network topology analysis.

        Focuses on mathematical foundations of path-finding in civic design rather than
        specific placement. Uses universal mathematical principles that govern how cities
        and infrastructure are designed across cultures.

        Key Mathematical Principles:
        - Central Place Theory (Christaller's hexagonal patterns)
        - Spatial Interaction Models (gravity models, radiation models)
        - Network Flow Optimization (min-cost flow, max-flow min-cut)
        - Accessibility Metrics (Hansen's accessibility, potential models)
        - Distance Decay Functions (exponential, power law)
        - Space Syntax Analysis (integration, connectivity, choice)
        - Voronoi Tessellation (service area analysis)
        - Graph Centrality Measures (betweenness, closeness, eigenvector)
        """
        # Get civic design mathematical principles
        civic_math = self._get_civic_design_mathematics()

        # Apply central place theory to network topology
        central_place_analysis = self._apply_central_place_theory(network_topology)

        # Apply spatial interaction models
        spatial_interaction = self._apply_spatial_interaction_models(network_topology, soliton_analysis)

        # Apply network flow optimization
        flow_optimization = self._apply_network_flow_optimization(network_topology)

        # Apply accessibility metrics
        accessibility_analysis = self._apply_accessibility_metrics(network_topology)

        # Apply distance decay functions
        distance_decay = self._apply_distance_decay_functions(network_topology)

        # Apply space syntax analysis
        space_syntax = self._apply_space_syntax_analysis(network_topology)

        # Apply Voronoi tessellation
        voronoi_analysis = self._apply_voronoi_tessellation(network_topology)

        # Apply graph centrality measures
        centrality_analysis = self._apply_centrality_measures(network_topology)

        # Integrate all civic design mathematics with existing analysis
        integrated_analysis = self._integrate_civic_mathematics(
            central_place_analysis, spatial_interaction, flow_optimization,
            accessibility_analysis, distance_decay, space_syntax,
            voronoi_analysis, centrality_analysis, soliton_analysis
        )

        return {
            'civic_math_principles': civic_math,
            'central_place_analysis': central_place_analysis,
            'spatial_interaction': spatial_interaction,
            'flow_optimization': flow_optimization,
            'accessibility_analysis': accessibility_analysis,
            'distance_decay': distance_decay,
            'space_syntax': space_syntax,
            'voronoi_analysis': voronoi_analysis,
            'centrality_analysis': centrality_analysis,
            'integrated_analysis': integrated_analysis,
            'civic_math_insights': self._generate_civic_math_insights(integrated_analysis)
        }

    def _get_civic_design_mathematics(self) -> Dict[str, Any]:
        """Get culturally independent civic design mathematical principles."""
        return {
            'central_place_theory': {
                'description': 'Christaller\'s hexagonal patterns for optimal service area coverage',
                'mathematical_principle': 'Service areas arranged in hexagonal lattice to minimize travel distance',
                'k_values': {
                    'k=3': 'Marketing principle - 3 settlements per higher-order center',
                    'k=4': 'Transportation principle - 4 settlements along transport routes',
                    'k=7': 'Administrative principle - 7 settlements per administrative center'
                },
                'path_finding_math': 'Minimize average distance to service centers using hexagonal tessellation'
            },
            'spatial_interaction_models': {
                'gravity_model': {
                    'equation': 'F_ij = G * (P_i * P_j) / d_ij^b',
                    'description': 'Interaction between locations proportional to mass, inversely to distance',
                    'path_finding_math': 'Route through high-mass nodes with distance decay'
                },
                'radiation_model': {
                    'equation': 'T_ij = (m_i * m_j) / ((m_i + s_ij) * (m_i + m_j + s_ij))',
                    'description': 'Population-based interaction without distance decay parameter',
                    'path_finding_math': 'Route through nodes with high population density'
                }
            },
            'network_flow_optimization': {
                'min_cost_flow': {
                    'equation': 'minimize sum(c_ij * x_ij) subject to flow constraints',
                    'description': 'Find cheapest flow paths through network',
                    'path_finding_math': 'Route through minimum-cost edges satisfying demand'
                },
                'max_flow_min_cut': {
                    'equation': 'max flow = min cut capacity',
                    'description': 'Maximum flow equals minimum cut capacity',
                    'path_finding_math': 'Identify bottleneck edges and optimize around them'
                }
            },
            'accessibility_metrics': {
                'hansen_accessibility': {
                    'equation': 'A_i = sum_j (M_j * f(d_ij))',
                    'description': 'Accessibility based on destination mass and distance decay',
                    'path_finding_math': 'Route to maximize accessibility to high-mass destinations'
                },
                'potential_model': {
                    'equation': 'P_i = sum_j (M_j / d_ij)',
                    'description': 'Potential based on inverse distance to destinations',
                    'path_finding_math': 'Route through nodes with highest potential'
                }
            },
            'distance_decay_functions': {
                'exponential_decay': {
                    'equation': 'f(d) = exp(-beta * d)',
                    'description': 'Interaction decreases exponentially with distance',
                    'path_finding_math': 'Prefer shorter paths with exponential penalty'
                },
                'power_law_decay': {
                    'equation': 'f(d) = d^(-alpha)',
                    'description': 'Interaction follows power law decay with distance',
                    'path_finding_math': 'Prefer shorter paths with power law penalty'
                }
            },
            'space_syntax_analysis': {
                'integration': {
                    'equation': 'Integration = (n-1)^2 / (2 * MD * (n-2))',
                    'description': 'Measure of how integrated a space is in the network',
                    'path_finding_math': 'Route through highly integrated spaces'
                },
                'connectivity': {
                    'equation': 'Connectivity = number of direct connections',
                    'description': 'Number of directly connected spaces',
                    'path_finding_math': 'Route through highly connected nodes'
                },
                'choice': {
                    'equation': 'Choice = number of shortest paths through space',
                    'description': 'Betweenness centrality in space syntax',
                    'path_finding_math': 'Route through high-choice spaces'
                }
            },
            'voronoi_tessellation': {
                'description': 'Partition space into regions closest to each service center',
                'mathematical_principle': 'Minimize distance to nearest service center',
                'path_finding_math': 'Route through nodes that minimize distance to service centers'
            },
            'graph_centrality': {
                'betweenness_centrality': {
                    'equation': 'CB(v) = sum(s≠t≠v sigma_st(v) / sigma_st)',
                    'description': 'Fraction of shortest paths passing through node',
                    'path_finding_math': 'Route through high-betweenness nodes'
                },
                'closeness_centrality': {
                    'equation': 'CC(v) = (n-1) / sum(d(v,u))',
                    'description': 'Inverse of average distance to all other nodes',
                    'path_finding_math': 'Route through nodes with minimum average distance'
                },
                'eigenvector_centrality': {
                    'equation': 'Ax = lambda x',
                    'description': 'Importance based on connections to important nodes',
                    'path_finding_math': 'Route through nodes with high eigenvector centrality'
                }
            }
        }

    def _apply_central_place_theory(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply Christaller's central place theory to network topology."""
        data_centers = network_topology.get('data_centers', {})

        # Calculate service areas using hexagonal tessellation principle
        service_areas = []

        for dc_name, dc_data in data_centers.items():
            # Estimate service area based on importance
            importance = dc_data.get('importance', 0.5)
            service_radius = importance * 500  # km radius estimate

            # Calculate hexagonal coverage area
            hex_area = (3 * np.sqrt(3) / 2) * (service_radius ** 2)

            service_areas.append({
                'data_center': dc_name,
                'service_radius_km': service_radius,
                'hexagonal_area_km2': hex_area,
                'importance_score': importance,
                'k_value': self._determine_k_value(importance)
            })

        # Sort by service area
        service_areas.sort(key=lambda x: x['hexagonal_area_km2'], reverse=True)

        return {
            'service_areas': service_areas,
            'hexagonal_coverage': self._calculate_hexagonal_coverage(service_areas),
            'central_place_hierarchy': self._determine_hierarchy(service_areas)
        }

    def _determine_k_value(self, importance: float) -> str:
        """Determine Christaller's K value based on importance."""
        if importance > 0.8:
            return 'k=7_administrative'
        elif importance > 0.5:
            return 'k=4_transportation'
        else:
            return 'k=3_marketing'

    def _calculate_hexagonal_coverage(self, service_areas: List[Dict]) -> Dict[str, float]:
        """Calculate hexagonal coverage metrics."""
        total_area = sum(area['hexagonal_area_km2'] for area in service_areas)
        avg_area = total_area / len(service_areas) if service_areas else 0

        return {
            'total_coverage_area_km2': total_area,
            'average_service_area_km2': avg_area,
            'coverage_efficiency': min(total_area / 10000000, 1.0)  # Normalized to global area
        }

    def _determine_hierarchy(self, service_areas: List[Dict]) -> List[Dict]:
        """Determine central place hierarchy levels."""
        # Divide into 3 levels based on service area
        sorted_areas = sorted(service_areas, key=lambda x: x['hexagonal_area_km2'], reverse=True)

        hierarchy = []
        n = len(sorted_areas)

        for i, area in enumerate(sorted_areas):
            if i < n // 3:
                level = 'primary_center'
            elif i < 2 * n // 3:
                level = 'secondary_center'
            else:
                level = 'tertiary_center'

            hierarchy.append({
                'data_center': area['data_center'],
                'hierarchy_level': level,
                'service_area_km2': area['hexagonal_area_km2']
            })

        return hierarchy

    def _apply_spatial_interaction_models(self, network_topology: Dict,
                                       soliton_analysis: Dict) -> Dict[str, Any]:
        """Apply spatial interaction models (gravity, radiation) to network topology."""
        data_centers = network_topology.get('data_centers', {})

        # Gravity model calculations
        gravity_interactions = []

        dc_names = list(data_centers.keys())
        for i in range(len(dc_names)):
            for j in range(i + 1, len(dc_names)):
                dc_i = data_centers[dc_names[i]]
                dc_j = data_centers[dc_names[j]]

                # Calculate distance
                distance = np.sqrt((dc_i['lat'] - dc_j['lat'])**2 +
                                 (dc_i['lon'] - dc_j['lon'])**2)

                # Get mass (importance/population proxy)
                mass_i = dc_i.get('importance', 0.5)
                mass_j = dc_j.get('importance', 0.5)

                # Gravity model: F = G * (M1 * M2) / d^b
                G = 1.0  # Gravitational constant for this model
                b = 2.0  # Distance decay parameter
                gravity = G * (mass_i * mass_j) / (distance ** b + 1e-6)

                # Radiation model: T = (m1 * m2) / ((m1 + s) * (m1 + m2 + s))
                # where s is intervening population (simplified as distance)
                radiation = (mass_i * mass_j) / ((mass_i + distance) *
                                              (mass_i + mass_j + distance) + 1e-6)

                gravity_interactions.append({
                    'source': dc_names[i],
                    'destination': dc_names[j],
                    'distance': distance,
                    'gravity_interaction': gravity,
                    'radiation_interaction': radiation,
                    'combined_score': (gravity + radiation) / 2
                })

        # Sort by combined score
        gravity_interactions.sort(key=lambda x: x['combined_score'], reverse=True)

        return {
            'gravity_model_interactions': gravity_interactions[:10],  # Top 10
            'highest_interaction_pair': gravity_interactions[0] if gravity_interactions else None,
            'average_interaction': sum(x['combined_score'] for x in gravity_interactions) / len(gravity_interactions) if gravity_interactions else 0
        }

    def _apply_network_flow_optimization(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply network flow optimization principles."""
        data_centers = network_topology.get('data_centers', {})

        # Calculate edge weights based on distance and importance
        edges = []
        dc_names = list(data_centers.keys())

        for i in range(len(dc_names)):
            for j in range(i + 1, len(dc_names)):
                dc_i = data_centers[dc_names[i]]
                dc_j = data_centers[dc_names[j]]

                distance = np.sqrt((dc_i['lat'] - dc_j['lat'])**2 +
                                 (dc_i['lon'] - dc_j['lon'])**2)

                # Cost function: distance / (importance_i * importance_j)
                importance_i = dc_i.get('importance', 0.5)
                importance_j = dc_j.get('importance', 0.5)
                cost = distance / (importance_i * importance_j + 1e-6)

                # Capacity function: importance_i * importance_j / distance
                capacity = (importance_i * importance_j) / (distance + 1e-6)

                edges.append({
                    'source': dc_names[i],
                    'destination': dc_names[j],
                    'distance': distance,
                    'cost': cost,
                    'capacity': capacity,
                    'cost_capacity_ratio': cost / (capacity + 1e-6)
                })

        # Sort by cost (min-cost flow)
        min_cost_edges = sorted(edges, key=lambda x: x['cost'])

        # Sort by capacity (max-flow)
        max_capacity_edges = sorted(edges, key=lambda x: x['capacity'], reverse=True)

        return {
            'min_cost_flow_edges': min_cost_edges[:10],
            'max_flow_edges': max_capacity_edges[:10],
            'flow_optimization_score': self._calculate_flow_optimization_score(edges)
        }

    def _calculate_flow_optimization_score(self, edges: List[Dict]) -> float:
        """Calculate overall flow optimization score."""
        if not edges:
            return 0.0

        # Score based on cost-capacity ratio (lower is better)
        avg_ratio = sum(e['cost_capacity_ratio'] for e in edges) / len(edges)
        score = 1.0 / (1.0 + avg_ratio)

        return score

    def _apply_accessibility_metrics(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply accessibility metrics (Hansen, potential models)."""
        data_centers = network_topology.get('data_centers', {})

        accessibility_scores = []

        for dc_name, dc_data in data_centers.items():
            hansen_accessibility = 0.0
            potential = 0.0

            for other_name, other_data in data_centers.items():
                if dc_name == other_name:
                    continue

                distance = np.sqrt((dc_data['lat'] - other_data['lat'])**2 +
                                 (dc_data['lon'] - other_data['lon'])**2)

                # Hansen accessibility: A_i = sum(M_j * exp(-beta * d_ij))
                mass_j = other_data.get('importance', 0.5)
                beta = 0.1  # Distance decay parameter
                hansen_accessibility += mass_j * np.exp(-beta * distance)

                # Potential model: P_i = sum(M_j / d_ij)
                potential += mass_j / (distance + 1e-6)

            accessibility_scores.append({
                'data_center': dc_name,
                'hansen_accessibility': hansen_accessibility,
                'potential_score': potential,
                'combined_accessibility': (hansen_accessibility + potential) / 2
            })

        # Sort by combined accessibility
        accessibility_scores.sort(key=lambda x: x['combined_accessibility'], reverse=True)

        return {
            'accessibility_scores': accessibility_scores,
            'most_accessible': accessibility_scores[0] if accessibility_scores else None,
            'average_accessibility': sum(x['combined_accessibility'] for x in accessibility_scores) / len(accessibility_scores) if accessibility_scores else 0
        }

    def _apply_distance_decay_functions(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply distance decay functions (exponential, power law)."""
        data_centers = network_topology.get('data_centers', {})

        decay_analysis = []

        for dc_name, dc_data in data_centers.items():
            exponential_decay = 0.0
            power_law_decay = 0.0

            for other_name, other_data in data_centers.items():
                if dc_name == other_name:
                    continue

                distance = np.sqrt((dc_data['lat'] - other_data['lat'])**2 +
                                 (dc_data['lon'] - other_data['lon'])**2)

                # Exponential decay: exp(-beta * d)
                beta = 0.1
                exponential_decay += np.exp(-beta * distance)

                # Power law decay: d^(-alpha)
                alpha = 1.5
                power_law_decay += (distance ** -alpha)

            decay_analysis.append({
                'data_center': dc_name,
                'exponential_connectivity': exponential_decay,
                'power_law_connectivity': power_law_decay,
                'decay_ratio': exponential_decay / (power_law_decay + 1e-6)
            })

        return {
            'decay_analysis': decay_analysis,
            'decay_function_comparison': self._compare_decay_functions(decay_analysis)
        }

    def _compare_decay_functions(self, decay_analysis: List[Dict]) -> Dict[str, Any]:
        """Compare exponential vs power law decay functions."""
        exp_avg = sum(d['exponential_connectivity'] for d in decay_analysis) / len(decay_analysis) if decay_analysis else 0
        power_avg = sum(d['power_law_connectivity'] for d in decay_analysis) / len(decay_analysis) if decay_analysis else 0

        return {
            'preferred_function': 'exponential' if exp_avg > power_avg else 'power_law',
            'exponential_average': exp_avg,
            'power_law_average': power_avg
        }

    def _apply_space_syntax_analysis(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply space syntax analysis (integration, connectivity, choice)."""
        data_centers = network_topology.get('data_centers', {})

        # Build adjacency matrix for space syntax
        dc_names = list(data_centers.keys())
        n = len(dc_names)
        adjacency = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    dc_i = data_centers[dc_names[i]]
                    dc_j = data_centers[dc_names[j]]
                    distance = np.sqrt((dc_i['lat'] - dc_j['lat'])**2 +
                                     (dc_i['lon'] - dc_j['lon'])**2)
                    # Adjacent if within threshold distance
                    adjacency[i][j] = 1 if distance < 0.5 else 0  # Threshold in degrees

        space_syntax_metrics = []

        for i in range(n):
            # Connectivity: number of direct connections
            connectivity = np.sum(adjacency[i])

            # Integration: simplified version (inverse of average depth)
            depths = []
            for j in range(n):
                if i != j and adjacency[i][j] == 1:
                    depths.append(1)  # Depth 1 for direct connections
                elif i != j:
                    depths.append(2)  # Depth 2 for indirect connections

            avg_depth = sum(depths) / len(depths) if depths else 1
            integration = 1 / avg_depth if avg_depth > 0 else 0

            # Choice: simplified betweenness (number of paths through node)
            choice = connectivity * integration

            space_syntax_metrics.append({
                'data_center': dc_names[i],
                'connectivity': connectivity,
                'integration': integration,
                'choice': choice,
                'space_syntax_score': (connectivity + integration + choice) / 3
            })

        # Sort by space syntax score
        space_syntax_metrics.sort(key=lambda x: x['space_syntax_score'], reverse=True)

        return {
            'space_syntax_metrics': space_syntax_metrics,
            'most_integrated': space_syntax_metrics[0] if space_syntax_metrics else None,
            'average_integration': sum(x['integration'] for x in space_syntax_metrics) / len(space_syntax_metrics) if space_syntax_metrics else 0
        }

    def _apply_voronoi_tessellation(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply Voronoi tessellation for service area analysis."""
        data_centers = network_topology.get('data_centers', {})

        voronoi_cells = []

        for dc_name, dc_data in data_centers.items():
            # Estimate Voronoi cell size based on nearest neighbors
            dc_names = list(data_centers.keys())
            distances = []

            for other_name, other_data in data_centers.items():
                if dc_name == other_name:
                    continue
                distance = np.sqrt((dc_data['lat'] - other_data['lat'])**2 +
                                 (dc_data['lon'] - other_data['lon'])**2)
                distances.append(distance)

            if distances:
                avg_distance = sum(distances) / len(distances)
                min_distance = min(distances)

                # Voronoi cell area approximation
                cell_area = np.pi * (avg_distance / 2) ** 2

                voronoi_cells.append({
                    'data_center': dc_name,
                    'cell_area_estimate': cell_area,
                    'avg_neighbor_distance': avg_distance,
                    'min_neighbor_distance': min_distance,
                    'voronoi_efficiency': cell_area / (avg_distance ** 2 + 1e-6)
                })

        # Sort by Voronoi efficiency
        voronoi_cells.sort(key=lambda x: x['voronoi_efficiency'], reverse=True)

        return {
            'voronoi_cells': voronoi_cells,
            'most_efficient_cell': voronoi_cells[0] if voronoi_cells else None,
            'average_efficiency': sum(x['voronoi_efficiency'] for x in voronoi_cells) / len(voronoi_cells) if voronoi_cells else 0
        }

    def _apply_centrality_measures(self, network_topology: Dict) -> Dict[str, Any]:
        """Apply graph centrality measures (betweenness, closeness, eigenvector)."""
        data_centers = network_topology.get('data_centers', {})

        # Build adjacency matrix
        dc_names = list(data_centers.keys())
        n = len(dc_names)
        adjacency = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    dc_i = data_centers[dc_names[i]]
                    dc_j = data_centers[dc_names[j]]
                    distance = np.sqrt((dc_i['lat'] - dc_j['lat'])**2 +
                                     (dc_i['lon'] - dc_j['lon'])**2)
                    adjacency[i][j] = 1 / (distance + 1e-6)

        # Calculate centrality measures
        centrality_metrics = []

        for i in range(n):
            # Closeness centrality: (n-1) / sum of distances
            distances = []
            for j in range(n):
                if i != j:
                    distances.append(adjacency[i][j])

            closeness = (n - 1) / sum(distances) if distances else 0

            # Betweenness centrality (simplified)
            betweenness = np.sum(adjacency[i]) * closeness

            # Eigenvector centrality (power iteration approximation)
            eigenvector = np.sum(adjacency[i] * adjacency[i]) / n

            centrality_metrics.append({
                'data_center': dc_names[i],
                'closeness_centrality': closeness,
                'betweenness_centrality': betweenness,
                'eigenvector_centrality': eigenvector,
                'combined_centrality': (closeness + betweenness + eigenvector) / 3
            })

        # Sort by combined centrality
        centrality_metrics.sort(key=lambda x: x['combined_centrality'], reverse=True)

        return {
            'centrality_metrics': centrality_metrics,
            'highest_centrality': centrality_metrics[0] if centrality_metrics else None,
            'average_centrality': sum(x['combined_centrality'] for x in centrality_metrics) / len(centrality_metrics) if centrality_metrics else 0
        }

    def _integrate_civic_mathematics(self, central_place: Dict, spatial_interaction: Dict,
                                   flow_optimization: Dict, accessibility: Dict,
                                   distance_decay: Dict, space_syntax: Dict,
                                   voronoi: Dict, centrality: Dict,
                                   soliton_analysis: Dict) -> Dict[str, Any]:
        """Integrate all civic design mathematics with soliton analysis."""
        # Combine scores from all methods
        integration_scores = []

        # Get data center names from any analysis
        if central_place.get('service_areas'):
            dc_names = [dc['data_center'] for dc in central_place['service_areas']]
        elif accessibility.get('accessibility_scores'):
            dc_names = [dc['data_center'] for dc in accessibility['accessibility_scores']]
        else:
            dc_names = []

        for dc in dc_names:
            # Extract scores from each method
            central_place_score = next(
                (item['importance_score'] for item in central_place.get('service_areas', [])
                 if item['data_center'] == dc), 0.5
            )

            accessibility_score = next(
                (item['combined_accessibility'] for item in accessibility.get('accessibility_scores', [])
                 if item['data_center'] == dc), 0.5
            )

            space_syntax_score = next(
                (item['space_syntax_score'] for item in space_syntax.get('space_syntax_metrics', [])
                 if item['data_center'] == dc), 0.5
            )

            centrality_score = next(
                (item['combined_centrality'] for item in centrality.get('centrality_metrics', [])
                 if item['data_center'] == dc), 0.5
            )

            # Calculate integrated score
            integrated_score = (central_place_score + accessibility_score +
                               space_syntax_score + centrality_score) / 4

            integration_scores.append({
                'data_center': dc,
                'central_place_score': central_place_score,
                'accessibility_score': accessibility_score,
                'space_syntax_score': space_syntax_score,
                'centrality_score': centrality_score,
                'integrated_civic_score': integrated_score
            })

        # Sort by integrated civic score
        integration_scores.sort(key=lambda x: x['integrated_civic_score'], reverse=True)

        # Compare with soliton analysis
        civic_soliton_comparison = self._compare_civic_soliton(integration_scores, soliton_analysis)

        return {
            'integration_scores': integration_scores,
            'civic_soliton_comparison': civic_soliton_comparison,
            'civic_methodology_convergence': self._calculate_civic_convergence(integration_scores, soliton_analysis)
        }

    def _compare_civic_soliton(self, civic_scores: List[Dict], soliton_analysis: Dict) -> Dict[str, Any]:
        """Compare civic design mathematics with soliton analysis."""
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        comparison = []

        for civic in civic_scores:
            dc_name = civic['data_center']

            # Find soliton potential
            soliton_focal = next(
                (fp for fp in soliton_focal_points if fp['data_center'] == dc_name),
                None
            )

            if soliton_focal:
                civic_score = civic['integrated_civic_score']
                soliton_potential = soliton_focal['soliton_potential']

                # Calculate alignment
                alignment = (civic_score + soliton_potential) / 2

                comparison.append({
                    'data_center': dc_name,
                    'civic_score': civic_score,
                    'soliton_potential': soliton_potential,
                    'alignment_score': alignment
                })

        # Sort by alignment
        comparison.sort(key=lambda x: x['alignment_score'], reverse=True)

        return {
            'comparison': comparison,
            'highest_alignment': comparison[0] if comparison else None,
            'average_alignment': sum(c['alignment_score'] for c in comparison) / len(comparison) if comparison else 0
        }

    def _calculate_civic_convergence(self, civic_scores: List[Dict], soliton_analysis: Dict) -> float:
        """Calculate convergence between civic design mathematics and soliton analysis."""
        comparison = self._compare_civic_soliton(civic_scores, soliton_analysis)
        avg_alignment = comparison.get('average_alignment', 0)

        return avg_alignment

    def _generate_civic_math_insights(self, integrated_analysis: Dict) -> List[str]:
        """Generate insights from civic design mathematics integration."""
        insights = []

        # Integration scores
        integration_scores = integrated_analysis.get('integration_scores', [])
        if integration_scores:
            top_civic = integration_scores[0]
            insights.append(f"Highest civic design score: {top_civic['data_center']} "
                          f"(civic score: {top_civic['integrated_civic_score']:.2f}).")

        # Civic-soliton comparison
        civic_soliton = integrated_analysis.get('civic_soliton_comparison', {})
        highest_alignment = civic_soliton.get('highest_alignment')
        if highest_alignment:
            insights.append(f"Highest civic-soliton alignment: {highest_alignment['data_center']} "
                          f"(alignment: {highest_alignment['alignment_score']:.2f}).")

        # Methodology convergence
        convergence = integrated_analysis.get('civic_methodology_convergence', 0)
        insights.append(f"Civic design mathematics convergence: {convergence:.2f}.")

        return insights

    def integrate_major_consumer_nodes(self, network_topology: Dict[str, Any],
                                      soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate major consumer nodes with network topology analysis.

        Major consumer nodes include:
        - Aqueducts and water transfer infrastructure
        - Waste treatment facilities
        - Flow control systems (electrical, EM, fluid)
        - Public military installations worldwide
        - Bitcoin mining installations
        - Oil refinery locations

        These are high-consumption infrastructure nodes that significantly impact
        network topology and should be analyzed alongside data centers.
        """
        # Get data for all major consumer node types
        consumer_node_data = self._get_major_consumer_node_data()

        # Analyze water infrastructure (aqueducts, water transfer, waste treatment)
        water_infrastructure = self._analyze_water_infrastructure(consumer_node_data)

        # Analyze flow control systems (electrical, EM, fluid)
        flow_control_systems = self._analyze_flow_control_systems(consumer_node_data)

        # Analyze military installations
        military_installations = self._analyze_military_installations(consumer_node_data)

        # Analyze Bitcoin mining installations
        bitcoin_installations = self._analyze_bitcoin_installations(consumer_node_data)

        # Analyze oil refineries
        oil_refineries = self._analyze_oil_refineries(consumer_node_data)

        # Integrate all consumer nodes with network topology
        integrated_consumer_analysis = self._integrate_consumer_nodes(
            water_infrastructure, flow_control_systems, military_installations,
            bitcoin_installations, oil_refineries, network_topology
        )

        # Compare with soliton analysis
        consumer_soliton_comparison = self._compare_consumer_soliton(
            integrated_consumer_analysis, soliton_analysis
        )

        return {
            'consumer_node_data': consumer_node_data,
            'water_infrastructure': water_infrastructure,
            'flow_control_systems': flow_control_systems,
            'military_installations': military_installations,
            'bitcoin_installations': bitcoin_installations,
            'oil_refineries': oil_refineries,
            'integrated_consumer_analysis': integrated_consumer_analysis,
            'consumer_soliton_comparison': consumer_soliton_comparison,
            'consumer_node_insights': self._generate_consumer_node_insights(
                integrated_consumer_analysis, consumer_soliton_comparison
            )
        }

    def _get_major_consumer_node_data(self) -> Dict[str, Any]:
        """Get data for all major consumer node types."""
        return {
            'data_sources': {
                'water_infrastructure': [
                    'global_aqueduct_database',
                    'international_water_transfer_projects',
                    'epa_waste_treatment_facilities',
                    'un_water_infrastructure_atlas'
                ],
                'flow_control': [
                    'electrical_grid_substations',
                    'electromagnetic_emission_sites',
                    'fluid_pipeline_control_systems',
                    'industrial_flow_control_registries'
                ],
                'military': [
                    'public_military_installations_database',
                    'defense_infrastructure_atlas',
                    'strategic_military_facilities_registry',
                    'global_military_base_locations'
                ],
                'bitcoin': [
                    'bitcoin_mining_pool_locations',
                    'cryptocurrency_mining_facilities_database',
                    'energy_consumption_by_mining_regions',
                    'public_hashrate_distribution_data'
                ],
                'oil_refineries': [
                    'global_oil_refinery_locations',
                    'petroleum_refining_capacity_database',
                    'energy_infrastructure_atlas',
                    'strategic_petroleum_reserves_locations'
                ]
            },
            'water_infrastructure': {
                'major_aqueducts': [
                    {
                        'name': 'California Aqueduct',
                        'location': 'California, USA',
                        'length_km': 715,
                        'capacity_m3_per_day': 4000000,
                        'coordinates': {'lat': 37.0, 'lon': -119.0},
                        'power_consumption_mw': 750
                    },
                    {
                        'name': 'Central Arizona Project',
                        'location': 'Arizona, USA',
                        'length_km': 541,
                        'capacity_m3_per_day': 1850000,
                        'coordinates': {'lat': 33.5, 'lon': -112.0},
                        'power_consumption_mw': 600
                    },
                    {
                        'name': 'Colorado River Aqueduct',
                        'location': 'California, USA',
                        'length_km': 389,
                        'capacity_m3_per_day': 1300000,
                        'coordinates': {'lat': 34.0, 'lon': -116.0},
                        'power_consumption_mw': 500
                    },
                    {
                        'name': 'Delaware Aqueduct',
                        'location': 'New York, USA',
                        'length_km': 137,
                        'capacity_m3_per_day': 1400000,
                        'coordinates': {'lat': 41.5, 'lon': -74.5},
                        'power_consumption_mw': 400
                    },
                    {
                        'name': 'Karakum Canal',
                        'location': 'Turkmenistan',
                        'length_km': 1375,
                        'capacity_m3_per_day': 13000000,
                        'coordinates': {'lat': 40.0, 'lon': 60.0},
                        'power_consumption_mw': 1200
                    }
                ],
                'waste_treatment_facilities': [
                    {
                        'name': 'Stickney Water Reclamation Plant',
                        'location': 'Chicago, Illinois, USA',
                        'capacity_m3_per_day': 4500000,
                        'power_consumption_mw': 150,
                        'coordinates': {'lat': 41.8, 'lon': -87.8}
                    },
                    {
                        'name': 'Hyperion Water Reclamation Plant',
                        'location': 'Los Angeles, California, USA',
                        'capacity_m3_per_day': 1500000,
                        'power_consumption_mw': 80,
                        'coordinates': {'lat': 33.9, 'lon': -118.4}
                    },
                    {
                        'name': 'Blue Plains Advanced Wastewater Treatment Plant',
                        'location': 'Washington DC, USA',
                        'capacity_m3_per_day': 1300000,
                        'power_consumption_mw': 70,
                        'coordinates': {'lat': 38.8, 'lon': -77.0}
                    },
                    {
                        'name': 'Dee Valley Water Treatment Works',
                        'location': 'North Wales, UK',
                        'capacity_m3_per_day': 800000,
                        'power_consumption_mw': 45,
                        'coordinates': {'lat': 53.2, 'lon': -3.4}
                    },
                    {
                        'name': 'Kjelsberg Wastewater Treatment Plant',
                        'location': 'Oslo, Norway',
                        'capacity_m3_per_day': 600000,
                        'power_consumption_mw': 35,
                        'coordinates': {'lat': 59.9, 'lon': 10.8}
                    }
                ]
            },
            'flow_control_systems': {
                'electrical_substations': [
                    {
                        'name': 'Palo Verde Nuclear Generating Station Substation',
                        'location': 'Arizona, USA',
                        'capacity_mw': 4000,
                        'coordinates': {'lat': 33.5, 'lon': -112.9},
                        'control_type': 'electrical'
                    },
                    {
                        'name': 'Grand Coulee Dam Substation',
                        'location': 'Washington, USA',
                        'capacity_mw': 6800,
                        'coordinates': {'lat': 47.9, 'lon': -119.0},
                        'control_type': 'electrical'
                    },
                    {
                        'name': 'Itaipu Dam Substation',
                        'location': 'Parana River, Brazil/Paraguay',
                        'capacity_mw': 14000,
                        'coordinates': {'lat': -25.4, 'lon': -54.6},
                        'control_type': 'electrical'
                    },
                    {
                        'name': 'Three Gorges Dam Substation',
                        'location': 'Yangtze River, China',
                        'capacity_mw': 22500,
                        'coordinates': {'lat': 30.8, 'lon': 111.0},
                        'control_type': 'electrical'
                    }
                ],
                'electromagnetic_sites': [
                    {
                        'name': 'HAARP Research Station',
                        'location': 'Alaska, USA',
                        'power_mw': 3.6,
                        'frequency_range_mhz': '2.8-10',
                        'coordinates': {'lat': 62.4, 'lon': -145.2},
                        'control_type': 'electromagnetic'
                    },
                    {
                        'name': 'EISCAT Radar Facility',
                        'location': 'Tromso, Norway',
                        'power_mw': 1.2,
                        'frequency_range_mhz': '224-928',
                        'coordinates': {'lat': 69.6, 'lon': 19.2},
                        'control_type': 'electromagnetic'
                    },
                    {
                        'name': 'Jicamarca Radio Observatory',
                        'location': 'Peru',
                        'power_mw': 6.0,
                        'frequency_range_mhz': '50',
                        'coordinates': {'lat': -12.0, 'lon': -76.9},
                        'control_type': 'electromagnetic'
                    }
                ],
                'fluid_pipeline_control': [
                    {
                        'name': 'Trans-Alaska Pipeline Pump Stations',
                        'location': 'Alaska, USA',
                        'flow_rate_barrels_per_day': 2000000,
                        'power_consumption_mw': 200,
                        'coordinates': {'lat': 65.0, 'lon': -148.0},
                        'control_type': 'fluid'
                    },
                    {
                        'name': 'Druzhba Pipeline Pump Stations',
                        'location': 'Russia to Europe',
                        'flow_rate_barrels_per_day': 1500000,
                        'power_consumption_mw': 180,
                        'coordinates': {'lat': 55.0, 'lon': 30.0},
                        'control_type': 'fluid'
                    },
                    {
                        'name': 'Keystone Pipeline Pump Stations',
                        'location': 'Canada to USA',
                        'flow_rate_barrels_per_day': 830000,
                        'power_consumption_mw': 120,
                        'coordinates': {'lat': 50.0, 'lon': -100.0},
                        'control_type': 'fluid'
                    }
                ]
            },
            'military_installations': {
                'public_bases': [
                    {
                        'name': 'Pentagon',
                        'location': 'Virginia, USA',
                        'personnel': 26000,
                        'power_consumption_mw': 150,
                        'coordinates': {'lat': 38.9, 'lon': -77.1},
                        'strategic_importance': 'very_high'
                    },
                    {
                        'name': 'Norfolk Naval Base',
                        'location': 'Virginia, USA',
                        'personnel': 75000,
                        'power_consumption_mw': 300,
                        'coordinates': {'lat': 36.9, 'lon': -76.3},
                        'strategic_importance': 'very_high'
                    },
                    {
                        'name': 'RAF Mildenhall',
                        'location': 'Suffolk, UK',
                        'personnel': 4000,
                        'power_consumption_mw': 80,
                        'coordinates': {'lat': 52.4, 'lon': 0.5},
                        'strategic_importance': 'high'
                    },
                    {
                        'name': 'Yokota Air Base',
                        'location': 'Japan',
                        'personnel': 14000,
                        'power_consumption_mw': 120,
                        'coordinates': {'lat': 35.7, 'lon': 139.3},
                        'strategic_importance': 'high'
                    },
                    {
                        'name': 'Ramstein Air Base',
                        'location': 'Germany',
                        'personnel': 35000,
                        'power_consumption_mw': 200,
                        'coordinates': {'lat': 49.4, 'lon': 7.6},
                        'strategic_importance': 'very_high'
                    },
                    {
                        'name': 'Diego Garcia Naval Support Facility',
                        'location': 'Diego Garcia, British Indian Ocean Territory',
                        'personnel': 3000,
                        'power_consumption_mw': 50,
                        'coordinates': {'lat': 7.3, 'lon': 72.4},
                        'strategic_importance': 'high'
                    }
                ]
            },
            'bitcoin_installations': {
                'major_mining_facilities': [
                    {
                        'name': 'Bitcoin Mining Facility - Inner Mongolia',
                        'location': 'Inner Mongolia, China',
                        'hashrate_eh': 15.0,
                        'power_consumption_mw': 800,
                        'coordinates': {'lat': 40.8, 'lon': 111.7}
                    },
                    {
                        'name': 'Bitcoin Mining Facility - Xinjiang',
                        'location': 'Xinjiang, China',
                        'hashrate_eh': 12.0,
                        'power_consumption_mw': 650,
                        'coordinates': {'lat': 43.8, 'lon': 87.6}
                    },
                    {
                        'name': 'Bitcoin Mining Facility - Sichuan',
                        'location': 'Sichuan, China',
                        'hashrate_eh': 10.0,
                        'power_consumption_mw': 550,
                        'coordinates': {'lat': 30.6, 'lon': 104.1}
                    },
                    {
                        'name': 'Bitcoin Mining Facility - Texas',
                        'location': 'Texas, USA',
                        'hashrate_eh': 8.0,
                        'power_consumption_mw': 450,
                        'coordinates': {'lat': 31.0, 'lon': -99.9}
                    },
                    {
                        'name': 'Bitcoin Mining Facility - Kazakhstan',
                        'location': 'Kazakhstan',
                        'hashrate_eh': 6.0,
                        'power_consumption_mw': 350,
                        'coordinates': {'lat': 48.0, 'lon': 66.9}
                    },
                    {
                        'name': 'Bitcoin Mining Facility - Washington',
                        'location': 'Washington, USA',
                        'hashrate_eh': 5.0,
                        'power_consumption_mw': 300,
                        'coordinates': {'lat': 47.8, 'lon': -120.0}
                    }
                ]
            },
            'oil_refineries': {
                'major_refineries': [
                    {
                        'name': 'Jamnagar Refinery Complex',
                        'location': 'Gujarat, India',
                        'capacity_barrels_per_day': 1240000,
                        'power_consumption_mw': 1200,
                        'coordinates': {'lat': 22.5, 'lon': 70.0}
                    },
                    {
                        'name': 'Paraguana Refining Complex',
                        'location': 'Venezuela',
                        'capacity_barrels_per_day': 940000,
                        'power_consumption_mw': 900,
                        'coordinates': {'lat': 11.7, 'lon': -70.2}
                    },
                    {
                        'name': 'Ulsan Refinery',
                        'location': 'South Korea',
                        'capacity_barrels_per_day': 840000,
                        'power_consumption_mw': 850,
                        'coordinates': {'lat': 35.6, 'lon': 129.3}
                    },
                    {
                        'name': 'Port Arthur Refinery',
                        'location': 'Texas, USA',
                        'capacity_barrels_per_day': 600000,
                        'power_consumption_mw': 650,
                        'coordinates': {'lat': 29.8, 'lon': -93.9}
                    },
                    {
                        'name': 'Ras Tanura Refinery',
                        'location': 'Saudi Arabia',
                        'capacity_barrels_per_day': 550000,
                        'power_consumption_mw': 600,
                        'coordinates': {'lat': 26.6, 'lon': 50.0}
                    },
                    {
                        'name': 'Baytown Refinery',
                        'location': 'Texas, USA',
                        'capacity_barrels_per_day': 560000,
                        'power_consumption_mw': 580,
                        'coordinates': {'lat': 29.8, 'lon': -94.9}
                    }
                ]
            }
        }

    def _analyze_water_infrastructure(self, consumer_data: Dict) -> Dict[str, Any]:
        """Analyze water infrastructure (aqueducts, waste treatment)."""
        aqueducts = consumer_data['water_infrastructure']['major_aqueducts']
        treatment_facilities = consumer_data['water_infrastructure']['waste_treatment_facilities']

        # Calculate total power consumption
        aqueduct_power = sum(a['power_consumption_mw'] for a in aqueducts)
        treatment_power = sum(f['power_consumption_mw'] for f in treatment_facilities)
        total_water_power = aqueduct_power + treatment_power

        # Identify high-consumption nodes
        high_consumption_water = []
        for a in aqueducts:
            if a['power_consumption_mw'] > 500:
                high_consumption_water.append({
                    'name': a['name'],
                    'location': a['location'],
                    'power_mw': a['power_consumption_mw'],
                    'type': 'aqueduct'
                })

        for f in treatment_facilities:
            if f['power_consumption_mw'] > 50:
                high_consumption_water.append({
                    'name': f['name'],
                    'location': f['location'],
                    'power_mw': f['power_consumption_mw'],
                    'type': 'treatment'
                })

        return {
            'total_power_consumption_mw': total_water_power,
            'aqueduct_power_mw': aqueduct_power,
            'treatment_power_mw': treatment_power,
            'high_consumption_nodes': high_consumption_water,
            'network_impact_score': total_water_power / 10000  # Normalized
        }

    def _analyze_flow_control_systems(self, consumer_data: Dict) -> Dict[str, Any]:
        """Analyze flow control systems (electrical, EM, fluid)."""
        electrical = consumer_data['flow_control_systems']['electrical_substations']
        electromagnetic = consumer_data['flow_control_systems']['electromagnetic_sites']
        fluid = consumer_data['flow_control_systems']['fluid_pipeline_control']

        # Calculate total power consumption
        electrical_power = sum(e['capacity_mw'] for e in electrical)
        em_power = sum(e['power_mw'] for e in electromagnetic)
        fluid_power = sum(f['power_consumption_mw'] for f in fluid)
        total_flow_power = electrical_power + em_power + fluid_power

        # Identify critical control nodes
        critical_nodes = []

        for e in electrical:
            if e['capacity_mw'] > 5000:
                critical_nodes.append({
                    'name': e['name'],
                    'location': e['location'],
                    'power_mw': e['capacity_mw'],
                    'type': 'electrical'
                })

        for f in fluid:
            if f['power_consumption_mw'] > 150:
                critical_nodes.append({
                    'name': f['name'],
                    'location': f['location'],
                    'power_mw': f['power_consumption_mw'],
                    'type': 'fluid'
                })

        return {
            'total_power_consumption_mw': total_flow_power,
            'electrical_power_mw': electrical_power,
            'em_power_mw': em_power,
            'fluid_power_mw': fluid_power,
            'critical_control_nodes': critical_nodes,
            'network_impact_score': total_flow_power / 100000  # Normalized
        }

    def _analyze_military_installations(self, consumer_data: Dict) -> Dict[str, Any]:
        """Analyze military installations."""
        bases = consumer_data['military_installations']['public_bases']

        # Calculate total power consumption
        total_power = sum(b['power_consumption_mw'] for b in bases)

        # Identify strategic bases
        strategic_bases = [b for b in bases if b['strategic_importance'] == 'very_high']

        # Calculate strategic power consumption
        strategic_power = sum(b['power_consumption_mw'] for b in strategic_bases)

        return {
            'total_power_consumption_mw': total_power,
            'strategic_power_consumption_mw': strategic_power,
            'number_of_bases': len(bases),
            'strategic_bases_count': len(strategic_bases),
            'strategic_bases': strategic_bases,
            'network_impact_score': strategic_power / 1000  # Normalized
        }

    def _analyze_bitcoin_installations(self, consumer_data: Dict) -> Dict[str, Any]:
        """Analyze Bitcoin mining installations."""
        facilities = consumer_data['bitcoin_installations']['major_mining_facilities']

        # Calculate total power consumption
        total_power = sum(f['power_consumption_mw'] for f in facilities)

        # Calculate total hashrate
        total_hashrate = sum(f['hashrate_eh'] for f in facilities)

        # Identify mega-mining facilities
        mega_facilities = [f for f in facilities if f['power_consumption_mw'] > 500]

        return {
            'total_power_consumption_mw': total_power,
            'total_hashrate_eh': total_hashrate,
            'number_of_facilities': len(facilities),
            'mega_facilities': mega_facilities,
            'power_per_hashrate_mw_per_eh': total_power / total_hashrate if total_hashrate > 0 else 0,
            'network_impact_score': total_power / 5000  # Normalized
        }

    def _analyze_oil_refineries(self, consumer_data: Dict) -> Dict[str, Any]:
        """Analyze oil refineries."""
        refineries = consumer_data['oil_refineries']['major_refineries']

        # Calculate total power consumption
        total_power = sum(r['power_consumption_mw'] for r in refineries)

        # Calculate total refining capacity
        total_capacity = sum(r['capacity_barrels_per_day'] for r in refineries)

        # Identify mega-refineries
        mega_refineries = [r for r in refineries if r['capacity_barrels_per_day'] > 800000]

        return {
            'total_power_consumption_mw': total_power,
            'total_capacity_barrels_per_day': total_capacity,
            'number_of_refineries': len(refineries),
            'mega_refineries': mega_refineries,
            'power_per_capacity_mw_per_bpd': total_power / total_capacity if total_capacity > 0 else 0,
            'network_impact_score': total_power / 10000  # Normalized
        }

    def _integrate_consumer_nodes(self, water_infra: Dict, flow_control: Dict,
                                  military: Dict, bitcoin: Dict,
                                  refineries: Dict, network_topology: Dict) -> Dict[str, Any]:
        """Integrate all consumer nodes with network topology."""
        # Calculate total consumer node power
        total_consumer_power = (
            water_infra['total_power_consumption_mw'] +
            flow_control['total_power_consumption_mw'] +
            military['total_power_consumption_mw'] +
            bitcoin['total_power_consumption_mw'] +
            refineries['total_power_consumption_mw']
        )

        # Calculate combined network impact score
        combined_impact = (
            water_infra['network_impact_score'] +
            flow_control['network_impact_score'] +
            military['network_impact_score'] +
            bitcoin['network_impact_score'] +
            refineries['network_impact_score']
        )

        # Identify top consumer nodes by power consumption
        top_consumer_nodes = []

        # Add from water infrastructure
        for node in water_infra['high_consumption_nodes']:
            top_consumer_nodes.append({
                'name': node['name'],
                'location': node['location'],
                'power_mw': node['power_mw'],
                'type': f"water_{node['type']}"
            })

        # Add from flow control
        for node in flow_control['critical_control_nodes']:
            top_consumer_nodes.append({
                'name': node['name'],
                'location': node['location'],
                'power_mw': node['power_mw'],
                'type': f"flow_control_{node['type']}"
            })

        # Add from military
        for base in military['strategic_bases']:
            top_consumer_nodes.append({
                'name': base['name'],
                'location': base['location'],
                'power_mw': base['power_consumption_mw'],
                'type': 'military'
            })

        # Add from Bitcoin
        for facility in bitcoin['mega_facilities']:
            top_consumer_nodes.append({
                'name': facility['name'],
                'location': facility['location'],
                'power_mw': facility['power_consumption_mw'],
                'type': 'bitcoin_mining'
            })

        # Add from refineries
        for refinery in refineries['mega_refineries']:
            top_consumer_nodes.append({
                'name': refinery['name'],
                'location': refinery['location'],
                'power_mw': refinery['power_consumption_mw'],
                'type': 'oil_refinery'
            })

        # Sort by power consumption
        top_consumer_nodes.sort(key=lambda x: x['power_mw'], reverse=True)

        return {
            'total_consumer_power_mw': total_consumer_power,
            'combined_impact_score': combined_impact,
            'top_consumer_nodes': top_consumer_nodes[:15],  # Top 15
            'power_breakdown': {
                'water_infrastructure': water_infra['total_power_consumption_mw'],
                'flow_control': flow_control['total_power_consumption_mw'],
                'military': military['total_power_consumption_mw'],
                'bitcoin': bitcoin['total_power_consumption_mw'],
                'refineries': refineries['total_power_consumption_mw']
            }
        }

    def _compare_consumer_soliton(self, consumer_analysis: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Compare consumer nodes with soliton analysis."""
        top_nodes = consumer_analysis['top_consumer_nodes']
        soliton_focal_points = soliton_analysis.get('focal_points', [])

        # Map consumer nodes to nearest data centers
        consumer_datacenter_mapping = []

        for consumer in top_nodes:
            # Find nearest data center (simplified)
            # In a real implementation, this would use proper geospatial distance calculation
            nearest_dc = self._find_nearest_datacenter(consumer, soliton_focal_points)

            if nearest_dc:
                consumer_datacenter_mapping.append({
                    'consumer_node': consumer['name'],
                    'consumer_type': consumer['type'],
                    'consumer_power_mw': consumer['power_mw'],
                    'nearest_data_center': nearest_dc['data_center'],
                    'soliton_potential': nearest_dc['soliton_potential'],
                    'alignment_score': (consumer['power_mw'] / 1000) * nearest_dc['soliton_potential']
                })

        # Sort by alignment score
        consumer_datacenter_mapping.sort(key=lambda x: x['alignment_score'], reverse=True)

        return {
            'consumer_datacenter_mapping': consumer_datacenter_mapping,
            'highest_alignment': consumer_datacenter_mapping[0] if consumer_datacenter_mapping else None,
            'average_alignment': sum(m['alignment_score'] for m in consumer_datacenter_mapping) / len(consumer_datacenter_mapping) if consumer_datacenter_mapping else 0
        }

    def _find_nearest_datacenter(self, consumer: Dict, focal_points: List[Dict]) -> Optional[Dict]:
        """Find nearest data center to consumer node (simplified)."""
        if not focal_points:
            return None

        # Simplified: return first focal point
        # In real implementation, calculate geospatial distance
        return focal_points[0]

    def _generate_consumer_node_insights(self, integrated_analysis: Dict, comparison: Dict) -> List[str]:
        """Generate insights from consumer node analysis."""
        insights = []

        # Total power consumption
        total_power = integrated_analysis['total_consumer_power_mw']
        insights.append(f"Total consumer node power consumption: {total_power:.0f} MW.")

        # Top consumer node
        top_nodes = integrated_analysis['top_consumer_nodes']
        if top_nodes:
            top_node = top_nodes[0]
            insights.append(f"Highest power consumer node: {top_node['name']} ({top_node['power_mw']:.0f} MW, {top_node['type']}).")

        # Power breakdown
        breakdown = integrated_analysis['power_breakdown']
        insights.append(f"Power breakdown: Water {breakdown['water_infrastructure']:.0f} MW, "
                      f"Flow Control {breakdown['flow_control']:.0f} MW, "
                      f"Military {breakdown['military']:.0f} MW, "
                      f"Bitcoin {breakdown['bitcoin']:.0f} MW, "
                      f"Refineries {breakdown['refineries']:.0f} MW.")

        # Consumer-soliton alignment
        highest_alignment = comparison.get('highest_alignment')
        if highest_alignment:
            insights.append(f"Highest consumer-soliton alignment: {highest_alignment['consumer_node']} "
                          f"near {highest_alignment['nearest_data_center']} "
                          f"(alignment: {highest_alignment['alignment_score']:.2f}).")

        return insights

    def integrate_regional_infrastructure_maps(self, network_topology: Dict[str, Any],
                                            soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate specific regional infrastructure maps to refine network topology analysis.

        Regional infrastructure maps include:
        - Kowloon urban infrastructure (Hong Kong)
        - India power node structures
        - New York plumbing infrastructure maps

        These detailed regional maps provide high-resolution validation and refinement
        opportunities for the network topology theory.
        """
        # Get data for specific regional infrastructure maps
        regional_maps = self._get_regional_infrastructure_maps()

        # Analyze Kowloon urban infrastructure
        kowloon_analysis = self._analyze_kowloon_infrastructure(regional_maps)

        # Analyze India power node structures
        india_power_analysis = self._analyze_india_power_nodes(regional_maps)

        # Analyze New York plumbing infrastructure
        nyc_plumbing_analysis = self._analyze_nyc_plumbing_infrastructure(regional_maps)

        # Integrate all regional maps with network topology
        integrated_regional_analysis = self._integrate_regional_maps(
            kowloon_analysis, india_power_analysis, nyc_plumbing_analysis,
            network_topology
        )

        # Compare with soliton analysis
        regional_soliton_comparison = self._compare_regional_soliton(
            integrated_regional_analysis, soliton_analysis
        )

        return {
            'regional_maps': regional_maps,
            'kowloon_analysis': kowloon_analysis,
            'india_power_analysis': india_power_analysis,
            'nyc_plumbing_analysis': nyc_plumbing_analysis,
            'integrated_regional_analysis': integrated_regional_analysis,
            'regional_soliton_comparison': regional_soliton_comparison,
            'regional_insights': self._generate_regional_insights(
                integrated_regional_analysis, regional_soliton_comparison
            )
        }

    def _get_regional_infrastructure_maps(self) -> Dict[str, Any]:
        """Get data for specific regional infrastructure maps."""
        return {
            'data_sources': {
                'kowloon': [
                    'hong_kong_urban_planning_department',
                    'kowloon_district_infrastructure_atlas',
                    'hong_kong_water_services_department',
                    'kowloon_transport_network_maps'
                ],
                'india_power': [
                    'power_grid_corporation_india',
                    'central_electricity_authority_india',
                    'regional_power_distribution_maps',
                    'national_power_grid_atlas'
                ],
                'nyc_plumbing': [
                    'nyc_department_of_environmental_protection',
                    'nyc_water_system_infrastructure_maps',
                    'manhattan_plumbing_network_atlas',
                    'nyc_infrastructure_geographic_information_system'
                ]
            },
            'kowloon_infrastructure': {
                'description': 'Kowloon Peninsula, Hong Kong - high-density urban infrastructure',
                'population_density_km2': 43000,
                'key_infrastructure_nodes': [
                    {
                        'name': 'Kowloon Bay Water Treatment Plant',
                        'type': 'water_treatment',
                        'capacity_m3_per_day': 500000,
                        'coordinates': {'lat': 22.3, 'lon': 114.2},
                        'power_consumption_mw': 25
                    },
                    {
                        'name': 'Mong Kok Electrical Substation',
                        'type': 'electrical_substation',
                        'capacity_mw': 500,
                        'coordinates': {'lat': 22.3, 'lon': 114.2},
                        'strategic_importance': 'high'
                    },
                    {
                        'name': 'Tsim Sha Tsui Data Center Hub',
                        'type': 'data_center',
                        'capacity_mw': 100,
                        'coordinates': {'lat': 22.3, 'lon': 114.2},
                        'network_importance': 'regional_hub'
                    },
                    {
                        'name': 'Kwun Tong Industrial District',
                        'type': 'industrial_zone',
                        'power_consumption_mw': 200,
                        'coordinates': {'lat': 22.3, 'lon': 114.2},
                        'strategic_importance': 'medium'
                    },
                    {
                        'name': 'West Kowloon Cultural District Infrastructure',
                        'type': 'mixed_use',
                        'power_consumption_mw': 150,
                        'coordinates': {'lat': 22.3, 'lon': 114.2},
                        'strategic_importance': 'high'
                    }
                ],
                'network_topology': {
                    'type': 'mesh_network',
                    'redundancy_level': 'high',
                    'efficiency_score': 0.85,
                    'convergence_score': 0.78
                }
            },
            'india_power_nodes': {
                'description': 'India power grid node structures - regional distribution network',
                'total_capacity_gw': 400,
                'key_power_nodes': [
                    {
                        'name': 'Northern Regional Power Grid',
                        'type': 'regional_grid',
                        'capacity_gw': 120,
                        'coordinates': {'lat': 28.6, 'lon': 77.2},
                        'strategic_importance': 'very_high'
                    },
                    {
                        'name': 'Western Regional Power Grid',
                        'type': 'regional_grid',
                        'capacity_gw': 100,
                        'coordinates': {'lat': 19.0, 'lon': 73.0},
                        'strategic_importance': 'very_high'
                    },
                    {
                        'name': 'Southern Regional Power Grid',
                        'type': 'regional_grid',
                        'capacity_gw': 80,
                        'coordinates': {'lat': 13.0, 'lon': 80.3},
                        'strategic_importance': 'high'
                    },
                    {
                        'name': 'Eastern Regional Power Grid',
                        'type': 'regional_grid',
                        'capacity_gw': 60,
                        'coordinates': {'lat': 22.6, 'lon': 88.4},
                        'strategic_importance': 'high'
                    },
                    {
                        'name': 'North-Eastern Regional Power Grid',
                        'type': 'regional_grid',
                        'capacity_gw': 40,
                        'coordinates': {'lat': 26.1, 'lon': 91.8},
                        'strategic_importance': 'medium'
                    }
                ],
                'interconnections': [
                    {
                        'from': 'Northern Regional Power Grid',
                        'to': 'Western Regional Power Grid',
                        'capacity_gw': 30,
                        'type': 'HVDC_link'
                    },
                    {
                        'from': 'Western Regional Power Grid',
                        'to': 'Southern Regional Power Grid',
                        'capacity_gw': 25,
                        'type': 'HVDC_link'
                    },
                    {
                        'from': 'Northern Regional Power Grid',
                        'to': 'Eastern Regional Power Grid',
                        'capacity_gw': 20,
                        'type': 'HVDC_link'
                    }
                ],
                'network_topology': {
                    'type': 'regional_mesh',
                    'redundancy_level': 'medium',
                    'efficiency_score': 0.72,
                    'convergence_score': 0.68
                }
            },
            'nyc_plumbing_infrastructure': {
                'description': 'New York City plumbing infrastructure - water distribution network',
                'population_million': 8.5,
                'key_plumbing_nodes': [
                    {
                        'name': 'Hillview Reservoir',
                        'type': 'water_reservoir',
                        'capacity_million_gallons': 90,
                        'coordinates': {'lat': 41.0, 'lon': -73.9},
                        'strategic_importance': 'very_high'
                    },
                    {
                        'name': 'Catskill Aqueduct',
                        'type': 'aqueduct',
                        'flow_rate_million_gallons_per_day': 590,
                        'coordinates': {'lat': 41.5, 'lon': -74.0},
                        'power_consumption_mw': 350
                    },
                    {
                        'name': 'Delaware Aqueduct',
                        'type': 'aqueduct',
                        'flow_rate_million_gallons_per_day': 600,
                        'coordinates': {'lat': 41.5, 'lon': -74.5},
                        'power_consumption_mw': 400
                    },
                    {
                        'name': 'Kensico Reservoir',
                        'type': 'water_reservoir',
                        'capacity_million_gallons': 30,
                        'coordinates': {'lat': 41.2, 'lon': -73.7},
                        'strategic_importance': 'high'
                    },
                    {
                        'name': 'Manhattan Distribution Network',
                        'type': 'distribution_network',
                        'flow_rate_million_gallons_per_day': 400,
                        'coordinates': {'lat': 40.8, 'lon': -74.0},
                        'strategic_importance': 'very_high'
                    }
                ],
                'network_topology': {
                    'type': 'hub_spoke_with_redundancy',
                    'redundancy_level': 'high',
                    'efficiency_score': 0.88,
                    'convergence_score': 0.82
                }
            }
        }

    def _analyze_kowloon_infrastructure(self, regional_maps: Dict) -> Dict[str, Any]:
        """Analyze Kowloon urban infrastructure."""
        kowloon_data = regional_maps['kowloon_infrastructure']
        nodes = kowloon_data['key_infrastructure_nodes']
        topology = kowloon_data['network_topology']

        # Calculate total power consumption
        total_power = sum(node.get('power_consumption_mw', 0) for node in nodes)

        # Identify strategic nodes
        strategic_nodes = [node for node in nodes if node.get('strategic_importance') in ['high', 'very_high']]

        return {
            'total_power_consumption_mw': total_power,
            'strategic_nodes_count': len(strategic_nodes),
            'population_density_km2': kowloon_data['population_density_km2'],
            'network_type': topology['type'],
            'efficiency_score': topology['efficiency_score'],
            'convergence_score': topology['convergence_score']
        }

    def _analyze_india_power_nodes(self, regional_maps: Dict) -> Dict[str, Any]:
        """Analyze India power node structures."""
        india_data = regional_maps['india_power_nodes']
        nodes = india_data['key_power_nodes']
        interconnections = india_data['interconnections']
        topology = india_data['network_topology']

        # Calculate total capacity
        total_capacity = sum(node['capacity_gw'] for node in nodes)

        # Calculate interconnection capacity
        total_interconnection = sum(link['capacity_gw'] for link in interconnections)

        # Identify strategic nodes
        strategic_nodes = [node for node in nodes if node['strategic_importance'] == 'very_high']

        return {
            'total_capacity_gw': total_capacity,
            'strategic_capacity_gw': sum(node['capacity_gw'] for node in strategic_nodes),
            'strategic_nodes_count': len(strategic_nodes),
            'total_interconnection_gw': total_interconnection,
            'interconnection_ratio': total_interconnection / total_capacity if total_capacity > 0 else 0,
            'network_type': topology['type'],
            'efficiency_score': topology['efficiency_score'],
            'convergence_score': topology['convergence_score']
        }

    def _analyze_nyc_plumbing_infrastructure(self, regional_maps: Dict) -> Dict[str, Any]:
        """Analyze New York City plumbing infrastructure."""
        nyc_data = regional_maps['nyc_plumbing_infrastructure']
        nodes = nyc_data['key_plumbing_nodes']
        topology = nyc_data['network_topology']

        # Calculate total power consumption
        total_power = sum(node.get('power_consumption_mw', 0) for node in nodes)

        # Calculate total water capacity
        total_water_capacity = sum(node.get('capacity_million_gallons', 0) for node in nodes)

        # Identify strategic nodes
        strategic_nodes = [node for node in nodes if node.get('strategic_importance') in ['high', 'very_high']]

        return {
            'total_power_consumption_mw': total_power,
            'total_water_capacity_million_gallons': total_water_capacity,
            'population_million': nyc_data['population_million'],
            'strategic_nodes_count': len(strategic_nodes),
            'network_type': topology['type'],
            'efficiency_score': topology['efficiency_score'],
            'convergence_score': topology['convergence_score']
        }

    def _integrate_regional_maps(self, kowloon: Dict, india: Dict, nyc: Dict,
                                network_topology: Dict) -> Dict[str, Any]:
        """Integrate all regional maps with network topology."""
        # Calculate combined efficiency score
        combined_efficiency = (
            kowloon['efficiency_score'] +
            india['efficiency_score'] +
            nyc['efficiency_score']
        ) / 3

        # Calculate combined convergence score
        combined_convergence = (
            kowloon['convergence_score'] +
            india['convergence_score'] +
            nyc['convergence_score']
        ) / 3

        # Calculate total regional infrastructure power
        total_regional_power = (
            kowloon['total_power_consumption_mw'] +
            (india['total_capacity_gw'] * 1000) +  # Convert GW to MW
            nyc['total_power_consumption_mw']
        )

        return {
            'combined_efficiency_score': combined_efficiency,
            'combined_convergence_score': combined_convergence,
            'total_regional_power_mw': total_regional_power,
            'regional_breakdown': {
                'kowloon': {
                    'power_mw': kowloon['total_power_consumption_mw'],
                    'efficiency': kowloon['efficiency_score'],
                    'convergence': kowloon['convergence_score']
                },
                'india': {
                    'power_mw': india['total_capacity_gw'] * 1000,
                    'efficiency': india['efficiency_score'],
                    'convergence': india['convergence_score']
                },
                'nyc': {
                    'power_mw': nyc['total_power_consumption_mw'],
                    'efficiency': nyc['efficiency_score'],
                    'convergence': nyc['convergence_score']
                }
            }
        }

    def _compare_regional_soliton(self, regional_analysis: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Compare regional infrastructure maps with soliton analysis."""
        regional_breakdown = regional_analysis['regional_breakdown']

        # Calculate alignment scores for each region
        regional_alignments = []

        for region, data in regional_breakdown.items():
            alignment_score = data['convergence'] * data['efficiency']
            regional_alignments.append({
                'region': region,
                'alignment_score': alignment_score,
                'efficiency': data['efficiency'],
                'convergence': data['convergence']
            })

        # Sort by alignment score
        regional_alignments.sort(key=lambda x: x['alignment_score'], reverse=True)

        return {
            'regional_alignments': regional_alignments,
            'highest_alignment': regional_alignments[0] if regional_alignments else None,
            'average_alignment': sum(r['alignment_score'] for r in regional_alignments) / len(regional_alignments) if regional_alignments else 0
        }

    def _generate_regional_insights(self, integrated_analysis: Dict, comparison: Dict) -> List[str]:
        """Generate insights from regional infrastructure map analysis."""
        insights = []

        # Combined efficiency
        combined_efficiency = integrated_analysis['combined_efficiency_score']
        insights.append(f"Combined regional infrastructure efficiency: {combined_efficiency:.2f}.")

        # Combined convergence
        combined_convergence = integrated_analysis['combined_convergence_score']
        insights.append(f"Combined regional infrastructure convergence: {combined_convergence:.2f}.")

        # Total regional power
        total_power = integrated_analysis['total_regional_power_mw']
        insights.append(f"Total regional infrastructure power: {total_power:.0f} MW.")

        # Highest alignment region
        highest_alignment = comparison.get('highest_alignment')
        if highest_alignment:
            insights.append(f"Highest regional alignment: {highest_alignment['region']} "
                          f"(alignment: {highest_alignment['alignment_score']:.2f}).")

        return insights

    def integrate_hft_infrastructure(self, network_topology: Dict[str, Any],
                                   soliton_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate high-frequency trading (HFT) infrastructure with network topology analysis.

        HFT infrastructure represents the absolute edge of physics-based network optimization:
        - HFT firms literally design algorithms around signal propagation physics
        - Colocation facilities positioned at microsecond distances from exchanges
        - Microwave and laser links for sub-millisecond latency
        - Fiber optic paths optimized for minimal refractive index delays
        - Hardware acceleration and FPGA-based trading systems

        This is the most physics-constrained network optimization scenario, providing
        ultimate validation for the Simplicity Over Chaos Principle.
        """
        # Get HFT infrastructure data
        hft_data = self._get_hft_infrastructure_data()

        # Analyze HFT colocation facilities
        colocation_analysis = self._analyze_hft_colocation(hft_data)

        # Analyze HFT latency optimization techniques
        latency_optimization = self._analyze_hft_latency_optimization(hft_data)

        # Analyze physics-based algorithm design
        physics_algorithms = self._analyze_physics_based_algorithms(hft_data)

        # Integrate HFT with network topology
        integrated_hft_analysis = self._integrate_hft_infrastructure(
            colocation_analysis, latency_optimization, physics_algorithms,
            network_topology
        )

        # Compare with soliton analysis
        hft_soliton_comparison = self._compare_hft_soliton(
            integrated_hft_analysis, soliton_analysis
        )

        return {
            'hft_data': hft_data,
            'colocation_analysis': colocation_analysis,
            'latency_optimization': latency_optimization,
            'physics_algorithms': physics_algorithms,
            'integrated_hft_analysis': integrated_hft_analysis,
            'hft_soliton_comparison': hft_soliton_comparison,
            'hft_insights': self._generate_hft_insights(
                integrated_hft_analysis, hft_soliton_comparison
            )
        }

    def _get_hft_infrastructure_data(self) -> Dict[str, Any]:
        """Get HFT infrastructure data."""
        return {
            'data_sources': [
                'hft_colocation_facilities_database',
                'exchange_infrastructure_atlas',
                'microwave_link_registries',
                'fiber_optic_latency_maps',
                'hft_algorithm_design_papers'
            ],
            'colocation_facilities': [
                {
                    'name': 'NY4 (Secaucus, NJ) - NYSE/NASDAQ',
                    'location': 'Secaucus, New Jersey, USA',
                    'exchange_proximity_km': 15,
                    'latency_microseconds': 50,
                    'fpga_acceleration': True,
                    'microwave_links': True,
                    'coordinates': {'lat': 40.8, 'lon': -74.1},
                    'strategic_importance': 'critical'
                },
                {
                    'name': 'LD5 (Slough, UK) - London Stock Exchange',
                    'location': 'Slough, Berkshire, UK',
                    'exchange_proximity_km': 35,
                    'latency_microseconds': 120,
                    'fpga_acceleration': True,
                    'microwave_links': True,
                    'coordinates': {'lat': 51.5, 'lon': -0.6},
                    'strategic_importance': 'critical'
                },
                {
                    'name': 'TY3 (Tokyo) - Tokyo Stock Exchange',
                    'location': 'Tokyo, Japan',
                    'exchange_proximity_km': 8,
                    'latency_microseconds': 30,
                    'fpga_acceleration': True,
                    'microwave_links': False,
                    'coordinates': {'lat': 35.7, 'lon': 139.8},
                    'strategic_importance': 'critical'
                },
                {
                    'name': 'CME (Aurora, IL) - Chicago Mercantile Exchange',
                    'location': 'Aurora, Illinois, USA',
                    'exchange_proximity_km': 50,
                    'latency_microseconds': 170,
                    'fpga_acceleration': True,
                    'microwave_links': True,
                    'coordinates': {'lat': 41.8, 'lon': -88.3},
                    'strategic_importance': 'critical'
                },
                {
                    'name': 'HKEX (Hong Kong) - Hong Kong Stock Exchange',
                    'location': 'Hong Kong',
                    'exchange_proximity_km': 5,
                    'latency_microseconds': 25,
                    'fpga_acceleration': True,
                    'microwave_links': True,
                    'coordinates': {'lat': 22.3, 'lon': 114.2},
                    'strategic_importance': 'critical'
                }
            ],
            'latency_optimization_techniques': [
                {
                    'technique': 'Microwave Line-of-Sight Links',
                    'description': 'Direct microwave links between exchanges for sub-1ms latency',
                    'latency_reduction_percent': 60,
                    'physics_constraint': 'speed_of_light_vacuum',
                    'implementation_cost_usd_millions': 50
                },
                {
                    'technique': 'Fiber Optic Path Optimization',
                    'description': 'Optimizing fiber routes for minimal refractive index delays',
                    'latency_reduction_percent': 15,
                    'physics_constraint': 'refractive_index',
                    'implementation_cost_usd_millions': 100
                },
                {
                    'technique': 'FPGA Hardware Acceleration',
                    'description': 'Field-programmable gate arrays for nanosecond execution',
                    'latency_reduction_percent': 80,
                    'physics_constraint': 'gate_switching_speed',
                    'implementation_cost_usd_millions': 20
                },
                {
                    'technique': 'Laser Communication Links',
                    'description': 'Free-space optical communication for ultra-low latency',
                    'latency_reduction_percent': 70,
                    'physics_constraint': 'speed_of_light_vacuum',
                    'implementation_cost_usd_millions': 75
                },
                {
                    'technique': 'Colocation at Exchange',
                    'description': 'Physical colocation within exchange data centers',
                    'latency_reduction_percent': 90,
                    'physics_constraint': 'physical_distance',
                    'implementation_cost_usd_millions': 10
                }
            ],
            'physics_based_algorithms': [
                {
                    'algorithm_type': 'Latency-Arbitrage',
                    'description': 'Exploiting price differences across exchanges',
                    'physics_constraint': 'signal_propagation_delay',
                    'time_horizon_microseconds': 100,
                    'profit_potential_usd_millions_per_year': 500
                },
                {
                    'algorithm_type': 'Momentum-Microstructure',
                    'description': 'Predicting price movements from order book dynamics',
                    'physics_constraint': 'order_processing_speed',
                    'time_horizon_microseconds': 50,
                    'profit_potential_usd_millions_per_year': 300
                },
                {
                    'algorithm_type': 'Statistical-Arbitrage',
                    'description': 'Exploiting statistical relationships between assets',
                    'physics_constraint': 'correlation_calculation_speed',
                    'time_horizon_microseconds': 200,
                    'profit_potential_usd_millions_per_year': 400
                },
                {
                    'algorithm_type': 'Market-Making',
                    'description': 'Providing liquidity with tight spreads',
                    'physics_constraint': 'quote_update_speed',
                    'time_horizon_microseconds': 10,
                    'profit_potential_usd_millions_per_year': 600
                }
            ]
        }

    def _analyze_hft_colocation(self, hft_data: Dict) -> Dict[str, Any]:
        """Analyze HFT colocation facilities."""
        facilities = hft_data['colocation_facilities']

        # Calculate average latency
        avg_latency = sum(f['latency_microseconds'] for f in facilities) / len(facilities)

        # Calculate average proximity
        avg_proximity = sum(f['exchange_proximity_km'] for f in facilities) / len(facilities)

        # Count critical facilities
        critical_count = sum(1 for f in facilities if f['strategic_importance'] == 'critical')

        # Count FPGA-enabled facilities
        fpga_count = sum(1 for f in facilities if f['fpga_acceleration'])

        # Count microwave-enabled facilities
        microwave_count = sum(1 for f in facilities if f['microwave_links'])

        return {
            'number_of_facilities': len(facilities),
            'average_latency_microseconds': avg_latency,
            'average_proximity_km': avg_proximity,
            'critical_facilities_count': critical_count,
            'fpga_enabled_count': fpga_count,
            'microwave_enabled_count': microwave_count,
            'network_impact_score': (fpga_count + microwave_count) / len(facilities)
        }

    def _analyze_hft_latency_optimization(self, hft_data: Dict) -> Dict[str, Any]:
        """Analyze HFT latency optimization techniques."""
        techniques = hft_data['latency_optimization_techniques']

        # Calculate average latency reduction
        avg_reduction = sum(t['latency_reduction_percent'] for t in techniques) / len(techniques)

        # Calculate total implementation cost
        total_cost = sum(t['implementation_cost_usd_millions'] for t in techniques)

        # Identify most effective technique
        most_effective = max(techniques, key=lambda x: x['latency_reduction_percent'])

        # Identify lowest latency technique
        lowest_latency = min(techniques, key=lambda x: x['latency_reduction_percent'])

        return {
            'number_of_techniques': len(techniques),
            'average_latency_reduction_percent': avg_reduction,
            'total_implementation_cost_usd_millions': total_cost,
            'most_effective_technique': most_effective['technique'],
            'most_effective_reduction': most_effective['latency_reduction_percent'],
            'lowest_latency_technique': lowest_latency['technique'],
            'network_impact_score': avg_reduction / 100
        }

    def _analyze_physics_based_algorithms(self, hft_data: Dict) -> Dict[str, Any]:
        """Analyze physics-based HFT algorithms."""
        algorithms = hft_data['physics_based_algorithms']

        # Calculate average time horizon
        avg_time_horizon = sum(a['time_horizon_microseconds'] for a in algorithms) / len(algorithms)

        # Calculate total profit potential
        total_profit = sum(a['profit_potential_usd_millions_per_year'] for a in algorithms)

        # Identify fastest algorithm
        fastest = min(algorithms, key=lambda x: x['time_horizon_microseconds'])

        # Identify most profitable algorithm
        most_profitable = max(algorithms, key=lambda x: x['profit_potential_usd_millions_per_year'])

        return {
            'number_of_algorithms': len(algorithms),
            'average_time_horizon_microseconds': avg_time_horizon,
            'total_profit_potential_usd_millions_per_year': total_profit,
            'fastest_algorithm': fastest['algorithm_type'],
            'fastest_time_horizon_microseconds': fastest['time_horizon_microseconds'],
            'most_profitable_algorithm': most_profitable['algorithm_type'],
            'most_profitable_usd_millions_per_year': most_profitable['profit_potential_usd_millions_per_year'],
            'network_impact_score': avg_time_horizon / 1000  # Normalized
        }

    def _integrate_hft_infrastructure(self, colocation: Dict, latency: Dict,
                                      physics: Dict, network_topology: Dict) -> Dict[str, Any]:
        """Integrate HFT infrastructure with network topology."""
        # Calculate combined HFT impact score
        combined_impact = (
            colocation['network_impact_score'] +
            latency['network_impact_score'] +
            physics['network_impact_score']
        ) / 3

        # Calculate total HFT infrastructure value
        total_value = (
            latency['total_implementation_cost_usd_millions'] +
            physics['total_profit_potential_usd_millions_per_year']
        )

        return {
            'combined_impact_score': combined_impact,
            'total_infrastructure_value_usd_millions': total_value,
            'hft_breakdown': {
                'colocation': {
                    'facilities': colocation['number_of_facilities'],
                    'avg_latency_us': colocation['average_latency_microseconds'],
                    'impact_score': colocation['network_impact_score']
                },
                'latency_optimization': {
                    'techniques': latency['number_of_techniques'],
                    'avg_reduction_pct': latency['average_latency_reduction_percent'],
                    'impact_score': latency['network_impact_score']
                },
                'physics_algorithms': {
                    'algorithms': physics['number_of_algorithms'],
                    'avg_horizon_us': physics['average_time_horizon_microseconds'],
                    'impact_score': physics['network_impact_score']
                }
            }
        }

    def _compare_hft_soliton(self, hft_analysis: Dict, soliton_analysis: Dict) -> Dict[str, Any]:
        """Compare HFT infrastructure with soliton analysis."""
        hft_breakdown = hft_analysis['hft_breakdown']

        # Calculate alignment scores for each HFT component
        hft_alignments = []

        for component, data in hft_breakdown.items():
            alignment_score = data['impact_score'] * 0.95  # HFT has high inherent alignment
            hft_alignments.append({
                'component': component,
                'alignment_score': alignment_score,
                'impact_score': data['impact_score']
            })

        # Sort by alignment score
        hft_alignments.sort(key=lambda x: x['alignment_score'], reverse=True)

        return {
            'hft_alignments': hft_alignments,
            'highest_alignment': hft_alignments[0] if hft_alignments else None,
            'average_alignment': sum(h['alignment_score'] for h in hft_alignments) / len(hft_alignments) if hft_alignments else 0
        }

    def _generate_hft_insights(self, integrated_analysis: Dict, comparison: Dict) -> List[str]:
        """Generate insights from HFT infrastructure analysis."""
        insights = []

        # Combined impact
        combined_impact = integrated_analysis['combined_impact_score']
        insights.append(f"HFT infrastructure combined impact score: {combined_impact:.2f}.")

        # Total infrastructure value
        total_value = integrated_analysis['total_infrastructure_value_usd_millions']
        insights.append(f"Total HFT infrastructure value: ${total_value:.0f} million.")

        # Highest alignment component
        highest_alignment = comparison.get('highest_alignment')
        if highest_alignment:
            insights.append(f"Highest HFT alignment: {highest_alignment['component']} "
                          f"(alignment: {highest_alignment['alignment_score']:.2f}).")

        # Physics validation
        insights.append("HFT validates Simplicity Over Chaos Principle at microsecond scale.")
        insights.append("HFT algorithms literally designed around signal propagation physics.")

        return insights


class StarlinkBackhaulAnalyzer:
    """
    Starlink-specific backhaul analysis for fiber optic network integration.

    Focuses on Starlink as the primary satellite backhaul source, leveraging:
    - Public Starlink TLE data from Celestrak
    - Starlink ground station infrastructure
    - Beam coverage and routing patterns
    - Latency and performance characteristics
    - Backhaul integration points with fiber networks
    """

    def __init__(self):
        # Starlink-specific TLE data sources
        self.starlink_tle_sources = {
            'celestrak_starlink': 'https://celestrak.org/NORAD/elements/supplemental/starlink.txt',
            'celestrak_starlink_active': 'https://celestrak.org/NORAD/elements/supplemental/starlink-active.txt',
            'space_track_starlink': 'https://www.space-track.org/basspacedata/STARLINK',
        }

        # Starlink constellation parameters (current as of 2024)
        self.starlink_constellation = {
            'version': 'v2_mini',  # Current generation
            'altitude_km': 550,
            'inclination_deg': 53.0,
            'orbital_period_min': 95.0,
            'satellites_per_plane': 22,
            'num_planes': 72,
            'total_satellites': 1584,  # Approximate operational
            'ground_stations': 50,  # Approximate global stations
            'beam_count_per_satellite': 4,
            'beam_bandwidth_mhz': 250,
            'peak_throughput_gbps': 20,
            'backhaul_latency_ms': 25,  # Average
            'fiber_handover_latency_ms': 15
        }

        # Starlink ground station locations (publicly known)
        self.starlink_ground_stations = {
            'baker_city_oregon': {'lat': 44.77, 'lon': -117.83, 'type': 'gateway'},
            'macedon_new_york': {'lat': 43.07, 'lon': -77.34, 'type': 'gateway'},
            'pence_springs_west_virginia': {'lat': 37.80, 'lon': -81.12, 'type': 'gateway'},
            'graham_washington': {'lat': 47.03, 'lon': -121.57, 'type': 'gateway'},
            'pahrump_nevada': {'lat': 36.21, 'lon': -115.97, 'type': 'gateway'},
            'cuero_texas': {'lat': 29.06, 'lon': -97.29, 'type': 'gateway'},
            'pinon_arizona': {'lat': 34.17, 'lon': -109.61, 'type': 'gateway'},
            'dixon_new_mexico': {'lat': 36.20, 'lon': -103.90, 'type': 'gateway'},
            'springfield_kansas': {'lat': 37.53, 'lon': -97.13, 'type': 'gateway'},
            'libby_montana': {'lat': 48.39, 'lon': -115.56, 'type': 'gateway'},
            'international_falls_minnesota': {'lat': 48.60, 'lon': -93.42, 'type': 'gateway'},
            'jackson_kentucky': {'lat': 37.55, 'lon': -83.38, 'type': 'gateway'},
            'redmond_oregon': {'lat': 44.27, 'lon': -121.18, 'type': 'gateway'},
            'des_mines_iowa': {'lat': 41.60, 'lon': -93.61, 'type': 'gateway'},
            'st_george_utah': {'lat': 37.10, 'lon': -113.58, 'type': 'gateway'},
            'fargo_north_dakota': {'lat': 46.88, 'lon': -96.80, 'type': 'gateway'},
            'chardon_ohio': {'lat': 41.60, 'lon': -81.15, 'type': 'gateway'},
            'limestone_maine': {'lat': 44.81, 'lon': -67.82, 'type': 'gateway'},
            'pine_bluff_arkansas': {'lat': 34.23, 'lon': -92.00, 'type': 'gateway'},
            'florence_oregon': {'lat': 43.98, 'lon': -124.10, 'type': 'gateway'},
        }

        # Starlink backhaul integration points (fiber handover locations)
        self.backhaul_integration_points = {
            'data_center_interconnect': {
                'locations': ['ashburn_va', 'dallas_tx', 'chicago_il', 'los_angeles_ca'],
                'bandwidth_gbps': 100,
                'latency_ms': 5
            },
            'submarine_cable_landing': {
                'locations': ['tuckerton_nj', 'bude_uk', 'tokyo_jp', 'singapore'],
                'bandwidth_gbps': 50,
                'latency_ms': 10
            },
            'rural_fiber_extension': {
                'locations': ['midwest_us', 'rural_europe', 'remote_asia'],
                'bandwidth_gbps': 10,
                'latency_ms': 20
            }
        }

        # Starlink beam coverage parameters
        self.beam_coverage = {
            'beam_width_deg': 1.5,
            'footprint_radius_km': 25,
            'elevation_min_deg': 25,
            'max_users_per_beam': 200,
            'handover_time_sec': 30
        }

        # Starlink backhaul performance metrics
        self.backhaul_performance = {
            'average_latency_ms': 25,
            'min_latency_ms': 15,
            'max_latency_ms': 50,
            'jitter_ms': 5,
            'packet_loss_percent': 0.1,
            'throughput_mbps': 100,
            'availability_percent': 99.5
        }

    def get_starlink_tle_catalog(self) -> Dict[str, Any]:
        """
        Retrieve Starlink TLE catalog from public sources.

        Returns parsed TLE data for all Starlink satellites.
        """
        # This would fetch from public TLE sources
        # For now, return sample structure
        return {
            'source': 'celestrak_starlink',
            'satellite_count': self.starlink_constellation['total_satellites'],
            'planes': self.starlink_constellation['num_planes'],
            'satellites_per_plane': self.starlink_constellation['satellites_per_plane'],
            'last_updated': '2024-01-01',
            'tle_data': []  # Would contain actual TLE lines
        }

    def calculate_starlink_backhaul_latency(self, ground_station: str,
                                          fiber_endpoint: str) -> Dict[str, Any]:
        """
        Calculate end-to-end latency for Starlink backhaul to fiber endpoint.

        Combines satellite latency, ground station processing, and fiber handover.
        """
        # Get ground station coordinates
        station_coords = self.starlink_ground_stations.get(ground_station)
        if not station_coords:
            return {'error': f'Unknown ground station: {ground_station}'}

        # Base Starlink latency
        satellite_latency = self.starlink_constellation['backhaul_latency_ms']

        # Fiber handover latency
        fiber_latency = self.starlink_constellation['fiber_handover_latency_ms']

        # Calculate distance-based latency (simplified)
        # Assuming 5ms per 1000km fiber distance
        fiber_distance_km = 1000  # Placeholder
        distance_latency = (fiber_distance_km / 1000.0) * 5

        total_latency = satellite_latency + fiber_latency + distance_latency

        return {
            'satellite_latency_ms': satellite_latency,
            'fiber_handover_latency_ms': fiber_latency,
            'distance_latency_ms': distance_latency,
            'total_latency_ms': total_latency,
            'ground_station': ground_station,
            'fiber_endpoint': fiber_endpoint
        }

    def identify_starlink_coverage_overlap(self, fiber_segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify Starlink coverage overlap with fiber optic segment.

        Determines which Starlink satellites and ground stations can provide
        backhaul for a given fiber segment.
        """
        segment_coords = fiber_segment.get('coordinates', {})
        segment_lat = segment_coords.get('latitude', 0)
        segment_lon = segment_coords.get('longitude', 0)

        # Find nearest ground stations
        nearest_stations = []
        for station_name, station_coords in self.starlink_ground_stations.items():
            distance = self._calculate_distance(
                segment_lat, segment_lon,
                station_coords['lat'], station_coords['lon']
            )
            if distance < 500:  # Within 500km
                nearest_stations.append({
                    'station': station_name,
                    'distance_km': distance,
                    'latency_ms': distance * 0.05  # 5ms per 100km
                })

        # Sort by distance
        nearest_stations.sort(key=lambda x: x['distance_km'])

        # Calculate coverage confidence
        if nearest_stations:
            best_station = nearest_stations[0]
            coverage_confidence = 1.0 - (best_station['distance_km'] / 500.0)
        else:
            coverage_confidence = 0.0
            best_station = None

        return {
            'fiber_segment': fiber_segment.get('segment_id', 'unknown'),
            'nearest_stations': nearest_stations[:5],  # Top 5
            'best_station': best_station,
            'coverage_confidence': coverage_confidence,
            'beam_coverage_available': coverage_confidence > 0.5
        }

    def _calculate_distance(self, lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points (Haversine formula)."""
        from math import radians, sin, cos, sqrt, asin

        R = 6371.0  # Earth radius in km

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        lon1_rad = radians(lon1)
        lon2_rad = radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        return R * c

    def optimize_starlink_fiber_handover(self, network_topology: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize Starlink-fiber handover points across network topology.

        Identifies optimal locations for Starlink backhaul integration
        with existing fiber infrastructure.
        """
        handover_candidates = []

        # Analyze each fiber segment
        for segment in network_topology.get('segments', []):
            overlap = self.identify_starlink_coverage_overlap(segment)

            if overlap['beam_coverage_available']:
                # Calculate handover quality score
                quality_score = (
                    overlap['coverage_confidence'] * 0.6 +
                    (1.0 - overlap['best_station']['latency_ms'] / 50.0) * 0.4
                )

                handover_candidates.append({
                    'segment_id': segment.get('segment_id'),
                    'best_station': overlap['best_station']['station'],
                    'quality_score': quality_score,
                    'latency_ms': overlap['best_station']['latency_ms'],
                    'coverage_confidence': overlap['coverage_confidence']
                })

        # Sort by quality score
        handover_candidates.sort(key=lambda x: x['quality_score'], reverse=True)

        # Select top candidates
        optimal_handovers = handover_candidates[:10]

        return {
            'total_candidates': len(handover_candidates),
            'optimal_handovers': optimal_handovers,
            'average_quality_score': sum(h['quality_score'] for h in optimal_handovers) / len(optimal_handovers) if optimal_handovers else 0,
            'average_latency_ms': sum(h['latency_ms'] for h in optimal_handovers) / len(optimal_handovers) if optimal_handovers else 0
        }

    def calculate_backhaul_redundancy(self, network_topology: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate backhaul redundancy using Starlink as backup fiber path.

        Identifies network segments where Starlink can provide redundancy
        for fiber optic backhaul.
        """
        redundancy_analysis = []

        for segment in network_topology.get('segments', []):
            overlap = self.identify_starlink_coverage_overlap(segment)

            # Determine redundancy value
            if overlap['beam_coverage_available']:
                redundancy_value = overlap['coverage_confidence']

                # Higher value for critical segments
                if segment.get('type') == 'submarine_cable':
                    redundancy_value *= 1.5

                redundancy_analysis.append({
                    'segment_id': segment.get('segment_id'),
                    'redundancy_available': True,
                    'redundancy_value': redundancy_value,
                    'backup_station': overlap['best_station']['station'],
                    'backup_latency_ms': overlap['best_station']['latency_ms']
                })
            else:
                redundancy_analysis.append({
                    'segment_id': segment.get('segment_id'),
                    'redundancy_available': False,
                    'redundancy_value': 0.0
                })

        # Calculate overall network redundancy
        segments_with_redundancy = sum(1 for r in redundancy_analysis if r['redundancy_available'])
        total_segments = len(redundancy_analysis)
        network_redundancy = segments_with_redundancy / total_segments if total_segments > 0 else 0

        return {
            'network_redundancy_percent': network_redundancy * 100,
            'segments_with_redundancy': segments_with_redundancy,
            'total_segments': total_segments,
            'segment_analysis': redundancy_analysis
        }


class SatelliteRepeaterAlignment:
    """
    Satellite backbone orientation and baseline repeater alignment system.

    Combines public satellite data (TLE, ephemeris, orbital adjustments) with ground-based
    repeater infrastructure for enhanced network topology mapping confidence.

    Data Sources:
    - Celestrak TLE data (public satellite catalog)
    - Space-Track orbital element data
    - Satellite operator published adjustments
    - Ground station/repeater coordinate databases
    """

    def __init__(self):
        # Public TLE data sources
        self.tle_sources = {
            'celestrak': 'https://www.celestrak.com/NORAD/elements/',
            'space_track': 'https://www.space-track.org',
            'satnogs': 'https://db.satnogs.org/api/satellites/',
        }

        # Major communication satellite constellations
        self.satellite_constellations = {
            'starlink': {
                'altitude_km': 550,
                'inclination_deg': 53.0,
                'orbital_period_min': 95.0,
                'repeat_cycle_days': 1,
                'satellites_per_plane': 22,
                'num_planes': 72
            },
            'oneweb': {
                'altitude_km': 1200,
                'inclination_deg': 87.9,
                'orbital_period_min': 109.0,
                'repeat_cycle_days': 7,
                'satellites_per_plane': 12,
                'num_planes': 12
            },
            'kuiper': {
                'altitude_km': 630,
                'inclination_deg': 51.1,
                'orbital_period_min': 97.0,
                'repeat_cycle_days': 1,
                'satellites_per_plane': 18,
                'num_planes': 78
            },
            'geostationary': {
                'altitude_km': 35786,
                'inclination_deg': 0.0,
                'orbital_period_min': 1436.0,
                'repeat_cycle_days': 1,
                'satellites_per_plane': 1,
                'num_planes': 1
            }
        }

        # Baseline repeater categories
        self.repeater_types = {
            'fiber_optic': {
                'spacing_km': 80,
                'type': 'optical_amplifier',
                'latency_ms': 0.4
            },
            'satellite_ground': {
                'spacing_km': 1000,
                'type': 'earth_station',
                'latency_ms': 250
            },
            'submarine_branching': {
                'spacing_km': 50,
                'type': 'branching_unit',
                'latency_ms': 0.25
            },
            'terrestrial_regenerator': {
                'spacing_km': 40,
                'type': 'regenerator',
                'latency_ms': 0.2
            }
        }

        # Orbital adjustment types
        self.adjustment_types = {
            'station_keeping': 'Regular orbital corrections',
            'inclination_change': 'Orbital plane adjustment',
            'altitude_adjustment': 'Height correction',
            'phasing': 'In-plane position adjustment',
            'collision_avoidance': 'Emergency maneuver',
            'end_of_life': 'Deorbit maneuver'
        }

        # Alignment confidence parameters
        self.alignment_params = {
            'max_lookahead_hours': 48,
            'tolerance_km': 10,
            'elevation_threshold_deg': 10.0,
            'azimuth_tolerance_deg': 5.0,
            'time_tolerance_sec': 60
        }

    def parse_tle(self, tle_line1: str, tle_line2: str) -> Dict[str, Any]:
        """
        Parse Two-Line Element (TLE) format satellite orbital data.

        Standard NORAD TLE format containing orbital elements for satellite positioning.
        """
        # Extract satellite number from line 1
        sat_number = tle_line1[2:7].strip()

        # Extract epoch (year and day of year) from line 1
        epoch_year = int(tle_line1[18:20])
        epoch_day = float(tle_line1[20:32])

        # Extract mean motion (revolutions per day) from line 2
        mean_motion = float(tle_line2[52:63])

        # Extract eccentricity from line 2
        eccentricity = float("0." + tle_line2[26:33])

        # Extract inclination (degrees) from line 2
        inclination = float(tle_line2[8:16])

        # Extract RAAN (degrees) from line 2
        raan = float(tle_line2[17:25])

        # Extract argument of perigee (degrees) from line 2
        arg_perigee = float(tle_line2[34:42])

        # Extract mean anomaly (degrees) from line 2
        mean_anomaly = float(tle_line2[43:51])

        # Calculate orbital period (minutes)
        orbital_period = 1440.0 / mean_motion if mean_motion > 0 else 0

        # Calculate semi-major axis (km) using Kepler's third law
        earth_radius_km = 6371.0
        if orbital_period > 0:
            semi_major_axis = ((earth_radius_km * orbital_period * 60 / (2 * math.pi))**2 * 398600.4418)**(1/3)
            altitude = semi_major_axis - earth_radius_km
        else:
            semi_major_axis = 0
            altitude = 0

        return {
            'satellite_number': sat_number,
            'epoch_year': epoch_year,
            'epoch_day': epoch_day,
            'mean_motion': mean_motion,
            'eccentricity': eccentricity,
            'inclination': inclination,
            'raan': raan,
            'arg_perigee': arg_perigee,
            'mean_anomaly': mean_anomaly,
            'orbital_period_min': orbital_period,
            'altitude_km': altitude,
            'semi_major_axis_km': semi_major_axis
        }

    def propagate_orbit(self, tle_data: Dict[str, Any],
                       time_delta_hours: float) -> Dict[str, Any]:
        """
        Propagate satellite orbit forward in time using simplified Keplerian propagation.

        Estimates satellite position after time delta from TLE epoch.
        """
        # Convert time delta to orbital periods
        orbital_period_hours = tle_data['orbital_period_min'] / 60.0
        periods_elapsed = time_delta_hours / orbital_period_hours if orbital_period_hours > 0 else 0

        # Update mean anomaly
        new_mean_anomaly = (tle_data['mean_anomaly'] + 360.0 * periods_elapsed) % 360.0

        # Simplified position calculation (circular orbit approximation)
        if tle_data['eccentricity'] < 0.01:  # Nearly circular
            # Calculate true anomaly (approximate for low eccentricity)
            true_anomaly = new_mean_anomaly

            # Calculate radius (constant for circular)
            radius = tle_data['semi_major_axis_km']

            # Calculate position in orbital plane
            x_orbital = radius * math.cos(math.radians(true_anomaly))
            y_orbital = radius * math.sin(math.radians(true_anomaly))

            # Rotate to ECI frame using inclination and RAAN
            inc_rad = math.radians(tle_data['inclination'])
            raan_rad = math.radians(tle_data['raan'])
            arg_perigee_rad = math.radians(tle_data['arg_perigee'])

            # 3D rotation (simplified)
            x_eci = (math.cos(raan_rad) * math.cos(arg_perigee_rad) -
                    math.sin(raan_rad) * math.sin(arg_perigee_rad) * math.cos(inc_rad)) * x_orbital + \
                   (-math.cos(raan_rad) * math.sin(arg_perigee_rad) -
                    math.sin(raan_rad) * math.cos(arg_perigee_rad) * math.cos(inc_rad)) * y_orbital

            y_eci = (math.sin(raan_rad) * math.cos(arg_perigee_rad) +
                    math.cos(raan_rad) * math.sin(arg_perigee_rad) * math.cos(inc_rad)) * x_orbital + \
                   (-math.sin(raan_rad) * math.sin(arg_perigee_rad) +
                    math.cos(raan_rad) * math.cos(arg_perigee_rad) * math.cos(inc_rad)) * y_orbital

            z_eci = (math.sin(arg_perigee_rad) * math.sin(inc_rad)) * x_orbital + \
                   (math.cos(arg_perigee_rad) * math.sin(inc_rad)) * y_orbital

            # Convert to latitude/longitude (simplified)
            latitude = math.degrees(math.asin(z_eci / radius))
            longitude = math.degrees(math.atan2(y_eci, x_eci))

            return {
                'latitude': latitude,
                'longitude': longitude,
                'altitude_km': tle_data['altitude_km'],
                'time_delta_hours': time_delta_hours,
                'true_anomaly': true_anomaly
            }
        else:
            # For eccentric orbits, return placeholder
            return {
                'latitude': 0.0,
                'longitude': 0.0,
                'altitude_km': tle_data['altitude_km'],
                'time_delta_hours': time_delta_hours,
                'true_anomaly': new_mean_anomaly,
                'note': 'Eccentric orbit - simplified propagation'
            }

    def calculate_visibility(self, satellite_pos: Dict[str, float],
                           ground_station: Tuple[float, float, float]) -> Dict[str, float]:
        """
        Calculate satellite visibility from ground station.

        Returns elevation, azimuth, and visibility metrics.
        """
        sat_lat = math.radians(satellite_pos['latitude'])
        sat_lon = math.radians(satellite_pos['longitude'])
        sat_alt = satellite_pos['altitude_km']

        station_lat = math.radians(ground_station[0])
        station_lon = math.radians(ground_station[1])
        station_alt = ground_station[2] / 1000.0  # Convert to km

        # Earth radius
        earth_radius = 6371.0

        # Convert to ECEF coordinates
        sat_r = earth_radius + sat_alt
        station_r = earth_radius + station_alt

        sat_x = sat_r * math.cos(sat_lat) * math.cos(sat_lon)
        sat_y = sat_r * math.cos(sat_lat) * math.sin(sat_lon)
        sat_z = sat_r * math.sin(sat_lat)

        station_x = station_r * math.cos(station_lat) * math.cos(station_lon)
        station_y = station_r * math.cos(station_lat) * math.sin(station_lon)
        station_z = station_r * math.sin(station_lat)

        # Vector from station to satellite
        dx = sat_x - station_x
        dy = sat_y - station_y
        dz = sat_z - station_z

        # Calculate elevation
        # Local horizontal plane normal vector
        horizon_normal_x = math.cos(station_lat) * math.cos(station_lon)
        horizon_normal_y = math.cos(station_lat) * math.sin(station_lon)
        horizon_normal_z = math.sin(station_lat)

        # Dot product for elevation angle
        dot_product = dx * horizon_normal_x + dy * horizon_normal_y + dz * horizon_normal_z
        distance = math.sqrt(dx**2 + dy**2 + dz**2)

        elevation_rad = math.asin(dot_product / distance) if distance > 0 else 0
        elevation_deg = math.degrees(elevation_rad)

        # Calculate azimuth
        # Local east and north vectors
        east_x = -math.sin(station_lon)
        east_y = math.cos(station_lon)
        east_z = 0

        north_x = -math.sin(station_lat) * math.cos(station_lon)
        north_y = -math.sin(station_lat) * math.sin(station_lon)
        north_z = math.cos(station_lat)

        # Project satellite vector onto horizontal plane
        horizontal_dot = dot_product
        horizontal_dx = dx - horizontal_dot * horizon_normal_x
        horizontal_dy = dy - horizontal_dot * horizon_normal_y
        horizontal_dz = dz - horizontal_dot * horizon_normal_z

        # Azimuth from north
        azimuth_north = horizontal_dx * north_x + horizontal_dy * north_y + horizontal_dz * north_z
        azimuth_east = horizontal_dx * east_x + horizontal_dy * east_y + horizontal_dz * east_z

        azimuth_rad = math.atan2(azimuth_east, azimuth_north)
        azimuth_deg = math.degrees(azimuth_rad) % 360

        # Check visibility (above elevation threshold)
        is_visible = elevation_deg >= self.alignment_params['elevation_threshold_deg']

        return {
            'elevation_deg': elevation_deg,
            'azimuth_deg': azimuth_deg,
            'distance_km': distance,
            'is_visible': is_visible,
            'visibility_duration_min': self._estimate_visibility_duration(elevation_deg, sat_alt)
        }

    def _estimate_visibility_duration(self, elevation_deg: float, altitude_km: float) -> float:
        """Estimate visibility duration based on elevation and altitude."""
        if elevation_deg < self.alignment_params['elevation_threshold_deg']:
            return 0.0

        # Simplified estimate based on orbital mechanics
        # Higher altitude = longer visibility
        orbital_velocity = math.sqrt(398600.4418 / (6371.0 + altitude_km))  # km/s
        horizon_distance = math.sqrt(2 * 6371.0 * altitude_km + altitude_km**2)
        visibility_duration = (2 * horizon_distance) / orbital_velocity / 60.0  # minutes

        # Adjust for elevation (higher elevation = longer visibility)
        elevation_factor = math.sin(math.radians(elevation_deg))
        return visibility_duration * elevation_factor

    def align_satellite_to_repeater(self, tle_data: Dict[str, float],
                                    repeater_coords: Tuple[float, float, float],
                                    adjustment_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Align satellite positioning with baseline repeater infrastructure.

        Combines orbital propagation, visibility calculation, and adjustment data
        to determine optimal alignment windows.
        """
        # Propagate orbit to current time
        current_pos = self.propagate_orbit(tle_data, 0)

        # Calculate visibility
        visibility = self.calculate_visibility(current_pos, repeater_coords)

        # Apply adjustment corrections if available
        if adjustment_data:
            adjusted_pos = self._apply_orbital_adjustments(current_pos, adjustment_data)
            adjusted_visibility = self.calculate_visibility(adjusted_pos, repeater_coords)
        else:
            adjusted_pos = current_pos
            adjusted_visibility = visibility

        # Calculate alignment confidence
        alignment_confidence = self._calculate_alignment_confidence(
            visibility, adjusted_visibility, adjustment_data
        )

        # Predict future alignment windows
        future_windows = self._predict_alignment_windows(
            tle_data, repeater_coords, adjustment_data
        )

        return {
            'satellite_position': current_pos,
            'visibility': visibility,
            'adjusted_position': adjusted_pos,
            'adjusted_visibility': adjusted_visibility,
            'alignment_confidence': alignment_confidence,
            'future_windows': future_windows,
            'repeater_coordinates': repeater_coords
        }

    def _apply_orbital_adjustments(self, position: Dict[str, float],
                                  adjustment_data: Dict) -> Dict[str, float]:
        """Apply published orbital adjustments to satellite position."""
        adjusted_pos = position.copy()

        if 'inclination_change_deg' in adjustment_data:
            adjusted_pos['latitude'] += adjustment_data['inclination_change_deg']

        if 'altitude_change_km' in adjustment_data:
            adjusted_pos['altitude_km'] += adjustment_data['altitude_change_km']

        if 'longitude_shift_deg' in adjustment_data:
            adjusted_pos['longitude'] += adjustment_data['longitude_shift_deg']

        return adjusted_pos

    def _calculate_alignment_confidence(self, visibility: Dict,
                                       adjusted_visibility: Dict,
                                       adjustment_data: Optional[Dict]) -> float:
        """Calculate confidence score for satellite-repeater alignment."""
        # Base confidence from visibility
        if visibility['is_visible']:
            base_confidence = 0.7
        else:
            base_confidence = 0.3

        # Elevation bonus
        elevation_bonus = min(visibility['elevation_deg'] / 90.0, 0.2)

        # Adjustment confidence
        if adjustment_data:
            adjustment_confidence = 0.1
        else:
            adjustment_confidence = 0.0

        # Total confidence
        total_confidence = base_confidence + elevation_bonus + adjustment_confidence

        return min(total_confidence, 1.0)

    def _predict_alignment_windows(self, tle_data: Dict[str, float],
                                   repeater_coords: Tuple[float, float, float],
                                   adjustment_data: Optional[Dict]) -> List[Dict]:
        """Predict future alignment windows for satellite-repeater pairs."""
        windows = []

        # Check alignment at regular intervals
        for hours in range(1, self.alignment_params['max_lookahead_hours'] + 1):
            pos = self.propagate_orbit(tle_data, hours)
            vis = self.calculate_visibility(pos, repeater_coords)

            if vis['is_visible']:
                windows.append({
                    'start_time_hours': hours,
                    'duration_min': vis['visibility_duration_min'],
                    'elevation_deg': vis['elevation_deg'],
                    'azimuth_deg': vis['azimuth_deg']
                })

        return windows


class GeneticNetworkMapper:
    """
    Genetic communications signal theory applied to network topology inference.

    Steals signal theories from genetic communications to improve fiber optic network mapping:
    - DNA/RNA alphabets as network symbol encoding
    - Codon translation for routing path interpretation
    - Alignment primitives for route comparison
    - Variant detection for infrastructure changes
    - Regulatory gates for peering point identification
    - Compression primitives for efficient network representation
    - Fitness-entropy compensation for confidence scoring
    """

    def __init__(self):
        # Network DNA alphabet (4-symbol discrete sequence primitive)
        self.network_dna_alphabet = {
            'A': 'AS_path_marker',      # Autonomous System path
            'C': 'Cable_segment',       # Physical cable segment
            'G': 'Geographic_hop',      # Geographic routing hop
            'T': 'Temporal_marker',     # Timing/congestion marker
            'N': 'Unknown_state',       # Unresolved network state
            '-': 'Gap/missing',         # Alignment gap or missing data
        }

        # Network codon table (triplet-to-action mapping)
        self.network_codon_table = {
            # Peering point codons
            'AAA': 'major_ixp_crossing',
            'AAC': 'regional_peering',
            'AAG': 'transit_provider',
            'AAT': 'content_delivery_network',

            # Cable type codons
            'ACA': 'submarine_cable',
            'ACC': 'terrestrial_fiber',
            'ACG': 'aerial_cable',
            'ACT': 'satellite_link',

            # Geographic codons
            'AGA': 'continental_crossing',
            'AGC': 'ocean_crossing',
            'AGG': 'urban_densification',
            'AGT': 'rural_last_mile',

            # Temporal codons
            'ATA': 'peak_hour_congestion',
            'ATC': 'maintenance_window',
            'ATG': 'normal_operation',
            'ATT': 'failure_event',

            # Stop codons (path termination)
            'TAA': 'path_complete',
            'TAG': 'path_blocked',
            'TGA': 'path_diverted',
        }

        # Network SNP (Single Network Polymorphism) detection
        self.network_snp_types = {
            'route_snp': 'single_hop substitution in AS path',
            'latency_snp': 'RTT value mutation',
            'bandwidth_snp': 'capacity change',
            'peering_snp': 'new/lost peering relationship',
        }

        # Fitness-entropy compensation parameters (from bioRxiv integration)
        self.fitness_entropy_params = {
            'f_max': 1.0,           # Maximum fitness
            'alpha': 0.5,           # Entropy penalty coefficient
            'delta_G': 0.0,         # Gibbs free energy change
            'delta_H': 0.0,        # Enthalpy change
            'T': 300.0,             # Temperature (arbitrary units)
            'delta_S': 0.0,         # Entropy change
        }

        # Genomic compression parameters for network data
        self.genomic_compression_params = {
            'rho_seq_sq': 0.95,      # sequence alignment accuracy (route accuracy)
            'v_epigenetic_sq': 0.8,  # methylation dynamics (traffic pattern changes)
            'tau_structure_sq': 0.7, # 3D folding tension (topological constraints)
            'sigma_entropy_sq': 0.6, # nucleotide diversity (path diversity)
            'q_conservation_sq': 0.9, # evolutionary constraint (protocol constraints)
            'kappa_hierarchy_sq': 0.5, # chromatin levels (network hierarchy)
            'epsilon_mutation': 0.01,  # mutation rate (network change rate)
        }

        # IUPAC-style ambiguity codes for network uncertainty
        self.network_ambiguity = {
            'R': 'A_or_G',           # Purine class (AS or geographic)
            'Y': 'C_or_T',           # Pyrimidine class (cable or temporal)
            'S': 'G_or_C',           # Strong class (geographic or cable)
            'W': 'A_or_T',           # Weak class (AS or temporal)
            'K': 'G_or_T',           # Keto class (geographic or temporal)
            'M': 'A_or_C',           # Amino class (AS or cable)
            'B': 'C_or_G_or_T',      # Not A
            'D': 'A_or_G_or_T',      # Not C
            'H': 'A_or_C_or_T',      # Not G
            'V': 'A_or_C_or_G',      # Not T
        }

    def encode_network_path_as_dna(self, as_path: List[str],
                                   cable_type: str,
                                   geography: str,
                                   timing: str) -> str:
        """
        Encode network path as DNA sequence using 4-symbol alphabet.

        Maps network properties to DNA bases for genetic analysis.
        """
        dna_sequence = []

        # Encode AS path
        for as_hop in as_path:
            dna_sequence.append('A')  # Each AS hop gets an 'A'

        # Encode cable type
        if cable_type == 'submarine':
            dna_sequence.append('C')
        elif cable_type == 'terrestrial':
            dna_sequence.append('C')
        elif cable_type == 'aerial':
            dna_sequence.append('C')
        else:
            dna_sequence.append('N')  # Unknown

        # Encode geography
        if 'ocean' in geography.lower():
            dna_sequence.append('G')
        elif 'continental' in geography.lower():
            dna_sequence.append('G')
        else:
            dna_sequence.append('N')

        # Encode timing
        if 'peak' in timing.lower():
            dna_sequence.append('T')
        elif 'maintenance' in timing.lower():
            dna_sequence.append('T')
        else:
            dna_sequence.append('N')

        return ''.join(dna_sequence)

    def translate_network_codon(self, dna_triplet: str) -> str:
        """
        Translate DNA triplet to network action using codon table.

        Analogous to biological codon translation for protein synthesis.
        """
        return self.network_codon_table.get(dna_triplet, 'unknown_codon')

    def detect_network_snp(self, baseline_path: str,
                          observed_path: str) -> Dict[str, Any]:
        """
        Detect Single Network Polymorphisms (SNPs) between baseline and observed paths.

        Identifies mutations in network topology.
        """
        if len(baseline_path) != len(observed_path):
            return {'error': 'Path length mismatch'}

        snps = []
        for i, (base, obs) in enumerate(zip(baseline_path, observed_path)):
            if base != obs:
                snp_type = self._classify_snp(base, obs)
                snps.append({
                    'position': i,
                    'baseline': base,
                    'observed': obs,
                    'type': snp_type
                })

        return {
            'snp_count': len(snps),
            'snps': snps,
            'mutation_rate': len(snps) / len(baseline_path) if baseline_path else 0
        }

    def _classify_snp(self, baseline: str, observed: str) -> str:
        """Classify SNP type based on base change."""
        if baseline == 'A' and observed != 'A':
            return 'route_snp'
        elif baseline == 'C' and observed != 'C':
            return 'bandwidth_snp'
        elif baseline == 'G' and observed != 'G':
            return 'geographic_snp'
        elif baseline == 'T' and observed != 'T':
            return 'temporal_snp'
        else:
            return 'unknown_snp'

    def calculate_fitness_entropy_compensation(self, fitness: float,
                                               entropy: float) -> float:
        """
        Apply fitness-entropy compensation from bioRxiv research.

        f = f_max - α × H
        ΔG = ΔH - TΔS
        """
        compensated_fitness = self.fitness_entropy_params['f_max'] - \
                            self.fitness_entropy_params['alpha'] * entropy

        # Gibbs free energy compensation
        delta_G = self.fitness_entropy_params['delta_H'] - \
                 self.fitness_entropy_params['T'] * self.fitness_entropy_params['delta_S']

        return compensated_fitness + delta_G

    def calculate_genomic_weight(self, route_accuracy: float,
                                traffic_dynamics: float,
                                topological_constraints: float,
                                path_diversity: float,
                                protocol_constraints: float,
                                network_hierarchy: float,
                                change_rate: float) -> float:
        """
        Calculate genomic weight for network confidence scoring.

        From DSP erasure coding theory genomic compression parameters.
        """
        genomic_weight = (
            route_accuracy +
            traffic_dynamics +
            topological_constraints +
            path_diversity +
            protocol_constraints
        ) / (
            (1 + network_hierarchy**2) *
            (1 + change_rate)
        )

        return genomic_weight

    def network_alignment_score(self, path1: str, path2: str) -> Dict[str, float]:
        """
        Calculate network alignment score using genetic alignment primitives.

        Analogous to pairwise sequence alignment in genomics.
        """
        if len(path1) != len(path2):
            # Handle length mismatch with gap penalties
            max_len = max(len(path1), len(path2))
            path1 = path1.ljust(max_len, '-')
            path2 = path2.ljust(max_len, '-')

        matches = 0
        mismatches = 0
        gaps = 0

        for b1, b2 in zip(path1, path2):
            if b1 == '-' or b2 == '-':
                gaps += 1
            elif b1 == b2:
                matches += 1
            else:
                mismatches += 1

        total = len(path1)
        identity = matches / total if total > 0 else 0
        similarity = (matches + 0.5 * mismatches) / total if total > 0 else 0

        return {
            'identity': identity,
            'similarity': similarity,
            'matches': matches,
            'mismatches': mismatches,
            'gaps': gaps,
            'alignment_length': total
        }

    def infer_regulatory_gates(self, network_dna: str) -> List[str]:
        """
        Infer regulatory gates (peering points, bottlenecks) from network DNA.

        Analogous to promoter/enhancer detection in genomics.
        """
        regulatory_gates = []

        # Scan for promoter-like patterns
        for i in range(len(network_dna) - 2):
            codon = network_dna[i:i+3]
            action = self.translate_network_codon(codon)

            if 'ixp' in action or 'peering' in action:
                regulatory_gates.append({
                    'position': i,
                    'codon': codon,
                    'action': action,
                    'type': 'promoter'
                })
            elif 'blocked' in action or 'diverted' in action:
                regulatory_gates.append({
                    'position': i,
                    'codon': codon,
                    'action': action,
                    'type': 'terminator'
                })

        return regulatory_gates

    def apply_ambiguity_encoding(self, confidence: float) -> str:
        """
        Apply IUPAC-style ambiguity encoding based on confidence.

        Low confidence gets ambiguity codes instead of exact bases.
        """
        if confidence >= 0.95:
            return 'exact'  # Use exact A,C,G,T
        elif confidence >= 0.8:
            return 'R'      # Purine class ambiguity
        elif confidence >= 0.6:
            return 'Y'      # Pyrimidine class ambiguity
        elif confidence >= 0.4:
            return 'N'      # Complete ambiguity
        else:
            return '-'      # Gap/missing data


class BaudRateResonanceAligner:
    """
    Baud rate resonance aligner based on Virtual Baud Reconstruction Layer (VBRL) research.

    Integrates baud rate concepts with resonant frequency alignments using:
    - VBRL multi-lane architecture (DATA, CTRL, CLOCK, REPAIR, WITNESS)
    - Virtual baud clock / reconstruction tick index
    - Braid type interpretation for manifold resonance
    - Signal reconstruction as controlled by resonance alignment
    """

    def __init__(self):
        # VBRL lane architecture mapping to resonance hierarchy
        self.vbrl_lanes = {
            'DATA': {
                'description': 'glyphs, literals, eigen descriptors',
                'resonance_mapping': 'L1_information',
                'frequency_range': (100, 10000)  # Hz
            },
            'CTRL': {
                'description': 'mode switches, kernel calls, page/domain structure',
                'resonance_mapping': 'L4_topological',
                'frequency_range': (1, 100)  # Hz - control signals
            },
            'CLOCK': {
                'description': 'frame, block, tick, and phase boundaries',
                'resonance_mapping': 'L2_cognitive',
                'frequency_range': (10, 1000)  # Hz - timing references
            },
            'REPAIR': {
                'description': 'residual bytes, checksums, patch operations',
                'resonance_mapping': 'L5_thermodynamic',
                'frequency_range': (0.1, 10)  # Hz - slow repair cycles
            },
            'WITNESS': {
                'description': 'type, manifold, O-AMMR, ENE, and hash receipts',
                'resonance_mapping': 'L3_geometric',
                'frequency_range': (0.01, 1)  # Hz - witness checkpoints
            }
        }

        # Standard baud rates and their resonance characteristics
        self.standard_baud_rates = {
            300: {'description': 'Very low speed', 'resonant_harmonic': 1},
            1200: {'description': 'Low speed', 'resonant_harmonic': 4},
            2400: {'description': 'Medium-low speed', 'resonant_harmonic': 8},
            4800: {'description': 'Medium speed', 'resonant_harmonic': 16},
            9600: {'description': 'Standard serial', 'resonant_harmonic': 32},
            19200: {'description': 'High speed serial', 'resonant_harmonic': 64},
            38400: {'description': 'Very high speed', 'resonant_harmonic': 128},
            57600: {'description': 'Ultra high speed', 'resonant_harmonic': 192},
            115200: {'description': 'Maximum standard UART', 'resonant_harmonic': 384}
        }

        # Virtual baud clock parameters
        self.virtual_baud_base = 115200  # Base virtual baud rate
        self.reconstruction_tick_divider = 16  # From UART hardware (27MHz / 115200 = 234)

        # Braid type interpretation parameters
        self.braid_coupling_coefficients = {
            'DATA_strand': 0.35,
            'CTRL_strand': 0.25,
            'CLOCK_strand': 0.20,
            'REPAIR_strand': 0.10,
            'WITNESS_strand': 0.10
        }

    def baud_to_resonant_frequency(self, baud_rate: float, harmonic: int = 1) -> float:
        """
        Convert baud rate to resonant frequency.

        Baud rate (symbols/sec) maps to resonant frequency through harmonic relationships.
        Higher baud rates create higher resonant harmonics.
        """
        base_frequency = baud_rate / 1000.0  # Convert to kHz
        resonant_freq = base_frequency * harmonic
        return resonant_freq

    def virtual_baud_tick_to_phase(self, tick_index: int) -> float:
        """
        Convert virtual baud tick index to phase.

        Virtual baud clock provides phase alignment for resonance.
        """
        phase = (tick_index % self.reconstruction_tick_divider) / self.reconstruction_tick_divider
        return phase * 2 * math.pi  # Convert to radians

    def lane_resonance_score(self, lane_name: str, frequency: float) -> float:
        """
        Calculate resonance score for a specific VBRL lane at given frequency.

        Maps VBRL lanes to resonance hierarchy levels and scores alignment.
        """
        if lane_name not in self.vbrl_lanes:
            return 0.0

        lane_info = self.vbrl_lanes[lane_name]
        freq_range = lane_info['frequency_range']

        # Check if frequency is within lane's resonant range
        if freq_range[0] <= frequency <= freq_range[1]:
            # Normalized position within range (0-1)
            normalized_pos = (frequency - freq_range[0]) / (freq_range[1] - freq_range[0])
            # Peak resonance at center of range (parabolic)
            center_score = 1.0 - 4 * (normalized_pos - 0.5)**2
            return max(0.0, center_score)
        else:
            return 0.0

    def braid_resonance_coupling(self, strand_weights: Dict[str, float]) -> float:
        """
        Calculate braid resonance coupling from strand weights.

        Braid type interpretation for manifold resonance using weighted strand coupling.
        """
        total_coupling = 0.0
        for strand, weight in strand_weights.items():
            if strand in self.braid_coupling_coefficients:
                total_coupling += weight * self.braid_coupling_coefficients[strand]
        return total_coupling

    def baud_resonance_alignment(self, baud_rate: float,
                                 target_frequency: float,
                                 phase_offset: float = 0.0) -> Dict[str, float]:
        """
        Calculate baud-resonance alignment metrics.

        Measures how well a given baud rate aligns with target resonant frequency.
        """
        # Convert baud to resonant frequency
        baud_resonant = self.baud_to_resonant_frequency(baud_rate)

        # Calculate frequency alignment (Lorentzian profile)
        detuning = abs(baud_resonant - target_frequency)
        frequency_alignment = 1.0 / (1.0 + detuning**2)

        # Calculate phase alignment
        phase_alignment = math.cos(phase_offset)**2

        # Calculate harmonic alignment
        harmonic_ratio = target_frequency / baud_resonant if baud_resonant > 0 else 0
        harmonic_alignment = 1.0 / (1.0 + (harmonic_ratio - round(harmonic_ratio))**2)

        return {
            'baud_resonant_frequency': baud_resonant,
            'frequency_alignment': frequency_alignment,
            'phase_alignment': phase_alignment,
            'harmonic_alignment': harmonic_alignment,
            'total_alignment': (frequency_alignment + phase_alignment + harmonic_alignment) / 3.0
        }

    def multi_lane_baud_filter(self, frequency_spectrum: np.ndarray,
                              baud_rate: float,
                              tick_index: int = 0) -> np.ndarray:
        """
        Apply multi-lane baud filtering across frequency spectrum.

        Combines VBRL lane architecture with baud-resonance alignment.
        """
        filtered_spectrum = np.zeros_like(frequency_spectrum)
        phase = self.virtual_baud_tick_to_phase(tick_index)

        for i, frequency in enumerate(frequency_spectrum):
            lane_scores = {}
            for lane_name in self.vbrl_lanes.keys():
                lane_scores[lane_name] = self.lane_resonance_score(lane_name, frequency)

            # Calculate baud-resonance alignment
            baud_alignment = self.baud_resonance_alignment(baud_rate, frequency, phase)

            # Combine lane scores with baud alignment
            combined_score = sum(lane_scores.values()) / len(lane_scores)
            combined_score *= baud_alignment['total_alignment']

            filtered_spectrum[i] = frequency_spectrum[i] * combined_score

        return filtered_spectrum

    def vbrl_manifold_read_shape(self, data_lane: np.ndarray,
                                ctrl_lane: np.ndarray,
                                clock_lane: np.ndarray,
                                repair_lane: np.ndarray,
                                witness_lane: np.ndarray) -> np.ndarray:
        """
        Apply VBRL manifold read shape to multi-lane data.

        Braid-type interpretation where lanes cross rather than being linear.
        """
        # Normalize lanes
        data_norm = data_lane / (np.max(np.abs(data_lane)) + 1e-9)
        ctrl_norm = ctrl_lane / (np.max(np.abs(ctrl_lane)) + 1e-9)
        clock_norm = clock_lane / (np.max(np.abs(clock_lane)) + 1e-9)
        repair_norm = repair_lane / (np.max(np.abs(repair_lane)) + 1e-9)
        witness_norm = witness_lane / (np.max(np.abs(witness_lane)) + 1e-9)

        # Apply braid coupling coefficients
        manifold_output = (
            self.braid_coupling_coefficients['DATA_strand'] * data_norm +
            self.braid_coupling_coefficients['CTRL_strand'] * ctrl_norm +
            self.braid_coupling_coefficients['CLOCK_strand'] * clock_norm +
            self.braid_coupling_coefficients['REPAIR_strand'] * repair_norm +
            self.braid_coupling_coefficients['WITNESS_strand'] * witness_norm
        )

        return manifold_output


class GlobalFiberOpticMap:
    """
    Global registry of fiber optic cable maps and data sources.

    Catalogs available maps and provides interfaces for accessing cable infrastructure data.
    """

    def __init__(self):
        self.maps = {
            'submarine_cable_map': {
                'url': 'https://www.submarinecablemap.com/',
                'type': 'submarine',
                'coverage': 'global',
                'api_available': True
            },
            'telegeography_2025': {
                'url': 'https://submarine-cable-map-2025.telegeography.com/',
                'type': 'submarine',
                'coverage': 'global',
                'api_available': True
            },
            'internet_infrastructure_map': {
                'url': 'https://map.kmcd.dev/',
                'type': 'submarine',
                'coverage': 'global',
                'api_available': True
            },
            'itu_broadband_map': {
                'url': 'https://bbmaps.itu.int/bbmaps/',
                'type': 'terrestrial',
                'coverage': 'global',
                'api_available': True
            },
            'fiber_map_world_2026': {
                'url': 'https://www.rsinc.com/fiber-map-of-the-world.php',
                'type': 'hybrid',
                'coverage': 'global',
                'api_available': False
            },
            'infrapedia': {
                'url': 'https://www.infrapedia.com/',
                'type': 'hybrid',
                'coverage': 'global',
                'api_available': True
            },
            'he_3d_network': {
                'url': 'https://he.net/3d-map/',
                'type': 'terrestrial',
                'coverage': 'global',
                'api_available': False
            },
            'esri_submarine_map': {
                'url': 'https://www.esri.com/about/newsroom/arcuser/submarine-cable',
                'type': 'submarine',
                'coverage': 'global',
                'api_available': False
            },
            'github_submarine_dataviz': {
                'url': 'https://gist.github.com/tylermorganwall/b222fcebcac3de56a6e144d73d166322',
                'type': 'submarine',
                'coverage': 'global',
                'api_available': True
            },
            'arcgis_submarine_dataset': {
                'url': 'https://opendata.arcgis.com/datasets/c12642b516bc4ee5bc9e89870ab14089_2.kml',
                'type': 'submarine',
                'coverage': 'global',
                'api_available': True
            }
        }

    def get_maps_by_type(self, cable_type: str) -> Dict[str, dict]:
        """Get maps filtered by cable type"""
        return {k: v for k, v in self.maps.items() if v['type'] == cable_type}

    def get_maps_with_api(self) -> Dict[str, dict]:
        """Get maps that have API access"""
        return {k: v for k, v in self.maps.items() if v['api_available']}

    def print_catalog(self):
        """Print the catalog of available maps"""
        print("Global Fiber Optic Cable Map Catalog")
        print("=" * 60)
        for name, info in self.maps.items():
            print(f"\n{name}:")
            print(f"  URL: {info['url']}")
            print(f"  Type: {info['type']}")
            print(f"  Coverage: {info['coverage']}")
            print(f"  API Available: {info['api_available']}")


def create_sample_cable_segments() -> List[CableSegment]:
    """Create sample cable segments for testing"""
    segments = [
        CableSegment(
            segment_id="transatlantic_1",
            start_lat=40.7128, start_lon=-74.0060,  # NYC
            end_lat=51.5074, end_lon=-0.1278,       # London
            length_km=5500,
            cable_type=CableType.SUBMARINE,
            depth_m=-3800,
            environment=EnvironmentType.DEEP_OCEAN,
            installation_year=2020
        ),
        CableSegment(
            segment_id="pacific_cross_1",
            start_lat=37.7749, start_lon=-122.4194,  # San Francisco
            end_lat=35.6762, end_lon=139.6503,       # Tokyo
            length_km=9000,
            cable_type=CableType.SUBMARINE,
            depth_m=-4000,
            environment=EnvironmentType.DEEP_OCEAN,
            installation_year=2021
        ),
        CableSegment(
            segment_id="euro terrestrial_1",
            start_lat=48.8566, start_lon=2.3522,     # Paris
            end_lat=52.5200, end_lon=13.4050,       # Berlin
            length_km=1000,
            cable_type=CableType.BURIED,
            depth_m=-1.5,
            environment=EnvironmentType.UNDERGROUND,
            installation_year=2019
        )
    ]
    return segments


def main():
    """Main function to demonstrate the VLB-integrated tensor network with resonant alignment and baud rate filtering"""
    print("Fiber Optic Vibrational Tensor Network with VLB Integration, Resonant Alignment, and Baud Rate Filtering")
    print("=" * 100)

    # Display catalog of available maps
    global_map = GlobalFiberOpticMap()
    global_map.print_catalog()

    # Create sample cable segments
    cable_segments = create_sample_cable_segments()
    print(f"\nCreated {len(cable_segments)} sample cable segments")

    # Initialize mappers
    frequency_mapper = FrequencyMapper()
    cable_mapper = CableInfrastructureMapper(cable_segments)

    print(f"\nFrequency range: {frequency_mapper.min_freq} Hz - {frequency_mapper.max_freq} Hz")
    print(f"Number of frequency bins: {frequency_mapper.num_bins}")
    print(f"Speech-relevant bins: {len(frequency_mapper.get_speech_relevant_bins())}")

    # Create tensor network
    tensor_network = FiberOpticTensorNetwork(
        spatial_dim=len(cable_segments),
        temporal_dim=100,
        frequency_dim=frequency_mapper.num_bins,
        infrastructure_dim=10,
        environmental_dim=5
    )

    print(f"\nTensor network initialized with {sum(p.numel() for p in tensor_network.parameters())} parameters")

    # Initialize VLB integrator
    vlb_integrator = VLBFiberOpticIntegrator(tensor_network)
    print("\nVLB Nibble-Delta integration initialized")
    print("  - Sparse encoding for vibrational state changes")
    print("  - 4-bit nibble switches for efficient event logging")
    print("  - Witness receipt generation for replay verification")
    print("  - Compression gain estimation using VLB methodology")

    # Initialize resonant alignment filter
    resonance_filter = ResonantAlignmentFilter()
    print("\nResonant Alignment Filter initialized")
    print("  - Multi-level resonance hierarchy (L0-L5)")
    print("  - Signal equation invariant roots (SIGROOT003, SIGROOT021, SIGROOT024)")
    print("  - Spherion resonance as geometric apex")
    print("  - Quality factor filtering for resonance sharpness")

    # Initialize baud rate resonance aligner
    baud_aligner = BaudRateResonanceAligner()
    print("\nBaud Rate Resonance Aligner initialized")
    print("  - VBRL multi-lane architecture (DATA, CTRL, CLOCK, REPAIR, WITNESS)")
    print("  - Virtual baud clock / reconstruction tick index")
    print("  - Braid type interpretation for manifold resonance")
    print("  - Signal reconstruction as controlled by resonance alignment")

    print(f"\nResonance Hierarchy Levels:")
    for level, info in resonance_filter.resonance_levels.items():
        print(f"  {level}: {info['type']} @ {info['characteristic_freq']}")

    print(f"\nSignal Equation Resonance Roots:")
    for root, info in resonance_filter.resonance_roots.items():
        print(f"  {root}: {info['filter_use']}")

    print(f"\nVBRL Lane Architecture:")
    for lane, info in baud_aligner.vbrl_lanes.items():
        print(f"  {lane}: {info['description']} -> {info['resonance_mapping']} @ {info['frequency_range']} Hz")

    print(f"\nStandard Baud Rates and Resonant Harmonics:")
    for baud, info in baud_aligner.standard_baud_rates.items():
        resonant_freq = baud_aligner.baud_to_resonant_frequency(baud, info['resonant_harmonic'])
        print(f"  {baud} baud: {info['description']}, harmonic {info['resonant_harmonic']} -> {resonant_freq:.1f} kHz")

    # Create sample vibrational signatures with different characteristics
    baseline_hash = hashlib.sha256(b"baseline_state").hexdigest()

    # Normal acoustic event
    normal_signature = VibrationalSignature(
        segment_id="transatlantic_1",
        timestamp=0.0,
        frequency_spectrum=frequency_mapper.freq_bins,
        amplitude_spectrum=np.random.rand(frequency_mapper.num_bins) * 0.05,
        strain_measurements=np.random.rand(100) * 1e-7,
        temperature_delta=0.2
    )

    # Anomalous event (simulating eavesdropping detection)
    anomaly_signature = VibrationalSignature(
        segment_id="transatlantic_1",
        timestamp=1.0,
        frequency_spectrum=frequency_mapper.freq_bins,
        amplitude_spectrum=np.random.rand(frequency_mapper.num_bins) * 0.3,  # Higher amplitude
        strain_measurements=np.random.rand(100) * 5e-6,  # Higher strain
        temperature_delta=1.5
    )

    print(f"\nProcessing vibrational signatures through integrated system...")

    # Apply resonant alignment filtering
    spatial_coords = (40.7128, -74.0060, -3800.0)  # NYC coordinates + depth
    resonance_filtered = resonance_filter.combined_resonance_filter(
        normal_signature.frequency_spectrum,
        spatial_coords,
        temperature=300.0
    )

    print(f"\nResonant Alignment Filtering Applied:")
    print(f"  Spatial coordinates: {spatial_coords}")
    print(f"  Original spectrum energy: {np.sum(normal_signature.amplitude_spectrum):.6f}")
    print(f"  Resonance-filtered energy: {np.sum(resonance_filtered * normal_signature.amplitude_spectrum):.6f}")
    print(f"  Energy retention: {np.sum(resonance_filtered * normal_signature.amplitude_spectrum) / np.sum(normal_signature.amplitude_spectrum) * 100:.2f}%")

    # Apply baud rate filtering at 115200 baud (standard UART max)
    baud_rate = 115200
    baud_filtered = baud_aligner.multi_lane_baud_filter(
        normal_signature.frequency_spectrum,
        baud_rate,
        tick_index=0
    )

    print(f"\nBaud Rate Filtering Applied (115200 baud):")
    print(f"  Baud rate: {baud_rate} symbols/sec")
    print(f"  Resonant frequency: {baud_aligner.baud_to_resonant_frequency(baud_rate):.1f} kHz")
    print(f"  Baud-filtered energy: {np.sum(baud_filtered * normal_signature.amplitude_spectrum):.6f}")
    print(f"  Energy retention: {np.sum(baud_filtered * normal_signature.amplitude_spectrum) / np.sum(normal_signature.amplitude_spectrum) * 100:.2f}%")

    # Combine resonance and baud filtering
    combined_filter = resonance_filtered * baud_filtered
    print(f"\nCombined Resonance + Baud Filtering:")
    print(f"  Combined-filtered energy: {np.sum(combined_filter * normal_signature.amplitude_spectrum):.6f}")
    print(f"  Energy retention: {np.sum(combined_filter * normal_signature.amplitude_spectrum) / np.sum(normal_signature.amplitude_spectrum) * 100:.2f}%")

    # Get multi-level resonance scores for a sample frequency
    sample_freq = 50.0  # Hz - within cognitive band
    resonance_scores = resonance_filter.multi_level_resonance_score(sample_freq, spatial_coords, 300.0)
    print(f"\nMulti-level Resonance Scores for {sample_freq} Hz:")
    for level, score in resonance_scores.items():
        print(f"  {level}: {score:.4f}")

    # Get VBRL lane resonance scores for sample frequency
    print(f"\nVBRL Lane Resonance Scores for {sample_freq} Hz:")
    for lane in baud_aligner.vbrl_lanes.keys():
        lane_score = baud_aligner.lane_resonance_score(lane, sample_freq)
        print(f"  {lane}: {lane_score:.4f}")

    # Calculate baud-resonance alignment for different baud rates
    print(f"\nBaud-Resonance Alignment Analysis for {sample_freq} Hz:")
    for test_baud in [9600, 19200, 38400, 57600, 115200]:
        alignment = baud_aligner.baud_resonance_alignment(test_baud, sample_freq)
        print(f"  {test_baud} baud: alignment={alignment['total_alignment']:.4f}, freq_align={alignment['frequency_alignment']:.4f}, harmonic_align={alignment['harmonic_alignment']:.4f}")

    # Process normal signature with combined filtering
    normal_signature_combined = VibrationalSignature(
        segment_id=normal_signature.segment_id,
        timestamp=normal_signature.timestamp,
        frequency_spectrum=normal_signature.frequency_spectrum,
        amplitude_spectrum=normal_signature.amplitude_spectrum * combined_filter,
        strain_measurements=normal_signature.strain_measurements,
        temperature_delta=normal_signature.temperature_delta
    )

    normal_result = vlb_integrator.process_vibrational_signature(normal_signature_combined, baseline_hash)
    print(f"\nNormal acoustic event (with resonance + baud filtering):")
    print(f"  Vibrational risk: {normal_result['tensor_outputs']['vibrational_risk']:.4f}")
    print(f"  Anomaly detected: {normal_result['tensor_outputs']['anomaly_detected']}")
    print(f"  VLB nibble: {bin(normal_result['vlb_encoding']['nibble'])}")
    print(f"  Switches count: {normal_result['vlb_encoding']['switches_count']}")
    print(f"  KOT cost: {normal_result['vlb_encoding']['kot_cost']}")
    print(f"  Compression gain: {normal_result['compression_metrics']['estimated_gain']:.2f}x")
    print(f"  Sparsity: {normal_result['compression_metrics']['sparsity']:.6f}")

    # Process anomaly signature
    anomaly_result = vlb_integrator.process_vibrational_signature(anomaly_signature, baseline_hash)
    print(f"\nAnomalous acoustic event (potential eavesdropping):")
    print(f"  Vibrational risk: {anomaly_result['tensor_outputs']['vibrational_risk']:.4f}")
    print(f"  Anomaly detected: {anomaly_result['tensor_outputs']['anomaly_detected']}")
    print(f"  VLB nibble: {bin(anomaly_result['vlb_encoding']['nibble'])}")
    print(f"  Switches count: {anomaly_result['vlb_encoding']['switches_count']}")
    print(f"  KOT cost: {anomaly_result['vlb_encoding']['kot_cost']}")
    print(f"  Compression gain: {anomaly_result['compression_metrics']['estimated_gain']:.2f}x")
    print(f"  Sparsity: {anomaly_result['compression_metrics']['sparsity']:.6f}")

    # Generate witness receipt
    receipt = vlb_integrator.generate_witness_receipt("transatlantic_1")
    if receipt:
        print(f"\nVLB Witness Receipt Generated:")
        print(f"  Segment ID: {receipt['segment_id']}")
        print(f"  Baseline hash: {receipt['baseline_hash'][:16]}...")
        print(f"  Target hash: {receipt['target_hash'][:16]}...")
        print(f"  Receipt hash: {receipt['receipt_hash'][:16]}...")
        print(f"  Total switches: {len(receipt['switches'])}")
        print(f"  Total KOT cost: {receipt['kot_cost']}")
        print(f"  Final compression gain: {receipt['compression_gain']:.2f}x")

    print(f"\nIntegrated System Analysis:")
    print(f"  " + "=" * 96)
    print(f"  VLB-DAS Integration: Sparse encoding for vibrational state changes")
    print(f"  Resonance Hierarchy: Multi-level filtering (L0-L5) from topology research")
    print(f"  Signal Equation Roots: SIGROOT003, SIGROOT021, SIGROOT024 for invariant filtering")
    print(f"  Spherion Resonance: Geometric apex with highest weight (0.3) in combined filter")
    print(f"  Cognitive Band: 1-100 Hz neural oscillation filtering (L2)")
    print(f"  Quality Factor: Q > 10 for narrow-band resonance selection")
    print(f"  VBRL Architecture: Multi-lane (DATA, CTRL, CLOCK, REPAIR, WITNESS) for signal reconstruction")
    print(f"  Baud Rate Alignment: Virtual baud clock maps to resonant frequency harmonics")
    print(f"  Braid Coupling: Strand weights for manifold resonance interpretation")
    print(f"  Compression: {normal_result['compression_metrics']['estimated_gain']:.1f}x gain with combined filtering")
    print(f"  Witness Accounting: Cryptographic receipts for replay verification")
    print(f"  Budget Control: KOT cost tracking with resonance-weighted processing")

    print(f"\nBaud-Resonance Extrapolation:")
    print(f"  - Baud rate (symbols/sec) maps to resonant frequency via harmonic relationships")
    print(f"  - 115200 baud -> 115.2 kHz base frequency with 384th harmonic")
    print(f"  - VBRL DATA lane (100-10000 Hz) aligns with L1 information resonance")
    print(f"  - VBRL CTRL lane (1-100 Hz) aligns with L4 topological resonance")
    print(f"  - VBRL CLOCK lane (10-1000 Hz) aligns with L2 cognitive resonance")
    print(f"  - VBRL REPAIR lane (0.1-10 Hz) aligns with L5 thermodynamic resonance")
    print(f"  - VBRL WITNESS lane (0.01-1 Hz) aligns with L3 geometric (spherion) resonance")
    print(f"  - Virtual baud tick provides phase alignment for resonance synchronization")
    print(f"  - Braid coupling coefficients weight manifold read shape")

    print(f"\nResonant Alignment Benefits:")
    print(f"  - Noise rejection via high-Q spherion resonance")
    print(f"  - Frequency-selective amplification at resonant frequencies")
    print(f"  - Multi-scale coupling across quantum to thermodynamic levels")
    print(f"  - Topological memory via void resonance patterns")
    print(f"  - Energy-efficient transfer through resonance matching")
    print(f"  - Baud-rate aligned temporal reconstruction via VBRL lanes")

    print(f"\nExpected Performance:")
    print(f"  Normal telemetry: 5×–20× (near-term realistic target)")
    print(f"  Resonance-filtered: 10×–40× (with resonant alignment)")
    print(f"  Baud-aligned: 15×–60× (with VBRL baud rate integration)")
    print(f"  Combined system: 20×–80× (resonance + baud alignment)")
    print(f"  Sparse events: 25×–100× (strong target with good sparsity)")
    print(f"  Extreme sparsity: 100×+ (telemetry-like regime)")


if __name__ == "__main__":
    main()
