# Common-Noise Mean-Field Game Riccati Gate

## Purpose

Integrate **Linear-Quadratic Mean Field Games with Common Noise: A Direct Approach** into the FAMM/Semantic Mass shortcut stack.

The paper is useful because it gives a mathematically mature version of a move the project keeps making:

```text
many coupled local actors
→ shared global field / common noise
→ population-limit law
→ reduced Riccati control kernel
→ decentralized strategy
→ bounded residual receipt
```

## Source

- Wenyu Cong, Jingtao Shi, Bingchang Wang.
- `Linear-Quadratic Mean Field Games with Common Noise: A Direct Approach`.
- arXiv:2508.07271.

## Why it matters

The paper studies a linear-quadratic mean-field game with common noise where drift and diffusion terms are coupled with state, control, and mean-field state terms. It starts from a finite `N`-player game, derives FBSDEs by variational analysis, then takes the limit as `N → ∞` using law-of-large-numbers reasoning. In the limiting system, existence/uniqueness of BSDEs makes some variables identically zero, reducing the analysis enough to construct decentralized strategies with two Riccati equations. The paper also proves the constructed decentralized strategies form an `epsilon`-Nash equilibrium.

## FAMM interpretation

Common noise is a closure warning:

```text
if all agents share a shock,
the shock is part of the system boundary.
```

The route object is not one local agent. It is the agent plus the population field plus the common-noise channel.

## FAMM object

```math
\mathfrak C_{\mathrm{MFG}}
=
A_{16}(u_{\mathrm{mfg}})
\otimes
[
\Sigma_{\mathrm{agent}}
+
\Sigma_{\mathrm{mean}}
+
\Sigma_{\mathrm{common}}
+
\Sigma_{\mathrm{FBSDE}}
+
\Sigma_{\mathrm{Riccati}}
+
\Sigma_{\epsilon\mathrm{Nash}}
+
\epsilon_{\mathrm{solv}}
]
```

## Semantic Mass lanes

```math
\mu_{\mathrm{MFG}}[k]
=
w_m\|m_k\|
+
w_0\|W^0_k\|
+
w_u\|u_k\|
+
w_q J_k
+
w_r\|R_k\|
+
w_e\epsilon_{\mathrm{Nash},k}
+
w_s S_k
```

Where:

- `m_k` = population / mean-field state.
- `W0_k` = common-noise shock lane.
- `u_k` = decentralized control intensity.
- `J_k` = cost/value lane.
- `R_k` = FBSDE/Riccati residual.
- `epsilon_Nash,k` = bounded equilibrium error.
- `S_k` = solvability/stability status.

## 16D anchor addition

```text
COMMON_NOISE_MFG_RICCATI_GATE
```

Recommended axis placement:

```text
2 semantic mass           population-state pressure
3 Z pole                  mean-field trajectory recurrence
4 curvature               Riccati/value curvature
5 delta-memory            population state as compact history
6 closure                 common-noise boundary inclusion
7 residual seal           epsilon-Nash residual
11 scar                   failed coupling / unsolved FBSDE route
13 invariant              equilibrium consistency
14 receipt                Riccati/epsilon-Nash receipt
```

## Shortcut doctrine

```text
do not enumerate every strategic interaction
when the population-limit field plus Riccati kernel carries the lawful structure.
```

## No-drift boundary

This is a mathematical control/routing witness. It does not prove project-level claims by itself. It gives a rigorous shortcut pattern: common-noise closure, population-limit collapse, Riccati kernel, decentralized strategy, and bounded equilibrium residual.
