#!/usr/bin/env python3
"""
Multi-API rotation fetcher.
Rotates through: Crossref, OpenAlex, Semantic Scholar, INSPIRE-HEP, Europe PMC, CORE.
Each API has its own rate limit — we cycle so none gets exhausted.
Slow, steady, accumulates over time. Writes incrementally to /dev/shm.
"""

import sqlite3
import urllib.request
import urllib.parse
import json
import time
import os
import sys
import random
from datetime import datetime

SRC = "/home/allaun/physics_equations.db"
TMP = "/dev/shm/physics_equations.db"

if os.path.exists(TMP):
    os.remove(TMP)
os.system(f"cp {SRC} {TMP}")

conn = sqlite3.connect(TMP)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()

# Load domain → equation mapping
cur.execute("SELECT id, name FROM domains WHERE id IN (SELECT DISTINCT domain_id FROM equations WHERE domain_id IS NOT NULL) ORDER BY id")
domains = {r[0]: r[1] for r in cur.fetchall()}

cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
domain_eqs = {}
for d, e in cur.fetchall():
    domain_eqs.setdefault(d, []).append(e)

# Find how many verifications each domain already has
cur.execute("""
    SELECT e.domain_id, COUNT(v.id)
    FROM equations e
    LEFT JOIN verifications v ON v.equation_id = e.id
    WHERE e.domain_id IS NOT NULL
    GROUP BY e.domain_id
""")
domain_ver_count = {r[0]: r[1] for r in cur.fetchall()}

# Domain search queries (short, effective)
SEARCHES = {
    1:  ("Newton's laws motion", "classical mechanics force acceleration"),
    2:  ("universal gravitation inverse square", "Newton law gravitation"),
    3:  ("Maxwell equations electromagnetism", "electromagnetic wave propagation"),
    4:  ("thermodynamics entropy second law", "Carnot efficiency heat engine"),
    5:  ("Schrodinger equation quantum", "Heisenberg uncertainty principle"),
    6:  ("general relativity test", "gravitational wave detection"),
    7:  ("Standard Model electroweak", "Higgs boson discovery"),
    8:  ("Hubble constant cosmology", "cosmic microwave background"),
    9:  ("Navier-Stokes turbulence", "Reynolds number flow transition"),
    10: ("Snell law refraction optics", "Fresnel diffraction interference"),
    11: ("speed of sound measurement", "acoustic wave resonance"),
    12: ("BCS superconductivity theory", "Josephson junction effect"),
    13: ("neutrino oscillation flavor", "radioactive decay nuclear"),
    14: ("Chandrasekhar white dwarf limit", "stellar evolution mass luminosity"),
    15: ("Debye plasma screening length", "Alfven wave magnetohydrodynamics"),
    16: ("Noether theorem symmetry", "Fourier transform analysis"),
    17: ("Jarzynski equality fluctuation", "statistical mechanics partition"),
    18: ("Hooke law elasticity stress", "Euler Bernoulli beam bending"),
    19: ("Landauer principle information", "Shannon channel capacity"),
    20: ("Planck constant kilogram redefinition", "atomic clock frequency standard"),
    21: ("Hall-Petch grain boundary strengthening", "Paris law fatigue crack"),
    22: ("X-ray crystallography Bragg law", "Debye-Waller factor thermal"),
    23: ("Shockley diode semiconductor junction", "MOSFET transistor characteristics"),
    24: ("Flory-Huggins polymer solution", "viscoelasticity glass transition"),
    25: ("Langmuir adsorption monolayer", "BET surface area measurement"),
    28: ("Gutenberg-Richter earthquake magnitude", "seismic wave velocity"),
    29: ("geostrophic wind atmospheric", "Rossby wave planetary"),
    30: ("ocean wave dispersion Ekman", "thermohaline circulation deep"),
    31: ("Darcy law groundwater flow", "Richards equation soil moisture"),
    32: ("Hodgkin-Huxley neuron action potential", "Michaelis-Menten enzyme kinetics"),
    33: ("Marcus electron transfer theory", "Arrhenius activation energy reaction"),
    34: ("optical frequency comb femtosecond", "nonlinear optics soliton"),
    35: ("Zeeman effect atomic spectra", "Lamb shift hydrogen fine structure"),
    36: ("non-Newtonian power-law fluid", "Bingham yield stress rheology"),
    37: ("Archard wear coefficient tribology", "Reynolds lubrication equation"),
    38: ("Janssen effect granular silo", "angle of repose granular flow"),
    39: ("Coulomb blockade single electron", "graphene Dirac cone dispersion"),
    40: ("Bell inequality quantum entanglement", "quantum error correction surface code"),
    41: ("Lorenz attractor deterministic chaos", "Feigenbaum period doubling universality"),
    42: ("MRI Bloch equation T1 T2", "proton therapy Bragg peak"),
    43: ("Bethe-Bloch stopping power", "radiation dosimetry cavity theory"),
    44: ("solar cell Shockley-Queisser efficiency", "Betz wind turbine limit"),
    45: ("Parker spiral solar wind magnetic", "magnetosphere radiation belt"),
    46: ("Chapman-Jouguet detonation wave", "Rankine-Hugoniot shock compression"),
    47: ("negative index metamaterial refraction", "transformation optics invisibility"),
    48: ("sonar equation underwater propagation", "ocean acoustic tomography"),
    49: ("PID controller feedback stability", "Nyquist criterion control theory"),
}

