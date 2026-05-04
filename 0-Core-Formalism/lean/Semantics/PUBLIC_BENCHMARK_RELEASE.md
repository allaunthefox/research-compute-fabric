# Public Benchmark Release

## Phase 12: Public Benchmark Release

**Status: REQUIRES EXTERNAL COORDINATION**

### Headline
**OpenWorm Kernel-Field Benchmark: Invariant preservation under compressed biological topology encoding.**

### Allowed Claims
- OpenWorm-only
- C. elegans-only
- public-data-only
- simulation-only
- non-human-only
- compression/invariant benchmark

### Forbidden Claims
- consciousness
- mind upload
- human brain solved
- personhood model
- behavioral control
- digital life

### Release Requirements
1. External red-team review completed (Phase 10)
2. OpenWorm-only safe shell published (Phase 5)
3. Benchmark gates demonstrated (Phase 4)
4. Baseline comparison wins (Phase 3)
5. AngrySphinx policy compliance (Phase 6)
6. Receipt reproducibility verified (Phase 13)

### Release Artifacts
- OpenWormKernelFieldBenchmark/ (safe shell)
- OpenWormBenchmark.lean (hardened benchmark)
- BaselineTest.lean (baseline comparison)
- OpenWormInvariantTest.lean (invariant verification)
- Receipt root hashes
- Aggregate results

### Benchmark Gates
- shim_pass: PRELIMINARY_FOOTHOLD
- shim_pass + baseline_win: CREDIBLE_RESULT
- baseline_win + Lean_witness: VERIFIED_BENCHMARK
- verified + reproducible_package: PUBLIC_BENCHMARK_READY

### Gate
- No release until shim_pass + baseline_win
- No release without Lean witness
- No release without reproducible package
- No release with forbidden claims
