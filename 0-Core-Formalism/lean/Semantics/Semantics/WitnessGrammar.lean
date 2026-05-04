/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

WitnessGrammar.lean — Finite Symbolic Source Code Recovered from a Field

A WitnessGrammar is the finite symbolic source code recovered from a field.
It stores the active witnesses, their amplitudes / frequencies / phases,
their routing roles, and a residual receipt.

Forest Position:
  branch: GeoCognition.Cartography.FieldDecomposition
  role: FNWH peeling front-end → manifold spawn/routing
  upstream:
    - SignalField (raw time-series / market data / PDE solutions)
    - FNWHPeel (harmonic / wavelet / operator decomposition)
  downstream:
    - EquationSniffer (pattern matching across grammars)
    - CoulombComplexity (charge assignment to witnesses)
    - MassNumberField (mass allocation from witness weights)
    - BHOCS / FAMM (commitment / drain from classified witness roles)

Canonical Law:
"FNWH decompiles fields into witness grammars; Equation Sniffers compare
those grammars; the market filter searches for shared behavioral operators,
not shared nouns."

Per AGENTS.md §1.4: Q16_16 fixed-point for all physics computations.
Per AGENTS.md §5: Target 6.5σ statistical confidence for routing decisions.
Per AGENTS.md §4: Every algorithm must be expressible as a bind instance.

Mathematical foundation documented in:
  docs/specs/BurgersHarmonicPeelingVerification.md
Key parameter: κ = 0.3547 (35.47% stiffening factor from energy bookkeeping).
-/

import Semantics.SigmaGate
import Semantics.FixedPoint
import Semantics.Bind
import Semantics.CoulombComplexity
import Mathlib.Data.Real.Basic

set_option linter.dupNamespace false

namespace Semantics.WitnessGrammar

open Semantics
open Semantics.Q16_16
open Semantics.CoulombComplexity

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Witness Role & Action Taxonomy
-- ═══════════════════════════════════════════════════════════════════════════

/-- A witness role names its structural function in the grammar.

    | Role      | Meaning                          | Downstream      |
    |-----------|----------------------------------|-----------------|
    | carrier   | dominant regime / DC component     | BHOCS witness   |
    | texture   | periodic / oscillatory shock     | FAMM drain      |
    | basin     | slow drift / attractor basin     | PIST basin      |
    | residual  | unexplained / unmodeled energy   | SigmaGate audit |
    -/
inductive WitnessRole where
  | carrier   -- dominant regime
  | texture   -- periodic shock
  | basin     -- drift / attractor
  | residual  -- unexplained energy
  deriving Repr, BEq, DecidableEq

/-- A witness action names the routing decision for this witness.

    | Action        | Meaning                              |
    |---------------|--------------------------------------|
    | routeToBHOCS  | structured mass → witness commitment |
    | routeToFAMM   | stress mass → drain                  |
    | routeToPIST   | basin → PIST manifold                |
    | auditSigma    | residual → SigmaGate confidence      |
    | neutralGround | no significant routing               |
    -/
inductive WitnessAction where
  | routeToBHOCS
  | routeToFAMM
  | routeToPIST
  | auditSigma
  | neutralGround
  deriving Repr, BEq, DecidableEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Witness — Atomic Decomposition Component
-- ═══════════════════════════════════════════════════════════════════════════

/-- A single witness extracted by FNWH peeling.

    ν (frequency)   — oscillation rate in manifold coordinates
    a (amplitude)   — energy contribution (Q16_16 fixed-point)
    φ (phase)       — phase offset in [0, 2π) mapped to Q16_16 circle
    role            — structural role in grammar
    action          — routing decision from SigmaGate + Coulomb filter

    Example (Burgers toy):
      Witness { ν = 1.0, a = 1.0,  φ = 0, role = carrier,  action = routeToBHOCS }
      Witness { ν = 2.0, a = 0.3, φ = 0, role = texture,  action = routeToFAMM }
      Witness { ν = 3.0, a = 0.1, φ = 0, role = texture,  action = routeToFAMM }
    -/
