#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Cognitive Mirror — predict the next concept your brain would go to,
using the same sym_idx + feature_byte mechanics as the Hutter v3 oracle,
but run over substrate_index.db's semantic vectors.

The hits = your natural cognitive flow.
The misses = connections you can't see on your own."""

import sqlite3
import json
import math
from collections import defaultdict
import sys

DB = "substrate_index.db"

# ── Cognitive feature byte: same 8-bit concept but for ideas, not bytes ──
#   Each concept in the database is classified by:
#   bit 0: ACTIVE    (forming_load > 1.0 = still hot)
#   bit 1: CRYSTALLIZED (tier in SETTLED/COMPRESSED = crystallized)
#   bit 2: CONNECTED (has deps on other packages)
#   bit 3: DEEP      (load > 2.0 = high cognitive pressure)
#   bit 4: HYPOTHESIS (concept_anchor says seed/forming)
#   bit 5: BRIDGE    (spans multiple domains via concept_vector similarity)
#   bit 6: RECENT    (indexed in last N commits/packages)
#   bit 7: CORE      (domain is COMPUTE or substrate)

def concept_feature(pkg):
    """Compute 8-bit cognitive feature byte for a package."""
    fb = 0
    fl = pkg.get('forming_load') or 0
    tier = (pkg.get('tier') or '').upper()

    if fl > 1.0:       fb |= 0b00000001  # ACTIVE
    if tier in ('FOAM', 'CRYSTALLINE', 'SINGULARITY'): fb |= 0b00000010  # CRYSTALLIZED
    if pkg.get('dependencies'):          fb |= 0b00000100  # CONNECTED
    if fl > 2.0:       fb |= 0b00001000  # DEEP
    anchor = pkg.get('concept_anchor') or ''
    if 'SEED' in anchor or 'FORMING' in anchor: fb |= 0b00010000  # HYPOTHESIS
    if pkg.get('concept_vector'):        fb |= 0b00100000  # BRIDGE
    idx = pkg.get('_index', 0)
    if idx > len(_all) - 50:             fb |= 0b01000000  # RECENT
    dom = pkg.get('domain', '').upper()
    if dom in ('COMPUTE', 'SUBSTRATE'):  fb |= 0b10000000  # CORE
    return fb

# ── Triangular pairing (same as mirror.rs) ──
def sym_idx(p, q):
    lo = min(p, q)
    hi = max(p, q)
    return hi * (hi + 1) // 2 + lo

# ── Build the LUT from the corpus ──
def build_lut(packages):
    """Build cognitive mirror LUT: for each (prev_fb, curr_fb) pair,
    store the most frequent next_fb."""
    counts = defaultdict(lambda: defaultdict(int))
    for i in range(2, len(packages)):
        prev = concept_feature(packages[i-2])
        curr = concept_feature(packages[i-1])
        nxt  = concept_feature(packages[i])
        addr = sym_idx(prev, curr)
        counts[addr][nxt] += 1

    # Freeze: pick most common next
    lut = {}
    for addr, next_counts in counts.items():
        best = max(next_counts.items(), key=lambda x: x[1])[0]
        total = sum(next_counts.values())
        confidence = next_counts[best] / total
        # Also get second best for "what you're NOT thinking"
        sorted_nexts = sorted(next_counts.items(), key=lambda x: -x[1])
        second = sorted_nexts[1][0] if len(sorted_nexts) > 1 else None
        second_prob = sorted_nexts[1][1] / total if len(sorted_nexts) > 1 else 0
        lut[addr] = (best, second, confidence, second_prob)
    return lut

def predict_next(prev_pkg, curr_pkg, _all):
    """Predict what concept comes next after the current trajectory."""
    prev_fb = concept_feature(prev_pkg)
    curr_fb = concept_feature(curr_pkg)
    addr = sym_idx(prev_fb, curr_fb)
    return addr

# ── Decode: find packages that match a predicted feature byte ──
def decode_prediction(target_fb, packages, current_pkgs):
    """Find packages whose feature byte matches the prediction,
    but that aren't in the current cognitive trajectory."""
    matches = []
    for p in packages:
        if p['pkg'] in current_pkgs:
            continue
        pfb = concept_feature(p)
        if pfb == target_fb:
            matches.append(p)
    return sorted(matches, key=lambda x: -(x.get('forming_load') or 0))

# ── Main frack ──
_all = []

