# Self-Adapting Compute Fabric

A design for the Research Stack that automatically adapts to rapid node changes
(churn, scaling, degradation) without manual intervention.

## Core Principle

> Every node declares what it *is* and what it *can do*. The fabric routes around
> failures, absorbs new capacity instantly, and degrades gracefully.

---

## Architecture Overview

```
                     ┌─────────────────────────────┐
                     │   Orchestrator (Ray Head)    │
                     │  Adaptive Scheduler Engine   │
                     └──────────┬──────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
   ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
   │ Registry  │         │  Health   │         │  Reconfig │
   │ (Capabilities)      │  Monitor  │         │   Engine  │
   └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Node Pool         │
                    │  (Tailscale + k3s)  │
                    │  ┌────┐ ┌────┐ ┌───┘
                    │  │GPU │ │ARM │ │VPS│
                    │  │fox │ │64  │ │edg│
                    │  └────┘ └────┘ └───┘
                    └─────────────────────┘
```

## Components

### 1. Node Bootstrap Agent

A single-shot agent that runs on every node at first boot. Runs once, then exits.

**File**: `4-Infrastructure/shim/node_bootstrap_agent.py`

```python
class NodeBootstrapAgent:
    """One-shot node initialization. Runs on first boot, exits."""
    
    def bootstrap(self):
        1. tailscale_up()              # Join Tailscale mesh
        2. detect_hardware()           # Run device_capability_probe
        3. build_labels()              # Generate k3s labels from capabilities
        4. register_capabilities()     # POST to Capability Registry
        5. join_k3s()                  # k3s agent join with labels
        6. install_nftables_fix()      # If CachyOS/Arch
        7. install_socat_redirects()   # If edge has permanent port maps
        8. report_ready()              # Signal orchestrator
```

**k3s labels generated from probe**:
```
topology.researchstack.io/role=auto:foxtop       # auto-detected role
topology.researchstack.io/tier=gpu_cuda           # compute tier
topology.researchstack.io/gpu=nvidia:rtx4070      # GPU model
topology.researchstack.io/arm64=false              # architecture
topology.researchstack.io/storage-tier=nvme-ssd    # storage class
topology.researchstack.io/network=tailscale        # network fabric
```

**Join script evolves from `join-agent.sh`** to be fully self-detecting:
```bash
# Old: bash join-agent.sh --role foxtop --server ... --token ...
# New: curl -sfL https://bootstrap.researchstack.info | bash
# The script auto-detects everything:
#   - Architecture (x86_64 vs aarch64)
#   - GPU (nvidia-smi, /dev/dri, lspci)
#   - Storage (lsblk)
#   - Memory (free)
#   - Network (tailscale status)
```

### 2. Capability Registry

A small CRUD service that stores what every node can do. Used by the scheduler
to decide where to place work.

**File**: `4-Infrastructure/shim/capability_registry.py`

```python
# Data model
{
    "node_id": "qfox-1.tail-abc123.ts.net",
    "tailscale_ip": "100.88.57.96",
    "k3s_hostname": "qfox-1",
    "hardware": {
        "arch": "x86_64",
        "cpu_cores": 12,
        "memory_mib": 31132,
        "gpus": [
            {"model": "NVIDIA RTX 4070", "vram_mib": 12282, "tier": "gpu_cuda"},
            {"model": "AMD iGPU", "vram_mib": 512, "tier": "gpu_apu"}
        ],
        "storage": [{"mount": "/", "type": "nvme", "size_gib": 1800}],
        "ffmpeg": ["h264_nvenc", "hevc_nvenc", "h264_vaapi"],
        "framebuffer": {"device": "/dev/fb0", "resolution": "3840x2160"}
    },
    "tier": "gpu_cuda",
    "limitations": get_limitations(caps),
    "last_seen": "2026-06-01T04:00:00Z",
    "status": "active"  # active | draining | offline | dead
}
```

**Storage**: The registry can be:
- A Kubernetes ConfigMap (simple, for small clusters)
- Trailbase (Postgres-compatible, already deployed in `media` namespace)
- A Ray in-memory store (if running on the Ray head)

