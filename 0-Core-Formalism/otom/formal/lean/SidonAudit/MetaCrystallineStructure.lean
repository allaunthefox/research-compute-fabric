import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Meta-Crystalline Stress Transfer

This module packages the refined interpretation:

* charge = local activation / material state of a meta-crystalline cell;
* phonon accumulation = mode energy accumulated in the cell before transfer;
* transfer points = discrete Lagrangian lattice locations where the structure
  changes regime;
* stress-induced metamaterial response = correlation-bearing contact term that
  can distinguish co-activation from separated activation.

The module proves only a local sanity check: a contact/correlation term blocks
the basic crossed-pair collision. It does **not** prove global Sidon uniqueness
or the square-root density target.
-/

namespace SidonAudit

/-- Gate status for this audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/--
Meta-crystalline two-mode energy.

Parameters:

* `M`: base separating transfer layers;
* `rhoX`, `rhoY`: local charge / activation state at each crystalline site;
* `kappa`: phonon accumulation coefficient;
* `tau`: stress-induced contact coefficient.

The `tau * x * y` term is the chiral/contact term: it activates only under
co-activation of the two modes, modeling stress-induced crystallization.
-/
def twoModeMetaCrystalEnergy
    (M rhoX rhoY kappa tau x y : ℕ) : ℕ :=
  x + y * M +
    ((rhoX * x ^ 2 + rhoY * y ^ 2) ^ 2 + kappa * (x ^ 2 + y ^ 2) + tau * x * y) * M ^ 2

/--
The stress-induced meta-crystalline contact term blocks the basic crossed-pair
collision locally.

This theorem captures the minimum useful audit result: if the material has a
positive contact coefficient, then co-activation `(1,1)` is not energetically
identical to separated activation `(0,1)+(1,0)`.
-/
theorem metaCrystal_contact_breaks_basic_crossing
    (M rhoX rhoY kappa tau : ℕ)
    (hM : 0 < M) (hX : 0 < rhoX) (hY : 0 < rhoY) (hTau : 0 < tau) :
    let a := twoModeMetaCrystalEnergy M rhoX rhoY kappa tau 0 0
    let b := twoModeMetaCrystalEnergy M rhoX rhoY kappa tau 1 1
    let c := twoModeMetaCrystalEnergy M rhoX rhoY kappa tau 0 1
    let d := twoModeMetaCrystalEnergy M rhoX rhoY kappa tau 1 0
    a + b ≠ c + d := by
  dsimp [twoModeMetaCrystalEnergy]
  intro h
  have hpos : 0 < (2 * rhoX * rhoY + tau) * M ^ 2 := by
    nlinarith [hM, hX, hY, hTau]
  nlinarith [h, hpos]

/-- Charge receipt: local site activation is represented as a state variable. -/
structure ChargeReceipt where
  statement : Prop

/-- Phonon receipt: mode accumulation before transfer is represented. -/
structure PhononAccumulationReceipt where
  statement : Prop

/-- Transfer receipt: exact Lagrangian transfer points are represented. -/
structure TransferPointReceipt where
  statement : Prop

/-- Meta-crystal receipt: the material regime is cell-structured and stress-induced. -/
structure MetaCrystallineReceipt where
  statement : Prop

/-- Chiral contact receipt: co-activation and separated activation are distinguished. -/
structure ChiralContactReceipt where
  statement : Prop

/-- Global uniqueness receipt: all admissible pair sums are audited. -/
structure GlobalSidonReceipt where
  statement : Prop

/-- Density receipt: the additional meta-crystal structure preserves the target law. -/
structure PowerLawDensityReceipt where
  statement : Prop

/-- Full receipt package for the meta-crystalline route. -/
structure MetaCrystalReceipts where
  charge : Prop
  phonon_accumulation : Prop
  transfer_points : Prop
  meta_crystalline : Prop
  chiral_contact : Prop
  global_sidon : Prop
  power_law_density : Prop

/-- Closure requires all semantic and mathematical receipts. -/
def MetaCrystalClosed (r : MetaCrystalReceipts) : Prop :=
  r.charge ∧ r.phonon_accumulation ∧ r.transfer_points ∧ r.meta_crystalline ∧
    r.chiral_contact ∧ r.global_sidon ∧ r.power_law_density

/-- Gate for the meta-crystalline route. -/
def MetaCrystalGate (r : MetaCrystalReceipts) : GateScope :=
  if MetaCrystalClosed r then GateScope.V_scope else GateScope.U_scope

/-- Missing chiral contact keeps the route in `U_scope`. -/
theorem metaCrystal_gate_U_without_chiral_contact
    (r : MetaCrystalReceipts) :
    ¬ r.chiral_contact → MetaCrystalGate r = GateScope.U_scope := by
  intro hNo
  simp [MetaCrystalGate, MetaCrystalClosed]
  intro hAll
  exact hNo hAll.2.2.2.2.1

/-- Missing global Sidon audit keeps the route in `U_scope`. -/
theorem metaCrystal_gate_U_without_global_sidon
    (r : MetaCrystalReceipts) :
    ¬ r.global_sidon → MetaCrystalGate r = GateScope.U_scope := by
  intro hNo
  simp [MetaCrystalGate, MetaCrystalClosed]
  intro hAll
  exact hNo hAll.2.2.2.2.2.1

/-- Missing power-law density keeps the route in `U_scope`. -/
theorem metaCrystal_gate_U_without_power_law_density
    (r : MetaCrystalReceipts) :
    ¬ r.power_law_density → MetaCrystalGate r = GateScope.U_scope := by
  intro hNo
  simp [MetaCrystalGate, MetaCrystalClosed]
  intro hAll
  exact hNo hAll.2.2.2.2.2.2

/-- All receipts promote only at the audit-gate layer. -/
theorem metaCrystal_gate_promotes_with_all_receipts
    (r : MetaCrystalReceipts) :
    r.charge →
    r.phonon_accumulation →
    r.transfer_points →
    r.meta_crystalline →
    r.chiral_contact →
    r.global_sidon →
    r.power_law_density →
    MetaCrystalGate r = GateScope.V_scope := by
  intro hC hP hT hM hCh hG hD
  simp [MetaCrystalGate, MetaCrystalClosed, hC, hP, hT, hM, hCh, hG, hD]

end SidonAudit
