import Semantics.FixedPoint

namespace ExtensionScaffold.Compression.CellCore

open Semantics

/-- Signature: 4-bit nibble summary. -/
structure LocalSignature where
  s1 : UInt8
  s2 : UInt8
  s3 : UInt8
  s4 : UInt8
  deriving Repr, BEq, DecidableEq

/-- A patch represents a transformation between cells. -/
structure CellPatch where
  p1 : Int
  p2 : Int
  p3 : Int
  p4 : Int
  deriving Repr, BEq

end ExtensionScaffold.Compression.CellCore

namespace ExtensionScaffold.Compression.PriorityGossip

open Semantics
open ExtensionScaffold.Compression.CellCore

inductive PriorityBand where
  | low
  | normal
  | high
  | critical
  deriving Repr, BEq, DecidableEq

structure GossipBudget where
  slots : Nat
  deriving Repr, BEq

structure GossipPayload where
  id : Nat
  sig : LocalSignature
  patch : CellPatch
  saddleScore : Int
  sigma : Q16_16 -- Trajectory quality invariant (fixed-point)
  deriving Repr, BEq

def priorityScore (p : GossipPayload) : Q16_16 :=
  let base := Q16_16.div (Q16_16.ofInt p.saddleScore) (Q16_16.ofInt 10)
  let bias := Q16_16.div p.sigma (Q16_16.ofInt 100)
  Q16_16.add base bias

end ExtensionScaffold.Compression.PriorityGossip
