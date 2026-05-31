# Research Stack — LLM Context Snapshot

> **Purpose**: Point any LLM to this URL for immediate full-stack context.  
> **Last updated**: 2026-05-21  
> **TTL**: Re-generate this file after any major architectural change.  
> **Host**: https://github.com/allaunthefox/Research-Stack/blob/main/6-Documentation/wiki/LLM-Context.md (or raw via `raw.githubusercontent.com`)
> **Access**: `https://researchstack.info/gettingstarted/` requires Authentik login. Unauthenticated users are redirected to the login flow.

---

## 1. What This Is

The **Research Stack** is a hybrid mathematical-computational infrastructure for:

- **Formal mathematics** (Lean 4 theorems for compression, physics, topology)
- **Distributed storage** (Garage S3 mesh over Tailscale, restic backups, rclone mirrors)
- **AI-assisted review** (Ollama/DeepSeek pipelines with machine-readable receipts)
- **Hardware extraction** (Verilog from Lean proofs → Tang Nano 9K FPGA)
- **Neuroscience-inspired computation** (BraidStorm topology, eigensolid convergence)

**Core thesis**: All deterministic computation (Q16_16 fixed-point arithmetic) is substrate-agnostic — it runs identically on GPU (WGSL), CPU (LLVM), FPGA (Verilog), and browser (WASM). No substrate is privileged.

---

## 2. Repository Layout

```
Research-Stack/
├── 0-Core-Formalism/          # Lean 4 semantics — THE source of truth
│   └── lean/Semantics/        # 3,400+ theorem proofs, Q16_16 fixed-point math
├── 1-Distributed-Systems/      # ENE (Endless Node Edges) mesh
│   └── ene/                   # Rust credential manager, session sync
├── 2-Search-Space/            # FAMM (Fractal Aggregate Memory Model)
├── 3-Agent-Surfaces/          # AVM (Adaptive Virtual Machine) bridges
├── 4-Infrastructure/           # Everything that runs
│   ├── storage/               # Garage S3, restic, rclone, storage-agent
│   ├── infra/                 # Credential server, session sync
│   ├── hardware/              # Verilog generation, FPGA bitstreams
│   ├── deploy/               # Deployment configs (some stale — check dates)
│   └── shim/                 # Python instrumentation, audit probes
├── 5-Applications/             # End-user tools
│   ├── text-to-cad/          # OpenSCAD/CAD harness
│   ├── parquet_compressor/    # WGSL GPU kernels
│   └── scripts/               # Topology maps, deployment scripts
├── 6-Documentation/
│   ├── docs/                  # Formal specs, roadmaps, research imports
│   └── wiki/                  # This file + operational docs
└── shared-data/               # Generated receipts, artifacts (gitignored)
    └── data/stack_solidification/
```

---

## 3. Key Technologies & Versions

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Proof assistant | Lean 4 | 4.30 | Mathlib, native_decide for finite checks |
| Language | Python | 3.11.15 (pinned) | uv for package management |
| Language | Rust | stable | ENE session sync, credential manager |
| Storage | Garage S3 | 2.3.0 | Rust, Dynamo-style, Tailscale mesh |
| Backup | restic | latest | S3 backend to Garage, cold-copy to gdrive |
| Sync | rclone | latest | gdrive ↔ Garage bi-directional |
| Mesh | Tailscale | 1.98.2 | PQC (X25519Kyber768) enabled |
| GPU | WGSL/wgpu | latest | 47 compute shaders, substrate-agnostic |
| FPGA | Yosys/nextpnr | latest | Tang Nano 9K target |
| Secrets | SOPS/age | 3.13.1 | `.sops.yaml` at repo root |
| Secrets | AWS RDS | PostgreSQL 16 | IAM auth tokens, `credential_store` schema |
| Identity / SSO | Authentik | 2026.2.3 | LLM agent management, user provisioning, OpenAPI v3 |

---

## 4. Live Infrastructure (Current State)

### Tailscale Mesh

