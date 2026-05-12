#!/usr/bin/env python3
"""Append material physics laws to the existing physics_equations.db"""

import sqlite3, os

DB = "/home/allaun/physics_equations.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Get current max IDs
cur.execute("SELECT MAX(id) FROM equations")
max_id = cur.fetchone()[0] or 333
cur.execute("SELECT MAX(eq_number) FROM equations")
max_num = cur.fetchone()[0] or 333
cur.execute("SELECT MAX(id) FROM sub_equations")
max_sub = cur.fetchone()[0] or 0
cur.execute("SELECT MAX(id) FROM verifications")
max_ver = cur.fetchone()[0] or 0

# Add material physics domains if missing
domains_new = [
    (21, "Material Physics", "Solid state, mechanical, thermal, electrical, magnetic, optical properties of materials", None),
    (22, "Crystallography", "Crystal structure, symmetry, diffraction, reciprocal lattice", 21),
    (23, "Semiconductor Physics", "Band gaps, doping, p-n junctions, transistors, quantum wells", 21),
    (24, "Polymer Physics", "Viscoelasticity, rubber elasticity, reptation, glass transition", 21),
    (25, "Surface Science", "Surface energy, adsorption, catalysis, tribology, thin films", 21),
    (26, "Soft Matter", "Colloids, liquid crystals, gels, self-assembly, emulsions", 21),
    (27, "Phase Transformations", "Nucleation, spinodal decomposition, diffusion, grain growth", 21),
]
for d in domains_new:
    cur.execute("INSERT OR IGNORE INTO domains VALUES (?,?,?,?)", d)

# ================================================================
# MATERIAL PHYSICS EQUATIONS
# ================================================================
mat_eqs = []
def add_eq(eq_num, title, dom, year, status, sig, prec):
    global max_id, max_num
    max_id += 1; max_num += 1
    mat_eqs.append((max_id, eq_num, title, dom, year, status, sig, prec))

# ---- CRYSTALLOGRAPHY ----
add_eq(334, "Bragg's Law (Generalized, Powder Diffraction)", 22, "1913", "Proven",
    "nλ = 2d sin θ; foundation of all crystal structure determination", "Every crystal structure solved")
add_eq(335, "Laue Equations (3D Diffraction Condition)", 22, "1912", "Proven",
    "a·Δk=2πh, b·Δk=2πk, c·Δk=2πl; constructive interference in 3D lattice", "Equivalent to Bragg's law; confirmed")
add_eq(336, "Structure Factor Equation", 22, "1915", "Proven",
    "F_{hkl} = Σ_j f_j exp[2πi(hx_j+ky_j+lz_j)]; determines diffraction intensities", "All crystallography")
add_eq(337, "Atomic Scattering Factor (X-ray Form Factor)", 22, "1920s", "Proven",
    "f(q) = ∫ ρ(r) exp(iq·r) d³r; Fourier transform of electron density", "Confirmed for all elements")
add_eq(338, "Reciprocal Lattice Vector Definition", 22, "1921", "Proven",
    "G = h a* + k b* + l c*; a*=(b×c)/V_cell, etc.", "Exact mathematical definition")
add_eq(339, "Brillouin Zone Boundaries", 22, "1930", "Proven",
    "2 k·G = |G|²; electron wave diffraction condition at BZ boundaries", "Band gap formation; confirmed")
add_eq(340, "Ewald Sphere Construction", 22, "1921", "Proven",
    "|k| = |k'| = 2π/λ; Δk = G falls on sphere → diffraction", "Geometric diffraction condition; exact")
add_eq(341, "Patterson Function (Interatomic Vectors)", 22, "1935", "Proven",
    "P(u,v,w) = ∫ |F_{hkl}|² exp[−2πi(hu+kv+lw)] d*h d*k d*l", "No phase problem; heavy-atom method")
add_eq(342, "Debye-Waller Factor (Thermal Motion)", 22, "1913", "Proven",
    "f_T(q) = f₀(q) exp(−½⟨(u·q)²⟩); B = 8π²⟨u²⟩", "Temperature-dependent X-ray intensities; confirmed")
add_eq(343, "Space Group Symmetry Operations", 22, "1891", "Proven",
    "230 space groups in 3D; {R|t} r = R r + t", "All crystalline materials classified")
add_eq(344, "Interplanar Spacing (Cubic Systems)", 22, "1913", "Proven",
    "1/d² = (h²+k²+l²)/a² (cubic); general: depends on lattice parameters", "Indexing diffraction patterns")
add_eq(345, "Scherrer Equation (Crystallite Size)", 22, "1918", "Proven",
    "D = K λ / (β cos θ); K≈0.9; β=FWHM in radians", "Nanocrystallite size from peak broadening")
add_eq(346, "Williamson-Hall Analysis (Size + Strain)", 22, "1953", "Proven",
    "β cos θ = Kλ/D + 4ε sin θ; separates size and microstrain broadening", "XRD line profile analysis")

# ---- MECHANICAL PROPERTIES ----
add_eq(347, "True Stress — True Strain Definition", 21, "19th c.", "Proven",
    "σ_true = F/A_inst; ε_true = ln(L/L₀) = ln(1+ε_eng)", "Beyond necking; large deformations")
add_eq(348, "Hollomon Equation (Work Hardening)", 21, "1945", "Proven",
    "σ = K ε^n; n = strain hardening exponent; K = strength coefficient", "Plastic flow curve; confirmed for metals")
add_eq(349, "Hall-Petch Relationship (Grain Size Strengthening)", 21, "1951–53", "Proven",
    "σ_y = σ₀ + k_y / √d; d = grain diameter", "Yield strength vs grain size; metals and ceramics")
add_eq(350, "Orowan Equation (Precipitation Strengthening)", 21, "1948", "Proven",
    "Δτ = G b / L; L = interparticle spacing; b = Burgers vector", "Dispersion/precipitation hardening")
add_eq(351, "Schmid's Law (Critical Resolved Shear Stress)", 21, "1924", "Proven",
    "τ_CRSS = σ_y cos φ cos λ; m = cos φ cos λ (Schmid factor)", "Yield onset in single crystals; confirmed")
add_eq(352, "Taylor Equation (Dislocation Strengthening)", 21, "1934", "Proven",
    "τ = α G b √ρ; ρ = dislocation density; α≈0.2–0.5", "Work hardening from dislocation interactions")
add_eq(353, "Petch-Forwood Hardness-Yield Strength Relation", 21, "1970s", "Proven",
    "H ≈ 3 σ_y (metals); Vickers/Brinell ≈ 3 × yield", "Rough correlation; material-dependent")
add_eq(354, "Griffith Criterion (Brittle Fracture)", 21, "1921", "Proven",
    "σ_f = √(2Eγ_s / πa); critical stress for crack propagation", "Brittle fracture; ceramics, glass")
add_eq(355, "Stress Intensity Factor (LEFM, Mode I)", 21, "1957", "Proven",
    "K_I = Y σ √(πa); fracture when K_I ≥ K_Ic", "Linear elastic fracture mechanics; exact in limit")
add_eq(356, "J-Integral (Elastic-Plastic Fracture)", 21, "1968", "Proven",
    "J = ∫_Γ (W dy − T_i ∂u_i/∂x ds); path-independent energy release rate", "EPFM; ductile fracture criterion")
add_eq(357, "Paris' Law (Fatigue Crack Growth)", 21, "1963", "Proven",
    "da/dN = C (ΔK)^m; C, m material constants; m≈2–4 for metals", "Fatigue life prediction; confirmed")
add_eq(358, "Basquin Equation (High-Cycle Fatigue)", 21, "1910", "Proven",
    "σ_a = σ_f' (2N_f)^b; b≈−0.05 to −0.12 for metals", "S-N curve; stress-life fatigue")
add_eq(359, "Coffin-Manson Relation (Low-Cycle Fatigue)", 21, "1950s", "Proven",
    "Δε_p/2 = ε_f' (2N_f)^c; c≈−0.5 to −0.7", "Plastic strain-life fatigue")
add_eq(360, "Norton-Bailey Creep Law", 21, "1929/1935", "Proven",
    "ε_cr = A σ^n t^m (primary creep); dε_cr/dt = B σ^n (secondary)", "High-temperature creep; confirmed")
add_eq(361, "Larson-Miller Parameter (Creep Rupture)", 21, "1952", "Proven",
    "P = T (C + log t_r); C≈20; T in K, t_r in hours", "Creep life extrapolation; engineering standard")
add_eq(362, "Mohr-Coulomb Failure Criterion", 21, "1776/1900", "Proven",
    "τ = c + σ_n tan φ; c=cohesion, φ=internal friction angle", "Rocks, soils, concrete, granular materials")
add_eq(363, "Drucker-Prager Yield Criterion", 21, "1952", "Proven",
    "√J₂ + α I₁ = k; pressure-dependent yielding", "Geomaterials, polymers, foams")
add_eq(364, "Weibull Distribution (Brittle Failure Statistics)", 21, "1939", "Proven",
    "P_f = 1 − exp[−(σ/σ₀)^m]; m = Weibull modulus", "Ceramic strength variability; size effect")
add_eq(365, "Stoney Equation (Thin Film Stress)", 21, "1909", "Proven",
    "σ_f = E_s h_s² κ / [6(1−ν_s) h_f]; substrate curvature → film stress", "Thin film metrology; MEMS")

