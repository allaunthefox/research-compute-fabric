import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.ManifoldPotential
import Semantics.ManifoldStructures
import Semantics.Errors

namespace Semantics.CausalGeometry

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.ManifoldPotential
open Semantics.ManifoldStructures
open Semantics.Errors

abbrev CausalId := UInt16
abbrev NodeId := UInt16

inductive CausalCurvature
| flat
| convergent
| divergent
| singular
| chaotic
  deriving DecidableEq

inductive CausalRegime
| linear
| gated
| entrained
| reconnected
| collapsed
  deriving DecidableEq

structure CausalCone where
  forwardWeight : PhysicsScalar.Q16_16
  backwardWeight : PhysicsScalar.Q16_16
  lateralWeight : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  deriving DecidableEq

structure CausalNode where
  nodeId : NodeId
  label : String
  regionId : RegionId
  potential : ManifoldPotential
  cone : CausalCone

structure CausalLayer where
  layerId : CausalId
  nodes : List CausalNode
  globalCurvature : PhysicsScalar.Q16_16

structure CausalSignature where
  nodeCount : UInt16
  avgForwardWeight : PhysicsScalar.Q16_16
  avgCoherence : PhysicsScalar.Q16_16
  maxCurvature : PhysicsScalar.Q16_16
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole

structure CausalTransitionRequest where
  source : CausalLayer
  target : CausalLayer
  boundary : BoundaryLayer
  errorField? : Option ErrorField

structure CausalTransitionResult where
  accepted : Bool
  mergedLayer : CausalLayer
  signature : CausalSignature
  stability : PotentialStability
  requiresAttention : Bool


def nodeCoherenceOf (node : CausalNode) : PhysicsScalar.Q16_16 :=
  let base := node.cone.coherence
  let bias := node.potential.gradient.coherence
  PhysicsScalar.Q16_16.avg base bias


def classifyCausalCurvature (cone : CausalCone) : CausalCurvature :=
  if PhysicsScalar.Q16_16.gt cone.forwardWeight (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.one PhysicsScalar.Q16_16.half) then .convergent
  else if PhysicsScalar.Q16_16.gt cone.lateralWeight PhysicsScalar.Q16_16.one then .chaotic
  else if PhysicsScalar.Q16_16.gt cone.backwardWeight PhysicsScalar.Q16_16.one then .divergent
  else .flat


def causalSignatureOf (layer : CausalLayer) : CausalSignature :=
  let count := layer.nodes.length
  let forwardSum := layer.nodes.foldl (fun acc node => PhysicsScalar.Q16_16.addSaturating acc node.cone.forwardWeight) PhysicsScalar.Q16_16.zero
  let coherenceSum := layer.nodes.foldl (fun acc node => PhysicsScalar.Q16_16.addSaturating acc (nodeCoherenceOf node)) PhysicsScalar.Q16_16.zero
  let div := if count = 0 then 1 else count
  { nodeCount := UInt16.ofNat count
  , avgForwardWeight := PhysicsScalar.Q16_16.divQ16_16 forwardSum (UInt32.ofNat div)
  , avgCoherence := PhysicsScalar.Q16_16.divQ16_16 coherenceSum (UInt32.ofNat div)
  , maxCurvature := layer.globalCurvature
  , aliasDetected := false
  , scaffoldingRole := .none }


def mergeLayers (request : CausalTransitionRequest) : CausalLayer :=
  let mergedNodes := request.source.nodes ++ request.target.nodes
  { layerId := request.source.layerId
  , nodes := mergedNodes
  , globalCurvature := PhysicsScalar.Q16_16.avg request.source.globalCurvature request.target.globalCurvature }


def processCausalTransition (request : CausalTransitionRequest) : CausalTransitionResult :=
  let merged := mergeLayers request
  let signature := causalSignatureOf merged
  { accepted := true
  , mergedLayer := merged
  , signature := signature
  , stability := .pStable
  , requiresAttention := false }

end Semantics.CausalGeometry
