# Recent AI Math Solves 2026 Import

Status: EXTERNAL_REFERENCE
Date ingested: 2026-05-20

## Claim Boundary

This note tracks recent AI-assisted or AI-autonomous mathematical solves that
should influence Research Stack search policy. These are not internal theorems
until the relevant proof object is imported, checked, or locally formalized.

Status labels:

```text
PAPER_BACKED_FORMALIZED:
  arXiv/paper claim includes a formal proof artifact or Lean/Mathlib claim

OFFICIAL_REVIEW_PENDING:
  official source reports expert-review confidence, but not a final theorem gate

TRACKING_SURFACE:
  benchmark or community index useful for routing, not itself a proof
```

## Additions

### Fel's Conjecture on Syzygies of Numerical Semigroups

Status:

```text
PAPER_BACKED_FORMALIZED
EXTERNAL_REFERENCE
```

Source:

```text
arXiv: https://arxiv.org/abs/2602.03716
```

Claim:

```text
The paper proves Fel's conjecture for normalized alternating syzygy power sums
of numerical semigroup rings. The abstract states that the argument is fully
formalized in Lean/Mathlib and was produced automatically by AxiomProver from a
natural-language statement.
```

Stack import:

```text
Receipt pattern: natural-language conjecture -> generated Lean proof -> paper
writeup.
Relevant layers: L0 algebraic identities, L5 autoformalization bridge, L6
proof-object-first routing.
```

Do not claim local validity until the Lean project or proof artifact is checked
inside the stack.

### Rethlas/Archon Anderson Open Problem

Status:

```text
PAPER_BACKED_FORMALIZED
EXTERNAL_REFERENCE
```

Source:

```text
arXiv: https://arxiv.org/abs/2604.03789
```

Claim:

```text
The paper reports an automated framework with Rethlas for informal reasoning
and Archon for Lean 4 formal verification. It reports resolving an open problem
in commutative algebra with essentially no human mathematical intervention.
Secondary summaries identify the target as D. D. Anderson's 2014 question:
whether weak quasi-completeness implies quasi-completeness for Noetherian local
rings, with the system producing a counterexample.
```

Stack import:

```text
Receipt pattern: theorem retrieval -> candidate proof -> formal agent gap-fill
-> no-sorry Lean project.
Relevant layers: L4 route memory, L5 retrieval/formalization bridge, L6
multi-agent proof search policy.
```

The safe stack claim is about the reported architecture and proof artifact. Do
not promote the Anderson theorem internally until the referenced Lean project is
built locally.

### OpenAI First Proof Submissions

Status:

```text
OFFICIAL_REVIEW_PENDING
EXTERNAL_REFERENCE
```

Source:

```text
OpenAI post: https://openai.com/index/first-proof-submissions/
First Proof paper: https://arxiv.org/abs/2602.05192
```

Claim:

```text
OpenAI reports running an internal model on all ten First Proof problems. Based
on expert feedback, OpenAI says at least five proof attempts, for problems 4, 5,
6, 9, and 10, have a high chance of correctness, while other attempts remain
under review.
```

Stack import:

```text
Receipt pattern: research-level problem set -> public proof attempt bundle ->
expert feedback loop.
Relevant layers: L6 evaluation design, L4 adversarial proof checking, L5
problem-statement ambiguity handling.
```

This is not a solved-theorem import yet. It is a review-pipeline import.

### Formal Conjectures Benchmark

Status:

```text
TRACKING_SURFACE
EXTERNAL_REFERENCE
```

Source:

```text
arXiv: https://arxiv.org/abs/2605.13171
```

Claim:

```text
Formal Conjectures provides a Lean 4 benchmark of research-level formal
mathematical problem statements, including open conjectures and solved problems.
The abstract reports that the benchmark has already been used to make new
mathematical discoveries, including resolutions of open research conjectures.
```

Stack import:

```text
Receipt pattern: formalized open-problem queue -> verified proof/disproof audit
-> benchmark refresh.
Relevant layers: L5 formal statement routing, L6 contamination-resistant
evaluation.
```

Use it to seed target selection and proof-checking policy, not as a theorem
source by itself.

### Erdős AI Contributions Wiki

Status:

```text
TRACKING_SURFACE
PROVISIONAL
```

Source:

```text
Tao Erdős wiki: https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems
```

Claim:

```text
The wiki tracks many 2026 AI contributions to Erdős problems, including full
solutions, partial results, formalizations, incorrect attempts, and literature
rediscoveries. The page itself warns that it is provisional and not a definitive
verdict.
```

Stack import:

```text
Receipt pattern: triage index -> source lookup -> status-tiered import.
Relevant layers: L4 scar handling for incorrect proofs, L6 provenance discipline.
```

Use the wiki as a watchlist only. Each row needs its own source or formal
artifact before promotion.

## Search Policy Update

The current frontier is not one single pattern. It is four patterns:

```text
1. AI finds a proof and humans write or review it.
2. AI generates Lean/Mathlib proof artifacts directly.
3. AI searches literature and discovers the problem was already effectively solved.
4. AI generates plausible attempts that require expert review and may fail.
```

The stack should keep separate receipts for all four. Collapsing them into a
single "AI solved it" label destroys the audit value.
