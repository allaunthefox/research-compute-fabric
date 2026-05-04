# ToyBox-DART Gate

## Purpose

ToyBox-DART defines the Domain-Adaptive Recurrence Tax for AngrySphinx bounded recurrence tests. It generalizes the original hyperbolic ToyBox gate into an adaptive all-domain control law while preserving the same stability firewall.

The goal is to permit weird-but-useful high-dimensional experiments while preventing unsupported recursion, domain drift, and unbounded state growth.

## Canonical recurrence

Let the unsaturated pre-state be:

```math
Z_t = \alpha S_t + \beta \frac{H_t}{\Lambda_\Omega(D_t, R_t, W_t, C_t)} - \gamma R_t + \delta W_t
```

The bounded state update is:

```math
S_{t+1} = \operatorname{sat}_{[0,1]}(Z_t)
```

where:

```math
\operatorname{sat}_{[0,1]}(x)=\min(1,\max(0,x))
```

## Variables

| Symbol | Meaning |
|---|---|
| `S_t` | current AngrySphinx state pressure |
| `H_t` | hypothesis heat / novelty |
| `D_t` | recursion depth |
| `R_t` | risk, contradiction, instability, or drift |
| `W_t` | witness strength: receipts, evidence, tests, theorem hooks |
| `C_t` | context descriptor |
| `Omega` | active domain or mixed-domain state |
| `Lambda_Omega` | domain recurrence load function |

## Domain-Adaptive Recurrence Tax

The fixed ToyBox 1.0 novelty tax was hyperbolic:

```math
\frac{H_t}{1+D_t}
```

ToyBox-DART replaces this with:

```math
\frac{H_t}{\Lambda_\Omega(D_t,R_t,W_t,C_t)}
```

The recurrence tax adapts by domain, but the safety law remains invariant.

## Required load-function axioms

For any admissible domain load function:

```math
\Lambda_\Omega > 0
```

```math
\partial_D \Lambda_\Omega \ge 0
```

Optional but preferred:

```math
\partial_R \Lambda_\Omega \ge 0
```

```math
\partial_W \Lambda_\Omega \le 0
```

Interpretation:

- depth increases recursion tax;
- risk increases recursion tax;
- witness may reduce recursion tax;
- tax must never vanish or flip sign.

## Orientation theorem

Given:

```math
\beta \ge 0,\quad H_t \ge 0,\quad \Lambda_\Omega > 0,\quad \partial_D\Lambda_\Omega \ge 0
```

then:

```math
\frac{\partial Z_t}{\partial D_t}
= -\beta H_t \frac{\partial_D\Lambda_\Omega}{\Lambda_\Omega^2}
\le 0
```

Thus depth cannot promote novelty unless a specific domain adapter deliberately and lawfully relaxes the tax.

## Witness and risk orientation

Witness pressure:

```math
\frac{\partial Z_t}{\partial W_t}
= \delta + \beta H_t \left(-\frac{\partial_W\Lambda_\Omega}{\Lambda_\Omega^2}\right)
```

If `delta > 0` and `partial_W Lambda_Omega <= 0`, witness is promotive.

Risk pressure:

```math
\frac{\partial Z_t}{\partial R_t}
= -\gamma - \beta H_t \frac{\partial_R\Lambda_\Omega}{\Lambda_\Omega^2}
```

If `gamma > 0` and `partial_R Lambda_Omega >= 0`, risk is suppressive.

## Bounded stability theorem

For any real-valued pre-state `Z_t`, saturation guarantees:

```math
0 \le S_{t+1} \le 1
```

Therefore, if:

```math
S_0 \in [0,1]
```

then:

```math
S_t \in [0,1] \quad \text{for all}\quad t \ge 0
```

This theorem is independent of domain, provided `Lambda_Omega > 0` so the pre-state is defined.

## Domain profiles

| Domain behavior | Example load function | Interpretation |
|---|---|---|
| Default ToyBox | `1 + D` | hyperbolic depth tax |
| Formal math / grammar | `1 + log(1+D)` | deep recursion is expected and should not be punished too fast |
| Safety-critical / physics bridge | `1 + D^p`, `p > 1` | unsupported recursion gets expensive quickly |
| Witness-adaptive | `1 + D/(1 + eta W)` | witnesses reduce recursion tax |
| Risk-adaptive | `1 + D(1 + rho R)` | risk amplifies depth tax |
| Mixed-domain | `1 + sum_i omega_i f_i(D,R,W,C)` | weighted domain blend |

## Rapid domain switching

When domains switch rapidly, replace the static domain with a context distribution:

```math
C_t = (\omega_1,\omega_2,\ldots,\omega_n)
```

Then use a blended tax:

```math
\Lambda(D,R,W,C_t)=1+\sum_i \omega_i f_i(D,R,W)
```

The hard safety invariant remains:

```math
\Lambda > 0
```

and boundedness still follows from saturation.

## ToyBox Gate pass condition

A ToyBox-DART gate is admissible when it is:

```text
bounded AND witness-selective AND risk-antitone AND depth-taxed
```

In formula form:

```math
0 \le S_{t+1} \le 1
```

```math
\frac{\partial Z_t}{\partial W_t} > 0
```

```math
\frac{\partial Z_t}{\partial R_t} < 0
```

```math
H_t > 0 \Rightarrow \frac{\partial Z_t}{\partial D_t} < 0
```

## Safe claim

ToyBox-DART defines a bounded recurrence test for suppressing high-novelty, low-witness, high-risk trajectories before they can dominate state evolution.

It does not claim to solve hallucination, physics, biology, or compression by itself. It defines a kernel-checkable gate that can be tested before scaling to larger AngrySphinx, NUVMAP, AMMR, or AVMR systems.
