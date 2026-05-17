# Lemma Proof Space Mapping

## Overview

This document maps the MetaManifoldProver lemma proving effort, including the
original search space, backend status, bounded verification evidence, and final
Lean closure path. The initial map prevented repeated troubleshooting; this
revision records that the four Q16_16 proof debts are now discharged in Lean.

## Target Lemmas

### 1. weighted_term_bounded

**Location:** MetaManifoldProver.lean line 89
**Statement:** `(E * α) / 65536 <= E` given `E >= 0`, `0 <= α`, `α <= 65536`
**Status:** ✅ Proven in Lean
**Computational Verification:** ✅ 10,201 test cases passed (E in [0,100], α in [0,100])
**Closure Method:** `Int.mul_le_mul_of_nonneg_left`, `Int.ediv_le_ediv`, and `Int.mul_ediv_cancel`

### 2. shiftRight_eq_div

**Location:** MetaManifoldProver.lean line 104
**Statement:** `x >>> 16 = x / 65536`
**Status:** ✅ Proven in Lean
**Computational Verification:** ✅ 1,001 test cases passed (x in [0,1000])
**Closure Method:** Split `Int` into `ofNat` and `negSucc`; use `Nat.shiftRight_eq_div_pow` and `Int.ediv_of_neg_of_pos`

### 3. shiftRight_monotone

**Location:** MetaManifoldProver.lean line 126
**Statement:** `a >>> 16 <= b >>> 16` given `a <= b`
**Status:** ✅ Proven in Lean
**Computational Verification:** ✅ 5,151 test cases passed (a,b in [0,100], all pairs where a <= b)
**Closure Method:** Rewrite with `shiftRight_eq_div`, then apply `Int.ediv_le_ediv`

### 4. div_le_div_of_lt

**Location:** MetaManifoldProver.lean line 136
**Statement:** `x / a <= x / b` given `x >= 0`, `a > b`, `b > 0`
**Status:** ✅ Proven in Lean
**Computational Verification:** ✅ 63,000+ test cases passed (x in [0,50], a,b in [1,50], all valid triples where a > b)
**Closure Method:** `Int.ediv_nonneg`, `Int.ediv_mul_le`, and `Int.le_ediv_iff_mul_le`

## Backend Space Mapping

### Vulkan Backend

**Status:** ✅ Available and working
**Initialization:** wgpu device successfully initialized
**Capabilities:** GPU-accelerated proof generation
**Historical Issue:** Generated generic tactics did not match specific proof contexts.

### Ollama Backend

**Status:** ❌ Not available in the mapped run
**Error:** 404 Client Error: Not Found for url: http://localhost:11434/api/generate
**Requirements:** Ollama API server running locally

### Unsloth Backend

**Status:** ❌ Not available in the mapped run
**Error:** Model not found in HuggingFace (llama3.2)
**Requirements:** Valid HuggingFace model identifier or local model folder

### Thoth Backend

**Status:** ❌ Not available in the mapped run
**Error:** Backend not available

## Approach Space Mapping

### 1. Vulkan GPU Tactics

**Tried:** ✅ Yes
**Result:** ❌ Failed in the original map
**Issue:** Generic tactics such as `intro h1 h2; simp at h2; apply Int.le_trans; assumption` failed because the current proof states had no additional binders.

### 2. Manual linarith Tactics

**Tried:** ✅ Yes
**Result:** ❌ Failed in the original map
**Issue:** The needed division inequalities are nonlinear for direct `linarith`.

### 3. Existing Lemma Application

**Tried:** ✅ Yes
**Result:** ✅ Succeeded after using the correct `Int` lemma shapes
**Resolved Issue:** The original route used mismatched lemma order and did not split signed shift behavior.

### 4. Computational Verification

**Tried:** ✅ Yes
**Result:** ✅ Success as bounded regression evidence
**Method:** CPU exhaustive search across bounded ranges
**Verification Script:** `/home/allaun/Documents/Research Stack/scripts/cpu_lemma_verifier.py`
**Total Test Cases:** 79,000+ across all lemmas
**Boundary:** These checks are evidence and regression fixtures; Lean proof closure is now the proof-bearing artifact.

## Computational Verification Results

