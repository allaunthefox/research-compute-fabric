#!/usr/bin/env python3
"""
Test: Hat of Infinite Bullshit — Progressive Revelation System

Demonstrates the "Um ack sh lee, I provide x. But... x(2). But... x(4)"
presentation architecture for mission-critical reliability assessment.
"""

import json
from extremophile_priors import MissionCriticalReliability, DeepExtremophilePrior


def demo_progressive_revelation():
    """Demonstrate the three-level presentation style."""
    print("\n" + "="*70)
    print("HAT OF INFINITE BULLSHIT — Progressive Revelation Demo")
    print("="*70)

    rel = MissionCriticalReliability()

    # Scenario 1: Evolutionary core solution (clean approval)
    print("\n--- Scenario 1: Mars Colony Life Support (EVOLUTIONARY CORE) ---")

    mars_params = {
        'pressure': 52e6,      # Pyrococcus optimum
        'temperature': 85 + 273.15,  # 85°C - overlap of Pyrococcus (80-108) and Thermococcus (60-90)
        'power': 1e-12,        # Comfortable margin above 10^-15 W
        'Q_factor': 5,         # Conservative damping
        'compressibility': 1e-10,  # Well above zero
    }

    levels = rel.hat_of_infinite_bullshit(mars_params, 'mars_colony_life_support')

    for level in levels:
        print(f"\nLevel {level['level']}: {level['claim']}")
        if 'zone' in level:
            print(f"  Zone: {level['zone']}")
            print(f"  Details: {level['details']}")
        if 'approved' in level.get('details', {}):
            print(f"  ✓ APPROVED for autonomous operation")

    # Scenario 2: Engineering frontier (the "but..." moment)
    print("\n--- Scenario 2: Nanoscale Sensor (ENGINEERING FRONTIER) ---")

    frontier_params = {
        'pressure': 100e6,     # Near Pyrococcus limit
        'temperature': 85 + 273.15,  # 85°C - within both ranges
        'power': 1e-14,        # Only 10x above minimum
        'Q_factor': 80,        # Near material limit of 100
        'compressibility': 1e-11,  # Very stiff
    }

    levels = rel.hat_of_infinite_bullshit(frontier_params, 'mars_colony_life_support')

    for level in levels:
        print(f"\nLevel {level['level']}: {level['claim']}")
        if 'requirement' in level:
            print(f"  {level['requirement']}")
            print(f"  {level['actual']}")
            print(f"  ⚠️ INSUFFICIENT for mission critical")
        if 'consequence' in level:
            print(f"  🚨 {level['consequence']}")
            print(f"  📋 {level['recommendation']}")

    # Scenario 3: Theoretical limit (rejection)
    print("\n--- Scenario 3: Theoretical Solution (THEORETICAL LIMIT) ---")

    theory_params = {
        'pressure': 1e5,     # Atmospheric
        'temperature': 300,   # Room temp
        'power': 1e-3,        # Milliwatt - comfortable
        'Q_factor': float('inf'),  # INFINITE Q (blow-up)
        'compressibility': 0.0,    # ZERO compressibility (incompressible)
    }

    result = rel.mission_critical_approval(theory_params, 'pure_mathematics')

    if not result.admissible:
        print(f"\n❌ REJECTED: {result.violated_constraint}")
        print(f"   Depth: {result.details.get('depth', 0)}")
        print(f"   Zone: {result.details.get('zone', 'UNKNOWN')}")
        print(f"\n   Physical blow-up detected.")
        print(f"   Even for pure mathematics: unphysical.")


