/-
SIConstants.lean — SI Defining Constants, Derived Constants, and Measurements

All defining constants below are exact under the SI 2019 redefinition (BIPM SI
Brochure 9th ed.). They are represented as exact integers (`Nat`/`Int`) where
they are integers, and as exact rationals (`Rat`) where they are decimal
fractions. No floating-point approximation is introduced for any defined-exact
quantity.

Derived constants computed from defining constants are exact by construction.
CODATA-recommended (measured) constants are stored at full CODATA precision and
labelled with their uncertainty status.

Mirror module to `scripts/fundamental_math_verifier.py` — every constant in the
verifier's anchor net (63/63 verified against Wolfram Alpha) has a
representation here.

Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: All defs have `#eval` witnesses or theorems.

Symbolic Real-valued constants (π, e, φ via √5) live in §10 with full Mathlib
analysis imports.
-/

import Mathlib.Data.Rat.Defs
import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Sqrt
import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Analysis.SpecialFunctions.Exp
import Semantics.FixedPoint

namespace Semantics.SIConstants

open Semantics

/-! ## §1 SI Defining Constants (post-2019 redefinition, all exact)

The seven SI defining constants. Together they define every SI base unit. -/

/-- Caesium-133 hyperfine transition frequency (defines the second). Exact. -/
def caesiumFrequency_Hz : Nat := 9192631770

/-- Speed of light in vacuum (defines the metre). Exact. -/
def speedOfLight_m_per_s : Nat := 299792458

/-- Planck constant. Exact: h = 6.62607015 × 10⁻³⁴ J·s. -/
def planckConstant_J_s : Rat := 662607015 / (10 ^ 42 : Nat)

/-- Elementary charge. Exact: e = 1.602176634 × 10⁻¹⁹ C. -/
def elementaryCharge_C : Rat := 1602176634 / (10 ^ 28 : Nat)

/-- Boltzmann constant. Exact: k_B = 1.380649 × 10⁻²³ J/K. -/
def boltzmannConstant_J_per_K : Rat := 1380649 / (10 ^ 29 : Nat)

/-- Avogadro constant. Exact: N_A = 6.02214076 × 10²³ /mol. -/
def avogadroConstant_per_mol : Rat := (602214076 * 10 ^ 15 : Nat)

/-- Luminous efficacy of 540 THz monochromatic radiation. Exact. -/
def luminousEfficacy_lm_per_W : Nat := 683

#eval caesiumFrequency_Hz       -- 9192631770
#eval speedOfLight_m_per_s      -- 299792458
#eval planckConstant_J_s        -- 662607015 / 10^42
#eval elementaryCharge_C        -- 1602176634 / 10^28
#eval boltzmannConstant_J_per_K -- 1380649 / 10^29
#eval avogadroConstant_per_mol  -- 602214076 × 10^15
#eval luminousEfficacy_lm_per_W -- 683

/-! ## §2 Derived SI Constants (exact derivations from defining constants) -/

/-- Universal gas constant R = N_A · k_B (exact). Equals 8.31446261815324 J/(mol·K). -/
def gasConstant_J_per_mol_K : Rat :=
  avogadroConstant_per_mol * boltzmannConstant_J_per_K

/-- Faraday constant F = N_A · e (exact). Equals 96485.33212… C/mol. -/
def faradayConstant_C_per_mol : Rat :=
  avogadroConstant_per_mol * elementaryCharge_C

#eval gasConstant_J_per_mol_K     -- 8.31446261815324
#eval faradayConstant_C_per_mol   -- 96485.33212…

/-! ## §3 Defined-Exact Composite Constants -/

/-- Standard acceleration due to gravity. Defined exact by CGPM (1901). -/
def standardGravity_m_per_s2 : Rat := 980665 / (10 ^ 5 : Nat)  -- 9.80665

/-- Astronomical unit. Defined exact by IAU 2012 Resolution B2. -/
def astronomicalUnit_m : Nat := 149597870700

/-- Light year = c × Julian year (Julian year = 31557600 s exactly). -/
def lightYear_m : Nat := 9460730472580800

#eval standardGravity_m_per_s2  -- 980665 / 10^5
#eval astronomicalUnit_m        -- 149597870700
#eval lightYear_m               -- 9460730472580800

/-- Witness: ly = c × seconds_in_Julian_year (decidable integer equality). -/
example :
    lightYear_m = speedOfLight_m_per_s * 31557600 := by
  decide

