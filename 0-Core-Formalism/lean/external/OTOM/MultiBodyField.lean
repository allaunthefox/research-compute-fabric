import Semantics.PhysicsScalar
import Semantics.PhysicsEuclidean
import Semantics.PhysicsLagrangian
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.CriticalityDynamics
import Semantics.MagnetoPlasma
import Semantics.ElectromagneticSpectrum
import Semantics.SpikingDynamics

namespace Semantics.MultiBodyField

open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean
open Semantics.PhysicsLagrangian
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.CriticalityDynamics
open Semantics.MagnetoPlasma
open Semantics.ElectromagneticSpectrum
open Semantics.SpikingDynamics

abbrev MultiBodyAssemblyId := UInt16
abbrev InteractionEdgeId := UInt16
abbrev BodyGroupId := UInt16

inductive MultiBodyRegime
| sparse
| coherent
| clustered
| critical
| magnetoDominant
| boundaryDominant
| collapsed
  deriving Repr, DecidableEq

inductive InteractionMode
| dormant
| coupled
| gated
| resonant
| cascading
| blocked
  deriving Repr, DecidableEq

inductive CollectiveStability
| stable
| metastable
| unstable
| collapseProne
  deriving Repr, DecidableEq

structure MultiBodyNode (n : Nat) where
  nodeId : MagnetoBodyId
  label : String
  body : MagnetoPlasmaBody n
  assignment : RegionAssignment
  criticalSite? : Option CriticalSite
  spikeState? : Option MembraneState
  deriving Repr

structure InteractionEdge where
  edgeId : InteractionEdgeId
  sourceId : MagnetoBodyId
  targetId : MagnetoBodyId
  link : MagnetoBodyLink
  boundaryId? : Option BoundaryId
  baseCoupling : Q16_16
  spectralWeight : Q16_16
  criticalWeight : Q16_16
  enabled : Bool
  deriving Repr, DecidableEq

structure MultiBodyAssembly (n : Nat) where
  assemblyId : MultiBodyAssemblyId
  label : String
  nodes : List (MultiBodyNode n)
  edges : List InteractionEdge
  boundaries : List BoundaryLayer
  defaultSample? : Option ElectromagneticSample
  deriving Repr

structure MultiBodySignature where
  bodyCount : UInt16
  activeEdgeCount : UInt16
  couplingDensity : Q16_16
  boundaryPressure : Q16_16
  criticalPressure : Q16_16
  spectralCoherence : Q16_16
  magnetoAlignment : Q16_16
  spikeActivity : Q16_16
  deriving Repr, DecidableEq

structure MultiBodyTransitionRequest (n : Nat) where
  assembly : MultiBodyAssembly n
  sample? : Option ElectromagneticSample
  spikeEvent? : Option SpikeEvent
  preferCriticalRedistribution : Bool
  deriving Repr

structure MultiBodyTransitionResult (n : Nat) where
  assembly : MultiBodyAssembly n
  regime : MultiBodyRegime
  interactionMode : InteractionMode
  stability : CollectiveStability
  admitted : Bool
  deriving Repr


def nodeCount (assembly : MultiBodyAssembly n) : UInt16 :=
  UInt16.ofNat assembly.nodes.length


def activeEdges (assembly : MultiBodyAssembly n) : List InteractionEdge :=
  assembly.edges.filter (fun edge => edge.enabled)


def activeEdgeCount (assembly : MultiBodyAssembly n) : UInt16 :=
  UInt16.ofNat (activeEdges assembly).length


def findNode? (assembly : MultiBodyAssembly n) (nodeId : MagnetoBodyId) : Option (MultiBodyNode n) :=
  assembly.nodes.find? (fun node => node.nodeId = nodeId)


def findBoundary? (assembly : MultiBodyAssembly n) (boundaryId : BoundaryId) : Option BoundaryLayer :=
  assembly.boundaries.find? (fun boundary => boundary.boundaryId = boundaryId)


