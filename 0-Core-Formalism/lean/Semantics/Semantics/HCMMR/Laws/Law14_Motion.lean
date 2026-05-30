/-
HCMMR Law14 — Motion Recovery.
Tests whether a 16D object can be projected into a classical trajectory.
The pass condition is ε_motion = ||m·ẍ - F|| → 0 in the Newtonian limit.
When residuals are small, the HCMMR manifold gear-reduces to classical
Newtonian/Lagrangian mechanics.
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint
import Semantics.Q16_16Numerics

namespace Semantics.HCMMR.Law14

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

set_option maxRecDepth 20000

-- ═══════════════════════════════════════════════════════════════════
-- §1  Projected Trajectory
-- ═══════════════════════════════════════════════════════════════════

structure TrajectoryPoint where
  positionX : Q16_16
  positionY : Q16_16
  positionZ : Q16_16
  velocityX : Q16_16
  velocityY : Q16_16
  velocityZ : Q16_16
  accelX    : Q16_16
  accelY    : Q16_16
  accelZ    : Q16_16
  mass      : Q16_16
  forceX    : Q16_16
  forceY    : Q16_16
  forceZ    : Q16_16
  timestamp : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Finite-difference velocity:  v = (p1 - p0) / dt
Applied per spatial dimension.
-/
def computeVelocity (pos0 pos1 dt : Q16_16) : Q16_16 :=
  Q16_16.div (Q16_16.sub pos1 pos0) dt

/--
Finite-difference acceleration:  a = (v1 - v0) / dt
Applied per spatial dimension.
-/
def computeAcceleration (vel0 vel1 dt : Q16_16) : Q16_16 :=
  Q16_16.div (Q16_16.sub vel1 vel0) dt

-- ═══════════════════════════════════════════════════════════════════
-- §2  Newtonian Recovery Tests
-- ═══════════════════════════════════════════════════════════════════

/--
ε_Fma = ||F - m·a|| — Newton's second-law residual.
Returns the per-dimension maximum across x, y, z.
-/
def newtonSecondLawResidual (tp : TrajectoryPoint) : Q16_16 :=
  let maX := Q16_16.mul tp.mass tp.accelX
  let maY := Q16_16.mul tp.mass tp.accelY
  let maZ := Q16_16.mul tp.mass tp.accelZ
  let resX := Q16_16.abs (Q16_16.sub tp.forceX maX)
  let resY := Q16_16.abs (Q16_16.sub tp.forceY maY)
  let resZ := Q16_16.abs (Q16_16.sub tp.forceZ maZ)
  Q16_16.max (Q16_16.max resX resY) resZ

/--
ε_pmv = ||p - m·v|| — momentum residual.
Supplied momentum components are compared against m·v in each dimension.
Returns the maximum residual.
-/
def momentumResidual (px py pz mass vx vy vz : Q16_16) : Q16_16 :=
  let mvx := Q16_16.mul mass vx
  let mvy := Q16_16.mul mass vy
  let mvz := Q16_16.mul mass vz
  let resX := Q16_16.abs (Q16_16.sub px mvx)
  let resY := Q16_16.abs (Q16_16.sub py mvy)
  let resZ := Q16_16.abs (Q16_16.sub pz mvz)
  Q16_16.max (Q16_16.max resX resY) resZ

/--
ε_Ek = ||E_k - ½·m·|v|²|| — kinetic-energy residual.
-/
def kineticEnergyResidual (ek mass vx vy vz : Q16_16) : Q16_16 :=
  let v2 := Q16_16.add (Q16_16.add (Q16_16.mul vx vx) (Q16_16.mul vy vy)) (Q16_16.mul vz vz)
  let halfMV2 := Q16_16.mul (Q16_16.mul (Q16_16.ofRatio 1 2) mass) v2
  Q16_16.abs (Q16_16.sub ek halfMV2)

-- ═══════════════════════════════════════════════════════════════════
-- §3  Lagrangian Recovery
-- ═══════════════════════════════════════════════════════════════════

structure LagrangianState where
  q          : Q16_16
  qdot       : Q16_16
  mass       : Q16_16
  kinetic    : Q16_16
  potential  : Q16_16
  lagrangian : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
