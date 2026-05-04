/-
  RaycastField.lean - Fixed-Point Raycast Field Propagation
-/

import Semantics.DynamicCanal
import Semantics.LocalDerivative

namespace Semantics.RaycastField

open DynamicCanal
open Semantics.LocalDerivative

abbrev Scalar := Fix16

structure ChannelField where
  phase : VecN 3 → Fix16
  amplitude : VecN 3 → Fix16

def sampleChannelField (_field : ChannelField) (_time : Scalar) : ChannelField :=
  { phase := fun _ => Fix16.zero, amplitude := fun _ => Fix16.zero }

def amplitudeMean (_field : ChannelField) : Scalar :=
  Fix16.zero

def inferLocalDerivativeFromMultiPath (_channel : ChannelField) (_time : Scalar) : LocalDerivative :=
  { jacobian := [[Fix16.zero]], hessian := [[Fix16.zero]], point := VecN.zero, stability := StabilityClass.stable }

end Semantics.RaycastField
