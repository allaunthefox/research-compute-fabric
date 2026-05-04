# Receipt Ledger Promotion Gate v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec records the receipt-ledger invariant recovered from the Lean failure log around the geometric compression workspace.

The target invariant is:

```text
A trial cannot be promoted to REVIEWED unless the persistent receipt ledger contains a proof receipt for the target.
```

This spec is intentionally separated from the full geometric compression workspace so the invariant can be preserved and formalized without depending on a missing or moving module path.

## Core invariant

Promotion is receipt-gated:

```text
candidate trial
+ ledger proof receipt exists for target
→ may become REVIEWED
```

But:

```text
candidate trial
+ no proof receipt in ledger
→ cannot become REVIEWED
```

The model blocks promotion by agreement, narrative plausibility, benchmark-looking output, metaphor strength, or unverified oracle consensus.

## Minimal model

Let:

```text
trial.status ∈ {HOLD, CANDIDATE, REVIEWED, REJECTED}
ledger : targetId -> List Receipt
receipt.kind ∈ {proof, benchmark, measurement, oracle, note}
```

Define:

```text
ledgerHasProofReceipt(ledger, targetId) = true
```

iff the ledger contains a proof receipt bound to `targetId`.

The promotion function is:

```text
promoteTrialLedger(trial, ledger, targetId) =
  REVIEWED    if trial.status = CANDIDATE and ledgerHasProofReceipt(ledger,targetId)
  trial       otherwise
```

The required theorem shape is:

```text
promoteTrialLedger(trial, ledger, targetId).status = REVIEWED
→ ledgerHasProofReceipt(ledger,targetId) = true
```

In words:

```text
If promotion produced REVIEWED, the ledger must have contained the proof receipt.
```

## Why this theorem matters

This invariant is the bridge between OTOM's Warden doctrine and executable review state.

Without this theorem, a system can accidentally encode:

```text
looks good
sounds plausible
multiple agents agree
therefore REVIEWED
```

The gate forbids that.

The only admissible shape is:

```text
proof receipt exists
therefore REVIEWED is permitted
```

## Recommended Lean proof strategy

The Lean failure log suggests the previous proof got stuck by destructing enum equality directly inside a larger theorem.

The robust approach is to split the proof into small lemmas:

```text
1. prove promotion against a simple receipt list
2. wrap that lemma with ledger lookup
3. avoid brittle dependent elimination over status equality
4. optionally use a Bool isReviewed helper
```

Suggested theorem names:

```text
promoteTrial_reviewed_implies_receipt
promoteTrialLedger_preserves_receipt_gate
reviewed_bool_implies_receipt
```

## Claim-state boundary

### Blocked claims

```text
LLM agreement promotes a claim to REVIEWED.
A benchmark-looking output promotes a claim to REVIEWED without a receipt.
A metaphor-derived operator promotes itself to REVIEWED.
A passing UI/demo implies proof receipt exists.
```

### Allowed claims

```text
A candidate can be promoted only through a proof receipt gate.
The persistent ledger is the source of promotion authorization.
A missing receipt preserves HOLD/CANDIDATE state rather than REVIEWED state.
Lean should prove the finite gate, not the full scientific claim.
```

## Strongest formulation

> The Receipt Ledger Promotion Gate enforces that REVIEWED status is not a model opinion. It is a ledger-backed state transition requiring a proof receipt bound to the target under review.
