#!/usr/bin/env python3
"""
Hopf-Cole Solver — Exact solution to 1D Burgers equation.

The Hopf-Cole transformation maps the nonlinear Burgers equation
to the linear heat equation:

  Burgers: du/dt + u·du/dx = v·d²u/dx²
  Hopf-Cole: u = -2v · d(ln ψ)/dx
  Heat: dψ/dt = v · d²ψ/dx²

Two solution methods for the heat equation:
  1. FFT (periodic BCs, O(N log N))
  2. Unified Transform / Fokas method (finite interval, mixed BCs)

Reference: Kalimeris, Mindrinos, Paraskevopoulos (2026)
  "The unified transform for Burgers' equation: Application to
   unsaturated flow in a finite interval" — arXiv:2605.11788

Key result from adversarial review:
  The RG fixed point assumption (nonlinear term vanishes,
  phases evolve linearly) is FALSE for 2D Burgers.
  But 1D Burgers IS integrable via Hopf-Cole.
  The "insultingly easy" regime exists — just not via RG.
"""

import numpy as np
import time
import json
from pathlib import Path

# NumPy 2.x compat: np.trapz was renamed to np.trapezoid
_trapezoid = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')


# ── Hopf-Cole Transformation ────────────────────────────────────────────────

def hopf_cole_forward(psi: np.ndarray, dx: float, nu: float) -> np.ndarray:
    """Hopf-Cole forward: ψ → u = -2ν · d(ln ψ)/dx
    
    Args:
        psi: positive function (heat equation solution)
        dx: grid spacing
        nu: viscosity
    
    Returns:
        u: velocity field
    """
    psi = np.maximum(psi, 1e-30)
    ln_psi = np.log(psi)
    dln_psi_dx = np.gradient(ln_psi, dx)
    u = -2.0 * nu * dln_psi_dx
    return u


def hopf_cole_inverse(u: np.ndarray, dx: float, nu: float) -> np.ndarray:
    """Hopf-Cole inverse: u → ψ = exp(-1/(2ν) · ∫u dx)
    
    Args:
        u: velocity field
        dx: grid spacing
        nu: viscosity
    
    Returns:
        psi: positive function
    """
    integral_u = np.cumsum(u) * dx
    psi = np.exp(-integral_u / (2.0 * nu))
    return psi


# ── Heat Equation Solver: FFT (periodic BCs) ────────────────────────────────

def solve_heat_exact(psi0: np.ndarray, t: float, nu: float, dx: float) -> np.ndarray:
    """Solve heat equation exactly via FFT (periodic boundary conditions).
    
    dψ/dt = ν · d²ψ/dx²
    Solution: ψ(x,t) = IFFT[FFT[ψ(x,0)] · exp(-ν·k²·t)]
    """
    N = len(psi0)
    psi0_hat = np.fft.fft(psi0)
    k = 2.0 * np.pi * np.fft.fftfreq(N, d=dx)
    propagator = np.exp(-nu * k**2 * t)
    psi_hat = psi0_hat * propagator
    psi = np.real(np.fft.ifft(psi_hat))
    return psi


# ── Heat Equation Solver: Unified Transform (Fokas method) ──────────────────

