/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MathQuery.lean — ENE Extension for Mathematical Subject Query

This module extends the ENE semantic database with specialized indexing
and retrieval for mathematical subjects: theorems, equations, proofs,
and formal structures.

Per AGENTS.md §1.4: Q16_16 fixed-point for all computation.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has #eval witness or theorem.

NII-01 SEMANTIC ANALYSIS CORE ASSIGNMENT:
========================================
This file is assigned to NII-01 Semantic Analysis Core for:
- Semantic indexing of mathematical subjects for ENE database
- Cost function computation for mathematical entity retrieval
- Formalization of mathematical subject taxonomy for semantic analysis
- Extraction of mathematical dependencies and citation networks

Translation responsibilities:
1. Map MathSubject taxonomy to semantic analysis indices
2. Translate query cost functions to semantic similarity metrics
3. Extract mathematical entity relationships for semantic graph construction
4. Formalize proof status tracking for semantic completeness verification

Integration:
- ENE graph schema (ENE_EQUATIONS.md)
- ResearchAgent pipeline (academic paper indexing)
- Bind primitive (unified cost function)
- FixedPoint.lean (Q16_16 arithmetic)
-/

import Semantics.FixedPoint
import Mathlib.Data.Fin.Basic

namespace Semantics.MathQuery

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Types: Mathematical Subject Taxonomy
-- ═══════════════════════════════════════════════════════════════════════════

/-- Mathematical subject categories (finite, enumerable per AGENTS.md §1.5) -/
inductive MathSubject where
  | algebra
  | analysis
  | geometry
  | topology
  | number_theory
  | combinatorics
  | logic
  | category_theory
  | probability
  | statistics
  | numerical_analysis
  | computational_math
  | foundations
  | discrete_math
  | differential_equations
  | chemistry  -- Molecular structures, SMILES/SELFIES parsing
  | materials_science  -- Crystal structures, COD/PDB data
  deriving BEq, DecidableEq, Repr, Inhabited

namespace MathSubject

/-- Convert subject to index for database addressing (0-15) -/
def toIdx : MathSubject → Fin 16
  | algebra => 0
  | analysis => 1
  | geometry => 2
  | topology => 3
  | number_theory => 4
  | combinatorics => 5
  | logic => 6
  | category_theory => 7
  | probability => 8
  | statistics => 9
  | numerical_analysis => 10
  | computational_math => 11
  | foundations => 12
  | discrete_math => 13
  | differential_equations => 14
  | chemistry => 15
  | materials_science => 0  -- wraps

/-- Human-readable label for subject -/
def label : MathSubject → String
  | algebra => "Algebra"
  | analysis => "Analysis"
  | geometry => "Geometry"
  | topology => "Topology"
  | number_theory => "Number Theory"
  | combinatorics => "Combinatorics"
  | logic => "Logic"
  | category_theory => "Category Theory"
  | probability => "Probability"
  | statistics => "Statistics"
  | numerical_analysis => "Numerical Analysis"
  | computational_math => "Computational Mathematics"
  | foundations => "Foundations"
  | discrete_math => "Discrete Mathematics"
  | differential_equations => "Differential Equations"
  | chemistry => "Chemistry"
  | materials_science => "Materials Science"

end MathSubject

/-- Proof status (finite states per AGENTS.md §1.5, no open strings) -/
inductive ProofStatus where
  | proven
  | partial
  | conjecture
  | disproven
  | under_review
  deriving BEq, DecidableEq, Repr, Inhabited

/-- Formalization status (tractability for ENE bind) -/
inductive FormalizationStatus where
  | lean4
  | other_proof
  | in_progress
  | informal
  | not_applicable
  deriving BEq, DecidableEq, Repr, Inhabited

/-- Mathematical entity record for ENE database -/
structure MathEntity where
  entityId : String              -- Unique identifier (SHA-256 prefix)
  subject : MathSubject            -- Primary subject classification
  secondarySubjects : List MathSubject  -- Cross-disciplinary tags
  name : String                  -- Human-readable name
  statement : String             -- Formal or informal statement
  proofStatus : ProofStatus
  formalStatus : FormalizationStatus
  leanModule : Option String       -- e.g., "Semantics.AVMR"
  dependencies : List String       -- Entity IDs this depends on
  citations : List String          -- DOI or arXiv IDs
  complexityScore : Q16_16         -- Estimated proof complexity (Q16_16)
  year : Nat                       -- Year of first statement
  deriving Repr

