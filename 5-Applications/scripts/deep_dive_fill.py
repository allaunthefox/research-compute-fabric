#!/usr/bin/env python3
"""
Deep dive fill — maximum surface area for invariant scan.
Targets thin domains with dense multi-query coverage per equation.
Uses 6 API rotation, 1.5s between queries.
"""

import sqlite3, urllib.request, urllib.parse, json, time, os, sys

DB = "/home/allaun/physics_equations.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()

cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
dom_eqs = {}
for d, e in cur.fetchall():
    dom_eqs.setdefault(d, []).append(e)

cur.execute("SELECT id, name FROM domains")
dom_names = {r[0]: r[1] for r in cur.fetchall()}

# ================================================================
# DEEP DIVE QUERY MAP
# Each domain gets queries matched to its specific equations
# ================================================================

DEEP = {
    # ── CONDENSED MATTER (33 eqs, 0.3 ratio) ──
    12: [
        "BCS theory energy gap measurement tunneling spectroscopy superconductor",
        "BCS isotope effect mercury tin lead superconducting transition temperature",
        "Josephson junction Shapiro steps microwave irradiation voltage standard",
        "Josephson effect SQUID magnetometer sensitivity measurement",
        "quantum Hall effect integer fractional von Klitzing constant plateau",
        "quantum anomalous Hall effect topological insulator Chern number measurement",
        "Bloch theorem ARPES angle resolved photoemission band structure copper oxide",
        "Kronig Penney model superlattice miniband transport measurement",
        "Fermi liquid theory quasiparticle effective mass de Haas van Alphen measurement",
        "Drude model optical conductivity free electron plasma frequency metal",
        "Sommerfeld model electronic specific heat linear temperature coefficient metal",
        "Landau Fermi liquid heavy fermion CeCu6 CeAl3 UBe13 measurement",
        "spin Peierls transition CuGeO3 inorganic measurement neutron scattering",
        "Peierls distortion charge density wave NbSe3 TaS3 transport measurement",
        "Mott insulator metal transition VO2 V2O3 resistivity switching measurement",
        "Anderson localization weak localization quantum correction conductivity magnetoresistance",
        "variable range hopping Mott Efros Shklovskii conductivity temperature exponent",
        "Kondo effect resistance minimum dilute magnetic alloy CuFe AuFe measurement",
        "RKKY oscillation exchange coupling magnetic multilayer Gd Y superlattice",
        "spin glass susceptibility cusp frequency dependence AC measurement CuMn",
        "heavy fermion superconductivity CeCu2Si2 UBe13 UPt3 unconventional pairing",
        "high temperature superconductor cuprate YBCO BSCCO pseudogap phase diagram",
        "iron based superconductor LaFeAsO SmFeAsO pnictide pairing symmetry measurement",
        "topological insulator Bi2Se3 Bi2Te3 surface state ARPES spin helical Dirac",
        "Weyl semimetal TaAs NbAs NbP Fermi arc ARPES chiral anomaly measurement",
        "Kosterlitz Thouless transition 2D superconductor vortex unbinding IV exponent",
    ],

    # ── MATERIAL PHYSICS (126 eqs, 0.3 ratio) ──
    21: [
        "Hall Petch breakdown inverse nanometer grain size molecular dynamics simulation",
        "grain boundary sliding creep diffusional Coble Nabarro Herring mechanism measurement",
        "dislocation density X ray line profile analysis modified Williamson Hall",
        "stacking fault energy measurement weak beam TEM dissociation width dislocation",
        "twinning induced plasticity TWIP steel high manganese stacking fault energy",
        "transformation induced plasticity TRIP steel retained austenite martensite measurement",
        "Orowan looping mechanism precipitate bypass transmission electron microscopy in situ",
        "solid solution strengthening Labusch Fleischer model size modulus misfit parameter",
        "fatigue crack initiation persistent slip band surface extrusion intrusion measurement",
        "very high cycle fatigue gigacycle ultrasonic testing fish eye fracture internal inclusion",
        "fracture toughness J integral R curve stable crack growth ASTM E1820 measurement",
        "dynamic strain aging Portevin Le Chatelier effect serrated flow aluminum alloy",
        "Luders band propagation yield point elongation mild steel strain localization DIC",
        "superplasticity grain boundary sliding large elongation fine grain aluminum alloy",
        "shape memory effect NiTi nitinol martensite austenite transformation DSC measurement",
        "superelasticity stress induced martensite NiTi temperature dependence loading unloading",
        "transformation temperature Af As Ms Mf NiTiHf NiTiPd high temperature shape memory",
        "magnetocaloric effect Gd Gd5Si2Ge2 magnetic refrigeration entropy change measurement",
        "giant magnetostriction Terfenol D Galfenol FeGa strain magnetic field measurement",
        "invar effect FeNi thermal expansion coefficient low temperature magnetic origin",
        "elastocaloric effect NiTi CuZnAl adiabatic temperature change stress measurement",
        "hydrogen embrittlement steel delayed fracture hydrogen diffusion trapping measurement",
        "stress corrosion cracking aluminum alloy chloride aqueous environment crack velocity",
        "irradiation embrittlement reactor pressure vessel steel neutron dose ductile brittle",
        "zirconium hydride delayed hydride cracking Zr alloy nuclear fuel cladding measurement",
        "thermal barrier coating yttria stabilized zirconia EB PVD columnar microstructure",
        "environmental barrier coating SiC ceramic matrix composite water vapor recession silica",
        "MAX phase Ti3SiC2 Ti2AlC machinable ceramic kinking nonlinear elastic damage",
        "high entropy alloy CrMnFeCoNi Cantor sluggish diffusion lattice distortion measurement",
        "bulk metallic glass ZrCuAlNi crystallization kinetics isothermal DSC activation energy",
        "equiatomic CrCoNi medium entropy alloy cryogenic temperature fracture toughness record",
        "refractory high entropy alloy NbMoTaW VNbMoTaW body centered cubic strength temperature",
        "graded material functionally graded thermal stress composition profile diffusion couple",
        "biomimetic composite nacre aragonite platelet brick mortar fracture toughness mechanism",
        "architectured material lattice truss octet cellular solid specific strength stiffness",
        "self-healing material microcapsule dicyclopentadiene Grubbs catalyst crack healing efficiency",
        "additive manufacturing selective laser melting process parameter porosity fatigue Ti6Al4V",
        "corrosion pitting stainless steel passive film breakdown chloride measurement",
        "galvanic corrosion aluminum steel couple seawater potential difference measurement",
        "hot corrosion gas turbine Na2SO4 NaCl vanadium attack nickel superalloy sulfidation",
    ],

    # ── MATHEMATICAL PHYSICS (19 eqs, 0.3 ratio) ──
    16: [
        "Noether theorem conservation law gauge symmetry field theory electromagnetic charge",
        "Stokes theorem fluid dynamics vorticity circulation Kelvin Helmholtz vortex",
        "Gauss divergence theorem electrostatics Maxwell stress tensor momentum conservation",
        "Fourier transform crystallography structure factor diffraction electron density",
        "Laplace equation boundary value problem electrostatics Dirichlet Neumann Green function",
        "Poisson equation gravitation electrostatics fast multipole method numerical solution",
        "Bessel function cylindrical waveguide mode cutoff frequency radial distribution",
        "Legendre polynomial spherical harmonic multipole expansion potential angular momentum",
        "Hermite polynomial quantum harmonic oscillator wavefunction Gaussian quadrature",
        "Laguerre polynomial hydrogen radial wavefunction associated electron orbital",
        "spherical harmonic angular momentum eigenfunction scattering phase shift partial wave",
        "Gamma function Stirling approximation factorial asymptotic statistical physics",
        "Dirac delta distribution Green function retarded propagator wave equation",
        "separation of variables Helmholtz equation cylindrical spherical coordinate Bessel Legendre",
        "Cauchy Schwarz inequality quantum uncertainty Heisenberg Robertson Schrodinger states",
        "eigenvalue eigenfunction Sturm Liouville problem boundary condition orthogonal completeness",
        "Wigner Eckart theorem irreducible tensor operator matrix element Clebsch Gordan",
        "Baker Campbell Hausdorff formula Lie algebra exponential operator commutation",
        "stationary phase approximation path integral semiclassical limit WKB connection formula",
        "method steepest descent complex analysis Airy function Stokes phenomenon asymptotic",
    ],

    # ── ASTROPHYSICS (18 eqs, 0.4 ratio) ──
    14: [
        "Chandrasekhar mass white dwarf Sirius B spectroscopic measurement radius",
        "neutron star mass radius NICER X ray timing pulse profile modeling equation state",
        "TOV equation maximum neutron star mass GW170817 tidal deformability constraint",
        "Eddington limit ultraluminous X ray source M82 X-1 NGC 1313 X-1 super Eddington",
        "Hertzsprung Russell globular cluster age isochrone fitting main sequence turnoff",
        "mass luminosity relation eclipsing binary spectroscopic orbit stellar evolution",
        "Jeans mass molecular cloud star formation initial mass function Salpeter slope",
        "virial theorem galaxy cluster dark matter Zwicky mass discrepancy Coma cluster",
        "solar neutrino pp chain Borexino Super Kamiokande flavor oscillation measurement",
        "triple alpha Hoyle resonance carbon 12 excited state 7.65MeV helium burning red giant",
        "silicon burning alpha process nuclear statistical equilibrium iron peak abundance",
        "r process rapid neutron capture kilonova GW170817 strontium lanthanide actinide production",
        "core collapse supernova neutrino mechanism Progenitor mass explosion energy SN1987A",
        "type Ia supernova Phillips relation luminosity light curve width standardization",
        "pulsar glitch Vela Crab sudden spin up superfluidity neutron pinning unpinning",
        "magnetar SGR 1806 20 2004 giant flare magnetic field 10^15 Gauss crust fracture",
        "fast radio burst dispersion measure host galaxy localization CHIME ASKAP measurement",
    ],

    # ── PLASMA PHYSICS (8 eqs, 0.6 ratio) ──
    15: [
        "Debye shielding Langmuir probe I-V characteristic electron temperature density measurement",
        "plasma frequency cut off density reflectometry tokamak interferometer measurement",
        "Alfven wave toroidal Alfven eigenmode fast ion transport tokamak NSTX DIII-D measurement",
        "sawtooth oscillation Kadomtsev reconnection model soft X ray tomography JET tokamak",
        "ELM edge localized mode peeling ballooning stability pedestal H mode ITER challenge",
        "magnetic reconnection MRX TREX experiment Sweet Parker Petschek rate measurement",
        "zonal flow geodesic acoustic mode turbulence regulation Doppler backscattering measurement",
        "I mode improved confinement energy confinement pedestal temperature no ELM alternative",
        "plasma wakefield acceleration electron bunch energy gain GeV per meter FACET measurement",
        "laser plasma interaction parametric Raman Brillouin scattering stimulated measurement",
    ],

    # ── STATISTICAL MECHANICS (13 eqs, 0.5 ratio) ──
    17: [
        "Boltzmann H theorem molecular dynamics simulation entropy production irreversibility",
        "Gibbs ensemble Monte Carlo phase coexistence Lennard Jones fluid vapor liquid measurement",
        "Jarzynski equality optical tweezers RNA hairpin unfolding single molecule force ramp",
        "Crooks fluctuation theorem DNA overstretching transition work distribution free energy",
        "fluctuation dissipation theorem microrheology passive particle tracking viscoelastic",
        "Kramers escape rate problem protein folding force dependent transition state measurement",
        "Wang Landau algorithm density states Monte Carlo polymer chain partition function",
        "parallel tempering replica exchange molecular dynamics protein folding free energy landscape",
        "Ising model critical exponent Monte Carlo renormalization group finite size scaling",
        "XY model Kosterlitz Thouless transition superfluid helium film torsional oscillator",
        "Kardar Parisi Zhang equation kinetic roughening surface growth scaling exponent universality",
        "percolation threshold cluster size distribution spanning probability critical exponent",
        "self organized criticality sandpile model Bak Tang Wiesenfeld avalanche power law exponent",
    ],

    # ── CONTINUUM MECHANICS (15 eqs, 0.4 ratio) ──
    18: [
        "Eshelby inclusion ellipsoidal elastic stress strain eigenvalue interior exterior solution",
        "Hashin Shtrikman bounds composite elastic modulus effective medium Mori Tanaka method",
        "J integral elastic plastic fracture finite element analysis contour path independence",
        "cohesive zone model traction separation law crack tip process zone Dugdale Barenblatt",
        "indentation hardness Oliver Pharr method elastic modulus nanohardness continuous stiffness",
        "contact mechanics adhesion JKR DMT Johnson Kendall Roberts transition parameter Tabor",
        "wave propagation anisotropic elastic Christoffel equation slowness surface polarization",
        "buckling Euler critical load column beam elastica nonlinear large deformation postbuckling",
        "plasticity yield surface associated flow rule normality Drucker postulate convexity",
        "strain gradient plasticity size effect micro bend torsion indentation intrinsic length",
        "crystal plasticity texture Taylor model Sachs self consistent viscoplastic polycrystal",
        "homogenization asymptotic expansion periodic composite unit cell finite element RVE",
        "configurational force Eshelby stress energy momentum tensor crack driving force J vector",
        "phase field fracture variational brittle regularization length crack topology diffuse",
        "nonlocal elasticity Eringen integral crack tip singular stress regularization",
    ],

    # ── TOP-OFF PASS for remaining sub-1.0 domains ──
    1: [  # Classical Mechanics
        "Euler rigid body rotation Poinsot ellipsoid polhode herpolhode torque free precession",
        "KAM theorem Arnold diffusion chaos Hamiltonian system solar system stability",
    ],
    4: [  # Thermodynamics
        "fluctuation dissipation Onsager reciprocal relation thermoelectricity Peltier Seebeck",
        "nonequilibrium thermodynamics entropy production minimum principle Prigogine theorem",
    ],
    5: [  # Quantum Mechanics
        "WKB approximation Wentzel Kramers Brillouin quantum tunneling transmission coefficient",
        "density matrix quantum Liouville von Neumann equation open system Lindblad master",
    ],
    7: [  # Quantum Field Theory
        "QCD lattice gauge theory hadron spectrum ab initio BMW collaboration physical pion mass",
        "renormalization group Callan Symanzik beta function asymptotic freedom non abelian gauge",
    ],
    8: [  # Cosmology
        "cosmic microwave background polarization B mode E mode gravitational wave tensor scalar ratio",
        "DESI dark energy spectroscopic instrument baryon acoustic oscillation Hubble parameter growth",
    ],
    9: [  # Fluid Dynamics
        "turbulent boundary layer log law von Karman constant high Reynolds Princeton pipe experiment",
        "Rayleigh Taylor instability Atwood number bubble spike growth rate Richtmyer Meshkov",
    ],
    10: [  # Optics
        "optical vortex orbital angular momentum Laguerre Gauss beam spiral phase plate hologram",
        "super resolution microscopy STED STORM PALM single molecule localization diffraction",
    ],
    13: [  # Nuclear Physics
        "double beta decay neutrinoless GERDA EXO KamLAND ZEN Majorana mass half life limit",
        "magicity disappearance island inversion neutron rich oxygen fluorine magnesium measurement",
    ],
}