# ================================================================
# API FETCHERS
# ================================================================
def fetch_crossref(query, limit=5):
    """Crossref API — polite pool with email in User-Agent."""
    papers = []
    try:
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": limit,
            "sort": "relevance",
            "filter": "type:journal-article",
        }
        full = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full, headers={
            "User-Agent": "PhysicsDB/1.0 (mailto:research@example.com)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("message", {}).get("items", []):
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""
            year = item.get("created", {}).get("date-parts", [[0]])[0][0]
            doi = item.get("DOI", "")
            journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
            if title:
                papers.append({"title": title[:250], "year": year, "doi": doi, "journal": journal, "source": "Crossref"})
    except Exception:
        pass
    return papers

def fetch_openalex(query, limit=5):
    """OpenAlex API — open, no key needed, ~10 req/sec polite."""
    papers = []
    try:
        url = "https://api.openalex.org/works"
        params = {"search": query, "per_page": limit, "sort": "cited_by_count:desc"}
        full = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full, headers={
            "User-Agent": "mailto:research@example.com",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("results", []):
            title = item.get("title", "")
            year = item.get("publication_year") or 0
            doi = item.get("doi", "") or ""
            journal = ""
            if item.get("primary_location") and item["primary_location"].get("source"):
                journal = item["primary_location"]["source"].get("display_name", "")
            if title:
                papers.append({"title": title[:250], "year": year, "doi": doi, "journal": journal, "source": "OpenAlex"})
    except Exception:
        pass
    return papers

def fetch_inspirehep(query, limit=5):
    """INSPIRE-HEP API — HEP papers, great for QFT/nuclear/astro domains."""
    papers = []
    try:
        url = "https://inspirehep.net/api/literature"
        params = {"q": query, "size": limit, "sort": "mostrecent"}
        full = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full, headers={
            "User-Agent": "PhysicsDB/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("hits", {}).get("hits", []):
            meta = item.get("metadata", {})
            title_el = meta.get("titles", [{}])
            title = title_el[0].get("title", "") if title_el else ""
            year = meta.get("publication_info", [{}])
            yr = year[0].get("year", 0) if year else 0
            dois = meta.get("dois", [{}])
            doi = dois[0].get("value", "") if dois else ""
            if title:
                papers.append({"title": title[:250], "year": yr, "doi": doi, "journal": "INSPIRE-HEP", "source": "INSPIRE-HEP"})
    except Exception:
        pass
    return papers

def fetch_europepmc(query, limit=5):
    """Europe PMC API — biomedical/life sciences papers (biophys, medphys, etc)."""
    papers = []
    try:
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {"query": query, "resultType": "core", "pageSize": limit, "format": "json"}
        full = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full, headers={"User-Agent": "PhysicsDB/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("resultList", {}).get("result", []):
            title = item.get("title", "")
            year = int(item.get("firstPublicationDate", "0")[:4]) if item.get("firstPublicationDate") else 0
            doi = item.get("doi", "")
            journal = item.get("journalTitle", "")
            if title:
                papers.append({"title": title[:250], "year": year, "doi": doi, "journal": journal, "source": "EuropePMC"})
    except Exception:
        pass
    return papers

def fetch_core(query, limit=5):
    """CORE.ac.uk API — open access repository aggregator."""
    papers = []
    try:
        url = "https://api.core.ac.uk/v3/search/works"
        body = json.dumps({"q": query, "limit": limit}).encode()
        req = urllib.request.Request(url, data=body, headers={
            "User-Agent": "PhysicsDB/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("results", []):
            title = item.get("title", "")
            year = item.get("yearPublished") or 0
            doi = item.get("doi", "")
            journal = item.get("publisher", "")
            if title:
                papers.append({"title": title[:250], "year": year, "doi": doi, "journal": journal, "source": "CORE"})
    except Exception:
        pass
    return papers

# ================================================================
# API rotation — 5 APIs, 1 query each cycle, 3s between queries
# ================================================================
APIS = [
    ("Crossref",  fetch_crossref,  1.5),
    ("OpenAlex",  fetch_openalex,  2.0),
    ("CrossRef2", fetch_crossref,  1.5),
    ("INSPIRE",   fetch_inspirehep, 1.5),
    ("EuropePMC", fetch_europepmc,  1.5),
    ("OpenAlex2", fetch_openalex,  2.0),
    ("Crossref3", fetch_crossref,  1.5),
    ("INSPIRE2",  fetch_inspirehep, 1.5),
]

# Get domains needing more papers (prioritize those with fewest)
gap_domains = sorted(
    [(did, domain_ver_count.get(did, 0)) for did in SEARCHES.keys()],
    key=lambda x: x[1]
)

print(f"Multi-API fetch — {len(APIS)} API slots, {len(gap_domains)} domains")
print(f"  Least-covered domains: {', '.join(domains[d] for d,_ in gap_domains[:5])}")
print(f"  APIs: {', '.join(a[0] for a in APIS)}")
print()

total = 0
insert_rows = []
start = time.time()
api_idx = 0

while gap_domains and (time.time() - start) < 7200:  # 2 hour max
    dom_id, _ = gap_domains.pop(0)

    if dom_id not in SEARCHES:
        continue

    name = domains.get(dom_id, f"dom_{dom_id}")
    eqs = domain_eqs.get(dom_id, [None])

    queries = SEARCHES[dom_id]
    # Pick one query — alternate between the two
    q = queries[0] if total % 2 == 0 else queries[1]

    api_name, fetcher, delay = APIS[api_idx % len(APIS)]
    api_idx += 1

    papers = fetcher(q, limit=5)

    for i, p in enumerate(papers):
        eq_id = eqs[i % len(eqs)] if eqs else None
        insert_rows.append((
            eq_id, p["title"],
            f"{p['source']}: {p['journal']}" if p.get('journal') else p['source'],
            p["year"], p.get("doi", p['source']), p['source'],
        ))
        total += 1

    t = time.time() - start
    marker = "✓" if papers else "○"
    print(f"  {marker} [{api_name:10s}] {name:28s} → {len(papers):2d} papers | {total:4d} total | {t:.0f}s", flush=True)

    # Re-add domain if it got zero papers (retry later with other query)
    if not papers:
        gap_domains.append((dom_id, 0))

    # Flush every 10 batches
    if len(insert_rows) >= 50:
        cur.executemany(
            """INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            insert_rows,
        )
        conn.commit()
        print(f"  ⟳ Flushed {len(insert_rows)} records ({total} total) [{time.time()-start:.0f}s]", flush=True)
        insert_rows = []

    time.sleep(delay)

# Final flush
if insert_rows:
    cur.executemany(
        "INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)",
        insert_rows,
    )
    conn.commit()

# ================================================================
# STATS
# ================================================================
cur.execute("SELECT COUNT(*) FROM verifications")
total_ver = cur.fetchone()[0]
cur.execute("SELECT status, COUNT(*) FROM verifications GROUP BY status ORDER BY COUNT(*) DESC")
print(f"\n═══ VERIFICATIONS: {total_ver} ═══")
for row in cur.fetchall():
    print(f"  {row[0]:30s}: {row[1]:6d}")

cur.execute("""
    SELECT d.name, COUNT(v.id) as n
    FROM verifications v
    JOIN equations e ON v.equation_id = e.id
    JOIN domains d ON e.domain_id = d.id
    GROUP BY d.id ORDER BY n DESC
""")
print(f"\n═══ DOMAINS BY COVERAGE ═══")
for row in cur.fetchall():
    pct = row[1] / max(total_ver, 1) * 100
    bar = "█" * int(pct / 2)
    print(f"  {row[0]:28s} {row[1]:4d}  {bar}")

conn.close()
os.system(f"cp {TMP} {SRC}")
elapsed = time.time() - start
print(f"\n✓ Complete — {total_ver} verifications in {elapsed:.0f}s ({elapsed/60:.1f} min)")
print(f"  Database: {SRC}")
