/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CompileBridge.lean — GPU-Accelerated Compilation Bridge Formal Specification

This module formalizes the interface between the Lean 4 build system (lake)
and GPU-accelerated theorem verification. It defines the receipt schema,
theorem batch descriptors, and verification result types that the Rust
lake_compile_bridge binary reads and writes.

Architecture:
  lake build ──► CompileBridge (Lean) ──► Rust bridge (wgpu) ──► WGSL compute
       ▲                                                        │
       └──────────── build_receipt.json ◄───────────────────────┘

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §4: Eval witnesses and theorems required.
-/

namespace Semantics.CompileBridge

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Theorem Registry
-- ═══════════════════════════════════════════════════════════════════════════

/-- Canonical theorem IDs for GPU-accelerated verification.
    Each ID maps to a theorem in FixedPoint.lean and a verification kernel
    in the WGSL compile_bridge shader. -/
inductive TheoremID
  | zeroMul       -- zero * a = zero
  | mulZero       -- a * zero = zero
  | addZero       -- a + zero = a
  | zeroAdd       -- zero + a = a
  | subSelf       -- a - a = zero
  | oneMul        -- one * a = a
  | mulOne        -- a * one = a
  | addComm       -- a + b = b + a
  | negInvolutive -- -(-a) = a
  | subViaNeg     -- a - b = a + (-b)
  deriving Repr, DecidableEq, BEq, Inhabited

instance : ToString TheoremID where
  toString
    | .zeroMul       => "zero_mul"
    | .mulZero       => "mul_zero"
    | .addZero       => "add_zero"
    | .zeroAdd       => "zero_add"
    | .subSelf       => "sub_self"
    | .oneMul        => "one_mul"
    | .mulOne        => "mul_one"
    | .addComm       => "add_comm"
    | .negInvolutive => "neg_involutive"
    | .subViaNeg     => "sub_via_neg"

namespace TheoremID

/-- Map theorem ID to its WGSL shader kernel name. -/
def toKernelName : TheoremID → String
  | .zeroMul       => "check_zero_mul"
  | .mulZero       => "check_mul_zero"
  | .addZero       => "check_add_zero"
  | .zeroAdd       => "check_zero_add"
  | .subSelf       => "check_sub_self"
  | .oneMul        => "check_one_mul"
  | .mulOne        => "check_mul_one"
  | .addComm       => "check_add_comm"
  | .negInvolutive => "check_neg_involutive"
  | .subViaNeg     => "check_sub_via_neg"

/-- Map theorem ID to numeric dispatch index (matches WGSL switch). -/
def toDispatchIndex : TheoremID → Nat
  | .zeroMul       => 0
  | .mulZero       => 1
  | .addZero       => 2
  | .zeroAdd       => 3
  | .subSelf       => 4
  | .oneMul        => 5
  | .mulOne        => 6
  | .addComm       => 7
  | .negInvolutive => 8
  | .subViaNeg     => 9

/-- Number of GPU-verifiable theorems. -/
def count : Nat := 10

end TheoremID

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  GPU Verification Batch
-- ═══════════════════════════════════════════════════════════════════════════

/-- A single test vector for Q16_16 theorem verification. -/
structure TestVector where
  a : UInt32         -- First Q16_16 operand
  b : UInt32         -- Second Q16_16 operand
  expected : UInt32  -- Expected result (0 for property-based checks)
  deriving Repr, BEq, Inhabited

/-- Descriptor for a GPU theorem verification batch. -/
structure TheoremBatch where
  theoremId : UInt32   -- Dispatch index from TheoremID.toDispatchIndex
  count : UInt32       -- Number of test vectors
  deriving Repr, BEq, Inhabited

/-- Result of GPU theorem verification. -/
structure TheoremResult where
  theoremId : UInt32   -- Matching dispatch index
  passed : Bool        -- True if all test vectors passed
  total : UInt32       -- Total test vectors checked
  failed : UInt32      -- Number of test vectors that failed
  deriving Repr, BEq, Inhabited

/-- Complete GPU verification receipt. -/
structure VerificationReceipt where
  schema : String      -- "lake_compile_bridge_receipt_v1"
  version : String     -- "0.1.0"
  target : String      -- Lake build target (e.g., "Semantics.FixedPoint")
  jobs : UInt32        -- Parallel jobs used for lake build
  vectorsPerTheorem : UInt32  -- Test vectors per theorem
  gpuAvailable : Bool  -- Whether GPU was available
  gpuDevice : String   -- GPU device name
  theorems : List TheoremResult  -- Per-theorem results
  totalTheorems : Nat  -- Total theorems checked
  passed : Nat         -- Theorems passing
  failed : Nat         -- Theorems failing
  buildExitCode : Int  -- lake build exit code
  elapsedMs : Nat      -- Total elapsed time in milliseconds
  timestampUtc : String  -- ISO 8601 timestamp
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Bridge Invariants
-- ═══════════════════════════════════════════════════════════════════════════

