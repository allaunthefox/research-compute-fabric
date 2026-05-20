# AngrySphinx Donated-Cycle Gate Specification

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-05-20 | Codex | Initial design spec for Anubis-style web proxy integration |

---

## 1. Purpose

AngrySphinx Donated-Cycle Gate is a web-facing proof-of-defense layer where suspicious or adversarial clients must spend local compute before receiving protected content. Unlike generic proof-of-work, the client work is shaped so accepted proofs contribute to the defender's own gate calibration, route hardening, challenge corpus, or bounded useful-compute queue.

The security doctrine is:

> The attacker either leaves, or donates cycles that improve the gate defending the system.

The system is intentionally compatible with an Anubis-style anti-bot proxy: browser-side or client-side challenge work is expensive for the requester, while server-side verification remains cheap and bounded.

Baseline critique: a plain Anubis-style proof-of-work gate is needlessly wasteful when the solved work is only discarded. It can still be operationally useful as bot friction, but the compute is burned rather than converted into route memory, defensive calibration, or challenge hardening. AngrySphinx keeps the cheap-verification proxy shape while requiring accepted work to leave a defensive receipt.

---

## 2. Design Goals

### 2.1 Primary Goals

- Convert abusive traffic into measurable defensive work.
- Avoid burn-only proof-of-work where accepted client cycles produce no defensive state.
- Preserve cheap server verification for every challenge response.
- Increase challenge difficulty based on observed attack pressure.
- Attach every accepted proof to an auditable proof-of-defense receipt.
- Keep protected origin services insulated from untrusted clients.
- Make useful work optional and bounded; the default challenge remains hashcash-compatible.

### 2.2 Non-Goals

- Do not execute arbitrary attacker-supplied code.
- Do not rely on server-expensive verification.
- Do not claim that web proof-of-work stops all bot traffic.
- Do not require useful scientific computation in the first prototype.
- Do not weaken accessibility or legitimate low-power client access without fallback paths.

---

## 3. System Model

### 3.1 Components

| Component | Responsibility |
|-----------|----------------|
| Edge Proxy | Intercepts requests before origin access, issues challenges, verifies proofs |
| Challenge Engine | Builds challenge payloads from policy, telemetry, and difficulty state |
| Work Client | Browser or command-line solver performing bounded local compute |
| Proof Verifier | Checks proof cheaply and deterministically |
| PoD Ledger | Records accepted work, shell depth, attestation, and route metadata |
| Defense Calibrator | Converts proof telemetry into difficulty and route-hardening updates |
| Policy Layer | Refuses forbidden operations and selects fallback behavior |

### 3.2 Existing Formal Anchors

- `Semantics.AngrySphinx.AttackPressure`: represents attack pressure as energy quanta.
- `Semantics.AngrySphinx.ShellDepth`: tracks S3 shell depth.
- `Semantics.AngrySphinx.gearProduct`: computes the shell multiplier, defaulting to `2^depth`.
- `Semantics.AngrySphinx.solveEnergy`: models required solve energy from pressure and shell depth.
- `Semantics.AngrySphinx.PodAccumulator`: records accepted work and the last attestation.
- `Semantics.AngrySphinx.verifyPod`: checks accumulated work against shell depth.
- `Semantics.AngrySphinxPolicy`: enforces refusal and review gates.

---

## 4. Core Mechanic

### 4.1 Request Flow

1. Client requests a protected URL.
2. Edge Proxy evaluates request risk using IP, path, rate, user-agent, cookies, prior receipts, and route class.
3. If risk is low, request passes normally.
4. If risk is medium or high, Challenge Engine emits an AngrySphinx challenge.
5. Work Client solves the challenge locally.
6. Client submits proof, nonce, challenge ID, and optional timing telemetry.
7. Proof Verifier checks the proof cheaply.
8. If valid, Edge Proxy issues a short-lived access token and forwards the request.
9. PoD Ledger records donated work and updates defensive state.
10. Defense Calibrator adjusts future challenge difficulty or route policy.

### 4.2 Challenge Shape

Every challenge must contain:

```json
{
  "challenge_id": "opaque id",
  "route_id": "normalized protected route class",
  "issued_at": "unix timestamp",
  "expires_at": "unix timestamp",
  "difficulty": 24,
  "shell_depth": 8,
  "gear_ratio": 2,
  "mode": "hashcash",
  "seed": "server signed random seed",
  "policy_root": "angrysphinx:web_gate:v0.1",
  "receipt_required": true
}
```

The initial prototype should use `mode = "hashcash"` because it is simple, auditable, and cheap to verify. Later modes can embed bounded useful-compute tasks, but only when verification remains cheap.

