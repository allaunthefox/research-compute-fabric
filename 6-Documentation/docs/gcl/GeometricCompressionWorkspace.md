# Geometric Compression Workspace

**Purpose**: Define the working arena where source objects are projected into Q0_64 coding atoms, embedded into geometric surfaces, compressed by collapse operators, and audited by Delta-Phi-Gamma-Lambda plus Warden receipts.

**Status**: Active  
**Version**: 3.0-Delta  
**Date**: 2026-05-01

---

## 1. Core Doctrine

### 1.1 The Three-Layer Type System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THREE-LAYER TYPE SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: Source-Space (Raw Measurements)                                   │
│  ├── Type: BioParamQ (Q16_16)                                              │
│  ├── Range: [-32768, 32767]                                               │
│  ├── Resolution: 2^-16                                                      │
│  └── Contains: Dimensions, charge, rigidity, temperature, Tm                │
│                                                                             │
│  Layer 2: Coding-Space (Normalized Atoms)                                 │
│  ├── Type: CodingQ (Q0_64)                                                 │
│  ├── Range: [-1, 1)                                                         │
│  ├── Resolution: 2^-63 ≈ 1.08e-19                                           │
│  └── Contains: ALL canonical coding values                                  │
│                                                                             │
│  Layer 3: Projection (Source → Coding Map)                                  │
│  ├── Type: BioCodingProjection                                             │
│  ├── Fields: raw? × normalized × scaleReceipt                               │
│  └── Requirement: Explicit normalization map with provenance              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 The Hard Rules

| Rule | Violation | Warden Emission |
|------|-----------|-----------------|
| All coding is Q0_64 | Field marked `coding_atom` but not CodingQ | `codingAtomTypeViolation` |
| No float in canonical | Constructor uses Float | `fixedPointViolation` |
| Projection requires receipt | Q0_64 derived from raw without scaleReceipt | `missingScaleReceipt` |
| Source ≠ Coding | Raw physical param presented as coding | `projectionProofConfusion` |
| Receipts for bio claims | Biological analogy without external receipts | `bioOverclaim` |

### 1.3 The Rational Constructor Doctrine

**NO FLOAT IN CANONICAL CODE.**

All decimal constants must enter through `ofRatio`:

```lean
-- WRONG: Float in canonical
Q0_64.ofFloat 0.55
Q16_16.ofFloat 2.2

-- CORRECT: Rational constructor
Q0_64.ofRatio 55 100    -- 0.55
Q0_64.ofRatio 22 40      -- 0.55 = 2.2/4.0 normalized
Q16_16.ofRatio 22 10     -- 2.2
Q16_16.ofRatio 18 10     -- 1.8
```

---

## 2. The Four Workspace Zones

### 2.1 Source-Space Zone

**Purpose**: Where raw, dimensioned, symbolic, or >1 values live before coding.

**Inhabitants**:
- Biophysical measurements (helicalDiameter: 2.2 nm)
- Algorithm source files
- Language symbol tables
- Mass Number packets
- Goxel fields
- Surface traces

**Rule**: Source values may be messy. They are **not** automatically coding atoms.

**Example**:
```lean
structure RawHelixGeometry where
  diameter : BioParamQ       -- Q16_16, e.g., 2.2 nm
  pitch : BioParamQ          -- Q16_16, e.g., 3.4 nm
  rise : BioParamQ           -- Q16_16, e.g., 0.34 nm
  charge : BioParamQ         -- Q16_16, e.g., -1.0 (negative)
```

### 2.2 Coding-Space Zone

**Purpose**: Where normalized Q0_64 atoms live.

**Inhabitants**:
- Symbol probabilities
- Channel reliability scores
- Compression ratios
- Stability indices
- Binding confidence
- Degeneracy measures

**Rule**: **All coding is Q0_64.** Period.

**Example**:
```lean
structure ChannelParameters where
  symbolReliability : CodingQ    -- Q0_64, e.g., 0.999
  stabilityScore : CodingQ       -- Q0_64, e.g., 0.95
  decodingEfficiency : CodingQ   -- Q0_64, e.g., 0.90
```

### 2.3 Geometry-Space Zone

**Purpose**: Where coding atoms become geometric structures.

**Inhabitants**:
- Points (coordinate vectors of CodingQ)
- Edges (pairwise relationships)
- Surfaces (2D manifolds of codewords)
- Basins (local minima in compression landscape)
- Ridges (high-stability sequences)
- Holes (unusable codewords)
- Seams (boundary between regimes)
- Flow lines (evolution trajectories)

