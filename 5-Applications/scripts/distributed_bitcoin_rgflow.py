#!/usr/bin/env python3
"""
Distributed Bitcoin RGFlow Analysis on Swarm

Assigns Bitcoin RGFlow analysis tasks to swarm nodes using Lean bindserver.
Per AGENTS.md: Uses swarm action metrics (cycles, operations) not human time units.
"""
import sys
import os
import json
import logging
import time
from typing import Dict, Any, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infra.lean_unified_shim import LeanUnifiedShim
from scripts.distributed_swarm_colonization import SwarmColonization

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BitcoinRGFlowSwarm")

class DistributedBitcoinRGFlow:
    def __init__(self):
        self.shim = LeanUnifiedShim()
        self.colonizer = SwarmColonization()
        
    def get_swarm_topology(self) -> List[Dict[str, Any]]:
        """Get current swarm topology from colonization."""
        logger.info("Discovering swarm topology...")
        topology = self.colonizer.discover_nodes()
        if not topology:
            logger.error("No swarm topology available")
            return []
        logger.info(f"Swarm topology: {len(topology)} nodes")
        return topology
    
    def assign_analysis_to_node(self, node: Dict[str, Any], prices: List[float], 
                                 window: int = 30, node_id: int = 0) -> Dict[str, Any]:
        """
        Assign Bitcoin RGFlow analysis task to a specific node.
        Returns result with swarm action metrics.
        """
        hostname = node.get('hostname', 'unknown')
        ip = node.get('tailscaleIP', 'unknown')
        role = node.get('role', 'worker')
        
        logger.info(f"Assigning Bitcoin RGFlow analysis to node {node_id}: {hostname} ({ip}) - ROLE: {role}")
        
        # Track start time for action metrics
        start_cycles = time.time_ns()
        
        try:
            # Execute Bitcoin RGFlow analysis via Lean bindserver
            result = self.shim.bitcoin_rgflow_analysis(prices, window)
            
            # Calculate swarm action metrics
            end_cycles = time.time_ns()
            action_cycles = end_cycles - start_cycles
            action_operations = len(prices) * window  # Approximate operation count
            
            if "error" in result:
                logger.error(f"Analysis failed on {hostname}: {result['error']}")
                return {
                    "node_id": node_id,
                    "hostname": hostname,
                    "role": role,
                    "status": "failed",
                    "error": result['error'],
                    "action_cycles": action_cycles,
                    "action_operations": action_operations
                }
            
            logger.info(f"Analysis completed on {hostname} - {action_cycles:,} cycles, {action_operations:,} operations")
            
            return {
                "node_id": node_id,
                "hostname": hostname,
                "role": role,
                "status": "success",
                "result": result,
                "action_cycles": action_cycles,
                "action_operations": action_operations
            }
            
        except Exception as e:
            logger.error(f"Exception on {hostname}: {e}")
            end_cycles = time.time_ns()
            action_cycles = end_cycles - start_cycles
            return {
                "node_id": node_id,
                "hostname": hostname,
                "role": role,
                "status": "error",
                "error": str(e),
                "action_cycles": action_cycles,
                "action_operations": 0
            }
    
    def distribute_analysis(self, prices: List[float], window: int = 30) -> Dict[str, Any]:
        """
        Distribute Bitcoin RGFlow analysis across swarm nodes.
        Uses coordinator nodes for orchestration, worker nodes for computation.
        """
        logger.info(f"Starting distributed Bitcoin RGFlow analysis with {len(prices)} price points, window={window}")
        
        # Get swarm topology
        topology = self.get_swarm_topology()
        if not topology:
            return {"error": "No swarm topology available"}
        
        # Separate coordinators and workers
        coordinators = [n for n in topology if n.get('role') == 'coordinator' and n.get('status') == 'active']
        workers = [n for n in topology if n.get('role') == 'worker' and n.get('status') == 'active']
        architect = [n for n in topology if n.get('role') == 'architect' and n.get('status') == 'active']
        
        logger.info(f"Active nodes: {len(coordinators)} coordinators, {len(workers)} workers, {len(architect)} architect")
        
        # If no active nodes, use all nodes
        active_nodes = [n for n in topology if n.get('status') == 'active']
        if not active_nodes:
            logger.warning("No active nodes, using all nodes")
            active_nodes = topology
        
        # Assign analysis to active nodes (simple round-robin)
        results = []
        total_cycles = 0
        total_operations = 0
        
        for i, node in enumerate(active_nodes):
            result = self.assign_analysis_to_node(node, prices, window, i)
            results.append(result)
            total_cycles += result.get('action_cycles', 0)
            total_operations += result.get('action_operations', 0)
        
        # Calculate aggregate metrics
        successful_nodes = [r for r in results if r.get('status') == 'success']
        failed_nodes = [r for r in results if r.get('status') in ['failed', 'error']]
        
        logger.info(f"Analysis complete: {len(successful_nodes)} successful, {len(failed_nodes)} failed")
        logger.info(f"Total swarm action cycles: {total_cycles:,}")
        logger.info(f"Total swarm action operations: {total_operations:,}")
        
        return {
            "status": "complete",
            "total_nodes": len(active_nodes),
            "successful_nodes": len(successful_nodes),
            "failed_nodes": len(failed_nodes),
            "total_action_cycles": total_cycles,
            "total_action_operations": total_operations,
            "results": results
        }
    
    def format_time_human_readable(self, seconds: float) -> str:
        """Convert seconds to human-readable time format."""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes} minutes {secs} seconds"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours} hours {minutes} minutes"
    
    def print_results(self, analysis_result: Dict[str, Any]):
        """Print formatted analysis results with human-readable time."""
        if "error" in analysis_result:
            print(f"ERROR: {analysis_result['error']}")
            return
        
        print("\n" + "=" * 70)
        print("DISTRIBUTED BITCOIN RGFLOW ANALYSIS - SWARM RESULTS")
        print("=" * 70)
        
        print(f"\nTotal Nodes: {analysis_result['total_nodes']}")
        print(f"Successful: {analysis_result['successful_nodes']}")
        print(f"Failed: {analysis_result['failed_nodes']}")
        
        # Convert cycles to human-readable time (assuming 1 cycle ≈ 1 nanosecond)
        total_cycles = analysis_result['total_action_cycles']
        total_seconds = total_cycles / 1_000_000_000
        human_time = self.format_time_human_readable(total_seconds)
        
        print(f"\nTotal Swarm Action Cycles: {total_cycles:,}")
        print(f"Estimated Duration: {human_time}")
        print(f"Total Swarm Action Operations: {analysis_result['total_action_operations']:,}")
        
        print("\n" + "-" * 70)
        print("PER-NODE RESULTS")
        print("-" * 70)
        
        for result in analysis_result['results']:
            hostname = result['hostname']
            role = result['role']
            status = result['status']
            cycles = result['action_cycles']
            operations = result['action_operations']
            
            # Convert node cycles to human-readable time
            node_seconds = cycles / 1_000_000_000
            node_time = self.format_time_human_readable(node_seconds)
            
            print(f"\n  {hostname} ({role}):")
            print(f"    Status: {status}")
            print(f"    Action Cycles: {cycles:,} ({node_time})")
            print(f"    Action Operations: {operations:,}")
            
            if status == 'success' and 'result' in result:
                print(f"    Analysis: {json.dumps(result['result'], indent=6)}")
            elif status in ['failed', 'error']:
                print(f"    Error: {result.get('error', 'Unknown')}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    # Example Bitcoin price data (Q16.16 format)
    # In production, this would come from a real Bitcoin price API
    example_prices = [
        65536,   # 1.0 in Q16.16
        98304,   # 1.5 in Q16.16
        131072,  # 2.0 in Q16.16
        163840,  # 2.5 in Q16.16
        196608,  # 3.0 in Q16.16
        229376,  # 3.5 in Q16.16
        262144,  # 4.0 in Q16.16
        294912,  # 4.5 in Q16.16
        327680,  # 5.0 in Q16.16
        360448   # 5.5 in Q16.16
    ]
    
    analyzer = DistributedBitcoinRGFlow()
    result = analyzer.distribute_analysis(example_prices, window=2)
    analyzer.print_results(result)
