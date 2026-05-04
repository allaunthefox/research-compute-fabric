# Undici Agent Routing Bridge

Status: HOLD / implementation-bridge note
Authority: uploaded API docs ingestion; not canonical proof
Related:

- `docs/gcl/MOIMConcepts.md`
- `docs/gcl/SovereignSurfaceRouterTelemetryIngestion.md`
- `docs/gcl/SovereignHyperEquationSynthesisIngestion.md`
- `docs/gcl/NonEquilibriumTransitionRisk.md`

## Purpose

This document maps the uploaded Undici Agent-family docs into the OTOM/GCL routing stack.

The useful abstraction is:

```text
Undici Agent family
  -> network dispatch substrate
  -> proxy / retry / mock / snapshot boundary
  -> telemetry and receipt surface
  -> MOIM route phenotype
```

These docs do not alter the mathematical core. They inform the implementation layer for HTTP dispatch, proxy routing, replay, testing, and network-boundary hardening.

## Source files ingested

```text
Agent.md
EnvHttpProxyAgent.md
MockAgent.md
ProxyAgent.md
RetryAgent.md
SnapshotAgent.md
Socks5ProxyAgent.md
```

## Core mapping

| Undici component | Stack role | MOIM/GCL interpretation |
|---|---|---|
| `Agent` | multi-origin request dispatcher | base network router over origins |
| `EnvHttpProxyAgent` | environment-driven proxy selection | ambient egress policy adapter |
| `ProxyAgent` | explicit HTTP/HTTPS proxy dispatcher | declared proxy boundary / route constraint |
| `Socks5ProxyAgent` | SOCKS/SOCKS5 proxy dispatcher | alternate tunnel phenotype / boundary route |
| `RetryAgent` | retry wrapper around dispatcher | transient-failure repair loop |
| `MockAgent` | intercepted/mocked request dispatcher | test isolation and synthetic route receipt |
| `SnapshotAgent` | record/replay HTTP dispatcher | regression receipt / deterministic replay surface |

## Architectural placement

```text
GCL object / runtime request
  -> MOIM route classification
  -> dispatcher selection
  -> proxy/retry/mock/snapshot policy
  -> telemetry receipt
  -> response or quarantine
```

This is not a proof layer. It is an implementation layer for routing real or simulated network calls.

## Agent as base dispatcher

`Agent` dispatches requests across multiple origins and supports custom factories and origin limits.

Accepted role:

```text
Agent = base network routing primitive
```

Relevant policy fields:

```text
factory
maxOrigins
stats()
close()
destroy()
```

Stack interpretation:

```text
maxOrigins = finite-route budget
factory = route phenotype constructor
stats = telemetry source
closed/destroyed = lifecycle gate
```

Boundary:

```text
Agent stats are operational telemetry, not proof of semantic correctness.
```

## Proxy agents as egress boundary gates

`ProxyAgent`, `EnvHttpProxyAgent`, and `Socks5ProxyAgent` define how requests leave the local process.

Accepted role:

```text
proxy agent = explicit egress boundary
```

Policy requirements:

```text
proxy URI must be declared
NO_PROXY / bypass rules must be explicit
credentials must not be written to snapshots/logs
proxy tunnel behavior must be recorded
proxy errors must route to HOLD/retry/quarantine, not silent fallback
```

## EnvHttpProxyAgent

`EnvHttpProxyAgent` reads proxy configuration from environment variables such as:

```text
http_proxy
https_proxy
no_proxy
```

Accepted role:

```text
ambient environment adapter
```

Risk:

```text
environment-derived behavior can silently change routing
```

Rule:

```text
When reproducibility matters, record effective proxy settings with secrets redacted.
```

## ProxyAgent

`ProxyAgent` gives explicit proxy configuration.

Accepted role:

```text
declared HTTP/HTTPS proxy route
```

Rule:

```text
Prefer explicit ProxyAgent over ambient environment proxy when route receipts matter.
```

## Socks5ProxyAgent

`Socks5ProxyAgent` supports SOCKS/SOCKS5 proxy URLs and optional auth.

Accepted role:

```text
alternate tunnel route / non-HTTP proxy phenotype
```

Security rule:

```text
Never persist SOCKS credentials from URL or options into snapshots, logs, or public receipts.
```

## RetryAgent as repair loop

`RetryAgent` wraps a dispatcher and retries according to configured retry behavior.

Accepted role:

```text
RetryAgent = transient route repair layer
```

MOIM interpretation:

```text
failure
  -> retry policy
  -> route attempt history
  -> receipt or scar
```

Boundary:

```text
Retry success does not prove the route is healthy.
It proves only that the request eventually completed under retry policy.
```

Required telemetry:

```text
attempt count
retry reason
delay/backoff policy
final status
whether non-idempotent request was retried
```

## MockAgent as isolation gate

`MockAgent` intercepts HTTP requests and returns mocked responses.

Accepted role:

```text
MockAgent = synthetic network boundary for tests
```

Use for:

```text
unit tests
route classifier tests
telemetry UI tests
failure-mode simulation
no-network CI
```

Boundary:

```text
Mock pass != live network validation
```

## SnapshotAgent as receipt/replay surface

`SnapshotAgent` records and replays HTTP requests for testing.

Accepted role:

```text
SnapshotAgent = deterministic replay and regression receipt layer
```

Use for:

```text
capture real response once
sanitize snapshot
replay deterministically
compare route behavior across changes
```

Security requirements:

```text
filter authorization headers
filter cookies
filter tokens
filter proxy credentials
filter personal data
avoid committing raw production snapshots
```

Boundary:

```text
snapshot replay proves regression consistency against recorded behavior,
not current external truth.
```

## Dispatch policy object

Candidate GCL/MOIM dispatch policy:

```ts
type NetworkDispatchPolicy = {
  policy_id: string;
  dispatcher_kind:
    | "Agent"
    | "EnvHttpProxyAgent"
    | "ProxyAgent"
    | "Socks5ProxyAgent"
    | "RetryAgent"
    | "MockAgent"
    | "SnapshotAgent";
  route_scope: "live" | "proxy" | "mock" | "snapshot" | "retry_wrapped";
  authority_scope:
    | "workbench_projection"
    | "simulation_only"
    | "receipt_backed"
    | "safety_policy";
  max_origins?: number;
  proxy_declared?: boolean;
  no_proxy_policy?: string;
  retry_policy_ref?: string;
  snapshot_policy_ref?: string;
  secret_redaction_required: boolean;
  receipt_refs: string[];
};
```

## Runtime routing rule

```text
if test_mode:
  use MockAgent or SnapshotAgent
elif explicit_proxy_required:
  use ProxyAgent or Socks5ProxyAgent
elif environment_proxy_allowed:
  use EnvHttpProxyAgent and record effective redacted policy
elif transient_failures_expected:
  wrap selected dispatcher with RetryAgent
else:
  use Agent
```

## Safe telemetry fields

Allowed telemetry:

```text
dispatcher kind
origin count
request count
status code class
retry count
mock/snapshot/live mode
redacted proxy mode
latency histogram
error class
```

Blocked telemetry:

```text
raw Authorization header
raw Cookie header
proxy username/password
full request bodies with secrets
private URLs if not explicitly allowed
```

## Relation to Sovereign Surface

The Sovereign Surface can display this layer as an egress/dispatch status panel.

Useful labels:

```text
LIVE_AGENT
PROXY_AGENT
SOCKS_AGENT
RETRY_WRAPPED
MOCK_MODE
SNAPSHOT_RECORD
SNAPSHOT_PLAYBACK
EGRESS_BLOCKED
```

Boundary:

```text
green network panel != proof of formal core
mock/snapshot success != live service health
proxy success != safe egress
```

## Relation to Hyper Equation routing

The Hyper Equation routes mathematical/semantic kernels.
The Undici Agent layer routes network requests.

Connection:

```text
semantic route chooses what work to do
network dispatch policy chooses how external calls are made
```

Do not collapse them.

## Validator targets

Suggested files:

```text
src/network/dispatchPolicy.ts
src/network/createDispatcher.ts
src/network/redactNetworkSnapshot.ts
src/network/telemetry.ts
tests/network/mock_agent.test.ts
tests/network/snapshot_agent.test.ts
tests/network/proxy_policy.test.ts
```

Suggested GCL registry:

```text
registry/network_dispatch_policies.json
```

## Required gates before use in production-like workflows

```text
1. Redaction test for Authorization/Cookie/proxy credentials.
2. Snapshot replay test.
3. Mock isolation test that blocks accidental live egress.
4. Retry policy test for idempotent vs non-idempotent requests.
5. Proxy/no_proxy behavior test.
6. Telemetry test ensuring no secret-bearing fields are emitted.
```

## Boundary

This bridge is defensive and architectural.

Allowed:

```text
routing policy
proxy boundary discipline
retry/replay testing
snapshot redaction
telemetry classification
```

Blocked:

```text
stealth proxying
credential capture
bypassing network controls
abusing proxies for unauthorized access
leaking secrets into snapshots
```

## Operating sentence

```text
The Undici Agent family gives the Goxel/MOIM runtime a disciplined network-dispatch phenotype: Agent routes origins, Proxy and SOCKS agents declare egress boundaries, RetryAgent records transient repair attempts, and Mock/Snapshot agents create testable receipt surfaces without letting network success become proof.
```
