#!/usr/bin/env python3
"""
Find eigenvectors from the equation database.

Builds a co-occurrence matrix based on domain relationships and computes
the principal eigenvector to identify the most central equations.
"""

import sqlite3
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
import json

DB_PATH = "/dev/shm/physics_equations.db"

def load_equations():
    """Load all equations from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT eq_number, title, domain_id, significance FROM equations ORDER BY eq_number")
    rows = cursor.fetchall()
    conn.close()
    return rows

def build_domain_adjacency(equations):
    """
    Build adjacency matrix based on domain co-occurrence.

    Two equations are connected if they share the same domain.
    """
    n = len(equations)

    # Create domain to equations mapping
    domain_to_eqs = {}
    for i, (_, _, domain_id, _) in enumerate(equations):
        if domain_id not in domain_to_eqs:
            domain_to_eqs[domain_id] = []
        domain_to_eqs[domain_id].append(i)

    # Build sparse adjacency matrix
    row_indices = []
    col_indices = []
    data = []

    # Connect equations in same domain
    for domain_id, eq_indices in domain_to_eqs.items():
        for i in eq_indices:
            for j in eq_indices:
                if i != j:
                    row_indices.append(i)
                    col_indices.append(j)
                    data.append(1.0 / len(eq_indices))  # Normalize by domain size

    # Create sparse matrix
    adj = csr_matrix((data, (row_indices, col_indices)), shape=(n, n))
    return adj

def find_principal_eigenvector(adj_matrix, n_eigenvectors=5):
    """Find the principal eigenvectors of the adjacency matrix."""
    # Find largest eigenvalues and corresponding eigenvectors
    eigenvalues, eigenvectors = eigsh(adj_matrix, k=n_eigenvectors, which='LM')

    return eigenvalues, eigenvectors

def main():
    print("=" * 60)
    print("Finding Eigenvectors from Equation Database")
    print("=" * 60)

    # Load equations
    print("\n[1/4] Loading equations...")
    equations = load_equations()
    n_eqs = len(equations)
    print(f"      → {n_eqs} equations loaded")

    # Build adjacency matrix
    print("\n[2/4] Building domain adjacency matrix...")
    adj = build_domain_adjacency(equations)
    print(f"      → Matrix shape: {adj.shape}")
    print(f"      → Non-zero entries: {adj.nnz}")

    # Find eigenvectors
    print("\n[3/4] Computing principal eigenvectors...")
    eigenvalues, eigenvectors = find_principal_eigenvector(adj, n_eigenvectors=5)
    print(f"      → Found {len(eigenvalues)} eigenvalues")

    # Display results
    print("\n[4/4] Results:")
    print("-" * 60)

    for i, (eval, evec) in enumerate(zip(eigenvalues, eigenvectors.T)):
        print(f"\nEigenvector #{i+1} (eigenvalue: {eval:.6f})")
        print("-" * 60)

        # Get top 10 equations by eigenvector magnitude
        magnitudes = np.abs(evec)
        top_indices = np.argsort(magnitudes)[-10:][::-1]

        print("Top 10 equations by eigenvector magnitude:")
        for rank, idx in enumerate(top_indices, 1):
            eq_num, title, domain_id, significance = equations[idx]
            mag = magnitudes[idx]
            print(f"  {rank:2d}. Eq {eq_num:4d}: {title[:50]} (|v|={mag:.6f})")

    # Save results to JSON
    print("\n" + "=" * 60)
    print("Saving results to equation_eigenvectors.json...")

    results = {
        'n_equations': n_eqs,
        'eigenvalues': eigenvalues.tolist(),
        'eigenvectors': eigenvectors.T.tolist(),
        'equations': [
            {
                'eq_number': eq[0],
                'title': eq[1],
                'domain_id': eq[2],
                'significance': eq[3][:200]
            }
            for eq in equations
        ]
    }

    with open('equation_eigenvectors.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("Done.")

if __name__ == "__main__":
    main()
