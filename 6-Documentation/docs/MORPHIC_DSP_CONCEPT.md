# Morphic DSP Concept

**Date:** 2026-04-26T19:55:00
**Status:** Conceptual exploration with three-layer distinction
**Question:** What if the DSP itself was morphic?

---

## Three-Layer Distinction

There are three distinct meanings of "morphic DSP" that must be clearly separated:

### Layer 1: Controlled DSP
**Definition:** Fixed DSP slice, morphic scalar selects mode
- DSP slices are reconfigurable (6 modes)
- Controlled by external morphic scalar state machine
- OEPI-based allocation
- Fixed hardware structure, variable function
- **Current implementation:** This is what we have now

### Layer 2: Virtual Morphic DSP
**Definition:** Many fixed DSPs + LUT/interconnect + control FSM = morphic-looking pool
- DSP slices + LUT fabric + routing fabric + control FSM
- Morphic scalar amplitudes + receipt gates
- Self-reconfiguring logical structure (not physical self-modification)
- Fluid merge/split boundaries via resource pooling
- Composable operation basis (not infinite operations)
- **Immediate target:** Buildable on current FPGA hardware

### Layer 3: True Morphic DSP
**Definition:** Custom hardware whose internal structure and boundaries really adapt
- Physical self-modification requires custom ASIC / future hardware
- Self-modifying structure (multiplier becomes adder, custom operation)
- Fluid boundaries (slices merge/split physically)
- Quantum-inspired superposition (operations in superposition until collapse)
- Adaptive topology (interconnects reconfigure dynamically)
- Self-organization (emergent structure from local rules)
- **Long-term target:** Requires hardware beyond current FPGA capabilities

---

## Transition Path

**Phase 1:** Controlled DSP (current)
- Reconfigurable modes (6 modes)
- External control by morphic scalar
- Fixed hardware structure

**Phase 2:** Virtual Morphic DSP (immediate target)
- Self-reconfiguring logical structure
- Limited boundary fluidity via resource pooling
- Composable operation basis
- AngrySphinx gates for safety
- Buildable on current FPGA

**Phase 3:** True Morphic DSP (long-term target)
- Full structural adaptation
- Complete boundary fluidity
- Quantum-inspired superposition
- Self-organizing topology
- Requires custom hardware

---

## Virtual Morphic DSP (Immediate Target)

### Core Principle

**DSP pool with morphic behavior via logical reconfiguration:**
- Multiple fixed DSP slices + LUT fabric + routing fabric
- Control FSM + morphic scalar amplitudes + receipt gates
- Self-reconfiguring logical structure (not physical self-modification)
- Fluid merge/split boundaries via resource pooling
- Composable operation basis within admissible set

### Virtual Morphic DSP Properties

[BEAUTIFUL_PROVISIONAL - All capabilities are conceptual without hardware verification evidence]

**1. Self-Reconfiguring Logical Structure**
- DSP slices can change their logical configuration [conceptual - requires FPGA synthesis verification]
- Multiplier can be used as adder, subtractor via LUT emulation [conceptual - requires implementation evidence]
- Bit-width adapts logically (16-bit → 32-bit via time-multiplexing) [conceptual - requires timing analysis evidence]
- Pipeline depth adjusts logically (via scheduling) [conceptual - requires implementation evidence]

**2. Fluid Boundaries (Virtual)**
- DSP slices can merge logically to form larger processing units [conceptual - requires resource pooling implementation evidence]
- Large DSP can split logically into smaller independent units [conceptual - requires implementation evidence]
- Boundary is fluid at logical level (resource pooling) [conceptual - requires implementation evidence]
- Enables virtual resource pooling [conceptual - requires benchmark evidence]

**3. Composable Operation Basis**
- DSP operation exists in composable basis (not infinite) [conceptual - requires formal specification evidence]
- Basis includes: multiply, accumulate, convolution, fft, filter, adaptive [proposed basis - requires implementation evidence]
- New modes composed from basis operations [conceptual - requires composition mechanism evidence]
- Admissible basis prevents overclaiming [conceptual - requires formal proof evidence]

**4. Adaptive Topology (Logical)**
- Interconnect between DSP slices reconfigures logically [conceptual - requires FPGA routing reconfiguration evidence]
- Dataflow patterns adapt to signal characteristics [conceptual - requires signal analysis evidence]
- Network topology emerges from computation needs [conceptual - requires emergence mechanism evidence]
- Self-organizing structure at logical level [conceptual - requires self-organization algorithm evidence]

