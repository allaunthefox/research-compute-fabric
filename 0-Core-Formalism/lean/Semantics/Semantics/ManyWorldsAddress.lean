/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ManyWorldsAddress.lean — Observer-Relative Addressing via Many-Worlds Spawning

Core insight: Remove the speed limit → no global simultaneity → every observer
frame is its own world. A person is a world, a group is a world, a village is a
world, a town is a world, a nation is a world, a species is a world.

The many-worlds equation gives the tractable kernel of Any-Planck-to-NaN
addressing: each world spawns n² sub-worlds under pressure, producing a
self-similar address tree with no privileged root.

Address form:
  A = ⟨ worldId, localCoord, depth, parentWorld, validity ⟩

Where:
- worldId      : observer-local chart identifier
- localCoord   : coordinate within that chart's frame
- depth        : nesting depth in the spawn tree
- parentWorld  : optional parent chart (none = root observer)
- validity     : Valid | ShoreWarning | Singular | NaN

Spawn law (the many-worlds equation):
  W_{d+1} = spawn(W_d, n)  where |spawn| = n²
  Total worlds at depth d  = (n²)^d
  Total addressable to depth D = Σ_{k=0}^{D} (n²)^k

Per AGENTS.md §1.4: Q16_16 fixed-point for hot paths.
Per AGENTS.md §1.5: Finite enumerable types for all decisions.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has eval witness or theorem.
-/ 

import Semantics.GeometricTopology
import Semantics.FixedPoint
import Mathlib.Tactic

namespace Semantics.ManyWorlds

open Semantics
open Semantics.GeometricTopology

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Validity: same four-state terminal algebra as APN addressing
-- ═══════════════════════════════════════════════════════════════════════════

/-- Validity state of an address. Finite, enumerable, no string parsing. -/
inductive Validity where
  | Valid        -- address denotes a computable point
  | ShoreWarning -- metric approaching degeneracy
  | Singular     -- metric degenerate but still tracked
  | NaN          -- explicit domain exit, not silent overflow
  deriving Repr, DecidableEq, BEq

/-- Validity is ordered: Valid < ShoreWarning < Singular < NaN.
    Used for monotonic shore-transition logic. -/
def validityLeq (a b : Validity) : Bool :=
  match a, b with
  | .Valid, _        => true
  | .ShoreWarning, .Valid => false
  | .ShoreWarning, _ => true
  | .Singular, .NaN  => true
  | .Singular, _     => false
  | .NaN, .NaN       => true
  | .NaN, _          => false

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  WorldFrame: each observer is their own center
-- ═══════════════════════════════════════════════════════════════════════════

/-- A WorldFrame is a CoordinateChart with observer identity.
    Each frame is its own origin; there is no global coordinate system.
    The overlap predicate between frames defines admissible transitions. -/
structure WorldFrame where
  chart   : CoordinateChart
  parent  : Option String  -- none = this frame is a root observer
  depth   : Nat            -- nesting depth in spawn tree
  deriving Repr, Inhabited

/-- A root world frame: observer with no parent, depth 0. -/
def rootFrame (chart : CoordinateChart) : WorldFrame :=
  { chart, parent := none, depth := 0 }

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  ManyWorldsAddress: observer-relative coordinate
-- ═══════════════════════════════════════════════════════════════════════════

/-- Full many-worlds address. Every coordinate is local to a specific
    observer frame. There is no global address space. -/
structure ManyWorldsAddress where
  worldId    : String       -- references WorldFrame.chart.pointId
  localCoord : List Q16_16  -- coordinate within observer's chart
  depth      : Nat          -- spawn-tree depth
  validity   : Validity     -- computability state
  deriving Repr

instance : Inhabited ManyWorldsAddress where
  default := { worldId := "", localCoord := [], depth := 0, validity := .Valid }

/-- Rest-mode address: scalar-only, no spawned shell structure. -/
def restAddress (scalar : Q16_16) : ManyWorldsAddress :=
  { worldId := "rest", localCoord := [scalar], depth := 0, validity := .Valid }

/-- Spawned-mode address: full manifold coordinate under pressure. -/
def spawnedAddress
    (worldId : String)
    (coords  : List Q16_16)
    (depth   : Nat)
    : ManyWorldsAddress :=
  { worldId, localCoord := coords, depth, validity := .Valid }

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Spawn Logic: the n(2) branching equation
--     Each world spawns n² sub-worlds when pressure is applied.
-- ═══════════════════════════════════════════════════════════════════════════

/-- Branching factor: n(2) means n × n children per spawn. -/
def spawnBranchingFactor (n : Nat) : Nat := n * n

/-- Number of worlds at depth d given branching factor b = n².
    W(d) = b^d. -/
def worldCountAtDepth (branching : Nat) (d : Nat) : Nat :=
  branching ^ d

/-- Total addressable worlds from depth 0 through maxDepth inclusive.
    Geometric series: (b^(D+1) − 1) / (b − 1) for b > 1. -/
def totalAddressableWorlds (branching : Nat) (maxDepth : Nat) : Nat :=
  if h : branching ≤ 1 then
    maxDepth + 1
  else
    have _hb : branching ≥ 2 := by omega
    (branching ^ (maxDepth + 1) - 1) / (branching - 1)

/-- Coordinate sub-division: parent coordinate space is split into
    n² equal child regions. Child i receives sub-interval [i/n², (i+1)/n²).
    Implemented via Q16.16 fixed-point arithmetic. -/
