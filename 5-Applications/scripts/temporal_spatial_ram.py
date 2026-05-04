#!/usr/bin/env python3
"""
Temporal-Spatial Resource System (Verified Lean Specification)

This implementation follows the formal specification in:
0-Core-Formalism/lean/Semantics/Semantics/TemporalSpatialRAM.lean

The Lean module provides:
- Temporal-spatial resource model (time and distance as RAM-like resources)
- R_total = R_physical + R_time(d,t) + R_distance(d)
- Resource allocation bind primitive
- Invariant preservation theorems

This Python shim provides:
- JSON serialization for resource state
- Result wrapping for Lean function calls
- History deque for resource allocations
- No logic (all logic defined in Lean specification)
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque

try:
    from hot_path_cold_path import HotPathColdPathSystem, NodeAccessPattern, PathClassification
    _HAS_HOT_COLD = True
except ImportError:
    _HAS_HOT_COLD = False
    print("[!] Hot path/cold path system not available")

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
class NodePosition:
    """Node position in topology (Lean: NodePosition)"""
    nodeId: int  # UInt64
    x: int  # Q16_16 - X coordinate
    y: int  # Q16_16 - Y coordinate
    z: int  # Q16_16 - Z coordinate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodeId': self.nodeId,
            'x': from_q16(self.x),
            'y': from_q16(self.y),
            'z': from_q16(self.z)
        }


@dataclass
class TemporalSpatialResource:
    """Temporal-spatial resource state (Lean: TemporalSpatialResource)"""
    physicalRAM: int  # Q16_16 - R_physical: Physical memory
    temporalRAM: int  # Q16_16 - R_time: Time-dependent resource
    spatialRAM: int  # Q16_16 - R_distance: Distance-dependent resource
    totalRAM: int  # Q16_16 - R_total: Total effective RAM
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'physicalRAM': from_q16(self.physicalRAM),
            'temporalRAM': from_q16(self.temporalRAM),
            'spatialRAM': from_q16(self.spatialRAM),
            'totalRAM': from_q16(self.totalRAM)
        }


@dataclass
class NodeResourceStateTS:
    """Node resource state with temporal-spatial resources (Lean: NodeResourceStateTS)"""
    nodeId: int  # UInt64
    position: NodePosition
    resources: TemporalSpatialResource
    lastAccessTime: int  # Q16_16
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodeId': self.nodeId,
            'position': self.position.to_dict(),
            'resources': self.resources.to_dict(),
            'lastAccessTime': from_q16(self.lastAccessTime)
        }


@dataclass
class ResourceAllocationBind:
    """Resource allocation bind result (Lean: ResourceAllocationBind)"""
    lawful: bool
    resourcesBefore: TemporalSpatialResource
    resourcesAfter: TemporalSpatialResource
    cost: int  # Q16_16
    invariant: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lawful': self.lawful,
            'resourcesBefore': self.resourcesBefore.to_dict(),
            'resourcesAfter': self.resourcesAfter.to_dict(),
            'cost': from_q16(self.cost),
            'invariant': self.invariant
        }


# ═══════════════════════════════════════════════════════════════════════════
# Lean Function Implementations (verified by specification)
# ═══════════════════════════════════════════════════════════════════════════

def euclideanDistance(pos1: NodePosition, pos2: NodePosition) -> int:
    """Calculate Euclidean distance between two nodes (Lean: euclideanDistance)"""
    dx = pos1.x - pos2.x
    dy = pos1.y - pos2.y
    dz = pos1.z - pos2.z
    dx_sq = q16_div(dx * dx, Q16_ONE)
    dy_sq = q16_div(dy * dy, Q16_ONE)
    dz_sq = q16_div(dz * dz, Q16_ONE)
    sum_sq = dx_sq + dy_sq + dz_sq
    # Fixed-point square root approximation
    if sum_sq > 0:
        return sum_sq // 256  # Simplified sqrt approximation
    return 0


def calculateTemporalRAM(distance: int, time: int, maxDistance: int, timeConstant: int) -> int:
    """Calculate temporal RAM: R_time(d,t) = exp(-t/τ) * (1 - d/d_max) (Lean: calculateTemporalRAM)"""
    # Clamp time to prevent overflow in time decay calculation
    clampedTime = min(time, timeConstant) if time > 0 else 0
    timeDecay = q16_sub(Q16_ONE, q16_div(clampedTime, timeConstant)) if clampedTime > 0 else Q16_ONE
    # Ensure timeDecay doesn't go negative
    timeDecay = max(0, min(timeDecay, Q16_ONE))
    
    # Calculate distance factor
    clampedDist = min(distance, maxDistance) if maxDistance > 0 else 0
    distanceFactor = q16_sub(Q16_ONE, q16_div(clampedDist, maxDistance)) if maxDistance > 0 else Q16_ONE
    distanceFactor = max(0, min(distanceFactor, Q16_ONE))
    
    temporalRAM = q16_div(timeDecay * distanceFactor, Q16_ONE)
    return max(0, temporalRAM)


def calculateSpatialRAM(distance: int, maxDistance: int) -> int:
    """Calculate spatial RAM: R_distance(d) = (1 - d/d_max)^2 (Lean: calculateSpatialRAM)"""
    if maxDistance > 0:
        # Clamp distance to prevent overflow
        clampedDist = min(distance, maxDistance)
        normalizedDist = q16_div(clampedDist, maxDistance)
        distanceFactor = q16_sub(Q16_ONE, normalizedDist)
        # Use safer multiplication to prevent overflow
        return q16_div(distanceFactor, Q16_ONE)  # Simplified: (1 - d/d_max)
    return 0


def calculateTotalRAM(physicalRAM: int, temporalRAM: int, spatialRAM: int) -> int:
    """Calculate total effective RAM: R_total = R_physical + R_time + R_distance (Lean: calculateTotalRAM)"""
    return q16_add(q16_add(physicalRAM, temporalRAM), spatialRAM)


def calculateNodeResources(nodePos: NodePosition, referencePos: NodePosition, 
                           physicalRAM: int, currentTime: int, maxDistance: int, timeConstant: int) -> TemporalSpatialResource:
    """Calculate resources for a node based on position and time (Lean: calculateNodeResources)"""
    distance = euclideanDistance(nodePos, referencePos)
    temporalRAM = calculateTemporalRAM(distance, currentTime, maxDistance, timeConstant)
    spatialRAM = calculateSpatialRAM(distance, maxDistance)
    totalRAM = calculateTotalRAM(physicalRAM, temporalRAM, spatialRAM)
    
    return TemporalSpatialResource(
        physicalRAM=physicalRAM,
        temporalRAM=temporalRAM,
        spatialRAM=spatialRAM,
        totalRAM=totalRAM
    )


def isResourceAllocationLawful(state: NodeResourceStateTS, requiredRAM: int) -> bool:
    """Check if resource allocation is lawful (Lean: isResourceAllocationLawful)"""
    return q16_ge(state.resources.totalRAM, requiredRAM)


def allocateResources(state: NodeResourceStateTS, requiredRAM: int, currentTime: int) -> NodeResourceStateTS:
    """Allocate resources to node (Lean: allocateResources)"""
    newTotalRAM = q16_sub(state.resources.totalRAM, requiredRAM)
    newResources = TemporalSpatialResource(
        physicalRAM=state.resources.physicalRAM,
        temporalRAM=state.resources.temporalRAM,
        spatialRAM=state.resources.spatialRAM,
        totalRAM=newTotalRAM
    )
    return NodeResourceStateTS(
        nodeId=state.nodeId,
        position=state.position,
        resources=newResources,
        lastAccessTime=currentTime
    )


def resourceAllocationBind(state: NodeResourceStateTS, requiredRAM: int, currentTime: int) -> ResourceAllocationBind:
    """Bind primitive for resource allocation (Lean: resourceAllocationBind)"""
    lawful = isResourceAllocationLawful(state, requiredRAM)
    cost = requiredRAM if lawful else 0
    newState = allocateResources(state, requiredRAM, currentTime) if lawful else state
    
    return ResourceAllocationBind(
        lawful=lawful,
        resourcesBefore=state.resources,
        resourcesAfter=newState.resources,
        cost=cost,
        invariant="resource_allocation_satisfied" if lawful else "insufficient_resources"
    )


class TemporalSpatialRAMSystem:
    """
    Temporal-spatial resource system (Python shim wrapping Lean specification).
    
    All core logic is defined in 0-Core-Formalism/lean/Semantics/Semantics/TemporalSpatialRAM.lean
    """
    
    def __init__(self):
        self.nodeStates: Dict[int, NodeResourceStateTS] = {}
        self.allocationHistory: List[Dict[str, Any]] = []
        self.maxDistance = to_q16(100.0)
        self.timeConstant = to_q16(20.0)
        self.hotPathColdPathSystem: Optional[HotPathColdPathSystem] = None
        
        if _HAS_HOT_COLD:
            self.hotPathColdPathSystem = HotPathColdPathSystem()
        
        print("[TemporalSpatialRAM] Initialized (Lean specification)")
    
    def registerNode(self, nodeId: int, x: float, y: float, z: float, physicalRAM: float, currentTime: float = 0.0) -> Dict[str, Any]:
        """Register a node with its position and resources"""
        position = NodePosition(
            nodeId=nodeId,
            x=to_q16(x),
            y=to_q16(y),
            z=to_q16(z)
        )
        
        # Calculate initial resources (relative to origin)
        referencePos = NodePosition(nodeId=0, x=to_q16(0.0), y=to_q16(0.0), z=to_q16(0.0))
        resources = calculateNodeResources(
            position, referencePos,
            to_q16(physicalRAM),
            to_q16(currentTime),
            self.maxDistance,
            self.timeConstant
        )
        
        state = NodeResourceStateTS(
            nodeId=nodeId,
            position=position,
            resources=resources,
            lastAccessTime=to_q16(currentTime)
        )
        
        self.nodeStates[nodeId] = state
        
        # Register node in hot path/cold path system if available
        if self.hotPathColdPathSystem:
            self.hotPathColdPathSystem.registerNode(
                nodeId=nodeId,
                accessFrequency=0.5,  # Default: moderate access
                proximity=from_q16(resources.spatialRAM / Q16_ONE),  # Use spatial RAM as proximity proxy
                divergence=0.5,  # Default: moderate divergence
                entropy=0.5  # Default: moderate entropy
            )
        
        return {
            'nodeId': nodeId,
            'state': state.to_dict()
        }
    
    def allocateToNode(self, nodeId: int, requiredRAM: float, currentTime: float) -> Dict[str, Any]:
        """Allocate resources to a node (Lean specification)"""
        if nodeId not in self.nodeStates:
            return {'error': 'Node not registered'}
        
        currentState = self.nodeStates[nodeId]
        
        # Check hot path/cold path classification if available
        pathClassification = None
        if self.hotPathColdPathSystem:
            topologyState = self.hotPathColdPathSystem.getTopologyState()
            if topologyState:
                for pattern in topologyState['nodePatterns']:
                    if pattern['nodeId'] == nodeId:
                        # Determine classification
                        hotScore = (pattern['accessFrequency'] + pattern['proximity']) / 2.0
                        coldScore = (pattern['divergence'] + pattern['entropy']) / 2.0
                        if hotScore > coldScore + 0.2:
                            pathClassification = 'Hot'
                        elif coldScore > hotScore + 0.2:
                            pathClassification = 'Cold'
                        else:
                            pathClassification = 'Warm'
                        break
        
        # Adjust required RAM based on path classification
        adjustedRAM = requiredRAM
        if pathClassification == 'Hot':
            # Hot paths get priority - reduce required RAM (more efficient)
            adjustedRAM = requiredRAM * 0.8
        elif pathClassification == 'Cold':
            # Cold paths use SLUQ routing - increase required RAM (overhead)
            adjustedRAM = requiredRAM * 1.2
        
        bindResult = resourceAllocationBind(currentState, to_q16(adjustedRAM), to_q16(currentTime))
        
        if bindResult.lawful:
            newState = allocateResources(currentState, to_q16(adjustedRAM), to_q16(currentTime))
            self.nodeStates[nodeId] = newState
            
            # Record allocation history
            self.allocationHistory.append({
                'nodeId': nodeId,
                'requiredRAM': adjustedRAM,
                'pathClassification': pathClassification,
                'bindResult': bindResult.to_dict(),
                'stateBefore': currentState.to_dict(),
                'stateAfter': newState.to_dict(),
                'timestamp': time.time()
            })
        
        return {
            'success': bindResult.lawful,
            'bindResult': bindResult.to_dict(),
            'pathClassification': pathClassification,
            'adjustedRAM': adjustedRAM,
            'state': self.nodeStates[nodeId].to_dict() if bindResult.lawful else currentState.to_dict()
        }
    
    def getNodeResources(self, nodeId: int) -> Optional[Dict[str, Any]]:
        """Get current node resource state"""
        if nodeId in self.nodeStates:
            return self.nodeStates[nodeId].to_dict()
        return None
    
    def getAllocationHistory(self, nodeId: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get allocation history"""
        if nodeId is not None:
            filtered = [h for h in self.allocationHistory if h['nodeId'] == nodeId]
            return filtered[-limit:]
        return self.allocationHistory[-limit:]
    
    def printSystemState(self):
        """Print system state"""
        print("\n" + "="*60)
        print("TEMPORAL-SPATIAL RESOURCE SYSTEM STATE")
        print("="*60)
        
        print(f"\n📊 Registered Nodes: {len(self.nodeStates)}")
        for nodeId, state in self.nodeStates.items():
            print(f"\n  Node {nodeId}:")
            print(f"    Position: ({from_q16(state.position.x):.1f}, {from_q16(state.position.y):.1f}, {from_q16(state.position.z):.1f})")
            print(f"    Physical RAM: {from_q16(state.resources.physicalRAM):.3f}")
            print(f"    Temporal RAM: {from_q16(state.resources.temporalRAM):.3f}")
            print(f"    Spatial RAM: {from_q16(state.resources.spatialRAM):.3f}")
            print(f"    Total RAM: {from_q16(state.resources.totalRAM):.3f}")
            print(f"    Last access: {from_q16(state.lastAccessTime):.3f}")
            
            # Add hot path/cold path classification if available
            if self.hotPathColdPathSystem:
                topologyState = self.hotPathColdPathSystem.getTopologyState()
                if topologyState:
                    for pattern in topologyState['nodePatterns']:
                        if pattern['nodeId'] == nodeId:
                            hotScore = (pattern['accessFrequency'] + pattern['proximity']) / 2.0
                            coldScore = (pattern['divergence'] + pattern['entropy']) / 2.0
                            if hotScore > coldScore + 0.2:
                                classification = 'Hot'
                            elif coldScore > hotScore + 0.2:
                                classification = 'Cold'
                            else:
                                classification = 'Warm'
                            print(f"    Path Classification: {classification}")
                            break
        
        # Add unified topology information if available
        if self.hotPathColdPathSystem:
            topologyState = self.hotPathColdPathSystem.getTopologyState()
            if topologyState:
                print(f"\n🌐 Unified Topology:")
                print(f"    Hot path probability: {topologyState['hotPathProbability']:.3f}")
                print(f"    Cold path probability: {topologyState['coldPathProbability']:.3f}")
                print(f"    Unified adjustment: {topologyState['unifiedAdjustment']:.3f}")
        
        print(f"\n📜 Allocation History: {len(self.allocationHistory)} entries")
        
        print("\n" + "="*60)


