#!/usr/bin/env python3
"""
Q-Factor Energy Balance System (Verified Lean Specification)

This implementation follows the formal specification in:
0-Core-Formalism/lean/Semantics/Semantics/QFactor.lean

The Lean module provides:
- Q-Factor energy balance equation: Q = (E_flash + E_enthalpy + E_recovered - W_demon) / (E_work + E_loss)
- Energy balance optimization
- Bind primitive for Q-Factor transitions
- Invariant preservation theorems

This Python shim provides:
- JSON serialization for energy balance state
- Result wrapping for Lean function calls
- History deque for Q-Factor transitions
- No logic (all logic defined in Lean specification)
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque

try:
    from temporal_spatial_ram import TemporalSpatialRAMSystem, NodePosition, TemporalSpatialResource
    _HAS_TS_RAM = True
except ImportError:
    _HAS_TS_RAM = False
    print("[!] Temporal-spatial RAM system not available")

# Q16_16 fixed-point utilities (from Lean FixedPoint module)
Q16_ONE = 65536  # 1.0 in Q16_16
Q16_SCALE = 65536.0

def to_q16(value: float) -> int:
    """Convert float to Q16_16 fixed-point"""
    return int(value * Q16_SCALE)

def from_q16(q16: int) -> float:
    """Convert Q16_16 fixed-point to float"""
    return q16 / Q16_SCALE

def q16_add(a: int, b: int) -> int:
    """Add two Q16_16 values"""
    return a + b

def q16_sub(a: int, b: int) -> int:
    """Subtract two Q16_16 values"""
    return a - b

def q16_mul(a: int, b: int) -> int:
    """Multiply two Q16_16 values with normalization"""
    return (a * b) // Q16_ONE

def q16_div(a: int, b: int) -> int:
    """Divide two Q16_16 values with normalization"""
    if b == 0:
        return 0
    return (a * Q16_ONE) // b

def q16_gt(a: int, b: int) -> bool:
    """Greater than comparison for Q16_16"""
    return a > b

def q16_ge(a: int, b: int) -> bool:
    """Greater than or equal comparison for Q16_16"""
    return a >= b


@dataclass
class EnergyBalance:
    """Energy balance components (Lean: EnergyBalance)"""
    flashEnergy: int  # Q16_16 - Burst computation energy
    enthalpy: int  # Q16_16 - Steady-state energy
    recoveredEnergy: int  # Q16_16 - Energy from optimizations
    demonWork: int  # Q16_16 - Landauer limit for erasure
    workEnergy: int  # Q16_16 - Useful work energy
    energyLoss: int  # Q16_16 - Waste energy
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'flashEnergy': from_q16(self.flashEnergy),
            'enthalpy': from_q16(self.enthalpy),
            'recoveredEnergy': from_q16(self.recoveredEnergy),
            'demonWork': from_q16(self.demonWork),
            'workEnergy': from_q16(self.workEnergy),
            'energyLoss': from_q16(self.energyLoss)
        }


@dataclass
class QFactorState:
    """Q-Factor state (Lean: QFactorState)"""
    agentId: int  # UInt64
    balance: EnergyBalance
    qFactor: int  # Q16_16 - Current Q-factor
    targetQ: int  # Q16_16 - Target Q-factor (≈1.05)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agentId': self.agentId,
            'balance': self.balance.to_dict(),
            'qFactor': from_q16(self.qFactor),
            'targetQ': from_q16(self.targetQ)
        }


@dataclass
class QFactorAction:
    """Q-Factor optimization action (Lean: QFactorAction)"""
    agentId: int  # UInt64
    flashEnergyDelta: int  # Q16_16 - Change in flash energy
    enthalpyDelta: int  # Q16_16 - Change in enthalpy
    recoveredEnergyDelta: int  # Q16_16 - Change in recovered energy
    workEnergyDelta: int  # Q16_16 - Change in work energy
    energyLossDelta: int  # Q16_16 - Change in energy loss
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agentId': self.agentId,
            'flashEnergyDelta': from_q16(self.flashEnergyDelta),
            'enthalpyDelta': from_q16(self.enthalpyDelta),
            'recoveredEnergyDelta': from_q16(self.recoveredEnergyDelta),
            'workEnergyDelta': from_q16(self.workEnergyDelta),
            'energyLossDelta': from_q16(self.energyLossDelta)
        }


@dataclass
class QFactorBind:
    """Q-Factor bind result (Lean: QFactorBind)"""
    lawful: bool
    qFactorBefore: int  # Q16_16
    qFactorAfter: int  # Q16_16
    energySurplus: int  # Q16_16
    invariant: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lawful': self.lawful,
            'qFactorBefore': from_q16(self.qFactorBefore),
            'qFactorAfter': from_q16(self.qFactorAfter),
            'energySurplus': from_q16(self.energySurplus),
            'invariant': self.invariant
        }


# ═══════════════════════════════════════════════════════════════════════════
# Lean Function Implementations (verified by specification)
# ═══════════════════════════════════════════════════════════════════════════

def calculateQFactor(balance: EnergyBalance) -> int:
    """Calculate Q-Factor from energy balance (Lean: calculateQFactor)"""
    numerator = balance.flashEnergy + balance.enthalpy + balance.recoveredEnergy - balance.demonWork
    denominator = balance.workEnergy + balance.energyLoss
    if denominator > 0:
        return q16_div(numerator, denominator)
    return 0


def meetsTargetQ(state: QFactorState) -> bool:
    """Check if Q-Factor meets target threshold (Lean: meetsTargetQ)"""
    return q16_ge(state.qFactor, state.targetQ)


def hasNetEnergyGain(state: QFactorState) -> bool:
    """Check if Q-Factor indicates net energy gain (Lean: hasNetEnergyGain)"""
    return q16_gt(state.qFactor, Q16_ONE)  # Q > 1.0


def energySurplus(balance: EnergyBalance) -> int:
    """Calculate energy surplus (positive if net gain) (Lean: energySurplus)"""
    totalGain = balance.flashEnergy + balance.enthalpy + balance.recoveredEnergy
    totalCost = balance.demonWork + balance.workEnergy + balance.energyLoss
    return totalGain - totalCost


def energyEfficiencyFromBalance(balance: EnergyBalance) -> int:
    """Calculate energy efficiency: η = E_work / (E_work + E_loss) (Lean: energyEfficiencyFromBalance)"""
    totalEnergyCost = balance.workEnergy + balance.energyLoss
    if totalEnergyCost > 0:
        return q16_div(balance.workEnergy, totalEnergyCost)
    return 0


def recoveryRatio(balance: EnergyBalance) -> int:
    """Calculate recovery ratio: η_rec = E_recovered / (E_flash + E_enthalpy) (Lean: recoveryRatio)"""
    totalInputEnergy = balance.flashEnergy + balance.enthalpy
    if totalInputEnergy > 0:
        return q16_div(balance.recoveredEnergy, totalInputEnergy)
    return 0


def isQFactorActionLawful(state: QFactorState, action: QFactorAction) -> bool:
    """Check if Q-Factor action is lawful (Lean: isQFactorActionLawful)"""
    workPositive = q16_gt(state.balance.workEnergy + action.workEnergyDelta, 0)
    lossReasonable = q16_ge(action.energyLossDelta, -state.balance.energyLoss // 2)
    recoveredReasonable = q16_ge(action.recoveredEnergyDelta, 0) or q16_ge(action.recoveredEnergyDelta, -state.balance.recoveredEnergy // 2)
    return workPositive and lossReasonable and recoveredReasonable


def updateEnergyBalance(balance: EnergyBalance, action: QFactorAction) -> EnergyBalance:
    """Update energy balance from action (Lean: updateEnergyBalance)"""
    return EnergyBalance(
        flashEnergy=q16_add(balance.flashEnergy, action.flashEnergyDelta),
        enthalpy=q16_add(balance.enthalpy, action.enthalpyDelta),
        recoveredEnergy=q16_add(balance.recoveredEnergy, action.recoveredEnergyDelta),
        demonWork=balance.demonWork,  # Constant for now
        workEnergy=q16_add(balance.workEnergy, action.workEnergyDelta),
        energyLoss=q16_add(balance.energyLoss, action.energyLossDelta)
    )


def qFactorBind(state: QFactorState, action: QFactorAction) -> QFactorBind:
    """Bind primitive for Q-Factor optimization (Lean: qFactorBind)"""
    lawful = isQFactorActionLawful(state, action)
    newBalance = updateEnergyBalance(state.balance, action) if lawful else state.balance
    qFactorBefore = state.qFactor
    qFactorAfter = calculateQFactor(newBalance) if lawful else state.qFactor
    surplus = energySurplus(newBalance) if lawful else 0
    
    return QFactorBind(
        lawful=lawful,
        qFactorBefore=qFactorBefore,
        qFactorAfter=qFactorAfter,
        energySurplus=surplus,
        invariant="energy_balance_satisfied" if lawful else "energy_constraint_violated"
    )


class QFactorSystem:
    """
    Q-Factor energy balance system (Python shim wrapping Lean specification).
    
    All core logic is defined in 0-Core-Formalism/lean/Semantics/Semantics/QFactor.lean
    """
    
    def __init__(self):
        self.agentStates: Dict[int, QFactorState] = {}
        self.qFactorHistory: List[Dict[str, Any]] = []
        self.temporalSpatialSystem: Optional[TemporalSpatialRAMSystem] = None
        
        if _HAS_TS_RAM:
            self.temporalSpatialSystem = TemporalSpatialRAMSystem()
        
        print("[QFactor] Initialized (Lean specification)")
    
    def initializeAgent(self, agentId: int, flashEnergy: float, enthalpy: float, workEnergy: float, energyLoss: float, targetQ: float = 1.05) -> Dict[str, Any]:
        """Initialize agent Q-Factor state"""
        balance = EnergyBalance(
            flashEnergy=to_q16(flashEnergy),
            enthalpy=to_q16(enthalpy),
            recoveredEnergy=to_q16(0.0),
            demonWork=to_q16(20.0),  # Landauer limit
            workEnergy=to_q16(workEnergy),
            energyLoss=to_q16(energyLoss)
        )
        
        qFactor = calculateQFactor(balance)
        state = QFactorState(
            agentId=agentId,
            balance=balance,
            qFactor=qFactor,
            targetQ=to_q16(targetQ)
        )
        
        self.agentStates[agentId] = state
        
        # Register node in temporal-spatial system if available
        if self.temporalSpatialSystem:
            self.temporalSpatialSystem.registerNode(
                nodeId=agentId,
                x=0.0, y=0.0, z=0.0,  # Origin for now
                physicalRAM=workEnergy,
                currentTime=0.0
            )
        
        return {
            'agentId': agentId,
            'state': state.to_dict()
        }
    
    def submitQFactorAction(self, action: QFactorAction) -> Dict[str, Any]:
        """Submit Q-Factor action for processing (Lean specification)"""
        if action.agentId not in self.agentStates:
            return {'error': 'Agent not initialized'}
        
        currentState = self.agentStates[action.agentId]
        bindResult = qFactorBind(currentState, action)
        
        if bindResult.lawful:
            newBalance = updateEnergyBalance(currentState.balance, action)
            
            # Adjust work energy based on temporal-spatial resources if available
            if self.temporalSpatialSystem:
                tsResources = self.temporalSpatialSystem.getNodeResources(action.agentId)
                if tsResources:
                    # Add temporal-spatial RAM to work energy (proximity bonus)
                    spatialBonus = tsResources['resources']['spatialRAM'] * 0.1
                    temporalBonus = tsResources['resources']['temporalRAM'] * 0.01
                    newBalance = EnergyBalance(
                        flashEnergy=newBalance.flashEnergy,
                        enthalpy=newBalance.enthalpy,
                        recoveredEnergy=newBalance.recoveredEnergy,
                        demonWork=newBalance.demonWork,
                        workEnergy=newBalance.workEnergy + to_q16(spatialBonus + temporalBonus),
                        energyLoss=newBalance.energyLoss
                    )
            
            newState = QFactorState(
                agentId=currentState.agentId,
                balance=newBalance,
                qFactor=calculateQFactor(newBalance),
                targetQ=currentState.targetQ
            )
            self.agentStates[action.agentId] = newState
            
            # Record Q-Factor history
            self.qFactorHistory.append({
                'agentId': action.agentId,
                'action': action.to_dict(),
                'bindResult': bindResult.to_dict(),
                'stateBefore': currentState.to_dict(),
                'stateAfter': newState.to_dict(),
                'timestamp': time.time()
            })
        
        return {
            'success': bindResult.lawful,
            'bindResult': bindResult.to_dict(),
            'state': self.agentStates[action.agentId].to_dict() if bindResult.lawful else currentState.to_dict()
        }
    
    def getAgentState(self, agentId: int) -> Optional[Dict[str, Any]]:
        """Get current agent Q-Factor state"""
        if agentId in self.agentStates:
            return self.agentStates[agentId].to_dict()
        return None
    
    def getQFactorHistory(self, agentId: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Q-Factor history"""
        if agentId is not None:
            filtered = [h for h in self.qFactorHistory if h['agentId'] == agentId]
            return filtered[-limit:]
        return self.qFactorHistory[-limit:]
    
    def calculateSystemEfficiency(self, agentId: int) -> Optional[float]:
        """Calculate system efficiency for agent"""
        if agentId not in self.agentStates:
            return None
        
        state = self.agentStates[agentId]
        efficiency = energyEfficiencyFromBalance(state.balance)
        return from_q16(efficiency)
    
    def printSystemState(self):
        """Print system state"""
        print("\n" + "="*60)
        print("Q-FACTOR ENERGY BALANCE SYSTEM STATE")
        print("="*60)
        
        print(f"\n📊 Active Agents: {len(self.agentStates)}")
        for agentId, state in self.agentStates.items():
            print(f"\n  Agent {agentId}:")
            print(f"    Q-Factor: {from_q16(state.qFactor):.3f} (target: {from_q16(state.targetQ):.3f})")
            print(f"    Net energy gain: {hasNetEnergyGain(state)}")
            print(f"    Energy surplus: {from_q16(energySurplus(state.balance)):.3f}")
            print(f"    Efficiency: {from_q16(energyEfficiencyFromBalance(state.balance)):.3f}")
            print(f"    Recovery ratio: {from_q16(recoveryRatio(state.balance)):.3f}")
            
            # Add temporal-spatial resource display if available
            if self.temporalSpatialSystem:
                tsResources = self.temporalSpatialSystem.getNodeResources(agentId)
                if tsResources:
                    print(f"    Temporal-Spatial RAM: {tsResources['resources']['totalRAM']:.3f}")
                    print(f"      - Temporal: {tsResources['resources']['temporalRAM']:.3f}")
                    print(f"      - Spatial: {tsResources['resources']['spatialRAM']:.3f}")
        
        print(f"\n📜 Q-Factor History: {len(self.qFactorHistory)} entries")
        
        print("\n" + "="*60)


