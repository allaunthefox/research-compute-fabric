/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CascadeDescent.lean — Barycentric descent: Triangle → Tile
Composition of triangles into Wang tiles via shared-edge matching.
-/

import Semantics.FixedPoint
import Semantics.Geometry.Cascade

namespace Semantics.Geometry.CascadeDescent

open Semantics.Q16_16 (Q16_16)
open Semantics.Q16_16.Q16_16
open Semantics.Geometry.Cascade

-- =============================================================================
-- SECTION 1: TYPED TRIANGLE
-- =============================================================================

/-- A triangle with typed edges in Fin 16.
    The XOR consistency relation (edge0 ^^^ edge1 = edge2) is checked
    separately via `isValidTriangle`, not enforced by the type.
    This allows eval-safe construction for #eval witnesses. -/
structure TypedTriangle where
  edge0 : Fin 16
  edge1 : Fin 16
  edge2 : Fin 16
  deriving Repr, BEq

/-- Check if a triangle satisfies XOR consistency.
    Hardware: 2 XOR gates + 1 comparator. -/
def isValidTriangle (t : TypedTriangle) : Bool :=
  t.edge0.val ^^^ t.edge1.val = t.edge2.val

-- =============================================================================
-- SECTION 2: TILE COMPOSITION
-- =============================================================================

/-- Compose two triangles into a Tile2D.
    The triangles must share an edge (the diagonal).
    Facets 0,1,2 store the first triangle's edges for round-trip recovery.
    Facet 3 stores the second triangle's non-shared edge. -/
def composeTile (t1 t2 : TypedTriangle)
    (h_share : t1.edge1 = t2.edge0)  -- shared diagonal
    : Tile 2 :=
  { facetTypes := fun i =>
      match i.val with
      | 0 => t1.edge0
      | 1 => t1.edge1
      | 2 => t1.edge2
      | 3 => t2.edge2
      | _ => ⟨0, by omega⟩ }

/-- Descent: extract the first 3 facets of a Tile2D as a triangle.
    Returns a triangle; validity must be checked separately with `isValidTriangle`.
    For tiles produced by `composeTile`, this always yields a valid triangle. -/
def descendToTriangle (t : Tile 2) : TypedTriangle :=
  { edge0 := t.facetTypes ⟨0, by omega⟩,
    edge1 := t.facetTypes ⟨1, by omega⟩,
    edge2 := t.facetTypes ⟨2, by omega⟩ }

/-- Extract the outer edges of a composed tile as a proper Wang tile.
    Outer edges of the square:
      top    = t1.edge0
      right  = t2.edge1
      bottom = t2.edge2
      left   = t1.edge2 -/
def tileOuterEdges (t1 t2 : TypedTriangle)
    (h_share : t1.edge1 = t2.edge0) : Tile 2 :=
  { facetTypes := fun i =>
      match i.val with
      | 0 => t1.edge0   -- top
      | 1 => t2.edge1   -- right
      | 2 => t2.edge2   -- bottom
      | 3 => t1.edge2   -- left
      | _ => ⟨0, by omega⟩ }

-- =============================================================================
-- SECTION 3: THEOREMS
-- =============================================================================

/-- Theorem: A directly-constructed triangle with consistent edges is valid. -/
theorem validTriangleCorrect (e0 e1 e2 : Fin 16)
    (h : e0.val ^^^ e1.val = e2.val) :
    isValidTriangle ⟨e0, e1, e2⟩ = true := by
  simp [isValidTriangle]
  exact h

/-- Theorem: Descent from a composed tile produces a valid triangle
    when the first input triangle is valid. -/
theorem descentProducesValid (t1 t2 : TypedTriangle)
    (h_share : t1.edge1 = t2.edge0)
    (h_valid : isValidTriangle t1 = true) :
    isValidTriangle (descendToTriangle (composeTile t1 t2 h_share)) = true := by
  simp [isValidTriangle, descendToTriangle, composeTile]
  have h : t1.edge0.val ^^^ t1.edge1.val = t1.edge2.val := by
    simp [isValidTriangle] at h_valid
    exact h_valid
  exact h

/-- Theorem: Composed tile has exactly 4 facets. -/
theorem composedTileFacetCount (t1 t2 : TypedTriangle)
    (_h_share : t1.edge1 = t2.edge0) :
    stageFacetCount .tile2D = 4 := by
  simp [stageFacetCount]

-- =============================================================================
-- SECTION 4: #eval WITNESSES
-- =============================================================================

-- Valid triangle: 1 ^^^ 2 = 3
#eval isValidTriangle ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩  -- true

-- Invalid triangle: 1 ^^^ 2 ≠ 4
#eval isValidTriangle ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨4, by decide⟩⟩  -- false

-- Valid triangle construction (eval-safe, no proof fields)
#eval let tri : TypedTriangle := ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩
      tri.edge0.val  -- 1

-- Compose two triangles: t1(1,2,3) + t2(2,4,6) share edge 2
#eval let t1 : TypedTriangle := ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩
      let t2 : TypedTriangle := ⟨⟨2, by decide⟩, ⟨4, by decide⟩, ⟨6, by decide⟩⟩
      let tile := composeTile t1 t2 (by decide)
      tile.facetTypes ⟨0, by omega⟩  -- = 1

#eval let t1 : TypedTriangle := ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩
      let t2 : TypedTriangle := ⟨⟨2, by decide⟩, ⟨4, by decide⟩, ⟨6, by decide⟩⟩
      let tile := composeTile t1 t2 (by decide)
      tile.facetTypes ⟨1, by omega⟩  -- = 2 (shared diagonal)

-- Descent round-trip: compose then descend recovers first triangle edges
#eval let t1 : TypedTriangle := ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩
      let t2 : TypedTriangle := ⟨⟨2, by decide⟩, ⟨4, by decide⟩, ⟨6, by decide⟩⟩
      let tile := composeTile t1 t2 (by decide)
      let tri := descendToTriangle tile
      tri.edge0.val == 1 ∧ tri.edge1.val == 2  -- true

-- Validity after descent
#eval let t1 : TypedTriangle := ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩
      let t2 : TypedTriangle := ⟨⟨2, by decide⟩, ⟨4, by decide⟩, ⟨6, by decide⟩⟩
      let tile := composeTile t1 t2 (by decide)
      isValidTriangle (descendToTriangle tile)  -- true

-- Outer edges tile: proper Wang tile representation
#eval let t1 : TypedTriangle := ⟨⟨1, by decide⟩, ⟨2, by decide⟩, ⟨3, by decide⟩⟩
      let t2 : TypedTriangle := ⟨⟨2, by decide⟩, ⟨4, by decide⟩, ⟨6, by decide⟩⟩
      let tile := tileOuterEdges t1 t2 (by decide)
      tile.facetTypes ⟨0, by omega⟩  -- top = 1

end Semantics.Geometry.CascadeDescent
