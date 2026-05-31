# Sovereign Research Stack — Authoritative Roadmap

> **This is the single authoritative roadmap.** `docs/roadmaps/RESEARCH_STACK_FOREST_MAP_WATERFALL.md` is retained for historical reference. `docs/roadmaps/UNIVERSAL_SUBSTRATE_ROADMAP.md` no longer exists on disk (contents absorbed into this file). Task-level granularity lives in `TODO_MAP.md` at the repository root (note: TODO_MAP.md may lag the current state; this roadmap is the authoritative source).

**Framework:** USTSM (Universal Substrate Topological State Machine)
**Timeline:** 7 phases / 7 months
**Active Milestone:** Burgers 4-Theorem Attack Plan (see `6-Documentation/docs/research/BURGERS_READINESS_ASSESSMENT.md`)
**Source of Truth:** Lean 4 (`0-Core-Formalism/lean/Semantics/`)

---

## 1. The Core Idea

The Sovereign Research Stack is a formalized system where Lean 4 is the single source of truth, all computation is Q16.16 fixed-point (with Q0_64 scalars as the universal interface), and architectural invariants derive from cross-domain equation analysis spanning 1,126 ingested equation rows across 40+ families (source: `shared-data/data/ingested_datasets/2026-05-18/equations.csv`; the previously cited "2,634 models" figure was unverified and has been retracted). Every transformation must declare what changed, what survived, what was lost, what it cost, at what scale, and what receipt proves it. This is not an opinionated workflow — it is a receipt-bounded law stack (GCCL) executed by a manifold compression engine (MISC) generalized to n-dimensional genetic shells (GENSIS), all unified under one substrate machine (USTSM). The operational goal is a hardware-extractable formal kernel with FPGA-verified invariants and Lean-proven correctness.

---

## 2. The Layer Model

| Level | Name | Domain | Status | Key Components |
|-------|------|--------|--------|----------------|
| **L0** | Primordial | Pure math, fixed-point arithmetic, braid fields | **Implemented** (746 modules, 3592 build jobs, 0 errors) | Q16_16 FixedPoint, Q0_64 Scalar, PIST/DIAT Shell, BraidField, SSMS_nD, EigensolidConvergence |
| **L1** | Geometric | Shape-aware topology, coupling geometry | **Partial** (docs migrated, partial Lean; eigensolid convergence proven) | GWL 5-factor Coupling, TorsionalPIST (quaternion), HybridTSMPISTTorus, GWL Throat, BodegaFlow horn-fiber |
| **L2** | Biological | Genetic codes, language zoology, expanded alphabets | **Partial** (12 Lean probes, 3592 jobs green) | GeneticCode, CodonOptimization, GenomicCompression, CrossModalCompression, GeneticThermodynamicLimitProbe, ExpandedGeneticAlphabetProbe, LanguageZoologyProbe, GeneticAnchorProbe, GeneticSignalTransformProbe, GeneticErrorMinimizationProbe, CrossModalGeneticLanguageProbe, LandauerGeneticClockProbe |
| **L3** | Thermodynamic | Energy-aware quality, semantic basin capacity, Landauer limits | **Partial** (5 Lean probes formalized) | Trixal Quality, Homeostatic Governor, HyperFlow, ThermodynamicLanguageProbe, LandauerShannonProbe, MediaTransferProbe, LanguageTransferProbe, SemanticBasinOverflowProbe, InformationBottleneckLanguageProbe |
| **L4** | Security | Attack-aware gating, frustration memory | **Partial** (AngrySphinx in Lean) | AngrySphinx (exponential PoD), FAMM Frustration, ASICTopology |
| **L5** | Semantic | Meaning-aware filtering, manifold routing, compression governance | **Partial** (projection receipts exist) | CrossDimensionalFilter (12 semantic primes), Manifold Networking, BracketedCalculus, CompressionControl, RRC Equation Projection |
| **L6** | Meta | Self-aware adaptation, cognitive routing, auto-adaptive metatyping | **Partial** (cognitive receipts + projection holds) | Cognitive Load Decomposition (5-factor), Adaptation, DynamicCanal, CompressionMechanics, Connectome-Protective Load Reweighting |

