# Research Stack Infrastructure

**Last updated:** 2026-05-29
**Domain:** researchstack.info
**Repo:** ~/Research Stack (git main)
**Hosting:** Self-hosted bare metal — no cloud instances. All compute runs on physical nodes connected via Tailscale mesh. AWS instances were shut down and migrated to this setup.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Tailscale Mesh Network                       │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ QFox     │  │ nixos    │  │ 361395-1 │  │ racknerd │           │
│  │ RTX 4070 │  │ control  │  │ edge     │  │ VPS      │           │
│  │ 100.88.  │  │ plane    │  │ 100.110. │  │ 100.80.  │           │
│  │ 57.96    │  │ 100.102. │  │ 163.82   │  │ 39.40    │           │
│  │          │  │ 173.61   │  │          │  │          │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │             │             │                   │
│       └─────────────┴─────────────┴─────────────┘                   │
│                        Tailscale Funnel                             │
│                        361395-1.tail4e7094.ts.net                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Nodes

| Node | Hostname | Role | IP (Tailscale) | Hardware |
|------|----------|------|----------------|----------|
| nixos | nixos-laptop | k3s control plane | 100.102.173.61 | NixOS 26.05, 6.18.32 kernel |
| qfox-1 | qfox-1 | GPU worker | 100.88.57.96 | CachyOS, RTX 4070, 7.0.9 kernel |
| 361395-1 | 361395-1 | Edge/Funnel | 100.110.163.82 | Proxmox VPS, Debian 13 |
| racknerd | racknerd-510bd9c | Edge worker | 100.80.39.40 | Debian 13, 6.12.43 kernel |
| steamdeck | nixos-steamdeck-1 | Worker | 100.85.244.73 | NixOS 25.11 |

## k3s Cluster

**Version:** v1.35.4+k3s1 (v1.34.5 on steamdeck)
**CNI:** Flannel (tailscale0 interface)
**Ingress:** Traefik
**Server:** nixos (control plane + etcd)

### Namespaces

| Namespace | Services |
|-----------|----------|
| `services` | Homer, Hermes, Actual Budget, Uptime Kuma, Homarr, Vaultwarden, Heimdall, Authentik, Credential Server, Registry API, Jobs API, Blobs API |
| `media` | Jellyfin, Navidrome, Audiobookshelf, Sonarr, Radarr, Prowlarr, SABnzbd |
| `mail` | Roundcube (Postfix + ProtonMail Bridge disabled) |
| `monitoring` | Cluster Dashboard (FastAPI + Vite, port 8787) |
| `edge` | WebRTC bridge (port 8080) |
| `ai-models` | Ollama (deepseek-coder-v2:16b, NodePort 31434) |
| `research` | AlphaProof loop |

### DNS & TLS

- **Domain:** researchstack.info
- **Auth:** auth.researchstack.info (Authentik OIDC)
- **Registry:** registry.researchstack.info
- **TLS:** Caddy with Porkbun DNS-01 (wildcard certs)
- **Funnel:** 361395-1.tail4e7094.ts.net → Traefik NodePort 30080
- **LE cert:** Valid until 2026-08-18

### URL Routing (Traefik Ingress)

| Path | Service | Auth |
|------|---------|------|
| `/` | Homer | SSO-gated |
| `/apps/chat/*` | Hermes | SSO + strip-prefix |
| `/apps/budget/*` | Actual Budget | SSO + strip-prefix |
| `/server/status/*` | Uptime Kuma | SSO + strip-prefix |
| `/server/dash/*` | Homarr | SSO + strip-prefix |
| `/server/vault/*` | Vaultwarden | SSO + strip-prefix |
| `/api/cred/*` | Credential Server | token-auth |
| `/api/registry/*` | Registry API | token-auth |
| `/api/jobs/*` | Jobs API | token-auth |
| `/api/blobs/*` | Blobs API | token-auth |
| `auth.researchstack.info` | Authentik | none |

## FPGA — Tang Nano 9K

**Board:** Sipeed Tang Nano 9K
**FPGA:** Gowin GW1NR-LV9QN88PC6/I5
**Clock:** 27 MHz
**BRAM:** 26 blocks (9Kbit each, 288Kbit total)
**LUTs:** 6,480

### Unified Bitstream: research_stack_top.fs

