#!/usr/bin/env python3
"""
Preseeded URL batch fetcher for ALL domain gaps.
Cycles S2, Crossref, OpenAlex, Europe PMC, OpenAlex — 5 APIs, 1 req/sec.
Generates exact query URLs for every domain, fetches in pipeline.
"""

import sqlite3, urllib.request, urllib.parse, json, time, os, sys

DB = "/home/allaun/physics_equations.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()

# Get domain→eq mapping
cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
dom_eqs = {}
for d, e in cur.fetchall():
    dom_eqs.setdefault(d, []).append(e)

cur.execute("SELECT id, name FROM domains")
dom_names = {r[0]: r[1] for r in cur.fetchall()}

# Get current verification counts per domain
cur.execute("""
    SELECT e.domain_id, COUNT(DISTINCT v.id)
    FROM equations e
    LEFT JOIN verifications v ON v.equation_id = e.id
    WHERE e.domain_id IS NOT NULL
    GROUP BY e.domain_id
""")
dom_ver = {r[0]: r[1] for r in cur.fetchall()}

# ================================================================
# PRESEED: Domain → [query_string, ...] for every domain
# ================================================================
PRESEED = {
    # CORE PHYSICS — high priority
    1:  ["Newton laws experimental verification precision test",
         "Lagrangian mechanics experimental validation least action principle",
         "Hamiltonian mechanics canonical equations applied"],
    2:  ["Newton law gravitation experimental confirmation inverse square test",
         "Kepler third law exoplanet mass determination radial velocity"],
    3:  ["Coulomb inverse square law experimental limit photon mass null",
         "Faraday law induction experimental verification transformer",
         "Maxwell displacement current experimental confirmation Hertz"],
    4:  ["Carnot theorem efficiency limit experimental validation heat engine",
         "Clausius entropy second law thermodynamic experimental proof",
         "Gibbs free energy chemical equilibrium experimental validation"],
    5:  ["Schrodinger equation experimental verification atomic spectrum hydrogen",
         "Heisenberg uncertainty principle experimental test quantum optics",
         "Born rule probability experimental confirmation double slit"],
    6:  ["Pound Rebka experiment gravitational redshift confirmation",
         "Shapiro time delay measurement Cassini spacecraft general relativity",
         "Gravity Probe B frame dragging Lense Thirring experimental confirmation"],
    7:  ["electron g factor measurement precision test QED anomalous magnetic moment",
         "electroweak precision measurement LEP Z boson properties standard model",
         "Higgs boson CMS ATLAS combined measurement properties coupling"],
    8:  ["Planck CMB anisotropy power spectrum cosmological parameters measurement",
         "Hubble constant measurement tension SH0ES local distance ladder",
         "dark energy equation state supernova Pantheon DESI BAO measurement"],
    9:  ["Kolmogorov turbulence energy spectrum experimental measurement wind tunnel",
         "Poiseuille flow experimental verification laminar pipe Hagen Poiseuille",
         "Bernoulli equation experimental verification venturi pitot tube"],
    10: ["Snell law refraction experimental measurement refractive index precision",
         "Young double slit interference experimental verification wave light",
         "Bragg X ray diffraction crystal structure experimental determination"],

    # MATERIAL PHYSICS
    21: ["Hall Petch grain boundary strengthening experimental measurement metals",
         "Paris law fatigue crack growth experimental da dN measurement alloy",
         "Griffith fracture criterion experimental measurement brittle ceramic",
         "Weibull statistics strength distribution ceramic experimental measurement",
         "Norton Bailey creep law experimental measurement high temperature alloy"],
    22: ["Debye Waller factor temperature measurement X ray diffraction thermal motion",
         "Scherrer equation crystallite size XRD peak broadening measurement",
         "Rietveld refinement crystal structure powder diffraction method"],
    23: ["Shockley diode equation I V characteristic measurement silicon germanium",
         "MOSFET I V characteristic long channel saturation measurement",
         "quantum well confinement energy photoluminescence measurement GaAs",
         "Mott transition doping semiconductor metal insulator measurement"],
    24: ["Flory Huggins chi parameter measurement polymer solution scattering",
         "WLF time temperature superposition experimental master curve polymer",
         "reptation diffusion coefficient polymer NMR measurement de Gennes model"],
    25: ["BET surface area measurement nitrogen adsorption isotherm standard",
         "Langmuir adsorption isotherm monolayer coverage measurement",
         "contact angle Young equation measurement surface energy Zisman plot",
         "DLVO colloid stability force measurement AFM Derjaguin approximation"],
    26: ["Einstein viscosity suspension measurement rigid sphere dilute limit",
         "Frank Oseen elastic constant nematic liquid crystal measurement Frederiks"],
    27: ["nucleation rate classical theory Turnbull droplet undercooling measurement",
         "Johnson Mehl Avrami kinetics crystallization DSC measurement exponent",
         "Ostwald ripening LSW theory precipitate coarsening measurement TEM"],

    # EARTH / ENVIRONMENT
    28: ["Gutenberg Richter b value measurement earthquake catalog global",
         "seismic tomography P wave S wave velocity mantle structure measurement",
         "Bouguer gravity anomaly continental crustal structure measurement"],
    29: ["Brunt Vaisala frequency atmospheric stability measurement radiosonde lidar",
         "geostrophic wind balance measurement upper air radiosonde verification",
         "Mie scattering aerosol optical depth measurement sun photometer AERONET"],
    30: ["Ekman transport wind driven ocean current measurement drifter buoy",
         "ocean wave dispersion relation measurement waverider buoy spectrum"],
    31: ["Darcy law permeability measurement sand column constant head falling head",
         "Richards equation soil moisture measurement TDR neutron probe field",
         "Manning roughness coefficient open channel flow measurement river"],
    32: ["patch clamp Hodgkin Huxley model validation squid giant axon measurement",
         "FRET Forster resonance energy transfer single molecule distance measurement",
         "Michaelis Menten kinetics enzyme steady state parameter measurement"],
    33: ["Marcus electron transfer reorganization energy measurement intervalence",
         "Eyring activation enthalpy entropy measurement temperature dependent kinetics"],
    34: ["optical frequency comb precision measurement atomic clock stability",
         "Schawlow Townes linewidth laser measurement fundamental quantum limit",
         "soliton propagation nonlinear Schrodinger equation fiber experiment"],
    35: ["Lamb shift measurement hydrogen spectroscopy radio frequency",
         "Zeeman effect Lande g factor measurement atomic beam magnetic resonance",
         "hyperfine structure cesium atomic clock measurement SI second definition"],
    36: ["power law fluid shear thinning viscosity measurement rotational rheometer",
         "Bingham plastic yield stress measurement vane rheometer direct",
         "Cox Merz rule empirical verification steady dynamic viscosity polymer"],
    37: ["Archard wear coefficient measurement pin disk tribometer standard ASTM",
         "Stribeck curve measurement bearing lubrication transition EHL"],
    38: ["Janssen silo pressure measurement granular material saturation depth",
         "angle repose granular material measurement funnel method standard",
         "Bagnold number granular flow rheology inertial regime measurement"],
    39: ["Coulomb blockade diamond measurement single electron transistor quantum dot",
         "Landauer ballistic conductance quantization quantum point contact 2DEG",
         "graphene Dirac cone ARPES measurement linear dispersion Fermi velocity"],
    40: ["Bell inequality loophole free test violation measurement entanglement",
         "quantum error correction surface code logical qubit fidelity measurement"],
    41: ["Lorenz attractor chaos Rayleigh Benard convection experimental measurement",
         "Kuramoto model synchronization transition coupled oscillator experimental"],
    42: ["MRI T1 T2 relaxation time tissue measurement Bloch equation validation",
         "proton Bragg peak depth dose measurement therapy spread out SOBP"],
    43: ["Bethe Bloch stopping power measurement proton heavy ion energy loss",
         "ionization chamber absolute dosimetry calibration Bragg Gray cavity"],
    44: ["Shockley Queisser limit solar cell record efficiency measurement perovskite",
         "Betz limit wind turbine power coefficient measurement field test",
         "thermoelectric figure merit ZT measurement material record high"],
    45: ["Parker spiral interplanetary magnetic field measurement Wind ACE spacecraft",
         "Van Allen radiation belt electron flux measurement Van Allen probes"],
    46: ["detonation velocity measurement Chapman Jouguet TNT HMX experimental",
         "Taylor Sedow blast wave radius measurement nuclear fireball photography"],
    47: ["negative index metamaterial refraction prism experiment measurement",
         "transformation optics carpet cloak measurement broadband invisibility"],
    48: ["sonar equation transmission loss measurement underwater acoustic tank",
         "sound speed seawater profile measurement CTD conductivity temperature depth"],
    49: ["PID controller Ziegler Nichols tuning experiment process control measurement",
         "Nyquist stability criterion gain phase margin measurement control system"],
}

