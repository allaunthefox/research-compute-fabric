/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GeometricCompressionWorkspace.lean — Four-Zone Workspace for LLM Search

This module implements the concrete workspace where source objects are projected
into Q0_64 coding atoms, embedded into geometric surfaces, compressed by collapse
operators, and audited by Delta-Phi-Gamma-Lambda plus Warden receipts.

External Anchors:
- MIT PlanetWaves (2026): Medium determines surface response
- Salimans et al. (2017): ES as scalable mutation-search
- ES at Scale (2025): Billion-parameter LLM fine-tuning
- EGGROLL (2025): Structured low-rank perturbations

Doctrine:
- All coding is Q0_64 (CodingQ)
- Source measurements use BioParamQ (Q16_16)
- Projections require explicit normalization receipts
- No Float in canonical code (use ofRatio)
- Geometry is the compression workspace, not decoration

Per AGENTS.md §1.4, §1.5: Fixed-point arithmetic, no Float in hot path.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has #eval witness or theorem.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint
import Semantics.ReceiptCore

namespace Semantics.GeometricCompressionWorkspace

open Semantics.Q16_16.Q0_64
open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  FOUR-ZONE TYPE SYSTEM
-- ═══════════════════════════════════════════════════════════════════════════

-- Zone 1: Source-Space (Raw measurements, dimensioned values)
-- Zone 2: Coding-Space (Normalized Q0_64 atoms)
-- Zone 3: Geometry-Space (Surfaces, perturbations, collapse)
-- Zone 4: Receipt-Space (Audit results, failures, Warden receipts)

/-- Zone 1: Source-Space — Raw measurements before projection.
    Type: BioParamQ (Q16_16). Range: [-32768, 32767].
    Examples: helicalDiameter=2.2nm, Tm=65°C, charge=-1.0 -/
structure SourceValue where
  name : String
  rawValue : Q16_16
  unit : String  -- e.g., "nm", "°C", "charge units"
  measurementProvenance : String
  deriving Repr, Inhabited

/-- Zone 2: Coding-Space — Normalized Q0_64 atoms.
    All canonical coding values. Range: [-1, 1). -/
structure CodingAtom where
  value : Q0_64
  provenance : String  -- How this atom was produced
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Zone 2: Projection Receipt — Source → Coding map documentation -/
structure ProjectionReceipt where
  source : SourceValue
  maxExpected : Q16_16  -- Normalization scale
  codingResult : CodingAtom
  receiptId : String
  deriving Repr, Inhabited

/-- Zone 3: Geometry-Space — Geometric embedding of coding atoms.
    Surface cell index for perturbation/collapse operations. -/
structure SurfaceCoordinate where
  x : CodingAtom
  y : CodingAtom
  z : Option CodingAtom  -- Optional for 2D surfaces
  cellId : String
  deriving BEq, Repr, Inhabited

/-- Zone 3: Perturbation Direction — Low-rank / structured basis direction.
    Inspired by EGGROLL/LoRA structured perturbations. -/
structure PerturbationDirection where
  directionId : String
  basisRank : Nat  -- Low-rank constraint
  startCoord : SurfaceCoordinate
  endCoord : SurfaceCoordinate
  invariantPreservation : CodingAtom  -- Phi survival estimate
  deriving BEq, Repr, Inhabited

/-- Zone 3: Collapse Operator — Compression transform on geometric surface.
    The core operator that DeepSeek/LLM must propose and validate.
    Note: No deriving Repr because of function fields. -/
structure CollapseOperator where
  name : String
  inputDims : Nat
  outputDims : Nat
  -- Geometric embedding: maps coding atoms to surface coordinates
  embedding : CodingAtom → SurfaceCoordinate
  -- Perturbation basis: low-rank directions for structured search
  basis : List PerturbationDirection
  -- Collapse function: reduces dimension while preserving structure
  collapse : SurfaceCoordinate → CodingAtom
  deriving Inhabited

/-- Zone 4: Receipt-Space — Delta-Phi-Gamma-Lambda Audit -/
structure DeltaResidual where
  changeDescription : String
  magnitude : CodingAtom  -- Normalized residual [0, 1)
  receipt : Option String
  deriving Repr, Inhabited

