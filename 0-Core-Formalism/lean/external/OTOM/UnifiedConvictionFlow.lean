import Mathlib.Data.Real.Basic
import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

noncomputable section

/-!
UnifiedConvictionFlow.lean

One coherent module combining:

1. A proof-carrying registry of laws
2. A reduced Φ-based state and gradient field
3. A law-driven augmentation of the potential
4. An augmented gradient flow whose dynamics genuinely depend on the laws

This file avoids fake `proofStatus : Bool` metadata. Every registered law carries an
actual proposition and its proof.

The continuous law layer is wired directly into the augmented potential, so the
gradient vector field changes when the law parameters change.
-/

namespace Semantics.UnifiedConvictionFlow

/- ============================================================
   §0  Proof-carrying registry
   ============================================================ -/

structure LawCertificate where
  lawName : String
  domain : String
  statementText : String
  theoremName : String
  statement : Prop
  proof : statement

def registrySize (L : List LawCertificate) : Nat := L.length

/- ============================================================
   §1  Discrete laws
   ============================================================ -/

namespace DiscreteLaws

theorem multiplicationDistributesNat (a b c : ℕ) :
    a * (b + c) = a * b + a * c := by
  rw [Nat.mul_add]

theorem degeneracyPenaltyBounded (D : ℕ) :
    64 - D ≤ 64 := by
  exact Nat.sub_le _ _

theorem productBoundedNat (a b A B : ℕ)
    (h_a : a ≤ A) (h_b : b ≤ B) :
    a * b ≤ A * B := by
  exact Nat.mul_le_mul h_a h_b

def hutterEquationStructure (C₁ C₂ C₃ S G F : ℕ) (w₁ w₂ w₃ : ℕ) : ℕ :=
  let unified := w₁ * C₁ + w₂ * C₂ + w₃ * C₃
  let denominator := G + F
  if denominator > 0 then unified * S / denominator else 0

def geneticEquationStructure (H G D : ℕ) : ℕ :=
  let penalty := 64 - D
  let product := H * G * penalty
  product / 64

def multiplicationLaw : LawCertificate :=
  { lawName := "Multiplication Distributes (Nat)"
    domain := "Discrete Algebra"
    statementText := "a * (b + c) = a*b + a*c over ℕ."
    theoremName := "multiplicationDistributesNat"
    statement := ∀ a b c : ℕ, a * (b + c) = a * b + a * c
    proof := multiplicationDistributesNat }

def degeneracyLaw : LawCertificate :=
  { lawName := "Degeneracy Penalty Bounded"
    domain := "Discrete Optimization"
    statementText := "64 - D ≤ 64 for every natural D."
    theoremName := "degeneracyPenaltyBounded"
    statement := ∀ D : ℕ, 64 - D ≤ 64
    proof := degeneracyPenaltyBounded }

def productBoundLaw : LawCertificate :=
  { lawName := "Product Bounded (Nat)"
    domain := "Discrete Order"
    statementText := "If a ≤ A and b ≤ B then a*b ≤ A*B over ℕ."
    theoremName := "productBoundedNat"
    statement := ∀ a b A B : ℕ, a ≤ A → b ≤ B → a * b ≤ A * B
    proof := productBoundedNat }

def registry : List LawCertificate :=
  [multiplicationLaw, degeneracyLaw, productBoundLaw]

end DiscreteLaws

/- ============================================================
   §2  Continuous / real laws
   ============================================================ -/

namespace RealLaws

def weightedScore (w₁ w₂ w₃ a b c : ℝ) : ℝ :=
  w₁ * a + w₂ * b + w₃ * c

