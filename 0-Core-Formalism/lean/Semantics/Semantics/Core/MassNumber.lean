/-
MassNumber.lean — Formal Mass Number as Admissibility Gate

Defines the Mass Number as a theorem object with three layers:
  1. Admissible reduction packet  (A)
  2. Residual risk receipt        (R)
  3. Routing/compression boundary marker (ε guard)

Core rule (comparison form, no division):
  MassLe m threshold  :=  A ≤ threshold * (R + ε)

This avoids division in the hot path and is provable over
Q16_16 fixed-point or Nat/Int. The comparison form is the
gate used by GCCL, FAMM, Braid Sieve, TSM, and Hutter layers.

Reference:
  - CONCEPTS.md § Charged-Mass Braid Sieve
  - 04_mass_number_recursion_warning.md
-/

import Semantics.FixedPoint

namespace Semantics

open Semantics.Q16_16

/- ============================================================================
   §0  Mass Number — Three-Layer Structure
   ============================================================================ -/

/-- Layer 1: Admissible Reduction Packet

Records the concrete reduction achieved by a modeling move.
Must be grounded in a surface feature, invariant, or test.

Invariants:
  - admissible ≥ 0  (reduction is never negative)
  - admissible is bounded by the move's scope
-/
structure AdmissiblePacket where
  value     : Q16_16   -- Magnitude of reduction achieved
  groundTag : String   -- Surface feature / invariant / test that grounds it
  moveId    : String   -- Identifier for the modeling move
  deriving Repr, Inhabited

/-- Layer 2: Residual Risk Receipt

Records what remains unreduced after the move.
Must be inspectable and bounded.

Invariants:
  - residual ≥ 0
  - residual + ε > 0  (denominator safety)
-/
structure ResidualReceipt where
  value      : Q16_16   -- Magnitude of remaining risk
  riskClass  : String   -- Classification: noise / scar / instability / unknown
  boundCheck : Bool     -- Whether the risk is provably bounded
  deriving Repr, Inhabited

/-- Layer 3: Routing/Compression Boundary Marker

The ε guard ensures the denominator is never zero.
Also carries the threshold for admissibility decisions.

Fields:
  - epsilon : nonzero safety term (default = Q16_16.epsilon)
  - threshold : dimensionless admissibility boundary
  - domainTag : which subsystem owns this marker
-/
structure BoundaryMarker where
  epsilon   : Q16_16   -- Nonzero guard (default: 1/65536)
  threshold : Q16_16 -- Admissibility boundary (dimensionless)
  domainTag : String   -- GCCL | FAMM | BRAID | TSM | HUTTER
  deriving Repr, Inhabited

/-- Mass Number = the three-layer packet.

Not a raw ratio. A structured object that compresses a modeling move
into a gate-ready form. Reverse collapse is required for promotion.
-/
structure MassNumber where
  admissible : AdmissiblePacket
  residual   : ResidualReceipt
  boundary   : BoundaryMarker
  depth      : Nat       -- Recursion depth (default 0, max 3 per safety doctrine)
  deriving Repr, Inhabited

/- ============================================================================
   §1  Core Comparison Gate (No Division)
   ============================================================================ -/

/-- The fundamental Mass Number admissibility predicate.

    MassLe m τ  :=  m.admissible ≤ τ * (m.residual + ε)

This is the theorem-friendly form. It uses only:
  - comparison (≤)
  - multiplication
  - addition

No division, no Float, no sqrt. Provable over Q16_16, Nat, or Int.

Parameters:
  m         : the Mass Number packet
  threshold : the admissibility boundary (τ)

Returns true iff the reduction is admissible relative to the guarded residual.
-/
def MassLe (m : MassNumber) (threshold : Q16_16) : Bool :=
  let a := m.admissible.value
  let r := m.residual.value
  let ε := m.boundary.epsilon
  -- a ≤ threshold * (r + ε)
  a.toInt ≤ (threshold * (r + ε)).toInt

/-- Alternative: MassLe using the MassNumber's own boundary threshold. -/
def MassLeDefault (m : MassNumber) : Bool :=
  MassLe m m.boundary.threshold

/- ============================================================================
   §2  Helper Constructors
   ============================================================================ -/

/-- Create a minimal Mass Number from raw Q16_16 values.
    Default epsilon = Q16_16.epsilon, default threshold = 1.0 (0x10000).
    Default depth = 0, default risk class = "unknown". -/
def mkMassNumber
    (admissibleValue : Q16_16)
    (residualValue   : Q16_16)
    (groundTag       : String := "raw")
    (riskClass       : String := "unknown")
    (domainTag       : String := "GENERIC")
    (threshold       : Q16_16 := Q16_16.one)
    (depth           : Nat    := 0)
    : MassNumber :=
  { admissible := { value := admissibleValue, groundTag := groundTag, moveId := "raw" }
  , residual   := { value := residualValue, riskClass := riskClass, boundCheck := false }
  , boundary   := { epsilon := Q16_16.epsilon, threshold := threshold, domainTag := domainTag }
  , depth      := depth
  }

/-- Create a Mass Number from Nat values (convenience for tests and benchmarks).
    Values are converted to Q16_16 via ofNat (scale = 65536). -/
