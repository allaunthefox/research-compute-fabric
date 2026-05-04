/-
QuaternionSidonField.lean — Quaternion/Sidon standing-wave lattice scaffold v0.1

Origin:
  Recovered from the Mercury Superfluidity Under Compression chat export.
  The physical idea is deliberately treated as BEAUTIFUL_PROVISIONAL:
  compressed mercury may be modeled as a pressure-locked lattice of local
  quaternion spin/phase rotors, with a Sidon-like pairwise uniqueness condition
  acting as a meta-emergent anti-aliasing property.

Core mathematical reading:
  * lattice sites carry quaternion-like rotor coordinates
  * pairwise interaction signatures are tracked as discrete values
  * a Sidon-like field forbids nontrivial pair-signature collisions
  * triangle-wave forcing is represented as an external phase driver

No Float. No claim of real mercury superfluidity. No material-phase assertion.
-/

import Std

namespace Semantics.QuaternionSidonField

/-- Evidence ladder for this speculative physical/mathematical scaffold. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Boundary status for physical interpretation. -/
inductive PhysicalBoundary where
  | toyFormalism
  | simulationHypothesis
  | measurementClaim
  deriving Repr, DecidableEq, Inhabited

/-- Integer lattice coordinate. -/
structure GridCoord where
  x : Nat
  y : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Quaternion-like rotor with integer components.

A later Q16_16 module may replace these fields with fixed-point signed values.
This scaffold only records the shape of the rotor state.
-/
structure QuaternionRotor where
  a : Nat
  b : Nat
  c : Nat
  d : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Squared norm proxy for a quaternion-like rotor. -/
def normSq (q : QuaternionRotor) : Nat :=
  q.a*q.a + q.b*q.b + q.c*q.c + q.d*q.d

/-- A local lattice site carrying a quaternion-like phase/spin rotor. -/
structure LatticeSite where
  id : Nat
  coord : GridCoord
  rotor : QuaternionRotor
  deriving Repr, DecidableEq, Inhabited

/-- A pairwise phase/interference signature between two sites. -/
structure PairSignature where
  i : Nat
  j : Nat
  signature : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Same unordered site-pair relation. -/
def sameUnorderedPair (p q : PairSignature) : Prop :=
  (p.i = q.i ∧ p.j = q.j) ∨ (p.i = q.j ∧ p.j = q.i)

/-- Sidon-like field condition: equal signatures imply the same unordered pair.

This is the non-additive analogue of Sidon uniqueness: pairwise interactions
are uniquely addressable and do not collapse into aliasing except by trivial
pair reordering.
-/
def SidonLike (pairs : List PairSignature) : Prop :=
  ∀ p q, p ∈ pairs → q ∈ pairs → p.signature = q.signature → sameUnorderedPair p q

/-- Alias collision: same signature, different unordered pair. -/
def AliasCollision (pairs : List PairSignature) : Prop :=
  ∃ p q, p ∈ pairs ∧ q ∈ pairs ∧ p.signature = q.signature ∧ ¬ sameUnorderedPair p q

/-- Sidon-like fields have no alias collisions. -/
theorem sidon_like_no_alias_collision
    (pairs : List PairSignature)
    (h : SidonLike pairs) :
    ¬ AliasCollision pairs := by
  intro hc
  rcases hc with ⟨p, q, hp, hq, hs, hneq⟩
  exact hneq (h p q hp hq hs)

/-- Triangle-wave forcing parameters for a cellular standing-flow toy model. -/
structure TriangleWaveDriver where
  amplitude : Nat
  period : Nat
  phaseOffset : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Valid triangle-wave driver: positive period. -/
def ValidTriangleDriver (d : TriangleWaveDriver) : Prop :=
  0 < d.period

/-- A single cellular update rule record. -/
structure CellularUpdate where
  driver : TriangleWaveDriver
  localCoupling : Nat
  damping : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Standing-wave flow candidate on a square-grid cellular field. -/
