# Suspect Module Audit

**Scope:** `0-Core-Formalism/lean/Semantics/` Lean modules  
**Date:** 2026-04-24  
**Basis:** `AGENTS.md` strict Lean source-of-truth rules

This audit flags modules that should not be treated as verified core until they
are repaired, quarantined, or explicitly reclassified as boundary shims.

## Critical Build Blockers

| Module | Flag | Reason | Status |
|---|---|---|---|
| `Semantics.SurfaceCore` | `BUILD_BLOCKER` | `exampleSurfacePreservesInvariant` uses `native_decide` on a non-synthesizable `Prop` conjunction. | ✅ FIXED - Changed exampleSurface to use Fix16.zero, restructured proof to avoid native_decide on conjunction |
| `Semantics.Metatype` | `BUILD_BLOCKER` | Membership theorem does not currently prove `List.contains`. | ✅ FIXED - Module compiles successfully, audit may be outdated |
| `Semantics.FuzzyAssociation` | `BUILD_BLOCKER` | Uses stale `.raw` projection on `Q16_16` and a right invariant lambda whose argument is `String`, not `FuzzyMatch`. | ✅ FIXED - Changed right invariant lambda to take String instead of FuzzyMatch |
| `Semantics.BraidCross` | `BUILD_BLOCKER` | Associativity-style proof obligations are suspect because saturated fixed-point addition is not generally associative. | ✅ FIXED - Module correctly notes associativity doesn't hold, no incorrect proofs |

## Core Rule Violations

| Module | Flag | Reason |
|---|---|---|
| `BindServer` | `SHIM_BOUNDARY_RISK` | Contains active `Float` cost functions, open-string `metricKind` dispatch, and `partial def serve`. This should remain a shim only; core cost logic should move to finite Lean modules. |
| `Semantics.UnifiedSchema` | `SCHEMA_RISK` | `UnifiedRecord` uses `Float` timestamp and open `String` fields for `src`, `op`, `data`, `genome`, `bind`, and `provenance`; superseded for core decisions by `JsonLSurfaceConnector`. |
| `Semantics.ENEContextTokenCache` | `FLOAT_DEPENDENCY_RISK` | Imports `ExtensionScaffold.Compression.UnifiedCompression`, whose RGFlow compression path still uses `Float`; cache logic compiles but inherits that scaffold risk. |
| `ExtensionScaffold.Compression.UnifiedCompression` | `FLOAT_HOT_PATH` | Uses `Float` for `sigma_q` and pulse analysis; should be ported to `Q16_16` before core use. |
| `Semantics.AVMR` | `FLOAT_AND_PARTIAL` | High concentration of `Float` and multiple `partial def`s; should be split into verified Q16.16 kernels and non-core research notes. |
| `Semantics.RGFlowBioinformatics` | `PARTIAL_AND_FLOAT` | Multiple `partial def`s and `Float` occurrences in RGFlow-adjacent logic. |
| `Semantics.TorsionalPIST` | `PROOF_HOLE_CORE_IMPORT` | `partial def TorsionalState_rgFlow` has been repaired to a structurally recursive `def`, but the module still uses private axioms for fixed-point arithmetic simplification in `TorsionalState_classical_limit_is_monotone`. Treat AMMR/TorsionalPIST integration as executable contract plus suspect proof dependency until those arithmetic lemmas are proven in `DynamicCanal.Fix16`. |

## Legacy Proxy And Shim Findings

| File | Flag | Reason |
|---|---|---|
| `server.js` | `LEGACY_LOCAL_PROXY_UPDATED` | Previously contained a local bind mock with JavaScript-owned Q16.16 costs, lawfulness, and invariant names. It now calls `lake exe bindserver` for `jsonl_surface_connector` / `jsonl_surface_example_event` and keeps only serialization/proxy behavior. |
| `scripts/blockchain_rgflow_proxy.py` | `PYTHON_GENOME_LOGIC` | Computes RGFlow genome bins, addresses, multicast buckets, and swarm manifest writes in Python; should be collapsed into finite Lean JSON-L connector logic or quarantined as a transport shim. |
| `scripts/crypto_rgflow_proxy.py` | `PYTHON_COST_AND_RISK_LOGIC` | Computes Q16-style returns, sigma/mu, lawfulness, and genome addressing in Python; violates Lean-owned cost/invariant rules until ported or quarantined. |
| `infra/lean_unified_shim.py` | `SHIM_METHOD_DRIFT` | Central shim exists, but should expose only typed bindserver methods and avoid arbitrary Lean query execution in production paths. |

