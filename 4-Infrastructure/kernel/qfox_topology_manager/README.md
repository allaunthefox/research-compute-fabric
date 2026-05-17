# QFox Topology Manager

`qfox_topology_manager` is the passive Linux-carrier phase of the GCL
nanokernel idea. It is intentionally an out-of-tree kernel module first, not a
core-kernel patch: the module observes kernel-adjacent events, maps them into
named topology slots, and exposes a receipt surface for userspace.

The module is a module/driver hybrid:

- misc device: `/dev/qfox_topoman`
- sysfs: `/sys/kernel/qfox_topology_manager/`
- debugfs: `/sys/kernel/debug/qfox_topology_manager/`
- kernel notifiers: network-device events and reboot/power events
- manual injection path for userspace shims and future kernel call sites

The operating rule is conservative:

> The GCL nanokernel may classify and receipt carrier behavior, but this Linux
> module does not become the root of trust and does not enforce policy.

## Build

```bash
make
sudo insmod qfox_topology_manager.ko
python3 probe_qfox_topology_manager.py --json
sudo rmmod qfox_topology_manager
```

The repo path contains a space, and Linux kbuild does not handle `M=...` paths
with spaces reliably. For now, build from a spaceless staging directory:

```bash
stage=/tmp/qfox_topology_manager_build
rm -rf "$stage"
install -d "$stage"
cp Makefile dkms.conf qfox_topology_manager.c qfox_topology_debug.sh \
  probe_qfox_topology_manager.py README.md "$stage"/
make -C "$stage" CC=clang LLVM=1
```

## DKMS Install

```bash
sudo install -d /usr/src/qfox-topology-manager-0.1.0
sudo cp Makefile dkms.conf qfox_topology_manager.c /usr/src/qfox-topology-manager-0.1.0/
sudo dkms add -m qfox-topology-manager -v 0.1.0
sudo dkms build -m qfox-topology-manager -v 0.1.0
sudo dkms install -m qfox-topology-manager -v 0.1.0
sudo modprobe qfox_topology_manager
```

Auto-load is intentionally a separate choice:

```bash
echo qfox_topology_manager | sudo tee /etc/modules-load.d/qfox-topology-manager.conf
```

## Topology Slots

| Slot | Meaning |
| --- | --- |
| `boot` | module lifecycle and boot-adjacent state |
| `sched` | scheduler / execution carrier observations |
| `mm` | memory-management observations |
| `fs` | filesystem and VFS observations |
| `block` | block-device / request observations |
| `net` | network-device observations |
| `device` | driver/device lifecycle observations |
| `power` | reboot and power-transition observations |
| `security` | admission, refusal, and policy-surface observations |
| `gpu` | GPU/display carrier observations |
| `user` | userspace shim injection |
| `receipt` | receipt or attestation emission |

## Interfaces

Read module status:

```bash
cat /sys/kernel/qfox_topology_manager/status
cat /sys/kernel/qfox_topology_manager/slots
```

Measure the first activity average:

```bash
python3 probe_qfox_topology_manager.py --sample-sec 10
```

Inject a userspace observation:

```bash
echo "fs repo_scan /home/allaun/Documents/Research Stack" \
  | sudo tee /sys/kernel/qfox_topology_manager/inject
```

Read the event surface:

```bash
sudo cat /sys/kernel/debug/qfox_topology_manager/events
cat /dev/qfox_topoman
```

Write to `/dev/qfox_topoman` to inject an event. The first token may be a slot
name; otherwise the event is treated as `user`.

## Live Debugger

Attach the non-halting ftrace debugger:

```bash
sudo ./qfox_topology_debug.sh attach
sudo ./qfox_topology_debug.sh snapshot
sudo ./qfox_topology_debug.sh detach
```

This uses function-graph tracing for the module call path. It does not stop the
kernel, require a reboot, or replace the normal boot path.

Sample wider kernel tracepoints into topology slots:

```bash
sudo python3 qfox_topology_trace_sampler.py --duration 10
```

The sampler temporarily enables available tracepoints for scheduler, memory,
filesystem syscall, block, network, power, and interrupt/device surfaces. It
restores prior tracepoint state and can inject per-slot summaries back into the
module's misc-device receipt path.

When `/home/allaun/Gdrive` is mounted, `qfox-topology-sample` also mirrors the
small JSON receipts to:

```text
/home/allaun/Gdrive/topological_storage/research-stack/qfox-topology-manager/
```

Generate an optimization-target report from collected samples:

```bash
python3 qfox_topology_optimizer_report.py
```

The report ranks topology slots by observed activity and produces advisory
targets such as scheduler wakeup churn, memory allocation churn, block IO,
network chatter, device/IRQ pressure, and power/idle transition churn. The
report is a receipt for what to inspect next; it does not change sysctls,
kernel parameters, IRQ affinity, CPU policy, or scheduler behavior.
