# RG Flow Assumption DAG — 2026-05-13

Seven generations of assumptions traced. Only Gens 1-2 pass inspection.

---

## Generation 1: SM beta functions ← SOLID
Standard 1-loop RGEs for SM couplings. Validated by LEP, LHC, g-2 to 10^-12.
- β(λ) — Higgs quartic running
- β(α) — QED running
- β(g₃) — QCD running
- Truncated at 1-loop; 2-loop corrections known but not implemented

## Generation 2: omega = |β|/|g| ← DEFINED, INTERPRETATION WEAK
omega = 0.05775 at the EW scale. Well-defined dimensionless number.
But calling it "torsion" (Einstein-Cartan) is a metaphysical leap — no connection to spacetime torsion is shown. The norm-ratio interpretation has no geometric justification.

## Generation 3: alpha = max|β|/(4π) ← INVENTED
No Lagrangian term produces this relation. The 1-loop formula gives 10% error; the "2-loop correction" is retrofitted to match α = 1/137.036. If this were correct QED, it would be the biggest discovery since Feynman. It appears to be curve-fitting.

## Generation 4: w0 = -1 + 2·f_lam·ω·P ← HEURISTIC
Heuristic projection formula with no QFT derivation. The projection factor P uses ΛCDM best-fit values (Ω_DE = 0.71, Ω_m = 0.29) to predict a deviation from ΛCDM — circular. Predicted value (-0.953) is 2.1σ from DESI (-0.838) with no model uncertainty.

## Generation 5: wa from SM running ← HONEST GAP
SM gives wa ≈ -0.06 from Higgs running. DESI observes wa = -0.59 ± 0.25. Factor 10 gap. This is the most interesting tension in the model — if DESI holds, the SM Higgs sector alone cannot produce the observed dark energy evolution.

## Generation 6: CMB from omega ← BROKEN
Q ≈ ω·α/π predicts CMB fluctuation amplitude 13× above measured. The factor 13 is handwaved as "Saha approximation error." T_CMB requires η (baryon asymmetry) as input — circular, since η is not explained by the torsion model (baryogenesis gap: factor 10¹²).

## Generation 7: M-sigma from fractal sum ← CURIOSITY
d_H + D_K = ln(80)/ln(3) = 3.989 ≈ 4.0 is a numerical coincidence. No GR or fluid mechanism connects fractal dimensions to BH scaling.

---

## Verdict

| Gen | Name | Status | Action |
|-----|------|--------|--------|
| 1 | SM beta functions | SOLID | Keep as-is |
| 2 | omega = |β|/|g| | CURIOUSTY | Keep, remove "torsion" label |
| 3 | alpha = max|β|/(4π) | INVENTED | Needs derivation or delete |
| 4 | w0 projection | HEURISTIC | Needs QFT derivation |
| 5 | wa from SM | HONEST GAP | Keep as open question |
| 6 | CMB from omega | BROKEN | Delete Q formula, keep T_CMB chain as curiosity |
| 7 | M-sigma sum | CURIOSITY | Keep as coincidence, not theory |

**The seed omega = 0.05775 is real. The projections are not.**

Recommended deletions: CMBTorsion.lean, TorsionWall.lean (unless alpha formula gets a proper derivation), CouplingRotation.lean (w0 formula is heuristic).