theorem weightedCombinationBoundedReal
    (w₁ w₂ w₃ a b c : ℝ)
    (h_nonneg₁ : 0 ≤ w₁)
    (h_nonneg₂ : 0 ≤ w₂)
    (h_nonneg₃ : 0 ≤ w₃)
    (h_sum : w₁ + w₂ + w₃ = 1) :
    weightedScore w₁ w₂ w₃ a b c ≤ max a (max b c) := by
  have ha : a ≤ max a (max b c) := le_max_left _ _
  have hb : b ≤ max a (max b c) := le_trans (le_max_left _ _) (le_max_right _ _)
  have hc : c ≤ max a (max b c) := le_trans (le_max_right _ _) (le_max_right _ _)
  have h1 : w₁ * a ≤ w₁ * max a (max b c) := by
    exact mul_le_mul_of_nonneg_left ha h_nonneg₁
  have h2 : w₂ * b ≤ w₂ * max a (max b c) := by
    exact mul_le_mul_of_nonneg_left hb h_nonneg₂
  have h3 : w₃ * c ≤ w₃ * max a (max b c) := by
    exact mul_le_mul_of_nonneg_left hc h_nonneg₃
  have hsum_le :
      weightedScore w₁ w₂ w₃ a b c
        ≤ w₁ * max a (max b c) + w₂ * max a (max b c) + w₃ * max a (max b c) := by
    dsimp [weightedScore]
    linarith
  have hfactor :
      w₁ * max a (max b c) + w₂ * max a (max b c) + w₃ * max a (max b c)
        = (w₁ + w₂ + w₃) * max a (max b c) := by
    ring
  rw [hfactor] at hsum_le
  rw [h_sum, one_mul] at hsum_le
  exact hsum_le

def infoDensity (I H : ℝ) : ℝ := I / H

theorem informationDensityBoundedReal
    (I H : ℝ)
    (h_I : I ≤ H)
    (h_H : 0 < H) :
    infoDensity I H ≤ 1 := by
  dsimp [infoDensity]
  have h_eq_one : H / H = 1 := by
    apply div_self
    exact ne_of_gt h_H
  have h_mul : I * (1 / H) ≤ H * (1 / H) := by
    apply mul_le_mul_of_nonneg_right h_I
    apply div_nonneg
    · linarith
    · exact le_of_lt h_H
  rw [mul_one_div, mul_one_div, h_eq_one] at h_mul
  exact h_mul

theorem informationDensityNonneg
    (I H : ℝ)
    (h_nonneg : 0 ≤ I)
    (h_H : 0 < H) :
    0 ≤ infoDensity I H := by
  dsimp [infoDensity]
  exact div_nonneg h_nonneg (le_of_lt h_H)

def weightedCombinationLaw : LawCertificate :=
  { lawName := "Weighted Combination Bounded (Real)"
    domain := "Convex Analysis"
    statementText := "A convex weighted score is bounded by the largest channel."
    theoremName := "weightedCombinationBoundedReal"
    statement := ∀ w₁ w₂ w₃ a b c : ℝ,
      0 ≤ w₁ → 0 ≤ w₂ → 0 ≤ w₃ →
      w₁ + w₂ + w₃ = 1 →
      weightedScore w₁ w₂ w₃ a b c ≤ max a (max b c)
    proof := weightedCombinationBoundedReal }

def informationDensityLaw : LawCertificate :=
  { lawName := "Information Density Bounded (Real)"
    domain := "Information Theory"
    statementText := "If I ≤ H and H > 0, then I/H ≤ 1."
    theoremName := "informationDensityBoundedReal"
    statement := ∀ I H : ℝ, I ≤ H → 0 < H → infoDensity I H ≤ 1
    proof := informationDensityBoundedReal }

def registry : List LawCertificate :=
  [weightedCombinationLaw, informationDensityLaw]

end RealLaws

def fullRegistry : List LawCertificate :=
  DiscreteLaws.registry ++ RealLaws.registry

theorem fullRegistry_nonempty : fullRegistry ≠ [] := by
  decide

/- ============================================================
   §3  Reduced state and base Φ-system
   ============================================================ -/

abbrev State := ℝ × ℝ × ℝ × ℝ × ℝ × ℝ × ℝ
-- (ρ, v, τ, σ, q, κ, ε)

namespace State

def rho   (x : State) : ℝ := x.1
def v     (x : State) : ℝ := x.2.1
def tau   (x : State) : ℝ := x.2.2.1
def sigma (x : State) : ℝ := x.2.2.2.1
def q     (x : State) : ℝ := x.2.2.2.2.1
def kappa (x : State) : ℝ := x.2.2.2.2.2.1
def eps   (x : State) : ℝ := x.2.2.2.2.2.2

def mk (rho v tau sigma q kappa eps : ℝ) : State :=
  (rho, v, tau, sigma, q, kappa, eps)

