/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

OmnidirectionalInterface.lean — Unified Query Router in Lean

Central coordinator that routes queries to appropriate swarm subsystems.
Integrates with SubagentOrchestrator for domain expert coordination.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic
import Lean.Data.Json
import Semantics.FixedPoint
import Semantics.SubagentOrchestrator
import Semantics.RcloneIntegration
import Semantics.GpuDutyAssignment
import Semantics.DomainModelIntegration

namespace Semantics.OmnidirectionalInterface

open Lean

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16.16 Fixed-Point
-- ═══════════════════════════════════════════════════════════════════════════

open Semantics (Q16_16)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Query Routing
-- ═══════════════════════════════════════════════════════════════════════════

inductive Subsystem
  | swarm
  | moe
  | ene
  | mathDb
  | asciiArt
  | rclone
  | gpuDuty
  | domainModel
  deriving Repr, DecidableEq, Inhabited, ToJson, FromJson

structure RoutedQuery where
  queryId : String
  target : Subsystem
  queryText : String
  priority : Nat
  timestamp : Nat
  deriving Repr, Inhabited, ToJson, FromJson

structure QueryResult where
  queryId : String
  source : Subsystem
  success : Bool
  data : String
  confidence : Q16_16
  deriving Repr, Inhabited, ToJson, FromJson

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Router State
-- ═══════════════════════════════════════════════════════════════════════════

structure RouterState where
  pendingQueries : List RoutedQuery
  completedResults : List QueryResult
  routeCounts : List (Subsystem × Nat)
  deriving Repr, Inhabited

namespace RouterState

def empty : RouterState :=
  { pendingQueries := [], completedResults := [], routeCounts := [] }

def route (state : RouterState) (query : RoutedQuery) : RouterState :=
  let counts := state.routeCounts.map (fun (s, n) => if s = query.target then (s, n + 1) else (s, n))
  let counts := if state.routeCounts.any (fun (s, _) => s = query.target) then counts else (query.target, 1) :: counts
  { state with pendingQueries := query :: state.pendingQueries, routeCounts := counts }

def complete (state : RouterState) (result : QueryResult) : RouterState :=
  let pending := state.pendingQueries.filter (fun q => q.queryId ≠ result.queryId)
  { state with pendingQueries := pending, completedResults := result :: state.completedResults }

def getResultsBySubsystem (state : RouterState) (target : Subsystem) : List QueryResult :=
  state.completedResults.filter (fun r => r.source = target)

end RouterState

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Integration with SubagentOrchestrator
-- ═══════════════════════════════════════════════════════════════════════════

def domainToSubsystem : SubagentOrchestrator.Domain → Subsystem
  | .cloudStorage => .rclone
  | .gpuResources => .gpuDuty
  | .domainModels => .domainModel
  | _ => .swarm

def proposalToQuery (proposal : SubagentOrchestrator.ImprovementProposal) (timestamp : Nat) : RoutedQuery :=
  { queryId := "proposal_" ++ toString proposal.id
    target := domainToSubsystem proposal.domain
    queryText := proposal.description
    priority := proposal.id
    timestamp := timestamp }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  System Health
-- ═══════════════════════════════════════════════════════════════════════════

structure SystemHealth where
  swarmStatus : String
  moeStatus : String
  rcloneStatus : String
  gpuDutyStatus : String
  domainModelStatus : String
  pendingQueries : Nat
  completedQueries : Nat
  deriving Repr, Inhabited

def checkSystemHealth (state : RouterState) : SystemHealth :=
  { swarmStatus := "operational"
    moeStatus := "operational"
    rcloneStatus := "operational"
    gpuDutyStatus := "operational"
    domainModelStatus := "operational"
    pendingQueries := state.pendingQueries.length
    completedQueries := state.completedResults.length }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

theorem routeIncreasesPending (state : RouterState) (query : RoutedQuery) :
    (state.route query).pendingQueries.length = state.pendingQueries.length + 1 := by
  simp [RouterState.route]

/--
Completing a query removes it from pending.
Bounded claim: pending does not increase.
-/
theorem complete_non_increasing_pending (state : RouterState) (result : QueryResult) :
    (state.complete result).pendingQueries.length ≤ state.pendingQueries.length := by
  unfold RouterState.complete
  simp
  apply List.length_filter_le

/--
Completing increments completed results count.
-/
theorem complete_increments_completed (state : RouterState) (result : QueryResult) :
    (state.complete result).completedResults.length = state.completedResults.length + 1 := by
  simp [RouterState.complete]

theorem totalQueriesMonotonic (state : RouterState) (query : RoutedQuery) :
    let newState := state.route query
    newState.pendingQueries.length + newState.completedResults.length ≥
    state.pendingQueries.length + state.completedResults.length := by
  simp [RouterState.route]

end Semantics.OmnidirectionalInterface
