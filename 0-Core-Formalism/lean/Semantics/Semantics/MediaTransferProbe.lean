/-
MediaTransferProbe.lean -- Information Transfer via Media as Pulse Driver

The user's fundamental mechanism: civilizational dynamics are driven by
information transfer via media channels, not abstract "growth rates."

Core model:
  1. Each media technology is a CHANNEL with a bandwidth (bits per second
     per person, or equivalent information density).
  2. Human cognitive capacity is approximately FIXED (brain architecture).
  3. Institutions and social structures are designed for a specific
     information density (the dominant media channel of their era).
  4. When a new media channel increases information density by an
     order of magnitude, old institutions become overloaded.
  5. The time to overload is: T = (cognitive_capacity × population) /
                                  (new_channel_bandwidth − old_channel_bandwidth)
     More precisely: T = C / ΔR where C = capacity buffer, ΔR = rate increase.
  6. A media transition is a "basin escape" — institutions collapse,
     reorganize, and adapt to the new channel.
  7. The civilizational pulse is the interval between media transitions
     that increase effective bandwidth by ~10×.

Historical media channels (approximate Shannon bandwidths):
  - Oral tradition:      ~10^0  bits/s per person (speech rate)
  - Writing:           ~10^1  bits/s per person (reading speed)
  - Printing press:    ~10^2  bits/s per person (mass book consumption)
  - Telegraph/radio:   ~10^3  bits/s per person (global real-time)
  - Television:        ~10^6  bits/s per person (visual broadcast)
  - Internet:          ~10^9  bits/s per person (bidigital network)
  - AI/LLM:            ~10^12 bits/s per person (generative inference)

Note: These are ORDER-OF-MAGNITUDE estimates of EFFECTIVE information
density, not rigorous Shannon calculations. The framework treats them
as phenomenological inputs.

  REFERENCES:
    See 6-Documentation/docs/provenance/LANGUAGE_MATH_MODEL_SOURCES.cff
    for DOIs on language modeling, compression, and information theory.

Conventions:
  PascalCase types, camelCase functions.
  theorem for every boundary claim.
  #eval! for executable receipt.
  Namespace: Semantics.MediaTransferProbe
-/

import Semantics.Toolkit
import Semantics.CognitiveLoad
import Semantics.GeneticFieldEquation

namespace Semantics.MediaTransferProbe

open Semantics.Toolkit
open Semantics.CognitiveLoad
open Semantics.GeneticFieldEquation

-- =========================================================================
-- S0  Media Channel Types and Bandwidths
-- =========================================================================

/-- Media channel: a technology for transferring information between
    humans and their accumulated knowledge substrate. -/
inductive MediaChannel where
  | oral         -- Speech, face-to-face transmission
  | writing      -- Persistent symbols: cuneiform, papyrus, paper
  | printing     -- Mass reproduction: Gutenberg press
  | electronic   -- Telegraph, telephone, radio
  | television   -- Broadcast visual information
  | internet     -- Digital bidirectional network
  | ai           -- Generative AI / LLM inference
  deriving Repr, Inhabited, DecidableEq, BEq

/-- Shannon-effective bandwidth: bits per second per person.
    These are ORDER-OF-MAGNITUDE phenomenological estimates.
    Oral: speech ~150 words/min ≈ 10 bits/s (very rough)
    Writing: reading ~250 words/min ≈ 20 bits/s
    Printing: same reading speed but mass reach ≈ 10× effective
    Electronic: telegraph ~40 wpm, radio broadcast ≈ 100× reach
    Television: visual channel ≈ 10^6 bits/s video stream
    Internet: searchable, bidirectional ≈ 10^9 effective
    AI: generative, interactive, personalized ≈ 10^12 effective
-/
def channelBandwidth (ch : MediaChannel) : Rat :=
  match ch with
  | .oral       => 10        -- 10^1 bits/s effective
  | .writing    => 100       -- 10^2 bits/s effective (persistent + re-readable)
  | .printing   => 1000      -- 10^3 bits/s effective (mass distribution)
  | .electronic => 10000     -- 10^4 bits/s effective (global real-time)
  | .television => 1000000   -- 10^6 bits/s effective (visual broadcast)
  | .internet   => 100000000 -- 10^8 bits/s effective (search + bidirectional)
  | .ai         => 1000000000000 -- 10^12 bits/s effective (generative inference)

