# SmallCode Constrained Agent Execution Gate

## Purpose

Add SmallCode as a constrained-agent execution gate for the project.

SmallCode is a terminal-native coding agent optimized for small local LLMs, especially models in the 7B-20B range. Its project value is that it does not assume frontier-model context, reliable tool calling, or perfect one-shot planning. Instead, it shrinks the active execution field with context budgeting, TODO decomposition, patch-first edits, working memory, forgiving tool parsing, verifier/governor logic, and optional escalation.

Project shape:

```text
small local model
→ budgeted context
→ category-level tool routing
→ TODO decomposition
→ patch-first mutation
→ verifier / governor receipt
→ Warden escalation only on hard fail
```

## Source

```text
Repository: https://github.com/Doorman11991/smallcode
README branch: master
Integrated: 2026-05-18
```

The README describes SmallCode as an AI coding agent optimized for small LLMs under or around 20B parameters. It emphasizes budget-managed context, multi-format/flexible tool parsing, TODO-file decomposed planning, patch-first editing, persistent working memory, early-stop detection, model profiles, and optional cloud escalation after retry/decompose hard failure.

## Project name

```text
SMALLCODE_CONSTRAINED_AGENT_EXECUTION_GATE
```

Alternative names:

```text
LOCAL_MODEL_WARDEN_EXECUTION_GATE
BUDGETED_AGENT_FIELD_SHRINKER
SMALL_LLM_LOGOGRAM_EXECUTION_GATE
```

## Why this fits

SmallCode is an operational example of field shrinking:

```text
raw coding task
→ summarized context
→ reduced tool schema exposure
→ atomic TODO plan
→ patch-level edit
→ compile/lint/check receipt
```

It is not merely a coding tool. In this stack, it becomes a practical execution model for Semantic Mass routing and logogram-kernel compression under constrained local compute.

## Mapping to project primitives

| SmallCode concept | Project mapping |
|---|---|
| small local LLM | constrained strand / low-capacity agent |
| context budget engine | Semantic Mass field budget |
| TODO-driven planning | Builder decomposition ledger |
| patch-first editing | residual-minimizing mutation |
| forgiving tool parser | Warden-tolerant interface layer |
| working memory | NUVMAP / Delta-DAG local memory |
| early-stop detection | loop scar / coarsening trigger |
| model escalation | Judge/Warden escalation gate |
| BoneScript | logogram/code-kernel compression |
| verifier / governor | Judge/Warden execution receipt |

## BoneScript as code-logogram kernel

SmallCode's README says BoneScript can reduce many backend-generation tool calls into one or two higher-level operations. Project translation:

```text
many low-level tool calls
→ one high-level semantic code kernel
→ deterministic expansion
→ fewer active transitions
→ smaller computational field
```

So a `.bone` file becomes a code logogram:

```math
\Gamma_{\mathrm{bone}}
=
(
\mathrm{schema},
\mathrm{routes},
\mathrm{auth},
\mathrm{db},
\mathrm{events},
\mathrm{sdk},
\epsilon,
\rho
)
```

Expansion path:

```text
.bone packet
→ generated backend project
→ compile/check receipt
→ residual repair if needed
```

## Universal Shortcut Center packet

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

| Packet term | Meaning |
|---|---|
| `X_task` | full software task / repository state |
| `pi_summary` | context-budget projection into signatures/summaries |
| `W_todo` | TODO-file working witness |
| `R_patch` | search-and-replace reconstruction route |
| `I_compile` | compile/lint/test invariant |
| `G_local` | local model/tooling guard |
| `K` | token/tool/compute cost |
| `epsilon` | residual errors after patch/check |

## Semantic radix / logogram connection

SmallCode is a real software analog of the Semantic Radix Field:

```math
b_\star(x)
=
\operatorname*{argmin}_{b,\mathcal G}
[
K_{\mathrm{symbols}}
+
K_{\mathrm{decoder}}
+
K_{\mathrm{routing}}
+
K_{\mathrm{residual}}
+
K_{\mathrm{receipt}}
]
```

In SmallCode terms:

```text
reduce K_context     via summaries/signatures
reduce K_routing     via 2-stage tool routing
reduce K_mutation    via patch-first edits
reduce K_planning    via TODO decomposition
reduce K_failure     via verifier/governor loops
```

## GCCL / imaginary phase codec placement

SmallCode can be treated as an execution-side consumer of GCCL phase packets:

```text
real/survivor packet         → apply patch / compile
imaginary/witness packet     → inspect / summarize / record memory
negative/cancellation packet → revert / remove bad route
negative-imaginary packet    → adversarial test / Warden probe
```

This gives a practical action mapping for imaginary GCCL routing.

## FAMM object

```math
\mathfrak C_{\mathrm{SmallCodeGate}}
=
A_{16}(u_{\mathrm{smallcode}})
\otimes
[
\Sigma_{\mathrm{task}}
+
\Sigma_{\mathrm{context}}
+
\Sigma_{\mathrm{todo}}
+
\Sigma_{\mathrm{patch}}
+
\Sigma_{\mathrm{toolRoute}}
+
\Sigma_{\mathrm{memory}}
+
\Sigma_{\mathrm{verifier}}
+
\Sigma_{\mathrm{escalation}}
+
\Sigma_{\epsilon}
+
\Sigma_{\mathrm{receipt}}
]
```

## BraidStorm use

Each local coding agent becomes a constrained strand:

```math
s_i=(M_i,C_i,T_i,P_i,V_i,\epsilon_i,\Omega_i,\rho_i)
```

where:

| Term | Meaning |
|---|---|
| `M_i` | local model profile |
| `C_i` | context budget state |
| `T_i` | TODO plan state |
| `P_i` | patch proposal |
| `V_i` | verifier result |
| `epsilon_i` | residual after verification |
| `Omega_i` | scar / loop / failure pressure |
| `rho_i` | receipt confidence |

Braid crossing:

```text
agent strand proposes patch
→ verifier checks invariant
→ Warden scars loop/failure
→ escalation only if local route hard-fails
```

## Anti-FAMM / Anti-BraidStorm checks

Anti-FAMM asks:

```text
Did the summary hide a relevant code path?
Did patch-first editing preserve local syntax but break global invariant?
Did the verifier miss a semantic failure?
```

Anti-BraidStorm asks:

```text
Did multiple agents converge on the same wrong patch?
Did tool-call parsing repair a malformed command into the wrong action?
Did TODO decomposition create false local success with global failure?
```

## Warden boundaries

Allowed claim:

```text
SmallCode gives the project a concrete constrained-agent execution model for small local LLMs, using context budgeting, TODO decomposition, patch-first mutation, verifier/governor checks, and escalation gates to shrink the active coding field.
```

Disallowed claim:

```text
SmallCode guarantees small models can perform all frontier-model coding tasks without error or verification.
```

Warden requirements:

```text
patches must be checked
summaries must be treated as lossy
escalation must be bounded
local model failures must become scars/coarsening agents
compile/lint/test receipts must dominate model confidence
```

## Stack placement

```text
SMALLCODE_CONSTRAINED_AGENT_EXECUTION_GATE
→ Semantic Radix / Logogram Kernel layer
→ GCCL Complex Phase Codec action mapping
→ Autonomous Speedrun Harness Gate
→ FAMM Scar Ledger
→ Anti-FAMM / Anti-BraidStorm adversarial checks
→ NUVMAP Delta-DAG execution receipt
→ Builder-Judge-Warden promotion or rejection
```

## Project sentence

SmallCode is a constrained-agent execution gate: instead of assuming frontier-model context and perfect tool calling, it shrinks the computational field through budgeted context, TODO decomposition, patch-first edits, working memory, verifier/governor checks, and optional escalation, making it a practical analog of Semantic Mass routing and logogram-kernel execution for small local models.

## Citation

```bibtex
@online{doorman11991_smallcode,
  title        = {SmallCode},
  author       = {{Doorman11991}},
  organization = {GitHub},
  url          = {https://github.com/Doorman11991/smallcode},
  urldate      = {2026-05-18},
  note         = {Terminal-native coding agent optimized for small local LLMs; README branch master.}
}
```
