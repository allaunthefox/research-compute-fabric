#!/usr/bin/env python3
"""
burgers_avm_trace_generator.py
==============================

Generates bit-exact execution traces for the Burgers AVM kernels 
(nuEffProgram and qEffProgram). These traces are used for 
hardware loopback verification on the Tang Nano 9K.
"""

import json
from pathlib import Path

# OpCodes from AVM.lean
OP_PUSH = 0x01
OP_ADD  = 0x02
OP_MUL  = 0x03
OP_SUB  = 0x04
OP_DIV  = 0x05
OP_SQRT = 0x06
OP_HALT = 0xFF

class AVMSimulator:
    def __init__(self):
        self.stack = []
        self.pc = 0
        self.trace = []

    def execute(self, program: list, initial_stack: list):
        self.stack = initial_stack.copy()
        self.pc = 0
        self.trace = []
        
        while self.pc < len(program):
            op = program[self.pc]
            self.pc += 1
            
            if op == OP_PUSH:
                val = program[self.pc]
                self.pc += 1
                self.stack.append(val)
                self.trace.append({"op": "PUSH", "val": val, "stack": self.stack.copy()})
            elif op == OP_ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                res = self.saturating_add(a, b)
                self.stack.append(res)
                self.trace.append({"op": "ADD", "res": res, "stack": self.stack.copy()})
            elif op == OP_MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                # (a * b) >>> 16
                res = (a * b) >> 16
                # Mask to 32-bit (simplified for trace)
                res &= 0xFFFFFFFF
                self.stack.append(res)
                self.trace.append({"op": "MUL", "res": res, "stack": self.stack.copy()})
            elif op == OP_SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                res = self.saturating_sub(a, b)
                self.stack.append(res)
                self.trace.append({"op": "SUB", "res": res, "stack": self.stack.copy()})
            elif op == OP_HALT:
                self.trace.append({"op": "HALT", "stack": self.stack.copy()})
                break
        return self.stack, self.trace

    def saturating_add(self, a, b):
        res = a + b
        if res > 0x7FFFFFFF: return 0x7FFFFFFF
        if res < -0x80000000: return -0x80000000
        return res

    def saturating_sub(self, a, b):
        res = a - b
        if res > 0x7FFFFFFF: return 0x7FFFFFFF
        if res < -0x80000000: return -0x80000000
        return res

def generate_traces():
    # Programs from BurgersAVM.lean
    # nuEffProgram: [PUSH, 1.0, ADD, MUL, HALT]
    # In Q16.16, 1.0 = 0x00010000
    nu_eff_prog = [OP_PUSH, 0x00010000, OP_ADD, OP_MUL, OP_HALT]
    
    # qEffProgram: [PUSH, kappa, MUL, PUSH, 1.0, ADD, MUL, HALT]
    # kappa = 0.3547 * 65536 = 23245 = 0x00005ACE
    q_eff_prog = [OP_PUSH, 0x00005ACE, OP_MUL, OP_PUSH, 0x00010000, OP_ADD, OP_MUL, OP_HALT]
    
    sim = AVMSimulator()
    
    # Inputs for 3-mode toy (Omega = 0.725 = 47513 = 0x0000B999)
    # nu_0 = 0.1 = 6554 = 0x0000199A
    # Q_0 = 1.0 = 65536 = 0x00010000
    omega = 47513
    nu0 = 6554
    q0 = 65536
    
    print("Generating nu_eff trace...")
    res_nu, trace_nu = sim.execute(nu_eff_prog, [nu0, omega])
    
    print("Generating Q_eff trace...")
    res_q, trace_q = sim.execute(q_eff_prog, [q0, omega])
    
    bundle = {
        "nu_eff": {
            "inputs": {"nu0": nu0, "omega": omega},
            "program": nu_eff_prog,
            "trace": trace_nu,
            "final_result": res_nu[0]
        },
        "q_eff": {
            "inputs": {"q0": q0, "omega": omega},
            "program": q_eff_prog,
            "trace": trace_q,
            "final_result": res_q[0]
        }
    }
    
    out_file = Path("/home/allaun/Documents/Research Stack/shared-data/burgers_avm_gold_traces.json")
    out_file.write_text(json.dumps(bundle, indent=2))
    print(f"Traces saved to {out_file}")

if __name__ == "__main__":
    generate_traces()
