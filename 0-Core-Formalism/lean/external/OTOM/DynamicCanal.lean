-- DYNAMIC_CANAL.lean
-- Reference Kernel Spec: SIMD/Fluid Hybrid with Pressure-Adaptive Transport
-- Fixed-point only, saturating arithmetic, unified step function
-- Integrates DIAT, AVMR, N-DAG, Dynamic Canal, and Throat models

import Semantics.Universality

namespace DynamicCanal

open Semantics.ENE

-- ============================================================
-- 1. FIXED-POINT CORE (Q16.16)
-- ============================================================

/-- Saturating fixed-point arithmetic structure -/
structure Fix16 where
  raw : UInt32
  deriving Repr, DecidableEq, BEq, Inhabited

namespace Fix16

/-- Zero value -/
def zero : Fix16 := ⟨0⟩

/-- One value (1.0 = 0x00010000 in Q16.16) -/
def one : Fix16 := ⟨0x00010000⟩

/-- Maximum positive value -/
def maxVal : Fix16 := ⟨0x7FFFFFFF⟩

/-- Minimum negative value -/
def minVal : Fix16 := ⟨0x80000000⟩

/-- Check if value is negative (MSB set) -/
def isNeg (f : Fix16) : Bool := f.raw >= 0x80000000

/-- Saturating addition -/
def add (a b : Fix16) : Fix16 :=
  let aInt : Int := if a.isNeg then (Int.ofNat (UInt32.toNat a.raw)) - 0x100000000 else Int.ofNat (UInt32.toNat a.raw)
  let bInt : Int := if b.isNeg then (Int.ofNat (UInt32.toNat b.raw)) - 0x100000000 else Int.ofNat (UInt32.toNat b.raw)
  let sum := aInt + bInt
  if sum > 0x7FFFFFFF then maxVal
  else if sum < -0x80000000 then minVal
  else if sum >= 0 then ⟨UInt32.ofNat sum.toNat⟩
  else ⟨UInt32.ofNat (sum + 0x100000000).toNat⟩

/-- Saturating subtraction -/
def sub (a b : Fix16) : Fix16 :=
  let aInt : Int := if a.isNeg then (Int.ofNat (UInt32.toNat a.raw)) - 0x100000000 else Int.ofNat (UInt32.toNat a.raw)
  let bInt : Int := if b.isNeg then (Int.ofNat (UInt32.toNat b.raw)) - 0x100000000 else Int.ofNat (UInt32.toNat b.raw)
  let diff := aInt - bInt
  if diff > 0x7FFFFFFF then maxVal
  else if diff < -0x80000000 then minVal
  else if diff >= 0 then ⟨UInt32.ofNat diff.toNat⟩
  else ⟨UInt32.ofNat (diff + 0x100000000).toNat⟩

/-- Saturating multiplication (Q16.16 × Q16.16 = Q32.32, truncated to Q16.16) -/
def mul (a b : Fix16) : Fix16 :=
  let a64 : Int64 := if a.isNeg then (Int64.ofNat (UInt32.toNat a.raw)) - 0x100000000 else Int64.ofNat (UInt32.toNat a.raw)
  let b64 : Int64 := if b.isNeg then (Int64.ofNat (UInt32.toNat b.raw)) - 0x100000000 else Int64.ofNat (UInt32.toNat b.raw)
  let prod := a64 * b64
  let shifted := prod >>> 16
  if shifted > 0x7FFFFFFF then maxVal
  else if shifted < -0x80000000 then minVal
  else if shifted >= 0 then ⟨UInt32.ofNat (Int64.toInt shifted).toNat⟩
  else ⟨UInt32.ofNat ((shifted + 0x100000000).toInt).toNat⟩

/-- Saturating division -/
def div (a b : Fix16) : Fix16 :=
  if b.raw == 0 then maxVal  -- Division by zero returns max (saturating)
  else
    let a64 : Int64 := if a.isNeg then (Int64.ofNat (UInt32.toNat a.raw)) - 0x100000000 else Int64.ofNat (UInt32.toNat a.raw)
    let b64 : Int64 := if b.isNeg then (Int64.ofNat (UInt32.toNat b.raw)) - 0x100000000 else Int64.ofNat (UInt32.toNat b.raw)
    let shifted := a64 <<< 16
    let quot := shifted / b64
    if quot > 0x7FFFFFFF then maxVal
    else if quot < -0x80000000 then minVal
    else if quot >= 0 then ⟨UInt32.ofNat (Int64.toInt quot).toNat⟩
    else ⟨UInt32.ofNat ((quot + 0x100000000).toInt).toNat⟩

