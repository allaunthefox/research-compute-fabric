import Semantics.Components.Core
import Semantics.Components.Gradient
import Semantics.Components.Quaternion
import Semantics.Components.Bind
import Semantics.Components.Pipeline
import Semantics.Components.State
import Semantics.Components.Composition

namespace Semantics.Components

/-! # Component Mixing Demo
Demonstrates on-the-fly mixing of atomic components.
-/

/-- Example 1: Mix gradient optimization with bind for cost computation -/
def demoGradientBindMix : Unit :=
  let gradState := GradientState.default
  let metric := MetricComponent.euclidean
  let mixer := createGradientBindMixer
  let result := mixComponents mixer
  ()

/-- Example 2: Mix quaternion math with bind for rotation-based cost -/
def demoQuaternionBindMix : Unit :=
  let q := Quaternion.one
  let metric := MetricComponent.euclidean
  let mixer := createQuaternionBindMixer
  let result := mixComponents mixer
  ()

/-- Example 3: Mix pipeline components for temporal processing -/
def demoPipelineMix : Unit :=
  let tempBuf := TemporalBufferComponent.empty 10
  let state := Q16_16.ofInt 100
  let (newBuf, updatedState) := TemporalBufferUpdater.updateBuffer tempBuf state
  ()

/-- Example 4: Mix state components for canonical transitions -/
def demoStateMix : Unit :=
  let canonicalState := CanonicalStateComponent.default
  let newDelta := Q16_16.ofInt 50
  let updatedState := updateStateWithDelta canonicalState newDelta
  ()

/-- Demonstrate dynamic component selection -/
def selectCostComponent (useGradient : Bool) : String :=
  if useGradient then "gradient_optimization" else "standard_cost"

/-- Demonstrate component configuration -/
def configureComponent (name : String) (config : String) : ComponentMixer :=
  { name := name, components := [name], config := config }

/-- Run all demos -/
def runAllDemos : Unit :=
  let _ := demoGradientBindMix
  let _ := demoQuaternionBindMix
  let _ := demoPipelineMix
  let _ := demoStateMix
  ()

end Semantics.Components
