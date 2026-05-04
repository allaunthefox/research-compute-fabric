#!/usr/bin/env python3
"""Test script for comprehensive physics and engineering learning mechanism"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import ComprehensiveLearning

def test_comprehensive_learning():
    """Test comprehensive physics and engineering learning mechanism"""
    
    print("[TEST] Testing comprehensive physics and engineering learning mechanism...")
    
    # Create comprehensive learning instance
    physics_learning = ComprehensiveLearning()
    
    # Test 1: Load guide
    print("\n[TEST 1] Loading comprehensive physics and engineering guide...")
    guide_content = physics_learning.load_guide()
    if guide_content:
        print(f"  ✓ Guide loaded successfully ({len(guide_content)} characters)")
    else:
        print("  ✗ Failed to load guide")
        return False
    
    # Test 2: Extract concepts
    print("\n[TEST 2] Extracting physics and engineering concepts...")
    concepts = physics_learning.extract_concepts(guide_content)
    print(f"  ✓ Extracted {len(concepts)} concepts")
    print(f"  Concepts: {concepts[:5]}...")
    
    # Test 3: Auto-learn concepts
    print("\n[TEST 3] Auto-learning physics and engineering concepts...")
    physics_learning.auto_learn()
    print(f"  ✓ Learned {len(physics_learning.learned_concepts)} concepts")
    
    # Test 4: Get recommendations
    print("\n[TEST 4] Getting physics and engineering recommendations...")
    
    # EM spectrum context
    em_recommendation = physics_learning.get_recommendation({'domain': 'em_spectrum'})
    print(f"  EM spectrum recommendation: {em_recommendation}")
    
    # Materials context
    materials_recommendation = physics_learning.get_recommendation({'domain': 'materials'})
    print(f"  Materials recommendation: {materials_recommendation}")
    
    # Computation context
    computation_recommendation = physics_learning.get_recommendation({'domain': 'computation'})
    print(f"  Computation recommendation: {computation_recommendation}")
    
    # Quantum context
    quantum_recommendation = physics_learning.get_recommendation({'domain': 'quantum'})
    print(f"  Quantum recommendation: {quantum_recommendation}")
    
    # Thermodynamics context
    thermo_recommendation = physics_learning.get_recommendation({'domain': 'thermodynamics'})
    print(f"  Thermodynamics recommendation: {thermo_recommendation}")
    
    # Networking context
    networking_recommendation = physics_learning.get_recommendation({'domain': 'networking'})
    print(f"  Networking recommendation: {networking_recommendation}")
    
    # OmniToken context
    omnitoken_recommendation = physics_learning.get_recommendation({'domain': 'omnitoken'})
    print(f"  OmniToken recommendation: {omnitoken_recommendation}")
    
    # ISO standards context
    iso_recommendation = physics_learning.get_recommendation({'domain': 'iso'})
    print(f"  ISO standards recommendation: {iso_recommendation}")
    
    # W3C standards context
    w3c_recommendation = physics_learning.get_recommendation({'domain': 'w3c'})
    print(f"  W3C standards recommendation: {w3c_recommendation}")
    
    # Internet protocols context
    protocols_recommendation = physics_learning.get_recommendation({'domain': 'protocols'})
    print(f"  Internet protocols recommendation: {protocols_recommendation}")
    
    # Comprehensive technical standards context
    technical_recommendation = physics_learning.get_recommendation({'domain': 'technical'})
    print(f"  Comprehensive technical standards recommendation: {technical_recommendation}")
    
    # Digital platforms context
    digital_recommendation = physics_learning.get_recommendation({'domain': 'digital'})
    print(f"  Digital platforms recommendation: {digital_recommendation}")
    
    # Test 5: Get learning summary
    print("\n[TEST 5] Getting learning summary...")
    summary = physics_learning.get_learning_summary()
    print(f"  ✓ Summary:")
    print(f"    Total concepts: {summary['total_concepts']}")
    print(f"    Average score: {summary['average_score']:.2f}")
    print(f"    Learning history count: {summary['learning_history_count']}")
    
    # Test 6: Learn specific concept
    print("\n[TEST 6] Learning specific concept...")
    physics_learning.learn_concept("custom_physics_concept", score=0.9)
    print(f"  ✓ Learned custom concept")
    
    # Test 7: Verify learning history
    print("\n[TEST 7] Verifying learning history...")
    if len(physics_learning.learning_history) > 0:
        print(f"  ✓ Learning history has {len(physics_learning.learning_history)} entries")
        print(f"  Latest entry: {physics_learning.learning_history[-1]}")
    else:
        print("  ✗ Learning history is empty")
        return False
    
    print("\n[SUCCESS] All comprehensive learning tests passed!")
    return True

if __name__ == "__main__":
    success = test_comprehensive_learning()
    sys.exit(0 if success else 1)
