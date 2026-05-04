/-
  MetricCore.lean - Minimal stub for LocalDerivative dependency
-/

import Semantics.DynamicCanal

namespace Semantics.MetricCore

open DynamicCanal

structure Metric where
  coupling : Fix16
  weightWidth : Fix16
  weightPosition : Fix16
  deriving Repr, DecidableEq

def metricInvariant (metric : Metric) : Prop :=
  metric.coupling.raw ≤ 0x00010000

end Semantics.MetricCore