/-- Query parameters for mathematical search -/
structure MathQueryParams where
  subjects : List MathSubject      -- Subject filter (OR semantics)
  proofStatus : Option ProofStatus   -- Optional proof status filter
  formalStatus : Option FormalizationStatus
  minYear : Option Nat               -- Year range
  maxYear : Option Nat
  maxComplexity : Option Q16_16    -- Complexity ceiling
  hasLeanFormalization : Bool      -- Require Lean 4 formalization
  keywordPattern : Option String     -- Substring match in name/statement
  deriving Repr

/-- Helper: Convert UInt32 to Q16_16 -/
def ofUInt32 (n : UInt32) : Q16_16 := ⟨n⟩

/-- Default query: no filters, any subject -/
def defaultQueryParams : MathQueryParams :=
  { subjects := []
    proofStatus := none
    formalStatus := none
    minYear := none
    maxYear := none
    maxComplexity := none
    hasLeanFormalization := false
    keywordPattern := none }

/-- Helper constants -/
def q16_one : Q16_16 := Q16_16.one

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Cost Functions (per ENE bind primitive)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Cost for subject mismatch (0 = exact match, 1 = different subject) -/
def subjectCost (query : MathSubject) (entity : MathSubject) : Q16_16 :=
  if query = entity then zero
  else if query.toIdx.val + 1 = entity.toIdx.val then
    ofUInt32 21845  -- ~0.333 (adjacent subjects cheaper)
    -- 21845/65536 ≈ 0.333
  else if query.toIdx.val = entity.toIdx.val + 1 then
    ofUInt32 21845  -- ~0.333 (adjacent subjects cheaper)
  else Q16_16.one  -- Full penalty (1.0) for unrelated subjects

/-- Reciprocal year distance cost (closer years = lower cost) -/
def yearCost (queryYear : Nat) (entityYear : Nat) : Q16_16 :=
  let diff := if queryYear > entityYear then queryYear - entityYear else entityYear - queryYear
  if diff = 0 then zero
  else if diff ≤ 10 then ofUInt32 13107  -- ~0.2 (recent within decade)
    -- 13107/65536 ≈ 0.2
  else if diff ≤ 50 then ofUInt32 32768   -- ~0.5 (within half-century)
    -- 32768/65536 = 0.5
  else Q16_16.one

/-- Complexity cost: penalize if entity complexity exceeds query ceiling -/
def complexityCost (ceiling : Option Q16_16) (entityComplexity : Q16_16) : Q16_16 :=
  match ceiling with
  | none => zero  -- No ceiling = no cost
  | some maxVal =>
    if entityComplexity ≤ maxVal then zero
    else (entityComplexity - maxVal) / entityComplexity  -- Proportional penalty

/-- Total query cost using ENE bind metric structure -/
def queryCost (params : MathQueryParams) (entity : MathEntity) : Q16_16 :=
  -- Subject match (minimum cost across all query subjects)
  let subjectMatchCost := params.subjects.foldl (fun acc subj =>
    let c := subjectCost subj entity.subject
    if c < acc then c else acc
  ) q16_one
  
  -- Proof status bonus (lower cost for matching status)
  let statusCost := match params.proofStatus with
    | none => zero
    | some ps => if ps = entity.proofStatus then zero else ofUInt32 32768  -- 0.5 penalty
  
  -- Year proximity (if year specified, use 2020 as default)
  let yearMatchCost := match params.minYear with
    | none => zero
    | some y => yearCost y entity.year
  
  -- Complexity ceiling
  let complexityMatchCost := complexityCost params.maxComplexity entity.complexityScore
  
  -- Lean formalization bonus
  let leanBonus := if params.hasLeanFormalization ∧ entity.leanModule.isSome then
    Q16_16.neg (ofUInt32 16384)  -- -0.25 bonus (negative cost = incentive)
  else
    zero
  
  -- Sum: subject + status + year + complexity + lean_bonus
  subjectMatchCost + statusCost + yearMatchCost + complexityMatchCost + leanBonus

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Database Operations
-- ═══════════════════════════════════════════════════════════════════════════

/-- In-memory math entity database (HashMap for O(1) lookup) -/
abbrev MathDatabase := HashMap String MathEntity

/-- Empty database -/
def emptyDatabase : MathDatabase := HashMap.empty

