# 2026 Erdős-Family Solves and Judo Flips

## Scope

This note records 2026 papers surfaced by literature search that claim to resolve, complete, or substantially settle Erdős-family problems or adjacent conjectural structures.

This is not an exhaustive proof-status certification. Some entries are preprints or AI-assisted reports and should remain `U_scope` until independently reviewed, formally verified, or corroborated by specialist consensus.

## High-Value 2026 Imports

### 1. Bloom Erdős Problems database sweep

Paper: `Semi-Autonomous Mathematics Discovery with Gemini: A Case Study on the Erdős Problems`

Claimed contribution:

```text
700 Bloom Erdős Problems labeled Open evaluated.
13 addressed:
  5 seemingly novel autonomous solutions
  8 previous solutions identified in literature
```

Judo flip:

```text
Open status can mean obscurity, not intrinsic hardness.
```

Stack implication:

```text
Add LiteratureObscurityPenalty and PriorSolutionSearchReceipt before treating an unsolved-looking obstruction as mathematically deep.
```

### 2. Erdős Problem #728, Lean proof writeup

Paper: `Resolution of Erdős Problem #728: a writeup of Aristotle's Lean proof`

Claimed contribution:

```text
Formal Lean proof of a logarithmic-gap factorial divisibility phenomenon.
```

Key pattern:

```text
Kummer theorem -> p-adic carry counts
construct carry-rich but spike-free integers
prove prime-wise divisibility inequalities
```

Judo flip:

```text
Carry debt can be engineered positively, not merely avoided.
```

Stack implication:

```text
Use p-adic carry engineering for Sidon window construction, AMREF collision hardening, and inverse-ascent receipt generation.
```

### 3. Erdős--Graham rapidly converging series

Paper: `Irrationality of rapidly converging series: a problem of Erdős and Graham`

Claimed contribution:

```text
Double-exponential growth condition sufficient for irrationality of sum 1/(a_n a_{n+1}), with generalizations and optimality results.
```

Judo flip:

```text
Fast growth can force arithmetic non-collapse.
```

Stack implication:

```text
Use growth-rate gates for anti-compression: if a candidate grows too fast to collapse into rational/periodic form, route it as possible structured residual rather than noise.
```

### 4. Erdős Matching Conjecture theorem claim

Paper: `Erdős Matching (Conjecture) Theorem`

Claimed contribution:

```text
Claims proof of the Erdős Matching Conjecture for k-uniform families with no s pairwise disjoint subsets.
```

Status caution:

```text
Treat as CLAIMED_SOLVE until community review confirms.
```

Judo flip:

```text
Extremal families often collapse to canonical obstruction templates.
```

Stack implication:

```text
When Sidon/AMREF candidates fail, classify whether the obstruction resembles a bounded-core family or a fixed-intersection family instead of generic noise.
```

### 5. Turán graph inducibility completion

Paper: `The inducibility of Turán graphs`

Claimed contribution:

```text
Completes picture for inducibility of Turán graphs and confirms a 1995 Bollobás--Egawa--Harris--Jin conjecture; resolves a Yuster problem.
```

Judo flip:

```text
Extremizers are often canonical and stable, not arbitrary.
```

Stack implication:

```text
Add CanonicalExtremizerCheck: if a candidate looks optimal, compare it to known extremal templates before claiming new structure.
```

### 6. Dowling / Mason matroid log-concavity line

Papers:

```text
Dowling's polynomial conjecture for independent sets of matroids
Tree metrics and log-concavity for matroids
```

Claimed contribution:

```text
Lorentzian polynomial machinery resolves Dowling's polynomial conjecture and related strengthening of Mason-style log-concavity questions.
```

Judo flip:

```text
Hidden convexity/log-concavity can certify stability of combinatorial mass distributions.
```

Stack implication:

```text
Add LogConcavityReceipt for MassNumber distributions and candidate-growth sequences.
```

### 7. Finite geometry / Furstenberg-Sárközy / Nikodym constructions

Paper: `Large point-line matchings and small Nikodym sets`

Claimed contribution:

```text
Uses a connection with the Furstenberg-Sárközy problem to build large induced matchings, improve finite-field Nikodym constructions, solve a longstanding finite-geometry blocking-set problem, and improve minimal-distance constructions.
```

Judo flip:

```text
Incidence geometry can convert additive constraints into large sparse matchings.
```

Stack implication:

```text
Use incidence-matching lifts as a virtual-Sidon escape hatch when direct pair-sum uniqueness is too expensive.
```

## Updated Cost / Credit Terms

### New penalties

```text
LiteratureObscurityPenalty(A)
PriorSolutionMissingPenalty(A)
CanonicalExtremizerMismatch(A)
UnreviewedPreprintRisk(A)
GrowthCollapseRisk(A)
```

### New credits

```text
FormalLeanReceipt(A)
CarryEngineeringCredit(A)
LogConcavityStabilityCredit(A)
IncidenceLiftCredit(A)
CanonicalTemplateMatchCredit(A)
```

## Updated Inverse-Ascent Equation

```text
AscentCost(A) =
    existing_costs(A)
  + lambda_L * LiteratureObscurityPenalty(A)
  + lambda_P * PriorSolutionMissingPenalty(A)
  + lambda_U * UnreviewedPreprintRisk(A)
  + lambda_E * CanonicalExtremizerMismatch(A)
  + lambda_G * GrowthCollapseRisk(A)
```

```text
EnergyAvailable(A) =
    existing_energy(A)
  + eta_F * FormalLeanReceipt(A)
  + eta_C * CarryEngineeringCredit(A)
  + eta_L * LogConcavityStabilityCredit(A)
  + eta_I * IncidenceLiftCredit(A)
  + eta_T * CanonicalTemplateMatchCredit(A)
```

## Direct Judo Flips for Sidon/AMREF Stack

```text
Erdős #728 / p-adic carries:
  replace carry avoidance with carry engineering.

Erdős-Graham irrationality:
  use growth-rate forcing to prevent rational/periodic collapse.

Erdős Matching templates:
  classify failures as canonical extremal obstructions.

Turán inducibility:
  compare candidates to canonical extremizers before novelty claims.

Matroid log-concavity:
  add stability tests for mass-number and growth sequences.

Finite geometry matchings/Nikodym:
  use incidence lifts as virtual-Sidon construction paths.
```

## Audit Classification

```text
Receipt: Erdos2026_SolvesAndJudoFlips
Status: 2026_LITERATURE_IMPORT_MAP
Gate: U_scope
Reason: useful current-year import map, but several entries are preprints/claims and require independent verification before being used as V_scope receipts.
```
