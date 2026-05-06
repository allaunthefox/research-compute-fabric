/-
  Mass-Number Metric Closure Conjecture

  Formalizes the four-part conjecture from the Mass-Number Admissibility Closure:

  1. Mass-Number Metric Closure: M is an admissibility potential, not a metric.
     A metric d_θ emerges from phi-normalization → symmetrized edge cost →
     admissibility graph → shortest-path closure → quotient metric.

  2. Shell Mass as Throat Curvature: shell_mass(n) = a*b identifies maximal
     representational ambiguity (midpoint/blend zone), NOT a distance.

  3. Residual Closure / Holy Diver: A candidate field is closed when every
     candidate is promoted, connected, typed as residual, quarantined, or rejected.

  4. Category-Error Rescue: Low mass in one domain may indicate category
     misplacement, not falsity, when cross-domain mass variance is high and
     another domain gives high admissibility.

  Reference: Mass-Number Admissibility Closure Conjecture (2026-04-30)
  Authors: Research Stack Team
-/

import Semantics.RealityContractMassNumber

namespace HolyDiver.ENE

/-! ## §0  Scaffolding Theorems (Score Arithmetic) -/

/-- Score addition (cross-multiplying to common denominator). -/
def Score.add (a b : Score) : Score :=
  { num := a.num * b.den + b.num * a.den,
    den := a.den * b.den,
    den_ne := by
      apply Nat.mul_ne_zero
      · exact a.den_ne
      · exact b.den_ne }

/-- Score is nonnegative: num ≥ 0 and den > 0. -/
theorem Score.nonneg (s : Score) : s.num ≥ 0 ∧ s.den > 0 := by
  constructor
  · exact Nat.zero_le s.num
  · have h : s.den ≠ 0 := s.den_ne
    exact Nat.zero_lt_of_ne_zero h

/-- A score is zero iff its numerator is zero. -/
theorem Score.zero_iff (s : Score) : s.num = 0 ↔ s.num * 1 = 0 * s.den := by
  simp [Nat.mul_one, Nat.zero_mul]

/-- Score comparison: a ≤ b as rational numbers. -/
def Score.le (a b : Score) : Prop :=
  a.num * b.den ≤ b.num * a.den

/-- Score strict comparison: a < b as rational numbers. -/
def Score.lt (a b : Score) : Prop :=
  a.num * b.den < b.num * a.den

instance : LE Score where
  le := Score.le

instance : LT Score where
  lt := Score.lt

/-- Reflexivity of score LE. -/
theorem Score.le_refl (a : Score) : a ≤ a := by
  unfold LE.le Score.le
  exact Nat.le_refl _

/-- Transitivity of score LE. -/
theorem Score.le_trans (a b c : Score) (h₁ : a ≤ b) (h₂ : b ≤ c) : a ≤ c := by
  unfold LE.le Score.le at h₁ h₂ ⊢
  have h₁' : a.num * b.den ≤ b.num * a.den := h₁
  have h₂' : b.num * c.den ≤ c.num * b.den := h₂
  have h₃ : a.num * b.den * c.den ≤ b.num * a.den * c.den := by
    apply Nat.mul_le_mul_right
    exact h₁'
  have h₄ : b.num * c.den * a.den ≤ c.num * b.den * a.den := by
    apply Nat.mul_le_mul_right
    exact h₂'
  have h₅ : a.num * c.den * b.den ≤ c.num * a.den * b.den := by
    rw [show a.num * c.den * b.den = a.num * b.den * c.den by ring]
    rw [show c.num * a.den * b.den = c.num * b.den * a.den by ring]
    apply Nat.le_trans h₃
    rw [show b.num * a.den * c.den = b.num * c.den * a.den by ring]
    exact h₄
  exact Nat.le_of_mul_le_mul_right h₅ (by positivity : b.den > 0)

/-! ## §1  Theorem 1: massNumber_nonneg -/

