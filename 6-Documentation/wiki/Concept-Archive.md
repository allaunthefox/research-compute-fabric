# Concept Archive

This page is the wiki attic for Research Stack concepts: canonical, active,
candidate, speculative, held, lossy, retired, and abandoned. Inclusion here is
not promotion. It means the concept has appeared in the repo and should remain
findable with an honest status.

## Status Legend

| Status | Meaning |
|---|---|
| **CANONICAL** | Defined by the main glossary, vocabulary lock, Lean surface, or roadmap. |
| **ACTIVE** | Used in current code/docs, but not necessarily fully proven. |
| **CANDIDATE** | Useful concept with a repo surface; needs stronger evidence before promotion. |
| **SPECULATIVE** | Research scratchpad or analogy; do not cite as established fact. |
| **HELD** | Preserved because it may be useful, but blocked by tests, proof gaps, or failed quantitative checks. |
| **LOSSY** | Useful experiment that cannot round-trip or preserve the needed invariant. |
| **EXTERNAL_REFERENCE** | Outside work kept as a citation/search anchor; do not treat as imported repo code or an internal claim. |
| **RETIRED_ALIAS** | Old evocative name retained for search; use the neutral technical term in formal docs. |
| **ABANDONED** | Preserved for provenance; not a current design direction. |

## Canonical And Active Concepts

