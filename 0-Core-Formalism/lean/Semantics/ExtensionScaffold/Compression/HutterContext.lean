import Semantics.Bind
import ExtensionScaffold.Compression.CodingCost

namespace ExtensionScaffold.Compression.HutterContext

open Semantics

-- Our 4 token vocabulary to keep tests manually verifiable but deeply typed
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
  In First Principles, N-Gram context compression bounds rely on 
  a conditional dependency. Instead of marginal P(X), we calculate P(X|Y).
-/
structure TransitionBin where
  past_token : Token 
  current_token : Token
  -- The observed factual traversal count from the dataset (Q16.16 fractional weight)
  observed_transitions : UInt32 
  -- The model's stubbornly predicted probability of moving from 'past' to 'current' Q16.16
  predicted_freq : UInt32 
  deriving Repr

/--
  evalConditionedCrossEntropy: Determines the overall storage limitation (thermodynamic cost)
  to bind a conditional sequence. Context dynamically shifts the code-lengths.
-/
def evalConditionedCrossEntropy (bins : List TransitionBin) : UInt32 :=
  let totalBits_Q16_16 : UInt64 := bins.foldl (fun sum bin =>
    let bits_for_token := CodingCost.negLog2Q16 bin.predicted_freq
    let weightedBits := (bin.observed_transitions.toUInt64 * bits_for_token.toUInt64) >>> 16
    sum + weightedBits
  ) 0
  totalBits_Q16_16.toUInt32

-- ============================================================================
-- THE CONTEXT EXPERIMENT (N-GRAM GEOMETRY VS NAIVE)
-- ============================================================================

def Q16_1_0 : UInt32 := 0x00010000 
def Q16_0_5 : UInt32 := 0x00008000
def Q16_0_25 : UInt32 := 0x00004000

/-- 
  Experiment A: 
  The text rigorously alternates: (e -> space), (space -> e), repeating forever.
  A marginal uncompressed (naive) model stubbornly ignores the sequence context, 
  always predicting flat probability 0.25 for any token at any time.

  Cost eval: 2 transitions observed at 0.5 freq, each costing 2 bits.
  Expected: (0.5 * 2) + (0.5 * 2) = 2.0 bit expected cost (131072 in Q16.16).
-/
def evalNaiveMarginalModel : UInt32 :=
  let e_to_space := { past_token := .e, current_token := .space, observed_transitions := Q16_0_5, predicted_freq := Q16_0_25 : TransitionBin}
  let space_to_e := { past_token := .space, current_token := .e, observed_transitions := Q16_0_5, predicted_freq := Q16_0_25 : TransitionBin}
  evalConditionedCrossEntropy [e_to_space, space_to_e]

/--
  Experiment B:
  A 1-Gram Context Topologically Deformed model successfully bends to predict 
  the sequence entirely. Because it "knows" what follows mathematically via context, 
  its evaluated probability (Q) becomes a perfectly predictable 1.0 path.

  Cost eval: 2 transitions observed at 0.5 freq, each costing 0 bits.
  Expected: (0.5 * 0) + (0.5 * 0) = 0.0 bit cost (0 in Q16.16) under
  the supplied deterministic conditional model.
-/
def evalContextDeformedModel : UInt32 :=
  let e_to_space := { past_token := .e, current_token := .space, observed_transitions := Q16_0_5, predicted_freq := Q16_1_0 : TransitionBin}
  let space_to_e := { past_token := .space, current_token := .e, observed_transitions := Q16_0_5, predicted_freq := Q16_1_0 : TransitionBin}
  evalConditionedCrossEntropy [e_to_space, space_to_e]

-- Expected: 2.0 Q16_16 bounds => 2 * 65536 = 131072
#eval evalNaiveMarginalModel

-- Expected: 0.0 Q16_16 bounds => 0
#eval evalContextDeformedModel

end ExtensionScaffold.Compression.HutterContext
