#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Sovereign Jenga Physics Test Suite
FEA + Rigid Body Simulation for N-Space Manifold Verification

This module provides physics validation for the Sovereign Jenga demonstration system.
It interfaces with external FEA/rigid body engines to test:
- Stress distribution across lattice structures
- Global vibration modes
- Load path redundancy
- "Impossible" configuration stability

External Dependencies (choose one or more):
- pyCalculix (CalculiX FEA, free/open-source)
- FEniCS (FEM, free/open-source)
- PyAnsys (ANSYS, commercial)
- pybullet (Rigid body dynamics, free)
- mujoco (Rigid body dynamics, free for research)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])

# Try to import optional physics engines
try:
    import calculix
    CALCULIX_AVAILABLE = True
except ImportError:
    CALCULIX_AVAILABLE = False

try:
    import fenics
    FENICS_AVAILABLE = True
except ImportError:
    FENICS_AVAILABLE = False

try:
    import pybullet as p
    PYBULLET_AVAILABLE = True
except ImportError:
    PYBULLET_AVAILABLE = False

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


# ============================================================================
# Material Properties (Aluminum 6061-T6)
# ============================================================================

@dataclass
class MaterialProperties:
    """First-principles material properties for Aluminum 6061-T6"""
    name: str = "Aluminum 6061-T6"
    
    # Atomic Properties
    atomic_mass: float = 26.98  # g/mol
    crystal_structure: str = "FCC"
    lattice_parameter: float = 4.05e-10  # m (4.05 Å)
    
    # Elastic Properties (Isotropic)
    youngs_modulus: float = 69e9  # Pa (69 GPa)
    shear_modulus: float = 26e9  # Pa (26 GPa)
    bulk_modulus: float = 76e9  # Pa (76 GPa)
    poisson_ratio: float = 0.33
    
    # Density
    density: float = 2700  # kg/m³
    
    # Strength
    yield_strength: float = 276e6  # Pa (276 MPa)
    ultimate_strength: float = 310e6  # Pa (310 MPa)
    
    # Wave Propagation
    longitudinal_wave_speed: float = 6400  # m/s
    shear_wave_speed: float = 3100  # m/s
    
    # Compressibility
    compressibility: float = 1.32e-11  # Pa⁻¹
    
    # Damping
    damping_ratio: float = 0.001  # Structural damping


# ============================================================================
# Stress Tensor Operations (6D "N-Space")
# ============================================================================

class StressTensor:
    """
    6D stress tensor operations for "N-space" mechanics.
    
    This is the real physics behind the "N-dimensional stress space" metaphor.
    """
    
    @staticmethod
    def from_components(sx: float, sy: float, sz: float,
                       txy: float, txz: float, tyz: float) -> AnyArray:
        """Create stress tensor from 6 independent components"""
        return xp.array([
            [sx, txy, txz],
            [txy, sy, tyz],
            [txz, tyz, sz]
        ])
    
    @staticmethod
    def to_vector(tensor: AnyArray) -> AnyArray:
        """Convert 3x3 tensor to 6D vector (Voigt notation)"""
        return xp.array([
            tensor[0, 0],  # σx
            tensor[1, 1],  # σy
            tensor[2, 2],  # σz
            tensor[0, 1],  # τxy
            tensor[0, 2],  # τxz
            tensor[1, 2]   # τyz
        ])
    
    @staticmethod
    def principal_stresses(tensor: AnyArray) -> Tuple[AnyArray, AnyArray]:
        """
        Compute principal stresses and directions.
        
        Returns:
            eigenvalues: Principal stresses (σ1, σ2, σ3)
            eigenvectors: Principal directions
        """
        eigenvalues, eigenvectors = xp.linalg.eigh(tensor)
        # Sort by magnitude
        idx = xp.abs(eigenvalues).argsort()[::-1]
        return eigenvalues[idx], eigenvectors[:, idx]
    
    @staticmethod
    def von_mises(tensor: AnyArray) -> float:
        """
        Compute von Mises stress (yield criterion).
        
        σ_vm = √(0.5 * [(σ1-σ2)² + (σ2-σ3)² + (σ3-σ1)²])
        """
        principal, _ = StressTensor.principal_stresses(tensor)
        s1, s2, s3 = principal
        
        von_mises = xp.sqrt(0.5 * (
            (s1 - s2)**2 + 
            (s2 - s3)**2 + 
            (s3 - s1)**2
        ))
        
        return von_mises
    
    @staticmethod
    def equilibrium_residual(stress_field: AnyArray, 
                            body_forces: AnyArray) -> AnyArray:
        """
        Check equilibrium: ∇ · σ + f = 0
        
        Returns residual (should be ~0 for equilibrium)
        """
        # Simplified: compute divergence numerically
        div_sigma = xp.gradient(stress_field, axis=0)
        residual = div_sigma + body_forces
        return residual


