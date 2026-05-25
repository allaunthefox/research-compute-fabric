/-
LogogramRotationLoop.lean — Holographic logogram encoding via lambda-rotation.

One beam carries multiple encoded projections.  The beam does not switch
between encodings — it always delivers the superposition of all projections
simultaneously.  The boundary resolves separate structures by threshold-band
filtering in lambda-space, not by coordinate separation in x-space.

This maps the DISH holographic volumetric printing insight onto logogram
encoding: the rotation loop is the periscope, each projection angle encodes
a different structure, the beam is the cumulative holographic field, and
the boundary (resin / decoder) materializes only those structures whose
threshold bands are crossed at each point.

Expansion space shrinks from coordinate buffers (Delta_x) to threshold
separation (Delta_lambda).
-/

import Semantics.FixedPoint
import Semantics.ThresholdVector
import Semantics.RRCLogogramProjection
import Semantics.LogogramSubstitution

set_option linter.dupNamespace false

namespace Semantics.LogogramRotationLoop

open Semantics.FixedPoint (Q0_16 Q0_16.ofRawInt Q16_16.ofRawInt)
open Semantics.ThresholdVector (ActivationState ActivationWeight
  ThresholdVector activationExcess totalActivation criticalActivationThreshold)
open Semantics.RRCLogogramProjection (RRCShape WitnessStatus SemanticRegime
  LogogramReceipt typeAdmissible projectionAdmissible)
open Semantics.LogogramSubstitution (SubstitutionReceipt SubstitutionDecision)

/-- A normalized rotation angle in [0, 1), representing one projection direction. -/
structure RotationAngle where
  angle : Q0_16
  deriving Repr, DecidableEq, BEq, Inhabited

/--
A threshold band in lambda-space [lower, upper].

Structures are separated not by coordinate distance but by which
lambda-band they occupy.  Overlapping bands produce interference;
non-overlapping bands resolve independently.
-/
structure ThresholdBand where
  lower : Q0_16
  upper : Q0_16
  deriving Repr, DecidableEq, BEq, Inhabited

/--
Check whether a total activation B falls within a threshold band (inclusive).
-/
def inBand (B : Q0_16) (band : ThresholdBand) : Bool :=
  Q0_16.ge B band.lower && Q0_16.le B band.upper

/--
A logogram projection layer: one encoding vector at a given angle,
targeting a specific threshold band.

Each layer is a single "exposure" in the rotation cycle — it encodes
one structure's data as an activation state that the beam carries.
-/
structure LogogramProjectionLayer where
  angle : RotationAngle
  encoding : ActivationState
  targetBand : ThresholdBand
  deriving Repr, DecidableEq, BEq, Inhabited

/--
The full rotation cycle: an ordered list of projection layers.

The beam cycles through these during one full rotation.  Each layer
contributes its encoding to the cumulative beam superposition.
The period is the number of layers.
-/
structure RotationCycle where
  layers : List LogogramProjectionLayer
  period : Nat
  deriving Repr, DecidableEq, BEq, Inhabited

/--
The cumulative state of the beam after integrating projections.

The beam carries the sum of all projection encodings, weighted by
their activation weights.  The boundary resolves this superposition
by checking which threshold bands are crossed at each point.
-/
structure BeamState where
  cumulative : ActivationState
  totalB : Q0_16
  layersIntegrated : Nat
  deriving Repr, DecidableEq, BEq, Inhabited

/-- A structure extracted from the beam superposition by threshold band. -/
structure ExtractedStructure where
  sourceAngle : RotationAngle
  resolvedBand : ThresholdBand
  resolvedActivation : Q0_16
  isMaterialized : Bool
  deriving Repr, DecidableEq, BEq, Inhabited

/- =======================================================================
    Beam operators
    ======================================================================= -/

/--
Integrate one projection layer into the beam state.

