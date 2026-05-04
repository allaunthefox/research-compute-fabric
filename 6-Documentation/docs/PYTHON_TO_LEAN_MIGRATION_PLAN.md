# Python → Lean Migration Plan

**Policy (AGENTS.md §0):** *Lean is the source of truth. Everything else is a shim.*
All Python code must move to Lean unless there is an explicit, documented reason it cannot.

**Generated:** 2026-04-22
**Auditor:** Cascade (via static review + grep pass)

## §0 AGENTS.md Compliance Gates

Every migration must clear all of the following — per-task reviewer checklist:

| Gate | Rule | Source |
|------|------|--------|
| **G1** | No new dependencies (crates / pip / lake) | §1.1 |
| **G2** | No `Float` in new core logic — use `Q16_16` | §1.4 |
| **G3** | No open string matching in decisions — use `Fin n` / inductives | §1.5 |
| **G4** | No `sorry` in committed code | §1.6 |
| **G5** | No helper/utility files — every file is a domain module | §1.8 |
| **G6** | `PascalCase.lean` file, `camelCase` functions, `PascalCase` types | §2 |
| **G7** | Every cost/invariant `def` has an `#eval` **or** theorem witness | §4 |
| **G8** | Logic expressible as a `bind` instance (one of 5 allowed classes) | §4 (bind) |
| **G9** | `lake build` passes with zero warnings | §5.3 |
| **G10** | Deletions require explicit human sign-off | §7.1, §8 |

**Violations are reverted.** If a migration cannot satisfy G1–G9, stop and ask before proceeding (§1.7).

---

## Summary

| Bucket | File Count | Disposition |
|--------|-----------:|-------------|
| **Keep in Python (external-boundary)** | ~40 | Shim layer only |
| **Delete — already has identical Lean counterpart** | 4 | Remove immediately |
| **Migrate to Lean — pure logic** | ~55 (scripts) + ~10 (infra) | Swarm work |
| **Migrate to Lean — mixed, needs split** | ~20 | Swarm with human review |
| **Scratch / sandbox** | 344 (scratch/) | Out of scope, keep or gitignore |

Core Python kept: **~40 files** (HTTP servers, DB drivers, OAuth clients, subprocess wrappers, hardware bridges).

---

## §1 Explicit "Keep in Python" Criteria

A file stays in Python only if **all** of the following are true:

1. **Hard external boundary** — talks to an OS/network/hardware interface Lean cannot reach directly (HTTP server, SQLite, rclone subprocess, OAuth, POSIX signals, GPU runtime, etc.).
2. **No business logic** — logic must already live in Lean; Python is a thin transport/marshaling shim.
3. **Documented reason** — file header names the boundary (e.g. `# BOUNDARY: FastAPI HTTP listener; logic in Semantics.SwarmQueryAPI`).

If the file has logic *and* IO, **split** it: logic → Lean, IO → Python shim calling the Lean binary via `lean --run` or FFI.

---

## §2 Immediate Deletions (identical Lean already exists)

These Python files have **complete, registered** Lean counterparts:

| Python File | Lean Replacement | Lines Removed | Status |
|-------------|------------------|--------------:|--------|
| `infra/omnidirectional_interface.py` | `Semantics.OmnidirectionalInterface` | 752 | Delete |
| `infra/gpu_duty_assignment.py` | `Semantics.GpuDutyAssignment` | 439 | Delete |
| `infra/rclone_integration.py` | `Semantics.RcloneIntegration` | 537 (keep thin IO shim) | Split |
| `infra/domain_model_integration.py` | `Semantics.DomainModelIntegration` | 442 (keep thin IO shim) | Split |
| `tools/swarm_api.py` | `Semantics.SwarmQueryAPI` + FastAPI shim | 335 (keep ~60 line shim) | Split |

**Action (requires human sign-off per §7.1/§8):**
1. Swarm posts a deletion request listing each file + grep proof that nothing in-tree imports it.
2. On approval, files are deleted and replaced with a ≤ 80-line FastAPI/subprocess shim that only marshals JSON into the Lean binary.
3. Shim bodies contain **no** cost functions, invariants, or branching on semantic content (§6.1).

---

## §3 Swarm Work Queue (Prioritized)

Each task is tagged with a lead role and estimated size.

### §3.1 Wave 1 — Pure-Logic Migration (no IO)