structure StandingWaveField where
  sites : List LatticeSite
  pairs : List PairSignature
  update : CellularUpdate
  claimState : ClaimState
  boundary : PhysicalBoundary
  note : String
  deriving Repr, Inhabited

/-- Lawfulness gate for the toy field. -/
def PassesSidonGate (field : StandingWaveField) : Prop :=
  SidonLike field.pairs

/-- If the field passes the Sidon gate, it has no pair-signature alias collision. -/
theorem field_passes_sidon_gate_no_alias
    (field : StandingWaveField)
    (h : PassesSidonGate field) :
    ¬ AliasCollision field.pairs := by
  exact sidon_like_no_alias_collision field.pairs h

/-- Example quaternion rotors for a four-site square. -/
def qA : QuaternionRotor := { a := 1, b := 0, c := 0, d := 0 }
def qB : QuaternionRotor := { a := 0, b := 1, c := 0, d := 0 }
def qC : QuaternionRotor := { a := 0, b := 0, c := 1, d := 0 }
def qD : QuaternionRotor := { a := 0, b := 0, c := 0, d := 1 }

/-- Four-site square lattice toy carrier. -/
def squareSites : List LatticeSite :=
  [ { id := 0, coord := { x := 0, y := 0 }, rotor := qA }
  , { id := 1, coord := { x := 1, y := 0 }, rotor := qB }
  , { id := 2, coord := { x := 0, y := 1 }, rotor := qC }
  , { id := 3, coord := { x := 1, y := 1 }, rotor := qD }
  ]

/-- Example pair signatures with no collisions. -/
def squarePairSignatures : List PairSignature :=
  [ { i := 0, j := 1, signature := 101 }
  , { i := 0, j := 2, signature := 102 }
  , { i := 1, j := 3, signature := 113 }
  , { i := 2, j := 3, signature := 123 }
  ]

/-- Example toy field matching the user image: square grid + triangle wave + standing flow. -/
def squareTriangleStandingField : StandingWaveField :=
  { sites := squareSites
    pairs := squarePairSignatures
    update :=
      { driver := { amplitude := 4, period := 8, phaseOffset := 0 }
        localCoupling := 1
        damping := 1 }
    claimState := .beautifulProvisional
    boundary := .toyFormalism
    note := "square-grid cellular quaternion field with triangle-wave standing-flow driver" }

/-- The example driver has positive period. -/
theorem squareTriangleDriver_valid :
    ValidTriangleDriver squareTriangleStandingField.update.driver := by
  unfold squareTriangleStandingField ValidTriangleDriver
  decide

/-- The example pair signatures satisfy the Sidon-like uniqueness gate. -/
theorem squarePairSignatures_sidon_like : SidonLike squarePairSignatures := by
  intro p q hp hq hs
  simp [squarePairSignatures] at hp hq
  rcases hp with hp | hp | hp | hp
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; left; constructor <;> rfl
    · subst q; contradiction
    · subst q; contradiction
    · subst q; contradiction
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; contradiction
    · subst q; left; constructor <;> rfl
    · subst q; contradiction
    · subst q; contradiction
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; contradiction
    · subst q; contradiction
    · subst q; left; constructor <;> rfl
    · subst q; contradiction
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; contradiction
    · subst q; contradiction
    · subst q; contradiction
    · subst q; left; constructor <;> rfl

/-- Example field passes the Sidon gate. -/
theorem squareTriangleStandingField_passes_sidon_gate :
    PassesSidonGate squareTriangleStandingField := by
  unfold PassesSidonGate squareTriangleStandingField
  exact squarePairSignatures_sidon_like

/-- Therefore the example field has no pair-signature alias collision. -/
theorem squareTriangleStandingField_no_alias_collision :
    ¬ AliasCollision squareTriangleStandingField.pairs := by
  exact field_passes_sidon_gate_no_alias squareTriangleStandingField
    squareTriangleStandingField_passes_sidon_gate

#eval normSq qA -- 1
#eval squareTriangleStandingField.note

end Semantics.QuaternionSidonField
