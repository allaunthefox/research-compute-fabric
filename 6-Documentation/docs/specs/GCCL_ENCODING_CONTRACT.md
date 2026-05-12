# GCCL Encoding Contract

Status: Draft v0.1
Scope: GCCL encoding contract for Lean, wiki, compiler, receipt, and logogram surfaces
Claim state: formal scaffold plus implementation contract; not a compression benchmark claim

## 1. What GCCL Means

GCCL means **Geometric, Cognitive, and Compression Law**.

It is not a single codec and not a claim that genome metaphors are biology or physics. GCCL is the law layer that decides whether a transformation of a structured object is lawful enough to promote.

The current formal anchor is:

```text
0-Core-Formalism/lean/Semantics/Semantics/GCCL.lean
```

The docs anchor is:

```text
docs/research/GCCL_THEORY_INTRO.md
docs/research/GCCL_GENETIC_INFORMATION_MIXTURE_PRIMITIVES.md
```

## 2. What We Encode

GCCL encodes **transitions**, not just objects.

A transition is any proposed change from one structured state to another:

```text
source state
  -> transform / compiler pass / projection / compression step
  -> target state
  -> receipt decision
```

The encoded object must declare seven law surfaces:

| Surface | What It Encodes |
|---|---|
| Geometric | state space, topology, projection, address, shape, locality, or adjacency |
| Cognitive | meaning, identity, salience, semantic load, routing burden, or interpretive constraint |
| Compression | canonicalization, bytecode, delta, representative carrier, index, or reduced form |
| Residual | mismatch, loss, drift, ambiguity, reconstruction error, or declared non-round-trip region |
| Cost | KOT, compute, memory, routing, storage, or audit cost |
| Scale | lambda band where the claim is valid: toy, local, benchmark, production, or cross-domain |
| Receipt | witness record explaining what passed, failed, held, or quarantined |

In Lean this starts as:

```lean
inductive LawAxis where
  | geometric
  | cognitive
  | compression
  | residual
  | cost
  | scale
  | receipt
```

## 3. How We Encode

Every GCCL transition is wrapped by the UMUP-lambda / IRP tuple:

```text
M = (S, T, I, R, K, P, Q, Lambda)
```

| Field | Meaning |
|---|---|
| S | state space declared |
| T | transform declared |
| I | invariants declared |
| R | residual declared |
| K | cost declared |
| P | projection declared |
| Q | quarantine path declared |
| Lambda | scale band declared |

Lean-facing form:

```lean
structure Wrapper where
  stateSpaceDeclared : Bool
  transformDeclared : Bool
  invariantsDeclared : Bool
  residualDeclared : Bool
  costDeclared : Bool
  projectionDeclared : Bool
  quarantineDeclared : Bool
  scaleDeclared : Bool
```

A wrapper is complete only when all fields are present:

```text
wrapperComplete =
  S && T && I && R && K && P && Q && Lambda
```

## 4. Bounded Lawful Surface

Raw GCCL can describe many things. Lawful GCCL is the bounded subset that can be replayed, checked, costed, and receipted.

A transition enters the **Bounded Lawful Surface** only if it has:

```text
complete wrapper
+ valid syntax
+ round-trip or declared loss policy
+ invariant preservation
+ residual within bound
+ cost within bound
+ ACCEPT receipt
```

Lean-facing gate:

```lean
def lawfulSurfaceAdmissible (t : Transition) : Bool :=
  wrapperComplete t.wrapper &&
  t.validSyntax &&
  t.roundTripOrLossPolicy &&
  t.invariantPreserved &&
  t.residualWithinBound &&
  t.costWithinBound &&
  transitionAccepted t
```

This is the first hard rule:

```text
Compression gain without invariant preservation is not lawful GCCL.
```

The second hard rule is the self-application rule:

```text
The GCCL model is not immune to information-theoretic bit rot.
```

Any compiler, logogram table, sidecar stream, topology label, or receipt chain
can accumulate sub-noticeable residual creep. A small unchecked difference is
not harmless because the lawful object is the replayable transition, not the
human impression that the transition still looks close enough.

Residual creep must be encoded directly:

| Creep Source | GCCL Encoding |
|---|---|
| substitution ambiguity | residual plus candidate-selection receipt |
| hash/literal collision | residual sidecar or HOLD |
| bounded-payload truncation | append sidecar or HOLD |
| topology-label drift | residual measurement or QUARANTINE |
| stale receipt/hash | receipt failure and HOLD |
| replay mismatch | failed transition |

This keeps compression-based explanations from becoming treatment-style goals,
truth claims, or aesthetic smoothing. The model is a measurement surface; it
must measure its own drift.

The Lean witness is:

```lean
theorem compression_gain_without_invariant_is_not_lawful :
    lawfulSurfaceAdmissible compressionOnlyExample = false
```

