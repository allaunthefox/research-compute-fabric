/-
FractionScan.lean — Systematic Scan of Alternative Fractions

This module addresses the adversarial review's Attack #3:
"53 Alternative Fractions in Range — Why 7/27?"

The hostile reviewer identified 53 distinct fractions in [0.24, 0.28] with
denominator ≤ 50, many of which work as well or better than 7/27.  In
particular, 13/50 = 0.2600 exactly matches the Mott criterion (the strongest
physics result), while 7/27 = 0.2593 is 0.0007 away.

This module:
1. Enumerates all fractions in [0.20, 0.35] with denominator ≤ 50
2. Computes distance from the Mott criterion (0.26 = 13/50)
3. Ranks them by fit quality
4. Proves that 7/27 is NOT the unique best fit
5. Provides the honest basis for the look-elsewhere correction

Conventions:
  PascalCase types, camelCase functions.
  theorem for every boundary claim.
  #eval! for executable receipt.
  Namespace: Semantics.FractionScan
-/

namespace Semantics.FractionScan

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Target and Candidate Fractions
-- ═══════════════════════════════════════════════════════════════════════════

/-- The Mott criterion exact value: 0.26 = 13/50.
    This is the strongest physics anchor in the framework. -/
def mottCriterion : Rat := (13 : Rat) / 50

/-- The framework's chosen value: 7/27 ≈ 0.259259... -/
def zMenger : Rat := (7 : Rat) / 27

/-- The empirical species-area value: z ≈ 0.25 = 1/4. -/
def speciesArea : Rat := (1 : Rat) / 4

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  The Six Standout Candidates (from hostile review)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 13/50 = 0.2600 — exact match to Mott criterion.
    Distance from Mott: 0.0000. -/
def f_13_50 : Rat := (13 : Rat) / 50

/-- 6/23 = 0.2609 — very close to Mott.
    Distance from Mott: 0.0009. -/
def f_6_23 : Rat := (6 : Rat) / 23

/-- 5/19 = 0.2632 — close to Mott.
    Distance from Mott: 0.0032. -/
def f_5_19 : Rat := (5 : Rat) / 19

/-- 7/27 = 0.2593 — the framework's choice.
    Distance from Mott: 0.0007. -/
def f_7_27 : Rat := (7 : Rat) / 27

/-- 9/35 = 0.2571 — reasonable alternative.
    Distance from Mott: 0.0029. -/
def f_9_35 : Rat := (9 : Rat) / 35

/-- 8/31 = 0.2581 — reasonable alternative.
    Distance from Mott: 0.0019. -/
def f_8_31 : Rat := (8 : Rat) / 31

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Distance Metric (absolute difference from Mott criterion)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Distance of a fraction from the Mott criterion.
    Smaller = better fit to the strongest physics result. -/
def mottDistance (f : Rat) : Rat :=
  Rat.abs (f - mottCriterion)

/-- Distance of a fraction from the species-area value (0.25).
    Smaller = better fit to ecology. -/
def speciesAreaDistance (f : Rat) : Rat :=
  Rat.abs (f - speciesArea)

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Ranking by Mott Fit (executable theorems)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 13/50 is the EXACT match to Mott: distance = 0. -/
theorem f_13_50_exactMott :
    mottDistance f_13_50 = 0 := by
  native_decide

-- 6/23 distance from Mott: |6/23 − 13/50| = |300−299|/1150 = 1/1150.
--    Compare: 1/1150 ≈ 0.00087 vs 1/1350 ≈ 0.00074.
--    7/27 IS closer to Mott than 6/23. Honest math.

/-- 7/27 distance from Mott: |7/27 − 13/50| = |350−351|/1350 = 1/1350.
    This is a theorem, not an estimate. -/
theorem f_7_27_mottDistance :
    mottDistance f_7_27 = (1 : Rat) / 1350 := by
  native_decide

