# ENE Schema Specification v1.0.0

**Status:** Formal specification for machine-checkable conformance  
**Date:** 2026-04-18  
**Purpose:** Type/schema contract separate from observed dataset

---

## 1. Type Hierarchy

```
BaseArchiveRecord              -- Lossless preservation layer
    ↓ enhancement
EnhancedArchiveRecord          -- Semantic enrichment layer
    ↓ attestation  
AttestedArchiveRecord        -- Provenance verification layer
```

---

## 2. BaseArchiveRecord (Lossless Layer)

**Purpose:** Complete, lossless preservation of original sources. No semantic processing required.

```typescript
interface BaseArchiveRecord {
  // Identity (§2.1)
  archive_id: ArchiveID;           // content-addressed per §2.1.1
  source_type: SourceType;         // §2.2
  source_file: string;             // absolute or relative path
  
  // Content preservation (§2.3)
  raw_content: JSONValue;          // original structure, unchanged
  extracted_text: string;           // UTF-8, flattened for indexing
  
  // Provenance (§2.4)
  extracted_at: ISOTimestamp;
  content_hash: SHA256Hex;        // §2.5
  extraction_version: string;      // "ene_complete_extract_v1"
  
  // Optional SQL metadata
  row_number?: uint32;            // SQL table row index
  table_name?: string;            // SQL table name
}
```

### 2.1.1 ArchiveID Derivation Rule

```
archive_id := source_prefix + "_" + content_truncated

where:
  source_prefix := source_type + optional_table_or_filename
  content_truncated := first 16 chars of content_hash

examples:
  "sqlite_packages_0_755cad3f154c4dc7"
  "chatgpt_aas_pi_computation_enhancement_b15d663e393283e4"
  "json_event_catalog_42_a1b2c3d4e5f67890"
```

**Invariant:** `content_hash` is SHA256 over canonical `raw_content` JSON.

### 2.2 SourceType Enum

```
SourceType ::= "sqlite" | "sql_insert" | "json_catalog" | "chatgpt" | "legacy_lean"
```

### 2.3 Content Preservation Rules

- `raw_content`: Original parsed structure, no transformation
- `extracted_text`: UTF-8 string, max 10,000 chars, for search/semantic processing
- Bytes in source → hex string with `"_type": "bytes"` marker in raw_content

### 2.4 Timestamp Format

```
ISOTimestamp := "YYYY-MM-DDTHH:MM:SS.ssssss"  // ISO 8601 with microseconds
```

### 2.5 Hash Format

```
SHA256Hex := [0-9a-f]{64}  // lowercase hex, no 0x prefix
```

---

## 3. EnhancedArchiveRecord (Semantic Layer)

**Purpose:** Multi-scale semantic representation for cross-linkage.

**Extends:** BaseArchiveRecord with required semantic fields.

```typescript
interface EnhancedArchiveRecord extends BaseArchiveRecord {
  // Multi-scale semantic representation (§3.1)
  concept_vector: ConceptVector14;     // required, 14-dim
  phrase_vector: PhraseVector;          // required, map<string, float>
  entities: EntityList;                  // required, string[]
  topic_clusters: TopicList;            // required, string[]
  
  // Connectivity (§3.2)
  link_count: uint32;                    // number of semantic links
}
```

### 3.1 ConceptVector14 Specification

```typescript
ConceptVector14 := [float; 14]  // L2-normalized, each in [0.0, 1.0]

Axis ordering (fixed):
  0: substrate      -- universal computation, foam
  1: compression    -- soliton, encoding, entropy
  2: topology       -- graph, dag, manifold, node
  3: hardware       -- chip, verilog, hdl, fpga
  4: time           -- temporal, clock, tick
  5: crypto         -- hash, sha256, proof, verify
  6: database       -- sql, index, query, storage
  7: semantic       -- language, meaning, concept
  8: physics        -- thermo, quantum, entropy
  9: security       -- isolation, warden, boundary
  10: os_vm         -- kernel, vm, bytecode, runtime
  11: research      -- theorem, proof, discovery
  12: omnitoken     -- token, score, manifest, capsule
  13: identity      -- provenance, attestation, signature

Extraction version: "concept_vector_14_v1"
Normalization: L2 per-vector: sum(x^2) = 1.0
```

### 3.2 EntityList and TopicList

```typescript
EntityList := string[]  // extracted domain entities, max 50
TopicList := Topic[]    // classified topics, max 10

Topic ::= "compression" | "topology" | "security" | "hardware" | 
          "physics" | "math_theorem" | "codon" | "neural_sae" | 
          "lean_semantics" | "geometry"
```

---

## 4. Provenance Layer

### 4.1 ProvenanceManifest

```typescript
interface ProvenanceManifest {
  pipeline_id: string;                  // e.g., "ene_complete_extract_v1"
  manifest_hash: SHA256Hex;           // §4.1.1 canonical hash
  input_digest: SHA256Hex;            // previous cumulative state
  op_code: OpCode;                    // §4.1.2
  signal_metadata: JSONValue;         // operation parameters
  output_digest: SHA256Hex;           // record content hash
  timestamp: ISOTimestamp;
  sequence_num: uint32;               // 0-indexed position in chain
  prev_manifest_hash?: SHA256Hex;     // previous manifest's manifest_hash
}
```

#### 4.1.1 Canonical Manifest Hash

```
manifest_hash := SHA256(canonical_json)

where canonical_json is JSON serialization of:
{
  "pipeline_id": string,
  "input_digest": SHA256Hex,
  "op_code": OpCode,
  "signal_metadata": JSONValue,
  "output_digest": SHA256Hex,
  "timestamp": ISOTimestamp,
  "sequence_num": uint32,
  "prev_manifest_hash": SHA256Hex | null
}

with:
  - sort_keys=True
  - separators=(',', ':')
  - ensure_ascii=False
  - no manifest_hash field (self-reference excluded)
```

#### 4.1.2 OpCode Enum

```
OpCode ::= "EXTRACT_SQLITE" | "EXTRACT_SQL_INSERT" | "EXTRACT_JSON_CATALOG" | 
           "EXTRACT_CHATGPT" | "EXTRACT_LEGACY_LEAN"
```

### 4.2 SentenceRecord

```typescript
interface SentenceRecord {
  data_hash: SHA256Hex;               // content hash (hex, not base64)
  prev_hash: SHA256Hex;               // previous sentence hash
  metadata_hash: SHA256Hex;           // operation metadata hash
  timestamp: UnixTimestamp;           // seconds since epoch, float
  cognitive_load: CognitiveLoadVector; // §4.2.1
  features: FeatureVector9;            // §4.2.2
}

UnixTimestamp := float  // time.time() output
```

#### 4.2.1 CognitiveLoadVector

```typescript
CognitiveLoadVector := {
  L_I: float,        // Intrinsic: Shannon entropy / 8, bits per byte
  L_E: float,        // Extraneous: structural complexity
  L_G: float,        // Germane: semantic density
  L_R: float,        // Routing: decision cost
  L_M: float,        // Memory: storage cost
  L_total: float,    // sum of above
  efficiency: float  // L_G / L_total, or 0 if L_total = 0
}

All values in [0.0, ∞), typically L_total ∈ [0.5, 2.0]
```

#### 4.2.2 FeatureVector9

```typescript
FeatureVector9 := [float; 9]

Index semantics:
  0: normalized_size          -- len(text) / 10000
  1: math_density            -- 'theorem' count / 10
  2: compression_domain      -- 'compression' count / 10
  3: security_domain         -- 'security' count / 10
  4: hardware_domain         -- 'hardware' count / 10
  5: code_density            -- '```' count / 5
  6: vocabulary_diversity    -- unique_words / 1000
  7: structure_density       -- newline count / 100
  8: capitalization_ratio  -- uppercase / total chars
```

### 4.3 ArchiveAttestation

```typescript
interface ArchiveAttestation {
  attestation_id: string;             // "attest_" + archive_id
  archive_id: ArchiveID;              // references EnhancedArchiveRecord
  source_type: SourceType;             // preserved from base record
  content_hash: SHA256Hex;
  provenance_key: SHA256Hex;          // Merkle root of manifest chain
  sentence_hash: SHA256Hex;           // links to SentenceRecord
  extracted_at: ISOTimestamp;
  attested_at: ISOTimestamp;
  verification_status: VerificationStatus; // §4.3.1
}
```

#### 4.3.1 VerificationStatus Enum

```
VerificationStatus ::= "pending" | "verified" | "failed"
```

---

## 5. EnhancedGraph

```typescript
interface EnhancedGraph {
  meta: GraphMeta;
  nodes: EnhancedNode[];
  links: EnhancedLink[];
  entity_index: Map<Entity, ArchiveID[]>;
}

interface GraphMeta {
  total_records: uint32;
  total_links: uint32;
  links_per_record: float;
  resolution: string;        // "maximum" | "high" | "standard"
  generated_at: ISOTimestamp;
}

interface EnhancedNode {
  id: ArchiveID;
  type: NodeType;            // "chatgpt_conversation" | "sqlite_table_row" | ...
  title?: string;
  timestamp?: ISOTimestamp;
  
  // From EnhancedArchiveRecord
  concept_vector: ConceptVector14;
  entities: EntityList;
  topic_clusters?: TopicList;
  theorems?: string[];
  insights_count?: uint32;
  code_snippets_count?: uint32;
  
  link_count: uint32;
  text_preview?: string;     // truncated extracted_text
}

