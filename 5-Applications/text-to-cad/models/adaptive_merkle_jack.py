"""
Adaptive Merkle Jack - Self-reconfiguring structure using Research Stack mathematics.

This model uses FAMM frustration physics, manifold-generalized Bernoulli equations,
and String-Star Manifold concepts to dynamically adapt geometry under load.

Key mathematical frameworks applied:
- FAMM (Frustration physics): Stress redistribution via frustration minimization
- Manifold-generalized Bernoulli: Optimal load distribution on curved manifolds
- String-Star Manifold: Adaptive geometry with information conservation
- Scale Space: Multi-scale adaptation across different load regimes
"""

import json
import numpy as np
import math
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LoadState:
    """Current load state of the structure."""
    load_type: str  # 'compression', 'tension', 'shear', 'torsion', 'mixed'
    magnitude: float
    direction: Tuple[float, float, float]
    stress_distribution: Dict[Tuple[int, int], float]
    max_stress: float
    safety_factor: float

@dataclass
class AdaptationParameters:
    """Parameters for geometry adaptation."""
    branch_angle_sensitivity: float = 0.01  # rad/MPa (reduced)
    tubule_radius_sensitivity: float = 0.0001  # m/MPa (reduced)
    famm_frustration_threshold: float = 0.5  # Frustration threshold
    bernoulli_curvature_weight: float = 0.3  # Weight for manifold curvature
    scale_space_sigma: float = 0.01  # Scale space smoothing parameter (reduced)