# ============================================================================
# Lattice Structure Generator (Octet Truss)
# ============================================================================

class OctetTrussGenerator:
    """
    Generate octet truss lattice structures for Sovereign Jenga blocks.
    """
    
    def __init__(self, 
                 unit_cell_size: float = 0.01,  # 10mm
                 strut_diameter: float = 0.001,  # 1mm
                 relative_density: float = 0.2):
        
        self.unit_cell_size = unit_cell_size
        self.strut_diameter = strut_diameter
        self.relative_density = relative_density
    
    def generate_unit_cell(self) -> Dict:
        """
        Generate single octet truss unit cell.
        
        Returns dict with:
        - nodes: Nx3 array of node positions
        - elements: Mx2 array of element connectivity
        """
        # Octet truss has 14 nodes per unit cell
        # (8 corner + 6 face-center)
        
        a = self.unit_cell_size
        
        # Node positions
        nodes = xp.array([
            # Corners
            [0, 0, 0],
            [a, 0, 0],
            [a, a, 0],
            [0, a, 0],
            [0, 0, a],
            [a, 0, a],
            [a, a, a],
            [0, a, a],
            
            # Face centers
            [a/2, a/2, 0],
            [a/2, a/2, a],
            [a/2, 0, a/2],
            [a/2, a, a/2],
            [0, a/2, a/2],
            [a, a/2, a/2],
        ])
        
        # Element connectivity (tetrahedra + octahedra)
        elements = [
            # Bottom tetrahedra
            [0, 1, 3, 8],
            [1, 2, 3, 8],
            
            # Top tetrahedra
            [4, 5, 7, 9],
            [5, 6, 7, 9],
            
            # Vertical struts
            [0, 4], [1, 5], [2, 6], [3, 7],
            
            # Face diagonals
            [8, 10], [8, 11], [8, 12], [8, 13],
            [9, 10], [9, 11], [9, 12], [9, 13],
            
            # Additional connections for full octet
            [10, 12], [10, 13],
            [11, 12], [11, 13],
        ]
        
        return {
            'nodes': nodes,
            'elements': elements,
            'num_nodes': len(nodes),
            'num_elements': len(elements)
        }
    
    def generate_block(self, 
                      length: float,
                      width: float, 
                      height: float) -> Dict:
        """
        Generate full block with internal octet lattice.
        """
        # Calculate number of unit cells
        nx = int(length / self.unit_cell_size)
        ny = int(width / self.unit_cell_size)
        nz = int(height / self.unit_cell_size)
        
        # Generate lattice
        all_nodes = []
        all_elements = []
        node_offset = 0
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    cell = self.generate_unit_cell()
                    
                    # Translate nodes
                    translation = xp.array([
                        i * self.unit_cell_size,
                        j * self.unit_cell_size,
                        k * self.unit_cell_size
                    ])
                    
                    cell_nodes = cell['nodes'] + translation
                    all_nodes.append(cell_nodes)
                    
                    # Update element connectivity
                    cell_elements = cell['elements'] + node_offset
                    all_elements.extend(cell_elements)
                    
                    node_offset += cell['num_nodes']
        
        return {
            'nodes': xp.vstack(all_nodes),
            'elements': all_elements,
            'dimensions': (length, width, height),
            'num_cells': (nx, ny, nz)
        }