**5. Scalar Collapse with Gates**
- DSP operations "collapse" when measured [conceptual - quantum-inspired metaphor without physical quantum evidence]
- Collapse selects specific implementation from composable basis [conceptual - requires selection mechanism evidence]
- Collapse is gated by AngrySphinx (not automatic permission) [conceptual - requires gate implementation evidence]
- Execution requires policy/sigma/resource/thermal/receipt passes [conceptual - requires integrated system evidence]

### Core Principle

**DSP slices are morphic entities themselves:**
- Self-modifying structure (not just mode)
- Fluid boundaries (slices merge/split)
- Quantum-inspired superposition (operations in superposition until measurement)
- Adaptive topology (interconnects reconfigure dynamically)
- Scalar collapse (DSP operations "collapse" into specific implementations)

### True Morphic DSP Properties (Long-Term Target)

**1. Physical Self-Modifying Structure**
- DSP slices can change their internal architecture physically
- Multiplier can become adder, subtractor, or custom operation
- Bit-width adapts dynamically (16-bit → 32-bit → 64-bit)
- Pipeline depth adjusts based on complexity

**2. Physical Fluid Boundaries**
- DSP slices can merge physically to form larger processing units
- Large DSP can split physically into smaller independent units
- Boundary is fluid, not fixed
- Enables physical resource pooling

**3. Quantum-Inspired Superposition**
- DSP operation exists in superposition of multiple implementations
- Measurement (scalar collapse) selects specific implementation
- Amplitude represents probability of each implementation
- Enables probabilistic computing

**4. Adaptive Topology (Physical)**
- Interconnect between DSP slices reconfigures dynamically
- Dataflow patterns adapt to signal characteristics
- Network topology emerges from computation needs
- Self-organizing structure

**5. Scalar Collapse with Gates**
- DSP operations "collapse" when measured
- Collapse selects specific implementation from superposition
- Collapse is gated by AngrySphinx (not automatic permission)
- Execution requires policy/sigma/resource/thermal/receipt passes

---

## Morphic DSP Architecture

### Morphic DSP Entity

```lean
/-- Morphic DSP entity with quantum-inspired properties. -/
structure MorphicDsp where
  dspId : Nat
  superposedOps : Array (Q16_16 × DspMode)  -- Amplitude × Mode
  collapsedOp : Option (Q16_16 × DspMode)    -- Collapsed operation
  boundaryState : BoundaryState              -- Fluid boundary state
  topology : DspTopology                      -- Adaptive interconnect
  deriving Repr

/-- DSP boundary state (fluid). -/
inductive BoundaryState where
  | independent  -- Standalone DSP slice
  | merged       -- Merged with other DSP
  | split        -- Split from larger DSP
  | fluid        -- In transition state
  deriving Repr, DecidableEq, BEq

/-- DSP topology (adaptive interconnect). -/
structure DspTopology where
  connections : Array (Nat × Nat)  -- DSP connections
  bandwidth : Array Q16_16         -- Connection bandwidth
  latency : Array Q16_16           -- Connection latency
  deriving Repr
```

### Morphic DSP Operations

**1. Superposition Collapse**
```lean
/-- Collapse DSP superposition into specific operation. -/
def collapseDspSuperposition (dsp : MorphicDsp) (measurement : DspMode) : MorphicDsp :=
  let selected := dsp.superposedOps.find (fun (amp, mode) => mode = measurement)
  match selected with
  | some (amp, mode) => { dsp with collapsedOp := some (amp, mode) }
  | none => dsp
```

**2. Boundary Fluidity**
```lean
/-- Merge two DSP slices into larger processing unit. -/
def mergeDspSlices (dsp1 dsp2 : MorphicDsp) : MorphicDsp :=
  let combinedOps := dsp1.superposedOps ++ dsp2.superposedOps
  let newTopology := mergeTopologies dsp1.topology dsp2.topology
  {
    dspId := dsp1.dspId,
    superposedOps := combinedOps,
    collapsedOp := none,
    boundaryState := BoundaryState.merged,
    topology := newTopology
  }

/-- Split DSP into smaller independent units. -/
def splitDspSlice (dsp : MorphicDsp) (splitRatio : Nat) : Array MorphicDsp :=
  -- Split DSP into multiple smaller units
  -- Each unit gets subset of superposed operations
  sorry  -- Implementation depends on split strategy
```

