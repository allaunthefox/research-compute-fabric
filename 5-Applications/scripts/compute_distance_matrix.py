#!/usr/bin/env python3
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial.distance import cosine

# Paths
BASE_PATH = Path('/home/allaun/Documents/Research Stack')
EQUATION_FOREST_PATH = BASE_PATH / 'shared-data/data/equations_forest.jsonl'
DISTANCE_MATRIX_PATH = BASE_PATH / 'shared-data/data/equation_distance_matrix.csv'

# Weights
WEIGHTS = {
    'kernel': 0.35,
    'street': 0.20,
    'bridge': 0.20,
    'typing': 0.10,
    'failure': 0.10,
    'numeric': 0.05
}

def compute_distance(node1, node2):
    """Compute the weighted distance between two nodes."""
    
    # 1. Kernel Distance (Cosine)
    v1 = np.array(node1['foundation_vector'])
    v2 = np.array(node2['foundation_vector'])
    if np.all(v1 == 0) and np.all(v2 == 0):
        d_kernel = 0.0
    elif np.all(v1 == 0) or np.all(v2 == 0):
        d_kernel = 1.0
    else:
        # Cosine distance returns 1 - cosine_similarity
        try:
            d_kernel = cosine(v1, v2)
            if np.isnan(d_kernel): d_kernel = 1.0
        except:
            d_kernel = 1.0

    # 2. Street Distance (Layer)
    d_street = 0.0 if node1['layer'] == node2['layer'] else 1.0

    # 3. Bridge/Shape Distance
    if node1['shape_uuid'] == node2['shape_uuid']:
        d_bridge = 0.0
    elif node1['bind_class'] == node2['bind_class'] and node1['bind_class']:
        d_bridge = 0.5
    else:
        d_bridge = 1.0

    # 4. Typing Distance
    d_typing = 0.0 if node1['typed_status'] == node2['typed_status'] else 1.0

    # 5. Failure Distance (Stubbed to 0 for now as data is sparse)
    d_failure = 0.0

    # 6. Numeric Distance (Genome18 Address)
    addr1 = node1.get('genome18_address', 0)
    addr2 = node2.get('genome18_address', 0)
    # Normalized by max 18-bit address space
    d_numeric = abs(addr1 - addr2) / 262144.0

    # Weighted Sum
    total_dist = (
        WEIGHTS['kernel'] * d_kernel +
        WEIGHTS['street'] * d_street +
        WEIGHTS['bridge'] * d_bridge +
        WEIGHTS['typing'] * d_typing +
        WEIGHTS['failure'] * d_failure +
        WEIGHTS['numeric'] * d_numeric
    )

    return total_dist

def main():
    if not EQUATION_FOREST_PATH.exists():
        print(f"Error: {EQUATION_FOREST_PATH} not found.")
        return

    nodes = []
    with open(EQUATION_FOREST_PATH, 'r') as f:
        for line in f:
            if line.strip():
                nodes.append(json.loads(line))

    n = len(nodes)
    print(f"Computing distance matrix for {n} nodes...")

    # Initialize matrix
    matrix = np.zeros((n, n))

    # Compute pairwise distances (optimized for symmetry)
    for i in range(n):
        if i % 100 == 0:
            print(f"Progress: {i}/{n} nodes...")
        for j in range(i + 1, n):
            dist = compute_distance(nodes[i], nodes[j])
            matrix[i, j] = dist
            matrix[j, i] = dist

    # Create DataFrame for CSV export
    names = [node['model_name'] for node in nodes]
    df = pd.DataFrame(matrix, index=names, columns=names)

    # Save to CSV
    df.to_csv(DISTANCE_MATRIX_PATH)
    print(f"Successfully saved distance matrix to {DISTANCE_MATRIX_PATH}")

if __name__ == '__main__':
    main()
