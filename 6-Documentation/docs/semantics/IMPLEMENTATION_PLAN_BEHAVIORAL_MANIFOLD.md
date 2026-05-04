# Implementation Plan: Behavioral Manifold → Research Stack
## Concrete Deliverables with Build Verification

**Target**: Port the MOIM (Meta-Ontological Inversion Machine) behavioral manifold theory into the Research Stack's Lean core, replacing all `Float` with `Q16_16`, eliminating all `sorry`, and collapsing every algorithm to the `bind` primitive.

**Constraint**: Zero new dependencies. No `Float` in hot paths. Every `def` has an `#eval` or theorem. `lake build` must pass before any milestone is declared complete.

---

## Milestone 0: Foundation Hardening (Prerequisite)

**Status**: Partially complete — Q16_16 exists but lacks operations needed for cascade.

### Deliverable 0.1: `Q16_16` Extended Operations
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Q16_16.lean` (modify existing)
**Lines added**: ~40

**Required additions**:
```lean
def min (a b : Q16_16) : Q16_16 := if a.val < b.val then a else b
def max (a b : Q16_16) : Q16_16 := if a.val > b.val then a else b
def clamp (x lo hi : Q16_16) : Q16_16 := max lo (min x hi)
def sqrt (x : Q16_16) : Q16_16  -- CORDIC or table lookup, documented
def fromUInt8 (n : UInt8) : Q16_16 := ⟨n.toUInt32 * 0x00000100⟩  -- Q16.16 = n / 256
def toUInt8 (x : Q16_16) : UInt8 := (x.val >>> 8).toUInt8
def half : Q16_16 := ⟨0x00008000⟩  -- 0.5
def quarter : Q16_16 := ⟨0x00004000⟩  -- 0.25
```

**Verification**:
```lean
#eval (one + one : Q16_16).val == 0x00020000  -- 2.0
#eval (half + half : Q16_16).val == 0x00010000  -- 1.0
#eval clamp (ofNat 3) (ofNat 1) (ofNat 2) == ofNat 2  -- clamped to 2
```

**Build check**: `cd 0-Core-Formalism/lean/Semantics && lake build`

---

## Milestone 1: Representation Cascade (Geometry Domain)

**Depends on**: Milestone 0
**Bind class**: `geometric_bind`
**Rationale**: The cascade is pure geometry — no physics, no probability. It reduces to `bind` over `Tile d × Tile (d+1) × Metric`.

### Deliverable 1.1: `Semantics.Geometry.Cascade`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Geometry/Cascade.lean` (new)
**Lines**: ~180
**Namespace**: `Semantics.Geometry.Cascade`

**Core definitions**:
```lean
/-- A Tile is a finite polytope with typed facets.
    d = dimension, k = number of facet types (always Fin 16 in hardware) -/
structure Tile (d : Nat) where
  facetTypes : Fin (d + 1) → Fin 16
  deriving Repr, DecidableEq

/-- Cost of representing a d-dimensional tile: (d+1) facets × 16 types -/
def tileCost (d : Nat) : Nat := (d + 1) * 16

/-- Uplift: d-tile becomes a facet of a (d+1)-tile.
    The new tile's first (d+1) facets are the old tile's facets.
    The final facet is derived via XOR composition. -/
def uplift {d : Nat} (t : Tile d) : Tile (d + 1) :=
  { facetTypes := fun i =>
      if h : i.val < d + 1 then
        t.facetTypes (Fin.castLE (by omega) ⟨i.val, h⟩)
      else
        -- Derived facet: XOR of all existing facets
        Finset.univ.fold (fun a b => a ^^^ b) 0
          (fun j => t.facetTypes j) }

/-- The cascade path: Tile2D → Cube3D → 4D → 5D → 6D (peak) → ... → Triangle2D -/
inductive CascadeStage
  | tile2D   -- 4 facets
  | cube3D   -- 6 facets
  | simplex4D  -- 5 facets
  | simplex5D  -- 6 facets (PEAK COST)
  | simplex6D  -- 7 facets
  | triangle2D -- 3 facets (base case)
  deriving Repr, DecidableEq

/-- Cost at each stage in Q16.16 units (arbitrary scale) -/
def stageCost : CascadeStage → Q16_16
  | .tile2D     => ⟨0x00040000⟩  -- 4.0
  | .cube3D     => ⟨0x00060000⟩  -- 6.0
  | .simplex4D  => ⟨0x00050000⟩  -- 5.0
  | .simplex5D  => ⟨0x00060000⟩  -- 6.0 (peak)
  | .simplex6D  => ⟨0x00070000⟩  -- 7.0
  | .triangle2D => ⟨0x00030000⟩  -- 3.0 (minimum)
```

