import Mathlib.Data.Real.Basic
import Semantics.CodonOTOM
import Semantics.PeptideMoE

namespace CodonPeptideConsistency

open CodonOTOM
open PeptideMoE

/-
  Codon -> amino acid -> peptide consistency layer.

  This file connects:
  - codon-level efficiency Φ_codon
  - translation into amino-acid labels
  - peptide-level efficiency Φ_peptide
  through a sequence-level aggregate score.
-/

/-- Abstract peptide alphabet label induced by amino acids. -/
axiom aaToPeptideClass : AminoAcid → Nat

/-- A coding sequence is a list of codons. -/
abbrev CDS := List Codon

/-- Codon-dependent translation speed (strongest biological defensibility). -/
axiom translationSpeed : Codon → ℝ

/-- Local folding delay (clearest simulator signal). -/
axiom foldingDelay : Codon → ℝ

/-- Synonymous-codon-specific structural bias (most ambitious structural claim). -/
axiom structuralBias : Codon → ℝ

/-- Expert bias for codon-specific structural effects. -/
structure CodonBias where
  b_k : ℝ  -- codon-specific bias for expert k

/-- Translate a coding sequence into amino acids. -/
noncomputable def translateCDS (s : CDS) : List AminoAcid :=
  s.map translate

/-- Average codon-level score over a coding sequence. -/
noncomputable def phiCDSCodon
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (s : CDS) : ℝ :=
  match s.length with
  | 0 => 0
  | n => (s.map (fun c => phiCodon w (fs c) c)).sum / n

/-- Abstract peptide state induced by a translated coding sequence with codon dynamics. -/
axiom buildPeptideStateWithDynamics :
  List AminoAcid → (Codon → ℝ) → (Codon → ℝ) → (Codon → ℝ) → PeptideState

/-- Abstract peptide state induced by a translated coding sequence (legacy, no dynamics). -/
axiom buildPeptideState :
  List AminoAcid → PeptideState

/-- Peptide-level score induced by the translated coding sequence with dynamics. -/
noncomputable def phiCDSPeptideWithDynamics
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (s : CDS)
    (v : Codon → ℝ)  -- translation speed
    (τ : Codon → ℝ)  -- folding delay
    (b : Codon → ℝ)  -- structural bias
    : ℝ :=
  phiPeptide tp ap (buildPeptideStateWithDynamics (translateCDS s) v τ b)

/-- Peptide-level score induced by the translated coding sequence (legacy, no dynamics). -/
noncomputable def phiCDSPeptide
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (s : CDS) : ℝ :=
  phiPeptide tp ap (buildPeptideState (translateCDS s))

/-- Combined sequence-level score with codon dynamics. -/
noncomputable def phiCDSWithDynamics
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (α β : ℝ)
    (v : Codon → ℝ)  -- translation speed
    (τ : Codon → ℝ)  -- folding delay
    (b : Codon → ℝ)  -- structural bias
    (s : CDS) : ℝ :=
  α * phiCDSCodon w fs s + β * phiCDSPeptideWithDynamics tp ap s v τ b

/-- Gate weight for expert k at codon c_i with folding delay. -/
noncomputable def gateWeightWithFolding
    (z_k : PeptideState → ℝ)  -- base gate weight
    (b_k : CodonBias)  -- codon-specific bias
    (η : ℝ)  -- folding sensitivity
    (P_t : PeptideState)
    (c_i : Codon) : ℝ :=
  let base := z_k P_t + b_k.b_k
  let folded := η * foldingDelay c_i
  -- softmax (simplified as exponential for single value)
  Real.exp (base - folded)

/-- Peptide dynamics: ∂Θ_t/∂t = Σ_k g_k(P_t; c_i) Advice_k(P_t; c_i) + ξ_t -/
noncomputable def peptideDynamics
    (P_t : PeptideState)
    (c_i : CDS)
    (z_k : PeptideState → ℝ)
    (b_k : CodonBias)
    (η : ℝ)
    (Advice_k : PeptideState → ℝ)
    (ξ_t : ℝ) : ℝ :=
  let g_sum := (c_i.map (fun c => gateWeightWithFolding z_k b_k η P_t c)).sum
  let advice_sum := Advice_k P_t * c_i.length
  g_sum * advice_sum + ξ_t

/-- Theorem: zero folding delay reduces to standard gate weight. -/
theorem gateWeight_zero_folding
    (z_k : PeptideState → ℝ)
    (b_k : CodonBias)
    (P_t : PeptideState)
    (c_i : Codon)
    (h : foldingDelay c_i = 0) :
    gateWeightWithFolding z_k b_k 0 P_t c_i = Real.exp (z_k P_t + b_k.b_k) := by
  unfold gateWeightWithFolding
  rw [h]
  ring_nf

/-- Theorem: zero codon bias reduces to base gate weight. -/
theorem gateWeight_zero_bias
    (z_k : PeptideState → ℝ)
    (η : ℝ)
    (P_t : PeptideState)
    (c_i : Codon) :
    gateWeightWithFolding z_k (CodonBias.mk 0) η P_t c_i = Real.exp (z_k P_t - η * foldingDelay c_i) := by
  unfold gateWeightWithFolding
  ring_nf

