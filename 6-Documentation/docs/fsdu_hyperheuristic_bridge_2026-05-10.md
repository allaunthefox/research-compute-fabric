# FSDU Hyper-Heuristic Bridge

Status: `ADMIT_FSDU_BRIDGE_RECEIPT`

Claim boundary: this is a receipt projection from the existing
hyper-heuristic orchestrator demo metrics into the FSDU dual-map scar surface.
It is not a live path optimality proof, not a compression claim, not a hardware
claim, and not a replacement for the Lean FSDU scaffold.

## Anchors

```text
Lean anchor:   2-Search-Space/FAMM/FAMM_FSDU.lean
Theory anchor: 2-Search-Space/FAMM/docs/FSDU_theory.md
Input receipt: 4-Infrastructure/shim/hyper_heuristic_orchestrator_receipt.json
Bridge script: 4-Infrastructure/shim/fsdu_hyperheuristic_bridge.py
Bridge receipt: 4-Infrastructure/shim/fsdu_hyperheuristic_bridge_receipt.json
Stack mirror: shared-data/data/stack_solidification/fsdu_hyperheuristic_bridge_receipt.json
```

## Equation Surface

```text
X_t = (M_a, M_b, S_a, S_b, Theta)
DeltaS_t = S_a - S_b
commit allowed iff ||DeltaS_t|| <= epsilon
```

The bridge projects each orchestrator component into:

```text
ahead_scar  = (1 - success_rate) * total_operations + 0.01 * heuristic_count
behind_scar = (1 - success_rate) * total_operations * success_rate
scar_delta  = ahead_scar - behind_scar
```

This is a deterministic accounting projection. It is not a physical scar
measurement and not a proof that a live solver path is admissible.

## Static Bridge Result

```text
epsilon: 1.25
component count: 5
max abs scar delta: 1.223152
decision: ADMIT_FSDU_BRIDGE_RECEIPT
```

Per-component projection:

| Component | Success rate | Ops | Ahead scar | Behind scar | Abs delta | Decision |
|---|---:|---:|---:|---:|---:|---|
| FAMM_DELAY | 0.815 | 20 | 3.73 | 3.0155 | 0.7145 | COMMIT_ALLOWED |
| PIST_MOVE | 0.771 | 15 | 3.465 | 2.648385 | 0.816615 | COMMIT_ALLOWED |
| SHIM_SELECTION | 0.718 | 12 | 3.414 | 2.429712 | 0.984288 | COMMIT_ALLOWED |
| GPU_SCHEDULING | 0.771 | 15 | 3.475 | 2.648385 | 0.826615 | COMMIT_ALLOWED |
| FPGA_BUILD | 0.686 | 12 | 3.808 | 2.584848 | 1.223152 | COMMIT_ALLOWED |

The FPGA build component is closest to the envelope. That makes it the first
candidate for retuning if epsilon is tightened or if live metrics increase scar
pressure.

## Live Follow-Up

The next gate has been run:

```text
script: 4-Infrastructure/shim/fsdu_live_hyperheuristic_probe.py
receipt: 4-Infrastructure/shim/fsdu_live_hyperheuristic_probe_receipt.json
decision: HOLD_LIVE_SCAR_DIVERGENCE
max abs scar delta: 14.392819767
worst component: fpga_build
```

This confirms the bridge was useful: static demo metrics admitted, while the
seeded live software snapshot refused commitment under the FSDU gate.

## Next Gate

The next meaningful step is:

```text
wire live orchestrator state snapshots into the same FSDU fields
```

That has now been completed by the live probe. The remaining work is a seed
sweep and retune pass, not a claim promotion.
