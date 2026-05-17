# Proven Equations of the Universe
> Equations that have withstood every experimental probe. None are "exact" — each has a known domain of validity — but within those domains they are unfalsified to extraordinary precision.

---

## 1. Maxwell's Equations (Electromagnetism, 1861–1865)

### 1.1 The Four Equations (Heaviside–Hertz Form)

**Differential form (SI units):**

```
∇ · E  =  ρ / ε₀                Gauss's law (electric)
∇ · B  =  0                      Gauss's law (magnetic) — no magnetic monopoles
∇ × E  =  −∂B / ∂t              Faraday-Lenz law of induction
∇ × B  =  μ₀J  +  μ₀ε₀ ∂E/∂t   Ampère's law with Maxwell's displacement current
```

**Integral form:**

```
∮_S E·dA  =  Q_enc / ε₀
∮_S B·dA  =  0
∮_C E·dl  =  −d/dt ∫_S B·dA
∮_C B·dl  =  μ₀ I_enc  +  μ₀ε₀ d/dt ∫_S E·dA
```

**Relativistic (covariant) form — tensor notation:**

```
∂_μ F^{μν}  =  μ₀ J^ν              inhomogeneous equations
∂_μ F̃^{μν}  =  0                    homogeneous (Bianchi identity)

F_{μν}  =  ∂_μ A_ν  −  ∂_ν A_μ     field strength tensor

F̃^{μν}  =  (1/2) ε^{μνρσ} F_{ρσ}   dual tensor

F_{μν}  =  ⌈  0     −E_x/c  −E_y/c  −E_z/c ⌉
           | E_x/c    0      −B_z     B_y  |
           | E_y/c   B_z      0      −B_x  |
           ⌊ E_z/c  −B_y     B_x      0   ⌋
```

### 1.2 Scalar and Vector Potentials

```
B  =  ∇ × A                     magnetic field from vector potential
E  =  −∇φ  −  ∂A/∂t            electric field from scalar + vector potentials

A^μ  =  (φ/c, A)                4-potential
F_{μν}  =  ∂_μ A_ν  −  ∂_ν A_μ
```

**Gauge invariance:** The fields E, B are unchanged under:

```
A_μ → A_μ + ∂_μ Λ(x)           arbitrary scalar function Λ
φ  → φ − ∂Λ/∂t
A  → A + ∇Λ
```

**Gauge choices:**
```
Coulomb gauge:          ∇ · A = 0
Lorenz gauge:           ∂_μ A^μ = 0        (1/c² ∂φ/∂t + ∇·A = 0)
Temporal gauge:         φ = 0
```

### 1.3 Lagrangian Formulation

```
ℒ_EM  =  −¼ F_{μν} F^{μν}  −  J^μ A_μ

S_EM  =  ∫ d⁴x ℒ_EM
δS = 0  →  ∂_μ F^{μν} = μ₀ J^ν      (Euler-Lagrange)
```

Coupled to matter: replace `∂_μ → D_μ = ∂_μ + i e A_μ` (minimal coupling, QED).

### 1.4 Wave Equation and Speed of Light

From Maxwell's equations in vacuum (ρ = 0, J = 0):

```
∇² E  −  (1/c²) ∂²E/∂t²  =  0
∇² B  −  (1/c²) ∂²B/∂t²  =  0

c  =  1 / √(μ₀ε₀)  =  299,792,458 m/s   (exact, defines meter)
```

Maxwell's displacement current term `μ₀ε₀ ∂E/∂t` was the theoretical prediction that electromagnetic waves exist and travel at `c`. Hertz confirmed it in 1887.

### 1.5 Poynting's Theorem (Energy Conservation)

```
∂u/∂t  +  ∇ · S  =  −J · E

u  =  (1/2) ε₀ E²  +  (1/2μ₀) B²         energy density (J/m³)
S  =  (1/μ₀) E × B                         Poynting vector (W/m², energy flux)

S^μ  =  (u c, S)                           energy-momentum 4-vector
∂_μ S^μ = −F^{μν} J_ν                      covariant form
```

**Electromagnetic momentum:**
```
p_EM  =  ∫ ε₀ (E × B) dV  =  ∫ S/c² dV
```

### 1.6 Polarization, Permittivity, Permeability in Media

**Constitutive relations:**
```
D  =  ε₀ E  +  P  =  ε E         (ε = ε_r ε₀, permittivity tensor)
H  =  B/μ₀  −  M  =  B/μ         (μ = μ_r μ₀, permeability tensor)
J  =  σ E                          (Ohm's law, conductivity)

∇ · D  =  ρ_free
∇ · B  =  0
∇ × E  =  −∂B/∂t
∇ × H  =  J_free  +  ∂D/∂t
```

### 1.7 Radiation: Lienard-Wiechert Potentials

Retarded potentials for a point charge `q` with trajectory `r_q(t)`:

```
φ(r, t)  =  (q / 4πε₀) [1 / (R − R·v/c)]_ret
A(r, t)  =  (μ₀ q / 4π) [v / (R − R·v/c)]_ret

R  =  r − r_q(t_ret)
t_ret  =  t − |R|/c                    retarded time
```

**Lienard-Wiechert fields:**
```
E  =  (q/4πε₀) [ (R̂−v/c)(1−v²/c²) / γ²R²(1−R̂·v/c)³  +  R̂×((R̂−v/c)×a) / c²R(1−R̂·v/c)³ ]_ret

  └── velocity field (Coulomb + SR correction) ──┘  └── acceleration field (radiation) ──┘

B  =  (R̂/c) × E
```

**Larmor formula (non-relativistic radiation power):**
```
P  =  (q² a²) / (6πε₀ c³)         (J/s = W)
```

**Liénard formula (relativistic generalization):**
```
P  =  (q² γ⁶ / 6πε₀ c³) [a² − (v × a)²/c²]
```

**Radiation reaction (Abraham-Lorentz force):**
```
F_rad  =  (q² / 6πε₀ c³) d³r/dt³      (pathological — pre-acceleration)
```

### 1.8 Electrodynamic Stress-Energy Tensor

```
Θ^{μν}  =  (1/μ₀) [F^μ_α F^{να}  +  (1/4) g^{μν} F_{αβ} F^{αβ}]

Θ^{00}  =  u                           energy density
Θ^{0i}  =  S^i / c                     momentum density (×c)
Θ^{ij}  =  −ε₀ E_i E_j − (1/μ₀) B_i B_j + (1/2) δ_{ij} (ε₀E² + B²/μ₀)   Maxwell stress tensor
```

**Radiation pressure on a perfect absorber:** `P = I/c` where `I = |S|`.

### 1.9 Green's Function for the Wave Equation

```
(∇² − (1/c²) ∂²/∂t²) G(r,t; r',t')  =  −δ³(r−r') δ(t−t')

G_ret(r,t; r',t')  =  δ(t − t' − |r−r'|/c) / (4π|r−r'|)        retarded
G_adv(r,t; r',t')  =  δ(t − t' + |r−r'|/c) / (4π|r−r'|)        advanced
```

General solution for potentials with source `f(r,t)`:
```
ψ(r,t)  =  ∫ d³r' dt' G(r,r'; t,t') f(r', t')
```

### 1.10 Experimental Verification

| Test | Precision | Status |
|------|-----------|--------|
| Coulomb's law (inverse square) | `1/r^{2±δ}` with δ < 10⁻¹⁶ | Confirmed |
| Photon mass limit | m_γ < 10⁻¹⁸ eV/c² | Confirmed |
| Magnetic monopole | None detected | Absence confirmed |
| Displacement current | Hertz experiment, all radio | Confirmed |
| c = 1/√(μ₀ε₀) | Measured to 10⁻⁹ | Confirmed |
| Poynting vector | Energy balance in every antenna | Confirmed |
| Lienard-Wiechert | Synchrotron radiation, undulators | Confirmed |
| Abraham-Lorentz | Qualitative features in laser-plasma | Confirmed (limited precision) |

**Domain:** Classical electromagnetism. Valid for field strengths ≪ Schwinger limit (`E_c = m²c³/eℏ ≈ 1.3×10¹⁸ V/m`). Unifies electricity, magnetism, and optics. **Every electronic device, radio, laser, and MRI machine is a continuous experimental verification.**

---

## 2. Einstein Field Equations (General Relativity, 1915)

### 2.1 Fundamental Equation

```
G_{μν}  +  Λ g_{μν}  =  (8πG / c⁴) T_{μν}

G_{μν}  =  R_{μν}  −  ½ R g_{μν}              Einstein tensor
R_{μν}  =  R^ρ_{μρν}                            Ricci tensor
R      =  g^{μν} R_{μν}                         Ricci scalar (curvature scalar)
```

**Trace-reversed form:**
```
R_{μν}  =  (8πG/c⁴) [T_{μν} − ½ g_{μν} T]  +  Λ g_{μν}
T      =  g^{μν} T_{μν}
```

### 2.2 Riemann Curvature Tensor

```
R^ρ_{σμν}  =  ∂_μ Γ^ρ_{νσ}  −  ∂_ν Γ^ρ_{μσ}  +  Γ^ρ_{μλ} Γ^λ_{νσ}  −  Γ^ρ_{νλ} Γ^λ_{μσ}

Γ^ρ_{μν}  =  ½ g^{ρλ} (∂_μ g_{νλ} + ∂_ν g_{μλ} − ∂_λ g_{μν})     Christoffel symbols
```

**Symmetries of Riemann (in 4D, 20 independent components):**
```
R_{ρσμν}  =  −R_{σρμν}  =  −R_{ρσνμ}  =  R_{μνρσ}           (antisymmetries)
R_{ρσμν}  +  R_{ρμνσ}  +  R_{ρνσμ}  =  0                    (Bianchi identity, algebraic)
∇_λ R_{ρσμν}  +  ∇_ν R_{ρσλμ}  +  ∇_μ R_{ρσνλ}  =  0       (Bianchi identity, differential)
```

Contracting to Einstein tensor:
```
∇^μ G_{μν}  =  0          →  ∇^μ T_{μν} = 0      (conservation of stress-energy)
```

### 2.3 Geodesic Equation (Motion in Curved Spacetime)

```
d²x^μ/dτ²  +  Γ^μ_{αβ} dx^α/dτ · dx^β/dτ  =  0

τ  =  proper time:  dτ²  =  −g_{μν} dx^μ dx^ν

For a test mass (T^{μν} = 0 elsewhere):
∇_u u  =  0                     u^μ = dx^μ/dτ is 4-velocity
```

**Equivalence principle:** In a freely falling frame, `g_{μν} → η_{μν}` and `Γ → 0` locally → SR physics.

### 2.4 Einstein-Hilbert Action

```
S  =  (c⁴ / 16πG) ∫ d⁴x √(−g) (R − 2Λ)  +  S_matter

g  =  det(g_{μν})

δS/δg^{μν} = 0  →  G_{μν} + Λ g_{μν} = (8πG/c⁴) T_{μν}

T^{μν}  =  (2 / √(−g)) δS_matter / δg_{μν}
```

**Gibbons-Hawking-York boundary term:**
```
S_total  =  S_EH  +  S_GHY

S_GHY  =  (c⁴ / 8πG) ∫_{∂M} d³y √(|h|) ε K

K      =  extrinsic curvature of boundary
ε      =  ±1 (timelike/spacelike boundary)
h      =  induced metric on boundary
```
Necessary for a well-posed variational principle with fixed boundary metric.

### 2.5 Palatini (First-Order) Formalism

Treat `g_{μν}` and `Γ^ρ_{μν}` as independent variables:
```
S_Palatini  =  (c⁴/16πG) ∫ d⁴x √(−g) g^{μν} R_{μν}(Γ)

δS/δΓ  →  Γ = Levi-Civita connection   (metric compatibility)
δS/δg   →  Einstein field equations
```
In vacuum GR, this is equivalent to the standard formulation. Extended to Einstein-Cartan theory with torsion.

### 2.6 Linearized Gravity and Gravitational Waves

**Perturbation expansion:** `g_{μν} = η_{μν} + h_{μν}` with `|h_{μν}| ≪ 1`.

**Trace-reversed perturbation:**
```
h̄_{μν}  =  h_{μν}  −  ½ η_{μν} h                h = η^{μν} h_{μν}
```

**Linearized Einstein equations (Lorenz gauge ∂^μ h̄_{μν} = 0):**
```
□ h̄_{μν}  =  −(16πG/c⁴) T_{μν}

□  =  η^{μν} ∂_μ ∂_ν  =  −(1/c²) ∂²/∂t² + ∇²
```

**Gravitational wave in TT gauge (transverse-traceless):**
```
h_{μν}^{TT}  =  [ 0   0       0       0    ]  e^{i(kz − ωt)}
                 [ 0  h_+    h_×      0    ]
                 [ 0  h_×   −h_+      0    ]
                 [ 0   0       0       0    ]

h_+  =  plus polarization     (stretches/squeezes along x,y axes)
h_×  =  cross polarization    (stretches/squeezes at 45°)
```

### 2.7 Quadrupole Formula (Gravitational Radiation)

Energy carried away by gravitational waves:
```
dE/dt  =  (G / 5c⁵) Σ_{i,j} ⟨d³Q_{ij}/dt³ · d³Q_{ij}/dt³⟩

Q_{ij}  =  ∫ d³x ρ(x) (x_i x_j − (1/3) δ_{ij} r²)    mass quadrupole moment
```

**Luminosity (full formula):**
```
L_GW  =  (G/5c⁵) ⟨Q̈_{ij} Q̈^{ij}⟩

For a binary system (masses M₁, M₂, separation a):
L_GW  =  (32/5) (G⁴/c⁵) (M₁² M₂² (M₁+M₂) / a⁵)
```

LIGO first detection (GW150914, 2015-09-14): two ~30 M_⊙ black holes merging at ~1.3 billion ly. Peak luminosity ~3.6×10⁴⁹ W — briefly outshining the entire observable universe.

**Orbital decay (binary inspiral):**
```
dE_orb/dt  =  −L_GW  →  da/dt  ∝  −1/a³  →  "chirp" frequency increase

f_GW  =  (c³ / G) [(5/256) (M_chirp/c²)^{-5/3} (t_coal − t)^{-3/8}]^{3/8}

M_chirp  =  (M₁ M₂)^{3/5} / (M₁+M₂)^{1/5}           chirp mass
```

### 2.8 Exact Solutions

**Schwarzschild metric (1916) — static, spherical, vacuum (Λ=0):**
```
ds²  =  −(1 − r_s/r) c² dt²  +  dr²/(1 − r_s/r)  +  r² dΩ²

r_s   =  2GM / c²                          Schwarzschild radius
dΩ²   =  dθ²  +  sin²θ dφ²

Event horizon at r = r_s.
Coordinate singularity at r = r_s (removable by Kruskal-Szekeres coordinates).
Physical singularity at r = 0.
```

**Kerr metric (1963) — rotating, stationary, axisymmetric:**
```
ds²  =  −(1 − r_s r/Σ) c² dt²  +  (Σ/Δ) dr²  +  Σ dθ²
        +  (r² + a² + r_s r a² sin²θ/Σ) sin²θ dφ²  −  (2 r_s r a sin²θ/Σ) c dt dφ

Σ     =  r²  +  a² cos²θ
Δ     =  r²  −  r_s r  +  a²
a     =  J / Mc                                 spin parameter (m)
J     =  angular momentum

Event horizons at r_± = (r_s/2) ± √((r_s/2)² − a²)
Ergosphere: region between r_+ and static limit where no observer can remain stationary.
Penrose process extracts energy from ergosphere (up to ~29% of rest mass for extreme Kerr a→r_s/2).
```

**Kerr-Newman metric — charged rotating black hole:**
```
Same form as Kerr with Δ = r² − r_s r + a² + r_Q²
r_Q²  =  G Q² / (4πε₀ c⁴)
```

**Reissner-Nordström metric — charged, non-rotating:**
```
ds²  =  −(1 − r_s/r + r_Q²/r²) c² dt²  +  dr²/(1 − r_s/r + r_Q²/r²)  +  r² dΩ²

Two horizons for Q < M (in geometric units).
Extremal black hole: r_s = 2r_Q → degenerate horizon.
```

**FLRW metric (Friedmann-Lemaître-Robertson-Walker) — homogeneous, isotropic cosmology:**
```
ds²  =  −c² dt²  +  a²(t) [ dr²/(1 − k r²)  +  r² dΩ² ]

k  =  +1 (closed/spherical),  0 (flat/Euclidean),  −1 (open/hyperbolic)
a(t) = scale factor
```

**de Sitter space — vacuum with Λ > 0:**
```
ds²  =  −(1 − Λr²/3) c² dt²  +  dr²/(1 − Λr²/3)  +  r² dΩ²

Static patch. Horizon at r = √(3/Λ).
Exponential expansion: a(t) ∝ exp( H t ),  H = c √(Λ/3).
```

