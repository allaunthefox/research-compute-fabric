# WIGNER-µG: WIGNER-µG — 3D Colloidal Wigner Crystals from Neutral Suspensions in Microgravity

**Priority:** High | **TRL:** TRL 2-3 | **Est. Crew Hours:** 8h
**Principal Regime:** colloid/DLVO/crystallization

---

## Physics Basis

A Wigner crystal is a lattice of particles ordered solely by electrostatic repulsion. In plasmas, PK-3 Plus and PKE-Nefedov demonstrated this on the ISS: charged microparticles formed bcc, fcc, and hcp Coulomb crystals in 3D. But for NEUTRAL colloids — polystyrene latex or silica spheres in water — the gravitational sedimentation pressure compresses the crystal to a 2D monolayer or a disordered glass. Even in matched-density solvents, residual convection and thermal gradients destroy long-range order on Earth. µg removes sedimentation entirely and allows the full 3D phase diagram (bcc → fcc → fluid) to be explored as a function of Debye screening length κ and particle volume fraction φ.

---

## Experimental Design

Monodisperse polystyrene spheres (diameter 1.0 ± 0.02 µm, 2.5% w/v in 10⁻⁴ M KCl) are loaded into a quartz observation cell (10mm × 10mm × 10mm) inside the Fluid Science Laboratory (FSL) or MSG. The cell has transparent ITO-coated walls to apply a uniform electric field. The particle volume fraction φ is varied (0.001 to 0.05) and the Debye length κ⁻¹ is controlled by KCl concentration (10⁻⁵ to 10⁻³ M, κ⁻¹ = 10-100 nm). 3D particle positions are tracked via confocal laser scanning microscopy or digital holographic microscopy (DHM). A CCD records z-stacks every 30s for 72 hours to observe crystallization kinetics. Control: identical cell run in 1g on ISS centrifuge (if available) or ground control with matched parameters.

---

## Required ISS Hardware

Fluid Science Laboratory (FSL) or Microgravity Science Glovebox, syringe pumps (existing), ITO-coated quartz cell (new, ~$5k), confocal microscope module (ESA has flown prototype on ISS — FSL's optical diagnostics module), DC power supply for electric field. Particle suspension is stable in storage; KCl solution prepackaged. Total new hardware: <$15k.

---

## Expected Result

At low φ and large κ⁻¹ (weak screening), the suspension should remain fluid. As φ increases or κ⁻¹ decreases (stronger electrostatic coupling), the system should crystallize — first into bcc at low φ (~0.005-0.01), then fcc at higher φ. The phase transition is predicted at Γ = (Z*²·e²)/(4πε₀·ε_r·a·k_B T) > Γ_crit ≈ 106 (for bcc, Robbins-Kremer-Grest 1988). This experiment directly measures Γ_crit for charged colloids in 3D without gravitational compression — the cleanest test of Wigner crystallization in soft matter. The crystal lattice constant a should scale as a ∝ n^{−1/3} (where n is number density), confirming that gravity no longer compresses the lattice.

---

## Eigenmass Justification

Eigenmass prediction: In µg, the Peclet number Pe = (4πR⁴·Δρ·g)/(3k_B T) → 0 — sedimentation vanishes entirely. §459 DLVO theory BECOMES DOMINANT (gravity_status='becomes_dominant') — the Yukawa potential U(r) = (Z*²·e²/4πε₀ε_r)·exp(−κr)/r is the SOLE interparticle interaction. §188 Archimedes principle VANISHES (gravity_status='vanishes'). PK-3 Plus proved the PRINCIPLE for plasma particles. WIGNER-µG extends this to neutral colloids — the eigenmass predicts identical DLVO-governed phase behavior at a different Debye length scale. The constraint graph says: same equations, different κ, same 3D crystallization.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