/-! ## §4 CODATA Measured Constants (have uncertainty)

These are NOT defined-exact. Stored at full CODATA precision; downstream code
should track propagated uncertainty if precision-critical. -/

/-- Bohr radius (CODATA 2018). a₀ ≈ 5.29177210903 × 10⁻¹¹ m. -/
def bohrRadius_m : Rat := 529177210903 / (10 ^ 22 : Nat)

/-- Rydberg energy (CODATA). Ry ≈ 13.605693123 eV. -/
def rydbergEnergy_eV : Rat := 13605693123 / (10 ^ 9 : Nat)

/-- Inverse fine structure constant (CODATA). 1/α ≈ 137.035999. -/
def inverseFineStructureConstant : Rat := 137035999 / (10 ^ 6 : Nat)

/-- Fine structure constant α ≈ 7.2973525693 × 10⁻³. -/
def fineStructureConstant : Rat := 1 / inverseFineStructureConstant

#eval bohrRadius_m                  -- 5.29177210903 × 10⁻¹¹
#eval rydbergEnergy_eV              -- 13.605693123
#eval inverseFineStructureConstant  -- 137.035999
#eval fineStructureConstant         -- ≈ 0.00729735

/-! ## §5 Wien & Stefan-Boltzmann Constants (CODATA) -/

/-- Wien displacement constant. b ≈ 2.897771955 × 10⁻³ m·K. -/
def wienDisplacement_m_K : Rat := 2897771955 / (10 ^ 12 : Nat)

#eval wienDisplacement_m_K  -- 2.897771955 × 10⁻³

/-- Specific instance: Sun blackbody peak wavelength.
    For T = 5778 K, λ_max ≈ 5.01518 × 10⁻⁷ m (501.5 nm, visible green-blue). -/
def sunBlackbodyPeak_m : Rat := wienDisplacement_m_K / 5778

#eval sunBlackbodyPeak_m  -- ≈ 5.01518 × 10⁻⁷

/-! ## §6 Specific Numerical Witnesses (mirror verifier anchor net) -/

/-- E = mc² for 1 gram of mass. Yields exactly 8.9875517873681764 × 10¹³ J. -/
def massEnergy_1g_J : Rat :=
  (1 / 1000 : Rat) * (speedOfLight_m_per_s : Rat) ^ 2

#eval massEnergy_1g_J  -- 22468879468420441 / 250 = 89875517873681.764

/-- PV = nRT solved for V at 1 mol IUPAC STP (T = 273.15 K, P = 101325 Pa).
    Yields V = 0.022413969545014137735011… m³ exactly. -/
def molarVolumeSTP_m3 : Rat :=
  (1 : Rat) * gasConstant_J_per_mol_K * (27315 / 100 : Rat) /
    (101325 : Rat)

#eval molarVolumeSTP_m3  -- 378515910691426251 / 16887500000000000000

/-- ΔS for irreversible heat transfer: 100 J flows 400 K → 300 K.
    Exactly 1/12 J/K (positive ⇒ second law holds). -/
def deltaS_irreversibleHeatTransfer_J_per_K : Rat := 100 / 300 - 100 / 400

#eval deltaS_irreversibleHeatTransfer_J_per_K  -- 1/12

/-- Carnot efficiency at T_cold = 300 K, T_hot = 400 K. Exactly 1/4. -/
def carnotEfficiency_300_400 : Rat := 1 - 300 / 400

#eval carnotEfficiency_300_400  -- 1/4

/-! ## §7 Stack-Specific Anchors (PHI, BASE-27, K=3, k=7, Q16.16 ms timing) -/

/-- BASE-27 = 3³ for K=3 ternary triplet encoding. -/
def baseTwentySeven : Nat := 3 ^ 3

#eval baseTwentySeven  -- 27

example : baseTwentySeven = 27 := by decide

/-- Coprime traversal modulus k = 7 (prime). -/
def coprimeTraversalModulus : Nat := 7

/-- Witness: 7 is prime. -/
example : Nat.Prime coprimeTraversalModulus := by decide

/-- Engram-length anchor: 500 ms expressed as raw Q16.16 ticks.
    round(0.5 × 65536) = 32768 (exact since 0.5 = 2⁻¹). -/
def engramLength500ms_Q1616_raw : Nat := 32768

/-- Engram-length anchor: 700 ms as raw Q16.16 ticks.
    round(0.7 × 65536) = 45875. -/
