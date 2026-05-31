# Specification: Virtio-Net DMA Compute Fabric & Packet-as-Computation (PIST)

This document specifies the architecture, data structures, and mathematical mapping for treating virtualized Ethernet networking hardware as a high-throughput, zero-copy, packetized DMA computation backplane.

---

## 1. Core Paradigm Shift

Traditional systems treat networking as a transmission layer for serialized compute payloads (e.g. JSON over TCP sockets):
$$\text{Memory} \xrightarrow{\text{Serialize}} \text{Payload} \xrightarrow{\text{OSI Stack}} \text{Network} \xrightarrow{\text{OSI Reassembly}} \text{Deserialize} \xrightarrow{\text{CPU Compute}}$$

This specification defines a **dataflow model** where:
1. **Ethernet is Math:** Packet headers, segmentation flags, and hardware queue indexes are structural dimensions of a computational state vector ($\Gamma$).
2. **Computation is Trajectory:** A program execution is represented as the trajectory of structured packet witnesses traversing a sequence of admissible transition operators ($T_i$) mapped directly to ring descriptors:
$$\Gamma_{k+1} = T_i(\Gamma_k)$$
3. **Offloads are Algebra:** Hardwired NIC/switch ASICs (CRC32, Toeplitz hashing, TCP Segmentation) are exploited as hardware-accelerated linear algebraic operators.

```
       GUEST MEMORY                       RING TRANSPORT                    TRANSFORM ENGINE
  ┌──────────────────────┐           ┌───────────────────────┐          ┌───────────────────────┐
  │ [PistPacket Header]  │           │   virtio-net TX Ring  │          │   Host QEMU/vhost     │
  │   - computation_id   │ ────────▶ │  (lock-free producer) │ ───────▶ │   (Matrix Transform)  │
  │   - coordinate_path  │           └───────────────────────┘          └───────────┬───────────┘
  │   - payload (Matrix) │                                                          │
  └──────────────────────┘                                                          ▼
  ┌──────────────────────┐           ┌───────────────────────┐          ┌───────────────────────┐
  │  Verified Result     │ ◀──────── │   virtio-net RX Ring  │ ◀────────│  NIC Offload Engines  │
  │  (CRC Witness Valid) │           │  (lock-free consumer) │          │  (Toeplitz RSS / CRC) │
  └──────────────────────┘           └───────────────────────┘          └───────────────────────┘
```

---

## 2. Packet Structure (`PistPacket`)

Compute frames traverse the ring buffer using standard Ethernet packaging to maintain driver compatibility, but their payload is structured as an immutable computation state capsule:

```c
struct __attribute__((packed)) pist_packet {
    /* 14-byte standard Ethernet Frame Header */
    uint8_t  dest_mac[6];       /* Target transform operator ID (T_i) */
    uint8_t  src_mac[6];        /* Provenance chain head / origin ID */
    uint16_t ethertype;         /* PIST-over-Ethernet identifier (0x88B5 or custom) */

    /* PIST Computation Header */
    uint64_t computation_id;    /* Unique ID of the dataflow graph instance */
    uint64_t step_index;        /* Sequential transition step count */
    uint32_t coordinate_path;   /* QuadTree/coordinate addressing path for spatial layout */
    uint32_t witness_hash;      /* Galois Field (CRC32) witness signature */
    uint32_t payload_len;       /* Length of active fixed-point matrix payload */

    /* Data Payload */
    uint8_t  payload[];         /* Saturating Q16_16 fixed-point data vector */
};
```

### Header Semantics:
*   `dest_mac`: Used by switch ASICs to route the packet to the appropriate hardware accelerator (GPU, FPGA, or SmartNIC queue) executing $T_i$.
*   `coordinate_path`: Encodes tree coordinates (e.g. `00` for $A_{11}$, `01` for $A_{12}$) enabling structured spatial partitioning.
*   `witness_hash`: Pre-calculated transition polynomial signature. An operator only executes if the incoming hash matches the mathematical precondition for that step.

