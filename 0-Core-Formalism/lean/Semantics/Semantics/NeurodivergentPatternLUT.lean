import Std

namespace Semantics.NeurodivergentPatternLUT

/-- Pattern type enumeration -/
inductive PatternType where
  | neurotypical  -- Standard cognitive pattern
  | autism  -- Autism spectrum pattern
  | adhd  -- ADHD pattern
  | combined  -- Comorbid autism + ADHD
  | adaptive  -- Adaptive pattern for specific task
deriving BEq

/-- Excitation/Inhibition ratio for autism pattern -/
structure EIRatio where
  ratio : UInt16  -- E/I ratio (neurotypical ≈ 1.0 = 65536, autism > 1.2)
  threshold : UInt16  -- Activation threshold (lower for autism)
  sensitivity : UInt16  -- Pattern detection sensitivity

/-- Local/Long-Range connectivity ratio for autism pattern -/
structure ConnectivityRatio where
  localDensity : UInt16  -- Local connectivity density
  longRangeDensity : UInt16  -- Long-range connectivity density
  ratio : UInt16  -- κ = f_local / f_long (autism > 1.3)

/-- Dopamine transport parameters for ADHD pattern -/
structure DopamineTransport where
  clearanceTime : UInt16  -- Dopamine clearance time (τ_clear)
  deficitFactor : UInt16  -- δ_adhd (0.2-0.4)
  baselineClearance : UInt16  -- τ_normal (neurotypical baseline)

/-- Sensory filter threshold for autism pattern -/
structure SensoryThreshold where
  threshold : UInt16  -- Sensory gating threshold (θ)
  hyperSensitivity : UInt16  -- σ_hyper (0.3-0.6)
  baselineThreshold : UInt16  -- θ_neurotypical

/-- Compensatory routing weight for neurodivergent patterns -/
structure CompensatoryRouting where
  standardWeight : UInt16  -- w_standard
  compensatoryWeight : UInt16  -- w_comp
  compensationFactor : UInt16  -- λ_comp (0.2-0.8)

/-- Complete neurodivergent pattern configuration -/
structure NeurodivergentPattern where
  eiRatio : EIRatio
  connectivity : ConnectivityRatio
  dopamine : DopamineTransport
  sensory : SensoryThreshold
  routing : CompensatoryRouting
  patternType : PatternType

/-- Inhabited instance for NeurodivergentPattern -/
instance : Inhabited NeurodivergentPattern :=
  ⟨
    {
      eiRatio := { ratio := 65536, threshold := 32768, sensitivity := 16384 },
      connectivity := { localDensity := 32768, longRangeDensity := 32768, ratio := 65536 },
      dopamine := { clearanceTime := 32768, deficitFactor := 0, baselineClearance := 32768 },
      sensory := { threshold := 32768, hyperSensitivity := 0, baselineThreshold := 32768 },
      routing := { standardWeight := 65536, compensatoryWeight := 65536, compensationFactor := 0 },
      patternType := .neurotypical
    }
  ⟩

/-- Warm LUT for neurodivergent patterns -/
structure NeurodivergentPatternLUT where
  entries : Array NeurodivergentPattern  -- Pre-computed pattern entries
  currentIndex : Nat  -- Current LUT index
  size : Nat  -- LUT size

/-- Task type for adaptive pattern selection -/
inductive TaskType where
  | securityScan  -- Fast threat detection
  | codeReview  -- Detail-oriented analysis
  | sustainedFocus  -- Attention maintenance
  | signalDetection  -- Weak signal detection
  | faultTolerance  -- Redundant routing
deriving Repr, BEq

/-- Initialize neurotypical baseline pattern -/
def mkNeurotypicalPattern : NeurodivergentPattern :=
  {
    eiRatio := { ratio := 65536, threshold := 32768, sensitivity := 16384 },
    connectivity := { localDensity := 32768, longRangeDensity := 32768, ratio := 65536 },
    dopamine := { clearanceTime := 32768, deficitFactor := 0, baselineClearance := 32768 },
    sensory := { threshold := 32768, hyperSensitivity := 0, baselineThreshold := 32768 },
    routing := { standardWeight := 65536, compensatoryWeight := 65536, compensationFactor := 0 },
    patternType := .neurotypical
  }

/-- Initialize autism pattern (enhanced pattern detection) -/
def mkAutismPattern : NeurodivergentPattern :=
  {
    eiRatio := { ratio := 78643, threshold := 20480, sensitivity := 24576 },  -- EIRatio: ξ=1.2, lower threshold
    connectivity := { localDensity := 40960, longRangeDensity := 24576, ratio := 106496 },  -- ConnectivityRatio: κ=1.6
    dopamine := { clearanceTime := 32768, deficitFactor := 0, baselineClearance := 32768 },
    sensory := { threshold := 20480, hyperSensitivity := 12288, baselineThreshold := 32768 },  -- SensoryThreshold: 40% lower
    routing := { standardWeight := 65536, compensatoryWeight := 98304, compensationFactor := 32768 },  -- CompensatoryRouting: λ=0.5
    patternType := .autism
  }

/-- Initialize ADHD pattern (attentional flexibility) -/
def mkADHDPattern : NeurodivergentPattern :=
  {
    eiRatio := { ratio := 65536, threshold := 32768, sensitivity := 16384 },
    connectivity := { localDensity := 32768, longRangeDensity := 32768, ratio := 65536 },
    dopamine := { clearanceTime := 40960, deficitFactor := 19661, baselineClearance := 32768 },  -- DopamineTransport: 30% deficit
    sensory := { threshold := 32768, hyperSensitivity := 0, baselineThreshold := 32768 },
    routing := { standardWeight := 65536, compensatoryWeight := 81920, compensationFactor := 16384 },  -- CompensatoryRouting: λ=0.25
    patternType := .adhd
  }

