# Mass-Number Lens MindVisualizer Adapter

**Status:** ARCHITECTURE_BRIDGE_DRAFT  
**Source pattern:** `Pixedar/MindVisualizer`  
**Target stack:** OTOM / Mass-Number Lens / Admissibility Forest  

## Purpose

This document adapts the interaction architecture of `MindVisualizer` into the Mass-Number Lens framework.

`MindVisualizer` demonstrates a useful pattern:

```text
connectivity substrate
+ learned manifold
+ continuous flow field
+ user probe
+ trajectory capture
+ perturbation propagation
+ LLM interpretation
```

The Mass-Number Lens generalizes that pattern away from brain ROIs and into arbitrary invariant fields:

```text
raw or residual field
+ invariant-energy unfolding
+ n-space shape manifold
+ Mass Number Foci
+ admissibility forest
+ semantic adapter explanation
```

## Upstream provenance / CFF

A `CITATION.cff` file was checked for at:

```text
Pixedar/MindVisualizer@master:CITATION.cff
```

No upstream `CITATION.cff` was available at the time this adapter was written. The following CFF-style provenance block is therefore a local citation receipt derived from the upstream repository metadata and README. It must be replaced by the upstream project's own `CITATION.cff` if one is later published.

```yaml
cff-version: 1.2.0
message: "If you use this architecture bridge, cite the upstream MindVisualizer repository and its listed data sources."
title: "MindVisualizer"
authors:
  - name: "Pixedar"
type: software
repository-code: "https://github.com/Pixedar/MindVisualizer"
abstract: >-
  A tool for exploring how information may move through the brain at rest,
  using a continuous flow model, raw rDCIM effective-connectivity graph,
  and ROI flow mode through a learned resting-state manifold.
keywords:
  - brain visualization
  - resting-state fMRI
  - rDCIM
  - effective connectivity
  - manifold flow
  - probe trajectory
  - LLM interpretation
license: "Research use; see upstream repository and source data licenses."
references:
  - type: data
    title: "Continuous, Tract-Constrained Directional Vector Fields from rDCM Effective Connectivity Using Mixture Density Networks"
    repository-code: "https://zenodo.org/records/18200415"
  - type: article
    title: "Local-Global Parcellation of the Human Cerebral Cortex from Intrinsic Functional Connectivity MRI"
    authors:
      - name: "Schaefer, A. et al."
    year: 2018
    journal: "Cerebral Cortex"
  - type: article
    title: "Regression dynamic causal modeling for resting-state fMRI"
    authors:
      - name: "Frässle, S. et al."
    year: 2021
    journal: "Human Brain Mapping"
  - type: article
    title: "An Open MRI Dataset For Multiscale Neuroscience"
    authors:
      - name: "Royer, J. et al."
    year: 2022
    journal: "Scientific Data"
  - type: article
    title: "The WU-Minn Human Connectome Project: An overview"
    authors:
      - name: "Van Essen, D. C. et al."
    year: 2013
    journal: "NeuroImage"
  - type: article
    title: "Population-based tract-to-region connectome of the human brain"
    authors:
      - name: "Yeh, F.-C. et al."
    year: 2022
    journal: "Nature Communications"
```

Provenance guardrail:

```text
MindVisualizer is an upstream architecture reference.
This adapter does not claim ownership of its code, data, preprint, assets, or neuroscience model.
Any derivative implementation must preserve upstream attribution and source-data license checks.
```

## Core adaptation

The adapter turns a raw field into an explorable manifold surface.

```text
ObservedField
  -> residual extraction
  -> deterministic stochastic coarse-graining
  -> invariant-energy decomposition
  -> n-space shape field
  -> probe trajectory
  -> foci detection
  -> closure classification
  -> semantic explanation
```

## Mapping table

| MindVisualizer concept | Mass-Number Lens concept |
|---|---|
| anatomical / ROI graph | raw graph substrate / candidate field |
| rDCIM effective connectivity | directed compatibility field `K(x,y)` |
| continuous MDN flow field | deterministic stochastic coarse-grained flow |
| learned resting-state manifold | n-space invariant shape manifold |
| probe placement | coordinate witness injection |
| probe trajectory | witness path through admissibility field |
| ROI activation delta | focus transition / basin shift |
| perturbation propagation | residual-field response |
| LLM path interpretation | semantic adapter, not validator |
| RAG knowledge base | domain-local interpretive context |

## Adapter components

### 1. Field substrate

The substrate is a typed source field:

```text
FieldSubstrate :=
  RawSignal
  | ResidualNoiseField
  | ConnectivityGraph
  | SpectralEnergyField
  | BrownianEnergyField
  | VibrationModeField
  | RecurrenceField
```

The substrate may be a graph, continuous vector field, time series, spectrogram, point cloud, or residual stream.

### 2. Coarse-graining operator

```text
CoarseGrain(field, basis, scale)
  -> CoarseField
```

Doctrine:

```text
Deterministic stochastic coarse-graining is signal,
just not signal aligned in the original coordinate frame.
```

A residual component is promoted only if coarse-graining produces stable invariant foci.

### 3. Probe

A probe is a witness injection into the field.

