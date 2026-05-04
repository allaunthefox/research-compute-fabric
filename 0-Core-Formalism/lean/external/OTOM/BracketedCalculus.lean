/-
  BracketedCalculus.lean - DIAT Extension to Bracketed Calculus
-/

import Semantics.DynamicCanal

namespace Semantics.BracketedCalculus

open DynamicCanal

structure BracketedDIAT where
  lower : Fix16
  upper : Fix16
  value : Fix16
  lowerGap : Fix16
  upperGap : Fix16
  scale : UInt32
  prod : Fix16
  diff : Int32
  deriving Repr, DecidableEq, BEq

namespace BracketedDIAT

def encode (lower value upper : Fix16) (scale : UInt32) : BracketedDIAT :=
  let lowerGap := Fix16.sub value lower
  let upperGap := Fix16.sub upper value
  let prod := Fix16.mul lowerGap upperGap
  let diff := Int32.ofNat (lowerGap.raw.toNat) - Int32.ofNat (upperGap.raw.toNat)
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

def width (b : BracketedDIAT) : Fix16 :=
  Fix16.sub b.upper b.lower

def checkGapConservation (b : BracketedDIAT) : Bool :=
  let sumGaps := Fix16.add b.lowerGap b.upperGap
  sumGaps.raw == (width b).raw

def isInterior (b : BracketedDIAT) : Bool :=
  b.lowerGap.raw > 0 && b.upperGap.raw > 0

def bracketAdd (x y : BracketedDIAT) : BracketedDIAT :=
  let newLower := Fix16.add x.lower y.lower
  let newValue := Fix16.add x.value y.value
  let newUpper := Fix16.add x.upper y.upper
  encode newLower newValue newUpper (UInt32.ofNat (Nat.max x.scale.toNat y.scale.toNat))

def bracketMulConservative (x y : BracketedDIAT) : BracketedDIAT :=
  let v1 := Fix16.mul x.lower y.lower
  let v2 := Fix16.mul x.lower y.upper
  let v3 := Fix16.mul x.upper y.lower
  let v4 := Fix16.mul x.upper y.upper
  let newLower := Fix16.min (Fix16.min v1 v2) (Fix16.min v3 v4)
  let newUpper := Fix16.max (Fix16.max v1 v2) (Fix16.max v3 v4)
  let newValue := Fix16.mul x.value y.value
  encode newLower newValue newUpper (UInt32.ofNat (Nat.max x.scale.toNat y.scale.toNat))

def bracketNeg (b : BracketedDIAT) : BracketedDIAT :=
  let newLower := Fix16.neg b.upper
  let newValue := Fix16.neg b.value
  let newUpper := Fix16.neg b.lower
  encode newLower newValue newUpper b.scale

def taylorWithinTolerance (b : BracketedDIAT) (tolerance : Fix16) : Bool :=
  let maxError := Fix16.max b.lowerGap b.upperGap
  maxError.raw <= tolerance.raw

def derivativeEstimate (b : BracketedDIAT) (h : Fix16) : Fix16 :=
  let diff := Fix16.sub b.upperGap b.lowerGap
  let twoH := Fix16.mul h (Fix16.mk 0x00020000)
  Fix16.div diff twoH

def secondDerivativeEstimate (b : BracketedDIAT) (h : Fix16) : Fix16 :=
  let h2 := Fix16.mul h h
  let asym := Fix16.mk (UInt32.ofInt b.diff.toInt)
  Fix16.neg (Fix16.div asym h2)

def adaptiveRefine (b : BracketedDIAT) (curvatureThreshold : Fix16)
                   ( _shrinkFactor  : Fix16) : BracketedDIAT × Bool :=
  let asymMag := Fix16.mk (UInt32.ofNat (Int.natAbs b.diff.toInt))
  if asymMag.raw > curvatureThreshold.raw then
    (b, true)
  else
    (b, false)

end BracketedDIAT

#eval (BracketedDIAT.encode Fix16.zero (Fix16.mk 0x00050000) (Fix16.mk 0x000A0000) 0).value.raw

end Semantics.BracketedCalculus
