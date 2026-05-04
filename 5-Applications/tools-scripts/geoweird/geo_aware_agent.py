"""
GeoWeird-Aware Agent Wrapper

Wraps native Python agents with GeoWeird self-typing capabilities.
Agents register their 7D constraints and receive multi-typed superposition.
"""

import hashlib
import json
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

from geoweird.self_typing_bridge import (
    SelfTypingBridge, MultiTypedDomain, SuperpositionEntry,
    UniverseType, Perspective, CollisionResult,
    init_self_typing_bridge, get_self_typing_bridge
)


@dataclass
class DomainExpertProfile:
    """Profile extracted from EXHAUSTIVE_DOMAIN_EXPERT_LIST.md"""
    name: str
    expertise_area: str
    constraints_7d: Dict[str, float]  # T, S, C, F, R, P, W
    typical_outputs: List[str]
    collaboration_patterns: List[str]
    
    @classmethod
    def from_markdown(cls, md_content: str) -> List['DomainExpertProfile']:
        """Parse domain expert profiles from emoji-bullet markdown lists."""
        profiles = []
        current_section = ""
        
        for line in md_content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            
            # Track section headings for expertise area
            if stripped.startswith("## ") or stripped.startswith("### "):
                current_section = stripped.lstrip("# ").strip()
                continue
            
            # Parse emoji bullet lists like "- 🔬 Compression Theory Domain Expert"
            if stripped.startswith("- "):
                # Extract name after the bullet (strip leading emoji if present)
                raw_name = stripped[2:].strip()
                # Remove leading emoji(s) and whitespace
                name = raw_name
                while name and not name[0].isalnum():
                    name = name[1:].strip()
                
                if not name:
                    continue
                
                profiles.append(cls(
                    name=name,
                    expertise_area=current_section,
                    constraints_7d={},
                    typical_outputs=[],
                    collaboration_patterns=[]
                ))
        
        return profiles


@dataclass
class GeoWeirdContext:
    """Context for agent operation in a specific universe"""
    universe_type: UniverseType
    perspective: Perspective
    metric_signature: tuple  # (positive_dims, negative_dims)
    curvature: float
    collaboration_id: str
    
    def to_projector_config(self) -> Dict[str, Any]:
        """Convert to Projector agent configuration"""
        return {
            "universe": self.universe_type.value,
            "perspective": self.perspective.value,
            "metric": self.metric_signature,
            "curvature": self.curvature,
            "session": self.collaboration_id
        }


