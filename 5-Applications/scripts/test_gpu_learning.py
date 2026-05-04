#!/usr/bin/env python3
"""Test script for GPU learning mechanism"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import GPULearning

def test_gpu_learning():
    """Test GPU learning mechanism"""
    
    print("[TEST] Testing GPU learning mechanism...")
    
    # Create GPU learning instance
    gpu_learning = GPULearning()
    
    # Test 1: Load guide
    print("\n[TEST 1] Loading GPU optimization guide...")
    guide_content = gpu_learning.load_guide()
    if guide_content:
        print(f"  ✓ Guide loaded successfully ({len(guide_content)} characters)")
    else:
        print("  ✗ Failed to load guide")
        return False
    
    # Test 2: Extract techniques
    print("\n[TEST 2] Extracting GPU optimization techniques...")
    techniques = gpu_learning.extract_techniques(guide_content)
    print(f"  ✓ Extracted {len(techniques)} techniques")
    print(f"  Techniques: {techniques[:5]}...")
    
    # Test 3: Auto-learn techniques
    print("\n[TEST 3] Auto-learning GPU optimization techniques...")
    gpu_learning.auto_learn()
    print(f"  ✓ Learned {len(gpu_learning.learned_techniques)} techniques")
    
    # Test 4: Get recommendations
    print("\n[TEST 4] Getting GPU optimization recommendations...")
    
    # CUDA context
    cuda_recommendation = gpu_learning.get_recommendation({'api': 'cuda'})
    print(f"  CUDA recommendation: {cuda_recommendation}")
    
    # Vulkan context
    vulkan_recommendation = gpu_learning.get_recommendation({'api': 'vulkan'})
    print(f"  Vulkan recommendation: {vulkan_recommendation}")
    
    # Unsloth context
    unsloth_recommendation = gpu_learning.get_recommendation({'api': 'unsloth'})
    print(f"  Unsloth recommendation: {unsloth_recommendation}")
    
    # PyTorch context
    pytorch_recommendation = gpu_learning.get_recommendation({'api': 'pytorch'})
    print(f"  PyTorch recommendation: {pytorch_recommendation}")
    
    # Test 5: Get learning summary
    print("\n[TEST 5] Getting learning summary...")
    summary = gpu_learning.get_learning_summary()
    print(f"  ✓ Summary:")
    print(f"    Total techniques: {summary['total_techniques']}")
    print(f"    Average score: {summary['average_score']:.2f}")
    print(f"    Learning history count: {summary['learning_history_count']}")
    
    # Test 6: Learn specific technique
    print("\n[TEST 6] Learning specific technique...")
    gpu_learning.learn_technique("custom_gpu_optimization", score=0.9)
    print(f"  ✓ Learned custom technique")
    
    # Test 7: Verify learning history
    print("\n[TEST 7] Verifying learning history...")
    if len(gpu_learning.learning_history) > 0:
        print(f"  ✓ Learning history has {len(gpu_learning.learning_history)} entries")
        print(f"  Latest entry: {gpu_learning.learning_history[-1]}")
    else:
        print("  ✗ Learning history is empty")
        return False
    
    print("\n[SUCCESS] All GPU learning tests passed!")
    return True

if __name__ == "__main__":
    success = test_gpu_learning()
    sys.exit(0 if success else 1)
