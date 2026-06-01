-- AVM ISA v1 (Lean-only): Step semantics

import Semantics.AVMIsa.State

namespace Semantics.AVMIsa

/-- Error tags for rejected states (ill-typed, underflow, etc.). -/
inductive StepError : Type where
  | stackUnderflow
  | typeMismatch
  | invalidJump
  | missingLocal
  deriving Inhabited, DecidableEq, BEq, Repr

/-- Outcome type for AVM execution.

We avoid Float and avoid exceptions. Backends should mirror this boundary.
-/
inductive Outcome (α : Type) : Type where
  | ok : α → Outcome α
  | err : StepError → Outcome α
  deriving Inhabited, Repr

/-- Pop one element from stack. -/
def pop1 (s : State) : Outcome (AnyVal × State) :=
  match s.stack with
  | [] => Outcome.err StepError.stackUnderflow
  | x :: xs => Outcome.ok (x, { s with stack := xs })

/-- Push one element onto stack. -/
def push1 (s : State) (v : AnyVal) : State :=
  { s with stack := v :: s.stack }

/-- Evaluate a primitive.

NOTE: This v1 skeleton implements only a small subset. Extend strictly by
adding Lean semantics; do not delegate meaning to backends.
-/
def evalPrim (p : Prim) (s : State) : Outcome State :=
  match p with
  | Prim.not =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v, s1) =>
          match v with
          | ⟨AvmTy.bool, AvmVal.b x⟩ =>
              Outcome.ok (push1 s1 ⟨AvmTy.bool, AvmVal.b (!x)⟩)
          | _ => Outcome.err StepError.typeMismatch
  | Prim.and =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v1, s1) =>
          match pop1 s1 with
          | Outcome.err e => Outcome.err e
          | Outcome.ok (v2, s2) =>
              match v1, v2 with
              | ⟨AvmTy.bool, AvmVal.b b1⟩, ⟨AvmTy.bool, AvmVal.b b2⟩ =>
                  Outcome.ok (push1 s2 ⟨AvmTy.bool, AvmVal.b (b2 && b1)⟩)
              | _, _ => Outcome.err StepError.typeMismatch
  | Prim.or =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v1, s1) =>
          match pop1 s1 with
          | Outcome.err e => Outcome.err e
          | Outcome.ok (v2, s2) =>
              match v1, v2 with
              | ⟨AvmTy.bool, AvmVal.b b1⟩, ⟨AvmTy.bool, AvmVal.b b2⟩ =>
                  Outcome.ok (push1 s2 ⟨AvmTy.bool, AvmVal.b (b2 || b1)⟩)
              | _, _ => Outcome.err StepError.typeMismatch
  | Prim.addSatQ0 =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v1, s1) =>
          match pop1 s1 with
          | Outcome.err e => Outcome.err e
          | Outcome.ok (v2, s2) =>
              match v1, v2 with
              | ⟨AvmTy.q0_16, AvmVal.q0 x⟩, ⟨AvmTy.q0_16, AvmVal.q0 y⟩ =>
                  Outcome.ok (push1 s2 ⟨AvmTy.q0_16, AvmVal.q0 (Semantics.Q0_16.add y x)⟩)
              | _, _ => Outcome.err StepError.typeMismatch
  | Prim.subSatQ0 =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v1, s1) =>
          match pop1 s1 with
          | Outcome.err e => Outcome.err e
          | Outcome.ok (v2, s2) =>
              match v1, v2 with
              | ⟨AvmTy.q0_16, AvmVal.q0 x⟩, ⟨AvmTy.q0_16, AvmVal.q0 y⟩ =>
                  Outcome.ok (push1 s2 ⟨AvmTy.q0_16, AvmVal.q0 (Semantics.Q0_16.sub y x)⟩)
              | _, _ => Outcome.err StepError.typeMismatch
  | Prim.addSatQ16 =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v1, s1) =>
          match pop1 s1 with
          | Outcome.err e => Outcome.err e
          | Outcome.ok (v2, s2) =>
              match v1, v2 with
              | ⟨AvmTy.q16_16, AvmVal.q16 x⟩, ⟨AvmTy.q16_16, AvmVal.q16 y⟩ =>
                  Outcome.ok (push1 s2 ⟨AvmTy.q16_16, AvmVal.q16 (Semantics.Q16_16.add y x)⟩)
              | _, _ => Outcome.err StepError.typeMismatch
  | Prim.subSatQ16 =>
      match pop1 s with
      | Outcome.err e => Outcome.err e
      | Outcome.ok (v1, s1) =>
          match pop1 s1 with
          | Outcome.err e => Outcome.err e
          | Outcome.ok (v2, s2) =>
              match v1, v2 with
              | ⟨AvmTy.q16_16, AvmVal.q16 x⟩, ⟨AvmTy.q16_16, AvmVal.q16 y⟩ =>
                  Outcome.ok (push1 s2 ⟨AvmTy.q16_16, AvmVal.q16 (Semantics.Q16_16.sub y x)⟩)
              | _, _ => Outcome.err StepError.typeMismatch

/-- One-step execution.

`Program` is modeled as a list for v1.
-/
def step (program : List Instr) (s : State) : Outcome State :=
  if s.halted then
    Outcome.ok s
  else
    match program[s.pc]? with
    | none => Outcome.err StepError.invalidJump
    | some instr =>
        match instr with
        | Instr.halt => Outcome.ok { s with halted := true }
        | Instr.push v => Outcome.ok { s with pc := s.pc + 1, stack := v :: s.stack }
        | Instr.pop =>
            match pop1 s with
            | Outcome.err e => Outcome.err e
            | Outcome.ok (_, s1) => Outcome.ok { s1 with pc := s.pc + 1 }
        | Instr.dup =>
            match s.stack with
            | [] => Outcome.err StepError.stackUnderflow
            | x :: xs => Outcome.ok { s with pc := s.pc + 1, stack := x :: x :: xs }
        | Instr.swap =>
            match s.stack with
            | a :: b :: xs => Outcome.ok { s with pc := s.pc + 1, stack := b :: a :: xs }
            | _ => Outcome.err StepError.stackUnderflow
        | Instr.load i =>
            match getLocal? s i with
            | none => Outcome.err StepError.missingLocal
            | some v => Outcome.ok { s with pc := s.pc + 1, stack := v :: s.stack }
        | Instr.store i =>
            match pop1 s with
            | Outcome.err e => Outcome.err e
            | Outcome.ok (v, s1) => Outcome.ok { (setLocal s1 i v) with pc := s.pc + 1 }
        | Instr.jump target =>
            if target < program.length then
              Outcome.ok { s with pc := target }
            else
              Outcome.err StepError.invalidJump
        | Instr.jumpIf target =>
            match pop1 s with
            | Outcome.err e => Outcome.err e
            | Outcome.ok (v, s1) =>
                match v with
                | ⟨AvmTy.bool, AvmVal.b b⟩ =>
                    if b then
                      if target < program.length then
                        Outcome.ok { s1 with pc := target }
                      else
                        Outcome.err StepError.invalidJump
                    else
                      Outcome.ok { s1 with pc := s.pc + 1 }
                | _ => Outcome.err StepError.typeMismatch
        | Instr.prim p =>
            match evalPrim p s with
            | Outcome.err e => Outcome.err e
            | Outcome.ok s1 => Outcome.ok { s1 with pc := s.pc + 1 }

end Semantics.AVMIsa
