/-
  CognitiveLoad.lean - Formal Cognitive Load Theory (CLT) Bindings
  Ports rows 2-11 from MATH_MODEL_MAP.tsv (Python → Lean).

  All values are Q16.16 fixed-point. 1.0 = 0x00010000 = 65536.
  ε = 1 (smallest nonzero Q16.16 unit) to prevent division by zero.
-/
import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.CognitiveLoad

open Q16_16

-- ε = 1 LSB in Q16.16 (prevents division by zero)
def epsilon : Q16_16 := ⟨1⟩

structure LoadVector where
  intrinsic  : Q16_16  -- L_I: germane schema processing
  extraneous : Q16_16  -- L_E: irrelevant processing
  germane    : Q16_16  -- L_G: schema construction effort
  routing    : Q16_16  -- L_R: inter-node routing overhead
  memory     : Q16_16  -- L_M: working memory pressure
deriving Repr, Inhabited, DecidableEq

-- Row 2: L_I(x) — intrinsic load (direct field access)
def intrinsicLoad (v : LoadVector) : Q16_16 := v.intrinsic

-- Row 3: L_E(x) — extraneous load
def extraneousLoad (v : LoadVector) : Q16_16 := v.extraneous

-- Row 4: L_G(x) — germane load
def germaneLoad (v : LoadVector) : Q16_16 := v.germane

-- Row 5: L_R(x) — routing load
def routingLoad (v : LoadVector) : Q16_16 := v.routing

-- Row 6: L_M(x) — memory load
def memoryLoad (v : LoadVector) : Q16_16 := v.memory

-- Row 7: L_total(x) = L_I + L_E + L_G + L_R + L_M
def totalLoad (v : LoadVector) : Q16_16 :=
  add (add (add (add v.intrinsic v.extraneous) v.germane) v.routing) v.memory

-- Row 8: η(x) = L_I / (L_total + ε)
-- Cognitive efficiency: ratio of useful intrinsic load to total
def cognitiveEfficiency (v : LoadVector) : Q16_16 :=
  let total := add (totalLoad v) epsilon
  div v.intrinsic total

-- Row 9: L_ρ(x) = L_total · (1 + ρ / ρ_max)
-- Regret-adjusted load where ρ is BPB regret signal
def regretAdjustedLoad (v : LoadVector) (regret regretMax : Q16_16) : Q16_16 :=
  let regretRatio := div regret (add regretMax epsilon)
  let factor := add one regretRatio
  mul (totalLoad v) factor

-- Row 10: L(x|B) = L_I + L_E + L_R (basin-specific routing replaces germane)
def basinConditionalLoad (lI lE lR_basin : Q16_16) : Q16_16 :=
  add (add lI lE) lR_basin

-- Row 11: P_w(x_i | x_{<i}) = Σ w_j · P_{m_j}(x_i | x_{<i})
-- MoE predictor distribution: weighted mixture
-- weights and predictions are parallel arrays of Q16.16 values
-- Result is Q16.16-normalized weighted sum
def moePredictorDistribution (weights predictions : Array Q16_16) : Q16_16 :=
  if weights.size == 0 || weights.size != predictions.size then zero
  else
    let weightedSum := Array.foldl (fun acc i =>
      if i < predictions.size then
        add acc (mul weights[i]! predictions[i]!)
      else acc
    ) zero (Array.range weights.size)
    let totalWeight := Array.foldl add zero weights
    if totalWeight.val == 0 then zero else div weightedSum totalWeight

-- Invariant string for bind witnesses
def loadInvariant (v : LoadVector) : String :=
  s!"load:I={v.intrinsic.val},E={v.extraneous.val},G={v.germane.val}"

-- Bind: computes informational cost between two load states
def loadDeltaCost (a b : LoadVector) (_m : Metric) : Q16_16 :=
  let da := totalLoad a
  let db := totalLoad b
  Q16_16.ofNat (abs (sub da db)).val.toNat

def cognitiveLoadBind (a b : LoadVector) (m : Metric) : Bind LoadVector LoadVector :=
  informationalBind a b m loadDeltaCost loadInvariant loadInvariant

-- Verify
#eval totalLoad { intrinsic := ⟨32768⟩, extraneous := ⟨16384⟩, germane := ⟨8192⟩, routing := ⟨4096⟩, memory := ⟨2048⟩ }
#eval cognitiveEfficiency { intrinsic := ⟨32768⟩, extraneous := ⟨16384⟩, germane := ⟨8192⟩, routing := ⟨4096⟩, memory := ⟨2048⟩ }

end Semantics.CognitiveLoad