| Node | IP | OS | k3s | Garage Zone | Role | Reachable? |
|------|-----|-----|-----|-------------|------|------------|
| qfox-1 | 100.88.57.96 | CachyOS | ✅ worker | local (780 GiB) | Primary, GPU compute, 1.8 TB NVMe | local |
| cupfox | 100.110.163.82 | Debian 13 | ✅ control-plane | fra (69 GiB) | k3s server, Netcup VPS | key OK |
| nixos-laptop | 100.102.173.61 | NixOS 26.05 | ✅ worker | ord (347 GiB) | GPU compute, 459 GB NVMe | key OK |
| neon-64gb | 100.64.19.78 | Debian 13 | ✅ worker (ARM64) | netcup-arm (93 GiB) | Netcup ARM64 VPS, 2 TB | root key OK |
| racknerd | 100.80.39.40 | Debian 13 | ✅ worker | vps (954 MiB) | RackNerd VPS, reverse proxy | key OK |
| steamdeck | 100.85.244.73 | NixOS 25.11 | ✅ worker | gpu (373 GiB) | RDNA 2 GPU compute, LLM inference | key OK |
| dracocomp | 100.100.140.27 | — | ❌ | — | Offline | unreachable |

### Distributed Storage Surface

```
qfox-1 NVMe (1.8 TB)          Google Drive (5 TB)
      │                             │
      ▼                             ▼
  Garage S3 ◄───────────────── rclone mount
  (s3://localhost:3900)      (gdrive:/)
      │                             │
      ├── restic snapshots ─────────► cold copy
      ├── db-scratch                └── gdrive-mirror bucket
      ├── rds-overflow              └── research-stack bucket
      └── snap-zone
```

| Layer | Capacity | Zone | Protocol |
|-------|----------|------|----------|
| qfox-1 NVMe | 780 GiB (allocated) | local | Tailscale :3901 |
| nixos-laptop NVMe | 347 GiB (allocated) | ord | Tailscale :3901 |
| cupfox VPS | 69 GiB (allocated) | fra | Tailscale :3901 |
| neon-64gb VPS | 93 GiB (allocated) | netcup-arm | Tailscale :3901 |
| steamdeck NVMe | 373 GiB (allocated) | gpu | Tailscale :3901 |
| racknerd VPS | 954 MiB (allocated) | vps | Tailscale :3901 |
| **Total** | **~1.6 TiB** (6 zones, RF3) | — | ~440 GiB effective |
| 361395-1 disk (future Garage node) | 125 GB | ~48 GB | ~77 GB | local SSD |
| **Google Drive** | **5.0 TB** | **1.9 TB** | **3.1 TB** | **rclone FUSE mount** |
| **Total addressable** | **~7.4 TB** | **~2.3 TB** | **~5.2 TB** | **Garage + rclone + Drive** |

**Garage S3 Cluster**
- **Status**: 6-node cluster (`replication_factor = 3`) across 6 zones — qfox-1 (local), cupfox (fra), nixos-laptop (ord), racknerd (vps), neon-64gb (netcup-arm), steamdeck (gpu)
- **Primary endpoint**: `s3:http://100.88.57.96:3900`
- **Buckets**: `research-stack`, `db-scratch`, `rds-overflow`, `snap-zone`, `gdrive-mirror`
- **Restic snapshots**: 2 (last: 2026-05-18, 5.4 GiB)
- **Next**: Bootstrap nixos-laptop + 361395-1 as storage nodes, bump `replication_factor` to 3

**rclone / Google Drive**
- **Mount**: `/home/allaun/gdrive` (FUSE, via rclone)
- **Cold copy**: `restic` chunks mirrored to `gdrive:restic-mirror`
- **Bi-directional sync**: `gdrive:research-stack` ↔ `s3://gdrive-mirror/`

### Compute Pool (Reachable Nodes)

| Resource | Total | Breakdown |
|----------|-------|-----------|
| **Logical CPUs** | **31** | qfox-1: 12 (Ryzen 5 9600X) · nixos-laptop: 16 (Ryzen 7 5700U) · 361395-1: 2 (EPYC-Genoa) · microvm-racknerd: 1 (Xeon E5-2680 v2) |
| **RAM** | **~48.5 GB** | qfox-1: 30 GB · nixos-laptop: 14 GB · 361395-1: 3.8 GB · microvm-racknerd: 715 MB |
| **Discrete GPUs** | **1** | RTX 4070 SUPER 12GB (qfox-1) |
| **Integrated GPUs** | **2** | AMD Raphael iGPU (qfox-1) · AMD Lucienne iGPU (nixos-laptop) |
| **Vulkan adapters** | **4** | RTX 4070 SUPER, Raphael iGPU, Lucienne iGPU, llvmpipe |
| **CPU blitter fallback** | **2** | llvmpipe on qfox-1 and nixos-laptop |
| **Planned: steam-deck** | **+8 threads, +16 GB, RDNA 2 8CU** | Edge LLM inference (3B-7B), tertiary GPU for wgpu dispatch |

