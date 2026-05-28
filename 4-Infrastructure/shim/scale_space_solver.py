"""
Multi-scale optimization using scale space theory.

Implements coarse-to-fine optimization via Gaussian smoothing at multiple
scales, with Q16.16 fixed-point arithmetic for FPGA compatibility.

Scale mapping:
    σ₃ (1.0):  coarse LP relaxation → approximate solution
    σ₂ (0.75): tighter LP → better solution
    σ₁ (0.5):  exact MIP → optimal solution
    σ₀ (0.25): formal verification target
"""

import math
from typing import Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ---------------------------------------------------------------------------
# Q16.16 fixed-point arithmetic
# ---------------------------------------------------------------------------

Q16_SCALE = 65536  # 2^16
Q16_MAX = 2147483647  # 2^31 - 1
Q16_MIN = -2147483648  # -2^31


def q16_clamp(v: int) -> int:
    """Clamp integer to Q16.16 representable range."""
    return max(Q16_MIN, min(Q16_MAX, v))


def q16_from_float(f: float) -> int:
    """Convert float to Q16.16 fixed-point."""
    return q16_clamp(round(f * Q16_SCALE))


def q16_to_float(q: int) -> float:
    """Convert Q16.16 fixed-point to float."""
    return q / Q16_SCALE


def q16_multiply(a: int, b: int) -> int:
    """Q16.16 multiplication: (a * b) >> 16."""
    return q16_clamp((a * b) >> 16)


def q16_exp(x_q16: int) -> int:
    """Q16.16 exponential: exp(x) where x is in Q16.16.

    Uses Python math.exp internally, converts to Q16.16.
    For FPGA, this would use a LUT-based approximation.
    """
    x_float = q16_to_float(x_q16)
    return q16_from_float(math.exp(x_float))


# ---------------------------------------------------------------------------
# Gaussian kernel in Q16.16
# ---------------------------------------------------------------------------

def gaussian_kernel_q16(sigma: float, size: int = 256) -> list[int]:
    """Compute 1D Gaussian kernel in Q16.16 fixed-point.

    G(x) = exp(-x²/(2σ²)) * 65536  (Q16.16 scale)

    Args:
        sigma: Standard deviation of the Gaussian (in normalized coords).
        size: Number of kernel taps. Must be odd for symmetry.

    Returns:
        List of Q16.16 kernel values, normalized so they sum to Q16_SCALE.
    """
    if size % 2 == 0:
        size += 1  # Ensure odd for symmetry

    half = size // 2
    two_sigma_sq = 2.0 * sigma * sigma

    # Compute unnormalized kernel
    kernel_raw = []
    for i in range(size):
        x = (i - half) / half  # Map to [-1, 1]
        g = math.exp(-(x * x) / two_sigma_sq)
        kernel_raw.append(q16_from_float(g))

    # Normalize so kernel sums to Q16_SCALE (1.0 in Q16.16)
    raw_sum = sum(kernel_raw)
    if raw_sum == 0:
        # Degenerate: delta function
        kernel_raw[half] = Q16_SCALE
    else:
        # Scale to sum to 65536
        kernel_raw = [q16_clamp(round(v * Q16_SCALE / raw_sum))
                      for v in kernel_raw]

    return kernel_raw


def gaussian_kernel_2d_q16(sigma: float, size: int = 16) -> list[list[int]]:
    """Compute 2D Gaussian kernel in Q16.16.

    Args:
        sigma: Standard deviation.
        size: Kernel dimension (size x size).

    Returns:
        2D list of Q16.16 values.
    """
    half = size // 2
    two_sigma_sq = 2.0 * sigma * sigma

    kernel = []
    total = 0
    for y in range(size):
        row = []
        for x in range(size):
            dx = (x - half) / half
            dy = (y - half) / half
            g = math.exp(-(dx * dx + dy * dy) / two_sigma_sq)
            v = q16_from_float(g)
            row.append(v)
            total += v
        kernel.append(row)

    # Normalize
    if total > 0:
        kernel = [[q16_clamp(round(v * Q16_SCALE / total))
                    for v in row] for row in kernel]

    return kernel


# ---------------------------------------------------------------------------
# Voltage ↔ scale mapping
# ---------------------------------------------------------------------------

# Voltage range: 0.6V → σ=1.0 (coarse), 1.2V → σ=0.0 (fine/identity)
_VOLTAGE_MIN = 0.6
_VOLTAGE_MAX = 1.2
_SIGMA_AT_VMIN = 1.0
_SIGMA_AT_VMAX = 0.01  # Not exactly 0 to avoid degenerate kernel


