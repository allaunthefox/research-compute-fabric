# TODO Map — Sovereign Stack / Bodega Kernel

**Version:** 0.1  
**Date:** 2026-04-24  
**Scope:** Equation Forest → FPGA route miner → Lean witness  
**Frozen vocabulary:** See §0. Vocabulary Lock

---

## Legend

| Status | Meaning |
|--------|---------|
| ✅ DONE | Built, tested, committed |
| 🔄 IN_PROGRESS | Active work, may have open PR |
| ⏳ BLOCKED | Needs upstream item or external dependency |
| 📋 TODO | Spec'd, ready to start |
| 🧊 ICEBOX | Interesting, not on critical path |

| Layer | Owner | Lang |
|-------|-------|------|
| L0 Formal | Lean | `0-Core-Formalism/lean/Semantics/` |
| L1 Shim | Python | `4-Infrastructure/infra/` |
| L2 RTL | Verilog | `5-Applications/out/verilog/` |
| L3 Bitstream | Build | `5-Applications/out/verilog/*.sh` |
| L4 Surface | FastAPI/WebSocket | `4-Infrastructure/surface/` (new) |

---

## 0. Vocabulary Lock

These names are frozen. No new name without `input type`, `output type`, `failure mode`, `witness format`.

```text
Equation Forest     = graph of mathematical/model objects
F01–F12             = 12 foundation kernel signatures
DIAT                = shell/integer coordinate transform
S3C                 = shell/topological codec
AVMR                = hierarchical vector roll-up
GWL                 = topology / coupling geometry
NII                 = prediction-observation surprise core (n_t = o_t - p_t)
MSNN                = morphic SNN route-prior generator
RGFlow              = torsion-generating admissibility gate
FAMM                = Frustration Aligned Memory Management
PIST                = witness / audit surface
KOT                 = Kinetic Operation Token (action-cost budget)
GCCL                = Geometric, Cognitive, and Compression Law
GCCL-Rep            = Representative Bytecode for GCCL transitions
O-AMMR              = Orthogonal AMMR (committed QR-basis tree)
GCCN                = Global Cognitive Consensus Network
Substrate VM        = executable ISA / opcode layer
Genome18            = 6 × 3-bit bins → 18-bit address
Tang Nano 9K        = proof-of-shape FPGA board
PCIe FPGA           = future math-hell router (VU9P-class)
```

**Deliverable:** `6-Documentation/docs/VOCABULARY_LOCK.md` — frozen  
**Blocked by:** None  **Owner:** Human architect  **Status:** ✅ DONE

---

## Phase H — Photonic Witness (Quandela)

### H1. Perceval Witness-Grammar (3-Mode)
- **What:** Photonic circuit encoding of the Burgers spectral witness $S(x)$.
- **Deliverable:** `5-Applications/tools-scripts/quandela/witness_grammar_photonic.py`
- **Owner:** Python Shim / Hardware  **Lang:** Python (Perceval)
- **Status:** ✅ DONE
- **Next action:** Investigate cloud `sim:slos` minimum photon constraint (1 vs 2).

### H2. Honest Findings Report
- **What:** Technical audit of hardware measurement vs formal proof gaps.
- **Deliverable:** `shared-data/artifacts/quandela_witness_grammar/HONEST_FINDINGS_REPORT.md`
- **Owner:** Agentic Coder
- **Status:** ✅ DONE

### H3. NUVMAP Visualization
- **What:** Tool to plot the NUVMAP projection $(u, v, \text{amplitude})$ of the photonic results.
- **Deliverable:** `5-Applications/tools-scripts/quandela/plot_nuvmap_projection.py`
- **Owner:** Python Shim
- **Status:** ✅ DONE
- **Next action:** None.

### H4. Burgers Formalization (Lean)
- **What:** Formalizing complexity Ω, effective viscosity ν_eff, and stiffening κ.
- **Deliverable:** `0-Core-Formalism/lean/Semantics/Semantics/FNWH/Burgers.lean`
- **Owner:** Agentic Coder
- **Status:** ✅ DONE
- **Result:** Successfully proved `nu_eff_ge_nu0` and `add_one_omega_ge_one`; verified non-negativity of saturating Q16.16 core.

---

## Phase A — Foundation (Data & Registry)

### A1. Equation Registry (Single Source of Truth)
- **What:** One registry row per equation/model: `id`, `canonical_name`, `raw_formula`, `normalized_formula`, `source`, `typed_status`, `proof_status`, `execution_status`, `failure_status`, `nearest_anchors`
- **Inputs:** 38 user equations, 13 historical anchors, 75 physics formulas, anyon math, periodic atoms, Standard Model kernels, ≥5σ signals
- **Deliverable:** `shared-data/data/equations_forest.jsonl` + `MATH_MODEL_MAP.tsv`
- **Owner:** Python shim  **Lang:** Python / JSONL / TSV
- **Status:** ✅ DONE
- **Result:** 1530 entries consolidated; stable UUIDv5s assigned. Ingested prior art from DeleteMe recovery (2026-05-04).

