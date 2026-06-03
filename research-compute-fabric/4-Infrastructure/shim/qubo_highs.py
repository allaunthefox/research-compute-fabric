"""
QUBO-to-MIP bridge using HiGHS solver.

Converts Quadratic Unconstrained Binary Optimization problems into
Mixed Integer Programming formulations solvable by HiGHS.

Falls back to simulated annealing if highspy is not installed.
"""

import math
import random
import time
from typing import Any

try:
    import highspy
    import numpy as np
    HAS_HIGHS = True
except ImportError:
    HAS_HIGHS = False


# ---------------------------------------------------------------------------
# QUBO → MIP reformulation
# ---------------------------------------------------------------------------

def qubo_to_mip(Q: dict[tuple[int, int], float]):
    """Convert QUBO matrix Q to MIP formulation.

    QUBO: min x^T Q x  where x in {0,1}^n
    Since x_i^2 = x_i for binary variables:
        min  sum_i Q[i,i]*x[i] + sum_{i<j} 2*Q[i,j]*x[i]*x[j]

    Linearization of bilinear terms y[i,j] = x[i]*x[j]:
        y[i,j] <= x[i]
        y[i,j] <= x[j]
        y[i,j] >= x[i] + x[j] - 1

    Returns (H, c, sense, rhs) where:
        H: objective coefficients dict {var_index: coeff}
        c: constraint matrix as list of (var_coeffs, sense, rhs)
        sense: list of constraint senses ('<=' or '>=')
        rhs: list of constraint RHS values
    """
    # Collect all variable indices
    indices = set()
    for i, j in Q:
        indices.add(i)
        indices.add(j)
    if not indices:
        return {}, [], [], []

    n = max(indices) + 1  # number of x variables

    # Separate diagonal (linear) and off-diagonal (bilinear) terms
    linear_coeffs: dict[int, float] = {}
    pair_coeffs: dict[tuple[int, int], float] = {}

    for (i, j), coeff in Q.items():
        if i == j:
            linear_coeffs[i] = linear_coeffs.get(i, 0.0) + coeff
        else:
            key = (min(i, j), max(i, j))
            pair_coeffs[key] = pair_coeffs.get(key, 0.0) + coeff

    # Build objective: linear part in x, bilinear part in y variables
    # x variables: indices 0..n-1
    # y variables: indices n, n+1, ... (one per pair)
    H: dict[int, float] = {}
    for i, coeff in linear_coeffs.items():
        H[i] = H.get(i, 0.0) + coeff

    y_index_map: dict[tuple[int, int], int] = {}
    y_idx = n
    for (i, j), coeff in pair_coeffs.items():
        if abs(coeff) < 1e-15:
            continue
        H[y_idx] = coeff
        y_index_map[(i, j)] = y_idx
        y_idx += 1

    # Build linearization constraints
    constraints = []  # list of (var_coeffs: dict, sense, rhs)
    for (i, j), yi_idx in y_index_map.items():
        # y[i,j] <= x[i]  →  y[i,j] - x[i] <= 0
        constraints.append(({yi_idx: 1.0, i: -1.0}, '<=', 0.0))
        # y[i,j] <= x[j]  →  y[i,j] - x[j] <= 0
        constraints.append(({yi_idx: 1.0, j: -1.0}, '<=', 0.0))
        # y[i,j] >= x[i] + x[j] - 1  →  -y[i,j] + x[i] + x[j] <= 1
        constraints.append(({yi_idx: -1.0, i: 1.0, j: 1.0}, '<=', 1.0))

    c = constraints
    sense_list = [s for _, s, _ in c]
    rhs_list = [r for _, _, r in c]

    return H, c, sense_list, rhs_list


# ---------------------------------------------------------------------------
# Simulated annealing fallback
# ---------------------------------------------------------------------------

def _sa_solve_qubo(Q: dict[tuple[int, int], float], n: int,
                   time_limit: float = 60.0) -> dict:
    """Simulated annealing fallback for QUBO."""
    if n is None or n == 0:
        return {'solution': [], 'objective': 0.0, 'status': 'empty'}

    def evaluate(x: list[int]) -> float:
        return sum(Q.get((i, j), 0.0) * x[i] * x[j]
                   for i in range(n) for j in range(n) if (i, j) in Q)

    # Initialize random solution
    current = [random.randint(0, 1) for _ in range(n)]
    current_val = evaluate(current)
    best = current[:]
    best_val = current_val

    T = 10.0
    T_min = 1e-8
    alpha = 0.9995
    start = time.time()

    while T > T_min and (time.time() - start) < time_limit:
        # Flip a random bit
        idx = random.randint(0, n - 1)
        current[idx] = 1 - current[idx]
        new_val = evaluate(current)

        delta = new_val - current_val
        if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-30)):
            current_val = new_val
            if current_val < best_val:
                best = current[:]
                best_val = current_val
        else:
            current[idx] = 1 - current[idx]  # revert

        T *= alpha

    return {'solution': best, 'objective': best_val, 'status': 'SA_heuristic'}