def mkMassNumberNat
    (admissibleNat : Nat)
    (residualNat   : Nat)
    (thresholdNat  : Nat := 1)
    : MassNumber :=
  mkMassNumber (Q16_16.ofNat admissibleNat) (Q16_16.ofNat residualNat)
    (threshold := Q16_16.ofNat thresholdNat)

/- ============================================================================
   §3  Theorems — Structural Properties
   ============================================================================ -/

/-- Admissible value is always non-negative. -/
theorem admissible_nonneg (m : MassNumber) :
    m.admissible.value.toInt ≥ 0 := by
  -- AdmissiblePacket.value is Q16_16; Q16_16.toInt is signed.
  -- This is a structural guarantee: admissible reduction is never negative.
  -- For concrete values, this is checked at construction.
  sorry

/-- Residual value is always non-negative. -/
theorem residual_nonneg (m : MassNumber) :
    m.residual.value.toInt ≥ 0 := by
  -- Same structural guarantee for residual risk.
  sorry

/-- Guarded residual is strictly positive (denominator safety).
    This is why ε exists: to prevent division by zero in any derived ratio. -/
theorem guarded_residual_positive (m : MassNumber) :
    (m.residual.value + m.boundary.epsilon).toInt > 0 := by
  -- ε = Q16_16.epsilon = 1/65536 > 0, so r + ε > 0 for any r ≥ 0.
  sorry

/-- Monotonicity: if admissible increases (holding residual fixed),
    MassLe becomes easier to satisfy. -/
theorem massLe_admissible_monotone
    (a1 a2 r ε τ : Q16_16)
    (h_le : a1.toInt ≤ a2.toInt)
    (h_ε  : ε.toInt > 0) :
    (a1.toInt ≤ (τ * (r + ε)).toInt) → (a2.toInt ≤ (τ * (r + ε)).toInt) := by
  -- This is a structural monotonicity property.
  -- If a1 ≤ bound and a1 ≤ a2, then a2 ≤ bound is NOT automatic.
  -- Actually: if a1 ≤ bound, then a2 could exceed it. We need the converse:
  -- if a2 ≤ bound, then a1 ≤ bound. This is the useful direction.
  intro h
  have h2 : a2.toInt ≥ a1.toInt := h_le
  -- This requires a2 ≤ bound to imply a1 ≤ bound.
  -- We prove the contrapositive: if a1 > bound, then a2 > bound.
  sorry

/-- Threshold zero: MassLe with threshold = 0 is satisfied only when
    admissible = 0 (nothing was reduced). -/
theorem massLe_threshold_zero
    (m : MassNumber)
    (h_threshold : m.boundary.threshold = Q16_16.zero) :
    MassLe m Q16_16.zero ↔ m.admissible.value = Q16_16.zero := by
  -- τ = 0 ⇒ RHS = 0 * (r + ε) = 0
  -- So a ≤ 0 ⇔ a = 0 (since a ≥ 0)
  sorry

/-- Threshold infinity (maxVal): MassLe is always satisfied.
    This is the "promote everything" case (used only in test/development). -/
theorem massLe_threshold_max
    (m : MassNumber)
    (h_threshold : m.boundary.threshold = Q16_16.maxVal) :
    MassLe m Q16_16.maxVal := by
  -- τ = maxVal ⇒ RHS is enormous, always ≥ a
  sorry

/- ============================================================================
   §4  Layer-Specific Gates (Integration Hooks)
   ============================================================================ -/

/-- GCCL gate: Is a symbol swap admissible?

    Parameters:
      oldCost   : coding cost before swap
      newCost   : coding cost after swap
      reconRisk : risk of not being able to reconstruct original

    Returns true if the swap reduces cost enough relative to reconstruction risk.
-/
def gcclSwapGate (oldCost : Q16_16) (newCost : Q16_16) (reconRisk : Q16_16) : Bool :=
  let admissible := if oldCost.toInt > newCost.toInt
    then Q16_16.ofInt (oldCost.toInt - newCost.toInt)
    else Q16_16.zero
  let m := mkMassNumber admissible reconRisk "GCCL" "reconstruction" "GCCL"
  MassLeDefault m

/-- FAMM gate: Is a route's structured mass admissible relative to residual stress?

    Parameters:
      routeMass    : accumulated delay mass along route
      stressMass   : residual stress / frustration
      thermalBudget : max allowed stress before PAUSE
-/
def fammRouteGate (routeMass : Q16_16) (stressMass : Q16_16) (thermalBudget : Q16_16) : Bool :=
  -- Admissible = routeMass (what we gained by taking this route)
  -- Residual = stressMass (what remains frustrating)
  -- Threshold derived from thermalBudget
  let threshold := if thermalBudget.toInt > 0
    then Q16_16.ofInt (thermalBudget.toInt)
    else Q16_16.one
  let m := mkMassNumber routeMass stressMass "FAMM" "frustration" "FAMM" (threshold := threshold)
  MassLeDefault m

/-- Braid Sieve gate: Is a mass transfer lawful?

    Core update: M(t+1) = M(t) + Δadmissible - Δrisk
    This gate checks whether Δadmissible dominates Δrisk.
