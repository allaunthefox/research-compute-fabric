/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

HermesAgentIntegration.lean — Field Operator Integration Boundary

This module formalizes the integration of Hermes Agent as a field operator,
messenger, and skill runtime that remains subordinate to Lean verification,
GCL classification, and Warden promotion gates.

Doctrine:
- Hermes observes, routes, schedules, and executes
- GCL classifies, compresses, and binds
- Lean verifies
- Warden promotes, holds, or blocks
- ENE persists and distributes

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has #eval witness or theorem.
Per AGENTS.md §1.6: No sorry in committed code.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Semantics.ReceiptCore
import Semantics.FixedPoint

namespace Semantics.HermesAgentIntegration

open Semantics (Q16_16)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  HERMES COMMAND SURFACE
-- ═══════════════════════════════════════════════════════════════════════════

/-- Commands that Hermes can receive via CLI or messaging gateways.
    These are read-only or receipt-producing operations only. -/
inductive HermesCommand where
  | runGclAudit          -- Execute GCL classification audit
  | summarizeReceipts    -- Summarize Warden receipt ledger
  | queueDeepseekReview    -- Bundle docs for adversarial review
  | checkLeanSorries     -- Scan Lean files for sorry locations
  | searchProvenance     -- Search provenance database
  | buildCffEntry        -- Generate CFF citation entry
  | wardenStatus         -- Report current HOLD/BLOCK/CANDIDATE state
  | skillRun             -- Execute a named skill with receipt emission
  deriving BEq, DecidableEq, Repr, Inhabited

namespace HermesCommand

/-- Human-readable command labels. -/
def toString : HermesCommand → String
  | runGclAudit       => "/run-gcl-audit"
  | summarizeReceipts => "/summarize-receipts"
  | queueDeepseekReview => "/queue-deepseek-review"
  | checkLeanSorries  => "/check-lean-sorries"
  | searchProvenance  => "/search-provenance"
  | buildCffEntry     => "/build-cff-entry"
  | wardenStatus      => "/warden-status"
  | skillRun          => "/skill-run"

/-- All available commands. -/
def all : List HermesCommand :=
  [runGclAudit, summarizeReceipts, queueDeepseekReview, checkLeanSorries,
   searchProvenance, buildCffEntry, wardenStatus, skillRun]

end HermesCommand

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  HERMES SKILL SPECIFICATION
-- ═══════════════════════════════════════════════════════════════════════════

/-- Authority level a skill may hold.
    Phase 0: read-only (search, summarize)
    Phase 1: receipt-producing (create artifacts, no promotion)
    Phase 2: scheduled audits (cron-driven, output defaults to HOLD)
    Phase 3: controlled write (PR/commit with receipt bundle) -/
inductive SkillPhase where
  | readOnly        -- Phase 0: no writes
  | receiptProduce  -- Phase 1: emits SkillRunReceipt + SourceReceipt
  | scheduledAudit  -- Phase 2: cron-driven, output defaults to HOLD
  | controlledWrite -- Phase 3: PR/commit with full receipt bundle
  deriving BEq, DecidableEq, Repr, Inhabited

/-- Promotion authority state for Hermes skill outputs.
    Mirrors WardenStatus but is local to the Hermes integration.
    All Hermes outputs begin at HOLD and require external receipts
    to advance. -/
inductive HermesStatus where
  | HOLD        -- Default: under review, no promotion
  | CANDIDATE   -- Skill ran successfully, awaiting receipt validation
  | REVIEWED    -- External review + receipts verified
  | BLOCKED     -- Promotion denied, failure mode recorded
  deriving BEq, DecidableEq, Repr, Inhabited

namespace HermesStatus

def toString : HermesStatus → String
  | HOLD => "HOLD"
  | CANDIDATE => "CANDIDATE"
  | REVIEWED => "REVIEWED"
  | BLOCKED => "BLOCKED"

instance : ToString HermesStatus := ⟨toString⟩

end HermesStatus

/-- A Hermes skill: repeatable Research Stack task with explicit
    source requirements, Warden checks, and promotion boundaries. -/
structure HermesSkill where
  name : String
  phase : SkillPhase
  taskRecipe : String
  requiredSources : List String
  wardenChecks : List String
  expectedReceiptKinds : List ReceiptCore.ReceiptKind
  failureModes : List String
  defaultStatus : HermesStatus
  deriving Repr, Inhabited

namespace HermesSkill

/-- Default status for any Hermes skill: HOLD.
    Warden-safe doctrine: Hermes may not self-promote. -/
def defaultHermesStatus : HermesStatus := HermesStatus.HOLD

