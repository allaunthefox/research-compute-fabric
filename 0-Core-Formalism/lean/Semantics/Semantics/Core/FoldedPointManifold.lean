/-
FoldedPointManifold.lean — apparent 0D footprint with higher-dimensional interior

This module makes explicit the frame distinction:

  observer-resolved dimension = 0
  internal/folded dimension   may be > 0

That prevents the model from treating "0D" as automatically empty. A point may
be an observer-frame footprint of folded higher-dimensional structure, but the
claim is admitted only when neutral closure, replay, bounded dimensionality, and
torsional potential are declared.

The stronger loopback claim is separate: when the observer frame has lost all
resolution at apparent 0D, a declared 16D interior may become a permeable return
surface only if the permeability witness is present.

Permeability is not free leakage. It is conservation-preserving porosity: every
dimensional level that participates in the loopback must carry the same
accounting value.
-/

import Semantics.FixedPoint

namespace Semantics.FoldedPointManifold

open Semantics.FixedPoint

/-- Terminal gate for a folded-point claim. -/
inductive FoldDecision where
  | admit
  | hold
  | reject
  deriving Repr, BEq, DecidableEq

/-- Terminal gate for the 0D -> 16D loopback/permeability claim. -/
inductive LoopbackDecision where
  | loopback
  | hold
  | reject
  deriving Repr, BEq, DecidableEq

/-- Terminal gate for conservation across the dimensional ladder. -/
inductive ConservationDecision where
  | conserved
  | hold
  | reject
  deriving Repr, BEq, DecidableEq

/-- Minimal folded-point event.

`resolvedDim = 0` means the observer frame sees no extension.
`internalDim > 0` means the event carries folded interior degrees of freedom.
`neutralClosure` links the claim back to U0 accounting.
`torsionPotential` is normalized Q0.16 expression potential.
`permeabilityDeclared` is the extra witness for the stronger loopback claim.
-/
structure FoldedPointEvent where
  resolvedDim : Nat
  internalDim : Nat
  apparentPoint : Bool
  neutralClosure : Bool
  replayReceiptPresent : Bool
  torsionPotential : Q0_16
  permeabilityDeclared : Bool
  deriving Repr, BEq, DecidableEq

/-- A folded point is a point only in the observer frame. -/
def isFoldedPoint (e : FoldedPointEvent) : Bool :=
  e.apparentPoint && e.resolvedDim == 0 && e.internalDim > 0

/-- Current model cap: the folded interior may be up to the declared 16D
manifold, but not an unbounded free variable. -/
def withinDeclaredDimensionalCap (e : FoldedPointEvent) : Bool :=
  e.internalDim <= 16

/-- There must be nonzero torsional potential to unfold. -/
def hasTorsionPotential (e : FoldedPointEvent) : Bool :=
  e.torsionPotential.val != 0

/-- The observer frame has lost all spatial resolution at the footprint. -/
def resolutionLost (e : FoldedPointEvent) : Bool :=
  e.apparentPoint && e.resolvedDim == 0

/-- A folded point is admissible only when the apparent point, internal
dimensional witness, neutral closure, replay, cap, and torsion potential close.
Missing replay/neutrality/capacity routes to HOLD if the event is at least a
folded-point candidate. Non-folded points reject the folded-space claim. -/
def decideFoldedPoint (e : FoldedPointEvent) : FoldDecision :=
  if isFoldedPoint e then
    if withinDeclaredDimensionalCap e &&
       e.neutralClosure &&
       e.replayReceiptPresent &&
       hasTorsionPotential e then
      .admit
    else
      .hold
  else
    .reject

/-- The stronger cyclic claim: after apparent 0D, a declared 16D interior can
be treated as a permeable return surface only when the separate permeability
witness is present. -/
def decideLoopback (e : FoldedPointEvent) : LoopbackDecision :=
  if resolutionLost e then
    if e.internalDim == 16 &&
       e.permeabilityDeclared &&
       e.neutralClosure &&
       e.replayReceiptPresent &&
       hasTorsionPotential e then
      .loopback
    else
      .hold
  else
    .reject

/-- Conservation witness across the compressed 0D seed, carrier path, generator,
projection surface, and 16D expression space.

`mengerZeroSeed` marks the 0D boundary as a porous/fractal conservation limit,
not an empty point. The values are abstract accounting charges/loads, not
physical mass claims.
-/
structure DimensionalConservation where
  level0 : Int
  level1 : Int
  level4 : Int
  level3 : Int
  level16 : Int
  mengerZeroSeed : Bool
  replayReceiptPresent : Bool
  deriving Repr, BEq, DecidableEq

/-- Conservation means every declared dimensional level carries the same
accounting value. -/
def conservedAcrossLevels (c : DimensionalConservation) : Bool :=
  c.level0 == c.level1 &&
  c.level1 == c.level4 &&
  c.level4 == c.level3 &&
  c.level3 == c.level16

