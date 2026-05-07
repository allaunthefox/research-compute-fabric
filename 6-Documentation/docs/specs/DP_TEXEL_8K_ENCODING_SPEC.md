# DisplayPort × NVENC Texel Stream Specification

**Status:** Specification — 8K60 texel transport via DisplayPort + hardware H.264/H.265
**Target:** RTX 4070 SUPER (NVENC/NVDEC), Tang Nano 9K FPGA (sink)

---

## 1. Capacity

```
DisplayPort 1.4a (HBR3 × 4 lanes):
  4K@120Hz   = 3840×2160×120 = 995M pixels/sec active
  8K@60Hz    = 7680×4320×60  = 1.99B pixels/sec (with DSC)

NVENC (Ada Lovelace, RTX 4070 SUPER):
  8 concurrent encode sessions
  H.265 8K@60fps — single session
  H.264 8K@30fps — single session
```

## 2. Texel Capacity

| Resolution | Freq | Pixels/frame | Bytes/frame | GB/s |
|-----------|------|-------------|-------------|------|
| 1920×1080 | 60Hz | 2.07M | 6.22M | 0.37 |
| 3840×2160 | 120Hz | 8.29M | 24.88M | 2.99 |
| 7680×4320 | 60Hz | 33.18M | 99.53M | 5.97 |

At 8K60: **~100 MB/s raw texel bandwidth = ~800M texels/sec**

## 3. NVENC Encoding Pipeline

```
Texel Stream (100 MB/s raw)
    │
    ▼
┌──────────────────────────────────────────┐
│ CUDA DtoH → NVENC Encode (8 concurrent)    │
│                                            │
│ Session 0: Lane 0 (φ-phase stream)        │
│ Session 1: Lane 1 (amplitude coeffs Aₙ)    │
│ Session 2: Lane 2 (velocity tensor vᵢⱼ)   │
│ Session 3: Lane 3 (witness/attestation)   │
│ Session 4: VBLANK TVI (temporal variants)  │
│ Session 5: HBLANK mistake vectors          │
│ Session 6: DDC attestation proof stream    │
│ Session 7: CEC ternary clock stream        │
│                                            │
│ Output: H.265 stream per lane (lossless)   │
│ Compression: ~2-3:1 for structured texels  │
└──────────────────────────────────────────┘
    │
    ▼
DisplayPort → FPGA Sink → NVENC Decode → Cayley Verify
```

## 4. FP16 Texel Packing (doubles capacity)

Standard NUVMAP: 4 bytes per texel (u16:v16)
Optimized: 2 bytes per texel (FP16 half-precision)

| Encoding | Bytes/texel | 8K60 throughput |
|----------|------------|----------------|
| Q16_16 u16:v16 | 4 | 400M texels/sec |
| FP16 packed | 2 | 800M texels/sec |
| NV12 subsampled | 1.5 | 1.07B texels/sec |
| H.265 lossless | ~0.8 | 2B texels/sec |

## 5. Hardware Path

```
┌─────────────────────────────────────────────────────────┐
│ RTX 4070 SUPER (source)                                  │
│                                                          │
│  CUDA Core: PIST(k,t) encoding → NUVMAP texel stream     │
│  NVENC(0-7): H.265 encode 8 parallel lanes              │
│  DisplayPort 1.4a: 8K@60Hz pseudo-frame output           │
│  TMDS → 4 HBR3 lanes                                     │
└──────────────────────┬──────────────────────────────────┘
                       │ DP 1.4a cable
┌──────────────────────┴──────────────────────────────────┐
│ Tang Nano 9K FPGA (sink)                                 │
│                                                          │
│  UART RX: NVENC bistream → NVDEC decode (on GPU side)    │
│  FPGA BRAM: V4 Cayley table, invariant LUT               │
│  Verify: ∀ texel, V4.cayley_dist(g·h) ≤ d(g)+d(h)      │
│  Verify: mass_preserved for all mirrrored texels         │
│  HPD Morse: SUBTRACT/PAUSE/ADD ternary clock             │
│  LEDs: chiral state visualization                        │
└──────────────────────────────────────────────────────────┘
```

## 6. Throughput Comparison

| Method | Texels/sec | Bytes/sec | Compressor |
|--------|-----------|-----------|------------|
| 1080p@60 raw | 124M | 0.50 GB/s | None |
| 4K@120 raw | 995M | 3.98 GB/s | None | 
| 8K@60 raw | 1.99B | 7.96 GB/s | None |
| 8K@60 + NVENC | 1.99B | 2.65 GB/s | H.265 lossless |
| 8K@60 + NVENC + FP16 | 3.98B | 2.65 GB/s | H.265 + half-precision |

## 7. V4 Chain Verification at Scale

8K frame = 7680×4320 = 33,177,600 texels per frame
At 60fps = 1,990,656,000 texels/sec

FPGA verification budget:
  - Clock: 27 MHz
  - 1.99B texels / 27M cycles = 73.7 texels per cycle needed
  - Pipeline depth 64 → 1.15 texels/cycle → feasible at 23.4 MHz effective
  - With BRAM LUT + pipelined Cayley table: ~1 texel/cycle → need ~2 GHz
  - Realistic: verify 1/frame (~16 samples) → 960 samples/sec, latency-bound

For streaming verification: verify selected texel samples (V4 anchors, extremophile loci) not every texel.

