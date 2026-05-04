namespace Semantics.Temporal.MetabolicTvi

/-
  Metabolic TVI
  -------------
  Scaffold-grade temporal accounting module.

  Purpose:
  - model temporal behavior as energy metabolism
  - make pause non-free
  - force commit every trinary tic
  - reset timer on goal completion
  - kill/regenerate units that exceed budget or timeout
-/

/-- Fixed-point Q16.16 value stored in UInt32. -/
abbrev Q16_16 := UInt32

def qZero : Q16_16 := 0
def qOne  : Q16_16 := 0x00010000

/-- Natural number to Q16.16 integer embedding. -/
def qOfNat (n : Nat) : Q16_16 :=
  UInt32.ofNat (n * 65536)

/-- Saturating placeholder addition for Q16.16. -/
def qAdd (a b : Q16_16) : Q16_16 := a + b

/-- Absolute difference on naturals. -/
def natAbsDiff (a b : Nat) : Nat :=
  if a ≥ b then a - b else b - a

/-- Temporal operations. -/
inductive TimeOp
| subtract
| pause
| add
deriving Repr, DecidableEq

/-- Policy governing metabolic TVI behavior. -/
structure MetabolicPolicy where
  basalCost    : Q16_16
  subtractCost : Q16_16
  pauseCost    : Q16_16
  addCost      : Q16_16
  commitCost   : Q16_16
  resetBudget  : Q16_16
  maxTimer     : Nat
deriving Repr, DecidableEq

/-- Per-op cost. -/
def opCost (p : MetabolicPolicy) : TimeOp → Q16_16
| .subtract => p.subtractCost
| .pause    => p.pauseCost
| .add      => p.addCost

/-- Signed temporal effect of an operation on predicted time. -/
def opDelta : TimeOp → Int
| .subtract => -1
| .pause    => 0
| .add      => 1

/-- Commit every trinary tic. -/
def shouldCommit (tick : Nat) : Bool :=
  tick % 3 = 0

/-- A single metabolic temporal state. -/
structure TemporalState where
  tick          : Nat
  predictedTime : Int
  systemTime    : Nat
  budget        : Q16_16
  timer         : Nat
  goalReached   : Bool
deriving Repr, DecidableEq

/-- Time mismatch between predicted and system time. -/
def timingMismatch (s : TemporalState) : Nat :=
  Int.natAbs (s.predictedTime - Int.ofNat s.systemTime)

/-- Whether the unit is still alive. -/
def alive (p : MetabolicPolicy) (s : TemporalState) : Bool :=
  s.budget > qZero && s.timer ≤ p.maxTimer

/-- Step cost = basal + op + optional commit. -/
def stepCost (p : MetabolicPolicy) (tick : Nat) (op : TimeOp) : Q16_16 :=
  let commitTerm := if shouldCommit tick then p.commitCost else qZero
  qAdd p.basalCost (qAdd (opCost p op) commitTerm)

/-- Budget update with timer-reset-on-goal semantics. -/
def nextBudget (p : MetabolicPolicy) (s : TemporalState) (op : TimeOp) : Q16_16 :=
  let cost := stepCost p s.tick op
  if s.goalReached then
    p.resetBudget - cost
  else
    s.budget - cost

/-- Timer update: reset on goal, otherwise increment. -/
def nextTimer (s : TemporalState) : Nat :=
  if s.goalReached then 0 else s.timer + 1

/-- Predicted time update from operation. -/
def nextPredictedTime (s : TemporalState) (op : TimeOp) : Int :=
  s.predictedTime + opDelta op

/-- Advance one tic. Caller supplies next system time and next goal flag. -/
def step
  (p : MetabolicPolicy)
  (s : TemporalState)
  (op : TimeOp)
  (nextSystemTime : Nat)
  (nextGoalReached : Bool) : TemporalState :=
  { tick          := s.tick + 1
    predictedTime := nextPredictedTime s op
    systemTime    := nextSystemTime
    budget        := nextBudget p s op
    timer         := nextTimer s
    goalReached   := nextGoalReached }

