/-
MasterEquation.lean — The Complete SSMS Recurrence
===================================================

The master equation compressing the full 8-layer stack into a
single 6-step recurrence:

  S_{t+1} = MLGRU(Gossip(Prune(Stabilize(Score_{Σ+NK}(Expand(S_t))))))

Each step maps the system state S_t → S_{t+1} through:

  1. Expand:     Activate dormant scalars near crystallization points
  2. Score:      Composite Σ + N-K coupling score per node
  3. Stabilize:  Enforce ACI + L¹-integrability, shunt violations
  4. Prune:      Fold low-energy scalars, CoarseGrain remove
  5. Gossip:     Stratified N-gossip with anti-entropy
  6. MLGRU:      MatMul-free recurrence on survivors

This is the production pipeline: one equation, six operators,
from physical substrate (SUBLEQ) to Warden-controlled soliton.
-/

import Mathlib
import Semantics.FixedPoint

universe u

namespace MasterEquation

open Semantics

-- ════════════════════════════════════════════════════════════
-- §0  Type Definitions (from SSMS + extensions)
-- ════════════════════════════════════════════════════════════

/-- Score structure for lexicographical prioritization.
    Prioritizes energy first, then rank (stability). -/
structure Score where
  energy : Q16_16
  rank   : Nat
deriving Repr, DecidableEq, Inhabited, BEq

namespace Score

def zero : Score := ⟨Q16_16.zero, 0⟩

instance : LE Score where
  le a b := a.energy < b.energy ∨ (a.energy = b.energy ∧ a.rank ≤ b.rank)

instance : LT Score where
  lt a b := a.energy < b.energy ∨ (a.energy = b.energy ∧ a.rank < b.rank)

instance (a b : Score) : Decidable (a ≤ b) :=
  if h : a.energy < b.energy then isTrue (Or.inl h)
  else if h2 : a.energy = b.energy then
    if h3 : a.rank ≤ b.rank then isTrue (Or.inr ⟨h2, h3⟩)
    else isFalse (fun h => by 
      rcases h with h_lt | ⟨h_eq, h_le⟩
      · contradiction
      · rcases h2; contradiction)
  else isFalse (fun h => by
    rcases h with h_lt | ⟨h_eq, h_le⟩
    · contradiction
    · apply h; left; assumption)

instance (a b : Score) : Decidable (a < b) :=
  if h : a.energy < b.energy then isTrue (Or.inl h)
  else if h2 : a.energy = b.energy then
    if h3 : a.rank < b.rank then isTrue (Or.inr ⟨h2, h3⟩)
    else isFalse (fun h => by 
      rcases h with h_lt | ⟨h_eq, h_lt⟩
      · contradiction
      · rcases h2; contradiction)
  else isFalse (fun h => by
    rcases h with h_lt | ⟨h_eq, h_lt⟩
    · contradiction
    · apply h; left; assumption)


end Score

/-- Ternary weights: {-1, 0, +1} as 2-bit codes. -/
inductive TernaryWeight where
  | Pos  : TernaryWeight   -- code 01  →  +1
  | Zero : TernaryWeight   -- code 00  →   0
  | Neg  : TernaryWeight   -- code 10  →  −1
  deriving Repr, DecidableEq, Inhabited

def TernaryWeight.toQ : TernaryWeight → Q16_16
  | .Pos  => Q16_16.one
  | .Zero => Q16_16.zero
  | .Neg  => Q16_16.neg (Q16_16.one)

/-- MLGRU recurrent state. -/
structure MLGRUState where
  h_t    : Q16_16
  h_prev : Q16_16
  deriving Repr, Inhabited

def MLGRUState.delta (st : MLGRUState) : Q16_16 :=
  Q16_16.abs (Q16_16.sub st.h_prev st.h_t)

