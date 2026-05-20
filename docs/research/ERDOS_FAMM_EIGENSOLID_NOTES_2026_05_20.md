# Erdős FAMM / Eigensolid Research Notes

Date: 2026-05-20
Status: BEAUTIFUL_PROVISIONAL

## Objective

Treat solved Erdős structures and finite witness packets as FAMM scar priors.

Use:

- NUVMAP projection
- braid aggregation
- rope collapse
- eigensolid closure
- selective residual memory

to reduce combinatorial explosion.

## Core Pipeline

solved/scar packets
-> NUVMAP projection
-> braid traversal
-> chirality filtering
-> rope aggregation
-> eigensolid closure
-> exact receipt verification

## Exact Gate Boundary

Active proof-spine paths required:

- gate = G:111
- min_omega = 0

All other routes are treated as diagnostic scars rather than active proof paths.

## Color Taxonomy

Green:

core exact receipt spine

Blue:

active zero-residual reserve

Cyan:

wide-alpha cold reserve

Slate:

large-alpha cold reserve

Amber:

failed gate / negative scar only

## Eigensolid Families

Leaf eigensolids:

exact residue-alpha leaves

Residue eigensolids:

collapse multiple leaves by residue class

Alpha eigensolids:

cross-residue alpha families

Phase eigensolids:

chirality / phase closure families

Global eigensolid:

run-now admissible closure body

## Alpha Family Collapse

Observed useful alpha family:

{3, 7, 11, 15, 19, 23}

Expanded rescue family:

{27, 31, 35, 39, 43, 47, 51, 55, 59}

Unused search window:

63..127

## Structural Collapse

For fixed alpha:

x = (p + alpha)/4
b = p x

Need:

e divides b^2

e == -b mod alpha

Then:

y = (b^2/e + b)/alpha
z = (e + b)/alpha

The swarm collapses from:

millions of braid candidates

to:

fixed-alpha divisor-residue channels.

## Inclusion-Exclusion Interpretation

Eigensolid closure behaves as topological inclusion-exclusion:

Count lawful braid routes.
Subtract overlapping duplicates.
Add back higher-order closure overlaps.
Continue until only the stable reconstruction body remains.

## Attention Residuals Interpretation

Attention Residuals map directly to FAMM selective reuse.

Instead of all prior braid states contributing equally:

alpha_(t,i) = softmax(M_i - Omega_i + S_i)

Only high-mass, low-obstruction, scar-supported states dominate closure.

## Core Insight

The architecture is not searching proofs naively.

It is constructing admissible reconstruction topology under finite scar guidance.
