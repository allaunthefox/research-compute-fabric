# IBM-II Software Ethernet Surface

This harness treats an IBM-II-class machine as a software Ethernet controller
surface. Ethernet is only the local shell. The admitted Omnitoken object is
still the two-byte scale-invariant LUT selector:

```text
u8 domain
u8 scalar
```

The controller emulates constraints that matter for old/small machines:

- four-slot RX ring
- 160-byte receive slot budget
- Ethernet-like frame shell with EtherType `0x88B5`
- CRC/FCS rejection before LUT admission
- no JSON parsing on the tiny side

The hosted observer can still emit JSON-L provenance after the tiny controller
has admitted the scalar.

Run:

```sh
make -C infra/embedded_surface/ibmii run
make -C infra/embedded_surface/ibmii noisy
make -C infra/embedded_surface/ibmii burst
```