structure PhiInvariant where
  invariantDescription : String
  preserved : Bool
  proofReceipt : Option String
  deriving Repr, Inhabited

structure GammaPressure where
  pressureLevel : CodingAtom  -- [0, 1)
  description : String
  deriving Repr, Inhabited

structure LambdaScale where
  scaleDescription : String
  byteSpan : Option Nat
  temporalWindow : Option Nat
  deriving Repr, Inhabited

/-- Complete Δφγλ audit record -/
structure DeltaPhiGammaLambdaAudit where
  delta : DeltaResidual
  phi : PhiInvariant
  gamma : GammaPressure
  lambda : LambdaScale
  auditPassed : Bool
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  PROJECTION FUNCTIONS (Source → Coding)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Project SourceValue to CodingAtom using explicit normalization.
    No Float. Uses rational arithmetic via ofRatio.

    Example: diameter=2.2nm, maxExpected=4.0nm
    → normalized = 2.2/4.0 = 0.55 = ofRatio 22 40 -/
def projectToCoding (src : SourceValue) (maxExpected : Q16_16) : CodingAtom :=
  -- Convert Q16_16 values to rational representation
  let num := src.rawValue.val.toNat
  let den := maxExpected.val.toNat
  -- Use ofRatio for canonical projection
  CodingAtom.mk (Q0_64.ofRatio num den)
    s!"Projected {src.name} via normalization to max {den}"

/-- Convenience: direct rational projection with provenance -/
def codingFromRatio (num : Nat) (den : Nat) (prov : String) : CodingAtom :=
  CodingAtom.mk (Q0_64.ofRatio num den) prov

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  GEOMETRIC EMBEDDING (Coding → Surface)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Map coding atom to surface coordinate (simple 2D embedding) -/
def embedToSurface2D (atom : CodingAtom) (cellId : String) : SurfaceCoordinate :=
  { x := atom,
    y := CodingAtom.mk (Q0_64.ofRatio 5 10) "embedded_y",  -- 0.5
    z := none,
    cellId := cellId
  }