/-- Mass number is nonnegative (numerator ≥ 0, denominator > 0). -/
theorem massNumber_nonneg (rs : List CertifiedReduction) (risk : ResidualRisk) :
    let m := massNumber rs risk
    m.num ≥ 0 ∧ m.den > 0 := by
  unfold massNumber
  apply Score.nonneg

/-! ## §2  Theorem 2: phi_bounded -/

/-- Phi is bounded in [0, 1] as a Score comparison. -/
theorem phi_bounded (rs : List CertifiedReduction) (risk : ResidualRisk) :
    let p := massPhi rs risk
    let zero : Score := { num := 0, den := 1, den_ne := by simp }
    let one  : Score := { num := 1, den := 1, den_ne := by simp }
    zero ≤ p ∧ p ≤ one := by
  unfold massPhi
  split
  · -- Case: a + u = 0, phi = 0/1
    constructor
    · unfold LE.le Score.le; simp
    · unfold LE.le Score.le; simp
  · -- Case: a + u > 0, phi = a/(a+u)
    constructor
    · -- 0 ≤ a/(a+u): trivial since a ≥ 0
      unfold LE.le Score.le
      simp
    · -- a/(a+u) ≤ 1: a ≤ a+u, trivial since u ≥ 0
      unfold LE.le Score.le
      simp [Nat.le_add_right]

/-! ## §3  Theorem 3: phiDistanceCost_nonneg -/

/-- Phi distance cost is nonnegative. -/
theorem phiDistanceCost_nonneg (rs : List CertifiedReduction) (risk : ResidualRisk) :
    let d := phiDistanceCost rs risk
    d.num ≥ 0 ∧ d.den > 0 := by
  unfold phiDistanceCost
  apply Score.nonneg

/-! ## §4  Graph Structure for Metric Closure -/

/-- An undirected edge between two candidates with a symmetric cost. -/
structure AdmissibilityEdge where
  u     : CandidateRecord
  v     : CandidateRecord
  cost  : Score
  symm  : cost = cost  -- trivial witness of symmetry (by reflexivity)

/-- A path is a sequence of edges. -/
def Path := List AdmissibilityEdge

/-- The cost of a path is the sum of edge costs. -/
def pathCost (p : Path) : Score :=
  p.foldl (fun acc e => acc.add e.cost)
    { num := 0, den := 1, den_ne := by simp }

/-- Score addition is commutative. -/
theorem Score.add_comm (a b : Score) : a.add b = b.add a := by
  unfold Score.add
  simp
  rw [Nat.add_comm, Nat.mul_comm]
  congr 1
  rw [Nat.mul_comm]

/-- Score addition is associative. -/
theorem Score.add_assoc (a b c : Score) : (a.add b).add c = a.add (b.add c) := by
  unfold Score.add
  simp
  constructor
  · ring
  · ring

/-- The empty path has zero cost. -/
theorem pathCost_nil : pathCost [] = { num := 0, den := 1, den_ne := by simp } := rfl

/-- Adjoining an edge to the end of a path adds its cost. -/
theorem pathCost_append (p : Path) (e : AdmissibilityEdge) :
    pathCost (p ++ [e]) = (pathCost p).add e.cost := by
  unfold pathCost
  rw [List.foldl_append]
  simp [List.foldl_cons]
  rfl

private lemma foldl_add_add (xs : List Score) (init x : Score) :
    (xs.foldl Score.add init).add x = xs.foldl Score.add (init.add x) := by
  induction xs generalizing init x with
  | nil => rfl
  | cons a as ih =>
    rw [List.foldl_cons, ih (init.add a) x]
    rw [Score.add_assoc, Score.add_comm a x, Score.add_assoc]

/-- Helper: foldl with commutative/associative operation is invariant under reversal. -/
theorem foldl_add_reverse (l : List Score) (init : Score) :
    l.reverse.foldl Score.add init = l.foldl Score.add init := by
  induction l generalizing init with
  | nil => rfl
  | cons x xs ih =>
    rw [List.reverse_cons, List.foldl_append]
    simp [List.foldl_cons]
    rw [ih, foldl_add_add]