def bodySpectralAffinity
  (body : MagnetoPlasmaBody n)
  (sample? : Option ElectromagneticSample) : Q16_16 :=
  spectralAffinityOf body.spectralHook sample?


def nodeCriticalPressure (node : MultiBodyNode n) : Q16_16 :=
  match node.criticalSite? with
  | none => zero
  | some site =>
      let potential := potentialOf site
      mean3 potential.load potential.threshold potential.gradient


def nodeSpikeActivity (node : MultiBodyNode n) : Q16_16 :=
  match node.spikeState? with
  | none => zero
  | some state => mean3 state.potential state.threshold state.leak


def edgeBoundaryPressure (assembly : MultiBodyAssembly n) (edge : InteractionEdge) : Q16_16 :=
  match edge.boundaryId? with
  | none => zero
  | some boundaryId =>
      match findBoundary? assembly boundaryId with
      | none => zero
      | some boundary => mean3 boundary.tension boundary.permeability boundary.fluidity


def edgeEffectiveCoupling (assembly : MultiBodyAssembly n) (edge : InteractionEdge) : Q16_16 :=
  if !edge.enabled then
    zero
  else
    let boundaryPressure := edgeBoundaryPressure assembly edge
    let retained := subSaturating one boundaryPressure
    let weighted := mean3 edge.baseCoupling edge.spectralWeight edge.criticalWeight
    mulQ16_16 weighted retained


def foldNodes
  (nodes : List (MultiBodyNode n))
  (f : Q16_16 → MultiBodyNode n → Q16_16) : Q16_16 :=
  nodes.foldl f zero


def foldEdges
  (edges : List InteractionEdge)
  (f : Q16_16 → InteractionEdge → Q16_16) : Q16_16 :=
  edges.foldl f zero


def multiBodySignatureOf
  (assembly : MultiBodyAssembly n)
  (sample? : Option ElectromagneticSample) : MultiBodySignature :=
  let bodyCount := nodeCount assembly
  let activeCount := activeEdgeCount assembly
  let edgeSum := foldEdges (activeEdges assembly) (fun acc edge => addSaturating acc (edgeEffectiveCoupling assembly edge))
  let boundarySum := foldEdges (activeEdges assembly) (fun acc edge => addSaturating acc (edgeBoundaryPressure assembly edge))
  let criticalSum := foldNodes assembly.nodes (fun acc node => addSaturating acc (nodeCriticalPressure node))
  let spectralSum := foldNodes assembly.nodes (fun acc node => addSaturating acc (bodySpectralAffinity node.body sample?))
  let magnetoSum := foldNodes assembly.nodes (fun acc node => addSaturating acc node.body.core.coherence)
  let spikeSum := foldNodes assembly.nodes (fun acc node => addSaturating acc (nodeSpikeActivity node))
  let couplingDensity :=
    if bodyCount = 0 then zero else divQ16_16 edgeSum (UInt32.ofNat bodyCount.toNat)
  { bodyCount := bodyCount
  , activeEdgeCount := activeCount
  , couplingDensity := couplingDensity
  , boundaryPressure := if activeCount = 0 then zero else divQ16_16 boundarySum (UInt32.ofNat activeCount.toNat)
  , criticalPressure := if bodyCount = 0 then zero else divQ16_16 criticalSum (UInt32.ofNat bodyCount.toNat)
  , spectralCoherence := if bodyCount = 0 then zero else divQ16_16 spectralSum (UInt32.ofNat bodyCount.toNat)
  , magnetoAlignment := if bodyCount = 0 then zero else divQ16_16 magnetoSum (UInt32.ofNat bodyCount.toNat)
  , spikeActivity := if bodyCount = 0 then zero else divQ16_16 spikeSum (UInt32.ofNat bodyCount.toNat) }


def classifyInteractionMode (signature : MultiBodySignature) : InteractionMode :=
  if signature.activeEdgeCount = 0 then
    .dormant
  else if ge signature.criticalPressure one then
    .cascading
  else if ge signature.couplingDensity (add half quarter) && ge signature.spectralCoherence half then
    .resonant
  else if ge signature.boundaryPressure (add half quarter) then
    .gated
  else if ge signature.couplingDensity quarter then
    .coupled
  else
    .blocked


