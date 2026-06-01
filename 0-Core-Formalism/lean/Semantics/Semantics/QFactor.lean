import Semantics.FixedPoint

namespace Semantics.QFactor

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q-Factor Energy Balance Equation
-- 
-- The Q-Factor equation describes global energy balance:
-- Q = (E_flash + E_enthalpy + E_recovered - W_demon) / (E_work + E_loss) > 1.0
-- 
-- where:
-- - Q = Quality factor (> 1.0 indicates net energy gain)
-- - E_flash = Flash energy (rapid energy release)
-- - E_enthalpy = Enthalpy (heat content)
-- - E_recovered = Recovered energy
-- - W_demon = Maxwell's Demon work (erasure cost)
-- - E_work = Work energy
-- - E_loss = Energy loss
-- 
-- For agents:
-- - E_flash = Burst computation energy
-- - E_enthalpy = Steady-state energy
-- - E_recovered = Energy from optimizations
-- - W_demon = Landauer limit for information erasure
-- - E_work = Useful work energy
-- - E_loss = Waste energy
-- 
-- Target: Q ≈ 1.05 (5% net energy gain)
-- ═══════════════════════════════════════════════════════════════════════════

structure EnergyBalance where
  flashEnergy : Q16_16
  enthalpy : Q16_16
  recoveredEnergy : Q16_16
  demonWork : Q16_16
  workEnergy : Q16_16
  energyLoss : Q16_16
  deriving Repr, Inhabited

structure QFactorState where
  agentId : UInt64
  balance : EnergyBalance
  qFactor : Q16_16
  targetQ : Q16_16
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Q-Factor Calculation
-- ═══════════════════════════════════════════════════════════════════════════

def calculateQFactor (balance : EnergyBalance) : Q16_16 :=
  let numerator := balance.flashEnergy + balance.enthalpy + balance.recoveredEnergy - balance.demonWork
  let denominator := balance.workEnergy + balance.energyLoss
  if denominator > zero then
    numerator / denominator
  else
    zero

def meetsTargetQ (state : QFactorState) : Bool :=
  state.qFactor >= state.targetQ

def hasNetEnergyGain (state : QFactorState) : Bool :=
  state.qFactor > one

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Energy Balance Optimization
-- ═══════════════════════════════════════════════════════════════════════════

def energySurplus (balance : EnergyBalance) : Q16_16 :=
  let totalGain := balance.flashEnergy + balance.enthalpy + balance.recoveredEnergy
  let totalCost := balance.demonWork + balance.workEnergy + balance.energyLoss
  totalGain - totalCost

def energyEfficiencyFromBalance (balance : EnergyBalance) : Q16_16 :=
  let totalEnergyCost := balance.workEnergy + balance.energyLoss
  if totalEnergyCost > zero then
    balance.workEnergy / totalEnergyCost
  else
    zero

def recoveryRatio (balance : EnergyBalance) : Q16_16 :=
  let totalInputEnergy := balance.flashEnergy + balance.enthalpy
  if totalInputEnergy > zero then
    balance.recoveredEnergy / totalInputEnergy
  else
    zero

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Bind Primitive for Q-Factor Optimization
-- ═══════════════════════════════════════════════════════════════════════════

structure QFactorAction where
  agentId : UInt64
  flashEnergyDelta : Q16_16
  enthalpyDelta : Q16_16
  recoveredEnergyDelta : Q16_16
  workEnergyDelta : Q16_16
  energyLossDelta : Q16_16
  deriving Repr, Inhabited

structure QFactorBind where
  lawful : Bool
  qFactorBefore : Q16_16
  qFactorAfter : Q16_16
  energySurplus : Q16_16
  invariant : String
  deriving Repr, Inhabited

def updateEnergyBalance (balance : EnergyBalance) (action : QFactorAction) : EnergyBalance :=
  {
    flashEnergy := balance.flashEnergy + action.flashEnergyDelta,
    enthalpy := balance.enthalpy + action.enthalpyDelta,
    recoveredEnergy := balance.recoveredEnergy + action.recoveredEnergyDelta,
    demonWork := balance.demonWork,
    workEnergy := balance.workEnergy + action.workEnergyDelta,
    energyLoss := balance.energyLoss + action.energyLossDelta
  }

def isQFactorActionLawful (state : QFactorState) (action : QFactorAction) : Bool :=
  let workPositive := state.balance.workEnergy + action.workEnergyDelta > zero
  let lossReasonable := action.energyLossDelta >= (-state.balance.energyLoss / ofNat 2)
  let recoveredReasonable := action.recoveredEnergyDelta >= zero ∨ action.recoveredEnergyDelta >= (-state.balance.recoveredEnergy / ofNat 2)
  let surplusNonnegative := energySurplus (updateEnergyBalance state.balance action) >= zero
  workPositive ∧ lossReasonable ∧ recoveredReasonable ∧ surplusNonnegative

