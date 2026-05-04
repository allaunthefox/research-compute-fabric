import Semantics.CanonicalInterval
import Semantics.MetricCore
import Semantics.LocalDerivative

namespace Semantics.SolitonLighthouse

open Semantics.CanonicalInterval
open Semantics.MetricCore
open Semantics.LocalDerivative

abbrev Scalar := Float

structure BindManifoldPoint where
  canonicalInterval : CanonicalInterval
  metric : Metric
deriving Repr, DecidableEq

def bindManifoldPointInvariant (point : BindManifoldPoint) : Prop :=
  canonicalIntervalInvariant point.canonicalInterval ∧
  conservationInvariant point.canonicalInterval ∧
  metricInvariant point.metric

structure Direction where
  heading : Scalar
  magnitude : Scalar
deriving Repr, DecidableEq

def directionInvariant (direction : Direction) : Prop :=
  direction.magnitude >= 0.0

structure SolitonWave where
  amplitude : Scalar
  phase : Scalar
  frequency : Scalar
  canonicalInterval : CanonicalInterval
  direction : Direction
deriving Repr, DecidableEq

def solitonWaveInvariant (wave : SolitonWave) : Prop :=
  wave.amplitude >= 0.0 ∧
  wave.frequency >= 0.0 ∧
  canonicalIntervalInvariant wave.canonicalInterval ∧
  directionInvariant wave.direction

structure SolitonLighthouse where
  origin : BindManifoldPoint
  solitonWave : SolitonWave
deriving Repr, DecidableEq

def solitonLighthouseInvariant (lighthouse : SolitonLighthouse) : Prop :=
  bindManifoldPointInvariant lighthouse.origin ∧
  solitonWaveInvariant lighthouse.solitonWave

def raycastSpawn
  (point : BindManifoldPoint)
  (direction : Direction) : SolitonLighthouse :=
  { origin := point
  , solitonWave :=
      { amplitude := point.canonicalInterval.width
      , phase := 0.0
      , frequency := point.metric.coupling + 1.0
      , canonicalInterval := point.canonicalInterval
      , direction := direction } }

def propagate
  (lighthouse : SolitonLighthouse)
  (derivative : LocalDerivative) : SolitonLighthouse :=
  let phaseDelta := divergenceCost derivative + torsionCost derivative
  let amplitudeScale := max 0.0 (1.0 - 0.1 * curvatureCost derivative)
  { lighthouse with
      solitonWave :=
        { lighthouse.solitonWave with
            phase := lighthouse.solitonWave.phase + lighthouse.solitonWave.frequency + phaseDelta
            amplitude := lighthouse.solitonWave.amplitude * amplitudeScale } }

def exampleBindManifoldPoint : BindManifoldPoint :=
  { canonicalInterval := exampleCanonicalInterval
  , metric := exampleMetric }

def exampleDirection : Direction :=
  { heading := 0.0, magnitude := 1.0 }

def exampleSolitonLighthouse : SolitonLighthouse :=
  raycastSpawn exampleBindManifoldPoint exampleDirection

end Semantics.SolitonLighthouse
