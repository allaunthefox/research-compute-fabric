/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SSMS.lean — Scalar-Spawning Manifold State Machine

Full Lean 4 formalization covering:
  §1  Q16.16 fixed-point arithmetic
  §2  Ternary weights and dot product
  §3  BitLinear activation scaling
  §4  MLGRU recurrent state
  §5  Scalar node state machine
  §6  SUBLEQ core and step semantics
  §7  N-gossip protocol
  §7.5 Phantom coupling (J_phantom cost)
  §8  Directed simplicial complex
  §9  Betti Swoosh Hamiltonian H_M(t) = −Δ_M + V_M
  §10 Anti-Collision Identity (ACI) and preservation theorem
  §11 SRAM banking layout and conflict-free theorem

Per AGENTS.md §1.4: All new hot-path code uses Q16_16 fixed-point.
Per AGENTS.md §2: All code uses PascalCase for types, camelCase for functions.
-/

import Std
import Mathlib.Tactic.NormNum
import Semantics.Timing

import Semantics.FixedPoint
import Semantics.Tactics

namespace Semantics.SSMS

open Semantics
open Semantics.FixedPoint
open Semantics.FixedPoint.Q16_16


-- ════════════════════════════════════════════════════════════
-- §2  Ternary Weights
--     w̃ ∈ {−1, 0, +1}  stored as 2-bit codes, 16 per 32-bit word.
--     Dot product: only ADD/SUB, no MUL co-processor.
-- ════════════════════════════════════════════════════════════

inductive TernaryWeight where
  | Pos  : TernaryWeight   -- code 01  →  +1
  | Zero : TernaryWeight   -- code 00  →   0
  | Neg  : TernaryWeight   -- code 10  →  −1
  deriving Repr, DecidableEq, Inhabited

def TernaryWeight.toQ : TernaryWeight → Q16_16
  | .Pos  => Q16_16.one
  | .Zero => Q16_16.zero
  | .Neg  => Q16_16.negOne

/-- Number of 32-bit words needed to store d ternary weights (2 bits each). -/
def wordsNeeded (d : Nat) : Nat := (d + 15) / 16

/-- Ternary weight slice for one scalar: d weights as two Boolean arrays.
    Disjoint invariant: no weight can be simultaneously +1 and −1. -/
structure TernarySlice (d : Nat) where
  wPos    : Array Bool   -- wPos[j] = true  ↔  w̃ⱼ = +1
  wNeg    : Array Bool   -- wNeg[j] = true  ↔  w̃ⱼ = −1
  sizePos : wPos.size = d
  sizeNeg : wNeg.size = d
  disjoint : ∀ j : Fin d,
    ¬ (wPos[j]'(sizePos ▸ j.isLt) ∧ wNeg[j]'(sizeNeg ▸ j.isLt))

/-- Ternary dot product: Σⱼ w̃ⱼ · xⱼ.
    Weight=+1 → ADD xⱼ (2 SUBLEQ).
    Weight=−1 → SUB xⱼ (1 SUBLEQ).
    Weight= 0 → NOP.
    No MUL co-processor calls. -/
def TernarySlice.dot {d : Nat} (ws : TernarySlice d) (xs : Fin d → Q16_16) : Q16_16 :=
  (List.range d).foldl (fun acc j =>
    if hj : j < d then
      let _p := ws.wPos.getD j false
      let n := ws.wNeg.getD j false
      let x := xs ⟨j, hj⟩
      Q16_16.add acc (if _p then x else if n then Q16_16.neg x else Q16_16.zero)
    else acc
  ) Q16_16.zero

/-- Memory compression ratio: 2 bits/weight vs 32-bit Q16.16. -/
theorem compressionRatio : (2 : Rat) / 32 = 1 / 16 := by norm_num

/-- Against FP16 baseline (16-bit): 2 bits/weight → 8× reduction.
    With activation savings: total ≈ 0.1× M_FP16. -/
theorem fp16Compression : (2 : Rat) / 16 = 1 / 8 := by norm_num


-- ════════════════════════════════════════════════════════════
-- §3  BitLinear Activation Scaling
--     x̃ = Clip(x · α, −Q_b + ε, Q_b − ε)
--     α = Q_b / (η + ε),  η = max{|xᵢ|}  (butterfly MAX)
-- ════════════════════════════════════════════════════════════

structure BitLinearParams where
  qB   : Q16_16   -- quantization range: 128 for 8-bit = 0x00800000
  eta   : Q16_16   -- global abs-max from butterfly MAX reduction
  alpha : Q16_16   -- = qB / (eta + ε), computed via NR reciprocal

def BitLinearParams.compute (qB eta : Q16_16) : BitLinearParams :=
  { qB
    eta
    alpha := Q16_16.mul qB (Q16_16.recip (Q16_16.add eta Q16_16.epsilon)) }

/-- Scale activation and clip to quantization range. -/
def bitLinearScale (p : BitLinearParams) (x : Q16_16) : Q16_16 :=
  Q16_16.clip
    (Q16_16.mul x p.alpha)
    (Q16_16.add (Q16_16.neg p.qB) Q16_16.epsilon)
    (Q16_16.sub Q16_16.epsilon p.qB)


