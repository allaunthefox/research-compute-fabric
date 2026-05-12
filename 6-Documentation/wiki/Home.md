# Research Stack Wiki

## Entry Points

| Document | Purpose |
|---|---|
| `docs/AGENTS.md` | Strict LLM operating rules — the one file every agent must read first |
| `docs/VOCABULARY_LOCK.md` | Fixed terminology — Lean references, PIST/FAMM/GWL signatures |
| `docs/GLOSSARY.md` | Project-wide glossary — all terms across all domains |
| `wiki/Concept-Archive.md` | Concept archive — canonical, speculative, held, lossy, retired, and abandoned terms |
| `docs/BEGINNERS_MAP.md` | Narrative onboarding — what this stack is and why it exists |
| `wiki/Build-System.md` | Build system — pinned Python (`3.11.15`), uv integration, VSCode tasks, npm scripts |
| `wiki/Text-to-CAD-Environment.md` | Text-to-CAD environment — CAD-specific venv sequencing, `build123d` / `OCP` verification, agent contract |
| `wiki/DeepSeek-Review-Process.md` | AI-assisted mathematical review — receipt schema, two-stage pipeline, prime-gap example |
| `docs/VISION_NORTH_STAR.md` | Long-term vision — where the stack converges |
| `docs/PHI_CENTER_REVAMP.md` | Phi-centered cockpit architecture — cost/efficiency comparison root |
| `docs/BRAIN_AS_MANIFOLD.md` | Biological manifold theory — hyperbolic geometry, intelligence ladder, Physarum |
| `docs/EQUATION_FOREST_INDEX.md` | Equation taxonomy — kernel IDs F01–F12 and equation families |
| `docs/MATH_MODEL_MAP.tsv` | Equation registry — source of truth for all mathematical models |

## Specifications

| Spec | Domain |
|---|---|
| `docs/specs/AVM_CANONICAL_SPEC.md` | Adaptive Virtual Machine — universal math language adapter |
| `docs/specs/PHI_S3C_PIST_BRIDGE_SPEC.md` | Phi–S3C–PIST bridge — witness transport for Phi-centered transforms |
| `docs/specs/GCL_FIELD_EQUATIONS_SPEC.md` | GCL field equations — manifold-weighted field snapshot |
| `docs/specs/MS3C_NESTED_REDUCTION_GEAR_SPEC.md` | Nested reduction gear — S³ shell gear reduction for AngrySphinx |

## Research Domains

| Domain | Location |
|---|---|
| GCL / GCCL (compression language) | `docs/gcl/`, `docs/research/GCCL_THEORY_INTRO.md` |
| MISC / GENSIS (encoding substrates) | `docs/research/MISC_THEORY.md`, `docs/research/MISC_GENETIC_NSPACE.md` |
| Security / AngrySphinx | `docs/research/BURGERS_READINESS_ASSESSMENT.md` |
| FPGA / Hardware | `docs/FPGA_IMPLEMENTATION_REVIEW.md`, `docs/FPGA_WARDEN_NODE_SPEC.md` |
| Semantics / Lean | `docs/semantics/`, `0-Core-Formalism/lean/Semantics/` |
| Safety | `docs/safety/`, `docs/SAFETY_GATED_VERIFICATION_PLAN.md` |
| Neuroscience | `docs/neuroscience/` |
| Physics | `docs/physics/` |
| Provenance / Audit | `docs/provenance/` |

## Roadmaps

| Roadmap | Target |
|---|---|
| `docs/roadmaps/UNIVERSAL_SUBSTRATE_ROADMAP.md` | USTSM — 36 substrates, 7 phases, unified state machine |
| `docs/roadmaps/RESEARCH_STACK_FOREST_MAP_WATERFALL.md` | Forest map waterfall — authority and substrate plumbing |

## Infrastructure

| Component | Location |
|---|---|
| ENE (Endless Node Edges) | `4-Infrastructure/infra/ene_distributed_node.py` |
| AVM ABI surface | `avm_abi.py` |
| AVM Core | `avm_core.py` |
| Topological Storage (Google Drive) | `RcloneIntegration.lean`, `CONCEPTS.md` §Topological Storage |

## Key Concept Docs

| Document | Summary |
|---|---|
| `CONCEPTS.md` | Core concepts — FAMM, OTOM, PIST, ENE, Charged-Mass Braid Sieve |
| `wiki/Concept-Archive.md` | Full concept archive — includes abandoned/held/speculative surfaces |
| `CITATION.cff` | Terminology neutrality map — technical terms vs cultural aliases |
| `PROJECT_MAP.md` | Repository-wide directory structure and module map |
| `MATH_MODEL_MAP.tsv` | Full equation registry indexed by phinary ID |

## Build System & Environments

| Document | Summary |
|---|---|
| `wiki/Build-System.md` | Python `3.11.15` pin via `.python-version`, uv install path, VSCode interpreter, npm script surface |
| `wiki/Text-to-CAD-Environment.md` | CAD-specific sequencing that consumes the canonical setup commands in `wiki/Build-System.md` |
| `GETTING_STARTED.md` | Lean toolchain installation and end-to-end Lean build walkthrough |

## AI-Assisted Review

| Document | Summary |
|---|---|
| `wiki/DeepSeek-Review-Process.md` | Receipt schema (`ollama_deepseek_review_receipt_v1`), two-stage pipeline (`deepseek-v3.2` + `deepseek-v4-flash` continuation), prime-gap entropy-collapse example |
| `shared-data/artifacts/deepseek_review/` | Paired answer + receipt artifacts for each review run |
| `5-Applications/tools-scripts/llm/deepseek_review_adapter.py` | Related Anthropic-compatible DeepSeek adapter; it does not emit the current Ollama-style receipt schema |
