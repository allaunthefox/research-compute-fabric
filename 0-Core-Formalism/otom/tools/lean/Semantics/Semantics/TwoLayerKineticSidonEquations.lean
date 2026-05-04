/-
TwoLayerKineticSidonEquations.lean — discrete gates for the two-layer kinetic/Sidon equation system v0.1

Purpose:
  Formalize the discrete, auditable side of the two-layer kinetic/Sidon model:
  pair signatures, alias detection, Sidon validity, reconstruction-error gates,
  and the compression pass condition.

Boundary:
  This module does not solve the PDE
    u_tt = c^2 ∇^2u - ζ u_t + T + F_S.
  The PDE and contour equations live in the companion Markdown spec.
  Lean only checks the finite/discrete gate structure.

No Float. Nat scores stand in for fixed-point encoded measurements.
-/

import Std

namespace Semantics.TwoLayerKineticSidonEquations

/-- Evidence state for this scaffold. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Encoded kinetic relation R_ij(t). -/
structure KineticRelation where
  i : Nat
  j : Nat
  distance : Nat
  deltaU : Nat
  deltaTheta : Nat
  deltaEnergy : Nat
  gradientCoupling : Nat
  contourCode : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Discrete Sidon-layer pair signature sigma_ij(t). -/
structure PairSignature where
  i : Nat
  j : Nat
  signature : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Same unordered pair relation. -/
def sameUnorderedPair (p q : PairSignature) : Prop :=
  (p.i = q.i ∧ p.j = q.j) ∨ (p.i = q.j ∧ p.j = q.i)

/-- Pair-address Sidon uniqueness. -/
def SidonLike (pairs : List PairSignature) : Prop :=
  ∀ p q, p ∈ pairs → q ∈ pairs → p.signature = q.signature → sameUnorderedPair p q

/-- Nontrivial alias collision: same signature, different unordered pair. -/
def AliasCollision (pairs : List PairSignature) : Prop :=
  ∃ p q, p ∈ pairs ∧ q ∈ pairs ∧ p.signature = q.signature ∧ ¬ sameUnorderedPair p q

/-- If a list is Sidon-like, it has no nontrivial alias collision. -/
theorem sidon_like_no_alias_collision
    (pairs : List PairSignature)
    (h : SidonLike pairs) :
    ¬ AliasCollision pairs := by
  intro hc
  rcases hc with ⟨p, q, hp, hq, hs, hneq⟩
  exact hneq (h p q hp hq hs)

/-- A simple integer signature encoder for a kinetic relation. -/
def encodeSignature (r : KineticRelation) : Nat :=
  r.distance
  + 17 * r.deltaU
  + 257 * r.deltaTheta
  + 4099 * r.deltaEnergy
  + 65537 * r.gradientCoupling
  + 1048583 * r.contourCode

/-- Forward flow K -> S: relation to pair signature. -/
def relationToSignature (r : KineticRelation) : PairSignature :=
  { i := r.i
    j := r.j
    signature := encodeSignature r }

/-- A finite discrete snapshot of the equation system. -/
structure EquationSnapshot where
  relations : List KineticRelation
  signatures : List PairSignature
  reconstructionError : Nat
  reconstructionThreshold : Nat
  claimState : ClaimState
  deriving Repr, Inhabited

/-- Every kinetic relation has a matching Sidon signature in the snapshot. -/
def AllRelationsRepresented (s : EquationSnapshot) : Prop :=
  ∀ r, r ∈ s.relations → relationToSignature r ∈ s.signatures

/-- Sidon alias gate: no nontrivial pair-signature aliasing. -/
def SidonGate (s : EquationSnapshot) : Prop :=
  SidonLike s.signatures

/-- Reconstruction gate: reconstruction error is bounded. -/
def ReconstructionGate (s : EquationSnapshot) : Prop :=
  s.reconstructionError ≤ s.reconstructionThreshold

