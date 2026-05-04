/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

DomainKernel.lean — Generic Trajectory Kernel with Domain Adapters

Architecture:
  1. Generic Kernel (domain-agnostic)
     - candidate generation
     - scoring via J(n)
     - stabilization
     - pruning (ACI-NMS)
     - propagation (butterfly gossip)
     - promotion

  2. Domain Adapter (domain-specific)
     - state encoding
     - local features
     - coupling features
     - admissibility constraints
     - visibility/importance signal

Per user specification: One reusable machine, not one universal ontology.
Axis 11 = the shared trajectory interface between domains.

Domains:
  • Astrophysics: mass field, mirror asymmetry, neighborhood coupling
  • Neural: spike/state encoding, local activation, topological burst
  • Maritime: vessel state, tide/noise signal, path visibility
-/

import Semantics.SSMS_nD
import Semantics.UniversalCoupling

namespace Semantics.DomainKernel

open Semantics.SSMS
open Semantics.SSMS_nD
open Semantics.UniversalCoupling

-- ════════════════════════════════════════════════════════════
-- §0  Cell and Patch Types
-- ════════════════════════════════════════════════════════════

/-- Grid cell for kernel routing. -/
structure Cell where
  t      : UInt8
  sigma  : Bool
  h      : Q1616
  s      : Q1616
  p_next : UInt8
  deriving Repr, Inhabited

/-- Patch applied to a cell. -/
structure CellPatch where
  deltaH : Q1616
  deltaS : Q1616
  deriving Repr, Inhabited

/-- Admissibility check for a patch on a cell. -/
def cellPatchAdmissible (_cell : Cell) (_patch : CellPatch) : Bool :=
  true  -- TODO(lean-port): Define actual admissibility predicate

/-- Payload carrying both a gossip packet and a patch. -/
structure KernelPayload where
  packet : GossipPacket
  patch  : CellPatch
  deriving Repr, Inhabited

-- ════════════════════════════════════════════════════════════
-- §1  Generic Kernel Interface (Domain-Agnostic)
-- ════════════════════════════════════════════════════════════

/-- Generic kernel input — all domains reduce to this. -/
structure KernelInput where
  cell       : Cell
  payloads   : Array KernelPayload
  signal     : CoarseSignal
  visibility : Visibility
  topo       : TopoState
  self       : Q1616
  nbrMean    : Q1616
  prev       : Q1616
  budget     : Nat
  lambda     : Q1616  -- phantom coupling parameter
  deriving Repr, Inhabited

/-- Generic kernel output — trajectory decision. -/
structure KernelOutput where
  chosen     : Option KernelPayload
  applied    : Option CellPatch
  score      : Q1616
  coupling   : Q1616
  promoted   : Bool
  tunneled   : Bool
  admissible : Bool
  budgetNext : Nat
  deriving Repr, Inhabited

/-- The generic kernel step — domain-agnostic pathing engine.
    Implements: evaluate → propagate → prune → promote -/
def stepKernel (x : KernelInput) : KernelOutput :=
  -- §1.1 Generate candidates from payloads
  let candidates := x.payloads.filter (fun p =>
    cellPatchAdmissible x.cell p.patch)

  -- §1.2 Score candidates via PhantomTideQ
  let scored := candidates.map (fun p =>
    let j := couplingPhantom x.lambda p.packet.energy x.signal.payload.energy x.signal.coherence
    let score := finalScorePhantom p.packet.energy j
    (p, score, j))

  -- §1.3 Select best (argmax via foldl)
  let best := scored.foldl (fun best (p, s, j) =>
    if s.raw > best.2.1.raw then (some p, s, j) else best
  ) (none, Q1616.zero, Q1616.zero)

  -- §1.4 Route decision
  let chosen := best.1
  let score := best.2.1
  let coupling := best.2.2

  let admissible := chosen.isSome &&
    cellPatchAdmissible x.cell (chosen.get!.patch)

  let promoted := admissible &&
    shouldPromotePhantom x.lambda Q1616.one score x.signal.payload.energy Q1616.zero x.prev

  let tunneled := admissible &&
    allowTunnelPhantom x.lambda score x.signal.payload.energy x.visibility.trust x.signal.coherence

  let budgetNext :=
    if admissible then dynamicGossipBudget coupling (x.budget + x.topo.epoch)
    else x.budget

  { chosen := chosen
  , applied := if admissible then chosen.map (·.patch) else none
  , score := score
  , coupling := coupling
  , promoted := promoted
  , tunneled := tunneled
  , admissible := admissible
  , budgetNext := budgetNext
  }


