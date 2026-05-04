# Oracle Interrogation IDPC v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec records the IDPC operator — **Inverse Delta Phi over Cosine** — as part of the OTOM oracle-interrogation path.

## Origin note

The operator began with the intuition chain:

```text
Delphi
→ Delta Phi
→ Inverse Delta Phi over Cosine
```

This is not treated as a mystical claim. It is treated as a naming event that revealed the correct architectural placement: **oracle interrogation**.

Delphi matters here because an oracle is not just a database. An oracle is interrogated through a question, a perturbation, a response, and a reconciliation step.

The deeper point is that historical oracles were usually wrong at the literal-answer layer, but sometimes right enough to reveal a hidden pattern. OTOM should preserve that distinction.

## Core thesis

Interrogation is inherently about change.

A question perturbs the oracle state. An answer is useful only if the resulting change remains coherent with the query context.

IDPC measures:

```text
coherence per phase displacement
```

The stable operator is:

```text
IDPC = cos(theta) / (DeltaPhi + epsilon)
```

For the integer/fixed-path scaffold:

```text
IDPC_q = alignment * scale / (deltaPhi + epsilon)
```

Where:

```text
alignment = encoder-supplied clipped/rescaled cosine alignment
DeltaPhi = phase / semantic displacement induced by interrogation
epsilon = stabilizer preventing division by zero
scale = integer precision multiplier
```

## Fallible oracle reading

The oracle is not trusted because it is always right.

The oracle is useful because its answer can be wrong at the surface layer while still perturbing the interrogator toward a deeper invariant.

So the interrogation target is not:

```text
Was the answer literally correct?
```

It is:

```text
Did the wrong-or-partial answer expose a deeper pattern that survives later receipts?
```

This creates three layers:

```text
literal answer layer
pattern-detection layer
receipt-validation layer
```

A fallible oracle may fail the first layer while still contributing signal at the second. It only earns stronger claim state at the third.

In short:

```text
mostly wrong
→ sometimes right enough
→ deeper pattern detected
→ receipts decide whether the pattern was real
```

This is the Delphi-compatible interpretation. The oracle is a noisy phase-transition instrument, not an authority.

## Why this belongs in oracle interrogation

Without change, there is no interrogation.

A static lookup asks:

```text
What value is stored?
```

Oracle interrogation asks:

```text
What changes when this question is applied?
Did the answer move the oracle state coherently?
Did the answer preserve the declared scope?
Did the answer create a new contradiction, adapter, or phase shift?
Did even a wrong answer reveal a pattern that can be receipted later?
```

So IDPC is not merely a stability score. It is a **question-answer transition score** and a **deeper-pattern detection gate**.

## OTOM mapping

```text
Question
→ perturb oracle state
→ answer emitted
→ literal correctness checked
→ phase displacement measured
→ alignment checked
→ deeper-pattern candidate extracted
→ IDPC computed
→ receipt / Warden gate
```

| Component | Meaning |
|---|---|
| Question | Controlled perturbation applied to oracle state |
| Oracle state before | Pre-query phase/coherence marker |
| Oracle state after | Post-answer phase/coherence marker |
| DeltaPhi | Magnitude of semantic/phase displacement |
| Cosine alignment | Directional agreement between query vector and answer vector |
| Literal correctness | Surface truth value of the answer |
| Pattern candidate | Possible deeper invariant exposed by the answer |
| IDPC | Coherence retained per unit change |
| Receipt | Evidence that the pattern survived later validation |

## Change-centered reading

The phrase “changes are inherently about this” maps to the following rule:

```text
Any meaningful oracle answer is a constrained state transition.
```

So the evaluation target is not just the answer text. It is:

```text
before_state → after_state
```

IDPC asks whether that transition is coherent.

High IDPC means:

```text
small DeltaPhi
high alignment
stable scope
low contradiction load
```

Low IDPC means:

```text
large DeltaPhi
low alignment
scope drift
possible contradiction or hallucinated transition
```

But high IDPC does not mean the answer is literally true. It means the transition is coherent enough to nominate a pattern for receipt validation.

## Deeper-pattern detector

IDPC should be paired with a pattern-survival gate:

```text
surface answer may be wrong
pattern candidate may be useful
receipt determines promotion
```

Suggested result states:

```text
literal_fail_pattern_fail
literal_fail_pattern_candidate
literal_pass_pattern_candidate
receipted_pattern
```

The critical state is:

```text
literal_fail_pattern_candidate
```

This is the place where oracles historically mattered: not because they answered cleanly, but because they forced a productive reorientation.

## Warden gates

### Gate 1 — Not a mystical oracle claim

Blocked claim:

```text
Delphi proves the operator.
```

Allowed claim:

```text
The Delphi intuition supplied a useful name and architectural placement for an oracle-interrogation transition metric.
```

### Gate 2 — Not answer-only scoring

Blocked claim:

```text
IDPC scores the answer in isolation.
```

Allowed claim:

```text
IDPC scores the query-answer state transition.
```

### Gate 3 — Cosine is encoder-supplied

Blocked claim:

```text
Lean computes semantic cosine similarity directly.
```

Allowed claim:

```text
The encoder supplies a bounded alignment score; Lean checks the arithmetic and gates.
```

### Gate 4 — DeltaPhi requires declared scope

Blocked claim:

```text
Any phase change is bad.
```

Allowed claim:

```text
A phase change is evaluated relative to declared scope; high change with low alignment is suspect, while high change with high alignment may indicate a useful discovery.
```

### Gate 5 — Mostly wrong is not useless

Blocked claim:

```text
If the oracle was wrong, discard the entire interrogation.
```

Allowed claim:

```text
A wrong answer can still produce a pattern candidate if the induced transition is coherent and later receipts validate the deeper invariant.
```

### Gate 6 — Pattern candidate is not reviewed truth

Blocked claim:

```text
The oracle exposed a pattern, therefore the pattern is true.
```

Allowed claim:

```text
The oracle exposed a pattern candidate; promotion requires receipts.
```

## Lean artifact

Paired module:

```text
0-Core-Formalism/lean/Semantics/Semantics/OracleInterrogation.lean
```

The module defines:

```text
OracleState
OracleQuestion
OracleAnswer
OracleInterrogation
IDPCInput
OracleInterrogationResult
PatternSignal
PatternStatus
```

And the core operators:

```text
idpcInputOfInterrogation
idpcScore
evaluateInterrogationStable
patternStatus
```

Key theorem shapes:

```text
zero_alignment_idpc_zero
idpc_denominator_monotone_nonincreasing
deltaPhi_monotone_nonincreasing
valid_idpc_score_le_scaled_alignment
literal_failure_can_still_be_pattern_candidate
```

These encode the basic lawfulness guardrails:

```text
no alignment -> no IDPC signal
more displacement weakly lowers score at fixed alignment
valid inputs remain bounded by scaled alignment
literal failure does not logically erase pattern candidacy
```

## Relation to prior OTOM artifacts

Market filter:

```text
behavioral match under changing market window
```

Alphabet reduction:

```text
symbol deletion under biological composition change
```

Receipt core:

```text
promotion change requires proof receipt
```

Oracle IDPC:

```text
question-answer transition change requires coherence receipt
```

The shared invariant is:

```text
change must pay for itself with preserved structure
```

The deeper oracle invariant is:

```text
wrong surface answers can still reveal candidate structure, but only receipts can promote the structure.
```

## Strongest formulation

> IDPC is the oracle-interrogation operator that measures how much directional coherence survives a question-induced phase change, including cases where a mostly wrong answer is still right enough to expose a deeper pattern.

That is the clean form to carry forward.
