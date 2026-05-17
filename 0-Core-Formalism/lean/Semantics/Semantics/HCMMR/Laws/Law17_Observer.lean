/-
Law 17 — Observer/Measurement Gate

In HCMMR, measurement and wavefunction collapse are modeled as typed gate events:
an object being forced through a specific dimensional gate (e.g., 3D Euclidean
projection). The observer is not a separate agent but a typed projection:
Π_{16→3} applied to the object. The measurement residual tracks what was lost in
projection.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law17
  Import: Semantics.HCMMR.Core, Semantics.FixedPoint
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law17

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Observer Model
-- ═══════════════════════════════════════════════════════════════════

/--
Observer-side dimensional gate. Describes the resolution an observer brings
to bear on a target object. When the observer's dimensional resolution is
lower than the target's native dimension, projection collapse occurs.
-/
structure ObserverGate where
  observerDim         : Nat
  targetDim           : Nat
  projectionDim       : Nat
  resolutionThreshold : Q16_16
  uncertainty         : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
The recorded event of a measurement-gate application. Captures pre- and
post-measurement eigenmass, the collapse residual, which gate was applied,
and a timestamp.
-/
structure MeasurementEvent where
  beforeState      : Q16_16
  afterState       : Q16_16
  collapseResidual : Q16_16
  gateApplied      : String
  timestamp        : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §2  Collapse as Gate Event
-- ═══════════════════════════════════════════════════════════════════

/--
ε_{collapse} = ||M_before − M_after||
The mass lost when projecting from a higher-dimensional object frame into
the observer's lower-dimensional frame.
-/
def collapseResidual (before after : Q16_16) : Q16_16 :=
  Q16_16.abs (Q16_16.sub before after)

/--
Applies an ObserverGate to an HCMMRObject, producing a MeasurementEvent.
If the object's nativeDim exceeds the observer's resolution, the eigenmass
collapses to the projection within the observer's frame. Otherwise, no collapse
occurs and the afterState equals the beforeState.
-/
def observe (mass : Q16_16) (obj : HCMMRObject) (gate : ObserverGate) : MeasurementEvent :=
  let after : Q16_16 :=
    if obj.nativeDim <= gate.observerDim then
      mass
    else
      let dimRatio := Q16_16.div (Q16_16.ofInt (Int.ofNat gate.observerDim))
                                 (Q16_16.ofInt (Int.ofNat obj.nativeDim))
      Q16_16.mul mass dimRatio
  let residual := collapseResidual mass after
  { beforeState      := mass
  , afterState       := after
  , collapseResidual := residual
  , gateApplied      := "ObserverMeasurement"
  , timestamp        := 0
  }

/--
Produces an HCMMR Gate representing the observer measurement.
Verdict:
  admit if the object is already within the observer's dimensional resolution
  hold  if collapse is pending but resolvable (projectionDim > 0)
  reject if the observer cannot resolve the object at all (projectionDim = 0)
-/
def measurementGateAdmit (obj : HCMMRObject) (gate : ObserverGate) : Gate :=
  let (verdict, score) :=
    if obj.nativeDim <= gate.observerDim then
      (GateVerdict.admit, Q16_16.one)
    else if gate.projectionDim > 0 then
      let dimRatio := Q16_16.div (Q16_16.ofInt (Int.ofNat gate.observerDim))
                                 (Q16_16.ofInt (Int.ofNat obj.nativeDim))
      (GateVerdict.hold, dimRatio)
    else
      (GateVerdict.reject, Q16_16.zero)
  { name := "ObserverMeasurement", required := true, score := score, verdict := verdict }

/--
Emits a DiagnosticReceipt recording what was collapsed, how much eigenmass
was lost, and where the lost mass routes (Underverse if residual > 0,
admitted otherwise).
-/
def emitMeasurementReceipt (evt : MeasurementEvent) (obj : HCMMRObject) : DiagnosticReceipt :=
  { object         := obj.payload
  , failedGate     := evt.gateApplied
  , residual       := ⟨"measurement_collapse", evt.collapseResidual, "ObserverGate"⟩
  , alternateRoute := if evt.collapseResidual.val == 0 then "admitted" else "Underverse"
  , timestamp      := evt.timestamp
  }

-- ═══════════════════════════════════════════════════════════════════
-- §3  Resolution Horizon
-- ═══════════════════════════════════════════════════════════════════

/--
Describes the observer's resolution horizon: the maximum resolvable
dimension, whether the horizon has been reached, and whether loopback
to 16D is possible (via a permeability witness, per FoldedPointManifold).
-/
structure ResolutionHorizon where
  maxResolvableDim : Nat
  horizonReached   : Bool
  loopbackPossible : Bool
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Checks whether the observer has hit a terminal resolution boundary.
If observerDim = 0, resolution is lost:
  With a permeability witness (FoldedPointManifold pattern): hold (loopback possible)
  Without: reject (true terminal)
Otherwise: admit (observer still has dimensional bandwidth).
-/
def checkResolutionHorizon (gate : ObserverGate) (permeabilityDeclared : Bool) : GateVerdict :=
  if gate.observerDim == 0 then
    if permeabilityDeclared then
      GateVerdict.hold
    else
      GateVerdict.reject
  else
    GateVerdict.admit

