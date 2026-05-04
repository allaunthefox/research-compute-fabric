#!/usr/bin/env python3
import json
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from pathlib import Path

# Paths
BASE_PATH = Path('/home/allaun/Documents/Research Stack')
DISTANCE_MATRIX_PATH = BASE_PATH / 'shared-data/data/equation_distance_matrix.csv'
SUPERNODES_PATH = BASE_PATH / 'shared-data/data/supernodes.json'

def main():
    if not DISTANCE_MATRIX_PATH.exists():
        print(f"Error: {DISTANCE_MATRIX_PATH} not found.")
        return

    print(f"Loading distance matrix from {DISTANCE_MATRIX_PATH}...")
    df = pd.read_csv(DISTANCE_MATRIX_PATH, index_col=0)
    matrix = df.values
    names = df.index.tolist()

    # Clustering into 40 supernodes
    n_clusters = 40
    print(f"Clustering {len(names)} nodes into {n_clusters} supernodes...")
    
    clustering = AgglomerativeClustering(
        n_clusters=n_clusters, 
        metric='precomputed', 
        linkage='average'
    )
    labels = clustering.fit_predict(matrix)

    # Group nodes by cluster
    clusters = {}
    for i, label in enumerate(labels):
        label = int(label)
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(names[i])

    # Find representative for each cluster (the one with min avg distance to others in cluster)
    supernodes = []
    for label, members in clusters.items():
        member_indices = [names.index(m) for m in members]
        
        if len(members) == 1:
            representative = members[0]
        else:
            # Sub-matrix for this cluster
            sub_matrix = matrix[np.ix_(member_indices, member_indices)]
            avg_distances = np.mean(sub_matrix, axis=1)
            best_idx = np.argmin(avg_distances)
            representative = members[best_idx]

        supernodes.append({
            "id": label,
            "representative": representative,
            "member_count": len(members),
            "members": members
        })

    # Sort supernodes by member count (descending)
    supernodes.sort(key=lambda x: x['member_count'], reverse=True)

    # Save to JSON
    with open(SUPERNODES_PATH, 'w') as f:
        json.dump(supernodes, f, indent=2)

    print(f"Successfully saved {len(supernodes)} supernodes to {SUPERNODES_PATH}")
    
    # Print top 5 clusters
    for i in range(min(5, len(supernodes))):
        s = supernodes[i]
        print(f"Supernode {s['id']}: {s['representative']} ({s['member_count']} members)")

if __name__ == '__main__':
    main()
