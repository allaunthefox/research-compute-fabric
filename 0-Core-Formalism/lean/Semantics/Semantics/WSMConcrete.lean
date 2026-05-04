import Mathlib.Data.Complex.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Matrix.Diagonal
import Mathlib.Data.Fin.Basic
import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Tactic

open Complex

namespace WSMConcrete

noncomputable section

abbrev Time := ℝ
abbrev State4 := Fin 4 → ℂ
abbrev Op4 := Matrix (Fin 4) (Fin 4) ℂ
abbrev Signal := Time → ℝ
abbrev Feature2 := Fin 2 → ℝ
abbrev Probe2 := Fin 2 → ℝ
abbrev Coarse1 := Fin 1 → ℝ

def sigAdd (s₁ s₂ : Signal) : Signal := fun t => s₁ t + s₂ t
def sigScale (a : ℝ) (s : Signal) : Signal := fun t => a * s t

infixl:65 " ⊞ " => sigAdd

def applyOp (A : Op4) (ψ : State4) : State4 :=
  A.mulVec ψ

def cInner (x y : State4) : ℂ :=
  star (x 0) * y 0 + star (x 1) * y 1 + star (x 2) * y 2 + star (x 3) * y 3

def expect (ψ : State4) (A : Op4) : ℝ :=
  Complex.re (cInner ψ (applyOp A ψ))

def finiteDiff (dt : ℝ) (s : Signal) : Signal :=
  fun t => (s (t + dt) - s t) / dt

/-
Concrete wavefunction ψ(t) ∈ ℂ⁴.
Only the first two amplitudes vary with time.
-/
def ψ : Time → State4 :=
  fun t =>
    ![
      (Real.cos t : ℂ),
      (Real.sin t : ℂ),
      0,
      0
    ]

/-
Explicit Hamiltonian:
diag(1,2,3,4)
-/
def H : Op4 :=
  !![
    (1 : ℂ), 0, 0, 0;
    0, (2 : ℂ), 0, 0;
    0, 0, (3 : ℂ), 0;
    0, 0, 0, (4 : ℂ)
  ]

/-
Two observable channels:
O₀ projects onto coordinate 0
O₁ projects onto coordinate 1
-/
def O0 : Op4 :=
  !![
    (1 : ℂ), 0, 0, 0;
    0, 0, 0, 0;
    0, 0, 0, 0;
    0, 0, 0, 0
  ]

def O1 : Op4 :=
  !![
    0, 0, 0, 0;
    0, (1 : ℂ), 0, 0;
    0, 0, 0, 0;
    0, 0, 0, 0
  ]

def Obs : Fin 2 → Op4
  | 0 => O0
  | 1 => O1

/-
Weights for the two channels.
-/
def w : Fin 2 → ℝ
  | 0 => 1.0
  | 1 => 0.5

def recordingChannel (O : Op4) : Signal :=
  fun t => expect (ψ t) O

def shapeWaveform : Signal :=
  fun t => w 0 * recordingChannel (Obs 0) t + w 1 * recordingChannel (Obs 1) t

def energySignal : Signal :=
  fun t => expect (ψ t) H

def temporalEnergyGradient (dt : ℝ) : Signal :=
  finiteDiff dt energySignal

/-
Toy spatial gradient channel.
You can replace this with anything more physical later.
-/
def gSpatial : Signal :=
  fun t => |Real.sin t|

def energyGradientMagnitude (dt : ℝ) : Signal :=
  fun t =>
    Real.sqrt ((temporalEnergyGradient dt t)^2 + (gSpatial t)^2)

def energyIncrease (dt : ℝ) : Signal :=
  fun t => max (temporalEnergyGradient dt t) 0

def energyDecrease (dt : ℝ) : Signal :=
  fun t => max (- temporalEnergyGradient dt t) 0

/-
Toy shape-energy coupling channel.
-/
def ΓSE : Signal :=
  fun t => Real.cos t * Real.sin t

/-
Toy noise channel.
-/
def η : Signal :=
  fun _ => 0.0

def totalSignal (dt : ℝ) (lambdaE : ℝ) (lambdaC : ℝ) : Signal :=
  shapeWaveform
  ⊞ sigScale lambdaE (energyGradientMagnitude dt)
  ⊞ sigScale lambdaC ΓSE
  ⊞ η

/-
Toy feature extractor:
sample the total signal at t=0 and t=1.
So F[S] = [S(0), S(1)] ∈ ℝ².
-/
def F (S : Signal) : Feature2 :=
  ![
    S 0,
    S 1
  ]

/-
Explicit waveprobe matrix W : ℝ² → ℝ².
-/
def W : Matrix (Fin 2) (Fin 2) ℝ :=
  !![
    (1 : ℝ), 2;
    (-1 : ℝ), 1
  ]

/-
Explicit coarse-graining matrix C : ℝ² → ℝ¹.
-/
def C : Matrix (Fin 1) (Fin 2) ℝ :=
  !![
    (0.5 : ℝ), 0.5
  ]

def probeState (dt : ℝ) (lambdaE : ℝ) (lambdaC : ℝ) : Probe2 :=
  W.mulVec (F (totalSignal dt lambdaE lambdaC))

def coarseState (dt : ℝ) (lambdaE : ℝ) (lambdaC : ℝ) : Coarse1 :=
  C.mulVec (probeState dt lambdaE lambdaC)

/-
A few concrete evaluation helpers.
-/
def example_dt : ℝ := 0.01
def example_lambdaE : ℝ := 0.2
def example_lambdaC : ℝ := 0.1

def exampleFeature : Feature2 :=
  F (totalSignal example_dt example_lambdaE example_lambdaC)

def exampleProbe : Probe2 :=
  probeState example_dt example_lambdaE example_lambdaC

def exampleCoarse : Coarse1 :=
  coarseState example_dt example_lambdaE example_lambdaC

/-
Sanity theorems
-/

theorem shapeWaveform_def :
    shapeWaveform = fun t => w 0 * recordingChannel (Obs 0) t + w 1 * recordingChannel (Obs 1) t := by
  rfl

theorem energySignal_def :
    energySignal = fun t => expect (ψ t) H := by
  rfl

theorem totalSignal_pointwise (dt lambdaE lambdaC t : ℝ) :
    totalSignal dt lambdaE lambdaC t
      =
      shapeWaveform t
      + lambdaE * energyGradientMagnitude dt t
      + lambdaC * ΓSE t
      + η t := by
  simp [totalSignal, sigAdd, sigScale]

theorem probeState_def (dt lambdaE lambdaC : ℝ) :
    probeState dt lambdaE lambdaC = W.mulVec (F (totalSignal dt lambdaE lambdaC)) := by
  rfl

theorem coarseState_def (dt lambdaE lambdaC : ℝ) :
    coarseState dt lambdaE lambdaC = C.mulVec (W.mulVec (F (totalSignal dt lambdaE lambdaC))) := by
  rfl

/-
The full concrete composition theorem.
-/
theorem full_pipeline_is_composition (dt lambdaE lambdaC : ℝ) :
    coarseState dt lambdaE lambdaC
      =
      C.mulVec (W.mulVec (F (totalSignal dt lambdaE lambdaC))) := by
  rfl

end

end WSMConcrete
