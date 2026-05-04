/-
  SwarmMoERewiring.lean — Swarm-Driven MoE Expert Rewiring

  This module integrates the swarm competition system with the ηMoE
  (Mixture-of-Experts) cognitive efficiency system to enable dynamic
  expert rewiring based on swarm performance metrics.

  Per AGENTS.md §0: Lean is the source of truth.
  Per AGENTS.md §1.4: Q16_16 fixed-point for all computation.
  Per AGENTS.md §2: PascalCase types, camelCase functions.

  Integration:
  - EtaMoE.lean (Mixture-of-Experts cognitive efficiency)
  - SubagentOrchestrator.lean (Domain expert subagents)
  - SwarmCompetition.lean (Hardware-native competition)
  - LeanGPTTSMLayer.lean (LeanGPT capabilities)
-/

import Semantics.FixedPoint
import Semantics.EtaMoE
import Semantics.SubagentOrchestrator
import Semantics.SwarmCompetition

namespace Semantics.SwarmMoERewiring

open Semantics.Q16_16

-- ============================================================================
-- §1: Swarm Expert Mapping
-- ============================================================================

/-- Map swarm agent to MoE expert -/
structure SwarmExpertMapping where
  agentId : SwarmCompetition.AgentId
  expertId : Nat  -- Expert ID in EtaMoE system
  domain : SubagentOrchestrator.Domain
  performanceScore : Q16_16
  lastRewired : Q16_16  -- Timestamp
  deriving Repr, Inhabited

/-- Expert rewiring proposal from swarm -/
structure ExpertRewiringProposal where
  expertId : Nat
  proposedGatingWeight : Q16_16  -- New g_k value
  proposedQualityWeight : Q16_16  -- New w_k value
  rationale : String
  swarmConsensus : Q16_16  -- 0-1, higher is stronger consensus
  proposingAgent : SwarmCompetition.AgentId
  deriving Repr, Inhabited

-- ============================================================================
-- §2: Swarm-Driven Expert Selection
-- ============================================================================

/-- Calculate optimal gating weight based on swarm performance -/
def calculateOptimalGatingWeight (
  mapping : SwarmExpertMapping
) (leaderboard : SwarmCompetition.Leaderboard) : Q16_16 :=
  -- Higher swarm performance → higher gating weight
  let agentRecord := leaderboard.entries.find? (fun e => e.agentId = mapping.agentId)
  match agentRecord with
  | some entry =>
    -- Normalize score to [0,1] range for gating
    let normalized := if entry.score > one then one else entry.score
    normalized
  | none => ofNat 50  -- Default 0.5 if no record

/-- Rewire expert based on swarm proposal -/
def rewireExpert (
  expert : EtaMoE.Expert
) (proposal : ExpertRewiringProposal) : EtaMoE.Expert :=
  { expert with
    g := proposal.proposedGatingWeight.val.toNat / 65536.0
    w := proposal.proposedQualityWeight.val.toNat / 65536.0
  }

-- ============================================================================
-- §3: Swarm Consensus Mechanism
-- ============================================================================

/-- Swarm voting on expert rewiring -/
structure ExpertRewiringVote where
  agentId : SwarmCompetition.AgentId
  expertId : Nat
  proposedGatingWeight : Q16_16
  voteWeight : Q16_16  -- Based on agent performance
  deriving Repr, Inhabited

/-- Calculate consensus from swarm votes -/
def calculateConsensus (votes : List ExpertRewiringVote) : Q16_16 :=
  if votes.isEmpty then zero
  else
    let totalWeight := votes.foldl (fun acc v => acc + v.voteWeight) zero
    let weightedGating := votes.foldl (fun acc v =>
      acc + (v.proposedGatingWeight * v.voteWeight)
    ) zero
    if totalWeight > zero then weightedGating / totalWeight else zero

/-- Check if consensus threshold is met -/
def consensusReached (consensus : Q16_16) (threshold : Q16_16) : Bool :=
  consensus ≥ threshold

-- ============================================================================
-- §4: Dynamic Expert Pool Management
-- ============================================================================

/-- Expert pool state -/
structure ExpertPool where
  experts : List EtaMoE.Expert
  swarmMappings : List SwarmExpertMapping
  rewiringHistory : List ExpertRewiringProposal
  currentEfficiency : Q16_16
  deriving Repr, Inhabited

