/-
ReceiptLedgerPromotionGate.lean — finite receipt-ledger REVIEWED promotion gate v0.1

Purpose:
  Encode the Warden invariant recovered from the Lean failure log:
  a trial cannot be promoted to REVIEWED unless the persistent ledger contains
  a proof receipt for the target.

Boundary:
  This module proves only the finite transition gate. It does not prove the
  external scientific claim, benchmark, metaphor, or PDE model being reviewed.
-/

import Std

namespace Semantics.ReceiptLedgerPromotionGate

/-- Warden status states. -/
inductive WardenStatus where
  | hold
  | candidate
  | reviewed
  | rejected
  deriving Repr, DecidableEq, Inhabited

/-- Receipt kinds. Only `proof` authorizes REVIEWED promotion. -/
inductive ReceiptKind where
  | proof
  | benchmark
  | measurement
  | oracle
  | note
  deriving Repr, DecidableEq, Inhabited

/-- A receipt bound to a target id. -/
structure Receipt where
  targetId : String
  kind : ReceiptKind
  payloadHash : Nat
  deriving Repr, DecidableEq, Inhabited

/-- A persistent receipt ledger. -/
structure ReceiptLedger where
  receipts : List Receipt
  deriving Repr, DecidableEq, Inhabited

/-- A Warden trial for a target id. -/
structure WardenTrial where
  targetId : String
  status : WardenStatus
  deriving Repr, DecidableEq, Inhabited

/-- A single receipt is a proof receipt for a target. -/
def receiptIsProofFor (r : Receipt) (targetId : String) : Bool :=
  r.targetId == targetId && r.kind == ReceiptKind.proof

/-- Receipt-list proof gate. -/
def hasProofReceipt (receipts : List Receipt) (targetId : String) : Bool :=
  receipts.any (fun r => receiptIsProofFor r targetId)

/-- Ledger proof gate. -/
def ledgerHasProofReceipt (ledger : ReceiptLedger) (targetId : String) : Bool :=
  hasProofReceipt ledger.receipts targetId

/-- Boolean reviewed helper avoids brittle dependent elimination over status equality. -/
def isReviewed (trial : WardenTrial) : Bool :=
  trial.status == WardenStatus.reviewed

/-- List-level promotion gate. -/
def promoteTrial (trial : WardenTrial) (receipts : List Receipt) (targetId : String) : WardenTrial :=
  if trial.status == WardenStatus.candidate && hasProofReceipt receipts targetId then
    { trial with status := WardenStatus.reviewed }
  else
    trial

/-- Ledger-level promotion gate. -/
def promoteTrialLedger (trial : WardenTrial) (ledger : ReceiptLedger) (targetId : String) : WardenTrial :=
  promoteTrial trial ledger.receipts targetId

/-- If the list-level promotion produces reviewed from a candidate, the proof receipt gate was true. -/
theorem promoteTrial_reviewed_implies_receipt
    (trial : WardenTrial)
    (receipts : List Receipt)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.candidate)
    (hReviewed : (promoteTrial trial receipts targetId).status = WardenStatus.reviewed) :
    hasProofReceipt receipts targetId = true := by
  unfold promoteTrial at hReviewed
  simp [hCandidate] at hReviewed
  by_cases hReceipt : hasProofReceipt receipts targetId
  · simpa [hReceipt]
  · simp [hReceipt] at hReviewed
    rw [hCandidate] at hReviewed
    contradiction

/-- Same invariant through the Boolean reviewed helper. -/
theorem promoteTrial_reviewed_bool_implies_receipt
    (trial : WardenTrial)
    (receipts : List Receipt)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.candidate)
    (hReviewed : isReviewed (promoteTrial trial receipts targetId) = true) :
    hasProofReceipt receipts targetId = true := by
  unfold isReviewed at hReviewed
  cases hStatus : (promoteTrial trial receipts targetId).status <;> simp [hStatus] at hReviewed
  exact promoteTrial_reviewed_implies_receipt trial receipts targetId hCandidate hStatus

