#!/usr/bin/env python3
"""Append ALL remaining physics domains to physics_equations.db"""

import sqlite3, os, sys

DB = "/home/allaun/physics_equations.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT MAX(id) FROM equations");  eid = cur.fetchone()[0] or 540
cur.execute("SELECT MAX(eq_number) FROM equations"); enum = cur.fetchone()[0] or 540
cur.execute("SELECT MAX(id) FROM sub_equations"); sid = cur.fetchone()[0] or 0
cur.execute("SELECT MAX(id) FROM verifications"); vid = cur.fetchone()[0] or 0
cur.execute("SELECT MAX(id) FROM domains"); did_val = cur.fetchone()[0] or 27

# ================================================================
# NEW DOMAINS
# ================================================================
new_domains = [
    (28,"Geophysics","Seismology, geomagnetism, geodesy, plate tectonics, gravity",None),
    (29,"Atmospheric Physics","Meteorology, cloud physics, radiation, lightning, climate",None),
    (30,"Oceanography","Ocean waves, tides, thermohaline circulation, coastal physics",None),
    (31,"Hydrology","Groundwater, surface water, Darcy's law, evapotranspiration, porous media",None),
    (32,"Biophysics","Ion channels, membrane potentials, molecular motors, protein folding",None),
    (33,"Chemical Physics","Reaction kinetics, transition state theory, Marcus theory, molecular dynamics",None),
    (34,"Photonics & Laser Physics","Laser physics, nonlinear optics, mode-locking, solitons, photonic crystals",None),
    (35,"Atomic & Molecular Physics","Atomic spectra, Zeeman/Stark, Franck-Condon, Born-Oppenheimer, hyperfine",None),
    (36,"Rheology","Non-Newtonian fluids, viscoelasticity, thixotropy, yield stress",None),
    (37,"Tribology","Friction, wear, lubrication, contact mechanics, Stribeck curve",None),
    (38,"Granular Materials","Janssen effect, angle of repose, force chains, jamming, granular flow",None),
    (39,"Nanoscience","Quantum dots, Coulomb blockade, Kondo effect, ballistic transport, 2D materials",None),
    (40,"Quantum Information","Qubits, entanglement, quantum gates, error correction, Bell states",None),
    (41,"Nonlinear Dynamics & Chaos","Bifurcation, Lorenz attractor, Lyapunov exponents, fractals, synchronization",None),
    (42,"Medical Physics","MRI, CT, PET, ultrasound, radiation therapy, dosimetry, laser surgery",None),
    (43,"Radiation Physics","Dosimetry, shielding, attenuation, Bragg peak, MIRD formalism, LET/RBE",None),
    (44,"Energy Physics","Photovoltaics, fuel cells, batteries, thermoelectrics, wind/hydro, fusion energy",None),
    (45,"Space Physics","Magnetosphere, solar wind, cosmic rays, Van Allen belts, ionosphere, reconnection",None),
    (46,"Detonics & Shock Physics","Detonation waves, Chapman-Jouguet, ZND theory, Rankine-Hugoniot, blast scaling",None),
    (47,"Metamaterials","Negative index, transformation optics, cloaking, split-ring resonators, phononic",None),
    (48,"Underwater Acoustics","SONAR equation, sound speed profiles, propagation loss, ambient noise, scattering",None),
    (49,"Engineering Physics","Heat exchangers, structural dynamics, feedback control, signal processing",None),
    (50,"Electrochemistry (Advanced)","Pourbaix diagrams, impedance spectroscopy, double-layer structure, fuel cells",None),
]
for d in new_domains:
    cur.execute("INSERT OR IGNORE INTO domains VALUES (?,?,?,?)", d)

# ================================================================
# EQUATION INJECTOR
# ================================================================
eqs = []
def E(title, dom, year, status, sig, prec):
    global eid, enum
    eid += 1; enum += 1
    eqs.append((eid, enum, title, dom, year, status, sig, prec))

subs = []
def S(rid, sub_name, name, latex, desc, cond=""):
    global sid
    sid += 1
    subs.append((sid, rid, sub_name, name, latex, desc, cond))

vers = []
def V(rid, test, expt, yr, prec, st="Confirmed"):
    global vid
    vid += 1
    vers.append((vid, rid, test, expt, yr, prec, st))

class EqID:
    """Tracks the last equation ID for referencing in sub-equations"""
    pass

# ================================================================
# 1. GEOPHYSICS (Seismology, Geodesy, Geomagnetism, Tectonics)
# ================================================================

E("Seismic Wave Equation (Elastic)", 28, "1820s", "Proven",
  "ρ ∂²u/∂t² = (λ+μ)∇(∇·u) + μ∇²u; vector elastic wave equation; P and S waves",
  "All seismology foundation; confirmed by every earthquake")
S(eid, "PWave", "P-Wave Speed", r"v_P = \sqrt{\frac{K + \frac{4}{3}\mu}{\rho}} = \sqrt{\frac{\lambda+2\mu}{\rho}}", "Compressional/primary wave; fastest", "Earth: v_P~5-8 km/s (crust), ~8-13 (mantle)")
S(eid, "SWave", "S-Wave Speed", r"v_S = \sqrt{\frac{\mu}{\rho}}", "Shear/secondary wave; does not travel through liquids", "v_S < v_P; Earth outer core: v_S=0")
V(eid, "Earthquake P/S wave arrival times", "Global Seismic Network", 1900, "Millisecond accuracy today", "Confirmed")

E("Snell's Law (Seismic Refraction at Interfaces)", 28, "1910", "Proven",
  "sin i₁/v₁ = sin i₂/v₂ = p (ray parameter); seismic ray tracing through layered Earth",
  "Seismic tomography; Mohorovicic 1909 discovered Moho")
S(eid, "RayParam", "Ray Parameter (Seismic)", r"p = \frac{\sin i}{v} = \frac{dt}{d\Delta}", "Constant along ray in layered media; used for inversion", "")
V(eid, "Moho discovery (1909)", "Mohorovicic 1909", 1909, "Crust-mantle boundary at ~30 km", "Confirmed")

E("Gutenberg-Richter Magnitude-Energy Relation", 28, "1956", "Proven",
  "log₁₀ E = 4.8 + 1.5 M (E in Joules); log₁₀ E = 5.24 + 1.44 M (later refinement)",
  "Empirical earthquake energy from magnitude")
S(eid, "Richter", "Richter Magnitude Definition", r"M_L = \log_{10} A - \log_{10} A_0(\Delta)", "A = max amplitude on Wood-Anderson seismograph; Δ=epicentral distance", "Local magnitude; standardized for S. California")
V(eid, "Energy release of 1906 San Francisco ~25×10^{15} J", "Lawson report 1908", 1956, "Matches G-R relation", "Confirmed")

E("Omori's Law (Aftershock Decay)", 28, "1894", "Proven",
  "n(t) = K / (c + t)^p; p≈1 (often 0.9–1.4); K,c constants; t=time after mainshock",
  "Aftershock rate decays as power law; universal")

E("Frequency-Magnitude Distribution (Gutenberg-Richter Law)", 28, "1944", "Proven",
  "log₁₀ N(≥M) = a − b M; b≈1 (global average); N=cumulative number of earthquakes",
  "Self-similarity of earthquake populations; b-value stress indicator")

E("Bullen's Compressibility-Pressure Hypothesis (Earth Interior)", 28, "1940s", "Proven",
  "K = a + bP; Earth core compressibility varies linearly with pressure",
  "Earth interior modeling; PREM model (Dziewonski-Anderson 1981)")

E("Love Wave Dispersion Equation (Surface Waves)", 28, "1911", "Proven",
  "tan(κβ₁H) = (μ₂β₂)/(μ₁β₁); Love wave existence condition in layer over half-space",
  "Crustal structure from surface wave dispersion")
S(eid, "RayleighWave", "Rayleigh Wave Equation", r"\left(2-\frac{v^2}{v_S^2}\right)^2 = 4\sqrt{\left(1-\frac{v^2}{v_P^2}\right)\left(1-\frac{v^2}{v_S^2}\right)}", "Determines Rayleigh wave speed v from v_P, v_S", "Surface waves in homogeneous half-space")
V(eid, "Love waves in 1906 SF earthquake", "Love 1911", 1911, "Theoretical prediction → observed", "Confirmed")

E("Airy Isostasy (Crustal Compensation Model)", 28, "1855", "Proven",
  "Mountain root thickness = h ρ_c/(ρ_m−ρ_c); h=elevation; ρ_c,ρ_m=crust/mantle density",
  "~5.6 km root per km elevation (ρ_c=2.67,ρ_m=3.27); Pratt model: variable density columns")
V(eid, "Himalayan root ~70 km crustal thickness", "Seismic sounding", 1980, "Matches Airy prediction within ~20%", "Confirmed")

E("Free-Air Gravity Anomaly", 28, "1930s", "Proven",
  "Δg_FA = g_obs − g_theoretical(λ) + δg_FAC; δg_FAC=0.3086h mGal (free-air correction, h in m)",
  "Gravity survey reduction; reveals subsurface density variations")

E("Bouguer Gravity Anomaly (Complete)", 28, "1749/1930s", "Proven",
  "Δg_B = g_obs − g_theo(λ) + 0.3086h − 0.0419ρh + δg_terrain; ρ=2.67 g/cm³ typical",
  "Removes topographic effect; reveals subsurface density anomalies")
V(eid, "Oceanic trench negative Bouguer anomalies", "Marine gravity surveys", 1960, "Matched by subducting slab model", "Confirmed")

E("Geodetic Reference System (GRS80/WGS84 Ellipsoid)", 28, "1980/84", "Proven",
  "a=6378137m, f=1/298.257223563 (WGS84); meridian radius M=a(1−e²)/(1−e²sin²φ)^{3/2}",
  "Global positioning reference; GPS/WGS84 is standard")

E("Geoid Undulation (Stokes' Formula)", 28, "1849", "Proven",
  "N = (R/4πγ)∫∫ Δg S(ψ) dσ; S(ψ) = Stokes function; Δg=gravity anomaly; ψ=angular distance",
  "Geoid height from gravity anomalies; gravimetric geodesy")
V(eid, "GOCE/GRACE satellite geoid models to cm precision", "GOCE 2009-2013, GRACE 2002-2017", 2010, "Geoid accuracy ~1-2 cm at 100 km resolution", "Confirmed")

E("Plate Motion on a Sphere (Euler Pole Rotation)", 28, "1960s", "Proven",
  "v = ω × R; v=linear velocity, ω=angular velocity vector, R=Earth radius vector",
  "All tectonic plate motions described by rotation about Euler poles")
S(eid, "PlateVel", "Plate Velocity Magnitude", r"v = \omega R \sin\alpha", "α = angular distance from Euler pole to point on plate", "Pacific plate: ~70-100 mm/yr")
V(eid, "GPS plate motion vectors match geologic rates", "Space geodesy (VLBI, GPS, SLR)", 1990, "Within 1-2 mm/yr", "Confirmed")

E("Geomagnetic Secular Variation (IGRF Model)", 28, "1960s", "Proven",
  "B(r,θ,φ,t) = −∇[a Σ(g_n^m cos mφ + h_n^m sin mφ)(a/r)^{n+1} P_n^m(cos θ)]",
  "International Geomagnetic Reference Field; updated every 5 years")

E("Curie Temperature Isotherm (Magnetic Crustal Thickness)", 28, "1970s", "Proven",
  "Magnetic minerals become paramagnetic above ~580°C (magnetite Curie point); ~20-30 km depth",
  "Moho often corresponds to Curie isotherm in continental crust")

E("Darcy's Law (Groundwater Flow in Porous Media)", 31, "1856", "Proven",
  "Q = −K A (dh/dl); v_Darcy = Q/A = −K ∇h; K = hydraulic conductivity",
  "All groundwater hydrology; confirmed experimentally by Darcy")
S(eid, "Darcy3D", "Darcy's Law (3D General)", r"\vec{q} = -\frac{k}{\mu}(\nabla p - \rho \vec{g})", "k=permeability (m²); μ=viscosity; valid for laminar flow through porous media", "Re<1-10 based on grain size")
V(eid, "Darcy's apparatus (Dijon fountains)", "Darcy 1856", 1856, "Linear Q vs dh/dl confirmed", "Confirmed")

E("Dupuit-Forchheimer Assumption (Unconfined Aquifer)", 31, "1863/1901", "Proven",
  "Q = −K h (dh/dx); h=saturated thickness; flow lines approximately horizontal",
  "Unconfined groundwater flow; Dupuit parabola for flow to wells")

E("Theis Solution (Well Hydraulics, Confined Aquifer)", 31, "1935", "Proven",
  "s(r,t) = Q/(4πT) ∫_u^∞ (e^{-x}/x) dx; u = r²S/(4Tt); T=transmissivity, S=storativity",
  "Transient drawdown around pumping well; exact for ideal confined aquifer")
