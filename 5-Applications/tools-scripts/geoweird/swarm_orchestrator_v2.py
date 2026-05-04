"""
GeoWeird Swarm Orchestrator v2

Uses Lean self-typing pipeline for perspective selection and universe assignment.

Flow:
1. Load domain experts from EXHAUSTIVE_DOMAIN_EXPERT_LIST.md
2. Register each with SelfTypingBridge (7D → ConstraintFeatures → MultiTypedDomain)
3. Pair agents for collaboration
4. For each pair, ask Lean: "What perspective maximizes consensus?"
5. Receive collapsed universe + perspective
6. Spawn Projector agents IN THAT UNIVERSE
7. Critics evaluate using shared metric signature
8. Integrator derives invariant from collapsed manifold geometry
"""

import json
import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from geoweird.self_typing_bridge import (
    SelfTypingBridge, UniverseType, Perspective, CollisionResult,
    init_self_typing_bridge, get_self_typing_bridge
)

from geoweird.geo_aware_agent import (
    GeoWeirdAwareAgent, GeoWeirdContext,
    create_geo_weird_agent, load_domain_experts_from_markdown
)


@dataclass
class CollaborationSession:
    """A collaboration session between two agents"""
    session_id: str
    agent_a: str
    agent_b: str
    context: GeoWeirdContext
    projectors: List[Dict[str, Any]] = field(default_factory=list)
    critiques: List[Dict[str, Any]] = field(default_factory=list)
    integrated_result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agents": [self.agent_a, self.agent_b],
            "universe": self.context.universe_type.value,
            "perspective": self.context.perspective.value,
            "metric": self.context.metric_signature,
            "projectors": len(self.projectors),
            "critiques": len(self.critiques),
            "integrated": self.integrated_result is not None
        }


@dataclass
class SwarmMetrics:
    """Metrics for swarm performance"""
    total_collaborations: int = 0
    successful_collaborations: int = 0
    universe_distribution: Dict[str, int] = field(default_factory=dict)
    perspective_distribution: Dict[str, int] = field(default_factory=dict)
    average_consensus: float = 0.0
    convergence_rate: float = 0.0