def neg (x : State) : State :=
  mk (-(rho x)) (-(v x)) (-(tau x)) (-(sigma x))
     (-(q x)) (-(kappa x)) (-(eps x))

end State

namespace Field

def WellFormed (x : State) : Prop :=
  -1 < State.eps x

def numerator (x : State) : ℝ :=
  (State.rho x)^2 +
  (State.v x)^2 +
  (State.tau x)^2 +
  (State.sigma x)^2 +
  (State.q x)^2

def geometry (x : State) : ℝ :=
  1 + (State.kappa x)^2

def energy (x : State) : ℝ :=
  1 + State.eps x

def phi (x : State) : ℝ :=
  numerator x / (geometry x * energy x)

theorem numerator_nonneg (x : State) : 0 ≤ numerator x := by
  dsimp [numerator]
  nlinarith

theorem geometry_pos (x : State) : 0 < geometry x := by
  dsimp [geometry]
  nlinarith [sq_nonneg (State.kappa x)]

theorem energy_pos (x : State) (h : WellFormed x) : 0 < energy x := by
  dsimp [WellFormed, energy] at h ⊢
  linarith

theorem phi_nonneg (x : State) (h : WellFormed x) : 0 ≤ phi x := by
  dsimp [phi]
  refine div_nonneg (numerator_nonneg x) ?_
  exact le_of_lt (mul_pos (geometry_pos x) (energy_pos x h))

def gradPhi (x : State) : State :=
  let g := geometry x
  let e := energy x
  let n := numerator x
  State.mk
    ((2 * State.rho x) / (g * e))
    ((2 * State.v x) / (g * e))
    ((2 * State.tau x) / (g * e))
    ((2 * State.sigma x) / (g * e))
    ((2 * State.q x) / (g * e))
    (-(2 * State.kappa x * n) / (g^2 * e))
    (-n / (g * e^2))

def flow (x : State) : State :=
  State.neg (gradPhi x)

end Field

/- ============================================================
   §4  Law-driven augmentation of Φ
   ============================================================ -/

structure LawParams where
  w₁ : ℝ
  w₂ : ℝ
  w₃ : ℝ
  alpha : ℝ
  h_w₁ : 0 ≤ w₁
  h_w₂ : 0 ≤ w₂
  h_w₃ : 0 ≤ w₃
  h_sum : w₁ + w₂ + w₃ = 1
  h_alpha : 0 ≤ alpha

namespace LawCoupling

def lawChannels (x : State) : ℝ × ℝ × ℝ :=
  ((State.rho x)^2, (State.v x)^2, (State.tau x)^2)

def lawWeighted (p : LawParams) (x : State) : ℝ :=
  RealLaws.weightedScore p.w₁ p.w₂ p.w₃
    ((State.rho x)^2) ((State.v x)^2) ((State.tau x)^2)

theorem lawWeighted_nonneg (p : LawParams) (x : State) : 0 ≤ lawWeighted p x := by
  dsimp [lawWeighted, RealLaws.weightedScore]
  nlinarith [sq_nonneg (State.rho x), sq_nonneg (State.v x), sq_nonneg (State.tau x),
    p.h_w₁, p.h_w₂, p.h_w₃]

theorem lawWeighted_bounded (p : LawParams) (x : State) :
    lawWeighted p x ≤ max ((State.rho x)^2) (max ((State.v x)^2) ((State.tau x)^2)) := by
  exact RealLaws.weightedCombinationBoundedReal
    p.w₁ p.w₂ p.w₃
    ((State.rho x)^2) ((State.v x)^2) ((State.tau x)^2)
    p.h_w₁ p.h_w₂ p.h_w₃ p.h_sum

/-- Explicit gradient of the law-driven weighted term. -/
def gradLawWeighted (p : LawParams) (x : State) : State :=
  State.mk
    (2 * p.w₁ * State.rho x)
    (2 * p.w₂ * State.v x)
    (2 * p.w₃ * State.tau x)
    0
    0
    0
    0

/--
Augmented potential:
base Φ plus a law-driven term that depends on the state.
This means the gradient flow actually changes with the law parameters.
-/
def phiAugmented (p : LawParams) (x : State) : ℝ :=
  Field.phi x + p.alpha * lawWeighted p x

