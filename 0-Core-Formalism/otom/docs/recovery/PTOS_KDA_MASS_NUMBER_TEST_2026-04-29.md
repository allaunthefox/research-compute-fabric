---
project: PerpetualTravelerOS
domain: axis-07-attestation
secondary_domains:
  - axis-06-safety
  - axis-12-governance
  - axis-11-geometry
  - axis-04-formalization
type: MassNumberTest
settlement: HOLD_WITH_EDGE_SURVIVORS
authority: registry
route_signature: recovery/axis-07-attestation/mass-number-test/ptos-kda-governance-lineage/2026-04-29
source_manifest: docs/recovery/PTOS_KDA_GOVERNANCE_LINEAGE_2026-03-20.md
status: TEST_PROVE_DRIFT_MAP
---

# PTOS / KDA Governance Lineage — Mass-Number Drift Test

## Purpose

This document applies the mass-number admissibility test to the recovered PTOS/KDA governance lineage.

The user assessment for this pass:

```text
most of that content is pure drift
```

Therefore this is not a promotion document. It is a drift test: identify which invariants have admissible mass, which claims are unsupported drift, and which fragments should survive as edge candidates.

## Governing equation

Using the current mass-number doctrine:

```text
Mass Number = Admissible Reduction / Residual Risk
```

For a candidate `x` in a domain `D` and reference frame `R`:

```text
M_D,R(x) = [Σ_i w_i,D · ρ_i,D(x) · κ_i,D(x) · α_i,D(x)]
           /
           [1 + T_D,R(x) + S_D,R(x) + L_D,R(x) + V_D,R(x) + O_D,R(x) + Δ_Drift_D,R(x)]
```

This test uses qualitative bins only:

```text
HIGH       = strong invariant, low residual, clear projection
MEDIUM     = useful invariant, unresolved implementation detail
LOW        = mostly narrative or domain-drift
QUARANTINE = dangerous, coercive, false-legitimacy, or unverifiable claim
```

## Candidate decomposition

The recovered PTOS/KDA lineage is decomposed into atomic candidates:

```text
C1. Collective Human Shape release lock
C2. Anonymous cumulative governance vote
C3. Entity Shape Integrity tamper detection
C4. Horse-bypass coercion friction principle
C5. CAV coercion-attack response
C6. TopologyOS bound register in PTOS
C7. Governance-bypass claim
C8. Perpetual Traveler OS as total operating system claim
C9. KDA simulation fragments as implementation evidence
```

## Test table

| ID | Candidate | Mass kind | Reduction strength | Residual risk | Drift risk | Decision |
|---|---|---|---:|---:|---:|---|
| C1 | Collective Human Shape release lock | attestation_mass / release_gate_mass | MEDIUM | HIGH | MEDIUM | EDGE_SURVIVOR |
| C2 | Anonymous cumulative governance vote | privacy_attestation_mass | MEDIUM | HIGH | MEDIUM | EDGE_SURVIVOR |
| C3 | Entity Shape Integrity tamper detection | identity_continuity_mass / coercion_signal_mass | MEDIUM | VERY_HIGH | HIGH | HOLD |
| C4 | Horse-bypass coercion friction principle | adversary_cost_mass | HIGH | MEDIUM | LOW | PROMOTE_AS_PRINCIPLE |
| C5 | CAV coercion-attack response | safety_response_mass | MEDIUM | HIGH | MEDIUM | EDGE_SURVIVOR |
| C6 | TopologyOS bound register | substrate_binding_mass | MEDIUM | MEDIUM | MEDIUM | EDGE_SURVIVOR |
| C7 | Governance-bypass claim | governance_legitimacy_mass | LOW | VERY_HIGH | VERY_HIGH | QUARANTINE |
| C8 | PTOS as total OS claim | architecture_mass | LOW | HIGH | HIGH | HOLD |
| C9 | KDA simulation fragments as evidence | executable_evidence_mass | LOW until files exist/build | HIGH | MEDIUM | TEMP_DUMP |

## Surviving invariants

### S1 — Coercion should be expensive, noisy, and non-scalable

Recovered phrase:

```text
make coercion as stupid as carrying a horse on your back
```

Mass-number result:

```text
PROMOTE_AS_PRINCIPLE
```

Reason:

- clear adversary-cost principle
- strong safety relevance
- low dependency on political legitimacy claims
- compatible with AngrySphinx / Warden / attestation lanes

Canonical form:

```text
A governance or release protocol should make coercion possible only at high cost, high visibility, and low scalability.
```