S(eid, "TheisApprox", "Cooper-Jacob Approximation", r"s = \frac{2.3 Q}{4\pi T}\log\frac{2.25 T t}{r^2 S}", "Valid for u<0.01; straight-line fit on semi-log plot", "Most commonly used well-test method")
V(eid, "Aquifer tests worldwide confirm Theis", "Countless pumping tests", 1950, "Standard hydrogeology method", "Confirmed")

E("Manning Equation (Open Channel Flow)", 31, "1889", "Proven",
  "v = (1/n) R_h^{2/3} S^{1/2}; n=Manning roughness; R_h=hydraulic radius; S=slope",
  "All open-channel hydraulics; rivers, canals, culverts")
V(eid, "River discharge measurements; USGS stream gages", "USGS standard method", 1900, "±5-10% typical accuracy", "Confirmed")

E("Rational Method (Peak Runoff Estimation)", 31, "1889", "Proven",
  "Q_peak = C i A; C=runoff coefficient (0-1); i=rainfall intensity; A=watershed area",
  "Stormwater design; small watersheds (<200 acres)")

E("Richards Equation (Unsaturated Flow in Soils)", 31, "1931", "Proven",
  "∂θ/∂t = ∇·[K(θ) ∇(ψ+z)]; θ=moisture content; ψ=pressure head; K(θ)=hydraulic conductivity",
  "Vadose zone hydrology; infiltration; soil physics")
S(eid, "Richards1D", "Richards Equation (1D Vertical)", r"\frac{\partial\theta}{\partial t} = \frac{\partial}{\partial z}\left[K(\theta)\left(\frac{\partial\psi}{\partial z}+1\right)\right]", "Unsaturated vertical flow in soil; highly nonlinear", "Richards 1931")
V(eid, "Tensiometer + TDR field measurements match Richards solutions", "Soil physics experiments", 1970, "Qualitatively correct; quantitative with fitted parameters", "Confirmed")

E("Horton Infiltration Model", 31, "1940", "Proven",
  "f(t) = f_c + (f₀−f_c) e^{−kt}; infiltration capacity decays exponentially",
  "Rainfall excess → runoff generation; empirical but widely validated")
V(eid, "Rainfall simulator plot experiments", "Horton 1940s", 1940, "Decay curve fits well for most soils", "Confirmed")

E("Penman-Monteith Evapotranspiration Equation", 31, "1965", "Proven",
  "ET = [Δ(R_n−G) + ρ_a c_p (e_s−e_a)/r_a] / [Δ + γ(1+r_s/r_a)]",
  "Standard reference evapotranspiration (FAO-56); energy + aerodynamic terms")
V(eid, "FAO-56 reference ET standard", "FAO Standard", 1998, "Matches lysimeter data to ~10%", "Confirmed")

E("Stomatal Conductance (Jarvis Model)", 31, "1976", "Proven",
  "g_s = g_s_max · f₁(PAR) · f₂(T) · f₃(VPD) · f₄(CO₂) · f₅(ψ_leaf); multiplicative stress functions",
  "Plant-atmosphere gas exchange; photosynthesis models")

# ================================================================
# 2. OCEANOGRAPHY
# ================================================================

E("Linear Wave Theory (Airy Wave, Dispersion Relation)", 30, "1845", "Proven",
  "ω² = gk tanh(kh); deep water (kh≫1): ω²=gk, c=g/ω; shallow water (kh≪1): ω²=ghk², c=√(gh)",
  "All ocean surface gravity waves; confirmed")
S(eid, "Wavelength", "Deep-Water Wavelength", r"\lambda = \frac{g T^2}{2\pi}", "Wavelength from period T; deep water", "T=10s → λ≈156m; c=gT/(2π)")
V(eid, "Ocean wave spectra match linear theory", "Waverider buoys", 1960, "Dispersion confirmed to high precision", "Confirmed")

E("Stokes Drift (Mass Transport Under Waves)", 30, "1847", "Proven",
  "U_s = ½ a² ω k e^{2kz}; net Lagrangian drift under progressive waves; ~O(ε²)",
  "Langmuir circulation; oil spill trajectories; confirmed")

E("Significant Wave Height (Sverdrup-Munk-Bretschneider)", 30, "1947/1977", "Proven",
  "H_s = H_{1/3} ≈ 4√m₀; m₀ = ∫ S(f) df (zeroth spectral moment)",
  "Standard ocean wave statistics; Rayleigh-distributed individual wave heights")

E("Tide-Generating Potential (Equilibrium Theory)", 30, "1775/1897", "Proven",
  "V_tide = −(3/2) GM_⊙ R²/r³ (cos²θ − 1/3); Laplace's tidal equations govern dynamic response",
  "M₂ semidiurnal dominant; Darwin's harmonic analysis of tides")

E("Geostrophic Balance (Ocean Currents)", 30, "1900s", "Proven",
  "f v = (1/ρ) ∂p/∂x; f u = −(1/ρ) ∂p/∂y; f=2Ω sin φ (Coriolis parameter); large-scale flow",
  "All major ocean gyres; Gulf Stream, Kuroshio, Antarctic Circumpolar")
V(eid, "Satellite altimetry matches geostrophic velocities", "TOPEX/Poseidon, Jason series", 1990, "Agreement within 10-20%", "Confirmed")

E("Ekman Transport (Wind-Driven Surface Layer)", 30, "1905", "Proven",
  "M_E = τ_wind / (ρ f); net transport 90° to right of wind (NH); left (SH)",
  "Upwelling/downwelling at coasts; Ekman spiral with depth")
V(eid, "Ekman spiral observed in ice drift (Nansen/Fram)", "Ekman 1905", 1905, "Ice drifts ~20-40° right of wind", "Confirmed")

E("Thermohaline Circulation (Stommel-Arons Model)", 30, "1960", "Proven",
  "Balance of advection, diffusion, and sources/sinks of heat and salt; deep ocean circulation",
  "Global conveyor belt circulation; abyssal flow dynamics")

E("Sverdrup Balance (Wind-Driven Gyre Circulation)", 30, "1947", "Proven",
  "β v = f ∂w/∂z + curl_z(τ)/(ρ); β=df/dy; meridional transport from wind stress curl",
  "Subtropical/subpolar gyre dynamics; confirmed in all ocean basins")
V(eid, "Wind-driven transport matches Sverdrup prediction", "Hydrographic sections", 1960, "Within factor ~2; validated theory", "Confirmed")

E("Munk's Western Boundary Current Theory", 30, "1950", "Proven",
  "A_H ∇⁴ψ − β ∂ψ/∂x = −curl_z(τ)/ρ; lateral friction balances β-effect; Gulf Stream width",
  "Western intensification of boundary currents; Gulf Stream, Kuroshio")
V(eid, "Gulf Stream width ~100 km matches Munk prediction", "Oceanographic surveys", 1950, "First-order agreement", "Confirmed")

E("Sonar Equation (Active, Monostatic)", 48, "1940s", "Proven",
  "SL − 2TL + TS = NL − DI + DT; SL=source level, TL=transmission loss, TS=target strength, NL=noise, DI=directivity index, DT=detection threshold",
  "All active sonar systems; military and scientific")
S(eid, "TL", "Transmission Loss (Spherical + Absorption)", r"TL = 20\log_{10} R + \alpha R", "R=range (m); α=absorption coefficient (dB/m); α∝f² in seawater", "")
V(eid, "Submarine detection ranges match sonar equation", "US Navy, WWII to present", 1945, "Quantitatively confirmed", "Confirmed")

E("Sound Speed in Seawater (UNESCO/IES-80/CTD)", 48, "1980", "Proven",
  "c(S,T,P) = 1449.2 + 4.6T − 0.055T² + 0.00029T³ + (1.34−0.010T)(S−35) + 0.016z",
  "Empirical; c = 1448−1570 m/s in ocean; SOFAR channel at ~1000m")
V(eid, "CTD profile sound speed matches direct measurement", "Oceanographic surveys", 1980, "Within 0.1 m/s", "Confirmed")

E("Acoustic Doppler Current Profiler (ADCP) Principle", 48, "1980s", "Proven",
  "v_radial = (c Δf)/(2 f₀); Doppler shift from scatterers moving with water; 4 beams → 3D velocity",
  "Standard ocean current measurement; thousands of ADCPs deployed globally")

# ================================================================
# 3. ATMOSPHERIC PHYSICS
# ================================================================

E("Hydrostatic Equation (Atmospheric)", 29, "19th c.", "Proven",
  "dp/dz = −ρ g; pressure decreases exponentially with height in isothermal atmosphere",
  "Standard atmosphere; barometric altimetry")
S(eid, "Barometric", "Barometric Altitude Formula", r"p = p_0 \exp\left(-\frac{M g z}{R T}\right)", "Isothermal atmosphere; scale height H=RT/(Mg)≈8.5 km", "p at 5.5 km ≈ ½ p₀")
V(eid, "Pressure altimeter validation", "Aviation standard", 1940, "Within few meters at low altitude", "Confirmed")

E("Ideal Gas Law (Moist Air, Virtual Temperature)", 29, "19th c.", "Proven",
  "p = ρ R_d T_v; T_v = T (1 + 0.608 q); q=specific humidity; virtual temperature correction",
  "Moist atmospheric dynamics; buoyancy calculations")

E("Potential Temperature (Adiabatic Reference)", 29, "19th c.", "Proven",
  "θ = T (p₀/p)^{R_d/c_p}; R_d/c_p ≈ 0.286; conserved under adiabatic vertical displacement",
  "Static stability criterion: ∂θ/∂z > 0 → stable; < 0 → unstable")

E("Brunt-Väisälä Frequency (Atmospheric Stability)", 29, "1920s", "Proven",
  "N² = (g/θ) dθ/dz; buoyancy oscillation frequency; N²>0 → stable oscillation",
  "Gravity wave generation; mountain waves; clear air turbulence")
S(eid, "BVfreq", "Brunt-Väisälä Frequency", r"N = \sqrt{\frac{g}{\theta}\frac{d\theta}{dz}}", "N≈0.01-0.02 s⁻¹ in troposphere; ~0.02 s⁻¹ in stratosphere", "")
V(eid, "Mountain lee waves (Bishop wave, Sierra Nevada)", "Photography + lidar", 1950, "Wavelength ~5-20 km; matches theory", "Confirmed")

E("Geostrophic Wind (Pressure Gradient + Coriolis Balance)", 29, "19th c.", "Proven",
  "u_g = −(1/ρf) ∂p/∂y; v_g = (1/ρf) ∂p/∂x; wind parallel to isobars; f=2Ω sin φ",
  "Large-scale weather systems; wind direction from isobar orientation")
V(eid, "Upper-air radiosonde winds match geostrophic", "Global radiosonde network", 1950, "Within ~10-15° direction, 20-30% speed", "Confirmed")

E("Thermal Wind Equation (Vertical Wind Shear)", 29, "1920s", "Proven",
  "∂u_g/∂z = −(g/fT) ∂T/∂y; ∂v_g/∂z = (g/fT) ∂T/∂x; temperature gradient → wind shear",
  "Jet stream existence explained; frontal zones")
V(eid, "Jet stream at ~10 km with ~100+ knot core matches thermal wind", "Global wind profiles", 1950, "Core height/speed matches mid-latitude temperature gradient", "Confirmed")

E("Rossby Number (Inertial vs Coriolis)", 29, "1939", "Proven",
  "Ro = U/(f L); Ro ≪ 1 → geostrophic; Ro ~ 1 → gradient wind; Ro ≫ 1 → cyclostrophic",
  "Dynamical scaling classification; tornadoes: Ro>1000; hurricanes: Ro~1")

E("Rossby Wave Phase Speed (Planetary Waves)", 29, "1939", "Proven",
  "c = ū − β/k²; β = 2Ω cos φ / R; westward phase speed relative to mean flow",
  "Mid-latitude weather patterns; persistent ridges/troughs; ~3-6 waves around hemisphere")
V(eid, "Hemispheric wave number 3-6 observed in 500mb maps", "NWP model analysis", 1960, "Rossby wave dispersion confirmed", "Confirmed")

E("Clausius-Clapeyron (Water Vapor Saturation Pressure)", 29, "1834", "Proven",
  "de_s/dT = L e_s/(R_v T²); saturated vapor pressure increases ~7%/K near surface",
  "Atmospheric moisture holding capacity; precipitation intensity scaling")
S(eid, "MagnusFormula", "Magnus-Tetens Formula (Saturation Pressure)", r"e_s(T) = 6.112 \exp\left(\frac{17.67\,T}{T+243.5}\right)", "T in °C; e_s in hPa; empirical approximation of C-C", "Accurate within 0.1% for -40<T<50°C")
V(eid, "Humidity sensors verify saturation pressure curves", "Psychrometry, chilled mirror hygrometry", 1950, "Within 0.1 hPa", "Confirmed")

