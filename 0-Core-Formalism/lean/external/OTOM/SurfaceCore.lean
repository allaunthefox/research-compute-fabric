/-
  SurfaceCore.lean - Fixed-Point Surface Definition (Stub)
-/

import Semantics.DynamicCanal
import Semantics.CanonicalInterval
import Semantics.MetricCore
import Semantics.LocalDerivative

namespace Semantics.SurfaceCore

open DynamicCanal
open Semantics.CanonicalInterval
open Semantics.MetricCore
open Semantics.LocalDerivative

abbrev Scalar := Fix16

structure Surface where
  canonicalInterval : CanonicalInterval
  metric : Metric
  localDerivative : LocalDerivative

def surfaceInvariant (surface : Surface) : Prop :=
  canonicalIntervalInvariant surface.canonicalInterval ∧
  metricInvariant surface.metric ∧
  localDerivativeInvariant surface.localDerivative

def divergence (surface : Surface) : Scalar :=
  LocalDerivative.divergence surface.localDerivative

def curvature (surface : Surface) : Scalar :=
  matrixFrobeniusNorm surface.localDerivative.hessian

def stabilityClass (surface : Surface) : StabilityClass :=
  surface.localDerivative.stability

def exampleSurface : Surface :=
  { canonicalInterval := { width := Fix16.one, a := Fix16.zero, b := Fix16.one, k := 1 }
  , metric := { coupling := Fix16.mk 0x00008000, weightWidth := Fix16.one, weightPosition := Fix16.zero }
  , localDerivative := { jacobian := [[Fix16.zero]], hessian := [[Fix16.zero]], point := VecN.zero, stability := StabilityClass.stable } }

theorem exampleSurfacePreservesInvariant :
  surfaceInvariant exampleSurface := by
  constructor
  · simp [exampleSurface, canonicalIntervalInvariant, Fix16.add]
    native_decide
  · constructor
    · simp [exampleSurface, metricInvariant]
    · simp [exampleSurface, localDerivativeInvariant,
        squareMatrixInvariant, rectangularRowsInvariant]

end Semantics.SurfaceCore