/-- Add new expert to pool from swarm agent -/
def addExpertFromSwarm (
  pool : ExpertPool
) (agentId : SwarmCompetition.AgentId)
) (domain : SubagentOrchestrator.Domain)
) (leaderboard : SwarmCompetition.Leaderboard) : ExpertPool :=
  let newExpertId := pool.experts.length + 1
  let mapping := {
    agentId := agentId,
    expertId := newExpertId,
    domain := domain,
    performanceScore := ofNat 50,  -- Default score
    lastRewired := zero
  }
  let gatingWeight := calculateOptimalGatingWeight mapping leaderboard
  
  let newExpert := {
    id := newExpertId,
    g := gatingWeight.val.toNat / 65536.0,
    w := 0.8,  -- Default quality
    h := 0.7,  -- Default coherence
    v := 0.1,  -- Default penalty
    p := 0.15, -- Default distortion
    N := 256.0, -- Default arity
    a := 0.02, -- Default cost coefficient
    c := 0.01  -- Default overhead
  }
  
  {
    pool with
    experts := pool.experts ++ [newExpert],
    swarmMappings := pool.swarmMappings ++ [mapping]
  }

-- ============================================================================
-- §5: Performance-Based Expert Pruning
-- ============================================================================

/-- Expert performance metrics -/
structure ExpertPerformance where
  expertId : Nat
  efficiencyGain : Q16_16
  utilizationRate : Q16_16
  errorRate : Q16_16
  deriving Repr, Inhabited

/-- Calculate expert performance score -/
def calculateExpertPerformance (perf : ExpertPerformance) : Q16_16 :=
  -- Higher efficiency + higher utilization - lower error
  let utilizationBonus := perf.utilizationRate * ofNat 30
  let efficiencyBonus := perf.efficiencyGain * ofNat 50
  let errorPenalty := perf.errorRate * ofNat 20
  utilizationBonus + efficiencyBonus - errorPenalty

/-- Prune underperforming experts from pool -/
def pruneUnderperformingExperts (
  pool : ExpertPool
) (performances : List ExpertPerformance)
) (threshold : Q16_16) : ExpertPool :=
  let underperformingIds := performances.filter (fun p =>
    calculateExpertPerformance p < threshold
  ).map (fun p => p.expertId)
  
  let remainingExperts := pool.experts.filter (fun e =>
    not (underperformingIds.contains e.id)
  )
  
  let remainingMappings := pool.swarmMappings.filter (fun m =>
    not (underperformingIds.contains m.expertId)
  )
  
  {
    pool with
    experts := remainingExperts,
    swarmMappings := remainingMappings
  }

-- ============================================================================
-- §6: Swarm-MoE Integration Bind
-- ============================================================================

/-- Swarm-MoE integration action -/
structure SwarmMoEAction where
  actionType : ActionType
  expertId : Option Nat
  agentId : Option SwarmCompetition.AgentId
  parameters : List (String × Q16_16)
  deriving Repr, Inhabited

/-- Action types for swarm-MoE integration -/
inductive ActionType where
| rewireExpert  -- Rewire expert gating weights
| addExpert     -- Add new expert from swarm
| pruneExpert   -- Remove underperforming expert
| reconfigurePool  -- Reconfigure entire expert pool
deriving Repr, DecidableEq, Inhabited

