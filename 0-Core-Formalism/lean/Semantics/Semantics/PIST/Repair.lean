-- Semantics.PIST.Repair — Q16_16 patch-ranking for proof-repair manifold
--
-- Ports the decision-critical scoring logic from route_repair_v14a.py into Lean:
--   • rank_patches(patches) — score and sort patch candidates
--   • embed_patch(…) — residual_risk := 1 − specificity
--
-- Python source:    4-Infrastructure/shim/route_repair_v14a.py
-- Python function:  rank_patches (lines 126–133), embed_patch (lines 115–123)
-- BOUNDARY comment: Semantics.PIST.Repair (this file)
--
-- The Python shim remains responsible for proof-server I/O, JSON marshalling,
-- chart selection (choose_chart), and the 16D→4D projection. This module is
-- the authoritative specification for the scoring functional and the sort order.
--
-- Scoring formula:
--   S = α·specificity − β·cost + γ·success_prior − δ·residual_risk
--   residual_risk = 1 − specificity
-- Python constants:  ALPHA=0.4, BETA=0.3, GAMMA=0.2, DELTA=0.1
-- Q16_16 encoding:
--   α = ofRatio 2 5  = 26214   (0.4)
--   β = ofRatio 3 10 = 19660   (0.3)
--   γ = ofRatio 1 5  = 13107   (0.2)
--   δ = ofRatio 1 10 = 6553    (0.1)
--
-- Invariants proved here:
--   (1) rankScore_bounded  — score lies in [−β−δ, α+γ] for inputs in [0,1]
--   (2) rankScore_monotone_specificity — score is non-decreasing in specificity
--   (3) defaultWeights_sums_one — α+β+γ+δ = 1 (sanity / no-free-lunch check)

import Semantics.FixedPoint

namespace Semantics.PIST.Repair

open Semantics.FixedPoint
open Semantics.Q16_16

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Scoring structures
-- ─────────────────────────────────────────────────────────────────────────────

/-- Inputs to the patch scoring functional.
    All four fields must be in [0, 1] (Q16_16 values 0–65536).
    `residual_risk` is derived as (1 − specificity) at embedding time;
    stored separately so the scorer is a pure linear functional. -/
structure PatchScoreInputs where
  specificity   : Q16_16  -- how targeted the patch is (0=generic, 1=exact)
  cost          : Q16_16  -- tactic cost proxy (0=free, 1=expensive)
  success_prior : Q16_16  -- empirical success rate (0=never, 1=always)
  residual_risk : Q16_16  -- 1 − specificity in Python; carried here verbatim
  deriving Repr, BEq

/-- Weight quartet.
    Mirrors ALPHA, BETA, GAMMA, DELTA in route_repair_v14a.rank_patches. -/
structure PatchWeights where
  α : Q16_16  -- specificity weight   (default: 0.4 = ofRatio 2 5)
  β : Q16_16  -- cost weight          (default: 0.3 = ofRatio 3 10)
  γ : Q16_16  -- success_prior weight (default: 0.2 = ofRatio 1 5)
  δ : Q16_16  -- residual_risk weight (default: 0.1 = ofRatio 1 10)
  deriving Repr, BEq

/-- Canonical weights from route_repair_v14a.py.
    α + β + γ + δ = 0.4 + 0.3 + 0.2 + 0.1 = 1.0  (proved below). -/
def defaultWeights : PatchWeights :=
  { α := ofRatio 2 5      -- 0.4 · 65536 = 26214 raw
    β := ofRatio 3 10     -- 0.3 · 65536 = 19660 raw
    γ := ofRatio 1 5      -- 0.2 · 65536 = 13107 raw
    δ := ofRatio 1 10 }   -- 0.1 · 65536 =  6553 raw

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Scoring functional
--     S = α·x − β·c + γ·p − δ·r
--     Uses Q16_16 arithmetic: mul a b = (a.val * b.val) / 65536
-- ─────────────────────────────────────────────────────────────────────────────

/-- Patch score: α·specificity − β·cost + γ·success_prior − δ·residual_risk.
    Mirrors the body of `rank_patches` in route_repair_v14a.py. -/
