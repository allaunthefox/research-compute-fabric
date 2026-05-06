import Mathlib.Data.Real.Basic
import Mathlib.Data.List.Basic

/-!
  PeptideMoE.lean — Mixture-of-Experts for Peptide Conformational Analysis

  This module formalizes a Mixture-of-Experts (MoE) system for peptide
  conformational state analysis, incorporating thermodynamic parameters,
  admissibility constraints, and expert coordination.

  Purpose: Mathematical formalization of peptide conformational search
  using expert gating, thermodynamic scoring, and constraint-based filtering.

  Key structures:
  - PeptideState: Conformational state (φ, ψ angles, energies)
  - Expert: MoE expert with gating and advice functions
  - AdmissibilityParams: Steric/bond/angle constraints
  - ThermoParams: Temperature and Boltzmann constant

  The module provides functions for:
  - Free energy computation
  - Admissibility checking
  - Score filtering and penalization
  - Expert usefulness evaluation
  - Candidate selection and reporting
-/

namespace PeptideMoE

/-- Peptide conformational state with Ramachandran angles and energies -/
structure PeptideState where
  phi : ℝ
  psi : ℝ
  internalEnergy : ℝ
  conformationalEntropy : ℝ
  structuralCoherence : ℝ
  stericEnergy : ℝ
  bondEnergy : ℝ

/-- MoE expert with gating function and advice for φ/ψ angles -/
structure Expert where
  name : String
  gate : PeptideState → ℝ
  advicePhi : PeptideState → ℝ
  advicePsi : PeptideState → ℝ

/-- Candidate peptide conformation with label -/
structure Candidate where
  state : PeptideState
  label : String

/-- Admissibility parameters for conformational constraints -/
structure AdmissibilityParams where
  stericMax : ℝ
  bondMax : ℝ
  phiMin : ℝ
  phiMax : ℝ
  psiMin : ℝ
  psiMax : ℝ
  c0 : ℝ

/-- Thermodynamic parameters for free energy computation -/
structure ThermoParams where
  kB : ℝ
  temperature : ℝ

/-- Learning parameters for gate weight updates -/
structure LearningParams where
  learningRate : ℝ
  updateSignal : PeptideState → Expert → ℝ
  previousEfficiency : ℝ  -- Track previous efficiency for ΔΦ computation

/-- Free energy: E + kB·T·S -/
noncomputable def freeEnergy (tp : ThermoParams) (P : PeptideState) : ℝ :=
  P.internalEnergy + tp.kB * tp.temperature * P.conformationalEntropy

/-- Cost function: C(x) - measures computational or thermodynamic cost -/
noncomputable def costFunction (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState) : ℝ :=
  freeEnergy tp P + ap.c0

/-- Utility function: U(x) - measures structural coherence or benefit -/
noncomputable def utilityFunction (P : PeptideState) : ℝ :=
  P.structuralCoherence

/-- Efficiency metric: Φ(x) = C(x) / U(x) - cost/utility ratio -/
noncomputable def efficiency (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState) : ℝ :=
  costFunction tp ap P / utilityFunction P

/-- φ-peptide score: structural coherence / (free energy + c0) - legacy name for efficiency -/
noncomputable def phiPeptide (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState) : ℝ :=
  efficiency tp ap P

/-- Admissibility predicate: steric, bond, and angle constraints -/
def admissible (ap : AdmissibilityParams) (P : PeptideState) : Prop :=
  ap.phiMin ≤ P.phi ∧ P.phi ≤ ap.phiMax ∧
  ap.psiMin ≤ P.psi ∧ P.psi ≤ ap.psiMax ∧
  P.stericEnergy < ap.stericMax ∧
  P.bondEnergy < ap.bondMax

noncomputable instance decidableAdmissible (ap : AdmissibilityParams) (P : PeptideState) : Decidable (admissible ap P) :=
  inferInstanceAs (Decidable (ap.phiMin ≤ P.phi ∧ P.phi ≤ ap.phiMax ∧
                          ap.psiMin ≤ P.psi ∧ P.psi ≤ ap.psiMax ∧
                          P.stericEnergy < ap.stericMax ∧
                          P.bondEnergy < ap.bondMax))

/-- Admissibility indicator: 1 if admissible, 0 otherwise -/
noncomputable def admissibilityIndicator (ap : AdmissibilityParams) (P : PeptideState) : ℝ :=
  if admissible ap P then 1 else 0

