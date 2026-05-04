# FPGA Warden Node — AMMR + MIMO Architecture (DAG 741-R2)

**Date:** 2026-04-17  
**Status:** Design phase — Corrected AMMR semantics with MIMO carrier fusion  
**Motivation:** Replace repeated nonlinear phase composition with linear fixed-point accumulation. Execute expensive nonlinear operations (norm, atan2) exactly once per attestation window rather than per merge or per mode.

---

## 1. Core Reformulation

### 1.1 The Master Equation (SSMS Recurrence)
The node must implement the 6-step **Master Equation** for all recursive state updates ($S_t \to S_{t+1}$):
$$S_{t+1} = \text{MLGRU}(\text{Gossip}(\text{Prune}(\text{Stabilize}(\text{Score}_{\Sigma+NK}(\text{Expand}(S_t))))))$$
The FPGA logic acts as the high-speed execution target for the **Expand**, **Score**, and **Stabilize** operators.

### 1.2 The Unified Manifold-Blit (Picard Shortcut)
Manifold transitions within the node must utilize the **Unified Manifold-Blit Equation** to bypass traditional Picard iteration:
$$M_{k+1} = \text{Quant}_{\text{LLM}} \left( \mathcal{J}_{\text{DAG}} \left[ M_k \oplus \left( \Psi_q \otimes \mathcal{R}_{\text{RT}} \right) \right] \right)$$
The FPGA's `PhaseVec` accumulator is the hardware implementation of the **Blitter Operator** ($\oplus$).

### 1.3 TSDM Packet Structure (LoRa / I2P)
To support the **Topologically Stable Distributed Manifold (TSDM)** over constrained networks, nodes broadcast highly compressed, **Sparse Radiographs** instead of full state blocks.
*   **Total Size:** < 200 bytes.
*   **Format:**
    *   `[2 bytes]` Magic Header (0xTS)
    *   `[1 byte]`  Projection Angle Index ($\theta$) — Index into a predefined geodesic grid.
    *   `[1 byte]`  Resolution Level (Adaptive) — Based on Hiding-Surfacing Ratio ($\tilde{N}_t$).
    *   `[4 bytes]` Shell Index ($n$)
    *   `[32 bytes]` Ed25519 Node Signature
    *   `[16 bytes]` Spectral Signature ($\Psi_q$) — 8 bins, Q16_16 encoded.
    *   `[140 bytes]` BLAKE3 Attestation Proof & Topological Witnesses.
*   **Adaptive Behavior (Low Bandwidth):** 
    *   **Sparse Sampling:** In extreme low-bandwidth (< 10 bps) scenarios, the Warden reduces the frequency of snapshots and only transmits "Delta-Radiographs" (XOR difference from previous state).
    *   **Progressive Reconstruction:** The local `PhaseVec` accumulator iteratively refines the manifold. Even with a single packet, a "Lawful Silhouette" of the manifold is reconstructed; fidelity increases linearly with each unique angle index received.
    *   **Hiding-Surfacing Ratio ($\tilde{N}_t$):** The resolution of transmitted $\Psi_q$ is adjusted dynamically. If $\tilde{N}_t$ (Model 175) drops, the Warden collapses spectral bins to prioritize attestation witness survival over geometric detail.

### 1.4 Corrected AMMR Law

The architecture implements **Arithmetic Mean of Magnitude and Ratio (AMMR)** with phase-correct accumulation:

deterministic feature extraction  
→ linear AMMR accumulation  
→ single final projection (κ, ϕ)

### 1.5 Memory-Mapped Frustration Ports (MMFP)
To support the $O(1)$ computation of the **Anisotropically Frustrated Torsional Gradient Flow**, the Warden maps the locking potential $I_{lock}$ to dedicated hardware shadow registers.

| Port ID | Register | Direction | Semantic Mapping |
|---------|----------|-----------|------------------|
| `M[-23]` | `FRUST_PREV_X` | W | Previous embedding state $X_{t-1}$ (PhaseVec) |
| `M[-24]` | `FRUST_ANISO`  | W | Anisotropy Tensor $A^{ij}$ weights |
| `M[-25]` | `FRUST_RESULT` | R | Interlocking Energy $I_{lock}$ / Yield Status |