**Theorems** (no `sorry`):
```lean
/-- Theorem: Uplift preserves facet count relationship.
    A d-tile has d+1 facets; uplifted (d+1)-tile has d+2 facets. -/
theorem upliftFacetCount {d : Nat} (t : Tile d) :
  ∀ i : Fin (d + 1), (uplift t).facetTypes (Fin.castLE (by omega) i) = t.facetTypes i

/-- Theorem: Simplex is cheaper than cube for d ≥ 3.
    Facets: simplex has d+1, cube has 2d. For d≥3: d+1 < 2d. -/
theorem simplexCheaperThanCube (d : Nat) (hd : d ≥ 3) :
  (d + 1) * 16 < (2 * d) * 16 := by omega

/-- Theorem: Triangle has minimum cost among all stages.
    3 facets < 4, 5, 6, 7 facets. -/
theorem triangleIsMinimum : stageCost .triangle2D < stageCost .tile2D := by
  simp [stageCost]; decide
```

**#eval witnesses**:
```lean
#eval stageCost .simplex5D > stageCost .simplex4D  -- true: peak > preceding
#eval stageCost .triangle2D < stageCost .tile2D     -- true: base < start
#eval let t : Tile 2 := ⟨fun i => i.val.toUInt8⟩; (uplift t).facetTypes 0
```

### Deliverable 1.2: `Semantics.Geometry.CascadeDescent`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Geometry/CascadeDescent.lean` (new)
**Lines**: ~120
**Namespace**: `Semantics.Geometry.CascadeDescent`

**Core definitions**:
```lean
/-- A TypedTriangle has 3 edges with types in Fin 16 -/
structure TypedTriangle where
  edge0 : Fin 16
  edge1 : Fin 16
  edge2 : Fin 16
  /-- XOR consistency: edge0 ^^^ edge1 = edge2 -/
  h_consistent : edge0.val ^^^ edge1.val = edge2.val

/-- Compose two triangles into a Tile2D (square).
    They must share an edge (the diagonal). -/
def composeTile (t1 t2 : TypedTriangle)
    (h_share : t1.edge1 = t2.edge0)  -- shared diagonal
    (h_match : t1.edge2 = t2.edge2)  -- matching opposite
    : Tile 2 :=
  { facetTypes := fun i =>
      match i.val with
      | 0 => t1.edge0  -- outer edge
      | 1 => t2.edge1  -- outer edge
      | 2 => t1.edge1  -- shared diagonal
      | 3 => t2.edge2  -- outer edge
      | _ => 0 }

/-- Descent is the inverse of uplift for valid configurations.
    Extract the first 3 facets as a triangle. -/
def descendToTriangle {d : Nat} (t : Tile d) (h : d ≥ 2) : TypedTriangle :=
  { edge0 := t.facetTypes ⟨0, by omega⟩,
    edge1 := t.facetTypes ⟨1, by omega⟩,
    edge2 := t.facetTypes ⟨2, by omega⟩,
    h_consistent := by
      -- Proof: for valid tiles, facets 0,1,2 satisfy XOR
      sorry  -- REJECTED: must prove from tile validity invariant
      -- CORRECT: add `h_valid : t.isValid` to structure, prove from invariant
  }
```

**Verification**:
```lean
#eval let tri : TypedTriangle := ⟨1, 2, 3, by decide⟩; tri.edge0
#eval composeTile ⟨1,2,3,by decide⟩ ⟨2,4,3,by decide⟩ (by decide) (by decide)
```

### Deliverable 1.3: `Semantics.Geometry.CascadeBind`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Geometry/CascadeBind.lean` (new)
**Lines**: ~100
**Namespace**: `Semantics.Geometry.CascadeBind`

**Collapse to `bind` primitive**:
```lean
/-- Cascade as geometric_bind instance.
    Input: Tile d (source), Tile d' (target), Metric = stage cost difference.
    Output: Bind Tile Tile with lawful check, cost, invariant extractor. -/
structure CascadeMetric where
  sourceDim : Nat
  targetDim : Nat
  cost : Q16_16  -- |stageCost source - stageCost target|

/-- The bind instance: uplift or descent between compatible tiles. -/
def cascadeBind (src : Tile d) (tgt : Tile d') (m : CascadeMetric) : Bool :=
  -- Lawful check: dimensions differ by exactly 1 (uplift) or any (descent)
  (d' = d + 1) ∨ (d = d' + 1) ∨ (d = d' ∧ d = 2)  -- 2D tiles compose

/-- Cost function for cascade: Q16.16 in arbitrary units -/
def cascadeCost (src : Tile d) (tgt : Tile d') : UInt32 :=
  -- Cost = number of dimensions traversed × base cost
  let diff := if d > d' then d - d' else d' - d
  (diff * 0x00010000).toUInt32  -- diff × 1.0 in Q16.16

/-- Invariant extractor: what string describes this cascade step? -/
def cascadeInvariant (src : Tile d) (tgt : Tile d') : String :=
  if d' = d + 1 then s!"uplift_{d}_to_{d'}"
  else if d = d' + 1 then s!"descent_{d}_to_{d'}"
  else if d = d' then s!"compose_{d}"
  else "incompatible"
```

