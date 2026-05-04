# SNN / NII / RGFlow / FAMM Test Harness

Imported 2026-04-24 from external triage pack. Calibration fixes applied
on import — see "Calibration deltas" below.

## Layout

- [snn_nii_reference.py](snn_nii_reference.py) — deterministic Python reference. Pipeline:
  `predict → nii_step (clamp + bounded Δw + decay) → msnn_step (LIF + FAMM-modulated drive) → rgflow_step (3-verdict) → famm_update (saturating + exp decay)`.
  Writes per-record JSONL with SHA-tagged hash for golden-vector compare.
- [generate_snn_vectors.py](generate_snn_vectors.py) — 4-phase synthetic stream
  (stable / drift / repeated bad / near-miss osc) OR pulls from a
  `uc_records.jsonl` topology18 stream.
- [snn_test_config.json](snn_test_config.json) — Q8 fixed-point + thresholds.
- RTL siblings live at [4-Infrastructure/hardware/tangnano9k/rtl/](../../hardware/tangnano9k/rtl/) and must
  bit-match this Python reference.

## Quick start

```bash
python generate_snn_vectors.py --out vectors.jsonl --n 256
python snn_nii_reference.py --vectors vectors.jsonl --config snn_test_config.json --out results.jsonl --summary summary.json
```

The reference prints a pass/fail JSON to stdout. All four flags must be
true for the run to count: `bounded_nii`, `all_verdicts_present`,
`famm_unsaturated`, and any custom hardware-equivalence check.

## Calibration deltas (vs upstream pack)

The upstream harness produced a misleading `pass_fail: famm_updated: True`
when FAMM was actually pegged at 255 across all three counters from i≈40
onward — half the run was testing a dead controller. Fixes applied on
import:

1. **Exponential FAMM decay** (`decay_q8 = 232 ≈ 9.4%/step`). Replaces
   the upstream linear `-1/step` on lawful-only. Time constant ~10 steps,
   so phase 2's 64 consecutive heavy rejects can saturate momentarily but
   recover before phase 3.
2. **Reduced reject contribution** (`rp/8` and `rp/16` instead of `rp/4`
   and `rp/8`). Even with decay, the upstream scaling drove phase 2 to
   saturation in ~5 events.
3. **Widened near-miss band** (`32 → 48`). Upstream produced 0/256
   near-miss events.
4. **Saturation surfaces as failure** (`famm_unsaturated`,
   `famm_saturation_steps`, `final_famm` now in pass/fail JSON). Failure
   contract: silent saturation is unacceptable, must be observable.

Verified end-to-end after fixes: 189 lawful / 1 near-miss / 66 reject,
no counter saturated >25% of the run, max abs surprise 359 ≤ NII clip 384.

## Known follow-ups

- Synthetic generator phase 3 produces only 1 near-miss event in 64
  steps — the σ corridor `[262, 293]` is too narrow for the current
  amplitude swings. Either re-tune phase 3 amplitudes or add a fifth
  phase explicitly designed for the near-miss band.
- RTL `nii_core.v` uses a one-tap `obs - prev_obs` predictor; the Python
  reference uses 4 weighted delay taps. They will not bit-match until
  the RTL is upgraded.
