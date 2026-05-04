/-
ReceiptCore.lean — Minimal receipt infrastructure scaffold v0.2

Purpose:
  A workspace may execute, self-test, benchmark, and propose promotion, but it
  may not promote itself to REVIEWED without a proof receipt recorded in the
  supplied receipt set or receipt ledger.

No Float. No probabilistic authority. No self-promotion shortcut.
-/

import Std

namespace Semantics.ReceiptCore

/-- Claim-state ladder used by Warden-style gates. -/
inductive ClaimState where
  | hold
  | candidate
  | reviewed
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Operational status for a trial or candidate artifact. -/
inductive WardenStatus where
  | HOLD
  | CANDIDATE
  | REVIEWED
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Receipt kinds. Only `proofReceipt` grants review authority. -/
inductive ReceiptKind where
  | leanBuild
  | executableEval
  | benchmark
  | adversarialTrial
  | measurement
  | provenance
  | sourceAudit
  | reverseCollapse
  | deltaPhiAudit
  | humanReview
  | wardenEmission
  | proofReceipt
  deriving Repr, DecidableEq, BEq, Inhabited

/-- A typed evidence receipt for a target artifact/operator. -/
structure Receipt where
  targetId : String
  kind : ReceiptKind
  passed : Bool
  note : String
  deriving Repr, BEq, Inhabited

/-- Candidate trial emitted by an executable/adversarial workspace. -/
structure AdversarialTrial where
  targetId : String
  status : WardenStatus
  auditPassed : Bool
  deriving Repr, BEq, Inhabited

/-- A proof receipt for a target. This is the only REVIEWED promotion authority. -/
def proofReceipt (targetId : String) (passed : Bool) : Receipt :=
  { targetId := targetId
    kind := .proofReceipt
    passed := passed
    note := "formal proof receipt" }

/-- A Lean build receipt. Useful evidence, but not promotion authority by itself. -/
def leanBuildReceipt (targetId : String) (passed : Bool) : Receipt :=
  { targetId := targetId
    kind := .leanBuild
    passed := passed
    note := "Lean build receipt" }

/-- An executable evaluation receipt. Useful evidence, but not promotion authority by itself. -/
def executableEvalReceipt (targetId : String) (passed : Bool) : Receipt :=
  { targetId := targetId
    kind := .executableEval
    passed := passed
    note := "executable evaluation receipt" }

/-- A benchmark receipt. Useful evidence, but not promotion authority by itself. -/
def benchmarkReceipt (targetId : String) (passed : Bool) : Receipt :=
  { targetId := targetId
    kind := .benchmark
    passed := passed
    note := "benchmark receipt" }

/-- An adversarial-trial receipt. Useful evidence, but not promotion authority by itself. -/
def adversarialTrialReceipt (targetId : String) (passed : Bool) : Receipt :=
  { targetId := targetId
    kind := .adversarialTrial
    passed := passed
    note := "adversarial-trial receipt" }

/-- A human-review receipt. Useful evidence, but not promotion authority by itself. -/
def humanReviewReceipt (targetId : String) (passed : Bool) : Receipt :=
  { targetId := targetId
    kind := .humanReview
    passed := passed
    note := "human review receipt" }

/-- True when a receipt is a valid receipt of the requested kind for the target. -/
def hasReceiptOfKind (receipts : List Receipt) (targetId : String) (kind : ReceiptKind) : Bool :=
  receipts.any (fun r => (r.targetId == targetId) && (r.kind == kind) && r.passed)

/-- Check that every required receipt kind is present and valid for the target. -/
def hasAllReceiptKinds (receipts : List Receipt) (targetId : String) (kinds : List ReceiptKind) : Bool :=
  kinds.all (hasReceiptOfKind receipts targetId)

/-- True exactly when a receipt is a passing proof receipt for the target. -/
def isPassingProofReceiptFor (targetId : String) (r : Receipt) : Bool :=
  (r.targetId == targetId) && (r.kind == .proofReceipt) && r.passed

/-- List-level proof authority gate. -/
def hasProofReceipt (receipts : List Receipt) (targetId : String) : Bool :=
  receipts.any (isPassingProofReceiptFor targetId)

/-- Append-only receipt ledger, keyed by target ID.

Duplicate keys are allowed intentionally. `ledgerAppend` prepends a fresh entry
whose value includes the prior lookup result, so the newest entry becomes a
persistent accumulated view for that target.
-/
structure ReceiptLedger where
  entries : List (String × List Receipt)
  deriving Repr, Inhabited

/-- Empty receipt ledger. -/
def emptyLedger : ReceiptLedger :=
  { entries := [] }

/-- Lookup accumulated receipts for a target. -/
def ledgerLookup (ledger : ReceiptLedger) (targetId : String) : List Receipt :=
  match ledger.entries.find? (fun e => e.fst == targetId) with
  | some e => e.snd
  | none => []

/-- Append a receipt to a target's accumulated receipt view. -/
def ledgerAppend (ledger : ReceiptLedger) (targetId : String) (r : Receipt) : ReceiptLedger :=
  { entries := (targetId, r :: ledgerLookup ledger targetId) :: ledger.entries }

