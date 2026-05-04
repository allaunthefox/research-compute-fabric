# Auditability and IP Boundary

This document defines how much of the platform should be disclosed before the platform
itself is ready to stand on its own.

The goal is not secrecy for its own sake.
The goal is to publish enough that honest outsiders can verify the shape, discipline,
and fairness of the system without requiring the operator to donate the full platform
before it exists as a durable project.

This boundary should be designed as if hostile interpretation is possible, without
assuming that hostility is guaranteed.

## Principle

Give as much as possible without collapsing the platform that still has to be built.

That means:

- disclose contracts before crown jewels
- disclose invariants before heuristics
- disclose replayable execution before private search
- disclose verification surfaces before optimization strategy

The intended result is a mutual non-trust posture:

- the operator does not have to donate private infrastructure for the claim to be
  checked
- the reviewer does not have to trust the operator personally for the public audit
  surface to be meaningful

## Human-in-the-Loop Attribution

LLM assistance may be used in the development and documentation process.

That does not make the model the governing authority.
The intended claim here is:

- machine assistance can help explore, draft, compare, and compress
- machine assistance can also help bridge operator-side accessibility constraints in
  numerically dense work
- the human operator remains responsible for judgment, synthesis, boundary-setting,
  and release decisions
- the critical thread-the-needle decisions are treated as human-in-the-loop decisions,
  not as autonomous model outputs

This distinction matters for both honesty and reviewability.

The operator also reports dyscalculia, so part of the value of LLM assistance here is
practical support in navigating number-heavy reasoning without transferring final
judgment to the model.
The intended record is not "LLM was used because the operator was lazy."
It is that LLM assistance functioned in part as an accessibility aid in the presence of
neurodivergent and numeracy-related constraints, while the human remained responsible
for the actual synthesis and decision-making.
This does not exempt the work from critique.
If the work is weak, it should be called weak.
The point is simply that the route through the work had to be adapted because standard
paths were not reliably available to the operator's brain architecture.

## Public By Default

The following should be publishable early:

- input and output hash contracts
- deterministic execution rules
- subregister boundaries
- allowed instruction set
- trace format
- execution-lane contract
- round-trip verification method
- reproducibility envelope for the build substrate
- integrity manifests and component hashes

These let an outsider inspect whether the system is disciplined without forcing full
disclosure of the platform's internal edge.

They also matter because outside reviewers should not be expected to receive direct
access to the operator's private network, private data, or private search substrate.
The public audit surface has to stand without that privileged access.

Public-facing prose and metadata should also be smoothed toward a low-distinctiveness
house voice where that can be done without harming auditability.
That policy is captured in `PUBLIC_SMOOTHING.md`.

## Substrate Independence

One useful early disclosure surface is substrate independence.

That means the public should be able to see that the declared derivation and validation
contract is not tied to one privileged executor.
The project should therefore prefer a public story like:

- same contract
- multiple constrained execution substrates
- one auditable execution lane per substrate
- at least one historically constrained substrate that makes hidden dependence on a
  modern CPU stack a weaker explanation
- at least one legible substrate path that makes malware-like or anti-analysis
  execution narratives a weaker explanation

This is a stronger and more honest claim than pretending an emulator can always prove
one physical core.

The multipath substrate strategy is captured in `EXECUTION_SUBSTRATE_STRATEGY.md`.

## Private Until the Platform Is Stable

The following may remain private until the platform has enough durability to survive
disclosure:

- search heuristics
- equation-family selection logic
- optimization schedules
- platform orchestration logic
- candidate-ranking strategy
- any tuning that creates the practical performance edge

These are the parts most likely to collapse the platform's advantage if donated too
early.

## Disclosure Ladder

The intended order of disclosure is:

1. build integrity and reproducibility substrate
2. deterministic VM and trace model
3. public audit statement and validation tooling
4. derivation rules that can be stated without donating the full search layer
5. selected reference programs and test vectors
6. deeper optimization details only when the platform can survive that disclosure

This is a ladder, not an all-at-once dump.

The operational release tiers for applying this ladder are captured in
`RELEASE_GATING.md`.

## What Must Never Be Hidden

Even with a private platform, some things must stay auditable:

- whether the declared executable path was actually followed
- whether undeclared side inputs were used
- whether the claimed output reconstructs correctly
- whether the build substrate matches the published integrity envelope
- whether a one-time challenge token was used only within its declared scope

If those are hidden, the project stops being credibly auditable.

## Working Test

Before publishing a component, ask:

- does this help someone verify honesty or reproducibility
- or does this mostly give away the still-fragile platform edge

If it is mostly the second, defer it.
If it materially improves auditability, publish it.

The aim is disciplined resilience, not panic.