**Verification**:
```lean
#eval cascadeBind (Tile.mk (fun _ => 0)) (Tile.mk (fun _ => 0)) ⟨2, 3, one⟩  -- true
#eval cascadeCost (Tile.mk (fun _ => 0) : Tile 2) (Tile.mk (fun _ => 0) : Tile 3)  -- 0x00010000
#eval cascadeInvariant (Tile.mk (fun _ => 0) : Tile 2) (Tile.mk (fun _ => 0) : Tile 3)  -- "uplift_2_to_3"
```

### Milestone 1 Completion Criteria
- [ ] `lake build` passes with zero errors
- [ ] All `def`s have `#eval` witnesses in comments
- [ ] All theorems are proved (zero `sorry`)
- [ ] No `Float` used anywhere
- [ ] Each file exports exactly one namespace matching its stem
- [ ] File count: 3 new `.lean` files

---

## Milestone 2: Behavioral Distance (Geometry Domain)

**Depends on**: Milestone 1
**Bind class**: `geometric_bind`
**Rationale**: Behavioral distance is a weighted metric on `Fin 31 → Q16_16`. It reduces to `bind` over `BehavioralPoint × BehavioralPoint × DomainWeight`.

### Deliverable 2.1: `Semantics.Geometry.Behavioral`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Geometry/Behavioral.lean` (new)
**Lines**: ~200
**Namespace**: `Semantics.Geometry.Behavioral`

**Core definitions**:
```lean
/-- A behavioral point is 31 binding strengths in Q16.16.
    Each component = how strongly a fundamental equation constrains
    the configuration. Range: [0, 255] in Q8.8, stored as Q16.16. -/
def BehavioralPoint : Type := Fin 31 → Q16_16

/-- The 5 domains partition the 31 equations:
    Domain 0 (IDENTITY):      equations 0-5   (6 equations)
    Domain 1 (CONSERVATION):  equations 6-12  (7 equations)
    Domain 2 (TRANSFORMATION): equations 13-18 (6 equations)
    Domain 3 (SCALING):       equations 19-24 (6 equations)
    Domain 4 (DYNAMICS):      equations 25-30 (6 equations) -/
def domainOf (eqIdx : Fin 31) : Fin 5 :=
  if eqIdx.val < 6 then 0
  else if eqIdx.val < 13 then 1
  else if eqIdx.val < 19 then 2
  else if eqIdx.val < 25 then 3
  else 4

/-- Domain transition cost in Q16.16:
    same domain      = 0.0    (0x00000000)
    adjacent (±1)    = 0.25   (0x00004000)
    skip-one (±2)    = 0.5    (0x00008000)
    opposite (±3, ±4) = 1.0   (0x00010000) -/
def domainWeight (d1 d2 : Fin 5) : Q16_16 :=
  if d1 = d2 then zero
  else if (d1.val + 1) % 5 = d2.val then quarter
  else if (d1.val + 2) % 5 = d2.val then half
  else one

/-- Behavioral distance: domain-weighted L1 metric.
    d(A,B) = Σ_i w(domain(i)) · |A_i - B_i| -/
def behavioralDistance (A B : BehavioralPoint) : Q16_16 :=
  Finset.univ.fold (fun acc i => acc + (domainWeight (domainOf i) (domainOf i)) * abs (A i - B i)) zero
  -- NOTE: domainWeight uses same domain for both → simplifies to 0 or based on actual transition
  -- CORRECTED: need weight matrix for domain transitions, not self-weight
```

**Corrected definition**:
```lean
/-- Full domain weight matrix (5×5) in Q16.16 -/
def domainWeightMatrix : Fin 5 → Fin 5 → Q16_16
  | 0, 0 => zero    | 0, 1 => quarter | 0, 2 => half   | 0, 3 => one    | 0, 4 => one
  | 1, 0 => quarter | 1, 1 => zero    | 1, 2 => half   | 1, 3 => half   | 1, 4 => half
  | 2, 0 => half    | 2, 1 => half    | 2, 2 => zero   | 2, 3 => half   | 2, 4 => quarter
  | 3, 0 => one     | 3, 1 => half    | 3, 2 => half   | 3, 3 => zero   | 3, 4 => quarter
  | 4, 0 => one     | 4, 1 => half    | 4, 2 => quarter| 4, 3 => quarter| 4, 4 => zero

/-- Behavioral distance with proper domain transition weights -/
def behavioralDistance (A B : BehavioralPoint) : Q16_16 :=
  Finset.univ.fold (fun acc i =>
    let di := domainOf i
    let w := domainWeightMatrix di di  -- For same-domain comparisons
    acc + w * abs (A i - B i)) zero
```

