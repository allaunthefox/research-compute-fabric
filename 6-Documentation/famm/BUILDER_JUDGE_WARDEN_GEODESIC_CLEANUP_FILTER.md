# Builder-Judge-Warden Geodesic Cleanup Filter

## Purpose

Add a triadic cleanup layer for the math forest.

The filter takes a messy equation, proof route, transform stack, NP search state, or FAMM packet and finds the shortest lawful cleanup path that preserves invariants and ends in a receipt.

```text
messy math object
→ Builder proposals
→ Judge receipts
→ Warden scars/blocks
→ accepted cleanup geodesic
→ NUVMAP Delta-DAG
→ exact receipt
```

## Core idea

```text
Builder = proposes cleanup moves.
Judge   = verifies law/invariant/receipt preservation.
Warden  = blocks unsafe collapse, drift, false merges, and scarred routes.
```

## Cleanup loss

```math
\mathcal L_{\mathrm{BJW}}(E)
=
\alpha C(E)
+
\beta R(E)
+
\gamma\Omega(E)
-
\delta I(E)
+
\lambda P(E)
```

Where:

| Term | Meaning |
|---|---|
| `C(E)` | complexity / byte / operator cost |
| `R(E)` | residual or unresolved tail |
| `Ω(E)` | FAMM scar / bad route pressure |
| `I(E)` | preserved invariant strength |
| `P(E)` | proof / receipt burden |

## Builder set

The Builder proposes constructive transformations:

```text
compactify
factor
project
transform
bind
delta-compress
merge DAG states
replace history with recurrence
replace search tree with exact gate
```

Formal sketch:

```math
B(E_t)
=
\operatorname{argmin}_{E'}
[
C(E')+R(E')
]
```

subject to a lawful transition candidate.

## Judge set

The Judge checks whether the move preserved the relevant object.

```math
J(E_t,E')=1
```

iff:

```math
\operatorname{Inv}(E_t)=\operatorname{Inv}(E')
```

and:

```math
\operatorname{Receipt}(E_t\to E')=\mathrm{PASS}
```

Judge tests include:

```text
same theorem
same payload
same exact verifier
same invariant
same boundary condition
same residual policy
same active chirality if chirality matters
```

## Warden set

The Warden blocks unsafe shortcuts:

```text
overcompression
false equivalence
NUVMAP false merge
wrong-handed chirality
missing boundary
unsealed residual
unsupported theorem claim
recurrence outside ROC
scarred transition repeated too often
```

Warden penalty:

```math
W(E_t,E')
=
\Omega_{\mathrm{scar}}
+
\Omega_{\mathrm{drift}}
+
\Omega_{\mathrm{boundary}}
+
\Omega_{\mathrm{receipt}}
```

Reject if:

```math
W(E_t,E')>\Theta_W
```

## Transition rule

```math
E_{t+1}
=
\begin{cases}
E' & \text{if } J(E_t,E')=1 \text{ and } W(E_t,E')\le \Theta_W \\
E_t+\operatorname{Scar}(E') & \text{otherwise}
\end{cases}
```

where:

```math
E'=B(E_t)
```

## Accepted geodesic

```math
\mathcal G^*
=
\operatorname{argmin}_{\mathcal G_{\mathrm{clean}}}
\sum_t
[
C(E_t)
+
R(E_t)
+
\Omega(E_t)
+
P(E_t)
]
```

subject to every transition passing Judge and Warden.

## Erdős-Szekeres calibration

Original route:

```text
scan all subsequences
→ check increasing/decreasing
```

Builder proposes:

```text
replace subsequence forest with (I_i, D_i) labels
```

Judge verifies:

```text
if a_i < a_j, then I_j > I_i
if a_i > a_j, then D_j > D_i
therefore labels are injective
```

Warden blocks:

```text
non-distinct sequence
wrong r/s bounds
infinite-domain overclaim
duplicate labels
```

Cleaned receipt:

```text
avoidance box has (r-1)(s-1) cells
sequence has one more point
injective labels impossible
PASS
```

## Stack placement

```text
Equation forest
→ Builder proposals
→ Judge receipts
→ Warden scars
→ BJW geodesic
→ NUVMAP Delta-DAG
→ cleaned equation
→ exact receipt
```

## No-drift boundary

This filter is a cleanup/search governor, not a proof generator by itself. Exactness still comes from the Judge and the downstream verifier. The Warden must block any cleanup path that hides assumptions, changes theorem strength, loses active chirality, or leaves residuals unsealed.

## Project sentence

The Builder-Judge-Warden filter turns mathematical cleanup into a lawful shortest-path problem: Builder proposes compression moves, Judge verifies invariant preservation, Warden blocks drift and scarred routes, and the accepted path becomes a delta-compressed NUVMAP DAG ending in an exact receipt.