/-- Create perturbation direction between two coordinates -/
def makePerturbation (start end_ : SurfaceCoordinate) (rank : Nat)
    (phiEstimate : CodingAtom) : PerturbationDirection :=
  { directionId := s!"pert_{start.cellId}_{end_.cellId}",
    basisRank := rank,
    startCoord := start,
    endCoord := end_,
    invariantPreservation := phiEstimate
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  COLLAPSE OPERATORS (The Search Target for LLM)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Identity collapse (baseline): no compression -/
def identityCollapse : CollapseOperator :=
  { name := "identity",
    inputDims := 64,
    outputDims := 64,
    embedding := fun atom => embedToSurface2D atom "identity_cell",
    basis := [],  -- No perturbation directions
    collapse := fun coord => coord.x  -- Pass through
  }

/-- Example: Low-rank collapse operator template.
    LLM must fill in the actual collapse logic. -/
def lowRankCollapseTemplate (rank : Nat) : CollapseOperator :=
  { name := s!"low_rank_{rank}",
    inputDims := 512,
    outputDims := 64,
    embedding := fun atom => embedToSurface2D atom "low_rank_cell",
    basis := [makePerturbation
                (embedToSurface2D (codingFromRatio 1 10 "start") "start")
                (embedToSurface2D (codingFromRatio 9 10 "end") "end")
                rank
                (codingFromRatio 95 100 "phi_0.95")],
    collapse := fun coord => coord.x  -- TODO: LLM implements actual collapse
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  DELTA-PHI-GAMMA-LAMBDA AUDIT
-- ═══════════════════════════════════════════════════════════════════════════

/-- Run Δφγλ audit on a collapse operator -/
def runDpglAudit
    (op : CollapseOperator)
    (input : CodingAtom)
    (output : CodingAtom)
    (pressure : GammaPressure)
    (scale : LambdaScale) : DeltaPhiGammaLambdaAudit :=
  let deltaMag := Q0_64.sub input.value output.value |> Q0_64.abs
  let delta := DeltaResidual.mk
    s!"Change from {op.inputDims} to {op.outputDims} dims"
    (CodingAtom.mk deltaMag "delta_calc")
    (some "auto_delta")
  let phi := PhiInvariant.mk
    "Structural invariants preserved"
    (deltaMag < Q0_64.ofRatio 1 10)  -- threshold 0.1
    (some "phi_check")
  DeltaPhiGammaLambdaAudit.mk delta phi pressure scale phi.preserved

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  WARDEN VALIDATION
-- ═══════════════════════════════════════════════════════════════════════════

inductive WardenEmission where
  | planetwavesMediumViolation  -- No medium declared for compression
  | esAnalogyOverclaim          -- Using ES as proof instead of analogue
  | missingProjectionReceipt    -- Source→Coding without normalization
  | codingAtomTypeViolation     -- Field marked coding but not Q0_64
  | floatInCanonical            -- Float used in hot path
  | deltaUnbounded              -- Residual exceeds threshold
  | phiNotPreserved             -- Invariant failed
  | missingReverseCollapse      -- No recovery path
  | lowRankBasisFailure         -- Perturbation basis invalid
  | compressionFailed           -- Operator did not achieve target
  deriving BEq, DecidableEq, Repr, Inhabited

structure WardenValidation where
  passed : Bool
  emissions : List WardenEmission
  requiredHolds : Bool
  deriving Repr, Inhabited

/-- Validate operator against Warden rules -/
def wardenValidate (op : CollapseOperator) (audit : DeltaPhiGammaLambdaAudit)
    : WardenValidation :=
  let emissions : List WardenEmission := []
  -- Check 1: Delta bounded
  let emissions := if audit.delta.magnitude.value > Q0_64.ofRatio 15 100
    then WardenEmission.deltaUnbounded :: emissions else emissions
  -- Check 2: Phi preserved
  let emissions := if !audit.phi.preserved
    then WardenEmission.phiNotPreserved :: emissions else emissions
  -- Check 3: Has basis directions (structured, not random)
  let emissions := if op.basis == []
    then WardenEmission.lowRankBasisFailure :: emissions else emissions
  { passed := emissions == [],
    emissions := emissions,
    requiredHolds := emissions != []
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  BENCHMARK PROTOCOL
-- ═══════════════════════════════════════════════════════════════════════════

structure BenchmarkResult where
  operatorName : String
  inputSize : Nat
  outputSize : Nat
  compressionRatio : Q0_64
  dpglAudit : DeltaPhiGammaLambdaAudit
  wardenResult : WardenValidation
  baselineComparison : String
  deriving Repr, Inhabited

/-- Compare geometric compression vs symbolic baseline -/
def runBenchmark
    (geometricOp : CollapseOperator)
    (symbolicSize : Nat)  -- Baseline compressed size
    (testInput : CodingAtom)
    : BenchmarkResult :=
  let output := geometricOp.collapse (geometricOp.embedding testInput)
  let audit := runDpglAudit geometricOp testInput output
    { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 5 10) "gamma_0.5",
      description := "Standard compression pressure" }
    { scaleDescription := "64-block code system",
      byteSpan := some 64,
      temporalWindow := none }
  let warden := wardenValidate geometricOp audit
  let ratio := Q0_64.ofRatio geometricOp.outputDims geometricOp.inputDims
  { operatorName := geometricOp.name,
    inputSize := geometricOp.inputDims,
    outputSize := geometricOp.outputDims,
    compressionRatio := ratio,
    dpglAudit := audit,
    wardenResult := warden,
    baselineComparison := s!"Symbolic baseline: {symbolicSize} bytes"
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  N-VOXEL GEOMETRY (Dimension-Parameterized Cells)
-- ═══════════════════════════════════════════════════════════════════════════

/-- N-Voxel: A dimension-parameterized volumetric cell primitive.
    Generalizes voxel across dimension. Used in Geometry-Space for
    representing compressed or partially compressed geometric states.

    Hierarchy:
    - Goxel: pre-compression / shape-agnostic manifold primitive
    - Voxel: compressed 3D cell
    - N-Voxel: compressed n-dimensional cell (dimension is a parameter)
    - Surface: rendered projection of Goxel / voxel / n-voxel states

    Note: No Inhabited deriving because of proof field hRefl.
    -/
structure NVoxel (n : Nat) where
  dimensions : Nat
  hRefl : dimensions = n  -- Proof that dimension matches parameter
  cellId : String
  coordinates : Array CodingAtom  -- n coordinates in Q0_64
  occupancy : CodingAtom  -- 0 = empty, 1 = full
  deriving Repr

/-- 3D voxel (specialized n-voxel) -/
structure Voxel3D where
  x : CodingAtom
  y : CodingAtom
  z : CodingAtom
  cellId : String
  occupancy : CodingAtom
  deriving Repr, Inhabited

/-- Convert 3D voxel to n-voxel -/
def voxel3DToNVoxel (v : Voxel3D) : NVoxel 3 :=
  { dimensions := 3,
    hRefl := rfl,
    cellId := v.cellId,
    coordinates := #[v.x, v.y, v.z],
    occupancy := v.occupancy }

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  AUTOPOIETIC MONITOR (Level 1: Bounded Self-Maintenance)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Failure patterns recognized by the workspace monitor.
    Autopoietic-GCL is not self-replication. It is bounded self-maintenance
    of a compression workspace: observing Warden emissions and proposing
    repair candidates. All repairs remain in HOLD state.
    -/
inductive FailurePattern where
  | deltaUnbounded
  | phiNotPreserved
  | gammaTooAggressive
  | lambdaMismatch
  | reverseCollapseFailed
  | aliasPolicyMissing
  | lowRankBasisFailure
  | normalizationAmbiguous
  | signConventionAmbiguous
  | biologicalOverclaim
  | projectionProofConfusion
  deriving Repr, DecidableEq, BEq, Inhabited

/-- A repair proposal generated from observed failure patterns.
    This is NOT an accepted repair. It is a HOLD-state candidate.

    Warden Rule: Autopoietic repair proposals must never promote themselves.
    if repair_proposal.generated_by == workspace_autopoiesis:
      claim_state = HOLD
      require external benchmark or second independent review before promotion
    -/
structure RepairProposal where
  pattern : FailurePattern
  suggestedAction : String
  targetOperatorId : String
  expectedEffect : String
  wardenStatus : String := "HOLD"
  receiptRequired : String
  deriving Repr, Inhabited

/-- Autopoietic monitor for the geometric compression workspace.
    Observes Warden emissions and proposes bounded repairs.
    Does not self-validate or self-promote. -/
structure WorkspaceAutopoiesis where
  failurePatterns : List FailurePattern
  repairProposals : List RepairProposal
  selfModificationReceipt : String
  convergenceCheck : CodingAtom
  deriving Repr, Inhabited

/-- Generate repair proposal from failure pattern.
    All proposals remain in HOLD state until external validation. -/
def proposeRepairForPattern (p : FailurePattern) : RepairProposal :=
  match p with
  | .deltaUnbounded =>
      { pattern := p,
        suggestedAction := "Reduce gamma pressure or increase lambda resolution.",
        targetOperatorId := "collapse_operator",
        expectedEffect := "Lower residual delta.",
        receiptRequired := "DeltaPhiAuditReceipt" }
  | .phiNotPreserved =>
      { pattern := p,
        suggestedAction := "Change embedding to preserve declared invariant phi.",
        targetOperatorId := "geometric_embedding",
        expectedEffect := "Improve invariant survival.",
        receiptRequired := "PhiSurvivalReceipt" }
  | .lowRankBasisFailure =>
      { pattern := p,
        suggestedAction := "Increase perturbation rank or switch basis family.",
        targetOperatorId := "low_rank_basis",
        expectedEffect := "Recover useful collapse direction.",
        receiptRequired := "BaselineComparisonReceipt" }
  | .normalizationAmbiguous =>
      { pattern := p,
        suggestedAction := "Require explicit source-to-Q0_64 normalization map.",
        targetOperatorId := "coding_projection",
        expectedEffect := "Remove hidden scaling ambiguity.",
        receiptRequired := "NormalizationReceipt" }
  | .signConventionAmbiguous =>
      { pattern := p,
        suggestedAction := "Declare unsigned or signed Q0_64 coding convention.",
        targetOperatorId := "coding_atom",
        expectedEffect := "Prevent signed/unsigned drift.",
        receiptRequired := "TypeBoundaryReceipt" }
  | .biologicalOverclaim =>
      { pattern := p,
        suggestedAction := "Downgrade to analogy-bounded external reference surface.",
        targetOperatorId := "bio_gcl_surface",
        expectedEffect := "Prevent biology metaphor from becoming evidence.",
        receiptRequired := "SourceAuditReceipt" }
  | .projectionProofConfusion =>
      { pattern := p,
        suggestedAction := "Separate render projection from proof/canonical layer.",
        targetOperatorId := "surface_projection",
        expectedEffect := "Prevent visualization from being treated as validation.",
        receiptRequired := "ProjectionBoundaryReceipt" }
  | _ =>
      { pattern := p,
        suggestedAction := "Hold for manual Warden review.",
        targetOperatorId := "unknown",
        expectedEffect := "Avoid unsafe automatic repair.",
        receiptRequired := "HumanReviewReceipt" }

/-- Classify Warden emission into failure pattern for autopoiesis -/
def classifyWardenEmission (e : WardenEmission) : FailurePattern :=
  match e with
  | .deltaUnbounded => .deltaUnbounded
  | .phiNotPreserved => .phiNotPreserved
  | .lowRankBasisFailure => .lowRankBasisFailure
  | .planetwavesMediumViolation => .biologicalOverclaim
  | .esAnalogyOverclaim => .biologicalOverclaim
  | .missingProjectionReceipt => .normalizationAmbiguous
  | .codingAtomTypeViolation => .signConventionAmbiguous
  | .floatInCanonical => .normalizationAmbiguous
  | .missingReverseCollapse => .reverseCollapseFailed
  | .compressionFailed => .gammaTooAggressive

/-- Build autopoiesis state from Warden validation result -/
def buildAutopoiesis (warden : WardenValidation) (receipt : String) : WorkspaceAutopoiesis :=
  let patterns := warden.emissions.map classifyWardenEmission
  let proposals := patterns.map proposeRepairForPattern
  let convergenceValue := if warden.passed then Q0_64.ofRatio 9 10 else Q0_64.ofRatio 1 10
  { failurePatterns := patterns,
    repairProposals := proposals,
    selfModificationReceipt := receipt,
    convergenceCheck := CodingAtom.mk convergenceValue "convergence"
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §9.5  ADVERSARIAL TRIAL (Process / Receipt Layer)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Warden promotion authority states.
    AdversarialTrial tests operators but may not self-promote. -/
inductive WardenStatus where
  | HOLD        -- Under review, no promotion
  | REVIEWED    -- External review completed, receipt required for promotion
  | BLOCKED     -- Promotion denied, Warden emission recorded
  | CANDIDATE   -- Passed adversarial trial, awaiting external proof receipt
  deriving BEq, DecidableEq, Repr, Inhabited

/-- AdversarialTrial tests whether a proposed collapse operator survives
    an explicitly constructed contra-operator.

    Doctrine: The workspace gains dynamic trial execution as an object of audit,
    but does not gain operator mutation authority.

    It may emit: surviving phi, delta residue, bounded synthesis, Warden status.
    It may not: rewrite the operator set, promote itself to proof, silently repair.

    Pipeline:
      CollapseOperator -> FailurePattern -> AdversarialTrial
        -> surviving φ / Δ residue -> RepairProposal -> WardenStatus
    -/
structure AdversarialTrial where
  thesisOperator : CollapseOperator       -- Proposed compression
  contraOperator : CollapseOperator       -- Counter-example generator
  phiThesis : PhiInvariant                -- Invariant thesis claims
  phiContra : PhiInvariant                -- Invariant contra claims
  gammaPressure : GammaPressure           -- Forcing intensity
  lambdaScale : LambdaScale               -- Scale band
  synthesis : DeltaPhiGammaLambdaAudit    -- What survived both
  repairProposal : Option RepairProposal  -- Generated repair if applicable
  status : WardenStatus                   -- Trial outcome state
  deriving Inhabited

/-- Proof receipt gate for AdversarialTrial.
    Delegates to ReceiptCore.hasProofReceipt over an externally supplied
    receipt list. The workspace never self-issues proof receipts.

    A trial must be paired with receipts via promoteTrial before it can
    achieve REVIEWED status. -/
def hasProofReceipt
    (receipts : List ReceiptCore.Receipt)
    (targetId : String) : Bool :=
  ReceiptCore.hasProofReceipt receipts targetId

/-- Promote a trial from CANDIDATE to REVIEWED if receipts satisfy the gate.
    Returns the trial unchanged if promotion criteria are not met.

    Uses `match` on status so the proof of `promoteTrial_preserves_receipt_gate`
    reduces cleanly by `simp [promoteTrial]`. -/
def promoteTrial
    (trial : AdversarialTrial)
    (receipts : List ReceiptCore.Receipt)
    (targetId : String) : AdversarialTrial :=
  match trial.status with
  | WardenStatus.CANDIDATE =>
    if hasProofReceipt receipts targetId then
      { trial with status := WardenStatus.REVIEWED }
    else
      trial
  | _ => trial

/-- Promotion invariant: promoteTrial only produces REVIEWED when
    the receipt gate is satisfied.

    This theorem is provable by definition of promoteTrial: the only
    way a CANDIDATE trial becomes REVIEWED is through the hasProofReceipt gate. -/
theorem promoteTrial_preserves_receipt_gate
    (trial : AdversarialTrial)
    (receipts : List ReceiptCore.Receipt)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.CANDIDATE)
    (hReviewed : (promoteTrial trial receipts targetId).status = WardenStatus.REVIEWED) :
    hasProofReceipt receipts targetId = true := by
  by_cases h : hasProofReceipt receipts targetId
  · -- h : hasProofReceipt = true
    exact h
  · -- h : hasProofReceipt = false, but REVIEWED was produced, contradiction
    have h2 : (promoteTrial trial receipts targetId).status = WardenStatus.CANDIDATE := by
      rw [show promoteTrial trial receipts targetId = trial by
        unfold promoteTrial
        rw [hCandidate]
        simp [h]]
      rw [hCandidate]
    rw [h2] at hReviewed
    exfalso
    have hNe : WardenStatus.CANDIDATE ≠ WardenStatus.REVIEWED := by decide
    exact hNe hReviewed

/-- Ledger-backed promotion: promotes using receipts drawn from a persistent ledger.
    This is the external boundary: the workspace references the ledger,
    but never self-writes to it. -/
def promoteTrialLedger
    (trial : AdversarialTrial)
    (ledger : ReceiptCore.ReceiptLedger)
    (targetId : String) : AdversarialTrial :=
  promoteTrial trial (ReceiptCore.ledgerLookup ledger targetId) targetId

/-- Ledger invariant: a trial promoted via the ledger must satisfy the ledger's
    proof-receipt gate. This connects the persistent receipt store to the
    transient trial state. -/
theorem promoteTrialLedger_preserves_invariant
    (trial : AdversarialTrial)
    (ledger : ReceiptCore.ReceiptLedger)
    (targetId : String)
    (hCandidate : trial.status = WardenStatus.CANDIDATE)
    (hReviewed : (promoteTrialLedger trial ledger targetId).status = WardenStatus.REVIEWED) :
    ReceiptCore.ledgerHasProofReceipt ledger targetId = true := by
  simp [promoteTrialLedger, ReceiptCore.ledgerHasProofReceipt] at hReviewed ⊢
  exact promoteTrial_preserves_receipt_gate trial (ReceiptCore.ledgerLookup ledger targetId) targetId hCandidate hReviewed

/-- Run adversarial trial: thesis vs contra, emit surviving structure.
    Trial generates an audit receipt; it does not modify operators.

    On successful survival, status is always CANDIDATE (not REVIEWED).
    Promotion to REVIEWED requires external receipts via promoteTrial. -/
def runAdversarialTrial
    (thesis : CollapseOperator)
    (contra : CollapseOperator)
    (input : CodingAtom)
    (pressure : GammaPressure)
    (scale : LambdaScale) : AdversarialTrial :=
  let thesisOutput := thesis.collapse (thesis.embedding input)
  let contraOutput := contra.collapse (contra.embedding input)
  let auditThesis := runDpglAudit thesis input thesisOutput pressure scale
  let auditContra := runDpglAudit contra input contraOutput pressure scale
  -- Synthesis: what survived both thesis and contra
  let survivedPhi := auditThesis.phi.preserved && auditContra.phi.preserved
  let synthesis :=
    { delta := auditThesis.delta,
      phi := { invariantDescription := "Adversarial synthesis: thesis AND contra survived",
               preserved := survivedPhi,
               proofReceipt := some "adversarial_trial_auto" },
      gamma := pressure,
      lambda := scale,
      auditPassed := survivedPhi }
  -- Generate repair proposal only if trial failed
  let repair := if !survivedPhi then
    some { pattern := FailurePattern.phiNotPreserved,
           suggestedAction := "Thesis failed contra-surface; redesign embedding or collapse.",
           targetOperatorId := thesis.name,
           expectedEffect := "Improve invariant survival under adversarial pressure.",
           receiptRequired := "AdversarialSynthesisReceipt" }
    else none
  -- Status: HOLD on failure, CANDIDATE on survival. REVIEWED only via promoteTrial.
  let status := if !survivedPhi then WardenStatus.HOLD else WardenStatus.CANDIDATE
  { thesisOperator := thesis,
    contraOperator := contra,
    phiThesis := auditThesis.phi,
    phiContra := auditContra.phi,
    gammaPressure := pressure,
    lambdaScale := scale,
    synthesis := synthesis,
    repairProposal := repair,
    status := status }

-- ═══════════════════════════════════════════════════════════════════════════
-- §10  THEOREMS
-- ═══════════════════════════════════════════════════════════════════════════

-- TODO(lean-port): Theorem projectionOrdering
-- Projection preserves ordering for positive values.
-- Proof relies on ofRatio preserving ordering for positive args.
-- theorem projectionOrdering (s1 s2 : SourceValue) (max : Q16_16)
--     (h1 : s1.rawValue.val > 0) (h2 : s2.rawValue.val > 0)
--     (h3 : s1.rawValue.val < s2.rawValue.val) :
--     (projectToCoding s1 max).value.val < (projectToCoding s2 max).value.val := by
--   sorry

-- ═══════════════════════════════════════════════════════════════════════════
-- §11  #eval WITNESSES
-- ═══════════════════════════════════════════════════════════════════════════

-- Source-Space examples (PlanetWaves analogy)
def titanWaveHeight : SourceValue :=
  { name := "wave_height", rawValue := Q16_16.ofRatio 10 1, unit := "feet",
    measurementProvenance := "Titan methane lake simulation" }

def lavaWaveHeight : SourceValue :=
  { name := "wave_height", rawValue := Q16_16.ofRatio 1 10, unit := "feet",
    measurementProvenance := "55 Cancri e lava ocean" }

-- Coding-Space projections
#eval (projectToCoding titanWaveHeight (Q16_16.ofRatio 20 1)).value
#eval (projectToCoding lavaWaveHeight (Q16_16.ofRatio 20 1)).value

-- Surface embedding
#eval embedToSurface2D (codingFromRatio 5 10 "test") "cell_0"

-- N-Voxel
def testVoxel3D : Voxel3D :=
  { x := CodingAtom.mk Q0_64.one "test",
    y := CodingAtom.mk Q0_64.half "test",
    z := CodingAtom.mk Q0_64.zero "test",
    cellId := "voxel_0",
    occupancy := CodingAtom.mk Q0_64.one "test" }

#eval (voxel3DToNVoxel testVoxel3D).dimensions

-- Low-rank operator template
#eval (lowRankCollapseTemplate 4).name
#eval (lowRankCollapseTemplate 4).basis.length

-- Δφγλ Audit
#eval (runDpglAudit identityCollapse
  (codingFromRatio 8 10 "input")
  (codingFromRatio 8 10 "output")
  { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 3 10) "gamma",
    description := "test" }
  { scaleDescription := "test", byteSpan := none, temporalWindow := none }).auditPassed

-- Autopoietic: Failure pattern to repair proposal
#eval (proposeRepairForPattern FailurePattern.deltaUnbounded).wardenStatus
#eval (proposeRepairForPattern FailurePattern.biologicalOverclaim).targetOperatorId
#eval (proposeRepairForPattern FailurePattern.lowRankBasisFailure).receiptRequired

-- Autopoietic: Build from Warden result
#eval (buildAutopoiesis
  { passed := false, emissions := [WardenEmission.deltaUnbounded, WardenEmission.phiNotPreserved],
    requiredHolds := true }
  "autopoiesis_test_001").failurePatterns.length