### 2.9 ADM Formalism (3+1 Decomposition)

Split spacetime into foliation of spacelike hypersurfaces Σ_t:
```
ds²  =  −N² c² dt²  +  γ_{ij} (dx^i + N^i c dt)(dx^j + N^j c dt)

N      =  lapse function       (rate of proper time vs coordinate time)
N^i    =  shift vector         (shift of spatial coordinates between slices)
γ_{ij} =  3-metric on Σ_t
```

**Hamiltonian constraint:**
```
R(³)  +  K²  −  K_{ij} K^{ij}  =  16πG/c⁴ · ρ

K_{ij} = (1/2N)(∂_t γ_{ij} − D_i N_j − D_j N_i)    extrinsic curvature
R(³)   = Ricci scalar of γ_{ij}
ρ      = energy density measured by Eulerian observer
```

**Momentum constraint:**
```
D_j (K^{ij} − γ^{ij} K)  =  8πG/c⁴ · J^i
```

These are elliptic constraint equations solved on each slice. Evolution equations are hyperbolic.

### 2.10 Post-Newtonian Approximation

Expand for slow motion, weak field: `(v/c) ∼ ε`, `GM/rc² ∼ ε²`.

```
1PN order:      corrections of order ε² to Newtonian
2PN order:      ε⁴, etc.

Full equations of motion for binary systems known to 4PN order.
```

Essential for LIGO/Virgo template waveforms, pulsar timing (e.g., Hulse-Taylor binary PSR B1913+16 — orbital decay matches GR prediction to <0.2%).

### 2.11 Experimental Verification

| Test | Experiment | Precision | Status |
|------|-----------|-----------|--------|
| Perihelion precession (Mercury) | Optical astrometry | 43"/century, <0.1% | Confirmed |
| Light deflection (Eddington 1919) | Solar eclipse, VLBI | 0.01% today | Confirmed |
| Gravitational redshift | Pound-Rebka (1960), GPS, ACES | 10⁻⁵ (Pound), 10⁻⁶ (GP-A) | Confirmed |
| Shapiro time delay | Viking, Cassini | 10⁻⁵ | Confirmed |
| Frame-dragging (Lense-Thirring) | Gravity Probe B, LAGEOS | ~10% | Confirmed |
| Gravitational waves | LIGO/Virgo (2015+) | SNR > 20 in loud events | Confirmed |
| Black hole shadow | Event Horizon Telescope (2019) | 40 μas resolution | Confirmed |
| Equivalence principle | MICROSCOPE (2022) | 10⁻¹⁵ | Confirmed |
| Binary pulsar orbital decay | PSR B1913+16, PSR J0737-3039 | 0.2% | Confirmed |
| Strong-field tests | LIGO ringdown, EHT | Ongoing | Passed so far |

**Domain:** Classical gravity = spacetime curvature. Tested from ~10⁻⁴ m to ~10²⁶ m (cosmological). Breaks down at Planck scale (~10⁻³⁵ m) where quantum effects become non-negligible.

---

## 3. Schrödinger Equation (Non-relativistic Quantum Mechanics, 1926)

### 3.1 Time-Dependent and Time-Independent Forms

```
iℏ ∂/∂t |ψ⟩  =  Ĥ |ψ⟩                       time-dependent Schrödinger equation

Ĥ  =  −(ℏ²/2m) ∇²  +  V(r, t)               Hamiltonian operator

Ĥ ψ_n(r)  =  E_n ψ_n(r)                      time-independent (stationary state)
|ψ(t)⟩  =  e^{−iĤt/ℏ} |ψ(0)⟩                time evolution (unitary)
```

**Probability interpretation (Born rule):**
```
ρ(r, t)  =  |ψ(r, t)|²  =  ψ* ψ              probability density
∫ d³r |ψ|²  =  1                               normalization (conserved)
```

**Probability current:**
```
j  =  (ℏ / 2mi) (ψ* ∇ψ  −  ψ ∇ψ*)            probability flux

∂ρ/∂t  +  ∇ · j  =  0                        continuity equation
```

### 3.2 Canonical Commutation Relations

```
[x̂_i, p̂_j]  =  iℏ δ_{ij}                          fundamental quantization postulate
p̂  =  −iℏ ∇                                        momentum operator in position rep.
[x̂_i, x̂_j]  =  [p̂_i, p̂_j]  =  0

[x̂, p̂_x^n]  =  iℏ n p̂_x^{n-1}
[p̂, f(x̂)]   =  −iℏ df/dx

Δx Δp  ≥  ℏ/2                                       Robertson-Schrödinger uncertainty

Generalized:  ΔA ΔB  ≥  (1/2) |⟨[Â, B̂]⟩|            for any Hermitian operators
```

### 3.3 Harmonic Oscillator (Exact Solution)

```
Ĥ  =  p̂²/(2m)  +  (1/2) m ω² x̂²

E_n  =  ℏω (n + 1/2)           n = 0, 1, 2, ...

Zero-point energy E₀ = ½ ℏω    (measurable — Casimir effect, quantum optics)
```

**Ladder operators (Dirac method):**
```
â   =  √(mω/2ℏ) x̂  +  i p̂ / √(2mℏω)          annihilation
â†  =  √(mω/2ℏ) x̂  −  i p̂ / √(2mℏω)          creation

[â, â†]  =  1
Ĥ  =  ℏω (â† â + 1/2)  =  ℏω (N̂ + 1/2)

N̂ |n⟩  =  n |n⟩            number operator
â† |n⟩ = √(n+1) |n+1⟩
â |n⟩  = √n |n−1⟩
|n⟩    = (â†)^n / √(n!) |0⟩
```

**Wavefunctions:**
```
ψ_n(x)  =  (1 / √(2^n n!)) · (mω/πℏ)^{1/4} · H_n(√(mω/ℏ) x) · e^{−mωx²/2ℏ}
```

### 3.4 Hydrogen Atom (Exact Solution)

```
Ĥ  =  −(ℏ²/2μ) ∇²  −  e²/(4πε₀ r)            μ = m_e m_p / (m_e+m_p) reduced mass

E_n  =  −(μ e⁴ / 32π² ε₀² ℏ²) · 1/n²  =  −R_y / n²

R_y  =  13.605693122994 eV              Rydberg energy (CODATA 2018)

Bohr radius:  a₀  =  4πε₀ ℏ² / (μ e²)  ≈  5.29177210903×10⁻¹¹ m
```

**Quantum numbers:**
```
n  =  1, 2, 3, ...                      principal
l  =  0, 1, ..., n−1                    orbital angular momentum
m_l = −l, ..., +l                       magnetic
m_s = ±½                                spin

Degeneracy: 2n² per principal level (including spin).
```

**Spherical harmonics Y_l^m(θ,φ):**
```
ψ_{nlm}(r,θ,φ)  =  R_{nl}(r) Y_l^m(θ,φ)

R_{nl}(r)  ∝  (2r/na₀)^l L_{n−l−1}^{2l+1}(2r/na₀) e^{−r/na₀}
```

### 3.5 Angular Momentum Algebra

```
L̂  =  r̂ × p̂                                   orbital angular momentum operator

[L̂_i, L̂_j]  =  iℏ ε_{ijk} L̂_k
[L², L̂_i]   =  0

L² |l,m⟩  =  ℏ² l(l+1) |l,m⟩
L_z |l,m⟩  =  ℏ m |l,m⟩

Spin-½ (S) = Pauli matrices:
σ_x = [0  1]   σ_y = [0  −i]   σ_z = [1   0]
      [1  0]         [i   0]         [0  −1]

Ŝ_i  =  (ℏ/2) σ_i

[σ_i, σ_j]  =  2i ε_{ijk} σ_k
{σ_i, σ_j}  =  2 δ_{ij} I

Total angular momentum: Ĵ = L̂ + Ŝ
Addition: |l−s| ≤ j ≤ l+s
```

### 3.6 Density Matrix and Mixed States

```
ρ̂  =  Σ_k p_k |ψ_k⟩⟨ψ_k|                   density operator (mixed state)
Tr[ρ̂]  =  1

⟨Â⟩  =  Tr[ρ̂ Â]                              expectation value

iℏ ∂ρ̂/∂t  =  [Ĥ, ρ̂]                        von Neumann (Liouville-von Neumann) equation

Pure state: ρ̂² = ρ̂,  Tr[ρ̂²] = 1
Mixed state: Tr[ρ̂²] < 1

Reduced density matrix: ρ̂_A = Tr_B[ρ̂_AB]     for subsystems
```

### 3.7 Ehrenfest Theorem (Quantum-Classical Bridge)

```
d/dt ⟨A⟩  =  (1/iℏ) ⟨[Â, Ĥ]⟩  +  ⟨∂Â/∂t⟩

For position and momentum:
d⟨x⟩/dt  =  ⟨p⟩/m
d⟨p⟩/dt  =  −⟨∇V(x̂)⟩               quantum Newton's 2nd law

Only equals classical if V varies slowly over ψ-packet width.
```

### 3.8 Time-Independent Perturbation Theory

**Non-degenerate — first order:**
```
Ĥ = Ĥ₀ + λ Ŵ

E_n^{(1)}  =  ⟨ψ_n^{(0)}|Ŵ|ψ_n^{(0)}⟩
|ψ_n^{(1)}⟩  =  Σ_{k≠n} [⟨ψ_k^{(0)}|Ŵ|ψ_n^{(0)}⟩ / (E_n^{(0)}−E_k^{(0)})] |ψ_k^{(0)}⟩
```

**Second order energy:**
```
E_n^{(2)}  =  Σ_{k≠n} |⟨ψ_k^{(0)}|Ŵ|ψ_n^{(0)}⟩|² / (E_n^{(0)}−E_k^{(0)})
```

**Degenerate case:** Diagonalize Ŵ in degenerate subspace.
```
det[⟨ψ_{n,i}^{(0)}|Ŵ|ψ_{n,j}^{(0)}⟩ − E^{(1)} δ_{ij}]  =  0
```

### 3.9 WKB Approximation (Semiclassical)

```
ψ(x)  ∼  (C/√p(x)) exp(± i/ℏ ∫ p(x') dx')

p(x)  =  √(2m(E − V(x)))

Connection formula at turning point (x_t where p(x_t)=0):
ψ(x) matches exponentially decaying → oscillatory or vice versa.

Bohr-Sommerfeld quantization:
∮ p dx  =  2πℏ (n + γ)          n = 0,1,2,...   γ = Maslov index
```

### 3.10 Scattering Theory

**Lippmann-Schwinger equation:**
```
|ψ^{(+)}⟩  =  |φ⟩  +  (E − Ĥ₀ + iε)^{-1} V̂ |ψ^{(+)}⟩

|φ⟩ = incident plane wave
```

**Scattering amplitude and differential cross-section:**
```
dσ/dΩ  =  |f(θ,φ)|²

Partial wave expansion (spherically symmetric potential):
f(θ)  =  (1/k) Σ_{l=0}^∞ (2l+1) e^{iδ_l} sin δ_l  P_l(cos θ)

k  =  √(2mE)/ℏ
δ_l = phase shift

σ_total  =  (4π/k²) Σ_{l=0}^∞ (2l+1) sin² δ_l
```

**Born approximation (first-order):**
```
f(θ,φ)  =  −(2m/ℏ²) · (1/4π) ∫ d³r e^{−i q·r} V(r)

q  =  k_final  −  k_initial            momentum transfer
```

### 3.11 Variational Principle

```
E_0  ≤  ⟨ψ_trial|Ĥ|ψ_trial⟩ / ⟨ψ_trial|ψ_trial⟩       for any trial function

δ[⟨ψ|Ĥ|ψ⟩ − E⟨ψ|ψ⟩]  =  0                               Euler-Lagrange → exact SE
```

Ritz method: expand `|ψ⟩ = Σ c_i |φ_i⟩` → generalized eigenvalue problem `H c = E S c`.

### 3.12 Quantum Tunneling

```
Transmission coefficient (WKB):
T  ≈  exp( −2/ℏ ∫_{x₁}^{x₂} √(2m(V(x)−E)) dx )       for E < V_max

Gamow factor in α-decay:
T  ∼  exp( −2π Z₁ Z₂ e² / (4πε₀ ℏ v) )

Explains Geiger-Nuttall law (α-decay half-life vs energy).
```

### 3.13 Experimental Verification

| Test | System | Precision | Status |
|------|--------|-----------|--------|
| Hydrogen spectrum | Balmer, Lyman, etc. | 10⁻¹⁰ (1S-2S transition) | Confirmed |
| Harmonic oscillator | Trapped ions, molecular vibrations | ~10⁻⁴ | Confirmed |
| Tunneling | STM, α-decay, tunnel diodes | Qualitative + quantitative | Confirmed |
| Scattering | Cross-section measurements | Percent level | Confirmed |
| Born rule | Double-slit, quantum eraser | Countless experiments | Confirmed |
| Superposition | SQUIDs, trapped ions, molecules | Decoherence timescale confirmed | Confirmed |
| Zero-point energy | Casimir effect | <1% | Confirmed |
| Entanglement | Bell-test violations > 40σ | > 40σ | Confirmed |

**Domain:** All non-relativistic quantum systems (v ≪ c, particle number conserved). Extends seamlessly to Schrödinger field theory (many-body QM) and, with second quantization, to non-relativistic QFT. **Not a single experimental counterexample.**

---

## 4. Dirac Equation (Relativistic Spin-½, 1928)

### 4.1 Fundamental Equation

```
(iℏ γ^μ ∂_μ  −  mc) ψ  =  0

γ^μ matrices satisfy:  {γ^μ, γ^ν}  =  γ^μ γ^ν + γ^ν γ^μ  =  2 g^{μν} I₄

g^{μν}  =  diag(−1, +1, +1, +1)               west-coast (mostly-minus) metric
g^{μν}  =  diag(+1, −1, −1, −1)               east-coast / Bjorken-Drell
```

**Feynman slash notation:** `∂̸ = γ^μ ∂_μ`, `p̸ = γ^μ p_μ`, etc.

**Conjugate spinor:**
```
ψ̄  =  ψ† γ⁰
```

**Lagrangian:**
```
ℒ_Dirac  =  ψ̄ (iℏ c ∂̸ − mc²) ψ
```

### 4.2 Gamma Matrix Representations

**Dirac (standard) representation:**
```
γ⁰  =  [ I   0 ]       γ^i  =  [  0    σ_i ]
        [ 0  −I ]               [ −σ_i   0  ]

γ⁵  =  i γ⁰ γ¹ γ² γ³  =  [ 0  I ]
                            [ I  0 ]
```

**Weyl (chiral) representation:**
```
γ⁰  =  [ 0  −I ]       γ^i  =  [  0   σ_i ]
        [ −I  0 ]               [ −σ_i  0  ]

γ⁵  =  [ I   0 ]
        [ 0  −I ]              (diagonal — eigenstates are chirality eigenstates)
```

**Majorana representation:** All γ^μ purely imaginary → real solutions possible.

### 4.3 Plane Wave Solutions

**Positive-energy (particle) spinors:**
```
ψ^{(+)}(x)  =  u^{(s)}(p) e^{−i p·x/ℏ}

u^{(s)}(p)  =  √(E+mc²) [ φ^{(s)}                ]      E = +√(p²c² + m²c⁴)
                          [ σ·p̂ c / (E+mc²) φ^{(s)} ]

φ^{(1)} = [1]    φ^{(2)} = [0]                   2-spinor basis
           [0]              [1]
```

**Negative-energy (antiparticle) spinors:**
```
ψ^{(−)}(x)  =  v^{(s)}(p) e^{+i p·x/ℏ}

v^{(s)}(p)  =  √(E+mc²) [ σ·p̂ c / (E+mc²) η^{(s)} ]
                          [ η^{(s)}                  ]

where η^{(s)} = iσ² φ^{(s)*}
```

**Normalization:** `ū^{(r)} u^{(s)} = 2mc δ_{rs}`, `Σ_s u^{(s)} ū^{(s)} = p̸ + mc`.

### 4.4 Discrete Symmetries

**Parity (P):**
```
P ψ(t, r) P^{-1}  =  γ⁰ ψ(t, −r)

Spinor bilinear transformation: ψ̄ψ → +ψ̄ψ (scalar), ψ̄γ⁵ψ → −ψ̄γ⁵ψ (pseudoscalar)
```

**Charge conjugation (C):**
```
C ψ C^{-1}  =  i γ² ψ*

C  =  i γ² γ⁰  (in Dirac rep.)
C^{-1} γ^μ C  =  −(γ^μ)^T

Majorana condition: ψ = ψ^C ≡ C ψ̄^T  (particle = own antiparticle)
```

