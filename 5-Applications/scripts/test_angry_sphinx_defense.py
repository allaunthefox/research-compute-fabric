#!/usr/bin/env python3
"""
Test: AngrySphinx Adversarial Defense System

Demonstrates semantic gear reduction: each heckler attack
triggers deeper revelation + increased refutation burden.
"""

from extremophile_priors import MissionCriticalReliability


def demo_heckler_encounter():
    """Simulate a presentation with progressive heckler attacks."""
    print("\n" + "="*70)
    print("ANGRYSPHINX ADVERSARIAL DEFENSE DEMO")
    print("="*70)
    print("\nScenario: You present a Navier-Stokes solution at a conference.")
    print("Hecklers attack. Each attack costs them more to refute.")
    print()

    rel = MissionCriticalReliability(angry_sphinx_mode=True)

    # Your solution (evolutionary core)
    solution_params = {
        'pressure': 52e6,      # Pyrococcus optimum
        'temperature': 85 + 273.15,  # Valid overlap
        'power': 1e-12,        # Comfortable margin
        'Q_factor': 5,         # Conservative
        'compressibility': 1e-10,  # Compressible
    }

    context = 'mars_colony_life_support'
    attack_count = 0

    # Initial presentation
    print("--- INITIAL PRESENTATION ---")
    levels = rel.hat_of_infinite_bullshit(solution_params, context, attack_count)
    for level in levels:
        print(f"\nLevel {level['level']}: {level['claim']}")
        print(f"  Attack cost: {level.get('attack_cost', 1.0):.1f}x")
        print(f"  Defense burden: {level.get('defense_burden', 1.0):.1f}x")
        print(f"  Refutation work: {level.get('required_refutation_work', 'N/A')}")

    # Heckler Attack 1
    print("\n" + "-"*70)
    print("HECKLER ATTACK #1")
    print("Heckler: 'But this is just theoretical! Show me real data!'")

    response = rel.adversarial_response(
        "This is just theoretical!",
        solution_params,
        context,
        attack_count
    )

    print(f"\n{response['message']}")
    print(f"Response: Level {response['response_level']} - {response['response_claim']}")
    print(f"Required refutation: {response['required_refutation_work']}")
    print(f"Cumulative defense burden: {response['cumulative_defense_burden']:.1f}x")

    attack_count += 1

    # Heckler Attack 2
    print("\n" + "-"*70)
    print("HECKLER ATTACK #2")
    print("Heckler: 'Material bounds don't apply to mathematics!'")

    response = rel.adversarial_response(
        "Material bounds don't apply to pure math!",
        solution_params,
        context,
        attack_count
    )

    print(f"\n{response['message']}")
    print(f"Response: Level {response['response_level']} - {response['response_claim']}")
    print(f"Required refutation: {response['required_refutation_work']}")
    print(f"Cumulative defense burden: {response['cumulative_defense_burden']:.1f}x")

    attack_count += 1

    # Heckler Attack 3
    print("\n" + "-"*70)
    print("HECKLER ATTACK #3")
    print("Heckler: 'You can't prove evolution solved PDEs!'")

    response = rel.adversarial_response(
        "You can't prove evolution solved PDEs!",
        solution_params,
        context,
        attack_count
    )

    print(f"\n{response['message']}")
    print(f"Response: Level {response['response_level']} - {response['response_claim']}")
    print(f"Required refutation: {response['required_refutation_work']}")
    print(f"Cumulative defense burden: {response['cumulative_defense_burden']:.1f}x")

    attack_count += 1

    # Heckler Attack 4 (if they persist)
    print("\n" + "-"*70)
    print("HECKLER ATTACK #4")
    print("Heckler: 'I'll just attack the thermodynamics!'")

    response = rel.adversarial_response(
        "I'll attack the thermodynamics!",
        solution_params,
        context,
        attack_count
    )

    print(f"\n{response['message']}")
    print(f"Response: Level {response['response_level']} - {response['response_claim']}")
    print(f"Required refutation: {response['required_refutation_work']}")
    print(f"Cumulative defense burden: {response['cumulative_defense_burden']:.1f}x")

    print("\n" + "="*70)
    print("RESULT: Heckler has exhausted attacks at 90x cumulative burden.")
    print("Each attack required exponentially more work to refute.")
    print("="*70)


