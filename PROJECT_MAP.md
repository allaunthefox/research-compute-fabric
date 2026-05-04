
--- FILE CONTENT ---
# PROJECT_MAP.md — Sorted by ENE Schema

**Purpose:** External memory of project structure. You don't need to hold any of this in your head — jump to the section you need.
**Sorting framework:** [6-Documentation/docs/ENE_SCHEMA.md](6-Documentation/docs/ENE_SCHEMA.md) — 14-axis hyperbolic concept space + 5 settlement states.
**Generated:** 2026-04-25. Regeneration recipe at the end of this file.

---

## How to use this map

If you want to... | Jump to
---|---
resume the Phi-centered cockpit | [6-Documentation/docs/PHI_CENTER_REVAMP.md](6-Documentation/docs/PHI_CENTER_REVAMP.md)
publish next | [§ Publication queue](#publication-queue)
find a paper or Lean module by *what it's about* | [§ 14-axis sort](#14-axis-sort)
see what's done vs. what's drafty | [§ Settlement state ladder](#settlement-state-ladder)
find a "family" of related work | [§ Concept clusters](#concept-clusters)
read a single thing first by purpose | [§ Entry points](#entry-points)
see what other maps exist | [§ Alternative maps](#alternative-maps)
understand repository structure | [§ Repository structure](#repository-structure)
regenerate this map | [§ Regeneration recipe](#regeneration-recipe)

---

## Three grounding axioms

These come from [6-Documentation/docs/AGENTS.md](6-Documentation/docs/AGENTS.md) and [6-Documentation/docs/VISION_NORTH_STAR.md](6-Documentation/docs/VISION_NORTH_STAR.md). Everything else descends from them.

1. **Lean is the source of truth.** Python/Rust/Verilog are extraction targets. Logic in shims is a bug.
2. **The publishing pipeline is `Substrate (ENE) ↔ Surface (Notion) ↔ Intent (Linear) ⟹ Metatype`.** ENE holds truth, Notion is the UI, Linear tracks intent. The integration *is* the self-typing loop.
3. **Settlement state is the lifecycle.** Every artifact lives in one of: `SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED`. Movement is the work.

---

## Repository structure

**Root level** contains only core navigation and configuration:
- **Core docs:** `CONCEPTS.md`, `PROJECT_MAP.md`, `TODO_MAP.md` (navigation maps)
- **Configuration:** `.gitignore`, `.env.example` (config files in `workspace-config/`)
- **Main directories:** (see below)

**Directory structure:**
- `0-Core-Formalism/` — Lean, core source, bind, Triumvirate
  - `lean/Semantics/` — Lean formalization (canonical truth, 49+ modules)
  - `core/` — Core source code (Rust, Lean, Python extraction targets)
  - `otom/` — One-Truth-Only-Model (Consolidated 2026-05-03)
  - `rust/` — Rust implementations
- `1-Distributed-Systems/` — ENE mesh, gossip, waveprobe
  - `ene/` — ENE nodes and mesh logic
  - `waveprobe/` — Signal probing tools
- `2-Search-Space/` — PIST, SVQF, FAMM
  - `manifold/` — Manifold search and optimization
  - `search/` — Search algorithms
- `3-Mathematical-Models/` — Equation registry, math database
  - `database/` — Mathlib and model databases
- `4-Infrastructure/` — Shims, GPU, cloud, hardware, drivers
  - `infra/` — Python shims and integration
    - `servo-fetch/` — (Moved to Forked/ 2026-05-03)
  - `hardware/` — Hardware designs (Verilog, FPGA)
  - `drivers/` — Hardware drivers
  - `gpu/` — GPU optimization and shaders
    - `wasmgpu/` — Wasm-based GPU shims (Consolidated 2026-05-03)
  - `config/` — System configuration
- `5-Applications/` — Scripts, tests, pipelines, audit
  - `scripts/` — Executable scripts (ingestion, processing)
  - `tests/` — Test files and testbenches
  - `out/` — Output files and reports
  - `audit/` — Audit results
  - `text-to-cad/` — (Moved to Forked/ 2026-05-03)
- `6-Documentation/` — Docs, papers, semantics, wiki, archive
  - `docs/` — Papers, specs, guides
    - `specs/RESEARCH_STACK_NUVMAP_ADDRESS_SPACE.md` — Canonical Address Mapping (New)
    - `recovered/` — Recovered research artifacts from DeleteMe (2026-05-04)
  - `papers/` — Scientific literature and PDFs
  - `archive/` — Historical materials / Risk Management
    - `PRIOR_ART/moim_v5_recovery/` — MOIM v5.0 recovered source and hardware (High Value)
    - `revenant/` — Archived (Liability reduction 2026-05-03)
    - `webmoji/` — Archived (Liability reduction 2026-05-03)
  - `finance/` — Financial records and ledgers
- `shared-data/` — Databases, artifacts, data
  - `data/` — Raw and processed data
    - `ingested/llm_research/` — ChatGPT/Kimi/Claude research logs
  - `artifacts/` — Generated artifacts
- `workspace-config/` — Environment and IDE settings
- `scratch/` — Experimental/temporary code

**Ignored directories** (in `.gitignore`):
- Virtual environments: `hutter_venv/`, `venv_proxy/`, `venv_wgpu/`, `*.venv/`, `venv/`
- Large tools: `ComfyUI/`, `locally-uncensored_temp/`, `searxng/`
- Build artifacts: `node_modules/`, `tools/bin/`, `5-Applications/build/`, `**/target/`
- Local projects: `Obdisidan connector/`, `String-Star-Manifold/`, `CompressionApproachViaTopology/`

---
... rest of the file ...
