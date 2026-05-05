/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

VisualPrimitive.lean — Coordinate-bearing visual witnesses

This module records the theorem-safe core of the "thinking with visual
primitives" bridge: a visual reference is treated as a bounded spatial
witness, not merely as an annotation or natural-language phrase.

Design boundary:
  - This file formalizes the minimal coordinate witness substrate.
  - It does not claim benchmark performance or model capability.
  - Empirical claims belong in docs/evidence receipts, not this module.

Connection to the stack:
  visual primitive → bounded region → goxel witness → replayable trace atom
-/

import Mathlib.Data.Fin.Basic
import Mathlib.Data.Nat.Basic

namespace Semantics.VisualPrimitive

/-- Minimal kind taxonomy for coordinate-bearing visual thought units. -/
inductive PrimitiveKind where
  | point
  | box
  | contour
  | mask
  | vector
  | spectral
  deriving Repr, BEq, DecidableEq

/-- A bounded integer image/manifold region.

`width > 0 ∧ height > 0` is the theorem-level nonempty-region gate.  A
point-like primitive may be represented as a `1 × 1` region. -/
structure BoundedRegion where
  x      : Nat
  y      : Nat
  width  : Nat
  height : Nat
  deriving Repr, BEq, DecidableEq

namespace BoundedRegion

/-- Nonempty coordinate support: the primitive actually binds somewhere. -/
def Nonempty (r : BoundedRegion) : Prop :=
  r.width > 0 ∧ r.height > 0

/-- A `1 × 1` point region is nonempty. -/
theorem point_nonempty (x y : Nat) :
    Nonempty { x := x, y := y, width := 1, height := 1 } := by
  exact ⟨Nat.succ_pos 0, Nat.succ_pos 0⟩

/-- The area cost of a bounded region, using integer arithmetic only. -/
def areaCost (r : BoundedRegion) : Nat :=
  r.width * r.height

/-- Nonempty regions have positive area. -/
theorem area_positive_of_nonempty (r : BoundedRegion) (h : r.Nonempty) :
    r.areaCost > 0 := by
  unfold areaCost
  exact Nat.mul_pos h.1 h.2

end BoundedRegion

/-- Coordinate-bearing visual primitive.

`confidenceQ16` is intentionally an integer field.  Interpret values through the
project Q16.16 convention at system boundaries; theorem-critical code should not
use floating-point coordinates or confidences. -/
structure VisualPrimitive where
  kind          : PrimitiveKind
  region        : BoundedRegion
  confidenceQ16 : Nat
  deriving Repr, BEq, DecidableEq

namespace VisualPrimitive

/-- A visual primitive binds when its region is nonempty. -/
def Binds (p : VisualPrimitive) : Prop :=
  p.region.Nonempty

/-- Bound primitives have positive spatial cost. -/
theorem area_positive_of_binds (p : VisualPrimitive) (h : p.Binds) :
    p.region.areaCost > 0 := by
  exact BoundedRegion.area_positive_of_nonempty p.region h

/-- Canonical point primitive witness. -/
def point (x y confidenceQ16 : Nat) : VisualPrimitive :=
  { kind := PrimitiveKind.point,
    region := { x := x, y := y, width := 1, height := 1 },
    confidenceQ16 := confidenceQ16 }

/-- Canonical point primitives bind to a nonempty region. -/
theorem point_binds (x y confidenceQ16 : Nat) :
    (point x y confidenceQ16).Binds := by
  exact BoundedRegion.point_nonempty x y

end VisualPrimitive

/-- A Goxel witness binds a semantic claim to a bounded visual/manifold region.

This is the repo-facing bridge from external visual-primitives work into the
Research Stack vocabulary:
  - primitive: coordinate witness payload
  - semanticTag: language-side binding label
  - timestep: reasoning/replay index
  - register: finite 4-bit state register compatible with TSM-style traces
-/
structure GoxelWitness where
  primitive   : VisualPrimitive
  semanticTag : String
  timestep    : Nat
  register    : Fin 16
  deriving Repr, BEq, DecidableEq

namespace GoxelWitness

/-- A Goxel witness is grounded when its primitive has nonempty coordinate support. -/
def Grounded (w : GoxelWitness) : Prop :=
  w.primitive.Binds

/-- Constructing a witness from a point primitive always gives a grounded witness. -/
theorem point_grounded (x y confidenceQ16 timestep : Nat) (tag : String) (register : Fin 16) :
    Grounded
      { primitive := VisualPrimitive.point x y confidenceQ16,
        semanticTag := tag,
        timestep := timestep,
        register := register } := by
  exact VisualPrimitive.point_binds x y confidenceQ16

/-- Grounded witnesses have a positive spatial receipt cost. -/
theorem area_positive_of_grounded (w : GoxelWitness) (h : w.Grounded) :
    w.primitive.region.areaCost > 0 := by
  exact VisualPrimitive.area_positive_of_binds w.primitive h

end GoxelWitness

end Semantics.VisualPrimitive