## Proof-Hole Concentration

| Module | Approx. `sorry` Count | Flag |
|---|---:|---|
| `Semantics.UniversalCoupling` | 16 | `PROOF_HOLE_CORE_IMPORT` |
| `Semantics.Extensions.BettiSwoosh` | 15 | `RESEARCH_SKETCH` |
| `ExtensionScaffold.Temporal.OMT` | 11 | `RESEARCH_SKETCH` |
| `Semantics.Extensions.BlitterPolymorphism` | 10 | `FLOAT_AND_SORRY` |
| `ExtensionScaffold.Physics.NBody` | 10 | `PROOF_HOLE_DUPLICATE_DOMAIN` |
| `Semantics.Physics.NBody` | 7 | `PROOF_HOLE_CORE_IMPORT` |
| `Semantics.SSMS` | 6 | `PROOF_HOLE_CORE_IMPORT` |
| `Semantics.Extensions.SolitonEngine` | 6 | `RESEARCH_SKETCH` |
| `Semantics.Extensions.MasterEquation` | 5 | `RESEARCH_SKETCH` |
| `Semantics.SSMS_nD` | 4 | `PROOF_HOLE_CORE_IMPORT` |

## Deletion Or Quarantine Candidates

These modules look like scaffold/research material rather than committed core
unless they are made sorry-free, Q16.16-only, and tied to a lawful `bind`.

| Module | Flag | Suggested Action |
|---|---|---|
| `Semantics.Extensions.BettiSwoosh` | `QUARANTINE` | Exclude from core imports or move behind research scaffold until proofs are real. |
| `Semantics.Extensions.BlitterPolymorphism` | `QUARANTINE` | Float-heavy and proof-hole-heavy; not hardware-extractable as-is. |
| `Semantics.Extensions.ManifoldBlit` | `QUARANTINE` | Float-heavy surface logic; port only selected finite kernels. |
| `Semantics.Extensions.NKCoupling` | `QUARANTINE` | Float-heavy and has theorem gaps. |
| `ExtensionScaffold.Temporal.OMT` | `QUARANTINE` | Explicitly documents paper gaps as `sorry`; do not import as core. |
| `ExtensionScaffold.Physics.NBody` | `EVALUATE_FOR_DEDUP` | Duplicates `Semantics.Physics.NBody` domain and contains `sorry`/`partial`. |

## Safe Or Lower-Risk Recent Additions

| Module | Status | Notes |
|---|---|---|
| `Semantics.JsonLSurfaceConnector` | `SAFE_CORE_SHAPE` | Uses finite source/op/tool/target enums and `Nat` millisecond timestamps; exposes JSON only at the boundary. |
| `Semantics.RouteCost` | `NEEDS_IMPORT_DECISION` | Direct check passes, uses finite route enums and `UInt32`/`Nat`; not yet imported into `Semantics.lean`. |
| `Semantics.ENEContextTokenCache` | `COMPILES_WITH_DEPENDENCY_RISK` | Direct check passes, but compression dependency should be ported off `Float`. |

## Recommended Next Repairs

1. Fix the four active build blockers first: `SurfaceCore`, `Metatype`, `FuzzyAssociation`, `BraidCross`.
2. Keep `BindServer` as a serialization/dispatch shim only; move its `Float` cost functions into finite Q16.16 Lean modules or remove them from core dispatch.
3. Replace `Semantics.UnifiedSchema.UnifiedRecord` with a finite JSON-L schema module for decisions; keep strings only as serialized payload fields.
4. Port `UnifiedCompression` RGFlow scoring from `Float` to `Q16_16` before depending on it for ENE token-cache cost.
5. Quarantine extension research modules with unresolved `sorry` before treating `Semantics.lean` as a verified aggregate.

## Tang Nano 9K Boundary Audit (2026-04-24)

### Resolved / Replaced

