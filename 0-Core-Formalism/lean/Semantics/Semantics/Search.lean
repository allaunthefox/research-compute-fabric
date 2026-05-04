import Semantics.FixedPoint
import Mathlib.Data.List.Sort

namespace Semantics.Search

/-- Precomputed φ⁻ⁱ weights in Q16.16 for i = 0..13.
    φ ≈ 1.618033988749895, so φ⁻¹ ≈ 0.618, φ⁻² ≈ 0.382, etc.
    These are computed as round(φ⁻ⁱ × 65536). -/
def phiWeights : Array Q16_16 := #[
  ⟨0x00010000⟩, -- φ⁰  = 1.00000
  ⟨0x00009E37⟩, -- φ⁻¹ ≈ 0.61803
  ⟨0x000061A8⟩, -- φ⁻² ≈ 0.38197
  ⟨0x00003C5C⟩, -- φ⁻³ ≈ 0.23607
  ⟨0x0000256C⟩, -- φ⁻⁴ ≈ 0.14590
  ⟨0x00001710⟩, -- φ⁻⁵ ≈ 0.09017
  ⟨0x00000E44⟩, -- φ⁻⁶ ≈ 0.05573
  ⟨0x000008D8⟩, -- φ⁻⁷ ≈ 0.03444
  ⟨0x00000570⟩, -- φ⁻⁸ ≈ 0.02129
  ⟨0x00000364⟩, -- φ⁻⁹ ≈ 0.01316
  ⟨0x00000218⟩, -- φ⁻¹⁰≈ 0.00813
  ⟨0x0000014C⟩, -- φ⁻¹¹≈ 0.00502
  ⟨0x000000D0⟩, -- φ⁻¹²≈ 0.00310
  ⟨0x00000084⟩  -- φ⁻¹³≈ 0.00192
]

/-- Helper: convert Nat to Q16_16 (n * 65536). -/
def q16_16_of_nat (n : Nat) : Q16_16 := Q16_16.ofInt (Int.ofNat n)

/-- A search record from the ENE substrate. -/
structure SearchRecord where
  id : String
  vector : Array Q16_16
  deriving Repr

/-- Build a query vector from a list of active axis indices (Fin 14).
    Each active axis is set to Q16_16.one (1.0). -/
def queryVector (axes : List (Fin 14)) : Array Q16_16 :=
  let base := Array.mk (List.replicate 14 Q16_16.zero)
  axes.foldl (fun acc ax => acc.set! ax.val Q16_16.one) base

/-- Weighted dot product of two 14D vectors using φ⁻ⁱ weights. -/
def weightedDot (v1 v2 : Array Q16_16) : Q16_16 :=
  let n := min v1.size v2.size
  let n14 := min n 14
  Fin.foldl n14 (fun acc i =>
    let w := phiWeights.getD i.val Q16_16.zero
    let a := v1.getD i.val Q16_16.zero
    let b := v2.getD i.val Q16_16.zero
    Q16_16.add acc (Q16_16.mul w (Q16_16.mul a b))
  ) Q16_16.zero

/-- Weighted magnitude of a 14D vector. -/
def weightedMag (v : Array Q16_16) : Q16_16 :=
  let n := min v.size 14
  Fin.foldl n (fun acc i =>
    let w := phiWeights.getD i.val Q16_16.zero
    let a := v.getD i.val Q16_16.zero
    Q16_16.add acc (Q16_16.mul w (Q16_16.mul a a))
  ) Q16_16.zero

/-- Cosine similarity approximated as dot / (mag1 + mag2 + 1).
    Avoids sqrt (which currently uses Float internally).
    The +1 prevents division by zero and preserves ordering for ranking. -/
def similarity (v1 v2 : Array Q16_16) : Q16_16 :=
  let dot := weightedDot v1 v2
  let mag1 := weightedMag v1
  let mag2 := weightedMag v2
  let denom := Q16_16.add (Q16_16.add mag1 mag2) Q16_16.one
  Q16_16.div dot denom

/-- Reciprocal Rank Fusion score from two ranked lists.
    keywordRanks: list of (id, keyword_rank) where rank is 0-indexed
    semanticRanks: list of (id, semantic_rank) where rank is 0-indexed
    K = 60 in Q16.16 -/
def rrfScore (keywordRanks semanticRanks : List (String × Nat)) (K : Q16_16) : List (String × Q16_16) :=
  let allIds := (keywordRanks.map Prod.fst ++ semanticRanks.map Prod.fst).eraseDups
  allIds.map (fun id =>
    let kwRank := (keywordRanks.find? (fun p => p.1 == id)).map Prod.snd |>.getD 999
    let semRank := (semanticRanks.find? (fun p => p.1 == id)).map Prod.snd |>.getD 999
    let kwScore := Q16_16.div Q16_16.one (Q16_16.add K (q16_16_of_nat (kwRank + 1)))
    let semScore := Q16_16.div Q16_16.one (Q16_16.add K (q16_16_of_nat (semRank + 1)))
    let total := Q16_16.add kwScore semScore
    (id, total)
  )

/-- Threshold for semantic recall filter (0.1 in Q16.16 ≈ 0x0000199A). -/
def similarityThreshold : Q16_16 := ⟨0x0000199A⟩

/-- K for RRF (60 in Q16.16). -/
def rrfK : Q16_16 := q16_16_of_nat 60

/-- Hybrid search: keyword ranks + semantic similarity + RRF.
    Returns list of (id, score) sorted by descending score. -/
def hybridSearch
  (axes : List (Fin 14))
  (keywordIds : List String)
  (records : List SearchRecord)
  : List (String × Q16_16) :=
  let qv := queryVector axes
  let keywordRanks := List.zip (List.range keywordIds.length) keywordIds |>.map (fun p => (p.2, p.1))
  let semanticResults := records.filterMap (fun r =>
    let sim := similarity qv r.vector
    if Q16_16.gt sim similarityThreshold then some (r.id, sim) else none
  )
  let semanticResultsSorted := semanticResults.insertionSort (fun a b => Q16_16.gt a.2 b.2)
  let semanticRanks := List.zip (List.range semanticResultsSorted.length) semanticResultsSorted |>.map (fun p => (p.2.1, p.1))
  let fused := rrfScore keywordRanks semanticRanks rrfK
  fused.insertionSort (fun a b => Q16_16.gt a.2 b.2)

-- #eval witnesses
#eval similarity (queryVector [⟨0, by decide⟩]) (queryVector [⟨0, by decide⟩])
#eval similarity (queryVector [⟨0, by decide⟩]) (queryVector [⟨1, by decide⟩])

end Semantics.Search
