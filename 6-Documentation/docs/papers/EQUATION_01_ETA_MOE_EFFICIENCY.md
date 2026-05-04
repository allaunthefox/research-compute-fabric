# ηMoE: Mixture-of-Experts Cognitive Efficiency

**Equation ID:** 0.1  
**Family:** Field Optimization  
**Status:** ✅ REFINED  
**Cross-refs:** 0, 1.1, 1.2, 6, 29

---

## The Equation

$$
\eta_{\text{MoE}}(x) = \frac{\sum_{k=1}^{K} g_k(x) \left(\frac{w_k h_k}{\ln N_k} - \frac{v_k p_k}{\ln N_k}\right)}{\sum_{k=1}^{K} g_k(x)(a_k \ln N_k + c_k) + k_B T \cdot I_{\text{discarded}}(x) + C_{\text{platform}}(x)}
$$

---

## Variables

| Symbol | Meaning |
|--------|---------|
| $g_k(x)$ | Gating weight for expert $k$ (state-dependent) |
| $w_k$ | Quality weight for expert $k$ |
| $h_k$ | Structural coherence / benefit from expert $k$ |
| $v_k$ | Penalty weight for expert $k$ |
| $p_k$ | Distortion / error from expert $k$ |
| $N_k$ | Effective arity / complexity of expert $k$ |
| $a_k$ | Cost coefficient for expert $k$ |
| $c_k$ | Per-expert overhead (fixed cost) |
| $I_{\text{discarded}}$ | Irreversible information loss (Landauer) |
| $C_{\text{platform}}$ | Substrate / hardware overhead |

---

## Purpose

The ηMoE equation bridges **microscopic cognitive control** to **macroscopic universal efficiency**:

1. **Mechanism:** Uses Mixture-of-Experts (MoE) architecture with state-dependent gating
2. **Load-dependence:** Gating weights deform under cognitive load ($\rho = L_{\text{total}}/C_{\text{cognitive}}$)
3. **Neurochemistry:** Gating modulated by cortisol ($c$), serotonin ($s$), and urgency ($u$)
4. **Thermodynamic bounds:** Includes Landauer cost $k_B T I_{\text{discarded}}$ and platform overhead $C_{\text{platform}}$

---

## Gating Function

The expert selection weights follow a sigmoid-based load response:

$$
g_k(x) = \sigma\left(\lambda_1 \rho + \lambda_2 c - \lambda_3 s + \lambda_4 u\right)
$$

Where:
- $\rho$ = load-to-capacity ratio
- $c$ = cortisol (stress drive)
- $s$ = serotonin (stabilization)
- $u$ = urgency / threat salience
- $\sigma$ = sigmoid function

---

## Physical Constraints (Anti-Paradox Safeguards)

From MathMan's stress-testing:

1. **$N_k \geq 2$**: Minimum arity prevents singularity
2. **$c_k > 0$**: Per-expert overhead prevents vanishing cost
3. **$C_{\text{platform}} > 0$**: Baseline cost prevents infinite efficiency
4. **$I_{\text{discarded}} \geq 0$**: Landauer limit respected

---

## Two-Expert Cognitive Case

For the cognitive/affective blend:

$$
\eta_{\text{cognitive}}(x) = \frac{\alpha\left(\frac{w_c h_c}{\ln N_c} - \frac{v_c p_c}{\ln N_c}\right) + \beta\left(\frac{w_a h_a}{\ln N_a} - \frac{v_a p_a}{\ln N_a}\right)}{\alpha(a_c \ln N_c + c_c) + \beta(a_a \ln N_a + c_a) + k_B T I_{\text{discarded}} + C_{\text{neural}}}
$$

Where:
- $\alpha = g_{\text{cog}}$ (deliberative weight)
- $\beta = g_{\text{aff}}$ (affective weight)
- $\alpha + \beta = 1$

---

## Connection to Φ_universal

The ηMoE is the **micro-mechanism** that realizes the macroscopic field equation:

| Layer | Role |
|-------|------|
| **Φ_universal** | Macro field equation (ground truth) |
| **ηMoE** | Local efficiency scoring (mechanism) |
| **MoE Control** | Gating dynamics (implementation) |

---

## Theorem (Efficiency-Load Tradeoff)

**Statement:** Under rising cognitive load, the efficiency-maximizing gate shifts from deliberative to affective experts.

**Proof sketch:**
- Low load: $\rho \approx 0 \Rightarrow \beta \approx 0 \Rightarrow$ cognition dominates
- Rising load: $\rho \uparrow \Rightarrow \beta \uparrow \Rightarrow$ affective weighting increases
- High load: $\beta \gg \alpha \Rightarrow$ heuristic control dominates

---

## Implementation

**Lean module:** `EtaMoE.lean`  
**Python shim:** `cognitive_efficiency_moe.py`

---

## References

- Landauer (1961): Irreversibility and heat generation
- Shazeer et al. (2017): Outrageously Large Neural Networks (MoE)
- OTOM Cognitive Load Integration (v3)

---

**Status:** ✅ Ready for Triumvirate Warden review
