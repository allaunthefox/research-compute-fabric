# Archival Publication Strategy

This note defines the intended end-state publication posture for the project.

The working system may stay gated while it is still fragile.
The durable public artifact should not.

## End-State Principle

When a version is ready to become a historical record, it should be published in a way
that is:

- freely accessible
- hashable
- archivally legible
- easy to mirror

## Primary Historical Record

The intended end-state public record is an `archive.org` publication.

That makes sense for two reasons:

- it provides a public, historically legible artifact surface
- it aligns the compression work with a real preservation mission rather than with a
  private demo-only posture

In this model, `archive.org` is the record, not the workshop.

## Optional Infrastructure Layer

If distributed infrastructure is needed later, content-addressed systems such as `IPFS`
may be used as a supporting layer.

The intended split is:

- `archive.org` as the primary public historical artifact
- `IPFS` as optional redundancy or distribution support

Redundancy should still be verified by hash, not assumed by hope.

## Why This Matters

Archive-scale storage is expensive.
If preservation institutions are running into real storage ceilings, better compression
is not just a benchmark exercise. It is a preservation multiplier.

That gives the work both:

- a financial rationale
- an ethical rationale

Better compression can help preserve more human record for the same physical and
financial budget.

## Human Absorbability

The public record should also be paced for human absorbability.

If a result pressures existing worldviews too abruptly, many readers will default to
dismissal stories before they can evaluate the artifact itself.
That is not a special failure of character.
It is a normal consequence of interpretive inertia.

This is one reason the project prefers a compression-first public story:

- it is bounded
- it is measurable
- it is easier to critique without demanding immediate agreement with every larger
  implication

The aim is to leave behind a record that people can gradually understand, not merely a
record that is technically present.

## Release Sequence

The intended order is:

1. private iteration
2. gated review
3. controlled challenge or expert validation where needed
4. durable public publication when the artifact is ready

The archival publication step should happen after the artifact is stable enough to
stand as a historical record.

## Publication Expectations

When the public artifact is published, it should ideally include:

- the software or bounded public subset
- hashes and manifests
- provenance notes
- reproducibility notes
- enough surrounding context that the artifact is understandable years later

The goal is not just to upload files.
The goal is to leave behind an intelligible record.
