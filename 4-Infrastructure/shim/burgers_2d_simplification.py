#!/usr/bin/env python3
"""
burgers_2d_simplification.py — 2D Burgers Equation Multi-core Solver & Helmholtz Decoupling Analysis

Solves the 2D Burgers equation:
  u_t + u*u_x + v*u_y = nu * nabla^2 u
  v_t + u*v_x + v*v_y = nu * nabla^2 v

Decomposes the velocity field into:
  1. Dilatational (curl-free) component: u_d = grad(Phi)
  2. Solenoidal (divergence-free) component: u_s = curl(A)

Tests the mathematical simplification hypothesis that the solenoidal (rotational)
energy decays rapidly compared to the dilatational energy, meaning the flow relaxes
toward the integrable (curl-free) Cole-Hopf manifold.

Uses NumPy's vectorized operations (which automatically run on multi-core OpenBLAS on NixOS).
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

def Helmholtz_decomposition(u: np.ndarray, v: np.ndarray, dx: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Decompose 2D velocity field (u, v) into dilatational and solenoidal parts.
    
    Using spectral/FFT projections:
      k_sq = k_x^2 + k_y^2
      u_d = FFT^-1 [ (k_x * (k_x*u_hat + k_y*v_hat)) / k_sq ]
      v_d = FFT^-1 [ (k_y * (k_x*u_hat + k_y*v_hat)) / k_sq ]
      u_s = u - u_d
      v_s = v - v_d
    """
    Ny, Nx = u.shape
    u_hat = np.fft.fft2(u)
    v_hat = np.fft.fft2(v)
    
    kx = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    ky = 2.0 * np.pi * np.fft.fftfreq(Ny, d=dx)
    Kx, Ky = np.meshgrid(kx, ky)
    
    K_sq = Kx**2 + Ky**2
    K_sq[0, 0] = 1.0  # avoid division by zero
    
    # Projection to dilatational (curl-free) space
    dot_prod = Kx * u_hat + Ky * v_hat
    u_d_hat = (Kx * dot_prod) / K_sq
    v_d_hat = (Ky * dot_prod) / K_sq
    
    # Zero out the mean component
    u_d_hat[0, 0] = 0.0
    v_d_hat[0, 0] = 0.0
    
    u_d = np.real(np.fft.ifft2(u_d_hat))
    v_d = np.real(np.fft.ifft2(v_d_hat))
    
    u_s = u - u_d
    v_s = v - v_d
    
    return u_d, v_d, u_s, v_s

