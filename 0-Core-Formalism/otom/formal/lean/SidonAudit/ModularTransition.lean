import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

namespace SidonAudit

structure Claim where
  statement : Prop

structure ClosureReceipts (c : Claim) where
  construction_receipt : Prop
  nesting_receipt : Prop
  density_receipt : Prop

inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

def HasAllClosureReceipts {c : Claim} (r : ClosureReceipts c) : Prop :=
  r.construction_receipt ∧ r.nesting_receipt ∧ r.density_receipt

def Gate {c : Claim} (r : ClosureReceipts c) : GateScope :=
  if HasAllClosureReceipts r then GateScope.V_scope else GateScope.U_scope

theorem promote_to_V_scope {c : Claim} (r : ClosureReceipts c) :
    r.construction_receipt →
    r.nesting_receipt →
    r.density_receipt →
    Gate r = GateScope.V_scope := by
  intro hC hN hD
  simp [Gate, HasAllClosureReceipts, hC, hN, hD]

theorem remain_U_scope_without_density {c : Claim} (r : ClosureReceipts c) :
    ¬ r.density_receipt →
    Gate r = GateScope.U_scope := by
  intro hD
  simp [Gate, HasAllClosureReceipts]
  intro hAll
  exact hD hAll.2.2

theorem committedAudit_notVerifiedTheorem {c : Claim} (r : ClosureReceipts c) :
    ¬ HasAllClosureReceipts r →
    Gate r = GateScope.U_scope := by
  intro hMissing
  simp [Gate, hMissing]

def SquaredDensityOneReceipt (cardB M : ℕ) : Prop :=
  M ≤ cardB ^ 2

theorem noCarry_forces_square_density_below_one
    (q M maxB cardB : ℕ)
    (hq : 0 < q)
    (hmax : maxB = q ^ 2 + q)
    (hcard : cardB = q + 1)
    (hNoCarry : 2 * maxB < M) :
    ¬ SquaredDensityOneReceipt cardB M := by
  intro hDensity
  subst maxB
  subst cardB
  have hStrict : (q + 1) ^ 2 < M := by
    nlinarith [hNoCarry, hq]
  exact not_lt_of_ge hDensity hStrict

theorem noCarry_densityReceipt_incompatible
    (q M : ℕ)
    (hq : 0 < q)
    (hNoCarry : 2 * (q ^ 2 + q) < M) :
    ¬ SquaredDensityOneReceipt (q + 1) M := by
  exact noCarry_forces_square_density_below_one q M (q ^ 2 + q) (q + 1)
    hq rfl rfl hNoCarry

structure ModularSidonSeed where
  q : ℕ
  M : ℕ
  cardB : ℕ
  is_dense_base : M = q ^ 2 + q + 1
  card_eq : cardB = q + 1
  modular_uniqueness : Prop

theorem modular_base_clears_squared_density_threshold
    (seed : ModularSidonSeed)
    (hq : 0 < seed.q) :
    SquaredDensityOneReceipt seed.cardB seed.M := by
  rw [SquaredDensityOneReceipt]
  rw [seed.is_dense_base, seed.card_eq]
  nlinarith [hq]

theorem modular_route_requires_uniqueness_receipt
    (seed : ModularSidonSeed) :
    ¬ seed.modular_uniqueness →
    ¬ (seed.modular_uniqueness ∧ SquaredDensityOneReceipt seed.cardB seed.M) := by
  intro hNo hBoth
  exact hNo hBoth.1

theorem modular_route_receipts_package
    (seed : ModularSidonSeed)
    (hq : 0 < seed.q)
    (hUnique : seed.modular_uniqueness) :
    seed.modular_uniqueness ∧ SquaredDensityOneReceipt seed.cardB seed.M := by
  exact ⟨hUnique, modular_base_clears_squared_density_threshold seed hq⟩

