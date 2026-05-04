#!/usr/bin/env python3
"""
burgers_avm_benchmark.py
========================

Validates the bit-exact informatic integrity of the Burgers AVM kernels.
Compares the Python AVM reference to the closed-form math for ν_eff and Q_eff.

Doctrine: Zero-float, Q16.16 saturating arithmetic.
"""

import json
import math
from dataclasses import dataclass

# =============================================================================
# 1. Q16.16 Fixed-Point Core (Reference)
# =============================================================================

def to_q16(val):
    return int(val * 65536)

def from_q16(val):
    return val / 65536.0

def qadd(a, b):
    res = a + b
    if res > 0x7FFFFFFF: return 0x7FFFFFFF
    if res < -0x80000000: return -0x80000000
    return res

def qsub(a, b):
    res = a - b
    if res > 0x7FFFFFFF: return 0x7FFFFFFF
    if res < -0x80000000: return -0x80000000
    return res

def qmul(a, b):
    # (a/2^16) * (b/2^16) * 2^16 = (a*b)/2^16
    res = (a * b) >> 16
    if res > 0x7FFFFFFF: return 0x7FFFFFFF
    if res < -0x80000000: return -0x80000000
    return res

def qdiv(a, b):
    if b == 0: return 0
    res = (a << 16) // b
    if res > 0x7FFFFFFF: return 0x7FFFFFFF
    if res < -0x80000000: return -0x80000000
    return res

# =============================================================================
# 2. AVM Reference Engine
# =============================================================================

class AVM:
    def __init__(self, program):
        self.program = program
        self.stack = []
        self.pc = 0

    def step(self):
        if self.pc >= len(self.program):
            return False
        
        instr = self.program[self.pc]
        op = instr["op"]
        
        if op == "push":
            self.stack.append(instr["val"])
        elif op == "add":
            v2 = self.stack.pop()
            v1 = self.stack.pop()
            self.stack.append(qadd(v1, v2))
        elif op == "mul":
            v2 = self.stack.pop()
            v1 = self.stack.pop()
            self.stack.append(qmul(v1, v2))
        elif op == "sub":
            v2 = self.stack.pop()
            v1 = self.stack.pop()
            self.stack.append(qsub(v1, v2))
        
        self.pc += 1
        return True

    def run(self, max_steps=100):
        for _ in range(max_steps):
            if not self.step():
                break
        return self.stack[-1] if self.stack else None

# =============================================================================
# 3. Burgers Kernels
# =============================================================================

def get_nu_eff_program(nu0, omega):
    return [
        {"op": "push", "val": omega},
        {"op": "push", "val": to_q16(1.0)},
        {"op": "add",  "val": None},
        {"op": "push", "val": nu0},
        {"op": "mul",  "val": None},
    ]

def get_q_eff_program(q0, kappa, omega):
    return [
        {"op": "push", "val": omega},
        {"op": "push", "val": kappa},
        {"op": "mul",  "val": None},
        {"op": "push", "val": to_q16(1.0)},
        {"op": "add",  "val": None},
        {"op": "push", "val": q0},
        {"op": "mul",  "val": None},
    ]

# =============================================================================
# 4. Main Benchmark
# =============================================================================

def main():
    # Parameters from BurgersHarmonicPeelingVerification.md
    kappa = to_q16(0.3547)
    nu0   = to_q16(0.01)
    q0    = to_q16(0.1)
    
    # Toy omega for S(x) = sin(x) + 0.3sin(2x) + 0.1sin(3x)
    # Omega = 0.5 * (1^2 * 1.0^2 + 2^2 * 0.3^2 + 3^2 * 0.1^2)
    # Omega = 0.5 * (1.0 + 0.36 + 0.09) = 0.5 * 1.45 = 0.725
    omega = to_q16(0.725)
    
    print(f"--- Burgers AVM Benchmark ---")
    print(f"ν0    : {from_q16(nu0):.6f}")
    print(f"Q0    : {from_q16(q0):.6f}")
    print(f"κ     : {from_q16(kappa):.6f}")
    print(f"Ω     : {from_q16(omega):.6f}")
    print()

    # 1. ν_eff
    nu_prog = get_nu_eff_program(nu0, omega)
    avm_nu = AVM(nu_prog)
    nu_eff_avm = avm_nu.run()
    
    # Golden
    nu_eff_gold = qmul(nu0, qadd(to_q16(1.0), omega))
    
    print(f"[ν_eff] AVM : {hex(nu_eff_avm)} ({from_q16(nu_eff_avm):.6f})")
    print(f"[ν_eff] Gold: {hex(nu_eff_gold)} ({from_q16(nu_eff_gold):.6f})")
    print(f"Match: {nu_eff_avm == nu_eff_gold}")
    print()

    # 2. Q_eff
    q_prog = get_q_eff_program(q0, kappa, omega)
    avm_q = AVM(q_prog)
    q_eff_avm = avm_q.run()
    
    # Golden
    q_eff_gold = qmul(q0, qadd(to_q16(1.0), qmul(kappa, omega)))
    
    print(f"[Q_eff] AVM : {hex(q_eff_avm)} ({from_q16(q_eff_avm):.6f})")
    print(f"[Q_eff] Gold: {hex(q_eff_gold)} ({from_q16(q_eff_gold):.6f})")
    print(f"Match: {q_eff_avm == q_eff_gold}")
    print()

if __name__ == "__main__":
    main()
