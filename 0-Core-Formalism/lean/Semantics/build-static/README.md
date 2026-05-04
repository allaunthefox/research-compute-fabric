# OTOM Static Compilation Suite

Builds Lean 4 executables with static linking via GCC for the OTOM Research Stack.

## Quick Start

```bash
cd 0-Core-Formalism/lean/Semantics/build-static

# Verify toolchain
./build_static.sh check

# Build all executables with static linking
./build_static.sh

# Optimized release build with LTO
./build_static.sh release --lto

# Build inside Docker (musl, fully static)
./build_static.sh docker
```

## Available Targets

| Target      | Description                                  |
|-------------|----------------------------------------------|
| `all`       | Static build of all executables (default)    |
| `release`   | Optimized `-O3` build, optional `--lto`      |
| `debug`     | Debug build with symbols                     |
| `check`     | Verify toolchain availability                |
| `lint`      | Run zero-trust linter (AGENTS.md)          |
| `verilog`   | Emit Lean-verified Verilog for FPGA          |
| `synthesis` | Full FPGA synthesis (yosys + nextpnr)      |
| `clean`     | Remove build artifacts                       |
| `docker`    | Reproducible Docker-based build              |

## Executables

The following targets are built from `lakefile.toml`:

- `bindserver` — OTOM bind server
- `searchserver` — Search service
- `SemanticsCli` — CLI interface
- `openworm_benchmark` — OpenWorm benchmark
- `ExtremeParameterTestEval` — Parameter test (extreme)
- `NominalParameterTestEval` — Parameter test (nominal)
- `moim_benchmark` — MOIM benchmark
- `generate_sparkle_phi_s3c` — Sparkle Phi/S3C generator
- `tangnano9k_emitter` — Tang Nano 9K Verilog emitter

## Configuration

Environment variables:

| Variable     | Default | Description                     |
|--------------|---------|---------------------------------|
| `LEAN_CC`    | `gcc`   | C compiler                      |
| `LEANC_OPTS` | —       | Additional compiler flags       |
| `JOBS`       | auto    | Parallel jobs                   |
| `TARGET_DIR` | `./out` | Output directory for binaries   |

## Static Linking Notes

- Uses `-static -static-libgcc` for glibc-based static linking
- Use `--musl` or Docker build for fully static musl binaries
- `lake` passes flags to `leanc`, which wraps the system compiler
- Verified with `ldd` to confirm no dynamic dependencies

## Makefile Interface

```bash
make static       # Default static build
make release      # Optimized build
make check        # Toolchain verification
make docker-build # Docker-based build
make clean        # Clean artifacts
```

## Architecture

- `build_static.sh` — Main orchestration script
- `Makefile` — Standard make interface
- `Dockerfile.static` — Alpine/musl reproducible build
