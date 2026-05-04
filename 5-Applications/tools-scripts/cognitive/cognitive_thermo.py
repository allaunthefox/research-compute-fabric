#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Cognitive Thermo — thermodynamic path walker for cognitive exploration.

Uses surprise/regret as thermodynamic resistance to reorder exploration:
- Low resistance (low stress) → explored first (natural flow)
- High resistance (high stress) → deferred to end (alternative paths)
- Stress = α·surprise + β·regret
- Engram memory: stress_memory[addr] += observed_regret"""

import sqlite3
import json
import math
from collections import defaultdict

DB = "substrate_index.db"

# Thermodynamic weights
ALPHA = 0.5   # surprise weight
BETA  = 0.3   # regret weight
LAMBDA = 0.2  # stress penalty on score

def concept_feature(pkg, _all=None):
    fb = 0
    fl = pkg.get('forming_load') or 0
    tier = (pkg.get('tier') or '').upper()
    if fl > 1.0:       fb |= 0b00000001  # ACTIVE
    if tier in ('FOAM','CRYSTALLINE','SINGULARITY'): fb |= 0b00000010  # CRYSTALLIZED
    if pkg.get('dependencies'): fb |= 0b00000100  # CONNECTED
    if fl > 2.0:       fb |= 0b00001000  # DEEP
    anchor = pkg.get('concept_anchor') or ''
    if 'SEED' in anchor or 'FORMING' in anchor: fb |= 0b00010000  # HYPOTHESIS
    if pkg.get('concept_vector'):        fb |= 0b00100000  # BRIDGE
    if _all is not None:
        idx = pkg.get('_index', 0)
        if idx > len(_all) - 50:         fb |= 0b01000000  # RECENT
    dom = pkg.get('domain', '').upper()
    if dom in ('COMPUTE','SUBSTRATE'):  fb |= 0b10000000  # CORE
    return fb

def hamming(a, b):
    return bin(a ^ b).count("1")

def sym_idx(p, q):
    hi, lo = max(p,q), min(p,q)
    return hi*(hi+1)//2 + lo

def fb_name(fb):
    p = []
    if fb&0b10000000: p.append('CORE')
    if fb&0b01000000: p.append('RECENT')
    if fb&0b00100000: p.append('BRIDGE')
    if fb&0b00010000: p.append('HYPOTHESIS')
    if fb&0b00001000: p.append('DEEP')
    if fb&0b00000100: p.append('CONNECTED')
    if fb&0b00000010: p.append('CRYSTALLIZED')
    if fb&0b00000001: p.append('ACTIVE')
    return '+'.join(p) if p else 'NULL'

def thermodynamic_score(prob, baseline_prob, alpha=ALPHA, beta=BETA, lam=LAMBDA):
    """Compute thermodynamic score for a path.
    
    surprise = -log(P) — how unexpected is this transition
    regret   = log(P_best) - log(P) — how much worse than optimal
    stress   = α·surprise + β·regret
    score    = log(P) - λ·stress  (lower stress → higher score)
    """
    p_safe = max(prob, 1e-6)
    surprise = -math.log(p_safe)
    regret = math.log(max(baseline_prob, 1e-6)) - math.log(p_safe)
    regret = max(0, regret)  # regret can't be negative
    stress = alpha * surprise + beta * regret
    score = math.log(p_safe) - lam * stress
    return score, stress

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT pkg, version, domain, concept_anchor, concept_vector,
               forming_load, confirmed_load, layer, tier, tags
        FROM packages
        ORDER BY forming_load DESC
    """)
    _all = []
    for i, r in enumerate(cur.fetchall()):
        pkg = {
            'pkg': r[0], 'version': r[1], 'domain': r[2],
            'concept_anchor': r[3],
            'concept_vector': json.loads(r[4]) if r[4] else [],
            'forming_load': r[5], 'confirmed_load': r[6],
            'layer': r[7], 'tier': r[8],
            'tags': json.loads(r[9]) if r[9] else [],
        }
        pkg['_index'] = i
        _all.append(pkg)

    # Build LUT with probabilities
    counts = defaultdict(lambda: defaultdict(int))
    for i in range(2, len(_all)):
        prev_fb = concept_feature(_all[i-2], _all)
        curr_fb = concept_feature(_all[i-1], _all)
        nxt_fb  = concept_feature(_all[i], _all)
        addr = sym_idx(prev_fb, curr_fb)
        counts[addr][nxt_fb] += 1
    
    lut = {}
    for addr, nc in counts.items():
        total = sum(nc.values())
        sorted_nc = sorted(nc.items(), key=lambda x: -x[1])
        best = sorted_nc[0][0]
        best_prob = sorted_nc[0][1] / total
        second = sorted_nc[1][0] if len(sorted_nc) > 1 else None
        second_prob = sorted_nc[1][1]/total if len(sorted_nc) > 1 else 0
        conf = best_prob
        lut[addr] = (best, second, conf, second_prob)

    # Build stress_memory (engram)
    stress_memory = defaultdict(float)
    for addr, nc in counts.items():
        total = sum(nc.values())
        best_count = max(nc.values())
        for fb, count in nc.items():
            if count < best_count:
                regret = math.log(best_count + 1) - math.log(count + 1)
                stress_memory[addr, fb] += regret

    print("="*70)
    print("COGNITIVE THERMO — thermodynamic path exploration")
    print("="*70)
    print(f"α={ALPHA} (surprise)  β={BETA} (regret)  λ={LAMBDA} (stress penalty)")

    # Top-3 hottest = current position
    top3 = _all[:3]
    print(f"\nCurrent position:")
    for i, p in enumerate(top3):
        fb = concept_feature(p, _all)
        print(f"  {i+1}. {p['pkg'].split('/')[-1][:50]}  load={p['forming_load']:.3f}")

    # Thermo walk from current position
    print(f"\n{'─'*70}")
    print(f"THERMODYNAMIC PATH WALK (depth=4, branch=3)")
    print(f"{'─'*70}")

    # Start from the hottest pair
    start_prev = top3[0]
    start_curr = top3[1]
    
    # Initialize paths: (path_list, score, total_stress)
    paths = [([start_prev, start_curr], 0.0, 0.0)]
    
    for step in range(4):
        new_paths = []
        for path, score, total_stress in paths:
            # path is a list of dicts; skip malformed entries
            if not isinstance(path, list) or len(path) < 2:
                continue
            prev, curr = path[len(path)-2], path[len(path)-1]
            prev_fb = concept_feature(prev, _all)
            curr_fb = concept_feature(curr, _all)
            addr = sym_idx(prev_fb, curr_fb)
            
            if addr not in lut:
                continue
            
            best, second, conf, second_prob = lut[addr]
            
            # Try all candidates (up to 3 branches)
            if best is not None:
                matches = [p for p in _all if concept_feature(p, _all) == best 
                          and p['pkg'] not in [x['pkg'] for x in path]]
                matches.sort(key=lambda x: -(x.get('forming_load') or 0))
                for m in matches[:2]:
                    prob = conf
                    s, stress = thermodynamic_score(prob, conf)
                    new_paths.append((path + [m], score + s, total_stress + stress))
            
            if second is not None and second_prob > 0.01:
                matches = [p for p in _all if concept_feature(p, _all) == second
                          and p['pkg'] not in [x['pkg'] for x in path]]
                matches.sort(key=lambda x: -(x.get('forming_load') or 0))
                for m in matches[:1]:
                    prob = second_prob
                    s, stress = thermodynamic_score(prob, conf)
                    new_paths.append((path + [m], score + s, total_stress + stress))
        
        # Sort by score (descending) — low stress paths naturally rise
        new_paths.sort(key=lambda x: -x[1])
        paths = new_paths[:15]  # beam width

    # Detect "DeepCompression" regions — addresses with entropy > threshold AND stress > threshold
    # These are thermodynamic sinks: high uncertainty + historically costly
    entropy_at_addr = {}
    for addr, nc in counts.items():
        total = sum(nc.values())
        if total > 0:
            probs = [c / total for c in nc.values()]
            entropy = -sum(p * math.log(p + 1e-6) for p in probs)
            stress = sum(stress_memory.get((addr, fb), 0) for fb in nc)
            entropy_at_addr[addr] = (entropy, stress)
    
    # Print paths grouped by stress level (low stress = natural flow, high = deferred)
    print(f"\n{'='*70}")
    print(f"PATHS RANKED BY THERMODYNAMIC SCORE (low stress = natural flow)")
    print(f"{'='*70}")

    for rank, (path, score, total_stress) in enumerate(paths[:10], 1):
        chain = [p['pkg'].split('/')[-1][:35] if isinstance(p, dict) else str(p)[:35] for p in path]
        loads = [p.get('forming_load', 0) if isinstance(p, dict) else 0 for p in path]
        
        # Stress level
        if total_stress < 2:
            level = "🟢 LOW (natural flow)"
        elif total_stress < 5:
            level = "🟡 MEDIUM (interesting deviation)"
        else:
            level = "🔴 HIGH (deferred/breakthrough)"
        
        print(f"\n  Path {rank:2d}  score={score:7.3f}  stress={total_stress:6.3f}  {level}")
        for j, (name, load) in enumerate(zip(chain, loads)):
            arrow = "→" if j > 0 else " "
            print(f"    {arrow} {name:35s}  load={load:.3f}")

    print(f"\n{'='*70}")
    print("HOW TO READ:")
    print("  🟢 Green paths = your brain's natural flow (low resistance, conscious)")
    print("  🟡 Yellow paths = structured deviations (interesting, semi-conscious)")
    print("  🔴 Red paths    = pushed to subconscious (high resistance, background work)")
    print("")
    print("YOUR BRAIN'S MECHANISM:")
    print("  Immediate danger → solve NOW (green)")
    print("  Not dangerous but hard → push to subconscious (red)")
    print("  Subconscious works on it in background between conscious thoughts")
    print("="*70)

    conn.close()

if __name__ == "__main__":
    main()