# Project-Wide Glossary — Sovereign Research Stack

**Authority:** `docs/VOCABULARY_LOCK.md`, `CONCEPTS.md`, `docs/gcl/GLOSSARY.md`
**Ground Truth:** Lean 4 (`0-Core-Formalism/lean/Semantics/`)

---

## Core Formalism

| Term | Definition |
|---|---|
| **bind** | The single universal primitive: `(A × B × Metric) → Bind A B`. All algorithms collapse to this. Five allowed classes: informational, geometric, thermodynamic, physical, control. |
| **Q16_16** | 32-bit fixed-point (`UInt32`, `0x00010000 = 1.0`). Mixed integer + fraction. Last-resort only; requires documented deterministic overflow. |
| **Q0_16** | 16-bit fixed-point (`UInt16`), pure fraction `[-1, 1 - 2^-16]`. Default for all dimensionless quantities (losses, scores, probabilities, phase angles). |
| **Q0_64** | 64-bit 0D scalar `[0, 1)`. Universal scalar for cross-substrate communication. |
| **FixedPoint** | The formal module (`Semantics.FixedPoint`) defining both Q16_16 and Q0_16 arithmetic. All operations must match bit-exactly across Lean/Verilog/Python. |
| **AMMR** | Algebraic Merkle Mountain Range — hierarchical cryptographic accumulator over equation forest nodes. |
| **AVMR** | Adaptive Vector Manifest Roll-up — hierarchical summary of vector manifolds across substrates. |
| **O-AMMR** | Ordered AMMR — AMMR with explicit dependency ordering on the equation DAG. |
| **BraidField** | Path-sensitive field `B(t)` through which information carriers are rotated to expose phase/charge instability. Basis of the Charged-Mass Braid Sieve. |
| **BracketedCalculus** | Gap-conserving bound calculus: `⟨l, u, v, g_l, g_u⟩` where `g_l + g_u = u − l`. Substrate #35. |
| **bindPreservesInvariant** | Core theorem: every lawful `bind` operation preserves the domain's declared invariant. |
| **MasterEquation** | `S_{t+1} = MLGRU(Gossip(Prune(Stabilize(Score_{Σ+NK}(Expand(S_t))))))` — the universal state transition across all agent substrates. |

## Geometry

| Term | Definition |
|---|---|
| **PIST** | Perfectly Imperfect Square Theory — witness/audit surface with shell coordinate transform. States: `(k, t) ∈ ℕ²`. Invariant: mass conservation. |
| **DIAT** | Dynamic Integer-Address Transform — shell coordinate system for energy cell quantization. |
| **NUVMAP** | Non-Uniform Variable Mapping — 2D spectral projection `(u, v)` where `u = f(t) = t×1000`, `v = g(n) = n`. |
| **GWL** | Gravitational-Wave-Like topology — 5-factor rotational coupling geometry (θ, φ, τ, χ, proximity). |
| **S3C** | Shell/Topological Codec — energy cell quantization into `n² + m` integer shells. |
| **SSMS_nD** | Nested self-similar manifold shell — recursive fractal dimension descent. Substrate #5. |
| **Goxel** | Geometric voxel — an N-space shape primitive whose derived math must be auditable in a declared field. |
| **Torus** | Toroidal manifold on which PIST operations wrap via `(k, t) mod T`. Substrate #9. |
| **BettiCycle** | Topological cycle (β₀, β₁, β₂) used as fingerprint of manifold connectivity. |
| **SolitonTensor** | Nonlinear persistent wave on the manifold with conserved identity (Sine-Gordon energy). Substrate #7. |
| **TorsionalPIST** | Quaternion-valued PIST extension: `(q₁, q₂, q₃) ∈ ℚ³` with quaternion geodesic distance. Substrate #8. |
| **GWLThroat** | Multi-factor GWL threshold traversal: holonomy bounded, `Φ_topo >> Φ_metric`. Substrate #24. |

## Compression

