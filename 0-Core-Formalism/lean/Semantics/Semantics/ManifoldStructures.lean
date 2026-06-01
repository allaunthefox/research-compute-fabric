import Semantics.PhysicsScalarBridge
import Semantics.FixedPoint
import Semantics.RegimeCore
import Semantics.ExoticSpacetime
import Semantics.SpikingDynamics
import Semantics.MagnetoPlasma
import Semantics.Errors

namespace Semantics.ManifoldStructures

open Semantics.FixedPoint
open Semantics.RegimeCore
open Semantics.ExoticSpacetime
open Semantics.SpikingDynamics
open Semantics.MagnetoPlasma
open Semantics.Errors

abbrev BoundaryId := UInt16

inductive BoundaryRegime
| rgOpen
| rgReflective
| rgAbsorptive
| rgTransmissive
| rgGated
| rgReconnectionDominant
| rgCollapsed
  deriving DecidableEq

inductive ManifoldReconnectionMode
| mNone
| mLatent
| mPartial
| mActive
| mCascading
  deriving DecidableEq

inductive BoundaryStabilityClass
| sStable
| sMetastable
| sUnstable
| sCollapseProne
  deriving DecidableEq

inductive BoundaryFluidityClass
| fRigid
| fViscous
| fAdaptive
| fDiffuse
| fTurbulent
  deriving DecidableEq

inductive IntersectionFlowKind
| fkPassThrough
| fkReflect
| fkAbsorb
| fkSplit
| fkEntrain
| fkReconnect
| fkPinch
  deriving DecidableEq

structure BoundaryLayer where
  boundaryId : BoundaryId
  sourceRegionId : RegionId
  targetRegionId : RegionId
  tension : PhysicsScalar.Q16_16
  permeability : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  fluidity : PhysicsScalar.Q16_16
  deriving DecidableEq

structure BoundarySignature where
  tension : PhysicsScalar.Q16_16
  permeability : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  fluidity : PhysicsScalar.Q16_16
  temporalGradient : PhysicsScalar.Q16_16
  reconnectionPotential : PhysicsScalar.Q16_16
  spikeAffinity : PhysicsScalar.Q16_16
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  deriving DecidableEq

structure BoundaryTransitionRequest where
  boundary : BoundaryLayer
  sourceAssignment : RegionAssignment
  targetAssignment : RegionAssignment
  sourceTemporalRegime : TemporalRegime
  targetTemporalRegime : TemporalRegime
  spikeEvent : Option SpikeEvent
  magnetoSignature : Option MagnetoPlasmaSignature
  errorField : Option ErrorField

structure BoundaryTransitionResult where
  admitted : Bool
  regime : BoundaryRegime
  flow : IntersectionFlowKind
  reconnection : ManifoldReconnectionMode
  resultingRegionId : RegionId
  stability : BoundaryStabilityClass
  fluidityClass : BoundaryFluidityClass
  aliasDetected : Bool
  scaffoldingRole : ErrorScaffoldingRole
  requiresAttention : Bool

end Semantics.ManifoldStructures
