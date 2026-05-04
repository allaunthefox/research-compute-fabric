import Semantics.FixedPoint
import Semantics.Bind

namespace Semantics.FuzzyAssociation

open Semantics

/--
FuzzyMatch: Represents a non-explicit connection between two concepts.
Confidence is a Q0.16 value between 0 and 1 (2-byte pure fraction).
-/
structure FuzzyMatch where
  sourcePkg : String
  targetPkg : String
  confidence : Q0_16
  rationale : String

/--
Fuzzy Admissibility: A match is 'Interesting' if its confidence 
is above the discovery threshold (0.4 ≈ 0x3333 in Q0.16).
-/
def isInteresting (m : FuzzyMatch) : Bool :=
  let threshold := Q0_16.ofFloat 0.4
  Q0_16.gt m.confidence threshold

/--
The Fuzzy Bind: Connects an external paper to a local research node 
via 'Near-Neighbor' semantic projection.
-/
def fuzzyBind (matchInfo : FuzzyMatch) (g : Metric) : Bind FuzzyMatch String :=
  controlBind matchInfo matchInfo.targetPkg g 
    (fun m _ _ => Q16_16.sub Q16_16.one (Q16_16.ofFloat (Q0_16.toFloat m.confidence))) -- Convert Q0_16 to Q16_16 for compatibility
    (fun m => if isInteresting m then "fuzzy_bridge_detected" else "below_discovery_threshold")
    (fun targetPkg => s!"witness:fuzzy_connection:{matchInfo.sourcePkg}-->{targetPkg}")

end Semantics.FuzzyAssociation
