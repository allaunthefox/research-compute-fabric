import Mathlib.Data.Set.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Semantics.SidonSet

/-!
# Sidon Sets — Singer Construction Infrastructure

Port of the reusable Sidon-set infrastructure from Hulak–Ramos–de Queiroz (2026),
"Formalizing Singer Sidon Constructions and Sidon Set Infrastructure in Lean 4"
(arXiv: 2605.03274).

Original Lean 4 source: https://github.com/d0d1/singer-theorem-lean
Commit: 0c890589afc58e8955a5d7c3a609daff6447da31
License: GPL-3.0-only

This module ports the key reusable definitions and theorem statements from the
Erdos30 development into the Semantics namespace. The heavy algebraic proofs
(Singer construction, Lindström inequality, unconditional bounds) are left as
`sorry` with `TODO(lean-port)` markers, since the original code targets
Mathlib v4.29.0 while this project uses v4.30.0-rc2.

## Reusable components ported

1. **IsSidon** — Finset ℤ Sidon predicate (compatible with paper's Erdos30.Sidon)
2. **IsSidonMod** — Modular Sidon predicate
3. **IsIntervalSidon** — Interval Sidon predicate with containment
4. **IsSidonMaximum / sidonMaximum** — Extremal function h(N)
5. **Singer construction** — sidon set mod p²+p+1 of size p+1
6. **Lindström's cross-difference inequality** — (m-k)·k ≤ N-1
7. **h(N) = Θ(√N) bounds** — unconditional two-sided bounds
8. **Erdos30Statement** — formal Erdős Problem 30

## Relationship to existing Semantics.SidonSet

The existing `Semantics.SidonSet` uses a greedy `List Nat` generator with a
computable `isSidon : List Nat → Prop` check. This module provides the
mathematically rigorous `Finset ℤ` version used in the paper's proofs.
Both coexist: the List Nat version for computation, the Finset ℤ version
for formal combinatorics.

## References

- Singer, J. (1938). A theorem in finite projective geometry and some applications.
  *Trans. Amer. Math. Soc.*, 43, 377–385.
- Lindström, B. (1969). An inequality for B₂-sequences.
  *J. Combin. Theory*, 6(2), 211–212.
- Erdős, P. (1976). Problems and results in combinatorial number theory.
  *Astérisque*, 24–25, 295–310. (Problem 30)
-/

namespace Semantics.SidonSets

open Finset

/-! ## Core Sidon Definitions (Finset ℤ) -/

/-- The Sidon property for a finite set of integers: all pairwise sums a + b
    (with a, b ∈ A) are distinct up to reordering. This is the standard
    combinatorial definition used in the Erdős Problem 30 literature. -/
def IsSidon (A : Finset ℤ) : Prop :=
  ∀ ⦃a b c d : ℤ⦄,
    a ∈ A → b ∈ A → c ∈ A → d ∈ A →
    a + b = c + d →
      (a = c ∧ b = d) ∨ (a = d ∧ b = c)

/-- The Sidon property for a list of natural numbers (computable version).
    Compatible with `Semantics.SidonSet.isSidon`. -/
def IsSidonNat (s : List Nat) : Prop :=
  Semantics.SidonSet.isSidon s

/-! ## Modular Sidon Sets -/

/-- `IsSidonMod M A` means A is Sidon modulo M: for any a, b, c, d ∈ A,
    M ∣ ((a + b) - (c + d)) implies {a, b} = {c, d} as unordered pairs.
    This is the form needed for Singer's construction, which produces
    Sidon sets in Z/(q²+q+1)Z. -/
def IsSidonMod (M : ℤ) (A : Finset ℤ) : Prop :=
  ∀ ⦃a b c d : ℤ⦄,
    a ∈ A → b ∈ A → c ∈ A → d ∈ A →
    (M ∣ ((a + b) - (c + d))) →
    (a = c ∧ b = d) ∨ (a = d ∧ b = c)

/-- Modular Sidon implies integer Sidon. -/
theorem IsSidonMod.toIsSidon {M : ℤ} {A : Finset ℤ} (h : IsSidonMod M A) :
    IsSidon A := by
  intro a b c d ha hb hc hd hsum
  exact h ha hb hc hd (by rw [hsum, sub_self]; exact dvd_zero M)

/-! ## Interval Sidon Sets -/

/-- The interval {1, ..., N} as a Finset ℤ. Empty when N < 1. -/
noncomputable def interval (N : ℤ) : Finset ℤ := Finset.Icc 1 N

/-- A Sidon subset of {1, ..., N}. -/
structure IsIntervalSidon (N : ℤ) (A : Finset ℤ) : Prop where
  subset : ∀ x ∈ A, 1 ≤ x ∧ x ≤ N
  sidon : IsSidon A

/-- Enlarging the ambient interval preserves IsIntervalSidon. -/
theorem IsIntervalSidon.mono {A : Finset ℤ} {N M : ℤ}
    (h : IsIntervalSidon N A) (hle : N ≤ M) : IsIntervalSidon M A where
  subset x hx := ⟨(h.subset x hx).1, le_trans (h.subset x hx).2 hle⟩
  sidon := h.sidon

/-! ## Translation -/

/-- Translate a finset by t. -/
def translate (A : Finset ℤ) (t : ℤ) : Finset ℤ :=
  A.map (⟨fun x => x + t, fun _ _ h => add_right_cancel h⟩ : ℤ ↪ ℤ)

@[simp] theorem card_translate (A : Finset ℤ) (t : ℤ) :
    (translate A t).card = A.card := by
  simp [translate]

/-- Translation preserves the Sidon property. -/
theorem IsSidon.translate {A : Finset ℤ} (hA : IsSidon A) (t : ℤ) :
    IsSidon (translate A t) := by
  intro a b c d ha hb hc hd hsum
  rcases Finset.mem_map.1 ha with ⟨a', ha', ha_eq⟩
  rcases Finset.mem_map.1 hb with ⟨b', hb', hb_eq⟩
  rcases Finset.mem_map.1 hc with ⟨c', hc', hc_eq⟩
  rcases Finset.mem_map.1 hd with ⟨d', hd', hd_eq⟩
  have ha_val : a' + t = a := by simpa using ha_eq
  have hb_val : b' + t = b := by simpa using hb_eq
  have hc_val : c' + t = c := by simpa using hc_eq
  have hd_val : d' + t = d := by simpa using hd_eq
  have hsum' : a' + b' = c' + d' := by
    calc
      a' + b' = (a' + t) + (b' + t) - (t + t) := by ring
      _ = a + b - (t + t) := by simp [ha_val, hb_val]
      _ = c + d - (t + t) := by rw [hsum]
      _ = (c' + t) + (d' + t) - (t + t) := by simp [hc_val, hd_val]
      _ = c' + d' := by ring
  rcases hA ha' hb' hc' hd' hsum' with (⟨hac, hbd⟩ | ⟨had, hbc⟩)
  · left
    constructor
    · calc
        a = a' + t := ha_val.symm
        _ = c' + t := by rw [hac]
        _ = c := hc_val
    · calc
        b = b' + t := hb_val.symm
        _ = d' + t := by rw [hbd]
        _ = d := hd_val
  · right
    constructor
    · calc
        a = a' + t := ha_val.symm
        _ = d' + t := by rw [had]
        _ = d := hd_val
    · calc
        b = b' + t := hb_val.symm
        _ = c' + t := by rw [hbc]
        _ = c := hc_val

/-! ## Extremal Function h(N) -/

/-- `IsSidonMaximum N h` states that h is the maximum cardinality of an
    interval Sidon subset of {1, ..., N}. -/
def IsSidonMaximum (N h : ℕ) : Prop :=
  (∃ A : Finset ℤ, IsIntervalSidon (N : ℤ) A ∧ A.card = h) ∧
    ∀ {A : Finset ℤ}, IsIntervalSidon (N : ℤ) A → A.card ≤ h

/-- Helper: the maximum Sidon cardinality exists for every N. -/
private theorem sidonMaximum_exists (N : ℕ) : ∃ h, IsSidonMaximum N h := by
  let Z := Finset.Icc 1 (N : ℤ)
  let cards : Set ℕ := {k | ∃ (A : Finset ℤ), A ⊆ Z ∧ IsSidon A ∧ A.card = k}
  have h_nonempty : cards.Nonempty := by
    refine ⟨0, ∅, Finset.empty_subset Z, ?_, Finset.card_empty⟩
    intro a b c d ha hb hc hd hsum
    simp at ha
  have h_fin : Set.Finite cards := by
    have h_fin_img : Set.Finite ((Z.powerset.image Finset.card : Finset ℕ) : Set ℕ) :=
      Finset.finite_toSet _
    apply Set.Finite.subset h_fin_img
    intro k hk
    rcases hk with ⟨A, hA_sub, hA_sidon, hcard⟩
    refine Finset.mem_image.mpr ⟨A, ?_, hcard⟩
    exact Finset.mem_powerset.mpr hA_sub
  have h_finset_nonempty : h_fin.toFinset.Nonempty := by
    rcases h_nonempty with ⟨k, hk⟩
    refine ⟨k, h_fin.mem_toFinset.mpr hk⟩
  let m := h_fin.toFinset.max' h_finset_nonempty
  have hm_cards : m ∈ cards :=
    h_fin.mem_toFinset.mp (Finset.max'_mem _ h_finset_nonempty)
  rcases hm_cards with ⟨A, hA_sub, hA_sidon, hcard⟩
  refine ⟨m, ?_⟩
  constructor
  · refine ⟨A, ?_, hcard⟩
    refine { subset := λ x hx => ?_, sidon := hA_sidon }
    have hx_mem_icc : x ∈ Z := hA_sub hx
    rcases Finset.mem_Icc.1 hx_mem_icc with ⟨hx1, hx2⟩
    exact ⟨hx1, hx2⟩
  · intro B hB
    have hB_sub : B ⊆ Z := by
      intro x hx; rcases hB.subset x hx with ⟨hx1, hx2⟩
      exact Finset.mem_Icc.mpr ⟨hx1, hx2⟩
    have hB_card : B.card ∈ cards := ⟨B, hB_sub, hB.sidon, rfl⟩
    have hB_fin : B.card ∈ h_fin.toFinset := h_fin.mem_toFinset.mpr hB_card
    exact Finset.le_max' h_fin.toFinset (B.card) hB_fin

/-- The extremal Sidon function h(N) = max{|A| : A ⊆ {1,...,N} is Sidon}. -/
noncomputable def sidonMaximum (N : ℕ) : ℕ :=
  Classical.choose (sidonMaximum_exists N)

/-- The maximum exists for every N. -/
theorem sidonMaximum_isSidonMaximum (N : ℕ) :
    IsSidonMaximum N (sidonMaximum N) :=
  Classical.choose_spec (sidonMaximum_exists N)

/-- The maximum cardinality is unique. -/
theorem isSidonMaximum_unique {N h k : ℕ}
    (hh : IsSidonMaximum N h) (hk : IsSidonMaximum N k) :
    h = k := by
  rcases hh.1 with ⟨A, hA, hAcard⟩
  rcases hk.1 with ⟨B, hB, hBcard⟩
  have hle : h ≤ k := by rw [← hAcard]; exact hk.2 hA
  have hge : k ≤ h := by rw [← hBcard]; exact hh.2 hB
  omega

/-! ## Difference-Counting Upper Bound -/

/-- First upper bound: for any interval Sidon set A ⊆ {1,...,N},
    |A| ≤ √(2N) + 1. This follows from pair-difference counting. -/
theorem IsIntervalSidon.card_le {A : Finset ℤ} {N : ℕ}
    (h : IsIntervalSidon (N : ℤ) A) (hN : 1 ≤ N) :
    A.card ≤ Nat.sqrt (2 * N) + 1 :=
  sorry -- TODO(lean-port): Port from Erdos30/Interval.lean (IsIntervalSidon.card_le)

/-- The quadratic upper bound on sidonMaximum: h(N) ≤ √(2N) + 1. -/
theorem sidonMaximum_le_sqrt_two (N : ℕ) (hN : 1 ≤ N) :
    sidonMaximum N ≤ Nat.sqrt (2 * N) + 1 :=
  sorry -- TODO(lean-port): Port from Erdos30/Lindstrom.lean

/-! ## Lindström's Cross-Difference Inequality -/

/-- **Lindström's cross-difference inequality.** For a Sidon set in {1,...,N}
    of cardinality m, and any k with 1 ≤ k ≤ m, we have (m - k) * k ≤ N - 1.

    This is the key bound that improves the quadratic estimate to
    h(N) ≤ √N + N^{1/4} + 1.

    Reference: Lindström, B. (1969). An inequality for B₂-sequences.
    *J. Combin. Theory*, 6(2), 211–212. -/
theorem IsIntervalSidon.lindstrom_cross_ineq {A : Finset ℤ} {N : ℕ}
    (hIS : IsIntervalSidon (N : ℤ) A) (hN : 1 ≤ N)
    {k : ℕ} (hk : 1 ≤ k) (hkm : k ≤ A.card) :
    (A.card - k) * k ≤ N - 1 :=
  sorry -- TODO(lean-port): Port from Erdos30/Lindstrom.lean (full proof, ~170 lines)

/-- The Lindström upper bound: h(N) ≤ √N + √(√N) + 2. -/
theorem sidonMaximum_le_lindstrom (N : ℕ) (hN : 16 ≤ N) :
    sidonMaximum N ≤ Nat.sqrt N + Nat.sqrt (Nat.sqrt N) + 2 :=
  sorry -- TODO(lean-port): Port from Erdos30/LindstromImproved.lean

/-! ## Singer's Construction -/

/-- **Singer's theorem.** For each prime p, there exists a Sidon set
    modulo p² + p + 1 of cardinality p + 1.

    This is the classical algebraic construction using the trace kernel
    of GF(p³)/GF(p). The proof proceeds through:
    1. Construction of GF(p) and its degree-3 extension GF(p³)
    2. Analysis of ker(Tr) as a 2-dimensional subspace
    3. Geometric argument via subspace intersections
    4. Transfer from quotient multiplication to modular integer addition

    Reference: Singer, J. (1938). A theorem in finite projective geometry
    and some applications. *Trans. Amer. Math. Soc.*, 43, 377–385. -/
theorem singer_sidon_set (p : ℕ) (hp : Nat.Prime p) :
    ∃ S : Finset ℤ, IsSidonMod (↑p * ↑p + ↑p + 1 : ℤ) S ∧ S.card = p + 1 :=
  sorry -- TODO(lean-port): Port from Erdos30/SingerTheorem.lean
        -- This requires: Singer.lean (algebraic core), SingerBridge.lean,
        -- SingerSidon.lean (quotient Sidon property), SingerTheorem.lean
        -- Total: ~800 lines of algebraic Lean 4

/-- The Singer family hypothesis: for every prime p, there exists a
    Sidon set mod (p²+p+1) of size p+1. -/
def SingerFamilyHypothesis : Prop :=
  ∀ p : ℕ, Nat.Prime p →
    ∃ S : Finset ℤ, IsSidonMod (↑p * ↑p + ↑p + 1 : ℤ) S ∧ S.card = p + 1

/-- Singer's theorem establishes the Singer family hypothesis. -/
theorem singerFamilyHypothesis_holds : SingerFamilyHypothesis :=
  fun p hp => singer_sidon_set p hp

/-! ## Unconditional h(N) = Θ(√N) Bounds -/

/-- **Unconditional lower bound** via Singer + Bertrand:
    h(N) > (√N + 1) / 2 for all N ≥ 5.

    Uses the Singer family theorem together with Bertrand's postulate
    to find a prime near √N, then transfers the Singer Sidon set to
    an interval Sidon set via the cyclic window method. -/
theorem sidonMaximum_gt_sqrt_div_two (N : ℕ) (hN : 5 ≤ N) :
    (Nat.sqrt N + 1) / 2 < sidonMaximum N :=
  sorry -- TODO(lean-port): Port from Erdos30/UnconditionalBounds.lean

/-- **Combined unconditional two-sided bound** on sidonMaximum:
    (√N + 1) / 2 < h(N) ≤ √(2N) + 1 for all N ≥ 5.

    This confirms h(N) = Θ(√N) without any conditional hypotheses. -/
theorem sidonMaximum_bounds (N : ℕ) (hN : 5 ≤ N) :
    (Nat.sqrt N + 1) / 2 < sidonMaximum N ∧
      sidonMaximum N ≤ Nat.sqrt (2 * N) + 1 :=
  ⟨sidonMaximum_gt_sqrt_div_two N hN,
   sidonMaximum_le_sqrt_two N (by omega)⟩

/-- The Sidon maximum is positive for N ≥ 1. -/
theorem sidonMaximum_pos (N : ℕ) (hN : 1 ≤ N) : 1 ≤ sidonMaximum N := by
  have hmax := sidonMaximum_isSidonMaximum N
  have hSidon : IsSidon ({1} : Finset ℤ) := by
    intro a b c d ha hb hc hd _; simp at ha hb hc hd
    left; exact ⟨ha ▸ hc.symm, hb ▸ hd.symm⟩
  have h1 : IsIntervalSidon (N : ℤ) ({1} : Finset ℤ) := by
    constructor
    · intro x hx; simp at hx; subst hx; exact ⟨le_refl 1, by exact_mod_cast hN⟩
    · exact hSidon
  have hle := hmax.2 h1; simp at hle; exact hle

/-- The Sidon maximum function is monotone non-decreasing. -/
theorem sidonMaximum_mono {N M : ℕ} (hNM : N ≤ M) :
    sidonMaximum N ≤ sidonMaximum M := by
  have hmax_N := sidonMaximum_isSidonMaximum N
  have hmax_M := sidonMaximum_isSidonMaximum M
  rcases hmax_N.1 with ⟨A, hA, hAcard⟩
  have hA_M : IsIntervalSidon (M : ℤ) A := hA.mono (by exact_mod_cast hNM)
  have hle := hmax_M.2 hA_M; omega

/-! ## Erdős Problem 30 Statement -/

/-- The formal Erdős Problem 30 statement: h(N) = √N + O_ε(N^ε) for every ε > 0. -/
def Erdos30Statement : Prop :=
  ∀ ε : ℝ, 0 < ε →
    ∃ C : ℝ, ∃ N0 : ℕ,
      0 ≤ C ∧
        ∀ {N h : ℕ}, N0 ≤ N → IsSidonMaximum N h →
          abs ((h : ℝ) - Real.sqrt (N : ℝ)) ≤ C * Real.rpow (N : ℝ) ε

/-- **Partial discharge for ε ≥ 1/2** (unconditional).
    For all ε ≥ 1/2, |h(N) - √N| ≤ 2·N^ε for all N ≥ 5. -/
theorem erdos30_partial_half :
    ∀ ε : ℝ, (1 : ℝ) / 2 ≤ ε → 0 < ε →
      ∃ C : ℝ, ∃ N0 : ℕ,
        0 ≤ C ∧
          ∀ {N h : ℕ}, N0 ≤ N → IsSidonMaximum N h →
            abs ((h : ℝ) - Real.sqrt (N : ℝ)) ≤ C * Real.rpow (N : ℝ) ε :=
  sorry -- TODO(lean-port): Port from Erdos30/UnconditionalBounds.lean

/-- **Lindström upper bound for ε ≥ 1/4** (unconditional).
    For all ε ≥ 1/4, h(N) ≤ √N + 2·N^ε for all N ≥ 16. -/
theorem sidonUpperBound_quarter :
    ∀ ε : ℝ, (1 : ℝ) / 4 ≤ ε → 0 < ε →
      ∃ C : ℝ, ∃ N0 : ℕ,
        0 ≤ C ∧
          ∀ {N h : ℕ}, N0 ≤ N → IsSidonMaximum N h →
            (h : ℝ) ≤ Real.sqrt (N : ℝ) + C * Real.rpow (N : ℝ) ε :=
  sorry -- TODO(lean-port): Port from Erdos30/UnconditionalBounds.lean

/-! ## Conditional Erdős Problem 30 Reduction -/

/-- **Conditional reduction.** Subpolynomial prime gaps together with a full
    subpolynomial upper-error hypothesis for h(N) imply the Erdős Problem 30
    estimate h(N) = √N + O_ε(N^ε) for every ε > 0.

    This is the paper's Theorem 1.1 (conditional). -/
theorem conditional_erdos30
    (h_prime_gap : ∀ ε : ℝ, 0 < ε → ∃ N₀ : ℕ, ∀ N ≥ N₀, ∃ p : ℕ, Nat.Prime p ∧
      abs ((p : ℝ) - Real.sqrt (N : ℝ)) ≤ Real.rpow (N : ℝ) ε)
    (h_upper : ∀ ε : ℝ, 0 < ε → ∃ C : ℝ, ∃ N0 : ℕ, 0 < C ∧
      ∀ {N h : ℕ}, N0 ≤ N → IsSidonMaximum N h →
        (h : ℝ) ≤ Real.sqrt (N : ℝ) + C * Real.rpow (N : ℝ) ε) :
    Erdos30Statement :=
  sorry -- TODO(lean-port): Port from Erdos30/ConditionalErdos30.lean

/-! ## Representation Function -/

/-- For a Sidon set, the representation function is bounded by 2:
    at most 2 ordered pairs (a,b) ∈ A×A satisfy a + b = n.
    Uses Finset.product instead of the ×ˢ notation. -/
theorem IsSidon.repr_le_two {A : Finset ℤ} (hA : IsSidon A) (n : ℤ) :
    ((A.product A).filter (fun ab : ℤ × ℤ => ab.1 + ab.2 = n)).card ≤ 2 := by
  set S := (A.product A).filter (λ ab : ℤ × ℤ => ab.1 + ab.2 = n) with hS
  by_cases h_empty : S.Nonempty
  · rcases h_empty with ⟨⟨a, b⟩, hab⟩
    have ha_mem_filter : (a, b) ∈ (A.product A).filter (λ ab : ℤ × ℤ => ab.1 + ab.2 = n) := by
      simpa [hS] using hab
    have ha_mem_product : (a, b) ∈ A.product A :=
      (Finset.mem_filter.1 ha_mem_filter).1
    have ha_all : a ∈ A ∧ b ∈ A := Finset.mem_product.1 ha_mem_product
    have ha : a ∈ A := ha_all.1
    have hb : b ∈ A := ha_all.2
    have hsum : a + b = n := by
      simpa using (Finset.mem_filter.1 ha_mem_filter).2
    have h_sub : S ⊆ {(a, b), (b, a)} := by
      intro ⟨x, y⟩ hxy
      have hx_mem_filter : (x, y) ∈ (A.product A).filter (λ ab : ℤ × ℤ => ab.1 + ab.2 = n) := by
        simpa [hS] using hxy
      have hx_mem_product : (x, y) ∈ A.product A :=
        (Finset.mem_filter.1 hx_mem_filter).1
      have hx_all : x ∈ A ∧ y ∈ A := Finset.mem_product.1 hx_mem_product
      have hx : x ∈ A := hx_all.1
      have hy : y ∈ A := hx_all.2
      have hsum_xy : x + y = n := by
        simpa using (Finset.mem_filter.1 hx_mem_filter).2
      have hab_eq : a + b = x + y := by
        calc
          a + b = n := hsum
          _ = x + y := hsum_xy.symm
      rcases hA ha hb hx hy hab_eq with (⟨hac, hbd⟩ | ⟨had, hbc⟩)
      · simp [hac, hbd]
      · simp [had, hbc]
    have h_card_sub : S.card ≤ ({(a, b), (b, a)} : Finset (ℤ × ℤ)).card :=
      Finset.card_le_card h_sub
    have h_card_two : ({(a, b), (b, a)} : Finset (ℤ × ℤ)).card ≤ 2 := by
      by_cases h_eq : (a, b) = (b, a)
      · simp [h_eq]
      · simp [h_eq]
    omega
  · have h_card_zero : S.card = 0 := by
      apply Finset.card_eq_zero.mpr
      ext x; simp; intro hx; exact h_empty ⟨x, hx⟩
    omega

/-! ## No-Wraparound Lemma -/

/-- **No-wraparound lemma.** If all elements of A are in {1,...,N} and
    M ≥ 2N - 1, then IsSidon A → IsSidonMod M A. This is the key step
    that lets interval Sidon sets be embedded into a cyclic ambient group
    without creating new sum collisions. -/
theorem IsSidon.isSidonMod_of_interval {A : Finset ℤ} {N M : ℤ}
    (hA : IsSidon A)
    (hbound : ∀ x ∈ A, 1 ≤ x ∧ x ≤ N)
    (hM : 2 * N - 1 ≤ M) : IsSidonMod M A := by
  intro a b c d ha hb hc hd hdiv
  have ha_bound := hbound a ha
  have hb_bound := hbound b hb
  have hc_bound := hbound c hc
  have hd_bound := hbound d hd
  have hN_pos : 1 ≤ N := le_trans ha_bound.1 ha_bound.2
  have hM_nonneg : 0 ≤ M := by omega
  have hdiff_bound : |(a + b) - (c + d)| ≤ 2 * N - 2 := by
    apply abs_le.mpr
    constructor <;> omega
  have hlt : |(a + b) - (c + d)| < M := by
    have : 2 * N - 2 < 2 * N - 1 := by omega
    omega
  rcases hdiv with ⟨k, hk⟩
  by_cases hk0 : k = 0
  · rw [hk0, mul_zero] at hk
    have hsum_eq : a + b = c + d := by omega
    exact hA ha hb hc hd hsum_eq
  · have hk_abs_ge_one : 1 ≤ |k| := by
      have hk_ne_zero : k ≠ 0 := hk0
      have hk_abs_pos : 0 < |k| := abs_pos.mpr hk_ne_zero
      omega
    have hM_eq_abs : |M| = M := abs_of_nonneg hM_nonneg
    have hdiff_bound_M : M ≤ |(a + b) - (c + d)| := by
      calc
        M = |M| := hM_eq_abs.symm
        _ ≤ |M| * |k| := by
          calc
            |M| = |M| * 1 := by simp
            _ ≤ |M| * |k| :=
              mul_le_mul_of_nonneg_left hk_abs_ge_one (abs_nonneg _)
        _ = |M * k| := by rw [abs_mul]
        _ = |(a + b) - (c + d)| := by rw [hk]
    linarith

/-! ## Singer ↔ Golden Angle Connection -/

/-- The Singer construction modulus for prime p: q² + q + 1 where q = p.
    For p = 2: 2² + 2 + 1 = 7. For p = 3: 3² + 3 + 1 = 13.
    These are the orders of the cyclic difference sets. -/
def singerModulus (p : ℕ) : ℕ := p * p + p + 1

/-- The Singer set cardinality for prime p: p + 1 elements. -/
def singerCardinality (p : ℕ) : ℕ := p + 1

/-- The Singer Sidon density ratio: numerator = p+1, denominator = p²+p+1.
    For large p, this ratio ≈ 1/p → 0, while the golden angle density
    1/φ ≈ 0.618 exceeds all finite Singer densities. -/
def singerDensityNum (p : ℕ) : ℕ := p + 1
def singerDensityDen (p : ℕ) : ℕ := p * p + p + 1

-- Executable witnesses for small primes
#eval singerModulus 2    -- 7
#eval singerCardinality 2  -- 3
#eval singerModulus 3    -- 13
#eval singerCardinality 3  -- 4
#eval singerModulus 5    -- 31
#eval singerCardinality 5  -- 6

end Semantics.SidonSets
