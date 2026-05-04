import Mathlib.Tactic

namespace Semantics.GradientPathMap

/-!
# Gradient Path Map

This module keeps the equation-forest gradient surface finite and proof-checkable.
The former sketch used strings, float conversions, and `sorry`-backed claims.  This
version uses finite node/type identifiers and milli-units for gradient/cost values.
-/

/-- Nodes currently represented in the finite gradient-path sample. -/
inductive EquationNode where
  | couchEquation
  | frameEvolutionContinuous
  | intrinsicLoad
  | totalCognitiveLoad
  | pressurePiling
  | hugoniotTemperature
  | mofCO2_2e_CO          -- MOF CO2 2-electron reduction to CO
  | mofCO2_2e_HCOOH       -- MOF CO2 2-electron reduction to formic acid
  | mofCO2_6e_CH3OH       -- MOF CO2 6-electron reduction to methanol
  | mofCO2_8e_CH4         -- MOF CO2 8-electron reduction to methane
  | affineLinearLayer      -- Affine linear layer Y = X·W + b
  | affineDecomposition    -- Time series decomposition x(t) = s(t) + f(t) + ε
  | affinePeriodic        -- Periodic theorem x(t) = s(t) = s(t-p)
  | affineScaledPeriodic  -- Scaled periodic x(t) = a·x(t-p) + c
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Finite connection classes; no string matching in the proof surface. -/
inductive ConnectionType where
  | variableShared
  | familyConnection
  | domainConnection
  | leanBridge
  | electrochemical       -- Electrochemical reaction pathway
  | electronTransfer      -- Electron transfer relationship
  | timeSeries           -- Time series relationship
  deriving Repr, Inhabited, BEq, DecidableEq

/--
Gradient milli-units.  `1000` represents unit normalized gradient.  The field is
kept as a `Nat`, and lawful connections prove the bound separately.
-/
abbrev GradientMilli := Nat

/-- Connection between two equation nodes in the forest. -/
structure EquationConnection where
  source : EquationNode
  target : EquationNode
  connectionType : ConnectionType
  gradientChange : GradientMilli
  deriving Repr, Inhabited, BEq, DecidableEq

/-- A finite gradient path. -/
structure GradientPath where
  pathId : Nat
  connections : List EquationConnection
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Gradient path map for a finite forest slice. -/
structure ForestGradientPathMap where
  paths : Array GradientPath
  nodeCount : Nat
  connectionCount : Nat
  deriving Repr, Inhabited, BEq, DecidableEq

/-- A connection is lawful when it is bounded and not a self-loop. -/
def equationConnectionLawful (conn : EquationConnection) : Prop :=
  conn.source ≠ conn.target ∧ conn.gradientChange ≤ 1000

/-- Decidable Boolean mirror of the connection lawfulness gate. -/
def equationConnectionBind (conn : EquationConnection) : Bool :=
  conn.source != conn.target && conn.gradientChange ≤ 1000

/-- Cost is the absolute normalized gradient change in milli-units. -/
def equationConnectionCost (conn : EquationConnection) : Nat :=
  conn.gradientChange

/-- A path is lawful when it is nonempty and every connection is lawful. -/
def gradientPathLawful (path : GradientPath) : Prop :=
  path.connections ≠ [] ∧ path.connections.all equationConnectionBind = true

/-- Boolean path gate used by extraction surfaces. -/
def gradientPathBind (path : GradientPath) : Bool :=
  path.connections.isEmpty == false && path.connections.all equationConnectionBind

/-- Total gradient change across a path, in milli-units. -/
def computeTotalGradientChange (connections : List EquationConnection) : Nat :=
  connections.foldl (fun acc conn => acc + conn.gradientChange) 0

/-- Total path cost, in milli-units. -/
def gradientPathCost (path : GradientPath) : Nat :=
  path.connections.foldl (fun acc conn => acc + equationConnectionCost conn) 0

theorem pathCost_eq_totalGradient (path : GradientPath) :
    gradientPathCost path = computeTotalGradientChange path.connections := by
  simp [gradientPathCost, computeTotalGradientChange, equationConnectionCost]

theorem emptyPathZeroGradient :
    computeTotalGradientChange [] = 0 := by
  rfl

/-- If a connection passes the Boolean gate, its cost is bounded by unit gradient. -/
theorem lawfulConnectionCost_le_unit
    (conn : EquationConnection) (h : equationConnectionBind conn = true) :
    equationConnectionCost conn ≤ 1000 := by
  simp [equationConnectionBind] at h
  exact h.2

