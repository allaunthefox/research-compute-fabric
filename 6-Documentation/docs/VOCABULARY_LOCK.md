# Vocabulary Lock: Sovereign Stack / Bodega Kernel

**Status:** FIXED  
**Date:** 2026-05-02  
**Authority:** Research Stack Architect (via Agentic Coder)

## 1. Core Definitions

| Term | Definition | Lean Reference |
| :--- | :--- | :--- |
| **Equation Forest** | A directed acyclic graph (DAG) of mathematical models and their dependencies. | `Semantics.Forest` |
| **F01–F12** | 12 foundation kernel signatures (e.g., Shannon, Carnot, Landauer). | `Semantics.Foundations` |
| **DIAT** | Dynamic Integer-Address Transform (shell coordinate transform). | `Semantics.DIAT` |
| **S3C** | Shell/Topological Codec for energy cell quantization. | `Semantics.S3C` |
| **AVMR** | Adaptive Vector Manifest Roll-up (hierarchical summary). | `Semantics.AVMR` |
| **NUVMAP** | Non-Uniform Variable Mapping (2D spectral projection). | `Semantics.NUVMATH` |
| **FNWH** | Formal Non-Wave Harmonic (the underlying framework). | `Semantics.FNWH` |
| **PIST** | Perfectly Imperfect Square Theory (witness/audit surface). | `Semantics.PIST` |
| **FAMM** | Frustration-Aware Manifold Management (memory/route manager). | `Semantics.FAMM` |
| **Genome18** | 18-bit address space (6 bins × 3 bits). | `Semantics.Genome18` |

## 2. Interface Signatures

### NUVMAP Encoding
- **Input:** Spectral state vector $A = [a_1, a_2, \dots, a_n]$
- **U-Coordinate:** $u = f(t) = t \times 1000$ (Distance-based albedo)
- **V-Coordinate:** $v = g(n) = n$ (Spectral index)
- **Projection:** $P = Q^T \cdot A$
- **Failure Mode:** Projection error exceeds $\epsilon_{tol}$ in `NUVMATH.lean`.

### Witness format (PIST)
- **Witness:** `{ event_id, proof_hash, signature, energy_cell }`
- **Verification:** `attest(witness) -> bool`

## 3. Implementation Constraints
- **Q16.16 Fixed Point:** All arithmetic in Lean (`Semantics.Q16_16`) and Verilog (`NIICore.v`) must match bit-exactly.
- **S3C Shells:** Energy cells must be quantized to `n^2 + m` integer shells before routing.
- **TREE(3) Bound:** All recursive lookups in `BHOCS` must carry a witness of finiteness.

---
*Signed by Antigravity on behalf of the User.*
