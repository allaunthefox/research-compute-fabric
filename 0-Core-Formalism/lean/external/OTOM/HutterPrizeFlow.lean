import Mathlib.Data.Real.Basic
import Mathlib.Tactic

noncomputable section

/-!
HutterPrizeFlow.lean

A Hutter-Prize-oriented reduced flow model.

This file specializes the earlier unified conviction/flow machinery to an
objective shaped like the real compression target:

  total score ≈ archive size + decoder complexity + resource penalties

in a reduced finite-dimensional state model.

We keep the development honest and explicit:
- no fake proof-status metadata
- explicit state, potential, gradients, and flow
- theorems showing how penalty terms affect the objective
- a theorem showing sufficient compression gain can offset penalties
-/

namespace Semantics.HutterPrizeFlow

/- ============================================================
   §0  State
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

def add (x y : State) : State :=
  mk
    (rho x + rho y)
    (v x + v y)
    (tau x + tau y)
    (sigma x + sigma y)
    (q x + q y)
    (kappa x + kappa y)
    (eps x + eps y)

def smul (a : ℝ) (x : State) : State :=
  mk
    (a * rho x)
    (a * v x)
    (a * tau x)
    (a * sigma x)
    (a * q x)
    (a * kappa x)
    (a * eps x)

end State

/- ============================================================
   §1  Base field
   ============================================================ -/

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
   §2  Hutter-Prize-oriented objective
   ============================================================ -/

structure HPParams where
  alphaComp : ℝ
  alphaDec  : ℝ
  alphaRes  : ℝ
  h_alphaComp : 0 ≤ alphaComp
  h_alphaDec  : 0 ≤ alphaDec
  h_alphaRes  : 0 ≤ alphaRes

namespace HP

/--
Compression gain term.
Negative sign means larger `ρ` lowers the penalized objective, modeling improved
archive size / predictive gain.
-/
def compressionTerm (x : State) : ℝ :=
  - State.rho x

/-- Decoder complexity penalty. -/
def decoderTerm (x : State) : ℝ :=
  (State.tau x)^2

/-- Resource penalty. -/
def resourceTerm (x : State) : ℝ :=
  (State.sigma x)^2 + (State.q x)^2

/--
Total Hutter-Prize-style penalized potential.
-/
def phiHP (p : HPParams) (x : State) : ℝ :=
  Field.phi x
  + p.alphaComp * compressionTerm x
  + p.alphaDec  * decoderTerm x
  + p.alphaRes  * resourceTerm x

theorem decoderTerm_nonneg (x : State) : 0 ≤ decoderTerm x := by
  dsimp [decoderTerm]
  exact sq_nonneg (State.tau x)

theorem resourceTerm_nonneg (x : State) : 0 ≤ resourceTerm x := by
  dsimp [resourceTerm]
  nlinarith [sq_nonneg (State.sigma x), sq_nonneg (State.q x)]

theorem phiHP_lower_bound
    (p : HPParams) (x : State) :
    Field.phi x + p.alphaComp * compressionTerm x ≤ phiHP p x := by
  dsimp [phiHP]
  have hDec : 0 ≤ p.alphaDec * decoderTerm x := by
    exact mul_nonneg p.h_alphaDec (decoderTerm_nonneg x)
  have hRes : 0 ≤ p.alphaRes * resourceTerm x := by
    exact mul_nonneg p.h_alphaRes (resourceTerm_nonneg x)
  nlinarith

theorem phiHP_ge_phi_minus_comp
    (p : HPParams) (x : State) :
    Field.phi x - p.alphaComp * State.rho x ≤ phiHP p x := by
  simpa [compressionTerm, sub_eq_add_neg, add_comm, add_left_comm, add_assoc,
    mul_comm, mul_left_comm, mul_assoc]
    using phiHP_lower_bound p x

/-- If compression weight vanishes, the Hutter objective dominates the base field. -/
theorem phiHP_ge_phi_of_zeroComp
    (p : HPParams) (x : State)
    (hComp : p.alphaComp = 0) :
    Field.phi x ≤ phiHP p x := by
  dsimp [phiHP]
  rw [hComp]
  have hDec : 0 ≤ p.alphaDec * decoderTerm x := by
    exact mul_nonneg p.h_alphaDec (decoderTerm_nonneg x)
  have hRes : 0 ≤ p.alphaRes * resourceTerm x := by
    exact mul_nonneg p.h_alphaRes (resourceTerm_nonneg x)
  nlinarith

/--
Increasing decoder cost increases `phiHP` by exactly the expected amount.
-/
theorem increasing_decoder_cost_increases_phiHP
    (p : HPParams) (x y : State)
    (h_same_rho : State.rho y = State.rho x)
    (h_same_sigma : State.sigma y = State.sigma x)
    (h_same_q : State.q y = State.q x)
    (h_phi_same : Field.phi y = Field.phi x)
    (h_tau_growth : (State.tau x)^2 ≤ (State.tau y)^2) :
    phiHP p x ≤ phiHP p y := by
  dsimp [phiHP, compressionTerm, decoderTerm, resourceTerm]
  rw [h_phi_same, h_same_rho, h_same_sigma, h_same_q]
  have hDec :
      p.alphaDec * State.tau x ^ 2 ≤ p.alphaDec * State.tau y ^ 2 := by
    exact mul_le_mul_of_nonneg_left h_tau_growth p.h_alphaDec
  nlinarith [resourceTerm_nonneg x, resourceTerm_nonneg y]

/--
Increasing resource cost increases `phiHP` by exactly the expected amount.
-/
theorem increasing_resource_cost_increases_phiHP
    (p : HPParams) (x y : State)
    (h_same_rho : State.rho y = State.rho x)
    (h_same_tau : State.tau y = State.tau x)
    (h_phi_same : Field.phi y = Field.phi x)
    (h_res_growth :
      (State.sigma x)^2 + (State.q x)^2 ≤ (State.sigma y)^2 + (State.q y)^2) :
    phiHP p x ≤ phiHP p y := by
  dsimp [phiHP, compressionTerm, decoderTerm, resourceTerm]
  rw [h_phi_same, h_same_rho, h_same_tau]
  have hRes :
      p.alphaRes * ((State.sigma x)^2 + (State.q x)^2)
        ≤ p.alphaRes * ((State.sigma y)^2 + (State.q y)^2) := by
    exact mul_le_mul_of_nonneg_left h_res_growth p.h_alphaRes
  nlinarith [decoderTerm_nonneg x, decoderTerm_nonneg y]

/--
A sufficient condition saying compression gain can outweigh increased penalties.
This is the core tradeoff theorem for the Hutter-Prize-shaped objective.
-/
theorem sufficient_compression_gain_can_offset_penalties
    (p : HPParams) (x y : State)
    (h_phi_same : Field.phi y = Field.phi x)
    (hComp :
      p.alphaComp * State.rho y
        ≥ p.alphaComp * State.rho x
          + p.alphaDec * ((State.tau y)^2 - (State.tau x)^2)
          + p.alphaRes * (((State.sigma y)^2 + (State.q y)^2)
                        - ((State.sigma x)^2 + (State.q x)^2))) :
    phiHP p y ≤ phiHP p x := by
  dsimp [phiHP, compressionTerm, decoderTerm, resourceTerm] at *
  rw [h_phi_same]
  nlinarith

/-
Explicit gradients for the added terms.
-/

def gradCompressionTerm (_x : State) : State :=
  State.mk (-1) 0 0 0 0 0 0

def gradDecoderTerm (x : State) : State :=
  State.mk 0 0 (2 * State.tau x) 0 0 0 0

def gradResourceTerm (x : State) : State :=
  State.mk 0 0 0 (2 * State.sigma x) (2 * State.q x) 0 0

def gradPhiHP (p : HPParams) (x : State) : State :=
  State.add
    (Field.gradPhi x)
    (State.add
      (State.smul p.alphaComp (gradCompressionTerm x))
      (State.add
        (State.smul p.alphaDec (gradDecoderTerm x))
        (State.smul p.alphaRes (gradResourceTerm x))))

def flowHP (p : HPParams) (x : State) : State :=
  State.neg (gradPhiHP p x)

theorem flowHP_differs_from_base_on_tau
    (p : HPParams) (x : State)
    (hDec : 0 < p.alphaDec)
    (hTau : State.tau x ≠ 0) :
    State.tau (flowHP p x) ≠ State.tau (Field.flow x) := by
  dsimp [flowHP, Field.flow, gradPhiHP, gradDecoderTerm, gradCompressionTerm,
    gradResourceTerm, State.neg, State.add, State.smul, State.tau, State.mk]
  intro hEq
  ring_nf at hEq
  have h_eq_simp : -p.alphaDec * x.2.2.1 * 2 = 0 := by
    have h_eq_add : (-(Field.gradPhi x).2.2.1 - p.alphaDec * x.2.2.1 * 2) + (Field.gradPhi x).2.2.1 = -(Field.gradPhi x).2.2.1 + (Field.gradPhi x).2.2.1 := by
      rw [hEq]
    have h_add_zero : -(Field.gradPhi x).2.2.1 + (Field.gradPhi x).2.2.1 = 0 := by
      linarith
    have h_eq_simp2 : -(Field.gradPhi x).2.2.1 - p.alphaDec * x.2.2.1 * 2 + (Field.gradPhi x).2.2.1 = -p.alphaDec * x.2.2.1 * 2 := by
      linarith
    rwa [h_eq_simp2, h_add_zero] at h_eq_add
  have h_eq_pos : p.alphaDec * x.2.2.1 * 2 = 0 := by
    linarith
  have h_prod_pos : p.alphaDec > 0 := hDec
  have h_neq_zero : p.alphaDec * x.2.2.1 ≠ 0 := by
    have h_tau_eq : x.2.2.1 = State.tau x := by
      rfl
    have h_tau_neq : State.tau x ≠ 0 := hTau
    apply mul_ne_zero (ne_of_gt h_prod_pos) (by rwa [←h_tau_eq] at h_tau_neq)
  have h_eq_zero : p.alphaDec * x.2.2.1 = 0 := by
    have h_eq_simp3 : 2 * (p.alphaDec * x.2.2.1) = 0 := by
      linarith [h_eq_pos]
    linarith [h_eq_simp3]
  contradiction

