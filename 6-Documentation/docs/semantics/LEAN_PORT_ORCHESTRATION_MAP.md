# Lean Port Orchestration Map

**Mission:** Forced, systematic port of every repository domain to Lean 4.  
**Principle:** There is only one orchestration layer — Lean. All other languages become extraction targets or shims.  
**Non-goal:** Big-bang rewrite. Port one module at a time; `lake build` must never break.

---

## 1. The Single Orchestration Layer (SOL)

The orchestration layer is `0-Core-Formalism/lean/Semantics/`. It is the only place where:
- Invariants are checked
- Costs are computed
- State transitions are validated
- Conservation laws are enforced
- Branching decisions are made

Every other file in the repository must fall into one of three categories:

| Category | Rule |
|----------|------|
| **Lean Core** | Source of truth. Compiles with `lake build`. |
| **Thin Shim** | I/O, serialization, hardware pinout, or OS integration. No logic. |
| **Deleted** | Cannot be typed, cannot be proven, or duplicates a Lean module. |

---

## 2. Domain-by-Domain Port Map

### 2.1 Semantic / Physical Foundation
**Current:** `0-Core-Formalism/lean/Semantics/` (28 modules, compiling)  
**Status:** ✅ **Already the SOL**  
**Shims:** `infra/access_control/bind_engine.py` (minimal loader)  
**Action:** Expand to subsume all remaining model families.

| Target Module | Replaces | Fate |
|---------------|----------|------|
| `Semantics/Physics/` | Python physical cost functions | **Keep Lean, delete Python** |
| `Semantics/FixedPoint.lean` | All `f32`/`f64` hot paths | **Port-dependent modules to Q16.16** |
| `Semantics/Bind.lean` | All geometry/compression/control plugins | **Collapse into `bind` instances** |
| `Semantics/Graph.lean` | `core/gwl-vm/src/dag_hybrid.rs` | **Port DAG logic to Lean** |
| `Semantics/Path.lean` | `core/src/earth_propagation.rs` | **Port path semantics** |

---

### 2.2 Python Pipeline / PBACS
**Current:** `infra/access_control/`  
**Language:** Python  
**Fate:** **Collapse to one shim file.**

| Current File | Lean Target | Fate |
|--------------|-------------|------|
| `bind_engine.py` | `BindServer.lean` | **Keep as shim** (already done) |
| `pipeline/unified_pipeline.py` | `Semantics/Orchestrate.lean` (new) | **Port logic; keep shim wrapper** |
| `geometry/geometry_plugin_v2.py` | `Semantics/Bind.lean` (`geometric_bind`) | **Delete** (replaced by `bind_engine.py`) |
| `core/pbacs_core.py` | `Semantics/Canon.lean` + `Constitution.lean` | **Port canonical state to Lean** |
| `core/canonical_state.py` | `Semantics/Canon.lean` | **Port** |
| `adapters/compression_adapter.py` | `Semantics/Bind.lean` (`informational_bind`) | **Port to Q16.16 KL cost** |
| `adapters/market_adapter.py` | `Semantics/Evolution.lean` | **Port regime transitions** |
| `topological_tape_machine.py` | `Semantics/Path.lean` + `Witness.lean` | **Port tape semantics** |
| `kimi_context_optimizer.py` | `Semantics/Substrate.lean` | **Delete or demote to util script** |
| `demo_context_compression.py` | — | **Delete** (demo only) |
| `tests/test_compliance_fixes.py` | `#eval` tests in Lean | **Port assertions to `#eval` / theorems** |
| `tests/test_unified_pipeline.py` | `#eval` tests in Lean | **Port assertions** |

---

### 2.3 Rust Core / GWL-VM
**Current:** `core/gwl-vm/src/`, `core/src/`  
**Language:** Rust  
**Fate:** **Extract from Lean; keep only FFI, I/O, and hardware bindings.**

| Current File | Lean Target | Fate |
|--------------|-------------|------|
| `gwl-vm/src/bytecode.rs` | `Semantics/Substrate.lean` (opcode enum) | **Port opcodes to Lean; Rust becomes executor** |
| `gwl-vm/src/vm.rs` | `Semantics/Substrate.lean` + `Semantics/Path.lean` | **Port VM step function; Rust is runtime** |
| `gwl-vm/src/dag_hybrid.rs` | `Semantics/Graph.lean` + `Semantics/Path.lean` | **Port DAG validation to Lean** |
| `gwl-vm/src/robust.rs` | `Semantics/Diagnostics.lean` | **Port diagnostics** |
| `gwl-vm/src/xtaf.rs` | `Semantics/Witness.lean` | **Port witness format** |
| `gwl-vm/examples/hybrid_dag_demo.rs` | `#eval` in Lean | **Delete Rust demo; replace with Lean `#eval`** |
| `gwl-vm/examples/cache_ipc_benchmark.rs` | — | **Delete or move to `5-Applications/tools-scripts/`** |
| `src/warden.rs` | `Semantics/Prohibited.lean` | **Port prohibited-state logic** |
| `src/regime_driver.rs` | `Semantics/Evolution.lean` | **Port regime transitions** |
| `src/engines/context_gate.rs` | `Semantics/Projections.lean` | **Port projection logic** |
| `src/dsp_neuromorphic_translation.rs` | `Semantics/Substrate.lean` | **Port to fixed-point DSP semantics** |
| `src/braid_neuromorphic_translation.rs` | `Semantics/Substrate.lean` | **Port braid translation** |
| `src/cipher_integration.rs` | `Semantics/Prohibited.lean` + crypto specs | **Port to formalized cipher constraints** |
| `src/earth_propagation.rs` | `Semantics/Path.lean` | **Port propagation rules** |
| `attest_wasm/src/*.rs` (scorer, decisions) | `Semantics/Diagnostics.lean` + `Bind.lean` | **Port scoring to Lean cost functions** |

---

### 2.4 Hardware Description (Verilog)
**Current:** `core/hw/`  
**Language:** Verilog / SystemVerilog  
**Fate:** **Keep as ultimate extraction target. No Verilog logic gets ported *to* Lean; instead, Lean specs *drive* Verilog generation.**

| Current File | Lean Target | Fate |
|--------------|-------------|------|
| `core/hw/bt20_*.v` / `*.vh` | `Semantics/Substrate.lean` + `FixedPoint.lean` | **Keep Verilog; generate from Lean spec** |
| `core/hw/tsm_phonon_ring_v11.v` | `Semantics/Substrate.lean` | **Keep; formal spec in Lean** |
| `core/hw/diat_phonon_node.v` | `Semantics/Physics/` | **Keep; verified against conservation laws** |
| `core/hw/circuits/ges_rollup.circom` | — | **Evaluate for deletion** (Circom is a separate toolchain) |

**Rule:** Verilog is the **physical instantiation layer**. Lean proves that the Verilog satisfies the spec; it does not replace the HDL.

---

### 2.5 Transport / Routing / Omnitoken
**Current:** `infra/routing/`, `5-Applications/tools-scripts/mining/`  
**Language:** Python  
**Fate:** **Collapse to a single transport shim. All routing logic ported to Lean.**

| Current File | Lean Target | Fate |
|--------------|-------------|------|
| `routing/transport/transport_organism.py` | `Semantics/Graph.lean` | **Port routing graph to Lean** |
| `routing/transport/omni_resolver.py` | `Semantics/Substrate.lean` | **Port resolution logic** |
| `routing/compute/warden.py` | `Semantics/Prohibited.lean` | **Port warden rules** |
| `routing/compute/aether_engine.py` | `Semantics/Path.lean` | **Port aether propagation** |
| `routing/moe/router.py` | `Semantics/Graph.lean` | **Port MOE routing to graph traversal** |
| `routing/moe/omnitoken_metrics.py` | `Semantics/Diagnostics.lean` | **Port metrics to Q16.16** |
| `scripts/mining/i2p_transport_adapter.py` | — | **Keep as thin I2P shim** |
| `scripts/mining/mimo_transport_router.py` | `Semantics/Graph.lean` | **Port router logic** |
| `scripts/mining/dht_layer.py` | `Semantics/Graph.lean` | **Port DHT overlay logic** |

---

### 2.6 TSM / Category Miners
**Current:** `infra/CATEGORY/TSM/`, `infra/CATEGORY/PTOS/`  
**Language:** Python  
**Fate:** **Delete or port. Most are ad-hoc scrapers and demos.**

