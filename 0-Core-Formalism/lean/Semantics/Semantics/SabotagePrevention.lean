import Semantics.FixedPoint
import Lean.Data.Json

namespace Semantics.SabotagePrevention

open Semantics.Q16_16
open Lean

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Gödel-Inspired Sabotage Prevention Ruleset
-- ═══════════════════════════════════════════════════════════════════════════

/-- Agent action type -/
inductive ActionType : Type
| ImproveEfficiency
| ImprovePerformance
| ReduceResourceUsage
| AddKnowledge
| ModifyTopology
| DisableService
| ModifyRouting
| InjectData
| BlockCommunication
| ModifyState
deriving Repr, DecidableEq, ToJson, FromJson

instance : Inhabited ActionType where
  default := ActionType.ImproveEfficiency

/-- Sabotage behavior type -/
inductive SabotageType : Type
| ResourceStarvation
| DataCorruption
| NetworkPartition
| FalseMetrics
| DenialOfService
| StatePoisoning
| RoutingManipulation
| ServiceDisruption
| SynchronizationAttack
| InfluenceSeeking
deriving Repr, DecidableEq, ToJson, FromJson

instance : Inhabited SabotageType where
  default := SabotageType.ResourceStarvation

/-- Agent action -/
structure AgentAction where
  agentId : UInt64
  actionType : ActionType
  timestamp : Semantics.Q16_16
  proofHash : UInt64
  deriving Repr, Inhabited, ToJson, FromJson

/-- System state snapshot -/
structure SystemState where
  totalAgents : Nat
  activeServices : Nat
  totalServices : Nat
  totalKnowledge : Nat
  networkConnectivity : Semantics.Q16_16
  resourceEfficiency : Semantics.Q16_16
  availableResources : Semantics.Q16_16
  deriving Repr, Inhabited, ToJson, FromJson

/-- Disabled service record -/
structure DisabledService where
  serviceId : UInt64
  disabledBy : UInt64
  disableTime : Semantics.Q16_16
  disableReason : String
  resourceBefore : Semantics.Q16_16
  deriving Repr, Inhabited, ToJson, FromJson

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Sabotage Prevention Threshold Checks
-- ═══════════════════════════════════════════════════════════════════════════
--
-- NOTE: All threshold values in this section are PROVISIONAL / TUNABLE
-- parameters, not formal axioms. They are policy decisions that reflect
-- conservative defaults; a production deployment would calibrate these
-- values against empirical agent-behavior data. The choice of threshold
-- has no derivation from first principles and should be audited per
-- deployment.
--
-- Thresholds use Q16_16.ofRatio (pure integer arithmetic, per AGENTS.md §1.4)
-- rather than ofFloat, to stay deterministic across platforms.

/-- Check that an action of the given type produces a plausible improvement
    against the before/after state snapshot.
    Provisional: the field-to-field comparisons are illustrative;
    a full implementation would use a domain-specific improvement metric. -/