/-- The Menger-style 0D seed only admits conservation when replay is present.
Broken conservation rejects. A missing porous seed or replay is HOLD. -/
def decideConservation (c : DimensionalConservation) : ConservationDecision :=
  if conservedAcrossLevels c then
    if c.mengerZeroSeed && c.replayReceiptPresent then .conserved
    else .hold
  else
    .reject

/-- Canonical fixture: observer sees 0D, interior declares 16D, closure and
replay are present, and torsional potential can unfold. -/
def folded16Fixture : FoldedPointEvent :=
  { resolvedDim := 0
  , internalDim := 16
  , apparentPoint := true
  , neutralClosure := true
  , replayReceiptPresent := true
  , torsionPotential := Q0_16.half
  , permeabilityDeclared := true }

/-- Same folded candidate, but no replay receipt: HOLD, not ADMIT. -/
def missingReplayFixture : FoldedPointEvent :=
  { folded16Fixture with replayReceiptPresent := false }

/-- Same observer point, but internal dimensionality exceeds the declared cap:
HOLD until a new cap/law is declared. -/
def overCapFixture : FoldedPointEvent :=
  { folded16Fixture with internalDim := 17 }

/-- An ordinary 0D point with no internal dimension rejects a folded-space
claim. -/
def ordinaryPointFixture : FoldedPointEvent :=
  { folded16Fixture with internalDim := 0 }

/-- Folded and neutral, but no permeability witness: HOLD for loopback. -/
def noPermeabilityFixture : FoldedPointEvent :=
  { folded16Fixture with permeabilityDeclared := false }

/-- Menger-style 0D seed preserves the same accounting value across every
declared dimensional level. -/
def mengerConservedFixture : DimensionalConservation :=
  { level0 := 3
  , level1 := 3
  , level4 := 3
  , level3 := 3
  , level16 := 3
  , mengerZeroSeed := true
  , replayReceiptPresent := true }

def brokenConservationFixture : DimensionalConservation :=
  { mengerConservedFixture with level16 := 4 }

def missingMengerSeedFixture : DimensionalConservation :=
  { mengerConservedFixture with mengerZeroSeed := false }

/-! ## Gate Algebra for Total Interaction

The total interaction is a pair `I_total(s) = (Γ(s), ΔR(s))`.

`Γ(s)` is the ordered tensor product of individual gate outcomes.
The order is: REJECT > HOLD > ADMIT.

`ΔR(s)` is the resolution delta: shortcut gain plus shell error recovery
minus projected error.
-/

/-- Ordered gate outcomes for the tensor product.
    REJECT > HOLD > ADMIT - this ordering ensures that a single
    rejection dominates, and a single hold blocks admission. -/
inductive GateOutcome where
  | reject
  | hold
  | admit
  deriving Repr, BEq, DecidableEq

/-- Ordered tensor product (⊗) of gate outcomes.
    If any gate rejects, the product rejects.
    If any gate holds (and none reject), the product holds.
    Only if all gates admit does the product admit. -/
def gateCompose (g1 g2 : GateOutcome) : GateOutcome :=
  match g1 with
  | .reject => .reject
  | .hold   => match g2 with | .reject => .reject | _ => .hold
  | .admit  => g2

/-- The tensor product extends to a list of gates. -/
def gateComposeList (gs : List GateOutcome) : GateOutcome :=
  gs.foldl gateCompose .admit

/-- Resolution delta components for the 0D→16D throat shortcut. -/
structure ResolutionDelta where
  manifoldDistance : Int  -- D_m: full manifold traversal distance
  throatDistance   : Int  -- D_t: shortcut throat distance
  shellError       : Int  -- E_s: recoverable shell baseline error
  projectedError   : Int  -- E_p: new residual from the projection
  deriving Repr, BEq, DecidableEq

/-- Compute the net resolution change.
    Positive = improvement (throat saves more than projection costs).
    Zero = break-even.
    Negative = decreased resolution. -/
def deltaResolution (r : ResolutionDelta) : Int :=
  (r.manifoldDistance - r.throatDistance) + r.shellError - r.projectedError

/-- Final interaction outcome after applying the decision law. -/
inductive InteractionOutcome where
  | improved    -- Γ = ADMIT and ΔR > 0
  | unchanged   -- Γ = ADMIT and ΔR = 0
  | decreased   -- Γ = ADMIT and ΔR < 0
  | hold        -- Γ = HOLD
  | reject      -- Γ = REJECT
  deriving Repr, BEq, DecidableEq

/-- The total interaction pair: (gate tensor, resolution delta). -/
structure TotalInteraction where
  gateTensor : GateOutcome
  deltaR     : ResolutionDelta
  deriving Repr

/-- Apply the decision law to the total interaction pair.
    If Γ = REJECT → REJECT
    If Γ = HOLD    → HOLD
    If Γ = ADMIT   → sign(ΔR) determines IMPROVED/UNCHANGED/DECREASED -/
def interact (ti : TotalInteraction) : InteractionOutcome :=
  match ti.gateTensor with
  | .reject => .reject
  | .hold   => .hold
  | .admit  =>
      let d := deltaResolution ti.deltaR
      if d > 0 then .improved
      else if d == 0 then .unchanged
      else .decreased