def gradPhiAugmented (p : LawParams) (x : State) : State :=
  State.mk
    (State.rho (Field.gradPhi x) + p.alpha * State.rho (gradLawWeighted p x))
    (State.v (Field.gradPhi x) + p.alpha * State.v (gradLawWeighted p x))
    (State.tau (Field.gradPhi x) + p.alpha * State.tau (gradLawWeighted p x))
    (State.sigma (Field.gradPhi x))
    (State.q (Field.gradPhi x))
    (State.kappa (Field.gradPhi x))
    (State.eps (Field.gradPhi x))

def flowAugmented (p : LawParams) (x : State) : State :=
  State.neg (gradPhiAugmented p x)

theorem phiAugmented_ge_phi (p : LawParams) (x : State) :
    Field.phi x ≤ phiAugmented p x := by
  have hLaw : 0 ≤ lawWeighted p x := lawWeighted_nonneg p x
  dsimp [phiAugmented]
  nlinarith [p.h_alpha, hLaw]

theorem phiAugmented_nonneg (p : LawParams) (x : State) (h : Field.WellFormed x) :
    0 ≤ phiAugmented p x := by
  have hBase : 0 ≤ Field.phi x := Field.phi_nonneg x h
  have hLaw : 0 ≤ lawWeighted p x := lawWeighted_nonneg p x
  dsimp [phiAugmented]
  nlinarith [p.h_alpha, hBase, hLaw]

theorem flowAugmented_differs_on_rho
    (p : LawParams) (x : State)
    (hα : 0 < p.alpha)
    (hw : 0 < p.w₁)
    (hρ : State.rho x ≠ 0) :
    State.rho (flowAugmented p x) ≠ State.rho (Field.flow x) := by
  dsimp [flowAugmented, Field.flow, gradPhiAugmented, LawCoupling.gradLawWeighted,
    State.neg, State.rho, State.mk]
  intro hEq
  have h_prod_pos : p.alpha * p.w₁ > 0 := by
    apply mul_pos hα hw
  have h_neq_zero : p.alpha * p.w₁ * State.rho x ≠ 0 := by
    apply mul_ne_zero (ne_of_gt h_prod_pos) hρ
  have h_eq_pos : (Field.gradPhi x).1 + p.alpha * (2 * p.w₁ * State.rho x) = (Field.gradPhi x).1 := by
    have h_eq_neg : -((Field.gradPhi x).1 + p.alpha * (2 * p.w₁ * State.rho x)) = -(Field.gradPhi x).1 := hEq
    linarith
  have h_eq_zero : p.alpha * (2 * p.w₁ * State.rho x) = 0 := by
    linarith [h_eq_pos]
  have hprod : p.alpha * p.w₁ * State.rho x = 0 := by
    have h_eq_simp3 : 2 * (p.alpha * p.w₁ * State.rho x) = 0 := by
      linarith [h_eq_zero]
    linarith [h_eq_simp3]
  contradiction

end LawCoupling

/- ============================================================
   §5  Unified theorem-bearing registry
   ============================================================ -/

def unifiedRegistry : List LawCertificate := fullRegistry

theorem unifiedRegistry_size :
    registrySize unifiedRegistry = 5 := by
  decide

/- ============================================================
   §6  Example parameters and example state
   ============================================================ -/

namespace Examples

def params : LawParams :=
  { w₁ := 1/2
    w₂ := 1/4
    w₃ := 1/4
    alpha := 2
    h_w₁ := by norm_num
    h_w₂ := by norm_num
    h_w₃ := by norm_num
    h_sum := by norm_num
    h_alpha := by norm_num }

def x0 : State := State.mk 2 1 3 0 0 0 0

example : Field.WellFormed x0 := by
  dsimp [x0, Field.WellFormed, State.eps, State.mk]
  norm_num

example : 0 ≤ LawCoupling.phiAugmented params x0 := by
  apply LawCoupling.phiAugmented_nonneg
  exact by
    dsimp [x0, Field.WellFormed, State.eps, State.mk]
    norm_num

example :
    State.rho (LawCoupling.flowAugmented params x0)
      ≠ State.rho (Field.flow x0) := by
  apply LawCoupling.flowAugmented_differs_on_rho
  · norm_num [params]
  · norm_num [params]
  · dsimp [x0, State.rho, State.mk]
    norm_num

end Examples

end Semantics.UnifiedConvictionFlow