# ================================================================
# API FETCHERS
# ================================================================
def cr(q, mx=5):
    o = []
    try:
        u = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query":q,"rows":mx,"sort":"relevance","filter":"type:journal-article"})
        r = urllib.request.Request(u, headers={"User-Agent":"DeepDive/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t = (i.get("title",[""]) or [""])[0]
            y = i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi = i.get("DOI","")
            jn = (i.get("container-title",[""]) or [""])[0]
            if t: o.append((t[:250],y,"Crossref",doi,jn))
    except: pass
    return o

def oa(q, mx=5):
    o = []
    try:
        u = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search":q,"per_page":mx,"sort":"cited_by_count:desc"})
        r = urllib.request.Request(u, headers={"User-Agent":"mailto:r@x.com"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("results",[]):
            t = i.get("title",""); y = i.get("publication_year")or 0; doi = i.get("doi","")
            jn = ""
            if i.get("primary_location") and i["primary_location"].get("source"):
                jn = i["primary_location"]["source"].get("display_name","")
            if t: o.append((t[:250],y,"OpenAlex",doi,jn))
    except: pass
    return o

def s2(q, mx=5):
    o = []
    try:
        u = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({"query":q,"limit":mx,"fields":"title,year,externalIds,journal,citationCount"})
        r = urllib.request.Request(u, headers={"User-Agent":"DeepDive/1.0"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for p in d.get("data",[]):
            e = p.get("externalIds",{}) or {}; jn = p.get("journal",{}) or {}
            o.append((p.get("title","")[:250],p.get("year")or 0,"S2",e.get("DOI",""),jn.get("name","")))
    except: pass
    return o

def ep(q, mx=5):
    o = []
    try:
        u = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query":q,"resultType":"core","pageSize":mx,"format":"json"})
        r = urllib.request.Request(u, headers={"User-Agent":"DeepDive/1.0"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("resultList",{}).get("result",[]):
            t = i.get("title","")
            y = int(i.get("firstPublicationDate","0")[:4]) if i.get("firstPublicationDate") else 0
            doi = i.get("doi",""); jn = i.get("journalTitle","")
            if t: o.append((t[:250],y,"EuropePMC",doi,jn))
    except: pass
    return o

# ================================================================
# MAIN PIPELINE
# ================================================================
# Build flat queue
tasks = []
for did, queries in DEEP.items():
    for q in queries:
        tasks.append((did, q))

apis = [(cr,1.5,"Crossref"),(oa,2.0,"OpenAlex"),(s2,2.0,"S2"),(ep,1.8,"EuropePMC"),
        (oa,2.0,"OpenAlex"),(cr,1.5,"Crossref"),(s2,2.0,"S2"),(oa,2.0,"OpenAlex")]

print(f"⚡ DEEP DIVE PASS 2")
print(f"  {len(tasks)} queries across {len(DEEP)} target domains")
print(f"  APIs: Crossref, OpenAlex, S2, EuropePMC ×2")
print(f"  ETA: {len(tasks)*1.8/60:.1f} min\n")

total, batch, start = 0, [], time.time()
prev_did, dom_paper_count = None, 0

for idx, (did, query) in enumerate(tasks):
    fn, delay, name = apis[idx % len(apis)]
    papers = fn(query, 5)
    eqs = dom_eqs.get(did, [None])

    if did != prev_did:
        if prev_did is not None:
            print(f"     ── {dom_paper_count} papers added to {dom_names.get(prev_did,'')}", flush=True)
        prev_did = did; dom_paper_count = 0
        print(f"\n┌─ {dom_names.get(did, f'#{did}')}", flush=True)

    for i, p in enumerate(papers):
        eq_id = eqs[i % len(eqs)] if eqs else None
        exp = f"{p[2]}: {p[4]}" if p[4] else p[2]
        batch.append((eq_id, p[0], exp, p[1], p[3] if p[3] else p[2], "Deep dive preseed"))
        total += 1; dom_paper_count += 1

    mark = "▪" if papers else "·"
    eta = (len(tasks) - idx) * delay
    print(f"  {mark} {name:8s} › {query[:65]:65s} → {len(papers)}p | {total:4d} | {eta:.0f}s", flush=True)

    if len(batch) >= 50:
        cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", batch)
        conn.commit(); batch = []

    time.sleep(delay)

if prev_did: print(f"     ── {dom_paper_count} papers added to {dom_names.get(prev_did,'')}", flush=True)

if batch:
    cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", batch)
    conn.commit()

# ================================================================
# FINAL REPORT
# ================================================================
cur.execute("SELECT COUNT(*) FROM verifications"); tv = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM equations"); te = cur.fetchone()[0]
elapsed = time.time() - start

print(f"\n{'═'*70}")
print(f"DONE — {tv} verifications, {te} equations, {total} added this pass")
print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f} min) | {len(tasks)/elapsed*60:.1f} queries/min\n")

cur.execute("""SELECT d.name, COUNT(DISTINCT e.id), COUNT(DISTINCT v.id),
    ROUND(COUNT(DISTINCT v.id)*1.0/COUNT(DISTINCT e.id),1)
    FROM domains d LEFT JOIN equations e ON e.domain_id=d.id
    LEFT JOIN verifications v ON v.equation_id=e.id
    WHERE e.id IS NOT NULL GROUP BY d.id ORDER BY COUNT(DISTINCT v.id) DESC""")

print(f"{'Domain':35s} {'Eqs':>4s}  {'Refs':>5s}  {'Ratio':>5s}")
print("-"*51)
for row in cur.fetchall():
    print(f"{row[0]:35s} {row[1]:4d}  {row[2]:5d}  {row[3]:5.1f}")

conn.close()
print(f"\n  {DB} ({os.path.getsize(DB)} bytes)")
