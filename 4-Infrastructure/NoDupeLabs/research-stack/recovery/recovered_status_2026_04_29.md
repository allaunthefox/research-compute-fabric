# Recovered Research Stack Status Snapshot — 2026-04-29

## Status

```yaml
status: recovered_from_connector_state
source: GitHub connector + uploaded-file context + current chat reconstruction
scope: last major Research Stack work session
```

## Current spine

The recovered session was not one isolated thread. It moved through six connected workstreams:

```text
1. Measurement-standard registry
2. Semantic Number Pattern Search
3. Chandelier / genus-3 / pulsar gradient models
4. Multiscale pulsar marble-jar simulation + validator
5. Abstract-CoT equation integration
6. Doppler-aware gradient instrumentation
```

The unifying idea is:

```text
artifact / equation / visual intuition / physical model
→ bounded source authority
→ normalized representation
→ trace / invariant / validator
→ HOLD unless gated
→ forest-map route update
```

## 1. Measurement-standard registry

Recovered commits:

```text
6b00cb2 Add SI 2019 exact constants pack
6cb4a2 Add extended physical constants foundation pack
c714fe6 Add Research Stack reweight policy v0
5c7d811 Add measurement standards source catalog v0
4c9be60 Add measurement registry operating doctrine
f85047c Add constants registry builder scaffold
7b1e7a9 Add measurement source adapter registry scaffold
8a2c1f1 Wire measurement adapters into constants registry builder
```

Recovered files:

```text
research-stack/constants/si_2019_exact_constants_v0.json
research-stack/constants/physical_constants_foundation_v0.json
research-stack/weights/research_stack_weight_policy_v0.json
research-stack/constants/measurement_standards_source_catalog_v0.json
research-stack/constants/README_MEASUREMENT_REGISTRY.md
src/plumbing/constants_registry_builder.ts
src/plumbing/measurement_source_adapters.ts
```

Core rule:

```text
A number is not knowledge until it carries:
source → unit → exactness → uncertainty → conditions → authority → allowed use
```

Registry target:

```text
BIPM / SI / CODATA / NIST
national metrology institutes
chemistry / thermophysical / materials / crystallography
astronomy / geodesy / time / coordinate registries
earth / atmosphere / ocean / climate
particle / nuclear / radiation
engineering / industrial standards
biomedical / clinical measurement standards
```

Boundary:

```text
full = federated standard-source catalog + adapters
not = hand-entered constants pretending to be a world database
```

## 2. Semantic Number Pattern Search

Recovered commit:

```text
1570317 Add Semantic Number Pattern Search pipeline
```

Recovered file:

```text
src/plumbing/semantic_number_pattern_search.ts
```

Expected run:

```bash
npx tsx src/plumbing/semantic_number_pattern_search.ts
```

Expected outputs:

```text
research-stack/constants/constants_registry_v0.json
research-stack/semantic-number-patterns/numeric_motifs.json
research-stack/semantic-number-patterns/numeric_pattern_roads.json
research-stack/semantic-number-patterns/numeric_torsion_candidates.json
research-stack/semantic-number-patterns/false_attractor_report.json
```

Core behavior:

```text
constants registry
+ equation packs
→ numeric motifs
→ weighted pattern roads
→ torsion candidates
→ false-attractor report
```

Rule:

```text
Every result remains HOLD.
No numeric motif, exact constant, or shared pattern can become a basin without gates.
```

## 3. Chandelier / genus-3 / blue-red shift gradient modeling

Recovered commits:

```text
0e2fc47 Add chandelier genus-3 blueshift model note
bd50665 Add chandelier genus-3 descent simulation
cb22bf0 Add pulsar genus-3 two-component model
4e85ef8 Add pulsar genus-3 two-component simulation
```

Recovered files:

```text
research-stack/models/chandelier_genus3_blueshift_model_v0.md
scripts/chandelier_genus3_descent.py
research-stack/models/pulsar_genus3_two_component_model_v0.md
scripts/pulsar_genus3_two_component.py
```

Core correction:

```text
There is no canonical vertical in n-space.
"Down" = increasing torsion / decreasing accessible phase volume / decreasing free energy.
```

Physical mapping:

```text
superfluid neutron vortices = chandelier filaments
crustal lattice = rigid basin rim / pinning substrate
vortex unpinning avalanches = phase-transition flashes
magnetic dipole braking = damping / slow energy bleed
glitch spin-up = angular momentum redistribution flash
relativistic beaming = blue/red shift trace
genus-3 = three reduced circulation routes
```

## 4. Multiscale pulsar marble-jar simulation and validator

Recovered commits:

```text
ba6132d Add multiscale pulsar marble jar simulation
45cdc68 Add validator for multiscale pulsar marble jar simulation
```

Recovered files:

```text
scripts/pulsar_marble_jar_multiscale.py
scripts/validate_pulsar_marble_jar_multiscale.py
```

