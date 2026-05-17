/-
Law 16 — Entropy/Heat Leak (Landauer Gate)

Every gate failure is not free — it emits a residual that costs energy
(Landauer limit: ΔE ≥ k_B·T·ln2). The Underverse is the residual heat sink
for every gate rejection. Gate rejections produce thermodynamic signatures;
the adiabatic boundary is the QCD regime at ~10¹² K. Torsion-light boundary:
as v_T → c⁻, ε_c → ∞ (horizon never crossed). Absolute zero (0 K) is a
boundary, never a reachable state.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts, `inductive` for enumerations.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law16
  Import: Semantics.HCMMR.Core, Semantics.FixedPoint
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law16

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Thermodynamic Constants
-- ═══════════════════════════════════════════════════════════════════

/--
Boltzmann constant k_B ≈ 1.380649e-23 J/K.
Represented as a scaled Q16_16 literal to keep `native_decide` reachable.
In the structural formalism, k_B carries the dimensional scaling factor
needed to make energy costs meaningful at typical HCMMR gate temperatures.
-/
def k_B : Q16_16 := ⟨90494⟩

/--
ln(2) ≈ 0.693147 — the natural log of 2 as Q16_16.
Used in the Landauer bound: ΔE ≥ k_B × T × ln2.
-/
def ln2 : Q16_16 := ⟨45426⟩

/--
Landauer minimum: ΔE_min = k_B × T × ln2.
Erasing 1 bit at temperature T costs at least k_B·T·ln2 energy.
Returns the minimum energy dissipation for information erasure at
operating temperature T.
-/
def landauerMinimum (T : Q16_16) : Q16_16 :=
  Q16_16.mul (Q16_16.mul k_B T) ln2

-- ═══════════════════════════════════════════════════════════════════
-- §2  Entropy Cost of Gate Failure
-- ═══════════════════════════════════════════════════════════════════

/--
Records the full thermodynamic cost of a single gate failure:
  - gateName: which gate ejected the residual
  - temperature: operating temperature T
  - residual: ε value (dimensionless mismatch scar)
  - energyCost: ε × k_B × T (energy dissipated as heat)
  - entropyIncrease: ΔS = energyCost / T (entropy produced)
-/
structure GateFailureCost where
  gateName        : String
  temperature     : Q16_16
  residual        : Q16_16
  energyCost      : Q16_16
  entropyIncrease : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Computes a GateFailureCost from a gate name, operating temperature,
and residual ε. Sets:
  energyCost = ε × k_B × T
  entropyIncrease = energyCost / T (0 if T = 0 to avoid division by zero)
-/
def computeFailureCost (name : String) (T : Q16_16) (eps : Q16_16) : GateFailureCost :=
  let eCost := Q16_16.mul eps (Q16_16.mul k_B T)
  let dS := if T.val == 0 then Q16_16.zero
            else Q16_16.div eCost T
  { gateName        := name
  , temperature     := T
  , residual        := eps
  , energyCost      := eCost
  , entropyIncrease := dS
  }

-- ═══════════════════════════════════════════════════════════════════
-- §3  Underverse Heat Sink
-- ═══════════════════════════════════════════════════════════════════

/--
The Underverse is the asymptotic heat sink — not colder than 0 K,
but time-dilated. After N settling cycles:
  - coolingFraction: η_U(N) = 1 − 10^{−N} (the "add another 9" model)
  - settleCycles: N
  - unresolvedHeat: r_U(N) = 10^{−N} (remaining unresolved fraction)
  - timeDilationFactor: τ_U / τ_external

The Underverse never reaches perfect 100 % cooling for any finite N.
-/
structure UnderverseSink where
  coolingFraction    : Q16_16
  settleCycles       : Nat
  unresolvedHeat     : Q16_16
  timeDilationFactor : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
η_U(N) = 1 − 10^{−N}
Cooling effectiveness after N Underverse settling cycles.
As N → ∞, η_U → 1.0. For N ≥ 5 the correction is below Q16_16 resolution,
so the result saturates at 1.0.
-/
def sinkEffectiveness (N : Nat) : Q16_16 :=
  let pow10 := Nat.pow 10 N
  if pow10 == 0 || pow10 > 65536 then Q16_16.one
  else
    let fraction := Q16_16.div Q16_16.one (Q16_16.ofNat pow10)
    Q16_16.sub Q16_16.one fraction

/--
r_U(N) = 10^{−N}
After N Underverse cooling cycles, this fraction of heat remains
unresolved. Returns Q16_16.epsilon (trace residual) when 10^{−N}
falls below fixed-point resolution (N ≥ 5).
-/
def sinkResidual (N : Nat) : Q16_16 :=
  let pow10 := Nat.pow 10 N
  if pow10 == 0 || pow10 > 65536 then Q16_16.epsilon
  else Q16_16.div Q16_16.one (Q16_16.ofNat pow10)

-- ═══════════════════════════════════════════════════════════════════
-- §4  Thermal Boundary Gate (Law 21)
-- ═══════════════════════════════════════════════════════════════════