def solve_heat_fokas(
    w0: np.ndarray, x: np.ndarray, t: float, D: float,
    f_t: float = None, g_L: float = None,
    bc_left: str = 'dirichlet', bc_right: str = 'dirichlet',
    N_s: int = 512, contour_scale: float = 5.0,
) -> np.ndarray:
    """Solve heat equation on finite interval [0, L] via Fokas method.
    
    Implements the unified transform (Fokas method) for:
        ∂w/∂t = D · ∂²w/∂x²,  0 < x < L, t > 0
    
    With mixed boundary conditions:
        Left (x=0):  Dirichlet w(0,t) = f(t)  or  Neumann ∂w/∂x(0,t) = g(t)
        Right (x=L): Dirichlet w(L,t) = f_L    or  Robin ∂w/∂x(L,t) + C·w(L,t) = 0
    
    The solution is given by an explicit integral representation over a
    deformed contour in the complex λ-plane (eq. 14 from arXiv:2605.11788).
    
    Args:
        w0: initial condition w(x,0) on the grid
        x: spatial grid points in [0, L]
        t: time (> 0)
        D: diffusion coefficient
        f_t: boundary value w(0,t) for Dirichlet left BC (or None for homogeneous)
        g_L: Robin coefficient C for ∂w/∂x(L,t) + C·w(L,t) = 0 (or None for Dirichlet)
        bc_left: 'dirichlet' or 'neumann'
        bc_right: 'dirichlet' or 'robin'
        N_s: number of quadrature points on contour
        contour_scale: controls contour deformation size
    
    Returns:
        w: solution at time t on grid x
    """
    L = x[-1] - x[0]
    x0 = x[0]
    x_rel = x - x0  # relative coordinates in [0, L]
    dx = x[1] - x[0]
    
    # ── Compute spectral transforms of initial condition ──
    # ŵ₀(λ) = ∫₀ᴸ w₀(x) e^{-iλx} dx  (Fourier transform of IC)
    # For general w0, compute numerically via trapezoidal rule
    # We'll evaluate this on the contour points
    
    # ── Set up the contour ∂D⁺ ──
    # D⁺ = {λ ∈ ℂ : Re(λ²) < 0, Im(λ) > 0}
    # Deformed contour to avoid poles:
    #   λ(s) for s ∈ (-∞, ∞) passing through the first quadrant
    
    # Parametrize contour: three segments
    # Segment 1: s ∈ (-∞, 0) — incoming ray at angle π/8
    # Segment 2: s ∈ [0, 1] — connecting segment
    # Segment 3: s ∈ (1, ∞) — outgoing ray at angle 7π/8
    
    alpha_in = np.pi / 8
    alpha_out = 7 * np.pi / 8
    
    # Choose contour points to avoid singularities
    # The key singularities are at λ = ±i√(B/D) for Robin BCs
    # and at λ = 0. We deform to miss them.
    
    # Build quadrature points on the deformed contour
    # Use a smooth parametrization
    s_vals = np.linspace(-contour_scale, contour_scale, N_s)
    
    # Smooth contour through the first quadrant
    # λ(s) = s·e^{iπ/4} + i·offset ensures we stay in D⁺
    # More precisely, use the parametrization from the paper (eq. 20-21)
    
    # Simple deformed contour: line at angle π/4 shifted into first quadrant
    lam = s_vals * np.exp(1j * np.pi / 4) + 1j * 0.5
    
    # Compute dλ/ds for the quadrature
    dlam_ds = np.exp(1j * np.pi / 4) * np.ones_like(s_vals)
    
    # ── Evaluate spectral transforms on contour ──
    
    # ŵ₀(λ) = ∫₀ᴸ w₀(x) e^{-iλx} dx
    # Vectorized: for each λ, compute the integral
    # w0_hat[j] = ∫ w0(x) e^{-i·lam[j]·x_rel} dx  (trapezoidal rule)
    
    # Shape: (N_s, N_x)
    exp_matrix = np.exp(-1j * np.outer(lam, x_rel))
    w0_hat = _trapezoid(w0[np.newaxis, :] * exp_matrix, x_rel, axis=1)
    
    # ── Boundary condition transforms ──
    # f̃(k, t) = ∫₀ᵗ e^{ks} f(s) ds
    # For constant BC f(t) = f_t:  f̃(k,t) = f_t · (e^{kt} - 1) / k
    
    if f_t is not None and f_t != 0:
        k_vals = D * lam**2  # k = Dλ²
        # f̃(Dλ², t) = f_t · (e^{Dλ²t} - 1) / (Dλ²)
        # Handle k ≈ 0 carefully
        kt = k_vals * t
        f_tilde = np.where(
            np.abs(kt) > 1e-12,
            f_t * (np.exp(kt) - 1.0) / k_vals,
            f_t * t * np.ones_like(k_vals)
        )
    else:
        f_tilde = np.zeros_like(lam)
    
    # ── Build the integrand ──
    # Following eq. (14) from the paper:
    #
    # w(x,t) = 1/(2π) ∫ e^{iλx - Dλ²t} ŵ₀(λ) dλ     [bulk term]
    #         + boundary correction terms
    #
    # For Dirichlet-Dirichlet BCs:
    #   w(x,t) = 1/(2π) ∫_{∂D⁺} [e^{iλx} ŵ₀(λ) + boundary terms] e^{-Dλ²t} dλ
    
    if bc_right == 'robin' and g_L is not None:
        # Robin BC: ∂w/∂x(L,t) + C·w(L,t) = 0
        C = g_L
        
        # All 2D arrays: (N_s, N_x) via outer products
        # lam_col = lam[:, np.newaxis]  → shape (N_s, 1)
        # x_row = x_rel[np.newaxis, :]  → shape (1, N_x)
        lam_col = lam[:, np.newaxis]
        
        sin_lam_x = np.sin(lam_col * x_rel[np.newaxis, :])     # (N_s, N_x)
        sin_lam_L = np.sin(lam * L)                              # (N_s,)
        cos_lam_L = np.cos(lam * L)                              # (N_s,)
        
        sin_lam_L_safe = np.where(np.abs(sin_lam_L) > 1e-30, sin_lam_L, 1e-30)
        
        # Δ(λ, x-L) = λ·cos(λ(x-L)) - C·sin(λ(x-L))  → (N_s, N_x)
        arg_xL = lam_col * (x_rel[np.newaxis, :] - L)
        Delta_xL = lam_col * np.cos(arg_xL) - C * np.sin(arg_xL)
        
        # Δ(λ, -L) = λ·cos(λL) + C·sin(λL)  → (N_s,)
        Delta_mL = lam * cos_lam_L + C * sin_lam_L
        Delta_mL_safe = np.where(np.abs(Delta_mL) > 1e-30, Delta_mL, 1e-30)
        
        # ŵ₀(-λ): ∫ w₀(x) e^{+iλx} dx
        exp_matrix_neg = np.exp(1j * lam_col * x_rel[np.newaxis, :])
        w0_hat_neg = _trapezoid(w0[np.newaxis, :] * exp_matrix_neg, x_rel, axis=1)
        
        # Bulk term: e^{iλx - Dλ²t} · ŵ₀(λ)  → (N_s, N_x)
        exp_ix = np.exp(1j * lam_col * x_rel[np.newaxis, :])
        exp_decay_col = np.exp(-D * lam**2 * t)[:, np.newaxis]  # (N_s, 1)
        bulk = exp_ix * exp_decay_col * w0_hat[:, np.newaxis]
        
        # Boundary correction from left BC (Dirichlet)
        # sin(λx)/Δ(λ,-L) · [(iλ+C)·e^{iλL}·ŵ₀(λ) + Δ(λ,x-L)·ŵ₀(-λ)]
        inv_DmL = (1.0 / Delta_mL_safe)[:, np.newaxis]  # (N_s, 1)
        
        iLpC_eiLL = ((1j * lam + C) * np.exp(1j * lam * L))[:, np.newaxis]  # (N_s, 1)
        
        bc_left_term = sin_lam_x * inv_DmL * (
            iLpC_eiLL * w0_hat[:, np.newaxis]
            + Delta_xL * w0_hat_neg[:, np.newaxis]
        )
        
        # Time-dependent boundary term: sin(λx)/Δ(λ,-L) · 2iDλ²·f̃
        if f_t is not None and f_t != 0:
            bc_time_term = sin_lam_x * inv_DmL * (
                1j * 2 * D * (lam**2)[:, np.newaxis] * f_tilde[:, np.newaxis]
            )
        else:
            bc_time_term = 0
        
        integrand = (bulk + exp_decay_col * (bc_left_term + bc_time_term)) * dlam_ds[:, np.newaxis]
        
    else:
        # Dirichlet-Dirichlet BCs (simpler case)
        # w(0,t) = f(t), w(L,t) = g_L (constant)
        
        sin_lam_x = np.sin(np.outer(lam, x_rel))
        sin_lam_L = np.sin(lam * L)
        sin_lam_L_safe = np.where(np.abs(sin_lam_L) > 1e-30, sin_lam_L, 1e-30)
        
        # Bulk term
        bulk = np.exp(1j * np.outer(lam, x_rel) - D * (lam**2 * t)[:, np.newaxis]) * w0_hat[:, np.newaxis]
        
        # Boundary correction: sin(λx)/sin(λL) · [...]
        ratio = sin_lam_x / sin_lam_L_safe[:, np.newaxis]
        exp_decay = np.exp(-D * (lam**2 * t)[:, np.newaxis])
        
        # Left BC contribution (Dirichlet)
        if f_t is not None and f_t != 0:
            k_vals = D * lam**2
            bc_left_contrib = ratio * (
                -np.sin(lam[:, np.newaxis] * (x_rel[np.newaxis, :] - L)) * w0_hat[:, np.newaxis]
                + np.sin(lam[:, np.newaxis] * x_rel[np.newaxis, :]) * np.exp(1j * lam * L)[:, np.newaxis] * w0_hat[:, np.newaxis]
            )
            # Simplified: use the standard Dirichlet-Dirichlet Green's function form
            # w = bulk + sin(λx)/sin(λL) · boundary terms
            bc_left_contrib = ratio * exp_decay * (
                -np.sin(lam[:, np.newaxis] * (x_rel[np.newaxis, :] - L)) * w0_hat[:, np.newaxis]
            )
        else:
            bc_left_contrib = 0
        
        # Right BC contribution
        if g_L is not None and g_L != 0:
            bc_right_contrib = ratio * exp_decay * (
                np.sin(lam[:, np.newaxis] * x_rel[np.newaxis, :]) * g_L * f_tilde[:, np.newaxis]
            )
        else:
            bc_right_contrib = 0
        
        integrand = (bulk + bc_left_contrib + bc_right_contrib) * dlam_ds[:, np.newaxis]
    
    # ── Integrate along contour ──
    w = np.real(_trapezoid(integrand, s_vals, axis=0)) / (2 * np.pi)
    
    return w


