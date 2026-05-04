# Compression Mechanics Execution Plan

This plan defines the work needed to verify compression approaches through a
rigorous chain:

1. informational compression evidence
2. thermodynamic lower bounds
3. physically admissible substrate witnesses
4. end-to-end bridge theorems

The plan is organized into phases, steps, and sub-steps with explicit completion
metrics.

## Phase 0: Scope Lock

Goal:

- freeze the theorem target so implementation work does not drift back into
  unsupported chemistry claims

### Step 0.1: Lock the proof target

Sub-steps:

1. State the target theorem family in one sentence.
2. State what is explicitly out of scope.
3. Bind the target to the Nature-family source pack in
   `NATURE_RIGOR_PREP.md`.

Completion metrics:

- one canonical statement of the goal exists in repo docs
- one explicit out-of-scope list exists in repo docs
- every later theorem module can be mapped to one section of the source pack

### Step 0.2: Lock the minimal variable set

Sub-steps:

1. Define the minimal quantities that every later phase may use.
2. Reject unsupported quantities from the proof core.
3. Separate proof-layer quantities from approximation-layer quantities.

Completion metrics:

- proof core variables list is finite and documented
- no theorem in later phases depends on free-form strings or vague descriptors
- no step assumes atomic weight alone can determine structure or admissibility

Suggested proof-core variables:

- source trace
- model trace
- block cost
- accuracy witness
- erased-information witness
- nonequilibrium cost
- substrate witness
- admissibility predicate

## Phase 1: Informational Core

Goal:

- prove that the compression side is mathematically well-defined before any
  physics is attached

### Step 1.1: Define compression evidence semantics

Sub-steps:

1. Create `Semantics.CompressionEvidence`.
2. Define a finite alphabet type.
3. Define block, trace, model state, and cost witness types.
4. Define deterministic scoring semantics.

Completion metrics:

- Lean file exists under `0-Core-Formalism/lean/Semantics/Semantics/`
- every new `def` has either an `#eval` witness or theorem in the same file
- no `Float` appears in the new core module
- no open string matching appears in core decisions

### Step 1.2: Define code-length / accuracy objects

Sub-steps:

1. Define code-length witness in Q16.16-compatible form.
2. Define accuracy witness for reconstruction or prediction quality.
3. Define contextual and flat model interfaces.

Completion metrics:

- code-length object is typed and total
- accuracy witness is typed and total
- contextual and flat models can be compared on the same trace

### Step 1.3: Prove first informational theorem

Sub-steps:

1. Formalize deterministic conditional source case.
2. Prove a matching contextual model is no worse than a flat model.
3. Add one concrete `#eval` example demonstrating the bound.

Completion metrics:

- theorem compiles without `sorry`
- theorem statement is independent of any physics module
- at least one example trace evaluates to the expected inequality witness

Exit criteria for Phase 1:

- `Semantics.CompressionEvidence` builds in isolation
- one nontrivial compression theorem is proven
- the theorem uses only informational quantities

## Phase 2: Thermodynamic Layer

Goal:

- connect irreversible information change to a rigorous physical lower bound

### Step 2.1: Define thermodynamic primitives

Sub-steps:

1. Create `Semantics.LandauerCompression`.
2. Define erased-information witness.
3. Define nonequilibrium cost object.
4. Define lower-bound function for irreversible steps.

Completion metrics:

- Lean file exists and compiles in isolation
- every primitive has a documented physical meaning
- no theorem depends on unformalized external numerics

### Step 2.2: Bind informational state change to thermodynamic cost

Sub-steps:

1. Define irreversible update predicate.
2. Define mapping from compression step to erased-information witness.
3. Define lower-bound theorem target.

Completion metrics:

- there is a total function from compression step to thermodynamic witness
- irreversible and reversible cases are distinguished by a typed predicate
- at least one simple theorem covers the nonzero irreversible case

### Step 2.3: Prove the first physics bridge theorem

Sub-steps:

1. Prove positive erased-information witness implies nonzero lower bound.
2. Add example witnesses for zero and nonzero cases.
3. Document the theorem's exact scope and limitations.

Completion metrics:

- theorem compiles without `sorry`
- theorem is stated in terms of the defined typed quantities only
- example witnesses distinguish reversible from irreversible cases

Exit criteria for Phase 2:

- `Semantics.LandauerCompression` builds in isolation
- one theorem links compression evidence to a thermodynamic lower bound
- the repo now has a truthful information -> physics bridge

## Phase 3: Materials / Defect Witness Layer

Goal:

- define a physically meaningful substrate witness that can support or reject a
  proposed compression process

### Step 3.1: Define local physical witness objects

Sub-steps:

1. Create `Semantics.DefectMechanics`.
2. Define a finite substrate or neighborhood type.
3. Define local descriptors such as vacancy or charge witness.
4. Define a transport / dissipation witness.

Completion metrics:

- Lean file exists and compiles in isolation
- descriptors are finite, typed, and enumerable where needed
- no descriptor is represented by an open-ended string in core logic

### Step 3.2: Define admissibility predicates

Sub-steps:

1. Define heat-dissipation admissibility.
2. Define defect-energy admissibility.
3. Define transport-regime admissibility.

Completion metrics:

- each predicate is total
- each predicate has one `#eval` or theorem witness
- predicates can be combined without ambiguity into a single admissibility view

### Step 3.3: Prove the first substrate theorem

