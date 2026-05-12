/-
S3CProjectedGeodesicResolution.lean — folded-throat resolution gate

This module compares the old S3C projected-geodesic score against the refined
folded-point theory:

  baseline S3C score
    = manifold distance minus shell/projection error

  folded-throat score
    = baseline distance plus throat shortcut gain minus projected error

The refinement is allowed to improve resolution only when the 0D throat has a
declared folded 16D interior, loopback permeability, Menger-style conservation,
and genus-3/S3C lobe alignment. Otherwise the refinement holds or rejects
instead of silently increasing precision.
-/

import Semantics.Core.FoldedPointManifold

namespace Semantics.S3CProjectedGeodesicResolution

open Semantics.FoldedPointManifold

/-- Resolution comparison after applying the folded-throat refinement. -/
inductive ResolutionDecision where
  | improved
  | unchanged
  | decreased
  | hold
  | reject
  deriving Repr, BEq, DecidableEq

/-- Diagnostic reason for the resolution decision. -/
inductive ResolutionReason where
  | foldedPointRejected
  | loopbackRejected
  | conservationRejected
  | foldedPointMissing
  | loopbackMissing
  | conservationMissing
  | lobeMismatch
  | noThroatShortcut
  | shortcutOutrunsResidual
  | residualOutrunsShortcut
  | exactBoundary
  deriving Repr, BEq, DecidableEq

/-- Minimal finite S3C geodesic sample.

`manifoldDist` is the original S3C route distance.
`throatLength` is the route through the projected 0D throat.
`shellError` is the old shell/projection residual.
`projectedError` is the residual after the folded-throat projection.
`lobeCount = 3` is the S3C/genus-3 alignment witness.
-/
structure S3CGeodesicSample where
  manifoldDist : Nat
  throatLength : Nat
  shellError : Nat
  projectedError : Nat
  lobeCount : Nat
  folded : FoldedPointEvent
  conservation : DimensionalConservation
  deriving Repr, BEq, DecidableEq

/-- Old resolution score: larger means more usable route resolution. -/
def baselineScore (s : S3CGeodesicSample) : Nat :=
  s.manifoldDist - s.shellError

/-- Distance saved by going through the projected throat. -/
def shortcutGain (s : S3CGeodesicSample) : Nat :=
  s.manifoldDist - s.throatLength

/-- S3C's three-handle/lobe alignment gate. -/
def genus3Aligned (s : S3CGeodesicSample) : Bool :=
  s.lobeCount == 3

/-- Full admissibility gate for using the folded 0D throat as a precision
refinement. -/
def foldedThroatAdmissible (s : S3CGeodesicSample) : Bool :=
  decideFoldedPoint s.folded == .admit &&
  decideLoopback s.folded == .loopback &&
  decideConservation s.conservation == .conserved &&
  genus3Aligned s &&
  s.throatLength <= s.manifoldDist

/-- Refined resolution score.

The refinement can only claim a sharper route when the folded-throat gate is
closed. Otherwise it preserves the baseline score and lets `decideResolution`
return HOLD/REJECT where appropriate.
-/
def refinedScore (s : S3CGeodesicSample) : Nat :=
  if foldedThroatAdmissible s then
    s.manifoldDist + shortcutGain s - s.projectedError
  else
    baselineScore s

/-- Amount of old uncertainty that the folded-throat refinement can pay down.

The refinement can improve only when this budget is larger than the new
projected residual:

  shortcutGain + shellError > projectedError
-/
def resolutionBudget (s : S3CGeodesicSample) : Nat :=
  shortcutGain s + s.shellError

/-- Signed score delta: refined score minus baseline score. -/
def resolutionDelta (s : S3CGeodesicSample) : Int :=
  Int.ofNat (refinedScore s) - Int.ofNat (baselineScore s)

/-- Compare the baseline and refined scores. -/
def compareScores (base refined : Nat) : ResolutionDecision :=
  if refined > base then .improved
  else if refined == base then .unchanged
  else .decreased

