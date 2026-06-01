#!/usr/bin/env python3
"""
Semantic Scholar batch fetcher.
100 requests per 5 minutes = 1 request per 3 seconds.
Fills verification table with real peer-reviewed paper references.
Uses /dev/shm for fast WAL-mode SQLite.
"""

import sqlite3
import shutil
import urllib.request
import urllib.parse
import json
import time
import os
import sys

SRC = "/home/allaun/physics_equations.db"
TMP = "/dev/shm/physics_equations.db"

if os.path.exists(TMP):
    os.remove(TMP)
shutil.copy2(SRC, TMP)

conn = sqlite3.connect(TMP)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-2000000")
cur = conn.cursor()

# Get all domain info
cur.execute("SELECT id, name FROM domains WHERE id IN (SELECT DISTINCT domain_id FROM equations WHERE domain_id IS NOT NULL) ORDER BY id")
domains = {r[0]: r[1] for r in cur.fetchall()}

# Get all equations grouped by domain
cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
domain_eqs = {}
for d, e in cur.fetchall():
    domain_eqs.setdefault(d, []).append(e)

# ================================================================
# Semantic Scholar search queries per domain
# ================================================================
DOMAIN_SEARCHES = [
    (1,  "Newton laws motion"),
    (2,  "universal gravitation inverse square"),
    (3,  "Maxwell equations experimental verification"),
    (4,  "second law thermodynamics entropy"),
    (5,  "Schrodinger equation quantum mechanics"),
    (6,  "Einstein field equations general relativity test"),
    (7,  "Standard Model electroweak precision"),
    (8,  "Hubble constant cosmological parameters"),
    (9,  "Navier-Stokes turbulence Kolmogorov"),
    (10, "Snell law refraction optics"),
    (11, "speed of sound acoustic measurement"),
    (12, "BCS superconductivity Cooper pairs"),
    (13, "neutrino oscillation flavor mixing"),
    (14, "Chandrasekhar limit white dwarf mass"),
    (15, "Debye length plasma physics"),
    (16, "Noether theorem symmetry conservation"),
    (17, "fluctuation theorem statistical mechanics"),
    (18, "Hooke law elasticity modulus"),
    (19, "Landauer principle information thermodynamics"),
    (20, "Planck constant Kibble balance kilogram"),
    (21, "Hall-Petch grain size strengthening"),
    (22, "Bragg diffraction crystal structure"),
    (23, "Shockley diode semiconductor pn junction"),
    (24, "Flory-Huggins polymer solution theory"),
    (25, "Langmuir adsorption isotherm"),
    (28, "Gutenberg-Richter earthquake magnitude"),
    (29, "geostrophic wind atmospheric dynamics"),
    (30, "ocean wave dispersion gravity wave"),
    (31, "Darcy law groundwater flow porous media"),
    (32, "Hodgkin-Huxley action potential neuron"),
    (33, "Marcus electron transfer reaction rate"),
    (34, "optical frequency comb laser spectroscopy"),
    (35, "Zeeman effect magnetic field splitting"),
    (36, "non-Newtonian fluid power-law rheology"),
    (37, "Archard wear law tribology"),
    (38, "Janssen effect granular silo pressure"),
    (39, "Coulomb blockade single-electron transistor"),
    (40, "Bell inequality entanglement quantum"),
    (41, "Lorenz attractor deterministic chaos"),
    (42, "MRI Bloch equation imaging contrast"),
    (43, "Bethe-Bloch stopping power charged particle"),
    (44, "Shockley-Queisser solar cell efficiency limit"),
    (45, "Parker spiral solar wind magnetic field"),
    (46, "Chapman-Jouguet detonation velocity"),
    (47, "negative refractive index metamaterial"),
    (48, "sonar equation underwater acoustics"),
    (49, "PID control feedback engineering"),
]

# ================================================================
# Semantic Scholar API
# ================================================================
def s2_search(query, limit=5):
    """
    Search Semantic Scholar for papers matching query.
    Returns list of dicts: {title, year, doi, journal, citations}
    Rate limit: 100 requests per 5 minutes.
    """
    papers = []
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,year,externalIds,journal,publicationDate,citationCount",
        }
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers={"User-Agent": "PhysicsDB/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())

        for paper in data.get("data", []):
            ext = paper.get("externalIds", {}) or {}
            journal_info = paper.get("journal", {}) or {}
            papers.append({
                "paperId": paper.get("paperId", ""),
                "title": paper.get("title", "")[:250],
                "year": paper.get("year") or 0,
                "doi": ext.get("DOI", ""),
                "journal": journal_info.get("name", "") if journal_info else "",
                "citations": paper.get("citationCount", 0),
                "query": query,
            })
    except Exception as e:
        print(f"  S2 error [{query[:40]}]: {e}", flush=True)
    return papers


# ================================================================
# Fetch all domains (serial, rate-limited)
# ================================================================
total_papers = 0
insert_rows = []
start_time = time.time()

print(f"Fetching Semantic Scholar for {len(DOMAIN_SEARCHES)} domains...")
print("(Rate limit: 100 req / 5 min = 1 per 3 seconds)\n")

for dom_id, query in DOMAIN_SEARCHES:
    papers = s2_search(query, limit=5)
    name = domains.get(dom_id, f"domain_{dom_id}")
    eqs = domain_eqs.get(dom_id, [None])

    for i, p in enumerate(papers):
        eq_id = eqs[i % len(eqs)] if eqs else None
        experiment_text = f"Semantic Scholar: {p['journal']}" if p['journal'] else f"S2 [{query}]"
        insert_rows.append((
            eq_id,
            p["title"],
            experiment_text,
            p["year"],
            p["doi"] if p["doi"] else f"S2:{p['paperId'][:20]}",
            "Peer-reviewed (S2)",
        ))
        total_papers += 1

    print(f"  {name:30s} → {len(papers):2d} papers | total: {total_papers:3d} | {time.time()-start_time:.0f}s", flush=True)
    time.sleep(3.1)  # Respect rate limit

# ================================================================
# Insert into database
# ================================================================
print(f"\nBatch inserting {len(insert_rows)} records into {TMP}...")
cur.executemany(
    """INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status)
       VALUES (?, ?, ?, ?, ?, ?)""",
    insert_rows,
)
conn.commit()

# Stats
cur.execute("SELECT COUNT(*) FROM verifications")
total_ver = cur.fetchone()[0]
cur.execute("SELECT status, COUNT(*) FROM verifications GROUP BY status ORDER BY COUNT(*) DESC")
print("\nVerification status breakdown:")
for row in cur.fetchall():
    print(f"  {row[0]:30s} : {row[1]:6d}")

cur.execute("""
    SELECT d.name, COUNT(v.id) as n
    FROM verifications v
    JOIN equations e ON v.equation_id = e.id
    JOIN domains d ON e.domain_id = d.id
    WHERE v.status = 'Peer-reviewed (S2)'
    GROUP BY d.id ORDER BY n DESC LIMIT 20
""")
print("\nTop domains by Semantic Scholar papers:")
for row in cur.fetchall():
    print(f"  {row[0]:30s} : {row[1]:5d}")

conn.close()

# Copy back
shutil.copy2(TMP, SRC)
elapsed = time.time() - start_time
print(f"\nDone — {total_ver} total verifications ({total_papers} new from Semantic Scholar) in {elapsed:.0f}s")
print(f"Database: {SRC} ({os.path.getsize(SRC)} bytes)")