**Key Hypothesis**:
> Geometry helps compression when it makes invariant structure cheaper to preserve than raw symbolic encoding does.

**Δφγλ Formulation**:
```
A geometric compression operator is useful only if it lowers description cost
while keeping DeltaPhi bounded across lambda under gamma.
```

### 2.4 Receipt-Space Zone

**Purpose**: Where compression results are audited and failures recorded.

**Inhabitants**:
- DeltaPhi audit results
- Reverse-collapse success/failure
- Alias policy violations
- Normalization receipts
- Warden validation statuses

**Underverse**: Failed projections, blocked aliases, and dead-ends go here rather than circulating in active fields.

---

## 3. Projection Protocol (Source → Coding)

### 3.1 Normalization Requirement

Any value entering Coding-Space from Source-Space **must** provide:

1. **Numerator**: Raw measurement value
2. **Denominator**: Maximum expected value (scale)
3. **Receipt**: Provenance of the normalization map

### 3.2 Projection Function Template

```lean
def projectSourceToCoding
    (raw : BioParamQ)
    (scale : BioParamQ)
    (receipt : String) : BioCodingProjection :=
  { raw? := some raw,
    normalized := CodingQ.mk (Q0_64.ofRatio raw.val scale.val),
    scaleReceipt := receipt
  }
```

### 3.3 Example: Helical Diameter

```lean
-- Source measurement
let rawDiameter : BioParamQ := BioParamQ.mk (Q16_16.ofRatio 22 10)  -- 2.2 nm
let maxDiameter : BioParamQ := BioParamQ.mk (Q16_16.ofRatio 40 10)  -- 4.0 nm

-- Projection to coding space
let projected : BioCodingProjection :=
  projectSourceToCoding rawDiameter maxDiameter
    "Helix diameter normalized to B-DNA max per Saenger 1984"

-- Result: normalized.value = Q0_64.ofRatio 22 40 = 0.55
```

---

## 4. Compression Operator Contract

### 4.1 Required Fields

Any proposed compression operator must specify:

| # | Field | Type | Description |
|---|-------|------|-------------|
| 1 | input | Source-Space | What is being compressed |
| 2 | codingProjection | CodingQ | Q0_64 normalized atoms |
| 3 | geometricEmbedding | Geometry-Space | Surface/point/edge structure |
| 4 | collapseOperator | Function | The compression transform |
| 5 | preservedPhi | PhiInvariant | What structure must survive |
| 6 | residualDelta | DeltaResidual | What is lost/distorted |
| 7 | gammaPressure | GammaPressure | Compression force |
| 8 | lambdaScale | LambdaScale | Scale of comparison |
| 9 | reversePath | ReverseCollapsePath | Recovery trajectory |
| 10 | aliasPolicy | String | Collision handling |
| 11 | wardenMode | WardenEmission | Failure handling |

### 4.2 Δφγλ Audit

Every operator must pass:

```lean
def operatorValid (op : CompressionOperator) : Bool :=
  op.phi.preserved &&
  op.delta.magnitude.value < threshold &&
  op.reversePath.exists &&
  op.wardenMode != blocked
```

---

## 5. Warden Rules Summary

```lean
inductive WardenEmission where
  | bioOverclaim              -- Biology as evidence without receipts
  | aliasBoundaryBlur         -- Aliases hide incompatible meanings  
  | projectionProofConfusion  -- Surface used as proof
  | missingTestReceipt         -- No behavior-preserving tests
  | recursiveAbstractionWithoutGround  -- No reverse-collapse
  | fixedPointViolation        -- Float in fixed-point hot path
  | codingAtomTypeViolation    -- coding_atom field not CodingQ
  | deltaUnbounded             -- Residual exceeds threshold
  | phiNotPreserved            -- Invariant failed
  | missingScaleReceipt        -- Projection lacks normalization provenance
```

**Promotion Gate**: `CANONICAL_LEAN` or `REVIEWED` authority state only if zero emissions.

---

## 6. Benchmark Protocol

### 6.1 Comparison Structure

```
Input: Same source corpus / packet set

Route A (Baseline):
  Source → Symbolic Encoding → Compression

Route B (Geometric):
  Source → Q0_64 Coding → Geometric Surface → Collapse Operator

Measure:
  - Compressed size
  - Phi survival (structure preservation)
  - Delta residue (distortion)
  - Reverse-collapse success
  - Alias failures  
  - Warden receipts
```

