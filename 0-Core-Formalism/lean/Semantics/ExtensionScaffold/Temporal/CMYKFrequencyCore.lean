/-
  CMYKFrequencyCore.lean

  Pure Lean 4 version of a decode-cheap CMYK frequency chart.

  Goal:
    - Map 4 hex nibbles into 4 channel-local frequency bins
    - Keep everything total and free of proof placeholders
    - Provide both forward and inverse mappings
-/namespace Semantics.CMYKFrequencyCore

/-- Four channel banks. -/inductive Channel where
  | C
  | M
  | Y
  | K
  deriving Repr, DecidableEq, BEq

/-- Hex digit, represented as a natural number in [0,15]. -/structure HexNibble where
  val : Nat
  isValid : val < 16
  deriving Repr, DecidableEq

/-- Smart constructor from Nat. Returns none if out of range. -/def mkHexNibble? (n : Nat) : Option HexNibble :=
  if h : n < 16 then
    some ⟨n, h⟩
  else
    none

/-- Convert a valid nibble back to Nat. -/def HexNibble.toNat (h : HexNibble) : Nat := h.val

/-- Base frequency of each channel bank (Hz). -/def baseFreq : Channel → Nat
  | .C => 600
  | .M => 1200
  | .Y => 1800
  | .K => 2400

/-- Bin spacing inside each channel bank (Hz). -/def deltaFreq : Nat := 20

/-- Frequency for a given channel and hex nibble. -/def freq (ch : Channel) (h : HexNibble) : Nat :=
  baseFreq ch + deltaFreq * h.toNat

/-- A CMYK packet is exactly 4 hex nibbles, one per channel. -/structure Packet where
  c : HexNibble
  m : HexNibble
  y : HexNibble
  k : HexNibble
  deriving Repr, DecidableEq

/-- Frequency image of a packet. -/structure PacketFreq where
  cFreq : Nat
  mFreq : Nat
  yFreq : Nat
  kFreq : Nat
  deriving Repr, DecidableEq

/-- Encode a packet into its channel frequencies. -/def encodePacket (p : Packet) : PacketFreq :=
  { cFreq := freq .C p.c
  , mFreq := freq .M p.m
  , yFreq := freq .Y p.y
  , kFreq := freq .K p.k }

/-- Check whether a frequency belongs to a given channel bank. -/def inBank (ch : Channel) (f : Nat) : Bool :=
  let b := baseFreq ch
  let top := b + deltaFreq * 15
  b ≤ f && f ≤ top && ((f - b) % deltaFreq = 0)

/-- Decode a channel-local frequency back into a nibble, if valid. -/def decodeFreq? (ch : Channel) (f : Nat) : Option HexNibble :=
  let b := baseFreq ch
  if _h0 : b ≤ f then
    let d := f - b
    if _h1 : d % deltaFreq = 0 then
      let n := d / deltaFreq
      mkHexNibble? n
    else
      none
  else
    none

/-- Decode a full frequency packet back into a packet, if all channels are valid. -/def decodePacket? (pf : PacketFreq) : Option Packet := do
  let c ← decodeFreq? .C pf.cFreq
  let m ← decodeFreq? .M pf.mFreq
  let y ← decodeFreq? .Y pf.yFreq
  let k ← decodeFreq? .K pf.kFreq
  pure { c := c, m := m, y := y, k := k }

/-- Exact 16-bin table for one channel. -/def channelTable (ch : Channel) : List (Nat × Nat) :=
  (List.range 16).map (fun n => (n, baseFreq ch + deltaFreq * n))

/-- Explicit tables. -/def cTable : List (Nat × Nat) := channelTable .C
def mTable : List (Nat × Nat) := channelTable .M
def yTable : List (Nat × Nat) := channelTable .Y
def kTable : List (Nat × Nat) := channelTable .K

/-- Useful examples. -/def hex0 : HexNibble := ⟨0, by decide⟩
def hexA : HexNibble := ⟨10, by decide⟩
def hexF : HexNibble := ⟨15, by decide⟩

def examplePacket : Packet :=
  { c := ⟨1, by decide⟩
  , m := ⟨10, by decide⟩
  , y := ⟨3, by decide⟩
  , k := ⟨15, by decide⟩ }

#eval cTable
#eval mTable
#eval yTable
#eval kTable
#eval encodePacket examplePacket
#eval decodePacket? (encodePacket examplePacket)

/-
  Small theorems: no proof placeholders needed.
-/theorem freq_ge_base (ch : Channel) (h : HexNibble) :
    baseFreq ch ≤ freq ch h := by
  unfold freq
  omega

theorem freq_le_top (ch : Channel) (h : HexNibble) :
    freq ch h ≤ baseFreq ch + deltaFreq * 15 := by
  unfold freq deltaFreq
  have hh : h.toNat ≤ 15 := Nat.le_of_lt_succ h.isValid
  omega

/-- Decoding the encoding of a nibble returns that nibble. -/theorem decodeFreq_encodeFreq (ch : Channel) (h : HexNibble) :
    decodeFreq? ch (freq ch h) = some h := by
  unfold decodeFreq? freq mkHexNibble?
  simp [HexNibble.toNat, baseFreq, deltaFreq]
  have hmod : (20 * h.toNat) % 20 = 0 := by
    simp
  simp
  have hdiv : (20 * h.toNat) / 20 = h.toNat := by
    omega
  simp [h.isValid]

/-- Decoding an encoded packet returns the original packet. -/theorem decodePacket_encodePacket (p : Packet) :
    decodePacket? (encodePacket p) = some p := by
  unfold decodePacket? encodePacket
  simp [decodeFreq_encodeFreq]

end Semantics.CMYKFrequencyCore
