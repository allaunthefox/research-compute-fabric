import Semantics.FixedPoint
import Semantics.Bind

namespace Semantics.FuzzyAssociation

/--
FuzzyMatch: Represents a non-explicit connection between two concepts.
Confidence is a Q16.16 value between 0 and 1.
-/
structure FuzzyMatch where
  sourcePkg : String
  targetPkg : String
  confidence : Q16_16
  rationale : String

/--
Fuzzy Admissibility: A match is 'Interesting' if its confidence 
is above the discovery threshold (0.4 ≈ 0x00006666 in Q16.16).
-/
def isInteresting (m : FuzzyMatch) : Bool :=
  Q16_16.ge m.confidence (Q16_16.ofFloat 0.4)

/--
The Fuzzy Bind: Connects an external paper to a local research node 
via 'Near-Neighbor' semantic projection.
-/
def fuzzyBind (matchInfo : FuzzyMatch) (g : Metric) : Bind FuzzyMatch String :=
  controlBind matchInfo matchInfo.targetPkg g 
    (fun m _ _ => (Q16_16.sub Q16_16.one m.confidence).val) -- Cost is higher for low confidence
    (fun m => if isInteresting m then "fuzzy_bridge_detected" else "below_discovery_threshold")
    (fun targetPkg => s!"witness:fuzzy_connection:{matchInfo.sourcePkg}-->{targetPkg}")

end Semantics.FuzzyAssociation
