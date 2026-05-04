#!/usr/bin/env python3
"""
Topological State Machines (TSM) Total Resource Report

This script calculates and reports the total resources used by the
topological state machines implemented in this session:
- Temporal-Spatial RAM system
- Hot Path / Cold Path topology optimization
- Q-Factor energy balance
- Joule energy tracking
"""

import sys
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from temporal_spatial_ram import TemporalSpatialRAMSystem
from hot_path_cold_path import HotPathColdPathSystem
from q_factor import QFactorSystem
from joule_energy import JouleEnergySystem

def calculate_tsm_resources():
    """Calculate total TSM resources from all implemented systems"""
    print("="*70)
    print("TOPOLOGICAL STATE MACHINES (TSM) TOTAL RESOURCE REPORT")
    print("="*70)
    
    # Initialize all systems
    print("\n[1/4] Initializing Temporal-Spatial RAM system...")
    tsram_system = TemporalSpatialRAMSystem()
    
    print("\n[2/4] Initializing Hot Path / Cold Path system...")
    hpcp_system = HotPathColdPathSystem()
    
    print("\n[3/4] Initializing Q-Factor system...")
    qfactor_system = QFactorSystem()
    
    print("\n[4/4] Initializing Joule Energy system...")
    joule_system = JouleEnergySystem()
    
    # Register sample nodes for resource calculation
    print("\n" + "="*70)
    print("REGISTERING SAMPLE TOPOLOGY")
    print("="*70)
    
    # Node 1: Hot path (frequent access, high proximity)
    tsram_system.registerNode(nodeId=1, x=0.0, y=0.0, z=0.0, physicalRAM=100.0, currentTime=5.0)
    hpcp_system.registerNode(nodeId=1, accessFrequency=0.9, proximity=0.95, divergence=0.1, entropy=0.2)
    qfactor_system.initializeAgent(agentId=1, flashEnergy=100.0, enthalpy=50.0, workEnergy=80.0, energyLoss=10.0)
    joule_system.initializeAgent(agentId=1, initialCharge=10.0, initialVoltage=5.0)
    
    # Node 2: Cold path (rare access, high divergence)
    tsram_system.registerNode(nodeId=2, x=50.0, y=0.0, z=0.0, physicalRAM=100.0, currentTime=5.0)
    hpcp_system.registerNode(nodeId=2, accessFrequency=0.1, proximity=0.2, divergence=0.8, entropy=0.9)
    qfactor_system.initializeAgent(agentId=2, flashEnergy=50.0, enthalpy=30.0, workEnergy=60.0, energyLoss=20.0)
    joule_system.initializeAgent(agentId=2, initialCharge=5.0, initialVoltage=3.0)
    
    # Node 3: Warm path (intermediate)
    tsram_system.registerNode(nodeId=3, x=25.0, y=0.0, z=0.0, physicalRAM=100.0, currentTime=5.0)
    hpcp_system.registerNode(nodeId=3, accessFrequency=0.5, proximity=0.5, divergence=0.5, entropy=0.5)
    qfactor_system.initializeAgent(agentId=3, flashEnergy=75.0, enthalpy=40.0, workEnergy=70.0, energyLoss=15.0)
    joule_system.initializeAgent(agentId=3, initialCharge=7.5, initialVoltage=4.0)
    
    # Calculate total resources
    print("\n" + "="*70)
    print("RESOURCE CALCULATION")
    print("="*70)
    
    # Temporal-Spatial RAM Resources
    print("\n[1] Temporal-Spatial RAM Resources:")
    tsram_total_physical = 0.0
    tsram_total_temporal = 0.0
    tsram_total_spatial = 0.0
    tsram_total = 0.0
    
    for nodeId in [1, 2, 3]:
        state = tsram_system.getNodeResources(nodeId)
        if state:
            tsram_total_physical += state['resources']['physicalRAM']
            tsram_total_temporal += state['resources']['temporalRAM']
            tsram_total_spatial += state['resources']['spatialRAM']
            tsram_total += state['resources']['totalRAM']
    
    print(f"  Total Physical RAM: {tsram_total_physical:.3f} MB")
    print(f"  Total Temporal RAM: {tsram_total_temporal:.3f} MB")
    print(f"  Total Spatial RAM: {tsram_total_spatial:.3f} MB")
    print(f"  Total TS-RAM: {tsram_total:.3f} MB")
    
    # Hot Path / Cold Path Resources
    print("\n[2] Hot Path / Cold Path Topology Resources:")
    topology_state = hpcp_system.getTopologyState()
    if topology_state:
        hot_prob = topology_state['hotPathProbability']
        cold_prob = topology_state['coldPathProbability']
        unified_adj = topology_state['unifiedAdjustment']
        
        print(f"  Hot Path Probability: {hot_prob:.3f}")
        print(f"  Cold Path Probability: {cold_prob:.3f}")
        print(f"  Unified Adjustment: {unified_adj:.3f}")
        print(f"  Topology Efficiency: {hot_prob / (hot_prob + cold_prob) if (hot_prob + cold_prob) > 0 else 0:.3f}")
    
    # Q-Factor Resources
    print("\n[3] Q-Factor Energy Balance Resources:")
    qfactor_total_flash = 0.0
    qfactor_total_enthalpy = 0.0
    qfactor_total_recovered = 0.0
    qfactor_total_work = 0.0
    qfactor_total_loss = 0.0
    
    for agentId in [1, 2, 3]:
        state = qfactor_system.getAgentState(agentId)
        if state:
            balance = state['balance']
            qfactor_total_flash += balance['flashEnergy']
            qfactor_total_enthalpy += balance['enthalpy']
            qfactor_total_recovered += balance['recoveredEnergy']
            qfactor_total_work += balance['workEnergy']
            qfactor_total_loss += balance['energyLoss']
    
    print(f"  Total Flash Energy: {qfactor_total_flash:.3f} J")
    print(f"  Total Enthalpy: {qfactor_total_enthalpy:.3f} J")
    print(f"  Total Recovered Energy: {qfactor_total_recovered:.3f} J")
    print(f"  Total Work Energy: {qfactor_total_work:.3f} J")
    print(f"  Total Energy Loss: {qfactor_total_loss:.3f} J")
    
    # Calculate overall Q-Factor
    numerator = qfactor_total_flash + qfactor_total_enthalpy + qfactor_total_recovered - 20.0  # W_demon
    denominator = qfactor_total_work + qfactor_total_loss
    overall_q = numerator / denominator if denominator > 0 else 0
    print(f"  Overall Q-Factor: {overall_q:.3f} (dimensionless ratio)")
    
    # Joule Energy Resources
    print("\n[4] Joule Energy Resources:")
    joule_total_charge = 0.0
    joule_total_voltage = 0.0
    joule_total_power = 0.0
    joule_total_energy = 0.0
    
    for agentId in [1, 2, 3]:
        state = joule_system.getAgentState(agentId)
        if state:
            joule_total_charge += state['charge']
            joule_total_voltage += state['voltage']
            joule_total_power += state['power']
            joule_total_energy += state['energy']
    
    print(f"  Total Charge (Q): {joule_total_charge:.3f} units")
    print(f"  Total Voltage (V): {joule_total_voltage:.3f} V")
    print(f"  Total Power (P): {joule_total_power:.3f} W")
    print(f"  Total Energy (E): {joule_total_energy:.3f} J")
    
    # Total TSM Resources Summary
    print("\n" + "="*70)
    print("TOTAL TSM RESOURCES SUMMARY")
    print("="*70)
    
    total_tsm_resources = {
        'TS-RAM (Total)': f"{tsram_total:.3f} MB",
        'TS-RAM (Physical)': f"{tsram_total_physical:.3f} MB",
        'TS-RAM (Temporal)': f"{tsram_total_temporal:.3f} MB",
        'TS-RAM (Spatial)': f"{tsram_total_spatial:.3f} MB",
        'Topology Adjustment': f"{unified_adj if topology_state else 0:.3f} (ratio)",
        'Q-Factor Energy': f"{numerator if denominator > 0 else 0:.3f} J",
        'Joule Energy': f"{joule_total_energy:.3f} J",
        'Total Active Nodes': "3 nodes"
    }
    
    print(f"\n📊 Total TSM Resources:")
    for resource, value in total_tsm_resources.items():
        print(f"  {resource}: {value}")
    
    # Resource Efficiency Metrics
    print(f"\n📈 Resource Efficiency Metrics:")
    tsram_efficiency = tsram_total / tsram_total_physical if tsram_total_physical > 0 else 0
    print(f"  TS-RAM Efficiency (Total/Physical): {tsram_efficiency:.3f} (ratio)")
    print(f"  Topology Hot Path Ratio: {hot_prob / (hot_prob + cold_prob) if (hot_prob + cold_prob) > 0 else 0:.3f} (ratio)")
    print(f"  Q-Factor Gain: {overall_q:.3f} (dimensionless)")
    joule_per_task = joule_total_energy / joule_total_charge if joule_total_charge > 0 else 0
    print(f"  Joule Energy per Task: {joule_per_task:.3f} J/unit")
    
    # Overall TSM Resource Score
    print(f"\n🎯 Overall TSM Resource Score:")
    tsm_score = (
        (tsram_efficiency * 0.3) +
        (hot_prob / (hot_prob + cold_prob) if (hot_prob + cold_prob) > 0 else 0) * 0.2 +
        (min(overall_q, 2.0) / 2.0) * 0.3 +
        (1.0 - min(joule_per_task / 20.0, 1.0)) * 0.2
    )
    print(f"  TSM Score: {tsm_score:.3f} (0-1 scale)")
    
    print("\n" + "="*70)
    print("TSM RESOURCE REPORT COMPLETE")
    print("="*70)
    
    return total_tsm_resources, tsm_score

if __name__ == '__main__':
    calculate_tsm_resources()