Sub-steps:

1. Define a minimal substrate witness record.
2. Prove that a substrate satisfying the threshold conditions is admissible.
3. Add one positive and one negative example witness.

Completion metrics:

- theorem compiles without `sorry`
- positive witness evaluates to admissible
- negative witness evaluates to not admissible

Exit criteria for Phase 3:

- `Semantics.DefectMechanics` builds in isolation
- one theorem certifies substrate admissibility
- local physical descriptors are separated from learned surrogate claims

## Phase 4: Compression <-> Mechanics Bridge

Goal:

- prove that a compression step is physically admissible on a specified
  substrate witness

### Step 4.1: Define bridge objects

Sub-steps:

1. Create `Semantics.CompressionMechanicsBridge`.
2. Import the informational, thermodynamic, and substrate layers.
3. Define a bridge record carrying all required witnesses.

Completion metrics:

- bridge record contains no undocumented fields
- every bridge field comes from a previous phase
- no direct dependency on approximation-layer ML outputs exists in the theorem core

### Step 4.2: Define admissible compression step

Sub-steps:

1. Define the predicate that a compression step is physically admissible.
2. Separate proof obligations for informational validity, lower-bound validity,
   and substrate validity.
3. Add a helper theorem for assembling the three obligations.

Completion metrics:

- predicate is total
- obligations are decomposed into named lemmas
- at least one helper theorem reduces final theorem complexity

### Step 4.3: Prove the bridge theorem

Sub-steps:

1. Prove that a compression step with valid informational witness, valid
   thermodynamic lower bound, and admissible substrate is physically admissible.
2. Add one end-to-end worked example.
3. Document what this theorem does not prove.

Completion metrics:

- theorem compiles without `sorry`
- one complete end-to-end example evaluates successfully
- limitations are written explicitly in the module or companion doc

Exit criteria for Phase 4:

- repo contains one honest end-to-end compression-to-physics theorem
- theorem depends only on proven or explicitly witnessed inputs
- no unsupported chemistry claims remain in the proof path

## Phase 5: Approximation / Surrogate Layer

Goal:

- allow ML or symbolic-regression accelerators to be used without confusing them
  with the proof layer

### Step 5.1: Define approximation boundary

Sub-steps:

1. Document that surrogates are extraction targets or numerical witnesses.
2. Define accepted surrogate outputs as data artifacts, not axioms.
3. Define a verification boundary for importing surrogate results.

Completion metrics:

- documentation explicitly separates proof from surrogate
- surrogate artifacts are never imported as trusted theorems
- each imported surrogate result must attach to a typed witness object

### Step 5.2: Add one surrogate-backed witness path

Sub-steps:

1. Choose one descriptor class such as vacancy witness.
2. Define how an external predictor may populate it.
3. Prove that the bridge theorem only uses the populated witness, not the model internals.

Completion metrics:

- surrogate-backed witness path exists without changing proof-layer theorems
- theorem statements remain independent of the surrogate architecture
- repo documentation states what is proved and what is estimated

Exit criteria for Phase 5:

- the project can use practical predictors without collapsing rigor
- proof-layer semantics remain stable if the surrogate changes

## Phase 6: Integration and Validation

Goal:

- integrate the new modules into the repo and validate them against the repo's
  operating rules

### Step 6.1: Local build validation

Sub-steps:

1. Build each new module in isolation.
2. Record any dependencies that prevent integration.
3. Fix isolated issues before touching broader imports.

Completion metrics:

- each new module builds individually
- no new module contains `sorry`
- no new module introduces new dependencies

### Step 6.2: Repo integration

Sub-steps:

1. Add imports to the appropriate aggregate files only after isolated success.
2. Re-run `lake build`.
3. Separate pre-existing failures from new failures.

Completion metrics:

- import graph is minimal
- any build failures introduced by integration are attributable and fixed
- no unrelated files are changed during integration

### Step 6.3: Documentation closure

Sub-steps:

1. Update the rigor prep note with implemented modules.
2. Add a short theorem inventory.
3. Record any deferred work explicitly.

Completion metrics:

- theorem inventory exists in repo docs
- every implemented module has a corresponding documentation entry
- deferred items are listed as explicit future work, not hidden gaps

Exit criteria for Phase 6:

- new modules are integrated cleanly
- documentation and code agree
- completion can be reported against explicit metrics

## Overall Completion Metrics

The program is complete when all of the following are true:

1. `Semantics.CompressionEvidence` exists, builds, and contains at least one
   nontrivial informational theorem.
2. `Semantics.LandauerCompression` exists, builds, and contains at least one
   theorem linking erased-information witness to nonzero lower bound.
3. `Semantics.DefectMechanics` exists, builds, and contains at least one
   substrate admissibility theorem.
4. `Semantics.CompressionMechanicsBridge` exists, builds, and contains one
   end-to-end admissibility theorem.
5. Every new theorem is free of `sorry`.
6. Every new `def` has an `#eval` or theorem witness.
7. No new core module uses `Float`.
8. No new core decision procedure uses open string matching.
9. No new dependencies are added.
10. The final documentation states clearly what is proved, what is witnessed, and
    what is only approximated.

## Reporting Template

Use this template at the end of each implementation checkpoint:

- Phase completed:
- Steps completed:
- Files added or changed:
- Theorems added:
- `#eval` witnesses added:
- Isolated build status:
- Full `lake build` status:
- Deferred items:

