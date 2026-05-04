#!/usr/bin/env python3
import json
from pathlib import Path

# Paths
BASE_PATH = Path('/home/allaun/Documents/Research Stack')
EQUATION_FOREST_PATH = BASE_PATH / 'shared-data/data/equations_forest.jsonl'
STREETS_PATH = BASE_PATH / 'shared-data/data/equation_streets.jsonl'

# Define the 5 Streets
STREETS = {
    "S1_ENTROPY": ["COMPRESSION", "ENTROPY", "INFORMATION"],
    "S2_THERMO": ["THERMODYNAMIC", "ENERGY", "LANDAUER", "CARNOT"],
    "S3_GEOMETRY": ["TOPOLOGY", "GEOMETRY", "RIEMANNIAN", "GEODESIC"],
    "S4_LOAD": ["COGNITIVE", "ROUTING", "LOAD", "EFFICIENCY"],
    "S5_BRIDGE": ["BRIDGE", "DIAT", "AVMR", "S3C", "PIST", "NII", "FAMM"]
}

def determine_street(node):
    """Determine the primary street for a node."""
    layer = (node.get('layer') or '').upper()
    domain = (node.get('domain_type') or '').upper()
    type_name = (node.get('type') or '').upper()
    name = (node.get('model_name') or '').upper()

    # Priority check for Bridge street (Level 5)
    for keyword in STREETS["S5_BRIDGE"]:
        if keyword in layer or keyword in domain or keyword in type_name or keyword in name:
            return "S5_BRIDGE"

    # Check other streets
    for street_id, keywords in STREETS.items():
        if street_id == "S5_BRIDGE": continue
        for keyword in keywords:
            if keyword in layer or keyword in domain or keyword in type_name or keyword in name:
                return street_id

    return "S0_GENERAL"

def main():
    if not EQUATION_FOREST_PATH.exists():
        print(f"Error: {EQUATION_FOREST_PATH} not found.")
        return

    nodes = []
    with open(EQUATION_FOREST_PATH, 'r') as f:
        for line in f:
            if line.strip():
                nodes.append(json.loads(line))

    print(f"Assigning {len(nodes)} models to streets...")

    street_entries = []
    counts = {"S1_ENTROPY": 0, "S2_THERMO": 0, "S3_GEOMETRY": 0, "S4_LOAD": 0, "S5_BRIDGE": 0, "S0_GENERAL": 0}

    for node in nodes:
        street = determine_street(node)
        counts[street] += 1
        
        entry = {
            "uuid": node['uuid'],
            "model_name": node['model_name'],
            "primary_street": street,
            "is_bridge_candidate": (street == "S5_BRIDGE")
        }
        street_entries.append(entry)

    with open(STREETS_PATH, 'w') as f:
        for entry in street_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"Successfully saved street assignments to {STREETS_PATH}")
    print("Counts:")
    for s, c in counts.items():
        print(f"  {s}: {c}")

if __name__ == '__main__':
    main()