| Concept | Status | Why it is kept | Primary surface |
|---|---|---|---|
| **AMMR** | CANONICAL | Merkle-mountain accumulator over equation forests. | `docs/GLOSSARY.md`, `3-Mathematical-Models/AMMR/` |
| **AngrySphinx** | CANONICAL | Exponential proof-of-defense gate and quarantine default. | `Semantics.AngrySphinx`, `docs/safety/ANGRYSPHINX_ADAPTIVE_SHELL_DEFENSE.md` |
| **AVM** | ACTIVE | Math-language-to-bytecode adapter and shim boundary. | `Semantics.AVM`, `docs/AGENTS.md` |
| **AVMR / O-AVMR** | ACTIVE | Vector manifest roll-up and orthogonal/geodesic hotpath surfaces. | `AVMR*.lean`, PIST shifter |
| **Artin Braid Geometry** | ACTIVE | Byte-to-crossing functions over `sigma_i` / `sigma_i^-1`, braid composition, inverse, simplification, and crossing entropy. | `pist_biological_polymorphic_shifter_v3_complete.py` |
| **bind** | CANONICAL | Universal primitive for lawful transformations. | `docs/GLOSSARY.md`, Lean Semantics |
| **BraidField** | CANONICAL | Path-sensitive field for exposing phase/charge instability. | `Semantics.BraidField`, `CONCEPTS.md` |
| **CacheSieve** | ACTIVE | PASS/HOLD/REJECT classifier before expensive proof work. | `Semantics.CacheSieve` |
| **Charged-Mass Braid Sieve** | CANDIDATE | Routes unstable mass into basin, hold, scar, or discharge. | `CONCEPTS.md`, `docs/charged_mass_braid_sieve.md` |
| **CognitiveLoad** | CANONICAL | Five-part load model for strategy selection. | `Semantics.CognitiveLoad`, `docs/GLOSSARY.md` |
| **DAG-LUT** | ACTIVE | Burned immutable coordinate history for pruning and FPGA checks. | `docs/AGENTS.md`, FPGA Warden docs |
| **DIAT** | CANONICAL | Integer shell coordinate transform. | `docs/GLOSSARY.md` |
| **DynamicCanal** | ACTIVE | Adaptive route canal with nonnegative width constraint. | `Semantics.DynamicCanal` |
| **ENE** | CANONICAL | Durable node/credential/knowledge substrate. | `CONCEPTS.md`, `4-Infrastructure/infra/` |
| **English Word Bonding Equations** | CANDIDATE | Uses words like `CAGE`, `BRIDGE`, `CHAIN`, `SCAR`, `SALT`, and `RING` as mnemonic handles for finite bonding/routing operators. Kept only as a graph/search and speculative-materials surface; element-symbol parses are not material claims. | `docs/speculative-materials/EnglishWordBondingEquations.md` |
| **Adaptive Material Math Application Map** | CANDIDATE | Crosswalk from layered flip-tile/fractal-hair/MXene-scroll material ideas into DynamicCanal, COUCH, Braid Sieve, Waveprobe, MorphicDSP, PIST, Hutter, cotranslational folding, and branch-cut math surfaces. | `docs/speculative-materials/AdaptiveMaterialMathApplicationMap.md` |
| **FAMM** | CANONICAL | Frustration-aware memory policy over basins and scars. | `CONCEPTS.md`, `docs/GLOSSARY.md` |
| **FixedPoint** | CANONICAL | Q16_16/Q0_16 deterministic arithmetic surface. | `Semantics.FixedPoint` |
| **FNWH** | ACTIVE | Formal harmonic framework for Burgers/Braiding surfaces. | `docs/GLOSSARY.md`, FNWH modules |
| **Fractal Extendable Hair Field** | CANDIDATE | Nested active micron-scale hair/fibril field over a tensioned material skin; branches extend, orient, stiffen, and retract to multiply dry adhesion or microhook contact while preserving detachability. | `docs/speculative-materials/LocallyAdaptiveContactMaterials.md` |
| **Fuck Your Couch** | RETIRED_ALIAS | Operator-facing search alias for the COUCH equation family. Use `F-Number COUCH`, `U-Rotated COUCH Value`, `Y-Axis O-Step COUCH Container`, or `Route-Pressure COUCH Gate` in formal writing. | `Semantics.CouchFilterNormalization`, `COUCH_EQUATION.md` |
| **GENSIS** | ACTIVE | Genetic N-space extension of MISC over shell coordinates. | `manifold_compression/src/gensis_kernel.py`, GENSIS docs |
| **GCCL / GCL / DeltaGCL** | CANONICAL | Compression/law language and delta representation. | `docs/gcl/`, `docs/GLOSSARY.md` |
| **Gecko Dry Adhesion Anchor** | EXTERNAL_REFERENCE | Real-world precedent for reversible van der Waals-style contact authority via hierarchical setae/spatulae; used as the grounded model for layered flip-tile material adhesion, with roughness, contamination, humidity, peel direction, and wear limits preserved. | `docs/speculative-materials/LocallyAdaptiveContactMaterials.md` |
| **Recovered Session Material Concepts** | CANDIDATE | Local chat recovery bundle for missing material primitives: MXene nanoscrolls, charge-flow shaping, resonant SLS tubules, conductive valence matrices, magnetic labyrinths, magnetoelectric laminate capsules, piezo alerts, ferrite/carbon SLS doping, and SDR resonant void readout. | `docs/speculative-materials/RecoveredSessionMaterialConcepts.md` |
| **Genome18** | ACTIVE | 18-bit address space, six 3-bit bins. | `Semantics.Genome18`, `EQUATION_FOREST_INDEX.md` |
| **Geometry Is Memory** | CANDIDATE | Topological RAM principle: shape stores state. | `CONCEPTS.md`, `BRAIN_AS_MANIFOLD.md` |
| **Goxel** | CANDIDATE | Geometric voxel/domain primitive. | `docs/GLOSSARY.md`, `ENE_RESEARCH_TOPIC_CANDIDATES.md` |
| **GWL / GWL Throat** | CANONICAL | Five-factor coupling and topological traversal gate. | `docs/GLOSSARY.md`, GWL modules |
| **HomeostaticGovernor** | CANONICAL | Pressure controller and fixed-point convergence target. | `docs/GLOSSARY.md` |
| **Harmonic Shape Transform (HST)** | EXTERNAL_REFERENCE | Laplace-eigenfunction "harmonic note" used as an intrinsic scalar coordinate for shape correspondence; useful precedent for semantic eigenvector bundles, not imported as repo code. License preserved in `CITATION.cff` and `THIRD_PARTY_NOTICES.md`. | `https://github.com/sel8888/harmonic-shape-transform-2026-koncept` |
| **HELLO Transform** | CANDIDATE | Joke-born mnemonic/operator sketch: `E(H equiv N) + (L x L) -> O(n)`, where harmonic/eigenstructure aligns to graph nodes so language-lattice matching avoids full pairwise explosion. | Search target, semantic eigenvector bundle notes |
| **HyperFlow** | ACTIVE | Navier-Stokes-like manifold flow. | `Semantics.HyperFlow` |
| **IRP / InvariantReceipt** | ACTIVE | Receipt proving a transition preserved its invariant. | `Semantics.InvariantReceipt` |
| **LNMF / Loch-Nessie-Monster Filter** | CANDIDATE | Hidden-basin routing filter: `Loch(L) = internal/(1+leakage) * A_L`, `nE_i(L) = A_{L,i} * rho_{L,i} * Scar_i(L)`, and `M(L) = |Aut(L)| * Loch(L) * sum nE_i(L)`. Preserved as a symmetry-amplified routing score, not a claim that the mathematical Monster group is present. | `0-Core-Formalism/otom/tools/lean/Semantics/Semantics/LochMonsterFilter.lean` |
| **Loc Nes Monster** | RETIRED_ALIAS | Operator-facing search alias for LNMF / Loch-Nessie-Monster Filter and the hidden recurrence side of the monster-filter family. | `Semantics.LochMonsterFilter` |
| **Locally Adaptive Contact Materials** | CANDIDATE | Cooperative anisotropic layered flip-tile material/control patches held near a bounded critical phase boundary so local charge/field inputs can change stiffness, adhesion, damping, texture, or shape while preserving contact authority. | `docs/speculative-materials/LocallyAdaptiveContactMaterials.md` |
| **Structural eFuse Surface** | CANDIDATE | Passive material/geometry gate where tubule buckling, flux imbalance, percolation shift, or RF-signature drift produces a piezo/ME alert receipt before catastrophic structural failure. | `docs/speculative-materials/RecoveredSessionMaterialConcepts.md` |
| **Monster Filter Assignment** | CANDIDATE | Explicit bridge assigning monster-filter outputs to `treeFiddyBound`, `locNesRecurrence`, or `combinedGate`. Tree Fiddy owns BHOCS/archive commit routes; Loc Nes owns hidden-basin/Nessie recurrence witnesses; quarantine stays marked. | `Semantics.LochMonsterFilter` |
| **Mass Number** | ACTIVE | Admissible reduction + residual risk + boundary guard packet. | `Semantics.Core.MassNumber` |
| **Matroska-S3C Nested Reduction Gear** | CANDIDATE | Nested shell route-prior geometry. | `docs/specs/MS3C_NESTED_REDUCTION_GEAR_SPEC.md` |
| **MISC** | CANONICAL | Manifold-invariant shell compression engine. | `docs/research/MISC_THEORY.md` |
| **MOIM** | ACTIVE | Behavioral/discrete manifold surface. | `Semantics.MOIMMetaprobe`, manifold taxonomy |
| **MORE_FAMM** | ACTIVE | Capability-isolated FAMM memory architecture. | `docs/GLOSSARY.md`, nanokernel notes |
| **NaNBoundary** | ACTIVE | Refusal boundary for invalid/zero-frustration paths. | `docs/GLOSSARY.md`, GENSIS compiler spec |
| **Neural Type Eigenvector Coverage** | CANDIDATE | Broad neuron-type morphology/evidence graph reduced to a principal coverage direction, used to rank which biological analogues improve routing, compression, or verification efficiency. | `6-Documentation/docs/research/NEURAL_TYPE_EIGENVECTOR_COVERAGE.md` |
| **NUVMAP** | CANONICAL | Non-uniform variable mapping and address projection. | `docs/GLOSSARY.md`, NUVMAP specs |
| **OEPI** | ACTIVE | Operator Escalation Percentage Index. | `Semantics.OEPI` |
| **OTOM** | CANONICAL | Ordered Transformation and Orchestration Model. | `CONCEPTS.md`, `OTOMOntology.lean` |
| **PIST** | CANONICAL | Shell witness/address surface with mass conservation. | `docs/GLOSSARY.md`, `Semantics.PIST` |
| **PodAccumulator** | ACTIVE | Distributed witness/signature accumulator. | `docs/GLOSSARY.md` |
| **Q0_16 / Q0_64 / Q16_16** | CANONICAL | Fixed-point and scalar communication formats. | `Semantics.FixedPoint`, `docs/GLOSSARY.md` |
| **RGFlow** | ACTIVE | Scale-coherence and lawfulness surface. | `SemanticRGFlow`, formal verification docs |
| **S3C** | CANONICAL | Shell/topological codec. | `Semantics.S3C`, `docs/GLOSSARY.md` |
| **Semantic Primes** | CANONICAL | Twelve irreducible semantic dimensions. | `CrossDimensionalFilter`, `docs/GLOSSARY.md` |
| **Semantic Mass** | ACTIVE | Dimensionless semantic/routing load; not physical mass, and not itself a Mass Number receipt. | `Semantics.SemanticMass`, `mass_numbers_deanthropocentric_revision.md` |
| **Semantic Eigenvector Bundle** | CANDIDATE | Cluster of concepts treated as a principal direction in a semantic graph rather than as isolated keywords. | Search target, eigenvector literature anchors |
| **Semantic Prime Refraction** | CANDIDATE | Semantic route law over concept eigenvectors, semantic-prime alignment, and MassNumber gradients. | `hdmi_as_computation_fabric_ene_brief.md` |
| **SIM** | CANDIDATE | Sovereign Informatic Manifold. | `INFORMATION_MANIFOLD_TAXONOMY.md` |
| **SLUQ** | ACTIVE | Routing accumulator/state-machine surface. | `Hardware/AdaptiveFabric.lean` |
| **STDP** | CANONICAL | Spike-timing-dependent plasticity. | `docs/GLOSSARY.md` |
| **SolitonTensor** | CANONICAL | Persistent nonlinear wave identity. | `docs/GLOSSARY.md` |
| **TSM** | CANONICAL | Builder/Judge/Warden thermal clock. | `docs/GLOSSARY.md`, `docs/AGENTS.md` |
| **TorsionalPIST** | CANONICAL | Quaternion-valued PIST shell traversal. | `docs/GLOSSARY.md` |
| **Trixal** | CANONICAL | Thermal/work/irreversibility quality vector. | `docs/GLOSSARY.md`, MISC theory |
| **Tree Fiddy Monster Assignment** | CANDIDATE | Bounded archive side of the monster filter: `.bhocsCommitMonster` routes are assigned to Tree Fiddy/BHOCS because the result should be caged as bounded recursive history, not left as active dynamics. | `Semantics.LochMonsterFilter`, `Semantics.BHOCS`, `Semantics.CoulombComplexity` |
| **UMUP-lambda** | CANONICAL | Universal manifold update protocol. | `docs/GLOSSARY.md` |
| **USTSM** | CANONICAL | 36-substrate census under Q0_64 scalar interface. | `docs/roadmaps/ROADMAP.md` |
| **Waveprobe** | ACTIVE | Hysteretic local selection/risk kernel. | `Semantics.Waveprobe`, `waveprobe_qubo_spec.tex` |
| **WebGPU Geant4-DNA** | EXTERNAL_REFERENCE | Browser/WebGPU Monte Carlo track-structure simulation for radiobiology, with IRT chemistry and B-DNA SSB/DSB scoring. Useful external validation analogue for GPU physics kernels, DNA damage scoring, and browser-resident compute surfaces; not imported as repo code. License preserved in `CITATION.cff` and `THIRD_PARTY_NOTICES.md`. | `https://github.com/abgnydn/webgpu-dna` |

