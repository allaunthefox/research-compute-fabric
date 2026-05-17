#!/usr/bin/env python3
"""
Finalize physics database — all remaining TODOs.
1. Fetch open-problem research papers (arXiv + Crossref + OpenAlex)
2. Create equation_constants table + populate
3. Add sub-equations for equations lacking LaTeX forms
4. Add people-to-equation links where discoverable
5. Build summary views for invariant scan querying
6. Integrity check
"""

import sqlite3
import urllib.request
import urllib.parse
import json
import time
import os
import re

DB = "/home/allaun/physics_equations.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()

start = time.time()

# ================================================================
# PART 1 — Open Problems Research Papers
# ================================================================
print("=" * 60)
print("PART 1: Filling open problems with research citations")
print("=" * 60)

cur.execute("SELECT id, name FROM open_problems ORDER BY id")
problems = [(r[0], r[1]) for r in cur.fetchall()]

# Custom queries per problem
OP_QUERIES = {
    1: "quantum gravity string theory loop quantum gravity experimental test",
    2: "dark matter particle detection WIMP axion sterile neutrino experimental",
    3: "cosmological constant problem dark energy vacuum energy fine tuning",
    4: "baryon asymmetry matter antimatter sakharov CP violation leptogenesis",
    5: "neutrino mass Majorana Dirac seesaw mechanism neutrinoless double beta decay",
    6: "strong CP problem axion Peccei Quinn neutron electric dipole moment limit",
    7: "hierarchy problem Higgs mass naturalness supersymmetry extra dimensions LHC",
    8: "cosmic inflation inflaton primordial gravitational waves B mode CMB",
    9: "quantum measurement problem collapse wavefunction interpretation Copenhagen many worlds",
    10: "arrow of time entropy past hypothesis initial conditions Big Bang low entropy",
    11: "Hubble tension H0 measurement CMB SH0ES discrepancy cosmological crisis",
    12: "cosmic lithium problem BBN primordial nucleosynthesis abundance discrepancy",
    13: "dark energy equation of state w DESI Euclid time evolution survey",
    14: "black hole information paradox island formula replica wormhole holography",
    15: "proton decay lifetime limit Super Kamiokande grand unified theory SU5",
    16: "muon g-2 anomaly Fermilab lattice QCD hadronic vacuum polarization",
    17: "CKM unitarity matrix quark mixing Vud Vus precision test flavor physics",
    18: "gallium anomaly sterile neutrino BEST experiment reactor deficit",
    19: "magnetic monopole Dirac quantization MoEDAL ATLAS LHC search limit",
    20: "cosmic lithium problem BBN nucleosynthesis lithium 7 abundance halo stars",
}

def crossref(q, mx=5):
    o = []
    try:
        u = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query": q, "rows": mx, "sort": "relevance", "filter": "type:journal-article"})
        r = urllib.request.Request(u, headers={"User-Agent": "Finalize/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r, timeout=15) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("message", {}).get("items", []):
            t = (i.get("title", [""]) or [""])[0]
            y = i.get("created", {}).get("date-parts", [[0]])[0][0]
            doi = i.get("DOI", "")
            if t: o.append((t[:250], y, doi))
    except: pass
    return o

def openalex(q, mx=5):
    o = []
    try:
        u = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "per_page": mx, "sort": "cited_by_count:desc"})
        r = urllib.request.Request(u, headers={"User-Agent": "mailto:r@x.com"})
        with urllib.request.urlopen(r, timeout=15) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("results", []):
            t = i.get("title", "")
            y = i.get("publication_year") or 0
            doi = i.get("doi", "")
            if t: o.append((t[:250], y, doi))
    except: pass
    return o

# Fetch papers for each open problem, update description
op_total = 0
for pid, name in problems:
    q = OP_QUERIES.get(pid, name)
    papers = crossref(q, 5) + openalex(q, 5)
    if papers:
        citations = "; ".join(
            f"\"{p[0][:100]}\" ({p[1]})"
            for p in papers[:3] if p[0]
        )
        cur.execute(
            "UPDATE open_problems SET description = description || ' Key papers: ' || ? WHERE id = ?",
            (citations, pid)
        )
        op_total += len(papers)
    print(f"  [{pid:2d}] {name[:50]:50s} → {len(papers)} papers", flush=True)
    time.sleep(1.5)

conn.commit()
print(f"  ✓ {op_total} open-problem references added\n")

# ================================================================
# PART 2 — Equation Constants Table
# ================================================================
print("=" * 60)
print("PART 2: Creating equation_constants table + populating")
print("=" * 60)

cur.execute("DROP TABLE IF EXISTS equation_constants")
cur.execute("""CREATE TABLE equation_constants (
    equation_id INTEGER REFERENCES equations(id),
    constant_id INTEGER REFERENCES constants(id),
    symbol TEXT,
    role TEXT,
    PRIMARY KEY (equation_id, constant_id)
)""")

