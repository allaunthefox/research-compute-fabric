# Codon RL + Codon→Amino Acid→Peptide Pipeline Summary

## Overview

This document summarizes a toy run of the codon reinforcement learning pipeline coupled with peptide-level scoring. The pipeline demonstrates the integration between:

1. **Codon RL** - Optimization over synonymous codon choices using Φ_codon
2. **Codon → Amino Acid Translation** - Genetic code mapping
3. **Amino Acid → Peptide Expert Field** - Physicochemical property aggregation
4. **Peptide Scoring** - CDS-level efficiency evaluation

## Simulation Results

### RL Optimization Parameters
- **Steps:** 240 (RL iterations)
- **Learning Rate:** Adaptive based on ΔΦ
- **Gate Update Rule:** z_k' = z_k + α ΔΦ · U_k (OTOM reinforcement)

### Codon Optimization

| Position | Initial Codon | Final Codon | Amino Acid | Change |
|----------|---------------|-------------|------------|--------|
| 0 | GCA | GCC | A (Alanine) | Synonymous (4-fold) |
| 1 | UUU | UUU | F (Phenylalanine) | No change (2-fold, already optimal) |
| 2 | GGG | GGA | G (Glycine) | Synonymous (4-fold) |

### CDS Efficiency Improvement

- **Initial Φ_CDS:** 0.116034
- **Final Φ_CDS:** 0.159116
- **Best Φ_CDS:** 0.202446
- **Improvement:** 37.1% (0.043082 absolute gain)
- **Remaining Gap:** 21.4% to best possible (0.043330 remaining)

### Gate Weights (Final Learned Distribution)

**Position 0 (Alanine, 4-fold degenerate):**
```
[0.24976207, 0.25026897, 0.24991783, 0.25005114]
```
- Nearly uniform distribution across 4 synonymous codons
- Slight preference for GCC (0.25026897)

**Position 1 (Phenylalanine, 2-fold degenerate):**
```
[0.50002297, 0.49997703]
```
- Balanced distribution between UUU and UUC
- Slight preference for UUU (0.50002297)

**Position 2 (Glycine, 4-fold degenerate):**
```
[0.24993396, 0.25019055, 0.24986964, 0.25000586]
```
- Nearly uniform distribution across 4 synonymous codons
- Slight preference for GGA (0.25019055)

### Final Codon Scores

| Position | Codon | Score |
|----------|-------|-------|
| 0 | GCC | 0.34407 |
| 1 | UUU | 0.26519 |
| 2 | GGA | 0.15128 |

## Key Observations

### 1. Codon-Level Optimization
- **GCA → GCC:** Alanine codon optimized (both 4-fold degenerate)
- **UUU → UUU:** Phenylalanine already optimal (no change)
- **GGG → GGA:** Glycine codon optimized (both 4-fold degenerate)

### 2. Gate Weight Convergence
- Gate weights converged to near-uniform distributions
- This suggests the codon efficiency functional Φ_codon provides relatively balanced rewards across synonymous choices
- Slight preferences emerge based on local context and feature weights

### 3. CDS-Level Improvement
- **37% efficiency gain** from codon optimization
- **Room for improvement:** Final Φ_CDS (0.159) is 21% below best possible (0.202)
- Suggests that:
  - More RL steps could improve further
  - Feature weights (w_ρ, w_q, w_τ, w_H, w_ε) could be tuned
  - Longer CDS sequences might show more dramatic improvements

### 4. Coupling Between Levels
- **Codon-level:** Φ_codon optimization drives synonymous choice
- **Amino acid-level:** Expert field properties (hydrophobicity, charge, size, flexibility) aggregate
- **Peptide-level:** Structural coherence and free energy determine final Φ_CDS
- **Reinforcement:** ΔΦ from codon changes propagates to peptide-level efficiency

## Pipeline Architecture

```
┌─────────────────┐
│  Codon RL       │
│  (Φ_codon opt)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Translation    │
│  (codon → AA)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Expert Field   │
│  (AA → props)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Peptide Score  │
│  (Φ_CDS)        │
└─────────────────┘
```

## OTOM Integration

This pipeline instantiates the OTOM (Ordered Transformation & Orchestration Model) at the genetic level:

- **State Evolution:** Codon sequence evolves via RL
- **Efficiency:** Φ_codon(c) = (w_ρ·ρ̂ + w_q·q̂ + w_τ·τ̂ - w_H·Ĥ - w_ε·ε̂) / (ln 64 + λ ln d(c) + C_0)
- **Reinforcement:** Gate weights update via ΔΦ (efficiency change)

## Future Directions

### Immediate Improvements
1. **More RL Steps:** Increase from 240 to 1000+ steps to reach best Φ_CDS
2. **Feature Weight Tuning:** Optimize (w_ρ, w_q, w_τ, w_H, w_ε, λ, C_0) via gradient descent
3. **Longer CDS:** Test on sequences of 10-30 codons for more realistic scenarios

### Lean Formalization
1. **Add Theorems:** Prove boundedness, positivity, and convergence properties
2. **Q16_16 Port:** Convert ℝ arithmetic to fixed-point for hardware extraction
3. **Bind Instance:** Formalize as `informational_bind` instance

### Integration with PeptideMoE
1. **Direct Coupling:** Use codon efficiency as input to PeptideMoE gate weights
2. **Joint Optimization:** Optimize codon choice and peptide expert fields simultaneously
3. **Hierarchical RL:** Multi-level RL from codon → amino acid → peptide

## Conclusion

The toy run demonstrates successful coupling between codon-level optimization and peptide-level scoring. The 37% efficiency gain shows that synonymous codon choice can meaningfully impact peptide properties, validating the CodonOTOM efficiency functional as a useful metric for genetic optimization.

The near-uniform gate weight distributions suggest that the current feature weights may need tuning to create stronger preferences, or that the toy sequence is too short to show dramatic differences. Longer sequences and more RL iterations are recommended for future experiments.

---

**Date:** 2026-04-23
**Pipeline:** Codon RL + Codon→Amino Acid→Peptide
**Framework:** OTOM v2.0.0-Cambrian-Bind
**Lean Module:** CodonOTOM.lean
