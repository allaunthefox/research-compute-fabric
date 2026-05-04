/-
  PhiRedundancy.lean

  Extension-only 3-stream redundancy scheme for 4-bit nibble units:
    - 3-bit Hachimoji symbol
    - 1-bit recovery flag

  This module uses:
    * π₀ = identity
    * π₁ = affine permutation with step coprime to N
    * π₂ = second affine permutation with different coprime step

  In implementation, the affine steps may be generated from a phi-derived rule.
  Here they are parameters so the core remains total and easy to prove over.
-/
namespace ExtensionScaffold.Compression.PhiRedundancy

/-- A 4-bit nibble unit:
    lower 3 bits = Hachimoji symbol in [0,7]
    upper bit    = recovery bit in [0,1]
-/
structure Nibble where
  raw : UInt8
  deriving Repr, DecidableEq, Inhabited

/-- Extract 3-bit symbol. -/
def symbol (n : Nibble) : UInt8 :=
  n.raw &&& 0x07

/-- Extract recovery bit. -/
def recovery (n : Nibble) : UInt8 :=
  (n.raw >>> 3) &&& 0x01

/-- Construct nibble from symbol and recovery bit. -/
def mkNibble (sym : UInt8) (rec : UInt8) : Nibble :=
  { raw := ((rec &&& 0x01) <<< 3) ||| (sym &&& 0x07) }

/-- Weight used in recovery vote. -/
def weight (n : Nibble) : Nat :=
  if recovery n = 1 then 2 else 1

/-- Modulo helper on Nat. -/
def modN (x n : Nat) : Nat :=
  if n = 0 then 0 else x % n

/-- Affine permutation:
    π(i) = (offset + step * i) mod N

    This is a true permutation when gcd(step, N) = 1.
-/
def affinePerm (n step offset i : Nat) : Nat :=
  modN (offset + step * i) n

/-- Brute-force inverse lookup for a permutation encoded as affine parameters.
    Returns none if no inverse image is found.
-/
def affinePermInv? (n step offset target : Nat) : Option Nat :=
  let rec go (j : Nat) : Option Nat :=
    if j < n then
      if affinePerm n step offset j = target then some j else go (j + 1)
    else
      none
  go 0

/-- Three-stream redundancy descriptor. -/
structure RedundancyScheme where
  n : Nat
  step1 : Nat
  offset1 : Nat
  step2 : Nat
  offset2 : Nat
  deriving Repr

/-- π₀ = identity. -/
def pi0 (sch : RedundancyScheme) (i : Nat) : Nat :=
  modN i sch.n

/-- π₁ = affine low-discrepancy surrogate. -/
def pi1 (sch : RedundancyScheme) (i : Nat) : Nat :=
  affinePerm sch.n sch.step1 sch.offset1 i

/-- π₂ = second affine low-discrepancy surrogate. -/
def pi2 (sch : RedundancyScheme) (i : Nat) : Nat :=
  affinePerm sch.n sch.step2 sch.offset2 i

/-- Inverses. -/
def pi0Inv? (sch : RedundancyScheme) (i : Nat) : Option Nat :=
  if i < sch.n then some i else none

def pi1Inv? (sch : RedundancyScheme) (i : Nat) : Option Nat :=
  affinePermInv? sch.n sch.step1 sch.offset1 i

def pi2Inv? (sch : RedundancyScheme) (i : Nat) : Option Nat :=
  affinePermInv? sch.n sch.step2 sch.offset2 i

/-- Build stream k from logical sequence A. -/
def buildStream0 (sch : RedundancyScheme) (xs : Array Nibble) : Array Nibble :=
  (Array.range sch.n).map (fun j => xs[pi0 sch j]!)

def buildStream1 (sch : RedundancyScheme) (xs : Array Nibble) : Array Nibble :=
  (Array.range sch.n).map (fun j => xs[pi1 sch j]!)