# ---- THERMAL PROPERTIES ----
add_eq(366, "Debye Specific Heat Model (Full)", 21, "1912", "Proven",
    "C_V = 9 N k_B (T/Θ_D)³ ∫₀^{Θ_D/T} x⁴ e^x / (e^x−1)² dx", "Phonon heat capacity; all solids; exact")
add_eq(367, "Dulong-Petit Law", 21, "1819", "Proven",
    "C_V = 3R ≈ 24.94 J/(mol·K) at high T (classical limit of Debye)", "Most solids above Debye temperature")
add_eq(368, "Einstein Heat Capacity Model", 21, "1907", "Proven",
    "C_V = 3 N k_B (Θ_E/T)² e^{Θ_E/T} / (e^{Θ_E/T}−1)²", "First quantum model; qualitatively correct")
add_eq(369, "Wiedemann-Franz Law (Electronic Thermal Conductivity)", 21, "1853", "Proven",
    "κ_e / (σ T) = L; L = (π²/3)(k_B/e)² ≈ 2.44×10⁻⁸ W Ω/K²", "Metals; Sommerfeld value; confirmed")
add_eq(370, "Debye-Callaway Model (Lattice Thermal Conductivity)", 21, "1959", "Proven",
    "κ_l = (k_B/2π²v)(k_B T/ℏ)³ ∫₀^{Θ_D/T} τ_c x⁴ e^x / (e^x−1)² dx", "Phonon thermal conductivity; confirmed")
add_eq(371, "Thermal Expansion Coefficient (Grüneisen Relation)", 21, "1912", "Proven",
    "α = γ C_V / (3 B V); γ = Grüneisen parameter; B = bulk modulus", "All solids; confirmed")
add_eq(372, "Grüneisen Equation of State (Solids)", 21, "1912", "Proven",
    "P(V) = −dU₀/dV + γ U_th/V; γ = Grüneisen parameter", "Thermal pressure; shock physics")
add_eq(373, "Lindemann Melting Criterion", 21, "1910", "Proven",
    "T_m ≈ C θ_D² M V^{2/3}; C depends on crystal structure", "Empirical; qualitatively correct")
add_eq(374, "Stefan-Boltzmann Radiative Heat Transfer (Between Surfaces)", 21, "1880s", "Proven",
    "q = ε_eff σ (T₁⁴−T₂⁴); view factor + emissivity correction", "Radiation in materials processing")

# ---- ELECTRICAL PROPERTIES ----
add_eq(375, "Complex Dielectric Constant", 21, "1920s", "Proven",
    "ε* = ε' − i ε''; tan δ = ε''/ε'; loss tangent", "All dielectrics; AC response")
add_eq(376, "Clausius-Mossotti Relation (Polarizability)", 21, "1879", "Proven",
    "(ε_r−1)/(ε_r+2) = N α / (3 ε₀); links macro/micro dielectric properties", "Non-polar dielectrics; confirmed")
add_eq(377, "Debye Relaxation (Dipole Response)", 21, "1929", "Proven",
    "ε*(ω) = ε_∞ + (ε_s−ε_∞) / (1 + i ω τ)", "Polar liquids, polymers; confirmed")
add_eq(378, "Cole-Cole Relaxation (Distributed)", 21, "1941", "Proven",
    "ε*(ω) = ε_∞ + (ε_s−ε_∞) / [1 + (i ω τ)^{1−α}]", "Broadened relaxation; polymers, glasses")
add_eq(379, "Havriliak-Negami Relaxation", 21, "1966", "Proven",
    "ε*(ω) = ε_∞ + (ε_s−ε_∞) / [1 + (i ω τ)^α]^β", "General empirical relaxation function")
add_eq(380, "Curie-Weiss Law for Ferroelectrics (Above T_c)", 21, "1940s", "Proven",
    "ε_r = C / (T − T_c); C = Curie constant", "BaTiO₃, PZT; phase transition temperature")
add_eq(381, "Piezoelectric Constitutive Equations", 21, "1880s", "Proven",
    "S = s^E T + d^t E; D = d T + ε^T E (strain-charge form)", "All piezoelectrics; confirmed")
add_eq(382, "Pyroelectric Coefficient", 21, "19th c.", "Proven",
    "p = dP_s/dT; ΔQ = p A ΔT", "Ferroelectrics; IR detectors")
add_eq(383, "Fowler-Nordheim Tunneling (Field Emission)", 21, "1928", "Proven",
    "J = (A/φ)(βE)² exp(−B φ^{3/2} / βE); A,B constants", "Field emission; confirmed")
add_eq(384, "Poole-Frenkel Conduction (Insulators)", 21, "1938", "Proven",
    "σ = σ₀ exp[−q(φ_B−√(qE/πε))/k_B T]", "Field-enhanced thermal emission; insulators")
add_eq(385, "Varistor I-V Characteristic (Nonlinear)", 21, "1970s", "Proven",
    "I = k V^α; α >> 1 (ZnO varistors α≈20–100)", "Surge protection; grain boundary effect")
add_eq(386, "Percolation Threshold (Conductivity)", 21, "1970s", "Proven",
    "σ = σ₀ (p − p_c)^t; p = volume fraction; p_c = percolation threshold", "Composites, granular materials")

# ---- SEMICONDUCTOR PHYSICS ----
add_eq(387, "Intrinsic Carrier Concentration (Semiconductors)", 23, "1931", "Proven",
    "n_i = √(N_c N_v) exp(−E_g / 2 k_B T); N_c = 2(2π m_e* k_B T/h²)^{3/2}", "Silicon: n_i≈1.0×10¹⁰ cm⁻³ at 300K")
add_eq(388, "Fermi Level in Doped Semiconductors", 23, "1930s", "Proven",
    "n-type: E_F = E_c − k_B T ln(N_c/N_d); p-type: E_F = E_v + k_B T ln(N_v/N_a)", "Doping control; all semiconductor devices")
add_eq(389, "Mass Action Law (Semiconductors)", 23, "1930s", "Proven",
    "n p = n_i²; product constant at fixed T", "Thermal equilibrium; exact")
add_eq(390, "Shockley Diode Equation (Ideal)", 23, "1949", "Proven",
    "I = I_s [exp(q V / n k_B T) − 1]; I_s = reverse saturation current", "All p-n junctions; n = ideality factor")
add_eq(391, "Built-in Potential (p-n Junction)", 23, "1949", "Proven",
    "V_bi = (k_B T / q) ln(N_a N_d / n_i²)", "From Fermi level alignment; confirmed")
add_eq(392, "Depletion Width (p-n Junction)", 23, "1949", "Proven",
    "W = √[2ε_s (V_bi−V)(1/N_a+1/N_d)/q]", "Junction capacitance; confirmed")
add_eq(393, "MOS Capacitor Threshold Voltage", 23, "1960s", "Proven",
    "V_th = V_FB + 2φ_F + √(4ε_s q N_a φ_F)/C_ox", "MOSFET operation foundation")
add_eq(394, "MOSFET Drain Current (Saturation, Long Channel)", 23, "1960s", "Proven",
    "I_D = (μ_n C_ox W / 2L) (V_GS − V_th)²", "All digital logic; confirmed to percent level")
add_eq(395, "Subthreshold Swing (MOSFET)", 23, "1960s", "Proven",
    "SS = (k_B T/q) ln(10) (1 + C_dep/C_ox); ideal: 60 mV/decade at 300K", "Low-power limit; confirmed")
add_eq(396, "Avalanche Breakdown (Impact Ionization)", 23, "1950s", "Proven",
    "M = 1 / [1 − (V/V_BR)^n]; n≈3–6", "High-field breakdown; confirmed in all devices")
add_eq(397, "Quantum Confinement Energy (Particle in a Box)", 23, "1970s", "Proven",
    "E_n = n² π² ℏ² / (2 m* L²); blue shift with decreasing size", "Quantum wells, wires, dots; confirmed")
add_eq(398, "Brus Equation (Semiconductor Nanocrystal Band Gap)", 23, "1986", "Proven",
    "E_g(R) = E_g(bulk) + ℏ²π²/(2μ R²) − 1.8e²/(ε_r R); μ = reduced exciton mass", "Quantum dot emission tuning; confirmed")
add_eq(399, "Kane's k·p Band Model (Non-Parabolicity)", 23, "1957", "Proven",
    "E(1+αE) = ℏ² k² / (2 m*); α = 1/E_g; non-parabolic correction", "Narrow-gap semiconductors")
add_eq(400, "Mott Transition (Doped Semiconductor)", 23, "1949", "Proven",
    "n_c^{1/3} a_B* ≈ 0.25; insulator-metal transition at critical doping", "Confirmed in Si:P, Si:B")
add_eq(401, "Anderson Localization (Disordered Materials)", 23, "1958", "Proven",
    "W/V > W_c → localized states; mobility edge at E_c", "Amorphous semiconductors; confirmed")
add_eq(402, "Tauc Plot (Band Gap from Absorption)", 23, "1968", "Proven",
    "(α h ν)^{1/r} = A (hν − E_g); r=½ for direct, r=2 for indirect", "Optical band gap determination")

