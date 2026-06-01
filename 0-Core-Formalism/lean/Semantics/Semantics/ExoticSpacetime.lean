import Semantics.PhysicsScalarBridge
import Semantics.PhysicsEuclidean
import Semantics.PhysicsLagrangian
import Semantics.RegimeCore

namespace Semantics.ExoticSpacetime

open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean
open Semantics.PhysicsLagrangian
open Semantics.RegimeCore

abbrev TemporalOrder := UInt16
abbrev CurveId := UInt16
abbrev ConnectorId := UInt16
abbrev RegionClockId := UInt16

inductive SignatureClass
| spacelike
| timelike
| nullLike
| mixed
  deriving Repr, DecidableEq

inductive TemporalRegime
| monotonic
| dilated
| branched
| cyclic
| suspended
| unresolved
  deriving Repr, DecidableEq

inductive CausalStatus
| admissible
| guarded
| rejected
  deriving Repr, DecidableEq

inductive ConnectorKind
| throatBridge
| wormholeLike
| foldBridge
| sliceBridge
| delayBridge
  deriving Repr, DecidableEq

structure TemporalDifferential where
  localStep : PhysicsScalar.Q16_16
  externalStep : PhysicsScalar.Q16_16
  drift : PhysicsScalar.Q16_16
  dilation : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure CausalCone where
  forwardWeight : PhysicsScalar.Q16_16
  backwardWeight : PhysicsScalar.Q16_16
  lateralWeight : PhysicsScalar.Q16_16
  signature : SignatureClass
  deriving Repr, DecidableEq

structure ExoticRegionProfile where
  regionId : RegionId
  clockId : RegionClockId
  temporalRegime : TemporalRegime
  baseDifferential : TemporalDifferential
  cone : CausalCone
  permitsClosedTraversal : Bool
  permitsDimFold : Bool
  deriving Repr, DecidableEq

structure TimelikeCurve where
  curveId : CurveId
  label : String
  sourceRegionId : RegionId
  targetRegionId : RegionId
  temporalOrder : TemporalOrder
  differential : TemporalDifferential
  cone : CausalCone
  stable : Bool
  deriving Repr, DecidableEq

structure WormholeConnector where
  connectorId : ConnectorId
  label : String
  kind : ConnectorKind
  mouthARegionId : RegionId
  mouthBRegionId : RegionId
  entryDifferential : TemporalDifferential
  exitDifferential : TemporalDifferential
  requiresResolvedGate : Bool
  active : Bool
  deriving Repr, DecidableEq

structure ExoticTransitionRequest (n : Nat) where
  state : PhysicsLagrangian n
  sourceRegionId : RegionId
  targetRegionId : RegionId
  temporalDifferential : TemporalDifferential
  requestedOrder : TemporalOrder

structure ExoticTransitionResult (n : Nat) where
  status : CausalStatus
  resultingState : PhysicsLagrangian n
  resultingRegime : TemporalRegime
  usedConnector? : Option ConnectorId


def zeroDifferential : TemporalDifferential :=
  { localStep := PhysicsScalarBridge.zero
  , externalStep := PhysicsScalarBridge.zero
  , drift := PhysicsScalarBridge.zero
  , dilation := PhysicsScalarBridge.one
  , coherence := PhysicsScalarBridge.one }


def unitCone : CausalCone :=
  { forwardWeight := PhysicsScalarBridge.one
  , backwardWeight := PhysicsScalarBridge.zero
  , lateralWeight := PhysicsScalarBridge.zero
  , signature := .timelike }


def classifySignature (cone : CausalCone) : SignatureClass :=
  if PhysicsScalarBridge.gt cone.forwardWeight cone.backwardWeight && PhysicsScalarBridge.gt cone.forwardWeight cone.lateralWeight then
    .timelike
  else if PhysicsScalarBridge.eq cone.forwardWeight cone.backwardWeight && PhysicsScalarBridge.gt cone.forwardWeight PhysicsScalarBridge.zero then
    .nullLike
  else if PhysicsScalarBridge.gt cone.lateralWeight cone.forwardWeight then
    .spacelike
  else
    .mixed


def temporalRatio (differential : TemporalDifferential) : PhysicsScalar.Q16_16 :=
  PhysicsScalarBridge.divQ16_16 differential.externalStep (PhysicsScalarBridge.max differential.localStep PhysicsScalarBridge.one)


def temporalGradient (differential : TemporalDifferential) : PhysicsScalar.Q16_16 :=
  PhysicsScalarBridge.absDiff differential.externalStep PhysicsScalarBridge.zero -- simplified for now


def classifyTemporalRegime (differential : TemporalDifferential) (cone : CausalCone) : TemporalRegime :=
  if PhysicsScalarBridge.isZero differential.coherence then
    .unresolved
  else if PhysicsScalarBridge.eq cone.backwardWeight PhysicsScalarBridge.zero && PhysicsScalarBridge.ge differential.dilation PhysicsScalarBridge.one then
    .monotonic
  else if PhysicsScalarBridge.gt differential.dilation PhysicsScalarBridge.one then
    .dilated
  else if PhysicsScalarBridge.nonZero cone.backwardWeight then
    .cyclic
  else if PhysicsScalarBridge.nonZero differential.drift then
    .branched
  else
    .suspended


def permitsTimelikeTraversal (cone : CausalCone) : Bool :=
  match classifySignature cone with
  | .timelike | .nullLike => true
  | .spacelike | .mixed => false


def differentialCompatible
  (source target : ExoticRegionProfile)
  (request : TemporalDifferential) : Bool :=
  let localOk := PhysicsScalarBridge.ge request.localStep source.baseDifferential.localStep
  let coherenceOk := PhysicsScalarBridge.ge request.coherence (PhysicsScalarBridge.min source.baseDifferential.coherence target.baseDifferential.coherence)
  let dilationOk :=
    PhysicsScalarBridge.betweenInclusive request.dilation PhysicsScalarBridge.half PhysicsScalarBridge.four
  localOk && coherenceOk && dilationOk


