import Semantics.Temporal.TemporalVariantIndex

namespace Semantics.Decoherence.HistoryTvi

open Semantics.Temporal.TemporalVariantIndex

/-
  History TVI Adapter
  -------------------
  Maps decoherence/history domain objects into TVI framework.

  Purpose:
  - Demonstrate TVI kernel works for branching histories
  - Define admissibility for history consistency
  - Expose failure axes (timing, rate, pattern, collapse)
-/

/-- A branch in a decoherent history. -/
structure HistoryBranch where
  branchId : Nat
  eventCount : Nat
  meanInterval : Nat
  divergenceFromParent : Nat  -- how much this branch diverged
  coherenceScore : Nat        -- 0 = fully decohered, higher = more coherent
  deriving Repr, DecidableEq

/-- A decoherent history tree. -/
structure DecoherentHistory where
  branches : List HistoryBranch
  parentBranchId : Nat
  splitTime : Nat
  deriving Repr

/-- Map a history branch to a temporal profile for TVI calculation. -/
def branchToProfile (b : HistoryBranch) : TemporalProfile :=
  { eventCount := b.eventCount
    meanGap := b.meanInterval
    patternCount := b.divergenceFromParent
    collapseBudget := b.coherenceScore }

/-- Calculate TVI between two history branches. -/
def tviBetweenBranches (b₁ b₂ : HistoryBranch) : TviVector :=
  fromProfiles (branchToProfile b₁) (branchToProfile b₂)

/-- Calculate total TVI of a branch against its parent history. -/
def tviAgainstParent (branch : HistoryBranch) (history : DecoherentHistory) : TviVector :=
  -- Find parent branch or use empty default
  let parentProfile : TemporalProfile :=
    match history.branches.find? (fun b => b.branchId = history.parentBranchId) with
    | some parent => branchToProfile parent
    | none => { eventCount := 0, meanGap := 0, patternCount := 0, collapseBudget := 0 }
  fromProfiles parentProfile (branchToProfile branch)

/-- Sum TVI across all branches in a history. -/
def totalHistoryTvi (history : DecoherentHistory) : TviVector :=
  let parentProfile : TemporalProfile :=
    match history.branches.find? (fun b => b.branchId = history.parentBranchId) with
    | some parent => branchToProfile parent
    | none => { eventCount := 0, meanGap := 0, patternCount := 0, collapseBudget := 0 }
  
  -- Sum all branch TVIs against parent
  history.branches.foldl (fun acc branch =>
    let branchTvi := fromProfiles parentProfile (branchToProfile branch)
    { timing := qAdd acc.timing branchTvi.timing
      rate := qAdd acc.rate branchTvi.rate
      pattern := qAdd acc.pattern branchTvi.pattern
      collapse := qAdd acc.collapse branchTvi.collapse })
    zero

/-- Admissibility: history is consistent if total TVI stays within policy. -/
def historyAdmissible (policy : TviPolicy) (history : DecoherentHistory) : Prop :=
  admissible policy (totalHistoryTvi history)

/-- Which axis dominates the history divergence? -/
def dominantHistoryAxis (history : DecoherentHistory) : TviAxis :=
  dominantAxis (totalHistoryTvi history)

/-
  Example witnesses
-/

def exampleParentBranch : HistoryBranch :=
  { branchId := 0
    eventCount := 100
    meanInterval := 10
    divergenceFromParent := 0
    coherenceScore := 50 }

def exampleChildBranch1 : HistoryBranch :=
  { branchId := 1
    eventCount := 95
    meanInterval := 11
    divergenceFromParent := 5
    coherenceScore := 30 }

def exampleChildBranch2 : HistoryBranch :=
  { branchId := 2
    eventCount := 110
    meanInterval := 9
    divergenceFromParent := 15
    coherenceScore := 20 }

def exampleHistory : DecoherentHistory :=
  { branches := [exampleParentBranch, exampleChildBranch1, exampleChildBranch2]
    parentBranchId := 0
    splitTime := 50 }

def exampleHistoryPolicy : TviPolicy :=
  { maxTiming := qOfNat 100
    maxRate := qOfNat 50
    maxPattern := qOfNat 100
    maxCollapse := qOfNat 200
    maxTotal := qOfNat 400 }

-- TVI between two specific branches
#eval tviBetweenBranches exampleParentBranch exampleChildBranch1

-- Total TVI for entire history tree
#eval totalHistoryTvi exampleHistory

-- Dominant axis of divergence
#eval dominantHistoryAxis exampleHistory

-- Is the history admissible under policy?
#eval historyAdmissible exampleHistoryPolicy exampleHistory

/-
  Theorems
-/

/-- A branch compared to itself has zero TVI. -/
theorem tviBranch_self (b : HistoryBranch) :
    tviBetweenBranches b b = zero := by
  simp [tviBetweenBranches, branchToProfile, fromProfiles_self]

/-- Empty history has zero TVI. -/
theorem tviEmptyHistory_zero :
    totalHistoryTvi { branches := [], parentBranchId := 0, splitTime := 0 } = zero := by
  rfl

end Semantics.Decoherence.HistoryTvi