/-- Minimum of two values -/
def min (a b : Fix16) : Fix16 := if a.raw <= b.raw then a else b

/-- Maximum of two values -/
def max (a b : Fix16) := if a.raw >= b.raw then a else b

/-- Absolute value -/
def abs (a : Fix16) : Fix16 := if a.isNeg then ⟨(0x100000000 - UInt32.toNat a.raw).toUInt32⟩ else a

/-- Clamp between low and high -/
def clamp (x lo hi : Fix16) : Fix16 := max lo (min x hi)

/-- Saturate to [0, 1] range -/
def sat01 (x : Fix16) : Fix16 := clamp x zero one

/-- Negate -/
def neg (a : Fix16) : Fix16 := ⟨(0x100000000 - UInt32.toNat a.raw).toUInt32⟩

/-- Approximate exp(-x) for x ≥ 0 using piecewise linear -/
def expNeg (x : Fix16) : Fix16 :=
  if x.raw >= 0x00030000 then zero  -- exp(-3) ≈ 0.05, treat as 0
  else if x.raw >= 0x00020000 then ⟨0x00004D29⟩  -- exp(-2) ≈ 0.135
  else if x.raw >= 0x00010000 then ⟨0x0000C5C0⟩  -- exp(-1) ≈ 0.368
  else if x.raw >= 0x00008000 then ⟨0x000147AE⟩  -- exp(-0.5) ≈ 0.606
  else ⟨0x0001C5C0⟩  -- exp(-0.25) ≈ 0.779

/-- Reciprocal approximation -/
def recip (a : Fix16) : Fix16 :=
  if a.raw == 0 then maxVal
  else div one a

end Fix16

-- ============================================================
-- 2. VECTOR PRIMITIVES
-- ============================================================

/-- Small fixed-point vector -/
abbrev VecN (n : Nat) := Fin n → Fix16

/-- Zero vector -/
def VecN.zero {n : Nat} : VecN n := fun _ => Fix16.zero

/-- Vector addition (component-wise saturating) -/
def vecAdd {n : Nat} (a b : VecN n) : VecN n :=
  fun i => Fix16.add (a i) (b i)

/-- Vector subtraction -/
def vecSub {n : Nat} (a b : VecN n) : VecN n :=
  fun i => Fix16.sub (a i) (b i)

/-- Vector L1 norm (sum of absolute values) -/
noncomputable def vecL1 {n : Nat} (v : VecN n) : Fix16 :=
  Fin.foldl n (fun acc i => Fix16.add acc (Fix16.abs (v i))) Fix16.zero

/-- Vector max absolute component -/
def vecMaxAbs {n : Nat} (v : VecN n) : Fix16 :=
  Fin.foldl n (fun acc i => Fix16.max acc (Fix16.abs (v i))) Fix16.zero

/-- Dot product -/
def vecDot {n : Nat} (a b : VecN n) : Fix16 :=
  Fin.foldl n (fun acc i => Fix16.add acc (Fix16.mul (a i) (b i))) Fix16.zero

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
def normA (d : DIAT) : Fix16 :=
  Fix16.div (Fix16.mk d.a) (Fix16.mk ((2 * d.shell + 1) * 0x10000))

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
  metadata    : Fix16    -- Scalar metadata (generalized from array)
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
  phase     : Fix16
  stress    : Fix16
  pressure  : Fix16
  lambdaEff : Fix16     -- Dynamic canal effective resistance
  energy    : Fix16
  mismatch  : Fix16
  regime    : Regime
  timing    : Timing
  payload   : LanePayload

/-- AVMR summary for aggregation -/
structure AVMRSummary where
  count        : UInt32
  phaseX       : Fix16
  phaseY       : Fix16
  coherence    : Fix16
  mismatchSum  : Fix16
  mismatchMax  : Fix16
  massSum      : Fix16
  energySum    : Fix16
  coherentCnt  : UInt32
  stressedCnt  : UInt32
  throatCnt    : UInt32
  deriving Repr, DecidableEq, BEq

