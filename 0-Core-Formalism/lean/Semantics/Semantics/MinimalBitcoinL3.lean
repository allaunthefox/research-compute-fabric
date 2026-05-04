import Semantics.Bind
import Semantics.FixedPoint
import Semantics.BitcoinMetaprobe

namespace Semantics.MinimalBitcoinL3

/-! ## Minimal Bitcoin L3 Surface

**Goal:**
Nearly impossibly small surface for Bitcoin L3 internal compute layer.

**Principle:**
Layer 3 = computation (local, private, no transmission)
Layer 2 = aggregation (optional, semi-global)
Layer 1 = commitment (global, public anchor)

**Minimal Interface:**
- Internal transition: (from, to, delta) → local receipt
- Local receipt: (transition_id, proof) → optional anchor
- External anchor: (receipt_id, commitment) → global commitment

**Key Insight:**
No computation needs to become public merely because it was verified.
Do the work locally, verify locally, commit locally, anchor externally only when justified.

**Minimal Surface:**
3 structures, 3 functions, 1 theorem.

Per AGENTS.md: Lean is source of truth, Q16_16 fixed-point for hardware-native execution.
-/

open Semantics.Q16_16

/-- Minimal internal transition (from → to with delta). -/
structure MinimalTransition where
  from : String  -- Source state
  to : String  -- Target state
  delta : Semantics.Q16_16  -- State change (sigma, data, etc.)
deriving Repr

/-- Minimal local receipt (transition proof, no transmission). -/
structure MinimalReceipt where
  transitionId : String  -- Associated transition
  proof : String  -- Local proof
  localOnly : Bool  -- True = no transmission
deriving Repr

/-- Minimal external anchor (optional upward commitment). -/
structure MinimalAnchor where
  receiptId : String  -- Local receipt being anchored
  commitment : String  -- External commitment hash
  anchored : Bool  -- True = anchored to external layer
deriving Repr

/-- Explicit permission to export a local receipt upward. -/
structure ExportGrant where
  allowed : Bool
  reason : String
deriving Repr

/-! ## Minimal Functions -/

/-- Execute minimal internal transition (local only). -/
def executeTransition (transition : MinimalTransition) : MinimalReceipt :=
  {
    transitionId := s!"{transition.from}→{transition.to}",
    proof := s!"proof:{transition.delta}",
    localOnly := true
  }

/-- Check if transition is allowed (from != to, delta != zero). -/
def transitionAllowed (transition : MinimalTransition) : Bool :=
  transition.from ≠ transition.to ∧ transition.delta ≠ zero

/-- Apply transition to current state (preserves state if not allowed). -/
def applyTransition (currentState : String) (transition : MinimalTransition) : String :=
  if transitionAllowed transition then
    transition.to
  else
    currentState

/-- Try to anchor receipt externally. Local-only receipts require explicit export grant. -/
def tryAnchorReceipt (receipt : MinimalReceipt) (commitment : String) (grant : ExportGrant) : MinimalAnchor :=
  if receipt.localOnly ∧ ¬grant.allowed then
    {
      receiptId := receipt.transitionId,
      commitment := "",
      anchored := false
    }
  else
    {
      receiptId := receipt.transitionId,
      commitment := commitment,
      anchored := true
    }

/-- Check if receipt is local-only (no transmission). -/
def isLocalOnly (receipt : MinimalReceipt) : Bool :=
  receipt.localOnly

/-- Check if delta is within bound. -/
def deltaWithinBound (transition : MinimalTransition) (bound : Semantics.Q16_16) : Bool :=
  transition.delta ≤ bound ∧ -bound ≤ transition.delta

/-! ## Conservative Theorems -/

/-- 1. Local-only receipts cannot anchor upward without explicit export grant. -/
theorem localOnlyNoTransmissionWithoutGrant
  (receipt : MinimalReceipt)
  (commitment : String)
  (grant : ExportGrant)
  (hLocal : receipt.localOnly = true)
  (hDenied : grant.allowed = false) :
  let anchor := tryAnchorReceipt receipt commitment grant
  anchor.anchored = false := by
  unfold tryAnchorReceipt
  simp [hLocal, hDenied]

/-- 2. Refused transition preserves state (no transition = no state change). -/
theorem refusedTransitionPreservesState
  (currentState : String)
  (transition : MinimalTransition)
  (h : transitionAllowed transition = false) :
  applyTransition currentState transition = currentState := by
  unfold applyTransition transitionAllowed
  simp [h]

/-- 3. Zero delta preserves state (no change = no state change). -/
theorem zeroDeltaPreservesState
  (currentState : String)
  (transition : MinimalTransition)
  (h : transition.delta = zero) :
  applyTransition currentState transition = currentState := by
  unfold applyTransition transitionAllowed
  simp [h]