**Auto-registration**: Every node that runs the bootstrap agent registers
itself. Nodes are automatically removed from the active pool if they miss
3 heartbeat cycles (90s with 30s interval).

### 3. Adaptive Scheduler Engine

The core routing engine. Runs on the Ray head (or as a k3s Deployment).

**File**: `4-Infrastructure/shim/adaptive_scheduler.py`

```python
class AdaptiveScheduler:
    """
    Routes compute work to the best available node.
    Adapts to node churn, scaling events, and capability changes.
    """
    
    tiers = OrderedDict([
        ("gpu_cuda",    10),  # Best: discrete NVIDIA
        ("gpu_vaapi",    9),  # Discrete AMD via VA-API
        ("gpu_apu",      8),  # Integrated GPU (shared memory)
        ("cpu_ffmpeg",   7),  # CPU-only encode
        ("batch",        6),  # GitHub Actions async
        ("ethernet",     5),  # virtio-net DMA compute
        ("framebuffer",  4),  # /dev/fb0 display compute
        ("wasm",         3),  # Cloudflare Workers
        ("dsp",          2),  # PipeWire audio DSP
        ("esp32",        1),  # MCU scalar compute
        ("relay",        0),  # Network relay only
    ])
    
    def select_worker(self, requirement: Requirement) -> NodeAssignment:
        """
        Select the best node for a given requirement.
        
        Strategy:
        1. Find nodes that satisfy the requirement's min_tier
        2. Within those, prefer the HIGHEST tier
        3. Within same tier, prefer LOWEST current utilization
        4. If no node satisfies min_tier, FALL BACK to next lower
        5. If nothing available, ENQUEUE for retry
        """
        candidates = self._query_registry(requirement)
        if not candidates:
            return self._fallback(requirement)  # Try lower tier
        best = self._score_and_select(candidates)
        return best
    
    def _fallback(self, req):
        """Graceful degradation: try next tier down."""
        req.min_tier -= 1
        if req.min_tier < 0:
            return NodeAssignment(status="deferred", reason="no capacity")
        return self.select_worker(req)
```

**Ray integration** with the scheduler:

```python
# Instead of @ray.remote(num_gpus=1) which is static:
from adaptive_scheduler import AdaptiveScheduler, Requirement

scheduler = AdaptiveScheduler()

@ray.remote
def adaptive_compute(data, min_tier="gpu_apu"):
    # Scheduler picks the best node AT CALL TIME
    assignment = scheduler.select_worker(
        Requirement(min_tier=min_tier, payload_size=len(data))
    )
    if assignment.status == "deferred":
        raise CapacityError("no nodes available")
    # Execute on the assigned node
    return ray.get(assignment.execute.remote(data))
```

### 4. Health Monitor

Watches the cluster and triggers reconfiguration on changes.

**File**: `4-Infrastructure/shim/health_monitor.py`

```python
class HealthMonitor:
    """
    Watches node health via:
    1. kubelet heartbeats (Kubernetes node conditions)
    2. Tailscale connectivity (tailscale status)
    3. Capability Registry heartbeat
    4. Ray worker heartbeats
    
    Triggers:
    - Node added   → update registry, scale up worker pools
    - Node lost    → drain workloads, update registry, scale down
    - Node degraded → reduce tier assignment, alert
    - Burst detect  → scale up cloud tiers (WASM, BATCH)
    """
    
    HEARTBEAT_INTERVAL = 30  # seconds
    NODE_TIMEOUT = 90        # 3 missed beats → offline
    DRAIN_GRACE = 300        # 5 min drain before force-removal
    
    def tick(self):
        live_nodes = self._check_kubelet_heartbeats()
        ts_nodes = self._check_tailscale()
        registry_nodes = self._check_registry_heartbeats()
        
        for node in live_nodes - registry_nodes:
            self._register_node(node)          # New node!
            self._scale_up_worker_pool(node)
            self._update_routing(node)
            
        for node in registry_nodes - live_nodes:
            self._mark_draining(node)          # Lost node
            self._evacuate_workloads(node)
            self._scale_down_worker_pool(node)
            self._schedule_gc(node, delay=300)  # Remove after 5min
```

