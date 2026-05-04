import Semantics.FixedPoint

namespace Semantics

/-! # Canonical State
Ported from `infra/access_control/core/canonical_state.py`.
Unified state representation for the control system.
All scalar fields use Q16_16 fixed-point per Commandment IV.

Fixed-point usage justification (Section 13.3):
- Q16_16 used for all control state fields to preserve integer precision for control logic
- Required for PBACS projections, regime tracking, and geometry features
- Deterministic overflow behavior: operations use standard Q16_16 arithmetic with wraparound
- No Q0_16 usage in this module - all control values require integer component for control decisions

NII-02 TRANSLATION ENGINE ASSIGNMENT:
====================================
This file is assigned to NII-02 Translation Engine for:
- Translation of canonical state representation to hardware-native format
- Extraction of semantic coordinate packing for hardware serialization
- Translation of normalization modes to hardware-accelerated computation
- Formalization of canonical binary form for hardware transmission

Translation responsibilities:
1. Map CanonicalState structure to hardware-native memory layout
2. Translate normalization functions to GPU/accelerator kernels
3. Extract canonical serialization for hardware communication protocols
4. Formalize semantic coordinate packing for hardware state machines

Historical note on semantic values
----------------------------------
Earlier ENE/PBACS-era modules did not treat semantic values as free-form labels,
embeddings, or open-text annotations. They treated them as bounded projection
coordinates derived from lawful comparison between:

- raw observation,
- projected target state, and
- current internal state.

In practice this meant that meaning appeared as compact operational fields such
as mismatch, curvature, tension, coherence, gain, cost, and reliability. The
older adapter family repeatedly expressed these as stable coordinates like:

- `u_phi`      semantic margin / actionable alignment,
- `u_delta`    state-target mismatch,
- `u_delta_dot` change in mismatch,
- `u_gamma`    second-order temporal curvature,
- `u_tau`      hazard / tension / burden,
- `u_chi`      productive coherence under constraint,
- `u_gain`     opportunity or expected upside,
- `u_cost`     friction or burden,
- `u_bias`     trust / reliability prior,
- `u_pacing`   urgency or pacing surface (drives engramLength ℓ in SSS).

So the semantic value was not "what the symbol means" in isolation. It was the
position of a system inside a bounded semantic field that could be:

- measured,
- updated,
- packed into canonical coordinates, and
- used for control or assignment.

The canonical layer therefore preserves an older design commitment:
semantic value should be represented as lawful, bounded, reusable coordinates
before it is represented as narrative description.
-/

/-- Unified control states across PBACS and RegimeTracker. -/
inductive ControlState
  | commit
  | hold
  | halt
  | dmt      -- Dimensionally Mismatched Throat
  | flame    -- Extreme emergency state
deriving Repr, BEq, DecidableEq

/-- PBACS projection export. -/
structure PbacsProjections where
  uPhi      : Q16_16
  uPsi      : Q16_16
  uDelta    : Q16_16
  uGamma    : Q16_16
  uChi      : Q16_16
  uTau      : Q16_16
  uDeltaDot : Q16_16
  uPacing   : Q16_16
deriving Repr, BEq

#eval { uPhi := Q16_16.zero, uPsi := Q16_16.zero, uDelta := Q16_16.zero, uGamma := Q16_16.zero, uChi := Q16_16.zero, uTau := Q16_16.zero, uDeltaDot := Q16_16.zero, uPacing := Q16_16.zero : PbacsProjections }

/-- RegimeTracker observable export. -/
structure RegimeTrackerObservables where
  phi          : Q16_16
  psi          : Q16_16
  delta        : Q16_16
  fieldStrain  : Q16_16
  chi          : Q16_16
  torsion      : Q16_16
  gapVelocity  : Q16_16
deriving Repr, BEq

#eval { phi := Q16_16.zero, psi := Q16_16.zero, delta := Q16_16.zero, fieldStrain := Q16_16.zero, chi := Q16_16.zero, torsion := Q16_16.zero, gapVelocity := Q16_16.zero : RegimeTrackerObservables }

/-- Geometry feature export. -/
structure GeometryFeatures where
  angularDrift      : Q16_16
  curvature         : Q16_16
  coherence         : Q16_16
  angularMomentum   : Q16_16
  radiusDev         : Q16_16
deriving Repr, BEq

#eval { angularDrift := Q16_16.zero, curvature := Q16_16.zero, coherence := Q16_16.one, angularMomentum := Q16_16.zero, radiusDev := Q16_16.zero : GeometryFeatures }

/-- Unified representation of control system state. -/
structure CanonicalState where
  phi           : Q16_16
  psi           : Q16_16
  delta         : Q16_16
  gamma         : Q16_16
  chi           : Q16_16
  tau           : Q16_16
  deltaDot      : Q16_16
  drift         : Q16_16
  curvature     : Q16_16
  coherence     : Q16_16
  angularMomentum : Q16_16
  radiusDev     : Q16_16
  step          : Nat
  mode          : ControlState
  priority      : Nat
  budget        : Nat
  domain        : String
  source        : String
deriving Repr, BEq

#eval CanonicalState.mk Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero 0 ControlState.commit 0 0 "test" "test"