These 18 scripts produce JSON reports from hand-authored cost models / designs. They have no IO dependencies beyond `json.dump` and deserve Lean modules with theorems.

| # | Python Source | Target Lean Module | Lead Role |
|--:|---------------|--------------------|-----------|
| 1 | `scripts/swarm_design_nextgen_agents.py` | `Semantics.NextGenAgentDesign` | Type System Architect |
| 2 | `scripts/swarm_genetic_groundup_redesign.py` | (done: `Semantics.GeneticGroundUp`) | — |
| 3 | `scripts/swarm_review_genetic_groundup.py` | `Semantics.SwarmCodeReview` | Formal Verification |
| 4 | `scripts/swarm_gene_bytecode_jit.py` | `Semantics.GeneBytecodeJIT` | Compiler Theory |
| 5 | `scripts/swarm_math_debate.py` | `Semantics.MathDebate` | Logic |
| 6 | `scripts/swarm_competition.py` | `Semantics.SwarmCompetition` | Game Theory |
| 7 | `scripts/swarm_topology_integration.py` | `Semantics.SwarmTopology` | Topology |
| 8 | `scripts/swarm_topology_optimizer.py` | `Semantics.TopologyOptimizer` | Topology |
| 9 | `scripts/swarm_nonstandard_web_interfaces.py` | `Semantics.NonStandardInterfaces` | Interface |
| 10 | `scripts/tsm_swarm_efficiency_optimization.py` | `Semantics.TSMEfficiency` | Perf Analysis |
| 11 | `scripts/virtual_gpu_real_benchmark_fast.py` | `Semantics.VirtualGPUBenchmark` | Perf Analysis (honest toy-cost framing) |
| 12 | `scripts/virtual_gpu_workload_testbench.py` | `Semantics.WorkloadTestbench` | Perf Analysis |
| 13 | `scripts/virtual_gpu_testbench.py` | `Semantics.VirtualGPUTestbench` | Perf Analysis |
| 14 | `scripts/virtual_gpu_topology_loader.py` | `Semantics.VirtualGPUTopology` | Topology |
| 15 | `scripts/combined_resource_layers.py` | `Semantics.ResourceLayers` | Resource |
| 16 | `scripts/swarm_network_capacity.py` | `Semantics.NetworkCapacity` | Resource |
| 17 | `scripts/q_factor.py` | (likely subset of `Semantics.QFactor`) | Verify + delete |
| 18 | `scripts/efficiency_analysis.py` | `Semantics.EfficiencyAnalysis` | Perf |

**Rule for Wave 1:** No theorem may overclaim. All cost/speedup claims must be framed as `toyXxxCostRatio` per the `GeneticGroundUpBenchmark` review.

### §3.2 Wave 2 — `ask_swarm_*` → `SwarmQueryAPI` calls

All `scripts/ask_swarm_*.py` files are query routers that should go through the just-built `Semantics.SwarmQueryAPI`.

| # | Python Source | Migration |
|--:|---------------|-----------|
| 1 | `ask_swarm_tsm.py` | Build `SwarmQueryRequest` for subject `"tsm"` |
| 2 | `ask_swarm_gossip_sync.py` | subject `"gossip"` |
| 3 | `ask_swarm_gpu_translation_surface.py` | subject `"gpu"` → routes to `Subsystem.gpuDuty` |
| 4 | `ask_swarm_kimi_optimization.py` | subject `"kimi"` |
| 5 | `ask_swarm_self_solving_space.py` | subject `"self-solving"` |
| 6 | `ask_swarm_virtual_gpu_limits.py` | subject `"virtual-gpu"` |
| 7 | `ask_swarm_web_interaction_surface.py` | subject `"web"` |
| 8 | `ask_swarm_hotload_kimi.py` | subject `"hotload"` |

**Deliverable:** Replace all 8 scripts with a single `scripts/ask_swarm.py` (≤ 30 lines) that calls the Lean query binary. Lead: Formal Verification.

### §3.3 Wave 3 — Infra split (logic vs IO)

Each of these infra modules has substantial logic mixed with IO. Split them.