def qFactorBind (state : QFactorState) (action : QFactorAction) : QFactorBind :=
  let lawful := isQFactorActionLawful state action
  let newBalance := if lawful then updateEnergyBalance state.balance action else state.balance
  let qFactorBefore := state.qFactor
  let qFactorAfter := if lawful then calculateQFactor newBalance else state.qFactor
  let surplus := if lawful then energySurplus newBalance else zero
  
  {
    lawful := lawful,
    qFactorBefore := qFactorBefore,
    qFactorAfter := qFactorAfter,
    energySurplus := surplus,
    invariant := if lawful then "energy_balance_satisfied" else "energy_constraint_violated"
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Invariant Preservation Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/--
Lawful transitions preserve non-negative energy surplus.
The lawfulness gate now includes the post-action surplus check; the current
surplus premise is retained for call-site compatibility and audit context.
-/
theorem lawful_preserves_non_negative_surplus (state : QFactorState) (action : QFactorAction)
    (_hSurplus : energySurplus state.balance ≥ zero)
    (hLawful : isQFactorActionLawful state action) :
    let bind := qFactorBind state action
    bind.energySurplus ≥ zero := by
  dsimp
  unfold qFactorBind
  simp [hLawful]
  unfold isQFactorActionLawful at hLawful
  have hLawfulProp := of_decide_eq_true hLawful
  simpa using hLawfulProp.right.right.right

/--
Lawful transitions with positive energy surplus preserve the invariant string.
-/
theorem lawful_preserves_invariant_string (state : QFactorState) (action : QFactorAction)
    (hLawful : isQFactorActionLawful state action) :
    (qFactorBind state action).invariant = "energy_balance_satisfied" := by
  unfold qFactorBind
  simp [hLawful]

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  #eval Examples
-- ═══════════════════════════════════════════════════════════════════════════

#eval calculateQFactor {
  flashEnergy := Q16_16.ofFloat 100.0,
  enthalpy := Q16_16.ofFloat 50.0,
  recoveredEnergy := Q16_16.ofFloat 30.0,
  demonWork := Q16_16.ofFloat 20.0,
  workEnergy := Q16_16.ofFloat 80.0,
  energyLoss := Q16_16.ofFloat 10.0
}

#eval calculateQFactor {
  flashEnergy := Q16_16.ofFloat 50.0,
  enthalpy := Q16_16.ofFloat 30.0,
  recoveredEnergy := Q16_16.ofFloat 20.0,
  demonWork := Q16_16.ofFloat 20.0,
  workEnergy := Q16_16.ofFloat 60.0,
  energyLoss := Q16_16.ofFloat 20.0
}

#eval energySurplus {
  flashEnergy := Q16_16.ofFloat 100.0,
  enthalpy := Q16_16.ofFloat 50.0,
  recoveredEnergy := Q16_16.ofFloat 30.0,
  demonWork := Q16_16.ofFloat 20.0,
  workEnergy := Q16_16.ofFloat 80.0,
  energyLoss := Q16_16.ofFloat 10.0
}

#eval energyEfficiencyFromBalance {
  flashEnergy := Q16_16.ofFloat 100.0,
  enthalpy := Q16_16.ofFloat 50.0,
  recoveredEnergy := Q16_16.ofFloat 30.0,
  demonWork := Q16_16.ofFloat 20.0,
  workEnergy := Q16_16.ofFloat 80.0,
  energyLoss := Q16_16.ofFloat 10.0
}

#eval recoveryRatio {
  flashEnergy := Q16_16.ofFloat 100.0,
  enthalpy := Q16_16.ofFloat 50.0,
  recoveredEnergy := Q16_16.ofFloat 30.0,
  demonWork := Q16_16.ofFloat 20.0,
  workEnergy := Q16_16.ofFloat 80.0,
  energyLoss := Q16_16.ofFloat 10.0
}

#eval qFactorBind {
  agentId := 1,
  balance := {
    flashEnergy := Q16_16.ofFloat 100.0,
    enthalpy := Q16_16.ofFloat 50.0,
    recoveredEnergy := Q16_16.ofFloat 30.0,
    demonWork := Q16_16.ofFloat 20.0,
    workEnergy := Q16_16.ofFloat 80.0,
    energyLoss := Q16_16.ofFloat 10.0
  },
  qFactor := Q16_16.ofFloat 1.78,
  targetQ := Q16_16.ofFloat 1.05
} {
  agentId := 1,
  flashEnergyDelta := Q16_16.ofFloat 10.0,
  enthalpyDelta := Q16_16.ofFloat 5.0,
  recoveredEnergyDelta := Q16_16.ofFloat 5.0,
  workEnergyDelta := Q16_16.ofFloat 10.0,
  energyLossDelta := Q16_16.ofFloat 2.0
}

end Semantics.QFactor
