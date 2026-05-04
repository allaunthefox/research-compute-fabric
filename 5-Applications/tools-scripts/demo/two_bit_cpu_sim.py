#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
2-Bit CPU Simulator: Deterministic, auditable, minimal.
- Only ADD, SUB, NOP, HALT instructions
- 2-bit registers (values 0-3, wrap on overflow/underflow)
- Every tick and state change logged
- Program and log are human-readable
- Manifest with hashes and environment info

Usage:
  python3 two_bit_cpu_sim.py program.txt

Example program.txt:
ADD 1 2  # reg0 = reg0 + reg1
SUB 0 1  # reg0 = reg0 - reg1
NOP
HALT

"""

import sys
import hashlib
import json
import platform
from datetime import datetime
from dag_recorder import DAGRecorder

REG_BITS = 2
REG_MAX = (1 << REG_BITS) - 1


class TwoBitCPU:
    def __init__(self, num_registers=2, dag_path='dag_log.jsonl'):
        self.reg = [0] * num_registers
        self.tick = 0
        self.halted = False
        self.log = []
        self.dag = DAGRecorder(dag_path)

    def log_state(self, op, args):
        entry = {
            'tick': self.tick,
            'op': op,
            'args': args,
            'registers': self.reg.copy()
        }
        self.log.append(entry)
        self.dag.record(self.tick, op, args, self.reg)

    def step(self, op, args):
        if self.halted:
            return
        if op == 'ADD':
            a, b = int(args[0]), int(args[1])
            self.reg[a] = (self.reg[a] + self.reg[b]) & REG_MAX
        elif op == 'SUB':
            a, b = int(args[0]), int(args[1])
            self.reg[a] = (self.reg[a] - self.reg[b]) & REG_MAX
        elif op == 'NOP':
            pass
        elif op == 'HALT':
            self.halted = True
        else:
            raise ValueError(f"Unknown op: {op}")
        self.log_state(op, args)
        self.tick += 1

    def run(self, program):
        pc = 0
        while pc < len(program) and not self.halted:
            op, *args = program[pc]
            self.step(op, args)
            pc += 1
        self.dag.dump()

    def dump_log(self, path):
        with open(path, 'w') as f:
            for entry in self.log:
                f.write(f"tick={entry['tick']} op={entry['op']} args={entry['args']} reg={entry['registers']}\n")

    def state_hash(self):
        m = hashlib.sha256()
        for entry in self.log:
            m.update(str(entry).encode())
        return m.hexdigest()

def parse_program(path):
    program = []
    with open(path) as f:
        for line in f:
            line = line.split('#')[0].strip()
            if not line:
                continue
            parts = line.split()
            op = parts[0].upper()
            args = parts[1:]
            program.append([op] + args)
    return program


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 two_bit_cpu_sim.py program.txt")
        sys.exit(1)
    prog_path = sys.argv[1]
    program = parse_program(prog_path)
    dag_path = 'dag_log.jsonl'
    cpu = TwoBitCPU(dag_path=dag_path)
    cpu.run(program)
    log_path = 'cpu_log.txt'
    cpu.dump_log(log_path)
    manifest = {
        'program_file': prog_path,
        'log_file': log_path,
        'dag_file': dag_path,
        'final_registers': cpu.reg,
        'total_ticks': cpu.tick,
        'state_hash': cpu.state_hash(),
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    with open('cpu_manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] Simulation complete. Log: {log_path}, DAG: {dag_path}, Manifest: cpu_manifest.json")

if __name__ == '__main__':
    main()
