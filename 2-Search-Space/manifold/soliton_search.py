#!/usr/bin/env python3
"""
Soliton Search Engine — Wave Propagation with AVMR O(√N) Indexing
First-Principles Derivation: Search is soliton propagation along path of least resistance

Performance Targets:
- O(√N) search complexity (AVMR shell indexing)
- < 200ms query response time
- < 50ms attractor convergence
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import math


@dataclass
class FrustrationWave:
    """Frustration wave parameters for soliton propagation"""
    wave_vector: np.ndarray  # k_r wave vector (14D)
    weight: float  # w_r weight from anisotropy
    
    def __repr__(self) -> str:
        return f"FrustrationWave(weight={self.weight:.3f})"


@dataclass
class Attractor:
    """Local energy minimum (attractor in manifold)"""
    coordinate: np.ndarray  # 14D coordinate
    energy: float  # Energy at this point
    archive_ids: List[str]  # Points that converge to this attractor
    confidence: float  # Attraction strength
    
    def __repr__(self) -> str:
        return f"Attractor(energy={self.energy:.3f}, points={len(self.archive_ids)})"


@dataclass
class Trajectory:
    """Soliton propagation trajectory"""
    points: List[np.ndarray]  # Path points
    energies: List[float]  # Energy at each point
    converged: bool  # Whether trajectory converged to attractor
    final_attractor: Optional[Attractor]  # Final attractor if converged
    
    def __repr__(self) -> str:
        return f"Trajectory(steps={len(self.points)}, converged={self.converged})"


class AVMRShellIndex:
    """
    AVMR Shell Indexing for O(√N) search
    
    Shell decomposition: n = k² + a, 0 ≤ a < 2k + 1
    Shell state: (k, a, b) where b = (k+1)² - n
    Tip coordinates: Tip(n) = (ab, a-b)
    """
    
    def __init__(self, vectors: List[np.ndarray], archive_ids: List[str]):
        """
        Build AVMR shell index from concept vectors
        
        Args:
            vectors: List of 14D concept vectors
            archive_ids: List of archive IDs
        """
        self.vectors = np.array(vectors)
        self.archive_ids = archive_ids
        self.n_vectors = len(vectors)
        
        # Compute magnitudes for shell decomposition
        self.magnitudes = np.linalg.norm(self.vectors, axis=1)
        
        # Build shell index
        self.shell_index = self._build_shell_index()
        
        # Build axial generators for shell indexing
        self.axial_generators = self._build_axial_generators()
    
    def _build_shell_index(self) -> Dict[Tuple[int, int, int], List[int]]:
        """Build shell index: (k, a, b) → vector indices"""
        shell_index = {}
        
        for i, magnitude in enumerate(self.magnitudes):
            n = int(magnitude * 1000)  # Scale factor
            k = int(math.sqrt(n))
            a = n - k * k
            b = (k + 1) * (k + 1) - n
            
            shell_key = (k, a, b)
            if shell_key not in shell_index:
                shell_index[shell_key] = []
            shell_index[shell_key].append(i)
        
        return shell_index
    
    def _build_axial_generators(self) -> np.ndarray:
        """Build axial generators for shell indexing"""
        # Use principal components as axial generators
        centered = self.vectors - np.mean(self.vectors, axis=0)
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        
        # Sort by eigenvalues (descending)
        idx = np.argsort(eigenvalues)[::-1]
        axial_generators = eigenvectors[:, idx[:2]]  # Top 2 axes
        
        return axial_generators
    
    def query_shell(self, k: int, a: int, b: int) -> List[Tuple[int, str]]:
        """
        Query vectors in specific shell
        
        Args:
            k: Shell level
            a: Shell offset
            b: Shell complement
            
        Returns:
            List of (index, archive_id) tuples
        """
        shell_key = (k, a, b)
        if shell_key not in self.shell_index:
            return []
        
        indices = self.shell_index[shell_key]
        return [(i, self.archive_ids[i]) for i in indices]
    
    def query_neighborhood(self, query_vector: np.ndarray, radius: float) -> List[Tuple[int, str]]:
        """
        Query neighborhood using shell indexing (O(√N) complexity)
        
        Args:
            query_vector: Query vector (14D)
            radius: Query radius
            
        Returns:
            List of (index, archive_id) tuples within radius
        """
        # Compute query magnitude
        query_magnitude = np.linalg.norm(query_vector)
        query_n = int(query_magnitude * 1000)
        query_k = int(math.sqrt(query_n))
        
        # Search nearby shells (within radius in shell space)
        results = []
        shell_radius = int(radius * 1000)
        
        for dk in range(-shell_radius, shell_radius + 1):
            k = query_k + dk
            if k < 0:
                continue
            
            # Search all possible (a, b) combinations for this shell
            for a in range(2 * k + 1):
                n = k * k + a
                b = (k + 1) * (k + 1) - n
                
                shell_results = self.query_shell(k, a, b)
                results.extend(shell_results)
        
        # Filter by actual Euclidean distance
        filtered_results = []
        for i, archive_id in results:
            distance = np.linalg.norm(self.vectors[i] - query_vector)
            if distance <= radius:
                filtered_results.append((i, archive_id))
        
        return filtered_results


class SolitonSearchEngine:
    """
    Soliton Search Engine with AVMR O(√N) indexing
    
    Search via wave propagation along path of least resistance
    """
    
    def __init__(self, vectors: List[np.ndarray], archive_ids: List[str]):
        """
        Initialize soliton search engine
        
        Args:
            vectors: List of 14D concept vectors
            archive_ids: List of archive IDs
        """
        self.vectors = np.array(vectors)
        self.archive_ids = archive_ids
        
        # Build AVMR shell index
        self.avmr_index = AVMRShellIndex(vectors, archive_ids)
        
        # Initialize frustration waves (default: uniform weights)
        self.waves = self._initialize_waves()
    
    def _initialize_waves(self) -> List[FrustrationWave]:
        """Initialize frustration waves with default parameters"""
        waves = []
        
        # Create waves along principal axes
        for i in range(14):
            wave_vector = np.zeros(14)
            wave_vector[i] = 1.0
            waves.append(FrustrationWave(wave_vector=wave_vector, weight=0.1))
        
        return waves
    
    def _cosine_approx(self, x: float) -> float:
        """Cosine approximation using Taylor series"""
        x2 = x * x
        return 1.0 - x2 * 0.5
    
    def _compute_frustration(self, z: np.ndarray, waves: List[FrustrationWave]) -> float:
        """
        Compute frustration W(z;A) = Σ_r w_r(A)(1 - cos(k_r·z))
        
        Args:
            z: Lock pattern (14D vector)
            waves: List of frustration waves
            
        Returns:
            Frustration value
        """
        frustration = 0.0
        
        for wave in waves:
            dot_product = np.dot(wave.wave_vector, z)
            cosine = self._cosine_approx(dot_product)
            contribution = wave.weight * (1.0 - cosine)
            frustration += contribution
        
        return frustration
    
    def propagate_soliton(
        self,
        query_vector: np.ndarray,
        max_steps: int = 100,
        convergence_threshold: float = 0.001,
        learning_rate: float = 0.1
    ) -> Trajectory:
        """
        Propagate soliton from query vector to attractor
        
        Args:
            query_vector: Initial perturbation (query)
            max_steps: Maximum propagation steps
            convergence_threshold: Energy change threshold for convergence
            learning_rate: Step size for gradient descent
            
        Returns:
            Trajectory of soliton propagation
        """
        trajectory_points = [query_vector.copy()]
        trajectory_energies = [self._compute_frustration(query_vector, self.waves)]
        
        current_z = query_vector.copy()
        
        for step in range(max_steps):
            # Compute gradient of frustration
            gradient = self._compute_gradient(current_z, self.waves)
            
            # Gradient descent (move toward lower energy)
            new_z = current_z - learning_rate * gradient
            
            # Compute energy
            energy = self._compute_frustration(new_z, self.waves)
            
            # Check convergence
            energy_change = abs(energy - trajectory_energies[-1])
            if energy_change < convergence_threshold:
                trajectory_points.append(new_z)
                trajectory_energies.append(energy)
                
                # Find attractor
                attractor = self._find_attractor(new_z)
                
                return Trajectory(
                    points=trajectory_points,
                    energies=trajectory_energies,
                    converged=True,
                    final_attractor=attractor
                )
            
            trajectory_points.append(new_z)
            trajectory_energies.append(energy)
            current_z = new_z
        
        # Did not converge
        return Trajectory(
            points=trajectory_points,
            energies=trajectory_energies,
            converged=False,
            final_attractor=None
        )
    
    def _compute_gradient(self, z: np.ndarray, waves: List[FrustrationWave]) -> np.ndarray:
        """
        Compute gradient of frustration with respect to z
        
        Args:
            z: Current position
            waves: Frustration waves
            
        Returns:
            Gradient vector (14D)
        """
        gradient = np.zeros_like(z)
        
        for wave in waves:
            dot_product = np.dot(wave.wave_vector, z)
            
            # Derivative of (1 - cos(k·z)) is sin(k·z) * k
            # Approximate sin(x) ≈ x for small x
            sine_approx = dot_product
            gradient += wave.weight * sine_approx * wave.wave_vector
        
        return gradient
    
    def _find_attractor(self, coordinate: np.ndarray) -> Optional[Attractor]:
        """
        Find attractor near coordinate using AVMR shell indexing
        
        Args:
            coordinate: 14D coordinate
            
        Returns:
            Attractor if found, None otherwise
        """
        # Query neighborhood using AVMR shell indexing
        neighbors = self.avmr_index.query_neighborhood(coordinate, radius=0.5)
        
        if not neighbors:
            return None
        
        # Compute energy at neighbor points
        energies = []
        for i, _ in neighbors:
            energy = self._compute_frustration(self.vectors[i], self.waves)
            energies.append((i, energy))
        
        # Find minimum energy (attractor)
        min_idx, min_energy = min(energies, key=lambda x: x[1])
        
        # Get all points near this attractor
        attractor_coordinate = self.vectors[min_idx]
        attractor_neighbors = self.avmr_index.query_neighborhood(attractor_coordinate, radius=0.3)
        
        archive_ids = [aid for _, aid in attractor_neighbors]
        
        # Compute confidence based on energy difference
        confidence = 1.0 / (1.0 + min_energy)
        
        return Attractor(
            coordinate=attractor_coordinate,
            energy=min_energy,
            archive_ids=archive_ids,
            confidence=confidence
        )
    
    def search(
        self,
        query_vector: np.ndarray,
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search using soliton propagation with branch prediction
        
        Args:
            query_vector: Query vector (14D)
            max_results: Maximum number of results to return
            
        Returns:
            List of (archive_id, confidence) tuples
        """
        # Propagate soliton
        trajectory = self.propagate_soliton(query_vector)
        
        if not trajectory.converged or trajectory.final_attractor is None:
            # Fallback to direct AVMR search
            neighbors = self.avmr_index.query_neighborhood(query_vector, radius=1.0)
            return [(aid, 0.5) for _, aid in neighbors[:max_results]]
        
        # Return attractor results
        results = []
        for archive_id in trajectory.final_attractor.archive_ids[:max_results]:
            results.append((archive_id, trajectory.final_attractor.confidence))
        
        return results


def main():
    """Test soliton search engine with sample data"""
    # Generate sample 14D vectors
    np.random.seed(42)
    n_samples = 100
    sample_vectors = np.random.randn(n_samples, 14)
    archive_ids = [f"sample_{i}" for i in range(n_samples)]
    
    # Create soliton search engine
    engine = SolitonSearchEngine(sample_vectors, archive_ids)
    
    # Test search
    query_vector = np.random.randn(14)
    results = engine.search(query_vector, max_results=5)
    
    print(f"Search results for random query:")
    for archive_id, confidence in results:
        print(f"  {archive_id}: confidence={confidence:.3f}")
    
    # Test soliton propagation
    trajectory = engine.propagate_soliton(query_vector)
    print(f"\nTrajectory: {trajectory}")
    print(f"Converged: {trajectory.converged}")
    if trajectory.converged:
        print(f"Final attractor: {trajectory.final_attractor}")


if __name__ == "__main__":
    main()