### S2 — Coercion is an attack method

Mass-number result:

```text
EDGE_SURVIVOR
```

Reason:

- strong safety invariant
- needs formal coercion model before promotion
- should be handled as attack detection, not voter punishment

Canonical form:

```text
coercion attempt → review gate → release lock hardening / refusal path
```

### S3 — Aggregate approval can be useful without exposing individual vote content

Mass-number result:

```text
EDGE_SURVIVOR
```

Reason:

- compatible with privacy-preserving voting / threshold cryptography
- but recovered text lacks cryptographic protocol details
- must not imply deployed governance legitimacy

Canonical form:

```text
aggregate authorization may be visible while individual vote content and motive remain private
```

### S4 — TopologyOS as bound register

Mass-number result:

```text
EDGE_SURVIVOR
```

Reason:

- useful architectural invariant
- unclear implementation semantics
- should become a typed registry interface, not a political claim

Canonical form:

```text
PTOS variants require a topology-state register for attestation and safety routing.
```

## Drift / quarantine findings

### D1 — “Bypasses why normal human government fails”

Mass-number result:

```text
QUARANTINE
```

Reason:

- overbroad governance legitimacy claim
- high drift
- no formal proof
- unsafe if interpreted as replacement for accountable institutions

Allowed rewrite:

```text
PTOS explores protocol-level mitigations for specific governance failure modes such as coercion, opacity, capture, and low-integrity release authorization.
```

Disallowed rewrite:

```text
PTOS solves government.
```

### D2 — “No one knows what you voted for, why, or how”

Mass-number result:

```text
HOLD
```

Reason:

- useful privacy objective
- but absolute privacy claim is too strong without cryptographic specification

Allowed rewrite:

```text
The protocol should minimize exposure of individual vote content, motive, and method while proving aggregate authorization.
```

### D3 — Entity-shape coercion detection

Mass-number result:

```text
HOLD
```

Reason:

- potentially useful as continuity/tamper signal
- high risk of identity scoring abuse
- needs due-process and false-positive boundaries

Allowed rewrite:

```text
Entity-shape changes may be used as a review trigger, not as automatic guilt or enforcement.
```

## Mass-number proof sketch

The recovered lineage has high narrative load and high drift. Under the master mass-number equation, most fragments suffer large penalties:

```text
L_D,R(x)          high cognitive/routing load
Δ_Drift_D,R(x)   high domain drift from metaphor → governance
V_D,R(x)          high violation risk for coercion/identity claims
O_D,R(x)          hidden oracle risk in entity-shape scoring
```

So broad PTOS governance claims do not promote.

However, several narrow invariants retain admissible mass because their reductions are strong and domain-local:

```text
coercion friction
coercion-as-attack
aggregate authorization without individual disclosure
release-lock review gate
TopologyOS as required state register
```

Therefore:

```text
PTOS_TOTAL_GOVERNANCE_CLAIM → HOLD / QUARANTINE
PTOS_COERCION_FRICTION      → PROMOTE_AS_PRINCIPLE
PTOS_ATTESTATION_LOCKS      → EDGE_SURVIVOR
PTOS_ENTITY_SHAPE_SCORING   → HOLD_WITH_SAFETY_BOUNDARY
```

## Autodoc action

Using the autodoc doctrine:

```text
a candidate should write itself down only when it reduces more future confusion than it adds
```

Decision:

```text
UPDATE_EXISTING recovery manifest
CREATE targeted future specs only for surviving invariants
DO NOT promote total PTOS governance claim
```

Recommended future specs:

```text
docs/safety/PTOS_COERCION_ATTACK_MODEL.md
docs/attestation/PTOS_RELEASE_LOCKS.md
docs/attestation/ENTITY_SHAPE_INTEGRITY_REVIEW_SIGNAL.md
docs/architecture/TOPOLOGYOS_BOUND_REGISTER.md
```

## Final decision

```text
HOLD_WITH_EDGE_SURVIVORS
```

Survives:

- coercion friction principle
- coercion-as-attack lane
- privacy-preserving aggregate authorization objective
- release-lock review concept
- TopologyOS bound-register concept

Does not survive as canonical:

- PTOS solves or bypasses government
- absolute vote privacy
- automatic entity-shape guilt detection
- KDA simulation fragments as implementation evidence without raw files/build evidence

## Next test

The next proof-test should target only one survivor:

```text
PTOS_COERCION_ATTACK_MODEL
```

because it has the cleanest mass number and lowest drift.
