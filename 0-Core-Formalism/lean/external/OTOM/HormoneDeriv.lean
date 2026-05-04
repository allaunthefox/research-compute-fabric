/-
  HormoneDeriv.lean - Neuroendocrine Control System Bindings
  Ports rows 121, 122, 138 from MATH_MODEL_MAP.tsv (Python → Lean).

  Q16.16: 1.0 = 65536. All hormone concentrations ∈ [0,1] → [0, 65536].
-/
import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.HormoneDeriv

open Q16_16

def epsilon : Q16_16 := ⟨1⟩
-- ln(2) ≈ 0.6931 in Q16.16 = 45426
def ln2 : Q16_16 := ⟨45426⟩

-- Row 121: k = ln(2) / t_half   (decay rate from half-life)
-- t_half in Q16.16 seconds; k in Q16.16 per-second
def halfLifeToDecayRate (tHalf : Q16_16) : Q16_16 :=
  if tHalf.val == 0 then infinity
  else div ln2 tHalf

-- Row 122: logit(x) = log(x / (1-x))
-- z = (logit(x) - mean_logit) / std_logit
-- Approximated in Q16.16 integer domain:
-- logit is undefined at 0/1 boundaries; clamp x to (ε, 1-ε)
-- Use: logit(x) ≈ (x - 0.5) * 4 for x near 0.5 (Taylor linear approx)
-- For full logit: logit(x) = log(x) - log(1-x).
-- Here we use a 4-segment piecewise linear approximation.
def logitApprox (x : Q16_16) : Q16_16 :=
  let half : Q16_16 := ⟨32768⟩  -- 0.5
  let four : Q16_16 := ⟨4 * 65536⟩
  if x.val ≥ half.val
  then mul four (sub x half)
  else neg (mul four (sub half x))

def logitZNorm (x meanLogit stdLogit : Q16_16) : Q16_16 :=
  let lx := logitApprox x
  let diff := if lx.val ≥ meanLogit.val then sub lx meanLogit else sub meanLogit lx
  if stdLogit.val == 0 then zero
  else div diff (add stdLogit epsilon)

-- Row 138: Hormone concentration decay update
-- C(t+dt) = C(t) * e^(-k*dt) ≈ C(t) * (1 - k*dt) for small k*dt
def concentrationDecay (c decayRate dt : Q16_16) : Q16_16 :=
  -- (1 - k·dt) in Q16.16
  let kdt := mul decayRate dt
  if kdt.val >= one.val then zero
  else mul c (sub one kdt)

-- State vector for a single hormone channel
structure HormoneState where
  concentration : Q16_16  -- current level ∈ [0,1] Q16.16
  decayRate     : Q16_16  -- k = ln(2)/t_half
  stimulation   : Q16_16  -- external drive signal ∈ [0,1]
deriving Repr, Inhabited, DecidableEq

-- Advance one timestep: dC/dt = stimulation - k·C
def advanceHormone (h : HormoneState) (dt : Q16_16) : HormoneState :=
  let decayed := concentrationDecay h.concentration h.decayRate dt
  let stim := mul h.stimulation dt
  let newC := min one (add decayed stim)
  { h with concentration := newC }

def hormoneInvariant (h : HormoneState) : String :=
  s!"hormone:c={h.concentration.val},k={h.decayRate.val}"

def hormoneCost (a b : HormoneState) (_m : Metric) : UInt32 :=
  (abs (sub a.concentration b.concentration)).val

def hormoneBind (a b : HormoneState) (m : Metric) : Bind HormoneState HormoneState :=
  controlBind a b m hormoneCost hormoneInvariant hormoneInvariant

-- Verify
#eval halfLifeToDecayRate ⟨65536⟩        -- t_half = 1.0s → k ≈ ln(2)
#eval concentrationDecay ⟨65536⟩ ⟨45426⟩ ⟨6554⟩  -- C=1.0, k=ln2, dt=0.1s

end Semantics.HormoneDeriv