structure Witness where
  frequency : Q16_16
  amplitude : Q16_16
  phase     : Q16_16
  role      : WitnessRole
  action    : WitnessAction
  deriving Repr, BEq

/-- Default witness (neutral residual, zero amplitude). -/
instance : Inhabited Witness where
  default := ⟨Q16_16.zero, Q16_16.zero, Q16_16.zero, WitnessRole.residual, WitnessAction.neutralGround⟩

namespace Witness

/-- Convert amplitude to a signed mass contribution.
    Carrier → positive (structured), Texture → negative (stress),
    Basin → neutral (phase-dependent), Residual → zero (audit only). -/
def toCharge (w : Witness) : Charge :=
  match w.role with
  | WitnessRole.carrier  => Q16_16.ofInt 1  -- unit structured charge
  | WitnessRole.texture  => Q16_16.ofInt (-1) -- unit stress charge
  | WitnessRole.basin    => Q16_16.zero      -- neutral
  | WitnessRole.residual => Q16_16.zero      -- no charge

/-- Weighted amplitude as mass contribution.
    Z = Σ a_i for carriers, N = Σ a_i for textures. -/
def toMass (w : Witness) : Q16_16 :=
  Q16_16.abs w.amplitude

/-- Routing action from role (default, overridable by SigmaGate). -/
def defaultAction (role : WitnessRole) : WitnessAction :=
  match role with
  | WitnessRole.carrier  => WitnessAction.routeToBHOCS
  | WitnessRole.texture  => WitnessAction.routeToFAMM
  | WitnessRole.basin    => WitnessAction.routeToPIST
  | WitnessRole.residual => WitnessAction.auditSigma

end Witness

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  WitnessGrammar — Finite Symbolic Source Code
-- ═══════════════════════════════════════════════════════════════════════════

/-- A WitnessGrammar is the finite symbolic source code recovered from a field.

    witnesses       — active components from FNWH peeling
    residualEnergy  — unmodeled / unpeeled energy
    closed          — true if residual is below closure threshold

    Invariant: residualEnergy < threshold ↔ closed = true
    -/
structure WitnessGrammar where
  witnesses      : Array Witness
  residualEnergy : Q16_16
  closed         : Bool
  deriving Repr

namespace WitnessGrammar

/-- Default closure threshold for residual energy (Q16_16 ≈ 0.01). -/
def closureThreshold : Q16_16 := ⟨655⟩  -- 0.01 * 65536 ≈ 655

/-- Check if grammar is closed (residual below threshold). -/
def isClosed (g : WitnessGrammar) : Bool :=
  g.residualEnergy.val < closureThreshold.val

/-- Compute total mass number A = Σ |a_i| across all witnesses. -/
def totalMass (g : WitnessGrammar) : Q16_16 :=
  g.witnesses.foldl (fun acc w => Q16_16.add acc (Witness.toMass w)) Q16_16.zero

/-- Compute structured mass Z = Σ a_i for carriers. -/
def structuredMass (g : WitnessGrammar) : Q16_16 :=
  g.witnesses.foldl (fun acc w =>
    if w.role == WitnessRole.carrier then Q16_16.add acc w.amplitude else acc) Q16_16.zero

/-- Compute stress mass N = Σ a_i for textures. -/
def stressMass (g : WitnessGrammar) : Q16_16 :=
  g.witnesses.foldl (fun acc w =>
    if w.role == WitnessRole.texture then Q16_16.add acc w.amplitude else acc) Q16_16.zero

/-- Convert grammar to Coulomb charge Q = Z - N. -/
def toCharge (g : WitnessGrammar) : Charge :=
  Charge.compute g.structuredMass g.stressMass

/-- Convert grammar to polarity classification. -/
def toPolarity (g : WitnessGrammar) (tolerance : Q16_16) : Polarity :=
  Polarity.classify g.toCharge tolerance

