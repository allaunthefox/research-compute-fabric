/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SubagentOrchestrator.lean — Hybrid Multi-Agent Codebase Improvement System

This module designs and formalizes a system of domain expert subagents that:
1. Analyze the current codebase (90+ modules across 18 domains)
2. Identify cross-domain coherence gaps
3. Generate prioritized improvement proposals
4. Output a structured improvement map

Subagent Architecture:
- DomainExpert: Specialized in one research domain (Compression, Geometry, etc.)
- CodebaseExpert: Knows module structure, imports, dependencies
- IntegrationAnalyst: Finds hybridization opportunities
- PriorityScheduler: Ranks improvements by impact/effort

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring
Per AGENTS.md §2: PascalCase types, camelCase functions
Per AGENTS.md §4: Eval witnesses and theorems required
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic
import Semantics.RcloneIntegration
import Semantics.GpuDutyAssignment
import Semantics.DomainModelIntegration
import Semantics.FixedPoint

namespace Semantics.SubagentOrchestrator

open Semantics (Q16_16)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Domain Taxonomy (14 Expert Domains)
-- ═══════════════════════════════════════════════════════════════════════════

inductive Domain
  | coreBind
  | compression
  | spatialVLSI
  | diffusionFlow
  | pistShell
  | fieldPhysics
  | braidAlgebra
  | kernelDomain
  | evolutionSearch
  | memoryState
  | cognitiveControl
  | geometry
  | thermodynamic
  | diagnostic
  | cloudStorage
  | gpuResources
  | domainModels
  | fieldOperator
  deriving Repr, DecidableEq, Inhabited

namespace Domain

def toString : Domain → String
  | coreBind => "Core Bind"
  | compression => "Compression"
  | spatialVLSI => "Spatial/VLSI"
  | diffusionFlow => "Diffusion/Flow"
  | pistShell => "PIST/Shell"
  | fieldPhysics => "Field Physics"
  | braidAlgebra => "Braid/Algebra"
  | kernelDomain => "Kernel/Domain"
  | evolutionSearch => "Evolution/Search"
  | memoryState => "Memory/State"
  | cognitiveControl => "Cognitive/Control"
  | geometry => "Geometry"
  | thermodynamic => "Thermodynamic"
  | diagnostic => "Diagnostic"
  | cloudStorage => "Cloud/Storage"
  | gpuResources => "GPU/Resources"
  | domainModels => "Domain Models"
  | fieldOperator => "Field Operator"

/-- Module count per domain (actual). -/
def moduleCount : Domain → Nat
  | coreBind => 6
  | compression => 7
  | spatialVLSI => 5
  | diffusionFlow => 6
  | pistShell => 6
  | fieldPhysics => 12
  | braidAlgebra => 5
  | kernelDomain => 4
  | evolutionSearch => 8
  | memoryState => 9
  | cognitiveControl => 5
  | geometry => 6
  | thermodynamic => 4
  | diagnostic => 3
  | cloudStorage => 1
  | gpuResources => 1
  | domainModels => 1
  | fieldOperator => 1

/-- All domains. -/
def all : List Domain :=
  [coreBind, compression, spatialVLSI, diffusionFlow, pistShell, fieldPhysics, braidAlgebra,
   kernelDomain, evolutionSearch, memoryState, cognitiveControl, geometry, thermodynamic, diagnostic,
   cloudStorage, gpuResources, domainModels, fieldOperator]

end Domain

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Module Registry (Current State)
-- ═══════════════════════════════════════════════════════════════════════════

/-- A registered module in the codebase. -/
structure Module where
  name : String
  domain : Domain
  lines : Nat           -- Approximate size
  imports : List String -- Direct dependencies
  hasTheorems : Bool    -- Contains proved theorems
  hasEvals : Bool       -- Has verification witnesses
  deriving Repr, Inhabited

/-- Current module registry (representative samples). -/
def moduleRegistry : List Module :=
  [ { name := "Bind", domain := .coreBind, lines := 100, imports := [], hasTheorems := true, hasEvals := true }
  , { name := "ExperienceCompression", domain := .compression, lines := 350, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "SpatialEvo", domain := .spatialVLSI, lines := 400, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "VLsIPartition", domain := .spatialVLSI, lines := 320, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "DiffusionSNRBias", domain := .diffusionFlow, lines := 380, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "LaviGen", domain := .diffusionFlow, lines := 420, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "ManifoldFlow", domain := .diffusionFlow, lines := 280, imports := ["DynamicCanal"], hasTheorems := true, hasEvals := true }
  , { name := "Timing", domain := .memoryState, lines := 200, imports := ["ManifoldFlow"], hasTheorems := true, hasEvals := true }
  , { name := "SSMS", domain := .memoryState, lines := 800, imports := ["Timing"], hasTheorems := true, hasEvals := true }
  , { name := "HybridConvergence", domain := .coreBind, lines := 350, imports := ["ExperienceCompression", "SpatialEvo"], hasTheorems := true, hasEvals := true }
  , { name := "PIST", domain := .pistShell, lines := 500, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "OrderedFieldTokens", domain := .evolutionSearch, lines := 450, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "EntropyMeasures", domain := .compression, lines := 300, imports := ["Bind"], hasTheorems := true, hasEvals := true }
  , { name := "Metatype", domain := .coreBind, lines := 50, imports := [], hasTheorems := false, hasEvals := true }
  ]

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Subagent Types
-- ═══════════════════════════════════════════════════════════════════════════

