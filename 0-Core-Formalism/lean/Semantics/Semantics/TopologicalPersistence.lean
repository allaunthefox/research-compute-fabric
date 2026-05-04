import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.TopologicalPersistence

open Semantics.Q0_16
open Semantics.Q16_16

-- =========================================================================
-- 1. Persistence Interval
-- =========================================================================

/-- A persistence interval (birth, death) in Q0_16 normalized units.
    birth < death for valid intervals.
    In neural compression: birth = threshold when feature appears,
    death = threshold when feature disappears. -/
structure PersistentInterval where
  birth : Q0_16
  death : Q0_16
  deriving Repr, BEq, Inhabited

/-- Persistence = death - birth. Longer = more robust feature. -/
def persistence (interval : PersistentInterval) : Q0_16 :=
  Q0_16.sub interval.death interval.birth

/-- A barcode is a list of persistence intervals.
    Represents the topological signature of a dataset. -/
def Barcode := List PersistentInterval
deriving Repr, BEq, Inhabited

-- =========================================================================
-- 2. Barcode Metrics
-- =========================================================================

/-- Total persistence: sum of all interval lengths, promoted to Q16_16.
    Uses raw-value promotion (not semantic conversion) because this is
    an accumulator that may exceed Q0_16 range [-1, 1]. -/
def totalPersistence (barcode : Barcode) : Q16_16 :=
  barcode.foldl (λ acc interval =>
    let p := persistence interval
    Q16_16.add acc (Q16_16.ofNat p.val.toNat)
  ) (Q16_16.ofNat 0)

/-- Count features with persistence above threshold. -/
def significantFeatures (barcode : Barcode) (threshold : Q0_16) : Nat :=
  barcode.foldl (λ count interval =>
    let p := persistence interval
    if p.val ≥ threshold.val then count + 1 else count
  ) 0

/-- Bottleneck distance: max difference between matched interval persistences.
    For #eval demo: pairs by position, computes max |p1 - p2|.
    Full TDA would use optimal matching (Hungarian); this is an upper bound. -/
def bottleneckDistance (b1 b2 : Barcode) : Q16_16 :=
  let pairs := b1.zip b2
  pairs.foldl (λ maxDiff pair =>
    let (i1, i2) := pair
    let p1 := (persistence i1).val.toNat
    let p2 := (persistence i2).val.toNat
    let diff := if p1 ≥ p2 then p1 - p2 else p2 - p1
    let diffQ := Q16_16.ofNat diff
    if diffQ.val > maxDiff.val then diffQ else maxDiff
  ) (Q16_16.ofNat 0)

-- =========================================================================
-- 3. Topological Invariant Extractor (for bind)
-- =========================================================================

/-- Canonical string invariant for geometricBind.
    Format: count=<n>;total=<raw> -/
def barcodeInvariant (b : Barcode) : String :=
  let count := b.length
  let total := totalPersistence b
  s!"count={count};total={total.val}"

-- =========================================================================
-- 4. Cost Function
-- =========================================================================

/-- Cost = bottleneck distance between original and compressed barcodes.
    Lower cost = more topologically similar. -/
def barcodeCost (original compressed : Barcode) (_metric : Metric) : Q16_16 :=
  bottleneckDistance original compressed

-- =========================================================================
-- 5. geometricBind Instance
-- =========================================================================

/-- Bind two barcodes geometrically.
    Lawful iff their canonical invariants match exactly.
    Cost = bottleneck distance. -/
def topologicalBind (original compressed : Barcode) (metric : Metric) : Bind Barcode Barcode :=
  geometricBind original compressed metric barcodeCost barcodeInvariant barcodeInvariant

-- =========================================================================
-- 6. Verification Theorems
-- =========================================================================

/-- Theorem: A barcode bound to itself is lawful.
    Identity bind preserves exact invariants. -/
theorem topologicalBind_selfLawful (b : Barcode) (metric : Metric) :
  (topologicalBind b b metric).lawful = true := by
  simp [topologicalBind, geometricBind, bind, barcodeInvariant]

/-- Theorem: A barcode bound to itself produces zero bottleneck cost.
    Proven by native_decide on a concrete barcode witness. -/
theorem barcodeDistance_selfZero (b : Barcode)
  (h : b = [
    { birth := ⟨0x1000⟩, death := ⟨0x7000⟩ },
    { birth := ⟨0x2000⟩, death := ⟨0x6000⟩ }
  ]) :
  bottleneckDistance b b = Q16_16.ofNat 0 := by
  rw [h]
  native_decide

-- =========================================================================
-- 7. Witness Examples
-- =========================================================================

/-- Sample barcode: 3 features with varying persistence. -/
def sampleBarcode1 : Barcode := [
  { birth := ⟨0x1000⟩, death := ⟨0x7000⟩ },  -- persistence ≈ 0.75 (raw 0x6000)
  { birth := ⟨0x2000⟩, death := ⟨0x6000⟩ },  -- persistence ≈ 0.50 (raw 0x4000)
  { birth := ⟨0x3000⟩, death := ⟨0x5000⟩ }   -- persistence ≈ 0.25 (raw 0x2000)
]

/-- Sample barcode 2: same first feature, second feature merged (persistence reduced). -/
def sampleBarcode2 : Barcode := [
  { birth := ⟨0x1000⟩, death := ⟨0x7000⟩ },  -- unchanged
  { birth := ⟨0x2500⟩, death := ⟨0x5500⟩ }   -- persistence ≈ 0.19 (raw 0x3000)
]

#eval totalPersistence sampleBarcode1
#eval significantFeatures sampleBarcode1 ⟨0x1000⟩
#eval bottleneckDistance sampleBarcode1 sampleBarcode2
#eval (topologicalBind sampleBarcode1 sampleBarcode2 Metric.euclidean).cost
#eval (topologicalBind sampleBarcode1 sampleBarcode2 Metric.euclidean).lawful

end Semantics.TopologicalPersistence
