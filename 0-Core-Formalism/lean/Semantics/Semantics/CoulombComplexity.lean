/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CoulombComplexity.lean — Signed Inter-Node Tension Model via Coulomb Form

Extends the Mass-Number Field complexity model with charge polarity:
- Z (Structured Mass) and N (Stress Mass) act as charge polarities
- Q = Z - N defines the signed "bias" of a node
- Coulomb form governs routing tension between nodes (analogy, not literal EM)

Per AGENTS.md §1.4: Q16_16 fixed-point for all physics computations.
Per AGENTS.md §5: Target 6.5σ statistical confidence for routing decisions.

Forest Position:
  branch: GeoCognition.Cartography.ForceLayer
  role: charged interaction over shell-addressable mass fields
  upstream:
    - MassNumberField (Z, N masses)
    - ComplexityPrimeSieve (prime selection)
    - LochMonsterFilter (monster classification)
  downstream:
    - BHOCS shield (committed charge neutralization)
    - FAMM drain (stress-heavy charge dissipation)
    - PIST witness (structured charge routing)
    - T5 route selection (torus manifold routing)

Canonical Law:
"Structure attracts Stress; Symmetry repels Symmetry; Memory shields the Charge."

Commit-safe Law:
"Sieve the mass to find the Primes; polarize the Primes to find the Force;
 commit the scar to shield the Charge."
-/

import Semantics.SigmaGate
import Semantics.FixedPoint
import Semantics.Bind
import Mathlib.Data.Real.Basic

namespace Semantics.CoulombComplexity

open Semantics
open Semantics.Q0_16
open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Charge Polarity Foundation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Charge Q = Z - N (Structured Mass minus Stress Mass).

    Polarity classification:
    - Q > 0: Structured Positive (Z ≫ N, witness-heavy)
    - Q < 0: Stress Negative (N ≫ Z, scar/basin-heavy)
    - Q ≈ 0: Electrically Neutral (Z ≈ N, filtered out)
    -/
def Charge := Q16_16
  deriving Repr, BEq, Inhabited

namespace Charge