def solve_burgers_2d(
    Nx: int,
    Ny: int,
    nu: float,
    t_final: float,
    dt: float,
    dx: float,
    init_rot_ratio: float,
    save_interval: int = 100
) -> Dict:
    """Solve 2D Burgers and analyze the energy decay profiles."""
    x = np.linspace(0, 2.0 * np.pi, Nx, endpoint=False)
    y = np.linspace(0, 2.0 * np.pi, Ny, endpoint=False)
    X, Y = np.meshgrid(x, y)
    
    # Initialize velocity fields with a mix of curl-free and rotational parts
    # Dilatational part: grad(sin(x)*cos(y))
    u_d_init = np.cos(X) * np.cos(Y)
    v_d_init = -np.sin(X) * np.sin(Y)
    
    # Solenoidal part: curl(sin(x)*sin(y))
    u_s_init = np.sin(X) * np.cos(Y)
    v_s_init = -np.cos(X) * np.sin(Y)
    
    u = u_d_init + init_rot_ratio * u_s_init
    v = v_d_init + init_rot_ratio * v_s_init
    
    n_steps = int(t_final / dt)
    print(f"[*] Simulating 2D Burgers: Grid={Nx}x{Ny}, ν={nu}, Steps={n_steps}, dt={dt}")
    
    kx = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    ky = 2.0 * np.pi * np.fft.fftfreq(Ny, d=dx)
    Kx, Ky = np.meshgrid(kx, ky)
    K_sq = Kx**2 + Ky**2
    
    # Orszag 2/3 dealiasing mask to prevent aliasing blowup
    Kx_max = np.max(np.abs(Kx))
    Ky_max = np.max(np.abs(Ky))
    dealias_mask = (np.abs(Kx) < (2.0 / 3.0) * Kx_max) & (np.abs(Ky) < (2.0 / 3.0) * Ky_max)
    
    history = []
    
    t0 = time.time()
    
    for step in range(1, n_steps + 1):
        t = step * dt
        
        # Spectral representation of current fields
        u_hat = np.fft.fft2(u)
        v_hat = np.fft.fft2(v)
        
        # Compute derivatives in real space for nonlinear terms
        ux = np.real(np.fft.ifft2(1j * Kx * u_hat))
        uy = np.real(np.fft.ifft2(1j * Ky * u_hat))
        vx = np.real(np.fft.ifft2(1j * Kx * v_hat))
        vy = np.real(np.fft.ifft2(1j * Ky * v_hat))
        
        # Nonlinear terms in real space
        Nu = - (u * ux + v * uy)
        Nv = - (u * vx + v * vy)
        
        # Transform nonlinear terms to Fourier space
        Nu_hat = np.fft.fft2(Nu)
        Nv_hat = np.fft.fft2(Nv)
        
        # Semi-implicit Crank-Nicolson update in Fourier space
        denom = 1.0 + 0.5 * nu * dt * K_sq
        u_hat_new = ((u_hat * (1.0 - 0.5 * nu * dt * K_sq) + dt * Nu_hat) / denom) * dealias_mask
        v_hat_new = ((v_hat * (1.0 - 0.5 * nu * dt * K_sq) + dt * Nv_hat) / denom) * dealias_mask
        
        # Transform back to real space
        u = np.real(np.fft.ifft2(u_hat_new))
        v = np.real(np.fft.ifft2(v_hat_new))
        
        if step % save_interval == 0 or step == 1 or step == n_steps:
            # Helmholtz decomposition
            u_d, v_d, u_s, v_s = Helmholtz_decomposition(u, v, dx)
            
            # Compute energies
            E_dilatational = 0.5 * np.mean(u_d**2 + v_d**2)
            E_solenoidal = 0.5 * np.mean(u_s**2 + v_s**2)
            E_total = 0.5 * np.mean(u**2 + v**2)
            
            history.append({
                "step": step,
                "time": t,
                "E_total": float(E_total),
                "E_dilatational": float(E_dilatational),
                "E_solenoidal": float(E_solenoidal),
                "ratio_solenoidal": float(E_solenoidal / max(E_total, 1e-10))
            })
            
            print(f"  [Step {step:05d}] t={t:.3f} | Total E: {E_total:.6f} | Solenoidal E: {E_solenoidal:.6f} ({E_solenoidal/E_total*100:.2f}%)")

    elapsed = time.time() - t0
    print(f"[+] Simulation complete in {elapsed:.2f}s.")
    
    return {
        "grid_size": [Nx, Ny],
        "nu": nu,
        "t_final": t_final,
        "dt": dt,
        "init_rot_ratio": init_rot_ratio,
        "history": history,
        "elapsed_seconds": elapsed
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="2D Burgers Helmholtz Decoupling Analysis")
    parser.add_argument("--grid", type=int, default=256, help="Grid size Nx=Ny")
    parser.add_argument("--nu", type=float, default=0.005, help="Viscosity")
    parser.add_argument("--steps", type=int, default=1000, help="Number of steps")
    parser.add_argument("--dt", type=float, default=0.0005, help="Time step")
    parser.add_argument("--init-rot", type=float, default=1.0, help="Initial solenoidal ratio")
    parser.add_argument("--output", default="burgers_2d_simplification_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    dx = 2.0 * np.pi / args.grid
    t_final = args.steps * args.dt
    
    res = solve_burgers_2d(
        Nx=args.grid,
        Ny=args.grid,
        nu=args.nu,
        t_final=t_final,
        dt=args.dt,
        dx=dx,
        init_rot_ratio=args.init_rot,
        save_interval=args.steps // 10
    )
    
    # Save receipt
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
    print(f"[+] Output receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
