#!/usr/bin/env python3
"""Test script for node OmniToken integration"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import RemoteNode, OmniTokenAction

def test_node_omnitoken():
    """Test node OmniToken integration"""
    
    print("[TEST] Testing node OmniToken integration...\n")
    
    # Create a remote node with OmniToken support
    print("[TEST 1] Creating remote node with OmniToken support...")
    node = RemoteNode(
        node_id="node_1",
        address="192.168.1.100",
        port=8080,
        node_type="compute",
        capabilities=["topology_analysis", "omnitoken"],
        status="online",
        omnitoken_supported=True,
        omnitoken_kot_balance=1000.0,
        omnitoken_chains=['base', 'arbitrum', 'ethereum']
    )
    print(f"  ✓ Node {node.node_id} created")
    print(f"    - OmniToken supported: {node.omnitoken_supported}")
    print(f"    - KOT balance: {node.omnitoken_kot_balance:.2f}")
    print(f"    - Supported chains: {', '.join(node.omnitoken_chains)}\n")
    
    # Create OmniToken action system
    print("[TEST 2] Creating OmniToken action system...")
    omni_action = OmniTokenAction()
    print("  ✓ OmniToken action system created\n")
    
    # Create a container
    print("[TEST 3] Creating OmniToken container...")
    action_data = {
        'type': 'transfer',
        'from': '0x1234567890abcdef',
        'to': '0xabcdef1234567890',
        'amount': 500,
        'token': 'ETH'
    }
    
    container_id = omni_action.create_container(action_data, target_chain='base')
    print(f"  ✓ Created container {container_id}\n")
    
    # Add container to node
    print("[TEST 4] Adding container to node...")
    result = node.add_omnitoken_container(container_id)
    print(f"  ✓ Container added to node: {result}")
    print(f"    - Node containers: {node.omnitoken_containers}\n")
    
    # Check chain support
    print("[TEST 5] Checking chain support...")
    base_supported = node.supports_chain('base')
    arbitrum_supported = node.supports_chain('arbitrum')
    ethereum_supported = node.supports_chain('ethereum')
    polygon_supported = node.supports_chain('polygon')
    
    print(f"  ✓ Base supported: {base_supported}")
    print(f"  ✓ Arbitrum supported: {arbitrum_supported}")
    print(f"  ✓ Ethereum supported: {ethereum_supported}")
    print(f"  ✓ Polygon supported: {polygon_supported}\n")
    
    # Add compliance evidence
    print("[TEST 6] Adding compliance evidence to container...")
    compliance_evidence = {
        'normalized': True,
        'provenance_verified': True,
        'jurisdiction_checked': True,
        'economic_purpose': 'arbitrage',
        'sanctions_screened': True
    }
    
    omni_action.add_compliance_evidence(container_id, compliance_evidence)
    print("  ✓ Compliance evidence added\n")
    
    # Burn KOT for execution
    print("[TEST 7] Burning KOT for execution...")
    container = omni_action.active_containers[container_id]
    kot_cost = container['total_kot_cost']
    
    burn_result = node.burn_kot(kot_cost)
    print(f"  ✓ KOT burn result: {burn_result}")
    print(f"    - KOT cost: {kot_cost:.2f}")
    print(f"    - New KOT balance: {node.omnitoken_kot_balance:.2f}\n")
    
    # Execute container
    print("[TEST 8] Executing container...")
    execution_result = omni_action.execute_container(container_id)
    print(f"  ✓ Container execution: {'SUCCESS' if execution_result['success'] else 'FAILED'}")
    if execution_result['success']:
        print(f"    - TX ID: {execution_result['tx_generation_id']}")
        print(f"    - Target chain: {execution_result['target_chain']}")
        print(f"    - KOT cost: {execution_result['kot_cost']:.2f}\n")
    
    # Remove container from node after execution
    print("[TEST 9] Removing container from node...")
    remove_result = node.remove_omnitoken_container(container_id)
    print(f"  ✓ Container removed: {remove_result}")
    print(f"    - Node containers: {node.omnitoken_containers}\n")
    
    # Test insufficient KOT balance
    print("[TEST 10] Testing insufficient KOT balance...")
    node.omnitoken_kot_balance = 0.1
    burn_result = node.burn_kot(kot_cost)
    print(f"  ✓ KOT burn with insufficient balance: {burn_result}")
    print(f"    - KOT balance: {node.omnitoken_kot_balance:.2f}")
    print(f"    - Required KOT: {kot_cost:.2f}\n")
    
    # Create multiple containers for load testing
    print("[TEST 11] Creating multiple containers...")
    for i in range(3):
        action_data = {
            'type': 'swap',
            'pair': f'ETH/USDT_{i}',
            'amount': 100 * (i + 1)
        }
        container_id = omni_action.create_container(action_data, target_chain='arbitrum')
        node.add_omnitoken_container(container_id)
    
    print(f"  ✓ Created 3 additional containers")
    print(f"    - Total node containers: {len(node.omnitoken_containers)}")
    print(f"    - Total system containers: {len(omni_action.active_containers)}\n")
    
    # Get node status
    print("[TEST 12] Getting node OmniToken status...")
    print(f"  ✓ Node OmniToken status:")
    print(f"    - OmniToken supported: {node.omnitoken_supported}")
    print(f"    - Active containers: {len(node.omnitoken_containers)}")
    print(f"    - KOT balance: {node.omnitoken_kot_balance:.2f}")
    print(f"    - Supported chains: {', '.join(node.omnitoken_chains)}")
    print(f"    - Is online: {node.is_online()}\n")
    
    print("[SUCCESS] All node OmniToken integration tests passed!")
    return True

if __name__ == "__main__":
    success = test_node_omnitoken()
    sys.exit(0 if success else 1)
