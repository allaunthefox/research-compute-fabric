"""
Demonstration of GeoWeird Self-Typing Bridge

Shows the complete flow:
1. Domain expert with 7D constraints
2. Registration with SelfTypingBridge
3. Multi-typed superposition
4. Collision with another domain
5. Perspective collapse
6. Projector spawning
7. Critique with shared metric
8. Invariant derivation
"""

import json
from pathlib import Path

from geoweird.self_typing_bridge import (
    init_self_typing_bridge, SelfTypingBridge,
    UniverseType, Perspective
)

from geoweird.geo_aware_agent import (
    create_geo_weird_agent, GeoWeirdAwareAgent
)

from geoweird.swarm_orchestrator_v2 import (
    GeoWeirdSwarmOrchestrator, run_geo_weird_swarm
)


def demo_individual_agent():
    """Demo: Single agent registration and superposition"""
    print("="*70)
    print("DEMO 1: Individual Agent Registration")
    print("="*70)
    
    # Initialize bridge
    bridge = init_self_typing_bridge()
    
    # Create Lighthouse Keeper with 7D constraints
    keeper = create_geo_weird_agent(
        name="Lighthouse Keeper",
        constraints_7d={
            "T": 0.8,   # High temporal (flash interval)
            "S": 0.7,   # High spatial (tower structure)
            "C": 0.6,   # Moderate causal (event ordering)
            "F": 0.5,   # Moderate field (light propagation)
            "R": 0.9,   # High rotational (Fresnel lens)
            "P": 0.4,   # Low phase (steady state)
            "W": 0.3    # Low wave (local scope)
        }
    )
    
    print(f"\nAgent: {keeper.name}")
    print(f"Registered with SelfTypingBridge ✓")
    
    # Show extracted features
    print("\n📐 Extracted Constraint Features:")
    f = keeper.domain.features
    print(f"  Mean curvature: {f.meanCurvature:.2f}")
    print(f"  Rotational symmetry: {f.rotationalSymmetry:.2f}")
    print(f"  Translational symmetry: {f.translationalSymmetry:.2f}")
    print(f"  Has temporal ordering: {f.hasTemporalOrdering}")
    print(f"  Causal cone angle: {f.causalConeAngle:.2f}")
    print(f"  Is compact: {f.isCompact}")
    print(f"  Volume growth rate: {f.volumeGrowthRate:.2f}")
    
    # Show universe scores
    print("\n🌌 Universe Type Scores:")
    s = keeper.domain.scores
    print(f"  Σ₁ Euclidean:   {s.euclidean:.2f}  (physical structure)")
    print(f"  Σ₂ Hyperbolic:  {s.hyperbolic:.2f}  (information tree)")
    print(f"  Σ₃ Spherical:   {s.spherical:.2f}  (Fresnel rotation)")
    print(f"  Σ₄ Lorentzian:  {s.lorentzian:.2f} (flash causality)")
    print(f"  Σ₅ Custom:      {s.custom:.2f}  (keeper social)")
    
    # Show superposition
    print("\n⚛️ Multi-Typed Superposition:")
    for entry in keeper.get_superposition():
        print(f"  {entry.perspective.value} → {entry.universe_type.value} (weight: {entry.weight:.2f})")
    
    # Check if multi-typed
    if s.should_multi_type(0.5):
        print("\n✓ Agent is MULTI-TYPED (maintaining superposition)")
    
    return keeper


def demo_collision():
    """Demo: Collision between two agents"""
    print("\n" + "="*70)
    print("DEMO 2: Domain Collision & Perspective Selection")
    print("="*70)
    
    bridge = init_self_typing_bridge()
    
    # Create two agents
    keeper = create_geo_weird_agent(
        name="Lighthouse Keeper",
        constraints_7d={"T": 0.8, "S": 0.7, "C": 0.6, "F": 0.5, "R": 0.9, "P": 0.4, "W": 0.3}
    )
    
    chart = create_geo_weird_agent(
        name="Maritime Chart",
        constraints_7d={"T": 0.3, "S": 0.9, "C": 0.2, "F": 0.4, "R": 0.1, "P": 0.6, "W": 0.2}
    )
    
    print(f"\nColliding: {keeper.name} ↔ {chart.name}")
    
    # Try all perspective combinations
    collisions = bridge.collide_domains(keeper.name, chart.name)
    
    print(f"\n🔀 Perspective Combinations Tried:")
    for i, c in enumerate(collisions[:5], 1):
        print(f"  {i}. {c.universe_a.value} × {c.universe_b.value}")
        print(f"     Consensus: {c.consensus_strength:.2f}")
        print(f"     Perspective: {c.perspective.value}")
        print(f"     Intersection volume: {c.intersection_volume:.1f}")
    
    # Select best
    best = bridge.select_best_perspective(keeper.name, chart.name)
    
    if best:
        print(f"\n✓ SELECTED: {best.universe_a.value} × {best.universe_b.value}")
        print(f"  Consensus: {best.consensus_strength:.2f}")
        print(f"  Perspective: {best.perspective.value}")
        print(f"\n  → Keeper will operate in {best.universe_a.value} universe")
        print(f"  → Chart will operate in {best.universe_b.value} universe")
        print(f"  → Shared perspective: {best.perspective.value}")
    
    return keeper, chart, best


