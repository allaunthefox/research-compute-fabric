# OR-Tools WASM Constraint Solver Gate

## Purpose

Add `or-tools-wasm` as a browser/TypeScript constraint-solver execution gate for the project.

This is important because it puts serious optimization solvers into the same environment as web agents, dashboards, browser-side witnesses, and TypeScript tooling.

```text
constraint model
→ WebAssembly OR-Tools runtime
→ validate model
→ solve in worker / local runtime
→ optimization receipt
→ FAMM / Warden decision
```

## Source

```text
Repository: https://github.com/Axelwickm/or-tools-wasm
Default branch inspected: stable
Integrated: 2026-05-18
```

The README describes `or-tools-wasm` as Google OR-Tools running as multithreaded WebAssembly for TypeScript. It exposes solver-specific runtimes and TypeScript APIs for CP-SAT, routing, MPSolver, MathOpt, and PDLP. It is packaged as ESM and verified across Vite, Webpack, Rollup, Node, Deno, and Bun.

## Project name

```text
OR_TOOLS_WASM_CONSTRAINT_SOLVER_GATE
```

Alternative names:

```text
BROWSER_CP_SAT_WARDEN_GATE
LOCAL_OPTIMIZATION_RECEIPT_GATE
WASM_CONSTRAINT_PLANNER_GATE
```

## Why this matters

The project has many places where choices must be made under hard constraints:

```text
which agent acts next
which patch route is cheapest
which memory entries survive pruning
which witness channel closes a shadow gap
which BraidStorm crossing schedule avoids aliasing
which compute budget allocation is admissible
which proof-search branch should be explored
```

`or-tools-wasm` gives a practical route to solve these as explicit optimization models rather than relying only on LLM judgement.

## Solver surfaces and project mapping

| OR-Tools surface | Project use |
|---|---|
| CP-SAT | discrete routing, scheduling, assignment, Boolean/integer gate selection |
| Routing | BraidStorm route ordering, vehicle-route analogues, agent/task traversal |
| MPSolver | linear/mixed-integer planning wrappers |
| MathOpt | unified modeling interface for solver-agnostic optimization |
| GLOP | LP relaxations / fast linear witness checks |
| PDLP | large LP / convex diagonal quadratic approximation and relaxation |
| SAT integer programming | integer-only patch/agent/task selection |

## Universal Shortcut Center packet

```math
\Gamma_{\mathrm{ORToolsWASM}}
=
(
X_{\mathrm{decision}},
\pi_{\mathrm{model}},
W_{\mathrm{solution}},
R_{\mathrm{validate}},
I_{\mathrm{constraints}},
G_{\mathrm{runtime}},
K,
\epsilon
)
```

| Packet term | Meaning |
|---|---|
| `X_decision` | original routing / scheduling / planning decision surface |
| `pi_model` | projection into CP-SAT, routing, LP, MIP, or MathOpt model |
| `W_solution` | solver result / feasible assignment / optimum candidate |
| `R_validate` | model validation and solution verification receipt |
| `I_constraints` | hard constraints that must survive projection |
| `G_runtime` | WebAssembly/browser/Node/Deno/Bun runtime guard |
| `K` | solve time, worker cost, model size, memory budget |
| `epsilon` | relaxation gap, infeasibility, timeout, or model mismatch residual |

## Generic optimization form

A solver problem can be written as:

```math
x^*=
\operatorname*{argmin}_{x\in\mathcal X}
 c^T x
\quad\text{s.t.}\quad
A x\le b,
\quad
x_i\in\mathbb Z\;\text{or}\;\{0,1\}
```

For Warden decisions:

```math
x_i=1
\quad\Longleftrightarrow\quad
\text{route/task/witness }i\text{ is selected}
```

FAMM residual:

```math
R_{\mathrm{opt}}
=
\mathrm{constraintViolation}(x^*)
+
\lambda\,\mathrm{optimalityGap}(x^*)
+
\mu\,\mathrm{runtimeScar}(x^*)
```

Promotion requires:

```math
R_{\mathrm{opt}}\le\Theta_{\mathrm{tol}}
```

## Constrained-agent planning use

This extends the possible constrained-agent architecture:

```text
GLIA recalls context
→ SmallCode proposes TODO / patch candidates
→ OR-Tools WASM solves schedule/assignment under constraints
→ FastPatch / StructuralAdmissibility verifies
→ Anti-FAMM / Anti-BraidStorm probes
→ Warden promotes, scars, or reopens
```

Example decision variables:

```text
x_patch_i        = choose patch i
x_test_j         = run test j
x_memory_k       = retain memory entry k
x_agent_t        = assign task t to agent a
x_witness_l      = activate witness channel l
x_route_ij       = choose crossing route i→j
```

Hard constraints:

```text
budget ≤ B
no unverified patch promotion
must run at least one relevant test
no pair-address alias
memory recall must match project scope
Warden-blocked route cannot be selected
```

Objective:

```text
minimize compute cost + residual risk + scar pressure + context noise
maximize receipt strength + expected reduction value
```

## BraidStorm / Sidon / routing use

`or-tools-wasm` is useful for choosing a crossing schedule:

```text
strand set
→ candidate crossings
→ anti-alias constraints
→ route cost / scar cost
→ solve schedule
→ receipt-bearing BraidStorm traversal
```

CP-SAT can encode:

```text
crossing selected or not
order constraints
no repeated conflicting pair
budget bounds
scarred basin avoidance
required witness coverage
```

Routing API can encode traversal problems:

```text
visit witness basins
avoid scarred routes
minimize travel/search cost
respect time-window/budget constraints
```

## Memory pruning use

Combine with N-space KV / GLIA memory:

```text
memory candidates
→ reward/reduction score
→ staleness penalty
→ project-isolation guard
→ solve retention set under context budget
```

Binary variable:

```math
m_k\in\{0,1\}
```

Objective:

```math
\max_m
\sum_k m_k(
\alpha R_{\mathrm{reduction},k}
+\beta S_{\mathrm{sparse},k}
-\gamma\Omega_{\mathrm{scar},k}
-\delta N_{\mathrm{noise},k}
)
```

subject to:

```math
\sum_k m_k\,\mathrm{tokens}_k\le B_{\mathrm{context}}
```

## Browser / runtime Warden guards

The README notes that browser builds use WebAssembly threads, SIMD, and `SharedArrayBuffer`, requiring cross-origin isolation headers:

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Warden checks:

```text
SharedArrayBuffer available
COOP/COEP headers enabled for browser runtime
worker bridge starts successfully
model validates before solve
timeout / infeasible / unknown status recorded
runtime path recorded: browser / Node / Deno / Bun
solver backend recorded: CP-SAT / Routing / MPSolver / MathOpt / PDLP
```

## FAMM object

```math
\mathfrak C_{\mathrm{ORToolsWASM}}
=
A_{16}(u_{\mathrm{or\_tools\_wasm}})
\otimes
[
\Sigma_{\mathrm{model}}
+
\Sigma_{\mathrm{constraints}}
+
\Sigma_{\mathrm{objective}}
+
\Sigma_{\mathrm{solver}}
+
\Sigma_{\mathrm{runtime}}
+
\Sigma_{\mathrm{solution}}
+
\Sigma_{\mathrm{gap}}
+
\Sigma_{\mathrm{infeasible}}
+
\Sigma_{\mathrm{receipt}}
]
```

## Anti-FAMM / Anti-BraidStorm checks

Anti-FAMM asks:

```text
Did the optimization model omit a constraint that changes the decision?
Did relaxation hide an integer conflict?
Did timeout produce a false optimum claim?
Did model validation pass while semantic intent failed?
```

Anti-BraidStorm asks:

```text
Did the optimized crossing schedule produce false convergence?
Did the solver choose low-cost routes that all share the same hidden scar?
Did the route schedule create pair-address or receipt aliasing?
```

## Stack placement

```text
OR_TOOLS_WASM_CONSTRAINT_SOLVER_GATE
→ Possible Constrained-Agent Approaches
→ GLIA / N-space KV memory scoring
→ SmallCode patch/task scheduling
→ BraidStorm crossing schedule
→ Sidon anti-alias constraints
→ FastPatch / StructuralAdmissibility verification
→ Anti-FAMM / Anti-BraidStorm adversarial probes
→ FAMM/NUVMAP optimization receipt
```

## Warden boundary

Allowed claim:

```text
or-tools-wasm gives the project a practical local/browser TypeScript route for solving constrained planning, routing, assignment, scheduling, memory-retention, and BraidStorm traversal models with explicit solver receipts.
```

Disallowed claim:

```text
A solver optimum proves the original informal goal unless the model projection preserves the real constraints and objective.
```

Hard rule:

```text
The optimization model is a witness projection, not the problem itself.
```

## Project sentence

OR-Tools WASM turns constrained-agent planning into an explicit local/browser optimization gate: GLIA memory, SmallCode patch candidates, BraidStorm crossings, Sidon anti-alias rules, and Warden budgets can be projected into CP-SAT/routing/LP models, solved in TypeScript/WebAssembly, and returned as receipt-bearing decisions rather than model-confidence guesses.

## Citation

```bibtex
@online{wickman_or_tools_wasm,
  title        = {or-tools-wasm: Google OR-Tools for WebAssembly},
  author       = {Wickman, Axel},
  organization = {GitHub},
  url          = {https://github.com/Axelwickm/or-tools-wasm},
  urldate      = {2026-05-18},
  note         = {TypeScript/WebAssembly packaging layer for Google OR-Tools, exposing CP-SAT, routing, MPSolver, MathOpt, and PDLP surfaces.}
}

@software{google_or_tools,
  title        = {Google OR-Tools},
  author       = {{Google}},
  url          = {https://github.com/google/or-tools},
  license      = {Apache-2.0}
}
```
