# Drift-Aware Repository Memory Bridge

Status: V_scope / external repo-memory bridge
Authority: `agents-remember-md` README and workbench integration analysis
Related:

- `docs/gcl/ThreeLayerBuilderJudgeWardenGate.md`
- `docs/gcl/AdaptiveAngrySphinxCopyWriteRationale.md`
- `docs/gcl/FederatedNanokernelSwarmDoctrine.md`
- `docs/gcl/RunawayDigitalCellDivisionDoctrine.md`
- `docs/gcl/SurfMCPFusionGate.md`

## Purpose

This document maps the `agents-remember-md` repository-memory pattern into the Research Stack.

The core idea:

```text
Every important source file can have a path-local companion memory card.
That card records local quirks, hidden contracts, related files, and a source commit hash.
Before an agent trusts the card, it checks for drift.
```

This is exactly the kind of low-friction, receipt-backed memory layer needed by coding agents.

## Source model

The upstream pattern is described as:

```text
source file
  -> mirrored onboarding companion markdown
  -> commit hash of source at last verification
  -> drift check before planning
  -> refresh stale companion before use
```

Example shape:

```text
resolve_auto_editor/src/orchestrator/core_editor.py

ar-management/onboarding/resolve_auto_editor/orchestrator-and-agent-loop/src/orchestrator/core_editor.py.md
```

## Why this matters

A top-level `AGENTS.md` is necessary but insufficient.

It gives global operating law, but it cannot reliably carry every file-local invariant, migration scar, hidden dependency, and domain-specific gotcha.

The companion-card layer makes context:

```text
local
path-addressable
versioned
staleness-checkable
agent-discoverable
```

## Stack mapping

| Repository-memory concept | Research Stack concept |
|---|---|
| Source file | digital cell / route phenotype source |
| Companion onboarding file | local memory receipt / context card |
| Source commit hash | drift anchor / provenance checkpoint |
| Drift detection | Judge freshness gate |
| Refresh stale card | Builder/Judge memory repair |
| Approval before implementation | Warden action gate |
| Update after approved change | ENE inheritance rule |
| Heavy workflow phase gates | Builder/Judge/Warden staged route control |

## Builder/Judge/Warden interpretation

```text
Builder
  constructs or refreshes the companion memory card

Judge
  checks whether the companion card is fresh against the source file commit

Warden
  prevents planning or implementation from trusting stale or speculative memory

Adaptive AngrySphinx
  scars repeated drift, repeated missing cards, or repeated attempts to plan from stale notes
```

## ENE interpretation

The companion onboarding tree is an ENE-like memory substrate for code.

It stores durable local context only after the relevant source state is known.

```text
source edit
  -> approved change
  -> companion update
  -> commit hash refresh
  -> durable repository memory
```

This prevents memory pollution:

```text
planned behavior
  != implemented behavior
  != inherited memory
```

Only approved, source-backed state should be promoted.

## Runaway digital cell division prevention

Agent memory can also divide uncontrollably:

```text
chat explanation
  -> task note
  -> speculative docs
  -> stale onboarding
  -> future agent trusts it
  -> bad edits multiply
```

The drift-aware companion-card pattern blocks that by requiring:

```text
source-local card
commit-hash anchor
drift check before planning
approval before code changes
onboarding update only after approved implementation
```

## Mass/route interpretation

Each companion card reduces local route mass.

Without the card:

```text
agent must rediscover architecture from code and search
```

With the card:

```text
agent reads the relevant local invariant at the path where it is needed
```

But the card only reduces route mass if it is fresh.

```text
fresh card = context compression
stale card = contamination risk
missing card = discovery cost
```

## Drift state model

Candidate state labels:

```text
fresh
  source commit matches companion anchor

drifted
  source changed since companion anchor

missing
  no companion exists for touched file

directional_only
  useful but not source-fresh; may guide exploration but not implementation authority

quarantined
  known misleading or repeatedly stale companion
```

## Minimal card schema

```yaml
source_path: src/example/module.py
source_commit: abc1234
last_verified: 2026-05-01
trust_state: fresh
related_files:
  - src/example/caller.py
  - src/example/schema.py
hidden_contracts:
  - Do not change serialized field names without migration.
  - This module is called indirectly by the scheduler.
failure_scars:
  - Prior refactor broke retry idempotency.
update_policy: after approved implementation only
```

## Agent loop

```text
agent opens source file
  -> derive companion path
  -> load companion card if present
  -> run drift check
  -> if fresh, use as local memory
  -> if drifted, refresh or mark directional-only
  -> plan with explicit trust state
  -> wait for approval before implementation
  -> after approved change, update companion card
```

## Relation to Surf MCP / external tools

Surf MCP or other browser/API tools can help retrieve or operate on repository context, but the memory card remains the local authority only if:

```text
path is correct
source hash is checked
card trust state is declared
Warden allows use
```

External tools may fetch; they do not replace drift checks.

## What this solves

```text
agent forgetfulness
hidden file quirks
cross-file contracts not visible in import graph
context-window waste
AGENTS.md overload
stale documentation ambiguity
repeated developer explanations getting lost in chat
```

## What it does not solve by itself

```text
formal correctness
security safety
review authority
test coverage
design validity
truth of stale notes
```

## Allowed claim

```text
A path-local, commit-hash-anchored repository memory layer lets coding agents retrieve relevant file-specific context and detect stale onboarding before planning, turning repeated chat explanations into versioned, drift-aware memory.
```

## Blocked claims

```text
A companion card proves the code is correct.
A fresh companion card replaces tests.
A top-level AGENTS.md is enough for large systems.
Stale onboarding may be trusted because it is useful.
Agent-written memory may be promoted before implementation approval.
```

## Operating sentence

```text
Drift-aware repository memory is the codebase-local ENE layer for agents: every source file may have a path-mirrored companion card that compresses local quirks and cross-file contracts, but the card only becomes planning authority after commit-hash drift checks, declared trust state, and Builder/Judge/Warden approval discipline.
```