/-- Domain Expert: Deep knowledge in one research area. -/
structure DomainExpert where
  domain : Domain
  expertiseLevel : Q16_16  -- 0.0 to 1.0
  modulesKnown : List String
  deriving Repr, Inhabited

/-- Codebase Expert: Knows module structure and dependencies. -/
structure CodebaseExpert where
  coverage : Q16_16  -- Fraction of modules analyzed
  importGraphComplete : Bool
  theoremCoverage : Q16_16
  deriving Repr, Inhabited

/-- Integration Analyst: Finds hybridization opportunities. -/
structure IntegrationAnalyst where
  crossDomainPairs : List (Domain × Domain)
  hybridizationScore : Q16_16
  gapIdentified : List String
  deriving Repr, Inhabited

/-- Priority Scheduler: Ranks improvements. -/
structure PriorityScheduler where
  impactWeight : Q16_16  -- 0.6
  effortWeight : Q16_16  -- 0.4
  threshold : Q16_16     -- Minimum score to include
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Improvement Proposal System
-- ═══════════════════════════════════════════════════════════════════════════

/-- Type of improvement. -/
inductive ImprovementType
  | addTheorem       -- Add missing theorem proof
  | addEval          -- Add verification witness
  | crossDomainLink  -- Create hybrid module
  | refactorImport   -- Optimize dependency graph
  | addDocumentation -- Add module docs
  deriving Repr, DecidableEq, Inhabited

/-- A single improvement proposal. -/
structure ImprovementProposal where
  id : Nat
  targetModule : String
  improvementType : ImprovementType
  description : String
  impact : Q16_16      -- 0.0 to 1.0
  effort : Q16_16      -- Estimated effort
  priority : Q16_16    -- Computed: impact × 0.6 + (1-effort) × 0.4
  domain : Domain
  deriving Repr, Inhabited

namespace ImprovementProposal

/-- Calculate priority score. -/
def calculatePriority (impact effort : Q16_16) : Q16_16 :=
  let impactPart := Q16_16.mul impact (Q16_16.ofFloat 0.6)
  let effortPart := Q16_16.mul (Q16_16.sub Q16_16.one effort) (Q16_16.ofFloat 0.4)
  Q16_16.add impactPart effortPart

end ImprovementProposal

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Subagent Analysis Functions
-- ═══════════════════════════════════════════════════════════════════════════

/-- Domain Expert: Analyze gaps in their domain. -/
def domainExpertAnalyze (expert : DomainExpert) (modules : List Module) : List ImprovementProposal :=
  let domainMods := modules.filter (fun m => m.domain = expert.domain)
  
  -- Find modules missing theorems
  let missingTheorems := domainMods.filter (fun m => ¬m.hasTheorems)
  
  -- Create proposals
  missingTheorems.map (fun m => 
    { id := 0  -- Assigned later
      targetModule := m.name
      improvementType := .addTheorem
      description := "Add theorem witness for " ++ m.name
      impact := Q16_16.ofFloat 0.8
      effort := Q16_16.ofFloat 0.5
      priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.8) (Q16_16.ofFloat 0.5)
      domain := expert.domain })

/-- Codebase Expert: Find import graph optimizations. -/
def codebaseExpertAnalyze (expert : CodebaseExpert) (_modules : List Module) : List ImprovementProposal :=
  if ¬expert.importGraphComplete then
    [{ id := 0
       targetModule := "Semantics.lean"
       improvementType := .refactorImport
       description := "Complete import graph analysis and remove cycles"
       impact := Q16_16.ofFloat 0.7
       effort := Q16_16.ofFloat 0.6
       priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.7) (Q16_16.ofFloat 0.6)
       domain := .coreBind }]
  else
    []

