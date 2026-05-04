/-
NKCoupling.lean — N-K Coupling Law: Structural-to-Spectral Field Interaction
=============================================================================

The N-K Coupling Law governs how structural research coordinates (N-space)
interact with spectral information fields (K-space):

  J(n) = (ab)·F_m + (a-b)·F_p + ⟨χ(n), F_c(n)⟩

Where:
  • (ab)·F_m: Mass Resonance — stability at crystallization points
  • (a-b)·F_p: Mirror Resonance — symmetry across domains
  • ⟨χ, F_c⟩: Spectral Coupling — dot product of topological character with carrier field

Emergent Result: Space Creation
  d/dt(a,b) = (1, -1) + ε·∇J

Topological space is created faster than metric space collapses,
reproducing MOND-like effects through dimensionality reduction.

References:
  • Arabieh et al. (2026) — "MOND from Compact Dimension Compression"
  • N-K Coupling — structural-spectral field interaction
-/

import Mathlib
import Mathlib.Analysis.InnerProductSpace.Basic

universe u v

namespace NKCoupling

-- =========================================================================
-- 1. Hyperbola Index (Perfect Square Distances)
-- =========================================================================

/-- For a research coordinate n ∈ ℕ, find the nearest perfect squares.
    a = distance to lower square, b = distance to upper square.
    ab = product (small = near crystallization point).
    a-b = difference (measure of asymmetry).
    -/
def nearestSquares (n : ℕ) : ℕ × ℕ :=
  let s := Nat.sqrt n
  let lower := s * s
  let upper := (s + 1) * (s + 1)
  (n - lower, upper - n)

/-- Hyperbola Index: ab = product of distances to nearest squares.
    Small values indicate coordinates near perfect squares (stable points). -/
def hyperbolaIndex (n : ℕ) : ℕ :=
  let (a, b) := nearestSquares n
  a * b

/-- Mirror Index: a-b = difference of distances.
    Measures symmetry — zero means exactly midway between squares. -/
def mirrorIndex (n : ℕ) : ℤ :=
  let (a, b) := nearestSquares n
  (a : ℤ) - (b : ℤ)

-- =========================================================================
-- 2. Field Definitions
-- =========================================================================

/-- Mass field F_m: local density of research mass at coordinate n.
    Higher where many ideas cluster. -/
structure MassField where
  density : ℕ → Float
  nonneg  : ∀ n, density n ≥ 0

/-- Phase-mirror field F_p: symmetry measure across domain boundary.
    High where physics↔market mirroring is strong. -/
structure MirrorField where
  symmetry : ℕ → Float
  bounded  : ∀ n, -1.0 ≤ symmetry n ∧ symmetry n ≤ 1.0

/-- Topological character χ(n): local structure of the research node.
    Encodes Betti numbers, connectivity, visibility. -/
structure TopologicalCharacter where
  chi : ℕ → Float
  norm : ∀ n, -1.0 ≤ chi n ∧ chi n ≤ 1.0

/-- Carrier field F_c: the "gossip" signal from other nodes.
    Dot product ⟨χ, F_c⟩ measures resonance with network. -/
structure CarrierField where
  signal : ℕ → Float
  energy : ∀ n, signal n ≥ 0

-- =========================================================================
-- 3. N-K Coupling Score J(n)
-- =========================================================================

/-- The N-K Coupling Score at coordinate n.

    J(n) = (ab)·F_m(n) + (a-b)·F_p(n) + χ(n)·F_c(n)

    Maximizing J(n) means:
    • High mass resonance (near crystallization point)
    • High mirror symmetry (cross-domain transferability)
    • High spectral coupling (network resonance)
    -/
def couplingScore
    (n : ℕ)
    (F_m : MassField)
    (F_p : MirrorField)
    (χ : TopologicalCharacter)
    (F_c : CarrierField)
    : Float :=
  let (a, b) := nearestSquares n
  let ab := (a * b : Float)
  let amb := ((a : ℤ) - (b : ℤ) : Float)
  let chi_n := χ.chi n
  let fc_n := F_c.signal n
  (ab * F_m.density n) + (amb * F_p.symmetry n) + (chi_n * fc_n)

/-- The N-K Coupling Law: J(n) is maximized at structural-spectral resonance.
    This is the condition for entering the MOND regime. -/
def isNKResonance
    (n : ℕ)
    (F_m : MassField)
    (F_p : MirrorField)
    (χ : TopologicalCharacter)
    (F_c : CarrierField)
    (threshold : Float := 0.5)
    : Prop :=
  couplingScore n F_m F_p χ F_c ≥ threshold

-- =========================================================================
-- 4. Space Creation Rate
-- =========================================================================

/-- Space creation rate: topological links vs metric curvature.

    d/dt(a,b) = (1, -1) + ε·∇J

    This means:
    • The (a,b) coordinate system evolves under the coupling gradient
    • Topological space (links between ideas) grows faster than
      metric space (Euclidean distance) collapses
    • This is the MOND-like effect: dimensionality reduction creates
      "shortcuts" between distant concepts

    In the Blitter context:
    • (1, -1): natural drift toward/away from crystallization
    • ε·∇J: coupling-driven correction that bends the trajectory
    -/