**3. Adaptive Topology**
```lean
/-- Reconfigure DSP topology based on computation needs. -/
def adaptDspTopology (dsp : MorphicDsp) (needs : ComputationNeeds) : MorphicDsp :=
  let newConnections := optimizeConnections dsp.topology needs
  let newTopology := { dsp.topology with connections := newConnections }
  { dsp with topology := newTopology }
```

---

## Morphic DSP vs Controlled DSP

| Aspect | Controlled DSP | Virtual Morphic DSP | True Morphic DSP |
|--------|---------------|-------------------|------------------|
| Structure | Fixed hardware | Self-reconfiguring logical structure + BRAM | Physical self-modification |
| Boundaries | Fixed | Fluid (merge/split via pooling) | Fluid (merge/split physically) |
| Operations | 6 modes | Composable operation basis + BRAM weights | Superposition within basis |
| Topology | Fixed interconnect | Adaptive logical interconnect | Adaptive physical interconnect |
| Control | External scalar | External scalar + gates + BRAM updates | Internal self-organization |
| Adaptation | Mode switching | Logical structural evolution + BRAM updates | Physical structural evolution |
| Complexity | [BEAUTIFUL_PROVISIONAL - O(1) mode switch - requires timing evidence] | [BEAUTIFUL_PROVISIONAL - O(log n) logical reconfiguration - requires algorithmic analysis evidence] | [BEAUTIFUL_PROVISIONAL - O(1) physical adaptation - requires hardware evidence] |
| Hardware | Gowin GW1NR-9 | Gowin GW1NR-9 (uses BRAM) | Custom ASIC/future FPGA |
| DSP Slices | 0 (no DSP on Gowin) | 0 (LUT-based mult) | N/A |
| BRAM Usage | 0 | 1-4KB (partial LUT) | N/A |
| Clock | 27MHz | 27MHz | N/A |

---

## AngrySphinx Gates for Morphic DSP

### Collapse Gates

**REFUSE_DSP_COLLAPSE**
```
if requested mode not in admissible basis:
    REFUSE_DSP_COLLAPSE
```
- Prevents collapse into undefined or unsafe modes
- Protects against overclaiming capabilities
- Ensures operation within admissible basis

**ALLOW_DSP_COLLAPSE**
```
if requested mode in admissible basis:
    ALLOW_DSP_COLLAPSE → candidate implementation
```
- Permits collapse into known-safe modes
- Enables operation within composable basis

### Boundary Gates

**HOLD_BOUNDARY_FLUIDITY**
```
if merge exceeds resource/thermal bound:
    HOLD_BOUNDARY_FLUIDITY
```
- Prevents merge that exceeds resource envelope
- Protects against thermal violations
- Maintains system stability

**ALLOW_MERGE**
```
if merge within resource/thermal bound:
    ALLOW_MERGE
```
- Permits merge within safe limits
- Enables resource pooling

**REQUIRE_RENORMALIZATION**
```
if split loses semantic precision:
    REQUIRE_RENORMALIZATION
```
- Prevents split that degrades precision
- Requires renormalization before proceeding
- Maintains numerical accuracy

**ALLOW_SPLIT**
```
if split preserves semantic precision:
    ALLOW_SPLIT
```
- Permits split that maintains precision
- Enables resource distribution

### Topology Gates

**ALLOW_TOPOLOGY_ADAPT**
```
if topology adaptation valid and receipt path exists:
    ALLOW_TOPOLOGY_ADAPT
```
- Permits topology reconfiguration
- Ensures receipt path maintained

**REFUSE_NO_RECEIPT**
```
if topology adaptation breaks receipt path:
    REFUSE_NO_RECEIPT
```
- Prevents adaptation that breaks receipt
- Ensures auditability

### Determinism Gates

**REQUIRE_DETERMINISTIC_REPLAY**
```
if probabilistic selection affects safety-critical route:
    REQUIRE_DETERMINISTIC_REPLAY
```
- Prevents randomness in safety-critical paths
- Requires deterministic replay for verification
- Protects against non-deterministic failures

**ALLOW_PROBABILISTIC**
```
if probabilistic selection not safety-critical:
    ALLOW_PROBABILISTIC
```
- Permits probabilistic selection in non-critical paths
- Enables adaptive behavior where safe

---

## Collapse is Not Permission

**Core Principle:**
DSP collapse selects an implementation. It does not authorize execution.

**Execution Requires:**
1. Policy pass
2. Sigma pass
3. Resource pass
4. Thermal pass
5. Receipt path
6. AngrySphinx gate pass