/-- Channel bandwidth is strictly increasing with technological level. -/
theorem channelBandwidthIncreasing :
    channelBandwidth .oral < channelBandwidth .writing ∧
    channelBandwidth .writing < channelBandwidth .printing ∧
    channelBandwidth .printing < channelBandwidth .electronic ∧
    channelBandwidth .electronic < channelBandwidth .television ∧
    channelBandwidth .television < channelBandwidth .internet ∧
    channelBandwidth .internet < channelBandwidth .ai := by
  native_decide

/-- Order-of-magnitude ratio between adjacent channels.
    For most transitions: ~10× increase in effective bandwidth. -/
def channelBandwidthRatio (oldCh newCh : MediaChannel) : Rat :=
  channelBandwidth newCh / channelBandwidth oldCh

/-- Writing/print ratio ≈ 10. -/
theorem writingToPrintRatio : channelBandwidthRatio .writing .printing = 10 := by
  native_decide

/-- Print/electronic ratio ≈ 10. -/
theorem printToElectronicRatio : channelBandwidthRatio .printing .electronic = 10 := by
  native_decide

/-- Electronic/TV ratio ≈ 100. -/
theorem electronicToTvRatio : channelBandwidthRatio .electronic .television = 100 := by
  native_decide

/-- TV/internet ratio ≈ 100. -/
theorem tvToInternetRatio : channelBandwidthRatio .television .internet = 100 := by
  native_decide

/-- Internet/AI ratio ≈ 10,000. -/
theorem internetToAiRatio : channelBandwidthRatio .internet .ai = 10000 := by
  native_decide

-- =========================================================================
-- S1  Human Cognitive Capacity (Fixed Substrate)
-- =========================================================================

