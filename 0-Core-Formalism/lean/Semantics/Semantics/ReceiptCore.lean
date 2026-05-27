/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ReceiptCore.lean — Proof Receipt Infrastructure for GCL Workspace

This module defines the receipt types that external validation systems
(build, benchmark, audit, human review) must produce before a Warden
status can promote from CANDIDATE or HOLD to REVIEWED.

Per AGENTS.md §1.6: Every `sorry` must have a `TODO(lean-port)` comment.
Per AGENTS.md §4: Every `def` that computes a cost or invariant must have
an `#eval` example or a theorem.

Integration:
- GeometricCompressionWorkspace.lean: hasProofReceipt consumes List Receipt
- FixedPoint.lean: Q0_64 for receipt scoring
- SyntheticGeneticCoding.lean: AuthorityState alignment (HOLD / REVIEWED)
-/

namespace Semantics.ReceiptCore

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  RECEIPT KINDS
-- ═══════════════════════════════════════════════════════════════════════════

/-- The kinds of external validation receipts that can unblock promotion.
    Each receipt is produced by a distinct authority outside the workspace.
    
    Policy: No receipt kind may be self-issued by the workspace autopoiesis. -/
inductive ReceiptKind where
  | leanBuild         -- Compilation success (lake build)
  | benchmark         -- Benchmark result with bounded delta / preserved phi
  | sourceAudit       -- External source audit (PlanetWaves, ES papers, etc.)
  | reverseCollapse   -- Verified reverse-collapse path
  | deltaPhiAudit     -- Δφγλ audit passed with explicit thresholds
  | adversarialTrial  -- Adversarial trial survived with surviving phi
  | humanReview       -- Human or external reviewer sign-off
  | wardenEmission    -- Warden classification of failure pattern
  | externalProof     -- Peer-reviewed theorem or formal proof
  deriving BEq, DecidableEq, Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  RECEIPT STRUCTURE
-- ═══════════════════════════════════════════════════════════════════════════

/-- A Receipt is evidence that an external validation step completed.
    
    Fields:
    - kind: what kind of validation produced this
    - targetId: the operator / trial / object this receipt validates
    - summary: human-readable description
    - valid: did the validation pass?
    - authority: who issued it (machine tag or human identity)
    - timestamp: optional ordering for multi-receipt sequences
    
    Warden rule: A receipt with valid=false is a BLOCK, not a HOLD. -/
structure Receipt where
  kind : ReceiptKind
  targetId : String
  summary : String
  valid : Bool
  authority : String
  timestamp : Nat  -- monotonic nonce / epoch seconds
  deriving Repr, Inhabited, BEq, DecidableEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  RECEIPT GATES
-- ═══════════════════════════════════════════════════════════════════════════

/-- Default empty receipt list for uninitialized states. -/
def emptyReceipts : List Receipt := []

/-- Check whether a target has at least one receipt of a given kind that is valid. -/
def hasReceiptOfKind
    (receipts : List Receipt)
    (targetId : String)
    (kind : ReceiptKind) : Bool :=
  receipts.any (fun r => r.targetId == targetId && r.kind == kind && r.valid)

/-- Check whether a target has receipts covering all required kinds.
    Used by Warden to decide if a CANDIDATE can advance to REVIEWED. -/
def hasAllReceiptKinds
    (receipts : List Receipt)
    (targetId : String)
    (required : List ReceiptKind) : Bool :=
  required.all (fun k => hasReceiptOfKind receipts targetId k)

/-- Promotion gate: Does the target have enough receipts to unblock?
    Policy: At least one valid receipt of any kind is minimum.
    Stronger policies can be enforced by callers. -/
def canPromoteFromCandidate
    (receipts : List Receipt)
    (targetId : String) : Bool :=
  receipts.any (fun r => r.targetId == targetId && r.valid)