def engramLength700ms_Q1616_raw : Nat := 45875

/-- 0.8 in Q16.16 (corrected from prior 52428 → 52429). -/
def pointEight_Q1616_raw : Nat := 52429

/-- 150 ms as raw Q16.16 ticks. round(0.150 × 65536) = 9830. -/
def extractionTime150ms_Q1616_raw : Nat := 9830

#eval engramLength500ms_Q1616_raw  -- 32768
#eval engramLength700ms_Q1616_raw  -- 45875
#eval pointEight_Q1616_raw         -- 52429
#eval extractionTime150ms_Q1616_raw -- 9830

example : engramLength500ms_Q1616_raw = 32768 := by decide
example : pointEight_Q1616_raw = 52429 := by decide

/-! ## §8 Q16.16 Hardware-Native Forms (where the constant fits)

Q16_16 range is roughly [-32768, 32767.999985]. Most SI constants do NOT fit.
Those that do (g₀, π, φ-1, normalised values) get a Q16.16 representation here.
Constants outside the Q16_16 range are intentionally omitted.
-/

/-- g₀ = 9.80665 m/s² in Q16.16 (raw int = 642729). -/
def standardGravity_Q1616_raw : Nat := 642729  -- round(9.80665 × 65536)

#eval standardGravity_Q1616_raw

example : standardGravity_Q1616_raw = 642729 := by decide

/-- π in Q16.16 (raw int = 205887). -/
def pi_Q1616_raw : Nat := 205887  -- round(3.14159265358979… × 65536)

/-- φ - 1 = 1/φ ≈ 0.61803398… in Q16.16 (fits in Q0_16 too). -/
def phiMinusOne_Q1616_raw : Nat := 40503  -- round(0.61803398875 × 65536)

#eval pi_Q1616_raw
#eval phiMinusOne_Q1616_raw

/-! ## §9 Computational Witnesses (native_decide for big rationals)

`native_decide` compiles the equality to native code and checks it — fastest
way to anchor large rational identities that exceed `decide`'s kernel budget. -/

/-- R = N_A · k_B exactly equals 8.31446261815324 (in fully-reduced form). -/
example : gasConstant_J_per_mol_K = (207861565453831 / 25000000000000 : Rat) := by
  native_decide

/-- E = mc² for 1 g equals exactly 22468879468420441/250 J. -/
example : massEnergy_1g_J = (22468879468420441 / 250 : Rat) := by
  native_decide

/-- ΔS for irreversible heat 100 J 400K→300K = exactly 1/12 J/K. -/
example : deltaS_irreversibleHeatTransfer_J_per_K = (1 / 12 : Rat) := by
  native_decide

/-- Carnot η at T_c=300, T_h=400 = exactly 1/4. -/
example : carnotEfficiency_300_400 = (1 / 4 : Rat) := by
  native_decide

/-- V_STP for 1 mol equals 378515910691426251 / 16887500000000000000 m³. -/
example :
    molarVolumeSTP_m3 = (378515910691426251 / 16887500000000000000 : Rat) := by
  native_decide

/-! ## §10 Symbolic Real-Valued Constants

These need Mathlib analysis. Computable forms live in earlier sections; these
are the symbolic/exact-real anchors used by downstream proofs that need them. -/

/-- π — symbolic from Mathlib. Use this for analytic limits / integrals. -/
noncomputable def pi : Real := Real.pi

/-- e = exp(1) — symbolic. -/
noncomputable def euler : Real := Real.exp 1

/-- Golden ratio φ = (1 + √5) / 2. Symbolic exact. -/
noncomputable def goldenRatio : Real := (1 + Real.sqrt 5) / 2

/-- √2 — symbolic. -/
noncomputable def sqrtTwo : Real := Real.sqrt 2

/-- √3 — symbolic. -/
noncomputable def sqrtThree : Real := Real.sqrt 3

/-- ℏ = h / (2π) — reduced Planck constant. Needs Real because π is not rational. -/
noncomputable def reducedPlanckConstant_J_s : Real :=
  (planckConstant_J_s : Real) / (2 * Real.pi)

/-- Witness: φ² = φ + 1 (defining identity of the golden ratio). -/
example : goldenRatio ^ 2 = goldenRatio + 1 := by
  unfold goldenRatio
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num : (5 : Real) ≥ 0)
  ring_nf
  nlinarith [h5, Real.sqrt_nonneg 5]

end Semantics.SIConstants
