/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

OrderedFieldTokens.lean — Test-Time Search with Ordered Field Tokens

This module formalizes the AMMR-backed projection solver architecture with
ordered field tokenization for verifiable, composable, search-driven field
computation.

Covers:
  §1  Token type definitions (ActivateBasis, CommitCRC, Promote, ResolveTail)
  §2  Coarse-to-fine ordering phases
  §3  State representation with grid, QR decompositions, CRC, AMMR
  §4  Verifier function with weighted components
  §5  Beam search procedure over token sequences
  §6  AMMR integration for verifiable computation history
  §7  Token transition semantics
  §8  Search trace replayability theorems

Per AGENTS.md §1.4: All new hot-path code uses Q16_16 fixed-point.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: All defs must have eval witnesses or theorems.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Fin.Basic
import Std

namespace Semantics.OrderedFieldTokens

-- ════════════════════════════════════════════════════════════
-- §0  Fixed-Point Precision (Q16.16 for verifier scores)
-- ════════════════════════════════════════════════════════════

/-- Q16.16 fixed-point for verifier scores and weights. -/
structure Q1616 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q1616

def zero    : Q1616 := ⟨0⟩
def one     : Q1616 := ⟨65536⟩        -- 0x00010000 = 1.0
def epsilon : Q1616 := ⟨1⟩            -- 2^{-16}
def ofNat (n : Nat) : Q1616 := ⟨Int.ofNat n⟩

def add (a b : Q1616) : Q1616 := ⟨a.raw + b.raw⟩
def sub (a b : Q1616) : Q1616 := ⟨a.raw - b.raw⟩
def mul (a b : Q1616) : Q1616 := ⟨(a.raw * b.raw) / 65536⟩
def div (a b : Q1616) : Q1616 := ⟨(a.raw * 65536) / b.raw⟩

def le (a b : Q1616) : Prop := a.raw ≤ b.raw
instance : LE Q1616 := ⟨le⟩

instance : Add Q1616 := ⟨add⟩
instance : Sub Q1616 := ⟨sub⟩
instance : Mul Q1616 := ⟨mul⟩

/-- Weighted sum: Σᵢ wᵢ · vᵢ -/
def weightedSum (pairs : List (Q1616 × Q1616)) : Q1616 :=
  pairs.foldl (fun acc (w, v) => acc + (w * v)) zero

end Q1616

-- ════════════════════════════════════════════════════════════
-- §1  Token Type Definitions
-- ════════════════════════════════════════════════════════════

/-- Region identifier for basis activation. -/
abbrev RegionId := Nat

/-- Basis mode index within a region. -/
abbrev BasisMode := Nat

/-- CRC (Cyclic Redundancy Check) cell identifier. -/
abbrev CRCCell := Nat × Nat  -- (row, col) in grid

/-- Grid cell coordinate. -/
structure Cell where
  row : Nat
  col : Nat
  deriving DecidableEq, Repr, Inhabited

/-- Token types for ordered field computation. -/
inductive Token
  | activateBasis (r : RegionId) (k : BasisMode)
  | commitCRC (c : CRCCell)
  | promote (i j : Cell)
  | resolveTail (i j : Cell)
  deriving DecidableEq, Repr, Inhabited

namespace Token

/-- String representation for AMMR hashing. -/
def toString : Token → String
  | activateBasis r k => s!"ActivateBasis({r},{k})"
  | commitCRC c         => s!"CommitCRC({c.1},{c.2})"
  | promote i j         => s!"Promote({i.row},{i.col};{j.row},{j.col})"
  | resolveTail i j     => s!"ResolveTail({i.row},{i.col};{j.row},{j.col})"

/-- Token category for phase classification. -/
inductive Category
  | globalStructure
  | mesoscopicStabilization
  | localRefinement
  | terminalCompletion
  deriving DecidableEq, Repr

/-- Classify token by coarse-to-fine phase. -/
def category : Token → Category
  | activateBasis _ _ => Category.globalStructure
  | commitCRC _       => Category.mesoscopicStabilization
  | promote _ _       => Category.localRefinement
  | resolveTail _ _ => Category.terminalCompletion

end Token

-- ════════════════════════════════════════════════════════════
-- §2  Coarse-to-Fine Ordering Phases
-- ════════════════════════════════════════════════════════════