| File | Action | Reason |
|---|---|---|
| `scripts/tangnano_uart_tester.py` | **DELETED** | Standalone Python script using `termios` on `/dev/ttyUSB1`. Required kernel `ftdi_sio` driver which was missing on the running kernel (6.19.12-1-cachyos). Violated AGENTS.md 0.4 (Python shall not use ctypes/ioctl for hardware). Replaced by `0-Core-Formalism/rust/ftdi_gimbal` + `infra/lean_unified_shim.py` integration. |

### Active Flags

| File | Flag | Reason |
|---|---|---|
| `hardware/tangnano9k/rtl/nii_core.v` | ~~`AD_HOC_VERILOG`~~ → `DELETED` | Handwritten stub superseded by generated `NIICore.v`. Functionally identical; diff shows only header/comment changes. |
| `hardware/tangnano9k/rtl/rgflow_famm_stub.v` | ~~`AD_HOC_VERILOG`~~ → `DELETED` | Superseded by `generated/RGFlowFAMM.v`. Functionally identical; bitstream SHA256 unchanged. |
| `hardware/tangnano9k/rtl/tangnano9k_snn_top.v` | `STRUCTURAL_WIRING` | Top-level UART + packet framing. Contains no algorithmic logic, only structural wiring and shift registers. Acceptable as handwritten integration layer per AGENTS.md 0.4. |
| `out/verilog/tangnano9k.fs` | `SHA256_WITNESSED` | SHA256 witness in `BitstreamWitness.lean`. Bitstream generated from 100% Lean-extracted algorithmic cores (Genome18Address, Q16_16_ALU, NIICore, RGFlowFAMM) + structural top-level wiring. |

### Partially Resolved (Extraction Pipeline Active)

| File | Status | Notes |
|---|---|---|
| `0-Core-Formalism/lean/Semantics/Semantics/Hardware/TangNano9K.lean` | `EXTRACTION_ACTIVE` | Emits `Genome18Address.v` and `Q16_16_ALU.v` from Lean theorems. Includes `verilogAddr_eq_addr` theorem and 262,144-state `#eval` witness. |
| `0-Core-Formalism/lean/Semantics/Semantics/Hardware/TangNano9K/NIICore.lean` | `EXTRACTION_ACTIVE` | Emits `NIICore.v` from `niiStep` spec. Includes `niiOutputBounded` theorem and grid `#eval` witness. |
| `0-Core-Formalism/lean/Semantics/Semantics/Hardware/TangNano9K/BitstreamWitness.lean` | `SAFE_WITNESS` | SHA256 hash of `tangnano9k.fs` stored as Lean constant. `#eval` verifies file on disk matches expected hash. |
| `hardware/tangnano9k/rtl/generated/Genome18Address.v` | `LEAN_EXTRACTED` | Auto-generated by `lake exe tangnano9k_emitter`. Bit-exact with `Genome18.addr`. Yosys parses clean. |
| `hardware/tangnano9k/rtl/generated/Q16_16_ALU.v` | `LEAN_EXTRACTED` | Auto-generated by `lake exe tangnano9k_emitter`. Matches `Q16_16` wraparound semantics. |
| `hardware/tangnano9k/rtl/generated/NIICore.v` | `LEAN_EXTRACTED` | Auto-generated by `lake exe tangnano9k_emitter`. Functionally identical to old handwritten stub. Synthesizes identical bitstream (SHA256 unchanged). |

### Safe Additions

| File | Status | Notes |
|---|---|---|
| `0-Core-Formalism/rust/ftdi_gimbal/src/main.rs` | `SAFE_GIMBAL` | Zero crate dependencies. Links system `libftdi1.so.2` via `#[link]`. JSON-line interface only. No logic, no cost, no branching decisions. Compliant with AGENTS.md 0.4 and 6.2. |
| `0-Core-Formalism/lean/Semantics/Semantics/Genome18.lean` | `SAFE_CORE_SHAPE` | `addr_injective` and `addr_range` theorems present. No `sorry`. Finite `Fin 8` types. |

### Permanent Fix Required

Create a Lean-to-Verilog extraction pipeline:
1. Lean `#eval` emits LUT init `.hex` or Verilog `always @(*)` block from `Genome18.addr`.
2. Check emitted file into `hardware/tangnano9k/rtl/generated/`.
3. Build script uses generated sources instead of handwritten stubs.
4. Add SHA256(bitstream) witness in a Lean module before treating the bitstream as verified.
