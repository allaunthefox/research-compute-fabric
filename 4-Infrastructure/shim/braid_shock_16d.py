#!/usr/bin/env python3
"""
braid_shock_16d.py - 16D BraidShock PrimeFold Simulator with Dimensional Shock Trim (DST)
Implements Q16_16 integer-only arithmetic to model soliton charged front propagation,
folded-prime impedance, reaction drainage, and underverse payment ledger logging.
"""

import sys
import os
import json
import argparse
import hashlib

# Canonical Q16_16 Fixed-Point Arithmetic in Python
class Q16_16:
    SCALE = 65536
    MIN_VAL = -2147483648
    MAX_VAL = 2147483647

    @staticmethod
    def from_float(f: float) -> int:
        return int(max(min(f * Q16_16.SCALE, Q16_16.MAX_VAL), Q16_16.MIN_VAL))

    @staticmethod
    def to_float(val: int) -> float:
        return val / Q16_16.SCALE

    @staticmethod
    def clamp(val: int) -> int:
        if val > Q16_16.MAX_VAL:
            return Q16_16.MAX_VAL
        if val < Q16_16.MIN_VAL:
            return Q16_16.MIN_VAL
        return val

    @staticmethod
    def add(a: int, b: int) -> int:
        return Q16_16.clamp(a + b)

    @staticmethod
    def sub(a: int, b: int) -> int:
        return Q16_16.clamp(a - b)

    @staticmethod
    def mul(a: int, b: int) -> int:
        return Q16_16.clamp((a * b) // Q16_16.SCALE)

    @staticmethod
    def div(a: int, b: int) -> int:
        if b == 0:
            return Q16_16.MAX_VAL
        return Q16_16.clamp((a * Q16_16.SCALE) // b)

    @staticmethod
    def neg(val: int) -> int:
        return Q16_16.clamp(-val)

    @staticmethod
    def abs(val: int) -> int:
        return abs(val) if val != Q16_16.MIN_VAL else Q16_16.MAX_VAL

# Simple 1D array operations for Q16_16 without importing numpy to ensure portability/compatibility
class Q16Array:
    @staticmethod
    def zeros(size: int):
        return [0] * size

    @staticmethod
    def add_arrays(a: list, b: list) -> list:
        return [Q16_16.add(x, y) for x, y in zip(a, b)]

    @staticmethod
    def sub_arrays(a: list, b: list) -> list:
        return [Q16_16.sub(x, y) for x, y in zip(a, b)]

    @staticmethod
    def mul_scalar(a: list, s: int) -> list:
        return [Q16_16.mul(x, s) for x in a]

    @staticmethod
    def grad(a: list) -> list:
        # Central difference with periodic boundary conditions
        size = len(a)
        res = [0] * size
        for i in range(size):
            prev_val = a[i - 1]
            next_val = a[(i + 1) % size]
            # (next - prev) / 2
            res[i] = Q16_16.div(Q16_16.sub(next_val, prev_val), 131072) # 2.0 in Q16_16 is 131072
        return res

    @staticmethod
    def laplacian(a: list) -> list:
        # Second derivative with periodic boundary conditions
        size = len(a)
        res = [0] * size
        for i in range(size):
            prev_val = a[i - 1]
            curr_val = a[i]
            next_val = a[(i + 1) % size]
            # next - 2*curr + prev
            sum_neighbors = Q16_16.add(next_val, prev_val)
            two_curr = Q16_16.mul(curr_val, 131072)
            res[i] = Q16_16.sub(sum_neighbors, two_curr)
        return res

def run_simulation(grid_size: int, steps: int):
    # Primes to construct folded prime potential lattice
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    
    # 1. Precompute Folded-Prime Potential lattice on grid
    phi_p = Q16Array.zeros(grid_size)
    for i in range(grid_size):
        val = 0
        for p in primes:
            # Distance to nearest multiple of prime
            dist = abs((i % p) - p / 2)
            # Add to potential (fixed-point math)
            val = Q16_16.add(val, Q16_16.from_float(1.0 / (dist + 1.0)))
        phi_p[i] = val
    
    # Gradient of prime potential
    grad_phi_p = Q16Array.grad(phi_p)
    
    # Initialize variables
    u = Q16Array.zeros(grid_size) # Velocity
    q = Q16Array.zeros(grid_size) # Front Charge / Admissibility
    r = Q16Array.zeros(grid_size) # Reaction tail
    b = Q16Array.zeros(grid_size) # Underverse bleed ledger
    
    # Initialize a localized initial pressure (Gaussian-like packet in Q16_16)
    for i in range(grid_size):
        dist = min(abs(i - grid_size // 4), grid_size - abs(i - grid_size // 4))
        u[i] = Q16_16.from_float(2.0 / (1.0 + 0.1 * dist * dist))
        q[i] = Q16_16.from_float(1.5 / (1.0 + 0.1 * dist * dist))
        
    # Constant coefficients in Q16_16
    nu = Q16_16.from_float(0.05)    # Viscosity
    beta = Q16_16.from_float(0.01)  # Soliton dispersion
    kappa = Q16_16.from_float(0.15) # Charge self-reinforcement
    lam = Q16_16.from_float(0.1)    # Reaction bleed coefficient
    dt = Q16_16.from_float(0.1)     # Time step
    gamma = Q16_16.from_float(0.08) # Drainage rate
    
    underverse_total_payment = 0
    entropy_total = 0
    discarded_pressure_total = 0

    # 2. Time Evolve
    for step in range(steps):
        # Calculate gradients
        grad_u = Q16Array.grad(u)
        lap_u = Q16Array.laplacian(u)
        grad_lap_u = Q16Array.grad(lap_u)
        
        grad_q = Q16Array.grad(q)
        q_grad_q = [Q16_16.mul(qi, gqi) for qi, gqi in zip(q, grad_q)]
        
        grad_r = Q16Array.grad(r)
        
        # Burgers momentum update:
        # du/dt = -u * grad(u) + nu * lap(u) - grad_phi_p + beta * grad_lap_u + kappa * q_grad_q - lam * grad_r
        du = Q16Array.zeros(grid_size)
        for i in range(grid_size):
            term_advect = Q16_16.mul(u[i], grad_u[i])
            term_visc = Q16_16.mul(nu, lap_u[i])
            term_disp = Q16_16.mul(beta, grad_lap_u[i])
            term_charge = Q16_16.mul(kappa, q_grad_q[i])
            term_drain = Q16_16.mul(lam, grad_r[i])
            
            val = Q16_16.sub(term_visc, term_advect)
            val = Q16_16.sub(val, grad_phi_p[i])
            val = Q16_16.add(val, term_disp)
            val = Q16_16.add(val, term_charge)
            val = Q16_16.sub(val, term_drain)
            du[i] = val
            
        # Update u
        u_next = [Q16_16.add(ui, Q16_16.mul(dui, dt)) for ui, dui in zip(u, du)]
        
        # Charge conservation update with decay at composite/scar lanes (where phi_p has local maxima)
        # dq/dt = -grad(q * u) - bleed_loss
        q_u = [Q16_16.mul(qi, ui) for qi, ui in zip(q, u)]
        grad_qu = Q16Array.grad(q_u)
        
        dq = Q16Array.zeros(grid_size)
        for i in range(grid_size):
            # Bleed loss is proportional to potential (impedance)
            bleed_loss = Q16_16.mul(q[i], Q16_16.mul(phi_p[i], Q16_16.from_float(0.1)))
            dq[i] = Q16_16.sub(Q16_16.neg(grad_qu[i]), bleed_loss)
            
            # Record bleed in ledger
            b[i] = Q16_16.add(b[i], Q16_16.mul(bleed_loss, dt))
            underverse_total_payment += Q16_16.mul(bleed_loss, dt)

        q_next = [Q16_16.add(qi, Q16_16.mul(dqi, dt)) for qi, dqi in zip(q, dq)]
        
        # Reaction tail drainage
        # dr/dt = bleed_loss - gamma * r
        dr = Q16Array.zeros(grid_size)
        for i in range(grid_size):
            bleed_loss = Q16_16.mul(q[i], Q16_16.mul(phi_p[i], Q16_16.from_float(0.1)))
            decay = Q16_16.mul(gamma, r[i])
            dr[i] = Q16_16.sub(bleed_loss, decay)
            
        r_next = [Q16_16.add(ri, Q16_16.mul(dri, dt)) for ri, dri in zip(r, dr)]
        
        # DST: Dimensional Shock Trim - keep only high-amplitude front
        # Dimensions with u < 0.1 are trimmed, adding to ledger
        for i in range(grid_size):
            if u_next[i] < Q16_16.from_float(0.1):
                discarded_pressure_total += u_next[i]
                u_next[i] = 0
                q_next[i] = 0
                r_next[i] = 0
        
        # Calculate step entropy
        for i in range(grid_size):
            if q_next[i] > 0:
                entropy_total += q_next[i] // 100
        
        u = u_next
        q = q_next
        r = r_next

    # Extract surviving path
    surviving_indices = [i for i, ui in enumerate(u) if ui > 0]
    
    # Build metrics receipt
    receipt = {
        "schema": "braid_shock_16d_receipt_v1",
        "grid_size": grid_size,
        "steps": steps,
        "underverse_ledger": {
            "total_bleed_payment_q16": underverse_total_payment,
            "discarded_pressure_q16": discarded_pressure_total,
            "entropy_acc_q16": entropy_total,
            "final_surviving_front_nodes": len(surviving_indices)
        },
        "surviving_path": surviving_indices,
        "u_final_q16": u,
        "q_final_q16": q,
        "r_final_q16": r,
        "b_final_q16": b
    }
    
    # Self-validation check
    data_str = json.dumps(receipt, sort_keys=True)
    receipt_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
    receipt["receipt_sha256"] = receipt_hash
    
    return receipt

def main():
    parser = argparse.ArgumentParser(description="16D BraidShock Simulation")
    parser.parse_arguments = parser.add_argument("--output", type=str, required=True, help="Output JSON receipt path")
    parser.parse_arguments = parser.add_argument("--grid-size", type=int, default=256, help="Simulation grid size")
    parser.parse_arguments = parser.add_argument("--steps", type=int, default=100, help="Simulation steps")
    
    args = parser.parse_args()
    
    print(f"Initializing BraidShock PrimeFold 16D Simulation (grid_size={args.grid_size}, steps={args.steps})...")
    receipt = run_simulation(args.grid_size, args.steps)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(receipt, f, indent=2)
        
    print(f"Simulation complete. Receipt written to {args.output}")
    print(f"Receipt SHA256: {receipt['receipt_sha256']}")

if __name__ == "__main__":
    main()