namespace CanonicalState

instance : Inhabited CanonicalState where
  default := {
    phi := Q16_16.zero, psi := Q16_16.zero, delta := Q16_16.zero,
    gamma := Q16_16.zero, chi := Q16_16.zero, tau := Q16_16.zero,
    deltaDot := Q16_16.zero, drift := Q16_16.zero,
    curvature := Q16_16.zero, coherence := Q16_16.one,
    angularMomentum := Q16_16.zero, radiusDev := Q16_16.zero,
    step := 0, mode := ControlState.commit, priority := 0, budget := 0,
    domain := "generic", source := "unknown"
  }

def default : CanonicalState := {
  phi := Q16_16.zero, psi := Q16_16.zero, delta := Q16_16.zero,
  gamma := Q16_16.zero, chi := Q16_16.zero, tau := Q16_16.zero,
  deltaDot := Q16_16.zero, drift := Q16_16.zero,
  curvature := Q16_16.zero, coherence := Q16_16.one,
  angularMomentum := Q16_16.zero, radiusDev := Q16_16.zero,
  step := 0, mode := ControlState.commit, priority := 0, budget := 0,
  domain := "generic", source := "unknown"
}

/-- Compute confidence from geometry: 1 / (1 + drift * curvature + angularMomentum), clamped to [0,1]. -/
def computeConfidence (drift curvature angularMomentum : Q16_16) : Q16_16 :=
  let denom := Q16_16.add (Q16_16.add Q16_16.one (Q16_16.mul drift curvature)) angularMomentum
  let raw := Q16_16.div Q16_16.one denom
  Q16_16.max Q16_16.zero (Q16_16.min Q16_16.one raw)

/-- Smart constructor that creates a CanonicalState with all fields. -/
def mk'
  (phi psi delta gamma chi tau deltaDot drift curvature coherence
   angularMomentum radiusDev : Q16_16)
  (step : Nat)
  (mode : ControlState)
  (priority budget : Nat)
  (domain source : String) :
  CanonicalState :=
  {
    phi := phi, psi := psi, delta := delta, gamma := gamma,
    chi := chi, tau := tau, deltaDot := deltaDot, drift := drift,
    curvature := curvature, coherence := coherence,
    angularMomentum := angularMomentum, radiusDev := radiusDev,
    step := step, mode := mode, priority := priority, budget := budget,
    domain := domain, source := source
  }

def toPbacsProjections (s : CanonicalState) : PbacsProjections := {
  uPhi := s.phi, uPsi := s.psi, uDelta := s.delta, uGamma := s.gamma,
  uChi := s.chi, uTau := s.tau, uDeltaDot := s.deltaDot,
  uPacing := Q16_16.max s.delta (Q16_16.abs s.deltaDot)
}

def toPbacsProjectionsList (s : CanonicalState) : List (String × Q16_16) :=
  let p := toPbacsProjections s
  [
    ("u_phi", p.uPhi), ("u_psi", p.uPsi), ("u_delta", p.uDelta),
    ("u_gamma", p.uGamma), ("u_chi", p.uChi), ("u_tau", p.uTau),
    ("u_delta_dot", p.uDeltaDot), ("u_pacing", p.uPacing)
  ]

def toRegimeTrackerObservables (s : CanonicalState) : RegimeTrackerObservables := {
  phi := s.phi, psi := s.psi, delta := s.delta,
  fieldStrain := s.gamma, chi := s.chi, torsion := s.tau,
  gapVelocity := s.deltaDot
}

def toGeometryFeatures (s : CanonicalState) : GeometryFeatures := {
  angularDrift := s.drift, curvature := s.curvature,
  coherence := s.coherence, angularMomentum := s.angularMomentum,
  radiusDev := s.radiusDev
}

def fromPbacsProjections (p : PbacsProjections) (mode : ControlState)
  (step : Nat) (priority budget : Nat) (domain source : String) : CanonicalState :=
  mk' p.uPhi p.uPsi p.uDelta p.uGamma p.uChi p.uTau p.uDeltaDot
    Q16_16.zero Q16_16.zero Q16_16.one Q16_16.zero Q16_16.zero
    step mode priority budget domain source

def fromGeometryFeatures (g : GeometryFeatures) (mode : ControlState)
  (step : Nat) (priority budget : Nat) (domain source : String) : CanonicalState :=
  mk' Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
    g.angularDrift g.curvature g.coherence g.angularMomentum g.radiusDev
    step mode priority budget domain source

/-- Stable when mode is COMMIT and delta < 0.3. -/
def isStable (s : CanonicalState) : Bool :=
  s.mode == ControlState.commit && Q16_16.lt s.delta (Q16_16.div (Q16_16.ofInt 3) (Q16_16.ofInt 10))

/-- Critical when mode is HALT or FLAME. -/
def isCritical (s : CanonicalState) : Bool :=
  s.mode == ControlState.halt || s.mode == ControlState.flame

/-- Default state is stable because delta = 0 < 0.3 and mode = COMMIT. -/
theorem defaultIsStable : CanonicalState.default.isStable = true := by
  native_decide

end CanonicalState

end Semantics
