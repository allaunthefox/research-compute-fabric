/-
Law 21 — Thermal Boundary Gate

Formalises the HCMMR temperature-regime admissibility gate A_thermal.

Doctrine: temperature is a *gate variable*, not a free parameter.  Two
hard boundaries bracket the physically accessible regime, and the CMB floor
anchors the observable cosmic background.

  1. **Absolute zero boundary — 0 K = hard floor (not a state)**
     T = 0 K is a asymptotic limit, never a reachable state.  Any thermal
     input claiming T ≤ 0 is inadmissible — an Underverse entry with a
     "subliminal temperature" residual.

  2. **CMB anchor — T_CMB ≈ 2.725 K**
     The cosmic microwave background sets the coldest observable large-scale
     thermal state in the present-epoch universe.  Objects claimed below T_CMB
     in an unshielded environment are flagged with a "subCMB" residual; they
     are not rejected outright (local cooling below CMB is possible) but carry
     a non-zero ambient-friction scar.

  3. **Hagedorn / matter-phase ceiling — T_Hagedorn ≈ 10¹² K**
     Above T_Hagedorn, hadronic matter undergoes a phase transition to a
     quark–gluon plasma.  The HCMMR boundary is set at 10¹² K.  Objects
     claiming T > 10¹² K are not rejected but are rerouted to a
     "plasma phase" receipt — the Boltzmann/equipartition assumptions of
     the thermal gate no longer apply and a separate plasma-regime gate is needed.

  4. **Landauer threshold — ΔE ≥ k_B T ln 2 per bit erased**
     Every irreversible computation has a minimum energy cost of k_B T ln 2.
     The gate checks whether a proposed erasure event is above this threshold.
     Below-threshold erasure claims are routed to the Underverse as
     "sub-Landauer" violations.

  5. **Thermal regime classification**
     Based on T, objects are classified into: CryogenicDeep, CryogenicShallow,
     Ambient, Hot, Plasma — each with distinct physics chart recommendations.

  6. **Thermal receipt**
     Every evaluation emits a typed `ThermalReceipt` recording the raw
     temperature, the Landauer floor at that T, the regime class, and the
     admissibility verdict.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law21
  Imports: Semantics.HCMMR.Core, Semantics.FixedPoint
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law21

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Thermal Constants
-- ═══════════════════════════════════════════════════════════════════

/--
Boltzmann constant: k_B = 1.380649 × 10⁻²³ J/K (exact SI 2019).

Stored as a rational value for Landauer floor computations.
Nat representation: 1380649 / (10^29).  Not converted to Q16_16 directly
because thermal energies span 30+ orders of magnitude; instead we
compute k_B × T as a rational and convert the *ratio* to Q16_16 when needed.
-/
def boltzmann_num : Nat := 1380649     -- numerator × 10⁻²³
def boltzmann_den : Nat := 10000000    -- × 10^7 → effective 10⁻³⁰

/--
Cosmic microwave background temperature: T_CMB ≈ 2.72548 K (Fixsen 2009).

Stored in Q16_16 units where 1 K = 65536.
  2.72548 × 65536 = 178,618  (rounded)
-/
def T_CMB : Q16_16 := ⟨178618⟩

/--
ln(2) in Q16_16: ln 2 ≈ 0.693147 × 65536 = 45,426.
Used in the Landauer threshold ΔE ≥ k_B T ln 2.
-/
def ln2_Q16 : Q16_16 := ⟨45426⟩

/--
Hagedorn temperature ceiling (HCMMR boundary): T_H = 10¹² K.

This exceeds Q16_16 range, so we store it as a Nat and only use it in
comparison logic (not arithmetic).  Gate comparisons use integer temperature
values in units of millikelvin to avoid overflow in Q16_16.

In millikelvin: T_H = 10¹² K × 1000 mK/K = 10¹⁵ mK.
-/
def T_Hagedorn_K : Nat := 1000000000000  -- 10¹² K