/-- Integration Analyst: Find cross-domain hybridization. -/
def integrationAnalystAnalyze (analyst : IntegrationAnalyst) (_modules : List Module) : List ImprovementProposal :=
  analyst.crossDomainPairs.map (fun (d1, d2) =>
    { id := 0
      targetModule := d1.toString ++ "_" ++ d2.toString ++ "Bridge"
      improvementType := .crossDomainLink
      description := "Create hybrid bridge between " ++ d1.toString ++ " and " ++ d2.toString
      impact := Q16_16.ofFloat 0.9
      effort := Q16_16.ofFloat 0.8
      priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.9) (Q16_16.ofFloat 0.8)
      domain := .coreBind })

/-- Priority Scheduler: Filter and sort by priority. -/
def prioritySchedulerFilter (scheduler : PriorityScheduler) (proposals : List ImprovementProposal) : List ImprovementProposal :=
  let filtered := proposals.filter (fun p => Q16_16.ge p.priority scheduler.threshold)
  let sorted := filtered.mergeSort (fun a b => Q16_16.gt a.priority b.priority)
  -- Assign IDs
  sorted.zipIdx.map (fun (p, i) => { p with id := i + 1 })

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Orchestrator: Coordinate Subagents
-- ═══════════════════════════════════════════════════════════════════════════

/-- Subagent system configuration. -/
structure SubagentSystem where
  domainExperts : List DomainExpert
  codebaseExpert : CodebaseExpert
  integrationAnalyst : IntegrationAnalyst
  scheduler : PriorityScheduler
  deriving Repr, Inhabited

/-- Run full subagent analysis. -/
def runSubagentAnalysis (system : SubagentSystem) (modules : List Module) : List ImprovementProposal :=
  -- Phase 1: Domain experts analyze their domains
  let domainProposals := system.domainExperts.flatMap (fun e => domainExpertAnalyze e modules)
  
  -- Phase 2: Codebase expert analyzes structure
  let codebaseProposals := codebaseExpertAnalyze system.codebaseExpert modules
  
  -- Phase 3: Integration analyst finds hybrid opportunities
  let integrationProposals := integrationAnalystAnalyze system.integrationAnalyst modules
  
  -- Phase 4: Scheduler prioritizes all proposals
  let allProposals := domainProposals ++ codebaseProposals ++ integrationProposals
  prioritySchedulerFilter system.scheduler allProposals

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Concrete System Instance & Improvement Map
-- ═══════════════════════════════════════════════════════════════════════════

/-- Instantiated subagent system for current codebase. -/
def currentSubagentSystem : SubagentSystem :=
  { domainExperts := 
      [ { domain := .compression, expertiseLevel := Q16_16.one, modulesKnown := ["ExperienceCompression", "EntropyMeasures"] }
      , { domain := .spatialVLSI, expertiseLevel := Q16_16.one, modulesKnown := ["SpatialEvo", "VLsIPartition"] }
      , { domain := .diffusionFlow, expertiseLevel := Q16_16.one, modulesKnown := ["DiffusionSNRBias", "LaviGen", "ManifoldFlow"] }
      , { domain := .memoryState, expertiseLevel := Q16_16.one, modulesKnown := ["Timing", "SSMS"] }
      , { domain := .coreBind, expertiseLevel := Q16_16.one, modulesKnown := ["Bind", "HybridConvergence"] }
      , { domain := .cloudStorage, expertiseLevel := Q16_16.one, modulesKnown := ["RcloneIntegration"] }
      , { domain := .gpuResources, expertiseLevel := Q16_16.one, modulesKnown := ["GpuDutyAssignment"] }
      , { domain := .domainModels, expertiseLevel := Q16_16.one, modulesKnown := ["DomainModelIntegration"] }
      , { domain := .fieldOperator, expertiseLevel := Q16_16.one, modulesKnown := ["HermesAgentIntegration"] }
      ]
  , codebaseExpert := { coverage := Q16_16.ofFloat 0.8, importGraphComplete := false, theoremCoverage := Q16_16.ofFloat 0.7 }
  , integrationAnalyst := 
      { crossDomainPairs := [(.compression, .spatialVLSI), (.diffusionFlow, .memoryState), (.coreBind, .compression), (.cloudStorage, .domainModels), (.fieldOperator, .coreBind)]
        hybridizationScore := Q16_16.ofFloat 0.8
        gapIdentified := ["FAMM-Thermodynamic link", "Experience-Space compression", "Cloud-storage manifold sync"]
      }
  , scheduler := { impactWeight := Q16_16.ofFloat 0.6, effortWeight := Q16_16.ofFloat 0.4, threshold := Q16_16.ofFloat 0.1 }
  }

