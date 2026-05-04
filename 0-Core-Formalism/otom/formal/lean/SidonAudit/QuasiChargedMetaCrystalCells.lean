import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Quasi-Charged Meta-Crystal Cells

This module records the refined ontology:

* a cell is not a literal electromagnetic particle;
* `quasi_charge` is the local activation / permittivity-like state of a
  meta-crystalline cell;
* `phonon_load` is accumulated mode energy before a transfer event;
* `transfer_index` is the discrete Lagrangian lattice site where a regime
  transition is represented;
* `contact_coupling` is the stress-induced interaction term that can distinguish
  co-activation from separated activation.

The audit distinction remains important: this ontology explains the mechanism,
but the number-theoretic theorem still requires non-separable global coupling,
global Sidon uniqueness, and power-law density receipts.
-/

namespace SidonAudit

/-- Gate status for this audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/--
A quasi-charged meta-crystal cell.

The fields are intentionally discrete because this audit is tracking an integer
construction, not a continuum material simulation.
-/
structure QuasiChargedCell where
  quasi_charge : ℕ
  phonon_load : ℕ
  transfer_index : ℕ
  contact_coupling : ℕ

/-- A cell is active when it has nonzero quasi-charge. -/
def CellActive (c : QuasiChargedCell) : Prop :=
  0 < c.quasi_charge

/-- A cell has stored phonon energy when its load is nonzero. -/
def HasPhononAccumulation (c : QuasiChargedCell) : Prop :=
  0 < c.phonon_load

/-- A cell has a stress-contact response when its coupling coefficient is nonzero. -/
def HasStressContact (c : QuasiChargedCell) : Prop :=
  0 < c.contact_coupling

/--
Cell-level activation package: charge, phonon accumulation, and contact response
are all present locally.
-/
def CellMechanismReady (c : QuasiChargedCell) : Prop :=
  CellActive c ∧ HasPhononAccumulation c ∧ HasStressContact c

/-- If contact coupling is absent, the cell mechanism is not ready. -/
theorem cell_not_ready_without_contact
    (c : QuasiChargedCell) :
    ¬ HasStressContact c → ¬ CellMechanismReady c := by
  intro hNo hReady
  exact hNo hReady.2.2

/-- If quasi-charge is absent, the cell mechanism is not ready. -/
theorem cell_not_ready_without_charge
    (c : QuasiChargedCell) :
    ¬ CellActive c → ¬ CellMechanismReady c := by
  intro hNo hReady
  exact hNo hReady.1

/-- If phonon accumulation is absent, the cell mechanism is not ready. -/
theorem cell_not_ready_without_phonon_load
    (c : QuasiChargedCell) :
    ¬ HasPhononAccumulation c → ¬ CellMechanismReady c := by
  intro hNo hReady
  exact hNo hReady.2.1

/--
A local cell pair with a cross-contact term. This is the two-cell analogue of a
stress-induced metamaterial interaction.
-/
def cellPairContactEnergy (a b : QuasiChargedCell) : ℕ :=
  a.quasi_charge * b.quasi_charge +
  a.phonon_load + b.phonon_load +
  a.contact_coupling * b.contact_coupling

/--
Positive charge and positive contact in both cells force a positive interaction
energy. This is a local mechanism sanity check, not global Sidon uniqueness.
-/
theorem positive_cells_have_positive_contact_energy
    (a b : QuasiChargedCell)
    (haQ : 0 < a.quasi_charge) (hbQ : 0 < b.quasi_charge)
    (haC : 0 < a.contact_coupling) (hbC : 0 < b.contact_coupling) :
    0 < cellPairContactEnergy a b := by
  dsimp [cellPairContactEnergy]
  nlinarith [haQ, hbQ, haC, hbC]

/-- Receipt package for promoting the quasi-charged cell ontology into theorem use. -/
structure QuasiChargedCellReceipts where
  local_cell_mechanism : Prop
  nonseparable_global_coupling : Prop
  global_sidon : Prop
  power_law_density : Prop

/-- Closure requires local mechanism plus global nonseparability, uniqueness, and density. -/
def QuasiChargedCellClosed (r : QuasiChargedCellReceipts) : Prop :=
  r.local_cell_mechanism ∧ r.nonseparable_global_coupling ∧ r.global_sidon ∧ r.power_law_density

/-- Gate for the quasi-charged meta-crystal cell route. -/
def QuasiChargedCellGate (r : QuasiChargedCellReceipts) : GateScope :=
  if QuasiChargedCellClosed r then GateScope.V_scope else GateScope.U_scope

/-- Missing non-separable global coupling keeps the route in `U_scope`. -/
theorem quasiCharged_gate_U_without_nonseparable_coupling
    (r : QuasiChargedCellReceipts) :
    ¬ r.nonseparable_global_coupling → QuasiChargedCellGate r = GateScope.U_scope := by
  intro hNo
  simp [QuasiChargedCellGate, QuasiChargedCellClosed]
  intro hAll
  exact hNo hAll.2.1

/-- Missing global Sidon audit keeps the route in `U_scope`. -/
theorem quasiCharged_gate_U_without_global_sidon
    (r : QuasiChargedCellReceipts) :
    ¬ r.global_sidon → QuasiChargedCellGate r = GateScope.U_scope := by
  intro hNo
  simp [QuasiChargedCellGate, QuasiChargedCellClosed]
  intro hAll
  exact hNo hAll.2.2.1

/-- Missing density receipt keeps the route in `U_scope`. -/
theorem quasiCharged_gate_U_without_power_law_density
    (r : QuasiChargedCellReceipts) :
    ¬ r.power_law_density → QuasiChargedCellGate r = GateScope.U_scope := by
  intro hNo
  simp [QuasiChargedCellGate, QuasiChargedCellClosed]
  intro hAll
  exact hNo hAll.2.2.2

/-- All receipts promote only at the audit-gate layer. -/
theorem quasiCharged_gate_promotes_with_all_receipts
    (r : QuasiChargedCellReceipts) :
    r.local_cell_mechanism →
    r.nonseparable_global_coupling →
    r.global_sidon →
    r.power_law_density →
    QuasiChargedCellGate r = GateScope.V_scope := by
  intro hL hN hG hD
  simp [QuasiChargedCellGate, QuasiChargedCellClosed, hL, hN, hG, hD]

end SidonAudit
