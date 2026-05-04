# Tiny IP Emulator

This is a Contiki-inspired concept emulator for the embedded surface shell
layer. It does not make UDP semantic. The shell label can be `udp`, `onion`,
`serial`, `ipv923u`, or anything else; the internal payload is a two-byte
Omnitoken scalar/LUT selector.

It models:

- cooperative event-loop ticks
- fixed MTU admission
- two-byte scale-invariant scalar/LUT payloads
- lossy, duplicated, and reordered links
- app-level ACKs
- timer-based retransmission
- duplicate suppression
- quorum reporting

Run:

```bash
make -C infra/embedded_surface/tinyip run
make -C infra/embedded_surface/tinyip stress
```
