/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ASCIIArtCompetition.lean — ASCII Art Competition Scoring

Replaces infra/ascii_art_competition.py scoring logic with a formal Lean module.
Defines ASCII art competition scoring algorithms and evaluation metrics.

Per AGENTS.md:
  - Q16_16 for scoring (§1.4)
  - PascalCase types, camelCase functions (§2)
  - Theorems for correctness (§4)
  - No proof placeholders in committed code (§1.6)
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Std

namespace Semantics.ASCIIArtCompetition

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16_16 Fixed-Point Arithmetic
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16
  def zero : Q16_16 := ⟨0⟩
  def one : Q16_16 := ⟨65536⟩
  def ofFrac (num denom : Nat) : Q16_16 :=
    if denom = 0 then zero else ⟨(num * 65536) / denom⟩
  def toNat (q : Q16_16) : Nat := q.raw.toNat
end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Competition Type Enumeration
-- ═══════════════════════════════════════════════════════════════════════════

inductive CompetitionType where
  | generation : CompetitionType
  | styleClassification : CompetitionType
  | semanticMatching : CompetitionType
  | ranking : CompetitionType
deriving Repr, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Competition Entry Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure CompetitionEntry where
  agentId : String
  competitionType : CompetitionType
  asciiArtId : String
  score : Q16_16
  metrics : List (String × Q16_16)
  timestamp : Nat
  proposal : String
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Quality Metrics Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure QualityMetrics where
  aspectRatio : Q16_16
  lineConsistency : Q16_16
  characterDiversity : Q16_16
  overallQuality : Q16_16
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §4  ASCII Art Evaluation Functions
-- ═══════════════════════════════════════════════════════════════════════════

/-- Evaluate ASCII art generation quality metrics -/
def evaluateGenerationQuality (asciiArt : String) : QualityMetrics :=
  let lines := String.splitOn asciiArt "\n"
  let width :=
    if lines.isEmpty then 0
    else
      let lineLengths := lines.map String.length
      lineLengths.foldl Nat.max 0
  let height := lines.length
  
  -- Aspect ratio score: 1.0 - abs(1.0 - width/height) if height > 0
  let aspectRatioScore :=
    if height = 0 then Q16_16.zero
    else
      let ratio := (width * 65536) / height
      let deviation := if ratio ≥ 65536 then ratio - 65536 else 65536 - ratio
      Q16_16.ofFrac (65536 - deviation) 65536
  
  -- Line consistency: 1.0 if all lines have same length, 0.5 otherwise
  let lineLengths := lines.map String.length
  let lineConsistency :=
    if lineLengths.isEmpty then Q16_16.one
    else
      let allSame := lineLengths.all (· = lineLengths.head!)
      if allSame then Q16_16.one else Q16_16.ofFrac 1 2
  
  -- Character diversity: unique characters / 95 (printable ASCII)
  let uniqueChars := (String.toList asciiArt).eraseDups.length
  let characterDiversity := Q16_16.ofFrac uniqueChars 95
  
  -- Overall quality: average of three metrics
  let overallQuality :=
    let sum := aspectRatioScore.raw + lineConsistency.raw + characterDiversity.raw
    ⟨sum / 3⟩
  
  {
    aspectRatio := aspectRatioScore,
    lineConsistency := lineConsistency,
    characterDiversity := characterDiversity,
    overallQuality := overallQuality
  }

/-- Evaluate style classification accuracy -/
def evaluateStyleClassification (predictedStyle actualStyle : String) : Q16_16 :=
  if predictedStyle = actualStyle then Q16_16.one else Q16_16.zero

/-- Evaluate semantic similarity between two texts (Jaccard index) -/
def evaluateSemanticSimilarity (text1 text2 : String) : Q16_16 :=
  let set1 := (String.toList text1).eraseDups
  let set2 := (String.toList text2).eraseDups
  let intersection := (set1.filter (· ∈ set2)).length
  let union := (set1 ++ set2).eraseDups.length
  if union = 0 then Q16_16.zero else Q16_16.ofFrac intersection union

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Leaderboard Entry Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure LeaderboardEntry where
  agentId : String
  totalScore : Q16_16
  competitionsWon : Nat
  entriesCount : Nat
  lastUpdated : Nat
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- Style classification returns 1.0 for exact match -/
theorem styleClassificationExactMatch (style : String) :
    (evaluateStyleClassification style style).raw = 65536 := by
  simp [evaluateStyleClassification, Q16_16.one]

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Example Usage
-- ═══════════════════════════════════════════════════════════════════════════

#eval evaluateStyleClassification "block" "block"

#eval evaluateStyleClassification "block" "line"

#eval evaluateSemanticSimilarity "hello" "hello world"

#eval evaluateGenerationQuality "  /\\_/\\\n ( . .)\n  C(\" \")(\" \")"

end Semantics.ASCIIArtCompetition