interface EnhancedLink {
  source: ArchiveID;
  target: ArchiveID;
  score: float;              // [0.0, 1.0]
  type: LinkType;
}

NodeType ::= "chatgpt_conversation" | "sqlite_table_row" | "sql_insert_row" | 
             "json_catalog_entry" | "legacy_lean"

LinkType ::= "concept_similar" | "entity_sha256" | "semantic_phrase" | 
             "shared_topic" | "shared_substrate" | "ene_entity_bridge" | 
             "weak_semantic"
```

---

## 6. Integrity Invariants

### 6.1 Archive Integrity

```
∀ record ∈ archive.records:
  record.content_hash = SHA256(canonical(record.raw_content))
  record.archive_id follows §2.1.1 format
  record.source_type ∈ SourceType enum
  record.extraction_version = "ene_complete_extract_v1"
```

### 6.2 Enhanced Graph Integrity

```
∀ node ∈ graph.nodes:
  node.id ∈ archive.records.keys()
  len(node.concept_vector) = 14
  ∀ v ∈ node.concept_vector: 0.0 ≤ v ≤ 1.0
  node.link_count = count(link where link.source = node.id or link.target = node.id)

∀ link ∈ graph.links:
  link.source ∈ graph.nodes.id
  link.target ∈ graph.nodes.id
  link.score ∈ [0.0, 1.0]
  link.type ∈ LinkType enum
```

### 6.3 Provenance Chain Integrity

```
∀ i ∈ [1, len(manifests)):
  manifests[i].prev_manifest_hash = manifests[i-1].manifest_hash
  
manifests[0].prev_manifest_hash = null

∀ manifest ∈ manifests:
  manifest.manifest_hash = compute_manifest_hash(manifest) per §4.1.1
```

### 6.4 Attestation Integrity

```
∀ attestation ∈ attestations:
  attestation.archive_id ∈ archive.records.keys()
  attestation.source_type = archive.records[attestation.archive_id].source_type
  attestation.verification_status ∈ VerificationStatus enum
  attestation.content_hash ≠ ""  // never empty
```

### 6.5 Merkle Tree Integrity

```
merkle_leaves.length > 0
∀ leaf ∈ merkle_leaves: leaf ≠ ""  // no empty leaves
merkle_root = compute_merkle_root(merkle_leaves)
```

---

## 7. Conformance Checking (Lean Target)

Future Lean verification should check:

```lean
-- Schema conformance
def isValidArchiveRecord (r : ArchiveRecord) : Bool :=
  r.archive_id.length > 0 &&
  r.source_type ∈ SourceType.values &&
  r.content_hash.length = 64 &&
  isHex r.content_hash

-- Enhanced conformance  
def isValidEnhancedRecord (r : EnhancedArchiveRecord) : Bool :=
  isValidArchiveRecord r &&
  r.concept_vector.length = 14 &&
  isL2Normalized r.concept_vector &&
  r.entities.length > 0

-- Provenance chain validity
def isValidManifestChain (manifests : List ProvenanceManifest) : Bool :=
  ∀ i ∈ [1, manifests.length),
    manifests[i].prev_manifest_hash = manifests[i-1].manifest_hash

-- Cross-reference integrity
def isValidAttestation (a : ArchiveAttestation) (archive : Archive) : Bool :=
  a.archive_id ∈ archive.records &&
  a.source_type = archive.records[a.archive_id].source_type &&
  a.verification_status ∈ ["pending", "verified", "failed"]
```

---

## 8. AVMR-Enhanced Vector Layer (Optional Physics-Rooted Indexing)

**Purpose:** Alternative to HNSW indexing using AVMR (Algebraic Vector Mountain Range) spectral geometry from `Semantics/AVMR.lean`. Provides O(√N) shell-based search with field-coupled similarity.

### 8.1 AVMR State Structure

```typescript
interface AVMRState {
  // Shell decomposition: n = k² + a = (k+1)² - b, where a+b = 2k+1
  shell: {
    n: uint32;           // integer position in mountain range
    k: uint32;           // floor(sqrt(n)) — shell number
    a: uint32;           // forward offset from k²
    b: uint32;           // backward offset to (k+1)²
  };
  
  // Tip coordinates: Tip(n) = (ab, a-b) ∈ ℝ²
  mass: int;             // ab product
  polarity: int;         // a - b
  
  // 8-bin spectral signature (from AVMR eventSpectrum)
  spectrum: [Q16_16; 8];  // quantized spectral bins
  
  // Field interaction state
  interaction: Q16_16;    // computed interaction score
  phase: int;            // -3 to 3 classification bucket
  
  // Aggregation metadata
  resonance_count: uint32;  // degeneracy count from merges
  priority_bias: int;       // 0 or 1 from parity check
  
  // Provenance
  derived_from: "concept_vector" | "text_embedding" | "direct";
  generation_timestamp: ISOTimestamp;
}
```

### 8.2 Shell-Based Indexing

```typescript
interface ShellIndex {
  // Index by shell number k = floor(sqrt(n))
  shells: Map<uint32, {
    k: uint32;
    shell_range: [uint32, uint32];   // [k², (k+1)²)
    record_ids: ArchiveID[];           // records in this shell
    
    // Axial generators (A_k, G_k, C_k, T_k positions per AVMR)
    A_position: uint32;   // k² — purine anchor
    G_position: uint32;   // k² + k — purine mid-shell
    C_position: uint32;   // k² + k + 1 — pyrimidine mid-shell
    T_position: uint32;   // (k+1)² - 1 — pyrimidine anchor
    
    // Field aggregate for the shell (precomputed)
    aggregate_spectrum: [Q16_16; 8];
    total_mass: int;
    total_polarity: int;
  }>;
  
  // Search radius: how many adjacent shells to query
  default_search_radius: uint32;  // typically 1 (3 shells total)
}

// Shell decomposition function (from AVMR.lean:67-71)
function shellState(n: uint32): { k: uint32, a: uint32, b: uint32 } {
  const k = Math.floor(Math.sqrt(n));
  const a = n - k*k;
  const b = (k+1)*(k+1) - n;
  return { k, a, b };
}
```

**Search Complexity:** O(√N) — search 2r+1 shells containing O(√N) records each, vs O(N) brute force.

### 8.3 AVMR Similarity Scoring

```typescript
interface AVMRScoring {
  // Interaction score: J(n) = ab·F_m + (a-b)·F_p + ⟨χ(n), F_c(n)⟩
  computeInteractionScore(
    query: AVMRState,
    target_shell: { k: uint32, aggregate: LocalField },
    echo_depth: uint32  // 1, 2, or 3 for tailWeight decay
  ): Q16_16;
  
  // Field construction with echo weights [1, ½, ¼]
  buildFieldAt(
    n: uint32,
    maxN: uint32,
    records: AVMRState[]
  ): LocalField;
  
  // Resonance detection between siblings
  siblingResonance(left: AVMRState, right: AVMRState): uint32;
  
  // Final combined score
  computeAVMRScore(
    query: AVMRState,
    candidate: AVMRState,
    field: LocalField
  ): float {
    const massTerm = query.mass * field.massField / Q16_16_SCALE;
    const polTerm = query.polarity * field.polarityField / Q16_16_SCALE;
    const specTerm = spectralOverlap(query.spectrum, field.spectrum) / Q16_16_SCALE;
    const resonance = siblingResonance(query, candidate) * 0.1;
    return massTerm + polTerm + specTerm + resonance;
  }
}

// Spectral overlap: Σᵢ(spectrum₁ᵢ · spectrum₂ᵢ)
function spectralOverlap(a: [Q16_16; 8], b: [Q16_16; 8]): Q16_16 {
  return a.map((ai, i) => ai * b[i]).reduce((sum, x) => sum + x, 0);
}
```

### 8.4 Integration with Concept Vectors

```typescript
// Map 14-dim concept vectors to AVMR shell coordinates
function conceptVectorToAVMR(
  concept_vector: [float; 14],
  source_text_hash: SHA256Hex
): AVMRState {
  // 1. Compute magnitude and map to shell position
  const magnitude = Math.sqrt(concept_vector.reduce((a, b) => a + b*b, 0));
  const n = Math.floor(magnitude * 1000);  // scale factor tunable
  
  // 2. Shell decomposition
  const { k, a, b } = shellState(n);
  
  // 3. Collapse 14 concept axes to 8 spectral bins
  const spectrum = collapse14to8Bins(concept_vector);
  
  // 4. Derive mass/polarity from dominant axes
  // Axis 0: substrate, Axis 1: compression (example weighting)
  const mass = Math.floor(concept_vector[0] * concept_vector[1] * 100);
  const polarity = Math.floor((concept_vector[0] - concept_vector[1]) * 100);
  
  // 5. Compute phase from interaction bucket
  const phase = computePhaseFromPolarity(polarity, k);
  
  return {
    shell: { n, k, a, b },
    mass, polarity, spectrum,
    interaction: 0,  // computed later via buildFieldAt
    phase,
    resonance_count: 0,
    priority_bias: (polarity > 0) ? 1 : 0,
    derived_from: "concept_vector",
    generation_timestamp: now()
  };
}

// Bin collapse: 14 axes → 8 spectral bins
function collapse14to8Bins(concept: [float; 14]): [Q16_16; 8] {
  return [
    quantize(concept[0] + concept[1]),   // substrate + compression
    quantize(concept[2] + concept[3]),   // topology + hardware
    quantize(concept[4] + concept[5]),   // time + crypto
    quantize(concept[6] + concept[7]),   // database + semantic
    quantize(concept[8] + concept[9]),   // physics + security
    quantize(concept[10] + concept[11]), // os_vm + research
    quantize(concept[12] + concept[13]), // omnitoken + identity
    Q16_16.zero                           // reserved
  ];
}