## Weird, Speculative, Held, Or Retired Concepts

| Concept | Status | Why it is kept | Primary surface |
|---|---|---|---|
| **AEGIS Shifter** | CANDIDATE | Expanded synthetic genetic alphabet transform. | `pist_biological_polymorphic_shifter_v3_complete.py` |
| **Basin** | ACTIVE | Stable routing neighborhood and positive memory signal. | FAMM docs |
| **Braid Rope Fusion Shifter** | CANDIDATE | Combined braid/rope geometry; reported best ratio `0.327` and entropy `2.376`. | PIST shifter |
| **Braid Shifter** | CANDIDATE | Artin braid group encoding; reported ratio `0.490`, entropy `1.161`, with simplification. | PIST shifter |
| **Builder** | RETIRED_ALIAS | Old actor name for constructive ADD phase. | `docs/AGENTS.md` |
| **CE-sRGB-NIICore** | CANDIDATE | Chiral eigenvector sRGB-style NIICore packet surface for display-color-like compute cells. | HDMI computation fabric ingest |
| **Chiral GCCL** | CANDIDATE | Handedness layer across GCCL transforms. | PIST shifter |
| **Chirality Destabilizer** | CANDIDATE | Bounded novelty perturbation that surfaces hidden eigenroutes without unbounded chaos. | HDMI computation fabric ingest |
| **Crystallization Front Invariant** | ACTIVE | Neutral name for work reducing future work. | `docs/AGENTS.md`, `BRAIN_AS_MANIFOLD.md` |
| **DSE Shifter** | CANDIDATE | Deterministic-stochastic perturbation folded through PIST mass. | PIST shifter |
| **Edge Survivor** | CANDIDATE | HOLD fragment that is neither promoted nor discarded. | Braid sieve docs |
| **Edge-of-Universe Anomalies** | SPECULATIVE | Variable torsional clock remapping for cosmology anomalies. | `variable_omega_edge_anomalies.md` |
| **Epistemic Inhibitory Controller / Warden** | RETIRED_ALIAS | Old actor name for verification/SUBTRACT phase. | `docs/AGENTS.md` |
| **FAMM Scar** | ACTIVE | Remembered failed route. | FAMM docs |
| **Foldback Lock** | CANDIDATE | Prevents runaway manifold evolution. | `INFORMATION_MANIFOLD_TAXONOMY.md` |
| **F-Number COUCH** | CANDIDATE | Integer-scaled COUCH route-pressure proxy: `F_COUCH(κ) = avg_curvature_milli(κ) + max_curvature_milli(κ) + FAMM_frustration_milli`. Full-sweep Lean witnesses cover `κ=0.50,1.00,1.50,2.00,2.50` as `18085,18163,18274,18419,18596`; high-F threshold `18500`. | `Semantics.CouchFilterNormalization`, `COUCH_EQUATION.md` |
| **Galois Ring Shifter** | CANDIDATE | GF(256)-style byte transform. | PIST shifter |
| **Golden Stratum Gate** | RETIRED_ALIAS | Old phi-ratio phase-gate name. | `docs/AGENTS.md`, `EXPLORATION_PLAN.md` |
| **Hachimoji Shifter** | CANDIDATE | 16-symbol synthetic DNA transform. | PIST shifter |
| **Heat-2D Adapter** | CANDIDATE | Maps physical source deposits into 2D heat PDE. | `3-Mathematical-Models/AMMR/HEAT2D_ADAPTER.md` |
| **Holographic Recursive Fractal Connectome** | CANDIDATE | Fingerprint/keystream shifter family. | PIST shifter |
| **Hot/Cold FAMM** | CANDIDATE | Hot path routes deterministic admissible states; cold path captures scars, ambiguity, and expensive recovery. | HDMI computation fabric ingest |
| **Hyphal Net Shifter** | CANDIDATE | Fungal-network-inspired routing transform. | PIST shifter |
| **Judge** | RETIRED_ALIAS | Old actor name for PAUSE/adjudication phase. | `docs/AGENTS.md` |
| **Multilayer Moire Decoder** | SPECULATIVE | Cross-domain decoder analogy using layers, twist, and gaps. | `unified_equation.md` |
| **Multicolor Rope Geometry** | CANDIDATE | Encodes `(strand, color, twist)` tuples; tension comes from twist variance and color entropy tracks color usage. | PIST shifter |
| **Multicolor Rope Shifter** | CANDIDATE | Colored strand bundle transform; reported ratio `0.329`, entropy `2.363`, rope tension `0.107`, color entropy `2.122`. | PIST shifter |
| **NExponent** | CANDIDATE | Heuristic shifter capacity score. | PIST shifter |
| **N-Shell Coordinate** | ACTIVE | Generalized PIST coordinate in N-dimensional shells. | `manifold_compression/src/gensis_kernel.py` |
| **Nonlinear Persistent Wave / Soliton** | RETIRED_ALIAS | Old evocative label for persistent nonlinear wave. | `docs/AGENTS.md` |
| **O-AVMR Hotpath** | CANDIDATE | Orthogonal AVMR with PIST geodesic hotpath. | PIST shifter |
| **PIST Direct** | CANDIDATE | Byte to `(shell, offset)` coordinate encoding. | PIST shifter |
| **PIST Mirror** | ACTIVE | Same-mass involution on a PIST shell. | PIST shifter, `misc_kernel.py` |
| **PIST Resonance** | ACTIVE | Jump between same-mass coordinates. | PIST shifter, `gensis_kernel.py` |
| **PIST-NUVMAP Texel** | CANDIDATE | Packed NUVMAP projection of PIST coordinates. | PIST shifter |
| **Quarantine** | ACTIVE | Refusal state for unsafe or unbounded transitions. | AngrySphinx/Warden docs |
| **Reactive Semantic Perturbation / Fluorinated Semantics** | CANDIDATE | Method term for injecting highly reactive, informal, or absurd concept atoms into a formal/search engine to reveal hidden structure. Kept only with the output discipline: typed gates, receipts, failure modes, and quarantine. | `docs/WEIRD_CONCEPTS_GLOSSARY.md` |
| **Recursive Branch Cut** | HELD | Quantitative thermodynamic tests failed; useful as large-scale analogy only. | `recursive_branch_cut_self_similarity.md`, `thermodynamic_test_recursive_branch_cut.md` |
| **Reverse-Sisyphus** | RETIRED_ALIAS | Old name for crystallization-front/work-reduces-work invariant. | `docs/GLOSSARY.md`, `BRAIN_AS_MANIFOLD.md` |
| **Route-Pressure COUCH Gate** | CANDIDATE | Operational COUCH payoff gate: `P_COUCH(κ) = F_COUCH(κ) + U_rot(κ) - R_value`, selecting `local`, `atlas`, or `reject` from finite Lean witnesses. | `Semantics.CouchFilterNormalization`, `COUCH_EQUATION.md` |
| **Scar Memory** | ACTIVE | Persistent failed-route evidence. | FAMM docs |
| **Spiegelmer Shifter** | CANDIDATE | Mirror-image aptamer transform. | PIST shifter |
| **Topological RAM** | CANDIDATE | Geometry stores state directly. | `CONCEPTS.md` |
| **TMDS Timing Plane** | CANDIDATE | Display timing treated as clock/law surface, separate from payload and authority. | HDMI computation fabric ingest |
| **Torsional Gradient Particle** | SPECULATIVE | Particle as stable gradient in torsional unwinding field. | `torsional_cosmology_spin.md` |
| **Torsional Uncertainty** | SPECULATIVE | Quantum uncertainty as torsional vibration/phase resolution. | `uncertainty_from_torsional_vibration.md` |
| **Torsional Unwinding** | SPECULATIVE | Time/expansion as decreasing torsional winding. | `torsional_cosmology_spin.md` |
| **Underverse packet** | CANDIDATE | Downgraded non-promotable Mass Number outcome. | `Semantics.Core.MassNumber` |
| **Universal Evolutionary Equation** | CANDIDATE | Evolution/compression bridge through conserved basis fusion. | `universal_evolutionary_equation.md` |
| **Universal Unified Equation** | SPECULATIVE | Cross-domain umbrella operator over physics, biology, and compression. | `unified_equation.md` |
| **U-Rotated COUCH Value** | CANDIDATE | Fixed-point-safe COUCH projection along curvature and coupling: `U_rot(κ) = C_avg_milli(κ) + κ_milli * U_norm_milli(κ) / 1000`. Full-sweep Lean witnesses cover `κ=0.50,1.00,1.50,2.00,2.50` as `8785,9552,10322,11093,11867`. | `Semantics.CouchFilterNormalization`, `COUCH_EQUATION.md` |
| **Variable Omega Field** | SPECULATIVE | Local torsional clock-rate field. | `variable_omega_edge_anomalies.md` |
| **Virtual HDMI Blitter** | CANDIDATE | Virtual display/blitter contract where raster pixels act as command/state cells and display machinery becomes compute/witness fabric. | HDMI computation fabric ingest |
| **Wave Overhangs Adapter** | CANDIDATE | Toolpath-as-wavefront model coupled to Heat-2D. | `AMMR/WAVE_OVERHANGS_ADAPTER.md` |
| **Whirlpool** | SPECULATIVE | FAMM basin-circulation / route-intensity image. | `INFORMATION_MANIFOLD_TAXONOMY.md` |
| **Wireworld Shifter** | LOSSY | Cellular automaton transform; decode is explicitly lossy. | PIST shifter |
| **Y-Axis O-Step COUCH Container** | CANDIDATE | Finite COUCH sweep packet `{O_steps, U_value, R_value}` where `O_steps = trajectory_steps(κ)`, `U_value = U_rot(κ)`, and `R_value = 1000` is constant. | `Semantics.CouchFilterNormalization`, `COUCH_EQUATION.md` |

