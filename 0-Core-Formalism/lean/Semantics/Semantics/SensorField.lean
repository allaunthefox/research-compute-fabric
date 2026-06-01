import Semantics.PhysicsScalar
import Semantics.PhysicsEuclidean
import Semantics.FixedPoint
import Semantics.ElectromagneticSpectrum
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.CausalGeometry
import Semantics.SubstrateProfile
import Semantics.Errors

namespace Semantics.SensorField

open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean
open Semantics.FixedPoint
open Semantics.ElectromagneticSpectrum
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.CausalGeometry
open Semantics.SubstrateProfile
open Semantics.Errors

abbrev SensorId := UInt16
abbrev SensorChannelId := UInt16

inductive SensorKind
| passive
| active
| hybrid
| directional
| array
| manifoldProbe
  deriving Repr, DecidableEq

inductive SensorModality
| rf
| microwave
| infrared
| visible
| ultraviolet
| magnetic
| plasma
| boundary
| causal
| hybrid
  deriving Repr, DecidableEq

inductive SensorRegime
| dormant
| listening
| probing
| tracking
| saturated
| occluded
| gated
  deriving Repr, DecidableEq

inductive DetectionClass
| none
| weak
| coherent
| resonant
| anomalous
| critical
  deriving Repr, DecidableEq


inductive SensorErrorDisposition
| clear
| scaffold
| inspect
| intervene
  deriving Repr, DecidableEq

structure SensorErrorAssessment where
  errorField : ErrorField
  classification : ErrorClassification
  disposition : SensorErrorDisposition
  deriving Repr, DecidableEq

structure SensorBandWindow where
  primaryBand : SpectrumBand
  acceptsAdjacentBands : Bool
  minimumIntensity : FixedPoint.Q16_16
  maximumIntensity : FixedPoint.Q16_16
  deriving Repr, DecidableEq

structure SensorAperture where
  directionalBias : FixedPoint.Q16_16
  fieldWidth : FixedPoint.Q16_16
  lineOfSightRequired : Bool
  boundaryPenetration : FixedPoint.Q16_16
  deriving Repr, DecidableEq

structure SensorCarrierProfile where
  role : CarrierRole
  interactionClass : InteractionClass
  propagationClass : PropagationClass
  deriving Repr, DecidableEq

structure SensorSample where
  band : SpectrumBand
  intensity : FixedPoint.Q16_16
  coherence : FixedPoint.Q16_16
  delayMass : FixedPoint.Q16_16
  regionId : RegionId
  boundaryFluidity : FixedPoint.Q16_16
  detectionClass : DetectionClass
  errorField : Option ErrorField
  deriving Repr, DecidableEq

structure SensorField where
  sensorId : SensorId
  label : String
  kind : SensorKind
  modality : SensorModality
  regime : SensorRegime
  window : SensorBandWindow
  aperture : SensorAperture
  carrierProfile : SensorCarrierProfile
  substrate : SubstrateProfile
  homeRegion : RegionId
  deriving Repr, DecidableEq

structure SensorChannel where
  channelId : SensorChannelId
  sourceRegion : RegionId
  targetRegion : RegionId
  preferredOrientation : CausalOrientation
  minimumCoherence : FixedPoint.Q16_16
  supportsBoundaryCrossing : Bool
  deriving Repr, DecidableEq

structure SensorDetection where
  sample : SensorSample
  confidence : FixedPoint.Q16_16
  admissible : Bool
  errorAssessment : Option SensorErrorAssessment
  deriving Repr, DecidableEq


def modalityBandCompatible (modality : SensorModality) (band : SpectrumBand) : Bool :=
  match modality, band with
  | .rf, .radio => true
  | .microwave, .microwave => true
  | .infrared, .infrared => true
  | .visible, .visible => true
  | .ultraviolet, .ultraviolet => true
  | .magnetic, .radio => true
  | .magnetic, .microwave => true
  | .plasma, _ => true
  | .boundary, _ => true
  | .causal, _ => true
  | .hybrid, _ => true
  | _, _ => false


def intensityWithinWindow (window : SensorBandWindow) (intensity : FixedPoint.Q16_16) : Bool :=
  FixedPoint.Q16_16.ge intensity window.minimumIntensity && FixedPoint.Q16_16.le intensity window.maximumIntensity


