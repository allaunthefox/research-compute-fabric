/-
UnderverseZeroLayer.lean — explicit neutral closure accounting

The zero layer is the receipt boundary between observable accounting and
Underverse/complement accounting. It prevents "missing" or "opposite" terms
from becoming free variables: a neutral event is admitted only when the net
charge closes exactly and the replay receipt is present.

The genus-3 case is deliberately a checked assumption surface, not a topology
proof. Genus 3 may be the selected chart, but zero charge still has to be
declared and replayed.
-/

namespace Semantics.UnderverseZeroLayer

/-- Which chart the neutral event is being checked in. -/
inductive ChargeChart where
  | ordinary
  | genus3
  | mirror
  | antiBaryonic
  deriving Repr, BEq, DecidableEq

/-- Terminal decision for the zero layer. -/
inductive ZeroDecision where
  | admit
  | hold
  | reject
  deriving Repr, BEq, DecidableEq

/-- Minimal zero-layer event.

`observableCharge` is the visible/accounted side.
`underverseCharge` is the complement, inverse, hidden, or Underverse side.
`sinkCharge` is a typed loss/annihilation/sink sidecar.

The event is neutral only when all three sum to zero and replay is present.
-/
structure ZeroLayerEvent where
  chart : ChargeChart
  genus : Nat
  observableCharge : Int
  underverseCharge : Int
  sinkCharge : Int
  replayReceiptPresent : Bool
  deriving Repr, BEq, DecidableEq

/-- Net accounting charge across observable, Underverse, and sink lanes. -/
def netCharge (e : ZeroLayerEvent) : Int :=
  e.observableCharge + e.underverseCharge + e.sinkCharge

/-- The neutral closure predicate. -/
def closesNeutral (e : ZeroLayerEvent) : Bool :=
  netCharge e == 0 && e.replayReceiptPresent

/-- Genus-3 zero-charge assumption is explicit: genus=3, chart=genus3, net=0,
and the replay receipt is present. -/
def genus3ZeroChargeEvent (e : ZeroLayerEvent) : Bool :=
  e.chart == .genus3 && e.genus == 3 && closesNeutral e

/-- Decision gate for neutral closure. -/
def decideZeroLayer (e : ZeroLayerEvent) : ZeroDecision :=
  if closesNeutral e then .admit
  else if netCharge e == 0 then .hold
  else .reject

/-- Canonical fixture: visible +1, Underverse -1, no sink, genus-3 chart. -/
def genus3BalancedFixture : ZeroLayerEvent :=
  { chart := .genus3
  , genus := 3
  , observableCharge := 1
  , underverseCharge := -1
  , sinkCharge := 0
  , replayReceiptPresent := true
  }

/-- Same charges, but no replay receipt: balance is only HOLD. -/
def missingReplayFixture : ZeroLayerEvent :=
  { genus3BalancedFixture with replayReceiptPresent := false }

/-- Nonzero net charge rejects the zero-layer claim. -/
def nonzeroChargeFixture : ZeroLayerEvent :=
  { genus3BalancedFixture with underverseCharge := 0 }

theorem genus3BalancedFixture_closes :
    genus3ZeroChargeEvent genus3BalancedFixture = true := by
  rfl

theorem missingReplayFixture_holds :
    decideZeroLayer missingReplayFixture = .hold := by
  rfl

theorem nonzeroChargeFixture_rejects :
    decideZeroLayer nonzeroChargeFixture = .reject := by
  rfl

#eval genus3ZeroChargeEvent genus3BalancedFixture
#eval decideZeroLayer missingReplayFixture
#eval decideZeroLayer nonzeroChargeFixture

end Semantics.UnderverseZeroLayer
