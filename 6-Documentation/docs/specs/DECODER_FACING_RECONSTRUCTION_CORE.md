# Decoder-Facing Reconstruction Core

Status: Draft v0.1
Date: 2026-05-08
Scope: compression-core interface boundary for logogram, OMCF, PIST, residual, and verifier pipelines
Claim state: terminology and admission contract; not a benchmark result, decompressor implementation, or Hutter Prize claim

## 1. Purpose

This document defines the interface boundary for the compressed core.

Current architecture shift:

```text
6-Documentation/docs/specs/LAW_GATED_RECONSTRUCTION_CORE_SHIFT.md
```

Math consistency review:

```text
6-Documentation/docs/specs/RECONSTRUCTION_CORE_MATH_REVIEW_2026_05_09.md
```

Project memory promotion:

```text
shared-data/data/stack_memory_promotions/reconstruction_core_ladder_memory_receipt.json
```

That shift makes this document the inspection boundary for all compression
routes: route priors, glyphs, physics corpora, proof corpora, DNA-style filters,
and quantum/transfold kernels remain `HOLD` until they provide deterministic
replay, declared residual repair, byte accounting, receipts, and control-filter
evidence.

The compressed representation is not assembly language, source code, bytecode
in the ordinary human-inspectable sense, or a prose notation for the payload.
It is a decoder-facing reconstruction core.

Canonical phrase:

```text
This is not assembly. It is a lawful reconstruction core.
```

Expanded:

```text
The compressed core should not be treated as assembly language, source code,
or a human-readable intermediate representation. It is a decoder-facing
reconstruction core: its validity is established by deterministic replay,
residual repair, receipts, and byte-exact output rather than by direct
readability.

This is not anti-inspection. It is a consequence of the compression process.
Inspection moves to the lawful interfaces: codec specification, replay rules,
receipts, residuals, hashes, benchmarks, and reconstructed bytes.
```

## 2. Interface Layers

The system separates human-facing handles from decoder-facing reconstruction
material.

| Layer | Purpose |
|---|---|
| human surface | logograms, prose labels, diagrams, control names, documentation |
| proposal surface | candidate laws, seeds, type witnesses, Mass Number basins |
| reconstruction core | compressed replay material, not human-readable by contract |
| receipt surface | hashes, O-AMVR/O-AVMR receipts, replay checks, residual policy |
| output surface | byte-exact reconstructed payload |

The core is inspectable only through the declared interfaces. A human may inspect
the core bytes, but direct readability is not a validity criterion.

## 3. Validity Rule

A reconstruction core is valid only when:

```text
decode(core, residual, rules) == original_bytes
receipt verifies deterministic replay
residual policy is declared
all counted bytes satisfy the admission law
```

The core is invalid when:

```text
direct inspection looks plausible
but replay fails
```

or:

```text
semantic grouping looks elegant
but residual cost erases gain
```

## 4. Relationship To OMCF / PIST

The reconstruction core may contain OMCF and PIST material:

```text
OMCF = structure + semantic mass + deterministic expansion + braid receipt
PIST = lawful surface transform over the carrier
```

But those internal packets are still judged by replay:

```text
project -> mass -> braid -> PIST -> receipt -> residual -> byte-exact output
```

No internal notation is promoted because it is readable, elegant, or mnemonic.
Promotion requires deterministic reconstruction and positive byte law.

## 5. Proposal / Verifier Split

Stochastic systems may propose reconstruction laws, but they are not the trust
boundary.

```text
model proposes
parser structures
verifier replays
residual repairs
byte law admits or rejects
```

The model may wander. The verifier does not.

### Prethinker Prior

The Prethinker computational-epistemics prior sharpens this boundary for
language-derived state:

```text
LLM constructs semantic workspace
deterministic mapper admits operations
durable state remains behind the admission gate
```

For this stack:

```text
model proposal != accepted atom
source envelope != payload truth
counterfactual lane != durable fact lane
structured absence != missing data
selector decision != corpus mutation
```

Local source manifest:

```text
6-Documentation/docs/provenance/PRETHINKER_COMPUTATIONAL_EPISTEMICS_SOURCES.cff
```

Local packet generator:

```text
4-Infrastructure/shim/prethinker_computational_epistemics_prior.py
```

### Mass Equation Distill Receipt

The local mass-equation distill is admitted only as a coverage/routing prior,
not as a total all-mathematics claim.

Current receipt:

```text
3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified_receipt.json
```

Human summary:

```text
3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified_receipt.md
```

Receipt generator:

```text
4-Infrastructure/shim/mass_equation_distill_receipt.py
```

The receipt records row counts, schema, artifact hashes, source/domain coverage,
feature counts, duplicate-equation hash statistics, and exclusions. Its claim
boundary is explicit: the artifact is useful for OMCF/PIST routing and
candidate-law discovery, but it does not prove equations, does not verify
physics, does not assert full corpus coverage, and does not establish a
compression benchmark.

RRC projection receipt:

```text
3-Mathematical-Models/equations_parquet_tagged/mass_equations_rrc_projection_receipt.json
```

RRC projection table:

```text
3-Mathematical-Models/equations_parquet_tagged/mass_equations_rrc_projection_table.csv
```

The RRC projection maps unique mass-equation hashes into lawful routing shapes
and intentionally keeps under-receipted rows in `HOLD`. This projection is a
route atlas and negative-control surface, not a proof atlas.

