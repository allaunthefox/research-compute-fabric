# Unified Transport Encoding Architecture

## Encoding Agents & Channel Responsibilities

### Agent 1: TMDS Lane Encoding (HDMI/DP PHY)
**Responsibility:** Wire encoding over GPU display controller TMDS lanes.

- 3 lanes (HDMI 2.0) / 4 lanes (DP 1.4/2.0) — byte-striped round-robin
- Fragment packet (31 bytes): `PacketType(1) | VersionFlags(1) | FragmentIndex(1) | FragmentData(28)`
- 8b/10b encoding per lane (hardware, transparent)
- Blanking interval insertion: ~16% of link capacity for RDMA stealth
- RDMANetHeader (41 bytes) → 2 fragments (START + END)
- Multi-frame reassembly via `{FragmentIndex, QPN, seq}`
- Hot-plug state machine: disconnected → training → trained → suspended | error

### Agent 2: VCN Video Encoding (Steam Deck MKV Trick)
**Responsibility:** Pack RDMA payload into video frames, hardware encode/decode.

- 1920×1080 YUV420 frame = 3,110,400 bytes per frame
- Pixel packing: 6 bytes → 1 macroblock (4 Y + 1 U + 1 V)
- Pixel signature in first 24 bytes: `RDMAVCN\0` + version + seq + length
- H.265 Main, All-IDR, QP 2-4, transform skip on, deblocking+SAO off
- CRC32 per frame in SEI NAL (user_data_unregistered type 5)
- ~9 MB/s raw at 60fps (H.265 at QP4 compresses to ~162 Mbps)
- Pipeline latency: ~10ms (DMA + encode + transmit + decode + verify)

### Agent 3: Mesh Multi-Transport Routing
**Responsibility:** Transport selection, fragmentation, multi-hop relay, fallback.

- Unified envelope: `[tag(1)] + [transport-specific header] + [RDMANetHeader(41)] + [payload]`
- Fragmentation at MTU boundaries: `[fragSeq(2)][totalFrags(1)][flags(1)]`
- Transport cost = latency_ratio × 1000 + bandwidth_ratio × 100 + priority × 10 + frag_penalty
- Multi-hop: receive on transport A → decap → refrag for MTU_B → re-encap → send on transport B
- Fallback: ordered chain through top-N transports, max 3 retries per transport
- Multi-transmit: stripe payload across top-N transports concurrently

---

## Channel Hierarchy & Wire Formats

```
Priority  Transport           MTU       Tag  Header Overhead    Best Use
──────────────────────────────────────────────────────────────────────────
0         DP 2.0 UHBR20      65536     0x04  1+31 (fragment)   Bulk RDMA
1         HDMI 2.1 FRL       65536     0x04  1+31              Bulk RDMA
2         DP 1.4 HBR3        65536     0x04  1+31              Bulk RDMA
3         HDMI 2.0 TMDS      65536     0x04  1+31              Bulk RDMA
4         VCN H.265 encode   3.1M/f    0x05  1+1+4             Compressed bulk
5         USB DMA            65536     0x00  4+41              General RDMA
6         VCN H.264 encode   3.1M/f    0x05  1+1+4             Wider compat
7         WiFi UDP           1472      0x01  2+2+41            Remote mesh
8         Bluetooth L2CAP    251       0x02  2+41              Close peer
9         Serial (braid)     8         0x03  1+41              FPGA fabric
10        DP AUX             16        0x06  2+41              Control/keys
```

### Unified Envelope Wire Format

```
Byte 0:     Transport Tag (0x00-0x06)
Byte 1-4:   Transport-Specific Header (varies per tag)
Byte 5-45:  RDMANetHeader (41 bytes, fixed)
Byte 46+:   Payload (fragmented at MTU-46 boundary)
```

### Fragment Header (within payload region)

```
Byte 0-1:   fragSeq (UInt16, sequence within transfer)
Byte 2:     totalFrags (UInt8)
Byte 3:     flags (bit 0=START, bit 1=END, bit 2=RETRANS)
```

### Transport-Specific Headers

| Tag | Header | Size |
|-----|--------|------|
| 0x00 (USB DMA) | `sessionId:UInt32` | 4 |
| 0x01 (WiFi) | `srcPort:UInt16, dstPort:UInt16` | 4 |
| 0x02 (BT) | `cid:UInt16` | 2 |
| 0x03 (Serial) | `mode:UInt8` | 1 |
| 0x04 (TMDS) | `configId:UInt8` + fragment framing | 1+31 |
| 0x05 (VCN) | `codec:UInt8, seq:UInt32` + YUV frame | 5+3.1M |
| 0x06 (AUX) | `addr:UInt16` | 2 |

---

## Multi-Hop Routing Flow

```
Source peer
  → computeRDMApath(target) → [relay0 via WiFi, relay1 via BT, target via USB]
  → selectEgressNIC(dst) → pick NIC with wire link to first hop
  → encapsulateRDMARequest(wr, qp, transport) → wire bytes
  → send on transport A

Intermediate relay peer
  → receive on transport A
  → parse TransportEnvelope tag
  → reencapsulateForNextHop: strip A header, wrap in B header
  → refragment for MTU_B if needed
  → send on transport B

Destination peer
  → receive on transport B
  → reassemble fragments via {transferId, fragSeq}
  → validate RDMANetHeader (lkey/rkey checks)
  → perform DMA into registered memory region
```

## Fallback Chain

```
For each (transport, maxRetries=3) in selectTopNTransports(all_reachable):
  attempt encapsulateRDMARequest(wr, qp, transport)
  if success: return
  if failure after maxRetries: advance to next transport
If all exhausted: return failure
```

## Multi-Transmit Striping

```
partition(payload, n_transports):
  each plane = payload[n * i : n * (i+1)], capped at MTU × 64
  send all planes concurrently
  wait for all completions
  reassemble in order
```