/-- Compression gate G_compress(t). -/
def CompressionGate (s : EquationSnapshot) : Prop :=
  SidonGate s ∧ ReconstructionGate s

/-- Full discrete gate: all K->S flows represented and compression gate passes. -/
def FullDiscreteGate (s : EquationSnapshot) : Prop :=
  AllRelationsRepresented s ∧ CompressionGate s

/-- Passing the compression gate implies no Sidon alias collision. -/
theorem compression_gate_no_alias
    (s : EquationSnapshot)
    (h : CompressionGate s) :
    ¬ AliasCollision s.signatures := by
  exact sidon_like_no_alias_collision s.signatures h.left

/-- Passing the full gate implies no Sidon alias collision. -/
theorem full_gate_no_alias
    (s : EquationSnapshot)
    (h : FullDiscreteGate s) :
    ¬ AliasCollision s.signatures := by
  exact compression_gate_no_alias s h.right

/-- Passing the full gate includes bounded reconstruction error. -/
theorem full_gate_reconstruction_bounded
    (s : EquationSnapshot)
    (h : FullDiscreteGate s) :
    s.reconstructionError ≤ s.reconstructionThreshold := by
  exact h.right.right

/-- Example kinetic relation R_01. -/
def r01 : KineticRelation :=
  { i := 0, j := 1
    distance := 1
    deltaU := 2
    deltaTheta := 3
    deltaEnergy := 4
    gradientCoupling := 5
    contourCode := 6 }

/-- Example kinetic relation R_02. -/
def r02 : KineticRelation :=
  { i := 0, j := 2
    distance := 2
    deltaU := 3
    deltaTheta := 4
    deltaEnergy := 5
    gradientCoupling := 6
    contourCode := 7 }

/-- Example signature list from the two relations. -/
def exampleSignatures : List PairSignature :=
  [relationToSignature r01, relationToSignature r02]

/-- Example finite snapshot. -/
def exampleSnapshot : EquationSnapshot :=
  { relations := [r01, r02]
    signatures := exampleSignatures
    reconstructionError := 3
    reconstructionThreshold := 5
    claimState := .beautifulProvisional }

/-- The two example signatures are Sidon-like. -/
theorem exampleSignatures_sidon_like : SidonLike exampleSignatures := by
  intro p q hp hq hs
  simp [exampleSignatures, r01, r02, relationToSignature, encodeSignature] at hp hq hs
  rcases hp with hp | hp
  · subst p
    rcases hq with hq | hq
    · subst q
      left; constructor <;> rfl
    · subst q
      contradiction
  · subst p
    rcases hq with hq | hq
    · subst q
      contradiction
    · subst q
      left; constructor <;> rfl

/-- Example relations are represented by their signatures. -/
theorem example_relations_represented : AllRelationsRepresented exampleSnapshot := by
  intro r hr
  simp [exampleSnapshot, exampleSignatures] at hr ⊢
  rcases hr with hr | hr
  · subst r
    simp [r01, relationToSignature]
  · rcases hr with hr | hr
    · subst r
      simp [r02, relationToSignature]
    · cases hr

/-- Example snapshot passes the compression gate. -/
theorem example_compression_gate : CompressionGate exampleSnapshot := by
  constructor
  · unfold SidonGate exampleSnapshot
    exact exampleSignatures_sidon_like
  · unfold ReconstructionGate exampleSnapshot
    decide

/-- Example snapshot passes the full discrete gate. -/
theorem example_full_discrete_gate : FullDiscreteGate exampleSnapshot := by
  constructor
  · exact example_relations_represented
  · exact example_compression_gate

/-- Therefore the example has no alias collision. -/
theorem example_no_alias_collision : ¬ AliasCollision exampleSnapshot.signatures := by
  exact full_gate_no_alias exampleSnapshot example_full_discrete_gate

#eval encodeSignature r01
#eval encodeSignature r02
#eval exampleSnapshot.reconstructionError <= exampleSnapshot.reconstructionThreshold

end Semantics.TwoLayerKineticSidonEquations
