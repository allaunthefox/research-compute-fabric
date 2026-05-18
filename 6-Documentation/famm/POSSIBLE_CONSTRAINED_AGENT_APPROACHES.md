# Possible Constrained-Agent Approaches

## Purpose

Consolidate the project's prior SmallCode-like approaches and add GLIA as a persistent-memory substrate.

This document is intentionally named **possible approaches**. It is a routing map, not a final architecture claim. Each approach is a candidate route for shrinking the active computational field while preserving receipts, memory, verification, and Warden boundaries.

```text
small/local model or constrained agent
→ memory recall
→ context-budget projection
→ TODO/plan decomposition
→ patch/logogram mutation
→ verifier/governor check
→ adversarial dual tests
→ FAMM scar/coarsening or promotion
→ memory update receipt
```

## External anchors

### SmallCode

```text
Repository: https://github.com/Doorman11991/smallcode
Role: constrained local coding agent / execution field shrinker
```

SmallCode is a terminal-native coding agent optimized for small local LLMs, especially 7B-20B models. It uses budget-managed context, TODO-file decomposition, patch-first editing, forgiving tool parsing, working memory, verifier/governor logic, early-stop detection, and optional escalation.

### GLIA

```text
Repository: https://github.com/Eshaan-Nair/Glia-AI
Role: local-first cross-tool persistent memory / recall substrate
```

GLIA describes itself as a local-first memory layer that captures AI conversations, builds a searchable knowledge graph, and injects relevant context into new prompts. It has two shared-memory interfaces: a browser extension for chat websites and an MCP server for coding tools. Both read/write the same backend memory store.

GLIA features especially relevant to this stack:

```text
browser extension + MCP server
shared local memory store
hybrid retrieval: sentence vectors + chunk vectors + FTS5
knowledge graph extraction
HyDE retrieval
small-to-big retrieval
surgical sentence trimming
background indexing
project isolation
prune_memory for outdated facts
SQLite/WAL local mode
```

## Consolidated approach map

| Approach | Role | Existing project analogue | External analogue |
|---|---|---|---|
| Hermes field-operator bridge | controlled workflow operator | Hermes / Warden receipts | GLIA MCP + SmallCode skills |
| FastPatchCheck | fast viability check | local patch smoke test | SmallCode verifier |
| StructuralAdmissibilityCheck | invariant legitimacy check | Judge structural gate | SmallCode governor |
| BridgeModel_GlobalGate | hard execution choke point | guarded transition | SmallCode tool routing / GLIA injection guard |
| BridgeModel_Linter | architecture safety scanner | Warden pre-runtime alert | SmallCode parser repair / GLIA sanitization |
| GCL Combined Coding Surface | typed coding substrate | encode/mutate/repair/gate/receipt | coding tools + MCP surfaces |
| Logogram Chirality Route Gate | semantic kernel routing | glyph/code kernel phase | BoneScript / semantic code packets |
| TraceInvariant direction | session continuity / drift prevention | trace budget + failure ledger | GLIA memory + SmallCode TODO/session state |
| Anti-FAMM | witness blind-spot adversary | projection-nullspace attack | memory/summary hidden-failure tests |
| Anti-BraidStorm | hostile crossing adversary | false survivor detection | multi-agent patch convergence tests |

## Approach A — Memory-first agent substrate

Use GLIA as the memory substrate.

```text
conversation / coding session
→ store_memory / Save Chat
→ embeddings + knowledge graph triples
→ recall_context / auto-injection
→ project-scoped memory packet
```

Project mapping:

```math
\Gamma_{\mathrm{GliaMemory}}
=
(
X_{\mathrm{history}},
\pi_{\mathrm{chunk}},
W_{\mathrm{recall}},
R_{\mathrm{inject}},
I_{\mathrm{decision}},
G_{\mathrm{project}},
K,
\epsilon
)
```

| Packet term | Meaning |
|---|---|
| `X_history` | full conversation / project history |
| `pi_chunk` | chunking, embedding, graph extraction |
| `W_recall` | retrieved context / graph facts |
| `R_inject` | prompt or MCP context injection |
| `I_decision` | remembered project decisions and constraints |
| `G_project` | project/session isolation guard |
| `K` | retrieval, storage, and prompt budget cost |
| `epsilon` | stale, irrelevant, or missing memory residual |