### weighted_term_bounded

- **Range:** E in [0,100], α in [0,100]
- **Test Cases:** 10,201
- **Result:** ✅ All passed
- **Verification:** `(E * α) / 65536 <= E` holds for all tested values

### shiftRight_eq_div

- **Range:** x in [0,1000]
- **Test Cases:** 1,001
- **Result:** ✅ All passed
- **Verification:** `x >>> 16 = x / 65536` holds for all tested values

### shiftRight_monotone

- **Range:** a,b in [0,100], all pairs where a <= b
- **Test Cases:** 5,151
- **Result:** ✅ All passed
- **Verification:** `a >>> 16 <= b >>> 16` when `a <= b` holds for all tested pairs

### div_le_div_of_lt

- **Range:** x in [0,50], a,b in [1,50], all valid triples where a > b
- **Test Cases:** 63,000+
- **Result:** ✅ All passed
- **Verification:** `x / a <= x / b` when `a > b`, `x >= 0`, `b > 0` holds for all tested triples

## Current File State

### MetaManifoldProver.lean

**Compilation Status:** ✅ `lake build Semantics.MetaManifoldProver` succeeds
**Sorry Blocks:** ✅ 0 in the four mapped lemmas
**Computational Documentation:** ✅ Retained as bounded regression evidence
**Lean Closure:** ✅ Integer arithmetic proof path added for all four lemmas

## Proof Strategy Space

### QUBO Optimization Approach

**Concept:** Treat lemma proving as QUBO optimization problem
**Status:** Historical search route; no longer needed for these four lemmas

### Soliton Sweep Approach

**Concept:** Exhaustive search across bounded ranges
**Status:** Retained as regression evidence, not used as proof replacement

### Traditional Lean Tactics

**Concept:** Use standard Lean 4 tactics and Mathlib lemmas
**Status:** ✅ Succeeded after aligning to the correct signed integer division lemmas

## Future Directions

### 1. Full Semantics Build

**Action:** Run the full `lake build` for `0-Core-Formalism/lean/Semantics`
**Priority:** High
**Expected Outcome:** Confirm no downstream module relies on the old sorry-backed surface.

### 2. Proof Receipt Capture

**Action:** Add a durable proof-closure receipt for the four lemmas
**Priority:** High
**Expected Outcome:** Wiki and ENE surfaces can cite exact build output and source hash.

### 3. Backend Improvement

**Action:** Improve Vulkan backend tactic generation
**Priority:** Medium
**Expected Outcome:** More context-aware tactic suggestions for future proof debts.

### 4. Alternative Backends

**Action:** Set up Ollama or another working backend
**Priority:** Medium
**Expected Outcome:** More automated proof-generation options.

### 5. Formal Verification Extension

**Action:** Extend computational verification to larger Q16_16 ranges
**Priority:** Low
**Expected Outcome:** Stronger bounded regression coverage, not a replacement for Lean proof closure.

## Technical Details

### Type System

**Q16_16:** Fixed-point arithmetic alias to `Int`
**Int:** Standard integer type
**Resolved Point:** The Q16_16 alias means the final proof path can use Mathlib `Int` lemmas directly.

### Division Semantics

**Floor Division:** Used by Lean's integer `/`
**Bit Shift:** For signed `Int`, `>>> 16` matches floor division by `65536`
**Resolved Point:** The shift proof needs both `ofNat` and `negSucc` cases.

## References

### Files

- **Main File:** `/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/MetaManifoldProver.lean`
- **Verification Script:** `/home/allaun/Documents/Research Stack/scripts/cpu_lemma_verifier.py`
- **Backend Interface:** `/home/allaun/Documents/Research Stack/scripts/prover_backend_interface.py`
- **BF4Prover:** `/home/allaun/Documents/Research Stack/scripts/bf4prover.py`

## Summary

The original proof-space map showed four Q16_16 lemmas blocked behind `sorry`
after generic GPU tactics, direct `linarith`, and mismatched lemma applications
failed. The closure path was smaller than the search space suggested: use the
right `Int` floor-division lemmas, prove signed shift by an `Int` case split,
and keep the 79,000+ bounded CPU checks as regression evidence rather than as
formal proof substitutes.
