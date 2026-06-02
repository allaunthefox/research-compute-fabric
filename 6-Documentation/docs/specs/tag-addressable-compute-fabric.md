# Tag-Addressable Compute Fabric (TACF)

A ground-up redesign based on your core concepts.

## The Core Idea

**Work is published to a tag. Any node that can handle it picks it up.**
No scheduler. No registry. No health monitor. Nodes self-select.

```
  ┌─────────────────────────────────────────────────────────┐
  │                    Tag Rings (6 channels)                │
  │                                                         │
  │  STRAND ────┬───────┬───────┬───────┬───────┬───────┐   │
  │  CROSSING ──┼───────┼───────┼───────┼───────┼───────┤   │
  │  PIST ──────┼───────┼───────┼───────┼───────┼───────┤   │
  │  LUPINE ────┼───────┼───────┼───────┼───────┼───────┤   │
  │  VAAPI ─────┼───────┼───────┼───────┼───────┼───────┤   │
  │  FLAC ──────┼───────┼───────┼───────┼───────┼───────┤   │
  └─────────────┴───────┴───────┴───────┴───────┴───────┘
                  ▲       ▲       ▲       ▲       ▲
                  │       │       │       │       │
               qfox-1  steamd  neon64  rackn   esp32
               (GPU)   (GPU)   (ARM)   (edge)  (MCU)
```

Each node subscribes to tags it can handle. Work lands on the ring.
Whoever is free and capable picks it up. No central decision.

---

## Concepts Mapped

| Your concept | How it maps |
|-------------|-------------|
| **Copy-if** | Ray ObjectRef is content-addressed. Same payload = same hash = no copy. Work is "copied-if-needed" — if the consumer already has the input (because it computed it earlier), zero transfer. The `CopyIfPattern` from your SPIR-V optimizer becomes the fabric's transport primitive. |
| **HEP as LUT** | Hardware capability is a **tag subscription table**, not a device tree. `{tag: LUPINE, max_concurrent: 12}` — that's the entire capability model. No GPU model strings, no driver versions, no CUDA compute caps. The LUT is a 6-entry array. |
| **Spatial hash as storage** | The node pool IS a spatial hash. Tags are the dimensions. A node's position in capability space is `<tag_0_support, tag_1_support, ..., tag_5_support>`. Finding a node for a tag is O(1) hash lookup, not O(n) scan. Morton code indexes across tiers naturally. |
| **Virtio-net as compute** | Each tag is a **virtio ring**. You write a descriptor (payload ref + tag) into the ring. A consumer reads it, computes, writes back a completion descriptor. The ring IS the scheduler. Your QEMU compute surface concept extends this: the ring can be a network interface, shared memory, or even a physical ring buffer on an FPGA. |
| **Universal compute surface** | ESP32 subscribes to PIST (braid math). RTX 4070 subscribes to LUPINE (CUDA) AND PIST. Both are equally valid compute surfaces — just different LUT entries. `{tag: PIST, max_concurrent: 1}` for ESP32, `{tag: PIST, max_concurrent: 100}` for the RTX 4070. The tag doesn't care. |
| **FrameDispatcher tags** | The 6 tags ARE the fabric. Not an implementation detail — they're the entire addressing scheme. `dispatch(tag, payload)` = `write(tag_ring, payload_ref)`. That's the only API. |
| **DeviceLimitations** | The ONLY policy. Each node says "I can handle N concurrent of tag X". The fabric doesn't decide — the node decides. This is `backpressure` from virtio: if the ring is full, the producer waits. |
| **Mesa over NVIDIA** | LUPINE tag is decoupled from CUDA. On qfox-1, LUPINE runs via Vulkan compute (Mesa NVK). Same LUT entry, different driver. The fabric doesn't care. |
| **Plans need failure modes** | Tags have no "failure." If no node subscribes to LUPINE, the write blocks until one appears. This IS the failure mode — not a crash, not an error, just deferral. |

---

## Architecture

### The Only Primitives

```
1. Tag          — uint8 (0x01-0x06), maps to FrameDispatcher tags
2. Subscription — {node: tag, max_concurrent: N, current_load: M}
3. Descriptor   — {tag, payload_ref, result_ref} (like virtio-ring desc)
4. Ring         — ordered list of pending descriptors per tag
5. LUT          — node's subscription table (6 entries)
```