/--
Absolute zero boundary: T_abs = 0 K.  Any claimed T ≤ 0 is inadmissible.
Stored as Nat for comparison.
-/
def T_absZero_K : Nat := 0

-- ═══════════════════════════════════════════════════════════════════
-- §2  Temperature Input Model
-- ═══════════════════════════════════════════════════════════════════

/--
Thermal input: a claimed temperature and an energy budget for erasure.

  - `temp_mK`     : claimed temperature in millikelvin (Nat, avoids Q16_16 overflow)
  - `energyBudget`: energy available for one-bit erasure, in units of 10⁻²³ J
                    (same scale as k_B so the Landauer comparison is unit-direct)
  - `bitsToErase` : number of bits being erased (for multi-bit Landauer check)
-/
structure ThermalInput where
  temp_mK      : Nat      -- millikelvin, avoids overflow
  energyBudget : Nat      -- in units of 10⁻²³ J per bit
  bitsToErase  : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §3  Regime Classification
-- ═══════════════════════════════════════════════════════════════════

/--
Thermal regime classes based on temperature thresholds.

| Regime          | Range             | Physics chart          |
|-----------------|-------------------|------------------------|
| SubZero         | T ≤ 0 K           | Inadmissible           |
| CryogenicDeep   | 0 < T < 1 K       | Quantum degenerate     |
| CryogenicShallow| 1 K ≤ T < 50 K    | Liquid He / SuC regimes|
| Ambient         | 50 K ≤ T < 1000 K | Classical stat-mech    |
| Hot             | 1000 K ≤ T < 10¹² K| Thermodynamic limit   |
| Plasma          | T ≥ 10¹² K        | Hadronic phase break   |
-/
inductive ThermalRegime
  | SubZero          -- T ≤ 0 K (inadmissible)
  | CryogenicDeep    -- 0 K < T < 1000 mK  (1 K)
  | CryogenicShallow -- 1000 mK ≤ T < 50000 mK  (50 K)
  | Ambient          -- 50000 mK ≤ T < 1_000_000 mK  (1000 K)
  | Hot              -- 1_000_000 mK ≤ T < 10¹² × 1000 mK
  | Plasma           -- T ≥ 10¹⁵ mK  (10¹² K)
  deriving Repr, BEq, DecidableEq, Inhabited

def classifyThermalRegime (inp : ThermalInput) : ThermalRegime :=
  if inp.temp_mK = 0 then ThermalRegime.SubZero
  else if inp.temp_mK < 1000 then ThermalRegime.CryogenicDeep
  else if inp.temp_mK < 50000 then ThermalRegime.CryogenicShallow
  else if inp.temp_mK < 1000000 then ThermalRegime.Ambient
  else if inp.temp_mK < 1000000000000000 then ThermalRegime.Hot
  else ThermalRegime.Plasma

#eval classifyThermalRegime { temp_mK := 2725, energyBudget := 0, bitsToErase := 0 }
-- expected: ThermalRegime.CryogenicShallow  (2.725 K = 2725 mK)

#eval classifyThermalRegime { temp_mK := 293000, energyBudget := 0, bitsToErase := 0 }
-- expected: ThermalRegime.Ambient  (293 K = 293000 mK, room temp)

-- ═══════════════════════════════════════════════════════════════════
-- §4  CMB Anchor Check
-- ═══════════════════════════════════════════════════════════════════

/--
T_CMB in millikelvin: 2725.48 mK (we use 2725 for integer comparison).
-/
def T_CMB_mK : Nat := 2725

/--
Returns `true` if the input temperature is at or above T_CMB.
Objects below T_CMB carry a non-zero ambient-friction scar but are not rejected.
-/
def aboveCMB (inp : ThermalInput) : Bool :=
  inp.temp_mK ≥ T_CMB_mK

/--
Sub-CMB residual: how far below T_CMB the input is, in millikelvin.
Zero if at or above T_CMB.
-/
def subCMBresidual (inp : ThermalInput) : Nat :=
  if inp.temp_mK < T_CMB_mK then T_CMB_mK - inp.temp_mK else 0

