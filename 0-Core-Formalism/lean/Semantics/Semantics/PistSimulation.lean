/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

PistSimulation.lean — PIST Data Slice Processing Pipeline

This module models the functional data transformations from the PIST
interactive simulation (Injection → Pruning → Convergence).

Pipeline phases:
  1. Injection — Load raw geometric states into active tensor set
  2. Predictive Pruning — Hardware predictor kills ~95% of doomed paths
  3. Blitter & Gossip — Discrete Picard integral + local gossip clustering

Maps directly to WebGPU compute shader dispatch:
  • Phase 1: VRAM initialization
  • Phase 2: Predictor kernel (early out)
  • Phase 3: Blitter physics kernel + Gossip reduction

Per AGENTS.md §0: Lean is the source of truth.
Per AGENTS.md §1.4: Uses Q16_16 (Fix16) throughout.
-/

import Semantics.FixedPoint
import Semantics.ShellModel
import Semantics.SSMS

namespace Semantics.PistSimulation

open Semantics
open Semantics.ShellModel
open Semantics.SSMS

-- ════════════════════════════════════════════════════════════
-- §1  Tensor Data Structure
-- ════════════════════════════════════════════════════════════

/-- Single particle/data point in the PIST visual simulation.
    Represents a candidate state in the (a,b) perfect-square coordinate space.
    
    Fields:
    • id — Unique identifier for tracking
    • a — Distance from lower perfect square (k²)
    • b — Distance to upper perfect square ((k+1)²)
    • confidence — Gossip-accumulated viability score
    • isActive — Survival flag (false = pruned/dimmed) -/
structure TensorData where
  id : Nat
  a : Q16_16
  b : Q16_16
  confidence : Q16_16
  isActive : Bool
  deriving Repr, DecidableEq, Inhabited

/-- Zero tensor (inactive, zero confidence). -/
def TensorData.zero (id : Nat) : TensorData :=
  { id := id, a := Q16_16.zero, b := Q16_16.zero,
    confidence := Q16_16.zero, isActive := false }


-- ════════════════════════════════════════════════════════════
-- §2  Phase 1: Injection (Canvas Population)
-- ════════════════════════════════════════════════════════════

/-- Maps to visual step where points populate the screen.
    Loads raw (a,b,confidence) tuples into active TensorData array.
    
    In WebGPU execution: this initializes VRAM with geometric states.
    Each tensor maps to one workgroup thread's initial state. -/
def injectDataSlice (rawInputs : Array (Q16_16 × Q16_16 × Q16_16)) : Array TensorData :=
  rawInputs.mapIdx (λ i val => 
    { id := i,
      a := val.1, 
      b := val.2.1, 
      confidence := val.2.2, 
      isActive := true })

/-- Alternative injection from shell state indices.
    Converts event indices to (a,b) coordinates for PIST simulation. -/
def injectFromShellStates (indices : List Nat) : Array TensorData :=
  let coords := indices.map (λ n => 
    let s := shellState n
    (Q16_16.ofInt (Int.ofNat s.a), 
     Q16_16.ofInt (Int.ofNat s.b),
     Q16_16.ofInt (Int.ofNat (s.a * s.b))))
  injectDataSlice coords.toArray


-- ════════════════════════════════════════════════════════════
-- §3  Phase 2: Predictive Pruning (Heuristic Guillotine)
-- ════════════════════════════════════════════════════════════

/-- Hardware viability predictor.
    Evaluates fast geometric heuristic to kill doomed paths early.
    
    PIST criterion: |a - b| > threshold indicates far from perfect square.
    Near-perfect-squares have a ≈ b (symmetric position in shell).
    
    Returns true if particle survives pruning. -/
def predictViability (a b confidence : Q16_16) : Bool :=
  let diff := Q16_16.abs (Q16_16.sub a b)
  let threshold := Q16_16.ofInt 2  -- Within 2 units of symmetry
  let confThreshold := Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 10)  -- 0.1 confidence minimum
  Q16_16.lt diff threshold && Q16_16.gt confidence confThreshold

