import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum
import Semantics.ExoticSpacetime
import Semantics.SpikingDynamics
import Semantics.MagnetoPlasma
import Semantics.Errors

namespace Semantics.BoundaryDynamics

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum
open Semantics.ExoticSpacetime
open Semantics.SpikingDynamics
open Semantics.MagnetoPlasma
open Semantics.Errors

abbrev BoundaryId := UInt16
abbrev SeparatrixId := UInt16
abbrev IntersectionId := UInt16

inductive BoundaryKind
| interface
| sheath
| throat
| spectralCurtain
| reconnectionSurface
| dimensionalSeam
  deriving Repr, DecidableEq

inductive BoundaryRegime
| open
| reflective
| absorptive
| transmissive
| gated
| reconnectionDominant
| collapsed
  deriving Repr, DecidableEq

inductive ReconnectionMode
| none
| latent
| partial
| active
| cascading
  deriving Repr, DecidableEq

inductive BoundaryStability
| stable
| metastable
| unstable
| collapseProne
  deriving Repr, DecidableEq

inductive BoundaryFluidity
| rigid
| viscous
| adaptive
| diffuse
| turbulent
  deriving Repr, DecidableEq

inductive IntersectionFlow
| passThrough
| reflect
| absorb
| split
| entrain
| reconnect
| pinch
  deriving Repr, DecidableEq

structure BoundaryLayer where
  boundaryId : BoundaryId
  label : String
  kind : BoundaryKind
  sourceRegionId : RegionId
  targetRegionId : RegionId
  thickness : Q16_16
  tension : Q16_16
  permeability : Q16_16
  coherence : Q16_16
  fluidity : Q16_16
  spectralCondition? : Option GateSpectralCondition
  deriving Repr, DecidableEq

structure Separatrix where
  separatrixId : SeparatrixId
  label : String
  boundaryId : BoundaryId
  sourceRegime : RegimeClass
  targetRegime : RegimeClass
  gradient : Q16_16
  narrowness : Q16_16
  active : Bool
  deriving Repr, DecidableEq

structure BoundarySignature where
  thickness : Q16_16
  tension : Q16_16
  permeability : Q16_16
  coherence : Q16_16
  fluidity : Q16_16
  spectralAffinity : Q16_16
  temporalGradient : Q16_16
  reconnectionPotential : Q16_16
  spikeAffinity : Q16_16
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  deriving Repr, DecidableEq

structure BoundaryIntersection where
  intersectionId : IntersectionId
  leftBoundaryId : BoundaryId
  rightBoundaryId : BoundaryId
  flow : IntersectionFlow
  reconnectionMode : ReconnectionMode
  stability : BoundaryStability
  fluidityClass : BoundaryFluidity
  scaffoldingRole : ErrorScaffoldingRole
  deriving Repr, DecidableEq

structure BoundaryTransitionRequest where
  boundary : BoundaryLayer
  sourceAssignment : RegionAssignment
  targetAssignment : RegionAssignment
  sample? : Option ElectromagneticSample
  sourceTemporalRegime : TemporalRegime
  targetTemporalRegime : TemporalRegime
  spikeEvent? : Option SpikeEvent
  magnetoSignature? : Option MagnetoPlasmaSignature
  errorField? : Option ErrorField
  deriving Repr, DecidableEq

structure BoundaryTransitionResult where
  admitted : Bool
  regime : BoundaryRegime
  flow : IntersectionFlow
  reconnectionMode : ReconnectionMode
  resultingRegionId : RegionId
  stability : BoundaryStability
  fluidityClass : BoundaryFluidity
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  requiresAttention : Bool
  deriving Repr, DecidableEq


def spectralAffinityOf
  (boundary : BoundaryLayer)
  (sample? : Option ElectromagneticSample) : Q16_16 :=
  match boundary.spectralCondition?, sample? with
  | some cond, some sample =>
      if gateAllowsSample cond sample then
        Q16_16.mean3 sample.intensity sample.coherence sample.modulation
      else
        Q16_16.zero
  | none, some sample => Q16_16.mean3 sample.intensity sample.coherence sample.modulation
  | _, none => Q16_16.zero


def spikeAffinityOf (event? : Option SpikeEvent) : Q16_16 :=
  match event? with
  | none => Q16_16.zero
  | some event => event.intensity


def reconnectionPotentialOf
  (boundary : BoundaryLayer)
  (magnetoSignature? : Option MagnetoPlasmaSignature) : Q16_16 :=
  match magnetoSignature? with
  | none => Q16_16.zero
  | some signature => Q16_16.mean3 boundary.tension signature.reconnectionPotential signature.loopCoherence


def explicitAliasDetected (request : BoundaryTransitionRequest) : Bool :=
  request.sourceAssignment.regionId = request.targetAssignment.regionId ||
  request.boundary.sourceRegionId = request.boundary.targetRegionId ||
  request.sourceAssignment.regionId = request.boundary.targetRegionId ||
  request.targetAssignment.regionId = request.boundary.sourceRegionId


def scaffoldingRoleOf (errorField? : Option ErrorField) : ErrorScaffoldingRole :=
  match errorField? with
  | none => ErrorScaffoldingRole.none
  | some field => (classifyErrorField field).scaffoldingRole