/-- Decide whether the folded-throat theory improves, preserves, decreases, or
refuses the projected-geodesic resolution. -/
def decideResolution (s : S3CGeodesicSample) : ResolutionDecision :=
  if decideFoldedPoint s.folded == .reject ||
     decideLoopback s.folded == .reject ||
     decideConservation s.conservation == .reject then
    .reject
  else if foldedThroatAdmissible s then
    compareScores (baselineScore s) (refinedScore s)
  else
    .hold

/-- Explain why the score improved, decreased, held, or rejected. -/
def explainResolution (s : S3CGeodesicSample) : ResolutionReason :=
  if decideFoldedPoint s.folded == .reject then
    .foldedPointRejected
  else if decideLoopback s.folded == .reject then
    .loopbackRejected
  else if decideConservation s.conservation == .reject then
    .conservationRejected
  else if decideFoldedPoint s.folded != .admit then
    .foldedPointMissing
  else if decideLoopback s.folded != .loopback then
    .loopbackMissing
  else if decideConservation s.conservation != .conserved then
    .conservationMissing
  else if !genus3Aligned s then
    .lobeMismatch
  else if !(s.throatLength <= s.manifoldDist) then
    .noThroatShortcut
  else
    match compareScores (baselineScore s) (refinedScore s) with
    | .improved => .shortcutOutrunsResidual
    | .decreased => .residualOutrunsShortcut
    | .unchanged => .exactBoundary
    | .hold => .exactBoundary
    | .reject => .exactBoundary

/-- The theory improves resolution when the throat is short, projection error is
lower than the old shell residual, and all folded/conservation gates close. -/
def improvedFixture : S3CGeodesicSample :=
  { manifoldDist := 100
  , throatLength := 40
  , shellError := 20
  , projectedError := 5
  , lobeCount := 3
  , folded := folded16Fixture
  , conservation := mengerConservedFixture }

/-- The theory can decrease resolution when a nominally admissible throat adds
too little shortcut gain and the projected residual is worse. -/
def decreasedFixture : S3CGeodesicSample :=
  { improvedFixture with
    throatLength := 95
    shellError := 10
    projectedError := 20 }

/-- Missing permeability leaves the refinement in HOLD. -/
def holdFixture : S3CGeodesicSample :=
  { improvedFixture with folded := noPermeabilityFixture }

/-- Broken conservation rejects the refined geodesic claim. -/
def rejectFixture : S3CGeodesicSample :=
  { improvedFixture with conservation := brokenConservationFixture }

/-- The exact boundary where folded-throat gain equals projected residual. -/
def unchangedFixture : S3CGeodesicSample :=
  { improvedFixture with
    throatLength := 90
    shellError := 10
    projectedError := 20 }

theorem improvedFixtureImproves :
    decideResolution improvedFixture = .improved := by
  native_decide

theorem decreasedFixtureDecreases :
    decideResolution decreasedFixture = .decreased := by
  native_decide

theorem holdFixtureHolds :
    decideResolution holdFixture = .hold := by
  native_decide

theorem rejectFixtureRejects :
    decideResolution rejectFixture = .reject := by
  native_decide

theorem unchangedFixtureUnchanged :
    decideResolution unchangedFixture = .unchanged := by
  native_decide

theorem improvedFixtureBaselineScore :
    baselineScore improvedFixture = 80 := by
  native_decide

theorem improvedFixtureRefinedScore :
    refinedScore improvedFixture = 155 := by
  native_decide

theorem improvedFixtureReason :
    explainResolution improvedFixture = .shortcutOutrunsResidual := by
  native_decide

theorem decreasedFixtureReason :
    explainResolution decreasedFixture = .residualOutrunsShortcut := by
  native_decide

theorem unchangedFixtureReason :
    explainResolution unchangedFixture = .exactBoundary := by
  native_decide

#eval baselineScore improvedFixture
#eval refinedScore improvedFixture
#eval resolutionBudget improvedFixture
#eval resolutionDelta improvedFixture
#eval decideResolution improvedFixture
#eval explainResolution improvedFixture
#eval decideResolution decreasedFixture
#eval explainResolution decreasedFixture
#eval decideResolution unchangedFixture
#eval explainResolution unchangedFixture
#eval decideResolution holdFixture
#eval decideResolution rejectFixture

end Semantics.S3CProjectedGeodesicResolution
