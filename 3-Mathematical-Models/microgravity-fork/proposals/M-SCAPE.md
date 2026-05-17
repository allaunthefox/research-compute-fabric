# M-SCAPE: M-SCAPE — Marangoni-Driven Self-Assembled Particle Architectures in Microgravity

**Priority:** Medium | **TRL:** TRL 2 | **Est. Crew Hours:** 6h
**Principal Regime:** surface tension/Marangoni + diffusion

---

## Physics Basis

Temperature gradients at a liquid-gas interface produce surface tension gradients (∂γ/∂T), which drive Marangoni convection. In µg, this convection is NOT overridden by buoyancy (Rayleigh-Bénard convection), so Marangoni flow cells become the primary circulation mechanism. Suspended microparticles are advected by these flows and can organize — accumulating at stagnation points, being trapped in vortex cores, or forming regular arrays at the interface. On Earth, simultaneous buoyancy-driven convection disrupts these patterns. µg enables pure thermocapillary organization: the Marangoni number Ma = (dγ/dT)·ΔT·L/(μ·α) is the sole dimensionless control parameter.

---

## Experimental Design

A shallow liquid layer (silicone oil, 1 cSt or 10 cSt, 2mm depth, containing 10µm fluorescent polystyrene tracer particles at 0.01% w/v) is placed in a 50mm-diameter circular cell with a thermoelectric heater ring at the perimeter and a cooled central post. This creates a radial temperature gradient ΔT = 2-10°C, driving outward Marangoni flow at the surface and return flow beneath (thermocapillary cells). The particle distribution is imaged from above via fluorescence microscopy (488nm excitation, 520nm emission) every 5s. Particle image velocimetry (PIV) extracts the 2D surface velocity field. The experiment runs for 60 minutes per ΔT setting. A secondary experiment replaces the radial gradient with a linear gradient (heated/cooled edges) to observe the transition from axisymmetric cells to roll patterns.

---

## Required ISS Hardware

Fluid Science Laboratory (FSL) or MSG, Peltier heater/cooler ring with PID controller (new, COTS, ~$3k), fluorescent tracer particles (commercial), 488nm LED + 520nm filter + CMOS camera (new, COTS, ~$5k). Silicone oil is non-toxic, low vapor pressure — ISS-approved fluid. Total new hardware: <$10k.

---

## Expected Result

At low Ma (Ma < Ma_crit ≈ 80), flow should be steady and axisymmetric — particles will trace streamlines that reveal the thermocapillary cell structure. At higher Ma, the flow transitions to oscillatory (standing waves) and eventually turbulent (JAXA's Marangoni experiments confirmed this sequence). At intermediate Ma, stable stagnation rings should form where surface flow diverges — particles should accumulate at these rings, forming visible concentric circles. The ring spacing should follow λ ∝ (μ·α/(dγ/dT·ΔT))¹/³ — the characteristic Marangoni length. If particles DO self-organize at stagnation points, this is the first demonstration of Marangoni-driven directed assembly in µg — with direct applications to manufacturing structured materials in orbit.

---

## Eigenmass Justification

Eigenmass predicts: In µg, Ra = g·β·ΔT·L³/(ν·α) → 0. ONLY Ma governs. §189 surface tension BECOMES DOMINANT (gravity_status='becomes_dominant'). The constraint graph shows that the §179 Bernoulli equation LACKS its gravitational term — all pressure-driven flow is from ∇γ, not ∇(ρ·g·z). The Marangoni stress balance at the interface (∂γ/∂T)·∇T = μ·∂v/∂n is the sole boundary condition. This experiment is the eigenmass routing diagram made physical: when you remove the Ra node from the graph, the Ma node becomes the ONLY circulation driver. Particles will trace the Ma eigenmode.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
