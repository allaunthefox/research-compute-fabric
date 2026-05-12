# Optional Science Toolbelt

These tools are optional reference surfaces for math-first work. They are not
default repo dependencies. Add them to a local environment only when a task
needs an executable witness, conversion adapter, or independent solver.

The operating rule is simple: Lean remains the source of truth; these tools
produce receipts, counterexamples, fixtures, and sanity checks.

## Install Manifests

Python packages that are reasonable to install into a task-specific virtual
environment:

```bash
uv venv .venv-science
source .venv-science/bin/activate
uv pip install -r requirements-optional-science.txt
```

Equivalent npm convenience commands:

```bash
npm run setup-science-light
npm run probe-science
```

Native command-line tools are listed in:

```text
system-packages-optional-science.txt
```

Do not wire these into default CI unless the workflow is explicitly optional or
the tool is already installed on the runner.

## Probe What Is Available

Use the probe before asking an agent to rely on a domain tool:

```bash
python3 scripts/probe_science_toolbelt.py
python3 scripts/probe_science_toolbelt.py --json
python3 scripts/probe_science_toolbelt.py --json --out shared-data/artifacts/science_toolbelt/probe.json
```

The probe exits successfully even when optional tools are missing. Missing tools
are data, not failure.

## Domain Priorities

| Domain | First tools | Use in this stack |
| --- | --- | --- |
| Genetics / bioinformatics | Biopython, pysam, samtools, bcftools, minimap2 | Validate FASTA/FASTQ/GenBank/SAM/BAM/VCF fixtures for the genetic-code, Hachimoji, and PIST surfaces. |
| CFD / PDE | Dedalus, ParaView | Produce spectral PDE reference traces for Burgers/KdV/hyperfluid claims without committing to a heavyweight engineering CFD stack. |
| Cryptography | liboqs-python, PyCryptodome, galois | Check post-quantum KEM/signature examples, hashes, finite-field arithmetic, and receipt digests. |
| Chemistry / materials | RDKit, Open Babel | Parse/canonicalize SMILES, compute descriptors, and turn molecular claims into inspectable fixtures. |
| Formal bridge | Z3, cvc5 | Search bounded counterexamples before spending Lean effort. |
| Algebra / graph theory | SageMath, GAP, NetworkX, Graphviz | Generate lattice/group/graph witnesses and diagrams for later Lean or receipt promotion. |
| Compression / signal | zstandard, PyWavelets | Provide compression baselines and spectral/wavelet witnesses for signal-shaping claims. |

## What Not To Do

- Do not add these packages to the default repo environment.
- Do not treat a solver result as a theorem.
- Do not commit generated datasets unless they are promoted as small,
  receipt-bearing evidence.
- Do not copy implementation code from external tools into the repo.

## Receipt Pattern

For any adapter built on this toolbelt, prefer:

1. Input fixture path.
2. Tool name and version from `probe_science_toolbelt.py`.
3. Exact command or Python module call.
4. Output hash and short human-readable summary.
5. Link to the Lean theorem, claim registry entry, or distilled doc that the
   receipt supports.
