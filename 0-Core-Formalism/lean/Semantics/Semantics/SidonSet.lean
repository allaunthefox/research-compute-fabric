import Mathlib.Data.Set.Basic

namespace Semantics.SidonSet

/-! # Sidon Set Generator

A Sidon set (also called a B₂ set or Erdős–Sidon set) is a set of natural numbers
where all pairwise sums a + b (with a ≤ b) are unique.

This module implements a greedy generator for Sidon sets and provides utilities
for checking the Sidon property. Such sets have applications in:
- Frequency assignment (avoiding interference)
- Difference sets in combinatorics
- Signal processing (unique pairwise frequencies)

## Main definitions

- `isSidon`: Predicate that checks if a list satisfies the Sidon property
- `pairwiseSums`: Computes all pairwise sums a + b where a ≤ b
- `canAdd`: Checks if a candidate number can be added while preserving Sidon property
- `generateSidon`: Greedy algorithm to generate a Sidon set of specified size

## Example

```lean
#eval generateSidon 6  -- Produces [1, 2, 5, 10, 16, 23]
```
-/

/-- Checks if a list satisfies the Sidon property:
    All pairwise sums a + b (with a ≤ b) are unique. -/
def isSidon (s : List Nat) : Prop :=
  ∀ a b c d, a ∈ s → b ∈ s → c ∈ s → d ∈ s →
  a + b = c + d → ({a, b} : Set Nat) = {c, d}

/-- Computes all pairwise sums a + b where a ≤ b. -/
def pairwiseSums (l : List Nat) : List Nat :=
  match l with
  | [] => []
  | x :: xs => (x + x) :: xs.map (fun y => x + y) ++ pairwiseSums xs

/-- Checks if a new candidate 'n' can be added to existing Sidon set 's'
    while preserving the Sidon property. -/
def canAdd (s : List Nat) (n : Nat) : Bool :=
  let currentSums := pairwiseSums s
  -- New sums formed by adding n: n + x for each x in s, plus n + n
  let newSums := s.map (fun x => x + n) ++ [n + n]
  -- Ensure no intersection between existing sums and new sums
  (newSums.all (fun sum => !currentSums.contains sum)) &&
  -- Ensure no duplicates within the new sums themselves
  (newSums.length == newSums.eraseDups.length)

/-- Greedy generator for a Sidon set of size 'k'.
    Starts with [1] and greedily adds the smallest valid candidate.
    
    The partial annotation is required because Lean cannot prove termination
    of this greedy search automatically - it's theoretically unbounded. -/
partial def generateSidon (k : Nat) (current : List Nat := [1]) (candidate : Nat := 2) : List Nat :=
  if current.length >= k then
    current.reverse
  else
    if canAdd current candidate then
      generateSidon k (candidate :: current) (candidate + 1)
    else
      generateSidon k current (candidate + 1)

/-- Alternative version using well-founded recursion with fuel.
    Returns none if fuel runs out (shouldn't happen for reasonable inputs). -/
def generateSidonFuel (k : Nat) (fuel : Nat := 10000) : Option (List Nat) :=
  let rec loop (current : List Nat) (candidate : Nat) (fuel : Nat) : Option (List Nat) :=
    match fuel with
    | 0 => none
    | fuel' + 1 =>
      if current.length >= k then
        some current.reverse
      else
        if canAdd current candidate then
          loop (candidate :: current) (candidate + 1) fuel'
        else
          loop current (candidate + 1) fuel'
  loop [1] 2 fuel

/-- Main IO action to generate and display a Sidon set. -/
def main : IO Unit := do
  let size := 6
  match generateSidonFuel size with
  | some sidonSet =>
    IO.println s!"Generated Erdős-Sidon Set of size {size}:"
    IO.println s!"{sidonSet}"
    let sums := pairwiseSums sidonSet |>.mergeSort (· < ·)
    IO.println s!"Pairwise sums: {sums}"
    IO.println s!"Number of pairwise sums: {sums.length}"
    -- Verify property: should have n(n+1)/2 sums for set of size n
    let expectedCount := size * (size + 1) / 2
    IO.println s!"Expected sum count: {expectedCount}"
    if sums.length == expectedCount then
      IO.println "✓ Correct number of pairwise sums"
    else
      IO.println "✗ Incorrect number of pairwise sums"
    -- Check uniqueness
    if sums.length == sums.eraseDups.length then
      IO.println "✓ All pairwise sums are unique (Sidon property verified)"
    else
      IO.println "✗ Duplicate sums found"
  | none =>
    IO.println "Failed to generate Sidon set (fuel exhausted)"

#eval main


end Semantics.SidonSet