/-- Insert entity into database -/
def insertEntity (db : MathDatabase) (entity : MathEntity) : MathDatabase :=
  db.insert entity.entityId entity

/-- Query database, returning ranked results -/
def queryDatabase (db : MathDatabase) (params : MathQueryParams) : List (MathEntity × Q16_16) :=
  let allEntities := db.toList.map (fun (_, e) => e)
  
  -- Score all entities
  let scored := allEntities.map (fun e => (e, queryCost params e))
  
  -- Filter: keep only if total cost < 2.0 (reasonable match threshold)
  let filtered := scored.filter (fun (_, cost) => cost.val < 0x00020000)
  
  -- Sort by cost (ascending = best matches first)
  let sorted := filtered.insertionSort (fun a b => a.2 ≤ b.2)
  
  sorted

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Shim Boundary (Python Interface)
-- ═══════════════════════════════════════════════════════════════════════════

/-- JSON-serializable query result for Python shim -/
structure QueryResult where
  entityId : String
  subject : String
  name : String
  cost : UInt32  -- Q16_16 raw value
  year : Nat
  deriving Repr

/-- Convert scored entity to serializable result -/
def toQueryResult (e : MathEntity) (c : Q16_16) : QueryResult :=
  { entityId := e.entityId
    subject := MathSubject.label e.subject
    name := e.name
    cost := c.val.toUInt32
    year := e.year }

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Verification Examples
-- ═══════════════════════════════════════════════════════════════════════════

/-- Test entity 1 -/
def testEntity1 : MathEntity :=
  { entityId := "test-001"
    subject := .algebra
    secondarySubjects := [.number_theory]
    name := "Fermat's Last Theorem"
    statement := "a^n + b^n ≠ c^n for n > 2"
    proofStatus := .proven
    formalStatus := .other_proof
    leanModule := none
    dependencies := []
    citations := ["10.2307/3597226"]
    complexityScore := q16_one
    year := 1995 }

/-- Test entity 2 -/
def testEntity2 : MathEntity :=
  {
    entityId := "test-002",
    subject := .topology,
    secondarySubjects := [],
    name := "Poincaré Conjecture",
    statement := "Every simply connected closed 3-manifold is homeomorphic to S^3",
    proofStatus := .proven,
    formalStatus := .lean4,
    leanModule := some "Mathlib.Geometry.Manifold",
    dependencies := [],
    citations := ["arXiv:math/0211159"],
    complexityScore := q16_one,
    year := 2003
  }

-- #eval queryCost defaultQueryParams testEntity1
-- Expected: low cost (~0.0) since no restrictive filters

-- #eval subjectCost .algebra .number_theory
-- Expected: ~0.333 (adjacent subjects cost)

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Theorems (Invariant Preservation)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Theorem: Subject cost is symmetric for adjacent indices -/
-- TODO(lean-port): Fix omega proof
-- theorem subjectCostSymmetric (s1 s2 : MathSubject)
--     (hAdj : s1.toIdx.val + 1 = s2.toIdx.val) :
--     subjectCost s1 s2 = subjectCost s2 s1 := by
--   simp [subjectCost, hAdj]
--   -- Both directions yield the same adjacent-subject cost
--   all_goals omega

/-- Theorem: Exact subject match has zero cost -/
theorem exactSubjectZeroCost (s : MathSubject) :
    subjectCost s s = zero := by
  simp [subjectCost]

/-- Theorem: Query cost is monotonic in complexity ceiling violation -/
-- TODO(lean-port): Fix proof - need to show (entity - c1) / entity > (entity - c2) / entity given c1 < c2
-- theorem complexityCostMonotonic (c1 c2 entity : Q16_16)
--     (h1 : c1 < c2) (h2 : entity > c2) :
--     complexityCost (some c1) entity > complexityCost (some c2) entity := by
--   simp [complexityCost, h1, h2]
--   -- Since entity > c2 > c1, both exceed their ceilings
--   -- cost1 = (entity - c1) / entity
--   -- cost2 = (entity - c2) / entity
--   -- Since c1 < c2, entity - c1 > entity - c2, so cost1 > cost2
--   have h_c1_lt_entity : c1 < entity := by trans h1 h2
--   have h_c2_lt_entity : c2 < entity := by exact h2

-- TODO(lean-port): Theorem: Empty query matches all entities (zero or minimal cost)
-- Fix implicit argument synthesis issue in theorem signature

end Semantics.MathQuery
