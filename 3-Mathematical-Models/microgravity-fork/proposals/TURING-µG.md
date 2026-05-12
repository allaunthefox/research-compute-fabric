# TURING-µG: TURING-µG — Convection-Free Turing Pattern Formation in Microgravity

**Priority:** High | **TRL:** TRL 3 | **Est. Crew Hours:** 4h
**Principal Regime:** diffusion/reaction-diffusion

---

## Physics Basis

Turing's 1952 mechanism (∂c/∂t = f(c) + D·∇²c) predicts spontaneous spatial pattern formation when an inhibitor diffuses faster than its activator. On Earth, buoyancy-driven convection disrupts the delicate concentration gradients before patterns can fully form. This has NEVER been experimentally verified in a pure liquid-phase reaction-diffusion system — all ground-based demonstrations use gels, microemulsions, or flow cells to suppress convection. µg eliminates convection entirely, enabling the first convection-free liquid Turing experiment.

---

## Experimental Design

The chlorite-iodide-malonic acid (CIMA) reaction is prepared in two pre-loaded syringes inside the MSG. At t=0, the reagents are mixed and injected into a thin observation cell (50mm × 50mm × 1mm depth, quartz windows, no gel). The cell is held at constant T (20±0.1°C) via Peltier. A CCD camera images the cell every 10s at 1024×1024 resolution through a 600nm bandpass filter (iodine-starch complex absorption). The experiment runs for 24 hours to capture pattern formation, stabilization, and any long-term drift. Control experiment: identical setup in a 1mm gel layer (agarose 1%) to compare with the convection-free liquid. A second run varies the cell depth (0.5mm, 1mm, 2mm) to map the transition from 2D to 3D pattern formation as diffusion becomes isotropic.

---

## Required ISS Hardware

Microgravity Science Glovebox (MSG), syringe pumps (existing), quartz observation cell (new, ~$3k), Peltier thermal stage (new, COTS), CCD camera with filter wheel (existing in MSG). CIMA reagents are non-toxic at these concentrations; approved for ISS. Total new hardware: <$10k.

---

## Expected Result

Without convection, Turing patterns should emerge at reaction-diffusion length scales 2-5× larger than in gels (where convection still operates at pore scale). The wavelength λ_Turing = 2π√(D_a·D_i/(k₁·k₂)) should match the linear stability analysis exactly — something no ground experiment has achieved. The pattern should be isotropic (no gravity-induced vertical asymmetry). At 2mm depth, 3D Turing structures (bcc-like standing waves) may emerge — never observed in any liquid system. The experiment provides the cleanest test of Turing's 1952 theory and validates #465 Fick's 2nd law for multi-component diffusion without convective correction terms.

---

## Eigenmass Justification

Eigenmass prediction: §580 Brunt-Väisälä frequency VANISHES (gravity_status='vanishes'), removing the convective instability mechanism. §465 Fick's 2nd law and §464 Fick's 1st law BECOME DOMINANT (gravity_status='becomes_dominant') — they are now the SOLE transport mechanism. The Rayleigh number Ra = g·β·ΔT·L³/(ν·α) → 0, so the Turing instability threshold becomes the PURE reaction-diffusion threshold: Turing bifurcation when D_i/D_a > critical ratio. The constraint graph correctly identifies that the dominant eigenmode shifts from Ra-governed to D-governed. This experiment IS the eigenmass made visible.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
