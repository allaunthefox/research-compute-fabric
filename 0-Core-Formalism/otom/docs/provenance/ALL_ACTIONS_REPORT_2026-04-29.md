# All Actions Provenance Report

**Date:** 2026-04-29
**Workflow:** @[/all-actions]
**Scope:** /home/allaun/Documents/Research Stack/
**Commit:** ddf028ab (HEAD -> reorg/lean-domain-atlas-2026-04-29)
**Report State:** REMEDIATION_IMPORTED_FROM_LATEST_RUN

## Executive Summary

**Status:** PROVENANCE_COMPLIANT_AFTER_REMEDIATION
**Critical Issues:** 0 (remediated)
**Warnings:** 0 (remediated)
**Compliant Claims:** 6+
**User Bandwidth Protection:** FULLY_ENFORCED_BY_POLICY

This report supersedes the earlier `PROVENANCE_ISSUES_DETECTED` version. The latest all-actions remediation pass reports that the four remaining blocker classes were addressed:

1. false Wolfram Alpha verification comments were replaced with arithmetic sanity checks plus external-CAS provenance disclaimers,
2. partial commit hashes were expanded to full 40-character hashes,
3. citation accessibility verification was run and logged,
4. benchmark artifacts were linked from provenance guidelines.

A follow-up GitHub search for the combined offending strings returned no matching results in this repository snapshot.

## 1. External Verification Claims

### Status: REMEDIATED

The previous report identified six false Wolfram Alpha claims without attached evidence:

- `tools/lean/Semantics/Semantics/EntropyPhaseEngine.lean:717`
- `tools/lean/Semantics/Semantics/CompressionMechanics.lean:174`
- `tools/lean/Semantics/Semantics/Basic.lean:59`
- `tools/lean/Semantics/Semantics/Basic.lean:96`
- `tools/lean/Semantics/Semantics/Bind.lean:97`
- `tools/lean/Semantics/Semantics/Bind.lean:184`

Latest remediation result:

```text
Replaced with "Arithmetic sanity check" comments.
Added external CAS provenance disclaimers:
Not Wolfram-verified in this chain. Do not mark as Wolfram-verified unless an API result, saved query output, or reproducible external artifact is attached.
```

Policy retained:

```text
externalVerificationClaim → attachedEvidence
```

Allowed comment classes:

```text
Arithmetic sanity check
Externally unverified arithmetic check
Verified with Wolfram Alpha only when API output / saved query / reproducible artifact is attached
```

## 2. Build Claims

### Status: COMPLIANT_WITH_DAG_LOGGING_POLICY

Evidence already attached:

- `docs/specs/NII_CORE_DRIVER_COMPLETION_SUMMARY.md` references `out/build_logs/lake_build_20260429.log`
- `docs/nic_cpu_probe_report.md` references `out/build_logs/lake_build_20260429.log`
- `docs/FIELD_EQUATION_COMPARISON.md` references `out/build_logs/lake_build_20260429.log`

Latest provenance hardening:

- DAG-based build logger created: `scripts/dag_build_logger.sh`
- build logs must explicitly state each step taken
- each build run receives a UUID
- each build step receives a UUID and timestamp
- logs are written to `out/build_logs/`
- machine-readable DAG JSON is written to `out/build_dag/`
- path quoting invariant added:

```text
path_with_spaces → must_be_quoted
```

Future build claims must resolve to:

```yaml
claim_type: buildClaim
claim: Lake build passed
build_id: UUID
timestamp: ISO-8601
log: out/build_logs/lake_build_YYYYMMDD_UUID.log
dag: out/build_dag/build_dag_YYYYMMDD_UUID.json
commit: full_40_character_commit_hash
status: passed | failed
```

## 3. Benchmark Claims

### Status: REMEDIATED / ARTIFACTS LINKED

Benchmark artifact lane:

```text
data/benchmarks/
```

Documented artifacts include:

- `data/benchmarks/braid_explained_events_1_200.csv`
- `data/benchmarks/braid_feature_records_1_200.csv`
- `data/benchmarks/braid_field_interaction.png`
- `data/benchmarks/braid_glossary.csv`
- `data/benchmarks/braid_photonic_emulation.csv`
- `data/benchmarks/braid_photonic_emulation.png`
- `data/benchmarks/braid_photonic_netlist.json`
- `data/benchmarks/killer_criterion/`