Warden checks:

```text
stale memory
wrong project memory
cross-project leakage
prompt injection in retrieved chunks
PII leakage
over-injection / context noise
memory facts treated as proof
```

## Approach B — Execution-first constrained coding agent

Use SmallCode-like architecture as the execution substrate.

```text
raw coding request
→ budgeted context summary
→ TODO decomposition
→ patch-first edit
→ compile/lint/test verifier
→ Warden decision
→ escalation only on hard fail
```

Project mapping:

```math
\Gamma_{\mathrm{SmallCode}}
=
(
X_{\mathrm{task}},
\pi_{\mathrm{summary}},
W_{\mathrm{todo}},
R_{\mathrm{patch}},
I_{\mathrm{compile}},
G_{\mathrm{local}},
K,
\epsilon
)
```

Useful when:

```text
local models are weaker than frontier models
context is limited
whole-file rewrites are risky
patches can be locally verified
session state must survive across turns
```

Warden checks:

```text
patch compiles but violates global invariant
summary hid relevant code path
tool parser repaired into wrong command
TODO plan says done while tests fail
local loop / repetition detected
unbounded cloud escalation
```

## Approach C — GLIA + SmallCode combined route

This is the strongest practical integration.

```text
GLIA recalls durable project memory
→ SmallCode executes constrained patch plan
→ verifier emits receipt
→ GLIA stores final decision and scars
```

Pipeline:

```text
1. identify_active_project / project selection
2. recall_context for relevant prior decisions
3. SmallCode builds TODO plan
4. execute patch-first edit
5. run verifier / tests / lint
6. Anti-FAMM checks summary/memory blind spots
7. Anti-BraidStorm checks false convergence across candidate patches
8. store_memory with final decision, failure, or scar
9. NUVMAP Delta-DAG records the route
```

This route turns memory and execution into a closed loop:

```text
memory informs action
action emits receipt
receipt updates memory
future recall sees the scar or promotion
```

## Approach D — Hermes-style authority bridge

Hermes remains the authority/workflow bridge.

```text
tool or agent may execute/suggest/schedule
but may not promote without receipts
```

Use Hermes when the route needs explicit permissioning:

```text
skill execution
scheduled audit
automation
cross-tool workflow
write authority
promotion-state changes
```

Project mapping:

```text
Hermes = authority substrate
GLIA = memory substrate
SmallCode = execution substrate
FAMM = scar/residual substrate
BJW = decision substrate
NUVMAP = route-memory substrate
```

## Approach E — FastPatch + StructuralAdmissibility route

This is the local-to-global verifier route.

```text
FastPatchCheck
→ local viability
→ StructuralAdmissibilityCheck
→ invariant legitimacy
→ escalationNeeded or promotion
```

Use it as the default verification stack for coding agents:

```text
patch is syntactically valid
patch compiles/tests locally
patch preserves architectural invariant
patch has no hidden route leak
patch emits receipt
```

## Approach F — Logogram/code-kernel route

Use semantic/logogram kernels to reduce active tool calls.

```text
many low-level tool calls
→ one high-level semantic kernel
→ deterministic expansion
→ compile/check receipt
```

External analogue:

```text
BoneScript in SmallCode
```

Project analogue:

```text
LOGOGRAM_RADIX_FIELD
GCCL_COMPLEX_PHASE_CODEC
CODE_LOGOGRAM_KERNEL
```

Rule:

```text
internal bases may be weird;
external recovery must be boring.
```

So every code-logogram must expand back to ordinary files, tests, bytes, or standard source code with receipts.

## Approach G — GCCL complex phase action routing

Use GCCL complex phase routing to classify agent actions:

```text
phase  1   → survivor action / apply patch
phase  i   → witness action / inspect, recall, summarize
phase -1   → cancellation action / revert, remove, undo
phase -i   → adversarial action / probe, fuzz, Warden test
```

With omnidirectional GCCL:

```math
\theta=e^{i\phi}
```

becomes a continuous routing field rather than a four-state switch.