function quantize(f: float): Q16_16 {
  return Math.floor(f * 65536);  // Q16.16 fixed point
}
```

### 8.5 AVMR-Enhanced Merkle Aggregation

```typescript
// Replace standard Merkle with AVMR vector aggregation
interface AVMRMerkleNode {
  // Standard Merkle
  hash: SHA256Hex;
  
  // AVMR enhancement: aggregate vector state
  vec: AVMRState;
  
  // Resonance tracking from merge
  sibling_resonance: uint32;
  
  // Queryable aggregate properties
  aggregate_mass: int;
  aggregate_polarity: int;
  dominant_spectrum: [Q16_16; 8];
}

// AVMR merge: spectral superposition with resonance detection
function createAVMRParent(left: AVMRMerkleNode, right: AVMRMerkleNode): AVMRMerkleNode {
  const resonance = siblingResonance(left.vec, right.vec);
  
  return {
    hash: SHA256(left.hash + right.hash),
    vec: mergeAVMR(left.vec, right.vec, resonance),
    sibling_resonance: resonance,
    aggregate_mass: left.vec.mass + right.vec.mass,
    aggregate_polarity: left.vec.polarity + right.vec.polarity,
    dominant_spectrum: piecewiseMerge(left.vec.spectrum, right.vec.spectrum)
  };
}

// Merge law from AVMR.lean:228-240
function mergeAVMR(l: AVMRState, r: AVMRState, resonance: uint32): AVMRState {
  return {
    shell: r.shell,  // inherit from right (newer)
    mass: l.mass + r.mass,
    polarity: l.polarity + r.polarity,
    spectrum: piecewiseMerge(l.spectrum, r.spectrum),
    interaction: l.interaction + r.interaction,
    phase: r.phase,
    resonance_count: l.resonance_count + r.resonance_count + resonance,
    priority_bias: l.priority_bias + r.priority_bias,
    derived_from: "merged",
    generation_timestamp: now()
  };
}

// Piecewise spectral merge: bin-wise max or sum
function piecewiseMerge(a: [Q16_16; 8], b: [Q16_16; 8]): [Q16_16; 8] {
  return a.map((ai, i) => Math.max(ai, b[i]));  // or: ai + b[i]
}
```

**Benefit:** Merkle tree now carries **semantic aggregate state** — query "what's the spectral composition of subtree X?" without leaf traversal.

### 8.6 Query Interface: AVMR-Enhanced Search

```typescript
interface AVMRSearchQuery {
  // Input
  query_text?: string;
  query_concept_vector?: [float; 14];
  query_avmr_state?: AVMRState;
  
  // Constraints (same as FilteredConceptSearch)
  filter_criteria?: {
    source_type?: SourceType;
    topic_cluster?: string[];
    entity_presence?: string[];
    shell_range?: [uint32, uint32];  // k_min to k_max
  };
  
  // AVMR-specific parameters
  search_radius?: uint32;       // shells to search (default: 1)
  echo_depth?: uint32;          // tailWeight depth (1-3, default: 2)
  resonance_boost?: float;        // weight for resonance bonus (default: 0.1)
  
  // Output
  top_k: uint32;
  min_score?: float;
}

// Example: "Find records in shells adjacent to query, with field coupling"
function executeAVMRSearch(query: AVMRSearchQuery): SearchResult {
  // 1. Get or compute AVMR state
  const queryAVMR = query.query_avmr_state ?? 
                    conceptVectorToAVMR(query.query_concept_vector);
  
  // 2. Determine shell search window
  const centerK = queryAVMR.shell.k;
  const radius = query.search_radius ?? 1;
  const shellsToSearch = range(centerK - radius, centerK + radius + 1);
  
  // 3. Collect candidates from shells
  const candidates = shellsToSearch
    .flatMap(k => shellIndex[k]?.record_ids ?? [])
    .filter(id => matchesFilter(id, query.filter_criteria));
  
  // 4. Build field at each candidate's position
  const maxN = Math.max(...candidates.map(id => getAVMRState(id).shell.n));
  
  // 5. Score with interaction + resonance
  const scored = candidates.map(id => {
    const candidate = getAVMRState(id);
    const field = buildFieldAt(candidate.shell.n, maxN, candidates.map(getAVMRState));
    const score = computeAVMRScore(queryAVMR, candidate, field);
    return { id, score, shell: candidate.shell.k };
  });
  
  // 6. Return top-k
  return scored
    .filter(r => r.score >= (query.min_score ?? 0))
    .sort((a, b) => b.score - a.score)
    .slice(0, query.top_k);
}
```

### 8.7 AVMR Invariants

```
∀ record with avmr_state:
  record.avmr_state.shell.n ≥ 0
  record.avmr_state.shell.k = floor(sqrt(record.avmr_state.shell.n))
  record.avmr_state.shell.a + record.avmr_state.shell.b = 2*k + 1
  record.avmr_state.mass = record.avmr_state.shell.a * record.avmr_state.shell.b
  record.avmr_state.polarity = record.avmr_state.shell.a - record.avmr_state.shell.b
  len(record.avmr_state.spectrum) = 8
  -3 ≤ record.avmr_state.phase ≤ 3
```

### 8.8 Comparison: Standard vs AVMR-Enhanced

| Feature | Standard (Cosine + HNSW) | AVMR-Enhanced |
|---------|---------------------------|---------------|
| **Indexing** | HNSW O(N) space | Shell index O(√N) space |
| **Search** | O(log N) ANN | O(√N) deterministic |
| **Similarity** | Cosine (angle only) | Interaction score (mass + polarity + spectrum) |
| **Aggregation** | None | mergeVec with resonance |
| **Theoretical basis** | Information theory | Spectral physics + braid topology |
| **Best for** | Large-scale ANN | Physics-rooted semantic clustering |

---

## 9. Bracketed/Witness Database Layer (Interval Semantics & Provenance Tracking)

**Purpose:** Apply bracket calculus (`BracketedDIAT`, `BraidBracket`) and witness structures to database operations for **interval queries**, **uncertainty bounds**, and **grounded provenance**. Derived from `Semantics/BracketedCalculus.lean` and `Semantics/Witness.lean`.

### 9.1 Bracketed Record Bounds

**Problem:** Standard databases store point values. Real-world semantic data has **uncertainty** — a record's concept activation is not a single float but a range with confidence bounds.

**Solution:** Store bracketed intervals for all scored fields:

```typescript
// Replace: concept_vector: [float; 14]
// With: bracketed concept bounds
interface BracketedConceptVector {
  // Each axis stored as [lower, value, upper] with gap conservation
  axes: {
    lower: Q16_16;    // conservative minimum
    value: Q16_16;    // measured/estimated value  
    upper: Q16_16;    // conservative maximum
    lowerGap: Q16_16; // value - lower
    upperGap: Q16_16; // upper - value
    prod: Q16_16;     // lowerGap * upperGap (uncertainty metric)
    scale: uint32;     // precision/derivation level
  }[14];
  
  // Invariant: lowerGap + upperGap = width for each axis
  gapConservation: bool[];  // checkGapConservation per axis
}

// Query using brackets: "find records where compression axis MAY exceed 0.8"
interface BracketedQuery {
  axis: uint32;           // which concept axis (0-13)
  minLower?: Q16_16;     // lower bound must exceed
  minValue?: Q16_16;     // value must exceed  
  minUpper?: Q16_16;     // upper bound must exceed (weakest)
  
  // Tolerance for approximate matches
  tolerance: Q16_16;     // max acceptable gap width
}
```

**Invariants from BracketedCalculus.lean:**
```
∀ axis in bracketed_vector.axes:
  axis.lowerGap + axis.upperGap = axis.upper - axis.lower  // gap conservation
  axis.prod = axis.lowerGap * axis.upperGap                  // uncertainty product
  
∀ query match:
  record.axes[query.axis].isInterior() ||  // value strictly inside bounds
  record.checkGapConservation()           // bounds are valid
```

### 9.2 Braid Bracket Provenance (Temporal Strands)

**Problem:** Linear provenance chains (manifest → manifest) lose the **braid structure** of real data evolution — multiple strands merging, crossing, diverging.

**Solution:** Track provenance as braid strands with bracket shells:

```typescript
interface BraidProvenance {
  // Each record is a "strand" with accumulated phase state
  strand_id: string;           // unique strand identifier
  slot: uint32;               // position in braid (like AVMR slot)
  
  // Phase accumulation from ancestor traversals
  phase_accumulator: {
    x: Q16_16;  // accumulated x-component (from PhaseVec)
    y: Q16_16;  // accumulated y-component
  };
  
  // Bracket shell: admissibility bounds for this strand
  bracket: {
    lower: Q16_16;     // minimum admissible phase magnitude
    upper: Q16_16;     // maximum admissible phase magnitude
    gap: Q16_16;       // upper - lower (admissibility window)
    kappa: Q16_16;     // norm approximation ||phase||
    phi: Q16_16;       // orientation/angle
    admissible: bool;  // lower ≤ upper (valid bracket)
  };
  
