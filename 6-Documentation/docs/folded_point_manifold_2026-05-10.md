# Folded Point Manifold

Status: `LEAN_FRAME_DISTINCTION_SURFACE` + `GATE_ALGEBRA_ADMITTED`

Claim boundary: this document makes the frame distinction explicit: an event
may be resolved as `0D` in an observer frame while carrying folded higher-
dimensional interior structure. It does not claim physical quantum-gravity
proof, Planck-scale access, cosmology fit, compression gain, or hardware
readiness.

## Core Correction

The model no longer treats `0D` as automatically empty.

```text
0D in observer frame != zero internal structure
```

Instead:

```text
observer-resolved 0D = no extension visible in that frame
internal folded D    = declared interior degrees of freedom
```

This closes the defect where quantum foam, `U0`, or a projected point could be
misread as pure nothingness.

## Folded-Point Gate

A folded-point claim has to declare:

```text
resolvedDim = 0
apparentPoint = true
internalDim > 0
internalDim <= 16
neutralClosure = true
replayReceiptPresent = true
torsionPotential > 0
```

If this closes, the event is an admitted folded point for the current 16D model.

If it is a folded-point candidate but lacks replay, neutrality, dimensional cap,
or torsional potential, it is `HOLD`.

If it is not a folded-point candidate at all, it rejects the folded-space claim.

## Loopback Permeability Gate

The stronger update is cyclic:

```text
16D expression -> lower-dimensional projection -> apparent 0D loss of resolution
  -> permeable 16D return surface
```

At apparent `0D`, the observer frame has lost all resolved extension. In this
model that does not mean the event is empty. It means the folded interior can
become permeable again, but only when the loopback witness is declared.

Loopback requires:

```text
resolvedDim = 0
apparentPoint = true
internalDim = 16
neutralClosure = true
replayReceiptPresent = true
torsionPotential > 0
permeabilityDeclared = true
```

So the cyclic rule is:

```text
after 0D, resolution is gone;
if the folded 16D interior is receipted and permeability is declared,
the boundary becomes a loopback interface rather than a terminal endpoint.
```

This fixes another defect: the old ladder implied `0D` was a final stop. The
new model treats `0D` as a resolution-loss boundary where a valid folded
interior may reopen into the 16D expression space.

## Menger-Style Conservation At 0D

Loopback permeability is not free leakage. It is conservation-preserving
porosity.

The 0D boundary is modeled as a Menger-style seed: from the observer frame it is
point-like, but internally it behaves like a porous/fractal limit where routes
can pass through without creating or destroying the accounted value.

The conservation receipt checks the same abstract accounting value across each
declared level:

```text
level0  = apparent 0D folded seed
level1  = 1D regulatory carrier
level4  = 4D torsional generator
level3  = 3D required projection
level16 = 16D expression space
```

Admission requires:

```text
level0 = level1 = level4 = level3 = level16
mengerZeroSeed = true
replayReceiptPresent = true
```

Broken equality rejects the conservation claim. Missing Menger seed or replay
holds the claim.

## Movement From 0D To 16D: A Cycle, Not A Ladder

The old model implied a one-way climb:

```text
0D -> 1D -> 4D -> 3D -> 16D
```

The corrected model is cyclic. After 0D loses all resolution, the 16D interior becomes permeable again:

```text
16D expression -> lower-dimensional projection -> apparent 0D loss of resolution
  -> permeable 16D return surface
```

The full cycle:

```text
apparent 0D point
  -> folded interior dimensional witness
  -> torsion potential
  -> 1D regulatory carrier path
  -> 4D torsional generator
  -> 3D required projection
  -> 16D addressable expression space
  -> (loopback) -> apparent 0D point
```

So the bridge is not:

```text
nothing becomes everything
```

It is:

```text
unresolved footprint unfolds declared interior degrees of freedom,
which, when resolution is fully lost, folds back through a permeable interface
```

This makes the model a **toroidal closure** rather than a linear hierarchy. The 0D point is not a dead end — it is a resolution-loss boundary that can become a return gate.