class GeoWeirdAwareAgent:
    """
    Native Python agent wrapped with GeoWeird self-typing.
    
    This agent:
    1. Registers its 7D constraints with the self-typing bridge
    2. Maintains multi-typed superposition
    3. Collapses to specific universe on collaboration
    4. Spawns Projector agents IN THAT UNIVERSE
    5. Uses shared metric signature for Critique
    6. Derives invariants from collapsed manifold geometry
    """
    
    def __init__(
        self,
        name: str,
        profile: Optional[DomainExpertProfile] = None,
        constraints_7d: Optional[Dict[str, float]] = None,
        self_typing_bridge: Optional[SelfTypingBridge] = None
    ):
        self.name = name
        self.bridge = self_typing_bridge or get_self_typing_bridge()
        
        if not self.bridge:
            raise RuntimeError("SelfTypingBridge not initialized. Call init_self_typing_bridge() first.")
        
        # Register with self-typing bridge
        if profile:
            self.domain = self._register_from_profile(profile)
        elif constraints_7d:
            self.domain = self._register_from_7d(constraints_7d)
        else:
            raise ValueError("Must provide either profile or constraints_7d")
        
        # Collaboration state
        self.current_context: Optional[GeoWeirdContext] = None
        self.collaboration_history: List[GeoWeirdContext] = []
        self.spawned_projectors: List[Dict[str, Any]] = []
        
        # Learned preferences (which universe types work best)
        self.universe_preferences: Dict[UniverseType, float] = {}
    
    def _register_from_profile(self, profile: DomainExpertProfile) -> MultiTypedDomain:
        """Register agent using DomainExpertProfile"""
        c = profile.constraints_7d
        return self.bridge.register_domain_7d(
            name=profile.name,
            T=c.get("T", 0.5),
            S=c.get("S", 0.5),
            C=c.get("C", 0.5),
            F=c.get("F", 0.5),
            R=c.get("R", 0.5),
            P=c.get("P", 0.5),
            W=c.get("W", 0.5)
        )
    
    def _register_from_7d(self, constraints: Dict[str, float]) -> MultiTypedDomain:
        """Register agent using 7D constraint vector"""
        return self.bridge.register_domain_7d(
            name=self.name,
            T=constraints.get("T", 0.5),
            S=constraints.get("S", 0.5),
            C=constraints.get("C", 0.5),
            F=constraints.get("F", 0.5),
            R=constraints.get("R", 0.5),
            P=constraints.get("P", 0.5),
            W=constraints.get("W", 0.5)
        )
    
    # ========================================================================
    # COLLABORATION API
    # ========================================================================
    
    def initiate_collaboration(
        self,
        other_agent: 'GeoWeirdAwareAgent',
        task_description: str,
        collision: Optional[CollisionResult] = None
    ) -> Optional[GeoWeirdContext]:
        """
        Initiate collaboration with another agent.
        
        This:
        1. Collides domains via self-typing bridge (unless precomputed collision provided)
        2. Selects perspective that maximizes consensus
        3. Creates GeoWeirdContext for operation
        4. Spawns Projector agents IN THAT UNIVERSE
        
        Returns None if no viable consensus found.
        """
        if collision is not None:
            best = collision
        else:
            # Collide domains
            collision_results = self.bridge.collide_domains(self.name, other_agent.name)
            
            if not collision_results:
                print(f"[{self.name}] No viable consensus with {other_agent.name}")
                return None
            
            # Select best perspective
            best = collision_results[0]
        
        # Determine which universe we operate in
        my_universe = best.universe_a if best.domain_a == self.name else best.universe_b
        
        # Create context
        context = GeoWeirdContext(
            universe_type=my_universe,
            perspective=best.perspective,
            metric_signature=self._universe_to_metric(my_universe),
            curvature=self._universe_to_curvature(my_universe),
            collaboration_id=f"{self.name}_{other_agent.name}_{hashlib.sha256(task_description.encode()).hexdigest()[:8]}"
        )
        
        self.current_context = context
        self.collaboration_history.append(context)
        
        # Update learned preferences
        self._update_preferences(my_universe, best.consensus_strength)
        
        # Spawn Projector agents
        self._spawn_projectors(context, task_description)
        
        print(f"[{self.name}] Collaboration with {other_agent.name}: {my_universe.value} universe, "
              f"{best.perspective.value} perspective, consensus={best.consensus_strength:.2f}")
        
        return context
    
    def _universe_to_metric(self, u_type: UniverseType) -> tuple:
        """Get metric signature for universe type"""
        metrics = {
            UniverseType.EUCLIDEAN: (3, 0),
            UniverseType.HYPERBOLIC: (3, 0),
            UniverseType.SPHERICAL: (3, 0),
            UniverseType.LORENTZIAN: (3, 1),
            UniverseType.CUSTOM: (2, 2)
        }
        return metrics.get(u_type, (3, 0))
    
    def _universe_to_curvature(self, u_type: UniverseType) -> float:
        """Get curvature for universe type"""
        curvatures = {
            UniverseType.EUCLIDEAN: 0.0,
            UniverseType.HYPERBOLIC: -1.0,
            UniverseType.SPHERICAL: 1.0,
            UniverseType.LORENTZIAN: 0.0,
            UniverseType.CUSTOM: 0.0
        }
        return curvatures.get(u_type, 0.0)
    
    def _update_preferences(self, u_type: UniverseType, consensus: float):
        """Update learned universe preferences"""
        if u_type not in self.universe_preferences:
            self.universe_preferences[u_type] = 0.0
        
        # Exponential moving average
        self.universe_preferences[u_type] = (
            0.7 * self.universe_preferences[u_type] + 
            0.3 * consensus
        )
    
    def _spawn_projectors(self, context: GeoWeirdContext, task: str):
        """Spawn Projector agents in the selected universe"""
        # Number of projectors based on universe type
        projector_counts = {
            UniverseType.EUCLIDEAN: 3,
            UniverseType.HYPERBOLIC: 5,  # More for exponential search
            UniverseType.SPHERICAL: 2,   # Compact, fewer needed
            UniverseType.LORENTZIAN: 4,  # Causal chains
            UniverseType.CUSTOM: 3
        }
        
        num_projectors = projector_counts.get(context.universe_type, 3)
        
        for i in range(num_projectors):
            projector = {
                "id": f"{self.name}_projector_{i}",
                "universe": context.universe_type.value,
                "perspective": context.perspective.value,
                "task": task,
                "metric": context.metric_signature,
                "spawned_by": self.name
            }
            self.spawned_projectors.append(projector)
        
        print(f"[{self.name}] Spawned {num_projectors} Projectors in {context.universe_type.value} universe")
    
    # ========================================================================
    # CRITIQUE API
    # ========================================================================
    
    def critique_output(
        self,
        output: str,
        criteria: List[str],
        other_agent: Optional['GeoWeirdAwareAgent'] = None
    ) -> Dict[str, Any]:
        """
        Critique output using shared metric signature.
        
        Critics evaluate using the manifold geometry from the
        collapsed collaboration context.
        """
        if not self.current_context:
            return {"error": "No active collaboration context"}
        
        # Use metric signature from context
        pos_dims, neg_dims = self.current_context.metric_signature
        
        # Evaluate each criterion
        evaluations = {}
        for criterion in criteria:
            # Score based on universe-appropriate metrics
            score = self._evaluate_in_universe(
                output, criterion, 
                self.current_context.universe_type
            )
            evaluations[criterion] = score
        
        # Calculate invariant (geometric mean in appropriate metric)
        invariant = self._derive_invariant(evaluations, self.current_context)
        
        return {
            "evaluations": evaluations,
            "invariant": invariant,
            "universe": self.current_context.universe_type.value,
            "metric": self.current_context.metric_signature,
            "confidence": sum(evaluations.values()) / len(evaluations) if evaluations else 0.0
        }
    
    def _evaluate_in_universe(
        self, 
        output: str, 
        criterion: str, 
        u_type: UniverseType
    ) -> float:
        """Evaluate output using universe-appropriate metrics"""
        # Placeholder: real implementation would use actual criteria
        
        if u_type == UniverseType.EUCLIDEAN:
            # Euclidean: distance-based metrics
            return 0.7 + 0.2 * (int(hashlib.sha256((output + criterion).encode()).hexdigest(), 16) % 100) / 100
        
        elif u_type == UniverseType.HYPERBOLIC:
            # Hyperbolic: exponential scaling
            return 0.6 + 0.3 * (int(hashlib.sha256((output + criterion).encode()).hexdigest(), 16) % 100) / 100
        
        elif u_type == UniverseType.SPHERICAL:
            # Spherical: angular metrics
            return 0.75 + 0.15 * (int(hashlib.sha256((output + criterion).encode()).hexdigest(), 16) % 100) / 100
        
        elif u_type == UniverseType.LORENTZIAN:
            # Lorentzian: causal consistency
            return 0.65 + 0.25 * (int(hashlib.sha256((output + criterion).encode()).hexdigest(), 16) % 100) / 100
        
        else:
            return 0.5 + 0.3 * (int(hashlib.sha256((output + criterion).encode()).hexdigest(), 16) % 100) / 100
    
    def _derive_invariant(
        self, 
        evaluations: Dict[str, float], 
        context: GeoWeirdContext
    ) -> float:
        """Derive geometric invariant from evaluations"""
        if not evaluations:
            return 0.0
        
        values = list(evaluations.values())
        
        if context.universe_type == UniverseType.EUCLIDEAN:
            # Euclidean: arithmetic mean
            return sum(values) / len(values)
        
        elif context.universe_type == UniverseType.HYPERBOLIC:
            # Hyperbolic: exponential of mean of logs
            import math
            log_sum = sum(math.log(max(v, 0.001)) for v in values)
            return math.exp(log_sum / len(values))
        
        elif context.universe_type == UniverseType.SPHERICAL:
            # Spherical: minimum (most restrictive)
            return min(values)
        
        elif context.universe_type == UniverseType.LORENTZIAN:
            # Lorentzian: weighted by causal importance
            return sum(values) / len(values)  # Simplified
        
        else:
            return sum(values) / len(values)
    
    # ========================================================================
    # INTEGRATION API
    # ========================================================================
    
    def integrate_results(
        self,
        projector_outputs: List[Dict[str, Any]],
        critiques: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Integrate Projector outputs and Critique evaluations.
        
        Derives final invariant from the collapsed manifold geometry.
        """
        if not self.current_context:
            return {"error": "No active collaboration context"}
        
        # Aggregate projector outputs
        aggregated = self._aggregate_projectors(projector_outputs)
        
        # Weight by critique confidence
        weighted = self._weight_by_critique(aggregated, critiques)
        
        # Derive final invariant
        final_invariant = self._derive_final_invariant(weighted, self.current_context)
        
        return {
            "integrated_output": weighted,
            "final_invariant": final_invariant,
            "universe": self.current_context.universe_type.value,
            "manifold_geometry": {
                "curvature": self.current_context.curvature,
                "metric": self.current_context.metric_signature
            }
        }
    
    def _aggregate_projectors(
        self, 
        outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate outputs from multiple projectors"""
        # Simplified: just take the most common
        if not outputs:
            return {}
        
        # Group by content
        from collections import Counter
        contents = [json.dumps(o.get("content", {}), sort_keys=True) for o in outputs]
        most_common = Counter(contents).most_common(1)[0][0]
        
        return {"aggregated": most_common, "count": len(outputs)}
    
    def _weight_by_critique(
        self, 
        aggregated: Dict[str, Any], 
        critiques: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Weight aggregated output by critique confidence"""
        avg_confidence = sum(
            c.get("confidence", 0.5) for c in critiques
        ) / len(critiques) if critiques else 0.5
        
        return {
            **aggregated,
            "weighted_confidence": avg_confidence
        }
    
    def _derive_final_invariant(
        self, 
        weighted: Dict[str, Any], 
        context: GeoWeirdContext
    ) -> float:
        """Derive final geometric invariant"""
        base = weighted.get("weighted_confidence", 0.5)
        
        # Adjust by curvature
        if context.curvature > 0:
            # Spherical: more restrictive
            return base * 0.9
        elif context.curvature < 0:
            # Hyperbolic: more permissive
            return min(1.0, base * 1.1)
        else:
            # Euclidean: neutral
            return base
    
    # ========================================================================
    # STATE API
    # ========================================================================
    
    def get_superposition(self) -> List[SuperpositionEntry]:
        """Get current multi-typed superposition"""
        return self.domain.superposition
    
    def get_converged_type(self, threshold: float = 0.8) -> Optional[UniverseType]:
        """Check if agent has converged on single universe type"""
        return self.bridge.has_converged(self.name, threshold)
    
    def get_preferences(self) -> Dict[UniverseType, float]:
        """Get learned universe preferences"""
        return self.universe_preferences.copy()
    
    def reset_collaboration(self):
        """Reset current collaboration context"""
        self.current_context = None
        self.spawned_projectors = []


# ================================================================================
# FACTORY FUNCTIONS
# ================================================================================

def create_geo_weird_agent(
    name: str,
    md_file: Optional[Path] = None,
    constraints_7d: Optional[Dict[str, float]] = None
) -> GeoWeirdAwareAgent:
    """
    Factory function to create GeoWeird-aware agent.
    
    Usage:
        agent = create_geo_weird_agent(
            name="Lighthouse Keeper",
            constraints_7d={"T": 0.8, "S": 0.7, "C": 0.6, "F": 0.5, "R": 0.9, "P": 0.4, "W": 0.3}
        )
    """
    profile = None
    
    if md_file and md_file.exists():
        content = md_file.read_text()
        profiles = DomainExpertProfile.from_markdown(content)
        profile = next((p for p in profiles if p.name == name), None)
    
    return GeoWeirdAwareAgent(
        name=name,
        profile=profile,
        constraints_7d=constraints_7d
    )


def load_domain_experts_from_markdown(md_path: Path) -> List[GeoWeirdAwareAgent]:
    """Load all domain experts from EXHAUSTIVE_DOMAIN_EXPERT_LIST.md"""
    content = md_path.read_text()
    profiles = DomainExpertProfile.from_markdown(content)
    
    agents = []
    for profile in profiles:
        agent = GeoWeirdAwareAgent(name=profile.name, profile=profile)
        agents.append(agent)
    
    return agents
