#!/usr/bin/env python3
"""
Execute Fundamental Topology Reinvention Using Real Swarm System

This script uses the enhanced integrated swarm system to execute the fundamental
topology reinvention query with actual time allocation (up to 1 hour).
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_integrated_swarm import (
    EnhancedIntegratedSwarm,
    create_demo_topology,
    MathDatabase
)

def load_swarm_request(request_path):
    """Load the swarm request from file."""
    with open(request_path, 'r') as f:
        return json.load(f)

def execute_fundamental_reinvention():
    """Execute fundamental topology reinvention using real swarm system."""
    print("=" * 70)
    print("Executing Fundamental Topology Reinvention Using Real Swarm System")
    print("=" * 70)
    
    # Load the swarm request
    request_path = "shared-data/data/swarm_requests/swarm_fundamental_reinvention.json"
    print(f"\nLoading request from: {request_path}")
    request = load_swarm_request(request_path)
    
    print(f"Request ID: {request['request_id']}")
    print(f"Time Allocation: {request['time_allocation']}")
    print(f"Priority: {request['priority']}")
    
    # Create demo topology
    print("\nCreating topology...")
    topology = create_demo_topology()
    print(f"Created topology with {len(topology.nodes)} nodes, {len(topology.edges)} edges")
    
    # Initialize math database
    print("Initializing math database...")
    math_db = MathDatabase()
    
    # Create enhanced integrated swarm with many agents for deep reasoning
    print("\nInitializing enhanced integrated swarm...")
    num_agents = 200  # Use 200 agents for deep reasoning
    swarm = EnhancedIntegratedSwarm(topology, math_db, num_agents=num_agents)
    print(f"Swarm initialized with {num_agents} agents")
    
    # Base geometric parameters for topology analysis
    base_params = {
        'kappa_squared': 0.5,
        'rho_seq': 0.5,
        'v_epigenetic': 0.5,
        'tau_structure': 0.5,
        'sigma_entropy': 0.5,
        'q_conservation': 0.5,
        'kappa_hierarchy': 0.5,
        'epsilon_mutation': 0.5
    }
    
    # Execute swarm analysis for topology
    print("\nExecuting swarm analysis for fundamental topology reinvention...")
    print(f"Subject: {request['context']['scope']}")
    print(f"Objective: {request['context']['objective']}")
    print(f"Time allocation: {request['time_allocation']}")
    
    start_time = time.time()
    
    # Run swarm analysis
    result = swarm.run_swarm_analysis(base_params, subject="topology")
    
    elapsed_time = time.time() - start_time
    
    print(f"\nSwarm analysis completed in {elapsed_time:.2f} seconds")
    
    # Output results
    print("\n" + "=" * 70)
    print("Swarm Analysis Results")
    print("=" * 70)
    print(f"Consensus: {result.consensus:.3f}")
    print(f"Topology Optimization Score: {result.topology_optimization_score:.3f}")
    print(f"Math Coverage Score: {result.math_coverage_score:.3f}")
    print(f"Lean Coverage Score: {result.lean_coverage_score:.3f}")
    print(f"Agents: {len(result.agents)}")
    print(f"Recommendations: {len(result.recommendations)}")
    
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(result.recommendations[:10], 1):
        print(f"  {i}. {rec}")
    
    # Save results
    output_path = f"shared-data/data/swarm_responses/swarm_response_fundamental_reinvention_real_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_data = {
        "response_id": f"swarm_response_real_{request['request_id'].replace('swarm_', '')}",
        "timestamp": datetime.now().isoformat(),
        "request_id": request['request_id'],
        "elapsed_time_seconds": elapsed_time,
        "consensus": result.consensus,
        "topology_optimization_score": result.topology_optimization_score,
        "math_coverage_score": result.math_coverage_score,
        "lean_coverage_score": result.lean_coverage_score,
        "agent_count": len(result.agents),
        "recommendations": result.recommendations,
        "nii_core_status": [
            {
                "core_id": status.core_id,
                "status": status.status,
                "geometric_score": status.geometric_score
            }
            for status in result.nii_core_status
        ]
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print("=" * 70)
    
    return result_data

if __name__ == "__main__":
    try:
        result = execute_fundamental_reinvention()
        print("\n✅ Fundamental topology reinvention executed successfully using real swarm system")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
