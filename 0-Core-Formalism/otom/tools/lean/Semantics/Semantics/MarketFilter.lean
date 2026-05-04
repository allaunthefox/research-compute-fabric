/-
Copyright (c) 2026 Sovereign Research Stack.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MarketFilter.lean — Behavioral Manifold Market Filter v0.1

Purpose:
  Embed heterogeneous market objects as fixed-point behavioral manifold points,
  then filter them by invariant dynamics rather than ontology/sector labels.

Design constraints:
  * No Float in the hot path.
  * Q16_16 only for coordinates, weights, scores, and thresholds.
  * Market filter, not trading oracle.
  * Outputs are evidence states, not recommendations.

Intended imports:
  Semantics.FixedPoint supplies Q16_16 and fixed-point arithmetic.
-/

import Std
import Semantics.FixedPoint

namespace Semantics.MarketFilter

open Semantics
open Semantics.Q16_16

/-- Claim ladder for evidence discipline. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Five behavioral blocks of the 31-dimensional manifold. -/
inductive MarketDomain where
  | identity
  | conservation
  | transformation
  | scaling
  | dynamics
  deriving Repr, DecidableEq, Inhabited

/--
Domain assignment for a 31-coordinate behavioral vector.

  0–5     Identity
  6–12    Conservation
  13–18   Transformation
  19–24   Scaling
  25–30   Dynamics
-/
def domainOfIndex (i : Fin 31) : MarketDomain :=
  if i.val < 6 then
    .identity
  else if i.val < 13 then
    .conservation
  else if i.val < 19 then
    .transformation
  else if i.val < 25 then
    .scaling
  else
    .dynamics

/-- Human-readable class of the observed object. This is metadata, not the metric. -/
inductive OntologyLabel where
  | equity
  | commodity
  | index
  | currency
  | supplyChain
  | biologicalPipeline
  | foodBatchSystem
  | protocol
  | unknown
  deriving Repr, DecidableEq, Inhabited

/--
MarketPoint is the core embedding object.

It intentionally forgets sector labels in the metric path.
The ontology label is retained only for explanations and mismatch diagnostics.
-/
structure MarketPoint where
  objectId  : String
  windowId  : String
  ontology  : OntologyLabel
  coord     : Fin 31 → Q16_16
  deriving Inhabited

/-- A behavioral query prototype, e.g. "batch bottleneck" or "inventory glut". -/
structure PrototypePoint where
  name        : String
  description : String
  coord       : Fin 31 → Q16_16
  deriving Inhabited

/-- Coordinate and domain weights for the manifold metric. -/
structure MetricWeights where
  coordinate : Fin 31 → Q16_16
  identityWeight       : Q16_16
  conservationWeight   : Q16_16
  transformationWeight : Q16_16
  scalingWeight        : Q16_16
  dynamicsWeight       : Q16_16
  deriving Inhabited

/-- Weight associated with a coordinate's behavioral domain. -/
def domainWeight (w : MetricWeights) (d : MarketDomain) : Q16_16 :=
  match d with
  | .identity       => w.identityWeight
  | .conservation   => w.conservationWeight
  | .transformation => w.transformationWeight
  | .scaling        => w.scalingWeight
  | .dynamics       => w.dynamicsWeight

/-- Sum over all 31 behavioral coordinates. -/
def sum31 (f : Fin 31 → Q16_16) : Q16_16 :=
  (List.finRange 31).foldl
    (fun acc i => Q16_16.add acc (f i))
    Q16_16.zero

/-- Absolute fixed-point coordinate difference. -/
def absCoordDiff (a b : Fin 31 → Q16_16) (i : Fin 31) : Q16_16 :=
  Q16_16.abs (Q16_16.sub (a i) (b i))

/--
Weighted behavioral distance.

This is the central operator:
  compare objects by invariant behavior, not by ontology.
-/
def behavioralDistance
    (w : MetricWeights)
    (a : MarketPoint)
    (b : PrototypePoint) : Q16_16 :=
  sum31 fun i =>
    let cw := w.coordinate i
    let dw := domainWeight w (domainOfIndex i)
    let δ  := absCoordDiff a.coord b.coord i
    Q16_16.mul cw (Q16_16.mul dw δ)

/--
Trace of an object across rolling windows.

The encoder outside Lean should construct this from historical windows.
Lean consumes the already-fixed-point behavioral points.
-/
structure MarketTrace where
  current  : MarketPoint
  previous : MarketPoint
  older    : MarketPoint
  deriving Inhabited

