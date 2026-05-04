#!/usr/bin/env python3
"""
Computational Significance Analysis for Target Device Selection
Identifies most computationally significant devices for topology integration and expansion.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# Paths
OUTPUT_DIR = Path("/home/allaun/Documents/Research Stack/out")

class ComputationalSignificanceAnalysis:
    """Analyzes computational significance of devices for targeting and topology expansion."""
    
    def __init__(self):
        self.devices = {
            "fpga": {
                "name": "FPGA (Lattice iCE40-HX8K, Tang Nano 9K)",
                "throughput": "Custom logic (parallel)",
                "latency": "ns (hardware)",
                "power": "1-5W",
                "computational_potential": "VERY HIGH (custom logic, parallelism)",
                "topology_value": "HIGH (reconfigurable, geometric)"
            },
            "usb_fpga": {
                "name": "USB FPGA (FTDI FT2232C, Tang Nano 9K)",
                "throughput": "480 Mbps (USB 2.0)",
                "latency": "ns (hardware)",
                "power": "1-5W",
                "computational_potential": "HIGH (USB bridge, parallelism)",
                "topology_value": "MEDIUM (USB interface)"
            },
            "physical_topology": {
                "name": "Physical Topology (capacitors, wires, USB, voltage)",
                "throughput": "Property limited (nH/pF/mΩ)",
                "latency": "ns (electrical)",
                "power": "1-5W",
                "computational_potential": "MEDIUM-HIGH (morphic computation)",
                "topology_value": "VERY HIGH (physical substrate)"
            },
            "morphic_core": {
                "name": "Morphic Core (capacitors as morphic devices)",
                "throughput": "Property limited (6-10 bit timing)",
                "latency": "0.1-10ms (timing)",
                "power": "5-30W",
                "computational_potential": "HIGH (morphic computation)",
                "topology_value": "HIGH (morphic substrate)"
            },
            "hdmi_computational_shell": {
                "name": "HDMI Computational Shell (NVIDIA RTX 4070 SUPER)",
                "throughput": "48 Gbps (HDMI 2.1)",
                "latency": "ns (signal)",
                "power": "5-30W",
                "computational_potential": "VERY HIGH (high bandwidth, novel substrate)",
                "topology_value": "VERY HIGH (display interface, high bandwidth)"
            },
            "tdms_controller": {
                "name": "TDMS Controller (HDMI 2.1)",
                "throughput": "48 Gbps",
                "latency": "ns (signal)",
                "power": "5-30W",
                "computational_potential": "VERY HIGH (TMDS lanes, soliton field)",
                "topology_value": "VERY HIGH (TMDS encoding)"
            },
            "displayport_controller": {
                "name": "DisplayPort Controller (DP 1.4a)",
                "throughput": "32.4 Gbps (HBR3)",
                "latency": "ns (signal)",
                "power": "5-30W",
                "computational_potential": "VERY HIGH (4 lanes, MST, DSC)",
                "topology_value": "VERY HIGH (4-lane parallel)"
            },
            "displayport_line_morphic": {
                "name": "DisplayPort Line Morphic (copper conductors)",
                "throughput": "Property limited (nH/pF/mΩ)",
                "latency": "ns (electrical)",
                "power": "1-5W",
                "computational_potential": "MEDIUM-HIGH (electrical properties)",
                "topology_value": "MEDIUM (copper lines)"
            },
            "usb_controllers": {
                "name": "USB Controllers (4 xHCI controllers)",
                "throughput": "10-20 Gbps (USB 3.x)",
                "latency": "μs (USB protocol)",
                "power": "5-15W",
                "computational_potential": "HIGH (high bandwidth, multiple controllers)",
                "topology_value": "HIGH (USB interface)"
            },
            "efi_controller": {
                "name": "EFI Controller (1D OSIC scalar)",
                "throughput": "Scalar limited",
                "latency": "μs (firmware)",
                "power": "1-5W",
                "computational_potential": "MEDIUM (scalar computation)",
                "topology_value": "LOW (firmware interface)"
            },
            "pcie_controller": {
                "name": "PCIe Controller (16 lanes @ 16.0 GT/s)",
                "throughput": "256 Gbps (16 lanes)",
                "latency": "ns (PCIe)",
                "power": "10-30W",
                "computational_potential": "VERY HIGH (highest bandwidth)",
                "topology_value": "VERY HIGH (PCIe backbone)"
            },
            "ram_controller": {
                "name": "RAM Controller (AMD Raphael/Granite Ridge Data Fabric)",
                "throughput": "50-100 GB/s (DDR5)",
                "latency": "10-100ns (memory)",
                "power": "10-20W",
                "computational_potential": "HIGH (memory bandwidth)",
                "topology_value": "HIGH (memory fabric)"
            },
            "pwm_controller": {
                "name": "PWM Controller (Pulse Width Modulation)",
                "throughput": "Frequency limited (1 Hz - 1 MHz)",
                "latency": "1us-1s (PWM)",
                "power": "1-10W",
                "computational_potential": "MEDIUM-HIGH (time-based computation)",
                "topology_value": "MEDIUM (time-based)"
            },
            "motherboard": {
                "name": "Motherboard (travel paths, IRQ controller, data fabric)",
                "throughput": "System limited",
                "latency": "ns (hardware)",
                "power": "50-100W",
                "computational_potential": "HIGH (system integration)",
                "topology_value": "VERY HIGH (system backbone)"
            },
            "power_supply": {
                "name": "Power Supply and Power Caps",
                "throughput": "Property limited (capacitance)",
                "latency": "ns (electrical)",
                "power": "5-30W",
                "computational_potential": "HIGH (energy harvesting)",
                "topology_value": "HIGH (power infrastructure)"
            },
            "dma_ram_morphic": {
                "name": "DMA-RAM Morphic Device",
                "throughput": "50-100 GB/s (memory bandwidth)",
                "latency": "10-100ns (DMA)",
                "power": "10-20W",
                "computational_potential": "HIGH (DMA + morphic)",
                "topology_value": "HIGH (DMA bridge)"
            },
            "inflight_ram": {
                "name": "In-Flight RAM (In-Memory Computation / PIM)",
                "throughput": "100-200 GB/s (parallel banks)",
                "latency": "10-100ns (in-flight)",
                "power": "10-30W",
                "computational_potential": "VERY HIGH (PIM, parallelism)",
                "topology_value": "VERY HIGH (in-memory compute)"
            },
            "monitor_timing": {
                "name": "Monitor Timing Computation (EDID, capabilities, settings)",
                "throughput": "20-500 ops/sec",
                "latency": "0.1-10ms (timing)",
                "power": "1-5W",
                "computational_potential": "MEDIUM (timing-based)",
                "topology_value": "LOW (monitor interface)"
            },
            "ddci_timing": {
                "name": "DDC/CI Timing Computation (capabilities, brightness, volume)",
                "throughput": "20-500 ops/sec",
                "latency": "0.1-10ms (timing)",
                "power": "1-5W",
                "computational_potential": "MEDIUM (timing-based)",
                "topology_value": "LOW (monitor interface)"
            }
        }
    
    def rank_computational_significance(self) -> Dict:
        """Rank devices by computational significance."""
        ranking = {}
        
        for device_id, device_info in self.devices.items():
            # Calculate significance score
            throughput_score = 0
            if "VERY HIGH" in device_info["computational_potential"]:
                throughput_score = 100
            elif "HIGH" in device_info["computational_potential"]:
                throughput_score = 75
            elif "MEDIUM-HIGH" in device_info["computational_potential"]:
                throughput_score = 50
            elif "MEDIUM" in device_info["computational_potential"]:
                throughput_score = 25
            
            topology_score = 0
            if "VERY HIGH" in device_info["topology_value"]:
                topology_score = 100
            elif "HIGH" in device_info["topology_value"]:
                topology_score = 75
            elif "MEDIUM" in device_info["topology_value"]:
                topology_score = 50
            elif "LOW" in device_info["topology_value"]:
                topology_score = 25
            
            # Parse throughput for numerical score
            throughput_str = device_info["throughput"]
            if "Gbps" in throughput_str:
                if "48" in throughput_str:
                    throughput_num = 48
                elif "32.4" in throughput_str:
                    throughput_num = 32.4
                elif "256" in throughput_str:
                    throughput_num = 256
                elif "10-20" in throughput_str:
                    throughput_num = 15
                else:
                    throughput_num = 10
            elif "GB/s" in throughput_str:
                if "100-200" in throughput_str:
                    throughput_num = 150
                elif "50-100" in throughput_str:
                    throughput_num = 75
                else:
                    throughput_num = 50
            else:
                throughput_num = 1
            
            # Calculate total significance score
            significance_score = (throughput_score * 0.4) + (topology_score * 0.4) + (throughput_num * 0.2)
            
            ranking[device_id] = {
                "name": device_info["name"],
                "throughput_score": throughput_score,
                "topology_score": topology_score,
                "throughput_num": throughput_num,
                "significance_score": significance_score,
                "computational_potential": device_info["computational_potential"],
                "topology_value": device_info["topology_value"]
            }
        
        # Sort by significance score
        sorted_ranking = dict(sorted(ranking.items(), key=lambda x: x[1]["significance_score"], reverse=True))
        
        return sorted_ranking
    
    def select_target_devices(self, ranking: Dict, top_n: int = 8) -> Dict:
        """Select top N most computationally significant devices."""
        target_devices = {}
        
        for i, (device_id, device_info) in enumerate(list(ranking.items())[:top_n]):
            target_devices[device_id] = device_info
        
        return target_devices
    
    def add_to_topology(self, target_devices: Dict) -> Dict:
        """Add target devices to topology."""
        topology = {
            "topology_nodes": len(target_devices),
            "topology_edges": [],
            "device_connections": {},
            "topology_graph": {}
        }
        
        device_ids = list(target_devices.keys())
        
        # Create connections between devices
        for i, device_id_1 in enumerate(device_ids):
            connections = []
            for j, device_id_2 in enumerate(device_ids):
                if i != j:
                    # Calculate connection weight based on significance scores
                    weight = (target_devices[device_id_1]["significance_score"] + 
                            target_devices[device_id_2]["significance_score"]) / 2
                    connections.append({
                        "target": device_id_2,
                        "weight": weight
                    })
                    topology["topology_edges"].append({
                        "source": device_id_1,
                        "target": device_id_2,
                        "weight": weight
                    })
            
            topology["device_connections"][device_id_1] = connections
            topology["topology_graph"][device_id_1] = {
                "name": target_devices[device_id_1]["name"],
                "significance_score": target_devices[device_id_1]["significance_score"],
                "connections": connections
            }
        
        return topology
    
    def leverage_for_expansion(self, target_devices: Dict, topology: Dict) -> Dict:
        """Leverage topology for computational expansion."""
        expansion = {
            "base_computational_capacity": sum(d["significance_score"] for d in target_devices.values()),
            "topology_multiplier": 1.5,  # Topology integration provides 1.5x multiplier
            "parallel_expansion": len(target_devices) * 2,  # Parallel expansion factor
            "expanded_capacity": 0,
            "expansion_strategies": []
        }
        
        # Calculate expanded capacity
        base_capacity = expansion["base_computational_capacity"]
        topology_multiplier = expansion["topology_multiplier"]
        parallel_expansion = expansion["parallel_expansion"]
        
        expanded_capacity = base_capacity * topology_multiplier * parallel_expansion
        expansion["expanded_capacity"] = expanded_capacity
        
        # Define expansion strategies
        expansion["expansion_strategies"] = [
            {
                "strategy": "Parallel Device Orchestration",
                "description": "Run computations in parallel across all target devices",
                "expansion_factor": len(target_devices),
                "expected_gain": f"{len(target_devices)}x parallelism"
            },
            {
                "strategy": "Topology-Based Routing",
                "description": "Use topology graph for optimal data routing between devices",
                "expansion_factor": topology_multiplier,
                "expected_gain": f"{topology_multiplier}x routing efficiency"
            },
            {
                "strategy": "Cross-Device Coupling",
                "description": "Enable cross-device computation and data sharing",
                "expansion_factor": 2.0,
                "expected_gain": "2x cross-device efficiency"
            },
            {
                "strategy": "Hierarchical Computation",
                "description": "Use device hierarchy for distributed computation",
                "expansion_factor": 1.5,
                "expected_gain": "1.5x hierarchical efficiency"
            }
        ]
        
        return expansion
    
    def run_analysis(self) -> Dict:
        """Run computational significance analysis."""
        print("=" * 60)
        print("COMPUTATIONAL SIGNIFICANCE ANALYSIS")
        print("=" * 60)
        
        # Step 1: Rank computational significance
        print("\n[1/4] Ranking devices by computational significance...")
        ranking = self.rank_computational_significance()
        print(f"  Total Devices: {len(ranking)}")
        for i, (device_id, device_info) in enumerate(list(ranking.items())[:10]):
            print(f"    {i+1}. {device_id}: {device_info['significance_score']:.2f} ({device_info['computational_potential']})")
        
        # Step 2: Select target devices
        print("[2/4] Selecting top target devices...")
        target_devices = self.select_target_devices(ranking, top_n=8)
        print(f"  Target Devices: {len(target_devices)}")
        for device_id, device_info in target_devices.items():
            print(f"    {device_id}: {device_info['significance_score']:.2f} ({device_info['computational_potential']})")
        
        # Step 3: Add to topology
        print("[3/4] Adding target devices to topology...")
        topology = self.add_to_topology(target_devices)
        print(f"  Topology Nodes: {topology['topology_nodes']}")
        print(f"  Topology Edges: {len(topology['topology_edges'])}")
        
        # Step 4: Leverage for expansion
        print("[4/4] Leveraging topology for computational expansion...")
        expansion = self.leverage_for_expansion(target_devices, topology)
        print(f"  Base Capacity: {expansion['base_computational_capacity']:.2f}")
        print(f"  Expanded Capacity: {expansion['expanded_capacity']:.2f}")
        print(f"  Expansion Factor: {expansion['expanded_capacity'] / expansion['base_computational_capacity']:.2f}x")
        
        print("\n" + "=" * 60)
        print("COMPUTATIONAL SIGNIFICANCE ANALYSIS COMPLETE")
        print("=" * 60)
        
        return {
            "device_ranking": ranking,
            "target_devices": target_devices,
            "topology": topology,
            "expansion": expansion
        }

if __name__ == '__main__':
    analyzer = ComputationalSignificanceAnalysis()
    results = analyzer.run_analysis()
    
    # Save results
    output_file = OUTPUT_DIR / "computational_significance_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nAnalysis results saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("COMPUTATIONAL SIGNIFICANCE SUMMARY")
    print("=" * 60)
    print(f"Target Devices: {len(results['target_devices'])}")
    print(f"Topology Nodes: {results['topology']['topology_nodes']}")
    print(f"Expanded Capacity: {results['expansion']['expanded_capacity']:.2f}")
    print(f"Expansion Factor: {results['expansion']['expanded_capacity'] / results['expansion']['base_computational_capacity']:.2f}x")
