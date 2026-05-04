import Semantics.PhysicsEuclidean

namespace Semantics.PhysicsLagrangian

open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean

abbrev Q16_16 := PhysicsScalar.Q16_16

structure PhysicsLagrangian (n : Nat) where
  position : PhysicsEuclidean.PhysicsEuclidean n
  velocity : PhysicsEuclidean.PhysicsEuclidean n
  momentum : PhysicsEuclidean.PhysicsEuclidean n
  massScale : Q16_16
  actionDensity : Q16_16

namespace PhysicsLagrangian

def zero (n : Nat) : PhysicsLagrangian n :=
  { position := PhysicsEuclidean.zero n
  , velocity := PhysicsEuclidean.zero n
  , momentum := PhysicsEuclidean.zero n
  , massScale := Q16_16.one
  , actionDensity := Q16_16.zero }

instance {n : Nat} : Inhabited (PhysicsLagrangian n) where
  default := zero n


def kineticProxy (state : PhysicsLagrangian n) : Q16_16 :=
  let momentumEnergy := PhysicsEuclidean.dot state.velocity state.momentum
  Q16_16.mul Q16_16.half momentumEnergy


def transportWeight (state : PhysicsLagrangian n) : Q16_16 :=
  Q16_16.add state.massScale state.actionDensity


def advanceLinear (delta : Q16_16) (state : PhysicsLagrangian n) : PhysicsLagrangian n :=
  let displacement := PhysicsEuclidean.scale delta state.velocity
  { state with position := PhysicsEuclidean.add state.position displacement }


def updateMomentum
  (coupling : Q16_16)
  (state : PhysicsLagrangian n) : PhysicsLagrangian n :=
  let shiftedMomentum := PhysicsEuclidean.scale coupling state.velocity
  { state with momentum := PhysicsEuclidean.add state.momentum shiftedMomentum }


def applyImpulse
  (impulse : PhysicsEuclidean.PhysicsEuclidean n)
  (state : PhysicsLagrangian n) : PhysicsLagrangian n :=
  { state with momentum := PhysicsEuclidean.add state.momentum impulse }


def dampVelocity
  (retention : Q16_16)
  (state : PhysicsLagrangian n) : PhysicsLagrangian n :=
  { state with velocity := PhysicsEuclidean.scale retention state.velocity }


def withActionDensity (actionDensity : Q16_16) (state : PhysicsLagrangian n) : PhysicsLagrangian n :=
  { state with actionDensity := actionDensity }


def effectiveEnergy (state : PhysicsLagrangian n) : Q16_16 :=
  Q16_16.add (kineticProxy state) state.actionDensity

end PhysicsLagrangian

abbrev BodyState2D := PhysicsLagrangian 2
abbrev BodyState3D := PhysicsLagrangian 3
abbrev BodyState4D := PhysicsLagrangian 4

end Semantics.PhysicsLagrangian
