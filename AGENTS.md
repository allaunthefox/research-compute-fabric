# AGENTS.md - Research Stack Operating Contract

This file is the first stop for coding agents working in this repository.

## Ground Rules

- Use `/home/allaun/Research Stack` as the active host checkout and git root.
  When the `research-stack` dev container is available, run Lean builds,
  WGSL shader work, and research execution through `podman exec research-stack`
  from the container-local checkout at `/home/researcher/repo/`. Treat the
  host checkout and container checkout as synchronized views of the same repo;
  verify paths before copying artifacts between them.
- The dev container is `research-stack` (podman, `research-stack-otom:latest`).
- **Research artifacts (design docs, experimental Lean files, exploration output)
  must be written to container-local paths under `/home/researcher/research/`**.
  These are not in the git tree and do not pollute the working tree. Use
  `podman cp` to extract research artifacts when they are ready for promotion
  to production.
- Read the nearest nested `AGENTS.md` before editing a subtree.
- Preserve user work. The working tree is often intentionally dirty; do not revert, delete, or stage unrelated files.
- Prefer repo-native tools and receipt generators over ad hoc summaries.
- Treat Lean as the source of truth for formal or hardware-adjacent claims.
- **Load the `lean-proof` skill before any Lean work.** It enforces the proof
  quality contract: no bare sorries, no tautologies, Q16_16 compliance, and
  `#eval` witness requirements. Trigger patterns auto-load it on `.lean`,
  `lake build`, `sorry`, `Q16_16`, `theorem`, `lemma`, etc.
- **No `Float` in compute paths.** `ofFloat` is only permitted at the external
  boundary (JSON parsing, sensor data). All core/main computation uses
  `Q16_16.ofNat`, `Q16_16.ofRatio`, or `Q16_16.ofRawInt`. This applies to
  Lean, Python, and Verilog. The HiGHS boundary is the only exception (it
  requires float inputs, but the result is immediately converted to Q16_16).
- Keep claims bounded: a receipt proves only the gate it actually checks.
- Secrets are runtime-only. Use environment variables such as `OLLAMA_API_KEY`
  or `DEEPSEEK_API_KEY`; never paste, print, or commit literal provider keys.
- For repo-stabilization tasks, finish with a clean `git status --branch --short
  --untracked-files=all` and an empty `git clean -nd` dry run before claiming
  the tree is stable.

## Core Surfaces

- Lean/Semantics: `0-Core-Formalism/lean/Semantics/`
- Infrastructure shims and probes: `4-Infrastructure/shim/`
- Hardware bring-up: `4-Infrastructure/hardware/`
- Documentation and wiki surfaces: `6-Documentation/`
- Virtio-Net DMA Compute Spec: `6-Documentation/docs/specs/virtio_net_compute_fabric_spec.md`
- Citation reference map: `CITATION.cff` (external sources are provenance and
  terminology references unless a Lean theorem or receipt explicitly promotes
  a bounded claim)
- Stack receipts: `shared-data/data/stack_solidification/`
- Promoted review receipts: `shared-data/artifacts/deepseek_review/`
- Canonical Ollama/DeepSeek review emitter:
  `5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py`
