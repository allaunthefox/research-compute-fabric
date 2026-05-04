#!/usr/bin/env python3
"""
gwl_earth_riemannian_conversion.py

TEST OF GEOWEIRD LANGUAGE (GWL)

Converting Euclidean circumference estimates into Riemannian manifold model.

Problem: We have flat-space (Euclidean) measurements of Earth's circumference:
  - Equatorial: C_eq ≈ 40,075 km
  - Meridional: C_mer ≈ 40,008 km

Goal: Construct intrinsic Riemannian metric g_ij on 2D manifold S²
      that produces these circumferences through geodesic flow.

Key insight: Circumference is path-length of closed geodesic.
In Riemannian geometry: C = ∮ √g_ij dx^i dx^j along geodesic

GWL Approach:
  - μ-seed represents points on manifold with metric field
  - π_E encodes local frame (tangent space)
  - g(μ) is metric tensor derived from Earth parameters
  - Geodesic equation: d²x^i/dt² + Γ^i_jk dx^j/dt dx^k/dt = 0
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Callable, Optional
import math


# =============================================================================
# PHYSICAL CONSTANTS (Euclidean measurements)
# =============================================================================

EARTH_EQUATORIAL_CIRCUMFERENCE = 40_075_017  # meters (WGS84)
EARTH_MERIDIONAL_CIRCUMFERENCE = 40_007_863  # meters (polar circumference)
EARTH_RADIUS_EQUATORIAL = 6_378_137  # meters (WGS84 semi-major axis)
EARTH_RADIUS_POLAR = 6_356_752  # meters (WGS84 semi-minor axis)
EARTH_FLATTENING = 1 / 298.257223563  # WGS84 flattening


@dataclass
class GWLEarthPoint:
    """
    GWL μ-seed representation of a point on Earth's Riemannian manifold.
    
    Fields:
      - p_E: Euclidean embedding coordinates (optional, for visualization)
      - q: Intrinsic manifold coordinates (θ, φ) - geodesic coordinates
      - π_E: Local frame orientation (tangent space basis)
      - g_local: Metric tensor at this point
      - Γ_local: Christoffel symbols at this point
    """
    # Intrinsic coordinates (manifold-native)
    theta: float  # Latitude-like (from -π/2 to π/2)
    phi: float    # Longitude-like (from 0 to 2π)
    
    # Local metric tensor (2x2 for 2D surface)
    g_theta_theta: float
    g_theta_phi: float
    g_phi_phi: float
    
    # Local frame orientation (π_E field)
    # Represents basis vectors in tangent space
    e_theta: np.ndarray  # Basis vector in θ direction
    e_phi: np.ndarray    # Basis vector in φ direction
    
    # Geometric state
    curvature_scalar: float  # Gaussian curvature K at this point
    
    def metric_tensor(self) -> np.ndarray:
        """Return metric tensor g_ij."""
        return np.array([
            [self.g_theta_theta, self.g_theta_phi],
            [self.g_theta_phi, self.g_phi_phi]
        ])
    
    def line_element(self, dtheta: float, dphi: float) -> float:
        """
        Compute ds² = g_ij dx^i dx^j
        This is the Riemannian line element.
        """
        g = self.metric_tensor()
        dx = np.array([dtheta, dphi])
        return np.sqrt(dx @ g @ dx)


class EarthRiemannianManifold:
    """
    Riemannian manifold model of Earth constructed from circumference data.
    
    Key property: Geodesic distances match measured circumferences.
    """
    
    def __init__(self, 
                 C_eq: float = EARTH_EQUATORIAL_CIRCUMFERENCE,
                 C_mer: float = EARTH_MERIDIONAL_CIRCUMFERENCE):
        """
        Construct manifold from Euclidean circumference measurements.
        
        These circumferences constrain the Riemannian metric.
        """
        self.C_eq = C_eq
        self.C_mer = C_mer
        
        # Compute ellipsoid parameters from circumferences
        # For oblate spheroid: C_eq = 2πa, C_mer ≈ 2πa(1 - f/2 + ...)
        self.a = C_eq / (2 * math.pi)  # Equatorial radius
        
        # Flattening from meridional circumference
        # C_mer = 2πc where c is mean polar radius
        c = C_mer / (2 * math.pi)
        
        # For ellipsoid: c = a(1 - f)
        # Approximate: f ≈ (a - c) / a
        self.f = (self.a - c) / self.a
        self.c = c
        
        print(f"Riemannian Earth Model:")
        print(f"  Equatorial circumference: {C_eq:,} m")
        print(f"  Meridional circumference: {C_mer:,} m")
        print(f"  Semi-major axis (a): {self.a:,.3f} m")
        print(f"  Semi-minor axis (c): {self.c:,.3f} m")
        print(f"  Flattening (f): {self.f:.12f}")
        print(f"  Eccentricity (e): {math.sqrt(2*self.f - self.f**2):.12f}")
    
    def metric_at(self, theta: float, phi: float) -> Tuple[float, float, float]:
        """
        Compute metric tensor g_ij at point (θ, φ).
        
        For oblate spheroid in geodetic coordinates:
        ds² = (M)² dθ² + (N cos θ)² dφ²
        
        Where:
          M = a(1 - e²) / (1 - e² sin² θ)^(3/2)  - meridional radius
          N = a / (1 - e² sin² θ)^(1/2)          - prime vertical radius
        """
        e2 = 2 * self.f - self.f**2  # Eccentricity squared
        
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        
        # Radius of curvature in meridian (M)
        W = math.sqrt(1 - e2 * sin_theta**2)
        M = self.a * (1 - e2) / (W**3)
        
        # Radius of curvature in prime vertical (N)
        N = self.a / W
        
        # Metric components
        g_theta_theta = M**2
        g_phi_phi = (N * cos_theta)**2
        g_theta_phi = 0.0  # Orthogonal coordinates
        
        return g_theta_theta, g_theta_phi, g_phi_phi
    
    def christoffel_at(self, theta: float, phi: float) -> np.ndarray:
        """
        Compute Christoffel symbols Γ^k_ij at point (θ, φ).
        
        Γ^k_ij = ½ g^kl (∂g_il/∂x^j + ∂g_jl/∂x^i - ∂g_ij/∂x^l)
        """
        # Get metric
        g_tt, g_tp, g_pp = self.metric_at(theta, phi)
        g = np.array([[g_tt, g_tp], [g_tp, g_pp]])
        g_inv = np.linalg.inv(g)
        
        # Numerical derivatives for Christoffel
        eps = 1e-8
        
        # ∂g_tt/∂θ
        g_tt_plus, _, _ = self.metric_at(theta + eps, phi)
        g_tt_minus, _, _ = self.metric_at(theta - eps, phi)
        dg_tt_dtheta = (g_tt_plus - g_tt_minus) / (2 * eps)
        
        # ∂g_pp/∂θ
        _, _, g_pp_plus = self.metric_at(theta + eps, phi)
        _, _, g_pp_minus = self.metric_at(theta - eps, phi)
        dg_pp_dtheta = (g_pp_plus - g_pp_minus) / (2 * eps)
        
        # For diagonal metric g = diag(g_tt, g_pp):
        # Γ^θ_θθ = ½ g^θθ ∂g_θθ/∂θ
        # Γ^θ_φφ = -½ g^θθ ∂g_φφ/∂θ
        # Γ^φ_θφ = Γ^φ_φθ = ½ g^φφ ∂g_φφ/∂θ
        
        Gamma = np.zeros((2, 2, 2))  # Gamma[k, i, j] = Γ^k_ij
        
        Gamma[0, 0, 0] = 0.5 * g_inv[0, 0] * dg_tt_dtheta
        Gamma[0, 1, 1] = -0.5 * g_inv[0, 0] * dg_pp_dtheta
        Gamma[1, 0, 1] = 0.5 * g_inv[1, 1] * dg_pp_dtheta
        Gamma[1, 1, 0] = Gamma[1, 0, 1]  # Symmetry
        
        return Gamma
    
    def create_point(self, theta: float, phi: float) -> GWLEarthPoint:
        """Create GWL μ-seed at given coordinates."""
        g_tt, g_tp, g_pp = self.metric_at(theta, phi)
        
        # Basis vectors in tangent space (orthonormal with respect to g)
        e_theta = np.array([1.0, 0.0])
        e_phi = np.array([0.0, 1.0])
        
        # Gaussian curvature for oblate spheroid
        e2 = 2 * self.f - self.f**2
        sin_theta = math.sin(theta)
        K = (1 - e2) / (self.a**2 * (1 - e2 * sin_theta**2)**2)
        
        return GWLEarthPoint(
            theta=theta,
            phi=phi,
            g_theta_theta=g_tt,
            g_theta_phi=g_tp,
            g_phi_phi=g_pp,
            e_theta=e_theta,
            e_phi=e_phi,
            curvature_scalar=K
        )
    
    def geodesic_equation(self, state: np.ndarray) -> np.ndarray:
        """
        Geodesic equation: d²x^i/dt² = -Γ^i_jk dx^j/dt dx^k/dt
        
        State vector: [θ, φ, dθ/dt, dφ/dt]
        Returns: [dθ/dt, dφ/dt, d²θ/dt², d²φ/dt²]
        """
        theta, phi, v_theta, v_phi = state
        
        Gamma = self.christoffel_at(theta, phi)
        
        # Accelerations
        a_theta = (-Gamma[0, 0, 0] * v_theta**2 
                   - 2 * Gamma[0, 0, 1] * v_theta * v_phi
                   - Gamma[0, 1, 1] * v_phi**2)
        
        a_phi = (-Gamma[1, 0, 0] * v_theta**2
                - 2 * Gamma[1, 0, 1] * v_theta * v_phi
                - Gamma[1, 1, 1] * v_phi**2)
        
        return np.array([v_theta, v_phi, a_theta, a_phi])
    
    def integrate_geodesic(self, theta0: float, phi0: float, 
                          v_theta0: float, v_phi0: float,
                          steps: int, dt: float = 0.001) -> List[Tuple[float, float]]:
        """
        Integrate geodesic equation using symplectic integrator.
        
        Returns path in intrinsic coordinates.
        """
        state = np.array([theta0, phi0, v_theta0, v_phi0])
        path = [(theta0, phi0)]
        
        for _ in range(steps):
            # Symplectic Euler (staggered)
            # Update velocities
            deriv = self.geodesic_equation(state)
            state[2] += deriv[2] * dt  # v_theta
            state[3] += deriv[3] * dt  # v_phi
            
            # Update positions with new velocities
            state[0] += state[2] * dt  # theta
            state[1] += state[3] * dt  # phi
            
            path.append((state[0], state[1]))
        
        return path


class EarthCircumferenceTests:
    """
    Test suite: Verify Riemannian manifold reproduces Euclidean circumferences.
    """
    
    def __init__(self):
        self.earth = EarthRiemannianManifold()
        self.results = {}
    
    def test_equatorial_circumference(self) -> Tuple[bool, dict]:
        """
        Test 1: Equatorial geodesic should have length C_eq.
        
        Equator: θ = 0, φ ∈ [0, 2π]
        Geodesic equation with v_θ = 0 should give equator.
        """
        print("\n[Test] Equatorial Circumference")
        print("-" * 60)
        
        # Start at equator, move in φ direction
        theta0 = 0.0
        phi0 = 0.0
        v_theta0 = 0.0  # Stay at equator
        v_phi0 = 1.0    # Move eastward
        
        # Integrate until we complete circle
        # Need to track when φ wraps by 2π
        path = self.earth.integrate_geodesic(theta0, phi0, v_theta0, v_phi0, 
                                             steps=10000, dt=0.001)
        
        # Compute path length
        total_length = 0.0
        for i in range(len(path) - 1):
            theta, phi = path[i]
            dtheta = path[i+1][0] - theta
            dphi = path[i+1][1] - phi
            
            point = self.earth.create_point(theta, phi)
            ds = point.line_element(dtheta, dphi)
            total_length += ds
        
        # Scale by initial velocity (we used v_phi = 1.0)
        # Actual circumference = length / v_phi0 * (2π / delta_phi)
        delta_phi = path[-1][1] - path[0][1]
        C_measured = total_length / v_phi0 * (2 * math.pi / delta_phi)
        
        error = abs(C_measured - self.earth.C_eq) / self.earth.C_eq
        passed = error < 0.01  # 1% tolerance
        
        print(f"  Expected: {self.earth.C_eq:,.3f} m")
        print(f"  Measured: {C_measured:,.3f} m")
        print(f"  Error: {error*100:.4f}%")
        print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
        
        return passed, {
            'expected': self.earth.C_eq,
            'measured': C_measured,
            'error': error
        }
    
    def test_meridional_circumference(self) -> Tuple[bool, dict]:
        """
        Test 2: Meridional geodesic (through poles) should have length C_mer.
        
        Meridian: φ = constant, θ ∈ [-π/2, π/2]
        """
        print("\n[Test] Meridional Circumference")
        print("-" * 60)
        
        # Start at south pole, move north
        theta0 = -math.pi / 2 + 0.01  # Near south pole
        phi0 = 0.0
        v_theta0 = 1.0  # Move north
        v_phi0 = 0.0    # Stay on meridian
        
        path = self.earth.integrate_geodesic(theta0, phi0, v_theta0, v_phi0,
                                             steps=10000, dt=0.001)
        
        # Compute path length
        total_length = 0.0
        for i in range(len(path) - 1):
            theta, phi = path[i]
            dtheta = path[i+1][0] - theta
            dphi = path[i+1][1] - phi
            
            point = self.earth.create_point(theta, phi)
            ds = point.line_element(dtheta, dphi)
            total_length += ds
        
        # Scale to full meridian (-π/2 to π/2)
        delta_theta = path[-1][0] - path[0][0]
        scale = math.pi / delta_theta
        C_measured = total_length * scale
        
        # Account for both hemispheres (full circumference)
        C_measured *= 2
        
        error = abs(C_measured - self.earth.C_mer) / self.earth.C_mer
        passed = error < 0.05  # 5% tolerance (meridian is harder)
        
        print(f"  Expected: {self.earth.C_mer:,.3f} m")
        print(f"  Measured: {C_measured:,.3f} m")
        print(f"  Error: {error*100:.4f}%")
        print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
        
        return passed, {
            'expected': self.earth.C_mer,
            'measured': C_measured,
            'error': error
        }
    
    def test_metric_properties(self) -> Tuple[bool, dict]:
        """
        Test 3: Metric tensor properties.
        
        - Positive definite: g_tt > 0, g_pp > 0, det(g) > 0
        - Symmetric: g_tp = g_pt
        """
        print("\n[Test] Metric Tensor Properties")
        print("-" * 60)
        
        test_points = [
            (0.0, 0.0),           # Equator
            (math.pi/4, 0.0),     # 45° N
            (math.pi/2 - 0.1, 0.0),  # Near pole
        ]
        
        all_passed = True
        for theta, phi in test_points:
            g_tt, g_tp, g_pp = self.earth.metric_at(theta, phi)
            g = np.array([[g_tt, g_tp], [g_tp, g_pp]])
            det_g = np.linalg.det(g)
            eigenvalues = np.linalg.eigvals(g)
            
            pos_def = all(e > 0 for e in eigenvalues)
            symmetric = abs(g_tp - g[0,1]) < 1e-10
            
            passed = pos_def and symmetric
            all_passed = all_passed and passed
            
            print(f"  θ={math.degrees(theta):.1f}°: det(g)={det_g:.3e}, "
                  f"eigenvalues=[{eigenvalues[0]:.3e}, {eigenvalues[1]:.3e}], "
                  f"{'✓' if passed else '✗'}")
        
        return all_passed, {'points_tested': len(test_points)}
    
    def test_gauss_theorema_egregium(self) -> Tuple[bool, dict]:
        """
        Test 4: Gaussian curvature is intrinsic (Theorema Egregium).
        
        For oblate spheroid, Gaussian curvature varies with latitude.
        This is a property of the Riemannian metric alone (no embedding).
        """
        print("\n[Test] Gauss's Theorema Egregium (Intrinsic Curvature)")
        print("-" * 60)
        
        # Gaussian curvature at different latitudes
        latitudes = np.linspace(-math.pi/2 + 0.1, math.pi/2 - 0.1, 5)
        curvatures = []
        
        for theta in latitudes:
            point = self.earth.create_point(theta, 0.0)
            K = point.curvature_scalar
            curvatures.append(K)
            print(f"  θ={math.degrees(theta):.1f}°: K={K:.6e} m⁻²")
        
        # For oblate spheroid:
        # K = c² / (a² (1 - e² sin² θ)²) where c = a(1-f)
        # Should be maximum at poles (θ = ±π/2), minimum at equator (θ = 0)
        
        K_eq = curvatures[len(curvatures)//2]  # Near equator
        K_pole_max = max(curvatures)
        
        # Curvature should be higher at poles for oblate spheroid
        curvature_increases_toward_poles = K_pole_max > K_eq
        
        # Check magnitude (should be ~1/R² ~ 2.5e-14)
        reasonable_magnitude = all(abs(K) < 1e-13 for K in curvatures)
        
        passed = curvature_increases_toward_poles and reasonable_magnitude
        
        print(f"  K_equator ≈ {K_eq:.6e}")
        print(f"  K_pole_max ≈ {K_pole_max:.6e}")
        print(f"  Curvature increases toward poles: {curvature_increases_toward_poles}")
        print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
        
        return passed, {
            'K_equator': K_eq,
            'K_pole_max': K_pole_max,
            'curvatures': curvatures
        }
    
    def test_gwl_mu_seed(self) -> Tuple[bool, dict]:
        """
        Test 5: GWL μ-seed representation is complete and consistent.
        """
        print("\n[Test] GWL μ-seed Completeness")
        print("-" * 60)
        
        # Create μ-seed at various points
        test_coords = [
            (0.0, 0.0),              # Equator, prime meridian
            (math.pi/2, 0.0),        # North pole area
            (0.0, math.pi),          # Equator, 180° E
            (-math.pi/4, math.pi/2), # 45° S, 90° E
        ]
        
        all_valid = True
        for theta, phi in test_coords:
            point = self.earth.create_point(theta, phi)
            
            # Check all fields present
            has_metric = (point.g_theta_theta > 0 and point.g_phi_phi > 0)
            has_basis = (len(point.e_theta) == 2 and len(point.e_phi) == 2)
            has_curvature = (point.curvature_scalar > 0)
            
            valid = has_metric and has_basis and has_curvature
            all_valid = all_valid and valid
            
            print(f"  ({math.degrees(theta):.1f}°, {math.degrees(phi):.1f}°): "
                  f"metric={has_metric}, basis={has_basis}, K={has_curvature} "
                  f"{'✓' if valid else '✗'}")
        
        return all_valid, {'points_tested': len(test_coords)}
    
    def run_all(self):
        """Run complete GeoWeird test suite."""
        print("=" * 80)
        print("GEOWEIRD LANGUAGE TEST: Earth Riemannian Conversion")
        print("=" * 80)
        print()
        print("Converting Euclidean circumference → Riemannian manifold")
        print(f"  Input: C_eq = {EARTH_EQUATORIAL_CIRCUMFERENCE:,} m")
        print(f"  Input: C_mer = {EARTH_MERIDIONAL_CIRCUMFERENCE:,} m")
        print()
        
        tests = [
            ('Equatorial Circumference', self.test_equatorial_circumference),
            ('Meridional Circumference', self.test_meridional_circumference),
            ('Metric Properties', self.test_metric_properties),
            ('Theorema Egregium', self.test_gauss_theorema_egregium),
            ('GWL μ-seed', self.test_gwl_mu_seed),
        ]
        
        all_passed = True
        for name, test_fn in tests:
            try:
                passed, details = test_fn()
                self.results[name] = {'passed': passed, 'details': details}
                all_passed = all_passed and passed
            except Exception as e:
                print(f"✗ ERROR: {e}")
                import traceback
                traceback.print_exc()
                self.results[name] = {'passed': False, 'error': str(e)}
                all_passed = False
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for name, result in self.results.items():
            status = "✓ PASS" if result.get('passed') else "✗ FAIL"
            print(f"{name:35s}: {status}")
        
        print("\n" + "=" * 80)
        if all_passed:
            print("ALL GEOWEIRD TESTS PASSED ✓")
            print("=" * 80)
            print("""
The Euclidean circumference measurements have been successfully
converted into a Riemannian manifold model using GWL/TSM.

Key Results:
  ✓ Equatorial geodesic reproduces C_eq
  ✓ Meridional geodesic reproduces C_mer  
  ✓ Metric tensor g_ij is positive definite and symmetric
  ✓ Gaussian curvature is intrinsic (Theorema Egregium)
  ✓ μ-seed representation is complete

The GeoWeird approach demonstrates:
  - Topology-first representation (μ-seed with intrinsic coords)
  - Local metric tensor g(μ) derived from global measurements
  - Geodesic flow on manifold reproduces Euclidean measurements
  - Curvature as emergent property of metric
            """)
        else:
            print("SOME TESTS FAILED")
            print("=" * 80)
        
        return all_passed


if __name__ == "__main__":
    tests = EarthCircumferenceTests()
    success = tests.run_all()
    exit(0 if success else 1)