/-- Filtered score: zero if not admissible, otherwise φ-peptide score -/
noncomputable def filteredScore (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState) : ℝ :=
  admissibilityIndicator ap P * phiPeptide tp ap P

/-- Penalized score: subtract penalty if not admissible -/
noncomputable def penalizedScore (tp : ThermoParams) (ap : AdmissibilityParams) (penalty : ℝ) (P : PeptideState) : ℝ :=
  phiPeptide tp ap P - (if admissible ap P then 0 else penalty)

/-- Expert usefulness: negative of gate-weighted advice alignment with gradient -/
def expertUsefulness
    (gradPhi gradPsi : PeptideState → ℝ)
    (E : Expert)
    (P : PeptideState) : ℝ :=
  -(E.gate P) * ((E.advicePhi P) * (gradPhi P) + (E.advicePsi P) * (gradPsi P))

/-- Expert helpful predicate: usefulness is non-negative -/
def expertHelpful
    (gradPhi gradPsi : PeptideState → ℝ)
    (E : Expert)
    (P : PeptideState) : Prop :=
  0 ≤ expertUsefulness gradPhi gradPsi E P

/-- MoE drift: sum of gate-weighted advice across all experts -/
def moeDrift (experts : List Expert) (P : PeptideState) : ℝ × ℝ :=
  let dphi := List.sum (experts.map fun E => E.gate P * E.advicePhi P)
  let dpsi := List.sum (experts.map fun E => E.gate P * E.advicePsi P)
  (dphi, dpsi)

/-- Gates normalized: sum to 1, all non-negative -/
def gatesNormalized (experts : List Expert) (P : PeptideState) : Prop :=
  0 ≤ List.sum (experts.map fun E => E.gate P) ∧
  List.sum (experts.map fun E => E.gate P) = 1 ∧
  ∀ E ∈ experts, 0 ≤ E.gate P

/-- Gate weight update: z_k' = z_k + α ΔΦ · U_k(t) where ΔΦ = Φ(x) - Φ_prev -/
noncomputable def gateUpdate
    (lp : LearningParams)
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (E : Expert)
    (P : PeptideState) : ℝ :=
  let currentEfficiency := efficiency tp ap P
  let deltaEfficiency := currentEfficiency - lp.previousEfficiency
  E.gate P + lp.learningRate * deltaEfficiency * lp.updateSignal P E

/-- Temporal transformation T(P_t, z_t) = (∂t/∂Θ_t, z_{k(t+1)}) -/
structure TemporalTransformation where
  driftPhi : ℝ
  driftPsi : ℝ
  updatedGates : List Expert

/-- Apply temporal transformation: compute drift and update all gate weights -/
noncomputable def applyTemporalTransformation
    (lp : LearningParams)
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (experts : List Expert)
    (P : PeptideState) : TemporalTransformation :=
  let drift := moeDrift experts P
  let updatedExperts := experts.map fun E =>
    { name := E.name
    , gate := fun _ => gateUpdate lp tp ap E P
    , advicePhi := E.advicePhi
    , advicePsi := E.advicePsi }
  { driftPhi := drift.1
  , driftPsi := drift.2
  , updatedGates := updatedExperts }

/-- Best candidate: fold-based selection maximizing filtered score among admissible candidates -/
noncomputable def bestCandidate?
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (cands : List Candidate) : Option Candidate :=
  cands.foldl
    (fun best cand =>
      match best with
      | none =>
          if admissible ap cand.state then some cand else none
      | some b =>
          if admissible ap cand.state ∧
             filteredScore tp ap b.state < filteredScore tp ap cand.state
          then some cand
          else some b)
    none

/-- Candidate report: label, free energy, φ-peptide score, filtered score -/
noncomputable def candidateReport
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (cands : List Candidate) : List (String × ℝ × ℝ × ℝ) :=
  cands.map fun c =>
    ( c.label
    , freeEnergy tp c.state
    , phiPeptide tp ap c.state
    , filteredScore tp ap c.state
    )

/-- Denominator safe: free energy + c0 is positive -/
def denominatorSafe (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState) : Prop :=
  0 < freeEnergy tp P + ap.c0

/-- All denominators safe: holds for all candidates -/
def allDenominatorsSafe (tp : ThermoParams) (ap : AdmissibilityParams) (cands : List Candidate) : Prop :=
  ∀ c ∈ cands, denominatorSafe tp ap c.state

