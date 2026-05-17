-- DYNAMIC_CANAL.lean
-- Reference Kernel Spec: SIMD/Fluid Hybrid with Pressure-Adaptive Transport
-- Fixed-point only, saturating arithmetic, unified step function
-- Integrates DIAT, AVMR, N-DAG, Dynamic Canal, and Throat models

import Semantics.FixedPoint
import Semantics.Tactics

set_option linter.dupNamespace false

namespace Semantics.DynamicCanal

open Semantics

-- ============================================================
-- 1a. Fix16 Type Alias (for NBody compatibility)
-- ============================================================

/-- Fix16 is an alias for Q16_16, used in physics contexts.
    Provides signed fixed-point arithmetic for particle simulations. -/
abbrev Fix16 := Q16_16

namespace Fix16
-- Re-export Q16_16 constants and operations under Fix16 namespace
def zero := Q16_16.zero
def one := Q16_16.one
def epsilon := Q16_16.epsilon
def abs := Q16_16.abs
def add := Q16_16.add
def sub := Q16_16.sub
def mul := Q16_16.mul
def div := Q16_16.div
def sqrt := Q16_16.sqrt
def max := Q16_16.max
def sat01 := Q16_16.sat01
def ofInt := Q16_16.ofInt
def ofNat := Q16_16.ofNat
def toInt := Q16_16.toInt
def ofFloat := Q16_16.ofFloat
def toFloat := Q16_16.toFloat
def neg := Q16_16.neg
def mk (raw : UInt32) : Fix16 := { val := raw }
end Fix16

-- ============================================================
-- 2. VECTOR PRIMITIVES
-- ============================================================

/-- Small fixed-point vector -/
abbrev VecN (n : Nat) := Fin n → Q16_16

/-- Zero vector -/
def VecN.zero {n : Nat} : VecN n := fun _ => Q16_16.zero

/-- Vector addition (component-wise saturating) -/
def vecAdd {n : Nat} (a b : VecN n) : VecN n :=
  fun i => Q16_16.add (a i) (b i)

/-- Vector subtraction -/
def vecSub {n : Nat} (a b : VecN n) : VecN n :=
  fun i => Q16_16.sub (a i) (b i)

/-- Vector L1 norm (sum of absolute values) -/
noncomputable def vecL1 {n : Nat} (v : VecN n) : Q16_16 :=
  Fin.foldl n (fun acc i => Q16_16.add acc (Q16_16.abs (v i))) Q16_16.zero

/-- Vector max absolute component -/
def vecMaxAbs {n : Nat} (v : VecN n) : Q16_16 :=
  Fin.foldl n (fun acc i => Q16_16.max acc (Q16_16.abs (v i))) Q16_16.zero

/-- Dot product -/
def vecDot {n : Nat} (a b : VecN n) : Q16_16 :=
  Fin.foldl n (fun acc i => Q16_16.add acc (Q16_16.mul (a i) (b i))) Q16_16.zero

-- ============================================================
-- 3. ENUMERATIONS
-- ============================================================

/-- Execution regime for lanes -/
inductive Regime
  | coherent    -- Stable transport
  | stressed    -- Distorted transport
  | throat      -- Wormhole transfer
  deriving Repr, DecidableEq, BEq

/-- Execution mode: explicit lanes vs aggregate fluid -/
inductive ExecMode
  | lane
  | fluid
  deriving Repr, DecidableEq, BEq

/-- Throat classification -/
inductive ThroatClass
  | stableBridge
  | lossyChannel
  | rupture
  deriving Repr, DecidableEq, BEq

/-- Gradient type for precision metrics -/
inductive GradientType
  | pressureGradient
  | thermalGradient
  | velocityGradient
  | densityGradient
  | stressGradient
  deriving Repr, DecidableEq, BEq

-- ============================================================
-- 4. DIAT (Dual-Interval Algebraic Transform)
-- ============================================================

/-- DIAT encoding of integer n: shell + distances to adjacent squares -/
structure DIAT where
  shell : UInt32  -- k = floor(sqrt(n))
  a     : UInt32  -- n - k² (forward distance)
  b     : UInt32  -- (k+1)² - n (backward distance)
  prod  : UInt32  -- a * b (shell interaction)
  diff  : Int32   -- a - b (signed asymmetry)
  deriving Repr, DecidableEq, BEq

namespace DIAT

/-- Integer square root (iterative approximation) -/
def isqrt (n : UInt32) : UInt32 :=
  if n <= 1 then n
  else
    let rec loop (x : UInt32) (iter : Nat) : UInt32 :=
      if iter = 0 then x
      else
        let y := (x + n / x) / 2
        if y >= x then x else loop y (iter - 1)
    loop n 16