- CAD harness: `5-Applications/text-to-cad/`
- Historical scoped staging maps:
  `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
  and `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-10.md`

## Verification Expectations

- For Lean changes, run the narrow target first, then the broader `lake build` when feasible.
- For Python shims, run `python3 -m py_compile` on touched files.
- For JSON receipts, run `python3 -m json.tool` or a repo-native receipt parser.
- For promoted Ollama/DeepSeek review receipts, run
  `python3 5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py --verify-only`
  so `answer_sha256` is checked against the answer file after write.
- For hardware claims, distinguish software witness, bitstream presence, SRAM load, flash persistence, UART beacon, and live hardware receipt.
- Before committing, run `git diff --cached --check` and a staged secret scan
  for touched source/receipt files. The repository credential hook is a final
  gate, not a substitute for local review.
- For root CAD setup changes, JSON-parse `package.json`, `.vscode/settings.json`,
  and `.vscode/tasks.json`, then use the pinned Python/CAD commands documented
  in `5-Applications/text-to-cad/AGENTS.md`.

## Post-Interaction Workflow (mandatory after every agent session)

After every interaction with the user that changes code, Lean modules,
shim scripts, receipts, or architecture decisions, the agent MUST run the
following steps **before claiming the session is complete**:

### 1. Update AGENTS.md files

Update the nearest scoped AGENTS.md for every subtree touched:

| Subtree touched | AGENTS.md to update |
|----------------|-------------------|
| `0-Core-Formalism/lean/Semantics/` | `0-Core-Formalism/lean/Semantics/AGENTS.md` |
| `4-Infrastructure/` | `4-Infrastructure/AGENTS.md` |
| Root or multi-subtree | `AGENTS.md` (this file) |

Minimum required updates per touched subtree:
- **Blessed surface table** — add/remove/update module rows if Compiler roots changed
- **Build baseline** — update job count and commit hash if `lake build` was run
- **Architecture section** — update if data-flow or boundary rules changed
- **Pending proof work** — add new `TODO(lean-port)` stubs; remove resolved ones
- **Quarantine table** — add quarantined files; remove revived ones

### 2. Verify the build

```bash
cd 0-Core-Formalism/lean/Semantics && lake build Compiler
```

If Lean files were touched, also run the full build:

```bash
cd 0-Core-Formalism/lean/Semantics && lake build
```

### 3. Commit

Stage only explicitly touched files (never `git add .`).
Commit message format:

```
<type>(<scope>): <summary>

<body — what changed and why>

Build: <N> jobs, 0 errors (lake build)
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`.
Scope examples: `lean`, `rrc`, `avm-isa`, `infra`, `corpus278`.

### 4. Check tree cleanliness

```bash
git status --branch --short --untracked-files=all
```

Untracked files that are not generated artifacts should either be staged or
noted as intentionally dirty. Do not claim the tree is stable if there are
unexpected modifications.

### 5. Programming choice flow (check before writing any new code)

Before writing or placing any new logic, run through this decision tree in
order. Stop at the first rule that applies.

```
New logic needed?
│
├── Does it make an admissibility, routing, alignment, or gating decision?
│   └── YES → Write it in Lean. No Python equivalent allowed.
│             File: Semantics/RRC/Emit.lean or a new Semantics.* module.
│
├── Does it mint, stamp, or emit a top-level receipt or JSON bundle?
│   └── YES → It belongs in Semantics.AVMIsa.Emit ONLY.
│             AVMIsa.Emit is the sole output boundary. No other module
│             may call leanBuildReceipt and produce a top-level JSON.
│
├── Does it classify rows, run an alignment gate, or compute scores?
│   └── YES → Lean (Semantics.RRC.Emit or a new Semantics.RRC.* module).
│             Python may call it via #eval / lake exe but may not replicate it.
│
├── Does it supply raw input features (equation text, route_hint, domain_type,
│   equation_id hashing, weak_axes count)?
│   └── YES → Python shim is acceptable. The shim must:
│             (a) produce only a List FixtureRow (or equivalent data structure)
│             (b) carry no admissibility logic — every field it sets is "raw"
│             (c) be regenerable from source (document the regeneration command)
│             (d) live in 4-Infrastructure/shim/ with a clear TODO(lean-port) if
│                 any logic in it could eventually move to Lean
│
├── Does it use floating-point arithmetic in a compute path?
│   └── YES → STOP. Use Q16_16.ofNat / Q16_16.ofRatio / Q16_16.ofInt instead.
│             ofFloat is only permitted at the external boundary (JSON parsing,
│             sensor input) and must be immediately bracketed.
│
├── Does it advance promotion status (e.g. set promotion = "promoted")?
│   └── YES → STOP. Promotion is always not_promoted until a Lean gate
│             explicitly passes. Never advance it in shim space or by hand.
│
└── Is it pure I/O (read JSON, write JSONL, call subprocess, format output)?
    └── YES → Python shim is fine. Keep it in 4-Infrastructure/shim/.
              Receipt-writing Python must still route output through
              AVMIsa.Emit (Lean stamps; Python only formats/stores).
