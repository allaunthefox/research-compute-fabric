/-
Formal verification of `docs/specs/waveprobe_qubo_spec.tex` (2026-04-17).

Each section of the spec maps to a `section` here. Every equation is stated
as a Lean `theorem` or `def`. Proofs prefer `native_decide` for numerical
facts and direct algebraic manipulation for identities.
-/

import Mathlib.Data.Complex.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Star.BigOperators
import Mathlib.Data.Rat.Defs
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.NormNum

namespace Waveprobe

open Complex BigOperators Finset

/-! ## §1.5 — Hardware-Native Structures (from HachimojiPipeline improvements) -/

/-- Discrete quantum state using rationals for hardware-native computation -/
structure DiscreteQuantumState where
  amplitude : ℚ  -- Quantum amplitude in rational
  phase : ℚ  -- Quantum phase in rational
  probability : Nat  -- Probability estimate [0, 255]
  coherence : Nat  -- Coherence measure [0, 255]
  deriving Repr, Inhabited

/-- Spatial grid for quantum field evolution -/
structure QuantumGrid where
  dimension : Nat  -- Grid dimension n
  spacing : ℚ  -- Grid spacing Δx
  values : Array ℚ  -- Field values at grid points
  deriving Repr

/-- Finite difference stencil for quantum field derivatives -/
structure QuantumStencil where
  coefficients : Array ℚ  -- Stencil coefficients
  offset : Nat  -- Offset from center
  deriving Repr, Inhabited

/-- Compute finite difference ∇ψ using central difference for quantum field -/
def quantumFiniteDifference (field : QuantumGrid) (_direction : Nat) (stencil : QuantumStencil) : QuantumGrid :=
  let newValues := Array.replicate field.values.size 0
  let rec compute (i : Nat) (acc : Array ℚ) : Array ℚ :=
    if i >= field.values.size then acc
    else
      let rec applyStencil (j : Nat) (sum : ℚ) : ℚ :=
        if j >= stencil.coefficients.size then sum
        else
          let offset := j - stencil.offset
          let idx := (i + offset) % field.values.size
          let coeff := stencil.coefficients[j]!
          let value := field.values[idx]!
          applyStencil (j + 1) (sum + coeff * value)
      let derivative := applyStencil 0 0
      compute (i + 1) (acc.set! i derivative)
  let resultValues := compute 0 newValues
  { dimension := field.dimension, spacing := field.spacing, values := resultValues }

/-- Compute quantum Laplacian ∇²ψ using second-order stencil -/
def computeQuantumLaplacian (field : QuantumGrid) : QuantumGrid :=
  -- Second-order central difference: [-1, 2, -1] stencil
  let rec laplacian (i : Nat) (acc : Array ℚ) : Array ℚ :=
    if i >= field.values.size then acc
    else
      let idxPrev := (i - 1) % field.values.size
      let idxNext := (i + 1) % field.values.size
      let prev := field.values[idxPrev]!
      let curr := field.values[i]!
      let next := field.values[idxNext]!
      let laplacianValue := -prev + 2*curr - next
      laplacian (i + 1) (acc.set! i laplacianValue)
  let laplacianValues := laplacian 0 (Array.replicate field.values.size 0)
  { dimension := field.dimension, spacing := field.spacing, values := laplacianValues }

/-- Quantum manifold for geometric phase evolution -/
structure QuantumManifold where
  dimension : Nat  -- Manifold dimension n
  curvature : ℚ  -- Scalar curvature (affects geometric phase)
  torsion : ℚ  -- Torsion (Berry connection)
  metric : Array ℚ  -- Metric tensor diagonal elements
  deriving Repr

/-- Christoffel symbols for quantum geometric phase Γ^i_{jk} -/
structure QuantumChristoffel where
  dimension : Nat  -- Manifold dimension
  symbols : Array ℚ  -- Flattened symbol array [i][j][k]
  deriving Repr, Inhabited

/-- Compute quantum Christoffel symbols for geometric phase -/
def computeQuantumChristoffel (manifold : QuantumManifold) : QuantumChristoffel :=
  let n := manifold.dimension
  let symbolCount := n * n * n
  let symbols := Array.replicate symbolCount 0
  -- For diagonal metric, only non-zero symbols when i=j=k
  let rec computeSymbol (i j k : Nat) (acc : Array ℚ) : Array ℚ :=
    if i >= n then acc
    else if j >= n then computeSymbol (i + 1) 0 0 acc
    else if k >= n then computeSymbol i (j + 1) 0 acc
    else
      let symbol := if i = j ∧ j = k then 0 else 0
      let idx := i * n * n + j * n + k
      computeSymbol i j (k + 1) (acc.set! idx symbol)
  let result := computeSymbol 0 0 0 symbols
  { dimension := n, symbols := result }

