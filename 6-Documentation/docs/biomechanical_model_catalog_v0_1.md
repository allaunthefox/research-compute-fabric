# Biomechanical Model Catalog: Pressure, Cavitation, Vibration, Suction, Jetting, and Acoustic Residuals

**Working purpose.** This file collects peer-reviewed mathematical model families that can plug into the BioMechanicalResidualAxes / Flat Burgers Adapter Stack. It is intentionally equation-first: a species or biological mechanism is admitted only when it can be attached to a documented governing model, measurable variable set, or computational formulation.

**Status.** Draft v0.1, generated for review. This is not exhaustive; it is a curated starter file biased toward models with clear equations and adapter value.

---

## 0. Adapter spine

For every biological mechanism below, define a domain signal:

\[
X_S(t,x)=\text{measured or modeled biological/mechanical field}
\]

Flatten into a dimensionless field:

\[
U(\xi,\tau)=\frac{X_S(x,t)-X_0}{X_s},\qquad \xi=\frac{x}{L},\qquad \tau=\frac{t}{T}
\]

Then test residual lawfulness using the flat, domain-neutral core:

\[
R(U;\epsilon)=\partial_\tau U+U\partial_\xi U-\epsilon\partial_{\xi\xi}U
\]

The species-specific adapter carries the biology. The residual carries no biology.

General value functional:

\[
V_S=W_{\text{useful}}+I(\Omega;Y)-E_{\text{actuation}}-C_{\text{noise}}-C_{\text{failure}}-C_{\text{self-damage}}
\]

where \(\Omega\) is hidden world-state, \(Y\) is the received signal, and \(W_{\text{useful}}\) is useful work produced by the pressure/vibration/acoustic mechanism.

---

# 1. Cavitation bubble dynamics

## 1.1 Rayleigh-Plesset-type cavitation model

**Relevant biological systems.**
- Snapping/pistol shrimp, especially *Alpheus heterochaelis*.
- Mantis shrimp secondary cavitation damage.
- Biomedical/biological microcavitation systems.
- Bio-inspired cavitation generators.

**Core model.**

\[
\rho\left(R\ddot R+\frac{3}{2}\dot R^2\right)
=
P_B(R,t)-P_\infty(t)-\frac{2\sigma}{R}-\frac{4\mu\dot R}{R}
\]

where:

| Symbol | Meaning |
|---|---|
| \(R(t)\) | bubble radius |
| \(\dot R,\ddot R\) | bubble wall velocity and acceleration |
| \(\rho\) | liquid density |
| \(P_B\) | bubble interior pressure |
| \(P_\infty\) | far-field liquid pressure |
| \(\sigma\) | surface tension |
| \(\mu\) | dynamic viscosity |

**Cavitation condition.**

\[
P_{\text{local}}<P_{\text{vapour}}
\Rightarrow
\text{bubble nucleation/growth}
\]

**Collapse pulse proxy.**

\[
P_{\text{pulse}}(t)\propto \rho\left(R\ddot R+2\dot R^2\right)
\]

**Biological action explanation.**

\[
\text{fast appendage/jet}\rightarrow P_{\text{local}}\downarrow \rightarrow R(t)\uparrow \rightarrow R(t)\downarrow \rightarrow P_{\text{collapse}}\uparrow
\]

**Key paper notes.**
- Versluis et al. used a Rayleigh-Plesset-type model to account for snapping shrimp bubble radius time-dependence and emitted sound.
- Abu-Nab et al. review Rayleigh-Plesset, Church, diffusion-concentration, and Keller-Miksis microcavitation models in biological systems.
- Hong et al. derive nondimensional Rayleigh-Plesset forms and analyze energy-flow/stability criteria.

**Adapter.**

\[
\alpha_{\text{cav}}(X)=\frac{P_{\text{collapse}}(t)-P_0}{P_s}
\]

**Value.**

\[
V_{\text{cav}}=D_{\text{target}}+I_{\text{signal}}-E_{\text{snap/strike}}-C_{\text{self-damage}}
\]

---

## 1.2 Homogeneous mixture / homogeneous equilibrium cavitating CFD

**Relevant biological systems.**
- Snapping shrimp claw closure.
- Bio-inspired snapping-claw/plunger cavitation devices.
- Cavitating hydrofoils and engineered analogs useful for parameter transfer.

**Core equations.**

Mixture continuity:

\[
\frac{\partial \rho_m}{\partial t}+\nabla\cdot(\rho_m\mathbf{u})=0
\]

Mixture momentum:

\[
\frac{\partial(\rho_m\mathbf{u})}{\partial t}
+\nabla\cdot(\rho_m\mathbf{u}\mathbf{u})
=
-\nabla p+\nabla\cdot\boldsymbol{\tau}+\mathbf{f}_{IB}
\]

where \(\mathbf{f}_{IB}\) is an immersed-boundary forcing term for moving biological/biomimetic structures.

Vapor fraction transport, generic form:

\[
\frac{\partial \alpha_v}{\partial t}
+
\nabla\cdot(\alpha_v\mathbf{u})
=
\dot m_{\text{vap}}-\dot m_{\text{cond}}
\]

Rayleigh-Plesset-based mass transfer closes the vaporization/condensation source terms.

**Biological action explanation.**

\[
\text{claw closure}\rightarrow \text{high-speed jet}\rightarrow \text{vortex roll-up}\rightarrow \text{vortex-core pressure depression}\rightarrow \text{cavitation ring}\rightarrow \text{collapse pulse}
\]

