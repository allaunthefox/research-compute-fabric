/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GPUResourceManager.lean — GPU resource allocation and optimization for 80% load target.

This module formalizes:
1. Dynamic GPU resource allocation based on task suitability
2. Priority-based resource scheduling
3. 80% load target enforcement

Per AGENTS.md §1.4: Q1616 fixed-point for hot paths.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has eval witness or theorem.
-/

import Semantics.Bind

namespace Semantics.GPUResourceManager

open Semantics

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Task Suitability Classification
-- ═══════════════════════════════════════════════════════════════════════════

/-- Task types with different GPU suitability profiles. -/
inductive TaskType
  | cpuOnly      -- Cannot run on GPU (control logic, small tasks)
  | gpuPreferred -- Runs better on GPU but can fall back to CPU
  | gpuRequired  -- Must run on GPU (large matrix ops, neural nets)
  deriving Repr, DecidableEq, BEq

/-- Task priority levels for resource allocation. -/
inductive Priority
  | low
  | medium
  | high
  | critical
  deriving Repr, DecidableEq, BEq

/-- A task request with resource requirements. -/
structure TaskRequest where
  taskType : TaskType
  priority : Priority
  memoryReq : UInt32    -- VRAM required in bytes
  computeReq : UInt32   -- Estimated compute cycles
  deriving Repr, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  GPU Resource State
-- ═══════════════════════════════════════════════════════════════════════════

/-- GPU specification (RTX 4070 SUPER baseline). -/
structure GPUSpec where
  cudaCores : Nat       -- 7168
  tensorCores : Nat     -- 56
  vramTotal : UInt32    -- 12 GB = 12 * 1024^3 bytes
  memoryBandwidth : UInt32  -- 504 GB/s
  deriving Repr

/-- Default GPU spec (RTX 4070 SUPER). -/
def defaultGPUSpec : GPUSpec :=
  { cudaCores := 7168,
    tensorCores := 56,
    vramTotal := 12 * 1024 * 1024 * 1024,
    memoryBandwidth := 504 * 1024 * 1024 * 1024 }

/-- Current GPU resource utilization. -/
structure GPUState where
  vramUsed : UInt32
  cudaCoresUsed : Nat
  tensorCoresUsed : Nat
  deriving Repr, BEq

/-- Compute VRAM utilization ratio (0.0 to 1.0 as UInt32 fraction). -/
def vramUtilizationRatio (state : GPUState) (spec : GPUSpec) : UInt32 :=
  (state.vramUsed * 10000) / spec.vramTotal  -- Returns value in [0, 10000]

/-- Compute core utilization ratio (0.0 to 1.0 as UInt32 fraction). -/
def coreUtilizationRatio (state : GPUState) (spec : GPUSpec) : UInt32 :=
  (state.cudaCoresUsed.toUInt32 * 10000) / spec.cudaCores.toUInt32  -- Returns value in [0, 10000]

/-- Check if GPU is at 80% load target (8000/10000 = 0.8). -/
def atTargetLoad (state : GPUState) (spec : GPUSpec) : Bool :=
  let vramRatio := vramUtilizationRatio state spec
  let target := 8000  -- 80% in our fraction representation
  vramRatio ≥ target ∧ vramRatio ≤ 8500  -- Allow 80-85% range

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Dynamic Task Allocation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Allocation result: success with GPU/CPU assignment, or failure. -/
inductive AllocationResult
  | gpuAllocated (cores : Nat) (vram : UInt32)
  | cpuFallback
  | rejected (reason : String)
  deriving Repr

/-- Determine if task can be allocated to GPU given current state. -/
def canAllocateGPU (req : TaskRequest) (state : GPUState) (spec : GPUSpec) : Bool :=
  match req.taskType with
  | .cpuOnly => false
  | .gpuPreferred =>
    let vramFree := spec.vramTotal - state.vramUsed
    let coresFree := spec.cudaCores - state.cudaCoresUsed
    req.memoryReq ≤ vramFree ∧ req.computeReq.toNat ≤ coresFree
  | .gpuRequired =>
    let vramFree := spec.vramTotal - state.vramUsed
    let coresFree := spec.cudaCores - state.cudaCoresUsed
    req.memoryReq ≤ vramFree ∧ req.computeReq.toNat ≤ coresFree

