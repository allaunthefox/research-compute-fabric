# NUVMAP Delta-DAG Search Compressor

## Purpose

Make the NP-search acceleration stack explicitly shardable.

The stack is now:

```text
SEMANTIC_MASS_ROUTE_PLOW
→ 16D_CHAOS_GAME_FIELD_SHRINKER
→ DELTA_STREAM
→ NUVMAP_DAG
→ NOGOOD_SCAR_CACHE
→ EXACT_RECEIPT
```

The key distinction:

```text
Delta compression shrinks the path.
NUVMAP DAG shrinks the search topology.
```

## Why this tilts the needle

A normal backtracking solver creates a tree. Many branches can produce equivalent remaining subproblems. A tree repeats them.

A NUVMAP DAG stores projected state addresses and merges equivalent frontier basins:

```math
D_{\mathrm{NUVMAP}}
=
(V_{\mathrm{state}},E_{\Delta},h)
```

Each node is an addressed projected state:

```math
\nu_t
=
h(
G,
\text{assignment frontier},
\text{domains},
\text{scars},
\text{residual}
)
```

Each edge is only a legal delta:

```math
e_t=(\nu_t,\Delta_t,\nu_{t+1})
```

## FAMM object

```math
\mathfrak C_{\Delta\mathrm{DAG}}
=
A_{16}(u_G)
\otimes
[
\Sigma_G
+
\Sigma_{\Delta}
+
\Sigma_{\mathrm{NUV}}
+
\Sigma_{\mathrm{DAG}}
+
\Sigma_{\mathrm{nogood}}
+
\Sigma_{\mathrm{resid}}
+
\Sigma_{\mathrm{receipt}}
]
```

## NUVMAP address

```math
h_{\mathrm{NUV}}(s)
=
h(
\Pi_{\mathrm{frontier}}(s),
\Pi_{\mathrm{domain}}(s),
\Pi_{\mathrm{scar}}(s),
\Pi_{\mathrm{residual}}(s),
\Pi_{\mathrm{sym}}(s)
)
```

This is stronger than raw memoization because it does not ask only whether the state is byte-identical. It asks whether the projected route basin is equivalent.

## Sharding model

| Shard | Contents | Local verification |
|---|---|---|
| Base instance shard | graph / exact-cover / SAT instance | hash matches manifest |
| Route-rule shard | deterministic FAMM route rule and weights | rule hash matches manifest |
| NUVMAP node shard | projected frontier/domain/scar/residual address | node hash recomputes |
| Delta-edge shard | legal operation from parent to child | replay parent + delta → child |
| Nogood/scar shard | failed basin, contradiction, or forbidden transition | scar hash and projection match |
| Solution-path shard | ordered edge hashes | path joins from root to receipt |
| Exact receipt shard | final verifier output | residual = 0 |

## Multiplicative gain

```math
G_{\mathrm{total}}
=
G_{\mathrm{route}}
\cdot
G_{\Delta}
\cdot
G_{\mathrm{DAG}}
```

The earlier estimate was:

```text
FAMM route shortening: >= 393.7×
delta trace shrink:    ~30×
```

So before DAG merging:

```text
>= 11,800× effective route-trace shrink
```

With NUVMAP DAG merging:

```text
40% redundant frontier states → ~20,000×
70% redundant frontier states → ~39,000×
```

These are architecture estimates, not proof of general-case NP collapse.

## No-drift boundary

This is not a P vs NP claim. It is a route/topology/receipt compression layer. Exactness still comes from the final verifier: graph coloring conflict count zero, exact cover residual zero, SAT formula satisfied, Lean proof accepted, or other domain-specific receipt.