  // How this strand was formed
  formation: 
    | { type: "leaf", source: SourceType }                    // initial extraction
    | { type: "merge", parents: [strand_id, strand_id] }      // two strands combined
    | { type: "cross", parent: strand_id, crossing_id: string } // interaction event
    | { type: "evolution", parent: strand_id, op: OpCode };    // transformed
}

// AVMR-style entry for audit trail
interface BraidAttestationEntry {
  slot: uint32;
  phase_accumulator: PhaseVec;
  bracket: BraidBracket;
  residual?: BraidBracket;  // Some if from crossing/merge, None if leaf
  timestamp: uint64;
  archive_id: ArchiveID;
}
```

**Crossing Residual (from BraidBracket.lean:108-119):**

When two strands merge, compute their **interaction energy**:

```typescript
// R_ij = B_ij - (B_i + B_j)
// Measures semantic "tension" between merged records
function computeCrossingResidual(
  merged: BraidBracket,
  left: BraidBracket,
  right: BraidBracket
): BraidBracket {
  return {
    lower: merged.lower - (left.lower + right.lower),
    upper: merged.upper - (left.upper + right.upper),
    gap: merged.gap - (left.gap + right.gap),
    kappa: merged.kappa - (left.kappa + right.kappa),
    phi: merged.phi - (left.phi + right.phi),
    admissible: merged.admissible && left.admissible && right.admissible
  };
}

// Use residual for anomaly detection:
// Large residual = unexpected interaction, possible data corruption
```

### 9.3 Witness Receipts for Grounded Retrieval

**Problem:** Retrieved records lack **epistemic status** — is this observation? inference? evolution? What was the cognitive load?

**Solution:** Attach witness receipts to query results:

```typescript
interface WitnessedRecord {
  // Original record data
  record: EnhancedArchiveRecord;
  
  // Witness certification (from Witness.lean)
  witness: {
    witness_id: Nat;
    provenance: WitnessProvenance;  // observation | inference | evolution | ...
    
    // Path from query to this record
    path: {
      steps: AtomicPath[];  // query → result traversal
      isLawful: bool;       // path obeys semantic constraints
    };
    
    // Cognitive cost of retrieval (from CognitiveLoad)
    load: {
      intrinsic: float;      // L_I: entropy of path
      extraneous: float;     // L_E: overhead
      germane: float;        // L_G: useful computation
      total: float;
      efficiency: float;    // L_G / L_total
    };
    
    timestamp: float;
  };
  
  // What was preserved vs lost in retrieval
  atoms: {
    preserved: Atom[];  // semantic atoms retained
    lost: Atom[];       // atoms filtered/dropped
  };
  
  // Capability score: how well this result satisfies query
  result_capability: float;
}

// Query now returns witnessed results
interface WitnessedQueryResult {
  results: WitnessedRecord[];
  
  // Aggregate witness statistics
  summary: {
    total_load: float;
    average_efficiency: float;
    provenance_breakdown: Map<WitnessProvenance, uint32>;
    groundedness_checks: Groundedness[];  // §9.4
  };
}
```

**Provenance Types (from Witness.lean:11-18):**
```
observation    → Direct DB record retrieval
inference      → Derived via semantic similarity/vector match
projection     → Result of collapse/simplification (top-k truncation)
evolution      → Retrieved from evolved/updated record
translation    → Cross-source mapping (ChatGPT → SQLite schema alignment)
composed       → Built from atomic path composition (multi-hop graph search)
```

### 9.4 Groundedness Checks for Query Validity

**Problem:** How to verify that a query result is **semantically valid** and not hallucinated/approximated into nonsense?

**Solution:** Apply `Groundedness` structure from Witness.lean:58-78:

```typescript
interface GroundednessCheck {
  // 8 conditions for habitable semantic results
  atomic_basis: bool;        // Reducible to semantic atoms in our 14-axis space
  lawful_reachability: bool;  // Path from query obeys lawful atomic transitions
  bounded_load: bool;        // Cognitive load < threshold (not computationally absurd)
  faithful_projection: bool; // Collapse (top-k truncation) preserves meaning
  evolution_auditable: bool; // All changes from source are traceable
  universal_dynamics: bool;  // Result preserves universality class (not type confusion)
  scaling_preserved: bool;  // Scaling laws intact (small query → small result set)
  class_membership_visible: bool; // Can inspect which dynamical class result belongs to
}

// Combined check
def Groundedness.habitable(g: GroundednessCheck): bool {
  return g.atomic_basis && 
         g.lawful_reachability && 
         g.bounded_load &&
         g.faithful_projection && 
         g.evolution_auditable &&
         g.universal_dynamics &&
         g.scaling_preserved &&
         g.class_membership_visible;
}

// Use in query pipeline:
function executeGroundedQuery(query: SearchQuery): WitnessedQueryResult {
  const candidates = executeSearch(query);
  
  // Filter for groundedness
  const grounded = candidates.filter(r => 
    Groundedness.habitable(computeGroundedness(r, query))
  );
  
  // If too few grounded results, warn about possible semantic drift
  if (grounded.length < candidates.length * 0.5) {
    return {
      results: grounded,
      warning: "High semantic drift detected — many candidates failed groundedness checks",
      ungrounded_samples: candidates.filter(r => !Groundedness.habitable(...)).slice(0, 3)
    };
  }
  
  return { results: grounded };
}
```

### 9.5 Interval Temporal Queries (Bracketed Time)

**Problem:** Temporal queries use point timestamps. Real data has **uncertainty** — "extracted sometime between 3pm and 5pm".

**Solution:** Bracketed temporal bounds:

```typescript
interface BracketedTimestamp {
  earliest: ISOTimestamp;   // conservative earliest
  latest: ISOTimestamp;     // conservative latest
  nominal: ISOTimestamp;  // best estimate (like value in BracketedDIAT)
  
  // Uncertainty gaps
  past_gap: Duration;     // nominal - earliest
  future_gap: Duration;   // latest - nominal
  
  // Source of uncertainty
  precision: "exact" | "milliseconds" | "seconds" | "minutes" | "hours" | "derived";
}

// Temporal query with brackets
interface TemporalBracketQuery {
  // "Find records that MAY overlap with [start, end]"
  search_window: {
    start: BracketedTimestamp;
    end: BracketedTimestamp;
  };
  
  // Match criteria
  match_type: 
    | "definite_overlap"    // record.latest ≥ query.earliest AND record.earliest ≤ query.latest
    | "possible_overlap"    // record.latest ≥ query.earliest OR record.earliest ≤ query.latest
    | "definitely_before"   // record.latest < query.earliest (gap conservation check)
    | "definitely_after";   // record.earliest > query.latest
}
```

### 9.6 Database Integration Summary

| Bracket/Witness Concept | Database Enhancement | Source File |
|------------------------|---------------------|-------------|
| `BracketedDIAT` | Interval-valued concept vectors | `BracketedCalculus.lean` |
| `BraidBracket` | Strand-based provenance with admissibility | `BraidBracket.lean` |
| `crossingResidual` | Merge anomaly detection | `BraidBracket.lean:108` |
| `AVMREntry` | Append-only audit with phase/bracket | `BraidBracket.lean:124` |
| `WitnessReceipt` | Epistemic status tracking | `Witness.lean:21` |
| `Groundedness` | Query result validity verification | `Witness.lean:58` |
| `PhaseVec` | 2D phase accumulation for traversal cost | `BraidBracket.lean:17` |

### 9.7 Example: Grounded Semantic Search

```typescript
// Execute search with full bracket/witness machinery
function groundedSemanticSearch(query: string): WitnessedQueryResult {
  // 1. Extract bracketed concept vector (with uncertainty)
  const queryConcept = extractBracketedConceptVector(query);
  // → { axes: [{lower: 0.6, value: 0.85, upper: 0.9, ...}, ...] }
  
  // 2. AVMR shell-based candidate retrieval
  const candidates = executeAVMRSearch({
    query_concept_vector: queryConcept.axes.map(a => a.value),
    top_k: 50
  });
  
  // 3. Bracketed similarity: allow matches within uncertainty bounds
  const bracketedMatches = candidates.filter(c => 
    cosineSimilarity(queryConcept, c.bracketed_concept) > 0.7
  );
  
  // 4. Witness each result
  const witnessed = bracketedMatches.map(c => ({
    record: c,
    witness: {
      witness_id: generateWitnessId(),
      provenance: "inference",  // derived via vector similarity
      path: computePath(query, c),
      load: computeCognitiveLoad(query, c),
      timestamp: now()
    },
    atoms: { preserved: c.entities, lost: [] },
    result_capability: computeCapability(query, c)
  }));
  
  // 5. Groundedness filter
  const grounded = witnessed.filter(w => 
    Groundedness.habitable(computeGroundedness(w, query))
  );
  
  // 6. Braid attestation for audit trail
  const attestation = createBraidAttestation({
    slot: getNextSlot(),
    phase_accumulator: accumulatePhase(witnessed.map(w => w.witness.path)),
    bracket: computeBracketFromResults(grounded),
    residual: computeCrossingResidualFromQuery(query, grounded)
  });
  
  return {
    results: grounded,
    summary: {
      total_load: sum(grounded.map(w => w.witness.load.total)),
      groundedness_rate: grounded.length / candidates.length,
      attestation
    }
  };
}
```

---

## 10. PBACS/Compression Database Layer (Constraint-Based Storage)

**Purpose:** Apply PBACS (Physics-Based Addressable Compression System) and Unified Compression to database storage for **content-addressed encoding**, **thermodynamic cost tracking**, and **constraint-based retrieval**. Derived from `Semantics/Pbacs.lean` and `ExtensionScaffold/Compression/UnifiedCompression.lean`.

### 10.1 Content-Addressed Compression Encoding

**Problem:** Standard databases store raw bytes. PBACS provides **constraint-based encoding** where content determines its own storage address through thermodynamic-valid encoding steps.

**Solution:** Store records with their PBACS encoding trace:

```typescript
interface PBACSEncodedRecord {
  // Original content (for retrieval)
  raw_content: JSONValue;
  