def buildStream2 (sch : RedundancyScheme) (xs : Array Nibble) : Array Nibble :=
  (Array.range sch.n).map (fun j => xs[pi2 sch j]!)

/-- Optional stream slot, to model erasure/damage. -/
abbrev MaybeNibble := Option Nibble

/-- Fetch candidate from stream using inverse map. -/
def fetchCandidate
  (stream : Array MaybeNibble)
  (inv? : Nat → Option Nat)
  (logicalIdx : Nat) : Option Nibble := do
  let j ← inv? logicalIdx
  if j < stream.size then
    stream[j]!
  else
    none

/-- Vote totals for symbols 0..7. -/
def emptyVotes : Array Nat :=
  #[0, 0, 0, 0, 0, 0, 0, 0]

def addVote (votes : Array Nat) (n : Nibble) : Array Nat :=
  let s := (symbol n).toNat
  let w := weight n
  if s < votes.size then
    votes.set! s (votes[s]! + w)
  else
    votes

/-- Argmax over 8 vote counters. -/
def argmax8 (votes : Array Nat) : UInt8 :=
  let rec go (i best : Nat) : Nat :=
    if h : i < votes.size then
      let best' := if votes[i]! > votes[best]! then i else best
      go (i + 1) best'
    else
      best
  UInt8.ofNat (go 1 0)

/-- Recover one nibble from up to 3 candidates. -/
def recoverNibble (c0 c1 c2 : Option Nibble) : Option Nibble :=
  let cs := [c0, c1, c2].filterMap id
  match cs with
  | [] => none
  | _ =>
      let votes := cs.foldl addVote emptyVotes
      let bestSym := argmax8 votes
      let recCount := cs.foldl (fun acc n => acc + (recovery n).toNat) 0
      let bestRec : UInt8 := if recCount >= 2 then 1 else 0
      some (mkNibble bestSym bestRec)

/-- Recover full logical sequence from three possibly damaged streams. -/
def recoverSequence
  (sch : RedundancyScheme)
  (s0 s1 s2 : Array MaybeNibble) : Array (Option Nibble) :=
  (Array.range sch.n).map (fun i =>
    let c0 := fetchCandidate s0 (pi0Inv? sch) i
    let c1 := fetchCandidate s1 (pi1Inv? sch) i
    let c2 := fetchCandidate s2 (pi2Inv? sch) i
    recoverNibble c0 c1 c2
  )

/-- Example Hachimoji symbol sequence packed into nibbles. -/
def exampleSeq : Array Nibble :=
  #[
    mkNibble 0 1,
    mkNibble 1 0,
    mkNibble 2 1,
    mkNibble 3 0,
    mkNibble 4 1,
    mkNibble 5 0,
    mkNibble 6 1,
    mkNibble 7 0
  ]

/-- Example scheme with affine permutations over eight positions. -/
def exampleScheme : RedundancyScheme :=
  { n := 8, step1 := 5, offset1 := 1, step2 := 3, offset2 := 2 }

/-- Build example streams. -/
def ex0 : Array Nibble := buildStream0 exampleScheme exampleSeq
def ex1 : Array Nibble := buildStream1 exampleScheme exampleSeq
def ex2 : Array Nibble := buildStream2 exampleScheme exampleSeq

/-- Damage one element in each recovery stream. -/
def ex0d : Array (Option Nibble) := ex0.map some
def ex1d : Array (Option Nibble) := (ex1.map some).set! 2 none
def ex2d : Array (Option Nibble) := (ex2.map some).set! 5 none

/-- Minimality note:
    three streams are the minimal robust scheme:
    primary + recovery + adjudicator.
-/
def minimalRobustStreamCount : Nat := 3

#eval exampleSeq
#eval ex0
#eval ex1
#eval ex2
#eval recoverSequence exampleScheme ex0d ex1d ex2d

end ExtensionScaffold.Compression.PhiRedundancy
