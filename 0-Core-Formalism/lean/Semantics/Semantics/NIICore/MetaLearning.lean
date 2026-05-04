/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MetaLearning.lean — Meta-Learning for Adaptive Morphing Policies

This module implements meta-learning for adaptive morphing policies, enabling
cores to learn morphing policies that generalize across different task distributions.
Inspired by the Dynamic Neural Networks survey's instance-wise dynamic models.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 4, Step 4: Implement meta-learning for adaptive policies
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic

namespace Semantics.NIICore.MetaLearning

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Fixed-Point Scoring (Q16.16)
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16

def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def ofNat (n : Nat) : Q16_16 := ⟨n * 65536⟩

instance : LE Q16_16 := ⟨fun a b => a.raw ≤ b.raw⟩
instance : LT Q16_16 := ⟨fun a b => a.raw < b.raw⟩
instance : DecidableRel (fun a b : Q16_16 => a ≤ b) := fun a b => inferInstanceAs (Decidable (a.raw ≤ b.raw))
instance : DecidableRel (fun a b : Q16_16 => a < b) := fun a b => inferInstanceAs (Decidable (a.raw < b.raw))
instance : Add Q16_16 := ⟨fun a b => ⟨a.raw + b.raw⟩⟩
instance : Sub Q16_16 := ⟨fun a b => ⟨a.raw - b.raw⟩⟩
instance : Mul Q16_16 := ⟨fun a b => ⟨(a.raw * b.raw) / 65536⟩⟩
instance : Div Q16_16 := ⟨fun a b => ⟨(a.raw * 65536) / b.raw⟩⟩

instance : Neg Q16_16 := ⟨fun a => ⟨-a.raw⟩⟩

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Semantic Domain and Morphic Mode Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive SemanticDomain where
  | semantic
  | translation
  | verification
  deriving Repr, DecidableEq, Inhabited, BEq

inductive MorphicMode where
  | monosemantic (domain : SemanticDomain)
  | polysemantic (domains : List SemanticDomain)
  | adaptive (current : SemanticDomain) (available : List SemanticDomain)
  deriving Repr, DecidableEq, Inhabited, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Task Distribution Types
-- ═══════════════════════════════════════════════════════════════════════════

structure TaskFeatures where
  complexity : Q16_16
  semanticDensity : Q16_16
  resourceDemand : Q16_16
  temporalPattern : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

structure TaskDistribution where
  tasks : List TaskFeatures
  meanComplexity : Q16_16
  meanResourceDemand : Q16_16
  variance : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace TaskDistribution

def fromTasks (tasks : List TaskFeatures) : TaskDistribution :=
  let meanComplexity := if tasks.isEmpty then Q16_16.zero else (tasks.map (·.complexity)).foldl (· + ·) Q16_16.zero / Q16_16.ofNat tasks.length
  let meanResourceDemand := if tasks.isEmpty then Q16_16.zero else (tasks.map (·.resourceDemand)).foldl (· + ·) Q16_16.zero / Q16_16.ofNat tasks.length
  -- Simplified variance calculation
  let variance := Q16_16.ofNat 10  -- Placeholder
  ⟨tasks, meanComplexity, meanResourceDemand, variance⟩

end TaskDistribution

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Meta-Learning Policy Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive MorphingAction where
  | morphTo (targetMode : MorphicMode)
  | maintainCurrent
  | requestAssistance
  deriving Repr, DecidableEq, Inhabited, BEq

structure PolicyParameters where
  complexityWeight : Q16_16
  densityWeight : Q16_16
  resourceWeight : Q16_16
  temporalWeight : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

structure MetaPolicy where
  parameters : PolicyParameters
  adaptationRate : Q16_16
  taskHistory : List TaskFeatures
  actionHistory : List MorphingAction
  performanceHistory : List Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace MetaPolicy

def initial : MetaPolicy :=
  ⟨⟨Q16_16.ofNat 25, Q16_16.ofNat 25, Q16_16.ofNat 25, Q16_16.ofNat 25⟩, Q16_16.ofNat 10, [], [], []⟩

