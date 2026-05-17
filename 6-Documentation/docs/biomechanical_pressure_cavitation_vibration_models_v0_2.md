# Biomechanical Pressure–Cavitation–Vibration Model Catalog v0.2

**Scope:** Pressure gradients, cavitation, shockwave propagation, hydrodynamic vibration, lateral-line sensing, suction, jetting, hydraulic actuation, osmotic projectiles, and Burgers-style shock smoothing.

**Status:** Working review file. This is not a final paper. It is a model inventory and stress-test scaffold for later Lean-facing adapters, simulations, and evidence receipts.

**Update basis:** This version folds in the attached cavitation / Acoustic-Crystalline Water / Burgers stress-test notes and separates:
1. documented peer-reviewed model families,
2. idealized test-material assumptions,
3. speculative or unverified quantitative claims that need receipts.

---

## 0. Core Adapter Schema

A species or material system enters the framework through an adapter:

\[
\alpha_S : X_S \rightarrow U(\xi,\tau)
\]

where \(X_S\) is the native physical state and \(U\) is a normalized dimensionless field.

For pressure/cavitation/vibration systems:

\[
X_S =
(P,\rho,\mu,\sigma,c,R,\dot R,\mathbf{u},\nabla P,\nabla \mathbf{u},f,t,\Omega)
\]

\[
U(\xi,\tau)
=
w_P\widehat{\Delta P}
+
w_u\|\hat{\mathbf{u}}\|
+
w_R\hat R
+
w_{\nabla P}\|\widehat{\nabla P}\|
+
w_f \hat f
\]

A general residual layer can then test propagation or shock-like deviations:

\[
R(U;\epsilon)
=
\partial_\tau U
+
U\partial_\xi U
-
\epsilon\partial_{\xi\xi}U
\]

This is only an adapter-level diagnostic; it is not a replacement for full fluid equations.

---

# 1. Cavitation Bubble Dynamics

## 1.1 Rayleigh–Plesset Equation

**Use:** Spherical bubble growth/collapse in an incompressible liquid.

\[
\rho_l
\left(
R\ddot R + \frac{3}{2}\dot R^2
\right)
=
P_B(R,t)
-
P_\infty(t)
-
\frac{2\sigma}{R}
-
\frac{4\mu \dot R}{R}
\]

A common gas-pressure closure is:

\[
P_B(R)
=
\left(
P_{\infty,0}
+
\frac{2\sigma}{R_0}
\right)
\left(
\frac{R_0}{R}
\right)^{3\gamma}
+
P_v
\]

### Variables

| Symbol | Meaning |
|---|---|
| \(R(t)\) | bubble radius |
| \(\rho_l\) | liquid density |
| \(\sigma\) | surface tension |
| \(\mu\) | liquid viscosity |
| \(\gamma\) | polytropic gas index |
| \(P_\infty(t)\) | far-field liquid pressure |
| \(P_v\) | vapor pressure |
| \(P_B\) | internal bubble pressure |

### Strengths

- Excellent baseline for growth/collapse timing.
- Good for subsonic spherical collapse.
- Common first model for cavitation, sonoluminescence, and snapping-shrimp bubble radius fitting.

### Failure modes

- Assumes incompressible liquid.
- Cannot directly model acoustic radiation or shock emission.
- Can become singular or overpredict collapse intensity when compressibility matters.

### Evidence anchor

Versluis et al. reported that snapping shrimp sound is emitted at cavitation bubble collapse and that a Rayleigh–Plesset-type model quantitatively accounts for bubble radius time-dependence and emitted sound.

---

## 1.2 Keller–Miksis Equation

**Use:** Weakly compressible bubble dynamics; includes first-order acoustic radiation terms.

\[
\left(1-\frac{\dot R}{c}\right)R\ddot R
+
\frac{3}{2}\dot R^2
\left(1-\frac{\dot R}{3c}\right)
=
\frac{1}{\rho_l}
\left(
1+\frac{\dot R}{c}
+
\frac{R}{c}\frac{d}{dt}
\right)
[
P_B(R,\dot R)-P_\infty(t)
]
\]

### Added physics