**Theorems**:
```lean
/-- Theorem: behavioralDistance is symmetric. -/
theorem behavioralDistanceSymmetric (A B : BehavioralPoint) :
  behavioralDistance A B = behavioralDistance B A := by
  simp [behavioralDistance]
  -- Proof: |A_i - B_i| = |B_i - A_i|, sum is commutative
  sorry  -- REJECTED
  -- CORRECT: use Finset.sum_comm + abs_sub_comm

/-- Theorem: behavioralDistance(A,A) = 0. -/
theorem behavioralDistanceSelfZero (A : BehavioralPoint) :
  behavioralDistance A A = zero := by
  simp [behavioralDistance, abs]
  -- Proof: |A_i - A_i| = 0 for all i, sum of zeros = 0
  sorry  -- REJECTED
  -- CORRECT: show each term is zero, then sum is zero
```

**#eval witnesses**:
```lean
#eval let A : BehavioralPoint := fun _ => ⟨0x00010000⟩; behavioralDistance A A == zero  -- true
#eval domainWeightMatrix 0 1 == quarter  -- true: IDENTITY→CONSERVATION = 0.25
#eval domainWeightMatrix 0 4 == one      -- true: IDENTITY→DYNAMICS = 1.0
```

### Deliverable 2.2: `Semantics.Geometry.BehavioralBind`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Geometry/BehavioralBind.lean` (new)
**Lines**: ~80
**Namespace**: `Semantics.Geometry.BehavioralBind`

```lean
/-- Geodesic condition: C is on or near the geodesic [A,B] if
    |d(A,C) + d(C,B) - d(A,B)| < threshold. -/
def onGeodesic (A B C : BehavioralPoint) (threshold : Q16_16) : Bool :=
  let dAC := behavioralDistance A C
  let dCB := behavioralDistance C B
  let dAB := behavioralDistance A B
  abs (dAC + dCB - dAB) ≤ threshold

/-- Resolution: an adapter point between A and B.
    A resolution exists if there is a point C on the geodesic with
    high binding strength. -/
structure Resolution (A B : BehavioralPoint) where
  point : BehavioralPoint
  geodesicError : Q16_16  -- |d(A,C)+d(C,B) - d(A,B)|
  binding : Q16_16        -- Σ_i point(i)
  h_geodesic : onGeodesic A B point ⟨0x00010000⟩  -- threshold = 1.0
  h_binding : binding > ⟨0x00008000⟩  -- binding > 0.5

/-- Behavioral bind instance. -/
def behavioralBind (A B : BehavioralPoint) : Bool :=
  -- Lawful: A and B are "compatible" if their distance < some bound
  behavioralDistance A B < ⟨0x000A0000⟩  -- distance < 10.0

/-- Cost = behavioral distance itself. -/
def behavioralCost (A B : BehavioralPoint) : UInt32 :=
  (behavioralDistance A B).val

/-- Invariant extractor. -/
def behavioralInvariant (A B : BehavioralPoint) : String :=
  let d := behavioralDistance A B
  s!"behavioral_dist_{d.val}"
```

**Verification**:
```lean
#eval let A : BehavioralPoint := fun _ => zero; let B : BehavioralPoint := fun _ => one;
  behavioralBind A B  -- true: distance = 31 × 1.0 = 31.0... wait, 31 > 10
  -- CORRECT: test with closer points
#eval let A : BehavioralPoint := fun _ => ⟨0x00010000⟩;
      let B : BehavioralPoint := fun i => if i.val < 5 then ⟨0x00018000⟩ else ⟨0x00010000⟩;
      behavioralBind A B  -- compute actual distance
```

### Milestone 2 Completion Criteria
- [ ] `lake build` passes
- [ ] All theorems proved (zero `sorry`)
- [ ] No `Float`
- [ ] `#eval` witnesses for distance, geodesic check, resolution
- [ ] File count: 2 new `.lean` files

---

## Milestone 3: Foam-Behavioral Bridge (Physics Domain)

**Depends on**: Milestone 2
**Bind class**: `physical_bind`
**Rationale**: The foam computes φ⁴ lattice field theory. The bridge extracts statistical invariants and maps them to behavioral points. This is `physical_bind` over `VacuumState × BehavioralPoint × ExtractionMetric`.

### Deliverable 3.1: `Semantics.Physics.FoamState`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Physics/FoamState.lean` (new)
**Lines**: ~150
**Namespace**: `Semantics.Physics.FoamState`

