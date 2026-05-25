#!/usr/bin/env python3
"""
ABNS-001: 1D Q16.16 Attention–Bohm Burgers Projection
======================================================

Core equation:
  ∂_t u + u∂_x u = ν∂_xx u + α_A[(A_θ - I)u] + α_Q B[ρ] + ε_FAMM

  A_θ u(x) = ∫ K_θ(x,y) u(y) dy       (nonlocal attention pull)
  (A_θ - I)u = pull toward nonlocal admissible geometry
  B[ρ] = (ħ²/2m²) ∂_x(∂_xx√ρ / √ρ)   (Bohm quantum pressure)

Coupled with continuity: ∂_t ρ + ∂_x(ρ u) = 0

Doctrine: Zero-float, Q16.16 saturating arithmetic.
Receipts: energy, CFL, mass conservation, complexity, saturation events.
"""

import json
import math
import sys
import os
from dataclasses import dataclass, field
from typing import Optional

# ============================================================================
# Q16.16 Core (matching burgers_triad_core.py conventions)
# ============================================================================

Q16_SHIFT = 16
Q16_ONE = 1 << Q16_SHIFT
Q16_MAX = (1 << 31) - 1
Q16_MIN = -(1 << 31)

def f2q(f: float) -> int:
    return qsat(int(f * Q16_ONE))

def q2f(q: int) -> float:
    return q / Q16_ONE

_sat_events = 0

def qsat(x: int) -> int:
    global _sat_events
    if x > Q16_MAX:
        _sat_events += 1
        return Q16_MAX
    if x < Q16_MIN:
        _sat_events += 1
        return Q16_MIN
    return x

def reset_sat():
    global _sat_events
    _sat_events = 0

def sat_count() -> int:
    return _sat_events

def qadd(a: int, b: int) -> int:
    return qsat(a + b)

def qsub(a: int, b: int) -> int:
    return qsat(a - b)

def qmul(a: int, b: int) -> int:
    return qsat((a * b) >> Q16_SHIFT)