/-- Search phase in the token execution schedule. -/
inductive Phase
  | phase1_globalStructure
  | phase2_mesoscopicStabilization
  | phase3_localRefinement
  | phase4_terminalCompletion
  deriving DecidableEq, Repr, Inhabited, Ord

namespace Phase

/-- Total order on phases (coarse-to-fine). -/
def toNat : Phase → Nat
  | phase1_globalStructure         => 0
  | phase2_mesoscopicStabilization => 1
  | phase3_localRefinement         => 2
  | phase4_terminalCompletion      => 3

/-- Check if phase p comes before or at phase q. -/
def le (p q : Phase) : Bool := p.toNat ≤ q.toNat

end Phase

/-- Token sequence ordered by phase (enforced structure). -/
structure OrderedTokens where
  phase1 : List Token  -- activateBasis tokens
  phase2 : List Token  -- commitCRC tokens
  phase3 : List Token  -- promote tokens
  phase4 : List Token  -- resolveTail tokens

namespace OrderedTokens

/-- Flatten to chronological sequence. -/
def toList (ts : OrderedTokens) : List Token :=
  ts.phase1 ++ ts.phase2 ++ ts.phase3 ++ ts.phase4

/-- Check all tokens are in correct phase categories. -/
def wellFormed (ts : OrderedTokens) : Bool :=
  (ts.phase1.all fun t => t.category == .globalStructure) &&
  (ts.phase2.all fun t => t.category == .mesoscopicStabilization) &&
  (ts.phase3.all fun t => t.category == .localRefinement) &&
  (ts.phase4.all fun t => t.category == .terminalCompletion)

end OrderedTokens

-- ════════════════════════════════════════════════════════════
-- §3  State Representation
-- ════════════════════════════════════════════════════════════

/-- Grid state with cell values (None = unresolved). -/
abbrev Grid (rows cols : Nat) := Fin rows → Fin cols → Option Q1616

/-- QR decomposition for region r (simplified representation). -/
structure RegionQR where
  q : Array Q1616  -- Q matrix (orthogonal)
  r : Array Q1616  -- R matrix (upper triangular)
  deriving Repr, Inhabited

/-- CRC pattern with stability signature. -/
structure CRCState where
  cell : CRCCell
  signature : UInt64  -- Hash of committed pattern
  stable : Bool
  deriving Repr, Inhabited

/-- AMMR (Authenticated Merkle Mountain Range) root reference. -/
structure AMMRRoot where
  rootHash : UInt64
  height : Nat
  deriving Repr, Inhabited, DecidableEq

/-- Complete solver state at step t. -/
structure SolverState (rows cols : Nat) where
  grid : Grid rows cols
  regions : Array RegionQR
  crcs : Array CRCState
  ammr : AMMRRoot
  stepCount : Nat
  deriving Inhabited

-- ════════════════════════════════════════════════════════════
-- §4  Verifier Function
-- ════════════════════════════════════════════════════════════

/-- Verifier component weights (normalized to 1.0 total). -/
structure VerifierWeights where
  wProj : Q1616  -- projection consistency
  wRoute : Q1616  -- routing agreement
  wCRC : Q1616    -- pattern stability
  wAMMR : Q1616   -- historical consistency
  
  deriving Repr, Inhabited

namespace VerifierWeights

/-- Default weights: equal 0.25 each (65536/4 = 16384 in Q16.16). -/
def default : VerifierWeights :=
  { wProj := ⟨16384⟩, wRoute := ⟨16384⟩, wCRC := ⟨16384⟩, wAMMR := ⟨16384⟩ }

/-- Check weights sum to approximately 1.0 (within epsilon). -/
def normalized (w : VerifierWeights) : Bool :=
  let sum := w.wProj + w.wRoute + w.wCRC + w.wAMMR
  (65530 ≤ sum.raw) && (sum.raw ≤ 65542)  -- 1.0 ± 0.0001

end VerifierWeights