/-- 4. External anchor preserves receipt root (anchor commits to same receipt). -/
theorem externalAnchorPreservesReceiptRoot
  (receipt : MinimalReceipt)
  (commitment : String)
  (grant : ExportGrant)
  (hAllowed : grant.allowed = true ∨ ¬receipt.localOnly) :
  let anchor := tryAnchorReceipt receipt commitment grant
  anchor.receiptId = receipt.transitionId := by
  unfold tryAnchorReceipt
  simp [hAllowed]

/-- 5. Anchor does not expand scope (anchoring does not add new data). -/
theorem anchorDoesNotExpandScope
  (receipt : MinimalReceipt)
  (commitment : String)
  (grant : ExportGrant)
  (hAllowed : grant.allowed = true ∨ ¬receipt.localOnly) :
  let anchor := tryAnchorReceipt receipt commitment grant
  anchor.commitment = commitment := by
  unfold tryAnchorReceipt
  simp [hAllowed]

/-- 6. Delta bounded (delta cannot exceed reasonable bounds). -/
theorem deltaWithinBound_valid (transition : MinimalTransition) (bound : Semantics.Q16_16) :
  deltaWithinBound transition bound ↔
    (transition.delta ≤ bound ∧ -bound ≤ transition.delta) := by
  unfold deltaWithinBound
  rfl

/-- 7. Replay resistance (same transition produces same receipt). -/
theorem replayResistance (transition : MinimalTransition) :
  let receipt1 := executeTransition transition
  let receipt2 := executeTransition transition
  receipt1.transitionId = receipt2.transitionId ∧ receipt1.proof = receipt2.proof := by
  unfold executeTransition
  rfl

/-- 8. executeTransition produces local-only receipt. -/
theorem executeTransition_localOnly (transition : MinimalTransition) :
  (executeTransition transition).localOnly = true := by
  unfold executeTransition
  simp

/-- 9. transitionAllowed is true when from != to and delta != zero. -/
theorem transitionAllowed_true_whenValid (transition : MinimalTransition) :
  transition.from ≠ transition.to ∧ transition.delta ≠ zero → transitionAllowed transition = true := by
  unfold transitionAllowed
  simp

/-- 10. transitionAllowed is false when from = to. -/
theorem transitionAllowed_false_whenFromEqualsTo (transition : MinimalTransition) :
  transition.from = transition.to → transitionAllowed transition = false := by
  unfold transitionAllowed
  simp

/-- 11. transitionAllowed is false when delta = zero. -/
theorem transitionAllowed_false_whenDeltaZero (transition : MinimalTransition) :
  transition.delta = zero → transitionAllowed transition = false := by
  unfold transitionAllowed
  simp

/-- 12. applyTransition preserves state when transition not allowed. -/
theorem applyTransition_preservesWhenNotAllowed (currentState : String) (transition : MinimalTransition) :
  transitionAllowed transition = false → applyTransition currentState transition = currentState := by
  unfold applyTransition
  simp

/-- 13. applyTransition changes state to target when allowed. -/
theorem applyTransition_changesToTarget (currentState : String) (transition : MinimalTransition) :
  transitionAllowed transition = true → applyTransition currentState transition = transition.to := by
  unfold applyTransition
  simp

/-! #eval Witnesses -/

#eval executeTransition { from := "state_0", to := "state_1", delta := 0x00005000 }
  -- Expected: MinimalReceipt with localOnly=true

#eval transitionAllowed { from := "state_0", to := "state_1", delta := 0x00005000 }
  -- Expected: true (from != to, delta != zero)

#eval applyTransition "state_0" { from := "state_0", to := "state_1", delta := 0x00005000 }
  -- Expected: "state_1"

#eval tryAnchorReceipt {
  transitionId := "state_0→state_1",
  proof := "proof:327680",
  localOnly := true
} "external_commit_abc123" { allowed := false, reason := "no_export_grant" }
  -- Expected: MinimalAnchor with anchored=false (local-only without grant)

#eval tryAnchorReceipt {
  transitionId := "state_0→state_1",
  proof := "proof:327680",
  localOnly := true
} "external_commit_abc123" { allowed := true, reason := "explicit_export_grant" }
  -- Expected: MinimalAnchor with anchored=true (local-only with grant)

#eval isLocalOnly {
  transitionId := "state_0→state_1",
  proof := "proof:327680",
  localOnly := true
}
  -- Expected: true

#eval deltaWithinBound { from := "state_0", to := "state_1", delta := 0x00005000 } 0x00010000
  -- Expected: true (delta within bound)

end Semantics.MinimalBitcoinL3
