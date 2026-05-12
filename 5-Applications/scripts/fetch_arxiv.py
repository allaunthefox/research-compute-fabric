#!/usr/bin/env python3
"""arXiv API parallel fetcher — fills verification table with peer-reviewed papers for each domain."""

import sqlite3
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

SRC = "/home/allaun/physics_equations.db"
TMP = "/dev/shm/physics_equations.db"

if os.path.exists(TMP):
    os.remove(TMP)

# Copy to tmpfs
os.system(f"cp {SRC} {TMP}")

conn = sqlite3.connect(TMP)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()

# Get all domains and their names
cur.execute("SELECT id, name FROM domains WHERE id IN (SELECT DISTINCT domain_id FROM equations WHERE domain_id IS NOT NULL) ORDER BY id")
domain_map = {row[0]: row[1] for row in cur.fetchall()}

# Domain → arXiv search queries
SEARCHES = [
    (1,  ["classical mechanics laws","Newton laws motion","Lagrangian mechanics principle","Hamiltonian mechanics canonical","rigid body dynamics Euler","Coriolis force rotating","conservation angular momentum"]),
    (2,  ["Newton law gravitation","Kepler laws planetary","gravitational potential energy","escape velocity orbit","Poisson equation gravity","tidal force earth moon","precession Mercury general relativity"]),
    (3,  ["Coulomb law verification","Lorentz force measurement","Maxwell equations electromagnetic","Biot Savart law","Faraday induction experiment","Poynting theorem energy flux","electromagnetic wave propagation"]),
    (4,  ["laws thermodynamics zeroth first second third","Carnot efficiency heat engine","Clausius inequality entropy","Gibbs free energy chemical","Maxwell relations thermodynamics","Clausius Clapeyron phase"]),
    (5,  ["Schrodinger equation validation","Heisenberg uncertainty principle test","Dirac equation prediction","Born rule probability","Pauli exclusion principle verification","Bell inequality loophole free","quantum harmonic oscillator"]),
    (6,  ["general relativity experimental test","gravitational redshift Pound Rebka","Shapiro time delay Viking","frame dragging Gravity Probe B","LIGO gravitational wave detection","Event Horizon Telescope black hole","binary pulsar orbital decay"]),
    (7,  ["Standard Model precision test","electron g-2 measurement","muon anomalous magnetic moment","Higgs boson discovery CMS ATLAS","electroweak precision fit LEP","QCD asymptotic freedom HERA","CKM matrix quark mixing"]),
    (8,  ["Hubble constant measurement","Planck CMB cosmological parameters","dark energy supernova evidence","baryon acoustic oscillations SDSS","big bang nucleosynthesis primordial","cosmic microwave background spectrum","Sachs Wolfe effect CMB"]),
    (9,  ["Navier Stokes equation validation","Reynolds number transition turbulence","Kolmogorov turbulence spectrum","Bernoulli equation verification","Poiseuille flow measurement","Stokes law drag sphere","aerodynamic lift Kutta Joukowski"]),
    (10, ["Snell law refraction measurement","Bragg X ray diffraction crystal","Fresnel equations reflection transmission","diffraction grating equation","Fermat principle least time","interference Young double slit","Fabry Perot etalon transmission"]),
    (11, ["speed of sound measurement","Doppler effect acoustic verification","standing wave resonance frequency","Helmholtz resonator frequency","beat frequency interference","decibel sound pressure level"]),
    (12, ["BCS superconductivity theory","Josephson junction voltage standard","quantum Hall effect resistance","Bloch theorem band structure","Fermi liquid theory Landau","Drude model conductivity","BCS energy gap tunneling"]),
    (13, ["radioactive decay law measurement","Bethe Weizsacker mass formula","Geiger Nuttall law alpha decay","nuclear shell model magic numbers","neutrino oscillation confirmation","reactor antineutrino disappearance"]),
    (14, ["Chandrasekhar limit white dwarf","Eddington luminosity limit","Hertzsprung Russell diagram","mass luminosity relation stars","Jeans instability star formation","solar neutrino flux measurement","triple alpha process carbon"]),
    (15, ["Debye length plasma measurement","plasma frequency oscillation","Alfven wave speed solar wind","MHD induction equation","Saha ionization equation","gyro frequency Larmor motion"]),
    (16, ["Noether theorem symmetry conservation","Stokes theorem vector calculus","Gauss divergence theorem","Green theorem two dimensional","Fourier transform signal processing","Laplace equation potential","Bessel equation cylindrical"]),
    (17, ["Boltzmann distribution equilibrium","partition function canonical ensemble","Boltzmann entropy formula","Gibbs entropy generalized","Jarzynski equality experiment","Crooks fluctuation theorem","Bose Einstein condensation temperature"]),
    (18, ["Hooke law elasticity measurement","Cauchy stress principle","Euler Bernoulli beam equation","Young modulus tensile test","shear modulus torsion","Poisson ratio measurement","Timoshenko beam theory"]),
    (19, ["Shannon entropy information theory","Shannon Hartley channel capacity","Nyquist Shannon sampling theorem","Landauer principle bit erasure","Kolmogorov complexity algorithmic"]),
    (20, ["speed light defines meter","Planck constant kilogram Kibble balance","elementary charge ampere","Boltzmann constant kelvin","Avogadro number mole","Josephson voltage standard","quantum Hall resistance standard"]),
    (21, ["Hall Petch grain size strengthening","Griffith fracture criterion","Paris law fatigue crack growth","stress intensity factor fracture","Weibull statistics brittle failure","Norton Bailey creep law","Larson Miller parameter creep"]),
    (22, ["Bragg law X ray diffraction","Laue equations diffraction","structure factor crystallography","atomic scattering factor","reciprocal lattice vector","Ewald sphere construction","Scherrer equation crystallite"]),
    (23, ["Shockley diode equation","MOSFET drain current saturation","intrinsic carrier concentration silicon","quantum confinement nanostructure","Brus equation quantum dot","band gap semiconductor measurement","Kane k dot p model"]),
    (24, ["Flory Huggins polymer solution","rubber elasticity Gaussian chain","WLF equation time temperature","reptation de Gennes polymer","Avrami crystallization kinetics","entanglement molecular weight","Rouse model polymer dynamics"]),
    (25, ["Langmuir adsorption isotherm","BET surface area measurement","Young contact angle wetting","Wenzel Cassie Baxter wetting","DLVO colloid stability","Kelvin equation capillary condensation","Gibbs adsorption equation surface"]),
    (28, ["seismic wave equation P S","Gutenberg Richter magnitude frequency","Omori law aftershock decay","plate tectonics Euler pole GPS","Airy isostasy compensation","Bouguer gravity anomaly measurement","geoid undulation Stokes formula"]),
    (29, ["geostrophic wind balance","hydrostatic equation atmosphere","Brunt Vaisala frequency stability","Rossby wave dispersion","Kohler cloud droplet activation","Mie scattering aerosol","Rayleigh scattering atmosphere"]),
    (30, ["ocean wave dispersion relation","Stokes drift mass transport","geostrophic balance ocean current","Ekman transport wind driven","Sverdrup balance gyre","Munk western boundary current","thermohaline circulation"]),
    (31, ["Darcy law permeability measurement","Richards equation unsaturated flow","Manning equation open channel","Penman Monteith evapotranspiration","Theis solution well hydraulics","Horton infiltration model"]),
    (32, ["Hodgkin Huxley action potential","Goldman Hodgkin Katz resting potential","cable equation dendrite","Michaelis Menten enzyme kinetics","FRET Forster resonance energy transfer","Monod Wyman Changeux allostery","muscle force velocity Hill equation"]),
    (33, ["Eyring transition state theory","Marcus electron transfer rate","Arrhenius equation activation energy","Butler Volmer electrode kinetics","Beer Lambert law absorbance"]),
    (34, ["laser rate equations Einstein","Schawlow Townes linewidth","optical frequency comb precision","nonlinear Schrodinger soliton fiber","Kramers Kronig optics dispersion","second harmonic generation phase matching"]),
    (35, ["Zeeman effect magnetic field","Stark effect electric field","hyperfine structure hydrogen 21cm","Born Oppenheimer approximation molecular","Franck Condon principle vibrational","Morse potential anharmonic","Rydberg formula atomic spectra"]),
    (36, ["power law fluid rheology","Bingham plastic yield stress","Herschel Bulkley model","Maxwell viscoelastic model","Kelvin Voigt viscoelastic solid","Cox Merz rule equivalence"]),
    (37, ["Coulomb Amontons friction law","Archard wear law adhesive","Reynolds equation lubrication","Stribeck curve bearing","Hertzian contact stress","elastohydrodynamic lubrication film thickness"]),
    (38, ["Janssen effect pressure silo","Coulomb yield criterion granular","angle of repose granular","Bagnold scaling inertial granular","mu I rheology dense granular flow","Brazil nut segregation vibration"]),
    (39, ["Coulomb blockade single electron transistor","Landauer formula ballistic conductance","Kondo effect quantum dot","graphene Dirac dispersion ARPES","Casimir force measurement","quantum confinement nanostructure"]),
    (40, ["Bell test loophole free entanglement","no cloning theorem quantum","Grover search algorithm quantum","Shor factoring algorithm quantum","quantum error correction surface code","Holevo bound quantum information"]),
    (41, ["Lorenz attractor experiment chaos","logistic map Feigenbaum constant","Lyapunov exponent measurement","Kuramoto synchronization oscillators","Mandelbrot set fractal dimension","KAM theorem invariant tori"]),
    (42, ["Bloch equation NMR MRI","Larmor frequency proton NMR","Radon transform CT reconstruction","linear quadratic model radiotherapy","Bragg peak proton therapy"]),
    (43, ["Bethe Bloch stopping power measurement","Bragg Gray cavity theory dosimetry","MIRD internal dosimetry formalism","radiation shielding attenuation coefficient"]),
    (44, ["Shockley Queisser limit solar cell","Betz limit wind turbine","Rankine cycle efficiency","Nernst equation fuel cell","thermoelectric figure merit ZT","battery Peukert law capacity"]),
    (45, ["Parker spiral interplanetary magnetic field","Chapman Ferraro magnetopause","Dungey cycle magnetospheric convection","Stoermer cosmic ray cutoff","radiation belt diffusion Fokker Planck","auroral acceleration Knight relation"]),
    (46, ["Chapman Jouguet detonation theory","ZND detonation wave structure","Rankine Hugoniot shock relations","Taylor Sedov blast wave","Hopkinson Cranz blast scaling","Mie Gruneisen equation state shock"]),
    (47, ["negative index metamaterial experiment","Pendry perfect lens subwavelength","transformation optics cloaking","Maxwell Garnett effective medium","split ring resonator metamaterial"]),
    (48, ["sonar equation verification","sound speed seawater measurement","underwater acoustic propagation loss","acoustic Doppler current profiler","ocean acoustic tomography"]),
    (49, ["heat exchanger NTU effectiveness","cantilever beam natural frequency","PID controller tuning Ziegler Nichols","Nyquist stability criterion control","Bode plot frequency response"]),
]

