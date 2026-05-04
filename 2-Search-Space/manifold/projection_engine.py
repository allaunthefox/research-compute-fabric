#!/usr/bin/env python3
"""
Manifold Projection Engine — 14D Concept Vector to 2D Projection
First-Principles Derivation: Files are n-space vectors, not locations

Projection Methods:
- tSNE: t-Distributed Stochastic Neighbor Embedding
- UMAP: Uniform Manifold Approximation and Projection
- PCA: Principal Component Analysis
- ManifoldChart: Custom manifold-based projection

Performance Targets:
- < 100ms coordinate transformation latency
- 60 FPS projection rendering (GPU-accelerated)
- < 50ms neighborhood query (AVMR O(√N))
"""

import numpy as np
from typing import List, Tuple, Optional, Literal
from dataclasses import dataclass
from enum import Enum


class ProjectionMethod(Enum):
    """Available projection methods for 14D → 2D transformation"""
    T_SNE = "tSNE"
    UMAP = "UMAP"
    PCA = "PCA"
    MANIFOLD_CHART = "ManifoldChart"


@dataclass
class ConceptVector14:
    """14-dimensional concept vector from ENE database"""
    vector: np.ndarray  # Shape: (14,)
    archive_id: str
    
    def __post_init__(self):
        if self.vector.shape != (14,):
            raise ValueError(f"ConceptVector14 must have shape (14,), got {self.vector.shape}")
    
    def __repr__(self) -> str:
        return f"ConceptVector14(archive_id={self.archive_id}, vector=...)"


@dataclass
class ProjectedPoint:
    """2D projected point from 14D concept vector"""
    x: float
    y: float
    archive_id: str
    original_vector: np.ndarray
    confidence: float  # Projection confidence (0-1)
    
    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "archive_id": self.archive_id,
            "confidence": self.confidence
        }


class ProjectionEngine:
    """
    14D → 2D Projection Engine
    
    Transforms concept vectors from ENE database into 2D coordinates
    for manifold navigation interface.
    """
    
    def __init__(self, method: ProjectionMethod = ProjectionMethod.PCA):
        self.method = method
        self.fitted = False
        self._projection_matrix = None
        self._mean = None
        self._umap_model = None
        
    def fit(self, vectors: List[ConceptVector14]) -> None:
        """
        Fit projection model to dataset
        
        Args:
            vectors: List of 14D concept vectors
        """
        if not vectors:
            raise ValueError("Cannot fit on empty dataset")
        
        # Convert to numpy array
        data = np.array([v.vector for v in vectors])
        
        if self.method == ProjectionMethod.PCA:
            self._fit_pca(data)
        elif self.method == ProjectionMethod.T_SNE:
            self._fit_tsne(data)
        elif self.method == ProjectionMethod.UMAP:
            self._fit_umap(data)
        elif self.method == ProjectionMethod.MANIFOLD_CHART:
            self._fit_manifold_chart(data)
        else:
            raise ValueError(f"Unknown projection method: {self.method}")
        
        self.fitted = True
    
    def _fit_pca(self, data: np.ndarray) -> None:
        """Fit PCA projection"""
        # Center data
        self._mean = np.mean(data, axis=0)
        centered = data - self._mean
        
        # Compute covariance matrix
        cov = np.cov(centered.T)
        
        # Compute eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        
        # Sort by eigenvalues (descending)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, idx]
        
        # Take top 2 components
        self._projection_matrix = eigenvectors[:, :2]
    
    def _fit_tsne(self, data: np.ndarray) -> None:
        """Fit t-SNE projection (simplified for performance)"""
        # For now, use PCA as fallback
        # Full t-SNE would require scikit-learn
        self._fit_pca(data)
    
    def _fit_umap(self, data: np.ndarray) -> None:
        """Fit UMAP projection (simplified for performance)"""
        # For now, use PCA as fallback
        # Full UMAP would require umap-learn
        self._fit_pca(data)
    
    def _fit_manifold_chart(self, data: np.ndarray) -> None:
        """Fit custom manifold-based projection"""
        # Use first 2 dimensions as baseline
        # In full implementation, this would use manifold learning
        self._projection_matrix = np.eye(14)[:, :2]
        self._mean = np.mean(data, axis=0)
    
    def transform(self, vectors: List[ConceptVector14]) -> List[ProjectedPoint]:
        """
        Transform 14D vectors to 2D projected points
        
        Args:
            vectors: List of 14D concept vectors
            
        Returns:
            List of 2D projected points
        """
        if not self.fitted:
            raise RuntimeError("Projection engine not fitted. Call fit() first.")
        
        # Convert to numpy array
        data = np.array([v.vector for v in vectors])
        
        # Apply projection
        if self.method in [ProjectionMethod.PCA, ProjectionMethod.MANIFOLD_CHART]:
            centered = data - self._mean
            projected = centered @ self._projection_matrix
        else:
            # For tSNE/UMAP, use PCA fallback
            centered = data - self._mean
            projected = centered @ self._projection_matrix
        
        # Create projected points
        points = []
        for i, v in enumerate(vectors):
            confidence = self._compute_confidence(v.vector)
            point = ProjectedPoint(
                x=float(projected[i, 0]),
                y=float(projected[i, 1]),
                archive_id=v.archive_id,
                original_vector=v.vector,
                confidence=confidence
            )
            points.append(point)
        
        return points
    
    def _compute_confidence(self, vector: np.ndarray) -> float:
        """
        Compute projection confidence based on reconstruction error
        
        Args:
            vector: 14D concept vector
            
        Returns:
            Confidence score (0-1)
        """
        if not self.fitted:
            return 0.5
        
        # Project to 2D
        centered = vector - self._mean
        projected = centered @ self._projection_matrix
        
        # Reconstruct (simplified)
        reconstructed = projected @ self._projection_matrix.T + self._mean
        
        # Compute reconstruction error
        error = np.linalg.norm(vector - reconstructed)
        
        # Convert to confidence (lower error = higher confidence)
        confidence = 1.0 / (1.0 + error)
        
        return float(confidence)
    
    def fit_transform(self, vectors: List[ConceptVector14]) -> List[ProjectedPoint]:
        """
        Fit model and transform in one step
        
        Args:
            vectors: List of 14D concept vectors
            
        Returns:
            List of 2D projected points
        """
        self.fit(vectors)
        return self.transform(vectors)
    
    def get_slice_axes(self, axes: Tuple[int, int]) -> 'ProjectionEngine':
        """
        Get projection for specific 14D axes slice
        
        Args:
            axes: Tuple of 2 axes to display (0-13)
            
        Returns:
            New projection engine with slice configuration
        """
        # Create new engine with slice configuration
        new_engine = ProjectionEngine(self.method)
        new_engine._slice_axes = axes
        return new_engine


