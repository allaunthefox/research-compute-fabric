import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.CriticalityDynamics
import Semantics.MultiBodyField
import Semantics.CosmicStructure
import Semantics.Errors
import Semantics.ManifoldStructures
import Semantics.ExoticSpacetime
import Semantics.DomainState

namespace Semantics.ManifoldPotential

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.CriticalityDynamics
open Semantics.MultiBodyField
open Semantics.CosmicStructure
open Semantics.Errors
open Semantics.ManifoldStructures
open Semantics.ExoticSpacetime
open Semantics.DomainState

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
| pStable
| pMetastable
| pUnstable
| pCollapseProne
  deriving Repr, DecidableEq

structure PotentialCoordinate where
  radial : PhysicsScalar.Q16_16
  angular : PhysicsScalar.Q16_16
  depth : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure PotentialGradient where
  inward : PhysicsScalar.Q16_16
  tangential : PhysicsScalar.Q16_16
  vertical : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure PotentialBasin where
  centerRegion : RegionId
  radius : PhysicsScalar.Q16_16
  depth : PhysicsScalar.Q16_16
  rimStrength : PhysicsScalar.Q16_16
  nestedDepth : PhysicsScalar.Q16_16
  morphology : PotentialMorphology
  deriving Repr, DecidableEq

structure PotentialThread where
  sourceRegion : RegionId
  targetRegion : RegionId
  pull : PhysicsScalar.Q16_16
  torsion : PhysicsScalar.Q16_16
  permeability : PhysicsScalar.Q16_16
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

structure PotentialSignature where
  basinDepth : PhysicsScalar.Q16_16
  rimStrength : PhysicsScalar.Q16_16
  threadCount : UInt16
  totalPull : PhysicsScalar.Q16_16
  boundaryFluidity : PhysicsScalar.Q16_16
  criticalScore : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole

structure PotentialTransitionRequest where
  source : ManifoldPotential
  target : ManifoldPotential
  boundary : BoundaryLayer
  criticality : CriticalNetwork
  sample? : Option ElectromagneticSample
  sourceTemporalRegime : TemporalRegime
  targetTemporalRegime : TemporalRegime
  errorField? : Option ErrorField

structure PotentialTransitionResult where
  accepted : Bool
  mergedPotential : ManifoldPotential
  signature : PotentialSignature
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  requiresAttention : Bool


def addPulls (threads : List PotentialThread) : PhysicsScalar.Q16_16 :=
  threads.foldl (fun acc thread => PhysicsScalar.Q16_16.addSaturating acc thread.pull) PhysicsScalar.Q16_16.zero


def explicitAliasDetected (s : ManifoldPotential) (t : ManifoldPotential) (b : BoundaryLayer) : Bool :=
  s.anchorRegion = t.anchorRegion ||
  s.basin.centerRegion = t.basin.centerRegion ||
  b.sourceRegionId = b.targetRegionId


def threadAliasDetected (threads : List PotentialThread) : Bool :=
  threads.any (fun thread => thread.sourceRegion = thread.targetRegion)


def scaffoldingRoleOf (errorField? : Option ErrorField) : ErrorScaffoldingRole :=
  match errorField? with
  | none => ErrorScaffoldingRole.none
  | some field => (classifyErrorField field).scaffoldingRole


def classifyPotentialMorphology (gradient : PotentialGradient) (basin : PotentialBasin) : PotentialMorphology :=
  if PhysicsScalar.Q16_16.gt basin.nestedDepth PhysicsScalar.Q16_16.zero then .nestedBasin
  else if PhysicsScalar.Q16_16.gt basin.rimStrength basin.depth then .ridge
  else if PhysicsScalar.Q16_16.gt gradient.tangential gradient.inward then .spiral
  else if PhysicsScalar.Q16_16.gt gradient.vertical gradient.inward then .throat
  else if PhysicsScalar.Q16_16.gt basin.depth PhysicsScalar.Q16_16.half then .basin
  else .flat


def boundaryModeOf (boundary : BoundaryLayer) (role : ErrorScaffoldingRole) : PotentialBoundaryMode :=
  let fluidityClass := classifyBoundaryFluidity (boundarySignatureOf {
    boundary := boundary,
    sourceAssignment := { regionId := boundary.sourceRegionId, state := { resolutionStatus := .resolved, stabilityClass := .stable, discreteState := default }, regimeClass := .transitional },
    targetAssignment := { regionId := boundary.targetRegionId, state := { resolutionStatus := .resolved, stabilityClass := .stable, discreteState := default }, regimeClass := .transitional },
    sourceTemporalRegime := .monotonic,
    targetTemporalRegime := .monotonic,
    spikeEvent := none,
    magnetoSignature := none,
    errorField := none })
  match role, fluidityClass with
  | .boundaryScaffold, _ => .fluid
  | .causalScaffold, _ => .gated
  | .criticalScaffold, _ => .reconnective
  | _, .fRigid => .reflective
  | _, .fViscous => .gated
  | _, .fAdaptive => .fluid
  | _, .fDiffuse => .open
  | _, .fTurbulent => .reconnective