| Term | Definition |
|---|---|
| **GCCL** | Geometric-Coded Compression Language — the unified compression theory spanning all substrates. |
| **GCLang** | Executable notation / compiler substrate for GCL. |
| **GCCL-Rep** | GCCL representation format — the serialized interchange format. |
| **MISC** | Manifold-Invariant Shell Compression — compression via shell coordinate encoding on the manifold. |
| **GENSIS** | Genetic-Natured N-Space universal encoding substrate — MISC extended with every known biological/genetic coding system generalized to N-dimensional hypercubic shells. |
| **DeltaGCL** | Differential GCL — compact representation of differences (deltas) between successive manifold states. Substrate #19. |
| **PTOS** | Photonic Topological Optical Storage — photon-pulse-based read/write of crystal substrate topology. |
| **KOT** | Kinetic Optical Transform — the optical pulse modulation mechanism for substrate state update. |
| **VLE** | Variable-Length Encoding — adaptive symbol encoding based on frequency/basin statistics. |
| **ΔφγKλ** | Delta-phase-gamma-kappa-lambda — the complete differential encoding across phase (φ), gamma (γ), curvature (κ), and wavelength (λ). |

## Biology / Neural

| Term | Definition |
|---|---|
| **SpikingNeuron** | Izhikevich model: `(v, u, I)` with membrane potential dynamics `dv/dt`, `du/dt`. Substrate #20. |
| **STDP** | Spike-Timing-Dependent Plasticity: `Δw = A·exp(-Δt/τ)`. Weight update depends on relative spike timing. Substrate #21. |
| **GeneticCode** | Codon → amino acid mapping with Hamming distance `d_H = Σ[b_i ≠ b_j]`. Includes 30+ variant tables. Substrate #16. |
| **CodonOptimization** | Codon reassignment driven by CAI (Codon Adaptation Index): `CAI = Π(w_i)^(1/L)`. Substrate #18. |
| **DNAmethylation** | Epigenetic mark — methyl group addition to cytosine, altering expression without changing sequence. |
| **HistoneMod** | Histone tail modification (acetylation, methylation, phosphorylation) — encodes regulatory state on chromatin. |
| **Prion** | Misfolded protein acting as conformational template — a physical instantiation of the Reverse-Sisyphus structural-memory principle. |
| **Genome18** | 18-bit genome address space: 6 bins × 3 bits per bin. |
| **r_vs_SAE** | Pearson correlation between codon bias and SAE neural feature alignment — a project-specific manifold-capacity proxy. |

## Thermodynamics

| Term | Definition |
|---|---|
| **Trixal** | Multi-axis thermodynamic quality state: `(thermal, work, irrev)` with `|Δ| = √(Σaxis²)`. Compression modeled as a heat engine. Substrate #13. |
| **HomeostaticGovernor** | Control dynamics: `stress = α·surprise + β·regret`, pressure evolution `p_{t+1} = γ·p_t + s_t`. Fixed-point condition: `|γ + s'(p*)| < 1`. Substrate #15. |
| **DynamicCanal** | Adaptive canal that deforms under pressure: `λ(p, pressure)` with width ≥ 0. Substrate #27. |
| **Landauer** | Landauer's principle: minimum energy `kT·ln2` per bit erasure. Grounds AngrySphinx thermodynamic asymmetry. |
| **HyperFlow** | Navier-Stokes on the manifold: `∂F/∂t = ν∇²F - (F·∇)F + ∇p`. Fixed-point convergence with bounded pressure. Substrate #10. |
| **TSM** | Thermal State Machine — Builder (ADD), Judge (PAUSE), Warden (SUBTRACT) clock triad. |
| **Reverse-Sisyphus** | Property: `dC/dt = f(W, C)` AND `E[W(t+Δ)] < E[W(t)]` — work persistently reduces future work on the same pattern class. |
| **CognitiveLoad** | 5-component load model: `(L_I, L_E, L_G, L_R, L_M)` with efficiency `η = Î/(total+ε)`. Substrate #14. |

## Security

| Term | Definition |
|---|---|
| **AngrySphinx** | Lattice-based PQC primitive. Exponential energy asymmetry: `E_attack = n ⟹ E_solve ≥ 2^n`. NaN boundary at `F → 0`. Substrate #3. |
| **FAMM** | Frustration-Aware Manifold Mesh — frustration-aligned memory policy that stores failed/partial/successful routes as basin/scar signals. Substrate #6. |
| **FrustrationTensor** | Triadic frustration tensor `(i, j, k)` storing route constraint violation as geometric torsion. |
| **NaNBoundary** | The limit surface where AngrySphinx frustration metric `F → 0`, returning undefined — a deliberate defense mechanism. |
| **PodAccumulator** | Distributed attestation accumulator that collects and verifies PIST witness signatures across swarm pods. |
| **Waveprobe** | Hysteretic mode-switch security sensor: `risk = (1+γ·(1-cosθ))/d² + η·h` with barriers `B_lock > B_warn > B_recover`. Substrate #30. |
| **stark_trace** | STARK-based validation trace used by the Warden to verify GCL program execution integrity. |
| **nanokernel_isolation** | Theorem: different capabilities map to different physical addresses — non-interference guarantee for MORE FAMM. |