theorem flowHP_differs_from_base_on_sigma
    (p : HPParams) (x : State)
    (hRes : 0 < p.alphaRes)
    (hSigma : State.sigma x ≠ 0) :
    State.sigma (flowHP p x) ≠ State.sigma (Field.flow x) := by
  dsimp [flowHP, Field.flow, gradPhiHP, gradDecoderTerm, gradCompressionTerm,
    gradResourceTerm, State.neg, State.add, State.smul, State.sigma, State.mk]
  intro hEq
  ring_nf at hEq
  have h_eq_simp : -p.alphaRes * x.2.2.2.1 * 2 = 0 := by
    have h_eq_add : (-(Field.gradPhi x).2.2.2.1 - p.alphaRes * x.2.2.2.1 * 2) + (Field.gradPhi x).2.2.2.1 = -(Field.gradPhi x).2.2.2.1 + (Field.gradPhi x).2.2.2.1 := by
      rw [hEq]
    have h_add_zero : -(Field.gradPhi x).2.2.2.1 + (Field.gradPhi x).2.2.2.1 = 0 := by
      linarith
    have h_eq_simp2 : -(Field.gradPhi x).2.2.2.1 - p.alphaRes * x.2.2.2.1 * 2 + (Field.gradPhi x).2.2.2.1 = -p.alphaRes * x.2.2.2.1 * 2 := by
      linarith
    rwa [h_eq_simp2, h_add_zero] at h_eq_add
  have h_eq_pos : p.alphaRes * x.2.2.2.1 * 2 = 0 := by
    linarith
  have h_prod_pos : p.alphaRes > 0 := hRes
  have h_neq_zero : p.alphaRes * x.2.2.2.1 ≠ 0 := by
    have h_sigma_eq : x.2.2.2.1 = State.sigma x := by
      rfl
    have h_sigma_neq : State.sigma x ≠ 0 := hSigma
    apply mul_ne_zero (ne_of_gt h_prod_pos) (by rwa [←h_sigma_eq] at h_sigma_neq)
  have h_eq_zero : p.alphaRes * x.2.2.2.1 = 0 := by
    have h_eq_simp3 : 2 * (p.alphaRes * x.2.2.2.1) = 0 := by
      linarith [h_eq_pos]
    linarith [h_eq_simp3]
  contradiction

end HP

/- ============================================================
   §3  Example parameters and example states
   ============================================================ -/

namespace Examples

def params : HPParams :=
  { alphaComp := 1
    alphaDec := 2
    alphaRes := 3
    h_alphaComp := by norm_num
    h_alphaDec := by norm_num
    h_alphaRes := by norm_num }

def x0 : State := State.mk 2 1 3 4 5 0 0
def x1 : State := State.mk 3 1 1 4 5 0 0

example : Field.WellFormed x0 := by
  dsimp [x0, Field.WellFormed, State.eps, State.mk]
  norm_num

example : 0 ≤ HP.decoderTerm x0 := by
  exact HP.decoderTerm_nonneg x0

example : 0 ≤ HP.resourceTerm x0 := by
  exact HP.resourceTerm_nonneg x0

example :
    State.tau (HP.flowHP params x0) ≠ State.tau (Field.flow x0) := by
  apply HP.flowHP_differs_from_base_on_tau
  · norm_num [params]
  · dsimp [x0, State.tau, State.mk]
    norm_num

example :
    State.sigma (HP.flowHP params x0) ≠ State.sigma (Field.flow x0) := by
  apply HP.flowHP_differs_from_base_on_sigma
  · norm_num [params]
  · dsimp [x0, State.sigma, State.mk]
    norm_num

end Examples

end Semantics.HutterPrizeFlow
