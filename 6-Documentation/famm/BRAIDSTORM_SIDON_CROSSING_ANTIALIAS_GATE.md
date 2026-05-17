# BraidStorm Sidon Crossing Anti-Alias Gate

## Purpose

Use Sidon pair-sum uniqueness to give every BraidStorm crossing a collision-free additive address.

This is the first concrete problem selected for the Sidon FAMM Map:

```text
Given m BraidStorm strands,
assign each strand a Sidon label a_i,
so every unordered crossing {i,j} has a unique address a_i + a_j.
```

This solves the pair-address aliasing problem for BraidStorm receipts, scars, delta edges, coarsening agents, and NUVMAP handoffs.

## Problem statement

Given strands:

```math
s_1,s_2,\dots,s_m
```

assign labels:

```math
a_i\in A\subset[1,N]
```

such that:

```math
a_i+a_j=a_k+a_l
\Rightarrow
\{i,j\}=\{k,l\}
```

for unordered pairs, usually with `i <= j` if self-crossings are allowed or `i < j` if only distinct-strand crossings are allowed.

## Crossing address

```math
\operatorname{addr}(i,j)=a_i+a_j
```

Every crossing event becomes addressable:

```math
\beta_{ij}:(s_i,s_j)\to(s_i',s_j',r_{ij},\epsilon_{ij},\Omega_{ij})
```

with:

```math
r_{ij}=H(\operatorname{addr}(i,j),\Delta_{ij},\epsilon_{ij},\Omega_{ij})
```

## FAMM object

```math
\mathfrak C_{\mathrm{BraidSidon}}
=
A_{16}(u_{\mathrm{braid\_sidon}})
\otimes
[
\Sigma_{\mathrm{strand}}
+
\Sigma_A
+
\Sigma_{2A}
+
\Sigma_{\mathrm{crossing}}
+
\Sigma_{\mathrm{collision}}
+
\Sigma_{\mathrm{scar}}
+
\Sigma_{\mathrm{receipt}}
]
```

## Residual

```math
R_{\mathrm{SidonCross}}
=
\left|\{(i,j,k,l):a_i+a_j=a_k+a_l,\;\{i,j\}\ne\{k,l\}\}\right|
```

Solved means:

```math
R_{\mathrm{SidonCross}}=0
```

## Theodorus/Sidon capacity prior

For ordinary integer Sidon labels in `[1,N]`, use the rough routing prior:

```math
|A|\sim\sqrt N
```

So for `m` strands:

```math
N\approx m^2
```

Examples:

| Strands | Address budget prior |
|---:|---:|
| 16 | 256 |
| 32 | 1024 |
| 64 | 4096 |
| 128 | 16384 |
| 256 | 65536 |

This is a capacity prior, not a constructive maximality proof.

## Integer versus modular mode

Two operational modes are supported:

| Mode | Meaning | Use |
|---|---|---|
| `integer` | pair sums are unique as integers | safest receipt; direct additive address |
| `modular` | pair sums are unique modulo `N` | useful for fixed-width address rings / hardware registers |

The Warden must record which mode was used.

## Coarsening behavior

If two distinct crossings alias:

```text
crossing(i,j) and crossing(k,l) share address
→ collision scar
→ coarsen that address basin
→ downweight future fine routing through that label assignment
→ reopen only if labels or address mode change
```

## BraidStorm placement

```text
BraidStorm strand registry
→ Sidon label assignment
→ crossing address map
→ crossing receipt
→ FAMM scar ledger
→ NUVMAP Delta-DAG edge
→ coarsening cache if collision
```

## Builder-Judge-Warden mapping

| Role | Use |
|---|---|
| Builder | propose Sidon labels / address budget / modular or integer mode |
| Judge | verify pair-sum injectivity and emit zero-collision receipt |
| Warden | block aliasing, false maximality, wrong address mode, and unreceipted collisions |

## Claim boundary

This gate does not prove BraidStorm convergence. It solves a narrower infrastructure problem:

```text
pairwise crossings get collision-free additive addresses.
```

## Project sentence

The BraidStorm Sidon Crossing Anti-Alias Gate assigns every strand a Sidon label so each pairwise crossing has a unique additive address, letting FAMM receipts, NUVMAP Delta-DAG edges, scars, and coarsening agents attach to the correct interaction without pair-address collision.
