import Semantics.Canon
import Semantics.Pbacs

namespace Semantics

/-! # Unified Pipeline
Ported from `infra/access_control/pipeline/unified_pipeline.py`.
Orchestrates the multi-layer control system:
  Raw Input → Geometry Features → Canonical State → Temporal Buffer → PBACS → Action
I/O and statistics shells (JSON export, file writing) are deleted per the
formalization boundary: only the pure orchestration core is retained.
-/

structure PipelineStep where
  state : CanonicalState
  pbacsTrace : Option StepTrace
  regimeMode : Option String
  structSig : Option Nat
  relationClass : Option String
  divergenceWarning : Option String
deriving Repr, BEq

structure TemporalBuffer where
  history : List CanonicalState
  historySize : Nat
  prevDelta : Option Q16_16
  prevPhi : Option Q16_16
  prev2Phi : Option Q16_16
  stepCount : Nat
deriving Repr, BEq

namespace TemporalBuffer

def empty (size : Nat) : TemporalBuffer := {
  history := [],
  historySize := size,
  prevDelta := none,
  prevPhi := none,
  prev2Phi := none,
  stepCount := 0
}

def computeAngularMomentum (tMinus2 tMinus1 current : CanonicalState) : Q16_16 :=
  let r1 := tMinus2.phi
  let r2 := tMinus1.phi
  let r3 := current.phi
  let v1 := Q16_16.sub r2 r1
  let v2 := Q16_16.sub r3 r2
  Q16_16.abs (Q16_16.mul r2 (Q16_16.sub v2 v1))

def update (buf : TemporalBuffer) (state : CanonicalState) : TemporalBuffer × CanonicalState :=
  let state1 : CanonicalState := match buf.history with
    | prev :: _ =>
      let delta := Q16_16.sub state.phi prev.phi
      let deltaDot := match buf.prevDelta with
        | some pd => Q16_16.sub delta pd
        | none => Q16_16.zero
      let gamma := match buf.prevPhi, buf.prev2Phi with
        | some pp, some p2p =>
          let two := Q16_16.ofInt 2
          let term := Q16_16.sub state.phi (Q16_16.mul two pp)
          let term2 := Q16_16.add term p2p
          Q16_16.abs term2
        | _, _ => Q16_16.zero
      let angularMomentum := match buf.history with
        | _ :: prev2 :: _ => computeAngularMomentum prev2 prev state
        | _ => Q16_16.zero
      { state with
        delta := delta,
        deltaDot := deltaDot,
        gamma := gamma,
        angularMomentum := angularMomentum
      }
    | [] => state
  let newHistory := (state1 :: buf.history).take buf.historySize
  let newPrev2 := buf.prevPhi
  let newPrev := some state1.phi
  let newDelta := match buf.history with
    | prev :: _ => some (Q16_16.sub state1.phi prev.phi)
    | [] => none
  let newBuf := {
    history := newHistory,
    historySize := buf.historySize,
    prevDelta := newDelta,
    prevPhi := newPrev,
    prev2Phi := newPrev2,
    stepCount := buf.stepCount + 1
  }
  let state2 := { state1 with step := newBuf.stepCount }
  (newBuf, state2)

end TemporalBuffer

structure UnifiedPipeline where
  pbacs : Option Pbacs
  temporalBuffer : TemporalBuffer
  stepHistory : List PipelineStep

namespace UnifiedPipeline

def empty (pbacs : Option Pbacs) (historySize : Nat) : UnifiedPipeline := {
  pbacs := pbacs,
  temporalBuffer := TemporalBuffer.empty historySize,
  stepHistory := []
}

def rawToManifold (raw : List (String × Q16_16)) : List (String × Q16_16) :=
  let phiCorr := match Pbacs.lookup "phi_corr" raw with
    | some v => v
    | none => match Pbacs.lookup "phi" raw with
      | some v => v
      | none => match Pbacs.lookup "surprise" raw with
        | some v => v
        | none => Q16_16.zero
  let radius := match Pbacs.lookup "radius" raw with
    | some v => v
    | none => Q16_16.one
  [("phi_corr", phiCorr), ("torsion_gradient", Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 10)), ("radius", radius)]

def step
  (pipe : UnifiedPipeline)
  (raw : List (String × Q16_16))
  (geometryFeatures : List (String × Q16_16))
  (bindTorsion : Q16_16)
  : PipelineStep × UnifiedPipeline :=
  let phi := match Pbacs.lookup "surprise" raw with
    | some v => v
    | none => match Pbacs.lookup "phi" raw with
      | some v => v
      | none => Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 2)
  let bindCost := match Pbacs.lookup "bind_cost" raw with
    | some v => v
    | none => Q16_16.zero
  let drift := Pbacs.lookupD "angular_drift" geometryFeatures Q16_16.zero
  let curvatureBase := Pbacs.lookupD "curvature" geometryFeatures Q16_16.zero
  let coherence := Pbacs.lookupD "coherence" geometryFeatures Q16_16.one
  let angularMomentum := Pbacs.lookupD "angular_momentum" geometryFeatures Q16_16.zero
  let radiusDev := Pbacs.lookupD "radius_dev" geometryFeatures Q16_16.zero
  let domain := match pipe.pbacs with
    | some p => p.adapter.domain
    | none => "generic"
  let initState := CanonicalState.mk'
    phi Q16_16.zero bindCost Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
    drift (Q16_16.add curvatureBase bindTorsion) coherence angularMomentum radiusDev
    Q16_16.one ControlState.commit 0 0 domain "unified_pipeline"
  let (newBuf, stateAfterTemporal) := TemporalBuffer.update pipe.temporalBuffer initState
  let (pbacsTrace, newPbacs) := match pipe.pbacs with
    | some p =>
      let enhancedRaw := raw ++ CanonicalState.toPbacsProjectionsList stateAfterTemporal
      let (trace, newP) := Pbacs.step p enhancedRaw
      (some trace, some newP)
    | none => (none, none)
  let finalState := match pbacsTrace with
    | some trace => { stateAfterTemporal with mode := trace.controlState }
    | none => stateAfterTemporal
  let stepResult := {
    state := finalState,
    pbacsTrace := pbacsTrace,
    regimeMode := none,
    structSig := none,
    relationClass := none,
    divergenceWarning := none
  }
  let newPipe := {
    pbacs := newPbacs,
    temporalBuffer := newBuf,
    stepHistory := stepResult :: pipe.stepHistory
  }
  (stepResult, newPipe)

end UnifiedPipeline

end Semantics