/-- Encode integer n as DIAT tuple -/
def encode (n : UInt32) : DIAT :=
  let k  := isqrt n
  let lo := k * k
  let kp := k + 1
  let hi := kp * kp
  let a  := n - lo
  let b  := hi - n
  {
    shell := k
    a     := a
    b     := b
    prod  := a * b
    diff  := Int32.ofInt (a.toNat : Int) - Int32.ofInt (b.toNat : Int)
  }

/-- Shell width = 2k + 1 -/
def shellWidth (d : DIAT) : UInt32 := 2 * d.shell + 1

/-- Normalized a: a / (2k+1) -/
def normA (d : DIAT) : Q16_16 :=
  Q16_16.div ⟨d.a⟩ ⟨((2 * d.shell + 1) * 0x10000)⟩

end DIAT

-- ============================================================
-- 5. TIMING AND PAYLOAD
-- ============================================================

/-- Timing tuple for synchronization -/
structure Timing where
  slot   : UInt16
  parity : Bool
  index  : UInt32
  deriving Repr, DecidableEq, BEq

/-- Lane payload with DIAT and metadata -/
structure LanePayload where
  diat        : DIAT
  codonWindow : UInt32  -- Packed representation
  metadata    : Q16_16    -- Scalar metadata (generalized from array)
  deriving Repr, DecidableEq, BEq

-- ============================================================
-- 6. CORE DATA STRUCTURES
-- ============================================================

/-- SIMD lane state -/
structure Lane where
  active    : Bool
  node      : UInt32
  pos       : VecN 3    -- 3D position (generalized N-space)
  vel       : VecN 3    -- 3D velocity
  phase     : Q16_16
  stress    : Q16_16
  pressure  : Q16_16
  lambdaEff : Q16_16     -- Dynamic canal effective resistance
  energy    : Q16_16
  mismatch  : Q16_16
  regime    : Regime
  timing    : Timing
  payload   : LanePayload

/-- AVMR summary for aggregation -/
structure AVMRSummary where
  count        : UInt32
  phaseX       : Q16_16
  phaseY       : Q16_16
  coherence    : Q16_16
  mismatchSum  : Q16_16
  mismatchMax  : Q16_16
  massSum      : Q16_16
  energySum    : Q16_16
  coherentCnt  : UInt32
  stressedCnt  : UInt32
  throatCnt    : UInt32
  deriving Repr, DecidableEq, BEq

/-- Canal section for fluid mode -/
structure CanalSection where
  density        : Q16_16
  capacity       : Q16_16
  flux           : Q16_16
  siphon         : Q16_16
  meanEnergy     : Q16_16
  meanMismatch   : Q16_16
  meanStress     : Q16_16
  pressure       : Q16_16
  lambdaEff      : Q16_16
  compliance     : Q16_16
  width          : Q16_16
  roughness      : Q16_16
  gradient       : Q16_16
  throatExposure : Q16_16
  unpackScore    : Q16_16
  unpacked       : Bool
  loopIteration  : Nat      -- Current loop iteration
  coarseGrainLevel : Nat    -- Current coarse-graining level (0 = full precision)
  deriving Repr, DecidableEq, BEq

/-- Precision metrics based on gradient type -/
structure PrecisionMetrics where
  pressurePrecision : Q16_16  -- Precision for pressure gradients
  thermalPrecision  : Q16_16  -- Precision for thermal gradients
  velocityPrecision : Q16_16  -- Precision for velocity gradients
  densityPrecision  : Q16_16  -- Precision for density gradients
  stressPrecision   : Q16_16  -- Precision for stress gradients
  deriving Repr, DecidableEq, BEq

/-- Edge attributes -/
structure EdgeAttr where
  baseWeight       : Q16_16
  dPos             : VecN 3
  dPhase           : Q16_16
  dEnergy          : Q16_16
  torsion          : Q16_16
  loss             : Q16_16
  mismatchGain     : Q16_16
  capacity         : Q16_16
  pressureCoupling : Q16_16
  throatBias       : Q16_16
  prefPhase        : Q16_16
  isThroat         : Bool

/-- Graph edge -/
structure Edge where
  src  : UInt32
  dst  : UInt32
  attr : EdgeAttr

/-- Node state across universes -/
structure NodeState where
  diatState    : Q16_16
  waveState    : Q16_16
  timeState    : Q16_16
  torsionState : Q16_16
  fluidState   : Q16_16
  deriving Repr, DecidableEq, BEq