def couchToFrame : EquationConnection :=
  { source := .couchEquation
  , target := .frameEvolutionContinuous
  , connectionType := .leanBridge
  , gradientChange := 500 }

def loadToCognitive : EquationConnection :=
  { source := .intrinsicLoad
  , target := .totalCognitiveLoad
  , connectionType := .variableShared
  , gradientChange := 100 }

def pressureToHugoniot : EquationConnection :=
  { source := .pressurePiling
  , target := .hugoniotTemperature
  , connectionType := .familyConnection
  , gradientChange := 300 }

/-- MOF 2e- CO to 6e- CH3OH electron transfer pathway. -/
def mof2eCO_to_6eCH3OH : EquationConnection :=
  { source := .mofCO2_2e_CO
  , target := .mofCO2_6e_CH3OH
  , connectionType := .electronTransfer
  , gradientChange := 400 }

/-- MOF 6e- CH3OH to 8e- CH4 electron transfer pathway. -/
def mof6eCH3OH_to_8eCH4 : EquationConnection :=
  { source := .mofCO2_6e_CH3OH
  , target := .mofCO2_8e_CH4
  , connectionType := .electronTransfer
  , gradientChange := 200 }

/-- MOF 2e- HCOOH to 2e- CO electrochemical pathway. -/
def mof2eHCOOH_to_2eCO : EquationConnection :=
  { source := .mofCO2_2e_HCOOH
  , target := .mofCO2_2e_CO
  , connectionType := .electrochemical
  , gradientChange := 150 }

/-- Affine linear layer to time series decomposition. -/
def affineLinear_to_decomposition : EquationConnection :=
  { source := .affineLinearLayer
  , target := .affineDecomposition
  , connectionType := .timeSeries
  , gradientChange := 250 }

/-- Affine decomposition to periodic theorem. -/
def affineDecomposition_to_periodic : EquationConnection :=
  { source := .affineDecomposition
  , target := .affinePeriodic
  , connectionType := .timeSeries
  , gradientChange := 300 }

/-- Affine periodic to scaled periodic. -/
def affinePeriodic_to_scaled : EquationConnection :=
  { source := .affinePeriodic
  , target := .affineScaledPeriodic
  , connectionType := .timeSeries
  , gradientChange := 200 }

/-- Sample gradient paths for the current forest slice. -/
def sampleForestPaths : Array GradientPath :=
  #[ { pathId := 0, connections := [couchToFrame, loadToCognitive] }
   , { pathId := 1, connections := [pressureToHugoniot] }
   , { pathId := 2, connections := [mof2eCO_to_6eCH3OH, mof6eCH3OH_to_8eCH4] }
   , { pathId := 3, connections := [mof2eHCOOH_to_2eCO] }
   , { pathId := 4, connections := [affineLinear_to_decomposition, affineDecomposition_to_periodic] }
   , { pathId := 5, connections := [affinePeriodic_to_scaled] } ]

theorem samplePathsLawful :
    sampleForestPaths.all gradientPathBind = true := by
  native_decide

/-- Gradient path map for the finite forest slice. -/
def forestGradientPathMap : ForestGradientPathMap :=
  { paths := sampleForestPaths
  , nodeCount := 14  -- 6 original + 4 MOF nodes + 4 Affine nodes
  , connectionCount := 10 }  -- 3 original + 3 MOF connections + 3 Affine connections

theorem forestMapHasConnections :
    forestGradientPathMap.connectionCount > 0 := by
  native_decide

theorem forestMapPathsLawful :
    forestGradientPathMap.paths.all gradientPathBind = true := by
  native_decide

theorem samplePathZero_cost_eq_600 :
    gradientPathCost (sampleForestPaths[0]!) = 600 := by
  native_decide

theorem mofPath2_cost_eq_600 :
    gradientPathCost (sampleForestPaths[2]!) = 600 := by
  native_decide

theorem mofPath3_cost_eq_150 :
    gradientPathCost (sampleForestPaths[3]!) = 150 := by
  native_decide

theorem affinePath4_cost_eq_550 :
    gradientPathCost (sampleForestPaths[4]!) = 550 := by
  native_decide

theorem affinePath5_cost_eq_200 :
    gradientPathCost (sampleForestPaths[5]!) = 200 := by
  native_decide

end Semantics.GradientPathMap
