# Morphic Neural Network Router

Low-level adaptive routing between LUT admission and GCL codons.

## Architecture Position

```
surface shell (UDP/onion/Ethernet/serial/ipv923u)
  ↓
scale-invariant 1D scalar
  ↓
LUT admission (ultra-compressed codon lookup)
  ↓
MNN routing layer (adaptive path formation)
  ↓
GCL codon/action (lawful state transition)
```

## Key Features

- **Morphic routing**: Adapts based on historical outcomes
- **Goal-aware**: Routes based on packet goal (health, attest, compress, route, recover)
- **State-constrained**: Considers memory, CPU, recovery mode, trust score
- **Carrier-agnostic**: Works with any shell (UDP, Ethernet, onion, serial, future protocols)
- **Cost-aware**: Minimizes energy, time, and bandwidth cost

## Usage

```python
from mnn_router import MorphicRouter, ScalarInput, NodeState, CarrierMetrics

router = MorphicRouter(max_history=16)

scalar = ScalarInput(domain=1, scalar=10)  # attest operation
state = NodeState(
    memory_budget_mb=715,
    memory_used_mb=100,
    cpu_load=0.3,
    recovery_mode=False,
    trust_score=0.9,
    uptime_seconds=3600,
)
carrier = CarrierMetrics(
    shell="ethernet",
    latency_ms=1.0,
    loss_rate=0.0,
    bandwidth_kbps=100000,
    encrypted=False,
)

decision = router.route_with_adaptation(scalar, state, carrier)
print(f"Action: {decision.action}")
print(f"GCL Codon: 0x{decision.gcl_codon:02X}")
print(f"Reason: {decision.reason}")

# Update history after execution
router.update_history("attest", state, carrier, success=True)
```

## Build and Test

```bash
make test
```

## Memory Constraints

For 8 KB RAM targets, the MNN uses:
- Pre-allocated routing tables (no dynamic allocation)
- Coarse-grained state signatures (3-bit quantization)
- Tiny history cache (last 16 entries)
- Fixed-point arithmetic (Q8.8 or Q16.16)

## Integration

See IBM II controller integration example in `../ibmii/ibmii_mnn_controller.py`.

## Spec

See `../../docs/specs/MORPHIC_NEURAL_NETWORK_ROUTING_SPEC.md`.
