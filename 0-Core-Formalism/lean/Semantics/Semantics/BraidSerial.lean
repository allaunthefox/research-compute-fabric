/-
BraidSerial.lean - Braid-Encoded Serial Communication

This module keeps the serial-transport surface small enough to compile and
extract. Bytes are carried explicitly at the strand boundary, while the braid
phase/bracket fields provide the local receipt used by downstream transport
checks. The phase projection is fixed-point-only; it does not decide decode
semantics.
-/

import Semantics.BraidBracket
import Semantics.FixedPoint

set_option linter.dupNamespace false

namespace Semantics.BraidSerial

open Semantics.BraidBracket

/-- Serial packet header: finite transport metadata. -/
structure PacketHeader where
  packetType : UInt8
  seqNum     : UInt16
  length     : UInt8
deriving Repr, DecidableEq, BEq

/-- Packet payload as a byte list at the shim boundary. -/
structure PacketPayload where
  bytes : List UInt8
deriving Repr, DecidableEq, BEq

namespace PacketPayload

/-- Empty payload. -/
def empty : PacketPayload :=
  { bytes := [] }

/-- Create payload from bytes. -/
def fromBytes (bytes : List UInt8) : PacketPayload :=
  { bytes := bytes }

/-- Payload length. -/
def length (p : PacketPayload) : Nat :=
  p.bytes.length

end PacketPayload

/-- Complete serial packet with the braid receipt from its frame. -/
structure SerialPacket where
  header   : PacketHeader
  payload  : PacketPayload
  bracket  : BraidBracket
  residual : Q16_16
deriving Repr, DecidableEq, BEq

namespace SerialPacket

/-- Empty packet used for fail-closed decode. -/
def empty : SerialPacket :=
  { header := { packetType := 0, seqNum := 0, length := 0 }
  , payload := PacketPayload.empty
  , bracket := BraidBracket.zero
  , residual := Q16_16.zero }

end SerialPacket

/-- One encoded byte plus its braid receipt. -/
structure EncodedStrand where
  rawByte  : UInt8
  phaseAcc : Q0_16
  slot     : UInt8
  parity   : Bool
  residue  : Q0_16
  bracket  : BraidBracket
deriving Repr, DecidableEq, BEq

/-- Complete braid frame. Eight strands match the hardware byte lane count. -/
structure BraidFrame where
  strands  : List EncodedStrand
  frameNum : UInt32
  phiPhase : Q16_16
deriving Repr, DecidableEq, BEq

namespace BraidFrame

/-- Maximum number of parallel byte lanes. -/
def maxWires : Nat := 8

/-- Structural frame check. -/
def validWireCount (f : BraidFrame) : Bool :=
  f.strands.length == maxWires

end BraidFrame

/-- Finite modulation selector. -/
inductive ModulationMode where
  | direct
  | qpsk
  | qam16
  | dmt
deriving Repr, DecidableEq, BEq

/-- Bound a natural into the byte interval. -/
def byteOfNat (n : Nat) : UInt8 :=
  UInt8.ofNat (n % 256)

/-- Boundary fixed-point projection used for receipts, not for decode. -/
def byteToPhase (b : UInt8) : Q0_16 :=
  ⟨UInt16.ofNat (b.toNat * 257)⟩

/-- A deterministic lossy phase inspection helper for diagnostics. -/
def phaseBucket (q : Q0_16) : UInt8 :=
  UInt8.ofNat (q.val.toNat / 257)

/-- Convert a lane slot into the Q16.16 coordinate used by the bracket shell. -/
def slotScalar (slot : UInt8) : Q16_16 :=
  Q16_16.ofNat slot.toNat

/-- Convert a byte into a one-dimensional phase vector for bracket receipts. -/
def bytePhaseVec (b : UInt8) : PhaseVec :=
  { x := Q16_16.ofRatio b.toNat 255
  , y := Q16_16.zero }

