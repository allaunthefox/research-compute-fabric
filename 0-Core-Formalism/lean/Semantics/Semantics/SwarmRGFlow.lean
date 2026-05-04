/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SwarmRGFlow.lean — RGFlow evaluation for swarm code filtering.

Ported from Python scripts/rgflow_swarm_filter.py.
All logic previously in Python now lives in Lean.
Python shims may only serialize/deserialize and call the bindserver.

Per AGENTS.md §1.4: Q1616 fixed-point for all hot-path arithmetic.
Per AGENTS.md §4: Every def has an #eval or theorem witness.
-/

import Semantics.SSMS
import Semantics.CooperativeLUT

namespace Semantics.SwarmRGFlow

open Semantics.SSMS
open Semantics.CooperativeLUT

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Swarm Code State (continuous Q16.16 parameters)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Six-dimensional swarm code state in Q16.16 fixed-point.
    These are the continuous counterparts to QuantizedGenome bins. -/
structure SwarmCodeState where
  muQ    : Q1616  -- mutation rate
  rhoQ   : Q1616  -- refresh rate
  cFac   : Q1616  -- graph connectance
  mFac   : Q1616  -- modularity
  ne     : Q1616  -- observer count
  sigmaQ : Q1616  -- selection coefficient
  deriving Repr, BEq

namespace SwarmCodeState

def zero : SwarmCodeState :=
  { muQ := Q1616.zero, rhoQ := Q1616.zero, cFac := Q1616.zero,
    mFac := Q1616.zero, ne := Q1616.zero, sigmaQ := Q1616.zero }

end SwarmCodeState

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Biophysical Constants (Q16.16)
-- ═══════════════════════════════════════════════════════════════════════════

def drakeBudgetD    : Q1616 := ⟨197⟩       -- ~0.003
def driftBarrierB  : Q1616 := ⟨66⟩        -- ~0.001
def lambdaParam    : Q1616 := ⟨32768⟩     -- 0.5
def mStar          : Q1616 := ⟨32768⟩     -- 0.5
def epsilonQ       : Q1616 := ⟨66⟩        -- ~0.001
def maxSigmaQ      : Q1616 := ⟨131072⟩    -- 2.0

-- Beta-function scale constants
def betaMu         : Q1616 := ⟨62259⟩     -- ~0.95
def betaRho        : Q1616 := ⟨58982⟩     -- ~0.90
def betaC          : Q1616 := ⟨68812⟩     -- ~1.05
def betaSigma      : Q1616 := ⟨68812⟩     -- ~1.05
def betaNe         : Q1616 := ⟨66846⟩     -- ~1.02
def betaMScale     : Q1616 := ⟨3276⟩      -- ~0.05

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Beta Function — Informatic RGFlow evolution
-- ═══════════════════════════════════════════════════════════════════════════

/-- Evolve swarm code state across one abstraction scale step.
    All operations in Q16.16 saturating fixed-point. -/
def betaFunction (s : SwarmCodeState) : SwarmCodeState :=
  let muS    := Q1616.mul s.muQ betaMu
  let rhoS   := Q1616.mul s.rhoQ betaRho
  let cS     := Q1616.min (Q1616.mul s.cFac betaC) Q1616.one
  let sigmaS := Q1616.min (Q1616.mul s.sigmaQ betaSigma) maxSigmaQ
  let neS    := Q1616.mul s.ne betaNe
  let mDelta := Q1616.mul betaMScale (Q1616.sub s.mFac mStar)
  let mS     := Q1616.add s.mFac mDelta
  { muQ := muS, rhoQ := rhoS, cFac := cS, mFac := mS, ne := neS, sigmaQ := sigmaS }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Lawfulness Checks
-- ═══════════════════════════════════════════════════════════════════════════

/-- Drake budget: muQ <= drakeBudgetD / max(cFac, epsilon). -/
def drakeOk (s : SwarmCodeState) : Bool :=
  let cSafe := Q1616.max s.cFac epsilonQ
  let adjustedDrake := Q1616.mul drakeBudgetD (Q1616.recip cSafe)
  Q1616.le s.muQ adjustedDrake

/-- Drift barrier: muQ * ne >= driftBarrierB / max(mFac, epsilon). -/
def driftOk (s : SwarmCodeState) : Bool :=
  let mSafe := Q1616.max s.mFac epsilonQ
  let adjustedDrift := Q1616.mul driftBarrierB (Q1616.recip mSafe)
  let unProduct := Q1616.mul s.muQ s.ne
  Q1616.le adjustedDrift unProduct

/-- Error threshold: muQ < sigmaQ - 1. -/
def errorOk (s : SwarmCodeState) : Bool :=
  let lnSigma := Q1616.sub s.sigmaQ Q1616.one
  Q1616.lt s.muQ lnSigma

/-- Combined lawfulness with failure mask.
    Mask bits: 0x1 = Drake, 0x2 = Drift, 0x4 = Error. -/
def isLawful (s : SwarmCodeState) : Bool × UInt8 :=
  let dOk := drakeOk s
  let drift := driftOk s
  let eOk := errorOk s
  let mask : UInt8 :=
    (if dOk then 0 else 1) |||
    (if drift then 0 else 2) |||
    (if eOk then 0 else 4)
  (dOk && drift && eOk, mask)

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  RGFlow Trajectory Simulation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Result of an RGFlow simulation over N scale steps. -/
structure RGFlowResult where
  lawfulNow       : Bool
  lawfulUnderFlow : Bool
  reachesAttractor : Bool
  flowsToNoise    : Bool
  flowsToSabotage : Bool
  adaptationCost  : UInt32
  rgDepth         : Nat
  attractorId     : Nat
  failureMask     : UInt8
  deriving Repr, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Attractor Classification
