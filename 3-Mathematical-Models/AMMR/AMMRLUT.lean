import Semantics.Spectrum

open Semantics
open Semantics.Spectrum

namespace AVMR

/-!
# AMMRLUT

An evolving lookup-table layer for shell-documented forward computation.

Purpose:
- avoid repeated long-history scans,
- cache shell/event-local bias for stochastic computation,
- provide a reusable addressing scheme for zipper-style forward steps.

This file is intentionally conservative:
- it does not assume a particular hash map backend,
- it uses an association-list style table first,
- and it flags the theorem targets still missing.
-/

inductive EventType
  | a | t | g | c
  deriving Repr, DecidableEq

structure ShellState where
  n : Nat
  k : Nat
  a : Nat
  b : Nat
  deriving Repr, DecidableEq

structure TipCoord where
  mass : Int
  polarity : Int
  deriving Repr, DecidableEq

/-- Integer square root via Newton iteration. -/
partial def isqrt (n : Nat) : Nat :=
  if n <= 1 then
    n
  else
    let rec newton (guess : Nat) : Nat :=
      let next := (guess + n / guess) / 2
      if next >= guess then guess else newton next
    newton (n / 2)

def shellState (n : Nat) : ShellState :=
  let k := isqrt n
  let a := n - k*k
  let b := (k+1)*(k+1) - n
  { n := n, k := k, a := a, b := b }

def classifyEvent (s : ShellState) : Option EventType :=
  let k := s.k
  let n := s.n
  if n = k*k then some .a
  else if n = k*k + k then some .g
  else if n = k*k + k + 1 then some .c
  else if n = (k+1)*(k+1) - 1 then some .t
  else none

def tipCoord (s : ShellState) : TipCoord :=
  { mass := Int.ofNat (s.a * s.b)
  , polarity := Int.ofNat s.a - Int.ofNat s.b }

/-- Shell/event-local key for evolving cached bias. -/
structure LUTKey where
  k : Nat
  a : Nat
  b : Nat
  event : EventType
  deriving Repr, DecidableEq

/-- Cached local bias package.

Interpretation:
- lockValue: most recent snapped/locked forward value
- support: accumulated support for reusing this region
- recurrenceBias: local bias toward revisitation / reinforcement
- nextIndexHint: suggested next forward index
- hitCount: number of successful reuses
-/
structure LUTEntry where
  lockValue : Q16_16
  support : Q16_16
  recurrenceBias : Q16_16
  nextIndexHint : Nat
  hitCount : Nat
  deriving Repr, DecidableEq

/-- A simple evolving table using an association list.
Replaceable later with a hash map backend once the key semantics stabilize.
-/
structure EvolvingLUT where
  entries : List (LUTKey × LUTEntry)
  deriving Repr, DecidableEq

namespace EvolvingLUT

def empty : EvolvingLUT := { entries := [] }

/-- Linear lookup in the current prototype table. -/
def lookup (lut : EvolvingLUT) (key : LUTKey) : Option LUTEntry :=
  match lut.entries.find? (fun kv => kv.1 = key) with
  | some (_, entry) => some entry
  | none => none

/-- Insert or replace one entry. -/
def upsert (lut : EvolvingLUT) (key : LUTKey) (entry : LUTEntry) : EvolvingLUT :=
  let filtered := lut.entries.filter (fun kv => kv.1 ≠ key)
  { entries := (key, entry) :: filtered }

/-- Number of cached keys. -/
def size (lut : EvolvingLUT) : Nat :=
  lut.entries.length

end EvolvingLUT

/-- Build a shell/event key from a forward index when the index lands on an active event. -/
def keyAt (n : Nat) : Option LUTKey := do
  let s := shellState n
  let e ← classifyEvent s
  pure { k := s.k, a := s.a, b := s.b, event := e }

/-- Default cold-start entry for an unseen shell/event key. -/
def defaultEntry (n : Nat) : LUTEntry :=
  { lockValue := Q16_16.ofInt (Int.ofNat n)
  , support := Q16_16.zero
  , recurrenceBias := Q16_16.zero
  , nextIndexHint := n + 1
  , hitCount := 0 }

/-- Convert tip geometry into a small local support contribution. -/
def supportFromTip (tip : TipCoord) : Q16_16 :=
  let m := Q16_16.ofInt tip.mass
  let p := Q16_16.ofInt tip.polarity
  Q16_16.add m p

