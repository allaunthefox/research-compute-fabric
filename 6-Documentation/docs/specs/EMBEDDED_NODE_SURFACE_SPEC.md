# Embedded Node Surface Specification

**Version:** 0.1  
**Status:** Draft for reusable deployment  
**Target nodes:** Racknerd, Netcup, Architect, Hutter, local edge nodes  
**Protocol reference:** `docs/specs/OMNITOKEN_GCL_REDESIGN.md`  
**GCL revision reference:** `docs/specs/GCL_TOPOLOGY_REVISION_SPEC.md`  
**Principle:** A node is a small observer chart, not a full general-purpose stack.
The kernel contract is a GCL nanokernel; Linux is only one possible carrier.

---

## Purpose

This spec defines a reusable embedded surface for low-resource nodes. The node
keeps only the local machinery required to join the atlas, expose a minimal API,
recover itself, and mount external state. Bulk data, datasets, archives, and
large working sets are provided by Google Drive topological storage through an
ENE-managed mount.

The surface does not require Linux as its conceptual kernel. The portable
kernel contract is the GCL nanokernel: the smallest executable transition unit
that admits work, routes state, checks recovery transitions, emits receipts, and
exposes the node as an observer chart. Linux, LFS, NixOS, unikernels,
bare-metal firmware, or a VM monitor may host that contract, but they are
substrate choices rather than the mathematical center.

The intended result is a small, repeatable node shape:

```text
GCL nanokernel + read-only carrier + tiny writable state + compressed API + recovery
```

This avoids deploying the full Research Stack onto nodes that are better used as
lightweight coordinate charts. RackNerd is the first `GCL-Edge`: a constrained
edge node whose primary job is to host the GCL nanokernel, expose recovery and
health, and carry topology phases without running the full research stack.
Operationally, RackNerd is an appliance server: it has a narrow managed surface,
bounded local state, explicit update channels, and no expectation that operators
log in to run arbitrary workloads.

Builder, Warden, and Judge behavior are not deployed as separate software
layers. They are topology phases carried by the general node surface:

1. Builder is the topology's constructive/forward phase.
2. Warden is the topology's inhibitory/verification phase.
3. Judge is the topology's adjudication/settlement phase.

Historical builder, warden, and judge state, receipts, and validation routines
are topology artifacts. A node may expose these phases through topology
capabilities, but there is no standalone Builder, Warden, or Judge runtime
boundary in the embedded profile.

---

## Design Constraints

Every conforming node MUST:

1. Preserve SSH or recovery console access during upgrades.
2. Boot without Google Drive being available.
3. Treat the GDrive mount as optional external state, never as the root of trust.
4. Expose a plain recovery health endpoint even if the compressed API fails.
5. Keep writable local state small, explicit, and backed up.
6. Admit work through RGFlow/compression policy before local execution.
7. Support atomic image or service rollback.

Every conforming node SHOULD:

1. Use a compressed read-only root or read-only service bundle.
2. Use tmpfs for transient logs and scratch.
3. Store persistent node identity under a single state directory.
4. Keep large data in mounted topological storage.
5. Prefer push/pull artifacts over building locally.

---

## Appliance Server Model

An appliance server is a node operated as a sealed function rather than as a
general-purpose host. The RackNerd `GCL-Edge` appliance exposes only the surface
needed to join the atlas, emit receipts, answer health/status probes, carry
topology phases, and recover itself.

Appliance invariants:

1. The primary runtime is `rs-surface-api.service`.
2. Builder, Warden, and Judge are topology phases inside the surface.
3. Legacy full-stack services remain masked unless a rescue procedure explicitly
   says otherwise.
4. Local mutation is restricted to `/var/lib/rs-surface`, bounded spools,
   rollback slots, and explicit topology artifacts.
5. Software changes enter through in-place nanokernel updates, A/B release
   updates, or provider rescue pivots.
6. The node is not a build worker, dataset host, database server, or ad hoc
   shell box.

The appliance may still use Debian, systemd, SSH, and Tailscale as carrier
facilities. Those facilities serve the appliance contract; they do not redefine
the node as a general VM.

---

## Surface Layers

```text
+------------------------------------------------------------+
| Atlas clients / controller                                 |
+------------------------------------------------------------+
| Compressed WebSocket API + plain /health fallback           |
+------------------------------------------------------------+
| Admission layer: RGFlow, compression policy, attestation    |
+------------------------------------------------------------+
| MNN routing: adaptive path formation (local/atlas/reject) |
+------------------------------------------------------------+
| Topology phases: builder, warden, judge                     |
+------------------------------------------------------------+
| Local actions: route, attest, compress, status, recovery    |
+------------------------------------------------------------+
| State: /var/lib/rs-surface + optional GDrive mount          |
+------------------------------------------------------------+
| Carrier: Linux, LFS, Nix, unikernel, firmware, VM monitor   |
+------------------------------------------------------------+
```