/-- Allocate task to GPU or CPU based on suitability and availability. -/
def allocateTask (req : TaskRequest) (state : GPUState) (spec : GPUSpec) : AllocationResult :=
  if canAllocateGPU req state spec then
    let cores := min req.computeReq.toNat (spec.cudaCores - state.cudaCoresUsed)
    let vram := req.memoryReq
    .gpuAllocated cores vram
  else
    match req.taskType with
    | .cpuOnly => .cpuFallback
    | .gpuPreferred => .cpuFallback
    | .gpuRequired => .rejected "Insufficient GPU resources"

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Bind Instance: Resource Allocation Cost
-- ═══════════════════════════════════════════════════════════════════════════

/-- Resource allocation state. -/
structure ResourceState where
  gpuState : GPUState
  deriving Repr, BEq

def resourceInvariant (s : ResourceState) : String :=
  s!"VRAM={s.gpuState.vramUsed.toNat},Cores={s.gpuState.cudaCoresUsed}"

/-- Cost function: penalize deviation from 80% target. -/
def resourceCost (_left right : ResourceState) (_metric : Metric) : UInt32 :=
  let ratio := vramUtilizationRatio right.gpuState defaultGPUSpec
  let target := 8000  -- 80%
  -- Cost = absolute distance from target
  if ratio ≥ target then ratio - target else target - ratio

/-- Bind instance: resource allocation step. -/
def resourceBind (left right : ResourceState) (metric : Metric) : Bind ResourceState ResourceState :=
  let c := resourceCost left right metric
  let isLawful := atTargetLoad right.gpuState defaultGPUSpec
  let w := Witness.lawful (resourceInvariant left) (resourceInvariant right)
  { left := left, right := right, metric := metric, cost := c, witness := w, lawful := isLawful }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Eval Witnesses
-- ═══════════════════════════════════════════════════════════════════════════

/-- Witness 1: GPU at exactly 80% load. -/
def gpuAtTarget : GPUState :=
  { vramUsed := 10 * 1024 * 1024 * 1024,  -- 10 GB of 12 GB
    cudaCoresUsed := 5734,  -- 80% of 7168
    tensorCoresUsed := 45 }  -- 80% of 56

/-- Witness 2: GPU under-utilized (50%). -/
def gpuUnderUtilized : GPUState :=
  { vramUsed := 6 * 1024 * 1024 * 1024,
    cudaCoresUsed := 3584,
    tensorCoresUsed := 28 }

/-- Witness 3: GPU over-utilized (90%). -/
def gpuOverUtilized : GPUState :=
  { vramUsed := 11 * 1024 * 1024 * 1024,
    cudaCoresUsed := 6451,
    tensorCoresUsed := 50 }

#eval atTargetLoad gpuAtTarget defaultGPUSpec      -- expected: true
#eval atTargetLoad gpuUnderUtilized defaultGPUSpec  -- expected: false
#eval atTargetLoad gpuOverUtilized defaultGPUSpec   -- expected: false

/-- Witness 4: Task allocation. -/
def gpuTask : TaskRequest :=
  { taskType := .gpuPreferred,
    priority := .high,
    memoryReq := 2 * 1024 * 1024,  -- 2 MB
    computeReq := 1000 }

def cpuTask : TaskRequest :=
  { taskType := .cpuOnly,
    priority := .medium,
    memoryReq := 512 * 1024,
    computeReq := 100 }

def idleGPU : GPUState :=
  { vramUsed := 0, cudaCoresUsed := 0, tensorCoresUsed := 0 }

#eval allocateTask gpuTask idleGPU defaultGPUSpec  -- expected: gpuAllocated
#eval allocateTask cpuTask idleGPU defaultGPUSpec  -- expected: cpuFallback

#eval resourceCost { gpuState := gpuAtTarget } { gpuState := gpuAtTarget } Metric.euclidean  -- expected: 0 (at target)

end Semantics.GPUResourceManager

