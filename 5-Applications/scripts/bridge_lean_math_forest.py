#!/usr/bin/env python3
"""
Bridge Lean Analysis Math with Forest Equations

Uses Equation Forest bridge nodes (B1-B8) to systematically bridge
Lean analysis math equations with forest equations based on intersections.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any


class ForestBridge:
    """
    Bridges equations using Equation Forest bridge nodes.
    """
    
    # Bridge nodes from Equation Forest
    BRIDGES = {
        "B1": {"name": "Entropy ↔ Load", "from": "entropy", "to": "load"},
        "B2": {"name": "AVMR ↔ Entropy", "from": "avmr", "to": "entropy"},
        "B3": {"name": "S3C ↔ Codec", "from": "s3c", "to": "codec"},
        "B4": {"name": "PIST ↔ Surface", "from": "pist", "to": "surface"},
        "B5": {"name": "Geometry ↔ Energy", "from": "geometry", "to": "energy"},
        "B6": {"name": "Load ↔ Verification", "from": "load", "to": "verification"},
        "B7": {"name": "Energy ↔ Control", "from": "energy", "to": "control"},
        "B8": {"name": "Codec ↔ Verification", "from": "codec", "to": "verification"}
    }
    
    def __init__(self):
        self.bridges_created = []
    
    def classify_equation_domain(self, equation: Dict[str, str]) -> str:
        """
        Classify equation into a domain for bridging.
        """
        # Handle both Lean equations (Model_Name) and forest equations (name)
        name = equation.get("Model_Name", equation.get("name", "")).lower()
        family = equation.get("Family", equation.get("family", "")).lower()
        equation_str = equation.get("Equation", equation.get("equation", "")).lower()
        
        # Classification logic
        if "continuity" in name or "differentiable" in name:
            return "surface"  # Continuity = surface smoothness
        elif "convex" in name:
            return "geometry"  # Convexity = geometric property
        elif "lipschitz" in name or "ode" in name:
            return "energy"  # ODE/Lipschitz = energy dynamics
        elif "topology" in family or "manifold" in name:
            return "geometry"  # Topology = geometry
        elif "efficiency" in family:
            return "load"  # Efficiency = load reduction
        elif "entropy" in equation_str:
            return "entropy"
        elif "verification" in equation_str:
            return "verification"
        elif "control" in equation_str:
            return "control"
        elif "codec" in equation_str or "compression" in equation_str:
            return "codec"
        elif "pist" in equation_str:
            return "pist"
        elif "avmr" in equation_str:
            return "avmr"
        elif "s3c" in equation_str:
            return "s3c"
        else:
            return "surface"  # Default to surface for analysis math
    
    def find_bridge(self, from_domain: str, to_domain: str) -> Dict[str, str]:
        """
        Find appropriate bridge node between two domains.
        """
        for bridge_id, bridge in self.BRIDGES.items():
            if bridge["from"] == from_domain and bridge["to"] == to_domain:
                return {"id": bridge_id, **bridge}
            if bridge["from"] == to_domain and bridge["to"] == from_domain:
                return {"id": bridge_id, **bridge}
        
        # No direct bridge, try indirect
        return None
    
    def create_bridge(self, lean_eq: Dict[str, str], forest_eq: Dict[str, str]) -> Dict[str, Any]:
        """
        Create a bridge between Lean and forest equations.
        """
        lean_domain = self.classify_equation_domain(lean_eq)
        forest_domain = self.classify_equation_domain(forest_eq)
        
        bridge = self.find_bridge(lean_domain, forest_domain)
        
        if bridge:
            bridge_record = {
                "bridge_id": bridge["id"],
                "bridge_name": bridge["name"],
                "lean_equation": lean_eq["Model_Name"],
                "forest_equation": forest_eq["name"],
                "lean_domain": lean_domain,
                "forest_domain": forest_domain,
                "connection_type": "direct"
            }
        else:
            # Indirect bridge via intermediate domain
            bridge_record = {
                "bridge_id": "INDIRECT",
                "bridge_name": f"{lean_domain} → {forest_domain}",
                "lean_equation": lean_eq["Model_Name"],
                "forest_equation": forest_eq["name"],
                "lean_domain": lean_domain,
                "forest_domain": forest_domain,
                "connection_type": "indirect"
            }
        
        self.bridges_created.append(bridge_record)
        return bridge_record
    
    def bridge_all(self, lean_equations: List[Dict[str, str]], 
                   forest_equations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Bridge all Lean equations with forest equations.
        """
        bridges = []
        
        # Create bridges based on intersections
        for lean_eq in lean_equations:
            for forest_eq in forest_equations:
                # Check if they should be bridged
                lean_name = lean_eq["Model_Name"].lower()
                forest_name = forest_eq["name"].lower()
                
                # Bridge based on domain classification
                lean_domain = self.classify_equation_domain(lean_eq)
                forest_domain = self.classify_equation_domain(forest_eq)
                
                # Only bridge if domains differ
                if lean_domain != forest_domain:
                    bridge = self.create_bridge(lean_eq, forest_eq)
                    bridges.append(bridge)
        
        return bridges