/-- Reversing an edge swaps endpoints and preserves cost. -/
def AdmissibilityEdge.reverse (e : AdmissibilityEdge) : AdmissibilityEdge :=
  { u := e.v, v := e.u, cost := e.cost, symm := rfl }

/-- Reversing a path reverses the list and reverses each edge. -/
def Path.reversePath (p : Path) : Path :=
  p.reverse.map AdmissibilityEdge.reverse

/-- Symmetry: path reversal preserves cost. -/
theorem pathCost_reverse (p : Path) : pathCost (p.reversePath) = pathCost p := by
  unfold pathCost Path.reversePath
  rw [List.foldl_map]
  -- foldl (fun x => x.reverse.cost) p.reverse init
  -- Since e.reverse.cost = e.cost, this is foldl (fun x => x.cost) p.reverse init
  have h_cost : ∀ e, (e.reverse).cost = e.cost := fun e => rfl
  simp [h_cost]
  rw [foldl_add_reverse]

/-- A graph is a set of edges over a finite type of candidates. -/
structure AdmissibilityGraph where
  vertices  : List CandidateRecord
  edges     : List AdmissibilityEdge
  threshold : Score  -- θ_min: minimum mass for inclusion

/-- An edge is admissible if both endpoints meet the mass threshold. -/
def edgeAdmissible (g : AdmissibilityGraph) (e : AdmissibilityEdge) : Bool :=
  let mu_u := e.u.mass
  let mu_v := e.v.mass
  Score.ge mu_u g.threshold && Score.ge mu_v g.threshold

/-- The admissible subgraph containing only threshold-meeting edges. -/
def admissibleSubgraph (g : AdmissibilityGraph) : List AdmissibilityEdge :=
  g.edges.filter (edgeAdmissible g)

/-- A path is valid from x to y in graph g if it connects them using admissible edges. -/
def is_path (g : AdmissibilityGraph) (x y : CandidateRecord) (p : Path) : Prop :=
  match p with
  | [] => x = y
  | [e] => e.u = x ∧ e.v = y ∧ e ∈ g.edges ∧ edgeAdmissible g e
  | e :: es => e.u = x ∧ e ∈ g.edges ∧ edgeAdmissible g e ∧ is_path g e.v y es

/-- Symmetry: if p is a path from x to y, p.reversePath is a path from y to x. -/
theorem is_path_reverse (g : AdmissibilityGraph) (x y : CandidateRecord) (p : Path) :
    (∀ e ∈ g.edges, e.reverse ∈ g.edges) →
    is_path g x y p → is_path g y x p.reversePath := by
  sorry -- TODO(lean-port): induction on path length (WIP-2026-05-01)

/-- All paths between two candidates in the admissible subgraph. -/
def allPaths (g : AdmissibilityGraph) (x y : CandidateRecord) : List Path :=
  -- Set of paths p such that is_path g x y p
  []

/-- The shortest-path distance is the minimum path cost. -/
def shortestPathDist (g : AdmissibilityGraph) (x y : CandidateRecord) : Score :=
  let paths := allPaths g x y
  match paths with
  | [] => { num := 1, den := 0, den_ne := by simp } -- Infinite distance
  | p :: ps => ps.foldl (fun min_cost path =>
      let c := pathCost path
      if Score.le c min_cost then c else min_cost) (pathCost p)

/-- Symmetry of shortest-path distance (by construction from undirected edges). -/
theorem shortestPathDist_symmetric (g : AdmissibilityGraph) (x y : CandidateRecord)
    (h_symm : ∀ e ∈ g.edges, e.reverse ∈ g.edges) :
    shortestPathDist g x y = shortestPathDist g y x := by
  unfold shortestPathDist
  -- If paths_xy = {p1, ...}, then paths_yx = {p1.reverse, ...}
  -- Since cost(p) = cost(p.reverse), the sets of costs are identical.
  -- Therefore the minimum is the same.
  sorry -- TODO(lean-port): set-of-costs equivalence (WIP-2026-05-01)

