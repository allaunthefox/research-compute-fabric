# VLB Nibble-Delta Witness Substrate — Earthside Estimate

Status: HOLD / workbench projection  
Domain: ENE / GCCL / telemetry / compression / witness accounting  
Safety: benign software/data modeling only; not propulsion hardware

## Purpose

This note translates the old Pioneer / VLB instrumentation idea into an Earthside repository experiment:

> Treat repository, Drive, ENE, and instrumentation-like update streams as topology-bearing manifolds whose updates are encoded as counted 4-bit switch events rather than full snapshots.

The goal is to estimate the gain from a **Nibble-Switched Manifold Delta** encoding before writing an implementation.

## Core model

A baseline state is committed once. After that, updates are stored as sparse counted nibble switches.

```text
baseline manifold state
→ local update
→ counted nibble switches
→ witness receipt
→ replay to reconstruct target state
```

A minimal update atom:

```gclang
structure NibbleSwitch where
  locusId    : String        -- NUVMAP / repo / document / symbol locus
  nibble     : UInt4         -- 4-bit transition symbol
  count      : Nat           -- run length / duration / repeated update count
  polarity   : SignedQ16     -- signed contribution or debt
  kotCost    : SignedQ16     -- action cost
  receiptId  : Option String
```

A manifold delta:

```gclang
structure ManifoldDelta where
  baselineHash : String
  targetHash   : String
  sourceDomain  : String
  switches      : Array NibbleSwitch
  deltaGCCL     : DeltaGCCL
  kotCost       : KOTValue
  replayPass    : Bool
```

## Nibble semantics

Use the 4-bit symbol as a compact transition atom:

```text
high 2 bits = quandary control state
low  2 bits = CMYK / strand / domain selector
```

### High bits: quandary state

```text
00 = REJECT / no-change / cooling
01 = ACCEPT / apply update
10 = HOLD / needs witness / recovery
11 = QUARANTINE / break / reset
```

### Low bits: strand selector

```text
00 = K / axis / stable backbone
01 = C / winding / route deformation
10 = M / tension / attestation
11 = Y / break / reset
```

So a symbol is:

```text
[quandary_state][strand]
```

Example:

```text
0101 = ACCEPT + C-winding update
1010 = HOLD + M-attestation update
1111 = QUARANTINE + Y-reset update
```

## Compression estimate

Let:

```text
N = number of loci in a full state
B = bytes per locus in the snapshot representation
r = fraction of loci changed per update epoch
E = bytes per encoded switch event
c = mean run length captured by count compression
```

Then:

```text
Full snapshot bytes = N × B
Nibble-delta bytes  ≈ (N × r / c) × E + receipt overhead
Gain ratio          ≈ Full snapshot bytes / Nibble-delta bytes
```

## Conservative Earthside assumptions

These are deliberately boring values, intended for repo/Drive/ENE metadata and text-update streams rather than deep-space probes.

```text
B = 32 bytes per locus
E = 8–16 bytes per encoded switch after practical framing
receipt overhead = 128–512 bytes per epoch
c = 1–16 depending on local repetition
```

The dominant variable is sparsity: how much of the manifold actually changes per epoch.

## Estimated gains

For large enough states where receipt overhead is amortized:

| Changed loci per epoch | Mean run length | Practical gain estimate | Interpretation |
|---:|---:|---:|---|
| 20% | 1× | 2×–4× | weak sparsity; still useful mostly for witnesses |
| 10% | 2× | 4×–8× | ordinary sparse update stream |
| 5% | 4× | 10×–25× | good repo/ENE delta regime |
| 1% | 8× | 50×–150× | strong long-baseline / telemetry-like regime |
| 0.1% | 16× | 500×+ | very sparse remote-instrument regime |

## Expected gains for this repository

### Near-term realistic target

```text
5×–20× reduction
```

This is realistic for repo/document/ENE update streams where most loci are stable and only a few package states, registry terms, claims, or witness edges change per epoch.

### Strong target

```text
25×–100× reduction
```

This becomes plausible if updates are batched by locus, counted, and replayed against stable baselines using AMMR commits.

### Extreme target

```text
100×–500×+
```

Only plausible for very sparse telemetry-like streams where the baseline is stable, updates are localized, and count compression captures long periods of no-change / repeated state.

## What counts as a gain

A gain is not just smaller bytes. A valid gain must satisfy:

```text
1. replay(baseline, delta) == target
2. AMMR commits baseline and target hashes
3. ΔGCCL shows no hidden loss
4. KOT cost is bounded and paid
5. Warden does not quarantine the update
```

So the system is not allowed to win by deleting evidence.

## Earthside experiment plan

### Phase 0 — Passive measurement

Measure current update sparsity without changing behavior.

```text
Input:
  repo files, Drive-derived ENE exports, wiki definitions, registry docs

Output:
  per-epoch changed loci
  run-length statistics
  estimated delta size
  estimated replay cost
```

### Phase 1 — JSONL delta prototype

Create an append-only stream:

```text
data/nibble-delta/events.jsonl
```

Each line:

```json
{"baseline":"sha256:...","target":"sha256:...","locus":"docs/wiki/Mass_Number.md#G_MNL","nibble":"0101","count":3,"kot":"0x00002000","receipt":"..."}
```

### Phase 2 — Replay verifier

Build a verifier:

```text
tools/nibble_delta/replay.py
```

Checks:

```text
baseline + event stream → target hash
missing receipt → HOLD
invalid replay → QUARANTINE
unbounded update cost → QUARANTINE
```

### Phase 3 — GCCL integration

Add profile deltas:

```text
G_geo, G_comp, G_load, G_spec, G_topo, G_arith, G_MNL, G_AMN
```

A delta is valid only when the transition is smaller **and** lawful.

## Why this belongs in ENE

ENE already treats knowledge packages as manifold objects with semantic vectors, settlement states, and activation/magnitude. Nibble-delta updates turn that idea into a sparse update stream: instead of re-exporting whole package states, only topology-bearing switch events are transmitted and witnessed.

## Risks

| Risk | Mitigation |
|---|---|
| Delta stream loses semantic context | Keep baseline hash + AMMR commit |
| Compression hides evidence | Require replay verifier |
| Old metaphors contaminate current framing | FAMM Sieve sanitizes raw source |
| False gain from metric shift | ΔGCCL multi-axis gate |
| Overspend or runaway update churn | KOT budget + Warden quarantine |

## Initial conclusion

The Earthside version is worth implementing as a measurement/prototype layer.

Expected practical gain:

```text
5×–20× near term
25×–100× if sparsity and run-length structure are good
100×+ only for telemetry-like streams
```

The strongest non-byte gain is not compression ratio alone. It is that every update becomes:

```text
small
replayable
witnessed
budgeted
quarantinable
```

That makes this a good fit for GCCL/KOT/ENE rather than a generic compression trick.