# ---- MAGNETIC PROPERTIES (detailed) ----
add_eq(403, "Stoner Criterion (Itinerant Ferromagnetism)", 21, "1936", "Proven",
    "N(E_F) I > 1; spontaneous magnetization when DOS × exchange exceeds unity", "Fe, Co, Ni; confirmed")
add_eq(404, "Stoner-Wohlfarth Model (Single-Domain Particle)", 21, "1948", "Proven",
    "E = K V sin²θ − μ₀ M_s H V cos(φ−θ); hysteresis from anisotropy+Zeeman", "Magnetic recording; permanent magnets")
add_eq(405, "Néel Temperature (Antiferromagnetism)", 21, "1936", "Proven",
    "T_N = (2J S(S+1)/3k_B) z (from mean-field); sublattice ordering temperature", "MnO, NiO; confirmed")
add_eq(406, "Curie Temperature (Mean-Field Ferromagnetism)", 21, "1907", "Proven",
    "T_c = (2J S(S+1)/3k_B) z; z = coordination number", "All ferromagnets; order-of-magnitude correct")
add_eq(407, "Bloch T^{3/2} Law (Magnetization at Low T)", 21, "1930", "Proven",
    "M_s(T) = M_s(0) [1 − (T/T_c)^{3/2}] (3D Heisenberg)", "Spin-wave theory; confirmed for insulators")
add_eq(408, "Landau-Lifshitz-Gilbert Equation (Magnetization Dynamics)", 21, "1935/2004", "Proven",
    "dM/dt = −γ M × H_eff + (α/M_s) M × dM/dt", "All magnetization dynamics; spintronics foundation")
add_eq(409, "Brown's Paradox (Domain Wall Motion)", 21, "1963", "Proven",
    "v = (γ Δ / α)(H − H_c); soft magnetic materials", "Domain wall dynamics; confirmed")
add_eq(410, "Magnetostriction (Joule Magnetostriction)", 21, "1842", "Proven",
    "ΔL/L = (3/2) λ_s (cos²θ − 1/3); λ_s = saturation magnetostriction", "Terfenol-D, Galfenol; confirmed")
add_eq(411, "Giant Magnetoresistance (GMR, CIP)", 21, "1988", "Proven",
    "ΔR/R = (R_AP−R_P)/R_P; spin-dependent scattering at interfaces", "Nobel 2007; hard disk read heads")
add_eq(412, "Tunneling Magnetoresistance (TMR, Julliere Model)", 21, "1975", "Proven",
    "TMR = (R_AP−R_P)/R_P = 2P₁P₂/(1−P₁P₂); P = spin polarization", "MRAM, read heads; confirmed")
add_eq(413, "RKKY Interaction (Indirect Exchange)", 21, "1954–57", "Proven",
    "J(R) ∝ cos(2k_F R) / R³; oscillatory coupling through conduction electrons", "Multilayer magnetic coupling; confirmed")
add_eq(414, "Superexchange (Anderson-Goodenough-Kanamori Rules)", 21, "1950s", "Proven",
    "J_ij ∝ −b²/U (for 180° cation-anion-cation); sign depends on orbital filling", "Magnetic insulators; MnO, ferrites")

# ---- OPTICAL PROPERTIES (Materials) ----
add_eq(415, "Complex Refractive Index (General)", 21, "19th c.", "Proven",
    "ñ = n + i κ; I(z) = I₀ exp(−α z); α = 4πκ/λ", "All optical materials")
add_eq(416, "Kramers-Kronig Relations (Optical Constants)", 21, "1926–27", "Proven",
    "n(ω)−1 = (2/π) P ∫₀^∞ ω' κ(ω')/(ω'²−ω²) dω'; causality → dispersion relations", "All linear optical materials; exact")
add_eq(417, "Tauc-Lorentz Model (Amorphous Semiconductor Optics)", 21, "1996", "Proven",
    "ε_2(E) = [A E₀ C (E−E_g)²] / [(E²−E₀²)² + C² E²] E for E>E_g; 0 otherwise", "a-Si, a-C; ellipsometry standard")
add_eq(418, "Sellmeier Equation (Refractive Index Dispersion)", 21, "1871", "Proven",
    "n²(λ) = 1 + Σ_i A_i λ² / (λ² − λ_i²); empirical fit for transparent regions", "Glasses, crystals; standard")
add_eq(419, "Cauchy Equation (Refractive Index Fit)", 21, "1836", "Proven",
    "n(λ) = A + B/λ² + C/λ⁴; empirical for transparent region", "Simple fit; visible range")
add_eq(420, "Urbach Tail (Absorption Edge)", 21, "1953", "Proven",
    "α(E) = α₀ exp[σ (E−E₀) / k_B T]; exponential absorption below band edge", "Disordered semiconductors; thermal/lattice disorder")
add_eq(421, "Beer-Lambert Law (Absorption)", 3, "1729–1852", "Proven",
    "A = log₁₀(I₀/I) = ε c L; absorbance proportional to concentration and path", "All spectrophotometry; exact for dilute")
add_eq(422, "Kubelka-Munk Theory (Diffuse Reflectance)", 21, "1931", "Proven",
    "F(R_∞) = (1−R_∞)²/(2R_∞) = K/S ∝ α; for thick opaque scattering media", "Powders, pigments, paper; confirmed")
add_eq(423, "Fresnel Loss at Normal Incidence", 21, "1823", "Proven",
    "R = [(n₁−n₂)/(n₁+n₂)]²; reflection coefficient at normal incidence", "All dielectric interfaces; exact")
add_eq(424, "Drude Model for Free-Carrier Absorption", 21, "1900", "Proven",
    "ε(ω) = ε_∞ − ω_p²/(ω² + i ω/τ); ω_p = √(n e²/ε₀ m*)", "Metals, doped semiconductors in IR; confirmed")
add_eq(425, "Forster Resonance Energy Transfer (FRET) Efficiency", 21, "1948", "Proven",
    "E = 1 / [1 + (r/R₀)⁶]; R₀ = Förster radius (~1–10 nm)", "Molecular photophysics; single-molecule detection")
add_eq(426, "Stokes Shift (Luminescence)", 21, "1852", "Proven",
    "ΔE = E_abs − E_em > 0; from vibrational relaxation", "All fluorescence/phosphorescence")
add_eq(427, "Dexter Energy Transfer (Exchange)", 21, "1953", "Proven",
    "k_ET ∝ exp(−2r/L); short-range (≲1 nm) electron exchange", "Triplet energy transfer; OLEDs")

# ---- MECHANICAL TESTING ----
add_eq(428, "Vickers Hardness Definition", 21, "1924", "Proven",
    "HV = 1.854 F / d²; F in kgf, d = average diagonal (mm)", "Standard micro/macro hardness test")
add_eq(429, "Brinell Hardness", 21, "1900", "Proven",
    "HB = 2F / [π D (D − √(D²−d²))]; D = ball diameter", "Bulk hardness; metals")
add_eq(430, "Rockwell Hardness (Indirect)", 21, "1919", "Proven",
    "HR = N − h/s; h = penetration depth; N,s depend on scale", "Industrial QC; rapid measurement")
add_eq(431, "Knoop Hardness (Thin Films / Brittle)", 21, "1939", "Proven",
    "HK = 14.229 F / d₁²; long diagonal; shallow penetration", "Ceramics, coatings, thin films")
add_eq(432, "Nanoindentation (Oliver-Pharr Method)", 21, "1992", "Proven",
    "H = P_max/A; E_r = √π S/(2β√A); S = dP/dh at unload", "Submicron property mapping; confirmed")
add_eq(433, "Charpy Impact Toughness", 21, "1900s", "Proven",
    "KV = m g (h_initial − h_final); energy absorbed in fracture (J)", "Notch toughness; metals, polymers")
add_eq(434, "Izod Impact Test", 21, "1903", "Proven",
    "Similar to Charpy; energy absorbed per unit width (J/m)", "Plastics, composites")

# ---- POLYMER PHYSICS ----
add_eq(435, "Rubber Elasticity (Gaussian Chain, Affine)", 24, "1930s", "Proven",
    "σ_true = n k_B T (λ − 1/λ²); n = crosslink density; λ = extension ratio", "Elastomers at moderate strain; confirmed")
add_eq(436, "Mooney-Rivlin Equation (Hyperelastic)", 24, "1940s", "Proven",
    "W = C₁₀(I₁−3) + C₀₁(I₂−3); I₁,I₂ = invariants of Cauchy-Green tensor", "Rubber at large strains; phenomenological")
add_eq(437, "Flory-Huggins Theory (Polymer Solution Free Energy)", 24, "1942", "Proven",
    "ΔG_mix/k_B T = n₁ ln φ₁ + n₂ ln φ₂ + χ n₁ φ₂; χ = Flory interaction parameter", "Polymer-solvent thermodynamics")
add_eq(438, "Williams-Landel-Ferry (WLF) Equation", 24, "1955", "Proven",
    "log a_T = −C₁ (T−T_ref) / (C₂ + T−T_ref); time-temperature superposition", "Viscoelasticity time-temperature shift")
add_eq(439, "Arrhenius Viscosity (Above Glass Transition)", 24, "1930s", "Proven",
    "η(T) = η₀ exp(E_a / R T) (simple) or Vogel-Fulcher-Tammann: η = η₀ exp[B/(T−T₀)]", "Polymer melt viscosity")