| Module | LUTs | FFs | Function |
|--------|------|-----|----------|
| Blitter6502OISC | ~2000 | ~500 | SUBLEQ CPU, 4K memory, UART |
| Q16 LUT Core | 266 | 68 | 8 ops, 2-stage pipeline, 74ns |
| Memory Map | ~100 | ~50 | 8-bit ↔ 32-bit bridge |
| Voltage Controller | ~200 | ~100 | 4 BRAM modes (STORE/COMPUTE/APPROX/MORPHIC) |
| Scale Space BRAM | ~300 | ~150 | 4 Gaussian kernel banks (σ=0.25/0.50/0.75/1.00) |
| HiGHS Pivot | ~150 | ~80 | 3-stage simplex pipeline |

**Timing:** 195.92 MHz (7.2x margin over 27 MHz target)
**Status:** Flashed, Verilator verified (5/5 sims pass), UART TX confirmed in simulation

### FPGA Toolchain

| Tool | Version | Path |
|------|---------|------|
| Yosys | 0.64 | /usr/bin/yosys |
| nextpnr-himbaechel | 0.10-75 | /usr/bin/nextpnr-himbaechel |
| gowin_pack | — | /usr/bin/gowin_pack |
| Verilator | 5.048 | /usr/bin/verilator |
| openFPGALoader | — | /usr/bin/openFPGALoader |

### Pin Mapping (Tang Nano 9K)

| Pin | Signal | Direction | Type |
|-----|--------|-----------|------|
| 52 | clk | input | LVCMOS33 |
| 4 | rst_n | input | LVCMOS33 (pull-up) |
| 3 | user_btn | input | LVCMOS33 (pull-up) |
| 10-16 | led[0:5] | output | LVCMOS18 |
| 17 | uart_tx | output | LVCMOS33 |
| 18 | uart_rx | input | LVCMOS33 (pull-up) |

## GPU — QFox

**Card:** NVIDIA RTX 4070
**Driver:** NVML 610.43
**Ollama:** deepseek-coder-v2:16b (Q4_0, 8.9GB)
**NodePort:** 31434

## Lean 4 / Semantics

**Toolchain:** Lean 4.30.0-rc2 + Mathlib
**Build:** `lake build` — 3572 jobs, 0 errors
**Modules:** 10,353 .lean files

### Key Modules

| Module | Lines | Jobs | Status |
|--------|-------|------|--------|
| FixedPoint | 900+ | — | Q16_16 type, arithmetic |
| AdjugateMatrix | 535 | 3300 | Matrix inversion, cofactor identity |
| GoldenRatioSeparation | 123 | 3301 | Lemma 3.4, φ boundary |
| DegeneracyConversion | 311 | 3302 | Unified gate condition |
| LadderBraidAlgebra | 312 | 3314 | Ladder operators → braid crossings |
| PenguinDecayLUT | 356 | 3318 | HEP equations → OTOM framework |
| RiemannianResonanceCorrelator | 373 | 3317 | PDE discovery from data |
| PhysicsPipeline | 360 | 3320 | 8-stage particle physics pipeline |
| RouteCost | 475 | 2 | 9-dimension cost (with latency) |
| OptimizedRoute | 42 | 3 | 2-opt proof (14.1% shorter) |

### Sorry Inventory

| File | Count | Status |
|------|-------|--------|
| AdjugateMatrix.lean | 3 | Q16_16 obstruction (documented) |
| FourPrimitiveErdosRenyi.lean | 4 | Research grade |
| HyperbolicStateSurface.lean | 1 | TODO with proof sketch |
| HamiltonianMechanics.lean | 1 | Legacy Picard-Lindelöf |

## Python Shims

**Version:** Python 3.14.5
**Tests:** 68/68 pass (test_braid_pipeline.py)

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| highspy | 1.14.0 | HiGHS MIP/LP solver |
| reedsolo | ≥1.7.0 | Reed-Solomon ECC |
| cryptography | ≥41.0.0 | ChaCha20 encryption |
| numpy | ≥1.24.0 | Numerical operations |
| requests | ≥2.31.0 | HTTP client |

### Key Modules

| Module | Function |
|--------|----------|
| `qubo_highs.py` | QUBO→MIP via HiGHS (8.4ms vs 53.5ms SA) |
| `braid_search.py` | Dense Sidon sets (Mian-Chowla), soliton search |
| `alphaproof_loop.py` | Ollama → lake build → feedback |
| `scale_space_solver.py` | Multi-scale optimization, Tailscale detection |
| `particle_physics_lut.py` | 34 particle masses, 11 cross-sections as Q16_16 |
| `reed_solomon_vcn.py` | RS encode/decode for VCN frames |
| `chacha20_braid.py` | ChaCha20 encryption for braid data |
| `polynomial_commitment.py` | KZG polynomial commitments |