ε_EL = ||d/dt(∂L/∂q̇) - ∂L/∂q|| — discrete Euler-Lagrange residual.
Approximates d/dt(m·q̇) ≈ (p₁-p₀)/dt  and  ∂V/∂q ≈ (V₁-V₀)/(q₁-q₀).
The E-L equation demands  dp/dt + ∂V/∂q = 0.
-/
def eulerLagrangeResidual (s0 s1 : LagrangianState) (dt : Q16_16) : Q16_16 :=
  let p0 := Q16_16.mul s0.mass s0.qdot
  let p1 := Q16_16.mul s1.mass s1.qdot
  let dp_dt := Q16_16.div (Q16_16.sub p1 p0) dt
  let dV_dq := if s0.q == s1.q then Q16_16.zero
               else Q16_16.div (Q16_16.sub s1.potential s0.potential) (Q16_16.sub s1.q s0.q)
  Q16_16.abs (Q16_16.add dp_dt dV_dq)

/--
ε_S = ||δS|| — first variation of the action.
Discrete approximation:  δS ≈ (∂L/∂q)·δq·dt.
Uses finite-difference ∂L/∂q between two consecutive states.
-/
def actionResidual (s0 s1 : LagrangianState) (dt δq : Q16_16) : Q16_16 :=
  if s0.q == s1.q then Q16_16.zero
  else
    let dL_dq := Q16_16.div (Q16_16.sub s1.lagrangian s0.lagrangian) (Q16_16.sub s1.q s0.q)
    let deltaS := Q16_16.mul (Q16_16.mul dL_dq δq) dt
    Q16_16.abs deltaS

-- ═══════════════════════════════════════════════════════════════════
-- §4  Motion Recovery Gate
-- ═══════════════════════════════════════════════════════════════════

/--
Motion-recovery gate: admits iff all classical residuals are within
their respective thresholds. Otherwise holds (motion is not classical;
it may be quantum, relativistic, or intrinsically 16D).
-/
def motionRecoveryGate (epsFma epsEL epsS tauFma tauEL tauS : Q16_16) : Gate :=
  let passed := Q16_16.le epsFma tauFma && Q16_16.le epsEL tauEL && Q16_16.le epsS tauS
  { name     := "MotionRecovery"
  , required := true
  , score    := if passed then Q16_16.one else Q16_16.zero
  , verdict  := if passed then GateVerdict.admit else GateVerdict.hold
  }

/--
Emit a diagnostic receipt for every equation whose residual exceeds its
threshold.  Each receipt records the failed equation, residual value,
and a suggested alternate route.
-/
def motionDiagnostic (epsFma epsEL epsS epsPmv epsEk tauFma tauEL tauS tauPmv tauEk : Q16_16)
    (objId : String) (ts : Nat) : List DiagnosticReceipt :=
  let mk (failed : String) (res : Q16_16) (route : String) : DiagnosticReceipt :=
    { object := objId, failedGate := failed,
      residual := ⟨failed, res, "MotionRecovery"⟩,
      alternateRoute := route, timestamp := ts }
  let check (cond : Bool) (failed : String) (res : Q16_16) (route : String)
      (acc : List DiagnosticReceipt) : List DiagnosticReceipt :=
    if cond then acc else mk failed res route :: acc
  let receipts : List DiagnosticReceipt := []
  let receipts := check (Q16_16.le epsFma tauFma) "F=ma"  epsFma "relativistic_correction" receipts
  let receipts := check (Q16_16.le epsEL  tauEL)  "δS=0"  epsEL  "quantum_regime"          receipts
  let receipts := check (Q16_16.le epsS   tauS)   "δS=0"  epsS   "quantum_regime"          receipts
  let receipts := check (Q16_16.le epsPmv tauPmv) "p=mv"  epsPmv "16D_direct"              receipts
  let receipts := check (Q16_16.le epsEk  tauEk)  "E=½mv²" epsEk  "relativistic_correction" receipts
  receipts.reverse

-- ═══════════════════════════════════════════════════════════════════
-- §5  Gear Reduction Check
-- ═══════════════════════════════════════════════════════════════════