-- ════════════════════════════════════════════════════════════
-- §2  Domain Adapter Interface
-- ════════════════════════════════════════════════════════════

/-- Domain adapter: each domain implements this to feed the kernel.
    σ = domain-specific state type -/
structure DomainAdapter (σ : Type) where
  toCell        : σ → Cell
  toSignal      : σ → CoarseSignal
  toVisibility  : σ → Visibility
  toTopo        : σ → TopoState
  selfValue     : σ → Q1616
  nbrMeanValue  : σ → Q1616
  prevValue     : σ → Q1616
  payloads      : σ → Array KernelPayload
  admissible    : σ → KernelPayload → Bool

/-- Domain input: state + budget. -/
structure DomainInput (σ : Type) where
  state   : σ
  budget  : Nat
  lambda  : Q1616
  deriving Repr, Inhabited

/-- Convert domain input to generic kernel input. -/
def toKernelInput {σ : Type} (a : DomainAdapter σ) (x : DomainInput σ) : KernelInput :=
  { cell := a.toCell x.state
  , payloads := a.payloads x.state
  , signal := a.toSignal x.state
  , visibility := a.toVisibility x.state
  , topo := a.toTopo x.state
  , self := a.selfValue x.state
  , nbrMean := a.nbrMeanValue x.state
  , prev := a.prevValue x.state
  , budget := x.budget
  , lambda := x.lambda
  }

/-- Run domain step: adapter feeds generic kernel. -/
def runDomainStep {σ : Type} (a : DomainAdapter σ) (x : DomainInput σ) : KernelOutput :=
  stepKernel (toKernelInput a x)


-- ════════════════════════════════════════════════════════════
-- §3  Astrophysics Adapter
--     Feeds: mass field, mirror asymmetry, neighborhood coupling
-- ════════════════════════════════════════════════════════════

/-- Astrophysical state: galaxy cluster particle. -/
structure AstroState where
  position    : Array Q1616  -- 3D spatial coordinates
  velocity    : Array Q1616  -- 3D velocity
  mass        : Q1616         -- particle mass
  asymmetry   : Q1616         -- mirror asymmetry χ
  neighbors   : Nat           -- neighbor count for coupling
  pressure    : Q1616         -- local pressure field
  curvature   : Q1616         -- Ricci scalar approximation
  epoch       : UInt8         -- simulation step
  deriving Repr, Inhabited

def astroAdapter : DomainAdapter AstroState where
  toCell s :=
    { t := s.epoch
    , sigma := true
    , h := ⟨s.mass.raw / 65536⟩  -- mass as normalized h
    , s := s.position.getD 0 Q1616.zero  -- x-coordinate as scalar
    , p_next := 0
    }
  toSignal s :=
    { payload :=
        { energy := s.mass
        , sigma := true
        , sVal := s.asymmetry
        , version := 0
        , load := s.pressure
        , deltaH := s.curvature
        }
    , velocity := Q1616.zero
    , coherence := s.pressure
    }
  toVisibility s :=
    { trust := ⟨255⟩  -- max trust
    , depth := ⟨10⟩   -- deep field
    , nbrCount := s.neighbors
    }
  toTopo s :=
    { index := ⟨s.epoch.toNat % 16, by omega⟩
    , partition := 0
    , epoch := s.epoch.toNat
    }
  selfValue s := s.mass
  nbrMeanValue s := ⟨s.neighbors * 4096⟩  -- normalized neighbor coupling
  prevValue s := s.velocity.getD 0 Q1616.zero
  payloads s := #[]  -- empty for N-body (gravity only)
  admissible _ _ := true  -- all mass admissible


-- ════════════════════════════════════════════════════════════
-- §4  Neural Adapter
--     Feeds: spike/state encoding, local activation, topological burst
-- ════════════════════════════════════════════════════════════

/-- Neural state: population of neurons. -/
structure NeuralState where
  membranePot : Array Q1616  -- V_m for each neuron
  spikeHist   : Array Q1616  -- recent spike counts
  synWeights  : Array Q1616  -- synaptic coupling matrix (flattened)
  burstDetect : Q1616        -- topological burst metric
  learningVis : Q1616        -- learning rate visibility
  topoIndex   : UInt16       -- population index
  deriving Repr, Inhabited

