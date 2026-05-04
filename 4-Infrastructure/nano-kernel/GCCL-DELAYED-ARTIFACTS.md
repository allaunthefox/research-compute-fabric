# GCCL Delayed Artifacts Manifest

Status: HOLD / workbench projection  
Created from ChatGPT artifact generation session after GCCL naming lock.

This manifest records the delayed artifacts that were generated locally before repository write access became available.

## Delayed artifacts

### 1. Full expanded GCCL / GCLang kernel module set

Local artifact name:

```text
gcl_kernel_modules_full_expanded.zip
```

SHA-256:

```text
60f84d6e6f310ccf458472f8aa5a1e085504a10c85432cb419196e4cbac6dfdb
```

Contents generated:

```text
00-gcl-prelude.gcl
01-bind-lawful-loss.gcl
02-nuvmap-kernel-integration.gcl
03-diat-shell-arithmetic.gcl
04-mass-number-kernel.gcl
05-semantic-mass-kernel.gcl
06-famm-neuromorphic-kernel.gcl
07-avmr-vector-mountain.gcl
08-ammr-commit-mountain.gcl
09-waveprobe-spectral-gate.gcl
10-rgflow-lawfulness-gate.gcl
11-metaprobe-kernel-gate.gcl
12-angry-sphinx-kernel-gate.gcl
13-triumvirate-kernel.gcl
14-gcl-self-host.gcl
15-gcl-kernel-module-registry.gcl
README.md
```

Forward naming note after GCCL lock:

```text
GCCL   = Geometric, Cognitive, and Compression Law
GCLang = Genetic Coding Language / executable notation layer
```

The forward-facing module extension should be `.gclang` once compatibility aliases are wired.

### 2. Offline-first wiki dataset seed

Local artifact name:

```text
offline_wiki_dataset.zip
```

SHA-256:

```text
7d5d26c4202a2996e8c7df37aab9b3a0ab333cad3786678b767b16bcb2f2150a
```

Contents generated:

```text
README.md
WIKI_INDEX.md
data/edges.jsonl
data/manifest.json
data/wiki_entries.jsonl
pages/*.md
schemas/wiki_entry.schema.json
```

Definition pages included the core current stack: GCCL/GCLang compatibility, GCL, MN-GCL, Mass Number, Semantic Mass, NUVMAP, Delta-GCL, AVMR, AMMR, DIAT, BindResult, lawfulLoss, Lawful Hardware, GCL Self-Host, Triumvirate Kernel, MetaProbe, Morphic Neural Encoding, OpenWorm Benchmark, Photonic Morphic Neural Emulation, QuandelaWitness, IBMQuantumWitness, and related support terms.

### 3. GCCL naming patch

Local artifact name:

```text
gccl_commit_patch.zip
```

SHA-256:

```text
8e6899d494e8a9f9993f578b27b379d7a303f330f7d74452c061c704c76ed854
```

This naming patch has now been committed separately as:

```text
4-Infrastructure/nano-kernel/GCCL-NAMING-AND-COMPATIBILITY.md
```

## Commit policy

This manifest exists so the generated local artifacts are not lost. The preferred next step is to unpack and commit the full GCCL module set under:

```text
4-Infrastructure/nano-kernel/gccl-modules/
```

and the offline wiki dataset under:

```text
docs/offline-wiki/
```

## Guardrail

These artifacts are workbench projections. They are not proof-grade until receipts, tests, or Lean mirrors are attached.
