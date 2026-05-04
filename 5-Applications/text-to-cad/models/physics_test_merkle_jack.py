"""
Physics testing for Merkle Jack structure under common strain conditions.

This script loads the merkle jack geometry and applies various strain conditions
to analyze structural integrity, stress distribution, and failure modes.
"""

import json
import numpy as np
from typing import List, Tuple, Dict, Any
import math

class StrainCondition:
    """Define a strain condition for testing."""
    
    def __init__(self, name: str, description: str, load_type: str, 
                 magnitude: float, direction: Tuple[float, float, float] = None):
        self.name = name
        self.description = description
        self.load_type = load_type  # 'compression', 'tension', 'shear', 'torsion'
        self.magnitude = magnitude
        self.direction = direction or (0, 0, 1)

class MerkleJackPhysics:
    """Physics analysis for Merkle Jack structure."""
    
    def __init__(self, geometry_file: str):
        """Load geometry data from JSON file."""
        with open(geometry_file, 'r') as f:
            data = json.load(f)
        
        self.nodes = data['nodes']
        self.edges = data['edges']
        self.params = data['parameters']
        
        # Build node lookup
        self.node_map = {n['id']: n for n in self.nodes}
        
        # Material properties (assumed: steel-like)
        self.youngs_modulus = 200e9  # Pa (200 GPa)
        self.shear_modulus = 79.3e9   # Pa (79.3 GPa)
        self.yield_strength = 250e6   # Pa (250 MPa)
        self.ultimate_strength = 400e6  # Pa (400 MPa)
        
        # Convert parameters from mm to meters
        self.tubule_radius = self.params['tubule_radius'] / 1000.0  # m
        self.cross_sectional_area = math.pi * self.tubule_radius**2
        self.moment_of_inertia = (math.pi * self.tubule_radius**4) / 4
    
    def calculate_edge_length(self, edge: Tuple[int, int]) -> float:
        """Calculate length of an edge in meters."""
        p_id, c_id = edge
        parent = self.node_map[p_id]
        child = self.node_map[c_id]
        
        dx = (child['x'] - parent['x']) / 1000.0  # mm to m
        dy = (child['y'] - parent['y']) / 1000.0
        dz = (child['z'] - parent['z']) / 1000.0
        
        return math.sqrt(dx**2 + dy**2 + dz**2)
    
    def calculate_edge_vector(self, edge: Tuple[int, int]) -> Tuple[float, float, float]:
        """Calculate unit vector along an edge."""
        p_id, c_id = edge
        parent = self.node_map[p_id]
        child = self.node_map[c_id]
        
        dx = (child['x'] - parent['x']) / 1000.0
        dy = (child['y'] - parent['y']) / 1000.0
        dz = (child['z'] - parent['z']) / 1000.0
        
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        if length < 1e-9:
            return (0, 0, 1)
        
        return (dx/length, dy/length, dz/length)
    
    def apply_compression(self, magnitude: float) -> Dict[int, float]:
        """Apply compressive load and calculate axial stress in each edge."""
        edge_stresses = {}
        
        # Load applied at top nodes (highest z)
        max_z = max(n['z'] for n in self.nodes)
        top_nodes = [n for n in self.nodes if abs(n['z'] - max_z) < 1e-6]
        
        total_load = magnitude  # Newtons
        load_per_node = total_load / len(top_nodes) if top_nodes else 0
        
        # Distribute load through tree structure
        node_loads = {n['id']: 0.0 for n in self.nodes}
        for node in top_nodes:
            node_loads[node['id']] = load_per_node
        
        # Propagate loads down the tree
        for node in sorted(self.nodes, key=lambda n: -n['z']):
            if node['parent'] is not None:
                node_loads[node['parent']] += node_loads[node['id']]
        
        # Calculate stress in each edge
        for edge in self.edges:
            p_id, c_id = edge
            load = node_loads[c_id]  # Load carried by this edge
            stress = load / self.cross_sectional_area
            edge_stresses[tuple(edge)] = stress
        
        return edge_stresses
    
    def apply_tension(self, magnitude: float) -> Dict[int, float]:
        """Apply tensile load (upward force at root)."""
        edge_stresses = {}
        
        # Load applied at root (node 0)
        total_load = magnitude  # Newtons
        
        # Load propagates up through branching structure
        node_loads = {n['id']: 0.0 for n in self.nodes}
        node_loads[0] = total_load
        
        # Distribute load to children based on load_frac
        for node in sorted(self.nodes, key=lambda n: n['z']):
            if node['parent'] is not None:
                parent = self.node_map[node['parent']]
                node_loads[node['id']] = node_loads[node['parent']] * node['load_frac']
        
        # Calculate stress in each edge
        for edge in self.edges:
            p_id, c_id = edge
            load = node_loads[c_id]
            stress = load / self.cross_sectional_area
            edge_stresses[tuple(edge)] = stress
        
        return edge_stresses
    
    def apply_shear(self, magnitude: float, direction: Tuple[float, float, float]) -> Dict[int, float]:
        """Apply shear load and calculate shear stress."""
        edge_stresses = {}
        
        # Shear stress = Force / Area
        # For simplicity, assume shear distributed to all edges
        total_load = magnitude
        load_per_edge = total_load / len(self.edges) if self.edges else 0
        
        for edge in self.edges:
            # Calculate angle between edge and shear direction
            edge_vec = self.calculate_edge_vector(edge)
            shear_dir = np.array(direction) / np.linalg.norm(direction)
            edge_dir = np.array(edge_vec)
            
            # Shear stress depends on angle
            cos_theta = abs(np.dot(shear_dir, edge_dir))
            effective_load = load_per_edge * (1 - cos_theta)  # Maximum when perpendicular
            
            stress = effective_load / self.cross_sectional_area
            edge_stresses[tuple(edge)] = stress
        
        return edge_stresses
    
    def apply_torsion(self, magnitude: float) -> Dict[int, float]:
        """Apply torsional load and calculate shear stress."""
        edge_stresses = {}
        
        # Torsional stress = T * r / J
        # T = torque, r = radius, J = polar moment of inertia
        torque = magnitude  # N·m
        polar_moment = (math.pi * self.tubule_radius**4) / 2
        
        # For simplicity, distribute torsion through structure
        # Edges farther from center carry more torsional stress
        max_r = max(math.sqrt(n['x']**2 + n['y']**2) for n in self.nodes) / 1000.0
        
        for edge in self.edges:
            p_id, c_id = edge
            child = self.node_map[c_id]
            
            # Distance from center axis
            r = math.sqrt(child['x']**2 + child['y']**2) / 1000.0
            stress = (torque * r) / polar_moment
            
            edge_stresses[tuple(edge)] = stress
        
        return edge_stresses
    
    def calculate_von_mises(self, axial_stress: float, shear_stress: float = 0) -> float:
        """Calculate Von Mises stress from axial and shear components."""
        return math.sqrt(axial_stress**2 + 3 * shear_stress**2)
    
    def analyze_stress_distribution(self, edge_stresses: Dict[Tuple[int, int], float]) -> Dict[str, Any]:
        """Analyze stress distribution across the structure."""
        stresses = list(edge_stresses.values())
        
        if not stresses:
            return {
                'max_stress': 0,
                'min_stress': 0,
                'mean_stress': 0,
                'std_stress': 0,
                'max_edge': None,
                'safety_factor': float('inf'),
                'failure_edges': []
            }
        
        max_stress = max(stresses)
        min_stress = min(stresses)
        mean_stress = np.mean(stresses)
        std_stress = np.std(stresses)
        
        # Find edge with maximum stress
        max_edge = max(edge_stresses.items(), key=lambda x: x[1])[0] if edge_stresses else None
        
        # Calculate safety factor
        safety_factor = self.yield_strength / max_stress if max_stress > 0 else float('inf')
        
        # Identify edges exceeding yield strength
        failure_edges = [edge for edge, stress in edge_stresses.items() 
                        if stress > self.yield_strength]
        
        return {
            'max_stress': max_stress,
            'min_stress': min_stress,
            'mean_stress': mean_stress,
            'std_stress': std_stress,
            'max_edge': max_edge,
            'safety_factor': safety_factor,
            'failure_edges': failure_edges,
            'failure_count': len(failure_edges)
        }
    
    def run_strain_test(self, condition: StrainCondition) -> Dict[str, Any]:
        """Run a single strain test condition."""
        print(f"\n{'='*60}")
        print(f"Testing: {condition.name}")
        print(f"Description: {condition.description}")
        print(f"Load Type: {condition.load_type}")
        print(f"Magnitude: {condition.magnitude} N")
        print(f"{'='*60}")
        
        # Apply load based on type
        if condition.load_type == 'compression':
            edge_stresses = self.apply_compression(condition.magnitude)
        elif condition.load_type == 'tension':
            edge_stresses = self.apply_tension(condition.magnitude)
        elif condition.load_type == 'shear':
            edge_stresses = self.apply_shear(condition.magnitude, condition.direction)
        elif condition.load_type == 'torsion':
            edge_stresses = self.apply_torsion(condition.magnitude)
        else:
            raise ValueError(f"Unknown load type: {condition.load_type}")
        
        # Analyze stress distribution
        analysis = self.analyze_stress_distribution(edge_stresses)
        
        # Add condition info
        analysis['condition_name'] = condition.name
        analysis['condition_description'] = condition.description
        analysis['load_type'] = condition.load_type
        analysis['load_magnitude'] = condition.magnitude
        
        # Print results
        print(f"Maximum Stress: {analysis['max_stress']/1e6:.2f} MPa")
        print(f"Minimum Stress: {analysis['min_stress']/1e6:.2f} MPa")
        print(f"Mean Stress: {analysis['mean_stress']/1e6:.2f} MPa")
        print(f"Std Dev: {analysis['std_stress']/1e6:.2f} MPa")
        print(f"Safety Factor: {analysis['safety_factor']:.2f}")
        print(f"Failure Edges: {analysis['failure_count']}/{len(self.edges)}")
        
        if analysis['failure_edges']:
            print(f"⚠️  FAILURE DETECTED at edges: {analysis['failure_edges'][:5]}...")
        elif analysis['safety_factor'] < 1.5:
            print(f"⚠️  LOW SAFETY MARGIN (< 1.5)")
        else:
            print(f"✅ STRUCTURE SAFE")
        
        return analysis
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all common strain condition tests."""
        results = []
        
        # Define test conditions
        conditions = [
            StrainCondition(
                "Compression - Moderate",
                "Compressive load equal to structure weight",
                "compression",
                1000.0  # 1 kN
            ),
            StrainCondition(
                "Compression - Heavy",
                "Heavy compressive load (10x structure weight)",
                "compression",
                10000.0  # 10 kN
            ),
            StrainCondition(
                "Tension - Uplift",
                "Upward tensile load at root",
                "tension",
                5000.0  # 5 kN
            ),
            StrainCondition(
                "Shear - Lateral",
                "Lateral shear load in X direction",
                "shear",
                2000.0,
                (1, 0, 0)
            ),
            StrainCondition(
                "Shear - Wind",
                "Wind load simulation (lateral shear)",
                "shear",
                3000.0,
                (0, 1, 0)
            ),
            StrainCondition(
                "Torsion - Twist",
                "Torsional load about vertical axis",
                "torsion",
                500.0  # 500 N·m
            ),
        ]
        
        for condition in conditions:
            result = self.run_strain_test(condition)
            results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]], output_file: str):
        """Generate a physics test report."""
        with open(output_file, 'w') as f:
            f.write("# Merkle Jack Physics Test Report\n\n")
            f.write(f"Generated: {__import__('datetime').datetime.now()}\n\n")
            f.write("## Geometry Parameters\n\n")
            f.write(f"- Depth: {self.params['depth']}\n")
            f.write(f"- Branching Factor: {self.params['branching_factor']}\n")
            f.write(f"- Branch Angles: {self.params['branch_angles']}\n")
            f.write(f"- Azimuthal Offsets: {self.params['az_offsets']}\n")
            f.write(f"- Tubule Radius: {self.params['tubule_radius']} mm\n")
            f.write(f"- Height per Level: {self.params['height_per_level']} mm\n")
            f.write(f"- Total Nodes: {len(self.nodes)}\n")
            f.write(f"- Total Edges: {len(self.edges)}\n\n")
            
            f.write("## Material Properties\n\n")
            f.write(f"- Young's Modulus: {self.youngs_modulus/1e9:.1f} GPa\n")
            f.write(f"- Shear Modulus: {self.shear_modulus/1e9:.1f} GPa\n")
            f.write(f"- Yield Strength: {self.yield_strength/1e6:.1f} MPa\n")
            f.write(f"- Ultimate Strength: {self.ultimate_strength/1e6:.1f} MPa\n\n")
            
            f.write("## Test Results\n\n")
            
            for result in results:
                f.write(f"### {result['condition_name']}\n\n")
                f.write(f"**Description:** {result['condition_description']}\n\n")
                f.write(f"**Load Type:** {result['load_type']}\n")
                f.write(f"**Magnitude:** {result['load_magnitude']} N\n\n")
                f.write(f"**Maximum Stress:** {result['max_stress']/1e6:.2f} MPa\n")
                f.write(f"**Minimum Stress:** {result['min_stress']/1e6:.2f} MPa\n")
                f.write(f"**Mean Stress:** {result['mean_stress']/1e6:.2f} MPa\n")
                f.write(f"**Standard Deviation:** {result['std_stress']/1e6:.2f} MPa\n")
                f.write(f"**Safety Factor:** {result['safety_factor']:.2f}\n")
                f.write(f"**Failure Edges:** {result['failure_count']}/{len(self.edges)}\n\n")
                
                if result['failure_edges']:
                    f.write(f"⚠️ **FAILURE DETECTED** at edges: {result['failure_edges'][:5]}\n\n")
                elif result['safety_factor'] < 1.5:
                    f.write(f"⚠️ **LOW SAFETY MARGIN** (< 1.5)\n\n")
                else:
                    f.write(f"✅ **STRUCTURE SAFE**\n\n")
            
            f.write("## Summary\n\n")
            
            safe_tests = sum(1 for r in results if r['failure_count'] == 0 and r['safety_factor'] >= 1.5)
            warning_tests = sum(1 for r in results if r['failure_count'] == 0 and r['safety_factor'] < 1.5)
            failure_tests = sum(1 for r in results if r['failure_count'] > 0)
            
            f.write(f"- Safe Tests: {safe_tests}/{len(results)}\n")
            f.write(f"- Low Margin Tests: {warning_tests}/{len(results)}\n")
            f.write(f"- Failure Tests: {failure_tests}/{len(results)}\n\n")
            
            if failure_tests > 0:
                f.write("⚠️ **CRITICAL:** Structure fails under some load conditions.\n\n")
            elif warning_tests > 0:
                f.write("⚠️ **WARNING:** Structure has low safety margins under some conditions.\n\n")
            else:
                f.write("✅ **PASS:** Structure is safe under all tested conditions.\n\n")
        
        print(f"\nReport generated: {output_file}")

if __name__ == "__main__":
    # Load geometry and run physics tests
    geometry_file = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/merkle_jack.json"
    output_report = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/physics_test_report.md"
    
    print("Loading Merkle Jack geometry...")
    physics = MerkleJackPhysics(geometry_file)
    
    print(f"Loaded {len(physics.nodes)} nodes and {len(physics.edges)} edges")
    
    print("\nRunning physics strain tests...")
    results = physics.run_all_tests()
    
    print("\nGenerating test report...")
    physics.generate_report(results, output_report)
    
    print("\nPhysics testing complete!")