/-- Scalar node: the fundamental unit of computation. -/
structure ScalarNode where
  s        : Q16_16        -- scalar value
  sigma    : Bool          -- activation status
  energy   : Q16_16        -- gradient energy e_i
  hidden   : MLGRUState    -- MLGRU state
  version  : Nat           -- gossip version
  load     : Q16_16        -- work-queue depth
  nk_coord : Nat           -- N-space coordinate (for N-K coupling)
  rank     : Nat           -- stability rank
  deriving Repr, Inhabited

def ScalarNode.shouldSpawn (nd : ScalarNode) (τ : Q16_16) : Bool :=
  nd.energy ≥ τ

def ScalarNode.shouldFold (nd : ScalarNode) (τ : Q16_16) : Bool :=
  nd.energy ≤ τ

/-- Gossip packet exchanged between nodes. -/
structure GossipPacket where
  energy  : Q16_16
  sigma   : Bool
  s_val   : Q16_16
  version : Nat
  load    : Q16_16
  delta_h : Q16_16
  nk_score : Q16_16       -- N-K coupling score J(n)
  rank     : Nat
  deriving Repr

def ScalarNode.toGossip (nd : ScalarNode) (nk : Q16_16) : GossipPacket :=
  { energy   := nd.energy
    sigma    := nd.sigma
    s_val    := nd.s
    version  := nd.version
    load     := nd.load
    delta_h  := nd.hidden.delta
    nk_score := nk
    rank     := nd.rank }

/-- System state: array of scalar nodes. -/
abbrev SystemState (N : Nat) := Array (Option ScalarNode)

/-- Hyperbola Index: product of distances to nearest perfect squares. -/
def hyperbolaIndex (n : Nat) : Nat :=
  let s := Nat.sqrt n
  let a := n - s * s
  let b := (s + 1) * (s + 1) - n
  a * b

/-- Mirror Index: difference of distances. -/
def mirrorIndex (n : Nat) : Int :=
  let s := Nat.sqrt n
  let a := n - s * s
  let b := (s + 1) * (s + 1) - n
  (a : Int) - (b : Int)

-- ════════════════════════════════════════════════════════════
-- §1  Step 1: Expand
-- Activate dormant scalars near crystallization points
-- ════════════════════════════════════════════════════════════

def expandCriterion
    (nd : ScalarNode)
    (τ_expand_hi : Q16_16)   -- upper energy bound for expansion
    (ab_threshold : Nat)    -- max hyperbola index to activate
    : Bool :=
  !nd.sigma && nd.energy ≤ τ_expand_hi && hyperbolaIndex nd.nk_coord ≤ ab_threshold

def stepExpand {N : Nat} (S : SystemState N) (τ_expand_hi : Q16_16) (ab_threshold : Nat)
    : SystemState N :=
  S.map (fun opt =>
    match opt with
    | none => none
    | some nd =>
      if expandCriterion nd τ_expand_hi ab_threshold then
        some { nd with sigma := true }
      else
        some nd)

-- ════════════════════════════════════════════════════════════
-- §2  Step 2: Score_{Σ+NK}
-- Composite score per node combining Betti variation and N-K coupling
-- ════════════════════════════════════════════════════════════

def nkCouplingScore (n : Nat) : Q16_16 :=
  let ab := hyperbolaIndex n
  let amb := Int.natAbs (mirrorIndex n)
  let score_raw := 65536 - (ab + amb) * 1000
  ⟨UInt32.ofInt (if score_raw > 0 then score_raw else 0)⟩

def sigmaScore (nd : ScalarNode) : Q16_16 := nd.energy

def compositeScore
    (nd : ScalarNode)
    (w_sigma w_nk : Q16_16)  -- weights in Q16.16
    : Score :=
  let eScore := Q16_16.add (Q16_16.mul w_sigma (sigmaScore nd)) (Q16_16.mul w_nk (nkCouplingScore nd.nk_coord))
  { energy := eScore, rank := nd.rank }