## 5. GCCL-Rep

GCCL-Rep is the compact representative carrier for a transition. It is not the truth of the transition.

GCCL-Rep must encode:

| Field | Meaning |
|---|---|
| baseline | what the transition starts from |
| representative | the compact event, bytecode, nibble switches, or packet |
| replay | how to reconstruct or check the target |
| residual check | how mismatch/loss is measured |
| KOT ledger | cost paid |
| receipt | attached witness |
| commit | AMMR/O-AMMR or equivalent committed history state |

Minimal equation:

```text
baseline + GCCL-Rep + replay + residual check + KOT + receipt + commit
  = verified transition carrier
```

Lean-facing gate:

```lean
def repVerified (e : GcclRepEvent) : Bool :=
  e.baselineDeclared &&
  e.representativeDeclared &&
  e.replayAvailable &&
  e.residualChecked &&
  e.kotAccounted &&
  e.receiptAttached &&
  e.committed
```

A verified carrier promotes only with a lawful transition:

```lean
def repPromotable (e : GcclRepEvent) (t : Transition) : Bool :=
  repVerified e && lawfulSurfaceAdmissible t
```

### Projectable Geometry Canonical Representation

Projectable geometry enters GCCL-Rep as a dimensionally typed representative
carrier, not as an untyped metaphor:

```text
16D signed envelope
  -> 12D source/residual plane
  -> 4D primitive keel
  -> genus-3 residual boat
  -> 0D closure
```

Reference gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/ProjectableGeometryCanonical.lean
```

Replay laws:

```text
source_12D =
  lift(project(source_12D))
  + residual_12D
```

```text
packet_local
+ shear_torsion
+ spectral_field
= residual_12D
```

The shell closure prior is encoded in twelfths:

```text
visible_4d = 4/12
shadow_3d  = 3/12
closure_0d = 1/12
lawbound   = 4/12
unresolved = 0/12
total      = 12/12
```

The representative carrier can promote only when the axis counts match, the
12D source rehydrates exactly, the genus-3 residual handles close, no unresolved
shell mass remains, and source/receipt hashes are present.

### LadderLUT Representative

Ordered fixed-width LUTs may be represented by a deterministic LadderLUT packet
instead of storing every entry:

```text
base = radix^block_width
value_i = (start + i) mod base
```

Reference gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/LadderLUT.lean
```

Promotion requires:

```text
radix > 1
+ block_width > 0
+ base = radix^block_width
+ length > 0
+ generator_bytes + residual_bytes + receipt_bytes
   < length * block_width
```

The decimal `1 / 998001` identity is a witness for the `base = 1000` case
because `998001 = (1000 - 1)^2`; it is not the decompressor implementation.
Carry-disturbed or skipped entries require residual repair.

### HexLogogram Atlas Representative

A hex seed may represent a deterministic logogram grouping atlas when the target
substitution map is table-shaped. The seed is not the payload and not the glyph.
It is the replay law that maps token/Mass/type coordinates into logogram group
IDs:

```text
hex_seed
  -> grouping_law
  -> registry_id
  -> Mass Number / chart / type witness fields
  -> group_i
  -> residual exceptions
```

Reference gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/HexLogogramAtlas.lean
```

Promotion requires:

```text
hex_digit_width > 0
+ block_base = 16^hex_digit_width
+ registry_id > 0
+ group_count > 0
+ token_domain > 0
+ length > 0
+ stride > 0
+ window > 0
+ assignment_bytes > 0
+ seed_bytes + law_bytes + registry_bytes + residual_bytes + receipt_bytes
   < length * assignment_bytes
```

The replay rule is deterministic:

```text
group_i = grouping_law(hex_seed, start_index + i, mass_basin, chart_id, type_witness)
          mod group_count
```

Any token whose generated group does not match the explicit substitution map is
a residual exception. If the residual exceptions erase the byte savings, the
atlas is not promotable.

### Manifold Boundary Atlas Representative

The same seed-generated approach can emit candidate manifold boundaries for
RRC identification. This is not a claim that a tear exists. It is a compact
candidate surface that RRC can check against receipts:

```text
hex_seed
  -> boundary_law
  -> dimension / genus / Mass basin / torsion / phase fields
  -> boundary candidate coordinates
  -> RRC tear-boundary evidence candidate
  -> residual exceptions
```

Reference gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/ManifoldBoundaryAtlas.lean
```

Promotion requires:

```text
block_base = 16^hex_digit_width
+ dimension_count > 0
+ coordinate_domain > 0
+ boundary_count > 0
+ length > 0
+ stride > 0
+ explicit_boundary_bytes > 0
+ RRC shape evidence present
+ residual policy declared
+ seed_bytes + law_bytes + residual_bytes + receipt_bytes
   < length * explicit_boundary_bytes
```