Use this when actions need to carry:

```text
chirality
witness direction
cancellation pressure
scar burden
receipt confidence
adversarial pressure
```

## Approach H — Adversarial duals as mandatory hardening

Before promotion, run:

```text
Anti-FAMM
→ searches for invisible residuals and false scars

Anti-BraidStorm
→ searches for false convergence, aliasing, wrong-handed recombination, receipt drift
```

For memory-agent systems, this becomes:

```text
Anti-FAMM memory test:
  Does retrieved context omit a fact that changes the decision?

Anti-BraidStorm patch test:
  Do several agents converge on the same wrong edit because they share a poisoned memory or false summary?
```

## Approach I — NUVMAP Delta-DAG execution receipts

Every memory/action/check route becomes a Delta-DAG edge:

```text
state_t
→ recalled context
→ patch proposal
→ verifier result
→ adversarial result
→ state_t+1
```

Receipt packet:

```text
memory_hash
context_hash
patch_hash
test_hash
scar_hash
promotion_state
```

This gives the project replay, provenance, and failure reuse.

## Recommended practical architecture

```text
GLIA persistent memory
→ SmallCode constrained execution
→ FastPatchCheck / StructuralAdmissibilityCheck
→ Anti-FAMM / Anti-BraidStorm adversarial probes
→ FAMM scar/coarsening ledger
→ NUVMAP Delta-DAG route receipt
→ GLIA store_memory / project summary update
```

Short form:

```text
GLIA remembers.
SmallCode acts.
FAMM scars.
BJW decides.
NUVMAP receipts.
Hermes governs.
```

## Possible implementation tiers

### Tier 0 — Manual doctrine

Use the document as workflow guidance only.

```text
recall manually
patch manually
verify manually
store decision manually
```

### Tier 1 — Local memory + constrained execution

Use GLIA for memory and SmallCode for coding.

```text
GLIA recall_context
→ SmallCode plan/patch
→ tests
→ GLIA store_memory
```

### Tier 2 — Receipt-bearing workflow

Add FAMM-style receipts.

```text
memory hash
patch hash
test hash
scar class
promotion decision
```

### Tier 3 — Adversarial hardening

Add Anti-FAMM and Anti-BraidStorm.

```text
memory blind-spot probes
summary-loss checks
false-convergence checks
patch alias checks
```

### Tier 4 — GCCL phase-routed agents

Use complex phase routing to classify actions and automate Warden behavior.

```text
apply / witness / cancel / adversarial probe
```

## Warden boundaries

Allowed claim:

```text
These approaches give the project several concrete routes for constrained local-agent execution, persistent memory, patch-first coding, logogram-code kernels, and adversarial verification.
```

Disallowed claim:

```text
SmallCode, GLIA, or any local-agent stack guarantees correctness without tests, receipts, project isolation, and Warden checks.
```

Hard rules:

```text
memory is evidence, not proof
summaries are lossy
retrieval can be stale
patches must be verified
agent convergence can be false
cloud escalation must be bounded
project isolation must be checked
receipts dominate model confidence
```

## Project sentence

The possible constrained-agent approach is to pair GLIA-style durable memory with SmallCode-style constrained execution: recall the right project context, decompose into atomic TODOs, mutate by patch/logogram kernels, verify through fast and structural gates, attack with Anti-FAMM and Anti-BraidStorm, then store the resulting receipt, scar, or promotion back into the memory graph for the next run.

## Citations

```bibtex
@online{doorman11991_smallcode,
  title        = {SmallCode},
  author       = {{Doorman11991}},
  organization = {GitHub},
  url          = {https://github.com/Doorman11991/smallcode},
  urldate      = {2026-05-18},
  note         = {Terminal-native coding agent optimized for small local LLMs; README branch master.}
}

@online{nair_glia_ai,
  title        = {GLIA — Persistent Memory for AI Coding Tools},
  author       = {Nair, Eshaan},
  organization = {GitHub},
  url          = {https://github.com/Eshaan-Nair/Glia-AI},
  urldate      = {2026-05-18},
  note         = {Local-first memory layer with browser extension and MCP server sharing one memory store.}
}
```
