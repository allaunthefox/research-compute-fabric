import Semantics.FixedPoint
import Semantics.Bind

namespace Semantics

open Semantics.Q16_16

/-- Finite types for MNN routing decisions - no open string matching -/
inductive RoutingAction where
  | local : RoutingAction
  | atlas : RoutingAction
  | reject : RoutingAction
  deriving Repr, Inhabited, BEq, DecidableEq

instance : ToString RoutingAction where
  toString | .local => "local"
           | .atlas => "atlas"
           | .reject => "reject"

/-- Finite types for operation goals -/
inductive OperationGoal where
  | health : OperationGoal
  | attest : OperationGoal
  | compress : OperationGoal
  | route : OperationGoal
  | recover : OperationGoal
  deriving Repr, Inhabited, BEq, DecidableEq

instance : ToString OperationGoal where
  toString | .health => "health"
           | .attest => "attest"
           | .compress => "compress"
           | .route => "route"
           | .recover => "recover"

/-- Finite types for routing reasons -/
inductive RoutingReason where
  | localTrusted : RoutingReason
  | localVerified : RoutingReason
  | deferToAtlas : RoutingReason
  | recoveryDefer : RoutingReason
  | insufficientMemory : RoutingReason
  | unsatisfiable : RoutingReason
  deriving Repr, Inhabited, BEq, DecidableEq

instance : ToString RoutingReason where
  toString | .localTrusted => "localTrusted"
           | .localVerified => "localVerified"
           | .deferToAtlas => "deferToAtlas"
           | .recoveryDefer => "recoveryDefer"
           | .insufficientMemory => "insufficientMemory"
           | .unsatisfiable => "unsatisfiable"

/-- Scalar input from LUT layer -/
structure ScalarInput where
  domain : UInt8
  scalar : UInt8
  deriving Repr, Inhabited

/-- Node state using Q16_16 fixed-point arithmetic -/
structure NodeState where
  memoryBudget : Q16_16  -- in MB
  memoryUsed   : Q16_16  -- in MB
  cpuLoad      : Q16_16  -- 0.0 to 1.0
  recoveryMode : Bool
  trustScore   : Q16_16  -- 0.0 to 1.0
  uptime       : Q16_16  -- seconds
  deriving Repr, Inhabited

/-- Carrier metrics using Q16_16 fixed-point arithmetic -/
structure CarrierMetrics where
  shell       : String  -- carrier shell name (allowed human I/O)
  latency     : Q16_16  -- milliseconds
  lossRate    : Q16_16  -- 0.0 to 1.0
  bandwidth   : Q16_16  -- kbps
  encrypted   : Bool
  deriving Repr, Inhabited

/-- Cost metrics using Q16_16 fixed-point arithmetic -/
structure Cost where
  energy   : Q16_16
  time     : Q16_16
  bandwidth : Q16_16
  deriving Repr, Inhabited

/-- Routing decision -/
structure RoutingDecision where
  action   : RoutingAction
  gclCodon : UInt8
  cost     : Cost
  reason   : RoutingReason
  deriving Repr, Inhabited

/-- Map scalar domain to operation goal -/
def scalarToGoal (domain : UInt8) : OperationGoal :=
  match domain with
  | 0x01 => OperationGoal.health
  | 0x0A => OperationGoal.health  -- ack treated as health
  | 0x0D => OperationGoal.recover
  | 0x0F => OperationGoal.health  -- refuse treated as health
  | _    => OperationGoal.health  -- default to health for unknown

/-- Map operation goal to GCL codon -/
def goalToCodon (goal : OperationGoal) : UInt8 :=
  match goal with
  | OperationGoal.health   => 0x00
  | OperationGoal.attest   => 0x03
  | OperationGoal.compress => 0x04
  | OperationGoal.route    => 0x06
  | OperationGoal.recover  => 0x0D

/-- Check if node can satisfy goal locally -/
def canSatisfyLocally (goal : OperationGoal) (state : NodeState) (carrier : CarrierMetrics) : Bool :=
  match goal with
  | OperationGoal.health => true
  | OperationGoal.recover => state.recoveryMode  -- only in recovery mode
  | OperationGoal.compress =>
      let required := ⟨0x00000400⟩  -- 1KB in Q16_16 (1024 / 65536)
      let available := state.memoryBudget - state.memoryUsed
      available > required
  | OperationGoal.attest => state.trustScore > ⟨0x00008000⟩  -- 0.5 in Q16_16
  | OperationGoal.route => carrier.lossRate < ⟨0x0000199A⟩  -- 0.1 in Q16_16

