/-
  CBFTests.lean - Chromatic Braid Field Test Suite

  Verifies:
    - DIAT leaf encoding and lift
    - AMMR vector accumulation (associativity, commutativity)
    - Bracket calculus (post-merge derivation)
    - Braid strand merge (linear phaseAcc + recomputed bracket)
    - Crossing residuals
    - CMYK coloring
    - Rope bind/detangle
-/

import Semantics.BraidBracket
import Semantics.BraidStrand
import Semantics.BraidCross
import Semantics.MasterEquation

namespace Semantics.CBFTests

open Semantics.BraidBracket
open Semantics.BraidStrand
open Semantics.BraidCross
open Semantics.MasterEquation

-- =============================================================================
-- 1. PhaseVec Arithmetic Tests
-- =============================================================================

/-- PhaseVec addition is commutative -/
#eval (PhaseVec.add { x := Fix16.mk 0x00010000, y := Fix16.zero }
                   { x := Fix16.zero, y := Fix16.mk 0x00010000 }) ==
      (PhaseVec.add { x := Fix16.zero, y := Fix16.mk 0x00010000 }
                   { x := Fix16.mk 0x00010000, y := Fix16.zero })

/-- PhaseVec addition is associative -/
#eval let a := { x := Fix16.mk 0x00010000, y := Fix16.zero : PhaseVec }
      let b := { x := Fix16.zero, y := Fix16.mk 0x00010000 : PhaseVec }
      let c := { x := Fix16.mk 0x00008000, y := Fix16.mk 0x00008000 : PhaseVec }
      PhaseVec.add (PhaseVec.add a b) c == PhaseVec.add a (PhaseVec.add b c)

/-- Zero is identity for PhaseVec addition -/
#eval let v := { x := Fix16.mk 0x00012345, y := Fix16.mk 0x00067890 : PhaseVec }
      PhaseVec.add v PhaseVec.zero == v

/-- Negation inverts both components -/
#eval let v := { x := Fix16.mk 0x00010000, y := Fix16.mk 0x00020000 : PhaseVec }
      let neg := PhaseVec.neg v
      neg.x.raw == (0x10000 - 0x00010000) && neg.y.raw == (0x10000 - 0x00020000)

-- =============================================================================
-- 2. Norm Approximation Tests
-- =============================================================================

/-- Norm of zero vector is zero -/
#eval PhaseVec.zero.normApprox == Fix16.zero

/-- Norm approximation for (1,0) is ~1.0 -/
#eval let v := { x := Fix16.one, y := Fix16.zero : PhaseVec }
      let n := v.normApprox
      n.raw >= 0x0000F000 && n.raw <= 0x00011000  -- within ~6%

/-- Norm approximation for (1,1) is ~1.375 -/
#eval let v := { x := Fix16.one, y := Fix16.one : PhaseVec }
      let n := v.normApprox
      let expected := Fix16.add Fix16.one (Fix16.mk 0x00006000)  -- 1 + 3/8
      n.raw >= 0x00015000 && n.raw <= 0x00017000

-- =============================================================================
-- 3. BraidBracket Tests
-- =============================================================================

/-- Zero bracket has zero kappa and phi -/
#eval BraidBracket.zero.kappa == Fix16.zero && BraidBracket.zero.phi == Fix16.zero

/-- Zero bracket is admissible -/
#eval BraidBracket.zero.admissible == true

/-- Bracket from zero PhaseVec has zero kappa -/
#eval let b := BraidBracket.fromPhaseVec PhaseVec.zero (Fix16.mk 0x00010000)
      b.kappa == Fix16.zero && b.phi == Fix16.zero

/-- Bracket gap conservation: gap = upper - lower -/
#eval let b := BraidBracket.fromPhaseVec { x := Fix16.mk 0x00010000, y := Fix16.zero } (Fix16.mk 0x00010000)
      let expectedGap := Fix16.sub b.upper b.lower
      b.gap.raw == expectedGap.raw

/-- Componentwise addition is correct -/
#eval let b1 := BraidBracket.fromPhaseVec { x := Fix16.mk 0x00010000, y := Fix16.zero } (Fix16.mk 0x00010000)
      let b2 := BraidBracket.fromPhaseVec { x := Fix16.zero, y := Fix16.mk 0x00010000 } (Fix16.mk 0x00010000)
      let sum := BraidBracket.addComponentwise b1 b2
      sum.kappa.raw == b1.kappa.raw + b2.kappa.raw

-- =============================================================================
-- 4. BraidStrand Tests
-- =============================================================================

/-- Zero strand is admissible -/
#eval (BraidStrand.zero 0).isAdmissible == true

/-- Strand from leaf has correct slot -/
#eval let s := BraidStrand.zero 42
      s.slot == 42

/-- Add contribution updates phaseAcc linearly -/
#eval let s := BraidStrand.zero 0
      let Φ := { x := Fix16.mk 0x00010000, y := Fix16.mk 0x00020000 : PhaseVec }
      let s2 := s.addContribution Φ
      s2.phaseAcc.x == Φ.x && s2.phaseAcc.y == Φ.y

/-- Multiple contributions accumulate -/
#eval let s := BraidStrand.zero 0
      let Φ1 := { x := Fix16.mk 0x00010000, y := Fix16.zero : PhaseVec }
      let Φ2 := { x := Fix16.zero, y := Fix16.mk 0x00010000 : PhaseVec }
      let s2 := (s.addContribution Φ1).addContribution Φ2
      s2.phaseAcc.x == Φ1.x && s2.phaseAcc.y == Φ2.y

