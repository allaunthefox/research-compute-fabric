# Glossary

> **Source:** [[../docs/GLOSSARY.md|Main Glossary]] · [[../docs/WEIRD_CONCEPTS_GLOSSARY.md|Weird Concepts]] · [[Concept-Archive|Concept Archive]] · [[../docs/VOCABULARY_LOCK.md|Vocabulary Lock]] · [[../CONCEPTS.md|Core Concepts]]

---

## Core Formalism

| Term | Definition |
|---|---|
| **bind** | The single universal primitive: `(A × B × Metric) → Bind A B`. All algorithms collapse to this. Five allowed classes: informational, geometric, thermodynamic, physical, control. |
| **Q16_16** | 32-bit fixed-point (`UInt32`, `0x00010000 = 1.0`). Mixed integer + fraction. Last-resort only. |
| **Q0_16** | 16-bit fixed-point (`UInt16`), pure fraction `[-1, 1]`. Default for dimensionless quantities. |
| **Q0_64** | 64-bit 0D scalar `[0, 1)`. Universal scalar for cross-substrate communication. |
| **FixedPoint** | Formal module (`Semantics.FixedPoint`) defining both Q16_16 and Q0_16 arithmetic. |
| **AMMR** | Algebraic Merkle Mountain Range — hierarchical cryptographic accumulator over equation forest nodes. |
| **AVMR** | Adaptive Vector Manifest Roll-up — hierarchical summary of vector manifolds across substrates. |
| **O-AMMR** | Ordered AMMR — AMMR with explicit dependency ordering on the equation DAG. |
| **BraidField** | Path-sensitive field `B(t)` through which information carriers are rotated to expose phase/charge instability. |
| **BracketedCalculus** | Gap-conserving bound calculus: `⟨l, u, v, g_l, g_u⟩`. Substrate #35. |

---

## Geometry

| Term | Definition |
|---|---|
| **PIST** | Perfectly Imperfect Square Theory — witness/audit surface. States: `(k, t) ∈ ℕ²`. Invariant: mass conservation. |
| **DIAT** | Dynamic Integer-Address Transform — shell coordinate system for energy cell quantization. |
| **NUVMAP** | Non-Uniform Variable Mapping — 2D spectral projection `(u, v)`. |
| **GWL** | Gravitational-Wave-Like topology — 5-factor rotational coupling geometry (θ, φ, τ, χ, proximity). |
| **S3C** | Shell/Topological Codec — energy cell quantization into `n² + m` integer shells. |
| **SSMS_nD** | Nested self-similar manifold shell — recursive fractal dimension descent. |
| **Goxel** | Geometric voxel — N-space shape primitive. |
| **SolitonTensor** | Nonlinear persistent wave on the manifold with conserved identity (Sine-Gordon energy). |
| **TorsionalPIST** | Quaternion-valued PIST extension: `(q₁, q₂, q₃) ∈ ℚ³`. |

---

## Compression

| Term | Definition |
|---|---|
| **GCCL** | Geometric, Cognitive, and Compression Law — the unified law stack spanning all substrates. |
| **MISC** | Manifold-Invariant Shell Compression — compression via shell coordinate encoding on the manifold. |
| **GENSIS** | Genetic-Natured N-Space universal encoding substrate — MISC extended with biological/genetic coding systems. |
| **DeltaGCL** | Differential GCL — compact representation of differences between successive manifold states. |
| **PTOS** | Photonic Topological Optical Storage — photon-pulse-based read/write of crystal substrate topology. |
| **KOT** | Kinetic Operation Token — accounting layer for action cost. Every transformation pays. |
| **VLE** | Variable-Length Encoding — adaptive symbol encoding based on frequency/basin statistics. |
| **ΔφγKλ** | Delta-phase-gamma-kappa-lambda — complete differential encoding across phase, gamma, curvature, and wavelength. |

---

## Biology / Neural

| Term | Definition |
|---|---|
| **SpikingNeuron** | Izhikevich model: `(v, u, I)` with membrane potential dynamics. |
| **STDP** | Spike-Timing-Dependent Plasticity: `Δw = A·exp(-Δt/τ)`. |
| **GeneticCode** | Codon → amino acid mapping with 30+ variant tables. 64 codons, 20+ AAs. |
| **CodonOptimization** | Codon reassignment driven by CAI (Codon Adaptation Index). |
| **DNAmethylation** | Epigenetic mark — methyl group addition to cytosine. |
| **HistoneMod** | Histone tail modification encoding regulatory state. |
| **Prion** | Misfolded protein acting as conformational template — Reverse-Sisyphus structural memory. |
| **Neural Type Eigenvector Coverage** | Coverage-driven morphology/evidence graph where broad neuron-type features become a principal vector used to rank biological analogues by measured efficiency gain, provenance, and residual risk. |
| **Locally Adaptive Contact Materials** | Cooperative anisotropic layered flip-tile material/control patches held near a bounded critical phase boundary so local charge/field inputs can alter stiffness, adhesion, damping, friction, texture, or shape while preserving contact authority. |
| **Fractal Extendable Hair Field** | Nested active micron-scale hair/fibril field over a tensioned material skin; branches extend, orient, stiffen, and retract to multiply dry adhesion or microhook contact while preserving detachability. |
| **Recovered Session Material Concepts** | Material-primitives bundle mined from a recovered local chat: MXene nanoscrolls, resonant SLS tubules, conductive valence matrices, magnetic labyrinths, magnetoelectric laminate capsules, piezo receipts, ferrite/carbon doping, and SDR void hashes. |
| **Structural eFuse Surface** | Passive load-bearing geometry/material state that trips a measurable signal under unsafe strain, misalignment, flux imbalance, conductivity jump, or RF-signature drift. |