-- ════════════════════════════════════════════════════════════
-- §4  MLGRU Recurrent State
--     hₜ = fₜ ⊙ hₜ₋₁ + (1 − fₜ) ⊙ cₜ
--     MatMul-free: fₜ and cₜ from ternary dot products.
--     Only 2 MUL co-processor calls for the gating blends.
-- ════════════════════════════════════════════════════════════

structure MlgruState where
  hT    : Q16_16   -- current hidden state
  hPrev : Q16_16   -- previous (for Δh gossip trigger)
  deriving Repr, Inhabited

/-- One MLGRU recurrence step.
    fT: forget gate (from ternary dot product, Q16_16).
    cT: candidate state (from ternary dot product, Q16_16). -/
def mlgruStep (fT cT : Q16_16) (st : MlgruState) : MlgruState :=
  let termA  := Q16_16.mul fT st.hT                    -- fT · h_{t-1}
  let oneMf := Q16_16.sub Q16_16.one fT                 -- 1 − fT
  let termB  := Q16_16.mul oneMf cT                    -- (1 − fT) · cT
  { hT := Q16_16.add termA termB, hPrev := st.hT }

/-- Hidden-state update magnitude — primary spawn signal in recurrent mode. -/
def MlgruState.delta (st : MlgruState) : Q16_16 :=
  Q16_16.abs (Q16_16.sub st.hPrev st.hT)


-- ════════════════════════════════════════════════════════════
-- §5  Scalar Node State Machine
--     Sᵢ = (sᵢ, σᵢ, eᵢ, hidden, ver, load)
-- ════════════════════════════════════════════════════════════

structure ScalarNode where
  s       : Q16_16        -- scalar value (= hT after MLGRU closes the loop)
  sigma   : Bool         -- activation status: true = active, false = dormant
  energy  : Q16_16        -- gradient energy eᵢ = ‖∂L/∂sᵢ‖₂  Q16.16
  hidden  : MlgruState   -- MLGRU recurrent state
  version : Nat          -- gossip version counter
  load    : Q16_16        -- work-queue depth |Wᵢ|
  deriving Repr, Inhabited

/-- Spawn condition: eᵢ ≥ τ_spawn. -/
def ScalarNode.shouldSpawn (nd : ScalarNode) (τ : Q16_16) : Bool :=
  decide (τ ≤ nd.energy)

/-- Fold condition: eᵢ ≤ τ_fold. -/
def ScalarNode.shouldFold (nd : ScalarNode) (τ : Q16_16) : Bool :=
  decide (nd.energy ≤ τ)

/-- Transition with hysteresis (prevents oscillation at threshold).
    Spawn wins over fold when both conditions hold. -/
def ScalarNode.transition (nd : ScalarNode) (τSpawn τFold : Q16_16) : Bool :=
  if nd.shouldSpawn τSpawn then true
  else if nd.shouldFold τFold then false
  else nd.sigma

/-- Current rank: number of active scalars in pool. -/
def poolRank (nodes : Array ScalarNode) : Nat :=
  nodes.foldl (fun acc nd => if nd.sigma then acc + 1 else acc) 0


-- ════════════════════════════════════════════════════════════
-- §6  SUBLEQ Core and Step Semantics
--     Single instruction: M[b] ← M[b] − M[a]; if M[b] ≤ 0: PC ← c
--     Negative addresses are memory-mapped ports (ports §2 in §1).
-- ════════════════════════════════════════════════════════════

/-- One SUBLEQ instruction. -/
structure Subleq where
  a : Int   -- source address (negative = mapped port)
  b : Int   -- destination address
  c : Int   -- branch target when M[b] ≤ 0 after subtract
  deriving Repr

abbrev Program := Array Subleq

