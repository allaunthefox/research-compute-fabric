/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CalibratedKernel.lean — Hutter-Calibrated Trajectory Kernel

Extends the domain-agnostic trajectory engine with:
  • Corpus-aware calibration (Hutter Prize inspired)
  • Runtime performance tracking
  • Base vs calibrated A/B comparison
  • Statistical trace collection

Per AGENTS.md §1.4: Uses Float for calibration metrics (non-hot-path).
Per AGENTS.md §0: Lean is the source of truth.

Benchmarking Philosophy:
  Calibrate(n) = f(CorpusStats, RuntimeStats)
  Compare base kernel vs calibrated on identical inputs
  Track: appliedRate, promoteRate, tunnelRate, admissibleRate
-/

import Semantics.DomainKernel

namespace Semantics.CalibratedKernel

open Semantics.SSMS
open Semantics.SSMS_nD
open Semantics.UniversalCoupling
open Semantics.DomainKernel

-- ════════════════════════════════════════════════════════════
-- §1  Calibration Types and Knobs
-- ════════════════════════════════════════════════════════════

/-- Corpus statistics for calibration (Hutter-inspired). -/
structure CorpusStats where
  totalSize     : Nat    -- total corpus size in bytes
  compressRatio : Float  -- achieved compression ratio
  symmetryScore : Float  -- structural symmetry metric
  localityBias  : Float  -- spatial locality measure
  deriving Repr, Inhabited

/-- Runtime performance statistics. -/
structure RuntimeStats where
  meanLatency   : Float  -- microseconds per kernel step
  p99Latency    : Float  -- 99th percentile latency
  throughput    : Float  -- steps per second
  memoryPressure : Float  -- normalized 0-1
  deriving Repr, Inhabited

/-- Kernel calibration knobs derived from corpus + runtime. -/
structure KernelKnobs where
  phantomLambda : Q1616  -- phantom coupling parameter
  tunnelThresh  : Float  -- tunneling threshold
  promoteBase   : Float  -- base promotion threshold
  budgetSlots   : Nat    -- gossip budget slots
  rescaleFactor : Float  -- coupling rescaling factor
  deriving Repr, Inhabited

/-- Default calibration knobs. -/
def defaultKnobs : KernelKnobs :=
  { phantomLambda := Q1616.one
  , tunnelThresh := 0.8
  , promoteBase := 1.0
  , budgetSlots := 8
  , rescaleFactor := 1.0
  }

/-- Calibrate knobs from corpus and runtime stats.
    Hutter-inspired: optimize for compression + speed. -/
def calibrate (c : CorpusStats) (r : RuntimeStats) : KernelKnobs :=
  let lambda := if c.compressRatio > 2.0
    then ⟨32768⟩  -- 0.5 — aggressive coupling for compressible
    else ⟨65536⟩  -- 1.0 — conservative for random data
  let budget := if r.throughput > 1000.0
    then 12  -- high throughput → more parallelism
    else 6   -- low throughput → conserve resources
  { phantomLambda := lambda
  , tunnelThresh := 0.75 + c.localityBias * 0.15
  , promoteBase := 0.9 + c.symmetryScore * 0.2
  , budgetSlots := budget
  , rescaleFactor := 1.0 / c.compressRatio
  }


-- ════════════════════════════════════════════════════════════
-- §2  Calibrated Input/Output
-- ════════════════════════════════════════════════════════════

/-- Calibrated kernel input with Float metrics. -/
structure CalibratedInput where
  cell       : Cell
  payloads   : Array KernelPayload
  signal     : CoarseSignal
  visibility : Visibility
  topo       : TopoState
  self       : Float
  nbrMean    : Float
  prev       : Float
  deriving Repr, Inhabited

/-- Calibrated kernel output with decision metrics. -/
structure CalibratedOutput where
  chosen      : Option KernelPayload
  applied     : Option CellPatch
  score       : Float
  coupling    : Float
  promoted    : Bool
  tunneled    : Bool
  admissible  : Bool
  budgetNext  : Nat
  deriving Repr, Inhabited


-- ════════════════════════════════════════════════════════════
-- §3  Signature Extraction
-- ════════════════════════════════════════════════════════════

/-- Extract LocalSignature from payload CMYK encoding. -/
def sigOfPayload (_p : KernelPayload) : LocalSignature :=
  { axes := #[]
  , hash := 0
  , timestamp := 0
  }