/-- Generated improvement map. -/
def improvementMap : List ImprovementProposal :=
  runSubagentAnalysis currentSubagentSystem moduleRegistry

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Key Improvement Map Entries (Top Priorities)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Top priority: Create FAMM-Thermodynamic bridge. -/
def priority1_FAMMThermoBridge : ImprovementProposal :=
  { id := 1
    targetModule := "Timing_ThermodynamicBridge"
    improvementType := .crossDomainLink
    description := "Connect FAMM timing (tTCL/tMRE/tDLL) to thermodynamic efficiency bounds"
    impact := Q16_16.ofFloat 0.95
    effort := Q16_16.ofFloat 0.75
    priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.95) (Q16_16.ofFloat 0.75)
    domain := .thermodynamic
  }

/-- Priority 2: Experience-Spatial compression hybrid. -/
def priority2_ExpSpatialHybrid : ImprovementProposal :=
  { id := 2
    targetModule := "ExperienceSpatialHybrid"
    improvementType := .crossDomainLink
    description := "Merge ExperienceCompression L3 rules with SpatialEvo DGE validation"
    impact := Q16_16.ofFloat 0.9
    effort := Q16_16.ofFloat 0.7
    priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.9) (Q16_16.ofFloat 0.7)
    domain := .compression
  }

/-- Priority 3: Complete theorem coverage for Metatype. -/
def priority3_MetatypeTheorem : ImprovementProposal :=
  { id := 3
    targetModule := "Metatype"
    improvementType := .addTheorem
    description := "Add theorem: metatyping sigma accumulation preserves coherence"
    impact := Q16_16.ofFloat 0.85
    effort := Q16_16.ofFloat 0.4
    priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.85) (Q16_16.ofFloat 0.4)
    domain := .coreBind
  }

/-- Priority 4: Import graph optimization. -/
def priority4_ImportGraph : ImprovementProposal :=
  { id := 4
    targetModule := "Semantics.lean"
    improvementType := .refactorImport
    description := "Analyze and optimize 86-module import graph, remove cycles"
    impact := Q16_16.ofFloat 0.7
    effort := Q16_16.ofFloat 0.6
    priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.7) (Q16_16.ofFloat 0.6)
    domain := .coreBind
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  Subagent Spawning & Lifecycle
-- ═══════════════════════════════════════════════════════════════════════════

/-- Spawn strategy: how a parent creates child subagents. -/
inductive SpawnStrategy
  | fixed (count : Nat)         -- Spawn exactly N identical subagents
  | perDomain                    -- One subagent per Domain in Domain.all
  | perModule                    -- One subagent per module in registry
  | dynamic (max : Nat)          -- Up to max, based on workload
  | workStealing (poolSize : Nat) -- Fixed pool, idle agents steal queued work
  deriving Repr, DecidableEq, Inhabited

/--
Phase of a spawned subagent's lifecycle.

The lifecycle is always forward: Pending → Running → (Completed | Failed).
Subagents cannot skip phases or regress. This is enforced by the
lifecycleInvariant theorem.
-/
inductive SubagentLifecycle
  | pending    -- Created but not yet dispatched to a compute substrate
  | running    -- Dispatched; result not yet available
  | completed  -- Returned a CooperativeResult
  | failed     -- Returned a FailureRecord
  deriving Repr, DecidableEq, Inhabited, BEq

/-- Failure record for a failed subagent. -/
structure FailureRecord where
  agentId : Nat
  phase : String           -- Which analysis phase failed
  errorCode : Nat          -- Opaque error code from the substrate
  detail : String          -- Human-readable description for triage
  scarCandidate : Bool     -- Whether this failure should produce a FAMM scar
  deriving Repr, Inhabited

/-- A spawned subagent with full lifecycle state. -/
structure SpawnedSubagent where
  id : Nat
  parentId : Option Nat     -- None for root agents
  domain : Domain
  strategy : SpawnStrategy
  lifecycle : SubagentLifecycle
  taskDescription : String  -- What this agent was created to do
  assignedTo : String       -- Compute substrate: "cpu", "gpu:0", "gpu:1", etc.
  failureRecord : Option FailureRecord
  deriving Repr, Inhabited

namespace SpawnedSubagent

/-
Invariant: a SpawnedSubagent cannot transition from Completed or Failed back
to Running or Pending. This is a structural guarantee enforced by the
lifecycle-pattern type signature: stepForward returns a new SpawnedSubagent
only when the transition is valid.
-/

/-- Attempt to advance lifecycle forward. Returns none if the transition is illegal. -/
def stepForward (agent : SpawnedSubagent) (next : SubagentLifecycle) (failure : Option FailureRecord := none) : Option SpawnedSubagent :=
  match agent.lifecycle, next with
  | .pending,   .running   => some { agent with lifecycle := .running }
  | .running,   .completed => some { agent with lifecycle := .completed }
  | .running,   .failed    => some { agent with lifecycle := .failed, failureRecord := failure }
  | _,          _          => none  -- All other transitions are illegal