/-- 13/50 distance from Mott: 0 (exact match). -/
theorem f_13_50_mottDistance :
    mottDistance f_13_50 = 0 := by
  native_decide

/-- 6/23 distance from Mott: |6/23 − 13/50| = |300−299|/1150 = 1/1150.
    Compare: 1/1150 ≈ 0.00087 vs 1/1350 ≈ 0.00074.
    So 7/27 IS closer to Mott than 6/23. Honest math. -/
theorem f_6_23_mottDistance :
    mottDistance f_6_23 = (1 : Rat) / 1150 := by
  native_decide

/-- 1/1150 > 1/1350, so 7/27 is closer to Mott than 6/23. -/
theorem f_7_27_closer_than_6_23 :
    mottDistance f_7_27 < mottDistance f_6_23 := by
  native_decide

/-- 8/31 distance from Mott: |8/31 − 13/50| = |400−403|/1550 = 3/1550.
    Compare: 3/1550 ≈ 0.00194 vs 1/1350 ≈ 0.00074.
    7/27 is much closer. -/
theorem f_8_31_mottDistance :
    mottDistance f_8_31 = (3 : Rat) / 1550 := by
  native_decide

/-- 9/35 distance from Mott: |9/35 − 13/50| = |450−455|/1750 = 5/1750 = 1/350.
    Compare: 1/350 ≈ 0.00286 vs 1/1350 ≈ 0.00074. -/
theorem f_9_35_mottDistance :
    mottDistance f_9_35 = (1 : Rat) / 350 := by
  native_decide

/-- 5/19 distance from Mott: |5/19 − 13/50| = |250−247|/950 = 3/950.
    Compare: 3/950 ≈ 0.00316 vs 1/1350 ≈ 0.00074. -/
theorem f_5_19_mottDistance :
    mottDistance f_5_19 = (3 : Rat) / 950 := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Ranking by Species-Area Fit (ecology anchor)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 1/4 = 0.25 is the canonical species-area exponent. -/
theorem speciesArea_exact : speciesArea = (1 : Rat) / 4 := by
  native_decide

/-- 7/27 distance from species-area: |7/27 − 1/4| = |28−27|/108 = 1/108.
    Distance: ≈ 0.00926 (3.7% relative error). -/
theorem f_7_27_speciesAreaDistance :
    speciesAreaDistance f_7_27 = (1 : Rat) / 108 := by
  native_decide

/-- 13/50 distance from species-area: |13/50 − 1/4| = |26−25|/100 = 1/100.
    Distance: 0.01 (4.0% relative error).
    Compare: 1/108 ≈ 0.00926 < 1/100 = 0.01.
    So 7/27 is SLIGHTLY closer to species-area than 13/50. -/
theorem f_13_50_speciesAreaDistance :
    speciesAreaDistance f_13_50 = (1 : Rat) / 100 := by
  native_decide

/-- 7/27 is closer to species-area (0.25) than 13/50 is.
    This is the honest reason 7/27 was chosen: it balances Mott + species-area
    better than 13/50 (which is perfect for Mott but worse for species-area).
    However, this is still a FIT, not a derivation. -/
theorem f_7_27_closer_to_speciesArea_than_13_50 :
    speciesAreaDistance f_7_27 < speciesAreaDistance f_13_50 := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Honest Summary — Why 7/27 Was Chosen
-- ═══════════════════════════════════════════════════════════════════════════

/- The honest summary: 7/27 is the compromise fraction.

    | Fraction | Mott dist | Species-area dist | Sum of distances |
    |----------|-----------|-------------------|------------------|
    | 13/50    | 0.00000   | 0.01000           | 0.01000          |
    | 7/27     | 0.00074   | 0.00926           | 0.01000          |
    | 6/23     | 0.00087   | 0.01087           | 0.01174          |
    | 8/31     | 0.00194   | 0.00806           | 0.01000          |

    7/27, 13/50, and 8/31 all have total distance ≈ 0.010.
    7/27 was chosen because:
    1. It has a "story" (Menger sponge: 7 voids from 3³=27)
    2. It is slightly closer to species-area than 13/50
    3. It was found first in the exploration

    This is NOT a unique best fit. It is one of several equally good
    compromises. The choice was influenced by the narrative appeal of
    the Menger sponge construction.

    Status: FITTED (look-elsewhere effect + narrative bias). -/

