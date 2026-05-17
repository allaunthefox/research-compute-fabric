# LIQUID-TOWER: LIQUID-TOWER — Sub-Rayleigh-Limit Liquid Columns and Water Bridges in Microgravity

**Priority:** Medium | **TRL:** TRL 2 | **Est. Crew Hours:** 5h
**Principal Regime:** surface tension/Plateau-Rayleigh

---

## Physics Basis

The Plateau-Rayleigh instability predicts that a liquid column of radius R is unstable to perturbations with wavelength λ > 2πR. On Earth, this is modified by gravity: the hydrostatic head sags the column and accelerates breakup. The maximum stable length of a water bridge between two surfaces on Earth is ~3-5mm (depending on contact angle). In µg, the hydrostatic term vanishes and the instability is governed solely by surface tension. The Rayleigh criterion predicts stable columns at aspect ratios AR = L/R up to ~2π (the critical wavelength), after which the column should undergo varicose breakup. This has been partially tested (Pettit observed ~8cm water bridges holding a camera lens), but the quantitative stability limit — and what happens when it's crossed — has never been systematically measured.

---

## Experimental Design

Two 10mm-diameter stainless steel disks (one fixed, one on a linear actuator) are mounted inside the MSG. A 5mL degassed water droplet is placed between them. The actuator slowly separates the disks (0.1-2.0 mm/s) while a high-speed camera records the column profile. Separation continues until column rupture. Variables tested: (1) separation speed, (2) disk surface treatment (hydrophilic Ti vs hydrophobic PTFE coating), (3) liquid viscosity (water, water-glycerol mixtures at η=1-100 cP to vary Ohnesorge number Oh = μ/√(ρ·γ·R)). Disk vibration (controlled via piezoelectric exciter) applied to map the full dispersion relation ω(k) of capillary waves on the column — measuring both the Rayleigh (varicose) and the less-studied sinuous (bending) instability modes.

---

## Required ISS Hardware

Microgravity Science Glovebox (MSG), linear actuator (existing in MSG), 3D-printed disk mounts (new, $1k), high-speed camera (existing), piezoelectric disk driver (new, COTS, $500). Total new hardware: <$5k.

---

## Expected Result

For pure water (Oh ≈ 10⁻³), stable columns should persist to L/R ≈ 2π ≈ 6.3 — confirmed if the bridge holds at 10mm disk diameter up to ~63mm separation. At rupture, the breakup should follow the classical varicose mode (periodic necking) with wavelength λ* ≈ 9R, producing uniform droplets predicted by Rayleigh in 1878. For viscous liquids (Oh > 1), the stability limit should extend BEYOND 2π due to viscous damping of capillary waves — a regime inaccessible on Earth where gravity-driven drainage dominates. The experiment directly measures the Ohnesorge-dependent stability boundary of the Plateau-Rayleigh instability for the first time without gravity.

---

## Eigenmass Justification

Eigenmass prediction: §518 Plateau-Rayleigh instability loses its gravitational drainage term. The dispersion relation simplifies to ω² = (γk/ρR²)·(1−k²R²)·I₁(kR)/I₀(kR) (Rayleigh 1878). §179 Bernoulli's ρ·g term VANISHES. §189 surface tension (Young-Laplace) BECOMES DOMINANT. The critical L/R predicted by the constraint DAG without g-correction is exactly 2π for inviscid fluids — this experiment IS the null-gravity validation of Rayleigh's 1878 prediction. The eigenmass says: the instability is PURE. Measure it.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