/-- Canal section for fluid mode -/
structure CanalSection where
  density        : Fix16
  capacity       : Fix16
  flux           : Fix16
  siphon         : Fix16
  meanEnergy     : Fix16
  meanMismatch   : Fix16
  meanStress     : Fix16
  pressure       : Fix16
  lambdaEff      : Fix16
  compliance     : Fix16
  width          : Fix16
  roughness      : Fix16
  gradient       : Fix16
  throatExposure : Fix16
  unpackScore    : Fix16
  unpacked       : Bool
  deriving Repr, DecidableEq, BEq

/-- Edge attributes -/
structure EdgeAttr where
  baseWeight       : Fix16
  dPos             : VecN 3
  dPhase           : Fix16
  dEnergy          : Fix16
  torsion          : Fix16
  loss             : Fix16
  mismatchGain     : Fix16
  capacity         : Fix16
  pressureCoupling : Fix16
  throatBias       : Fix16
  prefPhase        : Fix16
  isThroat         : Bool

/-- Graph edge -/
structure Edge where
  src  : UInt32
  dst  : UInt32
  attr : EdgeAttr

/-- Node state across universes -/
structure NodeState where
  diatState    : Fix16
  waveState    : Fix16
  timeState    : Fix16
  torsionState : Fix16
  fluidState   : Fix16
  deriving Repr, DecidableEq, BEq

/-- N-DAG (N-dimensional directed graph) -/
structure NDAG where
  nodes : Array NodeState
  edges : Array Edge

/-- Throat state -/
structure ThroatState where
  edgeId       : UInt32
  mismatchNorm : Fix16
  dynWeight    : Fix16
  healingGain  : Fix16
  cls          : ThroatClass
  deriving Repr, DecidableEq, BEq

-- ============================================================
-- 7. GLOBAL PARAMETERS
-- ============================================================

/-- Kernel configuration parameters -/
structure KernelParams where
  -- Stress model
  alphaSurprise     : Fix16
  betaRegret        : Fix16
  -- Dynamic Canal
  lambda0           : Fix16    -- Base resistance
  canalElasticity   : Fix16    -- ξ: pressure sensitivity
  canalSaturation   : Fix16    -- σ: minimum fraction
  pressureDecay     : Fix16    -- γ: memory decay
  bioWeight         : Fix16    -- External pressure weight
  -- Regime thresholds
  coherentThresh    : Fix16
  throatThresh      : Fix16
  stressThresh      : Fix16
  -- Update rates
  relaxRate         : Fix16
  healRate          : Fix16
  torsionRate       : Fix16
  mismatchRate      : Fix16
  energyLossRate    : Fix16
  -- Capacity model
  capacityPressure  : Fix16
  capacityRoughness : Fix16
  capacityMismatch  : Fix16
  -- Velocity model
  velGradientGain   : Fix16
  velDensityLoss    : Fix16
  velRoughnessLoss  : Fix16
  velMismatchLoss   : Fix16
  velComplianceGain : Fix16
  -- Throat model
  throatMismatchLoss : Fix16
  throatPressureGain : Fix16
  throatStressLoss   : Fix16
  -- Unpack threshold
  thetaDensity      : Fix16
  thetaMismatch     : Fix16
  thetaStress       : Fix16
  thetaPT           : Fix16    -- Pressure-throat interaction
  thetaCrit         : Fix16
  deriving Repr

-- ============================================================
-- 8. DYNAMIC CANAL LAW (Core Constitutive Equation)
-- ============================================================

namespace DynamicCanal

/-- Dynamic Canal law: λ_eff(P) = λ₀[σ + (1-σ)e^(-ξP)] -/
def dynamicCanalLambda (p : KernelParams) (pressure : Fix16) : Fix16 :=
  let ξP := Fix16.mul p.canalElasticity pressure
  let eTerm := Fix16.expNeg ξP
  let oneMinusσ := Fix16.sub Fix16.one p.canalSaturation
  let deform := Fix16.add p.canalSaturation (Fix16.mul oneMinusσ eTerm)
  Fix16.mul p.lambda0 deform

/-- Canal compliance K(P) = 1/λ_eff(P) -/
def canalCompliance (p : KernelParams) (pressure : Fix16) : Fix16 :=
  let lambdaEff := dynamicCanalLambda p pressure
  Fix16.recip lambdaEff

