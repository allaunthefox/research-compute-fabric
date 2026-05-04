#!/usr/bin/env python3
"""Run swarm in monitoring mode to detect plateau"""
import subprocess
import time
import re
from typing import List, Dict

def parse_swarm_output(output: str) -> Dict[str, float]:
    """Parse swarm output to extract key metrics"""
    metrics = {}
    
    # Parse optimization metrics
    opt_ratio_match = re.search(r'Optimization Ratio: ([\d.]+)', output)
    if opt_ratio_match:
        metrics['optimization_ratio'] = float(opt_ratio_match.group(1))
    
    substrate_potential_match = re.search(r'Substrate Potential: ([\d.]+)', output)
    if substrate_potential_match:
        metrics['substrate_potential'] = float(substrate_potential_match.group(1))
    
    opt_cycles_match = re.search(r'Optimization Cycles: (\d+)', output)
    if opt_cycles_match:
        metrics['optimization_cycles'] = int(opt_cycles_match.group(1))
    
    consensus_match = re.search(r'Consensus: ([\d.]+)', output)
    if consensus_match:
        metrics['consensus'] = float(consensus_match.group(1))
    
    homeostasis_match = re.search(r'Homeostasis Score: ([\d.]+)', output)
    if homeostasis_match:
        metrics['homeostasis'] = float(homeostasis_match.group(1))
    
    overall_score_match = re.search(r'Overall System Score: ([\d.]+)', output)
    if overall_score_match:
        metrics['overall_score'] = float(overall_score_match.group(1))
    
    return metrics

def detect_plateau(history: List[Dict[str, float]], window_size: int = 5, threshold: float = 0.01) -> bool:
    """Detect if metrics have plateaued (stopped improving significantly)"""
    if len(history) < window_size:
        return False
    
    # Check optimization ratio plateau
    recent_ratios = [h.get('optimization_ratio', 0) for h in history[-window_size:]]
    ratio_variance = max(recent_ratios) - min(recent_ratios)
    
    # Check overall score plateau
    recent_scores = [h.get('overall_score', 0) for h in history[-window_size:]]
    score_variance = max(recent_scores) - min(recent_scores)
    
    # Plateau if variance is below threshold
    return ratio_variance < threshold and score_variance < threshold

def main():
    print("[INFO] Starting swarm monitoring for plateau detection")
    print("=" * 70)
    
    history: List[Dict[str, float]] = []
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n[CYCLE {cycle}] Running swarm...")
        
        try:
            result = subprocess.run(
                ['python3', 'enhanced_integrated_swarm.py'],
                cwd='/home/allaun/Documents/Research Stack/scripts',
                capture_output=True,
                text=True,
                timeout=60
            )
            
            metrics = parse_swarm_output(result.stdout)
            history.append(metrics)
            
            print(f"  Optimization Ratio: {metrics.get('optimization_ratio', 0):.3f}")
            print(f"  Substrate Potential: {metrics.get('substrate_potential', 0):.1f}")
            print(f"  Optimization Cycles: {metrics.get('optimization_cycles', 0)}")
            print(f"  Consensus: {metrics.get('consensus', 0):.3f}")
            print(f"  Homeostasis: {metrics.get('homeostasis', 0):.3f}")
            print(f"  Overall Score: {metrics.get('overall_score', 0):.3f}")
            
            # Check for plateau
            if detect_plateau(history):
                print("\n[PLATEAU DETECTED]")
                print(f"  Swarm has plateaued after {cycle} cycles")
                print(f"  Final Optimization Ratio: {metrics.get('optimization_ratio', 0):.3f}")
                print(f"  Final Overall Score: {metrics.get('overall_score', 0):.3f}")
                print(f"  Total Optimization Cycles: {metrics.get('optimization_cycles', 0)}")
                break
            
            # Check if fully optimized
            if metrics.get('optimization_ratio', 0) >= 0.9:
                print("\n[FULLY OPTIMIZED]")
                print(f"  Swarm reached optimization ratio {metrics.get('optimization_ratio', 0):.3f}")
                break
            
            # Wait before next cycle
            time.sleep(2)
            
        except subprocess.TimeoutExpired:
            print("[ERROR] Swarm timed out")
            break
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            break

if __name__ == '__main__':
    main()