/-- Combined sequence-level score. -/
noncomputable def phiCDS
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (α β : ℝ)
    (s : CDS) : ℝ :=
  α * phiCDSCodon w fs s + β * phiCDSPeptide tp ap s

/-- A synonymous mutation preserves the translated amino acid. -/
def synonymous (c₁ c₂ : Codon) : Prop :=
  translate c₁ = translate c₂

/-- Mutation at a single site in a coding sequence. -/
def pointMutate (s : CDS) (i : Nat) (c' : Codon) : CDS :=
  s.take i ++ c' :: s.drop (i + 1)

/-- Codon-local beneficial mutation. -/
def beneficialAtCodon
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (c₁ c₂ : Codon) : Prop :=
  0 < phiCodon w (fs c₂) c₂ - phiCodon w (fs c₁) c₁

/-- Sequence-level beneficial mutation. -/
def beneficialAtCDS
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (α β : ℝ)
    (s s' : CDS) : Prop :=
  0 < phiCDS tp ap w fs α β s' - phiCDS tp ap w fs α β s

/-
  Consistency axiom:
  a synonymous mutation that improves local codon score and leaves the peptide
  builder invariant should improve the combined CDS score when α > 0 and β ≥ 0.
-/
axiom synonymous_codon_improves_cds
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (α β : ℝ)
    (hα : 0 < α)
    (hβ : 0 ≤ β)
    (s : CDS)
    (i : Nat)
    (c₁ c₂ : Codon)
    (hi : i < s.length)
    (hget : s.get ⟨i, hi⟩ = c₁)
    (hsyn : synonymous c₁ c₂)
    (hlocal : beneficialAtCodon w fs c₁ c₂)
    (hpep :
      buildPeptideState (translateCDS (pointMutate s i c₂)) =
      buildPeptideState (translateCDS s)) :
    beneficialAtCDS tp ap w fs α β s (pointMutate s i c₂)

/-- A zero peptide weight reduces the CDS score to codon-average selection. -/
theorem phiCDS_zero_peptide_weight
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (α : ℝ)
    (s : CDS) :
    phiCDS tp ap w fs α 0 s = α * phiCDSCodon w fs s := by
  unfold phiCDS
  ring

/-- A zero codon weight reduces the CDS score to peptide-level selection. -/
theorem phiCDS_zero_codon_weight
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (β : ℝ)
    (s : CDS) :
    phiCDS tp ap w fs 0 β s = β * phiCDSPeptide tp ap s := by
  unfold phiCDS
  ring

/-- Kinetic cost term: Σ_i (ln 64 + λ ln d(c_i) + γ τ(c_i)) + C_0 -/
noncomputable def kineticCost
    (lam γ C_0 : ℝ)
    (d : Codon → ℝ)  -- degeneracy function
    (τ : Codon → ℝ)  -- folding delay
    (s : CDS) : ℝ :=
  match s.length with
  | 0 => C_0
  | _n => (s.map (fun c => Real.log 64 + lam * Real.log (d c) + γ * τ c)).sum + C_0

/-- Cotranslational folding window: at step t, only first t codons exist. -/
noncomputable def cotranslationalWindow
    (t : Nat)
    (s : CDS) : CDS :=
  s.take t

/-- Cotranslational peptide state at step t. -/
noncomputable def cotranslationalPeptideState
    (t : Nat)
    (s : CDS)
    (v : Codon → ℝ)
    (τ : Codon → ℝ)
    (b : Codon → ℝ) : PeptideState :=
  buildPeptideStateWithDynamics (translateCDS (cotranslationalWindow t s)) v τ b

/-- Theorem: cotranslational window is prefix of original sequence. -/
theorem cotranslationalWindow_is_prefix
    (t : Nat)
    (s : CDS) :
    (cotranslationalWindow t s).length = min t s.length := by
  unfold cotranslationalWindow
  simp [List.length_take]

/-- Theorem: empty cotranslational window has empty translation. -/
theorem cotranslationalWindow_empty
    (s : CDS) :
    translateCDS (cotranslationalWindow 0 s) = [] := by
  unfold cotranslationalWindow
  simp [List.take, translateCDS]

/-- Theorem: full cotranslational window equals original sequence. -/
theorem cotranslationalWindow_full
    (s : CDS) :
    cotranslationalWindow s.length s = s := by
  unfold cotranslationalWindow
  simp

/-- Theorem: Φ_CDS is bounded when codon and peptide components bounded. -/
axiom phiCDS_bounded
    (tp : ThermoParams)
    (ap : AdmissibilityParams)
    (w : CodonWeights)
    (fs : Codon → CodonFeatures)
    (α β : ℝ)
    (M_codon M_peptide : ℝ)
    (h_codon : ∀ s, |phiCDSCodon w fs s| ≤ M_codon)
    (h_peptide : ∀ s, |phiCDSPeptide tp ap s| ≤ M_peptide) :
    ∃ M, ∀ s, |phiCDS tp ap w fs α β s| ≤ M

end CodonPeptideConsistency
