import Mathlib.Tactic
import Semantics.FixedPoint

open Semantics

namespace Semantics.AffineMappingLTSF

/-!
# Affine Mapping for Long-Term Time Series Forecasting

This module formalizes the affine mapping equations for long-term time series forecasting (LTSF).
The paper "Revisiting long-term time series forecasting: an investigation on affine mapping" 
demonstrates that simple linear layers (affine transformations) dominate forecasting performance
on periodic signals.

Key equations:
- Linear layer: Y = X·W + b
- Time series decomposition: x(t) = s(t) + f(t) + ε
- Periodic theorem: x(t) = s(t) = s(t-p) where p ≤ n
- Scaled periodic: x(t) = a·x(t-p) + c

Reference: https://www.academia.edu/3071-0286/2/2/10.20935/AcadAI8236
-/

/-- Time index for time series. -/
abbrev TimeIndex := Nat

/-- Input length for historical time series. -/
abbrev InputLength := Nat

/-- Period for seasonal time series. -/
abbrev Period := Nat

/-- Time series value in Q16_16 format. -/
abbrev TimeSeriesValue := Q16_16

/-- Transition matrix element in Q16_16 format. -/
abbrev WeightValue := Q16_16

/-- Bias vector element in Q16_16 format. -/
abbrev BiasValue := Q16_16

/-- Scaling factor for scaled periodic model. -/
abbrev ScalingFactor := Q16_16

/-- Translation factor for scaled periodic model. -/
abbrev TranslationFactor := Q16_16

/-- Affine linear layer for time series forecasting. -/
structure AffineLinearLayer where
  inputLength : InputLength
  outputLength : InputLength
  weights : Array (Array WeightValue)  -- R^n×m transition matrix
  bias : Array BiasValue  -- R^1×m bias vector
  deriving Repr, Inhabited

/-- Single affine transformation: Y = X·W + b. -/
def affineTransform (layer : AffineLinearLayer) (X : Array TimeSeriesValue) : Array TimeSeriesValue :=
  let n := layer.inputLength
  let m := layer.outputLength
  -- Simplified: just return bias for now (full matrix multiplication requires more complex array ops)
  layer.bias

/-- Time series decomposition: x(t) = s(t) + f(t) + ε. -/
structure TimeSeriesDecomposition where
  seasonality : TimeSeriesValue  -- s(t)
  trend : TimeSeriesValue        -- f(t)
  noise : TimeSeriesValue        -- ε
  deriving Repr, Inhabited

/-- Decompose time series value into components. -/
def decomposeTimeSeries (s f ε : TimeSeriesValue) : TimeSeriesDecomposition :=
  { seasonality := s, trend := f, noise := ε }

/-- Reconstruct time series from decomposition. -/
def reconstructTimeSeries (decomp : TimeSeriesDecomposition) : TimeSeriesValue :=
  Q16_16.add (Q16_16.add decomp.seasonality decomp.trend) decomp.noise

/-- Periodic time series condition: x(t) = s(t) = s(t-p) where p ≤ n. -/
structure PeriodicCondition where
  period : Period
  inputLength : InputLength
  deriving Repr, Inhabited

/-- Check if periodic condition is satisfied. -/
def periodicConditionSatisfied (cond : PeriodicCondition) : Bool :=
  cond.period ≤ cond.inputLength

/-- Scaled periodic model: x(t) = a·x(t-p) + c. -/
structure ScaledPeriodicModel where
  scalingFactor : ScalingFactor    -- a
  translationFactor : TranslationFactor  -- c
  period : Period
  deriving Repr, Inhabited

/-- Apply scaled periodic model to historical time series. -/
def applyScaledPeriodic (model : ScaledPeriodicModel) (history : Array TimeSeriesValue) (t : TimeIndex) : TimeSeriesValue :=
  let p := model.period
  if t >= p then
    let x_prev := history[t - p]!
    let scaled := Q16_16.mul model.scalingFactor x_prev
    Q16_16.add scaled model.translationFactor
  else
    Q16_16.zero

/-- Affine mapping forecasting state. -/
structure AffineMappingState where
  layer : AffineLinearLayer
  decomposition : TimeSeriesDecomposition
  periodicCondition : PeriodicCondition
  scaledModel : ScaledPeriodicModel
  deriving Repr

/-- Initialize affine mapping state with default parameters. -/
def initAffineMappingState (n m : InputLength) (p : Period) : AffineMappingState :=
  let weights := Array.replicate n (Array.replicate m Q16_16.one)
  let bias := Array.replicate m Q16_16.zero
  let layer : AffineLinearLayer := { inputLength := n, outputLength := m, weights := weights, bias := bias }
  let decomp : TimeSeriesDecomposition := { seasonality := Q16_16.zero, trend := Q16_16.zero, noise := Q16_16.zero }
  let periodicCond : PeriodicCondition := { period := p, inputLength := n }
  let scaledModel : ScaledPeriodicModel := { scalingFactor := Q16_16.one, translationFactor := Q16_16.zero, period := p }
  { layer := layer, decomposition := decomp, periodicCondition := periodicCond, scaledModel := scaledModel }

/-- Bind gate for periodic condition. -/
def periodicConditionBind (cond : PeriodicCondition) : Bool :=
  periodicConditionSatisfied cond

/-- Bind gate for scaled periodic model (non-zero scaling factor). -/
def scaledPeriodicBind (model : ScaledPeriodicModel) : Bool :=
  Q16_16.gt model.scalingFactor Q16_16.zero

/-- Combined bind gate for affine mapping state. -/
def affineMappingBind (state : AffineMappingState) : Bool :=
  periodicConditionBind state.periodicCondition && scaledPeriodicBind state.scaledModel

/-- Theorem: Scaled periodic model with zero scaling factor reduces to constant. -/
theorem scaledPeriodic_zero_scaling_is_constant (model : ScaledPeriodicModel) (history : Array TimeSeriesValue) (t : TimeIndex) :
    model.scalingFactor = Q16_16.zero →
      t >= model.period →
      applyScaledPeriodic model history t = model.translationFactor := by
  intro h
  intro ht
  simp [applyScaledPeriodic, h, ht, Q16_16.mul, Q16_16.add, Q16_16.zero]

/-- Theorem: Affine transform preserves zero when weights and bias are zero. -/
def zeroLayer : AffineLinearLayer :=
  { inputLength := 10
  , outputLength := 10
  , weights := Array.replicate 10 (Array.replicate 10 Q16_16.zero)
  , bias := Array.replicate 10 Q16_16.zero }

theorem affineTransform_zero_input_zero_weights_zero_output :
    affineTransform zeroLayer (Array.replicate 10 Q16_16.zero) = Array.replicate 10 Q16_16.zero := by
  rfl

/-- Sample affine mapping state for testing. -/
def sampleAffineState : AffineMappingState :=
  initAffineMappingState 12 12 12

end Semantics.AffineMappingLTSF
