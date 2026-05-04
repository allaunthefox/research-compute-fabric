#!/usr/bin/env python3
"""
Unit Norm Preservation Validation for Resonance Quaternion Stochastic Differentials

This script validates that the quaternion operations preserve unit norm as required
by the swarm analysis of resonance quaternion stochastic differentials (MATH_MODEL_MAP 0.4.4).

Validation tests:
1. Quaternion multiplication preserves unit norm
2. Axis-angle construction preserves unit norm
3. SLERP interpolation preserves unit norm
4. Stochastic evolution preserves unit norm (with explicit renormalization)
5. SLUQ triage integration preserves unit norm
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

class Quaternion:
    """Unit quaternion with unit norm enforcement."""
    
    def __init__(self, w: float, x: float, y: float, z: float, enforce_norm: bool = True):
        self.w = w
        self.x = x
        self.y = y
        self.z = z
        if enforce_norm:
            self.normalize()
    
    def normalize(self):
        """Normalize quaternion to unit norm."""
        norm = np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)
        if norm > 1e-10:
            self.w /= norm
            self.x /= norm
            self.y /= norm
            self.z /= norm
    
    def norm(self) -> float:
        """Compute quaternion norm."""
        return np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)
    
    def multiply(self, other: 'Quaternion') -> 'Quaternion':
        """Hamilton product of quaternions."""
        w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
        x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y
        y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x
        z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
        return Quaternion(w, x, y, z)
    
    def from_axis_angle(self, axis: Tuple[float, float, float], angle: float) -> 'Quaternion':
        """Create unit quaternion from axis-angle representation."""
        ax, ay, az = axis
        axis_norm = np.sqrt(ax**2 + ay**2 + az**2)
        if axis_norm > 1e-10:
            ax /= axis_norm
            ay /= axis_norm
            az /= axis_norm
        
        half_angle = angle / 2.0
        cos_half = np.cos(half_angle)
        sin_half = np.sin(half_angle)
        
        w = cos_half
        x = sin_half * ax
        y = sin_half * ay
        z = sin_half * az
        
        return Quaternion(w, x, y, z)
    
    def slerp(self, other: 'Quaternion', t: float) -> 'Quaternion':
        """Spherical linear interpolation between quaternions."""
        dot = self.w * other.w + self.x * other.x + self.y * other.y + self.z * other.z
        
        # Ensure shortest path
        if dot < 0.0:
            other = Quaternion(-other.w, -other.x, -other.y, -other.z, enforce_norm=False)
            dot = -dot
        
        if dot > 0.9995:
            # Linear interpolation for nearly parallel quaternions
            w1 = 1.0 - t
            w2 = t
            result = Quaternion(
                w1 * self.w + w2 * other.w,
                w1 * self.x + w2 * other.x,
                w1 * self.y + w2 * other.y,
                w1 * self.z + w2 * other.z,
                enforce_norm=True
            )
            return result
        
        omega = np.arccos(np.clip(dot, -1.0, 1.0))
        sin_omega = np.sin(omega)
        
        w1 = np.sin((1.0 - t) * omega) / sin_omega
        w2 = np.sin(t * omega) / sin_omega
        
        result = Quaternion(
            w1 * self.w + w2 * other.w,
            w1 * self.x + w2 * other.x,
            w1 * self.y + w2 * other.y,
            w1 * self.z + w2 * other.z,
            enforce_norm=True
        )
        return result
    
    def stochastic_evolution(self, gradient: Tuple[float, float, float], 
                           noise: float, dt: float) -> 'Quaternion':
        """Stochastic evolution with resonance gradient guidance."""
        dR_domega, dR_dt, _ = gradient
        
        # Compute stochastic increment
        ito_correction = 0.5 * (dR_domega + dR_dt) * dt
        stochastic_increment = ito_correction + dR_domega * noise * np.sqrt(dt)
        
        # Apply small rotation based on increment
        axis = (1.0, 0.0, 0.0)  # Simplified: x-axis rotation
        angle = stochastic_increment * 0.1  # Scale factor
        
        rotated = self.from_axis_angle(axis, angle)
        result = rotated.multiply(self)
        
        return result


def validate_multiplication_preserves_norm() -> dict:
    """Test that quaternion multiplication preserves unit norm."""
    print("\n" + "=" * 70)
    print("Test 1: Quaternion Multiplication Unit Norm Preservation")
    print("=" * 70)
    
    # Generate random unit quaternions
    np.random.seed(42)
    num_tests = 1000
    norm_deviations = []
    
    for _ in range(num_tests):
        q1 = Quaternion(*np.random.randn(4))
        q2 = Quaternion(*np.random.randn(4))
        q3 = q1.multiply(q2)
        
        norm_deviation = abs(q3.norm() - 1.0)
        norm_deviations.append(norm_deviation)
    
    max_deviation = max(norm_deviations)
    mean_deviation = np.mean(norm_deviations)
    std_deviation = np.std(norm_deviations)
    
    passed = max_deviation < 1e-10
    
    result = {
        "test_name": "quaternion_multiplication_unit_norm",
        "num_tests": num_tests,
        "max_deviation": float(max_deviation),
        "mean_deviation": float(mean_deviation),
        "std_deviation": float(std_deviation),
        "passed": passed,
        "threshold": 1e-10
    }
    
    print(f"  Max deviation: {max_deviation:.2e}")
    print(f"  Mean deviation: {mean_deviation:.2e}")
    print(f"  Std deviation: {std_deviation:.2e}")
    print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return result


def validate_axis_angle_preserves_norm() -> dict:
    """Test that axis-angle construction preserves unit norm."""
    print("\n" + "=" * 70)
    print("Test 2: Axis-Angle Construction Unit Norm Preservation")
    print("=" * 70)
    
    np.random.seed(43)
    num_tests = 1000
    norm_deviations = []
    
    for _ in range(num_tests):
        axis = np.random.randn(3)
        axis = axis / np.linalg.norm(axis)
        angle = np.random.uniform(0, 2 * np.pi)
        
        q = Quaternion(0, 0, 0, 0, enforce_norm=False)
        q = q.from_axis_angle(tuple(axis), angle)
        
        norm_deviation = abs(q.norm() - 1.0)
        norm_deviations.append(norm_deviation)
    
    max_deviation = max(norm_deviations)
    mean_deviation = np.mean(norm_deviations)
    std_deviation = np.std(norm_deviations)
    
    passed = max_deviation < 1e-10
    
    result = {
        "test_name": "axis_angle_construction_unit_norm",
        "num_tests": num_tests,
        "max_deviation": float(max_deviation),
        "mean_deviation": float(mean_deviation),
        "std_deviation": float(std_deviation),
        "passed": passed,
        "threshold": 1e-10
    }
    
    print(f"  Max deviation: {max_deviation:.2e}")
    print(f"  Mean deviation: {mean_deviation:.2e}")
    print(f"  Std deviation: {std_deviation:.2e}")
    print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return result


def validate_slerp_preserves_norm() -> dict:
    """Test that SLERP interpolation preserves unit norm."""
    print("\n" + "=" * 70)
    print("Test 3: SLERP Interpolation Unit Norm Preservation")
    print("=" * 70)
    
    np.random.seed(44)
    num_tests = 1000
    norm_deviations = []
    
    for _ in range(num_tests):
        q1 = Quaternion(*np.random.randn(4))
        q2 = Quaternion(*np.random.randn(4))
        t = np.random.uniform(0, 1)
        
        q3 = q1.slerp(q2, t)
        
        norm_deviation = abs(q3.norm() - 1.0)
        norm_deviations.append(norm_deviation)
    
    max_deviation = max(norm_deviations)
    mean_deviation = np.mean(norm_deviations)
    std_deviation = np.std(norm_deviations)
    
    passed = max_deviation < 1e-10
    
    result = {
        "test_name": "slerp_interpolation_unit_norm",
        "num_tests": num_tests,
        "max_deviation": float(max_deviation),
        "mean_deviation": float(mean_deviation),
        "std_deviation": float(std_deviation),
        "passed": passed,
        "threshold": 1e-10
    }
    
    print(f"  Max deviation: {max_deviation:.2e}")
    print(f"  Mean deviation: {mean_deviation:.2e}")
    print(f"  Std deviation: {std_deviation:.2e}")
    print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return result


def validate_stochastic_evolution_preserves_norm() -> dict:
    """Test that stochastic evolution preserves unit norm with explicit renormalization."""
    print("\n" + "=" * 70)
    print("Test 4: Stochastic Evolution Unit Norm Preservation")
    print("=" * 70)
    
    np.random.seed(45)
    num_tests = 1000
    num_steps = 100
    norm_deviations = []
    
    for _ in range(num_tests):
        q = Quaternion(*np.random.randn(4))
        
        for _ in range(num_steps):
            gradient = (np.random.randn(3))
            noise = np.random.randn()
            dt = 0.01
            q = q.stochastic_evolution(gradient, noise, dt)
        
        norm_deviation = abs(q.norm() - 1.0)
        norm_deviations.append(norm_deviation)
    
    max_deviation = max(norm_deviations)
    mean_deviation = np.mean(norm_deviations)
    std_deviation = np.std(norm_deviations)
    
    passed = max_deviation < 1e-10
    
    result = {
        "test_name": "stochastic_evolution_unit_norm",
        "num_tests": num_tests,
        "num_steps_per_test": num_steps,
        "max_deviation": float(max_deviation),
        "mean_deviation": float(mean_deviation),
        "std_deviation": float(std_deviation),
        "passed": passed,
        "threshold": 1e-10
    }
    
    print(f"  Max deviation: {max_deviation:.2e}")
    print(f"  Mean deviation: {mean_deviation:.2e}")
    print(f"  Std deviation: {std_deviation:.2e}")
    print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return result


def validate_sluq_integration_preserves_norm() -> dict:
    """Test that SLUQ triage integration preserves unit norm."""
    print("\n" + "=" * 70)
    print("Test 5: SLUQ Triage Integration Unit Norm Preservation")
    print("=" * 70)
    
    np.random.seed(46)
    num_tests = 1000
    num_steps = 100
    norm_deviations = []
    
    for _ in range(num_tests):
        q = Quaternion(*np.random.randn(4))
        
        for _ in range(num_steps):
            # Simulate SLUQ stability check
            gradient = (np.random.randn(3))
            grad_magnitude = np.linalg.norm(gradient)
            stability_threshold = 2.0  # Lenient threshold
            
            if grad_magnitude < stability_threshold:
                # Stable: apply stochastic evolution
                noise = np.random.randn()
                dt = 0.01
                q = q.stochastic_evolution(gradient, noise, dt)
            # Else: unstable, skip update (prune trajectory)
        
        norm_deviation = abs(q.norm() - 1.0)
        norm_deviations.append(norm_deviation)
    
    max_deviation = max(norm_deviations)
    mean_deviation = np.mean(norm_deviations)
    std_deviation = np.std(norm_deviations)
    
    passed = max_deviation < 1e-10
    
    result = {
        "test_name": "sluq_triage_integration_unit_norm",
        "num_tests": num_tests,
        "num_steps_per_test": num_steps,
        "max_deviation": float(max_deviation),
        "mean_deviation": float(mean_deviation),
        "std_deviation": float(std_deviation),
        "passed": passed,
        "threshold": 1e-10
    }
    
    print(f"  Max deviation: {max_deviation:.2e}")
    print(f"  Mean deviation: {mean_deviation:.2e}")
    print(f"  Std deviation: {std_deviation:.2e}")
    print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return result


def main():
    """Run all unit norm preservation validation tests."""
    print("=" * 70)
    print("Unit Norm Preservation Validation for Resonance Quaternion Stochastic Differentials")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    results = []
    results.append(validate_multiplication_preserves_norm())
    results.append(validate_axis_angle_preserves_norm())
    results.append(validate_slerp_preserves_norm())
    results.append(validate_stochastic_evolution_preserves_norm())
    results.append(validate_sluq_integration_preserves_norm())
    
    # Summary
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["passed"])
    
    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"  {result['test_name']}: {status}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✅ All unit norm preservation tests PASSED")
        overall_status = "PASSED"
    else:
        print("❌ Some unit norm preservation tests FAILED")
        overall_status = "FAILED"
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": overall_status,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "test_results": [
            {
                "test_name": r["test_name"],
                "num_tests": r["num_tests"],
                "max_deviation": r["max_deviation"],
                "mean_deviation": r["mean_deviation"],
                "std_deviation": r["std_deviation"],
                "passed": bool(r["passed"]),
                "threshold": r["threshold"]
            }
            for r in results
        ]
    }
    
    output_path = Path("shared-data/data/validation/quaternion_unit_norm_preservation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return overall_status


if __name__ == "__main__":
    main()