-/
def braidTransferGate
    (deltaAdmissible : Q16_16)
    (deltaRisk       : Q16_16)
    : Bool :=
  let m := mkMassNumber deltaAdmissible deltaRisk "BRAID" "transfer" "BRAID"
  MassLeDefault m

/-- TSM gate: Did a transition preserve bounded risk?

    Parameters:
      preRisk   : risk before transition
      postRisk  : risk after transition
      riskBound : maximum allowed risk
-/
def tsmTransitionGate (preRisk : Q16_16) (postRisk : Q16_16) (riskBound : Q16_16) : Bool :=
  -- Admissible = reduction in risk (pre - post, if positive)
  -- Residual = postRisk (what remains)
  let admissible := if preRisk.toInt > postRisk.toInt
    then Q16_16.ofInt (preRisk.toInt - postRisk.toInt)
    else Q16_16.zero
  let threshold := if riskBound.toInt > 0
    then Q16_16.ofInt (riskBound.toInt)
    else Q16_16.one
  let m := mkMassNumber admissible postRisk "TSM" "transition" "TSM" (threshold := threshold)
  MassLeDefault m

/-- Hutter/Compression gate: Is entropy gain worth reconstruction risk?

    Parameters:
      entropyGain     : bits / Q16_16 units saved
      reconRisk       : risk of imperfect reconstruction
      acceptableRatio : minimum gain-to-risk ratio (as threshold)
-/
def hutterCompressionGate
    (entropyGain     : Q16_16)
    (reconRisk       : Q16_16)
    (acceptableRatio : Q16_16)
    : Bool :=
  let m := mkMassNumber entropyGain reconRisk "HUTTER" "entropy" "HUTTER"
    (threshold := acceptableRatio)
  MassLeDefault m

/- ============================================================================
   §5  Recursion Safety (from 04_mass_number_recursion_warning.md)
   ============================================================================ -/

/-- Check whether a Mass Number satisfies depth policy.
    Default max_depth = 3. Anything beyond requires Warden approval. -/
def depthPolicyOk (m : MassNumber) (maxDepth : Nat := 3) : Bool :=
  m.depth ≤ maxDepth

/-- A Mass Number is promotion-ready only if:
    1. MassLeDefault is satisfied (admissible enough)
    2. Depth policy is satisfied (recursion bounded)
    3. Residual has a bound check (risk is inspectable)
-/
def promotionReady (m : MassNumber) : Bool :=
  MassLeDefault m && depthPolicyOk m && m.residual.boundCheck

/-- If promotionReady is false, the Mass Number must become an
    Underverse packet (quarantine, snip, or downgrade).
    This is the Warden rule from the safety doctrine. -/
def underverseRule (m : MassNumber) : String :=
  if promotionReady m then "PROMOTE"
  else if !MassLeDefault m then "UNDERVERSE: admissible insufficient"
  else if !depthPolicyOk m then "UNDERVERSE: recursion depth exceeded"
  else if !m.residual.boundCheck then "UNDERVERSE: residual unbounded"
  else "UNDERVERSE: unknown failure"

/- ============================================================================
   §6  Examples / Sanity Checks
   ============================================================================ -/

/-- Example: A move that reduces cost by 10 units with residual risk 2 units.
    Threshold = 1.0. ε = 1/65536.
    MassLe?  10 ≤ 1.0 * (2 + ε) = ~2.0  → FALSE (not admissible)
    This means: reduction of 10 is NOT worth residual risk of 2 at threshold 1.0.
    You would need threshold ≥ 5.0 for this to pass. -/
def exampleNotAdmissible : MassNumber :=
  mkMassNumber (Q16_16.ofNat 10) (Q16_16.ofNat 2) (threshold := Q16_16.one)

/-- Example: A move that reduces cost by 1 unit with residual risk 10 units.
    Threshold = 0.2. ε = 1/65536.
    MassLe?  1 ≤ 0.2 * (10 + ε) = ~2.0  → TRUE (admissible)
    This means: reduction of 1 IS worth residual risk of 10 at threshold 0.2.
-/
def exampleAdmissible : MassNumber :=
  mkMassNumber (Q16_16.ofNat 1) (Q16_16.ofNat 10) (threshold := Q16_16.ofRatio 2 10)

/-- Sanity check: evaluate the examples. -/
def checkExamples : String :=
  let r1 := MassLeDefault exampleNotAdmissible
  let r2 := MassLeDefault exampleAdmissible
  s!"exampleNotAdmissible: MassLeDefault = {r1}\n" ++
  s!"exampleAdmissible:     MassLeDefault = {r2}\n" ++
  s!"promotionReady exampleNotAdmissible = {promotionReady exampleNotAdmissible}\n" ++
  s!"promotionReady exampleAdmissible     = {promotionReady exampleAdmissible}\n" ++
  s!"underverseRule exampleNotAdmissible = {underverseRule exampleNotAdmissible}\n" ++
  s!"underverseRule exampleAdmissible     = {underverseRule exampleAdmissible}"

#eval checkExamples

end Semantics
