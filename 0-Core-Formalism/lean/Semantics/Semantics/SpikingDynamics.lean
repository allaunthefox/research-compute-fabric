import Semantics.PhysicsScalar
import Semantics.PhysicsEuclidean
import Semantics.PhysicsLagrangian
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum
import Semantics.ExoticSpacetime

namespace Semantics.SpikingDynamics

open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean
open Semantics.PhysicsLagrangian
open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum
open Semantics.ExoticSpacetime

abbrev SpikeNodeId := UInt16
abbrev SpikeEventId := UInt16
abbrev SynapseId := UInt16

inductive SpikePolarity
| excitatory
| inhibitory
| modulatory
  deriving DecidableEq

inductive SpikingRegime
| quiescent
| integrating
| firing
| refractory
| oscillatory
| gated
  deriving DecidableEq

inductive EmHookMode
| disabled
| passiveSense
| activeCoupling
| carrierDrive
  deriving DecidableEq

inductive TemporalHookMode
| localOnly
| dilated
| causallyGated
| curveAligned
  deriving DecidableEq

inductive RegionHookMode
| unrestricted
| regimeChecked
| gateChecked
| partitionChecked
  deriving DecidableEq

inductive EmissionStatus
| emitted
| suppressed
| blocked
  deriving DecidableEq

structure MembraneState where
  potential : PhysicsScalar.Q16_16
  threshold : PhysicsScalar.Q16_16
  leak : PhysicsScalar.Q16_16
  refractoryLevel : PhysicsScalar.Q16_16
  recovery : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  deriving DecidableEq

structure SpikeEvent where
  eventId : SpikeEventId
  originNodeId : SpikeNodeId
  intensity : PhysicsScalar.Q16_16
  polarity : SpikePolarity
  temporalOrder : TemporalOrder
  deriving DecidableEq

structure SynapticGate where
  synapseId : SynapseId
  sourceNodeId : SpikeNodeId
  targetNodeId : SpikeNodeId
  gain : PhysicsScalar.Q16_16
  delay : PhysicsScalar.Q16_16
  openThreshold : PhysicsScalar.Q16_16
  polarity : SpikePolarity
  requiresSpectralMatch : Bool
  deriving DecidableEq

structure SpikingNode (n : Nat) where
  nodeId : SpikeNodeId
  kinematics : PhysicsLagrangian n
  membrane : MembraneState
  regionId : RegionId
  regime : SpikingRegime

structure ElectromagneticHook where
  mode : EmHookMode
  admittedBands : List SpectrumBand
  minimumIntensity : PhysicsScalar.Q16_16
  minimumCoherence : PhysicsScalar.Q16_16
  deriving DecidableEq

structure TemporalHook where
  mode : TemporalHookMode
  minimumCoherence : PhysicsScalar.Q16_16
  admittedTemporalRegimes : List TemporalRegime
  requiresTimelikeAdmissibility : Bool
  deriving DecidableEq

structure RegionHook where
  mode : RegionHookMode
  sourceRegionId : RegionId
  targetRegionId : RegionId
  admittedRegimes : List RegimeClass
  deriving DecidableEq

structure SpikingApiSurface where
  emHook? : Option ElectromagneticHook
  temporalHook? : Option TemporalHook
  regionHook? : Option RegionHook
  deriving DecidableEq

structure SpikingTransitionRequest (n : Nat) where
  node : SpikingNode n
  incomingCharge : PhysicsScalar.Q16_16
  gate : SynapticGate
  event : SpikeEvent
  apiSurface : SpikingApiSurface
  sample? : Option ElectromagneticSample
  sourceTemporalRegime : TemporalRegime
  targetTemporalRegime : TemporalRegime
  sourceRegimeClass : RegimeClass
  targetRegimeClass : RegimeClass

structure SpikingTransitionResult (n : Nat) where
  status : EmissionStatus
  updatedNode : SpikingNode n
  emittedEvent? : Option SpikeEvent
  resolvedRegime : SpikingRegime