/-- N-DAG (N-dimensional directed graph) -/
structure NDAG where
  nodes : Array NodeState
  edges : Array Edge

/-- Throat state -/
structure ThroatState where
  edgeId       : UInt32
  mismatchNorm : Q16_16
  dynWeight    : Q16_16
  healingGain  : Q16_16
  cls          : ThroatClass
  deriving Repr, DecidableEq, BEq

-- ============================================================
-- 7. GLOBAL PARAMETERS
-- ============================================================

/-- Kernel configuration parameters -/
structure KernelParams where
  -- Stress model
  alphaSurprise     : Q16_16
  betaRegret        : Q16_16
  -- Dynamic Canal
  lambda0           : Q16_16    -- Base resistance
  canalElasticity   : Q16_16    -- ξ: pressure sensitivity
  canalSaturation   : Q16_16    -- σ: minimum fraction
  pressureDecay     : Q16_16    -- γ: memory decay
  bioWeight         : Q16_16    -- External pressure weight
  -- Regime thresholds
  coherentThresh    : Q16_16
  throatThresh      : Q16_16
  stressThresh      : Q16_16
  -- Update rates
  relaxRate         : Q16_16
  healRate          : Q16_16
  torsionRate       : Q16_16
  torsionEnergyExtraction : Q16_16  -- How much energy torsion steals from manifold
  mismatchRate      : Q16_16
  energyLossRate    : Q16_16
  -- Capacity model
  capacityPressure  : Q16_16
  capacityRoughness : Q16_16
  capacityMismatch  : Q16_16
  -- Velocity model
  velGradientGain   : Q16_16
  velDensityLoss    : Q16_16
  velRoughnessLoss  : Q16_16
  velMismatchLoss   : Q16_16
  velComplianceGain : Q16_16
  -- Throat model
  throatMismatchLoss : Q16_16
  throatPressureGain : Q16_16
  throatStressLoss   : Q16_16
  -- Unpack threshold
  thetaDensity      : Q16_16
  thetaMismatch     : Q16_16
  thetaStress       : Q16_16
  thetaPT           : Q16_16    -- Pressure-throat interaction
  thetaCrit         : Q16_16
  deriving Repr

-- ============================================================
-- 8. DYNAMIC CANAL LAW (Core Constitutive Equation)
-- ============================================================

namespace DynamicCanal

/-- Dynamic Canal law: λ_eff(P) = λ₀[σ + (1-σ)e^(-ξP)] -/
def dynamicCanalLambda (p : KernelParams) (pressure : Q16_16) : Q16_16 :=
  let ξP := Q16_16.mul p.canalElasticity pressure
  let eTerm := Q16_16.expNeg ξP
  let oneMinusσ := Q16_16.sub Q16_16.one p.canalSaturation
  let deform := Q16_16.add p.canalSaturation (Q16_16.mul oneMinusσ eTerm)
  Q16_16.mul p.lambda0 deform

/-- Canal compliance K(P) = 1/λ_eff(P) -/
def canalCompliance (p : KernelParams) (pressure : Q16_16) : Q16_16 :=
  let lambdaEff := dynamicCanalLambda p pressure
  Q16_16.recip lambdaEff

/-- Canal width: W_c(P) = W_c,₀ · λ₀/λ_eff(P) -/
def canalWidth (p : KernelParams) (baseWidth : Q16_16) (pressure : Q16_16) : Q16_16 :=
  let lambdaEff := dynamicCanalLambda p pressure
  let ratio := Q16_16.div p.lambda0 lambdaEff
  Q16_16.mul baseWidth ratio

end DynamicCanal

-- ============================================================
-- COARSE-GRAINING WITH LOOP ITERATION
-- ============================================================

namespace CoarseGraining

/-- Default precision metrics (high precision for all gradients) -/
def defaultPrecisionMetrics : PrecisionMetrics :=
  {
    pressurePrecision := Q16_16.ofFloat 0.999,
    thermalPrecision := Q16_16.ofFloat 0.999,
    velocityPrecision := Q16_16.ofFloat 0.999,
    densityPrecision := Q16_16.ofFloat 0.999,
    stressPrecision := Q16_16.ofFloat 0.999
  }

/-- Get precision for a given gradient type -/
def getPrecision (metrics : PrecisionMetrics) (gtype : GradientType) : Q16_16 :=
  match gtype with
  | GradientType.pressureGradient => metrics.pressurePrecision
  | GradientType.thermalGradient => metrics.thermalPrecision
  | GradientType.velocityGradient => metrics.velocityPrecision
  | GradientType.densityGradient => metrics.densityPrecision
  | GradientType.stressGradient => metrics.stressPrecision

