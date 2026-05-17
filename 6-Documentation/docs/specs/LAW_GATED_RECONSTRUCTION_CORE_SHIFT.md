# Law-Gated Reconstruction Core Shift

Status: Draft v0.1
Date: 2026-05-09
Scope: roadmap shift from route-prior accumulation to decoder-facing, law-gated reconstruction-core promotion
Claim state: architectural migration plan; not a compression benchmark, proof result, biological model, renderer-correctness result, or Hutter Prize claim

Math consistency review:

```text
6-Documentation/docs/specs/RECONSTRUCTION_CORE_MATH_REVIEW_2026_05_09.md
```

## 1. Shift

The stack now has enough local receipt surface to make the reconstruction core
the organizing axis.

Old center of gravity:

```text
external source -> prior -> route idea -> possible future fixture
```

New center of gravity:

```text
source or proposal
-> lawful reconstruction kernel
-> declared parameters/protocol
-> residual repair
-> deterministic replay
-> byte-exact receipt
-> HOLD / ADMIT / QUARANTINE
```

Canonical compression target:

```text
Find the lowest-cost reconstruction basis whose residual is cheap enough to
repair byte-exactly.
```

The compressed object is not a readable program, not a glyph stream, and not a
semantic summary. It is a decoder-facing reconstruction core.

## 2. Canonical Object

The core object is:

```text
S -> (K, Theta, R, Pi, Receipts) -> S_hat
```

with the hard gate:

```text
Repair(Replay(K, Theta, Pi), R) == S
```

and:

```text
epsilon_byte = 0
```

Byte law:

```text
|D| + |K| + |Theta| + |Pi| + |R| + |Receipts| < |S|
```

If exact replay passes but byte law fails, the result may remain useful as a
diagnostic fixture, but it is not a compression admission.

Auxiliary route scores such as motif gain, binding-energy analogues, replay
curvature, cognitive burden, entropy, and mutation-budget pressure are
dimensionless or normalized diagnostics unless a receipt explicitly declares a
unit conversion. They may rank candidate kernels, but they do not replace the
counted byte law above.

## 3. Receipt Spine

The current shift rests on these local receipt surfaces:

| Surface | Receipt | Role |
|---|---|---|
| mass equation distill | `3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified_receipt.json` | equation coverage/routing prior |
| RRC projection | `3-Mathematical-Models/equations_parquet_tagged/mass_equations_rrc_projection_receipt.json` | route atlas / negative-control surface |
| external route registry | `shared-data/data/nspace_bulk_routes/nspace_bulk_dataset_route_receipt.json` | HOLD-first source registry |
| replay queue | `shared-data/data/replay_fixture_queue/replay_fixture_queue_receipt.json` | fixture execution order |
| symbolic law replay | `shared-data/data/symbolic_law_replay/symbolic_law_replay_receipt.json` | formula reconstruction micro-fixtures |
| PDE tiny replay | `shared-data/data/pde_tiny_replay/pde_tiny_replay_receipt.json` | deterministic field replay micro-fixtures |
| The Well schema probe | `shared-data/data/the_well_tiny_probe/the_well_tiny_schema_probe_receipt.json` | metadata-only field schema fixture |
| weather systems math prior | `shared-data/data/weather_systems_math_prior/weather_systems_math_prior_receipt.json` | conservation/assimilation/stability residual-routing prior |
| MeshGraphNets topology probe | `shared-data/data/meshgraphnets_tiny_probe/meshgraphnets_tiny_topology_probe_receipt.json` | irregular topology fixture |
| quantum cogload transfold | `shared-data/data/quantum_cogload_transfold/quantum_cogload_transfold_receipt.json` | Pauli/transfold cognitive-load prior |
| quantum basis objective | `shared-data/data/quantum_basis_compression_objective/quantum_basis_compression_objective_receipt.json` | generator/residual admission objective |
| enwiki8 wiki-logogram probe | `shared-data/data/enwiki8_wiki_logogram_probe/enwiki8_wiki_logogram_probe_receipt.json` | bounded MediaWiki/XML grammar replay fixture |
| enwiki9 logogram targeter | `shared-data/data/enwiki9_logogram_targeter/enwiki9_logogram_targeter_receipt.json` | imported slice-class targeter and local sample replay |
| enwiki9 XML dictionary probe | `shared-data/data/enwiki9_logogram_xml_dict_probe/enwiki9_logogram_xml_dict_probe_receipt.json` | fixed-tag dictionary promotion / core-delta check |
| whitespace-zero grammar probe | `shared-data/data/stack_solidification/whitespace_zero_grammar_probe.json` | canonical spaces are derived from symbol count/order; non-canonical whitespace remains residual/HOLD |
| enwiki9 receipt aggregation probe | `shared-data/data/enwiki9_logogram_receipt_aggregation_probe/enwiki9_logogram_receipt_aggregation_probe_receipt.json` | slice-level replay receipt / packet-delta check |
| enwiki9 dictionary amortization probe | `shared-data/data/enwiki9_logogram_dictionary_amortization_probe/enwiki9_logogram_dictionary_amortization_probe_receipt.json` | PASS/ADD/PAUSE/SUBTRACT global-delta fixture check |
| language surface ambiguity negative control | `shared-data/data/language_surface_ambiguity_negative_control/language_surface_ambiguity_negative_control_receipt.json` | analogy leakage and same-surface role-collision guardrail |
| reconstruction core ladder memory | `shared-data/data/stack_memory_promotions/reconstruction_core_ladder_memory_receipt.json` | project-memory pointer for current ladder, guardrails, and next action |
| DNA codec filter | `shared-data/data/dna_codec_filter/dna_codec_filter_receipt.json` | analogy-bound motif/binding/repair filter |
| logogram-DNA codec | `shared-data/data/logogram_dna_codec/logogram_dna_codec_receipt.json` | Omindirection/GCCL symbolic-genome gate |
| Lean proof replay | `shared-data/data/lean_proof_replay/lean_proof_replay_receipt.json` | local Lean proof-boundary fixture |