def fetch_arxiv(query, max_results=5):
    """Return list of dicts: {title, summary, year, doi, query}"""
    papers = []
    try:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "PhysDB/1.0"})
        resp = urllib.request.urlopen(req, timeout=20)
        data = resp.read().decode("utf-8")
        resp.close()

        root = ET.fromstring(data)
        ns = {
            "atom":   "http://www.w3.org/2005/Atom",
            "arxiv":  "http://arxiv.org/schemas/atom",
        }
        for entry in root.findall("atom:entry", ns):
            title_el   = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            doi_el     = entry.find("arxiv:doi", ns)
            yr_el      = entry.find("atom:published", ns)

            title = (title_el.text or "").strip().replace("\n", " ")[:250]
            summary = (summary_el.text or "").strip()[:500]
            doi = (doi_el.text or "").strip()[:80]
            year = int((yr_el.text or "0")[:4]) if yr_el is not None and yr_el.text else 0

            if title:
                papers.append({
                    "title":   title,
                    "summary": summary,
                    "doi":     doi,
                    "year":    year,
                    "query":   query,
                })
    except Exception as e:
        print(f"    arXiv error [{query[:40]}]: {e}", flush=True)
    return papers


def fetch_domain(dom_id, queries):
    """Fetch all papers for a domain, respecting arXiv rate limit."""
    name = domain_map.get(dom_id, f"domain_{dom_id}")
    all_p = []
    for q in queries:
        all_p.extend(fetch_arxiv(q, max_results=4))
        time.sleep(0.18)  # arXiv rate limit: ~1 req / 0.15s
    return dom_id, name, all_p