def demo_collaboration():
    """Demo: Full collaboration with projectors and critique"""
    print("\n" + "="*70)
    print("DEMO 3: Full Collaboration Flow")
    print("="*70)
    
    bridge = init_self_typing_bridge()
    
    # Create agents
    keeper = create_geo_weird_agent(
        name="Lighthouse Keeper",
        constraints_7d={"T": 0.8, "S": 0.7, "C": 0.6, "F": 0.5, "R": 0.9, "P": 0.4, "W": 0.3}
    )
    
    chart = create_geo_weird_agent(
        name="Maritime Chart",
        constraints_7d={"T": 0.3, "S": 0.9, "C": 0.2, "F": 0.4, "R": 0.1, "P": 0.6, "W": 0.2}
    )
    
    print(f"\nInitiating collaboration: {keeper.name} + {chart.name}")
    
    # Initiate collaboration
    context = keeper.initiate_collaboration(
        chart, 
        task_description="Coordinate lighthouse visibility with chart navigation"
    )
    
    if not context:
        print("Collaboration failed!")
        return
    
    print(f"\n📍 Collaboration Context:")
    print(f"  Universe: {context.universe_type.value}")
    print(f"  Perspective: {context.perspective.value}")
    print(f"  Metric signature: {context.metric_signature}")
    print(f"  Curvature: {context.curvature}")
    
    # Show spawned projectors
    print(f"\n🎬 Spawned Projectors ({len(keeper.spawned_projectors)}):")
    for p in keeper.spawned_projectors:
        print(f"  {p['id']} in {p['universe']} universe")
    
    # Simulate critique
    print(f"\n🔍 Critique (using shared metric {context.metric_signature}):")
    
    mock_output = json.dumps({"visibility_range": 20000, "flash_interval": 5})
    critique = keeper.critique_output(
        output=mock_output,
        criteria=["completeness", "consistency", "novelty"],
        other_agent=chart
    )
    
    print(f"  Evaluations:")
    for criterion, score in critique.get("evaluations", {}).items():
        print(f"    {criterion}: {score:.2f}")
    print(f"  Invariant: {critique.get('invariant', 0.0):.3f}")
    print(f"  Confidence: {critique.get('confidence', 0.0):.3f}")
    
    return keeper, chart, context, critique


def demo_swarm_orchestration():
    """Demo: Full swarm with multiple agents"""
    print("\n" + "="*70)
    print("DEMO 4: Swarm Orchestration")
    print("="*70)
    
    # Run complete swarm
    result = run_geo_weird_swarm(max_rounds=3)
    
    return result


def demo_learned_rules():
    """Demo: Show rules learned from collisions"""
    print("\n" + "="*70)
    print("DEMO 5: Learned Typing Rules")
    print("="*70)
    
    bridge = init_self_typing_bridge()
    
    # Create and collide multiple agents to generate rules
    agents = [
        ("Lighthouse Keeper", {"T": 0.8, "S": 0.7, "C": 0.6, "F": 0.5, "R": 0.9, "P": 0.4, "W": 0.3}),
        ("Maritime Chart", {"T": 0.3, "S": 0.9, "C": 0.2, "F": 0.4, "R": 0.1, "P": 0.6, "W": 0.2}),
        ("Fog Signal", {"T": 0.9, "S": 0.3, "C": 0.7, "F": 0.6, "R": 0.2, "P": 0.5, "W": 0.8}),
        ("Lens Prism", {"T": 0.4, "S": 0.6, "C": 0.3, "F": 0.8, "R": 0.95, "P": 0.7, "W": 0.4}),
        ("Keeper's Log", {"T": 0.6, "S": 0.4, "C": 0.5, "F": 0.3, "R": 0.3, "P": 0.8, "W": 0.5}),
    ]
    
    # Register all agents
    for name, constraints in agents:
        create_geo_weird_agent(name, constraints_7d=constraints)
    
    # Generate collisions
    for i, (name_a, _) in enumerate(agents):
        for name_b, _ in agents[i+1:]:
            bridge.collide_domains(name_a, name_b)
    
    # Get learned rules
    rules = bridge.get_learned_rules()
    
    print(f"\n📜 Learned from {len(bridge.get_collision_history())} collisions:")
    print(f"\nDiscovered {len(rules)} typing rules:")
    
    for rule in rules:
        print(f"\n  Rule: {rule['universe_type']}")
        print(f"    Confidence: {rule['confidence']:.2f}")
        print(f"    Evidence: {rule['evidence_count']} collisions")
        print(f"    Pattern: {rule['pattern']}")
    
    print("\n✓ These rules were DISCOVERED, not pre-programmed!")
    print("  The swarm learned which constraint features map to which universe types.")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("GEOWEIRD SELF-TYPING BRIDGE DEMONSTRATION")
    print("="*70)
    print("\nThis demonstrates the critical bridge from Lean formalism to Python native agents.")
    print("The bridge maps 7D constraints → ConstraintFeatures → MultiTypedDomain.")
    
    # Run demos
    demo_individual_agent()
    demo_collision()
    demo_collaboration()
    demo_swarm_orchestration()
    demo_learned_rules()
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("  1. Agents register with 7D constraints")
    print("  2. SelfTypingBridge maps to ConstraintFeatures")
    print("  3. MultiTypedDomain maintains superposition")
    print("  4. Collision selects optimal perspective")
    print("  5. Projectors spawn IN THAT UNIVERSE")
    print("  6. Critique uses shared metric signature")
    print("  7. Invariant derived from manifold geometry")
    print("  8. Rules learned from collision history")
    print("\nThe swarm is now GeoWeird-aware! 🌌")


if __name__ == "__main__":
    main()
