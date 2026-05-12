import Mathlib.Data.Nat.Choose.Basic

namespace Semantics.BernoulliOccupancyShockbow

/-!
Bernoulli occupancy and Shockbow gate for static decompressor replay.

This module formalizes the small invariant surface from
`BERNOULLI_OCCUPANCY_RECEIPT_MATH.md`.

Claim boundary: this is integer receipt math for admission gates. It is not a
compression-ratio claim and not a physical shockwave simulation.
-/

/-- Gate decision for a candidate survivor map. -/
inductive GateDecision where
  | admit
  | hold
  | quarantine
deriving DecidableEq, Repr

/-- Optional 2D shockbow angle gate. All angles are integer degrees. -/
structure ShockbowGate where
  enabled : Bool
  thetaIn : Nat
  thetaBow : Nat
  admittedBand : Nat
deriving DecidableEq, Repr

/-- Static decompressor admission input. -/
structure OccupancyGateInput where
  nSlots : Nat
  kCandidates : Nat
  threshold : Nat
  replayCapacity : Nat
  residualSize : Nat
  residualBudget : Nat
  proofCloses : Bool
  priorsDeclared : Bool
  shockbow : ShockbowGate
deriving DecidableEq, Repr

/-- Absolute difference on natural-number angle bins. -/
def absDiff (a b : Nat) : Nat :=
  if a ≤ b then b - a else a - b

/-- Shockbow gate passes if disabled, or if the angular delta fits the band. -/
def shockbowPass (g : ShockbowGate) : Bool :=
  if g.enabled then
    absDiff g.thetaIn g.thetaBow ≤ g.admittedBand
  else
    true

/-- Denominator for the uniform expected exact/at-least occupancy terms. -/
def occupancyDenominator (n k : Nat) : Nat :=
  n ^ (k - 1)

/--
Numerator for expected number of buckets with exactly `s` hits under uniform
slot probabilities:

`E[X_s] = choose(k,s) * (n-1)^(k-s) / n^(k-1)`
-/
def expectedExactNumerator (n k s : Nat) : Nat :=
  if n = 0 ∨ s > k then
    0
  else
    Nat.choose k s * (n - 1) ^ (k - s)

/-- Numerator for expected number of buckets with at least `s` hits. -/
def expectedAtLeastNumerator (n k s : Nat) : Nat :=
  if n = 0 ∨ s > k then
    0
  else
    (List.range (k - s + 1)).foldl
      (fun acc offset =>
        let j := s + offset
        acc + Nat.choose k j * (n - 1) ^ (k - j))
      0

/-- The declared occupancy shape is meaningful for receipt gating. -/
def shapeValid (i : OccupancyGateInput) : Bool :=
  i.nSlots > 0 && i.threshold > 0 && i.threshold ≤ i.kCandidates

/-- Expected survivor buckets fit the static replay capacity. -/
def expectedFitsReplay (i : OccupancyGateInput) : Bool :=
  expectedAtLeastNumerator i.nSlots i.kCandidates i.threshold ≤
    i.replayCapacity * occupancyDenominator i.nSlots i.kCandidates

/-- Residual lane fits the declared decompressor budget. -/
def residualFits (i : OccupancyGateInput) : Bool :=
  i.residualSize ≤ i.residualBudget

/--
Static decompressor gate.

The decompressor may replay only an admitted CMR survivor map. It does not
estimate probabilities at runtime; it verifies the committed integer gate
surface.
-/
def decideGate (i : OccupancyGateInput) : GateDecision :=
  if !shapeValid i then
    .quarantine
  else if !i.proofCloses then
    .quarantine
  else if !residualFits i then
    .quarantine
  else if !shockbowPass i.shockbow then
    .quarantine
  else if !i.priorsDeclared then
    .hold
  else if expectedFitsReplay i then
    .admit
  else
    .quarantine

/-- Invariant for admission: admitted maps are replay-bounded and receipted. -/
def admittedInvariant (i : OccupancyGateInput) : Bool :=
  decideGate i = .admit →
    shapeValid i = true ∧
    i.proofCloses = true ∧
    residualFits i = true ∧
    shockbowPass i.shockbow = true ∧
    i.priorsDeclared = true ∧
    expectedFitsReplay i = true

def noShockbow : ShockbowGate :=
  { enabled := false, thetaIn := 0, thetaBow := 0, admittedBand := 0 }

def passingShockbow : ShockbowGate :=
  { enabled := true, thetaIn := 23, thetaBow := 26, admittedBand := 4 }

def rejectingShockbow : ShockbowGate :=
  { enabled := true, thetaIn := 10, thetaBow := 26, admittedBand := 4 }

/-- Birthday-source-inspired fixture: expected triple buckets fit one replay slot. -/
def birthdayTripleFixture : OccupancyGateInput :=
  { nSlots := 365,
    kCandidates := 60,
    threshold := 3,
    replayCapacity := 1,
    residualSize := 2,
    residualBudget := 4,
    proofCloses := true,
    priorsDeclared := true,
    shockbow := passingShockbow }

def missingPriorFixture : OccupancyGateInput :=
  { birthdayTripleFixture with priorsDeclared := false }

def overCapacityFixture : OccupancyGateInput :=
  { birthdayTripleFixture with replayCapacity := 0 }

def missingProofFixture : OccupancyGateInput :=
  { birthdayTripleFixture with proofCloses := false }

def shockbowRejectFixture : OccupancyGateInput :=
  { birthdayTripleFixture with shockbow := rejectingShockbow }

theorem birthdayTripleAdmits :
    decideGate birthdayTripleFixture = .admit := by
  native_decide

theorem missingPriorHolds :
    decideGate missingPriorFixture = .hold := by
  native_decide

theorem overCapacityQuarantines :
    decideGate overCapacityFixture = .quarantine := by
  native_decide

theorem missingProofQuarantines :
    decideGate missingProofFixture = .quarantine := by
  native_decide

theorem shockbowRejectQuarantines :
    decideGate shockbowRejectFixture = .quarantine := by
  native_decide

theorem birthdayTripleInvariant :
    admittedInvariant birthdayTripleFixture := by
  native_decide

#eval decideGate birthdayTripleFixture
#eval expectedAtLeastNumerator 365 60 3
#eval occupancyDenominator 365 60
#eval shockbowPass passingShockbow

end Semantics.BernoulliOccupancyShockbow