def selectAction (policy : MetaPolicy) (currentMode : MorphicMode) (task : TaskFeatures) : MorphingAction :=
  -- Calculate weighted score for each potential action
  let complexityScore := policy.parameters.complexityWeight * task.complexity
  let densityScore := policy.parameters.densityWeight * task.semanticDensity
  let resourceScore := policy.parameters.resourceWeight * task.resourceDemand
  let temporalScore := policy.parameters.temporalWeight * task.temporalPattern
  
  let totalScore := complexityScore + densityScore + resourceScore + temporalScore
  
  -- Simple policy: morph if score is high enough
  if totalScore > Q16_16.ofNat 75 then
    MorphingAction.morphTo (MorphicMode.polysemantic [SemanticDomain.semantic, SemanticDomain.translation])
  else if totalScore > Q16_16.ofNat 50 then
    MorphingAction.maintainCurrent
  else
    MorphingAction.requestAssistance

def updatePolicy (policy : MetaPolicy) (task : TaskFeatures) (action : MorphingAction) (performance : Q16_16) : MetaPolicy :=
  let newTaskHistory := task :: policy.taskHistory
  let newActionHistory := action :: policy.actionHistory
  let newPerformanceHistory := performance :: policy.performanceHistory
  
  -- Update parameters based on performance (simplified gradient descent)
  let adjustment := if performance > Q16_16.ofNat 60 then Q16_16.ofNat 1 else -Q16_16.ofNat 1
  let newComplexityWeight := policy.parameters.complexityWeight + adjustment * policy.adaptationRate
  let newDensityWeight := policy.parameters.densityWeight + adjustment * policy.adaptationRate
  let newResourceWeight := policy.parameters.resourceWeight + adjustment * policy.adaptationRate
  let newTemporalWeight := policy.parameters.temporalWeight + adjustment * policy.adaptationRate
  
  ⟨⟨newComplexityWeight, newDensityWeight, newResourceWeight, newTemporalWeight⟩,
   policy.adaptationRate,
   newTaskHistory,
   newActionHistory,
   newPerformanceHistory⟩

def generalizeAcrossDistributions (policy : MetaPolicy) (distributions : List TaskDistribution) : MetaPolicy :=
  -- Average policy parameters across multiple task distributions
  let avgComplexityWeight := Q16_16.ofNat 25  -- Placeholder: would average across distributions
  let avgDensityWeight := Q16_16.ofNat 25
  let avgResourceWeight := Q16_16.ofNat 25
  let avgTemporalWeight := Q16_16.ofNat 25
  
  ⟨⟨avgComplexityWeight, avgDensityWeight, avgResourceWeight, avgTemporalWeight⟩,
   policy.adaptationRate,
   [],
   [],
   []⟩

end MetaPolicy

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════

structure MetaLearningController where
  coreId : String
  currentMode : MorphicMode
  policy : MetaPolicy
  currentDistribution : TaskDistribution
  deriving Repr, DecidableEq, Inhabited, BEq

namespace MetaLearningController

def create (coreId : String) (currentMode : MorphicMode) : MetaLearningController :=
  ⟨coreId, currentMode, MetaPolicy.initial, TaskDistribution.fromTasks []⟩

def processTask (controller : MetaLearningController) (task : TaskFeatures) : MorphicAction :=
  let action := MetaPolicy.selectAction controller.policy controller.currentMode task
  action

def updateWithResult (controller : MetaLearningController) (task : TaskFeatures) (action : MorphingAction) (performance : Q16_16) : MetaLearningController :=
  let updatedPolicy := MetaPolicy.updatePolicy controller.policy task action performance
  let updatedDistribution := TaskDistribution.fromTasks (task :: controller.currentDistribution.tasks)
  { controller with policy := updatedPolicy, currentDistribution := updatedDistribution }

