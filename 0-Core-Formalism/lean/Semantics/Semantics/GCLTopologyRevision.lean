import Std

namespace Semantics.GCLTopologyRevision

/-!
Typed vocabulary for the GCL topology revision.

This module is intentionally small: it records the revised contract that all
route-prior machinery feeds GCL, while only the full gate may admit state.
-/

/-- Historical authority layers are now phases inside one topology. -/
inductive TopologyPhase where
  | builder
  | warden
  | judge
  deriving Repr, BEq, DecidableEq

/-- Canonical GCL gate stages. -/
inductive GCLGate where
  | observe
  | bind
  | route
  | sigmaCheck
  | policyCheck
  | dagCheck
  | verify
  | receipt
  deriving Repr, BEq, DecidableEq

/-- Pre-admission route-prior sources. -/
inductive RoutePriorSource where
  | sequenceSurface
  | gclMotif
  | informatonSurface
  | ms3cReductionGear
  | metaprobe
  | rgflow
  | sparkleHardware
  | nodePrimitive
  deriving Repr, BEq, DecidableEq

/-- GCL admission verdict. -/
inductive AdmissionVerdict where
  | admit
  | refuse
  | renormalize
  | rememberFailure
  | holdReview
  deriving Repr, BEq, DecidableEq

/-- Compact route hint. This is evidence, not authority. -/
structure RouteHint where
  source : RoutePriorSource
  phase : TopologyPhase
  shear : UInt32
  confidence : UInt32
  deriving Repr, BEq

/-- A route hint may not directly authorize execution. -/
def hintAuthorizesExecution (_hint : RouteHint) : Bool :=
  false

/-- The canonical GCL gate sequence. -/
def canonicalGate : List GCLGate :=
  [ .observe
  , .bind
  , .route
  , .sigmaCheck
  , .policyCheck
  , .dagCheck
  , .verify
  , .receipt
  ]

/-- GCL admits state only after verify and receipt are present. -/
def gateHasAuthority (gate : List GCLGate) : Bool :=
  gate.contains .verify && gate.contains .receipt

/-- Bounded verdict policy used by nanokernel route planning. -/
def routeVerdict (hint : RouteHint) (gate : List GCLGate) : AdmissionVerdict :=
  if gateHasAuthority gate then
    if hint.confidence > 0 then .admit else .holdReview
  else if hint.shear > 0 then
    .renormalize
  else
    .refuse

/-- The canonical gate is authority-bearing because it includes verify+receipt. -/
theorem canonicalGateHasAuthority : gateHasAuthority canonicalGate = true := by
  rfl

/-- Route hints never bypass admission. -/
theorem routeHintNoDirectAuthority (hint : RouteHint) :
    hintAuthorizesExecution hint = false := by
  rfl

/-- MS3C high shear without the full gate renormalizes, it does not admit. -/
theorem ms3cShearWithoutGateRenormalizes (phase : TopologyPhase) (confidence : UInt32) :
    routeVerdict
      { source := .ms3cReductionGear, phase := phase, shear := 1, confidence := confidence }
      [] = .renormalize := by
  rfl

def sampleMS3CHint : RouteHint :=
  { source := .ms3cReductionGear, phase := .warden, shear := 179, confidence := 1 }

#eval hintAuthorizesExecution sampleMS3CHint
#eval routeVerdict sampleMS3CHint []
#eval routeVerdict sampleMS3CHint canonicalGate

end Semantics.GCLTopologyRevision
