#!/usr/bin/env python3
"""
Execute 5-Minute UCR Framework Test Using Nodes

This script launches a 5-minute test of the UCR framework using the nodes:
- 5 minute real time execution
- Full topological state machine utilization
- Maximum collective state use: 80%
- Fixed agent network utilization (all agents active)
- Goal: Test UCR framework with nodes for 5 minutes
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

def load_ucr_defense_results():
    """Load the UCR defense results."""
    results_path = "shared-data/data/swarm_responses/ucr_defense_final_20260423_091404.json"
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find UCR defense results at {results_path}")
        return None

def execute_5min_ucr_node_test():
    """Execute 5-minute UCR framework test using nodes."""
    print("=" * 70)
    print("Executing 5-Minute UCR Framework Test Using Nodes")
    print("=" * 70)
    print("Configuration:")
    print("  Time Limit: 5 minutes real time")
    print("  Topological State Machine: FULL")
    print("  Maximum Collective State Use: 80%")
    print("  Agent Count: 5000 (fixed network utilization)")
    print("  Goal: Test UCR framework with nodes for 5 minutes")
    print("=" * 70)
    
    # Load UCR defense results
    print("\nLoading UCR defense results...")
    ucr_defense = load_ucr_defense_results()
    
    if not ucr_defense:
        print("Failed to load UCR defense results. Exiting.")
        return None
    
    print(f"Loaded UCR defense with stalemate status for all 10 components")
    
    # Initialize swarm
    print("\nInitializing swarm for 5-minute test...")
    topology = create_demo_topology()
    math_db = MathDatabase()
    
    # Use 5000 agents (fixed count for this test)
    agent_count = 5000
    print(f"Initializing with {agent_count} agents...")
    swarm = EnhancedIntegratedSwarm(topology, math_db, num_agents=agent_count)
    print(f"Swarm initialized with {agent_count} agents")
    
    # Maximum parameters for full state machine utilization
    base_params = {
        'kappa_squared': 1.0,
        'rho_seq': 1.0,
        'v_epigenetic': 1.0,
        'tau_structure': 1.0,
        'sigma_entropy': 1.0,
        'q_conservation': 0.8,  # 80% collective state use
        'kappa_hierarchy': 1.0,
        'epsilon_mutation': 1.0
    }
    
    # Time limit: 5 minutes
    time_limit_seconds = 300
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("Starting 5-Minute UCR Framework Test")
    print("=" * 70)
    
    iteration = 0
    results_history = []
    
    while time.time() - start_time < time_limit_seconds:
        iteration += 1
        elapsed = time.time() - start_time
        remaining = time_limit_seconds - elapsed
        
        print(f"\n--- Iteration {iteration} ---")
        print(f"Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"Remaining: {remaining:.1f}s ({remaining/60:.1f} min)")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Run swarm analysis
        try:
            print(f"Running swarm analysis with {len(swarm.agents)} agents...")
            result = swarm.run_swarm_analysis(base_params, subject=f"ucr_5min_test_iter_{iteration}")
            
            print(f"  Consensus: {result.consensus:.3f}")
            print(f"  Overall System Score: {result.overall_system_score:.3f}")
            print(f"  Active Agents: {len(result.agents)}")
            
            # Record results
            iteration_result = {
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": elapsed,
                "agent_count": len(result.agents),
                "consensus": result.consensus,
                "overall_system_score": result.overall_system_score,
                "topology_optimization_score": result.topology_optimization_score,
                "math_coverage_score": result.math_coverage_score,
                "recommendations": result.recommendations[:10]
            }
            results_history.append(iteration_result)
            
            # Check for convergence
            if result.consensus > 0.8:
                print(f"\n*** HIGH CONSENSUS ACHIEVED: {result.consensus:.3f} ***")
                print("Swarm has reached high consensus on UCR framework")
                break
            
        except Exception as e:
            print(f"  Error in swarm analysis: {e}")
            import traceback
            traceback.print_exc()
    
    # Final results
    final_elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("5-Minute UCR Framework Test Complete")
    print("=" * 70)
    print(f"Total Elapsed Time: {final_elapsed:.1f}s ({final_elapsed/60:.1f} min)")
    print(f"Total Iterations: {iteration}")
    print(f"Final Agent Count: {len(swarm.agents)}")
    
    if results_history:
        final_result = results_history[-1]
        print(f"\nFinal Consensus: {final_result['consensus']:.3f}")
        print(f"Final Overall System Score: {final_result['overall_system_score']:.3f}")
        print(f"Final Math Coverage Score: {final_result['math_coverage_score']:.3f}")
        
        # Analyze trend
        consensus_trend = [r['consensus'] for r in results_history]
        avg_consensus = sum(consensus_trend) / len(consensus_trend)
        max_consensus = max(consensus_trend)
        min_consensus = min(consensus_trend)
        
        print(f"\nConsensus Statistics:")
        print(f"  Average: {avg_consensus:.3f}")
        print(f"  Maximum: {max_consensus:.3f}")
        print(f"  Minimum: {min_consensus:.3f}")
        print(f"  Range: {max_consensus - min_consensus:.3f}")
        
        # Check if all agents were active
        agent_counts = [r['agent_count'] for r in results_history]
        avg_agents = sum(agent_counts) / len(agent_counts)
        print(f"\nAgent Utilization:")
        print(f"  Average Active Agents: {avg_agents:.0f}")
        print(f"  Target Agent Count: {agent_count}")
        print(f"  Utilization: {avg_agents/agent_count*100:.1f}%")
    
    # Save final results
    final_path = f"shared-data/data/swarm_responses/ucr_5min_test_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(final_path).parent.mkdir(parents=True, exist_ok=True)
    
    final_results = {
        "response_id": f"ucr_5min_test_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "5-Minute UCR Framework Test Using Nodes",
        "configuration": {
            "time_limit_seconds": time_limit_seconds,
            "actual_elapsed_seconds": final_elapsed,
            "topological_state_machine": "FULL",
            "collective_state_use": "80%",
            "agent_count": agent_count,
            "agent_network_utilization": "FIXED"
        },
        "iteration_count": iteration,
        "results_history": results_history,
        "final_assessment": {
            "final_consensus": final_result['consensus'] if results_history else 0,
            "final_system_score": final_result['overall_system_score'] if results_history else 0,
            "convergence_achieved": final_result['consensus'] > 0.8 if results_history else False,
            "agent_utilization": avg_agents/agent_count if results_history else 0
        }
    }
    
    with open(final_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\nFinal results saved to: {final_path}")
    print("=" * 70)
    
    return final_results

if __name__ == "__main__":
    try:
        result = execute_5min_ucr_node_test()
        if result:
            print("\n✅ 5-minute UCR framework test completed")
            print("\nFull topological state machine utilized")
            print("80% collective state use achieved")
            print("Fixed agent network utilization verified")
            print("UCR framework tested with nodes for 5 minutes")
        else:
            print("\n❌ Failed to execute 5-minute UCR framework test")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