### The Well Physics-Dynamics Prior

Polymathic AI's The Well is admitted only as an external replay/route prior for
field-dynamics probes. It is not vendored and is not a compression benchmark
claim.

Source overview:

```text
https://polymathic-ai.org/the_well/datasets_overview/
```

Local route registry:

```text
shared-data/data/nspace_bulk_routes/nspace_bulk_dataset_route_receipt.json
```

Local source manifest:

```text
6-Documentation/docs/provenance/NSPACE_BULK_DATASET_ROUTE_SOURCES.cff
```

For this stack, The Well maps to:

```text
uniform HDF5 grids -> scalar/vector/tensor fields -> boundary-condition lanes
-> PIST/OMCF replay candidates -> residual/rollout stress tests -> HOLD/ADMIT
```

Use is metadata-first and tiny-slice-first. Full-corpus ingest requires
dataset-specific terms, storage budget receipts, field/time/trajectory
subsetting, and byte-accounted replay checks.

### Symbolic Regression / SRBench Prior

SRBench and ParFam are admitted only as external formula-reconstruction priors
for candidate-law discovery, negative controls, and replay scoring. They are
not vendored and do not establish a local benchmark result.

Source surfaces:

```text
https://cavalab.org/srbench/datasets/
https://arxiv.org/html/2310.05537
```

Local route registry:

```text
shared-data/data/nspace_bulk_routes/nspace_bulk_dataset_route_receipt.json
```

For this stack, SRBench/ParFam maps to:

```text
ground-truth formulas -> candidate-law packets -> RRC/OMCF route classes
black-box datasets -> negative controls -> residual scoring -> HOLD/ADMIT
rational families -> deterministic replay candidates -> receipt checks
```

Ground-truth formula tasks may seed exact replay fixtures. Black-box regression
tasks remain negative controls unless a proposed law replays deterministically,
declares residual policy, and passes byte-accounted admission checks.

### Strong-Source Route Shortlist

The following sources are admitted as separate HOLD-first route surfaces:

| Source | Route role |
|---|---|
| The Well | large-scale uniform-grid physics-dynamics replay corpus |
| PDEBench | canonical PDE-family fixtures and baseline residual curves |
| RealPDEBench | real-measurement calibration for simulation residuals |
| ERA5 / NWP / FV3 | weather-system conservation, assimilation, ensemble, and stability route priors |
| MeshGraphNets | irregular mesh / goxel-like topology substrate |
| LeanDojo + mathlib | formal proof and tactic-state routing corpus |
| DLMF + Feynman/SRBench | equation compression and symbolic law recovery |
| NuminaMath | broad math-reasoning proposal curriculum |

Local route registry:

```text
shared-data/data/nspace_bulk_routes/nspace_bulk_dataset_route_receipt.json
```

The routing contract is:

```text
external source -> metadata packet -> tiny replay fixture -> residual receipt
-> RRC/OMCF candidate -> HOLD unless deterministic replay and byte law pass
```

NuminaMath and other informal reasoning corpora may propose candidates, but do
not promote facts or proofs. LeanDojo/mathlib may route proof obligations, but
local Lean replay remains the proof boundary. PDE and mesh corpora may route
field dynamics and topology fixtures, but benchmark claims require explicit
baseline, split, metric, and storage receipts.

### Parallel Metaprobe And Replay Queue

The current parallel metaprobe launch is recorded as a HOLD receipt:

```text
4-Infrastructure/shim/parallel_metaprobe_runs/20260509T053755Z/parallel_metaprobe_launcher_receipt.json
```

Receipt hash:

```text
aa7a1d61131e47544fb25f9cbacfa5ee2a888fb67feca2dfa3f82b92af38373b
```

The run used 6 workers and passed 11 route-prior lanes. It is a launcher
receipt only; it does not promote any source, proof, compression benchmark, or
dataset ingest.

Status note:

```text
ADMIT_FIXTURE != ADMIT
```

`ADMIT_FIXTURE` means a tiny local fixture passed its local replay and byte
checks. It does not promote the whole receipt, source, codec, corpus, theorem,
or benchmark lane. Promotion still requires the top-level receipt decision and
control-filter stack to pass.

The replay fixture queue is:

```text
shared-data/data/replay_fixture_queue/replay_fixture_queue_receipt.json
```

Current queue receipt hash:

```text
914e6564fe33b56dd989016fe3c22369e55956a13a95d408a940d04cdd9bbf72
```

Human summary:

```text
shared-data/data/replay_fixture_queue/replay_fixture_queue.md
```

Current queue head:

```text
1. SRBench / ParFam
2. DLMF / Feynman Symbolic Regression
3. PDEBench
4. The Well
```

The first symbolic-law replay harness is:

```text
shared-data/data/symbolic_law_replay/symbolic_law_replay_receipt.json
```

It currently records 3 tiny fixtures:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not an SRBench result. It is the first local replay check for the
formula-reconstruction route: exact candidate formulas may pass as fixtures,
negative controls must remain HOLD, and small examples that fail byte law stay
diagnostic even when replay is exact.

The first PDE-style replay harness is:

```text
shared-data/data/pde_tiny_replay/pde_tiny_replay_receipt.json
```

Receipt hash:

```text
3871a238ae84450ce6081b6d74b0120b4624c75edf8af1625c61d90ff02c74c9
```

