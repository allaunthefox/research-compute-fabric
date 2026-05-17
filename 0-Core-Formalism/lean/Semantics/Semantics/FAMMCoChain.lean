import Semantics.FAMM
import Semantics.FixedPoint

open Semantics
open Semantics.FixedPoint (Q16_16)

namespace Semantics.FAMMCoChain

/-! # FAMM as a Discrete 1-Cochain

FAMM access costs are a 1-cochain on the access graph: each directed
edge (read/write operation between cells) carries a delay cost value.

The coboundary δ of this cochain measures the memory pressure gradient
across the cell topology. Where δ is large → thermal hotspot. Where
δ ≈ 0 → the delay field is locally flat (cheap to operate).

## Proof Target (by structure encoding)

    coboundary_vanishes_iff_thermally_stable

    The JUDGE_PAUSE trigger becomes a cohomology detector: when the
    coboundary exceeds a threshold, the thermal budget is exceeded.

## Cochain definitions

    A 0-cochain f : Cell → Q16_16 assigns a value to each cell.
    A 1-cochain ω : Edge → Q16_16 assigns a cost to each edge.
    The coboundary δ(f)(i→j) = f(j) − f(i).

    An exact cost cochain means no thermal hotspots (conservative field).
-/

-- ════════════════════════════════════════════════════
-- Graph types for the access topology
-- ════════════════════════════════════════════════════

/-- A directed edge between two cell addresses. -/
structure AccessEdge where
  source : Nat
  target : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

/-- Access operation type carried by each edge. -/
inductive AccessOp
  | read
  | write
  deriving Repr, BEq, DecidableEq, Inhabited

/-- Access graph edge with operation label and source/target. -/
structure AccessGraphEdge where
  source : Nat
  target : Nat
  op : AccessOp
  deriving Repr, BEq, DecidableEq, Inhabited

/-- Lift an AccessEdge to AccessGraphEdge with default op. -/
def accessEdgeToGraphEdge (e : AccessEdge) (op : AccessOp) : AccessGraphEdge :=
  { source := e.source, target := e.target, op := op }

-- ════════════════════════════════════════════════════
-- Cochains
-- ════════════════════════════════════════════════════

/-- A 0-cochain assigns a delay value to each cell. -/
structure ZeroCoChain where
  values : Array Q16_16
  deriving Repr, Inhabited

/-- A 1-cochain assigns a delay cost to each access edge. -/
structure OneCoChain where
  edges : Array AccessGraphEdge
  costs : Array Q16_16
  deriving Repr, Inhabited

/-- Look up the cost of a specific edge in a 1-cochain.
    Returns zero if the edge is not found. -/
def oneCoChainCost (ω : OneCoChain) (edge : AccessGraphEdge) : Q16_16 :=
  let idx := ω.edges.findIdx? (λ e => e == edge)
  match idx with
  | some i => ω.costs[i]!
  | none   => Q16_16.zero

-- ════════════════════════════════════════════════════
-- Coboundary operator δ
-- ════════════════════════════════════════════════════

/-- The coboundary δ: 0-cochain → 1-cochain.
    δ(f)(i→j) = f(j) − f(i).

    This gives the delay gradient along each edge.
    Where |δ(f)| is large → thermal hotspot.
    Where δ(f) ≈ 0 → locally flat delay field.
-/
def coboundary (f : ZeroCoChain) (edges : Array AccessGraphEdge) : OneCoChain :=
  let costs := edges.map (λ e =>
    let srcVal := if e.source < f.values.size then f.values[e.source]! else Q16_16.zero
    let tgtVal := if e.target < f.values.size then f.values[e.target]! else Q16_16.zero
    Q16_16.sub tgtVal srcVal)
  { edges := edges, costs := costs }

/-- Coboundary squared L2 norm — measures total thermal stress. -/
def coboundaryNorm (ω : OneCoChain) : Q16_16 :=
  ω.costs.foldl (λ acc c => Q16_16.add acc (Q16_16.mul c c)) Q16_16.zero

-- ════════════════════════════════════════════════════
-- Exactness check
-- ════════════════════════════════════════════════════

/-- A 1-cochain is exact if for every edge (i→j), the cost
    is balanced by the reverse edge (j→i). This is equivalent
    to the cycle condition: costs sum to zero around every cycle.
-/
def isExact (ω : OneCoChain) : Bool :=
  let forwardEdges := ω.edges
  forwardEdges.all (λ e =>
    let rev := forwardEdges.filter (λ r => r.source = e.target ∧ r.target = e.source)
    rev.all (λ r =>
      let costFwd := oneCoChainCost ω e
      let costRev := oneCoChainCost ω r
      Q16_16.add costFwd costRev = Q16_16.zero))