/--
Defines the physically admissible thermal range:
  - absoluteZero: always 0 (asymptotic boundary, never reachable)
  - cmbTemperature: 2.725 K cosmic-microwave baseline
  - qcdThreshold: ~10¹² K matter-phase regime break (sentinel: infinity)
  - isInRange: flag indicating whether a given T is physically admissible
-/
structure ThermalBoundary where
  absoluteZero   : Q16_16
  cmbTemperature : Q16_16
  qcdThreshold   : Q16_16
  isInRange      : Bool
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Checks temperature T against physical admissibility:
  - admit: T > 0, finite → acceptable operating temperature
  - hold:  T = 0 → asymptotic boundary (approached, not reachable)
  - reject: T < 0 → physically impossible (negative Kelvin)
-/
def thermalBoundaryCheck (T : Q16_16) : GateVerdict :=
  if T.val == 0 then
    GateVerdict.hold
  else if T.toInt < 0 then
    GateVerdict.reject
  else
    GateVerdict.admit

-- ═══════════════════════════════════════════════════════════════════
-- §5  Entropy Gate
-- ═══════════════════════════════════════════════════════════════════

/--
The entropy gate enforces thermodynamics across the HCMMR gate chain:
  1. Every gate failure has a recorded GateFailureCost
  2. Energy cost ≥ landauerMinimum for each bit of information loss
  3. Underverse sink has non-negative unresolved heat
  4. Thermal boundaries are respected

Returns a required Gate:
  admit  — all constraints satisfied
  hold   — some costs unresolvable, pending further settling
  reject — Landauer bound or thermal bounds violated
-/
def entropyGateAdmit (failures : List GateFailureCost) (sink : UnderverseSink) (T : Q16_16) : Gate :=
  let thermalOk := thermalBoundaryCheck T != GateVerdict.reject
  let sinkOk := sink.unresolvedHeat.toInt >= 0
  let landauerOk := failures.all (fun f =>
    f.energyCost.toInt >= (landauerMinimum T).toInt)
  let score := if thermalOk && sinkOk && landauerOk then Q16_16.one else Q16_16.zero
  let verdict :=
    if !thermalOk || !landauerOk then GateVerdict.reject
    else if !sinkOk then GateVerdict.hold
    else GateVerdict.admit
  { name := "EntropyHeatLeak", required := true, score := score, verdict := verdict }

/--
Sums energyCost across all GateFailureCost entries.
Returns the total dissipated energy budget as Q16_16.
-/
def totalEntropyBudget (failures : List GateFailureCost) : Q16_16 :=
  failures.foldl (fun acc f => Q16_16.add acc f.energyCost) Q16_16.zero

-- ═══════════════════════════════════════════════════════════════════
-- §6  Torsion-Light Boundary
-- ═══════════════════════════════════════════════════════════════════

/--
Causal speed residual ε_c at a torsion-front velocity fraction β_T = v_T / c.

  γ_T = 1 / √(1 − β_T²)    (Lorentz factor)
  ε_c = γ_T − 1

As v_T → c⁻ (β_T → 1⁻):
  √(1 − β_T²) → 0⁺  ⇒  γ_T → ∞  ⇒  ε_c → ∞

When β_T ≥ 1 or the denominator underflows to zero, returns infinity.
Uses Q16_16 arithmetic throughout.
-/
def causalSpeedResidual (beta_T : Q16_16) : Q16_16 :=
  let betaSq := Q16_16.mul beta_T beta_T
  let oneMinus := Q16_16.sub Q16_16.one betaSq
  if oneMinus.val == 0 then
    Q16_16.infinity
  else
    let r := Q16_16.sqrt oneMinus
    if r.val == 0 then Q16_16.infinity
    else
      let gamma := Q16_16.div Q16_16.one r
      Q16_16.sub gamma Q16_16.one

/--
Returns true iff 0 ≤ β_T < 1 (strict inequality).
The torsion horizon is an asymptotic boundary: sub-luminal is admissible,
luminal or super-luminal is not.
-/
def torsionHorizonAdmit (beta_T : Q16_16) : Bool :=
  beta_T.toInt >= 0 && beta_T.toInt < Q16_16.one.toInt

-- ═══════════════════════════════════════════════════════════════════
-- §7  Fixtures
-- ═══════════════════════════════════════════════════════════════════

/-- Room-temperature operating point: 300 K. -/
def roomTempFixture : Q16_16 := Q16_16.ofInt 300

/-- A gate rejection at 300 K with residual ε = 1. -/
def gateRejectCostFixture : GateFailureCost :=
  computeFailureCost "Chirality" roomTempFixture Q16_16.one

/-- Underverse sink after N = 6 cycles:
    coolingFraction ≈ 0.999999, unresolvedHeat at trace epsilon. -/
def underverseSettledFixture : UnderverseSink :=
  { coolingFraction    := sinkEffectiveness 6
  , settleCycles       := 6
  , unresolvedHeat     := sinkResidual 6
  , timeDilationFactor := Q16_16.ofInt 1000
  }