def childLocalCoord
    (parentCoord : List Q16_16)
    (childIndex  : Nat)
    (branching   : Nat)
    : List Q16_16 :=
  if branching = 0 then parentCoord
  else
    let scale := Q16_16.div Q16_16.one (Q16_16.ofNat branching)
    let offset := Q16_16.mul scale (Q16_16.ofNat childIndex)
    parentCoord.map (fun c =>
      let scaled := Q16_16.mul c scale
      Q16_16.add scaled offset)

/-- Spawn n² child WorldFrames from a parent frame.
    Each child inherits the parent's dimension but receives a
    sub-divided coordinate patch. -/
def spawnWorlds (parent : WorldFrame) (n : Nat) : List WorldFrame :=
  let b := spawnBranchingFactor n
  List.range b |>.map (fun i =>
    let childId := parent.chart.pointId ++ "_" ++ toString i
    let childChart := {
      pointId     := childId
      centerCoords := childLocalCoord parent.chart.centerCoords i b
      dimension   := parent.chart.dimension
    }
    { chart := childChart
      parent  := some parent.chart.pointId
      depth   := parent.depth + 1
    })

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Shore Transition: metric degeneracy → validity decay
--     Connects to GeometricTopology.infiniteShoreEquation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Advance validity one step toward NaN. Monotonic: never recovers. -/
def validityStep (v : Validity) : Validity :=
  match v with
  | .Valid        => .ShoreWarning
  | .ShoreWarning => .Singular
  | .Singular     => .NaN
  | .NaN          => .NaN

/-- Shore transition triggered by metric determinant.
    If metricDet = 0 (infiniteShoreEquation satisfied), advance validity.
    NaN is explicit — never silently reached. -/
def shoreTransition (addr : ManyWorldsAddress) (metricDet : Q16_16) : ManyWorldsAddress :=
  if metricDet = Q16_16.zero then
    { addr with validity := validityStep addr.validity }
  else
    addr

/-- Predicate: address is still computable (not Singular or NaN). -/
def isComputable (addr : ManyWorldsAddress) : Bool :=
  match addr.validity with
  | .Valid | .ShoreWarning => true
  | .Singular | .NaN       => false

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- The spawn operation produces exactly n² children. -/
theorem spawnProducesN2Children (parent : WorldFrame) (n : Nat) :
    (spawnWorlds parent n).length = n * n := by
  simp [spawnWorlds, spawnBranchingFactor, List.length_range]

/-- At depth 0 there is exactly 1 world regardless of branching. -/
theorem worldCountDepthZero (branching : Nat) :
    worldCountAtDepth branching 0 = 1 := by
  simp [worldCountAtDepth]

/-- Branching factor is strictly positive for n > 0. -/
theorem branchingFactorPos (n : Nat) (hn : n > 0) :
    spawnBranchingFactor n > 0 := by
  simp [spawnBranchingFactor]
  have h : n ≠ 0 := by omega
  exact h

/-- shoreTransition with non-zero metricDet preserves validity. -/
theorem shoreTransitionPreservesIfNonDegenerate
    (addr : ManyWorldsAddress)
    (metricDet : Q16_16)
    (h : metricDet ≠ Q16_16.zero) :
    shoreTransition addr metricDet = addr := by
  simp [shoreTransition, h]

/-- shoreTransition with zero metricDet always advances validity. -/
theorem shoreTransitionAdvancesAtShore
    (addr : ManyWorldsAddress)
    (metricDet : Q16_16)
    (h : metricDet = Q16_16.zero) :
    (shoreTransition addr metricDet).validity = validityStep addr.validity := by
  simp [shoreTransition, h]

/-- NaN is terminal: once reached, further shore transitions stay NaN. -/
theorem nanIsTerminal (addr : ManyWorldsAddress)
    (h : addr.validity = .NaN) :
    ∀ metricDet, (shoreTransition addr metricDet).validity = .NaN := by
  intro metricDet
  simp [shoreTransition]
  split
  · simp [h, validityStep]
  · simp [h]

/-- Rest address has depth 0. -/
theorem restAddressDepthZero (scalar : Q16_16) :
    (restAddress scalar).depth = 0 := by
  rfl

/-- Spawned address depth is exactly the supplied value. -/
theorem spawnedAddressDepth (worldId : String) (coords : List Q16_16) (d : Nat) :
    (spawnedAddress worldId coords d).depth = d := by
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Eval Witnesses
-- ═══════════════════════════════════════════════════════════════════════════

#eval spawnBranchingFactor 2  -- 4  (quad spawn)
#eval spawnBranchingFactor 3  -- 9  (non spawn)
#eval spawnBranchingFactor 4  -- 16 (hex spawn)

#eval worldCountAtDepth 4 0   -- 1
#eval worldCountAtDepth 4 1   -- 4
#eval worldCountAtDepth 4 3   -- 64

#eval totalAddressableWorlds 4 3  -- 85  (1 + 4 + 16 + 64)

#eval (restAddress Q16_16.zero).validity            -- Valid
#eval (shoreTransition (restAddress Q16_16.zero) Q16_16.zero).validity  -- ShoreWarning

#eval isComputable (restAddress Q16_16.one)         -- true
#eval isComputable { worldId := "test", localCoord := [], depth := 0, validity := .NaN }  -- false

end Semantics.ManyWorlds
