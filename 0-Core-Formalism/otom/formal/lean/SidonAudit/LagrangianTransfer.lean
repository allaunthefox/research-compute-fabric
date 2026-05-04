import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Lagrangian Transfer

This module formalizes the next audit correction:

* the Lagrangian / phonon-density language is useful as a diagnostic metaphor;
* a symmetric energy-gradient lock is not a Sidon receipt;
* a Hamiltonian of the form

  `E(x,y) = x + y*M + lambda*(x^2 + y^2)*M^2`

  still preserves the crossed-pair collision

  `E(0,0) + E(1,1) = E(0,1) + E(1,0)`.

Therefore the gate remains `U_scope` unless an orientation/correlation code is
supplied that is not symmetric under coordinate swap.
-/

namespace SidonAudit

/-- Gate status for the audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/--
Two-mode Lagrangian/phonon energy with a symmetric quadratic gradient lock.

The `lambda` parameter is the coupling strength of the quadratic lock. The
important point is that the lock is symmetric in the coordinates.
-/
def twoModeLagrangianEnergy (M lambda x y : ℕ) : ℕ :=
  x + y * M + lambda * (x ^ 2 + y ^ 2) * M ^ 2

/--
A symmetric Lagrangian lock does not break the crossed-pair collision.

For every positive base `M` and every coupling `lambda`, the states

`(0,0) + (1,1)` and `(0,1) + (1,0)`

have the same total energy, while the unordered pair of states is different.
This is the formal version of the phonon-density warning: a symmetric potential
changes the height of states but does not encode orientation.
-/
theorem symmetric_lagrangian_lock_collision
    (M lambda : ℕ) (hM : 0 < M) :
    let a := twoModeLagrangianEnergy M lambda 0 0
    let b := twoModeLagrangianEnergy M lambda 1 1
    let c := twoModeLagrangianEnergy M lambda 0 1
    let d := twoModeLagrangianEnergy M lambda 1 0
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp [twoModeLagrangianEnergy]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpos : 0 < M + lambda * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h.1, hpos]
    · have h1 : M + lambda * M ^ 2 = 0 := by
        nlinarith [h.2]
      have hpos : 0 < M + lambda * M ^ 2 := by
        nlinarith [hM]
      nlinarith [h1, hpos]

/-- A required receipt for any successful Lagrangian-transfer route. -/
structure OrientationGradientReceipt where
  statement : Prop

/-- A required receipt for showing that the orientation code does not destroy density. -/
structure PowerLawReceipt where
  statement : Prop

/-- A Lagrangian transfer route is not verified without orientation and power-law receipts. -/
structure LagrangianTransferReceipts where
  symmetric_energy_lock : Prop
  orientation_gradient : Prop
  power_law_density : Prop

/--
If the orientation-gradient receipt is absent, the Lagrangian transfer route
cannot be promoted. The symmetric lock alone is not enough.
-/
theorem lagrangian_route_requires_orientation_gradient
    (r : LagrangianTransferReceipts) :
    ¬ r.orientation_gradient →
    ¬ (r.symmetric_energy_lock ∧ r.orientation_gradient ∧ r.power_law_density) := by
  intro hNo hAll
  exact hNo hAll.2.1

/--
If the power-law density receipt is absent, even a symmetry-breaking orientation
code cannot promote the construction to a density theorem.
-/
theorem lagrangian_route_requires_power_law_density
    (r : LagrangianTransferReceipts) :
    ¬ r.power_law_density →
    ¬ (r.symmetric_energy_lock ∧ r.orientation_gradient ∧ r.power_law_density) := by
  intro hNo hAll
  exact hNo hAll.2.2

/--
A concise audit gate: all three receipts are required for `V_scope`.
The symmetric lock is explicitly treated as only one component.
-/
def LagrangianGate (r : LagrangianTransferReceipts) : GateScope :=
  if r.symmetric_energy_lock ∧ r.orientation_gradient ∧ r.power_law_density then
    GateScope.V_scope
  else
    GateScope.U_scope

/-- Missing orientation keeps the Lagrangian route in `U_scope`. -/
theorem lagrangian_gate_U_without_orientation
    (r : LagrangianTransferReceipts) :
    ¬ r.orientation_gradient →
    LagrangianGate r = GateScope.U_scope := by
  intro hNo
  simp [LagrangianGate]
  intro hAll
  exact hNo hAll.2.1

/-- Missing power-law density keeps the Lagrangian route in `U_scope`. -/
theorem lagrangian_gate_U_without_power_law
    (r : LagrangianTransferReceipts) :
    ¬ r.power_law_density →
    LagrangianGate r = GateScope.U_scope := by
  intro hNo
  simp [LagrangianGate]
  intro hAll
  exact hNo hAll.2.2

end SidonAudit
