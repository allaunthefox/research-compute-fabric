/-!
# LadderLUT

A LadderLUT is a deterministic expansion packet for ordered fixed-width
symbols.  It replaces an explicit table such as

```text
000, 001, 002, 003, ...
```

with a compact generator rule plus residual and receipt accounting.

The decimal identity `1 / 998001` is treated as a human-visible witness for the
base-1000 family because `998001 = (1000 - 1)^2`.  The codec primitive itself is
finite and byte-law gated; it does not depend on decimal string division.
-/

namespace Semantics.LadderLUT

/-- Deterministic LUT generator families. -/
inductive LadderFamily where
  | blockEnumerator
  | byteNativeEnumerator
  | semanticIdEnumerator
  deriving Repr, DecidableEq

/-- A fixed-width ladder generator packet. -/
structure LadderPacket where
  family : LadderFamily
  radix : Nat
  blockWidth : Nat
  base : Nat
  start : Nat
  length : Nat
  generatorBytes : Nat
  residualBytes : Nat
  receiptBytes : Nat
  deriving Repr, DecidableEq

/-- The intended base for a radix/block-width lane. -/
def expectedBase (p : LadderPacket) : Nat :=
  p.radix ^ p.blockWidth

/-- The classic denominator for the visible repeating block identity. -/
def blockEnumeratorDenominator (base : Nat) : Nat :=
  (base - 1) * (base - 1)

/-- A packet is structurally valid when its declared base matches radix^width. -/
def ladderStructurallyValid (p : LadderPacket) : Bool :=
  p.radix > 1 &&
    p.blockWidth > 0 &&
    p.base == expectedBase p &&
    p.length > 0

/-- Emit the i-th fixed-width symbol in the ladder. -/
def ladderValueAt (p : LadderPacket) (i : Nat) : Nat :=
  (p.start + i) % p.base

/-- Deterministically replay the ladder as a finite list of fixed-width symbols. -/
def replayLadder (p : LadderPacket) : List Nat :=
  (List.range p.length).map (ladderValueAt p)

/-- Explicit table cost: every emitted symbol costs one fixed-width block. -/
def explicitLutBytes (p : LadderPacket) : Nat :=
  p.length * p.blockWidth

/-- Generator cost with declared residual and receipt overhead. -/
def ladderEncodedBytes (p : LadderPacket) : Nat :=
  p.generatorBytes + p.residualBytes + p.receiptBytes

/-- The byte law: generator plus residual plus receipt must beat explicit table bytes. -/
def ladderByteLawHolds (p : LadderPacket) : Bool :=
  ladderEncodedBytes p < explicitLutBytes p

/-- Promotion gate for a deterministic LadderLUT route. -/
def ladderPromotable (p : LadderPacket) : Bool :=
  ladderStructurallyValid p && ladderByteLawHolds p

/-! ## Canonical examples -/

/-- Human-visible decimal toy: base 1000, width 3, denominator (1000-1)^2 = 998001. -/
def decimalThreeDigitPacket : LadderPacket :=
  { family := LadderFamily.blockEnumerator
    radix := 10
    blockWidth := 3
    base := 1000
    start := 0
    length := 10
    generatorBytes := 4
    residualBytes := 0
    receiptBytes := 1 }

/-- Byte-native 3-byte fixed-width enumerator: base = 256^3. -/
def byteThreePacket : LadderPacket :=
  { family := LadderFamily.byteNativeEnumerator
    radix := 256
    blockWidth := 3
    base := 16777216
    start := 0
    length := 128
    generatorBytes := 5
    residualBytes := 0
    receiptBytes := 2 }

/-- Too short to amortize the generator and receipt overhead. -/
def tinyLadderPacket : LadderPacket :=
  { decimalThreeDigitPacket with length := 1 }

/-- Bad base declaration: radix^width does not match the declared base. -/
def badBasePacket : LadderPacket :=
  { decimalThreeDigitPacket with base := 999 }

/-! ## Executable witnesses -/

theorem decimalDenominatorIsRedditWitness :
    blockEnumeratorDenominator 1000 = 998001 := by
  native_decide

theorem decimalReplayStartsAt000 :
    replayLadder decimalThreeDigitPacket = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] := by
  native_decide

theorem decimalPacketPromotable :
    ladderPromotable decimalThreeDigitPacket = true := by
  native_decide

theorem byteThreePacketPromotable :
    ladderPromotable byteThreePacket = true := by
  native_decide

theorem tinyLadderNotPromotable :
    ladderPromotable tinyLadderPacket = false := by
  native_decide

theorem badBaseNotPromotable :
    ladderPromotable badBasePacket = false := by
  native_decide

/-- Any promoted packet is structurally valid. -/
theorem promotable_ladder_structurally_valid (p : LadderPacket) :
    ladderPromotable p = true -> ladderStructurallyValid p = true := by
  unfold ladderPromotable
  intro h
  cases hStruct : ladderStructurallyValid p
  · simp [hStruct] at h
  · simp

/-- Any promoted packet satisfies the byte law. -/
theorem promotable_ladder_satisfies_byte_law (p : LadderPacket) :
    ladderPromotable p = true -> ladderByteLawHolds p = true := by
  unfold ladderPromotable
  intro h
  cases hStruct : ladderStructurallyValid p
  · simp [hStruct] at h
  cases hBytes : ladderByteLawHolds p
  · simp [hStruct, hBytes] at h
  · simp

#eval blockEnumeratorDenominator 1000
#eval replayLadder decimalThreeDigitPacket
#eval ladderPromotable decimalThreeDigitPacket
#eval ladderPromotable tinyLadderPacket
#eval ladderPromotable badBasePacket

end Semantics.LadderLUT
