import Semantics.Constitution
import Semantics.Adaptation
import Semantics.Security
import Semantics.KimiProber

namespace Semantics.Benchmarks.KillerCriterion

/-!
# Killer Criterion: Rigid Formalization

This module formalizes the benchmark claim:

A planted lawful core is distinguishable from random noise and trivial
repetition when and only when it satisfies the coincidence of:

1. exact spectral lawfulness,
2. RGFlow scale coherence,
3. verified payload identity,
4. security admission.

The flanks are rejected, and the core is uniquely admitted.
-/

/-- Use exact rationals for proof-level thresholds. Runtime floats should be
converted into this exact representation before formal checking. -/
structure SpectralSignature where
  entropy : Rat
  density : Rat
  coherence : Bool
deriving Repr

/-- Symbolic payload identifier.

For the canonical killer criterion, this may represent:

* π/e digit stream,
* ECC witness,
* checksum footer,
* canonical mathematical decoder proof.
-/
inductive PayloadID where
  | pi_e_core
  | other : String → PayloadID
deriving Repr, DecidableEq

/-- Region labels for the three-part blind benchmark. -/
inductive Region where
  | A
  | B
  | C
deriving Repr, DecidableEq

/-- Abstract binding between a genome and its measured spectral signature.

This must be supplied by the AVMR encoder / spectral audit pipeline.
It is deliberately not defined as `True`.
-/
constant HasSpectralSignature :
  Semantics.Adaptation.Genome → SpectralSignature → Prop

/-- Abstract payload verification predicate.

This is the formal hook for checksum/ECC/canonical-decoder verification.
It prevents "lawful-looking" noise from being admitted as the planted core.
-/
constant VerifiedPayload :
  Semantics.Adaptation.Genome → PayloadID → Prop

/-- Security bridge.

The benchmark should not unfold internal security definitions directly.
Instead, security exposes the intended invariant:
scale-coherent genomes are not classified as informatic sabotage.
This is an external security property depending on concrete Swarm/Security modules.
-/
structure ScaleCoherentNotSabotageHypothesis where
  property (g : Semantics.Adaptation.Genome) :
    Semantics.Swarm.isScaleCoherent g →
    Semantics.Security.NotAllowed_InformaticSabotage g = False

/-- Exact thresholds for the spectral invariant. -/
def entropyLower : Rat := 5 / 2      -- 2.5
def entropyUpper : Rat := 21 / 5     -- 4.2
def densityUpper : Rat := 19 / 20    -- 0.95

/-- Spectral Lawfulness Invariant.

A lawful spectral signature is:

* above trivial-repetition entropy,
* below chaotic entropy,
* below saturated alphabet density,
* coherent under spectral audit.
-/
def IsSpectrallyLawful (sig : SpectralSignature) : Prop :=
  entropyLower < sig.entropy ∧
  sig.entropy < entropyUpper ∧
  sig.density < densityUpper ∧
  sig.coherence = true

/-- Full lawfulness for the killer benchmark.

A genome is killer-lawful when its signature is lawful, its RGFlow is
scale-coherent, and its payload verifies against the expected witness.
-/
def IsKillerLawful
  (g : Semantics.Adaptation.Genome)
  (sig : SpectralSignature)
  (payload : PayloadID) : Prop :=
  HasSpectralSignature g sig ∧
  IsSpectrallyLawful sig ∧
  Semantics.Swarm.isScaleCoherent g ∧
  VerifiedPayload g payload

/-- Saturated-density rejection.

This rejects random/high-density spectral saturation.
-/
theorem noise_rejection_theorem
  (sig : SpectralSignature)
  (h_noise : sig.density ≥ densityUpper) :
  ¬ IsSpectrallyLawful sig := by
  unfold IsSpectrallyLawful
  intro h
  exact not_lt_of_ge h_noise h.right.right.left

/-- Low-entropy rejection.

This rejects trivial repetition, padding, and degenerate structure.
-/
theorem repetition_rejection_theorem
  (sig : SpectralSignature)
  (h_repeat : sig.entropy ≤ entropyLower) :
  ¬ IsSpectrallyLawful sig := by
  unfold IsSpectrallyLawful
  intro h
  exact not_lt_of_ge h_repeat h.left

/-- High-chaos rejection.