-- ═══════════════════════════════════════════════════════════════════
-- §4  Fixtures
-- ═══════════════════════════════════════════════════════════════════

def eigenmassFixture : Q16_16 := Q16_16.ofInt 5

def sameDimObject : HCMMRObject :=
  { payload       := "test_object"
  , nativeDim     := 3
  , requestedGate := "ObserverMeasurement"
  , source        := "test"
  , admissible    := true
  , receiptRoot   := "0000000000000000000000000000000000000000000000000000000000000000"
  }

def higherDimObject : HCMMRObject :=
  { sameDimObject with nativeDim := 16 }

def humanObserverFixture : ObserverGate :=
  { observerDim         := 3
  , targetDim           := 16
  , projectionDim       := 3
  , resolutionThreshold := Q16_16.one
  , uncertainty         := Q16_16.div Q16_16.one (Q16_16.ofInt 10)
  }

def quantumObserverFixture : ObserverGate :=
  { observerDim         := 4
  , targetDim           := 16
  , projectionDim       := 4
  , resolutionThreshold := Q16_16.one
  , uncertainty         := Q16_16.div Q16_16.one (Q16_16.ofInt 100)
  }

def sixteenDObserverFixture : ObserverGate :=
  { observerDim         := 16
  , targetDim           := 16
  , projectionDim       := 16
  , resolutionThreshold := Q16_16.one
  , uncertainty         := Q16_16.zero
  }

def zeroDimObserverFixture : ObserverGate :=
  { observerDim         := 0
  , targetDim           := 16
  , projectionDim       := 0
  , resolutionThreshold := Q16_16.zero
  , uncertainty         := Q16_16.one
  }

def measurementCollapseFixture : MeasurementEvent :=
  let before := Q16_16.ofInt 5
  let after  := Q16_16.div (Q16_16.ofInt 15) (Q16_16.ofInt 16)
  { beforeState      := before
  , afterState       := after
  , collapseResidual := collapseResidual before after
  , gateApplied      := "ObserverMeasurement"
  , timestamp        := 1
  }

-- ═══════════════════════════════════════════════════════════════════
-- §5  Theorems
-- ═══════════════════════════════════════════════════════════════════

/--
When observerDim >= targetDim, no collapse occurs.
-/
theorem same_dim_no_collapse :
    (observe eigenmassFixture sameDimObject humanObserverFixture).collapseResidual = Q16_16.zero := by
  native_decide

/--
When observerDim < targetDim, collapse residual is nonzero.
-/
theorem higher_to_lower_collapses :
    (observe eigenmassFixture higherDimObject humanObserverFixture).collapseResidual ≠ Q16_16.zero := by
  native_decide

/--
A 16D observer admits 16D objects without collapse.
-/
theorem full_resolution_admits :
    (measurementGateAdmit higherDimObject sixteenDObserverFixture).verdict = GateVerdict.admit := by
  native_decide

/--
A human (3D) observer holds 16D objects pending collapse.
-/
theorem human_observes_16d_holds :
    (measurementGateAdmit higherDimObject humanObserverFixture).verdict = GateVerdict.hold := by
  native_decide

/--
Without a permeability witness, 0D resolution rejects.
-/
theorem zero_dim_no_permeability_rejects :
    checkResolutionHorizon zeroDimObserverFixture false = GateVerdict.reject := by
  native_decide

/--
With a permeability witness, 0D resolution holds (loopback possible).
-/
theorem zero_dim_with_permeability_holds :
    checkResolutionHorizon zeroDimObserverFixture true = GateVerdict.hold := by
  native_decide

/--
Self-collapse residual is always zero (witnessed for canonical mass).
-/
theorem collapse_residual_self_zero_concrete :
    collapseResidual (Q16_16.ofInt 5) (Q16_16.ofInt 5) = Q16_16.zero := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════
-- §6  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════

#eval humanObserverFixture
#eval quantumObserverFixture
#eval sixteenDObserverFixture
#eval zeroDimObserverFixture

#eval observe eigenmassFixture sameDimObject humanObserverFixture
#eval observe eigenmassFixture higherDimObject humanObserverFixture
#eval observe eigenmassFixture higherDimObject sixteenDObserverFixture

#eval collapseResidual (Q16_16.ofInt 5) (Q16_16.ofInt 3)
#eval collapseResidual (Q16_16.ofInt 5) (Q16_16.ofInt 5)

#eval measurementGateAdmit sameDimObject humanObserverFixture
#eval measurementGateAdmit higherDimObject humanObserverFixture
#eval measurementGateAdmit higherDimObject sixteenDObserverFixture
#eval measurementGateAdmit higherDimObject zeroDimObserverFixture

#eval emitMeasurementReceipt measurementCollapseFixture higherDimObject

#eval checkResolutionHorizon humanObserverFixture true
#eval checkResolutionHorizon zeroDimObserverFixture false
#eval checkResolutionHorizon zeroDimObserverFixture true

#eval measurementCollapseFixture

end Semantics.HCMMR.Law17
