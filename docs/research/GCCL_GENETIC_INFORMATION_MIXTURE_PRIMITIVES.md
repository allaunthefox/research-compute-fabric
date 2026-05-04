# GCCL Genetic Information Mixture Primitives

Status: Draft v0.1  
Scope: available biological/genetic information coding forms as GCCL mixture primitives  
Claim state: taxonomy / integration map; not a biological equivalence claim

---

## 1. Purpose

This document records the available genetic-information coding families that GCCL may use as **mixture primitives**.

The intent is not to claim that GCCL is biological DNA. GCCL remains:

> **Geometric, Cognitive, and Compression Law**

Genetic information coding is one strategy inside GCCL for constructing compact, evolvable, auditable model representations.

A genetic coding type becomes a GCCL mixture primitive only when it is treated as:

```text
encoding primitive
+ declared alphabet
+ transformation rules
+ residual / ambiguity policy
+ KOT cost
+ projection surface
+ receipt requirements
```

No genetic primitive is promoted by analogy alone.

---

## 2. Mixture primitive definition

A **mixture primitive** is a coding family that can be mixed with other coding families inside a GCCL model genome, compiler pass, or receipt-bearing transformation.

A primitive is admissible only when it declares:

| Field | Meaning |
|---|---|
| alphabet | symbol set or token basis |
| arity | grouping size, e.g. nucleotide, codon, k-mer, graph node |
| direction | linear, graph, bidirectional, hierarchical, spatial, temporal |
| ambiguity | how unknown/degenerate/mixed symbols are handled |
| transform rules | mutation, projection, decoding, translation, alignment, rewrite |
| residual | mismatch or loss measure |
| cost | KOT / compute / storage / route cost |
| receipt | evidence that the primitive was applied lawfully |

Canonical wrapper:

```text
Primitive := (Alphabet, Arity, Direction, Ambiguity, Transform, Residual, Cost, Receipt)
```

---

## 3. Primitive groups

The full registry is grouped into layers.

```text
A. molecular alphabets
B. codon and translation systems
C. protein / peptide encodings
D. ambiguity and degeneracy encodings
E. sequence file and quality encodings
F. alignment, assembly, and graph encodings
G. variant, haplotype, and population encodings
H. annotation and feature encodings
I. epigenetic and regulatory encodings
J. structural / 3D genome encodings
K. expression and multi-omics encodings
L. compression/indexing encodings
M. synthetic/expanded genetic alphabets
N. GCCL-native model-genome encodings
```

Each group can be used independently or mixed.

---

## 4. A — Molecular alphabet primitives

These are base symbol systems.

| Primitive | Alphabet / carrier | GCCL use |
|---|---|---|
| DNA alphabet | A, C, G, T | canonical 4-symbol discrete sequence primitive |
| RNA alphabet | A, C, G, U | transcript / runtime-expression primitive |
| Complement encoding | A↔T/U, C↔G | involution / mirror / reverse-complement transform |
| Purine/pyrimidine class | R/Y | coarse biochemical binary projection |
| Strong/weak class | S/W | bonding-strength projection |
| Keto/amino class | K/M | chemical-class projection |
| Gap symbol | - | alignment/deletion/absence primitive |
| Unknown symbol | N or ? | unresolved-state primitive |
| Modified base symbol | e.g. methylated / edited base | epigenetic or post-transcriptional state primitive |

Mixture note:

```text
DNA/RNA alphabets are not sufficient by themselves. GCCL should always declare whether the primitive is exact, ambiguous, modified, aligned, or projected.
```

---

## 5. B — Codon and translation primitives

These encode triplet-to-amino-acid or triplet-to-action mappings.

| Primitive | Shape | GCCL use |
|---|---|---|
| Standard codon table | 64 triplets → amino acids / stop | canonical 3-symbol translation primitive |
| Alternative genetic codes | mitochondrial / organism-specific tables | context-dependent decoder primitive |
| Start codon logic | AUG and alternatives | initiation / promoter-like gate |
| Stop codon logic | UAA/UAG/UGA and alternatives | termination / hard boundary primitive |
| Degenerate codon family | multiple codons same amino acid | many-to-one canonicalization primitive |
| Synonymous codon usage | codon choice under same amino acid | pressure/cost/regulatory primitive |
| Codon-pair encoding | adjacent codon effects | local transition / second-order grammar primitive |
| Reading frame | frame 0/1/2 | phase / offset primitive |
| Frameshift | altered reading frame | controlled projection fault / mutation primitive |
| Reverse-complement ORF | coding on opposite strand | mirror-expression primitive |
| Overlapping ORF | multiple products from same locus | multi-projection primitive |

