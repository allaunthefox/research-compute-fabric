import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.CriticalityDynamics
import Semantics.MultiBodyField
import Semantics.CosmicStructure
import Semantics.Errors

namespace Semantics.ManifoldPotential

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.CriticalityDynamics
open Semantics.MultiBodyField
open Semantics.CosmicStructure
open Semantics.Errors

abbrev PotentialId := UInt16

inductive PotentialMorphology
| flat
| basin
| nestedBasin
| ridge
| throat
| saddle
| lattice
| spiral
| web
  deriving Repr, DecidableEq

inductive PotentialRegime
| quiescent
| guiding
| trapping
| critical
| cascading
| collapsed
  deriving Repr, DecidableEq

inductive PotentialBoundaryMode
| open
| gated
| reflective
| absorptive
| fluid
| reconnective
  deriving Repr, DecidableEq

inductive PotentialStability
| stable
| metastable
| unstable
| collapseProne
  deriving Repr, DecidableEq

structure PotentialCoordinate where
  radial : Q16_16
  angular : Q16_16
  depth : Q16_16
  deriving Repr, DecidableEq

structure PotentialGradient where
  inward : Q16_16
  tangential : Q16_16
  vertical : Q16_16
  coherence : Q16_16
  deriving Repr, DecidableEq

structure PotentialBasin where
  centerRegion : RegionId
  radius : Q16_16
  depth : Q16_16
  rimStrength : Q16_16
  nestedDepth : Q16_16
  morphology : PotentialMorphology
  deriving Repr, DecidableEq

structure PotentialThread where
  sourceRegion : RegionId
  targetRegion : RegionId
  pull : Q16_16
  torsion : Q16_16
  permeability : Q16_16
  deriving Repr, DecidableEq

structure ManifoldPotential where
  potentialId : PotentialId
  anchorRegion : RegionId
  coordinate : PotentialCoordinate
  gradient : PotentialGradient
  basin : PotentialBasin
  threads : List PotentialThread
  regime : PotentialRegime
  stability : PotentialStability
  boundaryMode : PotentialBoundaryMode
  scaffoldingRole : ErrorScaffoldingRole
  deriving Repr, DecidableEq

structure PotentialSignature where
  basinDepth : Q16_16
  rimStrength : Q16_16
  threadCount : UInt16
  totalPull : Q16_16
  boundaryFluidity : Q16_16
  criticalScore : Q16_16
  coherence : Q16_16
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  deriving Repr, DecidableEq

structure PotentialTransitionRequest where
  source : ManifoldPotential
  target : ManifoldPotential
  boundary : BoundaryLayer
  criticality : CriticalNetwork
  errorField? : Option ErrorField
  deriving Repr, DecidableEq

structure PotentialTransitionResult where
  accepted : Bool
  mergedPotential : ManifoldPotential
  signature : PotentialSignature
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  requiresAttention : Bool
  deriving Repr, DecidableEq


def addPulls (threads : List PotentialThread) : Q16_16 :=
  threads.foldl (fun acc thread => Q16_16.add acc thread.pull) Q16_16.zero


def explicitAliasDetected (request : PotentialTransitionRequest) : Bool :=
  request.source.anchorRegion = request.target.anchorRegion ||
  request.source.basin.centerRegion = request.target.basin.centerRegion ||
  request.boundary.sourceRegionId = request.boundary.targetRegionId


def threadAliasDetected (threads : List PotentialThread) : Bool :=
  threads.any (fun thread => thread.sourceRegion = thread.targetRegion)


def scaffoldingRoleOf (request : PotentialTransitionRequest) : ErrorScaffoldingRole :=
  match request.errorField? with
  | none => ErrorScaffoldingRole.none
  | some field => (classifyErrorField field).scaffoldingRole


def classifyPotentialMorphology (gradient : PotentialGradient) (basin : PotentialBasin) : PotentialMorphology :=
  if Q16_16.gt basin.nestedDepth Q16_16.zero then .nestedBasin
  else if Q16_16.gt basin.rimStrength basin.depth then .ridge
  else if Q16_16.gt gradient.tangential gradient.inward then .spiral
  else if Q16_16.gt gradient.vertical gradient.inward then .throat
  else if Q16_16.gt basin.depth Q16_16.half then .basin
  else .flat


def boundaryModeOf (boundary : BoundaryLayer) (role : ErrorScaffoldingRole) : PotentialBoundaryMode :=
  let fluidityClass := classifyBoundaryFluidity (boundarySignatureOf {
    boundary := boundary,
    sourceAssignment := { regionId := boundary.sourceRegionId, regimeClass := .transitional, resolutionStatus := .unresolved },
    targetAssignment := { regionId := boundary.targetRegionId, regimeClass := .transitional, resolutionStatus := .unresolved },
    sample? := none,
    sourceTemporalRegime := .synchronous,
    targetTemporalRegime := .synchronous,
    spikeEvent? := none,
    magnetoSignature? := none,
    errorField? := none })
  match role, fluidityClass with
  | .boundaryScaffold, _ => .fluid
  | .causalScaffold, _ => .gated
  | .criticalScaffold, _ => .reconnective
  | _, .rigid => .reflective
  | _, .viscous => .gated
  | _, .adaptive => .fluid
  | _, .diffuse => .open
  | _, .turbulent => .reconnective