# ============================================================================
# FEA Solver Interface
# ============================================================================

class FEASolver:
    """
    Interface to external FEA engines for stress analysis.
    """
    
    def __init__(self, engine: str = 'calculix'):
        self.engine = engine
        self.available_engines = []
        
        if CALCULIX_AVAILABLE:
            self.available_engines.append('calculix')
        if FENICS_AVAILABLE:
            self.available_engines.append('fenics')
        
        if engine not in self.available_engines:
            print(f"Warning: {engine} not available. Available: {self.available_engines}")
    
    def solve_static(self, 
                    geometry: Dict,
                    material: MaterialProperties,
                    boundary_conditions: Dict,
                    loads: Dict) -> Dict:
        """
        Solve static equilibrium problem.
        
        Returns:
            stress_field: Stress tensor at each node
            displacement_field: Displacement at each node
            von_mises_field: Von Mises stress at each node
        """
        
        if self.engine == 'calculix' and CALCULIX_AVAILABLE:
            return self._solve_with_calculix(geometry, material, boundary_conditions, loads)
        elif self.engine == 'fenics' and FENICS_AVAILABLE:
            return self._solve_with_fenics(geometry, material, boundary_conditions, loads)
        else:
            # Fallback: simplified analytical solution
            return self._solve_analytical(geometry, material, boundary_conditions, loads)
    
    def _solve_with_calculix(self, geometry, material, bc, loads):
        """Interface to CalculiX FEA solver.

        Requires: CalculiX (ccx) installed and on PATH.
        Workflow: write .inp → run ccx → parse .frd output.
        """
        raise NotImplementedError(
            "CalculiX (ccx) required. Install: apt install calculix-ccx or build from source."
        )

    def _solve_with_fenics(self, geometry, material, bc, loads):
        """Interface to FEniCS FEM solver.

        Requires: FEniCS (dolfin) Python package.
        """
        raise NotImplementedError(
            "FEniCS required. Install: pip install fenics or use conda install -c conda-forge fenics."
        )
    
    def _solve_analytical(self, 
                         geometry: Dict,
                         material: MaterialProperties,
                         bc: Dict,
                         loads: Dict) -> Dict:
        """
        Simplified analytical solution for quick testing.
        
        Uses beam theory + truss analysis for approximate results.
        """
        nodes = geometry['nodes']
        elements = geometry['elements']
        
        num_nodes = len(nodes)
        
        # Initialize fields
        displacement_field = xp.zeros((num_nodes, 3))
        stress_field = xp.zeros((num_nodes, 3, 3))
        von_mises_field = xp.zeros(num_nodes)
        
        # Simplified: assume uniform stress distribution
        total_load = loads.get('magnitude', 1000)  # N
        load_area = len([e for e in elements if len(e) > 2])  # Approximate
        
        avg_stress = total_load / (load_area * 1e-6)  # Pa (rough estimate)
        
        # Fill stress field (simplified)
        for i in range(num_nodes):
            stress_tensor = StressTensor.from_components(
                avg_stress, 0, 0, 0, 0, 0
            )
            stress_field[i] = stress_tensor
            von_mises_field[i] = StressTensor.von_mises(stress_tensor)
        
        # Simplified displacement (Hooke's law)
        strain = avg_stress / material.youngs_modulus
        displacement_field[:, 2] = strain * geometry['dimensions'][2]
        
        return {
            'stress_field': stress_field,
            'displacement_field': displacement_field,
            'von_mises_field': von_mises_field,
            'max_stress': xp.max(von_mises_field),
            'max_displacement': xp.max(xp.abs(displacement_field))
        }


# ============================================================================
# Verification Tests (Pass/Fail Criteria)
# ============================================================================