/-- Canal width: W_c(P) = W_c,₀ · λ₀/λ_eff(P) -/
def canalWidth (p : KernelParams) (baseWidth : Fix16) (pressure : Fix16) : Fix16 :=
  let lambdaEff := dynamicCanalLambda p pressure
  let ratio := Fix16.div p.lambda0 lambdaEff
  Fix16.mul baseWidth ratio

end DynamicCanal

-- ============================================================
-- 9. STRESS MODEL
-- ============================================================

/-- Edge evaluation context -/
structure EdgeEval where
  edge      : Edge
  score     : Fix16
  deltaNorm : Fix16
  logProb   : Fix16
  logBest   : Fix16

/-- Surprise = -log(P_actual) -/
noncomputable def surpriseOf (ev : EdgeEval) : Fix16 :=
  Fix16.abs ev.logProb

/-- Regret = max(0, log(P_best) - log(P_actual)) -/
def regretOf (ev : EdgeEval) : Fix16 :=
  Fix16.max Fix16.zero (Fix16.sub ev.logBest ev.logProb)

/-- Stress = α·surprise + β·regret -/
noncomputable def stressOfEval (p : KernelParams) (ev : EdgeEval) : Fix16 :=
  let s := surpriseOf ev
  let r := regretOf ev
  Fix16.add (Fix16.mul p.alphaSurprise s) (Fix16.mul p.betaRegret r)

-- ============================================================
-- 10. EDGE SCORING
-- ============================================================

/-- Compute edge score with Dynamic Canal stress penalty -/
noncomputable def edgeScore (_p : KernelParams) (lane : Lane) (ev : EdgeEval) : Fix16 :=
  let phaseErr := Fix16.abs (Fix16.sub lane.phase ev.edge.attr.prefPhase)
  let stressProxy := Fix16.add
                      (Fix16.mul ev.edge.attr.torsion Fix16.one)
                      (Fix16.mul ev.edge.attr.mismatchGain ev.deltaNorm)
  let stressPenalty := Fix16.mul lane.lambdaEff stressProxy
  Fix16.sub
    (Fix16.sub
      (Fix16.add ev.edge.attr.baseWeight ev.score)
      phaseErr)
    (Fix16.add stressPenalty lane.mismatch)

-- ============================================================
-- 11. REGIME CLASSIFICATION
-- ============================================================

/-- Classify lane regime based on mismatch, stress, and edge type -/
def classifyRegime (p : KernelParams) (lane : Lane) (chosen : Edge) : Regime :=
  if lane.mismatch.raw <= p.coherentThresh.raw &&
     lane.stress.raw <= p.stressThresh.raw then
    Regime.coherent
  else if lane.mismatch.raw >= p.throatThresh.raw && chosen.attr.isThroat then
    Regime.throat
  else
    Regime.stressed

-- ============================================================
-- 12. LANE UPDATE KERNELS (Three Regimes)
-- ============================================================