**Formal Flow:**
```
collapse(MorphicDsp, need)
→ candidate implementation
→ AngrySphinx gate
→ (gate pass) → execute or refuse
→ receipt
→ amplitude/topology update
```

**Key Distinction:**
- Collapse: Selection of implementation from superposition/basis
- Permission: Authorization to execute selected implementation
- Collapse is necessary but not sufficient for execution

---

## Morphic DSP Formal Model

### Virtual Morphic DSP (Immediate Target)

```lean
MorphicDsp(t) =
  superposed operation basis
+ boundary state (virtual)
+ adaptive topology (logical)
+ resource envelope
+ receipt path
+ AngrySphinx gates
```

### Collapse Flow

```lean
collapse(MorphicDsp, need)
→ candidate implementation
→ AngrySphinx gate check
→ if gate pass:
    → execute implementation
    → receipt generation
    → amplitude/topology update
→ if gate fail:
    → refuse execution
    → maintain current state
```

---

## Morphic DSP FPGA Implementation

### Virtual Morphic DSP on FPGA (Immediate Target)

**Target Hardware: Gowin GW1NR-9 (Tang Nano 9K)**
- 8,640 LUT4 cells
- 27 MHz clock
- 720KB BRAM (30 x 24Kb blocks)
- No DSP slices (Gowin architecture uses LUT-based multipliers)

**Acoustic Sensor: MEMS Microphone (SPH0645)**
- Metal-lid MEMS microphone
- I2S/PDM digital output interface
- Role: Resonant cavity / acoustic waveguide
- Provides audio input for morphic DSP pattern matching

**Hardware Composition:**
```
LUT fabric (8,640 cells)
+ Routing fabric (dynamic interconnect)
+ Control FSM (state machine)
+ Morphic scalar amplitudes (Q16.16)
+ Receipt gates (audit trail)
+ BRAM partial LUT (adaptive storage)
+ MEMS microphone interface (I2S/PDM)
= Virtual Morphic DSP (Gowin GW1NR-9)
```

**Implementation Strategy:**
- Use LUTs for multiplication (Gowin has no DSP slices)
- Reconfigure routing via control FSM
- Use LUTs to implement adaptive logical interconnect
- Use BRAM partial LUT for adaptive storage (pattern matching, weights, thresholds)
- Integrate MEMS microphone (SPH0645) via I2S/PDM interface
- Use audio input for pattern matching and OEPI calculation
- Compose operations from basis (multiply, accumulate, etc.)
- Emulate boundary fluidity via resource pooling
- AngrySphinx gates implemented in control logic

**BRAM Partial LUT Architecture:**
- BRAM stores adaptive pattern matching thresholds and weights
- Morphic scalar amplitudes update BRAM entries dynamically
- Enables runtime weight updates (unlike fixed LUTs)
- 1024-entry lookup table (10-bit address, 32-bit Q16.16 data)
- Write enable for partial updates
- 1-2 cycle lookup latency
- Gowin GW1NR-9 has 720KB BRAM (30 x 24Kb blocks)

**Capabilities:**
- [BEAUTIFUL_PROVISIONAL - Self-reconfiguring logical structure (via routing + LUTs) - requires FPGA synthesis evidence]
- [BEAUTIFUL_PROVISIONAL - Fluid boundaries (virtual merge/split via resource allocation) - requires implementation evidence]
- [BEAUTIFUL_PROVISIONAL - Composable operation basis (not infinite) - requires formal specification evidence]
- [BEAUTIFUL_PROVISIONAL - Adaptive topology (logical interconnect reconfiguration) - requires routing reconfiguration evidence]
- [BEAUTIFUL_PROVISIONAL - Scalar collapse with AngrySphinx gates - requires gate implementation evidence]
- [BEAUTIFUL_PROVISIONAL - Adaptive pattern matching via BRAM partial LUT - requires pattern matching evidence]
- [BEAUTIFUL_PROVISIONAL - Dynamic weight updates via BRAM writes - requires BRAM write evidence]
- [factual - LUT-based multiplication (no DSP slices on Gowin) - Gowin architecture documented]
- [factual - Audio input processing via MEMS microphone (SPH0645) - hardware interface documented]
- [BEAUTIFUL_PROVISIONAL - Acoustic pattern recognition for morphic scalar state - requires pattern recognition evidence]

