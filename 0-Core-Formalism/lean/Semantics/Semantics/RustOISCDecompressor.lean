import Std

namespace Semantics.RustOISCDecompressor

/-!
Rust OISC decompressor target, finite-state Lean surface.

This is intentionally small: it proves the shape of the decompressor hot path,
not a production codec. The only transition primitive is `step`. Rust, FPGA,
and ASIC targets must implement this same state update before promotion.
-/

abbrev Byte := Fin 256

def byte (n : Nat) : Byte :=
  ⟨n % 256, Nat.mod_lt n (by decide)⟩

def mixByte (a b : Byte) : Byte :=
  byte (a.val + b.val)

/-- Bounded decompressor state. `output` is newest-last. -/
structure OiscState where
  pc : Nat
  acc : Byte
  output : List Byte
  capacity : Nat
  halted : Bool
deriving DecidableEq, Repr

/-- One OISC instruction packet for the reference decompressor lane. -/
structure Instruction where
  symbol : Byte
  residual : Byte
  final : Bool
deriving DecidableEq, Repr

inductive StepOutcome where
  | continue
  | done
  | nan0
deriving DecidableEq, Repr

structure StepReceipt where
  state : OiscState
  outcome : StepOutcome
deriving DecidableEq, Repr

inductive DecodeDecision where
  | done
  | nan0
deriving DecidableEq, Repr

structure DecodeReceipt where
  state : OiscState
  decision : DecodeDecision
  instructionCount : Nat
deriving DecidableEq, Repr

def initState (capacity : Nat) : OiscState :=
  { pc := 0, acc := byte 0, output := [], capacity, halted := false }

def nan0State (s : OiscState) : OiscState :=
  { s with halted := true }

/--
The single decompressor transition.

If the state has halted, the transition is stable. If the bounded output tape
is full, the transition fails closed by halting. Otherwise it appends one
symbol, advances `pc`, and mixes symbol and residual into the accumulator.
-/
def step (s : OiscState) (i : Instruction) : StepReceipt :=
  if s.halted then
    { state := s, outcome := StepOutcome.done }
  else if s.output.length < s.capacity then
    let nextState : OiscState :=
      { pc := s.pc + 1,
        acc := mixByte (mixByte s.acc i.symbol) i.residual,
        output := s.output ++ [i.symbol],
        capacity := s.capacity,
        halted := i.final }
    { state := nextState,
      outcome := if i.final then StepOutcome.done else StepOutcome.continue }
  else
    { state := nan0State s, outcome := StepOutcome.nan0 }

def runInstructions : OiscState → List Instruction → StepReceipt
  | s, [] => { state := s, outcome := StepOutcome.done }
  | s, i :: rest =>
      let receipt := step s i
      match receipt.outcome with
      | StepOutcome.continue => runInstructions receipt.state rest
      | StepOutcome.done => receipt
      | StepOutcome.nan0 => receipt

def run (s : OiscState) (program : List Instruction) : OiscState :=
  (runInstructions s program).state

def emittedBytes (s : OiscState) : List Nat :=
  s.output.map (fun b => b.val)

def parseInstructions : List Nat → Option (List Instruction)
  | [] => some []
  | symbol :: residual :: final :: rest =>
      if final = 0 || final = 1 then
        match parseInstructions rest with
        | some tail =>
            some ({ symbol := byte symbol,
                    residual := byte residual,
                    final := final = 1 } :: tail)
        | none => none
      else
        none
  | _ => none

def magic : List Nat := [79, 73, 83, 67]
def version : Nat := 1
def header : List Nat := magic ++ [version]

def invalidReceipt (capacity : Nat) : DecodeReceipt :=
  { state := nan0State (initState capacity),
    decision := DecodeDecision.nan0,
    instructionCount := 0 }

def hasInternalFinal : List Instruction → Bool
  | [] => false
  | [_] => false
  | i :: rest => i.final || hasInternalFinal rest

def decodeWire (capacity : Nat) (wire : List Nat) : DecodeReceipt :=
  if wire.length < header.length then
    invalidReceipt capacity
  else if wire.take header.length ≠ header then
    invalidReceipt capacity
  else
    let body := wire.drop header.length
    if body = [] then
      { state := { initState capacity with halted := true },
        decision := DecodeDecision.done,
        instructionCount := 0 }
    else
      match parseInstructions body with
      | none => invalidReceipt capacity
      | some instructions =>
          if hasInternalFinal instructions then
            invalidReceipt capacity
          else
            let receipt := runInstructions (initState capacity) instructions
            { state := receipt.state,
              decision :=
                match receipt.outcome with
                | StepOutcome.nan0 => DecodeDecision.nan0
                | _ => DecodeDecision.done,
              instructionCount := instructions.length }

