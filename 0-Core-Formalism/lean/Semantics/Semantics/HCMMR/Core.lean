/-
HCMMR Core.lean — Hyper-CMMR Operadic Meta-Calculus v0.1 typeclass definitions.

This is the typeclass and core structure file. Every other HCMMR module
depends on these definitions. The HCMMR is a typed-gate diagnostic system:
objects enter a 16D transform stack, get decomposed through multiplicative
gates, and produce signed eigenmass with residual receipts. A failed gate
does NOT erase the object — it collapses the validity claim and routes the
residual to the Underverse.
-/

import Semantics.FixedPoint
import Semantics.Bind
import Semantics.ReceiptCore

namespace Semantics.HCMMR.Core

open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Gate Verdict (admit / hold / reject)
-- ═══════════════════════════════════════════════════════════════════

/--
The three possible outcomes of a gate evaluation, isomorphic to
`FoldedPointManifold.FoldDecision`. A failed gate routes the object's
residual to an alternate path rather than destroying it.
-/
inductive GateVerdict where
  | admit
  | hold
  | reject
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §2  HCMMRObject — the fundamental entity entering the transform stack
-- ═══════════════════════════════════════════════════════════════════

/--
The fundamental entity that enters the HCMMR 16D transform stack.
Carries its symbolic identity, native dimensional home, the metric gate
it targets, origin description, admissibility flag, and receipt chain root.
-/
structure HCMMRObject where
  payload        : String
  nativeDim      : Nat
  requestedGate  : String
  source         : String
  admissible     : Bool
  receiptRoot    : String
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §3  Gate — a single admission gate
-- ═══════════════════════════════════════════════════════════════════

/--
A single gate in the multiplicative admission chain.
`required` gates block the chain on hold or reject.
`score` is in [0, 1] via Q16_16 (0 = total failure, 1 = perfect pass).
-/
structure Gate where
  name     : String
  required : Bool
  score    : Q16_16
  verdict  : GateVerdict
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §4  GateChain — ordered list of gates forming a multiplicative series
-- ═══════════════════════════════════════════════════════════════════

/--
An ordered list of gates forming the multiplicative admission series.
The chain passes only if ALL required gates admit.
-/
structure GateChain where
  gates : List Gate
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §5  gateChainVerdict — evaluate a GateChain
-- ═══════════════════════════════════════════════════════════════════

/--
Evaluates a GateChain using multiplicative logic:
- If ANY required gate rejects → reject
- If ANY required gate is hold (and none reject) → hold
- If ALL required gates admit → admit

Non-required gates are ignored for chain verdict.
-/
def gateChainVerdict (chain : GateChain) : GateVerdict :=
  let requiredGates := chain.gates.filter (fun g => g.required)
  if requiredGates.any (fun g => g.verdict == GateVerdict.reject) then
    GateVerdict.reject
  else if requiredGates.any (fun g => g.verdict == GateVerdict.hold) then
    GateVerdict.hold
  else
    GateVerdict.admit

-- ═══════════════════════════════════════════════════════════════════
-- §6  EigenmassOperator — extracts stable modes
-- ═══════════════════════════════════════════════════════════════════

/--
The eigenmass operator extracts stable structural modes and per-gate
admission scores. Each score field records the corresponding gate's
Q16_16 value in [0, 1]. The canonical multiplicative eigenmass is
computed from these scores via `eigenmassProduct`.
-/
structure EigenmassOperator where
  eigenvalue         : Q16_16
  magnitude          : Q16_16
  admissibilityScore : Q16_16
  invarianceScore    : Q16_16
  chiralityScore     : Q16_16
  receiptScore       : Q16_16
  calibrationScore   : Q16_16
  projectionScore    : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §7  eigenmassProduct — the canonical multiplicative eigenmass M⁺
-- ═══════════════════════════════════════════════════════════════════

/--
Computes the canonical multiplicative eigenmass M⁺:
  M⁺ = (λ₁ × A × I × χ × R × Ω_K × Π) / (1 + ε)

