/-
TorsionFlipOperator.lean — discrete torsion-threshold flip gate v0.1

Purpose:
  Formalize the finite/discrete part of the rotation -> torsion -> inversion
  operator recovered from the phrase "turned round and round and upside down".

Boundary:
  This module does not claim a physical law. It defines a toy operator for
  kinetic/Sidon lattices: repeated winding accumulates torsion; crossing a
  threshold flips orientation; the resulting pair address must still pass a
  Sidon anti-alias gate elsewhere.

No Float. Nat and Bool fields stand in for fixed-point encoded measurements.
-/

import Std

namespace Semantics.TorsionFlipOperator

/-- Evidence state for this scaffold. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Orientation of a local frame after the flip gate. -/
inductive Orientation where
  | upright
  | inverted
  deriving Repr, DecidableEq, Inhabited

/-- A local phase/frame state in the kinetic lattice. -/
structure FrameState where
  id : Nat
  rotationCount : Nat
  torsionScore : Nat
  torsionThreshold : Nat
  orientation : Orientation
  deriving Repr, DecidableEq, Inhabited

/-- The torsion flip gate: crossing the threshold triggers inversion. -/
def ShouldFlip (s : FrameState) : Prop :=
  s.torsionThreshold ≤ s.torsionScore

/-- Boolean version for executable/eval witnesses. -/
def shouldFlipBool (s : FrameState) : Bool :=
  s.torsionThreshold <= s.torsionScore

/-- Apply the thresholded torsion flip to a frame. -/
def applyTorsionFlip (s : FrameState) : FrameState :=
  if shouldFlipBool s then
    { s with orientation := .inverted }
  else
    { s with orientation := .upright }

/-- Pair signature before/after a torsion flip. -/
structure FlipSignature where
  i : Nat
  j : Nat
  preSignature : Nat
  postSignature : Nat
  flipped : Bool
  deriving Repr, DecidableEq, Inhabited

/-- A simple re-indexer: if flipped, move to a disjoint post-flip address band. -/
def reindexSignature (preSignature : Nat) (flipped : Bool) : Nat :=
  if flipped then preSignature + 1000003 else preSignature

/-- Build a flip signature from a frame pair address. -/
def buildFlipSignature (i j preSignature : Nat) (s : FrameState) : FlipSignature :=
  let f := shouldFlipBool s
  { i := i
    j := j
    preSignature := preSignature
    postSignature := reindexSignature preSignature f
    flipped := f }

/-- Same unordered pair relation for flipped signatures. -/
def sameUnorderedPair (p q : FlipSignature) : Prop :=
  (p.i = q.i ∧ p.j = q.j) ∨ (p.i = q.j ∧ p.j = q.i)

/-- Post-flip Sidon uniqueness gate. -/
def PostFlipSidonLike (pairs : List FlipSignature) : Prop :=
  ∀ p q, p ∈ pairs → q ∈ pairs → p.postSignature = q.postSignature → sameUnorderedPair p q

/-- Post-flip alias collision: same post signature, different unordered pair. -/
def PostFlipAliasCollision (pairs : List FlipSignature) : Prop :=
  ∃ p q, p ∈ pairs ∧ q ∈ pairs ∧ p.postSignature = q.postSignature ∧ ¬ sameUnorderedPair p q

/-- A post-flip Sidon-like list has no post-flip alias collision. -/
theorem post_flip_sidon_like_no_alias
    (pairs : List FlipSignature)
    (h : PostFlipSidonLike pairs) :
    ¬ PostFlipAliasCollision pairs := by
  intro hc
  rcases hc with ⟨p, q, hp, hq, hs, hneq⟩
  exact hneq (h p q hp hq hs)

/-- If a state should flip, applying the gate makes it inverted. -/
theorem apply_flip_inverts_when_threshold_met
    (s : FrameState)
    (h : shouldFlipBool s = true) :
    (applyTorsionFlip s).orientation = Orientation.inverted := by
  unfold applyTorsionFlip
  simp [h]

/-- If a state should not flip, applying the gate leaves it upright. -/
theorem apply_flip_upright_when_threshold_not_met
    (s : FrameState)
    (h : shouldFlipBool s = false) :
    (applyTorsionFlip s).orientation = Orientation.upright := by
  unfold applyTorsionFlip
  simp [h]

/-- Re-indexing preserves the original signature when no flip occurs. -/
theorem reindex_no_flip_identity (pre : Nat) :
    reindexSignature pre false = pre := by
  unfold reindexSignature
  rfl

/-- Re-indexing moves a flipped signature to the post-flip band. -/
theorem reindex_flip_adds_band (pre : Nat) :
    reindexSignature pre true = pre + 1000003 := by
  unfold reindexSignature
  rfl

/-- Example below threshold: rotation continues without inversion. -/
def belowThresholdExample : FrameState :=
  { id := 0
    rotationCount := 3
    torsionScore := 4
    torsionThreshold := 7
    orientation := .upright }

/-- Example above threshold: torsion flips the local frame. -/
def aboveThresholdExample : FrameState :=
  { id := 1
    rotationCount := 9
    torsionScore := 12
    torsionThreshold := 7
    orientation := .upright }

/-- Two post-flip signatures with distinct addresses. -/
def exampleFlipSignatures : List FlipSignature :=
  [ buildFlipSignature 0 1 101 belowThresholdExample
  , buildFlipSignature 0 2 102 aboveThresholdExample ]

/-- The example post-flip signatures satisfy uniqueness. -/
theorem example_post_flip_sidon_like : PostFlipSidonLike exampleFlipSignatures := by
  intro p q hp hq hs
  simp [exampleFlipSignatures, buildFlipSignature, belowThresholdExample, aboveThresholdExample,
    shouldFlipBool, reindexSignature] at hp hq hs
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

/-- Therefore the example has no post-flip alias collision. -/
theorem example_post_flip_no_alias :
    ¬ PostFlipAliasCollision exampleFlipSignatures := by
  exact post_flip_sidon_like_no_alias exampleFlipSignatures example_post_flip_sidon_like

#eval shouldFlipBool belowThresholdExample -- false
#eval shouldFlipBool aboveThresholdExample -- true
#eval (applyTorsionFlip belowThresholdExample).orientation -- upright
#eval (applyTorsionFlip aboveThresholdExample).orientation -- inverted
#eval (buildFlipSignature 0 2 102 aboveThresholdExample).postSignature -- 1000105

end Semantics.TorsionFlipOperator
