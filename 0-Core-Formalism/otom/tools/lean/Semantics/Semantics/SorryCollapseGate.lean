/-
SorryCollapseGate.lean — support-collapse / lattice evacuation gate v0.1

Purpose:
  Formalize the discrete operator recovered from the remembered commercial motif:
    Connect Four board -> all pieces slide off -> "SORRY"

Interpretation:
  A board can contain a locally valid token arrangement only while support
  geometry holds. If support fails, the board state is globally evacuated/reset
  and a SORRY receipt marks invalidation.

Boundary:
  This module does not claim the commercial proves anything. It records a toy
  formal operator for support-predicate failure in a constrained lattice.
-/

import Std

namespace Semantics.SorryCollapseGate

/-- Evidence state for this scaffold. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Support status of the board/container geometry. -/
inductive SupportStatus where
  | valid
  | invalid
  deriving Repr, DecidableEq, Inhabited

/-- Receipt marker emitted by the collapse gate. -/
inductive CollapseReceipt where
  | ok
  | sorry
  deriving Repr, DecidableEq, Inhabited

/-- A token in a constrained columnar lattice. -/
structure Token where
  id : Nat
  column : Nat
  row : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Board state for the toy support-collapse gate. -/
structure BoardState where
  boardId : Nat
  tokens : List Token
  support : SupportStatus
  receipt : CollapseReceipt
  claimState : ClaimState
  deriving Repr, Inhabited

/-- Token count before or after a collapse operation. -/
def tokenCount (b : BoardState) : Nat :=
  b.tokens.length

/-- Evacuate/reset the board and emit a SORRY receipt. -/
def evacuate (b : BoardState) : BoardState :=
  { b with tokens := [], receipt := .sorry }

/-- Preserve the board and emit an OK receipt. -/
def preserve (b : BoardState) : BoardState :=
  { b with receipt := .ok }

/-- Collapse gate: invalid support forces evacuation. -/
def applySorryCollapseGate (b : BoardState) : BoardState :=
  match b.support with
  | .valid => preserve b
  | .invalid => evacuate b

/-- Invalid support predicate. -/
def SupportFailed (b : BoardState) : Prop :=
  b.support = SupportStatus.invalid

/-- Valid support predicate. -/
def SupportHolds (b : BoardState) : Prop :=
  b.support = SupportStatus.valid

/-- Invalid support triggers the SORRY receipt. -/
theorem invalid_support_emits_sorry
    (b : BoardState)
    (h : SupportFailed b) :
    (applySorryCollapseGate b).receipt = CollapseReceipt.sorry := by
  unfold SupportFailed at h
  unfold applySorryCollapseGate
  rw [h]
  unfold evacuate
  rfl

/-- Invalid support evacuates all tokens. -/
theorem invalid_support_evacuates_tokens
    (b : BoardState)
    (h : SupportFailed b) :
    (applySorryCollapseGate b).tokens = [] := by
  unfold SupportFailed at h
  unfold applySorryCollapseGate
  rw [h]
  unfold evacuate
  rfl

/-- Valid support preserves token list. -/
theorem valid_support_preserves_tokens
    (b : BoardState)
    (h : SupportHolds b) :
    (applySorryCollapseGate b).tokens = b.tokens := by
  unfold SupportHolds at h
  unfold applySorryCollapseGate
  rw [h]
  unfold preserve
  rfl

/-- Valid support emits OK receipt. -/
theorem valid_support_emits_ok
    (b : BoardState)
    (h : SupportHolds b) :
    (applySorryCollapseGate b).receipt = CollapseReceipt.ok := by
  unfold SupportHolds at h
  unfold applySorryCollapseGate
  rw [h]
  unfold preserve
  rfl

/-- Example stable board with two tokens. -/
def stableBoard : BoardState :=
  { boardId := 0
    tokens := [ { id := 0, column := 0, row := 0 }, { id := 1, column := 1, row := 0 } ]
    support := .valid
    receipt := .ok
    claimState := .beautifulProvisional }

/-- Example failed board with two tokens. -/
def failedBoard : BoardState :=
  { boardId := 1
    tokens := [ { id := 0, column := 0, row := 0 }, { id := 1, column := 1, row := 0 } ]
    support := .invalid
    receipt := .ok
    claimState := .beautifulProvisional }

/-- Stable board keeps its tokens. -/
theorem stableBoard_preserved :
    (applySorryCollapseGate stableBoard).tokens = stableBoard.tokens := by
  exact valid_support_preserves_tokens stableBoard rfl

/-- Failed board is evacuated. -/
theorem failedBoard_evacuated :
    (applySorryCollapseGate failedBoard).tokens = [] := by
  exact invalid_support_evacuates_tokens failedBoard rfl

/-- Failed board emits SORRY. -/
theorem failedBoard_sorry :
    (applySorryCollapseGate failedBoard).receipt = CollapseReceipt.sorry := by
  exact invalid_support_emits_sorry failedBoard rfl

#eval tokenCount stableBoard -- 2
#eval tokenCount (applySorryCollapseGate stableBoard) -- 2
#eval tokenCount failedBoard -- 2
#eval tokenCount (applySorryCollapseGate failedBoard) -- 0
#eval (applySorryCollapseGate failedBoard).receipt -- sorry

end Semantics.SorryCollapseGate