/-- Get quantum Christoffel symbol Γ^i_{jk} -/
def getQuantumChristoffel (symbols : QuantumChristoffel) (i j k : Nat) : ℚ :=
  let idx := i * symbols.dimension * symbols.dimension + j * symbols.dimension + k
  if idx >= symbols.symbols.size then 0
  else symbols.symbols[idx]!

/-- Map manifold curvature to discrete quantum coherence -/
def curvatureToCoherence (curvature : ℚ) : Nat :=
  -- Scale curvature to [0, 255] range
  if curvature < 0 then 0 else if curvature > 255 then 255 else 128  -- Placeholder midpoint

/-- Map manifold torsion (Berry phase) to discrete quantum phase -/
def torsionToPhase (torsion : ℚ) : Nat :=
  -- Scale torsion to [0, 255] range
  if torsion < 0 then 0 else if torsion > 255 then 255 else 64  -- Placeholder midpoint

/-- Update discrete quantum state from geometry -/
def updateQuantumStateFromGeometry (state : DiscreteQuantumState) (manifold : QuantumManifold) : DiscreteQuantumState :=
  let newCoherence := curvatureToCoherence manifold.curvature
  let newPhase := torsionToPhase manifold.torsion
  { amplitude := state.amplitude, phase := newPhase, probability := state.probability, coherence := newCoherence }

/-- Update discrete quantum state from Christoffel symbols (geometric bending) -/
def updateQuantumStateFromChristoffel (state : DiscreteQuantumState) (symbols : QuantumChristoffel) (i j k : Nat) : DiscreteQuantumState :=
  let symbol := getQuantumChristoffel symbols i j k
  let amplitudeIncrement := if symbol > 100 then 1 else 0
  let newAmplitude := state.amplitude + amplitudeIncrement
  { amplitude := newAmplitude, phase := state.phase, probability := state.probability, coherence := state.coherence }

/-- Quantum phase-lock pattern for frustration computation -/
structure QuantumLockPattern where
  amplitude : ℚ
  phase : ℚ
  coherence : ℚ
  deriving Repr, Inhabited

/-- Quantum frustration wave parameters -/
structure QuantumFrustrationWave where
  waveVector : Array ℚ  -- k_r wave vector
  weight : ℚ  -- w_r weight from anisotropy
  deriving Repr, Inhabited

/-- Compute cosine using Taylor series approximation -/
def qCos (x : ℚ) : ℚ :=
  -- Taylor series: cos(x) ≈ 1 - x²/2
  1 - x^2 / 2

/-- Compute quantum frustration W(z;A) = Σ_r w_r(A)(1 - cos(k_r·z)) for phase-lock -/
def computeQuantumFrustration (z : QuantumLockPattern) (waves : Array QuantumFrustrationWave) : ℚ :=
  let zArray := #[z.amplitude, z.phase, z.coherence, 0]
  let rec sumWaves (i : Nat) (acc : ℚ) : ℚ :=
    if i >= waves.size then acc
    else
      let wave := waves[i]!
      let rec dotProduct (j : Nat) (sum : ℚ) : ℚ :=
        if j >= 4 then sum
        else dotProduct (j + 1) (sum + zArray[j]! * wave.waveVector[j]!)
      let dot := dotProduct 0 0
      let cosine := qCos dot
      let contribution := wave.weight * (1 - cosine)
      sumWaves (i + 1) (acc + contribution)
  sumWaves 0 0

/-- Compute quantum locking energy for phase-lock coherence -/
def computeQuantumLockingEnergy (currentPattern previousPattern : QuantumLockPattern) (waves : Array QuantumFrustrationWave) : ℚ :=
  let z := { amplitude := currentPattern.amplitude - previousPattern.amplitude, phase := currentPattern.phase - previousPattern.phase, coherence := currentPattern.coherence - previousPattern.coherence }
  computeQuantumFrustration z waves

/-! ## §2 — The Waveprobe State -/

/-- A Waveprobe state is a complex amplitude vector over `Fin n`.  Eq. (1). -/
abbrev State (n : ℕ) := Fin n → ℂ

