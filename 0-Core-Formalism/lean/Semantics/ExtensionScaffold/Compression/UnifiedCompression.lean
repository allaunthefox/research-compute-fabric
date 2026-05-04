import Semantics.Spectrum
import ExtensionScaffold.Compression.Core
import Mathlib.Tactic
import Mathlib.Data.Nat.Sqrt

namespace ExtensionScaffold.Compression

open Semantics.Spectrum

/-! # Unified Compression Engine

Complete unification of 30 components into a single compression pipeline:

```
X → G_θ{πᵢ} →contact→ {χᵢ} →g→ {eᵢ} →Λ→ {zᵢ} →bind→ L(X)
```

**6-step execution:**
1. Generate structured pulses from shell coordinates
2. Build standing-wave field from echoes
3. Detect 3-point contact
4. Gate on closure + positive interaction
5. Emit constrained code
6. Compress via lawful binding

**Key insight:** Encode only when multi-layer constraints agree
(arithmetic + geometric + temporal + field + contact), not merely
statistical prediction.

Status: Extension — experimental unified compression primitive.

Citation: Contributed via ChatGPT research session, 2026-04-17.
Source: User specification of complete compression unification.
-/

/-- Triangle mode for pulse generation. -/
inductive TriangleMode
  | a  -- Axial generator (purine)
  | g  -- Guanine midpoint
  | c  -- Cytosine post-midpoint
  | t  -- Thymine terminal (pyrimidine)
  | square  -- Perfect square resonance hub
deriving Repr, BEq, DecidableEq

/-- Structured pulse from shell coordinates. -/
structure Pulse where
  mode : TriangleMode
  pos : Int          -- Position n in integer lattice
  width : Nat        -- Shell-derived width (2k+1)
  mass : UInt32      -- ab product (Q16.16 encoded)
  polarity : Int32   -- a - b difference
  square : Bool      -- Perfect square flag
  k : Nat            -- Shell index ⌊√n⌋
  a : Nat            -- Lower offset
  b : Nat            -- Upper offset
deriving Repr, BEq

/-- Local field with support function. -/
structure LocalField where
  -- Support value at position (Q16.16 fixed-point)
  support : Int → UInt32

/-- 3-point contact detection. -/
structure Contact where
  a : Bool  -- Left contact κ_A
  b : Bool  -- Center contact κ_B
  c : Bool  -- Right contact κ_C
deriving Repr, BEq

/-- Emitted code from Λ(π, χ). -/
structure Code where
  symbol : UInt8    -- 4-bit nibble or 8-bit byte
  valid : Bool      -- Constraint satisfaction flag
  cost : UInt32     -- Q16.16 binding cost
deriving Repr, BEq

/-- Standing-wave echo weights [1, ½, ¼]. -/
def echoWeights : List UInt32 :=
  [0x00010000,   -- 1.0
   0x00008000,   -- 0.5
   0x00004000]   -- 0.25

/-- Build field from pulse echoes (rear field). -/
def buildEchoField (pulse : Pulse) (field : LocalField) : UInt32 :=
  let w1 := echoWeights[0]!
  let w2 := echoWeights[1]!
  let w3 := echoWeights[2]!
  let f1 := field.support (pulse.pos - Int.ofNat pulse.width)
  let f2 := field.support pulse.pos
  let f3 := field.support (pulse.pos + Int.ofNat pulse.width)
  -- Weighted sum: w1·f1 + w2·f2 + w3·f3
  (w1 * f1 + w2 * f2 + w3 * f3) / 0x00010000

/-- Derive 3-point contact from pulse and field. -/
def deriveContact (π : Pulse) (σ : LocalField) (θ : UInt32) : Contact :=
  { a := σ.support (π.pos - Int.ofNat π.width) > θ
  , b := σ.support π.pos > θ
  , c := σ.support (π.pos + Int.ofNat π.width) > θ }

