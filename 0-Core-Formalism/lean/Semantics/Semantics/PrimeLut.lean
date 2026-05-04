/- Prime Number Lookup Table (LUT)

  Generated from: https://data.kennethjorgensen.com/primes/primes.html
  
  This module provides a constant-time lookup table for prime numbers
  used in the research stack for:
  - Shell geometry calculations
  - Resonance frequency selection
  - Cryptographic parameter generation
  - Hash table sizing
  
  Per AGENTS.md §1.4: Uses UInt64 for hardware-native indexing.
  Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

namespace Semantics.PrimeLut

/-- Safe array lookup by natural index. -/
def arrayGet? (xs : Array α) (n : Nat) : Option α :=
  if h : n < xs.size then
    some (xs[n]'h)
  else
    none

/-- Prime number entry with metadata -/
structure PrimeEntry where
  index : UInt64    -- Sequential index in the prime list
  value : UInt64    -- The prime number itself
  gap   : UInt16    -- Gap from previous prime (for pattern analysis)
  deriving Repr, BEq

/-- First 168 primes (all primes < 1000) for shell geometry -/
def firstPrimes : Array UInt64 := #[
  2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
  31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
  73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
  127, 131, 137, 139, 149, 151, 157, 163, 167, 173,
  179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
  233, 239, 241, 251, 257, 263, 269, 271, 277, 281,
  283, 293, 307, 311, 313, 317, 331, 337, 347, 349,
  353, 359, 367, 373, 379, 383, 389, 397, 401, 409,
  419, 421, 431, 433, 439, 443, 449, 457, 461, 463,
  467, 479, 487, 491, 499, 503, 509, 521, 523, 541,
  547, 557, 563, 569, 571, 577, 587, 593, 599, 601,
  607, 613, 617, 619, 631, 641, 643, 647, 653, 659,
  661, 673, 677, 683, 691, 701, 709, 719, 727, 733,
  739, 743, 751, 757, 761, 769, 773, 787, 797, 809,
  811, 821, 823, 827, 829, 839, 853, 857, 859, 863,
  877, 881, 883, 887, 907, 911, 919, 929, 937, 941,
  947, 953, 967, 971, 977, 983, 991, 997
]

/-- Lookup prime by index (0-indexed) -/
def primeAt (n : UInt64) : Option UInt64 :=
  if n < firstPrimes.size.toUInt64 then
    arrayGet? firstPrimes n.toNat
  else
    none

/-- Get the nth prime (1-indexed, mathematical convention) -/
def nthPrime (n : UInt64) : Option UInt64 :=
  primeAt (n - 1)

/-- Check if a number is in the prime LUT -/
def isPrimeInLut (x : UInt64) : Bool :=
  firstPrimes.contains x

/-- Find the largest prime ≤ x by scanning the finite LUT. -/
def primeFloor (x : UInt64) : Option UInt64 :=
  firstPrimes.toList.foldl
    (fun best p => if p ≤ x then some p else best)
    none

/-- Prime shell sizes for resonance calculations -/
def shellPrimes : Array UInt64 := #[
  2, 3, 5, 7, 11, 13, 17, 19, 23, 29,    -- Shell 0-9
  31, 37, 41, 43, 47, 53, 59, 61, 67, 71,  -- Shell 10-19
  73, 79, 83, 89, 97, 101, 103, 107, 109, 113  -- Shell 20-29
]

/-- Get shell prime for a given shell index -/
def shellPrime (shellIdx : UInt8) : UInt64 :=
  let idx := shellIdx.toNat % shellPrimes.size
  match arrayGet? shellPrimes idx with
  | some p => p
  | none => 2

/-- Twin prime pairs from the LUT -/
def twinPrimes : Array (UInt64 × UInt64) := #[
  (3, 5), (5, 7), (11, 13), (17, 19), (29, 31),
  (41, 43), (59, 61), (71, 73), (101, 103), (107, 109),
  (137, 139), (149, 151), (179, 181), (191, 193), (197, 199),
  (227, 229), (239, 241), (269, 271), (281, 283), (311, 313),
  (347, 349), (419, 421), (431, 433), (461, 463), (521, 523),
  (569, 571), (599, 601), (617, 619), (641, 643), (659, 661),
  (809, 811), (821, 823), (827, 829), (857, 859), (877, 881)
]

/-- Safe prime lookup (p where (p-1)/2 is also prime) -/
def safePrimes : Array UInt64 := #[
  5, 7, 11, 23, 47, 59, 83, 107, 167, 179,
  227, 263, 347, 359, 383, 467, 479, 503, 563, 587,
  719, 839, 863, 887, 983
]

/-- Get a safe prime for cryptographic parameters -/
def safePrimeAt (idx : UInt8) : UInt64 :=
  let i := idx.toNat % safePrimes.size
  match arrayGet? safePrimes i with
  | some p => p
  | none => 5

/- #eval examples for verification -/
#eval primeAt 0    -- some 2
#eval primeAt 10   -- some 31
#eval nthPrime 1   -- some 2
#eval nthPrime 26  -- some 101
#eval isPrimeInLut 997  -- true
#eval isPrimeInLut 1000 -- false
#eval shellPrime 5   -- 13
#eval shellPrime 25  -- 101
#eval safePrimeAt 0  -- 5
#eval primeFloor 100  -- some 97

end Semantics.PrimeLut
