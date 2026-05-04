/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

Cascade.lean — Representation cascade: Tile → Cube → ... → Triangle
Dimensional uplift and cost model for constraint propagation.
-/

import Mathlib.Data.Fin.Basic
import Mathlib.Data.Finset.Basic
import Semantics.FixedPoint

namespace Semantics.Geometry.Cascade

open Semantics.Q16_16 (Q16_16)
open Semantics.Q16_16.Q16_16

-- =============================================================================
-- SECTION 1: THE TILE
-- =============================================================================

/-- A `d`-dimensional tile is a regular polytope with facet types in Fin 16.
    A d-simplex has d+1 facets. A d-cube has 2d facets.
    Hardware: each facet type is 4 bits (16 possible types). -/
structure Tile (d : Nat) where
  facetTypes : Fin (d + 1) → Fin 16

/-- Representation cost in Q16.16: proportional to number of facets.
    For simplex: d+1 facets. For cube: 2d facets.
    Hardware stores 16 types per facet, but cost is facet count only. -/
def simplexCost (d : Nat) : Q16_16 := ⟨((d + 1) * 0x00010000).toUInt32⟩
def cubeCost (d : Nat) : Q16_16 := ⟨((2 * d) * 0x00010000).toUInt32⟩

-- =============================================================================
-- SECTION 2: UPLIFT
-- =============================================================================

/-- XOR all facets of a tile into a single Fin 16 value.
    Pure recursive function (no Finset, eval-safe). -/
def xorAllFacets {d : Nat} (t : Tile d) : Fin 16 :=
  let rec loop (n : Nat) (acc : Fin 16) : Fin 16 :=
    match n with
    | 0 => acc
    | n + 1 =>
      if h : n < d + 1 then
        loop n (acc ^^^ t.facetTypes ⟨n, h⟩)
      else
        acc
  loop (d + 1) ⟨0, by omega⟩

/-- Uplift a d-tile to a (d+1)-tile.
    The first d+1 facets are preserved from the original tile.
    The new (d+2)th facet is derived by XOR of all existing facets.
    Hardware: routing network that maps old facets to new positions. -/
def uplift {d : Nat} (t : Tile d) : Tile (d + 1) :=
  { facetTypes := fun i =>
      if h : i.val < d + 1 then
        -- Preserve existing facet
        t.facetTypes ⟨i.val, h⟩
      else
        -- Derived facet: XOR composition of all existing facets
        xorAllFacets t }

/-- Cost of the uplift operation: constant 1.0 per dimension step.
    Hardware: routing network cost is independent of specific tile. -/
def upliftCost : Q16_16 := one

-- =============================================================================
-- SECTION 3: CASCADE STAGES
-- =============================================================================

/-- Named cascade stages with their dimension and facet count.
    Cost peaks at 6D (highest dimension) and minimum at Triangle2D. -/
inductive CascadeStage
  | tile2D     -- 2D Wang tile: 4 facets
  | cube3D     -- 3D cube: 6 facets
  | simplex4D  -- 4-simplex: 5 facets
  | simplex5D  -- 5-simplex: 6 facets
  | simplex6D  -- 6-simplex: 7 facets (PEAK COST)
  | triangle2D -- 2-simplex: 3 facets (MINIMUM)
  deriving Repr, DecidableEq

/-- Dimension of each cascade stage. -/
def stageDim : CascadeStage → Nat
  | .tile2D     => 2
  | .cube3D     => 3
  | .simplex4D  => 4
  | .simplex5D  => 5
  | .simplex6D  => 6
  | .triangle2D => 2

/-- Facet count of each stage. -/
def stageFacetCount : CascadeStage → Nat
  | .tile2D     => 4
  | .cube3D     => 6
  | .simplex4D  => 5
  | .simplex5D  => 6
  | .simplex6D  => 7
  | .triangle2D => 3

/-- Cost of each stage in Q16.16 (facet count × 1.0). -/
def stageCost : CascadeStage → Q16_16
  | .tile2D     => ⟨0x00040000⟩  -- 4.0
  | .cube3D     => ⟨0x00060000⟩  -- 6.0
  | .simplex4D  => ⟨0x00050000⟩  -- 5.0
  | .simplex5D  => ⟨0x00060000⟩  -- 6.0
  | .simplex6D  => ⟨0x00070000⟩  -- 7.0 (peak)
  | .triangle2D => ⟨0x00030000⟩  -- 3.0 (minimum)

