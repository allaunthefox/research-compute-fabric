import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.MagnetoPlasma
import Semantics.ExoticSpacetime
import Semantics.SpikingDynamics
import Semantics.ElectromagneticSpectrum

namespace Semantics.MultiBodyField

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.MagnetoPlasma
open Semantics.ExoticSpacetime
open Semantics.SpikingDynamics
open Semantics.ElectromagneticSpectrum

abbrev FieldIntensity := PhysicsScalar.Q16_16
abbrev BodyId := UInt16

inductive FieldInteractionClass
| elastic
| plasma
| spectral
| temporal
| causal
  deriving DecidableEq

structure FieldBody where
  bodyId : BodyId
  label : String
  regionId : RegionId
  mass : PhysicsScalar.Q16_16
  charge : PhysicsScalar.Q16_16
  potential : PhysicsScalar.Q16_16
  velocity : PhysicsScalar.Q16_16
  magnetoSignature? : Option MagnetoPlasmaSignature
  spikeEvent? : Option SpikeEvent

inductive FieldSymmetry
| isotropic
| axial
| planar
| chiral
| chaotic
  deriving DecidableEq

structure MultiBodyAssembly (n : Nat) where
  bodies : Array FieldBody
  boundaries : Array BoundaryLayer
  interactionClass : FieldInteractionClass
  symmetry : FieldSymmetry
  globalPotential : PhysicsScalar.Q16_16

structure InteractionResult where
  netForce : PhysicsScalar.Q16_16
  potentialShift : PhysicsScalar.Q16_16
  reconnectionDetected : Bool
  aliasingDetected : Bool
  deriving Repr, DecidableEq

structure MultiBodySignature where
  bodyCount : UInt16
  criticalPressure : PhysicsScalar.Q16_16
  spectralCoherence : PhysicsScalar.Q16_16
  magnetoAlignment : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq


def interactionEffectiveMass (body : FieldBody) : PhysicsScalar.Q16_16 :=
  match body.magnetoSignature? with
  | none => body.mass
  | some signature =>
      PhysicsScalar.Q16_16.addSaturating body.mass (PhysicsScalar.Q16_16.mulQ16_16 signature.reconnectionPotential signature.loopCoherence)


def interactionEffectiveCharge (body : FieldBody) : PhysicsScalar.Q16_16 :=
  match body.spikeEvent? with
  | none => body.charge
  | some event =>
      PhysicsScalar.Q16_16.addSaturating body.charge event.intensity


def bodyDistance (b1 b2 : FieldBody) : PhysicsScalar.Q16_16 :=
  PhysicsScalar.Q16_16.absDiff b1.potential b2.potential


def interactionMagnitude (b1 b2 : FieldBody) (interactionClass : FieldInteractionClass) : PhysicsScalar.Q16_16 :=
  let m1 := interactionEffectiveMass b1
  let m2 := interactionEffectiveMass b2
  let q1 := interactionEffectiveCharge b1
  let q2 := interactionEffectiveCharge b2
  let r := bodyDistance b1 b2
  let baseForce :=
    match interactionClass with
    | FieldInteractionClass.elastic => PhysicsScalar.Q16_16.mulQ16_16 m1 m2
    | FieldInteractionClass.plasma => PhysicsScalar.Q16_16.mulQ16_16 q1 q2
    | _ => PhysicsScalar.Q16_16.avg (PhysicsScalar.Q16_16.mulQ16_16 m1 m2) (PhysicsScalar.Q16_16.mulQ16_16 q1 q2)
  
  if PhysicsScalar.Q16_16.lt r PhysicsScalar.Q16_16.quarter then
    PhysicsScalar.Q16_16.mulQ16_16 baseForce PhysicsScalar.Q16_16.four
  else
    baseForce


def bodyInteraction (b1 b2 : FieldBody) (interactionClass : FieldInteractionClass) : InteractionResult :=
  let force := interactionMagnitude b1 b2 interactionClass
  let reconnection :=
    match b1.magnetoSignature?, b2.magnetoSignature? with
    | some s1, some s2 => PhysicsScalar.Q16_16.ge s1.reconnectionPotential PhysicsScalar.Q16_16.half && PhysicsScalar.Q16_16.ge s2.reconnectionPotential PhysicsScalar.Q16_16.half
    | _, _ => false
  let aliasing := b1.regionId = b2.regionId && b1.bodyId != b2.bodyId
  { netForce := force
  , potentialShift := PhysicsScalar.Q16_16.divQ16_16 force PhysicsScalar.Q16_16.two
  , reconnectionDetected := reconnection
  , aliasingDetected := aliasing }


def assemblyStability (assembly : MultiBodyAssembly n) : Bool :=
  match assembly.interactionClass with
  | FieldInteractionClass.causal => PhysicsScalar.Q16_16.le assembly.globalPotential PhysicsScalar.Q16_16.three
  | _ => PhysicsScalar.Q16_16.le assembly.globalPotential PhysicsScalar.Q16_16.four


def interactionCoupling (assembly : MultiBodyAssembly n) : PhysicsScalar.Q16_16 :=
  match assembly.symmetry with
  | FieldSymmetry.chaotic => PhysicsScalar.Q16_16.addSaturating assembly.globalPotential PhysicsScalar.Q16_16.one
  | FieldSymmetry.isotropic => PhysicsScalar.Q16_16.divQ16_16 assembly.globalPotential PhysicsScalar.Q16_16.two
  | _ => assembly.globalPotential


def multiBodySignatureOf
  (assembly : MultiBodyAssembly n)
  (sample? : Option ElectromagneticSample) : MultiBodySignature :=
  let bodyCount := UInt16.ofNat assembly.bodies.size
  let coherence := match sample? with | some s => s.bandProfile.intensity | none => PhysicsScalar.Q16_16.zero
  { bodyCount := bodyCount
  , criticalPressure := assembly.globalPotential
  , spectralCoherence := coherence
  , magnetoAlignment := PhysicsScalar.Q16_16.half }

end Semantics.MultiBodyField
