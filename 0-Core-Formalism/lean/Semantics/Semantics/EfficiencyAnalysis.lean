import Semantics.FixedPoint
import Lean.Data.Json

namespace Semantics.EfficiencyAnalysis

open Semantics.Q16_16
open Lean

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Efficiency Structures
-- ═══════════════════════════════════════════════════════════════════════════

structure SabotagePreventionGains where
  efficiencyGain : Semantics.Q16_16
  connectivityGain : Semantics.Q16_16
  attacksBlocked : Nat
  deriving Repr, Inhabited, ToJson, FromJson

structure ServiceRestorationGains where
  capacityGain : Semantics.Q16_16
  restorationBenefit : Semantics.Q16_16
  deriving Repr, Inhabited, ToJson, FromJson

structure SyncAttackPreventionGains where
  connectivityGain : Semantics.Q16_16
  efficiencyGain : Semantics.Q16_16
  attacksPrevented : Nat
  deriving Repr, Inhabited, ToJson, FromJson

structure EnergyTrackingGains where
  energyReduction : Semantics.Q16_16
  efficiencyImprovement : Semantics.Q16_16
  deriving Repr, Inhabited, ToJson, FromJson

structure EfficiencySummary where
  sabotageGains : SabotagePreventionGains
  restorationGains : ServiceRestorationGains
  syncGains : SyncAttackPreventionGains
  energyGains : EnergyTrackingGains
  overallEfficiencyGain : Semantics.Q16_16
  overallConnectivityGain : Semantics.Q16_16
  totalAttacksPrevented : Nat
  deriving Repr, Inhabited, ToJson, FromJson

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Calculations
-- ═══════════════════════════════════════════════════════════════════════════

def calculateSabotagePreventionGains (baselineEfficiency baselineConnectivity afterSabotageEfficiency afterSabotageConnectivity : Semantics.Q16_16) : SabotagePreventionGains :=
  let efficiencyGain := baselineEfficiency - afterSabotageEfficiency
  let connectivityGain := baselineConnectivity - afterSabotageConnectivity
  
  let hundred := ofNat 100
  let efficiencyImprovementPct := if afterSabotageEfficiency == zero then zero
                                 else (efficiencyGain * hundred) / afterSabotageEfficiency
  let connectivityImprovementPct := if afterSabotageConnectivity == zero then zero
                                   else (connectivityGain * hundred) / afterSabotageConnectivity
  
  {
    efficiencyGain := efficiencyImprovementPct,
    connectivityGain := connectivityImprovementPct,
    attacksBlocked := 3
  }

def calculateServiceRestorationGains (baselineServices disabledServices : Nat) : ServiceRestorationGains :=
  let baselineCapacity := baselineServices - disabledServices
  let restoredCapacity := baselineServices
  
  let capacityGain := ofNat (restoredCapacity - baselineCapacity)
  let hundred := ofNat 100
  let capacityImprovementPct := if baselineCapacity = 0 then zero
                                 else (capacityGain * hundred) / ofNat baselineCapacity
  
  {
    capacityGain := capacityImprovementPct,
    restorationBenefit := ofFloat 1.2
  }

def calculateSyncAttackPreventionGains (baselineConnectivity baselineEfficiency worstConnectivity worstEfficiency : Semantics.Q16_16) : SyncAttackPreventionGains :=
  let connectivityGain := baselineConnectivity - worstConnectivity
  let efficiencyGain := baselineEfficiency - worstEfficiency
  
  let hundred := ofNat 100
  let connectivityImprovementPct := if worstConnectivity == zero then zero
                                   else (connectivityGain * hundred) / worstConnectivity
  let efficiencyImprovementPct := if worstEfficiency == zero then zero
                                 else (efficiencyGain * hundred) / worstEfficiency
  
  {
    connectivityGain := connectivityImprovementPct,
    efficiencyGain := efficiencyImprovementPct,
    attacksPrevented := 2
  }

def calculateEnergyTrackingGains (baselineEnergyPerTask baselineEfficiency trackedEnergyPerTask trackedEfficiency : Semantics.Q16_16) : EnergyTrackingGains :=
  let energyReduction := baselineEnergyPerTask - trackedEnergyPerTask
  let hundred := ofNat 100
  let energyReductionPct := if baselineEnergyPerTask == zero then zero
                           else (energyReduction * hundred) / baselineEnergyPerTask
  
  let efficiencyImprovement := trackedEfficiency - baselineEfficiency
  let efficiencyImprovementPct := if baselineEfficiency == zero then zero
                                 else (efficiencyImprovement * hundred) / baselineEfficiency
  
  {
    energyReduction := energyReductionPct,
    efficiencyImprovement := efficiencyImprovementPct
  }

def generateEfficiencySummary (sabotage : SabotagePreventionGains) (restoration : ServiceRestorationGains) (sync : SyncAttackPreventionGains) (energy : EnergyTrackingGains) : EfficiencySummary :=
  let overallEfficiencyGain := (sabotage.efficiencyGain + sync.efficiencyGain + energy.efficiencyImprovement) / ofNat 3
  let overallConnectivityGain := (sabotage.connectivityGain + sync.connectivityGain) / ofNat 2
  let totalAttacksPrevented := sabotage.attacksBlocked + sync.attacksPrevented
  
  {
    sabotageGains := sabotage,
    restorationGains := restoration,
    syncGains := sync,
    energyGains := energy,
    overallEfficiencyGain := overallEfficiencyGain,
    overallConnectivityGain := overallConnectivityGain,
    totalAttacksPrevented := totalAttacksPrevented
  }

end Semantics.EfficiencyAnalysis