  // PBACS encoding trace (from Pbacs.lean)
  encoding: {
    // 8-step canonical loop execution
    steps: PBACSStep[];
    
    // Final encoded representation
    encoded_bytes: UInt8[];  // Compressed form
    
    // Content-addressed hash (address = encoding result)
    content_address: SHA256Hex;  // SHA256(encoded_bytes)
    
    // Encoding cost (thermodynamic work required)
    total_cost: Q16_16;  // Σ binding costs per step
    
    // Constraint satisfaction log
    constraints_satisfied: {
      arithmetic: bool;   // Shell coordinates valid
      geometric: bool;    // 3-point contact detected
      temporal: bool;     // φ-accumulation valid
      field: bool;        // Standing-wave field built
      contact: bool;      // κ_A ∧ κ_B ∧ κ_C closure
    };
  };
}

// Single PBACS step (from Pbacs.lean:22-38)
interface PBACSStep {
  t: uint32;                    // Step index
  
  // Shell coordinates (from AVMR)
  shell: { n: uint32; k: uint32; a: uint32; b: uint32 };
  
  // Pulse generation (from UnifiedCompression.lean:44-54)
  pulse: {
    mode: "a" | "g" | "c" | "t" | "square";  // TriangleMode
    mass: UInt32;           // ab product
    polarity: Int32;        // a - b
    width: uint32;          // 2k+1
  };
  
  // Field interaction
  field_interaction: {
    support_values: [UInt32, UInt32, UInt32];  // [κ_A, κ_B, κ_C]
    echo_weights: [Q16_16, Q16_16, Q16_16];    // [1, ½, ¼]
    interaction_score: Int;  // J(n) = ab·F_m + (a-b)·F_p + ⟨χ, F_c⟩
  };
  
  // Emission decision
  emission: {
    gate_closed: bool;      // κ_A ∧ κ_C ∧ J>0
    symbol_emitted: UInt8;  // 4-bit nibble or 8-bit byte
    binding_cost: Q16_16;   // Cost to bind this symbol
  };
  
  // Control state (from Pbacs.lean:88-100)
  control: {
    state: "halt" | "hold" | "stable" | "transient";
    score: Q16_16;          // Weighted projection score
    alpha_t: Q16_16;        // Learning rate at step t
  };
}
```

**Encoding Pipeline (UnifiedCompression.lean:16-22):**

```
X → G_θ{πᵢ} →contact→ {χᵢ} →g→ {eᵢ} →Λ→ {zᵢ} →bind→ L(X)

Where:
  X: Input record content
  G_θ: Generate structured pulses from shell coordinates
  contact: Detect 3-point contact (κ_A, κ_B, κ_C)
  g: Emission gate (κ_A ∧ κ_C ∧ J>0)
  eᵢ: Emitted symbols
  Λ: Constraint validation
  zᵢ: Constrained codes
  bind: Lawful binding (cost accumulation)
  L(X): Final compressed representation
```

### 10.2 Thermodynamic Cost Tracking

**Problem:** Database operations consume resources. PBACS tracks **thermodynamic work** (Landauer-bound relevant) per operation.

**Solution:** Attach cost metrics to all storage and retrieval:

```typescript
interface ThermodynamicCost {
  // Per-operation costs (Q16.16 fixed-point)
  encoding_cost: Q16_16;      // Cost to compress/store
  retrieval_cost: Q16_16;     // Cost to decompress/read
  transmission_cost: Q16_16;  // Cost to move over network
  
  // Landauer-bound theoretical minimum
  landauer_limit: Q16_16;    // kT ln(2) per bit erased
  
  // Efficiency ratio
  efficiency: Q16_16;         // landauer_limit / actual_cost
  
  // Cost breakdown by component
  breakdown: {
    pulse_generation: Q16_16;
    field_construction: Q16_16;
    contact_detection: Q16_16;
    emission_gating: Q16_16;
    binding_accumulation: Q16_16;
  };
}

// Attach to archive records
interface CostAwareArchiveRecord extends EnhancedArchiveRecord {
  storage_cost: ThermodynamicCost;
  
  // Cost-weighted retrieval priority
  // Cheaper-to-retrieve records preferred when equivalent
  retrieval_score: Q16_16;  // semantic_score / storage_cost.encoding_cost
}
```

**Cost Invariant (from BracketedCalculus gap conservation):**

```
∀ encoding step:
  step.emission.binding_cost > 0  // Positive cost to emit
  step.field_interaction.interaction_score ≥ threshold  // Gate threshold
  
∀ complete encoding:
  encoding.total_cost = Σ steps[i].emission.binding_cost
  encoding.total_cost ≥ encoding.landauer_limit  // 2nd law respect
```

### 10.3 Constraint-Based Retrieval (PBACS Control)

**Problem:** Standard queries return all matches. PBACS provides **hysteretic control** — stateful filtering with entry/exit thresholds.

**Solution:** Apply PBACS control state machine to query processing:

```typescript
// PBACS Control State (from Pbacs.lean)
enum ControlState {
  HALT,      // Below entry threshold, not processing
  HOLD,      // Within hysteresis band, maintaining state
  STABLE,    // Confident match, proceed
  TRANSIENT  // Uncertain, require more samples
}

// Query with PBACS control
interface PBACSControlledQuery {
  // Standard query parameters
  filter: SearchFilter;
  
  // PBACS control parameters (from Pbacs.lean:11-20)
  control_config: {
    entry_thresholds: {
      halt_tau: Q16_16;        // Start processing if score >
      dmt_product: Q16_16;     // Dual-mode threshold
      hold_delta_dot: Q16_16;  // Rate-of-change entry
      hold_delta: Q16_16;      // Absolute delta entry
    };
    exit_thresholds: {
      halt_tau: Q16_16;        // Stop processing if score <
      dmt_product: Q16_16;
      hold_delta_dot: Q16_16;
      hold_delta: Q16_16;
    };
    // Hysteresis prevents oscillation
    hysteresis_gap: Q16_16;     // entry - exit > 0
    
    // Adaptive learning rate
    alpha0: Q16_16;           // Base learning rate
    beta: Q16_16;              // Decay factor
  };
  
  // Current control state
  control_state: ControlState;
  
  // Accumulated score (hysteresis memory)
  accumulated_score: Q16_16;
}

// PBACS query execution
function executePBACSQuery(query: PBACSControlledQuery): QueryResult {
  const results = [];
  let state = query.control_state;
  let acc = query.accumulated_score;
  
  for (const candidate of streamCandidates(query.filter)) {
    // Compute projection scores (from Pbacs.lean:77-78)
    const projections = computeProjections(candidate, query.filter);
    const score = computeWeightedScore(projections, query.control_config);
    
    // Update control state with hysteresis
    const newState = nextControlState(
      query.control_config,
      state,
      score,
      acc
    );
    
    // Collect results based on state
    if (newState === ControlState.STABLE) {
      results.push({ candidate, score, confidence: "high" });
    } else if (newState === ControlState.HOLD && state !== ControlState.HALT) {
      results.push({ candidate, score, confidence: "medium" });
    }
    
    // Early termination if HALT and sufficient samples
    if (newState === ControlState.HALT && results.length > 10) {
      break;
    }
    
    state = newState;
    acc = Q16_16.add(acc, Q16_16.mul(score, query.control_config.alpha0));
  }
  
  return {
    results,
    final_state: state,
    accumulated_score: acc,
    termination_reason: state === ControlState.HALT ? "threshold" : "exhausted"
  };
}
```

**Hysteretic Entry/Exit (from Pbacs.lean:88-100):**

```
Entry condition (any must hold):
  u_tau > entry.halt_tau
  u_tau * u_chi > entry.dmt_product
  |delta_dot| > entry.hold_delta_dot
  |delta| > entry.hold_delta

Exit condition (any must hold):
  u_tau < exit.halt_tau
  u_tau * u_chi < exit.dmt_product
  ...

Invariant: entry.threshold > exit.threshold (hysteresis gap)
```

### 10.4 Addressable Compression Storage

**Problem:** Content-addressed storage (like a Merkle tree) doesn't track encoding costs or constraint satisfaction.

**Solution:** PBACS-enhanced content addressing with verification:

```typescript
// Addressable storage with PBACS verification
interface PBACSAddressableStorage {
  // Content-derived address
  address: SHA256Hex;  // Hash of PBACS-encoded content
  
  // Storage entry
  entry: {
    raw_content: JSONValue;
    encoding_trace: PBACSStep[];
    encoded_bytes: UInt8[];
    
    // Verification that encoding is valid
    verification: {
      constraint_hash: SHA256Hex;  // Hash of satisfied constraints
      cost_verification: bool;    // total_cost matches sum
      landauer_compliance: bool;  // total_cost ≥ landauer_limit
    };
  };
  
  // Lookup index: content_hash → address
  content_index: Map<SHA256Hex, SHA256Hex>;
  
