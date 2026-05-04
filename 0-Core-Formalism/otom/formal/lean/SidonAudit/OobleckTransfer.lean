import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Oobleck Transfer

This module combines the phonon-density and Lagrangian-transfer metaphors into
an "oobleck" audit layer.

The terminology is useful:

* phonon modes describe the linear digit vibrations;
* Lagrangian lattice points describe exact transfer locations;
* oobleck/shear-thickening describes a desired collision-triggered lock.

But the audit rule is strict: metaphorical shear-thickening is not a Sidon
receipt. A symmetric lock still preserves the crossed-pair degeneracy

`(0,0) + (1,1) = (0,1) + (1,0)`.

A merely anisotropic diagonal lock also preserves that degeneracy. Distinct
coordinate weights change the cost of each coordinate, but they still sum the
same two coordinate costs on both sides of the crossed-pair collision.

A dielectric-field story is therefore admissible only if the field is nonlinear
or correlation-carrying enough to distinguish crossed pairings, and if that
orientation mechanism is paired with a power-law density receipt.
-/

namespace SidonAudit

/-- Gate status for this audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/--
Two-mode oobleck transfer energy.

`mu` is a shear-thickening coefficient multiplying the symmetric quadratic
phonon density. This is intentionally symmetric in `(x,y)`.
-/
def twoModeOobleckEnergy (M mu x y : ℕ) : ℕ :=
  x + y * M + mu * (x ^ 2 + y ^ 2) * M ^ 2

/--
The naive oobleck lock still has the crossed-pair collision.

For every positive base `M` and every shear coefficient `mu`, the symmetric
phonon-density lock gives the same total transfer energy to `(0,0)+(1,1)` and
`(0,1)+(1,0)`, while those are different unordered global pairs.
-/
theorem symmetric_oobleck_lock_collision
    (M mu : ℕ) (hM : 0 < M) :
    let a := twoModeOobleckEnergy M mu 0 0
    let b := twoModeOobleckEnergy M mu 1 1
    let c := twoModeOobleckEnergy M mu 0 1
    let d := twoModeOobleckEnergy M mu 1 0
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp [twoModeOobleckEnergy]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpos : 0 < M + mu * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h.1, hpos]
    · have h1 : M + mu * M ^ 2 = 0 := by
        nlinarith [h.2]
      have hpos : 0 < M + mu * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h1, hpos]

/--
Two-mode anisotropic oobleck energy.

The coefficients `lambdaX` and `lambdaY` weight the two coordinate-square
terms differently. This is a diagonal anisotropic lock, not a true orientation
or correlation code.
-/
def twoModeAnisotropicOobleckEnergy
    (M lambdaX lambdaY x y : ℕ) : ℕ :=
  x + y * M + (lambdaX * x ^ 2 + lambdaY * y ^ 2) * M ^ 2

/--
A diagonal anisotropic lock still has the crossed-pair collision.

Even with distinct coordinate weights, `(0,0)+(1,1)` and `(0,1)+(1,0)` have the
same total weighted-square contribution: `lambdaX + lambdaY` on both sides.
So anisotropy by coordinate weighting is not yet an orientation receipt.
-/
theorem anisotropic_oobleck_lock_collision
    (M lambdaX lambdaY : ℕ) (hM : 0 < M) :
    let a := twoModeAnisotropicOobleckEnergy M lambdaX lambdaY 0 0
    let b := twoModeAnisotropicOobleckEnergy M lambdaX lambdaY 1 1
    let c := twoModeAnisotropicOobleckEnergy M lambdaX lambdaY 0 1
    let d := twoModeAnisotropicOobleckEnergy M lambdaX lambdaY 1 0
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp [twoModeAnisotropicOobleckEnergy]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpos : 0 < M + lambdaY * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h.1, hpos]
    · have h1 : M + lambdaY * M ^ 2 = 0 := by
        nlinarith [h.2]
      have hpos : 0 < M + lambdaY * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h1, hpos]

/--
Linear dielectric energy is exactly diagonal anisotropy in physical language.
`epsX` and `epsY` are local permittivity/charge weights.
-/
def twoModeLinearDielectricEnergy
    (M epsX epsY x y : ℕ) : ℕ :=
  x + y * M + (epsX * x ^ 2 + epsY * y ^ 2) * M ^ 2

/--
A linear variable-charge dielectric field still has the crossed-pair collision.
Changing the local permittivity weights does not by itself encode orientation:
both sides contain one `epsX` contribution and one `epsY` contribution.
-/
theorem linear_dielectric_lock_collision
    (M epsX epsY : ℕ) (hM : 0 < M) :
    let a := twoModeLinearDielectricEnergy M epsX epsY 0 0
    let b := twoModeLinearDielectricEnergy M epsX epsY 1 1
    let c := twoModeLinearDielectricEnergy M epsX epsY 0 1
    let d := twoModeLinearDielectricEnergy M epsX epsY 1 0
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp [twoModeLinearDielectricEnergy]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpos : 0 < M + epsY * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h.1, hpos]
    · have h1 : M + epsY * M ^ 2 = 0 := by
        nlinarith [h.2]
      have hpos : 0 < M + epsY * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h1, hpos]

/--
A nonlinear dielectric potential: the weighted square contribution is passed
through a nonlinear external field `s ↦ s^2`.

This is not claimed to prove the Sidon theorem; it only demonstrates the kind of
nonlinear/correlation mechanism that can distinguish the basic crossed pair.
-/
def twoModeNonlinearDielectricEnergy
    (M epsX epsY x y : ℕ) : ℕ :=
  x + y * M + (epsX * x ^ 2 + epsY * y ^ 2) ^ 2 * M ^ 2

