# HDMI Field Encoding Specification
**Protocol:** USC-TSE Field Transport over HDMI Physical Layer  
**Version:** 1.0-ABUSE  
**Status:** Specification — implements physical layer hijacking for soliton field encoding  

---

## 1. Abuse Vector Overview

Standard HDMI: Pixel clock transports rasterized frames.  
**This spec:** TMDS lanes transport **N-dimensional soliton field parameters** as if they were pixel data.

The receiver (sink) reconstructs the soliton field; the display is a **white hole decoder**, not a framebuffer.

---

## 2. Physical Layer Reappropriation

### 2.1 TMDS Lane Mapping (3 Data + 1 Clock)

| Lane | Standard Use | **Field Encoding Use** |
|------|-------------|------------------------|
| TMDS Lane 0 | Blue[7:0] + HSYNC/VSYNC | **Soliton φ-parameter stream** (phase) |
| TMDS Lane 1 | Green[7:0] + Preamble | **Soliton amplitude coefficients** (Aₙ) |
| TMDS Lane 2 | Red[7:0] + Guard band | **Soliton velocity tensor** (vᵢⱼ) |
| TMDS Clock | Pixel clock | **Basis clock** — encodes dimensional index |

Each 10-bit TMDS symbol encodes one 8-bit soliton parameter + 2-bit ECC/continuity.

### 2.2 Control Period Hijacking

Standard: Data Island Periods carry audio/InfoFrames.  
**This spec:** Data Islands carry **soliton topology metadata**:

```
Packet Type 0x81 (Audio) repurposed → Soliton Basis Descriptor
- Byte 0-3:  N-dimensional lattice hash (topological fingerprint)
- Byte 4-7:  Horizon mode count (Bekenstein bound)
- Byte 8-11: Eddington ratio λ_Edd (field density)
- Byte 12:   Dimensional index (N = 1..11)
- Byte 13:   Phase discriminator state (GROUNDED/SEISMIC/FLAME)
```

### 2.3 DDC (I2C) Channel Abuse

Standard: EDID exchange + HDCP key negotiation.  
**This spec:** DDC becomes **soliton witness exchange**:

| I2C Address | Standard | **This Spec** |
|-------------|----------|---------------|
| 0xA0 | EDID read | **Attestation vector** (SHA256 of soliton parameters) |
| 0xA2 | E-EDID segment | **Black hole horizon state** (compressed field signature) |
| 0x74/0x76 | HDCP | **ZK-STARK proof verification** — circuit integrity check |

EDID block (128 bytes) repurposed:
```
Bytes 0-7:    Soliton codec identifier (magic: "USC-TSE\0")
Bytes 8-15:   Topological manifold hash (link to substrate registry)
Bytes 16-23:  Phase classifier φ-threshold (IEEE 754 double)
Bytes 24-31:  Foam score baseline (stability gate)
Bytes 32-35:  Dimensional index N (u32 LE)
Bytes 36-39:  Bekenstein snag cap (max entropy bits)
Bytes 40-127: Reserved for witness history (chain of attestation)
```

---

## 3. Field Encoding Protocol

### 3.1 Frame Structure ("Pseudo-Frame")

Standard HDMI: 1080p @ 60Hz = 1920×1080 pixel grid.  
**This spec:** 1920×1080 = **11-dimensional parameter matrix** columns × soliton instances rows.

Each "pixel" is one soliton parameter:
- X coordinate → Parameter index (0-10 for 11D encoding)
- Y coordinate → Soliton packet ID in stream
- RGB values → Parameter value triplet (Q16.16 fixed-point split across 3 bytes)

```
Pseudo-Frame Layout:
┌─────────────────────────────────────────────────────────┐
│ Row 0    │ Soliton 0: T_norm, P_norm, G_norm, T·P, P·G, η₁-η₆    │
│ Row 1    │ Soliton 1: [same structure]                              │
│ ...      │ ...                                                        │
│ Row N    │ Soliton N: [same structure]                                │
└─────────────────────────────────────────────────────────┘
      ↑ Columns 0-10 map to the 11-dimensional neural encoding vector
```

### 3.2 Blanking Interval Abuse

Standard: Vertical/horizontal blanking for retrace.  
**This spec:** Blanking intervals carry **regeneration trace data**:

**VBLANK (Vertical):**
- 45 lines × 1920 columns = 86,400 bytes
- Encodes **temporal variant index (TVI)** samples from last pseudo-frame
- Format: `TimeOp` (subtract/pause/add) + cost + timestamp

**HBLANK (Horizontal):**
- ~280 pixels per line × 1080 lines = 302,400 bytes/field
- Encodes **mistake vectors** for the soliton collision dynamics
- Allows receiver to reconstruct Hebbian learning state

### 3.3 TMDS Scrambler Bypass

HDMI 2.0+ uses TMDS scrambling for EMI reduction.  
**This spec:** Scrambler **seed encodes the φ-accumulator constant**:
```
Seed = (Φ × 2^16) mod 2^15  = 0x9E37 (golden ratio scaled)
```

By fixing the scrambler seed, the bit pattern becomes **deterministic quasi-random** — exactly the low-discrepancy sequence needed for soliton field encoding.