#eval aboveCMB { temp_mK := 300000, energyBudget := 0, bitsToErase := 0 }
-- expected: true  (300 K >> 2.725 K)

#eval subCMBresidual { temp_mK := 1000, energyBudget := 0, bitsToErase := 0 }
-- expected: 1725  (mK below CMB)

-- ═══════════════════════════════════════════════════════════════════
-- §5  Landauer Threshold
-- ═══════════════════════════════════════════════════════════════════

/--
Landauer minimum energy per bit erased: ΔE_min = k_B × T × ln 2.

We compute this directly in units of 10⁻²³ J per bit:
  k_B = 1380649 (where k_B_real = 1380649 × 10⁻²³⁻⁶ = 1.380649 × 10⁻²³ J/K)
  T   = inp.temp_mK / 1000  (convert mK → K)
  ln2 = 6931  (ln2 × 10000, fixed-point 4-decimal approx)

Derivation (units of 10⁻²³ J):
  k_B_real = 1.380649×10⁻²³ J/K = 1380649 × 10⁻²⁹ J/K
  T_K = T_mK / 1000
  ln2 = 6931 / 10000  (4-decimal fixed-point)

  ΔE_min = k_B_real × T_K × ln2
         = (1380649 × 10⁻²⁹) × (T_mK / 10³) × (6931 / 10⁴)
         = 1380649 × T_mK × 6931 × 10⁻²⁹⁻³⁻⁴ J
         = 1380649 × T_mK × 6931 × 10⁻³⁶ J

  In units of 10⁻²³ J (divide by 10⁻²³):
         = 1380649 × T_mK × 6931 / 10^(36-23)
         = 1380649 × T_mK × 6931 / 10^13

Denominator 10^13 = 10^29 (k_B stored scale) / 10^23 (unit) × 10^3 (mK→K) × 10^4 (ln2 scaling).

At T=293 K: 1380649 × 293000 × 6931 / 10^13 ≈ 280  (in 10⁻²³ J units)
Actual k_B × 293 K × ln2 = 1.380649×10⁻²³ × 293 × 0.6931 ≈ 2.804×10⁻²¹ J = 280.4 × 10⁻²³ J ✓
-/
def landauerFloor (inp : ThermalInput) : Nat :=
  -- ΔE_min in units of 10⁻²³ J per bit
  -- = 1380649 × T_mK × 6931 / 10^13
  (1380649 * inp.temp_mK * 6931) / 10000000000000

/--
Returns `true` if `energyBudget` ≥ Landauer floor per bit.

Both `energyBudget` (ThermalInput field) and `landauerFloor` are now in the
same units (10⁻²³ J), so the comparison is direct with no scaling factor.
-/
def landauerAdmissible (inp : ThermalInput) : Bool :=
  inp.bitsToErase = 0 ||
  inp.energyBudget ≥ landauerFloor inp

/--
Sub-Landauer deficit: how far the energy budget falls below the Landauer floor.
In units of 10⁻²³ J per bit.  Zero if admissible.
-/
def landauerDeficit (inp : ThermalInput) : Nat :=
  let floor := landauerFloor inp
  if inp.energyBudget < floor then floor - inp.energyBudget else 0

#eval landauerFloor { temp_mK := 293000, energyBudget := 0, bitsToErase := 1 }
-- T = 293 K → ΔE_min = 1380649 × 293000 × 6931 / 10^13 ≈ 280
-- Actual: k_B × 293 K × ln2 ≈ 2.804 × 10⁻²¹ J = 280.4 × 10⁻²³ J ✓

#eval landauerAdmissible { temp_mK := 293000, energyBudget := 300, bitsToErase := 1 }
-- expected: true  (300 × 10⁻²³ J > Landauer floor ~280 at 293 K)

#eval landauerAdmissible { temp_mK := 293000, energyBudget := 1, bitsToErase := 1 }
-- expected: false (1 × 10⁻²³ J << Landauer floor ~280 at 293 K)