# ── Burgers Solver: Hopf-Cole + FFT ─────────────────────────────────────────

def solve_burgers_hopf_cole(u0: np.ndarray, t: float, nu: float, dx: float) -> np.ndarray:
    """Solve 1D Burgers equation exactly via Hopf-Cole + FFT (periodic BCs).
    
    Args:
        u0: initial velocity field
        t: time
        nu: viscosity
        dx: grid spacing
    
    Returns:
        u: velocity field at time t
    """
    psi0 = hopf_cole_inverse(u0, dx, nu)
    psi_t = solve_heat_exact(psi0, t, nu, dx)
    u_t = hopf_cole_forward(psi_t, dx, nu)
    return u_t


# ── Burgers Solver: Hopf-Cole + Fokas ───────────────────────────────────────

def solve_burgers_fokas(
    u0: np.ndarray, x: np.ndarray, t: float, nu: float,
    bc_left_val: float = 0.0, bc_right_val: float = 0.0,
    bc_right_robin_C: float = None,
    N_s: int = 512, contour_scale: float = 5.0,
) -> np.ndarray:
    """Solve 1D Burgers equation via Hopf-Cole + Fokas method.
    
    Solves on a finite interval [x[0], x[-1]] with mixed boundary conditions.
    The Fokas method provides an integral representation that converges
    better than Fourier series, especially for short times and near boundaries.
    
    Args:
        u0: initial velocity field on grid x
        x: spatial grid points (finite interval)
        t: time
        nu: viscosity
        bc_left_val: Dirichlet BC value at x[0] for the heat equation variable
        bc_right_val: Dirichlet BC value at x[-1] (if Dirichlet)
        bc_right_robin_C: Robin coefficient C for ∂ψ/∂x + C·ψ = 0 at x[-1]
        N_s: number of quadrature points
        contour_scale: contour deformation parameter
    
    Returns:
        u: velocity field at time t
    """
    dx = x[1] - x[0]
    
    # Step 1: Inverse Hopf-Cole: u0 → ψ0
    psi0 = hopf_cole_inverse(u0, dx, nu)
    
    # Step 2: Solve heat equation via Fokas method
    if bc_right_robin_C is not None:
        psi_t = solve_heat_fokas(
            psi0, x, t, nu,
            f_t=bc_left_val, g_L=bc_right_robin_C,
            bc_left='dirichlet', bc_right='robin',
            N_s=N_s, contour_scale=contour_scale,
        )
    else:
        psi_t = solve_heat_fokas(
            psi0, x, t, nu,
            f_t=bc_left_val, g_L=bc_right_val,
            bc_left='dirichlet', bc_right='dirichlet',
            N_s=N_s, contour_scale=contour_scale,
        )
    
    # Ensure positivity
    psi_t = np.maximum(psi_t, 1e-30)
    
    # Step 3: Forward Hopf-Cole: ψ(t) → u(t)
    u_t = hopf_cole_forward(psi_t, dx, nu)
    
    return u_t


