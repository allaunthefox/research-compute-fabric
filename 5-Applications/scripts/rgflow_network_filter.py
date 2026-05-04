#!/usr/bin/env python3
"""
RGFlow Network Filter
Apply RGFlow analysis to network/graph structure.

Analyzes the structural integrity of network connections
under Renormalization Group Flow scale transformation.
"""

import json
import sys
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict, deque


class NetworkRGFlowAnalyzer:
    """Apply RGFlow to network graph structure."""
    
    def __init__(self):
        # RGFlow parameters for network analysis
        self.D = 0.12  # Diffusion coefficient for network structure
        self.B = 0.015  # Drift barrier for connectivity
        self.lam = 0.18  # Selection strength for edge weights
        self.SCALE_STEPS = 5  # Number of RG scale transformations
        
        # Network lawfulness thresholds
        self.entropy_lower = 1.5
        self.entropy_upper = 5.0
        self.density_lower = 0.01  # Minimum connectivity
        self.density_upper = 0.30  # Maximum connectivity (avoid over-connected)
        self.component_lower = 1  # Should be connected
        self.clustering_lower = 0.05  # Minimum local structure
        
    def extract_network_from_codebase(self) -> Dict[str, Any]:
        """Extract network structure from codebase imports and dependencies."""
        print("Extracting network structure from codebase...")
        
        # Build import dependency graph
        nodes = set()
        edges = []
        
        # Scan Python files for imports
        python_files = []
        for root, dirs, files in os.walk("."):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.lake', 'node_modules', 'venv', 'env', 'hutter_venv']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        print(f"Found {len(python_files)} Python files")
        
        # Extract imports
        for filepath in python_files:
            rel_path = filepath.replace('./', '').replace('.py', '').replace('/', '.')
            nodes.add(rel_path)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Simple import detection
                    import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
                    
                    for imp_line in import_lines:
                        imp_line = imp_line.strip()
                        
                        # Parse import statement
                        if imp_line.startswith('import '):
                            module = imp_line.replace('import ', '').split(' as ')[0].split(',')[0].strip()
                        elif imp_line.startswith('from '):
                            parts = imp_line.replace('from ', '').split(' import ')
                            module = parts[0].strip()
                        
                        # Normalize module name
                        if module and not module.startswith('.'):
                            # Check if it's a local import
                            if any(module.startswith(p) for p in ['infra', 'scripts', 'tools', 'core', 'drivers']):
                                nodes.add(module)
                                edges.append({
                                    'source': rel_path,
                                    'target': module,
                                    'edgeType': 'import',
                                    'weight': 1.0
                                })
            except Exception as e:
                continue
        
        # Convert nodes to list
        node_list = [{'id': n, 'nodeType': 'module'} for n in nodes]
        
        network = {
            'nodes': node_list,
            'edges': edges,
            'metadata': {
                'total_files': len(python_files),
                'extracted_nodes': len(nodes),
                'extracted_edges': len(edges)
            }
        }
        
        print(f"Extracted network: {len(nodes)} nodes, {len(edges)} edges")
        return network
    
    def calculate_network_features(self, network: Dict[str, Any]) -> Dict[str, float]:
        """Calculate network/graph features for RGFlow."""
        nodes = network.get("nodes", [])
        edges = network.get("edges", [])
        
        n_nodes = len(nodes)
        n_edges = len(edges)
        
        if n_nodes == 0:
            return self._empty_features()
        
        # Build adjacency matrix
        node_id_to_idx = {node["id"]: i for i, node in enumerate(nodes)}
        adj = np.zeros((n_nodes, n_nodes))
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            weight = edge.get("weight", 1.0)
            
            if source in node_id_to_idx and target in node_id_to_idx:
                i = node_id_to_idx[source]
                j = node_id_to_idx[target]
                adj[i, j] = weight
                adj[j, i] = weight  # Undirected for analysis
        
        # Calculate network features
        features = {}
        
        # 1. Node degree statistics
        degrees = np.sum(adj, axis=1)
        features["mean_degree"] = float(np.mean(degrees)) if n_nodes > 0 else 0.0
        features["std_degree"] = float(np.std(degrees)) if n_nodes > 0 else 0.0
        features["max_degree"] = float(np.max(degrees)) if n_nodes > 0 else 0.0
        features["min_degree"] = float(np.min(degrees)) if n_nodes > 0 else 0.0
        
        # 2. Edge density
        max_edges = n_nodes * (n_nodes - 1) / 2 if n_nodes > 1 else 0
        features["edge_density"] = n_edges / max_edges if max_edges > 0 else 0.0
        
        # 3. Clustering coefficient
        clustering = []
        for i in range(n_nodes):
            neighbors = np.where(adj[i] > 0)[0]
            k = len(neighbors)
            if k < 2:
                clustering.append(0.0)
                continue
            
            # Count triangles
            triangles = 0
            for j in range(k):
                for l in range(j + 1, k):
                    if adj[neighbors[j], neighbors[l]] > 0:
                        triangles += 1
            
            possible = k * (k - 1) / 2
            clustering.append(triangles / possible if possible > 0 else 0.0)
        
        features["mean_clustering"] = float(np.mean(clustering)) if clustering else 0.0
        
        # 4. Connected components
        visited = set()
        components = []
        
        for i in range(n_nodes):
            if i not in visited:
                # BFS to find component
                component = []
                queue = [i]
                visited.add(i)
                
                while queue:
                    node = queue.pop(0)
                    component.append(node)
                    
                    neighbors = np.where(adj[node] > 0)[0]
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                components.append(component)
        
        features["num_components"] = len(components)
        features["largest_component_size"] = max(len(c) for c in components) if components else 0
        features["largest_component_ratio"] = features["largest_component_size"] / n_nodes if n_nodes > 0 else 0.0
        
        # 5. Path length distribution
        if n_nodes > 0 and components:
            largest_comp = max(components, key=len)
            if len(largest_comp) > 1:
                # Calculate average shortest path in largest component
                sub_adj = adj[np.ix_(largest_comp, largest_comp)]
                path_lengths = []
                
                for i in range(len(largest_comp)):
                    for j in range(i + 1, len(largest_comp)):
                        # BFS for shortest path
                        dist = self._bfs_shortest_path(sub_adj, i, j)
                        if dist < float('inf'):
                            path_lengths.append(dist)
                
                features["avg_path_length"] = float(np.mean(path_lengths)) if path_lengths else 0.0
                features["diameter"] = float(max(path_lengths)) if path_lengths else 0.0
            else:
                features["avg_path_length"] = 0.0
                features["diameter"] = 0.0
        else:
            features["avg_path_length"] = 0.0
            features["diameter"] = 0.0
        
        # 6. Entropy (based on degree distribution)
        if n_nodes > 0 and features["std_degree"] > 0:
            degree_hist = np.histogram(degrees, bins=10, range=(0, features["max_degree"] + 1))[0]
            degree_hist = degree_hist[degree_hist > 0]
            probs = degree_hist / np.sum(degree_hist)
            entropy = -np.sum(probs * np.log2(probs))
            features["degree_entropy"] = float(entropy)
        else:
            features["degree_entropy"] = 0.0
        
        # 7. Betweenness centrality (simplified)
        features["betweenness_mean"] = self._calculate_betweenness(adj)
        
        # 8. Network robustness (algebraic connectivity)
        features["algebraic_connectivity"] = self._calculate_algebraic_connectivity(adj)
        
        return features
    
    def _empty_features(self) -> Dict[str, float]:
        """Return empty feature set."""
        return {
            "mean_degree": 0.0, "std_degree": 0.0, "max_degree": 0.0, "min_degree": 0.0,
            "edge_density": 0.0, "mean_clustering": 0.0, "num_components": 0.0,
            "largest_component_size": 0.0, "largest_component_ratio": 0.0,
            "avg_path_length": 0.0, "diameter": 0.0, "degree_entropy": 0.0,
            "betweenness_mean": 0.0, "algebraic_connectivity": 0.0
        }
    
    def _bfs_shortest_path(self, adj: np.ndarray, start: int, end: int) -> float:
        """BFS to find shortest path length."""
        if start == end:
            return 0.0
        
        visited = {start}
        queue = [(start, 0)]
        
        while queue:
            node, dist = queue.pop(0)
            
            neighbors = np.where(adj[node] > 0)[0]
            for neighbor in neighbors:
                if neighbor == end:
                    return float(dist + 1)
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        
        return float('inf')
    
    def _calculate_betweenness(self, adj: np.ndarray) -> float:
        """Simplified betweenness centrality calculation."""
        n = adj.shape[0]
        if n == 0:
            return 0.0
        
        # Count shortest paths through each node
        betweenness = np.zeros(n)
        
        for s in range(n):
            for t in range(s + 1, n):
                # Find all shortest paths from s to t
                paths = self._find_all_shortest_paths(adj, s, t)
                if paths:
                    for path in paths:
                        for node in path[1:-1]:  # Exclude endpoints
                            betweenness[node] += 1.0 / len(paths)
        
        return float(np.mean(betweenness)) if n > 0 else 0.0
    
    def _find_all_shortest_paths(self, adj: np.ndarray, start: int, end: int) -> List[List[int]]:
        """Find all shortest paths between two nodes."""
        if start == end:
            return [[start]]
        
        # BFS to find shortest distance
        visited = {start}
        queue = [(start, [start])]
        shortest_dist = float('inf')
        all_paths = []
        
        while queue:
            node, path = queue.pop(0)
            
            if len(path) > shortest_dist:
                continue
            
            neighbors = np.where(adj[node] > 0)[0]
            for neighbor in neighbors:
                if neighbor == end:
                    new_path = path + [neighbor]
                    dist = len(new_path) - 1
                    if dist < shortest_dist:
                        shortest_dist = dist
                        all_paths = [new_path]
                    elif dist == shortest_dist:
                        all_paths.append(new_path)
                elif neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return all_paths
    
    def _calculate_algebraic_connectivity(self, adj: np.ndarray) -> float:
        """Calculate algebraic connectivity (second smallest eigenvalue of Laplacian)."""
        n = adj.shape[0]
        if n < 2:
            return 0.0
        
        # Compute Laplacian matrix
        degree = np.sum(adj, axis=1)
        laplacian = np.diag(degree) - adj
        
        try:
            # Compute eigenvalues
            eigenvalues = np.linalg.eigvalsh(laplacian)
            # Sort eigenvalues
            eigenvalues = np.sort(eigenvalues)
            # Second smallest eigenvalue (first is 0 for connected graphs)
            return float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
        except:
            return 0.0
    
    def rgflow_transform(self, features: Dict[str, float], scale: float) -> Dict[str, float]:
        """Apply RGFlow scale transformation to network features."""
        transformed = {}
        
        # Scale transformation: network evolves under RG flow
        # Connectivity decays with scale (edge pruning)
        transformed["edge_density"] = features["edge_density"] * np.exp(-self.D * scale)
        
        # Clustering increases with scale (local structure preserved)
        transformed["mean_clustering"] = features["mean_clustering"] * (1 + self.lam * scale)
        
        # Components merge with scale (connectivity restoration)
        transformed["num_components"] = max(1, features["num_components"] * np.exp(-self.B * scale))
        
        # Path length increases with scale (hierarchical emergence)
        transformed["avg_path_length"] = features["avg_path_length"] * (1 + 0.15 * scale)
        
        # Entropy increases with scale (information growth)
        transformed["degree_entropy"] = features["degree_entropy"] * (1 + 0.08 * scale)
        
        # Degree distribution smooths with scale
        transformed["std_degree"] = features["std_degree"] * np.exp(-0.12 * scale)
        
        # Algebraic connectivity decays with scale
        transformed["algebraic_connectivity"] = features["algebraic_connectivity"] * np.exp(-0.1 * scale)
        
        return transformed
    
    def check_drift_barrier(self, features: Dict[str, float], scale: float) -> bool:
        """Check if network survives drift barrier."""
        # Drift barrier: ρ_q * N_e * Φ(M_fac) > B
        # For network: edge_density * largest_component_ratio * clustering > B
        
        rho_q = features["edge_density"]
        N_e = features.get("largest_component_ratio", 1.0)
        phi = features["mean_clustering"]
        
        verification_pressure = rho_q * N_e * phi
        
        return verification_pressure > self.B
    
    def evaluate_lawfulness(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate network lawfulness under RGFlow."""
        print("Calculating network features...")
        features = self.calculate_network_features(network)
        
        print("Applying RGFlow scale transformation...")
        rgflow_trajectory = []
        current_features = features.copy()
        
        for scale in range(1, self.SCALE_STEPS + 1):
            scale_factor = scale / self.SCALE_STEPS
            transformed = self.rgflow_transform(current_features, scale_factor)
            rgflow_trajectory.append({
                "scale": scale,
                "scale_factor": scale_factor,
                "features": transformed.copy()
            })
            current_features = transformed
        
        # Check lawfulness at each scale
        lawful_scales = []
        for step in rgflow_trajectory:
            step_features = step["features"]
            
            # Entropy bounds
            entropy = step_features["degree_entropy"]
            entropy_lawful = self.entropy_lower <= entropy <= self.entropy_upper
            
            # Density bounds
            density = step_features["edge_density"]
            density_lawful = self.density_lower <= density <= self.density_upper
            
            # Component bounds
            components = step_features["num_components"]
            component_lawful = components >= self.component_lower
            
            # Clustering bounds
            clustering = step_features["mean_clustering"]
            clustering_lawful = clustering >= self.clustering_lower
            
            # Drift barrier
            drift_survives = self.check_drift_barrier(step_features, step["scale"])
            
            # Algebraic connectivity (network robustness)
            alg_conn = step_features["algebraic_connectivity"]
            robustness_lawful = alg_conn > 0.001
            
            step_lawful = (entropy_lawful and density_lawful and component_lawful 
                          and clustering_lawful and drift_survives and robustness_lawful)
            
            lawful_scales.append({
                "scale": step["scale"],
                "scale_factor": step["scale_factor"],
                "lawful": step_lawful,
                "entropy_lawful": entropy_lawful,
                "density_lawful": density_lawful,
                "component_lawful": component_lawful,
                "clustering_lawful": clustering_lawful,
                "drift_survives": drift_survives,
                "robustness_lawful": robustness_lawful,
                "entropy": entropy,
                "density": density,
                "components": components,
                "clustering": clustering,
                "algebraic_connectivity": alg_conn,
                "verification_pressure": step_features["edge_density"] * step_features.get("largest_component_ratio", 1.0) * step_features["mean_clustering"]
            })
        
        # Determine overall lawfulness
        all_lawful = all(step["lawful"] for step in lawful_scales)
        final_state = lawful_scales[-1]
        
        # Calculate failure mask
        failure_mask = ""
        if not final_state["entropy_lawful"]:
            failure_mask += "1"
        else:
            failure_mask += "0"
        if not final_state["density_lawful"]:
            failure_mask += "1"
        else:
            failure_mask += "0"
        if not final_state["component_lawful"]:
            failure_mask += "1"
        else:
            failure_mask += "0"
        if not final_state["clustering_lawful"]:
            failure_mask += "1"
        else:
            failure_mask += "0"
        if not final_state["drift_survives"]:
            failure_mask += "1"
        else:
            failure_mask += "0"
        if not final_state["robustness_lawful"]:
            failure_mask += "1"
        else:
            failure_mask += "0"
        
        # Calculate attractor
        if all_lawful:
            attractor = "Attractor 1 (High-Fitness Network)"
        elif final_state["lawful"]:
            attractor = "Attractor 2 (Locally Lawful)"
        elif final_state["drift_survives"] and final_state["robustness_lawful"]:
            attractor = "Attractor 3 (Structurally Coherent)"
        elif failure_mask == "0000001":
            attractor = "Sabotage Attractor (Drift Barrier Violation)"
        elif failure_mask == "1000000":
            attractor = "Sabotage Attractor (Entropy Collapse)"
        else:
            attractor = "Noise Attractor (Network Fragmentation)"
        
        return {
            "initial_features": features,
            "rgflow_trajectory": rgflow_trajectory,
            "lawfulness_analysis": lawful_scales,
            "overall_lawful": all_lawful,
            "final_state": final_state,
            "attractor": attractor,
            "failure_mask": failure_mask,
            "rgflow_depth": self.SCALE_STEPS if all_lawful else len([s for s in lawful_scales if s["lawful"]])
        }
    
    def analyze_network(self) -> Dict[str, Any]:
        """Complete network RGFlow analysis."""
        print("=" * 60)
        print("RGFLOW NETWORK ANALYSIS")
        print("=" * 60)
        
        # Extract network
        network = self.extract_network_from_codebase()
        
        print(f"\nNetwork extracted:")
        print(f"  Nodes: {len(network.get('nodes', []))}")
        print(f"  Edges: {len(network.get('edges', []))}")
        
        # Evaluate lawfulness
        print("\nEvaluating network lawfulness under RGFlow...")
        evaluation = self.evaluate_lawfulness(network)
        
        return evaluation
    
    def print_results(self, evaluation: Dict[str, Any]):
        """Print formatted results."""
        if "error" in evaluation:
            print(f"\nERROR: {evaluation['error']}")
            return
        
        print("\n" + "=" * 60)
        print("RGFLOW NETWORK ANALYSIS RESULTS")
        print("=" * 60)
        
        # Initial features
        print("\nINITIAL NETWORK FEATURES")
        print("-" * 60)
        initial = evaluation["initial_features"]
        for key, value in initial.items():
            print(f"  {key}: {value:.4f}")
        
        # RGFlow trajectory
        print("\nRGFLOW SCALE TRANSFORMATION")
        print("-" * 60)
        for step in evaluation["lawfulness_analysis"]:
            status = "✓ LAWFUL" if step["lawful"] else "✗ UNLAWFUL"
            print(f"\n  Scale {step['scale']} (factor {step['scale_factor']:.2f}): {status}")
            print(f"    Entropy: {step['entropy']:.4f} (lawful: {step['entropy_lawful']})")
            print(f"    Density: {step['density']:.4f} (lawful: {step['density_lawful']})")
            print(f"    Components: {step['components']:.2f} (lawful: {step['component_lawful']})")
            print(f"    Clustering: {step['clustering']:.4f} (lawful: {step['clustering_lawful']})")
            print(f"    Algebraic Connectivity: {step['algebraic_connectivity']:.4f} (lawful: {step['robustness_lawful']})")
            print(f"    Drift Barrier: {step['drift_survives']} (pressure: {step['verification_pressure']:.4f})")
        
        # Overall assessment
        print("\n" + "-" * 60)
        print("OVERALL ASSESSMENT")
        print("-" * 60)
        print(f"  Overall Lawful: {evaluation['overall_lawful']}")
        print(f"  RGFlow Depth: {evaluation['rgflow_depth']}/{self.SCALE_STEPS}")
        print(f"  Attractor: {evaluation['attractor']}")
        print(f"  Failure Mask: {evaluation['failure_mask']}")
        
        # Final state
        print("\n" + "-" * 60)
        print("FINAL STATE (Scale 5)")
        print("-" * 60)
        final = evaluation["final_state"]
        print(f"  Entropy: {final['entropy']:.4f}")
        print(f"  Density: {final['density']:.4f}")
        print(f"  Components: {final['components']:.2f}")
        print(f"  Clustering: {final['clustering']:.4f}")
        print(f"  Algebraic Connectivity: {final['algebraic_connectivity']:.4f}")
        print(f"  Verification Pressure: {final['verification_pressure']:.4f}")
        
        print("\n" + "=" * 60)


class NativeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types and other non-serializable objects."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bool):
            return bool(obj)
        elif isinstance(obj, (str, int, float, list, dict, type(None))):
            return obj
        else:
            return str(obj)


def main():
    analyzer = NetworkRGFlowAnalyzer()
    results = analyzer.analyze_network()
    analyzer.print_results(results)
    
    # Save results
    output_path = Path("shared-data/data/network_rgflow_analysis.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, cls=NativeJSONEncoder)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