---

## 3. Exploit Mapping: Network ASIC to Linear Algebra

This design maps linear algebra workloads onto standard hardware-assisted network offloads:

| Network ASIC Feature | Network Purpose | Algebraic Representation | Computational Exploit |
| :--- | :--- | :--- | :--- |
| **RSS (Receive Side Scaling)** | CPU Queue Load Balancing | Toeplitz Matrix Multiplication: $R = T \cdot V \pmod 2$ | Parallel 1D Convolutions, linear feedback transforms, and hardware-level task routing. |
| **TSO (TCP Segmentation)** | Packet Fragmentation | Tensor Slicing: $M_{large} \to \bigcup_{j} m_{j}$ | Automatic recursive tiling of large matrices into QuadTree quadrant blocks. |
| **LRO/MRG_RXBUF (Receive Coalescing)**| Buffer Aggregation | Block Aggregation (Matrix Sum/Concat) | Tiled matrix block consolidation and queue synchronization. |
| **FCS (Frame Check Sequence)** | Frame Bit Error Detection | Galois Field Polynomial division over $GF(2)[x]$ | Instantaneous graph connection validation and mathematical transition proofs. |

### Mathematical Target: The Toeplitz Transform (RSS)
The Toeplitz engine on the NIC multiplies the header vector $V$ by a Toeplitz matrix $T$ (defined by the RSS key $K$ programmed into the card) over $GF(2)$:
$$R_i = \sum_{j} T_{i-j} \cdot V_j \pmod 2$$
This operation executes at full line rate (100 Gbps+) on commodity switches, effectively yielding billions of binary matrix-vector convolutions per second without CPU overhead.

---

## 4. Formal Grounding: Lean Tree Solvers