GCCL use:

```text
codon := fixed-width grouped token with decoder context
```

Codons can encode biological amino acids or GCCL compiler atoms, but the decoder must declare which domain is active.

---

## 6. C — Protein and peptide encodings

These represent translated or expressed products.

| Primitive | Alphabet / structure | GCCL use |
|---|---|---|
| 1-letter amino acid code | 20 canonical residues plus ambiguity | compact protein phenotype primitive |
| 3-letter amino acid code | Ala, Cys, Asp, ... | human-readable residue primitive |
| Stop / termination marker | * or Stop | boundary marker |
| Ambiguous amino acids | B, Z, J, X, U, O | uncertainty / extended residue primitive |
| Peptide sequence | residue chain | expressed phenotype string |
| Protein domain | motif/domain block | reusable gene/product module |
| Motif / PROSITE-like pattern | constrained residue pattern | pattern grammar primitive |
| Secondary structure | helix/sheet/coil | coarse structural projection |
| Fold/topology class | higher-order structure | phenotype geometry primitive |
| Post-translational modification | phosphorylation, methylation, etc. | regulatory decoration primitive |

GCCL use:

```text
protein primitive = expressed phenotype layer, not source genome layer unless explicitly encoded as source.
```

---

## 7. D — Ambiguity and degeneracy primitives

These encode uncertainty, mixtures, and underdetermined states.

| Primitive | Meaning | GCCL use |
|---|---|---|
| IUPAC DNA ambiguity | R,Y,S,W,K,M,B,D,H,V,N | bounded ambiguity alphabet |
| IUPAC RNA ambiguity | same pattern with U | transcript ambiguity primitive |
| Amino acid ambiguity | B/Z/J/X plus U/O | protein uncertainty primitive |
| Degenerate codon notation | mixed bases per codon position | compact family of codons |
| Wildcard / any | N, X, ? | unknown state / projection gap |
| Consensus sequence | most likely symbol per locus | population/projection summary |
| Profile column | probability over symbols | soft-symbol primitive |
| Position weight matrix | weighted motif encoding | regulatory/signal primitive |
| Hidden-state emission | HMM-style symbol probabilities | latent grammar primitive |

Important rule:

```text
Ambiguity is not error by default. It is a declared mixture state with its own residual and cost.
```

---

## 8. E — Sequence file and quality primitives

These are practical encodings used in bioinformatics workflows.

| Primitive | Carrier | GCCL use |
|---|---|---|
| FASTA | sequence + identifier | raw sequence object |
| FASTQ | sequence + per-base quality | sequence plus uncertainty surface |
| QUAL | quality scores separately | uncertainty vector primitive |
| SAM | text alignment | alignment receipt / projection trace |
| BAM | binary compressed alignment | compact alignment substrate |
| CRAM | reference-based compressed alignment | reference-dependent compression primitive |
| SRA-like run metadata | read collection metadata | dataset provenance primitive |
| Phred quality score | log error probability | residual/error primitive |
| Read group metadata | sample/library/run grouping | source-context primitive |

GCCL use:

```text
FASTQ-like primitive = symbol stream + confidence vector
```

This is useful for model genomes because uncertainty should be first-class, not hidden.

---

## 9. F — Alignment, assembly, and graph primitives

These encode relationships between sequences or fragments.

| Primitive | Shape | GCCL use |
|---|---|---|
| Pairwise alignment | sequence-to-sequence mapping | projection between two symbol spaces |
| Multiple sequence alignment | sequence family matrix | consensus / variation surface |
| CIGAR string | compact edit operations | delta/edit primitive |
| Edit script | insert/delete/substitute | transformation receipt primitive |
| k-mer | length-k substring | local motif/token primitive |
| minimizer | representative k-mer | indexing / sparse witness primitive |
| de Bruijn graph | k-mer overlap graph | assembly graph primitive |
| string graph | read overlap graph | assembly/reconstruction primitive |
| overlap-layout-consensus | assembly pipeline | workflow primitive |
| pangenome graph | population-scale genome graph | multi-reference topology primitive |
| variation graph | reference + variant graph | graph phenotype primitive |
| synteny block | conserved segment ordering | macro-structure primitive |