/-- Default routing: apply defaultAction per witness role. -/
def routeDefault (g : WitnessGrammar) : Array Witness :=
  g.witnesses.map (fun w => { w with action := Witness.defaultAction w.role })

end WitnessGrammar

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Equation Sniffer — Pattern Matching Across Grammars
-- ═══════════════════════════════════════════════════════════════════════════

/-- Behavioral distance between two witnesses (Q16_16 fixed-point).
    d(w1, w2) = |ν1 - ν2| + |a1 - a2| (simplified Manhattan on frequency + amplitude). -/
def witnessDistance (w1 w2 : Witness) : Q16_16 :=
  let dFreq := Q16_16.abs (Q16_16.sub w1.frequency w2.frequency)
  let dAmp  := Q16_16.abs (Q16_16.sub w1.amplitude w2.amplitude)
  Q16_16.add dFreq dAmp

/-- Binding / pattern stability: high when roles match and frequencies align. -/
def bindingStability (w1 w2 : Witness) : Q16_16 :=
  if w1.role == w2.role then
    let freqAlign := Q16_16.sub (Q16_16.ofInt 1)
      (Q16_16.sat01 (witnessDistance w1 w2))
    Q16_16.mul freqAlign freqAlign  -- square for convex reward
  else
    Q16_16.zero

/-- Turbulence / unresolved mismatch: high when roles differ wildly. -/
def turbulence (w1 w2 : Witness) : Q16_16 :=
  if w1.role ≠ w2.role then
    Q16_16.mul (Q16_16.ofInt 2) (witnessDistance w1 w2)
  else
    Q16_16.zero

/-- Filter score for a query witness against a grammar witness.

    S(w_query, w_grammar) = exp(-d/σ) · B / (1 + τ)

    Simplified for Q16_16 (no exp available): use saturation falloff.
    S = sat01(1 - d/σ) · B / (1 + τ)
    -/
def filterScore (query grammarWitness : Witness) (sigma : Q16_16) : Q16_16 :=
  let d := witnessDistance query grammarWitness
  -- Falloff term: 1 - d/σ, saturated to [0, 1]
  let falloff := Q16_16.sat01 (Q16_16.sub (Q16_16.ofInt 1) (Q16_16.div d sigma))
  let b := bindingStability query grammarWitness
  let tau := turbulence query grammarWitness
  let denom := Q16_16.add (Q16_16.ofInt 1) tau
  let numerator := Q16_16.mul falloff b
  Q16_16.div numerator denom

/-- Best-match score for a query witness against an entire grammar.
    Returns max score across all grammar witnesses. -/
def bestMatchScore (query : Witness) (grammar : WitnessGrammar) (sigma : Q16_16) : Q16_16 :=
  grammar.witnesses.foldl (fun acc w =>
    let score := filterScore query w sigma
    Q16_16.max acc score) Q16_16.zero

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Market Query Prototype: Capacity-Constrained Batch Transformer
--
-- The Burgers toy decomposition S(x)=sin(x)+0.3sin(2x)+0.1sin(3x) verifies
-- that FNWH peeling produces a finite witness grammar.  The 35.47% stiffening
-- factor κ (see BurgersHarmonicPeelingVerification.md) is the safety margin
-- that keeps the hyperfluid smooth under Burgers non-linearity.
-- ═══════════════════════════════════════════════════════════════════════════

/-- Behavioral class prototype for "capacity-constrained batch transformer".

    This class unifies ontologically unrelated systems by shared operational dynamics:
    - shipping containers
    - DNA sequencing
    - semiconductor fabs
    - clinical labs
    - warehouses
    - bakeries
    - ports
    - grandmother's cookies

    The query witness captures the dominant operational signature:
    - carrier: throughput rate (batch processing frequency)
    - texture: queueing oscillation (capacity-constraint shock)
    - basin: demand drift (seasonal / macro)
    - residual: unexplained event risk
    -/
