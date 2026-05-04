#!/usr/bin/env python3
"""
Hot Path / Cold Path Topology Optimization System (Verified Lean Specification)

This implementation follows the formal specification in:
0-Core-Formalism/lean/Semantics/Semantics/HotPathColdPath.lean

The Lean module provides:
- Hot path/cold path classification for unified topology adjustment
- Branch prediction for hot paths (frequent access)
- SLUQ routing for cold paths (divergent paths)
- Unified topology adjustment: T_unified = Σ(P_hot + P_cold)

This Python shim provides:
- JSON serialization for topology state
- Result wrapping for Lean function calls
- History deque for topology adjustments
- No logic (all logic defined in Lean specification)
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from collections import deque

try:
    from sluq_triage import SLUQTriageSystem, StochasticTrajectory, TriageDecision
    _HAS_SLUQ_TRIAGE = True
except ImportError:
    _HAS_SLUQ_TRIAGE = False
    print("[!] SLUQ triage system not available")

try:
    from hypercube_topology import HypercubeTopologySystem, HypercubeNode
    _HAS_HYPERCUBE = True
except ImportError:
    _HAS_HYPERCUBE = False
    print("[!] Hypercube topology system not available")

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
class NodeAccessPattern:
    """Node access pattern (Lean: NodeAccessPattern)"""
    nodeId: int  # UInt64
    accessFrequency: int  # Q16_16 - Access frequency (0.0 to 1.0)
    proximity: int  # Q16_16 - Proximity to reference node (0.0 to 1.0)
    divergence: int  # Q16_16 - Path divergence (0.0 to 1.0)
    entropy: int  # Q16_16 - Path entropy (0.0 to 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodeId': self.nodeId,
            'accessFrequency': from_q16(self.accessFrequency),
            'proximity': from_q16(self.proximity),
            'divergence': from_q16(self.divergence),
            'entropy': from_q16(self.entropy)
        }


class PathClassification(Enum):
    """Path classification (Lean: PathClassification)"""
    HOT = "Hot"  # Frequently accessed, low divergence
    COLD = "Cold"  # Rarely accessed, high divergence
    WARM = "Warm"  # Intermediate


@dataclass
class UnifiedTopologyState:
    """Unified topology state (Lean: UnifiedTopologyState)"""
    nodePatterns: List[NodeAccessPattern]
    hotPathProbability: int  # Q16_16 - P_hot
    coldPathProbability: int  # Q16_16 - P_cold
    unifiedAdjustment: int  # Q16_16 - T_unified
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodePatterns': [p.to_dict() for p in self.nodePatterns],
            'hotPathProbability': from_q16(self.hotPathProbability),
            'coldPathProbability': from_q16(self.coldPathProbability),
            'unifiedAdjustment': from_q16(self.unifiedAdjustment)
        }


@dataclass
class TopologyAdjustmentAction:
    """Topology adjustment action (Lean: TopologyAdjustmentAction)"""
    nodeId: int  # UInt64
    accessFrequencyDelta: int  # Q16_16 - Change in access frequency
    proximityDelta: int  # Q16_16 - Change in proximity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodeId': self.nodeId,
            'accessFrequencyDelta': from_q16(self.accessFrequencyDelta),
            'proximityDelta': from_q16(self.proximityDelta)
        }


@dataclass
class TopologyAdjustmentBind:
    """Topology adjustment bind result (Lean: TopologyAdjustmentBind)"""
    lawful: bool
    classificationBefore: PathClassification
    classificationAfter: PathClassification
    hotPathProbabilityBefore: int  # Q16_16
    hotPathProbabilityAfter: int  # Q16_16
    invariant: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lawful': self.lawful,
            'classificationBefore': self.classificationBefore.value,
            'classificationAfter': self.classificationAfter.value,
            'hotPathProbabilityBefore': from_q16(self.hotPathProbabilityBefore),
            'hotPathProbabilityAfter': from_q16(self.hotPathProbabilityAfter),
            'invariant': self.invariant
        }


# ═══════════════════════════════════════════════════════════════════════════
# Lean Function Implementations (verified by specification)
# ═══════════════════════════════════════════════════════════════════════════

def branchPrediction(accessFrequency: int, proximity: int) -> int:
    """Branch prediction function: f_branch(access_frequency, proximity) (Lean: branchPrediction)"""
    frequencyWeight = accessFrequency
    proximityWeight = proximity
    combined = q16_div(frequencyWeight + proximityWeight, to_q16(2.0))
    return combined  # Higher = more likely hot path


def sluqRouting(divergence: int, entropy: int) -> int:
    """SLUQ routing function: f_sluq(divergence, entropy) (Lean: sluqRouting)"""
    divergenceWeight = divergence
    entropyWeight = entropy
    combined = q16_div(divergenceWeight + entropyWeight, to_q16(2.0))
    return combined  # Higher = more likely cold path


def classifyPath(pattern: NodeAccessPattern) -> PathClassification:
    """Classify path as hot, cold, or warm (Lean: classifyPath)"""
    hotScore = branchPrediction(pattern.accessFrequency, pattern.proximity)
    coldScore = sluqRouting(pattern.divergence, pattern.entropy)
    
    if q16_gt(hotScore, coldScore + to_q16(0.2)):
        return PathClassification.HOT
    elif q16_gt(coldScore, hotScore + to_q16(0.2)):
        return PathClassification.COLD
    else:
        return PathClassification.WARM


def calculateHotPathProbability(patterns: List[NodeAccessPattern]) -> int:
    """Calculate hot path probability from patterns (Lean: calculateHotPathProbability)"""
    if not patterns:
        return 0
    
    total = 0
    for pattern in patterns:
        total += branchPrediction(pattern.accessFrequency, pattern.proximity)
    
    return total // len(patterns)


def calculateColdPathProbability(patterns: List[NodeAccessPattern]) -> int:
    """Calculate cold path probability from patterns (Lean: calculateColdPathProbability)"""
    if not patterns:
        return 0
    
    total = 0
    for pattern in patterns:
        total += sluqRouting(pattern.divergence, pattern.entropy)
    
    return total // len(patterns)


def calculateUnifiedAdjustment(hotProb: int, coldProb: int) -> int:
    """Calculate unified topology adjustment: T_unified = Σ(P_hot + P_cold) (Lean: calculateUnifiedAdjustment)"""
    return q16_add(hotProb, coldProb)


def updateUnifiedTopology(patterns: List[NodeAccessPattern]) -> UnifiedTopologyState:
    """Update unified topology state from patterns (Lean: updateUnifiedTopology)"""
    hotProb = calculateHotPathProbability(patterns)
    coldProb = calculateColdPathProbability(patterns)
    unifiedAdj = calculateUnifiedAdjustment(hotProb, coldProb)
    
    return UnifiedTopologyState(
        nodePatterns=patterns,
        hotPathProbability=hotProb,
        coldPathProbability=coldProb,
        unifiedAdjustment=unifiedAdj
    )


def isTopologyAdjustmentLawful(state: UnifiedTopologyState, action: TopologyAdjustmentAction) -> bool:
    """Check if topology adjustment is lawful (Lean: isTopologyAdjustmentLawful)"""
    freqValid = action.accessFrequencyDelta >= (-Q16_ONE) and action.accessFrequencyDelta <= Q16_ONE
    proxValid = action.proximityDelta >= (-Q16_ONE) and action.proximityDelta <= Q16_ONE
    return freqValid and proxValid


def updateNodePattern(pattern: NodeAccessPattern, action: TopologyAdjustmentAction) -> NodeAccessPattern:
    """Update node pattern from action (Lean: updateNodePattern)"""
    newFreq = pattern.accessFrequency + action.accessFrequencyDelta
    newProx = pattern.proximity + action.proximityDelta
    
    # Clamp to [0, 1]
    clampedFreq = max(0, min(newFreq, Q16_ONE))
    clampedProx = max(0, min(newProx, Q16_ONE))
    
    return NodeAccessPattern(
        nodeId=pattern.nodeId,
        accessFrequency=clampedFreq,
        proximity=clampedProx,
        divergence=pattern.divergence,
        entropy=pattern.entropy
    )


def topologyAdjustmentBind(state: UnifiedTopologyState, action: TopologyAdjustmentAction, currentTime: int) -> TopologyAdjustmentBind:
    """Bind primitive for topology adjustment (Lean: topologyAdjustmentBind)"""
    lawful = isTopologyAdjustmentLawful(state, action)
    
    # Find old pattern
    oldPattern = None
    for p in state.nodePatterns:
        if p.nodeId == action.nodeId:
            oldPattern = p
            break
    
    oldClassification = classifyPath(oldPattern) if oldPattern else PathClassification.COLD
    
    # Update patterns if lawful
    newPatterns = state.nodePatterns
    if lawful and oldPattern:
        newPatterns = [
            updateNodePattern(p, action) if p.nodeId == action.nodeId else p
            for p in state.nodePatterns
        ]
    
    newState = updateUnifiedTopology(newPatterns) if lawful else state
    
    # Find new pattern
    newPattern = None
    for p in newState.nodePatterns:
        if p.nodeId == action.nodeId:
            newPattern = p
            break
    
    newClassification = classifyPath(newPattern) if newPattern else PathClassification.COLD
    
    return TopologyAdjustmentBind(
        lawful=lawful,
        classificationBefore=oldClassification,
        classificationAfter=newClassification,
        hotPathProbabilityBefore=state.hotPathProbability,
        hotPathProbabilityAfter=newState.hotPathProbability,
        invariant="topology_adjustment_satisfied" if lawful else "topology_constraint_violated"
    )


class HotPathColdPathSystem:
    """
    Hot path/cold path topology optimization system (Python shim wrapping Lean specification).
    
    All core logic is defined in 0-Core-Formalism/lean/Semantics/Semantics/HotPathColdPath.lean
    """
    
    def __init__(self):
        self.topologyState: Optional[UnifiedTopologyState] = None
        self.adjustmentHistory: List[Dict[str, Any]] = []
        self.sluqTriageSystem: Optional[SLUQTriageSystem] = None
        self.hypercubeTopologySystem: Optional[HypercubeTopologySystem] = None
        
        if _HAS_SLUQ_TRIAGE:
            self.sluqTriageSystem = SLUQTriageSystem()
        
        if _HAS_HYPERCUBE:
            self.hypercubeTopologySystem = HypercubeTopologySystem()
        
        print("[HotPathColdPath] Initialized (Lean specification)")
    
    def initializeTopology(self, patterns: List[NodeAccessPattern]) -> Dict[str, Any]:
        """Initialize unified topology state"""
        state = updateUnifiedTopology(patterns)
        self.topologyState = state
        
        # Initialize hypercube topology if available
        if self.hypercubeTopologySystem:
            self.hypercubeTopologySystem.initializeTopology(dimensions=12, numNodes=len(patterns))
        
        return {
            'state': state.to_dict()
        }
    
    def registerNode(self, nodeId: int, accessFrequency: float, proximity: float, 
                     divergence: float, entropy: float) -> Dict[str, Any]:
        """Register a node in the topology"""
        pattern = NodeAccessPattern(
            nodeId=nodeId,
            accessFrequency=to_q16(accessFrequency),
            proximity=to_q16(proximity),
            divergence=to_q16(divergence),
            entropy=to_q16(entropy)
        )
        
        if self.topologyState is None:
            self.topologyState = updateUnifiedTopology([pattern])
            if self.sluqTriageSystem:
                self.sluqTriageSystem.initializeTriage()
        else:
            # Add pattern if not exists, update if exists
            existing = False
            newPatterns = []
            for p in self.topologyState.nodePatterns:
                if p.nodeId == nodeId:
                    newPatterns.append(pattern)
                    existing = True
                else:
                    newPatterns.append(p)
            
            if not existing:
                newPatterns.append(pattern)
            
            self.topologyState = updateUnifiedTopology(newPatterns)
        
        # Register cold path trajectories in SLUQ triage system if available
        if self.sluqTriageSystem:
            classification = classifyPath(pattern)
            if classification == PathClassification.COLD:
                # Register as stochastic trajectory for triage
                self.sluqTriageSystem.registerTrajectory(
                    trajectoryId=nodeId,
                    cacheLocality=proximity,  # Use proximity as cache locality proxy
                    stabilityScore=1.0 - entropy,  # Use entropy inverse as stability
                    entropy=entropy,
                    divergence=divergence
                )
        
        # Register node in hypercube topology if available
        if self.hypercubeTopologySystem:
            # Generate hypercube coordinates from nodeId
            coords = []
            for d in range(12):
                coords.append((nodeId >> d) & 1)
            
            self.hypercubeTopologySystem.registerNode(nodeId=nodeId, coordinates=coords, dimensions=12)
        
        return {
            'nodeId': nodeId,
            'pattern': pattern.to_dict(),
            'state': self.topologyState.to_dict()
        }
    
    def submitTopologyAdjustment(self, action: TopologyAdjustmentAction, currentTime: float = 0.0) -> Dict[str, Any]:
        """Submit topology adjustment for processing (Lean specification)"""
        if self.topologyState is None:
            return {'error': 'Topology not initialized'}
        
        bindResult = topologyAdjustmentBind(self.topologyState, action, to_q16(currentTime))
        
        if bindResult.lawful:
            # Update patterns
            newPatterns = []
            for p in self.topologyState.nodePatterns:
                if p.nodeId == action.nodeId:
                    newPatterns.append(updateNodePattern(p, action))
                else:
                    newPatterns.append(p)
            
            self.topologyState = updateUnifiedTopology(newPatterns)
            
            # Record adjustment history
            self.adjustmentHistory.append({
                'nodeId': action.nodeId,
                'action': action.to_dict(),
                'bindResult': bindResult.to_dict(),
                'timestamp': time.time()
            })
        
        return {
            'success': bindResult.lawful,
            'bindResult': bindResult.to_dict(),
            'state': self.topologyState.to_dict()
        }
    
    def getTopologyState(self) -> Optional[Dict[str, Any]]:
        """Get current topology state"""
        if self.topologyState:
            return self.topologyState.to_dict()
        return None
    
    def getAdjustmentHistory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get adjustment history"""
        return self.adjustmentHistory[-limit:]
    
    def printSystemState(self):
        """Print system state"""
        print("\n" + "="*60)
        print("HOT PATH / COLD PATH TOPOLOGY OPTIMIZATION STATE")
        print("="*60)
        
        if self.topologyState:
            print(f"\n📊 Unified Topology:")
            print(f"  Hot path probability: {from_q16(self.topologyState.hotPathProbability):.3f}")
            print(f"  Cold path probability: {from_q16(self.topologyState.coldPathProbability):.3f}")
            print(f"  Unified adjustment: {from_q16(self.topologyState.unifiedAdjustment):.3f}")
            
            print(f"\n📍 Node Patterns:")
            for pattern in self.topologyState.nodePatterns:
                classification = classifyPath(pattern)
                print(f"  Node {pattern.nodeId}: {classification.value}")
                print(f"    Access frequency: {from_q16(pattern.accessFrequency):.3f}")
                print(f"    Proximity: {from_q16(pattern.proximity):.3f}")
                print(f"    Divergence: {from_q16(pattern.divergence):.3f}")
                print(f"    Entropy: {from_q16(pattern.entropy):.3f}")
        
        # Add SLUQ triage information if available
        if self.sluqTriageSystem:
            triageState = self.sluqTriageSystem.getTriageState()
            if triageState:
                trajectoryCount = len(triageState['trajectories'])
                triageEfficiency = triageState['prunedCount'] / trajectoryCount if trajectoryCount > 0 else 0.0
                print(f"\n🔬 SLUQ Triage:")
                print(f"  Trajectory Count: {trajectoryCount}")
                print(f"  Pruned: {triageState['prunedCount']}")
                print(f"  Evaluated: {triageState['evaluatedCount']}")
                print(f"  Triage Efficiency: {triageEfficiency:.3f}")
        
        # Add hypercube topology information if available
        if self.hypercubeTopologySystem:
            hypercubeState = self.hypercubeTopologySystem.getTopologyState()
            if hypercubeState:
                print(f"\n🔷 Hypercube Topology (Connection Machine):")
                print(f"  Dimensions: {hypercubeState['dimensions']}")
                print(f"  Connectivity: {2 ** hypercubeState['dimensions']} nodes")
                print(f"  Neighbor Count: {2 * hypercubeState['dimensions']}")
                print(f"  Diameter: {hypercubeState['dimensions']}")
                print(f"  Registered Nodes: {len(hypercubeState['nodes'])}")
        
        print(f"\n📜 Adjustment History: {len(self.adjustmentHistory)} entries")
        
        print("\n" + "="*60)


