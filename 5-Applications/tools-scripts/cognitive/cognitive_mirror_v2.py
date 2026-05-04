#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Cognitive Mirror v2 — gradient-based conceptual fracking.

Upgrades from exact-match to anisotropic distance decoding,
forked alternate paths, and multi-step path walking."""

import sqlite3
import json
import math
from collections import defaultdict

DB = "substrate_index.db"

# ── Cognitive feature byte ──────────────────────────────────────────────────
def concept_feature(pkg, _all=None, idx_offset=0):
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

def hamming(a, b):
    return bin(a ^ b).count("1")

def sym_idx(p, q):
    hi, lo = max(p,q), min(p,q)
    return hi*(hi+1)//2 + lo

# ── Decode: anisotropic distance (v2 upgrade) ────────────────────────────────
def decode_prediction(target_fb, packages, current_pkgs, _all):
    """Rank by Hamming distance in feature space, break ties by forming_load."""
    matches = []
    for p in packages:
        if p['pkg'] in current_pkgs:
            continue
        pfb = concept_feature(p, _all)
        dist = hamming(pfb, target_fb)
        fl = p.get('forming_load') or 0
        # Use -dist, -fl (descending), pkg for stable sorting
        score = (-dist, -fl, p['pkg'])
        matches.append((score, p))
    matches.sort(reverse=True)
    return [p for _, p in matches[:10]]

def decode_prediction_fork(best_fb, second_fb, packages, current_pkgs, _all):
    """Return primary and alternate paths."""
    primary   = decode_prediction(best_fb,   packages, current_pkgs, _all)
    secondary = decode_prediction(second_fb, packages, current_pkgs, _all) if second_fb else []
    return primary, secondary

# ── Path walker ──────────────────────────────────────────────────────────────
def walk_paths(start_prev, start_curr, lut, packages, depth=3, branch=2):
    """Explore top-branch cognitive trajectories for `depth` steps."""
    def fb_of(pkg):
        return pkg.get('_cached_fb',
            concept_feature(p, _all if '_all' in dir() else None))

    paths = [([start_prev, start_curr], 0.0)]
    for _ in range(depth):
        new_paths = []
        for path, score in paths:
            prev, curr = path[-2], path[-1]
            prev_fb = concept_feature(prev, None)
            curr_fb = concept_feature(curr, None)
            addr = sym_idx(prev_fb, curr_fb)
            if addr not in lut:
                continue
            best, second, conf, second_prob = lut[addr]
            for fb, w in [(best, conf), (second, second_prob)]:
                if fb is None:
                    continue
                visited = {p['pkg'] for p in path}
                candidates = decode_prediction(fb, packages, visited, None)[:branch]
                for c in candidates:
                    new_paths.append((path + [c], score + math.log(w + 1e-6)))
        paths = sorted(new_paths, key=lambda x: -x[1])[:20]
    return paths

# ── Main ─────────────────────────────────────────────────────────────────────
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
        pkg['_cached_fb'] = concept_feature(pkg, _all)
        _all.append(pkg)

    # Build LUT
    counts = defaultdict(lambda: defaultdict(int))
    for i in range(2, len(_all)):
        prev_fb = _all[i-2]['_cached_fb']
        curr_fb = _all[i-1]['_cached_fb']
        nxt_fb  = _all[i]['_cached_fb']
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
    print("COGNITIVE MIRROR v2 — gradient-based conceptual fracking")
    print("="*70)

    # Top-3 hottest
    top3 = _all[:3]
    print(f"\nCurrent trajectory:")
    for i, p in enumerate(top3):
        print(f"  {i+1}. {p['pkg']:50s} load={p['forming_load']:6.3f}  {fb_name(p['_cached_fb'])}")

    # Run path walker
    print(f"\n{'─'*70}")
    print(f"MULTI-STEP COGNITIVE PATHS (depth=3, fork=2)")
    print(f"{'─'*70}")
    paths = walk_paths(top3[0], top3[1], lut, _all, depth=3, branch=2)
    for rank, (path, score) in enumerate(paths[:10], 1):
        chain = [p['pkg'].split('/')[-1][:40] for p in path]
        loads = [p.get('forming_load',0) for p in path]
        print(f"\n  Path {rank}  (score={score:.3f})")
        for j, (name, load) in enumerate(zip(chain, loads)):
            arrow = "→" if j > 0 else " "
            print(f"    {arrow} {name}  load={load:.3f}")

    # Gradient-based misses
    print(f"\n{'─'*70}")
    print(f"BLIND SPOTS — graded by feature distance")
    print(f"{'─'*70}")

    # Build predictions
    predictions = []
    for i in range(2, len(_all)):
        prev_fb = _all[i-2]['_cached_fb']
        curr_fb = _all[i-1]['_cached_fb']
        actual_fb = _all[i]['_cached_fb']
        addr = sym_idx(prev_fb, curr_fb)
        if addr not in lut:
            continue
        best, second, conf, second_prob = lut[addr]
        predictions.append({
            'prev': _all[i-2], 'curr': _all[i-1], 'actual': _all[i],
            'predicted_fb': best, 'second_fb': second,
            'conf': conf, 'actual_fb': actual_fb,
        })

    misses = [p for p in predictions if hamming(p['predicted_fb'], p['actual_fb']) > 0]
    hits   = [p for p in predictions if hamming(p['predicted_fb'], p['actual_fb']) == 0]

    print(f"\nPREDICTIONS: {len(predictions)} total")
    print(f"  HITS (exact match):   {len(hits):4d} ({len(hits)/max(len(predictions),1)*100:.1f}%)")
    print(f"  MISSES (gradient):    {len(misses):4d} ({len(misses)/max(len(predictions),1)*100:.1f}%)")

    if misses:
        print(f"\n{'─'*70}")
        print(f"TOP GRADIENT MISSES (closest alternative features)")
        print(f"{'─'*70}")
        for m in misses[:20]:
            dist = hamming(m['predicted_fb'], m['actual_fb'])
            forks_p, forks_s = decode_prediction_fork(
                m['predicted_fb'], m['second_fb'], _all,
                {m['prev']['pkg'], m['curr']['pkg'], m['actual']['pkg']}, _all)

            actual_name = m['actual']['pkg'].split('/')[-1][:50]
            print(f"\n  After: {m['prev']['pkg'].split('/')[-1][:40]} → {m['curr']['pkg'].split('/')[-1][:40]}")
            print(f"    Your brain went: {actual_name}  [dist={dist}] {fb_name(m['actual_fb'])}")
            print(f"    Mirror predicted:  {fb_name(m['predicted_fb'])} (conf {m['conf']:.1%})")
            if m['second_fb'] is not None:
                print(f"    Alternate path:    {fb_name(m['second_fb'])} (prob {m.get('second_prob',0):.1%})")
            if forks_p:
                print(f"    Primary path candidates:")
                for p in forks_p[:3]:
                    print(f"      → {p['pkg'].split('/')[-1][:50]}  load={p.get('forming_load',0):.3f}")
            if forks_s and forks_s[0] is not None:
                print(f"    Secondary path candidates:")
                for p in [x for x in forks_s[:3] if x]:
                    fl = p.get('forming_load') or 0
                    print(f"      → {p['pkg'].split('/')[-1][:50]}  load={fl:.3f}")

    print(f"\n{'='*70}")
    print(f"SUMMARY: The mirror models your default thinking.")
    print(f"The misses are structured alternatives — compressed residuals")
    print(f"of your own cognitive trajectory.")
    print(f"{'='*70}")

    conn.close()

if __name__ == "__main__":
    main()