def threadCountOf (threads : List PotentialThread) : UInt16 := UInt16.ofNat threads.length


def potentialSignatureOf (potential : ManifoldPotential) (boundary : BoundaryLayer) (criticality : CriticalNetwork) : PotentialSignature :=
  { basinDepth := potential.basin.depth
  , rimStrength := potential.basin.rimStrength
  , threadCount := threadCountOf potential.threads
  , totalPull := addPulls potential.threads
  , boundaryFluidity := boundary.fluidity
  , criticalScore := PhysicsScalar.Q16_16.one 
  , coherence := potential.gradient.coherence
  , aliasDetected := threadAliasDetected potential.threads
  , scaffoldingRole := potential.scaffoldingRole }


def classifyPotentialRegime (signature : PotentialSignature) : PotentialRegime :=
  if signature.aliasDetected then .collapsed
  else if PhysicsScalar.Q16_16.gt signature.criticalScore PhysicsScalar.Q16_16.three then .cascading
  else if PhysicsScalar.Q16_16.gt signature.basinDepth PhysicsScalar.Q16_16.two then .trapping
  else if PhysicsScalar.Q16_16.gt signature.totalPull PhysicsScalar.Q16_16.one then .guiding
  else if PhysicsScalar.Q16_16.gt signature.rimStrength PhysicsScalar.Q16_16.two then .critical
  else .quiescent


def classifyPotentialStability (signature : PotentialSignature) : PotentialStability :=
  if signature.aliasDetected then .pCollapseProne
  else if PhysicsScalar.Q16_16.gt signature.criticalScore PhysicsScalar.Q16_16.three then .pCollapseProne
  else if PhysicsScalar.Q16_16.gt signature.boundaryFluidity PhysicsScalar.Q16_16.two then .pUnstable
  else if PhysicsScalar.Q16_16.gt signature.totalPull PhysicsScalar.Q16_16.two then .pMetastable
  else .pStable


def potentialCompatibleWithBoundary (potential : ManifoldPotential) (boundary : BoundaryLayer) : Bool :=
  match potential.boundaryMode with
  | .reflective => boundary.targetRegionId != potential.anchorRegion
  | _ => true


def mergeBasins (left right : PotentialBasin) : PotentialBasin :=
  { centerRegion := left.centerRegion
  , radius := PhysicsScalar.Q16_16.max left.radius right.radius
  , depth := PhysicsScalar.Q16_16.avg left.depth right.depth
  , rimStrength := PhysicsScalar.Q16_16.avg left.rimStrength right.rimStrength
  , nestedDepth := PhysicsScalar.Q16_16.max left.nestedDepth right.nestedDepth
  , morphology := left.morphology }


def mergeGradients (left right : PotentialGradient) : PotentialGradient :=
  { inward := PhysicsScalar.Q16_16.avg left.inward right.inward
  , tangential := PhysicsScalar.Q16_16.avg left.tangential right.tangential
  , vertical := PhysicsScalar.Q16_16.avg left.vertical right.vertical
  , coherence := PhysicsScalar.Q16_16.avg left.coherence right.coherence }


def mergePotentials (request : PotentialTransitionRequest) : ManifoldPotential :=
  let mergedGradient := mergeGradients request.source.gradient request.target.gradient
  let mergedBasin := mergeBasins request.source.basin request.target.basin
  let mergedThreads := request.source.threads ++ request.target.threads
  let role := scaffoldingRoleOf request.errorField?
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
  let aliasDetected := explicitAliasDetected request.source request.target request.boundary || threadAliasDetected (request.source.threads ++ request.target.threads)
  let allowed :=
    !aliasDetected &&
    potentialCompatibleWithBoundary request.source request.boundary &&
    potentialCompatibleWithBoundary request.target request.boundary
  let merged := if allowed then mergePotentials request else request.source
  let signature := { (potentialSignatureOf merged request.boundary request.criticality) with
    aliasDetected := aliasDetected,
    scaffoldingRole := scaffoldingRoleOf request.errorField? }
  let requiresAttention :=
    match request.errorField? with
    | some field => requiresImmediateAction field || aliasDetected
    | none => aliasDetected
  { accepted := allowed
  , mergedPotential := merged
  , signature := signature
  , aliasDetected := aliasDetected
  , scaffoldingRole := scaffoldingRoleOf request.errorField?
  , requiresAttention := requiresAttention }

end Semantics.ManifoldPotential
