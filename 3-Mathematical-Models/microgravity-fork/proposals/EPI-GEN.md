# EPI-GEN: EPI-GEN — Multi-Generational Epigenetic Drift and Landauer's Limit in Microgravity C. elegans

**Priority:** Highest | **TRL:** TRL 4 (CBEF is flight-proven) | **Est. Crew Hours:** 10h
**Principal Regime:** information theory/epigenetics

---

## Physics Basis

Landauer's principle states that erasing 1 bit of information dissipates ≥ k_B T ln 2 of heat. In epigenetics, every DNA methylation mark set or erased is a bit flip — and it has a thermodynamic cost. In µg, the NASA Twin Study showed altered gene expression (>7% of genes) and telomere lengthening in Scott Kelly — both processes involve epigenetic regulation. But what happens across GENERATIONS? If the epigenetic maintenance budget is set by Nernst-governed ion gradients (§593), and those gradients are altered in µg (no hydrostatic pressure → fluid shift → altered membrane potentials), then the energy available for methylation maintenance changes. Over generations, this should produce a detectable drift in the methylome — a Landauer-limited information degradation across reproductive cycles.

---

## Experimental Design

C. elegans N2 wild-type (generation time ~3 days at 20°C, ~1000 somatic cells, fully sequenced genome and methylome) is cultured in the CBEF (Cell Biology Experiment Facility) inside Kibo. Four parallel populations are maintained: (1) µg continuous, (2) µg + 1g ISS centrifuge control, (3) ground control (1g), (4) ground control + simulated µg (clinostat). Each population runs for 20 generations (~60 days total). At generations 1, 5, 10, 15, and 20, samples are frozen at −80°C (MELFI freezer). Post-flight: whole-genome bisulfite sequencing (WGBS) maps methylation at single-base resolution. RNA-seq measures gene expression. Whole-genome sequencing identifies mutation accumulation. Analysis: methylation entropy H(t) = −Σ p_i·log₂(p_i) across CpG sites, measured as a function of generation number. Landauer prediction: dH/dt ≥ 0 (entropy of methylation pattern never decreases) and the rate should be higher in µg if the Nernst ion budget is constrained.

---

## Required ISS Hardware

Kibo CBEF (Cell Biology Experiment Facility — existing, has temperature control and 1g centrifuge), C. elegans culture plates and bacterial food (standard, ISS-approved), MELFI −80°C freezer (existing), fixation/storage tubes. No new ISS hardware required — all existing. Post-flight sequencing is ground-based. Total new hardware: $0. This experiment could fly on the next ISS resupply.

---

## Expected Result

Prediction 1: Methylation entropy H(t) should increase across generations in ALL populations (Landauer's principle — information erasure is irreversible). Prediction 2: H(t) should increase FASTER in µg than in 1g, because the Nernst-limited ion gradient budget (§593) reduces the metabolic energy available for methylation maintenance. Prediction 3: The µg+1g centrifuge control should show H(t) closer to ground 1g controls — confirming the effect is g-dependent, not radiation-dependent. Prediction 4 (most specific): the per-generation mutation rate should increase slightly but measurably in µg — consistent with p53 pathway alteration seen in Rad Gene experiment. This experiment connects Landauer's 1961 principle (information thermodynamics) to biological evolution (multi-generation genetic drift) for the first time — using µg as the experimental perturbation that would be impossible to achieve on Earth (no way to uniformly alter membrane potentials across all cells for 20 generations).

---

## Eigenmass Justification

Eigenmass prediction: This is the MOST complex proposal because it crosses three regimes. (1) §324 Landauer's principle (INFORMATION regime): methylation maintenance costs ≥ k_B T ln 2 per bit. (2) §593 Nernst equation (ELECTROCHEMICAL regime): membrane potential ΔΨ sets the per-cell energy budget via [Mg²⁺] and ATP synthesis. (3) In µg, §577 hydrostatic equation VANISHES (gravity_status='vanishes') → fluid shift → altered ion distribution → altered §594 GHK resting potential. The constraint graph predicts: Landauer's INFORMATION floor + altered Nernst ELECTROCHEMICAL budget = detectable epigenetic drift rate change. The eigenmass identifies §324 (INFORMATION, chiral scar Δ=83%) and §593 (ELECTROCHEMICAL, chiral scar Δ=74%) as the two most-handed equations in the biophysics subgraph — EPI-GEN measures their INTERACTION over evolutionary time.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
