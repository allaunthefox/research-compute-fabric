# Neural Type Eigenvector Coverage

Status: candidate research target

Goal: use broad neuron-type coverage to improve routing and compression
efficiency without pretending the stack has a complete model of every neuron in
biology.

## Plain Version

The useful move is not "model all neurons." That target is too large and would
invite overclaiming.

The useful move is:

```text
public neuron reconstructions
  -> typed morphology features
  -> species / region / cell-type evidence graph
  -> principal coverage eigenvector
  -> routing prior for which neural analogues pay their bills
```

In Research Stack terms, this is a coverage-driven gestalt vector. It asks which
neuron-type features repeatedly explain useful structure across species,
regions, and modalities, then promotes only those features that increase
retrieval, compression, routing, or verification efficiency.

## Evidence Inputs

Initial public surfaces to ingest or reference:

| Source | What it contributes | Receipt requirement |
|---|---|---|
| NeuroMorpho.Org | Reconstructed neuronal morphologies, usually SWC-like trees with metadata. | Species, region, cell type, reconstruction method, license/provenance. |
| Allen Cell Types Database | Morphology plus electrophysiology and transcriptomic labels for selected cells. | Dataset id, cell id, modality coverage. |
| BICCN / BICAN atlases | Cross-modal brain-cell taxonomy and region coverage. | Versioned atlas label and taxonomy mapping. |
| SWC morphology files | Tree geometry for soma, axon, dendrite, branch structure. | Parser result, malformed-node count, unit assumptions. |

This target should prefer coverage receipts over completeness claims. Missing
species, missing modalities, and ambiguous cell-type labels remain visible.

## Feature Basis

Each neuron sample becomes a fixed feature vector:

```text
f_i =
  [
    soma_size,
    total_dendrite_length,
    total_axon_length,
    branch_count,
    branch_order_depth,
    sholl_crossing_profile,
    arbor_asymmetry,
    tortuosity,
    spine_or_terminal_density,
    electrophysiology_bucket,
    transcriptomic_bucket,
    species_bucket,
    region_bucket
  ]
```

The feature vector must be normalized per source and tagged with missingness.
Unknown values are not filled with vibes; they are encoded as missing evidence
and penalized in the receipt.

## Graph Construction

Create a typed graph:

```text
V = neuron samples + cell-type labels + species + regions + feature buckets
E = has_feature, belongs_to_type, observed_in_species, observed_in_region,
    similar_morphology, shared_modality, cites_source
```

Edge weights should be finite and inspectable:

```text
w(u, v) =
  morphology_similarity
  * provenance_confidence
  * modality_coverage
  * license_ok
  * missingness_penalty
```

The graph is useful only if every high-weight edge can explain where it came
from.

## Coverage Eigenvector

Let `A` be the weighted adjacency matrix over the typed evidence graph.

```text
A x = lambda x
```

The principal vector `x` is the broad-coverage direction. It ranks neuron-type
features and labels by how much they connect reliable evidence across the graph.

For stack use, define a coverage score:

```text
Coverage(node) = x_node * source_count(node) * modality_count(node)
                 / (1 + missingness(node) + contradiction_count(node))
```

This makes repeated, multi-source structure rise while brittle single-source
patterns sink.

## Efficiency Gate

A neural feature pays its bills only if it improves an operational target.

```text
EfficiencyGain(feature) =
  baseline_cost - routed_cost(feature)
```

```text
NeuralTypeMass(feature) =
  admissible_efficiency_gain
  / (1 + residual_risk + missingness + overfit_penalty)
```

Promotion rule:

```text
promote(feature) iff
  EfficiencyGain(feature) > 0
  and Coverage(feature) >= coverage_floor
  and overfit_penalty <= overfit_ceiling
  and provenance_receipt_ok
```

If a feature is beautiful but does not reduce search, compression, routing, or
verification cost, it stays archived as biological texture rather than promoted
as architecture.