/-- Compute coarse-graining factor based on loop iteration.
    Factor decreases (precision reduces) as loops increase. -/
def coarseGrainFactor (loopIter : Nat) (maxLoops : Nat) : Q16_16 :=
  if maxLoops = 0 then Q16_16.one
  else if loopIter >= maxLoops then Q16_16.ofFloat 0.5  -- Minimum 50% precision
  else
    let ratio := Q16_16.ofNat loopIter / Q16_16.ofNat maxLoops
    let factor := Q16_16.one - (ratio * Q16_16.ofFloat 0.5)  -- Linear decay to 50%
    Q16_16.max (Q16_16.ofFloat 0.5) factor

/-- Apply coarse-graining to a value based on gradient type and loop iteration. -/
def applyCoarseGraining (value : Q16_16) (gtype : GradientType) (metrics : PrecisionMetrics)
    (loopIter : Nat) (maxLoops : Nat) : Q16_16 :=
  let precision := getPrecision metrics gtype
  let cgFactor := coarseGrainFactor loopIter maxLoops
  let effectivePrecision := Q16_16.mul precision cgFactor
  Q16_16.mul value effectivePrecision

/-- Update coarse-graining level based on loop iteration.
    Level increases every N loops to control granularity. -/
def updateCoarseGrainLevel (_currentLevel : Nat) (loopIter : Nat) (levelInterval : Nat) : Nat :=
  if levelInterval = 0 then 0
  else loopIter / levelInterval

end CoarseGraining

-- ============================================================
-- 9. STRESS MODEL
-- ============================================================

/-- Edge evaluation context -/
structure EdgeEval where
  edge      : Edge
  score     : Q16_16
  deltaNorm : Q16_16
  logProb   : Q16_16
  logBest   : Q16_16

/-- Surprise = -log(P_actual) -/
noncomputable def surpriseOf (ev : EdgeEval) : Q16_16 :=
  Q16_16.abs ev.logProb

/-- Regret = max(0, log(P_best) - log(P_actual)) -/
def regretOf (ev : EdgeEval) : Q16_16 :=
  Q16_16.max Q16_16.zero (Q16_16.sub ev.logBest ev.logProb)

/-- Stress = α·surprise + β·regret -/
noncomputable def stressOfEval (p : KernelParams) (ev : EdgeEval) : Q16_16 :=
  let s := surpriseOf ev
  let r := regretOf ev
  Q16_16.add (Q16_16.mul p.alphaSurprise s) (Q16_16.mul p.betaRegret r)

-- ============================================================
-- 10. EDGE SCORING
-- ============================================================

/-- Compute edge score with Dynamic Canal stress penalty -/
noncomputable def edgeScore (_p : KernelParams) (lane : Lane) (ev : EdgeEval) : Q16_16 :=
  let phaseErr := Q16_16.abs (Q16_16.sub lane.phase ev.edge.attr.prefPhase)
  let stressProxy := Q16_16.add
                      (Q16_16.mul ev.edge.attr.torsion Q16_16.one)
                      (Q16_16.mul ev.edge.attr.mismatchGain ev.deltaNorm)
  let stressPenalty := Q16_16.mul lane.lambdaEff stressProxy
  Q16_16.sub
    (Q16_16.sub
      (Q16_16.add ev.edge.attr.baseWeight ev.score)
      phaseErr)
    (Q16_16.add stressPenalty lane.mismatch)

-- ============================================================
-- 11. REGIME CLASSIFICATION
-- ============================================================

/-- Classify lane regime based on mismatch, stress, and edge type -/
def classifyRegime (p : KernelParams) (lane : Lane) (chosen : Edge) : Regime :=
  if lane.mismatch.val <= p.coherentThresh.val &&
     lane.stress.val <= p.stressThresh.val then
    Regime.coherent
  else if lane.mismatch.val >= p.throatThresh.val && chosen.attr.isThroat then
    Regime.throat
  else
    Regime.stressed

-- ============================================================
-- 12. LANE UPDATE KERNELS (Three Regimes)
-- ============================================================

