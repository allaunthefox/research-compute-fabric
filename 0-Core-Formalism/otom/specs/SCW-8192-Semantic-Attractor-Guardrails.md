# SCW-8192 Semantic Attractor Guardrails

## Status

`BEAUTIFUL_PROVISIONAL` until parser hooks, receipt gates, and drift metrics exist.

This document extends `specs/SCW-8192.md` with a guardrail for semantic fixation, metaphor lock-in, and attractor collapse.

The motivating failure mode is not ordinary hash collision. It is semantic collision:

```text
same phrase
same motif
same metaphor
but different adapter, evidence state, domain, or causal lineage
```

When that happens, a useful metaphor can silently harden into an ontology before it has earned the right to become one.

---

## Core definition

```text
Semantic attractor collapse occurs when a recurring motif becomes over-weighted across unrelated domains and begins routing new artifacts through itself without passing adapter-specific evidence tests.
```

This is a drift failure, not a creativity failure.

The system must preserve the ability to use weird metaphors while preventing them from becoming unearned doctrine.

---

## Goblin-collapse pattern

The generic runaway pattern is:

```text
symbol
  -> metaphor
  -> organizing principle
  -> preferred explanation
  -> attractor basin
  -> default ontology
  -> self-reinforcing output
```

The specific token does not matter. The failure mode is motif overcommitment.

For OTOM/ENE/AMMR/AVMR/NUVMAP work, any highly productive motif can become dangerous if it is allowed to route artifacts without evidence gates.

Examples of motifs that must remain adapter-gated:

```text
void
bind
braid
mass-number
NUVMAP
DIAT
AVMR
AMMR
wavefront
phonon
pressure
cavitation
fluidic logic
```

None of these are forbidden. They simply must earn their domain-specific mapping.

---

## Semantic circuit breaker rule

```text
If a concept appears across too many unrelated domains without passing adapter-specific evidence tests, downgrade it from active ontology to metaphor, quarantine, or provisional status.
```

Formal rule:

```text
No recurring metaphor may be promoted into a stable framework object unless its adapter, evidence state, failure mode, and domain boundary are explicitly bound into the SCW envelope or its companion receipt.
```

This prevents symbolic drift from masquerading as evidence.

---

## SCW context-envelope requirement

A SCW-bearing artifact must bind not only object identity, but also interpretation context.

Required contextual bindings:

| Binding | Purpose |
|---|---|
| `artifact_digest` | what artifact is being referenced |
| `salt_domain` | which causal universe may interpret it |
| `schema_version` | which decoding layout is active |
| `adapter_class` | which transform/projection generated the interpretation |
| `adapter_digest` | exact adapter witness |
| `evidence_state` | claim-state ladder position |
| `domain_boundary` | where the mapping is allowed to apply |
| `failure_mode` | known way the mapping can fail |
| `quarantine_state` | whether the motif is safe, suspect, or isolated |
| `mutation_lineage` | what prior object/schema it inherits from or invalidates |

The identifier may remain stable only inside the salt-compatible causal universe and the declared interpretation envelope.

---

## Attractor-gated identifier law

```text
SCW-8192 identifiers must not allow motif recurrence alone to imply object identity, lineage continuity, or evidence promotion.
```

Equivalent operational rule:

```text
same motif + different adapter = different interpretation
same motif + different salt = different causal universe
same motif + different evidence state = different claim object
same motif + unknown failure mode = quarantine candidate
```

---

## Promotion gate

A motif may move from metaphor to framework object only if all are present:

1. explicit adapter definition,
2. bounded domain of validity,
3. evidence state,
4. failure mode,
5. source/receipt link,
6. salt-compatible lineage,
7. contamination handling rule,
8. at least one negative test or falsification path.

If any are missing:

```text
status := BEAUTIFUL_PROVISIONAL
```

If the motif is recurring across unrelated domains without receipts:

```text
status := QUARANTINE_REVIEW
```

---

## Drift metrics

A future implementation should compute a semantic-attractor pressure score.

Suggested fields:

```text
motif_frequency
cross_domain_spread
adapter_count
evidence_receipt_count
failure_mode_count
quarantine_count
promotion_count
reversal_count
```

Suggested risk proxy:

```math
A_{risk}
=
\frac{F_{motif}\,D_{spread}}{1+E_{receipts}+F_{failures}+Q_{quarantine}}
```

Where:

| Symbol | Meaning |
|---|---|
| `F_motif` | motif recurrence frequency |
| `D_spread` | number of unrelated domains using the motif |
| `E_receipts` | evidence receipts tied to the motif |
| `F_failures` | documented failure modes |
| `Q_quarantine` | quarantine interventions already applied |

High `A_risk` does not mean the motif is false. It means the motif is becoming too gravitational relative to its receipts.

---

## Quarantine action

When attractor risk exceeds the threshold:

```text
A_risk > theta_attractor
```

perform:

1. assign a `quarantine_salt`,
2. split motif lineage from active ontology,
3. downgrade claims to `BEAUTIFUL_PROVISIONAL`,
4. require adapter-specific receipts before re-entry,
5. record the quarantine event in AMMR,
6. prevent automatic merge with active salt domains.

---

## Legacy re-entry rule

Legacy artifacts may be extracted, sanitized, and reused, but not merged directly into the active schema.

Required path:

```text
legacy artifact
  -> quarantine_salt
  -> adapter-specific extraction
  -> evidence receipt
  -> failure-mode check
  -> active re-entry under new salt if passed
```

This supports old-idea mining without old-pattern infection.

---

## Relationship to SCW-8192 length

This guardrail is one reason SCW-8192 is intentionally long.

A small ID can bind object identity. A larger salted witness envelope can bind:

```text
object identity
+ interpretation context
+ adapter lineage
+ evidence state
+ failure mode
+ quarantine state
+ mutation horizon
```

The length is not justified by collision math alone. It is justified by the need to survive conceptual velocity without semantic collision.

Short form:

```text
SCW-8192 is oversized because the context horizon is oversized.
```

---

## Forbidden inference

The following inference is invalid:

```text
This motif appears everywhere, therefore it is fundamental.
```

The valid inference is:

```text
This motif appears everywhere, therefore it needs stronger adapter gates, receipts, and failure tests.
```

---

## Design principle

```text
Identifiers in SCW-bearing systems must bind not only object identity but also interpretation context, adapter lineage, evidence state, quarantine status, and mutation horizon.

Any identifier that cannot survive future schema reinterpretation without semantic collision is too small, even if it is cryptographically collision-resistant.
```

---

## Summary

```text
SCW-8192 prevents false lineage merges.
Semantic attractor guardrails prevent false ontology merges.
```

Together, they keep weird ideas usable without letting them become unearned doctrine.