It currently records 3 tiny local fixtures:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not a PDEBench ingest or benchmark result. It is a no-download
micro-fixture for deterministic advection replay: exact periodic replay may
pass as a fixture, wrong-boundary controls must remain HOLD, and tiny exact
examples that do not pay byte law stay diagnostic.

The first The Well-style schema probe is:

```text
shared-data/data/the_well_tiny_probe/the_well_tiny_schema_probe_receipt.json
```

Receipt hash:

```text
97ebac7697555f10b45b3e6e1a1547a28eaaf02d28ab16875607d8a8af14bfb3
```

It currently records 3 tiny metadata fixtures:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not The Well data ingest, HDF5 vendoring, or a benchmark result. It is
a metadata-only schema probe: scalar/vector field rank, axes, boundaries,
dtype, shape, schema hashes, residuals, and byte-law accounting must replay
before any field slice is admitted.

The weather-systems borrowed-math prior is:

```text
shared-data/data/weather_systems_math_prior/weather_systems_math_prior_receipt.json
```

Human summary:

```text
shared-data/data/weather_systems_math_prior/weather_systems_math_prior_receipt.md
```

Local source manifest:

```text
6-Documentation/docs/provenance/WEATHER_SYSTEMS_MATH_PRIOR_SOURCES.cff
```

Receipt hash:

```text
fe3c8d27d24bd45af855faa062077467d9dfd8079c4ec5ab10c80a1101b82eac
```

It records the no-download weather math filter:

```text
weather_state -> transport/replay kernel + residual -> repaired state
Repair(Replay(K,Theta,Pi),R) == S
```

The tiny local replay currently records:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not an NWP forecast, ERA5 ingest, atmospheric-model validation, or
compression benchmark. It is a borrowed-math prior for conservative transport,
boundary-condition residuals, CFL/stability diagnostics, data-assimilation
innovation, ensemble spread, and residual-growth routing. Exact repair and
positive byte law remain the admission boundary; weather terms remain
diagnostics unless normalized and receipted.

The first MeshGraphNets-style topology probe is:

```text
shared-data/data/meshgraphnets_tiny_probe/meshgraphnets_tiny_topology_probe_receipt.json
```

Receipt hash:

```text
3bfa1dc795aed81c1b40d3e6d1937aa01dd807156fd687f0c7c015b5c85b3b25
```

It currently records 3 tiny topology fixtures:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not MeshGraphNets data ingest, trajectory vendoring, or a benchmark
result. It is a no-download topology probe: canonical edges, faces, boundary
nodes, degree sequence, topology hashes, tiny message-pass replay, residuals,
and byte-law accounting must replay before any irregular mesh slice is
admitted.

The quantum cognitive-load transfold prior is:

```text
shared-data/data/quantum_cogload_transfold/quantum_cogload_transfold_receipt.json
```

Human summary:

```text
shared-data/data/quantum_cogload_transfold/quantum_cogload_transfold_receipt.md
```

Receipt hash:

```text
f5dc5da184d2a920d317f08f39e02a37257189484ddf47a1220c053904c48c76
```

It records the merged equation:

```text
L_QCog(H_class,rho,Omega) =
  R_Sigma_Q({C_k_Q R_k_Q(x_k_Q(H_Q,U_Q,rho,Omega);theta_k_Q)
  lambda_phi^D_f B_k_Q(Omega)} for k in {I,E,G,R,M}; theta_Sigma_Q)

H_Q = (Pauli o C_n o Q_hbar)(H_class) = sum_alpha c_alpha P_alpha
```

The tiny Pauli replay currently records:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not a quantum-algorithm result, cognitive-science validation, proof, or
compression benchmark. It is a route prior for Pauli-string cognitive-load
features: coefficient entropy, support size, noncommutative coupling burden,
entanglement placeholder, truncation residual, replay depth, measurement
burden, and semantic/basis mismatch.

The quantum-basis compression objective receipt is:

```text
shared-data/data/quantum_basis_compression_objective/quantum_basis_compression_objective_receipt.json
```

Human summary:

```text
shared-data/data/quantum_basis_compression_objective/quantum_basis_compression_objective_receipt.md
```

Receipt hash:

```text
c6d23f33eb89ab26bfb1135e7f102dbbe94fa710b25b6685db715508d5ab79be
```

It records the compression implication:

```text
S -> (K_Q, Theta_Q, R, Pi) -> S_hat
Decode(K_Q, Theta_Q, R, Pi) == S
epsilon_byte = ||S - S_hat||_0 = 0
```

and the counted objective:

```text
J_compress =
  |D| + |K_Q| + |Theta_Q| + |R| + |Pi|
  + lambda_T D_replay + lambda_L L_decode

G_Q = |S| - (|D| + |K_Q| + |Theta_Q| + |R_Q| + |Pi_Q|)
```

The tiny generator/residual replay currently records:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not a quantum-compression result, Hutter claim, or proof. It is an
admission objective: a basis/kernel is useful only when lawful reconstruction
plus parameters, protocol, and residual replay byte-exactly and pay positive
byte law.

The enwiki8 wiki-logogram slice probe is:

```text
shared-data/data/enwiki8_wiki_logogram_probe/enwiki8_wiki_logogram_probe_receipt.json
```

Human summary:

```text
shared-data/data/enwiki8_wiki_logogram_probe/enwiki8_wiki_logogram_probe_receipt.md
```

Encoded core:

```text
shared-data/data/enwiki8_wiki_logogram_probe/enwiki8_wiki_logogram_probe_core.wlg1
```

Receipt hash:

```text
d93c768e02781fc197e6134238808197f7dbb69be590ece90f7a6a1853c54fac
```

It records a bounded local `enwik8` slice probe:

```text
corpus: shared-data/corpora/enwik8
offset: 1406
length: 4096
Decode(wiki_logogram_core) == slice_bytes
```

The tiny local replay currently records:

```text
ADMIT_FIXTURE: 1
```

Accounting:

```text
raw slice: 4096 bytes
encoded core: 3453 bytes
packet estimate: 4025 bytes
zlib-9 baseline: 1365 bytes
bz2-9 baseline: 1469 bytes
lzma-9 baseline: 1420 bytes
```

This is not a Hutter Prize submission, full enwiki8 result, or evidence of
compression competitiveness. It is a grammar-admission probe for MediaWiki/XML
replay atoms such as wiki links, templates, XML tag pairs, text-attribute
pairs, and exact empty tags. The ordinary compressors remain much smaller on
this slice; the probe only shows byte-exact replay and a positive local packet
estimate under truncated per-atom receipts.

The enwiki9 logogram targeter bundle receipt is:

```text
shared-data/data/enwiki9_logogram_targeter/enwiki9_logogram_targeter_receipt.json
```

Human summary:

```text
shared-data/data/enwiki9_logogram_targeter/enwiki9_logogram_targeter_receipt.md
```

Source bundle:

```text
/home/allaun/Documents/ingest/enwiki9_logogram_target.zip
```

Receipt hash:

```text
f77d7404ed76c1dd7697b5a02ddaf9ad02d073d40c09a5d747d8dc678ffbae9f
```

It records import and replay of the uploaded enwiki9 slice-targeting harness:

```text
demo slices: 3
demo roundtrip: true
sample source: /home/allaun/Downloads/data/enwik9_data/1234567
sample bytes: 20532
sample slices: 4
sample roundtrip: true
```

Current accounting:

```text
demo raw/core/packet: 948 / 1115 / 1491 bytes
sample raw/core/packet: 16384 / 17290 / 18678 bytes
```

This is not a canonical `enwik9` corpus run, Hutter/LTCB submission, or
compression-competitiveness claim. The uploaded bundle is a slice targeter, not
the 1,000,000,000-byte corpus. The available local sample is 20,532 bytes, and
the current grammar expands it; the useful result is byte-exact replay plus
slice-class targeting for future dictionary promotion.

The enwiki9 fixed XML/MediaWiki dictionary probe is:

```text
shared-data/data/enwiki9_logogram_xml_dict_probe/enwiki9_logogram_xml_dict_probe_receipt.json
```

Human summary:

```text
shared-data/data/enwiki9_logogram_xml_dict_probe/enwiki9_logogram_xml_dict_probe_receipt.md
```

Receipt hash:

```text
f9d2eb3bca3985bcc88c459b357f25fe0e194bb7c2e00385ed28b93a99357c4a
```

It records the v2 dictionary-promotion test:

```text
fixed tag entries: 25
pair tag entries: 12
attribute tag entries: 9
motif entries: 11
dictionary bytes: 1064
```

Current accounting:

```text
demo raw/core/packet/global-delta:
  948 / 767 / 1011 / -1127 bytes

local sample raw/core/packet/global-delta:
  16384 / 16177 / 17141 / -1821 bytes
```

Compared to v1:

```text
demo v1 raw/core/packet: 948 / 1115 / 1491 bytes
local sample v1 raw/core/packet: 16384 / 17290 / 18678 bytes
```

This is still `HOLD`: exact replay passes and `delta_core` flipped positive,
but packet and global deltas remain negative after receipt stubs and dictionary
bytes are counted. The local sample is also a noncanonical HTML file, not
`enwik9`. The valid conclusion is that fixed grammar promotion works as a core
shrink step; it is not yet compression admission.

The enwiki9 receipt-aggregation probe is:

```text
shared-data/data/enwiki9_logogram_receipt_aggregation_probe/enwiki9_logogram_receipt_aggregation_probe_receipt.json
```

Human summary:

```text
shared-data/data/enwiki9_logogram_receipt_aggregation_probe/enwiki9_logogram_receipt_aggregation_probe_receipt.md
```

Receipt hash:

```text
5b264b0fedf55f48bf1e790d2375bc4504b353e302a76677e5447ab39e8565d3
```

It records the v3 receipt-mode test:

```text
per-atom receipt stubs -> slice_root_v1
slice receipt root bytes: 32
protocol ID bytes per slice: 4
dictionary bytes still counted globally: 1064
```

Current accounting:

```text
demo raw/core/v3-packet/global-delta:
  948 / 767 / 875 / -991 bytes

local sample raw/core/v3-packet/global-delta:
  16384 / 16177 / 16321 / -1001 bytes
```

Compared to v2:

```text
demo packet delta: -63 -> 73 bytes
local sample packet delta: -757 -> 63 bytes
```

This is still top-level `HOLD`: exact replay passes and packet deltas are now
positive under slice-level receipt aggregation, but global deltas remain
negative once the fixed dictionary is counted. The local sample is also still a
noncanonical HTML file, not `enwik9`. The valid conclusion is that receipt
aggregation fixes the packet-overhead failure for these fixtures; dictionary
amortization over canonical slices remains unproven.

