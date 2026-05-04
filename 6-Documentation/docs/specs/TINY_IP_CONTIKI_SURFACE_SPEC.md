# Tiny IP Surface Spec

**Version:** 0.1  
**Status:** Draft  
**Scope:** Contiki-inspired shell concepts for embedded GCL/Omnitoken nodes  
**Reference implementation:** `infra/embedded_surface/tinyip/tinyip_emulator.py`

---

## Thesis

The embedded surface needs a shell layer that is small enough to reason about,
test, and eventually port into tiny carriers.

We do not need to clone Contiki, and Omnitoken must not become UDP. We want the
concepts that made Contiki useful on constrained systems:

1. Cooperative event loop.
2. Fixed packet buffers.
3. Timers instead of blocking calls.
4. Small datagram-like shell packets.
5. Explicit neighbor and route tables.
6. Application-level acknowledgments where reliability matters.
7. Admission before payload expansion.

The shell surface is not the root of trust. It is only the local appearance that
moves an admitted Omnitoken scalar between observer charts.

---

## Layer Shape

```text
GCL operation
  -> Omnitoken scalar/LUT entry
  -> local shell packet
  -> lossy link / serial / tunnel / hosted process
```

Tiny nodes may collapse the lower layers:

```text
Omnitoken scalar -> tiny packet buffer -> shell send
```

The shell may be named `udp`, `onion`, `serial`, `websocket`, `ipv923u`, or any
future substrate label. The shell name does not decide meaning.

---

## Core Concepts

### Cooperative Processes

Each node owns small cooperative processes. A process runs only when the event
loop dispatches an event to it. It must return quickly.

Required process classes:

| Process | Purpose |
|---------|---------|
| `net_rx` | Admit inbound packet headers |
| `net_tx` | Drain outbound packets |
| `timer` | Fire retransmit and maintenance events |
| `shell_app` | Handle tiny shell messages |
| `lut_bridge` | Project admitted scalar to Omnitoken/GCL |

No process may block waiting for network I/O.

### Packet Buffer

Each node has a fixed number of packet buffers. If all buffers are full, the
node refuses or drops work before expansion.

Recommended tiny defaults:

```text
MTU                  96 bytes
RX buffers            4
TX buffers            4
neighbor entries      8
route entries         8
```

### Tiny IP Header

The emulator uses symbolic fields, but the portable shape is:

```text
src       u16
dst       u16
proto     u8
seq       u16
ttl       u8
flags     u8
len       u8/u16
payload   bytes
```

`src` and `dst` are short atlas-local addresses, not public Internet addresses.

### OMNIsurface LUT Payload

The internal payload is an ultracompressed LUT selector, not a protocol-specific
message:

```text
u8 domain
u8 scalar
```

The 1D scalar is scale-invariant: different shells may encode it with different
padding, framing, or transport metadata, but the admitted `(domain, scalar)`
pair maps to the same LUT entry.

Example:

```text
0x0D 0x01 -> recover / recovery_subset / BOOT_OK
```

Reliability is not assumed at the shell layer. If a GCL transition needs proof
of receipt, the app sends an ACK scalar.

Required app messages:

| Domain | Scalar | Meaning |
|--------|--------|---------|
| `0x0D` | `0x01` | Recovery pulse |
| `0x0A` | `0x01` | Acknowledge a sequence |
| `0x01` | `0x01` | Health pulse |
| `0x0F` | `0x01` | Lawful refusal |

---

## Admission Rules

Before accepting a packet as state:

1. Header must parse.
2. `ttl` must be greater than zero.
3. Payload length must be within MTU.
4. Duplicate `(src, seq)` must be ignored.
5. `(domain, scalar)` must exist in the finite LUT.
6. GCL admission must accept the expanded operation.

The link may be lossy, duplicated, reordered, or stale. None of those conditions
make a packet state by themselves.

---

## Carrier Classes

| Class | Meaning |
|-------|---------|
| `tinyip_loopback` | In-process emulator |
| `tinyip_serial` | Serial or PTY link |
| `tinyip_tunnel` | Tailscale/TCP/WebSocket shell |
| `tinyip_kvm` | KVM guest surface via I/O or MMIO |
| `tinyip_qemu` | QEMU/TCG guest surface |
| `tinyip_ipv923u` | Future shell label; internal scalar unchanged |

Every class shares the same packet/admission behavior.

---

## Success Criteria

A tiny IP surface is healthy if:

1. All nodes can emit a recovery scalar.
2. The controller receives one valid pulse per node.
3. Duplicate pulses are ignored.
4. Lost pulses are retransmitted by timer.
5. Oversized payloads are refused before expansion.
6. Quorum can be reached under lossy links.