**Time reversal (T):**
```
T ψ(t, r) T^{-1}  =  γ¹ γ³ ψ(−t, r)    (antiunitary)

T i T^{-1} = −i
```

**CPT Theorem:** The combined CPT transformation is an exact symmetry of any local, Lorentz-invariant QFT. Violation of CPT has never been observed. Limits: mass difference `|m_K⁰ − m_K̄⁰|/m_K < 10⁻¹⁸`.

### 4.5 Bilinear Covariants

16 independent 4×4 matrices → 16 bilinear forms, classified by Lorentz transformation:

```
Scalar:         ψ̄ ψ                    (1 component)
Pseudoscalar:   ψ̄ γ⁵ ψ                 (1)
Vector:         ψ̄ γ^μ ψ                (4)
Axial-vector:   ψ̄ γ^μ γ⁵ ψ             (4)
Tensor:         ψ̄ σ^{μν} ψ             (6)    σ^{μν} = (i/2)[γ^μ, γ^ν]
─────────────────────────────────────────
Total:          16 independent bilinears
```

**Gordon decomposition (current):**
```
ψ̄ γ^μ ψ  =  (i/2m) [ψ̄ ∂^μ ψ − (∂^μ ψ̄) ψ]  +  (1/m) ∂_ν (ψ̄ σ^{μν} ψ)

         └── convection current ──┘        └── spin current ──┘
```

### 4.6 Non-Relativistic Reduction (Pauli Equation)

Expand in powers of `v/c`:

```
iℏ ∂ψ/∂t  =  [ (p − eA)²/2m  +  eφ  −  (eℏ/2m) σ·B  −  (p⁴/8m³c²)  +  ... ] ψ

Pauli spin term:  −μ · B  with  μ = (eℏ/2m) σ = g_s (eℏ/4m) σ,  g_s = 2
```

### 4.7 Relativistic Hydrogen Fine Structure

Iterating the reduction yields:

```
ΔE_{FS}  =  (R_y α²/n³) [ 1/(j+½)  −  3/(4n) ]

Fine structure constant: α = e²/(4πε₀ ℏc) ≈ 1/137.035999084

Term         Formula                       Origin
─────        ───────                       ──────
Relativistic  −(α²R_y/n³) (n/(l+½)−3/4)   kinetic energy expansion
Spin-orbit    +(α²R_y/n³) [j(j+1)−l(l+1)−3/4] / [2l(l+½)(l+1)]   Ŝ·L coupling
Darwin        +(α²R_y/n³) δ_{l0}            zitterbewegung smearing
```

**Lamb shift (2S_{1/2} − 2P_{1/2} in hydrogen):**
```
ΔE_Lamb  ≈  1057.8 MHz  ≈  4.37 μeV

From QED radiative corrections (vacuum polarization + electron self-energy).
Measured by Lamb & Retherford (1947) — confirmed QED as correct relativistic QFT.
```

### 4.8 Electron g-Factor and Anomalous Magnetic Moment

```
μ  =  g (eℏ/4m) σ/2

g_Dirac  =  2                          exactly, from Dirac equation

g_exp / 2  =  1.00115965218091(26)      CODATA 2018

a_e  =  (g−2)/2  measured to 3×10⁻¹³

QED prediction:
a_e^{QED}  =  α/2π  −  0.328478... (α/π)²  +  1.181241... (α/π)³  −  1.912... (α/π)⁴  +  ...

Agreement: 1 part in 10¹² — the most precisely tested prediction in physics.
```

### 4.9 Weyl Equation (Massless Fermions)

```
iℏ σ^μ ∂_μ ψ_L  =  0      (left-handed Weyl spinor)
iℏ σ̄^μ ∂_μ ψ_R  =  0      (right-handed)

σ^μ  =  (I, σ_i)             σ̄^μ  =  (I, −σ_i)

Chirality = helicity for massless particles:
Left-handed (ψ_L): spin antiparallel to momentum
Right-handed (ψ_R): spin parallel to momentum
```

Neutrinos were long thought massless Weyl fermions. Neutrino oscillations → nonzero mass → beyond-minimal SM.

### 4.10 Klein Paradox

For a potential step `V > 2mc²`, the reflection coefficient `|R|² > 1` in single-particle Dirac theory. Resolution: QFT pair production — the potential creates electron-positron pairs. No violation of unitarity in QED.

### 4.11 Experimental Verification

| Test | Precision | Status |
|------|-----------|--------|
| Electron g−2 | 3×10⁻¹³ | Matches QED+EW+hadronic |
| Positron existence | Anderson 1932 | Confirmed |
| Fine structure in hydrogen | ~10⁻¹⁰ | Confirmed |
| Lamb shift | ~10⁻⁶ | Confirmed |
| Antiparticle properties | m_ē = m_e to < 10⁻¹² | Confirmed |
| CPT symmetry | Kaon mass difference < 10⁻¹⁸ | Confirmed |
| Zitterbewegung | Observable in trapped-ion simulations | Confirmed (simulated) |

**Domain:** Relativistic spin-½ particles (all quarks and leptons). The foundation of fermionic QFT.

---

## 5. Newton's Laws of Motion (1687)

### 5.1 The Three Laws

```
1st Law (Inertia):    An object at rest stays at rest, and an object in motion stays in motion
                      with constant velocity, unless acted upon by a net external force.

2nd Law:              F  =  dp/dt  =  d(mv)/dt          (general form)
                      F  =  m a                           (constant mass)

3rd Law:              F_{A→B}  =  −F_{B→A}              (action = reaction, equal & opposite)
```

### 5.2 Relativistic Generalization

```
dp^μ/dτ  =  F^μ                          4-force = proper time derivative of 4-momentum

p^μ  =  m u^μ  =  (γmc, γmv)             4-momentum
u^μ  =  dx^μ/dτ  =  (γc, γv)             4-velocity, dt/dτ = γ

F^μ  =  γ (F·v/c, F)                     relation between 3-force and 4-force

For constant mass in SR:
F  =  d(γmv)/dt  =  γ³ m a_∥  +  γ m a_⊥     (transverse mass γm, longitudinal γ³m)
```

### 5.3 Lagrangian and Hamiltonian Mechanics (Generalized Newton)

**Principle of least action:**
```
S[q]  =  ∫_{t₁}^{t₂} L(q, q̇, t) dt
δS  =  0   →   Euler-Lagrange equations

d/dt (∂L/∂q̇_i)  −  ∂L/∂q_i  =  0           for each generalized coordinate
```

**For a particle:** `L = T − V = ½ m q̇² − V(q)` → `m q̈ = −dV/dq = F`.

**D'Alembert's principle (virtual work):**
```
Σ_i (F_i − ṗ_i) · δr_i  =  0                virtual displacements δr_i consistent with constraints

→  leads to Lagrange's equations for constrained systems.
```

**Hamilton's equations:**
```
H(q, p, t)  =  p_i q̇_i  −  L               Legendre transform
p_i  =  ∂L/∂q̇_i                               canonical momentum

q̇_i   =  ∂H/∂p_i
ṗ_i    =  −∂H/∂q_i

dH/dt  =  ∂H/∂t                              (conserved if H has no explicit t-dependence)
```

**Poisson bracket formulation:**
```
{A, B}_PB  =  Σ_i (∂A/∂q_i · ∂B/∂p_i  −  ∂A/∂p_i · ∂B/∂q_i)

df/dt  =  {f, H}_PB  +  ∂f/∂t              time evolution of any phase-space function
```

### 5.4 Rigid Body Dynamics (Euler's Equations)

```
I dω/dt  +  ω × (I ω)  =  τ                Euler's equations for rigid body rotation

I = inertia tensor (3×3), τ = torque vector

In principal axes (I = diag(I₁, I₂, I₃)):
I₁ ω̇₁  −  (I₂−I₃) ω₂ ω₃  =  τ₁
I₂ ω̇₂  −  (I₃−I₁) ω₃ ω₁  =  τ₂
I₃ ω̇₃  −  (I₁−I₂) ω₁ ω₂  =  τ₃
```

**Angular momentum:** `L = I ω`, `dL/dt = τ`.

**Poinsot's theorem:** Torque-free motion — angular velocity vector precesses in body frame around the angular momentum vector.

### 5.5 Continuum Mechanics (Cauchy's Stress Principle)

```
ρ d²u/dt²  =  ∇ · σ  +  f_body                         (Cauchy momentum equation)

∂σ_{ij}/∂x_j  +  f_i  =  ρ ü_i                           (index form)

σ = stress tensor (Pa), u = displacement vector
```

