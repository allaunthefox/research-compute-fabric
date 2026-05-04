# Execution Trust Model

This note defines how to think about three different infrastructure classes in the
project:

- a physical CPU run
- a quantum annealing or search network
- a VPS or hosted witness environment

They should not all be treated as the same thing.
Each plays a different role in the trust story.

## Plain Summary

The simplest model is:

- the annealer searches
- the physical CPU executes
- the VPS witnesses

In other words:

- search may be interesting and private
- execution must be boring and replayable
- witnessing must be legible and easy for outsiders to inspect

## Mutual Non-Trust Principle

The trust model should not require mutual personal trust.

That means:

- the operator should not have to trust outside parties with private network access,
  private data, or private search infrastructure
- outside parties should not have to trust the operator's intentions in order to check
  the public claim
- the public contract should stand on bounded execution, published artifacts, and
  reproducible checks

This is a practical constraint, not a sign of hostility.
It is the design response to a world where both sides may reasonably limit trust.

Outside reviewers should assume they will not have:

- direct access to the operator's private network
- direct access to the operator's private data
- direct access to the private search substrate

The trust model therefore has to stand without any privileged internal access.

## Why The Split Matters

If all three roles are blurred together, reviewers will reasonably worry about:

- hidden side inputs
- overfit search masquerading as execution
- cloud-only behavior that cannot be checked locally
- unverifiable claims about where the real work happened

The fix is to assign each layer a narrow job.

## Layer 1: Search Plane

Typical substrate:

- quantum annealer
- heuristic search cluster
- private optimization network

Job:

- find candidate programs
- find candidate equations
- search parameter space
- rank or discard candidate solutions

Trust posture:

- may remain private
- may be heuristic
- may be high-dimensional and difficult to explain

What it must not do:

- it must not be the only path that makes the codec work
- it must not silently become the audit story
- it must not inject undeclared side inputs into the public execution contract

The search plane is where interesting things are allowed to happen.
It is not where public trust should be anchored.
Reviewers may know it exists without ever being given direct access to it.

## Layer 2: Execution Plane

Typical substrate:

- physical CPU
- constrained emulated CPU
- classical ternary core
- other deterministic executor

Job:

- run the declared program
- produce the compressed artifact
- produce the reconstruction path
- emit the trace and execution receipt

Trust posture:

- deterministic
- replayable
- bounded
- inspectable

What it must do:

- accept a declared input
- run a declared executable path
- honor the single-lane execution contract
- produce hashes, receipts, and output artifacts

This is the layer that should carry the public burden of proof.

## Layer 3: Witness Plane

Typical substrate:

- VPS
- hosted runner
- externally accessible build box
- neutral replay environment

Job:

- witness a run
- preserve artifacts
- emit timestamps and logs
- provide an externally legible replication point

Trust posture:

- not fully trusted
- but useful as a public observation surface

What it should not be asked to prove:

- that the search process was noble
- that the hardware beneath it is metaphysically perfect
- that no one anywhere could have cheated

What it is good for:

- independent reruns
- public artifact hosting
- third-party observation
- challenge execution under constrained conditions

The VPS is best treated as a witness and relay surface, not as the ultimate root of
truth.
It is especially useful because it can expose bounded public artifacts without exposing
the operator's internal network or private data sources.

## Recommended Role Assignment

The preferred assignment is:

### Physical CPU Run

Role:

- primary execution plane

Reason:

- clearest path to deterministic replay
- easiest place to pin an execution-lane contract
- strongest bridge between software trace and real hardware behavior

### Quantum Annealing Network

Role:

- private search plane

Reason:

- best used for candidate discovery
- valuable without needing to become the public trust anchor
- can stay partially private without collapsing the audit story

### VPS

Role:

- witness plane

Reason:

- easy for others to access
- useful for challenge runs, logs, and archived receipts
- public enough to help with review without needing to carry the deepest trust burden

## Public Claim

The public claim should be as simple as possible:

- search may happen on more complex private infrastructure
- final execution happens on a deterministic constrained substrate
- public witnessing may happen on a VPS or other hosted surface
- the audit contract attaches to the executed path, not to the private search process
- the public proof should remain checkable even when the operator's private network and
  private data remain inaccessible

That keeps the story understandable.

## Review Order

If someone asks where to focus trust first, the order should be:

1. execution plane
2. witness plane
3. search plane

That order exists because:

- the executed path is what produced the artifact
- the witness plane helps others observe and replay it
- the search plane is useful, but it is not where the public proof should live

## Scope Limit

This is a trust model, not a complete deployment topology.

The exact hardware and network layout can change.
The role split should remain stable:

- search discovers
- execution proves
- witness observes