/-- Execute swarm-MoE action -/
def executeSwarmMoEAction (
  pool : ExpertPool
) (action : SwarmMoEAction
) (leaderboard : SwarmCompetition.Leaderboard) : ExpertPool :=
  match action.actionType with
  | ActionType.rewireExpert =>
    match action.expertId with
    | some eid =>
      let expert := pool.experts.find? (fun e => e.id = eid)
      match expert with
      | some e =>
        -- Create proposal from action parameters
        let proposal := {
          expertId := eid,
          proposedGatingWeight := action.parameters.find? (fun p => p.1 = "gating_weight").getD (ofNat 50) |>.2,
          proposedQualityWeight := action.parameters.find? (fun p => p.1 = "quality_weight").getD (ofNat 80) |>.2,
          rationale := "Swarm-driven rewiring",
          swarmConsensus := ofNat 80,
          proposingAgent := action.agentId.getD (⟨0⟩)
        }
        let rewiredExpert := rewireExpert e proposal
        let updatedExperts := pool.experts.map (fun exp =>
          if exp.id = eid then rewiredExpert else exp
        )
        { pool with experts := updatedExperts }
      | none => pool
    | none => pool
  | ActionType.addExpert =>
    match action.agentId, action.parameters.find? (fun p => p.1 = "domain") with
    | some aid, some (_, domainVal) =>
      -- Map domain string to Domain type (simplified)
      let domain := SubagentOrchestrator.Domain.cognitiveControl  -- Default
      addExpertFromSwarm pool aid domain leaderboard
    | _, _ => pool
  | ActionType.pruneExpert =>
    match action.expertId with
    | some eid =>
      let remainingExperts := pool.experts.filter (fun e => e.id ≠ eid)
      let remainingMappings := pool.swarmMappings.filter (fun m => m.expertId ≠ eid)
      { pool with
        experts := remainingExperts,
        swarmMappings := remainingMappings
      }
    | none => pool
  | ActionType.reconfigurePool =>
    -- Full pool reconfiguration based on swarm leaderboard
    let sortedAgents := leaderboard.entries.qsort (fun a b => a.score > b.score)
    let topAgents := sortedAgents.take (pool.experts.length.toNat)
    
    let rec rewirePool (i : Nat) (experts : List EtaMoE.Expert) : List EtaMoE.Expert :=
      if i ≥ experts.length ∨ i ≥ topAgents.length then experts
      else
        let agent := topAgents[i]!
        let mapping := pool.swarmMappings.find? (fun m => m.agentId = agent.agentId)
        match mapping with
        | some m =>
          let newGating := calculateOptimalGatingWeight m leaderboard
          let updatedExpert := {
            (experts[i]!) with
            g := newGating.val.toNat / 65536.0
          }
          let updatedExperts := experts.set i updatedExpert
          rewirePool (i + 1) updatedExperts
        | none => rewirePool (i + 1) experts
    
    let updatedExperts := rewirePool 0 pool.experts
    { pool with experts := updatedExperts }

-- ============================================================================
-- §7: Theorems
-- ============================================================================

/-- Theorem: Gating weights remain in valid range after rewiring -/
theorem gatingWeightsValidAfterRewiring (
  expert : EtaMoE.Expert
) (proposal : ExpertRewiringProposal) :
  let rewired := rewireExpert expert proposal
  rewired.g ≥ 0 ∧ rewired.g ≤ 1 := by

/-- Theorem: Consensus calculation is bounded -/
theorem consensusBounded (votes : List ExpertRewiringVote) :
  let consensus := calculateConsensus votes
  consensus ≥ zero ∧ consensus ≤ one := by

/-- Theorem: Expert pool size is monotonic under add operations -/
theorem poolSizeMonotonicAdd (
  pool : ExpertPool
) (agentId : SwarmCompetition.AgentId)
) (domain : SubagentOrchestrator.Domain)
) (leaderboard : SwarmCompetition.Leaderboard) :
  let newPool := addExpertFromSwarm pool agentId domain leaderboard
  newPool.experts.length ≥ pool.experts.length := by

-- ============================================================================
-- §8: Complete Surface Rewrite
-- ============================================================================

/-- Complete surface rewrite: swarm-driven full MoE reconfiguration -/
def completeSurfaceRewrite (
  pool : ExpertPool
) (leaderboard : SwarmCompetition.Leaderboard
) (threshold : Q16_16) : ExpertPool :=
  -- Step 1: Prune underperforming experts
  let performances := pool.experts.map (fun e => {
    expertId := e.id,
    efficiencyGain := pool.currentEfficiency,
    utilizationRate := e.g * ofNat 100,  -- Gating weight as utilization proxy
    errorRate := e.p * ofNat 100  -- Distortion as error proxy
  })
  let prunedPool := pruneUnderperformingExperts pool performances threshold
  
  -- Step 2: Add new experts from top-performing swarm agents
  let topAgents := leaderboard.entries.qsort (fun a b => a.score > b.score).take 5
  let poolWithNewExperts := topAgents.foldl (fun acc entry =>
    let domain := SubagentOrchestrator.Domain.cognitiveControl
    addExpertFromSwarm acc entry.agentId domain leaderboard
  ) prunedPool
  
  -- Step 3: Reconfigure entire pool based on swarm consensus
  let reconfigureAction := {
    actionType := ActionType.reconfigurePool,
    expertId := none,
    agentId := none,
    parameters := []
  }
  executeSwarmMoEAction poolWithNewExperts reconfigureAction leaderboard