E("Schwarzschild Equation (Radiative Transfer, No Scattering)", 29, "1906/1960s", "Proven",
  "dI_ν/ds = −k_ν ρ I_ν + k_ν ρ B_ν(T); absorption + thermal emission along path",
  "Infrared radiative transfer in atmosphere; greenhouse effect calculation")
V(eid, "Satellite IR radiance matching RT models", "NOAA/GOES/MetOp sounders", 1980, "Within 1K brightness temperature", "Confirmed")

E("Köhler Theory (Cloud Droplet Activation)", 29, "1936", "Proven",
  "S−1 = A/r − B/r³; A=Kelvin term (curvature); B=solute term (Raoult effect); critical supersaturation at r*",
  "CCN activation; cloud microphysics foundation")
S(eid, "CriticalS", "Critical Radius and Supersaturation", r"r^* = \sqrt{\frac{3B}{A}}, \; S^* = \frac{2A}{3r^*}", "r*~0.1-1 μm for typical CCN; S*<0.01-1%", "")
V(eid, "CCN counter measurements match Köhler theory", "Cloud physics laboratory", 1960, "Droplet activation curves confirmed", "Confirmed")

E("Terminal Fall Speed of Cloud/Rain Drops (Stokes/Davies)", 29, "1940s", "Proven",
  "v_t = k · r² (cloud droplets, r<40μm, Stokes regime); v_t = k' · r^{0.5} (rain, r>0.6mm, turbulent)",
  "Precipitation formation; warm rain collision-coalescence")
V(eid, "Drop fall speeds measured in wind tunnels", "Gunn & Kinzer 1949", 1949, "v_t(d) curve experimentally determined", "Confirmed")

E("Mie Scattering (Atmospheric Aerosols, Clouds)", 29, "1908", "Proven",
  "Q_ext, Q_sca, Q_abs as function of size parameter x=2πr/λ and refractive index m",
  "Cloud optical properties; aerosol radiative forcing; lidar")
V(eid, "Mie calculations match laboratory scattering measurements", "Laboratory nephelometers", 1960, "Single-particle scattering confirmed", "Confirmed")

E("Rayleigh Scattering (Molecular Atmosphere)", 29, "1871", "Proven",
  "I_sca ∝ 1/λ⁴; cross-section σ_R ∝ 1/λ⁴; blue sky, red sunsets; polarization patterns",
  "Sky color, atmospheric correction of satellite imagery")
S(eid, "RayleighOD", "Rayleigh Optical Depth", r"\tau_R = 0.008569\,\lambda^{-4}\,(1+0.0113\lambda^{-2}+0.00013\lambda^{-4})", "λ in μm; optical depth from sea level to space", "~0.12 at 550nm; ~0.05 at 800nm")
V(eid, "Sky radiance/polarization measurements", "Atmospheric optics", 1950, "Matches Rayleigh scattering predictions", "Confirmed")

E("Lightning Return Stroke Current (Heidler Function / Bruce-Golde)", 29, "1941/1985", "Proven",
  "i(t) = (I₀/η)((t/τ₁)^n/(1+(t/τ₁)^n)) exp(−t/τ₂); I₀≈10-200 kA; τ₁≈1-2μs, τ₂≈10-100μs",
  "Lightning protection design; EMC standards")
V(eid, "Rocket-triggered lightning current measurements", "Camp Blanding, Florida", 1990, "Direct measurement of current waveform", "Confirmed")

E("Primitive Equations (Numerical Weather Prediction)", 29, "1950s", "Proven",
  "Conservation of momentum (3D), mass (continuity), energy (thermodynamic), moisture, and ideal gas law",
  "Every weather forecast model (GFS, ECMWF, ICON, etc.)")

# ================================================================
# 4. BIOPHYSICS
# ================================================================

E("Nernst Equation (Membrane Equilibrium Potential)", 32, "1888", "Proven",
  "E_ion = (RT/zF) ln([ion]_out/[ion]_in); equilibrium potential for single ion species",
  "Neuronal electrophysiology; all excitable cells")
S(eid, "NernstVals", "Typical Nernst Potentials (Mammalian Neurons at 37°C)", r"E_K = -90\,\text{mV},\; E_{Na} = +60\,\text{mV},\; E_{Cl} = -70\,\text{mV},\; E_{Ca} = +120\,\text{mV}", "", "")
V(eid, "Patch-clamp measurements of reversal potentials", "Neher & Sakmann 1976 (Nobel 1991)", 1976, "Reversal potential matches Nernst for single-channel current", "Confirmed")

E("Goldman-Hodgkin-Katz (GHK) Voltage Equation", 32, "1949", "Proven",
  "V_m = (RT/F) ln[(P_K[K]_o+P_Na[Na]_o+P_Cl[Cl]_i)/(P_K[K]_i+P_Na[Na]_i+P_Cl[Cl]_o)]",
  "Resting membrane potential from multiple permeant ions; V_rest ≈ −70mV")
S(eid, "GHKcurrent", "GHK Current Equation", r"I_X = P_X z_X^2\frac{F^2 V_m}{RT}\frac{[X]_i - [X]_o e^{-z_X F V_m/RT}}{1 - e^{-z_X F V_m/RT}}", "Current for ion species X through open channel; constant-field assumption", "")
V(eid, "Resting potential ~-70mV matches GHK prediction", "Microelectrode recordings", 1950, "±5mV for most neurons", "Confirmed")

E("Hodgkin-Huxley Equations (Action Potential)", 32, "1952", "Proven",
  "C_m dV/dt = −g_K n⁴(V−E_K) − g_Na m³h(V−E_Na) − g_L(V−E_L) + I_stim",
  "Squid giant axon; Nobel 1963; all excitable cell modeling")
S(eid, "HHGates", "Hodgkin-Huxley Gating Variables", r"\frac{dn}{dt}=\alpha_n(1-n)-\beta_n n,\;\frac{dm}{dt}=\alpha_m(1-m)-\beta_m m,\;\frac{dh}{dt}=\alpha_h(1-h)-\beta_h h", "α,β are voltage-dependent rate constants; m=Na activation, h=Na inactivation, n=K activation", "")
V(eid, "Squid giant axon AP shape matches HH model", "Hodgkin & Huxley 1952", 1952, "All AP features (threshold, all-or-none, refractory) reproduced", "Confirmed")

E("FitzHugh-Nagumo Model (Simplified Excitable Dynamics)", 32, "1961/1962", "Proven",
  "dv/dt = v − v³/3 − w + I; dw/dt = ε(v + a − bw); 2-variable reduction of HH",
  "Bifurcation analysis of excitability; pattern formation; cardiac modeling")

E("Cable Equation (Neuronal Dendrite/Axon)", 32, "1950s", "Proven",
  "λ² ∂²V/∂x² = τ_m ∂V/∂t + V; λ=√(r_m/r_i); τ_m=r_m c_m; passive spread along membrane",
  "Synaptic integration in dendrites; Rall's cable theory")
S(eid, "CableParams", "Cable Parameters", r"\lambda = \sqrt{\frac{r_m}{r_i}}, \; \tau_m = r_m c_m", "λ~0.1-1 mm for dendrites; ~1 mm for unmyelinated axon; ~2 cm for myelinated", "")
V(eid, "Dendritic potential attenuation matches cable theory", "Dual patch-clamp recordings", 1990, "Dendritic filtering quantitatively predicted", "Confirmed")

E("Einstein-Smoluchowski Relation (Molecular Motor Stalling Force)", 32, "1905", "Proven",
  "F_stall = k_B T / δ; δ=step size (~8 nm for kinesin); ~6 pN stall force",
  "Single-molecule motor assays; optical trap measurements")
V(eid, "Kinesin stall force ~5-7 pN (optical trapping)", "Block/Schnitzer/Gelles 1990s", 1995, "Matches Einstein relation prediction", "Confirmed")

E("Bell's Model (Bond Rupture Under Force)", 32, "1978", "Proven",
  "k_off(F) = k₀ exp(F γ/k_B T); γ=reactive compliance (~0.1-0.5 nm); slip bond kinetics",
  "Single-molecule force spectroscopy; catch bonds; cell adhesion")
V(eid, "Biotin-streptavidin rupture force distribution matches Bell model", "AFM/optical tweezers force spectroscopy", 2000, "Dynamic force spectroscopy standard", "Confirmed")

E("Hill's Equation (Muscle Force-Velocity Relation)", 32, "1938", "Proven",
  "(F + a)(v + b) = (F₀ + a)b; hyperbola; v_max = F₀ b/a; a,b constants",
  "All striated muscle mechanics; cardiac/skeletal muscle")
V(eid, "Isotonic quick-release experiments in frog sartorius", "Hill 1938", 1938, "Characteristic hyperbolic F-v confirmed", "Confirmed")

E("Huxley Sliding Filament Model (Cross-Bridge Dynamics)", 32, "1957", "Proven",
  "∂n(x,t)/∂t = f(x)[1−n(x,t)] − g(x) n(x,t); n=attached cross-bridge probability; x=distortion",
  "Muscle force generation; all striated muscle; foundational mechanochemical model")
V(eid, "ATPase rate matches cross-bridge cycle predictions", "Biochemical + mechanical assays", 1970, "Coupling between chemistry and force confirmed", "Confirmed")

E("Monod-Wyman-Changeux (MWC) Model (Allosteric Transitions)", 32, "1965", "Proven",
  "L = [T₀]/[R₀]; Y = α(1+α)^{n-1}/(L + (1+α)^n); α=[S]/K_R; cooperative ligand binding",
  "Hemoglobin oxygen binding; many allosteric proteins; ion channel gating")
V(eid, "Hemoglobin O₂ binding curve fit (n_H~2.8)", "Monod/Wyman/Changeux 1965", 1965, "Sigmoidal binding curve explained", "Confirmed")

E("Michaelis-Menten Enzyme Kinetics", 33, "1913", "Proven",
  "v = V_max [S] / (K_m + [S]); K_m = (k_{−1}+k_cat)/k₁; V_max = k_cat [E]_total",
  "All enzyme kinetics; steady-state approximation")
S(eid, "MMeq", "Briggs-Haldane Steady-State", r"v = \frac{k_{cat}[E]_0[S]}{K_m + [S]}, \; K_m = \frac{k_{-1}+k_{cat}}{k_1}", "General case; Michaelis-Menten is special case k_cat≪k_{-1}", "")
V(eid, "Countless enzyme assays confirm MM kinetics", "Biochemistry standard", 1930, "Initial rate vs [S] hyperbolic confirmed", "Confirmed")

E("Transition State Theory (Eyring Equation)", 33, "1935", "Proven",
  "k = (k_B T/h) exp(−ΔG‡/RT) = (k_B T/h) exp(ΔS‡/R) exp(−ΔH‡/RT)",
  "Absolute reaction rate theory; all chemical kinetics")
V(eid, "Activation parameters from temperature-dependent rates", "Eyring/Polanyi 1935", 1935, "ΔH‡, ΔS‡ extracted; linear Eyring plots", "Confirmed")

E("Arrhenius Equation (Chemical Reaction Rate)", 33, "1889", "Proven",
  "k = A exp(−E_a/RT); log₁₀(k₂/k₁) = (E_a/2.303R)(1/T₁−1/T₂); activation energy from T-dependence",
  "Universal in chemical kinetics; 2-4x rate increase per 10K at room T")
V(eid, "Countless reactions verify linear ln(k) vs 1/T", "Chemical kinetics standard", 1900, "Most reactions follow Arrhenius behavior", "Confirmed")

E("Marcus Theory (Electron Transfer Rate)", 33, "1956", "Proven",
  "k_ET = (2π/ℏ) H_AB² (1/√(4πλ k_B T)) exp[−(ΔG⁰+λ)²/(4λ k_B T)]; Nobel 1992",
  "All electron transfer reactions; inverted region λ<−ΔG⁰")
S(eid, "MarcusInvert", "Marcus Inverted Region", r"\ln k \text{ decreases when } |\Delta G^0| > \lambda", "", "Confirmed by Closs/Miller experiments (1984)")
V(eid, "Photoinduced ET in donor-bridge-acceptor molecules confirms Marcus inverted region", "Closs & Miller 1984", 1984, "Bell-shaped ln(k) vs ΔG⁰ confirmed", "Confirmed")

E("Butler-Volmer Equation (Electrode Kinetics)", 33, "1930s", "Proven",
  "j = j₀[exp(α_a F η/RT) − exp(−α_c F η/RT)]; η=overpotential; α_a+α_c≈1",
  "All electrode reactions; charge transfer kinetics")
V(eid, "Tafel slopes for H₂ evolution, O₂ reduction match BV", "Electrode kinetics standard", 1950, "α≈0.5 for many metal electrodes", "Confirmed")

E("Beer-Lambert Law (Spectroscopy)", 34, "1729–1852", "Proven",
  "A = −log₁₀(T) = ε c L; absorbance, molar absorptivity, concentration, path length",
  "All absorption spectroscopy (UV-Vis, IR, etc.)")
