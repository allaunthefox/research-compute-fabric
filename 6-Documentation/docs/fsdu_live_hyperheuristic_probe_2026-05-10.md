# FSDU Live Hyper-Heuristic Probe

Status: `HOLD_LIVE_SCAR_DIVERGENCE`

Claim boundary: this is a seeded live software snapshot of the Python
hyper-heuristic orchestrator projected into the FSDU scar-differential surface.
It is not a live path optimality proof, not hardware evidence, and not a
compression claim.

## What Changed

The static bridge receipt used existing demo metrics. This probe executes the
orchestrator in-process, records actual heuristic outcomes, and then projects
those live events into:

```text
X_t = (M_a, M_b, S_a, S_b, Theta)
DeltaS_t = S_a - S_b
commit allowed iff ||DeltaS_t|| <= epsilon
```

The orchestrator was also repaired so returned heuristic results can mark
`success: false`; a Python function returning without exception is no longer
treated as automatic success.

## Receipts

```text
script: 4-Infrastructure/shim/fsdu_live_hyperheuristic_probe.py
receipt: 4-Infrastructure/shim/fsdu_live_hyperheuristic_probe_receipt.json
mirror: shared-data/data/stack_solidification/fsdu_live_hyperheuristic_probe_receipt.json
surface endpoint: /api/fsdu
```

## Result

```text
seed: 20260510
epsilon: 2.0
component count: 5
max abs scar delta: 14.392819767
decision: HOLD_LIVE_SCAR_DIVERGENCE
```

Per-component live scar projection:

| Component | Success rate | Avg cost | Ahead scar | Behind scar | Abs delta | Decision |
|---|---:|---:|---:|---:|---:|---|
| famm_delay | 0.7 | 3.2333333 | 8.303428046 | 4.361666665 | 3.941761381 | RETUNE_REQUIRED |
| pist_move | 0.466666667 | 3.866666667 | 9.875455956 | 3.926666667 | 5.94878929 | RETUNE_REQUIRED |
| shim_selection | 0.916666667 | 1.25 | 2.317819767 | 0.979166667 | 1.3386531 | COMMIT_ALLOWED |
| gpu_scheduling | 0.2 | 12.666666667 | 14.755455956 | 3.033333333 | 11.722122623 | RETUNE_REQUIRED |
| fpga_build | 0.0 | 24.0 | 15.592819767 | 1.2 | 14.392819767 | RETUNE_REQUIRED |

## Interpretation

The live run refused commitment, which is the correct FSDU behavior. The static
receipt bridge was near the envelope; the live software snapshot exceeded it.
The strongest scar pressure comes from `fpga_build`, then `gpu_scheduling`.

This does not mean the hardware failed. It means the current hyper-heuristic
software snapshot is too divergent to commit under `epsilon = 2.0`.

## Surface Integration

`/api/fsdu` now reads the live receipt when present and exposes:

```text
theta
divergence
epsilon
admissible
component scars
commit_gate
source receipt
```

The FSDU dashboard therefore shows the receipt-backed live scar state instead
of the old bootstrap mock when the live probe has been run.

## Next Gate

Run a small seed sweep and compare:

```text
seed -> max_abs_scar_delta -> worst component -> retune target
```

Only after repeated snapshots stay inside epsilon should the dashboard display
the state as admissible.