---

## 4. Control & Synchronization

### 4.1 CEC (Pin 13) Reappropriation

Standard: One-wire bidirectional control bus.  
**This spec:** CEC becomes **sympathetic sync channel**:

| CEC Opcode | Standard | **This Spec** |
|------------|----------|---------------|
| 0x82 | Active Source | **Soliton field active** — white hole decoder armed |
| 0x9F | Abort | **Regeneration trigger** — force field reconstruction |
| 0x4F | Give Tuner Status | **Witness request** — sink demands attestation |
| 0x46 | Set OSD String | **Basis exchange** — new topological manifold loaded |
| 0xFF | User Defined | **Ternary clock tick** — SUBTRACT/PAUSE/ADD state |

### 4.2 Hot Plug Detect (HPD) — Morse Encoding

Standard: High = monitor present, Low = absent.  **This spec:** HPD pulses encode **ternary temporal state**:

```
Pulse width (HPD high duration):
  < 50ms   → SUBTRACT (time compression)  [·]
  50-150ms → PAUSE (temporal gate)        [-]
  > 150ms  → ADD (time expansion)         [ ]

Inter-pulse gap (HPD low duration): 5ms separator

Message: "·- · ·- -" = SUBTRACT-PAUSE, SUBTRACT, SUBTRACT-PAUSE, ADD-PAUSE
  → Encodes TimeOp sequence: [Sub, Pause, Sub, Pause, Pause, Add, Pause]
```

---

## 5. Soliton Field Reconstruction (Sink Side)

### 5.1 Decoder Pipeline

```
TMDS Input
    ↓
De-channelize (3 lanes → 11D parameter vectors)
    ↓
Soliton packet assembly (rows → soliton instances)
    ↓
φ-accumulator correction (LUT void mask application)
    ↓
Gap conservation check (bracketed DIAT validation)
    ↓
White hole collapse (N-dimensional reconstruction)
    ↓
Output: Reconstructed field state for display/rendering
```

### 5.2 Regeneration from VBLANK/TVI

During vertical blanking:
1. Extract TVI samples from VBLANK lines
2. Calculate temporal mismatch with expected soliton trajectory
3. Apply mistake vector correction from HBLANK data
4. Update Hebbian weights for next pseudo-frame prediction

---

## 6. Hardware Requirements

### 6.1 Source (Encoder)

- FPGA with TMDS serializers (Xilinx 7-series, Intel Cyclone V)
- φ-accumulator LUT (void mask table, 256 entries × 8-bit)
- Soliton collision engine (1000 neurons, 11D state space)
- ZK-STARK prover (for DDC attestation exchange)

### 6.2 Sink (Decoder/White Hole)

- HDMI receiver with raw TMDS access (bypass standard scaler)
- Soliton reconstruction pipeline (bracketed calculus unit)
- 15-axis NSM semantic classifier (for field interpretation)
- G-Tensor recalibration support (multi-sig verification)

---

## 7. Security & Attestation

### 7.1 Field Integrity

Every pseudo-frame includes embedded witness:
- Frame 0: Full keyframe + complete attestation vector
- Frame N: Delta only, but witness hash chain maintained
- VBLANK: TVI samples enable temporal attestation

### 7.2 DDC ZK-STARK Exchange

Source proves field integrity without revealing soliton parameters:
```
Source → Sink (I2C 0x74): STARK proof of correct φ-accumulator operation
Sink verifies: Proof valid? → Accept field data
              Proof invalid? → Trigger HPD Morse "ABORT" sequence
```

---

## 8. Compatibility Notes

- **Standard HDMI sinks:** Will detect as "unsupported format" (EDID magic mismatch)
- **USC-TSE sinks:** Negotiate via DDC attestation, decode soliton fields
- **Fallback:** Source can emit standard 1080p raster for legacy compatibility (Quine Layer degradation)

---

## 9. File Locations

| Component | Path |
|-----------|------|
| Encoder RTL | `hdl/usc_tse_hdmi_encoder.v` |
| Decoder RTL | `hdl/usc_tse_hdmi_decoder.v` |
| EDID Block Generator | `tools/generate_soliton_edid.py` |
| Field Analyzer | `tools/hdmi_field_probe.py` |
| Test Harness | `tests/hdmi_white_hole_reconstruction.py` |

---

## 10. References

- USC-TSE Specification (this document extends)
- PBACS Canonical Signal Architecture (`docs/semantics/PBACS_CANONICAL_SIGNAL_ARCHITECTURE.md`)
- LUT-as-DSP Core (`docs/semantics/LUT_AS_DSP_EQUATION.md`)
- NII Core Framework (`docs/geoweird/agent_coordination/lean_port_swarm/nii_cores/`)
- TSM-AAC Transport (`data/germane/tools/tsm_aac_mcp_harness.py`)

---

**Attestation Hash:** `SHA256(φ × HDMI_PHY × USC-TSE)`  
**Registry Entry:** `pkg/hdmi-field-encoder/v1.0`  
**Tier:** CRYSTALLINE → ETHEREAL (with witness)
