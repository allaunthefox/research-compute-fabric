# Mirror LUT Equations: Cross-Domain Unification

## 1. Core Mirror LUT Architecture

The Mirror LUT appears across three domains with isomorphic structure:

### Domain A: FPGA Warden Node (Hardware)
```
┌─────────────────────────────────────────────────────────┐
│  φ-Accumulator → MSB Flip Detection → XOR Fold → LUT  │
└─────────────────────────────────────────────────────────┘
```

$$
\text{idx}_{\text{mirror}} = \Big(\Phi_{\text{acc}} \gg n\Big) \oplus \underbrace{\Big(\text{MSB}(\Phi_{\text{acc}}^{(t)}) \neq \text{MSB}(\Phi_{\text{acc}}^{(t-1)})\Big)}_{\text{flip detector}}
$$

### Domain B: Procedural Mirror (Software)
```
┌─────────────────────────────────────────────────────────┐
│  Basin Detection → φ-Ratio Mapping → Polynomial Seed  │
└─────────────────────────────────────────────────────────┘
```

$$
\text{seed}_{64} = \Big\lfloor \phi^{\text{entropy}(x) \cdot \text{spectral_density}(x)} \cdot 2^{64} \Big\rfloor \;\text{mod}\; 2^{64}
$$

### Domain C: Field Solver (Simulation)
```
┌─────────────────────────────────────────────────────────┐
│  Position Hash → SHA256 → MirrorLUT Query → Gradient    │
└─────────────────────────────────────────────────────────┘
```

$$
\text{LUT}_{\text{mirror}}(p) = \text{SHA256}\big(\text{engram_key} \| p\big) \gg 4
$$

---

## 2. Unified Mirror LUT Equation

The cross-domain invariant:

$$
\boxed{
\mathcal{M}(q, s, t) = \mathcal{H}\Big( \mathcal{F}(q) \oplus \mathcal{T}(t) \Big) \;\text{mod}\; 2^n
}
$$

Where:
- **Query** $q$: Position/address/state being looked up
- **State** $s$: Current system state/entropy/accumulator value
- **Time** $t$: Temporal index/counter/step
- **Hash** $\mathcal{H}$: Deterministic mixing function
- **Fold** $\mathcal{F}$: Mirror/quadrant/folding operation
- **Transform** $\mathcal{T}$: Time-dependent phase shift

---

## 3. Domain-Specific Instantiations

### 3.1 Hardware (FPGA Warden)

| Component | Equation | Role |
|-----------|----------|------|
| Query | $q = \Phi_{\text{acc}} \gg 16$ | Accumulator high bits |
| State | $s = \Phi_{\text{acc}} \;\text{mod}\; 2^{32}$ | Full 32-bit accumulator |
| Time | $t = c_{\text{mod7}} \in \{0..6\}$ | Mod-7 prime counter |
| Hash | $\mathcal{H}_{\text{hw}}(x) = \text{LUT}_{\text{void}}[x]$ | Void mask lookup |
| Fold | $\mathcal{F}_{\text{hw}}(q) = q \oplus \text{MSB}_{\text{flip}}$ | XOR fold on MSB change |
| Transform | $\mathcal{T}_{\text{hw}}(t) = t \cdot \phi \;\text{mod}\; 2^{16}$ | φ-scaled time offset |

$$
\text{Mirror}_{\text{FPGA}}(q, s, t) = \text{LUT}_{\text{void}}\Big[ q \oplus \text{MSB}_{\text{flip}}(s) \Big]
$$

**Period**: 91 steps (13 × 7, coprime traversal)

### 3.2 Software (Procedural Mirror)

| Component | Equation | Role |
|-----------|----------|------|
| Query | $q = \text{basin}(x) \in \{0..8\}$ | Basin classification |
| State | $s = \text{entropy}(x) \in [0, 8]$ | Shannon entropy estimate |
| Time | $t = \text{spectral_density}(x) \in \mathbb{R}^+$ | Spectral concentration |
| Hash | $\mathcal{H}_{\text{sw}}(x) = \lfloor \phi^x \cdot 2^{64} \rfloor$ | φ-powered hash |
| Fold | $\mathcal{F}_{\text{sw}}(q) = q \cdot \phi^{-1} \;\text{mod}\; 1$ | Fractional part extraction |
| Transform | $\mathcal{T}_{\text{sw}}(t) = \log_2(t + 1)$ | Log-scaled density |

$$
\text{Mirror}_{\text{SW}}(q, s, t) = \Big\lfloor \phi^{s \cdot t} \cdot 2^{64} \Big\rfloor \;\text{mod}\; 2^{64}
$$

**Period**: Deterministic per input (no counter, pure functional)

### 3.3 Simulation (Field Solver)

