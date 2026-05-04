/-
Semantics/Decoder.lean - Model 141 Self-Instantiating Weird Machine

This module implements the OISC-SLUG3 engine as described in the N-Folded MMR 
Gossip EBML Schema. It executes 27 ternary opcodes while enforcing 
Integrability and Stability constraints from the simulation manifold.

Lean is the source of truth.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Int.Basic
import Semantics.DynamicCanal
import Semantics.BraidBracket
import Semantics.Connectors
import Semantics.FixedPoint
import Semantics.SLUG3

namespace Semantics.Decoder

open DynamicCanal
open Semantics.BraidBracket
open Semantics.Connectors
open Semantics.Q16_16
open Semantics.BraidBracket
open Semantics.ManifoldFlow
open Semantics.SLUG3

/-- Machine State for Model 141 -/
structure MachineState where
  pc      : Nat
  stack   : List Q16_16
  memory  : Array Q16_16
  exhausted : Bool
  frustPrevX : BraidBracket.PhaseVec -- Hardware cache for P_{m-1}
  frustAniso : AnisotropyTensor      -- Hardware cache for A_ij

/-- Initial state with 1024 words of memory -/
def MachineState.init (initialMem : List Q16_16) : MachineState :=
  { pc := 0
  , stack := []
  , memory := (initialMem ++ (List.replicate (1024 - initialMem.length) Q16_16.zero)).toArray
  , exhausted := false
  , frustPrevX := BraidBracket.PhaseVec.zero
  , frustAniso := { xx := Q16_16.zero, xy := Q16_16.zero, yy := Q16_16.zero } }

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
  argA : Q16_16
  argB : Q16_16
  dest : Nat

/-- Native Port Reading Header -/
def MachineState.read (state : MachineState) (addr : Int) : Q16_16 :=
  if addr >= 0 then
    if _hSize : 0 < state.memory.size then
      state.memory[addr.toNat % state.memory.size]!
    else
      Q16_16.zero
  else match addr with
    | -25 => -- frustResult
      interlockingEnergy BraidBracket.PhaseVec.zero state.frustPrevX state.frustAniso
    | _ => Q16_16.zero

/-- Native Port Writing Header -/
def MachineState.write (state : MachineState) (addr : Int) (val : Q16_16) : MachineState :=
  if addr >= 0 then
    if _hSize : 0 < state.memory.size then
      let idx := addr.toNat % state.memory.size
      { state with memory := state.memory.set! idx val }
    else
      state
  else match addr with
    | -23 => { state with frustPrevX := { x := val, y := Q16_16.zero : PhaseVec } }
    | -24 => { state with frustAniso := { xx := val, xy := Q16_16.zero, yy := Q16_16.zero } }
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
      let res := a + b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .sub =>
      let res := a - b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .mul =>
      let res := a * b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .div =>
      let res := a / b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .min =>
      let res := Q16_16.min a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .max =>
      let res := Q16_16.max a b
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .abs =>
      let res := Q16_16.abs a
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .neg =>
      let res := -a
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .shl =>
      let res := a * Q16_16.ofFloat ((2 ^ (a.val.toNat % 16)).toFloat)
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .shr =>
      let res := a / Q16_16.ofFloat ((2 ^ (a.val.toNat % 16)).toFloat)
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .and =>
      let res : Q16_16 := ⟨a.val &&& b.val⟩
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .or =>
      let res : Q16_16 := ⟨a.val ||| b.val⟩
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .xor =>
      let res : Q16_16 := ⟨a.val ^^^ b.val⟩
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .eq =>
      let res := if a == b then Q16_16.one else Q16_16.zero
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .lt =>
      let res := if a.val < b.val then Q16_16.one else Q16_16.zero
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .gt =>
      let res := if a.val > b.val then Q16_16.one else Q16_16.zero
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .load =>
      let res := state.read (Int.ofNat a.val.toNat)
      MachineState.pcUpdate (state.write (Int.ofNat inst.dest) res) 1
    | .store =>
      MachineState.pcUpdate (state.write (Int.ofNat a.val.toNat) b) 1
    | .jmp => { state with pc := a.val.toNat % state.memory.size }
    | .jz =>
      if a.val == 0 then { state with pc := b.val.toNat % state.memory.size }
      else { state with pc := state.pc + 1 }
    | .jnz =>
      if a.val != 0 then { state with pc := b.val.toNat % state.memory.size }
      else { state with pc := state.pc + 1 }
    | .call =>
      { state with pc := a.val.toNat % state.memory.size, stack := Q16_16.ofFloat (state.pc + 1).toFloat :: state.stack }
    | .ret =>
      match state.stack with
      | [] => { state with exhausted := true }
      | s :: ss => { state with pc := s.val.toNat % state.memory.size, stack := ss }
    | .dup => { state with stack := a :: state.stack, pc := state.pc + 1 }
    | .drop => 
      match state.stack with
      | [] => { state with pc := state.pc + 1 }
      | _ :: ss => { state with stack := ss, pc := state.pc + 1 }
    | .halt => { state with exhausted := true }
  nextState

def interlockingEnergyPort
    (currentX prevX : BraidBracket.PhaseVec)
    (a : AnisotropyTensor) : Q16_16 :=
  interlockingEnergy currentX prevX a

def guardIntegrity (_state : MachineState) (v : BraidBracket.PhaseVec) (acc : BraidBracket.PhaseVec) (ε : Q16_16) : Bool :=
  -- Link to Connector 1
  isIntegrable (BraidBracket.PhaseVec.add acc v) [v] ε

/-- Max Bandwidth Guard: Link to Connector 2 (Parcae/OMT) -/
def guardBandwidth (norm : SpectralNorm) (nodes : Nat) (τ : Q16_16) (ops : Nat) : Bool :=
  -- Halt if operations per frame exceed bandwidth Ω_max
  let limit := (omegaMax norm nodes τ).val.toNat
  ops < limit

end Semantics.Decoder