```text
Probe := {
  probe_id,
  initial_position,
  projection_context,
  integration_step,
  max_steps,
  stopping_rule
}
```

The probe follows the unfolded field:

```text
z_{t+1} = z_t + step * Flow(z_t)
```

or in stochastic form:

```text
dz = Flow(z, t) dt + sigma(z,t) dW_t
```

### 4. Trajectory witness

```text
TrajectoryWitness := {
  path_points,
  velocity_profile,
  local_curvature,
  spectral_energy_along_path,
  Brownian_energy_along_path,
  recurrence_score_along_path,
  mode_persistence_along_path,
  residual_risk_along_path
}
```

A trajectory is not a proof. It is evidence that may support or weaken a focus hypothesis.

### 5. Mass Number Focus detector

A focus is a stable concentration basin in n-space.

```text
FocusCandidate := {
  focus_id,
  basin_center,
  basin_radius,
  incoming_probe_count,
  invariant_energy_signature,
  mass_number,
  residual_risk,
  closure_status
}
```

A focus is promoted only if it persists under:

```text
projection changes
scale changes
probe initializations
decomposition methods
shuffle / null controls
residual audits
```

### 6. Admissibility forest assignment

```text
leaf      = coordinate witness / spike / threshold contact / path sample
atom      = local invariant pattern
focus     = stable concentration basin
tree      = shape-family organized around one or more foci
forest    = competing admissibility geometry over all foci and residuals
```

Assignment rule:

```text
Raw points do not receive primary mass.
Invariant atoms and foci receive primary mass.
Points and probe samples receive witness mass through membership.
```

### 7. Semantic adapter

The LLM explanation layer is an interpreter only.

```text
LLMExplanation := SemanticAdapter(TrajectoryWitness, FocusCandidate, DomainContext)
```

Guardrail:

```text
LLM explanations are not validators.
They translate typed evidence into human-readable hypotheses.
```

## Runtime loop

```text
1. Load field substrate.
2. Select projection and scale.
3. Unfold field into invariant-energy channels.
4. Place one or more probes.
5. Integrate probe paths through the field.
6. Extract trajectory witnesses.
7. Detect foci and residual branches.
8. Assign mass-number scores.
9. Update stochastic conservation ledger.
10. Classify every component as:
    - aligned signal
    - unaligned/coarse-grained signal
    - promoted focus
    - candidate focus
    - typed residual
    - category-rescued branch
    - quarantine
    - rejection
11. Produce semantic explanation with provenance and guardrails.
```

## Mass-number equations

Focus mass:

```text
M(focus)
=
  invariant_persistence
  * cross_method_agreement
  * compression_gain
  * trajectory_convergence
  /
  residual_risk
```

Witness mass:

```text
M(point | focus)
= M(focus) * witness_strength(point, focus)
```

Trajectory mass:

```text
M(path)
= sum_t M(point_t | focus) - accumulated_residual_risk(path)
```

## Stochastic conservation ledger

```text
M_before_unfold
≈ M_promoted_foci
+ M_candidate_foci
+ M_typed_residuals
+ M_category_misplaced
+ M_quarantined
+ M_rejected
+ epsilon_loss
```

with:

```text
epsilon_loss <= tolerance
```

No mass may disappear into generic `noise`.

## UI controls inspired by MindVisualizer

```text
G          place probe
Shift+G    freeze probe and explain trajectory
C          clear probes
B          toggle branching mode
+/-        adjust integration speed or coarse-graining scale
S          initialize field state
Shift+S    propagate state changes through probe path
P          propose perturbation at selected focus or atom
Shift+P    propagate perturbation through admissibility graph
```

## Minimal implementation target

```text
MassNumberLensViewer
  - loads scalar/vector/graph fields
  - computes spectral, Brownian, recurrence, and vibration channels
  - renders n-space projection
  - supports probe placement
  - integrates probe paths
  - detects foci
  - emits JSON witness reports
```

Suggested report schema:

```json
{
  "field_id": "...",
  "projection_context": "...",
  "probe_id": "...",
  "trajectory": [],
  "focus_candidates": [],
  "residual_branches": [],
  "mass_ledger": {},
  "closure_status": "open|closed|quarantined",
  "semantic_explanation": "..."
}
```

## Definition of Done

The adapter is successful when a user can:

```text
1. load an unknown or residual field,
2. unfold it into invariant-energy channels,
3. place a probe in the n-space projection,
4. watch the probe follow the coarse-grained flow,
5. detect whether the path converges to a Mass Number Focus,
6. inspect the stochastic conservation ledger,
7. receive an LLM explanation clearly marked as interpretation, not validation.
```

## Guardrails

```text
The flow field is a model-based projection, not ground truth.
Probe trajectories are witnesses, not proofs.
Foci are candidate invariant basins until controls confirm stability.
LLM explanations are semantic adapters, not validators.
Residuals must be typed; they may not be erased as generic noise.
Upstream MindVisualizer attribution and source data provenance must be preserved.
```

## Short doctrine

```text
The probe makes the lens tactile.
The trajectory makes the residual visible.
The focus makes the mass local.
The ledger makes closure auditable.
```