**Key paper notes.**
- Koukouvinis et al. used immersed boundary + homogeneous equilibrium modeling for snapping shrimp cavitation.
- Cianferra and Armenio formulate Rayleigh-Plesset-based Eulerian mixture models for cavitating flows.
- Pardo Vigil et al. propose Rayleigh-Plesset-based homogeneous cavitation with microbubble and turbulence interactions.
- Salinas-Vázquez et al. used EDAC and immersed boundaries for bio-inspired snapping claw flows.
- Godínez et al. report bio-inspired snapping plunger experiments/simulations with Rayleigh-Plesset description.

**Adapter.**

\[
\alpha_{\text{mix-cav}}(X)=
\frac{\alpha_v(t,x)-\alpha_{v,0}}{\alpha_{v,s}}
+
\lambda\frac{p(t,x)-p_0}{p_s}
\]

---

## 1.3 Snapping shrimp vortex/jet efficiency model

**Relevant biological system.**
- Snapping shrimp / pistol shrimp.

**Model pieces.**
Hess et al. report that snapping shrimp claw models form a vortex ring with dimensionless formation number approximately:

\[
\Delta T^\* \approx 4
\]

This suggests efficient vortex formation, often associated with maximum vortex strength for minimum ejected fluid volume.

Generic formation number:

\[
T^\*=\frac{U t}{D}
\]

where \(U\) is jet velocity, \(t\) is formation time, and \(D\) is orifice/nozzle scale.

Jet momentum:

\[
J_{\text{jet}}=\int \rho Q(t)u_{\text{jet}}(t)\,dt
\]

**Biological action explanation.**

\[
\text{claw geometry}\rightarrow \text{nozzle-like contour}\rightarrow \text{vortex ring}\rightarrow \text{cavitating re-entrant jet}\rightarrow \text{extended penetration/damage range}
\]

---

# 2. Impact + cavitation weapons

## 2.1 Mantis shrimp spring-latch + cavitation model

**Relevant biological systems.**
- Peacock mantis shrimp, *Odontodactylus scyllarus*.
- Other stomatopods with raptorial appendages.
- Bio-inspired striking robots.

**Core elastic energy model.**

\[
E_{\text{spring}}=\frac{1}{2}kx^2
\]

Power amplification:

\[
P_{\text{release}}=\frac{E_{\text{spring}}}{\Delta t_{\text{release}}}
\]

Club kinetic energy:

\[
E_{\text{club}}=\frac{1}{2}m_{\text{club}}v_{\text{club}}^2
\]

Impact impulse:

\[
J_{\text{impact}}=\int F_{\text{impact}}(t)\,dt
\]

Total damage:

\[
D_{\text{total}}=D_{\text{impact}}+D_{\text{cavitation}}
\]

where:

\[
D_{\text{cavitation}}\propto \int P_{\text{collapse}}(t)A_{\text{target}}\,dt
\]

**Observed/derived action explanation.**

\[
E_{\text{muscle}}\rightarrow E_{\text{spring}}\rightarrow E_{\text{club}}\rightarrow F_{\text{impact}}+P_{\text{bubble collapse}}
\]

**Key paper notes.**
- Patek et al. showed saddle-shaped exoskeletal spring mechanics and vapor bubble formation/collapse.
- Patek and Caldwell measured peak limb impact forces and cavitation-force peaks; cavitation forces can be large relative to direct impact.
- Cox et al. built Ninjabot and found cavitation inception in rotating/accelerating biological conditions was best explained by maximum linear velocity.
- Ito et al. model and experimentally control mantis-shrimp-inspired cavitation.

**Adapter.**

\[
\alpha_{\text{impact-cav}}(X)=
w_i\frac{F_{\text{impact}}-F_0}{F_s}
+
w_c\frac{P_{\text{collapse}}-P_0}{P_s}
\]

---

# 3. Suction feeding and pressure-gradient prey capture

## 3.1 Quantitative hydrodynamical suction model

**Relevant biological systems.**
- Teleost fishes.
- Bluegill sunfish.
- Largemouth bass.
- Catfishes.
- Centrarchids.

**Core flow model.**
Muller, Osse, and Verhagen model suction feeding as an expanding/compressing rotationally symmetric profile with prescribed movement and posterior valve boundary conditions. The key formal move is unsteady flow, not steady suction.

Generic incompressible flow:

\[
\nabla\cdot\mathbf{u}=0
\]

Unsteady Navier-Stokes:

\[
\rho\left(\frac{\partial \mathbf{u}}{\partial t}+\mathbf{u}\cdot\nabla\mathbf{u}\right)
=
-\nabla P+\mu\nabla^2\mathbf{u}
\]

Buccal pressure differential:

\[
\Delta P_{\text{buccal}}=P_{\text{ambient}}-P_{\text{mouth}}
\]

Flow rate through gape:

\[
Q(t)=\int_{A_{\text{mouth}}}\mathbf{u}\cdot\mathbf{n}\,dA
\]

**Biological action explanation.**

\[
\text{cranial expansion}\rightarrow \Delta P_{\text{mouth}}\rightarrow Q(t)\rightarrow \text{prey transport}
\]

---

## 3.2 Pressure-gradient force on prey

**Relevant biological systems.**
- Aquatic suction-feeding vertebrates.

**Core model.**

Pressure-gradient force:

\[
F_{\Delta P}=-V_{\text{prey}}\nabla P
\]

Drag:

\[
F_D=\frac{1}{2}\rho C_D A\|\mathbf{u}-\mathbf{v}_{\text{prey}}\|^2
\]

Acceleration reaction:

\[
F_A=C_A\rho V_{\text{prey}}\frac{D\mathbf{u}}{Dt}
\]

Total force:

\[
F_{\text{prey}}=F_{\Delta P}+F_D+F_A
\]

Wainwright and Day’s key result: pressure-gradient force can dominate drag and acceleration reaction.

**Capture criterion.**

\[
\int_{t_0}^{t_1}F_{\text{prey}}(t)\,dt
>
J_{\text{escape}}
\Rightarrow
\text{capture}
\]

---

## 3.3 Suction-induced force-field model (SIFF)

**Relevant biological systems.**
- Centrarchid fishes.
- Comparative suction-feeding performance.

**Core model.**

\[
\mathbf{F}_{\text{SIFF}}(x,t)
=
\mathbf{F}_{\Delta P}(x,t)
+
\mathbf{F}_{D}(x,t)
+
\mathbf{F}_{A}(x,t)
\]

Performance over prey type \(k\):

\[
\Pi_k(\theta)=
\max_t \|\mathbf{F}_{\text{SIFF}}(x_k,t;\theta)\|
\]

where \(\theta\) is a vector of morphology/kinematic traits.

Fitness/performance landscape:

\[
\theta^\*_k=\arg\max_\theta \Pi_k(\theta)
\]

**Biological action explanation.**
Different prey types impose different optimal hydrodynamic trait combinations.

---

## 3.4 Larval fish suction: viscous/intermediate-Reynolds constraints

**Relevant biological systems.**
- Larval fishes.

**Core Reynolds number.**

\[
Re=\frac{\rho U L}{\mu}
\]

At small scale, viscous/frictional loss becomes significant.

Energy partition:

\[
E_{\text{input}}=E_{\text{kinetic}}+E_{\text{viscous loss}}
\]

Flow reversal condition:

\[
Q_{\text{net}}=Q_{\text{in}}-Q_{\text{out}}
\]

Failure condition:

\[
Q_{\text{out}}>0 \quad \text{before prey reaches safe transport depth}
\]

or:

\[
x_{\text{prey}}(t_{\text{closure}})<x_{\text{safe}}
\Rightarrow \text{in-and-out failure}
\]

**Key paper notes.**
- Drost et al. calculate friction, power, energy, and prey escape paths for larval suction.
- Yaniv et al. model life-stage scaling of suction flow.
- Krishnan et al. model flow reversal causing prey ejection during early ontogeny.

---

# 4. Marine mammal suction and hydraulic jetting

## 4.1 Bearded seal suction/jetting pressure-cycle model

**Relevant biological system.**
- Bearded seal, *Erignathus barbatus*.

**Measured pressure modes.**

Suction:

\[
\Delta P_{\text{suction}}=P_{\text{ambient}}-P_{\text{mouth}}
\]

Hydraulic jetting:

\[
\Delta P_{\text{jet}}=P_{\text{mouth}}-P_{\text{ambient}}
\]

Cycle work:

\[
W_{\text{cycle}}=
\int_{\text{suction}}\Delta P_{\text{suction}}\,dV
+
\int_{\text{jet}}\Delta P_{\text{jet}}\,dV
\]

**Key paper note.**
Marshall et al. measured bearded seal suction and hydraulic jetting, including large subambient and suprambient pressure values during feeding trials.

**Biological action explanation.**

\[
\Delta P<0\Rightarrow \text{intake/capture};\qquad
\Delta P>0\Rightarrow \text{excavating jet}
\]

---

# 5. Jet propulsion and transient internal pressure

## 5.1 Jetting animals transient pressure model

**Relevant biological systems.**
- Squid.
- Jellyfish.
- Dragonfly larvae.

**Core thrust model.**

\[
T=\dot m v_{\text{jet}}+(P_{\text{exit}}-P_{\text{ambient}})A_{\text{exit}}
\]

Cavity work:

\[
W_{\text{jet}}=\int \Delta P_{\text{cavity}}\,dV
\]

Pressure-circulation model family:

\[
\Delta P_{\text{cavity}}
=
\mathcal{F}\left(
\frac{d\Gamma}{dt},
\Gamma,
Q,
A_{\text{nozzle}},
\text{geometry}
\right)
\]

where \(\Gamma\) is circulation, \(Q\) is volume flux, and \(A_{\text{nozzle}}\) is exit/nozzle area.

**Key paper note.**
Krieg and Mohseni use a circulation-based pressure model to predict internal pressure dynamics and swimming forces in jetting animals.

**Biological action explanation.**

\[
\text{cavity deformation}\rightarrow \Delta P_{\text{internal}}\rightarrow Q_{\text{jet}}\rightarrow T
\]

---

# 6. Suction-based swimming and pressure-field propulsion

## 6.1 Pressure reconstruction from PIV

**Relevant biological systems.**
- Jellyfish.
- Lampreys.
- Flexible swimmers and flyers more broadly.

**Core pressure-force equation.**

\[
\mathbf{F}_{\text{pressure}}=-\int_A P(\mathbf{x},t)\mathbf{n}\,dA
\]

Suction contribution:

\[
\mathbf{F}_{\text{suction}}=
\int_A\left(P_{\text{ambient}}-P_{\text{local}}\right)\mathbf{n}\,dA
\]

Propulsive efficiency:

\[
\eta_{\text{prop}}=
\frac{\text{useful locomotor power}}{\text{mechanical/metabolic input power}}
\]

**Key paper note.**
Gemmell et al. show that efficient swimmers such as lampreys and jellyfish can primarily pull via low-pressure regions. Costello et al. generalize suction forces around flexible bending propulsors.

---