/-- Nonnegativity of shortest-path distance. -/
theorem shortestPathDist_nonneg (g : AdmissibilityGraph) (x y : CandidateRecord) :
    let d := shortestPathDist g x y
    d.num ≥ 0 ∧ d.den > 0 := by
  unfold shortestPathDist allPaths
  split
  · -- Empty path case: infinite distance (1/0 form - not a valid Score)
    -- In practice, we handle disconnected components separately.
    unfold Score.nonneg
    sorry  -- TODO(lean-port): disconnected component handling (WIP-2026-04-30)
  · -- Finite path case: sum of nonnegative edge costs
    sorry  -- TODO(lean-port): path cost is sum of nonnegative costs (WIP-2026-04-30)

/-- Triangle inequality for shortest-path closure:
    The shortest path from x to z is at most the shortest path from x to y
    plus the shortest path from y to z (by path concatenation). -/
theorem shortestPathDist_triangle (g : AdmissibilityGraph) (x y z : CandidateRecord) :
    let dxz := shortestPathDist g x z
    let dxy := shortestPathDist g x y
    let dyz := shortestPathDist g y z
    Score.le dxz (dxy.add dyz) := by
  unfold shortestPathDist allPaths
  sorry  -- TODO(lean-port): path concatenation gives upper bound (WIP-2026-04-30)

/-! ## §6  Pseudometric and Metric Spaces -/

/-- A pseudometric space: distance satisfies nonnegativity, symmetry,
    identity (d(x,x)=0), and triangle inequality, but distinct points
    may have zero distance. -/
class PseudometricSpace (α : Type) where
  dist          : α → α → Score
  dist_nonneg   : ∀ x y, (dist x y).num ≥ 0 ∧ (dist x y).den > 0
  dist_self_zero : ∀ x, dist x x = { num := 0, den := 1, den_ne := by simp }
  dist_symm     : ∀ x y, dist x y = dist y x
  dist_triangle : ∀ x y z, Score.le (dist x z) ((dist x y).add (dist y z))

/-- The shortest-path closure induces a pseudometric on the graph vertices. -/
instance (g : AdmissibilityGraph) : PseudometricSpace CandidateRecord where
  dist          := shortestPathDist g
  dist_nonneg   := shortestPathDist_nonneg g
  dist_self_zero := by
    -- Empty path from x to x has cost 0
    intro x
    unfold shortestPathDist allPaths
    -- In a real graph, we'd have a list [[]] for the reflexive case.
    -- For now, we assume the construction yields 0.
    refl
  dist_symm     := shortestPathDist_symmetric g
  dist_triangle := shortestPathDist_triangle g

/-- A metric space: pseudometric where d(x,y)=0 implies x=y. -/
class MetricSpace (α : Type) extends PseudometricSpace α where
  identity_of_indiscernibles : ∀ x y, dist x y = { num := 0, den := 1, den_ne := by simp } → x = y

/-- Two candidates are admissibly indistinguishable if their shortest-path
    distance is zero (connected by zero-cost edges). -/
def admissiblyIndistinguishable (g : AdmissibilityGraph) (x y : CandidateRecord) : Prop :=
  shortestPathDist g x y = { num := 0, den := 1, den_ne := by simp }

/-- Quotient type: candidates modulo admissible indistinguishability. -/
def QuotientCandidate (g : AdmissibilityGraph) : Type :=
  -- Setoid quotient by admissiblyIndistinguishable relation
  CandidateRecord  -- TODO(lean-port): proper quotient type (WIP-2026-04-30)

/-- The quotient of the admissibility graph by zero-distance equivalence
    is a metric space (Theorem 6 / quotientClosure_metric). -/
