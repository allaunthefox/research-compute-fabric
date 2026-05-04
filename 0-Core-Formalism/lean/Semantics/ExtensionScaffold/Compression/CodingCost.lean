namespace ExtensionScaffold.Compression.CodingCost

/--
  The Q16.16 representation of 1.0.
-/
def q16One : UInt32 := 0x00010000

/--
  A capped 16-bit coding penalty in Q16.16. This is used for zero-probability
  events so the extension experiments stay finite and deterministic.
-/
def maxCostQ16 : UInt32 := 0x00100000

/--
  Returns the octave index `k` such that:
    q16One >> (k + 1) <= p < q16One >> k

  This is the integer part of `-log2(p)` over Q16.16 probabilities.
-/
def octaveOfProbability (p : UInt32) : Nat :=
  let rec go (k : Nat) (threshold : UInt32) : Nat :=
    if k >= 15 then
      15
    else if p >= threshold then
      k
    else
      go (k + 1) (threshold >>> 1)
  if p >= q16One then 0 else go 0 (q16One >>> 1)

/--
  The upper power-of-two probability bound for a given octave.
-/
def octaveUpper : Nat → UInt32
  | 0 => q16One
  | k + 1 => octaveUpper k >>> 1

/--
  Left shift by a natural number using repeated single-bit shifts.
-/
def shiftLeftNat : UInt64 → Nat → UInt64
  | x, 0 => x
  | x, k + 1 => shiftLeftNat (x <<< 1) k

/--
  A monotone fixed-point proxy for `-log2(p)` over Q16.16 probabilities.

  The integer bit cost comes from the power-of-two octave containing `p`.
  Inside each octave, we interpolate linearly using only shifts because each
  interval width is itself a power of two.
-/
def negLog2Q16 (p : UInt32) : UInt32 :=
  if p == 0 then
    maxCostQ16
  else if p >= q16One then
    0
  else
    let octave := octaveOfProbability p
    let upper := octaveUpper octave
    let gap := upper - p
    let fractional : UInt32 := (shiftLeftNat gap.toUInt64 (octave + 1)).toUInt32
    ((UInt32.ofNat octave) <<< 16) + fractional

-- Anchor witnesses for the coding-cost scale.
#eval negLog2Q16 0x00010000
#eval negLog2Q16 0x00008000
#eval negLog2Q16 0x00004000
#eval negLog2Q16 0x00006000

end ExtensionScaffold.Compression.CodingCost
