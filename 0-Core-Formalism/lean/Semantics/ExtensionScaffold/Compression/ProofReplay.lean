namespace ExtensionScaffold.Compression.ProofReplay

/-!
# Proof replay fixture for compression admission

This extension module is a tiny proof-boundary fixture for the replay queue.
It does not prove a compression benchmark. It proves only that the local
admission predicate accepts an exact positive-gain fixture and rejects fixtures
that fail byte law or exact replay.
-/

/-- Counted byte fields for one lossless reconstruction candidate. -/
structure ReplayCandidate where
  rawBytes : Nat
  dictionaryBytes : Nat
  kernelBytes : Nat
  thetaBytes : Nat
  residualBytes : Nat
  protocolBytes : Nat
  exactReplay : Bool
  deriving Repr, DecidableEq

/-- The counted reconstruction core size. -/
def countedBytes (x : ReplayCandidate) : Nat :=
  x.dictionaryBytes + x.kernelBytes + x.thetaBytes + x.residualBytes + x.protocolBytes

/-- Positive byte law: the counted reconstruction is smaller than the raw payload. -/
def byteGainPositive (x : ReplayCandidate) : Bool :=
  countedBytes x < x.rawBytes

/-- Compression admission requires exact replay and positive byte law. -/
def admitCandidate (x : ReplayCandidate) : Bool :=
  x.exactReplay && byteGainPositive x

/-- A repeated generator fixture that pays byte law. -/
def repeatKernelFixture : ReplayCandidate := {
  rawBytes := 256
  dictionaryBytes := 32
  kernelBytes := 18
  thetaBytes := 20
  residualBytes := 0
  protocolBytes := 24
  exactReplay := true
}

/-- A candidate that repairs exactly but pays too much residual. -/
def residualHeavyFixture : ReplayCandidate := {
  rawBytes := 256
  dictionaryBytes := 32
  kernelBytes := 18
  thetaBytes := 20
  residualBytes := 200
  protocolBytes := 24
  exactReplay := true
}

/-- A compact candidate that is still inadmissible because replay is not exact. -/
def nonExactFixture : ReplayCandidate := {
  rawBytes := 256
  dictionaryBytes := 32
  kernelBytes := 18
  thetaBytes := 20
  residualBytes := 0
  protocolBytes := 24
  exactReplay := false
}

theorem repeatKernelFixtureExact : repeatKernelFixture.exactReplay = true := by
  native_decide

theorem repeatKernelFixturePaysByteLaw : byteGainPositive repeatKernelFixture = true := by
  native_decide

theorem repeatKernelFixtureAdmitted : admitCandidate repeatKernelFixture = true := by
  native_decide

theorem residualHeavyFixtureRejected : admitCandidate residualHeavyFixture = false := by
  native_decide

theorem nonExactFixtureRejected : admitCandidate nonExactFixture = false := by
  native_decide

-- Witnesses expected by the shim receipt.
#eval countedBytes repeatKernelFixture
#eval byteGainPositive repeatKernelFixture
#eval admitCandidate repeatKernelFixture
#eval admitCandidate residualHeavyFixture
#eval admitCandidate nonExactFixture

end ExtensionScaffold.Compression.ProofReplay