  // Deduplication: identical content → same address
  deduplication_stats: {
    unique_entries: uint32;
    total_references: uint32;
    compression_ratio: float;  // raw_size / encoded_size
  };
}

// Storage operation with cost tracking
function storeWithPBACS(content: JSONValue): StorageResult {
  // 1. Encode with PBACS
  const encoding = pbacsEncode(content);
  
  // 2. Compute content address
  const address = SHA256(encoding.encoded_bytes);
  
  // 3. Verify constraints
  const verification = {
    constraint_hash: SHA256(encoding.constraints_satisfied),
    cost_verification: verifyCostSum(encoding.steps, encoding.total_cost),
    landauer_compliance: encoding.total_cost >= computeLandauerLimit(encoding.encoded_bytes.length)
  };
  
  // 4. Store if valid
  if (verification.cost_verification && verification.landauer_compliance) {
    storage[address] = { raw_content: content, encoding_trace: encoding.steps, ... };
    return { success: true, address, cost: encoding.total_cost };
  } else {
    return { success: false, error: "constraint_violation", verification };
  }
}
```

### 10.5 Temporal Buffer for Streaming Queries

**Problem:** Database queries are stateless. PBACS provides **temporal accumulation** for streaming/continuous queries.

**Solution:** Add temporal buffer state to long-running queries:

```typescript
// Temporal buffer (from Orchestrate.lean:23-91)
interface TemporalBuffer {
  history: CanonicalState[];    // Recent query states
  history_size: uint32;        // Buffer capacity
  
  // Temporal derivatives (from delta, delta_dot, gamma)
  prev_delta: Option<Q16_16>;   // Previous φ-difference
  prev_phi: Option<Q16_16>;    // Previous accumulated phase
  prev_2phi: Option<Q16_16>;   // φ at t-2
  
  // Angular momentum (change in change)
  angular_momentum: Q16_16;      // |φ_t-1 · (δ_t - δ_t-1)|
  
  // Step counter
  step_count: uint32;
}

// Streaming query with temporal state
interface StreamingPBACSQuery {
  // Static filter
  filter: SearchFilter;
  
  // Temporal state (accumulated across chunks)
  temporal: TemporalBuffer;
  
  // Trigger conditions for re-evaluation
  triggers: {
    on_angular_momentum: Q16_16;  // Re-query if momentum > threshold
    on_gamma_spike: Q16_16;     // Re-query if acceleration > threshold
    on_state_divergence: float;   // Re-query if state drifts
  };
}

// Update temporal buffer with new state
function updateTemporalBuffer(
  buffer: TemporalBuffer,
  new_state: CanonicalState
): TemporalBuffer {
  // Compute delta = φ_t - φ_t-1
  const delta = Q16_16.sub(new_state.phi, buffer.prev_phi);
  
  // Compute delta_dot = delta_t - delta_t-1
  const delta_dot = buffer.prev_delta 
    ? Q16_16.sub(delta, buffer.prev_delta)
    : Q16_16.zero;
  
  // Compute gamma = |φ_t - 2·φ_t-1 + φ_t-2|
  const gamma = (buffer.prev_phi && buffer.prev_2phi)
    ? Q16_16.abs(Q16_16.sub(
        new_state.phi,
        Q16_16.add(buffer.prev_phi, buffer.prev_phi)  // 2·φ_t-1
      ), buffer.prev_2phi)
    : Q16_16.zero;
  
  // Compute angular momentum
  const angular_momentum = buffer.history.length >= 2
    ? computeAngularMomentum(
        buffer.history[1],  // t-2
        buffer.history[0],  // t-1
        new_state          // t
      )
    : Q16_16.zero;
  
  return {
    history: [new_state, ...buffer.history].slice(0, buffer.history_size),
    history_size: buffer.history_size,
    prev_delta: some(delta),
    prev_phi: some(new_state.phi),
    prev_2phi: buffer.prev_phi,
    angular_momentum,
    step_count: buffer.step_count + 1
  };
}
```

### 10.6 Integration Summary: PBACS + Database

| PBACS Concept | Database Enhancement | Source File |
|---------------------|----------------------|-------------|
| `Pbacs` control runtime | Hysteretic query processing | `Pbacs.lean` |
| `StepTrace` | Encoding trace with cost per step | `Pbacs.lean:22` |
| `UnifiedCompression` | Content-addressed encoding | `UnifiedCompression.lean` |
| `Pulse` | Shell-based pulse generation | `UnifiedCompression.lean:44` |
| `Contact` | 3-point constraint validation | `UnifiedCompression.lean:63` |
| `echoWeights` [1,½,¼] | Standing-wave field construction | `UnifiedCompression.lean:77` |
| `TemporalBuffer` | Streaming query state | `Orchestrate.lean:23` |
| `CanonicalState` | Accumulated query phase state | `Canon.lean` |
| `ControlState` | HALT/HOLD/STABLE/TRANSIENT gates | `Pbacs.lean:88` |

### 10.7 Complete Example: PBACS-Enhanced Storage

```typescript
// Store a research record with full PBACS encoding
async function storeResearchRecord(record: ResearchRecord): Promise<StorageReceipt> {
  // 1. Extract concept vector for shell coordinates
  const concept = extractConceptVector(record.text);
  
  // 2. Map to AVMR shell (n, k, a, b)
  const shell = conceptVectorToShell(concept);
  
  // 3. PBACS encode with constraint tracking
  const encoding = pbacsEncode(record, {
    shell,
    echo_depth: 2,
    emission_threshold: 0x00008000  // 0.5 in Q16.16
  });
  
  // 4. Compute content address
  const content_address = SHA256(encoding.encoded_bytes);
  
  // 5. Verify thermodynamic compliance
  const landauer = computeLandauerLimit(encoding.encoded_bytes.length);
  if (encoding.total_cost < landauer) {
    throw new Error("Landauer bound violated — encoding invalid");
  }
  
  // 6. Store with full trace
  const entry: PBACSAddressableStorage = {
    address: content_address,
    entry: {
      raw_content: record,
      encoding_trace: encoding.steps,
      encoded_bytes: encoding.encoded_bytes,
      verification: {
        constraint_hash: SHA256(encoding.constraints_satisfied),
        cost_verification: true,
        landauer_compliance: true
      }
    },
    content_index: new Map([[record.content_hash, content_address]]),
    deduplication_stats: {
      unique_entries: 1,
      total_references: 1,
      compression_ratio: record.text.length / encoding.encoded_bytes.length
    }
  };
  
  // 7. Return receipt with cost
  return {
    address: content_address,
    storage_cost: encoding.total_cost,
    landauer_limit: landauer,
    efficiency: Q16_16.div(landauer, encoding.total_cost),
    constraint_satisfaction: encoding.constraints_satisfied
  };
}
```

---

## 11. Wormhole Throat Physics Layer (Topological Shortcuts)

**Purpose:** Model semantic graph traversals as **wormhole throat physics** — shortcuts through the manifold that bypass normal path distance. Derived from `ExtensionScaffold/Topology/Wormhole.lean` and `ExtensionScaffold/Thermodynamics/ThroatPhysics.lean`.

### 11.1 Core Throat Physics Model

**Physical Analogy:** In general relativity, a wormhole throat connects distant spacetime regions. In ENE, this represents **semantic shortcuts** — direct links between records that skip intermediate graph traversals.

```typescript
// Wormhole mouth: entry/exit point of the shortcut
interface WormholeMouth {
  location: ManifoldPoint;      // Position in semantic manifold
  aperture: Q16_16;             // Throat radius (Q16.16: minSafeAperture = 0.001)
  tidalStress: Q16_16;         // Gradient of potential (maxTidalStress = 10.0)
  chronologyProtection: bool;    // Prevents time-travel paradoxes
}

// Throat stability states (from Wormhole.lean:13-19)
enum ThroatStability {
  COLLAPSED,      // Singularity — non-traversable
  FLUCTUATING,    // Unstable — probabilistic traversal
  STABLE,         // Consistent bidirectional passage
  CRYSTALLINE,    // Perfectly preserved geodesic
  RESONANT        // Actively amplified by external field
}

// Complete wormhole throat structure
interface WormholeThroat {
  // Mouths at each end
  mouthA: WormholeMouth;
  mouthB: WormholeMouth;
  
  // Geometry
  properLength: uint64;        // Through-throat distance (often << manifold distance)
  
  // Physics state
  stability: ThroatStability;
  exoticMatter: Q16_16;         // Negative energy density required (0 = none needed)
  
  // Information capacity
  fluxCapacity: Q16_16;         // Maximum information flux per unit time
  resonanceFreq: Q16_16;        // Natural oscillation frequency
  bidirectional: bool;           // True if traversable both ways equally
}
```

**Key Physical Constraints (from Wormhole.lean:47-61):**

```
Safe traversal requires:
  aperture > minSafeAperture (0.001 in Q16.16)
  tidalStress < maxTidalStress (10.0 in Q16.16)
  stability ∈ {stable, crystalline, resonant}
  payloadSize ≤ fluxCapacity
```

### 11.2 Throat Regime Quantization

**Problem:** Continuous throat physics needs discrete states for database indexing.

**Solution:** Quantized throat regimes from `ThroatPhysics.lean`:

```typescript
// Input loads that determine throat state (from ThroatPhysics.lean:46-59)
interface QuantizedThroatInput {
  // Physical loads
  pinchLoad: Q16_16;           // Pressure toward collapse
  collapseLoad: Q16_16;        // Critical destabilization force
  boundaryLoad: Q16_16;        // Boundary pressure
  