/--
The nonlinear dielectric potential breaks the basic crossed-pair degeneracy
when both local charges are positive.

This is only a local sanity check. It does not prove global Sidon uniqueness or
asymptotic density; those remain explicit receipts.
-/
theorem nonlinear_dielectric_breaks_basic_crossing
    (M epsX epsY : ℕ) (hM : 0 < M) (hX : 0 < epsX) (hY : 0 < epsY) :
    let a := twoModeNonlinearDielectricEnergy M epsX epsY 0 0
    let b := twoModeNonlinearDielectricEnergy M epsX epsY 1 1
    let c := twoModeNonlinearDielectricEnergy M epsX epsY 0 1
    let d := twoModeNonlinearDielectricEnergy M epsX epsY 1 0
    a + b ≠ c + d := by
  dsimp [twoModeNonlinearDielectricEnergy]
  intro h
  have hpos : 0 < 2 * epsX * epsY * M ^ 2 := by
    nlinarith [hM, hX, hY]
  nlinarith [h, hpos]

/-- The phonon component: linear digit vibrations are represented. -/
structure PhononDensityReceipt where
  statement : Prop

/-- The Lagrangian component: transfer points are exact in the chosen base. -/
structure LagrangianTransferReceipt where
  statement : Prop

/-- The missing structural component: orientation must be encoded, not merely norm. -/
structure OrientationShearReceipt where
  statement : Prop

/-- A stronger structural receipt: cross-coordinate correlation/chirality is encoded. -/
structure ChiralCorrelationReceipt where
  statement : Prop

/-- The dielectric field must be nonlinear/correlation-bearing, not merely weighted. -/
structure DielectricNonlinearReceipt where
  statement : Prop

/-- The asymptotic component: the extra lock must not destroy the target density. -/
structure OobleckPowerLawReceipt where
  statement : Prop

/-- Full receipt package for promoting the oobleck route. -/
structure OobleckTransferReceipts where
  phonon_density : Prop
  lagrangian_transfer : Prop
  orientation_shear : Prop
  chiral_correlation : Prop
  dielectric_nonlinearity : Prop
  power_law_density : Prop

/-- All six receipts are required. -/
def OobleckClosed (r : OobleckTransferReceipts) : Prop :=
  r.phonon_density ∧ r.lagrangian_transfer ∧ r.orientation_shear ∧
    r.chiral_correlation ∧ r.dielectric_nonlinearity ∧ r.power_law_density

/-- The oobleck gate promotes only if all receipts are present. -/
def OobleckGate (r : OobleckTransferReceipts) : GateScope :=
  if OobleckClosed r then GateScope.V_scope else GateScope.U_scope

/-- Missing orientation shear keeps the oobleck route unverified. -/
theorem oobleck_gate_U_without_orientation_shear
    (r : OobleckTransferReceipts) :
    ¬ r.orientation_shear →
    OobleckGate r = GateScope.U_scope := by
  intro hNo
  simp [OobleckGate, OobleckClosed]
  intro hAll
  exact hNo hAll.2.2.1

/-- Missing chiral/correlation receipt keeps the oobleck route unverified. -/
theorem oobleck_gate_U_without_chiral_correlation
    (r : OobleckTransferReceipts) :
    ¬ r.chiral_correlation →
    OobleckGate r = GateScope.U_scope := by
  intro hNo
  simp [OobleckGate, OobleckClosed]
  intro hAll
  exact hNo hAll.2.2.2.1

/-- Missing dielectric nonlinearity keeps the oobleck route unverified. -/
theorem oobleck_gate_U_without_dielectric_nonlinearity
    (r : OobleckTransferReceipts) :
    ¬ r.dielectric_nonlinearity →
    OobleckGate r = GateScope.U_scope := by
  intro hNo
  simp [OobleckGate, OobleckClosed]
  intro hAll
  exact hNo hAll.2.2.2.2.1

/-- Missing power-law density keeps the oobleck route unverified. -/
theorem oobleck_gate_U_without_power_law
    (r : OobleckTransferReceipts) :
    ¬ r.power_law_density →
    OobleckGate r = GateScope.U_scope := by
  intro hNo
  simp [OobleckGate, OobleckClosed]
  intro hAll
  exact hNo hAll.2.2.2.2.2

/-- Missing Lagrangian exactness keeps the oobleck route unverified. -/
theorem oobleck_gate_U_without_lagrangian_transfer
    (r : OobleckTransferReceipts) :
    ¬ r.lagrangian_transfer →
    OobleckGate r = GateScope.U_scope := by
  intro hNo
  simp [OobleckGate, OobleckClosed]
  intro hAll
  exact hNo hAll.2.1

/-- Missing phonon density keeps the oobleck route unverified. -/
theorem oobleck_gate_U_without_phonon_density
    (r : OobleckTransferReceipts) :
    ¬ r.phonon_density →
    OobleckGate r = GateScope.U_scope := by
  intro hNo
  simp [OobleckGate, OobleckClosed]
  intro hAll
  exact hNo hAll.1

/-- If all receipts are supplied, the oobleck route can promote at the gate layer. -/
theorem oobleck_gate_promotes_with_all_receipts
    (r : OobleckTransferReceipts) :
    r.phonon_density →
    r.lagrangian_transfer →
    r.orientation_shear →
    r.chiral_correlation →
    r.dielectric_nonlinearity →
    r.power_law_density →
    OobleckGate r = GateScope.V_scope := by
  intro hP hL hO hC hE hD
  simp [OobleckGate, OobleckClosed, hP, hL, hO, hC, hE, hD]

end SidonAudit
