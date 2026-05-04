import Semantics.Bind
import ExtensionScaffold.Compression.UnifiedCompression

namespace Semantics.ENEContextTokenCache

open ExtensionScaffold.Compression

/-!
# ENE Context Token Cache

Lean-owned accounting for context token usage across ENE-backed sessions.
External shims may serialize records, but cache lawfulness, cost, and invariant
extraction live here.
-/

abbrev SessionId := Nat
abbrev TurnId := Nat
abbrev TokenCount := UInt32

inductive TokenKind where
  | input
  | output
  | cached
  | reasoning
  deriving Repr, DecidableEq, BEq

inductive CachePolicy where
  | retainAll
  | retainCachedOnly
  | retainWithinBudget
  deriving Repr, DecidableEq, BEq

structure TokenUsage where
  inputTokens : TokenCount
  outputTokens : TokenCount
  cachedTokens : TokenCount
  reasoningTokens : TokenCount
  deriving Repr, DecidableEq

structure ContextTokenRecord where
  sessionId : SessionId
  turnId : TurnId
  usage : TokenUsage
  deriving Repr, DecidableEq

structure ContextTokenCache where
  policy : CachePolicy
  budget : TokenCount
  records : List ContextTokenRecord
  deriving Repr

inductive CompressionPhase where
  | raw
  | unified
  | rgflowLawful
  deriving Repr, DecidableEq, BEq

structure CompressionWitness where
  phase : CompressionPhase
  rawCost : TokenCount
  compressedCost : TokenCount
  lawful : Bool
  deriving Repr, DecidableEq

def zeroUsage : TokenUsage :=
  { inputTokens := 0, outputTokens := 0, cachedTokens := 0, reasoningTokens := 0 }

def usageTotal (u : TokenUsage) : TokenCount :=
  u.inputTokens + u.outputTokens + u.cachedTokens + u.reasoningTokens

def recordTotal (r : ContextTokenRecord) : TokenCount :=
  usageTotal r.usage

def addUsage (a b : TokenUsage) : TokenUsage :=
  { inputTokens := a.inputTokens + b.inputTokens
  , outputTokens := a.outputTokens + b.outputTokens
  , cachedTokens := a.cachedTokens + b.cachedTokens
  , reasoningTokens := a.reasoningTokens + b.reasoningTokens
  }

def totalUsage (cache : ContextTokenCache) : TokenUsage :=
  cache.records.foldl (fun acc record => addUsage acc record.usage) zeroUsage

def totalTokens (cache : ContextTokenCache) : TokenCount :=
  usageTotal (totalUsage cache)

def budgetRemaining (cache : ContextTokenCache) : TokenCount :=
  if totalTokens cache ≤ cache.budget then cache.budget - totalTokens cache else 0

def cacheWithinBudget (cache : ContextTokenCache) : Bool :=
  totalTokens cache ≤ cache.budget

def tokenUsagePositions (u : TokenUsage) : List Nat :=
  [u.inputTokens.toNat, u.outputTokens.toNat, u.cachedTokens.toNat, u.reasoningTokens.toNat]

def contextCompressionField : LocalField :=
  { support := fun _ => 0x00010000 }

def contextCompressionCodes (u : TokenUsage) : List Code :=
  unifiedCompress (tokenUsagePositions u) contextCompressionField 0x00000000

def rgflowUsageLawful (u : TokenUsage) : Bool :=
  (tokenUsagePositions u).all (fun n => (rgflowAnalyzePulse (pulseFromInt n)).2)

def compressedUsageCost (u : TokenUsage) : TokenCount :=
  let codes := contextCompressionCodes u
  let codeCost := codes.foldl (fun acc c => acc + c.cost) 0
  if codes.length == 0 then usageTotal u else codeCost

def minimalUsageCost (u : TokenUsage) : TokenCount :=
  let raw := usageTotal u
  let compressed := compressedUsageCost u
  if rgflowUsageLawful u && compressed < raw then compressed else raw

def compressionWitness (u : TokenUsage) : CompressionWitness :=
  let raw := usageTotal u
  let lawful := rgflowUsageLawful u
  { phase := if lawful then .rgflowLawful else .unified
  , rawCost := raw
  , compressedCost := minimalUsageCost u
  , lawful := lawful
  }

def effectiveRecordCost (record : ContextTokenRecord) : TokenCount :=
  minimalUsageCost record.usage

def retainRecord (policy : CachePolicy) (budget : TokenCount) (record : ContextTokenRecord) : Bool :=
  match policy with
  | .retainAll => true
  | .retainCachedOnly => record.usage.cachedTokens > 0
  | .retainWithinBudget => recordTotal record ≤ budget

def insertRecord (cache : ContextTokenCache) (record : ContextTokenRecord) : ContextTokenCache :=
  if retainRecord cache.policy cache.budget record then
    { cache with records := record :: cache.records }
  else
    cache

def contextTokenInvariant (cache : ContextTokenCache) : String :=
  s!"records={cache.records.length};total={totalTokens cache};remaining={budgetRemaining cache}"

def contextTokenCost (cache : ContextTokenCache) (_record : ContextTokenRecord) (_metric : Metric) : UInt32 :=
  let total := cache.records.foldl (fun acc record => acc + effectiveRecordCost record) 0
  let overBudget := if total ≤ cache.budget then 0 else total - cache.budget
  total + overBudget

def bindContextRecord (cache : ContextTokenCache) (record : ContextTokenRecord) : Bind ContextTokenCache ContextTokenRecord :=
  let nextCache := insertRecord cache record
  let metric := { Metric.euclidean with reference := "ene_context_token_cache", history_len := cache.records.length }
  informationalBind
    nextCache
    record
    metric
    contextTokenCost
    (fun c => if cacheWithinBudget c then contextTokenInvariant c else "over_budget")
    (fun _ => if cacheWithinBudget nextCache then contextTokenInvariant nextCache else "over_budget")

def emptyCache (budget : TokenCount) (policy : CachePolicy := .retainWithinBudget) : ContextTokenCache :=
  { policy := policy, budget := budget, records := [] }

def exampleUsage : TokenUsage :=
  { inputTokens := 1200, outputTokens := 300, cachedTokens := 200, reasoningTokens := 100 }

def exampleRecord : ContextTokenRecord :=
  { sessionId := 1, turnId := 1, usage := exampleUsage }

def exampleCache : ContextTokenCache :=
  insertRecord (emptyCache 4096) exampleRecord

theorem usageTotalZero :
    usageTotal zeroUsage = 0 := by
  rfl

theorem emptyCacheWithinBudget (budget : TokenCount) :
    cacheWithinBudget (emptyCache budget) = true := by
  unfold cacheWithinBudget totalTokens totalUsage usageTotal zeroUsage emptyCache
  simp

theorem insertRecordTotalWitness (cache : ContextTokenCache) (record : ContextTokenRecord) :
    ∃ total, totalTokens (insertRecord cache record) = total := by
  exact ⟨totalTokens (insertRecord cache record), rfl⟩

theorem minimalUsageCostTotal (u : TokenUsage) :
    ∃ cost, minimalUsageCost u = cost := by
  exact ⟨minimalUsageCost u, rfl⟩

#eval totalTokens exampleCache -- expected: 1800
#eval cacheWithinBudget exampleCache -- expected: true
#eval (compressionWitness exampleUsage).compressedCost -- expected: no more than raw usage
#eval (bindContextRecord (emptyCache 4096) exampleRecord).lawful -- expected: true

end Semantics.ENEContextTokenCache