**Status legend:** `Implemented` = Lean code with `#eval`/theorems exists. `Partial` = some Lean modules exist, docs are migrated. `Speculative` = documentation and design exist, awaiting Lean formalization.

---

## 3. The Three-Axis Pipeline

```
Substrate (ENE) ←→ Surface (Notion/Obsidian) ←→ Intent (Linear)
                          ↓
                      Metatype
```

| Axis | Role | Primary Tool | Direction |
|------|------|-------------|-----------|
| **Substrate** | Raw data, credential mesh, equation registry, FAMM memory, FPGA bitstreams | ENE distributed nodes, SQLite, Tang Nano 9K, Google Drive/Rclone | Bidirectional sync |
| **Surface** | Human-readable workbench, canonical graph authority, semantic registry, topological queries | Obsidian, Neo4j, Graph.lean, Notion, FastAPI/WebSocket surface | Read-heavy, projection target |
| **Intent** | Task routing, cognitive load decomposition, strategy selection, proof goals | Linear (task tracking), MCP Router, Cognitive Router | Write-heavy, command source |

**Data flow:** Intent issues a task → Surface resolves canonical references → Substrate executes (Lean proves, FPGA routes) → Result projects back to Surface → Metatype (auto-adaptive type judgment) classifies and promotes/holds/quarantines.

---

## 4. Data Flow

```
Raw Data → PIST/DIAT Shell Remap → GWL Multi-Factor Coupling → Cognitive Router (strategy select)
    → Delta GCL Encoding → Trixal Quality Verify → Homeostatic Governor Update → Compressed Output
    → [Optional: AngrySphinx Gate → FAMM Scar/Basin Write → AMMR Commit]
```

