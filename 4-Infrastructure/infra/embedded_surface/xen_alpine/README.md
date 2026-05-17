# Xen Alpine rs-surface

This is a minimal Alpine Linux carrier for the existing `rs-surface` embedded
node API. It is meant for small Xen guests where the useful interface is:

- serial console first: `console=hvc0`
- OpenRC service: `rs-surface`
- Python stdlib only at runtime
- HTTP receipts: `/health`, `/status`, `/metrics`, `/primitives`
- binary WebSocket frame lane: `/ws`

The guest does not need a full Research Stack checkout. The install script
copies only `server.py`, one profile JSON file, and the OpenRC service.

## Nanokernel Framing

The minimal path is a two-stage carrier:

```text
Xen/QEMU hardware model
  -> Alpine Linux with VirtIO and serial drivers
  -> rs-surface OpenRC service
  -> bounded GCL/nanokernel primitive surface
  -> future signed layer0 image handoff
```

In this stage, Alpine is not the trusted architecture. It is the driver shim and
rollback carrier. The current `rs-surface` process exposes the nanokernel-shaped
contract: bounded operations, local state budget, serial-first recovery, health
receipts, route decisions, snapshots, and explicit refusal of unimplemented
recovery transitions.

The profile records a future `layer0-gcl-nanokernel` handoff, but keeps
`destructive_handoff_allowed=false` and `handoff=manual` until a signed layer0
image, rollback boot entry, serial health pulse, and QEMU health probe all
exist. That makes the nanokernel approach incremental rather than theatrical:
first prove the carrier and receipt lane, then replace the Python carrier with
the smaller layer0 runtime.

## Files

- `xen-alpine-rs-surface.cfg`: `xl` domain template.
- `install_rs_surface_openrc.sh`: installs the interface inside Alpine.
- `rs-surface.openrc`: OpenRC service file.
- `rs_surface_static.c`: small static C surface for uClibc/musl/glibc-static.
- `rs_surface_nolibc.c`: smaller x86_64 Linux syscall-only surface.
- `smoke_xen_alpine_surface.py`: receipt-producing HTTP smoke check.
- `run_qemu_alpine_surface.sh`: disposable QEMU boot smoke using Alpine netboot.
- `../profiles/xen-alpine-surface.json`: default local/recovery profile.

## Alpine Guest Install

From a checked-out repo inside the Alpine guest:

```sh
cd "4-Infrastructure/infra/embedded_surface/xen_alpine"
doas ./install_rs_surface_openrc.sh
doas rc-service rs-surface start
python3 ./smoke_xen_alpine_surface.py --output /tmp/rs-surface-smoke.json
```

For a tiny copied payload, set `SOURCE_ROOT` to the directory containing
`server.py` and `profiles/xen-alpine-surface.json`:

```sh
doas SOURCE_ROOT=/tmp/rs-surface ./install_rs_surface_openrc.sh
```

## QEMU Smoke

The QEMU harness downloads Alpine `latest-stable` virt netboot assets, builds a
small `apkovl` overlay containing `rs-surface`, boots Alpine under QEMU, and
polls the forwarded health endpoint.

```sh
make -C 4-Infrastructure/infra/embedded_surface/xen_alpine qemu-smoke
```

For the stripped embedded path, build and boot the syscall-only static surface.
This is the preferred reduction target for now because it has no libc, no
dynamic linker, no Python runtime, no heap, and only a small Linux syscall
surface:

```sh
make -C 4-Infrastructure/infra/embedded_surface/xen_alpine qemu-static-smoke
```

When a uClibc toolchain is available, the C surface can be built with:

```sh
make -C 4-Infrastructure/infra/embedded_surface/xen_alpine static \
  CC=x86_64-buildroot-linux-uclibc-gcc
```

Current local receipt from the no-libc path:

```text
runtime=static-nolibc
surface_version=0.1-nolibc
text+data+bss=1627 bytes
stripped ELF=2.4K
```

Receipt and serial log are written under:

```text
4-Infrastructure/infra/embedded_surface/xen_alpine/build/qemu-alpine/
```

Those files are ignored because they include downloaded kernel/initramfs/modloop
assets and transient boot logs.

## Xen Host Sketch

1. Create a small Alpine guest disk, install `linux-lts`, `openrc`, `python3`,
   and `ca-certificates`.
2. Ensure the guest kernel command line includes `console=hvc0`.
3. Copy the tiny surface payload into the guest.
4. Start the domain with an edited copy of `xen-alpine-rs-surface.cfg`.
5. Attach serial console with `xl console rs-alpine-surface`.
6. Verify from inside the guest:

```sh
rc-service rs-surface status
wget -qO- http://127.0.0.1:8080/health
```

## Bind Modes

The default profile binds to localhost. For an exposed appliance, prefer a
Tailscale address by editing the copied profile:

```json
"api": {
  "plain_health_port": 8080,
  "websocket_port": 8080,
  "bind": "tailscale",
  "tailscale_ip": "100.x.y.z"
}
```

Public bind is supported by the server, but should be paired with an outer
firewall or reverse proxy.
