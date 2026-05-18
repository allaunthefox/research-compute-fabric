# Possible Constrained-Agent Approaches — Deep Dive Addendum

## Purpose

Extend `POSSIBLE_CONSTRAINED_AGENT_APPROACHES.md` with the older and less obvious attempts that point toward SmallCode-like constrained execution, GLIA-like persistent memory, key-value memory fields, compressed context surfaces, and Warden-gated agent workflows.

This addendum captures the deeper lineage:

```text
N-space KV memory
→ gossip scalar execution
→ folded KV-cache surface
→ ENE / Perpetual Traveler substrate split
→ Hermes authority bridge
→ patch/admissibility verification
→ BridgeModel global gate
→ GCL combined coding surface
→ logogram/chirality route gate
→ trace-level execution discipline
→ SmallCode / GLIA external anchors
```

## Found prior attempts

### 1. N-space key-value reward memory

Earlier idea:

```text
N-space key-value store
→ reward tied to reduction function
→ sparsity search
→ rounded number spaces
→ drop low-value entries for retention
```

This is the old key-value-memory route you were remembering. It is not only a KV cache. It is a **reward-scored reduction memory**.

Suggested packet:

```math
\Gamma_{\mathrm{NSpaceKV}}
=
(
q,
K(q),
V(q),
R_{\mathrm{reduction}}(q),
S_{\mathrm{sparse}}(q),
\Omega_{\mathrm{scar}}(q),
\rho_q
)
```

Where:

| Term | Meaning |
|---|---|
| `q` | rounded n-space coordinate / key |
| `K(q)` | key / route identity |
| `V(q)` | stored value / memory packet |
| `R_reduction` | reward from reducing future work |
| `S_sparse` | sparsity / uniqueness score |
| `Omega_scar` | failure or route-risk burden |
| `rho_q` | receipt hash / confidence |

Retention rule:

```math
\operatorname{keep}(q)=
\mathbf 1[
\alpha R_{\mathrm{reduction}}(q)
+
\beta S_{\mathrm{sparse}}(q)
-
\gamma\Omega_{\mathrm{scar}}(q)
>
\Theta
]
```

Project role:

```text
productive entries survive
redundant entries merge
low-value routes prune
bad routes respawn with encoded failure reason
```

How it connects to GLIA:

```text
GLIA stores chunks/triples.
N-space KV scores what should be retained, pruned, scarred, or promoted.
```

### 2. Round → KV lookup → nearest-neighbor → residual patch cascade

Earlier compression/reconstruction cascade:

```text
round
→ KV lookup
→ nearest-neighbor estimate
→ residual patch
```

This is a precise ancestor of Semantic Radix / logogram codec recovery.

Packet shape:

```text
[χ, k, q16_rounded, δ, ε]
```

Interpretation:

| Field | Meaning |
|---|---|
| `χ` | color / chirality / eigenclass |
| `k` | dictionary or kernel key |
| `q16_rounded` | rounded fixed-point coordinate |
| `δ` | nearest-neighbor delta |
| `ε` | exact residual repair |

Three-tier decoder:

```text
exact dictionary
→ rounded parametric template
→ nearest-neighbor + residual
```

Project role:

```text
This is the canonical recovery path for weird internal bases back into ordinary exact outputs.
```

### 3. Weird machine / reconstruction VM

Earlier concept:

```text
compression at scale discovers a weird machine
logograms become opcodes
color/eigen classes become dispatch
residuals become patch streams
```

Proposed bounded reconstruction ISA:

```text
LIT
LOGO
COLOR
QSET
BLEND
BRAID
COPY
PATCH
CHECK
HALT
```

Project role:

```text
compressed stream
→ bounded reconstruction VM
→ receipt/hash checks
→ canonical output
```

This directly anticipates:

```text
Semantic Radix Field
GCCL Complex Phase Codec
SmallCode constrained execution
BoneScript/code-logogram kernel
```

### 4. Zip spread / receipted shard fanout

Earlier replacement for zipbomb framing:

```text
zip spread
→ bounded receipted shard fanout
```

Archive declares budgets:

```text
max_output_size
shard_count
recursion_depth
max_decode_steps
final_output_hash
```

Shard fields:

```text
shard_id
output_offset
size
hash
budget
receipt
```

Project role:

```text
safe decompression fanout
bounded reconstruction
anti-zipbomb Warden guard
```

This belongs with constrained agents because autonomous tools need the same bounded expansion rule:

```text
agent plan fanout must declare budget, depth, and receipts.
```

### 5. OISC / n-gossip scalar execution

Earlier scalar execution idea:

```text
one-instruction-set computer
→ four-gate logic
→ n-gossip 1D scalars
→ parallel spawn based on folded manifold shape
→ local-neighborhood update sharing
→ prune non-informative scalars
→ respawn with failure reason encoded
```

Project interpretation:

```text
minimal instruction
+ manifold-shaped parallelism
+ gossip update propagation
+ failure-aware scalar respawn
```

This is an ancestor of:

```text
BraidStorm Gossip
Small local coding agents
Anti-BraidStorm hostile convergence checks
```

### 6. N-folded MMR gossip surface as KV cache

Earlier memory model:

```text
linear KV cache
→ n-folded MMR gossip surface
→ local neighborhood retrieval
→ small-world witness propagation
→ cryptographically authenticated context summary
```

Role:

```text
attention history becomes compressed topology
retrieval becomes local / folded / gossip-assisted
context becomes witness mass instead of unbounded transcript
```

Use with GLIA:

```text
GLIA retrieves context.
MMR gossip surface compresses long-session state.
N-space KV scores retention.
NUVMAP receipts the route.
```

### 7. ENE + Perpetual Traveler OS + GeoCognition split

Earlier correction:

```text
ENE = database / memory substrate
Perpetual Traveler OS = ISA / substrate runtime
GeoCognition = map / theory layer
```

Project split:

```text
ENE remembers.
Perpetual Traveler OS executes traversal.
GeoCognition maps route meaning.
FAMM / PIST / PBACS / MOIM act as engines or policies over the substrate.
```

This is the internal ancestor of:

```text
GLIA = memory substrate
SmallCode = execution substrate
FAMM/BJW = scar + decision substrate
```

### 8. Hermes Agent Field Operator Bridge

Hermes was already framed as:

```text
field operator / messenger / skill runtime
```

Hermes may:

```text
execute
remember
suggest
schedule
run skills
```

Hermes may not:

```text
promote without receipts
```

Authority split:

```text
Hermes = workflow layer
GCL = coding-space authority
Lean = proof authority
Warden = promotion gate
ENE = distributed persistence / sync / swarm substrate
```

This is the governance ancestor of SmallCode + GLIA.

### 9. FastPatchCheck / StructuralAdmissibilityCheck

Earlier verification stack:

```text
FastPatchCheck
→ local viability
→ StructuralAdmissibilityCheck
→ invariant legitimacy
→ AdmissibilityPipeline
→ escalationNeeded
```

FastPatchCheck fields:

```text
syntaxOK
typecheckOK
interfaceOK
importOK
testsSmokeOK
safetyOK
rollbackOK
```

StructuralAdmissibilityCheck fields:

```text
intentPreserved
invariantsPreserved
couplingOK
hiddenDistBounded
recoveryPreserved
observabilityOK
ethicalRiskBounded
```

Project role:

```text
SmallCode patch-first editing should feed this verifier stack.
```

### 10. BridgeModel global gate and linter

Earlier hard execution choke point:

```text
globalGate
→ gateTransition
→ guardedStep
```

Linter checked:

```text
missing global gate
direct execution bypass
missing NoSurface handling
viability without policy
unknown transitions not defaulting to alert
```

Project role:

```text
never let a tool route around Warden/GCL gates
make unsafe architecture visible before runtime
```

This is the safety ancestor of:

```text
SmallCode governor
GLIA injection guard
Hermes authority layer
```

### 11. GCL Combined Coding Surface

Earlier coding surface slots:

```text
symbolic_code
semantic_profile
mass_profile
signal_profile
computation_profile
admissibility
closure
receipts
```

Canonical operations:

```text
encode
express
mutate
recombine
repair
gate
project
receipt
oppose
synthesize
```

This is the umbrella that SmallCode and GLIA fit inside.

### 12. Logogram Chirality Route Gate

Earlier logogram route properties:

```text
route direction
handedness
phase
placement
modifier family
operator compatibility
```

This directly precedes:

```text
Semantic Radix Field
GCCL Complex Phase Codec
BoneScript / code-logogram kernels
phase-routed agent actions
```

### 13. Clean-room attribution / prior-art memory

The project already had a prior-art/citation hygiene pattern for external agent/memory systems.

Existing adaptation concepts:

```text
session lineage
FTS5 virtual table
pre-reset memory saving
schema versioning
WAL mode + retry jitter
OpenAI-compatible spillover tier
```

Use for SmallCode and GLIA:

```text
external anchor
→ clean adaptation note
→ project-specific mapping
→ Warden boundary
→ citation
```

### 14. VS Code / Copilot skill-index context

Captured editor-agent context included:

```text
customization skills
agent modes
subagent exploration
skill files
MCP setup context
search-view retrieval
```

Project role:

```text
editor agent
→ skills / prompts / agent modes
→ read/write customization files
→ subagent exploration
→ project-local workflow memory
```

This is another surface for Hermes + GLIA + SmallCode style execution.

### 15. Trace-level execution discipline

Earlier trace discipline included:

```text
execution trace
trace budget
failure ledger
retry policy
drift accumulator
convergence window
surface report: full / downgraded / alert / noSurface
```

Project role:

```text
local lawful steps can still drift globally
trace receipts prevent silent degradation across long runs
```

SmallCode's TODO/session state and GLIA's durable memory are practical examples of why this matters.

## Combined architecture after deep dive

```text
GLIA persistent memory
→ N-space KV scoring / sparse retention
→ MMR gossip surface for long-context compression
→ SmallCode constrained execution
→ FastPatchCheck / StructuralAdmissibilityCheck
→ BridgeModel global gate
→ Anti-FAMM / Anti-BraidStorm adversarial probes
→ FAMM scar/coarsening ledger
→ NUVMAP Delta-DAG route receipt
→ GLIA store_memory / project summary update
→ Hermes governs authority and scheduling
```

Short form:

```text
GLIA remembers.
N-space KV scores.
MMR folds context.
SmallCode acts.
FastPatch verifies.
BridgeModel gates.
FAMM scars.
BJW decides.
NUVMAP receipts.
Hermes governs.
```

## Implementation tiers

### Tier 0 — Manual doctrine

```text
recall manually
patch manually
verify manually
store decision manually
```

### Tier 1 — GLIA + SmallCode

```text
GLIA recall_context
→ SmallCode plan/patch
→ tests
→ GLIA store_memory
```

### Tier 2 — Receipt-bearing verifier

```text
memory hash
context hash
patch hash
test hash
scar class
promotion decision
```

### Tier 3 — N-space KV retention

```text
memory entry
→ reduction reward
→ sparsity score
→ retention / prune / scar
```

### Tier 4 — MMR gossip surface

```text
long history
→ folded context surface
→ local retrieval + gossip witness propagation
```

### Tier 5 — Adversarial hardening

```text
memory blind-spot probes
summary-loss checks
false-convergence checks
patch alias checks
```

### Tier 6 — GCCL phase-routed agents

```text
apply / witness / cancel / adversarial probe
```

## Warden boundaries

Allowed claim:

```text
These approaches give the project several concrete routes for constrained local-agent execution, persistent memory, patch-first coding, logogram-code kernels, sparse key-value retention, folded KV-cache context, and adversarial verification.
```

Disallowed claim:

```text
SmallCode, GLIA, N-space KV, folded KV cache, or any local-agent stack guarantees correctness without tests, receipts, project isolation, and Warden checks.
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
low-reward memory deletion must not destroy provenance
folded KV compression must preserve recovery receipts
```

## Project sentence

The full constrained-agent lineage is broader than SmallCode or GLIA: the project already had N-space key-value reward memory, rounded KV lookup with residual repair, n-gossip scalar execution, folded KV-cache surfaces, ENE/PTOS substrate separation, Hermes authority, FastPatch/Structural admissibility, BridgeModel global gates, GCL coding surfaces, logogram chirality, and trace-level discipline. SmallCode and GLIA are therefore external implementation anchors for a pattern already present: remember through a local memory graph, score through sparse key-value reductions, act through constrained patch/logogram kernels, verify through fast and structural gates, attack with adversarial duals, and receipt every route through FAMM/NUVMAP before promotion.

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