def boundarySignatureOf
  (request : BoundaryTransitionRequest) : BoundarySignature :=
  let temporalGradient :=
    if request.sourceTemporalRegime = request.targetTemporalRegime then Q16_16.zero else Q16_16.half
  { thickness := request.boundary.thickness
  , tension := request.boundary.tension
  , permeability := request.boundary.permeability
  , coherence := request.boundary.coherence
  , fluidity := request.boundary.fluidity
  , spectralAffinity := spectralAffinityOf request.boundary request.sample?
  , temporalGradient := temporalGradient
  , reconnectionPotential := reconnectionPotentialOf request.boundary request.magnetoSignature?
  , spikeAffinity := spikeAffinityOf request.spikeEvent?
  , aliasDetected := explicitAliasDetected request
  , scaffoldingRole := scaffoldingRoleOf request.errorField? }


def classifyReconnectionMode (signature : BoundarySignature) : ReconnectionMode :=
  if Q16_16.ge signature.reconnectionPotential Q16_16.one then .cascading
  else if Q16_16.ge signature.reconnectionPotential (Q16_16.add Q16_16.half Q16_16.quarter) then .active
  else if Q16_16.ge signature.reconnectionPotential Q16_16.half then .partial
  else if Q16_16.nonZero signature.reconnectionPotential then .latent
  else .none


def classifyBoundaryStability (signature : BoundarySignature) : BoundaryStability :=
  if signature.aliasDetected then .collapseProne
  else if Q16_16.ge signature.tension Q16_16.one && Q16_16.ge signature.temporalGradient Q16_16.half then .collapseProne
  else if Q16_16.ge signature.fluidity Q16_16.two then .unstable
  else if Q16_16.ge signature.coherence Q16_16.half then .stable
  else .metastable


def classifyBoundaryFluidity (signature : BoundarySignature) : BoundaryFluidity :=
  if Q16_16.ge signature.fluidity (Q16_16.add Q16_16.half Q16_16.quarter) &&
     Q16_16.ge signature.reconnectionPotential Q16_16.half then .turbulent
  else if Q16_16.ge signature.fluidity (Q16_16.add Q16_16.half Q16_16.quarter) then .diffuse
  else if Q16_16.ge signature.fluidity Q16_16.half then .adaptive
  else if Q16_16.nonZero signature.fluidity then .viscous
  else .rigid


def effectivePermeability (signature : BoundarySignature) : Q16_16 :=
  let baseBonus := Q16_16.avg signature.fluidity signature.spikeAffinity
  let scaffoldBonus :=
    match signature.scaffoldingRole with
    | .boundaryScaffold => Q16_16.half
    | .dimensionalScaffold => Q16_16.quarter
    | .causalScaffold => Q16_16.quarter
    | .criticalScaffold => Q16_16.quarter
    | .none => Q16_16.zero
  Q16_16.clamp (Q16_16.addSaturating signature.permeability (Q16_16.add baseBonus scaffoldBonus)) Q16_16.zero Q16_16.four


def classifyBoundaryRegime (signature : BoundarySignature) : BoundaryRegime :=
  if signature.aliasDetected then .collapsed
  else match classifyReconnectionMode signature with
  | .active | .cascading => .reconnectionDominant
  | .partial | .latent => .gated
  | .none =>
      if Q16_16.ge (effectivePermeability signature) (Q16_16.add Q16_16.half Q16_16.quarter) then .transmissive
      else if Q16_16.isZero (effectivePermeability signature) then .reflective
      else if Q16_16.ge signature.spectralAffinity Q16_16.half then .absorptive
      else .open


def classifyIntersectionFlow (signature : BoundarySignature) : IntersectionFlow :=
  if signature.aliasDetected then .pinch
  else match classifyReconnectionMode signature with
  | .active | .cascading => .reconnect
  | .partial => .split
  | .latent => .entrain
  | .none =>
      let permeability := effectivePermeability signature
      if Q16_16.ge permeability Q16_16.one then .passThrough
      else if Q16_16.isZero permeability then .reflect
      else if Q16_16.ge signature.spectralAffinity Q16_16.half then .absorb
      else .split


def boundaryAdmits (request : BoundaryTransitionRequest) : Bool :=
  request.sourceAssignment.regionId = request.boundary.sourceRegionId &&
  request.targetAssignment.regionId = request.boundary.targetRegionId &&
  !explicitAliasDetected request


def resolveBoundaryTransition (request : BoundaryTransitionRequest) : BoundaryTransitionResult :=
  let signature := boundarySignatureOf request
  let aliasDetected := signature.aliasDetected
  let regime := classifyBoundaryRegime signature
  let stability := classifyBoundaryStability signature
  let fluidityClass := classifyBoundaryFluidity signature
  let flow := classifyIntersectionFlow signature
  let admitted := boundaryAdmits request && regime != BoundaryRegime.collapsed
  let scaffoldingRole := signature.scaffoldingRole
  let requiresAttention :=
    match request.errorField? with
    | some field => requiresImmediateAction field || aliasDetected
    | none => aliasDetected
  { admitted := admitted
  , regime := regime
  , flow := flow
  , reconnectionMode := classifyReconnectionMode signature
  , resultingRegionId := if admitted then request.targetAssignment.regionId else request.sourceAssignment.regionId
  , stability := stability
  , fluidityClass := fluidityClass
  , aliasDetected := aliasDetected
  , scaffoldingRole := scaffoldingRole
  , requiresAttention := requiresAttention }

end Semantics.BoundaryDynamics
