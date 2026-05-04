# Sidon Matrix over Goxel Domains

Status: HOLD / workbench projection
Authority: modeling spec; not canonical proof
Related: `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/AutopoieticNScalarField.md`, `docs/gcl/MassNumberGCLSubset.md`

## Purpose

This document defines how Goxels make the Sidon matrix cleaner.

A Goxel is an N-space shape inhabiting a geometric volume:

```text
G = { v in R^n : Phi_G(v) <= iso }
```

Because each Goxel has a bounded scalar-domain definition, collisions can be modeled as structured field-domain interactions instead of ambiguous voxel-cell overlaps.

## Core insight

Voxel collision asks:

```text
Do two discrete cells overlap?
```

Goxel collision asks:

```text
Do two bounded scalar sub-manifolds create an inadmissible intersection, resonance, degeneracy, or non-manifold junction under regime R?
```

The Sidon matrix becomes the audit surface for those pairwise and higher-order interactions.

## Sidon matrix definition

Let the active Goxel set be:

```text
G_set = { G_1, G_2, ..., G_k }
```

Define the Sidon matrix under regime `R` as:

```text
S_R[i,j] = SidonAudit_R(G_i, G_j)
```

where each matrix entry is not merely boolean. It is a typed audit record.

```ts
type SidonMatrixEntry = {
  left_goxel: string;
  right_goxel: string;
  regime: string;
  intersection_class:
    | "disjoint"
    | "tangent"
    | "transverse_intersection"
    | "nested"
    | "fusable"
    | "repulsive"
    | "singular"
    | "unknown";
  cb2_status: "pass" | "fail" | "unknown";
  compatibility: "compatible" | "incompatible" | "needs_closure";
  residual_score?: number;
  mass_budget_delta?: number;
  recommended_response:
    | "no_action"
    | "fuse"
    | "repel"
    | "hold"
    | "quarantine"
    | "request_receipts";
  receipts: string[];
};
```

## Why Goxels clean up the matrix

With voxels, the matrix tends to collapse into occupancy logic:

```text
occupied / empty
same cell / different cell
collision / no collision
```

With Goxels, the matrix can represent geometric relation classes:

```text
G_i disjoint from G_j
G_i tangent to G_j
G_i nested inside G_j
G_i smoothly fuses with G_j
G_i intersects transversely with G_j
G_i creates a singular junction with G_j
G_i must repel from G_j under regime R
```

That makes Sidon analysis about **shape-domain compatibility**, not just cell occupancy.

## Scalar-field form

Each Goxel carries a local potential:

```text
Phi_i = Phi_Gi
Phi_j = Phi_Gj
```

A pairwise relation can be evaluated through:

```text
I_ij = { v in Omega_R : Phi_i(v) <= iso_i and Phi_j(v) <= iso_j }
```

The pair is easy if:

```text
I_ij = empty
```

The pair needs audit if:

```text
I_ij != empty
```

or if the boundaries approach below a regime threshold:

```text
dist_R(boundary(G_i), boundary(G_j)) <= epsilon_contact
```

## CB2 relationship

CB2 is the contradiction/collision detector. In this model, CB2 becomes one field of the Sidon matrix, not the whole matrix.

```text
CB2(G_i union G_j) = 0
```

means only:

```text
no detected collision contradiction under the current CB2 predicate
```

It does not, by itself, prove valid fusion.

## Fusion row condition

A Sidon matrix entry may recommend fusion only if:

```text
FusionCandidate_R(G_i, G_j) iff
  S_R[i,j].cb2_status = pass
  and S_R[i,j].compatibility = compatible
  and Regular(boundary(G_i union G_j))
  and m_A(G_i union G_j; R) <= Budget_R
```

Then the system may construct:

```text
G_ij = Fuse_R(G_i, G_j)
```

The fused result remains a candidate until receipts are attached.

## Repulsion row condition

A Sidon matrix entry may recommend repulsion when:

```text
RepulsionCandidate_R(G_i, G_j) iff
  S_R[i,j].cb2_status = fail
  or S_R[i,j].compatibility = incompatible
  or S_R[i,j].intersection_class in {singular, transverse_intersection}
```

Then the system may adjust local potentials:

```text
Phi_i' = Phi_i + Delta_repulse_i
Phi_j' = Phi_j + Delta_repulse_j
```

subject to budget and regularity gates.

## Higher-order Sidon tensor

The pairwise Sidon matrix is the first pass.

Some failures only appear when three or more Goxels interact.

Define optional higher-order audit tensors:

```text
S_R[i,j,l] = SidonAudit3_R(G_i, G_j, G_l)
S_R[i1,...,im] = SidonAuditM_R(G_i1, ..., G_im)
```

Use these only when pairwise passes but global field fusion still produces residual, singularity, or budget failure.

## Sidon matrix as graph

The Sidon matrix induces a typed graph:

```text
nodes = Goxels
edges = SidonMatrixEntry relations
```

Edge labels:

```text
disjoint
fusable
repulsive
singular
needs_closure
quarantined
```

This graph is projection-only. It helps route repair and audit work; it is not proof.

## Mass-number integration

Each row/column can carry aggregate metabolic load:

```text
row_cost(G_i) = sum_j cost(S_R[i,j])
```

A high row cost means the Goxel is interaction-heavy. It may indicate:

- high geometric centrality
- unresolved collision pressure
- excessive fusion/repulsion obligations
- mass-number budget stress
- need for decomposition into smaller Goxels
- need for quotient/closure repair

High row cost is an audit priority, not evidence of truth.

## Cleaner modeling sentence

```text
The Sidon matrix is no longer a table of voxel collisions. It is a typed compatibility matrix over N-space geometric-volume elements.
```

## Failure modes captured

The Goxel-based Sidon matrix can represent:

```text
cell overlap
boundary tangency
non-manifold singularity
projection collision
regime mismatch
unclosed mass interaction
SmoothMax residual
false fusion
false separation
higher-order junction failure
```

## Validator requirements

Every Sidon matrix entry must declare:

```text
left_goxel
right_goxel
regime
intersection_class
cb2_status
compatibility
recommended_response
receipt status
```

If any of those are missing, the row is `HOLD`.

## Operating sentence

```text
Goxels clean the Sidon matrix by turning collision detection into typed compatibility auditing over bounded scalar sub-manifolds.
```
