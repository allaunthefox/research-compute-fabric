/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

WavefrontEmitter.lean — Wavefront Emission for Resonant Field Propagation

Defines wavefront emission mechanisms for Resonant Field Propagation (RFP).
State changes emit wavefronts that propagate through the resonant field.

Per AGENTS.md:
  - Q16_16 for scoring (§1.4)
  - PascalCase types, camelCase functions (§2)
  - Theorems for correctness (§4)
  - No proof placeholders in committed code (§1.6)
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Mathlib.Data.Fin.Basic
import Std
import Semantics.RFPFieldSolver

namespace Semantics.WavefrontEmitter

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16_16 Fixed-Point Arithmetic
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited

namespace Q16_16
  def zero : Q16_16 := ⟨0⟩
  def one : Q16_16 := ⟨65536⟩
  def ofFrac (num denom : Nat) : Q16_16 :=
    if denom = 0 then zero else ⟨(num * 65536) / denom⟩
  def add (x y : Q16_16) : Q16_16 := ⟨x.raw + y.raw⟩
  def sub (x y : Q16_16) : Q16_16 := ⟨x.raw - y.raw⟩
  def mul (x y : Q16_16) : Q16_16 := ⟨(x.raw * y.raw) / 65536⟩
end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Wavefront Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure Wavefront where
  emitterId : Nat
  emissionTime : Nat
  amplitude : Q16_16
  frequency : Q16_16
  phase : Q16_16
  position : {row : Nat, col : Nat}
  deriving Repr, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Wavefront Parameters
-- ═══════════════════════════════════════════════════════════════════════════

structure WavefrontParameters where
  defaultAmplitude : Q16_16
  defaultFrequency : Q16_16
  propagationSpeed : Q16_16
  decayRate : Q16_16
  deriving Repr, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  State Change Trigger
-- ═══════════════════════════════════════════════════════════════════════════

structure StateChangeTrigger where
  nodeId : Nat
  tilePosition : {row : Nat, col : Nat}
  oldState : Nat  -- 0=empty, 1=black, 2=captured, 3=ko
  newState : Nat
  triggerTime : Nat
  deriving Repr, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Create Wavefront from State Change
-- ═══════════════════════════════════════════════════════════════════════════

def createWavefrontFromStateChange (trigger : StateChangeTrigger) 
    (params : WavefrontParameters) (currentTime : Nat) : Wavefront :=
  let amplitude := params.defaultAmplitude
      frequency := params.defaultFrequency
      phase := Q16_16.zero
  {
    emitterId := trigger.nodeId,
    emissionTime := currentTime,
    amplitude := amplitude,
    frequency := frequency,
    phase := phase,
    position := trigger.tilePosition
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Compute Wavefront at Position and Time
-- ═══════════════════════════════════════════════════════════════════════════

def computeWavefrontValue (wavefront : Wavefront) (targetPosition : {row : Nat, col : Nat})
    (currentTime : Nat) (params : WavefrontParameters) : Q16_16 :=
  let distance := Nat.max (Nat.abs (targetPosition.row - wavefront.position.row).toNat)
                       (Nat.abs (targetPosition.col - wavefront.position.col).toNat)
      timeSinceEmission := currentTime - wavefront.emissionTime
      waveDistance := Q16_16.mul params.propagationSpeed (⟨timeSinceEmission⟩)
      -- Wavefront reaches target if distance <= waveDistance
      if distance ≤ waveDistance.raw.toNat then
        let decay := Q16_16.mul params.decayRate (⟨distance⟩)
        let decayedAmplitude := Q16_16.sub wavefront.amplitude decay
        let phaseShift := Q16_16.mul wavefront.frequency (⟨distance⟩)
        let oscillation := Q16_16.ofFrac 
          (if (phaseShift.raw / 65536) % 2 = 0 then 1 else -1) 2
        Q16_16.mul decayedAmplitude oscillation
      else
        Q16_16.zero

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Emit Wavefront (Inject into Field)
-- ═══════════════════════════════════════════════════════════════════════════

def emitWavefront (fieldState : RFPFieldSolver.FieldState) (wavefront : Wavefront)
    (currentTime : Nat) (params : WavefrontParameters) : RFPFieldSolver.FieldState :=
  let wavefrontValue := computeWavefrontValue wavefront wavefront.position currentTime params
      newAcceleration := Q16_16.add fieldState.fieldAcceleration wavefrontValue
  {
    fieldValue := fieldState.fieldValue,
    fieldVelocity := fieldState.fieldVelocity,
    fieldAcceleration := newAcceleration
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Initialize Wavefront Parameters
-- ═══════════════════════════════════════════════════════════════════════════

def initializeWavefrontParameters : WavefrontParameters :=
  {
    defaultAmplitude := Q16_16.one,  -- A = 1.0
    defaultFrequency := Q16_16.ofFrac 1 10,  -- ω = 0.1
    propagationSpeed := Q16_16.one,  -- v = 1.0
    decayRate := Q16_16.ofFrac 1 100  -- γ = 0.01
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Create State Change Trigger
-- ═══════════════════════════════════════════════════════════════════════════

def createStateChangeTrigger (nodeId : Nat) (row col oldState newState triggerTime : Nat) 
    : StateChangeTrigger :=
  {
    nodeId := nodeId,
    tilePosition := {row := row, col := col},
    oldState := oldState,
    newState := newState,
    triggerTime := triggerTime
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- ═════════════════════════════════════════════════════════════════════════════
-- §9  #eval Examples
-- ═══════════════════════════════════════════════════════════════════════════

#eval initializeWavefrontParameters
-- Expected: Wavefront parameters with A=1.0, ω=0.1, v=1.0, γ=0.01

#eval createStateChangeTrigger 1 0 0 0 1 1000
-- Expected: State change trigger at (0,0), empty→black at time 1000

#eval createWavefrontFromStateChange 
        (createStateChangeTrigger 1 0 0 0 1 1000)
        initializeWavefrontParameters 1000
-- Expected: Wavefront emitted at (0,0) with default parameters

#eval computeWavefrontValue 
        (createWavefrontFromStateChange 
          (createStateChangeTrigger 1 0 0 0 1 1000)
          initializeWavefrontParameters 1000)
        {row := 1, col := 1} 1005 initializeWavefrontParameters
-- Expected: Wavefront value at (1,1) after 5 time steps

#eval emitWavefront (RFPFieldSolver.initializeFieldState Q16_16.zero)
        (createWavefrontFromStateChange 
          (createStateChangeTrigger 1 0 0 0 1 1000)
          initializeWavefrontParameters 1000)
        1000 initializeWavefrontParameters
-- Expected: Field state with wavefront acceleration injected

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §10  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

end Semantics.WavefrontEmitter