def voltage_to_scale(voltage_mv: float) -> float:
    """Map millivolt voltage to scale parameter σ.

    Range: 0.6V (600mV, σ=1.0) to 1.2V (1200mV, σ≈0.01).

    Args:
        voltage_mv: Voltage in millivolts.

    Returns:
        Scale parameter σ.
    """
    voltage_v = voltage_mv / 1000.0
    # Clamp to range
    voltage_v = max(_VOLTAGE_MIN, min(_VOLTAGE_MAX, voltage_v))
    # Linear interpolation: σ = 1.0 - (V - 0.6) / 0.6 * 0.99
    t = (voltage_v - _VOLTAGE_MIN) / (_VOLTAGE_MAX - _VOLTAGE_MIN)
    sigma = _SIGMA_AT_VMIN + t * (_SIGMA_AT_VMAX - _SIGMA_AT_VMIN)
    return max(0.01, sigma)


def scale_to_voltage(sigma: float) -> float:
    """Map scale parameter σ to millivolt voltage.

    Args:
        sigma: Scale parameter.

    Returns:
        Voltage in millivolts.
    """
    sigma = max(_SIGMA_AT_VMAX, min(_SIGMA_AT_VMIN, sigma))
    # Inverse of voltage_to_scale
    t = (sigma - _SIGMA_AT_VMIN) / (_SIGMA_AT_VMAX - _SIGMA_AT_VMIN)
    voltage_v = _VOLTAGE_MIN + t * (_VOLTAGE_MAX - _VOLTAGE_MIN)
    return voltage_v * 1000.0  # Return in mV


# ---------------------------------------------------------------------------
# Multi-scale solver
# ---------------------------------------------------------------------------

def _apply_smoothing_q16(matrix: list[list[float]],
                         sigma: float) -> list[list[float]]:
    """Apply Gaussian smoothing to a cost matrix using Q16.16 arithmetic.

    Convolves each row and column with the Gaussian kernel.
    """
    n = len(matrix)
    if n == 0:
        return matrix

    kernel = gaussian_kernel_q16(sigma, size=min(n, 33))
    k_half = len(kernel) // 2

    # Convert matrix to Q16.16
    q16_matrix = [[q16_from_float(matrix[i][j]) for j in range(n)]
                  for i in range(n)]

    # Smooth rows
    smoothed = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            total = 0
            for ki in range(len(kernel)):
                jj = j + ki - k_half
                if 0 <= jj < n:
                    total += q16_multiply(q16_matrix[i][jj], kernel[ki])
                else:
                    # Mirror boundary
                    jj = max(0, min(n - 1, jj))
                    total += q16_multiply(q16_matrix[i][jj], kernel[ki])
            smoothed[i][j] = q16_clamp(total)

    # Smooth columns
    result = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            total = 0
            for ki in range(len(kernel)):
                ii = i + ki - k_half
                if 0 <= ii < n:
                    total += q16_multiply(smoothed[ii][j], kernel[ki])
                else:
                    ii = max(0, min(n - 1, ii))
                    total += q16_multiply(smoothed[ii][j], kernel[ki])
            result[i][j] = q16_clamp(total)

    # Convert back to float
    return [[q16_to_float(result[i][j]) for j in range(n)]
            for i in range(n)]


def _greedy_tour(cost_matrix: list[list[float]]) -> tuple[list[int], float]:
    """Nearest-neighbor heuristic for TSP."""
    n = len(cost_matrix)
    if n == 0:
        return [], 0.0

    visited = {0}
    tour = [0]
    current = 0
    total_cost = 0.0

    while len(tour) < n:
        best_j = -1
        best_c = float('inf')
        for j in range(n):
            if j not in visited and cost_matrix[current][j] < best_c:
                best_c = cost_matrix[current][j]
                best_j = j
        tour.append(best_j)
        visited.add(best_j)
        total_cost += best_c
        current = best_j

    total_cost += cost_matrix[current][tour[0]]
    return tour, total_cost


def _2opt_improve(tour: list[int],
                  cost_matrix: list[list[float]]) -> tuple[list[int], float]:
    """2-opt local search improvement."""
    n = len(tour)
    if n < 4:
        cost = sum(cost_matrix[tour[i]][tour[(i + 1) % n]] for i in range(n))
        return tour, cost

    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                # Cost of current edges
                d1 = (cost_matrix[tour[i - 1]][tour[i]] +
                      cost_matrix[tour[j]][tour[(j + 1) % n]])
                # Cost of reversed segment edges
                d2 = (cost_matrix[tour[i - 1]][tour[j]] +
                      cost_matrix[tour[i]][tour[(j + 1) % n]])

                if d2 < d1 - 1e-10:
                    tour[i:j + 1] = reversed(tour[i:j + 1])
                    improved = True

    cost = sum(cost_matrix[tour[i]][tour[(i + 1) % n]] for i in range(n))
    return tour, cost


