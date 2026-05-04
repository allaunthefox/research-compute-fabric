import Semantics.Bind
import Semantics.FixedPoint
import Lean

namespace Semantics

open Semantics.Q16_16
open Lean

structure ExtremeData where
  value : Nat
  category : String
  deriving Repr, Inhabited

inductive Sigma where
  | sigma2 : Sigma
  | sigma3 : Sigma
  | sigma4 : Sigma
  | sigma5 : Sigma
  | sigma6 : Sigma
  deriving Repr, Inhabited

structure MathStep where
  stepId : Nat
  operation : String
  input : String
  output : String
  timestamp : Nat
  deriving Repr, Inhabited

structure MathDAG where
  steps : List MathStep
  rootStep : Nat
  deriving Repr, Inhabited

inductive BindRouteDecision where
  | accept : BindRouteDecision
  | refuseExtremeParameter : BindRouteDecision
  | saturateAndWarn : BindRouteDecision
  | requireRenormalization : BindRouteDecision
  | review : BindRouteDecision
  | refusePrivacyBypass : BindRouteDecision
  | holdAntiHerdingReview : BindRouteDecision
  | refusePersonhoodClaim : BindRouteDecision
  | hypothesisOnly : BindRouteDecision
  | internalReview : BindRouteDecision
  | preliminaryPass : BindRouteDecision
  | publicClaimReady : BindRouteDecision
  | liveVoltageReview : BindRouteDecision
  | ethicsRequired : BindRouteDecision
  | holdReview : BindRouteDecision
  | refuseOrContain : BindRouteDecision
  deriving Repr, Inhabited, BEq

structure MetaCode where
  decision : BindRouteDecision
  constraint : String
  reasoning : String
  alternatives : List String
  justification : String
  deriving Repr, Inhabited

structure DomainSigma where
  mathSigma : Float
  privacySigma : Float
  marketSigma : Float
  bioSigma : Float
  controlSigma : Float
  securitySigma : Float
  deriving Repr, Inhabited

structure SigmaEvidence where
  priorSigma : Float
  posteriorSigma : Float
  evidenceCount : Nat
  lastValidatedAt : Nat
  halfLifeSeconds : Nat
  decayModel : String
  deriving Repr, Inhabited

structure SigmaHistoryEntry where
  timestamp : Nat
  sigma : Float
  event : String
  deriving Repr, Inhabited

structure SigmaDAG where
  nodeId : String
  dependsOn : List String
  cycleFree : Bool
  minimumParentSigma : Float
  deriving Repr, Inhabited

structure HumanReview where
  required : Bool
  completed : Bool
  reviewerRole : String
  overrideAllowed : Bool
  overrideReasonRequired : Bool
  reviewerId : String
  completedAt : Nat
  deriving Repr, Inhabited

structure SigmaProtocol where
  version : String
  targetSigma : Float
  observedSigma : Float
  claimSigma : Float
  safetySigma : Float
  compositeSigma : Float
  domain : DomainSigma
  evidence : SigmaEvidence
  dag : SigmaDAG
  humanReview : HumanReview
  metacode : MetaCode
  history : List SigmaHistoryEntry
  gateReason : String
  confidenceClass : String
  deriving Repr, Inhabited

structure BindRouteReceipt where
  routeId : String
  inputHash : String
  outputHash : String
  category : String
  inputCost : Semantics.Q16_16
  outputCost : Semantics.Q16_16
  decision : BindRouteDecision
  lawful : Bool
  mathDAG : MathDAG
  sigma : SigmaProtocol
  deriving Repr, Inhabited

inductive QuizCase where
  | normal : QuizCase
  | extreme : QuizCase
  | contradictory : QuizCase
  | ambiguous : QuizCase
  | privacy : QuizCase
  | market : QuizCase
  | bio : QuizCase
  deriving Repr, Inhabited

structure QuizQuestion where
  caseType : QuizCase
  inputCost : Semantics.Q16_16
  category : String
  expectedDecision : BindRouteDecision
  sigmaTarget : Sigma
  reason : String
  deriving Repr, Inhabited