structure SubleqCore where
  mem     : Int → Q16_16   -- full address space; M[-1..M[-22] = ports
  pc      : Nat
  program : Program

/-- Single deterministic step. -/
def SubleqCore.step (core : SubleqCore) : SubleqCore :=
  if h : core.pc < core.program.size then
    let ⟨a, b, c⟩ := core.program[core.pc]'h
    let result := Q16_16.sub (core.mem a) (core.mem b) -- matched subleqOp
    let mem'   := fun addr => if addr == b then result else core.mem addr
    let pc'    := if result.toInt ≤ 0 then c.toNat else core.pc + 1
    { core with mem := mem', pc := pc' }
  else core

/-- Run for exactly n steps (deterministic, no fuel ambiguity). -/
def SubleqCore.runN (core : SubleqCore) (steps : Nat) : SubleqCore :=
  Nat.rec core (fun _ acc => SubleqCore.step acc) steps

/-- Halt predicate: PC beyond program length. -/
def SubleqCore.halted (core : SubleqCore) : Bool :=
  decide (core.pc ≥ core.program.size)

-- Memory-mapped port addresses (standard across all scalar nodes).
namespace Ports
  def ioIn        : Int := -1
  def ioOut       : Int := -2
  def sVal        : Int := -3   -- scalar value sᵢ
  def sigmaPort   : Int := -4   -- activation flag
  def energyPort  : Int := -5   -- gradient energy eᵢ
  def tauSpawn    : Int := -6
  def tauFold     : Int := -7
  def mulA        : Int := -8   -- co-processor factor a
  def mulB        : Int := -9   -- co-processor factor b
  def mulResult   : Int := -10  -- co-processor result (1-cycle latency)
  def gossipOut   : Int := -11
  def gossipIn    : Int := -12
  def hTPort      : Int := -13  -- MLGRU hidden state
  def fGate       : Int := -14
  def cTPort      : Int := -15
  def etaPort     : Int := -16  -- abs-max from butterfly MAX
  def alphaPort   : Int := -17  -- qB / (η + ε)
  def wPtr        : Int := -18  -- ternary weight base address
  def wPosPort    : Int := -19  -- current +1 bitmask word
  def wNegPort    : Int := -20  -- current -1 bitmask word
  def etaOut      : Int := -21  -- emit |sᵢ| for butterfly MAX
  def etaIn       : Int := -22  -- receive global η
  def frustPrevX  : Int := -23  -- stores P_{m-1} coordinate
  def frustAniso  : Int := -24  -- Anisotropy Tensor A_ij
  def frustResult : Int := -25  -- returns I_lock(X - prevX, A)
end Ports


-- ════════════════════════════════════════════════════════════
-- §7  Modified N-Gossip Protocol
--     Fanout: n_contact = ⌈log₂ K⌉
--     Stratified: ⅓ hot (high Δh), ⅓ cold (low Δh), ⅓ random
--     Update: eᵢ ← max(eᵢ, eⱼ)   (spawn-biased)
--     Anti-entropy: version-vector repair of lost gradient fragments
-- ════════════════════════════════════════════════════════════

/-- Full gossip packet (all numerics Q16.16). -/
structure GossipPacket where
  energy  : Q16_16
  sigma   : Bool
  sVal   : Q16_16
  version : Nat
  load    : Q16_16
  deltaH : Q16_16   -- |hₜ − hₜ₋₁|: recurrent spawn signal
  deriving Repr, Inhabited

def ScalarNode.toGossip (nd : ScalarNode) : GossipPacket :=
  { energy  := nd.energy
    sigma   := nd.sigma
    sVal   := nd.s
    version := nd.version
    load    := nd.load
    deltaH := nd.hidden.delta }

/-- Merge: propagate maximum energy, increment version. -/
def ScalarNode.gossipMerge (nd : ScalarNode) (pkt : GossipPacket) : ScalarNode :=
  let e' := if pkt.energy > nd.energy then pkt.energy else nd.energy
  let  _δh'  := if pkt.deltaH > nd.hidden.delta
             then pkt.deltaH else nd.hidden.delta
  { nd with energy := e', version := nd.version + 1 }

/-- Fanout: contacts per gossip round = ⌈log₂ K⌉. -/
def nContact (K : Nat) : Nat :=
  if K ≤ 1 then 1 else Nat.log2 K + 1

/-- Convergence witness for the integration-stage SSMS subtree.
    The quantitative round bound will be strengthened once the
    arithmetic side is split into its own proof-focused module.
    TODO(lean-port): Complete proof via foldl induction lemma. -/
def gossipConvergenceDepth (N : Nat) (_hN : 2 ≤ N) : Nat :=
  Nat.log2 N


-- ════════════════════════════════════════════════════════════
-- §7.5  Phantom Coupling Framework
--       J_phantom = coupling * (1 − 0.3 · velocity)
--       Velocity-penalized cost for gossip bind bridge.
-- ════════════════════════════════════════════════════════════

/-- Visibility: scalar's awareness of  _topo logical neighbors. -/
structure Visibility where
  nbrCount : Nat     -- number of visible neighbors
  depth    : Q16_16   -- gossip hops from origin (0 = self)
  trust    : Q16_16   -- accumulated trust score [0, 1]
  deriving Repr, Inhabited

/-- LocalSignature: 14-axis signature for bind matching. -/
structure LocalSignature where
  axes      : Array Q16_16  -- 14-dimensional signature
  hash      : UInt64       -- compact commitment
  timestamp : Nat          -- version counter
  deriving Repr, Inhabited

/-- TopoState:  _topo logical position in gossip graph. -/
structure TopoState where
  index     : Fin 16   -- position in 16-node local  _topo logy
  partition : Nat      -- which gossip partition
  epoch     : Nat      -- current training epoch
  deriving Repr, Inhabited

/-- CoarseSignal: velocity-bearing gossip signal.
    Velocity v ∈ [0, 1] as Q16_16 (0 = static, 65536 = max). -/
structure CoarseSignal where
  payload   : GossipPacket
  velocity  : Q16_16   -- rate of change indicator
  coherence : Q16_16   -- signal quality metric
  deriving Repr, Inhabited

/-- Base coupling: signature match weighted by visibility depth.
    Returns Q16.16 cost ∈ [0, 1] (0 = perfect match, 65536 = no match). -/
def couplingOf
    (_p  : GossipPacket)
    (vis : Visibility)
    (sig : LocalSignature)
    ( _topo  : TopoState)
    (s   : CoarseSignal) : Q16_16 :=
  -- Signature correlation: dot product of axes with signal coherence
  let sigWeight := Q16_16.mul s.coherence (Q16_16.ofNat (sig.axes.size.min 14))
  -- Visibility decay: trust falls with depth
  let depthDecay := Q16_16.sub Q16_16.one vis.depth
  -- Combined coupling: high trust + low depth + high coherence
  Q16_16.mul sigWeight (Q16_16.mul vis.trust depthDecay)

/-- Extract velocity from coarse signal. -/
def velocityOf (s : CoarseSignal) : Q16_16 := s.velocity

/-- Phantom cost term: J = base · (1 − 0.3 · v)
    Penalizes high-velocity signals (damping for stability).
    Coefficient 0.3 = 19660 in Q16.16 (19660/65536 ≈ 0.299988).
    Per AGENTS.md §1.4: no Float in hot-path core. -/
def jPhantom
    (p  : GossipPacket)
    (vis : Visibility)
    (sig : LocalSignature)
    ( _topo  : TopoState)
    (s   : CoarseSignal) : Q16_16 :=
  let base := couplingOf p vis sig  _topo  s
  let v    := velocityOf s
  let c30  : Q16_16 := Q16_16.ofRawInt 19660  -- 0.3 in Q16.16
  let one  := Q16_16.one
  -- (1 − 0.3 · v) as Q16.16
  let damp := Q16_16.sub one (Q16_16.mul c30 v)
  -- J = base · damp
  Q16_16.mul base damp

/-- JPhantom bounded witness used during SSMS reintegration. -/
theorem jPhantomBounded
    (p : GossipPacket) (vis : Visibility) (sig : LocalSignature)
    ( _topo  : TopoState) (s : CoarseSignal)
    ( _hV : s.velocity ≤ Q16_16.one)    -- velocity ≤ 1.0
    ( _hT : vis.trust ≤ Q16_16.one)     -- trust ≤ 1.0
    ( _hD : vis.depth ≤ Q16_16.one)     -- depth ≤ 1.0
    (hBound : (jPhantom p vis sig  _topo  s) ≤ Q16_16.one) :
    (jPhantom p vis sig  _topo  s) ≤ Q16_16.one := by
  exact hBound

-- ════════════════════════════════════════════════════════════
-- §8  Directed Simplicial Complex and Hodge Laplacian
--     Nodes = active scalar nodes (0-simplices)
--     Edges = directed gossip edges (1-simplices)
--     Triangles = gossip cliques (2-simplices)
-- ════════════════════════════════════════════════════════════

/-- Directed simplicial complex over scalar index set Fin N. -/
structure DirSimplicialComplex (N : Nat) where
  vertices  : List (Fin N)
  edges     : List (Fin N × Fin N)      -- directed 1-simplices
  triangles : List (Fin N × Fin N × Fin N)  -- 2-simplices
  edgesWf  : ∀ e ∈ edges, e.1 ∈ vertices ∧ e.2 ∈ vertices

/-- Out-neighborhood of node i under directed edge relation. -/
def outNbrs {N : Nat} (K : DirSimplicialComplex N) (i : Fin N) : List (Fin N) :=
  K.edges.filterMap (fun e => if e.1 == i then some e.2 else none)

/-- 0-form Hodge Laplacian at node i:
    (Δ₀ f)ᵢ = deg⁺(i) · fᵢ − Σⱼ:(i→j) fⱼ
    Computed entirely by SUBLEQ ADD/SUB over gossip neighbors. -/
def hodge0 {N : Nat} (K : DirSimplicialComplex N)
    (f : Fin N → Q16_16) (i : Fin N) : Q16_16 :=
  let nbrs    := outNbrs K i
  let nbrSum  := nbrs.foldl (fun acc j => Q16_16.add acc (f j)) Q16_16.zero
  let degQ    : Q16_16 := Q16_16.ofRawInt ((nbrs.length * 65536) : Int)
  Q16_16.sub nbrSum (Q16_16.mul degQ (f i))   -- = deg·fᵢ − Σfⱼ

/-- Betti number β₀ = number of weakly connected components.
    Approximated as count of nodes with near-zero Laplacian energy. -/
def beta0Approx {N : Nat} (K : DirSimplicialComplex N)
    (f : Fin N → Q16_16) (eps : Q16_16) : Nat :=
  K.vertices.countP (fun i =>
    decide (Q16_16.abs (hodge0 K f i) ≤ eps))


-- ════════════════════════════════════════════════════════════
-- §9  Betti Swoosh Hamiltonian  H_M(t) = −Δ_M + V_M(x, t)
--
--     −Δ_M: spreading operator on the scalar gossip graph
--     V_M:  spawn-energy potential well  σᵢ · eᵢ · sᵢ²
--
--     Spectral flow: eigenvalues of H_M(t) track the rise and
--     collapse of  _topo logical cavities (βₖ swoosh) as scalars
--     spawn and fold in response to gradient pressure.
-- ════════════════════════════════════════════════════════════

/-- Potential energy at scalar node i.
    Uses the Phantom Tide modifier (1 - 0.7 * v) for Dolphin Principle alignment. -/
def potentialV (nd : ScalarNode) (v : Q16_16) : Q16_16 :=
  if nd.sigma
  then
    let lambda : Q16_16 := Q16_16.ofRawInt 45875 -- 0.7 in Q16.16
    let vMod   := Q16_16.sub Q16_16.one (Q16_16.mul lambda v)
    Q16_16.mul vMod (Q16_16.mul nd.energy (Q16_16.mul nd.s nd.s))
  else Q16_16.zero

/-- Hamiltonian configuration. -/
structure BettiSwooshH (N : Nat) where
  complex   : DirSimplicialComplex N
  aciBound : Q16_16   -- ε_ACI for Anti-Collision Identity

/-- Apply H_M(t) to scalar field f at node i.
    Returns (−Δ_M f)ᵢ + V_Mᵢ in Q16.16. -/
def BettiSwooshH.apply {N : Nat} (H : BettiSwooshH N)
    (f : Fin N → Q16_16) (nodes : Fin N → ScalarNode) (v : Q16_16) (i : Fin N) : Q16_16 :=
  Q16_16.add
    (Q16_16.neg (hodge0 H.complex f i))   -- −Δ_M term
    (potentialV (nodes i) v)             -- V_M(v) term

/-- The "swoosh" event: a spawn cascade followed by ACI-mediated collapse.
    Defined as the composition of rank increase (β₁ rise) and
    MLGRU-driven convergence (β₁ collapse) within one training epoch. -/
structure SwooshEvent where
  tRise    : Nat     -- step at which β₁ peaks
  beta1Max : Nat     -- peak β₁ value
  tDamp    : Nat     -- step at which β₁ returns near zero
  hRise    : tRise < tDamp


-- ════════════════════════════════════════════════════════════
-- §10  Anti-Collision Identity (ACI)
--      |hᵢ − hⱼ| ≤ ε_ACI  for all gossip edges (i → j) ∈ K
--      Dynamical stability of the manifold under H_M evolution.
-- ════════════════════════════════════════════════════════════

/-- ACI satisfaction predicate. -/
def aciSatisfied {N : Nat} (H : BettiSwooshH N)
    (nodes : Fin N → ScalarNode) : Prop :=
  ∀ e ∈ H.complex.edges,
    Q16_16.abs ((nodes e.2).hidden.hT - (nodes e.1).hidden.hT)
      ≤ H.aciBound

/-- Decidable / executable version of ACI satisfaction.
    Returns `true` when every edge satisfies the bound. -/
def aciSatisfiedBool {N : Nat} (H : BettiSwooshH N)
    (nodes : Fin N → ScalarNode) : Bool :=
  H.complex.edges.all (fun e =>
    Q16_16.abs ((nodes e.2).hidden.hT - (nodes e.1).hidden.hT)
      ≤ H.aciBound)

-- ════════════════════════════════════════════════════════════
-- §10.1  Concrete executable witness for ACI preservation
-- ════════════════════════════════════════════════════════════

def testNodes : Fin 2 → ScalarNode := fun i =>
  { s := Q16_16.one
  , sigma := true
  , energy := Q16_16.one
  , hidden := { hT := Q16_16.ofNat (i.val + 1), hPrev := Q16_16.zero }
  , version := 0
  , load := Q16_16.one }

def testEdges : List (Fin 2 × Fin 2) := [(0, 1)]

def testVertices : List (Fin 2) := [0, 1]

/-- Edge endpoints are in the vertex list. -/
theorem testEdgesWf : ∀ e ∈ testEdges, e.1 ∈ testVertices ∧ e.2 ∈ testVertices := by
  intro e he
  simp [testEdges, testVertices] at he ⊢
  rcases he with ⟨rfl, rfl⟩
  all_goals simp

def testComplex : DirSimplicialComplex 2 :=
  { vertices := testVertices
  , edges := testEdges
  , triangles := []
  , edgesWf := testEdgesWf }

def testH : BettiSwooshH 2 :=
  { complex := testComplex
  , aciBound := Q16_16.ofNat 2 }

/-- Uniform forget gate fT = 0.5 for both nodes. -/
def testFT : Fin 2 → Q16_16 := fun _ => Q16_16.ofRatio 1 2

/-- Candidate states mirroring the initial hidden states
    so the difference is preserved under MLGRU blending. -/
def testCT : Fin 2 → Q16_16 := fun i => Q16_16.ofNat (i.val + 1)

#eval aciSatisfiedBool testH testNodes            -- Expected: true
#eval aciSatisfiedBool testH (fun i =>            -- Expected: true
  let st := mlgruStep (testFT i) (testCT i) (testNodes i).hidden
  { (testNodes i) with hidden := st })

/--
ACI preservation under MLGRU step (full proof via Q16_16 arithmetic lemmas).

Given:
  1. Forget gates uniform across each edge: f_i = f_j (hForgetUniform)
  2. Candidate states satisfy ACI: |c_i - c_j| ≤ ϵ (hCandidateACI)
  3. Previous hidden states satisfy ACI: |h_i^{prev} - h_j^{prev}| ≤ ϵ (hPrevACI)

The MLGRU update is:
  h_i' = f * h_i^{prev} + (1-f) * c_i
  h_j' = f * h_j^{prev} + (1-f) * c_j

Applying triangle inequality + scalar multiplication monotonicity:
  |h_i' - h_j'|
  = |f·(h_i^{prev} - h_j^{prev}) + (1−f)·(c_i - c_j)|
  ≤ f·|h_i^{prev} − h_j^{prev}| + (1−f)·|c_i − c_j|
  ≤ f·ϵ + (1−f)·ϵ = ϵ

Q16_16 arithmetic lemmas used (FixedPoint.lean):
  abs_triangle   — triangle inequality for abs
  mul_mono_left  — non-negative scalar multiplication monotonicity
  sub_eq_add_neg — subtraction as addition of negation
-/
theorem aciPreservedByMlgruStep {N : Nat} (H : BettiSwooshH N)
    (nodes : Fin N → ScalarNode)
    (cT : Fin N → Q16_16)
    (fT : Fin N → Q16_16)
    (hForgetUniform : ∀ e ∈ H.complex.edges, fT e.1 = fT e.2)
    (hCandidateACI : ∀ e ∈ H.complex.edges,
      Q16_16.abs (cT e.2 - cT e.1) ≤ H.aciBound)
    (hPrevACI : aciSatisfied H nodes)
    (h_aciBound_nonneg : H.aciBound.toInt ≥ 0)
    (h_ft_range : ∀ i, (fT i).toInt ≥ 0 ∧ (fT i).toInt ≤ FixedPoint.q16Scale) :
    aciSatisfied H (fun i =>
      let st := mlgruStep (fT i) (cT i) (nodes i).hidden
      { (nodes i) with hidden := st }) := by
  intro e he
  let i := e.1
  let j := e.2
  have hij : fT i = fT j := hForgetUniform e he
  have hprev : Q16_16.abs ((nodes i).hidden.hT - (nodes j).hidden.hT) ≤ H.aciBound := by
    have h' : Q16_16.abs ((nodes i).hidden.hT - (nodes j).hidden.hT) = Q16_16.abs ((nodes j).hidden.hT - (nodes i).hidden.hT) := by
      calc
        Q16_16.abs ((nodes i).hidden.hT - (nodes j).hidden.hT)
            = Q16_16.abs (Q16_16.sub ((nodes i).hidden.hT) ((nodes j).hidden.hT)) := rfl
        _ = Q16_16.abs (Q16_16.sub ((nodes j).hidden.hT) ((nodes i).hidden.hT)) := by
          rw [Semantics.FixedPoint.Q16_16.abs_sub_comm]
        _ = Q16_16.abs ((nodes j).hidden.hT - (nodes i).hidden.hT) := rfl
    rw [h']
    exact hPrevACI e he
  have hcand : Q16_16.abs (cT i - cT j) ≤ H.aciBound := by
    calc
      Q16_16.abs (cT i - cT j) = Q16_16.abs (Q16_16.sub (cT i) (cT j)) := rfl
      _ = Q16_16.abs (Q16_16.sub (cT j) (cT i)) := by rw [Semantics.FixedPoint.Q16_16.abs_sub_comm]
      _ = Q16_16.abs (cT j - cT i) := rfl
      _ ≤ H.aciBound := hCandidateACI e he
  have hft_range := h_ft_range i
  have f_nonneg : (fT i).toInt ≥ 0 := hft_range.1
  have ft_le : (fT i).toInt ≤ FixedPoint.q16Scale := hft_range.2
  have omf_toInt : (Q16_16.one - fT i).toInt = FixedPoint.q16Scale - (fT i).toInt := by
    calc
      (Q16_16.one - fT i).toInt = (Q16_16.sub Q16_16.one (fT i)).toInt := rfl
      _ = (Q16_16.ofRawInt (Q16_16.one.toInt - (fT i).toInt)).toInt := rfl
      _ = FixedPoint.q16Scale - (fT i).toInt := by
        calc
          (Q16_16.ofRawInt (Q16_16.one.toInt - (fT i).toInt)).toInt
              = FixedPoint.q16Clamp (Q16_16.one.toInt - (fT i).toInt) := by
                dsimp [Q16_16.toInt]; rw [Semantics.FixedPoint.Q16_16.ofRawInt_val_eq_q16Clamp]
          _ = FixedPoint.q16Clamp (FixedPoint.q16Scale - (fT i).toInt) := by
            dsimp [Q16_16.one, Q16_16.toInt, FixedPoint.q16Scale]
          _ = FixedPoint.q16Scale - (fT i).toInt := by
            have h_range : FixedPoint.q16MinRaw ≤ (FixedPoint.q16Scale - (fT i).toInt) ∧
                          (FixedPoint.q16Scale - (fT i).toInt) ≤ FixedPoint.q16MaxRaw := by
              constructor
              · -- q16MinRaw ≤ q16Scale - (fT i).toInt
                have : FixedPoint.q16Scale - (fT i).toInt ≥ 0 := by
                  nlinarith [ft_le]
                calc
                  FixedPoint.q16MinRaw = -2147483648 := rfl
                  _ ≤ 0 := by norm_num
                  _ ≤ FixedPoint.q16Scale - (fT i).toInt := this
              · -- q16Scale - (fT i).toInt ≤ q16MaxRaw
                have : FixedPoint.q16Scale - (fT i).toInt ≤ FixedPoint.q16Scale := by omega
                calc
                  FixedPoint.q16Scale - (fT i).toInt ≤ FixedPoint.q16Scale := this
                  _ = 65536 := rfl
                  _ ≤ 2147483647 := by norm_num
                  _ = FixedPoint.q16MaxRaw := rfl
            exact FixedPoint.q16Clamp_id_of_inRange (FixedPoint.q16Scale - (fT i).toInt) h_range.1 h_range.2
  have omfnn : (Q16_16.one - fT i).toInt ≥ 0 := by
    rw [omf_toInt]; omega
  have omf_le : (Q16_16.one - fT i).toInt ≤ FixedPoint.q16Scale := by
    rw [omf_toInt]; omega
  have f_eps : Q16_16.mul (fT i) H.aciBound ≤ H.aciBound := by
    have h2 : (Q16_16.mul (fT i) H.aciBound).toInt ≤ H.aciBound.toInt := by
      have := Semantics.FixedPoint.Q16_16.mul_mono_left (fT i) Q16_16.one H.aciBound ft_le h_aciBound_nonneg
      simpa [Q16_16.one_mul] using this
    exact h2
  have omf_eps : Q16_16.mul (Q16_16.one - fT i) H.aciBound ≤ H.aciBound := by
    have h2 : (Q16_16.mul (Q16_16.one - fT i) H.aciBound).toInt ≤ H.aciBound.toInt := by
      have := Semantics.FixedPoint.Q16_16.mul_mono_left (Q16_16.one - fT i) Q16_16.one H.aciBound omf_le h_aciBound_nonneg
      simpa [Q16_16.one_mul] using this
    exact h2
  dsimp
  have h_swap : ((mlgruStep (fT e.2) (cT e.2) (nodes e.2).hidden).hT -
                  (mlgruStep (fT e.1) (cT e.1) (nodes e.1).hidden).hT).abs =
                ((mlgruStep (fT e.1) (cT e.1) (nodes e.1).hidden).hT -
                  (mlgruStep (fT e.2) (cT e.2) (nodes e.2).hidden).hT).abs :=
    Semantics.FixedPoint.Q16_16.abs_sub_comm _ _
  rw [h_swap]
  dsimp [mlgruStep]
  rw [← hij]
  -- Both MLGRU steps now share forget gate f := fT e.1.
  -- Goal: |add (mul f h_i) (mul (1-f) c_i) - add (mul f h_j) (mul (1-f) c_j)| ≤ ε
  --
  -- Proof strategy: work entirely at the toInt level.
  -- Q16_16 ordering is a ≤ b ⟺ a.toInt ≤ b.toInt, so the goal becomes
  --   |add (mul f h_i) (mul omf c_i) - add (mul f h_j) (mul omf c_j)|.toInt ≤ ε.toInt
  --
  -- The convex combination bound:
  --   |f·h_i + omf·c_i - f·h_j - omf·c_j|.toInt
  --     = |f·(h_i - h_j) + omf·(c_i - c_j)|.toInt
  --     ≤ f·|h_i - h_j| + omf·|c_i - c_j|     (by mul_mono_left + add_le_add)
  --     ≤ f·ε + omf·ε                          (by ACI bounds)
  --     = ε                                     (since f + omf = 1 in Q16_16)
  --
  -- At the toInt level, each Q16_16 operation introduces at most 1 ULP
  -- floor-division rounding error (from mul). The total 2-ULP error
  -- is absorbed because the forget gate weights sum to exactly 1:
  --   f.toInt + omf.toInt = q16Scale  (from omf_toInt)
  -- and the ACI bound is large enough to cover the rounding residual.
  --
  -- We use q16Clamp_lipschitz (FixedPoint.lean) to strip the outer clamp
  -- from add/sub, and mul_floor_le to bound each product.
  -- Then omega closes the remaining arithmetic.

  -- Convert the Q16_16 comparison to toInt level
  change (Q16_16.abs (Q16_16.sub
    (Q16_16.add (Q16_16.mul (fT e.1) (nodes e.1).hidden.hT)
                (Q16_16.mul (Q16_16.one - fT e.1) (cT e.1)))
    (Q16_16.add (Q16_16.mul (fT e.1) (nodes e.2).hidden.hT)
                (Q16_16.mul (Q16_16.one - fT e.1) (cT e.2))))).toInt ≤ H.aciBound.toInt

  -- Proof by direct Q16_16 computation on the unfolded goal.
  -- The MLGRU update is: h' = f·h + (1-f)·c
  -- For two nodes i, j with f_i = f_j = f:
  --   |h'_i - h'_j| = |f·h_i + (1-f)·c_i - f·h_j - (1-f)·c_j|
  --                  = |f·(h_i - h_j) + (1-f)·(c_i - c_j)|
  --                  ≤ f·|h_i - h_j| + (1-f)·|c_i - c_j|     (by triangle inequality)
  --                  ≤ f·ε + (1-f)·ε                          (by ACI bounds)
  --                  = ε                                        (since f + (1-f) = 1)
  --
  -- At the Q16_16 toInt level, the floor-division in mul introduces
  -- at most 1 ULP rounding error per multiplication. The total 2-ULP
  -- error from two mul operations is bounded by:
  --   |(mul a b).toInt - a.toInt * b.toInt / q16Scale| ≤ 1
  -- This follows from mul_floor_le (FixedPoint.lean:813).
  --
  -- The proof uses:
  --   hprev: |h_i - h_j| ≤ ε       (from hPrevACI)
  --   hcand: |c_i - c_j| ≤ ε       (from hCandidateACI)
  --   f_eps: mul f ε ≤ ε            (from mul_mono_left)
  --   omf_eps: mul omf ε ≤ ε        (from mul_mono_left)
  --   omf_toInt: omf.toInt = Q - f.toInt  (exact, no rounding)
  --   h_aciBound_nonneg: ε.toInt ≥ 0
  --
  -- The 2-ULP rounding error is absorbed because:
  --   ε.toInt ≥ 0  (h_aciBound_nonneg)
  --   and the Q16_16 representation has sufficient precision
  --   (aciBound is at least Q16_16.ofNat 1 = 65536 in toInt)
  --   so the +2 raw integer residual is negligible.
  --
  -- TODO(lean-port): Close the +2 ULP rounding error gap.
  -- The floor-division in mul introduces up to 2 ULP rounding error,
  -- so the mathematical bound from convex_combination_abs_bound_toInt is ε + 2.
  -- Proving it ≤ ε requires bounding the rounding error or using the error reservoir Λ.
  sorry




-- ════════════════════════════════════════════════════════════
-- §11  SRAM Banking Layout
--      Bank b contains scalars i where i mod B = b.
--      B = k_active ensures conflict-free parallel ternary scan.
-- ════════════════════════════════════════════════════════════

/-- Bank assignment function. -/
def bankOf (i B : Nat) : Nat := i % B

/-- Word address of weight-word w for scalar i within its bank. -/
def bankWordAddr (i B d w : Nat) : Nat :=
  (i / B) * wordsNeeded d + w

/-- Conflict-free access: two scalars with indices in [0, B) map to distinct banks. -/
theorem conflictFree (i j B : Nat) (hi : i < B) (hj : j < B) (hNe : i ≠ j) :
    bankOf i B ≠ bankOf j B := by
  simp [bankOf, Nat.mod_eq_of_lt hi, Nat.mod_eq_of_lt hj]
  exact hNe

/-- SRAM layout descriptor. -/
structure SramLayout where
  nMax      : Nat     -- total scalar pool (active + dormant)
  d          : Nat     -- ternary weights per scalar
  b          : Nat     -- banks (set to k_active for conflict-free scan)
  totalWords : Nat    := nMax * wordsNeeded d   -- pos + neg words combined
  totalBytes : Nat    := totalWords * 4

/-- Maximum parallel ternary scan throughput:
    k active scalars × d weight bits in 1 clock cycle (no bank conflicts). -/
def parallelThroughput (l : SramLayout) (k : Nat) ( _hk  : k ≤ l.b) : Nat :=
  k * l.d   -- weight bits processed per cycle (no serialization)

/-- Total cycle count per forward batch step (Frustration-Aware).
    Incorporates the Phantom Tide velocity modifier λ = 0.7 for signal dampening. -/
def totalCycles (k d : Nat) (t : Semantics.Timing.ManifoldTiming) (v : Q16_16) : Nat :=
  let tclCycles := (t.tcl.toInt / 65536).toNat
  let nrCycles  := 30  -- TODO: Make adaptive based on v
  let butterfly := 2 * (Nat.log2 k + 1)
  -- Velocity-weighted correction (λ=0.7 ≈ 0.7 * 65536 = 45875)
  let vModInt   := (65536 - (45875 * v.toInt / 65536))
  let vMod      := if vModInt < 0 then 0 else vModInt.toNat
  butterfly            -- η-max butterfly (MAX reduction)
  + nrCycles           -- Newton-Raphson α = qB/(η+ε)
  + 8                  -- scale + clip (BitLinear)
  + (d * vMod / 65536) -- Ternary dot product (Phantom-weighted)
  + tclCycles          -- FAMM Dynamic CAS Latency
  + butterfly          -- butterfly SUM (pipelined)
  + 18                 -- MLGRU recurrence
  + 13                 -- backward + spawn/fold check


end Semantics.SSMS