/-- Compute routing decision based on goal, state, and carrier -/
def selectPath (goal : OperationGoal) (state : NodeState) (carrier : CarrierMetrics) : RoutingDecision :=
  -- Recovery mode: defer non-health/recover goals to atlas
  if state.recoveryMode ∧ goal ≠ OperationGoal.health ∧ goal ≠ OperationGoal.recover then
    {
      action := RoutingAction.atlas,
      gclCodon := goalToCodon goal,
      cost := { energy := ⟨0x0000A000⟩, time := carrier.latency, bandwidth := ⟨0x00020000⟩ },  -- energy=10, bw=128
      reason := RoutingReason.recoveryDefer
    }
  else if goal = OperationGoal.compress then
    -- Hard constraint: memory critically low for compress
    let required := ⟨0x00000400⟩  -- 1KB in Q16_16
    let available := state.memoryBudget - state.memoryUsed
    if available < required then
      {
        action := RoutingAction.reject,
        gclCodon := 0xFF,
        cost := { energy := zero, time := zero, bandwidth := zero },
        reason := RoutingReason.insufficientMemory
      }
    else if canSatisfyLocally goal state carrier then
      -- High trust + good carrier: local execution
      if state.trustScore > ⟨0x0000CCCC⟩ ∧ carrier.lossRate < ⟨0x00000CD0⟩ then  -- trust>0.8, loss<0.05
        {
          action := RoutingAction.local,
          gclCodon := goalToCodon goal,
          cost := { energy := ⟨0x00010000⟩, time := ⟨0x00010000⟩, bandwidth := zero },  -- energy=1, time=1
          reason := RoutingReason.localTrusted
        }
      else if state.trustScore > ⟨0x00008000⟩ then  -- trust>0.5
        {
          action := RoutingAction.local,
          gclCodon := goalToCodon goal,
          cost := { energy := ⟨0x00020000⟩, time := ⟨0x00020000⟩, bandwidth := zero },  -- energy=2, time=2
          reason := RoutingReason.localVerified
        }
      else
        {
          action := RoutingAction.atlas,
          gclCodon := goalToCodon goal,
          cost := { energy := ⟨0x00050000⟩, time := carrier.latency, bandwidth := ⟨0x00010000⟩ },  -- energy=5, bw=64
          reason := RoutingReason.deferToAtlas
        }
    else
      {
        action := RoutingAction.atlas,
        gclCodon := goalToCodon goal,
        cost := { energy := ⟨0x00050000⟩, time := carrier.latency, bandwidth := ⟨0x00010000⟩ },
        reason := RoutingReason.deferToAtlas
      }
  else if canSatisfyLocally goal state carrier then
    -- High trust + good carrier: local execution
    if state.trustScore > ⟨0x0000CCCC⟩ ∧ carrier.lossRate < ⟨0x00000CD0⟩ then
      {
        action := RoutingAction.local,
        gclCodon := goalToCodon goal,
        cost := { energy := ⟨0x00010000⟩, time := ⟨0x00010000⟩, bandwidth := zero },
        reason := RoutingReason.localTrusted
      }
    else if state.trustScore > ⟨0x00008000⟩ then
      {
        action := RoutingAction.local,
        gclCodon := goalToCodon goal,
        cost := { energy := ⟨0x00020000⟩, time := ⟨0x00020000⟩, bandwidth := zero },
        reason := RoutingReason.localVerified
      }
    else
      {
        action := RoutingAction.atlas,
        gclCodon := goalToCodon goal,
        cost := { energy := ⟨0x00050000⟩, time := carrier.latency, bandwidth := ⟨0x00010000⟩ },
        reason := RoutingReason.deferToAtlas
      }
  else
    -- Low trust or cannot satisfy locally: defer to atlas
    {
      action := RoutingAction.atlas,
      gclCodon := goalToCodon goal,
      cost := { energy := ⟨0x00050000⟩, time := carrier.latency, bandwidth := ⟨0x00010000⟩ },
      reason := RoutingReason.deferToAtlas
    }

/-- Main MNN routing function -/
def mnnRoute (scalar : ScalarInput) (state : NodeState) (carrier : CarrierMetrics) : RoutingDecision :=
  let goal := scalarToGoal scalar.domain
  selectPath goal state carrier

/-- Invariant extractor for scalar input -/
def scalarInvariant (s : ScalarInput) : String :=
  s!"domain={s.domain},scalar={s.scalar}"

/-- Invariant extractor for node state -/
def stateInvariant (s : NodeState) : String :=
  s!"mem={s.memoryBudget.val}/{s.memoryUsed.val},cpu={s.cpuLoad.val},rec={s.recoveryMode},trust={s.trustScore.val}"

/-- Invariant extractor for carrier metrics -/
def carrierInvariant (c : CarrierMetrics) : String :=
  s!"shell={c.shell},lat={c.latency.val},loss={c.lossRate.val}"

/-- Invariant extractor for routing decision -/
def decisionInvariant (d : RoutingDecision) : String :=
  s!"action={d.action},codon={d.gclCodon},reason={d.reason}"

/-- Cost function for MNN routing bind -/
def mnnRoutingCost (_scalar : ScalarInput) (decision : RoutingDecision) (_metric : Metric) : Q16_16 :=
  let energyCost := decision.cost.energy
  let timeCost := decision.cost.time
  let bandwidthCost := decision.cost.bandwidth
  energyCost + timeCost + bandwidthCost  -- simple additive cost model

/-- Bind instance for MNN routing using control_bind -/
def mnnRoutingBind (scalar : ScalarInput) (state : NodeState) (carrier : CarrierMetrics) : Bind ScalarInput RoutingDecision :=
  let decision := mnnRoute scalar state carrier
  let metric := {
    cost := zero,
    tensor := "control",
    torsion := zero,
    reference := "mnn_routing_baseline",
    history_len := 0
  }
  let costFn := fun _ _ _ => mnnRoutingCost scalar decision metric
  controlBind scalar decision metric costFn scalarInvariant decisionInvariant

-- #eval examples disabled due to proof-hole axioms in FixedPoint
-- Use lake build to verify compilation

end Semantics