Computational routing and spatial tiling correctness are verified using the formal tree representations in [TreeDIATKruskal.lean](file:///home/allaun/Research%20Stack/0-Core-Formalism/lean/Semantics/Semantics/TreeDIATKruskal.lean).

A block-matrix multiplication:
$$\begin{pmatrix} A_{11} & A_{12} \\ A_{21} & A_{22} \end{pmatrix} \cdot \begin{pmatrix} B_{11} & B_{12} \\ B_{21} & B_{22} \end{pmatrix}$$
is formalized as a recursive traversal of a `TreeNode` QuadTree.

```lean
-- From Semantics/Semantics/TreeDIATKruskal.lean
inductive TreeEmbeds : TreeNode → TreeNode → Prop
  | refl (t : TreeNode) : TreeEmbeds t t
  | intoLeft {s : TreeNode} {label : Nat} {l r : TreeNode} (h : TreeEmbeds s l) : TreeEmbeds s (.node label l r)
  | intoRight {s : TreeNode} {label : Nat} {l r : TreeNode} (h : TreeEmbeds s r) : TreeEmbeds s (.node label l r)
  | node {label : Nat} {l₁ r₁ l₂ r₂ : TreeNode} (hL : TreeEmbeds l₁ l₂) (hR : TreeEmbeds r₁ r₂) : TreeEmbeds (.node label l₁ r₁) (.node label l₂ r₂)
```

### Verification Contracts:
1.  **Structural Admissibility:** The `TreeEmbeds earlier later` relation proves that the sub-matrix workload `earlier` is homeomorphically compatible with the allocated physical cluster topology `later`.
2.  **Termination Guarantee:** `treeEmbeds_nodeCount_le` proves that sub-tasks strictly decrease in node size as computational flow descends the tree, guaranteeing routing termination.
3.  **Round-Free Denominator Scheduling:** Scheduling density priority is sorted via `scoreLENat` cross-multiplication, avoiding rounding drift in fixed-point registers:
    $$leaf_A \cdot (depth_B \cdot labels_B + 1) \le leaf_B \cdot (depth_A \cdot labels_A + 1)$$

---

## 5. Execution Pipeline (Zero-Copy Lifecycle)

```
[Guest App] Program descriptors in guest memory.
    │
    ▼
[Virtio TX Ring] Kick virtqueue; raw descriptors enqueued. (Zero-copy)
    │
    ▼
[QEMU Backend] Pop descriptor; detect PIST EtherType.
    │
    ├─► Match 'coordinate_path' to QuadTree structure.
    ├─► Apply matrix quadrant transform T_i.
    ▼
[NIC Offload Block] (Optional routing through hardware switch)
    ├─► TSO segments large payload matrices into sub-blocks.
    ├─► RSS Toeplitz hashes coordinates to assign target queues.
    ├─► CRC32 calculates Galois Field witness signature.
    ▼
[Virtio RX Ring] Push transformed results back into guest memory.
    │
    ▼
[Guest App / NAPI Hook] Intercept return frame; verify CRC witness; update state.
```

This pipeline allows matrix multiplication, grid subdivision, and node reduction to execute directly on the network plane, bypassing standard socket reassembly, OS scheduler bottlenecks, and user-space serialization layers.

---

## 6. Unified Transport Envelope & Multi-Hop Re-Encapsulation

For multi-transport and heterogeneous physical layouts, compute payloads are wrapped in a unified transmission envelope directly mirroring the formal specifications in `MeshRouting.lean`.

### 6.1 Wire Frame Layout
A serialized PIST packet is structured as a contiguous byte sequence containing:

1. **Transport Selector Tag (1 byte):**
   * `0x00`: USB DMA
   * `0x01`: WiFi
   * `0x02`: Bluetooth
   * `0x03`: Serial (UART)

2. **Transport-Specific Header (Variable, $H_{transport}$):**
   * USB DMA ($H_{transport} = 4$ bytes): session ID.
   * WiFi ($H_{transport} = 4$ bytes): source port + destination port.
   * Bluetooth ($H_{transport} = 2$ bytes): channel ID (`cid`).
   * Serial ($H_{transport} = 1$ byte): transmission mode.

3. **RDMA Net Header (41 bytes):**
   A packed representation of memory addresses and keys:
   ```c
   struct __attribute__((packed)) rdma_net_header {
       uint8_t  version;       /* Protocol version (always 1) */
       uint8_t  transport;     /* Transport enum: 0=USB, 1=WiFi, 2=BT, 3=Serial */
       uint8_t  wr_type;       /* Work Request type: 0=SEND, 1=WRITE, 2=READ */
       uint32_t qpn;           /* Queue Pair Number */
       uint32_t lkey;          /* Local Memory Key */
       uint32_t rkey;          /* Remote Memory Key */
       uint64_t local_addr;    /* Local source memory address pointer */
       uint64_t remote_addr;   /* Remote target memory address pointer */
       uint32_t length;        /* Total payload byte length */
       uint32_t seq;           /* Sequence number for verification */
       uint16_t flags;         /* Operational flags */
   };
   ```

4. **Fragment Header (4 bytes, Optional):**
   Appended if the payload size exceeds the transport's MTU:
   * `fragSeq` (2 bytes, little-endian): Sequence index of the current fragment.
   * `totalFrags` (1 byte): Total fragment count in the payload block.
   * `flags` (1 byte): State bits (`bit 0` = START, `bit 1` = END, `bit 2` = RETRANS).

5. **Compute Payload:**
   Raw $Q_{16.16}$ fixed-point data stream.

### 6.2 Fragmentation Bounds
MTU constraints require fragmenting the payload when total envelope size exceeds the physical layer's threshold:
$$\text{Max Payload Size} = \text{MTU} - (1 + H_{transport} + 41 + 4)$$

MTUs are defined statically per physical substrate:
* **USB DMA:** $65,536$ bytes
* **WiFi:** $1,472$ bytes
* **Bluetooth:** $251$ bytes
* **Serial:** $8$ bytes

### 6.3 Multi-Hop Re-Encapsulation Flow
At intermediate gateway nodes, the packet undergoes `reEncapForNextHop` to cross physical boundaries:
1. The incoming driver strips the 1-byte transport tag and $H_{transport}$ bytes.
2. The core router reads the `rdma_net_header` (41 bytes) to extract routing contexts, addresses, and sequence numbers.
3. The outbound driver assigns the new 1-byte transport tag corresponding to the target path.
4. The router prefixes a zeroed transport-specific header of size $H_{transport}$ for the target physical layer.
5. The packet is dispatched over the target interface, maintaining zero-copy data boundaries for the underlying payload.

---

## 7. 16D Goxel-to-Frame Compression Projection (VCN Substrate)

Large multi-dimensional systems, such as 16-dimensional shape potential fields, utilize physical video encoding hardware (AMD VCN) as high-throughput image compressors.

### 7.1 Coordinate Projection Hierarchy
A 16-dimensional shape potential state vector ($Goxel16D$) is projected down to 3D voxels ($Voxel3D$), which are then mapped to 2D coordinates $(u, v)$ for video frame processing.

#### Step 1: 16D Goxel to 3D Voxel
Given a 16-dimensional coordinate vector $(d_0, \dots, d_{15})$ in $Q_{16.16}$ space, the spatial position $(x, y, z)$ and attributes (intensity, torsion, coherence) are derived via:
$$x = \min\left(1023, \left\lfloor\frac{d_0.val}{64}\right\rfloor\right) - 512$$
$$y = \min\left(1023, \left\lfloor\frac{d_1.val}{64}\right\rfloor\right) - 512$$
$$z = \min\left(1023, \left\lfloor\frac{d_2.val}{64}\right\rfloor\right) - 512$$
$$\text{intensity} = d_3 + d_4 + d_5$$
$$\text{torsion} = d_6 + d_7$$
$$\text{coherence} = d_8 + d_9$$

#### Step 2: 3D Voxel to 2D Video Frame
The orthographic projection projects the voxel $(x, y, z)$ onto the 2D pixel coordinates $(u, v)$ in the frame:
$$u = \min(\text{width} - 1, \max(0, x + 512))$$
$$v = \min(\text{height} - 1, \max(0, y + 512))$$
$$\text{depth} = \text{intensity}$$

### 7.2 VCN Acceleration & Frame Formats
The 2D projection data is serialized into video frames for hardware-accelerated processing:
* **YUV420 Frame Format:** The depth/intensity values are written to the luminance channel ($Y$). Chroma subsampling ($U$ and $V$) is used to optimize memory, yielding a frame size of:
  $$\text{Size}_{YUV420} = \text{width} \times \text{height} \times \frac{3}{2} \text{ bytes}$$
* **RGB24 Frame Format:** Each pixel maps to three identical R, G, B bytes representing greyscale depth:
  $$\text{Size}_{RGB24} = \text{width} \times \text{height} \times 3 \text{ bytes}$$

Standard computation frame resolutions range dynamically from $240p$ ($320 \times 240$) up to $16K$ ($15,360 \times 8,640$) at frame rates up to $240\text{ fps}$.

Hardware encoding parameters use H.264 or HEVC codecs with high-compression quantization parameters ($qpMin = 2$, $qpMax = 4$) and `transformSkip = true` to prevent compression artifacts on numerical data grids.

### 7.3 Formal Soundness Theorems
The mathematical properties of the VCN compression pipeline are formally verified:
1. **Energy Conservation (`goxelFieldEnergyConservation`):**
   Let $E_{field}$ be the field energy and $C_{ratio}$ be the compression ratio. Saturated subtraction in $Q_{16.16}$ guarantees:
   $$(E_{field} - C_{ratio}).val \le 32768 \quad (\text{representing } 0.5 \text{ in } Q_{16.16})$$
   provided that $E_{field}.val \ge C_{ratio}.val$ and the energy difference is bounded within $0.5$ units.
2. **Topology Preservation (`goxelTopologyPreserved`):**
   The mapping preserves neighborhood adjacency relations on the grid, subject to the capacity condition:
   $$\text{Field size } |Goxels| \le \text{width} \times \text{height}$$

### 7.4 Lossless Density Optimization Vectors

To maximize the raw throughput of the VCN compression pipeline under mathematical losslessness ($qp = 0$ / `transquant_bypass = 1`), the mapping layer implements four density optimization vectors:

#### 7.4.1 Full-Range Pixel Mapping (Clamping Loss Elimination)
Standard YUV profiles restrict values to limited ranges ($16 \le Y \le 235$, $16 \le U, V \le 240$) to prevent out-of-bounds analog video signals. Under a pure computation backplane, this limited range clamps and corrupts binary/fixed-point values.
*   **Protocol Requirement:** The transport and encoder must enforce **Full-Range YUV** (JPEG range, e.g., `yuvj420p`, `yuvj444p` or via FFmpeg's `-color_range pc` option). This enables using the full $[0, 255]$ range for every byte, guaranteeing that all bit patterns are preserved without numerical clipping.

#### 7.4.2 Independent Y-Plane Packing (YUV420)
In standard YUV420, a $2 \times 2$ pixel macroblock utilizes $6$ bytes of video frame storage ($4\text{Y} + 1\text{U} + 1\text{V}$). Traditional implementations duplicate the luminance byte across all four pixels ($Y_0 = Y_1 = Y_2 = Y_3$) to preserve spatial low-frequency bounds.
*   **Lossless Packing:** Under a lossless configuration, spatial frequency boundaries are not quantized. The mapping engine packs **six independent data bytes** directly into the macroblock:
    $$\text{Macroblock} = \begin{pmatrix} Y_0 & Y_1 \\ Y_2 & Y_3 \end{pmatrix} \cup \{U_0, V_0\}$$
*   **Density Gain:** Increases the macroblock capacity from $4$ bytes of payload to $6$ bytes, yielding a **$50\%$ density increase** within YUV420.

#### 7.4.3 Subsampling Elimination via YUV444p / RGB24
When the hardware VCN block supports YUV444p or RGB24 profiles:
*   **Lossless Packing:** The mapping layer disables chroma subsampling completely. Every pixel coordinate $(u, v)$ stores three independent bytes (one in Y/Red, one in U/Green, one in V/Blue).
*   **Density Gain:** A $1920 \times 1080$ frame is packed to its maximum hardware boundary of $1920 \times 1080 \times 3 \text{ bytes} = 6.22 \text{ MB}$, yielding a **$3\times$ density increase** over YUV420.

#### 7.4.4 10-Bit and 12-Bit Hardware Channel Packing
Modern AMD VCN blocks support 10-bit HEVC (Main 10) and 12-bit AV1 hardware profiles.
*   **Lossless Packing:** By increasing the bit depth, each color channel sample represents 10 or 12 bits of numerical precision. Two pixels in a 10-bit YUV444 frame can store five $12$-bit coefficients or three $20$-bit variables, mapping more cleanly to $Q_{16.16}$ boundaries without bit-splitting overhead.
*   **Density Gain:** Yields a **$25\%$ to $50\%$ density increase** per channel.

---


## 8. Multi-Transmit Striping & Fallback Routing

To maximize throughput across concurrent physical interfaces (e.g. WiFi, USB DMA, Serial) and handle failures gracefully, PIST implements a cost-aware striping and fallback routing protocol.

### 8.1 Transport Cost Optimization
Outbound paths are prioritized based on a dynamic cost metric computed over integer space:
$$\text{Cost}(t, L) = \text{latency}(t) \times 1000 + \frac{100000}{\text{bandwidth}(t)} \times 100 + \text{frags}(t, L) \times 10$$

Where transport parameters are defined as:
* **USB DMA:** bandwidth = $3,840$ MB/s, latency = $1.0$ ms ($0x00010000$ in $Q_{16.16}$)
* **WiFi:** bandwidth = $150$ MB/s, latency = $10.0$ ms ($0x000A0000$ in $Q_{16.16}$)
* **Bluetooth:** bandwidth = $3$ MB/s, latency = $30.0$ ms ($0x001E0000$ in $Q_{16.16}$)
* **Serial:** bandwidth = $1$ MB/s, latency = $5.0$ ms ($0x00050000$ in $Q_{16.16}$)

### 8.2 Parallel Stripe Planes
To transmit a large compute buffer concurrently, the workload is divided into $N$ parallel stripe planes:
$$\text{Stripe Size} = \left\lfloor \frac{\text{Payload Length} + N - 1}{N} \right\rfloor$$
Each plane is dispatched over one of the $N$ active transport layers, balancing the bandwidth capabilities.

### 8.3 Fallback State Machine
When a transmission failure is detected, the protocol dynamically falls back to the next best link:
1. **Fallback Chain Sorting:** The system sorts all available physical interfaces by ascending cost.
2. **Link Promotion:** Upon failure of the primary transport, the state machine triggers `fallbackAdvance`:
   * The failed link is removed from active candidates.
   * The next link in the sorted chain is promoted to `currentTransport`.
   * The retry counter is reset to `maxRetries` (default = 3).
3. **Execution Recovery:** The current stripe plane is re-fragmented according to the new link's MTU and retransmitted.

---

## 9. Appendix A: Naming Conventions & Standard Mappings

This section documents non-standard or domain-specific terminology used in this specification and aligns it with standard mathematical and industry networking conventions.

| Project Term | Description / Custom Semantics | Standard Equivalent / Industry Specification | Standard Reference Link |
| :--- | :--- | :--- | :--- |
| **PIST** | Packet-as-Computation / Packet-in-State-Transfer. Treats Ethernet frames as dynamic algebraic state capsules. | Active Networking / In-Network Computing (INC) / Data Plane Programming (P4) | [Active Networking (Wikipedia)](https://en.wikipedia.org/wiki/Active_network) |
| **Goxel** | 16-dimensional shape potential state element representing a volumetric node in high-dimensional space. | Voxel (Volumetric Pixel) / Signed Distance Field (SDF) Volume Element | [Voxel (Wikipedia)](https://en.wikipedia.org/wiki/Voxel) |
| **Hoxel** | A hyper-dimensional voxel (specifically 4D or higher) representing a hyper-volume element. | Hyper-Voxel / Hyper-volume Element | [Hypervoxel Concept](https://en.wikipedia.org/wiki/Voxel) |
| **Sidon Label** | Unique address allocation key where pairwise sums of addresses are unique, preventing hash collisions. | Sidon Set / $B_2$ Set | [Sidon Set (Wikipedia)](https://en.wikipedia.org/wiki/Sidon_set) |
| **BraidStorm** | 8-strand braid topology modeling topological crossing nodes and crossing group iterations. | Braid Group ($B_n$) / Braid Topology | [Braid Group (Wikipedia)](https://en.wikipedia.org/wiki/Braid_group) |
| **Eigensolid** | Stationary state converged via braid crossings where consecutive operations act as identity. | Stationary State / Fixed Point of a Dynamic Map / Eigenstate | [Fixed Point (Wikipedia)](https://en.wikipedia.org/wiki/Fixed_point_(mathematics)) |
| **Scar** | Record logging FAMM capability memory failures, coarsening agents, and repair pressures. | Memory Fault Log / Exception Register / Error Status Record | [Page Fault (Wikipedia)](https://en.wikipedia.org/wiki/Page_fault) |
| **VCN** | Video Core Next. Dedicated AMD hardware block used for video stream encoding and decoding. | AMD VCN Hardware Accelerator | [Video Core Next (Wikipedia)](https://en.wikipedia.org/wiki/Video_Core_Next) |
| **RSS Toeplitz** | Receive Side Scaling. Hashing mechanism that maps TCP/UDP headers using a Toeplitz matrix. | Microsoft RSS Specification / Toeplitz Hashing | [Toeplitz Matrix (Wikipedia)](https://en.wikipedia.org/wiki/Toeplitz_matrix) |
| **Yang-Baxter** | Braid crossing relations modeling braid-order invariance. | Yang-Baxter Equation | [Yang-Baxter (Wikipedia)](https://en.wikipedia.org/wiki/Yang%E2%80%93Baxter_equation) |
| **enwik9** | Canonical 1GB Wikipedia XML dataset used as the end-to-end compression test benchmark. | Hutter Prize Large Text Compression Corpus | [enwik9 Reference](http://www.mattmahoney.net/dc/textdata.html) |
| **MORE FAMM** | Memory-Optimized Recursive Entropy Fractal Aggregate Memory Model. | Capability-Based Memory Segmentation / Segmented Paging | [Capability-Based Security (Wikipedia)](https://en.wikipedia.org/wiki/Capability-based_security) |


## 10. Design Constraints & Boundary Safeguards

This section outlines the operational constraints, hardware limits, and security boundaries that must be maintained when executing PIST compute operations over virtualized Ethernet rings.

### 10.1 Numerical & Arithmetic Constraints
1. **Fixed-Point Uniformity:** All numerical data vectors residing in the packet payload must use $Q_{16.16}$ fixed-point representation. Floating-point computations (`Float`) are strictly prohibited in the computational path.
2. **GF(2) Offload Limits:** The Toeplitz hashing engine (RSS) performs modulo-2 matrix-vector multiplication ($GF(2)$ arithmetic). It cannot perform general arithmetic over $Q_{16.16}$. Standard additions and multiplications must be handled by the transform engines on the host or external accelerator nodes, using the RSS engine solely for hashing-based task distribution and spatial routing.
3. **Non-overflow Saturation:** Fixed-point arithmetic operations on the host or within shims must use saturating arithmetic. Underflows and overflows must saturate to the minimum/maximum representable values:
   * Max Value: $+32767.99998$ (`0x7FFFFFFF` raw)
   * Min Value: $-32768.00000$ (`0x80000000` raw)

### 10.2 Queue & Ring Buffer Constraints
1. **Descriptor Ring Capacity:** The virtio-net descriptor table size ($N$) must be a power of 2 ($128 \le N \le 1024$).
2. **In-Flight Flow Control:** To prevent packet loss, the guest driver must implement strict flow control. The maximum number of concurrently dispatched (in-flight) descriptors must satisfy:
   $$\text{InFlight} \le N - 2$$
   If the available descriptor count falls below 2, the guest queue must block until the host returns a used buffer.
3. **Alignment Boundaries:** All descriptors referencing the packet payload must be aligned to 64-byte cache line boundaries to prevent split-cache access penalties and ensure optimal DMA transfer rates.

### 10.3 MTU & Packet Size Boundaries
1. **MTU Mapping:** Compute packets must not exceed the physical link or virtual device MTU unless TSO (TCP Segmentation Offload) is explicitly enabled.
2. **Maximum Payload Bounds:** For a standard virtual network interface with an MTU of 1500 bytes, the maximum payload size ($L_{payload}$) in a single unfragmented frame is:
   $$L_{payload} = 1500 - (14 + 41 + H_{transport}) \text{ bytes}$$
   Where $14$ is the Ethernet header, $41$ is the `RDMANetHeader`, and $H_{transport}$ is the transport-specific overhead.
3. **TSO Tiling Segments:** When TSO is used for matrix slicing, the segment size (`gso_size`) must be a multiple of the matrix row size (e.g. multiples of $32$ or $64$ bytes) to ensure that split packets do not bisect individual fixed-point numeric fields.

### 10.4 Hypervisor Isolation & Security Safeguards
1. **Address Space Isolation:** Memory addresses passed in `RDMANetHeader` (`local_addr`, `remote_addr`) represent Guest Physical Addresses (GPA). The host vhost-user backend must translate GPAs using its memory map (`VHOST_USER_SET_MEM_TABLE`) and validate that all accessed regions lie strictly within the guest's allocated memory space. Directly dereferencing unvalidated addresses is forbidden.
2. **Interface Scoping:** PIST Ethernet frames must be tagged with a dedicated EtherType (e.g., `0x88B5` or local custom tags) and bound to link-local interfaces or internal virtual bridges (`virbr0`, `xenbr0`). The host network filter must drop any PIST-ethertype packets originating from external interfaces to prevent spoofing or injection of rogue state capsules.
3. **State Verification:** Gateway nodes and transform engines must only execute transition steps if the incoming `witness_hash` matches the pre-calculated Galois Field polynomial of the target state, preventing the execution of out-of-order or corrupt state transitions.


## 11. QEMU Graphics Framebuffer Backplane

As a parallel transport channel to virtualized network interfaces, the virtual VGA or GPU graphics framebuffer (`/dev/fb0` on guest) can be exploited as a zero-copy DMA computation backplane.

This mechanism allows high-bandwidth VM-to-Host communication in locked-down microVMs where custom PCIe devices are blocked, but virtual graphics outputs (required for VM console access) remain enabled.

### 11.1 Pixel-to-Scalar Mapping Models

Data payloads are packed directly into the graphics framebuffer using format-specific pixel layouts:

#### 1. ARGB8888 Mode (100% Density)
Each pixel is represented as a 32-bit (4-byte) word. One $Q_{16.16}$ fixed-point scalar is mapped directly to one pixel.
*   **Byte Mapping:**
    *   `Byte 0` (Blue Channel): Lowest 8 bits of $Q_{16.16}$ scalar.
    *   `Byte 1` (Green Channel): Bits 8-15 of $Q_{16.16}$ scalar.
    *   `Byte 2` (Red Channel): Bits 16-23 of $Q_{16.16}$ scalar.
    *   `Byte 3` (Alpha Channel): Highest 8 bits of $Q_{16.16}$ scalar.
*   **Capacity:** A standard $1920 \times 1080$ display framebuffer holds exactly:
    $$1920 \times 1080 \times 4 \text{ bytes} \approx 8.29 \text{ MB of raw numerical data}$$

#### 2. RGB24 Mode (3-Byte Raw Packing)
Each pixel is represented as a 24-bit (3-byte) word. The red, green, and blue color channels hold three independent raw data bytes.
*   **Capacity:** A $1920 \times 1080$ display framebuffer holds:
    $$1920 \times 1080 \times 3 \text{ bytes} \approx 6.22 \text{ MB of raw data}$$

### 11.2 Memory-Mapped I/O Lifecycle
1.  **Guest Allocation:** The guest application opens `/dev/fb0` and maps the screen memory range into its user space using zero-copy memory mapping (`mmap`).
2.  **Envelope Injection:** The guest prefixes the standard 24-byte signature header (`RDMAVCN\0`) at the start of the frame (top-left screen pixels) to denote sequence number, length, and pixel format tag.
3.  **DMA Transfer:** The guest writes the packed matrix block into the mapped framebuffer. The write is instantly copied via guest physical memory to the virtual graphics card's PCI BAR.
4.  **Host Transformation:** QEMU’s UI thread or VNC/SPICE server detects dirty display scanlines. The host-side transformation engine parses the signature header, extracts the raw pixel data, applies the linear algebra transform, and writes the output back to the display buffer.
5.  **Guest Readback:** The guest application reads the updated frame buffer from `/dev/fb0` to retrieve the computed state.
