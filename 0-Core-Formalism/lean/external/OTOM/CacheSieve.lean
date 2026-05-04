/-
  CacheSieve.lean - L0 Local Sorter Cache Verification
  Migrates legacy f64 penalty evaluations and raw limits.
-/
import Semantics.Bind
import Semantics.SLUQ

namespace Semantics.CacheSieve

open SLUQ (SLUQState)

inductive CouplingBucket
| None
| Low
| Medium
| High
deriving Repr, DecidableEq, Inhabited

def edgeBand (bucket : CouplingBucket) : UInt16 :=
  match bucket with
  | .None   => 0x0200
  | .Low    => 0x0400
  | .Medium => 0x0800
  | .High   => 0x1000

def isEdgeBand (value threshold band : UInt16) : Bool :=
  let diff := if value > threshold then value - threshold else threshold - value
  diff <= band

structure SieveNode where
  acc : UInt16
  state : SLUQState
  previousState : SLUQState
  bucket : CouplingBucket
deriving Repr, DecidableEq, Inhabited

def stateToUInt8 (s : SLUQState) : UInt8 :=
  match s with
  | .Stable => 0
  | .Rising => 1
  | .Unstable => 2
  | .Reset => 3

def advanceNode (node : SieveNode) (val : UInt8) (phi : UInt8) : SieveNode :=
  let product := val.toUInt16 * phi.toUInt16
  let newAcc := node.acc + product
  let band := edgeBand node.bucket
  
  let edge0 := isEdgeBand newAcc 0x4000 band
  let edge1 := isEdgeBand newAcc 0x8000 band
  let edge2 := isEdgeBand newAcc 0xC000 band
  
  let inEdgeBand := edge0 || edge1 || edge2
  
  let newState := if inEdgeBand then node.previousState else
    if newAcc.toNat < 0x4000 then SLUQState.Stable
    else if newAcc.toNat < 0x8000 then SLUQState.Rising
    else if newAcc.toNat < 0xC000 then SLUQState.Unstable
    else SLUQState.Reset

  { node with acc := newAcc, state := newState, previousState := node.state }

/-- Compute raw survivor base ratio bounded as a fixed Q16.16 mapped index -/
def triageSurvivorValue (maxState : UInt8) : UInt32 :=
  -- Base Score (1.0 - max_state/3.0) represented in Q16.16 mathematically (1.0 == 65536)
  if maxState == 0 then 65536
  else if maxState == 1 then 43690 -- 2/3
  else if maxState == 2 then 21845 -- 1/3
  else 0

/-- Informational invariant binding the mathematical evaluation. -/
def sieveCost (nodesA _nodesB : Array SieveNode) (_metric : Metric) : UInt32 :=
  if nodesA.size > 0 then
    let maxSt := Array.foldl (fun (acc : UInt8) (n : SieveNode) => 
      if stateToUInt8 n.state > acc then stateToUInt8 n.state else acc
    ) 0 nodesA
    triageSurvivorValue maxSt
  else 0

def sieveInvariant (nodes : Array SieveNode) : String := s!"sieve[{nodes.size}]"

def sieveBind (nodesA _nodesB : Array SieveNode) (metric : Metric) : Bind (Array SieveNode) (Array SieveNode) :=
  controlBind nodesA _nodesB metric sieveCost sieveInvariant sieveInvariant

-- Evaluate structural completion.
#eval triageSurvivorValue 1

end Semantics.CacheSieve