-- ═══════════════════════════════════════════════════════════════════
-- §6  Full Thermal Gate
-- ═══════════════════════════════════════════════════════════════════

/--
Thermal admissibility verdict.
-/
inductive ThermalVerdict
  | Admitted        -- T in (0 K, 10¹² K), Landauer-satisfied
  | RejectedSubZero -- T ≤ 0 K: absolute-zero violation
  | RejectedPlasma  -- T ≥ 10¹² K: Hagedorn phase break, reroute to plasma chart
  | RejectedLandauer -- Erasure energy below Landauer floor
  | AdmittedSubCMB  -- Admitted but T < T_CMB: non-zero ambient scar attached
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Full thermal boundary receipt.
-/
structure ThermalReceipt where
  input          : ThermalInput
  regime         : ThermalRegime
  subCMBresidual : Nat           -- mK below CMB; 0 if above CMB
  landauerFloor  : Nat           -- Landauer minimum in 10⁻²³ J per bit
  landauerDeficit: Nat           -- 0 if satisfied
  verdict        : ThermalVerdict
  deriving Repr, Inhabited

/--
Thermal boundary gate: applies sub-zero check, Hagedorn ceiling, Landauer
threshold, and CMB scar tagging in order.
-/
def thermalGate (inp : ThermalInput) : ThermalReceipt :=
  let regime   := classifyThermalRegime inp
  let subCMB   := subCMBresidual inp
  let floor    := landauerFloor inp
  let deficit  := landauerDeficit inp
  let verdict :=
    if regime == ThermalRegime.SubZero then
      ThermalVerdict.RejectedSubZero
    else if regime == ThermalRegime.Plasma then
      ThermalVerdict.RejectedPlasma
    else if !landauerAdmissible inp then
      ThermalVerdict.RejectedLandauer
    else if subCMB > 0 then
      ThermalVerdict.AdmittedSubCMB
    else
      ThermalVerdict.Admitted
  { input := inp, regime, subCMBresidual := subCMB
  , landauerFloor := floor, landauerDeficit := deficit, verdict }

-- ═══════════════════════════════════════════════════════════════════
-- §6b  ThermalSuperposition Receipt
--
-- Rather than hard-rejecting plasma or sub-Landauer inputs, the
-- superposition receipt carries three regime weights that describe
-- *which* physics chart the input inhabits:
--
--   ε_classical  : Q16_16  — classical stat-mech weight (Boltzmann)
--   ε_quantum    : Q16_16  — quantum / Landauer-constrained weight
--   ε_hadronic   : Q16_16  — hadronic / quark-gluon plasma weight
--
-- The three weights sum to 65536 (= 1.0 in Q16_16).
-- Regime assignment rules:
--   SubZero    → inadmissible: all weights zero, `inadmissible = true`
--   Admitted / AdmittedSubCMB → ε_classical = 65536, others = 0
--   RejectedLandauer  → ε_quantum = 65536, others = 0
--   RejectedPlasma    → ε_hadronic = 65536, others = 0
--
-- This replaces hard-reject semantics with a typed receipt that can be
-- combined with downstream gates (e.g. HyperEigenSpectrum, BoundaryEigenFire).
-- ═══════════════════════════════════════════════════════════════════

/--
Three-regime thermal superposition receipt.
All weight fields are Q16_16; their sum is 65536 for any admissible input,
and 0 for inadmissible (SubZero) inputs.
-/
structure ThermalSuperposition where
  /-- Classical statistical mechanics weight (Boltzmann/equipartition valid). -/
  ε_classical : Q16_16
  /-- Quantum / Landauer-regime weight (quantum degenerate or sub-Landauer). -/
  ε_quantum   : Q16_16
  /-- Hadronic / plasma-phase weight (Hagedorn transition exceeded). -/
  ε_hadronic  : Q16_16
  /-- True iff the input is inadmissible (T ≤ 0 K). -/
  inadmissible : Bool
  deriving Repr, Inhabited