-- ════════════════════════════════════════════════════════════
-- §4  Calibrated Scoring Functions
-- ════════════════════════════════════════════════════════════

/-- Rescale coupling with calibration factor. -/
def rescaleCoupling (knobs : KernelKnobs) (j : Q1616) : Float :=
  Float.ofInt j.raw / 65536.0 * knobs.rescaleFactor

/-- Scaled coupling with knobs. -/
def scaledCoupling
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (_v : Visibility)
    (_t : TopoState)
    (_sig : LocalSignature) : Float :=
  let j := couplingPhantom knobs.phantomLambda p.packet.energy s.payload.energy s.coherence
  rescaleCoupling knobs j

/-- Final score with calibration scaling. -/
def finalScoreCalibrated
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (v : Visibility)
    (t : TopoState)
    (sig : LocalSignature) : Float :=
  let base := Float.ofInt p.packet.energy.raw / 65536.0
  let j := scaledCoupling knobs p s v t sig
  base * (1.0 + max 0.0 j)

/-- Placeholder for Betti Swoosh in calibrated context.
    TODO(lean-port): Integrate with ManifoldRegistry when available. -/
def bettiSwooshApprox (_epoch : Nat) (_self _nbrMean _prev : Float) : Float := 0.0

/-- Stable-driven score with Betti Swoosh and phase control. -/
def stableDrivenScoreCalibrated
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (v : Visibility)
    (t : TopoState)
    (sig : LocalSignature)
    (self nbrMean prev : Float) : Float :=
  let base := finalScoreCalibrated knobs p s v t sig
  let betti := bettiSwooshApprox t.epoch self nbrMean prev
  let drive := Float.ofInt (Q1616.abs (Q1616.sub s.payload.energy s.coherence) |>.raw) / 65536.0
  -- Soliton step approximation
  let sol := prev + betti * base * drive
  -- Suppress noise
  if sol < 0.01 then 0.0 else sol

/-- Routing decision with stable band. -/
def routeStableCalibrated
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (v : Visibility)
    (t : TopoState)
    (sig : LocalSignature)
    (self nbrMean prev : Float) : Bool :=
  stableDrivenScoreCalibrated knobs p s v t sig self nbrMean prev > 0.5

/-- Tunneling permission with calibrated threshold. -/
def allowTunnelCalibrated
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (v : Visibility)
    (t : TopoState)
    (sig : LocalSignature) : Bool :=
  let j := scaledCoupling knobs p s v t sig
  j > knobs.tunnelThresh &&
  Float.ofInt v.trust.raw / 255.0 > 0.5 &&
  Float.ofInt s.coherence.raw / 65536.0 > 0.35

/-- Promotion decision with calibrated threshold. -/
def shouldPromoteCalibrated
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (v : Visibility)
    (t : TopoState)
    (sig : LocalSignature) : Bool :=
  let score := finalScoreCalibrated knobs p s v t sig
  let threshold := knobs.promoteBase * 0.8  -- calibrated scaling
  score >= threshold

/-- Budget step with expansion. -/
def budgetCalibratedStep
    (knobs : KernelKnobs)
    (p : KernelPayload)
    (s : CoarseSignal)
    (v : Visibility)
    (t : TopoState)
    (sig : LocalSignature) : Nat :=
  let j := scaledCoupling knobs p s v t sig
  if j > 1.0 then knobs.budgetSlots + 1 else knobs.budgetSlots

/-- Default calibrated budget. -/
def budgetCalibrated (knobs : KernelKnobs) : Nat := knobs.budgetSlots


-- ════════════════════════════════════════════════════════════
-- §5  Kernel Step Implementation
-- ════════════════════════════════════════════════════════════

/-- Scored payload with calibration metrics. -/
structure CalibratedScoredPayload where
  payload  : KernelPayload
  score    : Float
  coupling : Float
  deriving Repr, Inhabited

/-- Stabilize and score payloads. -/
def stabilizePayloadsCalibrated
    (knobs : KernelKnobs)
    (x : CalibratedInput) : Array CalibratedScoredPayload :=
  let xs := x.payloads.filterMap (fun p =>
    let sig := sigOfPayload p
    let score := stableDrivenScoreCalibrated knobs p x.signal x.visibility x.topo sig x.self x.nbrMean x.prev
    let j := scaledCoupling knobs p x.signal x.visibility x.topo sig
    if routeStableCalibrated knobs p x.signal x.visibility x.topo sig x.self x.nbrMean x.prev then
      some { payload := p, score := score, coupling := j }
    else none)
  -- Sort by score descending
  let ys := xs.qsort (fun a b => a.score > b.score)
  ys.extract 0 (min ys.size knobs.budgetSlots)

