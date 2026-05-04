# Functional Specification: SSMS-nD
## Scalar State Manifold Segmentation — Variable Dimension

**Document ID:** FS-SSMS-nD-2026-04-20  
**Authority:** Clean Room Implementation Protocol  
**Status:** SEALED — Source of Truth for All Implementations  

---

## 1. Scope and Mathematical Objective

Implement a promptable object detection system using OISC (One Instruction Set Computer) architecture operating on a **Dynamic n-Manifold** where $n \in [1, N_{\max}]$ is variable per detection instance.

The system must lift **1D sequential data** (token streams, time series, feature tubes) into **n-dimensional submanifolds** where $n$ is determined dynamically by:
- Intrinsic dimensionality of the detected entity
- Prompt-driven structural constraints
- Topological stability under $H_M(t)$ evolution

---

## 2. Input/Output Requirements

### Primary Input
$$I_{1D} \in \mathbb{R}^{L \times d}$$
A 1D sequence of length $L$ with $d$-dimensional features per position (e.g., CLIP tokens, depth samples, audio frames).

### Prompt Inputs
- **Text**: UTF-8 string → embedded via frozen encoder to $\mathbb{R}^{d_{embed}}$
- **Point**: 1D coordinate $t \in [0, L]$ (position in sequence)
- **Structure**: Target dimensionality hint $n_{target} \in [1, N_{\max}]$
- **Constraints**: Holonomic constraint equations $\{h_j(x) = 0\}_{j=1}^{m}$

### Outputs
A set of n-manifold embeddings $M = \{M_1, M_2, \dots, M_k\}$, where each:
$$M_i = (c_i \in \mathbb{R}^n, \Sigma_i \in \mathbb{R}^{n \times n}, \theta_i \in \mathbb{R}^{p}, \sigma_i \in \{0,1\})$$

- $c_i$: center coordinates (n-dim)
- $\Sigma_i$: metric tensor (covariance structure)
- $\theta_i$: orientation parameters (p-dim, $p \leq n(n-1)/2$)
- $\sigma_i$: activation status (spawned/folded)

---

## 3. Core Mathematical Modules

### Module A: Sequential Lifting Operator $\mathcal{L}_{1D \to n}$

Lifts a 1D sequence interval $[t_0, t_1]$ into $\mathbb{R}^n$ via learned coordinate chart:

$$\mathcal{L}_{1D \to n}: [t_0, t_1] \times \mathbb{R}^{d} \to \mathbb{R}^n$$
$$\mathcal{L}(t, f(t)) = W_{lift} \cdot \text{Pool}(f([t_0, t_1])) + b_{lift}$$