```lean
/-- A foam vacuum state: 64 sites, each with field value φ_i in Q16.16.
    Hardware: 64 registers × 32 bits = 2048 bits total. -/
structure VacuumState where
  phi : Fin 64 → Q16_16
  gradient : Fin 64 → Q16_16  -- ∂S/∂φ_i
  converged : Fin 64 → Bool    -- |gradient| < threshold

/-- Validity: all sites converged. -/
def isValid (v : VacuumState) : Bool :=
  Finset.univ.all (fun i => v.converged i)

/-- Statistical invariants (computed by hardware accumulator). -/
def sumPhi (v : VacuumState) : Q16_16 :=
  Finset.univ.fold (fun acc i => acc + v.phi i) zero

def sumPhi2 (v : VacuumState) : Q16_16 :=
  Finset.univ.fold (fun acc i => acc + v.phi i * v.phi i) zero

def sumGradMag (v : VacuumState) : Q16_16 :=
  Finset.univ.fold (fun acc i => acc + abs (v.gradient i)) zero

def convergedCount (v : VacuumState) : Nat :=
  Finset.univ.filter (fun i => v.converged i) |>.card

def zeroCrossings (v : VacuumState) : Nat :=
  Finset.univ.filter (fun i : Fin 63 =>
    let a := v.phi (Fin.castLE (by omega) i)
    let b := v.phi (Fin.castLE (by omega) (i + 1))
    (a ≥ zero ∧ b < zero) ∨ (a < zero ∧ b ≥ zero)) |>.card
```

**Theorems**:
```lean
/-- Theorem: A valid vacuum has at least one non-zero binding.
    Proof: convergedCount = 64 → binding[0] = 64 × 4 = 256 > 0. -/
theorem validVacuumHasStructure (v : VacuumState)
    (h_valid : isValid v = true) :
    ∃ i : Fin 31, bindingFunction v i ≠ zero := by
  use ⟨0, by omega⟩
  simp [bindingFunction, convergedCount]
  -- Since all 64 sites converged, count = 64, binding = 64 × 4 = 256 > 0
  sorry  -- Must prove from h_valid: all converged → count = 64
```

### Deliverable 3.2: `Semantics.Physics.FoamBridge`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Physics/FoamBridge.lean` (new)
**Lines**: ~200
**Namespace**: `Semantics.Physics.FoamBridge`

```lean
/-- The 31 binding functions: foam statistic → behavioral binding in Q16.16.
    Each binding is a specific statistic of the vacuum, measuring how
    strongly the vacuum couples to each fundamental equation. -/
def bindingFunction (v : VacuumState) (i : Fin 31) : Q16_16 :=
  match i.val with
  -- DOMAIN 0: IDENTITY (equations 0-5)
  | 0  => ⟨convergedCount v * 4 * 0x00000100⟩  -- Convergence ratio × 4
  | 1  => (sumPhi v) / ⟨64 * 0x00010000⟩ + ⟨128 * 0x00000100⟩  -- Mean phi centered
  | 2  => (sumPhi2 v) / ⟨64 * 0x00010000⟩  -- Variance proxy
  | 3  => if sumPhi v > zero then ⟨192 * 0x00000100⟩ else ⟨64 * 0x00000100⟩  -- Skewness proxy
  | 4  => (sumPhi2 v * sumPhi2 v) / ⟨4096 * 0x00010000⟩  -- Kurtosis proxy
  | 5  => ⟨extremaCount v * 4 * 0x00000100⟩  -- Extrema density

  -- DOMAIN 1: CONSERVATION (equations 6-12)
  | 6  => sumBinding v / ⟨64 * 0x00010000⟩  -- Average binding
  | 7  => ⟨255 * 0x00000100⟩ - sumGradMag v / ⟨64 * 0x00010000⟩  -- Gradient uniformity
  | 8  => ⟨zeroCrossings v * 4 * 0x00000100⟩  -- Sign stability
  | 9  => (sumPhi2 v / ⟨128 * 0x00010000⟩) + (sumGradMag v / ⟨128 * 0x00010000⟩)  -- Energy
  | 10 => correlation v 4  -- Half-lattice symmetry
  | 11 => correlation v 1  -- Periodicity
  | 12 => ⟨invariantCount v * 0x00000100⟩  -- Invariant count

  -- ... (equations 13-30 follow same pattern)
  | _  => zero

/-- Foam → behavioral point mapping. -/
def vacuumToBehavioral (v : VacuumState) : BehavioralPoint :=
  fun i => bindingFunction v i

/-- Physical bind instance: foam state + extraction metric → behavioral point.
    Lawful check: vacuum must be converged.
    Cost: number of cycles to extract (74 cycles in hardware).
    Invariant: string describing the vacuum's statistical profile. -/
def foamBind (v : VacuumState) : Bool := isValid v

def foamCost (v : VacuumState) : UInt32 := 74  -- fixed hardware latency

def foamInvariant (v : VacuumState) : String :=
  s!"foam_valid_{isValid v}_converged_{convergedCount v}"
```

**#eval witnesses**:
```lean
#eval let v : VacuumState := {
  phi := fun _ => ⟨0x00010000⟩,
  gradient := fun _ => zero,
  converged := fun _ => true
}; isValid v  -- true
#eval bindingFunction v ⟨0, by omega⟩  -- convergedCount × 4 = 256 in Q8.8
```

### Milestone 3 Completion Criteria
- [ ] `lake build` passes
- [ ] All theorems proved
- [ ] No `Float`
- [ ] `#eval` witnesses for vacuum validity, binding extraction
- [ ] File count: 2 new `.lean` files

---

## Milestone 4: UberLUT Orchestration (Control Domain)

**Depends on**: Milestone 3
**Bind class**: `control_bind`
**Rationale**: The UberLUT is the memory management policy layer. It orchestrates address expansion, stochastic walks, and discovery accumulation. This is `control_bind` over `UberLUTCycle × UberLUTCycle × DiscoveryMetric`.

### Deliverable 4.1: `Semantics.Orchestrate.UberLUT`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Orchestrate/UberLUT.lean` (new)
**Lines**: ~180
**Namespace**: `Semantics.Orchestrate.UberLUT`

```lean
/-- UberLUT cycle state. Hardware: 6 registers.
    All arithmetic in UInt32 (addresses) and Q16.16 (ratios). -/
structure UberLUTCycle where
  walkerPos : UInt32       -- current position in address space
  seed : UInt32            -- stochastic seed
  population : UInt32      -- number of discovered formulas
  capacity : UInt32        -- current address space capacity
  discoveryCount : UInt32  -- total discoveries
  cycleNum : UInt32        -- iteration counter

/-- Initial capacity: 262,144 = 2^18 (Genome18 address space). -/
def initialCapacity : UInt32 := 262144

/-- Expansion threshold: 75% full triggers doubling.
    In Q16.16: 0.75 = 0x0000C000. -/
def expansionThreshold : Q16_16 := ⟨0x0000C000⟩

/-- Check if expansion should trigger.
    population / capacity > 0.75 ? -/
def shouldExpand (pop cap : UInt32) : Bool :=
  let ratio : Q16_16 := ⟨(pop.toNat * 0x00010000 / cap.toNat).toUInt32⟩
  ratio > expansionThreshold

/-- Seed mixing: avalanche function for stochasticity.
    Hardware: XOR + shift + multiply. -/
def seedMix (a b : UInt32) : UInt32 :=
  let x1 := a ^^^ b
  let x2 := x1 * 2654435761
  let x3 := (a <<< 7) ||| (b >>> 25)
  x2 + x3

/-- Discovery probability: (capacity - population) / capacity × coherence.
    Coherence = discoveryCount / population (or 1.0 if population = 0). -/
def discoveryProbability (pop cap disc : UInt32) : Q16_16 :=
  let remaining := cap - pop
  let ratio : Q16_16 := ⟨(remaining.toNat * 0x00010000 / cap.toNat).toUInt32⟩
  let coherence := if pop > 0
    then ⟨disc.toNat * 0x00010000 / pop.toNat⟩
    else one
  -- Multiplication in Q16.16
  ratio * coherence

/-- Execute one cycle. Returns new state + didDiscover flag. -/
def cycle (c : UberLUTCycle) : UberLUTCycle × Bool :=
  let coherence := if c.population > 0
    then ⟨c.discoveryCount.toNat * 0x00010000 / c.population.toNat⟩
    else one
  let p := discoveryProbability c.population c.capacity c.discoveryCount
  -- Determine discovery: (seed % 100) < (p × 100)
  let pPercent := (p.val.toNat * 100 / 0x00010000).toUInt32
  let discover := (c.seed % 100) < pPercent

  if discover then
    let newPop := c.population + 1
    let newSeed := seedMix c.seed c.population
    let newPos := newSeed % c.capacity
    let (newCap, newPop2) :=
      if shouldExpand newPop c.capacity then
        (c.capacity * 2, newPop)
      else
        (c.capacity, newPop)
    ({ c with walkerPos := newPos, seed := newSeed, population := newPop2,
       capacity := newCap, discoveryCount := c.discoveryCount + 1,
       cycleNum := c.cycleNum + 1 }, true)
  else
    let newSeed := seedMix c.seed c.walkerPos
    ({ c with walkerPos := newSeed % c.capacity, seed := newSeed,
       cycleNum := c.cycleNum + 1 }, false)
```