# 7. Pulsed chemical pressure jets

## 7.1 Bombardier beetle cyclic pressure chamber model

**Relevant biological systems.**
- Bombardier beetles, especially Brachinini.

**Core reaction-chamber pressure dynamics.**

\[
\frac{dP_c}{dt}
=
\frac{RT}{V_c}\frac{dn_g}{dt}
-
\frac{P_c}{V_c}\frac{dV_c}{dt}
-
\Phi_{\text{out}}(P_c,P_a)
\]

Valve threshold:

\[
P_c>P_{\text{valve}}\Rightarrow \text{spray pulse}
\]

Pulsed jet impulse:

\[
J_{\text{spray}}=
\sum_i
\int_{t_i}^{t_i+\Delta t_i}
\dot m(t)v_{\text{jet}}(t)\,dt
\]

**Pulse frequency observation.**

\[
f_{\text{pulse}}\approx 500\ \text{Hz}
\]

for *Stenaptinus insignis* in Dean et al.

**Key paper notes.**
- James et al. develop a mathematical model for cyclic bombardier beetle discharge.
- Dean et al. characterize the defensive spray as a biological pulse jet.
- Arndt et al. image explosion-induced pulsation and model passive valve mediation.
- Beheshti and McIntosh simulate two-phase flow ejection and pressure-relief-valve pulsed spray.

**Biological action explanation.**

\[
\text{reaction}\rightarrow P_c\uparrow\rightarrow \text{valve opens}\rightarrow \text{hot pulsed spray}\rightarrow \text{predator deterrence}
\]

---

# 8. Negative-pressure traps and small-scale suction

## 8.1 Bladderwort elastic suction trap

**Relevant biological system.**
- Carnivorous bladderworts, *Utricularia*.

**Core trap pressure differential.**

\[
\Delta P_{\text{trap}}=P_{\text{outside}}-P_{\text{inside}}
\]

Door opening condition:

\[
\Delta P_{\text{trap}}>\theta_{\text{door}}\Rightarrow \text{door opens}
\]

Inflow approximation:

\[
Q(t)=C_d A_{\text{door}}\sqrt{\frac{2\Delta P_{\text{trap}}}{\rho}}
\]

Capture work:

\[
W_{\text{trap}}=\int \Delta P_{\text{trap}}\,dV
\]

**Key paper note.**
Deban et al. compare small suction feeders and bladderworts, emphasizing high-power elastic recoil and size constraints.

---

# 9. Osmotic projectile systems

## 9.1 Cnidarian nematocyst / biological shooting mechanisms

**Relevant biological systems.**
- Cnidarians.
- Other osmotic shooting systems.

**Osmotic pressure.**

\[
\Pi=iCRT
\]

Stored pressure work:

\[
W_{\text{osmotic}}=\int \Pi\,dV
\]

Projectile kinetic energy:

\[
E_{\text{projectile}}=\frac{1}{2}mv^2
\]

Launch condition:

\[
W_{\text{osmotic}}>E_{\text{threshold}}\Rightarrow \text{discharge}
\]

**Key paper note.**
Sakes et al. systematically review shooting mechanisms across fungi, plants, and animals, identifying osmosis-powered systems as extremely high acceleration / high power at small scales.

---

# 10. Hydraulic force transmission

## 10.1 Biological hydraulic systems

**Relevant biological systems.**
- Spiders.
- Echinoderms.
- Annelids.
- Nematodes.
- Soft-bodied and hydrostatic-skeleton animals.

**Core hydraulic force.**

\[
F=\Delta P A
\]

Hydraulic work:

\[
W=\int P\,dV
\]

Incompressible volume constraint:

\[
V\approx \text{constant}
\]

For simple cylinder-like hydrostats:

\[
AL=\text{constant}
\]

so:

\[
\frac{\Delta L}{L}\approx-\frac{\Delta A}{A}
\]

**Key paper notes.**
- Chapman reviews animal hydraulic systems, open/closed/external fluid compartments, muscular antagonism, jet propulsion, and suction.
- Liu et al. define biological fluid power systems using power source, cavity, and working medium.

---

# 11. Underwater vibration, particle motion, and lateral-line mechanosensing

## 11.1 Particle motion / underwater acoustic ecology model

**Relevant biological systems.**
- Fishes.
- Aquatic invertebrates.
- Crustaceans.
- Zooplankton.
- Any organism whose primary acoustic stimulus is particle motion rather than pressure.

**Sound field decomposition.**

\[
X_{\text{sound}}=(p,\mathbf{v},\mathbf{a})
\]

where \(p\) is sound pressure, \(\mathbf{v}\) is particle velocity, and \(\mathbf{a}\) is particle acceleration.

Linear acoustic relation for plane-wave idealization:

\[
p=\rho c u
\]

but near-field/shallow-water conditions often violate simple pressure-to-particle-motion inference.

**Particle acceleration.**

\[
\mathbf{a}=\frac{\partial \mathbf{v}}{\partial t}
\]

**Biological action explanation.**

\[
\text{source motion/noise}\rightarrow \mathbf{v},\mathbf{a},p\rightarrow \text{mechanosensory hair cells/statocysts/lateral line}\rightarrow \text{behavior}
\]

**Key paper note.**
Nedelec et al. identify particle motion as the missing link in underwater acoustic ecology and emphasize that fish and many invertebrates primarily sense particle motion.

---

## 11.2 Fish lateral-line hydrodynamic sensing

**Relevant biological systems.**
- All fishes with lateral line.
- Cavefish.
- Schooling fish.
- Predator/prey hydrodynamic sensing.
- Artificial lateral line robotics.