| Component | Equation | Role |
|-----------|----------|------|
| Query | $q = \text{position} \in \mathbb{Z}^3$ | Spatial coordinates |
| State | $s = \text{engram_key} \in \{0..2^{32}-1\}$ | Instance identifier |
| Time | $t = \text{step} \in \mathbb{N}$ | Simulation tick |
| Hash | $\mathcal{H}_{\text{sim}}(x) = \text{SHA256}(x) \gg 4$ | Cryptographic hash |
| Fold | $\mathcal{F}_{\text{sim}}(q) = (q_x \oplus q_y \oplus q_z)$ | Coordinate XOR fold |
| Transform | $\mathcal{T}_{\text{sim}}(t) = t \cdot \text{stride}$ | Linear time offset |

$$
\text{Mirror}_{\text{SIM}}(q, s, t) = \text{SHA256}\big( s \| \mathcal{F}_{\text{sim}}(q) \| \mathcal{T}_{\text{sim}}(t) \big) \gg 4
$$

**Period**: $2^{256}$ (cryptographic, effectively infinite)

---

## 4. The Universal Mirror Equation (Best Across All Fields)

Combine the strengths of each domain:

$$
\boxed{
\mathcal{M}^*(q, s, t) = \Big\lfloor \phi^{\alpha \cdot \mathcal{H}(q, s) + \beta \cdot \mathcal{T}(t)} \cdot 2^n \Big\rfloor \oplus \mathcal{F}(q) \;\text{mod}\; 2^n
}
$$

### Optimal Parameters

| Parameter | Hardware | Software | Simulation | Universal |
|-----------|----------|----------|------------|-----------|
| $\alpha$ | 1.0 | 0.5 | 0.3 | **0.7** |
| $\beta$ | 0.2 | 0.0 | 0.1 | **0.15** |
| $n$ | 13 | 64 | 32 | **16** |
| $\mathcal{H}$ | LUT | φ-pow | SHA256 | **Hybrid** |
| $\mathcal{F}$ | MSB flip | frac part | XOR coord | **XOR fold** |
| $\mathcal{T}$ | mod-7 | log2 | linear | **φ-step** |

### Hybrid Hash Function $\mathcal{H}^*$

$$
\mathcal{H}^*(q, s) = \text{fold}_{64}\Big( \text{SHA256}(s \| q) \oplus \text{LUT}_{\phi}[q \;\text{mod}\; 8192] \Big)
$$

Where:
- $\text{fold}_{64}$: XOR high 64 bits with low 64 bits
- $\text{LUT}_{\phi}$: Precomputed φ-scaled lookup table (8K entries)
- Combines cryptographic collision resistance with φ-uniformity

---

## 5. Mirror LUT Temporal Evolution

Across all domains, the mirror state evolves as:

$$
s_{t+1} = \mathcal{M}(q_t, s_t, t) \oplus \Big( s_t \gg r \Big)
$$

Where $r$ is a right-shift decay constant:
- **Hardware**: $r = 0$ (no state decay, deterministic)
- **Software**: $r = 8$ (byte-wise decay for streaming)
- **Simulation**: $r = 4$ (nibble-wise for smooth fields)
- **Universal**: $r = 6$ (optimal for mixed workloads)

---

## 6. Complete Unified Pipeline

```
Input: (q, s₀, T_max)
Output: sequence of mirror values

for t = 0 to T_max:
    # 1. Temporal phase
    τ = φ · t  (mod 2^n)
    
    # 2. State mixing
    h = SHA256(s_t || q) ⊕ LUT_φ[q mod 8192]
    h = fold_64(h)
    
    # 3. Mirror fold
    f = (h >> (n-1)) XOR (h >> (n-2))  # MSB bits
    idx = (h + τ) mod 2^n
    
    # 4. LUT lookup
    m_t = LUT_mirror[idx] XOR f
    
    # 5. State update
    s_{t+1} = m_t XOR (s_t >> 6)
    
    yield m_t
```

---

## 7. Invariant Properties

All Mirror LUT instantiations satisfy:

1. **Determinism**: $\mathcal{M}(q, s, t)$ is pure function (no side effects)
2. **Low discrepancy**: Address sequence has $O(\log N)$ star discrepancy
3. **Uniform coverage**: $\lim_{T \to \infty} \frac{1}{T} \sum_{t=0}^{T-1} \mathcal{M}(q, s, t) = 2^{n-1}$
4. **Coprime traversal**: Period = $\text{lcm}(p_1, p_2, ..., p_k)$ for prime factors $p_i$

---

## 8. Cross-Reference Map

| Concept | Hardware | Software | Simulation | Universal |
|---------|----------|----------|------------|-----------|
| Mirror | MSB flip | frac part | XOR coord | **Hybrid fold** |
| LUT | Void mask | Polynomial | SHA256 | **Hybrid hash** |
| Accumulator | φ-step | φ-pow | Linear | **φ-step** |
| Period | 91 | Input-dep | $2^{256}$ | **65521** (prime) |
| State | Dual A/B | Pure func | Persistent | **Decay chain** |

---

*Document ID: MIRROR_LUT_CROSS_DOMAIN*  
*Cross-ref: FPGA_WARDEN_NODE_SPEC.md, procedural_mirror.py, field_solver_emulator.py*