V(eid, "Linearity of absorbance vs concentration", "Analytical chemistry standard", 1900, "Over 3-4 orders of magnitude", "Confirmed")

E("Förster Resonance Energy Transfer (FRET) Efficiency", 32, "1948", "Proven",
  "E = R₀⁶/(R₀⁶+r⁶); R₀⁶ ∝ κ² Φ_D J(λ)/n⁴; R₀~1-10 nm",
  "Molecular ruler; protein folding; single-molecule biophysics")
V(eid, "FRET distance measurements correlate with structural models", "Single-molecule TIRF microscopy", 2000, "Angstrom-scale distance discrimination", "Confirmed")

# ================================================================
# 5. PHOTONICS & LASER PHYSICS
# ================================================================

E("Einstein Rate Equations (Laser Dynamics)", 34, "1917/1960", "Proven",
  "dN₂/dt = R_p − B₂₁ ρ(ν) N₂ − A₂₁ N₂; dφ/dt = B₂₁ ρ(ν)(N₂−N₁) c' − φ/τ_c",
  "All laser operation; population inversion; gain/loss balance")

E("Laser Threshold Condition", 34, "1960", "Proven",
  "g_th = α_int + (1/2L) ln(1/R₁R₂); gain must overcome internal loss + mirror transmission",
  "Laser design; all laser types (gas, solid-state, semiconductor, fiber)")
V(eid, "Threshold pump power matches prediction in thousands of laser designs", "Since Maiman 1960", 1960, "Within factor ~2 for simple models", "Confirmed")

E("Schawlow-Townes Linewidth (Fundamental Laser Linewidth)", 34, "1958", "Proven",
  "Δν = (π hν (Δν_c)²)/P_out; quantum-limited linewidth; narrower with higher power",
  "Fundamental limit on laser coherence; Nobel 1981 (Schawlow)")
V(eid, "Linewidth narrowing with increased power", "High-finesse Fabry-Perot, fiber lasers", 1980, "Qualitatively; technical noise often dominates", "Confirmed")

E("Mode-Locking Condition (fs/ps Pulses)", 34, "1960s", "Proven",
  "T_R = 2L/c (round-trip time); f_rep = 1/T_R; N locked modes → τ_p = T_R/N ∝ 1/Δν_gain",
  "Femtosecond lasers; frequency combs (Nobel 2005: Hänsch/Hall)")
S(eid, "FreqComb", "Optical Frequency Comb", r"f_n = n f_{rep} + f_{CEO}", "f_rep=repetition rate; f_CEO=carrier-envelope offset frequency; self-referenced combs", "Nobel Prize in Physics 2005")
V(eid, "Attosecond timing precision in frequency combs", "Hänsch/Hall groups 1990s", 2000, "Precision 10^{-15} for optical clocks", "Confirmed")

E("Nonlinear Polarization (χ^{(n)} Expansion)", 34, "1960s", "Proven",
  "P_i = ε₀[χ^{(1)}_{ij} E_j + χ^{(2)}_{ijk} E_j E_k + χ^{(3)}_{ijkl} E_j E_k E_l + ...]",
  "All nonlinear optics; harmonic generation, parametric processes")
S(eid, "SHG", "Second-Harmonic Generation", r"P^{(2)}_{2\omega} \propto \chi^{(2)} E_\omega E_\omega", "Frequency doubling; requires non-centrosymmetric material; BBO, KTP, LiNbO₃", "")
V(eid, "Franken et al. 1961 first SHG in quartz", "Franken/Hill/Peters/Weinreich 1961", 1961, "First demonstration of nonlinear optics", "Confirmed")

E("Phase-Matching Condition (Nonlinear Optics)", 34, "1962", "Proven",
  "Δk = k_3 − k_2 − k_1 = 0 for SHG; n(2ω)=n(ω) required; birefringent or QPM",
  "Efficient harmonic generation; PPLN, PPKTP for quasi-phase-matching")
V(eid, "Maker fringes (phase-matching signature)", "Maker et al. 1962", 1962, "Oscillatory SHG vs crystal rotation", "Confirmed")

E("Nonlinear Schrödinger Equation (Optical Solitons in Fibers)", 34, "1973", "Proven",
  "i ∂A/∂z − (β₂/2)∂²A/∂t² + γ|A|²A = 0; balance GVD (β₂) and Kerr nonlinearity (γ)",
  "Soliton propagation in fibers; all-optical communication")
S(eid, "Soliton", "Fundamental Soliton Solution", r"A(z,t) = \sqrt{P_0}\, \text{sech}(t/T_0)\, e^{iz/(2L_D)}", "L_D=T₀²/|β₂|; P₀=|β₂|/(γT₀²); L_NL=1/(γP₀)=L_D for N=1 soliton", "")
V(eid, "Soliton propagation over thousands of km in fiber loops", "Mollenauer et al. 1980, Hasegawa prediction", 1980, "Pulse shape preserved over long distances", "Confirmed")

E("Kramers-Kronig Relations (Optical Dispersion)", 34, "1926-27", "Proven",
  "n(ω)−1 = (2/π)P∫₀^∞ ω'κ(ω')/(ω'²−ω²)dω'; causality → real and imaginary parts of χ linked",
  "All linear optical materials; refractive index and absorption intrinsically coupled")
V(eid, "n and k extracted from reflectometry match KK transform", "Ellipsometry, spectroscopy", 1950, "Causality test; confirmed without exception", "Confirmed")

E("Rate Equations for Semiconductor Lasers", 34, "1960s", "Proven",
  "dN/dt = η_i I/qV − R(N) − v_g g(N) N_ph; dN_ph/dt = Γ v_g g(N) N_ph − N_ph/τ_ph + β_sp R_sp",
  "All diode lasers; VCSELs, DFB, FP lasers; threshold, modulation response")

E("Master Equation for Mode-Locked Lasers (Haus)", 34, "1975", "Proven",
  "ΔA = (g−l + jD) A + (g/Ω_g² + jD_g) ∂²A/∂t² + (γ−jδ)|A|²A; Haus master equation",
  "Pulse formation theory; active/passive mode-locking; soliton fiber lasers")

E("Coupled-Mode Theory (Waveguides, Gratings, Resonators)", 34, "1970s", "Proven",
  "da_μ/dz = −j Σ_κ K_μκ a_κ exp[j(β_κ−β_μ)z]; coupling between waveguide/grating modes",
  "DFB/DBR lasers; fiber Bragg gratings; microring resonators; photonic circuits")

# ================================================================
# 6. ATOMIC & MOLECULAR PHYSICS
# ================================================================

E("Zeeman Effect (Normal + Anomalous)", 35, "1896/1925", "Proven",
  "ΔE = μ_B g_J m_J B; g_J = 1 + [J(J+1)+S(S+1)−L(L+1)]/[2J(J+1)]; Landé g-factor",
  "Magnetic field splitting of atomic spectral lines; astrophysical magnetic field diagnostics")
V(eid, "Zeeman effect in solar/stellar spectra", "Hale 1908 (sunspot magnetic fields)", 1908, "Magnetic field strengths derived from Zeeman splitting", "Confirmed")

E("Stark Effect (Linear + Quadratic)", 35, "1913/1920s", "Proven",
  "Linear: ΔE = 3ea₀ n (n₁−n₂) E / 2 (Hydrogen); Quadratic: ΔE = −½ α E² (general)",
  "Electric field splitting; Rydberg atoms; Stark spectroscopy")

E("Hyperfine Structure (Fermi Contact Interaction)", 35, "1930", "Proven",
  "ΔE_HFS = (A/2) [F(F+1) − I(I+1) − J(J+1)]; A ∝ μ_B μ_N ⟨1/r³⟩ |ψ(0)|²",
  "21 cm hydrogen line (1420 MHz); atomic clocks; nuclear moment determination")
S(eid, "HLine", "Hydrogen 21-cm Line", r"\Delta E = \frac{8}{3} g_I \mu_N \mu_B |\psi(0)|^2", "F=1→F=0; 1420.4057517667 MHz; astrophysically crucial for HI mapping", "Cosmic epoch of reionization; Galaxy structure")
V(eid, "21-cm hyperfine line discovered (Ewen/Purcell 1951)", "Ewen & Purcell 1951", 1951, "1420.4 MHz confirmed; standard for radio astronomy", "Confirmed")

E("Born-Oppenheimer Approximation (Molecular Hamiltonian Separation)", 35, "1927", "Proven",
  "Ψ(r,R) ≈ ψ_e(r;R) χ_N(R); electronic Schrödinger eq at fixed nuclear geometry; then nuclear motion",
  "All molecular quantum mechanics; potential energy surfaces; vibronic coupling")
V(eid, "Molecular vibrational frequencies match BO PES calculations", "Spectroscopy + quantum chemistry", 1950, "Within ~1-5% for harmonic frequencies", "Confirmed")

E("Franck-Condon Principle (Vibrational Transition Intensities)", 35, "1925–28", "Proven",
  "I_v'v'' ∝ |∫ ψ_v'* ψ_v'' dR|²; vertical transitions; overlap of vibrational wavefunctions",
  "All molecular electronic spectroscopy; absorption/emission band shapes")

E("Molecular Rotational Spectroscopy (Rigid Rotor)", 35, "1920s", "Proven",
  "E_J = B J(J+1); B = ℏ²/(2I); I = μ R²; ΔJ = ±1 selection rule → 2B spacing",
  "Molecular structure determination; interstellar molecule identification")

E("Molecular Vibrational Spectroscopy (Harmonic)", 35, "1920s", "Proven",
  "E_v = ℏω(v+½); ω = √(k/μ); fundamental transition ν₀ = ω/(2πc)",
  "IR and Raman spectroscopy; functional group identification; chemical analysis")
V(eid, "Vibrational frequencies match DFT predictions", "IR/Raman spectroscopy standard", 1950, "Within 2-5% for harmonic approximation", "Confirmed")

E("Morse Potential (Anharmonic Diatomic)", 35, "1929", "Proven",
  "V(r) = D_e [1 − e^{−a(r−r_e)}]²; analytical eigenvalues E_v = ℏω(v+½)−ℏωx_e(v+½)²",
  "Realistic diatomic potential; dissociation limit included; anharmonicity")
V(eid, "Anharmonic overtones fit Morse progression (HCl, CO, N₂)", "High-resolution IR spectroscopy", 1930, "Within ~1% for v<~10", "Confirmed")

E("Rydberg Formula (Atomic Series Limits)", 35, "1888", "Proven",
  "1/λ = R∞/(n₁+δ₁)² − R∞/(n₂+δ₂)²; R∞=10973731.568157 m⁻¹; δ=quantum defect",
  "All atomic spectral series; quantum defect from core penetration")
V(eid, "Spectral series of alkali atoms (Li, Na, K, Rb, Cs)", "Rydberg/Balmer/Paschen 1880s-1900s", 1890, "Series limits precisely determined", "Confirmed")

E("Racah Algebra (Angular Momentum Coupling in Complex Atoms)", 35, "1940s", "Proven",
  "Wigner 3-j, 6-j, 9-j symbols; recoupling coefficients; matrix elements of tensor operators",
  "Atomic structure theory; f-electron systems; lanthanide/actinide spectroscopy")

# ================================================================
# 7. RHEOLOGY
# ================================================================

E("Newtonian Constitutive Equation (Viscous Fluid)", 36, "1687/1820s", "Proven",
  "τ = μ γ̇; σ = −p I + 2 μ D; D = strain-rate tensor; τ ∝ shear rate linearly",
  "Water, oils, simple liquids; all fluids with constant viscosity")

E("Power-Law Fluid (Ostwald-de Waele Model)", 36, "1920s", "Proven",
  "τ = K γ̇^n; η_app = K γ̇^{n-1}; n<1 → shear-thinning (pseudoplastic); n>1 → shear-thickening; n=1 → Newtonian",
  "Polymer melts, solutions; blood; paints; food products; drilling muds")
V(eid, "Viscosity vs shear rate fits power-law over 2-3 decades", "Rotational rheometry standard", 1950, "Confirmed for thousands of materials", "Confirmed")

E("Bingham Plastic (Yield Stress Fluid)", 36, "1922", "Proven",
  "τ = τ_y + μ_p γ̇ for τ > τ_y; no flow for τ < τ_y",
  "Toothpaste, ketchup, drilling mud, concrete, many soft solids")
V(eid, "Yield stress measured by stress ramp in rheometer", "Rheometry standard", 1980, "τ_y determined from flow curve onset", "Confirmed")

E("Herschel-Bulkley Model (Yield + Power-Law)", 36, "1926", "Proven",
  "τ = τ_y + K γ̇^n for τ > τ_y",
  "Most real yield-stress fluids generalize Bingham; widely used")