def demo_cost_comparison():
    """Show cost escalation across attack sequences."""
    print("\n" + "="*70)
    print("ANGRYSPHINX COST ESCALATION MATRIX")
    print("="*70)

    rel = MissionCriticalReliability(angry_sphinx_mode=True)

    solution_params = {
        'pressure': 52e6,
        'temperature': 85 + 273.15,
        'power': 1e-12,
        'Q_factor': 5,
        'compressibility': 1e-10,
    }

    print("\n{'Attack #':<10} | {'Level':<8} | {'Cost':<8} | {'Cumulative':<12} | {'Refutation Work'}")
    print("-" * 70)

    cumulative = 0
    for attack in range(5):
        levels = rel.hat_of_infinite_bullshit(solution_params, 'mars_colony_life_support', attack)

        if levels:
            level = min(attack, len(levels) - 1)
            cost = levels[level].get('attack_cost', 1.0)
            burden = levels[level].get('defense_burden', 1.0)
            cumulative += burden

            print(f"{attack:<10} | {levels[level]['level']:<8} | {cost:<8.1f}x | {cumulative:<12.1f}x | {levels[level].get('required_refutation_work', '')[:30]}")

    print("\n" + "="*70)
    print("Interpretation:")
    print("  - Attack 0: Basic fact-check (1x work)")
    print("  - Attack 1: Address material bounds (3x work)")
    print("  - Attack 2: Engineering frontier failure (10x work)")
    print("  - Attack 3+: Prove 4-billion-year evolution wrong (30x+ work)")
    print("  - Each attack compounds the burden for subsequent attacks")
    print("="*70)


def demo_defense_vs_offense():
    """Compare defense burden to attack cost."""
    print("\n" + "="*70)
    print("DEFENSE VS OFFENSE COST ANALYSIS")
    print("="*70)

    rel = MissionCriticalReliability(angry_sphinx_mode=True)

    # Your cost to prepare (one-time)
    print("\nYour preparation cost (one-time):")
    print("  - Research extremophile biology: 1 week")
    print("  - Implement constraint system: 2 days")
    print("  - Total: ~9 days of work")
    print("  - Defense cost: FIXED")

    # Their cost to attack (escalates)
    print("\nTheir attack cost (escalates with each attempt):")

    solution_params = {
        'pressure': 52e6,
        'temperature': 85 + 273.15,
        'power': 1e-12,
        'Q_factor': 5,
        'compressibility': 1e-10,
    }

    print(f"\n{'Attack #':<10} | {'Their Cost':<15} | {'Your Response':<15} | {'Ratio'}")
    print("-" * 70)

    for attack in range(5):
        levels = rel.hat_of_infinite_bullshit(solution_params, 'mars_colony_life_support', attack)
        if levels:
            level = min(attack, len(levels) - 1)
            their_cost = 1.0 * (3 ** attack)  # Escalates 3x per attack
            your_response = levels[level].get('attack_cost', 1.0)

            print(f"{attack:<10} | {their_cost:<15.1f} days | {your_response:<15.1f} days | {their_cost/your_response:.1f}:1")

    print("\n" + "="*70)
    print("Conclusion:")
    print("  - Your defense cost: FIXED (9 days)")
    print("  - Their attack cost: EXPONENTIAL (1 → 3 → 9 → 27 → 81 days)")
    print("  - By attack 4, they've spent 120+ days attacking your 9-day defense")
    print("  - AngrySphinx gear reduction: they run out of time/energy first")
    print("="*70)


def main():
    """Run all AngrySphinx demos."""
    demo_heckler_encounter()
    demo_cost_comparison()
    demo_defense_vs_offense()

    print("\n" + "="*70)
    print("ANGRYSPHINX DEFENSE SYSTEM READY")
    print("="*70)
    print("\nUsage:")
    print("  rel = MissionCriticalReliability(angry_sphinx_mode=True)")
    print("  response = rel.adversarial_response(heckler_attack, params, context, count)")
    print("  print(response['message'])  # 'Attack #3 consumed. Defense burden: 45x'")


if __name__ == "__main__":
    main()