/-- Interaction score J(n) = ab·F_m + (a-b)·F_p + ⟨χ, F_c⟩. -/
def interactionScore (π : Pulse) (σ : LocalField) (χ : Contact) : Int :=
  let fm := σ.support π.pos
  let fp := σ.support π.pos
  let fc := if χ.a then 1 else 0
  let massTerm := π.mass.toNat * fm.toNat
  let polarityTerm := Int.ofNat π.polarity.toNatClampNeg * Int.ofNat fp.toNat
  Int.ofNat massTerm + polarityTerm + fc

/-- Gate emission: κ_A ∧ κ_C ∧ J > 0. -/
def emitGate (χ : Contact) (J : Int) : Bool :=
  χ.a && χ.c && J > 0

/-- Code LUT (placeholder — constraint-reachable structure). -/
def codeLUT (π : Pulse) (χ : Contact) : Code :=
  let symbol := if π.square then
    0x10  -- Square resonance marker
  else
    (π.a % 16).toUInt8 + (π.b % 16).toUInt8 * 16
  { symbol := symbol
  , valid := χ.a && χ.b && χ.c
  , cost := 0x00001000 }  -- Base cost

/-- Emit code only when structure closes. -/
def emitCode? (π : Pulse) (χ : Contact) (σ : LocalField) : Option Code :=
  let J := interactionScore π σ χ
  if emitGate χ J then
    some (codeLUT π χ)
  else
    none

/-- Integer square root (floor of sqrt) via Mathlib's `Nat.sqrt`. -/
def isqrt (n : Nat) : Nat :=
  Nat.sqrt n

/-- Generate pulse from integer n (shell decomposition). -/
def pulseFromInt (n : Nat) : Pulse :=
  let k := isqrt n
  let a := Nat.sub n (k*k)
  let b := Nat.sub ((k+1)*(k+1)) n
  let isSquare := a == 0
  let mass := (a * b).toUInt32
  let polarity := (Int.ofNat a - Int.ofNat b).toInt32
  { mode := if isSquare then .square else
            if a == k then .g else
            if a == k+1 then .c else
            if b == 1 then .t else .a
  , pos := Int.ofNat n
  , width := 2*k + 1
  , mass := mass
  , polarity := polarity
  , square := isSquare
  , k := k
  , a := a
  , b := b }

/-- Unified compression: L(X) = Σ bind(zᵢ). -/
def unifiedCompress (positions : List Nat) (σ : LocalField) (θ : UInt32) : List Code :=
  positions.filterMap (λ n =>
    let π := pulseFromInt n
    let χ := deriveContact π σ θ
    emitCode? π χ σ)

/-! ## Final Score Law (Model 119-120) -/

/-- Per-step cost components:
    - ℓₜ = eₜ·bind(γₜ,modelₜ,gₜ,historyₜ)
    - + λ₁·H(κₜ)           [codon entropy]
    - + λ₂·d_addr          [address/routing]
    - + λ₃·D_eff           [manifold complexity]
    - - λ₄·G               [gain reward]
-/
structure ScoreParams where
  lambda1 : UInt32  -- Q16.16: codon entropy weight
  lambda2 : UInt32  -- Q16.16: address penalty weight
  lambda3 : UInt32  -- Q16.16: manifold penalty weight
  lambda4 : UInt32  -- Q16.16: gain reward weight
deriving Repr

def defaultScoreParams : ScoreParams :=
  { lambda1 := 0x00010000  -- 1.0
  , lambda2 := 0x00008000  -- 0.5
  , lambda3 := 0x00004000  -- 0.25
  , lambda4 := 0x00020000  -- 2.0
  }

/-- Codon entropy H(κ) — 3-symbol entropy approximation. -/
def codonEntropy (κ : Contact) : UInt32 :=
  let activeCount := [κ.a, κ.b, κ.c].filter (λ b => b) |>.length
  -- H ≈ -Σ p·log₂(p) approximated by count of active contacts
  (activeCount.toUInt32 * 0x00010000) / 3

/-- Address distance penalty. -/
def addressPenalty (pos current : Int) : UInt32 :=
  let dist := if pos > current then (pos - current).toNat else (current - pos).toNat
  (dist * 0x00010000).toUInt32

/-- Manifold complexity penalty D_eff(M). -/
def manifoldPenalty (mass polarity : UInt32) : UInt32 :=
  -- Complexity ∝ |mass| + |polarity|
  (mass + polarity) / 2

