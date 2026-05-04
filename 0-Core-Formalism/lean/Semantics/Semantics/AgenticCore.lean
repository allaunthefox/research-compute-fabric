import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic
import Semantics.FixedPoint
import Semantics.TopologicalAwareness

namespace Semantics.AgenticOrchestration

open Semantics.Q16_16

/-! # Agentic Core Structures
Core agent types, states, and tasks for orchestration.
Split from AgenticOrchestration.lean per swarm suggestion (USER AUTHORIZED).
-/

/-- Agent specializations. -/
inductive AgentType
  | searchAgent      -- Literature discovery
  | extractAgent     -- Concept extraction
  | formalizeAgent   -- Lean 4 formalization
  | validateAgent    -- Empirical validation
  | synthesizeAgent  -- Report synthesis
  | metaAgent        -- Orchestrates other agents
  | builderAgent     -- Builder (Architect): ADD clock, proposes forward progress, builds state
  | wardenAgent      -- Warden: SUBTRACT clock, reverses to check, validates proofs
  | judgeAgent       -- Judge (HeatSink): PAUSE clock, holds state, adjudicates
  deriving Repr, DecidableEq, Inhabited

namespace AgentType

/-- Human-readable names. -/
def name : AgentType → String
  | searchAgent => "SearchAgent"
  | extractAgent => "ExtractAgent"
  | formalizeAgent => "FormalizeAgent"
  | validateAgent => "ValidateAgent"
  | synthesizeAgent => "SynthesizeAgent"
  | metaAgent => "MetaAgent"
  | builderAgent => "BuilderAgent"
  | wardenAgent => "WardenAgent"
  | judgeAgent => "JudgeAgent"

/-- Capabilities per agent type. -/
def capabilities : AgentType → List String
  | searchAgent => ["query_scholar", "fetch_pdf", "parse_bibliography", "lut_lookup"]
  | extractAgent => ["read_pdf", "identify_theorems", "extract_definitions", "lut_query"]
  | formalizeAgent => ["write_lean", "prove_lemmas", "integrate_module", "lut_validate"]
  | validateAgent => ["run_benchmarks", "collect_metrics", "compare_baselines", "lut_verify"]
  | synthesizeAgent => ["compile_report", "generate_plots", "write_paper", "lut_synthesize"]
  | metaAgent => ["delegate_task", "monitor_progress", "resolve_conflicts", "lut_coordinate"]
  | builderAgent => ["propose_change", "build_state", "manifold_update", "clock_add", "lut_build"]
  | wardenAgent => ["validate_proof", "reverse_check", "stark_trace", "clock_subtract", "lut_warden"]
  | judgeAgent => ["adjudicate", "hold_state", "energy_guard", "clock_pause", "lut_judge"]

end AgentType

/-- Agent state in the orchestration. -/
structure AgentState where
  id : String
  agentType : AgentType
  currentTask : Option String
  completedTasks : List String
  outputBuffer : List String  -- Results ready for other agents
  load : Q16_16  -- Changed from Float to Q16_16 for hardware-native computation (0.0-1.0 range)
  status : AgentStatus
  primitiveLUT : Option Semantics.TopologicalAwareness.PrimitiveLUT  -- Access to geometric primitives LUT
  deriving Repr, Inhabited

/-- Agent status. -/
inductive AgentStatus
  | idle
  | working
  | waiting  -- Blocked on dependency
  | completed
  | failed
  deriving Repr, DecidableEq, Inhabited

/-- Task with dependencies. -/
structure Task where
  id : String
  description : String
  requiredType : AgentType  -- Which agent type can execute
  dependencies : List String  -- Task IDs that must complete first
  estimatedDuration : Q16_16  -- Minutes (Q16.16 fixed-point)
  priority : Nat  -- 1 (high) to 5 (low)
  deriving Repr, Inhabited

/-- Research pipeline as task graph. -/
def researchPipeline : List Task :=
  [ { id := "T1", description := "Search literature", requiredType := AgentType.searchAgent
      dependencies := [], estimatedDuration := ofNat 655360, priority := 1 }  -- 10.0 minutes in Q16.16
  , { id := "T2", description := "Extract concepts", requiredType := AgentType.extractAgent
      dependencies := ["T1"], estimatedDuration := ofNat 1310720, priority := 1 }  -- 20.0 minutes in Q16.16
  , { id := "T3", description := "Generate hypotheses", requiredType := AgentType.extractAgent
      dependencies := ["T2"], estimatedDuration := ofNat 983040, priority := 2 }  -- 15.0 minutes in Q16.16
  , { id := "T4", description := "Formalize in Lean", requiredType := AgentType.formalizeAgent
      dependencies := ["T3"], estimatedDuration := ofNat 3932160, priority := 1 }  -- 60.0 minutes in Q16.16
  , { id := "T5", description := "Design experiments", requiredType := AgentType.validateAgent
      dependencies := ["T3"], estimatedDuration := ofNat 1966080, priority := 2 }  -- 30.0 minutes in Q16.16
  , { id := "T6", description := "Run benchmarks", requiredType := AgentType.validateAgent
      dependencies := ["T4", "T5"], estimatedDuration := ofNat 7864320, priority := 1 }  -- 120.0 minutes in Q16.16
  , { id := "T7", description := "Synthesize report", requiredType := AgentType.synthesizeAgent
      dependencies := ["T6"], estimatedDuration := ofNat 2949120, priority := 1 }  -- 45.0 minutes in Q16.16
  ]

end Semantics.AgenticOrchestration