E("Carreau-Yasuda Model (Shear-Thinning With Zero/Infinite Limits)", 36, "1972/1979", "Proven",
  "η(γ̇) = η_∞ + (η₀−η_∞)[1 + (λ γ̇)^a]^{(n-1)/a}",
  "Polymer solutions and melts; wide shear-rate range; smooth Newtonian plateau at low γ̇")

E("Maxwell Viscoelastic Model (Liquid)", 36, "1867", "Proven",
  "dε/dt = (1/E) dσ/dt + σ/η; relaxation time τ = η/E; elastic at short times, viscous at long",
  "Polymer melts; simple viscoelastic fluid model")
S(eid, "MaxwellRelax", "Stress Relaxation (Maxwell)", r"\sigma(t) = \sigma_0\,e^{-t/\tau}", "Exponential decay of stress at constant strain; τ = η/E", "")
V(eid, "Stress relaxation in polymer melts follows Maxwell at short times", "Rheometry", 1960, "Exponential decay at moderate strain", "Confirmed")

E("Kelvin-Voigt Model (Viscoelastic Solid)", 36, "1890s", "Proven",
  "σ = E ε + η dε/dt; retardation time = η/E; creep compliance J(t)=[1−e^{−t/τ}]/E",
  "Creep of viscoelastic solids; crosslinked polymers below T_g")

E("Generalized Maxwell / Wiechert Model (Multiple Relaxation Times)", 36, "1890s", "Proven",
  "G(t) = G_∞ + Σ_i G_i exp(−t/τ_i); relaxation spectrum H(τ); Prony series",
  "All real viscoelastic materials; DMA and rheometry analysis")
V(eid, "Prony series fit to DMA master curves", "Dynamic Mechanical Analysis", 1970, "Excellent fit with 5-15 Maxwell elements", "Confirmed")

E("Cox-Merz Rule (Steady vs Dynamic Viscosity Equivalence)", 36, "1958", "Proven",
  "η(γ̇) ≈ |η*(ω)| when γ̇ = ω; empirical equivalence for many polymer melts/solutions",
  "Rheological characterization; connects steady shear and oscillatory measurements")
V(eid, "Cox-Merz holds for linear polymers; fails for structured fluids", "Cox & Merz 1958", 1958, "Verified for most homogeneous polymer melts", "Confirmed")

E("Trouton Ratio (Extensional/Shear Viscosity Ratio)", 36, "1906", "Proven",
  "Tr = η_E / η; Newtonian: Tr=3; viscoelastic: Tr≫3; strain-hardening in extension",
  "Extensional rheology; polymer processing (fiber spinning, blow molding)")

# ================================================================
# 8. TRIBOLOGY
# ================================================================

E("Amontons-Coulomb Friction Laws", 37, "1699/1785", "Proven",
  "F_f = μ N (macroscopic); independent of apparent contact area and sliding speed (approximately)",
  "Macroscopic dry friction; deviations at high speed, low load, or clean surfaces")

E("Archard's Law (Adhesive Wear)", 37, "1953", "Proven",
  "V = k F s / H; k=wear coefficient (~10^{-2} to 10^{-7}); softer material hardness controls",
  "All sliding wear; used for component lifetime prediction")
V(eid, "Wear volume vs sliding distance ± linear; pin-on-disk tests confirm", "Standard tribology testing (ASTM G99)", 1960, "Wear map classification of materials", "Confirmed")

E("Stribeck Curve (Lubrication Regimes)", 37, "1902", "Proven",
  "μ = f(η N/p, roughness, geometry); boundary → mixed → EHL → hydrodynamic as speed increases",
  "Bearing design; all lubricated contacts: journal bearings, cams, gears")
V(eid, "Friction vs Sommerfeld number (ηN/p) confirms Stribeck shape", "Bearing test rigs", 1920, "Characteristic U-shaped curve confirmed", "Confirmed")

E("Reynolds Equation (Thin-Film Lubrication)", 37, "1886", "Proven",
  "∂/∂x[(h³/η)∂p/∂x] + ∂/∂y[(h³/η)∂p/∂y] = 6(U∂h/∂x + 2∂h/∂t)",
  "Hydrodynamic bearing pressure generation; journal & thrust bearings, seals")
V(eid, "Journal bearing pressure profiles match Reynolds equation predictions", "Bearing test rigs with pressure taps", 1930, "Film thickness within 10% of prediction", "Confirmed")

E("Hertzian Contact (Elastic Contact Between Curved Surfaces)", 18, "1882", "Proven",
  "a = (3FR/4E*)^{1/3}; p_max = 3F/(2πa²); E* = [(1−ν₁²)/E₁+(1−ν₂²)/E₂]⁻¹",
  "Ball bearings, gears, wheel-rail contact; maximum contact pressure at center")
S(eid, "HertzPressure", "Hertz Contact Pressure Distribution", r"p(r) = p_{max}\sqrt{1 - (r/a)^2}, \; \tau_{max} \approx 0.31 p_{max} \text{ at } z \approx 0.48 a", "Elliptical pressure distribution; max shear ~0.48a below surface", "Rolling contact fatigue originates at subsurface τ_max")
V(eid, "Contact area vs load matches Hertz prediction", "Photoelastic / pressure-sensitive film experiments", 1940, "Within 5% for elastic contacts", "Confirmed")

E("Elastohydrodynamic Lubrication (EHL) Film Thickness (Hamrock-Dowson)", 37, "1970s", "Proven",
  "h_min/R_x = 3.63 U⁰·⁶⁸ G⁰·⁴⁹ W⁻⁰·⁰⁷³ (1−e^{−0.68k}); U=η₀u/E'R_x, G=αE', W=w/E'R_x²",
  "Gears, rolling bearings; EHL film thickness separates surfaces elastically")
V(eid, "Optical EHL interferometry confirms film thickness formula", "Cameron/Gohar 1960s; Spikes group", 1970, "Within ~20% of Hamrock-Dowson prediction", "Confirmed")

# ================================================================
# 9. GRANULAR MATERIALS
# ================================================================

E("Janssen Effect (Pressure Saturation in Silos)", 38, "1895", "Proven",
  "p(z) = (ρ g D / 4 μ_w K) [1 − exp(−4 μ_w K z/D)]; pressure saturates at finite depth",
  "Silo design; grain storage; Janssen 1895 verified repeatedly")
S(eid, "JanssenStress", "Janssen Saturation Pressure", r"p_\infty = \frac{\rho g D}{4 \mu_w K}", "K=Janssen coefficient (ratio of horizontal/vertical stress); ≈0.3-0.6", "")
V(eid, "Silo pressure measurements confirm saturation", "Full-scale silo instrumentation", 1900, "Pressure plateaus at ~2-3 diameters depth", "Confirmed")

E("Coulomb Yield Criterion (Granular Failure)", 38, "1776", "Proven",
  "τ = σ tan φ + c; φ=internal friction angle (~25-45° for sands); c=cohesion (0 for dry sand)",
  "Soil mechanics; slope stability; granular pile failure; all geotechnical engineering")

E("Angle of Repose (Granular Pile)", 38, "Ancient", "Proven",
  "tan φ_r = H_max / R; φ_r ≈ φ (internal friction angle); ~30-40° for most granular materials",
  "Sand piles, hopper design, avalanche dynamics; empirical")

E("Brazil Nut Effect (Granular Convection/Segregation)", 38, "20th c.", "Proven",
  "Larger particles rise during vibration or shaking due to percolation + convection",
  "Mixing/de-mixing of granular mixtures; pharmaceutical processing; geophysical sorting")
V(eid, "Vibrated granular column: large bead rises to top", "Laboratory granular dynamics", 1990, "Brazil nut effect reproduced under controlled conditions", "Confirmed")

E("Bagnold Scaling (Granular Flow Rheology - Inertial)", 38, "1954", "Proven",
  "τ = a (ρ_p d²) γ̇² (inertial regime); Bagnold number Ba = ρ_p d² γ̇/η_f; Ba>450 → grain inertia dominates",
  "Debris flows, grain flow in chutes, aeolian sand transport")
V(eid, "Shear cell experiments confirm Bagnold scaling at high shear rates", "Granular rheometry", 1980, "τ ∝ γ̇² in inertial regime; τ ∝ γ̇¹ in quasi-static", "Confirmed")

E("μ(I) Rheology (Inertial Number Scaling for Dense Granular Flow)", 38, "2006", "Proven",
  "μ(I) = μ_s + (μ₂−μ_s)/(1+I₀/I); I = γ̇ d/√(p/ρ_p); dimensionless inertial number",
  "Modern dense granular flow rheology; unifies quasi-static and inertial regimes")

# ================================================================
# 10. NANOSCIENCE
# ================================================================

E("Coulomb Blockade Condition (Single-Electron Transistor)", 39, "1980s", "Proven",
  "E_c = e²/(2C_Σ) > k_B T; charging energy must exceed thermal energy for CB to be observed",
  "Single-electron transistors; quantum dots; Coulomb staircase in I-V")
S(eid, "SET", "SET Current — Orthodox Theory", r"I = \text{rate of sequential tunneling when } eV/2 > E_c", "Coulomb blockade at low bias; periodic in gate voltage (Coulomb oscillations)", "")
V(eid, "Coulomb oscillations observed in quantum dots at mK temperatures", "Kastner group (MIT) 1990s", 1990, "Periodic conductance peaks vs gate voltage confirmed", "Confirmed")

E("Landauer Formula (Ballistic Conductance)", 39, "1957/1988", "Proven",
  "G = (2e²/h) Σ T_n; G₀ = 2e²/h ≈ 77.5 μS (~12.9 kΩ); quantized conductance",
  "1D ballistic transport; quantum point contacts; carbon nanotubes; nanowires")
S(eid, "GQ", "Conductance Quantum", r"G_0 = \frac{2e^2}{h} \approx 7.748 \times 10^{-5}\,\text{S} \;\; (R_Q = h/2e^2 \approx 12.9\,\text{k}\Omega)", "Each open mode contributes G₀; spin degeneracy gives factor 2", "")
V(eid, "Quantized conductance steps in QPC (2DEG)", "Van Wees et al. 1988, Wharam et al. 1988", 1988, "Integer steps of G₀ confirmed in GaAs/AlGaAs heterostructures", "Confirmed")

E("Kondo Effect (Resistance Minimum in Dilute Magnetic Alloys)", 39, "1964", "Proven",
  "R ∝ −ln(T) below Kondo temperature T_K; magnetic impurity spin screened by conduction electrons",
  "Kondo insulators; quantum dot Kondo physics; heavy fermion systems")
V(eid, "R vs T minimum in AuFe, CuFe confirmed", "De Haas, Van Den Berg 1930s; Kondo 1964 explained", 1964, "−ln(T) dependence below T_K confirmed", "Confirmed")

E("2D Electron Gas Density of States (Constant)", 39, "1960s", "Proven",
  "g_{2D}(E) = m*/(πℏ²) = constant; independent of energy",
  "GaAs/AlGaAs heterostructures; MOSFET inversion layers; quantum Hall effect")

E("Graphene Dirac Dispersion (Massless 2D Fermions)", 39, "2005", "Proven",
  "E = ± v_F |k|; v_F ≈ 10⁶ m/s; linear dispersion near Dirac points K,K'",
  "Graphene; Nobel 2010 (Geim/Novoselov); half-integer QHE; Klein tunneling")
V(eid, "ARPES measurements confirm linear dispersion in graphene", "Angle-resolved photoemission spectroscopy", 2005, "Dirac cone directly imaged; v_F≈10⁶ m/s", "Confirmed")

E("Quantum Confinement (Infinite Well — Nanowire/Quantum Well)", 39, "1970s", "Proven",
  "E_n = n²π²ℏ²/(2m*L²); 1D wire; 2D well adds E_{n_x,n_y} terms; 0D dot adds all three",
  "Semiconductor nanostructures; blue-shift in optical transitions with decreasing size")
V(eid, "Photoluminescence blue-shift in quantum wells with decreasing thickness", "Molecular beam epitaxy grown QWs", 1980, "Quantized subband energies confirmed", "Confirmed")

E("Casimir Force (Between Ideal Plates, Nanoscale)", 39, "1948", "Proven",
  "F/A = −π²ℏc/(240 d⁴); d=separation; attractive; zero-point EM fluctuations",
  "MEMS/NEMS stiction; nanoscale force metrology; measured to ~1% accuracy")
V(eid, "Casimir force measured within 1% (Lamoreaux 1997, Mohideen/Roy)", "Torsion pendulum / AFM cantilever experiments", 1997, "Force vs d follows theory from ~0.5-6 μm", "Confirmed")

E("DLVO Theory (Colloidal Nanoparticle Stability)", 39, "1940s", "Proven",
  "V_total(d) = V_vdW + V_EDL; van der Waals attraction + electric double-layer repulsion",
  "Nanoparticle dispersion stability; aggregation; protein corona; nanotoxicology")

# ================================================================
# 11. QUANTUM INFORMATION
# ================================================================

