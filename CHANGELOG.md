# CHANGELOG

## 2026-05-09 through 2026-05-19 — Lean Hardening, Storage Stack, Gates & Physics Expansion

### Infrastructure / Storage

- Updated sqlx 0.7 → 0.8.6 to resolve Dependabot vulnerabilities; added ene-rds Cargo.lock.
- Added OpenGL/X11 libraries, pkg-config, and openssl to the devcontainer Nix flake.
- Expanded ene-rds Rust workspace membership and refined devcontainer configuration.
- Expanded devcontainer with full Python stack, added MCP servers for Notion and AWS, and strengthened Lean theorem stubs.
- Added storage observer/optimizer agent (`storage_agent.py`).
- Fixed Porkbun DNS configuration, automated postgres backup jobs, and resolved rds_probe dependency vulnerabilities.
- Added `apiProvider` service kind, credential gateway service, and cupfox routing layer.
- Added EC2 recovery backup suite: NixOS config, AppFlowy compose/env template, credential server bootstrap script, and recovery guide.
- Added RDS probe tool, credential server, and Notion/Linear ingestion pipeline.

### Lean / Core Formalism

- Added `Q16_16.add_pos_of_pos` lemma (quarantined with TODO pending sign-semantics resolution).
- Agent sorry-sprint: closed 9 open sorrys, fixed SSMS sign bug, corrected a false theorem statement.
- Quarantined sorry blocks, fixed `RcloneIntegration` proof, added ENE wiki re-ingest script, and added ZFS setup notes.
- Corrected `Q16_16` add/sub signed-vs-unsigned bug and added missing supporting lemmas.
- Added eigensolid convergence proof, QC flagging tool, and full pass/fail review receipt.
- QC cleanup: created `Q16Utils`, removed dead code, consolidated duplicate proofs.
- QC report: 14 structural and efficiency issues identified and recorded.
- Cleanup crew pass: fixed 95 inspection issues across the Lean surface.
- Created Lean Expert Agent with full inspection protocol.
- Stripped all non-mathematical commentary from `Physics/` files.
- Removed 8 broken, empty, or tautological theorems and 3 ornamental files.
- Full-stack assumption audit across 78 files covering approximately 280 assumptions.
- Fixed 3 critical jiggle issues and documented 10 known remaining jiggles.
- Deterministic build receipt recorded: 3529 jobs, 0 errors.
- Added adjacent coprime classification theorem for second-order recurrences.

### Gates & Documentation (adversarial / compression / witness)

- Added OR-Tools WASM constraint solver gate documentation.
- Added deep-dive addendum on possible constrained-agent approaches.
- Added constrained-agent approaches document with GLIA integration notes.
- Added SmallCode constrained agent execution gate documentation.
- Added citations to the Möbius-Apollonius gate.
- Added Möbius-Apollonius chord partition gate documentation.
- Added Chromatic Homotopy Height Spectral Gate documentation.
- Added Ahmed Integral scalar witness gate documentation.
- Added adversarial duals 16D anchor pack with Anti-FAMM and Anti-BraidStorm documentation and runners.
- Added Anti-BraidStorm hostile crossing gate documentation.
- Added Anti-FAMM shadow adversary documentation.
- Added BraidStorm Sidon Crossing Anti-Alias Gate documentation and runners.
- Added Golden Braid Centering Gate documentation and runners.
- Added autonomous speedrun harness gate.
- Added MarkovJunior 16D PIST rewrite shim.
- Added Sidon FAMM map documentation and runners.
- Added Builder-Judge-Warden geodesic cleanup filter.
- Added logogram chirality route gate.
- Added NUVMAP Delta-DAG search compressor documentation.
- Added common-noise MFG Riccati gate documentation.
- Added bio-organoid signal field gate documentation.
- Added 16D Chaos Game Field Shrinker.
- Added FAMM Semantic Mass math-forest plow and Z-domain accelerator.
- Added FAMM empirical Hessian curvature receipt.
- Added Universal Shortcut Center Manifold documentation.
- Added Plasma Chiral Drag Witness Gate and runners.
- Added Feynman path-integral shadow witness note.
- Added Navier-Stokes shadow control gap map note.