**Generic sensory field.**

\[
L(t,x)=\mathcal{N}\left(\mathbf{v}(t,x),\nabla \mathbf{v}(t,x),\partial_t\mathbf{v}(t,x)\right)
\]

Canal neuromasts often relate to pressure gradients; superficial neuromasts to flow velocity.

Pressure-gradient sensing:

\[
\Delta P_{ij}=P(x_i,t)-P(x_j,t)
\]

Velocity sensing:

\[
S_i(t)\propto \mathbf{v}(x_i,t)\cdot \mathbf{n}_i
\]

Hydrodynamic anomaly:

\[
\Delta L=L_{\text{observed}}-L_{\text{background}}
\]

Detection:

\[
\|\Delta L\|>\theta_L\Rightarrow \text{object/prey/wake/neighbor detected}
\]

**Dipole source localization model.**
A vibrating object can be approximated as a dipole source, with a pressure/velocity field sampled along the fish body. Goulet et al. provide theory and experiment for lateral-line object localization with body curvature, canal inter-pore spacing, boundary layer, and neuromast receptor behavior.

A simplified source-estimation objective:

\[
\hat{x}_{\text{source}}
=
\arg\min_x
\sum_i
\left[
S_i^{\text{observed}}-S_i^{\text{model}}(x)
\right]^2
\]

**Key paper notes.**
- Engelmann et al. show fish lateral lines detect minute hydrodynamic stimuli even in running water.
- Mogdans reviews sensory ecology and lateral-line adaptation to hydrodynamic conditions.
- Webb et al. discuss acoustic/hydrodynamic overlap and near-field complexities.
- Goulet et al. provide a biophysical hydrodynamic model for object localization.
- Artificial lateral line papers use pressure/velocity sensor arrays, beamforming, FFT, neural nets, and mode decomposition to reconstruct hydrodynamic fields.

---

# 12. Acoustic/vibroacoustic propagation in wood and solid substrates

## 12.1 Aye-aye / wood percussion transfer model

**Relevant biological systems.**
- Aye-aye, *Daubentonia madagascariensis*.
- Timber percussion NDE analogs.
- Wood-borne cavity detection.

**Transfer function.**

\[
H_{\text{wood}}(f)=\frac{Y(f)}{F_{\text{tap}}(f)}
\]

Hidden-interface anomaly:

\[
\Delta H(f)=H_{\text{candidate}}(f)-H_{\text{solid}}(f)
\]

Residual score:

\[
R_{\text{interface}}=\int_{f_1}^{f_2}|\Delta H(f)|^2\,df
\]

Excavation classifier:

\[
P(\text{excavate}\mid y)=
\sigma(w_A\Delta A+w_f\Delta f+w_\tau\Delta \tau+w_\phi\Delta\phi+w_mM-\theta)
\]

**Key paper notes.**
- Erickson’s aye-aye studies establish percussive foraging and subsurface interface/cavity stimulus logic.
- Nemati/Dehghan-Niri biomimetic studies model tap-scanning and auditory near-field sensitivity.
- Timber NDE papers use theoretical/numerical percussion models, DNN/ECAPA-TDNN classifiers, and finite-element/vibroacoustic analogs for hidden cavity detection.

---

# 13. Elastic shooting / catapult mechanisms

## 13.1 Latch-mediated spring actuation and biological shooting

**Relevant biological systems.**
- Mantis shrimp.
- Snapping shrimp.
- Cnidarians.
- Froghoppers and other elastic-powered fast movers.
- Plants/fungi with pressure/osmotic launch systems.

**Spring energy.**

\[
E=\frac{1}{2}kx^2
\]

Launch velocity:

\[
v=\sqrt{\frac{2E}{m}}
\]

Acceleration:

\[
a=\frac{F}{m}
\]

Mass-specific power:

\[
P_m=\frac{E}{m\Delta t}
\]

**Key paper note.**
Sakes et al. systematically compare shooting mechanisms and show scale-dependent acceleration/power patterns across fungi, plants, and animals. Patek’s mantis shrimp work gives animal spring-latch/cavitation coupling.

---

# 14. Dimensionless numbers for classification

These are cross-cutting model selectors.

## Reynolds number

\[
Re=\frac{\rho U L}{\mu}
\]

Inertial vs viscous dominance.

## Weber number

\[
We=\frac{\rho U^2 L}{\sigma}
\]

Inertial vs surface tension dominance; important for jets, droplets, bubble interfaces.

## Strouhal number

\[
St=\frac{fA}{U}
\]

Oscillatory locomotion, vortex shedding, propulsor timing.

## Cavitation number

\[
\sigma_c=\frac{P_\infty-P_v}{\frac{1}{2}\rho U^2}
\]

Cavitation likely when \(\sigma_c\) falls below a system-specific threshold.

## Womersley number

\[
\alpha=L\sqrt{\frac{\omega\rho}{\mu}}
\]

Unsteady oscillatory flow; relevant to pulsatile jets and biological pumping.

## Mach number

\[
Ma=\frac{U}{c}
\]

Compressibility and acoustic/shock relevance.

---

# 15. Integration table

