/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

Behavioral.lean — Behavioral distance on the 31-dimensional equation manifold.
Domain-weighted L1 metric for measuring distance between behavioral points.
-/

import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.FinRange
import Semantics.FixedPoint

namespace Semantics.Geometry.Behavioral

open Semantics.Q16_16 (Q16_16)
open Semantics.Q16_16.Q16_16

-- =============================================================================
-- SECTION 1: DOMAINS AND EQUATIONS
-- =============================================================================

/-- The 5 domains partition the 31 equations:
    Domain 0 (IDENTITY):       equations 0-5   (6 equations)
    Domain 1 (CONSERVATION):   equations 6-12  (7 equations)
    Domain 2 (TRANSFORMATION): equations 13-18 (6 equations)
    Domain 3 (SCALING):        equations 19-24 (6 equations)
    Domain 4 (DYNAMICS):       equations 25-30 (6 equations) -/
def domainOf (eqIdx : Fin 31) : Fin 5 :=
  if eqIdx.val < 6 then 0
  else if eqIdx.val < 13 then 1
  else if eqIdx.val < 19 then 2
  else if eqIdx.val < 25 then 3
  else 4

/-- Domain transition cost matrix in Q16.16.
    Same domain      = 0.0    (0x00000000)
    Adjacent (±1)    = 0.25   (0x00004000)
    Skip-one (±2)    = 0.5    (0x00008000)
    Opposite (>2)    = 1.0    (0x00010000)
    
    Matrix is symmetric: cost(d1,d2) = cost(d2,d1). -/
def domainWeight (d1 d2 : Fin 5) : Q16_16 :=
  if d1 = d2 then zero
  else
    let diff := if d1.val > d2.val then d1.val - d2.val else d2.val - d1.val
    match diff with
    | 1 => quarter
    | 2 => half
    | _ => one

-- =============================================================================
-- SECTION 2: BEHAVIORAL POINT AND DISTANCE
-- =============================================================================

/-- A behavioral point is 31 binding strengths in Q16.16.
    Each component = how strongly a fundamental equation constrains
    the configuration. Range: [0, 255] mapped to Q16.16. -/
def BehavioralPoint : Type := Fin 31 → Q16_16

/-- Behavioral distance: L1 metric over 31 dimensions.
    d(A,B) = Σ_i |A_i - B_i|
    
    Hardware: 31 parallel subtract+abs units, tree reduction.
    Cycle count: O(log 31) ≈ 5 cycles for tree reduction. -/
def behavioralDistanceL1 (A B : BehavioralPoint) : Q16_16 :=
  List.finRange 31 |>.foldl (fun acc (i : Fin 31) => acc + abs (A i - B i)) zero

/-- Midpoint of two behavioral points. -/
def midpoint (A B : BehavioralPoint) : BehavioralPoint :=
  fun i => (A i + B i) / ofNat 2

-- =============================================================================
-- SECTION 3: GEODESIC AND RESOLUTION
-- =============================================================================

/-- Geodesic condition: C is on or near the geodesic [A,B] if
    |d(A,C) + d(C,B) - d(A,B)| < threshold.
    Hardware: 3 distance units + 2 adders + 1 comparator. -/
def onGeodesic (A B C : BehavioralPoint) (threshold : Q16_16) : Bool :=
  let dAC := behavioralDistanceL1 A C
  let dCB := behavioralDistanceL1 C B
  let dAB := behavioralDistanceL1 A B
  abs (dAC + dCB - dAB) ≤ threshold

-- =============================================================================
-- SECTION 4: THEOREMS (Concrete Witnesses)
-- =============================================================================

/-- Theorem: Distance from a constant point to itself is zero.
    Proved by native_decide for concrete value. -/
theorem behavioralDistanceSelfZeroOne :
    behavioralDistanceL1 (fun _ => one) (fun _ => one) = zero := by
  native_decide

/-- Theorem: Distance between constant 0 and constant 2.0 is 62.0.
    Proved by native_decide for concrete values. -/
theorem behavioralDistanceZeroToTwo :
    behavioralDistanceL1 (fun _ => zero) (fun _ => ofNat 2) = ofNat 62 := by
  native_decide

-- =============================================================================
-- SECTION 5: #eval WITNESSES
-- =============================================================================

-- Domain assignment checks
#eval (domainOf ⟨0, by omega⟩).val   -- 0 (IDENTITY)
#eval (domainOf ⟨6, by omega⟩).val   -- 1 (CONSERVATION)
#eval (domainOf ⟨13, by omega⟩).val  -- 2 (TRANSFORMATION)
#eval (domainOf ⟨19, by omega⟩).val  -- 3 (SCALING)
#eval (domainOf ⟨25, by omega⟩).val  -- 4 (DYNAMICS)

-- Domain weight checks
#eval (domainWeight 0 0).val  -- 0 (same)
#eval (domainWeight 0 1).val  -- 0x4000 = 0.25 (adjacent)
#eval (domainWeight 0 2).val  -- 0x8000 = 0.5 (skip-one)
#eval (domainWeight 0 3).val  -- 0x10000 = 1.0 (opposite)

-- Distance between identical constant points = 0
#eval (behavioralDistanceL1 (fun _ => one) (fun _ => one)).val  -- 0

-- Distance between A=1.0 and B=3.0 on all 31 dims = 31 × 2.0 = 62.0
#eval (behavioralDistanceL1 (fun _ => one) (fun _ => ofNat 3)).val  -- 0x3E0000 = 62.0

-- Midpoint of A=0 and B=2.0 = 1.0
#eval let A : BehavioralPoint := fun _ => zero
      let B : BehavioralPoint := fun _ => ofNat 2
      let C := midpoint A B
      (C ⟨0, by omega⟩).val == one.val  -- true

-- Geodesic check: midpoint is on geodesic (threshold = 1.0)
#eval let A : BehavioralPoint := fun _ => zero
      let B : BehavioralPoint := fun _ => ofNat 2
      onGeodesic A B (midpoint A B) one  -- true

-- Cross-domain distance: A in IDENTITY, B in DYNAMICS
#eval let A : BehavioralPoint := fun i => if domainOf i = 0 then one else zero
      let B : BehavioralPoint := fun i => if domainOf i = 4 then one else zero
      (behavioralDistanceL1 A B).val  -- 6 + 6 = 12.0 (6 edges in each domain)

end Semantics.Geometry.Behavioral