/-- Distance instability across adjacent windows. Lower is more stable. -/
def distanceInstability
    (w : MetricWeights)
    (p : PrototypePoint)
    (tr : MarketTrace) : Q16_16 :=
  let d0 := behavioralDistance w tr.current p
  let d1 := behavioralDistance w tr.previous p
  let d2 := behavioralDistance w tr.older p
  let jump01 := Q16_16.abs (Q16_16.sub d0 d1)
  let jump12 := Q16_16.abs (Q16_16.sub d1 d2)
  Q16_16.add jump01 jump12

/--
Binding is persistence of a low-distance structure.

This uses a rational fixed-point proxy:
  B = 1 / (1 + distanceInstability)

So stable matches score higher without needing exp/log/Float.
-/
def bindingProxy
    (w : MetricWeights)
    (p : PrototypePoint)
    (tr : MarketTrace) : Q16_16 :=
  Q16_16.recip (Q16_16.add Q16_16.one (distanceInstability w p tr))

/--
Ontology mismatch is a diagnostic penalty.

The metric should be allowed to discover cross-ontology equivalence,
so mismatch is not an automatic rejection. It only raises turbulence.
-/
def ontologyMismatchPenalty (a : MarketPoint) : Q16_16 :=
  match a.ontology with
  | .unknown => Q16_16.one
  | _        => Q16_16.zero

/--
Turbulence is unresolved mismatch:
  * distance instability
  * ontology/behavior tension
  * local inability to bind to the prototype

This encodes the project rule:
  turbulence is not mere noise; it can indicate unresolved equivalence.
-/
def turbulenceProxy
    (w : MetricWeights)
    (p : PrototypePoint)
    (tr : MarketTrace) : Q16_16 :=
  let instability := distanceInstability w p tr
  let mismatch    := ontologyMismatchPenalty tr.current
  Q16_16.add instability mismatch

/--
Fixed-point filter score.

Original soft form:
  exp(-d/σ) · B/(1+τ)

Hot-path fixed-point proxy:
  B / (1 + d + τ)

Higher is better. This is a ranking/filter score, not a trade signal.
-/
def filterScore
    (w : MetricWeights)
    (p : PrototypePoint)
    (tr : MarketTrace) : Q16_16 :=
  let d := behavioralDistance w tr.current p
  let b := bindingProxy w p tr
  let τ := turbulenceProxy w p tr
  Q16_16.mul b (Q16_16.recip (Q16_16.add Q16_16.one (Q16_16.add d τ)))

/-- Output record for one asset/prototype comparison. -/
structure FilterResult where
  objectId      : String
  windowId      : String
  prototypeName : String
  distance      : Q16_16
  binding       : Q16_16
  turbulence    : Q16_16
  score         : Q16_16
  claimState    : ClaimState
  explanation   : String
  deriving Inhabited

/-- Build the result record for one trace and one prototype. -/
def evaluatePrototype
    (w : MetricWeights)
    (p : PrototypePoint)
    (tr : MarketTrace)
    (claimState : ClaimState := .beautifulProvisional)
    (explanation : String := "behavioral manifold match; not financial advice") :
    FilterResult :=
  { objectId      := tr.current.objectId
    windowId      := tr.current.windowId
    prototypeName := p.name
    distance      := behavioralDistance w tr.current p
    binding       := bindingProxy w p tr
    turbulence    := turbulenceProxy w p tr
    score         := filterScore w p tr
    claimState    := claimState
    explanation   := explanation }

/--
Thresholded match predicate.

A match requires:
  * distance below threshold
  * binding above threshold
  * turbulence below threshold

The score alone is not sufficient.
-/
def passesFilter
    (distanceMax bindingMin turbulenceMax : Q16_16)
    (r : FilterResult) : Bool :=
  r.distance.val <= distanceMax.val &&
  r.binding.val >= bindingMin.val &&
  r.turbulence.val <= turbulenceMax.val

/--
Adapter explanation placeholder.

The implementation layer should replace this with a real nearest-intermediate
prototype search:
  A object ↔ C adapter prototype ↔ B query prototype
-/
structure AdapterPath where
  sourceObject : String
  adapterName  : String
  targetProto  : String
  turbulence   : Q16_16
  claimState   : ClaimState
  deriving Inhabited

/-- Candidate prototype names for v0.1. -/
def prototypeNamesV01 : List String :=
  [ "batch bottleneck"
  , "inventory glut"
  , "supply squeeze"
  , "demand shock"
  , "margin compression"
  , "capacity expansion"
  , "regulatory delay"
  , "quality failure"
  , "commodity pass-through"
  , "platform network effect"
  ]

end Semantics.MarketFilter