# ================================================================
# API FETCHERS — return lists of {title, year, doi, journal, src}
# ================================================================
def fetch_crossref(q, mx=5):
    out = []
    try:
        u = "https://api.crossref.org/works?" + urllib.parse.urlencode({
            "query": q, "rows": mx, "sort": "relevance", "filter": "type:journal-article"})
        req = urllib.request.Request(u, headers={"User-Agent": "PhysFill/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t = (i.get("title",[""]) or [""])[0]
            y = i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi = i.get("DOI","")
            jn = (i.get("container-title",[""]) or [""])[0]
            if t: out.append({"t":t[:250],"y":y,"d":doi,"j":jn,"s":"Crossref"})
    except: pass
    return out

def fetch_openalex(q, mx=5):
    out = []
    try:
        u = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "search": q, "per_page": mx, "sort": "cited_by_count:desc"})
        req = urllib.request.Request(u, headers={"User-Agent": "mailto:r@x.com"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        for i in d.get("results",[]):
            t = i.get("title","")
            y = i.get("publication_year")or 0
            doi = i.get("doi","")
            jn = ""
            if i.get("primary_location") and i["primary_location"].get("source"):
                jn = i["primary_location"]["source"].get("display_name","")
            if t: out.append({"t":t[:250],"y":y,"d":doi,"j":jn,"s":"OpenAlex"})
    except: pass
    return out

def fetch_s2(q, mx=5):
    out = []
    try:
        u = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
            "query": q, "limit": mx, "fields": "title,year,externalIds,journal,citationCount"})
        req = urllib.request.Request(u, headers={"User-Agent": "PhysFill/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        for p in d.get("data",[]):
            e = p.get("externalIds",{}) or {}
            jn = p.get("journal",{}) or {}
            out.append({"t":p.get("title","")[:250],"y":p.get("year")or 0,
                       "d":e.get("DOI",""),"j":jn.get("name",""),"s":"S2"})
    except: pass
    return out

def fetch_europepmc(q, mx=5):
    out = []
    try:
        u = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
            "query": q, "resultType": "core", "pageSize": mx, "format": "json"})
        req = urllib.request.Request(u, headers={"User-Agent": "PhysFill/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        for i in d.get("resultList",{}).get("result",[]):
            t = i.get("title","")
            y = int(i.get("firstPublicationDate","0")[:4]) if i.get("firstPublicationDate") else 0
            doi = i.get("doi","")
            jn = i.get("journalTitle","")
            if t: out.append({"t":t[:250],"y":y,"d":doi,"j":jn,"s":"EuropePMC"})
    except: pass
    return out

# ================================================================
# MAIN LOOP — API ROTATION
# ================================================================
# Build flattened task queue: (domain_id, query_string)
tasks = []
for did, queries in PRESEED.items():
    for q in queries:
        tasks.append((did, q))

# Rotate APIs
apis = [
    (fetch_crossref,  1.8, "Crossref"),
    (fetch_openalex,  2.0, "OpenAlex"),
    (fetch_s2,         2.0, "S2"),
    (fetch_europepmc, 1.8, "EuropePMC"),
    (fetch_openalex,  2.0, "OpenAlex"),
    (fetch_crossref,  1.8, "Crossref"),
    (fetch_s2,         2.0, "S2"),
    (fetch_openalex,  2.0, "OpenAlex"),
]

print(f"PRESEEDED BATCH FETCH")
print(f"{len(tasks)} queries across {len(PRESEED)} domains")
print(f"APIs: Crossref, OpenAlex, S2, EuropePMC")
print(f"Rate: ~1 req / 2s | ETA: {len(tasks)*2/60:.0f} min\n")

total, batch = 0, []
start = time.time()
prev_did = None

for idx, (did, query) in enumerate(tasks):
    fn, delay, name = apis[idx % len(apis)]
    papers = fn(query, 5)
    eqs = dom_eqs.get(did, [None])

    for i, p in enumerate(papers):
        eq_id = eqs[i % len(eqs)] if eqs else None
        batch.append((eq_id, p['t'],
            f"{p['s']}: {p['j']}" if p.get('j') else p['s'],
            p['y'], p.get('d', p['s']), "Multi-API preseed"))
        total += 1

    # Print domain header when switching
    if did != prev_did:
        name = dom_names.get(did, f"#{did}")
        prev_did = did
        print(f"\n── {name} (gap: {dom_ver.get(did,0)} verifications) ──", flush=True)

    eta = (len(tasks) - idx) * delay
    mark = "✓" if papers else "○"
    print(f"  {mark} {name:10s} › {query[:72]:72s} → {len(papers)}p | {total:4d} | {eta:.0f}s left", flush=True)

    # Flush every 30 records
    if len(batch) >= 30:
        cur.executemany(
            """INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status)
               VALUES (?, ?, ?, ?, ?, ?)""", batch)
        conn.commit()
        batch = []

    time.sleep(delay)

# Final flush
if batch:
    cur.executemany("""INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status)
        VALUES (?, ?, ?, ?, ?, ?)""", batch)
    conn.commit()

# ================================================================
# FINAL STATS
# ================================================================
cur.execute("SELECT COUNT(*) FROM verifications")
total_v = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM equations")
total_e = cur.fetchone()[0]
elapsed = time.time() - start

print(f"\n{'═'*70}")
print(f"✓ COMPLETE — {total_v} verifications, {total_e} equations, {total} added this run")
print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
print(f"  Throughput: {len(tasks)/elapsed*60:.1f} queries/min")

# Show domain coverage now
cur.execute("""
    SELECT d.name, COUNT(DISTINCT e.id), COUNT(DISTINCT v.id),
           ROUND(COUNT(DISTINCT v.id)*1.0/MAX(COUNT(DISTINCT e.id),1),1)
    FROM domains d
    LEFT JOIN equations e ON e.domain_id = d.id
    LEFT JOIN verifications v ON v.equation_id = e.id
    WHERE e.id IS NOT NULL
    GROUP BY d.id
    ORDER BY COUNT(DISTINCT v.id) DESC
""")
print(f"\nDOMAIN COVERAGE (after fill):")
for row in cur.fetchall():
    bar = "█" * int(row[3])
    print(f"  {row[0]:32s} {row[2]:5d} ver / {row[1]:3d} eqs = {row[3]:4.1f}x  {bar}")

conn.close()
print(f"\n  {DB}")