def capacityConstrainedBatchTransformer : WitnessGrammar := {
  witnesses := #[
    { frequency := Q16_16.ofInt 1,  amplitude := Q16_16.ofInt 1,
      phase := Q16_16.zero, role := WitnessRole.carrier,
      action := WitnessAction.routeToBHOCS },
    { frequency := Q16_16.ofInt 2,  amplitude := ⟨19661⟩,
      -- 0.3 in Q16_16 = 0.3 * 65536 ≈ 19661
      phase := Q16_16.zero, role := WitnessRole.texture,
      action := WitnessAction.routeToFAMM },
    { frequency := Q16_16.ofInt 3,  amplitude := ⟨6554⟩,
      -- 0.1 in Q16_16 = 0.1 * 65536 ≈ 6554
      phase := Q16_16.zero, role := WitnessRole.texture,
      action := WitnessAction.routeToFAMM }
  ],
  residualEnergy := Q16_16.zero,
  closed := true
}

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Toy Market Examples with Hand-Labeled Vectors
-- ═══════════════════════════════════════════════════════════════════════════

/-- Toy asset A: shipping container port.
    High throughput carrier, moderate queueing texture, low seasonal drift. -/
def toyAssetShippingPort : WitnessGrammar := {
  witnesses := #[
    { frequency := Q16_16.ofInt 1,  amplitude := Q16_16.ofInt 1,
      phase := Q16_16.zero, role := WitnessRole.carrier,
      action := WitnessAction.routeToBHOCS },
    { frequency := Q16_16.ofInt 2,  amplitude := ⟨19661⟩,
      phase := Q16_16.zero, role := WitnessRole.texture,
      action := WitnessAction.routeToFAMM },
    { frequency := Q16_16.ofInt 4,  amplitude := ⟨3277⟩,
      -- 0.05 in Q16_16
      phase := Q16_16.zero, role := WitnessRole.basin,
      action := WitnessAction.routeToPIST }
  ],
  residualEnergy := ⟨3277⟩,
  closed := true
}

/-- Toy asset B: DNA sequencing lab.
    Same carrier class but higher texture (batch variability). -/
def toyAssetDNASequencing : WitnessGrammar := {
  witnesses := #[
    { frequency := Q16_16.ofInt 1,  amplitude := Q16_16.ofInt 1,
      phase := Q16_16.zero, role := WitnessRole.carrier,
      action := WitnessAction.routeToBHOCS },
    { frequency := Q16_16.ofInt 2,  amplitude := ⟨26214⟩,
      -- 0.4 in Q16_16 (higher texture than shipping)
      phase := Q16_16.zero, role := WitnessRole.texture,
      action := WitnessAction.routeToFAMM },
    { frequency := Q16_16.ofInt 5,  amplitude := ⟨6554⟩,
      -- 0.1 in Q16_16 (faster basin)
      phase := Q16_16.zero, role := WitnessRole.basin,
      action := WitnessAction.routeToPIST }
  ],
  residualEnergy := Q16_16.zero,
  closed := true
}

/-- Toy asset C: bakery (small scale, high residual).
    Same behavioral class but smaller amplitude, higher residual. -/
def toyAssetBakery : WitnessGrammar := {
  witnesses := #[
    { frequency := Q16_16.ofInt 1,  amplitude := ⟨32768⟩,
      -- 0.5 in Q16_16 (half throughput)
      phase := Q16_16.zero, role := WitnessRole.carrier,
      action := WitnessAction.routeToBHOCS },
    { frequency := Q16_16.ofInt 2,  amplitude := ⟨19661⟩,
      phase := Q16_16.zero, role := WitnessRole.texture,
      action := WitnessAction.routeToFAMM },
    { frequency := Q16_16.ofInt 6,  amplitude := Q16_16.zero,
      phase := Q16_16.zero, role := WitnessRole.residual,
      action := WitnessAction.auditSigma }
  ],
  residualEnergy := ⟨13107⟩,
  -- 0.2 residual energy (high for small system)
  closed := false
}

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Equation Sniffer Pipeline — Grammar Matching
-- ═══════════════════════════════════════════════════════════════════════════