GCCL use:

```text
alignment primitive = declared projection between state strings plus residual/edit receipt
```

---

## 10. G — Variant, haplotype, and population primitives

These encode differences between individuals, references, or populations.

| Primitive | Shape | GCCL use |
|---|---|---|
| SNP | single-symbol substitution | atomic mutation primitive |
| Indel | insertion/deletion | edit-length primitive |
| MNP | multi-nucleotide polymorphism | local block substitution |
| Structural variant | inversion/duplication/translocation/CNV | macro-transform primitive |
| Copy number | segment multiplicity | dosage/count primitive |
| VCF record | position + alleles + metadata | variant receipt primitive |
| BCF | binary VCF | compact variant substrate |
| Haplotype | linked allele sequence | path-through-graph primitive |
| Genotype | allele state per locus | individual-state primitive |
| Phase | linkage/order certainty | path certainty primitive |
| Allele frequency | population weight | mixture probability primitive |
| Hardy-Weinberg style summaries | population constraint | distribution gate primitive |

GCCL use:

```text
variant primitive = baseline + mutation + population/context metadata
```

---

## 11. H — Annotation and feature primitives

These encode interpreted regions and biological function labels.

| Primitive | Carrier | GCCL use |
|---|---|---|
| GFF/GFF3 | genomic features | interval annotation primitive |
| GTF | transcript/gene annotation | expression-structure primitive |
| BED | interval features | lightweight region primitive |
| GenBank / EMBL | annotated sequence record | rich provenance primitive |
| gene model | exon/intron/CDS/UTR layout | structured expression primitive |
| CDS | coding sequence | translated-region primitive |
| exon | expressed segment | splice building block |
| intron | non-coding removed region | masked/silent region primitive |
| UTR | untranslated regulatory region | boundary/regulatory primitive |
| promoter | initiation control | activation primitive |
| enhancer/silencer | distal regulation | nonlocal control primitive |
| terminator | termination control | expression stop primitive |
| operon | multi-gene regulatory unit | grouped expression primitive |

GCCL use:

```text
annotation primitive = semantic label over a sequence interval, with source and confidence.
```

---

## 12. I — Epigenetic and regulatory primitives

These encode state beyond the raw sequence.

| Primitive | Meaning | GCCL use |
|---|---|---|
| DNA methylation | base-level regulatory mark | gate/weight decoration |
| hydroxymethylation and related marks | modified-base state | extended alphabet primitive |
| histone modification | chromatin state | packaging/regulatory primitive |
| chromatin accessibility | open/closed signal | expression permission primitive |
| transcription factor binding | motif + binding event | regulatory operator primitive |
| enhancer-promoter contact | long-range regulation | nonlocal edge primitive |
| RNA editing | post-transcriptional base change | transcript mutation primitive |
| alternative splicing | multiple transcripts from one locus | multi-phenotype projection primitive |
| riboswitch | RNA-structure-regulated expression | conditional gate primitive |
| codon usage bias | translation efficiency / context | expression pressure primitive |
| translation pausing | timing effect | kinetic expression primitive |

GCCL use:

```text
regulatory primitive = condition that modifies whether, when, or how a region expresses.
```

---

## 13. J — Structural and 3D genome primitives

These encode spatial or long-range organization.

| Primitive | Shape | GCCL use |
|---|---|---|
| chromosome | large sequence container | macro-module primitive |
| chromatin domain | spatial/functional region | folded topology primitive |
| TAD-like domain | contact domain | local interaction basin primitive |
| contact map | matrix of spatial interactions | geometric adjacency primitive |
| Hi-C matrix | genome contact counts | 3D projection primitive |
| loop/contact edge | long-range connection | graph edge primitive |
| scaffold/contig | assembled sequence block | partial reconstruction primitive |
| telomere/centromere markers | structural boundaries | anchor / special-region primitive |

GCCL use:

```text
3D genome primitive = nonlocal topology over a linear code.
```