def causalStatusFor
  (source target : ExoticRegionProfile)
  (request : TemporalDifferential) : CausalStatus :=
  if !permitsTimelikeTraversal source.cone || !permitsTimelikeTraversal target.cone then
    .rejected
  else if !differentialCompatible source target request then
    .guarded
  else
    .admissible


def applyTemporalDifferential (state : PhysicsLagrangian n) (differential : TemporalDifferential) : PhysicsLagrangian n :=
  let scaledVelocity := PhysicsEuclidean.scale differential.dilation state.velocity
  let shiftedMomentum := PhysicsEuclidean.scale (PhysicsScalarBridge.max differential.coherence PhysicsScalarBridge.half) state.momentum
  let updatedAction := PhysicsScalarBridge.add state.actionDensity (temporalGradient differential)
  { state with
    velocity := scaledVelocity
    momentum := shiftedMomentum
    actionDensity := updatedAction }


def findRegionProfile?
  (profiles : List ExoticRegionProfile)
  (regionId : RegionId) : Option ExoticRegionProfile :=
  profiles.find? (fun profile => profile.regionId = regionId)


def findConnector?
  (connectors : List WormholeConnector)
  (sourceRegionId targetRegionId : RegionId) : Option WormholeConnector :=
  connectors.find? (fun connector =>
    connector.active &&
    ((connector.mouthARegionId = sourceRegionId && connector.mouthBRegionId = targetRegionId) ||
     (connector.mouthBRegionId = sourceRegionId && connector.mouthARegionId = targetRegionId)))


def connectorMatchesRequest
  (connector : WormholeConnector)
  (sourceRegionId targetRegionId : RegionId) : Bool :=
  connector.active &&
  ((connector.mouthARegionId = sourceRegionId && connector.mouthBRegionId = targetRegionId) ||
   (connector.mouthBRegionId = sourceRegionId && connector.mouthARegionId = targetRegionId))


def traverseExoticTransition
  (profiles : List ExoticRegionProfile)
  (connectors : List WormholeConnector)
  (request : ExoticTransitionRequest n) : ExoticTransitionResult n :=
  match findRegionProfile? profiles request.sourceRegionId, findRegionProfile? profiles request.targetRegionId with
  | some source, some target =>
      let status := causalStatusFor source target request.temporalDifferential
      let connector? := findConnector? connectors request.sourceRegionId request.targetRegionId
      let gatedStatus :=
        match connector? with
        | some connector =>
            if connector.requiresResolvedGate && status != .admissible then .guarded else status
        | none => status
      let resultingState :=
        match gatedStatus with
        | .admissible => applyTemporalDifferential request.state request.temporalDifferential
        | .guarded | .rejected => request.state
      let resultingRegime := classifyTemporalRegime request.temporalDifferential target.cone
      { status := gatedStatus
      , resultingState := resultingState
      , resultingRegime := resultingRegime
      , usedConnector? := connector?.map (fun connector => connector.connectorId) }
  | _, _ =>
      { status := .rejected
      , resultingState := request.state
      , resultingRegime := .unresolved
      , usedConnector? := none }


def flatlandRegionProfile (regionId : RegionId) : ExoticRegionProfile :=
  { regionId := regionId
  , clockId := 1
  , temporalRegime := .monotonic
  , baseDifferential :=
      { localStep := PhysicsScalarBridge.one
      , externalStep := PhysicsScalarBridge.one
      , drift := PhysicsScalarBridge.zero
      , dilation := PhysicsScalarBridge.one
      , coherence := PhysicsScalarBridge.one }
  , cone :=
      { forwardWeight := PhysicsScalarBridge.one
      , backwardWeight := PhysicsScalarBridge.zero
      , lateralWeight := PhysicsScalarBridge.half
      , signature := .timelike }
  , permitsClosedTraversal := false
  , permitsDimFold := true }


def wormholeRegionProfile (regionId : RegionId) : ExoticRegionProfile :=
  { regionId := regionId
  , clockId := 2
  , temporalRegime := .dilated
  , baseDifferential :=
      { localStep := PhysicsScalarBridge.one
      , externalStep := PhysicsScalarBridge.two
      , drift := PhysicsScalarBridge.half
      , dilation := PhysicsScalarBridge.two
      , coherence := PhysicsScalarBridge.three }
  , cone :=
      { forwardWeight := PhysicsScalarBridge.three
      , backwardWeight := PhysicsScalarBridge.quarter
      , lateralWeight := PhysicsScalarBridge.one
      , signature := .mixed }
  , permitsClosedTraversal := true
  , permitsDimFold := true }


def defaultWormholeConnector (sourceRegionId targetRegionId : RegionId) : WormholeConnector :=
  { connectorId := 1
  , label := "defaultWormholeConnector"
  , kind := .wormholeLike
  , mouthARegionId := sourceRegionId
  , mouthBRegionId := targetRegionId
  , entryDifferential :=
      { localStep := PhysicsScalarBridge.one
      , externalStep := PhysicsScalarBridge.two
      , drift := PhysicsScalarBridge.half
      , dilation := PhysicsScalarBridge.two
      , coherence := PhysicsScalarBridge.two }
  , exitDifferential :=
      { localStep := PhysicsScalarBridge.one
      , externalStep := PhysicsScalarBridge.one
      , drift := PhysicsScalarBridge.zero
      , dilation := PhysicsScalarBridge.one
      , coherence := PhysicsScalarBridge.one }
  , requiresResolvedGate := true
  , active := true }

end Semantics.ExoticSpacetime