| Term | Role |
|---|---|
| \(c\) | liquid sound speed |
| \(\dot R/c\) | bubble-wall Mach correction |
| \(R/c \cdot d/dt\) | acoustic radiation / compressibility correction |

### Strengths

- Better than Rayleigh–Plesset for sonoluminescence, ultrasound cavitation, and moderate collapse.
- Captures acoustic damping.

### Failure modes

- First-order compressibility only.
- Less reliable for very high Mach collapse, strong shocks, and highly nonlinear equations of state.

---

## 1.3 Gilmore Equation / Gilmore–Akulichev Type Models

**Use:** High-amplitude, compressible bubble collapse using liquid enthalpy and pressure-dependent sound speed.

\[
R\ddot R
\left(
1-\frac{\dot R}{C}
\right)
+
\frac{3}{2}\dot R^2
\left(
1-\frac{\dot R}{3C}
\right)
=
H
\left(
1+\frac{\dot R}{C}
\right)
+
\frac{R}{C}\dot H
\left(
1-\frac{\dot R}{C}
\right)
\]

where:

\[
H = \int_{P_\infty}^{P_R}\frac{dP}{\rho(P)}
\]

### Strengths

- Better for high-pressure collapse and shock generation.
- Natural fit with Tait-like equations of state.
- More physically grounded when wall velocity approaches liquid sound speed.

### Failure modes

- Still assumes spherical symmetry unless coupled to CFD.
- Needs reliable liquid equation of state.
- May fail under plasma, ionization, chemistry, phase change, and strong non-spherical jetting.

---

## 1.4 Tait Equation of State

**Use:** Pressure-density relation for water-like liquids under compression.

A common Tait form:

\[
P + B
=
(P_0+B)
\left(
\frac{\rho}{\rho_0}
\right)^n
\]

Equivalent shifted form:

\[
P
=
B
\left[
\left(
\frac{\rho}{\rho_0}
\right)^n
-
1
\right]
+
P_0
\]

Approximate water values near room temperature often use:

\[
n \approx 7.15
\]

\[
B \approx 300\ \text{MPa}
\]

### Derived sound speed

\[
c^2
=
\left(
\frac{\partial P}{\partial \rho}
\right)_s
=
\frac{n(P+B)}{\rho}
\]

### Use in framework

Gilmore + Tait gives the best compact model for high-amplitude cavitation shock estimates before switching to full compressible CFD.

---

## 1.5 Rayleigh–Plesset-Based Homogeneous Mixture Models

**Use:** CFD cavitating-flow model with vapor/liquid mixture.

Mixture continuity:

\[
\frac{\partial \rho_m}{\partial t}
+
\nabla\cdot(\rho_m\mathbf{u})
=
0
\]

Momentum:

\[
\frac{\partial \rho_m\mathbf{u}}{\partial t}
+
\nabla\cdot(\rho_m\mathbf{u}\mathbf{u})
=
-\nabla p
+
\nabla\cdot\boldsymbol{\tau}
+
\mathbf{f}
\]

Void fraction relation:

\[
\rho_m
=
\alpha_v\rho_v
+
(1-\alpha_v)\rho_l
\]

Transport:

\[
\frac{\partial \alpha_v}{\partial t}
+
\nabla\cdot(\alpha_v\mathbf{u})
=
\dot m_{\text{vap}}-\dot m_{\text{cond}}
\]

Rayleigh–Plesset-type growth supplies source terms:

\[
\dot R = \mathcal{F}(P_v-P,\rho,\sigma,\mu,R)
\]

### Use cases

- Snapping shrimp claw CFD.
- Cavitating jets.
- Hydrofoils.
- Bubble clouds.
- Bioinspired snapping plunger devices.

---

# 2. Cavitation Shockwave Properties

## 2.1 Collapse Pressure Estimate

Far-field acoustic pressure from a spherical bubble can be approximated by source acceleration:

\[
p(r,t)
\approx
\frac{\rho_l}{r}
\frac{d}{dt}
\left(
R^2\dot R
\right)
\]

Expanding:

\[
p(r,t)
\approx
\frac{\rho_l}{r}
\left(
2R\dot R^2 + R^2\ddot R
\right)
\]

Near collapse, \(R^2\ddot R\) and \(R\dot R^2\) can generate extremely sharp pressure pulses.