Latest remediation result:

```text
Benchmark artifacts were linked from docs/provenance/EVIDENCE_ATTACHMENT_GUIDELINES.md.
```

Policy retained:

```text
benchmarkClaim → benchmarkArtifact
```

## 4. Citation Claims

### Status: VERIFIED_WITH_EXCEPTIONS_CLASSIFIED

Citation verification script created:

```text
scripts/verify_citation_accessibility.sh
```

Report generated:

```text
docs/provenance/citation_accessibility_report_20260429.txt
```

Latest run summary:

```text
17 URLs checked
14 accessible
3 not accessible
```

Reported inaccessible URLs were classified as infrastructure/template/access-control links rather than academic citations requiring immediate remediation:

- `http://localhost:3000/health/notion` — local infrastructure endpoint
- `https://huggingface.co/datasets/leloy/enwik8` — returned 401 / authentication required
- `https://www.notion.so/USER/DATABASE_ID?v=...` — template URL / placeholder

Policy retained:

```text
citationClaim → sourceCitation + accessRecord
```

## 5. Commit Claims

### Status: REMEDIATED

Previous partial hash:

```text
f2d91324
```

Expanded to full 40-character hash:

```text
f2d91324e6a2282fee4bdae86d1f76d43ad46ddb
```

Affected file:

```text
PROJECT_MAP.md
```

Policy retained:

```text
commitClaim → full 40-character commitHash
```

## 6. Circular Dependencies

### Status: NO_CIRCULAR_DEPENDENCIES_DETECTED

Workflow DAG remains acyclic:

```text
chain-all
  → dag-check after each action
  → all-actions provenance pass
```

No circular workflow references were reported.

## 7. Provenance Inflation

### Status: REMEDIATED

Previously detected inflation classes:

- false Wolfram verification labels
- partial commit hashes
- benchmark claims without explicit artifact links
- citation accessibility not verified

Latest remediation result:

```text
No open critical provenance violations remain in the latest all-actions completion report.
```

## 8. User Bandwidth Protection

### Status: FULLY_ENFORCED_BY_POLICY

Invariant:

```text
claim_without_evidence → user_bandwidth_loss
```

Operational rules:

```text
externalVerificationClaim → attachedEvidence
buildClaim → buildLog + buildDAG
benchmarkClaim → benchmarkArtifact
citationClaim → sourceCitation + accessRecord
commitClaim → fullCommitHash
workflowStepClaim → stepUUID + timestamp + parentRunUUID
```

Core law:

```text
Proof burden belongs to the claiming process, not to the user after the fact.
```

## 9. Provenance Integrity Summary

**Claims by Type:**

- External verification: remediated
- Build: compliant with log references; future builds require DAG/UUID logger
- Benchmark: artifacts linked
- Citation: accessibility script and report created
- Commit: partial hashes expanded
- DAG: no circular workflow dependencies detected

**Mass-Number Status:**

```yaml
failure_class: none_open_after_remediation
cost_type: user_bandwidth_redirection_prevented
estimated_loss: 0% for remediated classes
decision: PROVENANCE_COMPLIANT_AFTER_REMEDIATION
```

## Remaining Operational Notes

This report marks the known all-actions blockers as remediated based on the latest completion pass. Future claims must continue to attach evidence at claim time.

Required ongoing controls:

1. Run `scripts/dag_build_logger.sh` for future build success claims.
2. Re-run citation accessibility checks when citation-bearing docs change.
3. Keep benchmark links explicit and local when possible.
4. Reject any future external verification claim without attached evidence.
5. Reject partial commit hashes in claim-bearing docs.

## Conclusion

The prior provenance failure class has been converted into enforceable workflow machinery:

```text
claim
  → evidence requirement
  → DAG step
  → UUID
  → timestamp
  → artifact path
  → append-only provenance record
```

**Invariant Status:** `claim_without_evidence → user_bandwidth_loss` is enforced for the remediated classes, and the stack is marked `PROVENANCE_COMPLIANT_AFTER_REMEDIATION` for the latest all-actions pass.
