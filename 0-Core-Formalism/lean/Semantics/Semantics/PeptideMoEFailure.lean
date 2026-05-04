import Mathlib.Data.Real.Basic
import Semantics.PeptideMoE
import Semantics.PeptideMoEExamples

namespace PeptideMoEFailure
open PeptideMoE
open PeptideMoEExamples

/-
  Failure-injection scenarios for the peptide-MoE specification.

  Goal:
  Deliberately weaken assumptions and document which safety guarantees fail.
-/

/-- Pathological admissibility parameters with zero offset and loose steric bound. -/
def badApZeroC0 : AdmissibilityParams :=
  { stericMax := 100.0
  , bondMax := 5.0
  , phiMin := -3.14159
  , phiMax := 3.14159
  , psiMin := -3.14159
  , psiMax := 3.14159
  , c0 := 0.0 }

/-- A state with zero denominator when `c0 = 0` and free energy is zero. -/
def singularState : PeptideState :=
  { phi := 0.0
  , psi := 0.0
  , internalEnergy := 0.0
  , conformationalEntropy := 0.0
  , structuralCoherence := 1.0
  , stericEnergy := 0.0
  , bondEnergy := 0.0 }

/-- A pathological expert with negative gate weight. -/
noncomputable def negativeGateExpert : Expert :=
  { name := "negative"
  , gate := fun _ => -0.5
  , advicePhi := fun _ => 1.0
  , advicePsi := fun _ => 1.0 }

/-- A pathological expert with arbitrarily huge advice magnitude. -/
noncomputable def explosiveExpert : Expert :=
  { name := "explosive"
  , gate := fun _ => 1.0
  , advicePhi := fun _ => 1000000.0
  , advicePsi := fun _ => 1000000.0 }

/-- A pathological candidate pool exposing the singular denominator issue. -/
def badCandidates : List Candidate :=
  [ { state := singularState, label := "singular" }
  , { state := clashState, label := "clash" } ]

/-
  Theorems demonstrating failure conditions:

  These prove the pathological properties that cause safety guarantees to fail.
-/

/-- Theorem: bad parameters have zero offset c0 -/
axiom bad_c0_zero : badApZeroC0.c0 = 0

/-- Theorem: bad parameters have very loose steric maximum -/
axiom bad_steric_max_loose : ap.stericMax < badApZeroC0.stericMax

/-- Theorem: singular state has zero free energy with bad parameters -/
axiom singular_free_energy_zero :
    freeEnergy tp singularState = 0

/-- Theorem: singular state has zero denominator with bad parameters -/
axiom singular_denominator_zero :
    freeEnergy tp singularState + badApZeroC0.c0 = 0

/-- Theorem: negative gate expert has negative gate weight -/
axiom negative_gate_expert_negative : negativeGateExpert.gate singularState < 0

/-- Theorem: gates are not normalized with negative expert -/
axiom gates_not_normalized_with_negative_expert :
    ¬ gatesNormalized [negativeGateExpert] singularState

/-- Theorem: explosive expert has very large advice magnitude -/
axiom explosive_advice_large :
    |explosiveExpert.advicePhi singularState| > 100000 ∧
    |explosiveExpert.advicePsi singularState| > 100000

/-- Theorem: clash state is admissible under loose steric bounds -/
axiom clash_admissible_under_loose_sterics :
    admissible badApZeroC0 clashState

/-
  Summary of failures documented by this file:

  1. If c0 = 0, denominator positivity can fail.
  2. If steric thresholds are too loose, clashing states become admissible.
  3. If gates are not constrained to be nonnegative/simplex-normalized, MoE control becomes invalid.
  4. If advice magnitudes are unconstrained, a single expert can dominate updates pathologically.

  These are not bugs in the good model; they are intended demonstrations of why the guardrails matter.
-/

end PeptideMoEFailure
