/-
  6502 OISC Blitter -- 0D Scalar Proof Engine
  
  A One-Instruction-Set Computer (OISC) with 6502 memory map semantics.
  The blitter verifies S3C theorems via exhaustive LUT enumeration.
  
  Proof strategy: Instead of symbolic proofs with free variables,
  we use native_decide on closed computations over the 8-bit domain.
  List.all (List.range 256) creates a single closed Bool that the
  native compiler can evaluate at proof-check time.
-/

import Std
import Mathlib.Data.Nat.Sqrt

namespace Blitter6502OISC

-- ============================================================================
-- Hardware sqrt LUT (8-bit domain: 0..255)
-- This table is loaded into blitter memory at $0200-$02FF.
-- ============================================================================

def sqrtLUT8 : List UInt8 :=
  [0, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3,
   4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5,
   5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
   6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
   8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
   8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
   9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
   10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11,
   11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
   11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
   12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
   12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
   13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
   13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
   14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
   14, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 15]

-- ============================================================================
-- S3C Theorem Verification (closed computations, no free variables)
-- ============================================================================

/-- Theorem 1: bPlus = bZero + 1 for all n in 0..255.
    Verified as a single closed computation. -/
theorem blitter_bPlusEqualsBZeroPlusOne :
  List.all (List.range 256) (fun n =>
    let k := Nat.sqrt n
    let bPlus := (k + 1) * (k + 1) - n
    let bZero := (k + 1) * (k + 1) - 1 - n
    bPlus = bZero + 1
  ) = true := by native_decide

/-- Theorem 2: throatAtShellMidpoint for all k in 0..255.
    At n = k^2 + k, handleA = handleBZero. -/
theorem blitter_throatAtShellMidpoint :
  List.all (List.range 256) (fun k =>
    let n := k * k + k
    let kk := Nat.sqrt n
    let a := n - kk * kk
    let bZero := (kk + 1) * (kk + 1) - 1 - n
    a = bZero
  ) = true := by native_decide

/-- Mirror term |a - b| using Nat subtraction (no if-expression).
    In Nat: |a-b| = (a-b) + (b-a) because truncation handles the cases. -/
def mirrorTerm (a b : Nat) : Nat := a - b + (b - a)

/-- Theorem 3: emitGateSimplified for all n in 0..255.
    The full gate (a>0 && bZero>0 && jScore>0) equals
    the simplified gate (a>0 && bZero>0) for every n. -/
theorem blitter_emitGateSimplified :
  List.all (List.range 256) (fun n =>
    let k := Nat.sqrt n
    let a := n - k * k
    let b := (k + 1) * (k + 1) - 1 - n
    let jScore := a * b + mirrorTerm a b + k
    let emitFull := a > 0 && b > 0 && jScore > 0
    let emitSimple := a > 0 && b > 0
    emitFull = emitSimple
  ) = true := by native_decide

-- ============================================================================
-- 6502 OISC Machine Specification (for hardware extraction)
-- ============================================================================

/-- CPU state. -/
structure CPU where
  pc : UInt16
  a  : UInt8
  x  : UInt8
  y  : UInt8
  halted : Bool

def initCPU : CPU :=
  { pc := 0, a := 0, x := 0, y := 0, halted := false }

end Blitter6502OISC