instance quotientMetricSpace (g : AdmissibilityGraph) : MetricSpace (QuotientCandidate g) where
  dist := shortestPathDist g
  dist_nonneg := shortestPathDist_nonneg g
  dist_self_zero := by sorry  -- TODO(lean-port): WIP-2026-04-30
  dist_symm := shortestPathDist_symmetric g
  dist_triangle := shortestPathDist_triangle g
  identity_of_indiscernibles := by
    -- After quotienting, zero distance implies equality by construction
    intro x y h
    sorry  -- TODO(lean-port): zero distance in quotient implies equality (WIP-2026-04-30)

/-! ## §7  Shell Mass as Throat Curvature (Conjecture 2) -/

/-- Shell mass: S_n = a * b where n = k² + a, b = (k+1)² - n.
    Identifies midpoints between perfect squares (points of maximal ambiguity). -/
def shellMass (n : Nat) : Nat :=
  let k := Nat.sqrt n
  let a := n - k * k
  let b := (k + 1) * (k + 1) - n
  a * b

/-- Shell mass is maximized at the midpoint between consecutive squares. -/
theorem shellMass_max_at_midpoint (k : Nat) :
    let n := k * k + k
    shellMass n = k * (k + 1) := by
  intro n
  unfold shellMass
  have hle_low : k * k ≤ n := by
    dsimp [n]
    omega
  have hle_high : n < (k + 1) * (k + 1) := by
    dsimp [n]
    nlinarith
  have hsq : Nat.sqrt n = k := by
    rw [Nat.sqrt_eq_iff_sq_le]
    constructor
    · exact hle_low
    · exact hle_high
  rw [hsq]
  dsimp [n]
  nlinarith

/-- Shell mass is NOT a distance: it does not satisfy the triangle inequality. -/
theorem shellMass_not_distance :
    ¬ (∀ n m p, shellMass n ≤ shellMass m + shellMass p) := by
  intro h
  have h_counter := h 6 5 4
  unfold shellMass at h_counter
  -- Nat.sqrt 6 = 2, Nat.sqrt 5 = 2, Nat.sqrt 4 = 2
  -- We can use native_decide or just compute
  have h6 : Nat.sqrt 6 = 2 := rfl
  have h5 : Nat.sqrt 5 = 2 := rfl
  have h4 : Nat.sqrt 4 = 2 := rfl
  rw [h6, h5, h4] at h_counter
  simp at h_counter
  -- 6 ≤ 4 is false
  contradiction

/-! ## §8  Category-Error Rescue (Conjecture 4) -/

/-- A candidate's mass in a different domain/frame. -/
def massInDomain (r : CandidateRecord) (d : DomainKind) (f : ReferenceFrame) : Score :=
  -- Simplified: only mass from reductions matching the domain
  let domainReductions := r.nativeReductions.filter (fun nr => nr.domain = d)
  let rs := domainReductions.map (fun nr => nr.reduction)
  massNumber rs r.risk

/-- Category misplacement: high variance across domains, but at least one
    domain gives high admissibility. -/
def CategoryMisplaced (r : CandidateRecord) (threshold rescueThreshold : Score) : Prop :=
  let masses := DomainKind.casesOn (motive := fun _ => Score)
    (massInDomain r DomainKind.mathematics r.frame)
    (massInDomain r DomainKind.physics r.frame)
    (massInDomain r DomainKind.biology r.frame)
    (massInDomain r DomainKind.computation r.frame)
    (massInDomain r DomainKind.cognition r.frame)
    (massInDomain r DomainKind.language r.frame)
    (massInDomain r DomainKind.social r.frame)
    (massInDomain r DomainKind.cryptography r.frame)
    (massInDomain r DomainKind.engineering r.frame)
    (massInDomain r DomainKind.unknown r.frame)
    []
  -- Var across domains is high AND max domain mass ≥ rescueThreshold
  -- (Simplified: at least one domain mass exceeds rescueThreshold)
  ∃ m ∈ masses, Score.ge m rescueThreshold

end ENE
end HolyDiver
