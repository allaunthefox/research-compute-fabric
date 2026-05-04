import Semantics.Bind
import ExtensionScaffold.Compression.CodingCost

namespace ExtensionScaffold.Compression.HutterUncompressed

open Semantics

/--
  Represents a single symbol's informatic boundary.
  Instead of a giant List of 256 Fin types, we evaluate statistically via bins.
-/
structure TokenBin where
  token_id : Nat
  observed_freq : UInt32 -- Frequency of this token in the actual data (Q16.16)
  predicted_freq : UInt32 -- Frequency stubbornly predicted by the model (Q16.16)
  deriving Repr

/--
  evalCrossEntropy: The foundational thermodynamic cost of generating a sequence 
  given a rigid model. It evaluates sum(P(x) * -log2(Q(x))).
  Output is the exact bit cost bounded in Q16.16 fixed point space.
-/
def evalCrossEntropy (bins : List TokenBin) : UInt32 :=
  let totalBits_Q16_16 : UInt64 := bins.foldl (fun sum bin =>
    let bits_for_token := CodingCost.negLog2Q16 bin.predicted_freq
    -- Cost = P * bits. Both are Q16.16 here, so we shift back down to Q16.16.
    let weightedBits := (bin.observed_freq.toUInt64 * bits_for_token.toUInt64) >>> 16
    sum + weightedBits
  ) 0
  totalBits_Q16_16.toUInt32

-- ============================================================================
-- THE UNCOMPRESSED HUTTER BINDING (FIRST PRINCIPLES)
-- ============================================================================

-- Q16.16 Definitions
def Q16_1_0 : UInt32 := 0x00010000 
def Q16_1_256 : UInt32 := 0x00000100 -- Uncompressed naive baseline

/--
  Scenario A: The empirical data is perfectly uniformly distributed (a true random hash).
  Observed = 1/256 for all 256 tokens.
  Model = 1/256 for all 256 tokens.
-/
def evalUniformDataset : UInt32 :=
  -- Simulating the fold across 256 identical bins: P = 1/256, Q = 1/256
  -- sum_{i=1..256} (1/256 * 8) = 8.0 
  -- In Q16.16: sum_{i=1..256} (256 * 8) = 256 * 256 * 8 = 65536 * 8 = 0x00080000
  let singleBin := { token_id := 0, observed_freq := Q16_1_256, predicted_freq := Q16_1_256 : TokenBin }
  let allBins := List.replicate 256 singleBin
  evalCrossEntropy allBins

/--
  Scenario B: The empirical data is extremely ordered/skewed (e.g. 100% of the byte stream is just the letter 'A').
  Observed = 1.0 for token 65, 0.0 for the other 255 tokens.
  Model = 1/256 for all 256 tokens (because we are stubbornly not compressing).
-/
def evalHighlyOrderedDataset : UInt32 :=
  let activeBin := { token_id := 65, observed_freq := Q16_1_0, predicted_freq := Q16_1_256 : TokenBin }
  let emptyBin := { token_id := 0, observed_freq := 0, predicted_freq := Q16_1_256 : TokenBin }
  let allBins := activeBin :: List.replicate 255 emptyBin
  evalCrossEntropy allBins


-- ============================================================================
-- EVALUATING FIRST PRINCIPLES
-- ============================================================================

-- Both MUST mathematically converge exactly to 8.0 bits in Q16.16 (which is 8 * 65536 = 524288 / 0x00080000)
-- because the code-length of an uncompressed sequence under a uniform model is completely 
-- decoupled from the underlying signal's true entropy.

#eval evalUniformDataset
#eval evalHighlyOrderedDataset

end ExtensionScaffold.Compression.HutterUncompressed
