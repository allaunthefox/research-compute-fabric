/-
Copyright (c) 2026 Sovereign Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NUVMAP - Non-Uniform Vector Map Projection
Fixed-point orthogonal projection structure for spectral addressing.
-/

import Semantics.FixedPoint
import Semantics.S3C
import Mathlib.Tactic.Ring

namespace Semantics

/-- UV coordinate in 2D projected space
    u: distance-based albedo scale (t×1000)
    v: spectral frequency index -/
structure UV where
  u : UInt32
  v : UInt32
deriving Repr, DecidableEq, BEq, Inhabited

/-- NUVMAP projection structure
    Fixed-point orthogonal basis projection with energy conservation -/
structure NUVMAP where
  uAxis : Q16_16  -- distance scaling factor
  vAxis : Q16_16  -- spectral scaling factor
  projection : List Q16_16  -- Q^T · state (orthogonal basis projection)
  energy : Q16_16  -- preserved energy after projection
deriving Repr, DecidableEq, BEq, Inhabited

/-- High-dimensional state to be projected -/
structure HighDimState where
  dimensions : Nat
  coefficients : List Q16_16
  energy : Q16_16
deriving Repr, DecidableEq, BEq, Inhabited

/-- Project high-dimensional state to UV coordinates using NUVMAP -/
def projectToUV (state : HighDimState) (nmap : NUVMAP) : UV :=
  let uVal := (Q16_16.mul nmap.uAxis state.energy).val
  let vVal := (Q16_16.mul nmap.vAxis state.energy).val
  ⟨uVal, vVal⟩

/-- Compute projection error (information loss) -/
def projectionError (state : HighDimState) (nmap : NUVMAP) : Q16_16 :=
  let projectedEnergy := nmap.energy
  Q16_16.abs (Q16_16.sub state.energy projectedEnergy)

/-- Check if projection preserves energy within tolerance -/
def preservesEnergy (state : HighDimState) (nmap : NUVMAP) (tolerance : Q16_16) : Bool :=
  Q16_16.toFloat (projectionError state nmap) <= Q16_16.toFloat tolerance

/-- Convert a non-negative Q16.16 value to its integer energy cell.
    This is the Lean-side handoff from a continuous wave amplitude into the
    exact S3C shell atlas. Negative signed values are clamped to cell 0. -/
def q16FloorNat (q : Q16_16) : Nat :=
  if q.toInt < 0 then 0 else q.toInt.toNat / Q16_16.scale

/-- Geometry audit produced by the S3C shell codec before a GPE/FAMM step. -/
structure S3CAudit where
  energyCell : Nat
  handles : S3C.ManifoldHandle
  contact : S3C.ThreePointContact
  jScore : S3C.JScore
  emit : Bool
deriving Repr, BEq

/-- Audit a Q16.16 energy density through S3C's integer shell manifold. -/
def auditS3C (energy : Q16_16) : S3CAudit :=
  let cell := q16FloorNat energy
  let handles := S3C.audioToManifold cell
  let contact := S3C.detectContact handles
  let jScore := S3C.computeJScore handles
  let emit := S3C.emissionGate contact jScore
  { energyCell := cell, handles, contact, jScore, emit }

/-- A Lean-audited wave state. The state can only inhabit the regular path when
    the S3C emission gate has accepted its shell geometry. `energy` is the
    audited `|psi|^2` cell carrier; shims may keep `psi` as a display/sample
    coordinate, but S3C control decisions are made from `energy`. -/
structure AtomicWaveState where
  psi : Q16_16
  energy : Q16_16
  audit : S3CAudit
  auditEnergy : audit.energyCell = q16FloorNat energy
  valid : audit.emit = true
deriving Repr

/-- Propose a GPE energy update. `none` is the formal FAMM deferment path: the
    controller must reduce the step, redistribute mass, or route to a lattice
    fallback instead of accepting boundary geometry. -/
def tryAtomicStep (_curr : AtomicWaveState) (nextEnergy : Q16_16) : Option AtomicWaveState :=
  let audit := auditS3C nextEnergy
  if hEmit : audit.emit = true then
    some { psi := nextEnergy, energy := nextEnergy, audit, auditEnergy := rfl, valid := hEmit }
  else
    none

/-- FAMM load weighted by S3C geometry.
    Closed emit gate means critical load. Otherwise, low J-score raises load and
    high J-score near the shell throat lowers scheduling pressure. -/
def fammLoadS3C (psiSq threshold : Q16_16) : Q16_16 :=
  let audit := auditS3C psiSq
  if audit.emit then
    let denom := Q16_16.ofNat (audit.jScore.total + 1)
    let geometricStress := Q16_16.div Q16_16.one denom
    let amplitudeLoad := Q16_16.div psiSq threshold
    Q16_16.sat01 (Q16_16.mul amplitudeLoad (Q16_16.add Q16_16.one geometricStress))
  else
    Q16_16.one