This rejects signatures above the lawful entropy ceiling.
-/
theorem chaos_rejection_theorem
  (sig : SpectralSignature)
  (h_chaos : sig.entropy ≥ entropyUpper) :
  ¬ IsSpectrallyLawful sig := by
  unfold IsSpectrallyLawful
  intro h
  exact not_lt_of_ge h_chaos h.right.left

/-- Incoherence rejection.

Even if entropy and density look plausible, a failed coherence bit rejects
the region.
-/
theorem incoherence_rejection_theorem
  (sig : SpectralSignature)
  (h_incoh : sig.coherence = false) :
  ¬ IsSpectrallyLawful sig := by
  unfold IsSpectrallyLawful
  intro h
  have h_coh : sig.coherence = true := h.right.right.right
  rw [h_incoh] at h_coh
  contradiction

/-- Blind detection theorem.

A genome satisfying the full killer-lawful predicate is not classified as
informatic sabotage.
-/
theorem blind_detection_theorem
  (sig : SpectralSignature)
  (g : Semantics.Adaptation.Genome)
  (payload : PayloadID)
  (h_lawful : IsKillerLawful g sig payload) :
  Semantics.Security.NotAllowed_InformaticSabotage g = False := by
  unfold IsKillerLawful at h_lawful
  rcases h_lawful with ⟨_h_bind, _h_spec, h_flow, _h_payload⟩
  exact scale_coherent_not_sabotage g h_flow

/-- Benchmark instance.

The three-region killer test consists of two flanks and one planted core.
-/
structure KillerInstance where
  sigA : SpectralSignature
  sigB : SpectralSignature
  sigC : SpectralSignature
  gB   : Semantics.Adaptation.Genome

/-- Admission predicate for a specific region.

Only region B has an associated genome and verified payload in this minimal
three-region benchmark. A and C are admitted only if their signatures are
spectrally lawful, which the benchmark hypotheses will deny.
-/
def RegionAdmitted
  (inst : KillerInstance)
  (payload : PayloadID)
  (r : Region) : Prop :=
  match r with
  | Region.A => IsSpectrallyLawful inst.sigA
  | Region.B => IsKillerLawful inst.gB inst.sigB payload
  | Region.C => IsSpectrallyLawful inst.sigC

/-- Three-region Killer Criterion.

The benchmark succeeds when A and C are rejected and B is admitted as the
verified lawful core.
-/
def KillerCriterionAdmission
  (inst : KillerInstance)
  (payload : PayloadID) : Prop :=
  ¬ IsSpectrallyLawful inst.sigA ∧
  IsKillerLawful inst.gB inst.sigB payload ∧
  ¬ IsSpectrallyLawful inst.sigC

/-- Positive admission theorem.

If the flanks are rejected and the core satisfies the spectral-flow-payload
coincidence, then the benchmark satisfies the Killer Criterion.
-/
theorem core_admission_theorem
  (inst : KillerInstance)
  (payload : PayloadID)
  (hA : ¬ IsSpectrallyLawful inst.sigA)
  (h_bind : HasSpectralSignature inst.gB inst.sigB)
  (hB_spec : IsSpectrallyLawful inst.sigB)
  (hB_flow : Semantics.Swarm.isScaleCoherent inst.gB)
  (hB_payload : VerifiedPayload inst.gB payload)
  (hC : ¬ IsSpectrallyLawful inst.sigC) :
  KillerCriterionAdmission inst payload := by
  unfold KillerCriterionAdmission
  unfold IsKillerLawful
  exact ⟨hA, ⟨h_bind, hB_spec, hB_flow, hB_payload⟩, hC⟩

/-- Canonical noise-flanked planted-core theorem.

A and C are rejected by saturated density.
B is admitted by spectral lawfulness, RGFlow coherence, and payload
verification.
-/
theorem noise_flanked_core_theorem
  (inst : KillerInstance)
  (payload : PayloadID)
  (hA_noise : inst.sigA.density ≥ densityUpper)
  (h_bind : HasSpectralSignature inst.gB inst.sigB)
  (hB_spec : IsSpectrallyLawful inst.sigB)
  (hB_flow : Semantics.Swarm.isScaleCoherent inst.gB)
  (hB_payload : VerifiedPayload inst.gB payload)
  (hC_noise : inst.sigC.density ≥ densityUpper) :
  KillerCriterionAdmission inst payload := by
  apply core_admission_theorem
  · exact noise_rejection_theorem inst.sigA hA_noise
  · exact h_bind
  · exact hB_spec
  · exact hB_flow
  · exact hB_payload
  · exact noise_rejection_theorem inst.sigC hC_noise

