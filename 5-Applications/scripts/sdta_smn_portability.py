#!/usr/bin/env python3
"""
sdta_smn_portability.py — SMN Portability Simulator for the SDTA Framework

Computes the portability coefficient η = ||Π_D A Π_D†||_F / ||A||_F
for a given constraint matrix, predicting how much of the problem's
structure can be captured in the degenerate (ZIM-Sidon) subspace.

This is a reference implementation of the SDTA portability screen.
See 6-Documentation/docs/specs/sdta_spec.md §4 for the formal definition.

Usage:
    python3 sdta_smn_portability.py                    # default 8x8 test
    python3 sdta_smn_portability.py instance.npy       # load from file
"""

import numpy as np
import sys


def compute_smn(A: np.ndarray) -> float:
    """Semantic mass: average absolute correlation between constraint pairs.
    Proxy for constraint interlocking. High SMN = low portability."""
    n = A.shape[0]
    smn = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            smn += abs(A[i, j] * A[j, i])
            count += 1
    return smn / max(count, 1)


def zim_sidon_rotate(A: np.ndarray, k: int):
    """Rotate A into the k-dimensional Sidon-degenerate subspace.
    Returns: (A_D, A_res, eta) where:
        A_D   = projection onto top-k singular subspace
        A_res = residual = A - A_D
        eta   = portability coefficient = ||A_D||_F / ||A||_F
    """
    n = A.shape[0]
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    k_actual = min(k, n)
    A_D = U[:, :k_actual] @ np.diag(s[:k_actual]) @ Vt[:k_actual, :]
    A_res = A - A_D
    norm_A = np.linalg.norm(A, 'fro')
    norm_AD = np.linalg.norm(A_D, 'fro')
    eta = norm_AD / norm_A if norm_A > 0 else 0.0
    return A_D, A_res, eta


def main():
    if len(sys.argv) < 2:
        # Default test: 8x8 symmetric random matrix
        n = 8
        np.random.seed(42)
        A = np.random.randn(n, n) * 0.5
        A = (A + A.T) / 2
    else:
        A = np.load(sys.argv[1])

    smn = compute_smn(A)
    k = A.shape[0] // 2
    A_D, A_res, eta = zim_sidon_rotate(A, k)

    print(f"Problem size: {A.shape[0]}x{A.shape[0]}")
    print(f"SMN (semantic mass): {smn:.4f}")
    print(f"Portability eta: {eta:.4f}")
    print(f"Original search space: 2^{A.shape[0]} = {2**A.shape[0]}")
    residual_bits = A.shape[0] * (1 - eta)
    print(f"Residual search space: 2^{residual_bits:.2f} = {int(2**residual_bits)}")


if __name__ == "__main__":
    main()