/-- Header serialization is fixed-width and byte-oriented. -/
def headerBytes (h : PacketHeader) : List UInt8 :=
  [ h.packetType
  , byteOfNat h.seqNum.toNat
  , byteOfNat (h.seqNum.toNat / 256)
  , h.length ]

/-- Packet bytes are header followed by payload. -/
def packetBytes (pkt : SerialPacket) : List UInt8 :=
  headerBytes pkt.header ++ pkt.payload.bytes

/-- Right-pad or truncate to the hardware lane count. -/
def laneBytes (bytes : List UInt8) : List UInt8 :=
  (bytes ++ List.replicate BraidFrame.maxWires 0).take BraidFrame.maxWires

/-- Read a byte from a list, failing closed to zero when absent. -/
def byteAt (bytes : List UInt8) (idx : Nat) : UInt8 :=
  (bytes[idx]?).getD 0

/-- Decode a fixed-width header from frame bytes. -/
def decodeHeader (bytes : List UInt8) : PacketHeader :=
  { packetType := byteAt bytes 0
  , seqNum := UInt16.ofNat ((byteAt bytes 2).toNat * 256 + (byteAt bytes 1).toNat)
  , length := byteAt bytes 3 }

/-- Select the payload bytes allowed by the decoded header. -/
def decodePayload (bytes : List UInt8) (h : PacketHeader) : PacketPayload :=
  PacketPayload.fromBytes ((bytes.drop 4).take h.length.toNat)

/-- Make a single encoded strand. -/
def encodeStrand (frameNum : UInt32) (slot : Nat) (byte : UInt8) : EncodedStrand :=
  let slotByte := byteOfNat slot
  let bracket := BraidBracket.fromPhaseVec (bytePhaseVec byte) (slotScalar slotByte)
  { rawByte := byte
  , phaseAcc := byteToPhase byte
  , slot := slotByte
  , parity := frameNum.toNat % 2 == 0
  , residue := Q0_16.zero
  , bracket := bracket }

/-- Encode lane bytes with stable slot indices. -/
def encodeStrands (frameNum : UInt32) (bytes : List UInt8) : List EncodedStrand :=
  let rec go (slot : Nat) : List UInt8 → List EncodedStrand
    | [] => []
    | byte :: rest => encodeStrand frameNum slot byte :: go (slot + 1) rest
  go 0 bytes

/-- Encode a serial packet into one braid frame. -/
def encodePacket (pkt : SerialPacket) (frameNum : UInt32) : BraidFrame :=
  let bytes := laneBytes (packetBytes pkt)
  let strands := encodeStrands frameNum bytes
  { strands := strands
  , frameNum := frameNum
  , phiPhase := Q16_16.ofRatio frameNum.toNat 100 }

/-- Decode a braid frame. Invalid lane counts fail closed. -/
def decodeFrame (frame : BraidFrame) : SerialPacket × Bool :=
  if !frame.validWireCount then
    (SerialPacket.empty, false)
  else
    let bytes := frame.strands.map (fun strand => strand.rawByte)
    let header := decodeHeader bytes
    let payload := decodePayload bytes header
    let allAdmissible := frame.strands.all (fun strand =>
      strand.bracket.admissible && BraidBracket.gapConserved strand.bracket)
    let receipt := (frame.strands.head?).map (fun strand => strand.bracket) |>.getD BraidBracket.zero
    ({ header := header
     , payload := payload
     , bracket := receipt
     , residual := Q16_16.zero }, allAdmissible)

/-- Modulation is represented as a finite receipt tag; byte semantics stay exact. -/
structure ModulationCodec where
  mode : ModulationMode
deriving Repr, DecidableEq, BEq

namespace ModulationCodec

/-- Encode under a modulation tag. The tag is metadata; it does not rewrite bytes. -/
def encodePacket (_codec : ModulationCodec) (pkt : SerialPacket) (frameNum : UInt32) : BraidFrame :=
  BraidSerial.encodePacket pkt frameNum

