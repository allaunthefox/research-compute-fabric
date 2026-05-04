#!/usr/bin/env python3
"""
Waveprobe Adapter for ENE Distributed Node

This adapter extracts signal metrics from the ENE (Endless Node Edges) distributed node system
and provides waveprobe-compatible interfaces for testing and validation.
"""

import json
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class ENEDistributedNodeAdapter:
    """Waveprobe adapter for ENE distributed node."""
    
    def __init__(self):
        """Initialize adapter."""
        self.probe_id = f"wave_{uuid.uuid4().hex[:12]}"
        self.timestamp = datetime.now().isoformat()
        
        # Gossip message types from ENE
        self.gossip_types = ["discovery", "heartbeat", "credential_sync", "replicate"]
        
    def execute_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a waveprobe probe on ENE distributed node."""
        # Extract probe parameters
        time_steps = probe_config.get("time_steps", 100)
        dt = probe_config.get("dt", 0.1)
        initial_peers = probe_config.get("initial_peers", 3)
        gossip_interval = probe_config.get("gossip_interval", 1.0)
        failure_rate = probe_config.get("failure_rate", 0.0)  # Simulated node failure rate
        consensus_threshold = probe_config.get("consensus_threshold", 0.67)
        
        # Simulate ENE distributed node operation
        history = self._simulate_ene_mesh(
            time_steps, dt, initial_peers, gossip_interval, failure_rate, consensus_threshold
        )
        
        # Extract metrics
        metrics = self._extract_metrics(history, probe_config)
        
        # Validate convergence
        convergence_status = self._validate_convergence(metrics)
        
        # Build result
        result = {
            "probe_id": self.probe_id,
            "probe_config": probe_config,
            "execution_timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "convergence_status": convergence_status,
            "history": history
        }
        
        return result
    
    def _simulate_ene_mesh(
        self, 
        time_steps: int, 
        dt: float, 
        initial_peers: int,
        gossip_interval: float,
        failure_rate: float,
        consensus_threshold: float
    ) -> Dict[str, Any]:
        """Simulate ENE distributed mesh operation."""
        
        # Initialize mesh
        t = 0.0
        nodes = self._initialize_nodes(initial_peers)
        
        # Trajectory storage
        time_trajectory = []
        peer_count_trajectory = []
        health_score_trajectory = []
        gossip_rate_trajectory = {msg_type: [] for msg_type in self.gossip_types}
        replication_success_trajectory = []
        consensus_reached_trajectory = []
        latency_trajectory = []
        
        for step in range(time_steps):
            # Simulate gossip protocol
            gossip_counts = self._simulate_gossip(nodes, t, gossip_interval)
            
            # Simulate node health monitoring
            health_scores = self._monitor_health(nodes, failure_rate)
            
            # Simulate replication
            replication_success = self._simulate_replication(nodes, failure_rate)
            
            # Simulate consensus
            consensus_reached = self._simulate_consensus(nodes, consensus_threshold)
            
            # Simulate latency
            avg_latency = self._compute_latency(nodes)
            
            # Store trajectory
            time_trajectory.append(t)
            peer_count_trajectory.append(len(nodes))
            health_score_trajectory.append(np.mean(list(health_scores.values())))
            
            for msg_type in self.gossip_types:
                gossip_rate_trajectory[msg_type].append(gossip_counts.get(msg_type, 0))
            
            replication_success_trajectory.append(replication_success)
            consensus_reached_trajectory.append(consensus_reached)
            latency_trajectory.append(avg_latency)
            
            # Evolve mesh
            nodes = self._evolve_mesh(nodes, dt, failure_rate)
            t += dt
        
        return {
            "time": time_trajectory,
            "peer_count": peer_count_trajectory,
            "health_scores": health_score_trajectory,
            "gossip_rates": gossip_rate_trajectory,
            "replication_success": replication_success_trajectory,
            "consensus_reached": consensus_reached_trajectory,
            "latency": latency_trajectory,
            "final_nodes": nodes
        }
    
    def _initialize_nodes(self, initial_peers: int) -> Dict[str, Dict[str, Any]]:
        """Initialize ENE nodes."""
        nodes = {}
        for i in range(initial_peers):
            node_id = f"ene_node_{i}"
            nodes[node_id] = {
                "node_id": node_id,
                "health_score": 1.0,
                "capabilities": ["storage", "compute", "relay"],
                "is_active": True,
                "last_seen": 0.0,
                "replication_version": "2.0.0-Cambrian-Bind"
            }
        return nodes
    
    def _simulate_gossip(self, nodes: Dict[str, Dict[str, Any]], t: float, interval: float) -> Dict[str, int]:
        """Simulate gossip protocol message exchange."""
        gossip_counts = {msg_type: 0 for msg_type in self.gossip_types}
        
        if t % interval < 0.1:  # Gossip happens at intervals
            active_nodes = [n for n in nodes.values() if n["is_active"]]
            
            for node in active_nodes:
                # Discovery messages (new node discovery)
                if np.random.rand() < 0.3:
                    gossip_counts["discovery"] += 1
                
                # Heartbeat messages (health monitoring)
                gossip_counts["heartbeat"] += 1
                
                # Credential sync (credential distribution)
                if np.random.rand() < 0.2:
                    gossip_counts["credential_sync"] += 1
                
                # Replication (ENE propagation)
                if np.random.rand() < 0.1:
                    gossip_counts["replicate"] += 1
        
        return gossip_counts
    
    def _monitor_health(self, nodes: Dict[str, Dict[str, Any]], failure_rate: float) -> Dict[str, float]:
        """Monitor node health."""
        health_scores = {}
        
        for node_id, node in nodes.items():
            if not node["is_active"]:
                health_scores[node_id] = 0.0
                continue
            
            # Health degrades randomly
            degradation = np.random.rand() * 0.05
            new_health = max(0.0, node["health_score"] - degradation)
            
            # Random failure
            if np.random.rand() < failure_rate:
                new_health = 0.0
                node["is_active"] = False
            
            node["health_score"] = new_health
            health_scores[node_id] = new_health
        
        return health_scores
    
    def _simulate_replication(self, nodes: Dict[str, Dict[str, Any]], failure_rate: float) -> bool:
        """Simulate ENE replication."""
        active_nodes = [n for n in nodes.values() if n["is_active"]]
        
        if len(active_nodes) < 2:
            return False
        
        # Replication succeeds if enough healthy nodes
        healthy_nodes = [n for n in active_nodes if n["health_score"] > 0.5]
        success_rate = len(healthy_nodes) / len(active_nodes)
        
        return success_rate > (1.0 - failure_rate)
    
    def _simulate_consensus(self, nodes: Dict[str, Dict[str, Any]], threshold: float) -> bool:
        """Simulate consensus achievement."""
        active_nodes = [n for n in nodes.values() if n["is_active"]]
        
        if len(active_nodes) == 0:
            return False
        
        # Simulate voting
        votes = sum(1 for n in active_nodes if np.random.rand() < n["health_score"])
        consensus_rate = votes / len(active_nodes)
        
        return consensus_rate >= threshold
    
    def _compute_latency(self, nodes: Dict[str, Dict[str, Any]]) -> float:
        """Compute average mesh latency."""
        active_nodes = [n for n in nodes.values() if n["is_active"]]
        
        if len(active_nodes) < 2:
            return 0.0
        
        # Simulate latency based on health
        latencies = []
        for node in active_nodes:
            base_latency = 100.0  # ms
            health_factor = 1.0 - node["health_score"]
            latency = base_latency * (1 + health_factor * 2)
            latencies.append(latency)
        
        return np.mean(latencies)
    
    def _evolve_mesh(self, nodes: Dict[str, Dict[str, Any]], dt: float, failure_rate: float) -> Dict[str, Dict[str, Any]]:
        """Evolve mesh topology."""
        # Auto-recovery for failed nodes
        for node_id, node in nodes.items():
            if not node["is_active"]:
                # Small chance of recovery
                if np.random.rand() < 0.05:
                    node["is_active"] = True
                    node["health_score"] = 0.5
        
        # New node discovery (auto-replication)
        if np.random.rand() < 0.02 and len(nodes) < 10:
            new_node_id = f"ene_node_{len(nodes)}"
            nodes[new_node_id] = {
                "node_id": new_node_id,
                "health_score": 1.0,
                "capabilities": ["storage", "compute", "relay"],
                "is_active": True,
                "last_seen": 0.0,
                "replication_version": "2.0.0-Cambrian-Bind"
            }
        
        return nodes
    
    def _extract_metrics(self, history: Dict[str, Any], probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized metrics from ENE mesh."""
        peer_count_trajectory = history["peer_count"]
        health_score_trajectory = history["health_scores"]
        gossip_rate_trajectory = history["gossip_rates"]
        replication_success_trajectory = history["replication_success"]
        consensus_reached_trajectory = history["consensus_reached"]
        latency_trajectory = history["latency"]
        
        metrics = {
            "final_peer_count": int(peer_count_trajectory[-1]),
            "max_peer_count": int(max(peer_count_trajectory)),
            "min_peer_count": int(min(peer_count_trajectory)),
            "final_health_score": float(health_score_trajectory[-1]),
            "mean_health_score": float(np.mean(health_score_trajectory)),
            "health_convergence_rate": self._compute_convergence_rate(health_score_trajectory),
            "final_gossip_rates": {
                msg_type: float(trajectory[-1])
                for msg_type, trajectory in gossip_rate_trajectory.items()
            },
            "mean_gossip_rates": {
                msg_type: float(np.mean(trajectory))
                for msg_type, trajectory in gossip_rate_trajectory.items()
            },
            "replication_success_rate": float(np.mean(replication_success_trajectory)),
            "consensus_achievement_rate": float(np.mean(consensus_reached_trajectory)),
            "final_latency": float(latency_trajectory[-1]),
            "mean_latency": float(np.mean(latency_trajectory)),
            "latency_convergence": self._compute_convergence_rate(latency_trajectory),
            "initial_peers": probe_config.get("initial_peers", 3),
            "failure_rate": probe_config.get("failure_rate", 0.0),
            "consensus_threshold": probe_config.get("consensus_threshold", 0.67),
            "total_time_steps": len(peer_count_trajectory)
        }
        return metrics
    
    def _validate_convergence(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate convergence criteria."""
        convergence_status = {
            "health_stable": metrics["health_convergence_rate"] < 0.01,
            "latency_stable": metrics["latency_convergence"] < 0.01,
            "replication_reliable": metrics["replication_success_rate"] > 0.9,
            "consensus_achievable": metrics["consensus_achievement_rate"] > 0.67,
            "mesh_stable": metrics["final_peer_count"] >= metrics["initial_peers"] * 0.8,
            "overall_status": "converged" if (
                metrics["health_convergence_rate"] < 0.01 and
                metrics["replication_success_rate"] > 0.9
            ) else "not_converged"
        }
        return convergence_status
    
    def _compute_convergence_rate(self, trajectory: List[float]) -> float:
        """Compute convergence rate from trajectory."""
        if len(trajectory) < 10:
            return 1.0
        
        tail_size = max(10, len(trajectory) // 10)
        tail = trajectory[-tail_size:]
        convergence_rate = float(np.std(tail) / (np.mean(np.abs(tail)) + 1e-10))
        return convergence_rate
    
    def serialize_results(self, result: Dict[str, Any]) -> str:
        """Serialize results in waveprobe-compatible JSON format."""
        serialized = json.dumps(result, indent=2, default=str)
        return serialized
    
    def store_to_topological(self, result: Dict[str, Any], storage_path: Optional[str] = None) -> str:
        """Store results in topological storage (placeholder for ENE integration)."""
        storage_path = storage_path or f"data/waveprobes/ene_distributed_node/{self.probe_id}.json"
        
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        serialized = self.serialize_results(result)
        Path(storage_path).write_text(serialized)
        
        return storage_path


class ENEDistributedNodeProbeGenerator:
    """Generate waveprobe test probes for ENE distributed node."""
    
    @staticmethod
    def generate_mesh_size_probes() -> List[Dict[str, Any]]:
        """Generate mesh size sweep probes."""
        probes = []
        
        # Sweep initial peer count
        for initial_peers in [3, 5, 10]:
            probes.append({
                "probe_type": "mesh_size_sweep",
                "initial_peers": initial_peers,
                "time_steps": 100,
                "dt": 0.1,
                "gossip_interval": 1.0,
                "failure_rate": 0.0,
                "consensus_threshold": 0.67,
                "description": f"Sweep initial_peers={initial_peers}"
            })
        
        return probes
    
    @staticmethod
    def generate_failure_tolerance_probes() -> List[Dict[str, Any]]:
        """Generate failure tolerance probes."""
        probes = []
        
        # Sweep failure rate
        for failure_rate in [0.0, 0.05, 0.1, 0.2]:
            probes.append({
                "probe_type": "failure_tolerance",
                "initial_peers": 5,
                "time_steps": 100,
                "dt": 0.1,
                "gossip_interval": 1.0,
                "failure_rate": failure_rate,
                "consensus_threshold": 0.67,
                "description": f"Failure tolerance: failure_rate={failure_rate}"
            })
        
        return probes
    
    @staticmethod
    def generate_consensus_threshold_probes() -> List[Dict[str, Any]]:
        """Generate consensus threshold probes."""
        probes = []
        
        # Sweep consensus threshold
        for threshold in [0.5, 0.67, 0.8, 0.9]:
            probes.append({
                "probe_type": "consensus_threshold",
                "initial_peers": 5,
                "time_steps": 100,
                "dt": 0.1,
                "gossip_interval": 1.0,
                "failure_rate": 0.0,
                "consensus_threshold": threshold,
                "description": f"Consensus threshold: {threshold}"
            })
        
        return probes


def main():
    """Main entry point for testing the adapter."""
    print("=" * 70)
    print("Waveprobe Adapter for ENE Distributed Node")
    print("=" * 70)
    
    # Initialize adapter
    adapter = ENEDistributedNodeAdapter()
    print(f"Adapter initialized: {adapter.probe_id}")
    
    # Test with a simple probe
    probe_config = {
        "probe_type": "test",
        "initial_peers": 5,
        "time_steps": 100,
        "dt": 0.1,
        "gossip_interval": 1.0,
        "failure_rate": 0.05,
        "consensus_threshold": 0.67
    }
    
    print(f"\nExecuting probe: {probe_config}")
    result = adapter.execute_probe(probe_config)
    
    print(f"\nProbe execution completed")
    print(f"Final Peer Count: {result['metrics']['final_peer_count']}")
    print(f"Max Peer Count: {result['metrics']['max_peer_count']}")
    print(f"Final Health Score: {result['metrics']['final_health_score']:.6f}")
    print(f"Replication Success Rate: {result['metrics']['replication_success_rate']:.6f}")
    print(f"Consensus Achievement Rate: {result['metrics']['consensus_achievement_rate']:.6f}")
    print(f"Final Latency: {result['metrics']['final_latency']:.2f} ms")
    print(f"Final Gossip Rates: {result['metrics']['final_gossip_rates']}")
    print(f"Convergence Status: {result['convergence_status']['overall_status']}")
    
    # Store results
    storage_path = adapter.store_to_topological(result)
    print(f"\nResults stored to: {storage_path}")
    
    # Generate probe types
    print("\n" + "=" * 70)
    print("Probe Generation Test")
    print("=" * 70)
    
    generator = ENEDistributedNodeProbeGenerator()
    
    mesh_size_probes = generator.generate_mesh_size_probes()
    print(f"Mesh size probes: {len(mesh_size_probes)}")
    
    failure_tolerance_probes = generator.generate_failure_tolerance_probes()
    print(f"Failure tolerance probes: {len(failure_tolerance_probes)}")
    
    consensus_threshold_probes = generator.generate_consensus_threshold_probes()
    print(f"Consensus threshold probes: {len(consensus_threshold_probes)}")
    
    print("\n✅ ENE distributed node waveprobe adapter test completed successfully")


if __name__ == "__main__":
    main()