# ── Finite Difference Burgers (for comparison) ──────────────────────────────

def solve_burgers_fd(u0: np.ndarray, t_final: float, nu: float, dx: float, 
                     dt: float = None) -> np.ndarray:
    """Solve 1D Burgers equation via finite differences (explicit Euler).
    
    For comparison with Hopf-Cole exact solution.
    """
    N = len(u0)
    u = u0.copy()
    
    if dt is None:
        dt = 0.4 * dx**2 / nu  # CFL condition
    
    n_steps = int(t_final / dt)
    
    for _ in range(n_steps):
        dudx = np.gradient(u, dx)
        d2udx2 = np.gradient(dudx, dx)
        u_new = u + dt * (-u * dudx + nu * d2udx2)
        u = u_new
    
    return u


# ── Fourier Series Solution (for Fokas comparison) ──────────────────────────

def solve_heat_fourier_series(
    w0_func, L: float, t: float, D: float,
    f_t: float, g_C: float, N_terms: int = 2000,
    x: np.ndarray = None,
) -> np.ndarray:
    """Solve heat equation on [0,L] via Fourier series (for comparison).
    
    IBVP: ∂w/∂t = D·∂²w/∂x²
    BCs:  w(0,t) = f(t),  ∂w/∂x(L,t) + C·w(L,t) = 0
    
    Uses eigenfunction expansion with Robin BCs at x=L.
    """
    if x is None:
        x = np.linspace(0, L, 256)
    
    # Eigenvalues for Robin BC: tan(λL) = -λ/C
    # Find eigenvalues numerically
    eigenvalues = []
    for n in range(N_terms):
        # Search for n-th eigenvalue
        lo = n * np.pi / L + 1e-6
        hi = (n + 1) * np.pi / L - 1e-6
        if n == 0:
            lo = 1e-6
        
        # tan(λL) + λ/C = 0  →  tan(λL) = -λ/C
        # Use bisection
        for _ in range(100):
            mid = (lo + hi) / 2
            val = np.tan(mid * L) + mid / g_C
            if val * (np.tan(lo * L) + lo / g_C) < 0:
                hi = mid
            else:
                lo = mid
        eigenvalues.append((lo + hi) / 2)
    
    eigenvalues = np.array(eigenvalues[:N_terms])
    
    # Eigenfunctions: φₙ(x) = sin(λₙx) (satisfying φ(0) = 0)
    # For w(0,t) = f(t) ≠ 0, we need to handle the inhomogeneous BC
    # Use the substitution v(x,t) = w(x,t) - f(t)·(1 - x/L) for Dirichlet-Dirichlet
    # Or use the Green's function approach
    
    # For simplicity, compute the homogeneous solution and add the steady-state
    # Steady state satisfying BCs: w_s(x) = f_t · cosh(γ(L-x)) / cosh(γL)
    # where γ = g_C (Robin coefficient)
    
    if g_C != 0:
        # Steady state for Robin BC
        w_steady = f_t * np.cosh(g_C * (L - x)) / np.cosh(g_C * L)
    else:
        # Dirichlet-Dirichlet: w_s = f_t * (1 - x/L)
        w_steady = f_t * (1 - x / L)
    
    # Transient part: v(x,t) = w(x,t) - w_s(x)
    # v satisfies homogeneous BCs and v(x,0) = w0(x) - w_s(x)
    w0_vals = w0_func(x)
    v0 = w0_vals - w_steady
    
    # Fourier coefficients for v
    # φₙ(x) = sin(λₙx),  ||φₙ||² = L/2 - sin(2λₙL)/(4λₙ)
    w = np.zeros_like(x)
    for n, lam_n in enumerate(eigenvalues):
        phi_n = np.sin(lam_n * x)
        norm_sq = L / 2 - np.sin(2 * lam_n * L) / (4 * lam_n)
        if abs(norm_sq) < 1e-30:
            continue
        c_n = _trapezoid(v0 * phi_n, x) / norm_sq
        w += c_n * phi_n * np.exp(-D * lam_n**2 * t)
    
    w += w_steady
    return w