That's it. Everything else is derived.

### How a Node Joins

```
1. Node boots
2. Tailscale connects (identity established)
3. Node probes itself (what tags can I handle?)
4. Node writes its LUT: {tag: LUPINE, max: 12, load: 0}
5. Node subscribes to those tags' rings
6. Node starts polling for descriptors
7. Node is now part of the fabric — no registration, no registry
```

**No bootstrap agent that "runs once."** The LUT is re-published on every
subscription poll (every 30s). If the node goes silent, its subscriptions
expire. If it reboots with different hardware, its LUT changes automatically.
This handles: reboots, hardware changes, nftables resets, kubelet failures —
all of them, because the node re-probes and re-subscribes.

### How Work Gets Done

```python
# The entire public API:

class TagRing:
    """A single dispatch ring for one tag."""

    def publish(self, payload: bytes) -> ray.ObjectRef:
        """Write work to the ring. Returns a future result."""
        payload_ref = ray.put(payload)  # content-addressed, copy-if
        result_ref = ray.put(None)      # placeholder for result
        self._descriptors.append(Descriptor(
            tag=self.tag,
            payload_ref=payload_ref,
            result_ref=result_ref,
        ))
        return result_ref

    def poll(self, node_id: str) -> list[Descriptor]:
        """Called by subscribers. Returns available work."""
        lim = self._get_limitations(node_id)
        available = []
        while len(available) < lim.max_concurrent - lim.current_load:
            desc = self._descriptors.pop(0) if self._descriptors else None
            if desc is None: break
            available.append(desc)
        return available
```

```python
# How a subscriber consumes work:

class TagSubscriber:
    """Runs on every node. Subscribes to tags the node can handle."""

    def poll_loop(self):
        while True:
            for tag in self._subscribed_tags:
                descriptors = tag_ring.poll(self.node_id)
                for desc in descriptors:
                    # Copy-if: if the payload is already in local Object Store,
                    # ray.get() returns instantly with zero network transfer
                    payload = ray.get(desc.payload_ref)
                    result = self._compute(tag, payload)
                    # Write result back — also content-addressed
                    ray.put(result, desc.result_ref)
                    self._update_load(tag, -1)
            time.sleep(0.1)  # 100ms poll interval
```

**No scheduler.** No reconfiguration engine. No health monitor. The tag ring
holds descriptors. Subscribers pull work when they have capacity. If a node
dies, its in-flight descriptors time out and reappear on the ring (virtio
descriptor timeout pattern). Other nodes pick them up.

### How Tiers Degrade

Each node declares its subscription for each tag:

| Node | STRAND | CROSSING | PIST | LUPINE | VAAPI | FLAC |
|------|--------|----------|------|--------|-------|------|
| qfox-1 (RTX 4070) | 100 | 100 | 100 | **12** | **4** | 1 |
| steamdeck (APU) | 50 | 50 | 50 | 0 | **2** | 1 |
| neon-64gb (ARM) | 20 | 20 | 20 | 0 | 0 | 1 |
| racknerd (VPS) | 1 | 1 | 1 | 0 | 0 | 1 |
| esp32 (MCU) | **1** | 0 | **1** | 0 | 0 | 0 |

When qfox-1 goes offline:
- LUPINE: **no subscribers** → publish blocks until node reappears LUPINE=0
- VAAPI: falls back to steamdeck (only other subscriber, lower capacity)
- STRAND/PIST: redistributed among remaining nodes
- FLAC: any subscriber handles it (all nodes support it)
- The ring for LUPINE just accumulates descriptors. No crash, no error.

**This IS the degradation.** Not a scheduler decision. Just subscribers.

### Copy-if in Practice

```python
# Two tasks, same input:
ref_a = ray.put(big_matrix)  # content hash: 0xabc123

# qfox-1 processes it:
task1 = tag_ring.publish(big_matrix)
result1 = ray.get(task1)  # computed on qfox-1, result in ref

# steamdeck also needs the same matrix (different transform):
task2 = tag_ring.publish(big_matrix)
# ray.put(big_matrix) returns SAME ref 0xabc123
# steamdeck already has it via Ray Object Store gossip
# Zero bytes transferred between nodes for the input
result2 = ray.get(task2)
```

