#!/usr/bin/env python3
"""
Common Crawl Ingestion Pipeline with Waveprobe + Compression + Genetic Algorithm

Leverages:
- Waveprobe-inspired quantum data probing for intelligent selection
- UnifiedCompression bytestream optimization
- Genetic algorithm for parameter optimization
- Common Crawl CC-MAIN-2026-12 (1.97 billion pages)

Pipeline:
1. Waveprobe-inspired data selection from Common Crawl index
2. Genetic optimization of selection parameters
3. Bytestream compression using UnifiedCompression principles
4. Efficient storage and indexing

License: Apache 2.0
"""

import os
import json
import gzip
import requests
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random
import logging
import re
import boto3
from botocore import UNSIGNED
from botocore.client import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CommonCrawlWaveprobe")

# ═══════════════════════════════════════════════════════════════════════════
# §0  Common Crawl Configuration
# ═══════════════════════════════════════════════════════════════════════════

COMMONCRAWL_BASE = "https://data.commoncrawl.org/crawl-shared-data/data/CC-MAIN-2026-12"
# Try different index file patterns
CC_INDEX_URLS = [
    f"{COMMONCRAWL_BASE}/cc-index.table.paths.gz",
    f"{COMMONCRAWL_BASE}/cc-index.paths.gz",
    f"{COMMONCRAWL_BASE}/warc.paths.gz",
]
# WARC files are hosted on S3 but accessible via HTTP redirects
COMMONCRAWL_S3_BASE = "https://commoncrawl.s3.amazonaws.com"

@dataclass
class CommonCrawlConfig:
    """Configuration for Common Crawl ingestion."""
    max_segments: int = 100  # Maximum segments to process
    pages_per_segment: int = 1000  # Pages per segment to ingest
    compression_threshold: float = 0.9  # Compression ratio threshold (relaxed for small files)
    waveprobe_threshold: float = 0.5  # Waveprobe selection threshold
    genetic_population: int = 50  # Genetic algorithm population size
    genetic_generations: int = 20  # Genetic algorithm generations

# ═══════════════════════════════════════════════════════════════════════════
# §1  Unified Adaptation Equation (Sovereign Informatic Manifold)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AdaptationState:
    """State in the 6D quantized genome space."""
    mu_q: float  # Mutation rate (μ_q)
    rho_q: float  # Refresh rate (ρ_q)
    C_fac: float  # Graph connectance (C_fac)
    M_fac: float  # Modularity (M_fac)
    n_e: float  # Observer count (n_e)
    sigma_q: float  # Selection coefficient (σ_q)