| Stage | What Happens | Substrate |
|-------|-------------|-----------|
| **PIST Remap** | Map tokens to shell coordinates `(k, t)` with mass `= t·(2k+1−t)` | PIST/DIAT (#1) |
| **GWL Coupling** | Compute 5-factor similarity weight between token positions | GWL Rotational (#2) |
| **Cognitive Router** | Decompose load into I/E/G/R/M components; select optimal compression strategy | Cognitive Load (#14) |
| **Delta GCL** | Encode as manifest; compute delta from previous block | Delta GCL (#19) |
| **Trixal Verify** | Assess compression as thermodynamic process (thermal/work/irreversibility) | Trixal (#13) |
| **Homeostatic Update** | Compute surprise/regret; adjust pressure and canal width | Homeostatic (#15) |
| **Output** | Emit compressed bitstream with trixal stamp + shell map | — |

The full loop adds security gates (AngrySphinx exponential gate #3, FAMM frustration check #6) and memory writes (AMMR/O-AMMR commit mountains) for transitions that pass all quality thresholds.

---

## 5. Master Timeline — Phases 0–7

### Phase 0 — Unification (Month 1) | **Status: IN PROGRESS (infrastructure bootstrapped; USTSM Lean type pending)**

Infrastructure plumbing completed: ENE private connector, Graph.lean authority, Obsidian+Neo4j connector, ENE RDS 8-crate Rust workspace, ene-session-sync crate (26 modules, 145 tests passing).

Lean formalization not yet started:
- Define `USTSM_State` as discriminated union of all 36 substrate states *(type does not yet exist in Lean)*
- Implement USTSM kernel (scalar → gate → route → transition → assess → update → check)
- Implement `reductionFilter` for every substrate (state → Q0_64)
- Prove cross-substrate resonances (mass = entropy = scalar)
- **Forest Map absorption:** Lock authority and substrate plumbing (Forest Phase 0) — infrastructure complete; Lean DAG tables created (DDL committed), data population pending

### Phase 1 — Primordial Substrates (Month 2) | **Status: PARTIAL (some Lean exists)**

- Q0_64 full Lean implementation + totality proofs
- PIST/DIAT n-dimensional generalization + zero-mass theorem
- BraidField invariant preservation across merge operations
- Q16_16 → Q0_64 bridge
- **Forest Map absorption:** Build canonical forest skeleton (Forest Phase 1): Graph.lean snapshot, ForestGradientRoads.lean, canonical node/edge taxonomies

### Phase 2 — Geometric Substrates (Month 3) | **Status: SPECULATIVE (docs migrated, Burgers active)**

- GWL Rotational 5-factor coupling in Q0_64
- HybridTSMPISTTorus proof (wrapping eliminates zero-mass degeneracy)
- TorsionalPIST quaternion RG flow in shell space
- GWL Throat traversal as topological transition
- **Forest Map absorption:** Complete equation inventory by domain (Forest Phase 2) — equation packs with required fields
- **Active milestone: BURGERS_READINESS_ASSESSMENT.md — Day 1-4 theorems (Energy Dissipation, FNWH Regularization, Shock Width, KdV Soliton)**

### Phase 3 — Biological Substrates (Month 4) | **Status: PARTIAL (12 probes formalized, 3592 jobs)**

**COMPLETED (2026-05-22):**
- `MediaTransferProbe.lean` — 7 media channels with Shannon bandwidths, proved `channelBandwidthIncreasing`
- `LanguageTransferProbe.lean` — 7 language substrates (chemical → generative), proved `languageEffectivenessStrictlyIncreasing`
- `LanguageZoologyProbe.lean` — 6 documented non-human languages (honeybee → octopus), substrate assignments proved
- `GeneticThermodynamicLimitProbe.lean` — 10 genetic polymer types, Landauer limit calculation, `R_max ≈ 3.5×10^8 bits/s`
- `ExpandedGeneticAlphabetProbe.lean` — hachimoji (8-base) and supernumerary DNA (12-base), proved `standardDnaOptimal`
- `GeneticAnchorProbe.lean` — codon-product ratio `64/21 ≈ 3.047`, tested genetic clock hypothesis
- `LANGUAGE_MATH_MODEL_SOURCES.cff` — 29 references with verified DOIs
- `GeneticSignalTransformProbe.lean` — unified power law `P ∝ S^{1/2} · λ_φ^{D_f} · exp(-γ·ΔE_eff/kT)`, LTEE fitness sqrt scaling, Drake rule direction
- `GeneticErrorMinimizationProbe.lean` — Freeland & Hurst error minimization, standard code better than random in polarity model
- `CrossModalGeneticLanguageProbe.lean` — developmental biology as 5-modality cross-modal language (genome → transcript → protein → complex → tissue)
- `LandauerGeneticClockProbe.lean` — thermodynamic cost of genetic preservation, genetic clock inversely proportional to genome size

**PENDING:**
- Genetic Code: all 30+ variant tables mapped to USTSM
- Genomic Compression field-theoretic pass
- Codon Optimization (CAI + GC content as state constraints)
- Spiking Neuron Izhikevich → Q0_64 spike encoding
- STDP weight update as GWL coupling replacement
- **Forest Map absorption:** Semantic Number Pattern Search (Forest Phase 3), COUCH coupling degeneracy fix (Forest Phase 4)

### Phase 4 — Thermodynamic & Security (Month 3–4, concurrent with Phases 2–3) | **Status: PARTIAL (AngrySphinx + 5 thermodynamic probes in Lean)**

> **Note:** Phase 4 runs concurrently with Phases 2–3. AngrySphinx Lean work can proceed independently of the geometric substrate proofs.

**COMPLETED (2026-05-22):**
- `ThermodynamicLanguageProbe.lean` — semantic basin capacity `B = C_dec / E_bit`, proved generative mismatch `M = 50,000,000×`
- `LandauerShannonProbe.lean` — Landauer energy `2.87×10^-21 J`, Heisenberg time `1.8×10^-14 s`, framework gap analysis
- `SemanticBasinOverflowProbe.lean` — consistency between 100× bandwidth acceleration and 50,000,000× compression asymmetry
- `InformationBottleneckLanguageProbe.lean` — `I(X;T) ≤ R` for 7 substrates, IB rate strictly increasing, generative relevance gap positive

**PENDING:**
- Trixal State Carnot efficiency in Q0_64
- Homeostatic Governor fixed point theorem in Q0_64
- HyperFlow Navier-Stokes convergence in shell space
- AngrySphinx full Lean formalization of E_solve ≥ 2^n
- FAMM Frustration triadic rejection as state machine guard
- ASICTopology admissible operation proofs
- **Forest Map absorption:** Extract first verified basin candidate (Forest Phase 5), build torsion heatmap (Forest Phase 6)

### Phase 5 — Semantic & Meta Substrates (Month 5) | **Status: SPECULATIVE**

- CrossDimensionalFilter 12 semantic primes as Q0_64 anchors
- Manifold Networking routing cost over all substrates
- Cognitive Load strategy selection over 36 substrates
- DynamicCanal adaptive canal per substrate
- SSMS_nD fractal shell hierarchy proof
- CompressionMechanics physical admissibility proofs
- RRC equation projection as label-minimized admissibility surface:
  `278` local equation surfaces projected; `29` CANDIDATE, `249` HOLD;
  primary repair targets are `scale_band_declared` and
  `negative_control_strength`
- Add Lean `RRCShape` mirror for the projection shapes before promoting
  equation projections into proof targets
- Root-lift translation table: map classical signal roots to quantum/operator/hardware analogue classes with explicit proof obligations, bounded witnesses, and exact receipt boundaries
- Root-lift semantic collider: collide source/target vocabularies, equation normal forms, invariants, admissibility constraints, and receipt packets to expose existing roads before declaring gaps
- Root-lift domain sweep: apply the semantic collider across compression, FPGA/hardware, quantum/signal, biophysics, CAD, genomics, materials, ENE/search, Typst/docs, MCP/tools, Lean/proofs, finance, thermodynamics, remote testing, and LLM compression
- Stent-physics flow-control table: map porous scaffolds, struts, porosity, apposition, overlap, shear/churn, and residence-time proxies into route-frontier and FPGA packet-flow gates with counted overhead and receipt boundaries
- Biophysics borrowable-math table: harvest reaction-diffusion, porous transport, membrane curvature, phase separation, excitable-media, fractional-memory, active-matter, and identifiability equations as route-control operators with exact receipt boundaries
- **Forest Map absorption:** Batch ingest light-source corpus (Forest Phase 7), Neo4j topological traversal (Forest Phase 8)

### Phase 6 — Compiler (Month 6) | **Status: SPECULATIVE**

- Lean 4 → Rust extraction for all 36 substrates
- Lean 4 → C extraction for embedded targets
- Lean 4 → Verilog extraction for FPGA targets *(LONG-TERM — prerequisite for all FPGA bring-up; Tang Nano 9K, iCE40, ECP5 hardware targets deferred until this phase completes)*
- Universal GENSIS compiler with auto substrate selection
- Cross-substrate benchmark suite
- **PCIe Idle-Cycle Compute Harvester:** Formalize a substrate for scheduling computation on idle PCIe bus cycles (GPU, NVMe, DMA controller). Target: a `pcie_idle` substrate that observes bus transaction gaps, dispatches hash/verify kernels into those slots via scatter-gather DMA descriptors, and guarantees zero impact on user-facing transactions. Reference implementation: Windows SMB hash worker using RTX 4070 GPU as PCIe-attached compute engine with IDLE priority + background I/O + EcoQoS, checkpointed via DAG for kill-safe resume.
- **Forest Map absorption:** Closure criteria for complete map (Forest Phase 9)

### Phase 7 — Proof of Completeness (Month 7) | **Status: SPECULATIVE**

- Prove every substrate transition preserves at least one invariant
- Prove every substrate can communicate via Q0_64 scalar
- Prove substrate composition is associative and commutative
- Prove USTSM state space is connected
- Prove USTSM is a topological quantum field theory (TQFT)

---

## 6. The 7 Core Invariants

| # | Invariant | Source Primitive | Statement |
|---|-----------|-----------------|-----------|
| **1** | Mass Conservation | PIST/DIAT Shell | `mass = t·(2k+1−t)`; dM/dt ≤ 0 under dissipative transitions; zero at perfect-square shell endpoints |
| **2** | Exponential Gate | AngrySphinx | `E_solve ≥ 2^depth`; F > 0 guard; NaN boundary at F→0 prevents unbounded compute |
| **3** | Semantic Prime Conservation | CrossDimensionalFilter | 12 semantic primes; reductionFilter preserves prime set; monotonic prime understanding |
| **4** | Frustration Monotonicity | FAMM | Triadic frustration F < threshold; frustration never spontaneously decreases without route resolution |
| **5** | Homeostatic Fixed Point | Homeostatic Governor | `|γ + s'(p*)| < 1`; stable equilibrium pressure where surprise + regret balance decay |
| **6** | Cognitive Load Decomposition | Cognitive Router | `L_total = λ_I·L_I + λ_E·L_E − λ_G·L_G + λ_R·L_R + λ_M·L_M`; strategy selected minimizes total load |
| **7** | Scalar Universality | Q0_64 / USTSM *(design goal)* | Every substrate state shall reduce to a dimensionless scalar ∈ [0,1); scalar is the universal inter-substrate communication primitive. **Current state:** Q0_64 type not yet in Lean; existing `bind` primitive uses Q16_16 for all cost and gradient computation (as required by `Bind.lean`: "all values require integer component for gradient computation"). Q0_64 universality is a Phase 0–1 deliverable, not a current enforced fact. |

Invariants 1–6 are partially enforced by existing Lean code. Invariant 7 is a Phase 0–1 design target — the USTSM kernel that would enforce it on every transition does not yet exist.

---

## 7. The Burgers 4-Theorem Attack Plan (Active Milestone)

**Location:** `6-Documentation/docs/research/BURGERS_READINESS_ASSESSMENT.md`
**Goal:** Close the 7 "half-solved" Burgers PDE files (zero theorems currently) using GENSIS/USTSM invariants.

| Day | Theorem | Maps To | Proof Template |
|-----|---------|---------|----------------|
| **Day 1** | Energy Dissipation `d(Σ½u²)/dt ≤ 0` | Invariant 1 (Mass) | `massConservation` + `frustration_monotonic` |
| **Day 2** | FNWH Regularization Bounded `∃Ω_max, Ω ≤ Ω_max` | Invariants 4,5,6 | `fixed_point_exists` + `cognitiveEfficiency` |
| **Day 3** | Shock Width Optimal `w* = argmin L_total(w)` | Invariant 6 (Cognitive) | `selectStrategy` + `totalTypeLoad` |
| **Day 4** | KdV Soliton Stability `mass(soliton) = constant` | Invariant 7 (Scalar) | `scalarImpliesMassEquality` |

**Status:** The Burgers stack has 7 Lean files with full numerical implementations (`#eval` passing). The GENSIS 7-invariant system provides exact proof templates.

- **Closed:** `eigensolid_convergence` — braid crossing loop convergence proven (`EigensolidConvergence.lean`, commit `d84569a5`).
- **Open:** Energy dissipation, FNWH regularization, shock width, KdV soliton stability — 4 theorems remaining. Tractable in ~4 days using `AutoAdaptiveMetatypeSystem.lean` templates.

---

## 8. Repository Structure

| Path | Purpose |
|------|---------|
| `0-Core-Formalism/lean/Semantics/` | **Source of truth.** All Lean 4 formalizations, theorems, invariants |
| `0-Core-Formalism/lean/Semantics/Foundations/` | F01–F12 foundation kernel definitions (Shannon, Carnot, Landauer, etc.) |
| `0-Core-Formalism/lean/Semantics/Semantics/` | Domain modules: 946+ entries including PIST, FAMM, AngrySphinx, Burgers (7 files), GWL, Q16_16, FixedPoint, HCMMR, FNWH subdirs, and many more |
| `4-Infrastructure/infra/` | Infrastructure shims (Rust): ENE distributed node (`ene-session-sync` 26-module crate, 145 tests), `rs-surface` Axum HTTP daemon; Python shims removed |
| `5-Applications/out/verilog/` | FPGA RTL (Verilog): Tang Nano 9K router, sim testbenches, bitstreams |
| `5-Applications/scripts/` | Python tools: formula canonicalizer, P9 query, compression demos |
| `6-Documentation/docs/` | All documentation: roadmaps, research theory, semantics specs, AGENTS.md |
| `6-Documentation/docs/research/` | Theory docs: GCCL, MISC, GENSIS, Burgers assessment, framework relationships |
| `6-Documentation/docs/roadmaps/` | Planning docs: **ROADMAP.md (this file — authoritative)**, historical roadmaps |
| `shared-data/data/` | Runtime data: equations_forest.jsonl, distance matrices, supernodes |
| `shared-data/artifacts/` | Experiment artifacts: photonic witness outputs, benchmarks |
| `tools/` | Codegen, MCP servers, Lean shims, equivalence checkers |
| `TODO_MAP.md` (root) | **Granular task tracker:** file-by-file status, dependency graph, blockers |
| `CONCEPTS.md` (root) | Quick-reference concept dictionary (FAMM, PIST, OTOM, ENE, etc.) |

---

## 9. Key Invariants (System Primitives)

### 9.1 The `bind` Primitive

Every algorithm must be expressible as:

```lean
bind : (A × B × Metric) → Bind A B
```

With a lawful check (`Bool`), a cost function (Q16_16 or Q0_64), and an invariant extractor. Five allowed classes: `informational_bind`, `geometric_bind`, `thermodynamic_bind`, `physical_bind`, `control_bind`. No sixth class without a blackboard session.

### 9.2 Settlement States

```
SEED → SANITIZED_METAPHOR → TOY_MODEL → TYPED_MODEL → RESIDUAL_TESTED
    → COST_ACCOUNTED → PROOF_CANDIDATE → CORE_MODULE → COMPRESSED
```

Reverse path for failures (e.g., `CORE_MODULE → failed proof → PROOF_CANDIDATE`). No transformation can skip a rung. `COMPRESSED` is the terminal settled state — a receipt-bearing, invariant-preserving, fixed-point artifact.

### 9.3 Promotion Ladder

```
BEAUTIFUL_PROVISIONAL (default, LLM-supported, unbenchmarked)
    → CALIBRATED_ENGINEERING_DELTA (requires baseline comparison: zlib/gzip/brotli/zstd)
    → REVIEWED (requires non-LLM validation: human reviewer, hardware measurement)
    → VERIFIED (requires reproducible benchmark + corpus provenance + Lean theorems)
```

No promotion without domain-appropriate evidence. Compression claims require SI standard `CR = original/compressed` ratio against named baselines. Statistical claims require ≥5σ minimum, ≥6.5σ preferred. Formal claims require Lean proof terms with zero `sorry`/`axiom` in the main import path.

### 9.4 Safety Words

- **`red`** (recording context): All cameras off, operator retreats. Used during Burgers AVM witness recording.

---

## 10. Current State Summary

| Layer | Status | Progress |
|-------|--------|----------|
| **L0 Primordial** | ✅ Lean implemented | 746 modules, 3592 build jobs, 0 errors; eigensolid convergence proven; Q16_16 signed-arithmetic bugs fixed; 9 sorrys closed; 95 inspection issues resolved |
| **L1 Geometric** | 🔄 Burgers active | Eigensolid convergence closed; BodegaFlow horn-fiber refinements committed; RG torsion physics suite (H0, DESI, BAO, Higgs, Jupiter moons); 4 Burgers theorems remain |
| **L2 Biological** | 📋 Speculative | GENSIS doc, genetic code tables mapped; no Lean |
| **L3 Thermodynamic** | 📋 Speculative | Trixal, Homeostatic docs; no Lean |
| **L4 Security** | 🔄 Partial | AngrySphinx Lean exists; Anti-FAMM + Anti-BraidStorm adversarial harnesses added; 16D anchor packs operational; 20+ gate library entries added |
| **L5 Semantic** | 🔄 Partial | RRC equation projection receipt exists; 278 surfaces projected, 249 HOLD pending scale-band/negative-control witnesses |
| **L6 Meta** | 🔄 Partial | Cognitive load receipts exist; connectome-protective overflow needs Lean witness surface |
| **FPGA Hardware** | 🔄 Bitstream ready | Tang Nano 9K: Yosys pass (614 cells), P&R pass (162 MHz), bitstream (2 MB) generated. **Live hardware receipt pending** — physical board + programmer required to flash and verify LED/UART behavior (see action #8 below) |
| **Surface** | 📋 TODO | FastAPI/WebSocket skeleton spec'd in TODO_MAP Phase F |
| **Integration** | 📋 TODO | Lean→Verilog extraction, equivalence checking spec'd |

**Immediate next actions** (from `TODO_MAP.md` §Immediate Next Actions):
1. Execute Burgers Day 1 theorem (Energy Dissipation `d(Σ½u²)/dt ≤ 0`)
2. Prove `receipt_invertible` for braid eigensolid compressor (second required theorem)
3. Add RRC scale-band witness schema for equation records; rerun `4-Infrastructure/shim/rrc_equation_classifier.py`
4. Add negative-control strength witnesses for HOLD rows before promotion
5. Garage replication_factor=3 with 6 nodes across 6 zones (qfox-1, cupfox, nixos-laptop, racknerd, neon-64gb, steamdeck) — ✅ done
6. UART packet format design (start byte + 3-byte payload + checksum)
7. Create `4-Infrastructure/surface/` FastAPI skeleton
8. Flash Tang Nano 9K with generated bitstream; verify LED behavior *(blocked: requires physical Tang Nano 9K board + USB programmer attached to host)*

---

## 11. Substrate Census Summary

The USTSM design targets 36 substrates across 7 abstraction levels. Every substrate will have: state space, metric, transition function, invariant, guard, Q0_64 reduction, and AngrySphinx gate compatibility. The substrate census file (`UNIVERSAL_SUBSTRATE_ROADMAP.md`) no longer exists on disk; the list below captures the key substrates for active work. Full census reconstruction is a Phase 0 deliverable.

**Key substrates for current work:**
- #1 (PIST/DIAT Shell): mass conservation, Burgers energy Lyapunov
- #3 (AngrySphinx): exponential gate, CFL stability condition
- #6 (FAMM Frustration): triadic rejection, FNWH regularization trigger
- #13 (Trixal): thermodynamic quality, compression as heat engine
- #14 (Cognitive Load): 5-component routing, shock width optimizer
- #15 (Homeostatic Governor): fixed point, AVM witness convergence
- #12 (Q0_64 Scalar): universal interface, soliton mass invariant

---

---

## 12. Infrastructure & Data Layer (Current)

### ENE RDS Rust Workspace

`4-Infrastructure/infra/ene-rds/` — 8-crate Rust workspace replacing the Python RDS stack:

| Crate | Purpose |
|-------|---------|
| `ene-rds-core` | Shared PostgreSQL client, DSN builder, receipts |
| `ene-rds-wiki` | Wiki CRUD + full-text search + revision tracking |
| `ene-rds-ephemeral` | EphemeralNode thermal zones, tasks, receipts, scars, metrics |
| `ene-rds-chat` | Chat session ingestion, keyword/semantic search |
| `ene-api` | Axum HTTP server on :3000 |
| `ene-node` | Node identity and gossip primitives |
| `ene-storage` | S3/Garage object storage client |
| `ene-sync` | Polls opencode.db SQLite → upserts into RDS chat tables |

sqlx 0.8.6 (Dependabot vuln from 0.7 resolved 2026-05-19).

### Storage Stack (restic + Garage + rclone)

Three tools, non-overlapping roles:

| Tool | Role |
|------|------|
| **restic** | Deduplicated, encrypted, content-addressed snapshots. Primary backend: Garage S3. |
| **Garage v2.3.0** | Self-hosted S3-compatible object store over Tailscale mesh. 6 nodes across 6 zones, `replication_factor=3`, zone redundancy enforced. ~1.6 TiB total capacity, ~440 GiB effective. |
| **rclone** | Raw sync between remotes (Garage↔gdrive). Cold copy of restic chunks to gdrive. |

Data flow: `git commit → post-commit hook → restic snap → Garage:research-stack`; daily 03:00 timer → `rclone copy → gdrive:restic-mirror`.

**Storage agent** (`4-Infrastructure/storage/storage_agent.py`): observe→decide→act loop every 15 min via systemd timer. All thresholds Q16_16. Receipts: JSONL hash-chain locally + `s3://research-stack/agent-receipts/`.

### NixOS Devcontainer

`.devcontainer/flake.nix`: hermetic NixOS environment with OpenGL/X11, pkg-config, openssl, full Python science stack, MCP servers for Notion and AWS.

### Credential Gateway

Credential endpoint is served by the `rs-surface` Rust binary (`/credentials` route, port 8444) on each node. The Python `credential_server.py` has been removed — all credential logic is now in the `credential.rs` module of `ene-session-sync`. Deploy scripts (`recover_credential_server.sh`, `nixos-setup-cred-server.sh`) updated to launch the binary. EC2 recovery backup includes NixOS config and AppFlowy compose/env template.

---

*Authoritative roadmap. All other roadmap files are historical reference. Task-level detail: `TODO_MAP.md`. Active milestone: `BURGERS_READINESS_ASSESSMENT.md`.*