### A2. Formula Canonicalizer
- **What:** Normalize symbols, strip human labels, extract operator skeleton, assign `shape`, `transform`, `persistence` tags
- **Deliverable:** `5-Applications/scripts/canonicalize_formula.py`
- **Owner:** Python shim
- **Status:** ✅ DONE
- **Result:** Regex-based structural normalizer emitting stable `shape_uuid`s.
- **Blocked by:** A1
- **Next action:** Build parser that reads raw LaTeX/ASCII formulas and emits anonymous structural fingerprint

### A3. Kernel Signature Assigner (F01–F12)
- **Status:** ✅ DONE
- **Result:** 12-dim foundation vectors initialized in registry.

### A4. Street & Bridge Assigner
- **Status:** ✅ DONE
- **Deliverable:** `shared-data/data/equation_streets.jsonl`
- **Result:** 1530 models assigned to 5 primary streets.

### A5. Distance Matrix & Supernode Compression
- **Status:** ✅ DONE
- **Deliverable:** `shared-data/data/equation_distance_matrix.csv` + `shared-data/data/supernodes.json`
- **Result:** Computed pairwise distances and clustered into 40 supernodes.

### A6. RRC Equation Projection Surface
- **What:** Project equation records into nearest lawful RRC shapes without treating human labels as ontology.
- **Deliverables:**
  - `4-Infrastructure/shim/rrc_equation_classifier.py`
  - `4-Infrastructure/shim/rrc_equation_classifier_receipt.json`
  - `4-Infrastructure/shim/rrc_equation_classifier_curriculum.jsonl`
  - `4-Infrastructure/shim/rrc_equation_classifier_table.csv`
  - `docs/rrc_equation_classification.md`
  - `Semantics/RRC/Corpus278.lean` — 278 FixtureRows, Python-supplied, Lean-gated ✅
  - `Semantics/RRC/Emit.lean` — alignment classifier (missingPrediction / alignedExact / etc.) ✅
  - `Semantics/AVMIsa/Emit.lean` — sole output boundary; stamps avm.rrc_corpus278.bundle ✅
- **Owner:** Python shim / Lean bridge
- **Status:** 🔄 IN_PROGRESS
- **Result:** 278 equation surfaces projected; 29 CANDIDATE, 249 HOLD. Labels demoted to non-authoritative route hints.
  Lean Compiler surface (RRC.Corpus278 → RRC.Emit → AVMIsa.Emit) implemented and building:
  `lake build Compiler` → 3311 jobs, 0 errors (commit `8d158bf9`).
- **Next action:** Add `scale_band_declared` witnesses and negative-control strength fields,
  then rerun the receipt and measure HOLD deltas.

---

## Phase B — Formal Core (Lean)

### B1. Foundation Kernels in Lean (F01–F12)
- **What:** Typed definitions for all 12 foundation equations with `#eval` witnesses or theorems
- **Deliverables:**
  - `0-Core-Formalism/lean/Semantics/Foundations/ShannonEntropy.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/InformationContent.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/HierarchicalEntropy.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/CarnotEfficiency.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/LandauerBound.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/EnergyBalance.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/MaxwellDemon.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/RiemannianDistance.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/GeodesicConnection.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/SymplecticGeodesicStep.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/AggregateLoad.lean`
  - `0-Core-Formalism/lean/Semantics/Foundations/IntrinsicRatio.lean`
- **Owner:** L0 Formal  **Lang:** Lean 4
- **Status:** 🔄 IN_PROGRESS (partial — some exist in `CooperativeLUT.lean`, `ManifoldPotential.lean`)
- **Blocked by:** None
- **Next action:** Audit existing Lean files; extract/refactor into `Foundations/` namespace; add `#eval` witnesses for each

### B2. Genome18 Lean Spec
- **What:** `structure Genome18` with 6 `Fin 8` bins, injective `addr` function, encoding theorem
- **Deliverable:** `0-Core-Formalism/lean/Semantics/Genome18.lean`
- **Owner:** L0 Formal
- **Status:** ✅ DONE (Extracted from CooperativeLUT.lean on 2026-05-03)

### B3. NS-MΔ (Nibble-Switched Manifold Delta)
- **What:** Sparse topological update protocol with 4-bit CMYK/Control state bridge.
- **Deliverable:** `0-Core-Formalism/lean/Semantics/Semantics/NS_MD.lean`
- **Owner:** L0 Formal / L1 Shim
- **Status:** ✅ DONE
- **Result:** Formalized semantics, Python codec (30x compression), and Verilog decoder implemented. Supports **GCCL-Rep** bytecode transitions.

