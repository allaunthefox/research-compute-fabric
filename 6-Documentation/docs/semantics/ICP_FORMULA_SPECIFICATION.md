# Specification: Infohazard Containment Protocol (ICP) Formula

This document provides the explicit mathematical definition of the **Infohazard Containment Protocol (ICP)**, mapping adversarial probe intensity to epistemic masking and complexity escalation.

## 1. Input Variable: Extraneous Load ($L_E$)
The extraneous load is the primary trigger for the ICP. It is calculated by the **SSMS (Steady State Manifold State)** engine based on current probe frequency ($f_p$) and signal noise ($N_s$).

$$L_E = f(f_p, N_s)$$

## 2. Threshold Mapping ($D_L$)
The **Detection Level** ($D_L \in \mathbb{N}$) is determined by the following step-function:

$$D_L(L_E) = \begin{cases} 
0 & \text{if } L_E < T_{L1} \\ 
1 & \text{if } T_{L1} \le L_E < T_{L2} \\ 
2 & \text{if } T_{L2} \le L_E < T_{L3} \\ 
3 & \text{if } L_E \ge T_{L3} 
\end{cases}$$

Where:
- $T_{L1} = 1.0$ (Peripheral Threshold)
- $T_{L2} = 5.0$ (Investigative Threshold)
- $T_{L3} = 10.0$ (Adversarial Threshold)

## 3. Repulsion Mode ($M_R$) & Containment ($C$)
The repulsion mode is governed by the **Deterrence Invariant** ($C \in \{0, 1\}$). 
- If $C = 1$ (Locked), the system is inhibited.
- If $C = 0$ (Armed), the system is active.

$$M_R(D_L, C) = \begin{cases} 
\text{Mild} & \text{if } D_L = 1 \\ 
\text{Hypercringe} & \text{if } D_L = 2 \\ 
\text{Radioactive} \cdot (1 - C) + \text{Hypercringe} \cdot C & \text{if } D_L = 3 
\end{cases}$$

## 4. Complexity Escalation ($\Delta H$)
When $D_L = 3$, the **AngrySphinx** protocol escalates the difficulty ($H$) of the manifold challenges.

$$H_{t+1} = H_t + \delta(L_E - T_{L3})$$

Where $\delta$ is the scaling factor $\frac{1}{2}$ in Q16.16.

## 5. Masking Load ($L_{mask}$)
The computational heat generated to mask real work is a product of the current extraneous load and a mode-specific density factor ($K$).

$$L_{mask} = L_E \times K(M_R)$$

Where:
- $K(\text{Mild}) = 100$
- $K(\text{Hypercringe}) = 500$
- $K(\text{Radioactive}) = 1000$

---
**Invariant**: `ICP_Lawfulness`
**Theorem**: $M_R = \text{Radioactive} \implies C = 0$ (The Radioactive mode can never be triggered in a Locked state).
