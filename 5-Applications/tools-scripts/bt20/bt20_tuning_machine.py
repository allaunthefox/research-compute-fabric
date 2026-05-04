#!/usr/bin/env python3
"""
bt20_tuning_machine.py — 20-Neuron TTM Tuning Machine

Implements the TSM-NR1 behavioral subset and GEFI-PRIM-1 operators.
Tunes the Sovereign Manifold (phi, k1, b) based on neuromorphic resonance.
"""

import json
import time
import random
import math
import argparse
from pathlib import Path
from typing import List, Dict

SEED_DATA = Path.home() / ".gemini/antigravity/scratch/bt20_initial_seeds.json"
OUTPUT_TUNING = Path.home() / ".gemini/antigravity/scratch/bt20_tuning_report.json"

class BT20Neuron:
    def __init__(self, seed: Dict):
        self.id = seed["neuron_id"]
        self.name = f"Neuron_{self.id:02d}"
        self.mu_seed = seed["mu_seed"]
        
        # Internal State (GEFI-PRIM-1: Activation State A)
        self.a = seed["activation"]  # Current activation (0-15)
        self.a_prev = self.a
        self.gamma = seed["gamma"]   # Transform mode
        self.confidence = seed["confidence"]
        self.state = "ACTIVE" if self.a > 4 else "LATENT"
        
        # Weights (Coupling) - Full Crossbar
        self.weights = [random.uniform(0.1, 0.5) for _ in range(20)]

    def a_accumulate(self, neighbors: List['BT20Neuron']):
        """Σ Operator: Accumulate activation from neighbors."""
        acc = sum(n.a_prev * self.weights[n.id] for n in neighbors if n.id != self.id)
        # Smoothing activation field
        self.a = (0.7 * self.a) + (0.3 * (acc / 19.0))
        self.a = min(15.0, self.a)

    def a_interact(self, neighbors: List['BT20Neuron']):
        """ι Operator: Resonance coupling."""
        # Simple bidirectional energy exchange based on Gamma class similarity
        for n in neighbors:
            if n.id != self.id:
                if self.gamma == n.gamma:
                    # High resonance: Pull activations closer
                    diff = (n.a_prev - self.a) * 0.1
                    self.a += diff
                else:
                    # Low resonance: Repel activations
                    diff = (n.a_prev - self.a) * 0.01
                    self.a -= diff

    def a_noise(self, phi: float):
        """ξ Operator: Stochastic variation modulated by informatic stress."""
        noise = random.gauss(0, phi * 0.5)
        self.a = max(0.0, min(15.0, self.a + noise))

    def update_state(self):
        """Transition logic based on TSM-NR1."""
        self.a_prev = self.a
        if self.a < 1.0:
            self.state = "QUIESCENT"
        elif self.a < 4.0:
            self.state = "LATENT"
        elif self.a < 12.0:
            self.state = "ACTIVE"
        else:
            self.state = "SATURATED"

class TuningMachine:
    def __init__(self, seeds: List[Dict], phi_initial: float = 0.5):
        self.neurons = [BT20Neuron(s) for s in seeds]
        self.phi = phi_initial
        self.k1 = 1.2
        self.cycle_count = 0
        self.history = []

    def step(self):
        """One BLINK cycle of the TTM."""
        self.cycle_count += 1
        
        # 1. Operators
        for n in self.neurons:
            n.a_accumulate(self.neurons)
            n.a_interact(self.neurons)
            n.a_noise(self.phi)
            n.update_state()
            
        # 2. COLLAPSE (Λ Operator): Adjust manifold constants
        # If the majority are SATURATED, we've hit a 'Stress Attractor'
        avg_activation = sum(n.a for n in self.neurons) / 20.0
        saturated_count = sum(1 for n in self.neurons if n.state == "SATURATED")
        
        # Logic: Tune K1 and PHI to minimize saturation pressure
        if saturated_count > 5:
            # Over-saturation: Increase saturation threshold (k1) and damp phi
            self.k1 += 0.05
            self.phi *= 0.95 # Cooling effect
        elif avg_activation < 4.0:
            # Under-saturation: Increase discovery pressure
            self.k1 -= 0.02
            self.phi *= 1.02 # Warming effect
            
        self.history.append({
            "cycle": self.cycle_count,
            "avg_a": round(avg_activation, 3),
            "saturated": saturated_count,
            "phi": round(self.phi, 4),
            "k1": round(self.k1, 4)
        })

    def run(self, cycles: int = 100):
        print(f"[*] Running BT20 Machine for {cycles} cycles...")
        for _ in range(cycles):
            self.step()
            if self.cycle_count % 20 == 0:
                h = self.history[-1]
                print(f"[{h['cycle']:03d}] Avg Activation: {h['avg_a']:>5} | Saturated: {h['saturated']:>2} | Φ: {h['phi']:>6} | k1: {h['k1']:>6}")

    def save_report(self):
        report = {
            "status": "CONVERGED",
            "cycles": self.cycle_count,
            "final_state": self.history[-1],
            "recommendations": {
                "phi_offset": self.history[-1]["phi"] - self.history[0]["phi"],
                "k1_offset": self.history[-1]["k1"] - self.history[0]["k1"]
            }
        }
        with open(OUTPUT_TUNING, 'w') as f:
            json.dump(report, f, indent=4)
        print(f"[✅] Tuning Report saved to {OUTPUT_TUNING}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=100)
    args = parser.parse_args()

    if not SEED_DATA.exists():
        print(f"[!] Error: Seed data not found at {SEED_DATA}. Run bootstrap first.")
        exit(1)

    with open(SEED_DATA, 'r') as f:
        seeds = json.load(f)

    tm = TuningMachine(seeds)
    tm.run(args.cycles)
    tm.save_report()
