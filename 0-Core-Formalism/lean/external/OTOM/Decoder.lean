/-
Semantics/Decoder.lean - Model 141 Self-Instantiating Weird Machine

This module implements the OISC-SLUG3 engine as described in the N-Folded MMR 
Gossip EBML Schema. It executes 27 ternary opcodes while enforcing 
Integrability and Stability constraints from the simulation manifold.

Lean is the source of truth.
-/

import Semantics.SLUG3
import Semantics.Connectors
import Semantics.DynamicCanal
import Semantics.BraidBracket
import Semantics.ManifoldFlow

namespace Semantics.Decoder

open DynamicCanal
open Semantics.SLUG3
open Semantics.Connectors
open Semantics.BraidBracket
open Semantics.ManifoldFlow

/-- Machine State for Model 141 -/
structure MachineState where
  pc      : Nat
  stack   : List Fix16
  memory  : Array Fix16
  exhausted : Bool
  frustPrevX : BraidBracket.PhaseVec -- Hardware cache for P_{m-1}
  frustAniso : AnisotropyTensor      -- Hardware cache for A_ij

/-- Initial state with 1024 words of memory -/
def MachineState.init (initialMem : List Fix16) : MachineState :=
  { pc := 0
  , stack := []
  , memory := (initialMem ++ (List.replicate (1024 - initialMem.length) Fix16.zero)).toArray
  , exhausted := false
  , frustPrevX := BraidBracket.PhaseVec.zero
  , frustAniso := { xx := Fix16.zero, xy := Fix16.zero, yy := Fix16.zero } }

instance : Inhabited MachineState := ⟨MachineState.init []⟩

namespace Ports
  def ioIn        : Int := -1
  def ioOut       : Int := -2
  def frustPrevX  : Int := -23
  def frustAniso  : Int := -24
  def frustResult : Int := -25
end Ports

/-- Instruction format: 6 bytes 
    [Opcode (1) | OperandA (2) | OperandB (2) | Result (1)]
-/
structure Instruction where
  op   : OISCOp
  argA : Fix16
  argB : Fix16
  dest : Nat

/-- Native Port Reading Header -/
def MachineState.read (state : MachineState) (addr : Int) : Fix16 :=
  if addr >= 0 then
    if _hSize : 0 < state.memory.size then
      state.memory[addr.toNat % state.memory.size]!
    else
      Fix16.zero
  else match addr with
    | -25 => -- frustResult
      interlockingEnergy BraidBracket.PhaseVec.zero state.frustPrevX state.frustAniso
    | _ => Fix16.zero

/-- Native Port Writing Header -/
def MachineState.write (state : MachineState) (addr : Int) (val : Fix16) : MachineState :=
  if addr >= 0 then
    if _hSize : 0 < state.memory.size then
      let idx := addr.toNat % state.memory.size
      { state with memory := state.memory.set! idx val }
    else
      state
  else match addr with
    | -23 => { state with frustPrevX := { x := val, y := Fix16.zero : PhaseVec } }
    | -24 => { state with frustAniso := { xx := val, xy := Fix16.zero, yy := Fix16.zero } }
    | _ => state

def MachineState.pcUpdate (state : MachineState) (n : Nat) : MachineState :=
  { state with pc := state.pc + n }

/-- Execute a single SLUG-3 Opcode update to the state -/
def executeOp (state : MachineState) (inst : Instruction) : MachineState :=
  let a := inst.argA
  let b := inst.argB
  let nextState := match inst.op with
    | .nop => { state with pc := state.pc + 1 }
    | .add => 
      let res := Fix16.add a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .sub => 
      let res := Fix16.sub a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .mul => 
      let res := Fix16.mul a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .div => 
      let res := Fix16.div a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .min => 
      let res := Fix16.min a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .max => 
      let res := Fix16.max a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .abs => 
      let res := Fix16.abs a
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .neg => 
      let res := Fix16.neg a
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .shl => 
      let res := Fix16.mul a (Fix16.mk ((2 ^ (a.raw.toNat % 16)) * 65536).toUInt32)
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .shr => 
      let res := Fix16.div a (Fix16.mk ((2 ^ (a.raw.toNat % 16)) * 65536).toUInt32)
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .and => 
      let res : Fix16 := ⟨a.raw &&& b.raw⟩
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .or => 
      let res : Fix16 := ⟨a.raw ||| b.raw⟩
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .xor => 
      let res : Fix16 := ⟨a.raw ^^^ b.raw⟩
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .eq => 
      let res := if a == b then Fix16.one else Fix16.zero
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .lt => 
      let res := if a.raw < b.raw then Fix16.one else Fix16.zero
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .gt => 
      let res := if a.raw > b.raw then Fix16.one else Fix16.zero
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .load => 
      let res := state.read (Int.ofNat a.raw.toNat)
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .store => 
      MachineState.pcUpdate (state.write (Int.ofNat a.raw.toNat) b) 1
    | .jmp => { state with pc := a.raw.toNat % state.memory.size }
    | .jz => 
      if a.raw == 0 then { state with pc := b.raw.toNat % state.memory.size }
      else { state with pc := state.pc + 1 }
    | .jnz => 
      if a.raw != 0 then { state with pc := b.raw.toNat % state.memory.size }
      else { state with pc := state.pc + 1 }
    | .call => 
      { state with pc := a.raw.toNat % state.memory.size, stack := (Fix16.mk (state.pc + 1).toUInt32) :: state.stack }
    | .ret => 
      match state.stack with
      | [] => { state with exhausted := true }
      | s :: ss => { state with pc := s.raw.toNat % state.memory.size, stack := ss }
    | .dup => { state with stack := a :: state.stack, pc := state.pc + 1 }
    | .drop => 
      match state.stack with
      | [] => { state with pc := state.pc + 1 }
      | _ :: ss => { state with stack := ss, pc := state.pc + 1 }
    | .halt => { state with exhausted := true }
  nextState

def interlockingEnergyPort
    (currentX prevX : BraidBracket.PhaseVec)
    (a : AnisotropyTensor) : Fix16 :=
  interlockingEnergy currentX prevX a

def guardIntegrity (_state : MachineState) (v : BraidBracket.PhaseVec) (acc : BraidBracket.PhaseVec) (ε : Fix16) : Bool :=
  -- Link to Connector 1
  isIntegrable (BraidBracket.PhaseVec.add acc v) [v] ε

/-- Max Bandwidth Guard: Link to Connector 2 (Parcae/OMT) -/
def guardBandwidth (norm : SpectralNorm) (nodes : Nat) (τ : Fix16) (ops : Nat) : Bool :=
  -- Halt if operations per frame exceed bandwidth Ω_max
  let limit := (omegaMax norm nodes τ).raw.toNat
  ops < limit

end Semantics.Decoder
