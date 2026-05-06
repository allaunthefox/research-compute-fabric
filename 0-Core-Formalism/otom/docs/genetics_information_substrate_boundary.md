---
project: OTOM
domain: axis-04-formalization
type: BoundaryRecord
settlement: FORMING
authority: registry
route_signature: otom/axis-04-formalization/boundaryrecord/genetics-information-substrate/v0
claim_state: BEAUTIFUL_PROVISIONAL
source_audit: uploaded-codemap-2026-05-05
---

# Genetics Information Substrate Boundary

Status: FORMING — claim-state hygiene document
Authority: audit receipt from `MATH_MODEL_MAP.tsv` + `0-Core-Formalism/lean/Semantics` tree
Date: 2026-05-04

---

## Purpose

Classify every genetics-connected model in the Research Stack into one of four buckets so that:
- no model is promoted on false pretenses
- ghost entries are visible and demotable
- misfiled artifacts are relocated
- canonical plumb has a clear perimeter

---

## The Four Buckets

| Bucket | Meaning | Promotion Rule |
|---|---|---|
| `CANONICAL_PLUMBED` | Compiled Lean or running real-data code exists and is reachable from `lake build` or a Python entry point | May be used as dependency, cited in proofs, or connected to production pipelines |
| `REGISTRY_ONLY` | Equation and purpose statement exist in `MATH_MODEL_MAP.tsv`, but no executable path found | May be referenced in docs and roadmaps; must be flagged for implementation if promoted |
| `GHOST_ENTRY` | Marked `✅` in registry but no Lean module, Python script, or data pipeline found after exhaustive search | Must be demoted to `⛔` or assigned an owner and deadline before any promotion |
| `MISFILED` | Physically located near genetics but has no biological sequence or population-information connection | Must be relocated to correct domain directory |
| `ASPIRATIONAL_MIXTURE_PRIMITIVE` | Taxonomy concept without proof/data path | BEAUTIFUL_PROVISIONAL only |

---

## CANONICAL_PLUMBED

### Lean Formalizations (compiled, in `lake build` tree)

| Module | Path | Genetics Layer | Information-Holding Mechanism |
|---|---|---|---|
| **GeneticCode.lean** | `Semantics/GeneticCode.lean` | B — Codon/Translation | Full NCBI Table 1: 64 codon states → 20 amino acids + stop. Codon degeneracy analysis. Start/stop identification. |
| **CodonOTOM.lean** | `Semantics/CodonOTOM.lean` | B — Codon/Translation | Codon efficiency functional `Φ_codon`, mutation `δΦ`, selection condition `beneficialMutation`. |
| **PeptideMoE.lean** | `Semantics/PeptideMoE.lean` | C — Protein/Peptide | `PeptideState` with Ramachandran (φ,ψ), internal energy, conformational entropy. MoE expert gating. |
| **GenomicCompression.lean** | `Semantics/GenomicCompression.lean` + submodules | L — Compression | `phiGenomic`, `compressWindow`, Q16_16 fixed-point. Theorems + `NonDriftProof`. |
| **SyntheticGeneticCoding.lean** | `Semantics/SyntheticGeneticCoding.lean` | M — Synthetic Alphabets | Three-layer type system: `CodingQ` (Q0_64), `BioParamQ` (Q16_16), `BioCodingProjection`. |
| **GeneticGroundUp.lean** | `Semantics/GeneticGroundUp.lean` | N — GCCL-Native / M | 6-state nucleotide (A/T/C/G/U/X) with exact `ofRatio`/`ofInt`/`neg` constants. No `ofFloat` — passes Lifeguard Rule 4. Quantum nucleotide encoding. |
| **HachimojiPipeline.lean** | `Semantics/HachimojiPipeline.lean` | M — Synthetic Alphabets | 8-symbol DNA/RNA alphabet analog (hachimoji). |
| **CodonPeptideConsistency.lean** | `Semantics/CodonPeptideConsistency.lean` | B→C bridge | Formal bridge between codon layer and peptide layer consistency. |

### Real-Data Scripts

| Script | Path | Genetics Layer | Information-Holding Mechanism |
|---|---|---|---|
| **Allelica.py** | `3-Mathematical-Models/genetics/Allelica/Allelica.py` | G — Population / A | Hardy-Weinberg genotype frequencies on gnomAD real data. Allele frequency → genotype frequency distribution. |
| **populations.csv** | `3-Mathematical-Models/genetics/Allelica/populations.csv` | G — Population | Real allele frequencies for 10 genes across 4 populations. |

---

## REGISTRY_ONLY