/-- Local recurrence bias from shell imbalance.
Smaller imbalance means easier revisitation / reuse.
-/
def recurrenceBiasFromShell (s : ShellState) : Q16_16 :=
  let imbalance := Int.natAbs (Int.ofNat s.a - Int.ofNat s.b)
  if imbalance = 0 then Q16_16.ofInt 4
  else if imbalance = 1 then Q16_16.ofInt 3
  else if imbalance = 2 then Q16_16.ofInt 2
  else Q16_16.one

/-- Update one entry after a successful forward lock at index n. -/
def evolveEntry (n : Nat) (entry : LUTEntry) : LUTEntry :=
  let s := shellState n
  let tip := tipCoord s
  { lockValue := Q16_16.ofInt (Int.ofNat n)
  , support := Q16_16.add entry.support (supportFromTip tip)
  , recurrenceBias := Q16_16.add entry.recurrenceBias (recurrenceBiasFromShell s)
  , nextIndexHint := n + 1
  , hitCount := entry.hitCount + 1 }

/-- Feed one forward index into the LUT.
If the index is not an active shell event, the LUT is unchanged.
-/
def feedIndex (lut : EvolvingLUT) (n : Nat) : EvolvingLUT :=
  match keyAt n with
  | none => lut
  | some key =>
      let base := match EvolvingLUT.lookup lut key with
        | some entry => entry
        | none => defaultEntry n
      EvolvingLUT.upsert lut key (evolveEntry n base)

/-- Read a stochastic bias package for a forward index.
Returns the cached entry when available, otherwise the cold-start default.
-/
def biasAt (lut : EvolvingLUT) (n : Nat) : Option LUTEntry := do
  let key ← keyAt n
  match EvolvingLUT.lookup lut key with
  | some entry => pure entry
  | none => pure (defaultEntry n)

/-- Batch-feed a finite list of forward indices into the LUT. -/
def feedIndices (lut : EvolvingLUT) (ns : List Nat) : EvolvingLUT :=
  ns.foldl feedIndex lut

/-- Simple stochastic seed hint derived from the cached entry.
This is intentionally lightweight: support + recurrence bias act as the fast reusable guide.
-/
def seedHint (entry : LUTEntry) : Q16_16 :=
  Q16_16.add entry.support entry.recurrenceBias

/-- A documented forward shell step.
This is the shell-ledger record that can later be passed to zipper or physics layers.
-/
structure ForwardShellStep where
  index : Nat
  shellK : Nat
  offsetA : Nat
  offsetB : Nat
  eventClass : EventType
  lockValue : Q16_16
  support : Q16_16
  recurrenceBias : Q16_16
  nextIndexHint : Nat
  deriving Repr, DecidableEq

/-- Materialize a documented forward step from the LUT.
Returns none when the index is not an active shell event.
-/
def documentStep (lut : EvolvingLUT) (n : Nat) : Option ForwardShellStep := do
  let s := shellState n
  let e ← classifyEvent s
  let entry := match biasAt lut n with
    | some x => x
    | none => defaultEntry n
  pure {
    index := n
    shellK := s.k
    offsetA := s.a
    offsetB := s.b
    eventClass := e
    lockValue := entry.lockValue
    support := entry.support
    recurrenceBias := entry.recurrenceBias
    nextIndexHint := entry.nextIndexHint
  }

/-- The LUT should never shrink when only feeding indices. -/
theorem feedIndices_monotone_size :
  ∀ (lut : EvolvingLUT) (ns : List Nat),
    lut.entries.length ≤ (feedIndices lut ns).entries.length := by
  intro lut ns
  induction ns generalizing lut with
  | nil => simp [feedIndices]
  | cons n rest ih =>
      simp [feedIndices]
      have hstep : lut.entries.length ≤ (feedIndex lut n).entries.length := by
        unfold feedIndex
        split
        · simp
        · rename_i key
          unfold EvolvingLUT.upsert
          by_cases h : EvolvingLUT.lookup lut key = none
          · simp [EvolvingLUT.lookup, h]
          · simp
      exact Nat.le_trans hstep (ih (feedIndex lut n))

/-- The intended acceleration claim is still only a target:
reusing a cached shell/event key should make future stochastic lookup cheaper than long-history scanning.
-/
theorem lut_reuse_accelerates_target :
  ∀ (lut : EvolvingLUT) (n : Nat), True := by
  intro lut n
  trivial

end AVMR