  // Counts affecting stability
  rejectCount: uint32;         // Rejected traversals (weakens throat)
  channelCount: uint32;        // Active channels
  branchCount: uint32;         // Branching complexity
  gateCount: uint32;          // Control gates
  
  // Regime classifications
  mediumRegime: MediumRegime;
  manifoldRegime: PlasmaManifoldRegime;
  topologyRegime: PlasmaTopologyRegime;
  invariantSurvivor: PlasmaTopologyInvariantSurvivor;
  stabilityClass: StabilityClass;
}

// Discrete throat regimes (from ThroatPhysics.lean:61-66)
enum ThroatRegime {
  OPEN_CHANNEL,  // Unrestricted flow
  PINCH,         // Constricted but open
  THROAT,        // Minimal viable channel
  COLLAPSE       // Non-traversable
}

// Stability class bias factors (from ThroatPhysics.lean:73-79)
// Added to loads for regime determination
const STABILITY_BIAS: Record<StabilityClass, Q16_16> = {
  stable: 0.25,       // quarter
  singular: 3.0,      // three
  throat: 1.0,        // one
  unstable: 0.5,      // half
  collapsed: 2.0      // two
};

// Regime quantization function (from ThroatPhysics.lean:90-96)
function quantizeThroat(input: QuantizedThroatInput): ThroatRegime {
  const pinchIndex = input.pinchLoad + STABILITY_BIAS[input.stabilityClass];
  const collapseGradient = input.collapseLoad + STABILITY_BIAS[input.stabilityClass];
  const boundaryPressure = input.boundaryLoad + STABILITY_BIAS[input.stabilityClass];
  
  // Thresholds in Q16.16
  if (pinchIndex > 2.0) return ThroatRegime.PINCH;        // 131072
  if (collapseGradient > 1.0) return ThroatRegime.COLLAPSE; // 65536
  if (boundaryPressure > 0.5) return ThroatRegime.THROAT;   // 32768
  return ThroatRegime.OPEN_CHANNEL;
}
```

### 11.3 Semantic Graph as Wormhole Network

**Database Application:** Model semantic links as traversable wormholes:

```typescript
// Semantic record positioned in manifold
interface ManifoldPoint {
  coords: Q16_16[];      // Fixed-point coordinates (1-16 dimensions)
  dimension: uint32;     // Manifold dimension (1-16)
}

// Map archive record to manifold position
interface PositionedRecord extends EnhancedArchiveRecord {
  manifold_position: ManifoldPoint;
  
  // Shell coordinates from AVMR give natural manifold embedding
  // n (shell position) → one manifold dimension
  // k (shell index) → another dimension
  // (a,b) tip coordinates → 2D submanifold
}

// Throat network: adjacency list of shortcuts
interface ThroatNetwork {
  throats: WormholeThroat[];
  
  // Index by mouth location for fast lookup
  locationIndex: Map<ManifoldPoint, WormholeThroat[]>;
}

// Find traversable shortcuts from a record
function findSemanticShortcuts(
  network: ThroatNetwork,
  fromRecord: PositionedRecord,
  payloadSize: Q16_16
): WormholeThroat[] {
  return network.throats.filter(throat =>
    (throat.mouthA.location == fromRecord.manifold_position ||
     throat.mouthB.location == fromRecord.manifold_position) &&
    throat.traversable(payloadSize)
  );
}
```

### 11.4 Shortcut Efficiency Metrics

**Key insight:** Wormholes provide value when `properLength << manifoldDistance`.

```typescript
// Efficiency computation (from Wormhole.lean:68-73)
function computeThroatEfficiency(
  throat: WormholeThroat,
  manifoldDistance: uint64
): Q16_16 {
  if (throat.properLength == 0) return 0;  // Singular
  
  // η = manifold_distance / throat_length (Q16.16 ratio)
  return (manifoldDistance / throat.properLength) * 65536;
}

// Distance saved (from Wormhole.lean:64-65)
function computeShortcut(
  throat: WormholeThroat,
  manifoldDistance: uint64
): int64 {
  return manifoldDistance - throat.properLength;
}

// Traversal cost (from Wormhole.lean:76-83)
function computeTraversalCost(throat: WormholeThroat): Q16_16 {
  const stabilityPenalty: Record<ThroatStability, Q16_16> = {
    collapsed: 65535.999,    // 0xFFFFFFFF - effectively infinite
    fluctuating: 8.0,      // 0x00080000
    stable: 1.0,             // 0x00010000
    crystalline: 0.5,        // 0x00008000
    resonant: 0.25           // 0x00004000 (externally supported)
  };
  
  return throat.exoticMatter + stabilityPenalty[throat.stability];
}

// Optimal path selection considering wormholes
interface PathSelection {
  // Standard graph path (many hops)
  graphPath: {
    hops: uint32;
    totalDistance: uint64;
    cumulativeCost: Q16_16;
  };
  
  // Wormhole shortcut (if available)
  wormholePath?: {
    throat: WormholeThroat;
    shortcutLength: uint64;
    traversalCost: Q16_16;
    efficiency: Q16_16;
  };
  
  // Optimal choice
  optimal: 'graph' | 'wormhole' | 'hybrid';
  savings: Q16_16;  // Cost difference
}
```

### 11.5 Throat Dynamics for Streaming Queries

**Application:** As query state evolves, throat stability may change:

```typescript
// Throat state evolution (combines with TemporalBuffer from §10)
interface ThroatDynamics {
  // Current state
  currentRegime: ThroatRegime;
  currentStability: ThroatStability;
  
  // Historical loads (for trend analysis)
  loadHistory: {
    pinchLoad: Q16_16[];
    collapseLoad: Q16_16[];
    boundaryLoad: Q16_16[];
  };
  
  // Predictive thresholds
  predictiveCollapse: bool;    // Trending toward collapse
  pinchImminent: bool;        // Approaching pinch threshold
  
  // Reactive control
  stabilizeAction?: {
    injectExoticMatter: Q16_16;  // Add negative energy
    reduceFlux: Q16_16;           // Throttle throughput
    reinforceGate: bool;          // Add control gates
  };
}

