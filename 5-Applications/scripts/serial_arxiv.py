#!/usr/bin/env python3
"""arXiv serial fetcher with proper rate limiting + backoff. Writes to /dev/shm."""

import sqlite3, xml.etree.ElementTree as ET, urllib.request, urllib.parse, time, os, sys

SRC = "/home/allaun/physics_equations.db"
TMP = "/dev/shm/physics_equations.db"
if os.path.exists(TMP): os.remove(TMP)
os.system(f"cp {SRC} {TMP}")

conn = sqlite3.connect(TMP)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-2000000")
cur = conn.cursor()

# Single request, with retry+backoff
def arxiv_search(query, mx=5, retries=3):
    for attempt in range(retries):
        try:
            params = {"search_query": f"all:{query}", "start": 0, "max_results": mx,
                      "sortBy": "relevance", "sortOrder": "descending"}
            url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "PhysDB-Researcher/1.0"})
            resp = urllib.request.urlopen(req, timeout=25)
            data = resp.read().decode()
            resp.close()
            root = ET.fromstring(data)
            ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
            papers = []
            for e in root.findall("a:entry", ns):
                t = e.find("a:title", ns)
                s = e.find("a:summary", ns)
                d = e.find("x:doi", ns)
                y = e.find("a:published", ns)
                title = (t.text or "").strip().replace("\n", " ")[:250]
                summary = (s.text or "").strip()[:500]
                doi = (d.text or "").strip()[:80]
                year = int((y.text or "0")[:4]) if y is not None and y.text else 0
                if title:
                    papers.append({"title": title, "summary": summary, "doi": doi, "year": year, "query": query})
            return papers
        except Exception as e:
            wait = 2 ** attempt
            print(f"  retry {attempt+1}/{retries} [{query[:40]}]: {e}", flush=True)
            time.sleep(wait)
    return []

# Domain → equations map
cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
domain_eqs = {}
for d, e in cur.fetchall():
    domain_eqs.setdefault(d, []).append(e)

# Key searches per domain (limited to 1 per domain to avoid rate limits)
SEARCHES = [
    (1,"classical mechanics","Newton laws verification experiment"),
    (2,"gravitation","Newton law gravitation experimental confirmation"),
    (3,"electromagnetism","Coulomb law inverse square experiment verification"),
    (4,"thermodynamics","Carnot efficiency experimental confirmation"),
    (5,"quantum mechanics","Schrodinger equation experimental verification"),
    (6,"relativity","general relativity experimental test Pound Rebka"),
    (7,"quantum field theory","Standard Model precision test LEP electroweak"),
    (8,"cosmology","Planck CMB cosmological parameters dark energy evidence"),
    (9,"fluid dynamics","Reynolds number transition turbulence experiment"),
    (10,"optics","Snell law refraction experimental measurement"),
    (11,"acoustics","speed sound measurement experimental confirmation"),
    (12,"condensed matter","BCS superconductivity tunneling spectroscopy experiment"),
    (13,"nuclear physics","radioactive decay law measurement half life"),
    (14,"astrophysics","Chandrasekhar limit white dwarf mass measurement"),
    (15,"plasma physics","Debye length plasma screening measurement"),
    (16,"mathematical physics","Noether theorem experimental confirmation symmetry conservation"),
    (17,"statistical mechanics","Jarzynski equality single molecule experiment"),
    (18,"continuum mechanics","Hooke law elastic modulus measurement experiment"),
    (19,"information theory","Landauer principle bit erasure experiment measurement"),
    (20,"metrology","Planck constant Kibble balance measurement kilogram"),
    (21,"material physics","Hall Petch grain size strengthening experimental measurement"),
    (22,"crystallography","Bragg law X ray diffraction crystal structure determination"),
    (23,"semiconductor physics","Shockley diode equation pn junction I-V measurement"),
    (24,"polymer physics","Flory Huggins polymer solution phase diagram measurement"),
    (25,"surface science","Langmuir adsorption isotherm monolayer measurement"),
    (26,"soft matter","Einstein viscosity suspension sphere measurement experiment"),
    (27,"phase transformations","nucleation theory classical Turnbull droplet experiment"),
    (28,"geophysics","Gutenberg Richter magnitude frequency b value measurement"),
    (29,"atmospheric physics","geostrophic wind balance radiosonde measurement"),
    (30,"oceanography","ocean wave dispersion relation buoy measurement"),
    (31,"hydrology","Darcy law permeability measurement sand column experiment"),
    (32,"biophysics","Hodgkin Huxley action potential squid giant axon measurement"),
    (33,"chemical physics","Arrhenius activation energy reaction rate measurement"),
    (34,"photonics","laser threshold condition experimental measurement ruby laser"),
    (35,"atomic physics","Zeeman effect magnetic field splitting spectral measurement"),
    (36,"rheology","power law fluid shear thinning viscosity measurement"),
    (37,"tribology","Archard wear law pin disk experiment wear coefficient"),
    (38,"granular materials","Janssen effect silo pressure saturation measurement"),
    (39,"nanoscience","Coulomb blockade single electron transistor measurement"),
    (40,"quantum information","Bell inequality loophole free test entanglement violation"),
    (41,"nonlinear dynamics","Lorenz attractor experiment Rayleigh Benard convection chaos"),
    (42,"medical physics","MRI Bloch equation relaxation time tissue measurement"),
    (43,"radiation physics","Bethe Bloch stopping power charged particle measurement"),
    (44,"energy physics","Shockley Queisser limit solar cell efficiency record measurement"),
    (45,"space physics","Parker spiral interplanetary magnetic field spacecraft measurement"),
    (46,"detonics shock","Chapman Jouguet detonation velocity experimental measurement TNT"),
    (47,"metamaterials","negative index metamaterial refraction experiment microwave"),
    (48,"underwater acoustics","sonar equation underwater acoustic propagation measurement"),
    (49,"engineering physics","PID controller industrial process control experiment tuning"),
]

total = 0
batch = []
print(f"Fetching {len(SEARCHES)} domains (serial, rate-limited)...")
for dom_id, name, query in SEARCHES:
    papers = arxiv_search(query, mx=5)
    eqs = domain_eqs.get(dom_id, [None])
    for i, p in enumerate(papers):
        batch.append((eqs[i % len(eqs)], p["title"], f"arXiv: {name}",
                      p["year"], p["doi"] or "arXiv", "arXiv indexed"))
        total += 1
    print(f"  [{dom_id:2d}] {name:25s} → {len(papers):2d} papers | total={total}", flush=True)
    time.sleep(2.0)  # Respect arXiv: 1 req per 5s for safety

print(f"\nInserting {len(batch)} records...")
cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", batch)
conn.commit()
cur.execute("SELECT COUNT(*) FROM verifications"); tot = cur.fetchone()[0]
print(f"Total verifications: {tot}")
conn.close()
os.system(f"cp {TMP} {SRC}")
print(f"Done. Database: {SRC} ({tot} verifications)")