**GPU role allocation**:

| Node | GPU | Best use |
|------|-----|----------|
| qfox-1 | RTX 4070 SUPER (12GB) | Primary GPU compute — wgpu, WGSL, training |
| qfox-1 | AMD Raphael iGPU | Secondary / parallel dispatch when RTX is saturated |
| nixos-laptop | AMD Lucienne iGPU | Background GPU compute, CI/build verification |
| steam-deck (planned) | RDNA 2 (8 CUs) | Edge inference, tertiary wgpu dispatch |
| all nodes | llvmpipe | Fallback when no GPU available — deterministic, slower |

### Credential Server

- **Host**: microvm-racknerd (`100.101.247.127:8444`)
- **Backend**: AWS RDS PostgreSQL (primary) → local JSON (fallback)
- **Active credentials**: 12 providers (deepseek, bedrock, quandela, porkbun, authentik, etc.)
- **Auth**: IAM tokens via boto3, SSL required
- **Wiki**: `wiki/Credential-System.md`

### Static Web Hosting (LLM Context Page)

- **Host**: microvm-racknerd (`100.101.247.127`)
- **Mechanism**: Caddy `forward_auth` → Authentik embedded outpost → static files
- **Status**: **Behind Authentik SSO** — login required
- **Tailnet URL**: `https://microvm-racknerd.tail4e7094.ts.net/getstarted/` (if Tailscale serve still active)
- **Public URL**: `https://researchstack.info/gettingstarted/` — **requires Authentik login**
- **Source markdown**: `6-Documentation/wiki/LLM-Context.md` → HTML via `uv run` script

### Chat Interface (Planned)

- **Host**: microvm-racknerd (Caddy) → Steam Deck (pending onboarding)
- **Mechanism**: Caddy `forward_auth` → Authentik → reverse_proxy to Open WebUI on Steam Deck
- **Status**: **Placeholder page deployed** — backend pending Steam Deck onboarding
- **Public URL**: `https://chat.researchstack.info` — **requires Authentik login**
- **Backend**: Ollama (Vulkan) + Open WebUI on Steam Deck, 3B–7B quantized models
- **DNS**: `chat.researchstack.info` → `172.245.19.182` (microvm-racknerd)
- **Caddy config**: `/etc/caddy/Caddyfile` on microvm-racknerd

### Dashboard (Homer)

- **Host**: microvm-racknerd (`100.101.247.127`)
- **Tool**: Homer (static dashboard, links to all services)
- **Status**: **Deployed** — static files at `/var/www/researchstack/dash`
- **Public URL**: `https://dash.researchstack.info` — **requires Authentik login**
- **DNS**: `dash.researchstack.info` → `172.245.19.182` (microvm-racknerd)
- **Config**: `assets/config.yml` in Homer dist

### Status Monitoring (Uptime Kuma)

- **Host**: nixos-laptop (`100.119.165.120:3001`)
- **Tool**: Uptime Kuma (HTTP/TCP/ping monitoring + alerts)
- **Status**: **Deployed** — podman container `uptime-kuma`
- **Public URL**: `https://status.researchstack.info` — **requires Authentik login**
- **DNS**: `status.researchstack.info` → `172.245.19.182` (microvm-racknerd)
- **Reverse proxy**: Caddy on microvm-racknerd → Tailscale → nixos-laptop:3001
- **Monitors** (7 configured, 6 active):
  - `researchstack.info` — 200 OK
  - `chat.researchstack.info` — 200 OK
  - `dash.researchstack.info` — 200 OK
  - `status.researchstack.info` — 200 OK
  - `auth.researchstack.info` — 200 OK
  - `Authentik nixos-laptop` — 200 OK
  - `Garage S3 qfox-1` — checking (Tailscale mesh reachability)

### Auth Alias

