# Stack Fail Closure Register

**Date:** 2026-05-09

This register turns current failures into closure gates. It does not mark them solved.

## Summary

- Tickets: `7`
- Promotion decision: `NO_PROMOTION`
- FPGA software status: `PASS`
- FPGA hardware status: `NOT_REQUESTED`

## Tickets

### `FAIL-FPGA-UART-001` Live fabric UART transport has no observable bytes

- Class: `fpga_transport_or_witness_debt`
- Status: `BLOCKED`
- Owner surface: `6-Documentation/docs/fpga_uart_route_analysis_2026-05-09.md`
- Evidence: Q16 software witness passes
- Evidence: Q16 hardware witness returns short receipt frames
- Evidence: TX-only beacon standard pins produced zero bytes on ttyUSB0 and ttyUSB1
- Evidence: TX-only beacon swapped pins produced zero bytes on ttyUSB0 and ttyUSB1
- Evidence: Old faXX/ffXX direct-probe interpretation is superseded as bridge/MPSSE behavior, not fabric proof
- Evidence: FPGA UART route analysis identifies the onboard BL702 bridge route as blocked and recommends external USB-UART
- Evidence: Forced JTAG reset plus SRAM reload succeeds, but beacon/Q16 UART receipts remain empty
- Evidence: Loopback-after-JTAG-clear diagnostic produced faXX-style bytes on ttyUSB0, consistent with bridge/MPSSE behavior rather than a valid fabric receipt
- Evidence: PTY-backed virtual serial Q16 probe: PASS_VIRTUAL_SERIAL (3/3 matches)
- Evidence: UART transport router active route: virtual://q16-pty (PASS_ACTIVE_VIRTUAL_ROUTE)
- Closure gate: external USB-UART or verified onboard bridge captures beacon payload a6425131360a
- Closure gate: loopback or beacon receipt passes before Q16 accelerator retry
- Closure gate: Q16 hardware receipts match software receipts for shift, weighted, and monotone cases
- Next action: Attach external USB-UART: adapter TX to fabric RX pin 18, adapter RX to fabric TX pin 17, and GND to GND
- Next action: Probe the new adapter path, usually /dev/ttyUSB2 or /dev/ttyACM0, with the TX-only beacon before Q16
- Next action: If external UART works, patch host default port or call scripts with --port and rerun Q16 hardware receipts
- Next action: If external UART fails, inspect PNR pin placement and add LED-observed heartbeat fallback

### `FAIL-FPGA-FLASH-002` Durable flash programming readback fails

- Class: `fpga_transport_or_witness_debt`
- Status: `HELD_SRAM_ONLY`
- Owner surface: `6-Documentation/docs/fpga_rrc_q16_accel_setup_2026-05-09.md`
- Evidence: SRAM load passes CRC
- Evidence: Flash programming attempt had readback CRC failure
- Closure gate: flash write and readback CRC pass for the exact Q16 bitstream
- Closure gate: or documentation keeps SRAM-only boundary explicit
- Next action: Keep SRAM-only claim boundary until flash command and board target are verified
- Next action: Do not mark hardware install persistent

### `FAIL-SECURITY-BEAVER-003` Adaptive Beaver coefficients are not privacy-equivalent masks yet

- Class: `security_proof_debt`
- Status: `HOLD`
- Owner surface: `Network-Topology-Theory.md + Fundamental_Network_Topology_Equation.md`
- Evidence: 6 security proof debt surfaces found
- Evidence: tri-cycle audit blocks promotion for adaptive mask claims
- Evidence: mask freshness negative controls: PASS_NEGATIVE_CONTROLS
- Evidence: mask freshness case count: 6
- Closure gate: formal independence/freshness theorem exists
- Closure gate: secret-sharing non-reuse receipt exists
- Closure gate: negative control shows adapted coefficients do not leak party inputs
- Next action: Add a Lean-facing finite-state mask freshness model
- Next action: Generate negative-control fixtures for repeated coefficients and topology-derived coefficients

### `FAIL-COEFFICIENT-CALIBRATION-004` Numeric weights remain receipt-weighted priors, not calibrated coefficients

- Class: `coefficient_or_calibration_debt`
- Status: `HOLD`
- Owner surface: `shared-data/network_topology_database.json`
- Evidence: 20 coefficient/calibration debt surfaces found
- Evidence: receipt reweighting exists, but coefficient calibration and negative controls remain open
- Evidence: coefficient HOLD manifest rows: 9
- Closure gate: dataset provenance receipt linked
- Closure gate: coefficient calibration receipt linked
- Closure gate: sensitivity sweep and negative controls pass
- Next action: Create coefficient calibration fixture manifest
- Next action: Separate hypothesis weights from calibrated weights in docs and JSON surfaces

### `FAIL-TOPOLOGY-PREDICTION-005` Topology predictions are not validation claims

- Class: `topology_prediction_debt`
- Status: `HOLD`
- Owner surface: `shared-data/network_topology_database.json`
- Evidence: 13 topology prediction debt surfaces found
- Evidence: tri-cycle audit requires pre-registered target and independent comparison
- Evidence: prediction HOLD registry rows: 15
- Closure gate: pre-registered prediction target exists
- Closure gate: outcome receipt exists
- Closure gate: independent public map or measurement comparison exists
- Next action: Create prediction-target registry with timestamps and immutable receipt hashes
- Next action: Move existing predicted nodes into HOLD prediction queue, not validation table

### `FAIL-RECEIPT-GATE-006` Route promotion lacks complete receipt and rollback closure

- Class: `receipt_gate_debt`
- Status: `HOLD`
- Owner surface: `4-Infrastructure/shim/rainbow_raccoon_compiler.py`
- Evidence: 11 receipt-gate debt surfaces found
- Evidence: compiler keeps 6 objects HOLD and only 1 candidate
- Evidence: compiler receipt hash: c006c48939fd12a280642e4fb70841fe502641d4c80233bef00b3c710e3f31ba
- Evidence: optional sem entity probe: OPTIONAL_AUDIT_AID_READY
- Evidence: HOLD closure checklist: 0 open documentation closures after RRC Gatekeeper refresh
- Closure gate: validation receipt exists
- Closure gate: rollback hash exists
- Closure gate: exact replay or decode closure hash matches
- Next action: Rerun compiler promotion against the refreshed rrc_hold_closure_checklist.json
- Next action: Do not widen candidate admission beyond Q16 until Lean or independent replay closes

### `FAIL-WORKTREE-SCOPE-007` Broad worktree is too dirty for safe sweep commit

- Class: `release_hygiene_debt`
- Status: `BLOCKED_FOR_BROAD_STAGE`
- Owner surface: `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
- Evidence: worktree status: DIRTY
- Evidence: changed/untracked count: 949
- Evidence: staging manifest created for the solidification slice
- Evidence: optional sem entity probe: OPTIONAL_AUDIT_AID_READY
- Closure gate: commit scope is explicit file list
- Closure gate: generated artifacts are intentionally included or excluded
- Closure gate: no unrelated modified Lean/doc/probe files are swept in
- Closure gate: entity-level change list exists for staged or scoped files when sem is available
- Next action: Use stack_solidification_staging_manifest_2026-05-09.md before any commit
- Next action: Create separate manifests for CPU/logogram/wiki maturation slices if needed
- Next action: Use /tmp/sem_probe/sem/crates/target/release/sem, not /usr/bin/sem, unless a durable sem binary is installed

## Machine Receipt

- `shared-data/data/stack_solidification/stack_fail_closure_register.json`
