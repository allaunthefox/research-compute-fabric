# Definition: Renormalization Group Flow (RG Flow)

> **TL;DR: The Manifold's Zoom Lens.**  
> RG Flow is the universal filter that zooms out of raw data to distinguish between **relevant signal** (structural invariants) and **irrelevant noise** (thermal fluctuations). It ensures that only scale-stable patterns—whether in Bitcoin price actions or genetic sequences—reach the Sovereign Core.

---

## 1. Core Mathematical Intuition
RG Flow describes how the effective parameters of a system (the "coupling constants") evolve as one changes the **scale** ($s$) of observation via coarse-graining.

### The Beta Function
The rate of change of a parameter $g$ with respect to the logarithmic scale change is given by the Beta Function:
$$\beta(g) = \frac{dg}{d(\ln s)}$$

- **Fixed Points**: Values of $g$ where $\beta(g) = 0$. These represent stable phases where the system's behavior is scale-invariant.
- **Relevant/Irrelevant Operators**: Parameters that grow (Relevant) or shrink (Irrelevant) as you zoom out, determining the large-scale "shape" of the manifold.

## 2. Implementation in the Manifold
In the `Semantics.BitcoinRGFlow` module, RG Flow is used to compute the **Lawfulness Invariant** of a signal:

### Scale Stability ($\sigma_q$)
A measure of how coherent a signal remains as the observation window increases.
$$\sigma_q = 1.0 + 0.35 \cdot \text{coherence} - 8.0 \cdot \text{volatility}$$

### The RG Flow Invariant
A state is considered **Lawful (Filtered)** if it satisfies:
$$\sigma_q > 1 + \lambda \cdot \mu_q$$
Where:
- $\mu_q$ is the **Drift Rate** (average log return).
- $\lambda$ is the **Observer Mass Penalty** (typically 0.5).

## 3. Practical Function
RG Flow acts as the **Neural Filter** for the manifold. By identifying "Fixed Points" in information flow, the system can distinguish between irrelevant noise (thermal fluctuations) and relevant structural data (germane signal).

---
**Formal implementation**: [BitcoinRGFlow.lean](file:///home/allaun/Research%20Stack/0-Core-Formalism/lean/Semantics/Semantics/BitcoinRGFlow.lean)  
**Database entry**: `Semantics.bitcoinInformationalBind`