/-- The canonical cascade path from Tile2D through peak to Triangle2D. -/
def cascadePath : List CascadeStage :=
  [.tile2D, .cube3D, .simplex4D, .simplex5D, .simplex6D, .triangle2D]

/-- Total cost of traversing the full cascade path.
    Explicit sum (eval-safe, no foldl). -/
def cascadeTotalCost : Q16_16 :=
  stageCost .tile2D + stageCost .cube3D + stageCost .simplex4D +
  stageCost .simplex5D + stageCost .simplex6D + stageCost .triangle2D

-- =============================================================================
-- SECTION 4: THEOREMS
-- =============================================================================

/-- Theorem: For d ≥ 3, simplex has fewer facets than cube.
    Simplex: d+1 facets. Cube: 2d facets.
    d+1 < 2d  ↔  1 < d  ↔  d ≥ 2. For d ≥ 3, definitely true. -/
theorem simplexCheaperThanCube (d : Nat) (hd : d ≥ 3) :
    (d + 1) < (2 * d) := by
  omega

/-- Theorem: Triangle has strictly fewer facets than Tile2D.
    3 < 4. -/
theorem triangleFewerFacetsThanTile :
    stageFacetCount .triangle2D < stageFacetCount .tile2D := by
  simp [stageFacetCount]

/-- Theorem: Triangle cost is strictly less than Tile2D cost.
    3.0 < 4.0 in Q16.16. -/
theorem triangleCheaperThanTile :
    stageCost .triangle2D < stageCost .tile2D := by
  simp [stageCost]
  -- 0x00030000 < 0x00040000
  decide

/-- Theorem: Peak cost (simplex6D) is greater than all preceding stages.
    We prove it's greater than simplex5D (6.0 < 7.0). -/
theorem peakGreaterThanPreceding :
    stageCost .simplex5D < stageCost .simplex6D := by
  simp [stageCost]
  decide

/-- Theorem: The cascade path includes exactly 6 stages. -/
theorem cascadePathLength :
    cascadePath.length = 6 := by
  simp [cascadePath]

/-- Theorem: Total cost equals sum of individual stage costs.
    True by definition since cascadeTotalCost IS the explicit sum. -/
theorem cascadeTotalCostEqualsSum :
    cascadeTotalCost = stageCost .tile2D + stageCost .cube3D +
                       stageCost .simplex4D + stageCost .simplex5D +
                       stageCost .simplex6D + stageCost .triangle2D := by
  rfl

-- =============================================================================
-- SECTION 5: #eval WITNESSES
-- =============================================================================

#eval stageDim .simplex6D  -- 6
#eval stageFacetCount .cube3D  -- 6
#eval (stageCost .simplex6D).val  -- 0x00070000 = 7.0
#eval (stageCost .triangle2D).val  -- 0x00030000 = 3.0
#eval (stageCost .simplex6D).val > (stageCost .simplex5D).val  -- true
#eval (stageCost .triangle2D).val < (stageCost .tile2D).val  -- true
#eval cascadePath.length  -- 6
#eval (stageCost .tile2D + stageCost .cube3D + stageCost .simplex4D +
       stageCost .simplex5D + stageCost .simplex6D + stageCost .triangle2D : Q16_16).val
  -- total = 31.0 = 0x001F0000

-- Uplift test: verify first facet is preserved
#eval let t : Tile 2 := ⟨fun i => ⟨i.val, Nat.lt_trans i.isLt (by decide)⟩⟩;
      (uplift t).facetTypes ⟨0, by decide⟩ == ⟨0, by decide⟩  -- true: preserved

-- Uplift test: verify derived facet (XOR of 0, 1, 2 = 3)
#eval let t : Tile 2 := ⟨fun i => ⟨i.val, Nat.lt_trans i.isLt (by decide)⟩⟩;
      (uplift t).facetTypes ⟨3, by decide⟩ == ⟨3, by decide⟩  -- true

end Semantics.Geometry.Cascade
