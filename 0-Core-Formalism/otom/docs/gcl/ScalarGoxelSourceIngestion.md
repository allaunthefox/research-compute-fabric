# Scalar / Goxel Source Ingestion Note

Status: HOLD / source-ingestion note
Authority: normalization record; not canonical proof
Related:

- `docs/gcl/AutopoieticNScalarField.md`
- `docs/gcl/GoxelAuditBridge.md`
- `docs/gcl/HolyDiverGoxelMOIMBridge.md`
- `docs/gcl/SidonMatrixGoxelModel.md`
- `docs/gcl/ENEUntrackedConceptInventory.md`

## Purpose

This note records the source-layer concepts from the pasted scalar-field / Goxel material and states how they should be normalized into the GCL/OTOM docs.

The paste contains the fossil layer for these concepts:

```text
Hoxel excision
0D scalar seed
n-dimensional adaptive scalar field
zero-crossing / sublevel-set surface
Anti-Music residual
Mass-Number metabolic cost
Inverse Ascent Gate
CB2 collision audit
Goxel as geometric-volume element
SmoothMax fusion
adaptive/lifeform metaphor
```

The material is accepted as a workbench source, not as proof.

## Accepted core concepts

### 1. Excise fixed grid ontology

Accepted:

```text
The system should not be defined as a fixed 1024^4 grid or fixed 4D hoxel array.
```

Normalized form:

```text
The executable regime declares finite dimension n, domain Omega, field Phi, projection, and resource budgets.
```

### 2. 0D scalar seeds

Accepted:

```text
0D scalar seeds are the genotype-like source objects that perturb or define a field.
```

Normalized form:

```text
S = { (s_i, psi_i, theta_i) } for i = 1,...,k
```

where:

```text
s_i = finite n-space coordinate
psi_i = perturbation strength
theta_i = seed metadata / type / regime parameters
```

### 3. Adaptive scalar field

Accepted:

```text
The field adapts its geometry, resolution, and topology around active seeds.
```

Normalized form:

```text
Phi : Omega x T -> R
```

with field evolution governed by a declared energy functional or PDE, not by an unconstrained self-referential assertion.

### 4. Surface as level set

Accepted:

```text
The phenotype surface is a level set or sublevel set of the scalar field.
```

Normalized forms:

```text
M_iso(t) = { v in Omega : Phi(v,t) = iso and ||grad Phi(v,t)|| > epsilon_grad }
```

and for a Goxel:

```text
G = { v in R^n : Phi_G(v) <= iso }
```

### 5. Anti-Music residual

Accepted:

```text
Anti-Music is the structured residual / curvature / non-harmonic cost of the field.
```

Normalized form:

```text
E_R(Phi) = integral_Omega ||(I - H_R) Phi||^2 dv
```

or a curvature surrogate:

```text
E_R_curv(Phi) = integral_Omega |Delta Phi|^2 dv
```

### 6. Mass-Number as finite metabolic accounting

Accepted:

```text
Mass-Number scores finite field cost, residual burden, topological complexity, active cache/materialization pressure, and route cost.
```

Normalized form:

```text
m_A(Phi; R)
  = w_R * E_R(Phi)
    + w_G * G_topo(Phi)
    + w_B * B_active(Phi)
    + w_C * C_route(Phi)
```

Boundary:

```text
Mass-Number is not SI mass by default.
Mass-Number is not merely volume.
Mass-Number may include volume only as one declared component.
```

### 7. Inverse Ascent Gate

Accepted:

```text
Updates/mutations must pass resource, topology, regularity, and receipt gates before promotion.
```

Normalized form:

```text
AscentAllowed(A, Phi, Phi') iff
  m_A(Phi'; R) <= Budget_R
  and CB2(Phi') = 0
  and Regular(M_iso')
  and ReceiptsRequired(A) are present or explicitly waived by regime
```

### 8. Goxel as geometric-volume element

Accepted:

```text
A Goxel is an N-space shape inhabiting a geometric volume.
```

Normalized definition:

```text
G = { v in R^n : Phi_G(v) <= iso }
```

Operating sentence:

```text
A Goxel is an N-space shape inhabiting a geometric volume, expressed as a bounded scalar sub-manifold and admitted into ordinary editing workflows only through declared projection, audit, and receipt gates.
```

## Corrected / blocked source claims

The paste includes several useful but overstrong statements. These must remain corrected everywhere.

### Blocked claim: CB2 alone proves viability

Do not use:

```text
CB2(A) = 0 -> manifold is topologically consistent and viable.
CB2(A) = 0 <-> manifold is viable.
CB2(Goxel_A union Goxel_B) = 0 -> volumes are topologically fused.
```

Correct form:

```text
CB2 = 0 is a necessary gate component, not a complete proof of viability.
```

Use:

```text
Viable_R(Phi) iff
  CB2(Phi) = 0
  and Regular(M_iso)
  and m_A(Phi; R) <= Budget_R
  and ClosureStatus(Phi) in {closed, quotiented, reviewed}
```

For Goxel fusion:

```text
FusionAllowed_R(G_A, G_B) iff
  CB2(G_A union G_B) = 0
  and Compatible_R(G_A, G_B)
  and Regular(boundary(G_A union G_B))
  and m_A(G_A union G_B; R) <= Budget_R
  and ReceiptsRequired(fusion) are present or explicitly marked missing
```

Then:

```text
FusionAllowed_R(G_A, G_B) -> may construct fused candidate G_AB
```

### Blocked claim: SmoothMax guarantees zero residual

Do not use:

```text
SmoothMax always maintains zero Anti-Music residual at Goxel junctions.
```

Correct form:

```text
SmoothMax is a candidate fusion operator. Residual must be measured.
```

Use:

```text
Phi_Total = SmoothMax_R(Phi_G1, ..., Phi_Gk)
```

with required declarations:

```text
regime R
smoothing parameter
continuity class
residual measurement
regularity gate
receipts
```

### Blocked claim: infinite executable dimension

Do not use:

```text
n = infinity
0D seed in infinite dimensions
infinite effective proof/resolution
```

Correct form:

```text
n is finite and regime-declared for executable purposes.
```

If unbounded dimensionality appears, route to:

```text
NaNMass
LimitBoundary
ProjectionArtifact
RegimeMismatch
```

### Blocked claim: topological errors are mathematically unreachable

Do not use:

```text
The system is immune to holes, inverted normals, or non-manifold geometry.
```

Correct form:

```text
The system detects, gates, repairs, quarantines, or refuses invalid topology when detectors and receipts are present.
```

### Blocked claim: Mass-Number directly proportional to volume

Do not use globally:

```text
m_A is directly proportional to volume.
```

Correct form:

```text
volume may be one mass component under a declared regime.
```

Candidate:

```text
m_A(G; R) = w_V * Volume_R(G) + w_R * E_R(G) + w_T * TopoCost(G) + w_C * ComputeCost(G)
```

## Canonical normalized equation family

Avoid the source's implicit self-referential integral form unless it is defined as an energy functional.

Preferred workbench form:

```text
partial_t Phi(v,t)
  = - delta E[Phi; S] / delta Phi(v,t)
```

with:

```text
E[Phi; S]
  = integral_Omega [
      alpha/2 * ||grad Phi||^2
    + beta/2  * |Delta Phi|^2
    + gamma   * V(Phi)
    + eta     * R_anti(Phi)
    - F_S(v) * Phi(v)
    ] dv
```

and:

```text
F_S(v) = sum_i psi_i * K_theta(v, s_i)
```

## Source-to-doc mapping

| Source phrase | Canonical home | Status |
|---|---|---|
| 0D scalar as seed/DNA | `AutopoieticNScalarField.md` | accepted with finite regime |
| Field adapts like lifeform | `AutopoieticNScalarField.md` | accepted as model metaphor |
| Goxel | `GoxelAuditBridge.md` | accepted and strengthened |
| SmoothMax fusion | `GoxelAuditBridge.md` / `SidonMatrixGoxelModel.md` | accepted as candidate operator only |
| Sidon Collision / CB2 | `SidonMatrixGoxelModel.md` | accepted as gate field, not whole proof |
| Anti-Music residual | `AutopoieticNScalarField.md` | accepted as residual/curvature cost |
| Mass-Number metabolism | `MassNumberGCLSubset.md` / `MOIMConcepts.md` | accepted as finite accounting |
| Inverse Ascent | `AutopoieticNScalarField.md` | accepted as conjunctive gate |
| n-dimensional organism | `AutopoieticNScalarField.md` | accepted only as finite-regime architecture |
| Managed manifold | `GoxelCADFluidBridge.md` / `ThreeJSGoxelWeirdnessBridge.md` | accepted as runtime projection frame |

## Implementation consequences

The source material supports these immediate engineering tasks:

```text
registry/equation_forest_kernels.json
registry/holy_diver_modules.json
scripts/sidon_goxel_fixture_runner.py
outputs/sidon_matrix/summary.md
Three.js WeirdnessClassifier
CAD/fluid Goxel bridge validator
Betti overlay/audit receipt class
```

## Boundary

This ingestion note does not promote source prose to theorem.

```text
source paste != proof
useful metaphor != validated biology
field render != topology proof
CB2 pass != viability proof
SmoothMax visual smoothness != zero residual
```

## Operating sentence

```text
The pasted scalar-field material is accepted as the source fossil for the Goxel-field architecture, but its proof boundaries are corrected: finite regimes only, SmoothMax as candidate fusion, CB2 as one gate component, and Mass-Number as multi-term finite accounting rather than volume or physical mass alone.
```