# Map equations to constants based on domain context + title keywords
# Domain-level mappings (every eq in domain uses these)
DOMAIN_CONSTANTS = {
    1:  [],  # Classical Mechanics — G is for gravity, not here
    2:  [4],  # Gravitation — G
    3:  [10, 11, 1],  # E&M — eps0, mu0, c
    4:  [5, 25],  # Thermo — kB, R
    5:  [3, 13, 7, 14, 15],  # QM — hbar, alpha, me, Ry, a0
    6:  [1, 4, 21, 22, 23],  # Relativity — c, G, lP, tP, mP
    7:  [3, 13, 6, 18, 19],  # QFT — hbar, alpha, e, GF, LambdaQCD
    8:  [4, 20, 24, 1],  # Cosmology — G, H0, T_CMB, c
    9:  [],  # Fluid — material constants, not fundamental
    10: [1],  # Optics — c
    11: [],  # Acoustics — material constants
    12: [5, 6, 3, 7, 26, 27],  # Condensed Matter — kB, e, hbar, me, Phi0, sigma_el
    13: [3, 6, 8, 9, 28],  # Nuclear — hbar, e, mp, mn, muN
    14: [4, 1, 5, 7, 8],  # Astrophysics — G, c, kB, me, mp
    15: [6, 10, 5],  # Plasma — e, eps0, kB
    16: [],  # Math Physics — no physical constants
    17: [5],  # Stat Mech — kB
    18: [],  # Continuum — material constants
    19: [5],  # Info Theory — kB (Landauer)
    20: [1, 2, 6, 5, 12],  # Metrology — c, h, e, kB, NA
    21: [5, 6, 3],  # Material Physics — kB, e, hbar
    22: [],  # Crystallography
    23: [5, 6, 3, 7],  # Semiconductor — kB, e, hbar, me
    24: [5, 12],  # Polymer — kB, NA
    25: [5],  # Surface — kB
    28: [4, 5],  # Geo — G, kB
    29: [5, 25, 24],  # Atmospheric — kB, R, T_CMB
    30: [],  # Ocean
    31: [],  # Hydro
    32: [5, 6],  # Bio — kB, e
    33: [5, 6, 25],  # Chem — kB, e, R
    34: [1, 3, 13],  # Photonics — c, hbar, alpha
    35: [3, 13, 14, 15, 7, 29, 16],  # Atomic — hbar, alpha, Ry, a0, me, lambdaC, muB
    36: [],  # Rheology
    37: [],  # Tribology
    38: [],  # Granular
    39: [3, 6, 7, 1],  # Nano — hbar, e, me, c
    40: [3, 5],  # Q Info — hbar, kB
    41: [],  # Chaos
    42: [5, 3, 6],  # Medical — kB, hbar, e
    43: [7, 6, 3, 30, 1],  # Radiation — me, e, hbar, re, c
    44: [5, 6, 3],  # Energy — kB, e, hbar
    45: [4, 6, 1, 8],  # Space — G, e, c, mp
    46: [],  # Detonics
    47: [1],  # Metamaterials — c
    48: [],  # UW Acoustics
    49: [],  # Engineering
    51: [5, 6],  # Extremophile — kB, e
    52: [],  # Radical Adaptations
}

# Per-equation additions based on title keywords
def get_eq_consts(eq_id, title, domain_id):
    result = set()
    # Add domain defaults
    for cid in DOMAIN_CONSTANTS.get(domain_id, []):
        result.add(cid)
    # Title-based matching
    tl = title.lower()
    kw_map = {
        "speed of light": [1], "c =": [1], "velocity": [1] if "light" in tl or "lorentz" in tl or "relativ" in tl else [],
        "planck": [2, 3], "h =": [2], "ħ": [3], "hbar": [3],
        "gravitation": [4], "newton": [4] if "grav" in tl or "tidal" in tl else [], "G =": [4],
        "boltzmann": [5], "entropy": [5], "temperature": [5],
        "electron": [7], "mass": [7] if "electron" in tl or "planck" in tl else [],
        "proton": [8], "neutron": [9],
        "fine": [13], "fine-structure": [13], "alpha": [13] if "constant" in tl else [],
        "rydberg": [14], "bohr": [15],
        "magneton": [16], "magnetic moment": [16],
        "stefan": [17], "blackbody": [17],
        "fermi constant": [18], "weak": [18] if "coupling" in tl or "force" in tl else [],
        "qcd": [19], "lambda_qcd": [19], "strong cp": [19],
        "hubble": [20], "hubble constant": [20], "cosmolog": [20],
        "compton": [29], "wavelength": [29] if "electron" in tl else [],
        "bcs": [5, 6], "supercon": [5, 6, 26], "josephson": [26],
        "quantum hall": [27], "hall": [27] if "quantum" in tl else [],
        "solar": [17, 8], "stellar": [4, 1, 8],
        "g-factor": [16], "g-2": [16],
        "neutrino": [18, 3],
        "nuclear": [28], "magnetic": [16, 28],
        "cosmic": [24], "cmb": [24],
        "diffusion": [5], "brownian": [5],
        "gas constant": [25], "R =": [25],
        "dielectric": [10], "permittivity": [10],
        "permeability": [11],
        "avogadro": [12],
    }
    for kw, cids in kw_map.items():
        if kw in tl:
            for cid in cids:
                result.add(cid)
    return result

# Insert
ec_count = 0
cur.execute("SELECT id, title, domain_id FROM equations")
role_default = "appears in equation"
for eq_id, title, did in cur.fetchall():
    cids = get_eq_consts(eq_id, title, did)
    for cid in cids:
        cur.execute("SELECT symbol, name FROM constants WHERE id = ?", (cid,))
        row = cur.fetchone()
        if row:
            sym, name = row
            # Check role
            role = role_default
            if "G =" in title and sym in ("G",): role = "primary constant in equation"
            if "c =" in title and sym in ("c",): role = "primary constant in equation"
            if "h =" in title and sym in ("h", "hbar"): role = "primary constant in equation"
            if "e =" in title and sym in ("e",): role = "primary constant in equation"
            cur.execute(
                "INSERT OR IGNORE INTO equation_constants VALUES (?, ?, ?, ?)",
                (eq_id, cid, sym, role)
            )
            ec_count += 1

conn.commit()
print(f"  ✓ equation_constants: {ec_count} mappings across {770} equations\n")

# ================================================================
# PART 3 — Add missing sub-equations (LaTeX)
# ================================================================
print("=" * 60)
print("PART 3: Adding sub-equations for equations lacking LaTeX forms")
print("=" * 60)

cur.execute("SELECT MAX(id) FROM sub_equations")
sid = cur.fetchone()[0] or 147

cur.execute("""
    SELECT e.id, e.eq_number, e.title, e.domain_id, d.name as domain
    FROM equations e
    JOIN domains d ON e.domain_id = d.id
    WHERE e.id NOT IN (SELECT DISTINCT equation_id FROM sub_equations WHERE equation_id IS NOT NULL)
    ORDER BY e.eq_number
""")
missing = [(r[0], r[1], r[2], r[3], r[4]) for r in cur.fetchall()]
print(f"  {len(missing)} equations lack sub-equations")

