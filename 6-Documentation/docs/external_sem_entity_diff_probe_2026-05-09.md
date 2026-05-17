# External sem Entity-Diff Probe

**Date:** 2026-05-09

## Decision

- Status: `OPTIONAL_AUDIT_AID_READY`
- No implementation code was imported.
- No repository dependency was added.
- Use only as an optional external audit aid unless explicitly vendored later.

## Why It Helps

- Primary fit: `FAIL-WORKTREE-SCOPE-007`, because entity-level diffs reduce broad dirty-tree risk.
- Secondary fit: `FAIL-RECEIPT-GATE-006`, because entity IDs can be attached to receipt and rollback checklists.
- It does not close security, coefficient, topology prediction, or FPGA transport gates by itself.

## Tool Boundary

- Source: `https://github.com/Ataraxy-Labs/sem`
- License: `MIT OR Apache-2.0`
- Requested binary: `/tmp/sem_probe/sem/crates/target/release/sem`
- Version result: `sem 0.5.3`
- `/usr/bin/sem` collision: `True`

## Entity Probe

### `4-Infrastructure/shim/stack_fail_closure_register.py`

- Status: `PASS`
- `function` `load_json` lines 20-21
- `function` `ticket` lines 24-43
- `function` `build_register` lines 46-215
- `function` `build_doc` lines 218-252
- `function` `main` lines 255-261

### `4-Infrastructure/shim/tang9k_uart_beacon_probe.py`

- Status: `PASS`
- `function` `read_port` lines 18-50
- `function` `main` lines 53-83

### `4-Infrastructure/shim/stack_solidification_audit.py`

- Status: `PASS`
- `class` `CmdResult` lines 43-49
- `function` `rel` lines 52-53
- `function` `run_cmd` lines 56-72
- `function` `load_json` lines 75-76
- `function` `file_sha256` lines 79-86
- `function` `json_gate` lines 89-105
- `function` `py_compile_gate` lines 108-111
- `function` `compiler_gate` lines 114-127
- `function` `tri_cycle_gate` lines 130-150
- `function` `lean_gate` lines 153-157
- `function` `hardware_bitstream_gate` lines 160-168
- `function` `worktree_gate` lines 171-194
- `function` `build_doc` lines 197-259
- `function` `main` lines 262-290

### `4-Infrastructure/shim/rrc_tri_cycle_audit.py`

- Status: `PASS`
- `class` `CmdResult` lines 106-112
- `function` `run_cmd` lines 115-131
- `function` `load_json` lines 134-135
- `function` `load_uart_beacon_diagnostics` lines 138-194
- `function` `scan_less_solid_surfaces` lines 197-216
- `function` `bucket_for_line` lines 219-231
- `function` `run_q16_witnesses` lines 234-308
- `function` `summarize_rrc` lines 311-331
- `function` `bucket_counts` lines 334-338
- `function` `active_gate_register` lines 341-347
- `function` `build_doc` lines 350-419
- `function` `main` lines 422-491

## Machine Receipt

- `shared-data/data/stack_solidification/external_sem_entity_diff_probe_receipt.json`