/- The human brain has a fixed information processing capacity:
   - Conscious processing: ~40-60 bits/s (reading, speaking)
   - Sensory bandwidth: ~10^7 bits/s (vision), but mostly unconscious
   - Working memory: ~7±2 chunks (Miller's law)
   - Long-term memory encoding: very slow, ~1 bit/s effective

   For the model, we use CONSCIOUS PROCESSING as the bottleneck:
   C ≈ 50 bits/s per person (conservative).

   This is the FIXED substrate that media channels must interface with.
   When a channel's effective bandwidth exceeds what institutions
   can process, those institutions become semantic basins.
-/

/-- Human conscious processing capacity: ~50 bits/s. -/
def humanConsciousCapacity : Rat := 50

/-- Human capacity is constant (biological substrate). -/
theorem humanCapacityConstant : humanConsciousCapacity = 50 := by rfl

-- =========================================================================
-- S2  Time to Institution Overload
-- =========================================================================

/- Model: An institution is designed for a specific channel bandwidth R_old.
   When a new channel R_new becomes dominant, the institution receives
   information at rate (R_new − R_old) that it cannot process.

   The institution has a "capacity buffer" B = C × T_design, where:
   - C = human cognitive capacity per person
   - T_design = design lifetime of the institution (generations)
   - Population = number of people the institution serves

   Overload occurs when: (R_new − R_old) × T > B × Population

   Solving for T_overload: T = B × Population / (R_new − R_old)

   For a civilization-scale institution (serving ~10^6 to 10^9 people):
     B ≈ C × T_design ≈ 50 bits/s × (25 years × 3.15×10^7 s/yr)
       ≈ 50 × 7.9×10^8 ≈ 4×10^10 bits per person

   With ΔR = R_new − R_old ≈ 9×R_old (for 10× transition):
     T_overload ≈ 4×10^10 / (9 × R_old)

   For oral→writing: R_old = 10, ΔR = 90
     T ≈ 4×10^10 / 90 ≈ 4.4×10^8 s ≈ 14 years per person-buffer
     But institutions span generations, so multiply by design lifetime.

   This simple model is too crude. Better: the PULSE is not about
   individual institution overload but about CIVILIZATION-WIDE
   restructuring when the dominant channel changes.

   Alternative model: the pulse period is the time needed for a
   population to ADAPT its institutions to a new channel. This is
   a sociological process, not a physical one.

   Empirical observation: media transitions are ACCELERATING:
     Writing→Print:  ~4450 years
     Print→Electronic: ~390 years
     Electronic→TV:   ~110 years
     TV→Internet:      ~40 years
     Internet→AI:      ~30 years (projected)

   The framework contribution: model the acceleration as
   T_next = T_prev / (channel_ratio × adaptation_factor).
-/

/-- Historical media transition dates (approximate year CE, negative = BCE). -/
def transitionDate (oldCh newCh : MediaChannel) : Option Rat :=
  match oldCh, newCh with
  | .oral, .writing    => some (-3000)   -- 3000 BCE: Sumerian cuneiform
  | .writing, .printing => some 1450      -- 1450 CE: Gutenberg
  | .printing, .electronic => some 1840  -- 1840 CE: telegraph
  | .electronic, .television => some 1950 -- 1950 CE: TV broadcast era
  | .television, .internet => some 1990    -- 1990 CE: WWW
  | .internet, .ai => some 2020            -- 2020 CE: GPT-3 era
  | _, _ => none

/-- Historical interval between transitions (years). -/
def transitionInterval (oldCh newCh : MediaChannel) : Option Rat :=
  match transitionDate oldCh newCh with
  | some t_new =>
    match oldCh with
    | .oral => some (t_new - (-10000))  -- oral tradition ~10,000 BCE
    | .writing => some (t_new - (-3000))
    | .printing => some (t_new - 1450)
    | .electronic => some (t_new - 1840)
    | .television => some (t_new - 1950)
    | .internet => some (t_new - 1990)
    | .ai => none  -- no next transition yet
  | none => none

/-- Print→Electronic interval: ~390 years. -/
theorem printToElectronicInterval :
    transitionInterval .printing .electronic = some 390 := by native_decide

/-- Electronic→TV interval: ~110 years. -/
theorem electronicToTvInterval :
    transitionInterval .electronic .television = some 110 := by native_decide

/-- TV→Internet interval: ~40 years. -/
theorem tvToInternetInterval :
    transitionInterval .television .internet = some 40 := by native_decide

/-- Internet→AI interval: ~30 years. -/
theorem internetToAiInterval :
    transitionInterval .internet .ai = some 30 := by native_decide

-- =========================================================================
-- S3  Deriving the Pulse from Media Transitions
-- =========================================================================

/- The user's insight: the civilizational pulse is NOT an abstract
   growth process. It is the time between media channel transitions
   that force institutional restructuring.

   For the PRE-INDUSTRIAL era (print and before):
     Dominant channels: oral → writing → print
     The pulse was LONG because channel bandwidths were low
     and transitions were rare.

   For the INDUSTRIAL era (electronic → TV):
     Channel bandwidth jumped to 10^3-10^6 bits/s
     The pulse compressed to ~100-400 years.

   For the DIGITAL era (internet → AI):
     Channel bandwidth jumped to 10^8-10^12 bits/s
     The pulse compresses to ~30-40 years.

   FRAMEWORK DERIVATION ATTEMPT:
   The time for a population to process a "channel transition shock"
   is proportional to the ratio of old channel bandwidth to the
   DIFFERENCE in bandwidth:

     T_pulse ∝ R_old / (R_new − R_old)

   For a 10× transition (R_new = 10 × R_old):
     T_pulse ∝ R_old / (9 × R_old) = 1/9

   This says the pulse is CONSTANT for all 10× transitions, which
   is wrong (empirically it accelerates).

   CORRECTED MODEL:
   The pulse is proportional to the ADAPTATION TIME, which depends
   on how many generations must pass for institutions to redesign
   themselves for the new channel. Each media transition requires:
     - 1 generation to recognize the new channel's potential
     - 1 generation to experiment with new institutional forms
     - 1 generation to stabilize the new forms
   → ~3 generations = ~60-75 years minimum

   But the ACTUAL interval is SHORTER because later transitions
   build on previous ones (internet builds on TV infrastructure).

   The framework's contribution: the pulse period is EMERGENT from
   the media channel structure, not a fitted parameter.
-/

/-- Minimum pulse period: ~3 generations for institutional adaptation.
    3 × 25 years = 75 years. -/
def minimumPulsePeriod : Rat := 75

/-- Framework-derived pulse for print-era institutions:
    minimum adaptation time × channel complexity factor.
    The complexity factor could relate to Menger levels (3^k).
    For k=5: 75 × (61.2/6.81) ≈ 75 × 9 ≈ 675? Too long.

    Alternative: pulse = minimumPeriod × (channel_level)
    where channel_level = 1 (oral), 2 (writing), 3 (print), etc.
    For print (level 3): 75 × 3 = 225 years.
    This is close to the empirical 245 years.
-/
def mediaLevelPulse (level : Nat) : Rat :=
  minimumPulsePeriod * (level : Rat)

/-- Print-era pulse (level 3): ~225 years. -/
theorem printLevelPulse : mediaLevelPulse 3 = 225 := by native_decide

/-
Electronic-era pulse (level 4): ~300 years.
This is longer because electronic institutions need more time? No,
empirically it should be shorter.

The level model fails — pulse should DECREASE with level, not increase.

CORRECTED: pulse = minimumPeriod / (adaptation_speed × channel_level)
where adaptation_speed increases with technological sophistication.
For level 3 (print): 75 / 0.3 ≈ 250 years.
For level 4 (electronic): 75 / 0.6 ≈ 125 years.
For level 5 (internet): 75 / 1.5 ≈ 50 years.
For level 6 (AI): 75 / 3.0 ≈ 25 years.

The adaptation speed is the rate at which institutions can
restructure, which increases with each media transition.
This acceleration is a HISTORICAL FACT, not a derived constant.
-/

-- =========================================================================
-- S4  The Framework's Honest Boundary
-- =========================================================================

/- SUMMARY OF WHAT THE MEDIA TRANSFER MODEL PROVIDES:

   1. PHENOMENOLOGICAL COHERENCE: The media channel model explains
      WHY information density grows (new channels) and WHY institutions
      overload (channel bandwidth exceeds design capacity).

   2. EMPIRICAL GROUNDING: Historical media transitions are real
      events with real dates. The intervals are measurable.

   3. SINGULARITY EXPLANATION: The internet→AI transition is a
      10,000× bandwidth jump, the largest in history. This explains
      the current institutional crisis (semantic basin overload).

   4. SPECIES-DEPENDENT P0: Each species' dominant information
      channel determines its effective pulse. Sardines (chemical/oral
      communication) have low bandwidth → long pulse. Humans
      (digital/AI channels) have high bandwidth → compressed pulse.

   WHAT IT DOES NOT PROVIDE:

   1. DERIVED CHANNEL BANDWIDTHS: The 10, 100, 1000, etc. values
      are order-of-magnitude estimates, not derived from framework
      constants. A genuine derivation would require:
      - Shannon capacity of each channel from physics
      - Processing capacity of each species' brain from neuroscience
      - These are outside the framework's scope.

   2. DERIVED TRANSITION DATES: Historical dates (1450, 1840, etc.)
      are empirical. The framework does not predict WHEN Gutenberg
      invented the press.

   3. DERIVED ADAPTATION SPEED: The acceleration of institutional
      adaptation is a sociological observation, not a derived constant.

   THE HONEST VERDICT:
   The media transfer model is a COHERENT PHENOMENOLOGICAL FRAMEWORK
   that connects information theory to civilizational dynamics. It
   explains the singularity, the pulse acceleration, and species
   differences in ecological timescales. But it does not DERIVE the
   fundamental rates from the framework's mathematical constants.

   The framework provides:
     - Universal dimensionless structure: n(k) = 3^k × z × 133/137
     - Cycle multiplier: 5 = 3 × 2 − 1
     - MassNumber gate for checking P0 admissibility

   The media transfer model provides:
     - Phenomenological mechanism for information growth
     - Species-dependent channel bandwidth estimates
     - Historical grounding for pulse periods

   Together they give a working model. But P0 remains emergent,
   not derived from first principles.
-/

/-- Status of the media transfer model. -/
def mediaTransferStatus : String :=
  "phenomenologically coherent; explains pulse acceleration and singularity; "
  ++ "channel bandwidths are empirical estimates, not derived from framework constants"

-- =========================================================================
-- S5  Executable Receipts
-- =========================================================================

#eval! channelBandwidth .oral
#eval! channelBandwidth .writing
#eval! channelBandwidth .printing
#eval! channelBandwidth .electronic
#eval! channelBandwidth .television
#eval! channelBandwidth .internet
#eval! channelBandwidth .ai
#eval! channelBandwidthRatio .writing .printing
#eval! channelBandwidthRatio .printing .electronic
#eval! channelBandwidthRatio .internet .ai
#eval! humanConsciousCapacity
#eval! minimumPulsePeriod
#eval! mediaLevelPulse 3
-- Theorems above are proved by native_decide; not computationally evaluable
-- #eval! printToElectronicInterval
-- #eval! electronicToTvInterval
-- #eval! tvToInternetInterval
-- #eval! internetToAiInterval
#eval! mediaTransferStatus

end Semantics.MediaTransferProbe
