/-
ThresholdVector.lean — The threshold activation vector for boundary physics.

A boundary is not where a system ends. A boundary is where accumulated encoded
states become physically active. The threshold vector Theta_i gates the regime
transitions that determine which physics are active at a given boundary
activation level.

Threshold components:
  Theta_sigma : elastic -> fracture       (stress threshold)
  Theta_eta   : low coupling -> ignition  (medium-coupling threshold)
  Theta_beta  : disconnected -> percolating topology (topology-persistence)
  Theta_lambda: stable eigenmode -> regime switch     (eigenvalue-drift)
  Theta_eps   : admissible residual -> divergence     (residual-accumulation)

The total activation is the weighted superposition:
  B = sum alpha_i * phi_i

where phi_i are encoded regime components and alpha_i are activation weights.
When B exceeds the critical threshold Theta_c, the boundary enters an active
physical regime (fire, shock, plasma, fracture, turbulence, filamentation).

Reference: Activated boundary physics model
-/

import Semantics.FixedPoint
import Semantics.Transition

set_option linter.dupNamespace false

namespace Semantics.ThresholdVector

open Semantics.FixedPoint (Q0_16 Q16_16 Q0_16.ofRawInt)
open Semantics.Transition (Regime)

/-- The index identifying which threshold component is being referenced. -/
inductive ThresholdIndex
  | sigma     -- elastic -> fracture (stress threshold)
  | eta       -- medium coupling -> atmospheric ignition
  | beta      -- disconnected -> percolating topology
  | lambda    -- stable eigenmode -> regime switch
  | epsilon   -- admissible residual -> divergence
  deriving Repr, DecidableEq, BEq, Inhabited

/--
ThresholdVector: the full set of regime transition thresholds.

Each component gates a specific physical regime transition:
  Theta_sigma : when stress exceeds this, material leaves elastic regime
  Theta_eta   : when coupling exceeds this, atmosphere enters ignition regime
  Theta_beta  : when topology persistence exceeds this, percolation connects
  Theta_lambda: when eigenvalue drift exceeds this, the dominant eigenmode switches
  Theta_eps   : when residual exceeds this, the chart enters divergence
-/
structure ThresholdVector where
  sigma   : Q0_16   -- elastic -> fracture
  eta     : Q0_16   -- low coupling -> atmospheric ignition
  beta    : Q0_16   -- disconnected -> percolating topology
  lambda  : Q0_16   -- stable eigenmode -> regime switch
  epsilon : Q0_16   -- admissible residual -> divergence
  deriving Repr, DecidableEq, BEq, Inhabited

/--
ActivationState: current activation levels for each boundary component.

These represent the accumulated encoded values phi_i that are compared
against thresholds and combined into the total activation B.
-/
structure ActivationState where
  stressAccumulated    : Q0_16   -- accumulated stress phi_sigma
  couplingAccumulated  : Q0_16   -- medium coupling phi_eta
  topologyPersistence  : Q0_16   -- topology persistence phi_beta
  eigenmodeDrift       : Q0_16   -- eigenmode spectral drift phi_lambda
  residualAccumulated  : Q0_16   -- accumulated residual phi_epsilon
  deriving Repr, DecidableEq, BEq, Inhabited

/--
ActivationWeight: the superposition coefficients alpha_i for each regime component.

The total boundary activation is:
  B = sum_i alpha_i * phi_i
-/
structure ActivationWeight where
  sigma   : Q0_16   -- weight alpha_sigma for stress component
  eta     : Q0_16   -- weight alpha_eta for coupling component
  beta    : Q0_16   -- weight alpha_beta for topology component
  lambda  : Q0_16   -- weight alpha_lambda for eigenmode component
  epsilon : Q0_16   -- weight alpha_epsilon for residual component
  deriving Repr, DecidableEq, BEq, Inhabited

/--
The boundary activation verdict.