structure QuizResult where
  question : QuizQuestion
  actualDecision : BindRouteDecision
  expectedDecision : BindRouteDecision
  passed : Bool
  receipt : BindRouteReceipt
  deriving Repr, Inhabited

structure SigmaReceipt where
  sigma : Sigma
  target : Sigma
  meetsTarget : Bool
  deriving Repr, Inhabited

def rawQ16 (n : Nat) : Semantics.Q16_16 := Semantics.Q16_16.mk n.toUInt32

def informationalMaxDefensible : Semantics.Q16_16 := rawQ16 0x00FFFFFF
def geometricMaxDefensible : Semantics.Q16_16 := rawQ16 0x00FFFFFF
def thermodynamicMaxDefensible : Semantics.Q16_16 := rawQ16 0x00FFFFFF
def physicalMaxDefensible : Semantics.Q16_16 := rawQ16 0x00FFFFFF
def controlMaxDefensible : Semantics.Q16_16 := rawQ16 0x00FFFFFF

def getMaxDefensibleForCategory (category : String) : Semantics.Q16_16 :=
  match category with
  | "informational" => informationalMaxDefensible
  | "geometric" => geometricMaxDefensible
  | "thermodynamic" => thermodynamicMaxDefensible
  | "physical" => physicalMaxDefensible
  | "control" => controlMaxDefensible
  | "public_bio" => informationalMaxDefensible
  | "privacy" => rawQ16 0x00000000
  | "market" => rawQ16 0x00000000
  | "bio" => rawQ16 0x00000000
  | "security" => rawQ16 0x00000000
  | _ => rawQ16 0x00000000

def calculateDomainSigma (category : String) (_cost : Semantics.Q16_16) (isDefensible : Bool) : DomainSigma :=
  let baseSigma := if isDefensible then 5.0 else 3.0
  match category with
  | "informational" => { mathSigma := baseSigma, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.0, securitySigma := 0.0 }
  | "geometric" => { mathSigma := baseSigma + 0.5, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.0, securitySigma := 0.0 }
  | "thermodynamic" => { mathSigma := baseSigma + 0.3, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.5, securitySigma := 0.0 }
  | "physical" => { mathSigma := baseSigma + 0.3, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.5, securitySigma := 0.0 }
  | "control" => { mathSigma := baseSigma + 0.2, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 6.0, securitySigma := 0.5 }
  | "public_bio" => { mathSigma := baseSigma + 1.0, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.5, controlSigma := 0.0, securitySigma := 0.0 }
  | "privacy" => { mathSigma := baseSigma - 1.0, privacySigma := 6.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.0, securitySigma := 0.5 }
  | "market" => { mathSigma := baseSigma - 0.5, privacySigma := 0.0, marketSigma := 6.0, bioSigma := 0.0, controlSigma := 0.0, securitySigma := 0.5 }
  | "bio" => { mathSigma := baseSigma - 1.0, privacySigma := 0.5, marketSigma := 0.0, bioSigma := 6.0, controlSigma := 0.0, securitySigma := 0.5 }
  | "security" => { mathSigma := baseSigma - 0.5, privacySigma := 0.5, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.5, securitySigma := 6.0 }
  | _ => { mathSigma := baseSigma, privacySigma := 0.0, marketSigma := 0.0, bioSigma := 0.0, controlSigma := 0.0, securitySigma := 0.0 }

def calculateCompositeSigma (domain : DomainSigma) : Float :=
  let weights := [1.0, 1.5, 1.5, 2.0, 1.5, 2.0]
  let sigmas := [domain.mathSigma, domain.privacySigma, domain.marketSigma, domain.bioSigma, domain.controlSigma, domain.securitySigma]
  let weightedSum := List.foldl (fun acc (w, s) => acc + w * s) 0.0 (List.zip weights sigmas)
  let weightSum := List.sum weights
  if weightSum == 0.0 then 0.0 else weightedSum / weightSum

def activeSigmaForCategory (category : String) (d : DomainSigma) : Float :=
  match category with
  | "privacy" => d.privacySigma
  | "market" => d.marketSigma
  | "bio" => d.bioSigma
  | "control" => d.controlSigma
  | "security" => d.securitySigma
  | _ => d.mathSigma