def defaultMembraneState : MembraneState :=
  { potential := PhysicsScalar.Q16_16.zero
  , threshold := PhysicsScalar.Q16_16.one
  , leak := PhysicsScalar.Q16_16.quarter
  , refractoryLevel := PhysicsScalar.Q16_16.zero
  , recovery := PhysicsScalar.Q16_16.half
  , coherence := PhysicsScalar.Q16_16.one }


def defaultSpikingApiSurface : SpikingApiSurface :=
  { emHook? := none
  , temporalHook? := none
  , regionHook? := none }


def eventCompatibleWithEm
  (hook : ElectromagneticHook)
  (_event : SpikeEvent)
  (sample? : Option ElectromagneticSample) : Bool :=
  match hook.mode with
  | .disabled => true
  | .passiveSense | .activeCoupling | .carrierDrive =>
      match sample? with
      | none => hook.mode = .carrierDrive
      | some sample =>
          let bandOk := sample.bandProfile.band ∈ hook.admittedBands
          let intensityOk := PhysicsScalar.Q16_16.ge sample.bandProfile.intensity hook.minimumIntensity
          bandOk && intensityOk


def eventCompatibleWithTemporal
  (hook : TemporalHook)
  (sourceTemporalRegime targetTemporalRegime : TemporalRegime) : Bool :=
  match hook.mode with
  | .localOnly => sourceTemporalRegime = targetTemporalRegime
  | .dilated => targetTemporalRegime ∈ hook.admittedTemporalRegimes
  | .causallyGated => sourceTemporalRegime ∈ hook.admittedTemporalRegimes && targetTemporalRegime ∈ hook.admittedTemporalRegimes
  | .curveAligned => targetTemporalRegime = .cyclic || targetTemporalRegime = .branched


def eventCompatibleWithRegion
  (hook : RegionHook)
  (sourceRegionId targetRegionId : RegionId)
  (sourceRegimeClass targetRegimeClass : RegimeClass) : Bool :=
  match hook.mode with
  | .unrestricted => true
  | .regimeChecked => sourceRegimeClass ∈ hook.admittedRegimes && targetRegimeClass ∈ hook.admittedRegimes
  | .gateChecked | .partitionChecked =>
      hook.sourceRegionId = sourceRegionId &&
      hook.targetRegionId = targetRegionId &&
      sourceRegimeClass ∈ hook.admittedRegimes &&
      targetRegimeClass ∈ hook.admittedRegimes


def apiAllowsTransition
  (apiSurface : SpikingApiSurface)
  (event : SpikeEvent)
  (sample? : Option ElectromagneticSample)
  (sourceTemporalRegime targetTemporalRegime : TemporalRegime)
  (sourceRegionId targetRegionId : RegionId)
  (sourceRegimeClass targetRegimeClass : RegimeClass) : Bool :=
  let emOk :=
    match apiSurface.emHook? with
    | none => true
    | some hook => eventCompatibleWithEm hook event sample?
  let temporalOk :=
    match apiSurface.temporalHook? with
    | none => true
    | some hook => eventCompatibleWithTemporal hook sourceTemporalRegime targetTemporalRegime
  let regionOk :=
    match apiSurface.regionHook? with
    | none => true
    | some hook => eventCompatibleWithRegion hook sourceRegionId targetRegionId sourceRegimeClass targetRegimeClass
  emOk && temporalOk && regionOk


def integratePotential (membrane : MembraneState) (incomingCharge gain : PhysicsScalar.Q16_16) : MembraneState :=
  let driven := PhysicsScalar.Q16_16.mul incomingCharge gain
  { membrane with potential := PhysicsScalar.Q16_16.add membrane.potential driven }


def applyLeak (membrane : MembraneState) : MembraneState :=
  { membrane with potential := PhysicsScalar.Q16_16.sub membrane.potential membrane.leak }


def applyRefractoryClamp (membrane : MembraneState) : MembraneState :=
  let lowered := PhysicsScalar.Q16_16.sub membrane.refractoryLevel membrane.recovery
  { membrane with refractoryLevel := lowered }