class GeoWeirdSwarmOrchestrator:
    """
    Swarm orchestrator that uses Lean self-typing for perspective selection.
    
    This orchestrator:
    1. Maintains pool of GeoWeird-aware agents
    2. Pairs agents based on complementarity
    3. Uses Lean to select optimal perspective for each pair
    4. Spawns projectors in collapsed universe
    5. Coordinates critique and integration
    6. Tracks emergent typing rules
    """
    
    def __init__(
        self,
        self_typing_bridge: Optional[SelfTypingBridge] = None,
        consensus_threshold: float = 0.5
    ):
        self.bridge = self_typing_bridge or get_self_typing_bridge()
        
        if not self.bridge:
            raise RuntimeError("SelfTypingBridge not initialized")
        
        self.consensus_threshold = consensus_threshold
        self.agents: Dict[str, GeoWeirdAwareAgent] = {}
        self.sessions: List[CollaborationSession] = []
        self.metrics = SwarmMetrics()
        
        # Learned patterns
        self.successful_pairs: List[Tuple[str, str]] = []
        self.universe_preferences: Dict[str, Dict[UniverseType, float]] = defaultdict(
            lambda: defaultdict(float)
        )
    
    # ========================================================================
    # AGENT MANAGEMENT
    # ========================================================================
    
    def register_agent(self, agent: GeoWeirdAwareAgent) -> 'GeoWeirdSwarmOrchestrator':
        """Register a GeoWeird-aware agent"""
        self.agents[agent.name] = agent
        return self
    
    def register_agents(self, agents: List[GeoWeirdAwareAgent]) -> 'GeoWeirdSwarmOrchestrator':
        """Register multiple agents"""
        for agent in agents:
            self.register_agent(agent)
        return self
    
    def load_from_markdown(self, md_path: Path) -> 'GeoWeirdSwarmOrchestrator':
        """Load domain experts from EXHAUSTIVE_DOMAIN_EXPERT_LIST.md"""
        agents = load_domain_experts_from_markdown(md_path)
        return self.register_agents(agents)
    
    def get_agent(self, name: str) -> Optional[GeoWeirdAwareAgent]:
        """Get agent by name"""
        return self.agents.get(name)
    
    # ========================================================================
    # PAIRING STRATEGIES
    # ========================================================================
    
    def pair_agents_random(self) -> List[Tuple[GeoWeirdAwareAgent, GeoWeirdAwareAgent]]:
        """Random pairing strategy"""
        agent_list = list(self.agents.values())
        random.shuffle(agent_list)
        
        pairs = []
        for i in range(0, len(agent_list) - 1, 2):
            pairs.append((agent_list[i], agent_list[i + 1]))
        
        return pairs
    
    def pair_agents_complementary(self) -> List[Tuple[GeoWeirdAwareAgent, GeoWeirdAwareAgent]]:
        """
        Pair agents with complementary superpositions.
        
        Agents with different dominant universe types are more likely
        to produce interesting collisions.
        """
        agent_list = list(self.agents.values())
        pairs = []
        
        # Sort by dominant universe type
        by_universe: Dict[UniverseType, List[GeoWeirdAwareAgent]] = defaultdict(list)
        for agent in agent_list:
            if agent.domain.superposition:
                dominant = agent.domain.superposition[0].universe_type
                by_universe[dominant].append(agent)
        
        # Pair across universe types
        universes = list(by_universe.keys())
        for i, u1 in enumerate(universes):
            for u2 in universes[i + 1:]:
                agents1 = by_universe[u1]
                agents2 = by_universe[u2]
                
                min_len = min(len(agents1), len(agents2))
                for j in range(min_len):
                    pairs.append((agents1[j], agents2[j]))
        
        # Fallback to random pairing if no complementary pairs found
        if not pairs:
            pairs = self.pair_agents_random()
        
        return pairs
    
    def pair_agents_learned(self) -> List[Tuple[GeoWeirdAwareAgent, GeoWeirdAwareAgent]]:
        """
        Pair agents based on learned successful collaborations.
        
        If two agents have collaborated successfully before,
        they're likely to do so again.
        """
        # Start with known successful pairs
        pairs = []
        used = set()
        
        for (name_a, name_b) in self.successful_pairs:
            if name_a in self.agents and name_b in self.agents:
                if name_a not in used and name_b not in used:
                    pairs.append((self.agents[name_a], self.agents[name_b]))
                    used.add(name_a)
                    used.add(name_b)
        
        # Fill remaining with random
        remaining = [a for name, a in self.agents.items() if name not in used]
        random.shuffle(remaining)
        
        for i in range(0, len(remaining) - 1, 2):
            pairs.append((remaining[i], remaining[i + 1]))
        
        return pairs
    
    # ========================================================================
    # MAIN ORCHESTRATION LOOP
    # ========================================================================
    
    def run_collaboration_round(
        self,
        pairing_strategy: str = "complementary",
        task_template: str = "Collaborative analysis of {domain}"
    ) -> List[CollaborationSession]:
        """
        Run one round of collaborations.
        
        This is the main entry point that implements the flow:
        1. Pair agents
        2. For each pair, ask Lean for optimal perspective
        3. Spawn projectors in collapsed universe
        4. Coordinate critique and integration
        """
        # Select pairing strategy
        if pairing_strategy == "random":
            pairs = self.pair_agents_random()
        elif pairing_strategy == "complementary":
            pairs = self.pair_agents_complementary()
        elif pairing_strategy == "learned":
            pairs = self.pair_agents_learned()
        else:
            pairs = self.pair_agents_random()
        
        sessions = []
        
        for agent_a, agent_b in pairs:
            print(f"\n[Orchestrator] Pairing: {agent_a.name} ↔ {agent_b.name}")
            
            # Step 1: Ask Lean "What perspective maximizes consensus?"
            collision = self.bridge.select_best_perspective(agent_a.name, agent_b.name)
            
            if not collision:
                print(f"  No viable consensus found")
                continue
            
            if collision.consensus_strength < self.consensus_threshold:
                print(f"  Consensus {collision.consensus_strength:.2f} below threshold")
                continue
            
            print(f"  Selected: {collision.universe_a.value} × {collision.universe_b.value}")
            print(f"  Consensus: {collision.consensus_strength:.2f}")
            print(f"  Perspective: {collision.perspective.value}")
            
            # Step 2: Create task
            task = task_template.format(domain=f"{agent_a.name} + {agent_b.name}")
            
            # Step 3: Both agents initiate collaboration using precomputed collision
            context_a = agent_a.initiate_collaboration(agent_b, task, collision=collision)
            context_b = agent_b.initiate_collaboration(agent_a, task, collision=collision)
            
            if not context_a or not context_b:
                print(f"  Collaboration initiation failed")
                continue
            
            # Step 4: Create session
            session = CollaborationSession(
                session_id=context_a.collaboration_id,
                agent_a=agent_a.name,
                agent_b=agent_b.name,
                context=context_a,
                projectors=agent_a.spawned_projectors.copy()
            )
            
            # Step 5: Simulate projector execution
            projector_outputs = self._simulate_projectors(session)
            
            # Step 6: Critique using shared metric signature
            critiques = self._coordinate_critique(agent_a, agent_b, projector_outputs)
            session.critiques = critiques
            
            # Step 7: Integrate results
            integrated = agent_a.integrate_results(projector_outputs, critiques)
            session.integrated_result = integrated
            
            # Step 8: Update learned patterns
            self._update_learned_patterns(agent_a, agent_b, collision)
            
            # Step 9: Update metrics
            self._update_metrics(collision, session)
            
            sessions.append(session)
            self.sessions.append(session)
            
            print(f"  Session complete: {integrated.get('final_invariant', 0.0):.3f}")
        
        return sessions
    
    def _simulate_projectors(
        self, 
        session: CollaborationSession
    ) -> List[Dict[str, Any]]:
        """Simulate projector agent execution"""
        outputs = []
        
        for projector in session.projectors:
            # Simulate execution in specific universe
            output = {
                "projector_id": projector["id"],
                "universe": projector["universe"],
                "content": {
                    "analysis": f"Analysis from {projector['universe']} perspective",
                    "confidence": random.uniform(0.6, 0.95)
                }
            }
            outputs.append(output)
        
        return outputs
    
    def _coordinate_critique(
        self,
        agent_a: GeoWeirdAwareAgent,
        agent_b: GeoWeirdAwareAgent,
        projector_outputs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Coordinate critique between agents using shared metric"""
        critiques = []
        
        # Agent A critiques
        for output in projector_outputs:
            critique = agent_a.critique_output(
                output=json.dumps(output),
                criteria=["completeness", "consistency", "novelty"],
                other_agent=agent_b
            )
            critiques.append(critique)
        
        # Agent B critiques
        for output in projector_outputs:
            critique = agent_b.critique_output(
                output=json.dumps(output),
                criteria=["completeness", "consistency", "novelty"],
                other_agent=agent_a
            )
            critiques.append(critique)
        
        return critiques
    
    def _update_learned_patterns(
        self,
        agent_a: GeoWeirdAwareAgent,
        agent_b: GeoWeirdAwareAgent,
        collision: CollisionResult
    ):
        """Update learned successful collaboration patterns"""
        # Record successful pair
        pair = tuple(sorted([agent_a.name, agent_b.name]))
        if pair not in self.successful_pairs:
            self.successful_pairs.append(pair)
        
        # Update universe preferences
        self.universe_preferences[agent_a.name][collision.universe_a] += collision.consensus_strength
        self.universe_preferences[agent_b.name][collision.universe_b] += collision.consensus_strength
        
        # Update agents' internal preferences
        self.bridge.update_domain_after_collision(agent_a.name, collision)
        self.bridge.update_domain_after_collision(agent_b.name, collision)
    
    def _update_metrics(
        self,
        collision: CollisionResult,
        session: CollaborationSession
    ):
        """Update swarm metrics"""
        self.metrics.total_collaborations += 1
        self.metrics.successful_collaborations += 1
        
        # Universe distribution
        u_name = collision.universe_a.value
        self.metrics.universe_distribution[u_name] = \
            self.metrics.universe_distribution.get(u_name, 0) + 1
        
        # Perspective distribution
        p_name = collision.perspective.value
        self.metrics.perspective_distribution[p_name] = \
            self.metrics.perspective_distribution.get(p_name, 0) + 1
        
        # Average consensus (EMA)
        self.metrics.average_consensus = (
            0.9 * self.metrics.average_consensus +
            0.1 * collision.consensus_strength
        )
    
    # ========================================================================
    # CONVERGENCE DETECTION
    # ========================================================================
    
    def check_convergence(self, threshold: float = 0.8) -> Dict[str, UniverseType]:
        """Check which agents have converged on single universe type"""
        converged = {}
        
        for name, agent in self.agents.items():
            u_type = self.bridge.has_converged(name, threshold)
            if u_type:
                converged[name] = u_type
        
        self.metrics.convergence_rate = len(converged) / len(self.agents) if self.agents else 0.0
        
        return converged
    
    def run_to_convergence(
        self,
        max_rounds: int = 10,
        convergence_threshold: float = 0.8
    ) -> List[CollaborationSession]:
        """Run collaboration rounds until agents converge"""
        all_sessions = []
        
        for round_num in range(max_rounds):
            print(f"\n{'='*60}")
            print(f"COLLABORATION ROUND {round_num + 1}/{max_rounds}")
            print(f"{'='*60}")
            
            sessions = self.run_collaboration_round()
            all_sessions.extend(sessions)
            
            # Check convergence
            converged = self.check_convergence(convergence_threshold)
            print(f"\nConverged agents: {len(converged)}/{len(self.agents)}")
            
            if len(converged) == len(self.agents):
                print("\n✓ All agents converged!")
                break
        
        return all_sessions
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive swarm report"""
        # Learned rules from collision history
        learned_rules = self.bridge.get_learned_rules()
        
        # Converged agents
        converged = self.check_convergence()
        
        return {
            "metrics": {
                "total_collaborations": self.metrics.total_collaborations,
                "successful_collaborations": self.metrics.successful_collaborations,
                "average_consensus": self.metrics.average_consensus,
                "convergence_rate": self.metrics.convergence_rate,
                "universe_distribution": self.metrics.universe_distribution,
                "perspective_distribution": self.metrics.perspective_distribution
            },
            "learned_rules": learned_rules,
            "converged_agents": {
                name: u_type.value for name, u_type in converged.items()
            },
            "sessions": [s.to_dict() for s in self.sessions],
            "successful_pairs": list(self.successful_pairs)
        }
    
    def print_report(self):
        """Print formatted report"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("GEOWEIRD SWARM ORCHESTRATOR REPORT")
        print("="*60)
        
        print("\n📊 Metrics:")
        print(f"  Total collaborations: {report['metrics']['total_collaborations']}")
        print(f"  Successful: {report['metrics']['successful_collaborations']}")
        print(f"  Average consensus: {report['metrics']['average_consensus']:.3f}")
        print(f"  Convergence rate: {report['metrics']['convergence_rate']:.1%}")
        
        print("\n🌌 Universe Distribution:")
        for u_name, count in report['metrics']['universe_distribution'].items():
            print(f"  {u_name}: {count}")
        
        print("\n👁 Perspective Distribution:")
        for p_name, count in report['metrics']['perspective_distribution'].items():
            print(f"  {p_name}: {count}")
        
        print("\n📜 Learned Rules:")
        for rule in report['learned_rules']:
            print(f"  {rule['universe_type']}: conf={rule['confidence']:.2f}, "
                  f"evidence={rule['evidence_count']}")
        
        print("\n✓ Converged Agents:")
        for name, u_type in report['converged_agents'].items():
            print(f"  {name}: {u_type}")
        
        print("\n" + "="*60)


# ================================================================================
# MAIN ENTRY POINT
# ================================================================================

def run_geo_weird_swarm(
    md_path: Optional[Path] = None,
    max_rounds: int = 5,
    consensus_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Run complete GeoWeird swarm with self-typing.
    
    Usage:
        result = run_geo_weird_swarm(
            md_path=Path("EXHAUSTIVE_DOMAIN_EXPERT_LIST.md"),
            max_rounds=10
        )
    """
    # Initialize self-typing bridge
    bridge = init_self_typing_bridge()
    
    # Create orchestrator
    orchestrator = GeoWeirdSwarmOrchestrator(
        self_typing_bridge=bridge,
        consensus_threshold=consensus_threshold
    )
    
    # Load agents
    if md_path and md_path.exists():
        orchestrator.load_from_markdown(md_path)
    else:
        # Create demo agents
        demo_agents = [
            create_geo_weird_agent("Lighthouse Keeper", constraints_7d={
                "T": 0.8, "S": 0.7, "C": 0.6, "F": 0.5, "R": 0.9, "P": 0.4, "W": 0.3
            }),
            create_geo_weird_agent("Maritime Chart", constraints_7d={
                "T": 0.3, "S": 0.9, "C": 0.2, "F": 0.4, "R": 0.1, "P": 0.6, "W": 0.2
            }),
            create_geo_weird_agent("Fog Signal", constraints_7d={
                "T": 0.9, "S": 0.3, "C": 0.7, "F": 0.6, "R": 0.2, "P": 0.5, "W": 0.8
            }),
            create_geo_weird_agent("Lens Prism", constraints_7d={
                "T": 0.4, "S": 0.6, "C": 0.3, "F": 0.8, "R": 0.95, "P": 0.7, "W": 0.4
            }),
        ]
        orchestrator.register_agents(demo_agents)
    
    print(f"Loaded {len(orchestrator.agents)} agents")
    
    # Run to convergence
    sessions = orchestrator.run_to_convergence(max_rounds=max_rounds)
    
    # Generate report
    orchestrator.print_report()
    
    return orchestrator.generate_report()


if __name__ == "__main__":
    # Demo run
    result = run_geo_weird_swarm()
    print("\n" + json.dumps(result, indent=2))