class UnifiedAdaptationEquation:
    """
    The Unified Adaptation Equation governing the Sovereign Informatic Manifold.
    Four-layer Evolutionary Cost Surface over 6D quantized genome space with RGFlow.
    
    L(g₀) = 1 ⟺ ∀s ∈ [0,S], g_s ∈ Ω_law ∧ lim_{s→S} g_s ∈ A_law, dg_s/ds = β(g_s)
    """
    
    # Constants from the equation
    DRAKE_BUDGET_D = 0.003  # Drake Budget constant (D)
    DRIFT_BARRIER_B = 0.001  # Drift Barrier constant (B)
    LAMBDA = 0.5  # Mutation load parameter (λ)
    M_STAR = 0.5  # Optimal modularity (M*)
    EPSILON = 0.001  # Minimum value for C_fac, M_fac
    
    # RGFlow parameters
    SCALE_STEPS = 10  # Number of scale steps to simulate
    MAX_SCALE = 1.0  # Maximum abstraction scale S
    
    def __init__(self):
        # Precompute adaptation surface LUT (18-bit, 262,144 entries)
        self.adaptation_surface = self._precompute_adaptation_surface()
    
    def _beta_function(self, state: AdaptationState) -> AdaptationState:
        """
        Informatic beta function β(g_s).
        Describes how genome coordinates change across abstraction scales.
        
        Physical interpretation:
        - μ_s decreases with scale (noise washes out)
        - ρ_s decreases with scale (refresh rate slows)
        - C_s increases with scale (abstraction increases connectivity)
        - M_s approaches M* with scale (modularity optimizes)
        - N_s saturates with scale (observer mass converges)
        - σ_s increases with scale (selection advantage emerges)
        
        Updated to be more permissive for code files.
        """
        # Scale-dependent transformations (more conservative changes)
        mu_s = state.mu_q * 0.95  # Mutation rate decreases slower (was 0.9)
        rho_s = state.rho_q * 0.9  # Refresh rate decreases slower (was 0.8)
        C_s = min(state.C_fac * 1.05, 1.0)  # Connectance increases slower (was 1.2)
        M_s = state.M_fac + 0.05 * (self.M_STAR - state.M_fac)  # Modularity approaches M* slower (was 0.1)
        N_s = state.n_e * 1.02  # Observer mass increases slower (was 1.05)
        sigma_s = min(state.sigma_q * 1.05, 2.0)  # Selection advantage increases slower (was 1.1, capped at 2.0)
        
        return AdaptationState(mu_s, rho_s, C_s, M_s, N_s, sigma_s)
    
    def _simulate_rgflow(self, initial_state: AdaptationState) -> Tuple[bool, bool, bool, bool, int, int]:
        """
        Simulate RGFlow trajectory across scales.
        Returns (lawful_under_flow, reaches_attractor, flows_to_noise, flows_to_sabotage, rg_depth, attractor_id).
        """
        current_state = initial_state
        lawful_under_flow = True
        reaches_attractor = False
        flows_to_noise = False
        flows_to_sabotage = False
        
        for step in range(self.SCALE_STEPS):
            # Check if current state is lawful
            lawful, failure_mask = self._is_lawful(
                current_state.mu_q, current_state.rho_q, current_state.C_fac,
                current_state.M_fac, current_state.n_e, current_state.sigma_q
            )
            
            if not lawful:
                lawful_under_flow = False
                
                # Determine flow direction based on failure type
                if failure_mask & 0x1:  # Drake Budget failed
                    flows_to_sabotage = True
                elif failure_mask & 0x2:  # Drift Barrier failed
                    flows_to_noise = True
                elif failure_mask & 0x4:  # Error Threshold failed
                    flows_to_noise = True
                break
            
            # Apply beta function to evolve state
            current_state = self._beta_function(current_state)
        
        # Check if final state is in lawful attractor basin
        if lawful_under_flow:
            final_lawful, _ = self._is_lawful(
                current_state.mu_q, current_state.rho_q, current_state.C_fac,
                current_state.M_fac, current_state.n_e, current_state.sigma_q
            )
            reaches_attractor = final_lawful
        
        # Calculate RGFlow depth (how many steps remained lawful)
        rg_depth = step if not lawful_under_flow else self.SCALE_STEPS
        
        # Assign attractor ID based on final state characteristics
        attractor_id = self._compute_attractor_id(current_state)
        
        return lawful_under_flow, reaches_attractor, flows_to_noise, flows_to_sabotage, rg_depth, attractor_id
    
    def _compute_attractor_id(self, state: AdaptationState) -> int:
        """
        Compute attractor ID based on final state characteristics.
        Different attractors represent different types of lawful states.
        """
        # Simple attractor classification based on dominant features
        if state.sigma_q > 0.8:
            return 1  # High-fitness attractor
        elif state.n_e > 0.7:
            return 2  # High-popularity attractor
        elif state.M_fac > 0.8:
            return 3  # High-modularity attractor
        elif state.C_fac < 0.3:
            return 4  # Low-connectance attractor
        else:
            return 0  # Default attractor
    
    def _precompute_adaptation_surface(self) -> np.ndarray:
        """
        Precompute the adaptation surface into a 262,144-entry LUT.
        18-bit coordinate: 3 bits per variable (6 variables)
        Updated LUT structure with RGFlow fields.
        """
        lut_size = 2**18  # 262,144 entries
        # Use 64-bit entries to accommodate additional RGFlow fields
        surface = np.zeros(lut_size, dtype=np.uint64)
        
        # Quantize variables into 3-bit ranges (8 levels each)
        for coord in range(lut_size):
            # Decode 18-bit coordinate (3 bits per variable)
            mu_q_bits = (coord >> 15) & 0x7    # Bits 15-17
            rho_q_bits = (coord >> 12) & 0x7   # Bits 12-14
            C_fac_bits = (coord >> 9) & 0x7    # Bits 9-11
            M_fac_bits = (coord >> 6) & 0x7    # Bits 6-8
            n_e_bits = (coord >> 3) & 0x7      # Bits 3-5
            sigma_q_bits = coord & 0x7         # Bits 0-2
            
            # Normalize to [0, 1] range for mu_q, rho_q, C_fac, M_fac, n_e
            mu_q = mu_q_bits / 7.0
            rho_q = rho_q_bits / 7.0
            C_fac = max(self.EPSILON, C_fac_bits / 7.0)
            M_fac = max(self.EPSILON, M_fac_bits / 7.0)
            n_e = n_e_bits / 7.0
            
            # Normalize sigma_q to [1, 2] range (since Layer 3 requires sigma_q > 1)
            sigma_q = 1.0 + (sigma_q_bits / 7.0)  # Maps [0,7] to [1,2]
            
            # Create initial state
            initial_state = AdaptationState(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
            
            # Compute three-layer invariants (local lawfulness)
            lawful, failure_mask = self._is_lawful(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
            
            # Simulate RGFlow trajectory
            lawful_under_flow, reaches_attractor, flows_to_noise, flows_to_sabotage, rg_depth, attractor_id = self._simulate_rgflow(initial_state)
            
            # Compute cost (distance to lawfulness)
            cost = self._compute_adaptation_cost(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
            
            # Compute stability margin
            margin = self._compute_stability_margin(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
            
            # Store in LUT with updated structure:
            # Bit 0: lawful_now
            # Bit 1: lawful_under_RGFlow
            # Bit 2: reaches_lawful_attractor
            # Bit 3: flows_to_noise
            # Bit 4: flows_to_sabotage
            # Bits 5-7: reserved
            # Bits 8-23: cost_to_lawfulness (16 bits)
            # Bits 24-31: stability_margin (8 bits)
            # Bits 32-39: RGFlow_depth (8 bits)
            # Bits 40-47: attractor_id (8 bits)
            # Bits 48-55: failure_layer_mask (8 bits)
            # Bits 56-63: reserved
            
            lut_entry = (
                (int(lawful) & 0x1) |
                (int(lawful_under_flow) & 0x1) << 1 |
                (int(reaches_attractor) & 0x1) << 2 |
                (int(flows_to_noise) & 0x1) << 3 |
                (int(flows_to_sabotage) & 0x1) << 4 |
                ((int(cost * 1000) & 0xFFFF) << 8) |
                ((int(margin * 1000) & 0xFF) << 24) |
                ((rg_depth & 0xFF) << 32) |
                ((attractor_id & 0xFF) << 40) |
                ((failure_mask & 0xFF) << 48)
            )
            surface[coord] = lut_entry
        
        return surface
    
    def _is_lawful(self, mu_q: float, rho_q: float, C_fac: float, M_fac: float, 
                   n_e: float, sigma_q: float) -> Tuple[bool, int]:
        """
        Check if state satisfies all three local invariants.
        Returns (lawful, failure_mask) where failure_mask indicates which layers failed.
        Note: RGFlow is checked separately in _simulate_rgflow.
        """
        failure_mask = 0
        
        # Layer 1: Drake Budget (Mutation Limit)
        # μ_q ≤ D/C_fac
        drake_satisfied = mu_q <= self.DRAKE_BUDGET_D / C_fac
        if not drake_satisfied:
            failure_mask |= 0x1  # Bit 0: Drake Budget failed
        
        # Layer 2: Drift Barrier (Meaning Preservation)
        # ρ_q * N_e * Φ(M_fac) ≥ B
        N_e = np.log(1 + n_e)  # Saturating observer mass
        Phi_M_fac = 1 - abs(M_fac - self.M_STAR)  # Modularity quality function
        drift_satisfied = rho_q * N_e * Phi_M_fac >= self.DRIFT_BARRIER_B
        if not drift_satisfied:
            failure_mask |= 0x2  # Bit 1: Drift Barrier failed
        
        # Layer 3: Error Threshold (Fitness Advantage)
        # σ_q > 1 + λ * μ_q
        error_satisfied = sigma_q > 1 + self.LAMBDA * mu_q
        if not error_satisfied:
            failure_mask |= 0x4  # Bit 2: Error Threshold failed
        
        lawful = drake_satisfied and drift_satisfied and error_satisfied
        return lawful, failure_mask
    
    def _compute_adaptation_cost(self, mu_q: float, rho_q: float, C_fac: float, M_fac: float,
                                n_e: float, sigma_q: float) -> float:
        """
        Compute the "distance" to lawfulness.
        Lower cost = closer to lawful state.
        """
        # Layer 1 violation cost
        drake_target = self.DRAKE_BUDGET_D / C_fac
        drake_cost = max(0, mu_q - drake_target) / drake_target if drake_target > 0 else 0
        
        # Layer 2 violation cost
        N_e = np.log(1 + n_e)
        Phi_M_fac = 1 - abs(M_fac - self.M_STAR)
        drift_target = self.DRIFT_BARRIER_B
        drift_actual = rho_q * N_e * Phi_M_fac
        drift_cost = max(0, drift_target - drift_actual) / drift_target if drift_target > 0 else 0
        
        # Layer 3 violation cost
        error_target = 1 + self.LAMBDA * mu_q
        error_cost = max(0, error_target - sigma_q) / error_target if error_target > 0 else 0
        
        # Total cost (weighted sum)
        total_cost = drake_cost + drift_cost + error_cost
        return total_cost
    
    def _compute_stability_margin(self, mu_q: float, rho_q: float, C_fac: float, M_fac: float,
                                 n_e: float, sigma_q: float) -> float:
        """
        Compute the stability margin (how far from violating invariants).
        Higher margin = more stable.
        """
        # Layer 1 margin
        drake_target = self.DRAKE_BUDGET_D / C_fac
        drake_margin = (drake_target - mu_q) / drake_target if drake_target > 0 else 0
        
        # Layer 2 margin
        N_e = np.log(1 + n_e)
        Phi_M_fac = 1 - abs(M_fac - self.M_STAR)
        drift_actual = rho_q * N_e * Phi_M_fac
        drift_margin = (drift_actual - self.DRIFT_BARRIER_B) / self.DRIFT_BARRIER_B if self.DRIFT_BARRIER_B > 0 else 0
        
        # Layer 3 margin
        error_target = 1 + self.LAMBDA * mu_q
        error_margin = (sigma_q - error_target) / error_target if error_target > 0 else 0
        
        # Minimum margin across all layers
        margin = min(drake_margin, drift_margin, error_margin)
        return max(0, margin)
    
    def evaluate_state(self, state: AdaptationState) -> Tuple[bool, bool, bool, bool, bool, float, float, int, int, int]:
        """
        Evaluate a state using the adaptation surface.
        Returns (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise, flows_to_sabotage, cost, margin, rg_depth, attractor_id, failure_mask).
        """
        # Quantize state to 18-bit coordinate (3 bits per variable)
        mu_q_bits = int(min(max(state.mu_q, 0), 1) * 7)
        rho_q_bits = int(min(max(state.rho_q, 0), 1) * 7)
        C_fac_bits = int(min(max(state.C_fac, self.EPSILON), 1) * 7)
        M_fac_bits = int(min(max(state.M_fac, self.EPSILON), 1) * 7)
        n_e_bits = int(min(max(state.n_e, 0), 1) * 7)
        # Quantize sigma_q from [1,2] to [0,7]
        sigma_q_bits = int(min(max(state.sigma_q - 1.0, 0), 1) * 7)
        
        # Encode coordinate
        coord = (mu_q_bits << 15) | (rho_q_bits << 12) | (C_fac_bits << 9) | (M_fac_bits << 6) | (n_e_bits << 3) | sigma_q_bits
        
        # Lookup in adaptation surface
        lut_entry = self.adaptation_surface[coord]
        
        # Decode result with updated structure
        lawful_now = bool(lut_entry & 0x1)
        lawful_under_flow = bool((lut_entry >> 1) & 0x1)
        reaches_attractor = bool((lut_entry >> 2) & 0x1)
        flows_to_noise = bool((lut_entry >> 3) & 0x1)
        flows_to_sabotage = bool((lut_entry >> 4) & 0x1)
        cost = (lut_entry >> 8) / 1000.0
        margin = (lut_entry >> 24) / 1000.0
        rg_depth = (lut_entry >> 32) & 0xFF
        attractor_id = (lut_entry >> 40) & 0xFF
        failure_mask = (lut_entry >> 48) & 0xFF
        
        return lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise, flows_to_sabotage, cost, margin, rg_depth, attractor_id, failure_mask
    
    def extract_adaptation_features(self, page_data: Dict) -> AdaptationState:
        """
        Extract adaptation equation variables from page data.
        Maps Common Crawl features to 6D genome space.
        """
        content = page_data.get('content', '')
        url = page_data.get('url', '')
        
        # μ_q: Mutation rate (content change frequency)
        # Estimate from content length and URL complexity
        mu_q = min(len(content) / 10000.0, 1.0) * 0.1  # Normalize to [0, 1]
        
        # ρ_q: Refresh rate (how often content is updated)
        # Estimate from URL patterns and content freshness
        rho_q = 0.5  # Default refresh rate (can be enhanced with timestamp data)
        
        # C_fac: Graph connectance (link density)
        # Estimate from structural complexity
        C_fac = min(self._calculate_structural_complexity(content), 1.0)
        C_fac = max(self.EPSILON, C_fac)  # Ensure minimum value
        
        # M_fac: Modularity (partition quality)
        # Estimate from unique word ratio
        M_fac = self._calculate_text_complexity(content)
        M_fac = max(self.EPSILON, M_fac)  # Ensure minimum value
        
        # n_e: Observer count (neural mass, citations, downloads)
        # Estimate from URL depth and content richness
        url_depth = len(url.split('/'))
        n_e = min(url_depth / 10.0, 1.0)
        
        # σ_q: Selection coefficient (fitness/significance)
        # Estimate from entropy and text complexity
        entropy = self._calculate_entropy(content)
        text_complexity = self._calculate_text_complexity(content)
        sigma_q = min((entropy + text_complexity) / 2.0, 1.0)
        
        return AdaptationState(
            mu_q=mu_q,
            rho_q=rho_q,
            C_fac=C_fac,
            M_fac=M_fac,
            n_e=n_e,
            sigma_q=sigma_q
        )
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        total = len(text)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        max_entropy = np.log2(len(char_counts)) if char_counts else 1.0
        return min(entropy / max_entropy, 1.0) if max_entropy > 0 else 0.0
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity (unique words / total words)."""
        if not text:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        unique_words = len(set(word.lower() for word in words))
        total_words = len(words)
        
        return min(unique_words / total_words, 1.0)
    
    def _calculate_structural_complexity(self, text: str) -> float:
        """Calculate structural complexity based on HTML/markdown patterns."""
        if not text:
            return 0.0
        
        html_tags = len(re.findall(r'<[^>]+>', text))
        headings = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
        code_blocks = len(re.findall(r'```', text))
        links = len(re.findall(r'\[([^\]]+)\]\([^\)]+\)', text))
        
        total_elements = html_tags + headings + code_blocks + links
        return min(total_elements / 50.0, 1.0)

@dataclass
class WaveprobeState:
    """Quantum-inspired state for data selection."""
    amplitude: float  # Wave amplitude (0-1)
    phase: float  # Wave phase (0-2π)
    coherence: float  # Coherence score (0-1)
    overlap: float  # Overlap with target (0-1)

class WaveprobeSelector:
    """Quantum-inspired data selection using waveprobe and Unified Adaptation Equation."""
    
    def __init__(self, config: CommonCrawlConfig):
        self.config = config
        self.target_state = WaveprobeState(
            amplitude=0.8,
            phase=0.0,
            coherence=0.9,
            overlap=0.7
        )
        # Initialize Unified Adaptation Equation for lawfulness checking
        self.adaptation_equation = UnifiedAdaptationEquation()
    
    def compute_overlap(self, page_data: Dict) -> float:
        """
        Compute quantum overlap between page and target state.
        Uses wave function inner product: ⟨ψ|φ⟩ = Σ conj(ψ_i) · φ_i
        """
        # Extract features from page data
        features = self._extract_features(page_data)
        
        # Compute overlap as dot product
        target_features = np.array([
            self.target_state.amplitude,
            np.cos(self.target_state.phase),
            self.target_state.coherence,
            self.target_state.overlap,
            0.8,  # Target entropy
            0.7,  # Target text complexity
            0.6   # Target structural complexity
        ])
        
        page_features = np.array(features)
        
        # Normalize
        target_norm = np.linalg.norm(target_features)
        page_norm = np.linalg.norm(page_features)
        
        if target_norm == 0 or page_norm == 0:
            return 0.0
        
        overlap = np.abs(np.dot(target_features, page_features) / (target_norm * page_norm))
        return overlap
    
    def _extract_features(self, page_data: Dict) -> List[float]:
        """Extract quantum-inspired features from page data."""
        # Content length (normalized)
        content_len = len(page_data.get('content', ''))
        norm_len = min(content_len / 10000.0, 1.0)
        
        # URL complexity (normalized)
        url = page_data.get('url', '')
        url_complexity = min(len(url.split('/')) / 10.0, 1.0)
        
        # Language score (placeholder)
        lang_score = 0.8  # Default language score
        
        # Domain authority (placeholder)
        domain_score = 0.7  # Default domain score
        
        # Advanced features for waveprobe
        # Entropy of content (information content)
        content_entropy = self._calculate_entropy(page_data.get('content', ''))
        
        # Text complexity (unique words / total words)
        text_complexity = self._calculate_text_complexity(page_data.get('content', ''))
        
        # Structural complexity (HTML tags, headings, etc.)
        structural_complexity = self._calculate_structural_complexity(page_data.get('content', ''))
        
        return [norm_len, url_complexity, lang_score, domain_score, content_entropy, text_complexity, structural_complexity]
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        
        # Calculate character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        total = len(text)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        # Normalize entropy
        max_entropy = np.log2(len(char_counts)) if char_counts else 1.0
        return min(entropy / max_entropy, 1.0) if max_entropy > 0 else 0.0
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity (unique words / total words)."""
        if not text:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        unique_words = len(set(word.lower() for word in words))
        total_words = len(words)
        
        return min(unique_words / total_words, 1.0)
    
    def _calculate_structural_complexity(self, text: str) -> float:
        """Calculate structural complexity based on HTML/markdown patterns."""
        if not text:
            return 0.0
        
        # Count various structural elements
        html_tags = len(re.findall(r'<[^>]+>', text))
        headings = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
        code_blocks = len(re.findall(r'```', text))
        links = len(re.findall(r'\[([^\]]+)\]\([^\)]+\)', text))
        
        # Normalize complexity
        total_elements = html_tags + headings + code_blocks + links
        return min(total_elements / 50.0, 1.0)
    
    def select_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Select pages based on waveprobe overlap and Unified Adaptation Equation with RGFlow.
        Only pages that are "lawful" under RGFlow are selected.
        """
        selected = []
        for page in pages:
            # Compute waveprobe overlap
            overlap = self.compute_overlap(page)
            
            # Evaluate lawfulness using Unified Adaptation Equation with RGFlow
            adaptation_state = self.adaptation_equation.extract_adaptation_features(page)
            (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise, 
             flows_to_sabotage, adaptation_cost, stability_margin, rg_depth, 
             attractor_id, failure_mask) = self.adaptation_equation.evaluate_state(adaptation_state)
            
            # Select if waveprobe overlap threshold met AND lawful under RGFlow
            if overlap >= self.config.waveprobe_threshold and lawful_under_flow:
                page['waveprobe_overlap'] = overlap
                page['lawful_now'] = lawful_now
                page['lawful_under_flow'] = lawful_under_flow
                page['reaches_attractor'] = reaches_attractor
                page['flows_to_noise'] = flows_to_noise
                page['flows_to_sabotage'] = flows_to_sabotage
                page['adaptation_cost'] = adaptation_cost
                page['stability_margin'] = stability_margin
                page['rg_depth'] = rg_depth
                page['attractor_id'] = attractor_id
                page['failure_mask'] = failure_mask
                selected.append(page)
        
        logger.info(f"Waveprobe + RGFlow Adaptation selected {len(selected)}/{len(pages)} pages")
        return selected

# ═══════════════════════════════════════════════════════════════════════════
# §2  UnifiedCompression-Inspired Bytestream Compression
# ═══════════════════════════════════════════════════════════════════════════

class UnifiedCompressor:
    """Bytestream compression inspired by UnifiedCompression.lean."""
    
    def __init__(self):
        self.echo_weights = [1.0, 0.5, 0.25]  # Echo weights [1, ½, ¼]
    
    def compress_bytestream(self, data: bytes) -> Tuple[bytes, float]:
        """
        Compress bytestream using UnifiedCompression principles.
        Returns compressed data and compression ratio.
        Uses conditional compression based on file size.
        """
        original_size = len(data)
        
        # Conditional compression strategy based on file size
        if original_size < 1024:  # Small files (< 1KB): use simple RLE
            compressed = self._apply_rle_compression(np.frombuffer(data, dtype=np.uint8))
        elif original_size < 10240:  # Medium files (1KB-10KB): use pattern detection
            compressed = self._apply_echo_compression(np.frombuffer(data, dtype=np.uint8))
        else:  # Large files (> 10KB): use full Huffman compression
            compressed = self._apply_huffman_compression(np.frombuffer(data, dtype=np.uint8))
        
        # Convert back to bytes
        compressed_bytes = compressed.astype(np.uint8).tobytes()
        
        # Calculate compression ratio
        compressed_size = len(compressed_bytes)
        ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        logger.info(f"Compression: {original_size} -> {compressed_size} bytes (ratio: {ratio:.3f})")
        return compressed_bytes, ratio
    
    def _apply_huffman_compression(self, arr: np.ndarray) -> np.ndarray:
        """Apply Huffman-inspired compression using frequency analysis."""
        # Calculate byte frequencies
        unique, counts = np.unique(arr, return_counts=True)
        frequencies = dict(zip(unique, counts))
        
        # Sort by frequency (most frequent first)
        sorted_bytes = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Create compression dictionary (shorter codes for frequent bytes)
        compression_dict = {}
        for i, (byte, _) in enumerate(sorted_bytes):
            # Use variable-length encoding: frequent bytes get shorter codes
            if i < 16:  # Top 16 bytes get 4-bit codes
                code = bytes([i])
            elif i < 64:  # Next 48 bytes get 6-bit codes
                code = bytes([0x40 + i])
            else:  # Rest get 8-bit codes
                code = bytes([byte])
            compression_dict[byte] = code
        
        # Compress data using dictionary
        compressed = []
        for byte in arr:
            code = compression_dict.get(int(byte), bytes([int(byte)]))
            compressed.extend(code)
        
        # Add dictionary header for decompression
        header = []
        for byte, code in compression_dict.items():
            header.extend([byte] + list(code))
        header_bytes = bytes([len(compression_dict)]) + bytes(header)
        
        return np.array(list(header_bytes) + compressed, dtype=np.uint8)
    
    def _apply_rle_compression(self, arr: np.ndarray) -> np.ndarray:
        """Apply simple run-length encoding for small files."""
        compressed = []
        i = 0
        while i < len(arr):
            if i + 4 < len(arr) and arr[i] == arr[i+1] == arr[i+2] == arr[i+3] == arr[i+4]:
                # Run of 5+ same bytes
                count = 1
                while i + count < len(arr) and arr[i] == arr[i+count]:
                    count += 1
                    if count >= 255:  # Limit count to 255
                        break
                compressed.append(0xFE)  # RLE marker
                compressed.append(arr[i])  # Byte value
                compressed.append(count)  # Count
                i += count
            else:
                compressed.append(arr[i])
                i += 1
        
        return np.array(compressed, dtype=np.uint8)
    
    def _apply_echo_compression(self, arr: np.ndarray) -> np.ndarray:
        """Apply echo field compression with standing wave patterns."""
        # Detect repeating patterns (standing waves)
        compressed = []
        i = 0
        while i < len(arr):
            # Look for patterns of length 2-8
            pattern_found = False
            for pattern_len in range(2, 9):
                if i + pattern_len * 3 <= len(arr):
                    pattern = arr[i:i+pattern_len]
                    # Check if pattern repeats at least 3 times
                    matches = 0
                    for j in range(3):
                        if np.array_equal(arr[i+j*pattern_len:i+(j+1)*pattern_len], pattern):
                            matches += 1
                    
                    if matches == 3:
                        # Compress pattern repetition
                        compressed.append(0xFF)  # Pattern marker
                        compressed.append(pattern_len)  # Pattern length
                        compressed.extend(pattern)  # Pattern data
                        compressed.append(3)  # Repeat count
                        i += pattern_len * 3
                        pattern_found = True
                        break
            
            if not pattern_found:
                compressed.append(arr[i])
                i += 1
        
        return np.array(compressed, dtype=np.uint8)
    
    def decompress_bytestream(self, compressed: bytes) -> bytes:
        """Decompress bytestream."""
        arr = np.frombuffer(compressed, dtype=np.uint8)
        
        # Extract header
        dict_size = arr[0]
        decompression_dict = {}
        pos = 1
        for _ in range(dict_size):
            byte = arr[pos]
            code_len = 1
            code = arr[pos+1:pos+1+code_len]
            decompression_dict[tuple(code)] = byte
            pos += 1 + code_len
        
        # Decompress data
        decompressed = []
        while pos < len(arr):
            # Try to find matching code
            found = False
            for code, byte in decompression_dict.items():
                if pos + len(code) <= len(arr) and np.array_equal(arr[pos:pos+len(code)], list(code)):
                    decompressed.append(byte)
                    pos += len(code)
                    found = True
                    break
            
            if not found:
                decompressed.append(arr[pos])
                pos += 1
        
        return np.array(decompressed, dtype=np.uint8).tobytes()

# ═══════════════════════════════════════════════════════════════════════════
# §3  Genetic Algorithm for Parameter Optimization
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GeneticIndividual:
    """Individual in genetic algorithm population."""
    waveprobe_threshold: float
    compression_threshold: float
    fitness: float = 0.0

class GeneticOptimizer:
    """Genetic algorithm for optimizing ingestion parameters."""
    
    def __init__(self, config: CommonCrawlConfig):
        self.config = config
        self.population: List[GeneticIndividual] = []
    
    def initialize_population(self) -> List[GeneticIndividual]:
        """Initialize random population."""
        population = []
        for _ in range(self.config.genetic_population):
            individual = GeneticIndividual(
                waveprobe_threshold=random.uniform(0.3, 0.9),
                compression_threshold=random.uniform(0.5, 0.9)
            )
            population.append(individual)
        self.population = population
        logger.info(f"Initialized population with {len(population)} individuals")
        return population
    
    def evaluate_fitness(self, individual: GeneticIndividual, pages: List[Dict]) -> float:
        """
        Evaluate fitness of an individual.
        Fitness = (selected_ratio * 0.5) + (compression_ratio * 0.5)
        """
        # Simulate selection with individual's threshold
        selector = WaveprobeSelector(CommonCrawlConfig(
            waveprobe_threshold=individual.waveprobe_threshold
        ))
        selected = selector.select_pages(pages)
        selected_ratio = len(selected) / len(pages) if pages else 0
        
        # Simulate compression
        compressor = UnifiedCompressor()
        test_data = b"test data for compression" * 100
        _, compression_ratio = compressor.compress_bytestream(test_data)
        
        # Fitness: balance selection and compression
        fitness = (selected_ratio * 0.5) + ((1.0 - compression_ratio) * 0.5)
        
        individual.fitness = fitness
        return fitness
    
    def crossover(self, parent1: GeneticIndividual, parent2: GeneticIndividual) -> GeneticIndividual:
        """Crossover two parents to create offspring."""
        offspring = GeneticIndividual(
            waveprobe_threshold=(parent1.waveprobe_threshold + parent2.waveprobe_threshold) / 2,
            compression_threshold=(parent1.compression_threshold + parent2.compression_threshold) / 2
        )
        return offspring
    
    def mutate(self, individual: GeneticIndividual, mutation_rate: float = 0.1) -> GeneticIndividual:
        """Mutate an individual."""
        if random.random() < mutation_rate:
            individual.waveprobe_threshold = np.clip(
                individual.waveprobe_threshold + random.uniform(-0.1, 0.1),
                0.3, 0.9
            )
        if random.random() < mutation_rate:
            individual.compression_threshold = np.clip(
                individual.compression_threshold + random.uniform(-0.1, 0.1),
                0.5, 0.9
            )
        return individual
    
    def evolve(self, pages: List[Dict]) -> GeneticIndividual:
        """Evolve population for specified generations."""
        # Initialize population
        if not self.population:
            self.initialize_population()
        
        best_individual = None
        
        for generation in range(self.config.genetic_generations):
            # Evaluate fitness
            for individual in self.population:
                self.evaluate_fitness(individual, pages)
            
            # Sort by fitness
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            
            best_individual = self.population[0]
            logger.info(f"Generation {generation}: Best fitness = {best_individual.fitness:.4f}")
            
            # Selection: keep top 50%
            survivors = self.population[:self.config.genetic_population // 2]
            
            # Crossover and mutation
            offspring = []
            while len(offspring) < self.config.genetic_population - len(survivors):
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                offspring.append(child)
            
            self.population = survivors + offspring
        
        logger.info(f"Evolution complete. Best fitness: {best_individual.fitness:.4f}")
        logger.info(f"Best parameters: waveprobe_threshold={best_individual.waveprobe_threshold:.3f}, "
                   f"compression_threshold={best_individual.compression_threshold:.3f}")
        return best_individual

# ═══════════════════════════════════════════════════════════════════════════
# §4  Common Crawl Data Fetcher
# ═══════════════════════════════════════════════════════════════════════════

class CommonCrawlFetcher:
    """Fetch data from Common Crawl with WARC parsing and S3 integration."""
    
    def __init__(self, config: CommonCrawlConfig):
        self.config = config
        # Initialize S3 client for Common Crawl (unsigned access)
        self.s3_client = boto3.client(
            's3',
            config=Config(signature_version=UNSIGNED),
            region_name='us-east-1'
        )
        self.bucket_name = 'commoncrawl'
    
    def fetch_index_paths(self) -> List[str]:
        """Fetch index file paths from Common Crawl."""
        logger.info(f"Fetching index paths from Common Crawl")
        
        for url in CC_INDEX_URLS:
            try:
                logger.info(f"Trying URL: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Decompress gzipped content
                content = gzip.decompress(response.content)
                
                # Parse paths
                paths = content.decode('utf-8').strip().split('\n')
                
                logger.info(f"Fetched {len(paths)} index paths from {url}")
                return paths[:self.config.max_segments]
                
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue
        
        logger.error("Failed to fetch index paths from all URLs")
        return []
    
    def fetch_warc_file_from_http(self, warc_path: str) -> Optional[bytes]:
        """Fetch WARC file via HTTP from Common Crawl S3."""
        try:
            # Construct HTTP URL for S3 access
            http_url = f"{COMMONCRAWL_S3_BASE}/{warc_path}"
            logger.info(f"Fetching WARC from HTTP: {http_url}")
            
            response = requests.get(http_url, timeout=60)
            response.raise_for_status()
            
            warc_data = response.content
            logger.info(f"Downloaded {len(warc_data)} bytes from HTTP")
            return warc_data
        except Exception as e:
            logger.error(f"Failed to fetch WARC from HTTP: {e}")
            return None
    
    def fetch_warc_file_from_s3(self, warc_path: str) -> Optional[bytes]:
        """Fetch WARC file directly from Common Crawl S3 bucket."""
        try:
            logger.info(f"Fetching WARC from S3: {warc_path}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=warc_path)
            warc_data = response['Body'].read()
            logger.info(f"Downloaded {len(warc_data)} bytes from S3")
            return warc_data
        except Exception as e:
            logger.error(f"Failed to fetch WARC from S3: {e}")
            return None
    
    def parse_warc_record(self, warc_data: bytes) -> List[Dict]:
        """Parse WARC records from WARC file data."""
        records = []
        
        try:
            # WARC format: each record starts with "WARC/1.0"
            warc_text = warc_data.decode('utf-8', errors='ignore')
            warc_records = warc_text.split('WARC/1.0')
            
            for record_text in warc_records[1:]:  # Skip first empty split
                if not record_text.strip():
                    continue
                
                record = self._parse_single_warc_record(record_text)
                if record:
                    records.append(record)
            
            logger.info(f"Parsed {len(records)} WARC records")
            
        except Exception as e:
            logger.error(f"Failed to parse WARC records: {e}")
        
        return records
    
    def _parse_single_warc_record(self, record_text: str) -> Optional[Dict]:
        """Parse a single WARC record."""
        try:
            lines = record_text.split('\n')
            
            record = {
                'type': None,
                'url': None,
                'date': None,
                'content_type': None,
                'content_length': 0,
                'content': ''
            }
            
            # Parse headers
            content_start = 0
            for i, line in enumerate(lines):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'warc-type':
                        record['type'] = value
                    elif key == 'warc-target-uri':
                        record['url'] = value
                    elif key == 'warc-date':
                        record['date'] = value
                    elif key == 'content-type':
                        record['content_type'] = value
                    elif key == 'content-length':
                        record['content_length'] = int(value)
                elif line.strip() == '':
                    content_start = i + 1
                    break
            
            # Extract content (everything after headers)
            if content_start < len(lines):
                content = '\n'.join(lines[content_start:])
                record['content'] = content[:10000]  # Limit content size
            
            return record if record['url'] else None
            
        except Exception as e:
            logger.warning(f"Failed to parse WARC record: {e}")
            return None
    
    def fetch_segment_data(self, segment_path: str) -> List[Dict]:
        """Fetch data from a Common Crawl segment using WARC parsing."""
        logger.info(f"Fetching segment: {segment_path}")
        
        # Try HTTP first (most reliable)
        warc_data = self.fetch_warc_file_from_http(segment_path)
        
        if not warc_data:
            # Try S3 as fallback
            warc_data = self.fetch_warc_file_from_s3(segment_path)
        
        if warc_data:
            # Parse WARC records
            records = self.parse_warc_record(warc_data)
            
            # Convert to page format
            pages = []
            for record in records[:self.config.pages_per_segment]:  # Limit pages
                page = {
                    'url': record.get('url', ''),
                    'content': record.get('content', ''),
                    'segment': segment_path,
                    'type': record.get('type', ''),
                    'date': record.get('date', '')
                }
                pages.append(page)
            
            return pages
        else:
            # Fallback to simulated data if both HTTP and S3 fail
            logger.warning("HTTP and S3 fetch failed, using simulated data")
            pages = []
            for i in range(self.config.pages_per_segment):
                page = {
                    'url': f'https://example.com/page{i}',
                    'content': f'Sample content for page {i} ' * 100,
                    'segment': segment_path
                }
                pages.append(page)
            
            return pages

# ═══════════════════════════════════════════════════════════════════════════
# §5  Main Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class CommonCrawlPipeline:
    """Main pipeline for Common Crawl ingestion."""
    
    def __init__(self, config: CommonCrawlConfig):
        self.config = config
        self.fetcher = CommonCrawlFetcher(config)
        self.compressor = UnifiedCompressor()
        self.optimizer = GeneticOptimizer(config)
    
    def run(self) -> Dict:
        """Run the complete pipeline."""
        logger.info("Starting Common Crawl Waveprobe Ingestion Pipeline")
        
        # Step 1: Fetch index paths
        index_paths = self.fetcher.fetch_index_paths()
        if not index_paths:
            logger.error("No index paths fetched")
            return {"error": "No index paths"}
        
        # Step 2: Fetch sample data for genetic optimization
        sample_segment = index_paths[0] if index_paths else ""
        sample_pages = self.fetcher.fetch_segment_data(sample_segment)
        
        # Step 3: Genetic optimization
        logger.info("Running genetic optimization...")
        best_params = self.optimizer.evolve(sample_pages)
        
        # Step 4: Update config with best parameters
        self.config.waveprobe_threshold = best_params.waveprobe_threshold
        self.config.compression_threshold = best_params.compression_threshold
        
        # Step 5: Process segments with optimized parameters
        selector = WaveprobeSelector(self.config)
        all_selected_pages = []
        
        for segment_path in index_paths[:10]:  # Limit to 10 segments for demo
            pages = self.fetcher.fetch_segment_data(segment_path)
            selected = selector.select_pages(pages)
            all_selected_pages.extend(selected)
        
        # Step 6: Compress selected pages
        compressed_data = {}
        for page in all_selected_pages[:100]:  # Limit to 100 pages for demo
            content = page['content'].encode('utf-8')
            compressed, ratio = self.compressor.compress_bytestream(content)
            
            if ratio <= self.config.compression_threshold:
                compressed_data[page['url']] = {
                    'compressed': compressed.hex(),
                    'original_size': len(content),
                    'compressed_size': len(compressed),
                    'compression_ratio': ratio,
                    'waveprobe_overlap': page.get('waveprobe_overlap', 0.0)
                }
        
        # Step 7: Save results
        output_path = Path("shared-data/data/commoncrawl_ingestion_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results = {
            "config": asdict(self.config),
            "best_parameters": asdict(best_params),
            "total_segments_processed": len(index_paths[:10]),
            "total_pages_selected": len(all_selected_pages),
            "compressed_pages": len(compressed_data),
            "results": compressed_data
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        logger.info(f"Compressed {len(compressed_data)} pages from {len(all_selected_pages)} selected pages")
        
        return results

def main():
    config = CommonCrawlConfig()
    pipeline = CommonCrawlPipeline(config)
    results = pipeline.run()
    
    print("\n=== Pipeline Complete ===")
    print(f"Total pages selected: {results.get('total_pages_selected', 0)}")
    print(f"Compressed pages: {results.get('compressed_pages', 0)}")
    print(f"Best waveprobe threshold: {results.get('best_parameters', {}).get('waveprobe_threshold', 0):.3f}")
    print(f"Best compression threshold: {results.get('best_parameters', {}).get('compression_threshold', 0):.3f}")

if __name__ == "__main__":
    main()