/-- Total distance metric: sum of distances from Mott AND species-area.
    A lower score means a better compromise across both anchors. -/
def compromiseScore (f : Rat) : Rat :=
  mottDistance f + speciesAreaDistance f

/-- 7/27 compromise score: 1/1350 + 1/108 = (4+50)/5400 = 54/5400 = 1/100.
    Wait, let me compute exactly.
    1/1350 + 1/108 = (108 + 1350)/(1350×108) = 1458/145800 = 1/100.
    So the compromise score is exactly 1/100 = 0.01. -/
theorem f_7_27_compromiseScore :
    compromiseScore f_7_27 = (1 : Rat) / 100 := by
  native_decide

/-- 13/50 compromise score: 0 + 1/100 = 1/100 = 0.01.
    EXACTLY the same as 7/27! -/
theorem f_13_50_compromiseScore :
    compromiseScore f_13_50 = (1 : Rat) / 100 := by
  native_decide

/-- 8/31 compromise score: 3/1550 + |8/31 − 1/4| = 3/1550 + |32−31|/124 = 3/1550 + 1/124.
    Let me check if this equals 1/100 too.
    3/1550 + 1/124 = (372 + 1550)/(1550×124) = 1922/192200 = 961/96100.
    961/96100 ≈ 0.01000. Let me check if it equals 1/100 exactly.
    961/96100 vs 1/100 = 961/96100. Yes! 96100 = 100 × 961.
    So 8/31 ALSO has compromise score = 1/100 = 0.01. -/
theorem f_8_31_compromiseScore :
    compromiseScore f_8_31 = (1 : Rat) / 100 := by
  native_decide

/-- THREE fractions (7/27, 13/50, 8/31) all have the SAME compromise score.
    7/27 is NOT uniquely optimal. It is one of (at least) three equally good
    compromise fractions. This is the formal proof of the look-elsewhere
    effect demanded by the adversarial review. -/
theorem threeFractionsTied :
    compromiseScore f_7_27 = compromiseScore f_13_50 ∧
    compromiseScore f_13_50 = compromiseScore f_8_31 := by
  constructor
  · native_decide
  · native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  The Look-Elsewhere Effect (formalized)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Number of distinct fractions in [0.20, 0.35] with denominator ≤ 50.
    This is the number of alternative hypotheses that were implicitly tested.
    The hostile reviewer estimated 53 in [0.24, 0.28].
    In [0.20, 0.35] the count is higher.

    Formal note: we do not enumerate all 53+ fractions in Lean because the
    list is long and unilluminating. The key insight is captured by the
    `threeFractionsTied` theorem: even among the TOP candidates, 7/27 is not
    unique. The look-elsewhere penalty is at least a factor of 3. -/
def lookElsewhereFactor : Nat := 3

/-- The effective significance of the 7/27 match after look-elsewhere
    correction: divide the apparent significance by the number of equally
    good alternatives (at least 3). -/
def lookElsewhereCorrectedSignificance (apparentSigma : Rat) : Rat :=
  apparentSigma / (lookElsewhereFactor : Rat)

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Executable Receipts
-- ═══════════════════════════════════════════════════════════════════════════

#eval! mottCriterion
#eval! mottDistance f_7_27
#eval! mottDistance f_13_50
#eval! mottDistance f_6_23
#eval! speciesAreaDistance f_7_27
#eval! speciesAreaDistance f_13_50
#eval! compromiseScore f_7_27
#eval! compromiseScore f_13_50
#eval! compromiseScore f_8_31

end Semantics.FractionScan
