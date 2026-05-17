/-
GoxelGridBus.lean - Goxel grid state machines over an internal serial bus

This module makes the goxel workbench idea executable: a goxel field is a
series of finite grid-local state machines, and cells communicate by addressed
packets carried through the existing braid serial transport surface.
-/

import Semantics.BraidSerial

set_option linter.dupNamespace false

namespace Semantics.GoxelGridBus

open Semantics.BraidSerial
open Semantics.FixedPoint

/-- Local finite phase of one goxel cell. -/
inductive GoxelPhase where
  | empty
  | idle
  | active
  | settled
  | hold
deriving Repr, DecidableEq, BEq

/-- Finite bus commands. -/
inductive GoxelCommand where
  | ping
  | activate
  | settle
  | hold
deriving Repr, DecidableEq, BEq

namespace GoxelCommand

def toByte : GoxelCommand → UInt8
  | ping => 0
  | activate => 1
  | settle => 2
  | hold => 3

def ofByte (b : UInt8) : GoxelCommand :=
  match b.toNat with
  | 1 => activate
  | 2 => settle
  | 3 => hold
  | _ => ping

end GoxelCommand

/-- Bounded grid address. Values are byte-sized at the serial boundary. -/
structure GoxelAddr where
  row : UInt8
  col : UInt8
deriving Repr, DecidableEq, BEq

namespace GoxelAddr

def zero : GoxelAddr := { row := 0, col := 0 }

def seqNum (a : GoxelAddr) : UInt16 :=
  UInt16.ofNat (a.row.toNat * 256 + a.col.toNat)

def fromSeqNum (n : UInt16) : GoxelAddr :=
  { row := UInt8.ofNat (n.toNat / 256)
  , col := UInt8.ofNat (n.toNat % 256) }

end GoxelAddr

/-- One goxel-local grid state machine. -/
structure GoxelCell where
  addr : GoxelAddr
  phase : GoxelPhase
  scalar : Q16_16
  residual : Q16_16
  ticks : Nat
deriving Repr, DecidableEq, BEq

namespace GoxelCell

def empty (addr : GoxelAddr) : GoxelCell :=
  { addr := addr
  , phase := GoxelPhase.empty
  , scalar := Q16_16.zero
  , residual := Q16_16.zero
  , ticks := 0 }

def idle (addr : GoxelAddr) : GoxelCell :=
  { addr := addr
  , phase := GoxelPhase.idle
  , scalar := Q16_16.zero
  , residual := Q16_16.zero
  , ticks := 0 }

end GoxelCell

/-- Addressed packet on the internal bus. -/
structure GoxelBusPacket where
  source : GoxelAddr
  target : GoxelAddr
  command : GoxelCommand
  arg0 : UInt8
  arg1 : UInt8
deriving Repr, DecidableEq, BEq

namespace GoxelBusPacket

/-- Encode into one braid serial packet. Payload is exactly four bytes. -/
def toSerialPacket (p : GoxelBusPacket) : SerialPacket :=
  { header := { packetType := p.command.toByte, seqNum := p.source.seqNum, length := 4 }
  , payload := PacketPayload.fromBytes [p.target.row, p.target.col, p.arg0, p.arg1]
  , bracket := BraidBracket.BraidBracket.zero
  , residual := Q16_16.zero }

def byteAt (bytes : List UInt8) (idx : Nat) : UInt8 :=
  (bytes[idx]?).getD 0

/-- Decode from one braid serial packet. Missing payload bytes fail closed to 0. -/
def fromSerialPacket (pkt : SerialPacket) : GoxelBusPacket :=
  { source := GoxelAddr.fromSeqNum pkt.header.seqNum
  , target := { row := byteAt pkt.payload.bytes 0, col := byteAt pkt.payload.bytes 1 }
  , command := GoxelCommand.ofByte pkt.header.packetType
  , arg0 := byteAt pkt.payload.bytes 2
  , arg1 := byteAt pkt.payload.bytes 3 }

def encodeFrame (p : GoxelBusPacket) (frameNum : UInt32) : BraidFrame :=
  encodePacket p.toSerialPacket frameNum

def decodeFrame (frame : BraidFrame) : GoxelBusPacket × Bool :=
  let decoded := BraidSerial.decodeFrame frame
  (fromSerialPacket decoded.1, decoded.2)

end GoxelBusPacket

/-- Apply a command to one cell. -/
def applyCommand (cell : GoxelCell) (cmd : GoxelCommand) (arg0 arg1 : UInt8) : GoxelCell :=
  let nextTicks := cell.ticks + 1
  match cmd with
  | GoxelCommand.ping =>
      { cell with ticks := nextTicks }
  | GoxelCommand.activate =>
      { cell with
        phase := GoxelPhase.active
        scalar := Q16_16.ofRatio arg0.toNat 255
        residual := Q16_16.ofRatio arg1.toNat 255
        ticks := nextTicks }
  | GoxelCommand.settle =>
      { cell with phase := GoxelPhase.settled, ticks := nextTicks }
  | GoxelCommand.hold =>
      { cell with phase := GoxelPhase.hold, ticks := nextTicks }