/-!
The next obstruction is stronger than the carry issue: a Cartesian digit product
can fail to be Sidon even when every digit-position pair-sum is locally unique.
The swaps can vary independently by digit.
-/

theorem twoDigit_product_collision (M : ℕ) (hM : 1 < M) :
    let a := 0
    let b := M + 1
    let c := M
    let d := 1
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp
  constructor
  · omega
  · intro h
    rcases h with h | h
    · omega
    · omega

/--
General form of the digit-product collision. Any two distinct digits `u` and `v`
produce the crossed-pair collision

`[u,u] + [v,v] = [u,v] + [v,u]`.

Thus the full Cartesian digit product cannot be Sidon as soon as the digit
alphabet has two distinct symbols. Local unordered-pair recovery in each column
is insufficient because the orientation may flip independently by column.
-/
theorem twoDigit_product_collision_any_two_digits
    (M u v : ℕ)
    (hM : 0 < M)
    (hne : u ≠ v) :
    let a := u + u * M
    let b := v + v * M
    let c := u + v * M
    let d := v + u * M
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp
  constructor
  · omega
  · intro h
    rcases h with h | h
    · exact hne (Nat.eq_of_mul_eq_mul_right hM h.1)
    · exact hne h.1

/-- Two-digit parabolic/checksum embedding used by the phonon-lock proposal. -/
def twoDigitParabolicValue (M x y : ℕ) : ℕ :=
  x + y * M + (x ^ 2 + y ^ 2) * M ^ 2

/--
The quadratic checksum `x^2 + y^2` still does not break the crossed-pair
collision. The two-digit parabolic slice contains

`phi(0,0) + phi(1,1) = phi(0,1) + phi(1,0)`.

So a single global quadratic checksum is not a Sidon receipt for the full digit
space. It leaves the gate in `U_scope` unless a stronger orientation/global
pairing code is supplied.
-/
theorem twoDigit_parabolic_checksum_collision (M : ℕ) (hM : 0 < M) :
    let a := twoDigitParabolicValue M 0 0
    let b := twoDigitParabolicValue M 1 1
    let c := twoDigitParabolicValue M 0 1
    let d := twoDigitParabolicValue M 1 0
    a + b = c + d ∧ ¬ ((a = c ∧ b = d) ∨ (a = d ∧ b = c)) := by
  dsimp [twoDigitParabolicValue]
  constructor
  · ring_nf
  · intro h
    rcases h with h | h
    · have hpos : 0 < M + M ^ 2 := by nlinarith [hM]
      nlinarith [h.1, hpos]
    · have h1 : M + M ^ 2 = 0 := by nlinarith [h.2]
      have hpos : 0 < M + M ^ 2 := by nlinarith [hM]
      nlinarith [h1, hpos]

/--
Local modular uniqueness is not enough. A promoted modular route must also prove
that digitwise pair recovery has a globally consistent pairing across all digit
positions.
-/
structure GlobalPairingReceipt where
  statement : Prop

/-- A stronger receipt for breaking crossed-pair symmetries. -/
structure OrientationCodeReceipt where
  statement : Prop

structure StrongModularSidonSeed extends ModularSidonSeed where
  global_pairing_consistency : Prop
  orientation_code : Prop

theorem strong_modular_route_requires_global_pairing
    (seed : StrongModularSidonSeed) :
    ¬ seed.global_pairing_consistency →
    ¬ (seed.modular_uniqueness ∧ seed.global_pairing_consistency ∧
       SquaredDensityOneReceipt seed.cardB seed.M) := by
  intro hNo hAll
  exact hNo hAll.2.1

theorem parabolic_route_requires_orientation_code
    (seed : StrongModularSidonSeed) :
    ¬ seed.orientation_code →
    ¬ (seed.modular_uniqueness ∧ seed.global_pairing_consistency ∧
       seed.orientation_code ∧ SquaredDensityOneReceipt seed.cardB seed.M) := by
  intro hNo hAll
  exact hNo hAll.2.2.1

end SidonAudit
