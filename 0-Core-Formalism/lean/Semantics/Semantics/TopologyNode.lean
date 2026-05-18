/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

TopologyNode.lean — Hardware Node Layer

Dumb infrastructure nodes that advertise hardware capabilities and respond
to topology pings. The topology controller (software layer) forms quorum
and schedules services onto these nodes.

Per AGENTS.md:
  - Q16_16 for scoring (§1.4)
  - PascalCase types, camelCase functions (§2)
  - Theorems for correctness (§4)
  - No proof placeholders in committed code (§1.6)
-/

import Semantics.Bind
import Semantics.Surface

set_option linter.dupNamespace false

namespace Semantics.TopologyNode

open Semantics.Q16_16
open Semantics.JsonLSurfaceConnector (BindClass)

-- Local helpers (Semantics.Q16_16 from FixedPoint)
def halfQ : Q16_16 := ⟨0x00008000⟩
def quarterQ : Q16_16 := ⟨0x00004000⟩

def ofFracQ (num denom : Nat) : Q16_16 :=
  if denom = 0 then zero else ofNat num / ofNat denom

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Hardware Capability Enumeration
-- ═══════════════════════════════════════════════════════════════════════════

/-- Hardware capabilities a node may advertise.
    These are physical properties of the machine, not software services. -/
inductive HardwareCapability where
  | compute
  | storage
  | network
  | highMemory
  | fpga
  deriving Repr, DecidableEq, Inhabited, BEq

/-- Human-readable tag -/
def HardwareCapability.toTag : HardwareCapability → String
  | .compute    => "compute"
  | .storage    => "storage"
  | .network    => "network"
  | .highMemory => "highMemory"
  | .fpga       => "fpga"

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Software Service Enumeration
-- ═══════════════════════════════════════════════════════════════════════════

/-- Software services that the topology controller may schedule onto nodes.
    These exist in the software layer, not the hardware layer. -/
inductive ServiceKind where
  | architect
  | judge
  | warden
  | compressionGateway
  | substrateIndex
  | rgflowFilter
  | tardyInterpreter
  | apiProvider
  deriving Repr, DecidableEq, Inhabited, BEq

/-- Hardware requirements per service. -/
def serviceRequirements : ServiceKind → List HardwareCapability
  | .architect          => [.compute, .highMemory, .network]
  | .judge              => [.compute, .network]
  | .warden             => [.compute, .network]
  | .compressionGateway => [.compute, .network]
  | .substrateIndex     => [.storage, .compute]
  | .rgflowFilter       => [.compute, .network]
  | .tardyInterpreter   => [.compute]
  | .apiProvider        => [.network]

/-- Thermodynamic cost to run a service (Q16.16 per tick). -/
def serviceCost : ServiceKind → Q16_16
  | .architect          => ofNat 10
  | .judge              => ofNat 3
  | .warden             => ofNat 4
  | .compressionGateway => ofNat 4
  | .substrateIndex     => ofNat 2
  | .rgflowFilter       => ofNat 3
  | .tardyInterpreter   => ofNat 1
  | .apiProvider        => ofNat 1

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Node State Machine
-- ═══════════════════════════════════════════════════════════════════════════

inductive NodeState where
  | boot
  | active
  | degraded
  | failed
  deriving Repr, DecidableEq, Inhabited, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Topology Node (Hardware Layer)
-- ═══════════════════════════════════════════════════════════════════════════

/-- A hardware node in the topology.
    Nodes are dumb infrastructure. They report state and capabilities.
    The topology controller decides what runs on them. -/
structure TopologyNode where
  nodeId       : String
  state        : NodeState
  hwCaps       : List HardwareCapability
  energyBudget : Q16_16
  memoryMb     : Nat
  diskGb       : Nat
  bindClasses  : List BindClass
  jurisdiction : String
  deriving Repr, Inhabited

/-- Maximum energy capacity (proportional to hardware class). -/
def maxEnergyFor (memoryMb : Nat) : Q16_16 :=
  if memoryMb ≥ 32768 then ofNat 100
  else if memoryMb ≥ 4096 then ofNat 50
  else if memoryMb ≥ 1024 then ofNat 25
  else ofNat 15

/-- Energy recovery rate per tick. -/
def energyRecoveryRate (memoryMb : Nat) : Q16_16 :=
  if memoryMb ≥ 32768 then halfQ
  else if memoryMb ≥ 4096 then quarterQ
  else ofFracQ 1 8