# ---------------------------------------------------------------------------
# HiGHS-based QUBO solver
# ---------------------------------------------------------------------------

def solve_qubo_highs(Q: dict[tuple[int, int], float],
                     time_limit: float = 60.0) -> dict:
    """Solve QUBO using HiGHS MIP solver.

    Returns: {'solution': list[int], 'objective': float, 'status': str}
    """
    indices = set()
    for i, j in Q:
        indices.add(i)
        indices.add(j)
    if not indices:
        return {'solution': [], 'objective': 0.0, 'status': 'empty'}

    n = max(indices) + 1

    if not HAS_HIGHS:
        print("[qubo_highs] highspy not installed, falling back to SA")
        return _sa_solve_qubo(Q, n, time_limit)

    H, c, sense_list, rhs_list = qubo_to_mip(Q)
    if not H:
        return {'solution': [0] * n, 'objective': 0.0, 'status': 'trivial'}

    num_vars = max(H.keys()) + 1
    num_rows = len(c)

    # Build model using passModel (reliable API)
    model = highspy.HighsModel()
    lp = model.lp_
    lp.num_col_ = num_vars
    lp.num_row_ = num_rows

    # Objective coefficients
    obj = np.zeros(num_vars)
    for v, coeff in H.items():
        obj[v] = coeff
    lp.col_cost_ = obj

    # Variable bounds: all binary [0, 1]
    lp.col_lower_ = np.zeros(num_vars)
    lp.col_upper_ = np.ones(num_vars)

    # Integrality
    lp.integrality_ = [highspy.HighsVarType.kInteger] * num_vars

    # Build constraint matrix in CSC format
    # First, convert to column-wise structure
    col_entries: dict[int, list[tuple[int, float]]] = {}
    for row_idx, (var_coeffs, s, rhs) in enumerate(c):
        for col, val in var_coeffs.items():
            if col not in col_entries:
                col_entries[col] = []
            col_entries[col].append((row_idx, val))

    starts = []
    indices_list = []
    values_list = []
    nnz = 0
    for col in range(num_vars):
        starts.append(nnz)
        if col in col_entries:
            for row_idx, val in col_entries[col]:
                indices_list.append(row_idx)
                values_list.append(val)
                nnz += 1

    starts.append(nnz)

    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(starts, dtype=np.int32)
    lp.a_matrix_.index_ = np.array(indices_list, dtype=np.int32) if indices_list else np.array([], dtype=np.int32)
    lp.a_matrix_.value_ = np.array(values_list) if values_list else np.array([])

    # Row bounds
    row_lower = []
    row_upper = []
    for (var_coeffs, s, rhs) in c:
        if s == '<=':
            row_lower.append(-1e30)
            row_upper.append(rhs)
        else:
            row_lower.append(rhs)
            row_upper.append(1e30)
    lp.row_lower_ = np.array(row_lower)
    lp.row_upper_ = np.array(row_upper)

    # Solve
    h = highspy.Highs()
    h.setOptionValue("time_limit", time_limit)
    h.setOptionValue("output_flag", False)
    h.passModel(model)
    h.run()

    sol = h.getSolution()
    x_vals = sol.col_value

    solution = [int(round(x_vals[i])) for i in range(n)]
    objective = sum(Q.get((i, j), 0.0) * solution[i] * solution[j]
                    for i in range(n) for j in range(n) if (i, j) in Q)

    # Get status
    status_val = h.getInfoValue("primal_solution_status")[1]
    status_map = {
        0: 'unknown',
        1: 'infeasible',
        2: 'feasible',
        3: 'optimal',
    }
    status_str = status_map.get(status_val, f'status_{status_val}')

    return {'solution': solution, 'objective': objective, 'status': status_str}


# ---------------------------------------------------------------------------
# Route LP relaxation
# ---------------------------------------------------------------------------

