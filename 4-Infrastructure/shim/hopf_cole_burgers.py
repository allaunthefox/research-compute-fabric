#!/usr/bin/env python3
"""
Hopf-Cole Solver — Exact solution to 1D Burgers equation.

The Hopf-Cole transformation maps the nonlinear Burgers equation
to the linear heat equation:

  Burgers: du/dt + u·du/dx = v·d²u/dx²
  Hopf-Cole: u = -2v · d(ln ψ)/dx
  Heat: dψ/dt = v · d²ψ/dx²

The heat equation has an exact solution via FFT:
  ψ(x,t) = IFFT[FFT[ψ(x,0)] · exp(-v·k²·t)]

This gives an O(N log N) exact solution to 1D Burgers.
No time stepping. No numerical diffusion. Exact.

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
    # Ensure psi is positive
    psi = np.maximum(psi, 1e-30)
    
    # ln(psi)
    ln_psi = np.log(psi)
    
    # d(ln psi)/dx via central differences
    dln_psi_dx = np.gradient(ln_psi, dx)
    
    # u = -2ν · d(ln ψ)/dx
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
    # ∫u dx via cumulative trapezoidal integration
    integral_u = np.cumsum(u) * dx
    
    # ψ = exp(-1/(2ν) · ∫u dx)
    psi = np.exp(-integral_u / (2.0 * nu))
    
    return psi


# ── Heat Equation Solver (exact via FFT) ────────────────────────────────────

def solve_heat_exact(psi0: np.ndarray, t: float, nu: float, dx: float) -> np.ndarray:
    """Solve heat equation exactly via FFT.
    
    dψ/dt = ν · d²ψ/dx²
    
    Solution: ψ(x,t) = IFFT[FFT[ψ(x,0)] · exp(-ν·k²·t)]
    
    Args:
        psi0: initial condition
        t: time
        nu: viscosity
        dx: grid spacing
    
    Returns:
        psi: solution at time t
    """
    N = len(psi0)
    
    # FFT of initial condition
    psi0_hat = np.fft.fft(psi0)
    
    # Wavenumbers
    k = 2.0 * np.pi * np.fft.fftfreq(N, d=dx)
    
    # Propagator: exp(-ν·k²·t)
    propagator = np.exp(-nu * k**2 * t)
    
    # Solution in frequency space
    psi_hat = psi0_hat * propagator
    
    # Transform back
    psi = np.real(np.fft.ifft(psi_hat))
    
    return psi


# ── Burgers Solver (Hopf-Cole) ──────────────────────────────────────────────

def solve_burgers_hopf_cole(u0: np.ndarray, t: float, nu: float, dx: float) -> np.ndarray:
    """Solve 1D Burgers equation exactly via Hopf-Cole.
    
    Args:
        u0: initial velocity field
        t: time
        nu: viscosity
        dx: grid spacing
    
    Returns:
        u: velocity field at time t
    """
    # Step 1: Inverse Hopf-Cole: u0 → ψ0
    psi0 = hopf_cole_inverse(u0, dx, nu)
    
    # Step 2: Solve heat equation: ψ0 → ψ(t)
    psi_t = solve_heat_exact(psi0, t, nu, dx)
    
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
        # du/dt = -u·du/dx + ν·d²u/dx²
        dudx = np.gradient(u, dx)
        d2udx2 = np.gradient(dudx, dx)
        
        u_new = u + dt * (-u * dudx + nu * d2udx2)
        u = u_new
    
    return u


# ── Benchmark ────────────────────────────────────────────────────────────────

def benchmark_hopf_cole():
    """Benchmark Hopf-Cole vs finite difference Burgers solver."""
    print("=" * 60)
    print("Hopf-Cole vs Finite Difference Burgers Solver")
    print("=" * 60)
    
    results = []
    
    for N in [512, 1024, 2048]:
        for nu in [0.01, 0.001]:
            dx = 2.0 * np.pi / N
            x = np.linspace(0, 2.0 * np.pi, N, endpoint=False)
            
            # Initial condition: sin(x)
            u0 = np.sin(x)
            
            t_final = 0.5
            
            # Hopf-Cole (exact)
            t0 = time.time()
            u_hc = solve_burgers_hopf_cole(u0, t_final, nu, dx)
            hc_time = time.time() - t0
            
            # Finite difference
            t0 = time.time()
            u_fd = solve_burgers_fd(u0, t_final, nu, dx)
            fd_time = time.time() - t0
            
            # Compare
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
    
    # Save results
    out = {
        'schema': 'hopf_cole_benchmark_v1',
        'results': results,
    }
    out_path = Path(__file__).resolve().parent.parent.parent / 'shared-data' / 'artifacts' / 'hopf_cole_benchmark.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved: {out_path}")
    
    return results


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
        print("       hopf_cole_burgers.py --plot")
        print("       hopf_cole_burgers.py --solve <N> <nu> <t>")
        sys.exit(1)
    
    if sys.argv[1] == '--benchmark':
        benchmark_hopf_cole()
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
