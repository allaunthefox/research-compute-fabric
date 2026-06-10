# RRC Shape Atomization: 16D Lego Brick System

## Overview

The Rainbow Raccoon Compiler (RRC) classifies equations into **6 shapes** based on
a **16-dimensional feature embedding**. Each dimension is a "lego brick"—an atomic
feature extracted from the equation. Shapes emerge as assembly patterns of these
bricks, forming the routing decisions in the RRC compilation pipeline.

## The 16D Lego Bricks

Defined in `Semantics.PathEpigeneticManifold.Dim16`  
(`0-Core-Formalism/lean/Semantics/Semantics/Core/PathEpigeneticManifold.lean:21`)

| # | Brick | Epigenetic role | Equation feature mapped |
|---|-------|-----------------|------------------------|
| 1 | `identity` | What the equation **is** | Equation object_id, type signature |
| 2 | `route` | How it got here | Route hint, compression/field/cad path |
| 3 | `scale` | Magnitude/range | Coefficient sizes, normalization bounds |
| 4 | `phase` | Alignment offset | Oscillatory phase, temporal alignment |
| 5 | `torsion` | Twist/deformation | Symmetry breaking, non-commutativity |
| 6 | `curvature` | Bending | Geometric curvature, nonlinearity |
| 7 | `energy` | Power/cost | Kinetic potential, dissipation |
| 8 | `velocity` | Rate of change | Time derivative coefficients |
| 9 | `residual` | Leftover/error | Weak axis count, approximation gap |
| 10 | `semanticMass` | Meaning density | Information content, token frequency |
| 11 | `confidence` | Certainty | Witness status, proof completeness |
| 12 | `density` | Sparsity | Matrix density, zero-cell fraction |
| 13 | `topology` | Connectivity | Braid adjacency (8×8 crossing matrix) |
| 14 | `witness` | Proof presence | Type witness, receipt validity |
| 15 | `underverse` | Quarantine side | Layout violations, quarantine routing |
| 16 | `time` | Temporal ordering | Step count, convergence timing |

Each brick is a `Q0_16` scalar (normalized [0,1] fixed-point) representing
expression level—how strongly that feature is present in the equation.

## The 6 RRC Shapes

Defined in `Semantics.RRCLogogramProjection.RRCShape`  
(`0-Core-Formalism/lean/Semantics/Semantics/RRCLogogramProjection.lean:18`)

| Shape | Brick assembly pattern | Typical equations |
|-------|----------------------|-------------------|
| **SignalShapedRouteCompiler** | `route` + `scale` + `velocity` dominant; `density` moderate; `residual` low | Compression routes, signal transforms |
| **ProjectableGeometryTopology** | `curvature` + `topology` + `phase` dominant; `torsion` moderate | Geometric PDEs, topological invariants |
| **CognitiveLoadField** | `semanticMass` + `energy` + `density` dominant; `residual` low | Field theories, semantic density equations |
| **CadForceProbeReceipt** | `energy` + `torsion` + `velocity` dominant; `identity` moderate | CAD force equilibrium, DAG constraints |
| **LogogramProjection** | `identity` + `witness` + `confidence` dominant; `underverse` absent | Logogram types with full receipts |
| **HoldForUnlawfulOrUnderspecifiedShape** | multiple bricks weak; `underverse` or `residual` elevated | Unclassified, negative controls |

Shapes are not mutually exclusive in brick space—they are **assembly pattern
prototypes**. The alignment gate disambiguates collisions using the PIST
classifier's structural vs. semantic distinction.

## Pipeline: Raw Features → 8×8 Matrix → Shape Classifier → Alignment Gate

```
┌─────────────────────────────────────────────────────────────────────┐
│ Python (I/O layer)                                                  │
│                                                                     │
│  rrc_equation_classifier_receipt.json                               │
│       │                                                             │
│       ▼                                                             │
│  build_corpus278.py                             pist_matrix_builder │
│    raw feature extraction                            .py            │
│    operator_tokens / inv_declared                       │           │
│    boundary_conds / template                            ▼           │
│       │                                     rrc_pist_predictions_   │
│       ▼                                     278_v1.json             │
│  Corpus278.lean  (AUTO-GENERATED)                │                  │
└───────────────────────────────────────────────┬───┘─────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Lean (decisions)                                                    │
│                                                                     │
│  corpus278 : List FixtureRow                         250 8×8       │
│       │                                          braid matrices    │
│       │                          ┌─────────────────┘               │
│       ▼                          ▼                                  │
│  PIST.Matrices278          PIST.Classify                            │
│   pistMatrices278           classifyByHash (base-5 poly)            │
│       │                          │                                  │
│       └──────────────────────────┘                                  │
│                        │                                            │
│                        ▼                                            │
│  FixtureRow.pistProxyLabel  : Option String                         │
│  FixtureRow.pistExactLabel  : Option String                         │
│                        │                                            │
│                        ▼                                            │
│  RRC.Emit.determineAlignment                                        │
│    → AlignmentStatus                                                 │
│    → compileRow → RrcRow (with Receipt)                             │
│    → emitCorpus → JSON bundle                                        │
│                        │                                            │
│                        ▼                                            │
│  AVMIsa.Emit  (SOLE output boundary)                                │
│    stamps avm.rrc_corpus278.bundle                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Alignment Gate Logic

Defined in `Semantics.RRC.Emit.determineAlignment`  
(`0-Core-Formalism/lean/Semantics/Semantics/RRC/Emit.lean:133`)

```
determineAlignment(row):
  1. No pistProxyLabel AND no pistExactLabel
     → missingPrediction (score 0)
  2. pistExactLabel == RRC shape string
     → alignedExact (score 100)
  3. pistProxyLabel == RRC shape string
     → alignedProxy (score 86)
  4. PIST label is a STRUCTURAL label
     ("LogogramProjection", "ProjectableGeometryTopology")
     AND RRC shape is a SEMANTIC shape
     (CognitiveLoadField, SignalShapedRouteCompiler,
      CadForceProbeReceipt, HoldForUnlawfulOrUnderspecifiedShape)
     → compatibleStructuralProjection (score 72)
  5. Otherwise → alignmentWarning (score 35)
