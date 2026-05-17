/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SwarmQueryAPI.lean — Native Lean Swarm Query Interface

Replaces tools/swarm_api.py (FastAPI/Python) with a pure Lean implementation
that routes through the OmnidirectionalInterface + SubagentOrchestrator.

Architecture:
  SwarmQueryRequest
      │
      ▼
  SwarmQueryAPI.handle
      │
      ▼
  OmnidirectionalInterface.RouterState.route (into target Subsystem)
      │
      ▼
  SubagentOrchestrator domain expert
      │
      ▼
  QueryResult → SwarmQueryResponse

Per AGENTS.md:
  - Q16_16 fixed-point for scoring (§1.4)
  - PascalCase types, camelCase functions (§2)
  - Theorems for correctness (§4)
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic
import Lean.Data.Json
import Semantics.FixedPoint
import Semantics.SubagentOrchestrator
import Semantics.OmnidirectionalInterface

namespace Semantics.SwarmQueryAPI

open Lean Semantics
open Semantics.SubagentOrchestrator (Domain)
open Semantics.OmnidirectionalInterface (Subsystem RoutedQuery QueryResult RouterState)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Typed query model (replaces Pydantic SwarmQueryRequest)
-- ═══════════════════════════════════════════════════════════════════════════

structure QueryLimit where
  value : Nat
  deriving Repr, DecidableEq, Inhabited, ToJson, FromJson

def QueryLimit.mk? (n : Nat) : QueryLimit :=
  if n ≤ 1000 then ⟨n⟩ else ⟨1000⟩

inductive FormalStatus
  | proven
  | stated
  | conjectured
  | unknown
  deriving Repr, DecidableEq, Inhabited, ToJson, FromJson

structure SwarmQueryRequest where
  subjects : List String
  keywords : List String
  formalStatus : Option FormalStatus
  requireLeanFormalization : Bool
  limit : QueryLimit
  includeMetadata : Bool
  deriving Repr, Inhabited, ToJson, FromJson

def SwarmQueryRequest.empty : SwarmQueryRequest :=
  { subjects := []
    keywords := []
    formalStatus := none
    requireLeanFormalization := false
    limit := QueryLimit.mk? 20
    includeMetadata := false }

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Typed response (replaces SwarmQueryResponse)
-- ═══════════════════════════════════════════════════════════════════════════

structure EntityRecord where
  entityId : String
  subject : String
  name : String
  statement : String
  formalStatus : FormalStatus
  hasLeanModule : Bool
  deriving Repr, Inhabited, ToJson, FromJson

structure SwarmStats where
  agentCount : Nat
  activeQueries : Nat
  systemConfidence : Q16_16
  networkMode : Bool
  deriving Repr, Inhabited, ToJson, FromJson

def getStats : SwarmStats :=
  let agents := Semantics.SubagentOrchestrator.Domain.all
  { agentCount := agents.length
    activeQueries := 0
    systemConfidence := Q16_16.one
    networkMode := true }

structure SwarmQueryResponse where
  success : Bool
  results : List EntityRecord
  count : Nat
  confidence : Q16_16
  suggestions : List String
  routedTo : Subsystem
  deriving Repr, Inhabited, ToJson, FromJson

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Request → RoutedQuery translation
-- ═══════════════════════════════════════════════════════════════════════════

def chooseSubsystem (req : SwarmQueryRequest) : Subsystem :=
  let subjectsLower := req.subjects.map String.toLower
  if subjectsLower.any (· == "gpu") then Subsystem.gpuDuty
  else if subjectsLower.any (· == "rclone") then Subsystem.rclone
  else if subjectsLower.any (· == "domain-model") then Subsystem.domainModel
  else if req.requireLeanFormalization then Subsystem.mathDb
  else Subsystem.swarm

def serializeQuery (req : SwarmQueryRequest) : String :=
  let subs := String.intercalate "," req.subjects
  let kws := String.intercalate " " req.keywords
  let fs := match req.formalStatus with
    | some .proven => "proven"
    | some .stated => "stated"
    | some .conjectured => "conjectured"
    | some .unknown => "unknown"
    | none => "any"
  s!"subjects={subs}|keywords={kws}|formalStatus={fs}|requireLean={req.requireLeanFormalization}"