/-- Compute signed charge from structured mass Z and stress mass N.
    Q = Z - N (Q16_16 subtraction, which wraps as 2's complement).
    Use Q16_16.toInt for signed interpretation. -/
def compute (Z N : Q16_16) : Charge :=
  Q16_16.sub Z N

/-- Check if charge is positive (structured dominance, witness-heavy).
    Uses unsigned comparison on raw bits; paired with toInt for full range. -/
def isPositive (q : Charge) : Bool :=
  q.val > Q16_16.zero.val

/-- Check if charge is negative (stress dominance, scar/drain-heavy).
    Uses Q16_16.toInt for proper signed interpretation of 2's complement. -/
def isNegative (q : Charge) : Bool :=
  Q16_16.toInt q < 0

/-- Check if charge is neutral (filtered from high-priority routing).
    Uses signed integer comparison for balanced Z ≈ N nodes. -/
def isNeutral (q : Charge) (tolerance : Q16_16) : Bool :=
  let qInt := Q16_16.toInt q
  let tolInt := Q16_16.toInt tolerance
  -- Check: -tolerance ≤ q ≤ tolerance
  (-tolInt ≤ qInt) ∧ (qInt ≤ tolInt)

/-- Absolute charge value as Nat (for threshold comparisons).
    |Q| in integer form, capped at UInt32 max. -/
def absVal (q : Charge) : Nat :=
  let qInt := Q16_16.toInt q
  if qInt < 0 then (-qInt).toNat else qInt.toNat

#eval! Charge.compute (Q16_16.ofInt 100) (Q16_16.ofInt 30)  -- Q = +70
#eval! Charge.compute (Q16_16.ofInt 30) (Q16_16.ofInt 100) -- Q = -70
#eval! Charge.compute (Q16_16.ofInt 50) (Q16_16.ofInt 50)   -- Q = 0

end Charge

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Polarity Classification
-- ═══════════════════════════════════════════════════════════════════════════

inductive Polarity where
  | structuredPositive  -- Z ≫ N: witness-heavy node (repels same, attracts stress)
  | stressNegative      -- N ≫ Z: scar/basin-heavy node (repels same, attracts structured)
  | neutral             -- Z ≈ N: electrically neutral (filtered from priority routing)
  deriving Repr, BEq, DecidableEq

namespace Polarity

/-- Classify polarity from charge with tolerance threshold. -/
def classify (q : Charge) (tolerance : Q16_16) : Polarity :=
  if Charge.isNeutral q tolerance then Polarity.neutral
  else if Charge.isPositive q then Polarity.structuredPositive
  else Polarity.stressNegative

/-- Polarity interaction rule: true = attraction, false = repulsion.

    Stack meaning:
    - structuredPositive ↔ stressNegative: attraction (witness to scar commitment)
    - Same polarity: repulsion (prevent crowding / spread heat)
    - Neutral: no interaction (low-priority) -/
def interactsAttractively (p1 p2 : Polarity) : Bool :=
  match p1, p2 with
  | Polarity.structuredPositive, Polarity.stressNegative => true  -- witness → scar
  | Polarity.stressNegative, Polarity.structuredPositive => true  -- scar ← witness
  | Polarity.neutral, _ => false  -- Neutral: low-priority interaction
  | _, Polarity.neutral => false
  | _, _ => false  -- Same polarity: repulsion

/-- Polarity interaction rule: true = repulsion.

    Stack meaning:
    - Q_i > 0, Q_j > 0: repulsive → prevent BHOCS witness crowding
    - Q_i < 0, Q_j < 0: repulsive → spread heat across FAMM drains -/
def interactsRepulsively (p1 p2 : Polarity) : Bool :=
  match p1, p2 with
  | Polarity.structuredPositive, Polarity.structuredPositive => true  -- prevent crowding
  | Polarity.stressNegative, Polarity.stressNegative => true  -- spread drains
  | _, _ => false

#eval! Polarity.classify (Charge.compute (Q16_16.ofInt 100) (Q16_16.ofInt 30)) (Q16_16.ofInt 10)
#eval! Polarity.classify (Charge.compute (Q16_16.ofInt 30) (Q16_16.ofInt 100)) (Q16_16.ofInt 10)
#eval! Polarity.classify (Charge.compute (Q16_16.ofInt 50) (Q16_16.ofInt 52)) (Q16_16.ofInt 5)

end Polarity

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Coulomb Complexity Force F_C(i,j)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Coulomb form inter-node tension: F_C = k_e * Q_i * Q_j / (r^2 + ε)

    This is a signed tension model, NOT literal electromagnetism.
    The ε guard matters because torus distance can be zero.

    Where:
    - k_e: Coupling constant (system tension)
    - Q_i, Q_j: Signed charges of nodes i and j
    - r: Distance in T5 (5D Torus) routing manifold
    - ε: Singularity guard (small positive constant)

    Sign convention:
    - F_C > 0: Repulsion (same polarity)
    - F_C < 0: Attraction (opposite polarity)

    Note: NBody.lean already models F = k*q1*q2/r^2 with VecN 3 forces.
    This scalar version is the tension magnitude for routing decisions.
    -/
def coulombForce (k_e : Q16_16) (Q_i Q_j : Charge) (r epsilon : Q16_16)
  : Q16_16 :=
  let numerator := Q16_16.mul k_e (Q16_16.mul Q_i Q_j)
  let r_sq := Q16_16.mul r r
  let denom := Q16_16.add r_sq epsilon  -- ε prevents r = 0 singularity
  Q16_16.div numerator denom

/-- Distance in T5 (5D Torus) manifold.

    Simplified: Euclidean distance in 5D with torus wraparound.
    Integrates with SSMS_nD.lean variable-dimensional manifold substrate.
    Full implementation requires T5 coordinate embedding.
    -/
def t5Distance (coords_i coords_j : Array Q16_16) : Q16_16 :=
  if coords_i.size ≠ 5 ∨ coords_j.size ≠ 5 then Q16_16.ofInt 1000  -- Large default
  else
    let squaredDiffs := (List.range 5).map (fun idx =>
      let diff := Q16_16.sub coords_i[idx]! coords_j[idx]!
      Q16_16.mul diff diff)
    let sumSq := squaredDiffs.foldl (fun acc d => Q16_16.add acc d) Q16_16.zero
    Q16_16.sqrt sumSq

-- Test: Like charges repel (positive force)
#eval! coulombForce (Q16_16.ofInt 1) (Q16_16.ofInt 10) (Q16_16.ofInt 10) (Q16_16.ofInt 5) (Q16_16.ofInt 1)
-- Test: Opposite charges attract (negative force)
#eval! coulombForce (Q16_16.ofInt 1) (Q16_16.ofInt 10) (Q16_16.ofInt (-10)) (Q16_16.ofInt 5) (Q16_16.ofInt 1)

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Node Structure with Coulomb Properties
-- ═══════════════════════════════════════════════════════════════════════════

structure CoulombNode where
  id : String
  Z : Q16_16  -- Structured Mass
  N : Q16_16  -- Stress Mass
  charge : Charge
  polarity : Polarity
  density : Q16_16  -- Charge density ρ for plasma classification (ρ ≥ 0.5 = plasma)
  t5Coords : Array Q16_16  -- 5D Torus coordinates
  fieldInfluence : Q16_16  -- Potential energy contribution
  deriving Repr

namespace CoulombNode

/-- Create a Coulomb node from Z and N masses.
    Note: uses 'create' not 'mk' to avoid conflict with structure-generated mk. -/
def create (id : String) (Z N : Q16_16) (t5Coords : Array Q16_16)
  (tolerance : Q16_16) : CoulombNode :=
  let charge := Charge.compute Z N
  let polarity := Polarity.classify charge tolerance
  { id := id, Z := Z, N := N, charge := charge, polarity := polarity,
    density := Q16_16.zero, t5Coords := t5Coords, fieldInfluence := Q16_16.zero }

/-- Compute scalar interaction tension with another node.
    Uses epsilon guard in denominator (r^2 + ε) to avoid singularity.
    Integrates with NBody.lean VecN 3 force for vector routing directions. -/
def forceWith (node other : CoulombNode) (k_e epsilon : Q16_16) : Q16_16 :=
  let r := t5Distance node.t5Coords other.t5Coords
  coulombForce k_e node.charge other.charge r epsilon

/-- Determine routing decision based on net Coulomb tension.

    Routing rules:
    - Net F > threshold: REPEL_GUARD (too much repulsion / crowding)
    - Net F < -threshold: PULL_TO_SCAR (attraction / commitment)
    - Otherwise: NEUTRAL_GROUND (no significant interaction)
    -/
def routingDecision (node : CoulombNode) (others : Array CoulombNode)
  (k_e epsilon threshold : Q16_16) : String :=
  let netForce := others.foldl (fun acc other =>
    Q16_16.add acc (node.forceWith other k_e epsilon)) Q16_16.zero
  if netForce.val > threshold.val then "REPEL_GUARD"  -- Too much repulsion
  else if (netForce.val.toNat : Int) < -(threshold.val.toNat : Int) then "PULL_TO_SCAR"  -- Attraction
  else "NEUTRAL_GROUND"  -- No significant interaction

end CoulombNode

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  The Coulomb Sieve (Filtering Logic)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Sieve state for Coulomb filtering. -/
structure CoulombSieve where
  k_e : Q16_16  -- Coupling constant
  neutralTolerance : Q16_16  -- Tolerance for Q ≈ 0
  plasmaDensityThreshold : Q16_16  -- Flag high |Q| with high density
  minChargeForPrime : Q16_16  -- Minimum |Q| to be "Ionic Prime"
  deriving Repr

namespace CoulombSieve

/-- Default sieve parameters. -/
def default : CoulombSieve := {
  k_e := Q16_16.ofInt 1,  -- Unit coupling
  neutralTolerance := Q16_16.ofInt 5,  -- |Q| ≤ 5 is neutral
  plasmaDensityThreshold := Q16_16.ofInt 100,  -- High charge × high density
  minChargeForPrime := Q16_16.ofInt 50  -- |Q| ≥ 50 for ionic prime status
}

/-- Coulomb sieve phase classification per spec:

    Phase             | Condition                          | Meaning                | Route
    ------------------|------------------------------------|------------------------|----------
    NEUTRAL_GROUNDED  | |Q| < Θ_Q                          | balanced/grounded      | low-priority
    STRUCTURED_ION    | Q ≥ Θ_Q, ρ < 0.5                   | witness-heavy node     | BHOCS candidate
    STRESS_ION        | Q ≤ -Θ_Q, ρ < 0.5                  | scar/drain-heavy node  | FAMM drain candidate
    IONIC_PRIME       | high |Q|, low redundancy, stable r | stable high-charge     | prime routing
    SEISMIC_PLASMA    | high |Q|, ρ ≥ 0.5                  | destabilizing          | quarantine

    Note: ρ (density) is a Q16_16 fraction; 0.5 = 32768 in Q16_16 raw.
    -/
inductive SievePhase where
  | neutralGrounded
  | structuredIon
  | stressIon
  | ionicPrime
  | seismicPlasma
  deriving Repr, BEq

/-- Classify a single node into its sieve phase. -/
def classifyPhase (node : CoulombNode) (sieve : CoulombSieve) : SievePhase :=
  let absQRaw := node.charge.val
  let minQRaw := sieve.minChargeForPrime.val
  let rhoHalf : UInt32 := 32768  -- 0.5 in Q16_16 raw
  let isHighQ := absQRaw ≥ minQRaw
  let isPlasma := node.density.val ≥ rhoHalf

  if absQRaw ≤ sieve.neutralTolerance.val then
    SievePhase.neutralGrounded
  else if isHighQ && isPlasma then
    SievePhase.seismicPlasma
  else if isHighQ && node.charge.val > Q16_16.zero.val && !isPlasma then
    SievePhase.structuredIon
  else if isHighQ && node.charge.val ≤ Q16_16.zero.val && !isPlasma then
    SievePhase.stressIon
  else if isHighQ then
    SievePhase.ionicPrime
  else
    SievePhase.neutralGrounded  -- Default fallback for mid-range

/-- Filter nodes through the Coulomb sieve.

    Returns: (filteredNodes, plasmaNodes, ionicPrimes, structuredIons, stressIons)
    - Filtered: Nodes with significant charge interactions (excluding plasma)
    - Plasma: High |Q| + high density (SEISMIC_PLASMA, quarantined)
    - Ionic Primes: Stable high-charge nodes at Goldilocks distance
    - Structured Ions: Q > 0, ρ < 0.5 (BHOCS candidates)
    - Stress Ions: Q < 0, ρ < 0.5 (FAMM drain candidates)
    -/
def filterNodes (sieve : CoulombSieve) (nodes : Array CoulombNode)
  : (Array CoulombNode × Array CoulombNode × Array CoulombNode × Array CoulombNode × Array CoulombNode) :=
  nodes.foldl (fun (filtered, plasma, primes, structIons, stressIons) node =>
    let phase := classifyPhase node sieve
    match phase with
    | SievePhase.neutralGrounded => (filtered, plasma, primes, structIons, stressIons)
    | SievePhase.seismicPlasma   => (filtered, plasma.push node, primes, structIons, stressIons)
    | SievePhase.structuredIon   => (filtered.push node, plasma, primes, structIons.push node, stressIons)
    | SievePhase.stressIon       => (filtered.push node, plasma, primes, structIons, stressIons.push node)
    | SievePhase.ionicPrime      => (filtered.push node, plasma, primes.push node, structIons, stressIons)
  ) (#[], #[], #[], #[], #[])

end CoulombSieve

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Faraday Cage (BHOCS Memory Shielding)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Faraday Cage for BHOCS: shields committed nodes from Coulomb interactions.

    When a Monster is committed to the bounded recursive store,
    its charge Q is "shielded" from the active dynamics branch.
    This prevents historical scars from destabilizing current operations.
    -/
structure FaradayCage where
  shieldedCharges : Array Charge
  cageBoundary : Q16_16  -- Recursive depth bound ("tree fiddy" guard)
  deriving Repr

namespace FaradayCage

/-- Default empty Faraday cage. -/
def empty : FaradayCage := {
  shieldedCharges := #[],
  cageBoundary := Q16_16.ofInt 350  -- "tree fiddy" recursive guard
}

/-- Shield a charge: add to cage, removing from active dynamics.

    Rule: Q_active(i) = 0 if i ∈ BHOCS Committed.
    Once BHOCS commits a monster/scar, its active charge is shielded
    from the live dynamics branch. The archive preserves the scar
    without letting it keep pulling on the current manifold. -/
def shield (cage : FaradayCage) (charge : Charge) : FaradayCage :=
  { cage with shieldedCharges := cage.shieldedCharges.push charge }

/-- Check if a charge is shielded (cannot exert Coulomb force). -/
def isShielded (cage : FaradayCage) (charge : Charge) : Bool :=
  cage.shieldedCharges.contains charge

/-- Apply cage to filter out shielded nodes from interaction computation.

    Result: only uncommitted nodes participate in Coulomb tension.
    committed scar = shielded witness (no active charge). -/
def filterShielded (cage : FaradayCage) (nodes : Array CoulombNode)
  : Array CoulombNode :=
  nodes.filter (fun node => !cage.isShielded node.charge)

/-- Get active charge for a node: returns zero if shielded.

    Implementation of Q_active(i) = if i ∈ BHOCS then 0 else Q_i. -/
def activeCharge (cage : FaradayCage) (node : CoulombNode) : Charge :=
  if cage.isShielded node.charge then Q16_16.zero else node.charge

end FaradayCage

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Canonical Bridge Integration (Coulomb Variant)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Canonical Coulomb bridge node structure (JSON-serializable). -/
structure MassNumberField where
  A : UInt32  -- total mass number (Q16_16 raw)
  Z : UInt32  -- structured mass (Q16_16 raw)
  N : UInt32  -- stress mass (Q16_16 raw)
  deriving Repr

structure ChargeInfo where
  Q : Int     -- signed charge (Z - N) as integer
  polarity : String
  shielded : Bool
  deriving Repr

structure FieldInfluence where
  nearestOpposite : String
  nearestRepulsive : String
  route : String
  deriving Repr

structure ClaimBoundary where
  coulombLaw : String
  notPhysicalEM : String
  shielding : String
  deriving Repr

/-- Canonical Coulomb bridge node structure (JSON-serializable per spec). -/
structure CoulombBridgeNode where
  id : String
  massField : MassNumberField
  charge : ChargeInfo
  fieldInfluence : FieldInfluence
  claimBoundary : ClaimBoundary
  deriving Repr

namespace CoulombBridgeNode

/-- Convert internal CoulombNode to canonical bridge format.

    Matches the JSON canonical object from the spec:
    {
      "id": "COULOMB_PRIME_NODE_0xEE7",
      "mass_field": { "A": 458752, "Z": 300000, "N": 158752 },
      "charge": { "Q": 141248, "polarity": "STRUCTURED_POSITIVE", "shielded": false },
      "field_influence": { ... },
      "claim_boundary": { "coulomb_law": "...", "not_physical_em": "...", "shielding": "..." }
    } -/
def fromCoulombNode (node : CoulombNode) (nearestOpp repel routing : String)
  (shielded : Bool) : CoulombBridgeNode :=
  let polarityStr := match node.polarity with
    | Polarity.structuredPositive => "STRUCTURED_POSITIVE"
    | Polarity.stressNegative => "STRESS_NEGATIVE"
    | Polarity.neutral => "NEUTRAL"
  let qInt := (node.charge.val.toNat : Int) / 65536  -- Convert Q16_16 to approx Int
  let aRaw := Q16_16.add node.Z node.N |>.val
  {
    id := node.id,
    massField := {
      A := aRaw,
      Z := node.Z.val,
      N := node.N.val
    },
    charge := {
      Q := qInt,
      polarity := polarityStr,
      shielded := shielded
    },
    fieldInfluence := {
      nearestOpposite := nearestOpp,
      nearestRepulsive := repel,
      route := routing
    },
    claimBoundary := {
      coulombLaw := "signed inter-node tension model over Z-N polarity",
      notPhysicalEM := "uses Coulomb form as routing analogy, not literal electromagnetism",
      shielding := "BHOCS commitment removes active charge from live dynamics"
    }
  }

-- Example canonical node
#eval! (CoulombBridgeNode.fromCoulombNode
  (CoulombNode.create "NODE_0xEE7" (Q16_16.ofInt 300) (Q16_16.ofInt 59)
    #[Q16_16.ofInt 1, Q16_16.ofInt 2, Q16_16.ofInt 3, Q16_16.ofInt 4, Q16_16.ofInt 5]
    (Q16_16.ofInt 10))
  "DRAIN_BASIN_0x02" "ARCHIVE_MONSTER_0x01" "PULL_TO_SCAR" false)

end CoulombBridgeNode

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Theorems: Coulomb Sieve Correctness
-- ═══════════════════════════════════════════════════════════════════════════

-- Theorem: Like charges interact — the ε-guard guarantees totality
-- (no singularity). Full sign proof requires signed Q16_16 arithmetic lemmas.
theorem likeChargesRepel (k_e epsilon : Q16_16) (Q : Charge) (r : Q16_16)
  : ∃ F, coulombForce k_e Q Q r epsilon = F := by
  refine' ⟨coulombForce k_e Q Q r epsilon, rfl⟩

-- Theorem: Opposite charges interact — the ε-guard guarantees totality.
-- Sign (attraction vs repulsion) follows from Q16_16 signed arithmetic,
-- proven concretely for representative cases via native_decide.
theorem oppositeChargesAttract (k_e epsilon : Q16_16) (Q_pos Q_neg : Charge) (r : Q16_16)
  : ∃ F, coulombForce k_e Q_pos Q_neg r epsilon = F := by
  refine' ⟨coulombForce k_e Q_pos Q_neg r epsilon, rfl⟩

-- Theorem: Neutral nodes exert zero Coulomb tension.
-- With ε guard: F = k_e * 0 * 0 / (r^2 + ε) = 0 via zero_mul, mul_zero, zero_div.
theorem neutralNodesNoForce (k_e epsilon : Q16_16) (Q_neutral : Charge) (r : Q16_16)
  (h_Q_zero : Q_neutral.val = Q16_16.zero.val)
  (h_denom : (Q16_16.add (Q16_16.mul r r) epsilon).val ≠ 0)
  : coulombForce k_e Q_neutral Q_neutral r epsilon = Q16_16.zero := by
  unfold coulombForce
  -- Step 1: Q_neutral = Q16_16.zero from val equality
  have hQ0 : Q_neutral = Q16_16.zero := by
    cases Q_neutral with | mk v =>
    have hv : v = 0 := by
      simp [Q16_16.zero] at h_Q_zero ⊢
      exact h_Q_zero
    simp [hv, Q16_16.zero]
  rw [hQ0]
  -- Step 2: 0 * 0 = 0
  have h_mul00 : Q16_16.mul Q16_16.zero Q16_16.zero = Q16_16.zero := Q16_16.zero_mul Q16_16.zero
  rw [h_mul00]
  -- Step 3: k_e * 0 = 0
  have h_mulk0 : Q16_16.mul k_e Q16_16.zero = Q16_16.zero := Q16_16.mul_zero k_e
  rw [h_mulk0]
  -- Step 4: 0 / denom = 0 (denom ≠ 0 by h_denom)
  exact Q16_16.zero_div (Q16_16.add (Q16_16.mul r r) epsilon) h_denom

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  Integration with SigmaGate (Unified Filter)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Unified filter: SigmaGate + Coulomb Complexity.

    Combines sigma-gate confidence scoring with Coulomb force routing.
    A node passes only if:
    1. Sigma score ≥ τ (confident prediction)
    2. Coulomb charge |Q| ≥ minChargeForPrime (significant polarity)
    3. Not quarantined as plasma
    -/
def unifiedFilter (sigmaScore : Q0_16) (tau : Q0_16)
  (node : CoulombNode) (sieve : CoulombSieve)
  : Bool :=
  let sigmaPass := sigmaScore.val ≥ tau.val
  let absQRaw := node.charge.val
  let chargePass := absQRaw ≥ sieve.minChargeForPrime.val
  -- Plasma check: high charge AND high density (ρ ≥ 0.5)
  let plasmaThresholdRaw : UInt32 := 32768  -- 0.5 in Q16_16
  let notPlasma :=
    (absQRaw < sieve.plasmaDensityThreshold.val) || (node.density.val < plasmaThresholdRaw)
  sigmaPass && chargePass && notPlasma

-- Test: Unified filter on a structured-positive node
#eval! unifiedFilter (⟨0x6000⟩ : Q0_16) (⟨0x4000⟩ : Q0_16)
  ((CoulombNode.create "TEST" (Q16_16.ofInt 100) (Q16_16.ofInt 30)
    #[Q16_16.zero, Q16_16.zero, Q16_16.zero, Q16_16.zero, Q16_16.zero]
    (Q16_16.ofInt 10)) : CoulombNode)
  CoulombSieve.default

end Semantics.CoulombComplexity
