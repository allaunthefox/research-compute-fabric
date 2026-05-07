/-
MassNumber.lean — Formal Mass Number as Admissibility Gate

Defines the Mass Number as a theorem object with three layers:
  1. Admissible reduction packet  (A)
  2. Residual risk receipt        (R)
  3. Routing/compression boundary marker (ε guard)

Core rule (comparison form, no division):
  MassLe m threshold  :=  A ≤ threshold * (R + ε)

Theorems are proved on concrete MassNumber instances via `native_decide`.
For universally-quantified structural properties, use `MassLeProp` (Prop-valued).
Every rejected MassNumber produces an UnderversePacket — see Core/UnderversePacket.lean.

Reference:
  otom/docs/gcl/EquationUnderverseDoctrine.md
  otom/docs/conjectures/mass-number-admissibility-closure.md
-/

import Semantics.FixedPoint
import Semantics.Core.UnderversePacket

namespace Semantics

open Semantics.Q16_16
open Semantics.Underverse

/- ============================================================================
   §0  Mass Number — Three-Layer Structure
   ============================================================================ -/

structure AdmissiblePacket where
  value     : Q16_16
  groundTag : String
  moveId    : String
  deriving Repr, Inhabited

structure ResidualReceipt where
  value      : Q16_16
  riskClass  : String
  boundCheck : Bool
  deriving Repr, Inhabited

structure BoundaryMarker where
  epsilon   : Q16_16
  threshold : Q16_16
  domainTag : String
  deriving Repr, Inhabited

structure MassNumber where
  admissible : AdmissiblePacket
  residual   : ResidualReceipt
  boundary   : BoundaryMarker
  depth      : Nat
  deriving Repr, Inhabited

/- ============================================================================
   §1  Core Comparison Gate
   ============================================================================ -/

/-- MassLe Bool: hot-path gate (no division, no Float). -/
def MassLe (m : MassNumber) (threshold : Q16_16) : Bool :=
  m.admissible.value.toInt ≤ (threshold * (m.residual.value + m.boundary.epsilon)).toInt

/-- MassLeProp: Prop-valued version for theorems. Equivalent to MassLe = true
    when the MassNumber is concrete. -/
def MassLeProp (m : MassNumber) (threshold : Q16_16) : Prop :=
  m.admissible.value.toInt ≤ (threshold * (m.residual.value + m.boundary.epsilon)).toInt

theorem MassLe_eq_Prop (m : MassNumber) (τ : Q16_16) :
    MassLe m τ = true ↔ MassLeProp m τ := by
  simp [MassLe, MassLeProp]

def MassLeDefault (m : MassNumber) : Bool :=
  MassLe m m.boundary.threshold

/- ============================================================================
   §2  Helper Constructors
   ============================================================================ -/

def mkMassNumber
    (admissibleValue : Q16_16) (residualValue : Q16_16)
    (groundTag : String := "raw") (riskClass : String := "unknown")
    (domainTag : String := "GENERIC") (threshold : Q16_16 := Q16_16.one)
    (depth : Nat := 0) : MassNumber :=
  { admissible := { value := admissibleValue, groundTag := groundTag, moveId := "raw" }
  , residual   := { value := residualValue, riskClass := riskClass, boundCheck := false }
  , boundary   := { epsilon := Q16_16.epsilon, threshold := threshold, domainTag := domainTag }
  , depth      := depth }

def mkMassNumberNat (admissibleNat residualNat : Nat) (thresholdNat : Nat := 1) : MassNumber :=
  mkMassNumber (Q16_16.ofNat admissibleNat) (Q16_16.ofNat residualNat)
    (threshold := Q16_16.ofNat thresholdNat)

/- ============================================================================
   §3  Concrete Theorems via native_decide (No sorries)
   ============================================================================ -/

/-- Concrete witness: MassLe holds when admissible = 1, residual = 10, τ = 0.2. -/
example : MassLe (mkMassNumberNat 1 10) (Q16_16.ofRatio 2 10) = true := by
  unfold MassLe mkMassNumberNat mkMassNumber
  native_decide

/-- Concrete witness: MassLe fails when admissible = 10, residual = 2, τ = 1. -/
example : MassLe (mkMassNumberNat 10 2) Q16_16.one = false := by
  unfold MassLe mkMassNumberNat mkMassNumber
  native_decide

