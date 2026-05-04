"""
GeoWeird Self-Typing Bridge - CORRECTED VERSION

FIXED: Feature extraction now actually inspects constraints.
Previously all extractors returned constants (0.0, 0.5, False, 1.0).

This made every domain produce identical ConstraintFeatures.
The Lighthouse Keeper and "Keeper's Dream" were indistinguishable.
Self-typing was not actually happening.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ConstraintType(Enum):
    """Types of constraints that can be analyzed"""
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    CYCLIC = "cyclic"
    HIERARCHICAL = "hierarchical"
    CAUSAL = "causal"
    METRIC = "metric"
    INFORMATIONAL = "informational"
    ENERGETIC = "energetic"


@dataclass
class Constraint:
    """A constraint with actual structure to analyze"""
    name: str
    constraint_type: ConstraintType
    parameters: List[float]


@dataclass
class ConstraintFeatures:
    """Geometric features extracted from constraints"""
    mean_curvature: float = 0.0
    curvature_variance: float = 0.0
    rotational_symmetry: float = 0.0
    translational_symmetry: float = 0.0
    has_temporal_ordering: bool = False
    causal_cone_angle: float = 0.0
    is_compact: bool = False
    fundamental_group_rank: int = 1
    volume_growth_rate: float = 1.0
    positive_dimensions: int = 3
    negative_dimensions: int = 0


# ================================================================================
# ACTUAL FEATURE EXTRACTORS (NOT CONSTANT STUBS)
# ================================================================================

def estimate_mean_curvature(constraints: List[Constraint]) -> float:
    """
    Estimate mean curvature from constraint topology.
    
    Tree-like structures (hierarchical) → negative curvature
    Cyclic structures → positive curvature
    Linear structures → zero curvature
    """
    if not constraints:
        return 0.0
    
    tree_count = sum(1 for c in constraints 
                     if c.constraint_type == ConstraintType.HIERARCHICAL)
    cyclic_count = sum(1 for c in constraints 
                       if c.constraint_type == ConstraintType.CYCLIC)
    total = len(constraints)
    
    # Tree-like → negative, Cyclic → positive
    tree_ratio = tree_count / total
    cyclic_ratio = cyclic_count / total
    return (cyclic_ratio - tree_ratio) * 2.0  # Scale to [-2, 2]


def estimate_curvature_variance(constraints: List[Constraint]) -> float:
    """How mixed are the constraint types?"""
    if not constraints:
        return 0.0
    
    types = set(c.constraint_type for c in constraints)
    if len(types) <= 1:
        return 0.0
    
    return len(types) / 8.0  # Normalize by max types


def detect_rotational_symmetry(constraints: List[Constraint]) -> float:
    """
    Detect rotational symmetry from cyclic constraints.
    
    High if many cyclic/rotational constraints
    Low if mostly linear/hierarchical
    """
    if not constraints:
        return 0.0
    
    cyclic_constraints = [c for c in constraints 
                          if c.constraint_type in 
                          (ConstraintType.CYCLIC, ConstraintType.SPATIAL)]
    
    ratio = len(cyclic_constraints) / len(constraints)
    
    # Weight by actual rotation parameters if available
    rotation_strength = 0.0
    for c in cyclic_constraints:
        if c.parameters:
            rotation_strength += c.parameters[0] / 360.0
    
    return min(1.0, ratio * 0.7 + rotation_strength * 0.3)


def detect_translational_symmetry(constraints: List[Constraint]) -> float:
    """Detect translational symmetry from spatial/metric constraints"""
    if not constraints:
        return 0.0
    
    spatial_constraints = [c for c in constraints 
                           if c.constraint_type in 
                           (ConstraintType.SPATIAL, ConstraintType.METRIC)]
    
    ratio = len(spatial_constraints) / len(constraints)
    
    # Check for uniform spacing (translational symmetry indicator)
    has_uniform_spacing = any(
        len(c.parameters) >= 2 and abs(c.parameters[0] - c.parameters[1]) < 10.0
        for c in spatial_constraints
    )
    
    if has_uniform_spacing:
        return min(1.0, ratio + 0.2)
    return ratio


def detect_temporal_ordering(constraints: List[Constraint]) -> bool:
    """Detect temporal ordering from temporal/causal constraints"""
    return any(c.constraint_type in (ConstraintType.TEMPORAL, ConstraintType.CAUSAL)
               for c in constraints)


def estimate_causal_cone_angle(constraints: List[Constraint]) -> float:
    """Estimate causal cone angle from temporal density"""
    temporal_count = sum(1 for c in constraints 
                         if c.constraint_type == ConstraintType.TEMPORAL)
    causal_count = sum(1 for c in constraints 
                       if c.constraint_type == ConstraintType.CAUSAL)
    
    total_relevant = temporal_count + causal_count
    if total_relevant == 0:
        return 0.0
    
    # Scale to [0, π/2]
    density = total_relevant / len(constraints)
    return density * 1.57  # π/2 ≈ 1.57


def detect_compactness(constraints: List[Constraint]) -> bool:
    """Detect compactness: bounded vs unbounded domains"""
    spatial_metric = [c for c in constraints 
                      if c.constraint_type in (ConstraintType.SPATIAL, ConstraintType.METRIC)]
    
    # Check if all spatial/metric constraints have bounded parameters
    all_bounded = all(
        all(p < 1000.0 for p in c.parameters)
        for c in spatial_metric
    )
    
    # Compact if bounded AND not too many constraints
    return all_bounded and len(constraints) < 10


def estimate_fundamental_group(constraints: List[Constraint]) -> int:
    """Estimate fundamental group rank from constraint topology"""
    hierarchical = [c for c in constraints 
                    if c.constraint_type == ConstraintType.HIERARCHICAL]
    cyclic = [c for c in constraints 
              if c.constraint_type == ConstraintType.CYCLIC]
    
    # Count "holes" in constraint topology
    tree_holes = sum(len(c.parameters) for c in hierarchical)
    cycle_holes = len(cyclic)
    
    return max(1, tree_holes + cycle_holes)


def estimate_volume_growth(constraints: List[Constraint]) -> float:
    """Estimate volume growth rate from constraint structure"""
    if not constraints:
        return 1.0
    
    hierarchical_count = sum(1 for c in constraints 
                             if c.constraint_type == ConstraintType.HIERARCHICAL)
    spatial_count = sum(1 for c in constraints 
                        if c.constraint_type == ConstraintType.SPATIAL)
    
    h_ratio = hierarchical_count / len(constraints)
    s_ratio = spatial_count / len(constraints)
    
    if h_ratio > 0.3:
        return 1.0 + h_ratio * 2.0  # Exponential
    elif s_ratio > 0.5:
        return 1.0  # Linear
    else:
        return 0.5 + s_ratio * 0.5  # Sublinear/bounded


def count_positive_dimensions(constraints: List[Constraint]) -> int:
    """Count positive dimensions from spatial constraints"""
    spatial_params = [len(c.parameters) for c in constraints 
                      if c.constraint_type == ConstraintType.SPATIAL]
    
    return max(spatial_params) if spatial_params else 3


def count_negative_dimensions(constraints: List[Constraint]) -> int:
    """Count negative dimensions from temporal/causal constraints"""
    has_time = any(c.constraint_type in (ConstraintType.TEMPORAL, ConstraintType.CAUSAL)
                   for c in constraints)
    return 1 if has_time else 0


# ================================================================================
# EXTRACT ALL FEATURES
# ================================================================================

def extract_constraint_features(constraints: List[Constraint]) -> ConstraintFeatures:
    """Extract all features from a constraint set - NOW ACTUALLY WORKS"""
    return ConstraintFeatures(
        mean_curvature=estimate_mean_curvature(constraints),
        curvature_variance=estimate_curvature_variance(constraints),
        rotational_symmetry=detect_rotational_symmetry(constraints),
        translational_symmetry=detect_translational_symmetry(constraints),
        has_temporal_ordering=detect_temporal_ordering(constraints),
        causal_cone_angle=estimate_causal_cone_angle(constraints),
        is_compact=detect_compactness(constraints),
        fundamental_group_rank=estimate_fundamental_group(constraints),
        volume_growth_rate=estimate_volume_growth(constraints),
        positive_dimensions=count_positive_dimensions(constraints),
        negative_dimensions=count_negative_dimensions(constraints)
    )


# ================================================================================
# VERIFICATION: DOMAINS ARE NOW DISTINGUISHABLE
# ================================================================================

def verify_domains_distinguishable():
    """Verify that Lighthouse Keeper and Keeper's Dream produce different features"""
    
    # Lighthouse Keeper constraints
    keeper_constraints = [
        Constraint("tower_height", ConstraintType.SPATIAL, [30.0]),
        Constraint("foundation_diameter", ConstraintType.SPATIAL, [10.0]),
        Constraint("flash_interval", ConstraintType.TEMPORAL, [5.0]),
        Constraint("flash_duration", ConstraintType.TEMPORAL, [0.5]),
        Constraint("lens_rotation", ConstraintType.CYCLIC, [360.0, 60.0]),
        Constraint("focal_length", ConstraintType.SPATIAL, [0.5]),
        Constraint("duty_schedule", ConstraintType.HIERARCHICAL, [8.0, 3.0]),
        Constraint("visibility_radius", ConstraintType.METRIC, [20000.0])
    ]
    
    # Keeper's Dream constraints (different!)
    dream_constraints = [
        Constraint("lucid_recognition", ConstraintType.INFORMATIONAL, [0.7]),
        Constraint("symbolic_content", ConstraintType.HIERARCHICAL, [5.0]),
        Constraint("emotional_valence", ConstraintType.ENERGETIC, [-1.0, 1.0]),
        Constraint("dream_time", ConstraintType.TEMPORAL, [0.3])
    ]
    
    keeper_features = extract_constraint_features(keeper_constraints)
    dream_features = extract_constraint_features(dream_constraints)
    
    print("="*60)
    print("VERIFICATION: Domains are now distinguishable")
    print("="*60)
    
    print("\nLighthouse Keeper features:")
    print(f"  mean_curvature: {keeper_features.mean_curvature:.2f}")
    print(f"  rotational_symmetry: {keeper_features.rotational_symmetry:.2f}")
    print(f"  has_temporal_ordering: {keeper_features.has_temporal_ordering}")
    print(f"  volume_growth_rate: {keeper_features.volume_growth_rate:.2f}")
    
    print("\nKeeper's Dream features:")
    print(f"  mean_curvature: {dream_features.mean_curvature:.2f}")
    print(f"  rotational_symmetry: {dream_features.rotational_symmetry:.2f}")
    print(f"  has_temporal_ordering: {dream_features.has_temporal_ordering}")
    print(f"  volume_growth_rate: {dream_features.volume_growth_rate:.2f}")
    
    # Check if they're different
    different = (
        keeper_features.mean_curvature != dream_features.mean_curvature or
        keeper_features.rotational_symmetry != dream_features.rotational_symmetry or
        keeper_features.has_temporal_ordering != dream_features.has_temporal_ordering
    )
    
    print(f"\n✓ Domains are distinguishable: {different}")
    
    # Explain why
    print("\nWhy they're different:")
    print(f"  - Keeper has {sum(1 for c in keeper_constraints if c.constraint_type == ConstraintType.CYCLIC)} cyclic constraints (Fresnel lens)")
    print(f"  - Dream has {sum(1 for c in dream_constraints if c.constraint_type == ConstraintType.CYCLIC)} cyclic constraints")
    print(f"  → Keeper has higher rotational_symmetry")
    
    return keeper_features, dream_features


if __name__ == "__main__":
    verify_domains_distinguishable()