### 6.2 Success Criteria

Geometric compression wins if:
- Compressed size < symbolic baseline
- Phi preserved = true
- Delta < threshold
- Reverse-collapse success rate > 95%
- Zero alias boundary blur emissions

---

## 7. Attack Surfaces for LLM Review

Give the model these pressure points:

1. Does Q0_64 lose too much source information?
2. Are normalization maps arbitrary?
3. Does geometric embedding preserve real invariants?
4. Does surface collapse create hidden aliases?
5. Does reverse-collapse recover useful structure?
6. Does operator beat ordinary compression baselines?
7. Does DeltaPhi have measurable proxies?
8. Are biological analogies smuggled as evidence?
9. Are render surfaces mistaken for proof?
10. Are fixed-point constraints obeyed end-to-end?

---

## 8. The One Sentence

> If geometry is the proposed solution to compression, then GCL must provide the workspace where source objects become Q0_64 coding atoms, coding atoms become surfaces, surfaces undergo collapse, and every lost or preserved invariant is audited by Delta-Phi-Gamma-Lambda.

---

## 9. External Source Anchors

### 9.3 Wang et al. — AI-Guided Alphabet Compression in E. coli Ribosomal Proteins

**Source**: Krywko, J. *Scientific American* (2026-04-30) — *Scientists used AI to rewrite part of life's alphabet*  
**Primary Citation**: Wang et al., *Science* (2026) — Ec19 E. coli strain engineered via ESM2 / AlphaFold2 / ProteinMPNN to remove isoleucine from 21 of 52 ribosomal proteins, maintaining >90% wild-type fitness across 450 generations.

**Core Insight**: A 20-amino-acid coding alphabet can be partially compressed to 19 (in specific protein domains) while preserving essential function, provided AI-guided redesign compensates for the lost symbol with structural adjustments.

**GCL Binding**:

| Ec19 Finding | GCL Translation |
|--------------|-----------------|
| 20 canonical amino acids | Source alphabet: `EncodingFamily.sixteenSymbolBlock`-like full code |
| 21/52 ribosomal proteins without isoleucine | Collapsed sub-alphabet over a restricted domain |
| ESM2 + AlphaFold2 + ProteinMPNN redesign | `CollapseOperator` thesis: AI-guided structural compensation |
| Manual debugging of lethal interactions | `AdversarialTrial` contra: lethal combinations detected and repaired |
| 90% fitness threshold | `WardenEmission` delta bounded; `phi.preserved = true` |
| 450 generations without reversion | Stable fixed-point; reverse-collapse path verified |
| Ribosome as "oldest remnant of common ancestor" | Core invariant preserved under compression |

**Δφγλ Mapping**:
- **Delta**: Fitness loss from wild-type (40% after naive swap → 90% after AI redesign)
- **Phi**: Ribosomal structure and function preserved across 21 proteins despite missing isoleucine
- **Gamma**: AI design pressure (ESM2 mutation proposals, AlphaFold2 structural validation)
- **Lambda**: Scale of 52 ribosomal proteins; restricted to ribosome, not full proteome

**Warden Emission Mapping**:
```
if naive_swap_fitness < 0.90:
  emit deltaUnbounded          -- compression too lossy
if AI_redesign_fitness >= 0.90:
  emit candidate_promotion     -- bounded delta, phi preserved
if lethal_interaction_detected:
  emit phiNotPreserved         -- contra-surface failed
  require manual_repair_receipt
```

**GCL Translation**:
> The 20-amino-acid code is not minimal for all protein domains. The ribosomal sub-domain tolerates 19-symbol compression when structural compensation (AI-designed mutations) is applied. This validates the GCL thesis: geometric surfaces can encode the same invariant structure with fewer symbols, provided the collapse operator accounts for lost degrees of freedom through compensated embeddings.

**Non-Negotiable Boundary**:
> Ec19 is NOT a 19-amino-acid organism. The rest of the genome still contains 81,000+ isoleucine residues. The compression is domain-restricted (ribosomal proteins only), not global. GCL claims about alphabet compression must declare the domain boundary (lambda scale) and must not overgeneralize from a sub-domain result.

---

### 9.1 MIT PlanetWaves — Medium/Geometry Analogy