// Monitor throat health during long-running queries
function monitorThroatHealth(
  throat: WormholeThroat,
  dynamics: ThroatDynamics,
  queryLoad: Q16_16
): ThroatHealth {
  const regime = quantizeThroat({
    pinchLoad: queryLoad,
    collapseLoad: dynamics.loadHistory.collapseLoad[dynamics.loadHistory.collapseLoad.length - 1],
    boundaryLoad: dynamics.loadHistory.boundaryLoad[dynamics.loadHistory.boundaryLoad.length - 1],
    rejectCount: 0,
    channelCount: 1,
    branchCount: 1,
    gateCount: 1,
    // ... other fields
  });
  
  return {
    traversable: regime != ThroatRegime.COLLAPSE,
    regime,
    recommendedAction: regime == ThroatRegime.PINCH 
      ? 'reduce_flux' 
      : regime == ThroatRegime.THROAT 
        ? 'stabilize' 
        : 'continue'
  };
}
```

### 11.6 Integration with Other Layers

| Throat Concept | Integration | Source |
|-----------------|-------------|--------|
| `ManifoldPoint` | Embeds AVMR shell coordinates | `Wormhole.lean:22` |
| `ThroatStability` | Maps to PBACS `ControlState` | `Wormhole:13`, `Pbacs:88` |
| `fluxCapacity` | Thermodynamic cost constraint | `Wormhole:42`, `ThroatPhysics:47` |
| `exoticMatter` | Resource budget from `ThermodynamicCost` | `Wormhole:41`, `§10.2` |
| `resonanceFreq` | Connects to AVMR spectral overlap | `Wormhole:43`, `AVMR.lean:141` |
| `ThroatRegime` | Query routing decisions | `ThroatPhysics:61` |

### 11.7 Complete Example: Throat-Aware Graph Query

```typescript
// Execute query using wormhole shortcuts when available
async function executeThroatAwareQuery(
  query: SearchQuery,
  network: ThroatNetwork
): Promise<QueryResult> {
  // 1. Position query in manifold (AVMR shell coordinates)
  const queryPosition = conceptVectorToManifoldPoint(
    extractConceptVector(query.text)
  );
  
  // 2. Find candidate records via standard graph search
  const graphCandidates = await graphSearch(query, maxHops: 3);
  
  // 3. Find wormhole shortcuts from query position
  const shortcuts = findSemanticShortcuts(
    network,
    { manifold_position: queryPosition } as PositionedRecord,
    payloadSize: estimateQueryComplexity(query)  // Q16_16
  );
  
  // 4. Evaluate each shortcut
  const shortcutResults = shortcuts.map(throat => {
    const destination = throat.mouthA.location == queryPosition 
      ? throat.mouthB.location 
      : throat.mouthA.location;
    
    // Records near destination mouth
    const nearbyRecords = findRecordsNear(destination, radius: 0.1);
    
    return {
      throat,
      records: nearbyRecords,
      efficiency: computeThroatEfficiency(
        throat,
        estimateManifoldDistance(queryPosition, destination)
      ),
      cost: computeTraversalCost(throat),
      traversable: throat.traversable(estimateQueryComplexity(query))
    };
  }).filter(s => s.traversable);
  
  // 5. Merge results: graph path + wormhole shortcuts
  const allCandidates = [
    ...graphCandidates.map(c => ({ source: 'graph', record: c, cost: c.hops * 65536 })),
    ...shortcutResults.flatMap(s => 
      s.records.map(r => ({ 
        source: 'wormhole', 
        record: r, 
        cost: s.cost,
        efficiency: s.efficiency 
      }))
    )
  ];
  
  // 6. Score and rank
  const scored = allCandidates.map(c => ({
    ...c,
    score: semanticSimilarity(query, c.record) / c.cost
  })).sort((a, b) => b.score - a.score);
  
  return {
    results: scored.slice(0, query.top_k),
    pathAnalysis: {
      graph_hits: graphCandidates.length,
      wormhole_hits: shortcutResults.length,
      average_wormhole_efficiency: average(shortcutResults.map(s => s.efficiency))
    }
  };
}
```

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0 | 2026-04-18 | Added Wormhole Throat Physics Layer (§11) for topological shortcuts |
| 1.2.0 | 2026-04-18 | Added PBACS/Compression Database Layer (§10) |
| 1.1.0 | 2026-04-18 | Added AVMR-Enhanced Vector Layer (§8) and Bracketed/Witness Database Layer (§9) |
| 1.0.0 | 2026-04-18 | Initial formal specification |

---

## 13. Machine-Checkable Schema (JSON Schema Draft)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "ene_schema_v1.0.0",
  
  "definitions": {
    "SHA256Hex": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "ConceptVector14": {
      "type": "array",
      "minItems": 14,
      "maxItems": 14,
      "items": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
    },
    "VerificationStatus": {
      "type": "string",
      "enum": ["pending", "verified", "failed"]
    },
    "SourceType": {
      "type": "string", 
      "enum": ["sqlite", "sql_insert", "json_catalog", "chatgpt", "legacy_lean"]
    },
    "Q16_16": {
      "type": "integer",
      "description": "Fixed-point Q16.16 representation (multiply by 65536)"
    },
    "AVMRShell": {
      "type": "object",
      "properties": {
        "n": { "type": "integer", "minimum": 0 },
        "k": { "type": "integer", "minimum": 0 },
        "a": { "type": "integer", "minimum": 0 },
        "b": { "type": "integer", "minimum": 0 }
      },
      "required": ["n", "k", "a", "b"]
    },
    "AVMRState": {
      "type": "object",
      "properties": {
        "shell": { "$ref": "#/definitions/AVMRShell" },
        "mass": { "type": "integer" },
        "polarity": { "type": "integer" },
        "spectrum": {
          "type": "array",
          "minItems": 8,
          "maxItems": 8,
          "items": { "$ref": "#/definitions/Q16_16" }
        },
        "interaction": { "$ref": "#/definitions/Q16_16" },
        "phase": { "type": "integer", "minimum": -3, "maximum": 3 },
        "resonance_count": { "type": "integer", "minimum": 0 },
        "priority_bias": { "type": "integer" },
        "derived_from": {
          "type": "string",
          "enum": ["concept_vector", "text_embedding", "direct"]
        },
        "generation_timestamp": { "type": "string" }
      },
      "required": ["shell", "mass", "polarity", "spectrum", "phase"]
    },
    "BracketedConceptAxis": {
      "type": "object",
      "properties": {
        "lower": { "$ref": "#/definitions/Q16_16" },
        "value": { "$ref": "#/definitions/Q16_16" },
        "upper": { "$ref": "#/definitions/Q16_16" },
        "lowerGap": { "$ref": "#/definitions/Q16_16" },
        "upperGap": { "$ref": "#/definitions/Q16_16" },
        "prod": { "$ref": "#/definitions/Q16_16" },
        "scale": { "type": "integer", "minimum": 0 }
      },
      "required": ["lower", "value", "upper"]
    },
    "BracketedConceptVector": {
      "type": "object",
      "properties": {
        "axes": {
          "type": "array",
          "minItems": 14,
          "maxItems": 14,
          "items": { "$ref": "#/definitions/BracketedConceptAxis" }
        },
        "gapConservation": {
          "type": "array",
          "minItems": 14,
          "maxItems": 14,
          "items": { "type": "boolean" }
        }
      },
      "required": ["axes"]
    },
    "WitnessProvenance": {
      "type": "string",
      "enum": ["observation", "inference", "projection", "evolution", "translation", "composed"]
    },
    "CognitiveLoad": {
      "type": "object",
      "properties": {
        "intrinsic": { "type": "number" },
        "extraneous": { "type": "number" },
        "germane": { "type": "number" },
        "total": { "type": "number" },
        "efficiency": { "type": "number" }
      }
    },
    "WitnessReceipt": {
      "type": "object",
      "properties": {
        "witness_id": { "type": "integer", "minimum": 0 },
        "provenance": { "$ref": "#/definitions/WitnessProvenance" },
        "timestamp": { "type": "number" },
        "load": { "$ref": "#/definitions/CognitiveLoad" }
      },
      "required": ["witness_id", "provenance"]
    },
    "BraidBracket": {
      "type": "object",
      "properties": {
        "lower": { "$ref": "#/definitions/Q16_16" },
        "upper": { "$ref": "#/definitions/Q16_16" },
        "gap": { "$ref": "#/definitions/Q16_16" },
        "kappa": { "$ref": "#/definitions/Q16_16" },
        "phi": { "$ref": "#/definitions/Q16_16" },
        "admissible": { "type": "boolean" }
      },
      "required": ["lower", "upper", "gap", "kappa", "admissible"]
    },
    "PhaseVec": {
      "type": "object",
      "properties": {
        "x": { "$ref": "#/definitions/Q16_16" },
        "y": { "$ref": "#/definitions/Q16_16" }
      },
      "required": ["x", "y"]
    },
    "ControlState": {
      "type": "string",
      "enum": ["halt", "hold", "stable", "transient"]
    },
    "PBACSPulse": {
      "type": "object",
      "properties": {
        "mode": { "type": "string", "enum": ["a", "g", "c", "t", "square"] },
        "mass": { "type": "integer", "minimum": 0 },
        "polarity": { "type": "integer" },
        "width": { "type": "integer", "minimum": 0 }
      },
      "required": ["mode", "mass", "polarity", "width"]
    },
    "PBACSEmission": {
      "type": "object",
      "properties": {
        "gate_closed": { "type": "boolean" },
        "symbol_emitted": { "type": "integer", "minimum": 0, "maximum": 255 },
        "binding_cost": { "$ref": "#/definitions/Q16_16" }
      }
    },
    "PBACSStep": {
      "type": "object",
      "properties": {
        "t": { "type": "integer", "minimum": 0 },
        "shell": { "$ref": "#/definitions/AVMRShell" },
        "pulse": { "$ref": "#/definitions/PBACSPulse" },
        "emission": { "$ref": "#/definitions/PBACSEmission" },
        "control": {
          "type": "object",
          "properties": {
            "state": { "$ref": "#/definitions/ControlState" },
            "score": { "$ref": "#/definitions/Q16_16" },
            "alpha_t": { "$ref": "#/definitions/Q16_16" }
          }
        }
      },
      "required": ["t", "shell", "pulse"]
    },
    "ThermodynamicCost": {
      "type": "object",
      "properties": {
        "encoding_cost": { "$ref": "#/definitions/Q16_16" },
        "retrieval_cost": { "$ref": "#/definitions/Q16_16" },
        "transmission_cost": { "$ref": "#/definitions/Q16_16" },
        "landauer_limit": { "$ref": "#/definitions/Q16_16" },
        "efficiency": { "$ref": "#/definitions/Q16_16" }
      }
    },
    "TemporalBuffer": {
      "type": "object",
      "properties": {
        "history_size": { "type": "integer", "minimum": 0 },
        "angular_momentum": { "$ref": "#/definitions/Q16_16" },
        "step_count": { "type": "integer", "minimum": 0 }
      }
    },
    "ManifoldPoint": {
      "type": "object",
      "properties": {
        "coords": {
          "type": "array",
          "items": { "$ref": "#/definitions/Q16_16" }
        },
        "dimension": { "type": "integer", "minimum": 1, "maximum": 16 }
      },
      "required": ["coords", "dimension"]
    },
    "ThroatStability": {
      "type": "string",
      "enum": ["collapsed", "fluctuating", "stable", "crystalline", "resonant"]
    },
    "WormholeMouth": {
      "type": "object",
      "properties": {
        "location": { "$ref": "#/definitions/ManifoldPoint" },
        "aperture": { "$ref": "#/definitions/Q16_16" },
        "tidalStress": { "$ref": "#/definitions/Q16_16" },
        "chronologyProtection": { "type": "boolean" }
      },
      "required": ["location", "aperture", "tidalStress"]
    },
    "WormholeThroat": {
      "type": "object",
      "properties": {
        "mouthA": { "$ref": "#/definitions/WormholeMouth" },
        "mouthB": { "$ref": "#/definitions/WormholeMouth" },
        "properLength": { "type": "integer", "minimum": 0 },
        "stability": { "$ref": "#/definitions/ThroatStability" },
        "exoticMatter": { "$ref": "#/definitions/Q16_16" },
        "fluxCapacity": { "$ref": "#/definitions/Q16_16" },
        "resonanceFreq": { "$ref": "#/definitions/Q16_16" },
        "bidirectional": { "type": "boolean" }
      },
      "required": ["mouthA", "mouthB", "properLength", "stability"]
    },
    "ThroatRegime": {
      "type": "string",
      "enum": ["open_channel", "pinch", "throat", "collapse"]
    }
  }
}
```

---

**End of Specification**