### B4. Q16_16 Fixed-Point ALU in Lean
- **What:** Saturated add/sub/mul/div/max/min/avg on `Int32` Q16.16 with overflow theorems
- **Deliverable:** `0-Core-Formalism/lean/Semantics/Q16_16.lean`
- **Owner:** L0 Formal
- **Status:** ✅ DONE (Unified UInt32 and Int variants on 2026-05-03)
- **Result:** Q16_16 signed/unsigned bug fix (commit `23bb6303`); `add_pos_of_pos` lemma proved.

### B5. NII Core in Lean
- **What:** `nii : predicted → observed → surprise` with bounded adaptation update rule
- **Deliverable:** `0-Core-Formalism/lean/Semantics/NII.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** B4
- **Next action:** Define `predict`, `observe`, `surprise`, `adapt` functions; add `#eval` test vectors

### B6. FAMM Memory in Lean
- **What:** `fammUpdate : State → RouteResult → State` with basin/scar/prior operations
- **Deliverable:** `0-Core-Formalism/lean/Semantics/FAMM.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** B3, B5
- **Next action:** Define `FAMMState` structure with frustration, torsion, basin, scar fields; prove update totality

### B7. Substrate VM in Lean
- **What:** Opcode enum, `VMState`, `step`, `run`, totality + roundtrip theorems
- **Deliverable:** `0-Core-Formalism/lean/Semantics/SubstrateVM.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** B4
- **Next action:** Define 18-bit ISA opcodes; prove `decode (encode op) = op`

### B8. GWL Topology in Lean
- **What:** Coupling geometry, packet state, throat condition, non-Euclidean distance
- **Deliverable:** `0-Core-Formalism/lean/Semantics/GWLTopology.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** B4
- **Next action:** Define `PacketState` 7-tuple, `ThroatCondition`, `NonEuclideanDistance` functions

### B9. PIST Witness in Lean
- **What:** `witness : Event → ProofStatus → Witness`, `attest : Witness → Bool`
- **Deliverable:** `0-Core-Formalism/lean/Semantics/PIST.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** B3, B7
- **Next action:** Define witness structure; prove `attest` is decidable

### B10. `lake build` CI Gate
- **What:** Every PR must pass `cd 0-Core-Formalism/lean/Semantics && lake build` with zero warnings, zero `sorry`
- **Owner:** L0 Formal + Infra
- **Status:** 📋 TODO
- **Blocked by:** B1–B9
- **Next action:** Add GitHub Actions workflow or local pre-commit hook

### B11. Eigensolid Convergence Theorem
- **What:** Prove that the braid crossing loop stabilizes: `crossStep(s) = s`
- **Deliverable:** `0-Core-Formalism/lean/Semantics/EigensolidConvergence.lean`
- **Owner:** L0 Formal
- **Status:** ✅ DONE
- **Result:** EigensolidConvergence.lean proof complete (commit `d84569a5`)

### B12. Language & Information Transfer Probes (6 modules)
- **What:** Formalize information transfer via media, language substrates, genetic thermodynamic limits, and expanded genetic alphabets
- **Deliverables:**
  - `0-Core-Formalism/lean/Semantics/Semantics/MediaTransferProbe.lean` — 7 media channels, Shannon bandwidths
  - `0-Core-Formalism/lean/Semantics/Semantics/LanguageTransferProbe.lean` — 7 language substrates, strict ordering proved
  - `0-Core-Formalism/lean/Semantics/Semantics/LanguageZoologyProbe.lean` — 6 non-human languages, substrate assignments
  - `0-Core-Formalism/lean/Semantics/Semantics/GeneticThermodynamicLimitProbe.lean` — 10 polymer types, Landauer limit
  - `0-Core-Formalism/lean/Semantics/Semantics/ExpandedGeneticAlphabetProbe.lean` — hachimoji + supernumerary DNA
  - `0-Core-Formalism/lean/Semantics/Semantics/GeneticAnchorProbe.lean` — codon ratio `64/21 ≈ 3.047`
- **Owner:** L0 Formal
- **Status:** ✅ DONE (2026-05-22)
- **Result:** All 6 modules compile; 3592 build jobs green; 10 theorems with `native_decide` receipts

### B13. Thermodynamic Language & Landauer-Shannon Probes
- **What:** Semantic basin capacity, encoding/decoding mismatch, Landauer limit formalization
- **Deliverables:**
  - `0-Core-Formalism/lean/Semantics/Semantics/ThermodynamicLanguageProbe.lean` — basin overflow theorem (M = 50,000,000×)
  - `0-Core-Formalism/lean/Semantics/Semantics/LandauerShannonProbe.lean` — Heisenberg time `1.8×10^-14 s`
  - `0-Core-Formalism/lean/Semantics/Semantics/SemanticBasinOverflowProbe.lean` — consistency between 100× and 50,000,000× mismatch
  - `0-Core-Formalism/lean/Semantics/Semantics/InformationBottleneckLanguageProbe.lean` — `I(X;T) ≤ R` for 7 substrates
