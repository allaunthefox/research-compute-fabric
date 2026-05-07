import Mathlib.Data.Real.Basic
import Mathlib.Data.List.Basic
import Semantics.PeptideMoE

noncomputable section

namespace PeptideMoEExamples
open PeptideMoE

noncomputable def tp : ThermoParams :=
  { kB := 1.0, temperature := 1.0 }

noncomputable def ap : AdmissibilityParams :=
  { stericMax := 5.0, bondMax := 5.0, phiMin := -3.14159, phiMax := 3.14159,
    psiMin := -3.14159, psiMax := 3.14159, c0 := 8.0 }

noncomputable def helixState : PeptideState :=
  { phi := -1.0, psi := -0.7, internalEnergy := 1.2, conformationalEntropy := 0.9,
    structuralCoherence := 2.8, stericEnergy := 0.6, bondEnergy := 0.8 }

noncomputable def sheetState : PeptideState :=
  { phi := -2.2, psi := 2.2, internalEnergy := 1.5, conformationalEntropy := 1.0,
    structuralCoherence := 2.5, stericEnergy := 0.8, bondEnergy := 0.9 }

noncomputable def clashState : PeptideState :=
  { phi := 0.4, psi := 0.4, internalEnergy := 2.0, conformationalEntropy := 1.6,
    structuralCoherence := 3.0, stericEnergy := 9.0, bondEnergy := 0.7 }

noncomputable def helixExpert : Expert :=
  { name := "helix", gate := fun P => if P.phi < -0.5 then 0.6 else 0.2,
    advicePhi := fun P => - (P.phi + 1.0), advicePsi := fun P => - (P.psi + 0.7) }

noncomputable def sheetExpert : Expert :=
  { name := "sheet", gate := fun P => if P.psi > 1.0 then 0.6 else 0.2,
    advicePhi := fun P => - (P.phi + 2.2), advicePsi := fun P => - (P.psi - 2.2) }

noncomputable def loopExpert : Expert :=
  { name := "loop", gate := fun _ => 0.2,
    advicePhi := fun P => - P.phi / 2, advicePsi := fun P => - P.psi / 2 }

noncomputable def experts : List Expert := [helixExpert, sheetExpert, loopExpert]

noncomputable def candidates : List Candidate :=
  [ { state := helixState, label := "helix" }
  , { state := sheetState, label := "sheet" }
  , { state := clashState, label := "clash" } ]

noncomputable def gradPhiToy : PeptideState → ℝ := fun P => P.phi
noncomputable def gradPsiToy : PeptideState → ℝ := fun P => P.psi

noncomputable def helixUsefulnessOnHelix : ℝ :=
  expertUsefulness gradPhiToy gradPsiToy helixExpert helixState

noncomputable def sheetUsefulnessOnHelix : ℝ :=
  expertUsefulness gradPhiToy gradPsiToy sheetExpert helixState

noncomputable def report : List (String × ℝ × ℝ × ℝ) :=
  candidateReport tp ap candidates

noncomputable def best : Option Candidate :=
  bestCandidate? tp ap candidates

end PeptideMoEExamples