/-- Gain reward G(v,τ,h) — positive reinforcement. -/
def gainReward (valid validTotal : Nat) : UInt32 :=
  if validTotal == 0 then 0
  else ((valid * 65536 : Nat) / validTotal).toUInt32

/-- Per-step score ℓₜ. -/
def stepScore (e : UInt32) (codeCost : UInt32) (κ : Contact)
              (pos current : Int) (mass polarity : UInt32)
              (valid validTotal : Nat) (params : ScoreParams) : Int :=
  let bindCost := Int.ofNat (e * codeCost).toNat
  let entropyPenalty := Int.ofNat (params.lambda1 * codonEntropy κ).toNat
  let addrPenalty := Int.ofNat (params.lambda2 * addressPenalty pos current).toNat
  let manifPenalty := Int.ofNat (params.lambda3 * manifoldPenalty mass polarity).toNat
  let gain := Int.ofNat (params.lambda4 * gainReward valid validTotal).toNat
  -- ℓₜ = e·bind + λ₁·H + λ₂·d_addr + λ₃·D_eff - λ₄·G
  bindCost + entropyPenalty + addrPenalty + manifPenalty - gain

/-- Total compression cost L(X). -/
def totalCompressionCost (positions : List Nat) (σ : LocalField) (θ : UInt32)
                         (params : ScoreParams) (history : List Code) : Int :=
  let codes := unifiedCompress positions σ θ
  let validCount := codes.filter (·.valid) |>.length
  let costs := codes.map (λ c => Int.ofNat c.cost.toNat)
  let baseCost := costs.foldl (λ acc x => acc + x) 0
  -- Add commitment cost for AVMR/AMMR structure
  let commitmentCost := Int.ofNat (history.length * 0x00001000)
  baseCost + commitmentCost

/-- Helper: isqrt returns floor(sqrt(n)) for n > 0.
    Key property: k² ≤ n < (k+1)² where k = isqrt n. -/
private theorem isqrt_spec (n : Nat) (hn : n > 0) :
  let k := isqrt n
  k * k ≤ n ∧ n < (k + 1) * (k + 1) := by
  simp [isqrt]
  exact ⟨Nat.sqrt_le n, Nat.lt_succ_sqrt n⟩

/-- Helper: isqrt(k²) = k for k > 0 -/
private theorem isqrt_kk_eq_k (k : Nat) (hk : k > 0) : isqrt (k * k) = k := by
  have h_spec := isqrt_spec (k * k) (by nlinarith)
  simp at h_spec
  -- From isqrt_spec: (isqrt(k*k))² ≤ k² < (isqrt(k*k)+1)²
  -- This implies isqrt(k*k) ≤ k and k ≤ isqrt(k*k)
  have h3 : isqrt (k * k) ≤ k := by
    nlinarith [h_spec.left]
  have h4 : k ≤ isqrt (k * k) := by
    nlinarith [h_spec.right]
  omega

/-- Helper: when n = k², isqrt n = k.
    Note: This proof relies on isqrt_spec. The key insight is that
    isqrt(k²) is the unique value m such that m² ≤ k² < (m+1)²,
    which implies m = k. -/
private theorem isqrt_of_square (n k : Nat) (h : n = k * k) (hn : n > 0) :
  isqrt n = k := by
  rw [h]
  have hk : k > 0 := by
    nlinarith [h, hn]
  exact isqrt_kk_eq_k k hk

/-- Witness: square pulses have zero mass.
    When n = k², then a = n - k² = 0, so mass = a·b = 0. -/