**Source**: MIT News (2026-04-16) — *Waves hit different on other planets*  
**Core Insight**: Same forcing signal → different medium → radically different surface expression.

**The Model**:  
PlanetWaves accounts for gravity, liquid density, viscosity, surface tension, and atmospheric pressure to predict how a liquid surface evolves under winds. Key result: mild winds can produce ~10-foot waves on Titan's methane/ethane lakes, while hurricane-force winds barely move dense lava oceans on 55 Cancri e.

**GCL Binding**:

| PlanetWaves | GCL Translation |
|-------------|-----------------|
| Wind forcing | Source coding pressure |
| Medium (gravity, density, viscosity) | Geometric embedding |
| Surface wave field | Compression/collapse surface |
| Wave height prediction | Residual delta estimation |

**Δφγλ Mapping**:
- **Delta**: Difference between expected Earth-like behavior and actual planetary response
- **Phi**: Invariant wave-generation structure (wind + gravity + liquid properties → surface)
- **Gamma**: Forcing pressure / coupling intensity (wind speed, energy transfer)
- **Lambda**: Scale band (ripple → lake → coastline → landscape)

**Key Doctrine**:
> The same input does not have the same meaning across media.

**GCL Translation**:
> The same coding pressure produces different compression surfaces depending on the medium, scale, and projection rules. Therefore every GCL compression claim must declare its medium and projection boundary.

**Warden Warning**:
```
if compression_claim && !medium_declared:
  emit planetwaves_medium_violation
  block promotion
```

---

### 9.2 Evolution Strategies — Mutation-Search Over Coded Surfaces

