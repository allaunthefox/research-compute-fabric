/-
GoldenAngleEncoding.lean — Golden-Angle Phase Encoding for WaveProbe/WebRTC Surface Sampling

Executable fixed-point phase sampling surface.  The mathematical golden angle is
represented by its Q0.16 turn-step approximation, avoiding noncomputable Real
trigonometry in the verified core.
-/

import Std
import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint

namespace Semantics.GoldenAngleEncoding

def phaseModulus : Nat := 65536
def goldenAngleStep : Nat := 40503

def q0OfNatMod (n : Nat) : Q0_16 :=
  ⟨(n % phaseModulus).toUInt16⟩

structure PhaseSample where
  index : Nat
  phase : Q0_16
  deriving Repr, Inhabited, DecidableEq

def computeGoldenAnglePhase (n : Nat) : PhaseSample :=
  { index := n, phase := q0OfNatMod (n * goldenAngleStep) }

def examplePhases : Array PhaseSample :=
  (List.range 10 |>.map computeGoldenAnglePhase).toArray

structure SphericalSample where
  theta : Q0_16
  phi : Q0_16
  deriving Repr, Inhabited, DecidableEq

def phaseToSpherical (n : Nat) (total : Nat) : SphericalSample :=
  let denom := if total = 0 then 1 else total
  { theta := q0OfNatMod ((n * phaseModulus) / denom)
    phi := (computeGoldenAnglePhase n).phase }

structure WaveProbeSample where
  phase : PhaseSample
  spherical : SphericalSample
  timestamp : Nat
  deriving Repr, Inhabited, DecidableEq

def generateWaveProbeSamples (count : Nat) : Array WaveProbeSample :=
  (List.range count |>.map (fun n =>
    { phase := computeGoldenAnglePhase n
      spherical := phaseToSpherical n count
      timestamp := 0 })).toArray

structure WebRTCSyncState where
  localPhase : PhaseSample
  remotePhase : PhaseSample
  phaseDiff : Nat
  synchronized : Bool
  deriving Repr, Inhabited, DecidableEq

def rawPhase (sample : PhaseSample) : Nat :=
  sample.phase.val.toNat

def cyclicDiff (a b : Nat) : Nat :=
  if a ≤ b then b - a else phaseModulus - (a - b)

def computePhaseDiff (localSample remoteSample : PhaseSample) : WebRTCSyncState :=
  let diff := cyclicDiff (rawPhase localSample) (rawPhase remoteSample)
  { localPhase := localSample
    remotePhase := remoteSample
    phaseDiff := diff
    synchronized := diff = 0 }

theorem computedPhaseKeepsIndex (n : Nat) :
    (computeGoldenAnglePhase n).index = n := by
  rfl

theorem samePhaseSynchronizes (sample : PhaseSample) :
    (computePhaseDiff sample sample).synchronized = true := by
  simp [computePhaseDiff, cyclicDiff, rawPhase]

theorem generatedSamplesHaveZeroTimestamp (count : Nat) :
    (generateWaveProbeSamples count).toList.all (fun s => s.timestamp == 0) = true := by
  simp [generateWaveProbeSamples]

#eval examplePhases.size
#eval rawPhase (computeGoldenAnglePhase 1)
#eval (generateWaveProbeSamples 4).size

end Semantics.GoldenAngleEncoding
