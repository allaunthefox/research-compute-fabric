import Sparkle

namespace Semantics.SparkleBridge

/--
Revision metadata for the Sparkle HDL dependency used by this workspace.

Sparkle currently tracks Lean 4.28 upstream, while this Semantics package is
validated on Lean 4.29. Keep all revision-sensitive facts here so future
Sparkle API or toolchain changes only need one shim update.
-/
structure SparkleRevision where
  packageName : String
  repository : String
  pinnedRevision : String
  upstreamLeanToolchain : String
  semanticsLeanToolchain : String
  notes : String
  deriving Repr, BEq

/-- The Sparkle revision pinned in `lakefile.toml`. -/
def pinnedSparkleRevision : SparkleRevision where
  packageName := "sparkle"
  repository := "https://github.com/Verilean/sparkle.git"
  pinnedRevision := "252341078dba3c2612719746e6a459dada2248ea"
  upstreamLeanToolchain := "leanprover/lean4:v4.28.0"
  semanticsLeanToolchain := "leanprover/lean4:v4.29.1"
  notes := "Build-checked under Semantics despite Sparkle's one-minor Lean toolchain skew."

/--
Revision shim for the external Sparkle HDL dependency.

S3C and morphic hardware modules should import this file rather than importing
Sparkle internals directly. If Sparkle renames modules or moves constructors,
repair this small surface and keep downstream Semantics code stable.
-/
abbrev DomainConfig := Sparkle.Core.Domain.DomainConfig
abbrev ActiveEdge := Sparkle.Core.Domain.ActiveEdge
abbrev ResetKind := Sparkle.Core.Domain.ResetKind

abbrev Signal := Sparkle.Core.Signal.Signal

def defaultDomain : DomainConfig := Sparkle.Core.Domain.defaultDomain
def domain50MHz : DomainConfig := Sparkle.Core.Domain.domain50MHz
def domain200MHz : DomainConfig := Sparkle.Core.Domain.domain200MHz

namespace Signal

variable {dom : DomainConfig} {α β : Type u}

/-- Create a constant signal. -/
def pure (x : α) : Signal dom α :=
  Sparkle.Core.Signal.Signal.pure x

/-- Map combinational logic over a signal. -/
def map (f : α → β) (s : Signal dom α) : Signal dom β :=
  Sparkle.Core.Signal.Signal.map f s

/-- Sample a signal at a single clock tick. -/
def atTime (s : Signal dom α) (t : Nat) : α :=
  Sparkle.Core.Signal.Signal.atTime s t

/-- Single-cycle register/delay primitive. -/
def register (init : α) (input : Signal dom α) : Signal dom α :=
  Sparkle.Core.Signal.Signal.register init input

/-- Sample the first `n` clock ticks. -/
def sample (s : Signal dom α) (n : Nat) : List α :=
  Sparkle.Core.Signal.Signal.sample s n

end Signal

/-- Minimal smoke circuit that exercises the compatibility surface. -/
def registerChain8 {dom : DomainConfig} (input : Signal dom (BitVec 8)) : Signal dom (BitVec 8) :=
  let d1 := Signal.register 0#8 input
  let d2 := Signal.register 0#8 d1
  Signal.register 0#8 d2

def registerChain8First4 : List (BitVec 8) :=
  let input : Signal defaultDomain (BitVec 8) :=
    Signal.map (fun n => BitVec.ofNat 8 n) (Signal.pure 7)
  Signal.sample (registerChain8 input) 4

def dependencyWitness : True := True.intro

-- ═══════════════════════════════════════════════════════════════════════════
-- § Tang Nano 9K target profile
-- ═══════════════════════════════════════════════════════════════════════════

/-- Board-level FPGA target metadata for Sparkle output. -/
structure FpgaTarget where
  targetName : String
  board : String
  device : String
  family : String
  packageName : String
  clockHz : Nat
  topModule : String
  constraintFile : String
  buildScript : String
  generatedRtlDir : String
  deriving Repr, BEq

/--
Primary local FPGA target.

Tang Nano 9K uses the Gowin GW1NR-LV9QN88PC6/I5 in QN88 package with the
27 MHz onboard oscillator on pin 52. Keep this target as the one source of
truth for Sparkle-generated hardware until a second board is explicitly added.
-/
def tangNano9KSparkleTarget : FpgaTarget where
  targetName := "sparkle_tangnano9k"
  board := "Sipeed Tang Nano 9K"
  device := "GW1NR-LV9QN88PC6/I5"
  family := "GW1N-9C"
  packageName := "QN88"
  clockHz := 27000000
  topModule := "SparkleTangNano9KTop"
  constraintFile := "hardware/sparkle/tangnano9k/sparkle_tangnano9k.cst"
  buildScript := "hardware/sparkle/tangnano9k/build_sparkle_tangnano9k.sh"
  generatedRtlDir := "hardware/sparkle/generated"

def targetWitness : String :=
  s!"{tangNano9KSparkleTarget.board}:{tangNano9KSparkleTarget.device}:{tangNano9KSparkleTarget.clockHz}"

end Semantics.SparkleBridge
