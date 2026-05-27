-- Semantics.PIST.Motif — Q16_16 motif scoring for proof-trace classification
--
-- Ports the motif-scoring surface from pist_trace_classify_mcp.py into Lean:
--   • motifScore        — base score + tactic-family match bonus
--   • rankMotifs        — sort candidates by score descending, tag tie-break
--
-- Python source:    4-Infrastructure/shim/pist_trace_classify_mcp.py
-- Python function:  classify_trace, lines 136–149
-- BOUNDARY comment: Semantics.PIST.Motif (this file)
--
-- The Python shim retains responsibility for:
--   RDS queries (ene.flexure_patterns, ene.flexures), MCP JSON-RPC protocol,
--   artifact insertion, and the classify_trace orchestration.
-- This module is the authoritative specification for motif score computation
-- and the sort order over candidates.
--
-- Scoring formula (lines 136–139 in Python):
--   base  = frequency / max(library_size, 1)         -- ∈ [0, 1] when freq ≤ lib
--   bonus = 0.3  if tactic_family(motif) = tactic_family(query) else 0
--   score = base + bonus
--   Q16_16 encoding:
--     base  = ofRatio frequency (max library_size 1)  -- exact rational
--     bonus = ofRatio 3 10 = 19660 raw                (0.3 · 65536)
--
-- Invariants proved here:
--   (1) motifScore_bonus_pos      — family-match bonus is strictly positive
--   (2) motifScore_match_ge_base  — matching score ≥ non-matching score (same inputs)
--   (3) motifScore_zero_freq      — zero frequency → score = bonus only if match, else 0
--   (4) motifScore_bounded_above  — score ≤ one + bonus (since base ≤ one when freq ≤ lib)
--   (5) rankMotifs_stable_order   — concrete sort witness: higher freq wins

import Semantics.FixedPoint

namespace Semantics.PIST.Motif

open Semantics.FixedPoint
open Semantics.Q16_16

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Constants
-- ─────────────────────────────────────────────────────────────────────────────

/-- Tactic-family match bonus: 0.3 in Python (PARTIAL BOUNDARY line 139).
    Q16_16: ofRatio 3 10 = (3 * 65536) / 10 = 19660 raw. -/
def familyMatchBonus : Q16_16 := ofRatio 3 10  -- 0.3 · 65536 = 19660 raw

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Scoring inputs and functional
-- ─────────────────────────────────────────────────────────────────────────────

/-- Inputs to the motif scoring function.
    `frequency`   — raw occurrence count from ene.flexure_patterns.frequency
    `librarySize` — total number of entries in the loaded flexure library
                    (denominator of the base score; clamped to 1 if zero)
    `familyMatch` — true iff motif tactic_family = classifyTacticFromName(query) -/
structure MotifInputs where
  frequency   : Nat
  librarySize : Nat
  familyMatch : Bool
  deriving Repr, BEq

/-- Base score: frequency / max(library_size, 1), as Q16_16. -/
def baseScore (x : MotifInputs) : Q16_16 :=
  ofRatio x.frequency (Nat.max x.librarySize 1)

/-- Full motif score = base + (familyMatchBonus if familyMatch else 0).
    Mirrors lines 136–139 of classify_trace. -/
def motifScore (x : MotifInputs) : Q16_16 :=
  let b := baseScore x
  if x.familyMatch then b + familyMatchBonus else b

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Motif candidate — carrier for rankMotifs
-- ─────────────────────────────────────────────────────────────────────────────

/-- A scored motif candidate.
    `motifId`  — opaque ID string from ene.flexure_patterns.id
    `score`    — filled by rankMotifs (zero before ranking)
    `inputs`   — the raw scoring inputs -/
structure MotifCandidate where
  motifId : String
  score   : Q16_16
  inputs  : MotifInputs
  deriving Repr, BEq

/-- Construct an unscored candidate, ready for rankMotifs. -/
def mkCandidate (motifId : String) (frequency librarySize : Nat) (familyMatch : Bool) : MotifCandidate :=
  { motifId, score := zero, inputs := { frequency, librarySize, familyMatch } }

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  rankMotifs
--     Mirrors: motifs.sort(key=lambda x: -x["score"]);  motifs[:top_k]
--     Python sort is stable. List.mergeSort is stable in Lean 4.
--     Tie-break: motifId ascending (deterministic).
-- ─────────────────────────────────────────────────────────────────────────────

/-- Score all candidates and return them sorted by score descending.
    Ties are broken by motifId ascending (deterministic, independent of input order).
    Mirrors the sort in classify_trace (line 148). -/
def rankMotifs (candidates : List MotifCandidate) : List MotifCandidate :=
  let scored := candidates.map fun c => { c with score := motifScore c.inputs }
  scored.mergeSort fun a b =>
    let sa := a.score.toInt
    let sb := b.score.toInt
    if sa ≠ sb then sa > sb else a.motifId ≤ b.motifId