/-- Coherent flow regime: stable transport -/
def coherentStep (p : KernelParams) (lane : Lane) (chosen : Edge)
                 (deltaNorm : Fix16) (heal : Fix16) (pNext lambdaNext : Fix16) : Lane :=
  let pos' := vecAdd lane.pos (vecAdd lane.vel chosen.attr.dPos)
  let vel' := vecAdd lane.vel chosen.attr.dPos
  let phase' := Fix16.add lane.phase chosen.attr.dPhase
  let stress' := Fix16.max Fix16.zero
                    (Fix16.sub
                      (Fix16.add lane.stress (Fix16.mul p.torsionRate chosen.attr.torsion))
                      (Fix16.mul p.relaxRate Fix16.one))
  let energy' := Fix16.sub
                   (Fix16.add lane.energy chosen.attr.dEnergy)
                   (Fix16.mul p.energyLossRate chosen.attr.loss)
  let mismatch' := Fix16.max Fix16.zero
                      (Fix16.sub
                        (Fix16.add lane.mismatch (Fix16.mul p.mismatchRate deltaNorm))
                        (Fix16.mul p.healRate heal))
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
                 (deltaNorm : Fix16) (heal : Fix16) (pNext lambdaNext : Fix16)
                 (distortion : VecN 3) : Lane :=
  let pos' := vecAdd lane.pos (vecAdd lane.vel (vecAdd chosen.attr.dPos distortion))
  let vel' := vecSub (vecAdd lane.vel chosen.attr.dPos) distortion
  let phase' := Fix16.add lane.phase chosen.attr.dPhase
  let stress' := Fix16.max Fix16.zero
                    (Fix16.sub
                      (Fix16.add
                        (Fix16.add lane.stress (Fix16.mul p.torsionRate chosen.attr.torsion))
                        (Fix16.mul p.mismatchRate lane.mismatch))
                      (Fix16.mul p.relaxRate heal))
  let energy' := Fix16.sub
                   (Fix16.sub
                     (Fix16.add lane.energy chosen.attr.dEnergy)
                     (Fix16.mul p.energyLossRate chosen.attr.loss))
                   lane.stress
  let mismatch' := Fix16.max Fix16.zero
                      (Fix16.sub
                        (Fix16.add lane.mismatch (Fix16.mul p.mismatchRate deltaNorm))
                        (Fix16.mul p.healRate heal))
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
               (deltaNorm : Fix16) (heal : Fix16) (pNext lambdaNext : Fix16)
               (distortion : VecN 3) : Lane :=
  let pos' := vecAdd lane.pos distortion
  let vel' := distortion
  let phase' := Fix16.add lane.phase chosen.attr.dPhase
  let stress' := Fix16.add lane.stress (Fix16.mul p.mismatchRate deltaNorm)
  let energy' := Fix16.max Fix16.zero
                    (Fix16.sub
                      (Fix16.sub lane.energy (Fix16.mul p.energyLossRate chosen.attr.loss))
                      deltaNorm)
  let mismatch' := Fix16.max Fix16.zero
                      (Fix16.sub
                        (Fix16.add lane.mismatch deltaNorm)
                        (Fix16.mul p.healRate heal))
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
  deltaNorm  : Fix16
  heal       : Fix16
  stressReal : Fix16
  pressureNext : Fix16
  lambdaNext : Fix16
  distortion : VecN 3

/-- Compute lane step context (edge selection + pressure update) -/
noncomputable def buildLaneCtx (p : KernelParams) (lane : Lane) (edges : Array Edge)
                 (pickEdge : Lane → Array Edge → Edge)
                 (computeDelta : Lane → Edge → VecN 3)
                 (computeHeal : Lane → Edge → Fix16) : LaneStepCtx :=
  let chosen := pickEdge lane edges
  let deltaVec := computeDelta lane chosen
  let deltaNorm := vecL1 deltaVec
  let heal := computeHeal lane chosen
  let stressReal := Fix16.mul p.alphaSurprise deltaNorm  -- Simplified stress model
  let pNext := Fix16.add (Fix16.mul p.pressureDecay lane.pressure) stressReal
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
             (computeHeal : Lane → Edge → Fix16) : Lane :=
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
def classifyThroat (stableW ruptureW stableD ruptureD w δ : Fix16) : ThroatClass :=
  if w.raw >= stableW.raw && δ.raw <= stableD.raw then
    ThroatClass.stableBridge
  else if w.raw <= ruptureW.raw || δ.raw >= ruptureD.raw then
    ThroatClass.rupture
  else
    ThroatClass.lossyChannel

/-- Update throat state with pressure coupling -/
def stepThroat (p : KernelParams) (sec : CanalSection) (thr : ThroatState) : ThroatState :=
  let compliance0 := Fix16.recip p.lambda0
  let gainP := Fix16.mul p.throatPressureGain (Fix16.sub sec.compliance compliance0)
  let lossδ := Fix16.mul p.throatMismatchLoss thr.mismatchNorm
  let lossS := Fix16.mul p.throatStressLoss sec.meanStress
  let w' := Fix16.max Fix16.zero
               (Fix16.add
                 (Fix16.sub thr.dynWeight lossδ)
                 (Fix16.sub gainP lossS))
  let cls' := classifyThroat
                (Fix16.mk 0x00018000)  -- stable weight threshold (~1.5)
                (Fix16.mk 0x00008000)  -- rupture weight threshold (~0.5)
                (Fix16.mk 0x00010000)  -- stable mismatch threshold (1.0)
                (Fix16.mk 0x00030000)  -- rupture mismatch threshold (3.0)
                w' thr.mismatchNorm
  { thr with dynWeight := w', cls := cls' }

-- ============================================================
-- 15. CANAL SECTION UPDATE (Fluid Mode)
-- ============================================================