The MNN (Morphic Neural Network) routing layer sits between admission and local actions. It uses:
- Goal-aware routing (health, attest, compress, route, recover)
- State-constrained decisions (memory, CPU, recovery mode, trust score)
- Carrier-agnostic adaptation (works with any shell)
- Cost-aware optimization (energy, time, bandwidth)
- Historical learning (adaptive morphic topology)

See `docs/specs/MORPHIC_NEURAL_NETWORK_ROUTING_SPEC.md` for the complete MNN specification.

The surface is intentionally carrier-agnostic. Debian can host it first; later
nodes may boot directly into an embedded image or a GCL-native runtime. The
important object is the topological substrate: the set of admitted primitives
that the GCL nanokernel can expose safely on a given carrier.

### Topological Substrate Primitive Exposure

A node does not need KVM to become a topological device. KVM, QEMU, Linux
processes, unikernels, firmware loops, and serial controllers are all carriers.
The GCL nanokernel is responsible for exposing the primitive vocabulary that
matters to the atlas.

Every appliance SHOULD expose a primitive descriptor:

```text
GET /primitives
WS op 10: primitives
```

The descriptor names:

1. The substrate class.
2. The carrier used to host the substrate.
3. Whether primitives are exposed through the kernel surface.
4. Compute slots and memory reserve.
5. Primitive names, such as `attest`, `compress`, `rgflow`, `route`,
   `plan_route`, `vector_filter`, `delta_batch`, `merkle_mmr`,
   `content_chunk`, `wiki`, `fractal_fold`, `meta_autotype`, and `receipt`.
6. Optional accelerators, such as AVX-512, BF16, VNNI, VAES, VPCLMULQDQ, or
   SHA-NI.

The primitive descriptor is descriptive, not a permission grant. Admission,
topology phases, and receipt checks still decide whether a requested transition
is lawful.

### Nanokernel Route Planning Primitive

The nanokernel route planner is a bounded pre-admission selector:

```text
WS op 11: plan_route
```

It applies:

```text
payload
-> metaprobe payload signature
-> MS3C/S3C shell codon
-> sequence/GCL motif/informaton surface selection
-> RGFlow persistence check
-> compression route tuple
```

The returned tuple has:

```text
surface
motif
witness
compressor
```

This tuple is not execution authority. It is a route-prior hint consumed by
GCL admission. The required gate remains:

```text
OBSERVE -> BIND -> ROUTE -> SIGMA_CHECK -> POLICY_CHECK -> DAG_CHECK -> VERIFY -> RECEIPT
```

If FAMM marks the shell region as saturated failure, the planner SHOULD downrank
or refuse similar route teeth before local execution.

The typed Lean vocabulary for this contract lives in:

```text
0-Core-Formalism/lean/Semantics/Semantics/GCLTopologyRevision.lean
```

That module fixes the distinction between route hints and authority: a
`RouteHint` cannot directly authorize execution, even if it comes from MS3C,
metaprobe, RGFlow, Sparkle, or a node primitive.

### ENE Wiki Primitive

The ENE wiki primitive is a MediaWiki-like knowledge surface without a full
MediaWiki runtime:

```text
WS op 12: wiki
```

It supports compact JSON requests:

```json
{"op":"put","title":"GCL","text":"See [[MS3C]] [[Category:Topology]]"}
{"op":"get","title":"GCL"}
{"op":"search","query":"topology"}
{"op":"backlinks","title":"MS3C"}
{"op":"recent","limit":20}
```

The implementation is `infra/ene_wiki_layer.py`. It stores revision history,
links, categories, backlinks, and recent changes in SQLite. Every write emits:

1. an ENE `BaseArchiveRecord`-style object using `source_type=json_catalog`;
2. a Unified JSON-L event using `src=ene` and `op=upsert`;
3. a deterministic receipt hash;
4. a schema-compatible `packages` upsert.

This keeps the wiki layer inside the ENE substrate instead of creating a
separate application authority.

### ENE Fractal Fold Primitive

The fractal fold primitive is the canonical ENE surface for self-similar
recursive storage and retrieval:

```text
WS op 13: fractal_fold
```

It supports compact JSON requests:

```json
{"op":"put","name":"payload","text":"...","chunk_size":4096,"branching_factor":4}
{"op":"put_graphml","name":"research_graph","data_b64":"..."}
{"op":"navigate","root_hash":"...","leaf_index":31}
{"op":"proof","root_hash":"...","leaf_index":31}
{"op":"verify","root_hash":"..."}
{"op":"graph_entity","root_hash":"...","graph_node_id":"n31"}
{"op":"graph_neighbors","root_hash":"...","graph_node_id":"n31"}
```

