import Semantics.Graph

namespace Semantics.ENE

-- Atomic Paths
-- Lawful semantic motion through the ENE graph.
-- An AtomicPath is a sequence of steps where each step is locally admissible.
-- This blocks "magic semantic jumps" — every transition must be justified.

/-- A single rewrite step in the semantic graph. -/
structure AtomicRewrite where
  fromNode : Node
  toNode   : Node
  viaEdge  : Edge
  locallyAdmissible : Bool
deriving Repr, BEq

/-- One step in an atomic path. -/
structure AtomicStep where
  rewrite : AtomicRewrite
  stepId  : Nat
deriving Repr, BEq

/-- A path through the ENE graph composed of atomic steps. -/
structure AtomicPath where
  steps : List AtomicStep
deriving Repr, BEq

/-- The empty path. -/
def AtomicPath.nil : AtomicPath := { steps := [] }

/-- Check if a path is empty. -/
def AtomicPath.isNil (p : AtomicPath) : Bool := p.steps.isEmpty

/-- Length of a path (number of steps). -/
def AtomicPath.length (p : AtomicPath) : Nat := p.steps.length

/-- A path is lawful if every step is locally admissible. -/
def AtomicPath.isLawful (p : AtomicPath) : Prop :=
  ∀ s ∈ p.steps, s.rewrite.locallyAdmissible = true

/-- The start node of a path. -/
def AtomicPath.start (p : AtomicPath) : Option Node :=
  p.steps.head?.map (λ s => s.rewrite.fromNode)

/-- The end node of a path. -/
def AtomicPath.end_ (p : AtomicPath) : Option Node :=
  p.steps.getLast?.map (λ s => s.rewrite.toNode)

/-- Predicate: two paths can be composed (the second starts where the first ends). -/
def AtomicPath.canCompose (p1 p2 : AtomicPath) : Bool :=
  match p1.end_, p2.start with
  | some n1, some n2 => n1 == n2
  | _, _ => p1.isNil || p2.isNil

/-- Compose two paths. If they cannot be composed, returns the first path.
For formal verification, use `canCompose` to check validity first. -/
def AtomicPath.compose (p1 p2 : AtomicPath) : AtomicPath :=
  if AtomicPath.canCompose p1 p2 then
    { steps := p1.steps ++ p2.steps }
  else
    p1

/-- Total number of rewrites in a path (same as length). -/
def AtomicPath.totalRewriteCount (p : AtomicPath) : Nat := AtomicPath.length p

/-- Count steps of a given edge type. -/
def AtomicPath.countEdgeType (p : AtomicPath) (t : EdgeType) : Nat :=
  p.steps.filter (λ s => s.rewrite.viaEdge.type == t) |>.length

/-- A path stays within a subgraph predicate if all its nodes satisfy a predicate. -/
def AtomicPath.staysWithin (p : AtomicPath) (pred : Node → Bool) : Bool :=
  p.steps.all (λ s => pred s.rewrite.fromNode && pred s.rewrite.toNode)

-- Theorems about path composition

theorem AtomicPath.nil_can_compose (p : AtomicPath) :
  AtomicPath.canCompose AtomicPath.nil p = true := by
  unfold AtomicPath.nil
  unfold AtomicPath.canCompose
  unfold AtomicPath.isNil
  unfold AtomicPath.end_
  unfold AtomicPath.start
  simp

theorem AtomicPath.can_compose_nil (p : AtomicPath) :
  AtomicPath.canCompose p AtomicPath.nil = true := by
  unfold AtomicPath.nil
  unfold AtomicPath.canCompose
  unfold AtomicPath.isNil
  unfold AtomicPath.end_
  unfold AtomicPath.start
  by_cases h : p.steps = []
  · simp [h]
  · simp

theorem AtomicPath.nil_compose (p : AtomicPath) :
  (AtomicPath.compose AtomicPath.nil p) = p := by
  unfold AtomicPath.compose
  rw [AtomicPath.nil_can_compose p]
  unfold AtomicPath.nil
  simp

theorem AtomicPath.compose_nil (p : AtomicPath) :
  (AtomicPath.compose p AtomicPath.nil) = p := by
  unfold AtomicPath.compose
  rw [AtomicPath.can_compose_nil p]
  simp [AtomicPath.nil]

/-- Lawfulness is preserved under valid path composition. -/
theorem AtomicPath.lawful_compose
  (p1 p2 : AtomicPath)
  (h1 : AtomicPath.isLawful p1)
  (h2 : AtomicPath.isLawful p2)
  (hc : AtomicPath.canCompose p1 p2 = true) :
  AtomicPath.isLawful (AtomicPath.compose p1 p2) := by
  unfold AtomicPath.compose
  rw [hc]
  unfold AtomicPath.isLawful at h1 h2 ⊢
  intro s hs
  simp at hs
  cases hs with
  | inl hsp1 => exact h1 s hsp1
  | inr hsp2 => exact h2 s hsp2

/-- Every path has finite length (trivial since lists are finite). -/
theorem AtomicPath.path_has_finite_length (p : AtomicPath) :
  AtomicPath.length p < (AtomicPath.length p + 1) := by
  simp

end Semantics.ENE