/-- Blocked check: Any invalid receipt for this target triggers BLOCK. -/
def isBlocked
    (receipts : List Receipt)
    (targetId : String) : Bool :=
  receipts.any (fun r => r.targetId == targetId && !r.valid)

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  RECEIPT CONSTRUCTORS (EXAMPLES)
-- ═══════════════════════════════════════════════════════════════════════════

def leanBuildReceipt (targetId : String) (passed : Bool) : Receipt :=
  { kind := .leanBuild,
    targetId := targetId,
    summary := if passed then "lake build passed" else "lake build failed",
    valid := passed,
    authority := "lake_build_bot",
    timestamp := 0 }

def benchmarkReceipt (targetId : String) (deltaBounded : Bool) (phiPreserved : Bool) : Receipt :=
  { kind := .benchmark,
    targetId := targetId,
    summary := s!"benchmark: deltaBounded={deltaBounded}, phiPreserved={phiPreserved}",
    valid := deltaBounded && phiPreserved,
    authority := "benchmark_harness",
    timestamp := 1 }

def adversarialTrialReceipt (targetId : String) (survivedPhi : Bool) : Receipt :=
  { kind := .adversarialTrial,
    targetId := targetId,
    summary := if survivedPhi then "Adversarial trial: phi survived" else "Adversarial trial: phi lost",
    valid := survivedPhi,
    authority := "adversarial_trial_runner",
    timestamp := 2 }

def humanReviewReceipt (targetId : String) (approved : Bool) (reviewer : String) : Receipt :=
  { kind := .humanReview,
    targetId := targetId,
    summary := if approved then s!"Approved by {reviewer}" else s!"Rejected by {reviewer}",
    valid := approved,
    authority := reviewer,
    timestamp := 3 }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  INTEGRATION: hasProofReceipt (replaces stub in GeometricCompressionWorkspace)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Real implementation of proof-receipt checking.
    
    A target has a proof receipt if it has at least one valid receipt
    of kind `externalProof`, or a valid `adversarialTrial` + `benchmark` pair.
    
    This replaces the placeholder `fun _ => false` in
    GeometricCompressionWorkspace.lean. -/
def hasProofReceipt
    (receipts : List Receipt)
    (targetId : String) : Bool :=
  hasReceiptOfKind receipts targetId .externalProof
  || (hasReceiptOfKind receipts targetId .adversarialTrial
      && hasReceiptOfKind receipts targetId .benchmark)

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  RECEIPT LEDGER (Persistent receipt store for target objects)
-- ═══════════════════════════════════════════════════════════════════════════

/-- A ledger maps target identifiers to their accumulated validation receipts.
    External validation systems (build bots, benchmark harnesses, human reviewers)
    append receipts to the ledger. The ledger is the ground truth for promotion
    decisions; trials may reference it but never self-write to it. -/
structure ReceiptLedger where
  entries : List (String × List Receipt)
  deriving Repr, Inhabited

/-- Lookup receipts for a given target in the ledger. Returns [] if absent. -/
def ledgerLookup (ledger : ReceiptLedger) (targetId : String) : List Receipt :=
  match ledger.entries.find? (fun (id, _) => id == targetId) with
  | some (_, rs) => rs
  | none => []

/-- Append a receipt to a target's entry. Creates a new entry if absent. -/
def ledgerAppend (ledger : ReceiptLedger) (targetId : String) (receipt : Receipt) : ReceiptLedger :=
  let existing := ledgerLookup ledger targetId
  let filtered := ledger.entries.filter (fun (id, _) => id != targetId)
  { ledger with entries := (targetId, existing ++ [receipt]) :: filtered }

/-- Check proof receipt gate against the ledger (convenience wrapper). -/
def ledgerHasProofReceipt (ledger : ReceiptLedger) (targetId : String) : Bool :=
  hasProofReceipt (ledgerLookup ledger targetId) targetId

/-- Ledger invariant: a target cannot be considered proven unless its ledger
    entry contains sufficient receipts. This is the formal bridge between
    the ledger state and the promotion gate. -/