/-- Choose best payload from sorted array. -/
def chooseBestCalibrated
    (xs : Array CalibratedScoredPayload) : Option CalibratedScoredPayload :=
  xs[0]?

/-- Main calibrated kernel step. -/
def stepKernelCalibrated
    (knobs : KernelKnobs)
    (x : CalibratedInput) : CalibratedOutput :=
  let cand := stabilizePayloadsCalibrated knobs x
  match chooseBestCalibrated cand with
  | none =>
      { chosen := none
      , applied := none
      , score := 0.0
      , coupling := 0.0
      , promoted := false
      , tunneled := false
      , admissible := false
      , budgetNext := budgetCalibrated knobs
      }
  | some best =>
      let p := best.payload
      let sig := sigOfPayload p
      let admissible := cellPatchAdmissible x.cell p.patch
      let promoted := if admissible then
        shouldPromoteCalibrated knobs p x.signal x.visibility x.topo sig
      else false
      let tunneled := if admissible then
        allowTunnelCalibrated knobs p x.signal x.visibility x.topo sig
      else false
      let budgetNext := if admissible then
        budgetCalibratedStep knobs p x.signal x.visibility x.topo sig
      else budgetCalibrated knobs
      { chosen := some p
      , applied := if admissible then some p.patch else none
      , score := best.score
      , coupling := best.coupling
      , promoted := promoted
      , tunneled := tunneled
      , admissible := admissible
      , budgetNext := budgetNext
      }


-- ════════════════════════════════════════════════════════════
-- §6  Tracing and Benchmarking
-- ════════════════════════════════════════════════════════════

/-- Calibrated execution trace. -/
structure CalibratedTrace where
  steps        : Nat
  chosenCount  : Nat
  appliedCount : Nat
  promoteCount : Nat
  tunnelCount  : Nat
  admissibleCt : Nat
  scoreTotal   : Float
  couplingSum  : Float
  deriving Repr, Inhabited

/-- Zero trace. -/
def CalibratedTrace.zero : CalibratedTrace :=
  { steps := 0, chosenCount := 0, appliedCount := 0
  , promoteCount := 0, tunnelCount := 0, admissibleCt := 0
  , scoreTotal := 0.0, couplingSum := 0.0 }

/-- Step the trace. -/
def CalibratedTrace.step
    (t : CalibratedTrace)
    (o : CalibratedOutput) : CalibratedTrace :=
  { steps := t.steps + 1
  , chosenCount := t.chosenCount + (if o.chosen.isSome then 1 else 0)
  , appliedCount := t.appliedCount + (if o.applied.isSome then 1 else 0)
  , promoteCount := t.promoteCount + (if o.promoted then 1 else 0)
  , tunnelCount := t.tunnelCount + (if o.tunneled then 1 else 0)
  , admissibleCt := t.admissibleCt + (if o.admissible then 1 else 0)
  , scoreTotal := t.scoreTotal + o.score
  , couplingSum := t.couplingSum + o.coupling }

/-- Rate metrics. -/
def CalibratedTrace.appliedRate (t : CalibratedTrace) : Float :=
  if t.steps = 0 then 0.0 else Float.ofNat t.appliedCount / Float.ofNat t.steps

def CalibratedTrace.promoteRate (t : CalibratedTrace) : Float :=
  if t.steps = 0 then 0.0 else Float.ofNat t.promoteCount / Float.ofNat t.steps

def CalibratedTrace.tunnelRate (t : CalibratedTrace) : Float :=
  if t.steps = 0 then 0.0 else Float.ofNat t.tunnelCount / Float.ofNat t.steps

def CalibratedTrace.admissibleRate (t : CalibratedTrace) : Float :=
  if t.steps = 0 then 0.0 else Float.ofNat t.admissibleCt / Float.ofNat t.steps

def CalibratedTrace.meanScore (t : CalibratedTrace) : Float :=
  if t.steps = 0 then 0.0 else t.scoreTotal / Float.ofNat t.steps

/-- Benchmark calibrated kernel on input array. -/
def benchmarkCalibrated
    (knobs : KernelKnobs)
    (xs : Array CalibratedInput) : CalibratedTrace :=
  xs.foldl (fun acc x => acc.step (stepKernelCalibrated knobs x)) CalibratedTrace.zero


