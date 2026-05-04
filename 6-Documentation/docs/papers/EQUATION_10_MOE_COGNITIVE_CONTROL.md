# MoE Cognitive Control: State-Dependent Expert Blending

**Equation ID:** 10  
**Family:** Cognitive Load  
**Status:** ✅ REFINED  
**Cross-refs:** 0.1, 1, 6, 7, 29

---

## The Equation

$$
P_{\text{control}} = \sum_{k=1}^{K} g_k \cdot E_k
$$

Where the gating weights follow:

$$
\boxed{g_k = \sigma\left(\lambda_1 \rho + \lambda_2 c - \lambda_3 s + \lambda_4 u\right)}
$$

---

## Variables

| Symbol | Meaning |
|--------|---------|
| $P_{\text{control}}$ | Control decision policy |
| $g_k$ | Gating weight for expert $k$ |
| $E_k$ | Expert evaluator $k$ (cognitive or affective) |
| $\sigma$ | Sigmoid function (smooth blending) |
| $\rho = \frac{L_{\text{total}}}{C_{\text{cognitive}}}$ | Load-to-capacity ratio |
| $c$ | Cortisol (stress chemistry) |
| $s$ | Serotonin (stabilization) |
| $u$ | Urgency / threat salience |
| $\lambda_{1,2,3,4}$ | Weighting coefficients |

---

## Purpose

Models cognitive control as a **blended mechanism** under capacity constraints:

1. **Not a binary switch:** No hard transition from "cognition" to "emotion"
2. **Continuous mixture:** Expert weights deform smoothly with load
3. **Neurochemical modulation:** Stress chemistry biases gating
4. **Efficiency-optimal:** Seeks blend that maximizes $\eta_{\text{MoE}}$

---

## Two-Expert Cognitive Case

For the cognitive/affective system:

$$
\boxed{D(x) = \alpha \cdot U_{\text{cog}}(x) + \beta \cdot U_{\text{aff}}(x)}
$$

Where:
- $\alpha = g_{\text{cog}}$ = deliberative weight
- $\beta = g_{\text{aff}}$ = affective weight
- $\alpha + \beta = 1$

---

## Gating Dynamics

### Low Load Regime
- $\rho \approx 0.1$-$0.3$
- $\beta \approx 0.1$-$0.2$
- **Result:** Cognition dominates, high precision

### Medium Load Regime  
- $\rho \approx 0.5$-$0.8$
- $\beta \approx 0.3$-$0.5$
- **Result:** Balanced, adaptive mixture

### High Load Regime
- $\rho \approx 1.0$-$1.5$
- $\beta \approx 0.6$-$0.9$
- **Result:** Affective heuristics dominate, fast but lossy

---

## Connection to ηMoE

The MoE control feeds directly into the efficiency equation:

$$
\eta_{\text{MoE}}(x) = \frac{\sum_k g_k \left(\frac{w_k h_k}{\ln N_k} - \frac{v_k p_k}{\ln N_k}\right)}{\sum_k g_k(a_k \ln N_k + c_k) + k_B T I_{\text{discarded}} + C_{\text{platform}}}
$$

**Key insight:** Cognitive load doesn't directly choose actions—it **deforms the efficiency landscape**, and the system seeks gate weights that maximize $\eta_{\text{MoE}}$ under current constraints.

---

## The "Topological Throat" Interpretation

The throat is not a moment where emotion replaces cognition. It is:

$$
\boxed{\text{Capacity-constrained gating collapse}}
$$

When $\sum_k g_k C_k > C_{\text{cognitive}}$, the system must:
- Drop high-cost experts
- Simplify routing
- Shift weight toward low-cost heuristics

---

## Physical Safeguards

From MathMan's stress-testing:

1. **$g_k \in [0, 1]$:** Bounded weights
2. **$\sum_k g_k = 1$:** Conservation of control
3. **$C_k > 0$:** Per-expert cost prevents free lunch
4. **$N_k \geq 2$:** Minimum complexity prevents singularity

---

## Theorem (Load-Triggered Phase Transition)

**Statement:** Under rising cognitive load, the system undergoes a continuous control regime shift from deliberative to affective weighting.

**Proof sketch:**

1. Define $\beta = \sigma(k_1 \rho + k_2 c - k_3 s + k_4 u)$
2. As $\rho \uparrow$, argument to $\sigma$ increases
3. Since $\sigma$ is monotone, $\beta \uparrow$
4. Therefore $\alpha = 1 - \beta \downarrow$
5. Control shifts from cognitive to affective dominance

**QED**

---

## Implementation

**Lean module:** `MoECognitiveControl.lean`  
**Python shim:** `cognitive_moe_blender.py`

---

## References

- Shazeer et al. (2017): Outrageously Large Neural Networks (MoE)
- Kahneman (2011): Thinking, Fast and Slow (Dual-process theory)
- Sapolsky (2017): Behave (Stress neurobiology)
- OTOM Cognitive Load Integration (v3)

---

**Status:** ✅ Ready for Triumvirate Warden review
