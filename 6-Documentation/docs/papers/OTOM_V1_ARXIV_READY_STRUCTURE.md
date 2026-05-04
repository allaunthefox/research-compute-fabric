# OTOM v1 — Full Section Order (ArXiv-Ready)

**Date:** 2026-04-23
**Framework:** OTOM v2.0.0-Cambrian-Bind
**Status:** ArXiv-Ready Paper Structure

---

## Structured for:

- Clarity to reviewers
- Mathematical rigor
- Narrative progression from physics → biology → cognition

---

## 0. Abstract

**State the full claim cleanly:**
```
Φ = useful structure / realized cost
```

**Key points:**
- Unified efficiency framework across domains
- Corrected thermodynamic grounding (Landauer-consistent)
- Peptide + codon + RL integration
- Main result: kinetics dominates codon effects

---

## 1. Introduction

**Goals:**
- Define the problem: fragmented models across domains
- Motivate unification

**Include:**
- Inefficiency of isolated models (physics / biology / cognition)
- Need for a universal efficiency metric

**End with:**
> OTOM models systems as efficiency-optimized transformations under real physical cost.

---

## 2. Universal Efficiency Framework

### 2.1 Cost (Corrected)

Insert your fixed form:
```
Φ_cost = Σ_i w_i ln N_i
```

### 2.2 Efficiency Form
```
Φ_eff = quality / cost
```

### 2.3 Temporal Cost Extension (NEW — from your results)
```
Φ_cost = Σ_i (w_i ln N_i + γ τ_i)
```

**This is where you insert the key statement:**
> Time is a thermodynamic cost of information realization

---

## 3. Dynamical Systems and Separation of Concerns

**This is critical for rigor.**

### 3.1 Dynamics
```
dΘ/dt = -∇F + ξ_t
```

### 3.2 Evaluation
```
Φ = coherence / (F + C_0)
```

### 3.3 Control (MoE / RL)

**Make explicit:**
- Dynamics ≠ evaluation ≠ control

**This prevents "teleporting peptides" criticism.**

---

## 4. Peptide Folding as an MoE System

### 4.1 Expert Decomposition
- Helix
- Sheet
- Loop

### 4.2 Gating
```
ΔΘ_t = Σ_k g_k(P_t) Advice_k
```

### 4.3 Thermodynamic Consistency

**Tie back to:**
- Free energy
- Entropy
- Noise

---

## 5. Reinforced MoE Peptide Dynamics

### 5.1 Reward
```
R = ΔΦ_peptide
```

### 5.2 Update Rule
```
θ_{t+1} = θ_t + α R · usefulness
```

### 5.3 Numerical Results

**Include your RL plots**

**Describe:**
- Exploration → specialization
- Entropy reduction

---

## 6. Codon-Level Extension

**This is where your recent work goes.**

### 6.1 Codon Efficiency Functional
```
Φ_codon(c) = (signal - penalty) / (ln 64 + λ ln d(c) + γ τ(c) + C_0)
```

**Explain:**
- Degeneracy
- Translation speed
- Mutation penalty

### 6.2 Codon → Amino Acid → Peptide Pipeline

**Explain the pipeline:**
```
codon → amino acid → expert field → peptide trajectory
```

**Key idea:**
> Synonymous codons affect how, not what

### 6.3 Mutation as RL
```
ΔΦ > 0 ⇒ selected
```

**Tie to:**
- Evolutionary selection
- Local gradient ascent

---

## 7. Ablation Study

### 7.1 Baseline vs Kinetic vs Bias

**State the hierarchy:**
```
Primary: translation speed + folding delay
Secondary: structural bias (weak)
```

### 7.2 Cotranslational Extension

**Insert your v3 subsection here.**

**This is important structurally:**
- Shows robustness
- Defends against reviewer objections

**Reference:** docs/papers/EQUATION_COTRANSLATIONAL_ABLATION_2026-04-23.md

### 7.3 Final Result Statement

> Codon effects are primarily kinetic in the current model

---

## 8. Cross-Domain OTOM Interpretation

**This is where the paper becomes big.**

**Map:**

| Domain | Mechanism |
|--------|-----------|
| Physics | Energy minimization |
| Biology | Folding + evolution |
| Cognition | Attention routing |

**Unify them:**
> All are efficiency-optimized transformations under cost constraints

---

## 9. Limitations

**Be explicit:**
- Toy peptide system
- Simplified codon table
- Weak structural bias
- No ribosome model

**This builds trust.**

---

## 10. Future Work

**Point directly to your next-gen simulator:**
- Ribosome pausing
- Exposure windows
- Contact kinetics
- Dynamic codon bias

**Reference:** docs/OTOM_V1_PAPER_STRUCTURE_AND_NEXT_GEN_SIMULATOR.md

---

## 11. Conclusion

**Restate clearly:**
> OTOM unifies dynamics, information, and learning under a single efficiency principle

**And:**
> Biological codon effects emerge primarily through kinetics

---

## Appendices

### A. Lean Formalization
- Safety ladder
- RL invariants
- Codon-peptide consistency

### B. Simulation Details
- RL setup
- Parameter tables
- Reproducibility

---

## 🔥 Why This Structure Works

**It creates a clean arc:**
1. Physics foundation
2. Dynamic system rigor
3. Peptide system
4. Learning system
5. Genetics integration
6. Experimental validation
7. Universal interpretation

---

## Cross-References

**MATH_MODEL_MAP Entries:**
- Row 0: Phi_Universal (corrected cost form)
- Row 1.2.1: Codon_Fitness_Function
- Row 1.2.1.1: Phi_CDS_CodonPeptide
- Row 1.2.1.2: Kinetic_Cost_Term (temporal cost extension)
- Row 1.2.1.3: Peptide_Dynamics_Codon
- Row 1.2.1.4: Codon_Translation_Speed

**Documentation:**
- docs/codon_rl_v2_summary.md (v2-v3 results)
- docs/papers/EQUATION_COTRANSLATIONAL_ABLATION_2026-04-23.md (cotranslational validation)
- docs/OTOM_V1_PAPER_STRUCTURE_AND_NEXT_GEN_SIMULATOR.md (next-gen simulator design)

**Lean Modules:**
- 0-Core-Formalism/lean/Semantics/Semantics/CodonOTOM.lean
- 0-Core-Formalism/lean/Semantics/Semantics/CodonPeptideConsistency.lean
- 0-Core-Formalism/lean/Semantics/Semantics/PeptideMoE.lean