## 2.2 Shock Decay

Ideal spherical acoustic decay:

\[
P(r) \propto \frac{1}{r}
\]

Near-field nonlinear shock decay is usually stronger:

\[
P(r) \propto \frac{1}{r^\alpha}
\]

with:

\[
\alpha > 1
\]

The value of \(\alpha\) depends on amplitude, equation of state, viscosity, thermal conduction, geometry, and bubble asymmetry.

## 2.3 Microjet Water-Hammer Pressure

For asymmetric collapse near boundaries:

\[
P_{\text{hammer}}
\approx
\rho c v_{\text{jet}}
\]

where \(v_{\text{jet}}\) is the microjet impact speed.

This is separate from the spherical acoustic shock.

## 2.4 Collapse Energy

Bubble potential energy at maximum radius can be approximated by:

\[
E_B
\approx
\frac{4\pi}{3}
R_{\max}^3
(P_\infty - P_v)
\]

Shock/radiated fraction:

\[
E_{\text{shock}}
=
\eta_{\text{shock}}E_B
\]

where \(\eta_{\text{shock}}\) must be measured or modeled. It is not a universal constant.

---

# 3. Idealized Test Medium: Acoustic-Crystalline Water

## 3.1 Definition

**Acoustic-Crystalline Water (ACW)** is an idealized water-like continuum for model stress testing.

### ACW assumptions

| Property | ACW value / rule |
|---|---|
| Structure | homogeneous continuum |
| Dissolved gas | none |
| Microbubble nuclei | none |
| Surface tension | \(\sigma = 0.072\ \text{N/m}\) |
| Speed of sound | \(c_0 \approx 1500\ \text{m/s}\) |
| EOS | Tait equation |
| Viscosity | either real water or inviscid test limit |
| Thermal conduction | explicit switch: off / on |
| Phase change | explicit switch: off / on |

## 3.2 Use

ACW is not a claim about a real material. It is a controlled mathematical substrate for comparing:

1. Rayleigh–Plesset,
2. Keller–Miksis,
3. Gilmore + Tait,
4. compressible CFD,
5. Burgers shock propagation.

## 3.3 Reality-tether table

| Parameter | Real water near 20 °C | ACW default | Notes |
|---|---:|---:|---|
| Density \(\rho\) | ~998 kg/m³ | 1000 kg/m³ | close |
| Speed of sound \(c\) | ~1482 m/s | 1500 m/s | close |
| Dynamic viscosity \(\mu\) | ~1.0e-3 Pa·s | switchable | inviscid is a ceiling case |
| Surface tension \(\sigma\) | ~0.072 N/m | 0.072 N/m | close |
| Vapor pressure \(P_v\) | ~2.3 kPa | switchable | neglecting it exaggerates collapse |
| Dissolved gas | present | absent | ACW overpredicts collapse cleanliness |

## 3.4 Caution

The uploaded notes propose strong numerical statements such as extreme shock-front thickness and Mach cutoff values. These should remain **provisional** unless backed by experimental or simulation receipts.

---

# 4. Burgers Equation as Shock-Propagation Bridge

## 4.1 Inviscid Burgers Equation

\[
\partial_t u + u\partial_x u = 0
\]

### Characteristic solution

\[
u(x,t) = u_0(\xi)
\]

\[
x = \xi + u_0(\xi)t
\]

Shock forms when:

\[
\frac{\partial x}{\partial \xi}
=
1 + u_0'(\xi)t
=
0
\]

Earliest shock time:

\[
t_s
=
-\frac{1}{\min u_0'(\xi)}
\]

for \(\min u_0'(\xi)<0\).

### Relevance

Models nonlinear steepening of a pressure pulse but cannot model physical shock thickness.

---

## 4.2 Viscous Burgers Equation

\[
\partial_t u
+
u\partial_x u
=
\nu\partial_{xx}u
\]

### Cole–Hopf transform

Let:

\[
u = -2\nu \partial_x \ln \phi
\]

Then:

\[
\partial_t \phi = \nu \partial_{xx}\phi
\]

### Traveling shock solution

For left/right states \(u_L > u_R\):

\[
u(x,t)
=
u_R
+
\frac{u_L-u_R}
{1+\exp\left[
\frac{(u_L-u_R)(x-st)}{2\nu}
\right]}
\]

Shock speed:

\[
s =
\frac{u_L+u_R}{2}
\]

Shock thickness scaling:

\[
\delta
\sim
\frac{2\nu}{u_L-u_R}
\]

or by convention:

\[
\delta
\sim
\frac{4\nu}{\Delta u}
\]

### Relevance

This is the clean bridge between ideal discontinuous shock and physically smeared shock.

---

## 4.3 Forced Burgers / Acoustic Burgers

For nonlinear acoustics in lossy media, a Burgers-like equation often appears in retarded time form:

\[
\frac{\partial p}{\partial x}
=
\frac{\beta}{\rho c^3}
p\frac{\partial p}{\partial \tau}
+
\frac{\delta}{2c^3}
\frac{\partial^2 p}{\partial \tau^2}
\]

where:

| Symbol | Meaning |
|---|---|
| \(p\) | acoustic pressure |
| \(x\) | propagation distance |
| \(\tau = t-x/c\) | retarded time |
| \(\beta\) | nonlinearity parameter |
| \(\delta\) | sound diffusivity / attenuation coefficient |
| \(c\) | sound speed |

### Relevance

Better than plain Burgers when modeling finite-amplitude acoustic shock propagation in water.

---

## 4.4 Burgers–Gilmore Bridge

Gilmore models the bubble/source.

Burgers models shock propagation after emission.

\[
\text{Bubble collapse}
\rightarrow
p(r_0,t)
\rightarrow
\text{Burgers propagation}
\rightarrow
p(r,t)
\]

Boundary condition:

\[
p(r_0,t)
=
p_{\text{Gilmore}}(t)
\]

Propagation:

\[
\partial_x p
=
\frac{\beta}{\rho c^3}p\partial_\tau p
+
\frac{\delta}{2c^3}\partial_{\tau\tau}p
\]

### Interpretation

- Gilmore alone may overstate material damage if propagation losses are omitted.
- Burgers alone does not generate the bubble collapse source.
- The bridge is valid only while the pulse can be approximated as a weak/finite-amplitude acoustic shock rather than full multiphase compressible flow.

---

# 5. Stress-Test Regimes

## 5.1 Mach stress

Bubble wall Mach number:

\[
M_R = \frac{|\dot R|}{c}
\]

Regimes:

| \(M_R\) | Regime | Preferred model |
|---:|---|---|
| \(M_R \ll 1\) | incompressible / weak acoustic | Rayleigh–Plesset |
| \(M_R < 1\) but finite | weak compressibility | Keller–Miksis |
| \(M_R \sim 1\) | strong collapse | Gilmore + Tait |
| \(M_R > 1\) | shock-dominant | compressible CFD / Gilmore with caution |
| very high \(M_R\) | ionization/plasma possible | EOS + radiation/MHD/chemistry needed |

## 5.2 Nano-scale stress

Bubble Reynolds number:

\[
Re_R =
\frac{\rho R |\dot R|}{\mu}
\]

When \(R\) becomes very small, viscous effects dominate.

Viscous damping scale:

\[
D_\nu \sim \nu \partial_{xx}u
\]

Nonlinear steepening scale:

\[
N \sim u\partial_x u
\]

Ratio:

\[
\chi =
\frac{N}{D_\nu}
\sim
\frac{uL}{\nu}
=
Re
\]

If:

\[
\chi \ll 1
\]

then shock formation is suppressed.

## 5.3 High-density / high-impedance stress

Acoustic impedance:

\[
Z = \rho c
\]

Shock transmission/reflection at an interface:

\[
\mathcal{R}
=
\frac{Z_2-Z_1}{Z_2+Z_1}
\]

\[
\mathcal{T}
=
\frac{2Z_2}{Z_2+Z_1}
\]

High-\(Z\) fluids/materials change shock focusing, reflection, and local damage.

## 5.4 Plasma / chemistry failure mode

Adiabatic gas-temperature estimate:

\[
T_{\max}
=
T_0
\left(
\frac{R_{\max}}{R_{\min}}
\right)^{3(\gamma-1)}
\]

If temperature and density reach ionization/chemistry thresholds, hydrodynamic-only models fail.

Required extensions:

- reactive flow,
- plasma equation of state,
- radiative transfer,
- MHD if electromagnetic effects are non-negligible.

---

# 6. Pistol Shrimp Models

## 6.1 Biological mechanism

\[
\text{claw closure}
\rightarrow
\text{high-speed jet}
\rightarrow
\text{vortex core depressurization}
\rightarrow
\text{cavitation ring}
\rightarrow
\text{collapse shock}
\]

## 6.2 Vortex / jet model

Jet Reynolds number:

\[
Re_j =
\frac{\rho U_j D}{\mu}
\]

Cavitation number:

\[
Ca =
\frac{P_\infty - P_v}{\frac{1}{2}\rho U_j^2}
\]

Cavitation likely when:

\[
Ca < Ca_{\text{crit}}
\]

## 6.3 Vortex pressure drop

Approximate vortex-core pressure drop:

\[
\Delta P_{\text{vortex}}
\sim
\frac{1}{2}\rho v_\theta^2
\]

Cavitation condition:

\[
P_\infty - \Delta P_{\text{vortex}} < P_v
\]

## 6.4 Action value

\[
V_{\text{snap}}
=
D_{\text{target}}
+
I_{\text{contest}}
+
I_{\text{communication}}
-
E_{\text{snap}}
-
C_{\text{wear}}
\]

---

# 7. Mantis Shrimp Models

## 7.1 Spring-latch mechanics

\[
E_{\text{spring}}
=
\frac{1}{2}kx^2
\]

\[
P_{\text{release}}
=
\frac{E_{\text{spring}}}{\Delta t}
\]

\[
E_{\text{club}}
=
\frac{1}{2}m_{\text{club}}v_{\text{club}}^2
\]

## 7.2 Impact impulse

\[
J_{\text{impact}}
=
\int F_{\text{impact}}(t)\,dt
\]

## 7.3 Dual hit

\[
D_{\text{total}}
=
D_{\text{impact}}
+
D_{\text{cavitation}}
\]

\[
D_{\text{cavitation}}
\propto
\int P_{\text{collapse}}(t)A_{\text{target}}\,dt
\]

## 7.4 Cavitation inception around strike

A simple threshold:

\[
P_{\text{local}} < P_v
\]

or using cavitation number:

\[
Ca = \frac{P_\infty-P_v}{\frac12\rho U^2}
\]

Cavitation appears when \(Ca\) crosses a mechanism-specific threshold.

---

# 8. Suction Feeding Models

## 8.1 Buccal pressure drop

\[
\Delta P_{\text{buccal}}
=
P_{\text{ambient}} - P_{\text{mouth}}
\]

## 8.2 Flow field

Incompressible continuity:

\[
\nabla\cdot\mathbf{u}=0
\]

Navier–Stokes:

\[
\rho
\left(
\partial_t\mathbf{u}
+
\mathbf{u}\cdot\nabla\mathbf{u}
\right)
=
-\nabla P
+
\mu\nabla^2\mathbf{u}
\]

## 8.3 Force on prey

Pressure-gradient force:

\[
F_{\Delta P}
=
- V_{\text{prey}}\nabla P
\]

Drag:

\[
F_D
=
\frac{1}{2}\rho C_D A
\|\mathbf{u}-\mathbf{v}_{\text{prey}}\|^2
\]

Acceleration reaction:

\[
F_A
=
C_A\rho V_{\text{prey}}
\frac{D\mathbf{u}}{Dt}
\]

Total:

\[
F_{\text{prey}}
=
F_{\Delta P}
+
F_D
+
F_A
\]

## 8.4 Suction-Induced Force Field

\[
\mathbf{F}_{SIFF}(x,t)
=
\mathbf{F}_{\Delta P}(x,t)
+
\mathbf{F}_D(x,t)
+
\mathbf{F}_A(x,t)
\]

Capture condition:

\[
\int_{t_0}^{t_1}
\mathbf{F}_{SIFF}\,dt
>
J_{\text{escape}}
\]

---

# 9. Larval Fish Reynolds-Limited Suction

## 9.1 Reynolds number

\[
Re =
\frac{\rho U L}{\mu}
\]

## 9.2 Flow reversal

\[
Q_{\text{net}}
=
Q_{\text{in}}
-
Q_{\text{out}}
\]

Failure if prey is not transported far enough before efflux:

\[
x_{\text{prey}}(t_{\text{closure}}) < x_{\text{safe}}
\Rightarrow
\text{failed capture}
\]

## 9.3 Energetic limit

\[
E_{\text{suction}}
=
\int \Delta P\,dV
\]

\[
P_{\text{capture}}
=
\Pr(E_{\text{suction}} > E_{\text{escape/prey}})
\]

---

# 10. Bearded Seal Suction and Hydraulic Jetting

## 10.1 Suction mode

\[
\Delta P_{\text{suction}}
=
P_{\text{ambient}}
-
P_{\text{mouth}}
\]

## 10.2 Jetting mode

\[
\Delta P_{\text{jet}}
=
P_{\text{mouth}}
-
P_{\text{ambient}}
\]

## 10.3 Alternating work cycle

\[
W_{\text{cycle}}
=
\int_{\text{suction}}\Delta P_{\text{suction}}dV
+
\int_{\text{jet}}\Delta P_{\text{jet}}dV
\]

---

# 11. Jetting Animals

Includes squid, jellyfish, and dragonfly larvae.

## 11.1 Jet thrust

\[
T
=
\dot m v_{\text{jet}}
+
(P_e-P_a)A_e
\]

## 11.2 Volume flux

\[
Q = A_e v_{\text{jet}}
\]

\[
\dot m = \rho Q
\]

## 11.3 Jet work

\[
W_{\text{jet}}
=
\int \Delta P_{\text{cavity}}\,dV
\]

## 11.4 Circulation-pressure relation

A transient-pressure model can be summarized as:

\[
\Delta P_{\text{cavity}}
=
\mathcal{F}
\left(
\frac{d\Gamma}{dt},
\Gamma,
Q,
A_e,
\text{geometry}
\right)
\]

where \(\Gamma\) is circulation.

---

# 12. Suction-Based Swimming

## 12.1 Pressure-force integral

\[
\mathbf{F}_{P}
=
-\int_A P(\mathbf{x},t)\mathbf{n}\,dA
\]

Low-pressure suction component:

\[
\mathbf{F}_{\text{suction}}
=
\int_A
(P_{\text{ambient}}-P_{\text{local}})
\mathbf{n}\,dA
\]

## 12.2 Propulsive efficiency

\[
\eta
=
\frac{P_{\text{useful}}}{P_{\text{input}}}
\]

---

# 13. Bombardier Beetle Pulsed Spray

## 13.1 Chamber pressure dynamics

\[
\frac{dP_c}{dt}
=
\frac{RT}{V_c}\frac{dn_g}{dt}
-
\frac{P_c}{V_c}\frac{dV_c}{dt}
-
\Phi_{\text{out}}(P_c,P_a)
\]

## 13.2 Valve threshold

\[
P_c > P_{\text{valve}}
\Rightarrow
\text{pulse ejection}
\]

\[
P_c \downarrow
\Rightarrow
\text{valve close / reload}
\]

## 13.3 Pulse impulse

\[
J_{\text{spray}}
=
\sum_i
\int_{t_i}^{t_i+\Delta t_i}
\dot m(t)v_{\text{jet}}(t)\,dt
\]

---

# 14. Bladderwort Negative-Pressure Trap

## 14.1 Pressure differential

\[
\Delta P_{\text{trap}}
=
P_{\text{outside}}-P_{\text{inside}}
\]

Trigger:

\[
\Delta P_{\text{trap}} > \theta_{\text{door}}
\Rightarrow
\text{door opens}
\]

## 14.2 Orifice inflow

\[
Q(t)
=
C_d A_{\text{door}}
\sqrt{
\frac{2\Delta P_{\text{trap}}}{\rho}
}
\]

## 14.3 Trap work

\[
W_{\text{trap}}
=
\int \Delta P_{\text{trap}}dV
\]

---

# 15. Cnidarian Osmotic Projectiles

## 15.1 Osmotic pressure

\[
\Pi = iCRT
\]

## 15.2 Stored work

\[
W_{\text{osmotic}}
=
\int \Pi\,dV
\]

## 15.3 Projectile energy

\[
E_k =
\frac{1}{2}mv^2
\]

Launch threshold:

\[
W_{\text{osmotic}} > E_{\text{threshold}}
\]

---

# 16. Biological Hydraulic Force Transmission

## 16.1 Hydraulic force

\[
F = \Delta P A
\]

## 16.2 Hydraulic work

\[
W = \int P\,dV
\]

## 16.3 Hydrostatic incompressibility

\[
V \approx \text{constant}
\]

For a cylindrical body:

\[
V = AL
\]

\[
\frac{\Delta L}{L}
\approx
-\frac{\Delta A}{A}
\]

---

# 17. Lateral-Line / Hydrodynamic Vibration Models

## 17.1 Particle motion and pressure

For plane waves:

\[
p = \rho c u
\]

where \(u\) is particle velocity.

Particle acceleration:

\[
a = \frac{\partial u}{\partial t}
\]

## 17.2 Dipole source near-field

A vibrating sphere or dipole produces a velocity potential field often approximated as:

\[
\phi(\mathbf{x},t)
\propto
\frac{\mathbf{d}(t)\cdot\mathbf{r}}{r^3}
\]

Velocity:

\[
\mathbf{u} = \nabla\phi
\]

Pressure:

\[
p = -\rho\frac{\partial \phi}{\partial t}
\]

## 17.3 Neuromast response

Simplified hair-cell deflection:

\[
m\ddot y + b\dot y + ky = F_{\text{flow}}(t)
\]

Flow force can be approximated as drag:

\[
F_{\text{flow}}
=
\frac{1}{2}\rho C_D A u^2
\]

or linearized at low Reynolds number:

\[
F_{\text{flow}} \propto \mu L u
\]

## 17.4 Canal neuromast pressure-gradient sensing

Canal neuromasts approximate pressure-difference sensors:

\[
\Delta P = P(x+\Delta x)-P(x)
\]

\[
\Delta P \approx \nabla P \cdot \Delta x
\]

## 17.5 Artificial lateral-line localization

Given sensor vector:

\[
\mathbf{s}(t)
=
[s_1(t),s_2(t),...,s_N(t)]
\]

estimate source:

\[
\hat{\Omega}
=
\arg\max_{\Omega}
P(\Omega|\mathbf{s})
\]

or neural approximation:

\[
\hat{\Omega}
=
f_\theta(\mathbf{s})
\]

---

# 18. Vibroacoustic / Percussion Models

## 18.1 Transfer function

\[
H(f)
=
\frac{Y(f)}{F_{\text{input}}(f)}
\]

## 18.2 Cavity anomaly

\[
\Delta H(f)
=
H_{\text{candidate}}(f)
-
H_{\text{solid}}(f)
\]

Residual score:

\[
R_{\text{interface}}
=
\int_{f_1}^{f_2}
|\Delta H(f)|^2\,df
\]

## 18.3 Modal model

\[
M\ddot{\mathbf{x}}
+
C\dot{\mathbf{x}}
+
K\mathbf{x}
=
\mathbf{F}(t)
\]

Natural frequencies:

\[
\det(K-\omega^2M)=0
\]

## 18.4 Feature vector for percussion detection

\[
z =
[
\text{MFCC},
\text{wavelet energy},
\text{spectral centroid},
\text{modal peaks},
\text{decay constant}
]
\]

Classifier:

\[
\hat c
=
\arg\max_c P(c|z)
\]

---

# 19. Dimensionless Classifiers

## 19.1 Reynolds number

\[
Re = \frac{\rho U L}{\mu}
\]

Inertia vs viscosity.

## 19.2 Weber number

\[
We = \frac{\rho U^2 L}{\sigma}
\]

Inertia vs surface tension.

## 19.3 Cavitation number

\[
Ca = \frac{P_\infty-P_v}{\frac12\rho U^2}
\]

Cavitation tendency.

## 19.4 Strouhal number

\[
St = \frac{fA}{U}
\]

Oscillation / swimming efficiency.

## 19.5 Mach number

\[
M = \frac{U}{c}
\]

Compressibility/shock relevance.

## 19.6 Womersley number

\[
Wo = L\sqrt{\frac{\omega\rho}{\mu}}
\]

Oscillatory flow inertia vs viscosity.

## 19.7 Acoustic impedance

\[
Z = \rho c
\]

Interface reflection/transmission.

---

# 20. Model Selection Matrix

| Problem | Minimum viable model | Better model | Failure upgrade |
|---|---|---|---|
| slow bubble growth | Rayleigh–Plesset | Keller–Miksis | CFD with phase change |
| strong bubble collapse | Keller–Miksis | Gilmore + Tait | compressible multiphase CFD |
| shock propagation | acoustic \(1/r\) decay | acoustic Burgers | full compressible Navier–Stokes |
| snapping shrimp | vortex + cavitation number | IB + HEM CFD | compressible CFD + bubble clouds |
| mantis shrimp | spring-latch + impact | impact + cavitation force | FSI + fracture + cavitation |
| suction fish | pressure drop | SIFF | 3D CFD predator/prey |
| larval suction | Reynolds scaling | viscous CFD | deformable prey + escape model |
| bearded seal jetting | \(\int\Delta P dV\) | measured pressure cycle | full oral-cavity CFD |
| jellyfish/squid jetting | momentum thrust | transient pressure/circulation | FSI CFD |
| lateral line | dipole near-field | neuromast transfer model | CFD + neural encoding |
| timber/aye-aye percussion | transfer function | FEM vibroacoustic model | anisotropic FSI + classifier |

---

# 21. Claim Ladder

## REVIEWED / strongly grounded model families

- Rayleigh–Plesset cavitation.
- Keller–Miksis weak compressibility.
- Gilmore/Tait high-amplitude compressible collapse.
- Burgers nonlinear shock smoothing.
- Navier–Stokes / mixture CFD for cavitating flows.
- SIFF / pressure-gradient suction feeding.
- Jet thrust equation.
- Hydraulic force \(F=\Delta PA\).
- Osmotic pressure \(\Pi=iCRT\).
- Lateral-line dipole / pressure-gradient sensing.

## CALIBRATED ENGINEERING DELTA candidates

- ACW as an idealized test medium.
- Gilmore + Burgers bridge for cavitation shock propagation.
- Cavitation shock decay exponent \(\alpha>1\) fitted to real-water data.
- Nano-scale shock suppression by viscous dominance.
- Heavy-fluid/high-impedance stress-test map.

## BEAUTIFUL PROVISIONAL / needs receipts

- Exact Mach cutoff where Gilmore/Burgers bridge fails.
- Universal shock-front thickness estimates.
- Universal energy percentage radiated as shock.
- Mercury/very-high-density extrapolations without EOS data.
- Plasma/MHD threshold values without thermochemical model.

---

# 22. Next File Tasks

1. Add formal citations with DOI where available.
2. Split into:
   - `CavitationModels.md`
   - `PressureGradientSpecies.md`
   - `VibrationMechanosensing.md`
   - `BurgersShockBridge.md`
3. Add Lean structures:
   - `CavitationModel`
   - `PressureDifferentialAxis`
   - `HydrodynamicVibrationAxis`
   - `ShockPropagationBridge`
4. Add simulation scripts:
   - Rayleigh–Plesset ODE toy solver.
   - Viscous Burgers shock profile generator.
   - Cavitation-number threshold table.
   - SIFF force-field toy model.
5. Add evidence receipts:
   - source paper,
   - equation family,
   - variables,
   - domain of validity,
   - known failure mode.

---

# 23. Compact Unified Thesis

\[
\boxed{
\text{Biological pressure systems convert gradients into work, damage, sensing, or escape.}
}
\]

\[
\boxed{
\text{Cavitation systems convert local pressure collapse into bubble energy and shock.}
}
\]

\[
\boxed{
\text{Vibration systems convert mechanical waves into world-state information.}
}
\]

\[
\boxed{
\text{Burgers-type models bridge ideal shock formation and real dissipative smoothing.}
}
\]

The lawful path is not metaphorical. Each imported biological axis must enter through a documented equation family, explicit variables, and a stated failure regime.
