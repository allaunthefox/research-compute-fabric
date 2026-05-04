/-
  MetricCore.lean - Minimal stub for LocalDerivative dependency
-/

import Semantics.FixedPoint

namespace Semantics.MetricCore

open Semantics.Q16_16

structure Metric where
  coupling : Q16_16
  weightWidth : Q16_16
  weightPosition : Q16_16
  deriving Repr, DecidableEq

#eval { coupling := zero, weightWidth := zero, weightPosition := zero : Metric }

def metricInvariant (metric : Metric) : Prop :=
  metric.coupling.val ≤ 0x00010000

end Semantics.MetricCore