/-- Projection consistency: low residuals in QR solutions. -/
def projectionScore {r c : Nat} (state : SolverState r c) : Q1616 :=
  -- Simplified: count resolved cells vs total
  let total := r * c
  let resolved := state.grid |> (fun g =>
    (List.finRange r).foldl (fun acc i =>
      (List.finRange c).foldl (fun acc2 j =>
        match g i j with
        | some _ => acc2 + 1
        | none => acc2) acc) 0)
  if total = 0 then Q1616.zero else Q1616.ofNat (resolved * 65536 / total)

/-- Routing agreement: consistency across region boundaries. -/
def routingScore {r c : Nat} (_state : SolverState r c) : Q1616 :=
  -- Placeholder: would check boundary cell agreement
  ⟨65536⟩  -- 1.0 (optimistic)

/-- CRC stability: fraction of stable committed patterns. -/
def crcScore {r c : Nat} (state : SolverState r c) : Q1616 :=
  if state.crcs.isEmpty then ⟨65536⟩  -- 1.0 if no CRCs
  else
    let stableCount := state.crcs.foldl (fun acc c => if c.stable then acc + 1 else acc) 0
    Q1616.ofNat (stableCount * 65536 / state.crcs.size)

/-- AMMR consistency: height-based maturity score. -/
def ammrScore {r c : Nat} (state : SolverState r c) : Q1616 :=
  -- More commits = higher confidence (saturating)
  let h := state.ammr.height
  let sat := if h > 10 then 10 else h
  Q1616.ofNat (sat * 65536 / 10)

/-- Global verifier function: weighted sum of components. -/
def verifier {r c : Nat} (state : SolverState r c) (weights : VerifierWeights) : Q1616 :=
  let vProj := projectionScore state
  let vRoute := routingScore state
  let vCRC := crcScore state
  let vAMMR := ammrScore state
  weights.wProj * vProj + weights.wRoute * vRoute + weights.wCRC * vCRC + weights.wAMMR * vAMMR

-- ════════════════════════════════════════════════════════════
-- §5  Beam Search Procedure
-- ════════════════════════════════════════════════════════════

/-- Beam entry: state with its verifier score. -/
structure BeamEntry (rows cols : Nat) where
  state : SolverState rows cols
  score : Q1616
  tokensApplied : List Token
  deriving Inhabited

/-- Beam search configuration. -/
structure BeamConfig where
  width : Nat      -- B: number of states to keep
  maxDepth : Nat   -- T: maximum token sequence length
  deriving Repr, Inhabited

/-- Generate candidate tokens for current phase. -/
def generateCandidates (phase : Phase) (state : SolverState r c) : List Token :=
  match phase with
  | .phase1_globalStructure =>
      -- Generate activateBasis for each region
      (List.range state.regions.size).map (fun i => Token.activateBasis i 0)
  | .phase2_mesoscopicStabilization =>
      -- Generate commitCRC for unresolved cells
      []  -- Simplified: would scan grid for unresolved
  | .phase3_localRefinement =>
      []  -- Simplified: would generate promote for adjacent cells
  | .phase4_terminalCompletion =>
      []  -- Simplified: would identify tail cells

/-- Apply token to state (transition function f). -/
def applyToken {r c : Nat} (state : SolverState r c) (token : Token) : SolverState r c :=
  match token with
  | Token.activateBasis _reg _k =>
      -- Update QR decomposition for region
      { state with stepCount := state.stepCount + 1 }
  | Token.commitCRC cell =>
      -- Commit pattern to CRC memory
      let newCRC : CRCState := { cell := cell, signature := 0, stable := true }
      { state with crcs := state.crcs.push newCRC, stepCount := state.stepCount + 1 }
  | Token.promote _i _j =>
      -- Promote proposal using routed support
      { state with stepCount := state.stepCount + 1 }
  | Token.resolveTail _i _j =>
      -- Apply strict deterministic scoring
      { state with stepCount := state.stepCount + 1 }

/-- Select top B states by verifier score. -/
def selectTop {r c : Nat} (entries : List (BeamEntry r c)) (b : Nat) : List (BeamEntry r c) :=
  let sorted := entries.toArray.qsort (fun a b => b.score.raw < a.score.raw)
  sorted.toList.take b