/-- Decode under a modulation tag. Invalid frames still fail closed. -/
def decodeFrame (_codec : ModulationCodec) (frame : BraidFrame) : SerialPacket × Bool :=
  BraidSerial.decodeFrame frame

end ModulationCodec

/-- Small packet with four payload bytes so the entire packet fits in one frame. -/
def witnessPacket : SerialPacket :=
  { header := { packetType := 7, seqNum := 513, length := 4 }
  , payload := PacketPayload.fromBytes [10, 20, 30, 40]
  , bracket := BraidBracket.zero
  , residual := Q16_16.zero }

/-- Header preservation witness for the one-frame envelope. -/
theorem witnessRoundtripHeader :
  (decodeFrame (encodePacket witnessPacket 12)).1.header = witnessPacket.header := by
  native_decide

/-- Payload preservation witness for the one-frame envelope. -/
theorem witnessRoundtripPayload :
  (decodeFrame (encodePacket witnessPacket 12)).1.payload = witnessPacket.payload := by
  native_decide

/-- Fail-closed witness for frames with the wrong lane count. -/
theorem invalidFrameRejected :
  (decodeFrame { strands := [], frameNum := 0, phiPhase := Q16_16.zero }).2 = false := by
  native_decide

/-- Direct codec preserves the one-frame packet's user-visible bytes. -/
theorem directCodecRoundtripBytes :
  let codec : ModulationCodec := { mode := ModulationMode.direct }
  let decoded := (ModulationCodec.decodeFrame codec (ModulationCodec.encodePacket codec witnessPacket 12)).1
  decoded.header = witnessPacket.header ∧ decoded.payload = witnessPacket.payload := by
  native_decide

#eval BraidFrame.validWireCount (encodePacket witnessPacket 12)
#eval (decodeFrame (encodePacket witnessPacket 12)).1.header.packetType
#eval (decodeFrame (encodePacket witnessPacket 12)).1.payload.bytes.length
#eval (decodeFrame { strands := [], frameNum := 0, phiPhase := Q16_16.zero }).2

-- ═══════════════════════════════════════════════════════════════════════════
-- Boundedness Theorems (prevent silent truncation)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Maximum serialized bytes that fit in one braid frame (8 lanes). -/
def maxFrameBytes : Nat := BraidFrame.maxWires

/-- Header serializes to exactly 4 bytes (fixed-width). -/
theorem headerBytes_length (h : PacketHeader) : (headerBytes h).length = 4 := by
  unfold headerBytes
  simp

/--
Upper bound on serialized packet size: header (4) + payload length.
Used to prove that small packets fit in one frame without truncation.
-/
theorem packetBytes_length_bound (pkt : SerialPacket) :
    (packetBytes pkt).length ≤ 4 + pkt.payload.bytes.length := by
  unfold packetBytes
  simp

/--
A packet fits in one frame iff its serialized bytes ≤ maxFrameBytes.
Truncation via laneBytes is explicit but silent; this predicate detects it.
-/
def packetFitsOneFrame (pkt : SerialPacket) : Bool :=
  (packetBytes pkt).length ≤ maxFrameBytes

/--
The witness packet (4 header bytes + 4 payload bytes = 8 bytes) fits
in exactly one braid frame with zero truncation.
-/
theorem PacketFitsOneFrame : packetFitsOneFrame witnessPacket := by
  unfold packetFitsOneFrame witnessPacket
  unfold packetBytes headerBytes
  native_decide

/--
One-frame envelope is lossless: the decoded payload length equals the
original payload length when the packet fits.
-/
theorem oneFramePayloadPreserved :
  let decoded := (decodeFrame (encodePacket witnessPacket 12)).1
  decoded.payload.bytes.length = witnessPacket.payload.bytes.length := by
  native_decide

end Semantics.BraidSerial
