# Stack Solidification Unified Kanban

Date: 2026-05-09

Hygiene refresh: 2026-05-10

Status: `BOARD_SURFACE_CREATED`

Claim boundary: this is a unified board view over existing receipts and roadmap
items. It does not close HOLD gates, promote hardware acceleration, or replace
the underlying receipts.

Machine-readable board:

```text
shared-data/data/stack_solidification/stack_solidification_kanban_cards.json
```

## Source Surfaces

- `TODO_MAP.md`
- `6-Documentation/docs/roadmaps/ROADMAP.md`
- `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
- `shared-data/data/germane/architecture/BUILDER_KANBAN_SPEC.md`
- `shared-data/data/stack_solidification/stack_fail_closure_register.json`
- `shared-data/data/stack_solidification/rrc_hold_closure_checklist.json`
- `shared-data/data/stack_solidification/rust_oisc_decompressor_target_receipt.json`
- `shared-data/data/stack_solidification/bernoulli_occupancy_shockbow_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_full_cell_eigenmass_stability_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_sandpile_graph_replay_receipt.json`
- `shared-data/data/stack_solidification/hutter_transfer_readiness_fixture_manifest.json`

## Done

| Card | Title | Receipt |
|---|---|---|
| KANBAN-001 | Create unified stack-solidification kanban surface | `shared-data/data/stack_solidification/stack_solidification_kanban_cards.json` |
| KANBAN-002 | Lean/Semantics build gate | `shared-data/data/stack_solidification/stack_solidification_receipt.json` |
| KANBAN-003 | Stack JSON and Python shim integrity gates | `shared-data/data/stack_solidification/stack_solidification_receipt.json` |
| KANBAN-004 | Rust OISC decompressor Lean/Rust replay surface | `shared-data/data/stack_solidification/rust_oisc_decompressor_target_receipt.json` |
| KANBAN-005 | Q16 virtual serial transport route | `shared-data/data/stack_solidification/tang9k_rrc_q16_virtual_serial_probe.json` |
| KANBAN-021 | Stellar gas full-cell eigenmass stability controls | `shared-data/data/stellar_gas_observation/stellar_gas_full_cell_eigenmass_stability_receipt.json` |
| KANBAN-022 | Stellar gas sandpile graph replay | `shared-data/data/stellar_gas_observation/stellar_gas_sandpile_graph_replay_receipt.json` |
| KANBAN-023 | Hutter transfer readiness fixture | `shared-data/data/stack_solidification/hutter_transfer_readiness_fixture_manifest.json` |
| KANBAN-012 | RRC route promotion closure checklist | `shared-data/data/stack_solidification/rrc_hold_closure_checklist.json` |

## In Progress

| Card | Title | Next Action |
|---|---|---|
| KANBAN-006 | RRC projection HOLD surface | Add `scale_band_declared` witnesses and negative-control strength fields, then rerun the receipt. |
| KANBAN-007 | FAMM module status and dead-code distinction | Keep duplicate/dead module cleanup separate from theorem-bearing FAMM status. |
| KANBAN-008 | Universe model orbit-zoom protocol | Add local law test fixtures before using the protocol as a promotion gate. |
| KANBAN-024 | DESI/MaNGA object-level crossmatch | Build object-level crossmatch receipts with provenance, selection-function boundaries, and negative controls. |

## HOLD

| Card | Title | Why Held | Next Action |
|---|---|---|---|
| KANBAN-009 | Adaptive Beaver mask security | Finite negative controls pass, but full MPC privacy and adaptive security are not proved. | Add formal independence, entropy-source, non-reuse, and leakage negative-control receipts. |
| KANBAN-010 | Network topology coefficient calibration | 9 coefficient rows are registered as HOLD priors, not calibrated coefficients. | Attach provenance, calibration, sensitivity, and negative-control receipts. |
| KANBAN-011 | Network topology prediction validation | 15 prediction rows are queued as HOLD, not validation claims. | Pre-register targets and attach independent outcome comparison receipts. |
| KANBAN-013 | Bernoulli occupancy / Shockbow static decompressor gate | Lean gate exists; Rust replay and residual policy remain HOLD. | Wire Rust reference replay and CMR/residual fixtures. |
| KANBAN-014 | Rust OISC production decompressor lane | Toy Lean/Rust replay exists and a small non-toy byte-exact fixture now replays in Rust; residual policy, AMMR/O-AMMR receipts, full Hutter fixture eigenmass, FPGA lowering, and ASIC datapath remain HOLD. | Add fixture eigenmass replay, residual policy, and negative-control accounting before hardware lowering. |
| KANBAN-025 | Stellar gas physical calibration and mechanism claims | DESI row eigenmass, DESI/MaNGA cell eigenmass, multiscale alignment, full-cell controls, and graph replay are observational proxy diagnostics only. | Require object crossmatch, physical gas calibration, shock mechanism validation, selection-function fit, and cosmology separation before promotion. |

## Blocked

| Card | Title | Blocker | Next Action |
|---|---|---|---|
| KANBAN-015 | Live Tang Nano 9K fabric UART route | Physical UART/fabric receipts fail or return no bytes. | Attach external USB-UART to fabric pins 17/18 and test beacon before Q16 accelerator retry. |
| KANBAN-016 | Durable FPGA flash programming | SRAM load passes CRC; flash programming readback fails. | Keep SRAM-only claim boundary until flash command and board target are verified. |
| KANBAN-017 | Worktree-safe release scope | Broad working tree is dirty. | Keep stack-solidification, CPU/logogram/wiki, and hardware slices separated by manifest. |

## Next

| Card | Title | Next Action |
|---|---|---|
| KANBAN-018 | Audit Lean for sorry/admit/axiom | Run the strict actionable grep and address remaining theorem debt without deleting theorem surfaces. |
| KANBAN-019 | Create surface skeleton | Create the minimal FastAPI/WebSocket skeleton only after source-of-truth card data stays stable. |
| KANBAN-020 | Seed omni builder kanban service | Use the JSON card file as the seed input for the future `omni://builder/kanban` HTTP surface. |
| KANBAN-026 | Hutter fixture eigenmass replay and controls | Run fixture-level eigenmass only after raw/zlib/lzma/current-wire accounting, negative controls, and exact replay receipts close. |
| KANBAN-027 | RRC compiler promotion rerun | Rerun the compiler against the refreshed `0 open` checklist and record whether the six former HOLD objects become CANDIDATE or remain HOLD for compiler-level reasons. |

## Operating Rule

This board is the current stack-solidification kanban until the builder kanban
service is seeded. Source receipts remain authoritative. If a card conflicts
with a receipt, the receipt wins and the card must be updated.