| Python File | Logic → Lean | IO → Python shim (≤ 100 lines) |
|-------------|--------------|---------------------------------|
| `infra/ene_api.py` | `Semantics.ENEApi` (security, key derivation, envelope format) | HTTP routes |
| `infra/ene_distributed_node.py` | `Semantics.ENEDistributedNode` (gossip protocol, consensus) | Transport (asyncio) |
| `infra/ene_cloud_credential_manager.py` | `Semantics.ENECredentialEnvelope` (encrypt/decrypt spec) | Disk IO + rclone call |
| `infra/hyperbolic_encoding.py` | `Semantics.HyperbolicEncoding` (math) | None (pure — migrate fully) |
| `infra/moe_ene_cache.py` | `Semantics.MoECache` (eviction policy) | LRU container |
| `infra/swarm_ene_middleware.py` | `Semantics.SwarmENEMiddleware` (routing rules) | HTTP bridge |
| `infra/web_interaction_surface.py` | `Semantics.WebInteractionSurface` (protocol spec) | HTTP client |
| `infra/ascii_art_competition.py` | `Semantics.ASCIIArtCompetition` (scoring) | File IO |
| `infra/ascii_art_store.py` | `Semantics.ASCIIArtStore` (layout/diff) | Disk write |
| `infra/gemma_4_integration.py` | `Semantics.GemmaIntegration` (prompt routing) | LLM HTTP client |

### §3.4 Keep in Python (documented shims only)

| Python File | Reason Kept |
|-------------|------------|
| `infra/lean_shim.py` | **Required** — marshals Python ↔ Lean. Cannot self-replace. |
| `tools/swarm_api.py` → reduce to ~60-line shim | FastAPI listener only |
| `scripts/deploy_ene_full_mesh.py` | SSH/subprocess mesh deploy |
| `scripts/ingest_*.py` (3 files) | File system watch + HTTP fetch |
| `scripts/test_*.py` (9 files) | Pytest integration tests against live components |
| Data-import scripts (`extract_math_from_dumps.py`, `materials_data_ingestion.py`, etc.) | Parse binary/JSON dumps |

---

## §4 Deliverables per Swarm Agent

Each Wave 1 task deliverable must include:

1. **New Lean module** at `0-Core-Formalism/lean/Semantics/Semantics/<Name>.lean`
2. **Registration** in `Semantics.lean` imports
3. **≥ 2 theorems** about module invariants (not restatements of hypotheses)
4. **No `sorry`** in proofs (or explicit TODO with rationale)
5. **Honest naming** — any speedup/cost claim prefixed `toy` if not empirically backed
6. **Deletion** of the source Python script (or reduction to a ≤ 30-line shim)
7. **Update** `docs/PYTHON_TO_LEAN_MIGRATION_PLAN.md` status column

## §5 Review Gate

All migrations pass through `Semantics.SwarmCodeReview` (see Wave 1 task 3) before the Python file is deleted:

- **Builder** (ADD clock): Lean module compiles, theorems type-check
- **Warden** (SUBTRACT clock): No `sorry`, no hypothesis-restatement, claims match content
- **Judge** (PAUSE clock): Assigns accept/reject

---

## §6 Progress Tracker

| Wave | Total | Done | In Progress | Queued |
|-----:|------:|-----:|------------:|-------:|
| Wave 0 — duplicates | 5 | 5 (unified shim: lean_unified_shim.py replaces omnidirectional_interface.py, gpu_duty_assignment.py, rclone_integration.py, domain_model_integration.py, swarm_api.py) | 0 | 0 |
| Wave 1 — pure logic | 18 | 18 (GeneticGroundUp, SwarmCodeReview, NextGenAgentDesign, GeneBytecodeJIT, MathDebate, SwarmCompetition, SwarmTopology, TopologyOptimization, NonStandardInterfaces, TSMEfficiency, VirtualGPUBenchmark, WorkloadTestbench, VirtualGPUTestbench, VirtualGPUTopology, ResourceLayers, NetworkCapacity, QFactor (already exists as Lean shim), EfficiencyAnalysis) | 0 | 0 |
| Wave 2 — ask_swarm_* | 8 | 8 (unified_swarm_query.py consolidates 8 ask_swarm_*.py scripts) | 0 | 0 |
| Wave 3 — infra split | 10 | 10 (ENEApi.lean, MoECache.lean, ASCIIArtCompetition.lean, ASCIIArtStore.lean, SwarmENEMiddleware.lean, HyperbolicEncoding.lean, WebInteractionSurface.lean, GemmaIntegration.lean, ENECredentialEnvelope.lean, ENEDistributedNode.lean) | 0 | 0 |
| **Total migrations** | **41** | **41** | **0** | **0** |

Scratch files under `scratch/` (344 py) are excluded; they are not production code.