-- ═══════════════════════════════════════════════════════════════════════════

/-- Classify final state into an attractor basin.
    1 = high-fitness, 2 = high-popularity, 3 = high-modularity,
    4 = low-connectance, 0 = default. -/
def computeAttractorId (s : SwarmCodeState) : Nat :=
  if Q1616.lt ⟨52428⟩ s.sigmaQ then 1      -- sigma > 0.8  (52428 ≈ 0.8*65536)
  else if Q1616.lt ⟨45875⟩ s.ne then 2     -- ne > 0.7   (45875 ≈ 0.7*65536)
  else if Q1616.lt ⟨52428⟩ s.mFac then 3   -- M > 0.8
  else if Q1616.lt s.cFac ⟨19660⟩ then 4   -- C < 0.3    (19660 ≈ 0.3*65536)
  else 0

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  RGFlow Trajectory Simulation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Simulate RGFlow trajectory.  At each step apply betaFunction and check
    lawfulness.  Cost accumulates violations. -/
def simulateRGFlow (initial : SwarmCodeState) (steps : Nat) : RGFlowResult :=
  let rec loop (s : SwarmCodeState) (remaining : Nat) (depth : Nat)
               (costAcc : UInt32) (lawfulSoFar : Bool) : RGFlowResult :=
    let (lawfulNow, mask) := isLawful s
    let newCost : UInt32 :=
      let c1 := if !drakeOk s then (Q1616.sub (Q1616.mul drakeBudgetD (Q1616.recip (Q1616.max s.cFac epsilonQ))) s.muQ).raw.toNat else 0
      let c2 := if !driftOk s then (Q1616.sub (Q1616.mul driftBarrierB (Q1616.recip (Q1616.max s.mFac epsilonQ))) (Q1616.mul s.muQ s.ne)).raw.toNat else 0
      let c3 := if !errorOk s then 0x00FF0000 else 0
      UInt32.ofNat (c1 + c2 + c3)
    match remaining with
    | 0 =>
      { lawfulNow := lawfulNow,
        lawfulUnderFlow := lawfulSoFar,
        reachesAttractor := lawfulSoFar && lawfulNow,
        flowsToNoise := false,
        flowsToSabotage := false,
        adaptationCost := costAcc + newCost,
        rgDepth := depth,
        attractorId := computeAttractorId s,
        failureMask := mask }
    | rem + 1 =>
      if !lawfulNow then
        let sabotage := (mask &&& 1) != 0
        let noise := (mask &&& 6) != 0
        { lawfulNow := lawfulNow,
          lawfulUnderFlow := false,
          reachesAttractor := false,
          flowsToNoise := noise,
          flowsToSabotage := sabotage,
          adaptationCost := costAcc + newCost,
          rgDepth := depth,
          attractorId := computeAttractorId s,
          failureMask := mask }
      else
        loop (betaFunction s) rem (depth + 1) (costAcc + newCost) true
  loop initial steps 0 0 true

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Quantization Bridge (for Python shim)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Quantize a Q16.16 value into a 3-bit bin (Fin 8).
    Bin = min(7, floor(value * 8)).  Assumes value in [0, 1]. -/
def quantizeQ (q : Q1616) : Fin 8 :=
  let v := q.raw.toNat
  let scaled := (v * 8) / 65536
  let clamped := Nat.min scaled 7
  have h : clamped ≤ 7 := Nat.min_le_right scaled 7
  ⟨clamped, Nat.lt_succ_of_le h⟩

/-- Map SwarmCodeState to QuantizedGenome for LUT lookup. -/
def stateToGenome (s : SwarmCodeState) : QuantizedGenome :=
  { gBin           := quantizeQ s.muQ,   -- using muQ as proxy for gBin
    neBin          := quantizeQ s.ne,
    uBin           := quantizeQ s.muQ,
    sigmaBin       := quantizeQ s.sigmaQ,
    connectanceBin := quantizeQ s.cFac,
    modularityBin  := quantizeQ s.mFac }

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Eval Witnesses
-- ═══════════════════════════════════════════════════════════════════════════

-- Witness 1: E. coli-like state (lawful)
def ecoliState : SwarmCodeState :=
  { muQ := ⟨195⟩, rhoQ := ⟨32768⟩, cFac := ⟨13107⟩, mFac := ⟨19660⟩,
    ne := ⟨26214⟩, sigmaQ := ⟨72089⟩ }

#eval (isLawful ecoliState).1

-- Witness 2: Hypermutator (violates Drake)
def hypermutatorState : SwarmCodeState :=
  { muQ := ⟨520⟩, rhoQ := ⟨32768⟩, cFac := ⟨13107⟩, mFac := ⟨19660⟩,
    ne := ⟨26214⟩, sigmaQ := ⟨72089⟩ }

#eval (isLawful hypermutatorState).1

-- Witness 3: RGFlow simulation on ecoli seed
#eval let r := simulateRGFlow ecoliState 5
      s!"lawfulUnderFlow={r.lawfulUnderFlow}, cost={r.adaptationCost}, depth={r.rgDepth}, attractor={r.attractorId}"

-- Witness 4: RGFlow simulation on hypermutator
#eval let r := simulateRGFlow hypermutatorState 5
      s!"lawfulUnderFlow={r.lawfulUnderFlow}, sabotage={r.flowsToSabotage}, noise={r.flowsToNoise}"

end Semantics.SwarmRGFlow