The enwiki9 dictionary-amortization probe is:

```text
shared-data/data/enwiki9_logogram_dictionary_amortization_probe/enwiki9_logogram_dictionary_amortization_probe_receipt.json
```

Human summary:

```text
shared-data/data/enwiki9_logogram_dictionary_amortization_probe/enwiki9_logogram_dictionary_amortization_probe_receipt.md
```

Receipt hash:

```text
6eb32944aaba661e6b7d964b50d758b21a3b992f60587ab4a65b7a692b048907
```

It records the v4 accounting-scope test:

```text
PASS -> ADD -> PAUSE -> SUBTRACT
timestamp role: metadata_only
generated_at_utc included in receipt hash: false
dictionary bytes: 1064
slice size: 4096
byte limit per source: 131072
```

Current noncanonical fixture accounting:

```text
1234567 local HTML:
  raw/core/v3-packet/global-delta:
    20532 / 20282 / 20498 / -1030 bytes
  verdict: HOLD_GLOBAL

fawiki XML head:
  raw/core/v3-packet/global-delta:
    131072 / 125732 / 126884 / 3124 bytes
  verdict: ADMIT_FIXTURE

jawiki XML head:
  raw/core/v3-packet/global-delta:
    131072 / 130700 / 131852 / -1844 bytes
  verdict: HOLD_PACKET

viwiki XML head:
  raw/core/v3-packet/global-delta:
    131072 / 130152 / 131304 / -1296 bytes
  verdict: HOLD_PACKET
```

This is still top-level `HOLD`: one noncanonical MediaWiki XML fixture crosses
the global-delta gate after dictionary amortization, but no canonical `enwik9`
slice, baseline-compressor comparison, full protocol package, or corpus-scale
Hutter/LTCB accounting has passed. The valid conclusion is narrower: the same
frozen v2 dictionary and v3 receipt mode can amortize on at least one local
MediaWiki XML fixture while failing on others.

The enwiki9 canonical-slice baseline probe is:

```text
shared-data/data/enwiki9_logogram_canonical_baseline_probe/enwiki9_logogram_canonical_baseline_probe_receipt.json
```

Human summary:

```text
shared-data/data/enwiki9_logogram_canonical_baseline_probe/enwiki9_logogram_canonical_baseline_probe_receipt.md
```

Receipt hash:

```text
8159af52db8a90cd599ab6f279ce090e08e507fb2673bde352a3bb163e1d8452
```

It records the v5 provenance and baseline test:

```text
PROVENANCE -> PASS -> ADD -> PAUSE -> SUBTRACT -> BASELINE
codec_frozen_from: v4
encoder_changed: false
clock_participates_in_hash: false
canonical enwik9 size requirement: 1,000,000,000 bytes
```

Current local fixture accounting:

```text
input: /home/allaun/Downloads/data/enwik9_data/1234567
input size: 20532 bytes
canonical claim: fixture
provenance decision: FIXTURE

raw/core/packet/global-delta:
  20532 / 20248 / 20284 / -816 bytes

baselines:
  zlib-9: 7008 bytes
  bz2-9: 7510 bytes
  lzma-9: 6672 bytes
  zstd-19: 6800 bytes

decision: HOLD_GLOBAL
```

This is not canonical `enwik9` evidence. It is a v5 smoke receipt showing that
the frozen codec, provenance gate, duplicate-window guard, clockless event
chain, and baseline accounting run correctly on the existing local fixture.
The fixture preserves the ladder result: replay passes and packet delta remains
positive, but global delta is negative after dictionary accounting and ordinary
compressors are much smaller.

The language surface-ambiguity negative-control receipt is:

```text
shared-data/data/language_surface_ambiguity_negative_control/language_surface_ambiguity_negative_control_receipt.json
```

Human summary:

```text
shared-data/data/language_surface_ambiguity_negative_control/language_surface_ambiguity_negative_control_receipt.md
```

Receipt hash:

```text
f8dfa1611b6aa4f7dfea86f3d8d5cd89654fa1b0bb57a4d380841fba9be5005b
```

It records two language-law negative controls:

```text
flown_by_cancellation -> HOLD_DERIVATION
buffalo_surface_collision -> HOLD_SURFACE_COLLISION
```

The first fixture marks the "grew/grown = flew/x" derivation as invalid even
when it happens to land on the lexically correct output. Correct output is not
proof of a lawful replay path.

The Buffalo fixture handles repeated word surfaces by typed role:

```text
city_modifier
plural_noun_subject
plural_noun_relative_subject
transitive_verb_relative
transitive_verb_main
plural_noun_object
```

The surface token may be reused, but it cannot be collapsed into one untyped
atom unless role, position, case, and replay order are preserved or carried as
residual. This is not an English model or compression claim; it is a guardrail
against analogy leakage and same-surface role collision.

The reconstruction-core ladder project-memory receipt is:

```text
shared-data/data/stack_memory_promotions/reconstruction_core_ladder_memory_receipt.json
```

Human summary:

```text
shared-data/data/stack_memory_promotions/reconstruction_core_ladder_memory.md
```

Receipt hash:

```text
4364e9c1092020660f4ff3a64804ebc88db7136433f049ddaff9ac2880d29b39
```

It promotes only a compact memory pointer:

```text
memory key: reconstruction_core_ladder_2026_05_09
lawful status: HOLD_TOP_LEVEL
next action: find/verify canonical enwik9, then run frozen v5 on canonical slices
```