add_eq(440, "Rouse Model (Unentangled Polymer Dynamics)", 24, "1953", "Proven",
    "τ_R = ζ N² b² / (3π² k_B T); longest relaxation time of unentangled chain", "Short chains; N < N_e")
add_eq(441, "Reptation Model (de Gennes, Entangled Dynamics)", 24, "1971", "Proven",
    "τ_rep ∝ N³; D_rep ∝ N⁻²; disentanglement time; Nobel 1991", "Long entangled chains; N >> N_e")
add_eq(442, "Entanglement Molecular Weight", 24, "1970s", "Proven",
    "M_e = ρ R T / G_N⁰; from plateau modulus G_N⁰", "Characteristic for each polymer")
add_eq(443, "Flory-Fox Equation (T_g vs Molecular Weight)", 24, "1950", "Proven",
    "T_g = T_g∞ − K_F / M_n; T_g increases with MW to asymptotic limit", "All linear polymers; confirmed")
add_eq(444, "Cahn-Hilliard Equation (Spinodal Decomposition)", 24, "1958", "Proven",
    "∂c/∂t = M ∇²[∂f/∂c − 2κ ∇²c]; diffusion modulated by gradient energy", "Phase separation; alloys, polymers")
add_eq(445, "Avrami Equation (Crystallization Kinetics)", 27, "1939", "Proven",
    "X(t) = 1 − exp(−k t^n); n = Avrami exponent (dimensionality + nucleation mode)", "Polymer, metal, glass crystallization")
add_eq(446, "Lauritzen-Hoffman Theory (Polymer Crystal Growth)", 27, "1970s", "Proven",
    "G = G₀ exp[−U*/R(T−T_∞)] exp[−K_g / (T ΔT f)]; secondary nucleation", "Polymer crystallization rate")

# ---- SURFACES AND INTERFACES ----
add_eq(447, "Young's Equation (Contact Angle)", 25, "1805", "Proven",
    "γ_sv = γ_sl + γ_lv cos θ; balance of interfacial tensions", "Wettability; exact for smooth homogeneous")
add_eq(448, "Wenzel Equation (Rough Surface Wetting)", 25, "1936", "Proven",
    "cos θ* = r cos θ; r = actual/projected area > 1; roughness amplifies wetting", "Real surfaces; confirmed")
add_eq(449, "Cassie-Baxter Equation (Composite/Heterogeneous Wetting)", 25, "1944", "Proven",
    "cos θ* = f₁ cos θ₁ + f₂ cos θ₂; f₁+f₂=1; trapped air → superhydrophobic", "Lotus effect; superhydrophobic surfaces")
add_eq(450, "Laplace Pressure (Curved Interface)", 9, "1805", "Proven",
    "ΔP = γ (1/R₁ + 1/R₂); pressure inside curved surface", "Bubbles, droplets, capillary action")
add_eq(451, "Kelvin Equation (Capillary Condensation)", 25, "1871", "Proven",
    "ln(P/P₀) = −2γ V_m / (r R T); condensation in pores below saturation", "Mesoporous materials; confirmed")
add_eq(452, "Langmuir Adsorption Isotherm (Monolayer)", 25, "1918", "Proven",
    "θ = K P / (1 + K P); θ = fractional coverage; K = adsorption equilibrium constant", "Chemisorption, physisorption at low coverage")
add_eq(453, "BET Isotherm (Brunauer-Emmett-Teller, Multilayer)", 25, "1938", "Proven",
    "P/[V(P₀−P)] = 1/(V_m C) + (C−1)P/(V_m C P₀); surface area from multilayer adsorption", "Standard surface area measurement")
add_eq(454, "Freundlich Isotherm (Heterogeneous Surfaces)", 25, "1909", "Proven",
    "q = K_F P^{1/n}; empirical; heterogeneous adsorption", "Activated carbon, heterogeneous catalysts")
add_eq(455, "Gibbs Adsorption Equation", 25, "1878", "Proven",
    "dγ = −Σ Γ_i dμ_i; Γ_i = surface excess concentration", "Surfactant surface coverage; exact")
add_eq(456, "Amontons-Coulomb Friction Law (Dry Friction)", 18, "1699/1785", "Proven",
    "F_f ≤ μ_s N (static); F_f = μ_k N (kinetic); μ_k < μ_s", "Macroscopic friction; empirical")
add_eq(457, "Archard's Law (Adhesive Wear)", 25, "1953", "Proven",
    "V = k F s / H; k = wear coefficient; H = hardness", "Sliding wear volume prediction")
add_eq(458, "Hamaker Constant (Van der Waals Between Surfaces)", 25, "1937", "Proven",
    "A = π² C ρ₁ ρ₂; F_vdW/A = −A / (6π d³) (flat surfaces)", "Colloidal stability; DLVO theory")
add_eq(459, "DLVO Theory (Colloid Stability)", 25, "1940s", "Proven",
    "V_total(d) = V_vdW + V_edl; van der Waals + electric double-layer", "Colloids, nanoparticles; confirmed")
add_eq(460, "Zeta Potential (Smoluchowski Equation)", 25, "1903", "Proven",
    "ζ = η μ_e / ε; μ_e = electrophoretic mobility; η = viscosity", "Colloid surface charge; confirmed")
add_eq(461, "Derjaguin Approximation (Force Between Curved Surfaces)", 25, "1934", "Proven",
    "F_sphere(d) = 2πR W_flat(d); relates sphere-sphere to flat-plate energy", "AFM force spectroscopy; exact in limit")
add_eq(462, "Johnson-Kendall-Roberts (JKR) Adhesion Model", 25, "1971", "Proven",
    "a³ = (R/K)[F + 3πW_ad R + √(6πW_adRF + (3πW_adR)²)]; elastic + adhesion contact", "Soft materials; AFM adhesion")
add_eq(463, "Derjaguin-Muller-Toporov (DMT) Model", 25, "1975", "Proven",
    "a³ = (R/K)[F + 2πW_ad R]; adhesion without distortion of contact profile", "Hard materials; low adhesion")

# ---- DIFFUSION ----
add_eq(464, "Fick's First Law (Steady-State Diffusion)", 21, "1855", "Proven",
    "J = −D ∂c/∂x; flux proportional to concentration gradient", "All diffusion; exact for steady state")
add_eq(465, "Fick's Second Law (Time-Dependent Diffusion)", 21, "1855", "Proven",
    "∂c/∂t = D ∂²c/∂x²; for constant D; general: ∂c/∂t = ∂/∂x(D ∂c/∂x)", "All non-steady diffusion")
add_eq(466, "Diffusion Solutions (Common)", 21, "1855", "Proven",
    "Thin film: c(x,t) = (M/√(4πDt)) exp(−x²/4Dt); Error function: c = C₀ erfc(x/√(4Dt))", "All diffusion profiles; exact")
add_eq(467, "Arrhenius Diffusion Coefficient", 21, "1889", "Proven",
    "D = D₀ exp(−E_a / k_B T); thermally activated diffusion", "Atomic diffusion; vacancies, interstitials")
add_eq(468, "Darken Equations (Interdiffusion / Kirkendall Effect)", 21, "1948", "Proven",
    "D̃ = (X_B D_A + X_A D_B) Φ; Φ = thermodynamic factor including non-ideality", "Alloy interdiffusion; marker movement confirmed")
add_eq(469, "Nernst-Planck Equation (Ion Transport)", 21, "1888–1890", "Proven",
    "J_i = −D_i ∇c_i − (z_i F/RT)D_i c_i ∇φ + c_i v; diffusion + migration + convection", "Electrochemical transport; confirmed")
add_eq(470, "Stokes-Einstein Relation (Diffusion of Spheres)", 21, "1905", "Proven",
    "D = k_B T / (6π η r); hydrodynamic radius from diffusion", "Colloids, proteins; confirmed")
add_eq(471, "Tracer Diffusion Correlation Factor", 21, "1950s", "Proven",
    "D* = f D_rand; f = correlation factor; f<1 for vacancy mechanism", "Atomic-scale diffusion; confirmed")

# ---- PHASE TRANSFORMATIONS ----
add_eq(472, "Gibbs-Thomson Effect (Curvature Depression of Melting/Equilibrium Point)", 27, "1870s", "Proven",
    "T_m(r) = T_m(∞)(1 − 2γ_sl / (ρ_s ΔH_f r)); small particles melt at lower T", "Nanoparticle melting; confirmed")
add_eq(473, "Classical Nucleation Theory (Homogeneous)", 27, "1926–50", "Proven",
    "ΔG = (4π/3)r³ ΔG_v + 4πr² γ; r* = −2γ/ΔG_v; ΔG* = 16πγ³/(3ΔG_v²)", "All nucleation processes; confirmed")
add_eq(474, "Johnson-Mehl-Avrami-Kolmogorov (JMAK) Equation", 27, "1939–41", "Proven",
    "f = 1 − exp[−(kt)^n]; n depends on nucleation+growth dimensionality", "Phase transformation kinetics; standard")
add_eq(475, "Turnbull's Nucleation Rate (Steady-State)", 27, "1949", "Proven",
    "I = N_v (k_B T/h) exp[−(ΔG*+ΔG_a)/k_B T]; includes kinetic barrier", "Crystallization rate; qualitative")
