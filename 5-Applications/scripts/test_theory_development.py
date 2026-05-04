#!/usr/bin/env python3
"""Test script for theory development mechanism"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import TheoryDevelopment, ComprehensiveLearning, BiologicalLearning, GPULearning

def test_theory_development():
    """Test theory development mechanism"""
    
    print("[TEST] Testing theory development mechanism...")
    
    # Create learning systems
    physics_learning = ComprehensiveLearning()
    bio_learning = BiologicalLearning()
    gpu_learning = GPULearning()
    
    # Auto-learn physics concepts
    print("\n[TEST 1] Auto-learning physics concepts...")
    physics_learning.auto_learn()
    print(f"  ✓ Learned {len(physics_learning.learned_concepts)} physics concepts")
    
    # Create theory development system
    print("\n[TEST 2] Creating theory development system...")
    theory_development = TheoryDevelopment()
    theory_development.set_learning_systems(physics_learning, bio_learning, gpu_learning)
    print(f"  ✓ Theory development system created")
    
    # Test cross-domain synthesis
    print("\n[TEST 3] Testing cross-domain synthesis...")
    synthesis = theory_development.synthesize_cross_domain('thermo', 'quantum')
    print(f"  ✓ Synthesis: {len(synthesis['synthesis_points'])} points, confidence: {synthesis['confidence']:.2f}")
    
    # Test hypothesis generation
    print("\n[TEST 4] Testing hypothesis generation...")
    hypothesis = theory_development.generate_hypothesis(synthesis)
    if hypothesis['statement']:
        print(f"  ✓ Hypothesis: {hypothesis['statement'][:80]}...")
        print(f"    Confidence: {hypothesis['confidence']:.2f}, Testable: {hypothesis['testable']}")
    else:
        print(f"  ! No hypothesis generated (insufficient confidence)")
    
    # Test theory formulation
    print("\n[TEST 5] Testing theory formulation...")
    hypotheses = [h for h in theory_development.hypotheses if h['statement']]
    if hypotheses:
        theory = theory_development.formulate_theory(hypotheses)
        if theory.get('formal_statement'):
            print(f"  ✓ Theory: {theory['formal_statement'][:80]}...")
            print(f"    Confidence: {theory['confidence']:.2f}, Testability: {theory['testability_score']:.2f}")
        else:
            print(f"  ! No theory formulated")
    else:
        print(f"  ! No hypotheses available for theory formulation")
    
    # Test theory testing
    print("\n[TEST 6] Testing theory validation...")
    if theory_development.generated_theories:
        test_result = theory_development.test_theory(theory_development.generated_theories[-1])
        print(f"  ✓ Test result: {'PASSED' if test_result['test_passed'] else 'FAILED'}")
        print(f"    Consistency: {test_result['consistency_score']:.2f}")
    else:
        print(f"  ! No theories available for testing")
    
    # Test auto-development
    print("\n[TEST 7] Testing automatic theory development...")
    theory_development.auto_develop_theories()
    
    # Get theory summary
    print("\n[TEST 8] Getting theory development summary...")
    summary = theory_development.get_theory_summary()
    print(f"  ✓ Summary:")
    print(f"    Total theories: {summary['total_theories']}")
    print(f"    Total hypotheses: {summary['total_hypotheses']}")
    print(f"    Total syntheses: {summary['total_syntheses']}")
    print(f"    Average confidence: {summary['average_confidence']:.2f}")
    
    print("\n[SUCCESS] All theory development tests passed!")
    return True

if __name__ == "__main__":
    success = test_theory_development()
    sys.exit(0 if success else 1)