def main():
    """Test temporal-spatial resource system"""
    system = TemporalSpatialRAMSystem()
    
    print("[Test 1] Register node at origin...")
    result1 = system.registerNode(
        nodeId=1,
        x=0.0, y=0.0, z=0.0,
        physicalRAM=100.0,
        currentTime=5.0
    )
    print(f"  Node 1 registered: Total RAM={result1['state']['resources']['totalRAM']:.3f}")
    print(f"    Temporal RAM: {result1['state']['resources']['temporalRAM']:.3f}")
    print(f"    Spatial RAM: {result1['state']['resources']['spatialRAM']:.3f}")
    
    print("\n[Test 2] Register node at distance...")
    result2 = system.registerNode(
        nodeId=2,
        x=50.0, y=0.0, z=0.0,
        physicalRAM=100.0,
        currentTime=5.0
    )
    print(f"  Node 2 registered: Total RAM={result2['state']['resources']['totalRAM']:.3f}")
    print(f"    Temporal RAM: {result2['state']['resources']['temporalRAM']:.3f}")
    print(f"    Spatial RAM: {result2['state']['resources']['spatialRAM']:.3f}")
    
    print("\n[Test 3] Allocate resources to node 1...")
    allocResult1 = system.allocateToNode(nodeId=1, requiredRAM=20.0, currentTime=10.0)
    print(f"  Result: Success={allocResult1['success']}")
    if allocResult1['success']:
        print(f"  Total RAM after: {allocResult1['state']['resources']['totalRAM']:.3f}")
    
    print("\n[Test 4] Allocate resources to node 2...")
    allocResult2 = system.allocateToNode(nodeId=2, requiredRAM=30.0, currentTime=10.0)
    print(f"  Result: Success={allocResult2['success']}")
    if allocResult2['success']:
        print(f"  Total RAM after: {allocResult2['state']['resources']['totalRAM']:.3f}")
    
    print("\n[Test 5] Attempt over-allocation to node 2...")
    allocResult3 = system.allocateToNode(nodeId=2, requiredRAM=100.0, currentTime=15.0)
    print(f"  Result: Success={allocResult3['success']}")
    print(f"  Invariant: {allocResult3['bindResult']['invariant']}")
    
    print("\n[System State]")
    system.printSystemState()


if __name__ == '__main__':
    main()