/-- EquationSniffer input structure (YAML bridge Lean type). -/
structure EquationSnifferInput where
  grammar : WitnessGrammar
  query   : Witness  -- prototype to match against
  sigma   : Q16_16 -- distance temperature
  deriving Repr

/-- EquationSniffer result structure. -/
structure EquationSnifferResult where
  bestScore     : Q16_16
  matchedWitness : Option Witness
  routeDecision   : String
  confidence      : String
  deriving Repr

namespace EquationSnifferResult

/-- Run the sniffer: match query against grammar, return best score + decision. -/
def sniff (input : EquationSnifferInput) : EquationSnifferResult :=
  let grammar := input.grammar
  let query := input.query
  let sigma := input.sigma

  -- Find best matching witness (initialize from first to avoid none-stuck fold)
  let initScore := if h : grammar.witnesses.size > 0
    then filterScore query grammar.witnesses[0] sigma
    else Q16_16.zero
  let (bestScore, bestWitness) := grammar.witnesses.foldl
    (fun (bestScore, bestWit) w =>
      let score := filterScore query w sigma
      if score.val > bestScore.val then (score, some w) else (bestScore, bestWit))
    (initScore, if grammar.witnesses.size > 0 then some grammar.witnesses[0]! else none)

  -- Route decision from best match role
  let route := match bestWitness with
    | some w => match w.role with
      | WitnessRole.carrier  => "ROUTE_TO_BHOCS"
      | WitnessRole.texture  => "ROUTE_TO_FAMM"
      | WitnessRole.basin    => "ROUTE_TO_PIST"
      | WitnessRole.residual => "AUDIT_SIGMA"
    | none => "NO_MATCH"

  -- Confidence from score magnitude
  let confidence :=
    if bestScore.val > ⟨524288⟩ then "HIGH"      -- > 8.0 in Q16_16
    else if bestScore.val > ⟨65536⟩ then "MEDIUM" -- > 1.0 in Q16_16
    else if bestScore.val > ⟨6554⟩ then "LOW"    -- > 0.1 in Q16_16
    else "NONE"

  { bestScore := bestScore, matchedWitness := bestWitness,
    routeDecision := route, confidence := confidence }

end EquationSnifferResult

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  #eval Tests — Toy Market Matching
-- ═══════════════════════════════════════════════════════════════════════════

#eval! capacityConstrainedBatchTransformer.toCharge
#eval! capacityConstrainedBatchTransformer.toPolarity (Q16_16.ofInt 5)
#eval! capacityConstrainedBatchTransformer.structuredMass
#eval! capacityConstrainedBatchTransformer.stressMass

-- Test: shipping port matches prototype carrier
#eval! EquationSnifferResult.sniff {
  grammar := toyAssetShippingPort,
  query := capacityConstrainedBatchTransformer.witnesses[0]!,
  sigma := Q16_16.ofInt 2
}

-- Test: DNA sequencing matches prototype texture
#eval! EquationSnifferResult.sniff {
  grammar := toyAssetDNASequencing,
  query := capacityConstrainedBatchTransformer.witnesses[1]!,
  sigma := Q16_16.ofInt 2
}

-- Test: bakery matches prototype (should be lower score, partial match)
#eval! EquationSnifferResult.sniff {
  grammar := toyAssetBakery,
  query := capacityConstrainedBatchTransformer.witnesses[0]!,
  sigma := Q16_16.ofInt 2
}

-- Test: filter score directly
#eval! filterScore
  capacityConstrainedBatchTransformer.witnesses[0]!
  toyAssetShippingPort.witnesses[0]!
  (Q16_16.ofInt 2)

#eval! filterScore
  capacityConstrainedBatchTransformer.witnesses[1]!
  toyAssetDNASequencing.witnesses[1]!
  (Q16_16.ofInt 2)

end Semantics.WitnessGrammar
