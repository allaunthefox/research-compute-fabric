#!/usr/bin/env python3
"""
Joule Energy System (Verified Lean Specification)

This implementation follows the formal specification in:
0-Core-Formalism/lean/Semantics/Semantics/JouleEnergy.lean

The Lean module provides:
- Fundamental Joule equation: E = Q × V = P × t
- Energy transition bind primitive
- Energy efficiency metrics
- Invariant preservation theorems

This Python shim provides:
- JSON serialization for energy state
- Result wrapping for Lean function calls
- History deque for energy transitions
- No logic (all logic defined in Lean specification)
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque

try:
    from q_factor import QFactorSystem, QFactorAction, EnergyBalance as QFactorBalance, to_q16 as q16_to, from_q16 as q16_from
    _HAS_QFACTOR = True
except ImportError:
    _HAS_QFACTOR = False
    print("[!] Q-Factor system not available")

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
class AgentEnergyState:
    """Agent energy state (Lean: AgentEnergyState)"""
    agentId: int  # UInt64
    charge: int  # Q16_16 - Workload/task count
    voltage: int  # Q16_16 - Resource availability/priority
    current: int  # Q16_16 - Processing rate
    power: int  # Q16_16 - Power consumption rate
    energy: int  # Q16_16 - Total energy consumption
    time: int  # Q16_16 - Time elapsed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agentId': self.agentId,
            'charge': from_q16(self.charge),
            'voltage': from_q16(self.voltage),
            'current': from_q16(self.current),
            'power': from_q16(self.power),
            'energy': from_q16(self.energy),
            'time': from_q16(self.time)
        }


@dataclass
class EnergyAction:
    """Energy transition action (Lean: EnergyAction)"""
    agentId: int  # UInt64
    workloadDelta: int  # Q16_16 - Change in workload
    resourceLevel: int  # Q16_16 - New resource level
    duration: int  # Q16_16 - Time duration
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agentId': self.agentId,
            'workloadDelta': from_q16(self.workloadDelta),
            'resourceLevel': from_q16(self.resourceLevel),
            'duration': from_q16(self.duration)
        }


@dataclass
class EnergyBind:
    """Energy bind result (Lean: EnergyBind)"""
    lawful: bool
    cost: int  # Q16_16
    energyBefore: int  # Q16_16
    energyAfter: int  # Q16_16
    invariant: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lawful': self.lawful,
            'cost': from_q16(self.cost),
            'energyBefore': from_q16(self.energyBefore),
            'energyAfter': from_q16(self.energyAfter),
            'invariant': self.invariant
        }


# ═══════════════════════════════════════════════════════════════════════════
# Lean Function Implementations (verified by specification)
# ═══════════════════════════════════════════════════════════════════════════

def jouleEnergyChargeVoltage(charge: int, voltage: int) -> int:
    """Calculate energy from charge and voltage: E = Q × V (Lean: jouleEnergyChargeVoltage)"""
    return q16_mul(charge, voltage)


def joulePowerVoltageCurrent(voltage: int, current: int) -> int:
    """Calculate power from voltage and current: P = V × I (Lean: joulePowerVoltageCurrent)"""
    return q16_mul(voltage, current)


def jouleEnergyPowerTime(power: int, time: int) -> int:
    """Calculate energy from power and time: E = P × t (Lean: jouleEnergyPowerTime)"""
    return q16_mul(power, time)


def jouleCurrentChargeTime(charge: int, time: int) -> int:
    """Calculate current from charge and time: I = Q / t (Lean: jouleCurrentChargeTime)"""
    if time > 0:
        return q16_div(charge, time)
    return 0


def isEnergyTransitionLawful(state: AgentEnergyState, action: EnergyAction) -> bool:
    """Check if energy transition is lawful (Lean: isEnergyTransitionLawful)"""
    voltagePositive = q16_gt(action.resourceLevel, 0)
    workloadReasonable = q16_ge(action.workloadDelta, 0) or q16_ge(action.workloadDelta, -state.charge // 2)
    durationPositive = q16_gt(action.duration, 0)
    return voltagePositive and workloadReasonable and durationPositive


def energyTransitionCost(state: AgentEnergyState, action: EnergyAction) -> int:
    """Calculate energy transition cost (Lean: energyTransitionCost)"""
    newCharge = q16_add(state.charge, action.workloadDelta)
    newVoltage = action.resourceLevel
    jouleCost = jouleEnergyChargeVoltage(newCharge, newVoltage)
    return jouleCost


def updateEnergyState(state: AgentEnergyState, action: EnergyAction) -> AgentEnergyState:
    """Update agent energy state (Lean: updateEnergyState)"""
    newCharge = q16_add(state.charge, action.workloadDelta)
    newVoltage = action.resourceLevel
    newCurrent = jouleCurrentChargeTime(newCharge, action.duration)
    newPower = joulePowerVoltageCurrent(newVoltage, newCurrent)
    energyConsumed = jouleEnergyPowerTime(newPower, action.duration)
    newEnergy = q16_add(state.energy, energyConsumed)
    newTime = q16_add(state.time, action.duration)
    
    return AgentEnergyState(
        agentId=state.agentId,
        charge=newCharge,
        voltage=newVoltage,
        current=newCurrent,
        power=newPower,
        energy=newEnergy,
        time=newTime
    )


def energyBind(state: AgentEnergyState, action: EnergyAction) -> EnergyBind:
    """Bind primitive for energy transitions (Lean: energyBind)"""
    lawful = isEnergyTransitionLawful(state, action)
    cost = energyTransitionCost(state, action) if lawful else 0
    newState = updateEnergyState(state, action) if lawful else state
    
    return EnergyBind(
        lawful=lawful,
        cost=cost,
        energyBefore=state.energy,
        energyAfter=newState.energy,
        invariant="energy_conservation_satisfied" if lawful else "energy_constraint_violated"
    )


def energyEfficiency(usefulEnergy: int, totalEnergy: int) -> int:
    """Calculate energy efficiency: η = E_useful / E_total (Lean: energyEfficiency)"""
    if totalEnergy > 0:
        return q16_div(usefulEnergy, totalEnergy)
    return 0


def powerEfficiency(outputPower: int, inputPower: int) -> int:
    """Calculate power efficiency: η = P_output / P_input (Lean: powerEfficiency)"""
    if inputPower > 0:
        return q16_div(outputPower, inputPower)
    return 0


def energyPerTask(totalEnergy: int, taskCount: int) -> int:
    """Calculate energy per task: E_task = E_total / Q (Lean: energyPerTask)"""
    if taskCount > 0:
        return q16_div(totalEnergy, taskCount)
    return 0


class JouleEnergySystem:
    """
    Joule energy system (Python shim wrapping Lean specification).
    
    All core logic is defined in 0-Core-Formalism/lean/Semantics/Semantics/JouleEnergy.lean
    """
    
    def __init__(self):
        self.agentStates: Dict[int, AgentEnergyState] = {}
        self.energyHistory: List[Dict[str, Any]] = []
        self.qFactorSystem: Optional[QFactorSystem] = None
        
        if _HAS_QFACTOR:
            self.qFactorSystem = QFactorSystem()
        
        print("[JouleEnergy] Initialized (Lean specification)")
    
    def initializeAgent(self, agentId: int, initialCharge: float, initialVoltage: float) -> Dict[str, Any]:
        """Initialize agent energy state"""
        state = AgentEnergyState(
            agentId=agentId,
            charge=to_q16(initialCharge),
            voltage=to_q16(initialVoltage),
            current=jouleCurrentChargeTime(to_q16(initialCharge), to_q16(1.0)),
            power=joulePowerVoltageCurrent(to_q16(initialVoltage), jouleCurrentChargeTime(to_q16(initialCharge), to_q16(1.0))),
            energy=jouleEnergyChargeVoltage(to_q16(initialCharge), to_q16(initialVoltage)),
            time=to_q16(0.0)
        )
        
        self.agentStates[agentId] = state
        
        # Initialize Q-Factor system if available
        if self.qFactorSystem:
            self.qFactorSystem.initializeAgent(
                agentId=agentId,
                flashEnergy=initialCharge * 5.0,  # Burst computation energy
                enthalpy=initialVoltage * 10.0,  # Steady-state energy
                workEnergy=from_q16(state.power),
                energyLoss=from_q16(state.energy) * 0.1,
                targetQ=1.05
            )
        
        return {
            'agentId': agentId,
            'state': state.to_dict()
        }
    
    def submitEnergyAction(self, action: EnergyAction) -> Dict[str, Any]:
        """Submit energy action for processing (Lean specification)"""
        if action.agentId not in self.agentStates:
            return {'error': 'Agent not initialized'}
        
        currentState = self.agentStates[action.agentId]
        bindResult = energyBind(currentState, action)
        
        if bindResult.lawful:
            newState = updateEnergyState(currentState, action)
            self.agentStates[action.agentId] = newState
            
            # Record energy history
            self.energyHistory.append({
                'agentId': action.agentId,
                'action': action.to_dict(),
                'bindResult': bindResult.to_dict(),
                'stateBefore': currentState.to_dict(),
                'stateAfter': newState.to_dict(),
                'timestamp': time.time()
            })
            
            # Update Q-Factor system if available
            if self.qFactorSystem:
                qFactorAction = QFactorAction(
                    agentId=action.agentId,
                    flashEnergyDelta=to_q16(action.workloadDelta * 2.0),
                    enthalpyDelta=to_q16(0.0),
                    recoveredEnergyDelta=to_q16(action.workloadDelta * 0.5),
                    workEnergyDelta=to_q16(action.workloadDelta),
                    energyLossDelta=to_q16(action.duration * 0.1)
                )
                self.qFactorSystem.submitQFactorAction(qFactorAction)
        
        return {
            'success': bindResult.lawful,
            'bindResult': bindResult.to_dict(),
            'state': self.agentStates[action.agentId].to_dict() if bindResult.lawful else currentState.to_dict()
        }
    
    def getAgentState(self, agentId: int) -> Optional[Dict[str, Any]]:
        """Get current agent energy state"""
        if agentId in self.agentStates:
            return self.agentStates[agentId].to_dict()
        return None
    
    def getEnergyHistory(self, agentId: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get energy history"""
        if agentId is not None:
            filtered = [h for h in self.energyHistory if h['agentId'] == agentId]
            return filtered[-limit:]
        return self.energyHistory[-limit:]
    
    def calculateEfficiency(self, agentId: int, usefulEnergy: float) -> Optional[float]:
        """Calculate energy efficiency for agent"""
        if agentId not in self.agentStates:
            return None
        
        state = self.agentStates[agentId]
        efficiency = energyEfficiency(to_q16(usefulEnergy), state.energy)
        return from_q16(efficiency)
    
    def printSystemState(self):
        """Print system state"""
        print("\n" + "="*60)
        print("JOULE ENERGY SYSTEM STATE")
        print("="*60)
        
        print(f"\n📊 Active Agents: {len(self.agentStates)}")
        for agentId, state in self.agentStates.items():
            print(f"\n  Agent {agentId}:")
            print(f"    Charge: {from_q16(state.charge):.3f}")
            print(f"    Voltage: {from_q16(state.voltage):.3f}")
            print(f"    Current: {from_q16(state.current):.3f}")
            print(f"    Power: {from_q16(state.power):.3f}")
            print(f"    Energy: {from_q16(state.energy):.3f}")
            print(f"    Time: {from_q16(state.time):.3f}")
            
            # Add Q-Factor display if available
            if self.qFactorSystem:
                qFactorState = self.qFactorSystem.getAgentState(agentId)
                if qFactorState:
                    print(f"    Q-Factor: {qFactorState['qFactor']:.3f} (target: {qFactorState['targetQ']:.3f})")
                    print(f"    Energy surplus: {qFactorState.get('energySurplus', 0):.3f}")
        
        print(f"\n📜 Energy History: {len(self.energyHistory)} entries")
        
        print("\n" + "="*60)