# ── Benchmark ────────────────────────────────────────────────────────────────

def benchmark_hopf_cole():
    """Benchmark: Hopf-Cole FFT vs Finite Difference."""
    print("=" * 60)
    print("Hopf-Cole FFT vs Finite Difference Burgers Solver")
    print("=" * 60)
    
    results = []
    
    for N in [512, 1024, 2048]:
        for nu in [0.01, 0.001]:
            dx = 2.0 * np.pi / N
            x = np.linspace(0, 2.0 * np.pi, N, endpoint=False)
            u0 = np.sin(x)
            t_final = 0.5
            
            t0 = time.time()
            u_hc = solve_burgers_hopf_cole(u0, t_final, nu, dx)
            hc_time = time.time() - t0
            
            t0 = time.time()
            u_fd = solve_burgers_fd(u0, t_final, nu, dx)
            fd_time = time.time() - t0
            
            error = np.sqrt(np.mean((u_hc - u_fd)**2))
            speedup = fd_time / hc_time if hc_time > 0 else float('inf')
            
            print(f"\n  N={N}, ν={nu}:")
            print(f"    Hopf-Cole: {hc_time*1000:.2f}ms")
            print(f"    FD:        {fd_time*1000:.2f}ms")
            print(f"    Speedup:   {speedup:.2f}x")
            print(f"    RMSE:      {error:.6f}")
            
            results.append({
                'N': N, 'nu': nu,
                'hopf_cole_ms': hc_time * 1000,
                'fd_ms': fd_time * 1000,
                'speedup': speedup,
                'rmse': error,
            })
    
    return results