-- ════════════════════════════════════════════════════════════
-- §7  DomainKernel Integration
-- ════════════════════════════════════════════════════════════

/-- Convert DomainKernel input to calibrated input. -/
def ofDomainInput (x : DomainInput VarDimManifold) : CalibratedInput :=
  let ki := toKernelInput varDimAdapter x
  { cell := ki.cell
  , payloads := ki.payloads
  , signal := ki.signal
  , visibility := ki.visibility
  , topo := ki.topo
  , self := Float.ofInt ki.self.raw / 65536.0
  , nbrMean := Float.ofInt ki.nbrMean.raw / 65536.0
  , prev := Float.ofInt ki.prev.raw / 65536.0
  }

/-- Calibrate from domain input directly. -/
def calibrateDomain
    (c : CorpusStats)
    (r : RuntimeStats)
    (x : DomainInput VarDimManifold) : CalibratedOutput :=
  stepKernelCalibrated (calibrate c r) (ofDomainInput x)


-- ════════════════════════════════════════════════════════════
-- §8  A/B Comparison Framework
-- ════════════════════════════════════════════════════════════

/-- Base vs calibrated comparison structure. -/
structure BaseVsCalibrated where
  base       : KernelOutput
  calibrated : CalibratedOutput
  knobs      : KernelKnobs
  deriving Repr

/-- Compare base DomainKernel vs calibrated on same input. -/
def compareBaseVsCalibrated
    (c : CorpusStats)
    (r : RuntimeStats)
    (x : DomainInput VarDimManifold) : BaseVsCalibrated :=
  let knobs := calibrate c r
  { base := runDomainStep varDimAdapter x
  , calibrated := stepKernelCalibrated knobs (ofDomainInput x)
  , knobs := knobs
  }

/-- Delta metrics. -/
def appliedDelta (x : BaseVsCalibrated) : Float :=
  (if x.calibrated.applied.isSome then 1.0 else 0.0) -
  (if x.base.applied.isSome then 1.0 else 0.0)

def promoteDelta (x : BaseVsCalibrated) : Bool :=
  x.calibrated.promoted && !x.base.promoted

def tunnelDelta (x : BaseVsCalibrated) : Bool :=
  x.calibrated.tunneled && !x.base.tunneled

/-- Theorem: Calibrated kernel output structure.
    When the calibrated kernel marks a choice as inadmissible, it correctly
    sets applied := none, promoted := false, and tunneled := false.
    This replaces the too-strong "preserves rejection" claim, since calibrated
    scoring may select a different payload than the base kernel. -/
theorem calibratedRejectionStructure
    (c : CorpusStats)
    (r : RuntimeStats)
    (x : DomainInput VarDimManifold) :
    (compareBaseVsCalibrated c r x).calibrated.admissible = false →
    (compareBaseVsCalibrated c r x).calibrated.applied = none ∧
    (compareBaseVsCalibrated c r x).calibrated.promoted = false ∧
    (compareBaseVsCalibrated c r x).calibrated.tunneled = false := by
  intro h
  by_cases h_none : chooseBestCalibrated (stabilizePayloadsCalibrated (calibrate c r) (ofDomainInput x)) = none
  · -- none branch: all fields are default false/none
    simp [compareBaseVsCalibrated, stepKernelCalibrated, h_none] at h ⊢
  · -- some branch: admissible check determines applied/promoted/tunneled
    have h_some : ∃ best, chooseBestCalibrated (stabilizePayloadsCalibrated (calibrate c r) (ofDomainInput x)) = some best := by
      cases chooseBestCalibrated (stabilizePayloadsCalibrated (calibrate c r) (ofDomainInput x)) with
      | none => contradiction
      | some best => exists best
    rcases h_some with ⟨best, h_best⟩
    simp [compareBaseVsCalibrated, stepKernelCalibrated, h_best] at h ⊢
    simp_all

/-- #eval witness: calibration example. -/
def exampleCorpus : CorpusStats :=
  { totalSize := 1000000
  , compressRatio := 2.5
  , symmetryScore := 0.7
  , localityBias := 0.6 }

def exampleRuntime : RuntimeStats :=
  { meanLatency := 50.0
  , p99Latency := 100.0
  , throughput := 1500.0
  , memoryPressure := 0.3 }

#eval calibrate exampleCorpus exampleRuntime

end Semantics.CalibratedKernel