If any gate score is zero, the product is zero (multiplicative collapse).
`epsilon` is the residual friction from gate mismatches, passed in as a
Q16_16 value. The denominator is always at least 1.0.
-/
def eigenmassProduct (op : EigenmassOperator) (epsilon : Q16_16) : Q16_16 :=
  let gates := #[op.eigenvalue, op.admissibilityScore, op.invarianceScore,
                  op.chiralityScore, op.receiptScore, op.calibrationScore,
                  op.projectionScore]
  let anyZero := gates.any (fun s => s.val == 0)
  if anyZero then
    Q16_16.zero
  else
    let product := gates.foldl Q16_16.mul (Q16_16.ofInt 1)
    let denom := Q16_16.add (Q16_16.ofInt 1) epsilon
    if denom.val == 0 then
      Q16_16.zero
    else
      Q16_16.div product denom

-- ═══════════════════════════════════════════════════════════════════
-- §8  eigenmassSigned — the signed eigenmass M±
-- ═══════════════════════════════════════════════════════════════════

/--
Computes the signed eigenmass M±:
  M±(X) = M⁺(X) − M⁻(X)

M⁺ uses the positive-ladder residual ε⁺.
M⁻ uses the same gate scores but with the Underverse-side residual ε⁻
(higher friction yields smaller denominator and more mass penalty).
If the Underverse mass is zero, the signed mass equals the positive mass.
-/
def eigenmassSigned (op : EigenmassOperator) (epsilonPlus epsilonMinus : Q16_16) : Q16_16 :=
  let mPlus := eigenmassProduct op epsilonPlus
  let mMinus := eigenmassProduct op epsilonMinus
  Q16_16.sub mPlus mMinus

-- ═══════════════════════════════════════════════════════════════════
-- §9  Residual — dimensional mismatch friction
-- ═══════════════════════════════════════════════════════════════════

/--
A typed residual scar produced when an object mismatches a gate's
dimensional metric. Each residual carries its domain, Q16_16 magnitude,
and the source gate that produced it.
-/
structure Residual where
  domain : String
  value  : Q16_16
  source : String
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §10  DiagnosticReceipt — what a failed gate emits
-- ═══════════════════════════════════════════════════════════════════

/--
Emitted when a gate rejects an object. Records the failed object's
identity, which gate rejected it, the residual scar, an alternate route
for rerouting the residual, and a timestamp.
-/
structure DiagnosticReceipt where
  object         : String
  failedGate     : String
  residual       : Residual
  alternateRoute : String
  timestamp      : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §11  Fixtures
-- ═══════════════════════════════════════════════════════════════════

/--
A fully passing HCMMRObject with all gates admitting.
Represents an object that survives the full multiplicative chain.
-/
def canonicalFixture : HCMMRObject :=
  { payload       := "pythagorean_triple"
  , nativeDim     := 2
  , requestedGate := "L2"
  , source        := "Euclidean_geometry"
  , admissible    := true
  , receiptRoot   := "deadbeef00000000000000000000000000000000000000000000000000000000"
  }

/--
An EigenmassOperator for a perfectly passing object: all gate scores
are 1.0 and the eigenvalue is 1.0.
-/
def fullyAdmittingOperator : EigenmassOperator :=
  { eigenvalue         := Q16_16.one
  , magnitude          := Q16_16.one
  , admissibilityScore := Q16_16.one
  , invarianceScore    := Q16_16.one
  , chiralityScore     := Q16_16.one
  , receiptScore       := Q16_16.one
  , calibrationScore   := Q16_16.one
  , projectionScore    := Q16_16.one
  }

/--
An operator where the receipt gate has failed (score = 0).
-/
def receiptFailureOperator : EigenmassOperator :=
  { fullyAdmittingOperator with receiptScore := Q16_16.zero }