## Module Surface Census

The local wiki already contains a large generated/connector module surface:

- `6-Documentation/wiki/Obsidian-connector/Manifold/Modules/`
- Current count at archive creation: **631 module notes**

This directory is the broadest mechanical concept inventory. The tables above
are the human-facing archive. The module directory is the exhaustive surface for
module names such as `AMMR`, `AngrySphinx`, `BraidField`, `CacheSieve`,
`DynamicCanal`, `Genome18`, `Hardware_AdaptiveFabric`, `MOIMMetaprobe`,
`MassNumberAdapter`, `MorphicDSP`, `PIST`, `RGFlow`, `S3C`, `SLUQ`,
`SemanticRGFlow`, `TorsionalPIST`, `Waveprobe`, and hundreds of extension
surfaces.

## Search Engine Target

The future internal search engine must be semantic-driven, not only
keyword-driven. It should connect weird names, neutral technical names, code
symbols, theorem surfaces, abandoned aliases, and evidence receipts into one
retrievable concept graph.

Minimum target layers:

1. Literal index: exact symbols, paths, functions, theorem names, issue IDs.
2. Semantic concept index: aliases, weird names, neutral names, status labels,
   concept clusters, and gestalt/eigenvector-like bundles.
3. Evidence/routing layer: reversible vs lossy, canonical vs speculative,
   benchmark vs theory, proof vs scratchpad, Hutter-claim-safe vs
   discovery-only.