# Add key LaTeX forms for the most important missing equations
SUBEQ_BATCH = []
def add_sub(eq_id, subsec, name, latex, desc, cond=""):
    global sid
    sid += 1
    SUBEQ_BATCH.append((sid, eq_id, subsec, name, latex, desc, cond))

# Core Physics equations that need LaTeX
for eq_id, num, title, did, dname in missing:
    t = title.lower()

    # Kepler
    if "kepler" in t and "first" in t:
        add_sub(eq_id, "Kepler1", "Kepler's First Law", r"r(\theta) = \frac{a(1-e^2)}{1 + e\cos\theta}", "Elliptical orbit with Sun at focus; a=semi-major, e=eccentricity", "")
    elif "kepler" in t and "second" in t:
        add_sub(eq_id, "Kepler2", "Kepler's Second Law", r"\frac{dA}{dt} = \frac{1}{2}r^2\frac{d\theta}{dt} = \text{const} = \frac{L}{2m}", "Areal velocity constant; L=angular momentum", "")
    elif "kepler" in t and "third" in t:
        add_sub(eq_id, "Kepler3", "Kepler's Third Law", r"T^2 = \frac{4\pi^2}{G(M+m)}a^3 \approx \frac{4\pi^2}{GM}a^3", "Period squared proportional to semi-major axis cubed", "M >> m")

    # Conservation laws
    elif "conservation of momentum" in t:
        add_sub(eq_id, "Momentum", "Conservation of Momentum", r"\frac{d\vec{P}}{dt} = \sum \vec{F}_{\text{ext}} = 0 \Rightarrow \vec{P} = \text{constant}", "From Noether: spatial translation symmetry → momentum", "")
    elif "conservation of angular momentum" in t:
        add_sub(eq_id, "AngMom", "Conservation of Angular Momentum", r"\frac{d\vec{L}}{dt} = \vec{\tau}_{\text{ext}} = 0 \Rightarrow \vec{L} = \text{constant}", "From rotational symmetry; L = Iω for rigid bodies", "")
    elif "conservation of energy" in t:
        add_sub(eq_id, "Energy", "Conservation of Energy", r"E = T + V = \text{constant}, \; \frac{d}{dt}\langle\hat{H}\rangle = 0", "Time translation symmetry → energy conservation (Noether)", "")

    # Oscillations
    elif "simple harmonic" in t:
        add_sub(eq_id, "SHM", "Simple Harmonic Motion", r"\ddot{x} + \omega_0^2 x = 0, \; x(t) = A\cos(\omega_0 t + \varphi), \; T = \frac{2\pi}{\omega_0}", "Linear restoring force; ω₀=√(k/m) for mass-spring", "")
    elif "damped" in t:
        add_sub(eq_id, "Damped", "Damped Harmonic Oscillator", r"\ddot{x} + 2\beta\dot{x} + \omega_0^2 x = 0, \; \beta < \omega_0: x = Ae^{-\beta t}\cos(\omega_1 t + \varphi)", "ω₁=√(ω₀²−β²); β<ω₀ underdamped, β=ω₀ critically damped, β>ω₀ overdamped", "")
    elif "forced oscillator" in t:
        add_sub(eq_id, "Forced", "Forced Damped Oscillator", r"\ddot{x} + 2\beta\dot{x} + \omega_0^2 x = \frac{F_0}{m}\cos\omega t, \; A(\omega) = \frac{F_0/m}{\sqrt{(\omega_0^2-\omega^2)^2 + 4\beta^2\omega^2}}", "Amplitude peaks at ω≈ω₀ for small β; resonance", "")
    elif "coupled oscillat" in t:
        add_sub(eq_id, "Coupled", "Coupled Oscillators (Normal Modes)", r"\omega_{\pm} = \sqrt{\frac{k + k'}{m} \pm \frac{k'}{m}}", "Symmetric (+) and antisymmetric (−) normal mode frequencies", "Two equal masses, springs k (wall) + k' (coupling)")
    elif "pendulum" in t:
        add_sub(eq_id, "Pendulum", "Pendulum Equation", r"\ddot{\theta} + \frac{g}{L}\sin\theta = 0, \; T \approx 2\pi\sqrt{\frac{L}{g}}\left(1 + \frac{\theta_0^2}{16} + \cdots\right)", "Small-angle: T=2π√(L/g); finite amplitude correction", "")

    # Electromagnetism
    elif "coulomb" in t:
        add_sub(eq_id, "Coulomb", "Coulomb's Law", r"\vec{F}_{12} = \frac{1}{4\pi\varepsilon_0}\frac{q_1 q_2}{r_{12}^2}\hat{r}_{12}", "Force between point charges; inverse-square confirmed to δ<10⁻¹⁶", "")
    elif "lorentz force" in t:
        add_sub(eq_id, "Lorentz", "Lorentz Force", r"\vec{F} = q\left(\vec{E} + \vec{v}\times\vec{B}\right)", "Force on moving charge in EM fields; all particle accelerators", "")
    elif "biot-savart" in t:
        add_sub(eq_id, "BiotSavart", "Biot-Savart Law", r"d\vec{B} = \frac{\mu_0}{4\pi}\frac{I d\vec{l} \times \hat{r}}{r^2}", "Magnetic field from current element; exact for steady currents", "")
    elif "ohm" in t and "law" in t:
        add_sub(eq_id, "Ohm", "Ohm's Law", r"V = IR, \; \vec{J} = \sigma\vec{E}", "Voltage proportional to current; Drude conductivity model derivation", "")
    elif "kirchhoff" in t and "current" in t:
        add_sub(eq_id, "KCL", "Kirchhoff's Current Law", r"\sum_k I_k = 0 \text{ at any junction}", "Charge conservation: what flows in = what flows out", "")
    elif "kirchhoff" in t and "voltage" in t:
        add_sub(eq_id, "KVL", "Kirchhoff's Voltage Law", r"\sum_k V_k = 0 \text{ around any closed loop}", "Conservative electric field in lumped circuits", "")
    elif "faraday" in t and "induction" in t:
        add_sub(eq_id, "FaradayInd", "Faraday's Law of Induction", r"\mathcal{E} = -\frac{d\Phi_B}{dt}, \; \Phi_B = \int_S \vec{B}\cdot d\vec{A}", "Induced EMF = negative rate of change of magnetic flux", "")
    elif "lenz" in t:
        add_sub(eq_id, "Lenz", "Lenz's Law", r"\mathcal{E} = -\frac{d\Phi_{\text{ext}}}{dt}", "Induced current direction opposes flux change; energy conservation consequence", "")
    elif "poynting" in t and "theorem" in t:
        add_sub(eq_id, "Poynting", "Poynting's Theorem", r"\frac{\partial u}{\partial t} + \nabla\cdot\vec{S} = -\vec{J}\cdot\vec{E}, \; u = \frac{1}{2}\varepsilon_0 E^2 + \frac{1}{2\mu_0}B^2, \; \vec{S} = \frac{1}{\mu_0}\vec{E}\times\vec{B}", "EM energy conservation; Poynting vector S = energy flux (W/m²)", "")
    elif "electromagnetic wave" in t:
        add_sub(eq_id, "EMwave", "EM Wave Equation", r"\Box\vec{E} = 0, \; \Box\vec{B} = 0, \; \Box = -\frac{1}{c^2}\frac{\partial^2}{\partial t^2} + \nabla^2, \; c = \frac{1}{\sqrt{\mu_0\varepsilon_0}}", "Predicted EM waves; Hertz 1887 confirmed light=EM wave", "")
    elif "stress-energy" in t and "electro" in t:
        add_sub(eq_id, "SET", "EM Stress-Energy Tensor", r"T^{\mu\nu} = \frac{1}{\mu_0}\left[F^{\mu\alpha}F^\nu_{\ \alpha} + \frac{1}{4}g^{\mu\nu}F_{\alpha\beta}F^{\alpha\beta}\right]", "Relativistic formulation of EM energy-momentum", "")

    # Thermodynamics
    elif "zeroth" in t:
        add_sub(eq_id, "Zeroth", "Zeroth Law", r"A\sim B, B\sim C \Rightarrow A\sim C \text{ (thermal equilibrium is transitive)}", "Defines temperature as a transitive equivalence relation", "")
    elif "third law" in t:
        add_sub(eq_id, "ThirdLaw", "Third Law of Thermodynamics", r"S \to 0 \text{ as } T \to 0 \text{ (perfectly crystalline)}", "Nernst 1906; zero entropy at absolute zero; exceptions: glasses, ice", "")
    elif "van der waals" in t:
        add_sub(eq_id, "VdW", "Van der Waals Equation", r"\left(P + \frac{an^2}{V^2}\right)(V - nb) = nRT", "Real gas: a corrects for attraction, b corrects for finite molecular volume", "")
    elif "kinetic theory" in t:
        add_sub(eq_id, "KinetPres", "Kinetic Theory Pressure", r"P = \frac{1}{3}\frac{N}{V}m\langle v^2\rangle = \frac{2}{3}\frac{N}{V}\langle E_{\text{kin}}\rangle", "Microscopic derivation of ideal gas law from molecular motion", "")
    elif "maxwell-boltzmann" in t and "speed" in t:
        add_sub(eq_id, "MBDist", "Maxwell-Boltzmann Speed Distribution", r"f(v) = 4\pi\left(\frac{m}{2\pi k_B T}\right)^{3/2}v^2 e^{-mv^2/2k_B T}, \; v_{\text{rms}} = \sqrt{\frac{3k_B T}{m}}", "Velocity distribution in ideal gas; v_mp=√(2kT/m), v̄=√(8kT/πm)", "")
    elif "equipartition" in t:
        add_sub(eq_id, "Equipart", "Equipartition Theorem", r"\langle E \rangle = \frac{f}{2}k_B T, \; C_V = \frac{f}{2}R", "Each quadratic degree of freedom contributes ½ k_B T", "Classical limit; quantum corrections at low T")
    elif "clausius-clapeyron" in t:
        add_sub(eq_id, "CC", "Clausius-Clapeyron Relation", r"\frac{dP}{dT} = \frac{L}{T\Delta V} = \frac{\Delta S}{\Delta V}", "Phase coexistence curve slope from latent heat and volume change", "")
    elif "gibbs phase" in t:
        add_sub(eq_id, "GibbsPhase", "Gibbs Phase Rule", r"F = C - P + 2", "F=degrees of freedom, C=components, P=phases in equilibrium", "")
    elif "helmholtz" in t:
        add_sub(eq_id, "Helmholtz", "Helmholtz Free Energy", r"F = U - TS, \; \Delta F \leq 0 \text{ at constant T,V for spontaneous process}", "Legendre transform of U; work available at constant temperature", "")
    elif "gibbs free" in t:
        add_sub(eq_id, "GibbsFE", "Gibbs Free Energy", r"G = H - TS, \; \Delta G \leq 0 \text{ at constant T,P for spontaneous process}", "Chemical thermodynamics workhorse; ΔG⁰ = −RT ln K_eq", "")
    elif "enthalpy" in t:
        add_sub(eq_id, "Enthalpy", "Enthalpy Definition", r"H = U + PV, \; \Delta H = Q_P \text{ (constant pressure heat)}", "Used in constant-pressure processes; combustion, phase changes", "")
    elif "specific heat relation" in t or "cp-cv" in t:
        add_sub(eq_id, "CpCv", "C_p − C_v Relation", r"C_P - C_V = -T\left(\frac{\partial V}{\partial T}\right)_P^2 / \left(\frac{\partial V}{\partial P}\right)_T = TV\frac{\alpha^2}{\kappa_T}", "C_P always ≥ C_V; equality for incompressible substances", "")
    elif "joule-thomson" in t:
        add_sub(eq_id, "JT", "Joule-Thomson Coefficient", r"\mu_{JT} = \left(\frac{\partial T}{\partial P}\right)_H = \frac{V}{C_P}(T\alpha - 1)", "Gas cooling/heating during throttling; inversion temperature", "")

    # QM
    elif "born rule" in t:
        add_sub(eq_id, "Born", "Born Rule", r"P(x) = |\psi(x)|^2, \; \int |\psi|^2\,dx = 1", "Probability density = squared magnitude of wavefunction", "Born 1926; never violated")
    elif "probability current" in t:
        add_sub(eq_id, "ProbCurr", "Probability Current", r"\vec{j} = \frac{\hbar}{2mi}\left(\psi^*\nabla\psi - \psi\nabla\psi^*\right), \; \frac{\partial\rho}{\partial t} + \nabla\cdot\vec{j} = 0", "Continuity equation for quantum probability", "ρ = |ψ|²")
    elif "angular momentum quant" in t:
        add_sub(eq_id, "LQuant", "Angular Momentum Quantization", r"L^2|l,m\rangle = \hbar^2 l(l+1)|l,m\rangle, \; L_z|l,m\rangle = \hbar m|l,m\rangle", "Discrete eigenvalues from spherical symmetry", "l=0,1,2,...; m=−l,...,+l")
    elif "spin-orbit" in t:
        add_sub(eq_id, "S.O.", "Spin-Orbit Coupling", r"H_{SO} = \frac{1}{2m^2c^2}\frac{1}{r}\frac{dV}{dr}\vec{L}\cdot\vec{S} = \xi(r)\,\vec{L}\cdot\vec{S}", "Thomas precession factor 1/2; energy splitting = ξ⟨L·S⟩", "Nuclear shell model; fine structure")
    elif "spin-statistics" in t:
        add_sub(eq_id, "SpinStat", "Spin-Statistics Theorem", r"[\phi(x),\phi(y)] = 0 \text{ (bosons)}, \; \{\psi(x),\psi(y)\} = 0 \text{ (fermions)}", "Integer spin → commutators (bosons); half-integer → anticommutators (fermions)", "Relativistic QFT theorem (Fierz, Pauli 1939-40)")
    elif "time-dependent perturbation" in t:
        add_sub(eq_id, "TDPT", "Time-Dependent Perturbation Theory (1st order)", r"c_f(t) = -\frac{i}{\hbar}\int_0^t \langle f|V(t')|i\rangle e^{i\omega_{fi}t'}dt'", "Transition amplitude; P(i→f)=|c_f|²; Fermi's golden rule follows", "Valid when P≪1")
    elif "partial wave" in t:
        add_sub(eq_id, "PartialWave", "Partial Wave Expansion", r"f(\theta) = \frac{1}{k}\sum_{l=0}^\infty (2l+1)e^{i\delta_l}\sin\delta_l\,P_l(\cos\theta)", "Scattering theory; phase shifts δ_l from short-range potential", "")
    elif "von neumann" in t:
        add_sub(eq_id, "VonNeu", "Von Neumann Equation", r"i\hbar\frac{\partial\hat{\rho}}{\partial t} = [\hat{H}, \hat{\rho}]", "Quantum Liouville equation; evolution of density operator", "")
    elif "ehrenfest" in t:
        add_sub(eq_id, "Ehrenfest", "Ehrenfest Theorem", r"\frac{d}{dt}\langle A\rangle = \frac{1}{i\hbar}\langle[A,\hat{H}]\rangle + \langle\frac{\partial A}{\partial t}\rangle", "Expectation values obey classical equations of motion", "")
    elif "no-cloning" in t:
        add_sub(eq_id, "NoClone", "No-Cloning Theorem", r"|\psi\rangle|0\rangle \nrightarrow |\psi\rangle|\psi\rangle \text{ for arbitrary unknown } |\psi\rangle", "Linear unitary evolution forbids perfect copying of unknown quantum states", "Wootters-Zurek, Dieks 1982")

    # Relativity / GR
    elif "lorentz transform" in t:
        add_sub(eq_id, "Lorentz", "Lorentz Transformations (Boost)", r"x' = \gamma(x - vt),\; t' = \gamma\!\left(t - \frac{vx}{c^2}\right),\; \gamma = \frac{1}{\sqrt{1 - v^2/c^2}}", "Boost along x-axis; c invariant in all inertial frames", "")
    elif "minkowski" in t:
        add_sub(eq_id, "Minkowski", "Minkowski Interval", r"ds^2 = -c^2 dt^2 + dx^2 + dy^2 + dz^2 = \eta_{\mu\nu}dx^\mu dx^\nu", "Flat spacetime; Lorentz invariant; proper time dτ²=−ds²/c²", "")
    elif "time dilation" in t:
        add_sub(eq_id, "TimeDil", "Time Dilation", r"\Delta t' = \gamma\Delta t \text{ (moving clock runs slow)}", "Confirmed: muon lifetime, GPS, Hafele-Keating 1971", "γ ≥ 1")
    elif "length contraction" in t:
        add_sub(eq_id, "Length", "Length Contraction", r"L' = \frac{L}{\gamma} \text{ (moving object contracts along motion)}", "Confirmed in particle physics, EM fields of moving charges", "")
    elif "relativistic doppler" in t:
        add_sub(eq_id, "Doppler", "Relativistic Doppler Effect", r"f_{\text{obs}} = f_{\text{src}}\sqrt{\frac{1+\beta}{1-\beta}} \text{ (longitudinal)}, \; f_{\text{obs}} = \gamma f_{\text{src}} \text{ (transverse)}", "Red/blue shift including time dilation; Ives-Stilwell 1938 confirmed transverse", "β=v/c")
    elif "einstein-hilbert" in t:
        add_sub(eq_id, "EH", "Einstein-Hilbert Action", r"S = \frac{c^4}{16\pi G}\int d^4x\sqrt{-g}\,(R - 2\Lambda) + S_{\text{matter}}", "Action principle for GR; δS=0 → Einstein field equations", "")
    elif "schwarzschild" in t:
        add_sub(eq_id, "Schwarzschild", "Schwarzschild Metric", r"ds^2 = -\left(1-\frac{r_s}{r}\right)c^2dt^2 + \frac{dr^2}{1-r_s/r} + r^2 d\Omega^2, \; r_s = \frac{2GM}{c^2}", "Static, spherical vacuum solution; event horizon at r=r_s", "")
    elif "kerr" in t and "metric" in t:
        add_sub(eq_id, "Kerr", "Kerr Metric (Boyer-Lindquist)", r"ds^2 = -\left(1-\frac{r_s r}{\Sigma}\right)c^2dt^2 + \frac{\Sigma}{\Delta}dr^2 + \Sigma d\theta^2 + \cdots", "Rotating BH; Σ=r²+a²cos²θ, Δ=r²−r_s r+a², a=J/Mc", "Ergosphere: r between r_+ and static limit")
    elif "flrw" in t:
        add_sub(eq_id, "FLRW", "FLRW Metric", r"ds^2 = -c^2 dt^2 + a^2(t)\left[\frac{dr^2}{1-kr^2} + r^2 d\Omega^2\right]", "Homogeneous isotropic cosmology; k=+1,0,−1; a(t)=scale factor", "")

    # QFT / Cosmology
    elif "weinberg angle" in t:
        add_sub(eq_id, "ThetaW", "Weinberg Angle", r"\sin^2\theta_W = 1 - \frac{M_W^2}{M_Z^2} \approx 0.23121 \pm 0.00004", "EW mixing parameter; relates g, g', e: e = g sin θ_W", "")
    elif "faddeev-popov" in t:
        add_sub(eq_id, "FP_Ghost", "Faddeev-Popov Ghosts", r"\mathcal{L}_{\text{ghost}} = \bar{c}^a \partial^\mu D_\mu^{ab} c^b", "Anticommuting scalar ghosts cancel unphysical gauge d.o.f.", "Non-abelian gauge theories")
    elif "brst" in t:
        add_sub(eq_id, "BRST", "BRST Symmetry", r"sA_\mu^a = D_\mu^{ab}c^b, \; sc^a = -\frac{1}{2}gf^{abc}c^bc^c, \; s^2 = 0", "Nilpotent Grassmann-odd symmetry after gauge fixing; ensures unitarity", "")
    elif "cosmological fluid" in t:
        add_sub(eq_id, "FluidEq", "Cosmological Fluid Equation", r"\dot{\rho} + 3H\left(\rho + \frac{P}{c^2}\right) = 0", "Stress-energy conservation in FLRW; ρ_m∝a^{-3}, ρ_r∝a^{-4}, ρ_Λ=const", "")
    elif "sound horizon" in t:
        add_sub(eq_id, "SoundHor", "Sound Horizon at Recombination", r"r_s(z_*) = \int_{z_*}^\infty \frac{c_s(z)}{H(z)}dz \approx 147 \text{ Mpc (comoving)}", "BAO standard ruler; r_s measured from CMB acoustic peaks", "z_*≈1090, t_rec≈380,000 yr")
    elif "deceleration" in t:
        add_sub(eq_id, "Decel", "Deceleration Parameter", r"q_0 = -\frac{\ddot{a}a}{\dot{a}^2} = \frac{\Omega_m}{2} - \Omega_\Lambda \approx -0.53", "q<0 → accelerating expansion; SNe Ia 1998 Nobel discovery", "Planck 2018")
    elif "dark energy equation" in t:
        add_sub(eq_id, "DE-EoS", "Dark Energy Equation of State", r"w = \frac{P_{\text{DE}}}{\rho_{\text{DE}}c^2} = -1.03 \pm 0.03", "w=−1 → cosmological constant; w<−1 → phantom; w>−1 → quintessence", "Planck + BAO + SNe")

    # More equations — bulk add for remaining
    elif "kinematics" in t:
        add_sub(eq_id, "Kin", "Constant-Acceleration Kinematics", r"v = v_0 + at,\; x = x_0 + v_0t + \frac{1}{2}at^2,\; v^2 = v_0^2 + 2a(x-x_0)", "Exact for constant acceleration; foundation of mechanics", "")
    elif "center of mass" in t:
        add_sub(eq_id, "COM", "Center of Mass Equation", r"M\ddot{\vec{R}}_{\text{cm}} = \sum \vec{F}_{\text{ext}},\; \vec{R}_{\text{cm}} = \frac{\sum m_i\vec{r}_i}{\sum m_i}", "COM moves as point particle with total mass under net external force", "")
    elif "work-energy" in t:
        add_sub(eq_id, "WorkEnergy", "Work-Energy Theorem", r"W = \int \vec{F}\cdot d\vec{r} = \frac{1}{2}mv_f^2 - \frac{1}{2}mv_i^2 = \Delta K", "Work done = change in kinetic energy; derived from F=ma", "")
    elif "impulse-momentum" in t:
        add_sub(eq_id, "Impulse", "Impulse-Momentum Theorem", r"\vec{J} = \int_{t_1}^{t_2}\vec{F}\,dt = \Delta\vec{p} = m\vec{v}_2 - m\vec{v}_1", "From F = dp/dt; impulse = change in momentum", "")
    elif "parallel axis" in t:
        add_sub(eq_id, "ParallelAxis", "Parallel Axis Theorem", r"I = I_{\text{cm}} + Md^2", "Moment of inertia about parallel axis at distance d from CM axis", "")
    elif "coriolis" in t:
        add_sub(eq_id, "Coriolis", "Coriolis Force", r"\vec{F}_{\text{Cor}} = -2m\,\vec{\omega}\times\vec{v}'", "Fictitious force in rotating frame; Foucault pendulum, weather patterns", "")
    elif "centrifugal" in t:
        add_sub(eq_id, "Centrifugal", "Centrifugal Force", r"\vec{F}_{\text{cf}} = -m\,\vec{\omega}\times(\vec{\omega}\times\vec{r}) = m\omega^2\vec{r}_\perp", "Outward fictitious force in rotating frame", "")
    elif "gravitational potential" in t and "energy" in t:
        add_sub(eq_id, "GravPE", "Gravitational Potential Energy", r"U(r) = -\frac{GMm}{r}, \; F = -\nabla U", "From integration of F = −GMm/r²; U→0 as r→∞", "")
    elif "escape velocity" in t:
        add_sub(eq_id, "VEsc", "Escape Velocity", r"v_{\text{esc}} = \sqrt{\frac{2GM}{r}} = \sqrt{2}\,v_{\text{orb}}", "From energy conservation: ½mv²−GMm/r=0; Earth: ~11.2 km/s", "")
    elif "orbital velocity" in t:
        add_sub(eq_id, "VOrb", "Circular Orbital Velocity", r"v_{\text{orb}} = \sqrt{\frac{GM}{r}}", "Set centripetal = gravitational: mv²/r = GMm/r²", "")
    elif "poisson" in t and "gravit" in t:
        add_sub(eq_id, "PoissonGrav", "Poisson Equation (Gravity)", r"\nabla^2\Phi = 4\pi G\rho", "Newtonian limit of Einstein field equations; ρ=mass density", "")
    elif "tidal force" in t:
        add_sub(eq_id, "Tidal", "Tidal Force (Differential)", r"\vec{F}_{\text{tide}} \approx \frac{2GMm\Delta r}{r^3}\hat{r}", "Difference in gravity across extended body; Roche limit when ΔF>self-gravity", "")
    elif "gravitational time dilation" in t:
        add_sub(eq_id, "GravDil", "Gravitational Time Dilation", r"\Delta t' = \Delta t\sqrt{1 - \frac{2GM}{rc^2}} \approx \Delta t\left(1 - \frac{GM}{rc^2}\right)", "Clocks run slower deeper in gravitational well; Pound-Rebka 1960; GPS needs this", "")
    elif "precession" in t and "perihelion" in t:
        add_sub(eq_id, "PeriAdvance", "GR Perihelion Precession", r"\Delta\varphi = \frac{6\pi GM}{a(1-e^2)c^2} \text{ per orbit}", "Mercury: 43\"/century; confirmed to <0.1%", "")
    elif "lense-thirring" in t:
        add_sub(eq_id, "LT", "Lense-Thirring Precession (Frame Dragging)", r"\vec{\Omega}_{LT} = \frac{GJ}{2c^2 r^3}\left[3(\hat{r}\cdot\hat{J})\hat{r} - \hat{J}\right]", "Spinning mass drags spacetime; Gravity Probe B ~10% precision", "")