- **Owner:** L0 Formal
- **Status:** ✅ DONE (2026-05-22)
- **Result:** All 4 modules compile with `#eval` witnesses

### B14. Citation Provenance File
- **What:** CFF file with 29 verified DOIs for all referenced papers
- **Deliverable:** `6-Documentation/docs/provenance/LANGUAGE_MATH_MODEL_SOURCES.cff`
- **Owner:** L0 Formal / Agentic Coder
- **Status:** ✅ DONE (2026-05-22)
- **Result:** 29 references parsed OK; all Lean probe modules updated with inline REFERENCES blocks

---

## Phase C — Compression Layer

### C1. DIAT Shell Coordinate Transform
- **What:** `(a,b) → (a,b,ab,a-b)` with Q16.16 fixed-point implementation
- **Deliverable:** `0-Core-Formalism/lean/Semantics/DIAT.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** B4
- **Next action:** Define `diatTransform`; prove injectivity or bounded collision rate

### C2. S3C Shell/Topological Codec
- **What:** Shell-state encoding, topological compression, codec `L(X) = Σ bind(zᵢ)`
- **Deliverable:** `0-Core-Formalism/lean/Semantics/S3C.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** C1
- **Next action:** Define `shellEncode`, `shellDecode`; prove roundtrip for typed inputs

### C3. AVMR Vector Roll-Up
- **What:** Hierarchical vector summary from shell coordinates
- **Deliverable:** `0-Core-Formalism/lean/Semantics/AVMR.lean`
- **Owner:** L0 Formal
- **Status:** 📋 TODO
- **Blocked by:** C2
- **Next action:** Define `avmrRollup` from DIAT output; prove bounded error

### C4. Unified Compression MCP
- **What:** `rgflow_compress`, `genetic_compress`, `hybrid_compress` tools exposed via MCP
- **Deliverable:** `tools/mcp/unified_compression/server.py`
- **Owner:** L1 Shim  **Lang:** Python
- **Status:** 📋 TODO
- **Blocked by:** None
- **Next action:** Port ChatGPT-generated MCP scaffold; wire to local `LeanUnifiedShim`

---

## Phase D — FPGA Hardware (Tang Nano 9K)

### D1. Board Constraint Fix (QN88)
- **What:** Correct CST with valid QN88 pins, clock pin 52, LEDs 10-16
- **Deliverable:** `5-Applications/out/verilog/tangnano9k.cst`
- **Owner:** L2 RTL + L3 Bitstream
- **Status:** ✅ DONE
- **Blocked by:** None
- **Next action:** —

### D2. Yosys Synthesis Pass
- **What:** `synth_gowin` produces valid JSON netlist
- **Deliverable:** `5-Applications/out/verilog/tangnano9k.json`
- **Owner:** L3 Bitstream
- **Status:** ✅ DONE (614 cells, 53 LUT4, 120 ALU, 3 DFFC)

### D3. nextpnr Place & Route Pass
- **What:** P&R completes, timing passes
- **Deliverable:** `5-Applications/out/verilog/tangnano9k_pnr.json`
- **Owner:** L3 Bitstream
- **Status:** ✅ DONE (162.28 MHz, PASS at 27 MHz)

### D4. Bitstream Generation
- **What:** `gowin_pack` produces `.fs` file
- **Deliverable:** `5-Applications/out/verilog/tangnano9k.fs`
- **Owner:** L3 Bitstream
- **Status:** ✅ DONE (2.0 MB)

### D5. Simulation Testbench (5 Virtual Boards)
- **What:** Icarus Verilog testbench with 11 assertions, all passing
- **Deliverable:** `5-Applications/out/verilog/tangnano9k_topology_router_tb.v`
- **Owner:** L2 RTL
- **Status:** ✅ DONE

### D6. LUT Address Test
- **What:** 16×4 LUT-ROM test with pass/fail LEDs
- **Deliverable:** `5-Applications/out/verilog/LutAddressTest.v` + `lut_address_test_tb.v`
- **Owner:** L2 RTL
- **Status:** ✅ DONE (build passes, bitstream generated)

### D7. UART Packet Interface
- **What:** Host feeds 18-bit route states over UART; FPGA returns verdict + torsion
- **Deliverable:** `5-Applications/out/verilog/UartPacketInterface.v`
- **Owner:** L2 RTL
- **Status:** 📋 TODO
- **Blocked by:** D4
- **Next action:** Design packet format (start byte, payload, checksum); implement RX/TX state machines; test with `picocom` or Python `pyserial`

### D8. Genome18 Encoder (RTL)
- **What:** Combinational 6×3-bit → 18-bit address (matches Lean spec)
- **Deliverable:** `5-Applications/out/verilog/Genome18Encoder.v` (extracted from current `TangNano9KTopologyRouter`)
- **Owner:** L2 RTL
- **Status:** ✅ DONE (exists inside `tangnano9k_topology_router.v`)
- **Blocked by:** None
- **Next action:** Extract into standalone module for reuse