| Model family | Governing signal | Species/actions | Core equations |
|---|---|---|---|
| Rayleigh-Plesset cavitation | bubble radius / collapse pressure | snapping shrimp, mantis shrimp, microcavitation | \(R\ddot R+\frac{3}{2}\dot R^2\) |
| Homogeneous cavitating CFD | mixture pressure/vapor fraction | snapping claw, hydrofoils, bioinspired plungers | Navier-Stokes + \(\alpha_v\) transport |
| Vortex/jet formation | jet velocity, vortex ring | snapping shrimp | \(T^\*=Ut/D\), jet momentum |
| Spring-latch impact | stored elastic energy | mantis shrimp, snapping shrimp | \(E=\frac12kx^2\) |
| Suction feeding | pressure gradient, flow velocity | fishes, seals, bladderworts | \(F=-V\nabla P+F_D+F_A\) |
| Larval suction scaling | Reynolds number, viscous loss | larval fishes | \(Re=\rho UL/\mu\), \(Q_{net}=Q_{in}-Q_{out}\) |
| Jet propulsion | cavity pressure, nozzle flux | squid, jellyfish, dragonfly larvae | \(T=\dot mv+(P_e-P_a)A_e\) |
| Suction swimming | low-pressure body field | jellyfish/lamprey | \(F=-\int_A Pn\,dA\) |
| Bombardier pulse jet | chamber pressure / valve cycles | bombardier beetle | \(dP_c/dt=\text{reaction}-\text{outflow}\) |
| Osmotic projectiles | osmotic pressure | cnidarians | \(\Pi=iCRT\) |
| Hydraulic actuation | internal pressure | spiders, hydrostats | \(F=\Delta PA\), \(AL=\text{const}\) |
| Particle motion acoustics | \((p,\mathbf v,\mathbf a)\) | fishes/invertebrates | \(p=\rho cu\) in plane-wave limit |
| Lateral line | pressure gradient / velocity | fishes/cavefish/schooling | \(\hat{x}=\arg\min\sum(S_i-S_i^{model})^2\) |
| Wood vibroacoustics | transfer function | aye-aye/timber NDE | \(H(f)=Y(f)/F(f)\) |

---

# 16. Candidate Lean types

```lean
namespace BioMechanicalModels

inductive Mechanism
  | cavitation
  | suction
  | jetting
  | pressureGradient
  | hydraulicActuation
  | osmoticProjectile
  | acousticVibration
  | lateralLine
  | elasticSpringLatch
  deriving Repr, DecidableEq

structure EquationFamily where
  name : String
  mechanism : Mechanism
  variables : List String
  dimensionless : Bool
  hasPeerReviewedUse : Bool
  hasSpeciesAdapter : Bool
  deriving Repr

structure SpeciesModel where
  speciesName : String
  commonName : String
  equationFamily : EquationFamily
  action : String
  valueFunctionDeclared : Bool
  failureModeDeclared : Bool
  deriving Repr

def Admissible (M : SpeciesModel) : Prop :=
  M.equationFamily.dimensionless = true ∧
  M.equationFamily.hasPeerReviewedUse = true ∧
  M.equationFamily.hasSpeciesAdapter = true ∧
  M.valueFunctionDeclared = true ∧
  M.failureModeDeclared = true

end BioMechanicalModels
```

---

# 17. Priority next imports

1. **Cavitation core.** Rayleigh-Plesset, Keller-Miksis, homogeneous mixture, cavitation number.
2. **Pressure-gradient prey capture.** SIFF, unsteady suction, larval Reynolds constraints.
3. **Hydrodynamic mechanosensing.** Lateral-line dipole localization, pressure-gradient/velocity sensor models.
4. **Vibroacoustic substrate detection.** Aye-aye + timber NDE transfer functions.
5. **Pulsed pressure jets.** Bombardier beetle chamber/valve models.
6. **Hydraulic actuation.** \(F=\Delta PA\), volume constraints, hydrostatic skeletons.
7. **Dimensionless classifier.** Use \(Re, We, St, \sigma_c, \alpha, Ma\) to route mechanism class.

---

# References

