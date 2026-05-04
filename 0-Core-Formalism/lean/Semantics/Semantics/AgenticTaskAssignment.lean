import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic
import Semantics.FixedPoint
import AgenticCore
import AgenticOrchestrationField

namespace Semantics.AgenticOrchestration

open Semantics.Q16_16

/-! # Agentic Task Assignment
Task assignment and orchestration algorithm.
Split from AgenticOrchestration.lean per swarm suggestion (USER AUTHORIZED).
-/

/-- Assign task to best available agent using field-weighted selection. -/
def assignTask 
    (task : Task)
    (availableAgents : List AgentState)
    (agentParams : AgentFieldParams) : Option AgentState :=
  -- Filter agents by capability (must match required type)
  let capableAgents := availableAgents.filter (fun a =>
    a.agentType = task.requiredType && a.status = AgentStatus.idle
  )
  
  if capableAgents.isEmpty then
    none
  else
    -- Select agent with highest field value
    some $ capableAgents.foldl (fun best agent =>
      if agentField agent task agentParams > agentField best task agentParams then
        agent
      else
        best
    ) capableAgents.head!

/-- Check if all dependencies are satisfied. -/
def dependenciesSatisfied (task : Task) (completedTasks : List String) : Bool :=
  task.dependencies.all (fun dep => completedTasks.contains dep)

/-- Get ready tasks (dependencies satisfied, not yet assigned). -/
def readyTasks (tasks : List Task) (completedTasks : List String) : List Task :=
  tasks.filter (fun t => 
    dependenciesSatisfied t completedTasks && !completedTasks.contains t.id
  )

/-- Execute one step of orchestration. Returns updated agent states. -/
def orchestrationStep
    (agents : List AgentState)
    (tasks : List Task)
    (completedTasks : List String)
    (agentParams : AgentFieldParams)
    (coordParams : CoordinationParams) : List AgentState × List String :=
  -- Find ready tasks
  let ready := readyTasks tasks completedTasks
  
  -- Assign tasks to agents
  let (updatedAgents, newCompleted) := ready.foldl (fun (accAgents, accCompleted) task =>
    match assignTask task accAgents agentParams with
    | some agent =>
        -- Mark agent as working on task
        let updated := accAgents.map (fun a =>
          if a.id = agent.id then
            { a with 
              status := AgentStatus.working
              currentTask := some task.id
              load := a.load + ofNat 19660 }  -- 0.3 in Q16.16
          else a
        )
        (updated, accCompleted)
    | none =>
        -- No available agent, skip
        (accAgents, accCompleted)
  ) (agents, completedTasks)
  
  -- Simulate task completion (in real system, check actual status)
  let finalAgents := updatedAgents.map (fun a =>
    if a.status = AgentStatus.working && a.load >= ofNat 58982 then  -- 0.9 in Q16.16
      { a with
        status := AgentStatus.completed
        currentTask := none
        completedTasks := a.currentTask.toList ++ a.completedTasks
        load := zero
        outputBuffer := a.outputBuffer ++ a.currentTask.toList }
    else if a.status = AgentStatus.working then
      { a with load := a.load + ofNat 6553 }  -- 0.1 in Q16.16
    else
      a
  )
  
  let finalCompleted := finalAgents.foldl (fun acc a =>
    acc ++ a.completedTasks
  ) []
  
  (finalAgents, finalCompleted)

/-- Run full orchestration until all tasks complete. -/
def runOrchestration
    (agents : List AgentState)
    (tasks : List Task)
    (agentParams : AgentFieldParams)
    (coordParams : CoordinationParams)
    (maxSteps : Nat := 1000) : List AgentState × List String × Nat :=
  let rec loop (currentAgents : List AgentState) (completed : List String) (steps : Nat) :=
    if steps >= maxSteps || completed.length = tasks.length then
      (currentAgents, completed, steps)
    else
      let (newAgents, newCompleted) := orchestrationStep 
        currentAgents tasks completed agentParams coordParams
      loop newAgents newCompleted (steps + 1)
  
  loop agents [] 0

end Semantics.AgenticOrchestration