def main():
    """Bridge Lean analysis math with forest equations."""
    print("=" * 70)
    print("BRIDGE LEAN ANALYSIS MATH WITH FOREST")
    print("=" * 70)
    
    # Load Lean math equations
    print("\n[*] Loading Lean math equations...")
    with open('/home/allaun/Documents/Research Stack/data/lean_math_forest_import.json', 'r') as f:
        lean_data = json.load(f)
    
    lean_equations = lean_data["math_models"]
    print(f"    Loaded {len(lean_equations)} Lean equations")
    
    # Load forest equations
    print(f"\n[*] Loading forest equations...")
    forest_equations = []
    tsv_path = Path(__file__).resolve().parent.parent.parent / "3-Mathematical-Models" / "MATH_MODEL_MAP.tsv"
    with open(tsv_path, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                forest_equations.append({
                    "name": parts[1],
                    "family": parts[2],
                    "equation": parts[3],
                    "variables": parts[4]
                })
    
    print(f"    Loaded {len(forest_equations)} forest equations")
    
    # Create bridges
    print(f"\n[*] Creating bridges using Equation Forest bridge nodes...")
    bridge_system = ForestBridge()
    
    # Bridge Lean equations with forest equations
    bridges = bridge_system.bridge_all(lean_equations, forest_equations)
    
    print(f"    Created {len(bridges)} bridges")
    
    # Analyze bridges by type
    direct_bridges = [b for b in bridges if b["connection_type"] == "direct"]
    indirect_bridges = [b for b in bridges if b["connection_type"] == "indirect"]
    
    print(f"\n[*] Bridge Analysis:")
    print(f"    Direct bridges: {len(direct_bridges)}")
    print(f"    Indirect bridges: {len(indirect_bridges)}")
    
    # Show bridges by bridge node
    bridge_counts = {}
    for bridge in direct_bridges:
        bridge_id = bridge["bridge_id"]
        bridge_counts[bridge_id] = bridge_counts.get(bridge_id, 0) + 1
    
    print(f"\n[*] Direct Bridges by Node:")
    for bridge_id, count in sorted(bridge_counts.items()):
        bridge_name = ForestBridge.BRIDGES[bridge_id]["name"]
        print(f"    {bridge_id} ({bridge_name}): {count} bridges")
    
    # Show sample bridges
    print(f"\n[*] Sample Direct Bridges:")
    for bridge in direct_bridges[:10]:
        print(f"    {bridge['bridge_id']}: {bridge['lean_equation']} ↔ {bridge['forest_equation']}")
        print(f"        {bridge['lean_domain']} → {bridge['forest_domain']}")
    
    print(f"\n[*] Sample Indirect Bridges:")
    for bridge in indirect_bridges[:5]:
        print(f"    {bridge['lean_equation']} ↔ {bridge['forest_equation']}")
        print(f"        {bridge['lean_domain']} → {bridge['forest_domain']}")
    
    # Calculate bridge coverage
    lean_bridged = set(b["lean_equation"] for b in bridges)
    forest_bridged = set(b["forest_equation"] for b in bridges)
    
    print(f"\n[*] Bridge Coverage:")
    print(f"    Lean equations bridged: {len(lean_bridged)}/{len(lean_equations)} ({len(lean_bridged)/len(lean_equations)*100:.1f}%)")
    print(f"    Forest equations bridged: {len(forest_bridged)}/{len(forest_equations)} ({len(forest_bridged)/len(forest_equations)*100:.1f}%)")
    
    # Save results
    results = {
        "total_bridges": len(bridges),
        "direct_bridges": len(direct_bridges),
        "indirect_bridges": len(indirect_bridges),
        "bridge_counts": bridge_counts,
        "bridges": bridges,
        "coverage": {
            "lean_bridged": len(lean_bridged),
            "lean_total": len(lean_equations),
            "forest_bridged": len(forest_bridged),
            "forest_total": len(forest_equations)
        }
    }
    
    output_path = "/home/allaun/Documents/Research Stack/data/lean_math_forest_bridges.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ LEAN MATH - FOREST BRIDGING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
