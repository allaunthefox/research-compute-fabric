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

## Purpose

This boundary record separates genuinely plumbed genetics-information models from
registry-only, ghost, aspirational, and misfiled entries.

The immediate goal is claim-state hygiene:

```text
Do not claim the genetics layer is fully implemented when only part of it has
compiled Lean, running data code, or executable evidence receipts.
```

## Canonical boundary statement

```text
The Research Stack currently has a partial but real genetics-information
substrate: compiled codon/peptide/compression formalizations, one real-data
population-genetics script, and a larger registry of unplumbed or ghost model
entries. Claims about genetics information capacity must cite the plumbed
substrate or remain BEAUTIFUL_PROVISIONAL.
```

## Classification buckets

| Bucket | Meaning | Promotion rule |
|---|---|---|
| `CANONICAL_PLUMBED` | compiled Lean module or running real-data script | may support bounded claims |
| `REGISTRY_ONLY` | equation/model exists in registry but has no executable path | may support roadmap claims only |
| `GHOST_ENTRY` | marked complete/available but no corresponding implementation found | must be demoted or implemented |
| `MISFILED` | present near genetics but not genetics-relevant | relocate or mark out-of-scope |
| `ASPIRATIONAL_MIXTURE_PRIMITIVE` | taxonomy concept without proof/data path | BEAUTIFUL_PROVISIONAL only |

## Plumbed genetics substrate

### Lean / formalized substrate

The audit identifies the following as the strongest plumbed genetics-connected
information models:

| Module | Information-holding mechanism | Genetics tie | Status |
|---|---|---|---|
| `GeneticCode.lean` | NCBI Table 1 codon-to-amino-acid map; 64 codon states plus outputs | canonical translation and codon degeneracy | `CANONICAL_PLUMBED` |
| `CodonOTOM.lean` | codon efficiency functional, mutation delta, selection condition | codon usage bias and mutation-selection balance | `CANONICAL_PLUMBED` |
| `PeptideMoE.lean` | peptide state, Ramachandran coordinates, internal energy, entropy | conformational search as information geometry | `CANONICAL_PLUMBED` |
| `GenomicCompression.lean` | compression windows, phiGenomic, Q16_16 arithmetic | formal sequence-compression substrate | `CANONICAL_PLUMBED` |
| `SyntheticGeneticCoding.lean` | coding and biological parameter projections | normalized biological parameter projection | `CANONICAL_PLUMBED` |
| `GeneticGroundUp.lean` | nucleotide-state encoding, expression probability, binding energy, fold angle | synthetic biology / nucleotide-state model | `CANONICAL_PLUMBED` |
| `HachimojiPipeline.lean` | 8-symbol expanded genetic alphabet analog | expanded DNA/RNA coding regime | `CANONICAL_PLUMBED` |

### Running data substrate

| File | Information-holding mechanism | Genetics tie | Status |
|---|---|---|---|
| `Allelica.py` | Hardy-Weinberg genotype-frequency model over real gnomAD data | p² + 2pq + q² = 1 applied to real allele/genotype data | `CANONICAL_PLUMBED` |

## Registry-only model surface

These models may be scientifically relevant but should not be promoted as
implemented until a Lean module, Python script, test fixture, or receipt path
exists.

| Model family | Examples | Status |
|---|---|---|
| Population genetics registry | Wright-Fisher drift, Fisher fundamental theorem, Price equation | `REGISTRY_ONLY` |
| Sequence information registry | Shannon entropy, per-position entropy, Jensen-Shannon divergence, Jukes-Cantor distance, ANI/AAI, mutation rate, novel mutation count | `REGISTRY_ONLY` unless connected to compiled module |
| Thermodynamic/folding registry | RNA folding delta-G, Gibbs free energy, fitness-entropy tradeoff, Waddington potential | `REGISTRY_ONLY` |
| Cellular/regulatory registry | Central Dogma ODE, Gierer-Meinhardt pattern formation | `REGISTRY_ONLY` |

## Ghost entries requiring demotion or implementation

The audit reports these as present in the registry but not backed by a found Lean
module, Python implementation, or data pipeline:

| Ghost entry | Why it matters | Recommended action |
|---|---|---|
| Quasispecies equation | mutation-selection balance, error threshold, viral evolution | implement Lean skeleton + simulator |
| Replicator equation | evolutionary game dynamics | implement only if tied to population-genetics or ecology use case |
| Neutral theory / Kimura | drift-mutation balance | implement after drift/selection metrics |
| Masked language modeling loss for DNA | sequence-prediction information model | defer until corpus/data pipeline exists |
| pTM / TM-score | structural biology information metric | defer until protein-structure pipeline exists |

## Misfiled entry

| Entry | Reason | Action |
|---|---|---|
| `parametric-learn` | Three.js/TensorFlow.js parametric surface fitting demo; no biological sequence, population, or genetics-information role found | mark `MISFILED` or relocate outside genetics |

## Missing canonical gaps

| Missing area | Why it matters | Suggested implementation route |
|---|---|---|
| Selection detection | identifies signatures of selection in sequence/population data | implement Tajima's D and FST first |
| Phylogenetic tree inference | reconstructs evolutionary history as tree-structured information | use Jukes-Cantor distance, then neighbor-joining |
| Population structure | ancestry/latent-variable information | PCA/admixture after real genotype fixtures exist |
| Epigenetic HMM / chromatin states | regulatory information layer | HMM implementation plus receipt schema |
| Splicing / isoform quantification | transcript-level information | defer until RNA-seq or transcript fixtures exist |
| Variant calling | raw read to variant state inference | hard; requires aligner/error model |
| Comparative genomics | synteny/CNE/regulatory homology | hard; defer |

## Mass Number interpretation for genetics

Genetics is a communication regime, not a human-language regime.

```text
DNA sequence
  -> transcriptional decoder
  -> RNA folding / splicing decoder
  -> codon translation decoder
  -> peptide folding decoder
  -> cellular phenotype decoder
  -> population-selection decoder
```

Recommended Mass Number classes:

```text
MN-BIO-GEN   Genetic sequence mass
MN-BIO-COD   Codon / translation mass
MN-BIO-FOLD  Folding / conformation mass
MN-BIO-POP   Population-genetic mass
MN-BIO-REG   Regulatory / epigenetic mass
MN-BIO-EVO   Evolutionary trajectory mass
```

## Promotion policy

A genetics model may be promoted beyond `BEAUTIFUL_PROVISIONAL` only when it has
at least one of:

1. compiled Lean theorem or executable definition;
2. running Python/Rust pipeline with test fixtures;
3. real-data receipt with source provenance;
4. adversarial or benchmark receipt;
5. explicit connection to MassNumber admissibility or SemanticMass carrier scoring.

## Immediate promotion candidate

Implement selection metrics first:

```text
Tajima's D + FST
```

Rationale:

- low implementation difficulty;
- high genetics-information value;
- direct path from allele/genotype state to population selection signal;
- good MassNumber gate candidate for deciding whether selection evidence is
  strong enough to promote a registry model.