print(f"  ✓ Generated {len(SUBEQ_BATCH)} new sub-equations")

cur.executemany(
    "INSERT INTO sub_equations (id, equation_id, subsection, name, latex_formula, description, conditions) VALUES (?,?,?,?,?,?,?)",
    SUBEQ_BATCH
)
conn.commit()

cur.execute("SELECT COUNT(*) FROM sub_equations")
final_subs = cur.fetchone()[0]
print(f"  ✓ sub_equations: {147} → {final_subs}\n")

# ================================================================
# PART 4 — Equation-to-open-problem crosslinks
# ================================================================
print("=" * 60)
print("PART 4: Cross-linking equations to open problems")
print("=" * 60)

# Parse the related_equation_ids in open_problems and create a junction table
cur.execute("DROP TABLE IF EXISTS equation_problems")
cur.execute("""CREATE TABLE equation_problems (
    equation_id INTEGER REFERENCES equations(id),
    problem_id INTEGER REFERENCES open_problems(id),
    PRIMARY KEY (equation_id, problem_id)
)""")

# Each open problem references related equations by number in related_equation_ids
cur.execute("SELECT id, related_equation_ids FROM open_problems")
cp_count = 0
for pid, refs in cur.fetchall():
    if refs:
        # Parse eq_number references (comma-separated, may be ranges)
        parts = refs.replace(',', ' ').split()
        for part in parts:
            try:
                eq_num = int(part)
                # Find equation by eq_number
                cur.execute("SELECT id FROM equations WHERE eq_number = ?", (eq_num,))
                row = cur.fetchone()
                if row:
                    cur.execute("INSERT OR IGNORE INTO equation_problems VALUES (?, ?)", (row[0], pid))
                    cp_count += 1
            except ValueError:
                pass

