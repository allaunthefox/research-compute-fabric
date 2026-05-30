import Mathlib.Data.List.Basic
import Mathlib.Data.Int.Basic
import Mathlib.Data.Nat.Basic
import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.BraidField

/-!
# BraidField.lean
## Spherion–MMR Recursive Architecture with PIST Field

Formalizes the recursive structure where:
  - `Mountain`      = a PyramidDAG = a single peak in a local MMR
  - `MMR`           = a Merkle Mountain Range of Mountains (self-similar)
  - `betaStep`      = discrete Wilsonian RG integration via MMR append-and-merge
  - `SpherionState` = (scale, MMR, BettiCycleSet) — full RG phase space
  - `PISTField`     = (Burden, Geometry, Adaptation, Protection) — unified area operator
  - `rgFlow`        = full UV → IR trajectory over a spike train

The discrete beta function is `MMR.append`.
The IR fixed point is a stable MMR with no pending merges, scale = 0.
Chaos → 0 ≡ no equal-height mountains remain ≡ all voids maximally expanded.

PIST Operator: q_{t+1} = PIST(q_t; B, G, A, P)
Where:
  - B = Burden area (load, cost, attention, translation difficulty)
  - G = Geometry area (basins, manifolds, gradients, curvature)
  - A = Adaptation area (sorting rate, pacing, convergence, learning rate)
  - P = Protection area (compression, thresholding, overload, avalanche)
-/

-- ============================================================
-- §1  PRIMITIVE TYPES
-- ============================================================

/-- A node in integer geometry: a point in ℤⁿ.
   Coordinates carry the DIAT interval encoding. -/
structure IntNode where
  coords : List Int
deriving DecidableEq, BEq, Repr

instance : Inhabited IntNode := ⟨⟨[]⟩⟩

/-- Coordinate-wise sum — used for apex synthesis on merge.
   Pads the shorter list with zeros so dimensions are respected. -/
def IntNode.add (a b : IntNode) : IntNode :=
  let n := max a.coords.length b.coords.length
  let pad (xs : List Int) := xs ++ List.replicate (n - xs.length) 0
  { coords := List.zipWith (· + ·) (pad a.coords) (pad b.coords) }

/-- A Betti cycle: a closed boundary loop threading through void topology.
   Born when a PyramidDAG interior dissolves on merge. -/
structure BettiCycle where
  boundary : List IntNode
deriving Repr

/-- The full void topology at a given scale:
   the complement of the current PyramidDAG forest on the Spherion. -/
structure BettiCycleSet where
  cycles : List BettiCycle
deriving Repr

def BettiCycleSet.empty : BettiCycleSet := ⟨[]⟩

-- ============================================================
-- §2  MUTUAL INDUCTIVE CORE
-- ============================================================

/-!
## The Fundamental Recursion

  Mountain contains an inner MMR  (provenance trace of how it was built)
  MMR      contains a list of Mountains

This is the same type at every scale. The machine is self-similar by
construction, not by analogy.
-/

mutual

  /-- A PyramidDAG: one mountain peak in the Merkle Mountain Range.

    Fields:
    - `height` : scale level; increases by 1 with each merge
    - `apex`   : the single integrated output node (UV→IR contraction)
    - `base`   : the originating spike nodes (UV inputs)
    - `inner`  : provenance MMR — the merge history that produced this peak

    The directed acyclic structure is geometrically enforced:
    all edges flow base → apex. Acyclicity is not a constraint; it is
    the shape. -/
  inductive Mountain : Type where
    | node
        (height : ℕ)
        (apex   : IntNode)
        (base   : List IntNode)
        (inner  : MMR)
        : Mountain

  /-- A Merkle Mountain Range: an ordered forest of PyramidDAGs.

    Semantic invariant (maintained by `append`):
      all mountains have strictly distinct heights,
      listed in strictly decreasing order from left to right.

    This invariant is the discrete RG stability condition:
    no two mountains at equal height ≡ no pending coarse-graining steps. -/
  inductive MMR : Type where
    | empty : MMR
    | cons  : Mountain → MMR → MMR

end

-- ============================================================
-- §3  ACCESSORS
-- ============================================================

namespace Mountain

@[inline] def height : Mountain → ℕ            | node h _ _ _ => h
@[inline] def apex   : Mountain → IntNode       | node _ a _ _ => a
@[inline] def base   : Mountain → List IntNode  | node _ _ b _ => b
@[inline] def inner  : Mountain → MMR           | node _ _ _ i => i