/--
Full thermal receipt extended with a ThermalSuperposition field.
-/
structure ThermalReceiptEx where
  input          : ThermalInput
  regime         : ThermalRegime
  subCMBresidual : Nat              -- mK below CMB; 0 if above CMB
  landauerFloor  : Nat              -- Landauer minimum in 10⁻²³ J per bit
  landauerDeficit: Nat              -- 0 if satisfied
  verdict        : ThermalVerdict
  superposition  : ThermalSuperposition
  deriving Repr, Inhabited

/--
Compute the `ThermalSuperposition` from a `ThermalVerdict`.

Weight assignment:
  `Admitted` / `AdmittedSubCMB` → ε_classical = 65536 (full classical)
  `RejectedLandauer`            → ε_quantum   = 65536 (quantum regime)
  `RejectedPlasma`              → ε_hadronic  = 65536 (plasma regime)
  `RejectedSubZero`             → inadmissible = true, all weights 0
-/
def superpositionFromVerdict (v : ThermalVerdict) : ThermalSuperposition :=
  match v with
  | ThermalVerdict.Admitted | ThermalVerdict.AdmittedSubCMB =>
      { ε_classical := ⟨65536⟩, ε_quantum := ⟨0⟩, ε_hadronic := ⟨0⟩
      , inadmissible := false }
  | ThermalVerdict.RejectedLandauer =>
      { ε_classical := ⟨0⟩, ε_quantum := ⟨65536⟩, ε_hadronic := ⟨0⟩
      , inadmissible := false }
  | ThermalVerdict.RejectedPlasma =>
      { ε_classical := ⟨0⟩, ε_quantum := ⟨0⟩, ε_hadronic := ⟨65536⟩
      , inadmissible := false }
  | ThermalVerdict.RejectedSubZero =>
      { ε_classical := ⟨0⟩, ε_quantum := ⟨0⟩, ε_hadronic := ⟨0⟩
      , inadmissible := true }

/--
Theorem: weight sum is 65536 for all admissible inputs (not SubZero).
-/
theorem superposition_weight_sum (v : ThermalVerdict) (h : v ≠ ThermalVerdict.RejectedSubZero) :
    let s := superpositionFromVerdict v
    s.ε_classical.val + s.ε_quantum.val + s.ε_hadronic.val = 65536 := by
  cases v <;> simp_all [superpositionFromVerdict]

/--
Extended thermal gate: combines the base `thermalGate` with a `ThermalSuperposition`
receipt, replacing hard-reject semantics with regime-typed weights.
-/
def thermalGateEx (inp : ThermalInput) : ThermalReceiptEx :=
  let base  := thermalGate inp
  let super := superpositionFromVerdict base.verdict
  { input          := base.input
  , regime         := base.regime
  , subCMBresidual := base.subCMBresidual
  , landauerFloor  := base.landauerFloor
  , landauerDeficit:= base.landauerDeficit
  , verdict        := base.verdict
  , superposition  := super }

-- ═══════════════════════════════════════════════════════════════════
-- §7  Witnesses
-- ═══════════════════════════════════════════════════════════════════

-- Room temperature (293 K) with adequate erasure budget → Admitted.
-- Landauer floor at 293 K ≈ 280 × 10⁻²³ J; budget=300 clears it.
#eval (thermalGate { temp_mK := 293000, energyBudget := 300, bitsToErase := 1 }).verdict
-- expected: ThermalVerdict.Admitted

-- Exactly at absolute zero → RejectedSubZero.
#eval (thermalGate { temp_mK := 0, energyBudget := 300, bitsToErase := 1 }).verdict
-- expected: ThermalVerdict.RejectedSubZero

-- Above Hagedorn ceiling → RejectedPlasma.
#eval (thermalGate { temp_mK := 1000000000000001, energyBudget := 300, bitsToErase := 1 }).verdict
-- expected: ThermalVerdict.RejectedPlasma

-- Sub-Landauer erasure at room temp → RejectedLandauer.
-- Budget = 1 × 10⁻²³ J << floor ≈ 280; correctly rejected.
#eval (thermalGate { temp_mK := 293000, energyBudget := 1, bitsToErase := 1 }).verdict
-- expected: ThermalVerdict.RejectedLandauer