/--
Root-sum-square accumulation of projection residuals across the gear
reduction chain:  16D → 8D → 4D → 3D → trajectory.
Each step may introduce a dimensional mismatch ε; the total accumulated
error is the RSS of all steps.
-/
def gearReduceResidual (r16to8 r8to4 r4to3 r3ToTrajectory : Q16_16) : Q16_16 :=
  let r1 := Q16_16.mul r16to8 r16to8
  let r2 := Q16_16.mul r8to4 r8to4
  let r3 := Q16_16.mul r4to3 r4to3
  let r4 := Q16_16.mul r3ToTrajectory r3ToTrajectory
  Semantics.Q16_16Numerics.sqrt (Q16_16.add (Q16_16.add (Q16_16.add r1 r2) r3) r4)

-- ═══════════════════════════════════════════════════════════════════
-- §6  Fixtures
-- ═══════════════════════════════════════════════════════════════════

/--
Clean Newtonian trajectory:  F = m·a holds exactly in all three
dimensions.  mass = 2, a = (1,2,3), F = (2,4,6).
-/
def cleanNewtonFixture : TrajectoryPoint :=
  { positionX := Q16_16.zero, positionY := Q16_16.zero, positionZ := Q16_16.zero
  , velocityX := Q16_16.zero, velocityY := Q16_16.zero, velocityZ := Q16_16.zero
  , accelX    := Q16_16.one,  accelY    := Q16_16.two, accelZ    := (Q16_16.ofInt 3)
  , mass      := Q16_16.two
  , forceX    := Q16_16.two,  forceY    := (Q16_16.ofInt 4), forceZ := (Q16_16.ofInt 6)
  , timestamp := 0
  }

/--
Violating trajectory:  F ≠ m·a on the x-axis.
Same mass and acceleration, but x-force is off by 1.
-/
def violatingTrajectoryFixture : TrajectoryPoint :=
  { cleanNewtonFixture with
    forceX := Q16_16.add cleanNewtonFixture.forceX Q16_16.one
    timestamp := 1
  }

/--
Clean Lagrangian pair:  two consecutive states of a uniform-motion
system where V is constant and q̇ is constant, so E-L holds trivially.
-/
def cleanLagrangianFixture : LagrangianState × LagrangianState :=
  let s0 : LagrangianState :=
    { q := Q16_16.ofInt 0, qdot := Q16_16.one, mass := Q16_16.one
    , kinetic := Q16_16.ofRatio 1 2, potential := Q16_16.ofInt 5
    , lagrangian := Q16_16.sub (Q16_16.ofRatio 1 2) (Q16_16.ofInt 5) }
  let s1 : LagrangianState :=
    { q := Q16_16.one, qdot := Q16_16.one, mass := Q16_16.one
    , kinetic := Q16_16.ofRatio 1 2, potential := Q16_16.ofInt 5
    , lagrangian := Q16_16.sub (Q16_16.ofRatio 1 2) (Q16_16.ofInt 5) }
  (s0, s1)

/--
Free-particle fixture:  L = ½ m v² with V = 0.
Two consecutive states with constant velocity; E-L and action both vanish.
-/
def freeParticleFixture : LagrangianState × LagrangianState :=
  let s0 : LagrangianState :=
    { q := Q16_16.ofInt 0, qdot := Q16_16.one, mass := Q16_16.one
    , kinetic := Q16_16.ofRatio 1 2, potential := Q16_16.zero
    , lagrangian := Q16_16.ofRatio 1 2 }
  let s1 : LagrangianState :=
    { q := Q16_16.one, qdot := Q16_16.one, mass := Q16_16.one
    , kinetic := Q16_16.ofRatio 1 2, potential := Q16_16.zero
    , lagrangian := Q16_16.ofRatio 1 2 }
  (s0, s1)

-- ═══════════════════════════════════════════════════════════════════
-- §7  Theorems
-- ═══════════════════════════════════════════════════════════════════

/--
The clean Newtonian fixture passes the motion-recovery gate when the
other residual channels are set to zero.
-/
theorem newton_admits_clean :
    motionRecoveryGate (newtonSecondLawResidual cleanNewtonFixture)
      Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
    = { name := "MotionRecovery", required := true, score := Q16_16.one,
        verdict := GateVerdict.admit } := by
  native_decide