The `copy-if` pattern from your SPIR-V optimizer becomes the fabric's
native data movement primitive. Data moves exactly once — when first
computed. Every subsequent use is a reference.

### The Spatial Hash Node Pool

Instead of a registry:

```python
class SpatialHashPool:
    """
    Nodes are indexed by (tag_support_bits, tier_bits) as a Morton code.
    Finding all nodes that can handle LUPINE is a range scan on the spatial hash.
    """

    def _morton_code(self, subscriptions: dict[int, int]) -> int:
        """Encode a node's subscription profile into a Morton code."""
        code = 0
        for i, (tag, max_concurrent) in enumerate(subscriptions.items()):
            code |= (max_concurrent & 0xFF) << (i * 8)  # interleave
        return code

    def find_nodes(self, tag: int, min_concurrent: int = 1) -> list[str]:
        """O(1) lookup: which nodes can handle this tag?"""
        mask = 0xFF << (tag * 8)
        min_code = min_concurrent << (tag * 8)
        return [n for n in self._nodes
                if (self._morton_codes[n] & mask) >= min_code]
```

The pool is rebuilt from live node subscriptions every poll cycle. No
persistent storage needed. When a node's subscription changes (hardware
upgrade, load change), the hash updates automatically.

---

## Implementation

### The Ring

The tag ring is a Ray actor (one per tag). It's the only persistent state:

```python
@ray.remote
class TagRingActor:
    def __init__(self, tag: int, timeout: float = 30.0):
        self.tag = tag
        self.descriptors: deque[Descriptor] = deque()
        self.in_flight: dict[int, Descriptor] = {}
        self.timeout = timeout

    def publish(self, payload_ref, result_ref) -> int:
        desc_id = id(result_ref)
        self.descriptors.append(Descriptor(
            id=desc_id, payload_ref=payload_ref, result_ref=result_ref
        ))
        return desc_id

    def poll(self, node_id: str) -> list[Descriptor]:
        # Check for timed-out in-flight descriptors (virtio timeout)
        self._reap_stale()
        # Return available work up to node's limit
        limit = self._get_node_limit(node_id)
        available = []
        while len(available) < limit:
            if not self.descriptors: break
            desc = self.descriptors.popleft()
            self.in_flight[desc.id] = desc
            desc.started_at = time.monotonic()
            available.append(desc)
        return available

    def complete(self, desc_id: int):
        self.in_flight.pop(desc_id, None)

    def _reap_stale(self):
        now = time.monotonic()
        stale = [did for did, d in self.in_flight.items()
                 if now - d.started_at > self.timeout]
        for did in stale:
            desc = self.in_flight.pop(did)
            self.descriptors.appendleft(desc)  # re-queue for retry
```

### The Subscriber (runs on every node)

```python
class TagSubscriber:
    def __init__(self, node_id: str):
        self.node_id = node_id
        # Self-probe: what tags can THIS node handle?
        self.subscriptions = self._probe_hardware()
        # Register with tag rings
        for tag in self.subscriptions:
            tag_ring = TagRingActor.remote(tag)  # or get existing ref
            # Nothing else needed — polling discovers work

    def _probe_hardware(self):
        """Build subscription table from local hardware. Pure LUT."""
        caps = probe_device()  # existing device_capability_probe.py
        subs = {}
        if caps.tier >= ComputeTier.GPU_CUDA:
            subs[Tag.LUPINE] = caps.limitations.max_concurrent
        if caps.has_vaapi:
            subs[Tag.VAAPI] = caps.limitations.max_concurrent
        subs[Tag.STRAND] = max(1, caps.cpu_cores // 2)
        subs[Tag.CROSSING] = subs[Tag.STRAND]
        subs[Tag.PIST] = subs[Tag.STRAND]
        subs[Tag.FLAC] = 1  # any node can do FFT
        return subs

    def poll_loop(self):
        while True:
            for tag in self.subscriptions:
                ring = get_tag_ring(tag)
                descriptors = ray.get(ring.poll.remote(self.node_id))
                for desc in descriptors:
                    self._process(tag, desc)
            time.sleep(0.1)

    def _process(self, tag: int, desc: Descriptor):
        payload = ray.get(desc.payload_ref)
        result = FRAMEDISPATCHER.dispatch(tag, 0, 0, payload)
        ray.put(result, desc.result_ref)
        ring = get_tag_ring(tag)
        ray.get(ring.complete.remote(desc.id))
```