def neuralAdapter : DomainAdapter NeuralState where
  toCell s :=
    let active := decide ((s.membranePot.getD 0 Q1616.zero).raw > 32768)
    { t := 0
    , sigma := active  -- active if V_m > 0.5
    , h := ⟨s.spikeHist.size * 256⟩  -- activity as h
    , s := s.membranePot.getD 0 Q1616.zero
    , p_next := 0
    }
  toSignal s :=
    let active := decide ((s.membranePot.getD 0 Q1616.zero).raw > 32768)
    { payload :=
        { energy := s.membranePot.foldl (fun acc v => Q1616.add acc v) Q1616.zero
        , sigma := active
        , sVal := s.burstDetect
        , version := 0
        , load := Q1616.zero
        , deltaH := s.learningVis
        }
    , velocity := Q1616.zero
    , coherence := s.burstDetect
    }
  toVisibility s :=
    { trust := ⟨200⟩  -- medium-high trust for learned patterns
    , depth := ⟨5⟩    -- intermediate depth
    , nbrCount := 8
    }
  toTopo s :=
    { index := ⟨s.topoIndex.toNat % 16, by omega⟩
    , partition := 0
    , epoch := 0
    }
  selfValue s := s.membranePot.getD 0 Q1616.zero
  nbrMeanValue s := s.spikeHist.foldl (fun acc v => Q1616.add acc v) Q1616.zero
  prevValue s := s.membranePot.getD 1 Q1616.zero
  payloads s := #[]  -- spike packets generated externally
  admissible _ _ := true


-- ════════════════════════════════════════════════════════════
-- §5  Maritime Adapter
--     Feeds: vessel state, tide/noise signal, path visibility
-- ════════════════════════════════════════════════════════════

/-- Maritime state: vessel tracking. -/
structure MaritimeState where
  position    : Array Q1616  -- (x, y) surface coordinates
  velocity    : Array Q1616  -- (vx, vy)
  massEst     : Q1616         -- estimated vessel mass
  tideSignal  : Q1616         -- tide pressure gradient
  aisSig      : Array Q1616   -- AIS signature vector
  pathVis     : Q1616         -- path visibility score
  phantomDet  : Bool          -- phantom signature detected
  epoch       : UInt8         -- tracking step
  deriving Repr, Inhabited

def maritimeAdapter : DomainAdapter MaritimeState where
  toCell s :=
    { t := s.epoch
    , sigma := s.phantomDet
    , h := ⟨s.massEst.raw / 65536⟩
    , s := s.position.getD 0 Q1616.zero
    , p_next := 0
    }
  toSignal s :=
    { payload :=
        { energy := s.massEst
        , sigma := s.phantomDet
        , sVal := s.pathVis
        , version := 0
        , load := s.tideSignal
        , deltaH := s.pathVis
        }
    , velocity := Q1616.zero
    , coherence := s.tideSignal
    }
  toVisibility s :=
    { trust := ⟨150⟩  -- moderate trust (noisy environment)
    , depth := ⟨3⟩    -- shallow (surface)
    , nbrCount := 4
    }
  toTopo s :=
    { index := ⟨s.epoch.toNat % 16, by omega⟩
    , partition := 0
    , epoch := s.epoch.toNat
    }
  selfValue s := s.massEst
  nbrMeanValue s := s.velocity.foldl (fun acc v => Q1616.add acc v) Q1616.zero
  prevValue s := s.position.getD 1 Q1616.zero
  payloads s := #[]
  admissible _ _ := true


-- ════════════════════════════════════════════════════════════
-- §5.5  VarDimManifold Adapter
-- ════════════════════════════════════════════════════════════

def varDimAdapter : DomainAdapter VarDimManifold where
  toCell s :=
    { t := 0
    , sigma := s.sigma
    , h := s.energy
    , s := s.center.getD 0 Q1616.zero
    , p_next := 0
    }
  toSignal s :=
    { payload :=
        { energy := s.energy
        , sigma := s.sigma
        , sVal := s.center.getD 0 Q1616.zero
        , version := 0
        , load := Q1616.zero
        , deltaH := Q1616.zero
        }
    , velocity := Q1616.zero
    , coherence := Q1616.one
    }
  toVisibility _ :=
    { trust := ⟨200⟩
    , depth := ⟨5⟩
    , nbrCount := 8
    }
  toTopo s :=
    { index := ⟨0, by omega⟩
    , partition := 0
    , epoch := 0
    }
  selfValue s := s.energy
  nbrMeanValue s := s.center.getD 0 Q1616.zero
  prevValue s := s.energy
  payloads _ := #[]
  admissible _ _ := true


