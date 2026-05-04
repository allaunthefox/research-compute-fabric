namespace Semantics.Temporal.RegenerationTrace

/-
  Regeneration Trace
  ------------------
  Scaffold-grade regeneration semantics.

  Purpose:
  - preserve failure information as typed inheritance
  - prevent episode death from becoming an untracked sink
  - keep regeneration logic explicit and replayable
  - remain independent of full learning/mutation policy

  This module is self-contained (no imports) to maintain scaffold isolation.
-/

/-- Fixed-point Q16.16 value stored in UInt32. -/
abbrev Q16_16 := UInt32

def qZero : Q16_16 := 0

def qOfNat (n : Nat) : Q16_16 :=
  UInt32.ofNat (n * 65536)

/-- Temporal operations (trinary clock). -/
inductive TimeOp
  | subtract
  | pause
  | add
deriving Repr, DecidableEq

/-- Why a unit died. -/
inductive DeathReason
  | budgetExhausted
  | timerExceeded
  | both
deriving Repr, DecidableEq

/-- Compact mistake vector inherited by the next generation. -/
structure MistakeVector where
  subtractCount : Nat
  pauseCount    : Nat
  addCount      : Nat
  totalMismatch : Nat
  totalTviCost  : Q16_16
deriving Repr, DecidableEq

/-- Minimal metabolic state (simplified from MetabolicTvi). -/
structure TemporalState where
  tick          : Nat
  predictedTime : Int
  systemTime    : Nat
  budget        : Q16_16
  timer         : Nat
  goalReached   : Bool
deriving Repr, DecidableEq

/-- Minimal metabolic policy. -/
structure MetabolicPolicy where
  resetBudget  : Q16_16
  maxTimer     : Nat
deriving Repr, DecidableEq

/-- One-step TVI sample. -/
structure TviSample where
  totalCost : Q16_16
deriving Repr, DecidableEq

/-- Summary of one completed episode / lifetime. -/
structure EpisodeSummary where
  finalState   : TemporalState
  ops          : List TimeOp
  samples      : List TviSample
  deathReason  : DeathReason
deriving Repr, DecidableEq

namespace EpisodeSummary

/-- Count subtract/pause/add ops in an episode. -/
def opCounts : List TimeOp → Nat × Nat × Nat
| [] => (0, 0, 0)
| op :: ops =>
  let (s, p, a) := opCounts ops
  match op with
  | .subtract => (s + 1, p, a)
  | .pause    => (s, p + 1, a)
  | .add      => (s, p, a + 1)

/-- Time mismatch between predicted and system time. -/
def timingMismatch (s : TemporalState) : Nat :=
  Int.natAbs (s.predictedTime - Int.ofNat s.systemTime)

/-- Total TVI cost over samples. -/
def totalTvi : List TviSample → Q16_16
| [] => qZero
| x :: xs => x.totalCost + totalTvi xs

/-- Build the inherited mistake vector from an episode summary. -/
def toMistakeVector (e : EpisodeSummary) : MistakeVector :=
  let (s, p, a) := opCounts e.ops
  { subtractCount := s
    pauseCount    := p
    addCount      := a
    totalMismatch := timingMismatch e.finalState
    totalTviCost  := totalTvi e.samples }

end EpisodeSummary

/-- Minimal regeneration payload passed to the next generation. -/
structure RegenerationPayload where
  inheritedMistakes : MistakeVector
  parentTick        : Nat
  parentBudget      : Q16_16
  parentTimer       : Nat
deriving Repr, DecidableEq

/-- Determine death reason from the final state and policy. -/
def classifyDeath (p : MetabolicPolicy) (s : TemporalState) : DeathReason :=
  let budgetDead := s.budget ≤ qZero
  let timerDead  := s.timer > p.maxTimer
  match budgetDead, timerDead with
  | true,  false => .budgetExhausted
  | false, true  => .timerExceeded
  | true,  true  => .both
  | false, false => .timerExceeded

/-- Build the regeneration payload from a dead episode. -/
def buildPayload (e : EpisodeSummary) : RegenerationPayload :=
  { inheritedMistakes := e.toMistakeVector
    parentTick        := e.finalState.tick
    parentBudget      := e.finalState.budget
    parentTimer       := e.finalState.timer }

/-- Regenerate a fresh state from policy + inherited payload. -/
def regenerate (p : MetabolicPolicy) (_payload : RegenerationPayload) : TemporalState :=
  { tick          := 0
    predictedTime := 0
    systemTime    := 0
    budget        := p.resetBudget
    timer         := 0
    goalReached   := false }

/-
  Theorems / witnesses
-/

/-- A regenerated state always starts at tick 0. -/
theorem regenerateStartsAtZeroTick
  (p : MetabolicPolicy) (payload : RegenerationPayload) :
  (regenerate p payload).tick = 0 := by
  rfl

/-- A regenerated state always resets its timer. -/
theorem regenerateResetsTimer
  (p : MetabolicPolicy) (payload : RegenerationPayload) :
  (regenerate p payload).timer = 0 := by
  rfl

/-- A regenerated state restores the policy reset budget. -/
theorem regenerateRestoresBudget
  (p : MetabolicPolicy) (payload : RegenerationPayload) :
  (regenerate p payload).budget = p.resetBudget := by
  rfl

/-- Empty op trace yields zero op counts. -/
theorem opCountsNil :
  EpisodeSummary.opCounts [] = (0, 0, 0) := by
  rfl

/-
  Examples
-/

def examplePolicy : MetabolicPolicy :=
  { resetBudget  := qOfNat 20
    maxTimer     := 10 }

def exampleDeadState : TemporalState :=
  { tick          := 12
    predictedTime := 5
    systemTime    := 9
    budget        := qZero
    timer         := 11
    goalReached   := false }

def exampleEpisode : EpisodeSummary :=
  { finalState  := exampleDeadState
    ops         := [TimeOp.add, TimeOp.pause, TimeOp.add, TimeOp.subtract]
    samples     := []
    deathReason := classifyDeath examplePolicy exampleDeadState }

#eval classifyDeath examplePolicy exampleDeadState
#eval exampleEpisode.toMistakeVector
#eval buildPayload exampleEpisode
#eval regenerate examplePolicy (buildPayload exampleEpisode)

end Semantics.Temporal.RegenerationTrace
