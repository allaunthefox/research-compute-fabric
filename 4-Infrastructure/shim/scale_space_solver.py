"""
Multi-scale optimization using scale space theory.

Implements coarse-to-fine optimization via cluster-based route optimization
at multiple scales, with Q16.16 fixed-point arithmetic for FPGA compatibility.

Scale mapping:
    σ₃ (1.0):  coarse — merge nearby nodes, solve small problem
    σ₂ (0.75): medium — tighter clustering
    σ₁ (0.5):  fine — minimal clustering, warm-started
    σ₀ (0.25): formal verification target — full problem, 2-opt polish

The Gaussian kernel is used for route-space smoothing, NOT cost matrix
smoothing. At each scale σ, nodes whose pairwise cost is below σ·max_cost
are clustered together. The reduced problem is solved, then expanded back.
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

# Voltage range: 0.6V → σ=1.0 (coarse), 1.2V → σ=0.25 (fine)
_VOLTAGE_MIN = 0.6
_VOLTAGE_MAX = 1.2
_SIGMA_AT_VMIN = 1.0
_SIGMA_AT_VMAX = 0.25  # Matches finest scale in default sigmas


def voltage_to_scale(voltage_mv: float) -> float:
    """Map millivolt voltage to scale parameter σ.

    Range: 0.6V (600mV, σ=1.0) to 1.2V (1200mV, σ=0.25).

    Linear mapping: σ = 1.0 - (V - 0.6) / 0.6 * 0.75

    Args:
        voltage_mv: Voltage in millivolts.

    Returns:
        Scale parameter σ.
    """
    voltage_v = voltage_mv / 1000.0
    # Clamp to range
    voltage_v = max(_VOLTAGE_MIN, min(_VOLTAGE_MAX, voltage_v))
    # Linear interpolation: σ = 1.0 - (V - 0.6) / 0.6 * 0.75
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
# Cluster-based multi-scale solver
# ---------------------------------------------------------------------------

def _single_linkage_clusters(cost_matrix: list[list[float]],
                             threshold: float) -> list[list[int]]:
    """Cluster nodes using single-linkage clustering.

    Merge nodes whose minimum pairwise cost is below the threshold.

    Args:
        cost_matrix: n×n cost matrix.
        threshold: Cost threshold for merging.

    Returns:
        List of clusters, where each cluster is a list of node indices.
    """
    n = len(cost_matrix)
    if n == 0:
        return []

    # Union-find for single-linkage
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # Merge pairs whose cost is below threshold
    for i in range(n):
        for j in range(i + 1, n):
            if cost_matrix[i][j] < threshold:
                union(i, j)

    # Group nodes by cluster root
    clusters: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(i)

    return list(clusters.values())


def _build_reduced_cost_matrix(cost_matrix: list[list[float]],
                               clusters: list[list[int]]) -> list[list[float]]:
    """Build a reduced cost matrix for cluster representatives.

    The cost between two clusters is the minimum cost between any pair of
    nodes across the two clusters.

    Args:
        cost_matrix: Original n×n cost matrix.
        clusters: List of clusters (each a list of node indices).

    Returns:
        Reduced k×k cost matrix where k = number of clusters.
    """
    k = len(clusters)
    reduced = [[0.0] * k for _ in range(k)]

    for ci in range(k):
        for cj in range(ci + 1, k):
            # Minimum cost across cluster boundaries
            min_cost = float('inf')
            for ni in clusters[ci]:
                for nj in clusters[cj]:
                    if cost_matrix[ni][nj] < min_cost:
                        min_cost = cost_matrix[ni][nj]
            reduced[ci][cj] = min_cost
            reduced[cj][ci] = min_cost

    return reduced


def _expand_tour(cluster_tour: list[int],
                 clusters: list[list[int]],
                 cost_matrix: list[list[float]]) -> list[int]:
    """Expand a cluster-level tour back to individual nodes.

    For each cluster in the tour, we need to enter and exit through specific
    nodes. We pick the entry/exit nodes that minimize the inter-cluster edges.

    Args:
        cluster_tour: Tour over cluster indices.
        clusters: List of clusters (each a list of node indices).
        cost_matrix: Original cost matrix.

    Returns:
        Tour over original node indices.
    """
    if len(cluster_tour) <= 1:
        # Single cluster — order nodes greedily within cluster
        nodes = clusters[cluster_tour[0]]
        if len(nodes) <= 1:
            return nodes
        return _greedy_tour_subgraph(nodes, cost_matrix)[0]

    # For each consecutive pair of clusters, find the best entry/exit nodes
    k = len(cluster_tour)
    entry_node = [0] * k  # Which node in cluster i we enter through
    exit_node = [0] * k   # Which node in cluster i we exit through

    for i in range(k):
        ci = cluster_tour[i]
        cj = cluster_tour[(i + 1) % k]

        # Find the pair of nodes (one in ci, one in cj) with minimum cost
        best_cost = float('inf')
        best_exit = clusters[ci][0]
        best_entry = clusters[cj][0]

        for ni in clusters[ci]:
            for nj in clusters[cj]:
                c = cost_matrix[ni][nj]
                if c < best_cost:
                    best_cost = c
                    best_exit = ni
                    best_entry = nj

        exit_node[i] = best_exit
        entry_node[(i + 1) % k] = best_entry

    # Build the full tour by visiting each cluster's nodes between entry/exit
    full_tour = []
    for i in range(k):
        ci = cluster_tour[i]
        cluster_nodes = clusters[ci]
        entry = entry_node[i]
        exit_nd = exit_node[i]

        if len(cluster_nodes) == 1:
            full_tour.append(cluster_nodes[0])
        else:
            # Build a path through the cluster from entry to exit
            # Use greedy nearest-neighbor within the cluster, starting at entry
            path = _build_cluster_path(cluster_nodes, entry, exit_nd, cost_matrix)
            full_tour.extend(path)

    return full_tour


def _build_cluster_path(nodes: list[int], start: int, end: int,
                        cost_matrix: list[list[float]]) -> list[int]:
    """Build a path through cluster nodes from start to end.

    Uses nearest-neighbor heuristic constrained to the cluster.
    """
    if len(nodes) <= 2:
        # Just return all nodes, start first
        result = [start]
        for n in nodes:
            if n != start:
                result.append(n)
        return result

    visited = {start}
    path = [start]
    current = start

    # Visit all nodes except the end node
    remaining = set(nodes) - {start, end}

    while remaining:
        best_next: int = nodes[0]  # will be overwritten
        best_cost = float('inf')
        for n in remaining:
            c = cost_matrix[current][n]
            if c < best_cost:
                best_cost = c
                best_next = n
        path.append(best_next)
        visited.add(best_next)
        remaining.remove(best_next)
        current = best_next

    # End at the exit node
    if end != start:
        path.append(end)

    return path


def _greedy_tour_subgraph(nodes: list[int],
                          cost_matrix: list[list[float]]) -> tuple[list[int], float]:
    """Greedy nearest-neighbor tour on a subset of nodes."""
    if len(nodes) <= 1:
        return nodes, 0.0

    visited = {nodes[0]}
    tour = [nodes[0]]
    current = nodes[0]
    total_cost = 0.0

    for _ in range(len(nodes) - 1):
        best_j = -1
        best_c = float('inf')
        for j in nodes:
            if j not in visited and cost_matrix[current][j] < best_c:
                best_c = cost_matrix[current][j]
                best_j = j
        tour.append(best_j)
        visited.add(best_j)
        total_cost += best_c
        current = best_j

    total_cost += cost_matrix[current][tour[0]]
    return tour, total_cost


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
    """Solve routing problem at multiple scales using cluster-based optimization.

    Coarse-to-fine strategy with clustering:
        σ=1.0:  coarse — merge nearby nodes, solve small problem
        σ=0.75: medium — tighter clustering
        σ=0.5:  fine — minimal clustering, warm-started
        σ=0.25: formal verification target — full problem, 2-opt polish

    At each scale σ, nodes whose pairwise cost is below σ·max_cost are
    clustered together. The reduced problem is solved on cluster representatives,
    then expanded back to individual nodes. Solutions from coarser scales
    warm-start finer scales.

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

    # Find the maximum cost for threshold computation
    max_cost = 0.0
    for i in range(n):
        for j in range(n):
            if cost_matrix[i][j] > max_cost:
                max_cost = cost_matrix[i][j]

    if max_cost == 0.0:
        # All costs are zero — any tour is optimal
        tour = list(range(n))
        return {
            'solutions': {sigmas[0]: {'tour': tour, 'cost': 0.0,
                                       'n_clusters': 1, 'sigma': sigmas[0]}},
            'converged': True,
            'best_sigma': sigmas[0],
            'best_cost': 0.0,
        }

    solutions = {}
    best_cost = float('inf')
    best_sigma = sigmas[0]
    prev_tour = None

    for sigma in sigmas:
        # Compute clustering threshold: merge nodes with cost < sigma * max_cost
        threshold = sigma * max_cost

        # Cluster nodes using single-linkage
        clusters = _single_linkage_clusters(cost_matrix, threshold)
        n_clusters = len(clusters)

        if n_clusters == 1:
            # All nodes in one cluster — solve the full problem
            if prev_tour is not None:
                tour, cost = _2opt_improve(prev_tour[:], cost_matrix)
            else:
                tour, cost = _greedy_tour(cost_matrix)
                tour, cost = _2opt_improve(tour, cost_matrix)
        else:
            # Build reduced cost matrix for cluster representatives
            reduced_matrix = _build_reduced_cost_matrix(cost_matrix, clusters)

            # Solve the reduced problem
            if n_clusters <= 2:
                # Trivial: just order the clusters
                cluster_tour = list(range(n_clusters))
            else:
                cluster_tour, _ = _greedy_tour(reduced_matrix)
                if n_clusters >= 4:
                    cluster_tour, _ = _2opt_improve(cluster_tour, reduced_matrix)

            # Expand cluster tour back to individual nodes
            tour = _expand_tour(cluster_tour, clusters, cost_matrix)

            # Polish with 2-opt on the full problem
            if prev_tour is not None:
                # Warm-start: try both the expanded tour and the previous tour
                tour_a, cost_a = _2opt_improve(tour, cost_matrix)
                tour_b, cost_b = _2opt_improve(prev_tour[:], cost_matrix)
                if cost_a <= cost_b:
                    tour, cost = tour_a, cost_a
                else:
                    tour, cost = tour_b, cost_b
            else:
                tour, cost = _2opt_improve(tour, cost_matrix)

        solutions[sigma] = {
            'tour': tour,
            'cost': cost,
            'n_clusters': n_clusters,
            'sigma': sigma,
        }

        if cost < best_cost:
            best_cost = cost
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
              f"clusters={data['n_clusters']}")

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
