# Information Manifold Taxonomy — Canonical Specification

**Date:** 2026-05-04  
**Status:** CANONICAL BASE (unifies 4 previously-separate manifold concepts)  
**Replaces:** Assorted manifold descriptions scattered across `EntropyMeasures.lean`, `CANONICAL_CORE_V1.md`, `genus3_framework.md`, `BEHAVIORAL_MANIFOLD_PIPELINE.md`  
**Scope:** What "the information manifold" IS, how its four specializations relate, and what remains to be proven.

---

## 0. The Fundamental Object

> **The Information Manifold** is a triple $(\mathcal{M}, g, \nabla)$ where:
> - $\mathcal{M}$ is a smooth manifold whose points represent **information states**
> - $g$ is a **Riemannian metric** (the Fisher-Rao metric by default)
> - $\nabla$ is an **affine connection** (admitting torsion $T$ in the physicalized version)

**Points in $\mathcal{M}$** are probability distributions $p(\cdot \mid \theta)$ over a base space $\mathcal{X}$, parameterized by $\theta \in \mathbb{R}^n$. When $\mathcal{X}$ is finite, $\mathcal{M}$ is a statistical manifold; when $\mathcal{X}$ is continuous, $\mathcal{M}$ is an infinite-dimensional Fréchet manifold whose finite-dimensional projections are the objects of study.

**The metric** is the Fisher information metric:
$$g_{ij}(\theta) = \mathbb{E}_{p(x\mid\theta)}\!\left[\frac{\partial \log p}{\partial \theta_i} \frac{\partial \log p}{\partial \theta_j}\right] = \int p(x\mid\theta) \, \partial_i \log p \, \partial_j \log p \; d\mu(x)$$