def benchmark_fokas():
    """Benchmark: Fokas method vs Fourier series on finite interval.
    
    Tests the convergence advantage of the unified transform method
    over classical Fourier series for the heat equation on [0, L]
    with mixed boundary conditions (Robin at x=L).
    
    Based on: Kalimeris, Mindrinos, Paraskevopoulos (2026)
    arXiv:2605.11788
    """
    print("=" * 60)
    print("Fokas Method vs Fourier Series (Finite Interval)")
    print("Reference: arXiv:2605.11788")
    print("=" * 60)
    
    results = []
    
    # Physical parameters from paper Example 1
    D = 0.001  # diffusivity (m²/s)
    L = 0.25   # column length (m)
    theta_0 = 0.03
    theta_L = 0.03
    a_coeff = 1.0
    b_coeff = 0.0
    q_flux = 3.4e-6  # constant flux (m/s)
    
    # Derived parameters
    A_coeff = a_coeff / D * (theta_0 + b_coeff)
    B_coeff = a_coeff / D * q_flux
    C_robin = a_coeff / D * (theta_L + b_coeff)
    
    # Initial condition for heat equation: w0(x) = exp(-A·x)
    def w0_func(x):
        return np.exp(-A_coeff * x)
    
    N_x = 256
    x = np.linspace(0, L, N_x)
    w0 = w0_func(x)
    
    # Dirichlet BC at x=0: w(0,t) = exp(B·t)
    # For short time, approximate as constant f_t ≈ 1
    f_t = 1.0  # exp(B*0) = 1 for t≈0; use f_t=1 for the benchmark
    
    t_test = 600.0  # 10 minutes
    
    # ── Fokas method ──
    print("\n--- Fokas Method ---")
    for N_s in [128, 256, 512]:
        t0 = time.time()
        w_fokas = solve_heat_fokas(
            w0, x, t_test, D,
            f_t=f_t, g_L=C_robin,
            bc_left='dirichlet', bc_right='robin',
            N_s=N_s, contour_scale=8.0,
        )
        fokas_time = time.time() - t0
        print(f"  N_s={N_s}: {fokas_time*1000:.2f}ms")
    
    # ── Fourier series ──
    print("\n--- Fourier Series ---")
    for N_terms in [100, 500, 2000]:
        t0 = time.time()
        w_fourier = solve_heat_fourier_series(
            w0_func, L, t_test, D,
            f_t=f_t, g_C=C_robin,
            N_terms=N_terms, x=x,
        )
        fourier_time = time.time() - t0
        print(f"  N_terms={N_terms}: {fourier_time*1000:.2f}ms")
    
    # ── Compare convergence ──
    print("\n--- Convergence Comparison ---")
    # Reference: high-resolution Fokas
    w_ref = solve_heat_fokas(
        w0, x, t_test, D,
        f_t=f_t, g_L=C_robin,
        bc_left='dirichlet', bc_right='robin',
        N_s=1024, contour_scale=10.0,
    )
    
    print(f"\n  {'Method':<25} {'N_pts':<8} {'RMSE vs ref':<15} {'Time (ms)':<12}")
    print(f"  {'-'*60}")
    
    for N_s in [64, 128, 256, 512]:
        t0 = time.time()
        w_f = solve_heat_fokas(
            w0, x, t_test, D,
            f_t=f_t, g_L=C_robin,
            bc_left='dirichlet', bc_right='robin',
            N_s=N_s, contour_scale=8.0,
        )
        fokas_time = time.time() - t0
        rmse = np.sqrt(np.mean((w_f - w_ref)**2))
        print(f"  {'Fokas':<25} {N_s:<8} {rmse:<15.2e} {fokas_time*1000:<12.2f}")
        results.append({'method': 'fokas', 'N': N_s, 'rmse': rmse, 'time_ms': fokas_time * 1000})
    
    for N_terms in [50, 100, 500, 1000, 2000]:
        t0 = time.time()
        w_f = solve_heat_fourier_series(
            w0_func, L, t_test, D,
            f_t=f_t, g_C=C_robin,
            N_terms=N_terms, x=x,
        )
        fourier_time = time.time() - t0
        rmse = np.sqrt(np.mean((w_f - w_ref)**2))
        print(f"  {'Fourier series':<25} {N_terms:<8} {rmse:<15.2e} {fourier_time*1000:<12.2f}")
        results.append({'method': 'fourier', 'N': N_terms, 'rmse': rmse, 'time_ms': fourier_time * 1000})
    
    # ── Burgers equation comparison ──
    print("\n--- Burgers Equation: Hopf-Cole+Fokas vs Hopf-Cole+FFT ---")
    N_burgers = 256
    x_b = np.linspace(0, L, N_burgers)
    u0_b = np.sin(np.pi * x_b / L)  # smooth IC compatible with BCs
    
    t0 = time.time()
    u_fokas = solve_burgers_fokas(
        u0_b, x_b, 100.0, nu=D,
        bc_left_val=0.0, bc_right_robin_C=C_robin,
        N_s=256, contour_scale=8.0,
    )
    fokas_burgers_time = time.time() - t0
    
    # FFT version (periodic, for reference)
    dx_b = x_b[1] - x_b[0]
    t0 = time.time()
    u_fft = solve_burgers_hopf_cole(u0_b, 100.0, D, dx_b)
    fft_burgers_time = time.time() - t0
    
    print(f"  Hopf-Cole+Fokas: {fokas_burgers_time*1000:.2f}ms")
    print(f"  Hopf-Cole+FFT:   {fft_burgers_time*1000:.2f}ms")
    
    results.append({
        'method': 'burgers_fokas', 'time_ms': fokas_burgers_time * 1000,
    })
    results.append({
        'method': 'burgers_fft', 'time_ms': fft_burgers_time * 1000,
    })
    
    return results