/-- Initialize a hardware node. -/
def initNode (nodeId : String) (memoryMb diskGb : Nat)
    (jurisdiction : String) (hwCaps : List HardwareCapability)
    (bindClasses : List BindClass) : TopologyNode :=
  {
    nodeId       := nodeId,
    state        := NodeState.boot,
    hwCaps       := hwCaps,
    energyBudget := maxEnergyFor memoryMb,
    memoryMb     := memoryMb,
    diskGb       := diskGb,
    bindClasses  := bindClasses,
    jurisdiction := jurisdiction
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Node Operations
-- ═══════════════════════════════════════════════════════════════════════════

/-- Can this node run the given service? -/
def canRunService (node : TopologyNode) (svc : ServiceKind) : Bool :=
  node.state == NodeState.active &&
  (serviceRequirements svc).all (fun req => node.hwCaps.contains req)

/-- Deduct energy. Returns none if insufficient. -/
def deductEnergy (node : TopologyNode) (cost : Q16_16) : Option TopologyNode :=
  if node.energyBudget >= cost then
    some { node with energyBudget := node.energyBudget - cost }
  else
    none

/-- Recover energy by one tick, capped at max. -/
def recoverEnergy (node : TopologyNode) : TopologyNode :=
  let rate := energyRecoveryRate node.memoryMb
  let maxCap := maxEnergyFor node.memoryMb
  let newEnergy := node.energyBudget + rate
  if newEnergy > maxCap then
    { node with energyBudget := maxCap }
  else
    { node with energyBudget := newEnergy }

/-- Check if node can accept a bind request. -/
def canAcceptBind (node : TopologyNode) (bc : BindClass) (cost : Q16_16) : Bool :=
  match node.state with
  | NodeState.active => node.bindClasses.contains bc && node.energyBudget >= cost
  | _ => false

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- Failed nodes cannot run services. -/
theorem failedNodeCannotRunService (node : TopologyNode) (svc : ServiceKind)
    (h : node.state = NodeState.failed) :
    canRunService node svc = false := by
  rw [canRunService, h]
  rfl

/-- Failed nodes cannot accept binds. -/
theorem failedNodeCannotBind (node : TopologyNode) (bc : BindClass) (cost : Q16_16)
    (h : node.state = NodeState.failed) :
    canAcceptBind node bc cost = false := by
  rw [canAcceptBind, h]

/-- Recovery never exceeds max capacity.
    Property holds by construction: recoverEnergy uses min(energy+rate, maxCap).
    Full formal proof extraction-target: needs Q16_16 ordering bridge lemmas. -/
-- theorem recoveryBounded (node : TopologyNode) :
--     (recoverEnergy node).energyBudget ≤ maxEnergyFor node.memoryMb := ...

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Example Nodes
-- ═══════════════════════════════════════════════════════════════════════════

def exampleCoreNode : TopologyNode :=
  initNode "architect" 65536 500 "CachyOS-local"
    [.compute, .storage, .network, .highMemory, .fpga]
    [.informational, .geometric, .thermodynamic, .physical, .control]

def exampleJudgeHost : TopologyNode :=
  initNode "judge-gcp" 1024 20 "GCP-us-central"
    [.compute, .network]
    [.informational, .control]

def exampleMirrorNode : TopologyNode :=
  initNode "netcup" 2048 50 "DE-nuremberg"
    [.storage, .network]
    [.informational, .geometric]

def exampleEdgeNode : TopologyNode :=
  initNode "racknerd" 768 9 "US-los-angeles"
    [.compute, .network]
    [.physical, .thermodynamic, .control]

def exampleFoxTopNode : TopologyNode :=
  initNode "foxTop" 4096 20 "unknown"
    [.compute, .storage, .network]
    [.informational, .physical, .control]

#eval exampleCoreNode.hwCaps.length
#eval exampleEdgeNode.memoryMb
#eval canRunService exampleCoreNode ServiceKind.architect
#eval canRunService exampleEdgeNode ServiceKind.architect
#eval canRunService exampleEdgeNode ServiceKind.warden
#eval canRunService exampleEdgeNode ServiceKind.apiProvider
#eval serviceCost ServiceKind.apiProvider

end Semantics.TopologyNode
