"""
GeoWeird Self-Typing Bridge
Connects Python native agents to Lean self-typing formalization

Maps 7D constraint vectors (T, S, C, F, R, P, W) to Lean ConstraintFeatures,
calls MultiTypedDomain.fromConstraints(), returns superposition state.
"""

import ctypes
import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum, auto
from pathlib import Path

# Import the base lean_bridge for FFI
from geoweird.lean_bridge import LeanBridge, init_bridge, get_bridge


class Perspective(Enum):
    """Perspective types from Lean formalization"""
    PHYSICAL = "Physical"
    TEMPORAL = "Temporal"
    INFORMATIONAL = "Informational"
    SOCIAL = "Social"
    ENERGETIC = "Energetic"


class UniverseType(Enum):
    """The 5 GeoWeird universe types"""
    EUCLIDEAN = "Euclidean"      # Σ₁
    HYPERBOLIC = "Hyperbolic"    # Σ₂
    SPHERICAL = "Spherical"      # Σ₃
    LORENTZIAN = "Lorentzian"    # Σ₄
    CUSTOM = "Custom"            # Σ₅


@dataclass
class ConstraintFeatures:
    """Geometric features extracted from 7D constraints"""
    # Curvature indicators
    meanCurvature: float = 0.0
    curvatureVariance: float = 0.0
    
    # Symmetry properties
    rotationalSymmetry: float = 0.0
    translationalSymmetry: float = 0.0
    
    # Causal structure
    hasTemporalOrdering: bool = False
    causalConeAngle: float = 0.0
    
    # Topological properties
    isCompact: bool = False
    fundamentalGroupRank: int = 0
    
    # Growth behavior
    volumeGrowthRate: float = 1.0
    
    # Metric signature
    positiveDimensions: int = 3
    negativeDimensions: int = 0
    
    def to_lean_json(self) -> Dict[str, Any]:
        """Convert to JSON format expected by Lean FFI"""
        return {
            "meanCurvature": self.meanCurvature,
            "curvatureVariance": self.curvatureVariance,
            "rotationalSymmetry": self.rotationalSymmetry,
            "translationalSymmetry": self.translationalSymmetry,
            "hasTemporalOrdering": self.hasTemporalOrdering,
            "causalConeAngle": self.causalConeAngle,
            "isCompact": self.isCompact,
            "fundamentalGroupRank": self.fundamentalGroupRank,
            "volumeGrowthRate": self.volumeGrowthRate,
            "positiveDimensions": self.positiveDimensions,
            "negativeDimensions": self.negativeDimensions
        }


@dataclass
class UniverseScores:
    """Scores for each universe type"""
    euclidean: float = 0.0
    hyperbolic: float = 0.0
    spherical: float = 0.0
    lorentzian: float = 0.0
    custom: float = 0.0
    
    def best_fit(self) -> Tuple[UniverseType, float]:
        """Return best-fitting universe type and score"""
        scores = [
            (UniverseType.EUCLIDEAN, self.euclidean),
            (UniverseType.HYPERBOLIC, self.hyperbolic),
            (UniverseType.SPHERICAL, self.spherical),
            (UniverseType.LORENTZIAN, self.lorentzian),
            (UniverseType.CUSTOM, self.custom)
        ]
        return max(scores, key=lambda x: x[1])
    
    def should_multi_type(self, threshold: float = 0.5) -> bool:
        """Check if multiple types are above threshold"""
        scores = [self.euclidean, self.hyperbolic, self.spherical, 
                  self.lorentzian, self.custom]
        high_scores = [s for s in scores if s > threshold]
        return len(high_scores) > 1
    
    def multi_type_candidates(self, threshold: float = 0.5) -> List[Tuple[UniverseType, float]]:
        """Get all universe types above threshold"""
        candidates = [
            (UniverseType.EUCLIDEAN, self.euclidean),
            (UniverseType.HYPERBOLIC, self.hyperbolic),
            (UniverseType.SPHERICAL, self.spherical),
            (UniverseType.LORENTZIAN, self.lorentzian),
            (UniverseType.CUSTOM, self.custom)
        ]
        return [(u, s) for u, s in candidates if s > threshold]


@dataclass
class SuperpositionEntry:
    """Single entry in multi-typed superposition"""
    universe_type: UniverseType
    weight: float
    perspective: Perspective