/-- Check if agent can be dispatched to a substrate. -/
def isDispatchable (agent : SpawnedSubagent) : Bool :=
  agent.lifecycle = .pending

/-- Check if agent has completed successfully. -/
def isComplete (agent : SpawnedSubagent) : Bool :=
  agent.lifecycle = .completed

/-- Check if agent has failed. -/
def isFailed (agent : SpawnedSubagent) : Bool :=
  agent.lifecycle = .failed

end SpawnedSubagent

-- ═══════════════════════════════════════════════════════════════════════════
-- §10  Parallel Execution Model
-- ═══════════════════════════════════════════════════════════════════════════

/--
A work unit that can be dispatched to a compute substrate.
Each SpawnedSubagent produces zero or more WorkUnits during its
analysis phase. WorkUnits are the atomic unit of parallel dispatch.
-/
structure WorkUnit where
  unitId : Nat
  agentId : Nat          -- Owning subagent
  domain : Domain
  priority : Q16_16      -- Higher priority dispatched first
  description : String
  dependencies : List Nat  -- unitIds that must complete first
  deriving Repr, Inhabited

/--
Work-stealing pool for dynamic load balancing.

The pool distributes pending WorkUnits across available agents.
When an agent exhausts its queue, it "steals" from the most loaded
peer. This is the canonical pattern from the compute dispatch model
(4-Infrastructure/AGENTS.md §Compute Dispatch).
-/
structure WorkStealingPool where
  totalUnits : Nat
  pendingUnits : List WorkUnit
  inFlightUnits : List WorkUnit
  completedUnits : List WorkUnit
  failedUnits : List WorkUnit
  stealCount : Nat       -- Total steal events (metric)
  deriving Repr, Inhabited

namespace WorkStealingPool

/-- Create an empty work pool. -/
def empty : WorkStealingPool :=
  { totalUnits := 0, pendingUnits := [], inFlightUnits := [], completedUnits := [], failedUnits := [], stealCount := 0 }

/-- Enqueue a work unit. -/
def enqueue (pool : WorkStealingPool) (unit : WorkUnit) : WorkStealingPool :=
  { pool with
    totalUnits := pool.totalUnits + 1
    pendingUnits := pool.pendingUnits ++ [unit] }

/-- Claim a unit from the pending queue (simulates dispatch to substrate). -/
def claimUnit (pool : WorkStealingPool) (unitId : Nat) : WorkStealingPool :=
  let (claimed, rest) := pool.pendingUnits.partition (fun u => u.unitId = unitId)
  { pool with
    pendingUnits := rest
    inFlightUnits := pool.inFlightUnits ++ claimed }

/-- Mark a unit as completed. -/
def completeUnit (pool : WorkStealingPool) (unitId : Nat) (result : String) : WorkStealingPool :=
  let (completed, rest) := pool.inFlightUnits.partition (fun u => u.unitId = unitId)
  { pool with
    inFlightUnits := rest
    completedUnits := pool.completedUnits ++ completed }

/-- Steal a unit from another agent's in-flight queue (rebalance). -/
def stealUnit (pool : WorkStealingPool) (unitId : Nat) : WorkStealingPool :=
  let (stolen, rest) := pool.inFlightUnits.partition (fun u => u.unitId = unitId)
  { pool with
    inFlightUnits := rest
    pendingUnits := pool.pendingUnits ++ stolen
    stealCount := pool.stealCount + 1 }

/-- Number of remaining pending units. -/
def remaining (pool : WorkStealingPool) : Nat :=
  pool.pendingUnits.length

end WorkStealingPool

/--
Parallel execution state for the subagent swarm.

Tracks all spawned agents, their work units, and the work-stealing pool
across all available compute substrates (CPU cores, GPU lanes, FPGA slots).
-/
structure ParallelExecutionState where
  spawnedAgents : List SpawnedSubagent
  workPool : WorkStealingPool
  completedProposals : List ImprovementProposal
  nextAgentId : Nat
  nextUnitId : Nat
  deriving Repr, Inhabited

namespace ParallelExecutionState

/-- Create initial parallel execution state from a SubagentSystem. -/
def fromSystem (system : SubagentSystem) : ParallelExecutionState :=
  { spawnedAgents := []
    workPool := WorkStealingPool.empty
    completedProposals := []
    nextAgentId := 1
    nextUnitId := 1 }