-- AdversarialTrial: WardenStatus
#eval WardenStatus.HOLD
#eval WardenStatus.CANDIDATE

-- AdversarialTrial: Run thesis vs identity (identity as contra baseline)
#eval (runAdversarialTrial identityCollapse identityCollapse
  (codingFromRatio 5 10 "test_input")
  { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 2 10) "low_pressure",
    description := "adversarial_test" }
  { scaleDescription := "identity_vs_identity", byteSpan := some 64, temporalWindow := none }).synthesis.auditPassed

-- AdversarialTrial: Status after thesis=contra (should be CANDIDATE or HOLD)
#eval (runAdversarialTrial identityCollapse identityCollapse
  (codingFromRatio 5 10 "test_input")
  { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 2 10) "low_pressure",
    description := "adversarial_test" }
  { scaleDescription := "identity_vs_identity", byteSpan := some 64, temporalWindow := none }).status

-- hasProofReceipt with no receipts → false
#eval hasProofReceipt [] "any_target"

-- hasProofReceipt with adversarialTrial + benchmark pair → true
#eval hasProofReceipt
  [ReceiptCore.adversarialTrialReceipt "op1" true, ReceiptCore.benchmarkReceipt "op1" true true] "op1"

-- hasProofReceipt with only adversarialTrial → false (needs benchmark pair)
#eval hasProofReceipt [ReceiptCore.adversarialTrialReceipt "op1" true] "op1"

