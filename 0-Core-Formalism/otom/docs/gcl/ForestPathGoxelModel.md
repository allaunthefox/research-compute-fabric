# Forest Path Model over Goxel Domains

Status: HOLD / workbench projection
Authority: modeling spec; not canonical proof
Related: `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/SidonMatrixGoxelModel.md`, `docs/gcl/SidonSolvedDomainTestProtocol.md`, `docs/gcl/AutopoieticNScalarField.md`

## Purpose

This document defines how Goxels resolve the fuzziness around the forest metaphor and the paths inside it.

The forest is no longer a vague graph of possible routes. It becomes a typed field of bounded geometric-volume elements with auditable transitions.

```text
forest
  -> Goxel field / typed domain ecology

path
  -> admissible transition sequence through Goxel domains

fuzziness
  -> unresolved audit state, projection ambiguity, or missing closure
```

## Core idea

A Goxel is an N-space shape inhabiting a geometric volume:

```text
G = { v in R^n : Phi_G(v) <= iso }
```

A forest is a collection of such domains plus their compatibility relations.

```text
Forest_R = (G_set, S_R, P_R, Gates_R)
```

where:

```text
G_set    = active Goxels / domains / clearings / obstacles
S_R      = Sidon compatibility matrix over Goxels
P_R      = path relation / admissible transition graph
Gates_R  = audit gates for path validity
```

## Forest objects

In this model, forest language becomes typed.

| Forest term | Goxel-field meaning |
|---|---|
| tree | stable high-mass Goxel / semantic basin / persistent domain |
| trunk | central support path inside a Goxel domain |
| branch | admissible outgoing transition family |
| clearing | low-residual navigable domain |
| thicket | high-residual ambiguous region |
| trail | locally admissible transition sequence |
| hidden path | candidate path with missing projection/receipt |
| dead end | path blocked by gate or budget failure |
| root | provenance/seed/source constraint |
| canopy | high-level projection over many domains |
| undergrowth | unresolved local detail / microvoxel or goxel clutter |

## Path definition

A path is not merely an edge in a graph.

A path is a typed transition sequence through Goxel domains:

```text
Path_R = [G_0 ->_R G_1 ->_R ... ->_R G_k]
```

Each transition must declare:

```text
source Goxel
target Goxel
regime R
transition class
compatibility status
cost
residual
receipts
```

## Transition classes

```ts
type ForestPathTransition = {
  source_goxel: string;
  target_goxel: string;
  regime: string;
  transition_class:
    | "adjacent"
    | "overlapping"
    | "nested"
    | "fusable"
    | "bridge"
    | "projection_jump"
    | "blocked"
    | "unknown";
  compatibility: "compatible" | "incompatible" | "needs_closure";
  path_cost: number;
  residual_score?: number;
  mass_budget_delta?: number;
  receipt_status: "missing" | "present" | "failed" | "waived";
};
```

## Fuzziness resolution

Earlier forest/path language was fuzzy because the objects were not typed.

Goxels resolve this by forcing every fuzzy path to become one of these states:

```text
KnownPath
  transition sequence is declared and gates pass

CandidatePath
  transition sequence exists but receipts or closure are missing

ProjectionPath
  path appears in a rendered/projection layer but lacks source-domain proof

ResidualPath
  path is suggested by anti-music/residual structure but not yet stabilized

BlockedPath
  path fails a gate: CB2, budget, compatibility, regularity, or safety

QuarantinedPath
  path is misleading, unsafe, or overbroad
```

So fuzziness is not erased. It is typed.

## Relation to the Sidon matrix

The Sidon matrix gives pairwise domain compatibility.

```text
S_R[i,j] = SidonAudit_R(G_i, G_j)
```

The forest path graph is derived from compatible Sidon entries:

```text
Edge_R(G_i, G_j) exists iff
  S_R[i,j].compatibility in {compatible, needs_closure}
  and S_R[i,j].intersection_class not in {singular}
  and transition budget is finite
```

Then the path system can ask:

```text
Can I move from G_a to G_b through admissible domains?
Which routes are cheapest?
Which routes are unresolved?
Which routes are projection artifacts?
Which routes create collision pressure?
```

## Path cost

Path cost is finite accounting, not truth.

```text
C_R(Path) = sum_t C_R(G_t -> G_{t+1}) + residual_penalty + projection_penalty + repair_penalty
```

Candidate terms:

```text
transition cost
residual / anti-music cost
mass-number budget delta
projection distortion
repair cost
receipt debt
```

## Forest as semantic navigation

For the internal wiki, the forest is a semantic navigation space.

```text
concepts      -> Goxels
relations     -> Sidon/transition entries
pages         -> projections
paths         -> admissible reasoning routes
broken links  -> missing transitions
confusion     -> untyped residual or projection conflict
```

This gives a concrete way to audit research navigation:

```text
If a reader cannot follow a path, check whether the path is:
  missing a transition
  missing a receipt
  crossing a projection boundary
  passing through a high-residual thicket
  colliding with another domain
  relying on an undefined alias
```

## Forest path validator

A valid forest path must declare:

```text
start_goxel
end_goxel
ordered transition list
regime
path cost
claim state
authority scope
projection/canonical boundary
receipt status
failure mode if blocked
```

If any are missing, the path is `CandidatePath` or `HOLD`.

## How this furthers the larger goals

```text
GCL
  forest nodes become encoded concept-genotypes with expressed wiki/graph phenotypes

Goxels
  semantic regions become bounded domains rather than vague bubbles

Sidon matrix
  path adjacency is derived from typed compatibility, not loose association

Mass-Number
  path cost and row/column interaction load become finite audit metrics

Compression
  lawful paths may compress navigation better than naive graph links

Signal/noise
  fuzzy paths become residuals to classify, not noise to discard
```

## Boundary

A forest path is not proof.

```text
path exists != claim true
short path != correct path
central node != true node
pretty graph != valid reasoning
```

A path is an auditable route through typed domains.

## Operating sentence

```text
The forest becomes clear when every path is a typed transition through Goxel domains, and every fuzzy route is classified as candidate, residual, projection, blocked, or receipt-backed.
```
