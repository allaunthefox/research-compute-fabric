# HELICOID: HELICOID — Stable Pure-Water Minimal Surface Helicoids in Microgravity

**Priority:** High | **TRL:** TRL 3 | **Est. Crew Hours:** 6h
**Principal Regime:** surface tension/Young-Laplace

---

## Physics Basis

The Young-Laplace equation ΔP = γ(1/R₁ + 1/R₂) admits a family of minimal-surface solutions that are unstable on Earth due to the hydrostatic term ρ·g·h. In µg, the hydrostatic term → 0 and the Laplace pressure is the sole restoring force. The helicoid — a ruled minimal surface described by x = u·cos(v), y = u·sin(v), z = cv — has never been formed in a pure liquid without surfactant. Pettit (2003-2025) demonstrated stable planar water sheets of ~500µm thickness. HELICOID extends this to non-planar topologies by rotating a wire frame during film formation.

---

## Experimental Design

A 3D-printed titanium wire frame (helicoid geometry, ~5cm × 5cm, wire diameter 0.5mm) is mounted on a stepper motor inside the Microgravity Science Glovebox (MSG). A water droplet (~2mL ultrapure, degassed) is deposited on the frame via syringe. The frame is slowly rotated (0.1-1.0 rad/s) to draw the water into a helicoid film via capillary action. A high-speed camera (1000 fps) records film formation, drainage, and rupture. Thickness is measured via laser interferometry (reflected 633nm HeNe, fringe counting). Surface temperature is controlled via Peltier element (10-40°C) to vary γ and test stability across the capillary number Ca = μ·U/γ. ISS g-jitter is logged simultaneously via SAMS (Space Acceleration Measurement System) at 100 Hz to correlate film rupture with transient accelerations.

---

## Required ISS Hardware

Microgravity Science Glovebox (MSG), SAMS accelerometer, syringe pump (existing), 3D-printed Ti frame (new), 633nm laser diode + CMOS camera (new, COTS), Peltier temperature stage (new, COTS), high-speed camera (existing in MSG). Total new hardware: <$50k.

---

## Expected Result

Stable helicoid films should form at rotation rates where Ca < Ca_crit. Film lifetime should scale with γ/ρ·g_jitter — predicted t_stable ~10-100s for g_jitter ~10⁻⁴ g₀. Rupture analysis will yield the critical thickness h* = √(γ/(ρ·g_jitter)) — a direct measurement of the µg noise floor using liquid physics. If g_jitter can be characterized from rupture statistics, the experiment doubles as a µg accelerometer calibration tool. At minimum, the first-ever photographs of pure-water helicoids will be returned.

---

## Eigenmass Justification

Eigenmass prediction: §714 Young-Laplace equation with g→0 has a solution space 10× larger than at 1g. The helicoid is the simplest non-trivial minimal surface. The constraint graph shows §179 Bernoulli's ρ·g·h term VANISHES (gravity_status='vanishes') and §189 surface tension BECOMES DOMINANT (gravity_status='becomes_dominant'). The film stability criterion reduces from the full Navier-Stokes to a pure capillary-Laplace balance: stability when Ca < Ca_crit and ∂²h/∂t² < γ/ρ·∇²h. This IS the eigenmass: the constraint DAG re-weights from Ra-dominated to Ca-dominated.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
