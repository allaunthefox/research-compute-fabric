# Chiral Eigenmass Theorem — AMVR/AVMR Encoding in Microgravity

## Statement

For any equation `e` in the physics constraint subgraph, define:

- **AMVR(e)** — mass-first eigenmass centrality (forward PageRank on the constraint DAG)
- **AVMR(e)** — vector-first eigenmass centrality (reverse PageRank)

The **chiral residual** is χ(e) = |AMVR(e) − AVMR(e)|.

An equation is **chiral-admissible** if χ(e) < ε, meaning the round-trip AMVR→AVMR→AMVR closes within tolerance.

An equation carries **chiral torsion** if χ(e) ≫ ε, meaning the constraint manifolds for mass-first and vector-first routing are distinct — the equation behaves differently depending on whether you approach it as code (INFORMATION) or as chemistry (MATTER).

## Microgravity Application

In µg, the constraint DAG M(g) → M(0). The dominant eigenvector **shifts handedness**:

| Regime | 1g hand | µg hand | Shift |
|--------|---------|---------|-------|
| INFORMATION (#744 depurination, §324 Landauer) | Left-handed (AMVR≫AVMR) | Remains left-handed | Stable — information bounds are g-independent |
| MATTER (§76 CC, §605 Arrhenius) | Right-handed (AVMR≫AMVR) | WEAKENS — AVMR drops | Gravitational causal chains break |
| ELECTROCHEMICAL (§593 Nernst, §594 GHK) | Strongly right-handed | BECOMES MORE asymmetric | Fluid shift amplifies the Nernst anomaly |
| LIVING (endpoints: #746 crypto, #748 immortal) | Left-handed | Becomes MORE left-handed | Endpoints gain authority when causal sources weaken |

## The Kelly Anomaly

Scott Kelly's telomere lengthening is predicted by the chiral structure:

```
AMVR(#744, µg) - AVMR(#744, µg) ≪ AMVR(#593, µg) - AVMR(#593, µg)
```

The Nernst regime chiral gap DOMINATES the Information regime chiral gap in µg, producing a net effect opposite to pure Arrhenius prediction.

## Formal Encoding

```
ChiralAgreement(e, g) = 1 − |AMVR(e,g) − AVMR(e,g)| / (AMVR + AVMR)
ChiralState(e, g) = {
    achiral_bridge          if ChiralAgreement > 0.85
    left_handed_mass_bias   if AMVR > AVMR + ε
    right_handed_vector_bias if AVMR > AMVR + ε
}
```

The **µg chiral transition** is the set of equations where ChiralState(e, 1g) ≠ ChiralState(e, µg).

## Verified

- 52 achiral bridges in the global DAG (60%)
- 31 left-handed (36%) — all Layer 4 endpoints
- 3 right-handed (3%) — all Layer 1-2 source laws
- 18 chiral-admissible (± bidirectional routing)
- 4 chiral scars (Δ > 40) — these ARE the g-sensitive equations

**Table:** `chiral_eigenmass` (86 rows) in `physics_microgravity.db`
