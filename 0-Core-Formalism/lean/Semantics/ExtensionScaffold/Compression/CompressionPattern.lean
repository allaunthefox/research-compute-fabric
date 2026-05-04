import Semantics.Bind

namespace ExtensionScaffold.Compression.CompressionPattern

open Semantics

/--
  The finite enumerable alphabet for the Hutter enwik pattern.
  No open strings allowed in core logic decisions.
-/
inductive Token where
  | e
  | t
  | a
  | space
  deriving Repr, BEq, DecidableEq

def Token.toString : Token → String
  | .e => "e"
  | .t => "t"
  | .a => "a"
  | .space => "space"

/--
  A probabilty assigned to a specific token.
  Freq uses Q16_16 fixed point: 0x00010000 = 1.0. 
  Float is strictly banned.
-/
structure ProtocolState where
  token : Token
  freq  : UInt32 -- Q16_16
  deriving Repr

-- ============================================================================
-- DISTRIBUTION INVARIANTS
-- ============================================================================

def isValidFreq (s : ProtocolState) : Bool :=
  s.freq <= 0x00010000

def sumFreqs (l : List ProtocolState) : UInt64 :=
  l.foldl (fun sum s => sum + s.freq.toUInt64) 0

def hasNoDuplicates : List ProtocolState → Bool
  | [] => true
  | (x :: xs) => (xs.all (fun s => s.token != x.token)) && hasNoDuplicates xs

/-- 
  A strictly validated probability distribution over the protocol states.
  Enforces no duplicates, 1.0 sum (in Q16.16), and valid individual frequency parameters.
-/
structure Distribution where
  states : List ProtocolState
  validEq : states.all isValidFreq = true
  normEq  : sumFreqs states == 0x00010000
  nodupsEq : hasNoDuplicates states = true

/-- Invariant extractor for Bind validation. Serializes the token sequence cleanly to preserve structure. -/
def extractStateSignature (dist : Distribution) : String :=
  "dist_" ++ dist.states.foldl (fun acc s => acc ++ s.token.toString ++ "_") ""

def informationalMetric : Metric := {
  cost := 0x00000000,
  tensor := "informational",
  torsion := 0x00000000,
  reference := "hutter_mirror_baseline",
  history_len := 0
}

/--
  l1PatternCost: Computes linear divergence in pure Q16.16 using UInt64 accumulator 
  to prevent silent overflow on larger sets. 
  Note: This explicitly computes a total-variation proxy distance, distinct from standard KL divergence.
-/
def l1PatternCost (left right : Distribution) (_metric : Metric) : UInt32 :=
  let totalDiff : UInt64 := left.states.foldl (fun sum l_state =>
    let r_freq := match right.states.find? (fun r_state => r_state.token == l_state.token) with
                  | some r => r.freq
                  | none => 0x00000000 -- 0.0 Q16_16
    let diff := if l_state.freq > r_freq then l_state.freq - r_freq else r_freq - l_state.freq
    sum + diff.toUInt64
  ) 0
  totalDiff.toUInt32

/--
  informational_bind: The universal primitive applied to the Hutter pattern using validated distributions.
-/
def informationalBind (observed model : Distribution) : Bind Distribution Distribution :=
  bind observed model informationalMetric l1PatternCost extractStateSignature extractStateSignature

-- ============================================================================
-- TESTS AND WITNESSES
-- ============================================================================

-- Q16.16 equivalents:
-- 0x00008000 = 0.5
-- 0x00004000 = 0.25
-- 0x0000C000 = 0.75

def observedPattern : Distribution := {
  states := [
    { token := Token.e, freq := 0x00008000 },
    { token := Token.space, freq := 0x00008000 }
  ],
  validEq := rfl,
  normEq := rfl,
  nodupsEq := rfl
}

def optimalModel : Distribution := {
  states := [
    { token := Token.e, freq := 0x00008000 },
    { token := Token.space, freq := 0x00008000 }
  ],
  validEq := rfl,
  normEq := rfl,
  nodupsEq := rfl
}

def skewedModel : Distribution := {
  states := [
    { token := Token.e, freq := 0x00004000 },
    { token := Token.space, freq := 0x0000C000 }
  ],
  validEq := rfl,
  normEq := rfl,
  nodupsEq := rfl
}

-- Witness 1: Optimal pattern alignment -> cost is 0
#eval (informationalBind observedPattern optimalModel).cost
-- Expected cost: 0

-- Witness 2: Skewed pattern alignment -> cost is 32768 (0.50 L1 divergence)
#eval (informationalBind observedPattern skewedModel).cost
-- Expected cost: 32768

end ExtensionScaffold.Compression.CompressionPattern