The implementation is `infra/ene_fractal_fold.py`. It stores a recursive hash
tree in SQLite. Leaves use Gray-code folded addresses; navigation projects
folded addresses onto a golden-spiral chart and descends by manifold-distance
pruning. With fixed branching factor, entity retrieval is `O(log n)` in the
number of leaves. Damage is detectable because leaves and parents are checked
through fractal parent/child hash consistency.

GraphML is treated as a concept surface. Each GraphML node becomes one fractal
leaf carrying `graph_node_id`, `name`, `family`, `domain`, folded address,
golden-spiral coordinate, and outgoing neighbors. This lets ENE retrieve graph
concepts by the same fractal path used for raw payload chunks.

### ENE Meta-Autotype Primitive

The meta-autotype primitive handles unknown or fragmented ingestion surfaces:

```text
WS op 14: meta_autotype
```

It supports:

```json
{"name":"unknown_payload","text":"..."}
{"name":"unknown_payload","data_b64":"..."}
```

The implementation is `infra/ene_meta_autotype.py`. It deterministically emits
contingent fields with inferred type, confidence, extraction rule, bind class,
and receipt. These fields are not authority; they are provisional topology
until a defined ingestion surface binds them through the normal GCL gate.

### Bind Policy

The profile's `api.bind` field is normative:

| `api.bind` | Runtime bind host |
|------------|-------------------|
| `localhost` | `127.0.0.1` |
| `tailscale` | `api.tailscale_ip` or top-level `tailscale_ip` |
| `public` | `0.0.0.0` |

`RS_SURFACE_HOST` may override this during smoke tests, but production units
SHOULD omit it so the profile controls exposure. If `api.bind` is `tailscale`
and no Tailscale IP is present, the surface MUST fail closed rather than bind
publicly.

### KVM Carrier Addressing

Most deployment nodes are themselves virtual machines, so KVM must be treated as
an optional nested carrier rather than assumed bare metal. A node with no KVM
can still be a first-class topological substrate by exposing primitives directly
through the GCL nanokernel.

KVM addressing has three separate layers:

```text
host virtual pointer -> KVM memslot -> guest physical address -> guest CS:RIP
```

The guest physical address is not host physical memory. It is an address in a
userspace-owned memslot registered with `KVM_SET_USER_MEMORY_REGION`.

Minimal KVM surfaces MUST record:

1. Whether `/dev/kvm` exists and is openable.
2. Whether `KVM_CREATE_VM`, `KVM_CREATE_VCPU`, and `KVM_RUN` succeed.
3. The memslot number.
4. The guest physical base.
5. The guest entry address.
6. The I/O or MMIO pulse channel used for recovery output.

Carrier classification:

| Class | Meaning | Required behavior |
|-------|---------|-------------------|
| `kvm_native` | Hardware virtualization is directly available | Run KVM carrier |
| `kvm_nested` | KVM works inside a VM | Run KVM carrier with slower-exit budget |
| `kvm_unavailable` | `/dev/kvm` missing or denied | Fall back to QEMU TCG or hosted process |
| `kvm_restricted` | VM starts but required exits fail | Refuse or quarantine carrier |

KVM MUST NOT become the root of trust. It is only a carrier for admitted GCL
state. If KVM is unavailable, the node should expose the recovery surface and
topological primitives through another carrier.

---

## GCL Nanokernel Contract

GCL is the nanokernel of a node: the smallest trusted control surface that can
perform a bounded transition and produce a receipt. It is not required to be the
hardware kernel in the Unix sense. It is the invariant-preserving layer that
decides what the carrier is allowed to do.

Local repo usage treats a nanokernel as:

1. A tiny executable unit.
2. Local state.
3. Message passing.
4. Bounded transition.
5. Receipt.

For morphic topology, the nanokernel also assigns candidate niches for morphic
scalars. Assignment is a measurement hypothesis, not final permission; the
topology phases and AngrySphinx-style checks still decide whether collapse is
admissible.

GCL MUST provide:

1. Node identity and local observer-frame metadata.
2. Admission control for requested operations.
3. RGFlow/compression policy hooks.
4. Route selection or local execution refusal.
5. Attestation of state transitions.
6. Recovery transition checks.
7. A plain health signal independent of the compressed API.

GCL SHOULD be small enough to port across carriers. A Linux-hosted daemon, an
initramfs recovery binary, a unikernel service, a microcontroller firmware, or a
tiny VM monitor shim can all be valid GCL nanokernel carriers if they satisfy
the same contract.

The carrier MAY provide:

1. Process isolation.
2. Filesystems and mounts.
3. TCP/IP, WireGuard, Tailscale, or serial transport.
4. Timers and watchdogs.
5. Hardware drivers.