/-- Initialize combined autism + ADHD pattern -/
def mkCombinedPattern : NeurodivergentPattern :=
  {
    eiRatio := { ratio := 78643, threshold := 20480, sensitivity := 24576 },
    connectivity := { localDensity := 40960, longRangeDensity := 24576, ratio := 106496 },
    dopamine := { clearanceTime := 40960, deficitFactor := 19661, baselineClearance := 32768 },
    sensory := { threshold := 20480, hyperSensitivity := 12288, baselineThreshold := 32768 },
    routing := { standardWeight := 65536, compensatoryWeight := 114688, compensationFactor := 49152 },  -- CompensatoryRouting: λ=0.75
    patternType := .combined
  }

/-- Initialize adaptive pattern for specific task -/
def mkAdaptivePattern (taskType : TaskType) : NeurodivergentPattern :=
  match taskType with
  | .securityScan =>
    {
      eiRatio := { ratio := 81920, threshold := 16384, sensitivity := 28672 },  -- EIRatio: High sensitivity
      connectivity := { localDensity := 36864, longRangeDensity := 28672, ratio := 81920 },
      dopamine := { clearanceTime := 36864, deficitFactor := 13107, baselineClearance := 32768 },
      sensory := { threshold := 16384, hyperSensitivity := 16384, baselineThreshold := 32768 },
      routing := { standardWeight := 65536, compensatoryWeight := 65536, compensationFactor := 0 },
      patternType := .adaptive
    }
  | .codeReview =>
    {
      eiRatio := { ratio := 73728, threshold := 24576, sensitivity := 20480 },
      connectivity := { localDensity := 45056, longRangeDensity := 20480, ratio := 114688 },  -- ConnectivityRatio: High local
      dopamine := { clearanceTime := 32768, deficitFactor := 0, baselineClearance := 32768 },
      sensory := { threshold := 24576, hyperSensitivity := 8192, baselineThreshold := 32768 },
      routing := { standardWeight := 65536, compensatoryWeight := 73728, compensationFactor := 8192 },
      patternType := .adaptive
    }
  | .sustainedFocus =>
    {
      eiRatio := { ratio := 65536, threshold := 32768, sensitivity := 16384 },
      connectivity := { localDensity := 32768, longRangeDensity := 32768, ratio := 65536 },
      dopamine := { clearanceTime := 49152, deficitFactor := 26214, baselineClearance := 32768 },  -- DopamineTransport: High deficit
      sensory := { threshold := 32768, hyperSensitivity := 0, baselineThreshold := 32768 },
      routing := { standardWeight := 65536, compensatoryWeight := 65536, compensationFactor := 0 },
      patternType := .adaptive
    }
  | .signalDetection =>
    {
      eiRatio := { ratio := 65536, threshold := 32768, sensitivity := 16384 },
      connectivity := { localDensity := 32768, longRangeDensity := 32768, ratio := 65536 },
      dopamine := { clearanceTime := 32768, deficitFactor := 0, baselineClearance := 32768 },
      sensory := { threshold := 12288, hyperSensitivity := 20480, baselineThreshold := 32768 },  -- SensoryThreshold: Very low threshold
      routing := { standardWeight := 65536, compensatoryWeight := 65536, compensationFactor := 0 },
      patternType := .adaptive
    }
  | .faultTolerance =>
    {
      eiRatio := { ratio := 65536, threshold := 32768, sensitivity := 16384 },
      connectivity := { localDensity := 32768, longRangeDensity := 32768, ratio := 65536 },
      dopamine := { clearanceTime := 32768, deficitFactor := 0, baselineClearance := 32768 },
      sensory := { threshold := 32768, hyperSensitivity := 0, baselineThreshold := 32768 },
      routing := { standardWeight := 65536, compensatoryWeight := 122880, compensationFactor := 57344 },  -- CompensatoryRouting: High compensation
      patternType := .adaptive
    }

/-- Initialize warm LUT with pre-computed patterns -/
def initWarmLUT : NeurodivergentPatternLUT :=
  {
    entries := #[mkNeurotypicalPattern, mkAutismPattern, mkADHDPattern, mkCombinedPattern],
    currentIndex := 0,
    size := 4
  }

/-- Load pattern from LUT by index -/
def loadPattern (lut : NeurodivergentPatternLUT) (index : Nat) : Option NeurodivergentPattern :=
  if index < lut.size then
    some lut.entries[index]!
  else
    none

/-- Load pattern by type (search LUT) -/
def loadPatternByType (lut : NeurodivergentPatternLUT) (pType : PatternType) : Option NeurodivergentPattern :=
  let rec loop (i : Nat) : Option NeurodivergentPattern :=
    if i >= lut.size then
      none
    else
      let pattern := lut.entries[i]!
      if pattern.patternType == pType then
        some pattern
      else
        loop (i + 1)
  loop 0

/-- Load adaptive pattern for specific task (not in LUT, compute on demand) -/
def loadAdaptivePattern (taskType : TaskType) : NeurodivergentPattern :=
  mkAdaptivePattern taskType

end Semantics.NeurodivergentPatternLUT
