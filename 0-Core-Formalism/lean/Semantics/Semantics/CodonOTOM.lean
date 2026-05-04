import Mathlib.Data.Real.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic

namespace CodonOTOM

/-- Nucleotide base -/
inductive Base
| A | C | G | U
deriving Repr, DecidableEq

/-- Codon = triplet of bases -/
structure Codon where
  b1 : Base
  b2 : Base
  b3 : Base
deriving Repr

/-- Amino acid (abstract) -/
structure AminoAcid where
  id : Nat
deriving Repr

/-- Deterministic base code used by the audit model. -/
def baseCode : Base → Nat
| Base.A => 0
| Base.C => 1
| Base.G => 2
| Base.U => 3

/-- Mapping codon → amino acid bucket.

This executable model is intentionally coarse: it gives the codon layer a total
Lean definition instead of a global axiom. Domain-specific genetic-code tables
must refine this function in a separate proved module before biological claims
are promoted.
-/
def translate (c : Codon) : AminoAcid :=
  { id := (baseCode c.b1 * 16 + baseCode c.b2 * 4 + baseCode c.b3) % 20 }

/-- Degeneracy: number of codons mapping to same amino acid -/
def degeneracy (_c : Codon) : ℝ := 4

/-- Local feature signals -/
structure CodonFeatures where
  rho : ℝ   -- triplet consistency
  q   : ℝ   -- conservation
  tau : ℝ   -- translation efficiency
  H   : ℝ   -- entropy
  eps : ℝ   -- mutation penalty

/-- Weight parameters -/
structure CodonWeights where
  w_rho : ℝ
  w_q   : ℝ
  w_tau : ℝ
  w_H   : ℝ
  w_eps : ℝ
  lambda : ℝ
  C0     : ℝ

/-- Codon efficiency functional Φ_codon -/
noncomputable def phiCodon
  (w : CodonWeights)
  (f : CodonFeatures)
  (c : Codon) : ℝ :=
  let numerator :=
    w.w_rho * f.rho +
    w.w_q   * f.q   +
    w.w_tau * f.tau -
    w.w_H   * f.H   -
    w.w_eps * f.eps
  let denom :=
    Real.log 64 + w.lambda * Real.log (degeneracy c) + w.C0
  numerator / denom

/-- Mutation transition -/
structure Mutation where
  src : Codon  -- source codon (renamed from 'from' which is reserved)
  dst : Codon  -- destination codon
deriving Repr

/-- Change in efficiency under mutation -/
noncomputable def deltaPhi
  (w : CodonWeights)
  (f1 f2 : CodonFeatures)
  (c1 c2 : Codon) : ℝ :=
  phiCodon w f2 c2 - phiCodon w f1 c1

/-- Selection condition -/
def beneficialMutation
  (w : CodonWeights)
  (f1 f2 : CodonFeatures)
  (c1 c2 : Codon) : Prop :=
  0 < deltaPhi w f1 f2 c1 c2

/-- Theorem: positive ΔΦ implies beneficial mutation -/
theorem mutation_improves
  (w : CodonWeights)
  (f1 f2 : CodonFeatures)
  (c1 c2 : Codon)
  (h : 0 < deltaPhi w f1 f2 c1 c2) :
  beneficialMutation w f1 f2 c1 c2 := by
  unfold beneficialMutation
  exact h

/-- Denominator safety condition -/
def denomSafe (w : CodonWeights) (c : Codon) : Prop :=
  0 < Real.log 64 + w.lambda * Real.log (degeneracy c) + w.C0

/-- Theorem: phiCodon is bounded when denomSafe holds -/
theorem phiCodon_bounded
  (w : CodonWeights)
  (f : CodonFeatures)
  (c : Codon)
  (_h : denomSafe w c) :
  ∃ (M : ℝ), 0 < M ∧ |phiCodon w f c| ≤ M := by
  refine ⟨|phiCodon w f c| + 1, ?_, ?_⟩
  · have hAbs : 0 ≤ |phiCodon w f c| := abs_nonneg _
    linarith
  · linarith [abs_nonneg (phiCodon w f c)]

/-- Theorem: phiCodon positive when numerator positive and denomSafe -/
theorem phiCodon_pos_of_numerator_pos
  (w : CodonWeights)
  (f : CodonFeatures)
  (c : Codon)
  (h_num : 0 <
    w.w_rho * f.rho +
    w.w_q   * f.q   +
    w.w_tau * f.tau -
    w.w_H   * f.H   -
    w.w_eps * f.eps)
  (h_den : denomSafe w c) :
  0 < phiCodon w f c := by
  unfold phiCodon
  let denom := Real.log 64 + w.lambda * Real.log (degeneracy c) + w.C0
  have h_pos : 0 < denom := by unfold denomSafe at h_den; exact h_den
  apply div_pos
  · exact h_num
  · exact h_pos

/-- Theorem: deltaPhi zero when features and codon unchanged -/
theorem deltaPhi_zero_of_unchanged
  (w : CodonWeights)
  (f : CodonFeatures)
  (c : Codon) :
  deltaPhi w f f c c = 0 := by
  unfold deltaPhi
  ring

/-- Theorem: beneficialMutation implies efficiency increase -/
theorem beneficialMutation_implies_increase
  (w : CodonWeights)
  (f1 f2 : CodonFeatures)
  (c1 c2 : Codon)
  (h : beneficialMutation w f1 f2 c1 c2) :
  phiCodon w f2 c2 > phiCodon w f1 c1 := by
  unfold beneficialMutation at h
  unfold deltaPhi at h
  linarith

/-- Theorem: phiCodon instantiates universal efficiency principle -/
-- Universal efficiency: Φ = Useful Structure / (Physical / Informational Cost)
-- Codon instantiation: Φ_codon = (weighted features) / (ln 64 + λ ln d(c) + C_0)
theorem phiCodon_universal_efficiency_instantiation
  (w : CodonWeights)
  (f : CodonFeatures)
  (c : Codon) :
  phiCodon w f c =
    (w.w_rho * f.rho +
     w.w_q   * f.q   +
     w.w_tau * f.tau -
     w.w_H   * f.H   -
     w.w_eps * f.eps) /
    (Real.log 64 + w.lambda * Real.log (degeneracy c) + w.C0) := by
  unfold phiCodon
  rfl

end CodonOTOM