-- ════════════════════════════════════════════════════════════
-- §6  Cross-Domain Benchmarking Interface
-- ════════════════════════════════════════════════════════════

/-- Benchmark metrics for kernel evaluation. -/
structure BenchmarkMetrics where
  admissibleRate : Float  -- patches passing admissibility
  appliedRate    : Float  -- patches actually applied
  promotionRate  : Float  -- promotions / total
  tunnelRate     : Float  -- tunnel events / total
  sigmaTotal     : Float  -- total Σ coupling
  sigmaMean      : Float  -- mean coupling
  activeRoutes   : Nat    -- number of active trajectories
  deriving Repr, Inhabited

/-- Run benchmark on any domain. -/
def runBenchmark {σ : Type} (a : DomainAdapter σ) (states : Array σ)
    (budget : Nat) (lambda : Q1616) : Array (KernelOutput × BenchmarkMetrics) :=
  states.map (fun s =>
    let input := { state := s, budget := budget, lambda := lambda : DomainInput σ }
    let output := runDomainStep a input
    let metrics :=
      { admissibleRate := if output.admissible then 1.0 else 0.0
      , appliedRate := if output.applied.isSome then 1.0 else 0.0
      , promotionRate := if output.promoted then 1.0 else 0.0
      , tunnelRate := if output.tunneled then 1.0 else 0.0
      , sigmaTotal := Float.ofInt output.coupling.raw / 65536.0
      , sigmaMean := Float.ofInt output.score.raw / 65536.0
      , activeRoutes := output.budgetNext
      }
    (output, metrics))


-- ════════════════════════════════════════════════════════════
-- §7  Self-Typing: Kernel Recognition of Shared Structure
-- ════════════════════════════════════════════════════════════

/-- Self-typing predicate: state reduces to same kernel input structure. -/
def isKernelReducible (σ : Type) (a : DomainAdapter σ) (s : σ) : Prop :=
  -- The adapter successfully produces all required kernel inputs
  ∃ (cell : Cell) (sig : CoarseSignal) (vis : Visibility)
    (topo : TopoState) (self nbr prev : Q1616) (ps : Array KernelPayload),
    a.toCell s = cell ∧
    a.toSignal s = sig ∧
    a.toVisibility s = vis ∧
    a.toTopo s = topo ∧
    a.selfValue s = self ∧
    a.nbrMeanValue s = nbr ∧
    a.prevValue s = prev ∧
    a.payloads s = ps

/-- Theorem: All three domain adapters are kernel-reducible.
    This is the grounded "self-typing" — not universal ontology,
    just observation that domains reduce to same interface. -/
theorem astroIsKernelReducible (s : AstroState) : isKernelReducible AstroState astroAdapter s := by
  exists astroAdapter.toCell s
  exists astroAdapter.toSignal s
  exists astroAdapter.toVisibility s
  exists astroAdapter.toTopo s
  exists astroAdapter.selfValue s
  exists astroAdapter.nbrMeanValue s
  exists astroAdapter.prevValue s
  exists astroAdapter.payloads s
  all_goals simp [isKernelReducible]

theorem neuralIsKernelReducible (s : NeuralState) : isKernelReducible NeuralState neuralAdapter s := by
  exists neuralAdapter.toCell s
  exists neuralAdapter.toSignal s
  exists neuralAdapter.toVisibility s
  exists neuralAdapter.toTopo s
  exists neuralAdapter.selfValue s
  exists neuralAdapter.nbrMeanValue s
  exists neuralAdapter.prevValue s
  exists neuralAdapter.payloads s
  all_goals simp [isKernelReducible]

theorem maritimeIsKernelReducible (s : MaritimeState) : isKernelReducible MaritimeState maritimeAdapter s := by
  exists maritimeAdapter.toCell s
  exists maritimeAdapter.toSignal s
  exists maritimeAdapter.toVisibility s
  exists maritimeAdapter.toTopo s
  exists maritimeAdapter.selfValue s
  exists maritimeAdapter.nbrMeanValue s
  exists maritimeAdapter.prevValue s
  exists maritimeAdapter.payloads s
  all_goals simp [isKernelReducible]

end Semantics.DomainKernel