**Limitations:**
- Not true physical self-modification (logical reconfiguration only)
- FPGA has fixed routing (limited runtime reconfiguration)
- No DSP slices (multiplication via LUTs, slower)
- Bit-width adaptation limited (time-multiplexing, not true variable width)
- BRAM lookup slower than pure LUT (1-2 cycles vs 1 cycle)
- Limited BRAM write bandwidth

### True Morphic DSP on FPGA (Long-Term Target)

**Hardware Requirements:**
- **Reconfigurable Logic Blocks:** DSP slices must be reconfigurable at structural level
- **Dynamic Interconnect:** Routing must be runtime-reconfigurable
- **Bit-Width Adaptation:** Multipliers must support variable bit-width
- **Pipeline Adaptation:** Pipeline depth must be adjustable
- **Self-Organization:** Hardware must support emergent topology

**Target Hardware:**
- **Lattice ECP5:** Larger device with more routing resources
- **Xilinx UltraScale+:** Advanced DSP with reconfigurable pipeline
- **Intel Agilex:** Adaptive DSP blocks
- **Custom ASIC:** True morphic DSP (beyond FPGA)

---

## Morphic DSP Applications

### 1. Adaptive Signal Processing
[BEAUTIFUL_PROVISIONAL - Applications are conceptual without implementation evidence]
- DSP adapts structure to signal characteristics [conceptual - requires adaptation algorithm evidence]
- Multiplier becomes filter for low-frequency signals [conceptual - requires reconfiguration evidence]
- Multiplier becomes FFT for spectral analysis [conceptual - requires FFT implementation evidence]
- Self-optimizing for each signal type [conceptual - requires optimization algorithm evidence]

### 2. Energy-Efficient Computing
[BEAUTIFUL_PROVISIONAL - Applications are conceptual without power measurement evidence]
- DSP splits into smaller units for low-power processing [conceptual - requires power measurement evidence]
- DSP merges for high-performance processing [conceptual - requires performance benchmark evidence]
- Resource allocation adapts to energy constraints [conceptual - requires energy optimization evidence]
- Self-scaling computation [conceptual - requires scaling algorithm evidence]

### 3. Fault Tolerance
[BEAUTIFUL_PROVISIONAL - Applications are conceptual without fault injection evidence]
- DSP can reconfigure around faulty components [conceptual - requires fault detection evidence]
- Boundary fluidity enables graceful degradation [conceptual - requires degradation analysis evidence]
- Self-healing through structural adaptation [conceptual - requires healing mechanism evidence]
- Emergent redundancy [conceptual - requires redundancy emergence evidence]

### 4. Neuromorphic Computing
[BEAUTIFUL_PROVISIONAL - Applications are conceptual without neural implementation evidence]
- DSP structure adapts to neural network topology [conceptual - requires neural adaptation evidence]
- Synaptic weights become fluid connections [conceptual - requires synaptic plasticity evidence]
- Spike-timing-dependent plasticity in hardware [conceptual - requires STDP implementation evidence]
- Self-organizing neural networks [conceptual - requires self-organization evidence]

---

## Morphic DSP Mathematical Model

[BEAUTIFUL_PROVISIONAL - Mathematical model uses quantum-inspired notation as metaphor; does not imply actual quantum computing capabilities. This is a conceptual formalism without physical quantum evidence.]

### Superposition State

DSP operation in superposition:
```
|ψ⟩ = Σ_i a_i |mode_i⟩
```

Where:
- `|ψ⟩` is the DSP superposition state [conceptual - quantum-inspired metaphor]
- `a_i` is the amplitude (probability weight) of mode i [conceptual - Q16_16 representation]
- `|mode_i⟩` is a specific DSP operation mode [conceptual - mode enumeration]
- `Σ_i |a_i|² = 1` (normalization) [conceptual - requires normalization implementation]

### Collapse Operation

Measurement collapses superposition:
```
|ψ⟩ → |mode_k⟩ with probability |a_k|²
```

Where:
- Collapse is triggered by scalar measurement [conceptual - requires measurement mechanism evidence]
- `k` is selected based on amplitude probabilities [conceptual - requires selection algorithm evidence]
- Result is deterministic operation mode [conceptual - requires determinism guarantee evidence]

### Boundary Fluidity

DSP boundary state evolution:
```
∂(boundary)/∂t = f(computation_needs, resource_constraints)
```

Where:
- Boundary state evolves continuously [conceptual - requires evolution mechanism evidence]
- Driven by computation needs and resource constraints [conceptual - requires constraint satisfaction evidence]
- Enables dynamic merge/split operations [conceptual - requires operation evidence]

