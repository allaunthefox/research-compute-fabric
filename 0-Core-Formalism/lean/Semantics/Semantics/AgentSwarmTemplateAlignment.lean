import Semantics.ReceiptCore

/-!
# Agent Swarm Template Alignment

This module translates external agent/swarm template patterns into the local
AGENTS.md contract:

* finite node kinds instead of open prompt routing;
* explicit evaluation and receipt gates;
* fail-closed `HOLD` when evidence is missing;
* invalid receipts force `BLOCKED`.

It does not import external template code and it does not claim that any web
demo is proof-bearing.  It only captures the admissibility surface needed before
such a template can influence the Research Stack.
-/

namespace Semantics.AgentSwarmTemplateAlignment

/-- Finite local classes for externally observed template shapes. -/
inductive TemplateClass where
  | singleAgent
  | supportTriage
  | researchReport
  | codeReviewPipeline
  | retrievalEvaluation
  | contentModeration
  deriving Repr, BEq, DecidableEq

/-- Finite node kinds admitted by the local adapter. -/
inductive TemplateNodeKind where
  | input
  | classifier
  | retriever
  | generator
  | evaluator
  | approver
  | synthesizer
  | output
  deriving Repr, BEq, DecidableEq

/-- Promotion state for a translated template. -/
inductive TemplateStatus where
  | HOLD
  | CANDIDATE
  | REVIEWED
  | BLOCKED
  deriving Repr, BEq, DecidableEq

/-- A local, finite representation of one external template pattern. -/
structure TemplateGraph where
  templateClass : TemplateClass
  nodes : List TemplateNodeKind
  requiresApproval : Bool
  hasEvaluationGate : Bool
  targetId : String
  deriving Repr, BEq

/-- Every translated graph must have input and output boundaries. -/
def hasBoundary (graph : TemplateGraph) : Bool :=
  graph.nodes.contains .input && graph.nodes.contains .output

/-- Any template that can affect users, code, or claims must include an evaluator. -/
def needsEvaluation (templateClass : TemplateClass) : Bool :=
  match templateClass with
  | .singleAgent => false
  | .supportTriage => true
  | .researchReport => true
  | .codeReviewPipeline => true
  | .retrievalEvaluation => true
  | .contentModeration => true

/-- Human approval is mandatory for user-visible operational actions. -/
def needsApproval (templateClass : TemplateClass) : Bool :=
  match templateClass with
  | .supportTriage => true
  | .contentModeration => true
  | _ => false

/-- Required receipts for promotion beyond HOLD. -/
def requiredReceiptKinds (templateClass : TemplateClass) : List ReceiptCore.ReceiptKind :=
  match templateClass with
  | .singleAgent => [.sourceAudit]
  | .supportTriage => [.sourceAudit, .humanReview]
  | .researchReport => [.sourceAudit, .humanReview]
  | .codeReviewPipeline => [.leanBuild, .sourceAudit]
  | .retrievalEvaluation => [.benchmark, .sourceAudit]
  | .contentModeration => [.sourceAudit, .humanReview, .wardenEmission]

/-- Structural lawfulness before receipts are considered. -/
def graphStructurallyLawful (graph : TemplateGraph) : Bool :=
  hasBoundary graph
  && (!needsEvaluation graph.templateClass || graph.hasEvaluationGate)
  && (!needsApproval graph.templateClass || graph.requiresApproval)

/-- Receipt gate for CANDIDATE promotion. -/
def hasPromotionReceipts
  (graph : TemplateGraph)
  (receipts : List ReceiptCore.Receipt) : Bool :=
  ReceiptCore.hasAllReceiptKinds receipts graph.targetId (requiredReceiptKinds graph.templateClass)

/-- Fail-closed status assignment. -/
def classifyTemplate
    (graph : TemplateGraph)
    (receipts : List ReceiptCore.Receipt) : TemplateStatus :=
  if ReceiptCore.isBlocked receipts graph.targetId then
    .BLOCKED
  else if !graphStructurallyLawful graph then
    .HOLD
  else if hasPromotionReceipts graph receipts then
    .CANDIDATE
  else
    .HOLD

/-- External templates never self-promote to REVIEWED in this adapter. -/
theorem classifyTemplateNeverReviewed (graph : TemplateGraph) (receipts : List ReceiptCore.Receipt) :
    classifyTemplate graph receipts != TemplateStatus.REVIEWED := by
  unfold classifyTemplate
  by_cases hBlocked : ReceiptCore.isBlocked receipts graph.targetId = true
  · simp [hBlocked]
    rfl
  · by_cases hNotLawful : (!graphStructurallyLawful graph) = true
    · simp [hBlocked, hNotLawful]
      rfl
    · by_cases hReceipts : hasPromotionReceipts graph receipts = true
      · simp [hBlocked, hNotLawful, hReceipts]
        rfl
      · simp [hBlocked, hNotLawful, hReceipts]
        rfl

/-- Missing receipts keep a structurally valid template in HOLD. -/
theorem noReceiptsHold (graph : TemplateGraph)
    (hLawful : graphStructurallyLawful graph = true) :
    classifyTemplate graph [] = TemplateStatus.HOLD := by
  unfold classifyTemplate hasPromotionReceipts
  cases graph with
  | mk templateClass nodes requiresApproval hasEvaluationGate targetId =>
    cases templateClass <;>
      simp [ReceiptCore.isBlocked, ReceiptCore.hasAllReceiptKinds,
        ReceiptCore.hasReceiptOfKind, hLawful, requiredReceiptKinds]

/-- Any invalid receipt for the target blocks the template. -/
theorem invalidReceiptBlocks (graph : TemplateGraph) (kind : ReceiptCore.ReceiptKind) :
    classifyTemplate graph
      [{ kind := kind
       , targetId := graph.targetId
       , summary := "failed validation"
       , valid := false
       , authority := "alignment_check"
       , timestamp := 0 }] = TemplateStatus.BLOCKED := by
  unfold classifyTemplate ReceiptCore.isBlocked
  simp

/-- A code-review pipeline with build and source-audit receipts becomes CANDIDATE. -/
def codeReviewGraph : TemplateGraph :=
  { templateClass := .codeReviewPipeline
  , nodes := [.input, .generator, .evaluator, .output]
  , requiresApproval := false
  , hasEvaluationGate := true
  , targetId := "agentswarms.code_review_pipeline" }

def codeReviewReceipts : List ReceiptCore.Receipt :=
  [ ReceiptCore.leanBuildReceipt codeReviewGraph.targetId true
  , { kind := .sourceAudit
    , targetId := codeReviewGraph.targetId
    , summary := "external template mapped to finite local node kinds"
    , valid := true
    , authority := "agent_swarm_alignment"
    , timestamp := 1 } ]

theorem codeReviewGraphCandidate :
    classifyTemplate codeReviewGraph codeReviewReceipts = TemplateStatus.CANDIDATE := by
  native_decide

/-- A support triage graph without human approval fails closed. -/
def unsafeSupportGraph : TemplateGraph :=
  { templateClass := .supportTriage
  , nodes := [.input, .classifier, .generator, .evaluator, .output]
  , requiresApproval := false
  , hasEvaluationGate := true
  , targetId := "agentswarms.support_triage" }

theorem unsafeSupportGraphHeld :
    classifyTemplate unsafeSupportGraph [] = TemplateStatus.HOLD := by
  native_decide

#eval graphStructurallyLawful codeReviewGraph
-- Expected: true

#eval classifyTemplate codeReviewGraph []
-- Expected: HOLD

#eval classifyTemplate codeReviewGraph codeReviewReceipts
-- Expected: CANDIDATE

#eval classifyTemplate unsafeSupportGraph []
-- Expected: HOLD

end Semantics.AgentSwarmTemplateAlignment
