# TangNano9K Topology Router Testbench Receipt

Status: V_scope / hardware-parity testbench source
Authority: uploaded Verilog testbench text; not full hardware calibration
Related:

- `docs/gcl/SurfMCPFusionGate.md`
- `docs/gcl/AVMFixedPointComplianceRemediation.md`
- `docs/gcl/ThreeLayerBuilderJudgeWardenGate.md`
- `docs/gcl/FederatedNanokernelSwarmDoctrine.md`
- `docs/gcl/RunawayDigitalCellDivisionDoctrine.md`

## Purpose

This document records the uploaded Verilog testbench for `TangNano9KTopologyRouter` as a scoped hardware-parity receipt.

It advances the hardware parity track from pure prose toward executable simulation evidence, but it does not by itself prove AVM calibration, FPGA parity, or formal correctness.

## Source summary

The uploaded artifact is a Verilog testbench:

```text
TangNano9KTopologyRouter_tb
```

It simulates five virtual Tang Nano 9K router instances with distinct topology/manifold inputs.

The testbench instantiates five DUTs:

```text
TangNano9KTopologyRouter dut[0..4]
```

and drives each board with:

```text
muBin
rhoBin
cBin
mBin
neBin
sigmaBin
eventSource
lawful
bindCost
basinDepth
rimStrength
totalPull
boundaryFluidity
criticalScore
coherence
aliasDetected
```

Outputs observed:

```text
genomeAddr
genomeBucket
routingTarget
connectorCost
potentialRegime
potentialStability
aluOverflow
led
```

Clock:

```text
always #18.5 clk = ~clk;  // approximately 27 MHz
```

## Fixed-point compliance note

The numeric inputs are represented as 32-bit fixed-point constants consistent with Q16.16 usage.

Examples:

```text
0x00010000 = 1.0
0x00008000 = 0.5
0x00020000 = 2.0
0x00030000 = 3.0
0x00040000 = 4.0
```

This is consistent with the AVM fixed-point remediation direction:

```text
float-free core route semantics
Q16_16-style scalar representation
bit-oriented Verilog test surface
```

## Five virtual board scenarios

### Board 0: baseline lawful swarm node

```text
eventSource = swarm
lawful = true
expected routingTarget = 2 / swarm_nodes
expected genomeAddr = 0x14138
expected genomeBucket = 2
expected connectorCost = 0x00010002
```

### Board 1: unlawful swarm work queue

```text
eventSource = swarm
lawful = false
high bind/rim/critical pressures
expected routingTarget = 3 / swarm_work_queue
expected led_critical = 1
```

### Board 2: ENE package routing

```text
eventSource = ene
lawful = true
expected routingTarget = 0 / ene_packages
```

### Board 3: collapsed alias-detected state

```text
aliasDetected = true
expected potentialRegime = 5 / collapsed
expected potentialStability = 3 / collapseProne
expected led_stable = 0
```

### Board 4: RGFlow manifest

```text
eventSource = rgflow
lawful = true
expected routingTarget = 1 / swarm_manifest
```

## Assertion coverage

The testbench checks:

```text
routing target selection
collapsed-state regime selection
collapse-prone stability selection
genome address calculation
genome bucket calculation
connector cost calculation
critical LED behavior
stable LED behavior under alias collapse
```

## What this receipt supports

Allowed claim:

```text
A scoped Verilog simulation testbench exists for the TangNano9K topology router covering five virtual board scenarios and checking route, genome, cost, regime, stability, and LED outputs.
```

Allowed claim:

```text
The testbench uses Q16.16-style constants, aligning the hardware route surface with the AVM fixed-point remediation direction.
```

Allowed claim:

```text
This artifact contributes to the hardware-parity receipt chain required by the Surf MCP fusion gate.
```

## What this receipt does not prove

Blocked claims:

```text
This proves AVM is CALIBRATED.
This proves Lean/Python/Verilog bit-exact equivalence.
This proves FPGA hardware parity.
This proves the router is safe against malformed packet ingress.
This proves metastability containment.
This proves UART copy/write safety.
This proves the Hyper Equation.
```

## Missing receipts before hardware parity promotion

Still required:

```text
1. The actual `TangNano9KTopologyRouter.v` DUT source.
2. Simulator run log showing all assertions passing.
3. Waveform or trace artifact for the five board cases.
4. AVM reference trace for the same inputs.
5. State-hash comparison between AVM and Verilog.
6. UART ingress testbench if packet interface is added.
7. Partial-commit rejection test.
8. Metastability boundary documentation for external inputs.
9. FPGA synthesis/place/route receipt if targeting actual Tang Nano 9K hardware.
```

## Promotion impact

This moves one hardware parity requirement from missing to partially satisfied:

```text
hardware-parity test plan/log: PARTIAL / testbench source present
```

But AVM remains:

```text
HOLD / CLAIM_BUNDLE_PENDING_RECEIPTS
```

until the complete receipt chain is present.

## Operating sentence

```text
The TangNano9K topology router testbench is a scoped hardware-parity receipt: it exercises five virtual router boards with Q16.16-style manifold inputs and asserts routing, genome, cost, regime, stability, and LED behavior, but it remains a simulation source artifact until paired with the DUT source, passing run logs, AVM reference traces, and hardware or synthesis receipts.
```