### D9. RGFlow Gate (RTL)
- **What:** LUT-based lawfulness scorer from 18-bit address + feature bins
- **Deliverable:** `5-Applications/out/verilog/RGFlowGate.v`
- **Owner:** L2 RTL
- **Status:** 🔄 IN_PROGRESS (partial in `TangNano9KTopologyRouter`)
- **Blocked by:** D8, D7
- **Next action:** Define LUT contents from Lean `rgflowLawful`; load via `$readmemh` or hardcoded case statement

### D10. FAMM Scar/Basin LUT (RTL Stub)
- **What:** Small RAM (4096 entries × 24 bits) storing torsion, frustration, basin flags
- **Deliverable:** `5-Applications/out/verilog/FAMMLUT.v`
- **Owner:** L2 RTL
- **Status:** 📋 TODO
- **Blocked by:** D9
- **Next action:** Use Gowin B-SRAM primitive; implement read/write interface; test persistence across resets

### D11. NII Core (RTL)
- **What:** `predict → observe → subtract → normalize → clip` pipeline in fixed-point
- **Deliverable:** `5-Applications/out/verilog/NIICore.v`
- **Owner:** L2 RTL
- **Status:** 📋 TODO
- **Blocked by:** B5
- **Next action:** Implement leaky integrator predict; synchronous observation latch; Q16.16 subtract with saturation

### D12. Morphic SNN (RTL Minimal)
- **What:** 16–64 LIF neurons, sparse synapses, STDP-like update, UART I/O
- **Deliverable:** `5-Applications/out/verilog/MSNNCore.v`
- **Owner:** L2 RTL
- **Status:** 🧊 ICEBOX
- **Blocked by:** D11, D10
- **Next action:** Start with 16 neurons on Tang Nano; scale to thousands on PCIe FPGA

### D13. LED Status Mapper
- **What:** Map internal state (lawful, critical, stable, routing, regime, heartbeat) to 6 LEDs
- **Deliverable:** `5-Applications/out/verilog/LEDStatusMapper.v`
- **Owner:** L2 RTL
- **Status:** ✅ DONE (inside `TangNano9KBoardTest.v`)

---

## Phase E — FPGA Hardware (PCIe Card — Future)

### E1. PCIe DMA Interface
- **What:** Host → FPGA streaming via PCIe Gen3 x16
- **Deliverable:** `5-Applications/out/verilog/pcie/DmaEngine.v`
- **Owner:** L2 RTL
- **Status:** 🧊 ICEBOX
- **Blocked by:** Hardware acquisition (Alibaba Cloud VU9P-class card)
- **Next action:** Identify exact card model; port DMA reference design

### E2. Batch Route-Worker Array
- **What:** Array of RGFlow gates processing route states in parallel
- **Deliverable:** `5-Applications/out/verilog/pcie/RouteWorkerArray.v`
- **Owner:** L2 RTL
- **Status:** 🧊 ICEBOX
- **Blocked by:** E1, D9

### E3. FAMM Large Memory Window
- **What:** DDR4-backed FAMM with millions of scar/basin entries
- **Deliverable:** `5-Applications/out/verilog/pcie/FAMMDDR.v`
- **Owner:** L2 RTL
- **Status:** 🧊 ICEBOX
- **Blocked by:** E1, D10

### E4. Host-FPGA Co-Simulation
- **What:** Python/C++ host model vs FPGA RTL equivalence checking
- **Deliverable:** `5-Applications/tests/fpga_cosim/`
- **Owner:** L1 Shim + L2 RTL
- **Status:** 🧊 ICEBOX
- **Blocked by:** E1

---

## Phase F — Surface & Interface

### F1. Topological FastAPI Server
- **What:** Local backend with WebSocket, file watcher, compression, route scoring
- **Deliverable:** `4-Infrastructure/surface/main.py`
- **Owner:** L4 Surface  **Lang:** Python (FastAPI)
- **Status:** 📋 TODO
- **Blocked by:** None
- **Next action:** Create `4-Infrastructure/surface/`; implement `/ws` endpoint; mount static `index.html`

### F2. Codex-Like Virtual Surface (Browser UI)
- **What:** Local HTML/JS frontend for file loading, equation display, route visualization
- **Deliverable:** `4-Infrastructure/surface/static/index.html` + `app.js`
- **Owner:** L4 Surface
- **Status:** 📋 TODO
- **Blocked by:** F1
- **Next action:** Build minimal UI: file tree, equation viewer, kernel signature bar, route map canvas

