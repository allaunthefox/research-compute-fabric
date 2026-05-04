#!/usr/bin/env python3
"""Test script for biological learning mechanism"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import BiologicalLearning

def test_biological_learning():
    """Test biological learning mechanism"""
    
    print("[TEST] Testing biological learning mechanism...")
    
    # Create biological learning instance
    bio_learning = BiologicalLearning()
    
    # Test 1: Load guide
    print("\n[TEST 1] Loading biological systems guide...")
    guide_content = bio_learning.load_guide()
    if guide_content:
        print(f"  ✓ Guide loaded successfully ({len(guide_content)} characters)")
    else:
        print("  ✗ Failed to load guide")
        return False
    
    # Test 2: Extract principles
    print("\n[TEST 2] Extracting biological optimization principles...")
    principles = bio_learning.extract_principles(guide_content)
    print(f"  ✓ Extracted {len(principles)} principles")
    print(f"  Principles: {principles[:5]}...")
    
    # Test 3: Auto-learn principles
    print("\n[TEST 3] Auto-learning biological optimization principles...")
    bio_learning.auto_learn()
    print(f"  ✓ Learned {len(bio_learning.learned_principles)} principles")
    
    # Test 4: Get recommendations
    print("\n[TEST 4] Getting biological optimization recommendations...")
    
    # Network context
    network_recommendation = bio_learning.get_recommendation({'domain': 'network'})
    print(f"  Network recommendation: {network_recommendation}")
    
    # Transport context
    transport_recommendation = bio_learning.get_recommendation({'domain': 'transport'})
    print(f"  Transport recommendation: {transport_recommendation}")
    
    # Energy context
    energy_recommendation = bio_learning.get_recommendation({'domain': 'energy'})
    print(f"  Energy recommendation: {energy_recommendation}")
    
    # Resilience context
    resilience_recommendation = bio_learning.get_recommendation({'domain': 'resilience'})
    print(f"  Resilience recommendation: {resilience_recommendation}")
    
    # Test 5: Get learning summary
    print("\n[TEST 5] Getting learning summary...")
    summary = bio_learning.get_learning_summary()
    print(f"  ✓ Summary:")
    print(f"    Total principles: {summary['total_principles']}")
    print(f"    Average score: {summary['average_score']:.2f}")
    print(f"    Learning history count: {summary['learning_history_count']}")
    
    # Test 6: Learn specific principle
    print("\n[TEST 6] Learning specific principle...")
    bio_learning.learn_principle("custom_bio_principle", score=0.9)
    print(f"  ✓ Learned custom principle")
    
    # Test 7: Verify learning history
    print("\n[TEST 7] Verifying learning history...")
    if len(bio_learning.learning_history) > 0:
        print(f"  ✓ Learning history has {len(bio_learning.learning_history)} entries")
        print(f"  Latest entry: {bio_learning.learning_history[-1]}")
    else:
        print("  ✗ Learning history is empty")
        return False
    
    print("\n[SUCCESS] All biological learning tests passed!")
    return True

if __name__ == "__main__":
    success = test_biological_learning()
    sys.exit(0 if success else 1)
