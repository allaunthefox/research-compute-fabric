# Research Stack Wiki

> Comprehensive architecture reference — May 30, 2026

The Research Stack is a capability-adaptive compute fabric that turns every device in a Tailscale mesh — from NVIDIA GPUs to ESP32 microcontrollers — into a unified distributed compute cluster. Formal proofs live in Lean 4; Python shims handle I/O at the boundary; Ray schedules work across the mesh; and a custom VCN compression pipeline achieves [**50× bandwidth reduction**](#4-vcn-pipeline) for cross-node data transfers.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Compute Tiers](#2-compute-tiers)
3. [Infrastructure](#3-infrastructure)
4. [VCN Pipeline](#4-vcn-pipeline)
5. [Ray Integration](#5-ray-integration)
6. [Device Capability Probe](#6-device-capability-probe)
7. [Compute Surfaces](#7-compute-surfaces)
8. [Mesh Networking Plan](#8-mesh-networking-plan)
9. [Formal Verification](#9-formal-verification)
10. [Key Files](#10-key-files)

---

## 1. Architecture Overview

The stack is organized as **5 layers**, from physical connectivity up to application logic:

```
┌─────────────────────────────────────────────────────────────┐
│  Application Layer                                            │
│  Braid search, AlphaProof, RG tests, PIST classification     │
├─────────────────────────────────────────────────────────────┤
│  Ray Scheduler                                                │
│  Distributed task scheduling, ObjectRef transport             │
│  @ray.remote, ray.put(), ray.get()                            │
├─────────────────────────────────────────────────────────────┤
│  VCN Pipeline (compression)                                   │
│  Delta+RLE → RS ECC → ChaCha20 → H.264 → MKV               │
│  50× bandwidth reduction over raw data                        │
├─────────────────────────────────────────────────────────────┤
│  FrameDispatcher (routing)                                    │
│  TAG_STRAND → VCNBraidBackend                                 │
│  TAG_CROSSING → VCNBraidBackend                               │
│  TAG_PIST → VCNBraidBackend                                   │
│  TAG_LUPINE → CUDABackend                                     │
│  TAG_VAAPI → VAAPIBackend (AMD/Intel VA-API)                  │
│  TAG_FLAC → FLACBackend (PipeWire/FLAC DSP)                   │
├─────────────────────────────────────────────────────────────┤
│  Compute Surfaces (execution)                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ GPU_CUDA │ │ GPU_VAAPI│ │ ETHERNET │ │FRAMEBUFF │       │
│  │ NVENC    │ │ VAAPI    │ │ virtio   │ │ /dev/fb0 │       │
│  │ 12GB VRAM│ │ shared   │ │ TX/RX    │ │ DMA      │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  Tailscale Mesh (connectivity)                                │
│  WireGuard encryption, DERP relay fallback                    │
│  Direct P2P when possible, relay when NAT'd                  │
│  MagicDNS, subnet routing, exit nodes                         │
├─────────────────────────────────────────────────────────────┤
│  Physical Network                                             │
│  Ethernet, WiFi, 4G/5G, satellite, mesh radio                │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** The mesh networking layer doesn't just provide connectivity — it provides a *capability-adaptive compute fabric*. Every device in the Tailscale mesh is a potential compute node. The capability probe determines what each device can do, and Ray schedules work accordingly.

---

## 2. Compute Tiers

Every device in the cluster is classified into a compute tier by `device_capability_probe.py`. Tiers are ordered by decreasing capability:

| Tier | Level | Description | Encoder / Surface | Ray Resource |
|------|-------|-------------|-------------------|--------------|
| `GPU_CUDA` | 10 | NVIDIA discrete + CUDA | NVENC H.264 | `num_gpus=1` |
| `GPU_VAAPI` | 9 | AMD/Intel discrete + VA-API | VA-API H.264 | `num_gpus=1` (VAAPI) |
| `GPU_APU` | 8 | AMD integrated, shared memory | VAAPI (yuvj420p) | `resources={"APU": 1}` |
| `CPU_FFMPEG` | 7 | No GPU, software encode | libx264/libx265 | `num_cpus=N` |
| `BATCH` | 6 | GitHub Actions runner, 1500 min/month (reserve 500 for CI) | libx264 | ephemeral, `batch_compute.yml` |
| `ETHERNET` | 5 | virtio-net PistPacket DMA | TX/RX ring descriptors | `resources={"ethernet": 1}` |
| `FRAMEBUFFER` | 4 | `/dev/fb0` DMA backplane only | ARGB8888 pixel words | `resources={"framebuffer": 1}` |
| `WASM` | 3 | Cloudflare Workers, 512 B payload, 8 ms CPU | Rust WASM, `4-Infrastructure/cloudflare/` | N/A |
| `DSP` | 2 | PipeWire/FLAC DSP, 2048-sample FFT | FLAC encode/decode | N/A |
| `ESP32` | 2 | MCU, Q0_16 scalar in FreeRTOS idle hook | 520 KB SRAM | N/A |
| `RELAY` | 1 | Network only, no compute | data forwarding | N/A |
| `OFFLINE` | 0 | Unreachable | — | — |

**Design principle:** No `Float` in compute paths. All computation uses fixed-point arithmetic — `Q0_16` (16-bit pure fraction, range [-1, 1]) as default, `Q16_16` (32-bit mixed) only when integer range or hardware register width demands it.

### Device Limitations

Each compute tier has hard resource constraints captured by the `DeviceLimitations` dataclass. The `device_function` headroom field reserves capacity so the host device remains responsive while contributing to the cluster.

```python
@dataclass
class DeviceLimitations:
    tier: ComputeTier
    max_payload_bytes: int       # Per-frame hard limit
    max_cpu_ms: int              # Wall-clock budget per dispatch
    max_memory_bytes: int        # Working-set ceiling
    headroom_fraction: float     # Fraction reserved for device function (0.0–1.0)
    requires_gpu: bool           # True only for GPU_CUDA, GPU_VAAPI
    supports_pipewire: bool      # True for DSP tier
```

| Tier | `max_payload` | `max_cpu_ms` | `max_memory` | `headroom` | Notes |
|------|--------------|-------------|-------------|-----------|-------|
| `GPU_CUDA` | 256 MB | 5000 | VRAM (12 GB) | 0.10 | NVENC + CUDA kernels |
| `GPU_VAAPI` | 128 MB | 5000 | VRAM / shared | 0.10 | VA-API encode/decode |
| `GPU_APU` | 64 MB | 3000 | shared | 0.15 | Higher headroom, shared memory |
| `CPU_FFMPEG` | 32 MB | 10000 | system RAM | 0.20 | Software encode is slow |
| `BATCH` | 16 MB | 60000 | ephemeral | 0.00 | GitHub Actions, no host device |
| `ETHERNET` | 9000 B (jumbo) | 1 | ring descriptors | 0.05 | MTU-limited, near-zero CPU |
| `FRAMEBUFFER` | 8.29 MB | 2 | mmap region | 0.05 | 1080p ARGB8888 frame |
| `WASM` | 512 B | 8 | 128 MB | 0.00 | Cloudflare Workers hard limits |
| `DSP` | 8192 B | 50 | PipeWire buffer | 0.20 | 2048-sample FFT, real-time priority |
| `ESP32` | 2 B (Q0_16) | 1 | 520 KB SRAM | 0.30 | Idle-hook only, high headroom |

---

## 3. Infrastructure

### k3s Cluster

| Node | Tailscale IP | Role | Hardware | Status |
|------|-------------|------|----------|--------|
| `nixos` (control-plane) | `100.102.173.61` | k3s server, Ray GCS head, KubeRay operator | AMD GPU, 459 GB NVMe | Active |
| `qfox-1` (GPU worker) | `100.88.57.96` | k3s agent, Ray GPU+CPU workers, NVENC | RTX 4070 SUPER (12 GB VRAM), AMD iGPU | Active |
| `racknerd` (framebuffer) | `100.101.247.127` | k3s agent, lightweight compute | 2 vCPU, 9.1 GB disk | Active |
| `neon-64gb` | `100.64.19.78` | Ray ARM64 worker | 18-core ARM64 | Pending k3s fix |
| `steamdeck` | `100.85.244.73` | Edge GPU worker | RDNA 2 iGPU | Onboarded |

### Tailscale Mesh

All inter-node communication flows over **WireGuard** tunnels managed by Tailscale:

- **Direct P2P** when NAT traversal succeeds (< 10 ms RTT)
- **DERP relay** fallback when direct fails (~129 ms per hop added)
- **Post-quantum Kyber768** key exchange
- **MagicDNS** for node discovery
- **Subnet routing** for pod-to-pod networking across nodes

### KubeRay Operator

The KubeRay operator runs on the `nixos` control-plane and manages Ray clusters as Kubernetes custom resources:

```yaml
# 4-Infrastructure/kube/raycluster.yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: raycluster
  namespace: ray
spec:
  rayVersion: "2.41.0.dev0"
  headGroupSpec:
    # Binds to qfox-1, 2-4 CPU, 4-8 Gi memory
    # Exposes GCS (6379), Dashboard (8265), Client (10001), Serve (8000)
  workerGroupSpecs:
    - groupName: cpu-workers   # 1-4 replicas, 4-8 CPU each
    - groupName: gpu-worker    # 0-1 replicas, 1 GPU, 8-16 Gi memory
```

All Ray pods mount `/dev/dri` for GPU access and use `/dev/shm` (2–4 Gi) for shared memory IPC.

---

## 4. VCN Pipeline

The **Video Compute Network (VCN)** pipeline treats video encoding hardware as a computation device. Raw braid data is packed into YUV420 frames, compressed through a 5-stage pipeline, and shipped as MKV containers.

### Pipeline Stages

| Stage | Operation | Compression | Output Size (per 1 MB input) |
|-------|-----------|-------------|------------------------------|
| 1 | **Delta + RLE** | Temporal delta encoding + run-length | ~200 KB (5×) |
| 2 | **Reed-Solomon ECC** | Error correction (parity overhead) | ~250 KB |
| 3 | **ChaCha20** | Encryption (size-preserving) | ~250 KB |
| 4 | **H.264 encode** | Hardware video compression (NVENC/VAAPI/libx264) | ~20 KB (50×) |
| 5 | **MKV container** | Matroska muxing | ~22 KB |

**Result:** 1000 strands = 22 MB over mesh (1.8 seconds at 100 Mbps) vs 1000 MB raw (80 seconds).

### Key Scripts

| File | Purpose |
|------|---------|
| `braid_vcn_encoder.py` | End-to-end pipeline: braid data → Delta+RLE → Q16_16 → RS ECC → ChaCha20 → H.264 → MKV |
| `vcn_compute_substrate.py` | Hardware encoder abstraction: packs Q16_16 data into YUV420 frames, drives NVENC/VAAPI/libx264 via FFmpeg, extracts results from encoded bitstream |

### Frame Format

```
┌──────────────────────────────────────────┐
│ SIGNATURE_HEADER (8 bytes): "RDMAVCN\0"  │
├──────────────────────────────────────────┤
│ Sequence number (4 bytes)                │
│ Payload length (4 bytes)                 │
│ CRC32 witness hash (4 bytes)             │
│ Version (4 bytes)                        │
├──────────────────────────────────────────┤
│ Q16_16 fixed-point payload               │
│ (packed into YUV420 macroblocks)         │
└──────────────────────────────────────────┘
```

---

## 5. Ray Integration

### `ray_vcn_bridge.py` — FrameDispatcher over Ray

Replaces `GPUNodeConnection`'s TCP/MKV transport with Ray ObjectRef transport. The FrameDispatcher, backends, and frame protocol are unchanged — only the wire between daemon and GPU node changes.

**Two usage modes:**

```python
# Mode 1: Drop-in replacement for GPUNodeConnection
from ray_vcn_bridge import RayGPUNodeConnection
gpu = RayGPUNodeConnection()
reply = gpu.send_frame(TAG_STRAND, payload)

# Mode 2: Standalone Ray actor
import ray
ray.init("auto")
bridge = RayVCNBridge.remote()
reply_ref = bridge.dispatch_frame.remote(TAG_STRAND, payload)
reply = ray.get(reply_ref)
```

### Architecture

| Component | Role |
|-----------|------|
| `RayGPUNodeConnection` | Drop-in for `GPUNodeConnection`. Wraps Ray actor calls as sync `send_frame()` |
| `RayVCNBridge` | `@ray.remote` actor hosting a `FrameDispatcher` with GPU + Braid backends |
| `SyncBraidWrapper` | Wraps a Ray `BraidBackend` actor to satisfy `FrameDispatcher`'s sync interface |
| `SyncCUDAWrapper` | Wraps a Ray `CUDABackend` actor to satisfy `FrameDispatcher`'s sync interface |
| `SyncVAAPIWrapper` | Wraps a Ray `VAAPIBackend` actor to satisfy `FrameDispatcher`'s sync interface |
| `SyncFLACWrapper` | Wraps a Ray `FLACBackend` actor to satisfy `FrameDispatcher`'s sync interface |

**Design principle:** Ray replaces Unix socket IPC + TCP transport + MKV encode/decode. `ObjectRef` replaces MKV bytes over TCP (zero-copy on same node). FAMM gate check happens *before* `ray.put()`.

### Data Flow

```
send_frame(TAG, payload)
    │
    ▼
FAMM gate check (pre-dispatch)
    │
    ▼
ray.put(payload)  →  ObjectRef (zero-copy on same node)
    │
    ▼
ray.get(dispatch_actor.dispatch_frame.remote(TAG, ref))
    │
    ├── TAG_STRAND / TAG_CROSSING / TAG_PIST → BraidBackend.compute()
    ├── TAG_LUPINE → CUDABackend.compute()
    ├── TAG_VAAPI → VAAPIBackend.compute()
    └── TAG_FLAC → FLACBackend.compute()
    │
    ▼
ObjectRef(result)  →  ray.get()  →  bytes
```

---

## 6. Device Capability Probe

`device_capability_probe.py` scans DRM render nodes, FFmpeg encoders, framebuffer devices, and network connectivity to classify each device into the correct compute tier.

### Detection Logic

| Check | Command / Path | Determines |
|-------|---------------|------------|
| NVIDIA GPU | `/dev/dri/renderD*` + vendor `0x10de` + `nvidia-smi` | `GPU_CUDA` |
| AMD discrete GPU | `/dev/dri/renderD*` + vendor `0x1002` + `is_discrete=True` | `GPU_VAAPI` |
| AMD APU / iGPU | `/dev/dri/renderD*` + vendor `0x1002` + `is_discrete=False` | `GPU_APU` |
| FFmpeg encoders | `ffmpeg -encoders` → `libx264`, `h264_nvenc`, `h264_vaapi` | `CPU_FFMPEG` (if no GPU) |
| Framebuffer | `/dev/fb0` exists + readable | `FRAMEBUFFER` (fallback) |
| virtio-net | `/sys/class/net/*/device/driver` contains `virtio` | `ETHERNET` capability flag |
| Network reachability | Ping / SSH / kubectl | `RELAY` or `OFFLINE` |

### Multi-GPU Support

The probe detects **multiple GPUs per node** and classifies each independently:

- **NVIDIA + AMD coexistence** (e.g., RTX 4070 SUPER + AMD iGPU on qfox-1)
- **APU vs dGPU classification** via VRAM detection: discrete GPUs report VRAM > 0; APUs report `vram_mb=0` with shared memory
- Each GPU gets its own `GPUDevice` dataclass with render node path, vendor, device ID, VA-API profiles

### Output

```python
@dataclass
class DeviceCapabilities:
    hostname: str
    tier: ComputeTier
    gpus: List[GPUDevice]
    framebuffer: Optional[FramebufferDevice]
    has_ffmpeg: bool
    ffmpeg_encoders: List[str]
    preferred_encoder: str         # "h264_nvenc", "h264_vaapi", "libx264"
    preferred_pixel_format: str    # "yuv420p", "yuvj420p" (APU)
    ray_resources: dict            # Custom Ray resource labels
    has_virtio_net: bool
```

---

## 7. Compute Surfaces

### GPU (NVENC / VA-API)

| Property | NVIDIA (NVENC) | AMD (VA-API) |
|----------|---------------|--------------|
| Encoder | `h264_nvenc` | `h264_vaapi` |
| Pixel format | `yuv420p` | `yuvj420p` (APU), `yuv420p` (dGPU) |
| VRAM | Dedicated (12 GB on RTX 4070 SUPER) | Shared (APU) or dedicated |
| Throughput | ~500 fps @ 1080p | ~200 fps @ 1080p |
| Use case | Primary compute, NVENC encode, CUDA kernels | Secondary encode, bandwidth-optimized tasks |

### VA-API Backend (`VAAPIBackend`)

The `VAAPIBackend` class in `vcn_lupine_bridge.py` handles `TAG_VAAPI` (0x05) frames on AMD and Intel GPUs via the VA-API hardware acceleration interface:

- Dispatches through `FrameDispatcher` when the device probe detects a VA-API-capable render node (`/dev/dri/renderD*` with vendor `0x1002` or `0x8086`)
- Supports hardware H.264 encode/decode, JPEG decode, and VPP (video post-processing)
- Pixel format: `yuv420p` (discrete), `yuvj420p` (APU shared memory)
- Replaces `CUDABackend` path when no NVIDIA GPU is present

### FLAC DSP Backend (`FLACBackend`)

The `FLACBackend` class in `vcn_lupine_bridge.py` handles `TAG_FLAC` (0x06) frames through a PipeWire/FLAC DSP pipeline:

- Routes audio-domain compute through PipeWire's real-time graph
- Performs 2048-sample FFT for spectral analysis and transformation
- FLAC encode/decode for lossless audio data compression in the VCN pipeline
- Runs at DSP(2) tier with real-time scheduling priority
- Useful for acoustic sensor processing, waveform analysis, and audio-domain braiding operations

### Ethernet (virtio-net PistPacket DMA)

The **PistPacket** protocol treats Ethernet as a computation backplane:

- Guest writes structured compute packets to the **virtio-net TX ring** (lock-free producer)
- Host QEMU/vhost-user performs **matrix transforms** on the payload
- Results return via the **virtio-net RX ring** (lock-free consumer)
- NIC offload engines (CRC32, Toeplitz RSS) serve as hardware-accelerated algebraic operators

```c
struct __attribute__((packed)) pist_packet {
    uint8_t  dest_mac[6];       // Target transform operator ID
    uint8_t  src_mac[6];        // Provenance chain head
    uint16_t ethertype;         // 0x88B5 (PIST-over-Ethernet)
    uint64_t computation_id;    // Dataflow graph instance
    uint64_t step_index;        // Sequential transition step
    uint32_t coordinate_path;   // QuadTree addressing
    uint32_t witness_hash;      // CRC32 witness signature
    uint32_t payload_len;       // Q16_16 payload length
    uint8_t  payload[];         // Saturating Q16_16 fixed-point data
};
```

### Framebuffer (`/dev/fb0` zero-copy mmap)

`qemu_framebuffer_packer.py` uses the virtual graphics framebuffer as a DMA computation backplane:

- **ARGB8888** (32-bit): 1 pixel = 1 Q16_16 scalar (100% density mapping)
- **Zero-copy** via `mmap()` on `/dev/fb0`
- **8.29 MB/frame** at 1080p resolution
- Machine-readable `FramebufferReceipt` for every DMA packet
- CRC32 witness hash for integrity verification

### ESP32 (Q0_16 FreeRTOS idle Hook)

The lowest real compute tier — a microcontroller contributing scalars during idle cycles:

- **Q0_16** scalar computation in the FreeRTOS idle hook
- 520 KB SRAM, 240 MHz Xtensa LX6
- Contributes dimensionless quantities (confidence scores, phase angles)
- Connected to the mesh via WiFi → Tailscale

---

## 8. Mesh Networking Plan

### Ray over Tailscale

All Ray nodes communicate via Tailscale IPs. The Ray GCS (Global Control Store) head binds to the nixos Tailscale IP (`100.102.173.61`), and all workers connect through WireGuard tunnels.

```
qfox-1 ─── WireGuard ─── nixos ─── WireGuard ─── racknerd
   │            │            │            │            │
   └── WireGuard ── neon ──── WireGuard ── steamdeck ──┘
                  │
              DERP relay
              (fallback)
```

### Latency-Aware Scheduling

Latency classes from `RouteCost.lean` drive placement decisions:

| Class | RTT | Tailscale Path | FPGA Voltage | Placement Strategy |
|-------|-----|----------------|--------------|-------------------|
| `LOCAL` | < 1 ms | Same node | 1.2V | Preferred — zero network overhead |
| `NEAR` | < 10 ms | Direct P2P | 1.0V | Preferred — WireGuard direct |
| `FAR` | < 100 ms | Multi-hop | 0.8V | Acceptable — may need VCN compression |
| `DERP` | < 1 s | Relay | 0.6V | Penalized — 129 ms relay overhead |
| `OFFLINE` | ≥ 1 s | Unreachable | 0V | Excluded |

```python
def get_placement(caps: DeviceCapabilities, latency_class: str) -> dict:
    base = get_ray_placement_strategy(caps)
    if latency_class == "DERP":
        base["resources"]["derp_penalty"] = 1   # Penalize relay nodes
    if latency_class in ("LOCAL", "NEAR"):
        base["resources"]["direct_link"] = 1     # Prefer direct P2P
    return base
```

### VCN Compression for Cross-Node Transfers

The 50× VCN compression makes cross-mesh data transfer bandwidth-negligible. DERP relay adds ~129 ms per hop, but the compressed payloads mean **latency, not bandwidth, is the bottleneck**.

### Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Ray over Tailscale | 🟡 Partial | Ray cluster on qfox-1, KubeRay operator on nixos, nftables fix done. Pending: Ray head on Tailscale IP, worker Tailscale connectivity |
| 2. Multi-tier scheduling | 🟡 Partial | Capability probe, framebuffer fallback, Ethernet tier done. Pending: mesh-aware placement, VCN for ObjectRef transfers |
| 3. Framebuffer + Ethernet | ⬜ Planned | Host-side framebuffer reader, PistPacket transform engine, Ray actors for both surfaces |
| 4. Edge devices | ⬜ Planned | ESP32 firmware (Q0_16), 1-Wire sensor integration, Ray relay for data collection |

---

## 9. Formal Verification

The Lean 4 formalization lives in `0-Core-Formalism/lean/Semantics/`. As of May 30, 2026:

| Metric | Count |
|--------|-------|
| Lean files (Semantics) | 50+ |
| Files with `sorry` | ~37 (across Semantics + external/OTOM) |
| Total `sorry` occurrences | 109 |

### Key Formal Modules

| Module | File | Purpose |
|--------|------|---------|
| **BraidSpherionBridge** | `Semantics/BraidSpherionBridge.lean` | Bridge between braid group algebra and spherion geometry (9 sorries) |
| **BraidDiatCodec** | `Semantics/BraidDiatCodec.lean` | Diatonic codec for braid data encoding (2 sorries) |
| **BraidVCNBridge** | `Semantics/BraidVCNBridge.lean` | Formal bridge between braid structures and VCN pipeline |
| **FAMM** | `Semantics/HCMMR/Kernels/FAMMScarMemory.lean` | Force-Modified Arrhenius Model — scar memory kernel |
| **RouteCost** | `Semantics/RouteCost.lean` | Latency class definitions (LOCAL/NEAR/FAR/DERP/OFFLINE) with FPGA voltage mapping |
| **MeshRouting** | `Semantics/MeshRouting.lean` | Mesh-aware routing formalization |
| **Q16_16Numerics** | `Semantics/Q16_16Numerics.lean` | Fixed-point arithmetic — the foundation of all compute |
| **Bind** | `Semantics/Bind.lean` | Core `bind` primitive — the one axiom (3 sorries) |
| **LadderBraidAlgebra** | `Semantics/LadderBraidAlgebra.lean` | Algebraic structure of ladder braids |
| **CrossModalCompression** | `Semantics/CrossModalCompression.lean` | Formal model of cross-modal data compression |

### Verification Rules

- **No bare `sorry`** in committed code — every `sorry` must have a `TODO(lean-port)` comment
- **No `Float` in compute paths** — `Q0_16` (default) or `Q16_16` (when range demands)
- **Lean is the source of truth** — Python shims handle I/O only; all decision logic belongs in Lean
- **`#eval` witnesses** required for computational claims

---

## 10. Key Files

### Infrastructure Shims (`4-Infrastructure/shim/`)

| File | Description |
|------|-------------|
| `device_capability_probe.py` | Multi-GPU detection, tier classification (GPU_CUDA → OFFLINE), Ray resource mapping |
| `ray_vcn_bridge.py` | FrameDispatcher over Ray — `RayGPUNodeConnection` drop-in + `RayVCNBridge` actor |
| `braid_vcn_encoder.py` | End-to-end VCN pipeline: braid → Delta+RLE → RS ECC → ChaCha20 → H.264 → MKV |
| `vcn_compute_substrate.py` | Hardware encoder abstraction: packs Q16_16 into YUV420 frames, drives NVENC/VAAPI/libx264 |
| `qemu_framebuffer_packer.py` | Framebuffer DMA backplane: zero-copy mmap on `/dev/fb0`, ARGB8888 Q16_16 packing |
| `vcn_lupine_bridge.py` | Tag-based frame dispatcher with BraidBackend, CUDABackend, VAAPIBackend, FLACBackend |

### Cloudflare Workers (`4-Infrastructure/cloudflare/`)

| File | Description |
|------|-------------|
| `src/lib.rs` | Rust WASM trinary VM (7 ops, 32 trits) — SET/ADD/SUB/SHIFT/MERGE/PROJECT/WEIGHT |
| `src/index.js` | Worker entry point — POST only, JSON + binary protocols, `initSync` WASM load |
| `wrangler.toml` | Worker configuration, account `47b5018a9ddab552d535c8e046a6bc7e` |
| **Deployed** | `https://wasm-compute-edge.researchstack.workers.dev` — Q0_16 scalar compute floor |

### GitHub Actions (`.github/workflows/`)

| File | Description |
|------|-------------|
| `batch_compute.yml` | Batch compute workflow — 1500 min/month budget (500 reserved for CI), ephemeral runners |

### Kubernetes / Ray (`4-Infrastructure/kube/`)

| File | Description |
|------|-------------|
| `raycluster.yaml` | KubeRay RayCluster CRD — head on qfox-1, CPU workers (1-4), GPU worker (0-1) |

### Documentation (`6-Documentation/`)

| File | Description |
|------|-------------|
| `docs/mesh-networking-over-ray-plan.md` | Full mesh networking architecture plan — 4 implementation phases |
| `docs/specs/virtio_net_compute_fabric_spec.md` | Virtio-net DMA compute fabric & PistPacket specification |
| `docs/WIKI.md` | This file — comprehensive architecture wiki |

### Formal Verification (`0-Core-Formalism/lean/Semantics/`)

| File | Description |
|------|-------------|
| `Semantics/Q16_16Numerics.lean` | Fixed-point arithmetic foundation |
| `Semantics/RouteCost.lean` | Latency class definitions with FPGA voltage mapping |
| `Semantics/MeshRouting.lean` | Mesh-aware routing formalization |
| `Semantics/BraidVCNBridge.lean` | Formal bridge between braid algebra and VCN |
| `Semantics/BraidSpherionBridge.lean` | Braid group ↔ spherion geometry bridge |
| `Semantics/BraidDiatCodec.lean` | Diatonic codec for braid encoding |
| `Semantics/HCMMR/Kernels/FAMMScarMemory.lean` | FAMM scar memory kernel |
| `Semantics/Bind.lean` | Core bind primitive — the one axiom |

### Storage (`4-Infrastructure/storage/`)

| File | Description |
|------|-------------|
| `restic/backup.sh` | Deduplicated encrypted snapshots to Garage S3 |
| `garage/garage-node-bootstrap.sh` | Bootstrap a new Garage storage node in the mesh |
| `garage/garage-cluster-init.sh` | Connect Garage nodes, set replication factor |

---

## Quick Reference

### Build Commands

```bash
# Lean build (full)
cd 0-Core-Formalism/lean/Semantics && lake build

# Lean build (targeted)
cd 0-Core-Formalism/lean/Semantics && lake build Compiler

# Python shim compilation check
python3 -m py_compile 4-Infrastructure/shim/<script>.py

# Storage verification
bash 4-Infrastructure/storage/restic/backup.sh verify
```

### Ray Cluster Operations

```bash
# Start Ray head (on nixos, Tailscale IP)
ray start --head --node-ip=100.102.173.61 --dashboard-host=0.0.0.0 --port=6379

# Connect worker (on qfox-1)
ray start --address=100.102.173.61:6379

# Deploy RayCluster via KubeRay
kubectl apply -f 4-Infrastructure/kube/raycluster.yaml
```

### Device Probe

```bash
# Probe local device
python3 4-Infrastructure/shim/device_capability_probe.py

# Probe cluster (via SSH/kubectl)
python3 4-Infrastructure/shim/device_capability_probe.py --cluster
```

---

*This wiki is auto-maintained as part of the Research Stack documentation surface. Last updated: May 30, 2026.*