The carrier MUST NOT be the root of trust for atlas decisions. Those decisions
belong to GCL.

---

## Layer 0 Handoff Target

The long-term target is for the GCL nanokernel to become Layer 0: the first
meaningful runtime after firmware/provider boot. In that mode, Linux is no
longer the node's operating environment. Linux is only a bootstrap loader,
hardware discovery tool, artifact fetcher, and emergency recovery substrate.

The intended destructive handoff is:

```text
provider firmware / VPS boot
  -> minimal Linux loader
  -> verify signed Layer 0 image + last-good receipt
  -> kexec handoff
  -> GCL nanokernel Layer 0
  -> topology primitives, receipts, recovery pulse
```

After handoff, the current Linux userspace may be intentionally discarded. That
is the point: legacy services, model routers, ad hoc shell state, package
sprawl, and ordinary daemon assumptions should not survive into Layer 0.

### Kexec Role

`kexec` is the preferred bridge when the provider requires a normal Linux boot
but the node wants to replace Linux without a full firmware reboot. The loader
kernel prepares memory, validates the Layer 0 artifact, then transfers control
to the GCL image.

The Layer 0 image may initially be a tiny Linux/initramfs appliance, unikernel,
or purpose-built kernel. What matters is not the implementation label; what
matters is that the GCL nanokernel owns the primitive boundary and emits
receipts before admitting work.

### Layer 0 Gates

A node MUST NOT perform a destructive handoff until all gates pass:

1. Provider rescue console or reinstall path is confirmed.
2. A rollback boot entry or previous working image exists.
3. The Layer 0 image is signed or hash-pinned.
4. The loader can emit a pre-handoff receipt.
5. The Layer 0 image can emit a console, serial, or provider-visible health
   pulse without Tailscale.
6. The Layer 0 image can answer `/health` or the Omnitoken recovery equivalent.
7. Node identity and topology artifacts are preserved or intentionally sealed.
8. The operator has an out-of-band recovery window.

Until those gates exist, `destructive_handoff_allowed` MUST remain `false` in
node profiles. Hosted `rs-surface-api.service` remains the safe Phase 0
appliance.

Profiles SHOULD make the handoff mechanically checkable by declaring:

```json
{
  "layer0_image": {
    "path": "/boot/gcl/layer0-netcup.img",
    "sha256": "TBD",
    "signature": "/boot/gcl/layer0-netcup.img.sig",
    "public_key": "/etc/rs-surface/layer0.pub",
    "cmdline": "console=ttyS0 gcl.node=netcup-router gcl.mode=layer0"
  },
  "rollback": {
    "boot_entry": "debian-loader-last-good",
    "previous_image": "/boot/gcl/layer0-netcup.previous.img",
    "provider_rescue": "netcup-rescue-console"
  }
}
```

`sha256: "TBD"` is valid only while `destructive_handoff_allowed` is `false`.
Before enabling destructive handoff, the image digest and signature path MUST
refer to real artifacts.

### Preservation Set

Even when the Linux userspace is wiped, these concepts survive the handoff:

1. Node identity.
2. Last-good receipt.
3. Recovery pulse.
4. Topology artifacts such as `judge.tardy`, MMR roots, and node profile.
5. Primitive descriptor.
6. Provider recovery instructions.

Everything else is disposable unless the profile explicitly preserves it.

---

## JupiterBox and Omnitoken Carrier

For constrained nodes, the preferred GCL carrier envelope is JupiterBox and the
preferred wire/codon layer is Omnitoken.

JupiterBox provides the box boundary:

1. A bounded execution envelope.
2. A small routing identity.
3. A multiplexing slot for swarm traffic.
4. A place to attach recovery and last-good metadata.
5. A carrier abstraction that can run over Linux, serial, Tailscale, I2P, or a
   future non-Linux substrate.

Omnitoken provides the packet language:

1. Finite operation names instead of open strings.
2. Small typed fields for value, timestamp, tags, and checksum.
3. Fragmentation/reassembly for larger payloads.
4. A bridge into existing swarm transport and MIMO routing.
5. A natural path to codon compression on tiny RAM targets.

The normal embedded surface can expose WebSocket for compatibility, but the
inner frame SHOULD be Omnitoken-compatible:

```text
carrier transport
  -> JupiterBox envelope
  -> Omnitoken/GCL frame
  -> operation payload
```

On large carriers, the stack may be:

```text
WebSocket or Tailscale TCP -> JupiterBox -> Omnitoken -> GCL op
```

On tiny carriers, the stack may collapse to:

```text
serial frame -> Omnitoken codon -> GCL op
```

Or, on an IBM-II-class software Ethernet surface:

```text
Ethernet-looking shell -> 2-byte Omnitoken scalar/LUT selector -> GCL op
```

