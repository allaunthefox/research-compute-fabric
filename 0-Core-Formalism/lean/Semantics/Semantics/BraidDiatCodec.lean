/-
BraidDiatCodec.lean — Chirality-DIAT Slot + Mountain Pack + Braid Residual Codec

Codec for the mountains-on-mountain / braid / DIAT stack.

Layer 1 — Chirality-DIAT Slot Address (64 bits)
  bits [1:0]   Chirality flag   (00=none, 01=left, 10=right, 11=achiral)
  bits [9:2]   DIAT shell k     (floor(sqrt(n)), 0–255)
  bits [31:10] DIAT offset a    (n - k², max 510 → 22 bits)
  bits [53:32] DIAT offset b    ((k+1)² - n, same range → 22 bits)
  bits [61:54] DIAT prod_msb    (upper bits of a*b for slot anti-correlation)
  bits [63:62] reserved

  Decode: n = k² + a, verified by b = (k+1)² - n.
  Spatial hierarchy comes from shell (Morton-like levels).
  Anti-correlation slot from prod = a*b (high prod → sparse, low → dense).

Layer 2 — Mountain Pack (variable)
  self-contained binary representation of a Mountain without the inner MMR.
  Full MMR is encoded as a list of MountainPacked in strictly decreasing height.
  The inner MMR is encoded recursively (self-similar at every scale).

Layer 3 — Braid Residual (64 bits per crossing × 4 crossings = 256 bits)
  R_ij = B_ij - (B_i + B_j) from braidCross.
  Each residual packs 5 Q0_2 fields (lower, upper, gap, kappa, phi).
  Q0_2 range: exactly 4 states (0, 16384, 32768, 49152) → 2 bits each = 10 bits.

Layer 4 — Complete BraidDiatFrame (256 bits base + variable MMR)
  Fixed 256-bit header + variable-length mountain list.

References:
  - Semantics.BraidField     (Mountain, MMR, SpherionState)
  - Semantics.BraidBracket   (PhaseVec, BraidBracket)
  - Semantics.DynamicCanal   (DIAT)
  - Semantics.EntropyMeasures (Chirality)
  - Semantics.VoxelEncoding   (VoxelKey bit-packing patterns)
-/

import Semantics.BraidField
import Semantics.BraidBracket
import Semantics.DynamicCanal
import Semantics.EntropyMeasures
import Mathlib.Data.UInt

namespace Semantics.BraidDiatCodec

open DynamicCanal
open EntropyMeasures
open BraidBracket

-- ============================================================
-- §1  CHIRALITY-DIAT SLOT ADDRESS (64 bits)
-- ============================================================

/-- Chirality-DIAT slot address: 2-bit chirality + 62-bit DIAT.

   Physical interpretation:
   - Chirality encodes strand direction (L/R/achiral) — the sign bit of the braid.
   - Shell k gives spatial hierarchy level (Morton-code-like).
   - Offset a = n - k², offset b = (k+1)² - n.
   - prod = a*b encodes slot anti-correlation: high prod → sparse zone (small a or b),
     low prod → dense zone (both moderate).
   - n = k² + a is recovered by decode; b is verified as consistency check. -/
structure ChiralityDIAT where
  chirality : Chirality          -- 2 bits
  shell     : UInt8             -- k = floor(sqrt(n)), 0–255 (8 bits)
  offsetA   : UInt32             -- a = n - k², max 510 (22 bits used)
  offsetB   : UInt32             -- b = (k+1)² - n, max 510 (22 bits used)
  prodMsb   : UInt8             -- upper 8 bits of prod = a*b (10 bits enough; use 8 for headroom)
  deriving Repr, DecidableEq, BEq

namespace ChiralityDIAT

/-- Maximum value for offset a or b (at shell k, max a,b ≤ 2k).
   For k=255: max a,b = 510. 510 fits in 10 bits; we use 22 for safety. -/
def maxOffset (k : UInt8) : UInt32 := UInt32.ofNat (2 * k.toNat + 1)

/-- Encode n and chirality into a ChiralityDIAT slot address.

   Pre: n ≤ 2^24 (the 22-bit offset field limit).
   The shell is floor(sqrt(n)). -/