/-- Ledger-level theorem: REVIEWED promotion implies ledger has proof receipt. -/
theorem promoteTrialLedger_preserves_receipt_gate
    (trial : WardenTrial)
    (ledger : ReceiptLedger)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.candidate)
    (hReviewed : (promoteTrialLedger trial ledger targetId).status = WardenStatus.reviewed) :
    ledgerHasProofReceipt ledger targetId = true := by
  unfold promoteTrialLedger at hReviewed
  unfold ledgerHasProofReceipt
  exact promoteTrial_reviewed_implies_receipt trial ledger.receipts targetId hCandidate hReviewed

/-- A candidate without proof receipt is not promoted to reviewed. -/
theorem no_receipt_candidate_not_reviewed
    (trial : WardenTrial)
    (ledger : ReceiptLedger)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.candidate)
    (hNoReceipt : ledgerHasProofReceipt ledger targetId = false) :
    (promoteTrialLedger trial ledger targetId).status = WardenStatus.candidate := by
  unfold promoteTrialLedger promoteTrial ledgerHasProofReceipt at *
  simp [hCandidate, hNoReceipt]

/-- A candidate with proof receipt promotes to reviewed. -/
theorem proof_receipt_candidate_promotes_reviewed
    (trial : WardenTrial)
    (ledger : ReceiptLedger)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.candidate)
    (hReceipt : ledgerHasProofReceipt ledger targetId = true) :
    (promoteTrialLedger trial ledger targetId).status = WardenStatus.reviewed := by
  unfold promoteTrialLedger promoteTrial ledgerHasProofReceipt at *
  simp [hCandidate, hReceipt]

/-- Example proof receipt. -/
def proofReceipt : Receipt :=
  { targetId := "target-0", kind := ReceiptKind.proof, payloadHash := 12345 }

/-- Example note receipt: insufficient for REVIEWED promotion. -/
def noteReceipt : Receipt :=
  { targetId := "target-0", kind := ReceiptKind.note, payloadHash := 999 }

/-- Example candidate trial. -/
def candidateTrial : WardenTrial :=
  { targetId := "target-0", status := WardenStatus.candidate }

/-- Ledger with a proof receipt. -/
def proofLedger : ReceiptLedger :=
  { receipts := [proofReceipt] }

/-- Ledger with only a note receipt. -/
def noteOnlyLedger : ReceiptLedger :=
  { receipts := [noteReceipt] }

/-- Proof-ledger example promotes. -/
theorem example_proof_ledger_promotes :
    (promoteTrialLedger candidateTrial proofLedger "target-0").status = WardenStatus.reviewed := by
  exact proof_receipt_candidate_promotes_reviewed candidateTrial proofLedger "target-0" rfl rfl

/-- Note-only ledger example does not promote. -/
theorem example_note_only_ledger_does_not_promote :
    (promoteTrialLedger candidateTrial noteOnlyLedger "target-0").status = WardenStatus.candidate := by
  exact no_receipt_candidate_not_reviewed candidateTrial noteOnlyLedger "target-0" rfl rfl

/-- The promoted proof-ledger example preserves the receipt gate. -/
theorem example_promoted_implies_receipt :
    ledgerHasProofReceipt proofLedger "target-0" = true := by
  exact promoteTrialLedger_preserves_receipt_gate candidateTrial proofLedger "target-0" rfl example_proof_ledger_promotes

#eval ledgerHasProofReceipt proofLedger "target-0" -- true
#eval ledgerHasProofReceipt noteOnlyLedger "target-0" -- false
#eval (promoteTrialLedger candidateTrial proofLedger "target-0").status -- reviewed
#eval (promoteTrialLedger candidateTrial noteOnlyLedger "target-0").status -- candidate

end Semantics.ReceiptLedgerPromotionGate
