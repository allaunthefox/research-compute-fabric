import Semantics.FixedPoint

namespace Semantics.Components

/-! # Core Component Interface
Base components that can be mixed on-the-fly.
Each component defines a minimal interface for composition.
-/

/-- A component that can be composed with others -/
class Component where
  componentId : String
  componentType : String
deriving Repr, BEq

/-- Cost function component - computes cost between two values -/
class CostFunction (α β : Type) where
  computeCost : α → β → Q16_16

/-- Invariant extractor - extracts invariant from a value -/
class InvariantExtractor (α : Type) where
  extractInvariant : α → String

/-- Metric component - combines cost function with metadata -/
structure MetricComponent where
  tensor : String  -- "identity", "riemannian", "thermodynamic", "informational", "physical"
  torsion : Q16_16
  reference : String
  history_len : Nat
deriving Repr, BEq

def MetricComponent.euclidean : MetricComponent := {
  tensor := "identity",
  torsion := Q16_16.zero,
  reference := "euclidean_baseline",
  history_len := 0
}

/-- Witness component - trace of lawful operation -/
structure WitnessComponent where
  left_invariant : String
  right_invariant : String
  conserved : Bool
  trace_hash : String
deriving Repr, BEq

def WitnessComponent.lawful (left right : String) : WitnessComponent := {
  left_invariant := left,
  right_invariant := right,
  conserved := true,
  trace_hash := s!"lawful:{left}={right}"
}

#eval WitnessComponent.lawful "left" "right"

end Semantics.Components
