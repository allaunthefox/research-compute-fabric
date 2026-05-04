import Semantics.FixedPoint
import Semantics.UnifiedSchema

namespace Semantics.Hyperfluid

structure Point where
  id : String
  sigma : UInt32
  v : UInt32
  stability : String
deriving Repr, BEq

def propagateStress (points : List (String × Point)) : List (String × String) :=
  let highStress := points.filter (fun p => p.2.sigma > 0x0000CCCC) -- > 0.8
  highStress.flatMap (fun p1 => 
    points.filter (fun p2 => p1.1 != p2.1)
    |>.map (fun p2 => (p1.1, p2.1)))

#eval propagateStress [("a", {id := "1", sigma := 0x0000FFFF, v := 0, stability := "STABLE"}), ("b", {id := "2", sigma := 0, v := 0, stability := "STABLE"})]

end Semantics.Hyperfluid