| Current File | Fate |
|--------------|------|
| `TSM/TSM_COMPILER.py` | **Port core compiler to Lean** (`Semantics/Substrate.lean`) |
| `TSM/tsm_stark_module.py` | **Port to Lean STARK framework** (or delete if duplicate) |
| `TSM/ptos_compile_tsm.py` | **Delete** (bridge to nowhere) |
| `TSM/shipping_route_optimizer.py` | **Delete** (application demo) |
| `TSM/gold_rush_predictor.py` | **Delete** |
| `TSM/global_geology_scraper.py` | **Delete** |
| `PTOS/ptos_moe_router.py` | **Port to Lean** (`Semantics/Graph.lean`) |
| `PTOS/ptos_gpgpu_executor.py` | **Delete** (executor shim only) |
| `PTOS/search_ptos.py` | **Delete** (utility script) |

---

### 2.7 Lab / Experiments
**Current:** `lab/`  
**Language:** Rust, Python  
**Fate:** **Promote the proven; delete the rest.**

| Current File | Fate |
|--------------|------|
| `lab/bracket_braid_sb/` (Rust) | **Port to Lean** (`Semantics/Substrate.lean` or new `Semantics/Optimization.lean`) |
| `lab/hutter_bind_implementation/` | **Port to Lean** (bind primitive already subsumes this) |
| `lab/compression_comparison/` | **Delete** (benchmark data only) |
| `lab/consensus_net/` | **Port to Lean** (`Semantics/Graph.lean` + `Witness.lean`) |
| `lab/physics_fea/` | **Evaluate**; port finite-element invariants to Lean Physics |
| `lab/openwebui_moe_router/` | **Delete** (UI shim, out of scope) |
| `lab/openwebui_tools/` | **Delete** |
| `lab/mevbot/` | **Delete** |
| `lab/sme_blackboard/` | **Evaluate**; likely delete |

---

### 2.8 Documentation / Specifications
**Current:** `docs/`  
**Fate:** **Specs migrate into Lean theorems and docstrings. Markdown becomes human-readable export only.**

| Current Doc | Lean Target |
|-------------|-------------|
| `docs/semantics/BIND_BRIDGE_EQUATIONS.md` | Comments in `Semantics/Bind.lean` |
| `docs/physics/PHYSICAL_SEMANTICS_PARADIGM.md` | Module docstrings in `Semantics/Physics/` |
| `docs/PTOS_TAG_SCHEMA.md` | `Semantics/Canon.lean` + `Substrate.lean` |
| `docs/TSM-AAC_v1_spec.md` | `Semantics/Substrate.lean` (opcode spec) |
| `docs/SOVEREIGN_STACK_ARCHITECTURE.md` | Export from Lean module graph |

---

## 3. The Port Sequence (Phases)

### Phase 0: Foundation (DONE)
- `Semantics/Bind.lean`
- `Semantics/Physics/`
- `Semantics/FixedPoint.lean`
- `BindServer.lean` (JSON shim)

### Phase 1: Pipeline Collapse
1. Port `infra/access_control/core/canonical_state.py` → `Semantics/Canon.lean`
2. Port `infra/access_control/core/pbacs_core.py` → `Semantics/Constitution.lean`
3. Port `infra/access_control/pipeline/unified_pipeline.py` → `Semantics/Orchestrate.lean`
4. Port `infra/access_control/topological_tape_machine.py` → `Semantics/Path.lean` extensions
5. Delete `geometry_plugin_v2.py`

### Phase 2: Rust Core Extraction
1. Port `core/gwl-vm/src/bytecode.rs` → `Semantics/Substrate.lean` (opcode enum + decoder)
2. Port `core/gwl-vm/src/vm.rs` → `Semantics/Substrate.lean` (VM step function)
3. Port `core/gwl-vm/src/dag_hybrid.rs` → `Semantics/Graph.lean`
4. Port `src/warden.rs` → `Semantics/Prohibited.lean`
5. Port `src/regime_driver.rs` → `Semantics/Evolution.lean`

