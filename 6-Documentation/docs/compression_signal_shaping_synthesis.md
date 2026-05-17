# Compression Signal-Shaping Synthesis

Date: 2026-05-08

Runner:

```text
4-Infrastructure/shim/compression_signal_shaping_synthesis.py
```

Receipt:

```text
4-Infrastructure/shim/compression_signal_shaping_synthesis_receipt.json
```

Receipt hash:

```text
fc06057b20dc2281161e7380a63557171ab4d87ee7a82277fe2e8d74b1446f68
```

## Primary Read

Across the local compression, compressed-sensing, signal-root,
semantic-topology, and docmd payload notes, the new pattern is not another
universal compressor.

The new pattern is:

```text
signal-shaped route compiler
```

Shape the route space before coding, then pay exact residual, witness, decoder,
and container bytes after coding.

## Approach Classes

```text
PAQ-style context mixing
  shapes probability context

decision-diagram route search
  shapes candidate route space

T16 candidate pipeline
  shapes weak event detection

Phi response-family selection
  shapes response curve

nonlinear compressed sensing
  shapes regular nonlinear measurement maps

generative compressed sensing
  shapes latent proposal manifold

invertible generative inverse priors
  shapes invertible / flow charts

holographic fractional recursive fold
  shapes boundary descriptor and bounded memory

signal invariant roots
  shapes signal morphology feature space

semantic topology regimes
  shapes fold / prune / tear decisions

LLM control-plane compression
  shapes prompt / logogram / metaprobe representation

docmd static payload strategy
  shapes runtime payload
```

## What New Pops Up

### N1 Signal-Shaped Route Compiler

Combine signal invariant roots with decision-diagram route search:

```text
chunk
  -> feature vector
  -> route family
  -> codec trial
  -> exact residual
```

Candidate equation:

```text
route =
  argmin_r LB(r | phi_signal(chunk), topology_regime, history_state)
```

First test:

```text
wiki8 chunk sweep with:
  entropy
  XML tag density
  DCT energy
  transient edges
  autocorrelation
  cosine reuse
```

Promotion gate:

```text
chosen route beats bz2 / zstd baseline after feature and witness bytes
```

### N2 Runtime Staticization As Compression Prepass

Use the docmd lesson:

```text
do not ship branches you can rebuild
```

Candidate shape:

```text
tiddlers / articles
  -> static route pages
  -> external search index
  -> manifest
```

First test:

```text
build a small TiddlyWiki / article slice as both live and static outputs
compare initial gzip payload and search-index cost
```

### N3 Witness-Budgeted Latent Route

Generative and invertible models should only propose routes:

```text
latent z proposes transform
exact residual repairs
uncertainty decides hold
```

Cost:

```text
C =
  bytes(z)
  + bytes(model_id)
  + bytes(residual)
  + bytes(witness)
  + bytes(decoder)
```

Promotion gate:

```text
C < incumbent
and decoded hash equals source hash
```

### N4 Fractional History Route Scheduler

Use bounded memory for nonstationary corpus regions:

```text
h_t =
  sum_{tau<t, window W}
    K_alpha(t - tau) * residual_tau

route_t =
  R(chunk_t, h_t)
```

Promotion gate:

```text
history bytes counted
and total compressed size improves
```

### N5 Topology Regime Guard

Use semantic topology before tokenbook merges:

```text
beautiful  -> fold
ugly       -> prune
horrible   -> isolate / hold
```

Candidate classifier:

```text
regime =
  classify(invariant_overlap, torsion, round_trip_loss, contradiction)
```

Promotion gate:

```text
fewer bad merges without losing byte wins
```

### N6 Physical Signal Probe Feedback

Borrow the CAD-force-probe habit for compression routes:

```text
route hypothesis
  -> measurable perturbation
  -> negative control
  -> receipt
```

Promotion gate:

```text
positive route beats baseline
and matched negative control fails or underperforms
```

## Unifying Equations

Signal feature vector:

```text
phi_signal(c) =
  [
    H(c),
    tag_density(c),
    DCT_energy(c),
    transient(c),
    autocorr(c),
    cosine_reuse(c)
  ]
```

Route selection:

```text
r* =
  argmin_r LB(r | phi_signal(c), semantic_regime(c), history_state)
```

Exact cost:

```text
C_total =
  bytes(payload)
  + bytes(sidecar)
  + bytes(residual)
  + bytes(decoder)
  + bytes(witness)
  + bytes(container)
```

Promotion:

```text
promote iff
  H(decode(r*)) == H(source)
  and C_total < incumbent
  and failure_rules == none
```

Negative control:

```text
valid_gain iff
  C(candidate) < C(baseline)
  and C(candidate) < C(matched_bad_route)
```

## Immediate Experiment Ladder

```text
E1 wiki8_signal_feature_baseline
  extract per-chunk signal features and compare feature clusters to codec outcomes

E2 route_classifier_without_new_codec
  choose among existing routes only: raw, bz2, zstd, xml_token+bz2, tokenbook+bz2

E3 topology_guard_tokenbook
  apply semantic / topology guards before tokenbook merge

E4 docmd_static_wiki_slice
  export a small tiddler / article slice to static pages plus external index

E5 bounded_history_scheduler
  route stream chunks with finite fractional residual memory
```

## Failure Rules

```text
feature score treated as byte gain                         -> invalid
sidecar / witness / residual / decoder bytes omitted       -> invalid receipt
latent or generative prior used as hidden source payload    -> invalid
semantic merge without round-trip / contradiction check     -> hold
history kernel unbounded or uncounted                       -> fail closed
docmd-style staticization reported as Hutter compression    -> overclaim
negative controls omitted from new route claim              -> weak claim
```

## Claim Boundary

This synthesis proposes testable route-shaping experiments. It is not a Hutter
Prize result, not proof of a new compressor, and not a guarantee that signal
features will improve wiki8.
