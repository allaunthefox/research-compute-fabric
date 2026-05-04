#!/usr/bin/env python3
"""
Execute Fundamental Topology Reinvention Using Combined Swarm System

This script combines:
1. Swarm API (http://127.0.0.1:8000) - for querying existing math entities
2. Enhanced Integrated Swarm (200 agents) - for deep analysis and novel concept generation

The combined system can both query existing knowledge and generate novel frameworks.
"""

import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_integrated_swarm import (
    EnhancedIntegratedSwarm,
    create_demo_topology,
    MathDatabase
)

SWARM_API_URL = "http://127.0.0.1:8000"

def load_swarm_request(request_path):
    """Load the swarm request from file."""
    with open(request_path, 'r') as f:
        return json.load(f)

def query_swarm_api(subjects, keywords, limit=100):
    """Query the swarm API for existing math entities."""
    try:
        response = requests.post(
            f"{SWARM_API_URL}/query",
            json={
                "subjects": subjects,
                "keywords": keywords,
                "formalStatus": "unknown",
                "requireLeanFormalization": False,
                "limit": limit,
                "includeMetadata": True
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying swarm API: {e}")
        return None

def execute_fundamental_reinvention_combined():
    """Execute fundamental topology reinvention using combined swarm system."""
    print("=" * 70)
    print("Executing Fundamental Topology Reinvention Using Combined Swarm System")
    print("=" * 70)
    
    # Load the swarm request
    request_path = "shared-data/data/swarm_requests/swarm_fundamental_reinvention.json"
    print(f"\nLoading request from: {request_path}")
    request = load_swarm_request(request_path)
    
    print(f"Request ID: {request['request_id']}")
    print(f"Time Allocation: {request['time_allocation']}")
    print(f"Priority: {request['priority']}")
    
    # Step 1: Query swarm API for relevant existing math entities
    print("\n" + "=" * 70)
    print("Step 1: Querying Swarm API for Existing Math Entities")
    print("=" * 70)
    
    subjects = ["topology", "mathematics", "foundations", "geometry"]
    keywords = "topology mathematics foundations geometry"
    
    print(f"Subjects: {subjects}")
    print(f"Keywords: {keywords}")
    
    api_result = query_swarm_api(subjects, keywords, limit=50)
    
    if api_result:
        print(f"\nSwarm API Results:")
        print(f"  Success: {api_result.get('success', False)}")
        print(f"  Count: {api_result.get('count', 0)}")
        print(f"  Confidence: {api_result.get('confidence', 0)}")
        
        if api_result.get('results'):
            print(f"\n  Top 5 Results:")
            for i, entity in enumerate(api_result['results'][:5], 1):
                print(f"    {i}. {entity.get('name', 'Unknown')}")
                print(f"       Subject: {entity.get('subject', 'Unknown')}")
                print(f"       Statement: {entity.get('statement', 'No statement')[:80]}...")
    else:
        print("Failed to query swarm API, proceeding with enhanced swarm only")
    
    # Step 2: Initialize enhanced integrated swarm
    print("\n" + "=" * 70)
    print("Step 2: Initializing Enhanced Integrated Swarm")
    print("=" * 70)
    
    # Create demo topology
    print("Creating topology...")
    topology = create_demo_topology()
    print(f"Created topology with {len(topology.nodes)} nodes, {len(topology.edges)} edges")
    
    # Initialize math database
    print("Initializing math database...")
    math_db = MathDatabase()
    
    # Create enhanced integrated swarm with many agents for deep reasoning
    print(f"Initializing enhanced integrated swarm with 200 agents...")
    swarm = EnhancedIntegratedSwarm(topology, math_db, num_agents=200)
    print(f"Swarm initialized with 200 agents")
    
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
    
    # Step 3: Execute swarm analysis for topology
    print("\n" + "=" * 70)
    print("Step 3: Executing Swarm Analysis for Fundamental Topology Reinvention")
    print("=" * 70)
    print(f"Subject: {request['context']['scope']}")
    print(f"Objective: {request['context']['objective']}")
    print(f"Time allocation: {request['time_allocation']}")
    
    start_time = time.time()
    
    try:
        # Run swarm analysis
        result = swarm.run_swarm_analysis(base_params, subject="topology")
        
        elapsed_time = time.time() - start_time
        
        print(f"\nSwarm analysis completed in {elapsed_time:.2f} seconds")
        
        # Step 4: Combine results from both systems
        print("\n" + "=" * 70)
        print("Step 4: Combining Results from Both Swarm Systems")
        print("=" * 70)
        
        combined_results = {
            "response_id": f"swarm_response_combined_{request['request_id'].replace('swarm_', '')}",
            "timestamp": datetime.now().isoformat(),
            "request_id": request['request_id'],
            "elapsed_time_seconds": elapsed_time,
            "time_allocation": request['time_allocation'],
            
            # Swarm API results
            "swarm_api_results": api_result if api_result else None,
            
            # Enhanced swarm results
            "enhanced_swarm_results": {
                "consensus": result.consensus,
                "topology_optimization_score": result.topology_optimization_score,
                "math_coverage_score": result.math_coverage_score,
                "lean_coverage_score": result.lean_coverage_score,
                "gpu_computing_score": result.gpu_computing_score,
                "ssd_storage_score": result.ssd_storage_score,
                "genetic_compression_score": result.genetic_compression_score,
                "homeostasis_score": result.homeostasis_score,
                "patterns_learned": result.patterns_learned,
                "metatyping_score": result.metatyping_score,
                "remote_nodes_count": result.remote_nodes_count,
                "dag_events_count": result.dag_events_count,
                "optimization_ratio": result.optimization_ratio,
                "substrate_potential": result.substrate_potential,
                "optimization_cycles": result.optimization_cycles,
                "overall_system_score": result.overall_system_score,
                "agent_count": len(result.agents),
                "nii_core_count": len(result.nii_cores),
                "recommendation_count": len(result.recommendations)
            },
            
            # Combined analysis
            "combined_analysis": {
                "total_entities_considered": api_result.get('count', 0) if api_result else 0,
                "swarm_consensus": result.consensus,
                "enhanced_swarm_recommendations": result.recommendations[:20],
                "swarm_api_suggestions": api_result.get('suggestions', []) if api_result else []
            }
        }
        
        # Output combined results
        print(f"\nCombined Analysis Results:")
        print(f"  Total Entities Considered: {combined_results['combined_analysis']['total_entities_considered']}")
        print(f"  Swarm Consensus: {combined_results['enhanced_swarm_results']['consensus']:.3f}")
        print(f"  Topology Optimization Score: {combined_results['enhanced_swarm_results']['topology_optimization_score']:.3f}")
        print(f"  Math Coverage Score: {combined_results['enhanced_swarm_results']['math_coverage_score']:.3f}")
        print(f"  Overall System Score: {combined_results['enhanced_swarm_results']['overall_system_score']:.3f}")
        
        print(f"\nEnhanced Swarm Recommendations:")
        for i, rec in enumerate(result.recommendations[:10], 1):
            print(f"  {i}. {rec}")
        
        if api_result and api_result.get('suggestions'):
            print(f"\nSwarm API Suggestions:")
            for suggestion in api_result['suggestions']:
                print(f"  - {suggestion}")
        
        # Save combined results
        output_path = f"shared-data/data/swarm_responses/swarm_response_fundamental_reinvention_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(combined_results, f, indent=2)
        
        print(f"\nCombined results saved to: {output_path}")
        print("=" * 70)
        
        return combined_results
        
    except Exception as e:
        print(f"\n❌ Error during swarm analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = execute_fundamental_reinvention_combined()
        if result:
            print("\n✅ Fundamental topology reinvention executed successfully using combined swarm system")
        else:
            print("\n❌ Failed to execute fundamental topology reinvention using combined swarm system")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