### 4.3 Proof Shape

Every proof must contain:

```json
{
  "challenge_id": "opaque id",
  "nonce": "client nonce",
  "digest": "hash(seed || nonce || route_id)",
  "client_elapsed_ms": 1830,
  "work_claim": 16777216,
  "client_class_hint": "browser"
}
```

The verifier must be able to recompute the digest and compare it to the target threshold without replaying the full search.

---

## 5. Donated-Cycle Accounting

### 5.1 Work Units

The proxy records accepted challenge work as `work_units`, not trusted joules. For hashcash challenges:

```text
work_units = 2^difficulty
```

For sampled verification modes:

```text
work_units = verified_steps * confidence_factor
```

The client may report elapsed time, but elapsed time is telemetry only. It must not be trusted for accounting.

### 5.2 PoD Ledger Entry

Each accepted proof appends a record:

```json
{
  "receipt_id": "pod receipt id",
  "challenge_id": "challenge id",
  "route_id": "normalized route",
  "client_fingerprint": "privacy-preserving bucket",
  "risk_class": "medium|high|hostile",
  "difficulty": 24,
  "shell_depth_before": 8,
  "shell_depth_after": 9,
  "work_units": 16777216,
  "accepted_at": "unix timestamp",
  "attestation": "work=...,depth=...",
  "policy_root": "angrysphinx:web_gate:v0.1"
}
```

This corresponds to `PodAccumulator.accumulateWork`: accepted work increases `totalWork`, and sustained hostile pressure can deepen the shell.

### 5.3 Work Sinks

Accepted work can support four defensive sinks:

| Sink | Description | Prototype Priority |
|------|-------------|--------------------|
| Difficulty Calibration | Tune future difficulty by observed solve rates and route pressure | High |
| Route Hardening | Raise challenge depth for routes receiving hostile pressure | High |
| Challenge Corpus Expansion | Generate new signed seeds and route-specific challenge variants | Medium |
| Science Donation Plugin Queue | Assign bounded, verifiable tasks that contribute to research or defense models | Later |

The first implementation should only support calibration and route hardening. Science donation plugins should be added only after threat modeling and verification design are complete.

---

## 6. Difficulty and Shell Policy

### 6.1 Attack Pressure

Attack pressure is computed per route bucket:

```text
pressure = f(request_rate, failed_proofs, replay_attempts, origin_errors, suspicious_paths)
```

The pressure maps to `AttackPressure.joules` in the formal model. This is a normalized integer, not physical energy.

### 6.2 Shell Depth

Shell depth increases when hostile traffic keeps paying challenges or failing proofs:

```text
new_depth = min(max_depth, base_depth + pressure_band + route_sensitivity)
```

With default gear ratio `2`, solve cost scales as:

```text
required_work >= 2^shell_depth
```

### 6.3 Difficulty Bounds

The proxy must enforce bounds:

| Bound | Purpose |
|-------|---------|
| `min_difficulty` | Prevent zero-cost bypass |
| `max_difficulty` | Avoid denial of service against legitimate clients |
| `max_solve_ms_target` | Accessibility and device-safety budget |
| `token_ttl` | Limit replay value |
| `challenge_ttl` | Limit stale challenge reuse |

Suggested initial defaults:

```text
min_difficulty = 18
max_difficulty = 28
base_shell_depth = 8
max_shell_depth = 32
challenge_ttl = 120 seconds
access_token_ttl = 900 seconds
```

---

## 7. Verification Requirements

### 7.1 Server Verification

Verification must be:

- Deterministic.
- Stateless or bounded-state.
- O(1) or O(log n) relative to client work.
- Replay resistant.
- Bound to route, timestamp, and policy root.
- Signed or MACed so clients cannot forge easier challenges.

### 7.2 Replay Protection

The server must reject:

- Expired challenge IDs.
- Reused challenge IDs.
- Proofs bound to different routes.
- Proofs with invalid policy roots.
- Proofs below the target threshold.
- Proofs for revoked challenge versions.

### 7.3 Origin Isolation

The origin service should only receive requests with a valid access token or trusted bypass identity. It should not implement challenge verification itself.

---

## 8. Science Donation Plugin Extension

The science donation concept is a plugin track layered beside the live security gate. The gate still decides access using cheap proof verification. The plugin consumes eligible donated-cycle opportunities and assigns bounded work packets that can support science or defense research.

The plugin must not make origin access depend on expensive server-side recomputation. Its job is to turn otherwise wasted proof-of-work into auditable science work when safe, not to put arbitrary scientific workloads in the critical request path.

Critical rule: science donation is funded only by surplus attacker cost. The gate must first satisfy its defensive work requirement. Only the excess work budget above the active defense floor may be redirected to science tasks.