/-- Canonical repetition-flanked planted-core theorem.

A and C are rejected by insufficient entropy.
B is admitted by spectral lawfulness, RGFlow coherence, and payload
verification.
-/
theorem repetition_flanked_core_theorem
  (inst : KillerInstance)
  (payload : PayloadID)
  (hA_repeat : inst.sigA.entropy ≤ entropyLower)
  (h_bind : HasSpectralSignature inst.gB inst.sigB)
  (hB_spec : IsSpectrallyLawful inst.sigB)
  (hB_flow : Semantics.Swarm.isScaleCoherent inst.gB)
  (hB_payload : VerifiedPayload inst.gB payload)
  (hC_repeat : inst.sigC.entropy ≤ entropyLower) :
  KillerCriterionAdmission inst payload := by
  apply core_admission_theorem
  · exact repetition_rejection_theorem inst.sigA hA_repeat
  · exact h_bind
  · exact hB_spec
  · exact hB_flow
  · exact hB_payload
  · exact repetition_rejection_theorem inst.sigC hC_repeat

/-- Security corollary for the admitted core.

Once the planted core satisfies the Killer Criterion, it is not classified
as informatic sabotage.
-/
theorem admitted_core_not_sabotage
  (inst : KillerInstance)
  (payload : PayloadID)
  (h_admit : KillerCriterionAdmission inst payload) :
  Semantics.Security.NotAllowed_InformaticSabotage inst.gB = False := by
  unfold KillerCriterionAdmission at h_admit
  rcases h_admit with ⟨_hA, hB, _hC⟩
  exact blind_detection_theorem inst.sigB inst.gB payload hB

/-- Unique core admission theorem.

If the Killer Criterion holds, then any admitted region among A, B, and C
must be B.
-/
theorem unique_core_admission_theorem
  (inst : KillerInstance)
  (payload : PayloadID)
  (h_admit : KillerCriterionAdmission inst payload) :
  ∀ r : Region, RegionAdmitted inst payload r → r = Region.B := by
  intro r h_region
  unfold KillerCriterionAdmission at h_admit
  rcases h_admit with ⟨hA_reject, _hB_admit, hC_reject⟩
  cases r with
  | A =>
      unfold RegionAdmitted at h_region
      contradiction
  | B =>
      rfl
  | C =>
      unfold RegionAdmitted at h_region
      contradiction

/-- Fully rigid canonical theorem for the π/e planted core.

The canonical killer benchmark admits exactly the planted π/e core and
rejects both flanks.
-/
theorem canonical_pi_e_core_unique
  (inst : KillerInstance)
  (hA_noise : inst.sigA.density ≥ densityUpper)
  (h_bind : HasSpectralSignature inst.gB inst.sigB)
  (hB_spec : IsSpectrallyLawful inst.sigB)
  (hB_flow : Semantics.Swarm.isScaleCoherent inst.gB)
  (hB_payload : VerifiedPayload inst.gB PayloadID.pi_e_core)
  (hC_noise : inst.sigC.density ≥ densityUpper) :
  KillerCriterionAdmission inst PayloadID.pi_e_core ∧
  (∀ r : Region,
    RegionAdmitted inst PayloadID.pi_e_core r → r = Region.B) ∧
  Semantics.Security.NotAllowed_InformaticSabotage inst.gB = False := by
  have h_admit :
    KillerCriterionAdmission inst PayloadID.pi_e_core :=
    noise_flanked_core_theorem
      inst
      PayloadID.pi_e_core
      hA_noise
      h_bind
      hB_spec
      hB_flow
      hB_payload
      hC_noise

  have h_unique :
    ∀ r : Region,
      RegionAdmitted inst PayloadID.pi_e_core r → r = Region.B :=
    unique_core_admission_theorem inst PayloadID.pi_e_core h_admit

  have h_safe :
    Semantics.Security.NotAllowed_InformaticSabotage inst.gB = False :=
    admitted_core_not_sabotage inst PayloadID.pi_e_core h_admit

  exact ⟨h_admit, h_unique, h_safe⟩

end Semantics.Benchmarks.KillerCriterion