def LedgerPromotionInvariant
    (ledger : ReceiptLedger)
    (targetId : String) : Prop :=
  ledgerHasProofReceipt ledger targetId = true

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  EVAL WITNESSES
-- ═══════════════════════════════════════════════════════════════════════════

-- Receipt constructors
#eval (leanBuildReceipt "test_op_001" true).valid   -- expect: true
#eval (leanBuildReceipt "test_op_001" false).valid  -- expect: false
#eval (benchmarkReceipt "test_op_001" true true).summary   -- expect: "benchmark: deltaBounded=true, phiPreserved=true"
#eval (adversarialTrialReceipt "test_op_001" true).authority  -- expect: "adversarial_trial_runner"
#eval (humanReviewReceipt "test_op_001" true "reviewer_alpha").kind  -- expect: Semantics.ReceiptCore.ReceiptKind.humanReview

-- Empty list
#eval emptyReceipts.length  -- expect: 0

-- Single receipt queries: leanBuild present → true; benchmark absent → false; invalid → false
#eval hasReceiptOfKind [leanBuildReceipt "op1" true] "op1" .leanBuild   -- expect: true
#eval hasReceiptOfKind [leanBuildReceipt "op1" true] "op1" .benchmark   -- expect: false
#eval hasReceiptOfKind [leanBuildReceipt "op1" false] "op1" .leanBuild  -- expect: false

-- hasProofReceipt: no receipts → false
#eval hasProofReceipt [] "any_target"  -- expect: false

-- hasProofReceipt: only adversarialTrial → false (needs benchmark pair)
#eval hasProofReceipt [adversarialTrialReceipt "op1" true] "op1"  -- expect: false

-- hasProofReceipt: adversarialTrial + benchmark pair → true
-- expect: true
#eval hasProofReceipt
  [adversarialTrialReceipt "op1" true, benchmarkReceipt "op1" true true] "op1"

-- hasProofReceipt: externalProof alone → true
-- expect: true
#eval hasProofReceipt
  [{ kind := .externalProof, targetId := "op2", summary := "theorem proven",
     valid := true, authority := "lean_prover", timestamp := 4 }] "op2"

-- canPromoteFromCandidate: valid leanBuild → true; invalid → false; empty → false
#eval canPromoteFromCandidate [leanBuildReceipt "op1" true] "op1"   -- expect: true
#eval canPromoteFromCandidate [leanBuildReceipt "op1" false] "op1"  -- expect: false
#eval canPromoteFromCandidate [] "op1"                               -- expect: false

-- isBlocked: invalid receipt → true; valid receipt → false
#eval isBlocked [leanBuildReceipt "op1" false] "op1"  -- expect: true
#eval isBlocked [leanBuildReceipt "op1" true] "op1"   -- expect: false

-- hasAllReceiptKinds: both kinds present → true; one missing → false
-- expect: true
#eval hasAllReceiptKinds
  [leanBuildReceipt "op1" true, benchmarkReceipt "op1" true true] "op1"
  [.leanBuild, .benchmark]

-- expect: false
#eval hasAllReceiptKinds
  [leanBuildReceipt "op1" true] "op1"
  [.leanBuild, .benchmark]

-- Ledger: empty
#eval (ReceiptLedger.mk []).entries.length  -- expect: 0

-- Ledger: append receipt
#eval (ledgerAppend (ReceiptLedger.mk []) "op1" (leanBuildReceipt "op1" true)).entries.length  -- expect: 1

-- Ledger: lookup
#eval (ledgerLookup (ledgerAppend (ReceiptLedger.mk []) "op1" (leanBuildReceipt "op1" true)) "op1").length  -- expect: 1

-- Ledger: hasProofReceipt via ledger: adversarialTrial + benchmark → true
-- expect: true
#eval ledgerHasProofReceipt
  (ledgerAppend
    (ledgerAppend (ReceiptLedger.mk []) "op1" (adversarialTrialReceipt "op1" true))
    "op1" (benchmarkReceipt "op1" true true)) "op1"

end Semantics.ReceiptCore
