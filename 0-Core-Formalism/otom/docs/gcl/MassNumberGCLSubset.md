# Mass-Number GCL Subset

Status: HOLD / workbench projection
Authority: not canonical until schema, validator, and Lean receipts exist
Related Linear issue: RES-2368

## Purpose

Define a Mass-Number subset of GCL using existing GCL expansion slots instead of inventing a separate language.

GCL remains the host grammar. MN-GCL is a typed expansion profile that adds mass-number semantics, admissibility closure, torsion handling, finite thermodynamic accounting, and receipt-gated promotion rules.

## Canonical doctrine

```text
Mass is not distance.
Mass becomes distance only through admissibility closure.
```

MN-GCL may express raw semantic mass, route-cost pressure, torsion, residual weight, and nuclide-inspired mass-number notation. It may not treat raw mass-number magnitude as a metric until closure has been applied.

## Host/subset split

```text
GCL
  = host grammar / concept language / expansion-slot container

MN-GCL
  = Mass-Number subset using GCL expansion slots
  = typed mass coordinates
  = admissibility rules
  = closure operators
  = receipt-gated promotion
```

## Expansion slots

```text
slot.symbolic_code
  nuclide-style labels, isotope-like notation, mandala/radial markers, custom math glyph references

slot.mass_profile
  raw_mass_number, semantic_density, basin_strength, route_cost, torsion

slot.admissibility
  compatibility kernel, finite counters, receipt coverage, Lean gate status

slot.closure
  pseudometric closure, zero-distance quotient, quotient metric target

slot.projection
  wiki page, graph node, Three.js/WebGPU render, Mermaid/GraphML view

slot.receipts
  Lean theorem, benchmark, dataset row, simulation trace, source audit
```

## Minimal object model

```ts
type MassNumberGCLNode = {
  gcl_id: string;
  kind: "concept" | "symbol" | "claim" | "simulator" | "dataset" | "gate";
  mass_value: MassValue;
  semantic_density?: number;
  basin_strength?: number;
  torsion?: number;
  route_cost?: number;
  admissibility_status: "raw" | "held" | "closed" | "quotiented" | "reviewed";
  claim_state: "U_scope" | "HOLD" | "V_scope" | "REVIEWED" | "QUARANTINE";
  authority_scope: "workbench_projection" | "canonical_lean" | "receipt_backed" | "external_source" | "simulation_only";
  receipts: string[];
  projection_refs: string[];
  canonical_refs: string[];
};
```

## MassValue

MN-GCL is finite-first. It does not normalize infinity directly.

```ts
type MassValue =
  | { tag: "FiniteMass"; value: number; unit?: "dimensionless" }
  | { tag: "NaNMass"; reason: NaNMassReason; evidence: string[] }
  | { tag: "ClosedMass"; value: number; closure_receipt: string };

type NaNMassReason =
  | "division_by_unclosed_zero"
  | "unbounded_route_cost"
  | "missing_admissibility"
  | "regime_mismatch"
  | "infinite_projection_artifact"
  | "comparison_without_common_closure";
```

## NaNMass doctrine

```text
Apparent infinity is a diagnostic, not a destination.
NaNMass means: the current coordinate system failed to close the mass.
```

Infinity-like behavior routes as:

```text
Infinity-like expression
  -> unresolved closure
  -> NaNMass
  -> HOLD
  -> attempt admissibility repair
  -> finite surrogate | quotient closure | quarantine
```

## Thermodynamic objection

MN-GCL rejects raw infinity as a mass value because a physically realized mass, energy, entropy, memory, or work state must be bounded by finite resources in any local executable regime.

Completed infinity would require infinite energy, infinite storage, infinite time, or an undefined heat/work accounting boundary.

Therefore, when an expression behaves as if it is infinite, MN-GCL treats that as evidence of an unclosed model boundary rather than as a valid mass.

```text
Thermodynamic accounting fails
  -> resource boundary not closed
  -> apparent infinity
  -> NaNMass
  -> HOLD
  -> repair by limit, renormalization, quotient, finite surrogate, or quarantine
```

This does not deny mathematical infinities as abstract objects. It denies them direct authority as thermodynamic mass values inside finite executable regimes.

## Universe-local rule

```text
Other universe:
  may permit completed infinity as a native object

This executable universe:
  requires finite thermodynamic accounting
  rejects infinity as MassValue
  routes infinity-like behavior to NaNMass
```

The boundary is operational, not metaphysical. This regime only admits mass values that can be typed, accounted, closed, and receipt-backed under finite resources.

## Closure path

```text
Raw GCL node
  -> Mass profile annotation
  -> Compatibility kernel K_R(x,y)
  -> Admissible weighted edge set
  -> Shortest-path closure
  -> Pseudometric
  -> Zero-distance quotient
  -> Metric target
```

## Validator rule

A Mass-Number GCL node must not be promoted unless it declares:

- claim_state
- authority_scope
- admissibility_status
- MassValue type
- receipt list
- projection/canonical boundary

High mass-number score may increase audit priority. It cannot promote a claim by itself.

Rendered graph weight, visual centrality, symbolic beauty, or emotional intensity are not proof.

## Related anchors

- RES-2368: Mass-Number Admissibility Closure
- Research Wiki Hub / Research Wiki Index
- SemanticMassOntologyWikiStack.md
- Ring0InternalAlarmGate
- Graph Diff + Torsion Detector