The generated boundary atlas can set `tearBoundary` evidence for the RRC
receipt, but it does not by itself make a torn projection admissible. RRC still
requires contradiction evidence, detached-mass evidence, residual-lane evidence,
and the ordinary projection gates.

## 6. Mixture Primitive Encoding

Genetic, logogram, graph, file, codec, and model-genome symbols enter GCCL as **mixture primitives**.

A primitive is not accepted by analogy. It must declare:

| Field | Meaning |
|---|---|
| primitive ID | stable registry name |
| group | which primitive family it belongs to |
| alphabet | active symbol set or token basis |
| arity | grouping width, such as 1 base, 3 codon symbols, k-mer, or graph node |
| direction | linear, graph, bidirectional, hierarchical, spatial, temporal, or frame-dependent |
| domain | biological reference, GCCL-native, synthetic, external codec, or receipt-mixed |
| decoder | the active decoder |
| ambiguity policy | reject, expand, bounded mixture, probabilistic profile, or quarantine |
| residual policy | how mismatch/loss is measured |
| cost policy | how KOT is charged |
| projection | where the primitive projects |
| receipt requirement | whether it needs explicit witness evidence |
| claim boundary | what the primitive does not claim |

Lean-facing form:

```lean
structure MixturePrimitive where
  primitiveId : String
  group : PrimitiveGroup
  alphabetName : String
  arity : Nat
  direction : PrimitiveDirection
  domain : PrimitiveDomain
  decoderName : String
  ambiguityPolicy : AmbiguityPolicy
  residualPolicyDeclared : Bool
  costPolicyDeclared : Bool
  projectionDeclared : Bool
  receiptRequired : Bool
  claimBoundaryDeclared : Bool
```

Admission gate:

```lean
def mixturePrimitiveAdmissible (p : MixturePrimitive) : Bool :=
  activeAlphabetDeclared p &&
  p.arity > 0 &&
  p.residualPolicyDeclared &&
  p.costPolicyDeclared &&
  p.projectionDeclared &&
  p.receiptRequired &&
  p.claimBoundaryDeclared
```

## 7. Current Primitive Groups

The current GCCL primitive space is grouped as:

| Group | Encodes |
|---|---|
| molecular alphabet | DNA, RNA, complement, gap, unknown, modified bases |
| codon translation | codons, starts/stops, reading frame, frameshift, overlapping ORF |
| protein/peptide | amino acid symbols, motifs, domains, folds, modifications |
| ambiguity/degeneracy | IUPAC ambiguity, wildcards, profiles, weighted motif columns |
| sequence quality/file | FASTA, FASTQ, SAM/BAM/CRAM, Phred, read metadata |
| alignment/assembly/graph | CIGAR, edit scripts, k-mers, de Bruijn graph, pangenome graph |
| variant/haplotype/population | SNP, indel, VCF, haplotype, genotype, phase, frequency |
| annotation/feature | GFF/GTF/BED, gene models, exon/intron/CDS, promoters, enhancers |
| epigenetic/regulatory | methylation, histone marks, accessibility, TF binding, splicing |
| structural 3D genome | chromosomes, contact maps, loops, scaffold/contig, TAD-like domains |
| expression/multi-omics | RNA-seq, UMI, ATAC/ChIP peaks, proteomics, metabolomics, eQTL |
| compression/indexing | RLE, Huffman, arithmetic coding, BWT, FM-index, minimizers, Bloom filters |
| synthetic/expanded alphabet | hachimoji, XNA, noncanonical amino acids, quadruplet codons |
| GCCL-native model genome | model codons, genes, chromosomes, promoter/suppressor gates, phenotype |

## 8. Domain Mixing Rule

No symbol may be decoded without its active alphabet and decoder.

The same surface string can mean different things:

```text
AUG
```

It may be an RNA start codon, a biological amino-acid translation input, a symbolic model codon, or a compiler token. GCCL does not permit those meanings to merge silently.

Lean-facing rule:

```lean
def domainMixAllowed (left right : PrimitiveDomain) : Bool :=
  if left == right then
    true
  else
    left == PrimitiveDomain.mixedByReceipt || right == PrimitiveDomain.mixedByReceipt
```

Witnesses:

```lean
theorem biological_and_model_domains_do_not_mix_without_receipt :
    primitivesCanMix dnaIupacPrimitive modelCodonPrimitive = false

theorem biological_and_model_domains_mix_with_receipt_bridge :
    primitivesCanMix dnaIupacPrimitive mappedBridgePrimitive = true
```

## 9. Logogram Encoding

Logograms enter GCCL as projected glyph payloads with receipts. The current logogram projection contract is:

```text
logogram_cell -> canonical_hash -> glyph_payload -> projection_lane
```

The logogram payload is bounded, currently 16 bytes in the RRC bridge surface, and it must carry:

| Field | Meaning |
|---|---|
| canonical cell hash | deterministic identity of the symbolic cell |
| bounded glyph payload | compact visual/symbol payload |
| substitution receipt | what was canonicalized or replaced |
| semantic regime | folding, pruning, or tearing regime |
| projection lane | normal or quarantine |
| residual lane | required for repaired tears or overrun payloads |

The Lean formal gate lives in:

```text
0-Core-Formalism/lean/Semantics/Semantics/RRCLogogramProjection.lean
```

GCCL treats this as one projection family:

```lean
ProjectionKind.logogramGlyphPayload
```

## 10. Omindirection Encoding

Omindirection is the orientation and placement contract for logogram atoms. It is stricter than bidirectional text flow.

Formal source:

```text
0-Core-Formalism/lean/Semantics/Semantics/Omindirection.lean
```

Design/compiler source:

```text
6-Documentation/docs/specs/OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md
```

Every promoted omindirectional atom must encode:

| Field | Meaning |
|---|---|
| payload hash | canonical payload identity |
| direction | explicit LTR or RTL flow direction |
| chirality | left, right, ambidextrous, or none |
| phase | durable cyclic chirality degree, 0 through 359 |
| tone/status | witness, unknown, boundary, residual, growth, or neutral |
| placement | row, mirror-left, mirror-right, board, or quarantine |
| coordinate | explicit tile coordinate |
| torsion | binding twist or residual stress |
| temporal | corpus time, token order, recurrence distance, or metaprobe pass |
| rounding/residual | declared rehydration metadata |
| receipt | source, payload, and receipt hashes |

Lean-facing gate:

```lean
def atomAdmissible (a : OmiAtom) : Bool :=
  explicitDirection a.direction &&
  chiralityCompatibleWithPhase a.chirality a.phase &&
  receiptComplete a &&
  boardPlacementAdmissible a &&
  mirrorPlacementAdmissible a &&
  quarantinePlacementAdmissible a &&
  a.decision == AtomDecision.accept
```

The hard rules are:

```text
auto direction is not promotable
chirality is not inferred from LTR/RTL direction
phase is the durable chiral orbit
mirror-left requires left or ambidextrous chirality
mirror-right requires right or ambidextrous chirality
board placement requires at least one liberty or declared capture
quarantine placement requires a quarantine decision
receipt payload hash must match atom payload hash
```

Witnesses:

```text
row witness atom admitted: true
auto-direction atom admitted: false
mirror-right atom admitted: true
dead board tile admitted: false
quarantine atom routed to quarantine: true
```

## 11. Receipt Shape

Every promoted GCCL transition should emit or link a receipt with at least:

```yaml
gccl_receipt:
  model_id:
  source_id:
  baseline_hash:
  target_hash:
  transform:
  projection:
  scale_band:
  residual:
  residual_bound:
  kot_cost:
  cost_bound:
  invariants_checked:
  invariants_failed:
  round_trip:
  compression_ratio:
  compression_convention:
  proof_refs:
  benchmark_refs:
  decision:
```

Decision states:

```text
ACCEPT
REJECT
HOLD
QUARANTINE
```

## 12. Promotion Rule

GCCL uses a strict promotion ladder:

```text
RAW_IDEA
  -> SANITIZED_METAPHOR
  -> TOY_MODEL
  -> TYPED_MODEL
  -> RESIDUAL_TESTED
  -> COST_ACCOUNTED
  -> PROOF_CANDIDATE
  -> CORE_MODULE
```

The reverse path is allowed and expected. A broken invariant demotes the object. A failed residual test demotes the object. An undefined alphabet, decoder, or receipt routes to HOLD or QUARANTINE.

## 13. Current Build Evidence

As of this spec, the GCCL formal core has been checked with:

```text
lake env lean Semantics/GCCL.lean
lake build Semantics.GCCL
lake env lean Semantics/Omindirection.lean
lake build Semantics.Omindirection
lake env lean Semantics.lean
lake build Semantics
```

The GCCL witnesses evaluate:

```text
lawfulExample admitted: true
compressionOnlyExample admitted: false
verifiedRep + lawfulExample promotable: true
DNA primitive mixed with model codon without receipt: false
DNA primitive mixed through receipt bridge: true
omindirection row atom admitted: true
omindirection auto direction admitted: false
omindirection dead board tile admitted: false
```

## 14. Open Work

The next missing pieces are:

1. Define the canonical GCCL-native logogram alphabet as explicit Lean constructors.
2. Add a registry file that maps primitive IDs to concrete decoders and receipts.
3. Connect GCCL receipts to ENE/TiddlyWiki write paths.
4. Add machine-generated receipt examples for logogram, codon, graph, and bytecode transitions.
5. Tie GCCL-Rep to AMMR/O-AMMR commit records rather than string placeholders.