### 5. Reconfiguration Engine

Executes changes when nodes come or go.

```python
class ReconfigurationEngine:
    """
    Actions triggered by health monitor events.
    """
    
    def on_node_added(self, node):
        """New capacity available."""
        # 1. Register in Traefik if it exposes an ingress endpoint
        if node.tier in ("gpu_cuda", "gpu_vaapi"):
            self._scale_ray_workers(node, delta=+1)
        
        # 2. If this replaces a dead node, update routing
        if self._is_replacement(node):
            self._update_edge_routing(node)
        
        # 3. Rebalance workloads
        self._rebalance()
    
    def on_node_lost(self, node):
        """Capacity removed."""
        # 1. Mark node as draining
        self._cordon_node(node)
        
        # 2. Scale down Ray workers on that node
        self._scale_ray_workers(node, delta=-1)
        
        # 3. Redistribute workloads to remaining nodes
        pending = self._get_pending_tasks()
        for task in pending:
            self.scheduler.select_worker(task)  # Auto-fallback
        
        # 4. If lost node had special routing, update edge
        if node.roles.intersection({"edge", "auth"}):
            self._failover_edge_routing(node)
    
    def on_burst_detected(self, queue_depth: int):
        """Spike in work. Scale out horizontally."""
        if queue_depth > THRESHOLD_HIGH:
            if self._has_idle_capacity():
                self._activate_idle_workers()
            elif self._can_scale_cloud():
                self._deploy_batch_workers()   # GitHub Actions
                self._deploy_wasm_workers()    # Cloudflare Workers
```

### 6. Edge Routing Adapter

The edge Caddy on racknerd currently forwards to static qfox-1 IPs. This needs
to become dynamic. Options:

**Option A: Traefik as centralized router (aspirational)**
- Edge Caddy forwards all `*.researchstack.info` to Traefik
- Traefik routes based on Ingress resources (already configured)
- When backends move, update Service endpoints
- Requires: making nixos:80 work (install Caddy there)

**Option B: Dynamic DNS-based routing (pragmatic)**
- Edge Caddy uses `consul` or `etcd` for service discovery
- When a node changes, update the registry → Caddy reloads
- Requires: service discovery integration with Caddy

**Option C: NodePort-based with auto-port-allocation (current, hardened)**
- Each service gets a NodePort (managed)
- Edge Caddy forwards subdomains to `any-node:NodePort`
- NodePorts are stable even when pods move
- Add a `port-registry.sh` script that detects NodePort changes and generates
  the Caddy config, then reloads Caddy
- Requires: a way to push the generated config to racknerd

For the immediate term, **Option C** is most practical since the racknerd edge
is already using this pattern. The `port-registry.sh` script automates what's
currently done manually.

---

## Scaling Mechanisms

### Horizontal Scaling (more nodes)

```
Trigger: queue_depth > THRESHOLD_HIGH for 30s
Action:
  1. Health monitor detects burst
  2. Scheduler: try GPU_CUDA → GPU_VAAPI → GPU_APU → ... → RELAY
  3. If all local tiers saturated:
     a. Deploy BATCH workers (GitHub Actions, async)
     b. Deploy WASM workers (Cloudflare Workers, trinary)
  4. If cloud tiers also saturated: ENQUEUE with priority

Rate limit: Max 1 new worker group per 60s per tier
```

### Vertical Scaling (more resources on existing nodes)

```
Trigger: worker utilization > 80% for 5 min
Action:
  1. Check DeviceLimitations: is there headroom?
  2. If yes: increase max_concurrent for this node's tier
  3. If no: trigger horizontal scale instead

Trigger: worker utilization < 10% for 15 min
Action:
  1. Scale down idle worker groups to minReplicas
  2. Deactivate BATCH tier if queue empty
```

### Graceful Degradation

