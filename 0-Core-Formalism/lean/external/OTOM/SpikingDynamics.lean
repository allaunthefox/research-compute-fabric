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
  deriving Repr, DecidableEq

inductive SpikingRegime
| quiescent
| integrating
| firing
| refractory
| oscillatory
| gated
  deriving Repr, DecidableEq

inductive EmHookMode
| disabled
| passiveSense
| activeCoupling
| carrierDrive
  deriving Repr, DecidableEq

inductive TemporalHookMode
| localOnly
| dilated
| causallyGated
| curveAligned
  deriving Repr, DecidableEq

inductive RegionHookMode
| unrestricted
| regimeChecked
| gateChecked
| partitionChecked
  deriving Repr, DecidableEq

inductive EmissionStatus
| emitted
| suppressed
| blocked
  deriving Repr, DecidableEq

structure MembraneState where
  potential : Q16_16
  threshold : Q16_16
  leak : Q16_16
  refractoryLevel : Q16_16
  recovery : Q16_16
  coherence : Q16_16
  deriving Repr, DecidableEq

structure SpikeEvent where
  eventId : SpikeEventId
  originNodeId : SpikeNodeId
  intensity : Q16_16
  polarity : SpikePolarity
  temporalOrder : TemporalOrder
  carrier? : Option NamedCarrier
  deriving Repr, DecidableEq

structure SynapticGate where
  synapseId : SynapseId
  sourceNodeId : SpikeNodeId
  targetNodeId : SpikeNodeId
  gain : Q16_16
  delay : Q16_16
  openThreshold : Q16_16
  polarity : SpikePolarity
  requiresSpectralMatch : Bool
  deriving Repr, DecidableEq

structure SpikingNode (n : Nat) where
  nodeId : SpikeNodeId
  kinematics : PhysicsLagrangian n
  membrane : MembraneState
  regionId : RegionId
  regime : SpikingRegime
  deriving Repr, DecidableEq

structure ElectromagneticHook where
  mode : EmHookMode
  admittedBands : List SpectrumBand
  minimumIntensity : Q16_16
  minimumCoherence : Q16_16
  requiredRole? : Option CarrierRole
  allowedCarriers : List NamedCarrier
  deriving Repr, DecidableEq

structure TemporalHook where
  mode : TemporalHookMode
  minimumCoherence : Q16_16
  admittedTemporalRegimes : List TemporalRegime
  requiresTimelikeAdmissibility : Bool
  deriving Repr, DecidableEq

structure RegionHook where
  mode : RegionHookMode
  sourceRegionId : RegionId
  targetRegionId : RegionId
  admittedRegimes : List RegimeClass
  deriving Repr, DecidableEq

structure SpikingApiSurface where
  emHook? : Option ElectromagneticHook
  temporalHook? : Option TemporalHook
  regionHook? : Option RegionHook
  deriving Repr, DecidableEq

structure SpikingTransitionRequest (n : Nat) where
  node : SpikingNode n
  incomingCharge : Q16_16
  gate : SynapticGate
  event : SpikeEvent
  apiSurface : SpikingApiSurface
  sample? : Option ElectromagneticSample
  sourceTemporalRegime : TemporalRegime
  targetTemporalRegime : TemporalRegime
  sourceRegimeClass : RegimeClass
  targetRegimeClass : RegimeClass
  deriving Repr, DecidableEq

structure SpikingTransitionResult (n : Nat) where
  status : EmissionStatus
  updatedNode : SpikingNode n
  emittedEvent? : Option SpikeEvent
  resolvedRegime : SpikingRegime
  deriving Repr, DecidableEq


def defaultMembraneState : MembraneState :=
  { potential := Q16_16.zero
  , threshold := Q16_16.one
  , leak := Q16_16.quarter
  , refractoryLevel := Q16_16.zero
  , recovery := Q16_16.half
  , coherence := Q16_16.one }


def defaultSpikingApiSurface : SpikingApiSurface :=
  { emHook? := none
  , temporalHook? := none
  , regionHook? := none }


def isCarrierAllowed (hook : ElectromagneticHook) (event : SpikeEvent) : Bool :=
  match event.carrier? with
  | none => hook.allowedCarriers.isEmpty
  | some carrier => hook.allowedCarriers.isEmpty || carrier ∈ hook.allowedCarriers