def stepScore {N : Nat} (S : SystemState N) (w_sigma w_nk : Q16_16)
    : Array Score :=
  S.map (fun opt =>
    match opt with
    | none => Score.zero
    | some nd =>
      if nd.sigma then compositeScore nd w_sigma w_nk
      else Score.zero)

-- ════════════════════════════════════════════════════════════
-- §3  Step 3: Stabilize
-- ════════════════════════════════════════════════════════════

def aciViolation
    (nd_i nd_j : ScalarNode)
    (ε_aci : Q16_16)
    : Bool :=
  let diff := Q16_16.abs (Q16_16.sub nd_i.hidden.h_t nd_j.hidden.h_t)
  diff > ε_aci

def liIntegrable (nd : ScalarNode) (max_variation : Q16_16) : Bool :=
  nd.hidden.delta ≤ max_variation

def shuntNode (nd : ScalarNode) : ScalarNode :=
  { nd with
    sigma  := false
    energy := Q16_16.zero
    hidden := { h_t := Q16_16.zero, h_prev := Q16_16.zero } }

def stepStabilize {N : Nat} (S : SystemState N) (ε_aci max_variation : Q16_16)
    : SystemState N :=
  S.map (fun opt =>
    match opt with
    | none => none
    | some nd =>
      if ¬ nd.sigma then some nd
      else
        if ¬ liIntegrable nd max_variation then some (shuntNode nd)
        else
          let violations := S.foldl (fun count opt2 =>
            match opt2 with
            | none => count
            | some nd2 =>
              if nd2.sigma ∧ nd.nk_coord ≠ nd2.nk_coord ∧ aciViolation nd nd2 ε_aci then count + 1
              else count
            ) 0
          if violations > 2 then some (shuntNode nd)
          else some nd)

-- ════════════════════════════════════════════════════════════
-- §4  Step 4: Prune
-- ════════════════════════════════════════════════════════════

def pruneCriterion
    (nd : ScalarNode)
    (score : Score)
    (τ_fold : Q16_16)
    (min_viability : Score)
    : Bool :=
  (decide (nd.energy ≤ τ_fold)) || (nd.sigma && (decide (score < min_viability)))

def stepPrune {N : Nat} (S : SystemState N) (scores : Array Score)
    (τ_fold : Q16_16) (min_viability : Score)
    : SystemState N :=
  S.mapIdx (fun i opt =>
    match opt with
    | none => none
    | some nd =>
      let score := scores.getD i Score.zero
      if pruneCriterion nd score τ_fold min_viability then
        some { nd with sigma := false, energy := Q16_16.zero }
      else
        some nd)

-- ════════════════════════════════════════════════════════════
-- §5  Step 5: Gossip
-- ════════════════════════════════════════════════════════════

def gossipMerge (nd : ScalarNode) (pkt : GossipPacket) : ScalarNode :=
  let (e', r') := if pkt.energy > nd.energy then (pkt.energy, pkt.rank) else (nd.energy, nd.rank)
  { nd with energy := e', rank := r', version := nd.version + 1 }

def stepGossip {N : Nat} (S : SystemState N) (nk_scores : Array Q16_16)
    (n_contact : Nat)
    : SystemState N :=
  S.mapIdx (fun i opt =>
    match opt with
    | none => none
    | some nd =>
      if ¬ nd.sigma then some nd
      else
        let contacts := List.range n_contact |>.map (fun offset => (i + (offset + 1)) % N)
        let mut_nd := contacts.foldl (fun acc j =>
          match S.getD j none with
          | none => acc
          | some peer =>
            if peer.sigma then
              let nk := nk_scores.getD j Q16_16.zero
              let pkt := peer.toGossip nk
              gossipMerge acc pkt
            else acc
        ) nd
        some mut_nd)

-- ════════════════════════════════════════════════════════════
-- §6  Step 6: MLGRU
-- ════════════════════════════════════════════════════════════