/-- Phase 2: Apply predictive pruning to entire dataset.
    Maps to visual step where ~95% of points turn dim and stop.
    
    In WebGPU: This is a compute kernel with early-out for pruned threads. -/
def phase2Pruning (dataset : Array TensorData) : Array TensorData :=
  dataset.map (λ pt =>
    if pt.isActive then
      let viable := predictViability pt.a pt.b pt.confidence
      -- If not viable: particle "turns red and fades out"
      { pt with isActive := viable, 
                confidence := if viable then pt.confidence else Q16_16.zero }
    else pt)


-- ════════════════════════════════════════════════════════════
-- §4  Phase 3: Blitter & Gossip (Convergence)
-- ════════════════════════════════════════════════════════════

/-- Discrete Picard Integral (Blitter) step.
    Model 131 ODE: F(a,b,ε) = (1 + ε(0.5b + 0.3), -1 + ε(0.5a - 0.3))
    
    Performs one timestep of O(1) discrete integration:
      a' = a + ε · (1 + 0.5·b + 0.3)
      b' = b + ε · (-1 + 0.5·a - 0.3)
    
    Maps to WGSL: `blit_result = blit_op(fa, fb, timestep_mask)` -/
def picardBlitStep (a b epsilon : Q16_16) : Q16_16 × Q16_16 :=
  let half := Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 2)
  let c3 := Q16_16.div (Q16_16.ofInt 3) (Q16_16.ofInt 10)
  let fa := Q16_16.add (Q16_16.ofInt 1) 
    (Q16_16.mul epsilon (Q16_16.add (Q16_16.mul half b) c3))
  let fb := Q16_16.add (Q16_16.ofInt (-1))
    (Q16_16.mul epsilon (Q16_16.sub (Q16_16.mul half a) c3))
  let nextA := Q16_16.add a (Q16_16.mul epsilon fa)
  let nextB := Q16_16.add b (Q16_16.mul epsilon fb)
  (nextA, nextB)

/-- Local gossip confidence aggregation.
    Simulates neighbor-to-neighbor confidence sharing in workgroup.
    
    In WebGPU: This uses shared memory / LDS for neighbor access.
    Returns updated confidence from local neighborhood average. -/
def localGossip (neighbors : Array Q16_16) (selfConfidence : Q16_16) : Q16_16 :=
  if neighbors.size = 0 then selfConfidence
  else
    let sum := neighbors.foldl (λ acc c => Q16_16.add acc c) Q16_16.zero
    let avg := Q16_16.div sum (Q16_16.ofInt (Int.ofNat neighbors.size))
    -- Weighted mix: 70% self + 30% neighbor average
    let mixed := Q16_16.add (Q16_16.mul (Q16_16.div (Q16_16.ofInt 7) (Q16_16.ofInt 10)) selfConfidence)
                            (Q16_16.mul (Q16_16.div (Q16_16.ofInt 3) (Q16_16.ofInt 10)) avg)
    mixed

/-- Phase 3: Single simulation tick.
    Maps to visual step where surviving points cluster together.
    
    One "frame" of physics simulation:
      1. Blitter update (move toward perfect square)
      2. Local gossip (pull toward neighbor confidence)
    
    In WebGPU: Dispatch compute shader with barrier between steps. -/
def phase3Tick (dataset : Array TensorData) : Array TensorData :=
  dataset.map (λ pt =>
    if pt.isActive then
      -- Step 1: Discrete Picard Integral (particle moves toward resonance)
      let epsilon := Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 10)  -- ε = 0.1
      let (nextA, nextB) := picardBlitStep pt.a pt.b epsilon
      
      -- Step 2: Local Gossip (pull toward neighbor confidence)
      -- Neighbors are mod 8 in workgroup for L1 cache efficiency
      let neighborIds := List.range 8 |>.map (λ i => (pt.id + i) % dataset.size)
      let neighbors := neighborIds.filterMap (λ i => 
        if i < dataset.size then some (dataset[i]!.confidence) else none)
      let gossipConf := localGossip neighbors.toArray pt.confidence
      
      { pt with a := nextA, b := nextB, confidence := gossipConf }
    else pt)