### F3. MCP Surface Router
- **What:** Autoroutes tasks to local MCP tools (compression, RGFlow, Lean, etc.)
- **Deliverable:** `4-Infrastructure/surface/mcp_router.py`
- **Owner:** L4 Surface
- **Status:** 📋 TODO
- **Blocked by:** C4, F1
- **Next action:** Integrate `unified_compression_mcp`; add tool-discovery endpoint

### F4. Local MoE (Mixture of Experts)
- **What:** Router that dispatches to specialized local models/experts
- **Deliverable:** `4-Infrastructure/surface/moe_router.py`
- **Owner:** L4 Surface
- **Status:** 🧊 ICEBOX
- **Blocked by:** F3
- **Next action:** Define expert taxonomy: RGFlow, genetic, GWL, FAMM, Lean, FPGA, Planet Nine, general

### F5. WebSocket Dev Hook
- **What:** Browser ↔ FastAPI ↔ local files ↔ MCP ↔ MoE loop
- **Deliverable:** Working in F1 + F2 + F3
- **Owner:** L4 Surface
- **Status:** 📋 TODO
- **Blocked by:** F1, F2, F3
- **Next action:** Ensure `allowed_workspace/` is the only disk-exposed path; no arbitrary file reads

---

## Phase G — Integration & Test

### G1. Lean → Verilog Extraction
- **What:** Formal Lean spec lowers to synthesizable Verilog via codegen or manual extraction
- **Deliverable:** `tools/codegen/lean_to_verilog.py`
- **Owner:** L0 Formal + L2 RTL
- **Status:** 📋 TODO
- **Blocked by:** B1–B9, D8–D12
- **Next action:** Start with `Genome18` (simple structure); prove Lean `addr` == Verilog `addr`

### G2. LeanGPT Spec Generator Hook
- **What:** LLM generates Lean definitions/theorems from natural language hardware contracts
- **Deliverable:** `tools/codegen/leangpt_prompt_template.md`
- **Owner:** L1 Shim
- **Status:** 🧊 ICEBOX
- **Blocked by:** G1
- **Next action:** Design prompt template with strict output format; validate with `lake build`

### G3. Equivalence Checking (Lean vs Verilog vs Python)
- **What:** Same test vectors run through all three implementations; compare outputs bit-exact
- **Deliverable:** `5-Applications/tests/equivalence/`
- **Owner:** L0 Formal + L1 Shim + L2 RTL
- **Status:** 📋 TODO
- **Blocked by:** G1
- **Next action:** Start with Genome18 address: Lean `#eval`, Verilog `$display`, Python `assert`

### G4. Planet Nine Candidate Live Query
- **What:** Execute IRSA/VizieR/Gaia queries for P9 follow-up corridor; score results
- **Deliverable:** `5-Applications/scripts/p9_followup_query.py`
- **Owner:** L1 Shim
- **Status:** 📋 TODO
- **Blocked by:** Network access
- **Next action:** Run generated query queue against IRSA, SIMBAD, MPC; update FAMM with results

### G5. FPGA Flash & Bringup
- **What:** Program Tang Nano 9K SRAM with `tangnano9k.fs`; verify LED behavior
- **Deliverable:** Working hardware
- **Owner:** L3 Bitstream + Human
- **Status:** ⏳ BLOCKED
- **Blocked by:** Physical board + programmer cable + `openFPGALoader` or Gowin programmer
- **Next action:** Install `openFPGALoader`; connect board via USB; flash bitstream; verify LEDs cycle

### G6. UART Loopback Test
- **What:** Host sends packet, FPGA echoes or responds with RGFlow verdict
- **Deliverable:** Working UART comms
- **Owner:** L3 Bitstream + L1 Shim
- **Status:** 📋 TODO
- **Blocked by:** D7, G5
- **Next action:** Python `pyserial` script sends 18-bit state; reads verdict byte; compares to Python model

---

## Dependency Graph

```text
A0 (Vocab Lock)
  → A1 (Registry)
    → A2 (Canonicalizer)
      → A3 (Kernel Signatures)
        → A4 (Streets)
          → A5 (Distance Matrix)

B1 (F01–F12)
  → B2 (Genome18)
    → B3 (RGFlow Lean)
    → C1 (DIAT)
      → C2 (S3C)
        → C3 (AVMR)
  → B4 (Q16_16)
    → B5 (NII)
    → B6 (FAMM)
    → B7 (Substrate VM)
    → B8 (GWL)
    → C1 (DIAT)
  → B3 + B5 + B6 + B7 + B8
    → B9 (PIST)

D1–D4 (Tang Nano Build)
  → D5 (Simulation)
  → D6 (LUT Test)
  → D7 (UART)
    → D8 (Genome18 RTL) [parallel with B2]
      → D9 (RGFlow RTL) [parallel with B3]
        → D10 (FAMM RTL) [parallel with B6]
          → D11 (NII RTL) [parallel with B5]
            → D12 (MSNN RTL) [parallel, ICEBOX]

B2 + D8 → G1 (Lean → Verilog)
B3 + D9 → G3 (Equivalence)
D7 + G5 → G6 (UART Loopback)

C4 (Compression MCP) + F1 (FastAPI)
  → F3 (MCP Router)
    → F4 (MoE)

F1 + F2 + F3 + F5
  → Full surface working
```