```

**Summary rule:** Lean owns all decisions. Python owns all I/O.
If you find yourself writing decision logic in Python, stop and port it to Lean.

### What "every interaction" means

This workflow triggers whenever the user message results in:
- Any file edit (Lean, Python, TOML, JSON, shell, Rust, etc.)
- Any `lake build` run
- Any architectural decision that changes the data-flow or boundary rules
- Any new `TODO(lean-port)` or quarantine boundary

It does NOT trigger for pure read-only exploration, explanation, or
questions that result in no file changes.

## Do Not Sweep

Avoid broad cleanup or staging commands such as:

```bash
git add .
git add 0-Core-Formalism 4-Infrastructure 6-Documentation shared-data
git checkout -- .
git clean -fdx
```

Use explicit file lists from the relevant staging manifest.

`shared-data/` is ignored by default because most of it is generated or
offloaded. Promote only specific, durable receipts with `git add -f -- <path>`,
and keep empty/failed model outputs out of Git unless they are themselves the
evidence under review.

## Git Remote Hygiene

- The active branch may not have an upstream. Inspect with
  `git rev-parse --abbrev-ref --symbolic-full-name @{u}` before assuming push
  state.
- For GitHub sync, prefer the `github` remote and verify the remote head after
  push:

```bash
git fetch github <branch>
git rev-list --left-right --count FETCH_HEAD...HEAD
git push -u github <branch>
git ls-remote --heads github <branch>
```

- Dependabot banners printed by GitHub after push may be stale relative to the
  live alert API. Treat the push result and remote-head hash separately from
  dependency-alert remediation.

## Q16_16 Unification Migration

The codebase has 6 different Q16_16 type definitions causing fragmentation. A migration
is in progress to unify all consumers to the canonical `Semantics.FixedPoint.Q16_16`.

### Migration Status (Completed)
- ✅ `ManifoldStructures.lean` - Migrated (type-only usage)
- ✅ `Errors.lean` - Migrated (function-using, bridge-based approach)
- ✅ `SubstrateProfile.lean` - Migrated
- ✅ `BoundaryDynamics.lean` - Migrated
- ✅ `CausalGeometry.lean` - Migrated
- ✅ `CosmicStructure.lean` - Migrated
- ✅ `CriticalityDynamics.lean` - Migrated
- ✅ `ExoticSpacetime.lean` - Migrated
- ✅ `MagnetoPlasma.lean` - Migrated
- ✅ `ManifoldPotential.lean` - Migrated
- ✅ `MultiBodyField.lean` - Migrated
- ✅ `SpikingDynamics.lean` - Migrated
- ✅ `PhysicsScalarBridge.lean` - Created bridge with full function forwarding

### Migration Approach
For files using PhysicsScalar.Q16_16:

1. **Type-only files** (simple): Replace imports and open statements
   ```lean
   -import Semantics.PhysicsScalar
   +import Semantics.FixedPoint
   
   -open Semantics.PhysicsScalar
   +open Semantics.FixedPoint
   ```

2. **Function-using files** (requires bridge): Use `Semantics.PhysicsScalarBridge`
   ```lean
   import Semantics.PhysicsScalarBridge
   
   -- Replace PhysicsScalar.Q16_16.gt with PhysicsScalarBridge.gt
   -- Replace constants with PhysicsScalarBridge.one, .two, .three, etc.
   ```

### Available Bridge Functions
- `toFixedPoint : PhysicsScalar.Q16_16 → FixedPoint.Q16_16`
- `fromFixedPoint : FixedPoint.Q16_16 → PhysicsScalar.Q16_16`
- `add`, `mul`, `sub` - bridged arithmetic
- `gt`, `le` - bridged comparisons
- `zero`, `one`, `two`, `three`, `four`, `half`, `quarter` - constants

### Migration Guide
See `LEAD_Q16_16_MIGRATION_GUIDE.md` for detailed microsteps.

## Glossary (before reading further)

These terms appear throughout all AGENTS.md files and the codebase:

- **Sidon label** — an address from a set where all pairwise sums are unique.
  Powers of 2 (1,2,4,8,16,32,64,128) are the canonical Sidon set for 8 strands.
  Sidon slack = address budget − max label used (encodes capacity headroom).
- **BraidStorm** — the 8-strand braid topology used by the eigensolid compressor.
  Strands cross pairwise; each crossing merges phase and produces a residual.
- **eigensolid** — the converged, stable state of a braid crossing loop.
  Detected when `crossStep(s) = s`. The DC baseline in the TNT BraidCarrier model.
- **scar** — a FAMM failure record in `ene.scars`. Stores scar_pressure, failure_mode,
  and optional coarsening_agent for remediation path. Scar absence (∅) is a
  positive receipt dimension.
- **Yang-Baxter** — the braid relation `βij βjk βij = βjk βij βjk` that defines
  braid-order invariance. Represented in `BraidedFieldPaths.lean`; operational
  braid-action proofs must state their exact evaluation model.
- **Anti-BraidStorm** — adversarial dual that tests Yang-Baxter invariance and
  receipt aliasing as a validation layer for the compressor.
- **MORE FAMM** — Memory-Optimized Recursive Entropy Fractal Aggregate Memory Model.
  Capability-based memory isolation for the runtime stack.
- **TSM** — Topological S3C Manifold. Thermodynamic safety monitor with
  Builder/Warden/Judge clock domains.
- **GCL** — Genetic Code Language. Self-improving evolutionary program representation.
- **AVM** — Adaptive Virtual Machine. Universal bridge between math languages and
  Python bytecode. Core ISA is live in `Semantics.AVMIsa.*` (Types, Value, Instr,
  State, Step, Run). AVM is the **sole output boundary** for RRC receipts:
  `AVMIsa.Emit` stamps all top-level receipt JSON; `RRC.Emit` and `RRC.Corpus278`
  feed it as classifier and raw-feature supplier respectively.
- **enwik9** — the Hutter Prize 1GB Wikipedia XML corpus, used as the canonical
  end-to-end test vector for the hierarchical compressor.
- **receipt** — a machine-readable attestation record stored in `ene.receipts`.
  Receipt dimensions (C, σ, k, ε_seq, t, ∅_scars) together form the encoding
  of the compressed state. Every gate generates a receipt; a receipt proves only
  the gate it actually checks.

## Compression First Principles

- Zero-gap-timing-spacing-silence IS signal. No byte, no space, no absent row is noise.
  The compressor encodes everything; the decompressor must reconstruct everything,
  including the gaps, because the gaps ARE the compression.
- The receipt IS the compressed state — not metadata around it. Receipt dimensions
  (crossing matrix C, Sidon slack σ, step count k, residual series ε_seq, write
  timing t, scar absence ∅) together form the encoding. Invertibility of this
  receipt is the definition of lossless compression.
- Every compute substrate denies being a CPU: GPU (WGSL/wgpu), ASIC (SHA-256),
  FPGA (Verilog), PCIe/DMA (bus mastering), storage (NVMe/BTRFS), blitter
  (6502 OISC), hydraulic (pipes). All compute identically because Q16_16 integer
  arithmetic is deterministic across all of them. No substrate is privileged.
- The database IS the test field. enwik9 (1GB) and 259 TiddlyWiki tiddlers live
  in the same `ene.packages` table. The compressor does not distinguish between
  them. The schema is the substrate.
- Two distinct Lean theorems are required for every compressor:
  1. `eigensolid_convergence` — the braid crossing loop stabilizes
  2. `receipt_invertible` — given the receipt, the original state is reconstructible
     within bounded error, including all gap/timing/absence dimensions
- Float (`ofFloat`) is forbidden in compute paths. `Q16_16.ofNat` and `Q16_16.ofRatio`
  are the canonical constructors. `ofFloat` is only permitted at the external
  boundary (parsing JSON, reading sensor data) and must be immediately bracketed.

## Legacy Recovery Trigger

The phrase **`RECOVER LEGACY INFORMATION`** is the explicit retrieval trigger
for archived or quarantined concepts. Treat this as a user-controlled cold
archive request, not permission to revive an old branch wholesale.

Accepted trigger forms:

```text
RECOVER LEGACY INFORMATION: <path, commit, concept, or artifact>
Recover Legacy Information: <path, commit, concept, or artifact>
recover from cornfield: <path, commit, concept, or artifact>
```

When this trigger appears:

- Inspect the requested legacy source first with read-only commands such as
  `git show`, `git log`, or targeted file reads.
- Recover only the named file, concept, commit slice, or receipt requested.
- Modernize the recovered material onto the current clean branch before
  committing it.
- Never merge, reset to, or base new work on a legacy/cornfield branch unless
  the user explicitly asks for that exact branch operation.
- Preserve the legacy branch as retrievable archive state.

Current cornfield ref:

```text
backup/distilled-with-vcd-history-2026-05-11
```

## Nested Contracts

- Strict Lean/docs contract: `6-Documentation/docs/AGENTS.md`
- Lean module-local contract: `0-Core-Formalism/lean/Semantics/AGENTS.md`
- Infrastructure contract: `4-Infrastructure/AGENTS.md`
- CAD harness contract: `5-Applications/text-to-cad/AGENTS.md`
- QC flagger contract: `scripts/qc-flag/AGENTS.md`
- Lean expert agent contract: `shared-data/artifacts/lean_expert_agent/AGENTS.md`

## Clean PIST predictions pipeline (no Rust authority)

### Canonical IDs + dedup

Join key is invariant ID: `equation_id := invariant_receipt.object_id` (format `rrc_eq_<hex>`).
The 278 source file contains duplicate object_id groups; predictions artifacts must be
deduped by `equation_id`.

Preserve auditability by attaching provenance:
- `summary.total_source_records = 278`
- `summary.unique_equation_ids = 250`
- each prediction row includes `source_records : Array {equation_record_id, name}` for
  all source rows sharing that invariant.

### Deterministic representative selection

When multiple compiled records share the same `equation_id`, select a representative
deterministically:

```
representative := min(records, key = equation_record.equation_id)  (lexicographic)
```

Never "last wins".

### Prediction artifact (v1, matrix-only)

Generate: `shared-data/rrc_pist_predictions_278_v1.json`

Constraints:
- `schema: "rrc_pist_predictions_278_v1"`
- `claim_boundary: "matrix-only;no-classifier;no-lean-spectral"`
- `proxy_pred: null`, `exact_pred: null` (until a classifier surface is defined)
- include:
  - `global_vocab_hash`
  - `matrix_schema: "token_strand_adjacency_8x8_v1"`
  - `matrix_hash` (sha256 of canonical row-major JSON, no whitespace)
  - `matrix_8x8` (Int counts)

### Generation rules (matrix_schema v1)

1. global vocab = all unique tokens across corpus, sorted
2. `strand(token) = vocab_index % 8`
3. matrix is 8×8 adjacency of token bigrams in original order, projected to strands:
   `M[strand(t_i)][strand(t_{i+1})] += 1`

### Merge path into Lean corpus

```
pist_matrix_builder.py
  → writes rrc_pist_predictions_278_v1.json (dedup by invariant id)
  → build_corpus278.py reads it and merges by equation_id = rrc_eq_<hex>
  → regenerates Semantics/RRC/Corpus278.lean with pistProxyLabel/pistExactLabel
    populated when present
  → emit278.json alignment gate becomes non-missing_prediction only when labels exist.
```

### Required validations (every change)

- `python3 -m py_compile` on touched shim scripts
- `python3 -m json.tool` on generated JSON
- reproducibility check: two consecutive runs must produce identical file SHA256
- `lake build` (full workspace) must stay green

### NOTE on counts

Prediction artifact row count may be 250 while source record count is 278. This is
correct: one prediction per invariant equation id, with provenance for all source
records.

<!-- BEGIN ContextStream -->
### When to Use ContextStream Search:
✅ Project is indexed and fresh
✅ Looking for code by meaning/concept
✅ Need semantic understanding

---
<!-- END ContextStream -->
