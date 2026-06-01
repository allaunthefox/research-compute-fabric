import Semantics.PhysicsScalarBridge
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
  | none => PhysicsScalarBridge.zero
  | some signature =>
      PhysicsScalarBridge.mean3 boundary.tension signature.reconnectionPotential signature.loopCoherence


def explicitAliasDetected (request : BoundaryTransitionRequest) : Bool :=
  let sId := request.sourceAssignment.regionId
  let tId := request.targetAssignment.regionId
  let bSId := request.boundary.sourceRegionId
  let bTId := request.boundary.targetRegionId
  sId = tId || bSId = bTId || sId = bTId || tId = bSId


def boundarySignatureOf
  (request : BoundaryTransitionRequest) : BoundarySignature :=
  let b := request.boundary
  let temporalGradient := if request.sourceTemporalRegime = request.targetTemporalRegime then PhysicsScalarBridge.zero else PhysicsScalarBridge.half
  let sa := match request.spikeEvent with | some e => e.intensity | none => PhysicsScalarBridge.zero
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
  if PhysicsScalarBridge.ge signature.reconnectionPotential PhysicsScalarBridge.one then .mCascading
  else if PhysicsScalarBridge.ge signature.reconnectionPotential (PhysicsScalarBridge.add PhysicsScalarBridge.half PhysicsScalarBridge.quarter) then .mActive
  else if PhysicsScalarBridge.ge signature.reconnectionPotential PhysicsScalarBridge.half then .mPartial
  else if PhysicsScalarBridge.nonZero signature.reconnectionPotential then .mLatent
  else .mNone


def classifyBoundaryStability (signature : BoundarySignature) : BoundaryStabilityClass :=
  if signature.aliasDetected then .sCollapseProne
  else if PhysicsScalarBridge.ge signature.tension PhysicsScalarBridge.one && PhysicsScalarBridge.ge signature.temporalGradient PhysicsScalarBridge.half then .sCollapseProne
  else if PhysicsScalarBridge.ge signature.fluidity (PhysicsScalarBridge.fromNat 2) then .sUnstable
  else if PhysicsScalarBridge.ge signature.coherence PhysicsScalarBridge.half then .sStable
  else .sMetastable


def classifyBoundaryFluidity (signature : BoundarySignature) : BoundaryFluidityClass :=
  if PhysicsScalarBridge.ge signature.fluidity (PhysicsScalarBridge.add PhysicsScalarBridge.half PhysicsScalarBridge.quarter) &&
     PhysicsScalarBridge.ge signature.reconnectionPotential PhysicsScalarBridge.half then .fTurbulent
  else if PhysicsScalarBridge.ge signature.fluidity (PhysicsScalarBridge.add PhysicsScalarBridge.half PhysicsScalarBridge.quarter) then .fDiffuse
  else if PhysicsScalarBridge.ge signature.fluidity PhysicsScalarBridge.half then .fAdaptive
  else if PhysicsScalarBridge.nonZero signature.fluidity then .fViscous
  else .fRigid


def effectivePermeability (signature : BoundarySignature) : PhysicsScalar.Q16_16 :=
  let baseBonus := PhysicsScalarBridge.avg signature.fluidity signature.spikeAffinity
  let scaffoldBonus :=
    match signature.scaffoldingRole with
    | .boundaryScaffold => PhysicsScalarBridge.half
    | .dimensionalScaffold => PhysicsScalarBridge.quarter
    | .causalScaffold => PhysicsScalarBridge.quarter
    | .criticalScaffold => PhysicsScalarBridge.quarter
    | .none => PhysicsScalarBridge.zero
  PhysicsScalarBridge.clamp (PhysicsScalarBridge.add signature.permeability (PhysicsScalarBridge.add baseBonus scaffoldBonus)) PhysicsScalarBridge.zero PhysicsScalarBridge.four


def classifyBoundaryRegime (signature : BoundarySignature) : BoundaryRegime :=
  if signature.aliasDetected then .rgCollapsed
  else match classifyReconnectionMode signature with
  | .mActive | .mCascading => .rgReconnectionDominant
  | .mPartial | .mLatent => .rgGated
  | .mNone =>
      let ep := effectivePermeability signature
      if PhysicsScalarBridge.ge ep (PhysicsScalarBridge.add PhysicsScalarBridge.half PhysicsScalarBridge.quarter) then .rgTransmissive
      else if PhysicsScalarBridge.isZero ep then .rgReflective
      else .rgOpen


def classifyIntersectionFlow (signature : BoundarySignature) : IntersectionFlowKind :=
  if signature.aliasDetected then .fkPinch
  else match classifyReconnectionMode signature with
  | .mActive | .mCascading => .fkReconnect
  | .mPartial => .fkSplit
  | .mLatent => .fkEntrain
  | .mNone =>
      let permeability := effectivePermeability signature
      if PhysicsScalarBridge.ge permeability PhysicsScalarBridge.one then .fkPassThrough
      else if PhysicsScalarBridge.isZero permeability then .fkReflect
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