The Ethernet controller does not need to implement IP. It only validates the
local shell boundary, extracts the invariant `(domain, scalar)` pair, and lets
GCL decide admission.

This is how the same node surface can scale from Racknerd down toward an 8 KB
RAM target. The carrier changes; the GCL operation vocabulary does not.

### 8 KB RAM Shape

At the smallest target, JupiterBox is not a container in the Linux sense. It is a
fixed memory envelope:

```text
RX frame       512 B
TX frame       512 B
GCL registers  512 B
route table      1 KB
compression      1 KB
recovery log     1 KB
stack          512 B
free margin      3 KB
```

The tiny target MUST NOT require JSON, HTTP, WebSocket, TLS, malloc, a
filesystem, or dynamic loading. It only needs enough Omnitoken/GCL vocabulary to
say:

```text
health
status
attest
rgflow-admit
compress
route
snapshot
recover
```

---

## Filesystem Contract

### Required Local Paths

| Path | Mode | Purpose |
|------|------|---------|
| `/opt/rs-surface` | read-only preferred | Surface daemon, static assets, API schema |
| `/etc/rs-surface/node.json` | read-only or managed | Node identity and role profile |
| `/var/lib/rs-surface` | persistent writable | Identity, tokens, last-good marker, tiny state |
| `/var/log/rs-surface` | tmpfs or capped persistent | Ring logs and boot reports |
| `/run/rs-surface` | tmpfs | Sockets, pid files, ephemeral cache |
| `/mnt/topological-storage` | optional mount | GDrive/rclone topological storage |

### Required Persistent State

```text
/var/lib/rs-surface/
  node-id
  authorized_keys
  api-token.hash
  ed25519-node.key
  last-good.json
  boot-count
  state.sqlite       optional, small
  recovery/
    last-failure.log
    rollback-target
```

Persistent state MUST stay small enough to archive and restore quickly.

### External State

Google Drive topological storage SHOULD be mounted at:

```text
/mnt/topological-storage
```

Recommended remote layout:

```text
gdrive:topological_storage/
  nodes/<node-id>/
    inbox/
    outbox/
    artifacts/
    snapshots/
    logs/
  shared/
    datasets/
    models/
    manifests/
    dictionaries/
```

Nodes MUST tolerate the mount being absent. On mount failure, the node remains in
normal mode with degraded storage, or enters recovery mode only if local state is
also invalid.

---

## Runtime Modes

### Normal Mode

Normal mode runs the compressed API and the minimal local action set.

Required services:

```text
rs-surface-api
rs-surface-heartbeat
rs-storage-mount        optional/degraded if unavailable
```

Allowed operations:

```text
health
status
metrics
attest
compress
rgflow
route
mount-status
snapshot
enter-recovery
```

### Recovery Mode

Recovery mode is deliberately boring. It MUST NOT depend on custom compression,
RGFlow, GDrive, or the normal API.

Required recovery services:

```text
dropbear or sshd
plain HTTP /health
rollback command
mount inspection
log dump
authorized_keys restore
```

Allowed operations:

```text
GET  /health
GET  /boot-report
POST /rollback
POST /mark-good
POST /reboot-normal
```

Recovery mode MUST be able to run with only local disk and network.

---

## API Contract

### Plain HTTP Fallback

Every node MUST expose:

```text
GET /health
```

Minimal response:

```json
{
  "ok": true,
  "node": "racknerd-510bd9c",
  "mode": "normal",
  "surface_version": "0.1",
  "storage": "mounted|degraded|absent",
  "last_good": true
}
```

### Compressed WebSocket Endpoint

Normal mode SHOULD expose:

```text
GET /ws
```

The WebSocket transport carries custom binary frames. The custom layer is inside
WebSocket for compatibility with browsers, proxies, and standard debugging
tools.

Frame format:

```text
byte  0      version       currently 1
byte  1      flags         bitfield
byte  2      codec         0 none, 1 zstd, 2 lz4, 3 hutter, 4 rgflow-zstd
byte  3      op            finite operation id
u32le 4..7   request_id
u32le 8..11  payload_len
u32le 12..15 crc32_payload
bytes 16..N  payload
bytes N..M   optional ed25519 signature when flags.sig = 1
```

Operation IDs:

| ID | Operation | Notes |
|----|-----------|-------|
| 0 | `health` | same meaning as `/health` |
| 1 | `status` | node status and local budgets |
| 2 | `metrics` | capped telemetry |
| 3 | `attest` | hash/sign payload |
| 4 | `compress` | run compression policy |
| 5 | `rgflow` | admission/classification |
| 6 | `route` | forward or queue task |
| 7 | `mount_status` | report external storage state |
| 8 | `snapshot` | write tiny local snapshot |
| 9 | `enter_recovery` | authenticated only |

