# MarkovJunior 16D PIST Rewrite Shim

## Purpose

Add a shim that treats MarkovJunior-style rewrite programs as 16D FAMM/PIST/NUVMAP objects.

This is an adapter, not a replacement for MarkovJunior. MarkovJunior provides the rewrite-rule grammar and constraint-propagation style. The shim projects those rules into the current project stack:

```text
MarkovJunior rule
→ 16D rewrite anchor
→ PIST transition candidate
→ FAMM scar/residual accounting
→ NUVMAP rewrite-basin address
→ Delta-DAG replay edge
→ BJW cleanup / exact receipt
```

## Why MarkovJunior fits

MarkovJunior programs are built from rewrite rules. In basic form, a program is an ordered list of rewrite rules. A rule match is selected and applied on the grid, and the process halts when no rules match. MarkovJunior also supports probabilistic inference through constraint propagation.

Project translation:

```text
rewrite rule       = PIST surface-transition operator
rule match         = local state crossing
changed cells      = delta edge
failed constraint  = FAMM scar
inference field    = Semantic Mass / route pressure
trace              = NUVMAP Delta-DAG
```

## 16D rewrite state

```math
X_{\mathrm{MJ}}
=
[
\nu,
s,
m_L,
m_\Delta,
h_{\mathrm{rule}},
p_{\mathrm{obs}},
\chi,
\mu,
z,
\Delta_{\mathrm{mem}},
\Omega,
R,
I,
C,
\rho,
\pi
]
```

| Axis | Meaning |
|---:|---|
| 0 | NUVMAP rewrite-state address |
| 1 | S3C shell / dimensional shell |
| 2 | left-pattern mass |
| 3 | rewrite delta mass |
| 4 | rule hash / rule-order pressure |
| 5 | observation / constraint pressure |
| 6 | chirality / orientation |
| 7 | semantic mass |
| 8 | recurrence / Z-domain lane |
| 9 | delta-memory state |
| 10 | FAMM scar pressure |
| 11 | residual / unsatisfied constraint |
| 12 | invariant overlap |
| 13 | route cost |
| 14 | receipt strength |
| 15 | projection / display gauge |

## Rule anchor

```math
A_r
=
\operatorname{Embed}_{16D}
(
H(L_r),
H(R_r),
\|L_r\|,
\|R_r-L_r\|,
\mathrm{wildcards},
\mathrm{weight},
\mathrm{constraints}
)
```

Where `L_r` is the left pattern and `R_r` is the right pattern.

## PIST transition law

```math
X_{t+1}
=
\Pi_{\mathrm{adm}}
\left[
\mathrm{PIST}_{r_t}(X_t)
+
\Delta_{\mathrm{MJ}}(r_t,m_t)
\right]
```

## Rule score

```math
P(r_t=i\mid X_t)
\propto
\exp[
-\alpha d_i
-\beta\Omega_i
-\kappa K_i
+\gamma I_i
-\eta C_i
+\lambda\mu_i
+\rho R_i
+\chi H_i
]
```

This makes MarkovJunior rule selection compatible with semantic mass, scar pressure, coarsening pressure, invariant overlap, route cost, receipt strength, and chirality compatibility.

## Coarsening-agent behavior

```text
failed rewrite
→ residual measured
→ scar written
→ basin coarsened
→ future matching downweighted
→ route reopened only if new evidence changes the boundary
```

## Boundary

This shim does not execute full MarkovJunior XML semantics. It is a projection layer. It maps MarkovJunior-style rewrite rules and traces into the 16D project state so they can be routed, scored, replayed, and receipted.

## Project sentence

The MarkovJunior shim lets the project treat local rewrite rules as 16D surface-transition anchors: MarkovJunior supplies the rewrite grammar, PIST supplies lawful motion, FAMM tracks scars and residuals, NUVMAP stores rewrite basins, and Delta-DAG receipts the replay path.
