# Unified Signal Architecture — DisplayPort × Audio × FPGA

**Status:** Architecture — bridges 3 deployed hardware pathways into one texel state machine
**Deployed components:** HDMI shell, PipeWire waveprobe chain, DSP reconfiguration, braid DSP bridge

## Architecture

```
                        ┌──────────────────────────┐
                        │   NUVMAP Texel Stream     │
                        │   (PIST → Cayley V4 →     │
                        │    braid/rope encoding)    │
                        └──────────┬───────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ DisplayPort       │ │ PipeWire Audio    │ │ FPGA Tang Nano 9K│
    │ 8K@60Hz           │ │ 192kHz/24-bit     │ │ 27MHz UART/BRAM  │
    │                   │ │                   │ │                  │
    │ Lane 0: φ-phase   │ │ Left: TSM thermal │ │ V4 Cayley verify │
    │ Lane 1: Aₙ ampl   │ │ Right: Waveprobe  │ │ Mass preserved   │
    │ Lane 2: vᵢⱼ tensor│ │ Center: GCL delta  │ │ Triangle gate    │
    │ Lane 3: witness   │ │                   │ │ Chiral state LED │
    │                   │ │ VBLANK=SUBTRACT   │ │                  │
    │ NVENC session 0-7 │ │ HBLANK=PAUSE      │ │ DAG-LUT burned   │
    │                   │ │ FRAME=ADD          │ │                  │
    │ HPD: ternary clock│ │                   │ │ CEC: sync clock  │
    └────────┬──────────┘ └────────┬──────────┘ └────────┬─────────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │  Unified Frame Sync   │
                         │                       │
                         │  DP VSYNC = audio     │
                         │  buffer swap           │
                         │                       │
                         │  Frame 0: keyframe +  │
                         │    full attestation    │
                         │  Frame N: delta only   │
                         │                       │
                         │  VBLANK: TVI samples  │
                         │    + audio FFT bins   │
                         │  HBLANK: mistake vecs │
                         │    + GCL diff deltas  │
                         │  DDC: ZK-STARK proof  │
                         └───────────────────────┘
```

## Unified Timing

| Signal | DP 8K60 | PipeWire Audio | FPGA |
|--------|---------|---------------|------|
| Period | 16.67ms | 5.21µs (192kHz) | 37ns (27MHz) |
| Per frame | 33.18M texels | 3,200 samples | 450k cycles |
| Blanking | VBLANK=45 lines | PAUSE buffer | DAG-LUT write |
| Active | 4320 lines | ADD buffer | Cayley verify |
| Sync | HPD Morse | Jack transport | CEC clock tick |

## Deployed Verification

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| HDMI Computational Shell | `scripts/hdmi_computational_shell.py` | 301 | Deployed |
| DP 8K60 Texel Spec | `docs/specs/DP_TEXEL_8K_ENCODING_SPEC.md` | 116 | Written |
| PipeWire Waveprobe Chain | `tools-scripts/audio/pipewire_waveprobe_compression_chain.py` | 1,422 | Deployed |
| DSP Reconfiguration | `scripts/execute_swarm_dsp_reconfiguration.py` | — | Deployed |
| Braid DSP Bridge | `tools-scripts/braid/braid_dsp_bridge.py` | — | Deployed |
| Hybrid DSP Test | `tools-scripts/testing/test_hybrid_dsp_deterministic.py` | — | Deployed |
| V4 Cayley Verification | Lean 4 `CayleyFibergraph.lean` | — | Builds clean |
| FPGA Invariant Scanner | `cff/fpga/bridge.py` + Verilog | — | Flashed + live |
| GPU Eigenmass | `cff/gpu/eigenmass_engine.py` | — | CUDA 117ms |

## Key Equation

```
Frame[t+1] = bind(
  Frame[t],
  { DP_lane[0..3] → texel_stream,
    audio_left → waveprobe_score,
    audio_right → tsm_thermal,
    fpga_verify → V4_check },
  { Δ_frame = H(DP_texels[t]) - H(DP_texels[t-1]),
    Δ_audio = |waveprobe[t] - waveprobe[t-1]|,
    gate = Δ_frame < τ_frame ∧ Δ_audio < τ_audio }
)
```

The frame is admissible iff both the video texel entropy and audio waveprobe score remain within their Landauer thresholds. The FPGA V4 Cayley check is the hardware witness — if it fires a violation, the frame is quarantined via HPD Morse ABORT.
