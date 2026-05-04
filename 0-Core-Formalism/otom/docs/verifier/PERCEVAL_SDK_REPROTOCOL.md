# Perceval SDK Reproduction Protocol — GSP D_perceval_local Failure

Status: `PERCEVAL_REPRO_PENDING`

Purpose: reproduce the `D_perceval_local` over-damping failure from first principles against upstream Perceval SDK behavior, rather than relying on the existing local wrapper or agent assertions.

## Why this exists

The verifier-grounded audit found:

```text
B_constant_baseline G1 max-rel: 0.3043
D_perceval_local    G1 max-rel: 0.3078
```

The local Perceval witness was worse than the constant-viscosity baseline for the audited IC and `ν0 = 0.01`. The likely mechanism was:

```text
Ω_Q too large
→ ν_eff = ν0 · (1 + β Ω_Q) too high
→ over-dissipation
→ G1 reference-cosim error worse than baseline
```

This protocol tests whether that behavior comes from:

1. the upstream Perceval SDK semantics,
2. local wrapper/version drift,
3. circuit/exhaust-map design,
4. witness normalization/scaling,
5. or the verifier adapter.

## External SDK facts to pin in the report

Perceval is Quandela's open-source framework for programming photonic quantum computers. Its upstream repository is:

```text
https://github.com/Quandela/Perceval
```

The PyPI package is:

```text
perceval-quandela
```

Quandela's installation path is:

```bash
pip install --upgrade pip
pip install perceval-quandela
```

Perceval supports linear-optical circuit construction, Fock-state manipulation, simulation backends, and cloud/QPU interfaces. Do not treat Perceval as the claim under test. The claim under test is our witness construction.

## Repro environments

Use three environments:

```text
.venv-existing      existing local project environment
.venv-perceval-pip  clean pip wheel install
.venv-perceval-src  editable upstream source checkout
```

### pip wheel environment

```bash
mkdir -p ~/perceval-repro
cd ~/perceval-repro
python3.13 -m venv .venv-perceval-pip
source .venv-perceval-pip/bin/activate
python -m pip install --upgrade pip
python -m pip install perceval-quandela numpy scipy pytest
python - <<'PY'
import perceval as pcvl
print('perceval_version=', getattr(pcvl, '__version__', 'unknown'))
print('perceval_file=', getattr(pcvl, '__file__', 'unknown'))
PY
```

### source checkout environment

```bash
mkdir -p ~/perceval-repro
cd ~/perceval-repro
git clone https://github.com/Quandela/Perceval.git perceval-source
python3.13 -m venv .venv-perceval-src
source .venv-perceval-src/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ./perceval-source numpy scipy pytest
python - <<'PY'
import perceval as pcvl
print('perceval_version=', getattr(pcvl, '__version__', 'unknown'))
print('perceval_file=', getattr(pcvl, '__file__', 'unknown'))
PY
```

## Frozen test object

Triad state:

```text
a = (a1, a2, a3) = (1.0, 0.3, 0.1)
```

Fixed constants:

```text
ν0 = 0.01
β  = 0.5
M  = 6
exhaust_modes = (3, 4, 5)
n_samples = 128 or 256
seed = 42
```

Expected failure signature, if reproduced:

```text
Ω_Q ≈ large enough to push ν_eff above baseline
ν_eff > ν0
energy dissipation magnitude > baseline
G1 max-rel >= 0.3043
```

## Required outputs

Each environment must emit JSON with this shape:

```json
{
  "schema": "perceval_omega_repro_v0_1",
  "environment_label": "pip|source|existing",
  "python_version": "...",
  "perceval_version": "...",
  "perceval_file": "...",
  "input_state": [1.0, 0.3, 0.1],
  "M": 6,
  "exhaust_modes": [3, 4, 5],
  "n_samples": 128,
  "seed": 42,
  "omega_q": 0.0,
  "nu0": 0.01,
  "beta": 0.5,
  "nu_eff": 0.01,
  "omega_floor_candidate": null,
  "verdict": "REPRODUCED|NOT_REPRODUCED|SDK_API_MISMATCH|SCRIPT_ERROR"
}
```

## Gate interpretation

`REPRODUCED` means:

```text
upstream SDK + frozen witness construction produces large Ω_Q / over-damping signature
```

Then the likely bug is our witness construction or scaling, not Perceval.

`NOT_REPRODUCED` means:

```text
clean SDK behavior does not match local wrapper failure
```

Then the likely bug is local wrapper drift, version drift, sampling setup, or circuit construction.

`SDK_API_MISMATCH` means:

```text
Perceval public API changed enough that the reproducer needs an adapter update
```

This is not a physics result.

## No-promotion rule

Do not create `D2/D3/D4` tuning variants until this repro pass is complete.

Correct order:

```text
1. reproduce D_perceval_local failure under clean SDK
2. isolate cause: SDK / wrapper / circuit / witness / scaling
3. freeze report
4. then build normalized / centered / classifier Perceval variants
```

## Claim boundary

Safe:

> We are testing whether the current Perceval witness construction reproduces the verifier-observed over-damping failure under clean SDK conditions.

Unsafe:

> Perceval is broken, Quandela is broken, photonics cannot work, or Variant D can be repaired before reproducing the failure.
