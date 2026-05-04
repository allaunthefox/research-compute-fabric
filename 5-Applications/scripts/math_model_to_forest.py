#!/usr/bin/env python3
"""
Convert MATH_MODEL_MAP.tsv entries to equations_forest.jsonl format
This script adds new equations from MATH_MODEL_MAP to the equations forest
"""

import json
import csv
import uuid
import hashlib
from pathlib import Path

try:
    from math_model_to_forest_core import canonical_hash, generate_uuid
except ImportError:
    UUID_NAMESPACE = uuid.UUID("01000000-0000-4000-8000-000000000000")

    def generate_uuid(prefix: str, index: int) -> str:
        """Generate deterministic UUID for equation."""
        seed = f"{prefix}-{index:04d}"
        return str(uuid.uuid5(UUID_NAMESPACE, seed))

    def canonical_hash(value: str) -> str:
        """Generate a stable canonical SHA-256 hash."""
        return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()

def get_foundation_vector(bind_class: str) -> list:
    """Generate foundation vector based on bind class"""
    # Default to zeros, can be refined based on bind class
    return [0.0] * 12

def get_street_membership(domain_type: str) -> list:
    """Generate street membership based on domain type"""
    mapping = {
        'LAYER_A_COMPRESSION': ['entropy_compression'],
        'LAYER_B_ROUTING': ['routing'],
        'LAYER_C_TOPOLOGY': ['geometry'],
        'LAYER_D_INVARIANTS': ['geometry'],
        'LAYER_E_VERIFICATION': ['thermodynamic'],
        'LAYER_F_CONTROL': ['bridge'],
        'LAYER_G_ENERGY': ['thermodynamic']
    }
    return mapping.get(domain_type, [])

def tsv_to_forest_entry(row: dict, index: int) -> dict:
    """Convert TSV row to equations_forest.jsonl entry"""
    model_name = row.get('Model_Name', '')
    family = row.get('Family', '')
    equation = row.get('Equation', '')
    domain_type = row.get('Domain_Type', '')
    bind_class = row.get('Bind_Class', '')
    status = row.get('Status', '')

    # Generate UUID
    eq_uuid = generate_uuid(family.replace(' ', '_'), index)

    # Get object type (executable_expression for equations)
    object_uuid = "00000000-0000-4000-8000-000000000005"  # executable_expression

    # Get shape, transform, persistence, edge (use defaults)
    shape_uuid = "00000000-0000-4000-8000-000000000004"  # unary
    transform_uuid = "00000000-0000-4000-8000-000000000002"  # unchanged_under_composition
    persistence_uuid = "00000000-0000-4000-8000-000000000002"  # survives_one_transform
    edge_uuid = "00000000-0000-4000-8000-000000000001"  # same_canonical_form

    # Generate canonical hash
    equation_hash = canonical_hash(equation)

    # Build entry
    entry = {
        'uuid': eq_uuid,
        'namespace': 'equation',
        'layer': 'EQUATION',
        'object': object_uuid,
        'shape': shape_uuid,
        'transform': transform_uuid,
        'persistence': persistence_uuid,
        'edge': edge_uuid,
        'failure': None,
        'canonical_hash': equation_hash,
        'model_name': model_name,
        'family': family,
        'equation': equation,
        'variables': row.get('Variables', ''),
        'purpose': row.get('Purpose', ''),
        'location': row.get('Location', ''),
        'implemented': row.get('Implemented', ''),
        'status': status,
        'cross_refs': row.get('Cross_Refs', ''),
        'domain_type': domain_type,
        'bind_class': bind_class,
        'street_membership': get_street_membership(domain_type),
        'typed_status': 'formal' if status == '✅' else 'executable',
        'compression_role': 'none',
        'energy_role': 'none',
        'geometry_role': 'none',
        'routing_role': 'none',
        'risk': 'low' if status == '✅' else 'medium',
        'foundation_vector': get_foundation_vector(bind_class)
    }

    return entry

def main():
    base_path = Path('/home/allaun/Documents/Research Stack')
    tsv_path = base_path / '3-Mathematical-Models' / 'MATH_MODEL_MAP.tsv'
    forest_path = base_path / 'shared-data' / 'data' / 'equations_forest.jsonl'

    # Read existing forest to avoid duplicates
    existing_uuids = set()
    existing_names = set()
    if forest_path.exists():
        with open(forest_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('layer') == 'EQUATION':
                        existing_uuids.add(data.get('uuid'))
                        existing_names.add(data.get('model_name'))
                except:
                    pass

    # Read TSV and generate new entries
    new_entries = []
    with open(tsv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            model_name = row.get('Model_Name', '')
            if model_name and model_name not in existing_names:
                entry = tsv_to_forest_entry(row, i + 100)  # Offset index
                if entry['uuid'] not in existing_uuids:
                    new_entries.append(entry)
                    print(f"Added: {model_name}")

    # Append new entries to forest
    if new_entries:
        with open(forest_path, 'a') as f:
            for entry in new_entries:
                f.write(json.dumps(entry) + '\n')
        print(f"\nAdded {len(new_entries)} new equations to {forest_path}")
    else:
        print("No new equations to add")

if __name__ == '__main__':
    main()
