import Semantics.FixedPoint

namespace Semantics.BindEngine

structure SMInvariants where
  b : Int := 1
  l : Int := 1
  q : Int := 0
  phi : String := "ambient"
  tPast : Bool := true
deriving Repr, BEq

def verifyLawfulLoss (left right : SMInvariants) : Bool :=
  left.b == right.b && left.l == right.l

def calculateBindCost (iota : Nat) : UInt32 :=
  0x00010000 * (UInt32.ofNat (iota + 1))

#eval verifyLawfulLoss {} {}
#eval calculateBindCost 0

end Semantics.BindEngine
