# USB/IP Mesh Transport Design

> Status: design + capability probe. This document does not claim any exported
> USB device is live until a matching `usbip` attach receipt exists.

## Decision

Use USB/IP as an optional transport surface over the existing Tailscale mesh.
The local hardware probe showed that QFox and the laptop expose USB host
controllers, not USB gadget/device-mode ports. USB/IP matches that reality:
each node can keep acting as a USB host for physically attached devices while
making selected USB devices reachable to another node over IP.

## Transport Model

```
physical USB device
  -> exporting node xHCI host controller
  -> usbip-host + usbipd
  -> Tailscale/WiFi/Babel-routed IP path
  -> importing node vhci-hcd
  -> local kernel driver on importing node
```

USB/IP is not a replacement for USB-C host-to-host cabling. It is a remote bus
projection: one machine owns the physical port, another machine imports a
virtual host-controller slot.

## Roles

| Role | Responsibility | Required support |
|------|----------------|------------------|
| exporter | owns physical USB device and offers it to the mesh | `usbip-host`, `usbipd`, TCP 3240 on mesh-only address |
| importer | consumes a remote USB device as if local | `vhci-hcd`, `usbip attach` |
| controller | decides which node should export/import | Tailscale reachability, policy, receipts |

## Candidate Devices

Good candidates:

- USB serial adapters for FPGA / microcontroller boards.
- USB storage for short maintenance windows.
- USB NICs or active bridge cables when a node has better physical placement.
- Cameras, sensors, and test fixtures where single-owner access is acceptable.

Avoid or treat as experimental:

- Keyboards/mice used for local recovery.
- Bluetooth and WiFi controllers already needed by the exporting host.
- Audio/video devices with tight latency expectations.
- Security-sensitive devices unless the mesh ACL and exporter are trusted.

## Security Boundary

USB/IP has a large trust boundary because the importing kernel parses remote USB
traffic. Treat it as a privileged infrastructure path, not an open service.

Minimum policy:

- Bind/listen only on Tailscale or a private mesh address.
- Restrict TCP 3240 with host firewall and Tailscale ACLs.
- Export only explicit bus IDs, never all USB devices.
- Require an operator action or policy receipt before `usbip bind`.
- Prefer one active importer per exported device.
- Record attach/detach receipts with exporter, importer, bus ID, VID:PID, driver,
  and route metrics.

## Integration With Mesh Routing

The USB/IP path should be a transport candidate in the same selector as WiFi and
Tailscale:

| Transport | Purpose | Cost notes |
|-----------|---------|------------|
| local USB | direct attached device on current node | lowest software latency |
| USB/IP over LAN/WiFi | remote physical USB device in 5ft cluster | depends on WiFi latency and loss |
| USB/IP over Tailscale | non-local node device access | encrypted, reliable, higher latency |
| native IP service | prefer when device protocol already has an IP-native API | avoids kernel USB remoting |

For non-local nodes, USB/IP should ride over Tailscale first. If later we add
Babel across WiFi Direct/AP links, the USB/IP controller can choose the lower
cost route but should keep the service bound to a mesh-only interface.

## Probe

Capability probe:

```bash
bash 4-Infrastructure/auto/nodes/usbip.sh
```

The probe emits JSON with:

- `tools.usbip` and `tools.usbipd`
- kernel module availability/load state for `usbip_core`, `usbip_host`, `vhci_hcd`
- whether `usbipd` is active and TCP 3240 is listening
- visible USB devices by bus ID, VID:PID, speed, product, and current driver

The probe is observe-only. It does not bind, export, attach, or detach devices.

## Bring-Up Plan

1. Install userland `usbip` tools on QFox, nixos-laptop, and any non-local node
   that may export/import devices.
   - QFox/CachyOS: `sudo pacman -S usbip`
   - NixOS: add `pkgs.linuxPackages.usbip` to `environment.systemPackages`
     for the active kernel package set.
2. Load/persist modules:
   - exporters: `usbip-core`, `usbip-host`
   - importers: `usbip-core`, `vhci-hcd`
3. Run the probe on each node and store receipts.
4. Pick one low-risk test device, preferably a spare USB serial adapter.
5. On exporter:
   - `usbip list -l`
   - `usbip bind -b <busid>`
   - start `usbipd` on a mesh-only address if supported by the installed daemon,
     otherwise firewall TCP 3240 to Tailscale peers only.
6. On importer:
   - `usbip list -r <exporter-tailscale-ip>`
   - `usbip attach -r <exporter-tailscale-ip> -b <busid>`
   - verify the expected local device appears.
7. Record attach receipt and detach cleanly:
   - `usbip port`
   - `usbip detach -p <port>`

## Claim Boundaries

- A capability probe proves only that tools/modules/devices are visible.
- `usbip bind` proves only that an exporter made one bus ID available.
- `usbip attach` plus local device enumeration proves a remote USB projection.
- Device-specific success requires a higher-level receipt, such as UART bytes,
  block-device read, camera frame, or NIC link.

## Initial Probe Result

Current QFox and nixos-laptop probes show:

- Kernel modules are available and loaded on both nodes: `usbip-core`,
  `usbip-host`, `vhci-hcd`.
- Userland tools are installed on both nodes:
  - QFox: `/usr/bin/usbip`, `/usr/bin/usbipd`
  - nixos-laptop: `/run/current-system/sw/bin/usbip`,
    `/run/current-system/sw/bin/usbipd`
- No `usbipd` service was active and TCP 3240 was not listening.
- Both nodes exposed candidate physical USB devices through sysfs.

This means the remaining bring-up is policy/service/device selection, not
kernel or package availability.