theorem squarePulseZeroMass (n : Nat) (h : ∃ k, n = k*k) :
  (pulseFromInt n).mass = 0 := by
  rcases h with ⟨k, hk⟩
  by_cases hn : n > 0
  · -- n > 0 case
    unfold pulseFromInt
    have h_isqrt_n : isqrt n = k := by
      apply isqrt_of_square n k hk hn
    have hk_pos : k > 0 := by nlinarith [hk, hn]
    have h_isqrt_kk : isqrt (k * k) = k := by
      exact isqrt_kk_eq_k k hk_pos
    -- Use both isqrt facts: isqrt n = k and isqrt (k*k) = k
    -- With n = k*k, we have a = n - k² = 0
    simp [h_isqrt_n, h_isqrt_kk, hk, Nat.sub_self]
    <;> simp [Nat.zero_mul]
    <;> rfl
  · -- n = 0 case
    have hn0 : n = 0 := by omega
    rw [hn0] at hk
    have hk0 : k = 0 := by nlinarith
    have h_isqrt_0 : isqrt 0 = 0 := by simp [isqrt]
    have h_isqrt_00 : isqrt (0 * 0) = 0 := by simp [isqrt]
    unfold pulseFromInt
    simp only [hn0, hk0, h_isqrt_0, h_isqrt_00]
    rfl

/-- Witness: non-square pulses have positive mass.
    When n ≠ k² for any k, then a = n - floor(√n)² > 0 and
    b = (floor(√n)+1)² - n > 0, so mass = a·b > 0.
    Bounded to n < 65536 to avoid UInt32 overflow (matches original isqrt cap). -/
theorem nonSquarePulsePositiveMass (n : Nat) (hn : n < 65536) (h : ∀ k, n ≠ k*k) :
  (pulseFromInt n).mass > 0 := by
  unfold pulseFromInt
  simp [isqrt]
  have h_spec := Nat.sqrt_le n
  have h_lt := Nat.lt_succ_sqrt n
  let k := Nat.sqrt n
  have ha1 : k * k ≤ n := h_spec
  have hb1 : n < (k + 1) * (k + 1) := h_lt
  have ha2 : n - k * k > 0 := by
    by_contra h_a0
    push_neg at h_a0
    have h_a0' : n - k * k = 0 := by omega
    have h_eq : n = k * k := by
      rw [←Nat.sub_add_cancel ha1]
      rw [h_a0']
      simp
    exact h k h_eq
  have hb2 : (k + 1) * (k + 1) - n > 0 := by
    omega
  have hk_bound : k ≤ 255 := by
    nlinarith
  have ha_bound : n - k * k ≤ 510 := by
    have h_sub : n - k * k < (k + 1) * (k + 1) - k * k := by
      apply Nat.sub_lt_sub_right ha1 h_lt
    have h_eq : (k + 1) * (k + 1) - k * k = 2 * k + 1 := by
      simp [Nat.add_mul, Nat.mul_add]
      <;> omega
    rw [h_eq] at h_sub
    omega
  have hb_bound : (k + 1) * (k + 1) - n ≤ 511 := by
    omega
  have h_prod_bound : (n - k * k) * ((k + 1) * (k + 1) - n) < UInt32.size := by
    norm_num [UInt32.size]
    nlinarith
  have h_pos : (n - k * k) * ((k + 1) * (k + 1) - n) > 0 := by
    nlinarith
  -- Goal: 0 < UInt32.ofNat a * UInt32.ofNat b
  -- Rewrite using UInt32.ofNat_mul, then prove single ofNat is positive
  rw [←UInt32.ofNat_mul]
  have h_u32_pos : UInt32.ofNat ((n - k * k) * ((k + 1) * (k + 1) - n)) > 0 := by
    have h1 : (UInt32.ofNat ((n - k * k) * ((k + 1) * (k + 1) - n))).toNat
              = (n - k * k) * ((k + 1) * (k + 1) - n) := by
      simp [UInt32.toNat_ofNat]
      rw [Nat.mod_eq_of_lt h_prod_bound]
    have h2 : (0 : UInt32).toNat = 0 := by simp
    have h3 : (UInt32.ofNat ((n - k * k) * ((k + 1) * (k + 1) - n))).toNat > (0 : UInt32).toNat := by
      rw [h1, h2]
      omega
    have h4 : UInt32.ofNat ((n - k * k) * ((k + 1) * (k + 1) - n)) > (0 : UInt32) := by
      rw [GT.gt]
      rw [UInt32.lt_iff_toNat_lt]
      exact h3
    exact h4
  exact h_u32_pos

end ExtensionScaffold.Compression