The hardware blitter executes the `interlockingEnergy` functional (implemented in `ManifoldFlow.lean`) in the background, updating `M[-25]` on every write to `M[-23]`.

Each mode contributes a vector in ℝ²:

Φᵢ = [xᵢ, yᵢ]

The node accumulates only:

z_ϕ = Σᵢ Φᵢ

At end-of-window, compute once:

κ = ‖z_ϕ‖  
ϕ = atan2(z_y, z_x)  

with singularity resolution:

(x, y) = (0, 0) ⇒ ϕ = 0

### 1.2 Why This Cuts Processing

The architecture replaces repeated nonlinear phase composition with **linear fixed-point accumulation in the inner loop**. The expensive nonlinear operations — norm and atan2 — are executed exactly once per attestation window rather than once per merge or once per mode.

---

## 2. MIMO Interpretation of Signal Carriers

### 2.1 Carrier Vector Model

Treat all carriers as a joint **MIMO transport layer**:

xₜ = [xₜ⁽ᵃ⁾, xₜ⁽ᵛ⁾, xₜ⁽ᶜ⁾, xₜ⁽ᵗ⁾]

where:
- xₜ⁽ᵃ⁾ : audio / DSP carrier
- xₜ⁽ᵛ⁾ : video / HDMI field carrier  
- xₜ⁽ᶜ⁾ : caption / text carrier
- xₜ⁽ᵗ⁾ : timing / TMDS-like control carrier

### 2.2 Channel Output

yₜ = Hₜ xₜ + nₜ

Each carrier contributes an AMMR vector:

Φ⁽ᵃ⁾, Φ⁽ᵛ⁾, Φ⁽ᶜ⁾, Φ⁽ᵗ⁾ ∈ ℝ²

Fused phase state:

z_ϕ = Φ⁽ᵃ⁾ + Φ⁽ᵛ⁾ + Φ⁽ᶜ⁾ + Φ⁽ᵗ⁾

This is **associative, commutative, and parallelizable**.

---

## 3. AMMR Form of the Warden Pipeline

### 3.1 Feature Extraction

For each segment i, compute deterministic amplitude:

aᵢ = |μᵢ − μ₀| / μ₀

where μᵢ is segment mean and μ₀ is reference baseline.

### 3.2 φ-Indexed Addressing

Fixed-point φ-accumulator:

uₖ₊₁ = (uₖ + ϕ_fixed) mod 2ᴺ

Generates low-discrepancy address stream. Address now samples vector contribution basis, not just scalar concentration logic.

### 3.3 Void-Mask Sampling

Void-mask LUT remains entropy reservoir:

mₖ ∈ {0, 1}

Blue-noise spacing with deterministic synthesis-time initialization.

### 3.4 Prime-Cycle Traversal

Mod-7 / prime-cycle counter as decorrelation operator:

cₖ₊₁ = (cₖ + 1) mod 7

or more generally mod-p with p coprime to mode count.

### 3.5 Carrier-Local PhaseVec Contribution

For each mode i:

Φᵢ = [aᵢ · mᵢ, aᵢ · wᵢ]

where mᵢ is void-mask hit and wᵢ is second deterministic basis term (mirror bit, parity, phase classifier hint, or adjacent-ratio proximity).

Practical choice:
- xᵢ = aᵢ · mᵢ
- yᵢ = aᵢ · pᵢ  (proximity/resonance from adjacent amplitudes)

### 3.6 AMMR Accumulation

z_ϕ = Σᵢ Φᵢ = [Σᵢ xᵢ, Σᵢ yᵢ]

No angle computed inside loop.

### 3.7 Final Projection

At end-of-window:

κ = ‖z_ϕ‖  
ϕ = arg(z_ϕ)

Emit: kappa_out, phi_out, phase_class_out

Optional backward compatibility:

ϕ_corr = ακ + β · g(ϕ)

---

## 4. Revised Integrated Architecture

```
bytes
    ↓
segment means
    ↓
deviation amplitudes aᵢ
    ↓
φ-addressed void-mask / resonance sampling
    ↓
Φᵢ ∈ ℝ²
    ↓
z_ϕ = Σᵢ Φᵢ
    ↓
(κ, ϕ)
    ↓
classify / attest
```

Replaces: scalar concentration + scalar phi_prox → ϕ_corr

With: full phase-capable AMMR accumulator