```
When the GPU node (qfox-1) goes offline:
  GPU_CUDA  → unavailable
  GPU_VAAPI → unavailable  
  CPU_FFMPEG → steamdeck takes over (if online)
  BATCH     → GH Actions activated
  ETHERNET  → last resort
  FRAMEBUFFER → any device with a display

The FrameDispatcher tags handle this per-operation:
  STRAND/CROSSING/PIST (braid math) → CPU acceptable
  LUPINE (CUDA) → only on GPU_CUDA tier, fails if unavailable
  VAAPI (encode) → falls back to CPU_FFMPEG
  FLAC (audio) → any tier can do FFT
```

---

## Implementation Plan

### Phase 1: Detection & Registration

| Component | File | Est. |
|-----------|------|------|
| `NodeBootstrapAgent` | `4-Infrastructure/shim/node_bootstrap_agent.py` | 1 session |
| `CapabilityRegistry` (Trailbase backend) | `4-Infrastructure/shim/capability_registry.py` | 1 session |
| Auto-label k3s join script | Update `scripts/join-agent.sh` | Already partial |

### Phase 2: Adaptive Scheduling

| Component | File | Est. |
|-----------|------|------|
| `AdaptiveScheduler` engine | `4-Infrastructure/shim/adaptive_scheduler.py` | 2 sessions |
| `HealthMonitor` with event triggers | `4-Infrastructure/shim/health_monitor.py` | 1 session |
| Ray integration with tier fallback | Update `shim/ray_vcn_bridge.py` | 1 session |

### Phase 3: Reconfiguration & Routing

| Component | File | Est. |
|-----------|------|------|
| `ReconfigurationEngine` | `4-Infrastructure/shim/reconfig_engine.py` | 1 session |
| `port-registry.sh` for dynamic Caddy config | `4-Infrastructure/k3s-flake/scripts/port-registry.sh` | 1 session |
| Edge Caddy auto-reload via k8s | `4-Infrastructure/shim/edge_config_watcher.py` | 2 sessions |

### Phase 4: Cloud Tier Integration

| Component | File | Est. |
|-----------|------|------|
| BATCH tier worker (GH Actions) | `.github/workflows/adaptive-compute.yml` | 1 session |
| WASM tier worker (Cloudflare) | `4-Infrastructure/cloudflare/` update | 1 session |

---

## Verification

```bash
# Simulate node loss
kubectl cordon qfox-1
sleep 60
# Verify: scheduler falls back to next tier
kubectl exec raycluster-head -- ray status | grep "Active\|Pending\|GPU"

# Simulate node join
kubectl uncordon qfox-1
sleep 30 
# Verify: scheduler recognizes new capacity
curl -s http://localhost:30109/api/capabilities/nodes | jq '.nodes | length'

# Simulate burst
python3 -c "
from adaptive_scheduler import AdaptiveScheduler, Requirement
s = AdaptiveScheduler()
for i in range(100):
    req = Requirement(min_tier='gpu_apu', payload_size=1024)
    if i == 50: print('50/100 — mid-burst health check')
    s.select_worker(req)
print('100 tasks dispatched, fallback tiers used:', s.fallback_count)
"
```

## Edge Cases & Failure Modes

| Scenario | Behavior |
|----------|----------|
| **All GPU nodes offline** | Scheduler falls back to CPU_FFMPEG. LUPINE-tagged tasks (CUDA-only) hard-fail |
| **Network partition** | Health monitor sees missed heartbeats. 90s timeout before draining. DRAIN_GRACE prevents flapping |
| **Node flapping** | If node toggles 3 times in 300s, hold off rescheduling for 600s |
| **Tailscale DERP latency** | Heartbeat timeout increased to 45s (DERP adds 200-500ms) |
| **Race: new node appears before old node drains** | Scheduler treats as two separate nodes. Existing work stays on old node, new work goes to new node |
| **Capacity oversubscription** | Scheduler never allocates more than `DeviceLimitations.max_concurrent_tasks` per node |
| **Orchestrator itself crashes** | State is in the Capability Registry (Trailbase/PG), not in memory. On restart, re-read registry and reconcile |
| **Edge VPS goes down entirely** | All subdomains go unresolved. DNS TTL is 5min. Node restart needed — no automatic failover to another edge provider |