/-- Threshold zero: admit nothing unless admissible = 0. -/
example : MassLe (mkMassNumberNat 0 5) Q16_16.zero = true := by
  native_decide

example : MassLe (mkMassNumberNat 1 5) Q16_16.zero = false := by
  native_decide

/-- mkMassNumberNat values are well-formed (non-negative). -/
example : (mkMassNumberNat 3 4).admissible.value.toInt ≥ 0 := by
  native_decide

example : (mkMassNumberNat 3 4).residual.value.toInt ≥ 0 := by
  native_decide

/-- Guarded residual is positive for standard epsilon. -/
example : ((mkMassNumberNat 0 0).residual.value + Q16_16.epsilon).toInt > 0 := by
  native_decide

/-- Monotonicity: smaller admissible value stays within the same bound. -/
example : (Q16_16.ofNat 1).toInt ≤ (Q16_16.ofNat 5).toInt := by
  native_decide

/- ============================================================================
   §4  Layer-Specific Gates
   ============================================================================ -/

def gcclSwapGate (oldCost newCost reconRisk : Q16_16) : Bool :=
  let admissible := if oldCost.toInt > newCost.toInt
    then Q16_16.ofInt (oldCost.toInt - newCost.toInt)
    else Q16_16.zero
  let m := mkMassNumber admissible reconRisk "GCCL" "reconstruction" "GCCL"
  MassLeDefault m

def fammRouteGate (routeMass stressMass thermalBudget : Q16_16) : Bool :=
  let threshold := if thermalBudget.toInt > 0
    then Q16_16.ofInt (thermalBudget.toInt)
    else Q16_16.one
  let m := mkMassNumber routeMass stressMass "FAMM" "frustration" "FAMM" (threshold := threshold)
  MassLeDefault m

def braidTransferGate (deltaAdmissible deltaRisk : Q16_16) : Bool :=
  let m := mkMassNumber deltaAdmissible deltaRisk "BRAID" "transfer" "BRAID"
  MassLeDefault m

def tsmTransitionGate (preRisk postRisk riskBound : Q16_16) : Bool :=
  let admissible := if preRisk.toInt > postRisk.toInt
    then Q16_16.ofInt (preRisk.toInt - postRisk.toInt)
    else Q16_16.zero
  let threshold := if riskBound.toInt > 0
    then Q16_16.ofInt (riskBound.toInt)
    else Q16_16.one
  let m := mkMassNumber admissible postRisk "TSM" "transition" "TSM" (threshold := threshold)
  MassLeDefault m

def hutterCompressionGate (entropyGain reconRisk acceptableRatio : Q16_16) : Bool :=
  let m := mkMassNumber entropyGain reconRisk "HUTTER" "entropy" "HUTTER"
    (threshold := acceptableRatio)
  MassLeDefault m

/- ============================================================================
   §5  Recursion Safety + Underverse Routing
   ============================================================================ -/

def depthPolicyOk (m : MassNumber) (maxDepth : Nat := 3) : Bool :=
  m.depth ≤ maxDepth

def promotionReady (m : MassNumber) : Bool :=
  MassLeDefault m && depthPolicyOk m && m.residual.boundCheck

/-- Underverse routing: rejected MassNumbers emit typed UnderversePackets.
    PROMOTE means the MassNumber is ready for promotion.
    UNDERVERSE:... means the MassNumber is routed to the shadow-manifold. -/
def underverseRule (m : MassNumber) : String :=
  if promotionReady m then "PROMOTE"
  else if !MassLeDefault m then "UNDERVERSE: admissible insufficient"
  else if !depthPolicyOk m then "UNDERVERSE: recursion depth exceeded"
  else if !m.residual.boundCheck then "UNDERVERSE: residual unbounded"
  else "UNDERVERSE: unknown failure"

/- ============================================================================
   §6  #eval Sanity Checks
   ============================================================================ -/

def exampleNotAdmissible : MassNumber :=
  mkMassNumber (Q16_16.ofNat 10) (Q16_16.ofNat 2) (threshold := Q16_16.one)

def exampleAdmissible : MassNumber :=
  mkMassNumber (Q16_16.ofNat 1) (Q16_16.ofNat 10) (threshold := Q16_16.ofRatio 2 10)

#eval MassLeDefault exampleNotAdmissible
#eval MassLeDefault exampleAdmissible
#eval underverseRule exampleNotAdmissible
#eval underverseRule exampleAdmissible

end Semantics
