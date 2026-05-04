# MATH_MODEL_MAP — Sorted by Domain

**Generated:** 2026-04-19
**Last Updated:** 2026-04-27
**Total Models:** 739 across multiple families (including Neural Development, Cephalopod Distributed, Neurodivergent)
**Sorting:** Grouped by domain, then by model number

**Status:** ⚠️ OUTDATED - This document shows 206 models but current MATH_MODEL_MAP.tsv contains 739 models. Regeneration required.

[BEAUTIFUL_PROVISIONAL - All claims marked as "✅ PROVEN" require Lean theorem verification evidence. All claims marked as "🔄 SORRY" violate AGENTS.md rule "Never Leave sorry in Committed Code" and must be eliminated or quarantined. Per AGENTS.md v2.1, LLM agreement, beauty, elegance, and coherence are not evidence. PROVEN status requires actual Lean theorem proof or #eval witness evidence.]

---

## Layer A: COMPRESSION (14 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 1 | Intrinsic Load | L_I = -Σ p(b\|x) log₂ p(b\|x) | Shannon entropy |
| 2 | Extraneous Load | L_E = BPB(x, w_prior) - BPB*(x) | Suboptimal routing cost |
| 3 | Germane Load | L_G = Σ γˢ · ΔL_E(x_s, t+1) | Learning effort |
| 4 | Routing Load | L_R = Σ c_j·1[f_j] + Σ log₂\|M_l\| | Decision tree cost |
| 5 | Memory Load | L_M = log₂\|E\| + α·1[hit] + ... | Engram burden |
| 6 | Total Load | L_total = λI·l̂I + λE·l̂E - λG·l̂G + ... | Aggregate burden |
| 7 | Efficiency | η = l̂I / (l̂I + l̂E + l̂R + l̂M + ε) | Routing efficiency |
| 8 | Regret-Adjusted | L_ρ = L_total · (1 + ρ/ρ_max) | Performance penalty |
| 9 | Basin-Conditional | L(x\|B) = L_I + L_E(x\|B) + L_R^B | Basin load |
| 10 | MoE Predictor | P_w(x_i) = Σ w_j · P_{m_j}(x_i\|x_{<i}) | Mixture-of-experts |
| 71 | Mutual Information | MI(x) = baseline_bpb - actual_bpb | Structural density |
| 72 | k-NN MI | MI_pred = Σ (w_i·MI_i·S_i) / Σ (w_i·S_i) | Local estimation |
| 73 | Surprise | surprise = log(1 + \|MI_act - MI_pred\|) | Learning trigger |
| 74 | Structure Yield | ρ(x) = MI(x) / (cost(x) + ε) | ROI computation |

**Key Intersection:** A ↔ B (Load → Routing), A ↔ M (Compression → Lean)

---

## Layer B: ROUTING (18 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 16 | Coupling Weight | w_ij = g(Δθ,Δφ,χ_i,χ_j) · h(Δp) | Mu-seed compatibility |
| 17 | Rotational Alignment | g = cos(Δθ·2π/16)·cos(Δφ·π/8)·(1-2\|χ_i-χ_j\|) | Frame match |
| 18 | Spatial Proximity | h = exp(-\|Δp\|²/2σ²)·1_{\|Δp\|<r_max} | Distance decay |
| 19 | Interaction Force | F_ij = w_ij·(a_j-a_i)·Δp_ij/\|Δp_ij\| | Activation flow |
| 20 | Energy Function | E = -½Σ w_ij·a_i·a_j + Σ V(a_i) | Energy landscape |
| 21 | Frame Evolution | θ_i(t+1) = θ_i(t) + α_θ·F_{i,θ} + ξ_θ | Discrete update |
| 22 | Continuous Flow | df_i/dt = -α∇_{f_i}E(f) + ξ(t) | Langevin SDE |
| 23 | Energy Monotonicity | dE/dt = -αΣ\|∇_{f_i}E\|² ≤ 0 | Convergence |
| 75 | Weighted Distance | d(z₁,z₂) = √Σ w_i·((z₁_i-z₂_i)/s_i)² | Scale-normalized |
| 82 | Raw Event Weight | w(e\|V) = ε + spec + pol + int + res + par + pri | Additive score |
| 83 | Spectral Overlap | spec = Σᵢ(V.spectrumᵢ · e.spectrumᵢ) | Compatibility |
| 84 | Polarity Bias | pol = f(sign(V.polarity), e) | Purine/pyrimidine |
| 85 | Interaction Bucket | int = quantize(V.interaction, {-64,0,64}) | 5-level coupling |
| 86 | Resonance Weight | res = min(V.resonanceCount, 4) + 1 | Saturated bonus |
| 87 | Parity Weight | par = 2 if parity(e) = V.parityXor else 1 | XOR check |
| 88 | Normalized Probability | P(e\|V) = w(e) / Σ_{b∈{a,t,g,c}} w(b) | Distribution |
| 119 | Final Score Law | ℓₜ = eₜ·bind(γₜ,modelₜ,gₜ,historyₜ) + λ₁H + ... | Per-step cost |
| 120 | Total Compression | L(X) = Σₜℓₜ + commitments + residual | Global aggregation |

**Key Intersection:** B ↔ C₁ (Routing → Topology), B ↔ M (Routing → Lean)

---

## Layer C₁: TOPOLOGY (24 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 24 | Temporal Weight | w_ij^(τ) = cos(2π(τ_j-τ_i)/16) | Phase coupling |
| 25 | Complete Weight | w_ij = cos(Δθ·22.5°)·cos(Δφ·22.5°)·cos(2πΔτ/16)·... | Full 5-factor |
| 26 | Temporal Force | F_ij^(τ) = w_ij^(τ)·(a_j-a_i)·sgn(τ_j-τ_i) | Past→future |
| 27 | Temporal Evolution | τ_i(t+1) = τ_i(t) + α_τ·F_{i,τ} + ω₀ | Intrinsic clock |
| 28 | Temporal Stability | d/dt(τ_j-τ_i) = 0 | Locked phase |
| 29 | Temporal Entropy | H_τ = -Σ p(τ=k)·log₂ p(τ=k) | Temporal disorder |
| 30 | μ-Seed Cardinality | \|S_μ\| = 8,589,934,592 ≈ 2³³ | Local state |
| 31 | Fractal Occupancy | \|P_occ\| = ρ·N^{d_H} (d_H≈2.7268) | Menger sponge |
| 32 | Total Formal State | \|S_total\| ≈ 2^{5,900,000} | Upper bound |
| 33 | Reachable State | \|S_reachable\| ≈ \|S_total\| / 10²⁹ | Admissible |
| 34 | Packet State | P = (ΔV, Δt, π, τ, χ, C, A) | Wave packet |
| 35 | Throat Condition | Φ_topo(i,j) >> Φ_metric(i,j) | Non-local corridor |
| 36 | Multi-Factor Weight | w_ij = w_p·w_π·w_τ·w_χ·w_topo·w_σ | 6-factor |
| 37 | Holonomy | Hol(γ_loop) = ∮_γ T(p) dp | Phase around loop |
| 38 | Non-Euclidean Distance | d_N = path_length + curvature_penalty + torsion | Topology-aware |
| 94 | Traversal Safety | safe = aperture > 0.001 ∧ stress < 10.0 | Mouth stability |
| 95 | Shortcut Distance | Δd = manifold_dist - throat_length | Distance saved |
| 96 | Throat Efficiency | η = manifold_dist / throat_length | Compression ratio |
| 97 | Traversal Cost | cost = exotic_matter + stability_penalty | Resource |
| 98 | Flux Capacity | flux ≤ max_throughput | Bandwidth |
| 102 | Square-Shell Identity | n = k² + a = (k+1)² - b, a+b = 2k+1 | [REVIEWED - requires Lean theorem verification evidence] |
| 103 | Tip Coordinate Vector | Tip(n) = (ab, a-b) ∈ ℝ² | Embedding |
| 121 | Axial Generator Exhaustivity | {A_k, G_k, C_k, T_k} partition S_k | [REVIEWED - requires Lean theorem verification evidence] |
| 124 | 45° Line Factor | L_45°(n) contains all d\|n | Fermat factorization |

**Key Intersection:** C₁ ↔ C₂ (Topology → Braid), C₁ ↔ F (Topology → Control)

---

## Layer C₂: BRAID (10 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 79 | Cosine Similarity | cos = x·x_ref / (\|x\|·\|x_ref\|) | Reference alignment |
| 80 | Gradient Alignment | align = ∇g_i·∇g_j / (\|∇g_i\|·\|∇g_j\|) | Coherence |
| 81 | Phase Accumulation | phase += Σ y·dx | Work integral |
| 104 | Axial Event Production | A_k, G_k, C_k, T_k generators | PROVEN |
| 105 | Resonance Hub | Tip(m²) = (0, -(2k+1)) | PROVEN |
| 110 | AVMR Commitment | Σ_{k+1}[i] = Φ(Σ_k[2i], Σ_k[2i+1]) | Vectorized Merkle |
| 122 | Tip Mass Resonance | ab_i = ab_j | Hyperbola intersection |
| 123 | Tip Mirror Resonance | (a-b)_i = -(a-b)_j | Shell coupling |
| 131 | **Missing Link ODE** | d/dt(a,b) = (1,-1) + ε·∇J | [BEAUTIFUL_PROVISIONAL - VERIFIED — computational - requires Lean theorem proof evidence; computational verification alone is insufficient per AGENTS.md v2.1] |
| 132 | Universal Law | law(name, invariant, class, statement) | Cross-substrate |

**Key Intersection:** C₂ ↔ D (Braid → Invariants), C₂ ↔ M (Braid → Lean)

---

## Layer D: INVARIANTS (9 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 39 | Trixal Axes | (thermal, work, irreversibility) ∈ [0,1]³ | Thermodynamic space |
| 40 | Shannon Entropy | H = -Σ p·log₂(p) | Information |
| 41 | Kolmogorov Estimate | K_est = (8 - H) / 8 | Compressibility |
| 42 | Thermodynamic Entropy | S_thermo = H + K_est·0.1 | Combined |
| 43 | Entropy Gradient | dS/dt = (S_cur - S_prev) / Δt | Rate of change |
| 44 | Mutual Information | MI = H_initial - H_current | Work extracted |
| 45 | Carnot Efficiency | η = 1 - T_cold/T_hot | Max theoretical |
| 46 | Work Extraction | W_actual = Q_absorbed · η_Carnot · 0.7 | 70% limit |
| 49 | Thermodynamic Depth | depth = ΔS · ln(time_steps) | Complexity |

**Key Intersection:** D ↔ E (Invariants → Verification)

---

## Layer E: VERIFICATION (8 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 61 | Exact Cast Check | int_bits ≤ fp_mantissa + 1 | Safe int→FP |
| 62 | Narrowing Safety | can_safely_narrow(src_bits, signed, dst_mantissa) | Prove safe |
| 63 | RISC-V Latency | fdiv.d=33, fdiv.s=19 → 74% penalty | Dispatch scoring |
| 76 | Force Equilibrium | ΣF_in = ΣF_out at every node | Discrete ∇·σ=0 |
| 77 | Constitutive Law | σ = C:ε | Stress-strain |
| 78 | Global Validity | V(G) = ∧_{v∈V} (ΣF_in = ΣF_out) | Constraint closure |
| 115 | Emission Gate | eᵢ = κ_A ∧ κ_C ∧ J>0 | Closure constraint |
| 116 | Constrained Code | zᵢ = Λ(πᵢ, χᵢ) | LUT emission |

**Key Intersection:** E ↔ F (Verification → Control), E ↔ M (Verification → Lean)

---

## Layer F: CONTROL (13 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 47 | Irreversibility | score = (ΔS + path_asym + time_violation) / 3 | Total |
| 48 | Thermodynamic Length | L = Σ dist_i · (1 + irr_i) | Dissipative trajectory |
| 50 | Arrhenius Factor | AF = exp(E_a / (k_B·T)) | Temp acceleration |
| 51 | Black's Equation | EM_risk = Jⁿ · exp(E_a/(k_B·T)) | Electromigration |
| 52 | Coffin-Manson | damage = (ΔT/threshold)^m · 10⁻⁸ | Fatigue |
| 53 | Landauer Limit | W ≥ k_B·T·ln(2) J/bit | Min energy |
| 54 | Entropy Gen Rate | dS/dt = P_diss / (k_B·T·ln2) bits/s | Computational |
| 55 | 5D Bit-Flip Gradient | G = (T, V_jitter, φ_leak, ε_SEU, dt_clock)/5 | Stress |
| 56 | SEU Bit-Flip Rate | BFR = ε·2^{(T-25)/10}·(1+V_j/1000)·3600 | Flips/hour |
| 57 | Stress Decay | stress(t) = stress₀·e^{-t/300} | 5-min half-life |
| 58 | RUL | RUL = MTBF / (AF·(1+fatigue·0.01+thermal_fat·0.1)) | Lifetime |
| 59 | Homeostatic Injection | surprise = -ln(margin) | Regret signal |
| 60 | QCL Injection | η = (0.5 + window_bonus) · spacing_eff · (1 - stress_pen) | Dispatch |

**Key Intersection:** F ↔ G (Control → Energy), F ↔ M (Control → Lean)

---

## Layer G: ENERGY (26 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 11 | Pressure Piling | P(i) = P₀ · χⁱ (χ ≈ 1.63) | Shock amplification |
| 12 | Hugoniot Temperature | T_peak = T₀ · (P_peak/P₀)^0.65 | Non-isentropic |
| 13 | Pressure Ionization | α(P) = 1 - e^{-k(P - P_MIT)} | Insulator→metal |
| 14 | Energy Recovery | η_net = (W_rec - W_erasure) / W_in | Maxwell's Demon |
| 15 | Q-Factor | Q = (E_flash + E_enthalpy + E_recovered - W_demon) / ... | Global balance |
| 64 | Photon Energy | E = hc/λ = 1.2398/λ_μm eV | Wavelength↔energy |
| 65 | Subband Spacing | ΔE = E_upper - E_lower | QCL structure |
| 66 | Cascade Gain | G = photons_per_e⁻ · n_wells | Photon amp |
| 67 | Temperature Tuning | λ(T) = λ₀ + α·ΔT | Thermal shift |
| 68 | Injection Efficiency | η = (0.5 + window_bonus) · spacing_eff · (1 - stress_pen) | Dispatch |
| 69 | Atmospheric Windows | (3-5)μm, (8-12)μm, (16-20)μm | Lossless propagation |
| 70 | Tuning Range | DFB: 15 cm⁻¹, EC: 400 cm⁻¹ | Spectral adapt |

**Key Intersection:** G ↔ I (Energy → Encoding), G ↔ M (Energy → Lean)

---

## Layer H: ALGEBRA (8 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| — | Geometric Algebra | — | Chirality |
| — | Group Theory | — | Finite fields |
| — | Clifford Algebras | — | Spinors |

**Key Intersection:** H ↔ C₂ (Algebra → Braid), H ↔ G (Algebra → Energy)

---

## Layer I: ENCODING (3 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| — | Voxel Keys | — | Spatial addressing |
| — | Microvoxel Seeds | — | MOF structure |
| — | Bit-Packing | — | Compact representation |

**Key Intersection:** I ↔ M (Encoding → Lean)

---

## Layer J: DYNAMICS (2 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| — | Time Evolution | — | Phase transitions |
| — | Manifold Deformation | — | SHA256 fields |

**Key Intersection:** J ↔ K (Dynamics → Signal)

---

## Layer K: SIGNAL (3 models)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| — | DSP | — | Filter design |
| — | FFT | — | Spectral analysis |
| — | Bracket Braid | — | Dynamics |

**Key Intersection:** K ↔ C₂ (Signal → Braid)

---

## Layer L: APPLICATION (1 model)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| — | FEA | — | Engineering models |

**Key Intersection:** L ↔ G (Application → Energy)

---

| 132 | **Universality Class** | KPZ, Percolation, Ising, Mott, Diffusion | Substrate dynamics |
| 133 | **Scaling Invariant** | exponent ρ, name, description | Renormalization |
| 134 | **Universal Law** | law(name, invariant, class, statement) | Cross-substrate |
| 135 | **No Universality Loss** | cd.preservedUnderProjection ∧ cd.preservedUnderCollapse ∧ cd.preservedUnderEvolution | [REVIEWED - requires Lean theorem verification evidence] |

---

## Layer M: LEAN_SEMANTICS (66 models)

### M.1: Core Formalization

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 89 | uSeed Germination Cost | cost = 1.0 - activation | Energy to activate |
| 90 | Colony Health | health = mature / total | Success ratio |
| 91 | Manhattan Adjacency | adjacent = Σᵢ\|p₁ᵢ - p₂ᵢ\| ≤ threshold | Proximity |
| 92 | Seed Germination | state' = activating if energy > activation | Transition |
| 93 | Scaffold Connected | connected = links > 0 ∧ seeds > 1 | Integrity |

### M.2: CMYK Frequency

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 99 | Channel Frequency | f(ch, n) = base(ch) + 20·n | 16-bin encoding |
| 100 | Bank Membership | inBank = base ≤ f ≤ base+300 ∧ (f-base) mod 20 = 0 | Valid check |
| 101 | Round-trip Decode | decode(encode(p)) = p | ✅ PROVEN |

### M.3: AVMR Core

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 102 | Square-Shell | n = k² + a, a+b = 2k+1 | ✅ PROVEN |
| 103 | Tip Coordinate | Tip(n) = (ab, a-b) | Embedding |
| 104 | Axial Events | A_k, G_k, C_k, T_k | ✅ PROVEN |
| 105 | Resonance Hub | Tip(m²) = (0, -(2k+1)) | ✅ PROVEN |
| 106 | Standing-Wave | Ψ_i(n_i - d) = α_d · χ_i | Echo field |
| 107 | Interaction Score | J(n) = ab·F_m + (a-b)·F_p + ⟨χ,F_c⟩ | Coupling |
| 108 | Left-Right Transduction | (n,k,a,b) ↦ ... ↦ (S,P,G) | Pipeline |
| 109 | Temporal Error-Coding | t(n) = nR + τ | 8-slot |
| 110 | AVMR Commitment | Σ_{k+1}[i] = Φ(Σ_k[2i], Σ_k[2i+1]) | Merkle |

### M.4: Unified Compression

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 111 | Pulse Generation | πᵢ = G_θ(n,k,a,b,AVMR) | Structured pulse |
| 112 | Standing-Wave Field | F(n) = Σ Ψᵢ · α_d | Echo weights |
| 113 | 3-Point Contact | χᵢ = (κ_A, κ_B, κ_C) | Detection |
| 114 | Interaction Score | J(n) = ... | Gating |
| 117 | Unified Compression | L(X) = Σᵢ bind(zᵢ) | Pipeline |
| 118 | Square Pulse | Tip(m²) = (0, -(2k+1)) | Degenerate |

### M.5: Final Score Law

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 119 | Final Score Law | ℓₜ = eₜ·bind(...) + λ₁H + λ₂d + λ₃D - λ₄G | Per-step |
| 120 | Total Compression | L(X) = Σₜℓₜ + commitments + residual | Global |

### M.6: Agent F1/F2/F3 Tier Proofs

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 121 | Axial Generator Exhaustivity | {A_k,G_k,C_k,T_k} exhaust S_k | ✅ PROVEN |
| 122 | **Tip Mass Resonance** | ab_i = ab_j | [⚠️ VIOLATES AGENTS.md - 🔄 SORRY marker violates "Never Leave sorry in Committed Code" rule. Must be eliminated or quarantined with TODO(lean-port) ticket and human sign-off.] |
| 123 | **Tip Mirror Resonance** | (a-b)_i = -(a-b)_j | [⚠️ VIOLATES AGENTS.md - 🔄 SORRY marker violates "Never Leave sorry in Committed Code" rule. Must be eliminated or quarantined with TODO(lean-port) ticket and human sign-off.] |
| 124 | **45° Line Factor** | L_45°(n) contains d\|n | [⚠️ VIOLATES AGENTS.md - 🔄 SORRY marker violates "Never Leave sorry in Committed Code" rule. Must be eliminated or quarantined with TODO(lean-port) ticket and human sign-off.] |
| 125 | Φ_axial | (n,k,a,b) ↦ e | ✅ Implemented |
| 126 | Φ_tip | (e,a,b) ↦ (e, T) | ✅ Implemented |
| 127 | Φ_echo | (n,e,T) ↦ F | ✅ Implemented |
| 128 | Φ_time/color | (n,e,T,F) ↦ (τ,γ) | ✅ Implemented |
| 129 | Φ_group | {C_i} ↦ κ | ✅ Implemented |
| 130 | Φ_translate | κ ↦ S_neuro | ✅ Implemented |
| 131 | **Missing Link ODE** | d/dt(a,b) = (1,-1) + ε·∇J | [⚠️ VIOLATES AGENTS.md - 🔄 SORRY marker violates "Never Leave sorry in Committed Code" rule. Must be eliminated or quarantined with TODO(lean-port) ticket and human sign-off.] |

### M.7: Genetic Code (NCBI Table 1)

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 136 | **AminoAcid Type** | 20 AA + stop | ✅ Implemented |
| 137 | **Codon Structure** | (EventType)³ | ✅ Implemented |
| 138 | **Genetic Code** | Codon → AminoAcid | [REVIEWED - requires Lean theorem verification evidence] |
| 139 | **Start Codon** | AUG → Met | [REVIEWED - requires Lean theorem verification evidence] |
| 140 | **Stop Codons** | 3 stops | [REVIEWED - requires Lean theorem verification evidence] |
| 141 | **Codon Degeneracy** | 1,2,3,4,6 | ✅ Implemented |
| 142 | **Degeneracy Sum** | Σ = 64 | [REVIEWED - requires Lean theorem verification evidence] |
| 143 | **AUG is Start** | isStartCodon(AUG) | [REVIEWED - requires Lean theorem verification evidence] |
| 144 | **Stop Count** | 3 | [REVIEWED - requires Lean theorem verification evidence] |

### M.8: Information-Theoretic Properties

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 145 | **Genetic Code Entropy** | H ≈ 4.2 bits | Information content |
| 146 | **Max Entropy** | log₂(21) ≈ 4.39 bits | Theoretical capacity |
| 147 | **Coding Efficiency** | H_actual / H_max ≈ 96% | [CALIBRATED_ENGINEERING_DELTA - requires baseline comparison evidence with mathematical proof; 96% claim needs formal verification evidence] |
| 148 | **Silent Mutation P** | Error correction rate | [CALIBRATED_ENGINEERING_DELTA - requires baseline comparison evidence with mathematical proof] |
| 149 | **Channel Capacity** | C ≈ 5.9 bits | [CALIBRATED_ENGINEERING_DELTA - requires baseline comparison evidence with mathematical proof] |
| 150 | **Compressibility** | 27% redundancy | [CALIBRATED_ENGINEERING_DELTA - requires baseline comparison against industry standards with SI standard compression ratio] |
| 151 | **Kolmogorov Bound** | ~200 bits | Description length |
| 152 | **Self-Describing** | true | Bootstrap closure |
| 153 | **Frame Invariance** | true | Sync feature |
| 154 | **Universal Code** | true | Cross-species |
| 155 | **Error Detection** | 4.7% | Stop checksum |

### M.9: Species-Specific Analysis

| # | Model | Equation | Purpose |
|---|-------|----------|---------|
| 156 | **Species Type** | 7 species | Taxonomy |
| 157 | **Codon Frequency** | p_s(c) | Usage bias |
| 158 | **Species Entropy** | H_s | [REVIEWED - requires Lean theorem verification evidence] |
| 159 | **RSCU** | obs/exp | Synonymous usage |
| 159a | **RSCU Non-Negativity** | rscu ≥ 0 | [REVIEWED - requires Lean theorem verification evidence] |
| 159b | **RSCU Sum Synonymous** | Σ RSCU = d | [REVIEWED - requires Lean theorem verification evidence] (human) |
| 160 | **Optimal Code Length** | -log₂(p) | Huffman codes |
| 161 | **Kraft Sum** | Σ 2^(-L(c)) | [REVIEWED - requires Lean theorem verification evidence] |
| 162 | **CAI Bounds** | 0 ≤ CAI ≤ 1 | [REVIEWED - requires Lean theorem verification evidence] |
| 163 | **Species Better Than Generic** | n*H_s/8 < n*6/8 | [REVIEWED - requires Lean theorem verification evidence] |
| 164 | **Info Gain** | 6-H_s | Compressibility |
| 165 | **Portable Codons** | {CTG,GAG,AAG} | Conserved |
| 166 | **Portability Score** | mean/var | Cross-species |

---

## Cross-Domain Collapse Lines

| Concept | Domains | Expression |
|---------|---------|------------|
| **Q16.16** | A, C₁, C₂, D, E, F, G, M | Universal numeric |
| **Shell State** | C₁, C₂, H, I, M | (n,k,a,b) encoding |
| **Contact (κ)** | C₁, F, M | Closure constraint |
| **Resonance** | C₂, G, K, M | Spectral degeneracy |
| **bind()** | B, E, M | Lawful translation |

---

## Statistics

| Layer | Models | % of Total | Proven | Formalizing | Missing |
|-------|--------|------------|--------|-------------|---------|
| A | 14 | 7.7% | — | — | — |
| B | 18 | 9.9% | — | — | — |
| C₁ | 24 | 13.3% | 2 | 1 | 1 |
| C₂ | 10 | 5.5% | 1 | 3 | 1 |
| D | 9 | 5.0% | — | — | — |
| E | 8 | 4.4% | — | — | — |
| F | 13 | 7.2% | — | — | — |
| G | 26 | 14.4% | — | — | — |
| H | 8 | 4.4% | — | — | — |
| I | 3 | 1.7% | — | — | — |
| J | 2 | 1.1% | — | — | — |
| K | 3 | 1.7% | — | — | — |
| L | 1 | 0.6% | — | — | — |
| **M** | **68** | **32.6%** | **30** | **27** | **13** |
| **Total** | **208** | **100%** | **28** | **48** | **16** |

---

**Layer M (Lean Semantics) concentration:** 68 of 208 models (32.7%)
**Auto-proven in Layer M:** 30 of 68 (44%)
**Manual work remaining:** 40 of 67 (60%)