The beam accumulates the weighted activation from each layer,
building the total superposition B = sum alpha_i * phi_i over
all layers.
-/
def integrateLayer
  (beam : BeamState)
  (layer : LogogramProjectionLayer)
  (weights : ActivationWeight) : BeamState :=
  let newCumulative : ActivationState :=
    { stressAccumulated :=
        Q0_16.add beam.cumulative.stressAccumulated layer.encoding.stressAccumulated
    , couplingAccumulated :=
        Q0_16.add beam.cumulative.couplingAccumulated layer.encoding.couplingAccumulated
    , topologyPersistence :=
        Q0_16.add beam.cumulative.topologyPersistence layer.encoding.topologyPersistence
    , eigenmodeDrift :=
        Q0_16.add beam.cumulative.eigenmodeDrift layer.encoding.eigenmodeDrift
    , residualAccumulated :=
        Q0_16.add beam.cumulative.residualAccumulated layer.encoding.residualAccumulated }
  let newB := totalActivation newCumulative weights
  { cumulative := newCumulative
  , totalB := newB
  , layersIntegrated := beam.layersIntegrated + 1 }

/--
Run the full rotation cycle to produce the complete beam superposition.

This simulates a full rotation of the periscope, integrating all
projection layers into the cumulative beam state.
-/
def runRotationCycle
  (cycle : RotationCycle)
  (weights : ActivationWeight) : BeamState :=
  let initBeam : BeamState :=
    { cumulative :=
        { stressAccumulated := Q0_16.zero
        , couplingAccumulated := Q0_16.zero
        , topologyPersistence := Q0_16.zero
        , eigenmodeDrift := Q0_16.zero
        , residualAccumulated := Q0_16.zero }
    , totalB := Q0_16.zero
    , layersIntegrated := 0 }
  List.foldl (fun b l => integrateLayer b l weights) initBeam cycle.layers

/- =======================================================================
    Structure extraction
    ======================================================================= -/

/--
Resolve one structure from the beam superposition by threshold-band
filtering.

A structure materializes when its B value falls within its target band
AND the total beam activation is at or above the critical threshold.
-/
def resolveStructure
  (beam : BeamState)
  (layer : LogogramProjectionLayer)
  (_thresholds : ThresholdVector)
  (weights : ActivationWeight) : ExtractedStructure :=
  let B := beam.totalB
  let inTargetBand := inBand B layer.targetBand
  let critical := Semantics.ThresholdVector.isCriticallyActivated beam.cumulative weights
  let materialized := inTargetBand && critical
  { sourceAngle := layer.angle
  , resolvedBand := layer.targetBand
  , resolvedActivation := B
  , isMaterialized := materialized }

/--
Extract all structures from a beam superposition.

Each projection layer whose threshold band contains the beam's
total activation B materializes as a resolved structure.
This is the decoder operation: one beam, multiple structures,
separated by lambda-space bands.
-/
def resolveAllStructures
  (beam : BeamState)
  (cycle : RotationCycle)
  (thresholds : ThresholdVector)
  (weights : ActivationWeight) : List ExtractedStructure :=
  List.map (fun layer => resolveStructure beam layer thresholds weights) cycle.layers

/--
Count how many structures materialize from a given beam state.
This is the packing density in lambda-space at this boundary point.
-/
def materializedCount (structures : List ExtractedStructure) : Nat :=
  (List.filter (fun s => s.isMaterialized) structures).length

/- =======================================================================
    Canonical witnesses
    ======================================================================= -/

/-- A threshold band for low activation (density-gradient regime). -/
def lowBand : ThresholdBand :=
  { lower := Q0_16.ofRawInt 0x0000, upper := Q0_16.ofRawInt 0x2CCC }

/-- A threshold band for medium activation (coupling regime). -/
def midBand : ThresholdBand :=
  { lower := Q0_16.ofRawInt 0x2CCC, upper := Q0_16.ofRawInt 0x5555 }

/-- A threshold band for high activation (topology regime). -/
def highBand : ThresholdBand :=
  { lower := Q0_16.ofRawInt 0x5555, upper := Q0_16.ofRawInt 0x7FFF }