This maps well to NUVMAP, O-AMMR, and layered mountain projections.

---

## 14. K — Expression and multi-omics primitives

These encode measured expression and derived biological state.

| Primitive | Shape | GCCL use |
|---|---|---|
| RNA-seq count vector | expression counts | phenotype activity vector |
| transcript abundance | TPM/FPKM-like value | expression magnitude primitive |
| single-cell barcode | cell identity | lineage/source primitive |
| UMI | molecule identity | deduplication receipt primitive |
| ATAC-seq peak | accessibility interval | regulatory surface primitive |
| ChIP-seq peak | binding/modification interval | marked interval primitive |
| proteomics peptide ID | expressed protein evidence | phenotype evidence primitive |
| metabolomics vector | pathway state | downstream phenotype primitive |
| eQTL / QTL | genotype-phenotype relation | causal/association edge primitive |

GCCL use:

```text
omics primitive = measured phenotype surface with confidence, source, and transformation history.
```

---

## 15. L — Compression and indexing primitives

These are algorithmic primitives often used to compress, search, or compare genetic information.

| Primitive | Shape | GCCL use |
|---|---|---|
| run-length encoding | repeated symbol counts | counted switch primitive |
| Huffman coding | symbol-frequency code | entropy projection primitive |
| arithmetic/range coding | probability interval coding | compression substrate |
| Burrows-Wheeler Transform | reversible permutation | index/compression primitive |
| FM-index | compressed substring index | searchable compressed state |
| suffix array/tree | suffix indexing | motif/search primitive |
| minimizer index | sparse k-mer index | local witness primitive |
| syncmer/strobemer | robust sequence sampling | sparse representative primitive |
| reference-based compression | delta from baseline | AMMR/GCCL-Rep compatible primitive |
| CRAM-like reference coding | reference + read deltas | biological delta primitive |
| graph compression | compressed variation graph | topology-preserving compression |
| Bloom filter / counting filter | approximate membership | probabilistic witness primitive |
| sketching / MinHash | approximate similarity | coarse projection primitive |

GCCL use:

```text
compression primitive = representation reduction with declared decoder, residual, and baseline.
```

---

## 16. M — Synthetic and expanded genetic alphabets

These extend beyond the standard biological alphabets.

| Primitive | Alphabet / domain | GCCL use |
|---|---|---|
| synthetic base pairs | expanded DNA alphabets | larger symbol-space primitive |
| hachimoji DNA/RNA | 8-symbol genetic alphabet | octal biological-code analog |
| xeno-nucleic acids | alternative backbone systems | substrate-adapter primitive |
| noncanonical amino acids | expanded residue set | extended phenotype alphabet |
| quadruplet codons | 4-base codons | higher-arity codon primitive |
| recoded organisms | altered codon table | context-specific decoder primitive |
| unnatural base-pair systems | synthetic information carriers | nonstandard alphabet primitive |

GCCL use:

```text
expanded alphabet primitive = declared nonstandard symbol system requiring explicit decoder and receipt.
```

These are especially relevant to GCCL because the stack already uses 4-bit/quandary/nibble structures and may use hachimoji-like 8-symbol encodings.

---

## 17. N — GCCL-native model-genome primitives

These are not biological coding systems. They are GCCL internal analogs.

| Primitive | Shape | GCCL use |
|---|---|---|
| model codon | small compiler/action token | atomic model-expression unit |
| model gene | reusable transformation module | bounded operator packet |
| model chromosome | grouped module family | coherent model region |
| model genome | full encoded model family | compact generative specification |
| promoter gate | activation condition | expression control |
| suppressor gate | blocking condition | safety/regulatory control |
| intron region | non-expressed metadata or dormant payload | latent documentation / receipt storage |
| exon region | expressed artifact-producing region | active compiler product |
| mutation operator | admissible variation | model upgrade primitive |
| crossover operator | recombination between models | synthesis primitive |
| inversion / transposition | rearrangement operator | structure search primitive |
| codon-usage pressure | preference over equivalent encodings | γ pressure / KOT trade primitive |
| phenotype | decoded artifact or behavior | expressed model surface |
| fitness | residual + invariant + cost + task score | promotion pressure primitive |

GCCL use:

```text
GCCL-native genome primitives are inspired by biological coding, but they are compiler objects. They must not be described as biological equivalence.
```

