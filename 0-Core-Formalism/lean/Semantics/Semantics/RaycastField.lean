/-
  RaycastField.lean - Fixed-Point Raycast Field Propagation
-/

import Semantics.FixedPoint
import Semantics.LocalDerivative

namespace Semantics.RaycastField

open Semantics.Q16_16
open Semantics.LocalDerivative

abbrev Scalar := Q16_16

structure ChannelField where
  phase : Array Q16_16 → Q16_16
  amplitude : Array Q16_16 → Q16_16

def sampleChannelField (_field : ChannelField) (_time : Scalar) : ChannelField :=
  { phase := fun _ => zero, amplitude := fun _ => zero }

def amplitudeMean (_field : ChannelField) : Scalar :=
  zero

def inferLocalDerivativeFromMultiPath (_channel : ChannelField) (_time : Scalar) : LocalDerivative :=
  { jacobian := [[zero]], hessian := [[zero]], point := #[zero, zero, zero], stability := StabilityClass.stable }

end Semantics.RaycastField