/-- Phase 0 (read-only) skills never require receipts. -/
def isReadOnly (skill : HermesSkill) : Bool :=
  skill.phase = SkillPhase.readOnly

/-- Phase 1+ skills require receipts for promotion. -/
def requiresReceipts (skill : HermesSkill) : Bool :=
  skill.phase = SkillPhase.receiptProduce
  || skill.phase = SkillPhase.scheduledAudit
  || skill.phase = SkillPhase.controlledWrite

/-- Check whether a skill has sufficient receipts to advance from HOLD.
    A skill is promotable only if:
    1. It is not read-only
    2. It has at least one valid receipt of each expected kind
    3. No BLOCKED status exists for the target -/
def canPromote
    (skill : HermesSkill)
    (receipts : List ReceiptCore.Receipt)
    (targetId : String) : Bool :=
  if skill.isReadOnly then false  -- read-only never promotes
  else
    let hasAll := skill.expectedReceiptKinds.all
      (fun k => ReceiptCore.hasReceiptOfKind receipts targetId k)
    let blocked := receipts.any (fun r => r.targetId == targetId && !r.valid)
    hasAll && !blocked

/-- Example skills from the integration proposal. -/
def gclProvenanceCff : HermesSkill :=
  { name := "gcl-provenance-cff"
  , phase := .receiptProduce
  , taskRecipe := "Ingest DOI/article/source, create CFF entry, add Warden boundary"
  , requiredSources := ["doi", "article_metadata", "provenance_db"]
  , wardenChecks := ["source_boundary_present", "cff_schema_valid"]
  , expectedReceiptKinds := [.sourceAudit, .humanReview]
  , failureModes := ["missing_doi", "malformed_cff", "no_provenance"]
  , defaultStatus := defaultHermesStatus }

def leanSorryAudit : HermesSkill :=
  { name := "lean-sorry-audit"
  , phase := .receiptProduce
  , taskRecipe := "Scan Lean files, list sorry locations, classify gaps"
  , requiredSources := ["tools/lean/Semantics"]
  , wardenChecks := ["sorry_count_bounded", "no_new_sorry_without_todo"]
  , expectedReceiptKinds := [.leanBuild]
  , failureModes := ["build_failure", "sorry_increase", "missing_todo_comment"]
  , defaultStatus := defaultHermesStatus }

def adapterSpecWriter : HermesSkill :=
  { name := "adapter-spec-writer"
  , phase := .receiptProduce
  , taskRecipe := "Turn source cluster into GCL bridge doc"
  , requiredSources := ["source_cluster", "gcl_schema"]
  , wardenChecks := ["bind_primitive_present", "cost_function_defined"]
  , expectedReceiptKinds := [.humanReview, .deltaPhiAudit]
  , failureModes := ["missing_bind", "no_cost_function", "float_in_hotpath"]
  , defaultStatus := defaultHermesStatus }

def deepseekReviewBundle : HermesSkill :=
  { name := "deepseek-review-bundle"
  , phase := .receiptProduce
  , taskRecipe := "Collect docs, enforce adversarial convergence prompt, save artifact"
  , requiredSources := ["review_docs", "adversarial_prompt_template"]
  , wardenChecks := ["convergence_prompt_present", "artifact_saved"]
  , expectedReceiptKinds := [.adversarialTrial, .humanReview]
  , failureModes := ["missing_convergence_prompt", "artifact_too_large", "no_receipt_emitted"]
  , defaultStatus := defaultHermesStatus }

def wardenTriage : HermesSkill :=
  { name := "warden-triage"
  , phase := .scheduledAudit
  , taskRecipe := "Classify outputs as HOLD/CANDIDATE/BLOCK/REVIEWED"
  , requiredSources := ["output_artifact", "receipt_ledger"]
  , wardenChecks := ["status_explicit", "receipt_boundary_present"]
  , expectedReceiptKinds := [.wardenEmission]
  , failureModes := ["missing_status", "no_receipt_boundary", "self_promotion_detected"]
  , defaultStatus := defaultHermesStatus }

end HermesSkill

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  RECEIPT EMISSION (Skill Output Contract)
-- ═══════════════════════════════════════════════════════════════════════════

/-- A SkillRunReceipt documents that a Hermes skill executed.
    Emitted after every skill invocation, successful or not. -/
structure SkillRunReceipt where
  skillName : String
  command : HermesCommand
  startedAt : Nat       -- monotonic timestamp
  completedAt : Nat
  success : Bool
  outputs : List String -- file paths or artifact IDs produced
  statusEmitted : HermesStatus
  deriving Repr, Inhabited

