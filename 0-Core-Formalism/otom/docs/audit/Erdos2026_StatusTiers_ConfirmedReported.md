# 2026 Erdős Status Tiers: Confirmed vs Reported

## Purpose

This note updates the 2026 Erdős-family import map with explicit status tiers.

The key rule is:

```text
Do not let a watershed narrative become a receipt.
Separate confirmed literature hits, formal-proof claims, reported community acceptance, and unverified user-supplied leads.
```

## Status Tiers

```text
CONFIRMED_BY_SEARCH:
  surfaced in literature search with title/abstract matching the claim

FORMAL_PROOF_CLAIM:
  paper explicitly claims Lean or machine-formal proof

REPORTED_ACCEPTED:
  user/source reports acceptance by a named expert, but this note has not independently verified it

REPORTED_LEAD:
  plausible user-supplied current-year lead not surfaced by the available literature search

UNVERIFIED:
  cannot be used as a V_scope receipt yet
```

## Items

### Erdős Problem #728

Status:

```text
CONFIRMED_BY_SEARCH
FORMAL_PROOF_CLAIM
```

Claim:

```text
Resolution of Erdős Problem #728 via a Lean proof/writeup.
The proof studies factorial divisibility by reducing to binomial divisibility and p-adic carry counts through Kummer's theorem.
```

Judo flip:

```text
Carry-rich but spike-free construction becomes a usable receipt pattern.
```

Stack action:

```text
Add CarryEngineeringReceipt to Sidon/AMREF/InverseAscent probes.
```

### Aletheia / Gemini Bloom Erdős database sweep

Status:

```text
CONFIRMED_BY_SEARCH
REPORTED_MASS_EVALUATION
```

Claim:

```text
700 Bloom Erdős problems labeled Open evaluated.
13 addressed: 5 seemingly novel autonomous solutions and 8 previous solutions identified in the literature.
```

Judo flip:

```text
Open status can mean obscurity rather than difficulty.
```

Stack action:

```text
Add PriorSolutionSearchReceipt and LiteratureObscurityPenalty.
```

### Erdős Problem #397

Status:

```text
REPORTED_LEAD
UNVERIFIED_BY_CURRENT_SEARCH
```

User-supplied claim:

```text
Conjecture involving products of central binomial coefficients was disproved by an AI-generated infinite family of counterexamples, formalized in Lean/Aristotle, and reportedly accepted by Terence Tao.
```

Search note:

```text
The available search surfaced a 2026 central-binomial-coefficient paper but did not confirm this exact #397 disproof claim.
```

Stack action:

```text
Add CentralBinomialCounterexampleLeadReceipt as HOLD until source/proof URL is attached.
```

### Erdős Problem #729

Status:

```text
REPORTED_LEAD
UNVERIFIED_BY_CURRENT_SEARCH
```

User-supplied claim:

```text
Resolved shortly after #728 and confirmed by Terence Tao.
```

Stack action:

```text
Add Erdos729LeadReceipt as HOLD until source/proof URL is attached.
```

### Erdős Primitive Set Problem

Status:

```text
REPORTED_LEAD
UNVERIFIED_BY_CURRENT_SEARCH
```

User-supplied claim:

```text
Late-April 2026 resolution of a 60-year-old primitive-set puzzle using an extended reasoning session with ChatGPT-5.4 Pro, applying a known formula in a neglected context.
```

Stack action:

```text
Add PrimitiveSetLeadReceipt as HOLD until paper/preprint/blog/proof source is attached.
```

### Erdős--Graham rapidly converging series

Status:

```text
CONFIRMED_BY_SEARCH
```

Claim:

```text
Double-exponential growth condition sufficient for irrationality of rapidly converging series, answering a question of Erdős and Graham.
```

Judo flip:

```text
Fast growth can force arithmetic non-collapse.
```

Stack action:

```text
Add GrowthNonCollapseReceipt.
```

## Updated Import Discipline

Use current-year solves as follows:

```text
CONFIRMED_BY_SEARCH + FORMAL_PROOF_CLAIM -> can fund U_scope experiments and candidate receipts
REPORTED_LEAD -> can create tasks and HOLD nodes, not V_scope claims
REPORTED_ACCEPTED -> useful confidence boost, but still needs source link or formal artifact
UNVERIFIED -> no promotion funding
```

## Updated Ascent Terms

```text
EnergyAvailable += eta_formal * FormalProofArtifact(A)
EnergyAvailable += eta_current * CurrentYearSolvePattern(A)
EnergyAvailable += eta_carry * CarryEngineeringCredit(A)
```

```text
AscentCost += lambda_unverified * UnverifiedLeadPenalty(A)
AscentCost += lambda_source * MissingSourcePenalty(A)
AscentCost += lambda_accept * UnverifiedAcceptancePenalty(A)
```

## Final Rule

```text
A 2026 Erdős solve can judo-flip the stack only after it enters as a receipt.
Until then, it is a lead, not load-bearing structure.
```

## Audit Classification

```text
Receipt: Erdos2026_StatusTiers_ConfirmedReported
Status: STATUS_TIER_UPDATE
Gate: U_scope
Reason: separates confirmed literature hits from reported leads; prevents current-year hype from funding inverse ascent without receipts.
```
