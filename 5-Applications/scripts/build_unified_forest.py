#!/usr/bin/env python3
import json
import csv
import uuid
import hashlib
import re
from pathlib import Path

# Paths
BASE_PATH = Path('/home/allaun/Documents/Research Stack')
UNIVERSAL_MODELS_PATH = BASE_PATH / 'shared-data/data/MATH_MODELS_UNIVERSAL.json'
TSV_PATH = BASE_PATH / '3-Mathematical-Models' / 'MATH_MODEL_MAP.tsv'
USER_INVARIANTS_PATH = BASE_PATH / 'shared-data/data/germane/research/REVISED_EQUATIONS/sovereign_invariant_analysis.json'
SPINE_PATH = BASE_PATH / '6-Documentation/archive/from-NoDupeLabs/chemistry_physics_nspace_spine_v0.json'
GENOME18_PATH = BASE_PATH / 'shared-data/data/equations_forest_genome18.jsonl'
EQUATION_FOREST_PATH = BASE_PATH / 'shared-data/data/equations_forest.jsonl'

# UUID Namespaces
NAMESPACE_EQUATION = uuid.UUID('32c1e12a-686a-54af-af6b-16f4379ce5ad')
NAMESPACE_SHAPE = uuid.UUID('e4c875ee-2338-953a-1ba0-bc5c413d1d53')

def canonicalize_formula(formula):
    """Normalize a math formula."""
    if not formula:
        return ""
    formula = formula.replace('\\', '')
    formula = formula.replace('{', '(').replace('}', ')')
    formula = re.sub(r'\s+', ' ', formula).strip()
    known_functions = {'sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'sum', 'prod', 'delta', 'nabla', 'partial'}
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', formula)
    variables = []
    for token in tokens:
        if token.lower() not in known_functions and token not in variables:
            variables.append(token)
    canonical = formula
    for i, var in enumerate(variables):
        canonical = re.sub(r'\b' + re.escape(var) + r'\b', f'x{i}', canonical)
    return canonical

def generate_uuid(name, namespace=NAMESPACE_EQUATION):
    return str(uuid.uuid5(namespace, name))

def map_layer(domain_type):
    if not domain_type: return "GENERAL"
    dt = domain_type.upper()
    if "PHYSICS" in dt or "ENERGY" in dt: return "PHYSICS"
    if "COMPRESSION" in dt or "ROUTING" in dt: return "INFORMATIC"
    if "TOPOLOGY" in dt or "ALGEBRA" in dt: return "STRUCTURE"
    if "VERIFICATION" in dt or "CONTROL" in dt: return "PROTOCOL"
    return "GENERAL"

def main():
    forest = {} # name -> entry

    # 1. Load Universal Models
    if UNIVERSAL_MODELS_PATH.exists():
        with open(UNIVERSAL_MODELS_PATH, 'r') as f:
            data = json.load(f)
            for model in data.get('models', []):
                name = model['name']
                forest[name] = {
                    "uuid": generate_uuid(name),
                    "model_name": name,
                    "formula": model.get('equation', ''),
                    "description": model.get('purpose', ''),
                    "layer": map_layer(model.get('domain_type')),
                    "type": model.get('family', 'GENERAL'),
                    "domain_type": model.get('domain_type', ''),
                    "bind_class": model.get('bind_class', ''),
                    "foundation_vector": [0.0] * 12
                }

    # 2. Load TSV Models
    if TSV_PATH.exists():
        with open(TSV_PATH, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                name = row.get('Model_Name')
                if not name: continue
                if name not in forest:
                    forest[name] = {
                        "uuid": generate_uuid(name),
                        "model_name": name,
                        "formula": row.get('Equation', ''),
                        "description": row.get('Purpose', ''),
                        "layer": map_layer(row.get('Domain_Type')),
                        "type": row.get('Family', 'GENERAL'),
                        "domain_type": row.get('Domain_Type', ''),
                        "bind_class": row.get('Bind_Class', ''),
                        "foundation_vector": [0.0] * 12
                    }
                else:
                    # Update with TSV info if missing
                    if not forest[name]["formula"]: forest[name]["formula"] = row.get('Equation', '')
                    if not forest[name]["description"]: forest[name]["description"] = row.get('Purpose', '')

    # 3. Load User Invariants
    if USER_INVARIANTS_PATH.exists():
        with open(USER_INVARIANTS_PATH, 'r') as f:
            inv_data = json.load(f)
            roots = inv_data.get('invariant_roots', {})
            for cat_roots in roots.values():
                for root_id, root_info in cat_roots.items():
                    name = root_info.get('name')
                    if not name: continue
                    if name not in forest:
                        forest[name] = {
                            "uuid": generate_uuid(name),
                            "model_name": name,
                            "formula": "",
                            "description": root_info.get('root', ''),
                            "layer": "STRUCTURE",
                            "type": root_info.get('type', 'invariant'),
                            "domain_type": "",
                            "bind_class": "",
                            "foundation_vector": [0.0] * 12
                        }

    # 4. Load Chemistry/Physics Spine
    if SPINE_PATH.exists():
        with open(SPINE_PATH, 'r') as f:
            spine_data = json.load(f)
            for eq in spine_data.get('equations', []):
                name = eq['name']
                if name not in forest:
                    forest[name] = {
                        "uuid": generate_uuid(name),
                        "model_name": name,
                        "formula": eq.get('equation', ''),
                        "description": eq.get('meaning', ''),
                        "layer": map_layer(eq.get('layer')),
                        "type": eq.get('domain', 'GENERAL'),
                        "domain_type": eq.get('layer', ''),
                        "bind_class": eq.get('bind', ''),
                        "foundation_vector": [0.0] * 12
                    }

    # 5. Load Genome18 Addresses
    addresses = {}
    if GENOME18_PATH.exists():
        with open(GENOME18_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    addresses[data['model_name']] = data.get('genome18_address')

    # Final Processing
    final_entries = []
    for name, entry in forest.items():
        # Canonicalize
        entry['canonical_formula'] = canonicalize_formula(entry['formula'])
        entry['shape_uuid'] = generate_uuid(entry['canonical_formula'], NAMESPACE_SHAPE)
        
        # Link address if available
        if name in addresses:
            entry['genome18_address'] = addresses[name]
        
        # Add stable metadata
        entry['namespace'] = 'equation_forest'
        entry['typed_status'] = 'canonical'
        
        final_entries.append(entry)

    # Write Output
    with open(EQUATION_FOREST_PATH, 'w') as f:
        for entry in final_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"Successfully built unified forest with {len(final_entries)} entries.")

if __name__ == '__main__':
    main()