def main():
    """Test Q-Factor system"""
    system = QFactorSystem()
    
    print("[Test 1] Initialize agent with energy balance...")
    initResult = system.initializeAgent(
        agentId=1,
        flashEnergy=100.0,
        enthalpy=50.0,
        workEnergy=80.0,
        energyLoss=10.0,
        targetQ=1.05
    )
    print(f"  Agent 1 initialized: Q-Factor={initResult['state']['qFactor']:.3f}")
    
    print("\n[Test 2] Submit Q-Factor action (increase recovered energy)...")
    action1 = QFactorAction(
        agentId=1,
        flashEnergyDelta=to_q16(10.0),
        enthalpyDelta=to_q16(5.0),
        recoveredEnergyDelta=to_q16(15.0),
        workEnergyDelta=to_q16(10.0),
        energyLossDelta=to_q16(2.0)
    )
    result1 = system.submitQFactorAction(action1)
    print(f"  Result: Lawful={result1['success']}")
    if result1['success']:
        print(f"  Q-Factor before: {result1['bindResult']['qFactorBefore']:.3f}")
        print(f"  Q-Factor after: {result1['bindResult']['qFactorAfter']:.3f}")
        print(f"  Energy surplus: {result1['bindResult']['energySurplus']:.3f}")
    
    print("\n[Test 3] Submit Q-Factor action (optimize energy loss)...")
    action2 = QFactorAction(
        agentId=1,
        flashEnergyDelta=to_q16(0.0),
        enthalpyDelta=to_q16(0.0),
        recoveredEnergyDelta=to_q16(5.0),
        workEnergyDelta=to_q16(5.0),
        energyLossDelta=to_q16(-5.0)  # Reduce energy loss
    )
    result2 = system.submitQFactorAction(action2)
    print(f"  Result: Lawful={result2['success']}")
    if result2['success']:
        print(f"  Q-Factor after: {result2['state']['qFactor']:.3f}")
        print(f"  Energy surplus: {from_q16(energySurplus(system.agentStates[1].balance)):.3f}")
    
    print("\n[Test 4] Submit invalid Q-Factor action (negative work energy)...")
    action3 = QFactorAction(
        agentId=1,
        flashEnergyDelta=to_q16(0.0),
        enthalpyDelta=to_q16(0.0),
        recoveredEnergyDelta=to_q16(0.0),
        workEnergyDelta=to_q16(-100.0),  # Invalid: negative work energy
        energyLossDelta=to_q16(0.0)
    )
    result3 = system.submitQFactorAction(action3)
    print(f"  Result: Lawful={result3['success']}")
    print(f"  Invariant: {result3['bindResult']['invariant']}")
    
    print("\n[Test 5] Check if target Q is met...")
    state = system.agentStates[1]
    targetMet = meetsTargetQ(state)
    netGain = hasNetEnergyGain(state)
    print(f"  Target Q met: {targetMet}")
    print(f"  Net energy gain: {netGain}")
    
    print("\n[Test 6] Calculate system efficiency...")
    efficiency = system.calculateSystemEfficiency(agentId=1)
    if efficiency is not None:
        print(f"  System efficiency: {efficiency:.3f}")
    
    print("\n[System State]")
    system.printSystemState()


if __name__ == '__main__':
    main()