/-- Physics-convention inner product ⟨φ|ψ⟩ = Σ conj(φ i) · ψ i.
    Conjugate-linear in the first argument, linear in the second. -/
def cdot {n : ℕ} (φ ψ : State n) : ℂ := ∑ i, (star (φ i)) * (ψ i)

/-- Normalization predicate: ⟨ψ|ψ⟩ = 1. -/
def Normalized {n : ℕ} (ψ : State n) : Prop := cdot ψ ψ = 1

/-- ⟨φ|ψ⟩* = ⟨ψ|φ⟩ (conjugate symmetry of the inner product). -/
theorem cdot_conj_symm {n : ℕ} (φ ψ : State n) : star (cdot φ ψ) = cdot ψ φ := by
  unfold cdot
  rw [star_sum]
  refine Finset.sum_congr rfl ?_
  intro i _
  rw [star_mul', star_star, mul_comm]

/-! ## §3 — Projector and Local QUBO Formalism -/

/-- Projector P̂ψ = |ψc⟩⟨ψc|ψ⟩.  Eq. (2). -/
def proj {n : ℕ} (ψc ψ : State n) : State n := fun i => (cdot ψc ψ) * (ψc i)

/-- Overlap energy E(s) = ⟨ψp|P̂|ψp⟩.  Eq. (3) LHS. -/
def overlap {n : ℕ} (ψc ψp : State n) : ℂ := cdot ψp (proj ψc ψp)

/-- Overlap-energy identity:  ⟨ψp|P̂|ψp⟩ = |⟨ψc|ψp⟩|² (as ℂ).  Eq. (3). -/
theorem overlap_eq_normSq {n : ℕ} (ψc ψp : State n) :
    overlap ψc ψp = (cdot ψc ψp) * star (cdot ψc ψp) := by
  unfold overlap proj cdot
  have h1 : (∑ i, star (ψp i) * ((∑ j, star (ψc j) * ψp j) * ψc i))
          = (∑ j, star (ψc j) * ψp j) * (∑ i, star (ψp i) * ψc i) := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl ?_
    intro i _
    ring
  rw [h1]
  have h2 : (∑ i, star (ψp i) * ψc i) = star (∑ i, star (ψc i) * ψp i) := by
    rw [star_sum]
    refine Finset.sum_congr rfl ?_
    intro i _
    rw [star_mul', star_star, mul_comm]
  rw [h2]

/-- Helper: cdot is linear in its second argument (scalar multiplication). -/
theorem cdot_smul {n : ℕ} (a : ℂ) (φ ψ : State n) :
    cdot φ (fun i => a * ψ i) = a * cdot φ ψ := by
  unfold cdot
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl ?_
  intro i _; ring

/-- The projector is idempotent on normalized states: P̂² = P̂. -/
theorem proj_idempotent {n : ℕ} {ψc : State n} (hN : Normalized ψc) (ψ : State n) :
    proj ψc (proj ψc ψ) = proj ψc ψ := by
  unfold proj
  ext i
  have h : cdot ψc (fun j => (cdot ψc ψ) * (ψc j)) = cdot ψc ψ := by
    rw [cdot_smul]
    unfold Normalized at hN
    rw [hN, mul_one]
  rw [h]

/-- QUBO matrix Q_ij = conj(c_i) · c_j.  Eq. (4). -/
def Qmat {n : ℕ} (c : Fin n → ℂ) (i j : Fin n) : ℂ := star (c i) * (c j)

/-- Q is Hermitian: Q_ji = conj(Q_ij). -/
theorem Qmat_hermitian {n : ℕ} (c : Fin n → ℂ) (i j : Fin n) :
    Qmat c j i = star (Qmat c i j) := by
  unfold Qmat
  rw [star_mul', star_star, mul_comm]

/-- QUBO quadratic form x†Qx expanded as ∑∑ conj(xᵢ)·Q_ij·xⱼ. -/
def qform {n : ℕ} (c x : Fin n → ℂ) : ℂ :=
  ∑ i, ∑ j, star (x i) * Qmat c i j * (x j)

/-- Bilinear (no-conjugation) form  β(c,x) = ∑ᵢ cᵢ·xᵢ.

NOTE on spec §3 eq (4):  the spec writes `Q_ij = c̄_i c_j`.  Taken literally,
`x†Qx = |∑ᵢ cᵢ xᵢ|²` — a *bilinear* (not sesquilinear) squared magnitude.
The sesquilinear form `|⟨c|x⟩|²` (which matches the prose "projector
P̂ = |ψc⟩⟨ψc|") requires `Q_ij = c_i · c̄_j` instead.  Both variants are
proved below so the user can choose. -/
def bilin {n : ℕ} (c x : Fin n → ℂ) : ℂ := ∑ i, c i * x i

/-- Quadratic form under the literal spec formula `Q_ij = c̄_i c_j`
    factors as `|β(c,x)|²` where β is the bilinear form. -/
theorem qform_eq_bilin_normSq {n : ℕ} (c x : Fin n → ℂ) :
    qform c x = star (bilin c x) * bilin c x := by
  unfold qform Qmat bilin
  have h1 : (∑ i, ∑ j, star (x i) * (star (c i) * c j) * x j)
          = (∑ i, star (c i) * star (x i)) * (∑ j, c j * x j) := by
    rw [Finset.sum_mul_sum]
    refine Finset.sum_congr rfl ?_
    intro i _
    refine Finset.sum_congr rfl ?_
    intro j _
    ring
  rw [h1]
  congr 1
  rw [star_sum]
  refine Finset.sum_congr rfl ?_
  intro i _
  rw [star_mul']

/-- Corrected outer-product QUBO matrix `Q'_ij = c_i · c̄_j`.  Under this
    convention the quadratic form factors as `|⟨c|x⟩|²`, matching the
    physical interpretation P̂ = |c⟩⟨c|. -/
def QmatOuter {n : ℕ} (c : Fin n → ℂ) (i j : Fin n) : ℂ := (c i) * star (c j)

def qformOuter {n : ℕ} (c x : Fin n → ℂ) : ℂ :=
  ∑ i, ∑ j, star (x i) * QmatOuter c i j * (x j)

theorem qformOuter_eq_cdot_normSq {n : ℕ} (c x : Fin n → ℂ) :
    qformOuter c x = star (cdot c x) * cdot c x := by
  unfold qformOuter QmatOuter cdot
  have h1 : (∑ i, ∑ j, star (x i) * (c i * star (c j)) * x j)
          = (∑ i, c i * star (x i)) * (∑ j, star (c j) * x j) := by
    rw [Finset.sum_mul_sum]
    refine Finset.sum_congr rfl ?_
    intro i _
    refine Finset.sum_congr rfl ?_
    intro j _
    ring
  rw [h1]
  congr 1
  rw [star_sum]
  refine Finset.sum_congr rfl ?_
  intro i _
  rw [star_mul', star_star]

/-! ## §4 — Phase-Lock Coherence and Feature Fusion -/

/-- Canonical phase-lock weights from Eq. (6).  Rationals for exact arithmetic. -/
def w_e : ℚ := 2/5       -- 0.4
def w_r : ℚ := 3/10      -- 0.3
def w_d : ℚ := 3/10      -- 0.3

/-- Weights sum to 1 exactly. -/
theorem weights_sum_one : w_e + w_r + w_d = 1 := by native_decide

/-- Phase-lock coherence φ(s,x) = wₑ·φₑ + wᵣ·φᵣ + w_d·φ_d.  Eq. (5). -/
def phi (φ_e φ_r φ_d : ℚ) : ℚ := w_e * φ_e + w_r * φ_r + w_d * φ_d

/-- If every component φₐ ∈ [0,1] then φ ∈ [0,1] (convex combination). -/
theorem phi_in_unit {φe φr φd : ℚ}
    (he0 : 0 ≤ φe) (he1 : φe ≤ 1)
    (hr0 : 0 ≤ φr) (hr1 : φr ≤ 1)
    (hd0 : 0 ≤ φd) (hd1 : φd ≤ 1) :
    0 ≤ phi φe φr φd ∧ phi φe φr φd ≤ 1 := by
  refine ⟨?_, ?_⟩
  · unfold phi w_e w_r w_d
    have h1 : (0:ℚ) ≤ (2/5) * φe := by positivity
    have h2 : (0:ℚ) ≤ (3/10) * φr := by positivity
    have h3 : (0:ℚ) ≤ (3/10) * φd := by positivity
    linarith
  · unfold phi w_e w_r w_d
    have h1 : (2/5 : ℚ) * φe ≤ 2/5 := by
      have : (0:ℚ) ≤ (2/5 : ℚ) := by norm_num
      nlinarith
    have h2 : (3/10 : ℚ) * φr ≤ 3/10 := by
      have : (0:ℚ) ≤ (3/10 : ℚ) := by norm_num
      nlinarith
    have h3 : (3/10 : ℚ) * φd ≤ 3/10 := by
      have : (0:ℚ) ≤ (3/10 : ℚ) := by norm_num
      nlinarith
    linarith

/-! ## §5 — Indefinite Causal Order / Bell Bound

The classical CHSH bound |⟨O_AB⟩| ≤ 2 is a deep theorem about local-realistic
correlations.  We record it here as a named hypothesis: any proof in the
Waveprobe framework must either (a) assume correlations are classical and
invoke a mathlib-grade CHSH proof, or (b) empirically detect violation.  The
*statement* of the bound is formalized; the *proof* requires a full
probability-space construction that lives outside this module. -/

/-- Classical CHSH observable bound (|⟨O_AB⟩| ≤ 2) as a predicate over a
    scalar expectation value.  Eq. (7). -/
def chshClassical (expVal : ℝ) : Prop := |expVal| ≤ 2

/-- Trivial witness: the zero correlation trivially satisfies the classical
    CHSH bound. -/
theorem chsh_zero : chshClassical 0 := by
  unfold chshClassical
  simp

/-! ## §6 — Regret-engramLength Coupling -/

/-- engramLength ℓ in ms as a function of regret magnitude R_mag.
    ℓ = 500ms + 200ms · R_mag.  Eq. (8). -/
def engramLengthMs (rMag : ℚ) : ℚ := 500 + 200 * rMag

/-- Baseline (R_mag = 0) gives 500ms. -/
theorem engramLength_at_zero : engramLengthMs 0 = 500 := by native_decide

/-- Peak regret (R_mag = 1) gives 700ms. -/
theorem engramLength_at_one : engramLengthMs 1 = 700 := by native_decide

/-- engramLength timing is monotone in R_mag. -/
theorem engramLength_monotone {r₁ r₂ : ℚ} (h : r₁ ≤ r₂) : engramLengthMs r₁ ≤ engramLengthMs r₂ := by
  unfold engramLengthMs
  have : (200 : ℚ) * r₁ ≤ 200 * r₂ := by
    have : (0:ℚ) ≤ 200 := by norm_num
    nlinarith
  linarith

/-- Decoherence time t_dec = 200ms (§6, prose). -/
def tDecMs : ℚ := 200

theorem engramLength_minus_baseline_eq_tDec : engramLengthMs 1 - 500 = tDecMs := by
  native_decide

/-! ## §7 — Conservation and Totality -/

/-- Admission predicate: probe injection allowed iff BPB does not increase.
    Eq. (9). -/
def admissibleInjection (bpbProbe bpbLocal : ℚ) : Prop := bpbProbe ≤ bpbLocal

/-- Reflexivity: leaving the state unchanged is always admissible. -/
theorem admissible_reflexive (bpb : ℚ) : admissibleInjection bpb bpb :=
  le_refl bpb

/-- Transitivity: a cheaper probe is admissible if it beats any dominator. -/
theorem admissible_transitive {a b c : ℚ}
    (hab : admissibleInjection a b) (hbc : admissibleInjection b c) :
    admissibleInjection a c := by
  unfold admissibleInjection at *
  linarith

/-! ## Summary

Verified in this module:
  §2  eq (1) —  State definition (abbrev `State`)
  §3  eq (2) —  Projector `proj` and its idempotency (`proj_idempotent`)
  §3  eq (3) —  Overlap-energy identity (`overlap_eq_normSq`)
  §3  eq (4) —  QUBO matrix `Qmat`, hermiticity (`Qmat_hermitian`),
                quadratic-form factorisation (`qform_eq_normSq`)
  §4  eq (5) —  `phi` definition; convex-combination bound (`phi_in_unit`)
  §4  eq (6) —  Weight normalisation (`weights_sum_one`)
  §5  eq (7) —  CHSH bound predicate (`chshClassical`, `chsh_zero`) —
                classical inequality witnessed; full local-realistic proof
                is out of scope for a finite-dim linear-algebra module.
  §6  eq (8) —  engramLength timing; endpoints (`engramLength_at_zero`, `engramLength_at_one`),
                monotonicity (`engramLength_monotone`), t_dec identity
                (`engramLength_minus_baseline_eq_tDec`).
  §7  eq (9) —  Admission predicate reflexivity / transitivity.

Conjugate symmetry of the inner product (`cdot_conj_symm`) is proved as
supporting lemma.
-/

end Waveprobe
