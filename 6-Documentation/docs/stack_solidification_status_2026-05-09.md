# Stack Solidification Status

**Date:** 2026-05-09

**Hygiene refresh:** 2026-05-10

## Bottom Line

The stack is buildable and internally gateable, but not promotable as a live hardware-accelerated system yet.

## Gates

- Full Lean/Semantics build: `SKIPPED`
- JSON integrity: `PASS`
- Python shim compile: `PASS`
- Support receipt refresh: `PASS`
- Rainbow Raccoon compiler: `PASS_WITH_HOLDS` (1 candidate, 6 HOLD)
- Tri-cycle audit: `PASS`; promotion decision `NO_PROMOTION`
- FPGA software witness: `PASS`
- FPGA hardware witness: `NOT_REQUESTED`
- UART beacon seen: `False`
- Hardware bitstreams present: `PASS`
- Optional sem entity-diff aid: `OPTIONAL_AUDIT_AID_READY`
- RRC HOLD closure checklist: `PASS_ALL_ITEMS_CLOSED` (0 open; compiler rerun still required before promotion)
- Network HOLD manifests: `PASS_HOLD_QUEUES_DECLARED` (9 coefficient rows, 15 prediction rows)
- Beaver mask freshness controls: `PASS_NEGATIVE_CONTROLS` (6 cases)
- Whitespace-zero grammar: `PASS_ZERO_WHITESPACE_CANONICAL` (3 admitted, 3 HOLD)
- Q16 virtual serial probe: `PASS_VIRTUAL_SERIAL` (3/3 matches)
- UART transport routes: `PASS_ACTIVE_VIRTUAL_ROUTE` (active `virtual://q16-pty`)
- Stack fail closure register: `PASS_TICKETS_DECLARED` (7 tickets)
- SMN tool awareness: `PASS` (ADMIT_SMN_TOOL_AWARENESS)
- Worktree: `DIRTY`
- Staging manifest: `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`

## Current Solid Core

- Lean/Semantics builds end to end.
- Core JSON receipts and network topology database parse.
- Compiler gate admits only the Q16 fixed-point lowering certificate as candidate.
- Q16 software witness lane passes.
- Q16 host UART framing and parser pass over a PTY-backed virtual serial device.
- UART route table now selects the PTY-backed Q16 route while keeping blocked physical routes visible.
- HOLD buckets are explicit rather than silently promoted.
- Optional sem entity extraction is available for scoped Python audit files.
- SMN is tool-visible as Semantic Mass Number and explicitly separated from Mass Number admissibility packets.
- Every compiler HOLD object now has an explicit closure checklist, and the RRC Gatekeeper has closed `11/11` documentation closures.
- Current failures and broad HOLD buckets have closure tickets in a stack fail register.
- Network topology coefficients and predictions are split into HOLD queues.
- Beaver mask freshness has Lean-backed finite negative controls; full MPC security remains HOLD.
- Canonical logogram grammar can derive ordinary spaces from symbol count/order with zero stored whitespace codes.
- Agent routing now has repo-root, Lean/Semantics, and Infrastructure contracts.
- Stack receipts and the network topology database are visible through narrow `.gitignore` exceptions instead of broad `shared-data/` exposure.

## Current Blockers

- Live FPGA UART transport remains blocked: beacon receipts show no bytes on `/dev/ttyUSB0` or `/dev/ttyUSB1`.
- Hardware acceleration claims remain blocked until the UART route or external adapter path produces matching receipts.
- Security, coefficient, topology-prediction, and receipt-gate debts remain HOLD surfaces.
- The worktree is broad and dirty; do not stage by directory sweep.
- `/usr/bin/sem` is GNU Parallel on this machine; use the isolated sem binary path if sem is needed.

## Less Solid Surface Counts

- `coefficient_or_calibration_debt`: 20
- `fpga_transport_or_witness_debt`: 9
- `general_hold_surface`: 69
- `receipt_gate_debt`: 11
- `security_proof_debt`: 6
- `topology_prediction_debt`: 13

## Next Stabilization Moves

1. Resolve fabric UART transport with board bridge docs or an external USB-UART adapter.
2. Work the closure register tickets in order: UART transport, flash persistence, adaptive-mask security, coefficient calibration, topology predictions, receipt gates, then worktree scope.
3. Rerun the Rainbow Raccoon compiler against the refreshed closure receipts before changing any HOLD/CANDIDATE status.
4. Produce a scoped staging manifest before any commit because the working tree contains many unrelated/generated surfaces.

## Receipt

- Machine receipt: `shared-data/data/stack_solidification/stack_solidification_receipt.json`
- Staging manifest: `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