These exist in `MATH_MODEL_MAP.tsv` with equations and purpose statements but **no executable path** was found.

| Model | Equation | Purpose | Missing Implementation |
|---|---|---|---|
| **Hardy-Weinberg** | `p² + 2pq + q² = 1` | Genetic state closure condition | Lean theorem exists in `Allelica.py` context but not as standalone formal module |
| **Wright-Fisher Drift** | `Var(Δp) = p(1-p)/N` | Stochastic genetic sampling invariant | No Lean module; no simulation script |
| **Fisher's Fundamental Theorem** | `dM/dt = Var_A(w)` | Population fitness increase identity | No implementation found |
| **Price Equation** | `Δz̄ = cov(w,z)/w̄ + E[wΔz]/w̄` | General law of selection and transmission | No implementation found |
| **Central Dogma ODE** | `ṁ = α_m - δ_m·m` | Cellular state production drift | No implementation found |
| **RNA Folding ΔG** | `ΔG = Σ E_stack + E_loop` | Thermodynamic information topology | No implementation found |
| **Waddington Potential** | `V(x) = x⁴/4 - bx²/2 - ax` | Epigenetic landscape bifurcation | No implementation found |
| **Gierer-Meinhardt** | Activator-inhibitor PDEs | Morphogenetic pattern formation | No implementation found |
| **Shannon Entropy (Genomic)** | `H(X) = -Σ p(x_i) log₂ p(x_i)` | Per-position sequence information | Referenced in `BioRxivFormalization.lean` but not as standalone genetics module |
| **Per-Position Entropy** | `H(x) = -Σ P(c\|x) log₂ P(c\|x)` | Information at each locus | Referenced in `BioRxivFormalization.lean` |
| **Jensen-Shannon Divergence** | `JSD(P\|Q) = ½ D_KL(P\|M) + ½ D_KL(Q\|M)` | Population/sequence differentiation | Referenced in `BioRxivFormalization.lean` |
| **Jukes-Cantor Distance** | `d = -(3/4) ln(1 - 4p/3)` | Phylogenetic sequence divergence | Referenced in `BioRxivFormalization.lean` |
| **ANI** | `ANI = (percent_identity × coverage)/100` | Genome similarity metric | Referenced in `BioRxivFormalization.lean` |
| **AAI** | `AAI = average(sequence_identity)` | Protein similarity metric | Referenced in `BioRxivFormalization.lean` |
| **Mutation Rate (μ)** | `μ = N_mutations / L_genome` | Normalized mutation count | No standalone module; only registry entry |
| **Novel Mutation Count** | `N_novel = L_genome × (1 - ANI/100)` | Strain variant discovery | No standalone module |
| **Gibbs Free Energy** | `ΔG = ΔH - TΔS` | Equilibrium state function | No standalone module |
| **Fitness-Entropy Tradeoff** | `f = f_max - α·H` | Sequence evolvability constraint | No standalone module |

---

## GHOST_ENTRY

Marked `✅` in `MATH_MODEL_MAP.tsv` but **no implementation found** after exhaustive search of:
- `0-Core-Formalism/lean/Semantics/Semantics/` (417 .lean files)
- `0-Core-Formalism/lean/Semantics/Core/` (4 .lean files)
- `0-Core-Formalism/lean/Semantics/ExtensionScaffold/` (subdirs)
- `3-Mathematical-Models/` tree
- `2-Search-Space/` tree

| Model | Registry Claim | Ghost Status |
|---|---|---|
| **Quasispecies Equation** | `ẋ_i = (w_i q_i - w̄)x_i + Σ w_ij x_j` — molecular evolution error threshold | **GHOST** — no Lean, no Python, no spec beyond registry |
| **Replicator Equation** | `ẋ_i = x_i(f_i - f̄)` — evolutionary game theory | **GHOST** — no implementation found |
| **Neutral Theory (Kimura)** | `k = v` — genomic drift baseline | **GHOST** — no implementation found |
| **Masked Language Modeling Loss** | `L = -Σ log P(x \| x̃)` — could apply to DNA sequences | **GHOST** — no genetics-specific implementation |
| **pTM Template Modeling Score** | `TM-score` for protein structure | **GHOST** — only generic structural biology mention |
| **Free Energy Principle** | `F = E_q[ln q - ln p]` — variational self-organization | **GHOST** — generic information theory, no genetics bridge |
| **Tetz's Law** | `t_death ← q(t) ≥ q_max` — pangenome lifespan | **GHOST** — no implementation found |

**Action required:** Demote to `⛔` or assign owner + deadline.

---

## MISFILED

