/-!
# Continued Fraction Compression Surface

This module tests whether existing ratio-heavy Research Stack math can be
adapted into a vectorless continued-fraction codec.

The target is not real-number theorem proving. The target is exact, integer
replay: a finite partial-quotient stream reconstructs a rational carrier, and
promotion is allowed only when the partial-quotient stream plus residual and
receipt bytes beats the baseline representation.
-/

namespace Semantics.ContinuedFractionCompression

/-! ## Adaptation targets -/

/-- Repo math surfaces that naturally expose rational ratio ladders. -/
inductive CfAdaptationSurface where
  | goldenPhiRatio
  | recursiveBranchCutRatio
  | fixedPointThreshold
  | sidecarByteLaw
  | holographicBoundaryRatio
  | genericIntegerPayload
  deriving DecidableEq, Repr

/-- A rational carrier recovered from a continued fraction. -/
structure RationalCarrier where
  numerator : Nat
  denominator : Nat
  deriving Repr, DecidableEq

/-- A continued-fraction packet keeps integer partial quotients plus receipt cost. -/
structure ContinuedFractionPacket where
  surface : CfAdaptationSurface
  partialQuotients : List Nat
  target : RationalCarrier
  residualBytes : Nat
  receiptBytes : Nat
  baselineBytes : Nat
  deriving Repr, DecidableEq

/-! ## Exact continued fraction replay -/

/--
Evaluate a finite simple continued fraction as a numerator/denominator pair.
For example, `[1, 1, 1, 1, 1]` reconstructs `8/5`.
-/
def evalCf : List Nat → RationalCarrier
  | [] => { numerator := 0, denominator := 1 }
  | [a] => { numerator := a, denominator := 1 }
  | a :: rest =>
      let tail := evalCf rest
      { numerator := a * tail.numerator + tail.denominator
        denominator := tail.numerator }

/-- Nonempty CFs may have zero first quotient, but later quotients must be positive. -/
def partialQuotientsAdmissible : List Nat → Bool
  | [] => false
  | [_] => true
  | _ :: rest => rest.all (fun q => q > 0)

/-- Hardware-friendly first pass: every quotient fits in one byte. -/
def partialQuotientsByteSized (qs : List Nat) : Bool :=
  qs.all (fun q => q < 256)

/-- Current byte model: one byte per quotient when byte-sized. -/
def cfPayloadBytes (qs : List Nat) : Nat :=
  qs.length

/-- Exact replay gate. -/
def cfReconstructs (qs : List Nat) (target : RationalCarrier) : Bool :=
  partialQuotientsAdmissible qs &&
  let recovered := evalCf qs
  recovered.numerator == target.numerator &&
  recovered.denominator == target.denominator

/-- Continued-fraction byte law for compression promotion. -/
def cfByteLawHolds (p : ContinuedFractionPacket) : Bool :=
  partialQuotientsByteSized p.partialQuotients &&
  cfPayloadBytes p.partialQuotients + p.residualBytes + p.receiptBytes < p.baselineBytes

/-- A CF packet promotes only if it exactly replays and beats byte accounting. -/
def cfCompressionPromotable (p : ContinuedFractionPacket) : Bool :=
  cfReconstructs p.partialQuotients p.target &&
  cfByteLawHolds p

/-! ## Canonical packets -/

/-- Golden-ratio convergent: [1;1,1,1,1] = 8/5. -/
def phiFivePacket : ContinuedFractionPacket :=
  { surface := CfAdaptationSurface.goldenPhiRatio
    partialQuotients := [1, 1, 1, 1, 1]
    target := { numerator := 8, denominator := 5 }
    residualBytes := 1
    receiptBytes := 1
    baselineBytes := 16 }

/-- Phi-squared convergent: [2;1,1,1,1] = 13/5, close to 2.6. -/
def phiSquaredPacket : ContinuedFractionPacket :=
  { surface := CfAdaptationSurface.recursiveBranchCutRatio
    partialQuotients := [2, 1, 1, 1, 1]
    target := { numerator := 13, denominator := 5 }
    residualBytes := 1
    receiptBytes := 1
    baselineBytes := 16 }

/-- DNA-style 10.5 ratio as exact rational 21/2 = [10;2]. -/
def tenPointFivePacket : ContinuedFractionPacket :=
  { surface := CfAdaptationSurface.fixedPointThreshold
    partialQuotients := [10, 2]
    target := { numerator := 21, denominator := 2 }
    residualBytes := 1
    receiptBytes := 1
    baselineBytes := 16 }

/-- A route that is exact but not byte-sized for a one-byte quotient stream. -/
def largeQuotientPacket : ContinuedFractionPacket :=
  { surface := CfAdaptationSurface.recursiveBranchCutRatio
    partialQuotients := [1000]
    target := { numerator := 1000, denominator := 1 }
    residualBytes := 1
    receiptBytes := 1
    baselineBytes := 16 }

/-- A route that reconstructs but loses byte law after residual/receipt overhead. -/
def aestheticCfPacket : ContinuedFractionPacket :=
  { phiFivePacket with
    residualBytes := 8
    receiptBytes := 8
    baselineBytes := 16 }

/-! ## Executable witnesses -/

theorem phi_five_reconstructs :
    evalCf [1, 1, 1, 1, 1] = { numerator := 8, denominator := 5 } := by
  native_decide

theorem phi_squared_reconstructs :
    evalCf [2, 1, 1, 1, 1] = { numerator := 13, denominator := 5 } := by
  native_decide

theorem ten_point_five_reconstructs :
    evalCf [10, 2] = { numerator := 21, denominator := 2 } := by
  native_decide

theorem phi_packet_promotable :
    cfCompressionPromotable phiFivePacket = true := by
  native_decide

theorem phi_squared_packet_promotable :
    cfCompressionPromotable phiSquaredPacket = true := by
  native_decide

theorem ten_point_five_packet_promotable :
    cfCompressionPromotable tenPointFivePacket = true := by
  native_decide

theorem large_quotient_not_promotable :
    cfCompressionPromotable largeQuotientPacket = false := by
  native_decide

theorem aesthetic_cf_packet_not_promotable :
    cfCompressionPromotable aestheticCfPacket = false := by
  native_decide

/-- Any promoted CF packet exactly reconstructs its target rational carrier. -/
theorem promotable_cf_reconstructs (p : ContinuedFractionPacket) :
    cfCompressionPromotable p = true -> cfReconstructs p.partialQuotients p.target = true := by
  unfold cfCompressionPromotable
  intro h
  cases hReplay : cfReconstructs p.partialQuotients p.target
  · simp [hReplay] at h
  · simp

/-- Any promoted CF packet satisfies the byte law. -/
theorem promotable_cf_satisfies_byte_law (p : ContinuedFractionPacket) :
    cfCompressionPromotable p = true -> cfByteLawHolds p = true := by
  unfold cfCompressionPromotable
  intro h
  cases hReplay : cfReconstructs p.partialQuotients p.target
  · simp [hReplay] at h
  cases hBytes : cfByteLawHolds p
  · simp [hReplay, hBytes] at h
  · simp

#eval evalCf [1, 1, 1, 1, 1]
#eval evalCf [2, 1, 1, 1, 1]
#eval evalCf [10, 2]
#eval cfCompressionPromotable phiFivePacket
#eval cfCompressionPromotable largeQuotientPacket

end Semantics.ContinuedFractionCompression
