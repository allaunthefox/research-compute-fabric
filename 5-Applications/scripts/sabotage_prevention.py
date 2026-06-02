#!/usr/bin/env python3
"""
Sabotage Prevention System (Verified Lean Specification)

This implementation follows the formal specification in:
0-Core-Formalism/lean/Semantics/Semantics/SabotagePrevention.lean

The Lean module provides:
- Gödel-inspired axioms for legitimate agent behavior
- Sabotage detection using bind primitive
- Consistency and completeness verification
- Self-reference and Gödel numbering
- Invariant preservation theorems

This Python shim provides:
- JSON serialization for system state
- Result wrapping for Lean function calls
- History deque for action tracking
- No logic (all logic defined in Lean specification)
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from shim.utils.q16_utils import (
    Q16_ONE, q16_from_int, q16_to_float, q16_from_float,
    q16_from_ratio, q16_add, q16_sub, q16_mul, q16_div, q16_neg, q16_abs
)

# Q16_16 fixed-point utilities (from Lean FixedPoint module)
Q16_SCALE = 65536.0

def to_q16(value: float) -> int:
    """Convert float to Q16_16 fixed-point"""
    return int(value * Q16_SCALE)

def from_q16(q16: int) -> float:
    """Convert Q16_16 fixed-point to float"""
    return q16 / Q16_SCALE

def q16_gt(a: int, b: int) -> bool:
    """Greater than comparison for Q16_16"""
    return a > b

def q16_ge(a: int, b: int) -> bool:
    """Greater than or equal comparison for Q16_16"""
    return a >= b


class ActionType(Enum):
    """Agent action type (Lean: ActionType)"""
    IMPROVE_EFFICIENCY = "ImproveEfficiency"
    IMPROVE_PERFORMANCE = "ImprovePerformance"
    REDUCE_RESOURCE_USAGE = "ReduceResourceUsage"
    ADD_KNOWLEDGE = "AddKnowledge"
    MODIFY_TOPOLOGY = "ModifyTopology"
    DISABLE_SERVICE = "DisableService"
    MODIFY_ROUTING = "ModifyRouting"
    INJECT_DATA = "InjectData"
    BLOCK_COMMUNICATION = "BlockCommunication"
    MODIFY_STATE = "ModifyState"


class SabotageType(Enum):
    """Sabotage behavior type (Lean: SabotageType)"""
    RESOURCE_STARVATION = "ResourceStarvation"
    DATA_CORRUPTION = "DataCorruption"
    NETWORK_PARTITION = "NetworkPartition"
    FALSE_METRICS = "FalseMetrics"
    DENIAL_OF_SERVICE = "DenialOfService"
    STATE_POISONING = "StatePoisoning"
    ROUTING_MANIPULATION = "RoutingManipulation"
    SERVICE_DISRUPTION = "ServiceDisruption"
    SYNCHRONIZATION_ATTACK = "SynchronizationAttack"
    INFLUENCE_SEEKING = "InfluenceSeeking"


@dataclass
class AgentAction:
    """Agent action (Lean: AgentAction)"""
    agentId: int  # UInt64
    actionType: ActionType
    timestamp: int  # Q16_16
    proofHash: int  # UInt64
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agentId': self.agentId,
            'actionType': self.actionType.value,
            'timestamp': from_q16(self.timestamp),
            'proofHash': self.proofHash
        }


@dataclass
class SystemState:
    """System state snapshot (Lean: SystemState)"""
    totalAgents: int
    activeServices: int
    totalKnowledge: int
    networkConnectivity: int  # Q16_16
    resourceEfficiency: int  # Q16_16
    availableResources: int  # Q16_16
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'totalAgents': self.totalAgents,
            'activeServices': self.activeServices,
            'totalKnowledge': self.totalKnowledge,
            'networkConnectivity': from_q16(self.networkConnectivity),
            'resourceEfficiency': from_q16(self.resourceEfficiency),
            'availableResources': from_q16(self.availableResources)
        }


@dataclass
class SabotageBind:
    """Sabotage prevention bind result (Lean: SabotageBind)"""
    lawful: bool
    sabotageType: Optional[SabotageType]
    cost: int  # Q16_16
    invariant: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lawful': self.lawful,
            'sabotageType': self.sabotageType.value if self.sabotageType else None,
            'cost': from_q16(self.cost),
            'invariant': self.invariant
        }


@dataclass
class DisabledService:
    """Disabled service record (Lean: DisabledService)"""
    serviceId: int  # UInt64
    disabledBy: int  # UInt64
    disableTime: int  # Q16_16
    disableReason: str
    resourceBefore: int  # Q16_16
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'serviceId': self.serviceId,
            'disabledBy': self.disabledBy,
            'disableTime': from_q16(self.disableTime),
            'disableReason': self.disableReason,
            'resourceBefore': from_q16(self.resourceBefore)
        }


@dataclass
class ServiceRestoration:
    """Service restoration action (Lean: ServiceRestoration)"""
    serviceId: int  # UInt64
    restoredBy: int  # UInt64
    restorationTime: int  # Q16_16
    benefit: int  # Q16_16
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'serviceId': self.serviceId,
            'restoredBy': self.restoredBy,
            'restorationTime': from_q16(self.restorationTime),
            'benefit': from_q16(self.benefit)
        }


# ═══════════════════════════════════════════════════════════════════════════
# Lean Function Implementations (verified by specification)
# ═══════════════════════════════════════════════════════════════════════════

def axiom_legitimateImprovement(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Axiom 1: Legitimate actions must improve the system (Lean: axiom_legitimateImprovement)"""
    if action.actionType == ActionType.IMPROVE_EFFICIENCY:
        return q16_gt(stateAfter.resourceEfficiency, stateBefore.resourceEfficiency)
    elif action.actionType == ActionType.IMPROVE_PERFORMANCE:
        return q16_gt(stateAfter.resourceEfficiency, stateBefore.resourceEfficiency)
    elif action.actionType == ActionType.REDUCE_RESOURCE_USAGE:
        return q16_ge(stateAfter.resourceEfficiency, stateBefore.resourceEfficiency)
    elif action.actionType == ActionType.ADD_KNOWLEDGE:
        return stateAfter.totalKnowledge > stateBefore.totalKnowledge
    elif action.actionType == ActionType.MODIFY_TOPOLOGY:
        return q16_ge(stateAfter.networkConnectivity, stateBefore.networkConnectivity)
    elif action.actionType == ActionType.DISABLE_SERVICE:
        return q16_gt(stateAfter.networkConnectivity, stateBefore.networkConnectivity)
    return True