add_eq(476, "Lever Rule (Phase Diagram Tie Line)", 27, "19th c.", "Proven",
    "f_α = (C₀−C_β)/(C_α−C_β); f_β = (C_α−C₀)/(C_α−C_β)", "Phase fractions from composition; exact")
add_eq(477, "Gibbs-Thomson-Freundlich (Ostwald Ripening / LSW Theory)", 27, "1961", "Proven",
    "⟨r⟩³ − ⟨r₀⟩³ = k t; k ∝ γ D c_∞ V_m²/(R T); coarsening of precipitates", "Precipitate growth; nanoparticles")
add_eq(478, "Darken-Gurry Plot (Solubility Limits)", 21, "1950s", "Proven",
    "Extensive solubility when |ΔR_atom|<15% and |Δχ|<0.4 (electronegativity difference)", "Empirical Hume-Rothery rule extension")
add_eq(479, "Hume-Rothery Rules (Alloy Formation)", 21, "1920s–30s", "Proven",
    "(1) Size <15% (2) Similar electronegativity (3) Same valence (4) Same crystal structure", "Substitutional solid solution criteria")
add_eq(480, "Vegard's Law (Lattice Parameter in Solid Solutions)", 21, "1921", "Proven",
    "a_AB = x_A a_A + x_B a_B; linear interpolation; deviations = non-ideal mixing", "Alloys; approximate for many systems")

# ---- COMPOSITES AND POROUS MATERIALS ----
add_eq(481, "Rule of Mixtures (Composite Modulus, Isostrain)", 21, "1950s", "Proven",
    "E_c = E_f V_f + E_m V_m (Voigt bound, upper); 1/E_c = V_f/E_f + V_m/E_m (Reuss bound, lower)", "Composite stiffness bounds; exact limits")
add_eq(482, "Hashin-Shtrikman Bounds (Composite Moduli)", 21, "1963", "Proven",
    "Tighter bounds than Voigt-Reuss; K_lower = K_m + V_f/[1/(K_f−K_m)+3V_m/(3K_m+4G_m)]; etc.", "Optimal bounds for isotropic composites")
add_eq(483, "Halpin-Tsai Equations (Short Fiber Composites)", 21, "1969", "Proven",
    "E/E_m = (1 + ξ η V_f)/(1 − η V_f); η = (E_f/E_m−1)/(E_f/E_m+ξ); ξ = shape factor", "Short/random fiber reinforcement")
add_eq(484, "Porosity-Young's Modulus Relation (Empirical)", 21, "1950s", "Proven",
    "E = E₀ (1 − P)^n or exp(−bP); P = porosity fraction; n≈2–4", "Porous ceramics, bone, foams")
add_eq(485, "Gibson-Ashby Model (Cellular Solids / Foams)", 21, "1988", "Proven",
    "E*/E_s = C (ρ*/ρ_s)^n; n=2 open cell; n=3 closed cell; σ*/σ_ys ∝ (ρ*/ρ_s)^{3/2}", "Foams, honeycombs, bone, wood")
add_eq(486, "Eshelby Inclusion Problem (Stress in Ellipsoidal Inclusion)", 21, "1957", "Proven",
    "ε^T = S ε*; S = Eshelby tensor (depends on inclusion shape + matrix Poisson ratio)", "Micromechanics foundation; exact for ellipsoids")

# ---- OPTICAL AND ELECTRONIC MATERIALS ----
add_eq(487, "Moss-Burstein Shift (Doped Semiconductor Absorption Edge)", 21, "1954", "Proven",
    "ΔE_g = (ℏ²/2m*)(3π²n)^{2/3}; Fermi filling blocks lowest transitions", "Transparent conducting oxides; confirmed")
add_eq(488, "Franz-Keldysh Effect (Electro-Absorption)", 21, "1958", "Proven",
    "α(E,F) ∝ exp[−(E_g−E)^{3/2} / eℏF]; band edge shift in electric field", "Semiconductor optical modulators")
add_eq(489, "Pockels Effect (Linear Electro-Optic)", 21, "1906", "Proven",
    "Δ(1/n²)_i = r_ij E_j; r_ij = linear electro-optic coefficients", "LiNbO₃, KDP; modulators, Q-switches")
add_eq(490, "Kerr Effect (Quadratic Electro-Optic)", 21, "1875", "Proven",
    "Δn = K λ E²; quadratic field dependence", "Liquids, centrosymmetric crystals; high-speed shutters")
add_eq(491, "Photoconductivity (Rose Model)", 21, "1950s", "Proven",
    "Δσ = e μ τ G L / d; G=generation rate, τ=lifetime; gain = τ/t_transit", "Photodetectors; confirmed")
add_eq(492, "Shockley-Read-Hall Recombination Rate", 23, "1952", "Proven",
    "U = (np−n_i²) / [τ_p (n+n₁) + τ_n (p+p₁)]; trap-assisted recombination", "All semiconductors; confirmed")
add_eq(493, "Auger Recombination Rate", 23, "1950s", "Proven",
    "U_Auger = C_n n²p + C_p n p²; three-particle non-radiative recombination", "High carrier density; LEDs, lasers")

# ---- SUPERCONDUCTIVITY (extended) ----
add_eq(494, "BCS Energy Gap at T=0", 12, "1957", "Proven",
    "Δ(0) = 1.764 k_B T_c; universal BCS ratio", "All conventional superconductors; confirmed")
add_eq(495, "Ginzburg-Landau Coherence Length", 12, "1950", "Proven",
    "ξ(T) = ξ(0) / √(1−T/T_c); ξ(0) = √(ℏ²/2m*|α|); spatial variation of order parameter", "Type I/II boundary; confirmed")
add_eq(496, "Ginzburg-Landau Penetration Depth", 12, "1950", "Proven",
    "λ(T) = λ(0)/√(1−T/T_c); magnetic field penetration into superconductor", "All superconductors; confirmed")
add_eq(497, "Ginzburg-Landau Parameter (κ)", 12, "1950", "Proven",
    "κ = λ/ξ; κ < 1/√2 → Type I; κ > 1/√2 → Type II", "Classification of superconductors")
add_eq(498, "Abrikosov Vortex Lattice (Lower/Upper Critical Fields)", 12, "1957", "Proven",
    "H_c1 = H_c ln κ/(√2 κ); H_c2 = √2 κ H_c; vortex state between", "Type II superconductors; confirmed")
add_eq(499, "Flux Pinning (Bean Critical State Model)", 12, "1962", "Proven",
    "J_c = constant; ∇×B = μ₀ J_c; critical state penetration profile", "High-T_c superconductors; confirmed")
add_eq(500, "Little-Parks Effect (Fluxoid Quantization)", 12, "1962", "Proven",
    "T_c oscillates with flux through cylinder; period = Φ₀ = h/2e", "Superconducting rings; confirmed")
add_eq(501, "Andreev Reflection", 12, "1964", "Proven",
    "e⁻ → NS interface reflects as h⁺; retroreflection; sub-gap conductance enhancement", "N-S junctions; all superconductors")

# ---- ELECTROCHEMISTRY (Materials) ----
add_eq(502, "Nernst Equation (Electrode Potential)", 21, "1889", "Proven",
    "E = E⁰ − (RT/nF) ln Q; E⁰ = standard reduction potential", "All electrochemistry; batteries, corrosion")
add_eq(503, "Butler-Volmer Equation (Electrode Kinetics)", 21, "1930s", "Proven",
    "j = j₀ [exp(α_a F η/RT) − exp(−α_c F η/RT)]; η = overpotential", "Electrode kinetics; electrodeposition, batteries")
add_eq(504, "Tafel Equation (High Overpotential Limit)", 21, "1905", "Proven",
    "η = a + b log |j|; b = 2.303 RT/(α nF) ≈ 120 mV/decade (α=0.5 at 298K)", "Corrosion rate; kinetic parameters")
add_eq(505, "Randles-Sevcik Equation (Cyclic Voltammetry Peak Current)", 21, "1948", "Proven",
    "i_p = 0.4463 n F A C √(n F v D/RT); reversible: i_p ∝ √v", "Electroanalytical chemistry; confirmed")
add_eq(506, "Cottrell Equation (Chronoamperometry)", 21, "1903", "Proven",
    "i(t) = n F A C √(D) / √(π t); diffusion-limited current decay", "Planar electrode; exact")
add_eq(507, "Faraday's Laws of Electrolysis", 3, "1834", "Proven",
    "m = (Q M)/(n F); mass deposited proportional to charge; Q=It", "All electroplating; exact")
add_eq(508, "Wagner Number (Current Distribution Uniformity)", 21, "1951", "Proven",
    "Wa = κ (dη/dj) / L; Wa ≫ 1 → uniform; Wa ≪ 1 → non-uniform", "Electroplating uniformity")

# ---- MECHANICAL SPECTROSCOPY / INTERNAL FRICTION ----
add_eq(509, "Zener Anelasticity (Standard Linear Solid)", 21, "1948", "Proven",
    "ε = σ/E_R + (σ/E_U−σ/E_R) (1−e^{−t/τ}); relaxation strength Δ = (E_U−E_R)/√(E_U E_R)", "Internal friction; anelastic relaxation")
add_eq(510, "Debye Peak (Internal Friction, Point Defect Relaxation)", 21, "1940s", "Proven",
    "tan δ = Δ ω τ / (1 + ω² τ²); τ = τ₀ exp(E_a/k_B T); peak at ωτ=1", "Snoek relaxation in bcc metals; C,N in Fe")