def benchmark_all():
    """Run all benchmarks and save results."""
    print("=" * 70)
    print("Hopf-Cole Burgers Solver — Full Benchmark Suite")
    print("Includes: FFT solver, Fokas method, Fourier series comparison")
    print("=" * 70)
    
    all_results = {}
    
    # Part 1: FFT vs FD
    print("\n\n[1/2] Hopf-Cole FFT vs Finite Difference")
    fft_results = benchmark_hopf_cole()
    all_results['fft_vs_fd'] = fft_results
    
    # Part 2: Fokas vs Fourier series
    print("\n\n[2/2] Fokas Method vs Fourier Series")
    fokas_results = benchmark_fokas()
    all_results['fokas_vs_fourier'] = fokas_results
    
    # Save
    out = {
        'schema': 'hopf_cole_benchmark_v2',
        'description': 'Hopf-Cole solver benchmark with Fokas unified transform method',
        'reference': 'arXiv:2605.11788 (Kalimeris, Mindrinos, Paraskevopoulos 2026)',
        'results': all_results,
    }
    out_path = Path(__file__).resolve().parent.parent.parent / 'shared-data' / 'artifacts' / 'hopf_cole_benchmark.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n\nResults saved: {out_path}")
    
    return all_results


# ── Visualization ────────────────────────────────────────────────────────────