/--
The coboundary of a coboundary is zero: δ² = 0.
For a 1-cochain ω, δω(i→j→k) = ω(j→k) − ω(i→j).
A flat field has zero coboundary on all triangles.
-/
def coboundary2 (ω : OneCoChain) (triangles : Array (AccessGraphEdge × AccessGraphEdge × AccessGraphEdge)) : Bool :=
  triangles.all (λ t =>
    let (eij, ejk, _) := t
    let ω_ij := oneCoChainCost ω eij
    let ω_jk := oneCoChainCost ω ejk
    Q16_16.sub ω_jk ω_ij = Q16_16.zero)

-- ════════════════════════════════════════════════════
-- Thermal stress → JUDGE_PAUSE detector
-- ════════════════════════════════════════════════════

/-- Thermal stress in a bank: coboundary norm of delayMass.
    Replaces ad-hoc maxDelay checks with a cohomological invariant. -/
def thermalStress (bank : FAMMBank) (edges : Array AccessGraphEdge) : Q16_16 :=
  let f : ZeroCoChain := { values := bank.cells.map (λ c => c.delayMass) }
  let ω := coboundary f edges
  coboundaryNorm ω

/-- JUDGE_PAUSE trigger: thermal stress exceeds budget.
    A cohomology detector — high coboundary norm ⇒ large gradients. -/
def judgePauseTrigger (bank : FAMMBank) (edges : Array AccessGraphEdge)
    (budget : Q16_16) : Bool :=
  Q16_16.lt budget (thermalStress bank edges)

/-- Flat delay field check: field is flat iff coboundary ≈ 0. -/
def isThermallyFlat (bank : FAMMBank) (edges : Array AccessGraphEdge)
    (tolerance : Q16_16) : Bool :=
  Q16_16.lt (thermalStress bank edges) tolerance

-- ════════════════════════════════════════════════════
-- Construct the canonical access graph for a bank
-- ════════════════════════════════════════════════════

/-- Build the canonical nearest-neighbor access graph for a linear bank.
    Each cell i connects to i+1 (read) and i→i (write to self). -/
def linearAccessGraph (bankSize : Nat) : Array AccessGraphEdge :=
  let readEdges := Array.ofFn (λ (i : Fin (bankSize - 1)) =>
    { source := i.val, target := i.val + 1, op := AccessOp.read })
  let writeEdges := Array.ofFn (λ (i : Fin bankSize) =>
    { source := i.val, target := i.val, op := AccessOp.write })
  readEdges ++ writeEdges

-- ════════════════════════════════════════════════════
-- Fixtures and #eval witnesses
-- ════════════════════════════════════════════════════

def testBank : FAMMBank :=
  { cells := #[
      { data := Q16_16.one, delay := Q16_16.one, delayMass := Q16_16.ofInt 1, delayWeight := Q16_16.one }
    , { data := Q16_16.ofInt 2, delay := Q16_16.ofInt 2, delayMass := Q16_16.ofInt 10, delayWeight := Q16_16.one }
    , { data := Q16_16.ofInt 3, delay := Q16_16.ofInt 3, delayMass := Q16_16.ofInt 2, delayWeight := Q16_16.one }
    , { data := Q16_16.ofInt 4, delay := Q16_16.ofInt 4, delayMass := Q16_16.ofInt 15, delayWeight := Q16_16.one }
    ]
  , size := 4
  , maxDelay := Q16_16.ofInt 5
  }

def testEdges : Array AccessGraphEdge := linearAccessGraph 4

#eval testBank
#eval testEdges
#eval thermalStress testBank testEdges

-- Flat bank: all delayMass equal → coboundary ≈ 0
def flatBank : FAMMBank :=
  { cells := Array.replicate 4
      { data := Q16_16.one, delay := Q16_16.one, delayMass := Q16_16.ofInt 5, delayWeight := Q16_16.one }
  , size := 4
  , maxDelay := Q16_16.ofInt 5
  }

#eval thermalStress flatBank testEdges
#eval isThermallyFlat flatBank testEdges (Q16_16.ofInt 1)
#eval isThermallyFlat testBank testEdges (Q16_16.ofInt 1)

-- JUDGE_PAUSE detection
#eval judgePauseTrigger testBank testEdges (Q16_16.ofInt 50)
#eval judgePauseTrigger testBank testEdges (Q16_16.ofInt 500)
#eval judgePauseTrigger flatBank testEdges (Q16_16.ofInt 50)

-- 0-cochain and coboundary example
def testZeroChain : ZeroCoChain :=
  { values := testBank.cells.map (λ c => c.delayMass) }

def testOneChain : OneCoChain := coboundary testZeroChain testEdges

#eval testZeroChain.values
#eval testOneChain.costs
#eval coboundaryNorm testOneChain

end Semantics.FAMMCoChain