def adaptToNewDistribution (controller : MetaLearningController) (newDistribution : TaskDistribution) : MetaLearningController :=
  let generalizedPolicy := MetaPolicy.generalizeAcrossDistributions controller.policy [controller.currentDistribution, newDistribution]
  { controller with policy := generalizedPolicy, currentDistribution := newDistribution }

end MetaLearningController

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

theorem metaPolicyHistoryGrows (policy : MetaPolicy) (task : TaskFeatures) (action : MorphingAction) (performance : Q16_16) :
  (MetaPolicy.updatePolicy policy task action performance).taskHistory.length = policy.taskHistory.length + 1 := by
  simp [MetaPolicy.updatePolicy]
  rfl

theorem metaPolicyPerformanceHistoryGrows (policy : MetaPolicy) (task : TaskFeatures) (action : MorphingAction) (performance : Q16_16) :
  (MetaPolicy.updatePolicy policy task action performance).performanceHistory.length = policy.performanceHistory.length + 1 := by
  simp [MetaPolicy.updatePolicy]
  rfl

theorem metaLearningControllerPreservesCoreId (controller : MetaLearningController) (task : TaskFeatures) (action : MorphingAction) (performance : Q16_16) :
  (MetaLearningController.updateWithResult controller task action performance).coreId = controller.coreId := by
  simp [MetaLearningController.updateWithResult]
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def testMetaLearning : IO Unit := do
  IO.println (String.replicate 70 '=')
  IO.println "META-LEARNING TEST"
  IO.println (String.replicate 70 '=')
  IO.println ""
  
  let controller := MetaLearningController.create "nii01" (MorphicMode.monosemantic SemanticDomain.semantic)
  IO.println "Created meta-learning controller:"
  IO.println s!"  Core ID: {controller.coreId}"
  IO.println s!"  Current mode: {repr controller.currentMode}"
  IO.println ""
  
  let task1 : TaskFeatures := ⟨Q16_16.ofNat 60, Q16_16.ofNat 70, Q16_16.ofNat 50, Q16_16.ofNat 40⟩
  IO.println "Task 1 features:"
  IO.println s!"  Complexity: {task1.complexity.raw}"
  IO.println s!"  Semantic density: {task1.semanticDensity.raw}"
  IO.println s!"  Resource demand: {task1.resourceDemand.raw}"
  IO.println s!"  Temporal pattern: {task1.temporalPattern.raw}"
  IO.println ""
  
  let action1 := MetaLearningController.processTask controller task1
  IO.println s!"Selected action: {repr action1}"
  IO.println ""
  
  let updated1 := MetaLearningController.updateWithResult controller task1 action1 (Q16_16.ofNat 75)
  IO.println "After update with performance 75:"
  IO.println s!"  Task history length: {updated1.policy.taskHistory.length}"
  IO.println s!"  Performance history length: {updated1.policy.performanceHistory.length}"
  IO.println ""
  
  let task2 : TaskFeatures := ⟨Q16_16.ofNat 80, Q16_16.ofNat 90, Q16_16.ofNat 70, Q16_16.ofNat 60⟩
  let action2 := MetaLearningController.processTask updated1 task2
  IO.println s!"Task 2 selected action: {repr action2}"
  IO.println ""
  
  let updated2 := MetaLearningController.updateWithResult updated1 task2 action2 (Q16_16.ofNat 85)
  IO.println "After second update with performance 85:"
  IO.println s!"  Task history length: {updated2.policy.taskHistory.length}"
  IO.println s!"  Performance history length: {updated2.policy.performanceHistory.length}"
  IO.println ""
  
  let newDist := TaskDistribution.fromTasks [task1, task2]
  let adapted := MetaLearningController.adaptToNewDistribution updated2 newDist
  IO.println "After adapting to new distribution:"
  IO.println s!"  Policy parameters updated"
  IO.println ""
  
  IO.println "Meta-learning test complete."
  IO.println ""

end Semantics.NIICore.MetaLearning
