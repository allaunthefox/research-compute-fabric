/-
QuantumFoamBoundary.lean — bounded fluctuation guard around U0

Quantum foam is modeled here as an accounting boundary around the zero layer,
not as a promotion rule. Exact neutral closure still belongs to U0. Foam only
classifies sub-resolution, unreceipted, or stochastic jitter as HOLD.
-/

namespace Semantics.QuantumFoamBoundary

/-- Coarse scale band for an accounting fluctuation. -/
inductive FoamScale where
  | deterministic
  | measurementFloor
  | planckAnalogy
  | subResolution
  deriving Repr, BEq, DecidableEq

/-- Decision emitted by the foam boundary. -/
inductive FoamDecision where
  | exactClosure
  | holdFoam
  | rejectClaim
  deriving Repr, BEq, DecidableEq

/-- Minimal foam-boundary sample.

`netCharge` is the recomputed visible + Underverse + sink charge.
`jitterBound` is the declared symmetric tolerance for a measurement/noise floor.
`replayReceiptPresent` distinguishes exact U0 closure from a balanced-looking
but unreceipted claim.
-/
structure FoamSample where
  scale : FoamScale
  netCharge : Int
  jitterBound : Nat
  replayReceiptPresent : Bool
  deriving Repr, BEq, DecidableEq

/-- A signed integer lies inside the declared symmetric jitter band. -/
def withinJitter (s : FoamSample) : Bool :=
  s.netCharge.natAbs <= s.jitterBound

/-- Foam boundary classifier.

Exact zero with replay belongs to `exactClosure`.
Nonzero values inside a declared jitter band are HOLD, never ADMIT.
Nonzero values outside the band reject the zero/foam claim.
-/
def decideFoamBoundary (s : FoamSample) : FoamDecision :=
  if s.netCharge == 0 && s.replayReceiptPresent then .exactClosure
  else if withinJitter s then .holdFoam
  else .rejectClaim

def exactZeroFixture : FoamSample :=
  { scale := .deterministic
  , netCharge := 0
  , jitterBound := 0
  , replayReceiptPresent := true
  }

def foamJitterFixture : FoamSample :=
  { scale := .subResolution
  , netCharge := 1
  , jitterBound := 2
  , replayReceiptPresent := false
  }

def outOfBandFixture : FoamSample :=
  { scale := .measurementFloor
  , netCharge := 5
  , jitterBound := 2
  , replayReceiptPresent := false
  }

theorem exactZeroFixture_closes :
    decideFoamBoundary exactZeroFixture = .exactClosure := by
  rfl

theorem foamJitterFixture_holds :
    decideFoamBoundary foamJitterFixture = .holdFoam := by
  rfl

theorem outOfBandFixture_rejects :
    decideFoamBoundary outOfBandFixture = .rejectClaim := by
  rfl

#eval decideFoamBoundary exactZeroFixture
#eval decideFoamBoundary foamJitterFixture
#eval decideFoamBoundary outOfBandFixture

end Semantics.QuantumFoamBoundary