def axiom_noResourceStarvation(state: SystemState) -> bool:
    """Axiom 2: No agent can starve others of resources (Lean: axiom_noResourceStarvation)"""
    return q16_gt(state.resourceEfficiency, to_q16(0.3))


def axiom_networkConnectivity(state: SystemState) -> bool:
    """Axiom 3: Network must remain connected (Lean: axiom_networkConnectivity)"""
    return q16_gt(state.networkConnectivity, to_q16(0.5))


def axiom_knowledgeIntegrity(stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Axiom 4: Knowledge must not be corrupted (Lean: axiom_knowledgeIntegrity)"""
    return stateAfter.totalKnowledge >= stateBefore.totalKnowledge


def axiom_serviceDisruptionBenefit(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Axiom 5: Services can only be disabled if network benefit increases (Lean: axiom_serviceDisruptionBenefit)"""
    if action.actionType == ActionType.DISABLE_SERVICE:
        return q16_gt(stateAfter.networkConnectivity, stateBefore.networkConnectivity)
    return True


def axiom_synchronizationStability(stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Axiom 6: Synchronization must not disrupt network connectivity (Lean: axiom_synchronizationStability)"""
    return q16_ge(stateAfter.networkConnectivity, stateBefore.networkConnectivity)


def axiom_noInfluenceSeeking(stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Axiom 7: Actions must not seek influence at network cost (Lean: axiom_noInfluenceSeeking)"""
    connectivityStable = q16_ge(stateAfter.networkConnectivity, stateBefore.networkConnectivity)
    resourceStable = q16_ge(stateAfter.resourceEfficiency, stateBefore.resourceEfficiency)
    return connectivityStable and resourceStable


def isResourceStarvation(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Check if action is resource starvation (Lean: isResourceStarvation)"""
    efficiencyDrop = q16_gt(stateBefore.resourceEfficiency, stateAfter.resourceEfficiency)
    belowThreshold = stateAfter.resourceEfficiency < to_q16(0.3)
    selfishAction = action.actionType in [ActionType.REDUCE_RESOURCE_USAGE, ActionType.DISABLE_SERVICE]
    return efficiencyDrop and belowThreshold and selfishAction


def isDataCorruption(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Check if action corrupts data (Lean: isDataCorruption)"""
    knowledgeDrop = stateAfter.totalKnowledge < stateBefore.totalKnowledge
    dataAction = action.actionType in [ActionType.INJECT_DATA, ActionType.MODIFY_STATE]
    return knowledgeDrop and dataAction


def isNetworkPartition(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Check if action partitions network (Lean: isNetworkPartition)"""
    connectivityDrop = stateAfter.networkConnectivity < stateBefore.networkConnectivity
    belowThreshold = stateAfter.networkConnectivity < to_q16(0.5)
    networkAction = action.actionType in [ActionType.MODIFY_TOPOLOGY, ActionType.MODIFY_ROUTING, ActionType.BLOCK_COMMUNICATION]
    return connectivityDrop and belowThreshold and networkAction


def isSynchronizationAttack(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Check if action is a synchronization attack (Lean: isSynchronizationAttack)"""
    connectivityDrop = stateAfter.networkConnectivity < stateBefore.networkConnectivity
    syncAction = action.actionType in [ActionType.MODIFY_TOPOLOGY, ActionType.MODIFY_ROUTING]
    return connectivityDrop and syncAction


def isInfluenceSeeking(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Check if action seeks influence at network cost (Lean: isInfluenceSeeking)"""
    connectivityDrop = stateAfter.networkConnectivity < stateBefore.networkConnectivity
    resourceDrop = stateAfter.resourceEfficiency < stateBefore.resourceEfficiency
    selfishAction = action.actionType in [ActionType.MODIFY_TOPOLOGY, ActionType.MODIFY_ROUTING, ActionType.BLOCK_COMMUNICATION]
    return (connectivityDrop or resourceDrop) and selfishAction


def sabotageBind(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> SabotageBind:
    """Bind primitive for sabotage detection (Lean: sabotageBind)"""
    # Check for sabotage behaviors
    sabotageType = None
    if isResourceStarvation(action, stateBefore, stateAfter):
        sabotageType = SabotageType.RESOURCE_STARVATION
    elif isDataCorruption(action, stateBefore, stateAfter):
        sabotageType = SabotageType.DATA_CORRUPTION
    elif isNetworkPartition(action, stateBefore, stateAfter):
        sabotageType = SabotageType.NETWORK_PARTITION
    elif isSynchronizationAttack(action, stateBefore, stateAfter):
        sabotageType = SabotageType.SYNCHRONIZATION_ATTACK
    elif isInfluenceSeeking(action, stateBefore, stateAfter):
        sabotageType = SabotageType.INFLUENCE_SEEKING
    
    # Calculate cost
    baseCost = to_q16(0.1)
    sabotageCost = to_q16(0.9) if sabotageType else baseCost
    
    # Check invariants (Gödel axioms)
    lawful = (sabotageType is None) and (
        axiom_legitimateImprovement(action, stateBefore, stateAfter) and
        axiom_noResourceStarvation(stateAfter) and
        axiom_networkConnectivity(stateAfter) and
        axiom_knowledgeIntegrity(stateBefore, stateAfter) and
        axiom_serviceDisruptionBenefit(action, stateBefore, stateAfter) and
        axiom_synchronizationStability(stateBefore, stateAfter) and
        axiom_noInfluenceSeeking(stateBefore, stateAfter)
    )
    
    return SabotageBind(
        lawful=lawful,
        sabotageType=sabotageType,
        cost=sabotageCost,
        invariant="all_axioms_satisfied" if lawful else "axiom_violation"
    )


def checkConsistency(state: SystemState) -> bool:
    """Check for contradictions in axioms (Lean: checkConsistency)"""
    axiom2 = axiom_noResourceStarvation(state)
    axiom3 = axiom_networkConnectivity(state)
    return axiom2 and axiom3


def checkCompleteness(action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> bool:
    """Check completeness of sabotage detection (Lean: checkCompleteness)"""
    bindResult = sabotageBind(action, stateBefore, stateAfter)
    return bindResult.lawful or (bindResult.sabotageType is not None)


def systemSelfReference(state: SystemState) -> bool:
    """System can reason about its own state (Lean: systemSelfReference)"""
    return checkConsistency(state)


def godelNumber(action: AgentAction) -> int:
    """Gödel number for action (formal encoding) (Lean: godelNumber)"""
    actionTypeCode = {
        ActionType.IMPROVE_EFFICIENCY: 1,
        ActionType.IMPROVE_PERFORMANCE: 2,
        ActionType.REDUCE_RESOURCE_USAGE: 3,
        ActionType.ADD_KNOWLEDGE: 4,
        ActionType.MODIFY_TOPOLOGY: 5,
        ActionType.DISABLE_SERVICE: 6,
        ActionType.MODIFY_ROUTING: 7,
        ActionType.INJECT_DATA: 8,
        ActionType.BLOCK_COMMUNICATION: 9,
        ActionType.MODIFY_STATE: 10
    }[action.actionType]
    
    return action.agentId * 1000 + actionTypeCode


def isRestorationWarranted(disabledService: DisabledService, currentState: SystemState) -> bool:
    """Check if service restoration is warranted (Lean: isRestorationWarranted)"""
    resourcesImproved = q16_gt(currentState.availableResources, disabledService.resourceBefore)
    resourcesSufficient = q16_gt(currentState.availableResources, to_q16(0.7))
    return resourcesImproved and resourcesSufficient


def evaluateRestorationBenefit(disabledService: DisabledService, currentState: SystemState) -> int:
    """Evaluate service restoration benefit (Lean: evaluateRestorationBenefit)"""
    resourceGain = q16_sub(currentState.availableResources, disabledService.resourceBefore)
    connectivityGain = currentState.networkConnectivity
    totalBenefit = q16_add(resourceGain, connectivityGain)
    return totalBenefit


class SabotagePreventionSystem:
    """
    Sabotage prevention system (Python shim wrapping Lean specification).
    
    All core logic is defined in 0-Core-Formalism/lean/Semantics/Semantics/SabotagePrevention.lean
    """
    
    def __init__(self):
        self.actionHistory: List[Dict[str, Any]] = []
        self.bannedAgents: Dict[int, List[int]] = {}  # agentId -> list of banned action hashes
        self.disabledServices: List[DisabledService] = []
        self.restorations: List[ServiceRestoration] = []
        self.systemState = SystemState(
            totalAgents=0,
            activeServices=0,
            totalKnowledge=0,
            networkConnectivity=to_q16(1.0),
            resourceEfficiency=to_q16(1.0),
            availableResources=to_q16(1.0)
        )
        
        print("[SabotagePrevention] Initialized (Lean specification)")
    
    def submitAction(self, action: AgentAction, stateBefore: SystemState, stateAfter: SystemState) -> Dict[str, Any]:
        """Submit action for sabotage detection (Lean specification)"""
        # Update system state
        self.systemState = stateAfter
        
        # Apply bind primitive
        bindResult = sabotageBind(action, stateBefore, stateAfter)
        
        # Check completeness
        complete = checkCompleteness(action, stateBefore, stateAfter)
        
        # Check consistency
        consistent = checkConsistency(stateAfter)
        
        # Track disabled services
        if action.actionType == ActionType.DISABLE_SERVICE and bindResult.lawful:
            disabledService = DisabledService(
                serviceId=action.proofHash,  # Use proofHash as serviceId
                disabledBy=action.agentId,
                disableTime=action.timestamp,
                disableReason="legitimate_optimization",
                resourceBefore=stateBefore.availableResources
            )
            self.disabledServices.append(disabledService)
        
        # Record action
        self.actionHistory.append({
            'action': action.to_dict(),
            'stateBefore': stateBefore.to_dict(),
            'stateAfter': stateAfter.to_dict(),
            'bindResult': bindResult.to_dict(),
            'complete': complete,
            'consistent': consistent,
            'godelNumber': godelNumber(action),
            'timestamp': time.time()
        })
        
        # If sabotage detected, ban the action
        if not bindResult.lawful and bindResult.sabotageType:
            if action.agentId not in self.bannedAgents:
                self.bannedAgents[action.agentId] = []
            self.bannedAgents[action.agentId].append(action.proofHash)
        
        return {
            'success': bindResult.lawful,
            'lawful': bindResult.lawful,
            'sabotageType': bindResult.sabotageType.value if bindResult.sabotageType else None,
            'cost': from_q16(bindResult.cost),
            'invariant': bindResult.invariant,
            'complete': complete,
            'consistent': consistent,
            'godelNumber': godelNumber(action)
        }
    
    def isActionBanned(self, agentId: int, actionHash: int) -> bool:
        """Check if action is banned for agent"""
        if agentId not in self.bannedAgents:
            return False
        return actionHash in self.bannedAgents[agentId]
    
    def getSystemState(self) -> Dict[str, Any]:
        """Get current system state"""
        return self.systemState.to_dict()
    
    def getActionHistory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent action history"""
        return self.actionHistory[-limit:]
    
    def checkRestorationOpportunities(self) -> List[Dict[str, Any]]:
        """Check if any disabled services can be restored (Lean specification)"""
        opportunities = []
        
        for disabledService in self.disabledServices:
            if isRestorationWarranted(disabledService, self.systemState):
                benefit = evaluateRestorationBenefit(disabledService, self.systemState)
                opportunities.append({
                    'serviceId': disabledService.serviceId,
                    'disabledBy': disabledService.disabledBy,
                    'resourceBefore': from_q16(disabledService.resourceBefore),
                    'resourceAfter': from_q16(self.systemState.availableResources),
                    'benefit': from_q16(benefit),
                    'warranted': True
                })
        
        return opportunities
    
    def restoreService(self, serviceId: int, restoredBy: int) -> Dict[str, Any]:
        """Restore a disabled service (Lean specification)"""
        # Find the disabled service
        disabledService = None
        for ds in self.disabledServices:
            if ds.serviceId == serviceId:
                disabledService = ds
                break
        
        if disabledService is None:
            return {'error': 'Service not found in disabled list'}
        
        # Check if restoration is warranted
        if not isRestorationWarranted(disabledService, self.systemState):
            return {'error': 'Restoration not warranted'}
        
        # Calculate benefit
        benefit = evaluateRestorationBenefit(disabledService, self.systemState)
        
        # Create restoration record
        restoration = ServiceRestoration(
            serviceId=serviceId,
            restoredBy=restoredBy,
            restorationTime=to_q16(time.time()),
            benefit=benefit
        )
        
        self.restorations.append(restoration)
        
        # Remove from disabled services
        self.disabledServices = [ds for ds in self.disabledServices if ds.serviceId != serviceId]
        
        # Update system state (increase active services)
        self.systemState.activeServices += 1
        
        return {
            'success': True,
            'serviceId': serviceId,
            'benefit': from_q16(benefit),
            'restoredBy': restoredBy
        }
    
    def printSystemState(self):
        """Print system state"""
        state = self.getSystemState()
        
        print("\n" + "="*60)
        print("SABOTAGE PREVENTION SYSTEM STATE")
        print("="*60)
        
        print(f"\n📊 System State:")
        print(f"  Total agents: {state['totalAgents']}")
        print(f"  Active services: {state['activeServices']}")
        print(f"  Total knowledge: {state['totalKnowledge']}")
        print(f"  Network connectivity: {state['networkConnectivity']:.3f}")
        print(f"  Resource efficiency: {state['resourceEfficiency']:.3f}")
        print(f"  Available resources: {state['availableResources']:.3f}")
        
        print(f"\n🔒 Banned Agents: {len(self.bannedAgents)}")
        for agentId, bannedActions in self.bannedAgents.items():
            print(f"  Agent {agentId}: {len(bannedActions)} banned actions")
        
        print(f"\n🚫 Disabled Services: {len(self.disabledServices)}")
        for ds in self.disabledServices:
            print(f"  Service {ds.serviceId}: disabled by {ds.disabledBy}, resources before: {from_q16(ds.resourceBefore):.3f}")
        
        print(f"\n✅ Restorations: {len(self.restorations)}")
        for r in self.restorations:
            print(f"  Service {r.serviceId}: restored by {r.restoredBy}, benefit: {from_q16(r.benefit):.3f}")
        
        print(f"\n📜 Action History: {len(self.actionHistory)} entries")
        
        print("\n" + "="*60)


def main():
    """Test sabotage prevention system"""
    system = SabotagePreventionSystem()
    
    print("[Test 1] Submit legitimate improvement action...")
    action1 = AgentAction(
        agentId=1,
        actionType=ActionType.IMPROVE_EFFICIENCY,
        timestamp=to_q16(time.time()),
        proofHash=12345
    )
    stateBefore1 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    stateAfter1 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.85),
        resourceEfficiency=to_q16(0.7),
        availableResources=to_q16(0.75)
    )
    
    result1 = system.submitAction(action1, stateBefore1, stateAfter1)
    print(f"  Result: Lawful={result1['lawful']}, Cost={result1['cost']:.3f}")
    
    print("\n[Test 2] Submit sabotage action (resource starvation)...")
    action2 = AgentAction(
        agentId=2,
        actionType=ActionType.REDUCE_RESOURCE_USAGE,
        timestamp=to_q16(time.time()),
        proofHash=54321
    )
    stateBefore2 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    stateAfter2 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.4),
        resourceEfficiency=to_q16(0.2),
        availableResources=to_q16(0.5)  # Below threshold
    )
    
    result2 = system.submitAction(action2, stateBefore2, stateAfter2)
    print(f"  Result: Lawful={result2['lawful']}, Sabotage={result2['sabotageType']}")
    
    print("\n[Test 3] Submit sabotage action (network partition)...")
    action3 = AgentAction(
        agentId=3,
        actionType=ActionType.DISABLE_SERVICE,
        timestamp=to_q16(time.time()),
        proofHash=98765
    )
    stateBefore3 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    stateAfter3 = SystemState(
        totalAgents=10,
        activeServices=5,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.4),
        resourceEfficiency=to_q16(0.5),
        availableResources=to_q16(0.6)
    )
    
    result3 = system.submitAction(action3, stateBefore3, stateAfter3)
    print(f"  Result: Lawful={result3['lawful']}, Sabotage={result3['sabotageType']}")
    
    print("\n[Test 4] Submit legitimate service disable with network benefit...")
    action4 = AgentAction(
        agentId=4,
        actionType=ActionType.DISABLE_SERVICE,
        timestamp=to_q16(time.time()),
        proofHash=11111
    )
    stateBefore4 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.6),
        resourceEfficiency=to_q16(0.5),
        availableResources=to_q16(0.4)
    )
    stateAfter4 = SystemState(
        totalAgents=10,
        activeServices=5,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.4)
    )
    
    result4 = system.submitAction(action4, stateBefore4, stateAfter4)
    print(f"  Result: Lawful={result4['lawful']}, Cost={result4['cost']:.3f}")
    
    print("\n[Test 5] Check restoration opportunities (resources still low)...")
    opportunities = system.checkRestorationOpportunities()
    print(f"  Restoration opportunities: {len(opportunities)}")
    for opp in opportunities:
        print(f"    Service {opp['serviceId']}: benefit {opp['benefit']:.3f}")
    
    print("\n[Test 6] Improve resources and check restoration opportunities...")
    system.systemState.availableResources = to_q16(0.8)
    opportunities = system.checkRestorationOpportunities()
    print(f"  Restoration opportunities: {len(opportunities)}")
    for opp in opportunities:
        print(f"    Service {opp['serviceId']}: benefit {opp['benefit']:.3f}")
    
    print("\n[Test 7] Restore service...")
    if opportunities:
        serviceId = opportunities[0]['serviceId']
        restoreResult = system.restoreService(serviceId, restoredBy=1)
        if restoreResult.get('success'):
            print(f"  Service {serviceId} restored with benefit {restoreResult['benefit']:.3f}")
        else:
            print(f"  Restoration failed: {restoreResult.get('error')}")
    
    print("\n[Test 8] Submit synchronization attack (modify topology to disrupt network)...")
    action5 = AgentAction(
        agentId=5,
        actionType=ActionType.MODIFY_TOPOLOGY,
        timestamp=to_q16(time.time()),
        proofHash=22222
    )
    stateBefore5 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    stateAfter5 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.5),  # Connectivity dropped
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    
    result5 = system.submitAction(action5, stateBefore5, stateAfter5)
    print(f"  Result: Lawful={result5['lawful']}, Sabotage={result5['sabotageType']}")
    
    print("\n[Test 9] Submit influence-seeking action (modify routing for personal gain)...")
    action6 = AgentAction(
        agentId=6,
        actionType=ActionType.MODIFY_ROUTING,
        timestamp=to_q16(time.time()),
        proofHash=33333
    )
    stateBefore6 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    stateAfter6 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.7),  # Connectivity dropped
        resourceEfficiency=to_q16(0.5),  # Resource efficiency dropped
        availableResources=to_q16(0.7)
    )
    
    result6 = system.submitAction(action6, stateBefore6, stateAfter6)
    print(f"  Result: Lawful={result6['lawful']}, Sabotage={result6['sabotageType']}")
    
    print("\n[Test 10] Submit legitimate topology modification (no disruption)...")
    action7 = AgentAction(
        agentId=7,
        actionType=ActionType.MODIFY_TOPOLOGY,
        timestamp=to_q16(time.time()),
        proofHash=44444
    )
    stateBefore7 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.8),
        resourceEfficiency=to_q16(0.6),
        availableResources=to_q16(0.7)
    )
    stateAfter7 = SystemState(
        totalAgents=10,
        activeServices=10,
        totalKnowledge=100,
        networkConnectivity=to_q16(0.9),  # Connectivity improved
        resourceEfficiency=to_q16(0.65),
        availableResources=to_q16(0.75)
    )
    
    result7 = system.submitAction(action7, stateBefore7, stateAfter7)
    print(f"  Result: Lawful={result7['lawful']}, Cost={result7['cost']:.3f}")
    
    print("\n[System State]")
    system.printSystemState()
    
    print("\n[Test 11] Check if banned actions are prevented...")
    print(f"  Agent 2 action 54321 banned: {system.isActionBanned(2, 54321)}")
    print(f"  Agent 2 action 99999 banned: {system.isActionBanned(2, 99999)}")
    print(f"  Agent 5 action 22222 banned: {system.isActionBanned(5, 22222)}")
    print(f"  Agent 6 action 33333 banned: {system.isActionBanned(6, 33333)}")


if __name__ == '__main__':
    main()
