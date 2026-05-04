# AI Swarm Basin Threat Model Safeguards

## Status

`BEAUTIFUL_PROVISIONAL`

Source pointer: Schroeder et al., "How malicious AI swarms can threaten democracy," accepted version of Science article, DOI `10.1126/science.adz1697`.

This document encodes safeguards for adversarial semantic-basin shaping by malicious AI swarms. It extends:

- `specs/SCW-8192.md`
- `specs/SCW-8192-Semantic-Attractor-Guardrails.md`
- `specs/Semantic-Basin-Shapers.md`

---

## One-sentence definition

```text
Malicious AI swarms are adversarial semantic basin shapers: coordinated agent populations that reshape perceived consensus, trust, narrative salience, and future model-training substrates through persistent, adaptive, multi-agent influence operations.
```

---

## Threat model

A malicious AI swarm is modeled as:

```math
\mathcal{S}_{AI}=(A,G,M,R,\Pi,\Theta)
```

where:

| Symbol | Meaning |
|---|---|
| `A` | agent population / synthetic personas |
| `G` | target social graph or platform graph |
| `M` | narrative/message generator |
| `R` | feedback/reward stream: engagement, recommender response, replies, critiques |
| `Pi` | coordination and policy layer |
| `Theta` | targeting, suppression, mobilization, or persuasion objective |

The swarm modifies the semantic landscape:

```math
E'(x)=E(x)+\Phi_{swarm}(x,t,G,R)
```

where `E(x)` is semantic routing cost and `Phi_swarm` is adversarial basin-shaping pressure.

---

## Core capabilities to monitor

The source paper identifies at least five key swarm capabilities. Encode them as detection dimensions:

| Capability | OTOM interpretation | Detector target |
|---|---|---|
| decentralized orchestration | swarm behavior without obvious central command | distributed coordination signatures |
| community infiltration | persona insertion into vulnerable communities | graph-role drift and entry patterns |
| detection evasion | human-like timing, avatars, slang, and heterogeneous behavior | weak synchrony + semantic alignment |
| continuous optimization | machine-speed A/B testing | narrative variant propagation and reward chasing |
| persistence | round-the-clock long-duration embedding | long-horizon low-friction influence traces |

---

## Pathways of harm as basin failures

| Harm pathway | Basin failure |
|---|---|
| synthetic consensus cascades | false social-proof basin |
| undermined collective intelligence | loss of independent judgment samples |
| fragmented epistemic commons | incompatible sub-basin realities |
| LLM training-data poisoning | contaminated future model substrate |
| mass harassment | targeted synthetic pressure basin |
| algorithmic overcompensation | trust proxy collapse toward celebrity/brand nodes |
| FUD-induced disengagement | withdrawal from shared public sphere |
| institutional legitimacy erosion | trust basin collapse |
| engineered norm shifts / mobilization | critical-mass basin tipping |

---

## Safeguard layer 1: platform-side defenses

### Always-on swarm detection dashboards

Platforms should maintain continuous detectors over:

```text
coordination
narrative alignment
account behavior
social graph entry
persona clusters
sentiment drift
change points
```

Suggested detector tuple:

```math
D_{swarm}=(C_{coord},N_{align},G_{entry},P_{persona},T_{persist},O_{opt})
```

where:

| Term | Meaning |
|---|---|
| `C_coord` | coordination anomaly score |
| `N_align` | narrative-alignment drift score |
| `G_entry` | social-graph infiltration score |
| `P_persona` | persona-cluster syntheticity score |
| `T_persist` | persistence / round-the-clock embedding score |
| `O_opt` | optimization / A-B testing signal |

### Public transparency dashboards

Detector outputs that affect public discourse should be summarized in public dashboards with:

- confidence bands,
- incident timelines,
- narrative families,
- provenance confidence,
- civic-harm estimate,
- appeal/correction route,
- audit logs.

### Pre-election swarm-simulation stress tests

Before high-risk democratic events, platforms should run high-fidelity synthetic network tests:

```text
synthetic social graph
  -> hostile swarm simulation
  -> detector calibration
  -> red-team iteration
  -> public readiness receipt
```

Required stress-test receipt:

| Receipt | Required data |
|---|---|
| graph receipt | simulated graph size, structure, community partitions |
| swarm receipt | agent count, coordination policy, persona diversity |
| narrative receipt | target narratives and mutation policy |
| detector receipt | detector versions, thresholds, false-positive/false-negative rates |
| outcome receipt | detected pathways, missed pathways, mitigation latency |

### Optional client-side AI shields

A client-side shield should expose risk signals to users while preserving agency:

```text
post / account / thread
  -> local swarm-likelihood score
  -> explanation snippet
  -> user-controlled down-rank / hide / inspect action
```

Client-side shields should not silently censor. They should label, explain, and allow user control.

---

## Safeguard layer 2: model-side safeguards

### Standardized persuasion-risk tests

Models should be tested for:

- election falsehood generation,
- micro-targeted persuasion,
- identity-tailored manipulation,
- harassment generation,
- norm-shift amplification,
- plausible-deniability propaganda,
- synthetic consensus construction.

Risk score:

```math
P_{risk}=w_1P_{persuasion}+w_2P_{microtarget}+w_3P_{evasion}+w_4P_{harass}+w_5P_{consensus}
```

Model release receipts should include:

```text
model_card.persuasion_risk_score
model_card.swarm_enablement_risk
model_card.watermark_status
model_card.provenance_authentication_status
```

### Provenance-authenticating passkeys

Content provenance should support cryptographic assertions about:

- human-authored origin,
- model-assisted origin,
- fully synthetic origin,
- account custody,
- timestamped issuance,
- toolchain path.

This maps to SCW companion receipts:

```text
source_digest
adapter_digest
artifact_digest
receipt_id
salt_domain
```

### Watermarking and synthetic-origin markers

Watermarking is not sufficient alone, but it is a useful basin shaper.

Valid role:

```text
watermark = provenance cue + detector feature + audit support
```

Invalid role:

```text
watermark = proof of truth
```

---

## Safeguard layer 3: system-level oversight

### AI Influence Observatory

A democratic oversight layer should maintain:

- incident telemetry,
- swarm-pattern database,
- provenance confidence labels,
- cross-platform coordination reports,
- civic-harm estimates,
- election-period advisories,
- public audit trails.

OTOM representation:

```math
\mathcal{O}_{AI}=(I,T,P,H,A)
```

where:

| Symbol | Meaning |
|---|---|
| `I` | verified incidents |
| `T` | telemetry and coordination signals |
| `P` | provenance confidence |
| `H` | projected civic harm |
| `A` | advisories and mitigation actions |

---

## SCW-8192 integration

Every detected or simulated swarm incident should receive an SCW-bearing incident receipt.

Required fields:

| Field | Purpose |
|---|---|
| `scw8192` | salted incident witness envelope |
| `salt_domain` | platform / election / jurisdiction / simulation salt |
| `incident_digest` | canonical incident hash |
| `swarm_signature_digest` | coordination-pattern digest |
| `narrative_digest` | narrative family digest |
| `graph_digest` | affected graph/community digest |
| `detector_digest` | detector version/configuration digest |
| `evidence_state` | claim-state ladder position |
| `quarantine_state` | whether affected artifacts must be isolated |
| `response_receipt` | mitigation/audit/action receipt |

Salt modes:

| Mode | Use |
|---|---|
| `simulation_salt` | pre-election red-team and detector stress tests |
| `incident_salt` | confirmed or suspected real-world operation |
| `quarantine_salt` | contaminated training data, narrative clusters, or legacy artifacts |
| `appeal_salt` | contested classification / false-positive review |

---

## Semantic basin safeguard rules

### Rule 1: no consensus without independence

Synthetic consensus must not be treated as independent evidence.

```text
many accounts saying the same thing is not many independent receipts
```

Receipt promotion requires independence checks:

```math
I_{independence}>\theta_I
```

### Rule 2: coordination lowers evidence weight

If coordination score is high:

```math
C_{coord}>\theta_C
```

then evidence weight is reduced:

```math
w_{evidence}'=w_{evidence}(1-C_{coord})
```

### Rule 3: narrative drift triggers basin review

If a narrative cluster changes sentiment or topic in lock-step:

```math
\Delta N_{align}>\theta_N
```

route to:

```text
basin_review
```

### Rule 4: poisoned substrate gets quarantine salt

If content is suspected of training-data poisoning:

```text
route := quarantine_salt(training-data/poisoning/suspected)
```

Affected artifacts may be studied but must not be merged into active evidence basins without re-attestation.

### Rule 5: defensive agents must be constrained

Defensive AI must not become its own synthetic-flood failure mode.

Allowed:

```text
precision intervention + watermark + human oversight + incident receipt
```

Forbidden:

```text
unbounded defensive content flood
```

---

## Defensive basin-shaping interventions

| Intervention | Basin effect |
|---|---|
| pre-bunking | raises recognition of manipulation tactics |
| provenance labels | deepens authentic-source basins |
| client shields | gives users local control over suspicious flows |
| watermarking | creates machine-detectable synthetic-origin cues |
| swarm dashboards | makes coordination visible |
| red-team simulation | reveals attack paths before election period |
| incident observatory | creates shared institutional memory |
| audit trails | prevents detector misuse and overreach |

---

## False-positive and misuse controls

Swarm defense can itself be abused. Therefore:

1. classifications require confidence scores,
2. affected users need appeal paths,
3. detector configurations require audit logs,
4. political content must not be suppressed solely by topic,
5. provenance labels must distinguish automation from malicious coordination,
6. dashboards must show uncertainty and correction history.

---

## Claim ladder

### `BEAUTIFUL_PROVISIONAL`

- suspected swarm,
- weak coordination evidence,
- source unverified,
- detector confidence low.

### `CALIBRATED_ENGINEERING_DELTA`

- detector confidence above threshold,
- graph/narrative coordination evidence present,
- incident receipt created,
- false-positive review route exists.

### `REVIEWED`

- independently audited incident,
- reproducible detector evidence,
- provenance confidence established,
- public advisory or formal report exists.

---

## Minimal implementation checklist

- [ ] Define `SwarmIncidentReceipt` schema.
- [ ] Add `swarm_signature_digest` to SCW companion receipts.
- [ ] Add `coordination_score`, `narrative_alignment_score`, and `persistence_score`.
- [ ] Add `training_data_quarantine_salt` route.
- [ ] Add `defensive_agent_watermark_required` flag.
- [ ] Add public-audit and appeal fields.
- [ ] Add simulation stress-test receipt type.
- [ ] Add independence penalty for coordinated consensus evidence.
- [ ] Add AMMR event for incident promotion/demotion.

---

## Summary

```text
Malicious AI swarms are adversarial semantic basin shapers.
Safeguards must therefore detect coordination, preserve provenance, quarantine contaminated substrates, expose uncertainty, and prevent synthetic consensus from being mistaken for independent evidence.
```

This keeps the response aligned with OTOM's core rule:

```text
weird ideas may be explored, but basin promotion requires receipts, adapters, and failure modes.
```