E("Single Qubit State (Bloch Sphere)", 40, "1990s", "Proven",
  "|ψ⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩; pure state on Bloch sphere surface",
  "All single quantum bit representations; universal in quantum computing")

E("Bell States (Maximally Entangled Two-Qubit States)", 40, "1964", "Proven",
  "|Φ⁺⟩=(|00⟩+|11⟩)/√2; |Φ⁻⟩=(|00⟩−|11⟩)/√2; |Ψ⁺⟩=(|01⟩+|10⟩)/√2; |Ψ⁻⟩=(|01⟩−|10⟩)/√2",
  "Quantum teleportation; superdense coding; Bell's test; fundamental entanglement resource")
V(eid, "Bell pairs generated via SPDC, trapped ions, superconducting qubits", "Multiple platforms", 2000, "Fidelity >99% in modern quantum computers", "Confirmed")

E("No-Cloning Theorem", 40, "1982", "Proven",
  "An unknown quantum state cannot be copied perfectly; U|ψ⟩|0⟩ ≠ |ψ⟩|ψ⟩ for all |ψ⟩",
  "Fundamental theorem of quantum mechanics; basis for quantum cryptography (BB84)")

E("Holevo Bound (Classical Information From Qubit)", 40, "1973", "Proven",
  "χ ≤ S(ρ) − Σ p_i S(ρ_i); at most 1 classical bit extractable per qubit",
  "Quantum communication capacity limit; quantum key distribution security proof")
V(eid, "QKD systems limited to Holevo bound", "Commercial QKD (ID Quantique, Toshiba, etc.)", 2000, "Never exceeded", "Confirmed")

E("Deutsch-Jozsa Algorithm Speedup", 40, "1992", "Proven",
  "Single-query solution to balanced/constant problem; first clear quantum advantage",
  "Quantum algorithm prototype; extended to Bernstein-Vazirani, Simon's algorithm")

E("Grover's Search Algorithm (Quadratic Speedup)", 40, "1996", "Proven",
  "O(√N) quantum search via amplitude amplification; ~π√N/4 Grover iterations",
  "Unstructured database search; quadratic speedup over classical O(N)")
V(eid, "Grover search demonstrated on small-scale quantum processors", "IBM/Google/IonQ, N=2-8", 2020, "Verified for small problem sizes", "Confirmed")

E("Shor's Factoring Algorithm", 40, "1994", "Proven",
  "Quantum period-finding via QFT → polynomial-time integer factorization; O((log N)³); exponentially faster than classical best known",
  "Threatens RSA/public-key cryptography with large-scale quantum computer; not yet at scale")

E("Concatenated Quantum Error Correction Threshold Theorem", 40, "1996–2005", "Proven",
  "If gate error < p_th (~10⁻² to 10⁻⁴ depending on code), errors can be arbitrarily suppressed",
  "Fault-tolerant quantum computing is theoretically possible; p_th = surface code threshold ~1%")
V(eid, "Quantum error correction demonstrated (Shor code, surface code)", "Google Sycamore, IBM, superconducting circuits", 2020, "Logical error rate suppressed below physical error rate", "Confirmed")

# ================================================================
# 12. NONLINEAR DYNAMICS & CHAOS
# ================================================================

E("Lorenz Equations (Deterministic Chaos)", 41, "1963", "Proven",
  "ẋ = σ(y−x); ẏ = x(ρ−z)−y; ż = xy−β z; σ=10, β=8/3, ρ=28 → strange attractor",
  "First chaotic attractor discovered; weather unpredictability; butterfly effect")
S(eid, "LorenzParams", "Lorenz System Parameters", r"\sigma=10,\; \rho=28,\; \beta=8/3 \rightarrow \text{chaotic regime}", "Critical ρ_c≈24.74 for onset of chaos; Lyapunov exponents λ₁≈0.9, λ₂=0, λ₃≈−14.6", "")
V(eid, "Lorenz attractor realized in analog circuits, lasers, fluid convection", "Multiple experiments since 1970", 1970, "Phase portrait confirmed in diverse physical systems", "Confirmed")

E("Logistic Map (Period-Doubling Route to Chaos)", 41, "1976", "Proven",
  "x_{n+1} = r x_n (1−x_n); period-doubling bifurcations; chaos at r≈3.57; Feigenbaum universality",
  "Population dynamics; universal scaling in nonlinear maps")
S(eid, "Feigenbaum", "Feigenbaum Constants", r"\delta \approx 4.6692016, \; \alpha \approx 2.5029079", "Universality constants for period-doubling cascade", "Discovered by Feigenbaum 1975; verified")
V(eid, "Period doubling observed in Rayleigh-Bénard convection, electronic circuits, lasers", "Libchaber/Maurer 1980s", 1980, "Feigenbaum scaling confirmed in real experiments", "Confirmed")

E("Lyapunov Exponent (Chaos Diagnostic)", 41, "1960s", "Proven",
  "λ = lim_{t→∞} (1/t) ln |δx(t)/δx(0)|; λ>0 → chaos; λ<0 → stable; λ=0 → marginal",
  "Universal measure of sensitive dependence on initial conditions; chaos quantification")

E("KAM Theorem (Kolmogorov-Arnold-Moser)", 41, "1954–62", "Proven",
  "Most invariant tori survive small perturbations if frequency ratio is sufficiently irrational",
  "Solar system stability; plasma confinement in tokamaks; nonlinear oscillator theory")

E("Kuramoto Model (Synchronization of Coupled Oscillators)", 41, "1975", "Proven",
  "θ̇_i = ω_i + (K/N) Σ_j sin(θ_j−θ_i); K>K_c → phase transition to global synchronization",
  "Firefly flashing, pacemaker cells, power grids, Josephson junction arrays")
V(eid, "Synchronization onset at critical coupling (K_c) confirmed in Kuramoto experiments", "Oscillator arrays (chemical, electrical, mechanical)", 1990, "Order parameter abrupt rise at K_c", "Confirmed")

E("Mandelbrot Set (Fractal Geometry)", 41, "1980", "Proven",
  "z_{n+1} = z_n² + c; bounded orbits → c ∈ Mandelbrot set; fractal boundary with infinite complexity",
  "Fractal coastlines, turbulence, galaxy distribution, diffusion-limited aggregation")

# ================================================================
# 13. MEDICAL PHYSICS
# ================================================================

E("Bloch Equations (NMR/MRI Signal)", 42, "1946", "Proven",
  "dM/dt = γ M × B − (M_x î+M_y ĵ)/T₂ − (M_z−M₀)k̂/T₁; relaxation toward equilibrium",
  "All MRI physics; T₁ (spin-lattice) and T₂ (spin-spin) relaxation; image contrast")
S(eid, "MRIsignal", "MRI Signal Equation", r"S \propto \rho\, e^{-TE/T_2}\,(1-e^{-TR/T_1})", "ρ=proton density; TE=echo time; TR=repetition time; T₁,T₂ tissue contrast", "")
V(eid, "MRI contrast matches Bloch equation predictions", "Clinical MRI scanners (1.5T, 3T, 7T)", 1980, "T₁,T₂-weighted imaging standard worldwide", "Confirmed")

E("Larmor Frequency (NMR Precession)", 42, "1946", "Proven",
  "ω₀ = γ B₀; γ_H/2π = 42.577 MHz/T; proton Larmor frequency in clinical MRI",
  "NMR spectroscopy; MRI; magnetic field precision ~10⁻⁹; every MRI and NMR spectrometer")
V(eid, "Proton Larmor frequency verified to ppb precision", "NMR spectrometers since 1950s", 1950, "Chemical shift ~ppm; frequency known to ~10⁻¹⁰", "Confirmed")

E("Beer-Lambert Law (X-ray/γ-ray Attenuation, CT)", 42, "1900s", "Proven",
  "I = I₀ e^{−μx}; μ/p = mass attenuation coefficient; CT: μ(x,y) → Hounsfield units",
  "All X-ray imaging; CT scanner (Hounsfield/Cormack, Nobel 1979, Medicine)")
S(eid, "CT-HU", "Hounsfield Unit Scale", r"HU = 1000 \times \frac{\mu - \mu_{water}}{\mu_{water}}", "Water=0 HU; Air=−1000 HU; Bone=+300 to +3000 HU; Soft tissue ~+20-60 HU", "")
V(eid, "CT reconstruction produces quantitative attenuation maps", "Since Hounsfield 1971", 1971, "Clinical standard; spatial resolution ~0.5 mm", "Confirmed")

E("Radon Transform (CT Image Reconstruction)", 42, "1917/1970s", "Proven",
  "p(s,θ) = ∫_{-∞}^∞ f(s cosθ−t sinθ, s sinθ+t cosθ) dt; projection → 2D image via filtered backprojection",
  "CT, PET, SPECT reconstruction; Radon 1917; used since Hounsfield 1971")

E("Ultrasound Wave Equation (Medical Imaging)", 42, "1940s", "Proven",
  "∂²p/∂t² = c²∇²p; reflection at tissue interfaces (acoustic impedance mismatch Z=ρc)",
  "All medical ultrasound; obstetrics, cardiology, vascular; safe, real-time imaging")
S(eid, "ReflectionCoeff", "Acoustic Impedance Reflection Coefficient", r"R = \left(\frac{Z_2-Z_1}{Z_2+Z_1}\right)^2, \; Z = \rho c", "Soft tissue-bone: R≈0.4; soft tissue-air: R≈0.999 → gel coupling needed", "")
V(eid, "B-mode ultrasound images match anatomical structures", "Clinical ultrasound since 1950s", 1980, "Millimeter-scale resolution at MHz frequencies", "Confirmed")

E("Attenuation of Ultrasound in Tissue", 42, "1950s", "Proven",
  "I(x) = I₀ e^{−α f^n x}; n≈1 for most soft tissues; α≈0.5-1 dB/(cm·MHz)",
  "Penetration depth vs frequency tradeoff; 3-5 MHz for abdominal; 7-15 MHz for superficial")

E("Linear-Quadratic (LQ) Model (Radiation Therapy Cell Survival)", 43, "1980s", "Proven",
  "S = exp(−αD − βD²); α/β ratio ~3 Gy for late-responding (CNS, spinal); ~10 Gy for early-responding/acutely responding; D=total dose",
  "Virtually all radiation oncology treatment planning; fractionation rationale")
S(eid, "BED", "Biologically Effective Dose (BED)", r"BED = D\left(1 + \frac{d}{\alpha/\beta}\right)", "d=fraction size; accounts for fractionation effects; EQD₂=BED/(1+2/(α/β))", "Standard in clinical RT planning")
V(eid, "Tumor control probability vs dose matches LQ model predictions", "Clinical RT dose-response data", 1990, "TCP curves fit LQ in wide dose range", "Confirmed")

E("Bragg Peak (Proton/Ion Beam Depth-Dose)", 43, "1905/1946", "Proven",
  "dE/dx peaks sharply at end of range (Bragg peak); R ∝ E^{1.7−1.8}; sharp distal falloff",
  "Proton/heavy ion therapy; dose conformality superior to photons; spread-out Bragg peak (SOBP)")
V(eid, "Bragg peak in proton beams confirmed and used therapeutically", "Wilson 1946 (proposed), LBL/Harvard/MGH since 1950s", 1970, "Proton therapy centers worldwide (100+)", "Confirmed")

E("Bethe-Bloch Formula (Stopping Power for Charged Particles)", 43, "1930/1933", "Proven",
  "−⟨dE/dx⟩ = K z² (Z/A)(1/β²)[½ ln(2m_e c²β²γ²T_max/I²) − β² − δ(βγ)/2]",
  "Stopping power in any medium; relativistic charged particle energy loss; dE/dx minimum at βγ≈3-4 (minimum ionizing particle, MIP)")
S(eid, "BetheBloch", "Bethe-Bloch", r"-\left\langle\frac{dE}{dx}\right\rangle = K z^2 \frac{Z}{A}\frac{1}{\beta^2}\left[\frac{1}{2}\ln\frac{2m_e c^2\beta^2\gamma^2 T_{max}}{I^2} - \beta^2 - \frac{\delta}{2}\right]", "K=4πN_A r_e² m_e c²≈0.307 MeV·cm²/g; I=mean excitation potential; z=projectile charge", "Valid for β>0.05; δ=density correction at high γ")
V(eid, "Stopping power measurements in gases, solids, tissue-equivalent materials", "Particle physics since 1930", 1960, "Within ~1-3% of Bethe-Bloch; extensively validated tables (ICRU, NIST PSTAR)", "Confirmed")

E("Dosimetry: Cavity Theory (Bragg-Gray / Spencer-Attix)", 43, "1936/1955", "Proven",
  "D_med = (S̄/ρ)_med^wall · D_wall; dose to medium from dose measured in wall/gas cavity",
  "Absolute dosimetry standard; ionization chamber calibration; TG-51, TRS-398 protocols")

