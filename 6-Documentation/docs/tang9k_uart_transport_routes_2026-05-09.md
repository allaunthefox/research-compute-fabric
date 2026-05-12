# Tang Nano 9K UART Transport Routes

**Date:** 2026-05-09

Transport route table only. The active virtual route validates host Q16 serial framing and parser behavior. It does not validate live FPGA fabric or the Tang Nano onboard UART bridge.

## Active Route

- Active route: `virtual://q16-pty`
- Status: `PASS_ACTIVE_VIRTUAL_ROUTE`

## Route Table

| Route | Device | Kind | Status |
| --- | --- | --- | --- |
| `onboard-ftdi-a` | `/dev/ttyUSB0` | `physical_ftdi_mpsse_or_bridge` | `BLOCKED_FOR_FABRIC_UART` |
| `onboard-ftdi-b` | `/dev/ttyUSB1` | `physical_ftdi_secondary_endpoint` | `BLOCKED_FOR_FABRIC_UART` |
| `external-usb-uart` | `/dev/ttyUSB2_or_/dev/ttyACM0` | `physical_external_adapter` | `PENDING_HARDWARE` |
| `virtual-q16-pty` | `virtual://q16-pty` | `pty_backed_virtual_serial` | `PASS_VIRTUAL_SERIAL` |

## Routing Policy

- Default non-hardware route: `virtual://q16-pty`
- Live hardware promotion requires:
  - external or verified onboard route captures beacon payload a6425131360a
  - Q16 shift, weighted, and monotone hardware receipts match software expectations
  - stack audit reports FPGA hardware witness PASS

## Machine Receipt

- `shared-data/data/stack_solidification/tang9k_uart_transport_routes.json`