/-- GPE interaction multiplier `1 + kappa/(J+1)`, with hard-wall fallback when
    S3C refuses emission. This is the fixed-point Lean version of the C-side
    `compute_regularized_g` shim. -/
def regularizedGFactor (psiSq kappa hardWall : Q16_16) : Q16_16 :=
  let audit := auditS3C psiSq
  if audit.emit then
    let denom := Q16_16.ofNat (audit.jScore.total + 1)
    Q16_16.add Q16_16.one (Q16_16.div kappa denom)
  else
    hardWall

/-- Governor configuration for the adaptive GPE/S3C integration loop. -/
structure S3CGovernorConfig where
  baseDt : Q16_16
  minDt : Q16_16
  jMax : Nat
  maxRetries : Nat
deriving Repr, BEq

/-- A compact receipt for a governor step. `accepted=false` is the explicit FAMM
    deferment result consumed by shims or drivers. -/
structure S3CGovernorReceipt where
  accepted : Bool
  attempts : Nat
  finalDt : Q16_16
  finalAudit : S3CAudit
deriving Repr, BEq

/-- Conservative default: unit step, 1/256 minimum step, and shell-local J cap. -/
def defaultGovernorConfig : S3CGovernorConfig :=
  { baseDt := Q16_16.one
    minDt := Q16_16.div Q16_16.one (Q16_16.ofNat 256)
    jMax := 16
    maxRetries := 8 }

/-- Scale `dt` by the normalized S3C J-score. High J near a throat permits
    larger steps; low J near a boundary throttles the solver. -/
def geometricDt (audit : S3CAudit) (baseDt : Q16_16) (jMax : Nat) : Q16_16 :=
  if audit.emit then
    if jMax = 0 then
      Q16_16.epsilon
    else
      let cappedJ := Nat.min audit.jScore.total jMax
      Q16_16.satFromNat (baseDt.val.toNat * cappedJ / jMax)
  else
    Q16_16.epsilon

/-- One fixed-point Euler proposal for the audited GPE energy carrier. The force
    term remains a Lean function so the safety controller is independent of a
    specific physical stencil. -/
def proposeWaveStep (state : AtomicWaveState) (dt : Q16_16) (force : Q16_16 → Q16_16) : Q16_16 :=
  Q16_16.add state.energy (Q16_16.mul dt (force state.energy))

/-- Bounded adaptive S3C governor. A failed S3C gate halves `dt` and retries.
    Fuel is explicit, so the controller always terminates and returns a receipt. -/
def adaptiveStepFuel
    (state : AtomicWaveState)
    (dt : Q16_16)
    (force : Q16_16 → Q16_16)
    (fuel : Nat)
    (attempts : Nat := 0) :
    AtomicWaveState × S3CGovernorReceipt :=
  match fuel with
  | 0 =>
      (state,
        { accepted := false
          attempts
          finalDt := dt
          finalAudit := state.audit })
  | fuel' + 1 =>
      let proposedEnergy := proposeWaveStep state dt force
      match tryAtomicStep state proposedEnergy with
      | some nextState =>
          (nextState,
            { accepted := true
              attempts := attempts + 1
              finalDt := dt
              finalAudit := nextState.audit })
      | none =>
          let nextDt := Q16_16.div dt Q16_16.two
          if Q16_16.le nextDt Q16_16.epsilon then
            (state,
              { accepted := false
                attempts := attempts + 1
                finalDt := nextDt
                finalAudit := state.audit })
          else
            adaptiveStepFuel state nextDt force fuel' (attempts + 1)

/-- Full governor entrypoint: first throttle by J-score, then perform bounded
    retry/deferment through `tryAtomicStep`. -/
def adaptiveStep
    (cfg : S3CGovernorConfig)
    (state : AtomicWaveState)
    (force : Q16_16 → Q16_16) :
    AtomicWaveState × S3CGovernorReceipt :=
  let dt := Q16_16.max cfg.minDt (geometricDt state.audit cfg.baseDt cfg.jMax)
  adaptiveStepFuel state dt force cfg.maxRetries

/-- Finite ensemble carrier for the S3C-regularized GPE "hair ball" model.
    A hair is accepted into the ensemble only as an `AtomicWaveState`, so each
    filament already carries its local S3C audit proof. -/
structure HairBallState where
  hairs : List AtomicWaveState
deriving Repr

/-- Executable ensemble predicate used by extraction shims. -/
def allHairsEmit : List AtomicWaveState → Bool
  | [] => true
  | hair :: tail => hair.audit.emit && allHairsEmit tail

/-- Shell-local combing target: the closed-shell throat cell k^2+k. -/
def combTargetCell (audit : S3CAudit) : Nat :=
  audit.handles.handleK * audit.handles.handleK + audit.handles.handleK