/--
One local bus step. Addressed packets are consumed by the matching cell;
non-addressed packets are forwarded unchanged.
-/
def cellBusStep (cell : GoxelCell) (pkt : GoxelBusPacket) : GoxelCell × Option GoxelBusPacket :=
  if cell.addr == pkt.target then
    (applyCommand cell pkt.command pkt.arg0 pkt.arg1, none)
  else
    (cell, some pkt)

/-- A serial goxel grid is stored row-major. -/
structure GoxelGrid where
  rows : Nat
  cols : Nat
  cells : List GoxelCell
deriving Repr, DecidableEq, BEq

namespace GoxelGrid

def addrOfIndex (cols idx : Nat) : GoxelAddr :=
  { row := UInt8.ofNat (idx / cols)
  , col := UInt8.ofNat (idx % cols) }

def mkIdle (rows cols : Nat) : GoxelGrid :=
  let count := rows * cols
  let cells := (List.range count).map (fun idx => GoxelCell.idle (addrOfIndex cols idx))
  { rows := rows, cols := cols, cells := cells }

def cellAt (g : GoxelGrid) (idx : Nat) : Option GoxelCell :=
  g.cells[idx]?

/-- Route one packet through the row-major serial bus. -/
def routePacket (g : GoxelGrid) (pkt : GoxelBusPacket) : GoxelGrid × Option GoxelBusPacket :=
  let rec go (current : GoxelBusPacket) : List GoxelCell → List GoxelCell × Option GoxelBusPacket
    | [] => ([], some current)
    | cell :: rest =>
        let stepped := cellBusStep cell current
        match stepped.2 with
        | none => (stepped.1 :: rest, none)
        | some forwarded =>
            let tail := go forwarded rest
            (stepped.1 :: tail.1, tail.2)
  let routed := go pkt g.cells
  ({ g with cells := routed.1 }, routed.2)

end GoxelGrid

/-- Sample addressed packet from cell (0,0) to cell (0,1). -/
def witnessActivatePacket : GoxelBusPacket :=
  { source := { row := 0, col := 0 }
  , target := { row := 0, col := 1 }
  , command := GoxelCommand.activate
  , arg0 := 128
  , arg1 := 7 }

/-- Encoding through the internal serial bus preserves the target address. -/
theorem serialRoundtripPreservesTarget :
  let decoded := (GoxelBusPacket.decodeFrame (GoxelBusPacket.encodeFrame witnessActivatePacket 4)).1
  decoded.target = witnessActivatePacket.target := by
  native_decide

/-- Encoding through the internal serial bus preserves the command. -/
theorem serialRoundtripPreservesCommand :
  let decoded := (GoxelBusPacket.decodeFrame (GoxelBusPacket.encodeFrame witnessActivatePacket 4)).1
  decoded.command = witnessActivatePacket.command := by
  native_decide

/-- A targeted packet activates the target cell and is consumed. -/
theorem targetedPacketActivatesAndConsumes :
  let routed := GoxelGrid.routePacket (GoxelGrid.mkIdle 1 2) witnessActivatePacket
  routed.2 = none ∧ (routed.1.cellAt 1).map (fun c => c.phase) = some GoxelPhase.active := by
  native_decide

/-- A packet with no matching address stays on the serial bus. -/
theorem unmatchedPacketForwards :
  let pkt : GoxelBusPacket :=
    { source := { row := 0, col := 0 }
    , target := { row := 9, col := 9 }
    , command := GoxelCommand.activate
    , arg0 := 1
    , arg1 := 0 }
  (GoxelGrid.routePacket (GoxelGrid.mkIdle 1 2) pkt).2 = some pkt := by
  native_decide

/-- HOLD is an explicit phase, not an implicit failure. -/
theorem holdCommandSetsHoldPhase :
  let pkt : GoxelBusPacket :=
    { source := { row := 0, col := 0 }
    , target := { row := 0, col := 0 }
    , command := GoxelCommand.hold
    , arg0 := 0
    , arg1 := 0 }
  let routed := GoxelGrid.routePacket (GoxelGrid.mkIdle 1 1) pkt
  (routed.1.cellAt 0).map (fun c => c.phase) = some GoxelPhase.hold := by
  native_decide

#eval (GoxelBusPacket.decodeFrame (GoxelBusPacket.encodeFrame witnessActivatePacket 4)).1.command
#eval (GoxelGrid.routePacket (GoxelGrid.mkIdle 1 2) witnessActivatePacket).2
#eval (GoxelGrid.routePacket (GoxelGrid.mkIdle 1 2) witnessActivatePacket).1.cellAt 1 |>.map (fun c => c.phase)

end Semantics.GoxelGridBus
