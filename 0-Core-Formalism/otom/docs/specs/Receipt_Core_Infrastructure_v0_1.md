# Receipt Core Infrastructure v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec documents the minimal receipt infrastructure scaffold added to OTOM. It is a safety and evidence-routing layer: executable success, benchmark success, and adversarial-trial success may produce useful evidence, but they do not by themselves authorize promotion to `REVIEWED`.

## Source boundary

This was reconstructed from a recovered work log that described a missing `ReceiptCore.lean`, a proof-receipt gate, and integration work around `GeometricCompressionWorkspace`. The current repository state did not expose the referenced workspace file at the expected path, so this commit intentionally adds a standalone Lean scaffold first.

This spec therefore treats the artifact as:

```text
receipt infrastructure scaffold
not full workspace integration
not proof that all recovered-log work was committed
```

## Core thesis

A workspace may execute, self-test, benchmark, and produce candidate status, but it may not promote itself to reviewed status without an explicit proof receipt.

In OTOM terms:

```text
operator / artifact
→ executable receipt
→ benchmark receipt
→ adversarial-trial receipt
→ candidate status
→ proof receipt gate
→ reviewed status
```

The important invariant is:

```text
CANDIDATE + non-proof evidence ≠ REVIEWED
CANDIDATE + proof receipt may promote to REVIEWED
```

## Lean artifact

Paired module:

```text
tools/lean/Semantics/Semantics/ReceiptCore.lean
```

The module defines:

```text
ClaimState
WardenStatus
ReceiptKind
Receipt
AdversarialTrial
ReceiptLedger
```

It also defines these receipt constructors:

```text
proofReceipt
leanBuildReceipt
executableEvalReceipt
benchmarkReceipt
adversarialTrialReceipt
```

And these gates/operators:

```text
isPassingProofReceiptFor
hasProofReceipt
ledgerLookup
ledgerAppend
ledgerHasProofReceipt
promoteTrial
promoteTrialLedger
```

## Kernel-checked intent

The key theorem is:

```text
promoteTrial_preserves_receipt_gate
```

Meaning:

```text
If a CANDIDATE trial promotes to REVIEWED, then a passing proof receipt for that target must exist.
```

The ledger-level version is:

```text
promoteTrialLedger_preserves_invariant
```

Meaning:

```text
If a ledger-backed candidate promotes to REVIEWED, then the ledger contains a passing proof receipt for that target.
```

## Warden gates

### Gate 1 — Build success is not proof authority

Blocked claim:

```text
The Lean build passed, therefore the claim is reviewed.
```

Allowed claim:

```text
The Lean build passed; it is a build receipt, not review authority.
```

### Gate 2 — Executable success is not proof authority

Blocked claim:

```text
The executable returned the expected result, therefore the theorem is proven.
```

Allowed claim:

```text
The executable produced an eval receipt that may support candidate status.
```

### Gate 3 — Benchmark success is not proof authority

Blocked claim:

```text
The benchmark passed, therefore the invariant is reviewed.
```

Allowed claim:

```text
The benchmark is evidence, but promotion requires a proof receipt.
```

### Gate 4 — Adversarial trial is not self-review

Blocked claim:

```text
The adversarial trial passed, therefore it may mark itself REVIEWED.
```

Allowed claim:

```text
A passed adversarial trial may emit CANDIDATE status unless a proof receipt exists.
```

## Relation to the recovered workspace log

The recovered log described a broader state:

```text
ReceiptCore.lean added
GeometricCompressionWorkspace receipt theorem repaired
executable evals passed
receipt theorem previously blocked then fixed
summary docs updated
```

Only the first safe unit has been reintroduced here:

```text
ReceiptCore.lean as a standalone scaffold
```

The missing follow-up integration should be treated as future work until the target files are located and patched directly.

## Required follow-up receipts

To promote this above `BEAUTIFUL_PROVISIONAL`, collect:

```text
Lean build receipt for ReceiptCore.lean
import receipt from the surrounding workspace
proof receipt that GeometricCompressionWorkspace imports ReceiptCore cleanly
proof receipt that CANDIDATE promotion remains blocked without proofReceipt
proof receipt that ledger-backed promotion implies ledger proof authority
```

## Non-goals

This spec does not claim:

```text
all recovered-log files have been restored
GeometricCompressionWorkspace has been patched
all #eval outputs have been re-run in CI
receipt infrastructure is complete
benchmarks imply theorem validity
```

## Strongest formulation

The useful claim is:

> ReceiptCore establishes a minimal formal boundary between evidence and review authority: candidates may accumulate receipts, but REVIEWED status requires a passing proof receipt.

That is the part OTOM should absorb first.
