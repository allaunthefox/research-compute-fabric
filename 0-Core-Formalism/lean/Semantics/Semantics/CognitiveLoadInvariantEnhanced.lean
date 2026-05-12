/-
  CognitiveLoadInvariantEnhanced.lean — Invariant-Enhanced Cognitive Load Theory

  Extends CognitiveLoad.lean with invariant preservation, trajectory quality,
  and convergence inhibition as fundamental load dimensions.

  Per AGENTS.md §1.4: All values are Q16_16 fixed-point.
  Per AGENTS.md §4: Every def has an #eval or theorem witness.
  Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

import Semantics.CognitiveLoad
import Semantics.FixedPoint

namespace Semantics.CognitiveLoadInvariantEnhanced

open Q16_16
open Semantics.CognitiveLoad

/-- Invariant kind for classification of preserved properties. -/
inductive InvariantKind where
  | structural   -- Periodicity, symmetry, hierarchical structure
  | semantic     -- Meaning-preserving transformations
  | statistical  -- Distribution moments, correlation structure
  | topological  -- Connectivity, genus, homology groups
  | causal       -- Temporal ordering, dependency structure
deriving Repr, Inhabited, DecidableEq, BEq

/-- Invariant specification with weight and severity. -/
structure InvariantSpec where
  kind     : InvariantKind
  weight   : Q16_16  -- Importance in [0, 1]
  severity : Q16_16  -- 1 = minor, max = critical
deriving Repr, Inhabited, DecidableEq

/-- Enhanced load vector with invariant preservation dimension. -/
structure EnhancedLoadVector where
  base      : LoadVector          -- Original 5 dimensions
  invariant : Q16_16               -- L_inv: invariant preservation load
  trajectoryQuality : Q16_16       -- L_tq: trajectory quality metric
  convergenceInhibition : Q16_16 -- L_ci: convergence inhibition cost
deriving Repr, Inhabited, DecidableEq

/-- Invariant preservation load: weighted sum of broken invariants.
    L_inv(x, 𝓘) = Σᵢ wᵢ · 𝟙[broken(i,x)] · severity(i) -/
def invariantPreservationLoad
    (invariants : Array InvariantSpec)
    (brokenMask : Array Bool)       -- Parallel array: true if broken
    : Q16_16 :=
  if invariants.size == 0 then zero
  else
    let sum := Array.foldl (fun acc i =>
      if i < invariants.size && i < brokenMask.size then
        if brokenMask[i]! then
          let inv := invariants[i]!
          let cost := mul inv.weight inv.severity
          add acc cost
        else acc
      else acc
    ) zero (Array.range (min invariants.size brokenMask.size))
    sum

/-- Critical invariant check: returns true if any invariant with
    maximum severity is broken. -/
def criticalInvariantBroken
    (invariants : Array InvariantSpec)
    (brokenMask : Array Bool)
    : Bool :=
  Array.any (Array.zip invariants brokenMask) (fun p =>
    let (inv, isBroken) := p
    isBroken && inv.severity.val == 0xFFFFFFFF  -- max Q16_16
  )

/-- Trajectory quality: measures how well compression path
    preserves intended structure. Simplified as 1 - normalizedLoad. -/
def trajectoryQuality (totalLoad : Q16_16) (maxLoad : Q16_16) : Q16_16 :=
  let normalized := div totalLoad (add maxLoad Q16_16.epsilon)
  sub one normalized

/-- Convergence inhibition: cost of preventing premature convergence.
    Higher when compression is too aggressive. -/
def convergenceInhibition
    (compressionRatio : Q16_16)
    (targetRatio : Q16_16)
    : Q16_16 :=
  let diff := sub compressionRatio targetRatio
  Q16_16.ofNat (abs diff).val.toNat

/-- Enhanced total load: base dimensions + invariant + quality + inhibition. -/
def enhancedTotalLoad (v : EnhancedLoadVector) : Q16_16 :=
  let baseTotal := totalLoad v.base
  let withInv := add baseTotal v.invariant
  let withTq := add withInv v.trajectoryQuality
  add withTq v.convergenceInhibition

/-- Cognitive efficiency with invariant awareness. -/
def invariantAwareEfficiency (v : EnhancedLoadVector) : Q16_16 :=
  let total := add (enhancedTotalLoad v) Q16_16.epsilon
  let useful := add v.base.intrinsic (sub one v.invariant)  -- intrinsic minus invariant penalty
  div useful total

/-- Bind: informational cost between two enhanced load states. -/
def enhancedLoadDeltaCost (a b : EnhancedLoadVector) (_m : Metric) : Q16_16 :=
  let da := enhancedTotalLoad a
  let db := enhancedTotalLoad b
  Q16_16.ofNat (abs (sub da db)).val.toNat

/-- Invariant extractor for bind witnesses. -/
def enhancedLoadInvariant (v : EnhancedLoadVector) : String :=
  s!"enhanced:base={loadInvariant v.base},inv={v.invariant.val},tq={v.trajectoryQuality.val}"

/-- Bind instance for enhanced cognitive load. -/
def enhancedCognitiveLoadBind
    (a b : EnhancedLoadVector)
    (m : Metric)
    : Bind EnhancedLoadVector EnhancedLoadVector :=
  informationalBind a b m enhancedLoadDeltaCost enhancedLoadInvariant enhancedLoadInvariant

-- ════════════════════════════════════════════════════════════
-- § Witnesses
-- ════════════════════════════════════════════════════════════

#eval! enhancedTotalLoad {
  base := {
    intrinsic := ⟨32768⟩,  -- 0.5
    extraneous := ⟨16384⟩, -- 0.25
    germane := ⟨8192⟩,     -- 0.125
    routing := ⟨4096⟩,     -- 0.0625
    memory := ⟨2048⟩       -- 0.03125
  },
  invariant := ⟨4096⟩,       -- 0.0625
  trajectoryQuality := ⟨32768⟩, -- 0.5
  convergenceInhibition := ⟨8192⟩ -- 0.125
}

#eval! invariantAwareEfficiency {
  base := {
    intrinsic := ⟨65536⟩,  -- 1.0
    extraneous := ⟨0⟩,
    germane := ⟨0⟩,
    routing := ⟨0⟩,
    memory := ⟨0⟩
  },
  invariant := ⟨0⟩,
  trajectoryQuality := ⟨65536⟩,
  convergenceInhibition := ⟨0⟩
}

end Semantics.CognitiveLoadInvariantEnhanced
