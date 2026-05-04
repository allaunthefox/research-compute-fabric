import Semantics.Canon

namespace Semantics

/-! # PBACS Core
Ported from `infra/access_control/core/pbacs_core.py`.
Domain-agnostic control runtime with hysteretic gate, projection family,
and stable convex update law. All scalars use Q16_16 fixed-point.
-/

structure RootConfig where
  weights : List (String × Q16_16)
  polarities : List (String × Int)
  entryThresholds : List (String × Q16_16)
  exitThresholds : List (String × Q16_16)
  blinkMinMs : Q16_16
  blinkMaxMs : Q16_16
  alpha0 : Q16_16
  beta : Q16_16
deriving Repr, BEq

structure StepTrace where
  t : Nat
  raw : List (String × Q16_16)
  xT : List Q16_16
  zT : List Q16_16
  projections : List (String × Q16_16)
  score : Q16_16
  controlState : ControlState
  action : String
  mode : String
  alphaT : Q16_16
  blinkMs : Q16_16
  xNext : List Q16_16
  accumulation : List (String × Q16_16)
  carrierFrame : Option (List (String × Q16_16)) := none
  selectedBasis : Option String := none
deriving Repr, BEq

/-- Adapter interface for PBACS. -/
structure Adapter where
  domain : String
  initialState : List Q16_16
  modes : List String
  targetState : List (String × Q16_16) → List StepTrace → List Q16_16
  updateProjectionContext : List Q16_16 → List Q16_16 → List (String × Q16_16) → List StepTrace → List (String × Q16_16)
  projections : List (String × (List (String × Q16_16) → Q16_16))
  admissible : ControlState → List (String × String)
  tieBreak : List (String × String) → String × String

structure Pbacs where
  cfg : RootConfig
  adapter : Adapter
  history : List StepTrace
  xT : List Q16_16
  state : ControlState
  accumulation : List (String × Q16_16)

namespace Pbacs

def lookup (name : String) (m : List (String × Q16_16)) : Option Q16_16 :=
  match m.find? (λ p => p.1 == name) with
  | some p => some p.2
  | none => none

def lookupD (name : String) (m : List (String × Q16_16)) (default : Q16_16) : Q16_16 :=
  match lookup name m with
  | some v => v
  | none => default

def clamp01 (q : Q16_16) : Q16_16 :=
  Q16_16.max Q16_16.zero (Q16_16.min Q16_16.one q)

def q16_16Neg (q : Q16_16) : Q16_16 :=
  Q16_16.sub Q16_16.zero q

def project (adapter : Adapter) (context : List (String × Q16_16)) : List (String × Q16_16) :=
  adapter.projections.map (λ p => (p.1, clamp01 (p.2 context)))

def computeScore (cfg : RootConfig) (projections : List (String × Q16_16)) : Q16_16 :=
  cfg.weights.foldl (λ acc (name, weight) =>
    let p : Int := match cfg.polarities.find? (λ p => p.1 == name) with | some v => v.2 | none => 1
    let proj := lookupD name projections Q16_16.zero
    let signedWeight := if p == 1 then weight else q16_16Neg weight
    Q16_16.add acc (Q16_16.mul signedWeight proj)
  ) Q16_16.zero