### The Public API (unchanged from existing FrameDispatcher)

```python
# Same API you already have — just the transport changes:

class FrameDispatcher:
    def dispatch(self, tag: int, flags: int, seq: int, payload: bytes) -> bytes:
        ring = get_tag_ring(tag)
        payload_ref = ray.put(payload)
        result_ref = ray.put(None)
        desc_id = ray.get(ring.publish.remote(payload_ref, result_ref))
        result = ray.get(result_ref, timeout=30.0)
        return bytes(result)
```

The existing `FrameDispatcher.dispatch(tag, flags, seq, payload)` signature
doesn't change. Only the transport changes: from `self.backends[tag].compute()`
to `ring.publish()`. This is exactly your principle: **Ray replaces transport,
not dispatch logic.**

### The Subscriber Daemon (systemd)

```ini
[Unit]
Description=TACF Subscriber — tag polling loop for $(hostname)
After=network.target tailscaled.service
Wants=tailscaled.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/tacf/subscriber.py --node-id $(hostname)
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

This runs on every node. It's the watchdog, the bootstrap agent, and the
compute worker all in one. It:
1. Probes hardware every 30s (handles GPU changes, reboot, etc.)
2. Subscribes to appropriate tag rings
3. Polls for work
4. Executes via FrameDispatcher
5. Reports back via Ray ObjectRef
6. If the process dies, systemd restarts it in 5s

**This replaces: NodeBootstrapAgent, CapabilityRegistry, HealthMonitor,
ReconfigurationEngine, and AdaptiveScheduler.** All of them.

---

## What This Unlocks

| Device | Tags | Why It Works |
|--------|------|-------------|
| **ESP32** | STRAND, PIST | ESP32 does Q0_16 scalar. Braid math is Q0_16. Payloads are 512B. Subscribes with `max_concurrent=1`. When it polls, it gets one descriptor, computes, writes back. This is the ultimate fallback. |
| **QEMU VM** | ETHERNET, FRAMEBUFFER | Virtio-net ring IS the compute surface. VM subscribes to ETHERNET. Packets written to the ring IS computation. FrameBuffer compute (ARGB8888) works on any VM with a display. |
| **GH Actions runner** | STRAND | Can't do GPU, can't do real-time. But CAN do batch braid math. Runner polls when it starts a workflow, processes queued descriptors, publishes results. Poll interval = workflow trigger. |
| **Cloudflare Worker** | PIST | 10ms CPU, 512B payload, trinary VM. Subscribes with `max_concurrent=1`. Processes one PIST descriptor per invocation. Result is `ray.put()` to a persistent ObjectRef. |
| **FPGA (Tang Nano 9K)** | PIST | Currently builds bitstreams. With a UART or SPI transport, it can subscribe to PIST. Payloads go in, braid-crossing results come out. The LUT is the bitstream. |

---

## Comparison

| Aspect | Previous design | TACF |
|--------|---------------|------|
| Components | 6 (Bootstrap, Registry, Scheduler, Monitor, Reconfig, Edge) | **1** (Subscriber daemon) |
| State | Trailbase DB + k8s labels | **Ray ObjectRefs + in-memory rings** |
| Scheduling | Centralized scheduler picks node | **Nodes self-select via polling** |
| Node join | One-shot agent + registration | **30s probe loop, automatic** |
| Node loss detection | Health monitor heartbeat | **Ring descriptor timeout** |
| Edge routing | port-registry.sh + privileged pod | **Same — this is the one unsolved part** |
| Failure mode | Complex cascade logic | **Descriptor timeout + re-queue** |
| MVP | 3 files, 1 session | **1 file: subscriber.py, existing FrameDispatcher** |
| Implementation | 4 phases, 8 sessions | **1 subscriber daemon + 1 TagRingRayActor** |
