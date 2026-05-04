/-
  RelationMaskTrainer.lean - KS_RELATION_SIEVE Formalization
  Migrates legacy f64 outcome ratios to strict UInt64 limits.
-/
import Semantics.Bind

namespace Semantics.RelationMaskTrainer

inductive RelationClass
| Pass
| Hold
| Reject
deriving Repr, DecidableEq, Inhabited

inductive DownstreamOutcome
| PassStable
| HoldStabilized
| Rejected
| SurvivalTransition
| FlameTransition
deriving Repr, DecidableEq, Inhabited

structure SignatureStats where
  total : UInt64
  passStable : UInt64
  holdStabilized : UInt64
  rejected : UInt64
  survival : UInt64
  flame : UInt64
deriving Repr, Inhabited, DecidableEq

def observe (stats : SignatureStats) (outcome : DownstreamOutcome) : SignatureStats :=
  match outcome with
  | .PassStable => { stats with total := stats.total + 1, passStable := stats.passStable + 1 }
  | .HoldStabilized => { stats with total := stats.total + 1, holdStabilized := stats.holdStabilized + 1 }
  | .Rejected => { stats with total := stats.total + 1, rejected := stats.rejected + 1 }
  | .SurvivalTransition => { stats with total := stats.total + 1, survival := stats.survival + 1 }
  | .FlameTransition => { stats with total := stats.total + 1, flame := stats.flame + 1 }

/-- 
  Decision policy bounded analytically over integer multiplication instead of floats.
  rejectBadRate = 0.60  -->  bad * 10 >= total * 6
  passGoodRate  = 0.70  -->  good * 10 >= total * 7 
-/
def recommendForSig (stats : SignatureStats) : RelationClass :=
  if stats.total < 4 then .Hold
  else
    let bad := stats.rejected + stats.survival + stats.flame
    let good := stats.passStable + stats.holdStabilized
    
    if bad * 10 >= stats.total * 6 then .Reject
    else if good * 10 >= stats.total * 7 then .Pass
    else .Hold

-- Tests verify boundary execution correctly mapping to Float expectations
#eval recommendForSig { total := 10, passStable := 0, holdStabilized := 0, rejected := 6, survival := 0, flame := 0 }
#eval recommendForSig { total := 10, passStable := 7, holdStabilized := 0, rejected := 1, survival := 0, flame := 0 }

end Semantics.RelationMaskTrainer
