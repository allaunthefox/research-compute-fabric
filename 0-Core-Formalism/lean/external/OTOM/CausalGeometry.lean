import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.ExoticSpacetime
import Semantics.ManifoldPotential

namespace Semantics.CausalGeometry

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.ExoticSpacetime
open Semantics.ManifoldPotential

abbrev CausalNodeId := UInt16
abbrev CausalLinkId := UInt16
abbrev CausalLayerId := UInt16

inductive CausalOrientation
| forward
| backward
| lateral
| cyclic
| folded
  deriving Repr, DecidableEq

inductive CausalCurvature
| flat
| bent
| throatBiased
| saddleBiased
| folded
  deriving Repr, DecidableEq

inductive CausalRegime
| open
| directed
| delayed
| cyclic
| branched
| gated
| trapped
  deriving Repr, DecidableEq

inductive CausalStability
| stable
| metastable
| unstable
| collapseProne
  deriving Repr, DecidableEq

inductive CausalAdmissibility
| admissible
| guarded
| blocked
  deriving Repr, DecidableEq

structure CausalMetric where
  forwardBias : Q16_16
  backwardBias : Q16_16
  lateralBias : Q16_16
  closureBias : Q16_16
  delayWeight : Q16_16
  deriving Repr, DecidableEq

structure CausalNode where
  nodeId : CausalNodeId
  regionId : RegionId
  layerId : CausalLayerId
  potentialId : PotentialId
  temporalRegime : TemporalRegime
  cone : CausalCone
  metric : CausalMetric
  deriving Repr, DecidableEq

structure CausalLink where
  linkId : CausalLinkId
  sourceNodeId : CausalNodeId
  targetNodeId : CausalNodeId
  orientation : CausalOrientation
  strength : Q16_16
  delay : Q16_16
  permeability : Q16_16
  requiresGate : Bool
  deriving Repr, DecidableEq

structure CausalLayer where
  layerId : CausalLayerId
  anchorRegionId : RegionId
  nodes : List CausalNode
  links : List CausalLink
  potential : ManifoldPotential
  regime : CausalRegime
  stability : CausalStability
  deriving Repr, DecidableEq

structure CausalSignature where
  forwardFlux : Q16_16
  backwardFlux : Q16_16
  lateralFlux : Q16_16
  closureFlux : Q16_16
  delayMass : Q16_16
  throatBias : Q16_16
  coherence : Q16_16
  deriving Repr, DecidableEq

structure CausalTransitionRequest where
  source : CausalLayer
  target : CausalLayer
  connector? : Option WormholeConnector
  requireClosedTraversal : Bool
  deriving Repr, DecidableEq

structure CausalTransitionResult where
  status : CausalAdmissibility
  resultingLayer : CausalLayer
  signature : CausalSignature
  deriving Repr, DecidableEq


def zeroMetric : CausalMetric :=
  { forwardBias := PhysicsScalar.one
  , backwardBias := PhysicsScalar.zero
  , lateralBias := PhysicsScalar.zero
  , closureBias := PhysicsScalar.zero
  , delayWeight := PhysicsScalar.zero }


def addLinkMeasure (links : List CausalLink) (project : CausalLink → Q16_16) : Q16_16 :=
  links.foldl (fun acc link => PhysicsScalar.add acc (project link)) PhysicsScalar.zero


def nodeCoherenceOf (nodes : List CausalNode) : Q16_16 :=
  let coherences :=
    nodes.map (fun node =>
      Q16_16.min node.metric.forwardBias node.cone.forwardWeight)
  coherences.foldl PhysicsScalar.add PhysicsScalar.zero


def classifyCausalCurvature (cone : CausalCone) (potential : ManifoldPotential) : CausalCurvature :=
  match potential.basin.morphology with
  | PotentialMorphology.throat => .throatBiased
  | PotentialMorphology.saddle => .saddleBiased
  | PotentialMorphology.spiral | PotentialMorphology.web => .folded
  | _ =>
      if Q16_16.gt cone.lateralWeight cone.forwardWeight then .bent else .flat


def classifyCausalRegime (signature : CausalSignature) (curvature : CausalCurvature) : CausalRegime :=
  match curvature with
  | .folded => CausalRegime.cyclic
  | .throatBiased => CausalRegime.trapped
  | .saddleBiased => CausalRegime.branched
  | .flat | .bent =>
      if PhysicsScalar.gt signature.delayMass PhysicsScalar.one then
        .delayed
      else if PhysicsScalar.gt signature.backwardFlux PhysicsScalar.zero then
        .gated
      else if PhysicsScalar.gt signature.forwardFlux signature.lateralFlux then
        .directed
      else
        .open