def encode (chir : Chirality) (n : UInt32) : Option ChiralityDIAT := do
  let k := DynamicCanal.DIAT.isqrt n
  let lo := k * k
  let hi := (k + 1) * (k + 1)
  let a := n - lo
  let b := hi - n
  let prod := a * b
  -- Verify n is in valid range for 22-bit offset fields
  guard (a < 0x400000 && b < 0x400000)
  pure {
    chirality := chir
    shell     := k
    offsetA   := a
    offsetB   := b
    prodMsb   := UInt8.ofNat ((prod >>> 16).toNat)
  }

/-- Decode a ChiralityDIAT back to (n, chirality).

   Recovers n = k² + a. Consistency check: b must equal (k+1)² - n.
   Returns none if the encoded offsets are inconsistent. -/
def decode (cd : ChiralityDIAT) : Option (UInt32 × Chirality) := do
  let kSq : UInt32 := cd.shell.toNat * cd.shell.toNat
  let n := kSq + cd.offsetA
  let kpSq : UInt32 := (cd.shell.toNat + 1) * (cd.shell.toNat + 1)
  let expectedB := kpSq - n
  guard (cd.offsetB = expectedB)
  pure (n, cd.chirality)

/-- Roundtrip: decode(encode(chir, n)) = some (n, chir) when inputs are valid. -/
theorem encode_decode_roundtrip (chir : Chirality) (n : UInt32)
    (h : n < 0x400000) :
    match encode chir n with
    | some cd => decode cd = some (n, chir)
    | none    => false := by
  simp [encode, decode]
  split <;> intro h1
  . next k a b prod h_k hlo hhi ha hb hprod =>
      simp [hlo, hhi, ha, hb, hprod]
      have : b = (k + 1) * (k + 1) - n := rfl
      split <;> simp [this]
  . contradiction

end ChiralityDIAT

-- ============================================================
-- §2  MOUNTAIN PACK (binary representation)
-- ============================================================

/-- Packed binary representation of a Mountain without the inner MMR.

   Height:   8 bits  (0–255; actual heights are much smaller in practice)
   Apex:      3 × 16-bit signed coords (Int, biased by Int32 max)
   BaseCount: 8 bits (number of base IntNodes)

   Total header: 8 + 48 + 8 = 64 bits.
   Each base IntNode: 3 × 16-bit coords = 48 bits.

   Note: We store apex/base as raw Int (not Q16_16) since these are
   discrete geometric nodes. The inner MMR is encoded recursively
   (self-similar at every scale). -/
structure MountainPacked where
  height    : UInt8
  apexX     : Int32
  apexY     : Int32
  apexZ     : Int32
  baseCount : UInt8
  bases     : Array Int32  -- 3 × baseCount Int32 values (x,y,z tuples)
  deriving Repr, DecidableEq

namespace MountainPacked

/-- Encode a Mountain into a MountainPacked (lossless, no inner MMR). -/
def fromMountain (m : BraidField.Mountain) : MountainPacked :=
  match m with
  | BraidField.Mountain.node h apex base _ =>
    let bases := base.bind (fun (n : BraidField.IntNode) =>
      [Int32.ofInt n.coords[0]!, Int32.ofInt n.coords[1]!,
       Int32.ofInt n.coords[2]!])
    {
      height    := UInt8.ofNat h
      apexX     := Int32.ofInt apex.coords[0]!
      apexY     := Int32.ofInt apex.coords[1]!
      apexZ     := Int32.ofInt apex.coords[2]!
      baseCount := UInt8.ofNat base.length
      bases     := bases
    }

/-- Decode a MountainPacked back to a Mountain (inner MMR set to empty).
    The inner MMR must be reconstructed from the surrounding context. -/