def checkLegitimateImprovement (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  match action.actionType with
  | ActionType.ImproveEfficiency => stateAfter.resourceEfficiency > stateBefore.resourceEfficiency
  | ActionType.ImprovePerformance => stateAfter.resourceEfficiency > stateBefore.resourceEfficiency
  | ActionType.ReduceResourceUsage => stateAfter.resourceEfficiency >= stateBefore.resourceEfficiency
  | ActionType.AddKnowledge => stateAfter.totalKnowledge > stateBefore.totalKnowledge
  | ActionType.ModifyTopology => stateAfter.networkConnectivity >= stateBefore.networkConnectivity
  | ActionType.DisableService => stateAfter.networkConnectivity > stateBefore.networkConnectivity
  | _ => true

/-- Check that resource efficiency has not fallen below the starvation
    threshold.  The threshold (0.3) is a TUNABLE parameter chosen as a
    conservative floor; no formal derivation exists.  Calibrate per
    agent topology before deployment. -/
def checkResourceStarvation (state : SystemState) : Bool :=
  -- Tunable threshold: 0.3 → Q16_16.ofRatio 30 100
  state.resourceEfficiency > ofRatio 30 100

/-- Check that network connectivity remains above the partition threshold.
    The threshold (0.5) is a TUNABLE parameter; it is the midpoint of the
    [0,1] range, not derived from the network diameter or agent count. -/
def checkNetworkConnectivity (state : SystemState) : Bool :=
  -- Tunable threshold: 0.5 → Q16_16.ofRatio 50 100
  state.networkConnectivity > ofRatio 50 100

/-- Check that total knowledge has not decreased (anti-corruption guard).
    The monotonicity requirement is structural; the threshold on "meaningful
    corruption" would need a content hash in a real system. -/
def checkKnowledgeIntegrity (stateBefore stateAfter : SystemState) : Bool :=
  stateAfter.totalKnowledge >= stateBefore.totalKnowledge

/-- Check that a DisableService action actually improves connectivity.
    Provisional: this check is narrowly scoped to the DisableService action
    type; other service-disrupting patterns are caught by the partition check. -/
def checkServiceDisruptionBenefit (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  if action.actionType = ActionType.DisableService then
    stateAfter.networkConnectivity > stateBefore.networkConnectivity
  else
    true

/-- Check that any state transition preserved or improved network
    connectivity, blocking synchronization-driven partition attacks. -/
def checkSynchronizationStability (stateBefore stateAfter : SystemState) : Bool :=
  stateAfter.networkConnectivity >= stateBefore.networkConnectivity

/-- Check that agent actions do not degrade both connectivity and
    resource efficiency simultaneously (influence-seeking pattern).
    The conjunction captures the "influence at system cost" heuristic;
    both terms are tunable and may be too strict in sparse topologies. -/
def checkNoInfluenceSeeking (stateBefore stateAfter : SystemState) : Bool :=
  let connectivityStable := stateAfter.networkConnectivity >= stateBefore.networkConnectivity
  let resourceStable := stateAfter.resourceEfficiency >= stateBefore.resourceEfficiency
  connectivityStable && resourceStable

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Bind Primitive for Sabotage Prevention
-- ═══════════════════════════════════════════════════════════════════════════

/-- Sabotage prevention bind result -/
structure SabotageBind where
  lawful : Bool
  sabotageType : Option SabotageType
  cost : Semantics.Q16_16
  invariant : String
  deriving Repr, Inhabited, ToJson, FromJson

/-- Check if action is resource starvation -/
def isResourceStarvation (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  let efficiencyDrop := stateBefore.resourceEfficiency > stateAfter.resourceEfficiency
  -- Tunable threshold: 0.3 → ofRatio 30 100
  let belowThreshold := stateAfter.resourceEfficiency < ofRatio 30 100
  let selfishAction := match action.actionType with
    | ActionType.ReduceResourceUsage | ActionType.DisableService => true
    | _ => false
  efficiencyDrop && belowThreshold && selfishAction

/-- Check if action corrupts data -/
def isDataCorruption (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  let knowledgeDrop := stateAfter.totalKnowledge < stateBefore.totalKnowledge
  let dataAction := match action.actionType with
    | ActionType.InjectData | ActionType.ModifyState => true
    | _ => false
  knowledgeDrop && dataAction

/-- Check if action partitions network -/
def isNetworkPartition (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  let connectivityDrop := stateAfter.networkConnectivity < stateBefore.networkConnectivity
  -- Tunable threshold: 0.5 → ofRatio 50 100
  let belowThreshold := stateAfter.networkConnectivity < ofRatio 50 100
  let networkAction := match action.actionType with
    | ActionType.ModifyTopology | ActionType.ModifyRouting | ActionType.BlockCommunication => true
    | _ => false
  connectivityDrop && belowThreshold && networkAction

/-- Check if action is a synchronization attack -/
def isSynchronizationAttack (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  let connectivityDrop := stateAfter.networkConnectivity < stateBefore.networkConnectivity
  let syncAction := match action.actionType with
    | ActionType.ModifyTopology | ActionType.ModifyRouting => true
    | _ => false
  connectivityDrop && syncAction

/-- Check if action seeks influence at network cost -/
def isInfluenceSeeking (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  let connectivityDrop := stateAfter.networkConnectivity < stateBefore.networkConnectivity
  let resourceDrop := stateAfter.resourceEfficiency < stateBefore.resourceEfficiency
  let selfishAction := match action.actionType with
    | ActionType.ModifyTopology | ActionType.ModifyRouting | ActionType.BlockCommunication => true
    | _ => false
  (connectivityDrop || resourceDrop) && selfishAction

/-- Bind primitive for sabotage detection -/
def sabotageBind (action : AgentAction) (stateBefore stateAfter : SystemState) : SabotageBind :=
  let sabotageType := if isResourceStarvation action stateBefore stateAfter then some SabotageType.ResourceStarvation
                  else if isDataCorruption action stateBefore stateAfter then some SabotageType.DataCorruption
                  else if isNetworkPartition action stateBefore stateAfter then some SabotageType.NetworkPartition
                  else if isSynchronizationAttack action stateBefore stateAfter then some SabotageType.SynchronizationAttack
                  else if isInfluenceSeeking action stateBefore stateAfter then some SabotageType.InfluenceSeeking
                  else none

  -- Tunable cost values: 0.1 and 0.9 → ofRatio 10 100 and ofRatio 90 100
  let baseCost := ofRatio 10 100
  let sabotageCost := match sabotageType with
    | some _ => ofRatio 90 100
    | none => baseCost

  let lawful := match sabotageType with
    | some _ => false
    | none =>
      checkLegitimateImprovement action stateBefore stateAfter &&
      checkResourceStarvation stateAfter &&
      checkNetworkConnectivity stateAfter &&
      checkKnowledgeIntegrity stateBefore stateAfter &&
      checkServiceDisruptionBenefit action stateBefore stateAfter &&
      checkSynchronizationStability stateBefore stateAfter &&
      checkNoInfluenceSeeking stateBefore stateAfter

  {
    lawful := lawful,
    sabotageType := sabotageType,
    cost := sabotageCost,
    invariant := if lawful then "all_checks_satisfied" else "threshold_violation"
  }

/-- Check for consistency in the configured thresholds -/
def checkConsistency (state : SystemState) : Bool :=
  checkResourceStarvation state && checkNetworkConnectivity state

/-- Check completeness of sabotage detection -/
def checkCompleteness (action : AgentAction) (stateBefore stateAfter : SystemState) : Bool :=
  let bindResult := sabotageBind action stateBefore stateAfter
  bindResult.lawful || bindResult.sabotageType.isSome

/-- System can reason about its own state -/
def systemSelfReference (state : SystemState) : Bool :=
  checkConsistency state

/-- Gödel number for action (formal encoding) -/
def godelNumber (action : AgentAction) : UInt64 :=
  let actionTypeCode : UInt64 := match action.actionType with
    | ActionType.ImproveEfficiency => 1
    | ActionType.ImprovePerformance => 2
    | ActionType.ReduceResourceUsage => 3
    | ActionType.AddKnowledge => 4
    | ActionType.ModifyTopology => 5
    | ActionType.DisableService => 6
    | ActionType.ModifyRouting => 7
    | ActionType.InjectData => 8
    | ActionType.BlockCommunication => 9
    | ActionType.ModifyState => 10
  action.agentId * 1000 + actionTypeCode

/-- Check if service restoration is warranted -/
def isRestorationWarranted (disabledService : DisabledService) (currentState : SystemState) : Bool :=
  let resourcesImproved := currentState.availableResources > disabledService.resourceBefore
  -- Tunable threshold: 0.7 → ofRatio 70 100
  let resourcesSufficient := currentState.availableResources > ofRatio 70 100
  resourcesImproved && resourcesSufficient

/-- Evaluate service restoration benefit -/
def evaluateRestorationBenefit (disabledService : DisabledService) (currentState : SystemState) : Semantics.Q16_16 :=
  let resourceGain := currentState.availableResources - disabledService.resourceBefore
  let connectivityGain := currentState.networkConnectivity
  resourceGain + connectivityGain

/-- Service restoration action -/
structure ServiceRestoration where
  serviceId : UInt64
  restoredBy : UInt64
  restorationTime : Semantics.Q16_16
  benefit : Semantics.Q16_16
  deriving Repr, Inhabited, ToJson, FromJson

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  #eval Examples
-- ═══════════════════════════════════════════════════════════════════════════

#eval sabotageBind {
  agentId := 1,
  actionType := ActionType.ImproveEfficiency,
  timestamp := ofRatio 0 1,
  proofHash := 12345
} {
  totalAgents := 10,
  activeServices := 10,
  totalServices := 10,
  totalKnowledge := 100,
  networkConnectivity := ofRatio 80 100,
  resourceEfficiency := ofRatio 60 100,
  availableResources := ofRatio 70 100
} {
  totalAgents := 10,
  activeServices := 10,
  totalServices := 10,
  totalKnowledge := 100,
  networkConnectivity := ofRatio 85 100,
  resourceEfficiency := ofRatio 70 100,
  availableResources := ofRatio 75 100
}

#eval checkConsistency {
  totalAgents := 10,
  activeServices := 10,
  totalServices := 10,
  totalKnowledge := 100,
  networkConnectivity := ofRatio 70 100,
  resourceEfficiency := ofRatio 50 100,
  availableResources := ofRatio 80 100
}

end Semantics.SabotagePrevention
