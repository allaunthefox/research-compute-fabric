# FOLD-µG: FOLD-µG — Microgravity Protein Folding: Solvent Structure and Free Energy Landscapes

**Priority:** Medium | **TRL:** TRL 2-3 | **Est. Crew Hours:** 6h
**Principal Regime:** biophysics/protein folding

---

## Physics Basis

The Gibbs free energy of protein folding ΔG_fold = ΔH − TΔS has no explicit g-dependence. BUT: water's hydrogen bond network — the solvent that mediates the hydrophobic effect driving folding — is subtly structured by gravity on Earth. Rayleigh-Bénard convection cells in any aqueous solution create microscopic thermal gradients that perturb the hydration shell around folding proteins. In µg, these convection cells vanish. The question: does removing gravity-driven solvent perturbation change the folding free energy landscape? If ΔG_fold shifts by even 0.5 k_B T, it's a measurable effect with implications for protein-based pharmaceuticals manufactured in orbit and for understanding whether the hydrophobic effect has a gravitational component. No one has directly measured protein folding thermodynamics in µg.

---

## Experimental Design

Hen egg-white lysozyme (HEWL, the most-studied folding model, 129 residues, well-characterized ΔG_fold = −8.7 kcal/mol at pH 7, 25°C) is loaded into the FSL. A temperature-controlled cuvette (10-90°C, ±0.1°C) containing HEWL at 0.1 mg/mL in 50mM phosphate buffer pH 7.0 is heated slowly (1°C/min). Circular dichroism (CD) at 222nm (α-helix signal) and intrinsic tryptophan fluorescence (295nm excitation, 340nm emission — sensitive to tertiary structure burial) are measured simultaneously. The thermal denaturation curve yields T_m (midpoint of unfolding) and ΔH_vH (van't Hoff enthalpy). Four conditions: (1) µg, (2) µg + osmolytes (TMAO 0.5M — stabilizes folded state), (3) µg + denaturant (urea 2M), (4) ground 1g controls for all three. Each run takes ~2 hours. The experiment requires 8 runs total (4 conditions × 2 replicates). A secondary experiment measures folding KINETICS via stopped-flow: rapid dilution of urea-denatured HEWL into refolding buffer, monitoring Trp fluorescence with ms time resolution.

---

## Required ISS Hardware

Fluid Science Laboratory (FSL — existing, has optical diagnostics), temperature-controlled cuvette module (new, ~$10k for CD + fluorescence optics in microfluidic format), stopped-flow microfluidic chip (new, ~$5k, COTS microfluidics). Lysozyme and buffers are standard, ISS-approved. Total new hardware: <$20k.

---

## Expected Result

The null hypothesis is ΔG_fold(µg) = ΔG_fold(1g). If true, this experiment RETURNS NOTHING USEFUL and that IS the result — it proves gravity does not affect protein folding thermodynamics, closing a fundamental question. If ΔG_fold differs (predicted shift ≤ 1 kcal/mol, or ~1.7 k_B T at 298K), the sign and magnitude will reveal whether the hydrophobic effect is gravity-sensitive. A stabilization in µg (ΔG more negative) would suggest that convection-driven solvent perturbation on Earth slightly DESTABILIZES folded proteins — meaning proteins fold marginally better in space, with implications for long-duration spaceflight pharmacology. A destabilization would suggest the opposite. Either result is publishable in Nature or Science because this question has been OPEN since the first protein crystallizations in space (1980s) produced better crystals — but no one knew whether the improvement was from better nucleation (diffusion-limited, now understood) or from BETTER FOLDING (never tested).

---

## Eigenmass Justification

Eigenmass prediction: The constraint graph says: §78 Helmholtz free energy F = U − TS has no g term. But §79 Gibbs free energy G = H − TS = U + PV − TS DOES have a subtle g-dependence through P in the solvent — specifically, the hydrostatic pressure term in §577 (barometric equation) vanishes in µg. The question is whether the Δ(PV) term in the folding free energy is meaningful. For HEWL, the volume change upon folding ΔV_fold ≈ −50 mL/mol (typical for proteins — folding excludes solvent and compacts the structure). At 1g over a 1cm cuvette, ΔP_hydrostatic = ρ·g·Δh ≈ 100 Pa. Δ(PV)_hydrostatic ≈ 100 Pa × (−5×10⁻⁵ m³/mol) ≈ −5×10⁻³ J/mol ≈ 10⁻⁶ k_B T — UTTERLY NEGLIGIBLE. The constraint graph predicts the null hypothesis CORRECTLY: ΔG_fold should be IDENTICAL in µg. BUT: this experiment has never been done, and proving the null result IS the scientific value. The eigenmass constrains the search space: if there IS an effect, it MUST be from solvent structuring (ΔS term), not from Δ(PV) — and the graph tells you to look at §300 Gibbs entropy formula for the solvent, not §577 hydrostatic.

---

*Proposal generated from eigenmass constraint graph analysis of physics_microgravity.db. All predictions derive from the chiral eigenmass theorem — the shift in AMVR/AVMR centrality when g → 0.*
