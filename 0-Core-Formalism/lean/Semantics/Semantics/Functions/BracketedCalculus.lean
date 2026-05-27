/-
  BracketedCalculus.lean - DIAT Extension to Bracketed Calculus
-/

import Semantics.FixedPoint

namespace Semantics.BracketedCalculus

open Semantics.Q16_16

structure BracketedDIAT where
  lower : Q16_16
  upper : Q16_16
  value : Q16_16
  lowerGap : Q16_16
  upperGap : Q16_16
  scale : UInt32
  prod : Q16_16
  diff : Int32
  deriving Repr, DecidableEq, BEq

namespace BracketedDIAT

def encode (lower value upper : Q16_16) (scale : UInt32) : BracketedDIAT :=
  let lowerGap := value - lower
  let upperGap := upper - value
  let prod := lowerGap * upperGap
  let diff := Int32.ofNat (lowerGap.val.toNat) - Int32.ofNat (upperGap.val.toNat)
  {
    lower := lower
    upper := upper
    value := value
    lowerGap := lowerGap
    upperGap := upperGap
    scale := scale
    prod := prod
    diff := diff
  }

def width (b : BracketedDIAT) : Q16_16 :=
  b.upper - b.lower

def checkGapConservation (b : BracketedDIAT) : Bool :=
  let sumGaps := b.lowerGap + b.upperGap
  sumGaps.val == (width b).val

def isInterior (b : BracketedDIAT) : Bool :=
  b.lowerGap.val > 0 && b.upperGap.val > 0

def bracketAdd (x y : BracketedDIAT) : BracketedDIAT :=
  let newLower := x.lower + y.lower
  let newValue := x.value + y.value
  let newUpper := x.upper + y.upper
  encode newLower newValue newUpper (UInt32.ofNat (Nat.max x.scale.toNat y.scale.toNat))

def bracketMulConservative (x y : BracketedDIAT) : BracketedDIAT :=
  let v1 := x.lower * y.lower
  let v2 := x.lower * y.upper
  let v3 := x.upper * y.lower
  let v4 := x.upper * y.upper
  let newLower := Q16_16.min (Q16_16.min v1 v2) (Q16_16.min v3 v4)
  let newUpper := Q16_16.max (Q16_16.max v1 v2) (Q16_16.max v3 v4)
  let newValue := x.value * y.value
  encode newLower newValue newUpper (UInt32.ofNat (Nat.max x.scale.toNat y.scale.toNat))

def bracketNeg (b : BracketedDIAT) : BracketedDIAT :=
  let newLower := -b.upper
  let newValue := -b.value
  let newUpper := -b.lower
  encode newLower newValue newUpper b.scale

def taylorWithinTolerance (b : BracketedDIAT) (tolerance : Q16_16) : Bool :=
  let maxError := Q16_16.max b.lowerGap b.upperGap
  maxError.val <= tolerance.val

def derivativeEstimate (b : BracketedDIAT) (h : Q16_16) : Q16_16 :=
  let diff := b.upperGap - b.lowerGap
  let twoH := h * two
  diff / twoH

def secondDerivativeEstimate (b : BracketedDIAT) (h : Q16_16) : Q16_16 :=
  let h2 := h * h
  let asym := Q16_16.ofInt b.diff.toInt
  Q16_16.neg (asym / h2)

def adaptiveRefine (b : BracketedDIAT) (curvatureThreshold : Q16_16)
                   ( _shrinkFactor  : Q16_16) : BracketedDIAT × Bool :=
  let asymMag := Q16_16.ofInt (Int.natAbs b.diff.toInt)
  if asymMag.val > curvatureThreshold.val then
    (b, true)
  else
    (b, false)

end BracketedDIAT

#eval (BracketedDIAT.encode zero (Q16_16.ofFloat 5.0) (Q16_16.ofFloat 10.0) 0).value.val  -- expect: 327680

end Semantics.BracketedCalculus