This is not a private assistant memory write and not a compression promotion.
It records receipt paths, hashes, statuses, guardrails, claim boundary, and next
action pointer under the local memory-write rule.

The DNA-filtered codec objective receipt is:

```text
shared-data/data/dna_codec_filter/dna_codec_filter_receipt.json
```

Human summary:

```text
shared-data/data/dna_codec_filter/dna_codec_filter_receipt.md
```

Local source manifest:

```text
6-Documentation/docs/provenance/DNA_CODEC_FILTER_SOURCES.cff
```

Receipt hash:

```text
ae9b5fa3b54ef88a5035bf234b11745d6644dbfa2c046481077c16c57339b846
```

It records the analogy-bounded DNA codec filter:

```text
S = Repair_R(Regulate_B_DeltaG(Replay(K,Theta,Pi)))
Repair(Replay(K,Theta,Pi),R) == S
epsilon_byte = 0
```

The tiny local replay currently records:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 2
```

This is not a DNA model, biological-data ingest, thermodynamic simulation, or
compression benchmark. It is a codec filter prior: conserved motif gain, local
binding compatibility, repair layering, mutation-budget pressure, and replay
curvature may influence routing, but exact repair and positive byte law remain
the admission boundary.

The logogram-DNA codec objective receipt is:

```text
shared-data/data/logogram_dna_codec/logogram_dna_codec_receipt.json
```

Human summary:

```text
shared-data/data/logogram_dna_codec/logogram_dna_codec_receipt.md
```

Receipt hash:

```text
381ee58394408986d1971edf6ac388483786cc89fef7de982cefddcc8bc99f87
```

It records the Omindirection/GCCL-filtered version:

```text
S = Repair_R(Regulate_B_DeltaG(Replay_Pi(Gamma)))
a_i = (p_i,h_i,d_i,chi_i,phi_i,x_i,tau_i,r_i,g_i,rho_i,delta_i)
payload != glyph != rendered layout
```

The tiny local replay currently records:

```text
ADMIT_FIXTURE: 1
HOLD_DIAGNOSTIC: 1
QUARANTINE_DIAGNOSTIC: 1
```

This is not a renderer-correctness result, global logogram compression result,
or biological claim. It is a law-gated symbolic-genome prior: glyph codons can
route reconstruction only when payload, direction, chirality/phase, placement,
residual, receipt, and adapter gates preserve byte-exact recovery or explicitly
route to `HOLD` / `QUARANTINE`.

The LeanDojo/mathlib proof-boundary replay receipt is:

```text
shared-data/data/lean_proof_replay/lean_proof_replay_receipt.json
```

Human summary:

```text
shared-data/data/lean_proof_replay/lean_proof_replay_receipt.md
```

Local theorem fixture:

```text
0-Core-Formalism/lean/Semantics/ExtensionScaffold/Compression/ProofReplay.lean
```

Receipt hash:

```text
9855099f61256bb7e3ec30e298a32119212e3842949ae3ae0281676d4ef5851d
```

The local replay observed:

```text
countedBytes repeatKernelFixture = 94
byteGainPositive repeatKernelFixture = true
admitCandidate repeatKernelFixture = true
admitCandidate residualHeavyFixture = false
admitCandidate nonExactFixture = false
```

Verification commands:

```text
lake build ExtensionScaffold.Compression.ProofReplay
lake env lean ExtensionScaffold/Compression/ProofReplay.lean
lake build
```

All three completed successfully in the local Lean project. This is not a
LeanDojo benchmark result, mathlib coverage claim, or external theorem proof.
It is a proof-boundary fixture: external proof corpora may route obligations,
but only local Lean replay promotes proof state.

### Forward Foundation Equation Compiler

The forward-foundation compiler is the current trust boundary for equation
atoms:

```text
6-Documentation/docs/specs/FORWARD_FOUNDATION_EQUATION_COMPILER.md
```

Local generator:

```text
4-Infrastructure/shim/foundation_forward_equation_compiler.py
```

Current receipt:

```text
shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler_receipt.json
```

Receipt hash:

```text
b9c26ec185772576b27a9d176300ebe053edaae3b49650e9e2581969dda1b278
```

Canonical rule:

```text
No backward trust chain. Only forward admissible generation.
```

The foundation set is:

```text
F0 = {O4, SD, MN, gamma_star, H_dV, Omega, Lambda, A}
```

The shell equation is:

```text
SD = L4(O4) + L3(Rg3) + chi0 + U4 + E_HD + U_under
```

Human theorem labels, citation chains, equation names, expert names, and
logogram names are routing hints only. A trusted equation object must compile
forward from `F0`, declare residuals, close under `chi0`, pay projection and
budget costs, and carry a recomputable receipt. Anything that cannot compile
from the foundation kernel remains `HOLD`, `QUARANTINE`, `U_under`, or `NaN0`.

The current decision is:

```text
ACCEPT_CONTRACT_HOLD_RESULTS
```

This means the compiler contract itself is admitted as a local rule, but it
does not promote external equations, theorem labels, or benchmark claims.

Origin metadata is explicitly not authority:

```text
Origin may inspire. Only closure admits.
No vibes-to-axioms pipeline without a receipt.
```

Historical era, institution, biography, private intuition, altered-state
suspicion, and aesthetic elegance may route a candidate, but cannot promote it.

### Buoyancy Added-Mass Mobius Fixture

The buoyancy added-mass Mobius fixture is the first small physics equation atom
compiled through the forward-foundation style:

```text
4-Infrastructure/shim/buoyancy_added_mass_mobius_fixture.py
```

Current receipt:

```text
shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius_receipt.json
```

Human summary:

```text
shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius.md
```

Receipt hash:

```text
ad2dada2df046f6576f8831bbdc72d86f0a7b88ca9ab25712ece84ad8abadfcc
```

It compresses the classical early-time added-mass expression:

```text
a = g * (rho_o - rho_m) / (rho_o + C*rho_m)
```

into the Mass-Number Mobius form:

```text
MN_rho = (rho_o - rho_m) / (rho_o + rho_m)
alpha_C = 2 / (1 + C)
kappa_C = (1 - C) / (1 + C)
lambda_BAM(MN_rho, C) =
  g * alpha_C * MN_rho / (1 + kappa_C * MN_rho)