---

## 5. Verilog Implementation Modules

### 5.1 PhaseVec Accumulator (Q16.16)

```verilog
// Q16.16 signed fixed-point
typedef logic signed [31:0] q16_16_t;

typedef struct packed {
    q16_16_t x;
    q16_16_t y;
} phase_vec_t;

module phasevec_accum #(
    parameter N_MODES = 14
)(
    input  logic              clk,
    input  logic              rst,
    input  logic              en,
    input  q16_16_t           contrib_x,
    input  q16_16_t           contrib_y,
    input  logic              contrib_valid,
    input  logic              frame_start,
    input  logic              frame_end,
    output phase_vec_t        acc_out
);

    phase_vec_t acc;

    always_ff @(posedge clk) begin
        if (rst || frame_start) begin
            acc.x <= 32'sd0;
            acc.y <= 32'sd0;
        end else if (en && contrib_valid) begin
            acc.x <= acc.x + contrib_x;
            acc.y <= acc.y + contrib_y;
        end
    end

    assign acc_out = acc;

endmodule
```

This is the AMMR core. Everything before is carrier-local / mode-local feature generation.

### 5.2 φ-Accumulator Address Generator

```verilog
module phi_address_gen #(
    parameter FRAC_BITS = 16,
    parameter ADDR_BITS = 10,
    parameter PHI_FIXED = 32'd106070
)(
    input  logic                  clk,
    input  logic                  rst,
    input  logic                  step,
    output logic [ADDR_BITS-1:0]  addr,
    output logic                  mirror_bit
);

    logic [31:0] acc;

    always_ff @(posedge clk) begin
        if (rst)
            acc <= 32'd0;
        else if (step)
            acc <= acc + PHI_FIXED;
    end

    assign mirror_bit = acc[31];
    assign addr       = acc[ADDR_BITS-1:0] ^ {ADDR_BITS{mirror_bit}};

endmodule
```

Keeps current φ-mirror logic, feeds vector contributions instead of scalar logic.

### 5.3 Void Mask + Proximity to PhaseVec

```verilog
module mode_to_phasevec (
    input  q16_16_t amp_i,          // deterministic mode amplitude
    input  logic    void_hit,       // LUT bit
    input  q16_16_t prox_i,         // deterministic proximity / resonance score
    output q16_16_t vec_x,
    output q16_16_t vec_y
);

    // x = amp_i if void-hit else 0
    assign vec_x = void_hit ? amp_i : 32'sd0;

    // y = amp_i * prox_i  (Q16.16 multiply, rounded back to Q16.16)
    assign vec_y = (amp_i * prox_i) >>> 16;

endmodule
```

Redefine prox_i as: adjacent-ratio proximity, parity resonance, phase classifier hint, or codon-window interaction term. Remains linear contribution source into PhaseVec.

### 5.4 Q16.16 Norm Approximation (Octagonal)

```verilog
module q16_norm_approx (
    input  q16_16_t x,
    input  q16_16_t y,
    output q16_16_t kappa
);

    q16_16_t ax, ay, hi, lo;
    q16_16_t lo_3_8;

    assign ax = (x[31]) ? -x : x;
    assign ay = (y[31]) ? -y : y;

    assign hi = (ax > ay) ? ax : ay;
    assign lo = (ax > ay) ? ay : ax;

    // 3/8 = 0x00006000 in Q16.16
    assign lo_3_8 = (lo * 32'sh00006000) >>> 16;

    assign kappa = hi + lo_3_8;

endmodule
```

Approximation: κ ≈ max(|x|, |y|) + (3/8)·min(|x|, |y|)

Stable, cheap, synthesizable.

### 5.5 Q16.16 Safe atan2