def classifyCollectiveStability (signature : MultiBodySignature) : CollectiveStability :=
  if ge signature.criticalPressure one && ge signature.boundaryPressure half then
    .collapseProne
  else if ge signature.criticalPressure (add half quarter) then
    .unstable
  else if ge signature.couplingDensity half && ge signature.magnetoAlignment half then
    .stable
  else
    .metastable


def classifyMultiBodyRegime (signature : MultiBodySignature) : MultiBodyRegime :=
  if ge signature.criticalPressure one then
    .collapsed
  else if ge signature.boundaryPressure (add half quarter) then
    .boundaryDominant
  else if ge signature.magnetoAlignment (add half quarter) then
    .magnetoDominant
  else if ge signature.criticalPressure half then
    .critical
  else if ge signature.couplingDensity half then
    .clustered
  else if ge signature.spectralCoherence quarter then
    .coherent
  else
    .sparse


def rewriteNodeList
  (nodes : List (MultiBodyNode n))
  (updated : MultiBodyNode n) : List (MultiBodyNode n) :=
  nodes.map (fun node => if node.nodeId = updated.nodeId then updated else node)


def applySpikeEventToNode
  (node : MultiBodyNode n)
  (event : SpikeEvent) : MultiBodyNode n :=
  match node.spikeState? with
  | none => node
  | some state =>
      let updatedState := { state with potential := addSaturating state.potential event.intensity }
      { node with spikeState? := some updatedState }


def propagateSpikeEvent
  (assembly : MultiBodyAssembly n)
  (event? : Option SpikeEvent) : MultiBodyAssembly n :=
  match event? with
  | none => assembly
  | some event =>
      match findNode? assembly event.originNodeId with
      | none => assembly
      | some sourceNode =>
          let activeTargets :=
            activeEdges assembly |>.filter (fun edge => edge.sourceId = sourceNode.nodeId && ge (edgeEffectiveCoupling assembly edge) quarter)
          let updatedNodes :=
            activeTargets.foldl
              (fun acc edge =>
                match acc.find? (fun node => node.nodeId = edge.targetId) with
                | none => acc
                | some target => rewriteNodeList acc (applySpikeEventToNode target event))
              assembly.nodes
          { assembly with nodes := updatedNodes }


def redistributeCriticalSites
  (assembly : MultiBodyAssembly n) : MultiBodyAssembly n :=
  let updatedNodes :=
    assembly.nodes.map (fun node =>
      match node.criticalSite? with
      | none => node
      | some site =>
          if siteUnstable site then
            let reduced := { site with load := remainingAfterTopple site }
            { node with criticalSite? := some reduced }
          else
            node)
  { assembly with nodes := updatedNodes }


def bodyAdmittedInRegion (node : MultiBodyNode n) : Bool :=
  match node.assignment.regimeClass with
  | .blocked => false
  | _ => true


def admittedAssembly (assembly : MultiBodyAssembly n) : Bool :=
  assembly.nodes.all bodyAdmittedInRegion


def processMultiBodyTransition
  (request : MultiBodyTransitionRequest n) : MultiBodyTransitionResult n :=
  let spikedAssembly := propagateSpikeEvent request.assembly request.spikeEvent?
  let stabilizedAssembly :=
    if request.preferCriticalRedistribution then redistributeCriticalSites spikedAssembly else spikedAssembly
  let signature := multiBodySignatureOf stabilizedAssembly request.sample?
  { assembly := stabilizedAssembly
  , regime := classifyMultiBodyRegime signature
  , interactionMode := classifyInteractionMode signature
  , stability := classifyCollectiveStability signature
  , admitted := admittedAssembly stabilizedAssembly }


def defaultAssembly (n : Nat) : MultiBodyAssembly n :=
  { assemblyId := 0
  , label := "defaultAssembly"
  , nodes := []
  , edges := []
  , boundaries := []
  , defaultSample? := none }

end Semantics.MultiBodyField