/-- Single beam search step. -/
def beamStep {r c : Nat} (entries : List (BeamEntry r c)) (phase : Phase)
    (weights : VerifierWeights) (config : BeamConfig) : List (BeamEntry r c) :=
  let candidates := entries.flatMap (fun entry =>
    let toks := generateCandidates phase entry.state
    toks.map (fun tok =>
      let newState := applyToken entry.state tok
      let newScore := verifier newState weights
      { state := newState, score := newScore, tokensApplied := tok :: entry.tokensApplied }))
  selectTop candidates config.width

-- ════════════════════════════════════════════════════════════
-- §6  AMMR Integration
-- ════════════════════════════════════════════════════════════

/-- AMMR leaf node: committed token with state summary. -/
structure AMMRLeaf where
  tokenHash : UInt64
  stateSummary : UInt64  -- Hash of algebraic state
  stepIndex : Nat
  deriving Repr, Inhabited, DecidableEq

/-- Compute hash of token for AMMR integrity. -/
def hashToken (t : Token) : UInt64 :=
  -- Simplified: use string hash
  let s := t.toString
  s.foldl (fun acc c => acc * 31 + c.toNat.toUInt64) 0

/-- Compute summary of solver state. -/
def summarizeState {r c : Nat} (state : SolverState r c) : UInt64 :=
  -- Simplified: combine step count with CRC count
  state.stepCount.toUInt64 * 1000 + state.crcs.size.toUInt64

/-- Record token commit in AMMR. -/
def recordCommit (ammr : AMMRRoot) (token : Token) (state : SolverState r c) : AMMRRoot :=
  let _leaf : AMMRLeaf :=
    { tokenHash := hashToken token
      stateSummary := summarizeState state
      stepIndex := state.stepCount }
  -- Simplified: would compute Merkle root update
  { ammr with height := ammr.height + 1 }

-- ════════════════════════════════════════════════════════════
-- §7  Token Transition Semantics
-- ════════════════════════════════════════════════════════════

/-- State transition relation: S_{t+1} = f(S_t, z_t). -/
def transition {r c : Nat} (S_t : SolverState r c) (z_t : Token) (S_next : SolverState r c) : Prop :=
  S_next = applyToken S_t z_t

/-- Token sequence is valid if each transition is valid. -/
def validTransitions {r c : Nat} : List (SolverState r c) → List Token → Prop
  | [_s], [] => True
  | s1 :: s2 :: ss, t :: ts => transition s1 t s2 ∧ validTransitions (s2 :: ss) ts
  | _, _ => False

/-- Token sequence is valid if each transition is valid. -/
def validTokenSequence {r c : Nat} (S0 : SolverState r c) (tokens : List Token)
    (states : List (SolverState r c)) : Prop :=
  states.head? = some S0 ∧
  validTransitions states tokens

-- ════════════════════════════════════════════════════════════
-- §8  Search Trace Replayability Theorems
-- ════════════════════════════════════════════════════════════

/-- AMMR leaf integrity: token hash matches the fold used to build it. -/
theorem ammrLeafIntegrity (t : Token) :
    hashToken t = t.toString.foldl (fun acc c => acc * 31 + c.toNat.toUInt64) 0 := by
  rfl

/-- Every token application advances the solver clock by one step. -/
theorem stepCountAdvances {r c : Nat} (state : SolverState r c) (t : Token) :
    (applyToken state t).stepCount = state.stepCount + 1 := by
  cases t <;> rfl

/-- Beam search preserves top-B invariant. -/
theorem beamSearchInvariant {r c : Nat} (entries : List (BeamEntry r c)) (phase : Phase)
    (weights : VerifierWeights) (config : BeamConfig) :
    (beamStep entries phase weights config).length ≤ config.width := by
  unfold beamStep selectTop
  simp

-- ════════════════════════════════════════════════════════════
-- Verification Examples (AGENTS.md §4 requirement)
-- ════════════════════════════════════════════════════════════

#eval Token.activateBasis 0 0  -- ActivateBasis(0,0)
#eval Token.commitCRC (1, 2)     -- CommitCRC(1,2)
#eval Token.category (Token.promote ⟨0,0⟩ ⟨1,1⟩)  -- localRefinement

#eval Phase.le .phase1_globalStructure .phase3_localRefinement  -- true

#eval VerifierWeights.default.normalized  -- true

#eval hashToken (Token.activateBasis 42 3)  -- Some hash value

end Semantics.OrderedFieldTokens