```

Inverse:

```text
MN_rho = (a/g) / (alpha_C - kappa_C*(a/g))
```

The fixture checks exact rational equivalence with the expanded form and exact
rehydration back to `MN_rho` for:

```text
sphere, rho_o/rho_m = 2, C = 1/2 -> a/g = 0.4
cylinder perpendicular to axis, rho_o/rho_m = 2, C = 1 -> a/g = 1/3
light sphere limit probe, rho_o/rho_m = 0, C = 1/2 -> a/g = -2
```

Decision:

```text
ACCEPT_FIXTURE_WITH_BOUND_CORRECTION
```

This is not a new fluid theorem or experimental result. It is an algebraic
compression fixture and logogram candidate. The bound claim is explicitly
corrected: `|a| <= g` holds for the heavier/sinking branch or for suitable
`C >= 1` cases, but not for every density branch in the ideal added-mass model.
Drag, vorticity, and boundary effects remain declared residual lanes.

### Mass Number Transform Registry

The Mass Number transform registry is:

```text
4-Infrastructure/shim/mass_number_transform_registry.py
```

Current receipt:

```text
shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json
```

Human summary:

```text
shared-data/data/mass_number_transform_registry/mass_number_transform_registry.md
```

Receipt hash:

```text
b215abe8cca08253dd62a2c2e84ff1f90fbd8e7eb5b2bb02d60dec39bbea2b9c
```

It records reusable Mass-Number-able transform families:

```text
MN(a,b) = (a-b)/(a+b)
MN(a,b) = tanh(0.5*ln(a/b)) for positive a,b
```

Accepted exact-kernel opcodes currently include:

```text
MN
MN_RATIO_INV
MN_MOBIUS_LOAD
MN_SPLIT
MN_REDUCED
MN_PAIR_PRODUCT
MN_BLEND
MN_REFLECT
MN_TRANSMIT_POWER
MN_BINARY_P
MN_ELASTIC_1D
```

`MN_BINARY_ENTROPY` remains `HOLD_ANALYTIC` until log base, numerical
precision, and approximation/error policy are receipted.

Decision:

```text
ACCEPT_REGISTRY_WITH_HOLD_ANALYTIC
```

This is a compression/logogram registry, not a theorem atlas. It says repeated
ratio, pair, blend, reflection, binary-choice, and geometry-loaded Mobius
families can route through one bounded contrast plus a small transform opcode
when exact rational checks pass. Analytic or numerical transforms stay HOLD.

### Cross-Domain Kernel Adapter Registry

The cross-domain kernel adapter registry is:

```text
4-Infrastructure/shim/cross_domain_kernel_adapter_registry.py
```

Current receipt:

```text
shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry_receipt.json
```

Human summary:

```text
shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry.md
```

Receipt hash:

```text
a66552526d5213a8122ce8f1efa56137f70c707d991ac7fdc90dc83d970ac081
```

Cross-domain compression is admitted only as adapter-gated kernel reuse:

```text
X_d = A_d[K_j(theta)] + R_d + chi0
same shape does not imply same law
```

Current status counts:

```text
ACCEPT_ADAPTER_FIXTURE: 1
ACCEPT_KERNEL_ADAPTER: 4
HOLD_ANALYTIC_ADAPTER: 1
HOLD_BOUNDARY_WITNESS: 1
HOLD_CONTACT_TOPOLOGY: 1
```

Decision:

```text
HOLD_CROSS_DOMAIN_WITH_ACCEPTED_KERNEL_ADAPTERS
```

Accepted adapter entries admit algebraic reuse only. Domain truth, physical
interpretation, geometry optimality, corpus compression, and benchmark claims
still require source equations, deterministic replay, residual policy, and
closure receipts.

The moving-sofa / couch route is intentionally `HOLD_CONTACT_TOPOLOGY`:

```text
continuous motion -> finite contact grammar -> curve atoms -> area/closure receipt
```

It is useful as a COUCH stress surface because contact-state switching can be
represented as bounded clearance contrasts, but no moving-sofa optimality or
area claim is promoted.

The Earth-core / seismic-horizon route is intentionally
`HOLD_BOUNDARY_WITNESS`: boundary-crossing waves may route hidden-structure
hypotheses, but inaccessible interior uncertainty remains `Underverse` until
source data, residuals, and closure checks exist.

### Magnetic Derivative Kernel Probe

The magnetic derivative kernel probe is:

```text
4-Infrastructure/shim/magnetic_derivative_kernel_probe.py
```

Current receipt:

```text
shared-data/data/magnetic_derivative_kernels/magnetic_derivative_kernel_receipt.json
```

Human summary:

```text
shared-data/data/magnetic_derivative_kernels/magnetic_derivative_kernel.md
```

Receipt hash:

```text
b4617a8ff31586250efafd13e3ed402535fcad5d564922599aaa3cb95134c7e3
```

Current status counts:

```text
ACCEPT_DERIVATIVE_FIXTURE: 2
ACCEPT_KERNEL_ADAPTER: 1
ACCEPT_VECTOR_FIXTURE: 1
HOLD_ANALYTIC_ADAPTER: 1
HOLD_FIELD_EQUATION: 2
HOLD_MATERIAL_ADAPTER: 1
```

Decision:

```text
HOLD_MAGNETIC_DOMAIN_WITH_ACCEPTED_FIXTURES
```

Accepted fixtures include local scalar/vector algebra only:

```text
d/dB [B^2/(2*mu)] = B/mu
F_x = m*dB/dx
F_B = q*cross(v,B)
Gamma_mu = MN(mu2,mu1)
```

Maxwell, MHD, gauge, boundary-condition, hysteresis, material-response, and
measurement claims remain HOLD until units, sign conventions, source data,
residual policies, and closure receipts exist.

### Solids Physics Kernel Probe

The solids physics kernel probe is:

```text
4-Infrastructure/shim/solids_physics_kernel_probe.py
```

Current receipt:

```text
shared-data/data/solids_physics_kernels/solids_physics_kernel_receipt.json
```

Human summary:

```text
shared-data/data/solids_physics_kernels/solids_physics_kernel.md
```

Receipt hash:

```text
98501df5a36ddd8a103ff40e6c8973f93e5271df325dd43ebdbebe59e896defb
```

Current status counts:

```text
ACCEPT_DERIVATIVE_FIXTURE: 1
ACCEPT_ISOTROPIC_FIXTURE: 1
ACCEPT_KERNEL_ADAPTER: 2
ACCEPT_LINEAR_ELASTIC_FIXTURE: 1
HOLD_ANALYTIC_ADAPTER: 1
HOLD_FRACTURE_ADAPTER: 1
HOLD_PLASTICITY_ADAPTER: 1
HOLD_TENSOR_ADAPTER: 1
```

Decision:

```text
HOLD_SOLIDS_DOMAIN_WITH_ACCEPTED_FIXTURES
```

Accepted fixtures include local linear-elastic algebra only:

```text
sigma = E*epsilon
U = E*epsilon^2/2 = sigma^2/(2E)
dU/depsilon = sigma
G = E/(2*(1+nu))
K = E/(3*(1-2*nu))
E_eff = S/2*(1-MN(E1,E2)^2)
Gamma_Z = MN(Z2,Z1)
```

Wave-speed, plasticity, fracture, anisotropic tensor, boundary-value, geometry,
and material-model claims remain HOLD until units, conventions, source data,
boundary conditions, and residual policies are receipted.

### Cross-Domain Easy Wins Route Map

The cross-domain easy-wins route map is:

```text
4-Infrastructure/shim/cross_domain_easy_wins_route_map.py
```

Current receipt:

```text
shared-data/data/cross_domain_easy_wins/cross_domain_easy_wins_route_map_receipt.json
```

Human summary:

```text
shared-data/data/cross_domain_easy_wins/cross_domain_easy_wins_route_map.md
```

Receipt hash:

```text
ac1fe2ca6ee469c046cdb5fc78cef9efca6a601aee2e5270ef4b8c5854bb1e2e
```

Decision:

```text
ADMIT_ROUTE_MAP_HOLD_FIRST
```

Ranked next probes:

```text
1. electrical circuits and transmission lines
2. thermal conduction and diffusion
3. acoustics and scalar waves
4. probability, routing, and expert selection
5. two-body mechanics and orbital reductions
6. chemistry equilibrium and reaction routing
7. optics at normal incidence
8. statistics and signal scoring
9. biology expression/accessibility contrast
10. contact geometry and motion planning
```

This is a planning receipt only. It does not assert compression gain, domain
truth, or benchmark performance. The rule is:

```text
prefer exact local algebra first
HOLD nonlinear, field, geometry, and measurement claims
```

## 6. Control Filters

The reconstruction core is guarded by the control-filter stack:

| Filter | Function |
|---|---|
| LoC/NES Monster | rejects fake pattern / mirage / overfit |
| FYC Gate | rejects impossible constrained-manifold traversal |
| COUCH | rejects unstable hysteresis or chaotic route dynamics |
| Tree Fiddy | bounds recursion, retries, and refinement depth |
| BHOCS | commits only bounded, replayable survivors |

Canonical admission sketch:

```text
Admit(X) =
  replay_valid(X)
  ∧ byte_gain(X) > 0
  ∧ residual_declared(X)
  ∧ LoC_NES_pass(X)
  ∧ FYC_pass(X)
  ∧ COUCH_stable(X)
  ∧ TreeFiddy_bounded(X)
  ∧ BHOCS_verified(X)
```

## 7. Claim Boundary

This document does not claim that the current stack beats any compression
benchmark. It defines the inspection boundary for compressed artifacts:

```text
not readable != not auditable
```

The audit target is replay, residual repair, byte-exact reconstruction, and
receipted byte accounting.