-- ════════════════════════════════════════════════════════════
-- §5  Full Pipeline Execution
-- ════════════════════════════════════════════════════════════

/-- Execute complete PIST simulation pipeline.
    
    Steps:
      1. Inject raw (a,b,confidence) states
      2. Apply predictive pruning (kill doomed paths)
      3. Run Blitter+Gossip for N frames
    
    Returns final clustered states (the Perfect Square solutions).
    
    Maps to WebGPU sequence:
      • vkCmdDispatch(Phase1_Init)
      • vkCmdDispatch(Phase2_Prune)
      • for i in 0..frames: vkCmdDispatch(Phase3_BlitGossip) -/
def executePipeline (rawInputs : Array (Q16_16 × Q16_16 × Q16_16)) (frames : Nat) : Array TensorData :=
  -- Step 1: Populate canvas
  let injected := injectDataSlice rawInputs
  
  -- Step 2: Apply heuristic (kill doomed paths instantly)
  let pruned := phase2Pruning injected
  
  -- Step 3: Run physics for 'frames' iterations
  let rec loop (data : Array TensorData) (f : Nat) : Array TensorData :=
    match f with
    | 0 => data
    | f' + 1 => loop (phase3Tick data) f'
  loop pruned frames

/-- Execute pipeline from shell event indices.
    Convenience wrapper for AVMR/SSMS integration. -/
def executeFromShellIndices (indices : List Nat) (frames : Nat) : Array TensorData :=
  let rawInputs := indices.map (λ n => 
    let s := shellState n
    (Q16_16.ofInt (Int.ofNat s.a),
     Q16_16.ofInt (Int.ofNat s.b),
     Q16_16.ofInt (Int.ofNat (s.a * s.b))))
  executePipeline rawInputs.toArray frames


-- ════════════════════════════════════════════════════════════
-- §4b  Spectral Refinement — Gauss-Jordan Least-Squares (Rietveld-PIST)
-- ════════════════════════════════════════════════════════════

-- All types below are inlined from the former Astrophysics modules
-- to keep PistSimulation.lean self-contained and policy-clean.

/-- Bragg peak descriptor (pure Q16_16, no strings, no Float). -/
structure BraggPeak where
  position : Q16_16
  height   : Q16_16
  width    : Q16_16
  deriving Repr

/-- Simplified pseudo-Voigt profile in Q16_16.
    Gaussian approximation: height / (1 + dist²/width²). -/
def pseudoVoigtQ16 (peak : BraggPeak) (x : Q16_16) : Q16_16 :=
  let dist := if Q16_16.lt x peak.position then Q16_16.sub peak.position x else Q16_16.sub x peak.position
  let distSq := Q16_16.mul dist dist
  let widthSq := Q16_16.mul peak.width peak.width
  let denom := Q16_16.add Q16_16.one (Q16_16.div distSq widthSq)
  Q16_16.div peak.height denom

/-- χ² between observed and model value lists. -/
def chiSqWindow (observed model : List Q16_16) : Q16_16 :=
  let pairs := observed.zip model
  let sqDiffs := pairs.map (λ (o, m) =>
    let diff := Q16_16.sub o m
    Q16_16.mul diff diff)
  sqDiffs.foldl Q16_16.add Q16_16.zero

/-- Magnetic domain descriptor (pure Q16_16, no string fields). -/
structure MagneticDomain where
  domainId : Nat
  centerFreq : Q16_16
  sizeQ16 : Q16_16
  totalIntensity : Q16_16
  numPeaks : Nat
  deltaNegative : Bool   -- true = NÉEL (Δ<0), false = BLOCH (Δ≥0)
  deriving Repr, Inhabited

/-- Scale width to domain size proxy. -/
def domainSizeFromWidth (w : Q16_16) : Q16_16 := Q16_16.mul w (Q16_16.ofNat 2)

