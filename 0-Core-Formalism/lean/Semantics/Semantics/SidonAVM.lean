import Mathlib.Data.Set.Basic
import Semantics.AVM
import Semantics.SidonSet

namespace Semantics.SidonAVM

open Semantics
open Semantics.AVM
open Semantics.SidonSet

/-! # Sidon AVM — Greedy Erdős–Turán Construction

This module implements the greedy Sidon set generator as an AVM program.
The AVM state encodes the Sidon construction state in memory:
  M[0]  = target size (k)
  M[1]  = current length
  M[2..9] = current elements (max 8 slots for braid strands)
  M[10] = candidate
  M[11] = canAdd result (1 = yes, 0 = no)
  M[12] = loop index i
  M[13] = loop index j
  M[14] = temp sum
  M[15] = temp flag
-/

/-- Maximum Sidon set size supported by this AVM program (8 braid strands). -/
def maxSidonSize : Nat := 8

/-- Memory layout constants. -/
def memTarget : Nat := 0
def memCurrentLen : Nat := 1
def memCurrentBase : Nat := 2
def memCandidate : Nat := 10
def memCanAdd : Nat := 11
def memLoopI : Nat := 12
def memLoopJ : Nat := 13
def memTempSum : Nat := 14
def memTempFlag : Nat := 15

/-- Initialize AVM memory for Sidon generation. -/
def initMemory (target : Nat) : Array Value :=
  let mem := Array.mk (List.replicate 20 (Value.int 0))
  let mem := setMemory mem memTarget (Value.int target)
  let mem := setMemory mem memCurrentLen (Value.int 1)
  let mem := setMemory mem memCurrentBase (Value.int 1)
  let mem := setMemory mem memCandidate (Value.int 2)
  mem

/-- Read a Nat from memory at given address. Returns 0 if not an int. -/
def readNat (mem : Array Value) (addr : Nat) : Nat :=
  match mem[addr]? with
  | some (Value.int n) => n.toNat
  | _ => 0

/-- Read current Sidon elements from memory as a List Nat. -/
def readCurrent (mem : Array Value) : List Nat :=
  let len := readNat mem memCurrentLen
  (List.range len).map (fun i => readNat mem (memCurrentBase + i))

/-- Read the candidate from memory. -/
def readCandidate (mem : Array Value) : Nat :=
  readNat mem memCandidate

/-- Check if the greedy Sidon construction is complete. -/
def sidonCheckDone (s : State) : State :=
  let target := readNat s.memory memTarget
  let len := readNat s.memory memCurrentLen
  if len ≥ target then { s with halted := true } else s

/-- Check if candidate can be added to the current Sidon set.
    Uses the pure Lean `canAdd` function. -/
def sidonTryAdd (s : State) : State :=
  let current := readCurrent s.memory
  let candidate := readCandidate s.memory
  if canAdd current candidate then
    let len := readNat s.memory memCurrentLen
    let mem := setMemory s.memory (memCurrentBase + len) (Value.int candidate)
    let mem := setMemory mem memCurrentLen (Value.int (len + 1))
    { s with memory := mem }
  else s

/-- Increment the candidate. -/
def sidonIncrementCandidate (s : State) : State :=
  let c := readCandidate s.memory
  { s with memory := setMemory s.memory memCandidate (Value.int (c + 1)) }

/-- Sidon-specific step handler. Extends generic AVM step with
    method calls for Sidon operations. -/
def sidonStep (s : State) : State :=
  if s.halted then s
  else match s.program[s.pc]? with
    | some (Instruction.call "sidonCheckDone") =>
      sidonCheckDone { s with pc := s.pc + 1 }
    | some (Instruction.call "sidonTryAdd") =>
      sidonTryAdd { s with pc := s.pc + 1 }
    | some (Instruction.call "sidonIncrementCandidate") =>
      sidonIncrementCandidate { s with pc := s.pc + 1 }
    | _ => step s

/-- Run Sidon AVM with fuel. -/
def sidonRun (s : State) (fuel : Nat) : State :=
  match fuel with
  | 0 => s
  | fuel' + 1 =>
    let s' := sidonStep s
    if s'.halted then s' else sidonRun s' fuel'

/-- AVM program for greedy Sidon generation.
    Loop: checkDone → tryAdd → incrementCandidate → jump back. -/
def sidonProgram : Array Instruction := #[
  Instruction.call "sidonCheckDone",
  Instruction.call "sidonTryAdd",
  Instruction.call "sidonIncrementCandidate",
  Instruction.jump 0,
  Instruction.halt
]

/-- Create initial AVM state for generating a Sidon set of size target. -/
def sidonInitialState (target : Nat) : State :=
  { stack := [], pc := 0, memory := initMemory target,
    program := sidonProgram, halted := false }

/-- Extract the generated Sidon set from the final AVM state. -/
def extractSidonSet (s : State) : List Nat :=
  readCurrent s.memory

/-- Compuatable boolean test for the Sidon property. -/
def isSidonList (s : List Nat) : Bool :=
  let sums := pairwiseSums s
  sums.length == sums.eraseDups.length

/-- Receipt for one Sidon AVM step. -/
structure SidonReceipt where
  stepCount : Nat
  pc : Nat
  candidate : Nat
  currentLen : Nat
  deriving Repr

/-- Generate receipts from an AVM execution trace. -/
def sidonRunTrace (s : State) (fuel : Nat) (stepCount : Nat := 0)
    : State × List SidonReceipt :=
  match fuel with
  | 0 => (s, [])
  | fuel' + 1 =>
    if s.halted then (s, [])
    else
      let candidate := readCandidate s.memory
      let currentLen := readNat s.memory memCurrentLen
      let receipt := { stepCount := stepCount, pc := s.pc,
                       candidate := candidate, currentLen := currentLen }
      let s' := sidonStep s
      let (final_s, rest) := sidonRunTrace s' fuel' (stepCount + 1)
      (final_s, receipt :: rest)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Executable Witness
-- ═══════════════════════════════════════════════════════════════════════════

#eval extractSidonSet (sidonRun (sidonInitialState 6) 3600)
-- Expected: [1, 2, 4, 8, 13, 21]

#eval (sidonRun (sidonInitialState 8) 6400).halted
-- Expected: true

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Verification Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- Computational verification: for small targets, the AVM produces
    the same result as the pure functional generator. -/
theorem sidonAVM_eq_generateSidonFuel (target : Nat) (h : target ≤ maxSidonSize) :
  let fuel := target * target * 100 + 1
  let initial := sidonInitialState target
  let final := sidonRun initial fuel
  final.halted →
  generateSidonFuel target fuel = some (extractSidonSet final) :=
by
  unfold maxSidonSize at h
  interval_cases target <;> native_decide

/-- The AVM-generated set satisfies the Sidon property. -/
theorem sidonAVM_isSidonList (target : Nat) (h : target ≤ maxSidonSize) :
  let fuel := target * target * 100 + 1
  let initial := sidonInitialState target
  let final := sidonRun initial fuel
  final.halted →
  isSidonList (extractSidonSet final) = true :=
by
  unfold maxSidonSize at h
  interval_cases target <;> native_decide

/-- Termination bound: the greedy Sidon AVM terminates within
    target² * 100 + 1 steps for target ≤ 8. -/
theorem sidonAVM_terminates (target : Nat) (h : target ≤ maxSidonSize) :
  let fuel := target * target * 100 + 1
  let initial := sidonInitialState target
  let final := sidonRun initial fuel
  final.halted :=
by
  unfold maxSidonSize at h
  interval_cases target <;> native_decide

end Semantics.SidonAVM