/-- Theorem: filtered score is zero when not admissible -/
theorem filteredScore_of_not_admissible
    (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState)
    (h : ¬ admissible ap P) :
    filteredScore tp ap P = 0 := by
  unfold filteredScore admissibilityIndicator
  split
  · contradiction
  · simp

/-- Theorem: filtered score equals φ-peptide score when admissible -/
theorem filteredScore_of_admissible
    (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState)
    (h : admissible ap P) :
    filteredScore tp ap P = phiPeptide tp ap P := by
  unfold filteredScore admissibilityIndicator
  split
  · simp
  · contradiction

/-- Theorem: expert helpful iff usefulness is non-negative (reflexive) -/
theorem expertHelpful_iff
    (gradPhi gradPsi : PeptideState → ℝ)
    (E : Expert) (P : PeptideState) :
    expertHelpful gradPhi gradPsi E P ↔ 0 ≤ expertUsefulness gradPhi gradPsi E P := by
  rfl

/-- Theorem: gate mass is one when gates are normalized -/
theorem gate_mass_one
    (experts : List Expert) (P : PeptideState)
    (h : gatesNormalized experts P) :
    List.sum (experts.map fun E => E.gate P) = 1 := by
  exact h.2.1

/-
  Intended invariant:
  Any candidate returned by `bestCandidate?` should be admissible.
  This is an external correctness property of the fold-based selection.
-/
structure BestCandidateAdmissibleHypothesis where
  property (tp : ThermoParams) (ap : AdmissibilityParams) (cands : List Candidate) (c : Candidate) :
    bestCandidate? tp ap cands = some c → admissible ap c.state

/-
  Transformation T(P_t) properties:

  The transformation T(P_t) = (∂t/∂Θ_t, Φ_filtered[P_t]) should preserve
  key invariants of the peptide-MoE system.
-/

/-- Theorem: filtered score is zero when not admissible -/
theorem filteredScore_zero_of_not_admissible
    (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState)
    (h : ¬ admissible ap P) :
    filteredScore tp ap P = 0 := by
  unfold filteredScore admissibilityIndicator
  split
  · contradiction
  · simp

/-- Theorem: filtered score equals φ_peptide when admissible -/
theorem filteredScore_eq_phiPeptide_of_admissible
    (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState)
    (h : admissible ap P) :
    filteredScore tp ap P = phiPeptide tp ap P := by
  unfold filteredScore admissibilityIndicator
  split
  · simp
  · contradiction

/-- Hypothesis: filtered score is bounded when structural coherence is bounded -/
structure FilteredScoreBoundedHypothesis where
  property (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState)
    (h : 0 ≤ P.structuralCoherence) (hdenom : 0 < freeEnergy tp P + ap.c0) :
    0 ≤ filteredScore tp ap P ∧ filteredScore tp ap P ≤ P.structuralCoherence

/-- Hypothesis: φ_peptide is positive when denominator is safe and structural coherence is positive -/
structure PhiPeptidePosHypothesis where
  property (tp : ThermoParams) (ap : AdmissibilityParams) (P : PeptideState)
    (h : 0 < P.structuralCoherence) (hdenom : 0 < freeEnergy tp P + ap.c0) :
    0 < phiPeptide tp ap P

/-- Hypothesis: MoE drift is bounded when expert advice is bounded -/
structure MoEDriftBoundedHypothesis where
  property (B : ℝ) (experts : List Expert) (P : PeptideState)
    (hgate : gatesNormalized experts P)
    (hbound : ∀ E ∈ experts, |E.advicePhi P| ≤ B ∧ |E.advicePsi P| ≤ B) :
    |(moeDrift experts P).1| ≤ B ∧ |(moeDrift experts P).2| ≤ B

/-- Hypothesis: MoE drift preserves angle bounds when gates are normalized -/
structure MoEDriftPreservesBoundsHypothesis where
  property (experts : List Expert) (ap : AdmissibilityParams) (P : PeptideState)
    (hgate : gatesNormalized experts P) (h : admissible ap P)
    (hbound : ∀ E ∈ experts, |E.advicePhi P| ≤ 1 ∧ |E.advicePsi P| ≤ 1) :
    ap.phiMin ≤ P.phi + (moeDrift experts P).1 ∧
    P.phi + (moeDrift experts P).1 ≤ ap.phiMax ∧
    ap.psiMin ≤ P.psi + (moeDrift experts P).2 ∧
    P.psi + (moeDrift experts P).2 ≤ ap.psiMax

end PeptideMoE