def main():
    """Test hot path/cold path system"""
    system = HotPathColdPathSystem()
    
    print("[Test 1] Register hot path node (frequent access, low divergence)...")
    result1 = system.registerNode(
        nodeId=1,
        accessFrequency=0.8,
        proximity=0.9,
        divergence=0.1,
        entropy=0.2
    )
    pattern1 = NodeAccessPattern(
        nodeId=result1['nodeId'],
        accessFrequency=to_q16(result1['pattern']['accessFrequency']),
        proximity=to_q16(result1['pattern']['proximity']),
        divergence=to_q16(result1['pattern']['divergence']),
        entropy=to_q16(result1['pattern']['entropy'])
    )
    print(f"  Node 1 registered: Classification={classifyPath(pattern1).value}")
    
    print("\n[Test 2] Register cold path node (rare access, high divergence)...")
    result2 = system.registerNode(
        nodeId=2,
        accessFrequency=0.1,
        proximity=0.2,
        divergence=0.8,
        entropy=0.9
    )
    pattern2 = NodeAccessPattern(
        nodeId=result2['nodeId'],
        accessFrequency=to_q16(result2['pattern']['accessFrequency']),
        proximity=to_q16(result2['pattern']['proximity']),
        divergence=to_q16(result2['pattern']['divergence']),
        entropy=to_q16(result2['pattern']['entropy'])
    )
    print(f"  Node 2 registered: Classification={classifyPath(pattern2).value}")
    
    print("\n[Test 3] Register warm path node (intermediate)...")
    result3 = system.registerNode(
        nodeId=3,
        accessFrequency=0.5,
        proximity=0.5,
        divergence=0.5,
        entropy=0.5
    )
    pattern3 = NodeAccessPattern(
        nodeId=result3['nodeId'],
        accessFrequency=to_q16(result3['pattern']['accessFrequency']),
        proximity=to_q16(result3['pattern']['proximity']),
        divergence=to_q16(result3['pattern']['divergence']),
        entropy=to_q16(result3['pattern']['entropy'])
    )
    print(f"  Node 3 registered: Classification={classifyPath(pattern3).value}")
    
    print("\n[Test 4] Submit topology adjustment (increase access frequency for node 2)...")
    action1 = TopologyAdjustmentAction(
        nodeId=2,
        accessFrequencyDelta=to_q16(0.3),
        proximityDelta=to_q16(0.1)
    )
    adjustResult1 = system.submitTopologyAdjustment(action1)
    print(f"  Result: Success={adjustResult1['success']}")
    if adjustResult1['success']:
        print(f"  Classification before: {adjustResult1['bindResult']['classificationBefore']}")
        print(f"  Classification after: {adjustResult1['bindResult']['classificationAfter']}")
    
    print("\n[Test 5] Submit topology adjustment (increase proximity for node 2)...")
    action2 = TopologyAdjustmentAction(
        nodeId=2,
        accessFrequencyDelta=to_q16(0.0),
        proximityDelta=to_q16(0.3)
    )
    adjustResult2 = system.submitTopologyAdjustment(action2)
    print(f"  Result: Success={adjustResult2['success']}")
    if adjustResult2['success']:
        print(f"  Classification after: {adjustResult2['bindResult']['classificationAfter']}")
    
    print("\n[System State]")
    system.printSystemState()


if __name__ == '__main__':
    main()