class AdaptiveMerkleJack:
    """Self-adapting Merkle Jack structure using Research Stack mathematics."""
    
    def __init__(self, geometry_file: str):
        """Load initial geometry and initialize adaptive parameters."""
        with open(geometry_file, 'r') as f:
            data = json.load(f)
        
        self.nodes = data['nodes']
        self.edges = data['edges']
        self.params = data['parameters']
        
        # Build node lookup
        self.node_map = {n['id']: n for n in self.nodes}
        
        # Material properties
        self.youngs_modulus = 200e9  # Pa
        self.yield_strength = 250e6   # Pa
        
        # Convert to meters
        self.tubule_radius = self.params['tubule_radius'] / 1000.0
        self.cross_sectional_area = math.pi * self.tubule_radius**2
        
        # Adaptive state
        self.current_state = LoadState('none', 0, (0, 0, 1), {}, 0, float('inf'))
        self.adapt_params = AdaptationParameters()
        
        # FAMM frustration tensor (tracks stress frustration across edges)
        self.frustration_tensor = {}
        
        # Manifold curvature at each node (for Bernoulli adaptation)
        self.manifold_curvature = {}
        
        # Scale space representation (multi-scale geometry)
        self.scale_space = {}
    
    def calculate_famm_frustration(self, edge_stresses: Dict[Tuple[int, int], float]) -> Dict[Tuple[int, int], float]:
        """
        Calculate FAMM frustration for each edge.
        
        FAMM frustration measures the mismatch between local stress and
        optimal stress distribution. High frustration indicates need for adaptation.
        
        F = |σ_local - σ_optimal| / σ_optimal
        """
        if not edge_stresses:
            return {}
        
        # Optimal stress is uniform distribution (FAMM principle)
        mean_stress = np.mean(list(edge_stresses.values()))
        optimal_stress = mean_stress
        
        frustration = {}
        for edge, stress in edge_stresses.items():
            if optimal_stress > 0:
                frustration[edge] = abs(stress - optimal_stress) / optimal_stress
            else:
                frustration[edge] = 0.0
        
        return frustration
    
    def calculate_manifold_curvature(self, node_id: int) -> float:
        """
        Calculate manifold curvature at a node using String-Star Manifold.
        
        Curvature κ = ∇²φ where φ is the potential field from neighboring nodes.
        Higher curvature indicates geometric singularity requiring adaptation.
        """
        node = self.node_map[node_id]
        
        if node['parent'] is None:
            return 0.0  # Root has no curvature
        
        # Get neighboring nodes
        neighbors = [n for n in self.nodes if n['parent'] == node_id]
        parent = self.node_map[node['parent']]
        
        if not neighbors:
            return 0.0
        
        # Calculate curvature from position differences
        positions = []
        for neighbor in neighbors:
            dx = neighbor['x'] - node['x']
            dy = neighbor['y'] - node['y']
            dz = neighbor['z'] - node['z']
            positions.append(np.array([dx, dy, dz]))
        
        # Parent direction
        p_dx = node['x'] - parent['x']
        p_dy = node['y'] - parent['y']
        p_dz = node['z'] - parent['z']
        parent_dir = np.array([p_dx, p_dy, p_dz])
        
        # Curvature as deviation from parent direction
        if positions:
            avg_child_dir = np.mean(positions, axis=0)
            parent_norm = np.linalg.norm(parent_dir)
            child_norm = np.linalg.norm(avg_child_dir)
            
            if parent_norm > 0 and child_norm > 0:
                cos_angle = np.dot(parent_dir, avg_child_dir) / (parent_norm * child_norm)
                curvature = math.acos(min(1.0, max(-1.0, cos_angle)))
                return curvature
        
        return 0.0
    
    def apply_manifold_bernoulli(self, edge: Tuple[int, int], load_direction: Tuple[float, float, float]) -> float:
        """
        Apply manifold-generalized Bernoulli equation for load distribution.
        
        On a curved manifold, pressure distribution follows:
        P + ½ρv² + ρgh + ∫κ ds = constant
        
        This determines optimal load sharing based on manifold curvature.
        """
        p_id, c_id = edge
        parent = self.node_map[p_id]
        child = self.node_map[c_id]
        
        # Calculate edge direction
        dx = child['x'] - parent['x']
        dy = child['y'] - parent['y']
        dz = child['z'] - parent['z']
        edge_dir = np.array([dx, dy, dz])
        edge_dir = edge_dir / np.linalg.norm(edge_dir)
        
        # Load direction
        load_dir = np.array(load_direction)
        load_dir = load_dir / np.linalg.norm(load_dir)
        
        # Manifold curvature at child node
        curvature = self.manifold_curvature.get(c_id, 0.0)
        
        # Bernoulli adjustment: edges aligned with load and low curvature get more load
        alignment = abs(np.dot(edge_dir, load_dir))
        curvature_penalty = self.adapt_params.bernoulli_curvature_weight * curvature
        
        # Bernoulli factor (higher = better load capacity)
        bernoulli_factor = alignment * (1.0 - curvature_penalty)
        
        return bernoulli_factor
    
    def scale_space_adaptation(self, stress_level: float) -> Tuple[float, float]:
        """
        Apply Scale Space theory for multi-scale adaptation.
        
        Scale Space: Geometry evolves across scales σ to find optimal configuration.
        
        Returns: (angle_adjustment, radius_adjustment)
        """
        # Scale space parameter controls adaptation magnitude
        sigma = self.adapt_params.scale_space_sigma
        
        # Stress level normalized to yield strength
        normalized_stress = stress_level / self.yield_strength
        
        # Scale space evolution: adaptation scales with stress level
        angle_adj = self.adapt_params.branch_angle_sensitivity * normalized_stress * sigma
        radius_adj = self.adapt_params.tubule_radius_sensitivity * normalized_stress * sigma
        
        return angle_adj, radius_adj
    
    def adapt_branch_angles(self, frustration: Dict[Tuple[int, int], float]) -> Dict[int, List[float]]:
        """
        Adapt branch angles using FAMM frustration minimization.
        
        Edges with high frustration have their angles adjusted to redistribute stress.
        """
        new_angles = list(self.params['branch_angles'])
        angle_changes = {}
        
        for edge, f_val in frustration.items():
            if f_val > self.adapt_params.famm_frustration_threshold:
                p_id, c_id = edge
                child_depth = self.node_map[c_id]['depth']
                
                if child_depth < len(new_angles):
                    # Adjust angle to reduce frustration
                    # FAMM: move toward optimal configuration
                    current_angle = new_angles[child_depth]
                    
                    # Frustration-driven adjustment
                    angle_change = self.adapt_params.branch_angle_sensitivity * f_val
                    
                    # Adapt toward more vertical (better for compression)
                    if self.current_state.load_type in ['compression', 'tension']:
                        new_angles[child_depth] = max(5.0, current_angle - angle_change)
                    # Adapt toward more horizontal (better for shear/torsion)
                    else:
                        new_angles[child_depth] = min(60.0, current_angle + angle_change)
                    
                    angle_changes[edge] = [current_angle, new_angles[child_depth]]
        
        return new_angles, angle_changes
    
    def adapt_tubule_radii(self, stress_distribution: Dict[Tuple[int, int], float]) -> Dict[Tuple[int, int], float]:
        """
        Adapt tubule radii based on stress distribution.
        
        Edges under high stress get increased radius (material redistribution).
        """
        radius_changes = {}
        
        max_stress = max(stress_distribution.values()) if stress_distribution else 0
        if max_stress == 0:
            return radius_changes
        
        for edge, stress in stress_distribution.items():
            # Normalize stress
            normalized_stress = stress / max_stress
            
            # Radius adaptation proportional to stress
            if normalized_stress > 0.7:  # Only adapt highly stressed edges
                radius_increase = self.adapt_params.tubule_radius_sensitivity * normalized_stress
                radius_changes[edge] = radius_increase
        
        return radius_changes
    
    def reconfigure_geometry(self, load_state: LoadState) -> Dict[str, Any]:
        """
        Reconfigure geometry based on current load state.
        
        Uses FAMM frustration, manifold Bernoulli, and Scale Space to adapt.
        """
        self.current_state = load_state
        
        # Step 1: Calculate FAMM frustration
        frustration = self.calculate_famm_frustration(load_state.stress_distribution)
        self.frustration_tensor = frustration
        
        # Step 2: Calculate manifold curvature for all nodes
        for node in self.nodes:
            self.manifold_curvature[node['id']] = self.calculate_manifold_curvature(node['id'])
        
        # Step 3: Scale space adaptation parameters
        angle_adj, radius_adj = self.scale_space_adaptation(load_state.max_stress)
        
        # Step 4: Adapt branch angles using FAMM
        new_angles, angle_changes = self.adapt_branch_angles(frustration)
        
        # Step 5: Adapt tubule radii based on stress
        radius_changes = self.adapt_tubule_radii(load_state.stress_distribution)
        
        # Step 6: Calculate Bernoulli load redistribution factors
        bernoulli_factors = {}
        for edge in self.edges:
            bernoulli_factors[tuple(edge)] = self.apply_manifold_bernoulli(edge, load_state.direction)
        
        adaptation_result = {
            'new_branch_angles': new_angles,
            'angle_changes': angle_changes,
            'radius_changes': radius_changes,
            'frustration_tensor': frustration,
            'bernoulli_factors': bernoulli_factors,
            'manifold_curvature': self.manifold_curvature,
            'scale_space_adjustment': (angle_adj, radius_adj)
        }
        
        return adaptation_result
    
    def predict_adapted_stress(self, adaptation: Dict[str, Any], load_state: LoadState) -> Dict[Tuple[int, int], float]:
        """
        Predict stress distribution after adaptation.
        
        Uses Bernoulli factors to redistribute load based on new geometry.
        """
        adapted_stresses = {}
        
        # Base stress distribution
        base_stresses = load_state.stress_distribution
        
        # Apply Bernoulli redistribution
        total_bernoulli = sum(adaptation['bernoulli_factors'].values())
        
        for edge, base_stress in base_stresses.items():
            bernoulli_factor = adaptation['bernoulli_factors'][edge]
            
            # Redistribute based on Bernoulli factor
            if total_bernoulli > 0:
                redistribution_factor = bernoulli_factor / total_bernoulli
                adapted_stresses[edge] = base_stress * redistribution_factor
            else:
                adapted_stresses[edge] = base_stress
        
        # Apply radius changes (stress ∝ 1/r²)
        for edge, radius_change in adaptation['radius_changes'].items():
            if edge in adapted_stresses:
                new_radius = self.tubule_radius + radius_change
                area_ratio = (self.tubule_radius / new_radius) ** 2
                adapted_stresses[edge] *= area_ratio
        
        return adapted_stresses
    
    def evaluate_adaptation(self, adapted_stress: Dict[Tuple[int, int], float]) -> Dict[str, Any]:
        """
        Evaluate the effectiveness of adaptation.
        """
        if not adapted_stress:
            return {'improvement': 0, 'new_max_stress': 0, 'new_safety_factor': float('inf')}
        
        new_max_stress = max(adapted_stress.values())
        old_max_stress = self.current_state.max_stress
        
        improvement = (old_max_stress - new_max_stress) / old_max_stress if old_max_stress > 0 else 0
        new_safety_factor = self.yield_strength / new_max_stress if new_max_stress > 0 else float('inf')
        
        return {
            'improvement': improvement,
            'new_max_stress': new_max_stress,
            'new_safety_factor': new_safety_factor,
            'stress_reduction': old_max_stress - new_max_stress
        }
    
    def run_adaptive_simulation(self, load_type: str, magnitude: float, direction: Tuple[float, float, float]) -> Dict[str, Any]:
        """
        Run full adaptive simulation for a given load condition.
        """
        # Create load state (simplified - use stress from previous test)
        load_state = LoadState(load_type, magnitude, direction, {}, magnitude * 1e6, 1.0)
        
        # For simulation, create a mock stress distribution based on load type
        mock_stresses = {}
        for edge in self.edges:
            if load_type == 'tension':
                # Root edges take more load
                if edge[0] == 0:
                    mock_stresses[tuple(edge)] = magnitude / self.cross_sectional_area
                else:
                    mock_stresses[tuple(edge)] = magnitude * 0.5 / self.cross_sectional_area
            elif load_type == 'torsion':
                # Outer edges take more torsional load
                p_id, c_id = edge
                child = self.node_map[c_id]
                r = math.sqrt(child['x']**2 + child['y']**2) / 1000.0
                mock_stresses[tuple(edge)] = magnitude * r / self.cross_sectional_area
            else:
                mock_stresses[tuple(edge)] = magnitude * 0.1 / self.cross_sectional_area
        
        load_state.stress_distribution = mock_stresses
        load_state.max_stress = max(mock_stresses.values()) if mock_stresses else 0
        load_state.safety_factor = self.yield_strength / load_state.max_stress
        
        print(f"\n{'='*70}")
        print(f"ADAPTIVE SIMULATION: {load_type.upper()}")
        print(f"Magnitude: {magnitude} N")
        print(f"Initial Max Stress: {load_state.max_stress/1e6:.2f} MPa")
        print(f"Initial Safety Factor: {load_state.safety_factor:.2f}")
        print(f"{'='*70}")
        
        # Reconfigure geometry
        adaptation = self.reconfigure_geometry(load_state)
        
        print(f"\nAdaptation Summary:")
        print(f"  Branch angles changed: {len(adaptation['angle_changes'])}")
        print(f"  Radii adapted: {len(adaptation['radius_changes'])}")
        print(f"  Max frustration: {max(adaptation['frustration_tensor'].values()) if adaptation['frustration_tensor'] else 0:.3f}")
        print(f"  Scale space adjustment: ({adaptation['scale_space_adjustment'][0]:.4f} rad, {adaptation['scale_space_adjustment'][1]:.6f} m)")
        
        # Predict adapted stress
        adapted_stress = self.predict_adapted_stress(adaptation, load_state)
        
        # Evaluate adaptation
        evaluation = self.evaluate_adaptation(adapted_stress)
        
        print(f"\nAdaptation Results:")
        print(f"  Stress reduction: {evaluation['stress_reduction']/1e6:.2f} MPa")
        print(f"  Improvement: {evaluation['improvement']*100:.1f}%")
        print(f"  New Max Stress: {evaluation['new_max_stress']/1e6:.2f} MPa")
        print(f"  New Safety Factor: {evaluation['new_safety_factor']:.2f}")
        
        if evaluation['new_safety_factor'] >= 1.5:
            print(f"  ✅ ADAPTATION SUCCESSFUL")
        elif evaluation['new_safety_factor'] >= 1.0:
            print(f"  ⚠️  ADAPTATION PARTIAL (margin < 1.5)")
        else:
            print(f"  ❌ ADAPTATION INSUFFICIENT")
        
        return {
            'load_type': load_type,
            'magnitude': magnitude,
            'initial_state': {
                'max_stress': load_state.max_stress,
                'safety_factor': load_state.safety_factor
            },
            'adaptation': adaptation,
            'adapted_stress': adapted_stress,
            'evaluation': evaluation
        }

