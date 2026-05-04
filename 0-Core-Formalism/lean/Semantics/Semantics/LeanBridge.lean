import Mathlib.Data.Rat.Defs

/-!
Lean Bridge Utilities
ID: LEAN-BRIDGE-1

This module provides utility functions and type class instances to smooth over
Lean 4 idiosyncrasies encountered during development.

Common issues addressed:
- Structure field notation complexity in theorem hypotheses
- BEq instance not found for functions returning Bool
- OfNat instance resolution for numerals in ℚ
- Structure constructor syntax differences
- List operations requiring BEq instances

STATUS: UTILITY
WARNING:
- This is a pragmatic engineering solution to Lean 4 friction points
- Use these utilities to avoid common type inference pitfalls
- Prefer direct Lean idioms when they work cleanly
-/

namespace Semantics

/--
Safe list count with predicate function.

Avoids BEq instance issues by using a manual recursive implementation
instead of List.count which requires BEq for the predicate result type.
-/
def safeCount {α : Type} (pred : α → Bool) (xs : List α) : Nat :=
  let rec go (ys : List α) (acc : Nat) : Nat :=
    match ys with
    | [] => acc
    | y :: rest =>
      if pred y then
        go rest (acc + 1)
      else
        go rest acc
  go xs 0

/--
Structure type marker for typeclass dispatch.

Use this to mark types that are structures (not inductives) for
special handling in utility functions.
-/
class StructType (α : Type) where

/--
Safe rational numeral conversion.

Provides explicit type annotations to avoid OfNat instance resolution issues.
-/
def q0 : ℚ := (0 : ℚ)
def q1 : ℚ := (1 : ℚ)

/--
Safe structure construction helper.

Avoids ⟨⟩ notation issues by using explicit field assignment syntax
that works reliably across Lean versions.
-/
def mkStruct {α : Type} [StructType α] (fields : α) : α :=
  fields

/--
Pattern matching helper for structures.

Provides a cases-like interface that works better with structure types
in theorem proofs.
-/
def structCases {α : Type} [StructType α] (x : α) (onFields : α → β) : β :=
  onFields x

/--
List filter with explicit predicate.

Alternative to List.filter that avoids BEq requirements.
-/
def safeFilter {α : Type} (pred : α → Bool) (xs : List α) : List α :=
  xs.filter pred

/--
List find with predicate.

Returns the first element satisfying the predicate, or none if not found.
-/
def safeFind {α : Type} (pred : α → Bool) (xs : List α) : Option α :=
  xs.find? pred

/--
List any with predicate.

Returns true if any element satisfies the predicate.
-/
def safeAny {α : Type} (pred : α → Bool) (xs : List α) : Bool :=
  xs.any pred

/--
List all with predicate.

Returns true if all elements satisfy the predicate.
-/
def safeAll {α : Type} (pred : α → Bool) (xs : List α) : Bool :=
  xs.all pred

/--
Nat to ℚ conversion helper.

Avoids type inference issues in arithmetic contexts.
-/
def natToQ (n : Nat) : ℚ :=
  (n : ℚ)

/--
Int to ℚ conversion helper.

Avoids type inference issues in arithmetic contexts.
-/
def intToQ (n : Int) : ℚ :=
  (n : ℚ)

end Semantics