---

## 18. Mixture rules

A GCCL model may mix primitives from multiple groups, but only under explicit rules.

### Rule 1 — Declare the active alphabet

```text
No symbol may be decoded without its active alphabet.
```

Example:

```text
AUG
```

may mean RNA codon, start signal, symbolic token, or model codon depending on the declared decoder.

### Rule 2 — Declare the projection

A sequence, graph, protein, annotation, or Goxel projection is not the source object unless the receipt says so.

### Rule 3 — Declare ambiguity

Ambiguous symbols are mixture states, not garbage.

### Rule 4 — Keep biological and GCCL-native meanings separate

Biological codons and GCCL model codons may share structural inspiration, but they must not share claims unless mapped by a receipt.

### Rule 5 — Every mixture pays KOT

Combining primitives increases expressive power and audit burden. Mixture complexity must be budgeted.

### Rule 6 — Every mixture has a residual

If a primitive is projected, compressed, translated, aligned, or expressed, the residual must be declared.

### Rule 7 — Every mixture has a quarantine path

If a mixed primitive cannot be decoded, audited, or scoped, it routes to HOLD or QUARANTINE.

---

## 19. Mixture primitive schema

Suggested JSON shape:

```json
{
  "primitive_id": "gccl.mix.codon.standard.v1",
  "group": "codon_translation",
  "name": "Standard codon table",
  "alphabet": ["A", "C", "G", "U"],
  "arity": 3,
  "direction": "linear_frame_dependent",
  "domain": "biological_reference",
  "decoder": "standard_rna_codon_table",
  "ambiguity_policy": "reject_or_expand_iupac",
  "residual_policy": "exact_or_declared_degenerate",
  "cost_policy": "q16_kot_by_symbols_and_decoder",
  "projection_targets": ["amino_acid_sequence", "model_codon_analogy"],
  "receipt_required": true,
  "claim_boundary": "biological codon table; not GCCL-native unless mapped"
}
```

Suggested Lean-facing shape:

```lean
structure MixturePrimitive where
  primitiveId : String
  group : String
  alphabetName : String
  arity : Nat
  domain : String
  decoderName : String
  ambiguityPolicy : String
  residualPolicy : String
  costPolicy : String
  receiptRequired : Bool
```

---

## 20. Recommended initial registry IDs

```text
gccl.mix.dna.iupac.v1
gccl.mix.rna.iupac.v1
gccl.mix.codon.standard.v1
gccl.mix.codon.alternative_table.v1
gccl.mix.amino_acid.iupac.v1
gccl.mix.fastq.phred.v1
gccl.mix.alignment.cigar.v1
gccl.mix.variant.vcf.v1
gccl.mix.annotation.gff3.v1
gccl.mix.epigenetic.modified_base.v1
gccl.mix.regulatory.promoter_gate.v1
gccl.mix.graph.debruijn.v1
gccl.mix.graph.pangenome.v1
gccl.mix.index.fm_index.v1
gccl.mix.synthetic.hachimoji.v1
gccl.mix.model.codon.v1
gccl.mix.model.gene.v1
gccl.mix.model.genome.v1
```

---

## 21. How this plugs into GCCL

Genetic information coding enters GCCL through the model-genome layer:

```text
biological coding primitive
→ declared mixture primitive
→ optional GCCL-native analog
→ compiler pass / workflow node
→ residual + KOT accounting
→ receipt
→ promotion or quarantine
```

The model-genome layer is therefore a mixture surface:

```text
DNA/RNA alphabets
+ codon tables
+ protein alphabets
+ ambiguity codes
+ file/quality encodings
+ alignment graphs
+ variant graphs
+ epigenetic marks
+ regulatory gates
+ structural genome topology
+ compression indexes
+ synthetic alphabets
+ GCCL-native compiler codons
```

This does not make GCCL biology. It makes biological information coding available as a disciplined source of mixture primitives.

---

## 22. Operating sentence

> Genetic information coding systems are available to GCCL as mixture primitives: alphabets, codons, ambiguities, alignments, variants, regulatory marks, structural graphs, compression indexes, and model-genome analogs may be combined only when their decoder, residual, KOT cost, scale, projection, and receipt obligations are declared.