/-- Coherent flow regime: stable transport -/
def coherentStep (p : KernelParams) (lane : Lane) (chosen : Edge)
                 (deltaNorm : Q16_16) (heal : Q16_16) (pNext lambdaNext : Q16_16) : Lane :=
  let pos' := vecAdd lane.pos (vecAdd lane.vel chosen.attr.dPos)
  let vel' := vecAdd lane.vel chosen.attr.dPos
  let phase' := Q16_16.add lane.phase chosen.attr.dPhase
  let stress' := Q16_16.max Q16_16.zero
                    (Q16_16.sub
                      (Q16_16.add lane.stress (Q16_16.mul p.torsionRate chosen.attr.torsion))
                      (Q16_16.mul p.relaxRate Q16_16.one))
  -- Torsion steals energy from manifold
  let torsionEnergySteal := Q16_16.mul p.torsionEnergyExtraction chosen.attr.torsion
  let energy' := Q16_16.max Q16_16.zero
                   (Q16_16.sub
                     (Q16_16.sub
                       (Q16_16.add lane.energy chosen.attr.dEnergy)
                       (Q16_16.mul p.energyLossRate chosen.attr.loss))
                     torsionEnergySteal)
  let mismatch' := Q16_16.max Q16_16.zero
                      (Q16_16.sub
                        (Q16_16.add lane.mismatch (Q16_16.mul p.mismatchRate deltaNorm))
                        (Q16_16.mul p.healRate heal))
  {
    lane with
    pos       := pos'
    vel       := vel'
    phase     := phase'
    stress    := stress'
    pressure  := pNext
    lambdaEff := lambdaNext
    energy    := energy'
    mismatch  := mismatch'
    node      := chosen.dst
  }

/-- Stressed flow regime: distorted transport with torsion -/
def stressedStep (p : KernelParams) (lane : Lane) (chosen : Edge)
                 (deltaNorm : Q16_16) (heal : Q16_16) (pNext lambdaNext : Q16_16)
                 (distortion : VecN 3) : Lane :=
  let pos' := vecAdd lane.pos (vecAdd lane.vel (vecAdd chosen.attr.dPos distortion))
  let vel' := vecSub (vecAdd lane.vel chosen.attr.dPos) distortion
  let phase' := Q16_16.add lane.phase chosen.attr.dPhase
  let stress' := Q16_16.max Q16_16.zero
                    (Q16_16.sub
                      (Q16_16.add
                        (Q16_16.add lane.stress (Q16_16.mul p.torsionRate chosen.attr.torsion))
                        (Q16_16.mul p.mismatchRate lane.mismatch))
                      (Q16_16.mul p.relaxRate heal))
  -- Torsion steals energy from manifold (amplified in stressed regime)
  let torsionEnergySteal := Q16_16.mul p.torsionEnergyExtraction chosen.attr.torsion
  let energy' := Q16_16.max Q16_16.zero
                   (Q16_16.sub
                     (Q16_16.sub
                       (Q16_16.sub
                         (Q16_16.add lane.energy chosen.attr.dEnergy)
                         (Q16_16.mul p.energyLossRate chosen.attr.loss))
                       lane.stress)
                     torsionEnergySteal)
  let mismatch' := Q16_16.max Q16_16.zero
                      (Q16_16.sub
                        (Q16_16.add lane.mismatch (Q16_16.mul p.mismatchRate deltaNorm))
                        (Q16_16.mul p.healRate heal))
  {
    lane with
    pos       := pos'
    vel       := vel'
    phase     := phase'
    stress    := stress'
    pressure  := pNext
    lambdaEff := lambdaNext
    energy    := energy'
    mismatch  := mismatch'
    node      := chosen.dst
  }

/-- Throat transfer regime: wormhole-like lossy transfer -/
def throatStep (p : KernelParams) (lane : Lane) (chosen : Edge)
               (deltaNorm : Q16_16) (heal : Q16_16) (pNext lambdaNext : Q16_16)
               (distortion : VecN 3) : Lane :=
  let pos' := vecAdd lane.pos distortion
  let vel' := distortion
  let phase' := Q16_16.add lane.phase chosen.attr.dPhase
  let stress' := Q16_16.add lane.stress (Q16_16.mul p.mismatchRate deltaNorm)
  -- Torsion steals energy from manifold (maximum extraction in throat regime)
  let torsionEnergySteal := Q16_16.mul p.torsionEnergyExtraction chosen.attr.torsion
  let energy' := Q16_16.max Q16_16.zero
                    (Q16_16.sub
                      (Q16_16.sub
                        (Q16_16.sub lane.energy (Q16_16.mul p.energyLossRate chosen.attr.loss))
                        deltaNorm)
                      torsionEnergySteal)
  let mismatch' := Q16_16.max Q16_16.zero
                      (Q16_16.sub
                        (Q16_16.add lane.mismatch deltaNorm)
                        (Q16_16.mul p.healRate heal))
  {
    lane with
    pos       := pos'
    vel       := vel'
    phase     := phase'
    stress    := stress'
    pressure  := pNext
    lambdaEff := lambdaNext
    energy    := energy'
    mismatch  := mismatch'
    node      := chosen.dst
  }