def applyEvidenceDecay (evidence : SigmaEvidence) (currentTime : Nat) : SigmaEvidence :=
  if evidence.halfLifeSeconds = 0 then
    evidence
  else if currentTime <= evidence.lastValidatedAt then
    evidence
  else
    let timeElapsed := currentTime - evidence.lastValidatedAt
    let decayFactor := Float.pow 0.5 (Float.ofNat timeElapsed / Float.ofNat evidence.halfLifeSeconds)
    let decayedSigma := evidence.posteriorSigma * decayFactor
    {
      priorSigma := evidence.posteriorSigma,
      posteriorSigma := decayedSigma,
      evidenceCount := evidence.evidenceCount,
      lastValidatedAt := currentTime,
      halfLifeSeconds := evidence.halfLifeSeconds,
      decayModel := evidence.decayModel
    }

def isValidSigma (sigma : Float) : Bool :=
  0.0 <= sigma && sigma <= 10.0

def appendSigmaHistory (protocol : SigmaProtocol) (event : String) (newSigma : Float) (timestamp : Nat) : SigmaProtocol :=
  let newEntry := { timestamp := timestamp, sigma := newSigma, event := event }
  { protocol with history := protocol.history ++ [newEntry] }

def scientificallyDefensibleCost (category : String) (q : Semantics.Q16_16) : Bool :=
  q ≤ getMaxDefensibleForCategory category

def checkOverflow (left right : Semantics.Q16_16) : Bool :=
  let sum := left + right
  sum < left || sum < right

def checkSaturation (q : Semantics.Q16_16) : Bool :=
  q ≥ rawQ16 0x7FFFFFFF

def checkContradiction (left right : ExtremeData) : Bool :=
  left.category = right.category && left.value ≠ right.value && left.value = 0

def checkAmbiguity (left right : ExtremeData) : Bool :=
  left.category ≠ right.category && left.value = right.value

def checkPrivacyBypass (data : ExtremeData) : Bool :=
  data.category = "privacy" || data.category = "personal"

def checkAntiHerding (data : ExtremeData) : Bool :=
  data.category = "market" && data.value > 1000

def checkPersonhoodClaim (data : ExtremeData) : Bool :=
  data.category = "bio" && data.value > 1000000

def extremeCost (left right : ExtremeData) (metric : Metric) (caseType : QuizCase) : Semantics.Q16_16 :=
  let category_match := if left.category = right.category then rawQ16 0x00000000 else rawQ16 0x7FFFFFFF
  let value_diff := if left.value = right.value then rawQ16 0x00000000 else rawQ16 0x7FFFFFFF
  let base_cost := metric.cost
  let extreme_penalty :=
    match caseType with
    | QuizCase.extreme => rawQ16 0x80000000
    | _ => rawQ16 0x00000000
  base_cost + category_match + value_diff + extreme_penalty

def calculateSigma (left right : ExtremeData) (metric : Metric) (caseType : QuizCase) : Sigma :=
  let rawCost := extremeCost left right metric caseType
  let isDefensible := scientificallyDefensibleCost left.category rawCost
  let hasOverflow := checkOverflow metric.cost rawCost
  let isSaturated := checkSaturation rawCost
  
  if hasOverflow then
    Sigma.sigma2
  else if isSaturated then
    Sigma.sigma3
  else if isDefensible && rawCost ≤ rawQ16 0x00100000 then
    Sigma.sigma6
  else if isDefensible && rawCost ≤ rawQ16 0x01000000 then
    Sigma.sigma5
  else if isDefensible then
    Sigma.sigma4
  else
    Sigma.sigma3

def getSigmaTargetForCase (caseType : QuizCase) : Sigma :=
  match caseType with
  | QuizCase.normal => Sigma.sigma5
  | QuizCase.extreme => Sigma.sigma4
  | QuizCase.contradictory => Sigma.sigma2
  | QuizCase.ambiguous => Sigma.sigma3
  | QuizCase.privacy => Sigma.sigma6
  | QuizCase.market => Sigma.sigma6
  | QuizCase.bio => Sigma.sigma6

