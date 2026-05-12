# S3C Projected Geodesic Resolution Refinement

Status: `LEAN_RESOLUTION_COMPARISON_SURFACE`

Claim boundary: this is a finite resolution comparison for the S3C projected
geodesic after adding the folded-point / 0D throat theory. It does not prove
physical genus-3 topology, cosmology, quantum foam, compression gain, or
hardware readiness.

## Core Update

The older S3C surface already had a throat:

```text
n = k² + a
b⁰ = (k+1)² - 1 - n
throat when a = b⁰ = k
```

The new theory refines the throat by asking whether the apparent `0D` throat is
only a point in the observer frame or whether it carries a receipted folded 16D
interior.

```text
observer 0D throat
  + folded 16D interior
  + loopback permeability
  + Menger-style conservation
  => usable projected geodesic shortcut
```

## Resolution Equations

The baseline S3C resolution score is:

```text
baselineScore = manifoldDist - shellError
```

The folded-throat shortcut is:

```text
shortcutGain = manifoldDist - throatLength
```

The refined score is only active when the folded throat is admissible:

```text
refinedScore = manifoldDist + shortcutGain - projectedError
```

So the question is not "does the new theory always increase resolution?"

The executable question is:

```text
compare baselineScore with refinedScore
```

Equivalently, the reason boundary is:

```text
resolutionBudget = shortcutGain + shellError
resolutionDelta  = refinedScore - baselineScore
                 = shortcutGain + shellError - projectedError
```

So:

```text
if resolutionBudget > projectedError:  resolution improves
if resolutionBudget = projectedError:  resolution is unchanged
if resolutionBudget < projectedError:  resolution decreases
```

## Admission Gate

The refined projected geodesic is allowed only when all of these close:

```text
decideFoldedPoint = admit
decideLoopback = loopback
decideConservation = conserved
lobeCount = 3
throatLength <= manifoldDist
```

This is the 0D-throat correction:

```text
0D throat explains the projected geodesic only when the throat has a receipted
folded interior and the dimensional ledger is conserved.
```

## Result

The Lean fixtures show all four outcomes:

```text
improvedFixture:
  baselineScore = 80
  refinedScore  = 155
  decision      = improved

decreasedFixture:
  decision      = decreased
  reason        = residualOutrunsShortcut

unchangedFixture:
  decision      = unchanged
  reason        = exactBoundary

holdFixture:
  missing permeability
  decision      = hold

rejectFixture:
  broken dimensional conservation
  decision      = reject
```

Interpretation:

```text
The refinement improves resolution when the throat is a short, conserved,
receipted path with lower projected residual.

The refinement decreases resolution when the throat shortcut is weak and the
projected residual is worse than the old shell residual.

The exact failure mode is:

```text
projectedError > shortcutGain + shellError
```

That means the new folded-throat path did not buy enough route shortening or
old-error recovery to pay for the residual introduced by projection.

The refinement holds or rejects when the folded-point, permeability, or
conservation witnesses do not close.
```

That is the useful answer: the theory sharpens resolution only under a bounded
gate. It also gives a way to detect when the new geometry makes the model worse.

## Lean Surface

```text
0-Core-Formalism/lean/Semantics/Semantics/Core/S3CProjectedGeodesicResolution.lean
```

Executable witnesses:

```text
improvedFixtureImproves
decreasedFixtureDecreases
holdFixtureHolds
rejectFixtureRejects
unchangedFixtureUnchanged
improvedFixtureBaselineScore
improvedFixtureRefinedScore
improvedFixtureReason
decreasedFixtureReason
unchangedFixtureReason
```

The module is imported by:

```text
0-Core-Formalism/lean/Semantics/Semantics.lean
```

## Non-Claims

- No physical measurement of quantum foam.
- No proof that S3C is a physical genus-3 manifold.
- No cosmology fit.
- No compression-ratio or Hutter claim.
- No FPGA/ASIC readiness claim.