/--
Three projection layers encoding different structures in different
threshold bands, simulating a 3-structure-per-volume rotation cycle.
-/
def threeStructureCycle : RotationCycle :=
  { layers := [
      { angle := { angle := Q0_16.ofRawInt 0x0000 }
      , encoding :=
          { stressAccumulated := Q0_16.half
          , couplingAccumulated := Q0_16.zero
          , topologyPersistence := Q0_16.zero
          , eigenmodeDrift := Q0_16.zero
          , residualAccumulated := Q0_16.zero }
      , targetBand := lowBand }
    , { angle := { angle := Q0_16.ofRawInt 0x2AAA }
      , encoding :=
          { stressAccumulated := Q0_16.zero
          , couplingAccumulated := Q0_16.one
          , topologyPersistence := Q0_16.zero
          , eigenmodeDrift := Q0_16.zero
          , residualAccumulated := Q0_16.zero }
      , targetBand := midBand }
    , { angle := { angle := Q0_16.ofRawInt 0x5555 }
      , encoding :=
          { stressAccumulated := Q0_16.zero
          , couplingAccumulated := Q0_16.zero
          , topologyPersistence := Q0_16.one
          , eigenmodeDrift := Q0_16.zero
          , residualAccumulated := Q0_16.zero }
      , targetBand := highBand }
    ]
  , period := 3 }

/--
A single-structure cycle for comparison — this is the pre-holographic
baseline where one beam carries one encoding.
-/
def singleStructureCycle : RotationCycle :=
  { layers := [
      { angle := { angle := Q0_16.zero }
      , encoding :=
          { stressAccumulated := Q0_16.one
          , couplingAccumulated := Q0_16.zero
          , topologyPersistence := Q0_16.zero
          , eigenmodeDrift := Q0_16.zero
          , residualAccumulated := Q0_16.zero }
      , targetBand := lowBand }
    ]
  , period := 1 }

/-- =======================================================================
    Theorems
    ======================================================================= -/

theorem single_cycle_produces_one_structure :
    materializedCount
      (resolveAllStructures
        (runRotationCycle singleStructureCycle Semantics.ThresholdVector.uniformWeights)
        singleStructureCycle
        Semantics.ThresholdVector.defaultThresholds
        Semantics.ThresholdVector.uniformWeights) = 1 := by
  native_decide

theorem three_cycle_beam_has_positive_activation :
    Q0_16.gt
      (runRotationCycle threeStructureCycle Semantics.ThresholdVector.uniformWeights).totalB
      Q0_16.zero = true := by
  native_decide

theorem three_cycle_integrates_all_layers :
    (runRotationCycle threeStructureCycle Semantics.ThresholdVector.uniformWeights).layersIntegrated = 3 := by
  native_decide

theorem single_cycle_integrates_one_layer :
    (runRotationCycle singleStructureCycle Semantics.ThresholdVector.uniformWeights).layersIntegrated = 1 := by
  native_decide

theorem empty_cycle_has_zero_activation :
    (runRotationCycle { layers := [], period := 0 }
      Semantics.ThresholdVector.uniformWeights).totalB = Q0_16.zero := by
  native_decide

theorem zero_is_in_low_band :
    inBand Q0_16.zero lowBand = true := by
  native_decide

theorem half_is_in_mid_band :
    inBand Q0_16.half midBand = true := by
  native_decide

theorem one_is_in_high_band :
    inBand Q0_16.one highBand = true := by
  native_decide

theorem low_and_mid_bands_are_disjoint :
    inBand (Q0_16.ofRawInt 0x2CCC) lowBand = true && inBand (Q0_16.ofRawInt 0x2CCC) midBand = true := by
  native_decide

/- =======================================================================
    #eval witnesses
    ======================================================================= -/

#eval (runRotationCycle singleStructureCycle Semantics.ThresholdVector.uniformWeights).totalB
#eval (runRotationCycle threeStructureCycle Semantics.ThresholdVector.uniformWeights).totalB
#eval (runRotationCycle threeStructureCycle Semantics.ThresholdVector.uniformWeights).layersIntegrated

def singleBeam := runRotationCycle singleStructureCycle Semantics.ThresholdVector.uniformWeights
def threeBeam := runRotationCycle threeStructureCycle Semantics.ThresholdVector.uniformWeights

#eval materializedCount (resolveAllStructures singleBeam singleStructureCycle
  Semantics.ThresholdVector.defaultThresholds Semantics.ThresholdVector.uniformWeights)
#eval materializedCount (resolveAllStructures threeBeam threeStructureCycle
  Semantics.ThresholdVector.defaultThresholds Semantics.ThresholdVector.uniformWeights)

end Semantics.LogogramRotationLoop