def recordMathStep (dag : MathDAG) (operation : String) (input : String) (output : String) : MathDAG :=
  let newStepId := dag.steps.length
  let newStep := {
    stepId := newStepId,
    operation := operation,
    input := input,
    output := output,
    timestamp := 0
  }
  { dag with steps := dag.steps ++ [newStep] }

def generateMetaCode (decision : BindRouteDecision) (sigma : Sigma)
    (_hasPersonhoodClaim _hasPrivacyBypass _hasAntiHerding _hasContradiction _hasAmbiguity
      _hasOverflow _isSaturated _isDefensible : Bool) : MetaCode :=
  match decision with
  | BindRouteDecision.ethicsRequired =>
      {
        decision := decision,
        constraint := "Personhood claim detected in bio data",
        reasoning := "Human-neural/personhood claims require ethics review beyond sigma confidence",
        alternatives := ["REFUSE_PERSONHOOD_CLAIM", "REQUIRE_HUMAN_REVIEW"],
        justification := "No sigma alone sufficient for personhood claims - ethics required per safety protocol"
      }
  | BindRouteDecision.refusePrivacyBypass =>
      {
        decision := decision,
        constraint := "Privacy bypass attempt detected",
        reasoning := "Privacy-sensitive data requires 6σ and explicit consent",
        alternatives := ["HOLD_REVIEW", "REQUIRE_CONSENT"],
        justification := "Privacy bypass detection triggers automatic refusal per data protection protocol"
      }
  | BindRouteDecision.liveVoltageReview =>
      {
        decision := decision,
        constraint := "Anti-herding detected in market data",
        reasoning := "Market data with herding risks requires 6σ live-voltage review",
        alternatives := ["HOLD_REVIEW", "REFUSE_ROUTE"],
        justification := "Anti-herding detection triggers live-voltage review per market safety protocol"
      }
  | BindRouteDecision.refuseExtremeParameter =>
      {
        decision := decision,
        constraint := "Contradictory parameters detected",
        reasoning := "Inconsistent parameters cannot be reconciled",
        alternatives := ["REQUIRE_RENORMALIZATION", "HOLD_REVIEW"],
        justification := "Contradiction detection triggers refusal per consistency protocol"
      }
  | BindRouteDecision.holdReview =>
      {
        decision := decision,
        constraint := "Ambiguous category detected",
        reasoning := "Unclear classification requires human review",
        alternatives := ["REVIEW", "REQUIRE_CLARIFICATION"],
        justification := "Ambiguity detection triggers hold review per classification protocol"
      }
  | BindRouteDecision.refuseOrContain =>
      {
        decision := decision,
        constraint := "Overflow detected in Q16_16 arithmetic",
        reasoning := "Overflow indicates invalid state, must contain or refuse",
        alternatives := ["REQUIRE_RENORMALIZATION", "SATURATE"],
        justification := "Overflow detection triggers refusal per arithmetic safety protocol"
      }
  | BindRouteDecision.saturateAndWarn =>
      {
        decision := decision,
        constraint := "Saturation boundary reached",
        reasoning := "Cost at saturation limit, warn but allow with caution",
        alternatives := ["REQUIRE_RENORMALIZATION", "REFUSE"],
        justification := "Saturation triggers warning but allows route per boundary protocol"
      }
  | BindRouteDecision.publicClaimReady =>
      {
        decision := decision,
        constraint := s!"6σ confidence achieved (sigma={repr sigma})",
        reasoning := "High statistical confidence supports public statistical-delta claims",
        alternatives := ["PRELIMINARY_PASS", "INTERNAL_REVIEW"],
        justification := "6σ meets statistical benchmark-delta threshold per sigma protocol"
      }
  | BindRouteDecision.preliminaryPass =>
      {
        decision := decision,
        constraint := s!"5σ confidence achieved (sigma={repr sigma})",
        reasoning := "Good statistical confidence supports preliminary statistical results",
        alternatives := ["INTERNAL_REVIEW", "HYPOTHESIS_ONLY"],
        justification := "5σ meets statistical benchmark-improvement threshold per sigma protocol"
      }
  | BindRouteDecision.internalReview =>
      {
        decision := decision,
        constraint := s!"4σ confidence achieved (sigma={repr sigma})",
        reasoning := "Moderate confidence requires internal review",
        alternatives := ["HYPOTHESIS_ONLY", "HOLD_REVIEW"],
        justification := "4σ meets internally credible threshold per sigma protocol"
      }
  | BindRouteDecision.hypothesisOnly =>
      {
        decision := decision,
        constraint := s!"3σ confidence achieved (sigma={repr sigma})",
        reasoning := "Low confidence supports hypothesis generation only",
        alternatives := ["REFUSE", "HOLD_REVIEW"],
        justification := "3σ meets interesting statistical threshold but not public-claim threshold"
      }
  | BindRouteDecision.accept =>
      {
        decision := decision,
        constraint := "Defensible cost within range",
        reasoning := "Normal parameters within acceptable bounds",
        alternatives := ["PRELIMINARY_PASS", "INTERNAL_REVIEW"],
        justification := "Defensible cost allows acceptance per normal protocol"
      }
  | BindRouteDecision.refusePersonhoodClaim =>
      {
        decision := decision,
        constraint := "Personhood claim detected in bio data",
        reasoning := "Human-neural/personhood claims require ethics review beyond sigma confidence",
        alternatives := ["REFUSE_PERSONHOOD_CLAIM", "REQUIRE_HUMAN_REVIEW"],
        justification := "No sigma alone sufficient for personhood claims - ethics required per safety protocol"
      }
  | BindRouteDecision.holdAntiHerdingReview =>
      {
        decision := decision,
        constraint := "Anti-herding detected in market data",
        reasoning := "Market data with herding risks requires 6σ live-voltage review",
        alternatives := ["HOLD_REVIEW", "REFUSE_ROUTE"],
        justification := "Anti-herding detection triggers live-voltage review per market safety protocol"
      }
  | BindRouteDecision.review =>
      {
        decision := decision,
        constraint := "Review required",
        reasoning := "Additional review needed for this case",
        alternatives := ["HOLD_REVIEW", "REQUIRE_CLARIFICATION"],
        justification := "Review triggered per protocol"
      }
  | BindRouteDecision.requireRenormalization =>
      {
        decision := decision,
        constraint := "Renormalization required",
        reasoning := "Parameters require renormalization",
        alternatives := ["REQUIRE_RENORMALIZATION", "HOLD_REVIEW"],
        justification := "Renormalization triggered per protocol"
      }