**Theorems**:
```lean
/-- Theorem: After expansion, density < 75%.
    pop / (2×cap) < 0.75 when pop/cap > 0.75. -/
theorem expansionResetsDensity (pop cap : UInt32)
    (h : shouldExpand pop cap = true) :
    let newCap := cap * 2
    -- pop / newCap < 0.75
    ⟨pop.toNat * 0x00010000 / newCap.toNat⟩ < expansionThreshold := by
  sorry  -- Arithmetic: if pop/cap > 0.75 then pop/(2cap) < 0.75 (since pop < cap)
  -- CORRECT: pop/cap > 0.75 and pop ≤ cap → pop/(2cap) ≤ 0.5 < 0.75
```

**#eval witnesses**:
```lean
#eval shouldExpand 200000 262144  -- false: 200K/262K ≈ 0.76... wait, 200/262 = 0.76 > 0.75 → true
#eval shouldExpand 100000 262144  -- false: 100K/262K ≈ 0.38 < 0.75
#eval seedMix 12345 67890  -- deterministic output
#eval let c : UberLUTCycle := {
  walkerPos := 0, seed := 2654435761, population := 100000,
  capacity := 262144, discoveryCount := 1000, cycleNum := 0
}; (cycle c).2  -- true or false depending on seed
```

### Deliverable 4.2: `Semantics.Orchestrate.UberLUTBind`
**File**: `0-Core-Formalism/lean/Semantics/Semantics/Orchestrate/UberLUTBind.lean` (new)
**Lines**: ~80
**Namespace**: `Semantics.Orchestrate.UberLUTBind`

```lean
/-- Control bind instance for UberLUT orchestration.
    Lawful: cycle state is valid (population ≤ capacity).
    Cost: 1 cycle per iteration.
    Invariant: describe current phase (discovery rate, fullness). -/
def uberlutBind (before after : UberLUTCycle) : Bool :=
  before.population ≤ before.capacity ∧ after.population ≤ after.capacity

def uberlutCost (before after : UberLUTCycle) : UInt32 :=
  -- Cost = 1 + (1 if expansion occurred else 0)
  if after.capacity > before.capacity then 2 else 1

def uberlutInvariant (c : UberLUTCycle) : String :=
  let fullness := c.population.toNat * 100 / c.capacity.toNat
  s!"uberlut_pop_{c.population}_cap_{c.capacity}_full_{fullness}pct"
```

### Milestone 4 Completion Criteria
- [ ] `lake build` passes
- [ ] All theorems proved
- [ ] No `Float`
- [ ] `#eval` witnesses for expansion, cycle execution
- [ ] File count: 2 new `.lean` files

---

## Hardware Status: FPGA Disconnected

**Constraint**: Tang Nano 9K is currently disconnected. All hardware verification must be **virtual** (simulation-only).

**Implications**:
- Verilog modules will be validated via `iverilog` + `vvp` simulation, not FPGA programming
- `openFPGALoader` tests are deferred until reconnection
- Yosys synthesis reports will verify LUT/resource estimates without bitstream generation
- UART gimbal integration tests are blocked; Rust gimbal remains compiled but untested on hardware

**Virtual test pipeline**:
```bash
# For each Verilog module:
iverilog -o module_tb.vvp module.v module_tb.v
vvp module_tb.vvp
# Pass: $display outputs match expected values from Lean #eval
```

---

## Milestone 5: Integration & Aggregate Build

**Depends on**: Milestones 1-4
**Goal**: All new modules importable from `Semantics.lean` aggregate. Verilog validated in simulation only.

### Deliverable 5.1: Update `Semantics.lean`
**File**: `0-Core-Formalism/lean/Semantics/Semantics.lean` (modify)
**Action**: Add imports for all new modules.

```lean
-- Geometry (Cascade + Behavioral Manifold)
import Semantics.Geometry.Cascade
import Semantics.Geometry.CascadeDescent
import Semantics.Geometry.CascadeBind
import Semantics.Geometry.Behavioral
import Semantics.Geometry.BehavioralBind

-- Physics (Foam Bridge)
import Semantics.Physics.FoamState
import Semantics.Physics.FoamBridge

-- Orchestrate (UberLUT)
import Semantics.Orchestrate.UberLUT
import Semantics.Orchestrate.UberLUTBind
```

### Deliverable 5.2: Tang Nano 9K Verilog Extraction (SIMULATION-ONLY)
**Files**: 
- `hardware/tangnano9k/rtl/generated/CascadeUplift.v`
- `hardware/tangnano9k/rtl/generated/BehavioralDistance.v`
- `hardware/tangnano9k/rtl/generated/FoamBridge.v`
- `hardware/tangnano9k/rtl/generated/UberLUTController.v`

**Method**: Manual extraction from Lean `#eval` verified definitions. Each Verilog module:
- Has a 1:1 correspondence with a Lean `def`
- Includes a `module_tb.v` with `$display` assertions matching `#eval` expected outputs
- Yosys synthesis checks LUT estimate against 6,272 budget (existing ~2,500 used)
- **NO BITSTREAM GENERATION** until FPGA reconnected