Specialize to:
- **Elastic solids:** `σ = C : ε` (Hooke's law generalized — stiffness tensor)
- **Fluids:** `σ = −p I + μ(∇v + ∇v^T) + λ (∇·v) I` (Newtonian constitutive relation → Navier-Stokes)
- **Electrodynamics:** `σ_{ij}^{EM} = −ε₀E_iE_j − (1/μ₀)B_iB_j + ½δ_{ij}(ε₀E²+B²/μ₀)` (Maxwell stress)

### 5.6 Conservation Laws from Newton's Laws

```
Momentum conservation:     dP/dt  =  F_ext            (Σ forces = rate of change of total momentum)
Angular momentum:          dL/dt  =  τ_ext            (Σ torques = rate of change of angular momentum)
Center of mass:            M R̈_cm =  F_ext            (center of mass moves like a point particle)
```

These are the low-velocity limits of the corresponding Noether symmetries.

### 5.7 Experimental Domain

- **Validity:** All macroscopic systems with v ≪ c and weak gravity (Φ/c² ≪ 1).
- **Transition:** Relativistic corrections needed at v/c ≳ 0.01 (GPS satellites at 14,000 km/h need both SR + GR corrections = ~38 μs/day).
- **Quantum limit:** Position-momentum uncertainty prevents simultaneous perfect determination of both — but expectation values obey Ehrenfest's theorem which exactly mirrors Newton's 2nd law.

**Falsification status:** Never falsified within domain. Relativity and QM did not falsify Newton — they revealed him as a low-energy limiting case.

---

## 6. Conservation of Energy (First Law of Thermodynamics)

### 6.1 The First Law

```
dU  =  δQ  −  δW                              internal energy change

In a closed system (no heat/work exchange):
ΔU  =  0                                      E_total = constant

In differential form:
dU  =  T dS  −  p dV  +  Σ_i μ_i dN_i       chemical potential μ_i for species i
```

### 6.2 Thermodynamic Potentials (Legendre Transforms)

```
Internal energy:      U(S,V,N)
Enthalpy:             H(S,p,N)  =  U + pV
Helmholtz free energy: F(T,V,N)  =  U − TS
Gibbs free energy:    G(T,p,N)  =  U + pV − TS  =  H − TS

Differentials:
dH  =  T dS  +  V dp  +  Σ μ_i dN_i
dF  =  −S dT  −  p dV  +  Σ μ_i dN_i
dG  =  −S dT  +  V dp  +  Σ μ_i dN_i
```

### 6.3 Maxwell Relations

From equality of cross-derivatives (d²U = exact differential):

```
(∂T/∂V)_S    =  −(∂p/∂S)_V
(∂T/∂p)_S    =  +(∂V/∂S)_p
(∂S/∂V)_T    =  +(∂p/∂T)_V
(∂S/∂p)_T    =  −(∂V/∂T)_p
```

These relate seemingly unconnected quantities (e.g., how entropy changes with volume = how pressure changes with temperature). All experimentally confirmed.

### 6.4 Specific Heat Relations

```
C_V  =  T (∂S/∂T)_V  =  (∂U/∂T)_V
C_p  =  T (∂S/∂T)_p  =  (∂H/∂T)_p

C_p  −  C_V  =  −T (∂V/∂T)_p² / (∂V/∂p)_T  =  T V α² / κ_T

α = thermal expansion coefficient, κ_T = isothermal compressibility
```

**Equipartition theorem (classical):**
```
Each quadratic degree of freedom contributes ½ k_B T to energy.
C_V = (f/2) R per mole for f degrees of freedom.
```

### 6.5 Noether Derivation: Time Translation → Energy

```
S[φ]  =  ∫ d⁴x ℒ(φ, ∂_μ φ)

Under infinitesimal time translation:  x^μ → x^μ + ε δ₀^μ

Noether current:  J^μ  =  (∂ℒ/∂(∂_μ φ)) δφ  −  T^μ_ν ε^ν

where the canonical stress-energy tensor is:
T^μ_ν  =  (∂ℒ/∂(∂_μ φ)) ∂_ν φ  −  δ^μ_ν ℒ

E  =  ∫ d³x T⁰_₀               conserved charge = energy
```

### 6.6 Conservation in General Relativity

```
∇_μ T^{μν}  =  0                                covariant conservation

This does NOT imply a globally conserved energy in curved spacetime.
Energy is not globally defined in GR — only local conservation.
The "energy of the gravitational field" is not a tensor.
```

**Komar mass (stationary spacetimes):**
```
M_K  =  −(1/8πG) ∮_{S²_∞} ∇^μ ξ^ν dS_{μν}      ξ^ν = timelike Killing vector
```

**ADM mass (asymptotically flat):**
```
M_ADM  =  (1/16πG) ∮_{S²_∞} (∂_j h_{ij} − ∂_i h_{jj}) n^i dA
```

### 6.7 Quantum Energy

```
Ĥ |E⟩  =  E |E⟩                                 energy eigenvalue equation

⟨Ĥ⟩  =  ⟨ψ|Ĥ|ψ⟩                                 expectation value — constant if Ĥ is time-independent

In QFT, the Hamiltonian is:
Ĥ  =  ∫ d³x : T^{00} :

Vacuum expectation value: ⟨0|T^{μν}|0⟩ = ρ_vac g^{μν}
ρ_vac ∝ Λ (cosmological constant problem: observed ρ_vac ~ 10⁻¹²⁰ × QFT prediction)
```

### 6.8 Zero-Point Energy and Casimir Effect

```
E₀  =  ½ ℏω                                 per mode

Casimir force between two parallel conducting plates (area A, separation d):
F  =  −(π² ℏc / 240 d⁴) A                    (attractive)

P_Casimir  =  F/A  =  1.3×10⁻³ Pa at d=1μm    measured to ~1%
```

### 6.9 Experimental Status

Energy conservation: **zero violations ever observed**. Apparent violations (beta decay spectrum → neutrino predicted by Pauli 1930, discovered 1956) were resolved by discovering new particles.

In GR, Wheeler's "geon" and "mass without mass" ideas do not violate energy conservation — they are just nonlocal in gravitational energy definition.

**Domain:** Universal — classical, quantum, relativistic, cosmological. Derived from time-translation symmetry of physical laws.

---

## 7. Second Law of Thermodynamics

### 7.1 The Second Law

```
dS_total  ≥  0                        entropy of an isolated system never decreases

dS  =  δQ_rev / T                      Clausius definition of entropy change

For irreversible processes:  dS  >  δQ_irr / T
```

### 7.2 Boltzmann Entropy

```
S  =  k_B  ln  Ω                         (Boltzmann, 1877)

Ω  =  number of microstates corresponding to given macrostate
k_B = 1.380649×10⁻²³ J/K               (exact, defines kelvin since 2019)
```

### 7.3 Gibbs Entropy (Statistical Mechanics)

```
S  =  −k_B  Σ_i p_i ln p_i             classical discrete distribution

S  =  −k_B  ∫ f(p,q) ln f(p,q) dΓ      continuous phase space

S  =  −k_B  Tr[ρ̂ ln ρ̂]                 quantum (von Neumann entropy)

Maximized by uniform distribution (microcanonical) / canonical (Boltzmann) / grand canonical.
```

### 7.4 Shannon Entropy (Information Theory, 1948)

```
H(X)  =  −Σ_i p(x_i) log₂ p(x_i)        bits

Relationship:  S = k_B ln 2 · H          thermodynamic entropy = 0.957×10⁻²³ J/K per bit
```

### 7.5 Boltzmann H-Theorem (1872)

```
H(t)  =  ∫ d³p f(p,t) ln f(p,t)

dH/dt  ≤  0                             H always decreases (or constant at equilibrium)

H = −S/k_B + constant → dS/dt ≥ 0
```

Proves that the Boltzmann equation implies the 2nd Law. The "arrow of time" emerges from molecular chaos (Stosszahlansatz).

### 7.6 Loschmidt's Paradox and Resolution

**Paradox:** Microscopic equations of motion are time-reversible. Where does irreversibility come from?

**Resolution:** The H-theorem relies on the Stosszahlansatz (molecular chaos assumption) — correlations are discarded after each collision. This is a coarse-graining. The apparent irreversibility emerges from:
- Low-entropy initial conditions (Past Hypothesis)
- Dynamical instability (Lyapunov exponents → rapid information scrambling)
- Coarse-graining (observables don't resolve micro-details)

### 7.7 Fluctuation Theorems (1990s–present)

**Crooks Fluctuation Theorem (1999):**
```
p(W) / p_rev(−W)  =  exp( (W − ΔF) / k_B T )

p(W)  =  probability of work W during forward process
ΔF    =  free energy difference between initial and final states
```

**Jarzynski Equality (1997):**
```
⟨exp(−W / k_B T)⟩  =  exp(−ΔF / k_B T)

Averages over nonequilibrium trajectories recover equilibrium free energy differences.
```

These theorems **generalize** the 2nd Law — they describe fluctuations where `dS < 0` is probabilistically possible but exponentially unlikely for macroscopic systems.

**Experimental verification:** RNA pulling experiments, colloidal particle trapping, single-molecule force spectroscopy.

### 7.8 Landauer's Principle (1961)

```
Erasing 1 bit of information dissipates AT LEAST  k_B T ln 2  joules of heat.

Physical basis: information is physical — logical irreversibility → thermodynamic irreversibility.
```

Verified experimentally (Bérut et al., Nature 2012).

Resolves Maxwell's demon: the demon must erase its memory to operate cyclically → this inevitably generates `≥ k_B T ln 2` per erased bit → 2nd Law holds.

### 7.9 Entropy in Physical Systems

**Mixing entropy (ideal gases):**
```
ΔS_mix  =  −k_B (N₁ ln x₁ + N₂ ln x₂)     x_i = mole fraction
```

**Phase transitions:**
```
ΔS_vaporization  =  L_v / T_b               L_v = latent heat

Trouton's rule: ΔS_vap ≈ 85 J/(mol·K) for many liquids at boiling point.
```

**Configurational entropy (polymers, glasses):**
```
S_conf  =  k_B ln Ω_conf                     e.g., number of chain conformations
```

**Residual entropy of ice:** `S(0) ≈ 3.4 J/(mol·K)` — Pauling's estimate for proton disorder. Confirmed experimentally.

### 7.10 Black Hole Entropy (Generalized Second Law)

```
S_BH  =  k_B A / 4ℓ_P²                       Bekenstein-Hawking (1972–74)

ℓ_P  =  √(ℏG/c³)  ≈  1.616255×10⁻³⁵ m       Planck length

d/dt (S_BH + S_matter)  ≥  0                Generalized Second Law (GSL)
```

### 7.11 Heat Death and the Arrow of Time

The 2nd Law implies a future state of maximum entropy — "heat death":
- All free energy exhausted
- Uniform temperature everywhere
- No macroscopic work possible
- The universe reaches thermodynamic equilibrium

**Multiple arrows of time** all derive from the low-entropy initial condition:
- Thermodynamic arrow (entropy increase)
- Cosmological arrow (universe expansion)
- Psychological arrow (we remember the past, not the future)
- Causal arrow (causes precede effects)

### 7.12 Experimental Status

| Test | System | Status |
|------|--------|--------|
| Heat engines | Every engine since Newcomen (1712) | Efficiency ≤ Carnot — confirmed |
| Fluctuation theorems | Single-molecule biophysics | Confirmed |
| Landauer's principle | Micromagnetic bit manipulation | Confirmed |
| Maxwell's demon | Information engines (Toyabe et al. 2010) | Resolved |
| H-theorem | Molecular dynamics simulations | Confirmed |
| Entropy of black holes | Gravitational wave ringdown, analog gravity | Indirectly supported |
| Entropy increase | Every macroscopic process, every living organism | Universally observed |

**Domain:** Any system with many degrees of freedom. A statistical law — not absolute at the microscale — but overwhelmingly probable at macroscopic scales. **No macroscopic violation ever observed.**

---

## 8. Planck–Einstein Relation (Quantum of Action, 1900–1905)

### 8.1 The Fundamental Quantum Relations

```
E  =  hν  =  ℏω                           photon energy
p  =  h/λ  =  ℏk                           photon momentum

h   = 6.62607015×10⁻³⁴ J·s                (exact, defines kg since 2019)
ℏ   = h/2π = 1.054571817×10⁻³⁴ J·s
```

**Compton wavelength:**
```
λ_C  =  h / mc                              electron: 2.4263102389×10⁻¹² m
```

### 8.2 Planck's Blackbody Radiation Law (1900)

**Spectral radiance (energy per unit time, area, solid angle, frequency):**
```
B_ν(ν, T)  =  (2hν³ / c²) · 1 / [exp(hν/k_B T) − 1]        W·sr⁻¹·m⁻²·Hz⁻¹

B_λ(λ, T)  =  (2hc² / λ⁵) · 1 / [exp(hc/λk_B T) − 1]       W·sr⁻¹·m⁻²·m⁻¹
```

**Derivation:** Quantize the electromagnetic field oscillators → energy per mode = hν/(e^{hν/kT}−1). Sum over all modes with density of states `g(ν)dν = (8πν²/c³) dν`.

**Limits:**
```
hν ≪ k_B T:   B_ν → (2ν²/c²) k_B T          Rayleigh-Jeans law (classical)
hν ≫ k_B T:   B_ν → (2hν³/c²) e^{−hν/kT}    Wien approximation
```

### 8.3 Consequences of Planck's Law

**Wien's Displacement Law (1893):**
```
λ_max T  =  2.897771955...×10⁻³ m·K        wavelength of peak emission

ν_max / T  =  58.789... GHz/K               frequency of peak
```

**Stefan-Boltzmann Law (1879–1884):**
```
j*  =  σ T⁴                                  total radiated power per unit area

σ   =  (2π⁵ k_B⁴) / (15 h³ c²)               Stefan-Boltzmann constant
    =  5.670374419×10⁻⁸ W·m⁻²·K⁻⁴           (CODATA 2018)
```

**Photon number density (blackbody):**
```
n_γ  =  (2 ζ(3) / π²) (k_B T / ℏc)³         ≈  20.28 (T/1K)³ cm⁻³
```

**Energy density:**
```
u  =  a T⁴                                   a = 4σ/c = 7.5657×10⁻¹⁶ J·m⁻³·K⁻⁴
```

### 8.4 The Photoelectric Effect (Einstein, 1905)

```
K_max  =  hν  −  φ                            kinetic energy of ejected electron

φ    =  work function of metal (minimum energy to eject electron)
hν_0 =  φ                                      threshold frequency

K_max ≥ 0 → requires ν > ν_0 regardless of light intensity.
```

**Key predictions confirming photons, not classical waves:**
1. K_max depends only on ν, not intensity.
2. Threshold frequency ν_0 exists.
3. No time delay — emission is instantaneous (vs. minutes for classical energy accumulation).
4. Slope of K_max vs ν = h (Planck's constant — measured by Millikan 1916).

### 8.5 Compton Scattering (1923)

```
λ' − λ  =  (h / m_e c) (1 − cos θ)            Compton shift

λ'_max  =  λ + 2h/m_e c                        full backscatter (θ=π)

Δλ_max  ≈  0.00486 nm                          independent of incident wavelength
```

**Derivation:** Photon + electron, relativistic energy-momentum conservation:
```
hν + m_e c²  =  hν' + γ m_e c²
hν/c  =  (hν'/c) cos θ + γ m_e v cos φ
0      =  (hν'/c) sin θ − γ m_e v sin φ
```

Eliminating φ and v yields Δλ. Experimentally: detected recoil electron in coincidence with scattered photon (Bothe-Geiger 1925) — confirmed photon as particle.

### 8.6 de Broglie Wavelength (1923–1924)

```
λ  =  h / p  =  h / (γ m v)                   for any massive particle

Non-relativistic:   λ = h / √(2mE)
Electron at 100 eV:  λ ≈ 0.12 nm               (atomic-scale diffraction)
```

**Davisson-Germer experiment (1927):** Electron diffraction from nickel crystal → interference pattern exactly matching de Broglie wavelength prediction. Confirmed wave nature of matter.

**Modern:** Neutron diffraction, He-atom scattering, Bose-Einstein condensate interference, molecule interferometry (up to >2000 atoms — C₆₀ buckyballs, tailored organic molecules >25,000 amu).

### 8.7 Electromagnetic Field Quantization (QED)

**Single-mode field quantization:**
```
Ê(r,t)  =  E₀ (â e^{i(k·r−ωt)} + â† e^{−i(k·r−ωt)})

E₀  =  √(ℏω / 2ε₀ V)                         field amplitude per photon
```

**Fock (number) states:**
```
â† |n⟩ = √(n+1) |n+1⟩                         create photon
â  |n⟩ = √n |n−1⟩                             annihilate photon
N̂ |n⟩ = n |n⟩                                  N̂ = â† â

⟨n|Ê|n⟩ = 0                                    zero mean field
⟨n|Ê²|n⟩ = E₀² (n + ½)                         nonzero variance = zero-point fluctuations
```

**Coherent states (laser light, Glauber 1963):**
```
|α⟩  =  e^{−|α|²/2} Σ_{n=0}^∞ (α^n / √(n!)) |n⟩

â |α⟩ = α |α⟩                                   eigenvalue of annihilation operator
⟨n⟩ = |α|² = mean photon number
Δn = |α| = √⟨n⟩  →  Poissonian photon statistics
```

**Thermal state:**
```
ρ̂_th  =  (1/Z) Σ_n e^{−β ℏω n} |n⟩⟨n|
⟨n⟩   =  1 / (e^{ℏω/kT} − 1)                   Bose-Einstein distribution
```

### 8.8 Photon Momentum and Radiation Pressure

```
p_γ  =  hν / c  =  E_γ / c

Radiation pressure on perfect absorber:  P_rad  =  I / c
Radiation pressure on perfect reflector: P_rad  =  2I / c      (momentum reversal)
I = intensity (W/m²)

Solar radiation pressure at 1 AU:  P_sun  ≈  4.6 μPa
Solar sail acceleration:  a = 2η I / (c σ)     η = efficiency, σ = areal density
```

**Photon recoil in atomic transitions:** `v_recoil = hν / (m c)` — critical for laser cooling, optical molasses, Bose-Einstein condensates.

### 8.9 Planck Units (Derived Quantities from ℏ, G, c)

```
Planck length:     ℓ_P  =  √(ℏG/c³)     ≈  1.616255×10⁻³⁵ m
Planck time:       t_P  =  √(ℏG/c⁵)     ≈  5.391247×10⁻⁴⁴ s
Planck mass:       m_P  =  √(ℏc/G)      ≈  2.176434×10⁻⁸ kg  (≈ 1.22×10¹⁹ GeV)
Planck energy:     E_P  =  √(ℏc⁵/G)     ≈  1.9561×10⁹ J  (≈ 1.22×10¹⁹ GeV)
Planck temperature: T_P =  √(ℏc⁵/(G k_B²)) ≈  1.416784×10³² K
```

### 8.10 Experimental Verification

| Test | Experiment | Precision | Status |
|------|-----------|-----------|--------|
| Blackbody spectrum | Any thermal radiation, CMB | 10⁻⁵ | Confirmed |
| Photoelectric effect | Millikan 1916, photoemission spectroscopy | Percent | Confirmed |
| Compton scattering | Compton 1923, γ-ray astronomy | <1% | Confirmed |
| de Broglie wavelength | Davisson-Germer, electron microscopy | Confirmed |
| Photon statistics | Hanbury Brown-Twiss, single-photon sources | Confirmed |
| Casimir effect (zero-point) | Lamoreaux 1997, MEMS experiments | ~1% | Confirmed |
| Photon recoil | Laser cooling — sub-μK temperatures | Confirmed |
| CMB blackbody | COBE/FIRAS (1990) | 50 ppm | Confirmed |
| Wave-particle duality | Double-slit with electrons, atoms, molecules | Confirmed |

**Domain:** All quantum systems. The fundamental granularity of energy and action. Underpins quantum mechanics, QED, and quantum optics.

---

## 9. The Standard Model Lagrangian

### 9.1 Complete Lagrangian (Before Symmetry Breaking)

```
ℒ_SM  =  ℒ_gauge  +  ℒ_fermion  +  ℒ_Higgs  +  ℒ_Yukawa  +  ℒ_gauge-fix  +  ℒ_ghost

Gauge group:  SU(3)_c  ×  SU(2)_L  ×  U(1)_Y
```

### 9.2 Gauge Sector

```
ℒ_gauge  =  −¼ G_a^{μν} G^a_{μν}  −  ¼ W_i^{μν} W^i_{μν}  −  ¼ B^{μν} B_{μν}

G_a^{μν}  =  ∂^μ G_a^ν − ∂^ν G_a^μ + g_s f_{abc} G_b^μ G_c^ν         SU(3) — 8 gluons
W_i^{μν}  =  ∂^μ W_i^ν − ∂^ν W_i^μ + g ε_{ijk} W_j^μ W_k^ν           SU(2) — 3 W bosons
B^{μν}    =  ∂^μ B^ν   − ∂^ν B^μ                                      U(1) — B boson

g_s  →  strong coupling (α_s = g_s²/4π)
g    →  weak isospin coupling
g'   →  weak hypercharge coupling
```

### 9.3 Fermion Sector

```
ℒ_fermion  =  i Σ_f ψ̄_f D̸ ψ_f

Covariant derivative:  D_μ = ∂_μ − i g_s G_μ^a T^a − i g W_μ^i τ^i/2 − i g' Y B_μ

T^a          →  SU(3) generators (λ^a/2 for triplets, 0 for singlets)
τ^i/2        →  SU(2) generators (Pauli matrices/2 for doublets, 0 for singlets)
Y            →  hypercharge quantum number
```

**Fermion content (3 generations):**

```
      SU(3)_c  SU(2)_L  U(1)_Y    Q = T_3 + Y
      ────────  ───────  ─────     ────────────
Q_Lᵢ:    3        2      +1/6      +2/3, −1/3      left-handed quark doublet (u_L, d_L)
u_Rᵢ:    3        1      +2/3      +2/3             right-handed up-type
d_Rᵢ:    3        1      −1/3      −1/3             right-handed down-type
L_Lᵢ:    1        2      −1/2       0,   −1         left-handed lepton doublet (ν_L, e_L)
e_Rᵢ:    1        1      −1         −1               right-handed charged lepton
ν_Rᵢ:    1        1       0          0               right-handed neutrino (optional)
```

### 9.4 Higgs Sector (Electroweak Symmetry Breaking)

```
ℒ_Higgs  =  |D_μ Φ|²  −  V(Φ)                              D_μ = ∂_μ − i g W_μ^i τ^i/2 − i g' Y B_μ

Φ   =  [ φ⁺ ]     Y_Φ = +1/2
        [ φ⁰ ]

V(Φ)  =  −μ² |Φ|²  +  λ |Φ|⁴      μ² > 0, λ > 0

Minimum (vacuum expectation value):
⟨Φ⟩  =  [  0  ]          |⟨Φ⟩|² = v²/2 = μ²/(2λ)
        [ v/√2 ]

v  ≈  246.21971 GeV        from Fermi constant G_F measured in muon decay.
                           G_F / (√2) = 1/(2 v²)
```

### 9.5 Mass Generation After Symmetry Breaking

**SU(2)_L × U(1)_Y → U(1)_EM**

```
Massive gauge bosons:
W^±  =  (W¹ ∓ i W²) / √2           M_W  =  g v / 2  ≈  80.377 ± 0.012 GeV
Z⁰   =  (g W³ − g' B) / √(g² + g'²)  M_Z  =  v √(g²+g'²) / 2  ≈  91.1876 ± 0.0021 GeV

Massless gauge boson:
A    =  (g' W³ + g B) / √(g² + g'²)  M_γ = 0  (photon, unbroken U(1)_EM)

Weak mixing angle (Weinberg angle):
tan θ_W  =  g' / g
sin² θ_W  =  0.23121 ± 0.00004 (on-shell scheme)
       ≈  0.23141 (MS-bar, m_Z scale)

M_W = M_Z cos θ_W                     ρ = M_W²/(M_Z² cos² θ_W) = 1 at tree level
```

**Fermion masses (Yukawa couplings):**
```
ℒ_Yukawa  =  −Y_u^{ij} Q̄_Lⁱ Φ̃ u_Rʲ  −  Y_d^{ij} Q̄_Lⁱ Φ d_Rʲ  −  Y_e^{ij} L̄_Lⁱ Φ e_Rʲ  +  h.c.

Φ̃  =  i τ² Φ*  =  [ φ⁰* ]            transforms as Φ with Y = −1/2
                     [ −φ⁻  ]

After EWSB:  m_f = Y_f · v / √2

CKM mixing (Cabibbo-Kobayashi-Maskawa):
The Yukawa matrices are not diagonal in the gauge basis → quark mass eigenstates mix.
CKM matrix V_{CKM} (3×3 unitary, 4 parameters):
|V_ud| = 0.97435    |V_us| = 0.22500    |V_ub| = 0.00369
|V_cd| = 0.22486    |V_cs| = 0.97349    |V_cb| = 0.04182
|V_td| = 0.00857    |V_ts| = 0.04110    |V_tb| = 0.999118
```

**PMNS mixing (neutrinos):** If neutrinos have Dirac mass, analogous 3×3 matrix with mixing angles θ₁₂ ≈ 33°, θ₂₃ ≈ 45°, θ₁₃ ≈ 8.5°.

**Higgs boson mass:**
```
M_H²  =  2 λ v²

m_H  =  125.25 ± 0.17 GeV          (CMS+ATLAS combined)
λ    ≈  0.129                       Higgs self-coupling
```

### 9.6 Faddeev-Popov Gauge Fixing and Ghosts

```
ℒ_gauge-fix  =  −(1/2ξ_G) (∂^μ G_μ^a)²  −  (1/2ξ_W) (∂^μ W_μ^i)²  −  (1/2ξ_B) (∂^μ B_μ)²

ξ_i → gauge parameters (ξ→0: Landau gauge, ξ→1: Feynman gauge, ξ→∞: unitary gauge)

ℒ_ghost  =  Σ_{G,W} [c̄^a ∂^μ D_μ^{ab} c^b]

Ghost fields c^a are anticommuting scalars (Fermi statistics, Bose kinematics).
Required for perturbative unitarity in non-abelian gauge theories.
```

### 9.7 Accidental Symmetries

The SM Lagrangian has global symmetries that are NOT imposed but follow from the gauge structure and renormalizability:

```
Baryon number (B):  conserved at classical level.
                    Violated by non-perturbative effects (sphalerons) — ΔB = ΔL = 3 at T ≫ 100 GeV.

Lepton number (L):  separately L_e, L_μ, L_τ conserved (no neutrino oscillations in minimal SM).
                    Violated by neutrino masses → charged lepton flavor violation possible but unobserved.
```

### 9.8 Renormalizability ('t Hooft & Veltman, 1971–72)

The SM with spontaneous symmetry breaking is renormalizable. All divergences can be absorbed into a finite set of counterterms:

```
Counterterm Lagrangian:
δℒ  =  δZ_gauge (kinetic terms)  +  δZ_fermion (kinetic terms)  +  δm (mass)
       +  δλ (couplings)  +  δv (VEV)

Renormalization group equations (RGEs) determine running of all couplings.
```

### 9.9 Key Precision Tests

**Muon anomalous magnetic moment (g−2)_μ:**
```
a_μ^{EXP}  =  116 592 061(41) × 10⁻¹¹               (Fermilab + BNL)
a_μ^{SM}   =  116 591 810(43) × 10⁻¹¹               (2020 White Paper)

Tension:  251(59) × 10⁻¹¹  →  ~4.2σ discrepancy.  Possible new physics or underestimated hadronic corrections.
```

**Electroweak precision observables (LEP, SLC, Tevatron, LHC):**
```
M_W   =  80.377 ± 0.012 GeV
M_Z   =  91.1876 ± 0.0021 GeV
Γ_Z   =  2.4952 ± 0.0023 GeV
σ_h⁰  =  41.480 ± 0.033 nb
R_l   =  20.767 ± 0.025
A_FB^{0,b} = 0.0992 ± 0.0016
```

Global fit to all EWPO agrees with SM at <1σ across all observables.

**Higgs properties:**
```
σ(pp→H)          =  1.02 ± 0.05 × SM      (overall signal strength)
μ_γγ              =  1.10 ± 0.08 × SM
μ_ZZ*             =  1.01 ± 0.08 × SM
μ_WW*             =  1.00 ± 0.08 × SM
μ_ττ              =  0.91 ± 0.09 × SM
μ_bb̄              =  1.04 ± 0.14 × SM
```

All Higgs couplings consistent with SM predictions. CP properties: pure CP-even (0⁺⁺) favored; CP-odd/mixed disfavored at >3σ.

**Domain:** All known fundamental particles and the electromagnetic, weak, and strong forces (except gravity). The most precisely tested physical theory in history.

---

## 10. Yang–Mills Gauge Theory (1954)

### 10.1 Field Strength and Covariant Derivative

```
F_μν^a  =  ∂_μ A_ν^a  −  ∂_ν A_μ^a  +  g f^{abc} A_μ^b A_ν^c

D_μ  =  ∂_μ  −  i g A_μ^a T^a              gauge-covariant derivative

[f^{abc}] = structure constants of Lie algebra
[T^a, T^b] = i f^{abc} T^c                 Lie algebra
```

**Yang-Mills Lagrangian:**
```
ℒ_YM  =  −¼ F_μν^a F^{a μν}               gauge-invariant kinetic term

Gauge transformation:
A_μ  →  U A_μ U⁻¹  +  (i/g) U ∂_μ U⁻¹      U = exp(i g α^a(x) T^a)
F_μν →  U F_μν U⁻¹                           transforms covariantly (adjoint)
```

### 10.2 SU(N) Structure Constants

```
For SU(2):   f^{abc} = ε^{abc}              Levi-Civita (1 generator)
             T^a     = τ^a/2                Pauli matrices

For SU(3):   f^{abc}:  123 (1),  147 (1/2),  156 (−1/2),  246 (1/2),
                        257 (1/2),  345 (1/2),  367 (−1/2),
                        458 (√3/2),  678 (√3/2)

             d^{abc}:  118 (1/√3),  146 (1/2),  157 (1/2),  228 (1/√3),
                       247 (−1/2),  256 (1/2),  338 (1/√3),  344 (1/2),
                       355 (1/2),  366 (−1/2),  377 (−1/2),  448 (−1/2√3),
                       558 (−1/2√3),  668 (−1/2√3),  778 (−1/2√3), 888 (−1/√3)
```

### 10.3 Self-Interactions

The `g f^{abc}` term in `F_μν^a` produces:

**Three-gluon vertex (momentum space):**
```
V_{μνρ}^{abc}(p,q,r)  =  −g f^{abc} [g_{μν}(p−q)_ρ + g_{νρ}(q−r)_μ + g_{ρμ}(r−p)_ν]
                         with p+q+r=0 (all momenta incoming)
```

**Four-gluon vertex:**
```
V_{μνρσ}^{abcd}  =  −i g² [ f^{abe} f^{cde} (g_{μρ}g_{νσ}−g_{μσ}g_{νρ})
                  +     f^{ace} f^{bde} (g_{μν}g_{ρσ}−g_{μσ}g_{νρ})
                  +     f^{ade} f^{bce} (g_{μν}g_{ρσ}−g_{μρ}g_{νσ}) ]
```

These are the source of asymptotic freedom (antiscreening) — unique to non-abelian theories.

### 10.4 Gauge Invariance of the YM Lagrangian

```
F_μν → U F_μν U⁻¹  →  Tr(F_μν F^{μν}) = invariant
Tr(T^a T^b) = ½ δ^{ab} (normalization)
```

### 10.5 Classical Solutions — Instantons

Finite-action Euclidean solutions (Belavin, Polyakov, Schwartz, Tyupkin 1975):

```
A_μ(x)  =  (1/g) (x²/(x²+ρ²)) U⁻¹ ∂_μ U    (BPST instanton, ρ=scale size)

Topological charge (winding number):
Q  =  (g²/32π²) ∫ d⁴x F_μν^a F̃^{a μν}  ∈  ℤ

Action: S = 8π²|Q|/g²

Instanton transitions: ΔQ = ΔB = ΔL (in SM) — violates baryon number.
Strong CP problem from θ F\tilde{F} term in YM Lagrangian.
```

**Domain:** Non-abelian gauge invariance is the organizing principle behind QCD, the electroweak theory, and most beyond-SM proposals (GUTs, technicolor, etc.).

---

## 11. Noether's Theorem (1918)

### 11.1 Statement of the Theorem

```
Every continuous (differentiable) symmetry of the action S = ∫ L dt corresponds to a conserved current.

If δS = 0 under transformation φ → φ + ε Δφ (locally parametrized by ε^a(x)),
then there exist conserved currents J_a^μ satisfying:

∂_μ J_a^μ  =  0      on-shell (when equations of motion are satisfied).

Conserved charge:  Q_a  =  ∫ d³x J_a⁰
dQ_a/dt  =  0
```

### 11.2 Derivation (Field Theory)

Consider an infinitesimal global symmetry transformation:

```
x^μ → x^μ + ε^a X_a^μ(x)
φ_i(x) → φ_i(x) + ε^a Ψ_{i,a}(x)

Noether current (first theorem):
J_a^μ  =  Σ_i [∂ℒ/∂(∂_μ φ_i)] (Ψ_{i,a} − ∂_ν φ_i X_a^ν)  +  ℒ X_a^μ
```

### 11.3 Symmetry-Conservation Dictionary

```
──────────────────────────────────────────────────────────
Symmetry                       Conserved Quantity         Exact?
──────────────────────────────────────────────────────────
Time translation (t→t+ε)       Energy (E)                 Yes
Spatial translation (x→x+ε)    Momentum (p)               Yes
Rotation (x→R·x)               Angular momentum (L)       Yes
U(1) gauge phase               Electric charge (Q)        Yes
SU(2) weak isospin             Weak isospin current       Broken (SSB)
SU(3) color                    Color charge               Exact
SU(3)_L×SU(3)_R chiral (QCD)   Axial/vector currents      Approx. (SSB + anomaly)
Lorentz boost                  Center-of-mass motion      Yes
Scale/dilatation               Dilatation current         Broken by anomaly (QCD)
Supersymmetry                  Supercurrent               Broken (if realized)
Baryon number (accidental)     Baryon number (B)          Classical; violated nonpert.
Lepton number (accidental)     Lepton number (L)          Violated by ν mass
──────────────────────────────────────────────────────────
```

### 11.4 Noether's Second Theorem (Local/Gauge Symmetries)

For local gauge symmetries (ε^a(x) is an arbitrary function of x):

```
The second theorem gives identities (Bianchi identities in GR, Slavnov-Taylor in QFT)
relating the equations of motion — constraints on dynamics, not conserved charges.
```

This explains why gauge symmetries do not produce independent conserved charges in the same way.

### 11.5 Consequence: Why Conservation Laws Are Rock-Solid

Noether's theorem is a mathematical theorem given Lagrangian dynamics. It can only fail if:
1. The symmetry is NOT a symmetry of the Lagrangian.
2. The derivation of the Euler-Lagrange equations from the action fails.
3. The system is not Lagrangian (e.g., dissipative forces with no potential).

In all Lagrangian theories (all of fundamental physics), the symmetry-conservation link is absolute.

**Domain:** Every physical theory expressible in Lagrangian/Hamiltonian form — effectively all of fundamental physics. Not a testable hypothesis — a mathematical identity.

---

## 12. Friedmann Equations (Cosmology, 1922)

### 12.1 The Two Friedmann Equations

```
H²  ≡  (ȧ/a)²  =  (8πG/3) ρ  −  kc²/a²  +  Λc²/3          First (expansion rate)

ä/a  =  −(4πG/3) (ρ + 3p/c²)  +  Λc²/3                    Second (acceleration)

H  =  Hubble parameter
a(t) = scale factor
k   = +1, 0, −1 (closed, flat, open)
```

**Fluid equation (conservation of stress-energy from Friedmann + 2nd):**
```
ρ̇  +  3H (ρ + p/c²)  =  0

For matter (p=0):        ρ_m ∝ a^{-3}
For radiation (p=ρc²/3):  ρ_r ∝ a^{-4}
For dark energy (p=−ρc²): ρ_Λ = const.
```

### 12.2 Cosmological Parameters (ΛCDM — Planck 2018)

```
H₀  =  67.4 ± 0.5 km/s/Mpc              Hubble constant
Ω_m  =  0.315 ± 0.007                   matter density parameter
Ω_Λ  =  0.6847 ± 0.0073                 dark energy density parameter
Ω_b  =  0.0493 ± 0.0006                 baryon density parameter
Ω_k  =  0.001 ± 0.002                   curvature (consistent with flat)

Ω_m + Ω_Λ + Ω_k  =  1

Age of universe:  t₀  =  13.797 ± 0.023 Gyr
```

**Redshift relation:**
```
a(t)  =  1 / (1+z)

1 + z  =  λ_obs / λ_emit
```

### 12.3 Distance Measures

**Comoving distance:** `χ(z) = c ∫_0^z dz'/H(z')`

```
Luminosity distance:     d_L  =  (1+z) χ
Angular diameter distance: d_A =  χ / (1+z)
Distance modulus:         μ   =  5 log₁₀(d_L/10pc)
```

**BAO (Baryon Acoustic Oscillations):** Standard ruler at `r_d ≈ 147 Mpc` (comoving sound horizon at drag epoch). Measured in galaxy surveys (SDSS, DESI) — consistent with ΛCDM.

### 12.4 Thermal History

```
T(z)  =  T₀ (1+z)                           T₀ = 2.72548 ± 0.00057 K (CMB)

Key epochs:
z ~ 1100  (T~3000K):    Recombination — CMB emitted, universe becomes neutral (~380,000 yr)
z ~ 3400  (T~0.9eV):    Matter-radiation equality (~50,000 yr)
z ~ 10⁹   (T~1MeV):     Big Bang Nucleosynthesis (~3 min → H, He, Li)
z ~ 10¹⁵  (T~100GeV):   Electroweak phase transition (~10⁻¹¹ s)
```

### 12.5 BBN (Big Bang Nucleosynthesis)

Primordial abundances predicted:

```
Y_p     =  0.24709 ± 0.00025      Helium-4 mass fraction
D/H     =  (2.527 ± 0.030) × 10⁻⁵  Deuterium
³He/H   =  (1.1 ± 0.2) × 10⁻⁵    Helium-3
⁷Li/H   =  (1.6 ± 0.3) × 10⁻¹⁰   Lithium
```

All except ⁷Li (2–3σ tension, possibly astrophysical or new physics) agree with ΛCDM+BBN predictions using η (baryon-to-photon ratio) from CMB.

### 12.6 The Cosmological Constant Problem

```
Observed:  ρ_Λ  ≈  (2.3 × 10⁻³ eV)⁴  ≈  6 × 10⁻¹⁰ J/m³
QFT prediction (zero-point sum up to Planck scale): ρ_vac ~ (10¹⁸ GeV)⁴

ρ_obs / ρ_vac  ~  10⁻¹²⁰              worst prediction in physics
```

**Domain:** Homogeneous, isotropic cosmology on scales >~100 Mpc. FLRW metric. ΛCDM fits all cosmological datasets (CMB, BAO, SNe, LSS, cluster counts) at the ~1% level.

---

## 13. Klein–Gordon Equation (Relativistic spin-0, 1926)

### 13.1 Equation

```
(□ + m²c²/ℏ²) φ(x)  =  0                     where □ = ∂_μ ∂^μ = −(1/c²)∂²/∂t² + ∇²

Derived from relativistic energy-momentum: E² = p²c² + m²c⁴
Substituting E→iℏ∂/∂t, p→−iℏ∇ → (iℏ∂/∂t)² φ = [(−iℏ∇)²c² + m²c⁴] φ
```

### 13.2 Lagrangian and Conserved Current

```
ℒ_KG  =  ½ (∂_μ φ)(∂^μ φ)  −  ½ (m²c²/ℏ²) φ²

Noether current (U(1) symmetry φ→e^{iα}φ):
j^μ  =  i (φ* ∂^μ φ  −  φ ∂^μ φ*)             for complex scalar field
∂_μ j^μ  =  0                                   charge conservation

Energy-momentum tensor:
T^{μν}  =  (∂^μ φ)(∂^ν φ)  −  g^{μν} ℒ
```

### 13.3 Plane Wave Solutions

```
φ(x)  =  A e^{i(p·x − Et)/ℏ}                   with E = ±√(p²c² + m²c⁴)

Negative-energy solutions: reinterpreted as antiparticles in QFT.
```

### 13.4 Non-Relativistic Limit

```
φ = e^{−imc² t/ℏ} ψ                            factor out rest-energy oscillation

|∂²ψ/∂t²| ≪ mc²/ℏ |∂ψ/∂t|  →  KG → Schrödinger:

iℏ ∂ψ/∂t  =  −(ℏ²/2m) ∇² ψ
```

**Domain:** Relativistic scalar particles — pions, kaons, Higgs boson (before EWSB), axions (candidate), inflaton (candidate). Describes spin-0 particles. Used in QFT as field equation for spin-0 quantized fields. The Higgs field's dynamics before and after EWSB are governed by KG + self-interaction.

---

## 14. Heisenberg Uncertainty Principle (1927)

### 14.1 Standard Formulations

```
Δx · Δp  ≥  ℏ/2                              position-momentum
ΔE · Δt  ≥  ℏ/2                              energy-time (requires care — time is not an operator)
Δθ · ΔL  ≥  ℏ/2                              angle-angular momentum (cyclic variables)
ΔN · Δφ  ≥  ½                                 photon number-phase

General Robertson-Schrödinger inequality:
ΔA · ΔB  ≥  (1/2) |⟨[Â, B̂]⟩|                   for any two Hermitian operators

ΔA · ΔB  ≥  (1/2) |⟨Â B̂ + B̂ Â⟩ − 2⟨Â⟩⟨B̂⟩|²   (more robust — Schödinger)
```

### 14.2 Derivation (Cauchy-Schwarz)

```
Given Hermitian operators Â, B̂:
|⟨ψ|Â B̂|ψ⟩|² ≤ ⟨ψ|Â²|ψ⟩ ⟨ψ|B̂²|ψ⟩           (Cauchy-Schwarz)

Let Â' = Â − ⟨Â⟩, B̂' = B̂ − ⟨B̂⟩ →  ΔA ΔB ≥ ½|⟨[Â,B̂]⟩|
```

### 14.3 Energy-Time "Uncertainty"

The energy-time relation is different — `t` is not a Hermitian operator in standard QM (Pauli's theorem). Several precise formulations:

**Mandelstam-Tamm (1945):**
```
ΔE · τ ≥ ℏ/2

τ  =  ΔA / |d⟨Â⟩/dt|                          lifetime of an observable A
ΔE = energy uncertainty of the state
```

**Decaying state:**
```
dP/dt  =  −Γ P                                exponential decay
P(t)  =  e^{−Γt}  =  e^{−t/τ}

Γ = ℏ/τ = energy width of unstable state
ΔE · τ ≈ ℏ
```

### 14.4 Physical Consequences

- **Zero-point energy:** Harmonic oscillator ground state has `E₀ = ½ ℏω` because `Δx Δp ≥ ℏ/2` prevents `x=0, p=0` simultaneously.
- **Quantum tunneling:** Uncertainty in energy allows short-lived borrowing → tunneling through barriers.
- **Linewidths:** `Γ = ℏ/τ` — short-lived states (hadronic resonances, τ~10⁻²³ s) have GeV-scale widths.
- **Limit on measurement precision:** Any measurement that determines one observable more precisely increases uncertainty in its conjugate.

### 14.5 Experimental Tests

| Test | Result |
|------|--------|
| Neutron interferometry | Δx Δp confirmed |
| Spontaneous emission linewidth | Γ = ℏ/τ confirmed |
| Squeezed states in quantum optics | Δx₁ < ℏ/2Δp₁ while Δx₂ > ℏ/2Δp₂ — below SQL |
| Weak measurement + postselection | Apparent violation is consistent with UP when measurement disturbance accounted for |

**Domain:** All quantum systems. A kinematical theorem following from operator non-commutation. Not a limitation of measurement technology — a fundamental property of quantum states.

---

## 15. Pauli Exclusion Principle + Spin-Statistics Theorem

### 15.1 Statement

```
Fermions (half-integer spin):  total wavefunction antisymmetric under exchange
  ψ(x₁, ..., x_i, ..., x_j, ..., x_N)  =  −ψ(x₁, ..., x_j, ..., x_i, ..., x_N)

Bosons (integer spin):  total wavefunction symmetric under exchange
  ψ(x₁, ..., x_i, ..., x_j, ..., x_N)  =  +ψ(x₁, ..., x_j, ..., x_i, ..., x_N)

Consequence for fermions (Pauli principle):
No two identical fermions can occupy the same quantum state simultaneously.
```

### 15.2 Spin-Statistics Theorem (Fierz 1939, Pauli 1940)

In **relativistic QFT**, the spin-statistics connection is a **theorem**, not an assumption:

```
Microcausality + Lorentz invariance + positive-definite energy + locality
  ⇒  half-integer spin → Fermi-Dirac statistics (anticommutators for field operators)
  ⇒  integer spin → Bose-Einstein statistics (commutators for field operators)
```

Proof relies on `(−1)^{2s}` factor from Lorentz transformation of fields. Violation of spin-statistics would violate causality.

### 15.3 Occupation Number Formalism

**Fermions (Fermi-Dirac statistics):**
```
n_i ∈ {0, 1}                                 occupancy per single-particle state

⟨n_i⟩  =  1 / [e^{(E_i−μ)/k_B T} + 1]       Fermi-Dirac distribution
```

**Bosons (Bose-Einstein statistics):**
```
n_i ∈ {0, 1, 2, ...}                         any integer occupancy

⟨n_i⟩  =  1 / [e^{(E_i−μ)/k_B T} − 1]       Bose-Einstein distribution
```

### 15.4 Physical Consequences of the Pauli Principle

1. **Periodic table** — electron shells fill progressively; chemical properties from outermost shell.
2. **Stability of matter** (Dyson-Lenard theorem): fermionic electrons prevent collapse — without Pauli, all electrons would fall to 1s and matter would be ~10⁵ times smaller.
3. **Neutron star stability** — neutron degeneracy pressure supports stars against gravitational collapse up to ~2–3 M_⊙ (Tolman-Oppenheimer-Volkoff limit). Above this → black hole.
4. **White dwarf stability** — electron degeneracy pressure supports up to ~1.4 M_⊙ (Chandrasekhar limit).
5. **Fermi energy:** `E_F = (ℏ²/2m)(3π²n)^{2/3}` — conduction electrons occupy states up to E_F (several eV in metals).
6. **Nucleon shell model** — nuclear magic numbers from spin-orbit coupled shell filling.

### 15.5 Experimental Constraints on Pauli Violation

```
"VIP" experiment (Gran Sasso):  searched for Pauli-forbidden X-ray transitions
                                Limit: probability of Pauli violation < 4.5×10⁻²⁹

Borexino:  search for Pauli-forbidden nuclear transitions in ¹²C
           β²/2 < 2.6×10⁻³⁷ (Pauli violation parameter)
```

**No violation ever detected.** The Pauli principle is one of the most stringently tested laws in physics.

**Domain:** All quantum identical particles. A theorem in relativistic QFT; experimentally unfalsified to extreme precision.

---

## 16. Feynman Path Integral (1948)

### 16.1 The Fundamental Formula

```
⟨x_f, t_f | x_i, t_i⟩  =  ∫ D[x(t)] exp( i S[x] / ℏ )

S[x]  =  ∫_{t_i}^{t_f} dt L(x, ẋ, t)              classical action

Path measure D[x(t)]:
∫ D[x(t)]  ≡  lim_{N→∞}  Π_{k=1}^{N-1} ∫ dx_k  (m / 2πiℏΔt)^{N/2}
Δt = (t_f−t_i)/N
```

### 16.2 Equivalence to Schrödinger Equation

The path integral propagator:
```
K(x_f, t_f; x_i, t_i)  ≡  ⟨x_f|e^{−iĤ(t_f−t_i)/ℏ}|x_i⟩

ψ(x_f, t_f)  =  ∫ dx_i K(x_f, t_f; x_i, t_i) ψ(x_i, t_i)
```

Infinitesimal time evolution → Schrödinger equation.

### 16.3 Classical Limit ℏ → 0

Stationary phase approximation:
```
δS = 0  →  classical trajectory dominates path integral

Semiclassical expansion:
K  ∼  Σ_{classical paths} A e^{iS_cl/ℏ}

A = √(det ∂²S/∂x_i ∂x_f)                       Van Vleck determinant
```

### 16.4 Euclidean (Imaginary Time) Path Integral

```
t → τ = i t                                       Wick rotation

⟨x_f, τ_f | x_i, τ_i⟩  =  ∫ D[x(τ)] exp( −S_E[x] / ℏ )

S_E[x]  =  ∫_{τ_i}^{τ_f} dτ [ (m/2)(dx/dτ)² + V(x) ]

Path integral becomes well-defined (Gaussian convergence) → statistical mechanics analogy.
```

### 16.5 QFT Path Integral

```
Z[J]  =  ∫ D[φ] exp( i ∫ d⁴x [ℒ(φ) + J φ] )

Generating functional for correlation functions:
⟨0|T{φ(x₁)...φ(x_n)}|0⟩  =  (1/i^n) δ^n Z[J] / δJ(x₁)...δJ(x_n) |_{J=0}

Feynman diagrams emerge from perturbative expansion of exp(i∫ℒ_int).
```

### 16.6 Gaussian Integrals (Free Field)

```
∫ D[φ] exp( −½ ∫ d⁴x φ(x) K(x,y) φ(y) )  ∝  (det K)^{-1/2}

Propagator:  ⟨φ(x) φ(y)⟩ = K^{-1}(x,y)  =  ∫ d⁴p e^{ip·(x−y)} / (p² − m² + iε)
```

**Domain:** Equivalent formulation of quantum mechanics and quantum field theory. Yields identical predictions to operator formalism. Foundation of lattice QFT, instanton calculus, and semiclassical methods.

---

## 17. Navier–Stokes Equations (Fluid Dynamics, 1822–1845)

### 17.1 The Equations

**Compressible, Newtonian fluid:**

```
ρ (∂v/∂t + v·∇v)  =  −∇p  +  μ ∇²v  +  (μ_v + μ/3) ∇(∇·v)  +  ρ g  +  f_ext

∂ρ/∂t  +  ∇ · (ρ v)  =  0                         continuity (mass conservation)

ρ  =  density
v  =  velocity field
p  =  pressure
μ  =  dynamic (shear) viscosity
μ_v = bulk (dilatational) viscosity
```

### 17.2 Incompressible Navier-Stokes (ρ = const)

```
∂v/∂t  +  (v·∇) v  =  −(1/ρ) ∇p  +  ν ∇²v  +  g  +  f_ext/ρ

∇ · v  =  0

ν  ≡  μ/ρ   =  kinematic viscosity
```

### 17.3 Dimensionless Form: Reynolds Number

Non-dimensionalize: `v* = v/U`, `p* = p/(ρU²)`, `t* = t U/L`, `x* = x/L`:

```
∂v*/∂t*  +  (v*·∇*) v*  =  −∇* p*  +  (1/Re) ∇*² v*

Re  ≡  U L / ν          Reynolds number

Re ≪ 1:  laminar flow (viscosity dominates) — Stokes flow
Re ~ 10³–10⁵:  transition to turbulence
Re ≫ 1:  turbulent flow (inertia dominates)
```

**Physical examples:**
| Flow | Re | Regime |
|------|-----|--------|
| Swimming bacterium | 10⁻⁵ | Stokes |
| Blood in capillary | 10⁻³ | Stokes |
| Swimming fish | 10⁵ | Turbulent |
| Airplane wing | 10⁷ | Turbulent |
| Atmospheric weather | 10¹¹ | Fully turbulent |

### 17.4 Exact Solutions

**Poiseuille flow (pressure-driven pipe flow):**
```
v_z(r)  =  (G / 4μ) (R² − r²)                    G = −dp/dz
Q  =  π G R⁴ / 8μ                                volumetric flow rate
```
Hagen-Poiseuille law. Confirmed to incredible precision — used in viscometry.

**Couette flow (shear between moving plates):**
```
v_x(y)  =  U y / h                                shear rate γ̇ = U/h
τ     =  μ γ̇                                      shear stress
```

**Stokes flow (creeping flow past a sphere):**
```
F_drag  =  6π μ R U                                Stokes drag law
C_D    =  24 / Re                                  drag coefficient for Re ≪ 1
```

### 17.5 Vorticity Formulation

```
ω  ≡  ∇ × v                                         vorticity vector

∂ω/∂t  +  v·∇ ω  =  ω·∇ v  +  ν ∇²ω               vorticity transport

For incompressible 2D flow: ω·∇v = 0 → purely advection-diffusion.
```

**Helicity:** `H = ∫ v·ω d³x` — conserved in ideal fluid (ν→0).

### 17.6 Turbulence and the Kolmogorov Theory (1941)

**Energy cascade:** Energy injected at large scale L → cascades through inertial range → dissipated at Kolmogorov scale η.

```
Kolmogorov length scale:  η  =  (ν³/ε)^{1/4}
Kolmogorov time scale:    τ_η = (ν/ε)^{1/2}
Kolmogorov velocity:      v_η = (ν ε)^{1/4}

ε  =  energy dissipation rate per unit mass

Re  =  (L/η)^{4/3}
```

**Kolmogorov energy spectrum (inertial range):**
```
E(k)  =  C_K ε^{2/3} k^{-5/3}                      C_K ≈ 1.5 (Kolmogorov constant)

Valid for: 1/L ≪ k ≪ 1/η
```

**Structure functions:**
```
⟨|v(x+r) − v(x)|^p⟩  ∝  r^{ζ_p}                    ζ_p = p/3 (K41)
                                                                   = p/3 − τ_p/3 (intermittency corrections)
```

Observed in wind tunnels, oceanographic data, atmospheric measurements, and pipe flow over ~5 decades.

### 17.7 Bernoulli's Equation (Inviscid, Steady, Incompressible Along Streamline)

```
p + ½ ρ v² + ρ g z  =  constant                     along streamline

Inviscid, incompressible, steady flow.
Generalized:  ½ v² + ∫ dp/ρ + Φ = constant (compressible, Φ = body force potential).
```

### 17.8 Continuum Hypothesis Validity

Knudsen number: `Kn = λ/L` where `λ` = mean free path, `L` = characteristic length.
```
Kn < 0.01:  continuum (Navier-Stokes valid)
0.01 < Kn < 0.1: slip-flow regime
0.1 < Kn < 10:  transition regime
Kn > 10:        free molecular flow (Boltzmann/BGK needed)
```

Atmospheric mean free path at sea level: λ ≈ 68 nm.

### 17.9 The Millennium Prize Problem

Existence and smoothness of solutions to the 3D incompressible Navier-Stokes equations remain unproven. Despite this, the equations are used to ~10 decimal precision in engineering every day — a deep mathematical mystery.

**Domain:** Newtonian fluids (water, air at subsonic speeds, oils, most common liquids and gases). Underpins aerodynamics, hydrodynamics, meteorology, oceanography, hemodynamics, and industrial fluid processing.

---

## 18. Black Hole Thermodynamics (Bekenstein–Hawking, 1972–1974)

### 18.1 The Four Laws of Black Hole Mechanics (Bardeen-Carter-Hawking 1973)

```
0th Law:  Surface gravity κ is constant over the event horizon of a stationary black hole.
1st Law:  dM  =  (κ/8πG) dA  +  Ω_H dJ  +  Φ_H dQ
2nd Law:  dA/dt  ≥  0                                     (Hawking area theorem, 1971)
3rd Law:  κ cannot be reduced to zero by any finite process.
```

**Mapping to thermodynamics:**
```
E  ↔  M c²                   energy ↔ mass
T  ↔  κc²ℏ/(2πk_B)          Hawking temperature
S  ↔  k_B c³ A / (4Gℏ)      Bekenstein-Hawking entropy
```

### 18.2 Bekenstein-Hawking Entropy and Hawking Temperature

```
S_BH  =  k_B A / 4ℓ_P²  =  k_B c³ A / (4Gℏ)

T_H   =  ℏc³ / (8πGMk_B)                       Schwarzschild BH
T_H   =  ℏc κ / (2πk_B)                         general stationary BH

A  =  4π r_s²  =  16π G² M² / c⁴             Schwarzschild horizon area

T_H(Schwarzschild)  =  6.2×10⁻⁸ K  × (M⊙/M)   negligible for stellar BHs

A  =  8π G²/c⁴ [M² + M√(M²−a²−Q²)]            Kerr-Newman horizon area
```

### 18.3 Hawking Radiation (1974)

**Particle creation in curved spacetime:**
```
⟨N_{ωlm}⟩  =  Γ_{ωlm} / [exp(2πω/κ) ∓ 1]       Planckian spectrum

Γ_{ωlm}  =  greybody factor (absorption probability)

Lifetime for Schwarzschild BH:
τ_evap  ∼  M³ / (3 α ℏ c⁴/G²)  ≈  10⁶⁷ yr × (M/M⊙)³

τ_evap ≈ 10⁻¹⁷ s for M = 10¹⁵ g (primordial BH, if they exist).
```

**Information paradox:** Hawking radiation appears thermal → loss of quantum information. Resolution debated: complementarity, firewalls, fuzzballs, ER=EPR, island formula, holography.

### 18.4 Generalized Second Law (GSL)

```
d/dt (S_BH + S_matter)  ≥  0

S_BH dominates for macroscopic black holes:
S_BH (M⊙ BH)  ≈  10⁷⁷ k_B     vs     S_CMB (observable universe) ≈ 10⁸⁹ k_B
```

GSL has passed all tests accessible with current technology (thought experiments, gravitational wave ringdown tests of area theorem at ~97% confidence for GW150914).

**Domain:** Semiclassical gravity on black hole horizons. Hawking temperature is too small for direct astrophysical detection. LIGO/Virgo ringdown constrains area increase. Analog gravity (sonic BHs in BECs, water waves) observes analogue Hawking radiation.

---

## 19. Weinberg–Salam Electroweak Unification (1967–1968)

### 19.1 The Gauge Structure

```
Gauge group:  SU(2)_L × U(1)_Y

Spontaneous symmetry breaking:  SU(2)_L × U(1)_Y  →  U(1)_EM

Gauge bosons before SSB:
W_μ^i (i=1,2,3):  SU(2)_L gauge fields, coupling g
B_μ:              U(1)_Y gauge field, coupling g'

Higgs field:  Φ = [φ⁺, φ⁰]^T,  Y=+1/2, SU(2) doublet
```

### 19.2 Covariant Derivative and Mass Generation

```
D_μ Φ  =  (∂_μ − i g W_μ^i τ^i/2 − i g' Y B_μ) Φ

After Φ acquires VEV ⟨Φ⟩ = (0, v/√2)^T:

|D_μ Φ|² → mass terms for W^±, Z⁰:

M_W  =  g v / 2  =  80.379 ± 0.012 GeV               (Particle Data Group 2022)
M_Z  =  (v/2)√(g²+g'²)  =  91.1876 ± 0.0021 GeV

Photon remains massless:
A_μ  =  (g' W_μ³ + g B_μ) / √(g²+g'²)               M_γ = 0

Weak mixing angle:
cos θ_W  =  M_W / M_Z  →  sin² θ_W = 1 − M_W²/M_Z²
sin² θ_W  =  0.23121 ± 0.00004                      (on-shell scheme)
            ≈  0.23141                               (MS-bar at m_Z)
```

### 19.3 Weak Currents

**Charged current (W^±):**
```
J_CC^{+μ}  =  Σ_{gen} (ν̄_L γ^μ e_L + ū_L γ^μ d_L)

ℒ_CC  =  (g / 2√2) J_CC^{+μ} W_μ^+  +  h.c.

Fermi constant (from muon decay):
G_F / √2  =  g² / (8 M_W²)  →  G_F  =  1.1663787 × 10⁻⁵ GeV⁻²   (CODATA 2018)

v  =  1 / √(√2 G_F)  =  246.21971 GeV
```

**Neutral current (Z⁰):**
```
J_NC^μ  =  ψ̄ γ^μ (T³ − sin² θ_W Q) ψ

Vector coupling:   g_V  =  T³ − 2 Q sin² θ_W
Axial coupling:    g_A  =  T³

ℒ_NC  =  (g / 2 cos θ_W) J_NC^μ Z_μ
```

**Electromagnetic current:**
```
J_EM^μ  =  Q ψ̄ γ^μ ψ                              Q = T³ + Y (electric charge)

e  =  g sin θ_W  =  g' cos θ_W
α  =  e² / 4π  ≈  1/137.035999084
```

### 19.4 Key Predictions and Discoveries

```
1973: Neutral currents discovered at Gargamelle (CERN) — first confirmation of electroweak model.

1983: W⁺, W⁻, Z⁰ discovered at UA1/UA2 (CERN Spp̄S):
  W bosons in p̄p → ℓ ±ν
  Z boson in p̄p → ℓ⁺ ℓ⁻
  Direct Nobel Prize to Rubbia & van der Meer (1984).

M_W prediction (before discovery):  80–83 GeV
M_W measured:                        80.379 GeV
M_Z prediction (using sin² θ_W):     ~90 GeV
M_Z measured:                        91.1876 GeV

Number of light neutrino species from Z line shape at LEP:
N_ν  =  2.9840 ± 0.0082              consistent with exactly 3.
```

### 19.5 Electroweak Precision Tests

LEP/SLD/Tevatron/LHC global fit (PDG 2022):

```
Observable          Measured               SM Prediction           Pull (σ)
────────────────    ────────               ────────────            ────────
M_W (GeV)           80.379 ± 0.012         80.358 ± 0.006          +0.3
Γ_W (GeV)           2.085 ± 0.042          2.091 ± 0.001           −0.1
M_Z (GeV)           91.1876 ± 0.0021       91.1875 ± 0.0021        0.0
Γ_Z (GeV)           2.4952 ± 0.0023        2.4947 ± 0.0009         +0.2
σ_had⁰ (nb)         41.480 ± 0.033         41.478 ± 0.008          0.0
R_l                 20.767 ± 0.025         20.744 ± 0.018          +0.8
A_FB^l              0.0171 ± 0.0010        0.01627 ± 0.00018       +0.9
A_l (SLD)           0.1513 ± 0.0021        0.1475 ± 0.0008         +1.8
sin² θ_W^eff        0.23153 ± 0.00016      0.23149 ± 0.00013       +0.2
```

Overall χ²/ndf ≈ 22/15 — excellent fit. The 1.8σ deviation in A_l (SLD) is the most notable tension.

### 19.6 Anomalous Triple Gauge Couplings (Beyond SM Test)

```
ℒ_WWV  =  i g_WWV [ g₁^V (W_μν^+ W^{−μ} − W_μν^− W^{+μ}) V^ν
          + κ_V W_μ^+ W_ν^− V^{μν}
          + (λ_V/M_W²) W^{−ν}_μ W^{+ρ}_ν V^μ_ρ ]

SM values at tree level:  g₁^Z = g₁^γ = 1,  κ_Z = κ_γ = 1,  λ_Z = λ_γ = 0

LHC measurements:  all consistent with SM within 1–2σ.
```

**Domain:** Unifies weak force (β-decay) with electromagnetism at ~100 GeV energy scale. The gauge structure SU(2)_L × U(1)_Y spontaneously broken to U(1)_EM by the Higgs mechanism. Confirmed to per-mille level at LEP/SLC/LHC.

---

## 20. Quantum Chromodynamics (QCD, 1973)

### 20.1 The Lagrangian

```
ℒ_QCD  =  Σ_{f=1}^{6} ψ̄_f (i D̸ − m_f) ψ_f  −  ¼ G_a^{μν} G^a_{μν}  +  ℒ_θ

D_μ  =  ∂_μ  −  i g_s A_μ^a T^a          (covariant derivative, SU(3)_c)
T^a   =  λ^a / 2                          (Gell-Mann matrices, 8 generators)
```

The sum runs over 6 quark flavors: up, down, strange, charm, bottom, top (masses from ~2 MeV to ~173 GeV).

### 20.2 Color Gauge Field Strength

```
G_a^{μν}  =  ∂^μ A_a^ν  −  ∂^ν A_a^μ  +  g_s f_{abc} A_b^μ A_c^ν
```

The structure constants `f_{abc}` of SU(3) encode gluon self-interaction — the **three-gluon** and **four-gluon vertices**. This is the source of all non-abelian behavior. No photon analogue exists in QED.

```
Three-gluon vertex:  g_s f_{abc} [g^{μν}(k₁−k₂)^ρ + g^{νρ}(k₂−k₃)^μ + g^{ρμ}(k₃−k₁)^ν]
Four-gluon vertex:  −i g_s² [f_{abe}f_{cde}(g^{μρ}g^{νσ}−g^{μσ}g^{νρ}) + permutations]
```

### 20.3 Feynman Rules (Perturbative QCD)

```
Quark propagator:            i(γ^μ p_μ + m) / (p² − m² + iε)
Gluon propagator (Feynman):  −i g_{μν} δ_{ab} / (k² + iε)
  (in covariant gauge, needs ghost cancellation — Faddeev-Popov procedure)
Ghost propagator:            i δ_{ab} / (k² + iε)
Quark-gluon vertex:          −i g_s γ^μ T^a
Ghost-gluon vertex:          g_s f_{abc} p^μ     (p = outgoing ghost momentum)
```

BRST symmetry ensures unitarity of the gauge-fixed theory. Ghosts are unphysical but necessary for loop calculations — they cancel unphysical timelike/longitudinal gluon polarizations.

### 20.4 Running Coupling and the Beta Function

```
α_s(Q²)  ≡  g_s²(Q²) / 4π

β(α_s)  =  ∂α_s / ∂ ln μ  =  −(b₀/2π) α_s²  −  (b₁/4π²) α_s³  −  ...

b₀  =  11  −  (2/3) n_f              (one-loop coefficient)
b₁  =  102  −  (38/3) n_f            (two-loop coefficient)
```

For `n_f = 6` (all quark flavors active): `b₀ = 7`, so `β < 0` → **asymptotic freedom**.

```
α_s(Q²)  ≈  4π / [b₀ ln(Q²/Λ_QCD²)]        (leading-order solution)

Λ_QCD  ≈  210 ± 14 MeV  (MS-bar scheme)
```

| Scale | α_s value | Technique |
|-------|-----------|-----------|
| m_τ (1.78 GeV) | 0.33 ± 0.01 | τ decays |
| m_Z (91.2 GeV) | 0.1180 ± 0.0009 | global electroweak fit |
| LHC (1 TeV) | ~0.09 | jet cross-sections |
| LHC (10 TeV) | ~0.07 | extrapolation |

Confirmed: α_s decreases with energy over 4 orders of magnitude. The running is **logarithmic**, not a phase transition.

### 20.5 Color Confinement

No free colored particle has ever been observed. Conjectured mechanisms:

**Wilson loop area law (lattice QCD):**

```
⟨W(C)⟩  ∼  exp( −σ · Area(C) )        at large loop size
σ  ≈  (440 MeV)²  ≈  1 GeV/fm          string tension
```

This produces a linear potential at large distances:

```
V_QQ̄(r)  ≈  σ r  −  (4/3) α_s / r  +  constant     (Cornell potential)
```

The linear term means infinite energy to separate quarks to infinity → confinement. When the string stretches beyond ~1 fm, `V(r) > 2 m_q` and pair-creation (`q q̄` from vacuum) breaks the string — **hadronization**.

**Polyakov loop** (order parameter):
```
⟨L⟩ = 0  in confined phase  (Z(3) center symmetry unbroken)
⟨L⟩ ≠ 0  in deconfined phase (Z(3) broken, T > T_c)
```

**Deconfinement transition temperature:**
```
T_c  ≈  155–165 MeV  ≈  1.8 × 10¹² K     (from lattice QCD)
```
Cross-over at physical quark masses (not a sharp phase transition). The quark-gluon plasma (QGP) existed in the early universe for the first ~10 μs and is recreated in heavy-ion collisions at RHIC and LHC.

### 20.6 Chiral Symmetry and Its Breaking

In the limit `m_u, m_d → 0` (chiral limit), the QCD Lagrangian has an exact global symmetry:

```
SU(2)_L × SU(2)_R × U(1)_V × U(1)_A
```

- `U(1)_V` → **baryon number** (exact)
- `U(1)_A` → broken by **axial anomaly** (instanton effects, η' mass)
- `SU(2)_L × SU(2)_R` → **spontaneously broken** by quark condensate:

```
⟨ψ̄ ψ⟩  ≡  ⟨ū u⟩  =  ⟨d̄ d⟩  ≈  −(250 MeV)³  ≠  0

SU(2)_L × SU(2)_R  →  SU(2)_V   (isospin)
```

Goldstone's theorem → 3 massless pseudoscalar bosons. Since `m_u, m_d` are small but non-zero, the pions have small masses:

```
m_π²  =  −(m_u + m_d) ⟨ψ̄ ψ⟩ / f_π²              (Gell-Mann–Oakes–Renner relation)

f_π  ≈  92.2 MeV      (pion decay constant, measured from π⁺ → μ⁺ ν_μ)
m_π⁰  =  134.977 MeV
m_π±  =  139.570 MeV
```

Extending to SU(3) flavor (including strange quark):

```
SU(3)_L × SU(3)_R  →  SU(3)_V           (octet of pseudoscalar mesons)
m_K²  =  −(m_s + m_{u,d}) ⟨ψ̄ ψ⟩ / f_K² / 2
```

The proton mass decomposition (from lattice QCD + phenomenological analysis):

```
M_proton  ≈  938.272 MeV

Trace anomaly (gluon field energy):  ~90–95%          (scale anomaly in QCD)
Quark kinetic energy + masses:       ~5–10%
Quark masses (Higgs coupling):       ~1–2%  ≈  9 MeV  (σ_πN term)
```

**Only ~1% of your mass comes from the Higgs mechanism.** The rest is pure QCD binding energy.

### 20.7 Chiral Perturbation Theory (χPT)

Low-energy effective field theory of QCD (E ≪ 4πf_π ≈ 1.2 GeV):

```
ℒ_χPT  =  (f_π²/4) Tr[∂_μ U ∂^μ U†]  +  (f_π²/4) Tr[χ U† + U χ†]  +  ...

U  =  exp(i π^a λ^a / f_π)            (nonlinear sigma model field)
χ  =  2B₀ M                (M = quark mass matrix, B₀ = −⟨ψ̄ ψ⟩/f_π²)
```

Expands in powers of `(p/Λ_χ)²` where `Λ_χ ≈ 4πf_π`. Matches to QCD order-by-order. Used for low-energy ππ scattering, pion-nucleon interactions, and lattice extrapolations.

### 20.8 U(1)_A Anomaly and the Strong CP Problem

The axial anomaly:

```
∂_μ J_5^μ  =  (g_s² N_f / 16π²) G_a^{μν} G̃_a_{μν}           (Adler-Bell-Jackiw)

G̃_a^{μν}  =  (1/2) ε^{μνρσ} G_a^{ρσ}                        (dual field strength)
```

The θ-term allowed by gauge invariance:

```
ℒ_θ  =  θ (g_s² / 64π²) ε^{μνρσ} G_a^{μν} G_a^{ρσ}        (CP-violating)
```

The neutron electric dipole moment constrains:

```
|θ̄|  =  |θ_QCD + Arg det M_q|  <  10⁻¹⁰

d_n  <  1.8 × 10⁻²⁶ e·cm    (90% CL, experimental bound)
→  |θ̄|  ≲  10⁻¹⁰
```

This is the **strong CP problem**: why is θ̄ so small when it could be O(1)? Leading solution: Peccei-Quinn mechanism → **axion** (actively searched for by ADMX, CAST, etc.).

### 20.9 Hadron Spectrum

**Mesons (q q̄ bound states):**

```
Lightest pseudoscalar octet (J^P = 0⁻):
  π⁰, π⁺, π⁻       (u, d only)
  K⁺, K⁰, K̄⁰, K⁻  (u,d + s)
  η                 (mixing: (uū+d d̄−2ss̄)/√6)
  η′                (U(1)_A anomaly gives extra mass)

Vector meson nonet (J^P = 1⁻):
  ρ⁰, ρ⁺, ρ⁻, ω, K*⁺, K*⁰, K̄*⁰, K*⁻, φ

Scalar mesons (J^P = 0⁺) and higher excitations extend to ~3 GeV
```

**Baryons (3-quark bound states, qqq):**

```
Nucleon octet (J^P = ½⁺):    p, n, Λ, Σ⁺, Σ⁰, Σ⁻, Ξ⁰, Ξ⁻
Delta decuplet (J^P = ³⁄₂⁺): Δ⁺⁺, Δ⁺, Δ⁰, Δ⁻, Σ*⁺, Σ*⁰, Σ*⁻, Ξ*⁰, Ξ*⁻, Ω⁻
```

The Ω⁻ was predicted by the quark model (SU(3) flavor) and discovered in 1964 — one of QCD's early triumphs before QCD existed.

All masses up to ~2.5 GeV have been computed in lattice QCD with <1% error, including the nucleon mass.

### 20.10 Exotic Hadrons (Tetraquarks, Pentaquarks, Glueballs)

QCD permits color-singlet states beyond `q q̄` and `qqq`:

**Tetraquarks** (q q q̄ q̄): Z_c(3900), Z_c(4430), X(3872) — many confirmed at BESIII, LHCb, Belle. The X(3872) sits within 0.1 MeV of the D⁰ D̄*⁰ threshold.

**Pentaquarks** (q q q q q̄): P_c(4380), P_c(4450) → observed by LHCb in Λ_b → J/ψ p K decays (2015, updated 2019 with 3 narrow states).

**Glueballs** (gg, ggg — pure gauge excitations):
- Lightest predicted scalar glueball: `J^PC = 0⁺⁺`, m ≈ 1.5–1.7 GeV (lattice QCD)
- Candidates: f₀(1500), f₀(1710) — but mixing with ordinary mesons makes unambiguous identification difficult.
- Tensor glueball (`2⁺⁺`, m ≈ 2.4 GeV) — also predicted, not confirmed.

**Hybrid mesons** (q q̄ g): π₁(1600) with `J^PC = 1⁻⁺` (exotic quantum numbers impossible for `q q̄`). Evidence from COMPASS and GlueX experiments.

### 20.11 Deep Inelastic Scattering, Parton Distribution Functions, Factorization

**DIS kinematics** (e⁻ + p → e⁻ + X):

```
Q²  =  −q²                       (virtuality of exchanged photon)
x   =  Q² / (2 P·q)              (Bjorken-x, momentum fraction of struck parton)
ν   =  P·q / M_p                 (energy transfer in target rest frame)
W²  =  M_p² + Q²(1/x − 1)       (invariant mass of hadronic final state)
```

**Structure functions:**

```
d²σ / dx dQ²  =  (4πα² / x Q⁴) [ (1−y) F₂(x,Q²) + y² F₁(x,Q²) ]

F₁(x,Q²)  =  (1/2) Σ_q e_q² [q(x,Q²) + q̄(x,Q²)]       (Callan-Gross relation for spin-½)
F₂(x,Q²)  =  x Σ_q e_q² [q(x,Q²) + q̄(x,Q²)]
```

Callan-Gross (`F₂ = 2x F₁`) confirmed at SLAC (1969) → quarks are spin-½.

**DGLAP evolution** (Dokshitzer-Gribov-Lipatov-Altarelli-Parisi):

```
∂q(x,Q²)/∂ ln Q²  =  (α_s/2π) ∫_x¹ (dz/z) [P_{qq}(z) q(x/z,Q²) + P_{qg}(z) g(x/z,Q²)]

∂g(x,Q²)/∂ ln Q²  =  (α_s/2π) ∫_x¹ (dz/z) [P_{gq}(z) Σ q(x/z,Q²) + P_{gg}(z) g(x/z,Q²)]
```

Splitting functions at LO:
```
P_{qq}(z)  =  (4/3) (1+z²)/(1−z)_+  +  2 δ(1−z)
P_{qg}(z)  =  (1/2) [z² + (1−z)²]
P_{gq}(z)  =  (4/3) [1 + (1−z)²]/z
P_{gg}(z)  =  6 [z/(1−z)_+ + (1−z)/z + z(1−z)] + (11/2 − n_f/3) δ(1−z)
```

These predict how PDFs scale with Q². Confirmed from HERA (≈1 GeV²) to LHC (≈10⁴ GeV²).

**Factorization theorem:**
```
dσ_{AB→X}  =  Σ_{a,b} ∫ dx_a dx_b  f_a/A(x_a, μ_F) f_b/B(x_b, μ_F)  ·  dσ̂_{ab→X}(μ_R, μ_F)
```
Short-distance (`dσ̂`, calculable in pQCD) and long-distance (PDFs, universal/non-perturbative but measurable) factorize at leading twist. Foundation of all LHC precision physics.

### 20.12 Jets, Event Shapes, and Infrared Safety

A **jet** is a collimated spray of hadrons from a fragmenting high-energy parton. Jet algorithms:

**Anti-k_T algorithm** (Cacciari-Salam-Soyez, 2008):
```
d_{ij}  =  min(p_{Ti}^{-2}, p_{Tj}^{-2}) · ΔR_{ij}² / R²      (d_{iB} = p_{Ti}^{-2})
Merge smallest d_{ij}; if d_{iB} < d_{ij}, i becomes a jet.
```

Jet cross-sections measured at LHC agree with NNLO QCD predictions to ~5% over 8 orders of magnitude.

**Event shape variables** (e⁻e⁻ colliders):
```
Thrust:         T  =  max_{n̂} (Σ_i |p_i·n̂|) / (Σ_i |p_i|)          (T→1 for two back-to-back jets)
C-parameter:    C  =  3(λ₁λ₂ + λ₂λ₃ + λ₃λ₁)                           (linearized momentum tensor)
Broadening:     B_T, B_W                                                    (transverse/w.r.t thrust axis)
```

N³LL resummation + NNLO fixed-order matches LEP data to sub-percent precision.

**Infrared and collinear safety:** Observables must be insensitive to soft gluons and collinear splittings. This ensures finite perturbative predictions. All standard jet/event variables are IRC-safe.

### 20.13 Quark-Gluon Plasma (QGP)

Above T ≈ 155 MeV, hadrons "melt" into a deconfined medium of quarks and gluons. Heavy-ion collisions (Au-Au at RHIC, Pb-Pb at LHC) produce droplets of QGP.

**Signatures:**

**Jet quenching** — high-pT partons lose energy traversing the medium:
```
ΔE  ∼  C_R (α_s/4) q̂ L²                          (BDMPS energy loss, radiative)
q̂  ∼  1–10 GeV²/fm                                 (transport coefficient, extracted from data)
```
Manifested as dijet energy asymmetry and suppression of high-pT hadrons (R_AA < 1):

```
R_AA(p_T)  =  (dN_AA/dp_T) / [N_coll · (dN_pp/dp_T)]
```
R_AA ≈ 0.2–0.5 at RHIC/LHC central collisions — strong suppression.

**Elliptic flow (v₂):** pressure-driven anisotropy in non-central collisions. The QGP behaves as a near-perfect fluid (nearly inviscid):

```
η/s  ≈  1/4π  ≈  0.08                              (shear viscosity / entropy density)
```
This is conjectured to be a lower bound from AdS/CFT (Kovtun-Son-Starinets). The QGP is the most perfect fluid known.

**Quarkonium suppression (Matsui-Satz, 1986):** Debye screening in QGP dissolves quarkonium states sequentially:
```
J/ψ dissolves at T ≈ 1.5 T_c      (tightly bound, survives moderate QGP)
ψ'  dissolves at T ≈ 1.1 T_c      (loosely bound, "melts" early)
Υ(1S) survives to > 2 T_c         (very tightly bound, bottomonia thermometers)
```
Observed as sequential suppression pattern at SPS, RHIC, LHC.

**Electromagnetic probes:** Real and virtual photons escape the QGP without further interaction → direct thermometer. Thermal photon v₂ and direct photon spectra at RHIC/LHC are consistent with hydrodynamics + QGP radiation.

### 20.14 QCD Phase Diagram

```
                          Temperature
                              ↑
                        200 MeV ──── QUARK-GLUON PLASMA ──────
                              |   \                           \
                        155 MeV|    \   CROSSOVER               \  (1st order?)
                              |     \                           \
                              |      ──── HADRONS ───────────────
                              |          (confined, chiral broken)
                              |
                              |←────── μ_B ──────────────────────→
                         0   μ_B    ~900 MeV              μ_B
                        (LHC)                              (neutron stars)
```

- **Crossover** at μ_B ≈ 0 (confirmed by lattice QCD — no critical point at zero density).
- **Critical endpoint** predicted at μ_B ≈ 300–500 MeV, T ≈ 120–160 MeV (Beam Energy Scan at RHIC searching for it).
- **First-order phase transition** at large μ_B (cold, dense matter — neutron star interiors).
- **Color superconductivity**: at μ_B ≳ 400 MeV and low T, quarks form Cooper pairs → CFL (Color-Flavor-Locked) phase deep in neutron star cores.

### 20.15 Lattice QCD

Monte Carlo evaluation of the Euclidean path integral on a discrete spacetime grid:

```
⟨O⟩  =  (1/Z) ∫ D[U] D[ψ] D[ψ̄]  O[U, ψ, ψ̄]  exp(−S_E[U, ψ, ψ̄])

S_E^g  =  β Σ_□ (1 − (1/3) Re Tr U_□)            (Wilson gauge action, β = 6/g²)
S_E^q  =  ψ̄ D_W ψ                                  (Wilson/Staggered/DWF/Overlap fermions)
```

**Spectrum results:** Nucleon mass, pion mass, kaon mass, Δ mass, Ω⁻ mass, and excited-state masses computed with <1% systematic error. Light hadrons agree with experiment.

**Hadronic contributions to g−2:**
```
a_μ^{HVP}  =  692.8 ± 2.4 × 10⁻¹⁰           (lattice QCD, BMW collaboration 2020)
```
Tension with R-ratio dispersive method (~2σ). Crucial for interpreting the Muon g−2 experiment at Fermilab.

**Computational cost:** Scaling as `a^{-n} V L_t` with `a` the lattice spacing (continuum limit `a → 0`). Full QCD at physical pion mass requires petaflop-scale computing.

### 20.16 Soft-Collinear Effective Theory (SCET)

Effective field theory for QCD with highly boosted particles. Separates dynamics into distinct momentum regions:

```
SCET_I:  p² ∼ (Qλ², Qλ², Q²)       (e.g. B → ππ, endpoint regions)
SCET_II: p² ∼ (Qλ², Qλ, Q)         (e.g. Drell-Yan at small q_T)

Collinear fields: ξ_n(x)            (momentum along light-cone direction n)
Soft fields: q_s(x)                 (low-momentum modes)
```

SCET factorizes multi-scale processes and enables resummation of large Sudakov logarithms (e.g. `ln Q/m_b`, `ln τ Q`). Essential for precision B-physics at LHCb and Belle II.

### 20.17 Experimental Verification Summary

| Prediction | Test | Precision | Status |
|------------|------|-----------|--------|
| Asymptotic freedom | HERA, LHC DIS | α_s running over 4 decades | Confirmed |
| Jet cross-sections | LHC, Tevatron, LEP | 5% agreement with NNLO | Confirmed |
| DGLAP evolution | HERA → LHC | PDFs scale correctly across 10³ in Q² | Confirmed |
| Confinement | Absence of free quarks | Limit: σ < 10⁻²¹ cm² for free quarks | Confirmed |
| Chiral symmetry breaking | Pion mass, GOR relation | <1% | Confirmed |
| Hadron spectrum (light) | Lattice QCD | <1% for ground states | Confirmed |
| Hadron spectrum (excited) | Lattice + experiment | ~1–5% | Confirmed |
| Quark-gluon plasma | RHIC, LHC heavy-ion | v₂, R_AA, jet quenching | Confirmed |
| Tetraquarks / Pentaquarks | BESIII, LHCb, Belle | >5σ observations | Confirmed |
| Glueballs | Lattice predicts, exp. ambiguous | Candidates but no unambiguous ID | Active |
| Strong CP (θ ≪ 1) | nEDM bounds | θ̄ < 10⁻¹⁰ | Confirmed (problem remains) |
| Factorization | LHC, Tevatron | Global PDF fits consistent | Confirmed |
| Higgs production via ggF | LHC | ~10% agreement with NNLO QCD | Confirmed |
| α_s(m_Z) | Global average | 0.1180 ± 0.0009 | Confirmed |

**Domain:** The strong nuclear force. SU(3)_c non-abelian gauge theory. Tested from femtometer scales (nucleon structure) to LHC energies (~10 TeV). **Zero falsifications of any core prediction.**

---

## 21. Lorentz Invariance (Special Relativity, 1905)

```
ds²  =  η_μν dx^μ dx^ν  =  −c²dt² + dx² + dy² + dz²
Physical laws are identical in all inertial frames.
c is the same in all inertial frames.
```

**Domain:** Flat spacetime. Tested to extreme precision by Michelson-Morley, Kennedy-Thorndike, Hughes-Drever, modern optical-resonator experiments, and every particle accelerator ever built. Lorentz violation is constrained to < 10⁻¹⁷ in some parameters.

---

## 22. Einstein's Mass–Energy Equivalence (1905)

```
E²  =  (mc²)²  +  (pc)²
E  =  γmc²          (massive particle)
E  =  pc             (massless particle)
```

**Domain:** Every relativistic system. Tested in nuclear reactions (mass defect ≈ energy release), particle-antiparticle annihilation, and every synchrotron/cyclotron. E = mc² is the low-momentum limit.

---

## 23. Fermi's Golden Rule (Perturbation Theory)

```
Γ_{i→f}  =  (2π/ℏ) |⟨f|Ĥ'|i⟩|²  ρ(E_f)
```

**Domain:** Weak perturbations in QM. Underpins calculation of decay rates, scattering cross-sections, transition probabilities. Used in every branch of quantum physics. Derived from time-dependent perturbation theory — exact in the limit of weak coupling and long times.

---

## 24. Boltzmann Transport Equation (1872)

```
∂f/∂t  +  v·∇_r f  +  (F/m)·∇_v f  =  (∂f/∂t)_coll
```

**Domain:** Non-equilibrium statistical mechanics. Underpins plasma physics, semiconductor transport, neutron diffusion, galactic dynamics. The H-theorem (entropy increase) is a direct consequence.

---

## 25. Quantization of Electric Charge / Dirac Quantization Condition

```
Q_e  =  −e   (electron charge, exactly e)
Magnetic monopole charge g satisfies:  e·g  =  2πℏn  (n ∈ ℤ)
```

**Domain:** All of electromagnetism. Charge is quantized in units of e/3 (quark confinement hides fractional charges). The Dirac condition shows that if *one* magnetic monopole exists anywhere, *electric charge must be quantized everywhere*. No monopole found yet, but the condition is a theorem.

---

## 26. Optical Theorem (Unitarity)

```
Im[ f(θ=0) ]  =  (k/4π) σ_total
```

**Domain:** All scattering processes. A consequence of unitarity (probability conservation). Tested in every scattering experiment. Forward scattering amplitude's imaginary part directly gives the total cross-section.

---

## 27. Einstein Coefficients (1917)

```
A_21     =  spontaneous emission rate
B_12     =  absorption coefficient
B_21     =  stimulated emission coefficient

B_12/B_21 = g₂/g₁
A_21/B_21 = 8πhν³/c³
```

**Domain:** Atomic/molecular transitions. Derivation requires detailed balance and Planck's law. Underpins lasers, astrophysical spectroscopy, and atomic clocks. The ratio relations are exact consequences of thermodynamic equilibrium.

---

## 28. Equivalence Principle (Weak, Einstein Equivalence)

```
Inertial mass  =  Gravitational mass
(universality of free fall)
```

**Domain:** All gravitating bodies. Tested by Eötvös, Dicke, Braginsky, MICROSCOPE satellite to ~10⁻¹⁵. No violation. The foundation of GR.

---

## Summary Table

| # | Equation / Law | Domain | Last Falsified |
|---|---------------|--------|----------------|
| 1 | Maxwell | Classical E&M | Never |
| 2 | Einstein Field Equations | Gravity (GR) | Never |
| 3 | Schrödinger | Non-rel QM | Never |
| 4 | Dirac | Rel spin-½ | Never |
| 5 | Newton's 2nd (F=dp/dt) | Low-velocity mechanics | Never (relativistic correction, not falsified) |
| 6 | Energy Conservation | Universal | Never |
| 7 | 2nd Law of Thermo | Macroscopic systems | Never |
| 8 | E = hν | Quantum systems | Never |
| 9 | Standard Model Lagrangian | Particle physics | Never (neutrino masses are the only SM extension) |
| 10 | Yang-Mills | Gauge theory | Never |
| 11 | Noether's Theorem | All of physics | Mathematical theorem — can't be falsified |
| 12 | Friedmann | Cosmology | Never (ΛCDM fits all data) |
| 13 | Klein-Gordon | Rel spin-0 | Never |
| 14 | Heisenberg Uncertainty | Quantum systems | Never |
| 15 | Pauli Exclusion | Quantum statistics | Never |
| 16 | Path Integral | QM / QFT | Never |
| 17 | Navier-Stokes | Fluid dynamics | Never |
| 18 | Black Hole Thermo | Semiclassical gravity | Not directly falsifiable yet |
| 19 | Electroweak Unification | Particle physics | Never |
| 20 | QCD | Strong force | Never |
| 21 | Lorentz Invariance | Spacetime | Never |
| 22 | E² = (mc²)² + (pc)² | Relativity | Never |
| 23 | Fermi's Golden Rule | QM perturbation | Never |
| 24 | Boltzmann Transport | Non-equilibrium stat mech | Never |
| 25 | Charge Quantization | E&M | Never |
| 26 | Optical Theorem | Scattering | Never |
| 27 | Einstein Coefficients | Atomic transitions | Never |
| 28 | Equivalence Principle | Gravity | Never |

---

## What These Equations Do NOT Explain (Open Problems)

- **Quantum gravity** — GR and QM are mutually inconsistent at the Planck scale.
- **Dark matter** — evidence is overwhelming (rotation curves, CMB, lensing, bullet cluster), but no particle identification.
- **Dark energy** — Λ fits data, but the *value* is 10¹²⁰ smaller than QFT vacuum energy prediction.
- **Baryon asymmetry** — why does the universe contain matter, not equal matter/antimatter?
- **Neutrino masses** — require physics beyond the minimal SM (seesaw mechanism? Dirac? Majorana?).
- **Strong CP problem** — why is the QCD θ-angle < 10⁻¹⁰? (axion?)
- **Hierarchy problem** — why is the Higgs mass so light compared to the Planck scale?
- **Initial conditions** — what set the entropy and homogeneity of the early universe? (Inflation fits data but mechanism is speculative.)
- **Interpretation of QM** — the equations work; what they *mean* is debated (Copenhagen, Many-Worlds, de Broglie-Bohm, QBism).
- **Measurement problem** — why does "observation" collapse the wavefunction?

Every equation above continues to survive. The questions live in the gaps *between* them.