Run simulation:

```bash
python3 scripts/pulsar_marble_jar_multiscale.py
```

Run validator:

```bash
python3 scripts/validate_pulsar_marble_jar_multiscale.py
```

Expected outputs:

```text
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_spin_down.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_lag_torsion_phase.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_angular_momentum_residual.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_genus3_routes.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_doppler_vortex.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_glitch_sizes.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/multiscale_waiting_times.png
research-stack/models/pulsar_marble_jar_multiscale_outputs/pulsar_marble_jar_multiscale_report.json
research-stack/models/pulsar_marble_jar_multiscale_outputs/pulsar_marble_jar_multiscale_traces.csv
research-stack/models/pulsar_marble_jar_multiscale_outputs/pulsar_marble_jar_multiscale_validation.json
```

Critical fix:

```text
old failure: one arbitrary dt for all physics
new model: cruise years, glitch rise seconds, recovery days
```

Validator checks:

```text
finite traces
time-scale separation
lag accumulation
glitch crust spin-up / superfluid spin-down
lag reduction
angular momentum conservation residual
torsion vs accessible phase volume anticorrelation
genus-3 route normalization and drift
small non-explosive fractional spin jumps
```

## 5. Abstract-CoT equation integration

Recovered commits:

```text
e757a36 Add Abstract-CoT integration manifest
614f89b Add Abstract-CoT equation pack
d3d319b Add Abstract-CoT entropy formalization review
64f639b Add MATH_MODEL_MAP schema normalizer
```

Recovered files:

```text
research-stack/models/abstract_cot_integration_v0.md
research-stack/equation-packs/abstract_cot_equation_pack_v0.json
research-stack/formal/abstract_cot_entropy_review_v0.md
scripts/normalize_math_model_map.py
research-stack/models/MATH_MODEL_MAP.abstract_cot.normalized.tsv
```

Six Abstract-CoT equations recovered:

```text
Abstract_CoT_Marginal_Likelihood
Abstract_CoT_Constrained_Decoding
Abstract_CoT_Information_Bottleneck
Abstract_CoT_Power_Law_Distribution
Abstract_CoT_GRPO_Advantage
Abstract_CoT_Compression_Ratio
```

Important Lean/formal boundary:

```text
current mutualInformation / informationBottleneck additions are Q16_16 proxies
not proof-complete mutual information formalization
true MI requires joint distribution + marginals + Markov-chain assumption C → Z_abs → Y
```

Important TSV boundary:

```text
uploaded Abstract_CoT rows were content-present but schema-misaligned
normalizer expands compact 10-column rows into canonical 12-column rows
```

## 6. Doppler-aware gradient instrumentation

Recovered commit:

```text
e038688 Add Doppler gradient integration note
```

Recovered file:

```text
research-stack/gradient-models/doppler_gradient_integration_v0.md
```

Core requirement:

```text
Gradient models need explicit blue-shift / red-shift dynamics.
```

Minimal proxy:

```text
β_t = <v_t, n_t> / c_eff
shift_t = sqrt((1 + β_t) / (1 - β_t))
shift*_t = shift_t · (1 + κ τ_t)
```

Interpretation:

```text
shift_t > 1  → blue-shifted descent / compression / impact approach
shift_t < 1  → red-shifted retreat / relaxation / diffusion away
shift_t ≈ 1  → neutral drift
```

Required trace fields:

```text
time
state_id
basin_id
energy
energy_delta
gradient_norm
velocity_norm
torsion_proxy
accessible_phase_volume
beta_eff
doppler_shift
red_blue_label
flash_event
phase_boundary_id
route_weight_before
route_weight_after
```

## Current best next actions

### A. Execute generators locally

```bash
npx tsx src/plumbing/constants_registry_builder.ts
npx tsx src/plumbing/semantic_number_pattern_search.ts
python3 scripts/pulsar_marble_jar_multiscale.py
python3 scripts/validate_pulsar_marble_jar_multiscale.py
```

### B. Add Doppler trace to existing simulations

Patch:

```text
scripts/chandelier_genus3_descent.py
scripts/pulsar_genus3_two_component.py
scripts/pulsar_marble_jar_multiscale.py
```

so they emit:

```text
beta_eff
doppler_shift
red_blue_label
flash_event
phase_boundary_id
```

### C. Route Abstract-CoT through Semantic Number Pattern Search

Add `abstract_cot_equation_pack_v0.json` to the default equation pack list or run it as an explicit input.

### D. Keep solar-system region quarantined

Recovered rule remains:

```text
solar-system observations are not trusted as validation partners until separately verified
```

## Recovered state in one sentence

The project now has a measurement-authority backbone, numeric motif router, multiscale torsion/phase simulation family, Abstract-CoT compression bridge, and a new Doppler-aware gradient trace requirement — all still gated as HOLD unless validated by source, invariant, compile, or proof checks.
