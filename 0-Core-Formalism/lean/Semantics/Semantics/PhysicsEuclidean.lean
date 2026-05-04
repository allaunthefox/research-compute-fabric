import Semantics.PhysicsScalar

namespace Semantics.PhysicsEuclidean

open Semantics.PhysicsScalar

abbrev Q16_16 := PhysicsScalar.Q16_16

structure PhysicsEuclidean (n : Nat) where
  coords : Fin n → Q16_16

namespace PhysicsEuclidean

def zero (n : Nat) : PhysicsEuclidean n :=
  { coords := fun _ => Q16_16.zero }

instance {n : Nat} : Inhabited (PhysicsEuclidean n) where
  default := zero n

def component (vector : PhysicsEuclidean n) (index : Fin n) : Q16_16 :=
  vector.coords index

def map (vector : PhysicsEuclidean n) (f : Q16_16 → Q16_16) : PhysicsEuclidean n :=
  { coords := fun index => f (vector.coords index) }


def zipWith
  (left right : PhysicsEuclidean n)
  (f : Q16_16 → Q16_16 → Q16_16) : PhysicsEuclidean n :=
  { coords := fun index => f (left.coords index) (right.coords index) }


def add (left right : PhysicsEuclidean n) : PhysicsEuclidean n :=
  zipWith left right Q16_16.add


def sub (left right : PhysicsEuclidean n) : PhysicsEuclidean n :=
  zipWith left right Q16_16.sub


def componentwiseMin (left right : PhysicsEuclidean n) : PhysicsEuclidean n :=
  zipWith left right Q16_16.min


def componentwiseMax (left right : PhysicsEuclidean n) : PhysicsEuclidean n :=
  zipWith left right Q16_16.max


def scale (scalar : Q16_16) (vector : PhysicsEuclidean n) : PhysicsEuclidean n :=
  map vector (fun value => Q16_16.mul scalar value)


def hadamard (left right : PhysicsEuclidean n) : PhysicsEuclidean n :=
  zipWith left right Q16_16.mul


def dotAccumulate (index : Nat) (left right : PhysicsEuclidean n) (acc : Q16_16) : Q16_16 :=
  match _h : index with
  | 0 => acc
  | Nat.succ prev =>
      if hlt : prev < n then
        let finIndex : Fin n := ⟨prev, hlt⟩
        let product := Q16_16.mul (left.coords finIndex) (right.coords finIndex)
        dotAccumulate prev left right (Q16_16.add acc product)
      else
        acc


def dot (left right : PhysicsEuclidean n) : Q16_16 :=
  dotAccumulate n left right Q16_16.zero


def l1Accumulate (index : Nat) (vector : PhysicsEuclidean n) (acc : Q16_16) : Q16_16 :=
  match _h : index with
  | 0 => acc
  | Nat.succ prev =>
      if hlt : prev < n then
        let finIndex : Fin n := ⟨prev, hlt⟩
        l1Accumulate prev vector (Q16_16.add acc (vector.coords finIndex))
      else
        acc


def l1Norm (vector : PhysicsEuclidean n) : Q16_16 :=
  l1Accumulate n vector Q16_16.zero


def approxNorm (vector : PhysicsEuclidean n) : Q16_16 :=
  l1Norm vector


def distanceApprox (left right : PhysicsEuclidean n) : Q16_16 :=
  approxNorm (sub (componentwiseMax left right) (componentwiseMin left right))


def clampComponents
  (vector lower upper : PhysicsEuclidean n) : PhysicsEuclidean n :=
  { coords := fun index => Q16_16.clamp (vector.coords index) (lower.coords index) (upper.coords index) }


def withComponent
  (vector : PhysicsEuclidean n)
  (index : Fin n)
  (value : Q16_16) : PhysicsEuclidean n :=
  { coords := fun probe => if probe = index then value else vector.coords probe }


def sumComponents (vector : PhysicsEuclidean n) : Q16_16 :=
  l1Norm vector

end PhysicsEuclidean

abbrev PhysicsVec2 := PhysicsEuclidean 2
abbrev PhysicsVec3 := PhysicsEuclidean 3
abbrev PhysicsVec4 := PhysicsEuclidean 4

end Semantics.PhysicsEuclidean