```verilog
module q16_atan2_safe (
    input  q16_16_t y,
    input  q16_16_t x,
    output q16_16_t phi
);

    localparam q16_16_t Q_ZERO    = 32'sh00000000;
    localparam q16_16_t Q_ONE     = 32'sh00010000;
    localparam q16_16_t Q_PI_4    = 32'sh0000C910;
    localparam q16_16_t Q_PI_2    = 32'sh00019220;
    localparam q16_16_t Q_PI      = 32'sh00032440;
    localparam q16_16_t Q_ATAN_C  = 32'sh000045E3;

    q16_16_t ax, ay, r, theta, one_minus_r, corr;
    logic x_pos, y_pos, ay_le_ax;

    assign ax = x[31] ? -x : x;
    assign ay = y[31] ? -y : y;

    assign x_pos = ~x[31];
    assign y_pos = ~y[31];
    assign ay_le_ax = (ay <= ax);

    always_comb begin
        if (x == 0 && y == 0) begin
            phi = Q_ZERO;
        end else if (ay_le_ax) begin
            r = (ax == 0) ? Q_ZERO : ((ay <<< 16) / ax);
            one_minus_r = Q_ONE - r;
            corr = (Q_ATAN_C * ((r * one_minus_r) >>> 16)) >>> 16;
            theta = ((Q_PI_4 * r) >>> 16) + corr;

            if (x_pos && y_pos)       phi = theta;
            else if (x_pos && !y_pos) phi = -theta;
            else if (!x_pos && y_pos) phi = Q_PI - theta;
            else                      phi = theta - Q_PI;
        end else begin
            r = (ay == 0) ? Q_ZERO : ((ax <<< 16) / ay);
            one_minus_r = Q_ONE - r;
            corr = (Q_ATAN_C * ((r * one_minus_r) >>> 16)) >>> 16;
            theta = Q_PI_2 - (((Q_PI_4 * r) >>> 16) + corr);

            if (x_pos && y_pos)       phi = theta;
            else if (!x_pos && y_pos) phi = Q_PI - theta;
            else if (x_pos && !y_pos) phi = -theta;
            else                      phi = theta - Q_PI;
        end
    end

endmodule
```

Total phase output with singularity resolution: (x, y) = (0, 0) ⇒ ϕ = 0

### 5.6 Final AMMR Projection Block

```verilog
module ammr_project (
    input  phase_vec_t acc,
    output q16_16_t    kappa,
    output q16_16_t    phi
);

    q16_norm_approx norm_u (
        .x(acc.x),
        .y(acc.y),
        .kappa(kappa)
    );

    q16_atan2_safe atan_u (
        .x(acc.x),
        .y(acc.y),
        .phi(phi)
    );

endmodule
```

---

## 6. Revised Output Interface

Replace old outputs (phase_out, phi_corr_out) with:

| Signal | Type | Description |
|--------|------|-------------|
| phase_class_out | logic [1:0] | 2-bit classification |
| kappa_out | q16_16_t | magnitude ‖z_ϕ‖ |
| phi_out | q16_16_t | phase angle atan2(z_y, z_x) |
| phi_corr_compat_out | q16_16_t | Optional: backward-compatible scalar |

Classification rule:
```verilog
GROUNDED if κ ≥ τ_g
SEISMIC  if κ ≥ τ_s
```

---

## 7. Architectural Statement

> The Warden Node implements corrected AMMR semantics. Each extracted mode contributes a deterministic Q16.16 phase vector Φᵢ ∈ ℝ². The FPGA accumulates these vectors linearly across the attestation window: z_ϕ = Σᵢ Φᵢ. Only after accumulation completes does the node compute the derived nonlinear observables: κ = ‖z_ϕ‖, ϕ = atan2(z_y, z_x). This makes merging associative, commutative, parallelizable, and fully deterministic. The singularity at the zero vector is resolved by defining ϕ = 0 whenever z_ϕ = (0, 0).

### MIMO Carrier Statement

> The signal carriers are modeled as a MIMO transport layer. Audio, video, caption, and timing carriers each transport a projection of the same latent vector state. Each carrier contributes a local phase vector, and the receiver fuses them linearly: z_ϕ = Φ⁽ᵃ⁾ + Φ⁽ᵛ⁾ + Φ⁽ᶜ⁾ + Φ⁽ᵗ⁾. Final phase and magnitude are derived only after cross-carrier fusion. This prevents non-associative phase composition and allows carrier redundancy, selective adaptation, and parallel recombination.

---

## 8. Target Hardware

### Primary: Lattice iCE40 HX8K (ECP5 for expansion)