add_eq(511, "Bordoni Peak (Dislocation Relaxation)", 21, "1950s", "Proven",
    "kink-pair formation on dislocations; tan δ peak with E_a~0.1–0.2 eV", "fcc metals after cold work; confirmed")
add_eq(512, "Granato-Lücke Theory (Dislocation Damping)", 21, "1956", "Proven",
    "ε_d = (Λ L² σ)/(6 G) (amplitude-independent); breakaway at high amplitude", "Dislocation string model; confirmed")

# ---- SOFT MATTER / COLLOIDS / LIQUID CRYSTALS ----
add_eq(513, "Einstein Viscosity Equation (Rigid Sphere Suspension, Dilute)", 26, "1906", "Proven",
    "η = η_s (1 + 2.5 φ); φ = volume fraction; dilute limit φ≪1", "Colloid viscosity; confirmed")
add_eq(514, "Krieger-Dougherty Equation (Concentrated Suspension)", 26, "1959", "Proven",
    "η = η_s (1 − φ/φ_m)^{−[η]φ_m}; φ_m = maximum packing; [η]≈2.5", "Concentrated suspensions; divergence at φ_m")
add_eq(515, "Frank-Oseen Free Energy (Liquid Crystal Elastic)", 26, "1958", "Proven",
    "F = ½[K₁(∇·n)² + K₂(n·∇×n)² + K₃(n×∇×n)²]; splay, twist, bend", "Nematic liquid crystals; all LCDs")
add_eq(516, "Frederiks Transition Threshold (Liquid Crystal)", 26, "1920s", "Proven",
    "E_c = (π/d) √(K/ε₀Δε); voltage for director reorientation", "LCD device switching; confirmed")
add_eq(517, "Rayleigh Instability (Liquid Jet Breakup)", 26, "1878", "Proven",
    "λ_max = 9.016 r₀; fastest growing wavelength → uniform droplet formation", "Inkjet printing; fiber spinning")
add_eq(518, "Plateau-Rayleigh Instability for Liquid Threads", 26, "1873/1878", "Proven",
    "Cylindrical liquid thread unstable for λ > 2πr; surface-tension-driven breakup", "Microfluidics; droplet generation")

# ---- THERMAL ANALYSIS / CALORIMETRY ----
add_eq(519, "Kissinger Equation (DSC/DTA Peak Kinetics)", 21, "1957", "Proven",
    "ln(β/T_p²) = −E_a/(R T_p) + ln(A R/E_a); β = heating rate; T_p = peak temperature", "Activation energy from thermal analysis")
add_eq(520, "Ozawa-Flynn-Wall Equation (Isoconversional Kinetics)", 21, "1965/1966", "Proven",
    "log β = const − 0.4567 E_a/(R T); model-free kinetic analysis", "Polymer degradation; decomposition")
add_eq(521, "Tammann Nucleation Diagram (Nucleation vs Growth Rate)", 27, "1930s", "Proven",
    "Nucleation rate I(T) and growth rate U(T) bell-shaped; overlap → crystallization window", "Glass ceramics; crystallization control")
add_eq(522, "Time-Temperature-Transformation (TTT) Diagram Equation", 27, "1930s", "Proven",
    "τ(T) ∝ exp(ΔG*/k_B T + E_a/k_B T); C-curve shape; nose at intermediate T", "Steel heat treatment; glass devitrification")

# ---- THIN FILMS ----
add_eq(523, "Thornton Structure Zone Model (Thin Film Growth)", 21, "1974", "Proven",
    "T/T_m vs Ar pressure → Zone 1 (porous), Zone T (dense fibrous), Zone 2 (columnar), Zone 3 (recrystallized)", "All PVD/CVD film microstructure")
add_eq(524, "Herring Scaling Laws (Sintering Kinetics)", 21, "1950", "Proven",
    "(ΔL/L₀)^n ∝ t; n=1 viscous flow; n=2 volume diffusion; n=3 grain boundary diffusion; n=5 surface diffusion", "Sintering mechanism identification")
add_eq(525, "Pilling-Bedworth Ratio (Oxide Protectiveness)", 21, "1923", "Proven",
    "PBR = V_oxide / V_metal consumed; 1 < PBR < 2 → protective; PBR > 2 → spallation; PBR < 1 → porous", "High-temperature oxidation; empirical")
add_eq(526, "Ellingham Diagram (Oxide Thermodynamic Stability)", 21, "1944", "Proven",
    "ΔG⁰ = RT ln p_O₂; line slope = −ΔS⁰; lower line → more stable oxide", "Metallurgy; corrosion; standard reference")

# ---- ADDITIONAL ELECTRONIC MATERIALS ----
add_eq(527, "Mott-Gurney Law (Space-Charge-Limited Current)", 21, "1940", "Proven",
    "J = (9/8) ε μ V² / L³; trap-free SCLC; Child's law for solids", "Organic semiconductors; insulators")
add_eq(528, "Richardson-Dushman Equation (Thermionic Emission)", 21, "1901/1923", "Proven",
    "J = A_R T² exp(−φ/k_B T); A_R = 4π m e k_B²/h³ ≈ 1.20×10⁶ A/(m²K²)", "Vacuum tubes; thermionic converters")
add_eq(529, "Schottky Barrier Height (Metal-Semiconductor)", 23, "1938", "Proven",
    "φ_Bn = φ_m − χ_s; φ_Bp = E_g/q + χ_s − φ_m (ideal, no interface states)", "Schottky diode; confirmed with Fermi pinning corrections")
add_eq(530, "Spicer's Unified Defect Model (Fermi Level Pinning at Interfaces)", 23, "1979", "Proven",
    "E_F pinned by deep native defects at interface; independent of metal work function", "GaAs, InP Schottky barriers; confirmed")

# ---- BIOMATERIALS / BIOPHYSICS (Materials Context) ----
add_eq(531, "Wolff's Law (Bone Remodeling, Mechanical Adaptation)", 21, "1892", "Proven",
    "Bone density distribution adapts to principal stress trajectories; σ_ij → ρ_ij", "Bone biomechanics; implant design")
add_eq(532, "Fung's Quasi-Linear Viscoelasticity (Soft Tissue)", 21, "1972", "Proven",
    "σ(t) = ∫₀ᵗ G(t−τ) ∂σ_e(ε)/∂ε · ∂ε/∂τ dτ; separable elastic + relaxation", "Tendons, ligaments, blood vessels")
add_eq(533, "Ogden Hyperelastic Model (Biological Tissue)", 21, "1972", "Proven",
    "W = Σ (μ_k/α_k) (λ₁^{α_k} + λ₂^{α_k} + λ₃^{α_k} − 3); principal stretches; fits large deformations", "Arteries, skin, brain tissue")

# ---- MISCELLANEOUS MATERIAL LAWS ----
add_eq(534, "Matthiessen's Rule (Electrical Resistivity Additivity)", 21, "1864", "Proven",
    "ρ_total = ρ_thermal + ρ_impurity + ρ_deformation; independent contributions sum", "Metals; approximate due to deviations from phonon drag")
add_eq(535, "Nordheim's Rule (Alloy Resistivity)", 21, "1930s", "Proven",
    "ρ_alloy = ρ_pure + C x(1−x); x = atomic fraction; max at x=0.5 for disordered binary", "Binary alloy resistivity; confirmed")
add_eq(536, "Miedema's Rules (Alloy Formation Enthalpy)", 21, "1970s", "Proven",
    "ΔH_form = f(Δφ*, Δn_ws^{1/3}); work function + electron density mismatch → semi-empirical model", "Binary alloy thermodynamics; predictive")
add_eq(537, "Köhler's Rule (Magnetoresistance Scaling)", 21, "1940s", "Proven",
    "Δρ(B)/ρ(0) = F[B/ρ(0)]; Kohler plot universal for given material", "Metals; confirmed for simple Fermi surfaces")
add_eq(538, "Zener Breakdown (Band-to-Band Tunneling)", 23, "1934", "Proven",
    "D = exp[−4√(2m*) E_g^{3/2}/(3 e ℏ E)]; tunneling probability through forbidden gap", "Zener diodes; high E-field transport")
add_eq(539, "Klemens Model (Thermal Boundary Resistance / Kapitza)", 21, "1959", "Proven",
    "R_K = 4 / (ρ c v ζ); acoustic mismatch model; acoustic impedance mismatch → resistance", "Nanoscale thermal management; interfaces")
add_eq(540, "Diffuse Mismatch Model (Thermal Boundary Resistance)", 21, "1980s", "Proven",
    "R_K from transmission probability of phonons regardless of mode; rough interfaces", "Room temperature Kapitza resistance")

cur.executemany("INSERT INTO equations VALUES (?,?,?,?,?,?,?,?)", mat_eqs)

# ================================================================
# SUB-EQUATIONS for material physics (key formulas)
# ================================================================
m_se = []
def add_mse(eq_id, sub, name, latex, desc, cond=""):
    global max_sub
    max_sub += 1
    m_se.append((eq_id, sub, name, latex, desc, cond))

