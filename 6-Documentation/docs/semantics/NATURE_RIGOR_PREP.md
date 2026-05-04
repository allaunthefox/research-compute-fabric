# Nature Rigor Prep

This note collects Nature-family sources that can make the compression-to-physics
program more rigorous.

The target is not:

- atomic weights -> chemistry -> compression proof

The target is:

- information-processing task
- accuracy / code-length witness
- thermodynamic lower bound
- atomistic or materials witness for physical realizability

## Core Stack

### 1. Information -> Thermodynamics

These papers support the claim that information processing has a rigorous physical
cost and that accuracy can be bounded against nonequilibrium resources.

1. Experimental verification of Landauer's principle linking information and thermodynamics
   URL: https://www.nature.com/articles/nature10872
   Use:
   - canonical Landauer lower bound
   - irreversible erasure implies dissipated heat
   - baseline physical interpretation for compression / reset / overwrite steps

2. Experimentally probing Landauer's principle in the quantum many-body regime
   URL: https://www.nature.com/articles/s41567-025-02930-9
   Use:
   - extension of Landauer reasoning beyond one-bit toy models
   - mutual information and relative entropy language for many-body settings
   - useful if compression traces are treated as structured out-of-equilibrium processes

3. The nonequilibrium cost of accurate information processing
   URL: https://www.nature.com/articles/s41467-022-34541-w
   Use:
   - strongest mathematical upgrade for the repo
   - task accuracy formalism
   - explicit nonequilibrium cost / accuracy inequality
   - reverse-entropy concept for time-reversed task bounds

4. Experimentally achieving minimal dissipation via thermodynamically optimal transport
   URL: https://www.nature.com/articles/s41467-025-66519-9
   Use:
   - optimal transport framing for dissipation-minimizing protocols
   - good candidate reference for "best physically admissible implementation"

### 2. Atomistic / Materials Witness Layer

These papers support the claim that physically serious substrate arguments must be
phrased in terms of energies, descriptors, transport, defects, and relaxation, not
 just elemental masses.

1. Constructing machine learning interatomic potentials with minimum amount of ab initio data
   URL: https://www.nature.com/articles/s41524-026-02023-y
   Use:
   - correct modern chain: DFT -> MLIP -> MD
   - fine-tuned foundation potential plus distilled surrogate
   - useful for separating truth layer from acceleration layer

2. Framework to completely bypass expensive DFT calculations via graph neural networks for vacancy formation energy predictions in FCC high entropy alloys
   URL: https://www.nature.com/articles/s41524-026-02037-6
   Use:
   - vacancy formation energy as a concrete physically meaningful witness
   - Bader charge as local electronic descriptor
   - better bridge variables than atomic weight tables

3. Physically interpretable interatomic potentials via symbolic regression and reinforcement learning
   URL: https://www.nature.com/articles/s41524-025-01952-4
   Use:
   - interpretable potentials instead of black-box surrogates
   - symbolic-regression angle is closer to a proof-oriented stack
   - suggests a route from DFT-compatible semantics to explicit equations

4. Training data selection for accuracy and transferability of interatomic potentials
   URL: https://www.nature.com/articles/s41524-022-00872-x
   Use:
   - rigorous language for transferability failure
   - supports "approximation layer is not proof layer"
   - useful if learned surrogates are introduced later as extraction targets

5. Prediction of thermally driven quasi-1D superionic states in carbon hydride under giant planetary conditions
   URL: https://www.nature.com/articles/s41467-026-70603-z
   Local PDF: `/home/allaun/Downloads/data/Downloads_from_internet/s41467-026-70603-z_reference.pdf`
   Use:
   - anisotropic transport and phase-dependent conduction
   - first-principles + MLIP reasoning under extreme conditions
   - useful as a transport-regime witness, not as a compression theorem

### 3. Information Flow Metrics

1. Transfer Entropy and Transient Limits of Computation
   URL: https://www.nature.com/articles/srep05394
   Use:
   - transfer entropy as a possible dependency-structure witness
   - candidate metric for when compression exploits real predictive structure

## What These Papers Justify

They justify a theorem program shaped like:

1. A compression task has an informational score or cost.
2. A target accuracy or code-length reduction implies a minimum nonequilibrium cost.
3. A proposed physical substrate must satisfy an admissibility condition to realize that cost.
4. Optional surrogate layers can accelerate the numerical witness, but do not become the proof.

They do not justify:

- using atomic weight alone to derive molecular structure
- claiming a handwritten DAG is a first-principles proof
- treating ML surrogate outputs as formal truth

## Lean Targets

The minimum useful Lean modules suggested by the papers are:

1. `Semantics.CompressionEvidence`
   Purpose:
   - formalize block cost, accuracy, and conditional structure
   - keep this layer purely informational

2. `Semantics.LandauerCompression`
   Purpose:
   - connect irreversible information change to a thermodynamic lower bound
   - encode nonequilibrium cost and accuracy tradeoffs

3. `Semantics.DefectMechanics`
   Purpose:
   - define local physical descriptors such as vacancy cost or charge witness
   - avoid direct black-box potentials in the proof layer

4. `Semantics.CompressionMechanicsBridge`
   Purpose:
   - prove that a compression trace is physically admissible on a given substrate witness

## Candidate Theorems

These are the most defensible theorem shapes to aim for first.

1. Deterministic-context improvement
   Statement shape:
   - for a deterministic conditional source, a matching contextual model is never worse than a flat model
   Why:
   - this is the cleanest informational theorem in the current direction

2. Irreversible-update lower bound
   Statement shape:
   - a compression step with positive erased-information witness has a nonzero thermodynamic lower bound
   Why:
   - this is the first true information -> physics bridge

3. Accuracy-cost tradeoff
   Statement shape:
   - increasing task accuracy requires weakly greater nonequilibrium cost
   Why:
   - directly motivated by the reverse-entropy / nonequilibrium paper

4. Substrate admissibility
   Statement shape:
   - if defect / transport / dissipation constraints are below threshold, the substrate can realize the compression step
   Why:
   - this is the first materials witness theorem

## Repo Notes

Existing code that can be reused:

- `/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/ExtensionScaffold/Compression/Core.lean`
- `/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/ExtensionScaffold/Compression/HutterUncompressed.lean`
- `/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/ExtensionScaffold/Compression/HutterContext.lean`

Existing code that should not be treated as proof of the goal:

- `/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/InteratomicPotential.lean`
- `/home/allaun/Documents/Research Stack/5-Applications/tools-scripts/build_composition_dag.py`

Current integration caveat:

- full `lake build` is still failing elsewhere in the repo, so new theorem work should be kept minimal and locally verifiable until the existing build blockers are resolved

## Immediate Next Step

Start with:

1. `Semantics.CompressionEvidence`
2. `Semantics.LandauerCompression`

Reason:

- these modules capture the strongest rigor upgrades from the Nature-family sources
- they avoid premature chemistry claims
- they give a truthful base for any later defect-mechanics or interatomic witness layer