def bandAccepted (window : SensorBandWindow) (band : SpectrumBand) : Bool :=
  band = window.primaryBand || (window.acceptsAdjacentBands && (isRfBand band = isRfBand window.primaryBand || isOpticalBand band = isOpticalBand window.primaryBand))


def sampleCompatibleWithField (field : SensorField) (sample : SensorSample) : Bool :=
  modalityBandCompatible field.modality sample.band &&
  bandAccepted field.window sample.band &&
  intensityWithinWindow field.window sample.intensity &&
  supportsBand field.substrate sample.band


def sampleCompatibleWithBoundary
  (field : SensorField)
  (boundary : BoundaryLayer) : Bool :=
  compatibleWithBoundary field.substrate boundary &&
  (field.aperture.lineOfSightRequired = false || boundary.kind != BoundaryKind.spectralCurtain) &&
  (FixedPoint.Q16_16.le boundary.fluidity field.aperture.boundaryPenetration || field.carrierProfile.propagationClass = PropagationClass.penetrative)


def sampleCompatibleWithLink
  (field : SensorField)
  (link : CausalLink) : Bool :=
  compatibleWithLink field.substrate link &&
  (link.orientation = CausalOrientation.forward || field.kind = SensorKind.manifoldProbe || field.modality = SensorModality.causal)



def deriveErrorField (field : SensorField) (sample : SensorSample) : Option ErrorField :=
  if sample.regionId != field.homeRegion && FixedPoint.Q16_16.gt sample.boundaryFluidity field.aperture.boundaryPenetration then
    some
      { errorId := field.sensorId
      , kind := ErrorKind.boundaryLeak
      , magnitude := sample.intensity
      , coherence := sample.coherence
      , persistence := sample.delayMass
      , regionId := sample.regionId
      , fluidity := sample.boundaryFluidity
      , criticalLoad := sample.intensity }
  else if !sampleCompatibleWithField field { sample with errorField := none } then
    some
      { errorId := field.sensorId
      , kind := ErrorKind.carrierMismatch
      , magnitude := sample.intensity
      , coherence := sample.coherence
      , persistence := sample.delayMass
      , regionId := sample.regionId
      , fluidity := sample.boundaryFluidity
      , criticalLoad := FixedPoint.Q16_16.zero }
  else
    none


def classifyErrorDisposition (assessment : SensorErrorAssessment) : SensorErrorDisposition :=
  match assessment.classification.attention, assessment.classification.scaffoldingRole with
  | ErrorAttention.ignore, _ => SensorErrorDisposition.clear
  | ErrorAttention.monitor, ErrorScaffoldingRole.none => SensorErrorDisposition.inspect
  | ErrorAttention.scaffold, _ => SensorErrorDisposition.scaffold
  | _, role =>
      match role with
      | ErrorScaffoldingRole.none => SensorErrorDisposition.intervene
      | _ => if assessment.classification.stableForReuse then SensorErrorDisposition.scaffold else SensorErrorDisposition.intervene


def assessSensorError (field : SensorField) (sample : SensorSample) : Option SensorErrorAssessment :=
  match deriveErrorField field sample with
  | none => none
  | some errorField =>
      let classification := classifyErrorField errorField
      some { errorField := errorField, classification := classification, disposition := classifyErrorDisposition { errorField := errorField, classification := classification, disposition := SensorErrorDisposition.clear } }

def classifyDetectionClass (sample : SensorSample) : DetectionClass :=
  if FixedPoint.Q16_16.gt sample.intensity FixedPoint.Q16_16.ofNat 3 && FixedPoint.Q16_16.gt sample.coherence FixedPoint.Q16_16.ofRatio 1 2 then
    DetectionClass.resonant
  else if FixedPoint.Q16_16.gt sample.intensity FixedPoint.Q16_16.two then
    DetectionClass.coherent
  else if FixedPoint.Q16_16.gt sample.intensity FixedPoint.Q16_16.one then
    DetectionClass.weak
  else
    DetectionClass.none


def classifySensorRegime
  (field : SensorField)
  (sample : SensorSample) : SensorRegime :=
  if !sampleCompatibleWithField field sample then
    SensorRegime.gated
  else if FixedPoint.Q16_16.gt sample.intensity field.window.maximumIntensity then
    SensorRegime.saturated
  else if sample.regionId != field.homeRegion && field.aperture.lineOfSightRequired then
    SensorRegime.tracking
  else
    match field.kind with
    | SensorKind.passive => SensorRegime.listening
    | SensorKind.active => SensorRegime.probing
    | SensorKind.hybrid => SensorRegime.tracking
    | SensorKind.directional => SensorRegime.tracking
    | SensorKind.array => SensorRegime.listening
    | SensorKind.manifoldProbe => SensorRegime.probing


def detectionConfidence
  (field : SensorField)
  (sample : SensorSample) : FixedPoint.Q16_16 :=
  let base := FixedPoint.Q16_16.div (FixedPoint.Q16_16.add sample.intensity sample.coherence) FixedPoint.Q16_16.two
  if sampleCompatibleWithField field sample then
    base
  else
    FixedPoint.Q16_16.zero


def detectSample
  (field : SensorField)
  (sample : SensorSample) : SensorDetection :=
  let provisional := { sample with detectionClass := classifyDetectionClass sample, errorField := none }
  let errorAssessment := assessSensorError field provisional
  let classified := { provisional with errorField := errorAssessment.map (fun assessment => assessment.errorField) }
  { sample := classified
  , confidence := detectionConfidence field classified
  , admissible := sampleCompatibleWithField field classified
  , errorAssessment := errorAssessment }


def channelSupportsDetection
  (channel : SensorChannel)
  (detection : SensorDetection) : Bool :=
  channel.targetRegion = detection.sample.regionId &&
  FixedPoint.Q16_16.ge detection.sample.coherence channel.minimumCoherence


def fieldAdmitsTransition
  (field : SensorField)
  (channel : SensorChannel)
  (sample : SensorSample)
  (boundary? : Option BoundaryLayer)
  (link? : Option CausalLink) : Bool :=
  sampleCompatibleWithField field sample &&
  channelSupportsDetection channel (detectSample field sample) &&
  match boundary?, link? with
  | some boundary, some link => sampleCompatibleWithBoundary field boundary && sampleCompatibleWithLink field link
  | some boundary, none => sampleCompatibleWithBoundary field boundary
  | none, some link => sampleCompatibleWithLink field link
  | none, none => true


def wifiSensorField : SensorField :=
  { sensorId := 1
  , label := "wifiSensor"
  , kind := SensorKind.passive
  , modality := SensorModality.microwave
  , regime := SensorRegime.listening
  , window := { primaryBand := SpectrumBand.microwave, acceptsAdjacentBands := true, minimumIntensity := FixedPoint.Q16_16.zero, maximumIntensity := FixedPoint.Q16_16.ofNat 4 }
  , aperture := { directionalBias := FixedPoint.Q16_16.ofRatio 1 4, fieldWidth := FixedPoint.Q16_16.ofNat 3, lineOfSightRequired := false, boundaryPenetration := FixedPoint.Q16_16.two }
  , carrierProfile := { role := CarrierRole.communicationLink, interactionClass := InteractionClass.communication, propagationClass := PropagationClass.penetrative }
  , substrate := fpgaSubstrateProfile
  , homeRegion := 1 }


def opticalProbeField : SensorField :=
  { sensorId := 2
  , label := "opticalProbe"
  , kind := SensorKind.active
  , modality := SensorModality.visible
  , regime := SensorRegime.probing
  , window := { primaryBand := SpectrumBand.visible, acceptsAdjacentBands := false, minimumIntensity := FixedPoint.Q16_16.ofRatio 1 4, maximumIntensity := FixedPoint.Q16_16.ofNat 4 }
  , aperture := { directionalBias := FixedPoint.Q16_16.two, fieldWidth := FixedPoint.Q16_16.one, lineOfSightRequired := true, boundaryPenetration := FixedPoint.Q16_16.ofRatio 1 4 }
  , carrierProfile := { role := CarrierRole.activeProbe, interactionClass := InteractionClass.activeSensing, propagationClass := PropagationClass.lineOfSight }
  , substrate := fpgaSubstrateProfile
  , homeRegion := 1 }

end Semantics.SensorField
