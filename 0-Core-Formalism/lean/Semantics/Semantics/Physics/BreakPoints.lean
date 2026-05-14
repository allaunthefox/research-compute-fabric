-- BreakPoints.lean
--
-- Where the model breaks — ranked by likelihood.
-- Every testable model needs clear falsification criteria.
-- These are the knife edges.

namespace Semantics.Physics.BreakPoints

-- ═════════════════════════════════════════════════════════════════════════════
-- KNIFE EDGE 1: w_a (HIGH — factor 10 gap)
-- ═════════════════════════════════════════════════════════════════════════════

-- SM Higgs running gives w_a = -0.06
-- DESI DR2 sees w_a = -0.59 +- 0.25
-- Factor 10 gap. If DESI DR3 tightens to +-0.10 and confirms -0.6,
-- the Higgs sector alone cannot produce this. The model needs a
-- non-Higgs coupling source (top quark? neutrino? axion?).
--
-- Current tension: 2.1 sigma (DESI DR2 w_a error is still large).
-- If DR3 halves the error and the central value stays: TENSION > 4 sigma.

-- ═════════════════════════════════════════════════════════════════════════════
-- KNIFE EDGE 2: w0 projection formula (HIGH — heuristic, 2.1s off)
-- ═════════════════════════════════════════════════════════════════════════════

-- Predicted: w0 = -0.953 from heuristic projection formula
-- DESI DR2:  w0 = -0.838 +- 0.055
-- Residual: 2.1 sigma. The formula w0 = -1 + 2*f_lam*omega*P is heuristic.
-- Needs a proper QFT derivation.
--
-- If DESI DR3 tightens w0 to +-0.03 and the central value stays:
-- residual becomes > 3 sigma. The model is ruled out unless the
-- projection formula can be fixed with a proper derivation.

-- ═════════════════════════════════════════════════════════════════════════════
-- KNIFE EDGE 3: LISA null result (MODERATE — cleanest test, 10 years out)
-- ═════════════════════════════════════════════════════════════════════════════

-- The model predicts 0.13 rad of integrated torsion phase shift at mHz
-- frequencies for high-z gravitational wave sources. LISA (launch ~2035)
-- will have sensitivity to detect this at > 1000 sigma.
--
-- If LISA sees NO shift at 0.01 rad precision: FALSIFIED.
-- If LISA sees exactly 0.13 rad: CONFIRMED.
-- If LISA sees 0.01-0.12 rad: torsion coupling weaker than predicted.

-- ═════════════════════════════════════════════════════════════════════════════
-- KNIFE EDGE 4: SH0ES H0 (MODERATE — 4.8s exclusion could reverse)
-- ═════════════════════════════════════════════════════════════════════════════

-- The model predicts H0 = 68.0 km/s/Mpc. SH0ES measures H0 = 73.04.
-- The model rules out SH0ES at 4.8 sigma. If systematic errors in
-- the SH0ES measurement are small (< 1 km/s/Mpc), the model is correct.
-- If SH0ES is right and Planck/DESI have systematics, the model is wrong.

-- ═════════════════════════════════════════════════════════════════════════════
-- KNIFE EDGE 5: alpha = max|beta|/(4*pi) (LOW — already within 0.3% at 2-loop)
-- ═════════════════════════════════════════════════════════════════════════════

-- If a BSM particle is discovered that changes the SM beta function,
-- the predicted alpha would shift. Fermilab muon g-2 is the most
-- likely source. Current tension with SM: 5 sigma.
-- If g-2 proves BSM, alpha is not from SM beta alone.
-- If g-2 resolves with lattice QCD, alpha from beta stands.

-- ═════════════════════════════════════════════════════════════════════════════
-- SUMMARY
-- ═════════════════════════════════════════════════════════════════════════════

-- The model has 5 knife edges. 2 are high-probability (w_a, w0 formula).
-- 2 are moderate (LISA, SH0ES). 1 is low (alpha).
--
-- The FIRST break will be w_a. If DESI DR3 (2026-2027) confirms
-- w_a ≈ -0.6 with tight error bars, the SM Higgs running alone
-- cannot explain it. The model needs either:
--   1. A non-Higgs coupling source (top quark, neutrino, axion)
--   2. DESI w_a is wrong (systematic in SN data)
--
-- Either way: w_a is the knife edge. Everything else holds together.

end Semantics.Physics.BreakPoints