/-- Semantic regime as an inductive type (compute-path, no strings). -/
inductive MagneticRegime
  | bloch
  | neel
  | uglyAsymmetricPruning
  | horribleManifoldTearing
  deriving Repr, BEq

/-- Display function: maps inductive regime to human string at the boundary. -/
def regimeToString (r : MagneticRegime) : String :=
  match r with
  | .bloch => "BLOCH"
  | .neel => "NÉEL"
  | .uglyAsymmetricPruning => "uglyAsymmetricPruning"
  | .horribleManifoldTearing => "horribleManifoldTearing"

/-- Classify a list of domains into a regime. -/
def domainRegime (domains : List MagneticDomain) : MagneticRegime :=
  if domains.isEmpty then MagneticRegime.uglyAsymmetricPruning
  else
    let d := domains.head!
    if d.numPeaks == 0 then MagneticRegime.uglyAsymmetricPruning
    else if d.numPeaks > 1 then MagneticRegime.horribleManifoldTearing
    else if d.deltaNegative then MagneticRegime.neel
    else MagneticRegime.bloch

/-- Small-matrix row: up to 4 elements for 3×3 + RHS systems. -/
abbrev MatRow := Array Q16_16

/-- Augmented matrix for Gauss-Jordan: n rows × (n+1) columns. -/
abbrev AugMat := Array MatRow

def swapRows (m : AugMat) (i j : Nat) : AugMat :=
  if i < m.size && j < m.size then
    let ri := m[i]!
    let rj := m[j]!
    m.set! i rj |>.set! j ri
  else m

def scaleRow (row : MatRow) (factor : Q16_16) : MatRow :=
  row.map (λ v => Q16_16.mul v factor)

def addScaledRow (target : MatRow) (source : MatRow) (scale : Q16_16) : MatRow :=
  target.zip source |>.map (λ (t, s) => Q16_16.add t (Q16_16.mul scale s))

private def findPivot (m : AugMat) (col startRow : Nat) : Nat :=
  let rec search (r : Nat) (bestRow : Nat) (bestVal : Q16_16) : Nat :=
    if r >= m.size then bestRow
    else
      let row := m[r]!
      let v := row[col]!
      let absV := Q16_16.abs v
      if Q16_16.gt absV bestVal then search (r + 1) r absV
      else search (r + 1) bestRow bestVal
  search startRow startRow Q16_16.zero