/--
The free-particle Lagrangian passes the motion-recovery gate.
-/
theorem free_particle_admits :
    let (s0, s1) := freeParticleFixture
    let dt := Q16_16.one
    let tau : Q16_16 := Q16_16.ofRatio 1 100
    motionRecoveryGate Q16_16.zero (eulerLagrangeResidual s0 s1 dt)
      (actionResidual s0 s1 dt tau) Q16_16.zero tau tau
    = { name := "MotionRecovery", required := true, score := Q16_16.one,
        verdict := GateVerdict.admit } := by
  native_decide

/--
When momentum is computed from mass and velocity (p = m·v), the
momentum residual is identically zero.
-/
theorem momentum_identity_clean :
    momentumResidual Q16_16.two Q16_16.zero Q16_16.zero
      Q16_16.two Q16_16.one Q16_16.zero Q16_16.zero
    = Q16_16.zero := by
  native_decide

/--
When E_k is computed exactly from ½·m·|v|², the kinetic-energy
residual is zero.
-/
theorem kinetic_energy_clean :
    kineticEnergyResidual (Q16_16.ofInt 1) Q16_16.two
      Q16_16.one Q16_16.zero Q16_16.zero
    = Q16_16.zero := by
  native_decide

/--
The violating fixture produces a nonzero Newton residual.
-/
theorem newton_violating_residual_pos :
    (newtonSecondLawResidual violatingTrajectoryFixture).val > Q16_16.zero.val := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════
-- §8  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════

#eval computeVelocity Q16_16.zero (Q16_16.ofInt 10) (Q16_16.ofInt 2)
#eval computeAcceleration Q16_16.zero (Q16_16.ofInt 5) (Q16_16.one)

#eval newtonSecondLawResidual cleanNewtonFixture
#eval newtonSecondLawResidual violatingTrajectoryFixture

#eval momentumResidual (Q16_16.ofInt 10) Q16_16.zero Q16_16.zero
  (Q16_16.ofInt 2) (Q16_16.ofInt 5) Q16_16.zero Q16_16.zero
#eval momentumResidual Q16_16.two Q16_16.zero Q16_16.zero
  Q16_16.two Q16_16.one Q16_16.zero Q16_16.zero

#eval kineticEnergyResidual (Q16_16.ofInt 25)
  (Q16_16.ofInt 2) (Q16_16.ofInt 5) Q16_16.zero Q16_16.zero
#eval kineticEnergyResidual (Q16_16.mul (Q16_16.ofRatio 1 2)
  (Q16_16.mul Q16_16.two (Q16_16.mul Q16_16.one Q16_16.one)))
  Q16_16.two Q16_16.one Q16_16.zero Q16_16.zero

#eval eulerLagrangeResidual cleanLagrangianFixture.1 cleanLagrangianFixture.2 Q16_16.one
#eval actionResidual cleanLagrangianFixture.1 cleanLagrangianFixture.2
  Q16_16.one (Q16_16.ofRatio 1 100)

#eval eulerLagrangeResidual freeParticleFixture.1 freeParticleFixture.2 Q16_16.one
#eval actionResidual freeParticleFixture.1 freeParticleFixture.2
  Q16_16.one (Q16_16.ofRatio 1 100)

#eval motionRecoveryGate (newtonSecondLawResidual cleanNewtonFixture)
  Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
#eval motionRecoveryGate (newtonSecondLawResidual violatingTrajectoryFixture)
  Q16_16.zero Q16_16.zero (Q16_16.ofRatio 1 100) Q16_16.zero Q16_16.zero

#eval motionDiagnostic Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
  (Q16_16.ofRatio 1 100) (Q16_16.ofRatio 1 100) (Q16_16.ofRatio 1 100)
  (Q16_16.ofRatio 1 100) (Q16_16.ofRatio 1 100) "system_3A" 42
#eval motionDiagnostic (Q16_16.ofInt 5) Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
  Q16_16.one Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero "system_3A" 42

#eval gearReduceResidual (Q16_16.ofRatio 1 1000) (Q16_16.ofRatio 2 1000)
  (Q16_16.ofRatio 3 1000) (Q16_16.ofRatio 4 1000)
#eval gearReduceResidual Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero

end Semantics.HCMMR.Law14