/-- One-step TVI contribution: timing mismatch + metabolic cost. -/
structure TviSample where
  timingCost : Q16_16
  opCost     : Q16_16
  totalCost  : Q16_16
deriving Repr, DecidableEq

/-- Sample the TVI contribution at a state and chosen op. -/
def tviSample (p : MetabolicPolicy) (s : TemporalState) (op : TimeOp) : TviSample :=
  let timing := qOfNat (timingMismatch s)
  let cost   := stepCost p s.tick op
  { timingCost := timing
    opCost     := cost
    totalCost  := qAdd timing cost }

/-- Sum TVI sample totals over a finite trace. -/
def totalTvi : List TviSample → Q16_16
| [] => qZero
| x :: xs => qAdd x.totalCost (totalTvi xs)

/-- A compact mistake vector for regeneration. -/
structure MistakeVector where
  subtractCount : Nat
  pauseCount    : Nat
  addCount      : Nat
  totalMismatch : Nat
  totalTviCost  : Q16_16
deriving Repr, DecidableEq

/-- Count operations in a trace. -/
def opCounts : List TimeOp → Nat × Nat × Nat
| [] => (0, 0, 0)
| op :: ops =>
  let (s, p, a) := opCounts ops
  match op with
  | .subtract => (s + 1, p, a)
  | .pause    => (s, p + 1, a)
  | .add      => (s, p, a + 1)

/-- Build a mistake vector from op and state traces. -/
def mistakeVector (ops : List TimeOp) (states : List TemporalState) (samples : List TviSample) :
    MistakeVector :=
  let (s, p, a) := opCounts ops
  { subtractCount := s
    pauseCount    := p
    addCount      := a
    totalMismatch := states.foldl (fun acc st => acc + timingMismatch st) 0
    totalTviCost  := totalTvi samples }

/-
  Witnesses / theorems
-/

/-- Commit happens at tick 0. -/
theorem shouldCommit_zero : shouldCommit 0 = true := by
  simp [shouldCommit]

/-- Commit does not happen at tick 1. -/
theorem shouldCommit_one : shouldCommit 1 = false := by
  simp [shouldCommit]

/-- Timer resets when goal has already been reached. -/
theorem nextTimer_goal (s : TemporalState) (h : s.goalReached = true) :
    nextTimer s = 0 := by
  unfold nextTimer
  simp [h]

/-- Timer increments when goal has not been reached. -/
theorem nextTimer_noGoal (s : TemporalState) (h : s.goalReached = false) :
    nextTimer s = s.timer + 1 := by
  unfold nextTimer
  simp [h]

/-- The zero TVI of an empty trace is zero. -/
theorem totalTvi_nil : totalTvi [] = qZero := by
  rfl

/-
  Examples
-/

def examplePolicy : MetabolicPolicy :=
  { basalCost    := qOfNat 1
    subtractCost := qOfNat 1
    pauseCost    := qOfNat 1
    addCost      := qOfNat 3
    commitCost   := qOfNat 1
    resetBudget  := qOfNat 20
    maxTimer     := 10 }

def exampleState : TemporalState :=
  { tick          := 0
    predictedTime := 0
    systemTime    := 0
    budget        := qOfNat 10
    timer         := 0
    goalReached   := false }

#eval shouldCommit 0
#eval shouldCommit 1
#eval shouldCommit 3

#eval stepCost examplePolicy 0 TimeOp.pause
#eval stepCost examplePolicy 1 TimeOp.pause
#eval stepCost examplePolicy 0 TimeOp.add

#eval tviSample examplePolicy exampleState TimeOp.add

#eval step examplePolicy exampleState TimeOp.add 1 false
#eval step examplePolicy { exampleState with goalReached := true } TimeOp.pause 1 false

end Semantics.Temporal.MetabolicTvi