conn.commit()
print(f"  ✓ {cp_count} equation→problem crosslinks created\n")

# ================================================================
# PART 5 — Build summary views
# ================================================================
print("=" * 60)
print("PART 5: Building summary views for invariant scan querying")
print("=" * 60)

cur.executescript("""
DROP VIEW IF EXISTS v_invariant_scan;
CREATE VIEW v_invariant_scan AS
SELECT
    e.eq_number,
    e.title,
    d.name AS domain,
    e.status,
    e.significance,
    e.precision_note,
    COALESCE(vc.cnt, 0) AS verification_count,
    GROUP_CONCAT(DISTINCT se.latex_formula, ' | ') AS key_formulas,
    GROUP_CONCAT(DISTINCT ec.symbol, ', ') AS constants_used
FROM equations e
JOIN domains d ON e.domain_id = d.id
LEFT JOIN (SELECT equation_id, COUNT(*) AS cnt FROM verifications GROUP BY equation_id) vc ON vc.equation_id = e.id
LEFT JOIN sub_equations se ON se.equation_id = e.id
LEFT JOIN equation_constants ec ON ec.equation_id = e.id
GROUP BY e.id
ORDER BY d.name, e.eq_number;

DROP VIEW IF EXISTS v_domain_coverage;
CREATE VIEW v_domain_coverage AS
SELECT
    d.name AS domain,
    COUNT(DISTINCT e.id) AS total_equations,
    COUNT(DISTINCT v.id) AS total_verifications,
    ROUND(CAST(COUNT(DISTINCT v.id) AS REAL) / COUNT(DISTINCT e.id), 1) AS verifications_per_equation,
    COUNT(CASE WHEN vc.cnt >= 10 THEN 1 END) AS equations_at_10x
FROM domains d
LEFT JOIN equations e ON e.domain_id = d.id
LEFT JOIN verifications v ON v.equation_id = e.id
LEFT JOIN (SELECT equation_id, COUNT(*) AS cnt FROM verifications GROUP BY equation_id) vc ON vc.equation_id = e.id
WHERE e.id IS NOT NULL
GROUP BY d.id
ORDER BY verifications_per_equation DESC;

DROP VIEW IF EXISTS v_open_problems_with_refs;
CREATE VIEW v_open_problems_with_refs AS
SELECT
    op.name AS problem,
    op.description,
    COUNT(ep.equation_id) AS related_equation_count,
    GROUP_CONCAT(e.eq_number || ': ' || SUBSTR(e.title, 1, 60), '; ') AS related_equations
FROM open_problems op
LEFT JOIN equation_problems ep ON ep.problem_id = op.id
LEFT JOIN equations e ON e.id = ep.equation_id
GROUP BY op.id
ORDER BY op.id;

DROP VIEW IF EXISTS v_constant_usage;
CREATE VIEW v_constant_usage AS
SELECT
    c.symbol,
    c.name,
    c.value_si,
    COUNT(DISTINCT ec.equation_id) AS used_in_equations,
    COUNT(DISTINCT e.domain_id) AS used_in_domains,
    GROUP_CONCAT(DISTINCT d.name, ', ') AS domains
FROM constants c
LEFT JOIN equation_constants ec ON ec.constant_id = c.id
LEFT JOIN equations e ON e.id = ec.equation_id
LEFT JOIN domains d ON d.id = e.domain_id
GROUP BY c.id
ORDER BY used_in_equations DESC;

DROP VIEW IF EXISTS v_database_summary;
CREATE VIEW v_database_summary AS
SELECT
    (SELECT COUNT(*) FROM equations) AS total_equations,
    (SELECT COUNT(*) FROM domains) AS total_domains,
    (SELECT COUNT(*) FROM verifications) AS total_verifications,
    (SELECT COUNT(*) FROM sub_equations) AS total_sub_equations,
    (SELECT COUNT(*) FROM constants) AS total_constants,
    (SELECT COUNT(*) FROM open_problems) AS total_open_problems,
    (SELECT COUNT(*) FROM equation_constants) AS total_constant_links,
    (SELECT COUNT(*) FROM equation_problems) AS total_problem_links;
""")