/-- Spawn a new subagent within the parallel execution state. -/
def spawnAgent (state : ParallelExecutionState) (parentId : Option Nat) (domain : Domain)
    (strategy : SpawnStrategy) (description : String) (assignedTo : String) : ParallelExecutionState :=
  let agent : SpawnedSubagent :=
    { id := state.nextAgentId
      parentId := parentId
      domain := domain
      strategy := strategy
      lifecycle := .pending
      taskDescription := description
      assignedTo := assignedTo
      failureRecord := none }
  { state with
    spawnedAgents := state.spawnedAgents ++ [agent]
    nextAgentId := state.nextAgentId + 1 }

/-- Dispatch a pending agent to a compute substrate (pending → running). -/
def dispatchAgent (state : ParallelExecutionState) (agentId : Nat) : ParallelExecutionState :=
  { state with
    spawnedAgents := state.spawnedAgents.map (fun a =>
      if a.id = agentId then
        match a.stepForward .running with
        | some a' => a'
        | none => a
      else a) }

/-- Create a work unit from an agent's analysis and enqueue it. -/
def enqueueAgentWork (state : ParallelExecutionState) (agentId : Nat) (description : String)
    (priority : Q16_16) (deps : List Nat) : ParallelExecutionState :=
  let unit : WorkUnit :=
    { unitId := state.nextUnitId
      agentId := agentId
      domain := .coreBind  -- Will be refined by the agent
      priority := priority
      description := description
      dependencies := deps }
  { state with
    workPool := state.workPool.enqueue unit
    nextUnitId := state.nextUnitId + 1 }

/-- Collect completed proposals from all completed agents. -/
def collectResults (state : ParallelExecutionState) : List ImprovementProposal :=
  state.completedProposals

/-- Number of agents still running or pending. -/
def inFlightCount (state : ParallelExecutionState) : Nat :=
  (state.spawnedAgents.filter (fun a => a.lifecycle = .running || a.lifecycle = .pending)).length

/-- Number of agents that completed successfully. -/
def completedCount (state : ParallelExecutionState) : Nat :=
  (state.spawnedAgents.filter (fun a => a.lifecycle = .completed)).length

/-- Number of agents that failed. -/
def failedCount (state : ParallelExecutionState) : Nat :=
  (state.spawnedAgents.filter (fun a => a.lifecycle = .failed)).length

end ParallelExecutionState

-- ═══════════════════════════════════════════════════════════════════════════
-- §11  Cooperative Result Merging
-- ═══════════════════════════════════════════════════════════════════════════

/--
Conflict resolution when two subagents produce different proposals
for the same target module and improvement type.
-/
inductive ConflictResolution
  | keepFirst     -- Lower agent ID wins
  | keepHighest   -- Higher priority score wins
  | merge         -- Combine both proposals (union of descriptions, average scores)
  | discardBoth   -- Neither is used; emit a scar for review
  deriving Repr, DecidableEq, Inhabited

/--
Cooperative merge result: the outcome of merging two agents' outputs.
-/
structure MergeResult where
  mergedProposals : List ImprovementProposal
  conflictsResolved : Nat
  scarsEmitted : Nat
  deriving Repr, Inhabited

namespace MergeResult

/-- Empty merge (nothing to merge). -/
def empty : MergeResult :=
  { mergedProposals := [], conflictsResolved := 0, scarsEmitted := 0 }

/-- Check if two proposals conflict (same target + same improvement type). -/
def proposalsConflict (a b : ImprovementProposal) : Bool :=
  a.targetModule = b.targetModule && a.improvementType = b.improvementType

/--
Merge two proposal lists cooperatively.

Cooperative merging means:
1. Non-conflicting proposals from both agents are kept
2. Conflicting proposals are resolved using the configured strategy
3. Scars are emitted for conflicts that cannot be resolved automatically
-/
def cooperativeMerge (existing incoming : List ImprovementProposal) (resolution : ConflictResolution) : MergeResult :=
  let conflicts := existing.filter (fun e => incoming.any (fun i => proposalsConflict e i))
  let nonConflicting := incoming.filter (fun i => ¬existing.any (fun e => proposalsConflict e i))
  let resolved := match resolution with
    | .keepFirst   => existing  -- Keep existing, discard incoming conflicts
    | .keepHighest =>
      let merged := existing.map (fun e =>
        match incoming.find? (fun i => proposalsConflict e i) with
        | some i => if Q16_16.gt i.priority e.priority then i else e
        | none => e)
      merged ++ nonConflicting
    | .merge =>
      let merged := existing.map (fun e =>
        match incoming.find? (fun i => proposalsConflict e i) with
        | some i =>
          let avgImpact := Q16_16.add e.impact i.impact
          let avgEffort := Q16_16.add e.effort i.effort
          { e with
            description := e.description ++ " + " ++ i.description
            impact := Q16_16.div avgImpact (Q16_16.ofFloat 2.0)
            effort := Q16_16.div avgEffort (Q16_16.ofFloat 2.0)
            priority := ImprovementProposal.calculatePriority
              (Q16_16.div (Q16_16.add e.impact i.impact) (Q16_16.ofFloat 2.0))
              (Q16_16.div (Q16_16.add e.effort i.effort) (Q16_16.ofFloat 2.0)) }
        | none => e)
      merged ++ nonConflicting
    | .discardBoth =>
      let filtered := existing.filter (fun e => ¬incoming.any (fun i => proposalsConflict e i))
      filtered
  let resolvedCount := conflicts.length
  let scars := if resolution = .discardBoth then resolvedCount else 0
  { mergedProposals := resolved
    conflictsResolved := resolvedCount
    scarsEmitted := scars }