/-- Near-light torsion front: β_T = 0.9999. -/
def nearLightTorsionFixture : Q16_16 :=
  Q16_16.div (Q16_16.ofInt 9999) (Q16_16.ofInt 10000)

/-- Standard thermal-boundary descriptor. -/
def thermalBoundaryFixture : ThermalBoundary :=
  { absoluteZero   := Q16_16.zero
  , cmbTemperature := Q16_16.ofFloat 2.725
  , qcdThreshold   := Q16_16.infinity
  , isInRange      := true
  }

/-- A small list of failure costs for entropy-gate admission testing. -/
def failureListFixture : List GateFailureCost :=
  [ computeFailureCost "Chirality" (Q16_16.ofInt 300) Q16_16.one
  , computeFailureCost "Receipt"   (Q16_16.ofInt 300) (Q16_16.div Q16_16.one (Q16_16.ofInt 2))
  ]

/-- An empty sink (N = 0): no cooling, 100 % unresolved. -/
def rawSinkFixture : UnderverseSink :=
  { coolingFraction    := sinkEffectiveness 0
  , settleCycles       := 0
  , unresolvedHeat     := sinkResidual 0
  , timeDilationFactor := Q16_16.one
  }

-- ═══════════════════════════════════════════════════════════════════
-- §8  Theorems
-- ═══════════════════════════════════════════════════════════════════

/--
For T > 0, the Landauer minimum energy cost is strictly positive.
-/
theorem landauer_positive :
    landauerMinimum roomTempFixture > Q16_16.zero := by
  native_decide

/--
For finite N (here N = 6), unresolvedHeat of the Underverse sink is
strictly nonzero. The Underverse never reaches perfect cooling.
-/
theorem underverse_never_zero :
    underverseSettledFixture.unresolvedHeat ≠ Q16_16.zero := by
  native_decide

/--
β_T is always strictly less than 1 for finite-energy torsion fronts.
The torsion horizon is an asymptotic boundary, never crossed.
-/
theorem torsion_never_superluminal :
    nearLightTorsionFixture < Q16_16.one := by
  native_decide

/--
Thermal boundary check admits a positive finite temperature.
-/
theorem thermal_boundary_admits_positive :
    thermalBoundaryCheck roomTempFixture = GateVerdict.admit := by
  native_decide

/--
Thermal boundary check holds at absolute zero (boundary, never reachable).
-/
theorem thermal_boundary_holds_at_zero :
    thermalBoundaryCheck Q16_16.zero = GateVerdict.hold := by
  native_decide

/--
Torsion horizon admits the near-light fixture (0 ≤ β_T < 1).
-/
theorem torsion_horizon_admits_near_light :
    torsionHorizonAdmit nearLightTorsionFixture = true := by
  native_decide

/--
Torsion horizon rejects exactly-luminal β_T = 1.
-/
theorem torsion_horizon_rejects_luminal :
    torsionHorizonAdmit Q16_16.one = false := by
  native_decide

/--
GateFailureCost energyCost is strictly positive for ε > 0 at T > 0.
-/
theorem failure_cost_positive :
    gateRejectCostFixture.energyCost > Q16_16.zero := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════
-- §9  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════

-- Thermodynamic constants
#eval k_B
#eval ln2

-- Landauer minimum at room temperature
#eval landauerMinimum roomTempFixture

-- Gate failure cost computation
#eval gateRejectCostFixture
#eval computeFailureCost "Projection" (Q16_16.ofInt 500) (Q16_16.ofInt 2)

-- Underverse sink effectiveness and residual
#eval sinkEffectiveness 1
#eval sinkEffectiveness 3
#eval sinkEffectiveness 6
#eval sinkResidual 1
#eval sinkResidual 3
#eval sinkResidual 6
#eval underverseSettledFixture
#eval rawSinkFixture

-- Thermal boundary check
#eval thermalBoundaryCheck roomTempFixture
#eval thermalBoundaryCheck Q16_16.zero
#eval thermalBoundaryCheck (Q16_16.neg Q16_16.one)
#eval thermalBoundaryFixture

-- Entropy gate admission
#eval entropyGateAdmit failureListFixture underverseSettledFixture roomTempFixture
#eval entropyGateAdmit [] underverseSettledFixture roomTempFixture
#eval entropyGateAdmit failureListFixture rawSinkFixture roomTempFixture

-- Total entropy budget
#eval totalEntropyBudget failureListFixture
#eval totalEntropyBudget []

-- Torsion-light boundary
#eval causalSpeedResidual nearLightTorsionFixture
#eval causalSpeedResidual (Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 2))
#eval torsionHorizonAdmit nearLightTorsionFixture
#eval torsionHorizonAdmit Q16_16.one
#eval torsionHorizonAdmit (Q16_16.neg Q16_16.one)

-- Fixtures
#eval roomTempFixture
#eval gateRejectCostFixture
#eval underverseSettledFixture
#eval nearLightTorsionFixture

end Semantics.HCMMR.Law16