---

## Current Blockers

| # | Blocker | Unblocks | Mitigation |
|---|---------|----------|------------|
| 1 | Vocabulary not formally locked (A0) | A1–A5, B1–B9 | Human sign-off on `6-Documentation/docs/VOCABULARY_LOCK.md` |
| 2 | Tang Nano 9K not physically connected | G5, G6 | Acquire USB cable; install `openFPGALoader` |
| 3 | PCIe FPGA card not acquired | E1–E4 | Source second-hand Alibaba Cloud VU9P card |
| 4 | No network query runner for P9 | G4 | Run `5-Applications/scripts/p9_followup_query.py` from network-enabled host |
| 5 | `sorry` in existing Lean files | B10 | Audit `0-Core-Formalism/lean/Semantics/` for `sorry`/`admit`/`axiom`; replace with proofs or `#eval` witnesses |
| 6 | RRC projection HOLD surface lacks scale-band witnesses | A6, B10, C2 | Add scale-band schema to equation records; rerun RRC receipt; only promote rows whose HOLD clears |

---

## Immediate Next Actions (This Session)

### Priority: Language-Genetic-Thermodynamic Bridge (Completed 2026-05-22)
1. ✅ **GeneticSignalTransformProbe.lean** — Formalize unified power law `P ∝ S^{1/2} · λ_φ^{D_f} · exp(-γ·ΔE_eff/kT)` from SIGNAL_ANALYSIS_GENETIC_IMPLICATIONS.md; bridge Drake's Rule + LTEE fitness
2. ✅ **SemanticBasinOverflowProbe.lean** — Prove generative singularity consistency: `LanguageTransferProbe` 100× bandwidth jump is lower bound on `ThermodynamicLanguageProbe` 50,000,000× mismatch
3. ✅ **GeneticErrorMinimizationProbe.lean** — Formalize Freeland & Hurst claim: standard code is `~10^6×` better than random; connect to `ExpandedGeneticAlphabetProbe` optimality proof
4. ✅ **InformationBottleneckLanguageProbe.lean** — Formalize Tishby's IB `I(X;T) ≤ R` as constraint on all 7 language substrates
5. ✅ **CrossModalGeneticLanguageProbe.lean** — Bridge `CrossModalCompression` with language framework: morphogenesis as cross-modal genetic language flow
6. ✅ **LandauerGeneticClockProbe.lean** — Calculate minimum thermodynamic cost of maintaining genetic info across generations; answer `GeneticAnchorProbe` P0 anchoring question

### Ongoing Infrastructure
7. **Repair RRC projection HOLDs** — Add `scale_band_declared` witnesses for equation records; rerun `4-Infrastructure/shim/rrc_equation_classifier.py`
8. **Add negative controls** — Add negative-control strength witnesses for the 39 rows exposing weak control evidence
9. **Audit Lean for `sorry`** — `grep -rn "sorry\|admit\|axiom" 0-Core-Formalism/lean/Semantics/`; file count and locations
10. **Design UART packet format** — 1-byte start, 3-byte payload (18-bit state + 6-bit flags), 1-byte checksum

---

## Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Lean build jobs green | 3585+ | ✅ 3592 |
| Language-genetic-thermodynamic probes | 14 | ✅ 14 (MediaTransfer, LanguageTransfer, LanguageZoology, GeneticThermodynamicLimit, ExpandedGeneticAlphabet, GeneticAnchor, ThermodynamicLanguage, LandauerShannon, GeneticSignalTransform, SemanticBasinOverflow, GeneticErrorMinimization, InformationBottleneckLanguage, CrossModalGeneticLanguage, LandauerGeneticClock) |
| CFF provenance files with DOIs | 3 | ✅ 3 (DNA_CODEC_FILTER, ALPHAFOLD_BULK, LANGUAGE_MATH_MODEL) |
| Lean files with zero `sorry` | 100% | TBD |
| FPGA build passing | 100% | ✅ |
| FPGA timing margin | >2× | ✅ 6× |
| Equations in registry | 200+ | 0 (ChatGPT sandbox only) |
| Supernodes for exact TSP | 30–45 | 0 |
| Foundation kernel theorems | 12 | ~3 partial |
| UART packet roundtrip | <1 ms | N/A |
| FAMM LUT entries on Tang Nano | 4096 | 0 |
| Surface endpoints working | 5+ | 0 |

---

*Generated by Kimi Code CLI — 2026-04-24*  
*Frozen vocabulary effective immediately pending human approval*

---

