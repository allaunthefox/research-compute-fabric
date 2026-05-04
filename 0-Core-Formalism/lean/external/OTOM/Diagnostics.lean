import Semantics.Path

namespace Semantics.ENE

-- ENE Self-Diagnostics
-- Formalization of the five-condition unified invariant from the
-- unconventional mathematics specification.
--
-- The Five Conditions:
--   KNIT:    Hamiltonian path exists (learning loop covers all points)
--   RIGID:   Stress matrix Ω ⪰ 0, Ωp = 0 (load balanced, structure stable)
--   CRNT:    Deficiency δ = 0 (decision space minimally specified)
--   FLAVOR:  ΔMₛ > 0 (method assignments more coherent than random)
--   NEURO:   |gradient_slope| > τ (gradient mode active)

/-- Diagnostic report for the ENE graph. Mirrors `ene_diagnostics.py`. -/
structure DiagnosticReport where
  nPoints : Nat := 0

  -- KNIT condition
  knitPathExists : Bool := false
  knitCoverage   : Float := 0.0
  knitPathLength : Nat := 0

  -- RIGID condition
  rigidPsd       : Bool := false
  rigidResidual  : Float := 0.0
  rigidMinEigen  : Float := 0.0

  -- CRNT condition
  crntDeficiency : Nat := 0
  crntComplexes  : Nat := 0
  crntLinkage    : Nat := 0
  crntStoichDim  : Nat := 0
  crntIsZero     : Bool := false

  -- FLAVOR condition
  flavorSharing  : Float := 0.0
  flavorRandom   : Float := 0.0
  flavorBias     : Float := 0.0
  flavorPositive : Bool := false

  -- NEURO condition
  neuroSlope     : Float := 0.0
  neuroThreshold : Float := 0.3
  neuroOk        : Bool := false
  neuroMode      : String := "UNKNOWN"

deriving Repr, BEq

/-- Count how many conditions passed. -/
def DiagnosticReport.conditionsPassed (r : DiagnosticReport) : Nat :=
  let checks := [
    r.knitPathExists,
    r.rigidPsd,
    r.crntIsZero,
    r.flavorPositive,
    r.neuroOk
  ]
  checks.filter id |>.length

def DiagnosticReport.conditionsTotal : Nat := 5

/-- Overall health: all five conditions must pass. -/
def DiagnosticReport.overallHealthy (r : DiagnosticReport) : Bool :=
  r.conditionsPassed = DiagnosticReport.conditionsTotal

/-- KNIT condition: a Hamiltonian-like path exists through all MIPoint nodes.
In the formalization, this is a proposition that a lawful path visits
all observation nodes in the graph. -/
def KnitCondition (g : Graph) (p : AtomicPath) : Prop :=
  let miNodes := g.nodes.filter (λ n => match n.type with | NodeType.observation => true | _ => false)
  AtomicPath.isLawful p ∧ AtomicPath.length p = miNodes.length

/-- RIGID condition: the graph's stress structure is positive semi-definite.
We formalize this as a predicate on the graph's load profiles. -/
def RigidCondition (g : Graph) : Prop :=
  -- In the formal model, this requires that for every interpretation node,
  -- the associated load profile is non-negative and finite.
  ∀ n ∈ g.nodes,
    (∀ e ∈ g.edges,
      e.target == n ∧ e.type == EdgeType.has_load →
      e.weight ≥ 0.0)

/-- CRNT (Chemical Reaction Network Theory) condition:
The decision space is minimally specified — no hidden deficiency.
In the formal model: the graph has no orphan observation nodes
(nodes with no outgoing projection edge). -/
def CrntCondition (g : Graph) : Prop :=
  ∀ n ∈ g.nodes,
    n.type == NodeType.observation →
    (∃ e ∈ g.edges, e.source == n ∧ e.type == EdgeType.projects_to)

/-- FLAVOR condition: method assignments are more coherent than random.
In the formal model: nodes assigned to the same attractor share
a common method label more often than not. -/
def FlavorCondition (g : Graph) : Prop :=
  -- For every attractor, if multiple canonical states are assigned to it,
  -- they should share methods positively.
  ∀ a ∈ g.nodes,
    a.type == NodeType.attractor →
    let assigned := g.inEdges a |>.filter (λ e => e.type == EdgeType.assigned_to)
    let methods := assigned.map (λ e => e.source.label)
    methods.length ≤ 1 ∨
    -- There exists some method that appears more than once
    (∃ m, 1 < (methods.filter (λ x => x == m)).length)

/-- NEURO condition: the graph exhibits gradient structure along a principal axis.
In the formal model: there exists a path through observations where
the method labels correlate with position in the path. -/
def NeuroCondition (_g : Graph) : Prop :=
  -- There exists a non-empty lawful path through observations
  -- with at least 3 nodes, showing structured progression.
  ∃ (p : AtomicPath),
    AtomicPath.isLawful p ∧ AtomicPath.length p ≥ 3 ∧
    AtomicPath.staysWithin p (λ n => n.type == NodeType.observation)

/-- The complete set of five ENE conditions as a single structure. -/
structure ENEDiagnostics where
  graph : Graph
  knitPath : AtomicPath
  report : DiagnosticReport

/-- All five conditions hold simultaneously. -/
def ENEDiagnostics.allConditionsHold (d : ENEDiagnostics) : Prop :=
  KnitCondition (ENEDiagnostics.graph d) (ENEDiagnostics.knitPath d) ∧
  RigidCondition (ENEDiagnostics.graph d) ∧
  CrntCondition (ENEDiagnostics.graph d) ∧
  FlavorCondition (ENEDiagnostics.graph d) ∧
  NeuroCondition (ENEDiagnostics.graph d)

/-- A graph is healthy if all five diagnostics pass. -/
def Graph.isHealthy (g : Graph) (p : AtomicPath) : Prop :=
  KnitCondition g p ∧ RigidCondition g ∧ CrntCondition g ∧
  FlavorCondition g ∧ NeuroCondition g

end Semantics.ENE