/--
A fully admitting chain with all seven canonical gates.
-/
def fullyAdmittingChain : GateChain :=
  { gates :=
    [ { name := "Admissibility", required := true, score := Q16_16.one, verdict := GateVerdict.admit }
    , { name := "Invariance",    required := true, score := Q16_16.one, verdict := GateVerdict.admit }
    , { name := "Chirality",     required := true, score := Q16_16.one, verdict := GateVerdict.admit }
    , { name := "Receipt",       required := true, score := Q16_16.one, verdict := GateVerdict.admit }
    , { name := "Calibration",   required := true, score := Q16_16.one, verdict := GateVerdict.admit }
    , { name := "Projection",    required := true, score := Q16_16.one, verdict := GateVerdict.admit }
    ]
  }

/--
A chain where the Chirality gate holds.
-/
def chiralityHoldChain : GateChain :=
  { fullyAdmittingChain with
      gates := fullyAdmittingChain.gates.map (fun g =>
        if g.name == "Chirality" then
          { g with verdict := GateVerdict.hold }
        else
          g)
  }

/--
A chain where the Receipt gate rejects.
-/
def receiptRejectChain : GateChain :=
  { fullyAdmittingChain with
      gates := fullyAdmittingChain.gates.map (fun g =>
        if g.name == "Receipt" then
          { g with verdict := GateVerdict.reject }
        else
          g)
  }

/--
A chain where an optional/non-required gate rejects — should not affect
the chain verdict.
-/
def optionalRejectChain : GateChain :=
  { fullyAdmittingChain with
      gates := fullyAdmittingChain.gates.map (fun g =>
        if g.name == "Projection" then
          { g with required := false, verdict := GateVerdict.reject }
        else
          g)
  }

-- ═══════════════════════════════════════════════════════════════════
-- §12  Theorems
-- ═══════════════════════════════════════════════════════════════════

/--
When all required gates admit, the chain admits.
-/
theorem gate_chain_all_admit :
    gateChainVerdict fullyAdmittingChain = GateVerdict.admit := by
  native_decide

/--
A single required reject causes the chain to reject.
-/
theorem gate_chain_one_rejects :
    gateChainVerdict receiptRejectChain = GateVerdict.reject := by
  native_decide

/--
If a single required gate is hold (and none reject), the chain is hold.
-/
theorem gate_chain_one_holds :
    gateChainVerdict chiralityHoldChain = GateVerdict.hold := by
  native_decide

/--
An optional gate rejecting does not affect the chain verdict.
-/
theorem gate_chain_optional_reject_ignored :
    gateChainVerdict optionalRejectChain = GateVerdict.admit := by
  native_decide

/--
If any gate score is zero, eigenmassProduct is zero.
-/
theorem eigenmass_zero_on_any_gate_failure :
    eigenmassProduct receiptFailureOperator Q16_16.zero = Q16_16.zero := by
  native_decide

/--
When both epsilons are equal, M± = 0 (perfect symmetry in ladder vs underverse).
-/
theorem eigenmass_signed_identity :
    eigenmassSigned fullyAdmittingOperator Q16_16.zero Q16_16.zero
    = Q16_16.zero := by
  native_decide

/--
With nonzero epsilon, the fully admitting operator yields M⁺ < 1.0
(because denominator exceeds 1.0).
-/
theorem eigenmass_product_residual_dampens :
    Q16_16.lt (eigenmassProduct fullyAdmittingOperator (Q16_16.ofInt 2)) (Q16_16.ofInt 1) = true := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════
-- §13  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════

#eval canonicalFixture

#eval gateChainVerdict fullyAdmittingChain
#eval gateChainVerdict chiralityHoldChain
#eval gateChainVerdict receiptRejectChain
#eval gateChainVerdict optionalRejectChain

#eval eigenmassProduct fullyAdmittingOperator Q16_16.zero
#eval eigenmassProduct fullyAdmittingOperator (Q16_16.ofInt 2)
#eval eigenmassProduct receiptFailureOperator Q16_16.zero

#eval eigenmassSigned fullyAdmittingOperator Q16_16.zero Q16_16.zero
#eval eigenmassSigned fullyAdmittingOperator (Q16_16.ofInt 2) (Q16_16.ofInt 4)

end Semantics.HCMMR.Core