def main():
    global _all
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Get all packages with semantic data, ordered by forming_load (hot first)
    cur.execute("""
        SELECT pkg, version, domain, concept_anchor, concept_vector,
               idea_weights, forming_load, confirmed_load, layer, tier,
               tags, description
        FROM packages
        WHERE concept_vector IS NOT NULL OR concept_anchor IS NOT NULL
        ORDER BY forming_load DESC
    """)
    rows = cur.fetchall()

    _all = [{
        'pkg': r[0], 'version': r[1], 'domain': r[2],
        'concept_anchor': r[3],
        'concept_vector': json.loads(r[4]) if r[4] else [],
        'idea_weights': json.loads(r[5]) if r[5] else {},
        'forming_load': r[6], 'confirmed_load': r[7],
        'layer': r[8], 'tier': r[9],
        'tags': json.loads(r[10]) if r[10] else [],
        'description': (r[11] or '')[:200],
    } for r in rows]

    # Index them
    for i, p in enumerate(_all):
        p['_index'] = i

    print("=" * 70)
    print("COGNITIVE MIRROR — predicting your next concept")
    print("=" * 70)

    # Build LUT
    lut = build_lut(_all)
    print(f"\nLUT size: {len(lut)} unique transitions learned")

    # Run predictions: for each pair of consecutive hot concepts,
    # predict what comes next
    predictions = []
    for i in range(2, len(_all)):
        prev = _all[i-2]
        curr = _all[i-1]
        actual = _all[i]
        addr = predict_next(prev, curr, _all)
        if addr in lut:
            predicted_fb, second_fb, confidence, second_prob = lut[addr]
            actual_fb = concept_feature(actual)
            hit = (predicted_fb == actual_fb)
            predictions.append({
                'prev': prev['pkg'], 'prev_fb': feature_name(concept_feature(prev)),
                'curr': curr['pkg'], 'curr_fb': feature_name(concept_feature(curr)),
                'predicted_fb': predicted_fb,
                'second_fb': second_fb,
                'actual': actual['pkg'],
                'actual_fb': feature_name(actual_fb),
                'hit': hit,
                'confidence': confidence,
            })

    hits = [p for p in predictions if p['hit']]
    misses = [p for p in predictions if not p['hit']]

    print(f"\n{'─' * 70}")
    print(f"PREDICTIONS: {len(predictions)} total")
    print(f"  HITS:    {len(hits):4d} ({len(hits)/max(len(predictions),1)*100:.1f}%) — natural cognitive flow")
    print(f"  MISSES:  {len(misses):4d} ({len(misses)/max(len(predictions),1)*100:.1f}%) — connections you can't see")

    # The misses are the interesting part
    if misses:
        print(f"\n{'─' * 70}")
        print(f"BLIND SPOTS (misses) — connections you're NOT seeing")
        print(f"{'─' * 70}")
        for m in misses[:15]:
            print(f"\n  After: {m['prev']} → {m['curr']}")
            print(f"    Your brain went: {m['actual']}")
            print(f"    Mirror predicted: {feature_name(m['predicted_fb'])} "
                  f"(confidence {m['confidence']:.1%})")
            # Find what packages have that predicted feature
            predicted_pkgs = decode_prediction(
                m['predicted_fb'], _all,
                {m['prev'], m['curr'], m['actual']}
            )
            if predicted_pkgs:
                print(f"    You should also look at:")
                for pkg in predicted_pkgs[:3]:
                    print(f"      → {pkg['pkg']} (load={pkg.get('forming_load', 0):.3f}, "
                          f"domain={pkg['domain']})")

    # The hits show your natural flow
    if hits[:5]:
        print(f"\n{'─' * 70}")
        print(f"NATURAL FLOW (hits) — where your brain naturally goes")
        print(f"{'─' * 70}")
        for h in hits[:10]:
            print(f"  {h['prev']} → {h['curr']} → {h['actual']}  "
                  f"(predicted {h['actual_fb']}, confidence {h['confidence']:.1%})")

    conn.close()

def feature_name(fb):
    """Decode an 8-bit cognitive feature byte to readable name."""
    parts = []
    if fb & 0b10000000: parts.append('CORE')
    if fb & 0b01000000: parts.append('RECENT')
    if fb & 0b00100000: parts.append('BRIDGE')
    if fb & 0b00010000: parts.append('HYPOTHESIS')
    if fb & 0b00001000: parts.append('DEEP')
    if fb & 0b00000100: parts.append('CONNECTED')
    if fb & 0b00000010: parts.append('CRYSTALLIZED')
    if fb & 0b00000001: parts.append('ACTIVE')
    return '+'.join(parts) if parts else 'NULL'

if __name__ == "__main__":
    main()