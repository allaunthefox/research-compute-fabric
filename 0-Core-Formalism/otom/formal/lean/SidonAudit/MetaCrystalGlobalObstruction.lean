import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Meta-Crystal Global Obstruction

This module prevents overpromotion of the meta-crystalline stress-transfer model.

The local two-mode theorem is valuable: a positive contact term can distinguish
`(0,0)+(1,1)` from `(0,1)+(1,0)`. However, local crossing removal does not imply
global Sidon uniqueness.

The key obstruction is separability. If the meta-crystal is assembled from
independent local cells, then whole-cell swaps produce equal global sums even
when each local cell has its own nonlinear stress response.

Therefore a `GlobalSidonReceipt` must prove a non-separable global coupling or
an explicit admissibility restriction. A local chiral contact term is not enough.
-/

namespace SidonAudit

/-- Gate status for this audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/--
A two-mode meta-crystalline local cell.

This matches the positive part of the previous audit layer: charge terms,
phonon accumulation, and stress contact all live in one local energy cell.
-/
def localMetaCrystalCell
    (rhoX rhoY kappa tau x y : ℕ) : ℕ :=
  (rhoX * x ^ 2 + rhoY * y ^ 2) ^ 2 + kappa * (x ^ 2 + y ^ 2) + tau * x * y

/--
A four-mode structure made from two independent meta-crystalline cells.

This models the failure mode where the material is meta-crystalline locally but
still separable into independent stress-transfer blocks. The high-order base
slots record the local cell energies separately.
-/
def separableTwoCellMetaCrystalEnergy
    (M rhoX rhoY kappa tau a b c d : ℕ) : ℕ :=
  a + b * M + c * M ^ 2 + d * M ^ 3 +
    localMetaCrystalCell rhoX rhoY kappa tau a b * M ^ 4 +
    localMetaCrystalCell rhoX rhoY kappa tau c d * M ^ 5

/--
Local meta-crystal cells do not imply global Sidon uniqueness if the global
structure is separable.

The unordered pairs

`{(1,1,0,0), (0,0,1,1)}` and `{(1,1,1,1), (0,0,0,0)}`

have the same linear digit sum and the same multiset of independent cell
energies. This is a whole-cell swap, not the basic two-mode crossing.
-/
theorem separable_metaCrystal_cell_swap_collision
    (M rhoX rhoY kappa tau : ℕ) (hM : 1 < M) :
    let p := separableTwoCellMetaCrystalEnergy M rhoX rhoY kappa tau 1 1 0 0
    let q := separableTwoCellMetaCrystalEnergy M rhoX rhoY kappa tau 0 0 1 1
    let r := separableTwoCellMetaCrystalEnergy M rhoX rhoY kappa tau 1 1 1 1
    let s := separableTwoCellMetaCrystalEnergy M rhoX rhoY kappa tau 0 0 0 0
    p + q = r + s ∧ ¬ ((p = r ∧ q = s) ∨ (p = s ∧ q = r)) := by
  dsimp [separableTwoCellMetaCrystalEnergy, localMetaCrystalCell]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpos : 0 < M ^ 2 + M ^ 3 +
          ((rhoX + rhoY) ^ 2 + 2 * kappa + tau) * M ^ 5 := by
        nlinarith [hM]
      nlinarith [h.1, hpos]
    · have hpos : 0 < 1 + M +
          ((rhoX + rhoY) ^ 2 + 2 * kappa + tau) * M ^ 4 := by
        nlinarith [hM]
      nlinarith [h.1, hpos]

/-- Local crossing removal is a receipt, but not the global theorem. -/
structure LocalCrossingReceipt where
  statement : Prop

/-- Global coupling must prove that independent cell swaps cannot occur. -/
structure NonseparableGlobalCouplingReceipt where
  statement : Prop

/-- A full global Sidon audit must prove all pair sums are unique. -/
structure GlobalSidonReceipt where
  statement : Prop

/-- Density must still be proven after adding global coupling. -/
structure PowerLawDensityReceipt where
  statement : Prop

/-- Receipt package for the corrected meta-crystal route. -/
structure MetaCrystalGlobalReceipts where
  local_crossing : Prop
  nonseparable_global_coupling : Prop
  global_sidon : Prop
  power_law_density : Prop

/-- Closure requires nonseparability, global uniqueness, and density. -/
def MetaCrystalGlobalClosed (r : MetaCrystalGlobalReceipts) : Prop :=
  r.local_crossing ∧ r.nonseparable_global_coupling ∧ r.global_sidon ∧ r.power_law_density

/-- Gate for the corrected global meta-crystal route. -/
def MetaCrystalGlobalGate (r : MetaCrystalGlobalReceipts) : GateScope :=
  if MetaCrystalGlobalClosed r then GateScope.V_scope else GateScope.U_scope

/-- Missing non-separable global coupling keeps the route unverified. -/
theorem metaCrystal_global_gate_U_without_nonseparable_coupling
    (r : MetaCrystalGlobalReceipts) :
    ¬ r.nonseparable_global_coupling → MetaCrystalGlobalGate r = GateScope.U_scope := by
  intro hNo
  simp [MetaCrystalGlobalGate, MetaCrystalGlobalClosed]
  intro hAll
  exact hNo hAll.2.1

/-- Missing global Sidon audit keeps the route unverified. -/
theorem metaCrystal_global_gate_U_without_global_sidon
    (r : MetaCrystalGlobalReceipts) :
    ¬ r.global_sidon → MetaCrystalGlobalGate r = GateScope.U_scope := by
  intro hNo
  simp [MetaCrystalGlobalGate, MetaCrystalGlobalClosed]
  intro hAll
  exact hNo hAll.2.2.1

/-- Missing density receipt keeps the route unverified. -/
theorem metaCrystal_global_gate_U_without_power_law_density
    (r : MetaCrystalGlobalReceipts) :
    ¬ r.power_law_density → MetaCrystalGlobalGate r = GateScope.U_scope := by
  intro hNo
  simp [MetaCrystalGlobalGate, MetaCrystalGlobalClosed]
  intro hAll
  exact hNo hAll.2.2.2

/-- All receipts promote only at the audit-gate layer. -/
theorem metaCrystal_global_gate_promotes_with_all_receipts
    (r : MetaCrystalGlobalReceipts) :
    r.local_crossing →
    r.nonseparable_global_coupling →
    r.global_sidon →
    r.power_law_density →
    MetaCrystalGlobalGate r = GateScope.V_scope := by
  intro hL hN hG hD
  simp [MetaCrystalGlobalGate, MetaCrystalGlobalClosed, hL, hN, hG, hD]

end SidonAudit
