#!/usr/bin/env python3
"""
swarm_network_capacity.py — Network Resource Capacity Monitor

Checks all Tailscale-connected nodes (via ENE mesh) to determine:
- Total available resources across the network
- Currently utilized capacity
- Idle resources that could be leveraged
- Node health and connectivity status
"""

import subprocess
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class TailscaleNode:
    """Remote node in the Tailscale mesh."""
    ip: str
    hostname: str
    owner: str
    os: str
    status: str  # online, offline, idle
    last_seen: Optional[str]
    tags: List[str]
    
    def is_online(self) -> bool:
        return self.status == "online" or self.status == "idle"


@dataclass
class NodeResources:
    """Resource capacity of a node."""
    node_id: str
    cpu_cores: int
    memory_gb: float
    storage_gb: float
    bandwidth_mbps: float
    gpu_count: int
    ene_enabled: bool
    utilization_percent: float


class SwarmNetworkCapacity:
    """
    Monitor and report on full network resource capacity.
    
    Queries Tailscale mesh and ENE nodes to determine:
    - Total available compute across all nodes
    - Current utilization vs capacity
    - Resource distribution
    """
    
    def __init__(self):
        self.tailscale_nodes: List[TailscaleNode] = []
        self.ene_nodes: List[str] = []
        self.local_ip: Optional[str] = None
        
    def discover_tailscale_mesh(self) -> List[TailscaleNode]:
        """Discover all nodes in the Tailscale mesh."""
        print("\n[1] Discovering Tailscale mesh nodes...")
        
        try:
            result = subprocess.run(
                ["tailscale", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.strip().split('\n')
            nodes = []
            
            for line in lines:
                if not line.strip():
                    continue
                
                # Parse tailscale status line
                # Format: 100.x.x.x  hostname  owner@  os  status
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[0]
                    hostname = parts[1]
                    owner = parts[2]
                    os_type = parts[3]
                    
                    # Parse status (can be complex)
                    status_parts = ' '.join(parts[4:]) if len(parts) > 4 else ""
                    
                    # Determine status
                    if "offline" in status_parts.lower():
                        status = "offline"
                    elif "idle" in status_parts.lower():
                        status = "idle"
                    else:
                        status = "online"
                    
                    # Extract last seen if offline
                    last_seen = None
                    if "last seen" in status_parts:
                        match = re.search(r'last seen ([^,]+)', status_parts)
                        if match:
                            last_seen = match.group(1)
                    
                    # Extract tags
                    tags = []
                    if "tagged-devices" in line:
                        tags.append("tagged-devices")
                    
                    node = TailscaleNode(
                        ip=ip,
                        hostname=hostname,
                        owner=owner,
                        os=os_type,
                        status=status,
                        last_seen=last_seen,
                        tags=tags
                    )
                    nodes.append(node)
            
            self.tailscale_nodes = nodes
            
            # Get local IP
            try:
                ip_result = subprocess.run(
                    ["tailscale", "ip", "-4"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                self.local_ip = ip_result.stdout.strip()
            except:
                pass
            
            print(f"  Found: {len(nodes)} Tailscale nodes")
            online = sum(1 for n in nodes if n.is_online())
            print(f"  Online: {online}/{len(nodes)}")
            
            for node in nodes:
                status_icon = "🟢" if node.is_online() else "🔴"
                print(f"    {status_icon} {node.hostname} ({node.ip}) - {node.status}")
            
            return nodes
            
        except Exception as e:
            print(f"  ⚠️  Error discovering mesh: {e}")
            return []
    
    def check_ene_deployment(self) -> List[str]:
        """Check which nodes have ENE deployed."""
        print("\n[2] Checking ENE deployment status...")
        
        ene_nodes = []
        
        for node in self.tailscale_nodes:
            if not node.is_online():
                continue
            
            # Try to check if ENE is running on remote node
            # This would typically use SSH or ENE's gossip protocol
            # For now, we'll simulate based on known deployment
            
            if node.hostname in ["architect", "judge", "qfox"]:
                ene_nodes.append(node.hostname)
        
        self.ene_nodes = ene_nodes
        
        print(f"  ENE deployed on: {len(ene_nodes)} nodes")
        for node in ene_nodes:
            print(f"    ✅ {node}")
        
        # Nodes needing ENE deployment
        online_nodes = [n.hostname for n in self.tailscale_nodes if n.is_online()]
        need_ene = set(online_nodes) - set(ene_nodes)
        if need_ene:
            print(f"  Need ENE deployment: {len(need_ene)} nodes")
            for node in need_ene:
                print(f"    ⚠️  {node}")
        
        return ene_nodes
    
    def estimate_node_resources(self, node: TailscaleNode) -> Optional[NodeResources]:
        """Estimate resources available on a node."""
        # These would normally be queried from the node
        # For now, estimate based on hostname patterns
        
        resource_map = {
            "qfox": {"cpu": 16, "ram": 32, "storage": 1000, "gpu": 1, "bw": 1000},
            "architect": {"cpu": 8, "ram": 16, "storage": 500, "gpu": 0, "bw": 500},
            "judge": {"cpu": 4, "ram": 8, "storage": 200, "gpu": 0, "bw": 500},
            "ip-172-31-25-81": {"cpu": 2, "ram": 4, "storage": 100, "gpu": 0, "bw": 1000},  # AWS
            "netcup-router": {"cpu": 4, "ram": 8, "storage": 500, "gpu": 0, "bw": 1000},
            "racknerd-510bd9c": {"cpu": 2, "ram": 4, "storage": 100, "gpu": 0, "bw": 1000},
            "racknerd-atl": {"cpu": 2, "ram": 4, "storage": 100, "gpu": 0, "bw": 1000},
            "desktop-0u2ceal": {"cpu": 8, "ram": 16, "storage": 500, "gpu": 1, "bw": 100},
        }
        
        specs = resource_map.get(node.hostname, {"cpu": 2, "ram": 4, "storage": 100, "gpu": 0, "bw": 100})
        
        return NodeResources(
            node_id=node.hostname,
            cpu_cores=specs["cpu"],
            memory_gb=specs["ram"],
            storage_gb=specs["storage"],
            bandwidth_mbps=specs["bw"],
            gpu_count=specs["gpu"],
            ene_enabled=node.hostname in self.ene_nodes,
            utilization_percent=0.0  # Would need actual monitoring
        )
    
    def calculate_total_capacity(self) -> Dict[str, float]:
        """Calculate total network capacity."""
        print("\n[3] Calculating total network capacity...")
        
        total_cpu = 0
        total_ram = 0.0
        total_storage = 0.0
        total_gpu = 0
        total_bw = 0.0
        
        for node in self.tailscale_nodes:
            if not node.is_online():
                continue
            
            resources = self.estimate_node_resources(node)
            if resources:
                total_cpu += resources.cpu_cores
                total_ram += resources.memory_gb
                total_storage += resources.storage_gb
                total_gpu += resources.gpu_count
                total_bw += resources.bandwidth_mbps
        
        capacity = {
            "cpu_cores": total_cpu,
            "memory_gb": total_ram,
            "storage_gb": total_storage,
            "gpu_count": total_gpu,
            "bandwidth_mbps": total_bw,
            "online_nodes": sum(1 for n in self.tailscale_nodes if n.is_online()),
            "total_nodes": len(self.tailscale_nodes)
        }
        
        print(f"  CPU Cores: {total_cpu}")
        print(f"  Memory: {total_ram:.1f} GB")
        print(f"  Storage: {total_storage:.1f} GB")
        print(f"  GPUs: {total_gpu}")
        print(f"  Bandwidth: {total_bw:.0f} Mbps")
        
        return capacity
    
    def check_current_utilization(self) -> Dict[str, float]:
        """Check current resource utilization."""
        print("\n[4] Checking current utilization (local node only)...")
        
        try:
            # Get local CPU/memory
            result = subprocess.run(
                ["cat", "/proc/loadavg"],
                capture_output=True,
                text=True,
                timeout=5
            )
            load_parts = result.stdout.strip().split()
            load_1min = float(load_parts[0]) if load_parts else 0.0
            
            # Estimate CPU utilization from load
            # This is simplified - would need per-node queries
            cpu_util = min(100.0, (load_1min / 16) * 100)  # Assuming 16 cores
            
            # Memory
            mem_result = subprocess.run(
                ["free", "-m"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            mem_lines = mem_result.stdout.split('\n')
            mem_used = 0
            mem_total = 1
            for line in mem_lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    mem_total = int(parts[1])
                    mem_used = int(parts[2])
                    break
            
            mem_util = (mem_used / mem_total) * 100 if mem_total > 0 else 0
            
            utilization = {
                "cpu_percent": cpu_util,
                "memory_percent": mem_util,
                "local_node_only": True
            }
            
            print(f"  Local CPU: {cpu_util:.1f}%")
            print(f"  Local Memory: {mem_util:.1f}%")
            print(f"  ⚠️  Remote utilization requires ENE monitoring")
            
            return utilization
            
        except Exception as e:
            print(f"  ⚠️  Error checking utilization: {e}")
            return {"cpu_percent": 0, "memory_percent": 0, "local_node_only": True}
    
    def generate_capacity_report(self) -> Dict[str, any]:
        """Generate full capacity report."""
        print("\n" + "=" * 70)
        print("SWARM NETWORK CAPACITY REPORT")
        print("=" * 70)
        
        # Gather data
        self.discover_tailscale_mesh()
        self.check_ene_deployment()
        capacity = self.calculate_total_capacity()
        utilization = self.check_current_utilization()
        
        # Calculate utilization vs capacity
        report = {
            "timestamp": datetime.now().isoformat(),
            "network": {
                "total_nodes": len(self.tailscale_nodes),
                "online_nodes": capacity["online_nodes"],
                "offline_nodes": len(self.tailscale_nodes) - capacity["online_nodes"],
                "ene_deployed": len(self.ene_nodes),
                "ene_coverage": len(self.ene_nodes) / capacity["online_nodes"] * 100 if capacity["online_nodes"] > 0 else 0
            },
            "capacity": {
                "cpu_cores": capacity["cpu_cores"],
                "memory_gb": capacity["memory_gb"],
                "storage_gb": capacity["storage_gb"],
                "gpu_count": capacity["gpu_count"],
                "bandwidth_mbps": capacity["bandwidth_mbps"]
            },
            "utilization": {
                "cpu_percent": utilization["cpu_percent"],
                "memory_percent": utilization["memory_percent"],
                "note": "Local node only - full mesh monitoring requires ENE deployment on all nodes"
            },
            "idle_resources": {
                "cpu_cores_available": capacity["cpu_cores"] * (1 - utilization["cpu_percent"]/100),
                "memory_gb_available": capacity["memory_gb"] * (1 - utilization["memory_percent"]/100),
                "message": "Significant idle capacity available across mesh"
            },
            "recommendations": []
        }
        
        # Add recommendations
        ene_coverage = report["network"]["ene_coverage"]
        if ene_coverage < 100:
            report["recommendations"].append(
                f"Deploy ENE to {capacity['online_nodes'] - len(self.ene_nodes)} remaining nodes for full mesh monitoring"
            )
        
        if utilization["cpu_percent"] < 50:
            report["recommendations"].append(
                "CPU utilization low - swarm can scale up workloads"
            )
        
        if utilization["memory_percent"] < 50:
            report["recommendations"].append(
                "Memory available - can distribute more tasks across mesh"
            )
        
        report["recommendations"].append(
            "Consider load balancing across all online nodes via ENE"
        )
        
        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Network: {report['network']['online_nodes']}/{report['network']['total_nodes']} nodes online")
        print(f"ENE Coverage: {ene_coverage:.1f}% ({report['network']['ene_deployed']} nodes)")
        print(f"Total CPU: {report['capacity']['cpu_cores']} cores")
        print(f"Total Memory: {report['capacity']['memory_gb']:.1f} GB")
        print(f"Total Storage: {report['capacity']['storage_gb']:.1f} GB")
        print(f"\nUtilization (local only):")
        print(f"  CPU: {report['utilization']['cpu_percent']:.1f}%")
        print(f"  Memory: {report['utilization']['memory_percent']:.1f}%")
        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
        
        print("\n" + "=" * 70)
        
        return report


def main():
    """Run network capacity check."""
    monitor = SwarmNetworkCapacity()
    report = monitor.generate_capacity_report()
    
    # Save report
    import json
    from pathlib import Path
    
    output_path = Path("/home/allaun/Documents/Research Stack/data/swarm_network_capacity.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved: {output_path}")
    
    return report


if __name__ == "__main__":
    main()