def demo_context_matrix():
    """Show approval across different mission contexts."""
    print("\n" + "="*70)
    print("MISSION CONTEXT APPROVAL MATRIX")
    print("="*70)

    rel = MissionCriticalReliability()

    # Test solution at various depths
    test_cases = [
        ('Evolutionary Core', {
            'pressure': 52e6, 'temperature': 85 + 273.15, 'power': 1e-12,
            'Q_factor': 5, 'compressibility': 1e-10
        }),
        ('Engineering Frontier', {
            'pressure': 110e6, 'temperature': 85 + 273.15, 'power': 1e-14,
            'Q_factor': 80, 'compressibility': 1e-11
        }),
        ('Near Boundary', {
            'pressure': 120e6, 'temperature': 85 + 273.15, 'power': 5e-15,
            'Q_factor': 95, 'compressibility': 1e-12
        }),
    ]

    contexts = [
        'mars_colony_life_support',
        'deep_space_probe',
        'medical_implant',
        'lhc_experiment',
        'laboratory_demo',
        'pure_mathematics',
    ]

    print(f"\n{'Solution':<20} | {'Context':<25} | {'Depth':<6} | {'Approved':<10}")
    print("-" * 70)

    for name, params in test_cases:
        depth = rel.reliability_depth(params)
        zone = rel.zone_classification(depth)

        for context in contexts:
            result = rel.mission_critical_approval(params, context)
            approved = "✓ YES" if result.admissible else "✗ NO"

            print(f"{name:<20} | {context:<25} | {depth:.2f} | {approved:<10}")
        print("-" * 70)


def demo_navier_stokes_assessment():
    """Assess Navier-Stokes solutions with progressive revelation."""
    print("\n" + "="*70)
    print("NAVIER-STOKES SOLUTION ASSESSMENT")
    print("="*70)

    rel = MissionCriticalReliability()

    solutions = [
        ('Evolutionary Fluid', {
            'pressure': 52e6, 'temperature': 85 + 273.15,  # Valid for both
            'power': 1e-10, 'Q_factor': 10,
            'compressibility': 1e-9,  # Compressible
        }),
        ('Engineering Frontier Fluid', {
            'pressure': 100e6, 'temperature': 85 + 273.15,
            'power': 1e-12, 'Q_factor': 50,
            'compressibility': 1e-11,  # Very stiff
        }),
        ('Near-Incompressible', {
            'pressure': 75e6, 'temperature': 85 + 273.15,
            'power': 1e-10, 'Q_factor': 5,
            'compressibility': 1e-13,  # Dangerously close to zero
        }),
    ]

    for name, params in solutions:
        print(f"\n--- {name} ---")

        depth = rel.reliability_depth(params)
        zone = rel.zone_classification(depth)

        print(f"Reliability Depth: {depth:.3f}")
        print(f"Zone: {zone}")
        print(f"Description: {rel.zone_description(zone)}")

        # Progressive revelation
        levels = rel.hat_of_infinite_bullshit(params, 'deep_space_probe')

        print("\nPresentation:")
        for level in levels:
            print(f"  {level['level']}. {level['claim']}")
            if 'consequence' in level:
                print(f"     → {level['consequence']}")
            if 'recommendation' in level:
                print(f"     → {level['recommendation']}")

        # Approval for different contexts
        print("\nContext Approvals:")
        for context in ['mars_colony_life_support', 'lhc_experiment', 'pure_mathematics']:
            result = rel.mission_critical_approval(params, context)
            status = "✓" if result.admissible else "✗"
            print(f"  {status} {context}: {result.violated_constraint or 'APPROVED'}")


def main():
    """Run all demos."""
    demo_progressive_revelation()
    demo_context_matrix()
    demo_navier_stokes_assessment()

    print("\n" + "="*70)
    print("All demos completed.")
    print("="*70)
    print("\nUsage in presentations:")
    print("  from extremophile_priors import MissionCriticalReliability")
    print("  rel = MissionCriticalReliability()")
    print("  levels = rel.hat_of_infinite_bullshit(params, 'mars_colony')")
    print("  for level in levels:")
    print("      print(f'Level {level[\"level\"]}: {level[\"claim\"]}')")


if __name__ == "__main__":
    main()