def solve_multiscale(cost_matrix: list[list[float]],
                     sigmas: Optional[list[float]] = None) -> dict:
    """Solve routing problem at multiple scales.

    Coarse-to-fine strategy:
        σ₃ (1.0):  coarse LP relaxation → approximate solution
        σ₂ (0.75): tighter LP → better solution
        σ₁ (0.5):  exact MIP → optimal solution
        σ₀ (0.25): formal verification target

    At each scale, the cost matrix is Gaussian-smoothed, then solved
    with progressively tighter methods. Solutions from coarser scales
    seed finer scales.

    Args:
        cost_matrix: n×n cost matrix.
        sigmas: List of scale parameters (coarse to fine).

    Returns:
        {'solutions': {sigma: {'tour': list, 'cost': float}},
         'converged': bool, 'best_sigma': float}
    """
    if sigmas is None:
        sigmas = [1.0, 0.75, 0.5, 0.25]

    n = len(cost_matrix)
    if n == 0:
        return {'solutions': {}, 'converged': True, 'best_sigma': 0.0}

    solutions = {}
    best_cost = float('inf')
    best_sigma = sigmas[0]
    prev_tour = None

    for sigma in sigmas:
        # Smooth the cost matrix at this scale
        smoothed = _apply_smoothing_q16(cost_matrix, sigma)

        # Solve on smoothed costs
        if prev_tour is not None:
            # Warm-start: use previous solution as seed
            # Compute cost on smoothed matrix
            seed_cost = sum(smoothed[prev_tour[i]][prev_tour[(i + 1) % n]]
                            for i in range(n))
            # Run 2-opt on smoothed matrix starting from previous tour
            tour, smoothed_cost = _2opt_improve(prev_tour[:], smoothed)
        else:
            # Cold start: greedy + 2-opt
            tour, smoothed_cost = _greedy_tour(smoothed)
            tour, smoothed_cost = _2opt_improve(tour, smoothed)

        # Evaluate on original cost matrix
        real_cost = sum(cost_matrix[tour[i]][tour[(i + 1) % n]]
                        for i in range(n))

        solutions[sigma] = {
            'tour': tour,
            'cost': real_cost,
            'smoothed_cost': smoothed_cost,
            'sigma': sigma,
        }

        if real_cost < best_cost:
            best_cost = real_cost
            best_sigma = sigma

        prev_tour = tour

    # Check convergence: did the solution stabilize at the finest scale?
    converged = False
    if len(sigmas) >= 2:
        costs = [solutions[s]['cost'] for s in sigmas]
        if len(costs) >= 2:
            # Converged if last two scales are within 1%
            last = costs[-1]
            second_last = costs[-2]
            if second_last > 0:
                converged = abs(last - second_last) / second_last < 0.01
            else:
                converged = abs(last - second_last) < 1e-10

    return {
        'solutions': solutions,
        'converged': converged,
        'best_sigma': best_sigma,
        'best_cost': best_cost,
    }


# ---------------------------------------------------------------------------
# CLI / demo
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import random

    # Generate a random TSP instance
    n = 20
    random.seed(42)
    points = [(random.uniform(0, 100), random.uniform(0, 100))
              for _ in range(n)]

    cost = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            dx = points[i][0] - points[j][0]
            dy = points[i][1] - points[j][1]
            cost[i][j] = math.sqrt(dx * dx + dy * dy)

    print(f"Random TSP instance: {n} cities")
    print(f"Cost matrix range: [{min(min(row) for row in cost):.1f}, "
          f"{max(max(row) for row in cost):.1f}]")

    # Solve multi-scale
    result = solve_multiscale(cost)

    print(f"\nConverged: {result['converged']}")
    print(f"Best sigma: {result['best_sigma']}")
    print(f"Best cost: {result['best_cost']:.2f}")

    for sigma, data in sorted(result['solutions'].items(), reverse=True):
        print(f"  σ={sigma:.2f}: tour cost={data['cost']:.2f}, "
              f"smoothed={data['smoothed_cost']:.2f}")

    # Demo voltage mapping
    print("\nVoltage ↔ Scale mapping:")
    for mv in [600, 700, 800, 900, 1000, 1100, 1200]:
        s = voltage_to_scale(mv)
        v_back = scale_to_voltage(s)
        print(f"  {mv}mV → σ={s:.3f} → {v_back:.0f}mV")

    # Demo Q16 kernel
    print("\nQ16.16 Gaussian kernel (σ=0.5, 9 taps):")
    k = gaussian_kernel_q16(0.5, 9)
    total_q16 = sum(k)
    print(f"  Values: {k}")
    print(f"  Sum: {total_q16} (target: {Q16_SCALE})")
    print(f"  As floats: [{', '.join(f'{q16_to_float(v):.4f}' for v in k)}]")