| Artifact | Current Location | Actual Domain | Why Misfiled |
|---|---|---|---|
| **parametric-learn** | `3-Mathematical-Models/genetics/parametric-learn/` | Geometry / Machine Learning | Three.js/TensorFlow.js parametric surface fitting demo. No biological sequence, no population data, no genetic information. Surfaces: Klein bottle, torus, Möbius strip, sphere, ripple. |

**Action required:** Move to `3-Mathematical-Models/manifold_compression/` or `5-Applications/visualization/`.

---

## Coverage Map: GCCL Taxonomy vs. Reality

The GCCL taxonomy (`GCCL_GENETIC_INFORMATION_MIXTURE_PRIMITIVES.md`) lists 14 primitive groups A–N.

| Group | Name | Coverage | Canonical Modules |
|---|---|---|---|
| A | Molecular Alphabets | **Strong** | `GeneticCode.lean`, `GeneticGroundUp.lean`, `SyntheticGeneticCoding.lean` |
| B | Codon/Translation | **Strong** | `GeneticCode.lean`, `CodonOTOM.lean`, `CodonPeptideConsistency.lean` |
| C | Protein/Peptide | **Strong** | `PeptideMoE.lean` |
| D | Ambiguity/Degeneracy | **Weak** | Partial in `GeneticCode.lean` (IUPAC mentions) but no formal ambiguity algebra |
| E | Sequence File/Quality | **None** | No FASTA/FASTQ/Phred parser |
| F | Alignment/Assembly/Graph | **None** | No CIGAR, BWT, de Bruijn, or pangenome graph module |
| G | Variant/Haplotype/Population | **Partial** | `Allelica.py` (Hardy-Weinberg only); no VCF, BCF, or GWAS model |
| H | Annotation/Feature | **None** | No GFF/GTF/BED parser or gene model formalization |
| I | Epigenetic/Regulatory | **None** | Explicit TODO in `GenomicCompression.lean`: "Extract formal lemmas from 2504.03733 epigenetic analysis" |
| J | Structural/3D Genome | **None** | No TAD, Hi-C, or contact map module |
| K | Expression/Multi-omics | **None** | No RNA-seq, ATAC-seq, ChIP-seq, or proteomics module |
| L | Compression/Indexing | **Strong** | `GenomicCompression.lean` with Types, Components, Field, Theorems, `NonDriftProof` |
| M | Synthetic/Expanded Alphabets | **Strong** | `SyntheticGeneticCoding.lean`, `HachimojiPipeline.lean`, `GeneticGroundUp.lean` |
| N | GCCL-Native Model-Genome | **Strong** | `GeneBytecodeJIT.lean`, `GeneticGroundUp.lean` |

**Summary:** 5 of 14 groups are strongly covered (A, B, C, L, M, N). 6 groups have zero formalization (E, F, H, I, J, K). 2 groups are partial (D, G).

---

## Promotion Gate

Any genetics model may be promoted from `REGISTRY_ONLY` → `CANONICAL_PLUMBED` only if it passes:

```text
MassNumber gate:
  admissible_reduction = information_capacity_gain
  residual_risk        = implementation_complexity + data_dependency + biological_equivalence_claim_risk
  threshold            = 0.2 (generous for foundational models)
  depth                ≤ 2 (no deep abstraction recursion)
  boundCheck           = true (must declare data source and validation plan)
```

Warden rule: If a model claims biological equivalence (e.g., "GCCL is DNA"), it must emit `UnderversePacket.biological_equivalence_without_receipt` and be blocked.

---

## Next Actions

1. **Relocate `parametric-learn`** from `genetics/` to correct domain.
2. **Demote ghost entries** to `⛔` or assign owners.
3. **Pick one REGISTRY_ONLY model to implement:**
   - `Jukes-Cantor` + phylogenetic tree inference (medium complexity, clear mathematical path)
   - `Wright-Fisher` drift simulation (low complexity, connects to existing `Allelica.py`)
   - `RNA Folding ΔG` + ViennaRNA-style Nussinov (medium complexity, well-documented algorithms)
4. **Fill the epigenetics gap** — start with the paper reference already in `GenomicCompression.lean` TODO: 2504.03733 (AI for Epigenetic Sequence Analysis → Methylation pattern compression).

---

## Audit Trail

- Audit performed: 2026-05-04
- Tools used: `rg` over 2633-row `MATH_MODEL_MAP.tsv`, `find` over Lean tree (440+ .lean files), manual inspection of `genetics/` directory
- Auditor: Cascade (Research Stack pair programmer)
- Receipt hash: genetics-audit-20260504-v1