/-- Integer cell force toward the shell throat. Positive means the energy cell is
    below the throat, negative means it is above the throat. -/
def combForceCell (audit : S3CAudit) : Int :=
  Int.ofNat (combTargetCell audit) - Int.ofNat audit.energyCell

/-- Valid atomic states have an open S3C emit gate by construction. -/
theorem atomicStateEmitOpen (state : AtomicWaveState) :
    state.audit.emit = true := state.valid

/-- Atomic states carry the audit for their current energy cell. -/
theorem atomicStateAuditMatchesEnergy (state : AtomicWaveState) :
    state.audit.energyCell = q16FloorNat state.energy := state.auditEnergy

/-- Ensemble safety: every hair admitted to the ball is an audited emitting
    state, so the extracted driver never receives a boundary-closed filament as
    an accepted ensemble member. -/
theorem hairballSafety (ball : HairBallState) :
    allHairsEmit ball.hairs = true := by
  induction ball.hairs with
  | nil => rfl
  | cons hair tail ih =>
      simp [allHairsEmit, hair.valid, ih]

/-- Boundary cells close the emit gate and therefore force FAMM deferment. -/
theorem boundaryCellDefers :
    (auditS3C (Q16_16.ofNat 9)).emit = false ∧
    (auditS3C (Q16_16.ofNat 16)).emit = false := by
  native_decide

/-- The k=3 throat cell is accepted by S3C and has J-score 12:
    a=3, b0=3, k=3, so J=(3*3)+0+3. -/
theorem throatCellAccepted :
    (auditS3C (Q16_16.ofNat 12)).emit = true ∧
    (auditS3C (Q16_16.ofNat 12)).jScore.total = 12 := by
  native_decide

/-- The k=3 shell combing target is the accepted throat cell 12. -/
theorem combTargetAtK3Throat :
    combTargetCell (auditS3C (Q16_16.ofNat 12)) = 12 ∧
    combForceCell (auditS3C (Q16_16.ofNat 12)) = 0 := by
  native_decide

/-- Executable fixture for the accepted k=3 throat cell. -/
def throatAtomicState : AtomicWaveState :=
  { psi := Q16_16.ofNat 12
    energy := Q16_16.ofNat 12
    audit := auditS3C (Q16_16.ofNat 12)
    auditEnergy := rfl
    valid := by native_decide }

/-- A positive energy impulse from the throat can propose a boundary cell first;
    the governor therefore retries and returns deferment instead of accepting
    the unsafe shell boundary. -/
theorem adaptiveBoundaryAttemptDefers :
    let receipt := (adaptiveStepFuel throatAtomicState Q16_16.one (fun _ => Q16_16.ofNat 4) 1).snd
    receipt.accepted = false ∧ receipt.attempts = 1 := by
  native_decide

/-- Algebraic conservation at a shell boundary: the upper edge of shell `k`
    and the lower edge of shell `k+1` name the same energy cell. -/
theorem shellBoundaryEnergyInvariant (k : Nat) :
    k * k + (2 * k + 1) = (k + 1) * (k + 1) := by
  ring

/-- At exact square boundaries S3C's closed-shell mass resonance vanishes.
    This is the formal "silent window" used by the driver to defer, re-index,
    and retry from the next shell without accepting boundary evolution. -/
theorem shellBoundaryMassZero (k : Nat) :
    let n := (k + 1) * (k + 1)
    let coords := S3C.shellDecomposition n
    coords.massZero = 0 := by
  dsimp [S3C.shellDecomposition]
  rw [Nat.sqrt_eq (k + 1)]
  simp

/-- The runtime Q16.16 witness for the k=3/k=4 shell boundary closes the
    NUVMATH emit gate. The generic algebra above is unbounded Nat arithmetic;
    this executable audit stays in the fixed-width shim's representable range. -/
theorem shellBoundary16EmitClosed :
    (auditS3C (Q16_16.ofNat 16)).emit = false := by
  native_decide

/-- The same k=3/k=4 boundary has zero closed-shell mass resonance. -/
theorem shellBoundary16MassZero :
    (S3C.shellDecomposition 16).massZero = 0 := by
  native_decide

#eval! (auditS3C (Q16_16.ofNat 12)).jScore.total
#eval! (fammLoadS3C (Q16_16.ofNat 12) (Q16_16.ofNat 100)).val
#eval! (geometricDt (auditS3C (Q16_16.ofNat 12)) Q16_16.one 16).val
#eval! (adaptiveStepFuel throatAtomicState Q16_16.one (fun _ => Q16_16.ofNat 4) 1).snd
#eval! combForceCell (auditS3C (Q16_16.ofNat 12))
#eval! (S3C.shellDecomposition 16).massZero
#eval! (auditS3C (Q16_16.ofNat 16)).emit

end Semantics