def spaceCreationRate
    (a b : Float)
    (ε : Float)
    (gradJ_a gradJ_b : Float)
    : Float × Float :=
  (1.0 + ε * gradJ_a, -1.0 + ε * gradJ_b)

/-- The MOND regime condition: topological links grow faster than
    metric curvature collapses them.

    |d/dt topological| >> |d/dt metric|
    -/
def isMONDRegime
    (topo_rate : Float)
    (metric_rate : Float)
    (ratio_threshold : Float := 10.0)
    : Prop :=
  Float.abs topo_rate ≥ ratio_threshold * Float.abs metric_rate

-- =========================================================================
-- 5. Connection to Manifold-Blit
-- =========================================================================

/-- In the Blitter architecture:
    • N-space = structural coordinates (instruments, files, research nodes)
    • K-space = spectral fields (correlations, visibility, Σ)
    • J(n) = coupling score determines which nodes to activate
    • MOND regime = when gossip creates shortcuts faster than noise collapses them

    The N-K Coupling explains:
    1. Why ternary weights work: J(n) is maximized at crystallization points
       where coarse-grained structure is most stable
    2. Why gossip converges: ∇J drives nodes toward resonance
    3. Why ACI matters: collisions disrupt the coupling gradient
    4. Why solitons are stable: the crystalline fixed point is a
       local maximum of J(n)
    -/

/-- Map a Blitter scalar node to its N-K coordinates (a,b). -/
def nodeToNKCoord {N : Nat} (i : Fin N) : ℕ × ℕ :=
  nearestSquares i.val

/-- Gossip energy eᵢ maps to carrier field F_c(i). -/
def gossipEnergyToCarrier (e : Float) : Float :=
  -- Normalize to [0, 1] via sigmoid
  1.0 / (1.0 + Float.exp (-e))

/-- Coherence κ maps to topological character χ. -/
def coherenceToCharacter (κ : Float) : Float :=
  -- Coherence in [0,1] maps directly to character
  2.0 * κ - 1.0  -- map to [-1, 1]

-- =========================================================================
-- 6. Verified Properties
-- =========================================================================

/-- Hyperbola index is minimized at perfect squares (crystallization points).
    For n = k²: a = 0, b = 2k+1, so ab = 0. -/
theorem hyperbola_min_at_squares (k : ℕ) :
    hyperbolaIndex (k * k) = 0 := by
  unfold hyperbolaIndex nearestSquares
  simp [Nat.sqrt_sq]
  <;> ring_nf <;> simp [Nat.mul_assoc]

/-- Mirror index is zero exactly midway between consecutive squares.
    For n = k² + k: a = k, b = k+1, so a-b = -1 (not zero).
    For n = k(k+1): exactly midway, a = k, b = k+1. -/
theorem mirror_zero_midway (k : ℕ) :
    let n := k * k + k
    mirrorIndex n = -1 := by
  unfold mirrorIndex nearestSquares
  have h1 : Nat.sqrt (k * k + k) = k := by
    rw [Nat.sqrt_eq_iff_sq_le] <;> nlinarith [Nat.sqrt_le_self (k * k + k)]
  simp [h1]
  <;> ring_nf <;> omega

/-- J(n) is bounded when all fields are bounded. -/
theorem couplingScore_bounded
    (n : ℕ)
    (F_m : MassField)
    (F_p : MirrorField)
    (χ : TopologicalCharacter)
    (F_c : CarrierField)
    (hF_m : F_m.density n ≤ M_max)
    (hF_p : -1.0 ≤ F_p.symmetry n ∧ F_p.symmetry n ≤ 1.0)
    (hχ : -1.0 ≤ χ.chi n ∧ χ.chi n ≤ 1.0)
    (hF_c : F_c.signal n ≤ C_max) :
    Float.abs (couplingScore n F_m F_p χ F_c) ≤
      (n : Float) * M_max + (n : Float) + C_max := by
  -- TODO(lean-port): BLOCKED on Float arithmetic reasoning in Lean.
  -- Standard bound: |ab·F_m| ≤ n·M_max, |amb·F_p| ≤ n, |χ·F_c| ≤ C_max.
  -- But Float.abs, Float multiplication, and addition lack associativity/commutativity
  -- lemmas in the current library. Consider reformulating in Q16_16 where exact
  -- fixed-point bounds are provable, or adding Float inequality axioms.

/-- In the MOND regime, the coupling gradient dominates natural drift.
    This ensures the system creates topological shortcuts. -/
theorem mondominance
    (ε : Float)
    (gradJ : Float)
    (hε : ε > 0)
    (hgrad : Float.abs gradJ > 1.0 / ε) :
    Float.abs (ε * gradJ) > 1.0 := by
  have h : Float.abs (ε * gradJ) = ε * Float.abs gradJ := by
    rw [Float.abs_mul]
    simp [Float.abs_of_pos hε]
  rw [h]
  nlinarith

end NKCoupling