## Phase K — Standards Conformance & Adapters
- **What:** Bridge the gap between "Architecture-aligned" and "Conformance-tested".
- **Deliverables:**
    - [ ] **ISO 26262 Safety Case:** HARA/FMEA for the Q16.16 core
    - [ ] **W3C DID/VC Schema:** Canonical signature suites for GCCL-Rep
    - [ ] **MPEG-G Adapter:** Conformance test suite for Genome18
    - [ ] **Reproducible Replay Harness:** Canonical execution witness for AVMR/AMMR
- **Status:** 🌑 NOT_STARTED
- **Blocked by:** Phase B, C, D
- **Owner:** Human architect / L1 Shim

---

## Phase I — Infrastructure & Data Layer

### I1. ENE RDS Rust Workspace
- **What:** 8-crate Rust workspace replacing Python RDS stack: ene-rds-core, ene-rds-wiki, ene-rds-ephemeral, ene-rds-chat, ene-api, ene-node, ene-storage, ene-sync
- **Deliverable:** `4-Infrastructure/infra/ene-rds/`
- **Status:** ✅ DONE
- **Result:** Cargo build passing (sqlx 0.8.6, Axum HTTP on :3000, Ollama embedding, PostgreSQL RDS). Dependabot sqlx 0.7→0.8.6 vuln fixed.

### I2. Garage S3 Storage Stack
- **What:** Self-hosted S3-compatible object store (Garage v2.3.0) over Tailscale mesh with 5 buckets
- **Deliverable:** `4-Infrastructure/storage/garage/`
- **Status:** ✅ DONE (single-node, replication_factor=1)
- **Next action:** Bootstrap nixos-laptop and microvm-racknerd into Garage; 361395-1 needs SSH recovery first

### I3. Storage Observer/Optimizer Agent
- **What:** Observe → Decide → Act loop with Q16_16 thresholds, JSONL hash-chain receipts, dual S3+local sinks
- **Deliverable:** `4-Infrastructure/storage/storage_agent.py`
- **Status:** ✅ DONE
- **Result:** systemd timer (every 15 min), triggers: snap/cold-copy/verify/forget/offload/garage-restart

### I4. NixOS Devcontainer Flake
- **What:** Hermetic NixOS devcontainer with OpenGL/X11, pkg-config, openssl, full Python science stack, MCP Notion + AWS servers
- **Deliverable:** `.devcontainer/flake.nix` + `devcontainer.json`
- **Status:** ✅ DONE

### I5. Credential Gateway & EC2 Recovery
- **What:** apiProvider service kind, credential server, cupfox routing, EC2 recovery backup (NixOS config, AppFlowy compose/env template)
- **Deliverable:** `4-Infrastructure/infra/credential_server.py`, `4-Infrastructure/infra/ec2-configuration.nix`
- **Status:** ✅ DONE

### I6. Garage Replication Scale-Out (3 nodes)
- **What:** Bootstrap nixos-laptop and microvm-racknerd, run garage-cluster-init.sh, set replication_factor=3; 361395-1 after SSH recovery
- **Deliverable:** Updated `4-Infrastructure/storage/garage/node-registry.json` + cluster receipt
- **Status:** 📋 TODO
- **Blocked by:** Node provisioning
- **Next action:** Run `garage-node-bootstrap.sh 100.119.165.120`, `garage-node-bootstrap.sh 100.101.247.127`, then `garage-cluster-init.sh`; 361395-1 (100.110.163.82) needs SSH password recovery before bootstrap

---

## Phase J — Adversarial Harnesses & Gate Library

### J1. Anti-FAMM / Anti-BraidStorm Adversarial Harnesses
- **What:** Anti-FAMM shadow adversary + Anti-BraidStorm hostile crossing gate with 16D anchor packs, runners, receipt schemas
- **Deliverable:** `4-Infrastructure/shim/adversarial_duals/`
- **Status:** ✅ DONE

### J2. Gate Library Expansion
- **What:** BraidStorm Sidon Crossing, Golden Braid Centering, Autonomous speedrun, MarkovJunior 16D PIST rewrite, Sidon FAMM map, Builder-Judge-Warden geodesic cleanup, Logogram chirality, NUVMAP Delta-DAG, Common-noise MFG Riccati, Bio-organoid signal field, 16D Chaos Game, FAMM Semantic Mass plow + Z-accelerator, FAMM Hessian curvature, Möbius-Apollonius, Chromatic Homotopy Height Spectral, Ahmed Integral, Universal Shortcut Center Manifold, Plasma Chiral Drag, Feynman path-integral shadow, Navier-Stokes shadow control gap map, OR-Tools WASM constraint solver, SmallCode constrained agent
- **Status:** ✅ DONE (all gates have documentation, receipt schemas, and runners)

### J3. Constrained Agent Framework (GLIA)
- **What:** Document constrained agent approaches with GLIA; SmallCode execution gate; OR-Tools WASM solver gate
- **Status:** ✅ DONE (documentation complete; GLIA integration pending)
