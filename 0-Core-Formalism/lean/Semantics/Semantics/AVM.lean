import Semantics.FixedPoint
import Semantics.Bind

namespace Semantics.AVM

open Semantics

/-- AVM Value system enforcing Fixed-Point Determinism -/
inductive Value where
  | int : Int → Value
  | q16 : Q16_16 → Value
  | q0  : Q0_16 → Value
  | bool : Bool → Value
  | label : Nat → Value
  deriving Repr, BEq

/-- AVM Instruction Set
    Extended with arithmetic, comparison, stack manipulation, memory access,
    and halt for the Erdős–Turán AVM program. -/
inductive Instruction where
  | push (v : Value)
  | pop
  | dup
  | swap
  | add
  | sub
  | mul
  | div
  | eq
  | lt
  | load (addr : Nat)
  | store (addr : Nat)
  | jump (target : Nat)
  | jumpIf (target : Nat)
  | call (method : String)
  | ret
  | halt
  deriving Repr, BEq

structure State where
  stack : List Value
  pc : Nat
  memory : Array Value
  program : Array Instruction
  halted : Bool
  deriving Repr, BEq

/-- Safe memory write. If addr is out of bounds, memory is unchanged. -/
def setMemory (mem : Array Value) (addr : Nat) (v : Value) : Array Value :=
  if addr < mem.size then mem.set! addr v else mem

/--
Implementation of informationalBind for AVM state transitions.
Ensures every AVM step is a traceable, lawful bind.
-/
def bindStep (s1 s2 : State) (m : Metric) : Bind State State :=
  informationalBind s1 s2 m
    (fun _ _ _ => Q16_16.ofInt 1) -- Unit cost
    (fun _ => "AVM_STATE")
    (fun _ => "AVM_STATE")

/-- Single step execution. Fetches instruction from program at PC.
    If PC is out of bounds or halted, the machine halts. -/
def step (s : State) : State :=
  if s.halted then s
  else match s.program[s.pc]? with
    | none => { s with halted := true }
    | some instr =>
      let s := { s with pc := s.pc + 1 }
      match instr with
      | Instruction.push v => { s with stack := v :: s.stack }
      | Instruction.pop => match s.stack with
        | [] => s
        | _ :: rest => { s with stack := rest }
      | Instruction.dup => match s.stack with
        | [] => s
        | top :: rest => { s with stack := top :: top :: rest }
      | Instruction.swap => match s.stack with
        | a :: b :: rest => { s with stack := b :: a :: rest }
        | _ => s
      | Instruction.add => match s.stack with
        | Value.q16 b :: Value.q16 a :: rest =>
          { s with stack := Value.q16 (Q16_16.add a b) :: rest }
        | Value.int b :: Value.int a :: rest =>
          { s with stack := Value.int (a + b) :: rest }
        | _ => s
      | Instruction.sub => match s.stack with
        | Value.q16 b :: Value.q16 a :: rest =>
          { s with stack := Value.q16 (Q16_16.sub a b) :: rest }
        | Value.int b :: Value.int a :: rest =>
          { s with stack := Value.int (a - b) :: rest }
        | _ => s
      | Instruction.mul => match s.stack with
        | Value.q16 b :: Value.q16 a :: rest =>
          { s with stack := Value.q16 (Q16_16.mul a b) :: rest }
        | Value.int b :: Value.int a :: rest =>
          { s with stack := Value.int (a * b) :: rest }
        | _ => s
      | Instruction.div => match s.stack with
        | Value.q16 b :: Value.q16 a :: rest =>
          { s with stack := Value.q16 (Q16_16.div a b) :: rest }
        | Value.int b :: Value.int a :: rest =>
          if b ≠ 0 then { s with stack := Value.int (a / b) :: rest } else s
        | _ => s
      | Instruction.eq => match s.stack with
        | b :: a :: rest => { s with stack := Value.bool (a == b) :: rest }
        | _ => s
      | Instruction.lt => match s.stack with
        | Value.q16 b :: Value.q16 a :: rest =>
          { s with stack := Value.bool (a < b) :: rest }
        | Value.int b :: Value.int a :: rest =>
          { s with stack := Value.bool (a < b) :: rest }
        | _ => s
      | Instruction.load addr => match s.memory[addr]? with
        | some v => { s with stack := v :: s.stack }
        | none => s
      | Instruction.store addr => match s.stack with
        | v :: rest => { s with stack := rest, memory := setMemory s.memory addr v }
        | [] => s
      | Instruction.call method => s
      | Instruction.ret => s
      | Instruction.jump target => { s with pc := target }
      | Instruction.jumpIf target => match s.stack with
        | Value.bool true :: rest => { s with stack := rest, pc := target }
        | Value.bool false :: rest => { s with stack := rest }
        | _ => s
      | Instruction.halt => { s with halted := true }

/-- Run the AVM program with a fuel bound.
    Returns the final state when fuel is exhausted or the machine halts. -/
def run (s : State) (fuel : Nat) : State :=
  match fuel with
  | 0 => s
  | fuel' + 1 =>
    let s' := step s
    if s'.halted then s' else run s' fuel'

/-- Trace entry capturing one step of AVM execution. -/
structure TraceEntry where
  pc : Nat
  instr : Option Instruction
  stackDepth : Nat
  deriving Repr

/-- Run with trace collection for receipt generation. -/
def runTrace (s : State) (fuel : Nat) : State × List TraceEntry :=
  match fuel with
  | 0 => (s, [])
  | fuel' + 1 =>
    if s.halted then (s, [])
    else
      let entry := { pc := s.pc, instr := s.program[s.pc]?, stackDepth := s.stack.length }
      let s' := step s
      let (final_s, rest) := runTrace s' fuel'
      (final_s, entry :: rest)

end Semantics.AVM
