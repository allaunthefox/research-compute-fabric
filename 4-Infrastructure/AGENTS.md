# AGENTS.md - Infrastructure And Hardware

Scope: `4-Infrastructure/`

## Rules

- Keep infrastructure scripts receipt-bearing: every probe should have a
  machine-readable output or update an existing receipt.
- Separate software witnesses from live hardware witnesses.
- Do not claim FPGA acceleration from bitstream generation alone.
- Do not claim UART/fabric success without observed bytes or a matching hardware
  receipt.
- Treat `/usr/bin/sem` as GNU Parallel on this machine unless proven otherwise;
  use the isolated `sem` binary documented in stack solidification receipts when
  needed.

## Preferred Checks

```bash
python3 -m py_compile 4-Infrastructure/shim/<script>.py
python3 -m json.tool <receipt>.json >/dev/null
```

For Tang Nano 9K work, keep the boundaries explicit:

- bitstream present
- SRAM load
- flash persistence
- UART beacon
- Q16/software witness
- Q16/live hardware witness

## Current Stack-Solidification Anchors

- `4-Infrastructure/shim/stack_solidification_audit.py`
- `4-Infrastructure/shim/stack_fail_closure_register.py`
- `4-Infrastructure/shim/beaver_mask_freshness_negative_controls.py`
- `4-Infrastructure/shim/tang9k_uart_beacon_probe.py`
- `4-Infrastructure/shim/hutter_jxl_starfield_eigenprobe.py`
- `4-Infrastructure/shim/hutter_jxl_starfield_replay_verify.py`
