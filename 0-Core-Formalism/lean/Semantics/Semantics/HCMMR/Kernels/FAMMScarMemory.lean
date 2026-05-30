/-
FAMMScarMemory.lean — FAMM frustration/scar memory kernel wrapped around field steps.

Φ_FAMM = exp[-γ(Σ² + I_lock + Δφ)], where Σ² = accumulated scar energy,
I_lock = interference penalty, Δφ = phase mismatch. High frustration suppresses
step magnitude; low frustration permits aggressive exploration.
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint
import Semantics.Q16_16Numerics

namespace Semantics.HCMMR.Kernels.FAMMScarMemory

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

structure FAMMScar where
  frustrationEnergy  : Q16_16
  interferenceLock   : Q16_16
  phaseMismatch      : Q16_16
  dampingCoefficient : Q16_16
  scarHistory        : List String
  deriving Repr, BEq, DecidableEq, Inhabited

/-- FAMM bias using rigorous exponential.
    Uses Q16_16Numerics.expNeg for proper precision. -/
def fammBias (scar : FAMMScar) : Q16_16 :=
  let sigma2 := scar.frustrationEnergy
  let iLock := scar.interferenceLock
  let dPhi := scar.phaseMismatch
  let arg := scar.dampingCoefficient * (sigma2 + iLock + dPhi)
  Semantics.Q16_16Numerics.expNeg arg

def applyFAMMBias (delta : Q16_16) (scar : FAMMScar) : Q16_16 :=
  let bias := fammBias scar
  delta * bias

def recordScar (scar : FAMMScar) (event : String) (newResidual : Q16_16) : FAMMScar :=
  let energyDelta := Q16_16.sat01 newResidual
  { frustrationEnergy  := scar.frustrationEnergy + energyDelta
  , interferenceLock   := scar.interferenceLock
  , phaseMismatch      := scar.phaseMismatch + energyDelta
  , dampingCoefficient := scar.dampingCoefficient
  , scarHistory        := event :: scar.scarHistory
  }

def resetFrustration (scar : FAMMScar) (decayFactor : Q16_16) : FAMMScar :=
  { frustrationEnergy  := scar.frustrationEnergy * decayFactor
  , interferenceLock   := scar.interferenceLock * decayFactor
  , phaseMismatch      := scar.phaseMismatch * decayFactor
  , dampingCoefficient := scar.dampingCoefficient
  , scarHistory        := scar.scarHistory
  }

def fammMemoryGate : Gate :=
  { name     := "FAMMScarMemory"
  , required := false
  , score    := Q16_16.one
  , verdict  := GateVerdict.admit
  }

def fixtureScar : FAMMScar :=
  { frustrationEnergy  := Q16_16.one
  , interferenceLock   := Q16_16.zero
  , phaseMismatch      := Q16_16.zero
  , dampingCoefficient := Q16_16.one
  , scarHistory        := ["initial"]
  }

def fixtureHighScar : FAMMScar :=
  { frustrationEnergy  := Q16_16.ofInt 10
  , interferenceLock   := Q16_16.ofInt 3
  , phaseMismatch      := Q16_16.one
  , dampingCoefficient := Q16_16.two
  , scarHistory        := ["collision_1", "rejection_2", "phase_error_3"]
  }

theorem famm_gate_name_correct : fammMemoryGate.name = "FAMMScarMemory" := by
  rfl

theorem famm_gate_verdict_admits : fammMemoryGate.verdict = GateVerdict.admit := by
  rfl

theorem fixtureScar_initial_history : fixtureScar.scarHistory.length = 1 := by
  native_decide

theorem fixtureHighScar_history_length : fixtureHighScar.scarHistory.length = 3 := by
  native_decide

theorem reset_does_not_change_history_length : (resetFrustration fixtureScar (Q16_16.ofRatio 1 2)).scarHistory.length = fixtureScar.scarHistory.length := by
  native_decide

theorem record_extends_history : (recordScar fixtureScar "collision_at_3" Q16_16.one).scarHistory.length = fixtureScar.scarHistory.length + 1 := by
  native_decide

#eval fammBias fixtureScar
#eval fammBias fixtureHighScar
#eval applyFAMMBias (Q16_16.ofInt 7) fixtureScar
#eval applyFAMMBias (Q16_16.ofInt 7) fixtureHighScar
#eval recordScar fixtureScar "gate_hold" (Q16_16.ofRatio 3 10)
#eval resetFrustration fixtureHighScar (Q16_16.ofRatio 1 4)
#eval fammMemoryGate

end Semantics.HCMMR.Kernels.FAMMScarMemory