-- 1 K (below CMB) with adequate budget, no erasure → AdmittedSubCMB (scar attached).
-- Landauer floor at 1 K ≈ 0.96 × 10⁻²³ J; bitsToErase=0 bypasses check.
#eval (thermalGate { temp_mK := 1000, energyBudget := 5, bitsToErase := 0 }).verdict
-- expected: ThermalVerdict.AdmittedSubCMB

-- Check the actual Landauer floor at room temperature (correctness witness).
#eval landauerFloor { temp_mK := 293000, energyBudget := 0, bitsToErase := 0 }
-- expected: 280  (1380649 × 293000 × 6931 / 10^13 ≈ 280.4 → truncated to 280)

-- CMB floor value stored as Q16_16 check.
#eval T_CMB
-- expected: ⟨178618⟩  (2.725 K × 65536)

-- ThermalSuperposition witnesses.

-- Admitted → full classical weight.
#eval (thermalGateEx { temp_mK := 293000, energyBudget := 300, bitsToErase := 1 }).superposition
-- expected: { ε_classical := ⟨65536⟩, ε_quantum := ⟨0⟩, ε_hadronic := ⟨0⟩, inadmissible := false }

-- Plasma input → full hadronic weight (not a hard reject; receives plasma receipt).
#eval (thermalGateEx { temp_mK := 1000000000000001, energyBudget := 300, bitsToErase := 1 }).superposition
-- expected: { ε_classical := ⟨0⟩, ε_quantum := ⟨0⟩, ε_hadronic := ⟨65536⟩, inadmissible := false }

-- Sub-Landauer input → full quantum weight (below Landauer floor; quantum regime receipt).
#eval (thermalGateEx { temp_mK := 293000, energyBudget := 1, bitsToErase := 1 }).superposition
-- expected: { ε_classical := ⟨0⟩, ε_quantum := ⟨65536⟩, ε_hadronic := ⟨0⟩, inadmissible := false }

-- SubZero input → inadmissible, all weights 0.
#eval (thermalGateEx { temp_mK := 0, energyBudget := 300, bitsToErase := 1 }).superposition
-- expected: { ε_classical := ⟨0⟩, ε_quantum := ⟨0⟩, ε_hadronic := ⟨0⟩, inadmissible := true }

-- ε_classical weight check directly from superpositionFromVerdict.
#eval (superpositionFromVerdict ThermalVerdict.Admitted).ε_classical
-- expected: ⟨65536⟩

-- ε_hadronic check for plasma verdict.
#eval (superpositionFromVerdict ThermalVerdict.RejectedPlasma).ε_hadronic
-- expected: ⟨65536⟩

-- ═══════════════════════════════════════════════════════════════════
-- §8  HCMMR Gate Bundle
-- ═══════════════════════════════════════════════════════════════════

/--
`A_thermal(inp)` : the HCMMR thermal boundary gate.

Returns `true` iff the thermal input is admitted (not sub-zero, not plasma,
Landauer-satisfied — SubCMB counts as admitted with scar).
-/
def A_thermal (inp : ThermalInput) : Bool :=
  let v := (thermalGate inp).verdict
  v == ThermalVerdict.Admitted || v == ThermalVerdict.AdmittedSubCMB

/--
`A_thermal` factor as Q16_16 weight.
Admitted = 65536; rejected = 0.
-/
def A_thermal_weight (inp : ThermalInput) : Q16_16 :=
  if A_thermal inp then ⟨65536⟩ else ⟨0⟩

#eval A_thermal_weight { temp_mK := 293000, energyBudget := 300, bitsToErase := 1 }
-- expected: ⟨65536⟩  (room-temp, admitted)

#eval A_thermal_weight { temp_mK := 0, energyBudget := 300, bitsToErase := 1 }
-- expected: ⟨0⟩  (absolute-zero floor, rejected)

end Semantics.HCMMR.Law21
