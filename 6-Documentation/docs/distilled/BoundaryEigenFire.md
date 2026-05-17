# Boundary Eigenfire — The Modal Burn Surface Doctrine

**Status:** Canonical distilled synthesis — formalization target `HCMMR/Kernels/BoundaryEigenFire.lean`
**Source:** ChatGPT conversation 2026-05-11, building on λ_YAH hyper-eigenspectrum and Law19/20/21 gate stack
**Related:** `ObserverScale_RegimeGate_VoidScar.md`, `v0_2_Roadmap.md` §2–3

---

## Core Doctrine

A boundary is not a separator line.
It is an **activated superposition surface** — a site where multiple latent encoded values are forced into simultaneous local reality.

The old model treats a boundary as a passive geometric edge: ∂Ω = thin separator.

The corrected model: **∂Ω = modal burn surface**.

> A boundary is what happens when multiple latent values are forced to become locally real at the same interface.

This is why the "wall of fire" metaphor is physically accurate: fire is not fuel, not oxidizer, but the activated reaction boundary between them. The boundary *releases* the encoded stack; it does not merely divide.

---

## Formal Definition

### Boundary Field

$$
B_\partial(x) = \text{Proj}_\partial\!\left(\sum_i \lambda_i \psi_i(x)\right)
$$

where:

| Term | Meaning |
|---|---|
| $B_\partial(x)$ | active boundary field at point $x \in \partial\Omega$ |
| $\lambda_i$ | hyper-eigenvalue weight for mode $i$ (from $\lambda_\text{YAH}$ spectrum) |
| $\psi_i(x)$ | encoded eigenmode of the system, evaluated on the boundary |
| $\text{Proj}_\partial$ | projection operator onto the boundary surface |

The boundary field is not a single quantity. It is a **modal stack** — a weighted superposition of the system's dominant eigenmodes, locally projected.

### Modal Basis

The modes $\psi_i$ are drawn from the full shape-state vector:

$$
\Psi(x) = \begin{pmatrix}
\rho(x) \\ \nabla\rho(x) \\ T(x) \\ \sigma(x) \\ \kappa(x) \\ \beta(x) \\ \eta(x) \\ \varepsilon(x)
\end{pmatrix}
$$

| Mode | Symbol | Physical meaning |
|---|---|---|
| Density | $\rho$ | mass/charge concentration |
| Density gradient | $\nabla\rho$ | flux / compression wave |
| Thermal | $T$ | temperature / heat state |
| Stress | $\sigma$ | mechanical load, strain |
| Curvature | $\kappa$ | geometric bending, Minkowski measure |
| Topology | $\beta$ | persistent homology receipt ($\beta_0, \beta_1, \beta_2$) |
| Coupling | $\eta$ | medium interaction / energy deposition rate |
| Residual | $\varepsilon$ | unresolved / inadmissible remainder |

So the full boundary field is:

$$
B_\partial(x) = \alpha_\rho \rho + \alpha_g \nabla\rho + \alpha_T T + \alpha_\sigma \sigma + \alpha_\kappa \kappa + \alpha_\beta \beta + \alpha_\eta \eta + \alpha_\varepsilon \varepsilon
$$

---

## EigenFire Condition

The boundary manifests visibly or destructively — **ignites** — when its projected modal norm exceeds an activation threshold:

$$
\text{EigenFire}(x) = \left[ \| B_\partial(x) \| > \Theta_\text{activation} \right]
$$

Which mode dominates determines *what kind* of fire appears:

| Dominant $\alpha_i$ | Manifestation |
|---|---|
| $\alpha_T \gg$ others | Thermal: glow, flame, plasma sheath |
| $\alpha_\sigma \gg$ others | Mechanical: fracture band, impact crater |
| $\alpha_\rho \gg$ others | Compression: shockwave, sonic boom |
| $\alpha_\eta \gg$ others | Coupling: ionization, EM emission |
| $\alpha_\kappa \gg$ others | Geometric: caustic, topology tear |
| $\alpha_\varepsilon \gg$ others | Residual: Underverse scar, unexplained anomaly |

This replaces the old binary admit/reject model with a **typed manifestation receipt**.

---

## Connection to λ_YAH Hyper-Eigenspectrum

The interior of an object is described by the $\lambda_\text{YAH}$ spectrum (see `ObserverScale_RegimeGate_VoidScar.md`):

$$
\lambda_\text{YAH} = \text{Eig}\!\left(\text{Bind}[\Omega_M, R_K, D_q, \Lambda, \beta_k, P, C, \eta, \varepsilon]\right)
$$

