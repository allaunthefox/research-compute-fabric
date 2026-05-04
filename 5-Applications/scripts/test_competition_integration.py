#!/usr/bin/env python3
"""
Test competition system integration with distributed swarm.
"""

import sys
import os
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from distributed_swarm_colonization import DistributedSwarmColonizer, SwarmNodeConfig
from swarm_competition import SwarmCompetitionSystem, MetricType
import time

def main():
    print("[Test] Competition System Integration")
    
    # Create swarm node config (use hex node_id for DHT)
    config = SwarmNodeConfig(
        node_id="0x1234567890abcdef",
        transport_type="omnitoken",
        address="127.0.0.1",
        port=8080,
        jupiter_box_index=0,
        bandwidth_mbps=1000,
        latency_ms=10
    )
    
    # Initialize colonizer
    colonizer = DistributedSwarmColonizer(config)
    
    print("\n[Test 1] Check competition system initialization...")
    if colonizer.competition_system:
        print("  ✓ Competition system initialized")
    else:
        print("  ✗ Competition system not available")
        return
    
    print("\n[Test 2] Submit improvements to competition...")
    agent_id = 12345
    
    # Submit efficiency improvement
    result = colonizer.competition_system.submitImprovement(
        agentId=agent_id,
        metricType=MetricType.EFFICIENCY_GAIN,
        value=60.0,
        baseline=50.0,
        proof="test_proof_1"
    )
    
    if result.get('success'):
        print(f"  ✓ Efficiency improvement: Score {result['totalScore']:.3f}, Position {result['leaderboardPosition']}")
    else:
        print(f"  ✗ Failed: {result.get('error')}")
    
    # Submit performance improvement
    result = colonizer.competition_system.submitImprovement(
        agentId=agent_id,
        metricType=MetricType.PERFORMANCE_GAIN,
        value=70.0,
        baseline=50.0,
        proof="test_proof_2"
    )
    
    if result.get('success'):
        print(f"  ✓ Performance improvement: Score {result['totalScore']:.3f}")
    else:
        print(f"  ✗ Failed: {result.get('error')}")
    
    print("\n[Test 3] Get leaderboard...")
    leaderboard = colonizer.competition_system.getLeaderboard()
    print(f"  Current leader: {leaderboard['currentLeader']}")
    print(f"  Entries: {len(leaderboard['entries'])}")
    
    print("\n[Test 4] Check colonization status with competition...")
    status = colonizer.get_colonization_status()
    if 'competition_state' in status:
        print("  ✓ Competition state in colonization status")
        comp = status['competition_state']
        print(f"    Leader: {comp['currentLeader']}")
        print(f"    Generation: {comp['currentGeneration']}")
    else:
        print("  ✗ Competition state not in colonization status")
    
    print("\n[Test 5] Print status...")
    colonizer.print_status()
    
    print("\n[Test Complete]")

if __name__ == '__main__':
    main()
