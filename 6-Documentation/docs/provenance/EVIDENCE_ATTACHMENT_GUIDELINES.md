# Evidence Attachment Guidelines

Systematic approach for attaching evidence to claims in the Research Stack.

## Build Logs

**Location:** `out/build_logs/`

**Naming Convention:** `lake_build_YYYYMMDD_UUID.log`

**Required Attachments:**
- All build success claims must reference a build log file
- Build log must contain full lake build output with explicit step-by-step logging
- Each step must be logged with:
  - UUID (unique identifier for the build step)
  - Timestamp (ISO 8601 format)
  - Step description
  - Step output
- Build steps must be appended to a DAG structure
- Documentation must include markdown link to build log

**DAG Structure:**
```json
{
  "build_id": "UUID",
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "commit": "full_commit_hash",
  "steps": [
    {
      "step_id": "UUID",
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "description": "step description",
      "command": "command executed"
    }
  ],
  "final_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "completed"
}
```

**Implementation:**
- Script: `scripts/dag_build_logger.sh`
- Generates UUID for each build and each step
- Logs each step with timestamp to both log file and DAG
- Saves DAG as JSON in `out/build_dag/`
- Saves full log in `out/build_logs/`

**Path Quoting Invariant:**
```text
path_with_spaces → must_be_quoted
```

All filesystem paths must be quoted in shell scripts to handle spaces in repository paths. Use quoted variables:
```bash
REPO_ROOT="/home/allaun/Documents/Research Stack"
BUILD_LOG_DIR="$REPO_ROOT/out/build_logs"
mkdir -p "$BUILD_LOG_DIR"
```

**Updated Files:**
- `docs/specs/NII_CORE_DRIVER_COMPLETION_SUMMARY.md` - references `out/build_logs/lake_build_20260429.log`
- `docs/nic_cpu_probe_report.md` - references `out/build_logs/lake_build_20260429.log`
- `docs/FIELD_EQUATION_COMPARISON.md` - references `out/build_logs/lake_build_20260429.log`

## Benchmark Artifacts

**Location:** `data/benchmarks/`

**Benchmark Artifacts:**
- [`braid_explained_events_1_200.csv`](../../../data/benchmarks/braid_explained_events_1_200.csv) (44,526 bytes) - Event sequence data for braid benchmark
- [`braid_feature_records_1_200.csv`](../../../data/benchmarks/braid_feature_records_1_200.csv) (23,662 bytes) - Feature extraction results
- [`braid_field_interaction.png`](../../../data/benchmarks/braid_field_interaction.png) (95,097 bytes) - Field interaction visualization
- [`braid_glossary.csv`](../../../data/benchmarks/braid_glossary.csv) (1,708 bytes) - Terminology reference
- [`braid_photonic_emulation.csv`](../../../data/benchmarks/braid_photonic_emulation.csv) (2,602 bytes) - Photonic emulation data
- [`braid_photonic_emulation.png`](../../../data/benchmarks/braid_photonic_emulation.png) (79,633 bytes) - Photonic emulation visualization
- [`braid_photonic_netlist.json`](../../../data/benchmarks/braid_photonic_netlist.json) (12,545 bytes) - Netlist representation
- [`killer_criterion/`](../../../data/benchmarks/killer_criterion/) (directory with FASTA files for killer criterion benchmark)

**Required Attachments:**
- All benchmark performance claims must reference specific artifact files
- Artifacts must include: data files, methodology documentation, environment configuration
- Documentation must include markdown links to artifacts

**Files Requiring Updates:**
- `0-Core-Formalism/lean/Semantics/ChatGPT-Hutter_prize_Compression_#1.md` - references braid benchmark artifacts
- Any documentation referencing benchmark results must link to specific artifact files

## Citation Verification

**Required:**
- All citation claims must include accessible source URLs
- Verify URLs are stable and retrievable
- Document citation context and relevance
- Ensure sources are not ephemeral (avoid link rot)

**Verification Process:**
1. Extract all citation URLs from documentation
2. Test URL accessibility with curl/wget
3. Document any broken or unstable links
4. Replace unstable links with stable alternatives or archived versions

## Commit References

**Current Commit:** `ddf028ab` (HEAD -> reorg/lean-domain-atlas-2026-04-29)

**Required:**
- All commit references must use full commit hashes (40 characters)
- Document commit context and message
- Verify commit exists in repository
- Avoid branch names or partial hashes

## Automated Evidence Attachment

**Implementation Plan:**
1. Create pre-commit hook to generate build logs
2. Create script to verify citation accessibility
3. Create script to validate commit references
4. Integrate evidence attachment into CI/CD pipeline

**Invariant Enforcement:**
```text
buildClaim → buildLog
benchmarkClaim → benchmarkArtifact
citationClaim → sourceCitation
commitClaim → commitHash
```

## User Bandwidth Protection

**Core Law:**
If a verification claim consumes user attention to validate the claim itself, the workflow has already failed.

**Implementation:**
- All claims must have attached evidence at claim time
- User should never need to research to validate a claim
- Evidence must be in the repository or reliably accessible
- No "trust me, I verified this" claims without artifacts