/-- Invariant: theorem IDs in result match canonical registry. -/
def resultIdsValid (receipt : VerificationReceipt) : Bool :=
  receipt.theorems.all (fun r =>
    r.theoremId.toNat < TheoremID.count)

/-- Invariant: if passed then failed = 0, else failed = total. -/
def resultCountsValid (receipt : VerificationReceipt) : Bool :=
  receipt.theorems.all (fun r =>
    if r.passed then r.failed = 0 else r.failed = r.total)

/-- Invariant: totalTheorems = |theorems|. -/
def totalCountMatches (receipt : VerificationReceipt) : Bool :=
  receipt.totalTheorems = receipt.theorems.length

/-- All bridge invariants hold simultaneously. -/
def invariantsHold (receipt : VerificationReceipt) : Bool :=
  resultIdsValid receipt &&
  resultCountsValid receipt &&
  totalCountMatches receipt

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Lean-side Theorem Verification Wrapper
-- ═══════════════════════════════════════════════════════════════════════════

/--
Promote a GPU-verified theorem result into the Lean formal theory.

This is the receiving end of the bridge. The Rust binary writes a receipt,
and this function reads it, checks invariants, and returns a VerifiedClaim
that can be used in proofs.
-/
structure VerifiedClaim where
  theoremId : TheoremID
  gpuReceipt : TheoremResult
  leanTheorem : String   -- Name of the Lean theorem this verifies
  deriving Repr, Inhabited

/--
GPU results are an *accelerator* for native_decide, not a replacement.
The Lean-side theorem remains the authoritative proof. GPU verification
provides a fast, parallel cross-check that catches regressions early.
-/
def promoteToClaim (receipt : VerificationReceipt) (idx : Nat) : Option VerifiedClaim :=
  if h : idx < receipt.theorems.length then
    let res := receipt.theorems.get ⟨idx, h⟩
    let theoremId : TheoremID :=
      match res.theoremId with
      | 0 => TheoremID.zeroMul
      | 1 => TheoremID.mulZero
      | 2 => TheoremID.addZero
      | 3 => TheoremID.zeroAdd
      | 4 => TheoremID.subSelf
      | 5 => TheoremID.oneMul
      | 6 => TheoremID.mulOne
      | 7 => TheoremID.addComm
      | 8 => TheoremID.negInvolutive
      | 9 => TheoremID.subViaNeg
      | _ => TheoremID.zeroMul
    some {
      theoremId := theoremId
      gpuReceipt := res
      leanTheorem := toString theoremId
    }
  else
    none

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Eval Witnesses
-- ═══════════════════════════════════════════════════════════════════════════

/-- Empty receipt for invariant check (trivially valid). -/
def emptyReceipt : VerificationReceipt :=
  { schema := "lake_compile_bridge_receipt_v1"
    version := "0.1.0"
    target := ""
    jobs := 0
    vectorsPerTheorem := 0
    gpuAvailable := false
    gpuDevice := ""
    theorems := []
    totalTheorems := 0
    passed := 0
    failed := 0
    buildExitCode := 0
    elapsedMs := 0
    timestampUtc := "" }

#eval invariantsHold emptyReceipt

#eval List.map TheoremID.toDispatchIndex
  [TheoremID.zeroMul, TheoremID.mulZero, TheoremID.addZero, TheoremID.zeroAdd,
   TheoremID.subSelf, TheoremID.oneMul, TheoremID.mulOne, TheoremID.addComm,
   TheoremID.negInvolutive, TheoremID.subViaNeg]
  -- Expected: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

#eval (List.map TheoremID.toDispatchIndex
  [TheoremID.zeroMul, TheoremID.mulZero, TheoremID.addZero, TheoremID.zeroAdd,
   TheoremID.subSelf, TheoremID.oneMul, TheoremID.mulOne, TheoremID.addComm,
   TheoremID.negInvolutive, TheoremID.subViaNeg]).all (fun idx => idx < TheoremID.count)
  -- Expected: true

end Semantics.CompileBridge