/-- Canonical gate tensor: all five gates admit. -/
def allAdmit : GateOutcome := .admit

/-- Fixture: the throat saves distance and shell error exceeds projection cost. -/
def positiveDeltaFixture : ResolutionDelta :=
  { manifoldDistance := 10
  , throatDistance   := 3
  , shellError       := 2
  , projectedError   := 1 }

/-- Fixture: the throat costs more than it saves. -/
def negativeDeltaFixture : ResolutionDelta :=
  { positiveDeltaFixture with throatDistance := 15, projectedError := 5 }

/-- Fixture: break-even. -/
def zeroDeltaFixture : ResolutionDelta :=
  { positiveDeltaFixture with throatDistance := 11, projectedError := 1 }

/-- Total interaction with all gates open and positive delta → improved. -/
def improvedInteractionFixture : TotalInteraction :=
  { gateTensor := allAdmit, deltaR := positiveDeltaFixture }

/-- Total interaction with all gates open and negative delta → decreased. -/
def decreasedInteractionFixture : TotalInteraction :=
  { gateTensor := allAdmit, deltaR := negativeDeltaFixture }

/-- Total interaction with a reject in the gate tensor → reject. -/
def rejectedInteractionFixture : TotalInteraction :=
  { gateTensor := .reject, deltaR := positiveDeltaFixture }

/-- Total interaction with a hold in the gate tensor → hold (ΔR ignored). -/
def heldInteractionFixture : TotalInteraction :=
  { gateTensor := .hold, deltaR := positiveDeltaFixture }

theorem improvedFixture_yields_improved :
    interact improvedInteractionFixture = .improved := by
  native_decide

theorem decreasedFixture_yields_decreased :
    interact decreasedInteractionFixture = .decreased := by
  native_decide

theorem rejectedFixture_yields_reject :
    interact rejectedInteractionFixture = .reject := by
  native_decide

theorem heldFixture_yields_hold :
    interact heldInteractionFixture = .hold := by
  native_decide

theorem gateCompose_reject_dominates_left :
    gateCompose .reject .admit = .reject := by rfl

theorem gateCompose_reject_dominates_right :
    gateCompose .admit .reject = .reject := by rfl

theorem gateCompose_hold_blocks_admit :
    gateCompose .hold .admit = .hold := by rfl

theorem gateCompose_admit_neutral :
    gateCompose .admit .admit = .admit := by rfl

theorem deltaResolution_positive_fixture :
    deltaResolution positiveDeltaFixture = 8 := by native_decide

theorem deltaResolution_negative_fixture :
    deltaResolution negativeDeltaFixture = -8 := by native_decide

theorem deltaResolution_zero_fixture :
    deltaResolution zeroDeltaFixture = 0 := by native_decide

theorem folded16Fixture_admits :
    decideFoldedPoint folded16Fixture = .admit := by
  native_decide

theorem missingReplayFixture_holds :
    decideFoldedPoint missingReplayFixture = .hold := by
  native_decide

theorem overCapFixture_holds :
    decideFoldedPoint overCapFixture = .hold := by
  native_decide

theorem ordinaryPointFixture_rejects :
    decideFoldedPoint ordinaryPointFixture = .reject := by
  native_decide

theorem folded16Fixture_loopsBack :
    decideLoopback folded16Fixture = .loopback := by
  native_decide

theorem noPermeabilityFixture_holdsLoopback :
    decideLoopback noPermeabilityFixture = .hold := by
  native_decide

theorem ordinaryPointFixture_holdsLoopback :
    decideLoopback ordinaryPointFixture = .hold := by
  native_decide

theorem mengerConservedFixture_conserved :
    decideConservation mengerConservedFixture = .conserved := by
  native_decide

theorem brokenConservationFixture_rejects :
    decideConservation brokenConservationFixture = .reject := by
  native_decide

theorem missingMengerSeedFixture_holds :
    decideConservation missingMengerSeedFixture = .hold := by
  native_decide

#eval isFoldedPoint folded16Fixture
#eval decideFoldedPoint folded16Fixture
#eval decideFoldedPoint missingReplayFixture
#eval decideFoldedPoint ordinaryPointFixture
#eval decideLoopback folded16Fixture
#eval decideLoopback noPermeabilityFixture
#eval decideConservation mengerConservedFixture
#eval decideConservation brokenConservationFixture

#eval gateCompose .reject .admit
#eval gateCompose .hold .admit
#eval gateCompose .admit .admit
#eval gateComposeList [.admit, .admit, .admit]
#eval gateComposeList [.admit, .hold, .admit]
#eval gateComposeList [.admit, .reject, .admit]
#eval deltaResolution positiveDeltaFixture
#eval deltaResolution negativeDeltaFixture
#eval deltaResolution zeroDeltaFixture
#eval interact improvedInteractionFixture
#eval interact decreasedInteractionFixture
#eval interact rejectedInteractionFixture
#eval interact heldInteractionFixture

end Semantics.FoldedPointManifold
