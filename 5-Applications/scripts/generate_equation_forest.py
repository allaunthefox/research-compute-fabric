#!/usr/bin/env python3
import json
import uuid
import hashlib
from pathlib import Path

# Paths
BASE_PATH = Path('/home/allaun/Documents/Research Stack')
UNIVERSAL_MODELS_PATH = BASE_PATH / 'shared-data/data/MATH_MODELS_UNIVERSAL.json'
USER_INVARIANTS_PATH = BASE_PATH / 'shared-data/data/germane/research/REVISED_EQUATIONS/sovereign_invariant_analysis.json'
EQUATION_FOREST_PATH = BASE_PATH / 'shared-data/data/equations_forest.jsonl'

# UUID Namespace for Equation Forest
NAMESPACE_EQUATION = uuid.UUID('32c1e12a-686a-54af-af6b-16f4379ce5ad') # Based on existing forest

def generate_uuid(name):
    """Generate a stable UUIDv5 based on the canonical name."""
    return str(uuid.uuid5(NAMESPACE_EQUATION, name))

def map_layer(domain_type):
    """Map domain_type to unified layer."""
    if not domain_type:
        return "GENERAL"
    if "PHYSICS" in domain_type:
        return "PHYSICS"
    if "COMPRESSION" in domain_type or "ROUTING" in domain_type:
        return "INFORMATIC"
    if "TOPOLOGY" in domain_type or "ALGEBRA" in domain_type:
        return "STRUCTURE"
    if "VERIFICATION" in domain_type or "CONTROL" in domain_type:
        return "PROTOCOL"
    if "ENERGY" in domain_type:
        return "PHYSICS"
    return "GENERAL"

def main():
    if not UNIVERSAL_MODELS_PATH.exists():
        print(f"Error: {UNIVERSAL_MODELS_PATH} not found.")
        return

    with open(UNIVERSAL_MODELS_PATH, 'r') as f:
        data = json.load(f)

    models = data.get('models', [])
    print(f"Loaded {len(models)} models from universal database.")

    # Load existing forest to preserve existing UUIDs if any
    existing_forest = {}
    if EQUATION_FOREST_PATH.exists():
        with open(EQUATION_FOREST_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    existing_forest[entry['name']] = entry

    new_entries = []
    # Process universal models
    FOUNDATION_NAMES = {
        "Shannon_Entropy_Calculation": 0,
        "Byte_Global_Entropy": 1,
        "Hierarchical_Entropy_Decomposition": 2,
        "Carnot_Efficiency": 3,
        "Landauer_Erasure_Bound": 4,
        "Net_Energy_Balance_Threshold": 5,
        "Maxwell_Demon_Recovery_Ratio": 6,
        "Riemannian_Metric_Distance": 7,
        "Christoffel_Connection_Coefficients": 8,
        "Symplectic_Geodesic_Step": 9,
        "Aggregate_Cognitive_Load": 10,
        "Intrinsic_to_Total_Routing_Ratio": 11
    }

    for model in models:
        name = model.get('name')
        if not name:
            continue

        if name in existing_forest:
            entry = existing_forest[name]
        else:
            entry = {
                "uuid": generate_uuid(name),
                "namespace": "equation_forest",
                "layer": map_layer(model.get('domain_type')),
                "type": model.get('family', 'GENERAL'),
                "name": name,
                "description": model.get('purpose', ''),
                "formula": model.get('equation', ''),
                "street_membership": [model.get('domain_type', 'GENERAL')],
                "typed_status": "canonical",
                "foundation_vector": [0.0] * 12
            }
        
        # Tag foundations
        if name in FOUNDATION_NAMES:
            idx = FOUNDATION_NAMES[name]
            entry['typed_status'] = 'foundation'
            entry['foundation_vector'][idx] = 1.0
        
        new_entries.append(entry)

    # Process user invariants
    if USER_INVARIANTS_PATH.exists():
        with open(USER_INVARIANTS_PATH, 'r') as f:
            inv_data = json.load(f)
        
        roots = inv_data.get('invariant_roots', {})
        for cat_key, cat_roots in roots.items():
            for root_id, root_info in cat_roots.items():
                name = root_info.get('name')
                if not name:
                    continue
                
                # Check if already added
                exists = False
                for entry in new_entries:
                    if entry['name'] == name:
                        entry['type'] = root_info.get('type', entry['type'])
                        entry['description'] = root_info.get('root', entry['description'])
                        exists = True
                        break
                
                if not exists:
                    entry = {
                        "uuid": generate_uuid(name),
                        "namespace": "equation_forest",
                        "layer": "STRUCTURE",
                        "type": root_info.get('type', 'invariant'),
                        "name": name,
                        "description": root_info.get('root', ''),
                        "formula": "", # User invariants might not have a formula string here
                        "street_membership": [cat_key],
                        "typed_status": "canonical",
                        "foundation_vector": [0.0] * 12
                    }
                    new_entries.append(entry)
        print(f"Merged user invariants from {USER_INVARIANTS_PATH}")

    # Write to equations_forest.jsonl
    with open(EQUATION_FOREST_PATH, 'w') as f:
        for entry in new_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"Successfully wrote {len(new_entries)} entries to {EQUATION_FOREST_PATH}")

if __name__ == '__main__':
    main()
