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

open Semantics.FixedPoint

def phaseModulus : Nat := 65536
def goldenAngleStep : Nat := 40503

/--
Encode a Nat modulo `phaseModulus` (65536) into a `Q0_16` value by treating
the low 16 bits as a two's-complement bit pattern.  Values in [0, 32767] map
to themselves; values in [32768, 65535] map to the corresponding negative
signed integer (m - 65536).
-/
def q0OfNatMod (n : Nat) : Q0_16 :=
  let m := n % phaseModulus
  if h : m ≤ 32767 then
    ⟨(m : Int), by
      have hub : (m : Int) ≤ 32767 := by exact_mod_cast h
      refine ⟨?_, ?_⟩
      · show q0_16MinRaw ≤ (m : Int)
        unfold q0_16MinRaw; omega
      · show (m : Int) ≤ q0_16MaxRaw
        unfold q0_16MaxRaw; omega⟩
  else
    ⟨(m : Int) - 65536, by
      have hub : m < phaseModulus := Nat.mod_lt _ (by decide)
      have hub' : (m : Int) < 65536 := by exact_mod_cast hub
      have hge : (m : Int) ≥ 32768 := by
        have : ¬ m ≤ 32767 := h
        have : m ≥ 32768 := by omega
        exact_mod_cast this
      refine ⟨?_, ?_⟩
      · show q0_16MinRaw ≤ (m : Int) - 65536
        unfold q0_16MinRaw; omega
      · show (m : Int) - 65536 ≤ q0_16MaxRaw
        unfold q0_16MaxRaw; omega⟩

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

/--
Extract the unsigned modular phase in [0, phaseModulus).  Re-interprets the
signed Q0_16 value as a 16-bit two's-complement bit pattern.
-/
def rawPhase (sample : PhaseSample) : Nat :=
  let v := sample.phase.val
  if v ≥ 0 then v.toNat else (v + 65536).toNat

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