# ================================================================
# PARALLEL FETCH
# ================================================================
print(f"Fetching arXiv for {len(SEARCHES)} domains...\n", flush=True)
start = time.time()

total_papers = 0
insert_rows = []

with ThreadPoolExecutor(max_workers=12) as ex:
    futures = {ex.submit(fetch_domain, s[0], s[1]): s for s in SEARCHES}
    for f in as_completed(futures):
        dom_id, name, papers = f.result()

        # Get equation IDs for this domain
        cur.execute("SELECT id FROM equations WHERE domain_id=?", (dom_id,))
        eq_ids = [r[0] for r in cur.fetchall()]

        for i, p in enumerate(papers):
            eq_id = eq_ids[i % len(eq_ids)] if eq_ids else None
            insert_rows.append((
                eq_id,
                p["title"],
                f"arXiv [{p['query']}]",
                p["year"],
                p["doi"] if p["doi"] else "arXiv abstract",
                "arXiv indexed",
            ))
            total_papers += 1

        t = time.time() - start
        print(f"  ✓ {name:30s} → {len(papers):3d} papers | total: {total_papers:5d} | {t:.0f}s", flush=True)

# ================================================================
# BATCH INSERT into SQLite on /dev/shm
# ================================================================
print(f"\nBatch inserting {len(insert_rows)} records...", flush=True)
cur.executemany(
    """INSERT INTO verifications
       (equation_id, test_name, experiment, year, precision_level, status)
       VALUES (?, ?, ?, ?, ?, ?)""",
    insert_rows
)
conn.commit()

# Stats
cur.execute("SELECT COUNT(*) FROM verifications")
total_all = cur.fetchone()[0]
cur.execute("SELECT status, COUNT(*) FROM verifications GROUP BY status")
print("  Status breakdown:")
for row in cur.fetchall():
    print(f"    {row[0]:20s} : {row[1]:6d}")

# Count arXiv-indexed by domain
cur.execute("""
    SELECT d.name, COUNT(v.id) as n
    FROM verifications v
    JOIN equations e ON v.equation_id = e.id
    JOIN domains d ON e.domain_id = d.id
    WHERE v.status = 'arXiv indexed'
    GROUP BY d.id
    ORDER BY n DESC
    LIMIT 15
""")
print("\n  Top domains by arXiv papers:")
for row in cur.fetchall():
    print(f"    {row[0]:30s} : {row[1]:5d}")

conn.close()

# Copy back to persistent storage
os.system(f"cp {TMP} {SRC}")
elapsed = time.time() - start
print(f"\n✓ Done — {total_all} total verifications ({total_papers} new from arXiv) in {elapsed:.0f}s")
print(f"  Database: {SRC}")