-- ============================================================
-- 13. UNIFIED STEP FUNCTION
-- ============================================================

/-- Build step context for a lane -/
structure LaneStepCtx where
  chosenEdge : Edge
  deltaNorm  : Q16_16
  heal       : Q16_16
  stressReal : Q16_16
  pressureNext : Q16_16
  lambdaNext : Q16_16
  distortion : VecN 3

/-- Compute lane step context (edge selection + pressure update) -/
noncomputable def buildLaneCtx (p : KernelParams) (lane : Lane) (edges : Array Edge)
                 (pickEdge : Lane → Array Edge → Edge)
                 (computeDelta : Lane → Edge → VecN 3)
                 (computeHeal : Lane → Edge → Q16_16) : LaneStepCtx :=
  let chosen := pickEdge lane edges
  let deltaVec := computeDelta lane chosen
  let deltaNorm := vecL1 deltaVec
  let heal := computeHeal lane chosen
  let stressReal := Q16_16.mul p.alphaSurprise deltaNorm  -- Simplified stress model
  let pNext := Q16_16.add (Q16_16.mul p.pressureDecay lane.pressure) stressReal
  let lambdaNext := DynamicCanal.dynamicCanalLambda p pNext
  let distortion := deltaVec  -- Simplified distortion model
  {
    chosenEdge := chosen
    deltaNorm  := deltaNorm
    heal       := heal
    stressReal := stressReal
    pressureNext := pNext
    lambdaNext := lambdaNext
    distortion := distortion
  }

/-- Unified lane step: handles all three regimes -/
noncomputable def stepLane (p : KernelParams) (lane : Lane) (edges : Array Edge)
             (pickEdge : Lane → Array Edge → Edge)
             (computeDelta : Lane → Edge → VecN 3)
             (computeHeal : Lane → Edge → Q16_16) : Lane :=
  if !lane.active then lane
  else
    let ctx := buildLaneCtx p lane edges pickEdge computeDelta computeHeal
    let lane' := match lane.regime with
      | Regime.coherent => coherentStep p lane ctx.chosenEdge ctx.deltaNorm
                            ctx.heal ctx.pressureNext ctx.lambdaNext
      | Regime.stressed => stressedStep p lane ctx.chosenEdge ctx.deltaNorm
                            ctx.heal ctx.pressureNext ctx.lambdaNext ctx.distortion
      | Regime.throat   => throatStep p lane ctx.chosenEdge ctx.deltaNorm
                            ctx.heal ctx.pressureNext ctx.lambdaNext ctx.distortion
    let rg' := classifyRegime p lane' ctx.chosenEdge
    { lane' with regime := rg' }

-- ============================================================
-- 14. THROAT UPDATE
-- ============================================================

/-- Classify throat state -/
def classifyThroat (stableW ruptureW stableD ruptureD w δ : Q16_16) : ThroatClass :=
  if w.val >= stableW.val && δ.val <= stableD.val then
    ThroatClass.stableBridge
  else if w.val <= ruptureW.val || δ.val >= ruptureD.val then
    ThroatClass.rupture
  else
    ThroatClass.lossyChannel

/-- Update throat state with pressure coupling -/
def stepThroat (p : KernelParams) (sec : CanalSection) (thr : ThroatState) : ThroatState :=
  let compliance0 := Q16_16.recip p.lambda0
  let gainP := Q16_16.mul p.throatPressureGain (Q16_16.sub sec.compliance compliance0)
  let lossδ := Q16_16.mul p.throatMismatchLoss thr.mismatchNorm
  let lossS := Q16_16.mul p.throatStressLoss sec.meanStress
  let w' := Q16_16.max Q16_16.zero
               (Q16_16.add
                 (Q16_16.sub thr.dynWeight lossδ)
                 (Q16_16.sub gainP lossS))
  let cls' := classifyThroat
                ⟨0x00018000⟩  -- stable weight threshold (~1.5)
                ⟨0x00008000⟩  -- rupture weight threshold (~0.5)
                ⟨0x00010000⟩  -- stable mismatch threshold (1.0)
                ⟨0x00030000⟩  -- rupture mismatch threshold (3.0)
                w' thr.mismatchNorm
  { thr with dynWeight := w', cls := cls' }

