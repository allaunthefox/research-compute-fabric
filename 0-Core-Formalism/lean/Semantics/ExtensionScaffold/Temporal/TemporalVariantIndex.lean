namespace Semantics.Temporal.TemporalVariantIndex

/-
  Temporal Variant Index (TVI)
  ----------------------------
  Scaffold-grade experimental module.

  Status:
  - extension only
  - Q16.16 only
  - intended as a testing branch for temporal compatibility metrics
  - not imported by core Semantics

  Purpose:
  - provide a provisional metric for temporal mismatch
  - decompose failure into diagnosable axes
  - support later domains such as spike syncing
-/

/-- Fixed-point Q16.16 value stored in UInt32. -/
abbrev Q16_16 := UInt32

def qZero : Q16_16 := 0
def qOne  : Q16_16 := 0x00010000

/-- Natural number to Q16.16 integer embedding. -/
def qOfNat (n : Nat) : Q16_16 :=
  UInt32.ofNat (n * 65536)

/-- Saturating addition placeholder for Q16.16. -/
def qAdd (a b : Q16_16) : Q16_16 := a + b

/-- Absolute difference on naturals. -/
def natAbsDiff (a b : Nat) : Nat :=
  if a ≥ b then a - b else b - a

/-
  Core TVI decomposition
  ----------------------
  Keep the vector visible so failures are diagnosable.
-/

/-- A decomposed TVI vector. -/
structure TviVector where
  timing   : Q16_16    -- temporal alignment strain
  rate     : Q16_16    -- event-rate mismatch
  pattern  : Q16_16    -- structure/burst mismatch
  collapse : Q16_16    -- cost of coarse-graining / information loss
deriving Repr, DecidableEq

/-- Scalar TVI summary. -/
def total (v : TviVector) : Q16_16 :=
  qAdd (qAdd v.timing v.rate) (qAdd v.pattern v.collapse)

/-- Zero TVI vector. -/
def zero : TviVector :=
  { timing := qZero, rate := qZero, pattern := qZero, collapse := qZero }

/-- Componentwise boundedness policy for provisional admissibility. -/
structure TviPolicy where
  maxTiming   : Q16_16
  maxRate     : Q16_16
  maxPattern  : Q16_16
  maxCollapse : Q16_16
  maxTotal    : Q16_16
deriving Repr, DecidableEq

/-- Provisional admissibility: each axis and total stay within policy bounds. -/
def admissible (p : TviPolicy) (v : TviVector) : Prop :=
  v.timing   ≤ p.maxTiming ∧
  v.rate     ≤ p.maxRate ∧
  v.pattern  ≤ p.maxPattern ∧
  v.collapse ≤ p.maxCollapse ∧
  total v    ≤ p.maxTotal

/-
  Generic temporal profile
  ------------------------
  This avoids committing to neural spikes too early.
-/

/-- A minimal temporal profile suitable for provisional TVI calculations. -/
structure TemporalProfile where
  eventCount     : Nat
  meanGap        : Nat    -- average interval surrogate
  patternCount   : Nat    -- coarse structural feature count
  collapseBudget : Nat    -- allowed coarse-graining budget
deriving Repr, DecidableEq

/-- Timing error between two temporal profiles. -/
def timingError (a b : TemporalProfile) : Nat :=
  natAbsDiff a.meanGap b.meanGap

/-- Rate error between two temporal profiles. -/
def rateError (a b : TemporalProfile) : Nat :=
  natAbsDiff a.eventCount b.eventCount

/-- Pattern error between two temporal profiles. -/
def patternError (a b : TemporalProfile) : Nat :=
  natAbsDiff a.patternCount b.patternCount

/-- Collapse error induced by mismatch in collapse budget. -/
def collapseError (a b : TemporalProfile) : Nat :=
  natAbsDiff a.collapseBudget b.collapseBudget

/-- Build a provisional TVI vector from two temporal profiles. -/
def fromProfiles (a b : TemporalProfile) : TviVector :=
  { timing   := qOfNat (timingError a b)
    rate     := qOfNat (rateError a b)
    pattern  := qOfNat (patternError a b)
    collapse := qOfNat (collapseError a b) }

/-
  Interpretation helpers
  ----------------------
  These are for diagnosis, not ontology.
-/

/-- Which axis dominates the current TVI? -/
inductive TviAxis
| timing
| rate
| pattern
| collapse
deriving Repr, DecidableEq

/-- Return the dominant error axis. -/
def dominantAxis (v : TviVector) : TviAxis :=
  if v.timing ≥ v.rate ∧ v.timing ≥ v.pattern ∧ v.timing ≥ v.collapse then
    .timing
  else if v.rate ≥ v.pattern ∧ v.rate ≥ v.collapse then
    .rate
  else if v.pattern ≥ v.collapse then
    .pattern
  else
    .collapse

/-
  Basic theorems / witnesses
  --------------------------
  Scaffold modules still need witnesses.
-/

/-- Total cost of the zero vector is zero. -/
theorem total_zero : total zero = qZero := by
  rfl

/-- Any profile compared to itself has zero TVI. -/
theorem fromProfiles_self (a : TemporalProfile) :
    fromProfiles a a = zero := by
  cases a
  simp [fromProfiles, timingError, rateError, patternError, collapseError,
        natAbsDiff, zero, qOfNat, qZero]

/-- A zero TVI vector is admissible under any policy whose bounds are nonnegative. -/
theorem zero_admissible (p : TviPolicy) :
    admissible p zero := by
  unfold admissible zero total
  simp [qZero]

/-
  Example witnesses
-/

def exampleA : TemporalProfile :=
  { eventCount := 10, meanGap := 4, patternCount := 2, collapseBudget := 0 }

def exampleB : TemporalProfile :=
  { eventCount := 12, meanGap := 5, patternCount := 3, collapseBudget := 1 }

def examplePolicy : TviPolicy :=
  { maxTiming   := qOfNat 2
    maxRate     := qOfNat 3
    maxPattern  := qOfNat 2
    maxCollapse := qOfNat 1
    maxTotal    := qOfNat 6 }

#eval fromProfiles exampleA exampleB
#eval total (fromProfiles exampleA exampleB)
#eval dominantAxis (fromProfiles exampleA exampleB)
-- Note: admissible returns Prop, use in theorem context or with decide
#eval decide (admissible examplePolicy (fromProfiles exampleA exampleB))

end Semantics.Temporal.TemporalVariantIndex
