# Local Setup Reflow

**Source context:** `/home/allaun/Documents/DeleteMe/ChatGPT-Filling_in_Help.json`  
**Purpose:** turn the working conversation into a Phi-centered local cockpit for the Research Stack.
**Core upgrade:** [PHI_CENTER_REVAMP.md](PHI_CENTER_REVAMP.md)

This is an overlay, not a mass file move. The repo already has broad maps such as
`PROJECT_MAP.md` and `EQUATION_FOREST_INDEX.md`; this file captures the newer
working shape from the chat export and points to the local places that should be
used first. The revamp promotes Phi from a topic cluster to the root organizing
center.

## Operating Shape

The setup should be read as six active layers:

| Layer | Role | Local anchors |
|---|---|---|
| Phi center | Universal field, golden-ratio/phinary indexing, and traversal scheduling | `docs/PHI_CENTER_REVAMP.md`, `docs/papers/EQUATION_00_PHI_UNIVERSAL.md`, `UniversalField.lean`, `PhiShellEncoding.lean`, `PhinaryNumberSystem.lean`, `MATH_MODEL_MAP_phinary.tsv` |
| Foundation trunk | Base-load, compression, routing, and efficiency primitives under Phi | `MATH_MODEL_MAP.tsv`, `MATH_MODELS_UNIVERSAL.json`, `EQUATION_FOREST_INDEX.md`, `docs/semantics/UNIFIED_LOAD_EQUATION_SPEC.md` |
| Shell codec chassis | S3C/DIAT/PIST shell arithmetic and manifold bridge under Phi | `docs/specs/PHI_S3C_PIST_BRIDGE_SPEC.md`, `0-Core-Formalism/lean/Semantics/Semantics/S3C.lean`, `S3CGeometry.lean`, `PIST.lean`, `PISTMachine.lean`, `PistBridge.lean`, `docs/S3C_MANIFOLD_GEOMETRY.md` |
| Phylogenetic graph | GraphML/equation descent, lineage, and tree-of-life interpretation under Phi | `research_graph.graphml`, `docs/papers/EQUATION_PHYLOGENETIC_TREE.md`, `PROJECT_MAP.md` |
| Manifold field | n-space/manifold view of the graph organism under Phi weighting | `docs/specs/GCL_FIELD_EQUATIONS_SPEC.md`, `docs/specs/MS3C_NESTED_REDUCTION_GEAR_SPEC.md`, `0-Core-Formalism/lean/Semantics/Semantics/ManifoldFlow.lean` |
| Ingest/support shell | Text streams, databases, indexes, and search-friendly exports | `data/ingestion/`, `data/ingested/`, `docs/semantics/notation_ingest_bundle.md`, `scripts/reflow/` |

## Current Cockpit

Start here when resuming work:

1. **Phi center first.** Use Phi as the root comparison lens, while keeping
   `Phi_field`, `phi_ratio`, and `Phi_scheduler` distinct.
2. **Base loads second.** Stabilize `Intrinsic_Load_LI`, `Extraneous_Load_LE`,
   `Total_Cognitive_Load`, and their routing/homeostatic successors before
   using downstream geometry.
3. **S3C is the active shell codec.** Treat it as the bridge between arithmetic
   shell decomposition and manifold routing, with the open-shell versus
   closed-shell mass distinction kept explicit.
4. **PIST is the witness/transport chassis.** Use PIST and `PistBridge.lean`
   for typed state transport rather than scalar-only proof sketches.
5. **GraphML is phylogenetic descent.** Read `research_graph.graphml` as an
   organism map: root, trunk, branch, leaf, realization.
6. **Manifold field is the next synthesis layer.** Only move there after the
   base-load and shell-codec anchors are clean enough to keep the field from
   inheriting drift.

## Canonical Work Queues

### Tighten

These are the stability passes implied by the chat:

| Queue | Goal | First files |
|---|---|---|
| Phi center | Promote [BEAUTIFUL_PROVISIONAL - corrected Phi cost/efficiency - requires Lean theorem verification evidence] and phinary indexing to root | `docs/PHI_CENTER_REVAMP.md`, `UniversalField.lean`, `MATH_MODEL_MAP_phinary.tsv` |
| Base load substrate | Freeze primitives and collapse duplicate load meanings | `MATH_MODEL_MAP.tsv`, `MATH_MODELS_UNIVERSAL.json`, `docs/semantics/UNIFIED_LOAD_EQUATION_SPEC.md` |
| Homeostatic control | Connect load to routing/control without drifting names | `0-Core-Formalism/lean/Semantics/Semantics/CognitiveLoad.lean`, `CompressionControl.lean`, `EtaMoE.lean` |
| Geometric throat | Formalize throat, open/closed shell mass, and reduction gear | `docs/specs/PHI_S3C_PIST_BRIDGE_SPEC.md`, `S3C.lean`, `S3CGeometry.lean`, `docs/S3C_MANIFOLD_GEOMETRY.md`, `docs/specs/MS3C_NESTED_REDUCTION_GEAR_SPEC.md` |
| Bridge chassis | Keep PIST/S3C/DIAT transport typed and auditable | `PIST.lean`, `PISTMachine.lean`, `PistBridge.lean`, `HybridTSMPISTTorus.lean` |

### Expand

These are downstream expansion areas:

| Queue | Goal | First files |
|---|---|---|
| Phylogenetic graph descent | Classify nodes by lineage role and descent family | `research_graph.graphml`, `docs/papers/EQUATION_PHYLOGENETIC_TREE.md` |
| Manifold field snapshot | Measure current graph field and identify high-value frontiers | `docs/specs/GCL_FIELD_EQUATIONS_SPEC.md`, `ManifoldFlow.lean`, `GCLFieldEquationsMetaprobe.lean` |
| Proof chassis replacement | Rebuild scalar proof attempts in PIST/DIAT/S3C space | `PISTMachine.lean`, `BracketedCalculus.lean`, `BracketShellCount.lean`, `S3C.lean` |

## Generated Index

Run:

```bash
python3 scripts/reflow/generate_local_setup_reflow.py
```

This writes:

- `data/reflow/local_setup_reflow.tsv`
- `data/reflow/local_setup_reflow.json`
- `data/reflow/phi_center_manifest.json`
- `data/reflow/phi_s3c_pist_bridge_targets.tsv`
- `data/reflow/phi_s3c_pist_bridge_targets.json`

The generated files are deliberately lightweight: they classify existing files
into the cockpit categories above without moving or rewriting the underlying
repo.

## Rule Of Thumb

When a future task feels scattered, route it through this order:

```text
phi center -> base loads -> shell codec -> witness bridge -> graph descent -> manifold field -> support export
```

That order matches the conversation's method: stabilize low-level load and shell
definitions under Phi, then let the graph/manifold machinery inherit a cleaner
substrate.