def instrA : Instruction := { symbol := byte 65, residual := byte 1, final := false }
def instrB : Instruction := { symbol := byte 66, residual := byte 1, final := false }
def instrC : Instruction := { symbol := byte 67, residual := byte 1, final := true }
def instrHighResidual : Instruction := { symbol := byte 120, residual := byte 200, final := false }
def instrWrapFinal : Instruction := { symbol := byte 34, residual := byte 17, final := true }

def abcProgram : List Instruction := [instrA, instrB, instrC]
def residualWrapProgram : List Instruction := [instrHighResidual, instrWrapFinal]
def postFinalProgram : List Instruction := [instrA, instrC, instrB]
def abcWire : List Nat := header ++ [65, 1, 0, 66, 1, 0, 67, 1, 1]
def emptyWire : List Nat := header
def badMagicWire : List Nat := [88, 73, 83, 67, 1]
def badVersionWire : List Nat := magic ++ [2]
def truncatedWire : List Nat := header ++ [65, 1]
def trailingAfterFinalWire : List Nat := header ++ [65, 1, 1, 66, 1, 0]

def abcFinal : OiscState :=
  run (initState 8) abcProgram

def residualWrapFinal : OiscState :=
  run (initState 8) residualWrapProgram

def postFinalStableFinal : OiscState :=
  run (initState 8) postFinalProgram

def overflowFinal : OiscState :=
  run (initState 2) abcProgram

def abcReceipt : DecodeReceipt :=
  decodeWire 8 abcWire

def emptyReceipt : DecodeReceipt :=
  decodeWire 8 emptyWire

def overflowReceipt : DecodeReceipt :=
  decodeWire 2 abcWire

theorem haltedStepStable (s : OiscState) (i : Instruction) :
    (step { s with halted := true } i).state = { s with halted := true } := by
  simp [step]

theorem firstStepEmitsOne :
    (step (initState 8) instrA).state.output.length = 1 := by
  native_decide

theorem abcFixtureByteExact :
    emittedBytes abcFinal = [65, 66, 67] := by
  native_decide

theorem abcFixtureHalts :
    abcFinal.halted = true := by
  native_decide

theorem residualAccumulatorWrapsClosed :
    emittedBytes residualWrapFinal = [120, 34] ∧
    residualWrapFinal.acc.val = 115 ∧
    residualWrapFinal.pc = 2 ∧
    residualWrapFinal.halted = true := by
  native_decide

theorem postFinalRunStableClosed :
    postFinalStableFinal = run (initState 8) [instrA, instrC] ∧
    emittedBytes postFinalStableFinal = [65, 67] ∧
    postFinalStableFinal.acc.val = 134 ∧
    postFinalStableFinal.pc = 2 ∧
    postFinalStableFinal.halted = true := by
  native_decide

theorem overflowFailsClosed :
    overflowFinal.halted = true ∧ emittedBytes overflowFinal = [65, 66] := by
  native_decide

theorem abcWireFixtureCloses :
    emittedBytes abcReceipt.state = [65, 66, 67] ∧
    abcReceipt.state.halted = true ∧
    abcReceipt.state.acc.val = 201 ∧
    abcReceipt.instructionCount = 3 ∧
    abcReceipt.decision = DecodeDecision.done := by
  native_decide

theorem emptyWireCloses :
    emittedBytes emptyReceipt.state = [] ∧
    emptyReceipt.state.halted = true ∧
    emptyReceipt.instructionCount = 0 ∧
    emptyReceipt.decision = DecodeDecision.done := by
  native_decide

theorem overflowWireFailsClosed :
    emittedBytes overflowReceipt.state = [65, 66] ∧
    overflowReceipt.state.halted = true ∧
    overflowReceipt.instructionCount = 3 ∧
    overflowReceipt.decision = DecodeDecision.nan0 := by
  native_decide

theorem invalidMagicFailsClosed :
    (decodeWire 8 badMagicWire).decision = DecodeDecision.nan0 := by
  native_decide

theorem invalidVersionFailsClosed :
    (decodeWire 8 badVersionWire).decision = DecodeDecision.nan0 := by
  native_decide

theorem truncatedInstructionFailsClosed :
    (decodeWire 8 truncatedWire).decision = DecodeDecision.nan0 := by
  native_decide

theorem trailingAfterFinalFailsClosed :
    (decodeWire 8 trailingAfterFinalWire).decision = DecodeDecision.nan0 := by
  native_decide

#eval emittedBytes abcFinal
#eval abcFinal.halted
#eval emittedBytes residualWrapFinal
#eval residualWrapFinal.acc.val
#eval emittedBytes postFinalStableFinal
#eval postFinalStableFinal.acc.val
#eval emittedBytes overflowFinal
#eval overflowFinal.halted
#eval emittedBytes abcReceipt.state
#eval abcReceipt.state.acc.val
#eval abcReceipt.instructionCount
#eval abcReceipt.decision

end Semantics.RustOISCDecompressor
