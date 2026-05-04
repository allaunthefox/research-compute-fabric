import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Body-Vest Disproof Layer

This module tests the nonlinear body-vest / dielectric dampening claim.

The important correction is:

* a nonlinear scalar shell can break the basic two-mode crossed pair;
* but nonlinear dampening alone does **not** prove global Sidon uniqueness;
* an isotropic nonlinear shell still has higher-dimensional radial collisions;
* a successful repair needs a chiral/correlation-bearing weave plus a power-law
  density receipt.

The module intentionally does not prove `sigma = 1`.
-/

namespace SidonAudit

/-- Gate status for the audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/--
Four-mode nonlinear body-vest shell.

The first four base-`M` slots carry the information digits. The high slot carries
an isotropic nonlinear dampening shell:

`(a^2 + b^2 + c^2 + d^2)^2`.

This is deliberately radial/isotropic.
-/
def fourModeNonlinearShellEnergy
    (M a b c d : ℕ) : ℕ :=
  a + b * M + c * M ^ 2 + d * M ^ 3 +
    (a ^ 2 + b ^ 2 + c ^ 2 + d ^ 2) ^ 2 * M ^ 4

/--
A concrete radial collision for the nonlinear body-vest shell.

The two unordered pairs

`{(1,2,0,0), (0,0,1,2)}` and `{(1,0,0,2), (0,2,1,0)}`

have the same digitwise linear sum and the same isotropic shell value.
Thus the nonlinear shell does not by itself provide a global Sidon receipt.
-/
theorem isotropic_bodyVest_shell_collision
    (M : ℕ) (hM : 1 < M) :
    let a := fourModeNonlinearShellEnergy M 1 2 0 0
    let b := fourModeNonlinearShellEnergy M 0 0 1 2
    let c := fourModeNonlinearShellEnergy M 1 0 0 2
    let d := fourModeNonlinearShellEnergy M 0 2 1 0
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp [fourModeNonlinearShellEnergy]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpow : M < M ^ 3 := by nlinarith [hM]
      nlinarith [h.1, hpow]
    · have hsq : 1 < M ^ 2 := by nlinarith [hM]
      nlinarith [h.1, hsq]

/-- Nonlinear dampening is a local mechanism, not a theorem receipt by itself. -/
structure NonlinearDampeningReceipt where
  statement : Prop

/-- Chiral armor means the internal weave encodes coordinate correlation/orientation. -/
structure ChiralArmorReceipt where
  statement : Prop

/-- A global Sidon audit receipt: all pair sums are globally unique. -/
structure GlobalSidonReceipt where
  statement : Prop

/-- The density receipt: the extra armor does not destroy the asymptotic target. -/
structure PowerLawDensityReceipt where
  statement : Prop

/-- Full body-vest receipt package. -/
structure BodyVestReceipts where
  nonlinear_dampening : Prop
  chiral_armor : Prop
  global_sidon : Prop
  power_law_density : Prop

/-- Closure requires nonlinear dampening, chirality, global Sidon audit, and density. -/
def BodyVestClosed (r : BodyVestReceipts) : Prop :=
  r.nonlinear_dampening ∧ r.chiral_armor ∧ r.global_sidon ∧ r.power_law_density

/-- Gate for the body-vest route. -/
def BodyVestGate (r : BodyVestReceipts) : GateScope :=
  if BodyVestClosed r then GateScope.V_scope else GateScope.U_scope

/-- Missing chiral armor keeps the route in `U_scope`. -/
theorem bodyVest_gate_U_without_chiral_armor
    (r : BodyVestReceipts) :
    ¬ r.chiral_armor → BodyVestGate r = GateScope.U_scope := by
  intro hNo
  simp [BodyVestGate, BodyVestClosed]
  intro hAll
  exact hNo hAll.2.1

/-- Missing global Sidon audit keeps the route in `U_scope`. -/
theorem bodyVest_gate_U_without_global_sidon
    (r : BodyVestReceipts) :
    ¬ r.global_sidon → BodyVestGate r = GateScope.U_scope := by
  intro hNo
  simp [BodyVestGate, BodyVestClosed]
  intro hAll
  exact hNo hAll.2.2.1

/-- Missing power-law density keeps the route in `U_scope`. -/
theorem bodyVest_gate_U_without_power_law_density
    (r : BodyVestReceipts) :
    ¬ r.power_law_density → BodyVestGate r = GateScope.U_scope := by
  intro hNo
  simp [BodyVestGate, BodyVestClosed]
  intro hAll
  exact hNo hAll.2.2.2

/-- All receipts promote only at the audit-gate layer. -/
theorem bodyVest_gate_promotes_with_all_receipts
    (r : BodyVestReceipts) :
    r.nonlinear_dampening →
    r.chiral_armor →
    r.global_sidon →
    r.power_law_density →
    BodyVestGate r = GateScope.V_scope := by
  intro hN hC hG hD
  simp [BodyVestGate, BodyVestClosed, hN, hC, hG, hD]

end SidonAudit