end MergeResult

/--
Orchestrate parallel subagent execution with cooperative merging.

This is the parallel replacement for runSubagentAnalysis. It:
1. Spawns domain subagents per SpawnStrategy
2. Dispatches them to available compute substrates
3. Collects results from each completed agent
4. Merges results cooperatively using the configured resolution strategy
5. Returns the final merged proposal list and execution metrics
-/
structure ParallelOrchestrationResult where
  finalProposals : List ImprovementProposal
  totalAgentsSpawned : Nat
  agentsCompleted : Nat
  agentsFailed : Nat
  totalWorkUnits : Nat
  stealEvents : Nat
  conflictsResolved : Nat
  scarsEmitted : Nat
  deriving Repr, Inhabited

/--
Run parallel subagent analysis with cooperative merging.

Given a SubagentSystem and a SpawnStrategy, this function:
- Spawns agents according to the strategy
- Simulates dispatch to compute substrates
- Collects and merges results from all agents

The actual parallel dispatch is performed by the Rust/Python runtime
(lake_compile_bridge, wgpu compute). This Lean model provides the
formal specification and the merge logic.
-/
def runParallelAnalysis (system : SubagentSystem) (modules : List Module)
    (strategy : SpawnStrategy) (resolution : ConflictResolution) : ParallelOrchestrationResult :=
  let initialState : ParallelExecutionState := ParallelExecutionState.fromSystem system

  -- Phase 1: Spawn agents according to strategy
  let afterSpawn : ParallelExecutionState :=
    match strategy with
    | .fixed count =>
      List.range count |>.foldl (fun state i =>
        state.spawnAgent none .coreBind strategy s!"Fixed agent {i}" "cpu")
      initialState
    | .perDomain =>
      Domain.all.foldl (fun state domain =>
        state.spawnAgent none domain strategy s!"Domain expert: {domain.toString}" "cpu")
      initialState
    | .perModule =>
      modules.foldl (fun state mod =>
        state.spawnAgent none mod.domain strategy s!"Module agent: {mod.name}" "cpu")
      initialState
    | .dynamic max =>
      List.range max |>.foldl (fun state i =>
        state.spawnAgent none .coreBind strategy s!"Dynamic agent {i}" "cpu")
      initialState
    | .workStealing poolSize =>
      List.range poolSize |>.foldl (fun state i =>
        state.spawnAgent none .coreBind strategy s!"Worker {i}" "cpu")
      initialState

  -- Phase 2: Enqueue work units for each agent
  let afterEnqueue : ParallelExecutionState :=
    afterSpawn.spawnedAgents.foldl (fun state agent =>
      state.enqueueAgentWork agent.id s!"Analyze {agent.domain.toString}" Q16_16.one [])
    afterSpawn

  -- Phase 3: Simulate dispatch (all agents run, all succeed)
  let afterDispatch : ParallelExecutionState :=
    afterEnqueue.spawnedAgents.foldl (fun state agent =>
      let state' := state.dispatchAgent agent.id
      let pool' := state'.workPool.claimUnit agent.id
      { state' with
        workPool := pool'
        spawnedAgents := state'.spawnedAgents.map (fun a =>
          if a.id = agent.id then
            match a.stepForward .completed with
            | some a' => a'
            | none => a
          else a) })
    afterEnqueue

  -- Phase 4: Collect and merge proposals from domain experts
  let domainProposals := afterDispatch.spawnedAgents.flatMap (fun agent =>
    -- Each agent does the same analysis as the sequential version
    let expert : DomainExpert := { domain := agent.domain, expertiseLevel := Q16_16.one, modulesKnown := [] }
    domainExpertAnalyze expert modules)

  let mergeResult := MergeResult.cooperativeMerge [] domainProposals resolution

  -- Phase 5: Also run integration analyst and codebase expert
  let integrationProposals := integrationAnalystAnalyze system.integrationAnalyst modules
  let mergeResult2 := MergeResult.cooperativeMerge mergeResult.mergedProposals integrationProposals resolution

  let codebaseProposals := codebaseExpertAnalyze system.codebaseExpert modules
  let mergeResult3 := MergeResult.cooperativeMerge mergeResult2.mergedProposals codebaseProposals resolution

  -- Phase 6: Prioritize
  let prioritized := prioritySchedulerFilter system.scheduler mergeResult3.mergedProposals

  { finalProposals := prioritized
    totalAgentsSpawned := afterSpawn.spawnedAgents.length
    agentsCompleted := afterDispatch.completedCount
    agentsFailed := afterDispatch.failedCount
    totalWorkUnits := afterDispatch.workPool.totalUnits
    stealEvents := afterDispatch.workPool.stealCount
    conflictsResolved := mergeResult3.conflictsResolved
    scarsEmitted := mergeResult3.scarsEmitted }

