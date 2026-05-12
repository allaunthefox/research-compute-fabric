# High-Temperature Graphene Memristor Prior

Status: `EXTERNAL_REFERENCE_WITH_HARDWARE_PRIOR`

Sources:

- Physics World: `https://physicsworld.com/a/memory-device-breaks-high-temperature-performance-record/`
- ScienceDaily summary: `https://www.sciencedaily.com/releases/2026/04/260406192904.htm`
- Science paper mirror/metadata: `https://www.lifescience.net/entries/857827/high-temperature-memristors-enabled-by-interfacial/`

## Observed External Claim

The reported device is a high-temperature memristor using a layered stack:

```text
tungsten top electrode
hafnium oxide / HfOx switching layer
graphene bottom electrode
```

Reported performance from the external summaries:

```text
operating temperature: above 700 C
data retention: more than 50 hours at high temperature
endurance: more than 10^9 switching cycles
working voltage: about 1.5 V
switching speed: tens of nanoseconds
ON/OFF current ratio: greater than 10^3
```

The important mechanism is not merely "hot memory." It is interfacial
engineering: the graphene boundary appears to prevent the high-temperature
failure route seen when tungsten diffuses into a bottom electrode and leaves the
device stuck in one conductive state.

## Stack Mapping

For Research Stack, this is a hardware prior for thermal-stable state:

```text
thermal stress
  -> interface diffusion risk
  -> stable boundary layer
  -> nonvolatile state retention
  -> replayable hot-state memory cell
```

The useful abstraction is:

```text
thermal-stable memory = state cell whose boundary prevents destructive
                        material migration under heat
```

That maps to existing stack language as:

| Device term | Stack mapping |
|---|---|
| Memristor state | Nonvolatile route/state cell |
| HfOx switching layer | Resistive transition manifold |
| Graphene interface | Diffusion/quarantine boundary |
| Tungsten electrode | High-temperature drive/contact layer |
| ON/OFF ratio | Readout separation / state distinguishability |
| Retention at 700 C | Thermal persistence receipt |
| Endurance cycles | Replay count / write-stability receipt |

## Why It Helps

This prior is relevant to:

- FPGA/ASIC decompressor targets that may later want nonvolatile local state.
- Static decompressor devices where tiny replay state must survive harsh
  conditions.
- Memristive in-memory compute as a possible future matrix/kernel substrate.
- Thermal-stress modeling for hardware route cells.
- Claim-boundary language around "memory as physical state," not just RAM.

It also complements the Rust OISC decompressor target:

```text
Lean finite-state law
  -> Rust reference replay
  -> hardware lowering target
  -> thermal-stable nonvolatile memory prior
```

## Receipt Requirements Before Promotion

Minimum future receipt fields:

```text
device_stack
temperature_profile
retention_time
switching_cycles
read_voltage
write_voltage
ON_OFF_ratio
state_error_rate
thermal_cycle_count
array_size
peripheral_circuit_temperature
packaging_temperature
measurement_source
```

For stack-internal use, any hardware projection must also include:

```text
state_encoding
readout_threshold
write_protocol
replay_hash
negative_controls
failure_mode
```

## HOLD Boundary

Allowed:

- Keep as an external hardware prior.
- Use as a design analogy for thermal-stable nonvolatile route cells.
- Use the interfacial-engineering mechanism as a boundary/quarantine analogy.

HOLD:

- Product-ready memory.
- Large-array yield.
- Integration with CMOS peripheral circuits at 700 C.
- Packaging, thermal cycling, radiation, or Venus/deep-well readiness.
- In-memory AI acceleration claims.
- Any Research Stack hardware promotion.

Decision:

```text
ADMIT_REFERENCE_HOLD_DEVICE_PROMOTION
```
