import Semantics.Bind

namespace Semantics.Hutter

/--
A HutterCell represents a pair of bytes decomposed into 4-bit nibbles.
Matches the behavior of `byte_to_cell_pair` in the Python extraction target.
-/
structure HutterCell where
  n1 : UInt8
  n2 : UInt8
  n3 : UInt8
  n4 : UInt8

/--
The signature of a cell: the top 2 bits of each nibble.
-/
def signature (c : HutterCell) : (UInt8 × UInt8 × UInt8 × UInt8) :=
  ((c.n1 >>> 2) &&& 0x03, (c.n2 >>> 2) &&& 0x03, (c.n3 >>> 2) &&& 0x03, (c.n4 >>> 2) &&& 0x03)

/--
HutterMetrics: Tracks the results of a cellular analysis.
-/
structure HutterMetrics where
  totalCells : UInt64
  admissiblePatches : UInt64
  promotionCandidates : UInt64

/--
The Admissibility Ratio: (admissible / total) scaled by Q16.16.
-/
def admissibilityRatio (m : HutterMetrics) : UInt32 :=
  if m.totalCells == 0 then 0
  else (m.admissiblePatches.toUInt32 * 0x00010000) / m.totalCells.toUInt32

/--
Invariant: A Hutter result is lawful if the admissibility ratio is above 
the Golden Threshold (0.618 ≈ 0x00009E37 in Q16.16).
-/
def hutterInvariant (m : HutterMetrics) : String :=
  let ratio := admissibilityRatio m
  if ratio >= 0x00009E37 then "lawful_hutter_compression"
  else "unlawful_hutter_drift"

/--
Cost function: Measures the informational cost of the Hutter result.
Higher promotion candidates reduce the cost (more predictable structure).
-/
def hutterCost (m : HutterMetrics) (_g : Metric) : Q16_16 :=
  let base : Nat := 0x00010000 -- 1.0
  let discount := m.promotionCandidates.toNat * 0x00000100 -- Small discount per candidate
  let result := if discount >= base then 0x00000100 else base - discount
  Q16_16.ofNat result

/--
The Hutter Bind: Connects the compression metrics to the research substrate.
-/
def hutterBind (metrics : HutterMetrics) (target : String) (g : Metric) : Bind HutterMetrics String :=
  controlBind metrics target g (fun m _ _ => hutterCost m g) hutterInvariant (fun _ => "hutter_compression_verified")

end Semantics.Hutter