4. Inspectable graph layer: concept nodes, alias nodes, file/module nodes,
   theorem/function nodes, benchmark receipt nodes, Linear issue nodes, status
   nodes, and evidence-type nodes.

Ranking should use semantic mass: prefer hits connected to downstream concepts,
active/canonical status, executable evidence, and the current route. A
MassNumber-style gate should mark whether a result is admissible for the task
or only useful for discovery.

Graph edges should be typed, not just "related":

- `defines`
- `aliases`
- `imports`
- `cites`
- `derives`
- `gates`
- `blocks`
- `promotes`
- `demotes`
- `benchmarks`
- `round-trips`
- `fails`
- `quarantines`
- `related-to`

Every search result should be able to explain itself as a path, for example:

```text
Variable Omega Field -> torsional clock -> compression timing -> Hutter discovery-only
SemanticMass -> meaning-bearing load -> MassNumber -> admissibility receipt
Braid Rope Fusion Shifter -> benchmark receipt -> reversible? -> Hutter claim gate
HELLO Transform -> harmonic-node alignment -> language lattice -> O(n) search sketch
```

Minimum graph queries:

```text
neighbors SemanticMass
path SemanticMass MassNumber
why hutter braid rope
```

Graph export should stay local and inspectable first: GraphML, JSONL edges, or
a SQLite edge table. A visual UI can come later.