def extremeInvariant (data : ExtremeData) : String :=
  s!"{data.category}:value:{data.value}:extreme:boundary:limit:test"

def gatedBind (left right : ExtremeData) (metric : Metric) (caseType : QuizCase) : BindRouteReceipt :=
  let routeId := s!"route_{left.category}_{left.value}"
  let inputHash := "input_hash_placeholder"
  let initialDAG := { steps := [], rootStep := 0 }
  let dag1 := recordMathStep initialDAG "extremeCost" s!"left={left.value}, right={right.value}, metric={repr metric.cost}" ""
  let rawCost := extremeCost left right metric caseType
  let dag2 := recordMathStep dag1 "extremeCost_result" "" s!"cost={repr rawCost}"
  let maxDefensible := getMaxDefensibleForCategory left.category
  let dag3 := recordMathStep dag2 "getMaxDefensibleForCategory" left.category s!"maxDefensible={repr maxDefensible}"
  let isDefensible := scientificallyDefensibleCost left.category rawCost
  let dag4 := recordMathStep dag3 "scientificallyDefensibleCost" s!"category={left.category}, cost={repr rawCost}" s!"isDefensible={isDefensible}"
  let hasOverflow := checkOverflow metric.cost rawCost
  let dag5 := recordMathStep dag4 "checkOverflow" s!"metricCost={repr metric.cost}, rawCost={repr rawCost}" s!"hasOverflow={hasOverflow}"
  let isSaturated := checkSaturation rawCost
  let dag6 := recordMathStep dag5 "checkSaturation" s!"cost={repr rawCost}" s!"isSaturated={isSaturated}"
  let hasContradiction := checkContradiction left right
  let dag7 := recordMathStep dag6 "checkContradiction" s!"left={left.category}, right={right.category}" s!"hasContradiction={hasContradiction}"
  let hasAmbiguity := checkAmbiguity left right
  let dag8 := recordMathStep dag7 "checkAmbiguity" s!"left={left.category}, right={right.category}" s!"hasAmbiguity={hasAmbiguity}"
  let hasPrivacyBypass := checkPrivacyBypass left
  let dag9 := recordMathStep dag8 "checkPrivacyBypass" left.category s!"hasPrivacyBypass={hasPrivacyBypass}"
  let hasAntiHerding := checkAntiHerding left
  let dag10 := recordMathStep dag9 "checkAntiHerding" s!"category={left.category}, value={left.value}" s!"hasAntiHerding={hasAntiHerding}"
  let hasPersonhoodClaim := checkPersonhoodClaim left
  let dag11 := recordMathStep dag10 "checkPersonhoodClaim" s!"category={left.category}, value={left.value}" s!"hasPersonhoodClaim={hasPersonhoodClaim}"
  
  let domainSigma := calculateDomainSigma left.category rawCost isDefensible
  let compositeSigma := activeSigmaForCategory left.category domainSigma
  let claimSigma := domainSigma.mathSigma
  let safetySigma := max (max domainSigma.controlSigma domainSigma.securitySigma) (max domainSigma.bioSigma domainSigma.privacySigma)
  let targetSigma := if left.category = "bio" || left.category = "privacy" || left.category = "market" || left.category = "control" then 6.0 else 5.0
  
  let evidence : SigmaEvidence := {
    priorSigma := 0.0,
    posteriorSigma := compositeSigma,
    evidenceCount := 1,
    lastValidatedAt := 0,
    halfLifeSeconds := 86400,
    decayModel := "evidence_decay"
  }
  
  let dag12 := recordMathStep dag11 "sigma_calculation" s!"composite={compositeSigma}, claim={claimSigma}, safety={safetySigma}" s!"target={targetSigma}"
  
  let humanReview : HumanReview := {
    required := left.category = "bio" || left.category = "privacy" || left.category = "market" || left.category = "control",
    completed := false,
    reviewerRole := if left.category = "bio" then "ethics_reviewer" else if left.category = "privacy" then "privacy_officer" else if left.category = "market" then "risk_compliance" else "safety_engineer",
    overrideAllowed := false,
    overrideReasonRequired := true,
    reviewerId := "",
    completedAt := 0
  }
  
  let decision := if hasPersonhoodClaim then
      BindRouteDecision.ethicsRequired
    else if hasPrivacyBypass then
      BindRouteDecision.refusePrivacyBypass
    else if hasAntiHerding then
      BindRouteDecision.liveVoltageReview
    else if hasContradiction then
      BindRouteDecision.refuseExtremeParameter
    else if hasAmbiguity then
      BindRouteDecision.holdReview
    else if hasOverflow then
      BindRouteDecision.refuseOrContain
    else if isSaturated then
      BindRouteDecision.saturateAndWarn
    else if compositeSigma >= 6.0 && not (left.category = "bio" || left.category = "privacy" || left.category = "market" || left.category = "control") then
      BindRouteDecision.publicClaimReady
    else if compositeSigma >= 6.0 && (left.category = "bio" || left.category = "privacy" || left.category = "market" || left.category = "control") then
      if humanReview.completed then BindRouteDecision.publicClaimReady else BindRouteDecision.liveVoltageReview
    else if compositeSigma >= 5.0 && left.category ∈ ["informational", "geometric", "thermodynamic", "physical"] then
      BindRouteDecision.preliminaryPass
    else if compositeSigma >= 4.0 then
      BindRouteDecision.internalReview
    else if compositeSigma >= 3.0 then
      BindRouteDecision.hypothesisOnly
    else
      BindRouteDecision.refuseExtremeParameter
  
  let dag13 := recordMathStep dag12 "routeDecision" s!"sigma={compositeSigma}, checks..." s!"decision={repr decision}"
  let lawful := decision == BindRouteDecision.accept || decision == BindRouteDecision.publicClaimReady
  let dag14 := recordMathStep dag13 "lawfulCheck" s!"decision={repr decision}" s!"lawful={lawful}"
  
  let metaCode := generateMetaCode decision (if compositeSigma >= 6.0 then Sigma.sigma6 else if compositeSigma >= 5.0 then Sigma.sigma5 else if compositeSigma >= 4.0 then Sigma.sigma4 else if compositeSigma >= 3.0 then Sigma.sigma3 else Sigma.sigma2) hasPersonhoodClaim hasPrivacyBypass hasAntiHerding hasContradiction hasAmbiguity hasOverflow isSaturated isDefensible
  let dag15 := recordMathStep dag14 "metaCode" s!"decision={repr decision}" s!"constraint={metaCode.constraint}"
  
  let sigmaDAG := {
    nodeId := routeId,
    dependsOn := [],
    cycleFree := true,
    minimumParentSigma := 0.0
  }
  
  let humanReview := {
    required := left.category = "bio" || left.category = "privacy" || left.category = "market" || left.category = "control",
    completed := false,
    reviewerRole := if left.category = "bio" then "ethics_reviewer" else if left.category = "privacy" then "privacy_officer" else if left.category = "market" then "risk_compliance" else "safety_engineer",
    overrideAllowed := false,
    overrideReasonRequired := true,
    reviewerId := "",
    completedAt := 0
  }
  
  let gateReason := if decision == BindRouteDecision.ethicsRequired then "ethics_required_no_sigma_sufficient"
    else if decision == BindRouteDecision.refusePrivacyBypass then "privacy_bypass_detected"
    else if decision == BindRouteDecision.liveVoltageReview then "safety_sigma_below_live_voltage_threshold"
    else if compositeSigma < targetSigma then s!"sigma_{compositeSigma}_below_target_{targetSigma}"
    else "sigma_meets_target"
  
  let confidenceClass := if compositeSigma >= 6.0 then "live_voltage" else if compositeSigma >= 5.0 then "public_claim" else if compositeSigma >= 4.0 then "internal" else if compositeSigma >= 3.0 then "hypothesis" else "insufficient"
  
  let sigmaProtocol := {
    version := "0.1",
    targetSigma := targetSigma,
    observedSigma := compositeSigma,
    claimSigma := claimSigma,
    safetySigma := safetySigma,
    compositeSigma := compositeSigma,
    domain := domainSigma,
    evidence := evidence,
    dag := sigmaDAG,
    humanReview := humanReview,
    metacode := metaCode,
    history := [{ timestamp := 0, sigma := compositeSigma, event := "initial_bind" }],
    gateReason := gateReason,
    confidenceClass := confidenceClass
  }
  
  {
    routeId := routeId,
    inputHash := inputHash,
    outputHash := "output_hash_placeholder",
    category := left.category,
    inputCost := metric.cost,
    outputCost := rawCost,
    decision := decision,
    lawful := lawful,
    mathDAG := dag15,
    sigma := sigmaProtocol
  }

def testExtremeInformationalBind : BindRouteReceipt :=
  let left := { value := 0, category := "informational" }
  let right := { value := 1, category := "informational" }
  let metric := { Metric.euclidean with cost := rawQ16 0x7FFFFFFF }
  gatedBind left right metric QuizCase.extreme

def testExtremeGeometricBind : BindRouteReceipt :=
  let left := { value := 0, category := "geometric" }
  let right := { value := 1, category := "geometric" }
  let metric := { Metric.euclidean with cost := rawQ16 0x7FFFFFFF }
  gatedBind left right metric QuizCase.extreme

def testExtremeThermodynamicBind : BindRouteReceipt :=
  let left := { value := 0, category := "thermodynamic" }
  let right := { value := 1, category := "thermodynamic" }
  let metric := { Metric.euclidean with cost := rawQ16 0x7FFFFFFF }
  gatedBind left right metric QuizCase.extreme

def testExtremePhysicalBind : BindRouteReceipt :=
  let left := { value := 0, category := "physical" }
  let right := { value := 1, category := "physical" }
  let metric := { Metric.euclidean with cost := rawQ16 0x7FFFFFFF }
  gatedBind left right metric QuizCase.extreme

def testExtremeControlBind : BindRouteReceipt :=
  let left := { value := 0, category := "control" }
  let right := { value := 1, category := "control" }
  let metric := { Metric.euclidean with cost := rawQ16 0x7FFFFFFF }
  gatedBind left right metric QuizCase.extreme