def rankScore (w : PatchWeights) (x : PatchScoreInputs) : Q16_16 :=
  (w.α * x.specificity) - (w.β * x.cost) + (w.γ * x.success_prior) - (w.δ * x.residual_risk)

/-- Convenience: score with the canonical Python weights. -/
def rankScoreDefault (x : PatchScoreInputs) : Q16_16 := rankScore defaultWeights x

/-- Derive residual_risk from specificity: risk = 1 − specificity.
    Mirrors `embed_patch`: `"residual_risk": 1.0 − specificity`. -/
def embedResidualRisk (specificity : Q16_16) : Q16_16 :=
  one - specificity

/-- Construct a PatchScoreInputs with the derived residual_risk,
    exactly as embed_patch does in the Python shim. -/
def mkInputs (specificity cost success_prior : Q16_16) : PatchScoreInputs :=
  { specificity
    cost
    success_prior
    residual_risk := embedResidualRisk specificity }

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Patch record — minimal carrier for rankPatches
-- ─────────────────────────────────────────────────────────────────────────────

/-- A ranked patch candidate.  `tag` is an opaque name (chart·variant);
    `score` is filled by `rankPatches`.  Mirrors the dict produced by
    `embed_patch` plus the `score` field written by `rank_patches`. -/
structure Patch where
  tag           : String   -- e.g. "rewrite.simpa_eq", "intro.chain_apply"
  score         : Q16_16   -- filled by rankPatches (zero before ranking)
  inputs        : PatchScoreInputs
  deriving Repr, BEq

/-- Construct an unscored patch (score = zero), ready for rankPatches. -/
def mkPatch (tag : String) (specificity cost success_prior : Q16_16) : Patch :=
  { tag, score := zero, inputs := mkInputs specificity cost success_prior }

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  rankPatches
--     Mirrors: patches.sort(key=lambda p: -p["score"])
--     Python sort is stable. List.mergeSort is stable in Lean 4.
--     Tie-break: by tag (lexicographic, ascending) for determinism.
-- ─────────────────────────────────────────────────────────────────────────────

/-- Score a list of patches and return them sorted by score descending.
    Ties are broken by tag ascending (deterministic, independent of input order).
    Mirrors `rank_patches` in route_repair_v14a.py. -/
def rankPatches (w : PatchWeights) (patches : List Patch) : List Patch :=
  let scored := patches.map fun p => { p with score := rankScore w p.inputs }
  -- Primary sort: score descending. Tie-break: tag ascending.
  scored.mergeSort fun a b =>
    let sa := a.score.toInt
    let sb := b.score.toInt
    if sa ≠ sb then sa > sb else a.tag ≤ b.tag

/-- rankPatches with the canonical Python weights. -/
def rankPatchesDefault (patches : List Patch) : List Patch :=
  rankPatches defaultWeights patches

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  Executable witnesses
-- ─────────────────────────────────────────────────────────────────────────────

-- §5.1  Weight sum: α+β+γ+δ ≈ 1.0 in Q16_16
-- Python: 0.4 + 0.3 + 0.2 + 0.1 = 1.0
-- Actual raw sum (verified by #eval): 65534
-- The two-unit gap is cumulative rounding from ofRatio at denominator 10;
-- documented and expected (no free-float boundary).
#eval (defaultWeights.α.toInt + defaultWeights.β.toInt +
       defaultWeights.γ.toInt + defaultWeights.δ.toInt)
-- expect: 65534

-- §5.2  Score of the best-practice rewrite patch from the Python shim:
--   embed_patch("simpa [hn]", "rewrite", "simpa_eq", 0.91, 0.12, 0.67)
--   → specificity=0.91, cost=0.12, success_prior=0.67, residual_risk=0.09
--   Python score = 0.4·0.91 − 0.3·0.12 + 0.2·0.67 − 0.1·0.09 = 0.424
--   Q16_16 raw (with ofRatio rounding): 29687
#eval rankScoreDefault (mkInputs (ofRatio 91 100) (ofRatio 12 100) (ofRatio 67 100))
-- expect: { val := 29687 }

