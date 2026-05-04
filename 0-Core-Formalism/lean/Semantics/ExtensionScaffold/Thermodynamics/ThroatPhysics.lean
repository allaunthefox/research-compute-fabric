/-
  ThroatPhysics.lean - Fixed-Point Throat Physics
-/

import Semantics.DynamicCanal
import Semantics.LocalDerivative
import Semantics.HyperFlow

namespace ExtensionScaffold.Thermodynamics.ThroatPhysics

open Semantics.DynamicCanal
open Semantics.LocalDerivative
open Semantics.HyperFlow

-- Plasma regime types (ported from Semantics.PlasmaTopology)
inductive MediumRegime
| vacuum | gas | plasma | degenerate | condensate
 deriving Repr, DecidableEq

inductive PlasmaManifoldRegime
| euclidean | toroidal | spherical | hyperbolic
 deriving Repr, DecidableEq

inductive PlasmaTopologyRegime
| simple | complex | knotted | braided
 deriving Repr, DecidableEq

inductive PlasmaTopologyInvariantSurvivor
| none | weak | strong | absolute
 deriving Repr, DecidableEq

abbrev Q16_16 := UInt32

namespace Q16_16

def scale : Nat := 65536
def maxNat : Nat := 4294967295

def zero : Q16_16 := UInt32.ofNat 0
def one : Q16_16 := UInt32.ofNat 65536
def half : Q16_16 := UInt32.ofNat 32768
def quarter : Q16_16 := UInt32.ofNat 16384
def two : Q16_16 := UInt32.ofNat 131072
def three : Q16_16 := UInt32.ofNat 196608

def satFromNat (n : Nat) : Q16_16 :=
  if n > maxNat then UInt32.ofNat maxNat else UInt32.ofNat n

def satMul (x y : Q16_16) : Q16_16 :=
  let xNat := x.toNat
  let yNat := y.toNat
  let product := (xNat * yNat) / scale
  satFromNat product

def add (x y : Q16_16) : Q16_16 :=
  let sum := x.toNat + y.toNat
  satFromNat sum

end Q16_16

structure QuantizedThroatInput where
  pinchLoad : Q16_16
  collapseLoad : Q16_16
  boundaryLoad : Q16_16
  rejectCount : Nat
  channelCount : Nat
  branchCount : Nat
  gateCount : Nat
  mediumRegime : MediumRegime
  manifoldRegime : PlasmaManifoldRegime
  topologyRegime : PlasmaTopologyRegime
  invariantSurvivor : PlasmaTopologyInvariantSurvivor
  stabilityClass : StabilityClass
  deriving Repr, DecidableEq

inductive ThroatRegime
| openChannel
| pinch
| throat
| collapse
  deriving Repr, DecidableEq

structure ThroatState where
  regime : ThroatRegime
  stabilityClass : StabilityClass
  deriving Repr, DecidableEq

def stabilityBias (stability : StabilityClass) : Q16_16 :=
  match stability with
  | .stable => Q16_16.quarter
  | .singular => Q16_16.three
  | .throat => Q16_16.one
  | .unstable => Q16_16.half
  | .collapsed => Q16_16.two

def pinchIndex (pinchLoad : Q16_16) (stabilityClass : StabilityClass) : Q16_16 :=
  Q16_16.add pinchLoad (stabilityBias stabilityClass)

def boundaryPressure (boundaryLoad : Q16_16) (stabilityClass : StabilityClass) : Q16_16 :=
  Q16_16.add boundaryLoad (stabilityBias stabilityClass)

def collapseGradient (collapseLoad : Q16_16) (stabilityClass : StabilityClass) : Q16_16 :=
  Q16_16.add collapseLoad (stabilityBias stabilityClass)

def quantizeThroat (pinchLoad collapseLoad boundaryLoad : Q16_16)
                     (_rejectCount _channelCount _branchCount _gateCount : Nat)
                     (_mediumRegime : MediumRegime)
                     (_manifoldRegime : PlasmaManifoldRegime)
                     (_topologyRegime : PlasmaTopologyRegime)
                     (_invariantSurvivor : PlasmaTopologyInvariantSurvivor)
                     (stabilityClass : StabilityClass) : ThroatState :=
  let regime : ThroatRegime :=
    let pi := pinchIndex pinchLoad stabilityClass
    let cg := collapseGradient collapseLoad stabilityClass
    let bp := boundaryPressure boundaryLoad stabilityClass
    if UInt32.toNat pi > 131072 then .pinch
    else if UInt32.toNat cg > 65536 then .collapse
    else if UInt32.toNat bp > 32768 then .throat
    else .openChannel
  { regime := regime, stabilityClass := stabilityClass }

end ExtensionScaffold.Thermodynamics.ThroatPhysics