Linear target: `RES-2377`.

### Eigenvector Literature Anchors

The "concept bundle as eigenvector" target should be framed as an extension of
existing eigenvector traditions, not as an isolated invention. Immediate anchor
families to preserve in the search index:

| Anchor | Use in Research Stack |
|---|---|
| Bonacich, 2007, *Some unique properties of eigenvector centrality* | Centrality and prestige-weighted concept importance in the internal graph. |
| Langville, 2005, *A Survey of Eigenvector Methods for Web Information Retrieval* | Search ranking precedent for graph-native retrieval. |
| Nelson, 1976, *Simplified calculation of eigenvector derivatives*; Lim, 1987, *Re-examination of eigenvector derivatives* | Sensitivity of concept eigenvectors when evidence or edges change. |
| Shapiro, 1992, *Feature-based correspondence: an eigenvector approach* | Matching concepts across files, aliases, and modalities by feature structure. |
| Saaty, 1998/2001, analytic hierarchy process eigenvector ranking | Decision/prioritization surface for promotion gates and route choices. |
| Xiang, 2008, *Spectral clustering with eigenvector selection* | Selecting stable concept clusters without swallowing every adjacent term. |
| Gauch, 1982, *Noise Reduction By Eigenvector Ordinations* | Reducing noise in weird/scratchpad concepts before promotion. |
| Allez, 2012, *Eigenvector dynamics* | Dynamics of changing semantic fields over time. |
| Duguet, 2023, *Eigenvector Continuation and Projection-Based Emulators* | Continuation/emulator framing for moving between local concept regimes. |
| Ipsen, 1997, *Computing an Eigenvector with Inverse Iteration* | Practical computation path for local graph ranking. |
| Diniz-Filho, 1998, phylogenetic inertia eigenvector method | Inertia/history model for inherited concept structure. |
| Knowles, 2013, Wigner matrix eigenvector distribution | Random-matrix caution surface for noise, false structure, and null models. |
| Krahulik, 2026, Harmonic Shape Transform (HST) repository | Shape-domain analogue: a Laplace eigenfunction acts as a normalized intrinsic coordinate or "harmonic note" for correspondence. Treat as external reference, not internal proof. |