def nextControlState (cfg : RootConfig) (currentState : ControlState) (projections : List (String × Q16_16)) : ControlState :=
  let uTau := lookupD "u_tau" projections Q16_16.zero
  let uChi := lookupD "u_chi" projections Q16_16.zero
  let uGamma := lookupD "u_gamma" projections Q16_16.zero
  let uDeltaDot := lookupD "u_delta_dot" projections Q16_16.zero
  let uDelta := lookupD "u_delta" projections Q16_16.zero
  let enterHaltTau := lookupD "halt_tau" cfg.entryThresholds Q16_16.zero
  let enterDmtProduct := lookupD "dmt_product" cfg.entryThresholds Q16_16.zero
  let enterHoldDeltaDot := lookupD "hold_delta_dot" cfg.entryThresholds Q16_16.zero
  let enterHoldDelta := lookupD "hold_delta" cfg.entryThresholds Q16_16.zero
  let leaveHaltTau := lookupD "halt_tau" cfg.exitThresholds Q16_16.zero
  let leaveDmtProduct := lookupD "dmt_product" cfg.exitThresholds Q16_16.zero
  let leaveHoldDeltaDot := lookupD "hold_delta_dot" cfg.exitThresholds Q16_16.zero
  let leaveHoldDelta := lookupD "hold_delta" cfg.exitThresholds Q16_16.zero
  if Q16_16.ge uTau enterHaltTau then
    ControlState.halt
  else if Q16_16.ge (Q16_16.mul uChi uGamma) enterDmtProduct then
    ControlState.dmt
  else if Q16_16.ge uDeltaDot enterHoldDeltaDot && Q16_16.ge uDelta enterHoldDelta then
    ControlState.hold
  else if currentState == ControlState.halt && Q16_16.gt uTau leaveHaltTau then
    ControlState.halt
  else if currentState == ControlState.dmt && Q16_16.gt (Q16_16.mul uChi uGamma) leaveDmtProduct then
    ControlState.dmt
  else if currentState == ControlState.hold && Q16_16.gt uDeltaDot leaveHoldDeltaDot && Q16_16.gt uDelta leaveHoldDelta then
    ControlState.hold
  else
    ControlState.commit

def blinkMs (cfg : RootConfig) (projections : List (String × Q16_16)) : Q16_16 :=
  let uBlink := lookupD "u_blink" projections (lookupD "u_delta" projections Q16_16.zero)
  let rT := clamp01 uBlink
  Q16_16.add cfg.blinkMinMs (Q16_16.mul (Q16_16.sub cfg.blinkMaxMs cfg.blinkMinMs) rT)

def alpha (cfg : RootConfig) (blink : Q16_16) : Q16_16 :=
  let denom := Q16_16.add Q16_16.one (Q16_16.mul cfg.beta blink)
  clamp01 (Q16_16.div cfg.alpha0 denom)

def update (xT : List Q16_16) (zT : List Q16_16) (alphaT : Q16_16) : List Q16_16 :=
  List.zipWith (λ x_i z_i =>
    let term1 := Q16_16.mul (Q16_16.sub Q16_16.one alphaT) x_i
    let term2 := Q16_16.mul alphaT z_i
    clamp01 (Q16_16.add term1 term2)
  ) xT zT

def updateAccumulation
  (acc : List (String × Q16_16))
  (field : List (String × Q16_16))
  (decay : Q16_16)
  (gain : Q16_16) :
  List (String × Q16_16) :=
  field.foldl (λ accum (name, fieldVal) =>
    let oldVal := lookupD name accum Q16_16.zero
    let newVal := Q16_16.min Q16_16.one (Q16_16.add (Q16_16.mul oldVal decay) (Q16_16.mul fieldVal gain))
    (name, newVal) :: accum.filter (λ p => p.1 != name)
  ) acc

def step (p : Pbacs) (raw : List (String × Q16_16)) : StepTrace × Pbacs :=
  let zT := p.adapter.targetState raw p.history
  let context := p.adapter.updateProjectionContext p.xT zT raw p.history
  let projections := project p.adapter context
  let newAccumulation := updateAccumulation p.accumulation projections (Q16_16.div (Q16_16.ofInt 9) (Q16_16.ofInt 10)) (Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 10))
  let newState := nextControlState p.cfg p.state projections
  let admissible := p.adapter.admissible newState
  let s := computeScore p.cfg projections
  let best := match admissible with
    | [] => ("", "")
    | cs => p.adapter.tieBreak cs
  let b := blinkMs p.cfg projections
  let a := alpha p.cfg b
  let xNext := update p.xT zT a
  let trace := {
    t := p.history.length,
    raw := raw,
    xT := p.xT,
    zT := zT,
    projections := projections,
    score := s,
    controlState := newState,
    action := best.1,
    mode := best.2,
    alphaT := a,
    blinkMs := b,
    xNext := xNext,
    accumulation := newAccumulation
  }
  (trace, { p with history := trace :: p.history, xT := xNext, state := newState, accumulation := newAccumulation })

end Pbacs

end Semantics