---

## Thermodynamics

| Term | Definition |
|---|---|
| **Trixal** | Multi-axis thermodynamic quality state: `(thermal, work, irrev)`. Compression modeled as a heat engine. |
| **HomeostaticGovernor** | Control dynamics: pressure evolution `p_{t+1} = γ·p_t + s_t`. |
| **DynamicCanal** | Adaptive canal that deforms under pressure. |
| **Landauer** | Principle: minimum energy `kT·ln2` per bit erasure. |
| **HyperFlow** | Navier-Stokes on the manifold: `∂F/∂t = ν∇²F - (F·∇)F + ∇p`. |
| **F-Number COUCH** | Finite COUCH route-pressure proxy: `F_COUCH(κ) = avg_curvature_milli(κ) + max_curvature_milli(κ) + FAMM_frustration_milli`; current high-F threshold `18500`. |
| **U-Rotated COUCH Value** | Finite COUCH projection along curvature and coupling: `U_rot(κ) = C_avg_milli(κ) + κ_milli * U_norm_milli(κ) / 1000`. |
| **Y-Axis O-Step COUCH Container** | Finite COUCH packet `{O_steps, U_value, R_value}` where `U_value = U_rot(κ)` and `R_value = 1000` is constant. |
| **Route-Pressure COUCH Gate** | Operational COUCH pressure `P_COUCH(κ) = F_COUCH(κ) + U_rot(κ) - R_value`, mapped to `local`, `atlas`, or `reject` routing actions. |
| **LNMF / Loch-Nessie-Monster Filter** | Hidden-basin routing filter: `Loch(L) = internal/(1+leakage) * A_L`, `nE_i(L) = A_{L,i} * rho_{L,i} * Scar_i(L)`, `M(L) = |Aut(L)| * Loch(L) * sum nE_i(L)`. Candidate, not a Monster-group proof. |
| **Monster Filter Assignment** | Assignment layer over LNMF outputs: Tree Fiddy/BHOCS owns archive commit monsters, Loc Nes owns hidden recurrence witnesses, and quarantine remains explicit. |
| **English Word Bonding Equations** | Speculative-materials bridge where words such as `CAGE`, `BRIDGE`, `CHAIN`, `SCAR`, `SALT`, and `RING` name finite bonding/routing operators. Mnemonic only; not a chemistry claim. |
| **Reactive Semantic Perturbation / Fluorinated Semantics** | Discovery method that permits highly reactive or absurd semantic inputs, then admits only outputs that survive typed gates, receipts, failure modes, and quarantine. |
| **CognitiveLoad** | 5-component load model: `(L_I, L_E, L_G, L_R, L_M)`. |
| **Reverse-Sisyphus** | Property: `dC/dt = f(W, C)` AND `E[W(t+Δ)] < E[W(t)]` — work reduces future work. |

---

## Security

| Term | Definition |
|---|---|
| **AngrySphinx** | Exponential energy asymmetry: `E_attack = n ⟹ E_solve ≥ 2^n`. NaN boundary at `F → 0`. |
| **FAMM** | Frustration-Aligned Memory Management — stores failed/partial/successful routes as basin/scar signals. |
| **FrustrationTensor** | Triadic frustration tensor `(i, j, k)` storing route constraint violation. |
| **NaNBoundary** | Limit surface where frustration metric `F → 0`, returning undefined. |
| **PodAccumulator** | Distributed attestation accumulator collecting PIST witness signatures. |
| **Waveprobe** | Hysteretic mode-switch security sensor with barriers `B_lock > B_warn > B_recover`. |

---

## Semantics

| Term | Definition |
|---|---|
| **CrossDimensionalFilter** | Semantic filter operating across dimensions via 12 primal primes. |
| **SemanticPrime** | One of 12 irreducible meaning atoms. |

The 12 Semantic Primes:

| # | Prime | Description |
|---|-------|-------------|
| 1 | **Identity** | Self-reference, what a thing is |
| 2 | **Agent** | Active entity, actor |
| 3 | **Object** | Passive entity, thing acted upon |
| 4 | **Action** | Event, process, doing |
| 5 | **State** | Condition, property, mode |
| 6 | **Relation** | Connection, link, between |
| 7 | **Good** | Positive valence, desirable |
| 8 | **Bad** | Negative valence, undesirable |
| 9 | **Want** | Desire, intent, goal |
| 10 | **Know** | Knowledge, belief, awareness |
| 11 | **Place** | Location, space, where |
| 12 | **Time** | Temporal, when, duration |

---

## Meta

| Term | Definition |
|---|---|
| **Metatype** | Trajectory quality invariant — formal classification of agent trajectory behavior patterns. |
| **UMUP-λ** | Universal Manifold Update Protocol — λ-parameterized update rule across all manifolds. |
| **IRP** | Invariant Receipt Protocol — auditable proof that a transition preserved the declared invariant. |
| **SettlementState** | Ladder: `SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED`. |
| **PromotionLadder** | `BEAUTIFUL_PROVISIONAL → CALIBRATED_ENGINEERING_DELTA → REVIEWED → VERIFIED`. |
| **BLS** | Bounded Lawful Surface — set of transitions expressible under declared constraints. |
| **FNWH** | Formal Non-Wave Harmonic — underlying harmonic framework for Burgers/Braiding proofs. |

---

## Infrastructure

| Term | Definition |
|---|---|
| **ENE** | Endless Node Edges — distributed credential and node management with gossip protocol. |
| **OTOM** | Ordered Transformation & Orchestration Model — unifying label for all Research Stack work. |
| **NII** | Native Integer ISA — executable control layer (`Semantics.ISA`). |
| **Substrate** | A mathematical layer with: state space, metric, transition, invariant, guard. |
| **FPGA_Warden** | FPGA-based Warden node executing `stark_trace` validation on burned DAG-LUTs. |
| **CacheSieve** | 5×2-bit symbol classifier (PASS/HOLD/REJECT). |
| **MORE_FAMM** | Capability-based memory isolation via BRAM segments. |

---

## The 36 USTSM Substrates

| # | Substrate | Invariant |
|---|---|---|
| 1 | PIST/DIAT Shell | mass conservation |
| 2 | GWL Rotational | dE/dt ≤ 0 |
| 3 | AngrySphinx | E_solve ≥ 2^n |
| 4 | CrossDimensionalFilter | semantic prime preservation |
| 5 | SSMS_nD | self-similarity invariant |
| 6 | FAMM Frustration | frustration monotonic |
| 7 | SolitonTensor | soliton identity |
| 8 | TorsionalPIST | quaternion norm |
| 9 | HybridTSMPISTTorus | positive mass only |
| 10 | HyperFlow | fixed point convergence |
| 11 | Q16_16 FixedPoint | totality (no NaN) |
| 12 | Q0_64 0D Scalar | stay in [0,1) |
| 13 | Trixal Thermodynamic | irrev < threshold |
| 14 | Cognitive Load | efficiency ≥ 0 |
| 15 | Homeostatic Governor | pressure bounded |
| 16 | Genetic Code | codon validity |
| 17 | Genomic Compression | field invariant |
| 18 | Codon Optimization | CAI monotonic |
| 19 | Delta GCL | delta(m,m) = empty |
| 20 | Spiking Neuron | v < 30 mV until fire |
| 21 | STDP Synaptic | bounds conserved |
| 22 | Manifold Networking | curvature bounded |
| 23 | Quantum Geometry | observational fit |
| 24 | GWL Throat | holonomy bounded |
| 25 | Braid Field | mergeDebt ≤ threshold |
| 26 | Adaptation | isLawful, params in range |
| 27 | DynamicCanal | width ≥ 0 |
| 28 | CompressionMechanics | order contracts |
| 29 | PIST Bridge | O(1) per step |
| 30 | Waveprobe | B_lock > B_warn > B_recover |
| 31 | MasterEquation | probability sum = 1 |
| 32 | CompressionControl | canonicalized |
| 33 | CompressionEvidence | energy decomposes |
| 34 | ASICTopology | operation admissible |
| 35 | BracketedCalculus | g_l + g_u = u − l |
| 36 | CacheSieve | sieve invariant |

---

## Quick Reference: Framework Hierarchy

```
GCCL = Law Stack (what must be preserved)
  │
  ├── MISC = Compression Engine (how it runs)
  │     Uses: PIST shells, GWL coupling, Cognitive Router, Trixal Verify
  │     │
  │     └── GENSIS = N-D Extension (genetic codes + hypercubic shells)
  │
  └── USTSM = Substrate Census (36 substrates under one Q0_64 scalar)
```

---

## Quick Reference: Data Flow

```
Raw Data → PIST Remap → GWL Coupling → Cognitive Router → Delta GCL → Trixal Verify → Homeostatic Update → Output + Receipt
```

---

*For the full authoritative glossary with additional entries, see [[../docs/GLOSSARY.md|Main Glossary]].*