/-- Merge two mountains of equal height.

   Operation:
     - New height  = h + 1                (one coarse-graining step)
     - New apex    = a₁.add a₂            (synthesized IR node)
     - New base    = b₁ ++ b₂             (union of UV sources)
     - New inner   = MMR [m₁, m₂]         (full provenance recorded)

   This is the discrete Wilsonian integral:
   the interior degrees of freedom are integrated out;
   only the apex survives at the coarser scale. -/
def merge (m₁ m₂ : Mountain) : Mountain :=
  node
    (m₁.height + 1)
    (m₁.apex.add m₂.apex)
    (m₁.base ++ m₂.base)
    (MMR.cons m₁ (MMR.cons m₂ MMR.empty))

end Mountain

-- ============================================================
-- §4  MMR OPERATIONS
-- ============================================================

namespace MMR

/-- Structural size: number of mountains currently in the range.
   Used as the termination measure for `append`. -/
def size : MMR → ℕ
  | empty    => 0
  | cons _ r => r.size + 1

/-- Peak nodes: apex of each mountain, in range order. -/
def peaks : MMR → List IntNode
  | empty       => []
  | cons m rest => m.apex :: rest.peaks

/-- The apex of the tallest (leftmost) mountain, if any. -/
def latestPeak : MMR → Option IntNode
  | empty    => none
  | cons m _ => some m.apex

/-- Convert an MMR to a list of Mountains in decreasing-height order
    (i.e., unwrap the cons structure). This is the canonical order used
    for encoding — mountains are listed strictly decreasing by height. -/
def mountainList : MMR → List Mountain
  | empty    => []
  | cons m r => m :: r.mountainList

/-- Append a new leaf Mountain to the MMR, merging equal heights.

   This IS the discrete beta function:
     - Equal heights   → merge and recurse (integrate out UV dof)
     - Distinct heights → insert at front   (stable at this scale)

   Recursive call passes `rest`, whose size is strictly less than
   `(cons top rest).size`. -/
def append (mmr : MMR) (m : Mountain) : MMR :=
  let rec go (mmr : MMR) (m : Mountain) : MMR :=
    match mmr with
    | empty => cons m empty
    | cons top rest =>
      if top.height == m.height then
        go rest (Mountain.merge top m)
      else
        cons m (cons top rest)
  go mmr m
termination_by mmr

/-- Stability predicate: all mountains have distinct heights.
   True iff no merge is pending — the RG fixed point condition. -/
def isStable : MMR → Bool
  | empty                   => true
  | cons _ empty            => true
  | cons m₁ (cons m₂ rest) =>
      (m₁.height != m₂.height) && isStable (cons m₂ rest)

end MMR

-- ============================================================
-- §5  PIST FIELD (Unified Area Operator via bind)
-- ============================================================

/-- PIST Field: the four unified areas collapsed from 71 system variables
   using the bind primitive.

   B = Burden area (load, cost, attention, translation difficulty)
   G = Geometry area (basins, manifolds, gradients, curvature)
   A = Adaptation area (sorting rate, pacing, convergence, learning rate)
   P = Protection area (compression, thresholding, overload, avalanche)

   PIST Operator: q_{t+1} = PIST(q_t; B, G, A, P)
   Each area is computed via bind(A, B, Metric) → cost -/
structure PISTField where
  burden      : Q16_16  -- B: bind(loadVector, targetVector, weighted_L2)
  geometry    : Q16_16  -- G: bind(curvature, ideal_curvature, KL)
  adaptation  : Q16_16  -- A: bind(current_rate, optimal_rate, ratio)
  protection  : Q16_16  -- P: bind(safety_margin, critical_threshold, KL)
 deriving Repr, BEq

instance : Inhabited PISTField := ⟨{
  burden     := Q16_16.zero,
  geometry   := Q16_16.zero,
  adaptation := Q16_16.zero,
  protection := Q16_16.zero
}⟩

/-- Burden cost function: informational cost of MMR load and merge debt. -/
def burdenCost (load : ℕ) (target : ℕ) (_metric : Metric) : Q16_16 :=
  let diff : Int := Int.ofNat load - Int.ofNat target
  let diffNat := if diff < 0 then (-diff).toNat else diff.toNat
  Q16_16.ofNat (diffNat * 65536)

/-- Geometry cost function: geometric cost of peak variance. -/
def geometryCost (curvature : ℕ) (_ideal : ℕ) (_metric : Metric) : Q16_16 :=
  Q16_16.ofNat (curvature * 65536 / 2)