def namedCarrierToBand (carrier : NamedCarrier) : SpectrumBand :=
  match carrier with
  | .genericRadio | .cellular | .gps => .radio
  | .wifi | .bluetooth | .radar => .microwave
  | .infraredLink => .infrared
  | .lidar | .visibleLight => .visible
  | .ultravioletSource => .ultraviolet
  | .xrayImaging => .xray
  | .gammaBurst => .gamma


def eventCompatibleWithEm
  (hook : ElectromagneticHook)
  (event : SpikeEvent)
  (sample? : Option ElectromagneticSample) : Bool :=
  match hook.mode with
  | .disabled => true
  | .passiveSense | .activeCoupling | .carrierDrive =>
      let carrierOk := isCarrierAllowed hook event
      let sampleOk :=
        match sample? with
        | none => hook.mode = .carrierDrive && carrierOk
        | some sample =>
            let bandOk := sample.bandProfile.band ∈ hook.admittedBands
            let intensityOk := Q16_16.ge sample.intensity hook.minimumIntensity
            let coherenceOk := Q16_16.ge sample.coherence hook.minimumCoherence
            let roleOk :=
              match hook.requiredRole? with
              | none => true
              | some role => sample.role = role
            bandOk && intensityOk && coherenceOk && roleOk
      carrierOk && sampleOk


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


def integratePotential (membrane : MembraneState) (incomingCharge gain : Q16_16) : MembraneState :=
  let driven := Q16_16.mulQ16_16 incomingCharge gain
  { membrane with potential := Q16_16.add membrane.potential driven }


def applyLeak (membrane : MembraneState) : MembraneState :=
  { membrane with potential := Q16_16.subSaturating membrane.potential membrane.leak }


def applyRefractoryClamp (membrane : MembraneState) : MembraneState :=
  let lowered := Q16_16.subSaturating membrane.refractoryLevel membrane.recovery
  { membrane with refractoryLevel := lowered }


def membraneReadyToFire (membrane : MembraneState) : Bool :=
  Q16_16.ge membrane.potential membrane.threshold && Q16_16.isZero membrane.refractoryLevel


def classifySpikingRegime (membrane : MembraneState) : SpikingRegime :=
  if membraneReadyToFire membrane then
    .firing
  else if Q16_16.nonZero membrane.refractoryLevel then
    .refractory
  else if Q16_16.ge membrane.potential Q16_16.half then
    .integrating
  else if Q16_16.nonZero membrane.coherence then
    .oscillatory
  else
    .quiescent


def gatedIntensity (event : SpikeEvent) (gate : SynapticGate) : Q16_16 :=
  let driven := Q16_16.mulQ16_16 event.intensity gate.gain
  if Q16_16.ge driven gate.openThreshold then driven else Q16_16.zero


def nextEventFromNode (node : SpikingNode n) (request : SpikingTransitionRequest n) : SpikeEvent :=
  { request.event with
    originNodeId := node.nodeId
    intensity := node.membrane.potential }


def updateNodeAfterEmission (node : SpikingNode n) : SpikingNode n :=
  let membrane :=
    { node.membrane with
      potential := Q16_16.zero
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
    let integrated := integratePotential request.node.membrane (Q16_16.add request.incomingCharge gatedCharge) request.gate.gain
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
  , minimumIntensity := Q16_16.eighth
  , minimumCoherence := Q16_16.quarter
  , requiredRole? := some .communicationLink
  , allowedCarriers := [.wifi, .bluetooth] }


def opticalSpikeHook : ElectromagneticHook :=
  { mode := .activeCoupling
  , admittedBands := [.infrared, .visible]
  , minimumIntensity := Q16_16.quarter
  , minimumCoherence := Q16_16.quarter
  , requiredRole? := none
  , allowedCarriers := [.lidar, .visibleLight, .infraredLink] }


def defaultTemporalSpikeHook : TemporalHook :=
  { mode := .causallyGated
  , minimumCoherence := Q16_16.quarter
  , admittedTemporalRegimes := [.monotonic, .dilated, .branched]
  , requiresTimelikeAdmissibility := false }


def flatlandRegionHook (regionId : RegionId) : RegionHook :=
  { mode := .regimeChecked
  , sourceRegionId := regionId
  , targetRegionId := regionId
  , admittedRegimes := [.free, .boundary, .spectral] }

end Semantics.SpikingDynamics