- **Host**: microvm-racknerd (`100.101.247.127`)
- **Purpose**: Clean alias for Authentik login
- **Public URL**: `https://auth.researchstack.info` — **redirects to `https://researchstack.info/` behind Authentik SSO**
- **DNS**: `auth.researchstack.info` → `172.245.19.182` (microvm-racknerd)
- **Caddy**: `forward_auth *` → `redir / https://researchstack.info/ permanent`

### Authentik SSO / Agent Identity

- **Host**: nixos-laptop (`100.119.165.120:9000`)
- **Public URLs**: `https://researchstack.info`, `https://auth.researchstack.info` (alias)
- **Version**: 2026.2.3 (PostgreSQL 16 + Redis + server/worker via rootless podman-compose)
- **OpenAPI spec**: `https://researchstack.info/api/v3/schema/` (568 paths)
- **LLM controller account**: `llm-agent-controller` (service account, `AgentManager` group)
- **Token**: stored in SOPS `credentials.json` under `authentik`
- **Wiki**: `wiki/Authentik-Agent-Management.md`

### Steam Deck (Planned: Edge LLM Node)

> **Hardware**: AMD Zen 2 (4C/8T), 16 GB LPDDR5, RDNA 2 (8 CUs @ 1.6 GHz), 512 GB NVMe
> **Status**: Control stick drift — repurposing as headless compute node
> **Role**: Edge inference (3B-7B models), tertiary GPU for wgpu dispatch
> **Setup**: Tailscale + Ollama/llama.cpp (Vulkan backend) + wgpu Rust runtime

**What it can run**:

| Model Size | Quantization | RAM Use | Tokens/sec (est.) | Use Case |
|-----------|-------------|---------|------------------|----------|
| 2-3B (Gemma 2B, Phi-3 Mini) | Q4_K_M | ~2-3 GB | 20-40 t/s | Fast routing, classification, small reasoning |
| 7B (Llama 3.1, Mistral, Qwen) | Q4_K_M | ~4.5 GB | 10-20 t/s | Agent reasoning, summarization, code completion |
| 7B | Q5_K_M | ~5.5 GB | 8-15 t/s | Higher quality, still fits in 16 GB shared |
| 13B | Q4_K_M | ~8 GB | 5-10 t/s | Tight — may need swap, not recommended |

**Backend options**:

1. **Ollama with Vulkan** (preferred) — `OLLAMA_HOST=steam-deck.tail4e7094.ts.net:11434`, models pulled on-demand
2. **llama.cpp (Vulkan)** — lower overhead, better for single-model dedicated use
3. **wgpu compute** — RDNA 2 for WGSL kernels (braid compression, entropy detection) while CPU runs inference

**Limitations**:
- 16 GB is shared between CPU and GPU. Running a 7B Q4 model leaves ~10 GB for OS + GPU buffers.
- No wired ethernet. WiFi bandwidth to Garage/RDS is lower than wired nodes.
- Battery device — must stay plugged in for sustained compute.
- Thermal throttling under long loads.

**When it helps**:
- **Parallel inference**: qfox-1 runs 70B+ via API, nixos-laptop runs 13B, steam-deck runs 3-7B → 3-tier model cascade
- **Offline inference**: when Tailscale mesh is all you have, the Deck can still reason locally
- **GPU compute offload**: RDNA 2 absorbs wgpu kernels while RTX 4070 SUPER does heavy training

---

**Key API endpoints for LLM agent operations**:

| Operation | Endpoint | Method |
|-----------|----------|--------|
| List users | `/core/users/` | GET |
| Create user | `/core/users/` | POST |
| Create service account | `/core/users/service_account/` | POST |
| List groups | `/core/groups/` | GET |
| Add user to group | `/core/groups/{uuid}/add_user/` | POST |
| List applications | `/core/applications/` | GET |
| Create application | `/core/applications/` | POST |
| List tokens | `/core/tokens/` | GET |
| Create token | `/core/tokens/` | POST |

**Authentication**: Bearer token in `Authorization: Bearer <token>` header.

---

## 5. Critical Conventions (MUST FOLLOW)

### Lean
- Module names must match file names and namespaces
- `Q16_16.ofFloat` is **FORBIDDEN** in compute paths — use `ofNat`, `ofRatio`, `ofInt`
- Every new gate needs: theorem + `#eval` witness OR `native_decide` proof
- Two compressor theorems required: `eigensolid_convergence` + `receipt_invertible`
- Float contamination sites: `BraidCross.lean:49,50,84` and `BraidStrand.lean:57,71`