E("MIRD Formalism (Internal Dosimetry)", 43, "1968", "Proven",
  "D̄(r_T←r_S) = Ã_S Σ_i Δ_i φ_i(r_T←r_S); Ã_S=cumulated activity; Δ_i=mean energy per transition; φ=fraction absorbed",
  "Nuclear medicine dosimetry; I-131, Lu-177, Y-90 therapy; dose to tumors and organs")
S(eid, "MIRD", "MIRD Dose", r"\bar{D}(r_T \leftarrow r_S) = \tilde{A}_S \sum_i \Delta_i \Phi_i(r_T \leftarrow r_S)", "", "OLINDA/EXM software implements MIRD")

# ================================================================
# 14. ENERGY PHYSICS
# ================================================================

E("Shockley-Queisser Limit (Single-Junction Solar Cell Efficiency)", 44, "1961", "Proven",
  "η_max ≈ 33.7% for E_g=1.34 eV under AM1.5 spectrum (non-concentrated); detailed balance limit",
  "Maximum theoretical PV efficiency; Si (1.12 eV): ~29.4%; GaAs (1.43 eV): ~33%")
V(eid, "Best Si single-junction cell ~26.7% approaches SQ limit", "Kaneka, LONGi, ISFH", 2020, "Record efficiencies within ~80% of SQ limit", "Confirmed")

E("Solar Cell I-V Characteristic (One-Diode Model)", 44, "1960s", "Proven",
  "I = I_ph − I₀ [exp(q(V+IR_s)/nk_B T)−1] − (V+IR_s)/R_sh",
  "All photovoltaic device characterization; R_s=series resistance; R_sh=shunt resistance; n=ideality factor")
V(eid, "PV module I-V curve fitting for performance characterization", "Solar simulator standard (IEC 60904)", 1980, "Standard test conditions (STC): 1000 W/m², AM1.5, 25°C", "Confirmed")

E("Fill Factor (Solar Cell)", 44, "1960s", "Proven",
  "FF = (V_mpp I_mpp)/(V_oc I_sc); η = P_max/P_in = FF · V_oc · J_sc / P_in",
  "Key solar cell performance metric; typically 0.70-0.85 for good cells")

E("Betz Limit (Wind Turbine Maximum Efficiency)", 44, "1920", "Proven",
  "C_p_max = 16/27 ≈ 59.3%; maximum fraction of kinetic power extractable from wind",
  "All wind turbine design; modern turbines achieve C_p≈0.45-0.50")
S(eid, "WindPower", "Wind Power Equation", r"P = \frac{1}{2}\rho A v^3 C_p", "A=swept area; v=wind speed; ρ=1.225 kg/m³ (standard air density)", "")
V(eid, "Wind turbine power curves confirm C_p~0.45-0.50 below rated speed", "Field measurements at wind farms", 1980, "Approaches Betz limit; wake losses reduce farm efficiency", "Confirmed")

E("Rankine Cycle Efficiency (Steam Power Plant)", 44, "1859", "Proven",
  "η = (W_turbine − W_pump)/Q_in ≈ 1 − T_c/T_h (ideal Carnot upper bound, real ~30-45%)",
  "Coal, nuclear, geothermal, CSP power plants; ~90% of world electricity from Rankine cycle")

E("Brayton Cycle Efficiency (Gas Turbine / Jet Engine)", 44, "1872", "Proven",
  "η = 1 − 1/r_p^{(γ−1)/γ}; r_p = compressor pressure ratio; γ = c_p/c_v",
  "Gas turbines, jet engines; combined cycle: Gas + Steam → η>60%")

E("Nernst Equation (Fuel Cell Open-Circuit Voltage)", 44, "1889", "Proven",
  "E_rev = −ΔG/(nF); H₂/O₂ Fuel Cell: E⁰ = 1.229 V at 25°C; actual: E = E_rev − η_act − η_ohm − η_conc",
  "All fuel cells (PEM, SOFC, MCFC); efficiency ~40-60%")
V(eid, "PEM fuel cell OCV measurement", "Fuel cell testing labs", 2000, "OCV typically 0.95-1.0 V (below 1.229V due to H₂ crossover)", "Confirmed")

# ================================================================
# 15. SPACE PHYSICS
# ================================================================

E("Parker Spiral (Interplanetary Magnetic Field)", 45, "1958", "Proven",
  "B_r ∝ 1/r²; B_φ = −B_r (Ω r sin θ)/v_SW; Archimedean spiral angle; v_SW≈400 km/s (slow), ~750 km/s (fast)",
  "Solar wind magnetic field configuration; confirmed by spacecraft in situ measurements")
V(eid, "Parker spiral measured by Ulysses, Wind, ACE spacecraft", "Ulysses (1990-2009), Wind (1994-), ACE (1997-)", 1990, "Spiral field direction confirmed throughout heliosphere", "Confirmed")

E("Chapman-Ferraro Model (Magnetopause Standoff Distance)", 45, "1931", "Proven",
  "Balance of solar wind dynamic pressure with Earth's magnetic pressure: R_MP ~ 10 R_E (subsolar)",
  "Magnetopause shape and location; solar wind dynamic pressure compression")
V(eid, "Magnetopause crossing distances measured by many spacecraft", "ISEE, Cluster, THEMIS, MMS", 1980, "Agreement within ~1R_E of model predictions", "Confirmed")

E("Alfvén Mach Number (Solar Wind — Magnetosphere Coupling)", 45, "1940s", "Proven",
  "M_A = v_SW / v_A; M_A typical solar wind ~5-10; super-Alfvénic flow → bow shock forms",
  "Magnetosphere dynamics; IMF B_z southward → magnetic reconnection → geomagnetic storms")

E("Dungey Cycle (Magnetospheric Convection via Reconnection)", 45, "1961", "Proven",
  "Open flux transport from dayside reconnection → tail lobe → nightside reconnection → return flow (2-cell convection)",
  "Global magnetospheric circulation; Dungey 1961; confirmed by SuperDARN, Cluster, THEMIS")
V(eid, "2-cell ionospheric convection observed by SuperDARN (radar) and DMSP (satellite)", "SuperDARN radar network, DMSP satellites", 1990, "Dungey convection pattern is universal under southward IMF", "Confirmed")

E("Størmer Theory (Charged Particle Motion in Dipole Field)", 45, "1907/1955", "Proven",
  "Allowed/forbidden zones for cosmic ray access; rigidity cutoff P_c = 59.6 cos⁴ λ / r² (GV, dipole approx.)",
  "Cosmic ray access to atmosphere; radiation belt trapping; auroral zones")
V(eid, "Cosmic ray cutoffs verified by balloon and satellite measurements", "AMS-02, PAMELA, balloon campaigns", 1960, "Latitudinal cutoff variation matches Størmer theory", "Confirmed")

E("Radiation Belt Diffusion Equation (Fokker-Planck Approach)", 45, "1960s", "Proven",
  "∂f/∂t = L² ∂/∂L (D_LL L^{-2} ∂f/∂L) + radial diffusion + sources (CRAND, injections) + losses (wave-particle, atmospheric)",
  "Van Allen belt dynamics; radial diffusion coefficient D_LL; wave-particle interactions")

E("Auroral Electron Acceleration (Knight Relation)", 45, "1973", "Proven",
  "j_∥ = K (V − V_c); K = field-aligned conductance; V_c = critical voltage; parallel potential drop above aurora",
  "Discrete auroral arcs; FAST, Freja, Cluster observations confirm field-aligned potentials ~1-10 kV")
V(eid, "FAST satellite: inverted-V electron spectra and parallel potentials", "FAST satellite (1996-2009)", 2000, "Knight relation confirmed for auroral field lines", "Confirmed")

# ================================================================
# 16. DETONICS & SHOCK PHYSICS
# ================================================================

E("Chapman-Jouguet (CJ) Detonation Theory", 46, "1899/1905", "Proven",
  "Detonation products at sonic condition relative to shock front (M=1); Rayleigh line tangent to Hugoniot at CJ point",
  "All steady detonations; explosive performance prediction; detonation velocity D_CJ~1-10 km/s")
S(eid, "CJcondition", "CJ Condition", r"D = u_P + c_P \text{ at CJ plane}", "Sonic flow condition at end of reaction zone; separates steady detonation from wave-follower", "")
V(eid, "TNT detonation velocity ~6.9 km/s at ρ~1.6 g/cm³ matches CJ prediction", "Detonation velocity measurements (streak cameras, PDV, microwave interferometry)", 1950, "Within few % of CJ predictions", "Confirmed")

E("ZND Model (Zeldovich-Von Neumann-Döring Structure)", 46, "1940/1942/1943", "Proven",
  "Lead shock → von Neumann spike (induction zone, no reaction) → reaction zone → CJ plane",
  "Detonation wave internal structure; ignition and growth modeling")

E("Rankine-Hugoniot Relations (General Shock Jump Conditions)", 46, "1870/1887/1889", "Proven",
  "ρ₁ u₁ = ρ₂ u₂; p₁+ρ₁u₁² = p₂+ρ₂u₂²; h₁+½u₁² = h₂+½u₂²; conservation across any shock or detonation front",
  "All shock physics; gas dynamics, solids, liquids, plasma; Hugoniot EOS measurements")
S(eid, "HugoniotEqs", "Hugoniot Jump Conditions", r"\rho_1 u_1 = \rho_2 u_2,\; p_1+\rho_1 u_1^2 = p_2+\rho_2 u_2^2,\; h_1 + \frac{1}{2}u_1^2 = h_2 + \frac{1}{2}u_2^2", "u = particle velocity in shock frame; h = specific enthalpy; material-independent conservation laws", "")
V(eid, "Shock Hugoniot data for thousands of materials", "Gas guns, explosives, laser shocks, Z-machine", 1960, "EOS compilations (SESAME, LEOS) match shock data", "Confirmed")

E("Mie-Grüneisen Equation of State (Solids Under Shock)", 46, "1903/1912", "Proven",
  "p(V,E) = p_ref(V) + (γ(V)/V)[E − E_ref(V)]; γ(V)/V = Grüneisen parameter / volume",
  "Shock-compressed solids; thermal pressure contribution to total EOS")

E("Hopkinson-Cranz (Cube-Root) Blast Scaling Law", 46, "1915/1926", "Proven",
  "R₁/R₂ = (W₁/W₂)^{1/3} at equal overpressure; scaled distance Z = R/W^{1/3}",
  "Blast wave propagation; explosive safety distances; nuclear/conventional blast effects")
S(eid, "ScaledDistance", "Scaled Distance (Sachs Scaling)", r"Z = \frac{R}{W^{1/3}} \text{ or } Z = \frac{R}{E^{1/3}}", "R=distance; W=charge mass; E=energy; ambient pressure and temperature corrections apply (Sachs scaling)", "")
V(eid, "Blast overpressure decay with scaled distance confirmed", "Large-scale blast tests (Operation Sailor Hat, Minor Scale, etc.)", 1960, "Cube-root scaling works over many orders of magnitude", "Confirmed")

E("Taylor-Sedov Blast Wave (Point Explosion, Self-Similar Solution)", 46, "1941/1946", "Proven",
  "R(t) = ξ₀ (E/ρ₀)^{1/5} t^{2/5} (strong shock, spherical); nuclear fireball radius",
  "Nuclear explosions; supernova remnants; laser-produced plasmas; G.I. Taylor 1941, Sedov 1946")
V(eid, "Trinity test fireball radius matches Taylor prediction (E~20 kT TNT)", "Taylor 1950 (declassified photos)", 1950, "Yield estimated to ~10 kT from fireball photos; actual yield ~20 kT", "Confirmed")

# ================================================================
# 17. METAMATERIALS
# ================================================================

E("Veselago's Left-Handed Material Condition", 47, "1968", "Proven",
  "ε < 0 and μ < 0 simultaneously → ñ < 0 (negative index); reversed Snell's law, reversed Doppler, reversed Cherenkov",
  "First theoretical prediction of negative-index materials; Pendry/Smith demonstrated at microwaves 2000")
S(eid, "NegRefraction", "Negative Refraction (Snell's Law Generalized)", r"n_1 \sin\theta_1 = -|n_2| \sin\theta_2", "For μ<0,ε<0; wave vector k, Poynting vector S, and phase velocity form left-handed triad", "")
V(eid, "Negative refraction at microwave frequencies (Pendry, Smith 2000)", "Smith et al. 2000, Shelby et al. 2001", 2001, "Prism experiment confirms n<0 for split-ring resonator + wire array", "Confirmed")

E("Pendry's Perfect Lens (Subwavelength Imaging)", 47, "2000", "Proven",
  "n = −1, μ = ε = −1 → amplifies evanescent waves → subwavelength resolution; no diffraction limit",
  "Superlens concept; limitations from losses, fabrication; experimental realizations with silver films")

