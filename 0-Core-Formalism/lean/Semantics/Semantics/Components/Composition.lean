import Semantics.Components.Core
import Semantics.Components.Gradient
import Semantics.Components.Quaternion
import Semantics.Components.Bind

namespace Semantics.Components

/-! # Component Composition System
Allows on-the-fly mixing of atomic components.
-/

/-- Component mixer - combines components for dynamic composition -/
structure ComponentMixer where
  name : String
  components : List String
  config : String  -- JSON config for component parameters
deriving Repr, BEq

/-- Mix components into a functional pipeline -/
def mixComponents (mixer : ComponentMixer) : String :=
  s!"Mixed {mixer.components.length} components: {mixer.components}"

/-- Example: Mix gradient optimization with bind -/
def createGradientBindMixer : ComponentMixer := {
  name := "gradient_bind",
  components := ["core_bind", "gradient_optimization", "cost_function"],
  config := "{\"learning_rate\": 0.01, \"scaling_param\": 1.0}"
}

/-- Example: Mix quaternion math with bind -/
def createQuaternionBindMixer : ComponentMixer := {
  name := "quaternion_bind",
  components := ["core_bind", "quaternion_math", "cost_function"],
  config := "{\"scale_factor\": 100.0}"
}

#eval mixComponents createGradientBindMixer
#eval mixComponents createQuaternionBindMixer

end Semantics.Components