[1] [A review of microcavitation bubbles dynamics in biological systems and their mechanical applications](https://consensus.app/papers/details/32cd24fd9b3b5887b6bf1ce274a0763a/?utm_source=chatgpt) — A. K. Abu-Nab, A. Morad, E. S. Selima, Tetsuya Kanagawa, A. Abu-Bakr, 2025, *Ultrasonics Sonochemistry*, 0 citations.

[2] [How snapping shrimp snap: through cavitating bubbles](https://consensus.app/papers/details/a5289f80ad015bda9bcc7c257ed30875/?utm_source=chatgpt) — Michel Versluis, Barbara Schmitz, A. V. D. Heydt, Detlef Lohse, 2000, *Science*, 456 citations.

[3] [Energy flow investigations of Rayleigh-Plesset equation for cavitation simulations](https://consensus.app/papers/details/8b48d80d97e457028d17429bd8744e10/?utm_source=chatgpt) — Yi Hong, Miaomiao Li, Xiaodong He, Jing Tang Xing, 2024, *Ocean Engineering*, 5 citations.

[4] [Unveiling the physical mechanism behind pistol shrimp cavitation](https://consensus.app/papers/details/ab6a32e60764588285afe125e7422ed4/?utm_source=chatgpt) — P. Koukouvinis, C. Bruecker, M. Gavaises, 2017, *Scientific Reports*, 53 citations.

[5] [Rayleigh–Plesset-based Eulerian mixture model for cavitating flows](https://consensus.app/papers/details/9bc5e72611fd5e9abb82c6b8161b61e4/?utm_source=chatgpt) — M. Cianferra, V. Armenio, 2024, *Physics of Fluids*, 2 citations.

[6] [An improved, Rayleigh-Plesset based homogeneous cavitation model accounting for microbubble behaviour and turbulent interaction](https://consensus.app/papers/details/5effe805f9295f3697cc70ceadc9fe9c/?utm_source=chatgpt) — Álvaro Pardo Vigil, Laura Suárez Fernández, José González Pérez, A. Pandal, 2025, *International Journal of Multiphase Flow*, 1 citation.

[7] [Vortex Formation with a Snapping Shrimp Claw](https://consensus.app/papers/details/cfd051b0fcc65fe0b3483aaf970bbe4c/?utm_source=chatgpt) — D. Hess, C. Brücker, F. Hegner, Alexander Balmert, H. Bleckmann, 2013, *PLoS ONE*, 27 citations.

[8] [Biomechanics: Deadly strike mechanism of a mantis shrimp](https://consensus.app/papers/details/2ed3cf95d4265360aa5824349c29f9ca/?utm_source=chatgpt) — Sheila N. Patek, Wyatt L. Korff, Roy L. Caldwell, 2004, *Nature*, 340 citations.

[9] [Extreme impact and cavitation forces of a biological hammer: strike forces of the peacock mantis shrimp Odontodactylus scyllarus](https://consensus.app/papers/details/70b2cfb495bc505a82605c4c789a1904/?utm_source=chatgpt) — Sheila N. Patek, Roy L. Caldwell, 2005, *Journal of Experimental Biology*, 260 citations.

[10] [A physical model of the extreme mantis shrimp strike: kinematics and cavitation of Ninjabot](https://consensus.app/papers/details/27f597eab8bb5b2cb3544cb089bddfd7/?utm_source=chatgpt) — S. Cox, D. Schmidt, Y. Modarres-Sadeghi, S. Patek, 2014, *Bioinspiration & Biomimetics*, 45 citations.

[11] [A quantitative hydrodynamical model of suction feeding in fish](https://consensus.app/papers/details/a3231ef45ee35fa7b6675b726a50bbe2/?utm_source=chatgpt) — M. Muller, J. Osse, J. Verhagen, 1982, *Journal of Theoretical Biology*, 200 citations.

[12] [The forces exerted by aquatic suction feeders on their prey](https://consensus.app/papers/details/8a962a2f34bd55b8baeedaee011dc8dc/?utm_source=chatgpt) — P. Wainwright, S. Day, 2007, *Journal of The Royal Society Interface*, 81 citations.

[13] [An integrative modeling approach to elucidate suction-feeding performance](https://consensus.app/papers/details/3abd50c82cf454debc183ad4c3a37cf9/?utm_source=chatgpt) — R. Holzman, D. Collar, R. Mehta, P. Wainwright, 2012, *Journal of Experimental Biology*, 76 citations.

[14] [A quantitative hydrodynamical model of suction feeding in larval fishes: the role of frictional forces](https://consensus.app/papers/details/973637c711b95c0a9853b3d24e0ebe7c/?utm_source=chatgpt) — M. R. Drost, M. Muller, J. W. M. Osse, 1988, *Proceedings of the Royal Society of London. Series B. Biological Sciences*, 39 citations.

[15] [Suction feeding across fish life stages: flow dynamics from larvae to adults and implications for prey capture](https://consensus.app/papers/details/2bdd171c3f6b5a7484db2f37ca59eb93/?utm_source=chatgpt) — S. Yaniv, D. Elad, R. Holzman, 2014, *Journal of Experimental Biology*, 43 citations.

[16] [The hydrodynamic regime drives flow reversals in suction-feeding larval fishes during early ontogeny](https://consensus.app/papers/details/2370371afe265e07a8bddf649159f3d0/?utm_source=chatgpt) — Krishnamoorthy Krishnan, A. Nafi, R. Gurka, R. Holzman, 2020, *The Journal of Experimental Biology*, 2 citations.

[17] [Feeding kinematics, suction and hydraulic jetting capabilities in bearded seals (Erignathus barbatus)](https://consensus.app/papers/details/1f77eea741bd5ae389ad1cf99ff91885/?utm_source=chatgpt) — C. Marshall, K. Kovacs, C. Lydersen, 2008, *Journal of Experimental Biology*, 77 citations.

[18] [Transient Pressure Modeling in Jetting Animals](https://consensus.app/papers/details/a341291c0def51bb85754da84d07114a/?utm_source=chatgpt) — M. Krieg, K. Mohseni, 2020, *Journal of Theoretical Biology*, 3 citations.

[19] [Suction-based propulsion as a basis for efficient animal swimming](https://consensus.app/papers/details/32f59065f0a65b23bb13efd5050093b6/?utm_source=chatgpt) — B. Gemmell, S. Colin, J. Costello, J. Dabiri, 2015, *Nature Communications*, 133 citations.

[20] [A fundamental propulsive mechanism employed by swimmers and flyers throughout the animal kingdom](https://consensus.app/papers/details/d17c3176baa15e5fad968e6c7659dee1/?utm_source=chatgpt) — J. Costello, S. Colin, B. Gemmell, J. Dabiri, E. Kanso, 2023, *The Journal of Experimental Biology*, 3 citations.

[21] [A mathematical model of the defence mechanism of a bombardier beetle](https://consensus.app/papers/details/8a834e2c692c5df1a9731fe5944a334c/?utm_source=chatgpt) — A. James, K. Morison, S. Todd, 2013, *Journal of The Royal Society Interface*, 8 citations.

[22] [Defensive spray of the bombardier beetle: a biological pulse jet](https://consensus.app/papers/details/2ba8fb30b08a51b7b19b0eac1e2d9f87/?utm_source=chatgpt) — J. Dean, D. Aneshansley, H. Edgerton, T. Eisner, 1990, *Science*, 70 citations.

[23] [Mechanistic origins of bombardier beetle (Brachinini) explosion-induced defensive spray pulsation](https://consensus.app/papers/details/0a49f03f885e5ba299a461aef9a98a5e/?utm_source=chatgpt) — Eric M. Arndt, Wendy Moore, Wah-Keat Lee, Christine Ortiz, 2015, *Science*, 61 citations.

[24] [The bombardier beetle and its use of a pressure relief valve system to deliver a periodic pulsed spray](https://consensus.app/papers/details/a22d73809ad95241a85775ddc1477986/?utm_source=chatgpt) — N. Beheshti, A. McIntosh, 2007, *Bioinspiration & Biomimetics*, 35 citations.

[25] [Suction feeding by small organisms: Performance limits in larval vertebrates and carnivorous plants](https://consensus.app/papers/details/3359631edb6752d0b3f81247ac2f1bc6ac43ddbee29586/?utm_source=chatgpt) — S. Deban, R. Holzman, U. Müller, 2020, *Integrative and Comparative Biology*, 9 citations.

[26] [Shooting Mechanisms in Nature: A Systematic Review](https://consensus.app/papers/details/0a93123278a156f0a4c0aaca6e156b87/?utm_source=chatgpt) — A. Sakes, Marleen van der Wiel, P. Henselmans, J. V. van Leeuwen, Dimitra Dodou, P. Breedveld, 2016, *PLoS ONE*, 88 citations.

[27] [Versatility of hydraulic systems](https://consensus.app/papers/details/bde39679225c5d34a0d496f0be2cf1f4/?utm_source=chatgpt) — G. Chapman, 1975, *Journal of Experimental Zoology*, 52 citations.

[28] [A Review of Biological Fluid Power Systems and Their Potential Bionic Applications](https://consensus.app/papers/details/a2d00eea1ec2534d8c54edd85a549ef3/?utm_source=chatgpt) — Chun-bao Liu, Yingjie Wang, Luquan Ren, L. Ren, 2019, *Journal of Bionic Engineering*, 21 citations.

[29] [Particle motion: the missing link in underwater acoustic ecology](https://consensus.app/papers/details/b2ac0ce4aec85bd4bf2e7a0e9670fbb2/?utm_source=chatgpt) — S. Nedelec, James A. Campbell, A. Radford, S. Simpson, N. Merchant, 2016, *Methods in Ecology and Evolution*, 187 citations.

[30] [Sensory ecology of the fish lateral-line system: Morphological and physiological adaptations for the perception of hydrodynamic stimuli](https://consensus.app/papers/details/cd85e9e5b21b55dea761560c21749382/?utm_source=chatgpt) — J. Mogdans, 2019, *Journal of Fish Biology*, 88 citations.

[31] [Hydrodynamic stimuli and the fish lateral line](https://consensus.app/papers/details/44e7ccbededf56f29071e884879831da/?utm_source=chatgpt) — J. Engelmann, W. Hanke, J. Mogdans, H. Bleckmann, 2000, *Nature*, 265 citations.

[32] [Bioacoustics and the Lateral Line System of Fishes](https://consensus.app/papers/details/b099cec92ab7573cb41f72d0ac975674/?utm_source=chatgpt) — J. Webb, J. Montgomery, J. Mogdans, 2008, journal listed as Unknown Journal, 63 citations.

[33] [Object localization through the lateral line system of fish: theory and experiment](https://consensus.app/papers/details/3c61e4f8684d55ebb6b92dc694466641/?utm_source=chatgpt) — Julie Goulet, J. Engelmann, B. Chagnaud, Jan-Moritz P. Franosch, M. Suttner, J. van Hemmen, 2007, *Journal of Comparative Physiology A*, 116 citations.

[34] [Artificial lateral line with biomimetic neuromasts to emulate fish sensing](https://consensus.app/papers/details/912f9b4384fe57248fcecadab09af756/?utm_source=chatgpt) — Yingchen Yang, Nam H. Nguyen, N. Chen, M. Lockwood, C. Tucker, Huan Hu, H. Bleckmann, Chang Liu, Douglas L. Jones, 2010, *Bioinspiration & Biomimetics*, 182 citations.

[35] [Percussive foraging in the aye-aye, Daubentonia madagascariensis](https://consensus.app/papers/details/b97b44413f24565f971e1cc64d5ff13a/?utm_source=chatgpt) — C. J. Erickson, 1991, *Animal Behaviour*, 75 citations.

[36] [Percussive Foraging: Stimuli for Prey Location by Aye-Ayes (Daubentonia madagascariensis)](https://consensus.app/papers/details/178f25881c9c528c905749c479e2b3af/?utm_source=chatgpt) — C. J. Erickson, S. Nowicki, L. Dollar, N. Goehring, 1998, *International Journal of Primatology*, 41 citations.

[37] [The acoustic near-field measurement of aye-ayes’ biological auditory system utilizing a biomimetic robotic tap-scanning](https://consensus.app/papers/details/bf4767c8ab865069b79590d4f3585dde/?utm_source=chatgpt) — H. Nemati, Ehsan Dehghan-Niri, 2020, *Bioinspiration & Biomimetics*, 10 citations.

[38] [An innovative deep neural network–based approach for internal cavity detection of timber columns using percussion sound](https://consensus.app/papers/details/15d956b46c5654d68dcdc3c561285a34/?utm_source=chatgpt) — Lin Chen, H. Xiong, Xiaohan Sang, Cheng Yuan, Xiuquan Li, Qingzhao Kong, 2021, *Structural Health Monitoring*, 42 citations.
