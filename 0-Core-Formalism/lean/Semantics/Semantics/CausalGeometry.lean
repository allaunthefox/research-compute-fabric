import Semantics.PhysicsScalarBridge
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
  PhysicsScalarBridge.avg base bias


def classifyCausalCurvature (cone : CausalCone) : CausalCurvature :=
  if PhysicsScalarBridge.gt cone.forwardWeight (PhysicsScalarBridge.add PhysicsScalarBridge.one PhysicsScalarBridge.half) then .convergent
  else if PhysicsScalarBridge.gt cone.lateralWeight PhysicsScalarBridge.one then .chaotic
  else if PhysicsScalarBridge.gt cone.backwardWeight PhysicsScalarBridge.one then .divergent
  else .flat


def causalSignatureOf (layer : CausalLayer) : CausalSignature :=
  let count := layer.nodes.length
  let forwardSum := layer.nodes.foldl (fun acc node => PhysicsScalarBridge.addSaturating acc node.cone.forwardWeight) PhysicsScalarBridge.zero
  let coherenceSum := layer.nodes.foldl (fun acc node => PhysicsScalarBridge.addSaturating acc (nodeCoherenceOf node)) PhysicsScalarBridge.zero
  let div := if count = 0 then 1 else count
  { nodeCount := UInt16.ofNat count
  , avgForwardWeight := PhysicsScalarBridge.divQ16_16 forwardSum (UInt32.ofNat div)
  , avgCoherence := PhysicsScalarBridge.divQ16_16 coherenceSum (UInt32.ofNat div)
  , maxCurvature := layer.globalCurvature
  , aliasDetected := false
  , scaffoldingRole := .none }


def mergeLayers (request : CausalTransitionRequest) : CausalLayer :=
  let mergedNodes := request.source.nodes ++ request.target.nodes
  { layerId := request.source.layerId
  , nodes := mergedNodes
  , globalCurvature := PhysicsScalarBridge.avg request.source.globalCurvature request.target.globalCurvature }


def processCausalTransition (request : CausalTransitionRequest) : CausalTransitionResult :=
  let merged := mergeLayers request
  let signature := causalSignatureOf merged
  { accepted := true
  , mergedLayer := merged
  , signature := signature
  , stability := .pStable
  , requiresAttention := false }

end Semantics.CausalGeometry
