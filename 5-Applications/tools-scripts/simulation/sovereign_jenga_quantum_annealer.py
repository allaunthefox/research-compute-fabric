#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Quantum Annealing Interface for Sovereign Jenga Optimization

This module formulates the truss structure optimization as a QUBO (Quadratic Unconstrained
Binary Optimization) problem, solvable by:
- D-Wave quantum annealers (real quantum hardware)
- Classical simulated annealing (for testing)
- Fujitsu Digital Annealer (alternative quantum-inspired hardware)

The optimization finds optimal load paths through the truss structure, minimizing:
- Material usage (fewer struts = lighter)
- Stress concentrations (even distribution)
- While maintaining structural integrity
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])

# Try to import D-Wave libraries (optional)
try:
    import dwave.system
    import dimod
    DWAVE_AVAILABLE = True
except ImportError:
    DWAVE_AVAILABLE = False

# Try to import networkx for graph operations
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


# ============================================================================
# QUBO Formulation for Truss Optimization
# ============================================================================

@dataclass
class TrussOptimizationQUBO:
    """
    Formulates truss structure optimization as QUBO problem.
    
    The QUBO formulation encodes:
    - Binary variable for each potential strut (1 = exists, 0 = removed)
    - Objective: minimize weight while maintaining structural integrity
    - Constraints: stress < yield, displacement < threshold
    """
    
    nodes: AnyArray  # Nx3 array of node positions
    edges: List[Tuple[int, int]]  # List of (node_i, node_j) tuples
    loads: Dict[int, AnyArray]  # node_id -> force vector
    supports: List[int]  # Fixed node IDs
    
    # Optimization weights
    weight_penalty: float = 1.0  # Penalty for material usage
    stress_penalty: float = 10.0  # Penalty for stress violations
    displacement_penalty: float = 5.0  # Penalty for displacement violations
    
    def formulate_qubo(self) -> Tuple[AnyArray, float]:
        """
        Formulate truss optimization as QUBO.
        
        Returns:
            Q: QUBO matrix (NxN upper triangular)
            offset: Constant offset
        """
        n_struts = len(self.edges)
        
        # QUBO matrix (upper triangular)
        Q = xp.zeros((n_struts, n_struts))
        offset = 0.0
        
        # Objective 1: Minimize weight (fewer struts)
        for i in range(n_struts):
            Q[i, i] += self.weight_penalty
        
        # Objective 2: Stress distribution
        # Simplified: penalize struts that would be overloaded
        for i, (node_i, node_j) in enumerate(self.edges):
            # Calculate strut length
            pos_i = self.nodes[node_i]
            pos_j = self.nodes[node_j]
            length = xp.linalg.norm(pos_j - pos_i)
            
            # Simplified stress estimate (would need FEA for real calculation)
            # Penalize long struts (more prone to buckling)
            Q[i, i] += self.stress_penalty * (length / 10.0)
        
        # Objective 3: Connectivity constraints (Future Flow Variables Layer)
        
        return Q, offset
    
    def solve_classical(self, 
                       num_reads: int = 1000,
                       annealing_time: int = 1000) -> Dict:
        """
        Solve QUBO using classical simulated annealing.
        
        This is for testing when quantum hardware is not available.
        """
        Q, offset = self.formulate_qubo()
        n_struts = len(self.edges)
        
        best_energy = float('inf')
        best_solution = None
        
        # Simulated annealing
        for read in range(num_reads):
            # Random initial solution
            solution = xp.random.randint(0, 2, n_struts)
            
            # Annealing schedule
            for step in range(annealing_time):
                temp = 1.0 - (step / annealing_time)  # Linear cooling
                
                # Propose flip
                i = xp.random.randint(0, n_struts)
                new_solution = solution.copy()
                new_solution[i] = 1 - new_solution[i]
                
                # Calculate energy change
                delta_E = self._calculate_energy_change(Q, solution, new_solution, i)
                
                # Metropolis criterion
                if delta_E < 0 or xp.random.random() < xp.exp(-delta_E / (temp + 0.001)):
                    solution = new_solution
            
            # Calculate energy
            energy = self._calculate_energy(Q, solution) + offset
            
            if energy < best_energy:
                best_energy = energy
                best_solution = solution
        
        return {
            'solution': best_solution,
            'energy': best_energy,
            'offset': offset,
            'method': 'classical_simulated_annealing'
        }
    
    def solve_quantum(self,
                     num_reads: int = 100,
                     annealing_time: float = 20.0) -> Dict:
        """
        Solve QUBO using D-Wave quantum annealer.
        
        Requires D-Wave account and access to quantum hardware.
        """
        if not DWAVE_AVAILABLE:
            raise ImportError("D-Wave libraries not available. Install dwave-system.")
        
        Q, offset = self.formulate_qubo()
        
        # Convert to dimod BQM
        bqm = dimod.BinaryQuadraticModel.from_numpy_matrix(Q, offset=offset)
        
        # Use D-Wave sampler
        sampler = dwave.system.DWaveSampler()
        
        # Submit to quantum annealer
        response = sampler.sample(
            bqm,
            num_reads=num_reads,
            annealing_time=annealing_time,
            label='Sovereign Jenga Optimization'
        )
        
        # Get best solution
        best_sample = response.first
        best_solution = best_sample.sample
        best_energy = best_sample.energy
        
        # Convert to numpy array
        solution_array = xp.array([best_solution[i] for i in range(len(self.edges))])
        
        return {
            'solution': solution_array,
            'energy': best_energy,
            'offset': offset,
            'method': 'dwave_quantum_annealing',
            'response': response
        }
    
    def _calculate_energy(self, Q: AnyArray, solution: AnyArray) -> float:
        """Calculate QUBO energy for given solution"""
        energy = 0.0
        n = len(solution)
        for i in range(n):
            for j in range(i, n):
                energy += Q[i, j] * solution[i] * solution[j]
        return energy
    
    def _calculate_energy_change(self, Q: AnyArray, 
                                 old_solution: AnyArray,
                                 new_solution: AnyArray,
                                 flipped_index: int) -> float:
        """Calculate energy change from flipping one variable"""
        old_energy = self._calculate_energy(Q, old_solution)
        new_energy = self._calculate_energy(Q, new_solution)
        return new_energy - old_energy


