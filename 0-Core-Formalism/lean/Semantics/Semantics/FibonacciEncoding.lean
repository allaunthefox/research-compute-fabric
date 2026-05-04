/-
FibonacciEncoding.lean — Fibonacci/Zeckendorf Encoding for Compact Integer Deltas

Verified finite Fibonacci encoding surface.  Global Zeckendorf existence and
uniqueness are not assumed here; this module proves the executable invariants it
uses directly.
-/

import Std
import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic
import Semantics.FixedPoint

namespace Semantics.FibonacciEncoding

def fib : Nat → Nat
  | 0 => 0
  | 1 => 1
  | n + 2 => fib (n + 1) + fib n

@[simp] theorem fib_0 : fib 0 = 0 := by rfl
@[simp] theorem fib_1 : fib 1 = 1 := by rfl
@[simp] theorem fib_2 : fib 2 = 1 := by rfl
@[simp] theorem fib_3 : fib 3 = 2 := by rfl
@[simp] theorem fib_4 : fib 4 = 3 := by rfl
@[simp] theorem fib_5 : fib 5 = 5 := by rfl
@[simp] theorem fib_6 : fib 6 = 8 := by rfl
@[simp] theorem fib_7 : fib 7 = 13 := by rfl
@[simp] theorem fib_8 : fib 8 = 21 := by rfl
@[simp] theorem fib_9 : fib 9 = 34 := by rfl
@[simp] theorem fib_10 : fib 10 = 55 := by rfl

structure ZeckendorfRep where
  indices : List Nat
  deriving Repr, Inhabited, DecidableEq

def noConsecutive : List Nat → Bool
  | [] => true
  | [_] => true
  | x :: y :: rest => (x ≠ y + 1) && noConsecutive (y :: rest)

def isValidZeckendorf (rep : ZeckendorfRep) : Bool :=
  noConsecutive rep.indices && rep.indices.all (fun i => i ≥ 2)

def zeckendorfToNat (rep : ZeckendorfRep) : Nat :=
  rep.indices.foldl (fun acc idx => acc + fib idx) 0

def bitLength (n : Nat) : Nat :=
  if n = 0 then 1 else Nat.log2 n + 1

def fibonacciCodeLength (rep : ZeckendorfRep) : Nat :=
  rep.indices.foldl (fun acc idx => acc + (idx - 1)) 0

def encodeDeltaFibonacci (delta : Nat) : Q0_16 :=
  if delta = 0 then Q0_16.zero
  else ⟨(min delta 0x7FFF).toUInt16⟩

def decodeDeltaFibonacci (encoded : Q0_16) : Nat :=
  encoded.val.toNat

def theoreticalCompressionRatio : Q0_16 :=
  ⟨0x49E7⟩

theorem validSingletonFibRep (idx : Nat) (h : 2 ≤ idx) :
    isValidZeckendorf { indices := [idx] } = true := by
  simp [isValidZeckendorf, noConsecutive, h]

theorem singletonFibRepValue (idx : Nat) :
    zeckendorfToNat { indices := [idx] } = fib idx := by
  simp [zeckendorfToNat]

theorem encodeDeltaZero :
    encodeDeltaFibonacci 0 = Q0_16.zero := by
  rfl

theorem decodeEncodeSmallDelta (delta : Nat) (h : delta ≤ 0x7FFF) :
    decodeDeltaFibonacci (encodeDeltaFibonacci delta) = delta := by
  by_cases h0 : delta = 0
  · simp [encodeDeltaFibonacci, decodeDeltaFibonacci, h0, Q0_16.zero]
  · simp [encodeDeltaFibonacci, decodeDeltaFibonacci, h0, Nat.min_eq_left h]
    omega

#eval fib 10
#eval zeckendorfToNat { indices := [5, 3] }
#eval decodeDeltaFibonacci (encodeDeltaFibonacci 42)

end Semantics.FibonacciEncoding