E("Transformation Optics (Cloaking / Invisibility)", 47, "2006", "Proven",
  "g'^{μν} = Λ^μ_α Λ^ν_β g^{αβ} where Λ relates virtual to physical space; coordinate transformation → anisotropic ε,μ",
  "First demonstrated at microwaves (Schurig et al. 2006, cylindrical cloak); carpet cloaks (Liu/Zhang); broadband limitations")
V(eid, "Cylindrical invisibility cloak at microwaves (10 GHz)", "Schurig et al. Science 2006", 2006, "Reduced scattering for TM-polarized microwaves", "Confirmed")

E("Effective Medium Theory (Maxwell Garnett / Bruggeman)", 47, "1904/1935", "Proven",
  "MG: (ε_eff−ε_h)/(ε_eff+2ε_h) = f (ε_i−ε_h)/(ε_i+2ε_h); Bruggeman: f(ε_i−ε_eff)/(ε_i+2ε_eff) + (1−f)(ε_h−ε_eff)/(ε_h+2ε_eff)=0",
  "Composite/metamaterial homogenization; plasmonic nanoantenna arrays; anisotropic metamaterials")

# ================================================================
# 18. ENGINEERING PHYSICS
# ================================================================

E("NTU-Effectiveness Method (Heat Exchanger Design)", 49, "1950s", "Proven",
  "ε = Q/Q_max; NTU = UA/C_min; ε = f(NTU, C_r, flow arrangement); C_r = C_min/C_max",
  "All heat exchanger analysis; parallel-flow, counter-flow, cross-flow configurations")
S(eid, "CounterFlow", "Counter-Flow Heat Exchanger Effectiveness", r"\varepsilon = \frac{1 - \exp[-NTU(1-C_r)]}{1 - C_r\exp[-NTU(1-C_r)]}", "For C_r<1; ε→1 as NTU→∞ (balanced flow: ε=NTU/(1+NTU))", "")
V(eid, "Heat exchanger test data matches NTU method", "Industrial heat exchanger testing", 1960, "Standard design method (Kays and London 1955)", "Confirmed")

E("Natural Frequency of a Cantilever Beam", 49, "1750", "Proven",
  "f_n = (β_n L)²/(2π L²) √(EI/ρA); β₁L=1.875, β₂L=4.694, β₃L=7.855 for cantilever",
  "All structural dynamics; AFM cantilevers; MEMS resonators; building vibration modes")
V(eid, "AFM cantilever resonance frequencies match Euler-Bernoulli prediction", "AFM calibration standard", 1990, "Within 2-5% of beam theory", "Confirmed")

E("PID Control Law (Feedback Control)", 49, "1922/1940s", "Proven",
  "u(t) = K_p e(t) + K_i ∫₀ᵗ e(τ)dτ + K_d de/dt; e(t)=setpoint − measurement",
  "90%+ of all industrial control loops; temperature, pressure, flow, position control globally")
V(eid, "PID controllers universally deployed in industry", "Since pneumatic controllers 1930s, electronic 1950s, digital 1980s", 1940, "Stable regulation confirmed in countless systems", "Confirmed")

E("Nyquist Stability Criterion", 49, "1932", "Proven",
  "N = Z − P; encirclements of −1 point determine closed-loop stability from open-loop transfer function",
  "All feedback control system stability analysis; frequency-domain design")
V(eid, "Amplifier and control system stability margins verified", "Bode 1940s, Nyquist 1932", 1940, "Gain/phase margins derived from Nyquist/Bode plots", "Confirmed")

# ================================================================
# 19. BONUS ROUND: Everything else I missed
# ================================================================

E("Young-Laplace Equation (Capillary Pressure, Droplets/Bubbles)", 25, "1805", "Proven",
  "Δp = γ (1/R₁ + 1/R₂); Δp = 2γ/R (spherical); Δp = 4γ/R for soap bubble (2 interfaces)",
  "Every droplet, bubble, meniscus, capillary rise phenomenon; pore capillarity")

E("Kelvin Equation (Curvature + Vapor Pressure)", 25, "1871", "Proven",
  "ln(P/P_sat) = 2γ V_m/(r R T); concave meniscus (r<0) → condensation below P_sat",
  "Capillary condensation in pores; BET surface area; humidity effects in porous media")

E("Washburn Equation (Capillary Rise Dynamics)", 25, "1921", "Proven",
  "h(t) = √(γ R cos θ t/(2η)); Lucas-Washburn; √t dependence for capillary imbibition",
  "Inkjet printing; paper absorption; oil recovery; microfluidics; paper-based diagnostics")

E("Poiseuille Law (Microfluidic Channel Flow)", 36, "1840", "Proven",
  "Q = (Δp w h³)/(12 η L) [1 − 0.63 h/w] for rectangular channel (h≪w); ~h³ dependence",
  "All microfluidic chip design; lab-on-a-chip; MEMS flow sensors; biomedical diagnostics")

E("Stribeck Curve — Empirical Friction-Speed-Load Relation", 37, "1902", "Proven",
  "μ = μ_b + (μ_h−μ_b) / [1 + (η N/p)^m]; boundary → mixed → hydrodynamic transition",
  "Bearing selection; gearbox design; tribology standard")

E("Zener-Hollomon Parameter (Hot Deformation)", 21, "1944", "Proven",
  "Z = ε̇ exp(Q/RT); flow stress σ = f(Z); Z unifies temperature and strain-rate effects",
  "Hot working of metals; creep; high-temperature deformation mechanisms")
V(eid, "σ vs log Z linear for many alloys at elevated T", "Hot compression testing", 1960, "Constitutive modeling of hot rolling/forging", "Confirmed")

E("Ashby Deformation Mechanism Maps", 21, "1972", "Proven",
  "σ/G vs T/T_m plot with boundaries between plasticity, power-law creep, diffusional flow, etc.",
  "Material selection in engineering design; rate-controlling mechanism identification")

E("Tabor Parameter (Indentation Representative Strain)", 21, "1951", "Proven",
  "ε_rep ≈ 0.2 tan β; β = indenter angle; uniaxial stress-strain relation from hardness",
  "Inverse problem: extract σ-ε curve from spherical indentation; confirmed by FEA")

E("Lode Parameter (Stress Triaxiality for Ductile Fracture)", 21, "1926", "Proven",
  "η = σ_m/σ_v; σ_m=hydrostatic stress; σ_v=von Mises stress; η>1/3 needed for void growth",
  "Ductile fracture models; GTN (Gurson-Tvergaard-Needleman) porous plasticity")

E("Dislocation Density Evolution (Kocks-Mecking Model)", 21, "1970s", "Proven",
  "dρ/dε = k₁ √ρ − k₂ ρ; storage (hardening) vs dynamic recovery (annihilation); Stage II→III",
  "Work hardening theory; Kocks-Mecking 1976 (Kocks 1976, Mecking-Kocks 1981)")

E("Bauschinger Effect (Kinematic Hardening)", 21, "1881", "Proven",
  "Yield stress in reverse loading lower than forward loading; dislocation back-stress accumulation",
  "Cyclic plasticity; ratcheting; springback in sheet metal forming")

E("Schottky Diode I-V (Thermionic Emission Model)", 23, "1938", "Proven",
  "J = A* T² exp(−qφ_Bn/k_B T) [exp(qV/k_B T)−1]; A* = Richardson constant modified for effective mass",
  "All Schottky diodes; rectifying metal-semiconductor contacts; MESFETs")

E("Solar Cell Quantum Efficiency (External/Internal)", 44, "1960s", "Proven",
  "EQE(λ) = (J_sc(λ)/q) / Φ(λ); IQE(λ) = EQE(λ) / (1−R(λ)−T(λ))",
  "Solar cell characterization; IQE reveals collection efficiency losses; standard measurement")

E("Detailed Balance Limit (Tandem/Multijunction Solar Cells)", 44, "1980s", "Proven",
  "η_max → 45.7% (2-junction), 51.3% (3-junction), 68.2% (infinite junctions) at 1 sun; ~86.8% at max concentration",
  "Multijunction solar cell theoretical limits; record: 47.1% (6-junction, 2020, NREL/Fraunhofer ISE)")

E("Tandem Solar Cell Current-Matching Condition", 44, "1990", "Proven",
  "J_sc_top = J_sc_bottom (series-connected); otherwise limited by lower subcell current",
  "All multijunction PV design; spectral splitting alternative to relax current-matching")

E("Thermoelectric Figure of Merit (ZT)", 44, "1909/1950s", "Proven",
  "ZT = S² σ T / κ; S=Seebeck coefficient; σ=electrical conductivity; κ=thermal conductivity",
  "TE cooler/generator performance; ZT~1 commercially (Bi₂Te₃); ZT>2 in nanostructured/layered materials")
S(eid, "TEefficiency", "Thermoelectric Generator Max Efficiency", r"\eta_{\max} = \frac{T_h - T_c}{T_h}\frac{\sqrt{1+ZT_{avg}}-1}{\sqrt{1+ZT_{avg}}+T_c/T_h}", "Carnot × material factor; ZT_{avg}=average over temp range", "")
V(eid, "Radioisotope thermoelectric generators (RTG) in space", "NASA (Voyager, Cassini, Curiosity, Perseverance)", 1970, "Multi-decade operation confirmed; Pu-238 heat source", "Confirmed")

E("Seebeck Effect (Thermoelectric Voltage)", 44, "1821", "Proven",
  "ΔV = −∫ S(T) dT; V_oc = S ΔT for small ΔT; S∝k_B/e (≈86 μV/K per k_B/e)",
  "All thermocouples; TE generators; heat flux sensors")

E("Peltier Effect (Thermoelectric Heat Pumping)", 44, "1834", "Proven",
  "Q̇ = Π I; Π = S T (Kelvin relation); heat absorbed/released at junction",
  "Thermoelectric cooling; Peltier modules; laser diode temperature stabilization")

E("Electrochemical Overpotential Components (Fuel Cell/Battery)", 44, "1930s", "Proven",
  "V_cell = E_rev − η_act − η_ohm − η_conc; η_act from Butler-Volmer; η_ohm=IR; η_conc=(RT/nF)ln(1−j/j_L)",
  "Polarization curve of all electrochemical energy devices; batteries, fuel cells, electrolyzers")

E("Peukert's Law (Battery Capacity vs Discharge Rate)", 44, "1897", "Proven",
  "C = I^k t (k>1 for lead-acid, k≈1.1-1.3); capacity decreases at higher discharge rates",
  "All battery discharge characterization; empirical but widely applicable")

E("Ragone Plot (Energy vs Power Density)", 44, "1968", "Proven",
  "Specific energy (Wh/kg) vs specific power (W/kg); batteries, fuel cells, capacitors, flywheels occupy different regions",
  "Energy storage technology comparison; fundamental to device selection")

E("Magnetorheological Fluid (Bingham Plastic with Field-Dependent Yield)", 36, "1940s", "Proven",
  "τ = τ_y(B) + η γ̇; yield stress controllable via applied magnetic field; ~50-100 kPa max",
  "MR dampers in automotive suspensions, seismic protection, prosthetics")

E("Electrorheological Fluid (Field-Dependent Viscosity)", 36, "1947", "Proven",
  "η(E) = η₀ + α E^n; viscosity increases with electric field; Winslow effect",
  "ER clutches, valves; haptic devices; active vibration control; limited industrial use")

E("Phononic Crystal Band Gap (Bragg Scattering of Sound)", 47, "1990s", "Proven",
  "Ω(k+G)=Ω(k); periodic elastic constants → band gaps for acoustic/elastic waves",
  "Acoustic isolation; waveguide design; thermophononic crystals for thermal conductivity control")
V(eid, "Acoustic band gap measured in periodic composite plates", "Laser ultrasonics", 2000, "Band gap frequencies match Bloch mode calculations", "Confirmed")

print(f"Added {len(eqs)} equations (total: {eid})")
print(f"Added {len(subs)} sub-equations")
print(f"Added {len(vers)} verifications")

# ================================================================
# EXECUTE INSERTS
# ================================================================
cur.executemany("INSERT INTO equations VALUES (?,?,?,?,?,?,?,?)", eqs)
cur.executemany("INSERT INTO sub_equations (id, equation_id, subsection, name, latex_formula, description, conditions) VALUES (?,?,?,?,?,?,?)", subs)
cur.executemany("INSERT INTO verifications (id, equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?,?)", vers)

conn.commit()

# Stats
cur.execute("SELECT d.name, COUNT(e.id) FROM domains d LEFT JOIN equations e ON e.domain_id=d.id GROUP BY d.id ORDER BY d.id")
print("\nALL DOMAIN COUNTS:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("SELECT COUNT(*) FROM equations");  total_eq = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM sub_equations"); total_sub = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM verifications"); total_ver = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM open_problems"); total_op = cur.fetchone()[0]
print(f"\nTOTALS: {total_eq} equations, {total_sub} sub-formulas, {total_ver} verifications, {total_op} open problems, {did_val+23} domains")

conn.close()
