# Tang Nano 9K Metastability & CDC Boundary Analysis
**Device**: Gowin GW1NR-9 (Gowin LittleBee Family)
**Target**: Sovereign Research Stack - AVM Bridge

## 1. Metastability Summary
The Tang Nano 9K operates on a 27MHz crystal. For the AVM Bridge, the primary Clock Domain Crossing (CDC) risk is the asynchronous UART RX ingress (Pin 18).

### CDC Mitigation Strategy
- **UART RX Synchronizer**: A 3-stage shift-register synchronizer is mandated for all asynchronous inputs to prevent metastable states from propagating into the AVM state machine.
- **MTBF Estimation**: At 27MHz, a 3-stage synchronizer provides a Mean Time Between Failures (MTBF) exceeding the operational lifespan of the system.

## 2. UART Timing Constraints (115200 Baud)
- **Clock**: 27,000,000 Hz
- **Baud**: 115,200 bits/sec
- **Cycles per bit**: ~234.37
- **Clock Drift Tolerance**: ±2% (Standard UART specification).

### Constraints File (CST) Requirements
```tcl
IO_LOC "clk" 52;
IO_PORT "clk" PULL_MODE=UP;
IO_LOC "uart_tx" 17;
IO_PORT "uart_tx" IO_TYPE=LVCMOS33;
IO_LOC "uart_rx" 18;
IO_PORT "uart_rx" IO_TYPE=LVCMOS33;
```

## 3. Boundary Invariant
The AVM state-hash must only be updated on the `posedge clk` after the input signals have passed through the synchronization boundary. Any un-synchronized input detected by the Judge during a cycle-audit will result in a **Warden Refusal**.

---
**Status**: CALIBRATED_DOC_COMPLETE
**Lattice State**: LOCKED
