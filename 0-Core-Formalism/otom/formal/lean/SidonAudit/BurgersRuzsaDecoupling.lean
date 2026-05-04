import Mathlib.Data.Nat.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Tactic

/-!
# Sidon Audit: Burgers-Ruzsa Decoupling

This module records the corrected audit boundary:

* the Burgers shock layer is a selector / clock / alignment gate;
* the Sidon property must be supplied by a non-separable algebraic encoding;
* a Ruzsa/Lindstrom/Bose-Chowla style primitive-root construction is the right
  arithmetic lock candidate;
* local stress-contact terms and Burgers transport do not prove the global B₂
  condition by themselves.

Important correction:

The naive integer base-shift encoding

`Phi i = i * M + (g^i mod p)`

can separate the index-sum layer from the residue layer when `M > 2p`, and the
standard primitive-root argument then gives a finite Sidon receipt. However, this
base separation costs a constant density factor: with `M ≳ 2p`, a block of about
`p` elements lives at scale about `2p^2`, so it does not by itself certify the
optimal `sigma = 1` constant.

For the optimal density receipt, the compact modular Ruzsa construction, CRT
packing, or a Bose-Chowla finite-field construction must replace the naive
base-shift layer.
-/

namespace SidonAudit

/-- Gate status for the audit layer. -/
inductive GateScope where
  | U_scope
  | V_scope
deriving DecidableEq, Repr

/-- A Burgers alignment gate is a Boolean selector over candidate indices. -/
def BurgersGate := ℕ → Prop

/-- A candidate index is active when the Burgers selector admits it. -/
def ActiveIndex (gate : BurgersGate) (i : ℕ) : Prop :=
  gate i

/-- Pair-sum injectivity of an encoding map: the Sidon/B₂ condition. -/
def PairSumInjective (Phi : ℕ → ℕ) : Prop :=
  ∀ a b c d : ℕ,
    Phi a + Phi b = Phi c + Phi d →
      (a = c ∧ b = d) ∨ (a = d ∧ b = c)

/-- Pair-sum injectivity restricted to active Burgers-selected indices. -/
def PairSumInjectiveOnGate (gate : BurgersGate) (Phi : ℕ → ℕ) : Prop :=
  ∀ a b c d : ℕ,
    ActiveIndex gate a → ActiveIndex gate b →
    ActiveIndex gate c → ActiveIndex gate d →
    Phi a + Phi b = Phi c + Phi d →
      (a = c ∧ b = d) ∨ (a = d ∧ b = c)

/-- Global pair-sum injectivity immediately restricts to any Burgers gate. -/
theorem pairSumInjective_restricts_to_gate
    (gate : BurgersGate) (Phi : ℕ → ℕ)
    (hPhi : PairSumInjective Phi) :
    PairSumInjectiveOnGate gate Phi := by
  intro a b c d _ _ _ _ hsum
  exact hPhi a b c d hsum

/--
The Burgers layer can only supply an active index set. It is not itself a Sidon
receipt unless paired with pair-sum injectivity of the encoding.
-/
structure BurgersSelectorReceipt where
  gate : BurgersGate
  shock_kernel_valid : Prop
  finite_or_controlled_window : Prop

/--
A non-separable algebraic encoding receipt. The actual theorem-level content is
pair-sum injectivity, not geometric convexity or local collision blocking.
-/
structure NonseparableEncodingReceipt where
  Phi : ℕ → ℕ
  pair_sum_injective : PairSumInjective Phi

/--
A compact packing receipt is needed for the optimal square-root density constant.
Naive base separation may be Sidon but can lose the `sigma = 1` constant.
-/
structure CompactDensityReceipt where
  sigma_eq_one : Prop

/-- Full Burgers-Ruzsa receipt package. -/
structure BurgersRuzsaReceipts where
  burgers_selector : Prop
  nonseparable_encoding : Prop
  pair_sum_injective : Prop
  compact_density : Prop

/-- Closure requires selector, algebraic encoding, pair-sum injectivity, and density. -/
def BurgersRuzsaClosed (r : BurgersRuzsaReceipts) : Prop :=
  r.burgers_selector ∧ r.nonseparable_encoding ∧
    r.pair_sum_injective ∧ r.compact_density

/-- Gate for the Burgers-Ruzsa route. -/
def BurgersRuzsaGate (r : BurgersRuzsaReceipts) : GateScope :=
  if BurgersRuzsaClosed r then GateScope.V_scope else GateScope.U_scope

/-- Missing non-separable encoding keeps the route unverified. -/
theorem burgersRuzsa_gate_U_without_nonseparable_encoding
    (r : BurgersRuzsaReceipts) :
    ¬ r.nonseparable_encoding → BurgersRuzsaGate r = GateScope.U_scope := by
  intro hNo
  simp [BurgersRuzsaGate, BurgersRuzsaClosed]
  intro hAll
  exact hNo hAll.2.1

/-- Missing pair-sum injectivity keeps the route unverified. -/
theorem burgersRuzsa_gate_U_without_pair_sum_injective
    (r : BurgersRuzsaReceipts) :
    ¬ r.pair_sum_injective → BurgersRuzsaGate r = GateScope.U_scope := by
  intro hNo
  simp [BurgersRuzsaGate, BurgersRuzsaClosed]
  intro hAll
  exact hNo hAll.2.2.1

/-- Missing compact density keeps the route unverified. -/
theorem burgersRuzsa_gate_U_without_compact_density
    (r : BurgersRuzsaReceipts) :
    ¬ r.compact_density → BurgersRuzsaGate r = GateScope.U_scope := by
  intro hNo
  simp [BurgersRuzsaGate, BurgersRuzsaClosed]
  intro hAll
  exact hNo hAll.2.2.2

/-- All receipts promote only at the audit-gate layer. -/
theorem burgersRuzsa_gate_promotes_with_all_receipts
    (r : BurgersRuzsaReceipts) :
    r.burgers_selector →
    r.nonseparable_encoding →
    r.pair_sum_injective →
    r.compact_density →
    BurgersRuzsaGate r = GateScope.V_scope := by
  intro hB hN hP hD
  simp [BurgersRuzsaGate, BurgersRuzsaClosed, hB, hN, hP, hD]

/--
A local theorem schema: if a Ruzsa-style primitive-root encoding is proved
pair-sum-injective globally, then any Burgers-selected active subset inherits
the Sidon property.
-/
theorem burgers_selected_subset_is_sidon_when_encoding_is_sidon
    (gate : BurgersGate) (Phi : ℕ → ℕ)
    (hPhi : PairSumInjective Phi) :
    PairSumInjectiveOnGate gate Phi := by
  exact pairSumInjective_restricts_to_gate gate Phi hPhi

end SidonAudit