```text
required_defense_work = defense_floor(route, shell_depth, pressure, policy)
paid_work            = accepted client work
surplus_work         = max(0, paid_work - required_defense_work)

science_work_allowed iff surplus_work > 0 and defense_level_after >= defense_level_before
```

If a science plugin would reduce route hardening, lower shell depth, consume verifier budget, delay refusal, weaken replay protection, or otherwise reduce the active defense level, the plugin is not admissible for that request.

### 8.1 Required Properties

Science donation plugins are admissible only if they satisfy:

- Cheap verification.
- No private data exposure.
- No attacker-controlled program execution.
- No result dependence on unverifiable floating-point behavior.
- Bounded memory and CPU footprint.
- Deterministic challenge generation.
- Clear failure mode that falls back to hashcash.
- Explicit plugin manifest describing task class, verification method, resource budget, and data provenance.

### 8.2 Plugin Boundary

Each plugin exposes:

```json
{
  "plugin_id": "science.protein_microtask.v0",
  "task_class": "bounded_search",
  "verification": "known_witness_or_spot_check",
  "max_client_ms": 2000,
  "max_memory_mb": 64,
  "data_policy": "public_or_synthetic_only",
  "fallback_mode": "hashcash",
  "receipt_schema": "science_donation_receipt.v0"
}
```

The Challenge Engine may select a plugin task only when:

- required defensive work has already been met
- projected defense level will not decrease
- surplus work remains after gate accounting
- route policy permits plugin work
- client class can safely run it
- task verification remains bounded
- task data is public or synthetic
- fallback hashcash challenge is available

### 8.3 Candidate Task Classes

| Task Class | Verification Strategy | Risk |
|------------|-----------------------|------|
| Hashcash with route-derived seeds | Recompute digest | Low |
| Verifiable random function preimage search | Recompute proof | Low |
| Merkleized micro-benchmark witness | Spot-check trace commitments | Medium |
| SAT/CNF micro-instance with known witness | Verify assignment | Medium |
| Protein/graph heuristic search | Hard to verify cheaply | High |

Scientific or research-side tasks should start as offline sinks fed by proof telemetry, not as direct web challenges.

### 8.4 Plugin Receipt

Science donation work emits a separate receipt linked to the PoD receipt:

```json
{
  "science_receipt_id": "science receipt id",
  "pod_receipt_id": "linked proof-of-defense receipt id",
  "plugin_id": "science.protein_microtask.v0",
  "task_id": "bounded task id",
  "verification_result": "accepted|rejected|sampled",
  "work_units": 16777216,
  "output_commitment": "hash of submitted result",
  "data_policy": "public_or_synthetic_only"
}
```

This lets the security ledger remain simple while science donation work gets its own provenance chain.

### 8.5 Defense-Preserving Redirect

The redirect rule is:

```text
defense first, science second
```

The Challenge Engine computes a route-specific defense floor before issuing any science task. A client may be asked to solve a combined challenge, but the proof must be decomposable into:

- the defensive portion required for access control
- the surplus portion eligible for science donation

The PoD Ledger records the defensive portion first. The Science Donation Plugin records only surplus work. If the client abandons the science portion, the gate may still accept the defensive proof if the required defense floor was met.

This prevents the plugin system from becoming an accidental bypass where science work replaces route hardening.

### 8.6 Practical Rule

For web deployment:

```text
If verification is not cheap, it is not an AngrySphinx web gate task.
```

For plugin deployment:

```text
If science work cannot be verified cheaply online, route it to an offline donation queue instead of the access gate.
If science work competes with the defense floor, reject the science plugin and keep the defense work.
```

---

## 9. Privacy and Safety

### 9.1 Client Fingerprints

The ledger should store coarse buckets, not raw fingerprints:

- route bucket
- risk class
- approximate client class
- proof timing quantile
- coarse network bucket if needed

Avoid storing raw IPs unless operationally required. If raw IPs are stored, define retention and deletion policy.

### 9.2 Legitimate Client Fallback

The system must support:

- authenticated bypass
- low-power mode
- accessibility bypass
- allowlisted crawlers where appropriate
- manual review or contact path

### 9.3 Abuse Constraints

The system must not become a client-side cryptominer or hidden compute extractor. Challenges are only issued for access control and defense. The page must clearly indicate that a security check is running.

---

## 10. Anubis Integration Plan

### 10.1 Minimal Fork Strategy

Use Anubis as the edge proxy and challenge transport, but treat its default burn-only proof-of-work model as the baseline to improve. Add AngrySphinx as a policy/accounting layer:

```text
Anubis request classifier
  -> AngrySphinx difficulty policy
  -> Anubis-style hash challenge
  -> AngrySphinx proof ledger
  -> access token
  -> origin
```

This avoids rewriting proxy mechanics before the donated-cycle model is validated.

### 10.2 Required Integration Points

| Integration Point | Required Change |
|-------------------|-----------------|
| Challenge generation | Include `route_id`, `shell_depth`, `policy_root`, signed seed |
| Challenge page | Brand/copy as AngrySphinx, expose clear security-check semantics |
| Proof verification | Emit ledger event after accepted proof |
| Difficulty policy | Compute challenge difficulty from route pressure and shell depth |
| Metrics | Track solves, failures, replay attempts, elapsed time, and origin pass-through |
| Admin config | Add route-specific min/max difficulty and bypass rules |

### 10.3 First Prototype Scope

The first prototype should implement:

- Hashcash-only challenge mode.
- Route-bound challenge IDs.
- Signed challenge payloads.
- In-memory or SQLite PoD ledger.
- Per-route difficulty adjustment.
- Basic admin metrics.
- No useful-compute tasks yet.
- No science donation plugins in the request-critical path yet.

---

## 11. Formal Mapping

### 11.1 Lean Correspondence

| Web Spec Concept | Lean Concept |
|------------------|--------------|
| risk pressure | `AttackPressure` |
| route shell depth | `ShellDepth` |
| difficulty multiplier | `GearRatio` / `gearProduct` |
| donated proof work | `PodAccumulator.totalWork` |
| accepted proof receipt | `PodAccumulator.lastAttestation` |
| work admission check | `verifyPod` |
| refusal policy | `AngrySphinxPolicy` / `AngrySphinxGate` |

### 11.2 Intended Theorem Direction

Future formal work should prove:

```text
accepted_web_proof implies ledger_work_increases
ledger_work_increases implies nondecreasing_defense_budget
shell_depth_increases implies required_work_non_decreasing
invalid_or_expired_proof implies no_origin_access
```

The existing `solveEnergyExponential` theorem is the core target: route pressure should imply exponentially increasing solve obligation under bounded depth.

---

## 12. Operational Metrics

Track:

- challenge issue count
- proof success count
- proof failure count
- replay rejection count
- average solve time by difficulty
- p95 solve time by client class
- route pressure score
- current route shell depth
- donated work units per route
- origin requests spared
- bypass uses

The key dashboard metric:

```text
defense_work_ratio = accepted_donated_work_units / origin_requests_served
```

---

## 13. Open Questions

- Which Anubis version and extension points should be used for the prototype?
- Should the first ledger be SQLite, JSONL, or Prometheus-only?
- How should authenticated users bypass or receive lower difficulty?
- What is the maximum acceptable challenge time for low-power devices?
- Which route classes deserve independent shell depth?
- Should useful-compute be implemented at all in the web path, or only as an offline research sink?
- How should FAMM route scars and PIST shell coordinates be bound into the live challenge policy?
- What plugin manifest and receipt schema should science donation tasks use?

---

## 14. Implementation Milestones

### Milestone 1: Baseline Gate

- Run Anubis-style hashcash challenge on protected route.
- Bind challenge to route, timestamp, and policy root.
- Verify proof and issue short-lived access token.

### Milestone 2: PoD Ledger

- Persist accepted proof records.
- Track donated work units.
- Emit `work=...,depth=...` attestations compatible with `PodAccumulator`.

### Milestone 3: Adaptive Shell Policy

- Compute per-route pressure.
- Adjust shell depth and difficulty within bounds.
- Add replay and failure-rate hardening.
- Wire FAMM scar memory into route hardening using `FAMMScarMemory.lean`, `FAMM.lean`, and `RouteCost.lean`.
- Map route and challenge IDs into PIST/ShellModel coordinates using `PIST.lean`, `ShellModel.lean`, and `PistBridge.lean`.

### Milestone 4: Admin and Observability

- Add metrics endpoint or dashboard.
- Show route pressure, donated work, failure rate, and current difficulty.
- Add operational bypass and allowlist controls.

### Milestone 5: Useful-Compute Research Track

- Evaluate verifiable task classes offline.
- Add only if verification remains cheap and policy-compliant.
- Define the science donation plugin manifest.
- Define the linked science donation receipt schema.
- Keep plugin tasks outside the request-critical path until bounded verification is proven.

---

## 15. Summary

AngrySphinx Donated-Cycle Gate turns anti-bot friction into a defensive asset. The attacker does not merely burn cycles; accepted work is receipted, counted, and used to harden the same gate that blocked them. An Anubis-style proxy provides the correct implementation shape because it already separates expensive client solving from cheap server verification.