/-- Update canal section -/
def stepSection (p : KernelParams) (sec : CanalSection)
                (inFlux outFlux : Fix16) (inflow : Fix16) : CanalSection :=
  -- Pressure update: P' = γ·P + stress
  let stressAvg := sec.meanStress
  let p' := Fix16.add (Fix16.mul p.pressureDecay sec.pressure) stressAvg
  -- Dynamic Canal: lambda_eff(P')
  let lambdaEff := DynamicCanal.dynamicCanalLambda p p'
  let K' := DynamicCanal.canalCompliance p p'
  -- Capacity: C = C₀ + c_P·P - c_R·R - c_m·m
  let cap' := Fix16.sat01
                (Fix16.add
                  (Fix16.sub
                    (Fix16.sub Fix16.one (Fix16.mul p.capacityRoughness sec.roughness))
                    (Fix16.mul p.capacityMismatch sec.meanMismatch))
                  (Fix16.mul p.capacityPressure p'))
  -- Flux conservation: ρ' = ρ - (out - in) - siphon + inflow
  let density' := Fix16.max Fix16.zero
                   (Fix16.sub
                     (Fix16.sub
                       (Fix16.add sec.density inflow)
                       (Fix16.sub outFlux inFlux))
                     sec.siphon)
  -- Effective velocity with compliance gain
  let veff := Fix16.sat01
                (Fix16.add
                  (Fix16.sub
                    (Fix16.sub
                      (Fix16.sub Fix16.one (Fix16.mul p.velDensityLoss density'))
                      (Fix16.mul p.velRoughnessLoss sec.roughness))
                    (Fix16.mul p.velMismatchLoss sec.meanMismatch))
                  (Fix16.mul p.velComplianceGain K'))
  let flux' := Fix16.mul density' veff
  -- Unpack score with pressure-throat interaction
  let unpackScore' :=
    Fix16.add
      (Fix16.add
        (Fix16.add
          (Fix16.mul p.thetaDensity density')
          (Fix16.mul p.thetaMismatch sec.meanMismatch))
        (Fix16.mul p.thetaStress sec.meanStress))
      (Fix16.mul p.thetaPT (Fix16.mul K' sec.throatExposure))
  let unpacked' := unpackScore'.raw >= p.thetaCrit.raw
  {
    sec with
    density     := density'
    capacity    := cap'
    flux        := flux'
    pressure    := p'
    lambdaEff   := lambdaEff
    compliance  := K'
    unpackScore := unpackScore'
    unpacked    := unpacked'
  }

-- ============================================================
-- 16. TOTILITY THEOREMS (Zero-Trust Compliance)
-- ============================================================

/-- All Fix16 operations are total -/
theorem Fix16.add_total (a b : Fix16) : ∃ c, Fix16.add a b = c := by
  simp [Fix16.add]

theorem Fix16.sub_total (a b : Fix16) : ∃ c, Fix16.sub a b = c := by
  simp [Fix16.sub]

theorem Fix16.mul_total (a b : Fix16) : ∃ c, Fix16.mul a b = c := by
  simp [Fix16.mul]

theorem Fix16.div_total (a b : Fix16) : ∃ c, Fix16.div a b = c := by
  simp [Fix16.div]

/-- Dynamic Canal law is total -/
theorem dynamicCanalLambda_total (p : KernelParams) (pressure : Fix16) :
  ∃ lambdaEff, DynamicCanal.dynamicCanalLambda p pressure = lambdaEff := by
  simp [DynamicCanal.dynamicCanalLambda]

/-- All regime steps are total -/
theorem stepLane_total (p : KernelParams) (lane : Lane) (edges : Array Edge)
    (pickEdge : Lane → Array Edge → Edge)
    (computeDelta : Lane → Edge → VecN 3)
    (computeHeal : Lane → Edge → Fix16) :
  ∃ lane', stepLane p lane edges pickEdge computeDelta computeHeal = lane' := by
  simp [stepLane, buildLaneCtx, classifyRegime]

theorem stepSection_total (p : KernelParams) (sec : CanalSection)
    (inFlux outFlux inflow : Fix16) :
  ∃ sec', stepSection p sec inFlux outFlux inflow = sec' := by
  simp [stepSection]

-- ============================================================
-- 17. #EVAL WITNESSES (Self-Test)
-- ============================================================

-- Test fixed-point constructors
#eval Fix16.zero.raw
#eval Fix16.one.raw

-- Test DIAT encoding
#eval DIAT.encode 10

-- Test regime equality
#eval Regime.coherent == Regime.coherent
#eval Regime.stressed == Regime.throat