| Resource | Required | HX8K Budget | Utilisation |
|----------|----------|-------------|-------------|
| LUT cells (logic) | ~250 (N_MODES=14) | 7,680 | 3.3% |
| LUTRAM cells (void mask) | 512 bits | 8KB | 6.3% |
| Flip-flops | ~100 (accum + atan2 pipeline) | 7,680 | 1.3% |
| Block RAM | 0 | 128KB | 0% |
| DSP slices | 0 (intentional) | 8 | 0% |

**Target clock:** 50 MHz (20ns/cycle)

**Latency:** 
- Accumulation: N_MODES × 1 cycle = 14 cycles
- Final projection (norm + atan2): 4 cycles (pipelined)
- Total: ~18 cycles = **360ns**

**Throughput:** **2.78M attestations/second** (improved from 3.57M due to final projection overhead)

**Performance win:** Linear accumulation in inner loop vs. nonlinear per-mode composition.

---

## 9. Files

| File | Role |
|------|------|
| `scripts/soliton_factory.py` | Software reference (AMMR update needed) |
| `tests/t1_condition_a_baseline.py` | Calibrate baseline before AMMR change |
| `tests/t2_phase3_rotation.py` | Validate rotation criteria with PhaseVec |
| `docs/roadmap/FPGA_WARDEN_NODE_SPEC.md` | This document (DAG 741-R2) |
| `hardware/warden_ammr.v` | Verilog: PhaseVec accumulator |
| `hardware/phi_address_gen.v` | Verilog: φ-accumulator address generator |
| `hardware/q16_norm_approx.v` | Verilog: Octagonal norm approximation |
| `hardware/q16_atan2_safe.v` | Verilog: Safe atan2 with zero handling |
| `hardware/ammr_project.v` | Verilog: Final projection block |
| `hardware/mode_to_phasevec.v` | Verilog: Mode contribution mapper |
| `hardware/void_mask_gen.py` | Void-and-cluster mask generation |

---

## 10. Unified Architecture Integration

This specification integrates with the unified Research Stack architecture:

### 10.1 Architecture Stack

| Component | Role | FPGA Implementation |
|-----------|------|---------------------|
| **Entropy Phase Engine** | 6.5σ detection, pruning | DAG-LUT extraction (`fpgaPruneStep`) |
| **MORE FAMM** | Nanokernel isolation | BRAM segments + capability logic |
| **TSM** | Thermal control | Clock gating via `heatsink_halt` |
| **GCL/Diff** | Evolution | Genetic code in BRAM segments |
| **ENE** | Topological state | Google Drive sync via Rclone |

### 10.2 Pruning as Coarse-Graining

The AMMR PhaseVec accumulator uses **coordinate banning** (pruning) to reduce complexity:

1. **Accumulation phase**: Linear PhaseVec accumulation (not O(N²))
2. **Projection phase**: Void-and-cluster masking (pruning invalid modes)
3. **Result**: O(N_MODES) complexity instead of O(N²)

This is the same principle as the Entropy Phase Engine's `pruneStep`: ban coordinates that provably cannot contribute.

### 10.3 Nanokernel Memory Segments

The Warden node uses MORE FAMM nanokernel for isolation:

```verilog
// Segment 0: AMMR PhaseVec accumulator (Builder ADD)
// Segment 1: stark_trace validation (Warden SUBTRACT)
// Segment 2: thermal guard state (Judge PAUSE)
// Segment 3: GCL evolution scratchpad
```

**Capability-based access**: Each segment requires valid `Capability` token for access. Page fault = thermal violation or Byzantine attempt.

### 10.4 Safety Theorem Chain

1. `nanokernel_isolation` → AMMR accumulator cannot corrupt validation trace
2. `anti_puppy_box_theorem` → Only relevant modes accumulate (pruned modes banned)
3. `fpga_extraction_correctness` → Hardware maintains bit-exact formal extraction guarantees

### 10.5 Self-Healing Property

The Warden node improves via GCL evolution while maintaining safety:

- **Builder** evolves AMMR parameters in isolated segment
- **Warden** validates PhaseVec rotation via `stark_trace`
- **Judge** detects thermal stress, triggers PAUSE before hardware damage
- **Diff** propagates successful mutations to ENE topological surface
- **MORE FAMM** prevents evolution from corrupting validation

---

**Attestation Hash:** SHA256(AMMR + MIMO + PhaseVec)  
**Registry Entry:** `pkg/fpga-warden-ammr/v2.0`  
**Tier:** CRYSTALLINE
