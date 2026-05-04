---
project: ResearchStack
domain: axis-04-formalization
secondary_domains:
  - axis-11-geometry
  - axis-01-compression
  - axis-07-attestation
  - axis-03-neural
type: RecoveryManifest
settlement: FORMING
authority: registry
route_signature: recovery/axis-04-formalization/manifest/2026-04-29-hamiltonian-sigma65
status: TEMP_DUMP_WITH_CANONICAL_TARGETS
---

# Recovery Manifest — Hamiltonian Mechanics / Sigma 6.5 / GraphML

## Purpose

This manifest captures recovered work from the April 2026 research-thread recovery path and assigns each recovered artifact to a provisional canonical lane.

The user instruction for this pass was:

```text
auto place where needed, a temp dump if required
```

Therefore this document is both:

1. a canonical recovery map, and
2. a temp dump index for artifacts whose exact final module path still needs verification.

## Recovery groups

### 1. Hamiltonian Lean foundation

Recovered source thread:

```text
AnalysisFoundations-delete.md
HamiltonianMechanics.lean
```

Summary:

- Replaced a misleading stationary-only ODE certificate with real ODE solution definitions using derivative predicates.
- Added Hamiltonian mechanics foundations:
  - phase space
  - canonical symplectic form
  - Hamiltonian vector field
  - Hamilton's equations
  - harmonic oscillator example
  - energy conservation structure
  - Poisson bracket structure
  - flow and Liouville theorem lane
- Reduced proof gaps substantially by proving all elementary results and isolating only genuinely heavy analysis dependencies.

Provisional placement:

```text
tools/lean/Semantics/Semantics/Analysis/Foundations.lean
tools/lean/Semantics/Semantics/Physics/HamiltonianMechanics.lean
```

Fallback / temp dump placement:

```text
docs/recovery/temp/HamiltonianMechanics.recovered.lean.md
```

Status:

```text
RECOVERED_THREAD_CONTEXT
NEEDS_FILE_CONTENT_REHYDRATION
NEEDS_LAKE_BUILD_VERIFICATION
```

### 2. Hamiltonian GraphML proof map

Recovered artifact:

```text
HamiltonianMechanics.graphml
```

Reported structure:

```text
56 nodes
68 directed edges
```

Reported graph regions:

- single-variable analysis
- ODE theory
- phase space
- symplectic structure
- Hamiltonian mechanics
- energy conservation
- Poisson brackets
- flow
- Liouville theorem

Reported edge classes:

- depends-on
- uses
- uses-mathlib
- proves-property-of
- proves
- musical-isomorphism
- equivalent-to
- analogous-to
- requires-existence

Provisional placement:

```text
docs/graphs/HamiltonianMechanics.graphml
```

Fallback / temp dump placement:

```text
docs/recovery/temp/HamiltonianMechanics.graphml.md
```

Status:

```text
GRAPH_REPORTED
NEEDS_RAW_GRAPHML_REGEN_OR_UPLOAD
```

### 3. Sigma 6.5 framework vetting

Recovered source thread:

```text
vetting_report.md
corrected_framework.md
gates_1_4_derivation.md
round2_quality_check.md
```

Summary:

Initial review found major rigor issues, including:

- symplectic sign mismatch
- raw-residual stationarity instead of adjoint formulation
- false L2-to-sup equivalence
- postulated κ-to-Hamiltonian mapping
- scalar-mode tensor type mismatch
- undefined symbols
- underdetermined parameter system
- circular theorem structure

Later passes reframed the work around Sigma 6.5 discipline:

```text
strip semantic labels
prevent models from importing domain assumptions
separate type/math bugs from label-induced objections
```

Recovered classification:

```text
true math/type bugs      -> must fix
label-induced objections -> deflected by stripped-label protocol
open research gates      -> do not pretend closed unless derivation exists
```

Provisional placement:

```text
docs/rigor/vetting_report.md
docs/rigor/corrected_framework.md
docs/rigor/gates_1_4_derivation.md
docs/rigor/round2_quality_check.md
```

Fallback / temp dump placement:

```text
docs/recovery/temp/sigma65_framework_thread.md
```

Status:

```text
RECOVERED_THREAD_CONTEXT
NEEDS_ARTIFACT_REHYDRATION
NEEDS_CANONICALITY_REVIEW
```

### 4. Sigma 6.5 stripped-label rigor protocol

Recovered principle:

```text
labels are stripped so LLM models cannot inject assumptions about rigor
```

Canonical interpretation:

A framework candidate should be tested first as a formal symbolic object, with semantic labels suppressed or treated as comments. Objections should be classified as:

```text
1. type/formal bug
2. logic bug
3. dimensional/semantic objection
4. label-induced assumption
5. genuine open problem
```

Provisional placement:

```text
docs/rigor/SIGMA_6_5_STRIPPED_LABEL_PROTOCOL.md
```

Status:

```text
NEEDS_SPEC_EXTRACTION
HIGH_VALUE
```

## Immediate action queue

### P0 — preserve content

- [ ] Rehydrate `HamiltonianMechanics.lean` from the recovered thread or upload.
- [ ] Rehydrate `HamiltonianMechanics.graphml` or regenerate from the Lean file.
- [ ] Rehydrate `corrected_framework.md`.
- [ ] Rehydrate `gates_1_4_derivation.md`.
- [ ] Rehydrate `round2_quality_check.md`.
- [ ] Rehydrate `vetting_report.md`.

### P1 — canonicalize

- [ ] Move Hamiltonian Lean into atomic formalization path.
- [ ] Run Lake build on recovered Lean.
- [ ] Store GraphML in `docs/graphs/`.
- [ ] Promote Sigma 6.5 stripped-label protocol into a standalone rigor spec.
- [ ] Link vetting report to corrected framework and gate derivation.

### P2 — integrate with ontology

- [ ] Map Hamiltonian mechanics artifacts into atom / law / molecule / field ontology.
- [ ] Add graph topology export record for Hamiltonian proof map.
- [ ] Add FAMM route outcome after build verification.
- [ ] Add issue for remaining Picard-Lindelöf / Liouville proof obligations if any remain after actual build.

## Atom / physics / molecule placement

| Artifact | Ontology role | Notes |
|---|---|---|
| `PhaseSpace` | atom container | `(q,p)` state object |
| `canonicalSymplecticForm` | interaction law | governs allowed Hamiltonian flow geometry |
| `HamiltonianVectorField` | force law / vector field | maps scalar energy function to dynamics |
| `HamiltonsEquations` | particle-physics law | coordinate form of dynamics |
| `PoissonBracket` | interaction algebra | conserved quantities / commutator-like structure |
| `LiouvilleTheorem` | conservation certificate | symplectic preservation under flow |
| GraphML map | detector / proof topology | dependency trace of formal object |
| Sigma 6.5 protocol | rigor gate | strips labels to prevent assumption injection |

## Safety / rigor rule

Recovered artifacts must not be promoted merely because a previous agent reported success.

Promotion requires:

```text
raw artifact present
build or verification evidence present
claim-status attached
open proof obligations listed
canonical target path assigned
```

## Current status

```text
TEMP_DUMP_WITH_CANONICAL_TARGETS
```

This manifest is safe to commit because it preserves the recovery state without claiming that the recovered artifacts have already been rebuilt, verified, or promoted.
