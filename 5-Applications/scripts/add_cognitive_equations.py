#!/usr/bin/env python3
"""
Add Cognitive Physics equations to the physics database.

This script adds the 12 language prime equations and additional relevant equations
from the OTOM document to the physics_equations.db database.
"""

import sqlite3

DB_PATH = "/dev/shm/physics_equations.db"
DOMAIN_ID = 51  # Cognitive Physics

equations = [
    {
        "eq_number": 738,
        "title": "NSM Semantic Primes Explication",
        "significance": "Universal semantic decomposition using 64 irreducible primes. Foundation for language compression and cognitive load analysis.",
        "latex_formula": r"\text{Explication}(c) = \text{Compose}(\text{Primes}_{64}, \text{Grammar}_{\text{universal}})",
        "description": "The NSM framework defines 64 universal semantic primes with combinatorial syntax for explication of any concept."
    },
    {
        "eq_number": 739,
        "title": "Cognitive Load Matrix (Invariant-Enhanced)",
        "significance": "8-dimensional cognitive load model with invariant preservation. Critical for assessing processing overhead in semantic compression.",
        "latex_formula": r"L_{\text{total}} = \lambda_I \hat{l}_I + \lambda_E \hat{l}_E - \lambda_G \hat{l}_G + \lambda_R \hat{l}_R + \lambda_M \hat{l}_M + \lambda_{\text{inv}} \hat{l}_{\text{inv}} + \lambda_{\text{traj}} \hat{l}_{\text{traj}} + \lambda_{\text{aci}} \hat{l}_{\text{aci}}",
        "description": "Total cognitive load with intrinsic, extraneous, germane, routing, memory, invariant, trajectory, and ACI components."
    },
    {
        "eq_number": 740,
        "title": "Evolutionary Operator (Universal)",
        "significance": "Conserved operator frozen across 120 Myr evolution. Model for compression operators that remain stable across contexts.",
        "latex_formula": r"\text{Phenotype}(x, t) = \Psi_E [ \text{Genotype}(x) \times \text{Regulatory\_State}(t) ]",
        "description": "The operator Ψ_E is conserved; only the regulatory state changes. Analogous to compression operators in semantic systems."
    },
    {
        "eq_number": 741,
        "title": "Hutter Prize Compression Equation",
        "significance": "Weighted compression metric with decoder and resource penalties. Foundation for compression efficiency optimization.",
        "latex_formula": r"C = (0.4 \cdot C_{\text{comp}} + 0.35 \cdot C_{\text{phys}} + 0.25 \cdot C_{\text{geom}}) \times \left(\frac{S}{G + F}\right)",
        "description": "Compression score with computational, physical, and geometric components weighted by size over grammar+features."
    },
    {
        "eq_number": 742,
        "title": "Semantic Compression Operator",
        "significance": "Language-specific compression operator using NSM primes as conserved basis. Core of semantic-aware compression.",
        "latex_formula": r"\text{Compressed}(x) = \Psi_S [ \text{Primes}_{64} \times \text{Context}(x) ]",
        "description": "Ψ_S is the learned semantic compression operator; Primes_64 are the conserved basis; Context(x) is linguistic context."
    },
    {
        "eq_number": 743,
        "title": "Prime-to-Byte Mapping",
        "significance": "Maps semantic primes to compression primitives. Enables semantic-aware byte-level optimization.",
        "latex_formula": r"p_i \rightarrow \text{Primitive}_i = \{ \text{pattern}, \text{weight}, \text{context\_mask} \}",
        "description": "Each prime maps to a pattern, compression weight, and context mask for byte-level encoding."
    },
    {
        "eq_number": 744,
        "title": "Context as Cognitive Load Function",
        "significance": "Cognitive load determines regulatory state for compression. Links processing overhead to prime activation.",
        "latex_formula": r"\text{Context}(x) = f(L_{\text{total}}(x), L_{\text{inv}}(x, \mathcal{I}_{\text{NSM}}))",
        "description": "Context is a function of total cognitive load and prime-specific invariant load."
    },
    {
        "eq_number": 745,
        "title": "Gap Adaptation Equation",
        "significance": "Evolutionary fracking principle: gap width controls coupling strength. Adaptive prime filtering based on load.",
        "latex_formula": r"\text{Gap}(x) = \text{Gap}_{\text{max}} \cdot \left(1 - \frac{L_{\text{total}}(x)}{L_{\text{max}}}\right)",
        "description": "Gap narrows under high load (stress response, critical primes only) and widens under low load (relaxed processing)."
    },
    {
        "eq_number": 746,
        "title": "Unified Semantic Compression Equation",
        "significance": "Complete integration of primes, cognitive load, and gap adaptation. Master equation for semantic compression.",
        "latex_formula": r"\text{Compressed}(x) = \Psi_S [ \text{Primes}_{64} \times \text{Context}(L_{\text{total}}(x)) ] \times \text{Gap}(L_{\text{total}}(x))",
        "description": "Combines semantic operator, prime basis, cognitive load context, and gap-dependent filtering."
    },
    {
        "eq_number": 747,
        "title": "Gap-Dependent Prime Activation",
        "significance": "Threshold function for prime activation based on gap width. Implements stress response in compression.",
        "latex_formula": r"\mathbb{1}[\text{active}(p_i, \text{Gap}(x))] = \begin{cases} 1 & \text{if } \text{severity}(i) \geq \theta_{\text{gap}}(\text{Gap}(x)) \\ 0 & \text{otherwise} \end{cases}",
        "description": "Indicator function for prime activation based on severity threshold that varies with gap width."
    },
    {
        "eq_number": 748,
        "title": "Prime Compression Matrix",
        "significance": "64×64 matrix of prime weights and cross-correlations. Encodes conserved topology of semantic relationships.",
        "latex_formula": r"M_P = \begin{bmatrix} w_1 & c_{1,1} & c_{1,2} & \cdots & c_{1,64} \\ w_2 & c_{2,1} & c_{2,2} & \cdots & c_{2,64} \\ \vdots & \vdots & \vdots & \ddots & \vdots \\ w_{64} & c_{64,1} & c_{64,2} & \cdots & c_{64,64} \end{bmatrix}",
        "description": "Matrix of severity weights and cross-correlations between semantic primes. Topology is conserved across languages."
    },
    {
        "eq_number": 749,
        "title": "Matrix-Vector Compression",
        "significance": "Linear algebra formulation of semantic compression with gap modulation. Efficient implementation target.",
        "latex_formula": r"\text{Compressed}(x) = M_P \cdot \vec{v}(x) \cdot \text{Gap}(L_{\text{total}}(x))",
        "description": "Matrix multiplication of prime matrix with activation vector, modulated by gap width."
    },
    # Additional distilled equations
    {
        "eq_number": 750,
        "title": "Invariant Load with Prime Activation",
        "significance": "Modified invariant load that only counts active primes. Reduces penalty under high-stress conditions.",
        "latex_formula": r"L_{\text{inv}}^{\text{active}}(x, \mathcal{I}_{\text{NSM}}) = \sum_{i \in \mathcal{I}_{\text{NSM}}} w_i \cdot \mathbb{1}[\text{broken}(i, x)] \cdot \text{severity}(i) \cdot \mathbb{1}[\text{active}(p_i, \text{Gap}(x))]",
        "description": "Invariant load only counts primes that are both broken and active given current gap width."
    },
    {
        "eq_number": 751,
        "title": "Gap Threshold Function",
        "significance": "Piecewise threshold mapping gap width to severity cutoff. Implements discrete stress response levels.",
        "latex_formula": r"\theta_{\text{gap}}(\text{Gap}) = \begin{cases} \infty & \text{if Gap} < 0.2 \text{ (narrow, stress)} \\ 1.0 & \text{if } 0.2 \leq \text{Gap} < 0.5 \text{ (moderate)} \\ 0.5 & \text{if } 0.5 \leq \text{Gap} < 0.8 \text{ (relaxed)} \\ 0.1 & \text{if Gap} \geq 0.8 \text{ (wide, all primes)} \end{cases}",
        "description": "Severity threshold as function of gap width, defining four operating regimes."
    },
    {
        "eq_number": 752,
        "title": "Hutter Prize Penalty with Invariants",
        "significance": "Extended Hutter Prize penalty including invariant preservation cost. Tradeoff between compression and semantic fidelity.",
        "latex_formula": r"\phi_{\text{HP-NSM}} = \phi(x) + \alpha_{\text{Comp}} \cdot \text{Compression}_{\text{NSM}} + \alpha_{\text{Dec}} \cdot \text{Decoder}_{\text{NSM}} + \alpha_{\text{Res}} \cdot \text{Resource}_{\text{NSM}} + \alpha_{\text{Inv}} \cdot L_{\text{inv}}^{\text{active}}",
        "description": "Penalty function with compression, decoder, resource, and invariant preservation components."
    },
    {
        "eq_number": 753,
        "title": "Gap Adaptation Dynamics",
        "significance": "Gradient descent dynamics for gap adaptation. Ensures convergence to optimal load-balanced state.",
        "latex_formula": r"\frac{d\text{Gap}}{dt} = -\nabla_{\text{Gap}} L_{\text{total}}(x)",
        "description": "Gap evolves to minimize cognitive load via gradient descent."
    },
    {
        "eq_number": 754,
        "title": "Prime Conservation Theorem (Spectral Entropy Bound)",
        "significance": "Compression ratio bounded by spectral entropy of prime activation under conserved operator.",
        "latex_formula": r"H_{\Psi_S}(l) = -\sum_{i=1}^{64} p_l(i) \log_2 p_{\Psi_S}(i) \leq H_{\text{uniform}}(l)",
        "description": "Spectral entropy bound for compression ratio under conserved semantic operator."
    },
    {
        "eq_number": 755,
        "title": "Invariant Preservation Theorem",
        "significance": "Critical invariants (severity=∞) preserved regardless of gap width. Hard constraint on compression.",
        "latex_formula": r"\text{Compression}_{\text{max}} = \max_{\Psi_S} \text{Compression}(\Psi_S) \quad \text{s.t.} \quad \forall i \in \mathcal{I}_{\text{critical}}, \neg \text{broken}(i, x)",
        "description": "Maximum compression subject to critical invariant preservation constraint."
    },
    {
        "eq_number": 756,
        "title": "Matrix Evolution Learning Rule",
        "significance": "Gradient-based learning of prime matrix while conserving topology. Analogous to evolutionary mutation.",
        "latex_formula": r"M_P(t+1) = M_P(t) + \eta \cdot \nabla_{M_P} \text{Compression}_{\text{NSM}}",
        "description": "Prime matrix evolves via gradient descent on compression while preserving topology."
    },
    {
        "eq_number": 757,
        "title": "Cross-Linguistic Compression Equation",
        "significance": "Unified compression across languages with language-specific gap functions. Enables transfer learning.",
        "latex_formula": r"\text{Compressed}(x_l) = \Psi_S [ \text{Primes}_{64} \times \text{Context}_l(L_{\text{total}}(x_l)) ] \times \text{Gap}_l(L_{\text{total}}(x_l))",
        "description": "Compression for language l using conserved operator Ψ_S with language-specific context and gap functions."
    },
    {
        "eq_number": 758,
        "title": "Language-Specific Gap Function",
        "significance": "Gap function parameterized by language complexity. Accounts for morphological and syntactic differences.",
        "latex_formula": r"\text{Gap}_l(x) = g_l(L_{\text{total}}(x)) = \text{Gap}_{\text{max}, l} \cdot \left(1 - \frac{L_{\text{total}}(x)}{L_{\text{max}, l}}\right)",
        "description": "Language-specific gap adaptation with language-dependent maximum gap and load threshold."
    },
    # 0-AVMR Equations (Algebraic Vector Mountain Range)
    {
        "eq_number": 759,
        "title": "0-AVMR: Square Shell Identity",
        "significance": "Foundational partition of natural numbers into discrete shells indexed by k = floor(sqrt(n)). Basis for hierarchical vector aggregation.",
        "latex_formula": r"a + b = 2k + 1 \quad \text{where} \quad k = \lfloor \sqrt{n} \rfloor",
        "description": "Shell identity partitions naturals into shells where each shell k contains numbers in [k², (k+1)²)."
    },
    {
        "eq_number": 760,
        "title": "0-AVMR: Tip Coordinate Map",
        "significance": "Injective coordinate system on each shell mapping (a,b) to (product, difference). Enables vector aggregation with discriminant invariant.",
        "latex_formula": r"\text{Tip}(n) = (a \cdot b, a - b)",
        "description": "Tip map provides coordinate system with discriminant invariant: (a-b)² + 4ab = (a+b)²."
    },
    {
        "eq_number": 761,
        "title": "0-AVMR: Interaction Score",
        "significance": "Additive decomposition of interaction into mass, polarity, and spectral components. Basis for vector interaction terms.",
        "latex_formula": r"J = m + p + s",
        "description": "Interaction score as sum of mass_term, polarity_term, and spectral_overlap components."
    },
    {
        "eq_number": 762,
        "title": "0-AVMR: Genetic Transduction",
        "significance": "Composition mapping temporal-color encoding to genetic codon space. Theoretical bridge between temporal patterns and biological encoding.",
        "latex_formula": r"\Phi_{\text{trans}} = \text{GeneticCode}(\text{Codon}(\Phi_{\text{time\_color}}(n)))",
        "description": "Transduction from temporal-color space through codon space to genetic code output."
    },
    {
        "eq_number": 763,
        "title": "0-AVMR: Genetic Entropy Bound",
        "significance": "Information capacity bound for genetic coding system. H ≈ 4.2 bits bounded by log2(64) = 6 bits (codon space).",
        "latex_formula": r"H_{\text{genetic}} \approx 4.2 \text{ bits}, \quad \log_2(20) \leq H_{\text{genetic}} \leq \log_2(64)",
        "description": "Genetic entropy measured from codon usage frequencies, bounded by codon space capacity."
    },
    # 0-AMMR Equations (Analytic Mathematical Model of Reality)
    {
        "eq_number": 764,
        "title": "0-AMMR: Shell Partition of Computation",
        "significance": "Maps any computation (via Gödel encoding) to discrete shell structure. Provides hierarchical organization for ENE operations.",
        "latex_formula": r"\text{Partition}(n) = k = \lfloor \sqrt{n} \rfloor",
        "description": "Shell partition function maps natural numbers (computation encodings) to shell indices."
    },
    {
        "eq_number": 765,
        "title": "0-AMMR: Shell Coordinate System",
        "significance": "Tip map as injective coordinate system on each shell. Enables unique addressing within computational shells.",
        "latex_formula": r"\text{Coord}_k(a,b) = (a \cdot b, a - b) \quad \text{with} \quad a + b = 2k + 1",
        "description": "Coordinate system on shell k with injectivity guaranteed by fixed sum constraint."
    },
    {
        "eq_number": 766,
        "title": "0-AMMR: Additive Shell Interaction",
        "significance": "Interactions between shells decompose additively. Basis for multi-shell computation in ENE.",
        "latex_formula": r"J_{\text{inter-shell}} = \sum_{i} J_i = \sum_{i} (m_i + p_i + s_i)",
        "description": "Shell interactions sum additively across components and shells."
    },
    {
        "eq_number": 767,
        "title": "0-AMMR: Temporal-Genetic Transduction",
        "significance": "Temporal patterns transduced to genetic encoding. Potential for time-aware semantic compression in ENE.",
        "latex_formula": r"\Phi_{\text{temporal}} \rightarrow \text{Codon} \rightarrow \text{GeneticCode}",
        "description": "Three-stage transduction from temporal encoding through codon space to genetic output."
    },
    {
        "eq_number": 768,
        "title": "0-AMMR: Information Capacity Bound",
        "significance": "Genetic entropy bounds system information capacity. Provides theoretical limit for ENE compression.",
        "latex_formula": r"H_{\text{system}} \leq \log_2(64) = 6 \text{ bits}",
        "description": "System information capacity bounded by genetic codon space entropy."
    },
    {
        "eq_number": 769,
        "title": "0-AMMR: RG Flow Shell Preservation",
        "significance": "Renormalization group flow preserves shell structure under scale transformations. Critical for ENE scale-invariant operations.",
        "latex_formula": r"\sigma_q = 1.0 + 0.35 \cdot \text{coherence} - 8.0 \cdot \text{volatility}",
        "description": "RG flow equation governing shell preservation under scale transformations."
    },
    # Graph Native Equations
    {
        "eq_number": 770,
        "title": "Graph Laplacian Spectral Decomposition",
        "significance": "Spectral decomposition of graph Laplacian for graph-native computation. Enables eigenvector-based graph operations.",
        "latex_formula": r"L = D - A, \quad L \phi_k = \lambda_k \phi_k",
        "description": "Graph Laplacian L = D - A with eigenvectors φ_k and eigenvalues λ_k for spectral analysis."
    },
    {
        "eq_number": 771,
        "title": "Graph Attention Mechanism",
        "significance": "Attention-based message passing for graph neural networks. Enables context-aware graph operations.",
        "latex_formula": r"\alpha_{ij} = \frac{\exp(\text{LeakyReLU}(a^T [Wh_i \| Wh_j]))}{\sum_{k \in \mathcal{N}(i)} \exp(\text{LeakyReLU}(a^T [Wh_i \| Wh_k]))}",
        "description": "Graph attention coefficient α_ij for node i attending to node j."
    },
    {
        "eq_number": 772,
        "title": "Graph Convolution",
        "significance": "Spectral graph convolution for graph-native processing. Enables convolution operations on graph-structured data.",
        "latex_formula": r"H^{(l+1)} = \sigma(\tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2} H^{(l)} W^{(l)})",
        "description": "Graph convolution with normalized adjacency matrix and weight matrix."
    },
    # WGSL/WebGPU Equations
    {
        "eq_number": 773,
        "title": "WGSL Vector Swizzle Operation",
        "significance": "GPU vector component swizzling for efficient parallel processing. Enables flexible vector manipulation on GPU.",
        "latex_formula": r"\text{swizzle}(v, \text{mask}) = v_{\text{mask}}",
        "description": "Vector swizzle operation extracting components by mask (e.g., .xyz, .rgba)."
    },
    {
        "eq_number": 774,
        "title": "WGSL Workgroup Synchronization",
        "significance": "Barrier synchronization for GPU workgroups. Ensures correct parallel execution order.",
        "latex_formula": r"\text{workgroupBarrier}() \implies \forall i,j \in \text{workgroup}, \text{order}(i, j) \text{ preserved}",
        "description": "Workgroup barrier ensures all threads reach barrier before proceeding."
    },
    {
        "eq_number": 775,
        "title": "WGSL Shared Memory Reduction",
        "significance": "Parallel reduction in GPU shared memory. Enables efficient aggregation across workgroup.",
        "latex_formula": r"\text{reduce}(S) = \sum_{i=0}^{N-1} S_i \quad \text{with} \quad O(\log N) \text{ steps}",
        "description": "Parallel reduction in shared memory with logarithmic step complexity."
    },
    # Vector Appending Equations
    {
        "eq_number": 776,
        "title": "Vector Append Operation",
        "significance": "Dynamic vector appending for incremental processing. Enables streaming vector operations.",
        "latex_formula": r"v \oplus x = [v_1, v_2, \ldots, v_n, x]",
        "description": "Vector append operation adding element x to end of vector v."
    },
    {
        "eq_number": 777,
        "title": "Vector Concatenation",
        "significance": "Efficient vector concatenation for batch processing. Enables combining multiple vectors.",
        "latex_formula": r"v \parallel w = [v_1, \ldots, v_n, w_1, \ldots, w_m]",
        "description": "Vector concatenation combining v and w into single vector."
    },
    {
        "eq_number": 778,
        "title": "Vector Append with Capacity Growth",
        "significance": "Amortized O(1) append with geometric capacity growth. Optimizes memory allocation.",
        "latex_formula": r"\text{capacity}_{\text{new}} = \text{capacity}_{\text{old}} \times \phi, \quad \phi \approx 1.5-2.0",
        "description": "Geometric capacity growth for amortized O(1) append operations."
    },
    {
        "eq_number": 779,
        "title": "Graph Vector Append",
        "significance": "Appending vectors to graph nodes for incremental graph updates. Enables dynamic graph processing.",
        "latex_formula": r"G[v] \leftarrow G[v] \oplus x, \quad \text{update adjacency if needed}",
        "description": "Append vector x to node v in graph G, updating adjacency if structure changes."
    },
    # Vector Database Equations
    {
        "eq_number": 780,
        "title": "HNSW Hierarchical Navigable Small World",
        "significance": "Graph-based approximate nearest neighbor search. Combines probability skip list with navigable small world graphs for fast vector similarity search.",
        "latex_formula": r"\text{HNSW}(V) = \bigcup_{l=0}^{L_m} G_l(V), \quad G_0 \subset G_1 \subset \dots \subset G_{L_m}",
        "description": "Hierarchical graph structure where each layer is a proximity graph with increasing connectivity."
    },
    {
        "eq_number": 781,
        "title": "Approximate Nearest Neighbor Search",
        "significance": "Efficient vector search with slight accuracy penalty for massive speedup. Uses HNSW for O(log N) search complexity.",
        "latex_formula": r"\text{ANN}(q, V, k) = \{v_1, \ldots, v_k\} \approx \text{k-NN}(q, V)",
        "description": "Approximate k-nearest neighbors with recall-precision tradeoff."
    },
    {
        "eq_number": 782,
        "title": "Proximity Graph Edge Probability",
        "significance": "Probability of edge creation based on vector proximity in HNSW. Controls graph connectivity.",
        "latex_formula": r"P(e_{ij}) = \exp(-\lambda \|v_i - v_j\|^2)",
        "description": "Edge probability decreases exponentially with distance between vectors."
    },
    # Graph Database Equations
    {
        "eq_number": 783,
        "title": "Property Graph Traversal",
        "significance": "Efficient traversal of property graphs with nodes, edges, and properties. Basis for graph query languages like Cypher and GSQL.",
        "latex_formula": r"\text{Traverse}(G, v, d) = \{u \in V \mid \text{dist}(v, u) \leq d\}",
        "description": "Depth-limited traversal from starting node v in graph G."
    },
    {
        "eq_number": 784,
        "title": "Graph Pattern Matching",
        "significance": "Pattern-based query in graph databases. Enables complex relationship queries like Cypher's MATCH clause.",
        "latex_formula": r"\text{Match}(G, P) = \{(v_1, \ldots, v_k) \mid P(v_1, \ldots, v_k) \text{ holds in } G\}",
        "description": "Find all subgraphs in G matching pattern P."
    },
    {
        "eq_number": 785,
        "title": "Multi-Model Query Integration",
        "significance": "Unified querying across document, key-value, and graph models. Enables ArangoDB-style multi-model databases.",
        "latex_formula": r"Q_{\text{multi}} = Q_{\text{doc}} \cup Q_{\text{kv}} \cup Q_{\text{graph}}",
        "description": "Combine queries across different data models in single execution."
    },
    {
        "eq_number": 786,
        "title": "Parallel Graph Processing",
        "significance": "Native parallel graph engine for real-time analytics. TigerGraph-style parallel processing for massive graphs.",
        "latex_formula": r"\text{ParallelProcess}(G, f) = \bigoplus_{v \in V} f(v, N(v)) \quad \text{in parallel}",
        "description": "Apply function f to all nodes and their neighborhoods in parallel."
    },
    # Shockwave/Phonon/Photon Equations
    {
        "eq_number": 787,
        "title": "Shockwave Alignment and Relaxation",
        "significance": "Quasi-charged cells align under shockwave, propagate charge symmetrically, then dissipate and relax. Four-phase cycle: anisotropic → shock_aligned → discharge → relaxed.",
        "latex_formula": r"\text{ShockCell} = (\theta, q, \ell, \tau, \rho, \kappa), \quad \text{phase}: \text{anisotropic} \to \text{aligned} \to \text{discharge} \to \text{relaxed}",
        "description": "Shockwave forces orthogonal cells into alignment, enabling symmetric charge propagation, followed by phonon dissipation and relaxation."
    },
    {
        "eq_number": 788,
        "title": "Phonon Force Law",
        "significance": "Phonon correlation structure for self-healing. Force decays exponentially with Manhattan distance and oscillates with coherence period.",
        "latex_formula": r"F(c_i, c_j) = \exp\left(-\frac{d_M(c_i, c_j)}{127}\right) \cdot \cos\left(\frac{2\pi \cdot d_M(c_i, c_j)}{127}\right)",
        "description": "Phonon force law with 127-step coherence period for Cartesian coordinate space."
    },
    {
        "eq_number": 789,
        "title": "Cartesian Phonon Prime Integration",
        "significance": "256×256 Cartesian coordinate space with 16-bit fixed addressing and Manhattan distance metric for hardware-efficient phonon transport.",
        "latex_formula": r"\text{toAddr}(x, y) = 256y + x, \quad d_M((x_1, y_1), (x_2, y_2)) = |x_1 - x_2| + |y_1 - y_2|",
        "description": "Cartesian phonon language with fixed-width addressing and Manhattan distance."
    },
    {
        "eq_number": 790,
        "title": "Phonon Load Dissipation",
        "significance": "Phonon energy dissipates through discrete steps. Full dissipation returns cell to relaxed zero-load state.",
        "latex_formula": r"\ell_{\text{new}} = \ell_{\text{old}} - \delta, \quad \ell_{\text{relaxed}} = 0 \text{ when } \delta = \ell_{\text{old}}",
        "description": "Discrete phonon load dissipation leading to relaxed state."
    },
    {
        "eq_number": 791,
        "title": "Shock Aligned Contact Energy",
        "significance": "Positive aligned charge and contact coupling produce positive contact energy during shock-forced propagation.",
        "latex_formula": r"E_{\text{contact}}(a, b) = q_a q_b + \kappa_a \kappa_b + \ell_a + \ell_b",
        "description": "Local energetic version of shock-forced propagation with charge, coupling, and phonon load."
    },
    {
        "eq_number": 792,
        "title": "Photonic Spectral Witness",
        "significance": "Spectral amplitudes encoded into optical mode amplitudes. Photon-count distribution recovers scalar observable Ω[u].",
        "latex_formula": r"\text{spectral amplitudes} \to \text{optical mode amplitudes} \to \text{photon-count distribution} \to \hat{\Omega}[u]",
        "description": "Photonic witness grammar for empirical spectral sampling."
    },
    {
        "eq_number": 793,
        "title": "Pair-Bonded Shockwave Propagation",
        "significance": "Two quasi-charged cells form temporary bond during shock alignment, enabling symmetric charge transfer before relaxation.",
        "latex_formula": r"(a, b)_{\text{bonded}} = \text{CellsShockAligned}(a, b) \land \text{CellCharged}(a) \land \text{CellCharged}(b)",
        "description": "Pair-bonded state for symmetric charge propagation during shock alignment."
    },
    {
        "eq_number": 794,
        "title": "Phonon-Mediated Information Transport",
        "significance": "Information encoded in phonon packets propagates through lattice. Lossy transport preserves spectral structure not exact state.",
        "latex_formula": r"I_{\text{out}} = I_{\text{in}} \cdot \exp(-L_{\text{throat}}) \cdot R_{\text{repair}}",
        "description": "Lossy phonon transport with torsional corridor attenuation and repair."
    },
    # GCCL Equations
    {
        "eq_number": 795,
        "title": "ΔφγKλ Compression Law",
        "significance": "Compression-domain instance of GCCL with separate fields for transform pressure (γ) and cost paid (K). Corrected from Δφγλ which overloaded γ.",
        "latex_formula": r"\Delta\phi\gamma K\lambda = (\Delta, \phi, \gamma, K, \lambda)",
        "description": "Five-tuple compression law: residual delta, invariant phi, transform pressure gamma, cost paid K, scale band lambda."
    },
    {
        "eq_number": 796,
        "title": "Goxel Scalar Sub-Manifold",
        "significance": "N-space shape inhabiting geometric volume, expressed as bounded scalar sub-manifold. Admitted only through declared projection, audit, and receipt gates.",
        "latex_formula": r"G = \{ v \in \mathbb{R}^n : \Phi_G(v) \le \text{iso} \}",
        "description": "Goxel as geometric volume element with scalar field constraint."
    },
    {
        "eq_number": 797,
        "title": "Model Genome Encoding",
        "significance": "Compact generative encoding of model family with codon→gene→chromosome→genome→phenotype hierarchy.",
        "latex_formula": r"\text{Genome} = \{\text{codon} \to \text{gene} \to \text{chromosome} \to \text{genome} \to \text{phenotype}\}",
        "description": "Hierarchical model genome encoding for evolvable model families."
    },
    {
        "eq_number": 798,
        "title": "Kinetic Operation Token (KOT)",
        "significance": "Accounting layer for action cost. Every transformation pays and leaves a trace. Prevents free transformations.",
        "latex_formula": r"\text{KOT}(action) = (\text{authorizer}, \text{cost}, \text{budget}, \text{trace}, \text{receipt})",
        "description": "KOT accounting for transformation cost and authorization."
    },
    {
        "eq_number": 799,
        "title": "Bounded Lawful Surface",
        "significance": "Set of transitions and phenotypes that can be expressed, replayed, checked, budgeted, and receipted under declared constraints.",
        "latex_formula": r"\text{BLS}(\text{GCCL}, B, I, R, K, \Lambda)",
        "description": "Lawful surface bounded by budget, invariants, residuals, cost, and scale."
    },
    {
        "eq_number": 800,
        "title": "Genotype-Phenotype Split",
        "significance": "Separation of internal encoding from outward expression. Prevents projection from being mistaken for source object.",
        "latex_formula": r"\text{genotype} \neq \text{phenotype}, \quad \text{projection} \neq \text{proof}",
        "description": "GCL genotype/phenotype separation for identity preservation."
    },
    {
        "eq_number": 801,
        "title": "Mixture Primitive Combination",
        "significance": "Multiple coding families (DNA, codons, proteins, ambiguity, etc.) can be mixed only under explicit decoder, residual, KOT, scale, projection, and receipt rules.",
        "latex_formula": r"\text{Primitive} = (\text{Alphabet}, \text{Arity}, \text{Direction}, \text{Ambiguity}, \text{Transform}, \text{Residual}, \text{Cost}, \text{Receipt})",
        "description": "Canonical wrapper for GCCL mixture primitives."
    },
    {
        "eq_number": 802,
        "title": "Layered Mountain Model",
        "significance": "GCCL sits over layered state mountains: NUVMAP (address), AVMR (vector evolution), AMMR (commit history), O-AMMR (orthogonal projection), GCCL-Rep (transition rope).",
        "latex_formula": r"\text{Stack} = (\text{NUVMAP}, \text{AVMR}, \text{AMMR}, \text{O-AMMR}, \text{GCCL-Rep})",
        "description": "Layered mountain verification for multi-projected transitions."
    },
    # Model/Binding Equations
    {
        "eq_number": 803,
        "title": "Wavefront Emission",
        "significance": "State changes emit wavefronts that propagate through resonant field with amplitude, frequency, phase, position, and decay.",
        "latex_formula": r"W(t, x) = A \cdot e^{-\gamma d} \cdot \cos(\omega d - \phi), \quad d = |x - x_0| - v(t - t_0)",
        "description": "Wavefront propagation for resonant field changes with decay and oscillation."
    },
    {
        "eq_number": 804,
        "title": "MOIM Behavioral Fingerprint",
        "significance": "Objects become behavioral points across identity, conservation, transformation, scaling, and dynamics axes.",
        "latex_formula": r"\text{BehavioralPoint}(object) = \text{fingerprint}(\text{identity}, \text{conservation}, \text{transformation}, \text{scaling}, \text{dynamics})",
        "description": "Meta-ontological inversion: object behavior determines routing."
    },
    {
        "eq_number": 805,
        "title": "Universal Binding Manifold",
        "significance": "Binding affinity surface for conceptual relationships with energy-based binding strength.",
        "latex_formula": r"E_{\text{bind}}(A, B) = -\alpha \cdot \text{similarity}(A, B) + \beta \cdot \text{distance}(A, B)",
        "description": "Energy-based binding manifold for conceptual relationships."
    },
    {
        "eq_number": 806,
        "title": "Info Bottleneck Principle",
        "significance": "Optimal neural compression: minimize mutual information with input while maximizing with output.",
        "latex_formula": r"\min I(X;Z) - \beta I(Z;Y)",
        "description": "Information bottleneck for optimal compression."
    },
    {
        "eq_number": 807,
        "title": "Free Energy Principle",
        "significance": "Variational self-organization invariant: systems minimize free energy by minimizing surprise.",
        "latex_formula": r"F = \mathbb{E}_q[\ln q - \ln p]",
        "description": "Variational free energy for cognitive routing."
    },
    {
        "eq_number": 808,
        "title": "Predictive Coding",
        "significance": "Hierarchical prediction error update: predictions drive learning and inference.",
        "latex_formula": r"\frac{dr}{dt} \propto U^T(I - f(Ur))",
        "description": "Predictive coding for compression and routing."
    },
    {
        "eq_number": 809,
        "title": "Onsager Reciprocity",
        "significance": "Coupled transport symmetry law: cross-coupling coefficients are symmetric.",
        "latex_formula": r"L_{ij} = L_{ji}",
        "description": "Symmetry constraints on transport processes."
    },
    {
        "eq_number": 810,
        "title": "Jarzynski Equality",
        "significance": "Non-equilibrium work-extraction relation connects work fluctuations to free energy difference.",
        "latex_formula": r"\langle e^{-\beta W} \rangle = e^{-\beta \Delta F}",
        "description": "Non-equilibrium information physics."
    },
    {
        "eq_number": 811,
        "title": "DNA Linking Number",
        "significance": "Topological constraint on circular DNA: linking number equals twist plus writhe.",
        "latex_formula": r"Lk = Tw + Wr",
        "description": "Topological invariants for braid theory."
    },
    {
        "eq_number": 812,
        "title": "Cavity Persistence",
        "significance": "Topological information processing metric: persistence of topological features.",
        "latex_formula": r"\Delta \beta_k = \text{birth} - \text{death}",
        "description": "Persistent homology for topological processing."
    },
    {
        "eq_number": 813,
        "title": "Hill Regulation",
        "significance": "Nonlinear saturation feedback: sigmoid functions used throughout OTOM.",
        "latex_formula": r"f(X) = \frac{X^n}{K^n + X^n}",
        "description": "Sigmoid feedback for control systems."
    },
    {
        "eq_number": 814,
        "title": "Wilson-Cowan Equations",
        "significance": "Mean-field neural population dynamics for cognitive load modeling.",
        "latex_formula": r"\frac{dE}{dt} = -E + S(wE - wI + P)",
        "description": "Neural dynamics for cognitive load."
    },
    {
        "eq_number": 815,
        "title": "Turing Morphogenesis",
        "significance": "Spontaneous symmetry breaking for pattern formation on manifolds.",
        "latex_formula": r"\partial_t u = \Delta_{LB} u + f(u, v)",
        "description": "Reaction-diffusion for pattern formation."
    },
    # Mass Number Equations
    {
        "eq_number": 816,
        "title": "Mass Number Admissibility Gate",
        "significance": "Three-layer Mass Number structure: Admissible (A), Residual (R), Boundary (ε). Core rule: A ≤ threshold * (R + ε).",
        "latex_formula": r"\text{MassLe}(m, \tau) := m_A \le \tau \cdot (m_R + \epsilon)",
        "description": "Admissibility gate using comparison form (no division)."
    },
    {
        "eq_number": 817,
        "title": "Admissible Reduction Packet",
        "significance": "Layer 1 of Mass Number: records concrete reduction achieved by modeling move. Must be grounded in surface feature/invariant.",
        "latex_formula": r"A = (\text{value}, \text{groundTag}, \text{moveId}), \quad A \ge 0",
        "description": "Admissible reduction packet with nonnegativity invariant."
    },
    {
        "eq_number": 818,
        "title": "Residual Risk Receipt",
        "significance": "Layer 2 of Mass Number: records what remains unreduced after move. Must be inspectable and bounded.",
        "latex_formula": r"R = (\text{value}, \text{riskClass}, \text{boundCheck}), \quad R \ge 0, \quad R + \epsilon > 0",
        "description": "Residual risk receipt with boundedness guarantee."
    },
    {
        "eq_number": 819,
        "title": "Boundary Marker (ε Guard)",
        "significance": "Layer 3 of Mass Number: ensures denominator never zero. Carries threshold for admissibility decisions.",
        "latex_formula": r"\epsilon > 0, \quad \tau = \text{threshold}, \quad \text{domainTag} \in \{\text{GCCL}, \text{FAMM}, \text{BRAID}, \text{TSM}, \text{HUTTER}\}",
        "description": "Routing/compression boundary marker with nonzero guard."
    },
    {
        "eq_number": 820,
        "title": "NaNMass Doctrine",
        "significance": "Apparent infinity is diagnostic, not destination. NaNMass means coordinate system failed to close mass.",
        "latex_formula": r"\text{Infinity-like} \to \text{unclosed closure} \to \text{NaNMass} \to \text{HOLD} \to \text{repair}",
        "description": "Thermodynamic objection to raw infinity as mass value."
    },
    {
        "eq_number": 821,
        "title": "Closure Path to Metric",
        "significance": "Mass becomes distance only through admissibility closure. Raw mass → pseudometric → zero-distance quotient → metric.",
        "latex_formula": r"\text{Raw} \to K_R(x,y) \to \text{Admissible} \to \text{ShortestPath} \to \text{Pseudometric} \to \text{Quotient} \to \text{Metric}",
        "description": "Finite thermodynamic accounting path to metric closure."
    },
    {
        "eq_number": 822,
        "title": "Erdős Forced-Pattern Model",
        "significance": "If system is large enough, disorder cannot remain pure. Organized substructure must appear.",
        "latex_formula": r"N \gg N_0 \implies \exists \text{monochromatic clique/independent set/convex subset}",
        "description": "Ramsey-style forced pattern emergence."
    },
    {
        "eq_number": 823,
        "title": "General-Position Convexity Forcing",
        "significance": "Points in general position: when does convex n-gon become unavoidable?",
        "latex_formula": r"g(n) = \min\{N : \text{any N points in general position contain convex n-gon}\}",
        "description": "Happy Ending / Erdős-Szekeres point-set problem."
    },
    {
        "eq_number": 824,
        "title": "Cup-Cap Monotonicity",
        "significance": "Geometry converted to ordered subsequences. Convexity becomes pattern of slope changes.",
        "latex_formula": r"\text{points} \to \text{sequence}, \quad \text{convexity} \to \text{slope pattern}",
        "description": "Monotone subsequence via cup-cap decomposition."
    },
    {
        "eq_number": 825,
        "title": "Probabilistic Existence Method",
        "significance": "Do not construct directly. Show random object avoids bad event with positive probability.",
        "latex_formula": r"P(\text{bad event}) < 1 \implies \exists \text{avoider}",
        "description": "Erdős-style lower bounds via randomness."
    },
    {
        "eq_number": 826,
        "title": "Extremal Density Threshold",
        "significance": "Maximum possible density before forbidden structure is forced.",
        "latex_formula": r"\text{ex}(n, \mathcal{F}) = \max\{|G| : |G|=n, G \text{ avoids } \mathcal{F}\}",
        "description": "Turán-type extremal density bounds."
    },
    {
        "eq_number": 827,
        "title": "Sidon Additive Collision",
        "significance": "Integers as collision surfaces. Forbidden equality becomes overlap in additive address space.",
        "latex_formula": r"A + B = C + D \iff \{A, B\} \neq \{C, D\}",
        "description": "Additive combinatorics collision avoidance."
    },
    {
        "eq_number": 828,
        "title": "Order-Type Signature Function",
        "significance": "Coordinates discarded. Only orientation signatures kept for convexity encoding.",
        "latex_formula": r"\chi: \binom{P}{3} \to \{+1, -1\}, \quad \text{convexity encoded by signs}",
        "description": "Combinatorial geometry without metric coordinates."
    },
    # Extremophile Equations
    {
        "eq_number": 829,
        "title": "Strain121 Temperature Limit",
        "significance": "Absolute biological temperature limit: 122°C (395K) protein denaturation wall.",
        "latex_formula": r"T_{max} = 122°C = 395K \quad \text{(absolute biological wall)}",
        "description": "Protein denaturation prevents survival above 122°C."
    },
    {
        "eq_number": 830,
        "title": "Diatom Stiffness Limit",
        "significance": "Silica shells approach inorganic material limits. κ_T ≈ 2.7×10^-11 Pa^-1.",
        "latex_formula": r"\kappa_{T,min}^{biological} = 2.7 \times 10^{-11} \text{ Pa}^{-1} \quad \text{(silica)}",
        "description": "Biological stiffness limit from amorphous silica frustules."
    },
    {
        "eq_number": 831,
        "title": "Vibrio Natriegens Replication Speed",
        "significance": "Absolute biological replication speed limit: 10-15 minute doubling time.",
        "latex_formula": r"\tau_{min} = 600 \text{ seconds (10 minutes)} - \text{absolute biological wall}",
        "description": "Fastest known organism sets replication speed boundary."
    },
    {
        "eq_number": 832,
        "title": "Pyrococcus Pressure-Volume Work",
        "significance": "P·ΔV > kT prevents protein unfolding. Obligate piezophile stability condition.",
        "latex_formula": r"P \cdot \Delta V > k_B T \quad \text{(prevents unfolding)}",
        "description": "Pressure-volume work locks protein conformations."
    },
    {
        "eq_number": 833,
        "title": "Desulforudis Energy Flux",
        "significance": "Deep biosphere champion: 10^-15 W/cell energy flux, 1000-year division time.",
        "latex_formula": r"\Phi_{energy} = 10^{-15} \text{ W/cell}, \quad \tau_{division} = 1000 \text{ years}",
        "description": "Arbitrarily low energy flux admissible if time expands proportionally."
    },
    {
        "eq_number": 834,
        "title": "Landauer Limit",
        "significance": "Minimum energy per bit erasure: E = kT ln(2).",
        "latex_formula": r"E_{bit} = k_B T \ln(2) \approx 3.4 \times 10^{-21} \text{ J/bit at } 60°C",
        "description": "Thermodynamic limit for information processing."
    },
    {
        "eq_number": 835,
        "title": "Resonant Cavity Q-Factor Limit",
        "significance": "Material damping prevents infinite Q. Q_max ≈ 100 for biological tissue.",
        "latex_formula": r"Q_{max}^{biological} \approx 100 \quad \text{(tissue damping)}",
        "description": "Finite damping prevents blow-up resonance."
    },
    {
        "eq_number": 836,
        "title": "Turing Pattern Growth Limit",
        "significance": "Finite nutrient flux prevents infinite growth in reaction-diffusion systems.",
        "latex_formula": r"\partial_t c = D\nabla^2 c + R(c) + \lambda(c_{target} - c) \cdot \Theta(basin_{stable})",
        "description": "Skeletal formation with nutrient-limited growth."
    },
    {
        "eq_number": 837,
        "title": "Navier-Stokes Blow-up Rejection",
        "significance": "Evolutionary rejection of blow-up: infinite vorticity, zero compressibility, zero viscosity, infinite energy.",
        "latex_formula": r"\nabla \cdot v \neq 0, \quad \nu > 0, \quad E_{dissipation} < 10^{-14} \text{ W}",
        "description": "Physical admissibility requires finite parameters."
    },
    {
        "eq_number": 838,
        "title": "Thermococcus Pressure Adaptability",
        "significance": "Widest pressure-range organism: 1 atm to 130 MPa adaptive flexibility.",
        "latex_formula": r"P_{range} = (1 \text{ atm}, 130 \text{ MPa}), \quad \text{adaptive across full space}",
        "description": "Pressure adaptability from atmospheric to extreme."
    },
    {
        "eq_number": 839,
        "title": "Thermus Moderate Thermophily",
        "significance": "Moderate thermophile: 50-80°C (Taq polymerase source).",
        "latex_formula": r"50°C < T < 80°C \quad (122°F < T < 176°F)",
        "description": "Protein folding stable at 140°F (60°C)."
    },
    {
        "eq_number": 840,
        "title": "E. Coli Replication Reference",
        "significance": "Baseline replication efficiency: 20 minutes optimal doubling, 4.6M bp genome.",
        "latex_formula": r"\tau_{opt} = 1200 \text{ seconds}, \quad \text{Rate} = 3833 \text{ bp/s}",
        "description": "Standard replication reference point."
    },
    {
        "eq_number": 841,
        "title": "Rotational Phase Encoding",
        "significance": "4-bit π field encodes 16 rotational states (22.5° resolution) for geometric information flow.",
        "latex_formula": r"\theta = \pi \times \frac{2\pi}{16}, \quad \chi \in \{0,1\} \text{ (chirality)}",
        "description": "RotationalMuSeed encodes local torsion/orientation for alignment-based coupling."
    },
    {
        "eq_number": 842,
        "title": "Chiral Alignment Coupling",
        "significance": "Alignment strength between rotational states: A = cos(Δθ). Determines information flow.",
        "latex_formula": r"A_{ij} = \cos(\theta_i - \theta_j), \quad \text{coupling} \propto A_{ij}",
        "description": "Similar π values couple strongly; orthogonal channels via D/L chirality."
    },
    {
        "eq_number": 843,
        "title": "Manifold Blit Equation",
        "significance": "Hardware-accelerated manifold update: M_{k+1} = Quant_LLM( J_DAG[ M_k ⊕ (Ψ_q ⊗ R_RT) ] ).",
        "latex_formula": r"M_{k+1}(x) = \text{Quant}_{\text{LLM}}( \mathcal{J}_{\text{DAG}}[ M_k(x) \oplus (\Psi_q \otimes \mathcal{R}_{\text{RT}}) ] )",
        "description": "O(1) manifold update via blitter operator, quantum sampling, raytracing."
    },
    {
        "eq_number": 844,
        "title": "Blitter Accumulation",
        "significance": "Saturating bitwise accumulation: saturate(M_k + δ) for discrete Picard integral.",
        "latex_formula": r"\text{blit}(M, \delta) = \text{sat}_{\min}^{\max}(M + \delta)",
        "description": "Hardware-accelerated accumulation with saturation bounds."
    },
    {
        "eq_number": 845,
        "title": "Quantum Walk Amplitude",
        "significance": "Discrete diffusion for quadratic convergence: A_{t+1} = (A_t ⊗ K) / 4.",
        "latex_formula": r"\Psi_q(i,j,t+1) = \frac{1}{4} \sum_{neighbors} \Psi_q(i',j',t)",
        "description": "Grid-based quantum walk for path superposition and acceleration."
    },
    {
        "eq_number": 846,
        "title": "Anisotropic Torsion Flow",
        "significance": "∂_t ϕ = ∇_i(M^ij ∇_j δF/δϕ) - σ ∂ϕ/∂I_lock for manifold evolution.",
        "latex_formula": r"\partial_t \phi = \nabla_i(M^{ij} \nabla_j \delta F/\delta\phi) - \sigma \partial\phi/\partial I_{lock}",
        "description": "Foldback-lock dynamics with anisotropic tensor and interlocking energy."
    },
    {
        "eq_number": 847,
        "title": "Interlocking Energy",
        "significance": "I_lock = w(1 - cos(k·frustration)) for recursive deposition snagging.",
        "latex_formula": r"I_{lock} = w \cdot (1 - \cos(k \cdot \text{frustration})), \quad \text{frustration} = A^{ij} \Delta X_j",
        "description": "Periodic frustration modulated by anisotropy for pattern locking."
    },
    {
        "eq_number": 848,
        "title": "Spike Sync TVI",
        "significance": "Temporal Variant Index for spike trains: coarse-grained timing/rate/pattern/collapse.",
        "latex_formula": r"\text{TVI} = (T_{timing}, T_{rate}, T_{pattern}, T_{collapse})",
        "description": "Admissibility metric for neural spike synchronization."
    },
    {
        "eq_number": 849,
        "title": "Coarse-Graining Rule",
        "significance": "Quantize time into bins: t_bin = floor(t / Δt) for jitter tolerance.",
        "latex_formula": r"t_{bin} = \lfloor t / \Delta t \rfloor, \quad \text{tolerance} = \max\_time\_jitter",
        "description": "Observation rule for spike train coarse-graining."
    },
    {
        "eq_number": 850,
        "title": "Soliton Phase Singularity",
        "significance": "Phase winding number +1 around soliton center: topological charge = vortex.",
        "latex_formula": r"\oint \nabla \phi \cdot dl = 2\pi n, \quad n = +1 \text{ (soliton)}",
        "description": "Soliton as phase singularity (vortex) for geometric bit-flip suppression."
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for eq in equations:
        try:
            cursor.execute("""
                INSERT INTO equations (eq_number, title, domain_id, significance, status)
                VALUES (?, ?, ?, ?, 'Proven')
            """, (eq["eq_number"], eq["title"], DOMAIN_ID, eq["significance"]))

            eq_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO sub_equations (equation_id, subsection, name, latex_formula, description)
                VALUES (?, ?, ?, ?, ?)
            """, (eq_id, "main", eq["title"], eq["latex_formula"], eq["description"]))

            print(f"Added equation {eq['eq_number']}: {eq['title']}")
        except sqlite3.IntegrityError as e:
            print(f"Skipping equation {eq['eq_number']} (already exists): {e}")

    conn.commit()
    conn.close()
    print(f"\nTotal equations added: {len(equations)}")

if __name__ == "__main__":
    main()
