# OTOM v1 Paper Structure and Next-Gen Simulator Design

**Date:** 2026-04-23
**Framework:** OTOM v2.0.0-Cambrian-Bind
**Status:** Planning Document

---

## Part 1: Recommended OTOM v1 Paper Flow

### 1. Introduction

**Core Thesis:**
```
Φ = useful structure / realized cost
```

**Cross-domain framework for:**
- Physical systems
- Biological systems
- Cognitive systems

### 2. Universal Efficiency Framework

**Introduce:**
- Corrected thermodynamic cost form (lnN scaling matching Landauer)
- Efficiency form
- Separation of cost, objective, and control

### 3. Peptide-MoE Framework

**Add:**
- Free-energy dynamics
- MoE decomposition
- Filtered Φ_peptide
- Safety ladder

### 4. Reinforced Peptide Dynamics

**Add:**
- RL gate update
- Usefulness
- Entropy regularization
- RL numerical results

### 5. Codon-Level Extension

#### 5.1 Codon Efficiency Functional

```
Φ_codon(c) = (w_ρ·ρ̂_triplet(c) + w_q·q̂_conservation(c) + w_τ·τ̂_translation(c) 
             - w_H·Ĥ_local(c) - w_ε·ε̂_mutation(c)) 
             / (ln 64 + λ ln d(c) + γ τ(c) + C_0)
```

**Variables:**
- w_ρ, w_q, w_τ, w_H, w_ε: positive weights
- ρ̂_triplet: triplet consistency [0,1]
- q̂_conservation: evolutionary conservation [0,1]
- τ̂_translation: translation efficiency [0,1]
- Ĥ_local: local entropy penalty [0,1]
- ε̂_mutation: mutation deviation [0,1]
- λ: degeneracy weight
- d(c): synonymous degeneracy (1-6)
- γ: time cost coefficient
- τ(c): folding delay = 1/v(c)
- C_0: offset constant

#### 5.2 Codon → Amino Acid → Peptide Pipeline

**Show:**
- Synonymous mutation learning
- CDS-level score (Φ_CDS)
- Peptide trajectory coupling

#### 5.3 Ablation Hierarchy

**Revised Conclusion:**
```
Primary: translation speed and local folding delay
Secondary: synonymous-codon structural bias is weak in the current model
```

#### 5.4 Cotranslational Validation

**Use the new subsection:**
- The conclusion survives under cotranslational windows
- Reference: docs/papers/EQUATION_COTRANSLATIONAL_ABLATION_2026-04-23.md

### 6. Cross-Domain OTOM Interpretation

**Connect:**
- Codon mutation selection
- Peptide folding
- Cognitive routing
- Thermodynamic cost

### 7. Formal Appendix

**Point to:**
- Safety ladder Lean files
- RL Lean file
- Codon-peptide consistency Lean file (CodonPeptideConsistency.lean)

---

## Part 2: Next-Gen Simulator Design

### Current Simulator Assessment

**What the current simulator says:**
- Kinetics is clearly real
- Structural bias is still too weak

**Goal:** Build next-gen simulator specifically to give structural bias a real causal path.

### A. Ribosome Pausing

**Current:** Speed only affects timestep

**Upgrade:** Slow codons create pause states:
```
p_pause(c) = f(v(c))
```

**Pauses alter:**
- Local contact formation probability
- Solvent exposure time
- Expert competition duration

**Rationale:** This is the most biologically plausible way for codon choice to matter more.

### B. Nascent-Chain Exposure Window

**Current:** Just a visible prefix

**Upgrade:** Model an exposed tail of length m:
```
E_t = (a_{t-m+1}, ..., a_t)
```

**Only this tail can:**
- Form new contacts
- Bias local expert routing
- Receive codon-conditioned structural perturbations

**Rationale:** Makes local structure formation genuinely cotranslational.

### C. Contact Formation Kinetics

**Add a contact probability term:**
```
P_contact(i,j | t)
```

**Depends on:**
- Current chain length
- Delay window
- Local codon speed
- Current partial structure

**Rationale:** Structural bias can act by shifting contact timing, not just expert logits.

### D. Codon-Conditioned Residence-Time Field

**Current:** Static b_k(c)

**Upgrade:** Dynamic structural bias:
```
b_k(c, t) = b_k(c) · exp(-(t - t_c) / τ(c))
```

**Properties:**
- Local
- Temporary
- Stronger right after translation
- Naturally coupled to delay

**Rationale:** Much more likely to produce a measurable effect.

### E. State Memory

**Current:** Toy system is too forgetful

**Upgrade:** Add short folding memory term:
```
M_{t+1} = α M_t + (1 - α) ΔΘ_t
```

**Let expert advice depend on M_t.**

**Rationale:** Codon-induced pauses can create persistent path differences.

---

## Part 3: Next-Gen Hierarchy

### Simulator v4

**Add:**
- Ribosome pausing
- Exposed tail window
- Dynamic codon residence-time bias

### Simulator v5

**Add:**
- Contact formation kinetics
- Memory of prior partial folding states

### Simulator v6

**Add:**
- Explicit codon-context effects
- Local mRNA structure proxy
- Peptide emergence geometry

**Goal:** This sequence will let you see when structural bias first becomes non-negligible.

---

## Part 4: What to Say in the Current Paper

**OTOM v1 Statement:**
> In the present model, codon effects are dominated by kinetic timing and local folding delay. Direct synonymous structural bias remains weak, even after introducing cotranslational windows. This suggests that stronger codon-to-structure effects likely require richer cotranslational mechanisms such as pausing, exposure gradients, and contact formation kinetics.

**Rationale:** This is honest and strong.

---

## Part 5: Best Recommendation

### For OTOM v1

**Integrate the current result fully:**
- Kinetic dominance is real
- Structural bias is weak in current model
- Cotranslational windows don't change conclusion
- Future work needed for stronger mechanisms

### For OTOM v2 / Next Experiments

**Build next-gen simulator around:**
- Ribosome pausing
- Exposure windows
- Contact kinetics
- Codon-conditioned transient bias

**Rationale:** This is where the structural-bias mechanism has the best chance to become genuinely visible instead of being hand-imposed.

---

## Cross-References

**MATH_MODEL_MAP Entries:**
- 1.2.1: Codon_Fitness_Function
- 1.2.1.1: Phi_CDS_CodonPeptide
- 1.2.1.2: Kinetic_Cost_Term
- 1.2.1.3: Peptide_Dynamics_Codon
- 1.2.1.4: Codon_Translation_Speed

**Documentation:**
- docs/codon_rl_v2_summary.md (v2-v3 results)
- docs/papers/EQUATION_COTRANSLATIONAL_ABLATION_2026-04-23.md (cotranslational validation)

**Lean Modules:**
- 0-Core-Formalism/lean/Semantics/Semantics/CodonOTOM.lean
- 0-Core-Formalism/lean/Semantics/Semantics/CodonPeptideConsistency.lean
- 0-Core-Formalism/lean/Semantics/Semantics/PeptideMoE.lean

**Swarm Assessments:**
- data/swarm_codon_otom_improvement_suggestions.json
- data/swarm_peptide_moe_improvement_suggestions.json
- data/swarm_codon_peptide_coupling_assessment.json
