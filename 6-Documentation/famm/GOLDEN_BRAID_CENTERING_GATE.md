# Golden Braid Centering Gate

## Purpose

Add Fibonacci/golden-ratio centering as a BraidStorm calibration primitive.

This gate is not a solver. It is a stability, survivor, and coarsening test for 16D braid-strand states.

```text
BraidStorm strand states
→ braid crossing / hypothesis recombination
→ golden center pull
→ collapse-rate receipt
→ FAMM scar / coarsening decision
→ NUVMAP Delta-DAG update
→ Builder-Judge-Warden promotion or block
```

## Core intuition

Every strand receives the same harmonic reference: the shared 16D center `c`.

Healthy strands contract toward the center at the expected golden rate. Bad crossings, wrong hypotheses, missing boundaries, chirality mismatches, or overfit false centers produce measurable deviation.

```text
not useful: everything eventually reaches the center
useful: which strands reach center cleanly, which resist, and which crossings create drift
```

## Golden contraction law

Let:

```math
\varphi=\frac{1+\sqrt 5}{2}
```

For a 16D strand state:

```math
s_i(t)\in\mathbb R^{16}
```

with center:

```math
c\in\mathbb R^{16}
```

apply:

```math
s_i(t+1)=c+\varphi^{-1}(s_i(t)-c)
```

After `t` steps:

```math
s_i(t)-c=\varphi^{-t}(s_i(0)-c)
```

Ideal distance law:

```math
\|s_i(t)-c\|=\varphi^{-t}\|s_i(0)-c\|
```

## Braid crossing with centering receipt

A normal BraidStorm crossing is:

```math
\beta_{ij}:(s_i,s_j)\to(s_i',s_j',r_{ij},\epsilon_{ij},\Omega_{ij})
```

Add golden-centering receipt:

```math
\beta_{ij}:(s_i,s_j)\to(s_i',s_j',r_{ij},\epsilon_{ij},\Omega_{ij},G_{ij})
```

where:

```math
G_{ij}
=
\left|
\frac{\|s_i'-c\|}{\|s_i-c\|}
-\varphi^{-1}
\right|
+
\left|
\frac{\|s_j'-c\|}{\|s_j-c\|}
-\varphi^{-1}
\right|
```

Ideal crossing:

```math
G_{ij}=0
```

Scarred crossing:

```math
G_{ij}>\Theta_G
```

## Multi-strand collapse receipt

For strand set `S={s_1,...,s_m}` define:

```math
\Omega_{\mathrm{center}}
=
\sum_i R_i(t)
+
\left\|\operatorname{Cov}(S_t)-\lambda I\right\|
+
\left\|\bar s_t-c\right\|
+
\Omega_{\chi}
```

where:

```math
R_i(t)
=
\left|
\frac{\|s_i(t)-c\|}{\|s_i(0)-c\|}
-\varphi^{-t}
\right|
```

and `Omega_chi` is chirality/orientation mismatch when chirality is active.

## Failure modes detected

| Failure | Centering symptom | FAMM action |
|---|---|---|
| Bad hypothesis | high collapse residual | scar / coarsen basin |
| Toxic crossing | sudden center drift | Warden block |
| Chirality mismatch | asymmetric contraction or sign flip | chirality scar |
| Overfit local basin | false fast collapse into wrong center | require external Judge receipt |
| Missing boundary | persistent residual after centering | boundary investigation |
| Good survivor strand | clean contraction with receipt preservation | promote candidate |

## Coarsening behavior

If a strand or crossing repeatedly fails golden centering:

```text
failed center pull
→ residual measured
→ scar written
→ basin coarsened
→ fine search downweighted
→ route reopened only by new evidence or changed boundary
```

## Stack placement

```text
Braid crossing
→ hypothesis recombination
→ GOLDEN_BRAID_CENTERING_GATE
→ FAMM residual/scar measurement
→ NUVMAP node update
→ Delta-DAG crossing receipt
→ BJW Judge/Warden decision
```

In the larger stack:

```text
BraidStorm Gossip
→ PIST / PIST-Chaos transition
→ Golden Braid Centering Gate
→ FAMM Scar Ledger
→ NUVMAP Delta-DAG
→ Coarsening Agent
→ Builder-Judge-Warden
→ Exact / statistical receipt
```

## Boundary

This is not a claim that all useful dynamics should collapse to a literal center. It is a calibration primitive. The endpoint is boring; the collapse receipt is useful.

## Project sentence

In BraidStorm, Fibonacci centering is a harmonic calibration gate: every strand is pulled toward the shared 16D center at the expected `phi^-1` rate, and any deviation becomes a FAMM scar showing which braid crossings, hypotheses, or dimensions resisted lawful collapse.
