import Mathlib.Data.Real.Basic
import Semantics.PeptideMoE
import Semantics.PeptideMoEExamples

noncomputable section

namespace PeptideMoEFailure
open PeptideMoE
open PeptideMoEExamples

noncomputable def badApZeroC0 : AdmissibilityParams :=
  { stericMax := (100 : ℝ), bondMax := (5 : ℝ), phiMin := -3.14159, phiMax := 3.14159,
    psiMin := -3.14159, psiMax := 3.14159, c0 := (0 : ℝ) }

noncomputable def singularState : PeptideState :=
  { phi := (0 : ℝ), psi := (0 : ℝ), internalEnergy := (0 : ℝ), conformationalEntropy := (0 : ℝ),
    structuralCoherence := (1 : ℝ), stericEnergy := (0 : ℝ), bondEnergy := (0 : ℝ) }

noncomputable def negativeGateExpert : Expert :=
  { name := "negative", gate := fun _ => (-1/2 : ℝ),
    advicePhi := fun _ => (1 : ℝ), advicePsi := fun _ => (1 : ℝ) }

noncomputable def explosiveExpert : Expert :=
  { name := "explosive", gate := fun _ => (1 : ℝ),
    advicePhi := fun _ => (1000000 : ℝ), advicePsi := fun _ => (1000000 : ℝ) }

noncomputable def badCandidates : List Candidate :=
  [ { state := singularState, label := "singular" }
  , { state := clashState, label := "clash" } ]

end PeptideMoEFailure
