#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Cognitive Wheel — roulette-style view of your cognitive basin.

Shows the 'table' of possible next concepts:
- HOUSE bets: your natural trajectory (high probability, same basin)
- PLAYER bets: alternative paths (lower probability, escape routes)
- ZERO: unexplored territory (no transition in LUT)

Uses the cognitive mirror v2 but presents it as a roulette wheel
of conceptual choices."""

import sqlite3
import json
import math
from collections import defaultdict

DB = "substrate_index.db"

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

    # Build LUT
    counts = defaultdict(lambda: defaultdict(int))
    for i in range(2, len(_all)):
        prev_fb = concept_feature(_all[i-2], _all)
        curr_fb = concept_feature(_all[i-1], _all)
        nxt_fb  = concept_feature(_all[i], _all)
        addr = sym_idx(prev_fb, curr_fb)
        counts[addr][nxt_fb] += 1
    lut = {}
    for addr, nc in counts.items():
        best = max(nc.items(), key=lambda x: x[1])[0]
        total = sum(nc.values())
        conf = nc[best] / total
        sorted_nc = sorted(nc.items(), key=lambda x: -x[1])
        second = sorted_nc[1][0] if len(sorted_nc) > 1 else None
        second_prob = sorted_nc[1][1]/total if len(sorted_nc) > 1 else 0
        lut[addr] = (best, second, conf, second_prob)

    print("="*70)
    print("COGNITIVE WHEEL — roulette table of your conceptual choices")
    print("="*70)

    # Top-5 hottest concepts = your current position on the wheel
    top5 = _all[:5]
    print(f"\nCurrent position (hottest 5 concepts):")
    for i, p in enumerate(top5):
        fb = concept_feature(p, _all)
        print(f"  {i+1}. {p['pkg'].split('/')[-1][:45]:<45} load={p['forming_load']:6.3f}")

    # For each hot concept pair, show the wheel
    for pair_idx in range(min(3, len(top5)-2)):
        prev = top5[pair_idx]
        curr = top5[pair_idx+1]
        prev_fb = concept_feature(prev, _all)
        curr_fb = concept_feature(curr, _all)
        addr = sym_idx(prev_fb, curr_fb)

        if addr not in lut:
            continue

        best, second, conf, second_prob = lut[addr]

        print(f"\n{'─'*70}")
        print(f"ROULETTE: {prev['pkg'].split('/')[-1][:35]} → {curr['pkg'].split('/')[-1][:35]}")
        print(f"{'─'*70}")

        # HOUSE bet: your natural trajectory
        house_pkgs = [p for p in _all if concept_feature(p, _all) == best][:5]
        print(f"\n  🏠 HOUSE (p={conf:.1%}) — your natural flow:")
        for p in house_pkgs:
            dist = hamming(concept_feature(p, _all), best)
            print(f"     [{dist:1d}] {p['pkg'].split('/')[-1][:50]}  load={p.get('forming_load',0):.3f}")

        # PLAYER bet: alternative paths
        if second is not None:
            player_pkgs = [p for p in _all if concept_feature(p, _all) == second][:5]
            print(f"\n  🎯 PLAYER (p={second_prob:.1%}) — escape route:")
            for p in player_pkgs:
                dist = hamming(concept_feature(p, _all), second)
                print(f"     [{dist:1d}] {p['pkg'].split('/')[-1][:50]}  load={p.get('forming_load',0):.3f}")

        # ZERO: unexplored — concepts that match neither
        # Find high-load concepts NOT in house or player
        house_feats = {best}
        if second:
            house_feats.add(second)
        zero_pkgs = [p for p in _all[:50] if concept_feature(p, _all) not in house_feats]
        if zero_pkgs:
            print(f"\n  00  ZERO — unexplored territory:")
            for p in zero_pkgs[:3]:
                fb = concept_feature(p, _all)
                print(f"     [{fb_name(fb)}] {p['pkg'].split('/')[-1][:50]}  load={p.get('forming_load',0):.3f}")

        print(f"\n  {'─'*66}")
        print(f"  The house edge is {conf:.1%} — your brain defaults to this path.")
        print(f"  The player bet (1-{conf:.1%} = {1-conf:.1%}) is the alternative.")
        print(f"  Zero is the concept you haven't connected yet.")

    print(f"\n{'='*70}")
    print("HOW TO USE: The house always wins unless you deliberately")
    print("bet against it. The 'player bets' show where your brain")
    print("could go next if you step sideways instead of following")
    print("your strongest associations.")
    print("="*70)

    conn.close()

if __name__ == "__main__":
    main()