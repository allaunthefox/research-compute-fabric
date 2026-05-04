import Semantics.PhysicsScalar
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
  localStep : Q16_16
  externalStep : Q16_16
  drift : Q16_16
  dilation : Q16_16
  coherence : Q16_16
  deriving Repr, DecidableEq

structure CausalCone where
  forwardWeight : Q16_16
  backwardWeight : Q16_16
  lateralWeight : Q16_16
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
  deriving Repr, DecidableEq

structure ExoticTransitionResult (n : Nat) where
  status : CausalStatus
  resultingState : PhysicsLagrangian n
  resultingRegime : TemporalRegime
  usedConnector? : Option ConnectorId
  deriving Repr, DecidableEq


def zeroDifferential : TemporalDifferential :=
  { localStep := Q16_16.zero
  , externalStep := Q16_16.zero
  , drift := Q16_16.zero
  , dilation := Q16_16.one
  , coherence := Q16_16.one }


def unitCone : CausalCone :=
  { forwardWeight := Q16_16.one
  , backwardWeight := Q16_16.zero
  , lateralWeight := Q16_16.zero
  , signature := .timelike }


def classifySignature (cone : CausalCone) : SignatureClass :=
  if Q16_16.gt cone.forwardWeight cone.backwardWeight && Q16_16.gt cone.forwardWeight cone.lateralWeight then
    .timelike
  else if Q16_16.eq cone.forwardWeight cone.backwardWeight && Q16_16.gt cone.forwardWeight Q16_16.zero then
    .nullLike
  else if Q16_16.gt cone.lateralWeight cone.forwardWeight then
    .spacelike
  else
    .mixed


def temporalRatio (differential : TemporalDifferential) : Q16_16 :=
  Q16_16.divQ16_16 differential.externalStep (Q16_16.max differential.localStep Q16_16.one)


def temporalGradient (differential : TemporalDifferential) : Q16_16 :=
  Q16_16.absDiff differential.externalStep differential.localStep


def classifyTemporalRegime (differential : TemporalDifferential) (cone : CausalCone) : TemporalRegime :=
  if Q16_16.isZero differential.coherence then
    .unresolved
  else if Q16_16.eq cone.backwardWeight Q16_16.zero && Q16_16.ge differential.dilation Q16_16.one then
    .monotonic
  else if Q16_16.gt differential.dilation Q16_16.one then
    .dilated
  else if Q16_16.nonZero cone.backwardWeight then
    .cyclic
  else if Q16_16.nonZero differential.drift then
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
  let localOk := Q16_16.ge request.localStep source.baseDifferential.localStep
  let coherenceOk := Q16_16.ge request.coherence (Q16_16.min source.baseDifferential.coherence target.baseDifferential.coherence)
  let dilationOk :=
    Q16_16.betweenInclusive request.dilation Q16_16.half (Q16_16.four)
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
  let scaledVelocity := PhysicsEuclidean.scale state.velocity differential.dilation
  let shiftedMomentum := PhysicsEuclidean.scale state.momentum (Q16_16.max differential.coherence Q16_16.half)
  let updatedAction := Q16_16.add state.actionDensity (temporalGradient differential)
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
      { localStep := Q16_16.one
      , externalStep := Q16_16.one
      , drift := Q16_16.zero
      , dilation := Q16_16.one
      , coherence := Q16_16.one }
  , cone :=
      { forwardWeight := Q16_16.one
      , backwardWeight := Q16_16.zero
      , lateralWeight := Q16_16.half
      , signature := .timelike }
  , permitsClosedTraversal := false
  , permitsDimFold := true }


def wormholeRegionProfile (regionId : RegionId) : ExoticRegionProfile :=
  { regionId := regionId
  , clockId := 2
  , temporalRegime := .dilated
  , baseDifferential :=
      { localStep := Q16_16.one
      , externalStep := Q16_16.two
      , drift := Q16_16.half
      , dilation := Q16_16.two
      , coherence := Q16_16.three }
  , cone :=
      { forwardWeight := Q16_16.three
      , backwardWeight := Q16_16.quarter
      , lateralWeight := Q16_16.one
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
      { localStep := Q16_16.one
      , externalStep := Q16_16.two
      , drift := Q16_16.half
      , dilation := Q16_16.two
      , coherence := Q16_16.two }
  , exitDifferential :=
      { localStep := Q16_16.one
      , externalStep := Q16_16.one
      , drift := Q16_16.zero
      , dilation := Q16_16.one
      , coherence := Q16_16.one }
  , requiresResolvedGate := true
  , active := true }

end Semantics.ExoticSpacetime