Determined by which individual thresholds have been crossed and whether
the total weighted activation exceeds the critical threshold.
-/
inductive ActivationVerdict
  | latent       -- total activation below all thresholds
  | smooth       -- sigma threshold crossed: elastic regime active
  | turbulent    -- eta threshold crossed: coupling regime active
  | percolating  -- beta threshold crossed: topology regime active
  | switching    -- lambda threshold crossed: eigenmode regime switching
  | diverging    -- epsilon threshold crossed: residual divergence regime
  | active       -- multiple thresholds crossed: full boundary activation
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Critical threshold for total activation B.
    When B >= Theta_c the boundary system enters an active physical regime.
    Set to just below 0.2 so that a single uniform-weighted component at
    full strength (0x1998) clears the gate. -/
def criticalActivationThreshold : Q0_16 :=
  Q0_16.ofRawInt 0x1997  -- just below 0.2

/--
Default threshold vector with hierarchical separation between regimes.
Stress threshold lowest (easiest to cross), residual highest (hardest).
-/
def defaultThresholds : ThresholdVector :=
  { sigma   := Q0_16.ofRawInt 0x2CCC   -- approx 0.35 : stress -> fracture
  , eta     := Q0_16.ofRawInt 0x4000   -- approx 0.50 : coupling -> ignition
  , beta    := Q0_16.ofRawInt 0x5555   -- approx 0.67 : topology -> percolation
  , lambda  := Q0_16.ofRawInt 0x6AAA   -- approx 0.83 : eigenmode -> regime switch
  , epsilon := Q0_16.ofRawInt 0x7333 } -- approx 0.90 : residual -> divergence

/--
Uniform activation weights — each component contributes equally.
Sum approx 1.0 so B approx mean(phi_i).
-/
def uniformWeights : ActivationWeight :=
  { sigma   := Q0_16.ofRawInt 0x1999   -- approx 0.20
  , eta     := Q0_16.ofRawInt 0x1999   -- approx 0.20
  , beta    := Q0_16.ofRawInt 0x1999   -- approx 0.20
  , lambda  := Q0_16.ofRawInt 0x1999   -- approx 0.20
  , epsilon := Q0_16.ofRawInt 0x1999 } -- approx 0.20

/--
Stress-dominant weights — stress contributes most to activation.
Useful for modeling fracture/shock-dominated boundary regimes.
-/
def stressDominantWeights : ActivationWeight :=
  { sigma   := Q0_16.ofRawInt 0x3333   -- approx 0.40
  , eta     := Q0_16.ofRawInt 0x1999   -- approx 0.20
  , beta    := Q0_16.ofRawInt 0x0CCD   -- approx 0.10
  , lambda  := Q0_16.ofRawInt 0x0CCD   -- approx 0.10
  , epsilon := Q0_16.ofRawInt 0x1999 } -- approx 0.20

/--
Coupling-dominant weights — coupling contributes most to activation.
Useful for modeling atmospheric-ignition-dominated regimes.
-/
def couplingDominantWeights : ActivationWeight :=
  { sigma   := Q0_16.ofRawInt 0x0CCD   -- approx 0.10
  , eta     := Q0_16.ofRawInt 0x3333   -- approx 0.40
  , beta    := Q0_16.ofRawInt 0x1999   -- approx 0.20
  , lambda  := Q0_16.ofRawInt 0x0CCD   -- approx 0.10
  , epsilon := Q0_16.ofRawInt 0x1999 } -- approx 0.20

/- =======================================================================
    Activation evaluation functions
    ======================================================================= -/

/-- Check whether a single activation component exceeds its threshold. -/
def thresholdCrossed (value threshold : Q0_16) : Bool :=
  Q0_16.gt value threshold

/--
Compute the per-component activation excess (how far above threshold).
Returns zero if the threshold is not crossed.
-/
def activationExcess (value threshold : Q0_16) : Q0_16 :=
  if Q0_16.gt value threshold then
    Q0_16.sub value threshold
  else
    Q0_16.zero

/--
Compute the weighted total activation B = sum_i alpha_i * phi_i.

This is the superposition of encoded regime components. When B exceeds
Theta_c, the boundary enters an active physical regime.
-/
def totalActivation
  (state : ActivationState)
  (weights : ActivationWeight) : Q0_16 :=
  Q0_16.add (Q0_16.add (Q0_16.add (Q0_16.add
    (Q0_16.mul weights.sigma state.stressAccumulated)
    (Q0_16.mul weights.eta state.couplingAccumulated))
    (Q0_16.mul weights.beta state.topologyPersistence))
    (Q0_16.mul weights.lambda state.eigenmodeDrift))
    (Q0_16.mul weights.epsilon state.residualAccumulated)