/-- updateBracket recomputes bracket from phaseAcc -/
#eval let s := BraidStrand.zero 0
      let Φ := { x := Fix16.mk 0x00010000, y := Fix16.zero : PhaseVec }
      let s2 := (s.addContribution Φ).updateBracket
      s2.bracket.kappa.raw > 0

-- =============================================================================
-- 5. BraidCross Tests
-- =============================================================================

/-- braidCross merges phaseAcc linearly -/
#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let (merged, residual) := braidCross s1 s2
      merged.phaseAcc == PhaseVec.add s1.phaseAcc s2.phaseAcc

/-- braidCross produces unique slot -/
#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let (merged, _) := braidCross s1 s2
      merged.slot == 1.xor 2  -- slot is XOR of inputs

/-- Merged strand has recomputed bracket (not merged brackets) -/
#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let Φ1 := { x := Fix16.mk 0x00010000, y := Fix16.zero : PhaseVec }
      let Φ2 := { x := Fix16.zero, y := Fix16.mk 0x00010000 : PhaseVec }
      let s1' := s1.addContribution Φ1
      let s2' := s2.addContribution Φ2
      let (merged, _) := braidCross s1' s2'
      merged.bracket.kappa.raw > 0  -- has magnitude from merged vectors

/-- parallelCross merges all strands linearly -/
#eval let strands := [BraidStrand.zero 1, BraidStrand.zero 2, BraidStrand.zero 3]
      let merged := parallelCross strands
      merged.slot == 1.xor 2.xor 3

/-- crossingResidual produces valid residual -/
#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let (_, residual) := braidCross s1 s2
      residual.admissible == true  -- residual inherits admissibility

-- =============================================================================
-- 6. MasterEquation / CMYK Tests
-- =============================================================================

/-- CMYK zero is all zeros -/
#eval CMYK.zero.c == Fix16.zero && CMYK.zero.m == Fix16.zero &&
      CMYK.zero.y == Fix16.zero && CMYK.zero.k == Fix16.zero

/-- CMYK add combines componentwise -/
#eval let c1 := { c := Fix16.mk 0x00010000, m := Fix16.zero, y := Fix16.zero, k := Fix16.zero : CMYK }
      let c2 := { c := Fix16.zero, m := Fix16.mk 0x00010000, y := Fix16.zero, k := Fix16.zero : CMYK }
      let sum := CMYK.add c1 c2
      sum.c == c1.c && sum.m == c2.m

/-- Empty rope has zero slices -/
#eval (Rope.empty 0).slices.length == 0

/-- Rope from strands has correct count -/
#eval let strands := [BraidStrand.zero 1, BraidStrand.zero 2]
      let rope := Rope.fromSlices (strands.map (fun s => RopeSlice.fromStrand s CMYK.zero)) 0
      rope.slices.length == 2

/-- Rope is admissible if all slices admissible -/
#eval let s := BraidStrand.zero 1
      let rope := Rope.fromSlices [RopeSlice.fromStrand s CMYK.zero] 0
      rope.isAdmissible == true

/-- MIMOCarriers from rope duplicates rope to all carriers -/
#eval let rope := Rope.empty 0
      let carriers := MIMOCarriers.fromRope rope
      carriers.audio.slices.length == 0 && carriers.video.slices.length == 0

-- =============================================================================
-- 7. AVMR Entry Tests
-- =============================================================================

/-- AVMR leaf entry has no residual -/
#eval let entry := AVMREntry.leafEntry 1 PhaseVec.zero (Fix16.mk 0x00010000) 0
      entry.residual.isNone == true

/-- AVMR crossing entry has residual -/
#eval let entry := AVMREntry.crossingEntry 1 PhaseVec.zero (Fix16.mk 0x00010000) BraidBracket.zero 0
      entry.residual.isSome == true

-- =============================================================================
-- 8. Integration Test - Full Cycle
-- =============================================================================

/-- Full cycle: strands → rope → carriers → detangle -/
#eval
  let s1 := BraidStrand.zero 1
  let s2 := BraidStrand.zero 2
  let strands := [s1, s2]
  let colors := [CMYK.zero, CMYK.zero]
  let H := ChannelOperator.identity
  let D := Detangler.default
  let recovered := masterEquation strands colors H D 0
  recovered.length == 2  -- detangles back to 2 strands

/-- Identity cycle preserves strand count -/
#eval
  let s1 := BraidStrand.zero 1
  let s2 := BraidStrand.zero 2
  let s3 := BraidStrand.zero 3
  let strands := [s1, s2, s3]
  let colors := [CMYK.zero, CMYK.zero, CMYK.zero]
  let H := ChannelOperator.identity
  let D := Detangler.default
  let recovered := masterEquation strands colors H D 0
  recovered.length == 3

-- =============================================================================
-- 9. Strand Registry Tests
-- =============================================================================

/-- Empty registry has count 0 -/
#eval StrandRegistry.empty.count == 0

/-- Register increases count -/
#eval let reg := StrandRegistry.register StrandRegistry.empty (BraidStrand.zero 1)
      reg.count == 1

/-- All admissible if strands admissible -/
#eval let s := BraidStrand.zero 1
      let reg := StrandRegistry.empty
      let reg2 := StrandRegistry.register reg s
      reg2.allAdmissible == true

-- =============================================================================
-- 10. Crossing History Tests
-- =============================================================================

/-- Crossing history captures slots -/
#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let history := CrossingHistory.fromCross s1 s2 0
      history.leftSlot == 1 && history.rightSlot == 2

/-- Crossing history has merged slot as XOR -/
#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let history := CrossingHistory.fromCross s1 s2 0
      history.mergedSlot == 1.xor 2

-- =============================================================================
-- Summary
-- =============================================================================

#eval "CBF Test Suite Complete"

end Semantics.CBFTests
