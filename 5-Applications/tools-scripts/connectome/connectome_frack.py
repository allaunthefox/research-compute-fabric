#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Connectome Frack — run C. elegans connectome topology as a raw filter
through the substrate_index.db to reveal structure beneath semantic compression.

The connectome provides the wiring diagram.  The packages are the content.
The frack is: which packages fire together when the connectome runs?"""

import sqlite3
import json
import sys
from collections import defaultdict

DB = "substrate_index.db"

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Grab everything with semantic metadata
    cur.execute("""
        SELECT pkg, version, domain, concept_anchor, concept_vector,
               idea_weights, nd_point, forming_load, confirmed_load,
               layer, tier, tags, description
        FROM packages
        WHERE concept_vector IS NOT NULL OR concept_anchor IS NOT NULL
        ORDER BY pkg
    """)
    rows = cur.fetchall()
    print(f"Packages with semantic data: {len(rows)}")

    # Build neuron objects
    neurons = []
    by_domain = defaultdict(list)
    for row in rows:
        (pkg, ver, domain, anchor, cv, iw, nd,
         fl, cl, layer, tier, tags, desc) = row
        neuron = {
            'pkg': pkg, 'version': ver, 'domain': domain,
            'anchor': anchor,
            'concept_vector': json.loads(cv) if cv else [],
            'idea_weights': json.loads(iw) if iw else {},
            'forming_load': fl, 'confirmed_load': cl,
            'layer': layer, 'tier': tier,
            'tags': json.loads(tags) if tags else [],
            'description': (desc or '')[:120],
        }
        neurons.append(neuron)
        by_domain[domain].append(neuron)

    # The connectome filter: sort each domain by cognitive load
    # Highest forming_load = most "on fire" — ideas actively shifting
    # Lowest forming_load = settled/compressed — no longer processing

    print(f"\n{'='*70}")
    print(f"CONNECTOME FRACK — raw structure beneath semantic compression")
    print(f"{'='*70}")

    total_active = 0
    for domain in sorted(by_domain):
        pkgs = by_domain[domain]
        active = [p for p in pkgs if p['forming_load'] is not None]
        settled = [p for p in pkgs if p['forming_load'] is None]

        print(f"\n{'─'*70}")
        print(f"GANGLION: {domain}")
        print(f"  Neurons: {len(pkgs)}  "
              f"Active/Forming: {len(active)}  "
              f"Settled/Compressed: {len(settled)}")

        if active:
            total_active += len(active)
            active.sort(key=lambda x: -(x['forming_load'] or 0))
            print(f"\n  ╔═ ACTIVE / FORMING (load > 0) ═╗")
            for p in active[:10]:
                load = p['forming_load']
                tier = p['tier'] or '?'
                anchor = (p['anchor'] or 'none')[:60]
                print(f" ║ {p['pkg']:40s}  load={load:6.3f}  tier={tier:10s}")
                print(f" ║   ↳ {anchor}")
            if len(active) > 10:
                print(f"  ║   ... and {len(active)-10} more")
            print(f"  ╚{'═'*66}")

        if settled:
            print(f"\n  ╔═ SETTLED / COMPRESSED (no load) ═╗")
            for p in settled[:8]:
                tier = p['tier'] or '?'
                anchor = (p['anchor'] or 'none')[:60]
                print(f"  ║ {p['pkg']:40s}  tier={tier:10s}")
                print(f"  ║   ↳ {anchor}")
            if len(settled) > 8:
                print(f"  ║   ... and {len(settled)-8} more")
            print(f"  ╚{'═'*66}")

    print(f"\n{'='*70}")
    print(f"SUMMARY: {len(neurons)} total neurons, {total_active} active/forming")
    print(f"Domains: {len(by_domain)}")
    print(f"\nThe frack exposes which ideas are still hot (forming_load)")
    print(f"vs which have cooled into crystal (no load, compressed).")
    print(f"The connectome filter: topology reveals what compression hides.")

    conn.close()

if __name__ == "__main__":
    main()