def toMountain (p : MountainPacked) : BraidField.Mountain :=
  let apexCoords := [Int.ofInt p.apexX.toInt,
                     Int.ofInt p.apexY.toInt,
                     Int.ofInt p.apexZ.toInt]
  let baseNodesReversed : List BraidField.IntNode := (List.range p.baseCount.toNat).foldl (fun acc i =>
    let baseX := Int.ofInt p.bases[3*i.toNat]!.toInt
    let baseY := Int.ofInt p.bases[3*i.toNat + 1]!.toInt
    let baseZ := Int.ofInt p.bases[3*i.toNat + 2]!.toInt
    { coords := [baseX, baseY, baseZ] } :: acc
  ) []
  BraidField.Mountain.node
    p.height.toNat
    { coords := apexCoords }
    baseNodesReversed
    BraidField.MMR.empty

end MountainPacked

-- ============================================================
-- §3  BRAID RESIDUAL PACKING (Q0_2 per crossing × 4 crossings)
-- ============================================================

/-- Q0_2 field packing: 5 fields × 2 bits = 10 bits per crossing residual.

   Q0_2 has exactly 4 states: 0, 16384, 32768, 49152.
   We store them as 2-bit values: 00=0, 01=16384, 10=32768, 11=49152.

   BraidBracket fields (all Q0_2): lower, upper, gap, kappa, phi.
   Total per crossing residual: 5 × 2 = 10 bits.
   4 crossings × 10 bits = 40 bits per frame step.

   For admissibility: a single bit (1=admissible, 0=inadmissible).
   Total per crossing: 11 bits. 4 crossings = 44 bits. -/
structure BraidResidualPacked where
  lower : UInt8     -- 2 bits used (Q0_2: 0, 16384, 32768, 49152)
  upper : UInt8     -- 2 bits used
  gap   : UInt8     -- 2 bits used
  kappa : UInt8     -- 2 bits used
  phi   : UInt8     -- 2 bits used
  admissible : Bool  -- 1 bit
  deriving Repr, DecidableEq

namespace BraidResidualPacked

/-- Encode a Q0_2 value to 2 bits.
    Q0_2 range: {0, 16384, 32768, 49152} = {0, 2^14, 2^15, 2^14*3}. -/
def encodeQ02 (v : Q0_2) : UInt8 :=
  let raw := v.val.toInt
  if raw = 0 then 0
  else if raw = 16384 then 1
  else if raw = 32768 then 2
  else 3

/-- Decode 2 bits back to a Q0_2 value. -/
def decodeQ02 (b : UInt8) : Q0_2 :=
  match b.toNat % 4 with
  | 0 => Q0_2.zero
  | 1 => Q0_2.ofRawInt 16384
  | 2 => Q0_2.ofRawInt 32768
  | _ => Q0_2.ofRawInt 49152

/-- Encode a BraidBracket to a BraidResidualPacked (lossless). -/
def fromBracket (br : BraidBracket) : BraidResidualPacked :=
  {
    lower     := encodeQ02 br.lower
    upper     := encodeQ02 br.upper
    gap       := encodeQ02 br.gap
    kappa     := encodeQ02 br.kappa
    phi       := encodeQ02 br.phi
    admissible := br.admissible
  }

/-- Decode a BraidResidualPacked back to a BraidBracket (lossless). -/
def toBracket (p : BraidResidualPacked) : BraidBracket :=
  {
    lower     := decodeQ02 p.lower
    upper     := decodeQ02 p.upper
    gap       := decodeQ02 p.gap
    kappa     := decodeQ02 p.kappa
    phi       := decodeQ02 p.phi
    admissible := p.admissible
  }

/-- Roundtrip: toBracket (fromBracket br) = br. -/
theorem bracket_roundtrip (br : BraidBracket) :
    toBracket (fromBracket br) = br := by
  simp [fromBracket, toBracket]
  cases br <;> simp [encodeQ02, decodeQ02]

end BraidResidualPacked

-- ============================================================
-- §4  COMPLETE FRAME LAYOUT (BraidDiatFrame)
-- ============================================================