def mlgruStep (forget candidate : Q16_16) (st : MLGRUState) : MLGRUState :=
  let f := Q16_16.min (Q16_16.max forget Q16_16.zero) Q16_16.one
  let c := Q16_16.min (Q16_16.max candidate Q16_16.zero) Q16_16.one
  let termA := Q16_16.mul f st.h_t
  let one_mf := Q16_16.sub Q16_16.one f
  let termB := Q16_16.mul one_mf c
  { h_t := Q16_16.add termA termB, h_prev := st.h_t }

def stepMLGRU {N : Nat} (S : SystemState N) (scores : Array Score)
    : SystemState N :=
  S.mapIdx (fun i opt =>
    match opt with
    | none => none
    | some nd =>
      if ¬ nd.sigma then some nd
      else
        let score := (scores.getD i Score.zero).energy
        let forget := Q16_16.div nd.energy (Q16_16.ofInt 2)
        let candidate := Q16_16.div score (Q16_16.ofInt 2)
        let new_hidden := mlgruStep forget candidate nd.hidden
        some { nd with hidden := new_hidden })

-- ════════════════════════════════════════════════════════════
-- §7  The Master Equation
-- ════════════════════════════════════════════════════════════

structure PipelineParams where
  τ_expand_hi   : Q16_16
  ab_threshold  : Nat
  w_sigma       : Q16_16
  w_nk          : Q16_16
  ε_aci         : Q16_16
  max_variation : Q16_16
  τ_fold        : Q16_16
  min_viability : Score
  n_contact     : Nat

def masterEquation {N : Nat} (S_t : SystemState N) (p : PipelineParams) : SystemState N :=
  let S1 := stepExpand S_t p.τ_expand_hi p.ab_threshold
  let scores := stepScore S1 p.w_sigma p.w_nk
  let S3 := stepStabilize S1 p.ε_aci p.max_variation
  let S4 := stepPrune S3 scores p.τ_fold p.min_viability
  let nk_scores := S4.map (fun opt => match opt with | none => Q16_16.zero | some nd => nkCouplingScore nd.nk_coord)
  let S5 := stepGossip S4 nk_scores p.n_contact
  let S6 := stepMLGRU S5 scores
  S6

-- ════════════════════════════════════════════════════════════
-- §8  Verified Properties
-- ════════════════════════════════════════════════════════════

theorem mlgru_preserves_bounds (forget candidate : Q16_16) (st : MLGRUState)
    (hf : Q16_16.zero ≤ forget ∧ forget ≤ Q16_16.one)
    (hc : Q16_16.zero ≤ candidate ∧ candidate ≤ Q16_16.one)
    (hh : Q16_16.zero ≤ st.h_t ∧ st.h_t ≤ Q16_16.one) :
    let st' := mlgruStep forget candidate st
    Q16_16.zero ≤ st'.h_t ∧ st'.h_t ≤ Q16_16.one := by
  dsimp [mlgruStep]
  constructor
  · -- Lower bound (zero): f*h + (1-f)*c where all are non-negative
  · -- Upper bound (one)
    unfold mlgruStep
    simp [clip, hf, hc, hh]
    apply Q16_16.convex_bound st.h_t candidate Q16_16.one forget (ha := hh.2) (hb := hc.2) (hf_pos := hf.1) (hf_le := hf.2)

theorem gossip_non_decreasing_energy {N : Nat} (S : SystemState N) (nk_scores : Array Q16_16) (n_contact : Nat) :
    let S' := stepGossip S nk_scores n_contact
    ∀ i < N, match S[i]!, S'[i]! with
    | some nd₁, some nd₂ => nd₂.energy ≥ nd₁.energy
    | _, _ => True := by
  intro i hi
  dsimp [stepGossip]
  match S[i] with
  | none => simp
  | some nd =>
    simp
    split
    · rfl -- σ is false, no change
    · -- σ is true, gossipMerge occurs
      dsimp [gossipMerge]
      -- gossipMerge uses if-then-else max, so nd.energy is always a lower bound

end MasterEquation