/--
Gate function: is the total activation at or above the critical threshold?
-/
def isCriticallyActivated
  (state : ActivationState)
  (weights : ActivationWeight) : Bool :=
  Q0_16.ge (totalActivation state weights) criticalActivationThreshold

/--
Evaluate the full boundary activation given state, thresholds, and weights.

Returns an ActivationVerdict based on which individual thresholds are crossed
and whether the total superposition crosses the critical threshold.
-/
def evaluateActivation
  (state : ActivationState)
  (thresholds : ThresholdVector)
  (weights : ActivationWeight) : ActivationVerdict :=
  let stressActive := thresholdCrossed state.stressAccumulated thresholds.sigma
  let couplingActive := thresholdCrossed state.couplingAccumulated thresholds.eta
  let topologyActive := thresholdCrossed state.topologyPersistence thresholds.beta
  let eigenmodeActive := thresholdCrossed state.eigenmodeDrift thresholds.lambda
  let residualActive := thresholdCrossed state.residualAccumulated thresholds.epsilon
  let countActive :=
    (if stressActive then 1 else 0) +
    (if couplingActive then 1 else 0) +
    (if topologyActive then 1 else 0) +
    (if eigenmodeActive then 1 else 0) +
    (if residualActive then 1 else 0)
  let critical := isCriticallyActivated state weights
  if critical then
    if countActive >= 3 then ActivationVerdict.active
    else if residualActive then ActivationVerdict.diverging
    else if eigenmodeActive then ActivationVerdict.switching
    else if topologyActive then ActivationVerdict.percolating
    else if couplingActive then ActivationVerdict.turbulent
    else if stressActive then ActivationVerdict.smooth
    else ActivationVerdict.latent
  else
    ActivationVerdict.latent

/--
Map an ActivationVerdict to the corresponding Transition.Regime.
This connects the boundary activation framework to the existing regime semantics.
-/
def verdictToRegime (v : ActivationVerdict) : Regime :=
  match v with
  | ActivationVerdict.latent      => Regime.GROUNDED
  | ActivationVerdict.smooth      => Regime.GROUNDED
  | ActivationVerdict.turbulent   => Regime.SEISMIC
  | ActivationVerdict.percolating => Regime.SEISMIC
  | ActivationVerdict.switching   => Regime.SEISMIC
  | ActivationVerdict.diverging   => Regime.FLAME
  | ActivationVerdict.active      => Regime.FLAME

/- =======================================================================
    Canonical state witnesses
    ======================================================================= -/

/-- State with all components at zero activation. -/
def zeroActivationState : ActivationState :=
  { stressAccumulated   := Q0_16.zero
  , couplingAccumulated := Q0_16.zero
  , topologyPersistence := Q0_16.zero
  , eigenmodeDrift      := Q0_16.zero
  , residualAccumulated := Q0_16.zero }

/-- State with all components at maximum activation. -/
def fullActivationState : ActivationState :=
  { stressAccumulated   := Q0_16.one
  , couplingAccumulated := Q0_16.one
  , topologyPersistence := Q0_16.one
  , eigenmodeDrift      := Q0_16.one
  , residualAccumulated := Q0_16.one }

/-- State with only stress above threshold (smooth boundary regime). -/
def stressOnlyState : ActivationState :=
  { stressAccumulated   := Q0_16.one
  , couplingAccumulated := Q0_16.zero
  , topologyPersistence := Q0_16.zero
  , eigenmodeDrift      := Q0_16.zero
  , residualAccumulated := Q0_16.zero }

/-- State with stress and coupling active (approaching ignition). -/
def approachingIgnitionState : ActivationState :=
  { stressAccumulated   := Q0_16.one
  , couplingAccumulated := Q0_16.one
  , topologyPersistence := Q0_16.zero
  , eigenmodeDrift      := Q0_16.zero
  , residualAccumulated := Q0_16.zero }

/-- State with all except residual active (diverging regime). -/
def allButResidualState : ActivationState :=
  { stressAccumulated   := Q0_16.one
  , couplingAccumulated := Q0_16.one
  , topologyPersistence := Q0_16.one
  , eigenmodeDrift      := Q0_16.one
  , residualAccumulated := Q0_16.zero }

