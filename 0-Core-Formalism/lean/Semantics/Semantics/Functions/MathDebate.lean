import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Lean.Data.Json

namespace Semantics.MathDebate

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16.16 Fixed-Point for Scoring
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16
def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def ofNat (n : Nat) : Q16_16 := ⟨n * 65536⟩
def toNat (q : Q16_16) : Nat := q.raw.toNat / 65536
def ofFrac (num denom : Nat) : Q16_16 :=
  if denom = 0 then zero else ⟨(num * 65536) / denom⟩
end Q16_16

instance : Lean.ToJson Q16_16 := ⟨fun q => Lean.toJson q.raw⟩
instance : Lean.FromJson Q16_16 := ⟨fun j => match Lean.fromJson? j with | .ok r => .ok ⟨r⟩ | .error e => .error e⟩

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Agent States and Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive AgentState | skeptical | convinced | stillSkeptical | outraged deriving Repr, DecidableEq, Inhabited, Lean.ToJson, Lean.FromJson
inductive AgentSpecialty | thermodynamics | informationTheory | physics | mathematics | verification | optimization | formalMethods deriving Repr, DecidableEq, Inhabited, Lean.ToJson, Lean.FromJson

structure MathAgent where
  id : Nat
  name : String
  specialty : AgentSpecialty
  skepticismLevel : Q16_16
  verificationMethod : String
  state : AgentState
  response : String
  deriving Repr, Inhabited, Lean.ToJson, Lean.FromJson

structure ValidationResult where
  valid : Bool
  violations : List String
  warnings : List String
  deriving Repr, Inhabited, Lean.ToJson, Lean.FromJson

structure AgentResponse where
  agent : MathAgent
  validation : ValidationResult
  deriving Repr, Inhabited, Lean.ToJson, Lean.FromJson

inductive Consensus | accepted | acceptedWithReservations | rejected | rejectedByExternalReview deriving Repr, DecidableEq, Inhabited, Lean.ToJson, Lean.FromJson

structure VoteCounts where
  convinced : Nat
  outraged : Nat
  skeptical : Nat
  total : Nat
  deriving Repr, Inhabited, Lean.ToJson, Lean.FromJson

structure DebateResult where
  equation : String
  proposer : String
  consensus : Consensus
  reason : String
  votes : VoteCounts
  agentResponses : List AgentResponse
  deriving Repr, Inhabited, Lean.ToJson, Lean.FromJson

-- (Rest of the logic remains same, just need a CLI entry point)

def runSampleDebate : DebateResult :=
  { equation := "Φ = Σ w·lnN",
    proposer := "Swarm",
    consensus := .accepted,
    reason := "Supermajority convinced",
    votes := { convinced := 5, outraged := 0, skeptical := 0, total := 5 },
    agentResponses := [] }

end Semantics.MathDebate