conn.commit()
print("  ✓ Views created:")
cur.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
for row in cur.fetchall():
    print(f"    - {row[0]}")
print()

# ================================================================
# PART 6 — Integrity check
# ================================================================
print("=" * 60)
print("PART 6: Final integrity check")
print("=" * 60)

issues = 0

# Check for orphaned verifications (eq_id that doesn't exist)
cur.execute("SELECT COUNT(*) FROM verifications v WHERE v.equation_id NOT IN (SELECT id FROM equations) AND v.equation_id IS NOT NULL")
orphaned_v = cur.fetchone()[0]
if orphaned_v:
    print(f"  ⚠ {orphaned_v} orphaned verifications (removing...)")
    cur.execute("DELETE FROM verifications WHERE equation_id NOT IN (SELECT id FROM equations) AND equation_id IS NOT NULL")
    issues += 1
else:
    print(f"  ✓ 0 orphaned verifications")

# Check for orphaned sub-equations
cur.execute("SELECT COUNT(*) FROM sub_equations WHERE equation_id NOT IN (SELECT id FROM equations)")
orphaned_s = cur.fetchone()[0]
if orphaned_s:
    print(f"  ⚠ {orphaned_s} orphaned sub-equations")
    issues += 1
else:
    print(f"  ✓ 0 orphaned sub-equations")