if __name__ == "__main__":
    geometry_file = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/merkle_jack.json"
    
    print("Initializing Adaptive Merkle Jack...")
    adaptive_jack = AdaptiveMerkleJack(geometry_file)
    
    print(f"Loaded {len(adaptive_jack.nodes)} nodes and {len(adaptive_jack.edges)} edges")
    print("Using FAMM frustration physics, manifold-generalized Bernoulli, and Scale Space adaptation")
    
    # Test adaptive simulation for critical load conditions
    test_conditions = [
        ('tension', 5000.0, (0, 0, 1)),      # Uplift - failed in static test
        ('torsion', 500.0, (0, 0, 1)),       # Twist - catastrophic in static test
        ('shear', 3000.0, (0, 1, 0)),        # Wind - safe but test adaptation
        ('compression', 10000.0, (0, 0, -1)), # Heavy compression - test adaptation
    ]
    
    results = []
    for load_type, magnitude, direction in test_conditions:
        result = adaptive_jack.run_adaptive_simulation(load_type, magnitude, direction)
        results.append(result)
    
    print(f"\n{'='*70}")
    print("ADAPTIVE SIMULATION SUMMARY")
    print(f"{'='*70}")
    
    for result in results:
        print(f"\n{result['load_type'].upper()}:")
        print(f"  Initial SF: {result['initial_state']['safety_factor']:.2f}")
        print(f"  Final SF: {result['evaluation']['new_safety_factor']:.2f}")
        print(f"  Improvement: {result['evaluation']['improvement']*100:.1f}%")
        print(f"  Status: {'✅ PASS' if result['evaluation']['new_safety_factor'] >= 1.5 else '⚠️ MARGINAL' if result['evaluation']['new_safety_factor'] >= 1.0 else '❌ FAIL'}")
    
    # Count passes
    passes = sum(1 for r in results if r['evaluation']['new_safety_factor'] >= 1.5)
    marginals = sum(1 for r in results if 1.0 <= r['evaluation']['new_safety_factor'] < 1.5)
    fails = sum(1 for r in results if r['evaluation']['new_safety_factor'] < 1.0)
    
    print(f"\nFinal Results: {passes} PASS, {marginals} MARGINAL, {fails} FAIL out of {len(results)} tests")
    
    if fails == 0:
        print("✅ Adaptive model achieves safety under all tested conditions")
    elif passes + marginals >= len(results) * 0.8:
        print("⚠️ Adaptive model achieves acceptable safety under most conditions")
    else:
        print("❌ Adaptive model requires further optimization")