def solve_route_lp(cost_matrix: list[list[float]],
                   time_limit: float = 60.0) -> dict:
    """Solve TSP/VRP relaxation using HiGHS LP.

    Treats the routing problem as an assignment LP relaxation:
    min sum_{i,j} c[i][j] * x[i][j]
    s.t. sum_j x[i][j] = 1 for all i  (leave each city once)
         sum_i x[i][j] = 1 for all j  (enter each city once)
         0 <= x[i][j] <= 1

    Returns: {'route': list[int], 'cost': float, 'status': str}
    """
    n = len(cost_matrix)
    if n == 0:
        return {'route': [], 'cost': 0.0, 'status': 'empty'}

    if not HAS_HIGHS:
        # Greedy nearest-neighbor fallback
        return _greedy_route(cost_matrix)

    # Variables: x[i][j] for i,j in 0..n-1, i != j
    var_list = [(i, j) for i in range(n) for j in range(n) if i != j]
    num_vars = len(var_list)
    var_idx = {v: k for k, v in enumerate(var_list)}

    model = highspy.HighsModel()
    lp = model.lp_
    lp.num_col_ = num_vars
    lp.num_row_ = 2 * n  # leave + enter constraints

    # Objective
    costs = np.zeros(num_vars)
    for (i, j), vi in var_idx.items():
        costs[vi] = cost_matrix[i][j]
    lp.col_cost_ = costs

    # Bounds
    lp.col_lower_ = np.zeros(num_vars)
    lp.col_upper_ = np.ones(num_vars)

    # Build CSC constraint matrix
    starts = []
    indices_list = []
    values_list = []
    nnz = 0

    col_entries: dict[int, list[tuple[int, float]]] = {}

    # Leave constraints (rows 0..n-1)
    for i in range(n):
        for j in range(n):
            if i != j:
                vi = var_idx[(i, j)]
                if vi not in col_entries:
                    col_entries[vi] = []
                col_entries[vi].append((i, 1.0))

    # Enter constraints (rows n..2n-1)
    for j in range(n):
        for i in range(n):
            if i != j:
                vi = var_idx[(i, j)]
                if vi not in col_entries:
                    col_entries[vi] = []
                col_entries[vi].append((n + j, 1.0))

    for col in range(num_vars):
        starts.append(nnz)
        if col in col_entries:
            for row_idx, val in col_entries[col]:
                indices_list.append(row_idx)
                values_list.append(val)
                nnz += 1
    starts.append(nnz)

    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(starts, dtype=np.int32)
    lp.a_matrix_.index_ = np.array(indices_list, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(values_list)

    # Row bounds: all equality (= 1)
    lp.row_lower_ = np.ones(2 * n)
    lp.row_upper_ = np.ones(2 * n)

    # Solve
    h = highspy.Highs()
    h.setOptionValue("time_limit", time_limit)
    h.setOptionValue("output_flag", False)
    h.passModel(model)
    h.run()

    sol = h.getSolution()
    x_vals = sol.col_value

    # Extract route from assignment (greedy rounding)
    route = _extract_route_from_assignment(x_vals, var_idx, n)
    total_cost = sum(cost_matrix[route[i]][route[(i + 1) % n]]
                     for i in range(n))

    status_raw = h.getInfoValue("primal_solution_status")[1]
    status_str = {
        0: 'unknown',
        1: 'infeasible',
        2: 'feasible',
        3: 'optimal',
    }.get(status_raw, f'status_{status_raw}')

    return {'route': route, 'cost': total_cost, 'status': status_str}


def _extract_route_from_assignment(x_vals, var_idx, n):
    """Extract a tour from LP assignment solution via greedy rounding."""
    # Greedy: follow highest-weight edges to build a tour
    used = set()
    route = [0]
    current = 0
    while len(route) < n:
        candidates = [(x_vals[var_idx[(current, j)]], j)
                      for j in range(n) if j != current and j not in used
                      and (current, j) in var_idx]
        if not candidates:
            break
        candidates.sort(reverse=True)
        next_city = candidates[0][1]
        route.append(next_city)
        used.add(next_city)
        current = next_city

    return route


def _greedy_route(cost_matrix: list[list[float]]) -> dict:
    """Nearest-neighbor heuristic fallback."""
    n = len(cost_matrix)
    if n == 0:
        return {'route': [], 'cost': 0.0, 'status': 'heuristic'}

    visited = {0}
    route = [0]
    total = 0.0
    current = 0

    while len(route) < n:
        best_j = -1
        best_c = float('inf')
        for j in range(n):
            if j not in visited and cost_matrix[current][j] < best_c:
                best_c = cost_matrix[current][j]
                best_j = j
        route.append(best_j)
        visited.add(best_j)
        total += best_c
        current = best_j

    total += cost_matrix[current][route[0]]
    return {'route': route, 'cost': total, 'status': 'heuristic'}