-- promoteTrial: no receipts, stays CANDIDATE
#eval (promoteTrial
  (runAdversarialTrial identityCollapse identityCollapse
    (codingFromRatio 5 10 "test_input")
    { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 2 10) "low_pressure",
      description := "adversarial_test" }
    { scaleDescription := "identity_vs_identity", byteSpan := some 64, temporalWindow := none })
  [] "test_input").status

-- promoteTrial: with valid receipts → REVIEWED
#eval (promoteTrial
  (runAdversarialTrial identityCollapse identityCollapse
    (codingFromRatio 5 10 "test_input")
    { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 2 10) "low_pressure",
      description := "adversarial_test" }
    { scaleDescription := "identity_vs_identity", byteSpan := some 64, temporalWindow := none })
  [ReceiptCore.adversarialTrialReceipt "test_input" true,
   ReceiptCore.benchmarkReceipt "test_input" true true] "test_input").status

-- Warden validation
#eval (wardenValidate identityCollapse
  (runDpglAudit identityCollapse
    (codingFromRatio 8 10 "input")
    (codingFromRatio 7 10 "output")
    { pressureLevel := CodingAtom.mk (Q0_64.ofRatio 3 10) "gamma",
      description := "test" }
    { scaleDescription := "test", byteSpan := none, temporalWindow := none })).passed

-- Benchmark
#eval (runBenchmark identityCollapse 128
  (codingFromRatio 8 10 "test")).operatorName

end Semantics.GeometricCompressionWorkspace
