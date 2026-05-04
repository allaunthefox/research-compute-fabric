/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NetworkCapacity.lean — Network Resource Capacity Monitor

Replaces scripts/swarm_network_capacity.py with a formal Lean module
that defines network capacity structures and calculations.

Per AGENTS.md:
  - Q16_16 for scoring (§1.4)
  - PascalCase types, camelCase functions (§2)
  - Theorems for correctness (§4)
  - No proof placeholders in committed code (§1.6)
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic

namespace Semantics.NetworkCapacity

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16.16 Fixed-Point for Scoring
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16

def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def ofNat (n : Nat) : Q16_16 := ⟨n * 65536⟩
def toNat (q : Q16_16) : Nat := q.raw.toNat / 65536
def ofFrac (num denom : Nat) : Q16_16 :=
  if denom = 0 then zero else ⟨(num * 65536) / denom⟩

instance : LE Q16_16 := ⟨fun a b => a.raw ≤ b.raw⟩
instance : LT Q16_16 := ⟨fun a b => a.raw < b.raw⟩
instance : Add Q16_16 := ⟨fun a b => ⟨a.raw + b.raw⟩⟩
instance : Sub Q16_16 := ⟨fun a b => ⟨a.raw - b.raw⟩⟩
instance : Mul Q16_16 := ⟨fun a b => ⟨(a.raw * b.raw) / 65536⟩⟩
instance : HDiv Q16_16 Q16_16 Q16_16 := ⟨fun a b => ⟨(a.raw * 65536) / b.raw⟩⟩

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Node Status Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive NodeStatus
  | online
  | offline
  | idle
  deriving Repr, DecidableEq, Inhabited

instance : ToString NodeStatus where
  toString
  | .online => "online"
  | .offline => "offline"
  | .idle => "idle"

/-- Check if node is online (online or idle). -/
def isOnline (status : NodeStatus) : Bool :=
  match status with
  | .online => true
  | .idle => true
  | .offline => false

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Tailscale Node Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure TailscaleNode where
  ip : String
  hostname : String
  owner : String
  os : String
  status : NodeStatus
  tags : List String
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Node Resources Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure NodeResources where
  nodeId : String
  cpuCores : Nat
  memoryGb : Q16_16
  storageGb : Q16_16
  bandwidthMbps : Q16_16
  gpuCount : Nat
  eneEnabled : Bool
  utilizationPercent : Q16_16
  deriving Repr, Inhabited

/-- Estimate resources for a node based on hostname. -/
def estimateNodeResources (node : TailscaleNode) (eneNodes : List String) : NodeResources :=
  let resourceMap := [
    ("qfox", (16, 32, 1000, 1, 1000)),
    ("architect", (8, 16, 500, 0, 500)),
    ("judge", (4, 8, 200, 0, 500)),
    ("ip-172-31-25-81", (2, 4, 100, 0, 1000)),
    ("netcup-router", (4, 8, 500, 0, 1000)),
    ("racknerd-510bd9c", (2, 4, 100, 0, 1000))
  ]
  
  let defaultSpec := (2, 4, 100, 0, 100)
  let spec := resourceMap.find? (fun (name, _) => name = node.hostname) |>.map (fun (_, s) => s) |>.getD defaultSpec
  
  let (cpu, ram, storage, gpu, bw) := spec
  {
    nodeId := node.hostname,
    cpuCores := cpu,
    memoryGb := Q16_16.ofNat ram,
    storageGb := Q16_16.ofNat storage,
    bandwidthMbps := Q16_16.ofNat bw,
    gpuCount := gpu,
    eneEnabled := eneNodes.contains node.hostname,
    utilizationPercent := Q16_16.zero
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Network Capacity Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure NetworkCapacityData where
  cpuCores : Nat
  memoryGb : Q16_16
  storageGb : Q16_16
  gpuCount : Nat
  bandwidthMbps : Q16_16
  onlineNodes : Nat
  totalNodes : Nat
  deriving Repr, Inhabited

/-- Calculate total network capacity from nodes. -/
def calculateTotalCapacity (nodes : List TailscaleNode) (eneNodes : List String) : NetworkCapacityData :=
  let onlineNodes := nodes.filter (fun n => isOnline n.status)
  let resources := onlineNodes.map (fun n => estimateNodeResources n eneNodes)
  
  let totalCpu := resources.foldl (fun acc r => acc + r.cpuCores) 0
  let totalRam := resources.foldl (fun acc r => acc + r.memoryGb) Q16_16.zero
  let totalStorage := resources.foldl (fun acc r => acc + r.storageGb) Q16_16.zero
  let totalGpu := resources.foldl (fun acc r => acc + r.gpuCount) 0
  let totalBw := resources.foldl (fun acc r => acc + r.bandwidthMbps) Q16_16.zero
  
  {
    cpuCores := totalCpu,
    memoryGb := totalRam,
    storageGb := totalStorage,
    gpuCount := totalGpu,
    bandwidthMbps := totalBw,
    onlineNodes := onlineNodes.length,
    totalNodes := nodes.length
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Utilization Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure UtilizationMetrics where
  cpuPercent : Q16_16
  memoryPercent : Q16_16
  localNodeOnly : Bool
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Capacity Report Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure CapacityReport where
  totalNodes : Nat
  onlineNodes : Nat
  offlineNodes : Nat
  eneDeployed : Nat
  eneCoverage : Q16_16
  capacity : NetworkCapacityData
  utilization : UtilizationMetrics
  deriving Repr, Inhabited

/-- Calculate ENE coverage percentage. -/
def calculateENECoverage (eneDeployed : Nat) (onlineNodes : Nat) : Q16_16 :=
  if onlineNodes = 0 then Q16_16.zero
  else Q16_16.ofFrac (eneDeployed * 100) onlineNodes

/-- Generate capacity report. -/
def generateCapacityReport (nodes : List TailscaleNode) (eneNodes : List String) (utilization : UtilizationMetrics) : CapacityReport :=
  let onlineCount := (nodes.filter (fun n => isOnline n.status)).length
  let offlineCount := nodes.length - onlineCount
  let capacity := calculateTotalCapacity nodes eneNodes
  let eneCoverage := calculateENECoverage eneNodes.length onlineCount
  
  {
    totalNodes := nodes.length,
    onlineNodes := onlineCount,
    offlineNodes := offlineCount,
    eneDeployed := eneNodes.length,
    eneCoverage := eneCoverage,
    capacity := capacity,
    utilization := utilization
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Example Usage
-- ═══════════════════════════════════════════════════════════════════════════

#eval isOnline NodeStatus.online

#eval isOnline NodeStatus.offline

#eval estimateNodeResources { ip := "100.0.0.1", hostname := "qfox", owner := "user", os := "linux", status := NodeStatus.online, tags := [] } ["qfox", "architect"]

#eval calculateENECoverage 3 6

end Semantics.NetworkCapacity
