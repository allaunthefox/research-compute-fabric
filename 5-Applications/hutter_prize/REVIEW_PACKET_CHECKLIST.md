# Review Packet Checklist

This note defines the smallest useful packet for a first serious outside review.

The goal is not to overwhelm the reviewer.
The goal is to give them enough to evaluate the current claim without forcing them to
ingest the whole project at once.

## Default Packet

The default first packet should include:

1. `PLAIN_LANGUAGE_OVERVIEW.md`
2. `README.md`
3. `DERIVATION_SPEC.md`
4. `TERNARY_VM_SPEC.md`
5. `AUDITABILITY_IP_BOUNDARY.md`

That is the minimum set for understanding:

- what the repo currently claims
- what can be reproduced
- what can be validated
- what is still private

## If Execution Questions Come Up

If the reviewer asks about where trust attaches during runs, add:

1. `EXECUTION_SUBSTRATE_STRATEGY.md`
2. `EXECUTION_TRUST_MODEL.md`

Those documents explain:

- why multiple substrates matter
- why one physical core is not the core claim
- how search, execution, and witnessing are separated

## If Release Questions Come Up

If the reviewer asks how disclosure is being paced, add:

1. `RELEASE_GATING.md`
2. `ARCHIVAL_PUBLICATION_STRATEGY.md`

Those documents explain:

- why the project is being staged
- why compression comes first
- why the intended public endpoint is archival publication

## If Privacy Or Stylometry Questions Come Up

If the reviewer asks about wording, metadata, or authorial fingerprinting, add:

1. `PUBLIC_SMOOTHING.md`
2. a prepared public artifact bundle produced by `scripts/prepare_public_artifact.py`

That gives them:

- the smoothing policy
- the smoothing receipt
- the manifest with hashes

## Default Questions For Reviewers

The first review packet should ask bounded questions such as:

- Is the current technical claim legible?
- Is the current audit surface strong enough for the claim being made?
- Are there obvious cheating paths not yet closed?
- Are there obvious wording or trust problems that would confuse a careful reader?
- What is the next smallest artifact that would materially improve review?

Avoid open-ended questions like "what do you think of everything."

## Packet Rules

When preparing a review packet:

- prefer the smallest packet that still supports the review purpose
- prefer calm framing over exhaustive framing
- include hashes or manifests when artifacts are attached
- smooth public-facing packet text when that does not damage the audit surface
- do not include private network, private data, or private search access by default

The default procedural helper for this is `scripts/build_review_packet.py`.
That script copies the exact default packet into one directory and writes a manifest
with hashes so the handoff is procedural rather than improvised.

## Working Principle

The first packet should make the reviewer think:

- this is bounded
- this is checkable
- this is not asking for blind trust

That is enough for an initial serious pass.