def threadCountOf (threads : List PotentialThread) : UInt16 := UInt16.ofNat threads.length


def potentialSignatureOf (potential : ManifoldPotential) (boundary : BoundaryLayer) (criticality : CriticalNetwork) : PotentialSignature :=
  { basinDepth := potential.basin.depth
  , rimStrength := potential.basin.rimStrength
  , threadCount := threadCountOf potential.threads
  , totalPull := addPulls potential.threads
  , boundaryFluidity := boundary.fluidity
  , criticalScore := criticality.manifoldLoad
  , coherence := potential.gradient.coherence
  , aliasDetected := threadAliasDetected potential.threads
  , scaffoldingRole := potential.scaffoldingRole }


def classifyPotentialRegime (signature : PotentialSignature) : PotentialRegime :=
  if signature.aliasDetected then .collapsed
  else if Q16_16.gt signature.criticalScore Q16_16.three then .cascading
  else if Q16_16.gt signature.basinDepth Q16_16.two then .trapping
  else if Q16_16.gt signature.totalPull Q16_16.one then .guiding
  else if Q16_16.gt signature.rimStrength Q16_16.two then .critical
  else .quiescent


def classifyPotentialStability (signature : PotentialSignature) : PotentialStability :=
  if signature.aliasDetected then .collapseProne
  else if Q16_16.gt signature.criticalScore Q16_16.three then .collapseProne
  else if Q16_16.gt signature.boundaryFluidity Q16_16.two then .unstable
  else if Q16_16.gt signature.totalPull Q16_16.two then .metastable
  else .stable


def potentialCompatibleWithBoundary (potential : ManifoldPotential) (boundary : BoundaryLayer) : Bool :=
  match potential.boundaryMode with
  | .reflective => boundary.targetRegionId != potential.anchorRegion
  | .absorptive => boundary.kind != .interface
  | _ => true


def mergeBasins (left right : PotentialBasin) : PotentialBasin :=
  { centerRegion := left.centerRegion
  , radius := Q16_16.max left.radius right.radius
  , depth := Q16_16.avg left.depth right.depth
  , rimStrength := Q16_16.avg left.rimStrength right.rimStrength
  , nestedDepth := Q16_16.max left.nestedDepth right.nestedDepth
  , morphology := left.morphology }


def mergeGradients (left right : PotentialGradient) : PotentialGradient :=
  { inward := Q16_16.avg left.inward right.inward
  , tangential := Q16_16.avg left.tangential right.tangential
  , vertical := Q16_16.avg left.vertical right.vertical
  , coherence := Q16_16.avg left.coherence right.coherence }


def mergePotentials (request : PotentialTransitionRequest) : ManifoldPotential :=
  let mergedGradient := mergeGradients request.source.gradient request.target.gradient
  let mergedBasin := mergeBasins request.source.basin request.target.basin
  let mergedThreads := request.source.threads ++ request.target.threads
  let role := scaffoldingRoleOf request
  let provisional : ManifoldPotential :=
    { potentialId := request.source.potentialId
    , anchorRegion := request.source.anchorRegion
    , coordinate := request.source.coordinate
    , gradient := mergedGradient
    , basin := { mergedBasin with morphology := classifyPotentialMorphology mergedGradient mergedBasin }
    , threads := mergedThreads
    , regime := request.source.regime
    , stability := request.source.stability
    , boundaryMode := boundaryModeOf request.boundary role
    , scaffoldingRole := role }
  let signature := potentialSignatureOf provisional request.boundary request.criticality
  { provisional with
      regime := classifyPotentialRegime signature
      stability := classifyPotentialStability signature }


def processPotentialTransition (request : PotentialTransitionRequest) : PotentialTransitionResult :=
  let aliasDetected := explicitAliasDetected request || threadAliasDetected (request.source.threads ++ request.target.threads)
  let allowed :=
    !aliasDetected &&
    potentialCompatibleWithBoundary request.source request.boundary &&
    potentialCompatibleWithBoundary request.target request.boundary
  let merged := if allowed then mergePotentials request else request.source
  let signature := { (potentialSignatureOf merged request.boundary request.criticality) with
    aliasDetected := aliasDetected,
    scaffoldingRole := scaffoldingRoleOf request }
  let requiresAttention :=
    match request.errorField? with
    | some field => requiresImmediateAction field || aliasDetected
    | none => aliasDetected
  { accepted := allowed
  , mergedPotential := merged
  , signature := signature
  , aliasDetected := aliasDetected
  , scaffoldingRole := scaffoldingRoleOf request
  , requiresAttention := requiresAttention }

end Semantics.ManifoldPotential