### Deliverable 5.3: Lean Aggregate Build Verification
```bash
cd 0-Core-Formalism/lean/Semantics && lake build
# Must pass with zero errors, zero warnings, zero sorry
```

### Deliverable 5.4: Virtual Verilog Test Suite
```bash
cd hardware/tangnano9k/rtl/generated
for mod in CascadeUplift BehavioralDistance FoamBridge UberLUTController; do
  iverilog -o ${mod}_tb.vvp ${mod}.v ${mod}_tb.v
  vvp ${mod}_tb.vvp
done
# All $display outputs must match Lean #eval witnesses
```

### Milestone 5 Completion Criteria
- [ ] `lake build` passes on full aggregate
- [ ] All new modules imported by `Semantics.lean`
- [ ] Verilog modules pass `iverilog` simulation tests
- [ ] Yosys LUT estimates within Tang Nano 9K budget
- [ ] No `sorry` in any committed file
- [ ] No `Float` in any hot-path code
- [ ] All `def`s have `#eval` witnesses

---

## File Inventory (New Files Only)

| Milestone | File | Lines | Namespace |
|-----------|------|-------|-----------|
| 0 | `Semantics/Q16_16.lean` (modify) | +40 | `Semantics.Q16_16` |
| 1 | `Semantics/Geometry/Cascade.lean` | ~180 | `Semantics.Geometry.Cascade` |
| 1 | `Semantics/Geometry/CascadeDescent.lean` | ~120 | `Semantics.Geometry.CascadeDescent` |
| 1 | `Semantics/Geometry/CascadeBind.lean` | ~100 | `Semantics.Geometry.CascadeBind` |
| 2 | `Semantics/Geometry/Behavioral.lean` | ~200 | `Semantics.Geometry.Behavioral` |
| 2 | `Semantics/Geometry/BehavioralBind.lean` | ~80 | `Semantics.Geometry.BehavioralBind` |
| 3 | `Semantics/Physics/FoamState.lean` | ~150 | `Semantics.Physics.FoamState` |
| 3 | `Semantics/Physics/FoamBridge.lean` | ~200 | `Semantics.Physics.FoamBridge` |
| 4 | `Semantics/Orchestrate/UberLUT.lean` | ~180 | `Semantics.Orchestrate.UberLUT` |
| 4 | `Semantics/Orchestrate/UberLUTBind.lean` | ~80 | `Semantics.Orchestrate.UberLUTBind` |
| 5 | `Semantics.lean` (modify) | +12 imports | — |
| 5 | `hardware/.../CascadeUplift.v` | ~200 | — |
| 5 | `hardware/.../BehavioralDistance.v` | ~150 | — |
| 5 | `hardware/.../FoamBridge.v` | ~250 | — |
| 5 | `hardware/.../UberLUTController.v` | ~180 | — |

**Total new Lean**: ~1,660 lines
**Total new Verilog**: ~780 lines
**Total modified**: 2 files

---

## Execution Order & Dependencies

```
Milestone 0 (Q16_16 extend)
    ↓
Milestone 1 (Cascade geometry) ─┐
    ↓                           │
Milestone 2 (Behavioral dist) ──┤
    ↓                           │
Milestone 3 (Foam bridge) ──────┤
    ↓                           │
Milestone 4 (UberLUT control) ──┘
    ↓
Milestone 5 (Integration + build)
```

**No parallel execution**: Each milestone depends on the previous. `lake build` must pass at each milestone before proceeding.

---

## Success Criteria

1. **Build**: `lake build` passes with zero errors
2. **Proofs**: Zero `sorry` in committed code
3. **Type safety**: No `Float` in hardware-targeted modules
4. **Witnesses**: Every computing `def` has an `#eval` with expected output
5. **Bind compliance**: Every domain module exposes `bind`, `cost`, `invariantExtractor`
6. **Hardware**: Verilog extractions synthesize for Tang Nano 9K within LUT budget
7. **Documentation**: This plan + pipeline doc are up to date

---

## Risk Flags

| Risk | Mitigation |
|------|------------|
| `Finset.univ.fold` may not reduce in `#eval` | Use `List.foldl` with explicit `Fin` lists instead |
| `UInt32` arithmetic overflows in Q16.16 | Use `UInt64` for intermediate products, truncate at end |
| Mathlib dependency on `Float` for `abs` | Define `q16_16_abs` directly on `UInt32` bitwise |
| Verilog synthesis too large for Tang Nano 9K | Start with reduced precision (Q8.8) or fewer sites (32 instead of 64) |
| `lake build` timeout on large `Finset` proofs | Use `decide` for concrete bounds, avoid general `Finset` induction |

---

*Plan created: 2026-04-25*
*Status: AWAITING APPROVAL*