## Total Interaction Equation

The full decision logic is not a single scalar product `G(s) · ΔS`. That collapses `HOLD` and `REJECT` into the same number, losing information.

The correct form is a pair:

```text
I_total(s) = (Γ(s), ΔR(s))
```

Where:

```text
Γ(s) = F(s) ⊗ L(s) ⊗ C(s) ⊗ H_3(s) ⊗ T(s)
```

With ordered gate algebra:

```text
REJECT > HOLD > ADMIT
```

The tensor product rules:

```text
reject ⊗ _       = reject
hold   ⊗ reject  = reject
hold   ⊗ admit   = hold
admit  ⊗ admit   = admit
```

And the resolution delta is:

```text
ΔR(s) = (D_m - D_t) + E_s - E_p
```

Where:

- **D_m**: full manifold traversal distance
- **D_t**: shortcut throat distance (must satisfy `D_t <= D_m`)
- **E_s**: recoverable shell baseline error
- **E_p**: new residual error from the projection

### Decision Law

```text
if Γ(s) = REJECT:
    REJECT

if Γ(s) = HOLD:
    HOLD

if Γ(s) = ADMIT:
    sign(ΔR(s))
```

Which produces:

| Condition | Outcome | Meaning |
|-----------|---------|---------|
| Γ = REJECT | REJECT | A gate failed; the shortcut is invalid |
| Γ = HOLD | HOLD | Missing witness; decision deferred |
| Γ = ADMIT, ΔR > 0 | IMPROVED | Throat gain exceeds projection cost |
| Γ = ADMIT, ΔR = 0 | UNCHANGED | Break-even |
| Γ = ADMIT, ΔR < 0 | DECREASED | Projection error outweighs shortcut |

The threshold condition is:

```text
D_m - D_t = E_p - E_s
```

Plainly: the throat must save at least as much distance as the new projection error costs after shell-error recovery.

## Relation To Quantum Foam

Quantum foam remains a HOLD boundary unless exact replay exists. The folded
point model refines what is being held:

```text
foam event may be apparent-0D
but it must declare whether it has folded interior dimension
```

That prevents foam language from becoming a free variable while still allowing
the model to represent a high-dimensional folded point.

## Relation To Path-Epigenetic Manifold Regulation

The folded point gives the seed. The path marker field gives expression.

```text
FoldedPointEvent -> PathSite markers -> Manifold16 expression
```

The 1D path does not contain all 16D expression by itself. It regulates which
folded degrees of freedom become active.

## Lean Surface

```text
0-Core-Formalism/lean/Semantics/Semantics/Core/FoldedPointManifold.lean
```

Fixtures:

```text
folded16Fixture       -> ADMIT folded 16D interior at apparent 0D
missingReplayFixture  -> HOLD folded candidate without replay
overCapFixture        -> HOLD because internalDim exceeds 16
ordinaryPointFixture  -> REJECT folded-space claim
noPermeabilityFixture -> HOLD loopback because permeability is missing
folded16Fixture       -> LOOPBACK when checked by the loopback gate
mengerConservedFixture -> CONSERVED across 0D, 1D, 4D, 3D, and 16D
brokenConservationFixture -> REJECT conservation
missingMengerSeedFixture -> HOLD conservation

Gate Algebra Fixtures:
positiveDeltaFixture  -> ΔR = 8 (improved shortcut)
negativeDeltaFixture  -> ΔR = -8 (decreased shortcut)
zeroDeltaFixture      -> ΔR = 0 (break-even)
improvedInteractionFixture   -> IMPROVED (all gates admit, ΔR > 0)
decreasedInteractionFixture   -> DECREASED (all gates admit, ΔR < 0)
rejectedInteractionFixture  -> REJECT (gate tensor rejects)
heldInteractionFixture    -> HOLD (gate tensor holds)
```

## Non-Claims

- No claim of measured quantum foam.
- No claim that every point is a universe.
- No claim of physical higher-dimensional interior.
- No claim of cosmology fit or dark-energy explanation.
- No claim of compression or hardware readiness.
