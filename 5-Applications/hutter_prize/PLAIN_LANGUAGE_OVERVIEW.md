# Plain-Language Overview

If you are reading this quickly, start here.

This project is a compression lab.
Right now, it is not asking you to accept a new worldview.
It is asking you to look at a bounded technical claim:

- can a file be compressed and restored correctly
- can the run be measured
- can the run be audited
- can the run be reproduced

That is the current scope.

## What This Is

This repo is a small test harness for compression experiments.

It is designed to be:

- reproducible
- auditable
- measurable
- hard to fake casually

## What This Is Not

This is not:

- a demand for immediate belief
- a release of every private platform detail
- a claim that one benchmark result settles everything
- a request to ignore risk, uncertainty, or critique

It also does not require mutual personal trust.
The point of the public contract is that neither side should need to trust the other
more than necessary.

## Why The Docs Are So Careful

The docs are careful because people will reasonably be cautious.

That caution is expected.
The project therefore tries to remove easy failure modes:

- unclear derivation
- hidden side inputs
- overfit execution environments
- vague release boundaries
- confusing public language

## What You Can Check

A reviewer should be able to check simple things first:

- what file went in
- what file came out
- whether decompression restored the original
- what command ran
- how long it took
- what integrity and validation artifacts were emitted

Those checks matter more than any big narrative.

Reviewers should also assume they are not being asked to trust private internal access.
The intended public proof should work without access to:

- the operator's private network
- the operator's private data
- the operator's private search systems

That boundary is deliberate.

## Why Compression Comes First

Compression is the calmest place to start.

It is:

- technical
- bounded
- measurable
- easier to review than a larger platform claim

If this layer is weak, it should be called weak.
If it is strong, it earns the right to further review.

## Practical Reading Order

If you want the shortest path through the repo, read in this order:

1. this file
2. `README.md`
3. `DERIVATION_SPEC.md`
4. `TERNARY_VM_SPEC.md`
5. `AUDITABILITY_IP_BOUNDARY.md`

That path is enough to understand the current shape without drowning in architecture
detail.