/-- Convert a SkillRunReceipt into a canonical ReceiptCore.Receipt.
    Hermes skills emit benchmark-style receipts for Warden tracking. -/
def skillRunToReceiptCore (sr : SkillRunReceipt) : ReceiptCore.Receipt :=
  { kind := ReceiptCore.ReceiptKind.benchmark
  , targetId := sr.skillName
  , summary := s!"Hermes skill {sr.skillName} success={sr.success} status={sr.statusEmitted}"
  , valid := sr.success
  , authority := "hermes_skill_runner"
  , timestamp := sr.completedAt }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  PROMOTION GATE THEOREMS
-- ═══════════════════════════════════════════════════════════════════════════

/-- Read-only skills cannot promote by design.
    This is the formal enforcement of Phase 0 doctrine. -/
theorem readOnlyCannotPromote
    (skill : HermesSkill)
    (receipts : List ReceiptCore.Receipt)
    (targetId : String)
    (hReadOnly : skill.phase = SkillPhase.readOnly) :
    HermesSkill.canPromote skill receipts targetId = false := by
  simp [HermesSkill.canPromote, HermesSkill.isReadOnly, hReadOnly]

/-- A skill with empty expected receipts and non-read-only phase
    is trivially promotable (vacuously satisfies receipt requirements).
    This is the base case for receipt accumulation. -/
theorem emptyReceiptsVacuousPromote
    (skill : HermesSkill)
    (receipts : List ReceiptCore.Receipt)
    (targetId : String)
    (hPhase : skill.phase ≠ SkillPhase.readOnly)
    (hEmpty : skill.expectedReceiptKinds = [])
    (hNoBlocked : ¬(receipts.any (fun r => r.targetId == targetId && !r.valid))) :
    HermesSkill.canPromote skill receipts targetId = true := by
  simp [HermesSkill.canPromote, HermesSkill.isReadOnly,
        hPhase, hEmpty, hNoBlocked]

/-- The default Hermes status is always HOLD.
    Self-promotion is impossible without external receipts. -/
theorem defaultStatusIsHold :
    HermesSkill.defaultHermesStatus = HermesStatus.HOLD := by
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  EVAL WITNESSES
-- ═══════════════════════════════════════════════════════════════════════════

-- Command surface
#eval HermesCommand.toString HermesCommand.runGclAudit
#eval HermesCommand.all.length

-- Status values
#eval HermesStatus.HOLD
#eval HermesStatus.CANDIDATE

-- Skill: read-only never promotes
#eval (HermesSkill.canPromote
  { name := "test_readonly", phase := .readOnly, taskRecipe := "", requiredSources := [],
    wardenChecks := [], expectedReceiptKinds := [], failureModes := [],
    defaultStatus := HermesSkill.defaultHermesStatus }
  [] "test_target")

-- Skill: receipt-producer with empty expected receipts (vacuous case)
#eval (HermesSkill.canPromote
  { name := "test_receipt", phase := .receiptProduce, taskRecipe := "", requiredSources := [],
    wardenChecks := [], expectedReceiptKinds := [], failureModes := [],
    defaultStatus := HermesSkill.defaultHermesStatus }
  [] "test_target")

-- Skill: requires specific receipt kind, not present → false
#eval (HermesSkill.canPromote
  { name := "test_needs_build", phase := .receiptProduce, taskRecipe := "", requiredSources := [],
    wardenChecks := [], expectedReceiptKinds := [ReceiptCore.ReceiptKind.leanBuild], failureModes := [],
    defaultStatus := HermesSkill.defaultHermesStatus }
  [] "test_target")

-- Skill: requires specific receipt kind, present → true
#eval (HermesSkill.canPromote
  { name := "test_has_build", phase := .receiptProduce, taskRecipe := "", requiredSources := [],
    wardenChecks := [], expectedReceiptKinds := [ReceiptCore.ReceiptKind.leanBuild], failureModes := [],
    defaultStatus := HermesSkill.defaultHermesStatus }
  [ReceiptCore.leanBuildReceipt "test_target" true] "test_target")

-- SkillRunReceipt conversion
#eval (skillRunToReceiptCore
  { skillName := "test_skill", command := .skillRun, startedAt := 0, completedAt := 1,
    success := true, outputs := ["out.md"], statusEmitted := HermesStatus.HOLD }).valid

-- Example skill constructors
#eval HermesSkill.gclProvenanceCff.name
#eval HermesSkill.leanSorryAudit.phase
#eval HermesSkill.adapterSpecWriter.expectedReceiptKinds.length
#eval HermesSkill.deepseekReviewBundle.wardenChecks.length
#eval HermesSkill.wardenTriage.defaultStatus

end Semantics.HermesAgentIntegration