This is the **unique** Riemannian metric invariant under sufficient statistics (Chentsov's theorem, 1972). It is the natural geometry of information.

**The connection** is the Levi-Civita connection $\nabla^{LC}$ by default. When torsion is admitted (the physicalized version), the connection becomes $\nabla = \nabla^{LC} + T$ where $T$ is the torsion tensor. Torsion measures the **misalignment between information flow and the manifold's geodesics** — it is the geometric quantity corresponding to "frustration" in the FAMM vocabulary.

---

## 1. Taxonomy: Four Specializations of One Manifold

**These are NOT four separate manifolds.** They are four specializations / chart-restricted views / discretizations of the same object.

| # | Specialization | Manifold $\mathcal{M}$ | Metric $g$ | Connection $\nabla$ | Purpose |
|---|---|---|---|---|---|
| **S1** | **Fisher-Geometric** | Statistical manifold with optional genus-3 topological constraint | Fisher-Rao | Levi-Civita (torsion-free) | Classify laws of physics as local normal forms; derive QM commutation relations from symplectic topology |
| **S2** | **Alcubierre Warp** | 2D submanifold chart $(\tau, H)$ where $\tau$ = proper time, $H$ = entropy coordinate | Induced from Fisher on full $\mathcal{M}$; Lorentzian $d\mathcal{I}^2 = -d\tau^2 + (dH - \beta d\tau)^2$ | Levi-Civita (torsion emerges from shift vector $\beta$) | Model the compression frontier as a warp bubble; compute effective compression velocity |
| **S3** | **Sovereign Informatic (SIM)** | Full $\mathcal{M}$ with anisotropic tensors, torsion landscape, hyperfluid phase field $\phi$ | Fisher-Rao + anisotropic perturbation $A^{ij}$ | $\nabla = \nabla^{LC} + T$ (torsion active) | Physicalized evolution dynamics; foldback-lock gradient flow; hardware-attestable state transitions |
| **S4** | **Behavioral (MOIM)** | Discrete lattice approximation of $\mathcal{M}$ with Genome18 addressing ($262\,144$ states) | Induced discrete metric (Hamming + engram proximity) | Discrete gradient (finite differences) | Mathematical discovery engine; bootstrap cascade; FPGA-targetable search |

### Relationship Diagram

```
                    ┌──────────────────────────────┐
                    │   INFORMATION MANIFOLD (M,g,∇) │
                    │   Fisher-Rao metric            │
                    │   Points = prob. distributions  │
                    └──────────┬───────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
   │ S1: Fisher- │    │ S3: SIM      │    │ S4: MOIM     │
   │ Geometric   │    │ (Physicalized)│    │ (Discrete)   │
   │ T = 0       │    │ T ≠ 0        │    │ Lattice      │
   │ Genus-3 opt │    │ Anisotropic   │    │ Genome18     │
   └──────┬──────┘    └──────┬───────┘    └──────────────┘
          │                  │
          │    projects to    │
          └────────┬─────────┘
                   ▼
          ┌──────────────┐
          │ S2: Alcubierre│
          │ Warp Metric   │
          │ 2D chart (τ,H)│
          └──────────────┘
```

**Key claims:**
- S1 is the **abstract mathematical layer** (no physics, no hardware)
- S3 is the **physicalized layer** (adds torsion, anisotropy — what the hardware actually computes)
- S2 is a **2D projection** of S3 (a specific chart useful for compression frontier analysis)
- S4 is a **discrete lattice approximation** of S3 (what the FPGA actually executes)

**Unresolved:** Does S3 reduce to S1 when $T \to 0$ and $A^{ij} \to g^{ij}$? This is conjectured but not yet proven.

---

## 2. Detailed Specifications

### S1: Fisher-Geometric Information Manifold

**Files:** `6-Documentation/docs/avmr/genus3_framework.md`, `0-Core-Formalism/lean/Semantics/Semantics/Extensions/FisherGeometricAdaptationLaws.lean`, `6-Documentation/docs/avmr/c_info_derivation.md`

**Mathematical structure:**
- Base manifold: $(\mathcal{M}, g^{\text{Fisher}})$ with $\dim \mathcal{M} = n$ (number of model parameters)
- Topological constraint: $\mathcal{M}$ is taken to have genus 3 (connected sum of three tori). This is an **additional hypothesis**, not a consequence of the Fisher metric.
- Homology: $H_1(\mathcal{M}; \mathbb{Z}) \cong \mathbb{Z}^6$ with basis $\{a_1, b_1, a_2, b_2, a_3, b_3\}$
- Symplectic form: $\omega(a_i, b_j) = \delta_{ij}$, $\omega(a_i, a_j) = \omega(b_i, b_j) = 0$

**What is proven:**
- A genus-3 surface has the stated homology and intersection form. This is standard algebraic topology.
- The Fisher metric is the unique Riemannian metric on the space of probability distributions invariant under sufficient statistics (Chentsov's theorem). This is a known result.

**What is conjectured (marked `[BEAUTIFUL_PROVISIONAL]` in source):**
- [B.P.] The three handle pairs correspond to three spatial modes that project to observed 3D space.
- [B.P.] Quantization of the symplectic form yields canonical commutation relations $[\hat{x}_i, \hat{p}_j] = i\hbar\delta_{ij}$.
- [B.P.] The Fisher metric on $\mathcal{M}$, in an appropriate semiclassical limit, reduces to the Schrödinger equation.
- [B.P.] $c$ (speed of light) is the maximum information processing rate through all three handles simultaneously.
- [B.P.] The 75+ physics formulas cluster into 6 interior shape types (ORBITAL, DIFFUSIVE, INVERSE-SQUARE, QUANTIZED, CONSTRAINT-BALANCE, GEOMETRIC).

**Required for upgrade from [B.P.] to proven:**
1. A proof that the genus-3 topology is forced by something (not imposed as a hypothesis)
2. A derivation of the Schrödinger equation from the Fisher metric geodesic equation in an appropriate limit
3. A derivation of the Born rule from the natural measure on $\mathcal{M}$
4. A rigorous classification of the 75 formulas into shape types (not just clustering by inspection)

### S2: Alcubierre Virtual Warp Metric

**Files:** `CANONICAL_CORE_V1.md` (§7), `0-Core-Formalism/lean/Semantics/Semantics/VirtualWarpMetric.lean`, `0-Core-Formalism/lean/Semantics/Semantics/EntropyMeasures.lean` (§2.6, §2.12)

**Mathematical structure:**
- Chart: $(\tau, H)$ where $\tau$ = proper time (compression clock cycles), $H$ = entropy displacement (total bits in current context buffer)
- Metric: $d\mathcal{I}^2 = -d\tau^2 + (dH - v_{\text{eff}} \cdot f(x_i) \cdot \Omega_{\text{opcode}} \cdot d\tau)^2$
- Warp function: $f(x_i) = \frac{1}{1 + e^{-\kappa \cdot \Phi_{sss}(x_i)}} \cdot \Omega_{\text{opcode}}$
- Effective velocity: $v_{\text{eff}} = \frac{v_{\text{local}}}{1 - \phi(s_{\text{probe}}, x)}$

**What is proven:**
- The metric has signature $(-,+)$ and $\det(g) = -1$, so it is non-degenerate. This is a straightforward computation (C2 audit, 2026-04-02).
- The stability condition $\Phi_{sss} \cdot \Omega_{\text{opcode}} > 0$ is necessary for the bubble to hold.

**What is conjectured:**
- $v_{\text{eff}}$ can exceed $v_{\text{local}}$ arbitrarily when waveprobe coherence $\phi \to 1$.
- The waveprobe horizon $\|\nabla L_E\| \cdot \ell_{\text{probe}} > \theta_{\text{horizon}}$ bounds the effective velocity.

**Relationship to S1 and S3:**
S2 is a **2D submanifold chart** of the full SIM (S3). The $H$ coordinate is the entropy scalar; $\tau$ is the clock parameter along the flow. The warp function $f(x_i)$ is a sigmoid over the SSS potential $\Phi_{sss}$ — which is itself a function on the full manifold. The induced metric on the $(\tau, H)$ chart from the full Fisher metric on $\mathcal{M}$ has not yet been computed.

### S3: Sovereign Informatic Manifold (SIM)

**Files:** `0-Core-Formalism/lean/Semantics/Semantics/ManifoldFlow.lean`, `ManifoldPotential.lean`, `ManifoldStructures.lean`, `EntropyMeasures.lean` (primary), `ManifoldTopology.lean`

**Mathematical structure:**
- Governing equation (from `ManifoldFlow.lean`):
  $$\begin{aligned}
  \partial_t \phi &= \nabla_i(M^{ij} \nabla_j \delta F/\delta \phi) - \sigma \frac{\partial \phi}{\partial I_{\text{lock}}} \\
  \partial_t X^A &= -\Gamma^A_{BC} \partial_i X^B \partial_i X^C - \Lambda^{AB}(X^B - X_0^B) - \frac{\delta F}{\delta X^A} + \tau T^A
  \end{aligned}$$
- $M^{ij}$ = anisotropic tensor (encodes directional information flow preferences)
- $T^A$ = torsion vector (encodes manifold twist)
- $F[\phi, X]$ = free energy functional
- $I_{\text{lock}}$ = foldback-lock invariant (prevents runaway evolution)

**Tensor fields defined (all Q16.16):**
- `AnisotropyTensor` (A^ij): directional coupling
- `MetricTensor` (g_ij): local geometry
- `TorsionTensor` (T^k_ij): manifold twist
- `PhaseVec`: embedding coordinates X^A
- `ManifoldPoint`: combined state (φ, X, g, T, A)

**What is implemented:**
- The tensor structures are defined
- The gradient flow equations are stated
- The `bind` primitive connects states under a chosen metric
- No convergence theorems, no existence/uniqueness proofs for the PDE system

**What is missing:**
- The relationship between $M^{ij}$ and the Fisher metric $g^{ij}_{\text{Fisher}}$. Are they the same? Is $M^{ij} = g^{ij} + \text{perturbation}$?
- A proof that the foldback-lock term $\sigma \partial \phi / \partial I_{\text{lock}}$ is sufficient to prevent divergence.
- Numerical evidence that the gradient flow actually converges for non-trivial initial conditions.

### S4: Behavioral / MOIM Manifold

**Files:** `6-Documentation/docs/semantics/BEHAVIORAL_MANIFOLD_PIPELINE.md`, `0-Core-Formalism/lean/Semantics/Semantics/SovereignMathModel.lean` (in archive/MOIM recovery)

**Mathematical structure:**
- Discrete lattice with Genome18 addressing: $6 \times 3$-bit bins → 18-bit address ($262\,144$ states)
- Representation cascade: Tile → Cube → ... → Triangle → Tile (uplift and descent)
- φ⁴ lattice field theory engine (quantum foam)
- Course-grain stochastic shrinking (FAMM ban map)
- UberLUT: self-expanding address space

**What is implemented:**
- ~5,025 lines of Lean 4 (in MOIM archive, not yet in active Semantics/)
- ~1,580 lines of Verilog (FPGA-targetable)
- The Genome18 encoder is extracted and verified
- The cascade idempotence is stated but not proven

**Relationship to S3:**
S4 is a **discrete lattice approximation** of S3. The Genome18 address space is a $262\,144$-point sampling of the continuous manifold $\mathcal{M}$. The representation cascade (Tile → ... → Triangle) is a discrete analog of the geometric flow in S3. The φ⁴ foam is a lattice regularization of the continuous field $\phi$ in S3.

---

## 3. The `bind` Primitive: Unifying Interface

All four specializations interact through a single primitive:

$$\operatorname{bind}(a, b, g) : A \times B \times \operatorname{Metric} \to \mathbb{R}$$

where the result is the **cost of lawful assemblage** between $a$ and $b$ under metric $g$.

### Specializations of `bind`

| Specialization | What is bound? | Metric $g$ | Example |
|---|---|---|---|
| S1 (Fisher) | Probability distributions $p$, $q$ | KL divergence, Fisher-Rao distance | `bind(p, q, KL)` = $D_{KL}(p\|q)$ |
| S2 (Alcubierre) | Manifold states at different $\tau$ | Warp metric $d\mathcal{I}^2$ | `bind(state_t, state_{t+1}, warp)` = proper distance along bubble |
| S3 (SIM) | Manifold points with torsion | Anisotropic + torsion-corrected Fisher | `bind(μ_i, μ_j, angular_proximity_metric)` |
| S4 (MOIM) | Genome18 states | Hamming distance + engram proximity | `bind(tile_i, tile_j, engram_metric)` |

### Proposed Axioms (to be formalized)

A `bind`-compatible metric must satisfy:

1. **Associativity:** $\operatorname{bind}(\operatorname{bind}(a, b, g), c, g) = \operatorname{bind}(a, \operatorname{bind}(b, c, g), g)$
2. **Identity:** $\exists\, e_g : \operatorname{bind}(a, e_g, g) = a$ for all $a$ in the domain
3. **Metric monotonicity:** $g_1 \leq g_2$ (in Loewner order) $\implies \operatorname{bind}(a, b, g_1) \geq \operatorname{bind}(a, b, g_2)$
4. **Triangle inequality:** $\operatorname{bind}(a, c, g) \leq \operatorname{bind}(a, b, g) + \operatorname{bind}(b, c, g)$
5. **Torsion awareness:** $\operatorname{bind}(a, b, g) \neq \operatorname{bind}(b, a, g)$ when $T \neq 0$

Axioms 1-4 are standard for a metric. Axiom 5 is the distinguishing feature: `bind` is NOT symmetric when torsion is active. This is what makes the SIM (S3) different from the Fisher manifold (S1).

---

## 4. Cross-Reference: Lean Module → Manifold Specialization

| Lean Module | Specialization | Status |
|---|---|---|
| `Extensions/FisherGeometricAdaptationLaws.lean` | S1 | Defined; limited theorems |
| `VirtualWarpMetric.lean` | S2 | Defined; stability condition proven |
| `EntropyMeasures.lean` (§2.6-2.8) | S2, S3 | Structures defined; no composition proofs |
| `ManifoldFlow.lean` | S3 | Governing PDE stated; structures defined |
| `ManifoldPotential.lean` | S3 | Topology taxonomy (basin, ridge, throat, etc.) |
| `ManifoldStructures.lean` | S3 | Base types (maps, charts, atlases) |
| `ManifoldTopology.lean` | S3 | Genus, handles, cycles |
| `VirtualGPUTopology.lean` | S3 | GPU mapping of manifold states |
| `QuantumManifoldGeometry.lean` | S3 | QM-on-manifold structures |
| `GeometricTopology.lean` | S3 | General geometric topology primitives |
| `GoldenSpiralManifold.lean` | S3 | Golden-ratio spiral submanifold |
| `TriangleManifold.lean` | S3 | Triangular tessellation of manifold |
| `CollectiveManifoldInterface.lean` | S3 | Multi-agent manifold interaction |
| `S3CGeometry.lean` | S3 | Shell/topological codec geometry |
| `MOIM_*.lean` (in archive/MOIM recovery) | S4 | Discrete lattice; not yet in active Semantics/ |
| `Genome18.lean` | S4 | Discrete addressing scheme |
| `CooperativeLUT.lean` | S4 | LUT-based manifold navigation |

---

## 5. Verification Queue: Cross-Layer Theorems

The following theorems would establish formal relationships between the specializations. None are currently proven.

| Theorem | Statement | Priority |
|---|---|---|
| **T1: SIM reduces to Fisher** | When $T \to 0$ and $A^{ij} \to g^{ij}$, the SIM gradient flow (S3) reduces to Fisher-Rao geodesic flow (S1) | HIGH |
| **T2: Alcubierre chart consistency** | The induced metric on the 2D $(\tau, H)$ chart from the full Fisher metric on $\mathcal{M}$ equals the Alcubierre warp metric (S2) | HIGH |
| **T3: MOIM approximates SIM** | The discrete Genome18 lattice (S4) approximates the continuous SIM (S3) with error $O(2^{-18})$ per dimension | HIGH |
| **T4: Genus-3 forced** | Under appropriate constraints (3D base space, information preservation), the information manifold MUST have genus ≥ 3 | MEDIUM |
| **T5: InfoReynolds ↔ Canal** | The laminar/turbulent classification from $Re_{\text{info}}$ commutes with the Manning canal velocity computation | MEDIUM |
| **T6: Braid ⊗ Spiral** | The braid group relations preserve the golden ratio scaling from the chiral spiral layer | LOW |
| **T7: Gear ⊗ Whirlpool** | Shell gear reduction commutes with FAMM whirlpool intensity | LOW |
| **T8: IUTT preservation** | IUTT path-splitting preserves at least ONE invariant from the lower layers (braid, spiral, gear, or whirlpool) | LOW |

---

## 6. Notation Cross-Reference

| Concept | S1 (Fisher) | S2 (Alcubierre) | S3 (SIM) | S4 (MOIM) |
|---|---|---|---|---|
| **Manifold** | $\mathcal{M}$ (genus-3) | $(\tau, H)$-plane | $(\phi, X^A)$ field | $\{0,1\}^{18}$ lattice |
| **Metric** | $g_{ij}^{\text{Fisher}}$ | $d\mathcal{I}^2$ (Lorentzian) | $M^{ij}$ (anisotropic) | Hamming + engram |
| **Connection** | $\nabla^{LC}$ | $\nabla^{LC}$ | $\nabla^{LC} + T$ | Discrete gradient |
| **Torsion** | $0$ (by definition) | Emerges from $\beta$ shift | $T^k_{ij}$ | N/A (lattice) |
| **Distance** | Fisher-Rao | Proper interval $\Delta \mathcal{I}$ | $d_N$ (path length) | Genome edit distance |
| **State** | $p(x \mid \theta)$ | $(H, \tau)$ | `ManifoldPoint` | 18-bit Genome18 address |
| **Flow** | Geodesic equation | Bubble velocity $v_{\text{eff}}$ | $\partial_t \phi$ PDE | Cascade uplift/descent |
| **Stability** | Geodesic completeness | $\Phi_{sss} \cdot \Omega > 0$ | Foldback-lock $I_{\text{lock}}$ | SLUQ state machine |
| **Entropy** | Shannon $H(p)$ | $H$ (coordinate) | Vector $(S_1, S_2, S_3)$ | BPB per tile |

---

## 7. Immediate Next Steps

1. **[ ] Create `InformationManifold.lean`:** A single Lean module defining $(\mathcal{M}, g, \nabla)$ as the fundamental object, with all four specializations as `structure` extensions. This becomes the **single source of truth** for manifold definitions.

2. **[ ] Axiomatize `bind` in `Bind.lean`:** Add the five axioms from §3. Prove they hold for at least one specialization (S1, Fisher-KL is easiest).

3. **[ ] Separate abstract from concrete in Lean:** Move Q16.16-dependent manifold code to a `Concrete/` namespace. The `Core/` namespace should operate in $\mathbb{R}$.

4. **[ ] Upgrade genus3_framework.md:** Mark all conjectures with `[CONJECTURE]` and separate proven from conjectured statements. Publish the proven part as a taxonomy of what's known; publish the conjectured part as a research program.

5. **[ ] Begin T1 (SIM → Fisher reduction):** The most important cross-layer theorem. If S3 reduces to S1 when torsion vanishes, the whole architecture gains coherence.

---

## 8. References

- Amari, S. (2021). "Information geometry." Japanese Journal of Mathematics, 16, 1-48.
- Chentsov, N.N. (1972). "Statistical Decision Rules and Optimal Inference." AMS Translations.
- Ay, N., Jost, J., Lê, H.V., Schwachhöfer, L. (2017). "Information Geometry." Springer.
- `6-Documentation/docs/avmr/genus3_framework.md` — Genus-3 framework with multi-agent critique
- `shared-data/data/germane/architecture/CANONICAL_CORE_V1.md` — Alcubierre warp metric specification
- `0-Core-Formalism/lean/Semantics/Semantics/ManifoldFlow.lean` — SIM governing equations
- `6-Documentation/docs/semantics/BEHAVIORAL_MANIFOLD_PIPELINE.md` — MOIM behavioral manifold pipeline