## Anti-Overfit Tests

Run these before using the eigenvector as a routing prior:

1. Hold out species and require the same feature family to remain useful.
2. Hold out brain regions and check whether the ranking collapses.
3. Shuffle labels and require the coverage score to drop.
4. Compare against random graphs with the same degree distribution.
5. Separate morphology-only, electrophysiology-only, and transcriptomic-only
   eigenvectors, then test whether the fused vector adds value.

The null model matters. If a "neural type" vector performs no better than
degree, popularity, or dataset imbalance, it is not a discovery; it is a mirror.

## Rigor Protocol

The old local `neuron_coding_topology.json` average of `93.0` is a hand-scored
proxy. It can remain as an intuition note, but it is not acceptable evidence for
promotion.

The rigorous number must be computed from an evidence graph and reported with:

| Field | Meaning |
|---|---|
| `mean_coverage_all_nodes` | Average coverage score across every graph node. |
| `mean_coverage_feature_nodes` | Average coverage score across morphology/electrophysiology/transcriptomic feature nodes only. |
| `eigenvalue` | Principal graph eigenvalue from power iteration. |
| `residual_delta` | Final power-iteration residual; lower is better. |
| `holdouts` | Top-k stability when species or regions are removed. |
| `null_model.z_score` | Whether top coverage beats shuffled random graphs. |

Promotion thresholds should start conservative:

```text
residual_delta <= 1e-8
species_holdout_top_k_overlap >= 0.50
region_holdout_top_k_overlap >= 0.50
null_model.z_score >= 2.0
mean_coverage_feature_nodes > 0
```

Any result below those gates is exploratory only.

## Local Computation

The first local implementation is:

```text
5-Applications/scripts/neural_type_eigenvector_coverage.py
```

Run a smoke/demo graph:

```bash
python3 5-Applications/scripts/neural_type_eigenvector_coverage.py --demo
```

Run against a real evidence graph:

```bash
python3 5-Applications/scripts/neural_type_eigenvector_coverage.py \
  --input data/neural_type_evidence.jsonl \
  --output 5-Applications/out/neural_type_eigenvector_coverage.json
```

Required input records:

```json
{"kind":"feature","id":"feature:deep_branch_order","source_count":3,"modality_count":2,"missingness":0}
{"kind":"neuron_sample","id":"source:cell","species":"mouse","region":"cortex","source_count":1,"modality_count":1}
{"kind":"edge","src":"source:cell","dst":"feature:deep_branch_order","rel":"has_feature","weight":0.92,"receipt":"source row or file hash"}
```

The number to quote is not the largest node score. Quote the mean coverage, the
top feature rows, the holdout stability, and the null-model z-score together.

## Stack Integration

| Stack surface | Use |
|---|---|
| Semantic Eigenvector Bundle | Treat repeated neuron-type structure as a principal concept direction. |
| Mass Number | Promote only features with admissible efficiency gain and bounded residual risk. |
| FAMM | Store failed neuron analogues as scars so the same biological metaphor is not retried forever. |
| Internal semantic search | Rank biological analogues by coverage, source receipts, and measured utility. |
| GPU + FPGA verification | GPU computes feature similarity/eigenvector updates; FPGA verifies hashes, bounds, and receipt gates. |

## Minimal Artifact Shape

Store the first implementation as JSONL/SQLite before building a UI:

```json
{"kind":"neuron_sample","id":"source:cell","species":"...","region":"...","type":"...","features":{},"missing":[]}
{"kind":"edge","src":"source:cell","dst":"feature:high_branch_depth","rel":"has_feature","weight_q0_16":53120,"receipt":"..."}
{"kind":"coverage_score","node":"feature:high_branch_depth","score_q0_16":41240,"source_count":12,"modality_count":2}
```

The first win is a ranked list of biological structures that actually improve a
Research Stack task. The long-term win is an explainable neural morphology
manifold that says which living shapes are worth borrowing from, and why.
