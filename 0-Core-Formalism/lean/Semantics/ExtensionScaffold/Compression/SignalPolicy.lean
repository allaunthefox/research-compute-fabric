import ExtensionScaffold.Compression.CellCore

set_option linter.dupNamespace false

namespace ExtensionScaffold.Compression.SignalPolicy

open Semantics
open Semantics.Q16_16
open ExtensionScaffold.Compression.CellCore
open ExtensionScaffold.Compression.PriorityGossip

inductive SignalBand where
  | quiet
  | active
  | stressed
  | extreme
  deriving Repr, BEq, DecidableEq

def SignalBand.weight : SignalBand -> Q16_16
  | .quiet    => Q16_16.ofInt 0
  | .active   => Q16_16.ofInt 1
  | .stressed => Q16_16.ofInt 2
  | .extreme  => Q16_16.ofInt 3

structure SignalSample where
  value : Q16_16
  deriving Repr

def classifySignal (s : SignalSample) : SignalBand :=
  let v := s.value
  if Q16_16.lt v (Q16_16.ofFloat 0.25) then .quiet
  else if Q16_16.lt v (Q16_16.ofFloat 0.50) then .active
  else if Q16_16.lt v (Q16_16.ofFloat 0.75) then .stressed
  else .extreme

structure SignalPolicy where
  exploreBias   : Q16_16
  tunnelBias    : Q16_16
  promoteBias   : Q16_16
  gossipBias    : Q16_16
  deriving Repr, Inhabited

def policyOfBand : SignalBand -> SignalPolicy
  | .quiet    => { exploreBias := Q16_16.zero, tunnelBias := Q16_16.zero, promoteBias := Q16_16.one, gossipBias := Q16_16.zero }
  | .active   => { exploreBias := Q16_16.ofFloat 0.5, tunnelBias := Q16_16.ofFloat 0.5, promoteBias := Q16_16.ofFloat 0.5, gossipBias := Q16_16.ofFloat 0.5 }
  | .stressed => { exploreBias := Q16_16.one, tunnelBias := Q16_16.one, promoteBias := Q16_16.neg (Q16_16.ofFloat 0.5), gossipBias := Q16_16.one }
  | .extreme  => { exploreBias := Q16_16.ofFloat 1.5, tunnelBias := Q16_16.ofFloat 1.5, promoteBias := Q16_16.neg Q16_16.one, gossipBias := Q16_16.ofFloat 0.5 }

def branchBudgetWithSignal
  (base : GossipBudget)
  (s : SignalBand) : GossipBudget :=
  match s with
  | .quiet    => base
  | .active   => { slots := base.slots + 1 }
  | .stressed => { slots := base.slots + 2 }
  | .extreme  => { slots := base.slots + 1 }

def priorityScoreWithSignal
  (p : GossipPayload)
  (s : SignalBand) : Q16_16 :=
  let ps := priorityScore p
  let pol := policyOfBand s
  let weightTerm := Q16_16.mul (Q16_16.div (Q16_16.ofInt p.saddleScore) (Q16_16.ofInt 32)) (s.weight)
  Q16_16.add (Q16_16.add ps pol.gossipBias) weightTerm

def classifyPriorityWithSignal
  (p : GossipPayload)
  (s : SignalBand) : PriorityBand :=
  let x := priorityScoreWithSignal p s
  if Q16_16.gt x (Q16_16.ofInt 8) then .critical
  else if Q16_16.gt x (Q16_16.ofInt 4) then .high
  else if Q16_16.gt x (Q16_16.ofInt 1) then .normal
  else .low

def tunnelThresholdWithSignal
  (base : Q16_16)
  (s : SignalBand) : Q16_16 :=
  let b := policyOfBand s
  Q16_16.max Q16_16.zero (Q16_16.sub base b.tunnelBias)

def promotionThresholdWithSignal
  (base : Q16_16)
  (s : SignalBand) : Q16_16 :=
  let b := policyOfBand s
  Q16_16.max Q16_16.zero (Q16_16.sub base b.promoteBias)

def shouldPropagateSignal
  (budget : GossipBudget)
  (neighborCostBand : UInt8)
  (p : GossipPayload)
  (s : SignalBand) : Bool :=
  let band := classifyPriorityWithSignal p s
  match band with
  | .critical => true
  | .high     => neighborCostBand <= 2 || budget.slots > 0
  | .normal   => neighborCostBand <= 1 && budget.slots > 0
  | .low      => neighborCostBand == 0 && budget.slots > 1

def schedulePayloadsWithSignal
  (budget : GossipBudget)
  (neighborCost : GossipPayload -> UInt8)
  (signal : SignalSample)
  (ps : Array GossipPayload) : Array GossipPayload :=
  let sb := classifySignal signal
  let b' := branchBudgetWithSignal budget sb
  let filtered := ps.filter (fun p => shouldPropagateSignal b' (neighborCost p) p sb)
  let ranked := filtered.qsort (fun a b => Q16_16.gt (priorityScoreWithSignal a sb) (priorityScoreWithSignal b sb))
  ranked.extract 0 (min ranked.size b'.slots)

structure RoutedPatch where
  sig   : LocalSignature
  patch : CellPatch
  score : Q16_16
  deriving Repr

def chooseRouteWithSignal
  (sig : LocalSignature)
  (signal : SignalSample)
  (routes : Array RoutedPatch) : Option RoutedPatch :=
  let sb := classifySignal signal
  let xs := routes.filter (fun r => r.sig == sig)
  let ys := xs.qsort (fun a b => Q16_16.gt (Q16_16.add a.score sb.weight) (Q16_16.add b.score sb.weight))
  if h : 0 < ys.size then some (ys[0]) else none

end ExtensionScaffold.Compression.SignalPolicy
