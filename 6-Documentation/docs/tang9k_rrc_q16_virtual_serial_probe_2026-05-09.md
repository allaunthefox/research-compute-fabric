# Tang Nano 9K Q16 Virtual Serial Probe

**Date:** 2026-05-09

Virtual serial probe only. This validates the host Q16 UART framing, receipt parser, and opcode semantics over a PTY-backed serial device; it does not validate live FPGA fabric or the Tang Nano UART route.

## Status

- Status: `PASS_VIRTUAL_SERIAL`
- Cases: `3`
- Matches: `3`

## Cases

- `shift`: match `True`, receipt `4-Infrastructure/shim/tang9k_rrc_q16_virtual_shift_receipt.json`
- `weighted`: match `True`, receipt `4-Infrastructure/shim/tang9k_rrc_q16_virtual_weighted_receipt.json`
- `monotone`: match `True`, receipt `4-Infrastructure/shim/tang9k_rrc_q16_virtual_monotone_receipt.json`

## Machine Receipt

- `shared-data/data/stack_solidification/tang9k_rrc_q16_virtual_serial_probe.json`