### Phase 3: Transport & Routing
1. Port `infra/routing/moe/router.py` → `Semantics/Graph.lean`
2. Port `infra/routing/compute/warden.py` → `Semantics/Prohibited.lean`
3. Port `infra/routing/transport/transport_organism.py` → `Semantics/Graph.lean`
4. Collapse omnitoken metrics to `Semantics/Diagnostics.lean`

### Phase 4: Lab Promotion
1. Port `lab/bracket_braid_sb/` → `Semantics/Optimization.lean`
2. Port `lab/consensus_net/` → `Semantics/Graph.lean`
3. Port `lab/hutter_bind_implementation/` → `Semantics/Bind.lean`

### Phase 5: Hardware Verification Bridge
1. Formalize BT20 subregisters in `Semantics/Substrate.lean`
2. Write theorems proving Verilog modules satisfy Lean specs
3. Generate SystemVerilog assertions from Lean proofs

---

## 4. Deletion Criteria (Hard Rules)

A file **must be deleted** if any of the following apply:

1. **It is a demo or test script with no invariant.** (`demo_*.py`, benchmark scraps)
2. **It duplicates a Lean module.** (`geometry_plugin_v2.py`, `physical_cost` in Python)
3. **It cannot be typed without `unsafe` or `sorry`.** (hand-wavy ML models, stringly-typed dispatch)
4. **It is an application/integration with external SaaS.** (OpenWebUI tools, scrapers)
5. **It contains logic that resists `bind` collapse.** If it cannot be expressed as `bind(a, b, metric)`, it is either ill-posed or needs redesign.

---

## 5. Shim Specifications

### 5.1 Python Shim (`bind_engine.py` pattern)
**Allowed:**
- `subprocess` spawn of Lean executable
- JSON serialization
- History deque (n-local topology)
- Result dataclass wrapping

**Forbidden:**
- Cost computation
- Invariant checking
- Conservation law evaluation
- Branching decisions

### 5.2 Rust Shim (`gwl-vm` executor pattern)
**Allowed:**
- Opcode fetch/decode from byte stream
- Register file manipulation
- Memory I/O
- FFI call into compiled Lean library

**Forbidden:**
- DAG validation logic
- Decision scoring
- Prohibited-state checking
- Evolution rules

### 5.3 Verilog Boundary
**Allowed:**
- Combinatorial logic derived from Lean specs
- Register transfers
- Pin-level I/O

**Forbidden:**
- Nothing; Verilog is the physical layer. But it must be **provably correct** against Lean specs.

---

## 6. Target Lake Module Architecture

```
Semantics/
├── Bind.lean                    (the universal primitive)
├── FixedPoint.lean              (Q16.16 hardware-native arithmetic)
├── Canon.lean                   (canonical state / PBACS core)
├── Constitution.lean            (prohibited / allowed state predicates)
├── Evolution.lean               (state transitions / regime driver)
├── Graph.lean                   (DAGs, routing, MOE, DHT)
├── Path.lean                    (tape machine, propagation, timelines)
├── Substrate.lean               (opcodes, VM, bytecodes, registers)
├── Physics/                     (conservation laws, particles)
│   ├── BindPhysics.lean
│   ├── Boundary.lean
│   ├── Conservation.lean
│   ├── ParticleDomain.lean
│   └── ...
├── Optimization.lean            (braid SB, QUBO, Ising)
├── Orchestrate.lean             (unified pipeline, the single entry point)
└── Extraction/
    ├── C FFI signatures
    └── Verilog assertion generators
```

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| `lake build` modules | 50+ (from current 28) |
| Python files deleted | 40+ |
| Rust files reduced to shims | 15+ |
| `#eval` regression tests | 100+ |
| Theorem proofs per physics module | ≥3 |
| Lines of logic outside Lean | <5% of total |

---

## 8. Immediate Next Action

**Phase 1, Step 1:** Port `infra/access_control/core/canonical_state.py` to `Semantics/Canon.lean`.

This is the load-bearing beam of the Python pipeline. Once CanonicalState lives in Lean, the rest of PBACS can be collapsed behind it.

---

**Document ID:** LEAN_PORT_ORCHESTRATION_MAP  
**Branch:** `feature/hybrid-decision-integration`  
**Maintainer:** Human architect (forced port policy)