Payloads are canonical JSON unless the operation explicitly declares a binary
body. Binary bodies MUST include a JSON envelope with content hash, codec, and
size.

---

## Compression Policy

Compression is not automatic for every frame. The node chooses the cheapest
lawful path:

| Payload | Codec |
|---------|-------|
| Tiny control frames | `none` |
| Repeated telemetry | `zstd` with shared dictionary |
| Hot local API frames | `lz4` or `none` |
| Attestation bundles | `zstd` |
| Semantic or dataset payloads | RGFlow admission, then `zstd` |
| Unknown/high entropy payloads | reject, route, or store externally |

No node should spend more CPU compressing a payload than it saves in network,
memory, or storage cost. On tiny nodes, the first optimization is often to avoid
local work and route it elsewhere.

---

## GDrive Mount Contract

The mount provider SHOULD be `rclone`, managed by ENE credentials.

Recommended mount command shape:

```bash
rclone mount Gdrive:topological_storage /mnt/topological-storage \
  --read-only \
  --vfs-cache-mode minimal \
  --dir-cache-time 5m \
  --poll-interval 1m \
  --buffer-size 4M \
  --vfs-read-chunk-size 4M \
  --vfs-read-chunk-size-limit 32M
```

Tiny nodes SHOULD default to read-only mounts. Writes go through an explicit
outbox path or a controller-mediated upload:

```text
/mnt/topological-storage/nodes/<node-id>/outbox/
```

If write support is required, use a bounded local spool:

```text
/var/lib/rs-surface/spool/
```

The spool MUST have a byte cap and MUST degrade gracefully when full.

---

## Node Profile

Each node has a small JSON profile:

```json
{
  "surface_version": "0.1",
  "node_id": "racknerd-510bd9c",
  "role": "gcl-edge",
  "mode_default": "normal",
  "operational_model": "appliance",
  "memory_budget_mb": 715,
  "disk_budget_gb": 9,
  "local_state_budget_mb": 128,
  "api": {
    "plain_health_port": 8080,
    "websocket_port": 8080,
    "bind": "tailscale",
    "tailscale_ip": "100.103.54.58"
  },
  "storage": {
    "provider": "gdrive",
    "mount_point": "/mnt/topological-storage",
    "remote": "Gdrive:topological_storage",
    "required_for_boot": false,
    "write_mode": "outbox",
    "spool_budget_mb": 128
  },
  "capabilities": [
    "health",
    "status",
    "metrics",
    "attest",
    "compress",
    "rgflow",
    "route",
    "nanokernel",
    "topology",
    "builder",
    "warden",
    "judge",
    "mount_status",
    "snapshot",
    "recovery"
  ],
  "disabled": [
    "full_git_checkout",
    "local_training",
    "local_build",
    "large_database",
    "legacy_warden_service",
    "legacy_tardy_service",
    "legacy_substrate_index_service",
    "legacy_compression_gateway_service"
  ]
}
```

Profiles are deployable across nodes by changing only identity, budgets, and
capabilities.

---

## Upgrade and Rollback

The surface supports both in-place nanokernel updates and A/B-style deployment
even when hosted on Debian. RackNerd as `GCL-Edge` SHOULD use the smallest safe
upgrade path:

- **In-place nanokernel upgrade:** routine changes to the GCL control surface,
  profile, topology phase wiring, or small service-unit corrections.
- **In-place carrier kernel upgrade:** routine Linux kernel package updates on
  the Debian carrier when SSH/Tailscale and provider rescue fallback are ready.
- **A/B release upgrade:** larger release bundles, carrier changes, storage
  layout changes, or updates where the previous release must remain bootable.
- **Rescue pivot:** host repair, root filesystem work, SSH/Tailscale recovery,
  or anything that might make the node unreachable.

### In-Place Nanokernel Upgrade

The in-place path keeps the running OS, SSH access, Tailscale identity, topology
state, and legacy-service masks intact. It updates only the GCL nanokernel
carrier files:

```text
/opt/rs-surface/current/server.py
/etc/rs-surface/node.json
/var/lib/rs-surface/last-good.json
```

Operator entrypoint:

```bash
sudo infra/embedded_surface/gcl_edge_in_place_upgrade.sh upgrade \
  /tmp/rs-surface-upgrade/server.py \
  /tmp/rs-surface-upgrade/node.json
```

In-place upgrade steps:

1. Stage the new `server.py` and `node.json` outside the live paths.
2. Compile-check Python and parse-check JSON.
3. Start the candidate server on a temporary localhost port.
4. Run `/health` against the candidate.
5. Copy current live files into
   `/var/lib/rs-surface/rollback/inplace-<timestamp>/`.