def classifyCausalStability (signature : CausalSignature) : CausalStability :=
  if PhysicsScalar.gt signature.closureFlux PhysicsScalar.two then
    .collapseProne
  else if PhysicsScalar.gt signature.backwardFlux signature.forwardFlux then
    .unstable
  else if PhysicsScalar.gt signature.delayMass PhysicsScalar.one then
    .metastable
  else
    .stable


def causalSignatureOf (layer : CausalLayer) : CausalSignature :=
  let forwardFlux := addLinkMeasure layer.links (fun link =>
    match link.orientation with
    | .forward => link.strength
    | _ => PhysicsScalar.zero)
  let backwardFlux := addLinkMeasure layer.links (fun link =>
    match link.orientation with
    | .backward => link.strength
    | _ => PhysicsScalar.zero)
  let lateralFlux := addLinkMeasure layer.links (fun link =>
    match link.orientation with
    | .lateral => link.strength
    | _ => PhysicsScalar.zero)
  let closureFlux := addLinkMeasure layer.links (fun link =>
    match link.orientation with
    | .cyclic | .folded => link.strength
    | _ => PhysicsScalar.zero)
  let delayMass := addLinkMeasure layer.links (fun link => link.delay)
  let throatBias :=
    match layer.potential.basin.morphology with
    | PotentialMorphology.throat => layer.potential.basin.depth
    | _ => PhysicsScalar.zero
  { forwardFlux := forwardFlux
  , backwardFlux := backwardFlux
  , lateralFlux := lateralFlux
  , closureFlux := closureFlux
  , delayMass := delayMass
  , throatBias := throatBias
  , coherence := nodeCoherenceOf layer.nodes }


def nodeCompatibleWithPotential (node : CausalNode) (potential : ManifoldPotential) : Bool :=
  node.regionId = potential.anchorRegion ||
  potential.threads.any (fun thread => thread.sourceRegion = node.regionId || thread.targetRegion = node.regionId)


def layerCompatible (layer : CausalLayer) : Bool :=
  layer.nodes.all (fun node => nodeCompatibleWithPotential node layer.potential)


def connectorSupportsTransition
  (connector : WormholeConnector)
  (source target : CausalLayer) : Bool :=
  connector.active &&
  ((connector.mouthARegionId = source.anchorRegionId && connector.mouthBRegionId = target.anchorRegionId) ||
   (connector.mouthBRegionId = source.anchorRegionId && connector.mouthARegionId = target.anchorRegionId))


def transitionAdmissibility
  (source target : CausalLayer)
  (connector? : Option WormholeConnector)
  (requireClosedTraversal : Bool) : CausalAdmissibility :=
  if !layerCompatible source || !layerCompatible target then
    .blocked
  else
    match connector? with
    | some connector =>
        if connectorSupportsTransition connector source target then
          .admissible
        else
          .guarded
    | none =>
        if requireClosedTraversal then
          .guarded
        else if PhysicsScalar.gt (causalSignatureOf source).closureFlux PhysicsScalar.one then
          .guarded
        else
          .admissible


def mergeLinks (left right : List CausalLink) : List CausalLink :=
  left ++ right


def mergeLayers (source target : CausalLayer) : CausalLayer :=
  let mergedNodes := source.nodes ++ target.nodes
  let mergedLinks := mergeLinks source.links target.links
  let mergedPotential := mergePotentials source.potential target.potential
    { boundaryId := 0
    , sourceRegionId := source.anchorRegionId
    , targetRegionId := target.anchorRegionId
    , kind := .dimensionalSeam
    , thickness := PhysicsScalar.one
    , permeability := PhysicsScalar.half
    , fluidity := PhysicsScalar.half
    , spectralBias := PhysicsScalar.zero
    , regime := .gated
    , fluidityClass := .adaptive }
    { nodes := []
    , edges := []
    , manifoldLoad := PhysicsScalar.zero
    , avalancheClass := .none
    , status := .stable }
  let provisional : CausalLayer :=
    { layerId := source.layerId
    , anchorRegionId := source.anchorRegionId
    , nodes := mergedNodes
    , links := mergedLinks
    , potential := mergedPotential
    , regime := .open
    , stability := .stable }
  let signature := causalSignatureOf provisional
  let curvature := classifyCausalCurvature source.nodes.headD {
      nodeId := 0, regionId := source.anchorRegionId, layerId := source.layerId,
      potentialId := source.potential.potentialId, temporalRegime := .monotonic,
      cone := unitCone, metric := zeroMetric }.cone mergedPotential
  { provisional with
    regime := classifyCausalRegime signature curvature
    stability := classifyCausalStability signature }


def resolveCausalTransition (request : CausalTransitionRequest) : CausalTransitionResult :=
  let status := transitionAdmissibility request.source request.target request.connector? request.requireClosedTraversal
  let merged := mergeLayers request.source request.target
  let signature := causalSignatureOf merged
  { status := status
  , resultingLayer := merged
  , signature := signature }


end Semantics.CausalGeometry