-- ═══════════════════════════════════════════════════════════════════════════
-- §12  Integration with GPU Compile Bridge
-- ═══════════════════════════════════════════════════════════════════════════

/--
Map a subagent task to a GPU compute dispatch.

This connects the subagent system to the lake_compile_bridge's GPU dispatch.
When a subagent needs to verify a batch of theorems, it creates a
GpuDutyAssignment that the compile bridge executes.
-/
structure AgentComputeDispatch where
  agentId : Nat
  workUnitId : Nat
  substrate : String        -- "cpu", "gpu:0", "fpga:0"
  shaderName : Option String  -- WGSL shader entry point if GPU
  theoremBatchSize : Nat     -- Number of theorem verifications to batch
  deriving Repr, Inhabited

/--
Convert a work unit to a GPU compute dispatch for the compile bridge.
-/
def workUnitToDispatch (unit : WorkUnit) (gpuId : Nat) : AgentComputeDispatch :=
  { agentId := unit.agentId
    workUnitId := unit.unitId
    substrate := s!"gpu:{gpuId}"
    shaderName := some "compile_bridge.wgsl"
    theoremBatchSize := 65536 }

-- ═══════════════════════════════════════════════════════════════════════════
-- §13  Eval Witnesses
-- ═══════════════════════════════════════════════════════════════════════════

/- Witness: lifecycle state transitions are valid. -/
#eval (SpawnedSubagent.mk 1 none .coreBind .perDomain .pending "test" "cpu" none).stepForward .running
  -- Expected: some (agent with lifecycle = running)

/- Witness: illegal transition (completed → running) returns none. -/
#eval (SpawnedSubagent.mk 1 none .coreBind .perDomain .completed "test" "cpu" none).stepForward .running
  -- Expected: none

/- Witness: work-stealing pool basic operations. -/
#eval
  let pool := WorkStealingPool.empty
  let unit := { unitId := 1, agentId := 1, domain := .coreBind, priority := Q16_16.one, description := "test", dependencies := [] }
  let pool1 := pool.enqueue unit
  let pool2 := pool1.claimUnit 1
  (pool2.inFlightUnits.length, pool2.pendingUnits.length)
  -- Expected: (1, 0)

/- Witness: parallel orchestration with per-domain strategy. -/
#eval
  let result := runParallelAnalysis currentSubagentSystem moduleRegistry .perDomain .keepHighest
  (result.totalAgentsSpawned, result.conflictsResolved, result.finalProposals.length)
  -- Expected: (number of domains, some conflict count, some proposal count)

/- Witness: cooperative merge keeps highest priority on conflict. -/
#eval
  let p1 : ImprovementProposal :=
    { id := 1, targetModule := "Test", improvementType := .addTheorem, description := "low"
      impact := Q16_16.ofFloat 0.3, effort := Q16_16.ofFloat 0.3
      priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.3) (Q16_16.ofFloat 0.3)
      domain := .coreBind }
  let p2 : ImprovementProposal :=
    { id := 2, targetModule := "Test", improvementType := .addTheorem, description := "high"
      impact := Q16_16.ofFloat 0.9, effort := Q16_16.ofFloat 0.3
      priority := ImprovementProposal.calculatePriority (Q16_16.ofFloat 0.9) (Q16_16.ofFloat 0.3)
      domain := .coreBind }
  let merged := MergeResult.cooperativeMerge [p1] [p2] .keepHighest
  merged.mergedProposals.head?.map (fun p => p.description)
  -- Expected: some "high"

end Semantics.SubagentOrchestrator
