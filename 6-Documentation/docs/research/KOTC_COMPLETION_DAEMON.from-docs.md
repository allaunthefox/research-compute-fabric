# KOTC — Kinetic Operation Token Completion Daemon

Status: HOLD / prototype scaffold
Domain: OTOM Galaxy Compiler Workbench / Invariant Receipt Protocol / local code completion
Safety posture: bounded completion assistant; not an authority source

## Purpose

KOTC is a bounded microLLM-style completion daemon for the Sovereign Research Stack.

It treats code completion as an auditable compiler operation:

```text
completion request
→ context slice
→ candidate completion
→ policy checks
→ KOT debit
→ receipt
→ ACCEPT / REJECT / HOLD / QUARANTINE
```

The daemon exists because this codebase is too large and cross-coupled to rely on ordinary free-form autocomplete. Suggestions must be scoped, budgeted, and receipt-bearing.

## Design rule

> A completion is not code until it survives policy, cost, and invariant review.

KOTC may propose local completions, scaffolds, manifests, and repair candidates. It may not certify proofs, promote models, weaken invariants, or introduce new core claims without receipts.

## Roles

| Role | Description |
|---|---|
| Context slicer | Selects local files, symbols, policies, and nearby examples |
| MicroLLM adapter | Produces bounded candidate completions |
| Policy filter | Rejects forbidden patterns before insertion |
| KOT accountant | Assigns deterministic action cost / burn rate |
| Receipt emitter | Records completion context, outcome, checks, and hash |
| Warden gate | Quarantines unsafe or overbroad suggestions |

## Completion modes

```text
DRAFT  = exploratory scaffold; may include TODOs; cannot promote
REPAIR = compiler-error / test-error repair; must preserve local intent
STRICT = core-safe completion; no floats, no theorem weakening, no unchecked invariants
```

Recommended defaults:

| Area | Default mode |
|---|---|
| Lean theorem repair | REPAIR |
| Fixed-point arithmetic / hot path | STRICT |
| Docs / workflow manifests | DRAFT or REPAIR |
| Invariant definitions | STRICT + human review |
| Physical/SI claims | STRICT + evidence receipt |

## Hard policy checks

KOTC must flag or quarantine candidates that violate:

```text
no_float_hot_path
no_unreviewed_physical_claim
no_theorem_weakening
no_unchecked_invariant_introduction
no_unbudgeted_compiler_pass
no_authority_escalation
no_silent_receipt_drop
no_unbounded_recursion
```

## Receipt shape

Each completion emits a receipt bundle:

```json
{
  "receipt_type": "kotc.completion.v1",
  "completion_id": "kotc_000001",
  "mode": "REPAIR",
  "target_module": "Semantics.InvariantReceipt.Core",
  "context_files": ["Semantics/InvariantReceipt/Core.lean"],
  "symbol_refs": ["Receipt", "Outcome", "ModelUpgrade"],
  "kot_cost_q16": "0x00011000",
  "risk": "medium",
  "decision": "HOLD",
  "policy_checks": {
    "no_float_hot_path": "passed",
    "no_theorem_weakening": "passed"
  },
  "candidate_hash": "sha256:...",
  "notes": ["Requires human review before insertion"]
}
```

## Quandary decision states

| State | Meaning |
|---|---|
| ACCEPT | Candidate passed policy and may be staged |
| REJECT | Candidate is invalid or irrelevant |
| HOLD | Candidate is plausible but requires witness/human review |
| QUARANTINE | Candidate violates policy or creates unsafe drift |

## Integration with OTOM Galaxy Compiler

KOTC plugs into the Galaxy-inspired compiler workbench as a support node:

```text
Workflow DAG
├─ pass registry
├─ invariant gates
├─ KOT ledger
├─ AMMR receipts
├─ quarantine store
└─ KOTC completion daemon
```

Each completion request is modeled as a workflow event and can be replayed or audited.

## Allowed first-version behavior

The first version is a local simulator, not a real model integration.

It should:

1. accept mock completion requests
2. select declared context files
3. run policy checks over the proposed candidate text
4. estimate KOT cost deterministically
5. assign ACCEPT / REJECT / HOLD / QUARANTINE
6. emit JSON receipt bundles
7. support downstream integration with AMMR / InvariantReceipt

## Not allowed

KOTC must not:

- silently edit promoted core files
- claim a theorem is proven
- replace Lean proof obligations with comments
- introduce floats in fixed-point hot paths
- create physical claims without evidence mapping
- mark speculative metaphors as core modules
- bypass Warden / promotion ladder status

## Implementation artifacts

Initial scaffold:

```text
tools/kotc/kotc_sim.py
schemas/kotc_completion_receipt.schema.json
docs/research/KOTC_COMPLETION_DAEMON.md
```

## Operating sentence

> KOTC is a bounded completion daemon: every suggestion pays KOT, passes policy checks, and emits a receipt before it can become code.
