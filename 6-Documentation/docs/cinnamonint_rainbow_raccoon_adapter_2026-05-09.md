# Cinnamonint Rainbow Raccoon Adapter Prior

Status: `HOLD_EXTERNAL_PRIOR`

Source: <https://github.com/CinnamonInt/Cinnamonint/tree/master>

## Why It Matters

Cinnamonint is a deterministic sentence-reduction engine. It scans a sentence
for registered token keywords, selects a token by priority and position, runs
that token handler, replaces the handled part of the sentence, logs the
iteration, and repeats until no tokens remain.

That gives the Research Stack a useful external prior for the Rainbow Raccoon
Compiler because it has the same general shape:

```text
input surface
-> token discovery
-> priority/route selection
-> local handler transform
-> iteration receipt
-> final reduced output
```

The important part is not the Python implementation. The useful idea is the
receipt shape: one token, one local grammar, one bounded transform, one replay
record.

## Clean-Room Mapping

No Cinnamonint code is imported into the stack. The repository is GPL-3.0, and
the stack should treat it as a reference prior unless an explicit compatibility
decision is made later.

Mapping:

| Cinnamonint Surface | Research Stack Surface |
|---|---|
| Registered token | Finite logogram/operator entry |
| Token aliases | Grammar surface names |
| Token priority | Route-selection weight |
| Handler `handle(sentence)` | Local transformation primitive |
| One-token-per-call rule | Single-step bind transition |
| Iteration log | Replay receipt |
| Learn mode | Candidate operator synthesis |
| Token test suite | Promotion gate |
| Workshop mode | Mutable candidate registry |
| Hardened mode | Frozen receipt/replay registry |
| Subprocess isolation | Handler boundary / sandbox gate |
| Approval table | Human-reviewed execution gate |

## Rainbow Raccoon Compiler Adapter

The adapter concept is:

```text
sentence_or_logogram_stream
-> tokenize_against_finite_registry
-> select_next_operator(priority, position, route_cost)
-> apply_one_local_transform
-> emit_iteration_receipt
-> repeat_until_closed_or_nan0
```

RRC should keep this as a finite typed surface rather than open string matching:

```text
TokenId : Fin n
AliasId : Fin m
Priority : Q0_16 or bounded UInt
StepReceipt := input_hash + token_id + handler_id + output_hash + residual
```

Promotion gate:

```text
promote iff all token fixtures pass
        and replay receipts close
        and no destructive/imported handler runs without approval
        and hardened registry hash is stable
```

NaN0 gate:

```text
NaN0 iff unknown token required for progress
       or iteration bound exceeded
       or handler receipt missing
       or output hash fails replay
       or destructive/download/upload gate is unapproved
```

## Fit With Existing Stack Work

Cinnamonint is a strong external prior for:

- whitespace-zero grammar: tokens can be counted instead of space-delimited
  once the grammar has explicit boundaries.
- logogram compilation: each logogram can behave like a token with a bounded
  handler and replay receipt.
- AMMR receipts: every reduction step can become a leaf; folded iteration
  segments become peaks.
- Rainbow Raccoon compiler triage: generated operators enter workshop mode,
  then only fixture-passing operators move to hardened mode.
- FPGA/prover cycle: deterministic token steps are small enough to lower into
  fixed-point or finite-state witnesses later.

## Claim Boundary

This is an architecture prior, not an imported dependency and not a proof that
Cinnamonint itself satisfies stack invariants. It supports a clean-room adapter:
deterministic token reduction with bounded local transforms and replayable
iteration receipts.

References:

- Cinnamonint README, GitHub, retrieved 2026-05-09.
- Cinnamonint design document, GitHub, retrieved 2026-05-09.
- Cinnamonint AGENTS.md, GitHub, retrieved 2026-05-09.
- Cinnamonint LICENSE, GPL-3.0, GitHub, retrieved 2026-05-09.