These receipts do not prove global compression. They prove that the stack now
has enough local gates to stop promoting unreceipted priors.

## 4. Promotion Ladder

Every new route moves through the same ladder:

```text
SEED
-> ROUTE_PRIOR
-> TINY_FIXTURE
-> REPLAY_VALID
-> RESIDUAL_DECLARED
-> BYTE_LAW_CHECKED
-> CONTROL_FILTERED
-> ADMIT or HOLD or QUARANTINE
```

Meaning:

| State | Meaning |
|---|---|
| `SEED` | idea, source, equation, corpus, glyph, kernel, or external pointer |
| `ROUTE_PRIOR` | metadata and claim boundary recorded |
| `TINY_FIXTURE` | no-download or tiny local replay fixture exists |
| `REPLAY_VALID` | deterministic replay observed |
| `RESIDUAL_DECLARED` | repair stream or loss policy exists |
| `BYTE_LAW_CHECKED` | counted kernel/parameter/protocol/residual/receipt bytes compared to raw |
| `CONTROL_FILTERED` | LoC/NES, FYC, COUCH, Tree Fiddy, and BHOCS gates recorded |
| `ADMIT` | exact replay, positive byte law, and controls pass |
| `HOLD` | useful but incomplete, under-receipted, too costly, or diagnostic only |
| `QUARANTINE` | destructive tear, semantic mutation, receipt mismatch, or invalid adapter |

No source, symbol, proof, or codec packet skips the ladder.

Fixture receipts may use `ADMIT_FIXTURE` for a tiny local example that passes
its local replay and byte checks. That status is not global `ADMIT`. A receipt
whose top-level `decision` is `HOLD` remains non-promoted even if one fixture in
the receipt is marked `ADMIT_FIXTURE`.

## 5. Law Gates

The reconstruction core is admitted only through law gates, not through
readability or elegance.

Core gate:

```text
replay_valid
and residual_declared
and byte_gain > 0
and receipt_verified
```

GCCL gate:

```text
stateSpaceDeclared
and transformDeclared
and invariantsDeclared
and residualDeclared
and costDeclared
and projectionDeclared
and quarantineDeclared
and scaleDeclared
```

Omindirection gate:

```text
payload != glyph != rendered layout
and explicit direction
and chirality/phase compatible
and placement valid
and residual policy declared
and receipt complete
and adapter preserves canonical atom
```

Proof gate:

```text
external proof corpus may route obligations
but only local Lean replay promotes proof state
```

## 6. Routing Surfaces After The Shift

External corpora now serve one of four roles:

| Role | Examples | Promotion boundary |
|---|---|---|
| markup grammar replay | enwiki8 / MediaWiki XML | byte-exact decode + baselines + amortized receipt accounting |
| symbolic-law replay | SRBench, ParFam, DLMF, Feynman | exact formula replay + residual/byte law |
| field-dynamics replay | PDEBench, RealPDEBench, The Well, ERA5/NWP/FV3 | split/metric/boundary/storage receipts + replay |
| topology replay | MeshGraphNets, goxel-like mesh lanes | canonical edge/face/boundary/topology receipts |
| proof routing | LeanDojo, mathlib | local Lean theorem or executable witness |

Reasoning corpora such as NuminaMath remain proposal curricula. They do not
promote facts without an independent verifier.

## 7. Immediate Work Queue

The next work is not "add more priors." It is to convert existing priors into
fixture-bearing lanes.

1. Build a single reconstruction-core admission index from all receipt JSON.
2. Add a RealPDEBench no-download calibration card with license and split gates.
3. Attach the logogram-DNA gate to the existing math logogram substitution
   audit so `ACCEPT`, `HOLD`, and `QUARANTINE` share one decision vocabulary.
4. Mirror the Python admission gates in Lean where they are stable enough:
   replay validity, byte law, residual declaration, and atom gate predicates.
5. Add a tiny corpus-slice runner that reports raw bytes, kernel bytes,
   residual bytes, receipt bytes, replay time, and exact-repair status.
6. Promote nothing from `HOLD` until the receipt index can show the exact
   replay path and byte accounting.

## 8. Final Boundary

This shift does not make the stack a compression winner.

It makes the stack harder to fool:

```text
pretty transform != compression
glyph != payload
model proposal != accepted atom
external corpus != benchmark result
semantic elegance != byte law
local fixture != global claim
```

The new standard is:

```text
lawful reconstruction + declared repair + byte-exact receipt
```

Everything else stays `HOLD`.
