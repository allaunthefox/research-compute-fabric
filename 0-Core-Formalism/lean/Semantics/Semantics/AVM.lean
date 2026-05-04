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

/-- AVM Instruction Set -/
inductive Instruction where
  | push (v : Value)
  | pop
  | apply (arity : Nat)
  | jump (target : Nat)
  | jumpIf (target : Nat)
  | call (method : String)
  | ret
  deriving Repr, BEq

structure State where
  stack : List Value
  pc : Nat
  memory : List (String × Value)
  deriving Repr, BEq

/-- 
Implementation of informationalBind for AVM state transitions.
Ensures every AVM step is a traceable, lawful bind.
-/
def bindStep (s1 s2 : State) (m : Metric) : Bind State State :=
  informationalBind s1 s2 m 
    (fun _ _ _ => Q16_16.ofInt 1) -- Unit cost
    (fun _ => "AVM_STATE")
    (fun _ => "AVM_STATE")

/-- Single step execution -/
def step (instr : Instruction) (s : State) : State :=
  match instr with
  | Instruction.push v => { s with stack := v :: s.stack, pc := s.pc + 1 }
  | Instruction.pop => match s.stack with
    | [] => { s with pc := s.pc + 1 } 
    | _ :: rest => { s with stack := rest, pc := s.pc + 1 }
  | _ => { s with pc := s.pc + 1 } 

end Semantics.AVM
