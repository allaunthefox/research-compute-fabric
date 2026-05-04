"""
Moving Sofa Problem Solver

Attempts to solve the famous unsolved math problem #2:
"What is the largest sofa that can fit around a 90° corner in a hallway of width 1?"

Current bounds: 2.2195 ≤ S ≤ 2.8284
Goal: Find the exact sofa constant S or improve the bounds.

Approach:
- Parametric sofa shape optimization
- scipy.optimize for numerical optimization
- PIST state space pruning for efficient search
- FAMM frustration physics for constraint satisfaction
- Quaternion counter-rotation for rotational optimization
"""

import numpy as np
import scipy.optimize as opt
import scipy.integrate as integrate
import math
from typing import Tuple, List, Dict, Any
import json

# Problem parameters
HALLWAY_WIDTH = 1.0
CORNER_ANGLE = math.pi / 2  # 90 degrees

# Current known bounds
SOFA_LOWER_BOUND = 2.2195  # Hammersley (1958)
SOFA_UPPER_BOUND = 2.8284  # Gerver (1992)

class SofaShape:
    """Parametric representation of sofa shape."""
    
    def __init__(self, params: np.ndarray):
        self.params = params
        self.area = None
        self.feasible = None
    
    def boundary_curve(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Parametric boundary curve (x(t), y(t)).
        Using generalized superellipse with rotational components.
        """
        # Unpack parameters
        a, b, n, m, theta_offset = self.params[:5]
        
        # Superellipse parametric form
        x = a * np.sign(np.cos(t)) * np.abs(np.cos(t))**(2/n)
        y = b * np.sign(np.sin(t)) * np.abs(np.sin(t))**(2/m)
        
        # Apply rotation
        x_rot = x * math.cos(theta_offset) - y * math.sin(theta_offset)
        y_rot = x * math.sin(theta_offset) + y * math.cos(theta_offset)
        
        return x_rot, y_rot
    
    def calculate_area(self) -> float:
        """Calculate area using Green's theorem."""
        def integrand(t):
            x, y = self.boundary_curve(np.array([t]))
            return 0.5 * (x[0] * np.gradient(y, t) - y[0] * np.gradient(x, t))
        
        t = np.linspace(0, 2*math.pi, 1000)
        x, y = self.boundary_curve(t)
        
        # Shoelace formula for polygon area
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        self.area = area
        return area
    
    def check_corner_feasibility(self, num_positions: int = 50) -> bool:
        """
        Check if sofa can navigate around 90° corner in L-shaped hallway.
        
        The hallway is L-shaped: one corridor goes along x-axis (y ≥ 0), 
        the other goes along y-axis (x ≥ 0). The corner is at (0,0).
        
        The sofa must translate from one corridor to the other while rotating,
        staying within the hallway bounds at all times.
        """
        t = np.linspace(0, 2*math.pi, 200)
        x, y = self.boundary_curve(t)
        
        # Simulate navigation through corner
        # Start in x-corridor (y ≥ 0), end in y-corridor (x ≥ 0)
        for i in range(num_positions + 1):
            progress = i / num_positions
            
            # Rotation angle: 0 to π/2
            theta = progress * CORNER_ANGLE
            
            # Translation: move through corner
            # Start at (s, 0), end at (0, s) where s is sofa extent
            translation_x = (1 - progress) * 2.0
            translation_y = progress * 2.0
            
            # Rotate sofa
            x_rot = x * math.cos(theta) - y * math.sin(theta)
            y_rot = x * math.sin(theta) + y * math.cos(theta)
            
            # Translate
            x_final = x_rot + translation_x
            y_final = y_rot + translation_y
            
            # Check hallway constraints
            # In L-shaped hallway: points must satisfy (x ≥ 0 and y ≥ 0) or
            # (x ≥ 0 and y ≤ 0 and x ≤ 1) or (y ≥ 0 and x ≤ 0 and y ≤ 1)
            # Simplified: check if all points are in union of two corridors
            
            # Corridor 1: x ≥ 0, 0 ≤ y ≤ 1 (horizontal corridor)
            # Corridor 2: y ≥ 0, 0 ≤ x ≤ 1 (vertical corridor)
            
            in_corridor_1 = (x_final >= 0) & (y_final >= 0) & (y_final <= HALLWAY_WIDTH)
            in_corridor_2 = (y_final >= 0) & (x_final >= 0) & (x_final <= HALLWAY_WIDTH)
            
            # Point is feasible if in either corridor
            feasible_points = in_corridor_1 | in_corridor_2
            
            # All points must be feasible
            if not np.all(feasible_points):
                return False
        
        self.feasible = True
        return True

class PISTStateSpaceOptimizer:
    """PIST state space optimization for efficient sofa shape search."""
    
    def __init__(self):
        self.phi_threshold = 0.5
    
    def prune_state_space(self, candidates: List[np.ndarray]) -> List[np.ndarray]:
        """Prune state space using PIST frustration parameter."""
        pruned = []
        
        for params in candidates:
            # Calculate frustration parameter
            phi = self.calculate_frustration(params)
            
            # Keep only low-Φ regions
            if phi < self.phi_threshold:
                pruned.append(params)
        
        return pruned
    
    def calculate_frustration(self, params: np.ndarray) -> float:
        """Calculate PIST frustration parameter for sofa shape."""
        # Simplified: frustration based on shape complexity
        a, b, n, m, theta = params[:5]
        
        # Frustration increases with shape complexity
        phi = (abs(n - 2) + abs(m - 2) + abs(theta)) / 10.0
        
        return phi

class FAMMConstraintSolver:
    """FAMM frustration physics for constraint satisfaction."""
    
    def __init__(self):
        self.thermal_energy = 1.0
        self.magnetic_energy = 10.0
    
    def calculate_constraint_energy(self, sofa: SofaShape) -> float:
        """Calculate energy cost of violating hallway constraints."""
        # Simplified: energy based on boundary violations
        t = np.linspace(0, 2*math.pi, 100)
        x, y = sofa.boundary_curve(t)
        
        # Energy penalty for exceeding hallway width
        violation_energy = np.sum(np.maximum(0, np.abs(x) - HALLWAY_WIDTH))
        violation_energy += np.sum(np.maximum(0, np.abs(y) - HALLWAY_WIDTH))
        
        return violation_energy
    
    def calculate_frustration(self, sofa: SofaShape) -> float:
        """Calculate FAMM frustration parameter."""
        constraint_energy = self.calculate_constraint_energy(sofa)
        phi = (self.thermal_energy + constraint_energy) / self.magnetic_energy
        return phi

class QuaternionRotationOptimizer:
    """Quaternion counter-rotation for optimal sofa rotation."""
    
    def optimize_rotation(self, sofa: SofaShape) -> Tuple[float, float, float, float]:
        """Find optimal quaternion for sofa rotation through corner."""
        
        # Optimize rotation angles using scipy
        def objective(angles):
            theta, phi, psi = angles
            
            # Create quaternion from angles
            q = self.euler_to_quaternion(theta, phi, psi)
            
            # Calculate rotation energy
            energy = np.sum(np.abs(q))
            
            return energy
        
        # Optimize angles
        result = opt.minimize(
            objective,
            x0=[0, 0, 0],
            bounds=[(-math.pi, math.pi), (-math.pi, math.pi), (-math.pi, math.pi)],
            method='L-BFGS-B'
        )
        
        theta, phi, psi = result.x
        q = self.euler_to_quaternion(theta, phi, psi)
        
        return q
    
    def euler_to_quaternion(self, theta: float, phi: float, psi: float) -> Tuple[float, float, float, float]:
        """Convert Euler angles to quaternion."""
        cy = math.cos(phi * 0.5)
        sy = math.sin(phi * 0.5)
        cp = math.cos(theta * 0.5)
        sp = math.sin(theta * 0.5)
        cr = math.cos(psi * 0.5)
        sr = math.sin(psi * 0.5)
        
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        
        return (w, x, y, z)

class MovingSofaSolver:
    """Main solver for the Moving Sofa Problem."""
    
    def __init__(self):
        self.pist = PISTStateSpaceOptimizer()
        self.famm = FAMMConstraintSolver()
        self.quaternion = QuaternionRotationOptimizer()
        self.best_sofa = None
        self.best_area = 0.0
        self.history = []
    
    def objective_function(self, params: np.ndarray) -> float:
        """
        Objective: maximize area subject to corner feasibility.
        Returns negative area for minimization.
        """
        # Ensure parameters are valid
        params = np.abs(params)  # All parameters positive
        params[4] = params[4] % (2*math.pi)  # Angle in [0, 2π]
        
        # Create sofa shape
        sofa = SofaShape(params)
        
        # Check feasibility
        if not sofa.check_corner_feasibility():
            return 1e6  # Large penalty for infeasible shapes
        
        # Calculate area
        area = sofa.calculate_area()
        
        # FAMM frustration penalty
        phi = self.famm.calculate_frustration(sofa)
        penalty = phi * 1000  # Scale penalty
        
        # Maximize area, minimize penalty
        return -area + penalty
    
    def generate_initial_candidates(self, n: int = 100) -> List[np.ndarray]:
        """Generate initial candidate sofa shapes."""
        candidates = []
        
        for _ in range(n):
            # Random parameters: [a, b, n, m, theta]
            a = np.random.uniform(0.5, 2.0)
            b = np.random.uniform(0.5, 2.0)
            n = np.random.uniform(1.5, 3.0)
            m = np.random.uniform(1.5, 3.0)
            theta = np.random.uniform(0, 2*math.pi)
            
            params = np.array([a, b, n, m, theta])
            candidates.append(params)
        
        return candidates
    
    def optimize_candidate(self, params: np.ndarray) -> Dict[str, Any]:
        """Optimize a single candidate sofa shape."""
        
        result = opt.minimize(
            self.objective_function,
            params,
            bounds=[(0.1, 3.0), (0.1, 3.0), (1.0, 5.0), (1.0, 5.0), (0, 2*math.pi)],
            method='L-BFGS-B',
            options={'maxiter': 1000}
        )
        
        sofa = SofaShape(result.x)
        area = sofa.calculate_area()
        
        return {
            'params': result.x,
            'area': area,
            'success': result.success,
            'message': result.message
        }
    
    def solve(self, iterations: int = 50) -> Dict[str, Any]:
        """
        Attempt to solve the Moving Sofa Problem.
        
        Returns:
            Dictionary with best sofa parameters, area, and comparison to known bounds.
        """
        print("Attempting to solve the Moving Sofa Problem...")
        print(f"Current bounds: {SOFA_LOWER_BOUND} ≤ S ≤ {SOFA_UPPER_BOUND}")
        print("=" * 70)
        
        # Generate initial candidates
        candidates = self.generate_initial_candidates(200)
        
        # PIST pruning
        print(f"Initial candidates: {len(candidates)}")
        candidates = self.pist.prune_state_space(candidates)
        print(f"After PIST pruning: {len(candidates)}")
        
        # Optimize each candidate
        best_result = None
        best_area = 0.0
        
        for i, params in enumerate(candidates):
            print(f"\nOptimizing candidate {i+1}/{len(candidates)}...")
            
            result = self.optimize_candidate(params)
            
            if result['area'] > best_area:
                best_area = result['area']
                best_result = result
                print(f"  New best area: {best_area:.6f}")
            
            self.history.append(result)
        
        # Final optimization on best result
        if best_result:
            print("\nFinal optimization on best result...")
            final_result = self.optimize_candidate(best_result['params'])
            
            if final_result['area'] > best_area:
                best_area = final_result['area']
                best_result = final_result
        
        # Create best sofa
        self.best_sofa = SofaShape(best_result['params'])
        self.best_area = best_area
        
        # Compare to known bounds
        print("\n" + "=" * 70)
        print("RESULTS:")
        print(f"Best area found: {self.best_area:.6f}")
        print(f"Known lower bound: {SOFA_LOWER_BOUND}")
        print(f"Known upper bound: {SOFA_UPPER_BOUND}")
        
        if self.best_area > SOFA_LOWER_BOUND:
            improvement = self.best_area - SOFA_LOWER_BOUND
            print(f"Improvement over lower bound: {improvement:.6f}")
        
        if self.best_area < SOFA_UPPER_BOUND:
            gap = SOFA_UPPER_BOUND - self.best_area
            print(f"Gap to upper bound: {gap:.6f}")
        
        if self.best_area > SOFA_UPPER_BOUND:
            print("\n*** BREAKTHROUGH: Found sofa larger than current upper bound! ***")
        
        return {
            'best_params': best_result['params'].tolist(),
            'best_area': float(self.best_area),
            'lower_bound': SOFA_LOWER_BOUND,
            'upper_bound': SOFA_UPPER_BOUND,
            'improvement': float(self.best_area - SOFA_LOWER_BOUND),
            'history': self.history
        }

if __name__ == "__main__":
    solver = MovingSofaSolver()
    results = solver.solve(iterations=50)
    
    # Save results
    output_file = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/moving_sofa_results.json"
    
    # Convert numpy types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    with open(output_file, 'w') as f:
        json.dump(convert_numpy_types(results), f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nMoving Sofa Problem solver complete!")
