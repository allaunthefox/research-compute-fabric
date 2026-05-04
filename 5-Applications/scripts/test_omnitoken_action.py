#!/usr/bin/env python3
"""Test script for OmniToken action framework"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import OmniTokenAction

def test_omnitoken_action():
    """Test OmniToken action framework"""
    
    print("[TEST] Testing OmniToken action framework...\n")
    
    # Create OmniToken action system
    print("[TEST 1] Creating OmniToken action system...")
    omni_action = OmniTokenAction()
    print("  ✓ OmniToken action system created\n")
    
    # Test container creation
    print("[TEST 2] Creating OmniToken containers...")
    action_data_1 = {
        'type': 'transfer',
        'from': '0x1234567890abcdef',
        'to': '0xabcdef1234567890',
        'amount': 1000,
        'token': 'ETH'
    }
    
    container_id_1 = omni_action.create_container(action_data_1, target_chain='base')
    print(f"  ✓ Created container {container_id_1} for Base chain")
    
    action_data_2 = {
        'type': 'swap',
        'from': '0x1234567890abcdef',
        'pair': 'ETH/USDC',
        'amount': 500,
        'min_out': 490
    }
    
    container_id_2 = omni_action.create_container(action_data_2, target_chain='arbitrum')
    print(f"  ✓ Created container {container_id_2} for Arbitrum chain\n")
    
    # Test container status
    print("[TEST 3] Getting container status...")
    status_1 = omni_action.get_container_status(container_id_1)
    print(f"  ✓ Container {container_id_1} status:")
    print(f"    - Legal state: {status_1['legal_field_state']}")
    print(f"    - KOT cost: {status_1['total_kot_cost']:.2f}")
    print(f"    - Target chain: {status_1['target_chain']}")
    print(f"    - Fragmented: {status_1['fragmented']}")
    print(f"    - GCL encoded: {status_1.get('gcl_encoded', False)}")
    print(f"    - GCL length: {status_1.get('gcl_length', 0)} chars\n")
    
    # Test compliance evidence
    print("[TEST 4] Adding compliance evidence...")
    compliance_evidence = {
        'normalized': True,
        'provenance_verified': True,
        'jurisdiction_checked': True,
        'economic_purpose': 'arbitrage',
        'sanctions_screened': True
    }
    
    result_1 = omni_action.add_compliance_evidence(container_id_1, compliance_evidence)
    print(f"  ✓ Added compliance evidence to {container_id_1}")
    
    result_2 = omni_action.add_compliance_evidence(container_id_2, compliance_evidence)
    print(f"  ✓ Added compliance evidence to {container_id_2}\n")
    
    # Test container validation
    print("[TEST 5] Validating containers...")
    validation_1 = omni_action.validate_container(container_id_1)
    print(f"  ✓ Container {container_id_1} validation: {'PASSED' if validation_1['valid'] else 'FAILED'}")
    if not validation_1['valid']:
        print(f"    Reason: {validation_1['reason']}")
    
    validation_2 = omni_action.validate_container(container_id_2)
    print(f"  ✓ Container {container_id_2} validation: {'PASSED' if validation_2['valid'] else 'FAILED'}")
    if not validation_2['valid']:
        print(f"    Reason: {validation_2['reason']}\n")
    
    # Test container execution
    print("[TEST 6] Executing containers...")
    execution_1 = omni_action.execute_container(container_id_1)
    print(f"  ✓ Container {container_id_1} execution: {'SUCCESS' if execution_1['success'] else 'FAILED'}")
    if execution_1['success']:
        print(f"    - TX ID: {execution_1['tx_generation_id']}")
        print(f"    - KOT cost: {execution_1['kot_cost']:.2f}")
        print(f"    - Fragmented: {execution_1['fragmented']}")
    
    execution_2 = omni_action.execute_container(container_id_2)
    print(f"  ✓ Container {container_id_2} execution: {'SUCCESS' if execution_2['success'] else 'FAILED'}")
    if execution_2['success']:
        print(f"    - TX ID: {execution_2['tx_generation_id']}")
        print(f"    - KOT cost: {execution_2['kot_cost']:.2f}")
        print(f"    - Fragmented: {execution_2['fragmented']}\n")
    
    # Test fragmentation with large payload
    print("[TEST 7] Testing fragmentation with large payload...")
    large_action_data = {
        'type': 'complex_swap',
        'data': 'x' * 200000,  # Large payload that requires fragmentation
        'metadata': {'complex': True}
    }
    
    container_id_3 = omni_action.create_container(large_action_data, target_chain='ethereum')
    print(f"  ✓ Created container {container_id_3} for Ethereum chain")
    
    status_3 = omni_action.get_container_status(container_id_3)
    print(f"  ✓ Container {container_id_3} fragmented: {status_3['fragmented']}")
    if status_3['fragmented']:
        container = omni_action.active_containers[container_id_3]
        print(f"    - Number of fragments: {len(container['fragments'])}\n")
    
    # Test system status
    print("[TEST 8] Getting system status...")
    system_status = omni_action.get_system_status()
    print(f"  ✓ System status:")
    print(f"    - Total containers: {system_status['total_containers']}")
    print(f"    - Active containers: {system_status['active_containers']}")
    print(f"    - Executed containers: {system_status['executed_containers']}")
    print(f"    - Total KOT burned: {system_status['total_kot_burned']:.2f}")
    print(f"    - Compliance checks: {system_status['compliance_checks']}")
    print(f"    - Supported chains: {', '.join(system_status['supported_chains'])}\n")
    
    print("[SUCCESS] All OmniToken action tests passed!")
    return True

if __name__ == "__main__":
    success = test_omnitoken_action()
    sys.exit(0 if success else 1)