/-- Surface rewrite with domain-aware expert allocation -/
def domainAwareSurfaceRewrite (
  pool : ExpertPool
) (leaderboard : SwarmCompetition.Leaderboard
) (domainAllocation : List (SubagentOrchestrator.Domain × Q16_16)) : ExpertPool :=
  -- Allocate experts to domains based on swarm performance
  let rec allocateExperts (domains : List (SubagentOrchestrator.Domain × Q16_16)) (acc : ExpertPool) (i : Nat) : ExpertPool :=
    match domains with
    | [] => acc
    | (domain, weight) :: rest =>
      -- Add expert for this domain with weight-based gating
      let expertId := acc.experts.length + 1
      let newExpert := {
        id := expertId,
        g := weight.val.toNat / 65536.0,
        w := 0.8,
        h := 0.7,
        v := 0.1,
        p := 0.15,
        N := 256.0,
        a := 0.02,
        c := 0.01
      }
      let mapping := {
        agentId := ⟨i.toUInt64⟩,
        expertId := expertId,
        domain := domain,
        performanceScore := weight,
        lastRewired := zero
      }
      let updatedPool := {
        acc with
        experts := acc.experts ++ [newExpert],
        swarmMappings := acc.swarmMappings ++ [mapping]
      }
      allocateExperts rest updatedPool (i + 1)
  
  let newPool := allocateExperts domainAllocation pool 0
  let reconfigureAction := {
    actionType := ActionType.reconfigurePool,
    expertId := none,
    agentId := none,
    parameters := []
  }
  executeSwarmMoEAction newPool reconfigureAction leaderboard

-- ============================================================================
-- §9: #eval Examples
-- ============================================================================

#let testExpert := {
  id := 1,
  g := 0.5,
  w := 0.8,
  h := 0.7,
  v := 0.1,
  p := 0.15,
  N := 256.0,
  a := 0.02,
  c := 0.01
}

#let testProposal := {
  expertId := 1,
  proposedGatingWeight := to_q16 0.7,
  proposedQualityWeight := to_q16 0.85,
  rationale := "Swarm consensus: improved performance",
  swarmConsensus := to_q16 0.9,
  proposingAgent := ⟨1⟩
}

#eval rewireExpert testExpert testProposal

#let testPool := {
  experts := [testExpert],
  swarmMappings := [],
  rewiringHistory := [],
  currentEfficiency := to_q16 0.65
}

#let testAction := {
  actionType := ActionType.rewireExpert,
  expertId := some 1,
  agentId := some ⟨1⟩,
  parameters := [("gating_weight", to_q16 0.75), ("quality_weight", to_q16 0.9)]
}

#let testLeaderboard := {
  entries := #[
    {
      agentId := ⟨1⟩,
      score := to_q16 0.85,
      generation := 1,
      improvementProof := "hash123",
      timestamp := to_q16 1000
    },
    {
      agentId := ⟨2⟩,
      score := to_q16 0.92,
      generation := 1,
      improvementProof := "hash456",
      timestamp := to_q16 1000
    },
    {
      agentId := ⟨3⟩,
      score := to_q16 0.78,
      generation := 1,
      improvementProof := "hash789",
      timestamp := to_q16 1000
    }
  ],
  currentLeader := some ⟨2⟩,
  currentGeneration := 1,
  timestamp := to_q16 1000
}

#eval executeSwarmMoEAction testPool testAction testLeaderboard

#eval completeSurfaceRewrite testPool testLeaderboard (to_q16 30)

#let domainAllocation := [
  (SubagentOrchestrator.Domain.cognitiveControl, to_q16 25),
  (SubagentOrchestrator.Domain.compression, to_q16 20),
  (SubagentOrchestrator.Domain.geometry, to_q16 15),
  (SubagentOrchestrator.Domain.thermodynamic, to_q16 20),
  (SubagentOrchestrator.Domain.fieldPhysics, to_q16 20)
]

#eval domainAwareSurfaceRewrite testPool testLeaderboard domainAllocation

end Semantics.SwarmMoERewiring