### Secrets
- **NEVER** commit plaintext API keys. Use SOPS (`sops -d file`)
- Runtime only: `OLLAMA_API_KEY`, `DEEPSEEK_API_KEY`, etc. from env vars
- SOPS age key: `age1tp4vr565zkmvnyulatpyaj6z8zrz7q9mpaypz85yz8rty99crdasualxyr`

### Git
- Do NOT use `git add .` — use explicit file lists from staging manifests
- `shared-data/` is gitignored; promote receipts with `git add -f`
- Pre-commit: check `git diff --cached --check` and run secret scan
- Post-commit hook runs `db-consolidate.sh offload` → Garage S3

### Q16_16 Fixed-Point Arithmetic
- `one = 0x00010000 = 65536` — the fundamental scaling constant
- All arithmetic is saturating: `ofRawInt` clamps to `[minVal, maxVal]`
- No float in compute paths. Substrates (GPU, FPGA, CPU) must produce identical results.

---

## 6. Current Open Tasks

### High Priority
1. **Bootstrap Garage replication** — add nixos-laptop + 361395-1 to cluster, bump `replication_factor` to 3
2. **Complete Lean theorems** — 5 `sorry` admissions in `FixedPoint.lean` (ofRawInt_toInt, mul_self_nonneg, mul_toInt_nonneg, ofRaw_toInt_nonneg, add_one_omega_ge_one)
3. **Fresh restic snapshot** — last backup is 3+ days old
4. **Bump 361395-1 RAM** — 3.8 GB is tight; resize via Netcup console

### Medium Priority
5. **Wire credential access_log** — RDS `credential_store.access_log` is empty; audit trail needed
6. **Deploy storage-agent timer** — 15-min observe→decide→act loop on qfox-1
7. **Cold-copy restic to gdrive** — `backup.sh cold-copy` then verify
8. **Lean BraidEigensolid module** — planned: Q0_2 crossing matrix, Sidon labels, golden centering, convergence proof
9. **Implement Authentik MCP server** — wrap Rust shim into Model Context Protocol bridge
10. **Steam Deck onboarding** — Tailscale + Ollama (Vulkan) + wgpu. Repurpose drifting-stick Deck as edge LLM node (3B-7B inference)

### Completed (Recently)
- **Chat subdomain live** — `chat.researchstack.info` Caddy + Authentik SSO + placeholder page
- **Dashboard (Homer) deployed** — `dash.researchstack.info` static files, Authentik SSO
- **Status monitoring (Uptime Kuma) deployed and configured** — `status.researchstack.info` with 7 monitors (researchstack, chat, dash, status, auth, Authentik, Garage S3)
- **Auth alias deployed** — `auth.researchstack.info` → `researchstack.info` redirect, Authentik SSO
- **DNS cleanup** — deleted `ollama.` and `cupfox.`; created `dash.`, `status.`, `auth.` → `172.245.19.182`
- **Authentik token regeneration** — permanent non-expiring token via `ak shell`, updated in SOPS
- **Fresh restic snapshot** — `31fa3c64` saved, 8.497 GiB processed, 3.028 GiB added

### Blocked / Held
13. **Tang Nano 9K flash** — waiting for physical board + USB programmer
14. **Netcup ports 80/443** — upstream filtering; Caddy HTTPS only via Tailscale or SSH tunnel
15. **dracocomp** — offline 3+ days, unknown hardware profile

---

## 7. Quick Commands