def membraneReadyToFire (membrane : MembraneState) : Bool :=
  PhysicsScalar.Q16_16.ge membrane.potential membrane.threshold && PhysicsScalar.Q16_16.isZero membrane.refractoryLevel


def classifySpikingRegime (membrane : MembraneState) : SpikingRegime :=
  if membraneReadyToFire membrane then
    .firing
  else if PhysicsScalar.Q16_16.nonZero membrane.refractoryLevel then
    .refractory
  else if PhysicsScalar.Q16_16.ge membrane.potential PhysicsScalar.Q16_16.half then
    .integrating
  else if PhysicsScalar.Q16_16.nonZero membrane.coherence then
    .oscillatory
  else
    .quiescent


def gatedIntensity (event : SpikeEvent) (gate : SynapticGate) : PhysicsScalar.Q16_16 :=
  let driven := PhysicsScalar.Q16_16.mul event.intensity gate.gain
  if PhysicsScalar.Q16_16.ge driven gate.openThreshold then driven else PhysicsScalar.Q16_16.zero


def nextEventFromNode (node : SpikingNode n) (request : SpikingTransitionRequest n) : SpikeEvent :=
  { request.event with
    originNodeId := node.nodeId
    intensity := node.membrane.potential }


def updateNodeAfterEmission (node : SpikingNode n) : SpikingNode n :=
  let membrane :=
    { node.membrane with
      potential := PhysicsScalar.Q16_16.zero
      refractoryLevel := node.membrane.threshold }
  { node with membrane := membrane, regime := .refractory }


def processSpikeTransition
  (request : SpikingTransitionRequest n) : SpikingTransitionResult n :=
  let apiAllowed :=
    apiAllowsTransition
      request.apiSurface
      request.event
      request.sample?
      request.sourceTemporalRegime
      request.targetTemporalRegime
      request.node.regionId
      request.node.regionId
      request.sourceRegimeClass
      request.targetRegimeClass
  if !apiAllowed then
    { status := .blocked
    , updatedNode := request.node
    , emittedEvent? := none
    , resolvedRegime := request.node.regime }
  else
    let gatedCharge := gatedIntensity request.event request.gate
    let integrated := integratePotential request.node.membrane (PhysicsScalar.Q16_16.add request.incomingCharge gatedCharge) request.gate.gain
    let leaked := applyLeak integrated
    let recovered := applyRefractoryClamp leaked
    let updatedNode := { request.node with membrane := recovered, regime := classifySpikingRegime recovered }
    if membraneReadyToFire recovered then
      let emitted := nextEventFromNode updatedNode request
      let resetNode := updateNodeAfterEmission updatedNode
      { status := .emitted
      , updatedNode := resetNode
      , emittedEvent? := some emitted
      , resolvedRegime := resetNode.regime }
    else
      { status := .suppressed
      , updatedNode := updatedNode
      , emittedEvent? := none
      , resolvedRegime := updatedNode.regime }


def wifiSpikeHook : ElectromagneticHook :=
  { mode := .carrierDrive
  , admittedBands := [.microwave]
  , minimumIntensity := PhysicsScalar.Q16_16.eighth
  , minimumCoherence := PhysicsScalar.Q16_16.quarter }


def opticalSpikeHook : ElectromagneticHook :=
  { mode := .activeCoupling
  , admittedBands := [.infrared]
  , minimumIntensity := PhysicsScalar.Q16_16.quarter
  , minimumCoherence := PhysicsScalar.Q16_16.quarter }


def defaultTemporalSpikeHook : TemporalHook :=
  { mode := .causallyGated
  , minimumCoherence := PhysicsScalar.Q16_16.quarter
  , admittedTemporalRegimes := [.monotonic, .dilated, .branched]
  , requiresTimelikeAdmissibility := false }


def flatlandRegionHook (regionId : RegionId) : RegionHook :=
  { mode := .regimeChecked
  , sourceRegionId := regionId
  , targetRegionId := regionId
  , admittedRegimes := [.coherent, .transitional, .throat] }

end Semantics.SpikingDynamics