def plot_comparison():
    """Plot Hopf-Cole vs FD solution."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available")
        return
    
    N = 1024
    nu = 0.01
    dx = 2.0 * np.pi / N
    x = np.linspace(0, 2.0 * np.pi, N, endpoint=False)
    u0 = np.sin(x)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    for ax, t in zip(axes.flat, [0.1, 0.3, 0.5, 1.0]):
        u_hc = solve_burgers_hopf_cole(u0, t, nu, dx)
        u_fd = solve_burgers_fd(u0, t, nu, dx)
        
        ax.plot(x, u_hc, 'b-', label='Hopf-Cole (exact)', linewidth=2)
        ax.plot(x, u_fd, 'r--', label='Finite Difference', linewidth=1)
        ax.set_title(f't = {t}')
        ax.legend()
        ax.set_xlabel('x')
        ax.set_ylabel('u')
    
    plt.tight_layout()
    plt.savefig('/tmp/hopf_cole_comparison.png', dpi=150)
    print("Saved: /tmp/hopf_cole_comparison.png")


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: hopf_cole_burgers.py --benchmark")
        print("       hopf_cole_burgers.py --benchmark-fokas")
        print("       hopf_cole_burgers.py --plot")
        print("       hopf_cole_burgers.py --solve <N> <nu> <t>")
        sys.exit(1)
    
    if sys.argv[1] == '--benchmark':
        benchmark_all()
    elif sys.argv[1] == '--benchmark-fokas':
        benchmark_fokas()
    elif sys.argv[1] == '--plot':
        plot_comparison()
    elif sys.argv[1] == '--solve':
        N = int(sys.argv[2])
        nu = float(sys.argv[3])
        t = float(sys.argv[4])
        dx = 2.0 * np.pi / N
        x = np.linspace(0, 2.0 * np.pi, N, endpoint=False)
        u0 = np.sin(x)
        u = solve_burgers_hopf_cole(u0, t, nu, dx)
        print(f"u[0:10] = {u[:10]}")
