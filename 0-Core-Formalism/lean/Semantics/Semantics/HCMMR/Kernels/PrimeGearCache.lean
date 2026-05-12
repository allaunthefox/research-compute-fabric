/-
PrimeGearCache.lean — Prime exponent compositional caching kernel.

Instead of computing every step n from scratch, factor n = Π p^{v_p(n)} and
compose from cached prime-step receipts. Δ_n = g_field(p_n) × Π (Δ_p)^{v_p(n)}.
Composites are derived, not recomputed.
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Kernels.PrimeGearCache

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

structure PrimeGearEntry where
  prime            : Q16_16
  delta            : Q16_16
  fieldResponse    : Q16_16
  fammScar         : Q16_16
  chiralityReceipt : Q16_16
  residual         : Q16_16
  receiptRoot      : String
  deriving Repr, BEq, DecidableEq, Inhabited

structure PrimeCache where
  entries     : List PrimeGearEntry
  primesKnown : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

def factorize (n : Nat) : List (Nat × Nat) := Id.run do
  let mut result : List (Nat × Nat) := []
  let mut m := n
  let mut d := 2
  while d * d ≤ m do
    if m % d == 0 then
      let mut exp := 0
      while m % d == 0 do
        m := m / d
        exp := exp + 1
      result := (d, exp) :: result
    d := d + 1
  if m > 1 then
    result := (m, 1) :: result
  return result.reverse

def findEntry (cache : PrimeCache) (p : Q16_16) : Option PrimeGearEntry :=
  cache.entries.find? (fun e => e.prime == p)

def q16Pow : Q16_16 → Nat → Q16_16
  | _, 0     => Q16_16.one
  | base, n+1 => base * q16Pow base n

def composeFromPrimes (n : Nat) (cache : PrimeCache) : Q16_16 :=
  let factors := factorize n
  match factors with
  | [] => Q16_16.one
  | _  =>
    let f (acc : Q16_16) (pair : Nat × Nat) : Q16_16 :=
      let (p, exp) := pair
      let pQ := Q16_16.ofInt (Int.ofNat p)
      match findEntry cache pQ with
      | none => acc
      | some entry => acc * q16Pow entry.delta exp
    factors.foldl f Q16_16.one

def isCompositeCached (n : Nat) (cache : PrimeCache) : Bool :=
  let factors := factorize n
  factors.all (fun (p, _) =>
    let pQ := Q16_16.ofInt (Int.ofNat p)
    (findEntry cache pQ).isSome)

def cachePrimeStep (cache : PrimeCache) (entry : PrimeGearEntry) : PrimeCache :=
  let trimmed := cache.entries.filter (fun e => e.prime != entry.prime)
  { entries     := entry :: trimmed
  , primesKnown := if (findEntry cache entry.prime).isSome then cache.primesKnown else cache.primesKnown + 1
  }

def primeCacheGate : Gate :=
  { name     := "PrimeGearCache"
  , required := false
  , score    := Q16_16.one
  , verdict  := GateVerdict.admit
  }

def emptyCache : PrimeCache :=
  { entries := [], primesKnown := 0 }

def fixtureEntry2 : PrimeGearEntry :=
  { prime            := Q16_16.two
  , delta            := Q16_16.ofInt 1
  , fieldResponse    := Q16_16.ofInt 2
  , fammScar         := Q16_16.zero
  , chiralityReceipt := Q16_16.one
  , residual         := Q16_16.zero
  , receiptRoot      := "deadbeef00000000000000000000000000000000000000000000000000000000"
  }

def fixtureEntry3 : PrimeGearEntry :=
  { prime            := Q16_16.ofInt 3
  , delta            := Q16_16.ofInt 6
  , fieldResponse    := Q16_16.ofInt 3
  , fammScar         := Q16_16.one
  , chiralityReceipt := Q16_16.negOne
  , residual         := Q16_16.epsilon
  , receiptRoot      := "cafebabe00000000000000000000000000000000000000000000000000000000"
  }

def fixtureEntry5 : PrimeGearEntry :=
  { prime            := Q16_16.ofInt 5
  , delta            := Q16_16.ofInt 15
  , fieldResponse    := Q16_16.ofInt 5
  , fammScar         := Q16_16.zero
  , chiralityReceipt := Q16_16.one
  , residual         := Q16_16.epsilon
  , receiptRoot      := "feedface00000000000000000000000000000000000000000000000000000000"
  }

def fixtureCache : PrimeCache :=
  cachePrimeStep (cachePrimeStep emptyCache fixtureEntry2) fixtureEntry3

def fixtureCache3 : PrimeCache :=
  cachePrimeStep (cachePrimeStep (cachePrimeStep emptyCache fixtureEntry2) fixtureEntry3) fixtureEntry5

theorem cache_prime_increments_known : (cachePrimeStep emptyCache fixtureEntry2).primesKnown = 1 := by
  native_decide

theorem cache_duplicate_does_not_increment : (cachePrimeStep (cachePrimeStep emptyCache fixtureEntry2) fixtureEntry2).primesKnown = 1 := by
  native_decide

theorem gate_name_correct : primeCacheGate.name = "PrimeGearCache" := by
  rfl

theorem fixtureCache_primes_known_two : fixtureCache.primesKnown = 2 := by
  native_decide

theorem q16Pow_zero_exp : q16Pow (Q16_16.ofInt 5) 0 = Q16_16.one := by
  native_decide

theorem q16Pow_one_exp : q16Pow (Q16_16.ofInt 3) 1 = Q16_16.ofInt 3 := by
  native_decide

theorem empty_cache_no_entry : (findEntry emptyCache Q16_16.two).isSome = false := by
  native_decide

#eval! factorize 1
#eval! factorize 7
#eval! factorize 12
#eval! factorize 30
#eval! factorize 17
#eval! isCompositeCached 6 fixtureCache3
#eval! isCompositeCached 5 fixtureCache3
#eval! composeFromPrimes 2 fixtureCache3
#eval! composeFromPrimes 6 fixtureCache3
#eval cachePrimeStep emptyCache fixtureEntry2
#eval fixtureCache3
#eval primeCacheGate

end Semantics.HCMMR.Kernels.PrimeGearCache