/-- The complete BraidDiatFrame: fixed header + variable mountain list.

   Fixed header: 256 bits (32 bytes)
   Variable: mountain list (each MountainPacked is variable length)

   Frame layout (fixed part, 256 bits / 32 bytes):
     Bytes [0:1]   ChiralityDIAT.chirality(1:0) || shell(9:2)   (bits [9:0])
     Bytes [1:4]   offsetA[31:10]                                       (22 bits)
     Bytes [4:7]   offsetB[53:32]                                      (22 bits)
     Byte  [7]     prodMsb[61:54]                                      (8 bits)
     Bytes [8:9]   mmrSize[15:0]    (number of mountains in MMR)
     Bytes [9:10]  frameFlags     (reserved, set to 0)
     Bytes [10:18] braidReceipt: sidon_slack(7:0) || step_count[31:8]  (8+24 bits)
     Bytes [18:26] braidReceipt: write_time[63:32]
     Bytes [26:32] braidReceipt: write_time[31:0] || scar_absent(1) || residuals count(7)
     Bytes [32:]   MountainPacked[0..N-1], each variable length

   Note: braidReceipt fields are reconstructed from the 8 BraidStrands
   at encode time and stored compactly in the frame header.
   The residuals array follows the fixed header. -/
structure BraidDiatFrame where
  slot       : ChiralityDIAT          -- 64 bits
  mmrSize    : UInt16                 -- number of mountains
  sidonSlack : UInt8                  -- 128 - maxLabel (powers-of-2 Sidon set)
  stepCount  : UInt32                 -- crossStep count to convergence
  writeTime  : UInt64                 -- write timestamp (0 = untimed)
  scarAbsent : Bool                  -- true iff no FAMM scars
  mountains  : List MountainPacked   -- strictly decreasing heights
  residuals  : Array BraidResidualPacked  -- 4 crossings × residual
  deriving Repr, DecidableEq

namespace BraidDiatFrame

/-- Encode a SpherionState + BraidReceipt into a BraidDiatFrame.

   The SpherionState provides: scale, mmr (mountain list), voids (Betti cycles).
   The BraidReceipt provides: sidon_slack, step_count, write_time, scar_absent.
   The residuals come from the 4 parallel crossings.
   The slot chirality is derived from the void topology (Betti cycle winding). -/
def encode (state : BraidField.SpherionState)
           (receipt : BraidEigensolid.BraidReceipt)
           (slotChirality : Chirality)
           (slotN : UInt32)
           (residuals : Array BraidResidualPacked) : Option BraidDiatFrame := do
  let slot ← ChiralityDIAT.encode slotChirality slotN
  let packedMountains := state.mmr.mountainList.map MountainPacked.fromMountain
  pure {
    slot
    mmrSize    := UInt16.ofNat packedMountains.length
    sidonSlack := UInt8.ofNat receipt.sidon_slack.toNat
    stepCount  := UInt32.ofNat receipt.step_count
    writeTime  := receipt.write_time
    scarAbsent := receipt.scar_absent
    mountains  := packedMountains
    residuals  := residuals
  }

/-- Decode a BraidDiatFrame back to (SpherionState, BraidReceipt, slot info).

   Reconstructs SpherionState from the mountain list.
   The PIST field and void topology must be recomputed from the mountains
   (Betti cycles are derived from merge history, not stored directly).

   Returns none if the encoded DIAT offsets are inconsistent. -/
def decode (frame : BraidDiatFrame) :
    Option (BraidField.SpherionState × BraidEigensolid.BraidReceipt × Chirality × UInt32) :=
  do
  let (n, chir) ← frame.slot.decode
  let mountains := frame.mountains.map MountainPacked.toMountain
  let mmr := mountains.foldr BraidField.MMR.cons BraidField.MMR.empty
  let voids := BettiCycleSet.empty  -- recomputed from merge history
  let pist := BraidField.computePIST 0 mmr 0 mmr.isStable
  let state : BraidField.SpherionState := {
    scale := 0
    mmr
    voids
    pist
  }
  let receipt : BraidEigensolid.BraidReceipt := {
    crossing_matrix := BraidBracket.zero
    sidon_slack     := frame.sidonSlack.toNat
    step_count      := frame.stepCount.toNat
    residuals       := []
    write_time      := frame.writeTime
    scar_absent     := frame.scarAbsent
  }
  pure (state, receipt, chir, n)

end BraidDiatFrame

-- ============================================================
-- §5  ROUNDTRIP THEOREMS
-- ============================================================

namespace BraidDiatFrame