add_mse(335, "Laue", "Laue Equations", "\\vec{a}\\cdot\\Delta\\vec{k}=2\\pi h,\\; \\vec{b}\\cdot\\Delta\\vec{k}=2\\pi k,\\; \\vec{c}\\cdot\\Delta\\vec{k}=2\\pi l", "3D constructive interference condition; equivalent to Bragg", "")
add_mse(336, "StructFact", "Structure Factor", "F_{hkl}=\\sum_j f_j(\\vec{q})\\,e^{2\\pi i(hx_j+ky_j+lz_j)}", "Scattering amplitude from unit cell contents", "Accounts for all atoms")
add_mse(347, "TrueStress", "True Stress-Strain", "\\sigma_t = \\sigma_e(1+\\varepsilon_e),\\; \\varepsilon_t = \\ln(1+\\varepsilon_e)", "True (Ludwik) vs engineering; volume constancy in plasticity", "")
add_mse(349, "HallPetch", "Hall-Petch Relation", "\\sigma_y = \\sigma_0 + \\frac{k_y}{\\sqrt{d}}", "Grain boundary strengthening; d = grain diameter", "Valid down to ~10-20 nm; inverse Hall-Petch below")
add_mse(354, "Griffith", "Griffith Fracture Criterion", "\\sigma_f = \\sqrt{\\frac{2E\\gamma_s}{\\pi a}}", "Critical stress for unstable crack growth in brittle materials", "Glass, ceramics; energy balance")
add_mse(355, "SIF", "Stress Intensity Factor", "K_I = Y\\sigma\\sqrt{\\pi a}", "K_I ≥ K_Ic → fracture; Mode I loading", "Linear elastic fracture mechanics")
add_mse(357, "Paris", "Paris Law (Fatigue)", "\\frac{da}{dN} = C(\\Delta K)^m", "Crack growth per cycle; ΔK = stress intensity range", "Striations per cycle; m≈2–4 for metals")
add_mse(366, "DebyeCv", "Debye Heat Capacity", "C_V = 9Nk_B\\left(\\frac{T}{\\Theta_D}\\right)^3\\!\\int_0^{\\Theta_D/T}\\!\\frac{x^4 e^x}{(e^x-1)^2}dx", "Phonon specific heat; C_V ∝ T³ for T ≪ Θ_D", "All crystalline solids")
add_mse(375, "ComplexEps", "Complex Dielectric Constant", "\\varepsilon^*(\\omega)=\\varepsilon'(\\omega)-i\\varepsilon''(\\omega)", "Real part = storage; imaginary part = loss", "\\tan\\delta = \\varepsilon''/\\varepsilon'")
add_mse(376, "C-M", "Clausius-Mossotti Relation", "\\frac{\\varepsilon_r-1}{\\varepsilon_r+2} = \\frac{N\\alpha}{3\\varepsilon_0}", "Macroscopic ε_r from microscopic polarizability α", "Non-polar; Lorentz local field")
add_mse(381, "Piezo", "Piezoelectric Constitutive Equations", "S_{ij} = s_{ijkl}^E T_{kl} + d_{kij} E_k,\\; D_i = d_{ikl} T_{kl} + \\varepsilon_{ik}^T E_k", "Strain-charge form; direct and converse effects", "6mm symmetry for PZT")
add_mse(387, "Intrinsic", "Intrinsic Carrier Concentration", "n_i = \\sqrt{N_c N_v}\\, e^{-E_g/(2k_B T)}", "Si: n_i ≈ 1.0×10¹⁰ cm⁻³ at 300K; Ge: 2.4×10¹³", "Thermal generation across band gap")
add_mse(390, "Diode", "Shockley Diode Equation", "I = I_s\\left[e^{(qV)/(nk_BT)} - 1\\right]", "Ideal p-n junction; I_s ∝ n_i²", "n=1 ideal; n>1 recombination/generation")
add_mse(394, "MOSFET", "MOSFET Saturation Current", "I_{D,sat} = \\frac{\\mu_n C_{ox}}{2}\\frac{W}{L}(V_{GS}-V_{th})^2", "Channel width W, length L; V_GS > V_th", "Square-law; confirmed to % level")
add_mse(398, "Brus", "Brus Equation (Quantum Dot Gap)", "E_g(R) = E_g^{\\text{bulk}} + \\frac{\\hbar^2\\pi^2}{2\\mu R^2} - \\frac{1.8 e^2}{\\varepsilon_r R}", "μ = reduced exciton mass; third term = Coulomb", "CdSe, CdS, PbS dots; confirmed")
add_mse(403, "Stoner", "Stoner Criterion", "N(E_F)\\,I > 1", "Ferromagnetism when DOS × exchange exceeds unity", "Fe: N(E_F)I≈1.7; Pd: ≈0.9 (paramagnetic)")
add_mse(407, "Bloch3/2", "Bloch T^{3/2} Law", "M_s(T) = M_s(0)\\left[1 - \\left(\\frac{T}{T_c}\\right)^{3/2}\\right]", "Low-temperature magnetization from spin-wave excitations", "3D Heisenberg ferromagnet")
add_mse(411, "GMR", "Giant Magnetoresistance", "\\frac{\\Delta R}{R} = \\frac{R_{AP}-R_P}{R_P}", "Spin-dependent scattering; Co/Cu multilayers", "Nobel Prize 2007 (Fert + Grünberg)")
add_mse(421, "BeerLambert", "Beer-Lambert Law", "A = \\log_{10}\\frac{I_0}{I} = \\varepsilon c L", "Absorbance; linear with concentration and path length", "Dilute solutions; monochromatic light")
add_mse(425, "FRET", "FRET Efficiency", "E = \\frac{1}{1 + (r/R_0)^6}", "R₀ = Förster radius (1–10 nm); r⁻⁶ distance dependence", "Molecular ruler; single-molecule")
add_mse(435, "RubberElas", "Rubber Elasticity (Neo-Hookean)", "\\sigma_t = n k_B T\\left(\\lambda - \\frac{1}{\\lambda^2}\\right)", "Entropy elasticity; n = crosslink density", "Moderate strains (<300%); affine model")
add_mse(437, "FloryHuggins", "Flory-Huggins Free Energy", "\\frac{\\Delta G_{mix}}{k_B T} = n_1\\ln\\phi_1 + n_2\\ln\\phi_2 + \\chi n_1\\phi_2", "χ = Flory interaction parameter; χ < 0.5 → miscible", "Polymer solutions and blends")
add_mse(441, "Reptation", "Reptation Time (de Gennes)", "\\tau_{rep} \\propto N^3,\\; D_{rep} \\propto N^{-2}", "Entangled polymer chain motion through tube", "Nobel Prize in Physics 1991")
add_mse(445, "Avrami", "Avrami Crystallization Kinetics", "X(t) = 1 - \\exp(-k t^n)", "n = Avrami exponent; n≈1–4 depending on mechanism", "Johnson-Mehl-Avrami-Kolmogorov")
add_mse(447, "Young", "Young's Equation (Contact Angle)", "\\gamma_{sv} = \\gamma_{sl} + \\gamma_{lv}\\cos\\theta", "Three-phase equilibrium; smooth homogeneous surface", "Wettability; hydrophilicity θ<90°")
add_mse(452, "Langmuir", "Langmuir Isotherm", "\\theta = \\frac{KP}{1+KP}", "θ = fractional monolayer coverage; K ∝ e^{-ΔH/RT}", "Homogeneous surface; no lateral interactions")
add_mse(453, "BET", "BET Isotherm", "\\frac{P}{V(P_0-P)} = \\frac{1}{V_m C} + \\frac{(C-1)}{V_m C}\\frac{P}{P_0}", "Multilayer physisorption; surface area from V_m", "Standard for surface area (N₂ at 77K)")
add_mse(464, "Fick1", "Fick's First Law", "\\vec{J} = -D\\,\\nabla c", "Flux proportional to concentration gradient", "Steady-state diffusion")
add_mse(465, "Fick2", "Fick's Second Law", "\\frac{\\partial c}{\\partial t} = D\\,\\nabla^2 c", "Time-dependent diffusion; for constant D", "3D: ∂c/∂t = D ∂²c/∂x² (1D)")
add_mse(467, "Arrhenius-D", "Arrhenius Diffusion", "D = D_0\\,e^{-E_a/k_B T}", "Thermally activated atomic jumps", "Vacancy, interstitial mechanisms")
add_mse(473, "CNT", "Classical Nucleation Theory", "\\Delta G = \\frac{4}{3}\\pi r^3 \\Delta G_v + 4\\pi r^2 \\gamma", "r* = −2γ/ΔG_v; ΔG* = 16πγ³/(3ΔG_v²)", "Homogeneous nucleation barrier")
add_mse(477, "LSW", "Ostwald Ripening (LSW Theory)", "\\langle r\\rangle^3 - \\langle r_0\\rangle^3 = k t", "k ∝ γ D c_∞ V_m²/(RT); coarsening", "Diffusion-limited coarsening of precipitates")
add_mse(481, "ROM", "Rule of Mixtures", "E_c = E_f V_f + E_m V_m", "Voigt upper bound (isostrain, parallel loading)", "Elastic composite modulus")
add_mse(494, "BCS-gap", "BCS Energy Gap (T=0)", "\\Delta(0) = 1.764\\,k_B T_c", "Universal BCS ratio; confirmed by tunneling", "Weak-coupling BCS theory")
add_mse(495, "GL-Coher", "Ginzburg-Landau Coherence Length", "\\xi(T) = \\xi(0)/\\sqrt{1-T/T_c}", "\\xi(0) = \\sqrt{\\hbar^2/(2m^*|\\alpha|)}", "Superconducting order parameter range")
add_mse(502, "Nernst", "Nernst Equation", "E = E^\\ominus - \\frac{RT}{nF}\\ln Q", "Electrode potential from concentration and T", "All electrochemistry at equilibrium")
add_mse(503, "ButlerVol", "Butler-Volmer Equation", "j = j_0\\left[e^{\\alpha_a F\\eta/(RT)} - e^{-\\alpha_c F\\eta/(RT)}\\right]", "Current from overpotential η; α_a+α_c≈1", "Electrode kinetics; charge transfer")
add_mse(513, "EinsteinVisc", "Einstein Viscosity", "\\eta = \\eta_s(1 + 2.5\\phi)", "Dilute rigid sphere suspension; φ ≪ 0.01", "Brownian contribution; Einstein 1906")
add_mse(515, "FrankOseen", "Frank-Oseen Elastic Energy", "F = \\frac{1}{2}[K_1(\\nabla\\cdot\\mathbf{n})^2+K_2(\\mathbf{n}\\cdot\\nabla\\times\\mathbf{n})^2+K_3(\\mathbf{n}\\times\\nabla\\times\\mathbf{n})^2]", "Splay, twist, bend elastic constants", "Nematic liquid crystal director field")
add_mse(527, "SCLC", "Space-Charge-Limited Current (Mott-Gurney)", "J = \\frac{9}{8}\\varepsilon\\mu\\frac{V^2}{L^3}", "Trap-free SCLC; Child's law for solids", "Organic semiconductors; insulators")
add_mse(528, "Richardson", "Richardson-Dushman Thermionic Emission", "J = A_R T^2 e^{-\\phi/k_B T}", "A_R = 4π m e k_B²/h³ ≈ 120 A/(cm²K²)", "Electron emission from heated cathode")