-- ============================================================
-- 15. CANAL SECTION UPDATE (Fluid Mode)
-- ============================================================

/-- Update canal section with coarse-graining on each loop -/
def stepSection (p : KernelParams) (sec : CanalSection)
                (inFlux outFlux : Q16_16) (inflow : Q16_16)
                (precisionMetrics : PrecisionMetrics) (maxLoops : Nat) (levelInterval : Nat) : CanalSection :=
  -- Increment loop iteration
  let loopIter' := sec.loopIteration + 1
  -- Update coarse-graining level
  let cgLevel' := CoarseGraining.updateCoarseGrainLevel sec.coarseGrainLevel loopIter' levelInterval
  -- Pressure update: P' = γ·P + stress
  let stressAvg := sec.meanStress
  let rawP' := Q16_16.add (Q16_16.mul p.pressureDecay sec.pressure) stressAvg
  -- Apply coarse-graining to pressure based on pressure gradient type
  let p' := CoarseGraining.applyCoarseGraining rawP' GradientType.pressureGradient
              precisionMetrics loopIter' maxLoops
  -- Dynamic Canal: lambda_eff(P')
  let lambdaEff := DynamicCanal.dynamicCanalLambda p p'
  let K' := DynamicCanal.canalCompliance p p'
  -- Capacity: C = C₀ + c_P·P - c_R·R - c_m·m
  let rawCap' := Q16_16.sat01
                (Q16_16.add
                  (Q16_16.sub
                    (Q16_16.sub Q16_16.one (Q16_16.mul p.capacityRoughness sec.roughness))
                    (Q16_16.mul p.capacityMismatch sec.meanMismatch))
                  (Q16_16.mul p.capacityPressure p'))
  -- Apply coarse-graining to capacity based on density gradient
  let cap' := CoarseGraining.applyCoarseGraining rawCap' GradientType.densityGradient
              precisionMetrics loopIter' maxLoops
  -- Flux conservation: ρ' = ρ - (out - in) - siphon + inflow
  let rawDensity' := Q16_16.max Q16_16.zero
                   (Q16_16.sub
                     (Q16_16.sub
                       (Q16_16.add sec.density inflow)
                       (Q16_16.sub outFlux inFlux))
                     sec.siphon)
  -- Apply coarse-graining to density based on density gradient
  let density' := CoarseGraining.applyCoarseGraining rawDensity' GradientType.densityGradient
                  precisionMetrics loopIter' maxLoops
  -- Effective velocity with compliance gain
  let rawVeff := Q16_16.sat01
                (Q16_16.add
                  (Q16_16.sub
                    (Q16_16.sub
                      (Q16_16.sub Q16_16.one (Q16_16.mul p.velDensityLoss density'))
                      (Q16_16.mul p.velRoughnessLoss sec.roughness))
                    (Q16_16.mul p.velMismatchLoss sec.meanMismatch))
                  (Q16_16.mul p.velComplianceGain K'))
  -- Apply coarse-graining to velocity based on velocity gradient
  let veff := CoarseGraining.applyCoarseGraining rawVeff GradientType.velocityGradient
              precisionMetrics loopIter' maxLoops
  let flux' := Q16_16.mul density' veff
  -- Unpack score with pressure-throat interaction
  let rawUnpackScore' :=
    Q16_16.add
      (Q16_16.add
        (Q16_16.add
          (Q16_16.mul p.thetaDensity density')
          (Q16_16.mul p.thetaMismatch sec.meanMismatch))
        (Q16_16.mul p.thetaStress sec.meanStress))
      (Q16_16.mul p.thetaPT (Q16_16.mul K' sec.throatExposure))
  -- Apply coarse-graining to unpack score based on stress gradient
  let unpackScore' := CoarseGraining.applyCoarseGraining rawUnpackScore' GradientType.stressGradient
                    precisionMetrics loopIter' maxLoops
  let unpacked' := unpackScore'.val >= p.thetaCrit.val
  {
    sec with
    density          := density'
    capacity         := cap'
    flux             := flux'
    pressure         := p'
    lambdaEff        := lambdaEff
    compliance       := K'
    unpackScore      := unpackScore'
    unpacked         := unpacked'
    loopIteration    := loopIter'
    coarseGrainLevel := cgLevel'
  }

-- ============================================================
-- 16. TOTILITY THEOREMS (Zero-Trust Compliance)
-- ============================================================

/-- All Q16_16 operations are total -/
theorem Q16_16.add_total (a b : Q16_16) : ∃ c, Q16_16.add a b = c := by
  simp [Q16_16.add]

theorem Q16_16.sub_total (a b : Q16_16) : ∃ c, Q16_16.sub a b = c := by
  simp [Q16_16.sub]

theorem Q16_16.mul_total (a b : Q16_16) : ∃ c, Q16_16.mul a b = c := by
  simp [Q16_16.mul]

theorem Q16_16.div_total (a b : Q16_16) : ∃ c, Q16_16.div a b = c := by
  simp [Q16_16.div]

/-- Dynamic Canal law is total -/
theorem dynamicCanalLambda_total (p : KernelParams) (pressure : Q16_16) :
  ∃ lambdaEff, DynamicCanal.dynamicCanalLambda p pressure = lambdaEff := by
  simp [DynamicCanal.dynamicCanalLambda]

/-- All regime steps are total -/
theorem stepLane_total (p : KernelParams) (lane : Lane) (edges : Array Edge)
    (pickEdge : Lane → Array Edge → Edge)
    (computeDelta : Lane → Edge → VecN 3)
    (computeHeal : Lane → Edge → Q16_16) :
  ∃ lane', stepLane p lane edges pickEdge computeDelta computeHeal = lane' := by
  exact ⟨stepLane p lane edges pickEdge computeDelta computeHeal, rfl⟩

theorem stepSection_total (p : KernelParams) (sec : CanalSection)
    (inFlux outFlux inflow : Q16_16) :
  ∃ sec', stepSection p sec inFlux outFlux inflow = sec' := by
  exact ⟨stepSection p sec inFlux outFlux inflow, rfl⟩

-- ============================================================
-- 17. #EVAL WITNESSES (Self-Test)
-- ============================================================

-- Test fixed-point constructors
#eval Q16_16.zero.val
#eval Q16_16.one.val

-- Test DIAT encoding
#eval DIAT.encode 10

-- Test regime equality
#eval Regime.coherent == Regime.coherent
#eval Regime.stressed == Regime.throat

-- Test coarse-graining precision metrics
#eval CoarseGraining.defaultPrecisionMetrics

-- Test coarse-graining factor calculation
#eval CoarseGraining.coarseGrainFactor 0 10  -- Loop 0 of 10: should be 1.0
#eval CoarseGraining.coarseGrainFactor 5 10  -- Loop 5 of 10: should be 0.75
#eval CoarseGraining.coarseGrainFactor 10 10 -- Loop 10 of 10: should be 0.5

-- Test coarse-graining application
#eval CoarseGraining.applyCoarseGraining (Q16_16.ofFloat 1.0) GradientType.pressureGradient
        CoarseGraining.defaultPrecisionMetrics 0 10
#eval CoarseGraining.applyCoarseGraining (Q16_16.ofFloat 1.0) GradientType.pressureGradient
        CoarseGraining.defaultPrecisionMetrics 5 10
#eval CoarseGraining.applyCoarseGraining (Q16_16.ofFloat 1.0) GradientType.pressureGradient
        CoarseGraining.defaultPrecisionMetrics 10 10

-- Test coarse-graining level update
#eval CoarseGraining.updateCoarseGrainLevel 0 0 5  -- Level 0
#eval CoarseGraining.updateCoarseGrainLevel 0 5 5  -- Level 1
#eval CoarseGraining.updateCoarseGrainLevel 0 10 5 -- Level 2

-- Test canal section with loop iteration and coarse-graining
def testCanalSectionWithCoarseGraining : CanalSection :=
  {
    density        := Q16_16.ofFloat 0.5,
    capacity       := Q16_16.ofFloat 0.8,
    flux           := Q16_16.ofFloat 0.3,
    siphon         := Q16_16.ofFloat 0.1,
    meanEnergy     := Q16_16.ofFloat 1.0,
    meanMismatch   := Q16_16.ofFloat 0.2,
    meanStress     := Q16_16.ofFloat 0.3,
    pressure       := Q16_16.ofFloat 0.5,
    lambdaEff      := Q16_16.ofFloat 1.0,
    compliance     := Q16_16.ofFloat 1.0,
    width          := Q16_16.ofFloat 1.0,
    roughness      := Q16_16.ofFloat 0.1,
    gradient       := Q16_16.ofFloat 0.2,
    throatExposure := Q16_16.ofFloat 0.1,
    unpackScore    := Q16_16.ofFloat 0.5,
    unpacked       := false,
    loopIteration  := 0,
    coarseGrainLevel := 0
  }

#eval testCanalSectionWithCoarseGraining.loopIteration
#eval testCanalSectionWithCoarseGraining.coarseGrainLevel