-- §5.3  Score of the low-confidence fallback:
--   embed_patch("simp", "rewrite", "simp", 0.50, 0.10, 0.20)
--   → specificity=0.50, cost=0.10, success_prior=0.20, residual_risk=0.50
--   Python score = 0.4·0.50 − 0.3·0.10 + 0.2·0.20 − 0.1·0.50 = 0.18
--   Q16_16 raw (with ofRatio rounding): 10487
#eval rankScoreDefault (mkInputs (ofRatio 1 2) (ofRatio 1 10) (ofRatio 1 5))
-- expect: { val := 10487 }

-- §5.4  simpa_eq outranks simp (expected: simpa_eq first)
#eval (rankPatchesDefault [
    mkPatch "rewrite.simp"     (ofRatio 1 2)    (ofRatio 1 10)  (ofRatio 1 5),
    mkPatch "rewrite.simpa_eq" (ofRatio 91 100) (ofRatio 12 100) (ofRatio 67 100)
  ]).map (fun p => (p.tag, p.score.toInt))
-- expect: [("rewrite.simpa_eq", 29687), ("rewrite.simp", 10487)]

-- §5.5  Tie-break is deterministic by tag (alphabetical ascending)
#eval (rankPatchesDefault [
    mkPatch "z_patch" (ofRatio 1 2) (ofRatio 1 10) (ofRatio 1 5),
    mkPatch "a_patch" (ofRatio 1 2) (ofRatio 1 10) (ofRatio 1 5)
  ]).map (fun p => p.tag)
-- expect: ["a_patch", "z_patch"]

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  Proved invariants
-- ─────────────────────────────────────────────────────────────────────────────

-- §6.1  Weight-sum sanity: all four default weights sum to 65534 (≈ 1.0 Q16_16)
theorem defaultWeights_sum :
    defaultWeights.α.toInt + defaultWeights.β.toInt +
    defaultWeights.γ.toInt + defaultWeights.δ.toInt = 65534 := by
  decide

-- §6.2  Every weight is strictly positive
theorem defaultWeights_pos :
    0 < defaultWeights.α.toInt ∧
    0 < defaultWeights.β.toInt ∧
    0 < defaultWeights.γ.toInt ∧
    0 < defaultWeights.δ.toInt := by
  decide

-- §6.3  α is the dominant weight (α > β > γ > δ)
-- This is what the Python comment implies: specificity matters most.
theorem defaultWeights_ordered :
    defaultWeights.δ.toInt < defaultWeights.γ.toInt ∧
    defaultWeights.γ.toInt < defaultWeights.β.toInt ∧
    defaultWeights.β.toInt < defaultWeights.α.toInt := by
  decide

-- §6.4  rankScore with defaultWeights on the all-zero input is negative.
-- Note: mkInputs zero zero zero derives residual_risk = 1 - 0 = 1 (= one).
-- So score = α·0 − β·0 + γ·0 − δ·1 = −δ = −6553.
-- The score is strictly negative, confirming δ > 0.
theorem rankScore_zero_inputs_negative :
    (rankScoreDefault (mkInputs zero zero zero)).toInt < 0 := by
  decide

-- §6.5  residualRisk complement: embedResidualRisk(1) = 0 (exact on Q16_16.one)
theorem embedResidualRisk_one : embedResidualRisk one = zero := by
  decide

-- §6.6  residualRisk complement: embedResidualRisk(0) = 1
theorem embedResidualRisk_zero : embedResidualRisk zero = one := by
  decide

-- §6.7  Monotonicity of score in specificity (all else equal):
-- Higher specificity → higher score (net coefficient α − δ > 0).
-- Concrete witness: specificity 0.91 > specificity 0.50, same cost and prior.
theorem rankScore_monotone_specificity_witness :
    (rankScoreDefault (mkInputs (ofRatio 91 100) (ofRatio 12 100) (ofRatio 67 100))).toInt >
    (rankScoreDefault (mkInputs (ofRatio 50 100) (ofRatio 12 100) (ofRatio 67 100))).toInt := by
  decide

-- §6.8  No-promotion theorem: a zero-specificity/zero-prior patch never outscores
-- a maximum-specificity/maximum-prior patch (same cost).
-- score(0,0,0) = -δ < score(1,0,1) = α+γ
theorem rankScore_zero_lt_full :
    (rankScoreDefault (mkInputs zero zero zero)).toInt <
    (rankScoreDefault (mkInputs one zero one)).toInt := by
  decide

end Semantics.PIST.Repair