def toRoutedQuery (req : SwarmQueryRequest) (queryId : String) (timestamp : Nat) : RoutedQuery :=
  { queryId := queryId
    target := chooseSubsystem req
    queryText := serializeQuery req
    priority := req.limit.value
    timestamp := timestamp }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Confidence scoring
-- ═══════════════════════════════════════════════════════════════════════════

def confidenceFromResults (resultCount : Nat) (limit : QueryLimit) : Q16_16 :=
  if limit.value = 0 then Q16_16.zero
  else if resultCount ≥ limit.value then Q16_16.one
  else Q16_16.div (Q16_16.ofNat resultCount) (Q16_16.ofNat limit.value)

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Suggestion generator
-- ═══════════════════════════════════════════════════════════════════════════

def generateSuggestions (req : SwarmQueryRequest) (results : List EntityRecord) : List String :=
  let empty : List String := []
  let s1 := if results.isEmpty then
    "Try broadening your search terms or using different keywords." :: empty
  else
    "Review the formal status of these entities for Lean 4 implementation." :: empty
  let s2 := if req.subjects.isEmpty then s1
    else ("Consider exploring related subjects: " ++ String.intercalate ", " req.subjects) :: s1
  let s3 := if req.requireLeanFormalization then
    "Results restricted to Lean-formalized entities." :: s2
  else s2
  s3

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Result filtering
-- ═══════════════════════════════════════════════════════════════════════════

def applyFilters (req : SwarmQueryRequest) (records : List EntityRecord) : List EntityRecord :=
  records.filter fun r =>
    let subjectMatch := req.subjects.isEmpty ||
      req.subjects.any (fun s : String => decide ((r.subject.toLower.splitOn s.toLower).length > 1))
    let statusMatch := match req.formalStatus with
      | some fs => r.formalStatus = fs
      | none => true
    let leanMatch := !req.requireLeanFormalization || r.hasLeanModule
    subjectMatch && statusMatch && leanMatch

def applyLimit (req : SwarmQueryRequest) (records : List EntityRecord) : List EntityRecord :=
  records.take req.limit.value

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Top-level handler
-- ═══════════════════════════════════════════════════════════════════════════

def handle (req : SwarmQueryRequest) (rawRecords : List EntityRecord) : SwarmQueryResponse :=
  let filtered := applyFilters req rawRecords
  let limited := applyLimit req filtered
  { success := true
    results := limited
    count := limited.length
    confidence := confidenceFromResults limited.length req.limit
    suggestions := generateSuggestions req limited
    routedTo := chooseSubsystem req }

def runViaOrchestrator
    (state : RouterState) (req : SwarmQueryRequest)
    (queryId : String) (timestamp : Nat)
    (rawRecords : List EntityRecord) :
    RouterState × SwarmQueryResponse :=
  let rq := toRoutedQuery req queryId timestamp
  let routed := state.route rq
  let response := handle req rawRecords
  let result : QueryResult :=
    { queryId := queryId
      source := rq.target
      success := response.success
      data := s!"count={response.count}"
      confidence := response.confidence }
  let completed := routed.complete result
  (completed, response)

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/--
handle respects the request limit: the result count is bounded
by the limit value after applying both filters and limit.
-/
theorem handle_respects_limit (req : SwarmQueryRequest) (rawRecords : List EntityRecord) :
    (handle req rawRecords).count ≤ req.limit.value := by
  unfold handle applyLimit
  simp

/--
handle does not invent records: every result in the output
appears in the filtered version of the input records.
-/
theorem handle_subset_of_filtered (req : SwarmQueryRequest) (rawRecords : List EntityRecord) :
    (handle req rawRecords).results ⊆ applyFilters req rawRecords := by
  unfold handle applyLimit
  exact List.take_subset _ _

/--
When requireLeanFormalization is true and the subjects don't name
a specific subsystem, the query routes to mathDb.
-/
theorem lean_query_routes_to_mathdb (req : SwarmQueryRequest)
    (hLean : req.requireLeanFormalization)
    (hNoGpu : (req.subjects.map String.toLower).any (· == "gpu") = false)
    (hNoRclone : (req.subjects.map String.toLower).any (· == "rclone") = false)
    (hNoDomain : (req.subjects.map String.toLower).any (· == "domain-model") = false) :
    chooseSubsystem req = Subsystem.mathDb := by
  unfold chooseSubsystem
  simp [hLean, hNoGpu, hNoRclone, hNoDomain]

end Semantics.SwarmQueryAPI