Working interpretation:

```text
gestalt / concept bundle
  -> principal semantic direction over a typed evidence graph
  -> weighted by semantic mass and admissibility receipts
  -> exposed as a searchable, explainable path

HST shape note
  -> Laplace eigenfunction as intrinsic coordinate
  -> equal-level mapping between shapes
  -> analogy target for semantic-prime/eigenvector route maps

HELLO Transform
  -> "hello" as notation joke: H, E, L x L, O(n)
  -> candidate operator sketch, not theorem
  -> E(H equiv N) + (L x L) -> O(n)
  -> harmonic/eigen node alignment makes language-lattice matching route-based
```

Recent ingest artifacts:

- `shared-data/data/ingested/chatgpt/hdmi_as_computation_fabric_transcript.md`
- `shared-data/data/ingested/chatgpt/hdmi_as_computation_fabric_ene_brief.md`
- `shared-data/data/ingested/chatgpt/hdmi_as_computation_fabric_graph_edges.jsonl`
- `shared-data/data/ingested/chatgpt/hdmi_as_computation_fabric.graphml`

Recent research audit:

- `6-Documentation/docs/research/WEIRD_ACCELERATION_DEEP_DIVE_2026_05_06.md`

## Promotion Rule

Before a concept moves out of this archive into canonical docs, require:

1. A neutral technical name.
2. A declared invariant, gate, or receipt.
3. A source surface: Lean module, script, spec, model note, or audit artifact.
4. A status change recorded in docs, not just in conversation.