6. Install the candidate files atomically into the live paths.
7. Run `systemctl daemon-reload` and restart `rs-surface-api.service`.
8. Run post-start `/health`.
9. Mark `last-good.json` only after health succeeds.

If restart or health fails, restore the rollback copy, restart the service, and
health-check again:

```bash
sudo infra/embedded_surface/gcl_edge_in_place_upgrade.sh rollback \
  /var/lib/rs-surface/rollback/inplace-<timestamp>
```

An in-place update MUST NOT repartition disks, format filesystems, replace the
bootloader, alter SSH authorization, reset Tailscale identity, or unmask the
legacy Builder/Warden/Judge runtimes. Builder, Warden, and Judge are topology
phases of the GCL nanokernel surface; they are not restored as standalone
services.

### In-Place Carrier Kernel Upgrade

When "kernel" means the Linux carrier kernel rather than the GCL nanokernel,
RackNerd MAY still update in place, but only as a controlled reboot operation.
This path is for normal Debian security/kernel package updates, not topology
rewrites.

Carrier kernel in-place steps:

1. Confirm provider rescue mode is available and SSH authorization is intact.
2. Capture current boot state:
   `uname -a`, `lsblk -f`, `findmnt /`, `systemctl is-enabled rs-surface-api.service`.
3. Confirm `/boot` has enough free space and keep at least one previous kernel.
4. Apply the kernel package update without removing old kernels.
5. Run `update-grub` or the carrier's bootloader refresh command.
6. Reboot during a maintenance window.
7. Verify SSH/Tailscale, `/health`, and `rs-surface-api.service` after boot.
8. Only then prune stale kernels.

If the node fails to return, use provider rescue mode and the saved boot state
to restore the previous kernel entry or pivot back to the last-good surface.
Carrier kernel updates MUST NOT unmask legacy services or convert Builder,
Warden, or Judge back into standalone processes.

### A/B Release Upgrade

For larger upgrades, use release directories:

```text
/opt/rs-surface/releases/
  surface-20260425T170000/
  surface-20260425T180000/
current -> releases/surface-20260425T180000
previous -> releases/surface-20260425T170000
```

A/B upgrade steps:

1. Upload new release to `/opt/rs-surface/releases/<version>`.
2. Verify hashes and required files.
3. Start new API on a temporary port.
4. Run local health and atlas health probes.
5. Move `current` symlink.
6. Restart normal service.
7. Mark last-good only after post-start health succeeds.

A/B rollback steps:

1. Stop current service.
2. Move `current` to `previous`.
3. Restart service.
4. Enter recovery mode if rollback health fails.

Bootable embedded images use the same logic with `surface-A.squashfs` and
`surface-B.squashfs`.

---

## Minimal Deployment Phases

### Phase 0: Debian-Hosted Surface

Use the existing host OS as the recovery substrate.

```text
Debian
  systemd service: rs-surface-api
  optional rclone mount
  disabled legacy services
```

This is the safest first target for RackNerd and Netcup.

### Phase 1: Compressed Service Bundle

Package `/opt/rs-surface/current` as a compressed artifact and deploy the same
bundle across nodes.

### Phase 2: Embedded Root Surface

Move to read-only root or squashfs image, with local writable overlay for
`/var/lib/rs-surface`.

### Phase 3: Boot Pivot

Only after recovery mode is proven, the node may boot directly into the embedded
surface.

### Phase 4: Layer 0 Kexec Handoff

Use Linux only as a loader. The loader verifies the signed Layer 0 GCL image,
emits a pre-handoff receipt, then uses `kexec` to transfer control to the
nanokernel-owned runtime. This phase may wipe the old userspace assumptions, so
it is gated by provider rescue, rollback image, and Layer 0 health pulse.

---

## Racknerd Initial Profile

Observed on 2026-04-25:

```text
host: racknerd-510bd9c
os: Debian GNU/Linux 13 trixie
cpu: 1 vCPU
memory: 715 MiB
swap: 767 MiB
root disk: 9.1 GiB, about 6.8 GiB free
tailscale: 100.103.54.58
```

RackNerd SHOULD run Phase 0 first as `GCL-Edge`:

```text
disable: warden.service, tardy.service, substrate-index.service, compression-gateway.service
keep: SSH, Tailscale, recovery shell
add: rs-surface-api, rs-surface-heartbeat, optional rclone mount
avoid: local builds, full Research Stack checkout, large local databases
```

`GCL-Edge` means:

1. GCL nanokernel carrier is the primary runtime.
2. Builder/Warden/Judge exist only as topology phases.
3. SSH, Tailscale, and recovery health are preserved above everything else.
4. Full-stack services are not restored on the node.

Recommended Racknerd budgets:

```text
api RSS budget:        32-64 MiB
mount/cache budget:    64 MiB
local state budget:    128 MiB
spool budget:          128 MiB
free disk floor:       1 GiB
```

---

## Netcup Appliance Profile

Observed on 2026-04-27:

```text
host: netcup-router
os: Debian GNU/Linux 13 trixie
kernel: 6.12.74+deb13+1-amd64
cpu: 2 vCPU AMD EPYC-Genoa, AVX-512 available
memory: 3.8 GiB
swap: none
root disk: 125 GiB, about 87 GiB free
tailscale: 100.85.1.50
public ip: 46.232.249.226
kvm: unavailable
```

Netcup SHOULD run as a `mirror` appliance rather than a general shell host:

```text
keep: SSH, Tailscale, qemu-guest-agent, fail2ban, rs-surface-api
disable: tardy.service, openwebui-moe-router.service
stop: topology_node.py, swarm_surface.py
avoid: local builds, local training, unbounded web/router services, large databases
```

The Netcup appliance role is to keep the mirror/relay/storage chart available
while freeing CPU and memory for admitted computation. The surface itself should
remain tiny: health/status/metrics, topology phase receipts, RGFlow admission,
and bounded outbox storage. Compute work is admitted through the surface and
should run as explicit bounded jobs, not as always-on stack services.

Recommended Netcup budgets:

```text
api RSS budget:        32-64 MiB
relay/spool budget:    512 MiB
local state budget:    512 MiB
admitted compute:      up to 2 vCPU / 3 GiB when idle
free disk floor:       10 GiB
```

Netcup does not need `/dev/kvm` to be useful. Its best use is a hosted
topological substrate: the GCL nanokernel exposes primitive operations directly
on the Debian carrier, and AVX-512 accelerates admitted vector transitions.

### EPYC Genoa Topological Device Notes

Netcup's EPYC Genoa carrier deserves special handling. It exposes a small but
high-value vector topology:

```text
cpu topology:       2 vCPU, 1 NUMA node
per-vCPU cache:     32 KiB L1d, 32 KiB L1i, 1 MiB L2, 32 MiB L3
vector width:       AVX-512
useful extensions:  AVX-512 VNNI, BF16, VBMI/VBMI2, VPOPCNTDQ, VAES, VPCLMULQDQ, SHA-NI
carrier limit:      no /dev/kvm
```

Treat this as an `epyc-genoa-vector-substrate`: a topological device optimized
for wide deterministic transforms over compact batches. The appliance surface
should advertise Genoa as primitive substrate capacity without letting vector
jobs become resident daemons.

Kernel-exposed primitives:

```text
attest
compress
rgflow
route
snapshot
vector_filter
delta_batch
merkle_mmr
content_chunk
receipt
```

Preferred admitted work:

1. RGFlow vector filtering over batches.
2. Delta-GCL compression and dictionary scoring.
3. Structural attestation, Merkle/MMR receipt generation, and SHA-heavy scans.
4. Content-defined chunking and mirror deduplication.
5. BF16/VNNI experiments that fit under the appliance memory cap.

Scheduling rules:

1. Keep `rs-surface-api.service` small and latency-stable.
2. Reserve at least 768 MiB for the carrier, SSH/Tailscale, cache, and rollback.
3. Admit at most two CPU slots by default.
4. Prefer short batch jobs with explicit receipts over long-lived compute
   daemons.
5. Pin or shard jobs by vCPU when testing cache-sensitive kernels, because the
   observed L3 slices are not shared across the two exposed vCPUs.
6. Do not require KVM for substrate work; route only VM-specific experiments
   away from Netcup unless `/dev/kvm` appears in a future provider
   configuration.

---

## Acceptance Checks

A node conforms to this spec when:

1. `/health` works without GDrive mounted.
2. `/ws` accepts `health`, `status`, and `mount_status`.
3. The node can enter and leave recovery mode.
4. GDrive mount failure does not break SSH or `/health`.
5. Local persistent state remains below its budget.
6. Legacy heavyweight services are absent or disabled on constrained nodes.
7. An upgrade can be rolled back without manual file editing.

Layer 0 handoff adds stricter acceptance checks:

1. The loader can boot normally and refuse an unsigned Layer 0 image.
2. The loader can `kexec` into a non-production test image and return through
   provider rescue.
3. The Layer 0 image emits a recovery pulse without Linux userspace.
4. The Layer 0 image exposes the primitive descriptor.
5. The old Linux userspace can be discarded without losing node identity,
   last-good receipt, or topology artifacts.

---

## Non-Goals

This surface does not provide:

1. Full Git hosting.
2. Local model training.
3. Local large dataset storage.
4. Local package builds on tiny nodes.
5. Recovery that depends on custom compression or GDrive.

Those functions belong on larger atlas points or in topological storage.