private def eliminateColumn (m : AugMat) (col : Nat) (nRows : Nat) : AugMat :=
  let pivotRow := m[col]!
  let rec elim (m' : AugMat) (r : Nat) : AugMat :=
    if r >= nRows then m'
    else if r = col then elim m' (r + 1)
    else
      let row := m'[r]!
      let factor := Q16_16.neg (row[col]!)
      let newRow := addScaledRow row pivotRow factor
      elim (m'.set! r newRow) (r + 1)
  elim m 0

/-- Gauss-Jordan elimination for small linear systems (Ax = b).
    Returns solution vector x (last column of reduced matrix).
    Singular matrices yield a zero vector. -/
def gaussJordanSolve (mat : AugMat) : Array Q16_16 :=
  let n := mat.size
  let rec forward (m : AugMat) (col : Nat) : AugMat :=
    match col with
    | 0 => m
    | c' + 1 =>
        let pivotRow := findPivot m c' c'
        let m1 := swapRows m c' pivotRow
        let pivotRowData := m1[c']!
        let pivotVal := pivotRowData[c']!
        if pivotVal.val = 0 then m1
        else
          let invPivot := Q16_16.recip pivotVal
          let rowNormed := scaleRow pivotRowData invPivot
          let m2 := m1.set! c' rowNormed
          let m3 := eliminateColumn m2 c' n
          forward m3 c'
  let reduced := forward mat n
  reduced.map (λ row => if row.size > n then row[n]! else Q16_16.zero)

-- ════════════════════════════════════════════════════════════
-- §4c  Matrix Packet (G = AᵀA, det, rank, spectral witness)
-- ════════════════════════════════════════════════════════════

def matGet (m : Array (Array Q16_16)) (i j : Nat) : Q16_16 :=
  if h₁ : i < m.size then
    let row := m[i]
    if h₂ : j < row.size then row[j] else Q16_16.zero
  else Q16_16.zero

def det3 (m : Array (Array Q16_16)) : Q16_16 :=
  let a := matGet m 0 0; let b := matGet m 0 1; let c := matGet m 0 2
  let d := matGet m 1 0; let e := matGet m 1 1; let f := matGet m 1 2
  let g := matGet m 2 0; let h := matGet m 2 1; let i := matGet m 2 2
  let term1 := Q16_16.mul a (Q16_16.sub (Q16_16.mul e i) (Q16_16.mul f h))
  let term2 := Q16_16.mul b (Q16_16.sub (Q16_16.mul d i) (Q16_16.mul f g))
  let term3 := Q16_16.mul c (Q16_16.sub (Q16_16.mul d h) (Q16_16.mul e g))
  Q16_16.add term1 (Q16_16.sub term3 term2)

def trace3 (m : Array (Array Q16_16)) : Q16_16 :=
  Q16_16.add (matGet m 0 0) (Q16_16.add (matGet m 1 1) (matGet m 2 2))

def rank3 (m : Array (Array Q16_16)) : Nat :=
  if (det3 m).val != 0 then 3
  else
    let minors : List Q16_16 := [
      Q16_16.sub (Q16_16.mul (matGet m 0 0) (matGet m 1 1)) (Q16_16.mul (matGet m 0 1) (matGet m 1 0)),
      Q16_16.sub (Q16_16.mul (matGet m 0 0) (matGet m 1 2)) (Q16_16.mul (matGet m 0 2) (matGet m 1 0)),
      Q16_16.sub (Q16_16.mul (matGet m 0 1) (matGet m 1 2)) (Q16_16.mul (matGet m 0 2) (matGet m 1 1)),
      Q16_16.sub (Q16_16.mul (matGet m 0 0) (matGet m 2 1)) (Q16_16.mul (matGet m 0 1) (matGet m 2 0)),
      Q16_16.sub (Q16_16.mul (matGet m 0 0) (matGet m 2 2)) (Q16_16.mul (matGet m 0 2) (matGet m 2 0)),
      Q16_16.sub (Q16_16.mul (matGet m 0 1) (matGet m 2 2)) (Q16_16.mul (matGet m 0 2) (matGet m 2 1)),
      Q16_16.sub (Q16_16.mul (matGet m 1 0) (matGet m 2 1)) (Q16_16.mul (matGet m 1 1) (matGet m 2 0)),
      Q16_16.sub (Q16_16.mul (matGet m 1 0) (matGet m 2 2)) (Q16_16.mul (matGet m 1 2) (matGet m 2 0)),
      Q16_16.sub (Q16_16.mul (matGet m 1 1) (matGet m 2 2)) (Q16_16.mul (matGet m 1 2) (matGet m 2 1))
    ]
    if minors.any (λ v => v.val != 0) then 2
    else
      let elems := [matGet m 0 0, matGet m 0 1, matGet m 0 2,
                    matGet m 1 0, matGet m 1 1, matGet m 1 2,
                    matGet m 2 0, matGet m 2 1, matGet m 2 2]
      if elems.any (λ v => v.val != 0) then 1
      else 0

structure MatrixPacket where
  gram     : Array (Array Q16_16)
  det      : Q16_16
  trace    : Q16_16
  rank     : Nat
  nullity  : Nat
  spectral : Array (Array Q16_16)
  chiSq    : Q16_16
  deriving Repr

def spectralPlaceholder : Array (Array Q16_16) := #[
  #[Q16_16.one, Q16_16.zero, Q16_16.zero],
  #[Q16_16.zero, Q16_16.one, Q16_16.zero],
  #[Q16_16.zero, Q16_16.zero, Q16_16.one]
]

def buildMatrixPacket (_window : List Q16_16) : MatrixPacket :=
  let s0 := Q16_16.ofNat 8
  let s1 := Q16_16.ofNat 28
  let s2 := Q16_16.ofNat 140
  let s3 := Q16_16.ofNat 784
  let s4 := Q16_16.ofNat 4676
  let gram := #[
    #[s0, s1, s2],
    #[s1, s2, s3],
    #[s2, s3, s4]
  ]
  let d := det3 gram
  let r := rank3 gram
  let t := trace3 gram
  { gram := gram, det := d, trace := t, rank := r, nullity := 3 - r,
    spectral := spectralPlaceholder, chiSq := Q16_16.zero }

-- ════════════════════════════════════════════════════════════
-- §4d  Quadratic LSQ Fit and Packet
-- ════════════════════════════════════════════════════════════

def quadraticFitCoeffs (window : List Q16_16) : Array Q16_16 :=
  let n := 8
  let s0 := Q16_16.ofNat n
  let s1 := Q16_16.ofNat 28
  let s2 := Q16_16.ofNat 140
  let s3 := Q16_16.ofNat 784
  let s4 := Q16_16.ofNat 4676
  let rec computeSums (idx : Nat) (ys : List Q16_16)
      (sy : Q16_16) (sxy : Q16_16) (sx2y : Q16_16) : Q16_16 × Q16_16 × Q16_16 :=
    match ys with
    | [] => (sy, sxy, sx2y)
    | y :: rest =>
        let x := Q16_16.ofNat idx
        let x2 := Q16_16.mul x x
        computeSums (idx + 1) rest
          (Q16_16.add sy y)
          (Q16_16.add sxy (Q16_16.mul x y))
          (Q16_16.add sx2y (Q16_16.mul x2 y))
  let (rhs0, rhs1, rhs2) := computeSums 0 window Q16_16.zero Q16_16.zero Q16_16.zero
  let mat : AugMat := #[
    #[s0, s1, s2, rhs0],
    #[s1, s2, s3, rhs1],
    #[s2, s3, s4, rhs2]
  ]
  gaussJordanSolve mat

def quadraticDiscriminant (c0 c1 c2 : Q16_16) : Q16_16 :=
  Q16_16.sub (Q16_16.mul c1 c1) (Q16_16.mul (Q16_16.mul (Q16_16.ofNat 4) c2) c0)

structure QuadraticPacket where
  a : Q16_16
  h : Q16_16
  k : Q16_16
  delta : Q16_16
  width : Q16_16
  chiSq : Q16_16
  deriving Repr

def spectralEnergy (peak : BraggPeak) (window : List Q16_16) : Q16_16 :=
  let modelVals := window.mapIdx (fun idx _obs => pseudoVoigtQ16 peak (Q16_16.ofNat idx))
  chiSqWindow window modelVals

def coeffsToPacket (coeffs : Array Q16_16) (window : List Q16_16) : QuadraticPacket :=
  if coeffs.size < 3 then
    { a := Q16_16.zero, h := Q16_16.zero, k := Q16_16.zero,
      delta := Q16_16.zero, width := Q16_16.one, chiSq := Q16_16.zero }
  else
    let c0 := coeffs[0]!
    let c1 := coeffs[1]!
    let c2 := coeffs[2]!
    let delta := quadraticDiscriminant c0 c1 c2
    if c2.val = 0 then
      let avg := Q16_16.div (window.foldl Q16_16.add Q16_16.zero) (Q16_16.ofNat window.length)
      { a := Q16_16.zero, h := Q16_16.zero, k := avg,
        delta := delta, width := Q16_16.one, chiSq := Q16_16.zero }
    else
      let twoC2 := Q16_16.mul (Q16_16.ofNat 2) c2
      let h := Q16_16.div (Q16_16.neg c1) twoC2
      let c1sq := Q16_16.mul c1 c1
      let fourC2 := Q16_16.mul (Q16_16.ofNat 4) c2
      let k := Q16_16.sub c0 (Q16_16.div c1sq fourC2)
      let negK := Q16_16.neg k
      let twoA := Q16_16.mul (Q16_16.ofNat 2) c2
      let ratio := if twoA.val = 0 then Q16_16.zero else Q16_16.div negK twoA
      let widthApprox := if Q16_16.lt ratio Q16_16.zero then Q16_16.one
                         else Q16_16.add Q16_16.one (Q16_16.div ratio (Q16_16.ofNat 2))
      let peak : BraggPeak := { position := h, height := k, width := widthApprox }
      let chi := spectralEnergy peak window
      { a := c2, h := h, k := k, delta := delta,
        width := widthApprox, chiSq := chi }

def packetToPeak (pkt : QuadraticPacket) : BraggPeak :=
  { position := pkt.h, height := pkt.k, width := pkt.width }

def coeffsToPeak (coeffs : Array Q16_16) : BraggPeak :=
  packetToPeak (coeffsToPacket coeffs [])

def spectralRefineLsq (window : List Q16_16) : QuadraticPacket :=
  coeffsToPacket (quadraticFitCoeffs window) window

def spectralPacketToDomain (pkt : QuadraticPacket) (domainId : Nat) : MagneticDomain :=
  { domainId := domainId
  , centerFreq := pkt.h
  , sizeQ16 := domainSizeFromWidth pkt.width
  , totalIntensity := pkt.k
  , numPeaks := 1
  , deltaNegative := Q16_16.lt pkt.delta Q16_16.zero
  }

def spectralWindowToRegime (window : List Q16_16) : MagneticRegime :=
  let pkt := spectralRefineLsq window
  let domain := spectralPacketToDomain pkt 0
  domainRegime [domain]

def packetToRegime (pkt : QuadraticPacket) : MagneticRegime :=
  let domain := spectralPacketToDomain pkt 0
  domainRegime [domain]

-- ════════════════════════════════════════════════════════════
-- §4e  Chaos Game Affine IFS Iterative Refinement
-- ════════════════════════════════════════════════════════════

structure ChaosState where
  position : Q16_16
  height   : Q16_16
  width    : Q16_16
  deriving Repr

def chaosContractionStep (s : ChaosState) (anchor : ChaosState) (r : Q16_16) : ChaosState :=
  let oneMinusR := Q16_16.sub Q16_16.one r
  let newPos := Q16_16.add (Q16_16.mul oneMinusR anchor.position) (Q16_16.mul r s.position)
  let newHeight := Q16_16.add (Q16_16.mul oneMinusR anchor.height) (Q16_16.mul r s.height)
  let newWidth := Q16_16.add (Q16_16.mul oneMinusR anchor.width) (Q16_16.mul r s.width)
  { position := newPos, height := newHeight, width := newWidth }

def chaosStateDiff (s1 s2 : ChaosState) : Q16_16 :=
  let dPos := Q16_16.abs (Q16_16.sub s1.position s2.position)
  let dHeight := Q16_16.abs (Q16_16.sub s1.height s2.height)
  let dWidth := Q16_16.abs (Q16_16.sub s1.width s2.width)
  Q16_16.add dPos (Q16_16.add dHeight dWidth)

def packetToChaosState (pkt : QuadraticPacket) : ChaosState :=
  { position := pkt.h, height := pkt.k, width := pkt.width }

def chaosStateToPacket (s : ChaosState) (window : List Q16_16) : QuadraticPacket :=
  let peak : BraggPeak := { position := s.position, height := s.height, width := s.width }
  let chi := spectralEnergy peak window
  let a := Q16_16.recip (Q16_16.mul s.width s.width)
  let delta := Q16_16.neg (Q16_16.mul (Q16_16.mul (Q16_16.ofNat 4) a) s.height)
  { a := a, h := s.position, k := s.height, delta := delta,
    width := s.width, chiSq := chi }

def chaosConverge
    (initial : ChaosState)
    (anchor : ChaosState)
    (_window : List Q16_16)
    (r : Q16_16)
    (threshold : Q16_16)
    (maxSteps : Nat)
    : ChaosState × Nat :=
  let rec loop (s : ChaosState) (steps : Nat) (iter : Nat) : ChaosState × Nat :=
    match steps with
    | 0 => (s, iter)
    | steps' + 1 =>
        let sNext := chaosContractionStep s anchor r
        let diff := chaosStateDiff sNext s
        if Q16_16.lt diff threshold then (sNext, iter + 1)
        else loop sNext steps' (iter + 1)
  loop initial maxSteps 0

def spectralRefineChaos
    (window : List Q16_16)
    (r : Q16_16)
    (threshold : Q16_16)
    (maxSteps : Nat)
    : QuadraticPacket × Nat :=
  let lsqPkt := spectralRefineLsq window
  let anchor := packetToChaosState lsqPkt
  let perturbScale := Q16_16.ofRatio 1 10
  let initial := {
    position := Q16_16.add anchor.position (Q16_16.mul perturbScale Q16_16.one),
    height := Q16_16.add anchor.height (Q16_16.mul perturbScale Q16_16.one),
    width := Q16_16.add anchor.width (Q16_16.mul perturbScale Q16_16.one)
  }
  let (refined, steps) := chaosConverge initial anchor window r threshold maxSteps
  let pkt := chaosStateToPacket refined window
  (pkt, steps)

def spectralWindowToRegimeChaos (window : List Q16_16) : MagneticRegime :=
  let (pkt, _steps) := spectralRefineChaos window (Q16_16.ofRatio 1 2) (Q16_16.ofRatio 1 100) 20
  let domain := spectralPacketToDomain pkt 0
  domainRegime [domain]

-- ════════════════════════════════════════════════════════════
-- §6  Verification Examples
-- ════════════════════════════════════════════════════════════

#eval predictViability (Q16_16.ofInt 4) (Q16_16.ofInt 5) (Q16_16.ofInt 10)
#eval predictViability (Q16_16.ofInt 1) (Q16_16.ofInt 20) (Q16_16.ofInt 10)
#eval picardBlitStep (Q16_16.ofInt 4) (Q16_16.ofInt 5) (Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 10))
#eval executePipeline #[(Q16_16.ofInt 4, Q16_16.ofInt 5, Q16_16.ofInt 20)] 5

-- ════════════════════════════════════════════════════════════
-- §6b  Spectral Refinement Verification
-- ════════════════════════════════════════════════════════════

def fixtureSpectralWindow : List Q16_16 := [
  ⟨655360⟩, ⟨1310720⟩, ⟨6553600⟩, ⟨2621440⟩,
  ⟨1310720⟩, ⟨655360⟩, ⟨327680⟩, ⟨327680⟩
]

#eval! quadraticFitCoeffs fixtureSpectralWindow
#eval! spectralRefineLsq fixtureSpectralWindow
#eval! packetToPeak (spectralRefineLsq fixtureSpectralWindow)
#eval! (spectralRefineLsq fixtureSpectralWindow).chiSq
#eval! (spectralRefineLsq fixtureSpectralWindow).delta
#eval! spectralWindowToRegime fixtureSpectralWindow
#eval! packetToRegime (spectralRefineLsq fixtureSpectralWindow)
#eval! packetToChaosState (spectralRefineLsq fixtureSpectralWindow)
#eval! chaosContractionStep
  (packetToChaosState (spectralRefineLsq fixtureSpectralWindow))
  (packetToChaosState (spectralRefineLsq fixtureSpectralWindow))
  (Q16_16.ofRatio 1 2)
#eval! spectralRefineChaos fixtureSpectralWindow (Q16_16.ofRatio 1 2) (Q16_16.ofRatio 1 100) 20
#eval! spectralWindowToRegimeChaos fixtureSpectralWindow
#eval! buildMatrixPacket fixtureSpectralWindow

end Semantics.PistSimulation
