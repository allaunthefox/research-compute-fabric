import Semantics.HCMMR.Core
import Semantics.FixedPoint
import Semantics.Bind
import Semantics.ReceiptCore
import Semantics.Core.FoldedPointManifold

namespace Semantics.HCMMR.Bridge

open Semantics
open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16 Q0_16)
open Semantics.FoldedPointManifold (FoldDecision GateOutcome ResolutionDelta TotalInteraction)
open Semantics.ReceiptCore (Receipt ReceiptKind)

-- ═══════════════════════════════════════════════════════════════════
-- §1  FoldDecision ↔ HCMMR GateVerdict
-- ═══════════════════════════════════════════════════════════════════

def gateVerdictFromFoldDecision : FoldDecision → GateVerdict
  | FoldDecision.admit  => GateVerdict.admit
  | FoldDecision.hold   => GateVerdict.hold
  | FoldDecision.reject => GateVerdict.reject

def foldDecisionFromGateVerdict : GateVerdict → FoldDecision
  | GateVerdict.admit  => FoldDecision.admit
  | GateVerdict.hold   => FoldDecision.hold
  | GateVerdict.reject => FoldDecision.reject

#eval gateVerdictFromFoldDecision FoldDecision.admit
#eval gateVerdictFromFoldDecision FoldDecision.hold
#eval gateVerdictFromFoldDecision FoldDecision.reject
#eval foldDecisionFromGateVerdict GateVerdict.admit
#eval foldDecisionFromGateVerdict GateVerdict.hold
#eval foldDecisionFromGateVerdict GateVerdict.reject

-- ═══════════════════════════════════════════════════════════════════
-- §2  GateOutcome list → HCMMR GateChain
-- ═══════════════════════════════════════════════════════════════════

def gateChainFromGateOutcomeList (outcomes : List GateOutcome) (names : List String) : GateChain :=
  let extra := List.replicate (max 0 (outcomes.length - names.length)) "unnamed"
  let padded := names ++ extra
  let pairs := List.zip outcomes padded
  let gates := pairs.map fun (o, nm) =>
    let verdict : GateVerdict := match o with
      | GateOutcome.admit  => GateVerdict.admit
      | GateOutcome.hold   => GateVerdict.hold
      | GateOutcome.reject => GateVerdict.reject
    { name := nm, required := true, score := Q16_16.one, verdict := verdict }
  { gates := gates }

#eval gateChainFromGateOutcomeList [GateOutcome.admit, GateOutcome.hold, GateOutcome.reject] ["phi", "khi", "psi"]

-- ═══════════════════════════════════════════════════════════════════
-- §3  Bind.Metric → HCMMR Gate
-- ═══════════════════════════════════════════════════════════════════

def bindMetricToGate (m : Metric) : Gate :=
  let score := if m.cost.val == 0 then Q16_16.one
               else Q16_16.div Q16_16.one m.cost
  { name := m.tensor
  , required := true
  , score := score
  , verdict := if m.cost.val == Q16_16.zero.val then GateVerdict.admit
               else if score.val > 0 then GateVerdict.hold
               else GateVerdict.reject
  }

#eval bindMetricToGate Metric.euclidean
#eval bindMetricToGate { cost := Q16_16.ofInt 2, tensor := "riemannian", torsion := Q16_16.ofInt 1,
                         reference := "test", history_len := 1 }

-- ═══════════════════════════════════════════════════════════════════
-- §4  Theorems
-- ═══════════════════════════════════════════════════════════════════

theorem foldDecision_roundtrip (v : GateVerdict) :
    gateVerdictFromFoldDecision (foldDecisionFromGateVerdict v) = v := by
  cases v <;> rfl

theorem foldDecision_roundtrip_admit :
    foldDecisionFromGateVerdict (gateVerdictFromFoldDecision FoldDecision.admit) = FoldDecision.admit := by rfl

theorem foldDecision_roundtrip_reject :
    foldDecisionFromGateVerdict (gateVerdictFromFoldDecision FoldDecision.reject) = FoldDecision.reject := by rfl

theorem foldDecision_roundtrip_hold :
    foldDecisionFromGateVerdict (gateVerdictFromFoldDecision FoldDecision.hold) = FoldDecision.hold := by rfl

end Semantics.HCMMR.Bridge