## Semantics

| Term | Definition |
|---|---|
| **CrossDimensionalFilter** | Semantic filter operating across dimensions via 12 primal primes. `reductionFilter` and `expansionFilter` preserve prime overlap. Substrate #4. |
| **SemanticPrime** | One of 12 irreducible semantic dimensions: Identity, Agent, Object, Action, State, Relation, Good, Bad, Want, Know, Place, Time. |
| **reductionFilter** | Compresses state to scalar Q0.64 via prime-space projection. |
| **expansionFilter** | Reconstructs state from Q0.64 scalar via prime-space interpolation. |
| **PrimeOverlap** | The invariant: shared semantic primes must remain non-empty across filtering operations. |
| **Identity / Agent / Object / Action / State / Relation / Good / Bad / Want / Know / Place / Time** | The 12 semantic primes — atomic dimensions of the CrossDimensionalFilter. |

## Meta

| Term | Definition |
|---|---|
| **Metatype** | The trajectory quality invariant — a formal classification of agent trajectory behavior patterns. |
| **UMUP-λ** | Universal Manifold Update Protocol — the λ-parameterized update rule across all manifolds. |
| **IRP** | Invariant Receipt Protocol — auditable proof that a transition preserved the declared invariant. |
| **InvariantReceipt** | A signed cryptographic receipt proving a specific invariant was preserved through a state transition. |
| **SettlementState** | Ladder: `SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED`. Encodes the maturity of a claim, module, or route. |
| **PromotionLadder** | Evidence ladder: `BEAUTIFUL_PROVISIONAL → CALIBRATED_ENGINEERING_DELTA → REVIEWED → VERIFIED`. Each step requires non-LLM evidence. |
| **BLS** | BLS signature scheme — aggregate signatures for swarm consensus attestation. |
| **Sigma** | Statistical surprise measure (5σ / 6σ / 6.5σ). Applies ONLY to statistical claims, not formal proofs. |
| **FNWH** | Formal Non-Wave Harmonic — the underlying harmonic framework for Burgers/Braiding proofs. |

## Infrastructure

| Term | Definition |
|---|---|
| **ENE** | Endless Node Edges — distributed, self-replicating credential and node management system with gossip protocol and 2/3 consensus for credential rotation. |
| **OTOM** | Ordered Transformation & Orchestration Model — the unifying label for all Research Stack work. |
| **NII** | Native Integer ISA — the executable control layer (`Semantics.ISA`). |
| **SVQF** | Spherical Quaternion Vector Field — spherical quaternion geometry for field representation. |
| **PIST** | (also listed under Geometry) — serves dual role as witness surface and shell addressing infrastructure. |
| **Substrate** | A mathematical layer with: state space, metric, transition, invariant, guard. |
| **FPGA_Warden** | FPGA-based Warden node executing `stark_trace` validation on burned DAG-LUTs. |
| **ASICTopology** | Capability-vector topology over ASIC nodes, geodesic distance admissibility check. Substrate #34. |
| **CacheSieve** | 5×2-bit symbol classifier (PASS/HOLD/REJECT) with sieve invariant. Substrate #36. |
| **DAG-LUT** | Burned-in Look-Up Table representing banned/immutable coordinate history. Append-only. |
| **MORE_FAMM** | Capability-based memory isolation via BRAM segments. Foundation of the safety architecture. |
| **RcloneIntegration** | Formalized `TopologicalStorageArea` structure — Google Drive as persistent ENE surface. |
| **SubstrateState** | Component of `VMState` — the topological RAM substrate within the virtual machine. |

## The 36 USTSM Substrates

From `docs/roadmaps/UNIVERSAL_SUBSTRATE_ROADMAP.md` §1:

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
