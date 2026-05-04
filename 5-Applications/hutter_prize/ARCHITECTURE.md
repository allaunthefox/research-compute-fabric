# Hutter Prize Architecture Notes

This note captures the current high-level split between search, execution, and audit.

It is not a full codec specification yet. It is a boundary document for keeping the
system auditable without disclosing all platform internals.

## Current Stack

The working architecture is:

- annealing or search layer
- candidate equation / parameter layer
- deterministic trinary execution layer
- audit / proof layer

The search layer is allowed to be private and heuristic.
The execution layer must be deterministic and inspectable.
The audit layer must be boring enough for outsiders to verify without trusting the
private search process.

This repo also assumes a disclosure constraint:

- publish enough to make the system auditable
- do not publish so much, so early, that the platform collapses before it exists

That boundary is captured more directly in `AUDITABILITY_IP_BOUNDARY.md`.
The staged release logic that sits on top of it is captured in `RELEASE_GATING.md`.

## Attribution Boundary

LLM assistance may participate in drafting, comparison, search support, and structural
exploration.

The operator remains responsible for:

- choosing the path
- setting release boundaries
- accepting or rejecting candidate structures
- deciding what becomes canonical

In other words, the model may assist with exploration, but the human threads the
needle.

## Subregister Rule

Each operation is assigned a subregister.

That means an operation does not act against an undifferentiated global state by
default. Instead, it is given:

- a defined local state boundary
- explicit readable inputs
- explicit writable outputs
- a finite instruction budget
- a finite transition surface

The subregister is therefore both:

- an execution container
- an audit boundary

## Why Subregisters Matter

Assigning each operation a subregister helps with four things:

- locality
  Operations can be reasoned about without reading the entire machine state.
- reversibility
  It becomes easier to define what an operation changed and what must be restored.
- proofability
  A verifier can check a smaller transition claim rather than a blurred global one.
- IP separation
  The public contract can expose operation boundaries without exposing every internal
  heuristic that produced them.

## Proposed Execution Shape

At a high level:

1. The source file is ingested.
2. A deterministic derivation step may emit a baseline program directly from declared
   rules.
3. A private search process may later propose a stronger equation, instruction stream,
   or parameter set, but it should not be the only executable path.
4. The deterministic runtime maps each operation onto a subregister.
5. Each subregister executes only its allowed trinary instruction transitions.
6. The machine emits a compressed artifact and a reconstruction path.
7. The audit layer verifies that the declared transitions were valid and that the final
   reconstruction matches the original source.

The current baseline derivation contract is captured in `DERIVATION_SPEC.md`.
The intended multi-substrate execution posture is captured in
`EXECUTION_SUBSTRATE_STRATEGY.md`.

## Trinary Runtime Sketch

The runtime is currently imagined as a constrained trinary machine with values drawn
from:

- `-1`
- `0`
- `+1`

Operations may eventually include things like:

- add
- subtract
- weight / `W`
- shift
- merge
- project

The exact instruction set is still open.
What matters here is that every operation has an assigned subregister and an explicit
transition rule.

The current minimum executable contract is captured in `TERNARY_VM_SPEC.md`.
That document deliberately defines the smallest auditable VM we can use as a baseline
before the fuller codec runtime exists.
That VM is the semantic baseline, not the only allowed executor shape.
The same contract should be able to survive translation into multiple constrained
substrates so the system does not read as overfit to one privileged machine.

## Economic Principle

Computation is treated as thermodynamic action trade rather than abstract token
issuance.

In this model:

- each operation consumes, preserves, transfers, or releases a bounded amount of
  thermodynamic action
- each operation's action accounting belongs to its assigned subregister
- economic value is derived from verified entropy reduction and constrained
  transformation, not from unsupported claims of effort

The intended accounting shape is:

- operation
- subregister trace
- thermodynamic-action-denominated accounting unit
- verification
- settlement

This means the system should prefer:

- measurable operation cost
- bounded local action budgets
- explicit transition accounting
- settlement only after verification

If a later token or contract layer exists, it should wrap this verified
thermodynamic-action accounting substrate rather than replace it.

## Audit Boundary

The intended public boundary is:

- input hash
- compressed artifact hash
- reconstructed output hash
- allowed instruction set
- allowed subregister transition rules
- proof or verification path for deterministic execution

Where possible, the execution claim should be stated as a single auditable execution
lane rather than a guaranteed statement about one visible physical core.
That distinction matters when execution happens under emulation or virtualization.

The intended private boundary is:

- how the search layer found the candidate program
- how the equation family is chosen
- optimization heuristics
- platform orchestration logic

This split is not an attempt to hide cheating.
It is an attempt to expose the contract and the audit surface while keeping the
platform's still-fragile internal edge from being donated prematurely.

## Disclosure Ladder

The intended order of release is:

1. integrity substrate
2. deterministic VM contract
3. replayable traces and validation tooling
4. public derivation rules where they do not collapse the platform edge
5. selected reference programs and examples
6. deeper search and optimization details later, if the platform can survive it

This keeps the project legible without forcing an all-or-nothing disclosure decision.

## Self-Derivable Baseline

At least one executable path should be self-derivable from the input using declared
rules only.

That baseline matters because it lets us point to:

- immutable derivation rules
- reproducible program generation
- a public math-shaped reference path
- a portable baseline that can be implemented in many environments

Search may remain private.
The existence of a public deterministic baseline keeps the audit story grounded.

## Minimalist Reproducibility

The baseline software should be simple enough to implement almost anywhere.

That is a design choice, not an afterthought.
Minimalism helps because it reduces:

- dependency trust
- environment-specific magic
- hidden implementation assumptions
- excuses for why a verifier cannot reproduce the declared path

If the rules are clear enough, the software should be reproducible across different
machines, languages, and runtime environments while preserving the same contract.

That includes preserving the contract across different constrained execution
substrates, not just different host languages.

## Compression-First Posture

The compression layer should be treated as independently useful.

That means:

- it should be benchmarkable on its own
- it should justify itself without broader platform claims
- it can serve as a calmer review surface while larger capabilities remain gated

The current rationale for that posture is captured in
`COMPRESSION_FIRST_APPLICATIONS.md`.

## Working Principle

The search process may remain interesting.
The thing that gets audited must remain boring.

That means the final executable path should be:

- deterministic
- bounded
- hashable
- replayable
- explainable at the subregister level

The platform may stay partially private.
The executable contract must not.