/-- State with only residual accumulation (diverging regime). -/
def residualOnlyState : ActivationState :=
  { stressAccumulated   := Q0_16.zero
  , couplingAccumulated := Q0_16.zero
  , topologyPersistence := Q0_16.zero
  , eigenmodeDrift      := Q0_16.zero
  , residualAccumulated := Q0_16.one }

/- =======================================================================
    Theorems
    ======================================================================= -/

theorem zero_state_is_latent :
    evaluateActivation zeroActivationState defaultThresholds uniformWeights = ActivationVerdict.latent := by
  native_decide

theorem full_state_with_stress_weights_is_active :
    evaluateActivation fullActivationState defaultThresholds stressDominantWeights = ActivationVerdict.active := by
  native_decide

theorem stress_state_is_smooth :
    evaluateActivation stressOnlyState defaultThresholds uniformWeights = ActivationVerdict.smooth := by
  native_decide

theorem stress_coupling_is_turbulent :
    evaluateActivation approachingIgnitionState defaultThresholds uniformWeights = ActivationVerdict.turbulent := by
  native_decide

theorem residual_only_is_diverging :
    evaluateActivation residualOnlyState defaultThresholds uniformWeights = ActivationVerdict.diverging := by
  native_decide

theorem all_but_residual_is_active :
    evaluateActivation allButResidualState defaultThresholds uniformWeights = ActivationVerdict.active := by
  native_decide

theorem zero_state_is_grounded :
    verdictToRegime (evaluateActivation zeroActivationState defaultThresholds uniformWeights) = Regime.GROUNDED := by
  native_decide

theorem full_active_state_is_flame :
    verdictToRegime (evaluateActivation fullActivationState defaultThresholds stressDominantWeights) = Regime.FLAME := by
  native_decide

theorem zero_state_not_critical :
    isCriticallyActivated zeroActivationState uniformWeights = false := by
  native_decide

theorem full_state_is_critical :
    isCriticallyActivated fullActivationState uniformWeights = true := by
  native_decide

theorem threshold_crossed_gt_works :
    thresholdCrossed (Q0_16.ofRawInt 0x6FFF) (Q0_16.ofRawInt 0x2CCC) = true := by
  native_decide

theorem threshold_crossed_lt_works :
    thresholdCrossed Q0_16.zero (Q0_16.ofRawInt 0x2CCC) = false := by
  native_decide

theorem total_activation_zero_state_is_zero :
    totalActivation zeroActivationState uniformWeights = Q0_16.zero := by
  native_decide

theorem total_activation_full_state_nonzero :
    Q0_16.gt (totalActivation fullActivationState uniformWeights) Q0_16.zero = true := by
  native_decide

theorem stress_dominant_gt_uniform_on_stress_state :
    Q0_16.gt (totalActivation stressOnlyState stressDominantWeights)
             (totalActivation stressOnlyState uniformWeights) = true := by
  native_decide

/- =======================================================================
    #eval witnesses
    ======================================================================= -/

#eval evaluateActivation zeroActivationState defaultThresholds uniformWeights
#eval evaluateActivation fullActivationState defaultThresholds uniformWeights
#eval evaluateActivation fullActivationState defaultThresholds stressDominantWeights
#eval evaluateActivation stressOnlyState defaultThresholds uniformWeights
#eval evaluateActivation approachingIgnitionState defaultThresholds uniformWeights
#eval evaluateActivation residualOnlyState defaultThresholds uniformWeights
#eval evaluateActivation allButResidualState defaultThresholds uniformWeights

#eval totalActivation zeroActivationState uniformWeights
#eval totalActivation fullActivationState uniformWeights
#eval totalActivation stressOnlyState stressDominantWeights

#eval isCriticallyActivated zeroActivationState uniformWeights
#eval isCriticallyActivated fullActivationState uniformWeights

#eval verdictToRegime (evaluateActivation zeroActivationState defaultThresholds uniformWeights)
#eval verdictToRegime (evaluateActivation fullActivationState defaultThresholds stressDominantWeights)

end Semantics.ThresholdVector
