# Getting Started — Sovereign Research Stack

Start here. Every command on this page is copy-pasteable and verified against the repo.

---

## 1. Prerequisites

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Lean 4 (via `elan`) | `v4.30.0-rc2` | `lean --version` |
| Python | 3.10+ | `python3 --version` |
| Git | 2.x | `git --version` |
| Node.js (optional) | 18+ | `node --version` |

## 2. Installation

### 2.1 Install Lean 4 via elan

```bash
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | bash
source ~/.bashrc
elan default leanprover/lean4:stable
```

Verify:

```bash
lean --version
# Lean (version 4.29.1, ...)
```

### 2.2 Clone the Repository

```bash
git clone <repo-url> Research-Stack
cd Research-Stack
```

### 2.3 Set the Lean Toolchain Version

The project pins Lean at `v4.30.0-rc2`. Make sure elan respects it:

```bash
cd 0-Core-Formalism/lean/Semantics
elan show
cd ../../..
```

`elan` should auto-detect `lean-toolchain` in the `Semantics/` directory and download the correct version when you run `lake build`.

### 2.4 Python Virtual Environment (Optional)

Only needed if you plan to run Python scripts that pull in packages (e.g., the swarm scripts, RG-flow filter, or PIST compression).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r 5-Applications/requirements_swarm_api.txt   # most scripts use this
```

### 2.5 Environment Variables

Copy the template and fill in what you need:

```bash
cp .env .env.local   # edit .env.local, it's gitignored
```

**Required** only if you use the corresponding feature:

| Variable | Needed For |
|----------|------------|
| `DEEPSEEK_API_KEY` | Swarm scripts calling DeepSeek |
| `QUANDELA_API_KEY` | Quantum compute backend |
| `WOLFRAM_ALPHA_APPID` | Math verification with Wolfram |
| `LINEAR_API_KEY` | Linear issue tracking integration |
| `NEO4J_*` | Graph database ingestion |
| others | Optional — ignore the placeholders |

**You can build and run Lean modules without setting any env vars.**

---

## 3. Build the Core (Lean Proofs)

The mathematical core lives in `0-Core-Formalism/lean/Semantics/`. It contains 3,500+ verified proofs.

```bash
cd 0-Core-Formalism/lean/Semantics
lake build
```

This compiles:

- `Semantics` — the main library (AVM, FixedPoint, orchestration, topology)
- `PIST` / `FAMM` / `ExtensionScaffold` / `Biology` — linked libraries
- Executables: `bindserver`, `searchserver`, `openworm_benchmark`, `moim_benchmark`, etc.

Expected output:

```
Build completed successfully. (takes ~1-2 minutes first time)
```

### What Gets Compiled

```
Semantics.lean              →  umbrella module
Semantics/FixedPoint.lean   →  Q0_16 & Q16_16 fixed-point arithmetic (no floats)
Semantics/FNWH/BurgersAVM.lean →  Burgers equation AVM programs with correctness proofs
Semantics/*.lean           →  orchestration, network, coupling, extraction layers
```

### Build the Static Binary (Optional)

```bash
make -C build-static
```

---

## 4. Run Tests

### 4.1 Lean Tests (`#eval` in the REPL)

Open any `.lean` file in VS Code (with the `lean4` extension) and evaluate expressions inline.

Example in `Semantics/FixedPoint.lean`:

```lean
#eval Semantics.FixedPoint.Q0_16.one
#eval Semantics.FixedPoint.Q16_16.add
  (Semantics.FixedPoint.Q16_16.ofFloat 3.14)
  (Semantics.FixedPoint.Q16_16.ofFloat 2.71)
```

Example in `Semantics/FNWH/BurgersAVM.lean` (run `SemanticsCli` or evaluate inline):

```lean
#eval Semantics.FNWH.BurgersAVM.kappa
```

Lean theorems serve as tests — if `lake build` passes, all 3,500+ proofs are verified.

### 4.2 Python Tests

No `pytest` harness is wired at the repo root. Most Python scripts are self-contained research harnesses. To run a few quick ones:

```bash
cd /home/allaun/CascadeProjects/Research-Stack

# Quick smoke test — PIST-GCL compression on synthetic data
python3 5-Applications/pist-scripts/pist_gcl_compression.py

# Run the end-to-end pipeline test
python3 5-Applications/scripts/end_to_end_pipeline_test.py

# Run the English manifold builder (compresses English via grammar shapes)
python3 5-Applications/scripts/redpajama_english_manifold.py
```

### 4.3 Lean Benchmarks

```bash
cd 0-Core-Formalism/lean/Semantics
lake exe openworm_benchmark
lake exe moim_benchmark
```

---

## 5. First Steps

### 5.1 Open a Lean File in VS Code

```
Project root: /home/allaun/CascadeProjects/Research-Stack
Lean entry:   0-Core-Formalism/lean/Semantics/
```

1. Install the **lean4** VS Code extension
2. Open the `Research-Stack/` folder in VS Code
3. Navigate to `0-Core-Formalism/lean/Semantics/Semantics.lean`
4. The Lean server starts automatically — you'll see the "Lean Infoview" pane

**Best files to open first:**

| File | What You'll See |
|------|----------------|
| `Semantics/FixedPoint.lean` | Q0_16 and Q16_16 hardware-native arithmetic. Zero floats. |
| `Semantics/FNWH/BurgersAVM.lean` | A verified AVM program for Burgers regularization. Correctness theorem. |
| `Main.lean` | The CLI entry point that ties everything together. |

### 5.2 Run `#eval` Examples

Place this at the bottom of `FixedPoint.lean` (or a scratch `test.lean`) and click "Evaluate" in the infoview:

```lean
open Semantics.FixedPoint

#eval Q0_16.one           -- prints the internal representation
#eval Q16_16.ofFloat 0.5  -- converts float to Q16_16
```

Or in `BurgersAVM.lean`:

```lean
open Semantics.FNWH.BurgersAVM

#eval kappa               -- 0.3547 as Q16_16
```

### 5.3 Run PIST-GCL Compression Demo

```bash
cd /home/allaun/CascadeProjects/Research-Stack
python3 5-Applications/pist-scripts/pist_gcl_compression.py
```

This runs a 4-layer manifold compression pipeline (PIST remap → cognitive routing → delta+Huffman → thermodynamic verify) on built-in test data. No dependencies beyond the Python stdlib.

### 5.4 Run the English Manifold Builder

```bash
cd /home/allaun/CascadeProjects/Research-Stack
python3 5-Applications/scripts/redpajama_english_manifold.py
```

Compresses English text via grammar-shape coordinates. Uses PIST under the hood.

---

## 6. Key Files to Read First

| File | Purpose |
|------|---------|
| `CONCEPTS.md` | Core concept quick-reference (FAMM, PIST, ENE, GWL, AVM, etc.) |
| `6-Documentation/EXPLANATION_FOR_HUMANS.md` | Plain-English translation of technical jargon |
| `6-Documentation/docs/AGENTS.md` | Strict LLM operating rules — the "one rule" philosophy |
| `5-Applications/hutter_prize/ARCHITECTURE.md` | System architecture overview |
| `6-Documentation/calculator_plain_math.md` | Proof everything fits on a high-school calculator |

**The most important rule (from AGENTS.md):**

> Lean is the source of truth. Everything else is a shim.

Python, Rust, and Verilog exist only as extraction targets. No logic lives outside Lean.

---

## 7. Common Issues

### Lake build fails with version mismatch

```
error: toolchain 'leanprover/lean4:v4.30.0-rc2' not installed
```

**Fix:** Run `lake build` from the `Semantics/` directory. `elan` reads `lean-toolchain` automatically and downloads the correct version:

```bash
cd 0-Core-Formalism/lean/Semantics
lake build   # triggers auto-download of v4.30.0-rc2
```

### `lean` not found in PATH

```bash
export PATH="$HOME/.elan/bin:$PATH"
source ~/.bashrc
```

Or reinstall elan:

```bash
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | bash -s -- -y
```

### `lake` not found

`lake` is bundled with Lean. If `lean --version` works but `lake` doesn't:

```bash
which lake
# should be ~/.elan/bin/lake
```

Reinstall elan if missing.

### Lake build stalls on external dependencies

First build pulls `mathlib4` and `sparkle` from GitHub. It can take ~5-10 minutes on a slow connection. Subsequent builds use the cached `.lake/` directory.

### Python module not found

Most scripts only need `requirements_swarm_api.txt`. If a specific script fails on import:

```bash
source .venv/bin/activate
pip install <missing-package>
```

### VS Code Lean Infoview is blank

1. Make sure you opened the `Research-Stack/` folder (not a subdirectory)
2. Check the Lean server status in the status bar
3. Open a `.lean` file inside `0-Core-Formalism/lean/Semantics/` to trigger the server
4. `lake build` once from the terminal first — it pre-caches olean files the server needs

### `sorry` in committed files

You may see `sorry` placeholders in WIP branches. These are intentional stubs for incomplete proofs. Do not remove them — they are tracked with `TODO(lean-port)` tickets and human sign-off per AGENTS.md rules.

---

## 8. Repository Map

```
Research-Stack/
├── 0-Core-Formalism/lean/Semantics/   ← Lean 4 proofs (the source of truth)
│   ├── Semantics.lean                 ← umbrella module
│   ├── Semantics/FixedPoint.lean      ← Q0_16, Q16_16 arithmetic
│   ├── Semantics/FNWH/                ← Burgers equation AVM
│   ├── Semantics/Core/               ← bind primitive, collapse engine
│   ├── Semantics/blackboard/         ← agent coordination surface
│   ├── Main.lean                     ← CLI entry point
│   └── lakefile.toml                 ← build configuration
├── 1-Distributed-Systems/            ← multi-node networking
├── 2-Search-Space/                   ← search algorithms, PIST, FAMM, manifold
├── 3-Mathematical-Models/            ← stored equation databases
├── 4-Infrastructure/                 ← hardware drivers, FPGA, GPU shims
├── 5-Applications/                   ← Python scripts (shims only — no logic)
│   ├── scripts/                      ← runnable scripts
│   └── pist-scripts/                 ← PIST-GCL compression demo
├── 6-Documentation/                  ← papers, docs, AGENTS.md
│   └── docs/AGENTS.md               ← LLM operating rules
├── CONCEPTS.md                       ← concept quick-reference
├── GETTING_STARTED.md                ← this file
└── .env                              ← secrets (gitignored)
```

---

## Quick-Reference Commands

```bash
# Build everything
cd 0-Core-Formalism/lean/Semantics && lake build

# Run PIST compression demo
python3 5-Applications/pist-scripts/pist_gcl_compression.py

# Run English manifold builder
python3 5-Applications/scripts/redpajama_english_manifold.py

# Run Lean benchmarks
cd 0-Core-Formalism/lean/Semantics && lake exe openworm_benchmark

# Check Lean version
lean --version
```