```bash
# Lean build (narrow then full)
lake build Semantics.FixedPoint
lake build

# Verify Lean module
cd 0-Core-Formalism/lean/Semantics && lake build Semantics.<ModuleName>

# Restic snapshot
export AWS_ACCESS_KEY_ID=$(sudo cat /etc/garage/garage.env | grep GARAGE_ACCESS_KEY_ID | cut -d= -f2)
export AWS_SECRET_ACCESS_KEY=$(sudo cat /etc/garage/garage.env | grep GARAGE_SECRET_ACCESS_KEY | cut -d= -f2)
export AWS_DEFAULT_REGION=garage
restic -r s3:http://localhost:3900/research-stack snapshots

# Garage status
sudo -n /usr/local/bin/garage -c /etc/garage/garage.toml status

# Credential server health
curl -s http://100.101.247.127:8444/status | jq .

# Tailscale status
tailscale status

# Decrypt secrets
sops -d 4-Infrastructure/infra/secrets/credentials.json

# Authentik API — AUTHENTICATION REQUIRED
# You must be authenticated by Authentik (valid API token, authorized account).
# The llm-agent-controller service account (authentik Admins group) is the
# canonical identity for LLM-driven agent management.
export AUTHENTIK_TOKEN=$(sops -d --extract '["authentik"]["api_token"]' ../../infra/secrets/credentials.json)

# Authentik API via Rust shim (preferred)
cd 4-Infrastructure/shim/authentik_agent_manager
cargo build --release
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" list-users
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" create-agent new-agent "New LLM Agent"
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" execute plan.json  # DAG mode

# Authentik API via curl (raw)
curl -s -H "Authorization: Bearer $AUTHENTIK_TOKEN" https://researchstack.info/api/v3/core/users/ | jq '.results[] | {username, pk}'

curl -s -X POST -H "Authorization: Bearer $AUTHENTIK_TOKEN" -H "Content-Type: application/json" \
  -d '{"username":"new-agent","name":"New LLM Agent","type":"service_account","is_active":true}' \
  https://researchstack.info/api/v3/core/users/ | jq .
```

---

## 8. Glossary (Terms LLMs Will Encounter)

| Term | Meaning |
|------|---------|
| **Sidon label** | Address from a set where pairwise sums are unique. Powers of 2 for 8 strands. |
| **BraidStorm** | 8-strand braid topology; crossings merge phase and produce residuals. |
| **eigensolid** | Converged stable state of a braid crossing loop. `crossStep(s) = s`. |
| **scar** | FAMM failure record in `ene.scars` (failure_mode, scar_pressure). |
| **Yang-Baxter** | Braid relation `βij βjk βij = βjk βij βjk`. Invariance under reordering. |
| **MORE FAMM** | Memory-Optimized Recursive Entropy Fractal Aggregate Memory Model. |
| **TSM** | Topological S3C Manifold. Thermodynamic safety monitor. |
| **GCL** | Genetic Code Language. Self-improving evolutionary program representation. |
| **AVM** | Adaptive Virtual Machine. Universal math↔Python bytecode bridge. |
| **receipt** | Machine-readable attestation record. Dimensions: C, σ, k, ε_seq, t, ∅_scars. |
| **enwik9** | Hutter Prize 1GB Wikipedia corpus. Canonical compressor test vector. |
| **Q16_16** | Fixed-point format: 16 integer bits + 16 fraction bits, signed. `one = 65536`. |
| **Q0_2** | Contractive crossing matrix format. Values in `[0, 65536)`, row sum < 65536. |

---

## 9. How to Ask For Help

When asking an LLM (or human) for help with this stack, include:

1. **Which layer**: Lean/Semantics, Infrastructure, Applications, or Documentation?
2. **Which file**: Absolute path or module name.
3. **Expected vs actual**: What should happen vs what happens.
4. **Verification steps**: Build command, test command, or `#eval` witness.
5. **Error output**: Full traceback or `lake build` error message.
6. **Receipt**: If this is a bug claim, provide a machine-readable receipt.

**Example good prompt**:
> "In `Semantics/FixedPoint.lean` line 622, `theorem mul_self_nonneg` uses `sorry`. After `unfold mul; simp [ofRawInt, toInt, maxVal, minVal]`, `omega` cannot prove `(if raw > maxVal then maxVal else if raw < minVal then minVal else raw) ≥ 0`. I need a tactic that handles the three `ofRawInt` branches explicitly. Build command: `lake build Semantics.FixedPoint`."

---

## 10. Agent Contract

If you are an LLM agent reading this file:

- **Read `AGENTS.md` first** (repo root, then nearest nested one).
- **Never commit secrets**. Check with `git diff --cached --check`.
- **Prefer existing patterns**. Look at neighboring files before inventing new conventions.
- **Verify before claiming success**. Run `lake build` for Lean, `python3 -m py_compile` for Python.
- **Document changes**. Update this file if you alter architecture.
- **Bounded claims**. A receipt proves only the gate it checks. Do not overclaim.