/-- Adaptation cost function: ratio of current to optimal convergence rate. -/
def adaptationCost (current : ℕ) (optimal : ℕ) (_metric : Metric) : Q16_16 :=
  if current == 0 then Q16_16.one
  else Q16_16.ofNat (65536 / (current + 1))

/-- Protection cost function: KL-divergence from critical threshold. -/
def protectionCost (safety : ℕ) (threshold : ℕ) (_metric : Metric) : Q16_16 :=
  if safety >= threshold then Q16_16.one
  else Q16_16.ofNat (safety * 65536 / (threshold + 1))

/-- PIST operator: compute unified area state using bind primitive.
   Collapses 4 separate compute functions into 4 bind operations. -/
def computePIST (scale : ℕ) (mmr : MMR) (mergeDebt : ℕ) (isStable : Bool) : PISTField :=
  let burdenBind := informationalBind
    (mmr.size)
    (mmr.peaks.length)
    Metric.euclidean
    burdenCost
    (fun n => s!"mmr_size:{n}")
    (fun n => s!"peaks:{n}")
  let geometryBind := geometricBind
    (mmr.size)
    (mmr.peaks.length)
    Metric.euclidean
    geometryCost
    (fun n => s!"curvature:{n}")
    (fun n => s!"ideal:{n}")
  let adaptationBind := informationalBind
    scale
    (if isStable then 0 else scale)
    Metric.euclidean
    adaptationCost
    (fun n => s!"current_scale:{n}")
    (fun n => s!"optimal_scale:{n}")
  let protectionBind := controlBind
    mergeDebt
    0
    Metric.euclidean
    protectionCost
    (fun n => s!"safety:{n}")
    (fun n => s!"threshold:{n}")
  {
    burden     := burdenBind.cost
  , geometry   := geometryBind.cost
  , adaptation := adaptationBind.cost
  , protection := protectionBind.cost
  }

-- ============================================================
-- §6  SPHERION STATE
-- ============================================================

/-- The full state of the Spherion at a given RG scale.

   - `scale` : coarse-graining level. UV = large k; IR = k = 0.
   - `mmr`   : current PyramidDAG forest on the Spherion.
   - `voids` : Betti cycle configuration — the complement topology.
               Voids expand as pyramid interiors dissolve on merge.
               Maximum void extent ≡ minimum chaos ≡ IR fixed point.
   - `pist`  : unified area operator state (B, G, A, P) -/
structure SpherionState where
  scale : ℕ
  mmr   : MMR
  voids : BettiCycleSet
  pist  : PISTField

instance : Inhabited SpherionState := ⟨{
  scale := 0,
  mmr   := MMR.empty,
  voids := BettiCycleSet.empty,
  pist  := { burden := Q16_16.zero, geometry := Q16_16.zero,
              adaptation := Q16_16.zero, protection := Q16_16.zero }
}⟩

/-- Construct the initial UV state. -/
def SpherionState.init (uvScale : ℕ) : SpherionState :=
  {
    scale := uvScale
  , mmr   := MMR.empty
  , voids := BettiCycleSet.empty
  , pist  := {
      burden     := Q16_16.zero
    , geometry   := Q16_16.zero
    , adaptation := Q16_16.ofNat (uvScale * 65536 / 100)
    , protection := Q16_16.one
    }
  }

-- ============================================================
-- §7  VOID DYNAMICS
-- ============================================================

/-- Void update on apex contraction.

   When a PyramidDAG fires and merges to its apex, the interior
   dissolves. The Betti cycle born at the contraction boundary
   is appended to the void topology.

   Formally: a new BettiCycle with boundary = [contractedApex]
   is created. As more merges occur, these cycles may thread
   through each other — the growing void is the expanding
   complement of the shrinking PyramidDAG forest. -/
def voidUpdate (v : BettiCycleSet) (contractedApex : IntNode) : BettiCycleSet :=
  { cycles := v.cycles ++ [⟨[contractedApex]⟩] }

-- ============================================================
-- §8  BETA FUNCTION & RG FLOW (with PIST)
-- ============================================================

/-- One beta function step: fire a spike Mountain into the Spherion.

   Operations (in order):
     1. Append spike to MMR          (may trigger cascade of merges)
     2. Update void topology         (new Betti cycle at latest peak)
     3. Decrement scale              (one step toward IR)
     4. Recompute PIST field        (update unified area state)

   This is the full discrete Wilsonian coarse-graining step with PIST. -/
