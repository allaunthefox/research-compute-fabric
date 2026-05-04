/-
  Holy Diver / ENE
  Forest Autodoc Registry

  Third layer of the integrated architecture:
  - RealityContractMassNumber.lean (base ontology)
  - FieldEquationIntegration.lean (field equation machinery)
  - ForestAutodocRegistry.lean (forest registry with autodoc)

  This module combines the base ontology with field equation enhancements
  to provide a complete forest registry with automatic documentation pressure
  and history tracking via MMR.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Semantics.RealityContractMassNumber
import Semantics.FieldEquationIntegration

namespace HolyDiver
namespace ForestRegistry

/-! ## Forest registry structures -/

/-- 
A forest node represents a candidate in the forest with its enhanced
field equation state and web stabilization status.
History is now managed by the registry, not embedded in each node.
-/
structure ForestNode where
  record   : FieldSystem.EnhancedCandidate
  webStable : Bool
  deriving Repr

/-- 
The forest registry maintains a collection of forest nodes with
Σ-selector for decision-making, web stabilization for topology,
and owns the full SelfFeedingMMR for history tracking.
-/
structure ForestRegistry where
  nodes        : List ForestNode
  selector     : FieldSystem.SigmaSelector
  webs         : FieldSystem.WebSystem
  collapseMode : FieldSystem.CollapseMode
  history      : FieldSystem.SelfFeedingMMR  -- Registry owns full history

/-! ## Forest operations -/

/-- Check if two candidates have the same morphic core (identity continuity). -/
def sameMorphicCore
    (c1 c2 : FieldSystem.EnhancedCandidate) : Bool :=
  c1.core.coreId = c2.core.coreId

/-- Check if two candidates have similar morphic cores (for edge-survivor linkage). -/
def similarMorphicCore
    (c1 c2 : FieldSystem.EnhancedCandidate)
    (threshold : Nat) : Bool :=
  let m1 := c1.core.invariantMass
  let m2 := c2.core.invariantMass
  let massDiff := if m1 >= m2 then m1 - m2 else m2 - m1
  massDiff < threshold

/-- Add a new enhanced candidate to the forest registry using morphic core create-vs-update logic. -/
def ForestRegistry.addCandidate
    (reg : ForestRegistry)
    (candidate : FieldSystem.EnhancedCandidate) : ForestRegistry :=
  -- Check if candidate with same morphic core exists (update case)
  let existingNode := reg.nodes.find? (fun node => sameMorphicCore node.record candidate)
  match existingNode with
  | some node =>
    -- Update existing node with new projection
    let updatedNode :=
      { node with record := candidate }
    { reg with nodes := reg.nodes.map (fun n => if n.record.base.name = node.record.base.name then updatedNode else n) }
  | none =>
    -- Create new node
    let newNode :=
      { record := candidate,
        webStable := true }
    { reg with nodes := newNode :: reg.nodes }

/-- Apply web stabilization to all nodes in the registry. -/
def ForestRegistry.stabilizeAll (reg : ForestRegistry) : ForestRegistry :=
  let stabilizedNodes :=
    reg.nodes.map (fun node =>
      let currentState :=
        [node.record.fieldState.famm,
         node.record.fieldState.iutt,
         node.record.fieldState.center,
         node.record.fieldState.dp]
      let newState := reg.webs.stabilize currentState
      let newFieldState :=
        { node.record.fieldState with
          famm := FieldSystem.getNthDefault newState 0 0,
          iutt := FieldSystem.getNthDefault newState 1 0,
          center := FieldSystem.getNthDefault newState 2 0,
          dp := FieldSystem.getNthDefault newState 3 0 }
      { node with
        record := { node.record with fieldState := newFieldState },
        webStable := true })
  { reg with nodes := stabilizedNodes }

/-- Select the best candidate using the Σ-selector. -/
def ForestRegistry.selectBest (reg : ForestRegistry) : Option FieldSystem.EnhancedCandidate :=
  let candidates := reg.nodes.map (fun node => node.record)
  -- Simple selection based on tension score (using fieldState values)
  if candidates.isEmpty then none else
  candidates.foldl (fun acc x =>
    match acc with
    | none => some x
    | some best =>
      if x.tension > best.tension then some x else some best) none

/-- Apply collapse mode to a candidate based on threshold. -/
def applyCollapse
    (mode : FieldSystem.CollapseMode)
    (threshold : Nat)
    (epsilon : Nat)
    (value : Nat) : Nat :=
  if value < threshold then
    match mode with
    | FieldSystem.CollapseMode.soft => epsilon
    | FieldSystem.CollapseMode.hard => 0
  else
    value

/-- 
Compute autodoc pressure for a candidate using the integrated field equation
system and tension function.
-/
def autodocPressureIntegrated
    (candidate : FieldSystem.EnhancedCandidate)
    (risk : ENE.ResidualRisk)
    (factors : ENE.AutodocFactors) : Nat :=
  -- Use tension score from enhanced candidate
  let tensionScore := candidate.tension
  -- Use historyRef.root for history pressure
  let historyPressure := candidate.historyRef.root
  -- Compute composite pressure
  tensionScore + historyPressure + factors.novelty + factors.compression

/-! ## Forest update cycle -/

/-- 
Complete forest update cycle:
  1. Stabilize all nodes with web constraints
  2. Select best candidate with Σ-selector
  3. Apply collapse mode if needed
  4. Update MMR history (registry-owned)
-/
def ForestRegistry.updateCycle
    (reg : ForestRegistry)
    (threshold : Nat)
    (epsilon : Nat) : ForestRegistry :=
  let stabilized := reg.stabilizeAll
  let bestCandidate := stabilized.selectBest
  match bestCandidate with
  | none => stabilized
  | some best =>
    let collapsedValue :=
      applyCollapse reg.collapseMode threshold epsilon best.tension
    let updatedRecord :=
      { best with tension := collapsedValue }
    let updatedHistoryRef :=
      { best.historyRef with root := updatedRecord.historyRef.root }
    let updatedRecordWithRef :=
      { updatedRecord with historyRef := updatedHistoryRef }
    let updatedHistory :=
      reg.history.append updatedRecordWithRef.historyRef.root
    let updatedNodes :=
      stabilized.nodes.map (fun node =>
        if node.record.base.name = best.base.name then
          { node with record := updatedRecordWithRef }
        else
          node)
    { stabilized with nodes := updatedNodes, history := updatedHistory }

/-! ## Auto-mapping registry integration -/

/-- 
Lookup field equation concept and return corresponding Lean structure
from the integrated registry.
-/
def lookupIntegratedConcept (concept : String) : Option String :=
  match concept with
  | "Σ-selector" => some "FieldSystem.SigmaSelector"
  | "MMR" => some "FieldSystem.SelfFeedingMMR"
  | "pentagonal square" => some "FieldSystem.PentagonalSquare"
  | "FAMM" => some "FieldSystem.FieldType.famm"
  | "IUTT" => some "FieldSystem.FieldType.iutt"
  | "Center" => some "FieldSystem.FieldType.center"
  | "DP" => some "FieldSystem.FieldType.dp"
  | "Unified state" => some "FieldSystem.UnifiedState"
  | "Tension function" => some "FieldSystem.TensionFunction"
  | "Collapse mode" => some "FieldSystem.CollapseMode"
  | "Web system" => some "FieldSystem.WebSystem"
  | "Enhanced candidate" => some "FieldSystem.EnhancedCandidate"
  | "Candidate record MMR" => some "FieldSystem.CandidateRecordMMR"
  | _ => none

end ForestRegistry
end HolyDiver