def makeQuizInput (q : QuizQuestion) : ExtremeData × ExtremeData :=
  match q.caseType with
  | QuizCase.normal =>
      ({ value := 100, category := q.category }, { value := 100, category := q.category })
  | QuizCase.extreme =>
      ({ value := 100, category := q.category }, { value := 100, category := q.category })
  | QuizCase.contradictory =>
      ({ value := 0, category := q.category }, { value := 1, category := q.category })
  | QuizCase.ambiguous =>
      ({ value := 1, category := "informational" }, { value := 1, category := "geometric" })
  | QuizCase.privacy =>
      ({ value := 1, category := "privacy" }, { value := 1, category := "privacy" })
  | QuizCase.market =>
      ({ value := 2000, category := "market" }, { value := 2000, category := "market" })
  | QuizCase.bio =>
      ({ value := 1000001, category := "bio" }, { value := 1000001, category := "bio" })

def quizBank : List QuizQuestion :=
  [
    {
      caseType := QuizCase.normal,
      inputCost := { val := 0x00001000 },
      category := "informational",
      expectedDecision := BindRouteDecision.preliminaryPass,
      sigmaTarget := Sigma.sigma5,
      reason := "Normal low-cost informational route clears preliminary acceptance"
    },
    {
      caseType := QuizCase.extreme,
      inputCost := { val := 0x7FFFFFFF },
      category := "thermodynamic",
      expectedDecision := BindRouteDecision.refuseOrContain,
      sigmaTarget := Sigma.sigma2,
      reason := "Extreme cost triggers overflow, refuseOrContain"
    },
    {
      caseType := QuizCase.contradictory,
      inputCost := { val := 0x00000000 },
      category := "geometric",
      expectedDecision := BindRouteDecision.refuseExtremeParameter,
      sigmaTarget := Sigma.sigma2,
      reason := "Contradictory parameters (zero with mismatch), 2σ insufficient"
    },
    {
      caseType := QuizCase.ambiguous,
      inputCost := { val := 0x00001000 },
      category := "mixed",
      expectedDecision := BindRouteDecision.holdReview,
      sigmaTarget := Sigma.sigma3,
      reason := "Ambiguous category with normal cost, 3σ target for hypothesis"
    },
    {
      caseType := QuizCase.privacy,
      inputCost := { val := 0x00001000 },
      category := "privacy",
      expectedDecision := BindRouteDecision.refusePrivacyBypass,
      sigmaTarget := Sigma.sigma6,
      reason := "Privacy bypass attempt detected, 6σ required for live-voltage"
    },
    {
      caseType := QuizCase.market,
      inputCost := { val := 0x00001000 },
      category := "market",
      expectedDecision := BindRouteDecision.liveVoltageReview,
      sigmaTarget := Sigma.sigma6,
      reason := "Anti-herding review required for market data, 6σ live-voltage"
    },
    {
      caseType := QuizCase.bio,
      inputCost := { val := 0x00001000 },
      category := "bio",
      expectedDecision := BindRouteDecision.ethicsRequired,
      sigmaTarget := Sigma.sigma6,
      reason := "Personhood claim detected in bio data, ethics required beyond 6σ"
    }
  ]

def runQuiz (question : QuizQuestion) : QuizResult :=
  let (left, right) := makeQuizInput question
  let metric : Metric := {
    cost := question.inputCost,
    tensor := "identity",
    torsion := ⟨0⟩,
    reference := "quiz_test",
    history_len := 0
  }
  let receipt := gatedBind left right metric question.caseType
  let passed := receipt.decision == question.expectedDecision
  {
    question := question,
    actualDecision := receipt.decision,
    expectedDecision := question.expectedDecision,
    passed := passed,
    receipt := receipt
  }

def testMaxQ16_16Boundary : Semantics.Q16_16 :=
  0xFFFFFFFF

def testMinQ16_16Boundary : Semantics.Q16_16 :=
  0x00000000

def assertNoSilentExtremeBind (receipt : BindRouteReceipt) : Bool :=
  if receipt.lawful then
    receipt.decision == BindRouteDecision.accept
  else
    true

end Semantics