```

The structural/semantic distinction is key: PIST currently predicts
"LogogramProjection" for all equations (structural view), while the RRC
classifier sees semantic routing shapes. The `compatibleStructuralProjection`
score bridges this gap without false promotion.

## How Shapes Emerge as Assembly Patterns

The 8×8 braid adjacency matrix (`Matrices278.pistMatrices278`) encodes the
**topology** brick directly. The PIST classifier (`Classify.classifyByHash`)
fingerprints each matrix via a **base-5 polynomial hash** and maps to a shape
name. This is a pure hash lookup over 109 unique fingerprints from 250 matrices.

The shape emerges when the 8-strand braid crossing pattern (8D DualQuaternion)
projects through each of the 16 dimensions. A CognitiveLoadField equation has
different braid interaction topology than a SignalShapedRouteCompiler, even when
both carry the same PIST structural label.

## Adding New Bricks (Disambiguating Collisions)

When two distinct equation classes collide under the current 16D embedding (e.g.,
both map to the same RRC shape but have different semantic meaning), a new brick
can be added:

### Steps

1. **Add the dimension** to `Dim16` in `PathEpigeneticManifold.lean`:
   ```lean
   inductive Dim16 where
     ...
     | newDimension
   ```

2. **Add the field** to `Manifold16`:
   ```lean
   structure Manifold16 where
     ...
     newDimension : Q0_16
   ```

3. **Update `get`/`set`** accessors for the new dimension.

4. **Define the extraction** of this feature from equations. If the extraction
   involves decision logic (not pure I/O), it must be written in Lean. If it's
   pure I/O (read existing field, normalize), Python is acceptable.

5. **Add a MarkerAction** if the new dimension needs special regulatory behavior
   (activate, damp, gateWitness, quarantine).

6. **Regenerate** `Corpus278.lean` via `build_corpus278.py` if the new brick
   comes from an existing JSON field.

7. **Update the hash fingerprint** in `Classify.lean` if the braid matrix
   construction changes (the matrix hash → shape mapping regenerates via
   `pist_matrix_builder.py`).

### Collision analysis

Current confusion matrix (from fixture rows):
- `CognitiveLoadField` x `SignalShapedRouteCompiler`: both get
  `compatibleStructuralProjection` because PIST assigns "LogogramProjection" to
  all rows. To disambiguate, add bricks that distinguish **operator token
  distribution** (e.g., `operatorDensity` or `tokenEntropy`).
- `ProjectableGeometryTopology` x `CadForceProbeReceipt`: both have `weakAxesCnt`
  8 but different braid matrices. Already distinguished by hash.
- `HoldForUnlawfulOrUnderspecifiedShape`: catch-all. Elevated `residual` or
  `underverse` bricks mark these.

## Receipt Flow

Each compiled row produces a `LogogramReceipt` with:
- `shape : RRCShape` — which assembly pattern matched
- `status : WitnessStatus` — `candidate` or `hold`
- `regime : SemanticRegime` — `beautifulTopologicalFolding`, `uglyAsymmetricPruning`,
  or `horribleManifoldTearing`
- `payloadBound`, `contradictionWitness`, `tearBoundary`, `detachedMass`,
  `residualLane` — boolean receipt fields

The admission gates (`typeAdmissible`, `mergeAdmissible`, `projectionAdmissible`)
form a hierarchy:

```
typeAdmissible
  → projectionAdmissible (non-tears plus repaired tears)
    → mergeAdmissible (non-tears only)
```

Torn logograms (horribleManifoldTearing) require complete repair evidence
(contradictionWitness + tearBoundary + detachedMass + residualLane) before they
can project (into quarantine lane). They can never merge.

## Source Files

| File | Purpose |
|------|---------|
| `0-Core-Formalism/lean/Semantics/Semantics/Core/PathEpigeneticManifold.lean` | 16D Dim16 definition, Manifold16, epigenetic regulation |
| `0-Core-Formalism/lean/Semantics/Semantics/RRCLogogramProjection.lean` | RRCShape inductive, LogogramReceipt, admission gates |
| `0-Core-Formalism/lean/Semantics/Semantics/RRC/Emit.lean` | FixtureRow, AlignmentStatus, determineAlignment, emitCorpus |
| `0-Core-Formalism/lean/Semantics/Semantics/RRC/Corpus278.lean` | Auto-generated 278 FixtureRows |
| `0-Core-Formalism/lean/Semantics/Semantics/PIST/Matrices278.lean` | Auto-generated 250 8×8 braid matrices |
| `0-Core-Formalism/lean/Semantics/Semantics/PIST/Classify.lean` | classifyByHash, classifyProxy, classifyExact |
| `0-Core-Formalism/lean/Semantics/Semantics/PIST/Spectral.lean` | SpectralProfile, powerIteration, computeSpectral |
| `0-Core-Formalism/lean/Semantics/Semantics/ReceiptCore.lean` | leanBuildReceipt function |
| `4-Infrastructure/shim/build_corpus278.py` | Python→Lean Corpus278 generator |
| `4-Infrastructure/shim/pist_matrix_builder.py` | Python 8×8 matrix + predictions builder |
| `shared-data/rrc_pist_predictions_278_v1.json` | PIST prediction artifact (250 unique equation_ids) |