**Sources**:
1. Salimans et al. (2017) — *Evolution Strategies as a Scalable Alternative to RL* [arXiv:1703.03864](https://arxiv.org/abs/1703.03864)
2. ES at Scale: LLM Fine-Tuning Beyond RL [arXiv:2509.24372](https://arxiv.org/abs/2509.24372)
3. ES at Hyperscale with EGGROLL [arXiv:2511.16652](https://arxiv.org/abs/2511.16652)

**Core Insight**: ES perturbs a coded system (neural network parameters), scores variants by fitness, and uses weighted perturbations to update. Works at billion-parameter scale without backpropagation.

**Why GCL Cares**:

| ES Concept | GCL Translation |
|------------|-----------------|
| Parameter space | Q0_64 coding space |
| Perturbation population | Geometric surface variants |
| Fitness evaluation | Delta-Phi-Gamma-Lambda audit |
| Weighted update | Structured collapse operator |
| Common random numbers | Deterministic Q0_64 sampling |

**The Critical Upgrade: Structured vs. Random Perturbation**:

```
Naive ES:     Random mutation over all parameters
EGGROLL/LoRA: Structured low-rank perturbations
GCL Goal:     Geometric perturbation along invariant-preserving directions
```

**Δφγλ Mapping for ES**:
- **Delta**: Performance/structure change after mutation
- **Phi**: Invariant behavior preserved across perturbations
- **Gamma**: Perturbation strength, population size, selection intensity
- **Lambda**: Rank-r perturbation, surface patch, codon block, scale of basis

**GCL Hypothesis**:
> The compression trick is not "mutate more." It is "mutate in the right geometry."

**Low-Rank Geometric Coding Perturbation**:
```
Input: Q0_64-coded source atoms
Step 1: Embed into geometric surface
Step 2: Identify low-rank / motif-aware / invariant-preserving directions
Step 3: Perturb/collapse along those directions
Step 4: Audit with Δφγλ
Step 5: Warden receipt
```

**Warden Warning**:
```
Evolution Strategies are an external optimization analogue, not proof of GCL.
They show that structured mutation over a coded surface can be useful.

Any GCL operator inspired by ES must still declare:
1. Q0_64 coding projection
2. Geometric embedding
3. Fitness/compression objective
4. Reverse-collapse path
5. Baseline comparison
6. Delta-Phi-Gamma-Lambda audit
7. Warden receipt
```

**Attack Surface for LLM**:
- Does low-rank perturbation actually preserve useful invariants?
- Is the geometric basis discoverable or hand-coded?
- Does the ES analogy break down for discrete (not continuous) coding atoms?
- Can Q0_64 surfaces support gradient-free optimization?

---

### 9.3 Synthesis: The Workspace Doctrine

**The Four Zone Flow with External Anchors**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FOUR-ZONE COMPRESSION WORKFLOW                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCE-SPACE          CODING-SPACE          GEOMETRY-SPACE     RECEIPT   │
│  (PlanetWaves          (Q0_64 Atoms)           (ES Surfaces)       (Δφγλ)   │
│   Medium Analogy)                                                         │
│                                                                             │
│  Raw measurements  →  Normalized coding  →  Structured      →  Audit      │
│  (BioParamQ)          atoms (CodingQ)       perturbation        results     │
│                                              (EGGROLL/LoRA                │
│                                               style basis)                │
│                                                                             │
│  • 2.2 nm diameter    • 0.55 normalized    • Low-rank         • Phi        │
│  • 65°C Tm            • 0.999 reliability    surface          • Delta      │
│  • -1.0 charge        • 0.95 stability     directions         • Gamma      │
│  • LNA backbone       • 0.90 efficiency    • Geometric        • Lambda     │
│                                              collapse                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Binding**:
- **PlanetWaves**: Same forcing → different medium → different surface
- **ES**: Structured perturbation → fitness → update
- **GCL**: Source → Q0_64 → geometric surface → structured collapse → Δφγλ audit

**The Testable Claim**:
> Geometry helps compression when it makes invariant structure cheaper to preserve than raw symbolic encoding does, measured by Delta-Phi-Gamma-Lambda across lambda under gamma.

**Benchmark Protocol**:
```
Route A (Baseline): Source → Symbolic Encoding → Standard Compression

Route B (Geometric): Source → Q0_64 Coding → Geometric Surface 
                            → Structured Collapse (ES-style low-rank)
                            → Delta-Phi-Gamma-Lambda Audit

Win Condition: Route B achieves smaller compressed size 
               with bounded Delta and preserved Phi
```

---

## 10. N-Voxel Geometry Terminology

**Status**: v5 NVoxel terminology now canonical.

**Hierarchy**:
```
Goxel
  -> pre-compression / shape-agnostic manifold primitive
  -> unresolved geometric possibility

Voxel
  -> compressed 3D cell
  -> used only when geometry is specifically 3D

n-voxel
  -> compressed or partially compressed n-dimensional cell
  -> dimension is a parameter, not fixed
  -> represents geometry in n-dimensional manifold or coding surface

Surface
  -> rendered projection of Goxel / voxel / n-voxel states
  -> phenotype, not proof
```

**Deprecation**: `hoxel` is deprecated. Use `n-voxel` for dimension-parameterized cells.

**Warden Rule**:
```
Surface projection is an audit, not decoration.
Phenotype != genotype.
Visual centrality != truth.
Simulation convergence != theorem.
```

---

## 11. Autopoietic Monitor (Level 1)

**Purpose**: Bounded self-maintenance of compression workspace.

**Doctrine**:
> Autopoietic-GCL is not self-replication. It observes Warden emissions and proposes repair candidates. All repairs remain in HOLD state.

**Failure Patterns**:
- `deltaUnbounded` — Residual exceeds threshold
- `phiNotPreserved` — Invariant failed
- `lowRankBasisFailure` — Perturbation basis invalid
- `normalizationAmbiguous` — Missing explicit source→Q0_64 map
- `biologicalOverclaim` — Biology metaphor becoming evidence
- `projectionProofConfusion` — Render surface treated as proof
- `signConventionAmbiguous` — Unsigned/signed Q0_64 drift
- `reverseCollapseFailed` — No recovery path

**Repair Proposal Rule**:
```
if repair_proposal.generated_by == workspace_autopoiesis:
  claim_state = HOLD
  require external benchmark or second independent review before promotion
```

**Non-Negotiable**: Autopoietic repair proposals must never promote themselves.

---

## References

- `SyntheticGeneticCoding.lean` — Canonical implementation
- `GeometricCompressionWorkspace.lean` — Four-zone workspace, n-voxel, autopoiesis
- `FixedPoint.lean` — Q0_64 and Q16_16 definitions with `ofRatio`
- GCL v3 Delta Definitions — Conceptual foundation
- GCL v5 NVoxel — N-voxel terminology and hoxel deprecation
- AGENTS.md §1.4, §1.5 — Fixed-point and no-float rules
- MIT PlanetWaves (2026) — Medium/geometry analogy
- Salimans et al. (2017) — Evolution Strategies as scalable RL alternative
- ES at Scale (2025) — Billion-parameter LLM fine-tuning with ES
- EGGROLL/Hyperscale ES (2025) — Structured low-rank perturbations