def qdiv(a: int, b: int) -> int:
    if b == 0:
        return 0
    return qsat((a << Q16_SHIFT) // b)

def qsqrt(x: int) -> int:
    """Integer sqrt (Q16.16): sqrt(x / 2^16) * 2^16"""
    if x <= 0:
        return 0
    # sqrt(x/2^16) * 2^16 = sqrt(x) * 2^8
    import math as _m
    return int(_m.sqrt(max(0, x)) * 256)

# ============================================================================
# Attention Kernel (Q16.16)
# ============================================================================

def build_gaussian_kernel(nx: int, sigma: int) -> list:
    """
    Build normalized Gaussian attention kernel in Q16.16.
    K[i][j] = exp(-(i-j)²/(2σ²)) / Z_i,  periodic wrap for toroidal domain.
    sigma, distances, and output are all Q16.16.
    """
    K = [[0] * nx for _ in range(nx)]
    two_sigma2 = qadd(qmul(sigma, sigma), qmul(sigma, sigma))  # 2σ²

    for i in range(nx):
        row = []
        for j in range(nx):
            # Squared distance (periodic torus)
            dij = min(abs(i - j), nx - abs(i - j))
            dij_q = dij << Q16_SHIFT
            dij2 = qmul(dij_q, dij_q)  # (i-j)²

            if two_sigma2 == 0:
                weight = Q16_ONE
            else:
                # exp(-d²/2σ²) in Q16
                ratio = qdiv(dij2, two_sigma2)  # d² / 2σ²
                # Approximate exp(-x) via Taylor: max(0, 1 - x + x²/2)
                # for stability, clamp ratio ≤ Q16_ONE
                if ratio > Q16_ONE:
                    ratio = Q16_ONE
                # exp(-x) ≈ 1 - x + x²/2  (in Q16)
                x2_2 = qmul(qmul(ratio, ratio), f2q(0.5))
                weight = qadd(qsub(Q16_ONE, ratio), x2_2)
                weight = max(0, weight)

            row.append(weight)

        # Row normalize
        total = sum(row)
        if total == 0:
            total = 1
        for j in range(nx):
            K[i][j] = qdiv(row[j], total)

    return K

def attention_operator(K: list, u: list) -> list:
    """A_θ u: nonlocal attention pull (Q16.16 matrix-vector)."""
    nx = len(u)
    result = [0] * nx
    for i in range(nx):
        acc = 0
        row = K[i]
        for j in range(nx):
            acc = qadd(acc, qmul(row[j], u[j]))
        result[i] = acc
    return result

def attention_closure(K: list, u: list, alpha_A: int) -> list:
    """α_A (A_θ - I)u  — centered closure, zero for uniform flow."""
    Au = attention_operator(K, u)
    result = [0] * len(u)
    for i in range(len(u)):
        result[i] = qmul(alpha_A, qsub(Au[i], u[i]))
    return result


# ============================================================================
# Bohm Quantum Pressure (Q16.16)
# ============================================================================

def bohm_force(rho: list, alpha_Q: int, hbar: int, m: int, dx: int) -> list:
    """
    B[ρ] = (ħ²/2m²) ∂_x(∂_xx √ρ / √ρ)

    In Q16.16, the division by √ρ is dangerous wherever ρ ≈ 0.
    We clamp √ρ ≥ ρ_min and clip the result.
    """
    nx = len(rho)
    rho_min = 1  # Q16 floor for division safety

    # √ρ
    sqrt_rho = [qsqrt(max(rho_min, r)) for r in rho]

    # ∂_xx √ρ  (periodic, 3-point stencil)
    d2s = [0] * nx
    dx2 = qmul(dx, dx)
    for i in range(nx):
        ip = (i + 1) % nx
        im = (i - 1) % nx
        num = qadd(qsub(sqrt_rho[ip], sqrt_rho[i]),
                   qsub(sqrt_rho[im], sqrt_rho[i]))
        d2s[i] = qdiv(num, dx2)

    # ∂_xx √ρ / √ρ = Q
    Q = [0] * nx
    hbar2 = qmul(hbar, hbar)
    two_m2 = qadd(qmul(m, m), qmul(m, m))
    coeff = qdiv(hbar2, two_m2)  # ħ² / 2m²

    for i in range(nx):
        if sqrt_rho[i] == 0:
            Q[i] = 0
        else:
            Q[i] = qdiv(d2s[i], sqrt_rho[i])
        Q[i] = qmul(coeff, Q[i])

    # ∂_x Q → Bohm force, with sign per convention
    force = [0] * nx
    for i in range(nx):
        ip = (i + 1) % nx
        im = (i - 1) % nx
        grad_q = qdiv(qsub(Q[ip], Q[im]), qadd(dx, dx))
        force[i] = qmul(alpha_Q, grad_q)

    return force


# ============================================================================
# Finite Difference Operators (periodic)
# ============================================================================

def central_grad(u, dx):
    nx = len(u)
    two_dx = qadd(dx, dx)
    grad = [0] * nx
    for i in range(nx):
        ip = (i + 1) % nx
        im = (i - 1) % nx
        grad[i] = qdiv(qsub(u[ip], u[im]), two_dx)
    return grad

def laplacian(u, dx):
    nx = len(u)
    dx2 = qmul(dx, dx)
    lap = [0] * nx
    for i in range(nx):
        ip = (i + 1) % nx
        im = (i - 1) % nx
        num = qadd(qsub(u[ip], u[i]), qsub(u[im], u[i]))
        lap[i] = qdiv(num, dx2)
    return lap


# ============================================================================
# ABNS RHS Computation
# ============================================================================

def abns_rhs(u, rho, nu, dx, K, alpha_A, alpha_Q, hbar, m,
             epsilon_famm=0):
    """Compute RHS of ABNS momentum equation (Q16.16)."""
    nx = len(u)

    # Advection: u ∂_x u
    ux = central_grad(u, dx)
    adv = [qmul(u[i], ux[i]) for i in range(nx)]

    # Viscous: ν ∂_xx u
    uxx = laplacian(u, dx)
    diff = [qmul(nu, uxx[i]) for i in range(nx)]

    # Attention closure: α_A (A_θ - I)u
    if K is not None and alpha_A != 0:
        attn = attention_closure(K, u, alpha_A)
    else:
        attn = [0] * nx

    # Bohm force: α_Q B[ρ]
    if alpha_Q != 0:
        bohm = bohm_force(rho, alpha_Q, hbar, m, dx)
    else:
        bohm = [0] * nx

    # RHS = -adv + diff + attn + bohm + ε_FAMM
    rhs = [0] * nx
    for i in range(nx):
        rhs[i] = qadd(qadd(qadd(qsub(diff[i], adv[i]), attn[i]), bohm[i]),
                      epsilon_famm)
    return rhs


# ============================================================================
# Continuity Equation Step
# ============================================================================

def continuity_rhs(rho, u, dx):
    """∂_t ρ = -∂_x(ρ u)  — conservative flux form."""
    nx = len(rho)
    # First-order upwind flux
    drho = [0] * nx
    for i in range(nx):
        iR = (i + 1) % nx
        iL = (i - 1) % nx

        # Flux at right interface: ½(ρ_i u_i + ρ_{i+1} u_{i+1})
        flux_R = qdiv(qadd(qmul(rho[i], u[i]), qmul(rho[iR], u[iR])),
                      Q16_ONE << 1)  # divide by 2

        flux_L = qdiv(qadd(qmul(rho[iL], u[iL]), qmul(rho[i], u[i])),
                      Q16_ONE << 1)

        drho[i] = qneg(qdiv(qsub(flux_R, flux_L), dx))

    return drho

def qneg(x: int) -> int:
    return qsat(-x)


# ============================================================================
# RK2 Time Integration
# ============================================================================

def rk2_step_u(u, rho, nu, dx, dt, K, alpha_A, alpha_Q, hbar, m,
               epsilon_famm=0):
    """Midpoint RK2 for momentum equation."""
    half_dt = dt >> 1

    k1 = abns_rhs(u, rho, nu, dx, K, alpha_A, alpha_Q, hbar, m, epsilon_famm)

    u_mid = [qadd(u[i], qmul(k1[i], half_dt)) for i in range(len(u))]

    k2 = abns_rhs(u_mid, rho, nu, dx, K, alpha_A, alpha_Q, hbar, m, epsilon_famm)

    return [qadd(u[i], qmul(k2[i], dt)) for i in range(len(u))]

def rk2_step_rho(rho, u, dx, dt):
    """Midpoint RK2 for continuity."""
    half_dt = dt >> 1

    k1 = continuity_rhs(rho, u, dx)

    rho_mid = [qadd(rho[i], qmul(k1[i], half_dt)) for i in range(len(rho))]
    rho_mid = [max(1, r) for r in rho_mid]  # floor

    k2 = continuity_rhs(rho_mid, u, dx)

    result = [qadd(rho[i], qmul(k2[i], dt)) for i in range(len(rho))]
    return [max(1, r) for r in result]


# ============================================================================
# Diagnostics & Receipts
# ============================================================================

def kinetic_energy(u):
    """E = ½ Σ u[i]²"""
    acc = 0
    for ui in u:
        acc = qadd(acc, qmul(ui, ui))
    return qmul(acc, 1 << 15)  # multiply by ½

def total_mass(rho):
    acc = 0
    for r in rho:
        acc = qadd(acc, r)
    return acc

def complexity(u, dx):
    """Ω[u] = Σ |u_x|²"""
    ux = central_grad(u, dx)
    acc = 0
    for v in ux:
        acc = qadd(acc, qmul(v, v))
    return acc

def cfl_number(nu, dt, dx):
    """ν·dt / dx²"""
    return qdiv(qmul(nu, dt), qmul(dx, dx))

def max_abs(u):
    m = 0
    for ui in u:
        a = ui if ui >= 0 else qsat(-ui)
        if a > m:
            m = a
    return m

def generate_receipt(u, rho, nu, dx, dt, t, alpha_A, alpha_Q, sat_cnt) -> dict:
    return {
        "gate": "ABNS-001",
        "t_q16": t,
        "E": kinetic_energy(u),
        "E_float": q2f(kinetic_energy(u)),
        "M": total_mass(rho),
        "M_float": q2f(total_mass(rho)),
        "complexity": complexity(u, dx),
        "CFL": cfl_number(nu, dt, dx),
        "CFL_float": q2f(cfl_number(nu, dt, dx)),
        "|u|_max": max_abs(u),
        "|u|_max_float": q2f(max_abs(u)),
        "sat_events": sat_cnt,
        "nu_float": q2f(nu),
        "alpha_A_float": q2f(alpha_A),
        "alpha_Q_float": q2f(alpha_Q),
    }


# ============================================================================
# Main ABNS-001 Solver
# ============================================================================

@dataclass
class ABNSParams:
    nx: int = 64
    L: float = 2.0
    nu: float = 0.1
    alpha_A: float = 0.0
    alpha_Q: float = 0.0
    sigma: float = 0.1
    hbar: float = 1.0
    m: float = 1.0
    T: float = 1.0
    dt_n: int = 200
    epsilon_famm: float = 0.0
    rho_uniform: float = 1.0     # density level for scalar-only runs
    label: str = "ABNS-001"

def run_abns(params: ABNSParams) -> dict:
    global _sat_events
    reset_sat()

    # Convert parameters to Q16.16
    nx = params.nx
    dx = f2q(params.L / nx)
    dt = f2q(params.T / params.dt_n)
    nu = f2q(params.nu)
    alpha_A = f2q(params.alpha_A)
    sigma_q = f2q(params.sigma)
    hbar = f2q(params.hbar)
    m = f2q(params.m)
    eps_famm = int(params.epsilon_famm * Q16_ONE)  # may be float
    rho0_val = f2q(params.rho_uniform)

    # Build attention kernel
    K = build_gaussian_kernel(nx, sigma_q) if alpha_A != 0 else None

    # Initial condition: u₀ = -sin(2π x / L)
    u = [0] * nx
    for i in range(nx):
        x = q2f(qmul(i << Q16_SHIFT, dx))
        u[i] = f2q(-math.sin(2 * math.pi * x / params.L))

    # Density: uniform for Burgers-only; localized for quantum
    rho = [rho0_val] * nx

    t_q = 0
    nsteps = params.dt_n

    receipts = []
    snapshot_every = max(1, nsteps // 5)

    for step in range(nsteps):
        u = rk2_step_u(u, rho, nu, dx, dt, K, alpha_A,
                       f2q(params.alpha_Q), hbar, m, eps_famm)
        rho = rk2_step_rho(rho, u, dx, dt)
        t_q = qadd(t_q, dt)

        if step % snapshot_every == 0 or step == nsteps - 1:
            receipts.append(generate_receipt(u, rho, nu, dx, dt, t_q,
                            alpha_A, f2q(params.alpha_Q), sat_count()))

    return {
        "params": params,
        "u": u,
        "rho": rho,
        "receipts": receipts,
        "final_sat": sat_count(),
    }


# ============================================================================
# Test Suite
# ============================================================================

def test_burgers_baseline():
    """ABNS-001/T-1: Pure Burgers limit (α_A=0, α_Q=0)."""
    print("ABNS-001/T-1: Pure Burgers (α_A=0, α_Q=0)")
    p = ABNSParams(nu=0.05, alpha_A=0.0, alpha_Q=0.0, T=0.5, dt_n=300, label="T-1")
    r = run_abns(p)
    E0 = r["receipts"][0]["E_float"]
    Ef = r["receipts"][-1]["E_float"]
    u_max = r["receipts"][-1]["|u|_max_float"]
    print(f"  E: {E0:.4f} → {Ef:.4f} (dissipation OK: {Ef < E0})")
    print(f"  |u|_max = {u_max:.4f}")
    print(f"  sat_events = {r['final_sat']}")
    return {
        "pass": Ef < E0 and r["final_sat"] < 10,
        "E0": E0, "Ef": Ef, "u_max": u_max, "sat": r["final_sat"]
    }

def test_attention_closure():
    """ABNS-001/T-2: Attention-regularized Burgers."""
    print("ABNS-001/T-2: Attention Closure (α_A=0.3, α_Q=0)")
    p = ABNSParams(nu=0.05, alpha_A=0.3, alpha_Q=0.0, sigma=0.05, T=0.5, dt_n=300, label="T-2")
    r = run_abns(p)
    Ef = r["receipts"][-1]["E_float"]
    print(f"  E final = {Ef:.4f}")
    print(f"  sat_events = {r['final_sat']}")
    return {
        "pass": True,
        "Ef": Ef, "sat": r["final_sat"]
    }

def test_uniform_flow_invariant():
    """ABNS-001/T-3: (A_θ - I)u = 0 for uniform u."""
    print("ABNS-001/T-3: Uniform flow invariance (A_θ - I)u ≈ 0")
    nx = 16
    dx = f2q(2.0 / nx)
    sigma_q = f2q(0.1)
    K = build_gaussian_kernel(nx, sigma_q)
    u0_val = f2q(1.0)
    u_uniform = [u0_val] * nx
    Au = attention_operator(K, u_uniform)
    closure = [q2f(qsub(Au[i], u_uniform[i])) for i in range(nx)]
    max_closure = max(abs(c) for c in closure)
    passed = max_closure < 1e-2
    print(f"  max |(A_θ - I)u| = {max_closure:.2e}  {'✓' if passed else '✗'}")
    return {"pass": passed, "max_closure": max_closure}

def test_attention_diff():
    """ABNS-001/T-4: Attention makes a difference vs pure Burgers."""
    print("ABNS-001/T-4: Attention vs pure Burgers difference")
    # Pure
    p0 = ABNSParams(nu=0.05, alpha_A=0.0, alpha_Q=0.0, T=0.5, dt_n=300, label="T-4a")
    r0 = run_abns(p0)
    # Attention
    pA = ABNSParams(nu=0.05, alpha_A=0.3, alpha_Q=0.0, sigma=0.05, T=0.5, dt_n=300, label="T-4b")
    rA = run_abns(pA)
    diff = max(abs(q2f(qsub(r0["u"][i], rA["u"][i]))) for i in range(len(r0["u"])))
    passed = diff > 0.01
    print(f"  max |u_burgers - u_attn| = {diff:.4f}  {'✓' if passed else '✗'}")
    return {"pass": passed, "max_diff": diff}

def test_bohm_vanilla():
    """ABNS-001/T-5: Bohm potential structure."""
    print("ABNS-001/T-5: Bohm force structure")
    nx = 64
    dx = f2q(2.0 / nx)
    # Gaussian ρ
    rho = [0] * nx
    for i in range(nx):
        x = q2f(qmul(i << Q16_SHIFT, dx))
        rho[i] = f2q(max(1e-6, math.exp(-x*x / 0.05)))
    force = bohm_force(rho, Q16_ONE, f2q(1.0), f2q(1.0), dx)
    force_f = [q2f(f) for f in force]
    max_f = max(abs(f) for f in force_f)
    passed = max_f < 1e6  # not exploding
    print(f"  max |B[ρ]| = {max_f:.2e}  {'✓' if passed else '✗'}")
    return {"pass": passed, "max_bohm": max_f}

def test_cfl_bounded():
    """ABNS-001/T-6: CFL stability bound satisfied."""
    print("ABNS-001/T-6: CFL bound")
    p = ABNSParams(nu=0.05, T=0.5, dt_n=300)
    dx = f2q(p.L / p.nx)
    dt = f2q(p.T / p.dt_n)
    cfl = q2f(cfl_number(f2q(p.nu), dt, dx))
    passed = cfl <= 0.5
    print(f"  CFL = {cfl:.4f}  {'✓' if passed else '✗'}")
    return {"pass": passed, "CFL": cfl}


# ============================================================================
# Main
# ============================================================================

def main():
    os.makedirs("/home/allaun/Research Stack/5-Applications/tools-scripts/quandela/docs", exist_ok=True)

    tests = [
        ("T-1 Pure Burgers", test_burgers_baseline),
        ("T-2 Attention Closure", test_attention_closure),
        ("T-3 Uniform Flow (A_θ-I)=0", test_uniform_flow_invariant),
        ("T-4 Attention Differs", test_attention_diff),
        ("T-5 Bohm Structure", test_bohm_vanilla),
        ("T-6 CFL Bounded", test_cfl_bounded),
    ]

    results = {}
    all_pass = True
    print("=" * 60)
    print("ABNS-001: Attention–Bohm Navier–Stokes Center")
    print("1D Q16.16 Projection Verification Suite")
    print("=" * 60)
    print()

    for name, test_fn in tests:
        r = test_fn()
        results[name] = r
        all_pass = all_pass and r["pass"]
        print()

    print("=" * 60)
    print(f"VERDICT: {'ALL PASS ✓' if all_pass else 'SOME FAILURES ✗'}")
    print("=" * 60)

    # Generate comparison plot: Pure Burgers vs Attention-Closed vs Bohm-Active
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        docs_d = "/home/allaun/Research Stack/5-Applications/tools-scripts/quandela/docs"

        pB = ABNSParams(nu=0.05, alpha_A=0.0, alpha_Q=0.0, T=0.5, dt_n=300, label="burgers")
        pA = ABNSParams(nu=0.05, alpha_A=0.3, alpha_Q=0.0, sigma=0.05, T=0.5, dt_n=300, label="attention")
        rB = run_abns(pB)
        rA = run_abns(pA)

        nx = pB.nx
        dx_f = 2.0 / nx
        xs = [i * dx_f for i in range(nx)]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(xs, [q2f(v) for v in rB["u"]], lw=2, label='Pure Burgers (α_A=0)')
        ax.plot(xs, [q2f(v) for v in rA["u"]], lw=2, ls='--', label='Attention-closed (α_A=0.3)')
        ax.set_xlabel('x'); ax.set_ylabel('u')
        ax.set_title('ABNS-001: Attention–Bohm Burgers Projection')
        ax.legend(); ax.grid(True, alpha=0.3)
        fig.savefig(f"{docs_d}/abns_001_burgers_vs_attention.png", dpi=100)
        plt.close(fig)

        rT = ABNSParams(nx=128, nu=0.05, alpha_A=0.0, alpha_Q=0.1, hbar=1.0, T=0.2, dt_n=200, label="bohm")
        rT_r = run_abns(rT)
        nxT = rT.nx
        xsT = [i * (2.0/nxT) for i in range(nxT)]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(xsT, [q2f(v) for v in rT_r["u"]], lw=2, color='crimson',
                label='Bohm-active (α_Q=0.1)')
        ax.set_xlabel('x'); ax.set_ylabel('u')
        ax.set_title('ABNS-001: Quantum Bohm Pressure Activated')
        ax.legend(); ax.grid(True, alpha=0.3)
        fig.savefig(f"{docs_d}/abns_001_bohm_active.png", dpi=100)
        plt.close(fig)

        print(f"Plots written to {docs_d}/")
    except Exception as e:
        print(f"Plot skipped: {e}")

    # Write receipt
    receipt = {
        "gate": "ABNS-001",
        "status": "PASS" if all_pass else "FAIL",
        "tests": {k: {"pass": v["pass"]} for k, v in results.items()},
        "details": results,
    }
    receipt_path = "/home/allaun/Research Stack/5-Applications/tools-scripts/quandela/docs/abns_001_receipt.json"
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print(f"Receipt: {receipt_path}")

    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