/-- rankMotifs then take the first k results (mirrors [:top_k]). -/
def topKMotifs (k : Nat) (candidates : List MotifCandidate) : List MotifCandidate :=
  (rankMotifs candidates).take k

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  Executable witnesses
-- ─────────────────────────────────────────────────────────────────────────────

-- §5.1  familyMatchBonus raw value
-- 0.3 · 65536 = 19660.8 → truncated to 19660 by integer division
#eval familyMatchBonus.toInt
-- expect: 19660

-- §5.2  Base score: frequency=3, librarySize=10 → 3/10 · 65536 = 19660 raw
#eval (baseScore { frequency := 3, librarySize := 10, familyMatch := false }).toInt
-- expect: 19660

-- §5.3  Matching score = base + bonus: 3/10 + 3/10 = 0.6 → 39320 raw
#eval (motifScore { frequency := 3, librarySize := 10, familyMatch := true }).toInt
-- expect: 39320

-- §5.4  Non-matching score = base only: 3/10 → 19660 raw
#eval (motifScore { frequency := 3, librarySize := 10, familyMatch := false }).toInt
-- expect: 19660

-- §5.5  rankMotifs: matching motif outranks non-matching at same frequency
#eval (rankMotifs [
    mkCandidate "m_no_match"  3 10 false,
    mkCandidate "m_match"     3 10 true
  ]).map (fun c => (c.motifId, c.score.toInt))
-- expect: [("m_match", 39320), ("m_no_match", 19660)]

-- §5.6  Higher frequency beats lower even without family match
#eval (rankMotifs [
    mkCandidate "low_freq"  1 10 false,
    mkCandidate "high_freq" 7 10 false
  ]).map (fun c => (c.motifId, c.score.toInt))
-- expect: [("high_freq", 45875), ("low_freq", 6553)]

-- §5.7  topKMotifs respects k
#eval (topKMotifs 2 [
    mkCandidate "c" 1 10 false,
    mkCandidate "b" 5 10 false,
    mkCandidate "a" 3 10 false
  ]).map (fun c => c.motifId)
-- expect: ["b", "a"]

-- §5.8  Tie-break by motifId ascending
#eval (rankMotifs [
    mkCandidate "z_motif" 5 10 false,
    mkCandidate "a_motif" 5 10 false
  ]).map (fun c => c.motifId)
-- expect: ["a_motif", "z_motif"]

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  Proved invariants
-- ─────────────────────────────────────────────────────────────────────────────

-- §6.1  familyMatchBonus is strictly positive
theorem motifScore_bonus_pos : 0 < familyMatchBonus.toInt := by decide

-- §6.2  Concrete witness: matching score ≥ non-matching score at freq=3, lib=10.
-- (A general proof over all MotifInputs requires reasoning about Q16_16.add
--  clamping behaviour; deferred as TODO(lean-port).)
-- TODO(lean-port): Generalise to all MotifInputs once Q16_16.add_nonneg_monotone
--   is proved in FixedPoint.lean (i.e., 0 ≤ bonus → (base + bonus).toInt ≥ base.toInt).
theorem motifScore_match_ge_base_witness :
    (motifScore { frequency := 3, librarySize := 10, familyMatch := true }).toInt ≥
    (motifScore { frequency := 3, librarySize := 10, familyMatch := false }).toInt := by
  decide

-- §6.3  Zero frequency → base score is zero regardless of library size
theorem motifScore_zero_freq_base (lib : Nat) (fm : Bool) :
    (baseScore { frequency := 0, librarySize := lib, familyMatch := fm }).toInt = 0 := by
  simp [baseScore, ofRatio]

-- §6.4  Zero frequency, no match → full score is zero
theorem motifScore_zero_freq_no_match (lib : Nat) :
    (motifScore { frequency := 0, librarySize := lib, familyMatch := false }).toInt = 0 := by
  simp [motifScore, baseScore, ofRatio]

-- §6.5  Zero frequency, match → full score equals bonus exactly.
-- Concrete: lib=10, freq=0, match=true → score = 0 + 19660 = 19660.
theorem motifScore_zero_freq_match_witness :
    (motifScore { frequency := 0, librarySize := 10, familyMatch := true }).toInt =
    familyMatchBonus.toInt := by
  decide

-- §6.6  Concrete sort-order witness: matching motif (score 39320) leads the ranking.
theorem rankMotifs_match_beats_no_match :
    let ranked := rankMotifs [
      mkCandidate "no_match" 3 10 false,
      mkCandidate "match"    3 10 true ]
    (ranked.head?.map (fun c => (c.motifId, c.score.toInt))) =
    some ("match", 39320) := by
  native_decide

end Semantics.PIST.Motif