## Skills (111 enabled)

### Research Stack Skills (6)

| Skill | Triggers | Enforcement |
|-------|----------|-------------|
| `lean-proof` | .lean, lake build, sorry, Q16_16, theorem | Proof quality contract |
| `lean-autoformalization` | autoformalization, paper to Lean | Paper→Lean pipeline |
| `gowin-fpga-synthesis` | synthesize verilog, fpga bitstream | Gowin bitstream flow |
| `vcn-compute-substrate` | VCN, braid encode, MKV blitter | VCN pipeline |
| `research-stack-contracts` | Research Stack, Q16_16, PIST, FAMM | 12 hard-enforced rules |
| `python-numpy-preference` | python, numpy, array | Prefer NumPy |

### Hub Skills (12)

fpga, systemverilog, verilog-design, math-help, physics-intuition, hardware-counters, tensorrt-llm, formal-provers, pipeworx-newton, acorn-prover, numpy, cuopt-numerical-optimization, nemo-curator, Pre-flight Check

### MCP Servers

| Server | Tools | Path |
|--------|-------|------|
| eda | synthesize_verilog, simulate_verilog, view_waveform, run_openlane, view_gds, read_openlane_reports | ~/.hermes/mcp-eda/build/index.js |
| lean | verify_lean_theorem | uvx lean-mcp |
| sympy | 100+ symbolic math tools | uvx mcp-sympy |
| contextstream | memory, search, session management | MCP server |
| aws | AWS CLI tools (legacy — AWS instances shut down) | uvx awslabs.aws-api-mcp-server |

## Key Constants

| Constant | Value | Source |
|----------|-------|--------|
| Q16_16.one | 65536 | FixedPoint.lean |
| goldenAngleStep | 40503 | GoldenAngleEncoding.lean |
| goldenRatio | 106008 | GoldenRatioSeparation.lean |
| uartBaudDivisor | 233 | GenerateSparklePhiS3C.lean |
| UART baud rate | 115384 Hz | 27MHz / 234 |
| MAX_CYCLES | 1,000,000 | Blitter6502OISC_small.v |
| Kolmogorov 4/5 | 52429 | DegeneracyConversion.lean |

## Build Commands

```bash
# Lean full workspace
cd 0-Core-Formalism/lean/Semantics && lake build

# Python tests
cd 4-Infrastructure/shim && python3 test_braid_pipeline.py

# FPGA synthesis
cd 4-Infrastructure/hardware && bash build_research_stack.sh

# FPGA simulation
cd /tmp/fpga_sim_full && ./obj_dir/sim_top

# FPGA flash
openFPGALoader -b tangnano9k research_stack_top.fs

# k3s status
export KUBECONFIG=/tmp/researchstack-kubeconfig.yaml
kubectl get pods -A
```

## k3s Cluster Setup

Detailed cluster setup documentation: `4-Infrastructure/docs/k3s-cluster-setup.md`

### Topology (cupfox control plane)

| Node | Tailscale IP | Role | Arch |
|------|-------------|------|------|
| cupfox | 100.110.163.82 | control-plane | amd64 |
| neon-64gb | 100.64.19.78 | worker (heavy) | arm64 |
| steamdeck | 100.85.244.73 | worker (gpu) | amd64 |
| racknerd | 100.80.39.40 | worker (edge) | amd64 |

### Ollama Inference Serving

- Host-level deployment on Neon-64GB (bypasses KServe RAM limits)
- Caddy reverse proxy on racknerd (:8443 → 100.64.19.78:11434)
- Troubleshooting: autosave.json stale config, passt port interception

### netcup-vps (ARM64 EPYC)

NixOS configuration: `4-Infrastructure/netcup-vps/configuration.nix`

ARM64-optimized packages:
- openblas, blis, lapack — multi-threaded linear algebra
- petsc, slepc — sparse/eigenvalue solvers
- flintqs, pari, gap, singular — number theory / algebra
- symengine — fast C++ symbolic (SymPy backend)
- fftw, suitesparse — FFT and sparse direct solvers
- z3, julia_11 — SMT and JIT numerics

k3s ports: 6443, 2379, 2380 (firewall updated)