### Physics / RG Flow

- Added BodegaFlow horn-fiber refinements.
- Added superpositional boundary layers as a universal bridge formalism.
- Added the absolute wall analysis: Newton fails as omega → 1.
- Documented 5 gaps the torsion model does not currently close.
- Added protium atom probe for alpha running at the current experimental bound.
- Added Jupiter moons 400-year invariant test of torsion at 10^11 m scale.
- Derived torsion wall: alpha = max|beta| / (4*pi) from the Standard Model.
- Added gravitational wave torsion tests.
- Replaced discrete Menger seam model with continuous RG manifold flow.
- Added Higgs calibration derived from CERN 6-sigma data.
- Added multi-valve cosmological test suite covering S8, BAO, and universe age.
- Added H0 valve test showing the model rules out SH0ES at 4.8-sigma.
- Corrected DESI constants to match published DR1/DR2 values.
- Added DESI invariant and 16D horn-fiber model projection.

### Stack Solidification / Audits

- Disambiguated continuation receipt instructions in the wiki.
- Inventoried all 391 installed packages with FRT separation documented.

## 2026-05-04 — Documentation Consolidation

- Merged desktop manifold_compression specs into main repo
- Archived ChatGPT session logs from lean/Semantics
- Deleted stale otom doc copies, fixed duplicate files
- Created ARCHITECTURE.md, GETTING_STARTED.md, GLOSSARY.md, ROADMAP.md
- Added FRAMEWORK_RELATIONSHIPS.md reconciling GCCL/MISC/GENSIS naming
- Tauri build fixes: dependency simplification (reqwest removal), placeholder icons, navigate API
- Visual primitive witness formalism created and wired into constitution
- ENE research topic candidates, compression-core, notion-native-tauri, linear-native-tauri added
- InvariantReceipt constitutional layer (Receipt, Core, Ledger, Status, SubstrateAdapter; Th1/Th2 proven, Th3/Th4/Th5 deferred)
- Auto-generated GCL glossary (195 terms) from GCL documentation
- Research Stack forest map waterfall migrated from NoDupeLabs
- Genetic information mixture primitives and corrected GCCL theory introduction
- FAMM stigmergic route memory note and photon-chased ferrite trace formation concept
- VLB nibble-delta witness substrate estimate
- KOTC completion daemon design, receipt schema, and simulator
- Offloaded massive data and archives to Gdrive (repo streamlining)

## 2026-05-03 — Repository Consolidation & Kernel Architecture

- Servo-fetch, wasmgpu, text-to-cad moved to Forked/
- Revenue/Webmoji archived
- NUVMAP kernel integration — formal coordinate projection layer
- Triumvirate Kernel — Builder/Judge/Warden consensus, 2/3 fault tolerance
- GCL Self-Host — child kernel generation with metaprobe gate and lawful boot
- Lawful Hardware layer — every hardware event produces BindResult witness
- FAMM-Neuromorphic kernel layer — spatial cognition, event-driven processing, attention, and learning
- Nano kernel with 97% Delta compression, GCL architecture, QEMU test
- LawfulLoss.lean — BindResult structure (Q0_16, substrate-agnostic)
- GCCL naming and compatibility split documented
- Delta-GCL sync layer implemented in pre-push hook
- Git LFS configured for large assets
- Mountain-on-Mountains address space documented via NUVMAP

## 2026-04-29 — Repository Restructuring

- Repository flattened: Documents/Research Stack/ → root
- Goal-based numbered structure established (0-Core-Formalism through 6-Documentation)
- Internal path references updated
- AGENTS.md v2.1 — Anti-Drift Evidence Standards codified
- Claim-state ladder defined (BEAUTIFUL_PROVISIONAL → VERIFIED)
- SI units and standard model compliance rules established
- Fixed-point arithmetic guidelines finalized (Q0_16 default, Q16_16 last resort)

## 2026-04-25 — Project Mapping

- PROJECT_MAP.md generated — sorted by ENE Schema (14-axis hyperbolic concept space)

## 2026-04-21 — Initial Foundation

- Initial commit — sovereign research stack foundation
- .env configuration established
