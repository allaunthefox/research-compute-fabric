import Semantics.FixedPoint
import Semantics.Components.Core
import Semantics.Components.Gradient
import Semantics.Components.Quaternion

namespace Semantics.Components

/-! # Bind Component
Atomic bind primitive that can be composed with gradient and quaternion components.
-/

/-- Bind result component -/
structure BindResult (α β : Type) where
  left : α
  right : β
  metric : MetricComponent
  cost : Q16_16
  witness : WitnessComponent
  lawful : Bool
deriving Repr, BEq

/-- Core bind operation - can be composed with different cost functions and invariant extractors -/
def coreBind {α β : Type}
  [CostFunction α β]
  [InvariantExtractor α]
  [InvariantExtractor β]
  (left : α) (right : β) (metric : MetricComponent)
  : BindResult α β :=
  let c := CostFunction.computeCost left right
  let left_inv := InvariantExtractor.extractInvariant left
  let right_inv := InvariantExtractor.extractInvariant right
  let w := WitnessComponent.lawful left_inv right_inv
  let is_lawful := left_inv = right_inv
  { left := left, right := right, metric := metric, cost := c, witness := w, lawful := is_lawful }

/-- Optimized bind using gradient component -/
def gradientOptimizedBind {α β : Type}
  [CostFunction α β]
  [InvariantExtractor α]
  [InvariantExtractor β]
  [AdjointComputer Q16_16]
  [GradientStepper Q16_16]
  (left : α) (right : β) (metric : MetricComponent) (gradState : GradientState)
  : BindResult α β :=
  let initial := coreBind left right metric
  let optimized_cost := GradientStepper.gradientStep gradState initial.cost
  { initial with cost := optimized_cost }

/-- Quaternion-optimized bind - combines quaternion component with bind -/
def quaternionOptimizedBind {α β : Type}
  [CostFunction α β]
  [InvariantExtractor α]
  [InvariantExtractor β]
  [QuaternionOps]
  (left : α) (right : β) (metric : MetricComponent) (q : Quaternion) (scale : Q16_16)
  : BindResult α β :=
  let initial := coreBind left right metric
  let q_mag := QuaternionOps.magnitude q
  let adjustment := Q16_16.mul q_mag scale
  let optimized_cost := Q16_16.add initial.cost adjustment
  { initial with cost := optimized_cost }

end Semantics.Components