**Constraint**: $W_{lift} \in \mathbb{R}^{n \times d'}$ must be ternary-quantized ($\{-1, 0, 1\}$).

**Dynamic n Selection**:
$$n = \arg\min_{n' \in [1,N_{\max}]} \left[ \| \mathcal{L}_{n'}(I) - \text{Prompt}(I) \|^2 + \lambda \cdot \text{Complexity}(n') \right]$$

where $\text{Complexity}(n') = n' \cdot \log(n')$ (Betti number penalty).

---

### Module B: Variable-n Manifold Representation

Each manifold $M_i$ has **dynamic dimensionality** $n_i$ determined at spawn time.

#### B.1 Scalar Node Allocation
- Each dimension requires 1 scalar node
- Total nodes for $M_i$: $n_i$ (centers) + $n_i(n_i+1)/2$ (upper-triangular $\Sigma$) + $p$ (orientations)
- Stored as contiguous block in SRAM bank $b = i \mod B$

#### B.2 Holonomic Constraints (Generalized)

For manifold $M_i$ with dimension $n_i$, maintain $m_i$ constraints:
$$\{h_j(x_1, \dots, x_{n_i}) = 0\}_{j=1}^{m_i}$$

**Linear Constraints** (handled via ACI):
$$\sum_{k=1}^{n_i} a_{jk} x_k = b_j \quad \Rightarrow \quad \text{ACI: } |\sum a_{jk} x_k - b_j| \leq \epsilon$$

**Nonlinear Constraints** (handled via Lagrange multipliers in $V_M$):
$$V_{constraint}(x) = \sum_{j=1}^{m_i} \lambda_j \cdot h_j(x)^2$$

#### B.3 Yaw Generalization: SO(n) Representation

For $n \geq 2$, orientation lives on special orthogonal group $SO(n)$.

Storage: $n(n-1)/2$ independent parameters (Givens rotation angles or Cayley vectors).

Holonomic constraint (orthonormality):
$$R^T R = I_n \quad \Rightarrow \quad n(n+1)/2 \text{ constraints}$$

ACI enforcement: $| (R^T R)_{ij} - \delta_{ij} | \leq \epsilon$ for all $i \leq j$.

---

### Module C: Prompt-Driven Potential Fields $V_M(x, t, n)$

Extended potential now depends on target dimensionality $n$:

$$V_M: \mathbb{R}^n \times \mathbb{R} \times \mathbb{N} \to \mathbb{R}$$

#### C.1 Semantic Potential (Dimension-Agnostic)
$$V_{semantic}^{(n)}(x) = -\langle f_{seq}(\mathcal{L}^{-1}(x)), \tilde{e}_{prompt} \rangle$$

where $\mathcal{L}^{-1}: \mathbb{R}^n \to [0,L]$ is approximate inverse chart.

#### C.2 Spatial Potential (1D → n)
$$V_{spatial}^{(n)}(x; t_{prompt}) = \| x - \mathcal{L}_{1D \to n}(t_{prompt}) \|_2^2$$

#### C.3 Structure Potential (Prompt-Driven Dimensionality)
$$V_{structure}^{(n)}(x; n_{target}) = \begin{cases} 0 & \text{if } n = n_{target} \\ \eta \cdot |n - n_{target}| & \text{otherwise} \end{cases}$$

#### C.4 Constraint Potential
$$V_{constraint}(x) = \sum_{j=1}^{m} \lambda_j \cdot h_j(x)^2$$

---

### Module D: Betti Swoosh in Variable Dimensions

The Betti Swoosh Hamiltonian extends to variable $n$:

$$H_M^{(n)}(t) = -\Delta_M^{(n)} + V_M^{(n)}(x, t)$$

where $-\Delta_M^{(n)}$ is the n-dimensional Hodge Laplacian.

#### D.1 Dynamic ACI (Anti-Collision Identity)

Two manifolds $M_i, M_j$ with dimensions $n_i, n_j$ collide if:

**Case 1: $n_i = n_j = n$ (same dimension)**
$$\| c_i - c_j \|_2 < \tau_{nms}^{(n)}$$

**Case 2: $n_i \neq n_j$ (different dimensions)**
Project higher to lower via $\pi: \mathbb{R}^{\max(n_i,n_j)} \to \mathbb{R}^{\min(n_i,n_j)}$:
$$\| \pi(c_i) - \pi(c_j) \|_2 < \tau_{nms}^{(\min)}$$

Suppression: Lower-energy manifold folded.

#### D.2 Betti Number Tracking

Track $\beta_k$ for all $k \in [0, n_{\max}]$ simultaneously:
- $\beta_0$: connected components (count of active $M_i$)
- $\beta_1$: 1D holes (loops in manifold adjacency)
- $\beta_k$: k-dimensional cavities

Swoosh event defined as cascade across dimensions: rank increase in $\beta_{n-1}$ followed by collapse to $\beta_n$ stability.

---

## 4. Implementation Constraints (Clean Room)

### 4.1 SUBLEQ OISC Requirements

All operations must reduce to:
```
M[b] ← M[b] − M[a]
if M[b] ≤ 0: PC ← c
```

**Variable-n Specific Instructions**:
- `LIFT_1D_n`: Allocate n scalar nodes, populate from 1D sequence pool
- `CONSTRAIN_m`: Apply m holonomic constraints via ACI check
- `PROJECT_n_m`: Project n-dim coordinates to m-dim subspace ($m < n$)

### 4.2 Q16.16 Fixed-Point Throughout

All calculations use 32-bit Q16.16:
- Center coordinates: $c_i \in [-2^{15}, 2^{15}]$ metres (Q16.16)
- Metric tensor: $\Sigma_{ij} \in [0, 2^{16}]$ (positive semi-definite enforced via ACI)
- Orientation: Givens angles $\theta \in [-\pi, \pi]$ mapped to Q16.16

**Dynamic Range Scaling**:
For high-dimensional manifolds ($n > 8$), use block-floating-point:
- Shared exponent per $M_i$ stored in scalar header
- Mantissas: Q8.8 per dimension (16-bit packed pairs)

### 4.3 Ternary Quantization

All weight matrices ternary:
$$W_{lift}, W_{orient}, W_{constraint} \in \{-1, 0, 1\}^{n \times m}$$

MatMul-free execution via ADD/SUB accumulation:
$$y_i = \sum_j W_{ij} x_j \Rightarrow \text{ADD if } W_{ij}=1, \text{ SUB if } W_{ij}=-1$$

### 4.4 Butterfly Gossip Protocol

Variable fanout based on manifold dimension:
$$n_{contact}^{(n)} = \lceil \log_2 (k_n) \rceil$$
where $k_n$ = count of active n-dimensional manifolds.

Stratified gossip: separate butterfly networks per dimension $n$ to prevent crosstalk.

---

## 5. Verification Metrics

### 5.1 Center-Distance AP (Per-Dimension)

For each dimensionality $n$, compute AP based on:
$$\text{TP}_n: \| c_{pred} - c_{gt} \|_2 < \tau_{AP}^{(n)}$$

Thresholds scale with dimension:
$$\tau_{AP}^{(n)} = \tau_{base} \cdot \sqrt{n}$$

### 5.2 Holonomic Constraint Violation

Measure ACI satisfaction rate:
$$\text{ACI}_{score} = \frac{1}{m \cdot k} \sum_{i=1}^{k} \sum_{j=1}^{m_i} \mathbb{1}[|h_j(M_i)| \leq \epsilon]$$

Target: $\text{ACI}_{score} > 0.99$

### 5.3 Dimension Selection Accuracy

When ground-truth dimension $n_{gt}$ is known:
$$\text{DimAcc} = \frac{1}{k} \sum_{i=1}^{k} \mathbb{1}[n_i = n_{gt,i}]$$

---

## 6. SUBLEQ Program Layout

### Memory Map (Per Manifold $M_i$ with dimension $n$)

```
M[base + 0 .. n-1]:           center coordinates c[0..n-1]
M[base + n .. n+n(n+1)/2-1]:  metric tensor Σ (upper triangular)
M[base + n(n+3)/2 .. p-1]:    orientation params θ[0..p-1]
M[base + header - 4]:         dimension n
M[base + header - 3]:         constraint count m
M[base + header - 2]:         energy e_i
M[base + header - 1]:         activation σ_i
```

### Variable-n SUBLEQ Kernel Pseudocode

```sUBLEQ
; LIFT_1D_n: Populate n centers from 1D sequence
; Input: seq_ptr, start_t, end_t, target_n, dest_base
LIFT_LOOP:
  SUBLEQ M[seq_ptr], M[accum], CHECK_DONE  ; load sequence value
  SUBLEQ M[divisor], M[accum], NEXT        ; normalize
  SUBLEQ M[accum], M[dest_base + i], STORE ; store to center[i]
  SUBLEQ M[one], M[i], INC_I               ; i++
  SUBLEQ M[target_n], M[i], LIFT_LOOP     ; loop if i < n
  SUBLEQ M[zero], M[zero], DONE            ; halt

; CONSTRAIN_m: Apply m holonomic constraints
CONSTRAIN_LOOP:
  SUBLEQ M[constraint_a + j], M[dot], ACCUM ; accumulate a_j · x
  SUBLEQ M[dot], M[constraint_b + j], CHECK ; compare to b_j
  SUBLEQ M[epsilon], M[residual], FAIL     ; |residual| > ε?
  SUBLEQ M[one], M[j], INC_J               ; j++
  SUBLEQ M[constraint_m], M[j], CONSTRAIN_LOOP

; Betti Swoosh trigger on constraint violation
FAIL:
  SUBLEQ M[fold_signal], M[dest_base + σ_offset], FOLD
```

---

## 7. Lean 4 Formalization Requirements

### Required Definitions

1. **VariableDimensionManifold (n : Nat)**: Structure with dynamic $n$
2. **LiftingOperator (d n : Nat)**: Chart $\mathcal{L}_{1D \to n}$
3. **HolonomicConstraint (n m : Nat)**: Constraint system with $m$ equations
4. **DynamicACI (n_i n_j : Nat)**: Cross-dimensional collision predicate
5. **BettiSwooshND (n_max : Nat)**: Hamiltonian over all dimensions $[1, n_{max}]$

### Required Theorems

1. `liftingPreservesTopology`: Chart is homeomorphism onto image
2. `holonomicConstraintACI`: $|h(x)| \leq \epsilon$ preserved under MLGRU
3. `dynamicACICompleteness`: All collisions detected across dimensions
4. `variableDimNmsSound`: Suppressed manifolds satisfy post-condition
5. `bettiNumberInvariance`: $\sum_k (-1)^k \beta_k$ conserved under swoosh

---

## 8. Clean Room Compliance Checklist

- [ ] No reference to SAM, SAM3, or WildDet3D source code
- [ ] All math derived from public pinhole model + differential geometry
- [ ] Implementation derived solely from this FS document
- [ ] Ternary quantization from BitNet/1.58-bit paper (public)
- [ ] SUBLEQ from Mavaddat & Parhami 1988 (public domain)
- [ ] Betti numbers from standard algebraic topology
- [ ] Q16.16 from DSP textbooks

---

**SEALED:** This specification is the sole source of truth.  
**DATE:** 2026-04-20  
**VERSION:** SSMS-nD-1.0