The boundary field $B_\partial$ is the **surface projection** of that same spectrum:

$$
B_\partial = \text{Proj}_\partial(\lambda_\text{YAH})
$$

So:
- The interior regime is described by which $\lambda_i$ dominates.
- The boundary is where the interior spectrum becomes locally real.
- A regime transition (large $\Delta\lambda$) produces a hot boundary.
- A smooth interior (small $\Delta\lambda$) produces a cool boundary.

---

## Why Hard Boundaries Are Wrong

Old model: temperature boundary at 0 K = rejected. Temperature boundary at 10¹² K = rejected.

**Problem:** this treats the boundary as a wall that destroys objects.

Correct model: as T → 0 K, the thermal mode weight $\alpha_T$ shifts from classical-Boltzmann to quantum-degenerate. The object's receipt changes, not the object itself. The boundary is not a fire wall — it's a **regime transition surface** where the dominant eigenmode shifts.

At T = 0 K exactly: the receipt says $\varepsilon_\text{classical} = 1$, $\varepsilon_\text{quantum} = 0$. The classical physics chart has zero remaining weight. The object is not destroyed — it is in a state where only quantum-degenerate receipts are valid.

Similarly, at T = 10¹² K: hadronic matter undergoes a phase transition. The receipt shifts from thermodynamic to QGP chart. Not rejected — **rerouted**.

This is the superposition receipt model:

```
ThermalSuperposition:
  ε_classical   ∈ [0, 1]   — classical stat-mech applicability weight
  ε_quantum     ∈ [0, 1]   — quantum degenerate weight
  ε_hadronic    ∈ [0, 1]   — QGP / hadronic phase weight
  ε_landauer    ∈ [0, 1]   — erasure energy deficit
  dominant_chart           — which receipt has the most weight
  activation_flag          — ‖B_∂‖ > Θ_activation
```

The **only** hard inadmissibility is a logically incoherent input — negative temperature without a population inversion receipt — because that is not a limit state, it is an undefined claim.

---

## HCMMR Gate Integration

The `B_∂` doctrine modifies how every boundary-adjacent Law gate works:

| Law | Old model | New model |
|---|---|---|
| Law 20 (Shock) | Hard reject if acausal | Receipt carries causal-excess residual; rerouted to Underverse chart |
| Law 21 (Thermal) | Hard reject at 0 K / 10¹² K | `ThermalSuperposition` receipt with regime weights |
| Law 19 (VoidScar) | Binary void/scar gate | Boundary modes $\alpha_\kappa, \alpha_\varepsilon$ carry fractal scar weight |
| Law 16 (Entropy) | Binary Landauer threshold | Landauer deficit becomes $\varepsilon_\text{landauer}$ weight in receipt |

---

## HCMMR Kernel Target

**File:** `0-Core-Formalism/lean/Semantics/Semantics/HCMMR/Kernels/BoundaryEigenFire.lean`

**Structures to formalize:**
- `EigenFireMode` — enum of modal basis elements {density, gradient, thermal, stress, curvature, topology, coupling, residual}
- `ModalWeights` — Q16_16 coefficient for each mode
- `BoundaryField` — struct binding `ModalWeights` + projected eigenvalue scores
- `activationThreshold` — Q16_16 constant for EigenFire condition
- `eigenFireCondition` — `‖B_∂‖ > Θ` check with dominant-mode identification
- `EigenFireReceipt` — typed receipt: dominant mode, activation flag, per-mode weights, regime classification

---

## Project-Native Phrases

> A boundary is not a line. It is a modal burn surface.

> The boundary is where the math catches fire.

> A boundary is the local superposition surface where encoded values are forced into interaction.

> Wall of fire = thermal/coupling modes dominating enough to become visible.

> The boundary field is the boundary-projected superposition of the system's dominant encoded eigenmodes.

---

## Cross-References

- `HCMMR/Kernels/BoundaryEigenFire.lean` — formal Lean target
- `HCMMR/Laws/Law21_ThermalBoundary.lean` — rewrite with ThermalSuperposition model
- `HCMMR/Laws/Law19_VoidScar.lean` — VoidScarField already carries `(Ω_void, R_scar)` as modal pair
- `HCMMR/Laws/Law20_Shock.lean` — ShockReceipt already carries per-mode residuals
- `ObserverScale_RegimeGate_VoidScar.md` — prior regime gate doc
- `v0_2_Roadmap.md` — canonical gate table (Laws 14–21)