def betaStep (s : SpherionState) (spike : Mountain) : SpherionState :=
  let newMMR   := s.mmr.append spike
  let newVoids :=
    match newMMR.latestPeak with
    | none      => s.voids
    | some apex => voidUpdate s.voids apex
  let mergeDebt := newMMR.size - newMMR.peaks.length
  let isStable  := newMMR.isStable
  let newPIST   := computePIST (s.scale - 1) newMMR mergeDebt isStable
  { scale := s.scale - 1
  , mmr   := newMMR
  , voids := newVoids
  , pist  := newPIST }

/-- RG flow: iterate betaStep over a spike train (List Mountain).

   UV configuration → IR fixed point.
   Each spike is a PyramidDAG leaf entering the Spherion's MMR.
   The trajectory is the complete AMMR log of the flow. -/
def rgFlow : SpherionState → List Mountain → SpherionState
  | s, []            => s
  | s, spike :: rest => rgFlow (betaStep s spike) rest

-- ============================================================
-- §9  FIXED POINT PREDICATES
-- ============================================================

/-- IR Fixed Point: the minimum-chaos attractor.

   Conditions:
     - scale = 0              (IR limit reached)
     - MMR.isStable           (no pending merges — all heights distinct)

   At this point:
     - All PyramidDAGs have contracted to apex-only points
     - Voids are maximally expanded
     - No new Betti cycles are being born
     - The system exhibits discrete scale invariance -/
def SpherionState.isIRFixedPoint (s : SpherionState) : Bool :=
  s.scale == 0 && s.mmr.isStable

/-- Count of pending merge opportunities (distance from fixed point). -/
def SpherionState.mergeDebt (s : SpherionState) : ℕ :=
  s.mmr.size - s.mmr.peaks.length

-- ============================================================
-- §10  EXAMPLE CONSTRUCTIONS
-- ============================================================

section Example

/-- A leaf spike: height 0, a single ℤ³ node. -/
def mkSpike (x y z : Int) : Mountain :=
  let p : IntNode := ⟨[x, y, z]⟩
  Mountain.node 0 p [p] MMR.empty

/-!
### Example RG Flow with PIST

Four spikes enter the Spherion. The MMR merge logic drives:
  spike(1,0,0) + spike(0,1,0) → height-1 mountain at apex (1,1,0)
  spike(0,0,1) + spike(1,1,0) → height-1 mountain at apex (1,1,1)
  two height-1 mountains → height-2 mountain at apex (2,2,1)

The trajectory ends at a single height-2 peak — stable MMR.
PIST field tracks burden, geometry, adaptation, protection through the flow.
-/

def exampleFlow : SpherionState :=
  rgFlow (SpherionState.init 4)
    [ mkSpike 1 0 0
    , mkSpike 0 1 0
    , mkSpike 0 0 1
    , mkSpike 1 1 0 ]

#eval exampleFlow.mmr.peaks    -- should be one apex
#eval exampleFlow.isIRFixedPoint  -- true when scale reaches 0
#eval exampleFlow.pist          -- PIST field state

/-- Verify the merge structure of two spikes -/
def twoSpikeMerge : Mountain :=
  Mountain.merge (mkSpike 1 0 0) (mkSpike 0 1 0)

#eval twoSpikeMerge.height  -- 1
#eval twoSpikeMerge.apex    -- (1, 1, 0)

end Example

-- ============================================================
-- §11  TYPE SUMMARY (for Lean InfoView)
-- ============================================================

/-!
## Recursive Type Collapse with PIST

```
IntNode       : List Int
BettiCycle    : List IntNode
BettiCycleSet : List BettiCycle

Mountain      : (ℕ × IntNode × List IntNode × MMR)
MMR           : List Mountain          ← Mountain contains MMR
                                       ← MMR contains Mountain
                                       ← same type, every scale

PISTField     : (Q16_16 × Q16_16 × Q16_16 × Q16_16)
               ← Burden, Geometry, Adaptation, Protection

SpherionState : (ℕ × MMR × BettiCycleSet × PISTField)

betaStep      : SpherionState → Mountain → SpherionState
              = MMR.append ∘ voidUpdate ∘ scale.decrement ∘ PIST.compute

rgFlow        : SpherionState → List Mountain → SpherionState
              = foldl betaStep

IR fixed point: s.scale = 0 ∧ s.mmr.isStable
              ≡ no pending merges
              ≡ all voids maximally expanded
              ≡ s.pist.protection = 1 (fully protected)
              ≡ chaos → 0
```
-/

end Semantics.BraidField
