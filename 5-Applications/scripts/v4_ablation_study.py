#!/usr/bin/env python3
"""
V4 Ablation Study

Re-runs the V4 simulation with three configurations:
1. Speed only (no pause, no exposure window, no contacts, no transient bias)
2. Speed + delay (pause and exposure window, but no contacts, no transient bias)
3. Speed + delay + transient bias + contacts (full V4)

This tests whether structural bias becomes significant in V4.
"""

import numpy as np
import json
from typing import List, Dict
from v4_cotranslational_simulator import (
    V4CotranslationalSimulator, Codon, ExpertType, create_test_sequence
)


class V4AblationSimulator(V4CotranslationalSimulator):
    """Extended simulator with ablation modes"""
    
    def __init__(
        self,
        sequence: List[Codon],
        mode: str = "full",  # "speed_only", "speed_delay", "full"
        **kwargs
    ):
        super().__init__(sequence, **kwargs)
        self.mode = mode
    
    def pause_field(self, t: float) -> float:
        """Override based on mode"""
        if self.mode == "speed_only":
            return 0.0  # No pause
        return super().pause_field(t)
    
    def exposed_segment(self, t: float):
        """Override based on mode"""
        if self.mode == "speed_only":
            # No exposure window - return all translated residues
            m = self.visible_prefix_length(t)
            return self.translated_residues[:m]
        return super().exposed_segment(t)
    
    def contact_probability(self, i: int, j: int, t: float) -> float:
        """Override based on mode"""
        if self.mode in ["speed_only", "speed_delay"]:
            return 0.0  # No contacts
        return super().contact_probability(i, j, t)
    
    def transient_bias(self, expert_type: ExpertType, t: float, window_size: int = 5) -> float:
        """Override based on mode"""
        if self.mode in ["speed_only", "speed_delay"]:
            return 0.0  # No transient bias
        return super().transient_bias(expert_type, t, window_size)
    
    def expert_weights(self, t: float) -> Dict[ExpertType, float]:
        """Override based on mode"""
        if self.mode == "speed_only":
            # Simplified: uniform weights
            weights = {
                ExpertType.HELIX: 0.33,
                ExpertType.SHEET: 0.33,
                ExpertType.LOOP: 0.34
            }
            return weights
        return super().expert_weights(t)


def run_ablation_configuration(mode: str, sequence: List[Codon]) -> Dict:
    """Run simulation with specific ablation configuration"""
    print(f"\n{'='*70}")
    print(f"V4 ABLATION: {mode.upper()}")
    print(f"{'='*70}")
    
    sim = V4AblationSimulator(sequence, mode=mode, exposed_length=5)
    
    # Run simulation
    print(f"\nRunning simulation...")
    print(f"{'Time':>8} | {'Translated':>10} | {'Exposed':>7} | {'Pause':>6} | {'Contact':>7} | {'Score':>6}")
    print("-" * 70)
    
    t = 0.0
    dt = 0.5
    max_time = 10.0
    
    results = []
    
    while t < max_time:
        sim.step(dt)
        
        m = sim.visible_prefix_length(t)
        E = sim.exposed_segment(t)
        P = sim.pause_field(t)
        Pi = sim.get_contact_average(t)
        score = sim.get_cds_score(t)
        
        print(f"{t:8.2f} | {m:10d} | {len(E):7d} | {P:6.3f} | {Pi:7.3f} | {score:6.3f}")
        
        results.append({
            "time": t,
            "translated": m,
            "exposed": len(E),
            "pause": P,
            "contact": Pi,
            "score": score
        })
        
        t += dt
    
    # Summary statistics
    final_score = results[-1]["score"]
    avg_pause = np.mean([r["pause"] for r in results])
    avg_contact = np.mean([r["contact"] for r in results])
    score_std = np.std([r["score"] for r in results])
    
    print(f"\nSummary for {mode}:")
    print(f"  Final CDS Score: {final_score:.4f}")
    print(f"  Average Pause Field: {avg_pause:.4f}")
    print(f"  Average Contact Probability: {avg_contact:.4f}")
    print(f"  Score Std Dev: {score_std:.4f}")
    
    return {
        "mode": mode,
        "final_score": final_score,
        "avg_pause": avg_pause,
        "avg_contact": avg_contact,
        "score_std": score_std,
        "trajectory": results
    }


def run_ablation_study():
    """Run full ablation study comparing all configurations"""
    print("=" * 70)
    print("V4 ABLATION STUDY")
    print("=" * 70)
    print("\nComparing three configurations:")
    print("1. Speed only (baseline)")
    print("2. Speed + delay (pause and exposure window)")
    print("3. Speed + delay + transient bias + contacts (full V4)")
    
    # Create test sequence
    sequence = create_test_sequence()
    print(f"\nCreated test sequence with {len(sequence)} codons")
    
    # Run all configurations
    results = {}
    
    results["speed_only"] = run_ablation_configuration("speed_only", sequence)
    results["speed_delay"] = run_ablation_configuration("speed_delay", sequence)
    results["full"] = run_ablation_configuration("full", sequence)
    
    # Compare results
    print("\n" + "=" * 70)
    print("ABLATION STUDY RESULTS")
    print("=" * 70)
    
    print(f"\n{'Configuration':>20} | {'Final Score':>12} | {'Avg Pause':>10} | {'Avg Contact':>13} | {'Score Std':>11}")
    print("-" * 70)
    
    for mode, data in results.items():
        print(f"{mode:>20} | {data['final_score']:12.4f} | {data['avg_pause']:10.4f} | {data['avg_contact']:13.4f} | {data['score_std']:11.4f}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    speed_only_score = results["speed_only"]["final_score"]
    speed_delay_score = results["speed_delay"]["final_score"]
    full_score = results["full"]["final_score"]
    
    speed_delay_delta = speed_delay_score - speed_only_score
    full_delta = full_score - speed_only_score
    
    print(f"\nScore Changes:")
    print(f"  Speed only → Speed+Delay: {speed_delay_delta:+.4f}")
    print(f"  Speed only → Full V4:      {full_delta:+.4f}")
    
    # Contact effect
    contact_only_delta = full_score - speed_delay_score
    print(f"  Speed+Delay → Full V4:    {contact_only_delta:+.4f} (contact + bias effect)")
    
    # Interpretation
    print("\nInterpretation:")
    
    if abs(speed_delay_delta) < 0.01:
        print("  - Pause/exposure window has minimal effect on score")
    elif speed_delay_delta > 0:
        print("  - Pause/exposure window improves score")
    else:
        print("  - Pause/exposure window reduces score")
    
    if abs(contact_only_delta) < 0.01:
        print("  - Contacts + transient bias have minimal effect")
    elif contact_only_delta > 0:
        print("  - Contacts + transient bias improve score")
        print("  - This suggests structural bias is becoming significant in V4")
    else:
        print("  - Contacts + transient bias reduce score")
    
    # Variance analysis
    speed_only_std = results["speed_only"]["score_std"]
    full_std = results["full"]["score_std"]
    
    if full_std > speed_only_std:
        print(f"  - Full V4 increases score variance ({speed_only_std:.4f} → {full_std:.4f})")
        print("  - This suggests cotranslational dynamics create more diverse trajectories")
    else:
        print(f"  - Full V4 reduces score variance ({speed_only_std:.4f} → {full_std:.4f})")
        print("  - This suggests cotranslational dynamics stabilize trajectories")
    
    print("\n" + "=" * 70)
    print("ABLATION STUDY COMPLETE")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    results = run_ablation_study()
    
    # Save results
    output_path = "/home/allaun/Documents/Research Stack/data/v4_ablation_study_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