class NeighborhoodQuery:
    """
    Neighborhood query using AVMR shell indexing for O(√N) search
    """
    
    def __init__(self, projected_points: List[ProjectedPoint]):
        self.points = projected_points
        self._build_index()
    
    def _build_index(self) -> None:
        """Build spatial index for efficient neighborhood queries"""
        # For now, use simple numpy array
        # In full implementation, use AVMR shell indexing
        self.coordinates = np.array([[p.x, p.y] for p in self.points])
        self.archive_ids = [p.archive_id for p in self.points]
    
    def query(self, x: float, y: float, radius: float) -> List[ProjectedPoint]:
        """
        Query neighborhood around coordinate
        
        Args:
            x: X coordinate
            y: Y coordinate
            radius: Query radius
            
        Returns:
            List of projected points within radius
        """
        if not hasattr(self, 'coordinates'):
            return []
        
        # Compute distances
        distances = np.sqrt(
            (self.coordinates[:, 0] - x) ** 2 +
            (self.coordinates[:, 1] - y) ** 2
        )
        
        # Filter by radius
        mask = distances <= radius
        indices = np.where(mask)[0]
        
        # Return points
        return [self.points[i] for i in indices]
    
    def query_k_nearest(self, x: float, y: float, k: int) -> List[ProjectedPoint]:
        """
        Query k nearest neighbors
        
        Args:
            x: X coordinate
            y: Y coordinate
            k: Number of neighbors
            
        Returns:
            List of k nearest projected points
        """
        if not hasattr(self, 'coordinates'):
            return []
        
        # Compute distances
        distances = np.sqrt(
            (self.coordinates[:, 0] - x) ** 2 +
            (self.coordinates[:, 1] - y) ** 2
        )
        
        # Get k smallest indices
        k = min(k, len(self.points))
        indices = np.argpartition(distances, k)[:k]
        
        # Sort by distance
        sorted_indices = indices[np.argsort(distances[indices])]
        
        # Return points
        return [self.points[i] for i in sorted_indices]


def load_concept_vectors_from_ene(db_path: str) -> List[ConceptVector14]:
    """
    Load concept vectors from ENE database
    
    Args:
        db_path: Path to ENE database
        
    Returns:
        List of 14D concept vectors
    """
    import sqlite3
    
    vectors = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query concept vectors from packages table
        cursor.execute("""
            SELECT archive_id, concept_vector_14
            FROM packages
            WHERE concept_vector_14 IS NOT NULL
        """)
        
        for row in cursor.fetchall():
            archive_id, vector_str = row
            
            # Parse vector string (assuming JSON format)
            import json
            vector_data = json.loads(vector_str)
            vector = np.array(vector_data, dtype=np.float32)
            
            if len(vector) != 14:
                continue  # Skip invalid vectors
            
            vectors.append(ConceptVector14(vector=vector, archive_id=archive_id))
        
        conn.close()
        
    except Exception as e:
        print(f"Error loading concept vectors: {e}")
    
    return vectors


def main():
    """Test projection engine with sample data"""
    # Generate sample 14D vectors
    np.random.seed(42)
    n_samples = 100
    sample_vectors = np.random.randn(n_samples, 14)
    
    # Create ConceptVector14 objects
    vectors = [
        ConceptVector14(vector=sample_vectors[i], archive_id=f"sample_{i}")
        for i in range(n_samples)
    ]
    
    # Create projection engine
    engine = ProjectionEngine(method=ProjectionMethod.PCA)
    
    # Fit and transform
    projected = engine.fit_transform(vectors)
    
    # Print results
    print(f"Projected {len(projected)} points")
    print(f"First 5 points:")
    for p in projected[:5]:
        print(f"  {p.archive_id}: ({p.x:.2f}, {p.y:.2f}) confidence={p.confidence:.2f}")
    
    # Test neighborhood query
    neighborhood = NeighborhoodQuery(projected)
    neighbors = neighborhood.query(0.0, 0.0, radius=1.0)
    print(f"\nNeighbors of (0, 0) within radius 1.0: {len(neighbors)}")
    
    # Test k-nearest
    k_nearest = neighborhood.query_k_nearest(0.0, 0.0, k=5)
    print(f"\n5 nearest neighbors of (0, 0):")
    for p in k_nearest:
        print(f"  {p.archive_id}: ({p.x:.2f}, {p.y:.2f})")


if __name__ == "__main__":
    main()