cur.executemany("INSERT INTO sub_equations (equation_id, subsection, name, latex_formula, description, conditions) VALUES (?,?,?,?,?,?)", m_se)

# ================================================================
# VERIFICATIONS for material physics
# ================================================================
mat_ver = []
def add_mv(eid, test, expt, yr, prec, st="Confirmed"):
    global max_ver
    max_ver += 1
    mat_ver.append((eid, test, expt, yr, prec, st))

add_mv(334, "Powder X-ray Diffraction Structure Solution", "Bragg/Bragg Jr. 1913", 1913, "All crystal structures", "Confirmed")
add_mv(349, "Hall-Petch Confirmed in >100 Metals/Alloys", "Hall 1951, Petch 1953", 1953, "σ_y vs 1/√d linear", "Confirmed")
add_mv(357, "Paris Law for >50 Structural Alloys", "Paris & Erdogan 1963", 1963, "da/dN vs ΔK power law; confirmed by ASTM E647", "Confirmed")
add_mv(366, "Debye T³ Law at Low T", "Low-temperature calorimetry", 1920, "C_V ∝ T³ below ~Θ_D/30", "Confirmed")
add_mv(369, "Wiedemann-Franz in Metals (Sommerfeld value)", "Measurements since 1900", 1930, "Lorentz number = 2.44×10⁻⁸ WΩ/K²", "Confirmed")
add_mv(387, "Intrinsic Carrier Concentration in Si/Ge/GaAs", "Hall effect + resistivity vs T", 1950, "Extracted n_i matches theory", "Confirmed")
add_mv(390, "Shockley Diode I-V Fit (Si, Ge diodes)", "Shockley 1949", 1949, "Forward bias exponential; reverse saturation", "Confirmed")
add_mv(394, "MOSFET Long-Channel I-V Characteristics", "Intel 4004 to all modern chips", 1970, "Square-law saturation confirmed to <10%", "Confirmed")
add_mv(398, "Quantum Dot Size-Dependent Emission (CdSe)", "Brus/Bawendi/Alivisatos 1980s", 1990, "Emission blue-shift with decreasing R; matches Brus eq.", "Confirmed")
add_mv(403, "Stoner Criterion for 3d Ferromagnets", "Gunnarsson 1976, Janak 1977", 1977, "DFT calculations confirm N(E_F)I>1 for Fe,Co,Ni", "Confirmed")
add_mv(411, "GMR in Co/Cu Multilayers", "Baibich et al. (Fert group) 1988", 1988, "ΔR/R up to 50% at 4.2K; Nobel 2007", "Confirmed")
add_mv(412, "TMR in Fe/MgO/Fe MTJs", "Parkin/Yuasa 2004", 2004, "TMR > 200% at RT; Δ₁ coherent tunneling", "Confirmed")
add_mv(421, "Beer-Lambert Law in Analytical Chemistry", "Standard spectrophotometry", 1950, "A vs C linear over several orders of magnitude", "Confirmed")
add_mv(425, "FRET Single-Molecule Distance Measurement", "Ha et al. 1996, single-molecule", 1996, "Distance determined to <0.5 nm accuracy", "Confirmed")
add_mv(435, "Neo-Hookean Fit to Natural Rubber", "Treloar 1940s", 1944, "σ-λ fit for λ<3.0; deviation at high strains", "Confirmed")
add_mv(437, "Flory-Huggins Phase Diagram Predictions", "PS/cyclohexane, other systems", 1960, "χ parameter from SANS, osmotic pressure", "Confirmed")
add_mv(441, "Reptation: D~N⁻², τ~N³ confirmed", "NMR, neutron spin-echo, rheology", 1990, "Molecular weight scaling confirmed for entangled polymers", "Confirmed")
add_mv(445, "Avrami Kinetics for Polymer Crystallization", "DSC isothermal crystallization", 1960, "Exponent n matches nucleation+growth mechanism", "Confirmed")
add_mv(447, "Young's Equation on Molecularly Smooth Surfaces", "Self-assembled monolayers, mica", 1990, "Cosθ vs γ_lv (Zisman plot); consistent", "Confirmed")
add_mv(449, "Cassie-Baxter Superhydrophobic Surfaces", "Lotus leaf; artificial surfaces", 2000, "θ* > 150°, sliding angle < 10°; confirmed", "Confirmed")
add_mv(453, "BET Surface Area Standard (N₂, 77K)", "Commercial BET instruments", 1950, "Surface area ±5% for standards; widely used", "Confirmed")
add_mv(464, "Fick's Laws in Solid-State Diffusion", "Radioactive tracer measurements", 1950, "D values from penetration profiles; confirmed", "Confirmed")
add_mv(468, "Kirkendall Effect (Marker Movement)", "Kirkendall & Smigelskas 1947", 1947, "Inert markers move; D_Zn>D_Cu in brass; confirmed", "Confirmed")
add_mv(473, "CNT: Turnbull's Droplet Experiments", "Turnbull 1952 (Hg droplets)", 1952, "Undercooling ΔT/T_m≈0.18 confirmed for homogeneous", "Confirmed")
add_mv(474, "JMAK Kinetics for Metallic Glass Crystallization", "DSC/DTA measurements", 1980, "n ~ 3-4 for 3D growth; confirmed for many glasses", "Confirmed")
add_mv(481, "Rule of Mixtures for Continuous Fiber Composites", "Carbon/epoxy, glass/polyester", 1970, "Longitudinal E matches ROM within 5%", "Confirmed")
add_mv(494, "BCS Gap 2Δ/kT_c = 3.5 (tunneling)", "Giaever tunneling spectroscopy", 1960, "2Δ/k_B T_c ≈ 3.5–3.6 for weak coupling (Al, Sn, Pb)", "Confirmed")
add_mv(502, "Nernst Equation Verified by Concentration Cells", "Standard electrochemistry labs", 1900, "E vs log Q linear with RT/nF slope", "Confirmed")
add_mv(503, "Butler-Volmer for H₂ Evolution on Pt", "Electrode kinetics measurements", 1950, "Tafel slope ~120 mV/dec; j₀ matches exchange current", "Confirmed")
add_mv(507, "Faraday's Laws: Cu Electroplating Efficiency", "Industrial electroplating", 1900, "Mass deposited = QM/(nF) to >99.9% efficiency", "Confirmed")
add_mv(513, "Einstein Viscosity Verified for Latex Suspensions", "Dilute colloid viscometry", 1940, "η/η_s−1 = 2.5φ in dilute limit; confirmed", "Confirmed")
add_mv(515, "Frank-Oseen Elastic Constants from Frederiks Transition", "Nematic liquid crystals", 1970, "K₁₁,K₂₂,K₃₃ measured; match theory", "Confirmed")

cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", mat_ver)

# ================================================================
# UPDATE STATS
# ================================================================
conn.commit()
print(f"Added {len(mat_eqs)} material physics equations (now total: {max_id})")
print(f"Added {len(m_se)} sub-equations")
print(f"Added {len(mat_ver)} verifications")
print(f"New domains: Crystallography, Semiconductor Physics, Polymer Physics, Surface Science, Soft Matter, Phase Transformations")

cur.execute("SELECT d.name, COUNT(e.id) FROM domains d LEFT JOIN equations e ON e.domain_id=d.id GROUP BY d.id ORDER BY d.id")
print("\nDomain equation counts (all):")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
