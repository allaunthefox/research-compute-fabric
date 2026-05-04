/-! # DeepSeek Budget Calculator

A small executable model of DeepSeek-V4 API pricing for hobby-scale planning.
Mirrors the Python constants in
`5-Applications/tools-scripts/llm/deepseek_review_adapter.py` (`PRICING_USD_PER_1M`).

Pricing source (fetched 2026-05-03):
  https://api-docs.deepseek.com/quick_start/pricing

The Lean side is the *spec*; the Python side is the *runtime*. If they ever
disagree on cost, the spec wins until updated together.

## Main definitions

- `ModelPricing`     : per-model rates in USD / million tokens
- `v4Flash`, `v4Pro` : the two production tiers
- `QuerySpec`        : (model, cached_input_tokens, fresh_input_tokens, output_tokens)
- `queryCost`        : USD for a single query
- `WorkflowSpec`     : a list of QuerySpecs labelled by purpose
- `workflowCost`     : USD for a full workflow

## Example

```
#eval queryCost ⟨v4Pro, 21000, 1000, 3000⟩          -- first cached review
#eval workflowCost (eveningReview 21000)             -- one full evening
#eval workflowCost (monthlyHobbyRocket 21000)        -- one month
```
-/

namespace Semantics.DeepSeek

/-- Per-model pricing in USD per 1,000,000 tokens. -/
structure ModelPricing where
  name : String
  inputCacheHitPer1M : Float
  inputCacheMissPer1M : Float
  outputPer1M : Float
deriving Repr

/-- DeepSeek-V4-Flash: cheap and fast.  $0.0028 / $0.14 / $0.28 per 1M tokens. -/
def v4Flash : ModelPricing :=
  { name := "deepseek-v4-flash"
    inputCacheHitPer1M := 0.0028
    inputCacheMissPer1M := 0.14
    outputPer1M := 0.28 }

/-- DeepSeek-V4-Pro: more capable, with a 75% discount through 2026/05/31.
    Effective rates: $0.003625 / $0.435 / $0.87 per 1M tokens. -/
def v4Pro : ModelPricing :=
  { name := "deepseek-v4-pro"
    inputCacheHitPer1M := 0.003625
    inputCacheMissPer1M := 0.435
    outputPer1M := 0.87 }

/-- A single query against one model.

    `cachedInputTokens` : tokens in the cached prefix (project context, etc.)
    `freshInputTokens`  : tokens in the new part of the prompt this turn
    `outputTokens`      : tokens generated in the response

    On the first query in a session, the entire prefix is cache-miss, so callers
    should set `cachedInputTokens := 0` and put everything in `freshInputTokens`.
    On subsequent queries within the cache TTL, the prefix becomes cache-hit. -/
structure QuerySpec where
  model : ModelPricing
  cachedInputTokens : Nat
  freshInputTokens : Nat
  outputTokens : Nat
deriving Repr

/-- Cost of a single query in USD.

    cost = cached_in / 1M · cache_hit_rate
         + fresh_in  / 1M · cache_miss_rate
         + output    / 1M · output_rate -/
def queryCost (q : QuerySpec) : Float :=
  let p := q.model
  let cached := (Float.ofNat q.cachedInputTokens) / 1000000.0 * p.inputCacheHitPer1M
  let fresh  := (Float.ofNat q.freshInputTokens)  / 1000000.0 * p.inputCacheMissPer1M
  let out    := (Float.ofNat q.outputTokens)      / 1000000.0 * p.outputPer1M
  cached + fresh + out

/-- A labelled workflow: a sequence of queries with a human-readable purpose. -/
structure WorkflowSpec where
  name : String
  queries : List QuerySpec
deriving Repr

/-- Total USD cost of a workflow. -/
def workflowCost (w : WorkflowSpec) : Float :=
  w.queries.foldl (fun acc q => acc + queryCost q) 0.0

/-- Per-query cost breakdown (useful for receipts and audit trails). -/
def workflowBreakdown (w : WorkflowSpec) : List (String × Float) :=
  w.queries.map (fun q => (q.model.name, queryCost q))

/-! ## Hobby-rocket workflow templates

The audit-defended pattern: one cache-miss "fresh-load" v4-flash review per
evening, plus a few cache-hit follow-ups, optionally escalating one query
to v4-pro for adversarial review of substantive artifacts.

`projectContextTokens` is your stable cached prefix size — for the current
Burgers verifier project this is ~21,000 tokens (verifier code + audit code +
DAG code + findings + repro analysis). -/

/-- Single evening of review work:
    1× cache-miss flash load + 3× cache-hit flash follow-ups + 1× cache-hit pro adversarial. -/
def eveningReview (projectContextTokens : Nat) : WorkflowSpec :=
  { name := "evening_review"
    queries := [
      -- First query of the evening warms the cache (everything is cache-miss).
      ⟨v4Flash, 0, projectContextTokens + 1000, 3000⟩,
      -- Three follow-ups re-use the cache.
      ⟨v4Flash, projectContextTokens, 1000, 3000⟩,
      ⟨v4Flash, projectContextTokens, 1000, 3000⟩,
      ⟨v4Flash, projectContextTokens, 1000, 3000⟩,
      -- One adversarial-review escalation to v4-pro on a substantive artifact.
      ⟨v4Pro,   projectContextTokens, 1500, 5000⟩
    ] }

/-- A month of evening reviews (~22 working evenings). -/
def monthlyHobbyRocket (projectContextTokens : Nat) : WorkflowSpec :=
  { name := "monthly_hobby_rocket"
    queries := List.replicate 22 (eveningReview projectContextTokens) |>.flatMap (·.queries) }

/-- Worst-case month if we forget to cache and every query is a fresh load. -/
def monthlyNoCachePessimistic (projectContextTokens : Nat) : WorkflowSpec :=
  { name := "monthly_no_cache_pessimistic"
    queries := List.replicate (22 * 5) ⟨v4Flash, 0, projectContextTokens + 1000, 3000⟩
               ++ List.replicate 22 ⟨v4Pro, 0, projectContextTokens + 1500, 5000⟩ }

/-! ## #eval examples (run with `lean --run` or in editor) -/

-- Single first-query (cache miss) on v4-pro, 21k context + 1k prompt + 3k response.
-- Expected ~$0.012.
#eval queryCost ⟨v4Pro, 0, 22000, 3000⟩

-- Same query as a cache-hit follow-up. Expected ~$0.003.
#eval queryCost ⟨v4Pro, 21000, 1000, 3000⟩

-- One full evening with ~21k cached project context. Expected ~$0.013.
#eval workflowCost (eveningReview 21000)

-- One month of evenings. Expected ~$0.28.
#eval workflowCost (monthlyHobbyRocket 21000)

-- Worst-case (no caching) month. Expected ~$3-4.
#eval workflowCost (monthlyNoCachePessimistic 21000)

/-! ## Empirical sanity check (in lieu of an over-Float theorem)

    Float arithmetic in Lean is not a field (rounding, no associativity in the
    deep proof sense), so we don't try to formally prove `cache_hit < cache_miss`.
    Instead we provide a concrete `#eval` witness: for the v4-pro example query,
    the cached form is strictly cheaper than the equivalent fully-fresh form. -/

def cacheHitWitness : Bool :=
  queryCost ⟨v4Pro, 21000, 1000, 3000⟩ < queryCost ⟨v4Pro, 0, 22000, 3000⟩

#eval cacheHitWitness  -- expect: true

end Semantics.DeepSeek