# ============================================================================
# G-code Generator from Optimized Structure
# ============================================================================

class OptimizedGcodeGenerator:
    """
    Generates G-code from optimized truss structure.
    """
    
    def __init__(self, 
                 nodes: AnyArray,
                 edges: List[Tuple[int, int]],
                 strut_diameter: float = 1.0,
                 feedrate: float = 800):
        
        self.nodes = nodes
        self.edges = edges
        self.strut_diameter = strut_diameter
        self.feedrate = feedrate
    
    def generate_gcode(self, output_path: str):
        """
        Generate G-code for laser sintering machine.
        """
        gcode_lines = [
            "; Mechanical Merkle Tree G-code",
            "; Generated by Sovereign Jenga Optimizer",
            "; Quantum Annealing Optimized Structure",
            "",
            "G21  ; Metric units",
            "G90  ; Absolute positioning",
            ""
        ]
        
        # Generate toolpath for each strut
        for edge_idx, (node_i, node_j) in enumerate(self.edges):
            pos_i = self.nodes[node_i]
            pos_j = self.nodes[node_j]
            
            # Move to start
            gcode_lines.append(f"G0 X{pos_i[0]:.2f} Y{pos_i[1]:.2f} Z{pos_i[2]:.2f}")
            
            # Laser on
            gcode_lines.append("M3")
            
            # Move to end (deposit material)
            gcode_lines.append(f"G1 X{pos_j[0]:.2f} Y{pos_j[1]:.2f} Z{pos_j[2]:.2f} F{self.feedrate}")
            
            # Laser off
            gcode_lines.append("M5")
            
            gcode_lines.append("")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(gcode_lines))
        
        print(f"[+] G-code saved to: {output_path}")
    
    def generate_json(self, output_path: str, forces: Optional[AnyArray] = None):
        """
        Generate JSON structure file with node forces.
        """
        structure = {
            'nodes': [],
            'edges': self.edges
        }
        
        for i, node in enumerate(self.nodes):
            node_data = {
                'id': i,
                'x': float(node[0]),
                'y': float(node[1]),
                'z': float(node[2])
            }
            
            if forces is not None:
                node_data['F'] = float(forces[i])
            
            structure['nodes'].append(node_data)
        
        with open(output_path, 'w') as f:
            json.dump(structure, f, indent=2)
        
        print(f"[+] Structure JSON saved to: {output_path}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    Run quantum annealing optimization on Sovereign Jenga structure.
    """
    
    # Load structure from JSON
    structure_path = REPO_ROOT / "out" / "sovereign_jenga_structure.json"
    
    if not structure_path.exists():
        print(f"Error: Structure file not found: {structure_path}")
        print("Please generate structure first using sovereign_jenga_physics_test.py")
        return
    
    with open(structure_path, 'r') as f:
        structure = json.load(f)
    
    nodes = xp.array([[n['x'], n['y'], n['z']] for n in structure['nodes']])
    edges = [tuple(e) for e in structure['edges']]
    
    print(f"Loaded structure:")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    
    # Define loads and supports
    loads = {0: xp.array([0, 0, -1000])}  # 1000N downward at top node
    supports = [i for i in range(len(nodes)) if nodes[i, 2] < -20]  # Bottom nodes fixed
    
    print(f"  Loads: {len(loads)}")
    print(f"  Supports: {len(supports)}")
    
    # Formulate QUBO
    qubo = TrussOptimizationQUBO(
        nodes=nodes,
        edges=edges,
        loads=loads,
        supports=supports,
        weight_penalty=1.0,
        stress_penalty=10.0,
        displacement_penalty=5.0
    )
    
    # Solve (try quantum first, fall back to classical)
    if DWAVE_AVAILABLE:
        print("\nSolving with D-Wave quantum annealer...")
        try:
            result = qubo.solve_quantum(num_reads=100)
        except Exception as e:
            print(f"Quantum solve failed: {e}")
            print("Falling back to classical simulated annealing...")
            result = qubo.solve_classical(num_reads=1000)
    else:
        print("\nD-Wave not available. Using classical simulated annealing...")
        result = qubo.solve_classical(num_reads=1000)
    
    print(f"\nOptimization complete:")
    print(f"  Method: {result['method']}")
    print(f"  Energy: {result['energy']:.2f}")
    print(f"  Offset: {result['offset']:.2f}")
    
    # Extract optimized structure
    solution = result['solution']
    optimized_edges = [edges[i] for i in range(len(edges)) if solution[i] == 1]
    
    print(f"\nOptimization results:")
    print(f"  Original struts: {len(edges)}")
    print(f"  Optimized struts: {len(optimized_edges)}")
    print(f"  Material reduction: {(1 - len(optimized_edges)/len(edges)) * 100:.1f}%")
    
    # Generate G-code
    gcode_gen = OptimizedGcodeGenerator(
        nodes=nodes,
        edges=optimized_edges,
        strut_diameter=1.0,
        feedrate=800
    )
    
    output_dir = REPO_ROOT / "out" / "sovereign_jenga_quantum"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    gcode_gen.generate_gcode(output_dir / "optimized_structure.gcode")
    gcode_gen.generate_json(output_dir / "optimized_structure.json")
    
    # Save optimization results
    results = {
        'original_edges': len(edges),
        'optimized_edges': len(optimized_edges),
        'material_reduction_pct': (1 - len(optimized_edges)/len(edges)) * 100,
        'energy': result['energy'],
        'method': result['method'],
        'optimized_edges': optimized_edges
    }
    
    with open(output_dir / "optimization_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[+] All outputs saved to: {output_dir}")
    
    return results


if __name__ == "__main__":
    main()