### Topology Adaptation

DSP topology reconfiguration:
```
topology(t+1) = adapt(topology(t), signal_characteristics(t))
```

Where:
- Topology adapts to signal characteristics [conceptual - requires adaptation algorithm evidence]
- Continuous optimization of interconnect [conceptual - requires optimization evidence]
- Emerges from local interaction rules [conceptual - requires emergence evidence]

---

## Morphic DSP Lean Implementation

### Core Types

```lean
/-- Morphic DSP entity. -/
structure MorphicDsp where
  dspId : Nat
  superposedOps : Array (Q16_16 × DspMode)
  collapsedOp : Option (Q16_16 × DspMode)
  boundaryState : BoundaryState
  topology : DspTopology

/-- DSP boundary state. -/
inductive BoundaryState where
  | independent
  | merged
  | split
  | fluid

/-- DSP topology. -/
structure DspTopology where
  connections : Array (Nat × Nat)
  bandwidth : Array Q16_16
  latency : Array Q16_16
```

### Core Operations

```lean
/-- Collapse superposition. -/
def collapseDspSuperposition (dsp : MorphicDsp) (measurement : DspMode) : MorphicDsp

/-- Merge DSP slices. -/
def mergeDspSlices (dsp1 dsp2 : MorphicDsp) : MorphicDsp

/-- Split DSP slice. -/
def splitDspSlice (dsp : MorphicDsp) (splitRatio : Nat) : Array MorphicDsp

/-- Adapt topology. -/
def adaptDspTopology (dsp : MorphicDsp) (needs : ComputationNeeds) : MorphicDsp
```

---

## Keeper Law

**Core Principle:**
A controlled DSP changes modes. A morphic DSP changes what kind of worker it is. A safe morphic DSP still asks permission before it works.

**Sharper Formulation:**
The DSP may collapse into function. It may not collapse into authority.

**Implications:**
1. **Collapse ≠ Permission:** Selecting implementation does not authorize execution
2. **Function ≠ Authority:** DSP can change function, not authority
3. **Permission Required:** Execution always requires gate passes
4. **Receipt Mandatory:** All executions must generate receipt

**Safety Guarantee:**
Even a morphic DSP with self-reconfiguring structure must:
- Check AngrySphinx gates before execution
- Maintain receipt path for auditability
- Respect resource and thermal bounds
- Preserve semantic precision

---

## Morphic DSP vs Current Work

### Current Work (Controlled DSP - Layer 1)
- DSP slices are reconfigurable (6 modes)
- Controlled by external morphic scalar
- OEPI-based allocation
- Fixed hardware structure
- **Status:** Implemented in MorphicDSP.lean

### Next Evolution (Virtual Morphic DSP - Layer 2)
- DSP pool with self-reconfiguring logical structure
- Fluid boundaries via resource pooling
- Composable operation basis (not infinite)
- AngrySphinx gates for safety
- Adaptive logical topology
- **Status:** Design complete, Lean implementation pending

### Long-Term Target (True Morphic DSP - Layer 3)
- DSP slices are morphic entities
- Physical self-modifying structure
- Physical fluid boundaries
- Quantum-inspired superposition
- Adaptive physical topology
- Self-organization
- **Status:** Conceptual, requires custom hardware

---

## Conclusion

The morphic DSP concept must be understood in three distinct layers:

**Layer 1: Controlled DSP (Current)**
- Fixed DSP slices with mode selection
- External control by morphic scalar
- Implemented and ready for FPGA deployment

**Layer 2: Virtual Morphic DSP (Immediate Target)**
- Self-reconfiguring logical structure via DSP pool + LUTs
- Fluid boundaries via resource pooling
- Composable operation basis with AngrySphinx gates
- Buildable on current FPGA hardware
- **Key principle:** Collapse is not permission

**Layer 3: True Morphic DSP (Long-Term Target)**
- Physical self-modifying structure
- Physical fluid boundaries
- Quantum-inspired superposition
- Requires custom ASIC or future FPGA

The immediate path forward is **Virtual Morphic DSP**: create a morphic-looking DSP pool using current FPGA resources (DSP slices + LUT fabric + routing fabric + control FSM + morphic scalar + receipt gates). This provides morphic behavior without requiring custom hardware, while maintaining safety through AngrySphinx gates and the keeper law: "The DSP may collapse into function. It may not collapse into authority."