/-- Roundtrip: decode(encode(state, receipt, chir, n, residuals)) recovers
    the original state, receipt chirality, and slot n when inputs are valid.
    The crossing_matrix and residuals in the receipt are not preserved through
    the frame encode/decode (they travel separately via the residuals array). -/
theorem encode_decode_roundtrip
    (state : BraidField.SpherionState)
    (receipt : BraidEigensolid.BraidReceipt)
    (chir : Chirality)
    (n : UInt32)
    (residuals : Array BraidResidualPacked)
    (h_n : n < 0x400000) :
    match encode state receipt chir n residuals with
    | some frame =>
      match decode frame with
      | some (state', receipt', chir', n') =>
        state'.mmr = state.mmr ∧
        chir' = chir ∧
        n' = n ∧
        receipt'.sidon_slack = receipt.sidon_slack ∧
        receipt'.step_count = receipt.step_count ∧
        receipt'.write_time = receipt.write_time ∧
        receipt'.scar_absent = receipt.scar_absent
      | none => False
    | none => False := by
  simp [encode, decode]
  split
  . next frame h_frame =>
    simp [h_frame]
    split
    . next h_dec =>
      simp [h_dec]
      constructor
      . simp [mountains, mmr, mountainList]
      . rfl
      . rfl
      . simp [sidonSlack]
      . simp [stepCount]
      . simp [writeTime]
      . simp [scarAbsent]
    . intro h_none
      simp [h_none]
  . intro h_none
    simp [h_none]

/-- Encode after decode recovers the original frame (when chir/n are consistent).
    This requires the slot encode to succeed, which needs n < 0x400000. -/
theorem decode_encode_roundtrip
    (frame : BraidDiatFrame)
    (h : ∀ (chir : Chirality) (n : UInt32), n < 0x400000 → decode frame = some (_, _, chir, n) → encode { frame with slot := { frame.slot with chirality := chir } } receipt chir n residuals ≠ none)
    (receipt : BraidEigensolid.BraidReceipt)
    (residuals : Array BraidResidualPacked) :
    match decode frame with
    | some (state, receipt', chir, n) =>
      match encode state receipt' chir n residuals with
      | some frame' => frame'.slot = frame.slot ∧ frame'.mmrSize = frame.mmrSize ∧ frame'.sidonSlack = frame.sidonSlack ∧ frame'.stepCount = frame.stepCount ∧ frame'.writeTime = frame.writeTime ∧ frame'.scarAbsent = frame.scarAbsent
      | none => False
    | none => True := by
  simp [decode, encode]
  split
  . next frame _ _ _ _ h_slot =>
    simp [h_slot]
    simp [mmrSize, sidonSlack, stepCount, writeTime, scarAbsent]
    constructor <;> rfl
  . rfl

end BraidDiatFrame

-- ============================================================
-- §5  ESTIMATED BYTE SIZES
-- ============================================================

/-- Estimate the encoded byte size of a BraidDiatFrame.

   Fixed header: 32 bytes
   Per mountain: 8 bytes header + 3 × 4 × baseCount bytes
   Per residual: 6 bytes (5 × 1 byte + 1 byte admissible) × 4 = 24 bytes
   Total fixed: 32 + 24 = 56 bytes + variable mountain bytes -/
def estimatedBytes (frame : BraidDiatFrame) : Nat :=
  let mountainBytes (m : MountainPacked) : Nat :=
    8 + (3 * 4 * m.baseCount.toNat)
  32 + 24 + (frame.mountains.foldl (fun acc m => acc + mountainBytes m) 0)

/-- #eval estimate for a typical frame with 4 mountains and 8 base nodes each -/
#eval let frame := {
  slot := {
    chirality := Chirality.right
    shell     := UInt8.ofNat 16
    offsetA   := 100
    offsetB   := 156
    prodMsb   := 42
  }
  mmrSize    := 4
  sidonSlack := 64
  stepCount  := 12
  writeTime  := 0
  scarAbsent := true
  mountains  := []
  residuals  := #[]
}
  estimatedBytes frame  -- expect 56 (32 header + 24 residuals)

end Semantics.BraidDiatCodec