@dataclass
class MultiTypedDomain:
    """A domain with multi-typed superposition"""
    name: str
    features: ConstraintFeatures
    scores: UniverseScores
    superposition: List[SuperpositionEntry]
    
    def collapse(self, forced_type: UniverseType) -> 'MultiTypedDomain':
        """Collapse superposition to single type"""
        filtered = [s for s in self.superposition if s.universe_type == forced_type]
        if not filtered:
            # If forced type not in superposition, add it
            filtered = [SuperpositionEntry(forced_type, 1.0, Perspective.PHYSICAL)]
        return MultiTypedDomain(
            name=self.name,
            features=self.features,
            scores=self.scores,  # Could update scores here
            superposition=filtered
        )
    
    def universe_for_perspective(self, perspective: Perspective) -> Optional[UniverseType]:
        """Get universe type for specific perspective"""
        for entry in self.superposition:
            if entry.perspective == perspective:
                return entry.universe_type
        return None


@dataclass
class CollisionResult:
    """Result of colliding two multi-typed domains"""
    domain_a: str
    domain_b: str
    universe_a: UniverseType
    universe_b: UniverseType
    consensus_strength: float
    perspective: Perspective
    intersection_volume: float


class SelfTypingBridge:
    """
    Bridge between Python 7D constraints and Lean self-typing formalization.
    
    This class:
    1. Maps 7D float vectors (T, S, C, F, R, P, W) to ConstraintFeatures
    2. Calls Lean MultiTypedDomain.fromConstraints()
    3. Returns superposition state for swarm orchestration
    4. Handles perspective collapse on collision
    """
    
    def __init__(self, lean_bridge: Optional[LeanBridge] = None):
        self.lean = lean_bridge or get_bridge()
        self._domain_cache: Dict[str, MultiTypedDomain] = {}
        self._collision_history: List[CollisionResult] = []
    
    # =========================================================================
    # 7D CONSTRAINT MAPPING
    # =========================================================================
    
    def map_7d_to_features(
        self,
        T: float,  # Temporal coherence
        S: float,  # Spatial embedding
        C: float,  # Causal density
        F: float,  # Field strength
        R: float,  # Rotational symmetry
        P: float,  # Phase alignment
        W: float   # Wave propagation
    ) -> ConstraintFeatures:
        """
        Map 7D constraint vector to ConstraintFeatures.
        
        This is the critical mapping from your native agent representation
        to the Lean formalization's constraint geometry.
        """
        features = ConstraintFeatures()
        
        # Curvature from causal density and field strength
        # High C + low F → negative curvature (hyperbolic)
        # Low C + high F → positive curvature (spherical)
        features.meanCurvature = (F - C) * 0.5
        features.curvatureVariance = abs(C - F) * 0.3
        
        # Symmetry from rotational component
        features.rotationalSymmetry = R
        features.translationalSymmetry = S * (1 - R)
        
        # Temporal ordering from T and C
        features.hasTemporalOrdering = T > 0.5 and C > 0.3
        features.causalConeAngle = min(1.0, C * T * np.pi / 2)
        
        # Compactness from spatial embedding
        features.isCompact = S > 0.8 and W < 0.5
        
        # Fundamental group from topology of phase alignment
        features.fundamentalGroupRank = int(P * 3) + 1
        
        # Volume growth from wave propagation and temporal coherence
        # Exponential growth → hyperbolic
        if W > 0.7 and T < 0.3:
            features.volumeGrowthRate = 1.0 + W
        # Bounded growth → spherical
        elif S > 0.8 and W < 0.3:
            features.volumeGrowthRate = 0.5
        # Linear growth → Euclidean (default)
        else:
            features.volumeGrowthRate = 1.0
        
        # Metric signature from causal structure
        if features.hasTemporalOrdering:
            features.positiveDimensions = 3
            features.negativeDimensions = 1  # Time dimension
        else:
            features.positiveDimensions = 3
            features.negativeDimensions = 0
        
        return features
    
    def extract_features_from_constraints(
        self,
        constraints: List[Dict[str, Any]]
    ) -> ConstraintFeatures:
        """
        Extract features from structured constraint list.
        
        Constraints should have format:
        {"name": str, "type": str, "parameters": List[float]}
        """
        features = ConstraintFeatures()
        
        for constraint in constraints:
            c_type = constraint.get("type", "").lower()
            params = constraint.get("parameters", [])
            
            if c_type == "temporal":
                features.hasTemporalOrdering = True
                if params:
                    features.causalConeAngle = min(1.0, params[0] / 10.0 * np.pi / 2)
            
            elif c_type == "spatial":
                features.translationalSymmetry = max(features.translationalSymmetry, 
                                                      min(1.0, sum(params) / 100.0))
            
            elif c_type == "cyclic":
                features.rotationalSymmetry = max(features.rotationalSymmetry,
                                                   min(1.0, params[0] / 360.0 if params else 0.5))
            
            elif c_type == "hierarchical":
                # Tree-like structure → hyperbolic
                if len(params) >= 2:
                    branching_factor = params[1]
                    features.volumeGrowthRate = max(features.volumeGrowthRate, 
                                                     1.0 + branching_factor * 0.1)
            
            elif c_type == "causal":
                features.hasTemporalOrdering = True
                features.causalConeAngle = min(1.0, sum(params) / len(params) if params else 0.5)
            
            elif c_type == "metric":
                features.isCompact = max(params) < 1000.0 if params else False
        
        return features
    
    # =========================================================================
    # LEAN FFI CALLS
    # =========================================================================
    
    def call_lean_self_typing(self, features: ConstraintFeatures) -> Dict[str, Any]:
        """
        Call Lean self-typing via FFI.
        
        In production, this would call the compiled Lean library.
        For now, we implement the scoring logic in Python (mirroring Lean).
        """
        # TODO: Replace with actual FFI call to Lean
        # return self.lean.call("self_typing_from_features", features.to_lean_json())
        
        # Mirror Lean's scoring logic
        scores = self._calculate_universe_scores(features)
        
        # Build superposition
        superposition = self._build_superposition(features, scores)
        
        return {
            "scores": asdict(scores),
            "superposition": [
                {
                    "universe_type": entry.universe_type.value,
                    "weight": entry.weight,
                    "perspective": entry.perspective.value
                }
                for entry in superposition
            ]
        }
    
    def _calculate_universe_scores(self, features: ConstraintFeatures) -> UniverseScores:
        """Mirror Lean's UniverseScores.fromFeatures"""
        scores = UniverseScores()
        
        # Euclidean: flat, translational symmetry, no temporal
        scores.euclidean = (
            (0.8 if abs(features.meanCurvature) < 0.1 else 0.2) +
            features.translationalSymmetry * 0.5 +
            (0.0 if features.hasTemporalOrdering else 0.3)
        )
        
        # Hyperbolic: negative curvature, exponential growth, tree-like
        scores.hyperbolic = (
            (0.8 if features.meanCurvature < -0.1 else 0.1) +
            (0.5 if features.volumeGrowthRate > 1.5 else 0.0) +
            (0.3 if features.fundamentalGroupRank > 1 else 0.0)
        )
        
        # Spherical: positive curvature, compact, rotational symmetry
        scores.spherical = (
            (0.8 if features.meanCurvature > 0.1 else 0.1) +
            (0.5 if features.isCompact else 0.0) +
            features.rotationalSymmetry * 0.5
        )
        
        # Lorentzian: temporal ordering, causal cones, mixed metric
        scores.lorentzian = (
            (0.8 if features.hasTemporalOrdering else 0.0) +
            features.causalConeAngle * 0.5 +
            (0.5 if features.negativeDimensions > 0 else 0.0)
        )
        
        # Custom: none of the above fit well
        max_standard = max(scores.euclidean, scores.hyperbolic, 
                          scores.spherical, scores.lorentzian)
        scores.custom = 0.8 if max_standard < 0.3 else 0.1
        
        return scores
    
    def _build_superposition(
        self, 
        features: ConstraintFeatures, 
        scores: UniverseScores
    ) -> List[SuperpositionEntry]:
        """Build multi-typed superposition from scores"""
        candidates = scores.multi_type_candidates(0.4)
        
        if not candidates:
            # No strong fit, use best single
            best_type, best_score = scores.best_fit()
            return [SuperpositionEntry(best_type, 1.0, Perspective.PHYSICAL)]
        
        # Build superposition with perspective mapping
        superposition = []
        for u_type, score in candidates:
            perspective = self._universe_to_perspective(u_type)
            superposition.append(SuperpositionEntry(u_type, score, perspective))
        
        return superposition
    
    def _universe_to_perspective(self, u_type: UniverseType) -> Perspective:
        """Map universe type to default perspective"""
        mapping = {
            UniverseType.EUCLIDEAN: Perspective.PHYSICAL,
            UniverseType.HYPERBOLIC: Perspective.INFORMATIONAL,
            UniverseType.SPHERICAL: Perspective.ENERGETIC,
            UniverseType.LORENTZIAN: Perspective.TEMPORAL,
            UniverseType.CUSTOM: Perspective.SOCIAL
        }
        return mapping.get(u_type, Perspective.PHYSICAL)
    
    # =========================================================================
    # PUBLIC API: Domain Registration
    # =========================================================================
    
    def register_domain_7d(
        self,
        name: str,
        T: float, S: float, C: float, F: float, 
        R: float, P: float, W: float
    ) -> MultiTypedDomain:
        """
        Register a domain using 7D constraint vector.
        
        This is the main entry point for native agents.
        """
        features = self.map_7d_to_features(T, S, C, F, R, P, W)
        return self._create_domain(name, features)
    
    def register_domain_constraints(
        self,
        name: str,
        constraints: List[Dict[str, Any]]
    ) -> MultiTypedDomain:
        """
        Register a domain using structured constraint list.
        """
        features = self.extract_features_from_constraints(constraints)
        return self._create_domain(name, features)
    
    def _create_domain(self, name: str, features: ConstraintFeatures) -> MultiTypedDomain:
        """Create MultiTypedDomain from features"""
        # Call Lean (or mirror logic)
        result = self.call_lean_self_typing(features)
        
        # Parse result
        scores = UniverseScores(**result["scores"])
        superposition = [
            SuperpositionEntry(
                UniverseType(entry["universe_type"]),
                entry["weight"],
                Perspective(entry["perspective"])
            )
            for entry in result["superposition"]
        ]
        
        domain = MultiTypedDomain(
            name=name,
            features=features,
            scores=scores,
            superposition=superposition
        )
        
        # Cache for later
        self._domain_cache[name] = domain
        
        return domain
    
    # =========================================================================
    # PUBLIC API: Collision & Perspective Selection
    # =========================================================================
    
    def collide_domains(
        self,
        domain_a_name: str,
        domain_b_name: str
    ) -> List[CollisionResult]:
        """
        Collide two domains and return all viable perspective combinations.
        
        Returns list of (universe_a, universe_b, consensus, perspective) tuples.
        """
        domain_a = self._domain_cache.get(domain_a_name)
        domain_b = self._domain_cache.get(domain_b_name)
        
        if not domain_a or not domain_b:
            raise ValueError(f"Domains not registered: {domain_a_name}, {domain_b_name}")
        
        results = []
        
        # Try all perspective combinations
        for entry_a in domain_a.superposition:
            for entry_b in domain_b.superposition:
                consensus = self._calculate_consensus(entry_a, entry_b)
                
                if consensus > 0.3:  # Threshold for viable collision
                    combined_perspective = self._combine_perspectives(
                        entry_a.perspective, entry_b.perspective
                    )
                    
                    result = CollisionResult(
                        domain_a=domain_a_name,
                        domain_b=domain_b_name,
                        universe_a=entry_a.universe_type,
                        universe_b=entry_b.universe_type,
                        consensus_strength=consensus,
                        perspective=combined_perspective,
                        intersection_volume=self._estimate_intersection(
                            entry_a.universe_type, entry_b.universe_type, consensus
                        )
                    )
                    results.append(result)
        
        # Sort by consensus strength
        results.sort(key=lambda r: r.consensus_strength, reverse=True)
        
        # Log collision
        self._collision_history.extend(results)
        
        return results
    
    def select_best_perspective(
        self,
        domain_a_name: str,
        domain_b_name: str
    ) -> Optional[CollisionResult]:
        """
        Select the perspective that maximizes consensus between two domains.
        
        This is what the Swarm Orchestrator calls to decide:
        - Which universe to spawn Projector agents in
        - Which metric signature Critics should use
        - What manifold geometry Integrator derives invariants from
        """
        results = self.collide_domains(domain_a_name, domain_b_name)
        
        if not results:
            return None
        
        return results[0]  # Best consensus
    
    def _calculate_consensus(
        self,
        entry_a: SuperpositionEntry,
        entry_b: SuperpositionEntry
    ) -> float:
        """Calculate consensus strength between two superposition entries"""
        # Same universe type → high consensus
        if entry_a.universe_type == entry_b.universe_type:
            return min(1.0, (entry_a.weight + entry_b.weight) / 2 + 0.3)
        
        # Compatible perspectives → moderate consensus
        perspective_compatibility = {
            (Perspective.PHYSICAL, Perspective.ENERGETIC): 0.7,
            (Perspective.TEMPORAL, Perspective.INFORMATIONAL): 0.6,
            (Perspective.SOCIAL, Perspective.INFORMATIONAL): 0.5,
        }
        
        key = (entry_a.perspective, entry_b.perspective)
        reverse_key = (entry_b.perspective, entry_a.perspective)
        
        base_consensus = perspective_compatibility.get(key, 0.3)
        base_consensus = max(base_consensus, perspective_compatibility.get(reverse_key, 0.3))
        
        # Weight by confidence
        return base_consensus * (entry_a.weight + entry_b.weight) / 2
    
    def _combine_perspectives(
        self,
        p1: Perspective,
        p2: Perspective
    ) -> Perspective:
        """Combine two perspectives into unified view"""
        combinations = {
            (Perspective.PHYSICAL, Perspective.TEMPORAL): Perspective.ENERGETIC,
            (Perspective.TEMPORAL, Perspective.PHYSICAL): Perspective.ENERGETIC,
            (Perspective.INFORMATIONAL, Perspective.SOCIAL): Perspective.SOCIAL,
            (Perspective.SOCIAL, Perspective.INFORMATIONAL): Perspective.SOCIAL,
            (Perspective.ENERGETIC, Perspective.TEMPORAL): Perspective.ENERGETIC,
            (Perspective.PHYSICAL, Perspective.ENERGETIC): Perspective.ENERGETIC,
        }
        
        return combinations.get((p1, p2), p1)
    
    def _estimate_intersection(
        self,
        u1: UniverseType,
        u2: UniverseType,
        consensus: float
    ) -> float:
        """Estimate manifold intersection volume"""
        # Same type → large intersection
        if u1 == u2:
            return consensus * 100.0
        
        # Different types → smaller intersection
        return consensus * 50.0
    
    # =========================================================================
    # PUBLIC API: Domain Updates
    # =========================================================================
    
    def update_domain_after_collision(
        self,
        domain_name: str,
        collision: CollisionResult
    ) -> MultiTypedDomain:
        """
        Update domain's learned types after successful collision.
        
        Reinforces the universe type that produced consensus.
        """
        domain = self._domain_cache.get(domain_name)
        if not domain:
            raise ValueError(f"Domain not registered: {domain_name}")
        
        # Determine which universe type was reinforced
        reinforced_type = collision.universe_a if collision.domain_a == domain_name else collision.universe_b
        
        # Update superposition weights
        new_superposition = []
        for entry in domain.superposition:
            if entry.universe_type == reinforced_type:
                # Reinforce
                new_weight = min(1.0, entry.weight + 0.1 * collision.consensus_strength)
                new_superposition.append(SuperpositionEntry(
                    entry.universe_type, new_weight, entry.perspective
                ))
            else:
                # Decay
                new_weight = entry.weight * 0.95
                if new_weight > 0.1:  # Keep if still significant
                    new_superposition.append(SuperpositionEntry(
                        entry.universe_type, new_weight, entry.perspective
                    ))
        
        # Update domain
        updated_domain = MultiTypedDomain(
            name=domain.name,
            features=domain.features,
            scores=domain.scores,
            superposition=new_superposition
        )
        
        self._domain_cache[domain_name] = updated_domain
        return updated_domain
    
    def has_converged(self, domain_name: str, threshold: float = 0.8) -> Optional[UniverseType]:
        """Check if domain has converged on a single universe type"""
        domain = self._domain_cache.get(domain_name)
        if not domain:
            return None
        
        above_threshold = [entry for entry in domain.superposition if entry.weight > threshold]
        if not above_threshold:
            return None
        
        best_entry = max(above_threshold, key=lambda e: e.weight)
        return best_entry.universe_type
    
    # =========================================================================
    # PUBLIC API: Statistics
    # =========================================================================
    
    def get_collision_history(self) -> List[CollisionResult]:
        """Get all recorded collisions"""
        return self._collision_history.copy()
    
    def get_learned_rules(self) -> List[Dict[str, Any]]:
        """Extract learned typing rules from collision history"""
        rules = []
        
        # Group by universe type
        by_type: Dict[UniverseType, List[CollisionResult]] = {}
        for collision in self._collision_history:
            if collision.consensus_strength > 0.7:
                u_type = collision.universe_a  # Simplified
                if u_type not in by_type:
                    by_type[u_type] = []
                by_type[u_type].append(collision)
        
        for u_type, collisions in by_type.items():
            avg_consensus = sum(c.consensus_strength for c in collisions) / len(collisions)
            rules.append({
                "universe_type": u_type.value,
                "confidence": avg_consensus,
                "evidence_count": len(collisions),
                "pattern": f"Perspective: {collisions[0].perspective.value}"
            })
        
        return rules


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_self_typing_bridge: Optional[SelfTypingBridge] = None


def init_self_typing_bridge(lean_bridge: Optional[LeanBridge] = None) -> SelfTypingBridge:
    """Initialize global self-typing bridge"""
    global _self_typing_bridge
    _self_typing_bridge = SelfTypingBridge(lean_bridge)
    return _self_typing_bridge


def get_self_typing_bridge() -> Optional[SelfTypingBridge]:
    """Get global self-typing bridge instance"""
    return _self_typing_bridge
