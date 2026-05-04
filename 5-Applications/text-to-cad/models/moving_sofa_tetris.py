"""
Moving Sofa Problem as N-Space Tetris Problem

Treats the sofa as a tetromino-like shape that must navigate through
the corridor by rotating and translating, similar to tetris block fitting.

Approach:
- Discretize sofa into grid of unit squares (pixels)
- Model corridor as discrete grid
- Use pathfinding/search for navigation feasibility
- Optimize shape by adding/removing squares while maintaining navigability
- N-space: configuration space of (x, y, θ) for each position
"""

import numpy as np
import scipy.optimize as opt
from typing import List, Tuple, Set, Dict, Any
import json
from collections import deque
import math

# Problem parameters
GRID_RESOLUTION = 0.05  # Grid resolution for discretization
HALLWAY_WIDTH = 1.0
CORNER_ANGLE = math.pi / 2

# Known bounds
SOFA_LOWER_BOUND = 2.2195
SOFA_UPPER_BOUND = 2.8284

class TetrisSofa:
    """Sofa represented as collection of unit squares (tetris-like)."""
    
    def __init__(self, squares: Set[Tuple[int, int]]):
        """
        Initialize sofa from set of square coordinates.
        Coordinates are in grid units (integer).
        """
        self.squares = squares
        self.area = len(squares) * (GRID_RESOLUTION ** 2)
        self.center = self._calculate_center()
    
    def _calculate_center(self) -> Tuple[float, float]:
        """Calculate geometric center of sofa."""
        if not self.squares:
            return (0.0, 0.0)
        
        x_coords = [x for x, y in self.squares]
        y_coords = [y for x, y in self.squares]
        
        center_x = np.mean(x_coords) * GRID_RESOLUTION
        center_y = np.mean(y_coords) * GRID_RESOLUTION
        
        return (center_x, center_y)
    
    def rotate(self, angle: float) -> 'TetrisSofa':
        """Rotate sofa by given angle around center."""
        rotated_squares = set()
        
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        for x, y in self.squares:
            # Translate to origin
            x_centered = (x * GRID_RESOLUTION - self.center[0])
            y_centered = (y * GRID_RESOLUTION - self.center[1])
            
            # Rotate
            x_rot = x_centered * cos_a - y_centered * sin_a
            y_rot = x_centered * sin_a + y_centered * cos_a
            
            # Translate back and discretize
            x_new = int((x_rot + self.center[0]) / GRID_RESOLUTION)
            y_new = int((y_rot + self.center[1]) / GRID_RESOLUTION)
            
            rotated_squares.add((x_new, y_new))
        
        return TetrisSofa(rotated_squares)
    
    def translate(self, dx: float, dy: float) -> 'TetrisSofa':
        """Translate sofa by (dx, dy)."""
        translated_squares = set()
        
        dx_grid = int(dx / GRID_RESOLUTION)
        dy_grid = int(dy / GRID_RESOLUTION)
        
        for x, y in self.squares:
            translated_squares.add((x + dx_grid, y + dy_grid))
        
        return TetrisSofa(translated_squares)
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Get bounding box (xmin, ymin, xmax, ymax)."""
        if not self.squares:
            return (0.0, 0.0, 0.0, 0.0)
        
        x_coords = [x for x, y in self.squares]
        y_coords = [y for x, y in self.squares]
        
        xmin = min(x_coords) * GRID_RESOLUTION
        ymin = min(y_coords) * GRID_RESOLUTION
        xmax = max(x_coords) * GRID_RESOLUTION
        ymax = max(y_coords) * GRID_RESOLUTION
        
        return (xmin, ymin, xmax, ymax)
    
    def is_connected(self) -> bool:
        """Check if all squares are connected (tetris property)."""
        if not self.squares:
            return True
        
        # BFS to check connectivity
        visited = set()
        queue = deque([next(iter(self.squares))])
        visited.add(queue[0])
        
        while queue:
            current = queue.popleft()
            x, y = current
            
            # Check 4 neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (x + dx, y + dy)
                if neighbor in self.squares and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(self.squares)

class CorridorGrid:
    """Discrete representation of L-shaped corridor."""
    
    def __init__(self, resolution: float = GRID_RESOLUTION):
        self.resolution = resolution
        self.grid_size = int(HALLWAY_WIDTH / resolution) + 20  # Extra space for navigation
        self.occupied = set()
    
    def add_corridor(self):
        """Add L-shaped corridor to grid."""
        # Horizontal corridor (y ≥ 0, x from -10 to 10)
        for x in range(-10, 10):
            for y in range(0, int(HALLWAY_WIDTH / self.resolution)):
                self.occupied.add((x, y))
        
        # Vertical corridor (x ≥ 0, y from -10 to 10)
        for x in range(0, int(HALLWAY_WIDTH / self.resolution)):
            for y in range(-10, 10):
                self.occupied.add((x, y))
    
    def is_valid_position(self, sofa: TetrisSofa) -> bool:
        """Check if sofa position is valid (within corridor)."""
        for x, y in sofa.squares:
            if (x, y) not in self.occupied:
                return False
        return True

class NSpaceNavigator:
    """Navigate sofa through corridor in n-dimensional configuration space."""
    
    def __init__(self):
        self.corridor = CorridorGrid()
        self.corridor.add_corridor()
    
    def can_navigate(self, sofa: TetrisSofa, num_steps: int = 50) -> bool:
        """
        Check if sofa can navigate from horizontal to vertical corridor.
        Uses BFS in configuration space (x, y, θ).
        """
        # Configuration space: (x, y, θ)
        # Start position: in horizontal corridor, θ = 0
        # End position: in vertical corridor, θ = π/2
        
        start_config = (10, 5, 0)  # x, y, θ (grid coordinates)
        end_config = (5, 10, math.pi/2)
        
        # BFS in configuration space
        visited = set()
        queue = deque([start_config])
        visited.add(start_config)
        
        step_size_x = 1
        step_size_y = 1
        step_size_theta = CORNER_ANGLE / num_steps
        
        while queue:
            x, y, theta = queue.popleft()
            
            # Check if reached end
            if abs(x - end_config[0]) < 2 and abs(y - end_config[1]) < 2 and abs(theta - end_config[2]) < 0.1:
                return True
            
            # Generate neighbors in configuration space
            neighbors = [
                (x + step_size_x, y, theta),
                (x - step_size_x, y, theta),
                (x, y + step_size_y, theta),
                (x, y - step_size_y, theta),
                (x, y, theta + step_size_theta),
                (x, y, theta - step_size_theta)
            ]
            
            for nx, ny, ntheta in neighbors:
                if (nx, ny, ntheta) in visited:
                    continue
                
                # Check if this configuration is valid
                test_sofa = sofa.translate(nx * self.corridor.resolution, ny * self.corridor.resolution)
                test_sofa = test_sofa.rotate(ntheta)
                
                if self.corridor.is_valid_position(test_sofa):
                    visited.add((nx, ny, ntheta))
                    queue.append((nx, ny, ntheta))
        
        return False

class TetrisOptimizer:
    """Optimize sofa shape using tetris-like block assembly."""
    
    def __init__(self):
        self.navigator = NSpaceNavigator()
        self.best_sofa = None
        self.best_area = 0.0
    
    def generate_initial_shapes(self, n: int = 100) -> List[TetrisSofa]:
        """Generate initial tetris-like shapes."""
        shapes = []
        
        for _ in range(n):
            # Start with a single square
            squares = {(0, 0)}
            
            # Randomly add squares to build shape
            num_squares = np.random.randint(5, 20)
            
            for _ in range(num_squares):
                # Pick a random existing square
                if not squares:
                    break
                
                existing = list(squares)[np.random.randint(len(squares))]
                
                # Add neighbor
                neighbor_offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                dx, dy = neighbor_offsets[np.random.randint(len(neighbor_offsets))]
                new_square = (existing[0] + dx, existing[1] + dy)
                squares.add(new_square)
            
            sofa = TetrisSofa(squares)
            if sofa.is_connected():
                shapes.append(sofa)
        
        return shapes
    
    def optimize_shape(self, initial_sofa: TetrisSofa) -> TetrisSofa:
        """Optimize a single shape by adding/removing squares."""
        current_sofa = initial_sofa
        
        for iteration in range(100):
            # Try to add a square
            neighbors = set()
            for x, y in current_sofa.squares:
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    neighbors.add((x + dx, y + dy))
            
            # Remove squares that are already in sofa
            neighbors = neighbors - current_sofa.squares
            
            if neighbors:
                # Try adding a random neighbor
                new_square = list(neighbors)[np.random.randint(len(neighbors))]
                new_squares = current_sofa.squares.copy()
                new_squares.add(new_square)
                test_sofa = TetrisSofa(new_squares)
                
                if test_sofa.is_connected() and self.navigator.can_navigate(test_sofa):
                    if test_sofa.area > current_sofa.area:
                        current_sofa = test_sofa
        
        return current_sofa
    
    def solve(self, iterations: int = 50) -> Dict[str, Any]:
        """Solve Moving Sofa Problem using tetris approach."""
        print("Solving Moving Sofa Problem as N-Space Tetris Problem...")
        print(f"Current bounds: {SOFA_LOWER_BOUND} ≤ S ≤ {SOFA_UPPER_BOUND}")
        print("=" * 70)
        
        # Generate initial shapes
        initial_shapes = self.generate_initial_shapes(200)
        print(f"Generated {len(initial_shapes)} initial tetris shapes")
        
        # Filter navigable shapes
        navigable_shapes = []
        for i, shape in enumerate(initial_shapes):
            if self.navigator.can_navigate(shape):
                navigable_shapes.append(shape)
                if shape.area > self.best_area:
                    self.best_area = shape.area
                    self.best_sofa = shape
                    print(f"  Shape {i+1}: area = {shape.area:.6f} (new best)")
        
        print(f"Navigable shapes: {len(navigable_shapes)}")
        
        # Optimize each navigable shape
        for i, shape in enumerate(navigable_shapes):
            print(f"\nOptimizing shape {i+1}/{len(navigable_shapes)}...")
            optimized = self.optimize_shape(shape)
            
            if optimized.area > self.best_area:
                self.best_area = optimized.area
                self.best_sofa = optimized
                print(f"  New best area: {self.best_area:.6f}")
        
        # Results
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
            'best_area': float(self.best_area),
            'best_squares': list(self.best_sofa.squares) if self.best_sofa else [],
            'lower_bound': SOFA_LOWER_BOUND,
            'upper_bound': SOFA_UPPER_BOUND,
            'improvement': float(self.best_area - SOFA_LOWER_BOUND) if self.best_area > 0 else 0.0
        }

if __name__ == "__main__":
    optimizer = TetrisOptimizer()
    results = optimizer.solve(iterations=50)
    
    # Save results
    output_file = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/moving_sofa_tetris_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nMoving Sofa Problem (Tetris) solver complete!")