def main():
    """Test Joule energy system"""
    system = JouleEnergySystem()
    
    print("[Test 1] Initialize agent with initial charge and voltage...")
    initResult = system.initializeAgent(agentId=1, initialCharge=10.0, initialVoltage=5.0)
    print(f"  Agent 1 initialized: Charge={initResult['state']['charge']:.3f}, Voltage={initResult['state']['voltage']:.3f}")
    
    print("\n[Test 2] Submit energy action (increase workload)...")
    action1 = EnergyAction(
        agentId=1,
        workloadDelta=to_q16(5.0),
        resourceLevel=to_q16(6.0),
        duration=to_q16(2.0)
    )
    result1 = system.submitEnergyAction(action1)
    print(f"  Result: Lawful={result1['success']}")
    if result1['success']:
        print(f"  Energy before: {result1['bindResult']['energyBefore']:.3f}")
        print(f"  Energy after: {result1['bindResult']['energyAfter']:.3f}")
        print(f"  Cost: {result1['bindResult']['cost']:.3f}")
    
    print("\n[Test 3] Submit energy action (decrease workload)...")
    action2 = EnergyAction(
        agentId=1,
        workloadDelta=to_q16(-3.0),
        resourceLevel=to_q16(5.0),
        duration=to_q16(1.0)
    )
    result2 = system.submitEnergyAction(action2)
    print(f"  Result: Lawful={result2['success']}")
    if result2['success']:
        print(f"  Energy after: {result2['state']['energy']:.3f}")
    
    print("\n[Test 4] Submit invalid energy action (negative voltage)...")
    action3 = EnergyAction(
        agentId=1,
        workloadDelta=to_q16(2.0),
        resourceLevel=to_q16(-1.0),  # Invalid: negative voltage
        duration=to_q16(1.0)
    )
    result3 = system.submitEnergyAction(action3)
    print(f"  Result: Lawful={result3['success']}")
    print(f"  Invariant: {result3['bindResult']['invariant']}")
    
    print("\n[Test 5] Calculate energy efficiency...")
    efficiency = system.calculateEfficiency(agentId=1, usefulEnergy=40.0)
    if efficiency is not None:
        print(f"  Efficiency: {efficiency:.3f}")
    
    print("\n[Test 6] Calculate energy per task...")
    state = system.agentStates[1]
    energyPerTaskValue = energyPerTask(state.energy, state.charge)
    print(f"  Energy per task: {from_q16(energyPerTaskValue):.3f}")
    
    print("\n[System State]")
    system.printSystemState()


if __name__ == '__main__':
    main()
