import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum
import Semantics.ExoticSpacetime
import Semantics.SpikingDynamics
import Semantics.MagnetoPlasma
import Semantics.Errors
import Semantics.ManifoldStructures

namespace Semantics.BoundaryDynamics

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum
open Semantics.ExoticSpacetime
open Semantics.SpikingDynamics
open Semantics.MagnetoPlasma
open Semantics.Errors
open Semantics.ManifoldStructures

def reconnectionPotentialOf
  (boundary : BoundaryLayer)
  (magnetoSignature : Option MagnetoPlasmaSignature) : PhysicsScalar.Q16_16 :=
  match magnetoSignature with
  | none => PhysicsScalar.Q16_16.zero
  | some signature =>
      PhysicsScalar.Q16_16.mean3 boundary.tension signature.reconnectionPotential signature.loopCoherence


def explicitAliasDetected (request : BoundaryTransitionRequest) : Bool :=
  let sId := request.sourceAssignment.regionId
  let tId := request.targetAssignment.regionId
  let bSId := request.boundary.sourceRegionId
  let bTId := request.boundary.targetRegionId
  sId = tId || bSId = bTId || sId = bTId || tId = bSId


def boundarySignatureOf
  (request : BoundaryTransitionRequest) : BoundarySignature :=
  let b := request.boundary
  let temporalGradient := if request.sourceTemporalRegime = request.targetTemporalRegime then PhysicsScalar.Q16_16.zero else PhysicsScalar.Q16_16.half
  let sa := match request.spikeEvent with | some e => e.intensity | none => PhysicsScalar.Q16_16.zero
  let sr := match request.errorField with | some f => (classifyErrorField f).scaffoldingRole | none => ErrorScaffoldingRole.none
  { tension := b.tension
  , permeability := b.permeability
  , coherence := b.coherence
  , fluidity := b.fluidity
  , temporalGradient := temporalGradient
  , reconnectionPotential := reconnectionPotentialOf b request.magnetoSignature
  , spikeAffinity := sa
  , aliasDetected := explicitAliasDetected request
  , scaffoldingRole := sr }


def classifyReconnectionMode (signature : BoundarySignature) : ManifoldReconnectionMode :=
  if PhysicsScalar.Q16_16.ge signature.reconnectionPotential PhysicsScalar.Q16_16.one then .mCascading
  else if PhysicsScalar.Q16_16.ge signature.reconnectionPotential (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then .mActive
  else if PhysicsScalar.Q16_16.ge signature.reconnectionPotential PhysicsScalar.Q16_16.half then .mPartial
  else if PhysicsScalar.Q16_16.nonZero signature.reconnectionPotential then .mLatent
  else .mNone


def classifyBoundaryStability (signature : BoundarySignature) : BoundaryStabilityClass :=
  if signature.aliasDetected then .sCollapseProne
  else if PhysicsScalar.Q16_16.ge signature.tension PhysicsScalar.Q16_16.one && PhysicsScalar.Q16_16.ge signature.temporalGradient PhysicsScalar.Q16_16.half then .sCollapseProne
  else if PhysicsScalar.Q16_16.ge signature.fluidity (PhysicsScalar.Q16_16.fromNat 2) then .sUnstable
  else if PhysicsScalar.Q16_16.ge signature.coherence PhysicsScalar.Q16_16.half then .sStable
  else .sMetastable


def classifyBoundaryFluidity (signature : BoundarySignature) : BoundaryFluidityClass :=
  if PhysicsScalar.Q16_16.ge signature.fluidity (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) &&
     PhysicsScalar.Q16_16.ge signature.reconnectionPotential PhysicsScalar.Q16_16.half then .fTurbulent
  else if PhysicsScalar.Q16_16.ge signature.fluidity (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then .fDiffuse
  else if PhysicsScalar.Q16_16.ge signature.fluidity PhysicsScalar.Q16_16.half then .fAdaptive
  else if PhysicsScalar.Q16_16.nonZero signature.fluidity then .fViscous
  else .fRigid


def effectivePermeability (signature : BoundarySignature) : PhysicsScalar.Q16_16 :=
  let baseBonus := PhysicsScalar.Q16_16.avg signature.fluidity signature.spikeAffinity
  let scaffoldBonus :=
    match signature.scaffoldingRole with
    | .boundaryScaffold => PhysicsScalar.Q16_16.half
    | .dimensionalScaffold => PhysicsScalar.Q16_16.quarter
    | .causalScaffold => PhysicsScalar.Q16_16.quarter
    | .criticalScaffold => PhysicsScalar.Q16_16.quarter
    | .none => PhysicsScalar.Q16_16.zero
  PhysicsScalar.Q16_16.clamp (PhysicsScalar.Q16_16.add signature.permeability (PhysicsScalar.Q16_16.add baseBonus scaffoldBonus)) PhysicsScalar.Q16_16.zero PhysicsScalar.Q16_16.four


def classifyBoundaryRegime (signature : BoundarySignature) : BoundaryRegime :=
  if signature.aliasDetected then .rgCollapsed
  else match classifyReconnectionMode signature with
  | .mActive | .mCascading => .rgReconnectionDominant
  | .mPartial | .mLatent => .rgGated
  | .mNone =>
      let ep := effectivePermeability signature
      if PhysicsScalar.Q16_16.ge ep (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then .rgTransmissive
      else if PhysicsScalar.Q16_16.isZero ep then .rgReflective
      else .rgOpen


def classifyIntersectionFlow (signature : BoundarySignature) : IntersectionFlowKind :=
  if signature.aliasDetected then .fkPinch
  else match classifyReconnectionMode signature with
  | .mActive | .mCascading => .fkReconnect
  | .mPartial => .fkSplit
  | .mLatent => .fkEntrain
  | .mNone =>
      let permeability := effectivePermeability signature
      if PhysicsScalar.Q16_16.ge permeability PhysicsScalar.Q16_16.one then .fkPassThrough
      else if PhysicsScalar.Q16_16.isZero permeability then .fkReflect
      else .fkSplit


def resolveBoundaryTransition (request : BoundaryTransitionRequest) : BoundaryTransitionResult :=
  let signature := boundarySignatureOf request
  let regime := classifyBoundaryRegime signature
  let stability := classifyBoundaryStability signature
  let fluidityClass := classifyBoundaryFluidity signature
  let flow := classifyIntersectionFlow signature
  let admitted := (request.sourceAssignment.regionId = request.boundary.sourceRegionId &&
                  request.targetAssignment.regionId = request.boundary.targetRegionId &&
                  !signature.aliasDetected) && regime != BoundaryRegime.rgCollapsed
  let requiresAttention :=
    match request.errorField with
    | some field => requiresImmediateAction field || signature.aliasDetected
    | none => signature.aliasDetected
  let resultingRegionId := if admitted then request.targetAssignment.regionId else request.sourceAssignment.regionId
  { admitted := admitted
  , regime := regime
  , flow := flow
  , reconnection := classifyReconnectionMode signature
  , resultingRegionId := resultingRegionId
  , stability := stability
  , fluidityClass := fluidityClass
  , aliasDetected := signature.aliasDetected
  , scaffoldingRole := signature.scaffoldingRole
  , requiresAttention := requiresAttention }

end Semantics.BoundaryDynamics
