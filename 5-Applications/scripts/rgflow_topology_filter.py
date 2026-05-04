#!/usr/bin/env python3
"""
RGFlow Topology Filter
Apply RGFlow analysis to topology structure (manifold graph).

Analyzes the topological integrity of the codebase's manifold structure
under Renormalization Group Flow scale transformation.
"""

import json
import sys
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infra.lean_unified_shim import LeanUnifiedShim


class TopologyRGFlowAnalyzer:
    """Apply RGFlow to topology graph structure."""
    
    def __init__(self, lean_path="0-Core-Formalism/lean/Semantics", use_hardcoded=True):
        self.shim = LeanUnifiedShim(lean_path)
        self.use_hardcoded = use_hardcoded
        
        # RGFlow parameters for topology analysis
        self.D = 0.15  # Diffusion coefficient for graph structure
        self.B = 0.02  # Drift barrier for connectivity
        self.lam = 0.15  # Selection strength for edge weights
        self.SCALE_STEPS = 5  # Number of RG scale transformations
        
        # Topological lawfulness thresholds
        self.entropy_lower = 2.0
        self.entropy_upper = 4.5
        self.density_upper = 0.15  # Sparse graphs are typical
        self.component_lower = 1  # Should be connected
        
    def extract_topology(self) -> Dict[str, Any]:
        """Extract topology from Lean bindserver or use hardcoded data."""
        if self.use_hardcoded:
            # Use hardcoded topology from SwarmAnalysis.lean
            topology_data = {
                "nodes": [
                    {"id": "domain_astrophysics", "nodeType": "domain", "name": "astrophysics", "dimensionality": 3, "description": "Galaxy clusters, dark matter phenomenology"},
                    {"id": "domain_neural", "nodeType": "domain", "name": "neural", "dimensionality": 128, "description": "Spike populations, synaptic dynamics"},
                    {"id": "domain_maritime", "nodeType": "domain", "name": "maritime", "dimensionality": 2, "description": "Vessel tracking, phantom tide signatures"},
                    {"id": "domain_biosemiotics", "nodeType": "domain", "name": "biosemiotics", "dimensionality": 64, "description": "Sign systems in biological processes"},
                    {"id": "domain_mereotopological", "nodeType": "domain", "name": "mereotopological", "dimensionality": 32, "description": "Part-whole relations and topological structure"},
                    {"id": "domain_compression", "nodeType": "domain", "name": "compression", "dimensionality": 16, "description": "Shannon entropy, routing efficiency (Layer A)"},
                    {"id": "domain_routing", "nodeType": "domain", "name": "routing", "dimensionality": 24, "description": "Coupling weights, interaction forces (Layer B)"},
                    {"id": "domain_topology", "nodeType": "domain", "name": "topology", "dimensionality": 48, "description": "Temporal weights, holonomy, non-Euclidean distance (Layer C₁)"},
                    {"id": "domain_braid", "nodeType": "domain", "name": "braid", "dimensionality": 8, "description": "Cosine similarity, phase accumulation (Layer C₂)"},
                    {"id": "domain_invariants", "nodeType": "domain", "name": "invariants", "dimensionality": 6, "description": "Entropy, thermodynamic depth (Layer D)"},
                    {"id": "domain_verification", "nodeType": "domain", "name": "verification", "dimensionality": 4, "description": "Safety checks, equilibrium (Layer E)"},
                    {"id": "domain_control", "nodeType": "domain", "name": "control", "dimensionality": 12, "description": "Irreversibility, thermodynamic length (Layer F)"},
                    {"id": "domain_energy", "nodeType": "domain", "name": "energy", "dimensionality": 10, "description": "Q-factor, atmospheric windows (Layer G)"},
                    {"id": "domain_algebra", "nodeType": "domain", "name": "algebra", "dimensionality": 32, "description": "Geometric algebra, group theory (Layer H)"},
                    {"id": "domain_encoding", "nodeType": "domain", "name": "encoding", "dimensionality": 8, "description": "Voxel keys, bit-packing (Layer I)"},
                    {"id": "domain_dynamics", "nodeType": "domain", "name": "dynamics", "dimensionality": 16, "description": "Time evolution, manifold deformation (Layer J)"},
                    {"id": "domain_signal", "nodeType": "domain", "name": "signal", "dimensionality": 32, "description": "DSP, FFT, bracket braid (Layer K)"},
                    {"id": "domain_application", "nodeType": "domain", "name": "application", "dimensionality": 6, "description": "FEA, engineering models (Layer L)"},
                    {"id": "domain_informational", "nodeType": "domain", "name": "informational", "dimensionality": 14, "description": "Information theory, channel capacity"},
                    {"id": "domain_geometric", "nodeType": "domain", "name": "geometric", "dimensionality": 64, "description": "Hyperbolic geometry, manifold structure"},
                    {"id": "domain_quantum", "nodeType": "domain", "name": "quantum", "dimensionality": 8, "description": "QCLEnergy, quantum mechanics"},
                    {"id": "subdomain_Physics", "nodeType": "subdomain", "name": "Physics", "categories": ["ParticleDomain", "NBody", "Boundary", "Conservation", "BindPhysics", "Interaction", "Projection", "QCLEnergy", "Examples"]},
                    {"id": "subdomain_NIICore", "nodeType": "subdomain", "name": "NIICore", "categories": ["MereotopologicalSheafHypergraph", "MorphicTriggers"]},
                    {"id": "subdomain_Extensions", "nodeType": "subdomain", "name": "Extensions", "categories": ["BettiSwoosh", "BlitterPolymorphism", "HyperbolicStateSurface", "ManifoldBlit", "MasterEquation", "NKCoupling", "SolitonEngine"]}
                ],
                "edges": [
                    {"id": "edge_Physics_Extensions", "edgeType": "import_dependency", "source": "subdomain_Physics", "target": "subdomain_Extensions", "weight": 1.0, "description": ""},
                    {"id": "edge_Physics_Informational", "edgeType": "theoretical", "source": "domain_Physics", "target": "domain_informational", "weight": 1.0, "description": "Physical systems with information-theoretic properties"},
                    {"id": "edge_Topology_Algebra", "edgeType": "theoretical", "source": "domain_topology", "target": "domain_algebra", "weight": 1.0, "description": "Topological structures with algebraic properties"},
                    {"id": "edge_Geometric_Thermodynamic", "edgeType": "theoretical", "source": "domain_geometric", "target": "domain_thermodynamic", "weight": 1.0, "description": "Geometric manifolds with thermodynamic constraints"}
                ],
                "topology": {
                    "dimension": 19,
                    "connectedComponents": 3,
                    "eulerCharacteristic": 23
                }
            }
            print("Using hardcoded topology from SwarmAnalysis.lean")
            return topology_data
        else:
            try:
                result = self.shim.query("""
                    import Semantics.SwarmAnalysis
                    #eval toJson Semantics.SwarmAnalysis.createManifoldStructure
                """)
                
                if result and "data" in result:
                    topology_data = json.loads(result["data"])
                    return topology_data
                else:
                    print("ERROR: Failed to extract topology from Lean")
                    print(f"Result: {result}")
                    return {"error": "Failed to extract topology from Lean"}
            except Exception as e:
                print(f"ERROR: Exception extracting topology: {e}")
                return {"error": f"Exception extracting topology: {e}"}
    
    def calculate_topology_features(self, topology: Dict[str, Any]) -> Dict[str, float]:
        """Calculate topological features for RGFlow."""
        nodes = topology.get("nodes", [])
        edges = topology.get("edges", [])
        
        n_nodes = len(nodes)
        n_edges = len(edges)
        
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
        
        # Calculate topological features
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
            else:
                features["avg_path_length"] = 0.0
        else:
            features["avg_path_length"] = 0.0
        
        # 6. Entropy (based on degree distribution)
        if n_nodes > 0 and features["std_degree"] > 0:
            degree_hist = np.histogram(degrees, bins=10, range=(0, features["max_degree"] + 1))[0]
            degree_hist = degree_hist[degree_hist > 0]
            probs = degree_hist / np.sum(degree_hist)
            entropy = -np.sum(probs * np.log2(probs))
            features["degree_entropy"] = float(entropy)
        else:
            features["degree_entropy"] = 0.0
        
        # 7. Dimensionality diversity
        dimensionalities = [node.get("dimensionality", 0) for node in nodes]
        features["mean_dimensionality"] = float(np.mean(dimensionalities)) if dimensionalities else 0.0
        features["std_dimensionality"] = float(np.std(dimensionalities)) if dimensionalities else 0.0
        
        # 8. Edge weight diversity
        weights = [edge.get("weight", 1.0) for edge in edges]
        if weights:
            features["mean_weight"] = float(np.mean(weights))
            features["std_weight"] = float(np.std(weights))
        else:
            features["mean_weight"] = 0.0
            features["std_weight"] = 0.0
        
        return features
    
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
    
    def rgflow_transform(self, features: Dict[str, float], scale: float) -> Dict[str, float]:
        """Apply RGFlow scale transformation to topological features."""
        transformed = {}
        
        # Scale transformation: features evolve under RG flow
        # Connectivity decays with scale (edge pruning)
        transformed["edge_density"] = features["edge_density"] * np.exp(-self.D * scale)
        
        # Clustering increases with scale (local structure preserved)
        transformed["mean_clustering"] = features["mean_clustering"] * (1 + self.lam * scale)
        
        # Components merge with scale (connectivity restoration)
        transformed["num_components"] = max(1, features["num_components"] * np.exp(-self.B * scale))
        
        # Path length increases with scale (hierarchical emergence)
        transformed["avg_path_length"] = features["avg_path_length"] * (1 + 0.1 * scale)
        
        # Entropy increases with scale (information growth)
        transformed["degree_entropy"] = features["degree_entropy"] * (1 + 0.05 * scale)
        
        # Degree distribution smooths with scale
        transformed["std_degree"] = features["std_degree"] * np.exp(-0.1 * scale)
        
        return transformed
    
    def check_drift_barrier(self, features: Dict[str, float], scale: float) -> bool:
        """Check if topology survives drift barrier."""
        # Drift barrier: ρ_q * N_e * Φ(M_fac) > B
        # For topology: edge_density * num_nodes * clustering > B
        
        rho_q = features["edge_density"]
        N_e = features.get("num_components", 1)  # Use components as observer mass
        phi = features["mean_clustering"]
        
        verification_pressure = rho_q * N_e * phi
        
        return verification_pressure > self.B
    
    def evaluate_lawfulness(self, topology: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate topological lawfulness under RGFlow."""
        print("Calculating topological features...")
        features = self.calculate_topology_features(topology)
        
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
            density_lawful = density <= self.density_upper
            
            # Component bounds
            components = step_features["num_components"]
            component_lawful = components >= self.component_lower
            
            # Drift barrier
            drift_survives = self.check_drift_barrier(step_features, step["scale"])
            
            step_lawful = entropy_lawful and density_lawful and component_lawful and drift_survives
            
            lawful_scales.append({
                "scale": step["scale"],
                "scale_factor": step["scale_factor"],
                "lawful": step_lawful,
                "entropy_lawful": entropy_lawful,
                "density_lawful": density_lawful,
                "component_lawful": component_lawful,
                "drift_survives": drift_survives,
                "entropy": entropy,
                "density": density,
                "components": components,
                "verification_pressure": step_features["edge_density"] * step_features["num_components"] * step_features["mean_clustering"]
            })
        
        # Determine overall lawfulness
        all_lawful = all(step["lawful"] for step in lawful_scales)
        final_state = lawful_scales[-1]
        
        # Calculate attractor
        if all_lawful:
            attractor = "Attractor 1 (High-Fitness Topology)"
        elif final_state["lawful"]:
            attractor = "Attractor 2 (Locally Lawful)"
        elif final_state["drift_survives"]:
            attractor = "Attractor 3 (Drift Barrier Only)"
        else:
            attractor = "Noise Attractor (Topological Collapse)"
        
        return {
            "initial_features": features,
            "rgflow_trajectory": rgflow_trajectory,
            "lawfulness_analysis": lawful_scales,
            "overall_lawful": all_lawful,
            "final_state": final_state,
            "attractor": attractor,
            "rgflow_depth": self.SCALE_STEPS if all_lawful else len([s for s in lawful_scales if s["lawful"]])
        }
    
    def analyze_topology(self) -> Dict[str, Any]:
        """Complete topology RGFlow analysis."""
        print("=" * 60)
        print("RGFLOW TOPOLOGY ANALYSIS")
        print("=" * 60)
        
        # Extract topology
        topology = self.extract_topology()
        if "error" in topology:
            return topology
        
        print(f"\nTopology extracted:")
        print(f"  Nodes: {len(topology.get('nodes', []))}")
        print(f"  Edges: {len(topology.get('edges', []))}")
        print(f"  Dimension: {topology.get('topology', {}).get('dimension', 'N/A')}")
        print(f"  Connected Components: {topology.get('topology', {}).get('connectedComponents', 'N/A')}")
        
        # Evaluate lawfulness
        print("\nEvaluating topological lawfulness under RGFlow...")
        evaluation = self.evaluate_lawfulness(topology)
        
        return evaluation
    
    def print_results(self, evaluation: Dict[str, Any]):
        """Print formatted results."""
        if "error" in evaluation:
            print(f"\nERROR: {evaluation['error']}")
            return
        
        print("\n" + "=" * 60)
        print("RGFLOW TOPOLOGY ANALYSIS RESULTS")
        print("=" * 60)
        
        # Initial features
        print("\nINITIAL TOPOLOGICAL FEATURES")
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
            print(f"    Drift Barrier: {step['drift_survives']} (pressure: {step['verification_pressure']:.4f})")
        
        # Overall assessment
        print("\n" + "-" * 60)
        print("OVERALL ASSESSMENT")
        print("-" * 60)
        print(f"  Overall Lawful: {evaluation['overall_lawful']}")
        print(f"  RGFlow Depth: {evaluation['rgflow_depth']}/{self.SCALE_STEPS}")
        print(f"  Attractor: {evaluation['attractor']}")
        
        # Final state
        print("\n" + "-" * 60)
        print("FINAL STATE (Scale 5)")
        print("-" * 60)
        final = evaluation["final_state"]
        print(f"  Entropy: {final['entropy']:.4f}")
        print(f"  Density: {final['density']:.4f}")
        print(f"  Components: {final['components']:.2f}")
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
    analyzer = TopologyRGFlowAnalyzer()
    results = analyzer.analyze_topology()
    analyzer.print_results(results)
    
    # Save results with custom encoder
    output_path = Path("shared-data/data/topology_rgflow_analysis.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, cls=NativeJSONEncoder)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