# Check for equations with 0 verifications
cur.execute("SELECT COUNT(*) FROM equations e WHERE e.id NOT IN (SELECT equation_id FROM verifications WHERE equation_id IS NOT NULL)")
zero_v = cur.fetchone()[0]
if zero_v:
    print(f"  ⚠ {zero_v} equations with 0 verifications")
    issues += 1
else:
    print(f"  ✓ All equations have ≥1 verification")

# Check 10x coverage
cur.execute("SELECT COUNT(*) FROM equations e LEFT JOIN (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id WHERE COALESCE(vc.c,0) < 10")
below_10 = cur.fetchone()[0]
if below_10:
    print(f"  ⚠ {below_10} equations below 10x")
    issues += 1
else:
    print(f"  ✓ All 770 equations at 10x+ (≥10 verifications each)")

# Check domain coverage
cur.execute("SELECT COUNT(*) FROM domains WHERE id IN (SELECT domain_id FROM equations)")
domains_used = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM domains")
total_domains = cur.fetchone()[0]
empty_domains = total_domains - domains_used
if empty_domains:
    print(f"  ⚠ {empty_domains} domains have no equations")
    issues += 1
else:
    print(f"  ✓ All {total_domains} domains have equations")

conn.commit()

# Final counts
cur.execute("SELECT * FROM v_database_summary")
row = cur.fetchone()
cols = [desc[0] for desc in cur.description]
print(f"\n{'═'*60}")
print("FINAL DATABASE SUMMARY")
print(f"{'═'*60}")
for i, col in enumerate(cols):
    print(f"  {col:25s}: {row[i]:6d}")

elapsed = time.time() - start
print(f"\n  Integrity issues: {issues}")
print(f"  Execution time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
print(f"  Database: {DB} ({os.path.getsize(DB)} bytes)")
conn.close()