/-- Ledger-level proof authority gate. -/
def ledgerHasProofReceipt (ledger : ReceiptLedger) (targetId : String) : Bool :=
  hasProofReceipt (ledgerLookup ledger targetId) targetId

/-- Promotion rule: a CANDIDATE can become REVIEWED only with a proof receipt. -/
def promoteTrial (trial : AdversarialTrial) (receipts : List Receipt) : AdversarialTrial :=
  match trial.status with
  | .CANDIDATE =>
      if hasProofReceipt receipts trial.targetId then
        { trial with status := .REVIEWED }
      else
        trial
  | _ => trial

/-- Ledger-backed promotion rule. -/
def promoteTrialLedger (trial : AdversarialTrial) (ledger : ReceiptLedger) : AdversarialTrial :=
  promoteTrial trial (ledgerLookup ledger trial.targetId)

/-- List-level invariant: REVIEWED promotion from CANDIDATE implies proof receipt. -/
theorem promoteTrial_preserves_receipt_gate
    (trial : AdversarialTrial)
    (receipts : List Receipt)
    (hCandidate : trial.status = WardenStatus.CANDIDATE)
    (hReviewed : (promoteTrial trial receipts).status = WardenStatus.REVIEWED) :
    hasProofReceipt receipts trial.targetId = true := by
  unfold promoteTrial at hReviewed
  rw [hCandidate] at hReviewed
  cases hp : hasProofReceipt receipts trial.targetId with
  | false =>
      simp [hp] at hReviewed
  | true =>
      exact hp

/-- Ledger-level invariant: REVIEWED promotion from CANDIDATE implies ledger proof receipt. -/
theorem promoteTrialLedger_preserves_invariant
    (trial : AdversarialTrial)
    (ledger : ReceiptLedger)
    (hCandidate : trial.status = WardenStatus.CANDIDATE)
    (hReviewed : (promoteTrialLedger trial ledger).status = WardenStatus.REVIEWED) :
    ledgerHasProofReceipt ledger trial.targetId = true := by
  unfold promoteTrialLedger at hReviewed
  unfold ledgerHasProofReceipt
  exact promoteTrial_preserves_receipt_gate trial (ledgerLookup ledger trial.targetId) hCandidate hReviewed

/-- Appending a passing proof receipt for a target makes that target proof-visible in the ledger. -/
theorem ledger_append_proof_receipt_visible
    (ledger : ReceiptLedger)
    (targetId : String) :
    ledgerHasProofReceipt (ledgerAppend ledger targetId (proofReceipt targetId true)) targetId = true := by
  unfold ledgerHasProofReceipt ledgerAppend ledgerLookup hasProofReceipt isPassingProofReceiptFor proofReceipt
  simp

/-- Appending a non-proof receipt alone does not give proof authority on an empty ledger. -/
theorem empty_ledger_append_benchmark_not_proof
    (targetId : String) :
    ledgerHasProofReceipt (ledgerAppend emptyLedger targetId (benchmarkReceipt targetId true)) targetId = false := by
  unfold ledgerHasProofReceipt ledgerAppend ledgerLookup emptyLedger hasProofReceipt isPassingProofReceiptFor benchmarkReceipt
  simp

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  EVAL WITNESSES
-- ═══════════════════════════════════════════════════════════════════════════

/-- Example candidate without proof authority. -/
def candidateTrial : AdversarialTrial :=
  { targetId := "operator.alpha"
    status := .CANDIDATE
    auditPassed := true }

/-- Build/eval/benchmark/adversarial receipts alone do not review-promote. -/
def nonProofReceipts : List Receipt :=
  [ leanBuildReceipt "operator.alpha" true
  , executableEvalReceipt "operator.alpha" true
  , benchmarkReceipt "operator.alpha" true
  , adversarialTrialReceipt "operator.alpha" true
  , humanReviewReceipt "operator.alpha" true ]

/-- With an explicit proof receipt, promotion can reach REVIEWED. -/
def proofReceipts : List Receipt :=
  proofReceipt "operator.alpha" true :: nonProofReceipts

/-- Ledger with non-proof receipts only. -/
def nonProofLedger : ReceiptLedger :=
  ledgerAppend
    (ledgerAppend emptyLedger "operator.alpha" (adversarialTrialReceipt "operator.alpha" true))
    "operator.alpha"
    (benchmarkReceipt "operator.alpha" true)

/-- Ledger with a proof receipt appended on top of non-proof evidence. -/
def proofLedger : ReceiptLedger :=
  ledgerAppend nonProofLedger "operator.alpha" (proofReceipt "operator.alpha" true)

#eval hasProofReceipt nonProofReceipts "operator.alpha" -- false
#eval hasProofReceipt proofReceipts "operator.alpha"    -- true
#eval (promoteTrial candidateTrial nonProofReceipts).status == WardenStatus.CANDIDATE
#eval (promoteTrial candidateTrial proofReceipts).status == WardenStatus.REVIEWED
#eval ledgerHasProofReceipt nonProofLedger "operator.alpha" -- false
#eval ledgerHasProofReceipt proofLedger "operator.alpha"    -- true
#eval (promoteTrialLedger candidateTrial nonProofLedger).status == WardenStatus.CANDIDATE
#eval (promoteTrialLedger candidateTrial proofLedger).status == WardenStatus.REVIEWED

end Semantics.ReceiptCore
