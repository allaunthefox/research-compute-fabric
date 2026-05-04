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

---

## Immediate Next Actions (This Session)

1. **Lock vocabulary** — Create `6-Documentation/docs/VOCABULARY_LOCK.md` from §0 above; get human approval
2. **Audit Lean for `sorry`** — `grep -rn "sorry\|admit\|axiom" 0-Core-Formalism/lean/Semantics/`; file count and locations
3. **Extract Genome18** — Move from `CooperativeLUT.lean` to standalone `Genome18.lean`
4. **Design UART packet format** — 1-byte start, 3-byte payload (18-bit state + 6-bit flags), 1-byte checksum
5. **Create `4-Infrastructure/surface/` skeleton** — FastAPI app with `/health` and `/ws` endpoints
6. **Flash the board** — Install `openFPGALoader`; program `tangnano9k.fs`; verify LEDs

---

## Metrics

| Metric | Target | Current |
|--------|--------|---------|
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

## Phase I — Standards Conformance & Adapters
- **What:** Bridge the gap between "Architecture-aligned" and "Conformance-tested".
- **Deliverables:**
    - [ ] **ISO 26262 Safety Case:** HARA/FMEA for the Q16.16 core
    - [ ] **W3C DID/VC Schema:** Canonical signature suites for GCCL-Rep
    - [ ] **MPEG-G Adapter:** Conformance test suite for Genome18
    - [ ] **Reproducible Replay Harness:** Canonical execution witness for AVMR/AMMR
- **Status:** 🌑 NOT_STARTED
- **Blocked by:** Phase B, C, D
- **Owner:** Human architect / L1 Shim
