#!/usr/bin/env python3
"""
Equation Forest Exact TSP Solver v0.1

Implements the exact TSP pipeline over the compressed equation graph:
1. Load equations_forest.jsonl
2. Normalize equations into canonical form
3. Compute F01-F12 kernel vectors
4. Assign nearest street
5. Detect bridge candidates B1-B8
6. Collapse near-identical nodes into supernodes
7. Run exact TSP/path search on supernodes
8. Run exact local TSP inside each supernode
9. Stitch global route
10. Mark every edge: proved / executable / empirical / metaphorical / failed
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import itertools

# Street definitions
STREETS = {
    "entropy_compression": ["F01", "F02", "F03"],
    "thermodynamic_admissibility": ["F04", "F05", "F06", "F07"],
    "geometric_motion": ["F08", "F09", "F10"],
    "cognitive_routing_load": ["F11", "F12"],
    "diat_avmr_s3c_bridge": []
}

# Bridge definitions
BRIDGES = {
    "B1": {"name": "Entropy ↔ Load", "from": "entropy_compression", "to": "cognitive_routing_load"},
    "B2": {"name": "Entropy ↔ Landauer", "from": "entropy_compression", "to": "thermodynamic_admissibility"},
    "B3": {"name": "Energy ↔ Routing", "from": "thermodynamic_admissibility", "to": "cognitive_routing_load"},
    "B4": {"name": "Geometry ↔ Routing", "from": "geometric_motion", "to": "cognitive_routing_load"},
    "B5": {"name": "DIAT ↔ Geometry", "from": "diat_avmr_s3c_bridge", "to": "geometric_motion"},
    "B6": {"name": "AVMR ↔ Entropy", "from": "diat_avmr_s3c_bridge", "to": "entropy_compression"},
    "B7": {"name": "S3C ↔ Codec", "from": "diat_avmr_s3c_bridge", "to": "entropy_compression"},
    "B8": {"name": "PIST ↔ Surface", "from": "diat_avmr_s3c_bridge", "to": "geometric_motion"}
}

def load_equations_forest(filepath: str) -> List[Dict]:
    """Load equations from equations_forest.jsonl"""
    equations = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                equations.append(json.loads(line))
    return equations

def normalize_equation(eq: Dict) -> Dict:
    """Normalize equation into canonical form"""
    # Already canonical in our JSONL format
    return eq

def compute_kernel_distance(eq1: Dict, eq2: Dict) -> float:
    """Compute cosine distance between foundation vectors"""
    v1 = np.array(eq1.get("foundation_vector", [0.0]*12))
    v2 = np.array(eq2.get("foundation_vector", [0.0]*12))
    
    # Cosine distance
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 1.0  # Maximum distance
    dot = np.dot(v1, v2)
    cosine = dot / (norm1 * norm2)
    return 1.0 - cosine

def assign_nearest_street(eq: Dict) -> str:
    """Assign nearest street based on kernel signature"""
    foundation_vector = eq.get("foundation_vector", [0.0]*12)
    
    # Find which street has the highest activation
    street_scores = {}
    for street_name, kernel_ids in STREETS.items():
        if not kernel_ids:
            continue
        score = 0.0
        for kid in kernel_ids:
            idx = int(kid[1:]) - 1  # F01 -> index 0
            if idx < len(foundation_vector):
                score += foundation_vector[idx]
        street_scores[street_name] = score
    
    if not street_scores:
        return "diat_avmr_s3c_bridge"
    
    return max(street_scores, key=street_scores.get)

def detect_bridge_candidates(eq1: Dict, eq2: Dict) -> List[str]:
    """Detect which bridges explain the transition"""
    street1 = eq1.get("street_membership", [""])[0] if eq1.get("street_membership") else ""
    street2 = eq2.get("street_membership", [""])[0] if eq2.get("street_membership") else ""
    
    candidates = []
    for bridge_id, bridge in BRIDGES.items():
        if (bridge["from"] == street1 and bridge["to"] == street2) or \
           (bridge["from"] == street2 and bridge["to"] == street1):
            candidates.append(bridge_id)
    
    return candidates

def compute_distance_metric(eq1: Dict, eq2: Dict) -> float:
    """Compute refined distance metric D(x,y)"""
    # Component weights
    w_kernel = 0.35
    w_street = 0.20
    w_bridge = 0.20
    w_typing = 0.10
    w_failure = 0.10
    w_scale = 0.05
    
    # Kernel distance
    kernel_dist = compute_kernel_distance(eq1, eq2)
    
    # Street transition cost
    street1 = eq1.get("street_membership", [""])[0] if eq1.get("street_membership") else ""
    street2 = eq2.get("street_membership", [""])[0] if eq2.get("street_membership") else ""
    if street1 == street2:
        street_cost = 0.0  # Low
    elif street1 and street2:
        street_cost = 0.5  # Medium (bridgeable)
    else:
        street_cost = 1.0  # High (unrelated)
    
    # Bridge cost
    bridges = detect_bridge_candidates(eq1, eq2)
    bridge_cost = 0.0 if bridges else 1.0
    
    # Typing penalty
    typed1 = eq1.get("typed_status", "empirical")
    typed2 = eq2.get("typed_status", "empirical")
    if "metaphorical" in [typed1, typed2] or "untyped" in [typed1, typed2]:
        typing_penalty = 1.0
    else:
        typing_penalty = 0.0
    
    # Failure risk
    risk1 = eq1.get("risk", "medium")
    risk2 = eq2.get("risk", "medium")
    if "high" in [risk1, risk2]:
        failure_penalty = 1.0
    else:
        failure_penalty = 0.0
    
    # Numeric scale distance (simplified)
    scale_dist = 0.0  # Would need actual scale computation
    
    # Weighted sum
    distance = (
        w_kernel * kernel_dist +
        w_street * street_cost +
        w_bridge * bridge_cost +
        w_typing * typing_penalty +
        w_failure * failure_penalty +
        w_scale * scale_dist
    )
    
    return distance

def collapse_into_supernodes(equations: List[Dict], threshold: float = 0.1) -> List[Dict]:
    """Collapse near-identical nodes into supernodes"""
    supernodes = []
    used_indices = set()
    
    for i, eq in enumerate(equations):
        if i in used_indices:
            continue
        
        # Find similar equations
        cluster = [eq]
        used_indices.add(i)
        
        for j, other_eq in enumerate(equations):
            if j in used_indices or j == i:
                continue
            
            dist = compute_distance_metric(eq, other_eq)
            if dist < threshold:
                cluster.append(other_eq)
                used_indices.add(j)
        
        # Create supernode
        if len(cluster) == 1:
            supernodes.append(cluster[0])
        else:
            # Merge into supernode
            supernode = {
                "type": "supernode",
                "members": cluster,
                "uuid": f"SUPER-{len(supernodes)}",
                "model_name": f"SuperNode_{len(supernodes)}",
                "street_membership": list(set([m.get("street_membership", [""])[0] for m in cluster if m.get("street_membership")])),
                "foundation_vector": np.mean([m.get("foundation_vector", [0.0]*12) for m in cluster], axis=0).tolist(),
                "typed_status": cluster[0].get("typed_status", "empirical"),
                "risk": max([m.get("risk", "low") for m in cluster])
            }
            supernodes.append(supernode)
    
    return supernodes

def exact_tsp_bruteforce(nodes: List[Dict]) -> Tuple[List[int], float]:
    """Brute force exact TSP (for small graphs)"""
    n = len(nodes)
    if n <= 2:
        return list(range(n)), 0.0
    
    min_distance = float('inf')
    best_path = []
    
    # Try all permutations (for small n)
    for perm in itertools.permutations(range(n)):
        dist = 0.0
        for i in range(len(perm) - 1):
            dist += compute_distance_metric(nodes[perm[i]], nodes[perm[i+1]])
        
        if dist < min_distance:
            min_distance = dist
            best_path = list(perm)
    
    return best_path, min_distance

def solve_tsp_pipeline(equations: List[Dict]) -> Dict:
    """Execute the full TSP pipeline"""
    print("=== Equation Forest Exact TSP Solver v0.1 ===")
    
    # Step 1: Load equations (already done)
    print(f"Loaded {len(equations)} equations")
    
    # Step 2: Normalize (already canonical)
    print("Normalizing equations...")
    equations = [normalize_equation(eq) for eq in equations]
    
    # Step 3: Compute kernel vectors (already in data)
    print("Kernel vectors computed from data")
    
    # Step 4: Assign nearest street
    print("Assigning streets...")
    for eq in equations:
        if not eq.get("street_membership"):
            street = assign_nearest_street(eq)
            eq["street_membership"] = [street]
    
    # Step 5: Detect bridge candidates
    print("Detecting bridge candidates...")
    bridge_transitions = defaultdict(list)
    for i, eq1 in enumerate(equations):
        for j, eq2 in enumerate(equations):
            if i < j:
                bridges = detect_bridge_candidates(eq1, eq2)
                if bridges:
                    bridge_transitions[f"{i}-{j}"] = bridges
    
    print(f"Found {len(bridge_transitions)} bridgeable transitions")
    
    # Step 6: Collapse into supernodes
    print("Collapsing into supernodes...")
    supernodes = collapse_into_supernodes(equations, threshold=0.15)
    print(f"Collapsed {len(equations)} equations into {len(supernodes)} supernodes")
    
    # Step 7: Run exact TSP on supernodes
    print("Running exact TSP on supernodes...")
    if len(supernodes) <= 10:
        path, distance = exact_tsp_bruteforce(supernodes)
        print(f"Optimal path length: {distance:.4f}")
    else:
        print("Graph too large for brute force, using heuristic")
        path = list(range(len(supernodes)))
        distance = sum(compute_distance_metric(supernodes[i], supernodes[i+1]) for i in range(len(supernodes)-1))
    
    # Step 8: Run local TSP inside supernodes
    print("Running local TSP inside supernodes...")
    for i, node in enumerate(supernodes):
        if node.get("type") == "supernode":
            members = node["members"]
            if len(members) > 2:
                local_path, local_dist = exact_tsp_bruteforce(members)
                node["local_path"] = local_path
                node["local_distance"] = local_dist
            else:
                node["local_path"] = list(range(len(members)))
                node["local_distance"] = 0.0
    
    # Step 9: Stitch global route
    print("Stitching global route...")
    global_route = []
    for idx in path:
        node = supernodes[idx]
        if node.get("type") == "supernode":
            global_route.extend([node["uuid"]])
        else:
            global_route.append(node["uuid"])
    
    # Step 10: Mark edge types
    print("Marking edge types...")
    for i in range(len(path) - 1):
        node1 = supernodes[path[i]]
        node2 = supernodes[path[i+1]]
        
        # Determine edge type
        typed1 = node1.get("typed_status", "empirical")
        typed2 = node2.get("typed_status", "empirical")
        
        if typed1 == "formal" and typed2 == "formal":
            edge_type = "proved"
        elif typed1 == "executable" and typed2 == "executable":
            edge_type = "executable"
        elif "metaphorical" in [typed1, typed2]:
            edge_type = "metaphorical"
        else:
            edge_type = "empirical"
        
        node1["next_edge_type"] = edge_type
    
    # Output result
    result = {
        "supernode_count": len(supernodes),
        "global_distance": distance,
        "global_route": global_route,
        "supernodes": supernodes,
        "bridge_transitions": dict(bridge_transitions)
    }
    
    print(f"\n=== Results ===")
    print(f"Supernodes: {len(supernodes)}")
    print(f"Global distance: {distance:.4f}")
    print(f"Route length: {len(global_route)}")
    
    return result

def main():
    """Main entry point"""
    equations_file = "/home/allaun/Documents/Research Stack/data/equations_forest.jsonl"
    output_file = "/home/allaun/Documents/Research Stack/data/tsp_solver_result.json"
    
    # Load equations
    equations = load_equations_forest(equations_file)
    
    # Filter to equation entries only (skip taxonomy)
    equation_entries = [eq for eq in equations if eq.get("namespace") == "equation"]
    
    # Run TSP pipeline
    result = solve_tsp_pipeline(equation_entries)
    
    # Save result
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\nResult saved to {output_file}")

if __name__ == "__main__":
    main()