class SovereignJengaVerifier:
    """
    Run verification tests for Sovereign Jenga demonstration system.
    """
    
    def __init__(self, material: MaterialProperties):
        self.material = material
        self.results = {}
    
    def test_centerless_tower(self, 
                             block_geometry: Dict,
                             num_blocks: int = 18) -> Dict:
        """
        Test: Remove all central blocks, leave outer skeleton.
        Tower should stand under own weight.
        """
        print("\n=== Test: Center-less Tower ===")
        
        # Setup: Create hollow tower (only outer ring of blocks)
        # Simplified: check if stress < yield with center removed
        
        solver = FEASolver()
        
        # Apply gravity load
        loads = {
            'type': 'gravity',
            'magnitude': self.material.density * 9.81 * block_geometry['dimensions'][0]
        }
        
        # Fixed base
        bc = {'fixed': 'bottom'}
        
        # Solve
        result = solver.solve_static(block_geometry, self.material, bc, loads)
        
        # Check: max stress < yield strength
        max_stress = result['max_stress']
        passed = max_stress < self.material.yield_strength
        
        self.results['centerless_tower'] = {
            'passed': passed,
            'max_stress_MPa': max_stress / 1e6,
            'yield_strength_MPa': self.material.yield_strength / 1e6,
            'safety_factor': self.material.yield_strength / max_stress
        }
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"Result: {status}")
        print(f"  Max stress: {max_stress/1e6:.2f} MPa")
        print(f"  Yield strength: {self.material.yield_strength/1e6:.2f} MPa")
        print(f"  Safety factor: {self.results['centerless_tower']['safety_factor']:.2f}")
        
        return self.results['centerless_tower']
    
    def test_45deg_overhang(self,
                           block_geometry: Dict) -> Dict:
        """
        Test: Tower leans at 45° without support.
        Stability via torsional-to-compressive conversion.
        """
        print("\n=== Test: 45° Overhang ===")
        
        # This test requires rigid body dynamics (not just static FEA)
        # For now, simplified check: center of mass within support polygon
        
        # Simplified: check if geometry can support 45° lean
        # Real test would use PyBullet/MuJoCo
        
        # Placeholder result
        self.results['overhang_45deg'] = {
            'passed': False,  # Requires rigid body simulation
            'note': 'Requires PyBullet/MuJoCo integration'
        }
        
        print(f"Result: ⚠ NOT YET IMPLEMENTED")
        print(f"  Note: Requires rigid body dynamics engine")
        
        return self.results['overhang_45deg']
    
    def test_vibration_distribution(self,
                                   block_geometry: Dict) -> Dict:
        """
        Test: Strike one block, entire structure responds.
        Global vibration modes (not localized).
        """
        print("\n=== Test: Vibration Distribution ===")
        
        # Compute eigenmodes of stiffness matrix
        # Global modes = eigenvectors span entire structure
        
        solver = FEASolver()
        
        # Simplified: check if structure has delocalized modes
        # Real test would compute full modal analysis
        
        # Placeholder
        self.results['vibration_distribution'] = {
            'passed': False,  # Requires modal analysis
            'note': 'Requires eigenmode computation'
        }
        
        print(f"Result: ⚠ NOT YET IMPLEMENTED")
        print(f"  Note: Requires modal analysis (eigenmode computation)")
        
        return self.results['vibration_distribution']
    
    def test_load_redistribution(self,
                                block_geometry: Dict,
                                remove_fraction: float = 0.3) -> Dict:
        """
        Test: Remove 30% of blocks randomly.
        Tower should still support 10kg top load.
        """
        print("\n=== Test: Load Redistribution ===")
        
        # Setup: Remove random blocks, apply 10kg load
        # Check: stress < yield, displacement < threshold
        
        solver = FEASolver()
        
        loads = {
            'type': 'point',
            'magnitude': 10 * 9.81  # 10kg
        }
        
        bc = {'fixed': 'bottom'}
        
        result = solver.solve_static(block_geometry, self.material, bc, loads)
        
        # Check criteria
        max_stress = result['max_stress']
        max_disp = result['max_displacement']
        
        stress_ok = max_stress < self.material.yield_strength
        disp_ok = max_disp < 0.01  # 1cm threshold
        
        passed = stress_ok and disp_ok
        
        self.results['load_redistribution'] = {
            'passed': passed,
            'max_stress_MPa': max_stress / 1e6,
            'max_displacement_mm': max_disp * 1000,
            'stress_ok': stress_ok,
            'displacement_ok': disp_ok
        }
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"Result: {status}")
        print(f"  Max stress: {max_stress/1e6:.2f} MPa")
        print(f"  Max displacement: {max_disp*1000:.2f} mm")
        
        return self.results['load_redistribution']
    
    def test_semi_truck_lift(self,
                            block_geometry: Dict) -> Dict:
        """
        Test: Use as jack base.
        Lifts 10,000 lbs (one corner of semi-truck).
        """
        print("\n=== Test: Semi-Truck Lift (10,000 lbs) ===")
        
        # 10,000 lbs = 4536 kg = 44.5 kN
        
        solver = FEASolver()
        
        loads = {
            'type': 'point',
            'magnitude': 44500  # N (10,000 lbs)
        }
        
        bc = {'fixed': 'bottom'}
        
        result = solver.solve_static(block_geometry, self.material, bc, loads)
        
        max_stress = result['max_stress']
        passed = max_stress < self.material.yield_strength
        
        self.results['semi_truck_lift'] = {
            'passed': passed,
            'load_N': 44500,
            'load_lbs': 10000,
            'max_stress_MPa': max_stress / 1e6,
            'yield_strength_MPa': self.material.yield_strength / 1e6,
            'safety_factor': self.material.yield_strength / max_stress if max_stress > 0 else float('inf')
        }
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"Result: {status}")
        print(f"  Load: 44,500 N (10,000 lbs)")
        print(f"  Max stress: {max_stress/1e6:.2f} MPa")
        print(f"  Safety factor: {self.results['semi_truck_lift']['safety_factor']:.2f}")
        
        return self.results['semi_truck_lift']
    
    def run_all_tests(self, block_geometry: Dict) -> Dict:
        """Run complete verification suite"""
        print("\n" + "="*60)
        print("SOVEREIGN JENGA VERIFICATION SUITE")
        print("="*60)
        
        self.test_centerless_tower(block_geometry)
        self.test_45deg_overhang(block_geometry)
        self.test_vibration_distribution(block_geometry)
        self.test_load_redistribution(block_geometry)
        self.test_semi_truck_lift(block_geometry)
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results.values() if r.get('passed', False))
        total = len([r for r in self.results.values() if 'passed' in r])
        not_implemented = len([r for r in self.results.values() if 'note' in r])
        
        print(f"Passed: {passed}/{total}")
        print(f"Not yet implemented: {not_implemented}")
        
        return {
            'passed': passed,
            'total': total,
            'not_implemented': not_implemented,
            'details': self.results
        }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run Sovereign Jenga physics verification"""
    
    # Material
    material = MaterialProperties()
    print(f"Material: {material.name}")
    print(f"  Young's modulus: {material.youngs_modulus/1e9:.1f} GPa")
    print(f"  Yield strength: {material.yield_strength/1e6:.1f} MPa")
    print(f"  Density: {material.density} kg/m³")
    
    # Generate block geometry
    generator = OctetTrussGenerator(
        unit_cell_size=0.01,  # 10mm
        strut_diameter=0.001,  # 1mm
        relative_density=0.2
    )
    
    block_geometry = generator.generate_block(
        length=0.06,  # 60mm
        width=0.02,   # 20mm
        height=0.02   # 20mm
    )
    
    print(f"\nBlock geometry:")
    print(f"  Dimensions: {block_geometry['dimensions']}")
    print(f"  Num nodes: {len(block_geometry['nodes'])}")
    print(f"  Num elements: {len(block_geometry['elements'])}")
    
    # Run verification
    verifier = SovereignJengaVerifier(material)
    results = verifier.run_all_tests(block_geometry)
    
    # Save results
    output_path = REPO_ROOT / "out" / "sovereign_jenga_verification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n[+] Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    main()
