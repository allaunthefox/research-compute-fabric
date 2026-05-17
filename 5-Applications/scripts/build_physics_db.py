#!/usr/bin/env python3
"""Build a comprehensive SQLite flatfile of all proven physics equations."""

import sqlite3, os

DB = "/home/allaun/physics_equations.db"
if os.path.exists(DB): os.remove(DB)
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE domains (id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT, parent_domain_id INTEGER REFERENCES domains(id));
CREATE TABLE equations (id INTEGER PRIMARY KEY, eq_number INTEGER, title TEXT, domain_id INTEGER REFERENCES domains(id), year_range TEXT, status TEXT DEFAULT 'Proven', significance TEXT, precision_note TEXT);
CREATE TABLE sub_equations (id INTEGER PRIMARY KEY, equation_id INTEGER REFERENCES equations(id), subsection TEXT, name TEXT, latex_formula TEXT, description TEXT, conditions TEXT);
CREATE TABLE constants (id INTEGER PRIMARY KEY, symbol TEXT, name TEXT, value_si TEXT, uncertainty TEXT, is_exact INTEGER DEFAULT 0);
CREATE TABLE verifications (id INTEGER PRIMARY KEY, equation_id INTEGER REFERENCES equations(id), test_name TEXT, experiment TEXT, year INTEGER, precision_level TEXT, status TEXT DEFAULT 'Confirmed');
CREATE TABLE open_problems (id INTEGER PRIMARY KEY, name TEXT, description TEXT, related_equation_ids TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS eq_fts USING fts5(title, description, latex_formula, content='equations', content_rowid='id');
""")

domains = [
    (1,"Classical Mechanics","Forces, energy, momentum, rigid bodies, oscillations",None),
    (2,"Gravitation","Newtonian and relativistic gravity, orbits",None),
    (3,"Electromagnetism","Electric & magnetic fields, circuits, radiation",None),
    (4,"Thermodynamics","Heat, entropy, statistical mechanics, phase transitions",None),
    (5,"Quantum Mechanics","Wavefunctions, operators, uncertainty, spin",None),
    (6,"Relativity","Special and general relativity, spacetime, black holes",None),
    (7,"Quantum Field Theory","Standard Model, QED, QCD, electroweak, Yukawa",None),
    (8,"Cosmology","FLRW, Friedmann, CMB, BBN, dark energy",None),
    (9,"Fluid Dynamics","Navier-Stokes, turbulence, Bernoulli, aerodynamics",None),
    (10,"Optics","Wave optics, diffraction, interference, polarization, Snell",None),
    (11,"Acoustics","Sound waves, resonance, Doppler, standing waves",None),
    (12,"Condensed Matter","Solids, crystals, BCS, Josephson, magnetism, Bloch",None),
    (13,"Nuclear Physics","Decay, fission, fusion, shell model, neutrino oscillations",None),
    (14,"Astrophysics","Stellar structure, HR diagram, nucleosynthesis, compact objects",None),
    (15,"Plasma Physics","MHD, Debye screening, Alfvén waves, Saha ionization",None),
    (16,"Mathematical Physics","Noether, symmetry, Fourier, Stokes, Green, special functions",None),
    (17,"Statistical Mechanics","Ensembles, partition functions, fluctuation theorems",None),
    (18,"Continuum Mechanics","Hooke's law, Cauchy stress, Euler-Bernoulli beam",None),
    (19,"Information Theory","Shannon entropy, Landauer principle, channel capacity",None),
    (20,"Metrology","Fundamental constants, SI definitions",None),
]
cur.executemany("INSERT INTO domains VALUES (?,?,?,?)", domains)

constants = [
    (1,"c","Speed of light","299792458 m/s","Exact",1),
    (2,"h","Planck constant","6.62607015e-34 J·s","Exact",1),
    (3,"hbar","Reduced Planck constant","1.054571817e-34 J·s","9.1e-9 rel",0),
    (4,"G","Gravitational constant","6.67430e-11 m³/(kg·s²)","2.2e-5 rel",0),
    (5,"k_B","Boltzmann constant","1.380649e-23 J/K","Exact",1),
    (6,"e","Elementary charge","1.602176634e-19 C","Exact",1),
    (7,"m_e","Electron mass","9.1093837015e-31 kg","3.0e-10 rel",0),
    (8,"m_p","Proton mass","1.67262192369e-27 kg","5.1e-11 rel",0),
    (9,"m_n","Neutron mass","1.67492749804e-27 kg","5.7e-11 rel",0),
    (10,"eps0","Vacuum permittivity","8.8541878128e-12 F/m","1.5e-10 rel",0),
    (11,"mu0","Vacuum permeability","1.25663706212e-6 N/A²","1.5e-10 rel",0),
    (12,"N_A","Avogadro number","6.02214076e23 mol⁻¹","Exact",1),
    (13,"alpha","Fine-structure constant","1/137.035999084","1.5e-10 rel",0),
    (14,"R_y","Rydberg energy","13.605693123 eV","1.1e-12 rel",0),
    (15,"a0","Bohr radius","5.29177210903e-11 m","1.1e-12 rel",0),
    (16,"mu_B","Bohr magneton","9.2740100783e-24 J/T","3.0e-10 rel",0),
    (17,"sigma_SB","Stefan-Boltzmann constant","5.670374419e-8 W/(m²·K⁴)","3.7e-7 rel",0),
    (18,"G_F","Fermi constant","1.1663787e-5 GeV⁻²","5.1e-7 rel",0),
    (19,"Lambda_QCD","QCD scale","~0.210 GeV","~7%",0),
    (20,"H0","Hubble constant","67.4 km/(s·Mpc)","0.7%",0),
    (21,"l_P","Planck length","1.616255e-35 m","Derived",0),
    (22,"t_P","Planck time","5.391247e-44 s","Derived",0),
    (23,"m_P","Planck mass","2.176434e-8 kg","Derived",0),
    (24,"T_CMB","CMB temperature today","2.72548 K","5.7e-4 rel",0),
    (25,"R_gas","Gas constant","8.314462618 J/(mol·K)","Exact",1),
    (26,"Phi0","Magnetic flux quantum","2.067833848e-15 Wb","1.9e-9 rel",0),
    (27,"sigma_el","Electrical conductivity (Cu)","5.96e7 S/m","Material",0),
    (28,"mu_N","Nuclear magneton","5.0507837461e-27 J/T","3.0e-10 rel",0),
    (29,"lambda_C","Electron Compton wavelength","2.42631023867e-12 m","3.0e-10 rel",0),
    (30,"r_e","Classical electron radius","2.8179403262e-15 m","Derived",0),
]
cur.executemany("INSERT INTO constants VALUES (?,?,?,?,?,?)", constants)

# (id, eq_number, title, domain, year, status, significance, precision)
eq = []
def E(id, num, title, dom, year, status, sig, prec):
    eq.append((id, num, title, dom, year, status, sig, prec))

# CLASSICAL MECHANICS (1-25)
E(1,1,"Newton's Three Laws of Motion",1,"1687","Proven","Foundation of all classical mechanics; inertial frames; F=dp/dt; action=reaction","Exact in v<<c, weak gravity")
E(2,2,"Lagrangian Mechanics (Principle of Least Action)",1,"1788","Proven","Action S=∫L dt; δS=0 → Euler-Lagrange equations","Mathematical theorem — exact")
E(3,3,"Hamiltonian Mechanics",1,"1833","Proven","Canonical eqs: q̇=∂H/∂p, ṗ=−∂H/∂q; symplectic structure","Equivalent to Lagrangian; exact")
E(4,4,"Hamilton-Jacobi Equation",1,"1834","Proven","∂S/∂t + H(q,∂S/∂q,t)=0; bridges classical→quantum","Exact; classical limit of Schrödinger")
E(5,5,"Euler-Lagrange Equation",1,"1744–88","Proven","d/dt(∂L/∂q̇) − ∂L/∂q = 0; from δS=0","Exact consequence of calculus of variations")
E(6,6,"D'Alembert's Principle",1,"1743","Proven","Virtual work for dynamics: Σ(F_i−ṗ_i)·δr_i=0","Exact; leads to Lagrange equations")
E(7,7,"Euler's Rigid Body Rotation Equations",1,"1765","Proven","I·ω̇ + ω×(I·ω) = τ; angular momentum dynamics","Confirmed: gyroscopes, satellites, robots")
E(8,8,"Conservation of Momentum",1,"1687","Proven","dP/dt = ΣF_ext; P constant when ΣF_ext=0","Spatial translation symmetry; Noether; never violated")
E(9,9,"Conservation of Angular Momentum",1,"1687","Proven","dL/dt = τ_ext; L=Iω constant when τ=0","Rotational symmetry; never violated")
E(10,10,"Conservation of Energy",1,"1847","Proven","dE/dt=0 for isolated system; time translation symmetry","Never violated in any closed system")
E(11,11,"Work-Energy Theorem",1,"1829","Proven","W=ΔKE; ∫F·dr = ½mv²_f − ½mv²_i","Consequence of Newton's 2nd; exact for point particles")
E(12,12,"Impulse-Momentum Theorem",1,"1687","Proven","J=∫F dt=Δp","Derived from F=dp/dt; exact")
E(13,13,"Center of Mass Equation",1,"1687","Proven","MR̈_cm=ΣF_ext; COM moves like point particle","Exact consequence of Newton's 3rd")
E(14,14,"Hooke's Law",18,"1660","Proven","F=−kx; σ=Eε; linear elastic response","Valid up to elastic limit")
E(15,15,"Parallel Axis Theorem",1,"1673","Proven","I=I_cm+Md²","Exact geometric theorem")
E(16,16,"Coriolis Force",1,"1835","Proven","F_cor=−2m ω×v' (rotating frame)","Foucault pendulum; weather; ballistics")
E(17,17,"Centrifugal Force",1,"1687","Proven","F_cf=−m ω×(ω×r) (rotating frame)","Fictitious force in rotating frame; confirmed")
E(18,18,"Simple Harmonic Motion",1,"1673","Proven","ẍ+ω²x=0; x=A cos(ωt+φ); T=2π/ω","All oscillators; exact for linear restoring force")
E(19,19,"Damped Harmonic Oscillator",1,"19th c.","Proven","ẍ+2βẋ+ω₀²x=0; under/over/critically damped","Confirmed in all damped mechanical systems")
E(20,20,"Forced Oscillator + Resonance",1,"19th c.","Proven","ẍ+2βẋ+ω₀²x=(F₀/m)cos ωt; A=F₀/m/√((ω₀²−ω²)²+4β²ω²)","All driven oscillators; confirmed")
E(21,21,"Coupled Oscillators (Normal Modes)",1,"18th c.","Proven","mẍ₁=−k x₁−k'(x₁−x₂); symmetric/antisymmetric modes","Confirmed: molecular vibrations, engineering")
E(22,22,"Pendulum Equation",1,"1638","Proven","θ̈+(g/L)sin θ=0; small angle: ω=√(g/L)","Galileo's law of isochronism; confirmed")
E(23,23,"Kinematics (Constant Acceleration)",1,"Ancient","Proven","v=v₀+at, x=x₀+v₀t+½at², v²=v₀²+2aΔx","Exact for constant a")
E(24,24,"Universal Gravitation Law",2,"1687","Proven","F=−G m₁m₂/r² r̂","Weak-field limit of GR; inverse-square to 10⁻¹⁶")
E(25,25,"Gravitational Potential Energy",2,"1773","Proven","U=−GMm/r; F=−∇U","Scalar potential; confirmed")

# GRAVITATION (26-35)
E(26,26,"Kepler's First Law",2,"1609","Proven","Planetary orbits are ellipses with Sun at one focus","Derived from inverse-square force")
E(27,27,"Kepler's Second Law",2,"1609","Proven","Equal areas swept in equal times (areal velocity constant)","Angular momentum conservation")
E(28,28,"Kepler's Third Law",2,"1619","Proven","T²∝a³; T²=(4π²/GM)a³","Confirmed for all gravitational two-body systems")
E(29,29,"Escape Velocity",2,"1687","Proven","v_esc=√(2GM/r)","Energy conservation; spaceflight confirmed")
E(30,30,"Orbital Velocity (Circular)",2,"1687","Proven","v_orb=√(GM/r)","Exact for circular two-body orbits")
E(31,31,"Poisson Equation (Gravity)",2,"1813","Proven","∇²Φ=4πGρ","Newtonian limit of Einstein field eqs")
E(32,32,"Tidal Force",2,"1687","Proven","F_tide≈2GMmΔr/r³","Earth-Moon tides; Roche limit; confirmed")
E(33,33,"Gravitational Time Dilation (GR)",6,"1907","Proven","Δt'=Δt√(1−2GM/rc²)","Pound-Rebka 1960; GPS correction; confirmed")
E(34,34,"Precession of Perihelion (GR)",6,"1915","Proven","Δφ=6πGM/(a(1−e²)c²) per orbit","Mercury 43\"/century; confirmed to <0.1%")
E(35,35,"Lense-Thirring Precession (Frame Dragging)",6,"1918","Proven","Ω_LT=GJ/(2c²r³)(3(r̂·Ĵ)r̂−Ĵ)","Gravity Probe B; LAGEOS; ~10% precision")

# ELECTROMAGNETISM (36-65)
E(36,36,"Coulomb's Law",3,"1785","Proven","F=(1/4πε₀)q₁q₂/r² r̂","Inverse-square confirmed to δ<10⁻¹⁶")
E(37,37,"Lorentz Force Law",3,"1895","Proven","F=q(E+v×B)","Every accelerator validates it")
E(38,38,"Maxwell's Equations (Differential)",3,"1861–65","Proven","∇·E=ρ/ε₀, ∇·B=0, ∇×E=−∂B/∂t, ∇×B=μ₀J+μ₀ε₀∂E/∂t","Most tested equations; unified E&M+optics")
E(39,39,"Maxwell's Equations (Integral)",3,"1861–65","Proven","∮E·dA=Q/ε₀, ∮B·dA=0, ∮E·dl=−dΦ_B/dt, ∮B·dl=μ₀I+μ₀ε₀dΦ_E/dt","Equivalent; engineering applications")
E(40,40,"Maxwell's Equations (Covariant / Tensor)",3,"1908","Proven","∂_μF^{μν}=μ₀J^ν; ∂_μF̃^{μν}=0","Relativistic form; exact")
E(41,41,"Scalar and Vector Potentials",3,"19th c.","Proven","B=∇×A; E=−∇φ−∂A/∂t","Gauge-dependent potentials; EM fields gauge-invariant")
E(42,42,"Gauge Invariance (U(1) in E&M)",3,"1918","Proven","A_μ→A_μ+∂_μΛ; E,B unchanged","Exact; foundation of QED")
E(43,43,"Biot-Savart Law",3,"1820","Proven","dB=(μ₀/4π) I dl×r̂/r²","Magnetostatics; exact for steady currents")
E(44,44,"Ampère's Force Law (Wire)",3,"1825","Proven","dF=I dl×B","Exact in magnetostatics")
E(45,45,"Ohm's Law",3,"1827","Proven","V=IR; J=σE","Universal in ohmic materials")
E(46,46,"Kirchhoff's Current Law (KCL)",3,"1845","Proven","ΣI_in=ΣI_out at junction","Charge conservation; exact")
E(47,47,"Kirchhoff's Voltage Law (KVL)",3,"1845","Proven","ΣV around closed loop=0","Conservative E field in lumped circuits; exact")
E(48,48,"Faraday's Law of Induction",3,"1831","Proven","ε=−dΦ_B/dt; induced EMF=−flux change","Every generator, transformer, MRI")
E(49,49,"Lenz's Law",3,"1834","Proven","Induced current opposes flux change","Consequence of energy conservation")
E(50,50,"Poynting's Theorem",3,"1884","Proven","∂u/∂t+∇·S=−J·E; S=(1/μ₀)E×B","Energy conservation in EM fields")
E(51,51,"Electromagnetic Wave Equation",3,"1865","Proven","□E=0; □B=0; c=1/√(μ₀ε₀)","Maxwell predicted EM waves; Hertz 1887")
E(52,52,"EM Stress-Energy Tensor",3,"1908","Proven","T^{μν}=(1/μ₀)[F^μ_α F^{να}+¼g^{μν}F²]","Relativistic formulation; exact")
E(53,53,"Lienard-Wiechert Potentials",3,"1898–1900","Proven","Retarded potentials for arbitrarily moving point charge","Radiation from accelerated charges")
E(54,54,"Larmor Formula (Non-rel. Radiation)",3,"1897","Proven","P=q² a²/(6πε₀ c³)","Synchrotron radiation confirmed")
E(55,55,"Liénard Formula (Relativistic Radiation)",3,"1898","Proven","P=(q²γ⁶/6πε₀c³)[a²−(v×a)²/c²]","Accelerator beam energy loss confirmed")
E(56,56,"Abraham-Lorentz Force (Radiation Reaction)",3,"1905","Proven","F_rad=(q²/6πε₀c³)d³r/dt³","Qualitatively confirmed; pathological pre-accel.")
E(57,57,"Coulomb Gauge",3,"1867","Proven","∇·A=0","Gauge choice for radiation problems")
E(58,58,"Lorenz Gauge",3,"1867","Proven","∂_μ A^μ=0","Covariant gauge; Maxwell eqs diagonalize")
E(59,59,"RC Circuit Charging",3,"19th c.","Proven","q(t)=C ε(1−e^{−t/RC}); τ=RC","Every RC circuit")
E(60,60,"RL Circuit Time Constant",3,"19th c.","Proven","I(t)=I₀ e^{−tR/L}; τ=L/R","Every RL circuit")
E(61,61,"LC Oscillation",3,"19th c.","Proven","ω₀=1/√(LC); q̈+ω₀² q=0","Radios, resonant circuits")
E(62,62,"RLC Damped Oscillation",3,"19th c.","Proven","q̈+(R/L)q̇+(1/LC)q=0; γ=R/(2L)","All RLC circuits")
E(63,63,"Skin Effect",3,"1883","Proven","δ=√(2/ωμσ); penetration depth","High-frequency conductors")
E(64,64,"Dielectric Polarization (Linear)",3,"19th c.","Proven","D=ε₀E+P=ε_r ε₀ E","Linear dielectric response confirmed")
E(65,65,"Magnetic Susceptibility",3,"19th c.","Proven","M=χ_m H; B=μ₀(H+M)=μ_r μ₀ H","Paramagnets, diamagnets, ferromagnets confirmed")

# THERMODYNAMICS (66-85)
E(66,66,"Zeroth Law of Thermodynamics",4,"1931","Proven","Thermal equilibrium is transitive; defines temperature","Every thermometer")
E(67,67,"First Law of Thermodynamics",4,"1850","Proven","dU=δQ−δW; ΔU=Q−W","Energy conservation; never violated")
E(68,68,"Second Law of Thermodynamics",4,"1850","Proven","dS_total≥0; entropy never decreases","Statistical law; no macro violation")
E(69,69,"Third Law of Thermodynamics",4,"1912","Proven","S→0 as T→0 (perfect crystal)","Confirmed; residual entropy in glasses, ice")
E(70,70,"Ideal Gas Law",4,"1834","Proven","pV=nRT=N k_B T","Limit of real gases at low P/high T")
E(71,71,"Van der Waals Equation of State",4,"1873","Proven","(p+an²/V²)(V−nb)=nRT","Real gas corrections; qualitatively correct")
E(72,72,"Kinetic Theory: Pressure",4,"1857","Proven","p=(1/3) N m ⟨v²⟩/V","Microscopic derivation of ideal gas law")
E(73,73,"Equipartition Theorem",4,"1845","Proven","⟨E⟩=f k_B T/2; C_V=(f/2)R","Confirmed at high T; quantum corrections at low T")
E(74,74,"Maxwell-Boltzmann Speed Distribution",4,"1860","Proven","f(v)=4π(m/2πk_B T)^{3/2} v² e^{−mv²/2kBT}","Molecular beams; Stern-Gerlach confirmed")
E(75,75,"Carnot Efficiency",4,"1824","Proven","η_max=1−T_c/T_h","Upper bound; all heat engines obey")
E(76,76,"Clausius-Clapeyron Relation",4,"1834","Proven","dP/dT=L/(T ΔV) for phase coexistence","Phase boundary slopes; confirmed")
E(77,77,"Gibbs Phase Rule",4,"1876","Proven","F=C−P+2","Multi-component equilibrium; confirmed")
E(78,78,"Helmholtz Free Energy",4,"1882","Proven","F=U−TS; ΔF≤0 at const T,V (spontaneous)","Legendre transform; exact")
E(79,79,"Gibbs Free Energy",4,"1876","Proven","G=H−TS; ΔG≤0 at const T,P (spontaneous)","Chemical thermodynamics workhorse")
E(80,80,"Enthalpy",4,"1875","Proven","H=U+pV; ΔH=Q_p","Constant pressure heat; exact")
E(81,81,"Maxwell Relations (Thermodynamics)",4,"1871","Proven","(∂T/∂V)_S=−(∂p/∂S)_V; (∂T/∂p)_S=(∂V/∂S)_p; (∂S/∂V)_T=(∂p/∂T)_V; (∂S/∂p)_T=−(∂V/∂T)_p","Cross-derivative equalities; exact")
E(82,82,"TdS Equations",4,"19th c.","Proven","T dS=C_V dT+T(∂p/∂T)_V dV; T dS=C_p dT−T(∂V/∂T)_p dp","General thermodynamic identities")
E(83,83,"Specific Heat Relations (C_p−C_V)",4,"19th c.","Proven","C_p−C_V=−T(∂V/∂T)_p²/(∂V/∂p)_T=TVα²/κ_T","Confirmed for all substances")
E(84,84,"Joule-Thomson Coefficient",4,"1852","Proven","μ_JT=(∂T/∂p)_H=(V/C_p)(Tα−1)","Gas liquefaction; confirmed")
E(85,85,"Entropy of Mixing",4,"19th c.","Proven","ΔS_mix=−k_B(N₁ ln x₁+N₂ ln x₂)","Ideal mixing; confirmed")

# QUANTUM MECHANICS (86-120)
E(86,86,"Planck's Blackbody Radiation Law",5,"1900","Proven","B_ν=(2hν³/c²)/(e^{hν/kT}−1)","CMB fits to 50ppm; COBE/FIRAS 1990")
E(87,87,"Wien's Displacement Law",5,"1893","Proven","λ_max T=2.898×10⁻³ m·K","All thermal radiation")
E(88,88,"Stefan-Boltzmann Law",5,"1879–84","Proven","j*=σ T⁴; σ=2π⁵k_B⁴/(15h³c²)","Confirmed; consequence of Planck")
E(89,89,"Photoelectric Effect Equation (Einstein)",5,"1905","Proven","K_max=hν−φ; photon quanta","Millikan 1916 confirmed; quantum foundation")
E(90,90,"Einstein A and B Coefficients",5,"1917","Proven","A_21/B_21=8πhν³/c³; B_12/B_21=g₂/g₁","Laser theory foundation; confirmed")
E(91,91,"Compton Scattering Formula",5,"1923","Proven","Δλ=(h/m_e c)(1−cos θ); Δλ_max≈0.00486 nm","Every Compton experiment confirmed")
E(92,92,"de Broglie Wavelength",5,"1924","Proven","λ=h/p=h/(γmv)","Davisson-Germer 1927; every electron microscope")
E(93,93,"Schrödinger Equation (Time-Dependent)",5,"1926","Proven","iℏ∂ψ/∂t=Ĥψ","Never falsified for non-relativistic QM")
E(94,94,"Time-Independent Schrödinger Equation",5,"1926","Proven","Ĥψ=Eψ","All atomic/molecular spectra")
E(95,95,"Born Rule (Probability Interpretation)",5,"1926","Proven","ρ(r,t)=|ψ(r,t)|²","All quantum measurements; never violated")
E(96,96,"Probability Current (QM)",5,"1926","Proven","j=(ℏ/2mi)(ψ*∇ψ−ψ∇ψ*); ∂ρ/∂t+∇·j=0","Continuity equation; exact")
E(97,97,"Canonical Commutation Relations",5,"1925","Proven","[x̂_i,p̂_j]=iℏδ_{ij}","Quantization postulate; exact")
E(98,98,"Heisenberg Uncertainty Principle",5,"1927","Proven","Δx·Δp≥ℏ/2; ΔE·Δt≥ℏ/2","Operator non-commutation; confirmed")
E(99,99,"Harmonic Oscillator Energy Levels (QM)",5,"1926","Proven","E_n=ℏω(n+½); â|n⟩=√n|n−1⟩, â†|n⟩=√(n+1)|n+1⟩","Molecular vibrations, trapped ions")
E(100,100,"Hydrogen Atom Energy Levels",5,"1913–26","Proven","E_n=−R_y/n²; R_y=13.605693123 eV","1S-2S to 10⁻¹⁰; QED corrections confirmed")
E(101,101,"Angular Momentum Quantization",5,"1926","Proven","L²|l,m⟩=ℏ² l(l+1); L_z|l,m⟩=ℏ m","Universally confirmed")
E(102,102,"Spin-½ Algebra (Pauli Matrices)",5,"1927","Proven","S=(ℏ/2)σ; [σ_i,σ_j]=2iε_{ijk}σ_k; {σ_i,σ_j}=2δ_{ij}","All spin-½ systems; exact")
E(103,103,"Spin-Orbit Coupling",5,"1926","Proven","H_SO=(1/2m²c²)(1/r)(dV/dr) L·S","Fine structure; nuclear shell model")
E(104,104,"Dirac Equation",5,"1928","Proven","(iℏγ^μ∂_μ−mc)ψ=0","Predicted positron; g-2 to 10⁻¹²")
E(105,105,"Klein-Gordon Equation",5,"1926","Proven","(□+m²c²/ℏ²)φ=0","Scalar particles; pions, Higgs")
E(106,106,"Fine Structure Formula (Hydrogen)",5,"1928","Proven","ΔE_FS=(R_y α²/n³)[1/(j+½)−3/(4n)]","Dirac+SO+Darwin; confirmed")
E(107,107,"Lamb Shift",5,"1947","Proven","ΔE(2S−2P)≈1057.8 MHz; QED vacuum effects","Lamb-Retherford 1947; confirmed QED")
E(108,108,"Anomalous Magnetic Moment (Electron)",7,"1948","Proven","a_e=(g−2)/2≈0.00115965218091; QED+EW+hadronic","Most precise QFT test: 10⁻¹²")
E(109,109,"Pauli Exclusion Principle",5,"1925","Proven","No two identical fermions in same quantum state; ψ antisymmetric","Periodic table; neutron stars; violation <10⁻²⁹")
E(110,110,"Spin-Statistics Theorem",5,"1939–40","Proven","Half-int spin→fermion (anticommutators); int→boson (commutators)","Relativistic QFT theorem; never violated")
E(111,111,"Fermi's Golden Rule",5,"1927","Proven","Γ_{i→f}=(2π/ℏ)|⟨f|V|i⟩|² ρ(E_f)","Transition rates; all spectroscopy")
E(112,112,"Time-Dependent Perturbation Theory (1st Order)",5,"1926","Proven","c_f(t)=−(i/ℏ)∫₀ᵗ ⟨f|V(t')|i⟩ e^{iω_fi t'} dt'","Transition amplitudes; exact to 1st order")
E(113,113,"WKB Approximation",5,"1926","Proven","ψ∼(1/√p)exp(±i∫ p dx/ℏ); Bohr-Sommerfeld quantization","Semiclassical; α-decay, tunneling")
E(114,114,"Born Approximation (Scattering)",5,"1926","Proven","f(θ,φ)=−(2m/ℏ²)(1/4π)∫ e^{−iq·r} V(r) d³r","1st-order scattering; nuclear physics")
E(115,115,"Partial Wave Expansion (Scattering)",5,"1947","Proven","f(θ)=(1/k)Σ(2l+1)e^{iδ_l} sin δ_l P_l(cos θ)","Exact scattering; phase shift analysis")
E(116,116,"Optical Theorem",5,"1951","Proven","Im f(0)=(k/4π)σ_total","Unitarity of scattering; exact")
E(117,117,"Feynman Path Integral",5,"1948","Proven","⟨x_f,t_f|x_i,t_i⟩=∫ D[x(t)] exp(iS[x]/ℏ)","Equivalent to Schrödinger/Heisenberg; QFT foundation")
E(118,118,"Von Neumann Equation",5,"1927","Proven","iℏ ∂ρ̂/∂t=[Ĥ,ρ̂]","Quantum Liouville; mixed states; exact")
E(119,119,"Ehrenfest Theorem",5,"1927","Proven","d⟨A⟩/dt=(1/iℏ)⟨[A,Ĥ]⟩+⟨∂A/∂t⟩","Quantum expectation values obey classical EOM")
E(120,120,"Bell's Inequality",5,"1964","Proven","|E(a,b)−E(a,c)|≤1+E(b,c)","Local realism ruled out at >40σ")

# RELATIVITY (121-135)
E(121,121,"Lorentz Transformations (Boost)",6,"1905","Proven","x'=γ(x−vt); t'=γ(t−vx/c²); γ=1/√(1−v²/c²)","All SR applications; confirmed to 10⁻¹⁷")
E(122,122,"Minkowski Spacetime Interval",6,"1908","Proven","ds²=−c²dt²+dx²+dy²+dz²=η_μν dx^μ dx^ν","Flat spacetime; Lorentz invariant")
E(123,123,"Time Dilation",6,"1905","Proven","Δt'=γΔt (moving clock runs slow)","Muon lifetime; GPS; Hafele-Keating 1971")
E(124,124,"Length Contraction",6,"1905","Proven","L'=L/γ (moving object contracts)","Particle physics; confirmed")
E(125,125,"Relativistic Energy-Momentum Relation",6,"1905","Proven","E²=(pc)²+(mc²)²; E=γmc²; p=γmv","Every accelerator; confirmed")
E(126,126,"Mass-Energy Equivalence",6,"1905","Proven","E=mc²; ΔE=Δm c²","Nuclear reactions; particle-antiparticle annihilation")
E(127,127,"Relativistic Doppler Effect",6,"1905","Proven","f_obs=f_s√[(1+β)/(1−β)] (longitudinal); transverse: f_obs=γf_s","Ives-Stilwell 1938; confirmed")
E(128,128,"Relativistic Velocity Addition",6,"1905","Proven","u=(u'+v)/(1+u'v/c²)","Never exceeds c; confirmed")
E(129,129,"Einstein Field Equations (GR)",6,"1915","Proven","G_μν+Λg_μν=(8πG/c⁴)T_μν","All GR tests; GPS, LIGO, EHT; confirmed")
E(130,130,"Einstein-Hilbert Action",6,"1915","Proven","S=(c⁴/16πG)∫ d⁴x√(−g)(R−2Λ)+S_matter","Action principle for GR; exact")
E(131,131,"Schwarzschild Metric",6,"1916","Proven","ds²=−(1−r_s/r)c²dt²+dr²/(1−r_s/r)+r²dΩ²; r_s=2GM/c²","Non-rotating BH; gravitational redshift confirmed")
E(132,132,"Kerr Metric (Rotating Black Hole)",6,"1963","Proven","Rotating axisymmetric vacuum solution; a=J/Mc","Frame-dragging; EHT imaging; confirmed")
E(133,133,"FLRW Metric",6,"1922–35","Proven","ds²=−c²dt²+a²(t)[dr²/(1−kr²)+r²dΩ²]","Homogeneous isotropic cosmology; ΛCDM found.")
E(134,134,"Geodesic Equation",6,"1915","Proven","d²x^μ/dτ²+Γ^μ_αβ(dx^α/dτ)(dx^β/dτ)=0","Free-fall in curved spacetime; exact")
E(135,135,"Gravitational Wave (TT Gauge)",6,"1918","Proven","h_μν^{TT} has only h_+,h_× spatial transverse components","LIGO; PSR B1913+16 energy loss; confirmed")

# BLACK HOLE THERMODYNAMICS
E(136,136,"Bekenstein-Hawking Black Hole Entropy",6,"1972–74","Proven","S_BH=k_B A/4ℓ_P²=k_B c³A/(4Gℏ)","Horizon area/4; 4 laws map to thermodynamics")
E(137,137,"Hawking Temperature",6,"1974","Proven","T_H=ℏc³/(8πGMk_B); T_H(M⊙)≈6.2×10⁻⁸ K","Hawking radiation; analog gravity confirmed")
E(138,138,"Black Hole Area Theorem (Hawking 1971)",6,"1971","Proven","dA/dt≥0; horizon area never decreases","BH mechanics 2nd law; LIGO ringdown ~97% conf.")

# QFT / STANDARD MODEL (139-158)
E(139,139,"Standard Model Lagrangian (Full)",7,"1973","Proven","ℒ_SM=ℒ_gauge+ℒ_fermion+ℒ_Higgs+ℒ_Yukawa; SU(3)×SU(2)×U(1)","Most precise physical theory; all LHC data matches")
E(140,140,"Yang-Mills Field Strength",7,"1954","Proven","F_μν^a=∂_μA_ν^a−∂_νA_μ^a+gf^{abc}A_μ^bA_ν^c","Non-abelian gauge; QCD+EW foundation")
E(141,141,"QED Lagrangian",7,"1948","Proven","ℒ_QED=ψ̄(i∂̸−m)ψ−eψ̄γ^μψA_μ−¼F_μνF^{μν}","g-2 to 10⁻¹²; most precise theory")
E(142,142,"QCD Lagrangian",7,"1973","Proven","ℒ_QCD=Σψ̄_f(iD̸−m_f)ψ_f−¼G_a^{μν}G^a_{μν}","Asymptotic freedom; confinement; 0 falsifications")
E(143,143,"Electroweak Symmetry Breaking",7,"1967–68","Proven","SU(2)_L×U(1)_Y→U(1)_EM via Higgs VEV","W,Z masses predicted→confirmed")
E(144,144,"QCD Beta Function (1-loop)",7,"1973","Proven","β(α_s)=−(b₀/2π)α_s²; b₀=11−2n_f/3","Asymptotic freedom; α_s running over 4 decades")
E(145,145,"DGLAP Evolution Equations",7,"1972–77","Proven","∂q/∂lnQ²=(α_s/2π)∫(dz/z)[P_qq q+P_qg g]; gluon evolution similarly","HERA→LHC scaling confirmed")
E(146,146,"CKM Matrix (Quark Mixing)",7,"1973","Proven","3×3 unitary; 4 parameters (3 angles+1 CP phase)","All flavor physics; CP violation confirmed")
E(147,147,"PMNS Matrix (Neutrino Mixing)",7,"1962","Proven","3×3 leptonic mixing; θ₁₂≈33°,θ₂₃≈45°,θ₁₃≈8.5°","Neutrino oscillations; confirmed")
E(148,148,"Gell-Mann–Oakes–Renner Relation",7,"1968","Proven","m_π²=−(m_u+m_d)⟨ψ̄ψ⟩/f_π²","Chiral symmetry breaking; pion mass from quark masses")
E(149,149,"Higgs Mechanism (Mass Generation)",7,"1964","Proven","Scalar VEV v=246 GeV→W,Z masses; fermion masses via Yukawa","Higgs boson 2012; m_H=125.25 GeV")
E(150,150,"Weinberg Angle",7,"1967","Proven","sin²θ_W=1−M_W²/M_Z²; 0.23121±0.00004","EW precision parameter")
E(151,151,"Faddeev-Popov Gauge Fixing + Ghosts",7,"1967","Proven","Anticommuting scalar ghosts cancel unphysical gluon d.o.f.","Perturbative unitarity in non-abelian theories")
E(152,152,"BRST Symmetry",7,"1975","Proven","Residual global symmetry after gauge fixing","Exact; ensures unitarity and renormalizability")
E(153,153,"Running Coupling (RGE, General)",7,"1950s","Proven","μ dg/dμ=β(g); μ d m/dμ=γ_m m","Renormalization group; all QFT")
E(154,154,"Fermi's Theory (4-Fermion, Low-Energy EW)",7,"1934","Proven","ℒ_eff=−(G_F/√2) J_μ^{CC} J^{CC†μ}","Low-energy limit of SM; muon decay; confirmed")
E(155,155,"Pati-Salam Model (SU(4)×SU(2)×SU(2))",7,"1974","Proposed","Partial unification with lepton as 4th color","Not proven; historically important")
E(156,156,"Grand Unified Theories (GUTs)",7,"1974–","Proposed","SU(5), SO(10), E₆ unification at ~10¹⁶ GeV","Not confirmed; proton decay >10³⁴ yr")
E(157,157,"Axion (Peccei-Quinn Solution to Strong CP)",7,"1977","Proposed","a→γγ; m_a~μeV−meV","Strong CP solution candidate; searches ongoing")
E(158,158,"Muon g−2 Anomaly",7,"2021","Tension","a_μ(exp)−a_μ(SM)=251(59)×10⁻¹¹ (4.2σ)","Possible new physics; lattice vs R-ratio dispute")

# COSMOLOGY (159-175)
E(159,159,"First Friedmann Equation",8,"1922","Proven","H²=(ȧ/a)²=8πGρ/3−kc²/a²+Λc²/3; H₀=67.4 km/s/Mpc","ΛCDM; CMB, SNe, BAO consistent")
E(160,160,"Second Friedmann Equation",8,"1922","Proven","ä/a=−4πG(ρ+3p/c²)/3+Λc²/3","Cosmic acceleration from Λ; confirmed")
E(161,161,"Cosmological Fluid Equation",8,"1922","Proven","ρ̇+3H(ρ+p/c²)=0","Stress-energy conservation; exact")
E(162,162,"Redshift Relation",8,"1929","Proven","1+z=a₀/a(t); λ_obs=λ_emit(1+z)","Hubble law; all observational cosmology")
E(163,163,"Hubble-Lemaître Law",8,"1929","Proven","v=H₀ d (low z)","Hubble 1929; SN, CMB confirmed")
E(164,164,"CMB Blackbody Spectrum",8,"1965","Proven","T₀=2.72548±0.00057 K; ΔT/T₀<50 ppm","COBE/FIRAS; Planck 2018")
E(165,165,"BBN Primordial Element Abundances",8,"1948–66","Proven","Y_p=0.24709±0.00025; D/H=(2.527±0.030)×10⁻⁵","All except ⁷Li (tension) match BBN+CMB")
E(166,166,"Sound Horizon at Recombination",8,"1970","Proven","r_s≈147 Mpc (comoving); BAO standard ruler","SDSS/BOSS/DESI; confirmed")
E(167,167,"Sachs-Wolfe Effect (CMB)",8,"1967","Proven","ΔT/T=−Φ/(3c²) at large angular scales","CMB gravitational redshift; confirmed")
E(168,168,"Dark Energy Equation of State",8,"1998","Proven","w=p/ρc²=−1.03±0.03","Consistent with cosmological constant Λ")
E(169,169,"Deceleration Parameter",8,"1970","Proven","q₀=−äa/ȧ²=−0.53±0.02","Universe accelerating; SNe Nobel 2011")
E(170,170,"Matter Power Spectrum",8,"1990s","Proven","P(k)~k^{n_s}; n_s=0.9649±0.0042","Planck 2018; primordial fluctuations")
E(171,171,"Cosmic Distance Ladder Relations",8,"20th c.","Proven","d_L=(1+z)χ; μ=5log₁₀(d_L/10pc)","SNe, Cepheids, TRGB; confirmed")
E(172,172,"Inflation (Slow-Roll)",8,"1981","Proposed","ε=−Ḣ/H²≪1; η≪1 scalar spectral index","Fits data; no direct inflaton detection")
E(173,173,"Hubble Tension",8,"2020s","Tension","H₀(CMB)=67.4±0.5 vs H₀(local)=73.0±1.0 (5σ)","New physics or systematics?")
E(174,174,"S₈ Tension",8,"2020s","Tension","σ₈(Ω_m/0.3)^{0.5}=0.832±0.013 (CMB) vs ~0.76 (WL)","Clustering lower than ΛCDM predicts")
E(175,175,"Age of the Universe",8,"2018","Proven","t₀=13.797±0.023 Gyr (Planck 2018)","Consistent with oldest globular clusters, WDs")

# FLUID DYNAMICS (176-190)
E(176,176,"Navier-Stokes Equation (Incompressible)",9,"1822–45","Proven","∂v/∂t+(v·∇)v=−(1/ρ)∇p+ν∇²v+g; ∇·v=0","All Newtonian fluids; empirically perfect")
E(177,177,"Continuity Equation (Fluid)",9,"1757","Proven","∂ρ/∂t+∇·(ρv)=0","Mass conservation; exact")
E(178,178,"Euler Equation (Inviscid)",9,"1757","Proven","∂v/∂t+(v·∇)v=−(1/ρ)∇p+g (μ=0 limit)","Inviscid flow; exact limit of N-S")
E(179,179,"Bernoulli's Equation",9,"1738","Proven","p+½ρv²+ρgz=constant (steady, incompressible, inviscid)","Confirmed in wind tunnels, pipe flow, flight")
E(180,180,"Stokes Law (Drag on Sphere)",9,"1851","Proven","F_d=6πμRv (Re≪1)","Creeping flow; Millikan oil-drop; confirmed")
E(181,181,"Poiseuille Flow (Hagen-Poiseuille)",9,"1840","Proven","Q=πGR⁴/(8μ); v_z(r)=(G/4μ)(R²−r²)","Laminar pipe flow; viscometry")
E(182,182,"Reynolds Number",9,"1883","Proven","Re=ρUL/μ; transition at Re~2300 (pipe)","Universally confirmed scaling")
E(183,183,"Kolmogorov Energy Spectrum",9,"1941","Proven","E(k)=C_K ε^{2/3}k^{−5/3}; C_K≈1.5","Turbulence; ~5 decades confirmed")
E(184,184,"Froude Number",9,"19th c.","Proven","Fr=v/√(gL); wave/gravity scaling","Open channels; ship design")
E(185,185,"Mach Number",9,"1887","Proven","Ma=v/c_s; compressibility measure","Aerodynamics; shock waves")
E(186,186,"Kutta-Joukowski Theorem (Lift)",9,"1906","Proven","L'=ρvΓ (lift per unit span)","Airfoil lift confirmed")
E(187,187,"Torricelli's Law (Efflux Speed)",9,"1643","Proven","v=√(2gh); speed of fluid from orifice","Confirmed; energy conservation")
E(188,188,"Archimedes' Principle",9,"~250 BCE","Proven","F_b=ρ_fluid V_displaced g","Buoyancy; confirmed")
E(189,189,"Surface Tension (Young-Laplace)",9,"1805","Proven","Δp=2γ/R (spherical); Δp=γ(1/R₁+1/R₂)","Capillarity; confirmed")
E(190,190,"Kelvin-Helmholtz Instability Condition",9,"1871","Proven","Instability when (ρ₁ρ₂/ρ₁+ρ₂)(v₁−v₂)²>2√(ρ₁ρ₂)gγ","Shear flow instability; clouds, ocean waves")

# OPTICS (191-210)
E(191,191,"Snell's Law of Refraction",10,"1621","Proven","n₁ sinθ₁=n₂ sinθ₂","Fermat's principle; exact for isotropic media")
E(192,192,"Thin Lens Equation",10,"17th c.","Proven","1/f=1/d_o+1/d_i","Paraxial imaging; confirmed")
E(193,193,"Lens Maker's Formula",10,"17th c.","Proven","1/f=(n−1)(1/R₁−1/R₂)","Thin lens; paraxial; confirmed")
E(194,194,"Magnification (Geometric Optics)",10,"17th c.","Proven","M=−d_i/d_o=h_i/h_o","Geometric optics; exact")
E(195,195,"Scalar Wave Equation (d'Alembert)",10,"1747","Proven","∂²u/∂t²=c²∇²u","All wave phenomena; exact")
E(196,196,"Young's Double-Slit Interference",10,"1801","Proven","Δy=λL/d (fringe spacing); d sinθ=mλ (maxima)","Wave nature of light confirmed")
E(197,197,"Single-Slit Diffraction",10,"1835","Proven","I(θ)=I₀[sin(β/2)/(β/2)]²; β=2πa sinθ/λ","All diffraction; confirmed")
E(198,198,"Grating Equation",10,"1821","Proven","d(sinθ_i+sinθ_m)=mλ","Diffraction gratings; spectroscopy")
E(199,199,"Bragg's Law (X-ray Diffraction)",10,"1913","Proven","nλ=2d sinθ","All crystal structures solved")
E(200,200,"Fresnel Equations (Amplitude Reflection/Transmission)",10,"1823","Proven","r_s=(n₁cosθ_i−n₂cosθ_t)/(n₁cosθ_i+n₂cosθ_t); etc.","All dielectric interfaces; confirmed")
E(201,201,"Brewster's Angle",10,"1815","Proven","θ_B=arctan(n₂/n₁); reflected p-pol vanishes","Polarization; confirmed")
E(202,202,"Malus's Law",10,"1809","Proven","I=I₀ cos²θ","Polarizer transmission; confirmed")
E(203,203,"Rayleigh Criterion (Resolution Limit)",10,"1879","Proven","θ_min=1.22λ/D","Diffraction limit; telescopes, microscopes")
E(204,204,"Abbe Sine Condition",10,"1873","Proven","n y sinθ=n' y' sinθ'","Coma-free imaging condition; confirmed")
E(205,205,"Numerical Aperture",10,"1873","Proven","NA=n sinθ; resolution d=λ/(2 NA)","Microscopy; confirmed")
E(206,206,"Fermat's Principle of Least Time",10,"1662","Proven","δ∫ n ds=0; light path minimizes optical path length","All geometric optics; exact")
E(207,207,"Huygens-Fresnel Principle",10,"1678/1818","Proven","Every point on wavefront = source of spherical wavelets","All diffraction; confirmed")
E(208,208,"Fabry-Pérot Etalon Transmission",10,"1899","Proven","T=T_max/[1+(2F/π)² sin²(δ/2)]","High-resolution spectroscopy")
E(209,209,"Critical Angle (Total Internal Reflection)",10,"17th c.","Proven","θ_c=arcsin(n₂/n₁)","Fiber optics; confirmed")
E(210,210,"Fraunhofer vs Fresnel Diffraction Condition",10,"19th c.","Proven","Fresnel number F=a²/λz; F≪1→Fraunhofer; F≫1→Fresnel","Confirmed")

# ACOUSTICS (211-217)
E(211,211,"Speed of Sound",11,"17th c.","Proven","c=√(K/ρ); c_air=√(γRT/M)≈331.3+0.606·T_°C m/s","All acoustic media; precise")
E(212,212,"Doppler Effect (Sound)",11,"1842","Proven","f'=f(c±v_o)/(c∓v_s)","All moving sources/observers")
E(213,213,"Standing Waves (String/Column)",11,"18th c.","Proven","λ_n=2L/n (fixed-fixed/open-open); λ_n=4L/n (fixed-free)","Musical instruments; confirmed")
E(214,214,"Decibel Scale (SPL)",11,"1924","Proven","L_p=10 log₁₀(p²/p₀²) dB; p₀=20 μPa","Sound pressure reference; universal")
E(215,215,"Shock Wave Rankine-Hugoniot Relations",11,"1887","Proven","Conservation eqs across shock: ρ₁v₁=ρ₂v₂; p₁+ρ₁v₁²=p₂+ρ₂v₂²; etc.","Supersonic flow; confirmed")
E(216,216,"Beat Frequency",11,"18th c.","Proven","f_beat=|f₁−f₂|","Superposition; confirmed")
E(217,217,"Helmholtz Resonator Frequency",11,"1860","Proven","f=(c/2π)√(A/VL_eff)","Bottle resonance; confirmed")

# CONDENSED MATTER (218-240)
E(218,218,"Drude Model (Electrical Conductivity)",12,"1900","Proven","σ=n e²τ/m; J=σE","Classical; qualitatively correct; quantum corrections")
E(219,219,"Bloch's Theorem",12,"1928","Proven","ψ_k(r)=e^{ik·r} u_k(r); u_k periodic","Band theory foundation; confirmed")
E(220,220,"Kronig-Penney Model (1D Band Structure)",12,"1931","Proven","cos ka=cos αa+(P/αa)sin αa","1D crystal; bands naturally emerge")
E(221,221,"Fermi-Dirac Distribution",12,"1926","Proven","f(E)=1/[e^{(E−μ)/k_B T}+1]","Fermion occupancy; all solid-state devices")
E(222,222,"Free Electron Density of States",12,"1928","Proven","g(E)=(1/2π²)(2m/ℏ²)^{3/2}√E","3D electron gas; confirmed")
E(223,223,"Sommerfeld Model (Electron Heat Capacity)",12,"1928","Proven","C_V=(π²/2)n k_B(k_B T/E_F)","Metals; linear T contribution confirmed")
E(224,224,"BCS Theory (Superconductivity)",12,"1957","Proven","T_c=1.13Θ_D e^{−1/N(0)V}; Δ(T); Cooper pairs","All conventional superconductors")
E(225,225,"BCS Gap Equation at T=0",12,"1957","Proven","Δ(0)=1.76 k_B T_c","Confirmed by tunneling spectroscopy")
E(226,226,"London Equations (Perfect Diamagnetism)",12,"1935","Proven","∂J_s/∂t=(n_s e²/m)E; ∇×J_s=−(n_s e²/m)B","Meissner effect; confirmed")
E(227,227,"Josephson Effects (DC + AC)",12,"1962","Proven","I=I_c sin φ (DC); dφ/dt=(2e/ℏ)V=(2π/Φ₀)V (AC)","Voltage standard; SQUIDs; confirmed")
E(228,228,"Curie's Law (Paramagnetism)",12,"1895","Proven","χ=C/T; C=Nμ²/(3k_B)","Paramagnetic susceptibility; confirmed")
E(229,229,"Curie-Weiss Law (Ferromagnetism)",12,"1907","Proven","χ=C/(T−T_c) above Curie point","Ferromagnetic transition; confirmed")
E(230,230,"Heisenberg Exchange Interaction",12,"1928","Proven","H=−J Σ_{⟨ij⟩} S_i·S_j","Origin of ferromagnetism; confirmed")
E(231,231,"Magnetic Hysteresis Loop",12,"1890","Proven","B−H loop; remanence B_r, coercivity H_c","All permanent magnets")
E(232,232,"Einstein Relation (Diffusion)",12,"1905","Proven","D=μ k_B T/e","Brownian motion; ionic conduction; exact")
E(233,233,"Seebeck Effect (Thermoelectricity)",12,"1821","Proven","ΔV=S ΔT; S=−(π²k_B²T/3e)(d ln σ/dE)_{E=μ}","Thermocouples; confirmed")
E(234,234,"Hall Effect",12,"1879","Proven","V_H=(I B)/(n e d); R_H=1/(n e)","Carrier density; confirmed")
E(235,235,"Quantum Hall Effect (Integer)",12,"1980","Proven","R_H=h/(ν e²); ν integer; exact quantization","Resistance standard; 10⁻⁹ precision")
E(236,236,"Wiedemann-Franz Law",12,"1853","Proven","κ/(σT)=L; L=(π²/3)(k_B/e)²≈2.44×10⁻⁸ WΩ/K²","Metals; confirmed")
E(237,237,"Debye Model (Lattice Heat Capacity)",12,"1912","Proven","C_V≈(12π⁴/5) N k_B (T/Θ_D)³ for T≪Θ_D","Phonon specific heat; confirmed")
E(238,238,"Mott Insulator Transition",12,"1949","Proven","U/t≫W→Mott insulating gap; metal-insulator transition","Strongly correlated systems")
E(239,239,"Density Functional Theory (Kohn-Sham Equations)",12,"1964–65","Proven","(−½∇²+v_eff(r))φ_i(r)=ε_i φ_i(r)","All modern materials computation; confirmed")
E(240,240,"Landau Fermi Liquid Theory",12,"1956","Proven","Quasiparticles with renormalized mass m*/m; same quantum numbers","Normal metals; confirmed")

# NUCLEAR PHYSICS (241-250)
E(241,241,"Radioactive Decay Law",13,"1902","Proven","N(t)=N₀ e^{−λt}; T_{1/2}=ln 2/λ; τ=1/λ","All radioactive isotopes; exact")
E(242,242,"Bethe-Weizsäcker (Semi-Empirical) Mass Formula",13,"1935","Proven","B=a_vA−a_sA^{2/3}−a_cZ²/A^{1/3}−a_a(N−Z)²/A+δ(A,Z)","Nuclear binding energies to <1% avg")
E(243,243,"Geiger-Nuttall Law (α-Decay)",13,"1911","Proven","log T_{1/2}=A+B/√E_α","Quantum tunneling explained")
E(244,244,"Nuclear Shell Model (Magic Numbers)",13,"1949","Proven","Magic no: 2,8,20,28,50,82,126; spin-orbit coupling","Nuclear energy levels confirmed")
E(245,245,"Q-Value of Nuclear Reaction",13,"1930s","Proven","Q=(m_initial−m_final)c²","All nuclear reactions; exact")
E(246,246,"Neutrino Oscillation Probability",13,"1957","Proven","P(ν_α→ν_β)=sin²(2θ) sin²(Δm² L/4E)","Super-K, SNO, KamLAND, Daya Bay")
E(247,247,"Four-Factor Formula (Nuclear Reactor)",13,"1940s","Proven","k_eff=η ε p f; criticality when k_eff=1","Nuclear chain reaction")
E(248,248,"Rutherford Scattering Cross-Section",13,"1911","Proven","dσ/dΩ=(Z₁Z₂e²/16πε₀E)² csc⁴(θ/2)","Nuclear size discovered; confirmed")
E(249,249,"Mössbauer Effect (Recoilless γ Emission)",13,"1958","Proven","Fraction f=exp(−k²⟨x²⟩)","Recoil-free fraction; Pound-Rebka-GR; confirmed")
E(250,250,"Breit-Wigner Resonance (Nuclear Reactions)",13,"1936","Proven","σ(E)=πƛ² g (Γ_a Γ_b)/[(E−E_R)²+Γ²/4]","Resonance scattering; compound nucleus")

# ASTROPHYSICS (251-268)
E(251,251,"Lane-Emden Equation (Polytropic Stars)",14,"1870","Proven","(1/ξ²)d(ξ² dθ/dξ)/dξ=−θ^n","Stellar polytropic models; confirmed")
E(252,252,"Eddington Luminosity Limit",14,"1921","Proven","L_Edd=4πGM m_p c/σ_T≈1.3×10³¹(M/M⊙) W","Radiation pressure balance; confirmed")
E(253,253,"Chandrasekhar Limit (White Dwarf)",14,"1931","Proven","M_Ch≈1.44 M⊙ (electron degeneracy pressure)","White dwarf mass limit; confirmed")
E(254,254,"TOV Limit (Neutron Star Maximum Mass)",14,"1939","Proven","M_max≈2−3 M⊙ (equation of state dependent)","GW170817; pulsar timing; confirmed")
E(255,255,"Hertzsprung-Russell Diagram + Main Sequence",14,"1910","Proven","L∝M^{3.5} (MS, M>0.5M⊙); stellar radii, T_eff","All stars; confirmed")
E(256,256,"Mass-Luminosity Relation",14,"1924","Proven","L/L⊙≈(M/M⊙)^{3.5} (MS, intermediate mass)","Binary systems; confirmed")
E(257,257,"Virial Theorem (Astrophysics)",14,"1870","Proven","2⟨T⟩+⟨U⟩=0 for gravitational systems","Galaxy clusters; dark matter evidence")
E(258,258,"Jeans Instability Criterion (Star Formation)",14,"1902","Proven","λ_J=c_s√(π/Gρ); M_J∝c_s³/√(G³ρ)","Gravitational collapse condition; confirmed")
E(259,259,"Schwarzschild Criterion (Convection)",14,"1906","Proven","|dT/dr|_rad>|dT/dr|_ad→convective instability","Stellar convection zones; confirmed")
E(260,260,"pp Chain Energy Release",14,"1939","Proven","4p→⁴He+2e⁺+2ν_e+26.73 MeV","Solar neutrino flux matches (2/3 deficit→oscillation)")
E(261,261,"CNO Cycle (Massive Stars)",14,"1938","Proven","C, N, O catalytic H fusion; dominant above ~1.3 M⊙","Solar neutrinos confirm ~1% CNO")
E(262,262,"Triple-Alpha Process (Helium Burning)",14,"1952","Proven","3 ⁴He→¹²C+7.65 MeV (Hoyle resonance at 7.65 MeV)","Carbon production in red giants; confirmed")
E(263,263,"Core-Collapse Supernova Mechanism",14,"1960s","Proven","Fe core infall→neutrino burst→explosion (delayed neutrino mechanism)","SN 1987A neutrinos detected; confirmed")
E(264,264,"Type Ia Supernova (Standardizable Candle)",14,"1990s","Proven","Chandrasekhar mass WD thermonuclear detonation; Phillips rel.","Dark energy discovery; confirmed")
E(265,265,"Neutron Star Equation of State (Various)",14,"20th c.","Proven","p(ρ) from nuclear matter theory; constraints from NS masses","GW170817 tidal deformability; confirmed")
E(266,266,"Oppenheimer-Snyder Collapse (BH Formation)",14,"1939","Proven","Dust ball collapse→BH; event horizon forms","First BH formation model; confirmed")
E(267,267,"Pulsar Spin-Down",14,"1968","Proven","Ė=−I ω ω̇; B_dipole≈3.2×10¹⁹√(P Ṗ) G","Magnetic braking; all pulsars")
E(268,268,"Olbers' Paradox Resolution",14,"1826","Proven","Dark night sky→finite age+expanding universe","Cosmological principle consequence")

# PLASMA PHYSICS (269-276)
E(269,269,"Debye Length (Plasma Screening)",15,"1923","Proven","λ_D=√(ε₀ k_B T/(n e²))","All plasmas; confirmed")
E(270,270,"Plasma Frequency",15,"1929","Proven","ω_p=√(n e²/(ε₀ m_e))≈56.4√n (rad/s)","Ionospheric reflection; confirmed")
E(271,271,"Alfvén Wave Speed",15,"1942","Proven","v_A=B₀/√(μ₀ρ)","MHD waves; solar wind, fusion; confirmed")
E(272,272,"MHD Induction Equation",15,"1940s","Proven","∂B/∂t=∇×(v×B)+η∇²B","Magnetic field evolution; dynamo theory")
E(273,273,"Saha Ionization Equation",15,"1920","Proven","n_{i+1}n_e/n_i=(2/λ³_deB)(U_{i+1}/U_i)e^{−χ/(k_B T)}","Ionization equilibrium; stellar atmospheres")
E(274,274,"Gyro-frequency (Larmor Frequency)",15,"1897","Proven","ω_c=qB/m; r_L=v_⊥/ω_c","Particle motion in B; confirmed")
E(275,275,"Beta Parameter (Plasma Confinement)",15,"1950s","Proven","β=2μ₀ p/B²","Plasma pressure/magnetic pressure; fusion")
E(276,276,"Lawson Criterion (Fusion Ignition)",15,"1957","Proven","n T τ_E>3×10²¹ keV·s/m³ (D-T)","Fusion break-even condition; not yet achieved")

# MATHEMATICAL PHYSICS (277-295)
E(277,277,"Noether's Theorem",16,"1918","Proven","Continuous symmetry ⇔ conserved current/charge","Mathematical theorem; unfalsifiable")
E(278,278,"Stokes' Theorem",16,"1854","Proven","∫_S (∇×F)·dS=∮_C F·dl","Vector calculus; exact")
E(279,279,"Gauss's Divergence Theorem",16,"1813","Proven","∫_V ∇·F dV=∮_S F·dS","Vector calculus; exact")
E(280,280,"Green's Theorem (2D)",16,"1828","Proven","∬(∂Q/∂x−∂P/∂y)dxdy=∮ Pdx+Qdy","Special case of Stokes; exact")
E(281,281,"Fourier Transform",16,"1822","Proven","F(k)=∫ f(x)e^{−ikx}dx; f(x)=(1/2π)∫ F(k)e^{ikx}dk","All signal processing; exact")
E(282,282,"Laplace's Equation",16,"1782","Proven","∇²φ=0; harmonic functions","Potential theory: gravity, E&M, fluid")
E(283,283,"Poisson's Equation",16,"1813","Proven","∇²φ=−f(x); fundamental PDE of physics","Gravity, E&M; exact")
E(284,284,"Bessel's Equation",16,"1824","Proven","x² y''+x y'+(x²−n²)y=0","Cylindrical symmetry; exact")
E(285,285,"Legendre's Equation",16,"1785","Proven","(1−x²)y''−2xy'+n(n+1)y=0","Spherical symmetry; P_l(cosθ)")
E(286,286,"Hermite's Equation",16,"1864","Proven","y''−2xy'+2ny=0","Harmonic oscillator wavefunctions")
E(287,287,"Associated Legendre Equation",16,"19th c.","Proven","(1−x²)y''−2xy'+[n(n+1)−m²/(1−x²)]y=0","P_l^m; spherical harmonics; confirmed")
E(288,288,"Chebyshev Polynomials",16,"1853","Proven","T_n(cosθ)=cos(nθ); orthogonality","Approximation theory")
E(289,289,"Laguerre Polynomials",16,"19th c.","Proven","x y''+(1−x)y'+n y=0","Hydrogen radial wavefunction")
E(290,290,"Spherical Harmonics (Y_l^m)",16,"19th c.","Proven","Y_l^m(θ,φ)=√((2l+1)(l−m)!/4π(l+m)!) P_l^m(cosθ) e^{imφ}","Eigenfunctions of L², L_z")
E(291,291,"Gamma Function",16,"1729","Proven","Γ(z)=∫₀^∞ t^{z−1}e^{−t}dt; Γ(n+1)=n!","Factorial generalization; exact")
E(292,292,"Error Function",16,"19th c.","Proven","erf(x)=(2/√π)∫₀^x e^{−t²}dt","Diffusion, statistics; exact")
E(293,293,"Delta Function (Dirac)",16,"1927","Proven","∫ δ(x−a)f(x)dx=f(a); ∫ δ(x)dx=1","Distribution; Green's functions")
E(294,294,"Eigenvalue Equation",16,"19th c.","Proven","Âv=λv","All of QM, vibrations, linear systems; exact")
E(295,295,"Separation of Variables Method",16,"1750","Proven","ψ(x,y,z)=X(x)Y(y)Z(z); decouples PDEs","Method; exact when symmetry permits")

# STATISTICAL MECHANICS (296-308)
E(296,296,"Boltzmann Distribution",17,"1877","Proven","p_i=g_i e^{−βE_i}/Z; β=1/k_B T","Thermal equilibrium; all stat mech")
E(297,297,"Canonical Partition Function",17,"1902","Proven","Z=Σ g_i e^{−βE_i}; F=−k_B T ln Z","All thermodynamics from Z; exact")
E(298,298,"Grand Canonical Partition Function",17,"1902","Proven","Ξ=Σ_{N} Σ_{E} e^{−β(E−μN)}; Ω=−k_B T ln Ξ","Open systems; variable particle number")
E(299,299,"Boltzmann Entropy Formula",17,"1877","Proven","S=k_B ln Ω","Microstate counting; exact")
E(300,300,"Gibbs Entropy Formula",17,"1902","Proven","S=−k_B Σ p_i ln p_i","Generalized; exact")
E(301,301,"Fluctuation-Dissipation Theorem",17,"1951","Proven","⟨x²⟩_ω=(2k_B T/ω) Im χ(ω)","Linear response; confirmed")
E(302,302,"Einstein-Smoluchowski Relation (Diffusion)",17,"1905","Proven","⟨x²⟩=2Dt; D=μ k_B T","Brownian motion; confirmed")
E(303,303,"Jarzynski Equality",17,"1997","Proven","⟨e^{−W/k_B T}⟩=e^{−ΔF/k_B T}","Non-equilibrium work; exact")
E(304,304,"Crooks Fluctuation Theorem",17,"1999","Proven","P_F(W)/P_R(−W)=e^{(W−ΔF)/k_B T}","Single-molecule; confirmed")
E(305,305,"Ising Model (1D/2D Exact Solution)",17,"1925/1944","Proven","2D Onsager solution: T_c=2.269 J/k_B","Phase transitions; confirmed")
E(306,306,"Central Limit Theorem (Statistical)",17,"1901","Proven","(1/n)Σ X_i → N(μ,σ²/n)","Foundational; exact")
E(307,307,"Bose-Einstein Condensation (T_c)",17,"1925","Proven","T_c=(2πℏ²/m k_B)(n/ζ(3/2))^{2/3}","Rubidium BEC 1995; confirmed")
E(308,308,"Kramers-Kronig Relations (Dispersion)",17,"1926–27","Proven","Re χ(ω)=(1/π) P∫ Im χ(ω')/(ω'−ω)dω'","Causality; exact")

# CONTINUUM MECHANICS (309-320)
E(309,309,"Cauchy Stress Principle",18,"1822","Proven","t=σ·n; traction vector=stress tensor·normal","Foundation of continuum; exact")
E(310,310,"Generalized Hooke's Law (Linear Elasticity)",18,"19th c.","Proven","σ_{ij}=C_{ijkl} ε_{kl}; 21 independent elastic constants","All elastic solids; confirmed")
E(311,311,"Infinitesimal Strain Tensor",18,"19th c.","Proven","ε_{ij}=(1/2)(∂_j u_i+∂_i u_j)","Small deformations; exact in limit")
E(312,312,"Young's Modulus / Elastic Modulus",18,"1807","Proven","E=σ/ε (uniaxial); stress-strain ratio","Tensile testing; confirmed")
E(313,313,"Shear Modulus",18,"19th c.","Proven","G=τ/γ; G=E/[2(1+ν)] (isotropic)","Torsion testing; confirmed")
E(314,314,"Bulk Modulus",18,"19th c.","Proven","K=−V dp/dV; K=E/[3(1−2ν)] (isotropic)","Hydrostatic compression")
E(315,315,"Poisson's Ratio",18,"1827","Proven","ν=−ε_transvers/ε_axial; −1<ν<0.5","All materials; confirmed")
E(316,316,"Euler-Bernoulli Beam Equation",18,"1750","Proven","EI d⁴w/dx⁴=q(x); deflection","Structural engineering; confirmed")
E(317,317,"Timoshenko Beam Theory",18,"1921","Proven","Shear deformation included; more accurate for short beams","Confirmed; higher-order corrections")
E(318,318,"Elastic Wave Speeds (P and S waves)",18,"19th c.","Proven","v_P=√((K+4G/3)/ρ); v_S=√(G/ρ)","Seismology; confirmed")
E(319,319,"Creep / Viscoelastic Maxwell Model",18,"1867","Proven","dε/dt=(1/E) dσ/dt + σ/η","Polymer, metal creep; qualitative")
E(320,320,"Plastic Yield (Von Mises Criterion)",18,"1913","Proven","σ_v=√(½[(σ₁−σ₂)²+(σ₂−σ₃)²+(σ₃−σ₁)²])≥σ_y","Ductile failure; confirmed")

# INFORMATION THEORY (321-326)
E(321,321,"Shannon Entropy",19,"1948","Proven","H=−Σ p_i log₂ p_i (bits)","Information theory; exact")
E(322,322,"Shannon-Hartley Channel Capacity",19,"1948","Proven","C=B log₂(1+S/N)","All digital communication; exact")
E(323,323,"Nyquist-Shannon Sampling Theorem",19,"1949","Proven","f_s≥2 f_max to perfectly reconstruct","DSP everywhere")
E(324,324,"Landauer's Principle",19,"1961","Proven","Erasure of 1 bit dissipates ≥k_B T ln 2 heat","Confirmed experimentally 2012")
E(325,325,"Kolmogorov Complexity (Algorithmic Info)",19,"1965","Proven","K_U(x)=min{|p|:U(p)=x}","Theoretical; non-computable but defined")
E(326,326,"Maximum Entropy Principle (Jaynes)",19,"1957","Proven","Maximize S subject to constraints→least biased distribution","Inference; confirmed")

# METROLOGY / EXTRA (327-333)
E(327,327,"Speed of Light Defines Meter",20,"1983","Proven","c=299792458 m/s EXACT","1m=c·(1/299792458)s")
E(328,328,"Planck Constant Defines Kilogram",20,"2019","Proven","h=6.62607015e-34 J·s EXACT","Kibble balance")
E(329,329,"Elementary Charge Defines Ampere",20,"2019","Proven","e=1.602176634e-19 C EXACT","1A=e·(1/1.602176634e-19)s⁻¹")
E(330,330,"Boltzmann Constant Defines Kelvin",20,"2019","Proven","k_B=1.380649e-23 J/K EXACT","Acoustic gas thermometry")
E(331,331,"Avogadro Number Defines Mole",20,"2019","Proven","N_A=6.02214076e23 EXACT","XRCD; silicon sphere")
E(332,332,"Josephson Voltage Standard",12,"1962–90","Proven","V=n f/K_J; K_J=2e/h=483597.9 GHz/V EXACT","Voltage metrology")
E(333,333,"Quantum Hall Resistance Standard",12,"1980","Proven","R_H=h/(i e²); R_K=h/e²=25812.80745... Ω","Resistance metrology")

cur.executemany("INSERT INTO equations VALUES (?,?,?,?,?,?,?,?)", eq)

# ================================================================
# SUB-EQUATIONS (detailed formulas)
# ================================================================
subs = []
def add_sub(rid, sub, name, latex, desc, cond=""):
    subs.append((rid, sub, name, latex, desc, cond))

add_sub(1,"1st","Inertia","\\Sigma \\vec{F}=0\\Rightarrow \\vec{v}=\\text{const}","No net force → constant velocity","Inertial frames")
add_sub(1,"2nd","F=dp/dt","\\vec{F}=\\frac{d\\vec{p}}{dt}=m\\vec{a}","Constant mass; relativistic: F^\\mu=dp^\\mu/d\\tau","")
add_sub(1,"3rd","Action-Reaction","\\vec{F}_{A\\to B}=-\\vec{F}_{B\\to A}","Equal and opposite in Newtonian mechanics","")
add_sub(2,"EL","Euler-Lagrange","\\frac{d}{dt}\\frac{\\partial L}{\\partial \\dot{q}_i}-\\frac{\\partial L}{\\partial q_i}=0","From \\delta S=0; S=\\int L dt","Generalized coordinates")
add_sub(3,"Hamilton","Hamilton's Canonical Equations","\\dot{q}_i=\\frac{\\partial H}{\\partial p_i},\\; \\dot{p}_i=-\\frac{\\partial H}{\\partial q_i}","Phase space, symplectic; H=T+V for conservative","Exact")
add_sub(4,"HJ","Hamilton-Jacobi","\\frac{\\partial S}{\\partial t}+H\\left(q,\\frac{\\partial S}{\\partial q},t\\right)=0","S action as function of endpoint; classical→quantum bridge","")
add_sub(7,"Euler","Euler's Rigid Body Rotation","I_1\\dot{\\omega}_1-(I_2-I_3)\\omega_2\\omega_3=\\tau_1","Principal axes; torque-free precession","")
add_sub(14,"Hooke","Hooke's Law","\\sigma=E\\varepsilon,\\; F=-kx","Linear elastic; valid below yield","")
add_sub(16,"Coriolis","Coriolis Force","\\vec{F}_{\\text{cor}}=-2m\\,\\vec{\\omega}\\times\\vec{v}'","Rotating frame fictitious force","Weather, Foucault pendulum")
add_sub(24,"Newton-G","Newton's Law of Universal Gravitation","\\vec{F}=-\\frac{G m_1 m_2}{r^2}\\hat{r}","Inverse-square; weak-field GR limit","G=6.67430e-11")
add_sub(28,"Kepler3","Kepler's 3rd Law","T^2=\\frac{4\\pi^2}{GM}a^3","For elliptical orbits, a=semi-major axis","Two-body")
add_sub(33,"Redshift-GR","Gravitational Redshift","\\frac{\\Delta\\nu}{\\nu}=-\\frac{GM}{rc^2}","Pound-Rebka; GPS ~38μs/day correction","Static weak field")
add_sub(36,"Coulomb","Coulomb's Law","\\vec{F}=\\frac{1}{4\\pi\\varepsilon_0}\\frac{q_1 q_2}{r^2}\\hat{r}","Force between point charges","1/r^{2+\\delta}, \\delta<10^{-16}")
add_sub(37,"Lorentz","Lorentz Force","\\vec{F}=q(\\vec{E}+\\vec{v}\\times\\vec{B})","EM force on moving charge","All particle accelerators")
add_sub(38,"ME1","Gauss (Electric)","\\nabla\\cdot\\vec{E}=\\rho/\\varepsilon_0","Electric charge is source of E-field","SI units")
add_sub(38,"ME2","Gauss (Magnetic)","\\nabla\\cdot\\vec{B}=0","No magnetic monopoles; m_\\gamma<10^{-18} eV/c²","")
add_sub(38,"ME3","Faraday-Lenz","\\nabla\\times\\vec{E}=-\\frac{\\partial\\vec{B}}{\\partial t}","Changing B creates circulating E","Generators, MRI, induction")
add_sub(38,"ME4","Ampère-Maxwell","\\nabla\\times\\vec{B}=\\mu_0\\vec{J}+\\mu_0\\varepsilon_0\\frac{\\partial\\vec{E}}{\\partial t}","Currents+changing E create circulating B; displacement current predicted EM waves","")
add_sub(50,"Poynting","Poynting Vector","\\vec{S}=\\frac{1}{\\mu_0}\\vec{E}\\times\\vec{B}","EM energy flux (W/m²); u=½ε₀E²+½B²/μ₀","")
add_sub(51,"Wave-eq","EM Wave Equation","\\Box\\vec{E}=0,\\;\\Box\\vec{B}=0,\\; \\Box=-\\frac{1}{c^2}\\frac{\\partial^2}{\\partial t^2}+\\nabla^2","c=1/√(μ₀ε₀); Light=EM wave","Maxwell→Hertz 1887")
add_sub(54,"Larmor","Larmor Radiation Formula","P=\\frac{q^2 a^2}{6\\pi\\varepsilon_0 c^3}","Non-relativistic accelerated charge radiation","Synchrotron confirmed")
add_sub(70,"IdealGas","Ideal Gas Law","pV=nRT=N k_B T","p in Pa, V in m³, n in mol, T in K","R=8.314462618")
add_sub(75,"Carnot","Carnot Efficiency","\\eta_{\\max}=1-\\frac{T_c}{T_h}","Maximum possible heat engine efficiency","Irreversible: η<Carnot")
add_sub(86,"Planck","Planck's Blackbody Law","B_\\nu(\\nu,T)=\\frac{2h\\nu^3}{c^2}\\frac{1}{e^{h\\nu/k_B T}-1}","Spectral radiance [W/(sr·m²·Hz)]","Energy/mode: hν/(e^{hν/kT}−1)")
add_sub(91,"Compton","Compton Scattering","\\lambda'-\\lambda=\\frac{h}{m_e c}(1-\\cos\\theta)","Photon scatters from free electron; Δλ_max=0.00486 nm","Kinematic derivation")
add_sub(92,"deBroglie","de Broglie Wavelength","\\lambda=\\frac{h}{p}=\\frac{h}{\\gamma mv}","Matter waves; Davisson-Germer 1927","All particles")
add_sub(93,"TDSE","Time-Dependent Schrödinger Eq.","i\\hbar\\frac{\\partial}{\\partial t}|\\psi\\rangle=\\hat{H}|\\psi\\rangle","Unitary evolution; fundamental","Non-relativistic QM")
add_sub(93,"TISE","Time-Independent Schrödinger Eq.","\\hat{H}\\psi=E\\psi","Stationary states; eigenvalue eq.","")
add_sub(95,"Born","Born Rule","\\rho(\\vec{r},t)=|\\psi(\\vec{r},t)|^2","Probability density; normalized to 1","All quantum measurements")
add_sub(98,"HUP","Heisenberg Uncertainty","\\Delta x\\Delta p\\geq\\frac{\\hbar}{2},\\; \\Delta A\\Delta B\\geq\\frac{1}{2}|\\langle[A,B]\\rangle|","From non-commuting operators","General Robertson-Schrödinger")
add_sub(99,"HO","Harmonic Oscillator Levels","E_n=\\hbar\\omega(n+\\tfrac{1}{2}),\\; n=0,1,2,\\dots","Zero-point E₀=½ℏω; ladder ops â,â†","Casimir effect, quantum optics")
add_sub(100,"Hatom","Hydrogen Energy Levels","E_n=-\\frac{R_y}{n^2},\\; R_y=\\frac{m_e e^4}{8\\varepsilon_0^2 h^2}=13.605693\\,\\text{eV}","Non-relativistic; Bohr model energy","Degeneracy: 2n² including spin")
add_sub(102,"Pauli","Pauli Spin Matrices","S_i=\\frac{\\hbar}{2}\\sigma_i,\\; \\sigma_x=\\begin{pmatrix}0&1\\\\1&0\\end{pmatrix},\\; \\sigma_y=\\begin{pmatrix}0&-i\\\\i&0\\end{pmatrix},\\; \\sigma_z=\\begin{pmatrix}1&0\\\\0&-1\\end{pmatrix}","Spin-½ operators","[σ_i,σ_j]=2iε_{ijk}σ_k")
add_sub(104,"Dirac","Dirac Equation","(i\\hbar\\gamma^\\mu\\partial_\\mu-mc)\\psi=0","Relativistic spin-½; {γ^μ,γ^ν}=2g^{μν}I₄","Predicted positron; g=2")
add_sub(109,"PauliExc","Pauli Exclusion Principle","\\psi(\\vec{r}_1,\\dots,\\vec{r}_i,\\dots,\\vec{r}_j,\\dots)=-\\psi(\\vec{r}_1,\\dots,\\vec{r}_j,\\dots,\\vec{r}_i,\\dots)","Fermion antisymmetry","Violation prob<4.5×10^{-29}")
add_sub(116,"Optical","Optical Theorem","\\operatorname{Im}f(0)=\\frac{k}{4\\pi}\\sigma_{\\text{total}}","Unitarity of S-matrix; exact","Forward scattering amplitude")
add_sub(117,"PathInt","Feynman Path Integral","\\langle x_f,t_f|x_i,t_i\\rangle=\\int\\mathcal{D}[x(t)]\\, e^{iS[x]/\\hbar}","Sum over all possible paths","Equivalent to Schrödinger")
add_sub(121,"Lorentz-Boost","Lorentz Boost","x'=\\gamma(x-vt),\\; t'=\\gamma\\left(t-\\frac{vx}{c^2}\\right),\\; \\gamma=\\frac{1}{\\sqrt{1-v^2/c^2}}","Boost along x; SR","c invariant in all frames")
add_sub(126,"Emc2","Mass-Energy Equivalence","E^2=(pc)^2+(mc^2)^2","p=0 → E=mc²","Every nuclear reaction confirms")
add_sub(129,"EFE","Einstein Field Equations","G_{\\mu\\nu}+\\Lambda g_{\\mu\\nu}=\\frac{8\\pi G}{c^4}T_{\\mu\\nu}","G_{\\mu\\nu}=R_{\\mu\\nu}-½R g_{\\mu\\nu}","Gravity=spacetime curvature")
add_sub(136,"BH-Entropy","Bekenstein-Hawking Entropy","S_{\\text{BH}}=\\frac{k_B A}{4\\ell_P^2}=\\frac{k_B c^3 A}{4G\\hbar}","Entropy∝horizon area; 4 laws of BH mechanics","T_H=κ/2π")
add_sub(137,"HawkingT","Hawking Temperature","T_H=\\frac{\\hbar c^3}{8\\pi GM k_B}","Schwarzschild BH; T_H(M_⊙)≈6.2×10^{-8}K","Radiation too faint for astro. BH")
add_sub(139,"SM-Lagrangian","Standard Model Lagrangian","\\mathcal{L}_{\\text{SM}}=-\\frac{1}{4}G_a^{\\mu\\nu}G^a_{\\mu\\nu}-\\frac{1}{4}W_i^{\\mu\\nu}W^i_{\\mu\\nu}-\\frac{1}{4}B^{\\mu\\nu}B_{\\mu\\nu}+i\\sum\\bar\\psi\\cancel{D}\\psi+|D_\\mu\\Phi|^2-V(\\Phi)+\\mathcal{L}_{\\text{Yukawa}}","SU(3)×SU(2)×U(1); 3 generations","Most precise physical theory")
add_sub(140,"YM","Yang-Mills Field Strength","F_{\\mu\\nu}^a=\\partial_\\mu A_\\nu^a-\\partial_\\nu A_\\mu^a+gf^{abc}A_\\mu^b A_\\nu^c","Non-abelian gauge; self-interactions","Basis of QCD+EW theory")
add_sub(142,"QCD-Lag","QCD Lagrangian","\\mathcal{L}_{\\text{QCD}}=\\sum_{f=1}^6\\bar\\psi_f(i\\cancel{D}-m_f)\\psi_f-\\frac{1}{4}G_a^{\\mu\\nu}G^a_{\\mu\\nu}","D_\\mu=\\partial_\\mu-ig_s A_\\mu^a T^a","Asymptotic freedom+confinement")
add_sub(144,"Beta-QCD","QCD 1-loop Beta Function","\\beta(\\alpha_s)=-\\frac{\\alpha_s^2}{2\\pi}\\left(11-\\frac{2}{3}n_f\\right)","β<0 for n_f≤16 → asymptotic freedom","α_s running 4 decades confirmed")
add_sub(148,"GMOR","Gell-Mann–Oakes–Renner","m_\\pi^2=-\\frac{(m_u+m_d)\\langle\\bar\\psi\\psi\\rangle}{f_\\pi^2}","Pion mass from quark masses+condensate","f_π≈92.2 MeV")
add_sub(149,"Higgs-Mech","Higgs Mechanism","M_W=\\frac{gv}{2},\\; M_Z=\\frac{v}{2}\\sqrt{g^2+g'^2},\\; v=\\frac{1}{\\sqrt{\\sqrt{2}G_F}}\\approx 246\\,\\text{GeV}","SSB gives gauge boson masses","m_H=125.25 GeV")
add_sub(159,"Fried1","First Friedmann Equation","H^2=\\left(\\frac{\\dot{a}}{a}\\right)^2=\\frac{8\\pi G}{3}\\rho-\\frac{kc^2}{a^2}+\\frac{\\Lambda c^2}{3}","H(t)=Hubble parameter; a(t)=scale factor","H₀=67.4 km/s/Mpc")
add_sub(160,"Fried2","Second Friedmann Equation","\\frac{\\ddot{a}}{a}=-\\frac{4\\pi G}{3}\\left(\\rho+\\frac{3p}{c^2}\\right)+\\frac{\\Lambda c^2}{3}","Acceleration from Λ; SN 1998 Nobel","q₀=−0.53")
add_sub(176,"N-S","Navier-Stokes (Incompressible)","\\frac{\\partial\\vec{v}}{\\partial t}+(\\vec{v}\\cdot\\nabla)\\vec{v}=-\\frac{1}{\\rho}\\nabla p+\\nu\\nabla^2\\vec{v}+\\vec{g}","ν=μ/ρ kinematic viscosity; ∇·v=0","Re=UL/ν")
add_sub(183,"Kolmo","Kolmogorov Spectrum","E(k)=C_K\\varepsilon^{2/3}k^{-5/3}","Turbulence inertial range; C_K≈1.5","~5 decades confirmed")
add_sub(191,"Snell","Snell's Law","n_1\\sin\\theta_1=n_2\\sin\\theta_2","Fermat's principle; refraction","Isotropic media")
add_sub(196,"DoubleSlit","Young's Double-Slit","\\Delta y=\\frac{\\lambda L}{d}","Fringe spacing on screen at distance L","d=slit separation")
add_sub(199,"Bragg","Bragg's Law","n\\lambda=2d\\sin\\theta","X-ray diffraction from crystal planes","All crystallography")
add_sub(241,"Decay","Radioactive Decay Law","N(t)=N_0 e^{-\\lambda t},\\; T_{1/2}=\\frac{\\ln 2}{\\lambda},\\; \\tau=\\frac{1}{\\lambda}","Exponential decay","All radioactive isotopes")
add_sub(242,"BetheW","Bethe-Weizsäcker Mass Formula","B=a_v A-a_s A^{2/3}-a_c\\frac{Z^2}{A^{1/3}}-a_a\\frac{(N-Z)^2}{A}+\\delta","a_v≈15.75,a_s≈17.8,a_c≈0.711,a_a≈23.7 MeV","±δ=±34A^{-3/4} MeV (pairing)")
add_sub(246,"NueOsc","Neutrino Oscillation Probability","P(\\nu_\\alpha\\to\\nu_\\beta)=\\sin^2(2\\theta)\\,\\sin^2\\!\\left(\\frac{\\Delta m^2 L}{4E}\\right)","2-flavor approximation","Super-K, SNO, Daya Bay confirmed")
add_sub(277,"Noether","Noether Current","J^\\mu=\\frac{\\partial\\mathcal{L}}{\\partial(\\partial_\\mu\\phi)}\\Delta\\phi-T^{\\mu}_{\\;\\nu}\\epsilon^\\nu,\\; \\partial_\\mu J^\\mu=0","Symmetry → conserved current","Mathematical theorem")
add_sub(297,"Partition","Canonical Partition Function","Z=\\sum_i g_i e^{-\\beta E_i},\\; F=-k_B T\\ln Z","All thermo. from Z","β=1/k_B T")

cur.executemany("INSERT INTO sub_equations (equation_id, subsection, name, latex_formula, description, conditions) VALUES (?,?,?,?,?,?)", subs)

# ================================================================
# VERIFICATIONS
# ================================================================
v_list = []
def add_v(eid, test, expt, yr, prec, st="Confirmed"):
    v_list.append((eid, test, expt, yr, prec, st))

# Maxwell
add_v(38,"Hertz Radio Wave Detection","Hertz 1887",1887,"Qualitative→confirmed","Confirmed")
add_v(38,"Photon mass limit","Various electromagnetic tests",2000,"m_γ<10^{-18} eV/c²","Confirmed")
add_v(38,"1/r² Coulomb deviation","Cavendish-type electrostatics",2000,"δ<10^{-16}","Confirmed")
# GR
add_v(129,"Eddington Solar Eclipse (Light Deflection)","Eddington 1919",1919,"~10% precision","Confirmed")
add_v(129,"Gravitational Redshift (Pound-Rebka)","Pound & Rebka 1960",1960,"~10^{-5}","Confirmed")
add_v(129,"Shapiro Time Delay","Viking, Cassini",1970,"10^{-5}","Confirmed")
add_v(129,"Frame-Dragging (Gravity Probe B)","GP-B 2011",2011,"~10%","Confirmed")
add_v(129,"LIGO GW150914 (Binary BH Merger)","LIGO 2015",2015,"SNR>20; ringdown matches GR","Confirmed")
add_v(129,"EHT M87* Shadow","EHT 2019",2019,"40 μas; GR prediction","Confirmed")
add_v(129,"PSR B1913+16 Orbit Decay","Hulse-Taylor 1974",1974,"<0.2% agreement with GR quadrupole","Confirmed")
add_v(129,"Double Pulsar PSR J0737-3039","Kramer et al. 2006",2006,"5 independent GR tests passed","Confirmed")
# QM
add_v(93,"Hydrogen 1S-2S Spectroscopy","Hänsch group",2005,"10^{-10}","Confirmed")
add_v(104,"Positron Discovery (Anderson)","Anderson 1932",1932,"Prediction→discovery","Confirmed")
add_v(108,"Electron g-2","Hanneke et al. 2008",2008,"1 part in 10^{12}","Confirmed")
add_v(109,"VIP Pauli Violation Search","Gran Sasso",2015,"Violation prob<4.5×10^{-29}","Confirmed")
add_v(109,"Borexino Pauli Violation","Borexino",2016,"β²/2<2.6×10^{-37}","Confirmed")
add_v(120,"Loophole-free Bell Test","Hensen et al. 2015",2015,">40σ violation of local realism","Confirmed")
# SM
add_v(139,"Higgs Boson Discovery","ATLAS+CMS 2012",2012,"m_H=125.25±0.17 GeV; >5σ","Confirmed")
add_v(139,"LEP Electroweak Precision Fit","LEP/SLD",2001,"χ²/ndf≈22/15","Confirmed")
add_v(139,"W Boson Mass","CDF II/ATLAS",2022,"Tensions being resolved","Tension/Confirmed")
add_v(142,"α_s running 4 decades","HERA, LHC, SLD",2020,"Confirmed","Confirmed")
add_v(142,"Lattice QCD Hadron Spectrum","BMW/MILC/FLAG",2020,"<1% light hadrons","Confirmed")
add_v(142,"Tetraquark Z_c(3900)","BESIII/Belle 2013",2013,">5σ","Confirmed")
add_v(142,"Pentaquark P_c(4380)","LHCb 2015",2015,">5σ","Confirmed")
# Cosmology
add_v(159,"CMB Power Spectrum (Planck 2018)","Planck",2018,"ΛCDM at <1%","Confirmed")
add_v(159,"Supernova Ia Accelerating Universe","Riess/Perlmutter 1998",1998,"Nobel 2011; confirmed","Confirmed")
add_v(159,"BAO Standard Ruler","SDSS/BOSS/DESI",2015,"147 Mpc comoving sound horizon","Confirmed")
add_v(164,"CMB Temperature","COBE/FIRAS 1990",1990,"T₀=2.72548 K; ΔT<50 ppm","Confirmed")
add_v(165,"Primordial Deuterium Abundance","Quasar Absorption",2010,"D/H=(2.53±0.03)×10^{-5}","Confirmed")
add_v(165,"Primordial ⁴He Abundance","Extragalactic HII Regions",2018,"Y_p=0.24709±0.00025","Confirmed")
# Nuclear
add_v(241,"α-Decay Half-lives (Geiger-Nuttall)","Geiger+Nuttall 1911",1911,"Quantum tunneling explains range","Confirmed")
add_v(246,"Solar ν Deficit→Oscillation","Super-K + SNO 2001",2001,"ν_e→ν_{μ,τ} confirmed","Confirmed")
add_v(246,"Reactor ν Disappearance (θ₁₃)","Daya Bay/RENO 2012",2012,"θ₁₃≈8.5°; >5σ","Confirmed")
# Fluids
add_v(176,"Poiseuille Flow Viscometry","Standard viscometers",1900,"R⁴ dependence confirmed","Confirmed")
add_v(176,"Kolmogorov Spectrum","Wind tunnels, ocean, atmosphere",1980,"k^{-5/3} over ~5 decades","Confirmed")
add_v(179,"Bernoulli in Wind Tunnels","Aeronautical engineering",1900,"Lift+pipe flow confirmed","Confirmed")
# Optics
add_v(191,"Snell's Law Verification","Refractive index metrology",1900,"Confirmed to high precision","Confirmed")
add_v(199,"DNA Structure from X-ray Diffraction","Franklin/Watson/Crick 1953",1953,"Bragg's law applied","Confirmed")
# Condensed Matter
add_v(224,"BCS Isotope Effect","Various 1950",1950,"T_c∝M^{-1/2}","Confirmed")
add_v(227,"Josephson Voltage Standard","NIST",1980,"K_J=2e/h=483597.9 GHz/V; exact","Confirmed")
add_v(235,"Quantum Hall Resistance Standard","Klitzing 1980",1980,"R_K=h/e²=25812.807 Ω","Standard; 10^{-9} precision")
# Stat Mech
add_v(303,"Jarzynski Equality (RNA pulling)","Bustamante group",2005,"RNA hairpin unfolding","Confirmed")
add_v(304,"Crooks FT (DNA hairpin)","Collin et al. 2005",2005,"Single-molecule","Confirmed")
# Landauer
add_v(324,"Landauer Bit Erasure Heat","Bérut et al. 2012",2012,"k_B T ln 2 confirmed","Confirmed")
# Astro
add_v(252,"Eddington Limit in X-ray Binaries","X-ray telescopes",2000,"ULX confirmed","Confirmed")
add_v(260,"Solar pp Chain (Borexino)","Borexino",2014,"Solar ν flux matched","Confirmed")
# Exoplanet
add_v(28,"Exoplanet Mass via Radial Velocity","Kepler/TESS/HARPS",2015,"Kepler's 3rd law used for masses","Confirmed")

cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", v_list)

# ================================================================
# OPEN PROBLEMS
# ================================================================
op_list = []
def add_op(pid, name, desc, rel):
    op_list.append((pid, name, desc, rel))

add_op(1,"Quantum Gravity","GR+QM inconsistent at Planck scale (10^{-35}m). String theory, LQG, CDT, asymptotic safety — none confirmed.","129,93,104")
add_op(2,"Dark Matter","Overwhelming gravitational evidence (rotation curves, CMB, lensing, Bullet Cluster). No particle ID. WIMPs, axions, sterile ν — unconfirmed.","129,159")
add_op(3,"Dark Energy / CC Problem","Observed ρ_Λ≈(2.3×10^{-3}eV)⁴ vs QFT prediction ~(10^{18}GeV)⁴. Factor 10^{-120}. Why so small but nonzero?","129,159,168")
add_op(4,"Baryon Asymmetry","η=(n_B−n_B̄)/n_γ≈6×10^{-10}. Sakharov conditions satisfied but SM CP violation too small by factor ~10^{-9}.","139,146")
add_op(5,"Neutrino Masses","Oscillations prove m_ν≠0. Dirac? Majorana? Seesaw? 0νββ-decay not yet observed. Absolute scale unknown.","104,147,246")
add_op(6,"Strong CP Problem","Why is QCD θ-angle <10^{-10}? PQ mechanism→axion. ADMX, CAST searches ongoing.","142,144")
add_op(7,"Hierarchy Problem","Why is m_H(125 GeV)≪M_Pl(10^{19} GeV)? No SUSY, extra dims, or compositeness seen at LHC up to ~few TeV.","139,149")
add_op(8,"Inflation Mechanism","Inflation fits data (flatness, horizon, structure), but inflaton field unknown. No direct detection. Eternal inflation? Multiverse?","172")
add_op(9,"Quantum Measurement Problem","Why does observation collapse wavefunction? Copenhagen, Many-Worlds, de Broglie-Bohm, QBism — no experimental discrimination.","93,95,120")
add_op(10,"Arrow of Time","Why was Big Bang entropy so low? Past Hypothesis. Boltzmann brain problem.","68,299,300")
add_op(11,"Hubble Tension","H₀(CMB)=67.4±0.5 vs H₀(local)=73.0±1.0. ~5σ. New physics or systematics?","159,163,173")
add_op(12,"Lithium Problem (BBN)","Predicted ⁷Li/H~5×10^{-10} vs observed ~1.6×10^{-10} in metal-poor halo stars. Factor ~3.","165")
add_op(13,"Nature of Dark Energy","Is w exactly −1 (Λ) or evolving? DESI, Euclid, Roman Space Telescope.","168")
add_op(14,"Black Hole Information Paradox","Does info escape during BH evaporation? Island formula, replica wormholes — apparent resolution but exact mechanism unclear.","136,137,138")
add_op(15,"Proton Decay","τ_p>10^{34} yr (Super-K). No decay observed. Simple SU(5) GUT ruled out. Larger GUTs or no unification?","155,156")
add_op(16,"Muon g-2 Anomaly","a_μ(exp)−a_μ(SM)=251(59)×10^{-11} (4.2σ). New physics or underestimated hadronic contributions?","108,158")
add_op(17,"CKM Unitarity Tension","First-row unitarity: |V_ud|²+|V_us|²+|V_ub|²=0.9985±0.0007 (2σ low).","146")
add_op(18,"Gallium Neutrino Anomaly","Deficit in ⁵¹Cr/³⁷Ar calibration. Possible sterile ν.","246")
add_op(19,"Existence of Magnetic Monopoles","None detected. Dirac condition requires charge quantization if they exist.","38,36")
add_op(20,"Cosmic Lithium Problem","⁷Li from BBN higher than observations. Possible solution: astration, new physics, or stellar depletion.","165")

cur.executemany("INSERT INTO open_problems VALUES (?,?,?,?)", op_list)

# ================================================================
# POPULATE FTS
# ================================================================
cur.execute("INSERT INTO eq_fts(rowid, title, description) SELECT id, title, significance FROM equations")

# ================================================================
# USEFUL VIEWS
# ================================================================
cur.executescript("""
CREATE VIEW v_all AS
SELECT e.eq_number, e.title, e.year_range, d.name as domain, e.status, e.significance
FROM equations e JOIN domains d ON e.domain_id=d.id ORDER BY e.eq_number;

CREATE VIEW v_by_domain AS
SELECT d.name, COUNT(e.id) as num_eqs
FROM domains d LEFT JOIN equations e ON e.domain_id=d.id
GROUP BY d.id ORDER BY d.name;

CREATE VIEW v_verified AS
SELECT e.eq_number, e.title, v.test_name, v.experiment, v.year, v.precision_level, v.status
FROM equations e JOIN verifications v ON v.equation_id=e.id ORDER BY e.eq_number, v.year;

CREATE VIEW v_all_formulas AS
SELECT e.eq_number, e.title, se.subsection, se.name, se.latex_formula
FROM sub_equations se LEFT JOIN equations e ON se.equation_id=e.id
ORDER BY e.eq_number, se.id;
""")

conn.commit()
conn.close()

print(f"Database: {DB} ({os.path.getsize(DB)} bytes)")
print(f"Equations: {len(eq)}")
print(f"Sub-sections: {len(subs)}")
print(f"Verifications: {len(v_list)}")
print(f"Constants: {len(constants)}")
print(f"Open Problems: {len(op_list)}")
print(f"Domains: {len(domains)}")
