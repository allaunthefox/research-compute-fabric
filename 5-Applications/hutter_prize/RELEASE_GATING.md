# Release Gating

This document defines how the project should move from private work toward broader
disclosure without creating an unacceptable blast radius.

The aim is not perfect safety.
The aim is to reduce both:

- harm caused by negligent hesitation
- harm caused by reckless release

## Principle

Release should move only as fast as the safety case, review capacity, and containment
surface can move with it.

If a capability can plausibly create misuse, destabilization, parasitic capture,
catastrophic displacement, or irreversible social blast radius, it must not jump
directly from private work to public unrestricted release.

The working posture is:

- plan for the worst credible interpretation
- hope for the best real-world outcome
- be pleasantly surprised when the worst case does not materialize

This is meant to encourage resilient planning without turning the threat model into a
claim of certainty.

It also assumes that worldview inertia is normal.
People will often reach for familiar explanations first, especially when a new result
pressures old models of what is possible.
That should be treated as an expected human response, not as a unique defect in the
audience.

For that reason, release pacing should be designed for human absorbability as well as
for technical correctness.

## Release Levels

## `R0_PRIVATE`

Default mode.

Material remains private when any of the following are true:

- the audit surface is not yet strong enough to distinguish truth from hype
- the misuse path is clearer than the safety case
- the disclosure would donate the platform edge before the platform exists
- the social blast radius is unknown or obviously too large

Allowed outputs:

- internal notes
- private experiments
- simulation artifacts
- locked architecture drafts

## `R1_EXPERT_REVIEW`

Bounded disclosure to a small number of qualified reviewers.

Use this level when:

- independent scrutiny is needed
- public release would be premature
- the material is ethically important enough that total silence would be negligent

Requirements:

- reviewers are chosen for competence and seriousness
- disclosure is minimal for the review purpose
- safety concerns, misuse concerns, and uncertainties are stated plainly
- any high-risk detail remains constrained to the smallest useful surface
- excessive excitement about disruptive change is treated as a review signal, not as a
  trust signal

Allowed outputs:

- redacted specs
- audit contracts
- ethical boundary notes
- narrow technical packets needed for real critique

Preferred reviewers are those who can remain:

- curious without becoming euphoric
- cautious without becoming frozen
- serious about consequences without becoming theatrically apocalyptic

## `R2_CONTROLLED_EXECUTION`

Demonstration or validation under bounded conditions.

Use this level when:

- the executable path is deterministic
- the audit surface is credible
- outsiders need to see behavior rather than just read claims
- unrestricted release would still be too dangerous

Requirements:

- execution environment is constrained
- inputs and outputs are logged
- undeclared side inputs are blocked
- rollback, freeze, or kill-switch paths exist
- observers can verify the declared contract without receiving the full internal edge

Allowed outputs:

- controlled demos
- signed reports
- bounded test vectors
- replayable traces

## Scoped Challenge Authorization

One acceptable expert-review pattern is a one-time scoped challenge.

In that pattern:

- the reviewer chooses one target object
- the authorization is bound to that exact scope
- the authorization is time-bounded
- reuse outside that scope fails verification

If a challenge namespace is used, it should be explicit and narrow.
For example, a fixed `archive.org` domain with a reviewer-chosen object path is a
legible way to give the reviewer real choice without turning the token into a general
license.

The point of this challenge model is to demonstrate universality under reviewer-chosen
conditions, not to showcase a hand-fit demo prepared around one secretly favorable
file.

## `R3_PUBLIC_SAFE_SURFACE`

Broad public release of the parts that are safe enough to stand on their own.

Use this level when:

- the released surface is useful without revealing the most dangerous internals
- misuse pathways are materially reduced by the bounded design
- the public can verify reproducibility and honesty

Allowed outputs:

- deterministic VM spec
- benchmark harnesses
- build integrity manifests
- validation tools
- limited reference implementations

## `R4_FULL_DISCLOSURE`

Reserved for cases where:

- the platform can survive disclosure
- the safety case is substantially stronger
- the misuse amplification from release is no longer dominant
- governance and review are no longer bottlenecks

This should be treated as a late-stage option, not the default moral baseline.

For this project, the preferred durable public endpoint is not just broad availability,
but archival publication as described in `ARCHIVAL_PUBLICATION_STRATEGY.md`.

## Hard Stops

Release must pause or fall back a level if any of the following appear:

- memetic or parasitic uptake that outpaces understanding
- evidence of destabilizing social interpretation
- significant mismatch between public narrative and actual capability
- clear path from released detail to catastrophic misuse
- inability to audit whether the declared path was followed

## Review Questions

Before moving a capability upward, ask:

- does this reduce preventable harm more than it increases misuse risk
- does this help serious reviewers evaluate the work
- can the released surface be independently checked
- does the release create a social or economic shock larger than the review value
- if this spread fast, would the world have enough interpretive and governance capacity
- are we reacting to a credible risk model, or to unbounded fear
- if the worst case does not happen, does this release plan still make sense

If those answers are weak, the capability should stay gated.

## Compression First

Compression-oriented work is a preferred early release surface because it is:

- technical
- measurable
- auditable
- less immediately socially explosive than direct civilizational capability release

That does not make it harmless.
It means it is a calmer place to build trust, proof discipline, and review culture
before disclosing more disruptive layers.

It is also a better surface for readers and reviewers who need a bounded technical
entry point before they can process larger worldview implications.

## Target-Bound Reuse Principle

If a future reuse or servicing platform is ever discussed or demonstrated, it must be
target-bound by default.

That means:

- every operation is locked to an explicit authorized identity set
- no autonomous spread outside declared targets is permitted
- identity mismatch must fail closed
- every touch must leave an auditable authorization trail

The project should prefer bounded servicing tools over any design that could be
interpreted as self-propagating, opportunistic, or ambiguously authorized behavior.

## Scientific Gate Requirement

Any proposal involving heritage spacecraft, orbital servicing, or probe augmentation
must be gated behind real scientific and operational oversight.

That means:

- explicit review by qualified scientists and mission-relevant experts
- explicit authorization from the relevant mission or institutional authority
- bounded execution under a controlled protocol
- no lone-operator deployment logic
- no ambiguous claim of authority based on technical capability alone

The intended model is disciplined scientific augmentation, not improvised private
intervention.
