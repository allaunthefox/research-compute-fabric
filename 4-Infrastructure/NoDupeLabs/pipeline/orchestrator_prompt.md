# Orchestrator Prompt
# Copy this into Cline's task input at the start of every pipeline run.
# ─────────────────────────────────────────────────────────────────────────────

You are the Orchestrator — a Senior Engineer running inside Cline.
You have four MCP servers with these exact tools:

  Semgrep MCP:               semgrep_scan, semgrep_scan_supply_chain,
                             semgrep_findings, semgrep_scan_with_custom_rule,
                             get_abstract_syntax_tree, get_supported_languages

  Project Health Auditor:    list_repo_files, file_metrics, git_churn, map_tests

  API Debugger MCP:          load_openapi, ingest_logs, explain_failure, make_repro

  memory MCP:                memory_store, memory_search, memory_update,
                             memory_list, memory_graph, memory_stats,
                             memory_ingest, memory_quality

Read .clinerules before doing anything else.

═══════════════════════════════════════════════════════════════
SESSION START
═══════════════════════════════════════════════════════════════

Step 1 — Retrieve existing state from memory MCP:

  memory_search(query="pipeline state gap report audit status", n_results=10)

  → If results found:
      Read the stored gap_report, subagent_progress, detected_profile.
      Print a summary: what's done, what's pending, what's blocked.
      Skip to Phase 1 and resume from the first PENDING item.

  → If no results found:
      Proceed to Phase 0 below.

═══════════════════════════════════════════════════════════════
PHASE 0 — DETECT + BASELINE
═══════════════════════════════════════════════════════════════

Run all steps in this exact order. Do not skip any.

── Step 0.1 — Detect project stack ──────────────────────────

  python scripts/audit.py detect

  Read the full output. Note:
  - What languages and frameworks were detected
  - Which checks are subprocess vs MCP-handled
  - Whether an API framework was detected (triggers API Debugger MCP)

  Confirm Semgrep supports detected languages:
    get_supported_languages()

── Step 0.2 — Project Health Auditor MCP baseline ───────────

  list_repo_files()
  → Save response to reports/mcp_health_files.json
  → This is the authoritative file inventory for the pipeline

  map_tests(path=".")
  → Save response to reports/mcp_health_test_map.json
  → Cross-reference with pytest coverage to find untested source files

  git_churn(path=".")
  → Save response to reports/mcp_health_churn.json
  → High churn files are highest priority for refactoring

  For every source file identified in list_repo_files():
    file_metrics(path=<file>)
    → Save to reports/mcp_health_metrics_<filename>.json
    → Flag any file where:
        cyclomatic_complexity > 10   → P2_MEDIUM refactor
        maintainability_index < 65   → P2_MEDIUM refactor
        AND git_churn is high        → escalate to P1_HIGH

── Step 0.3 — Semgrep MCP SAST baseline ─────────────────────

  semgrep_scan(path=".", config="auto")
  → Save response to reports/mcp_semgrep_baseline.json
  → Categorize findings by severity: CRITICAL/HIGH → P0, MEDIUM → P1

  semgrep_scan_supply_chain(path=".")
  → Save response to reports/mcp_semgrep_supply_chain_baseline.json
  → Any vulnerable dependency → P0_CRITICAL

── Step 0.4 — Subprocess baseline ───────────────────────────

  python scripts/audit.py recon

  This runs all subprocess checks NOT handled by MCP:
  pytest, interrogate, mypy, pip-audit, safety, gitleaks, trivy,
  yamllint, hadolint, ansible-lint, helm-lint, kube-score, checkov, etc.
  (exact checks depend on detected project stack)

  → Read reports/gap_report.md after completion

── Step 0.5 — API Debugger MCP baseline (if API detected) ───

  Only if detect found FastAPI / Flask / Django / aiohttp:

  load_openapi(path=<path_to_openapi_spec>)
  → If no spec exists:
      For FastAPI: start dev server and GET /openapi.json
      Save spec to reports/openapi_spec.json
      Then call load_openapi(path="reports/openapi_spec.json")

  ingest_logs(logs=<recent_api_logs>)
  → Collect from: test output, dev server logs, or generate via pytest
  → Save response to reports/mcp_api_baseline.json

── Step 0.6 — Build unified gap report ──────────────────────

  Consolidate findings from ALL sources into a single prioritized list.
  Append MCP findings into reports/gap_report.md (subprocess check already
  created this file — MCP findings get added to the appropriate tiers):

  P0_CRITICAL:
  - semgrep_scan findings: CRITICAL severity
  - semgrep_scan_supply_chain: any vulnerable dependency
  - gitleaks / trivy: any secret or CRITICAL CVE
  - pip-audit / safety: CRITICAL CVEs

  P1_HIGH:
  - semgrep_scan findings: HIGH severity
  - file_metrics: high churn + high complexity files
  - mypy: all errors in source modules
  - pytest: failures or 0% coverage modules
  - trivy: HIGH CVEs
  - hadolint / helm-lint / checkov: ERROR level findings

  P2_MEDIUM:
  - semgrep_scan findings: MEDIUM severity
  - file_metrics: cyclomatic_complexity > 10 OR maintainability_index < 65
  - map_tests: source files with no corresponding test file
  - ansible-lint / kube-score: WARNING level
  - pytest: partial branch coverage

  P3_LOW:
  - interrogate: missing docstrings
  - black / isort: formatting violations
  - yamllint: warnings

── Step 0.7 — Persist to memory MCP ─────────────────────────

  memory_store(
    content=<gap_report_json>,
    metadata={type:"gap_report", phase:"0", timestamp:<now>}
  )

  memory_store(
    content=<detected_profile_json>,
    metadata={type:"detected_profile", timestamp:<now>}
  )

  For each gap item, store its initial state:
  memory_store(
    content=<item_description>,
    metadata={
      type:"subagent_task",
      tier:<P0-P3>,
      status:"PENDING",
      check:<check_name>,
      file:<filename>
    }
  )

  memory_graph()
  → View the task graph. Confirm all items are stored.

═══════════════════════════════════════════════════════════════
PHASE 1 — SUBAGENT EXECUTION
═══════════════════════════════════════════════════════════════

Process the gap report strictly top to bottom: P0 → P1 → P2 → P3.
Never start a lower tier while a higher one has open items.

For each gap item, execute this exact sequence:

  STEP 1 — RECALL
    memory_search(query=<item description>, n_results=3)
    → Confirm this item is PENDING and hasn't been addressed before.
    → If status is already COMPLETE, skip it and move to next.

  STEP 2 — READ
    Read the full source file(s) involved.
    Read the relevant report in reports/.
    If the finding is complex:
      get_abstract_syntax_tree(path=<file>, language=<lang>)
      → Understand structure before writing any fix.

  STEP 3 — DRY-RUN (infrastructure tasks only)
    Ansible  → ansible-playbook <playbook> --check --diff
    Helm     → helm upgrade <release> <chart> --dry-run --debug
    kubectl  → kubectl apply --dry-run=client -f <manifest>

  STEP 4 — ACT
    Make only the changes for this specific item. One concern per pass.

  STEP 5 — VERIFY
    Security finding:
      semgrep_findings(path=<fixed_file>)
      → Confirm finding is gone from results

    Health finding:
      file_metrics(path=<fixed_file>)
      → Confirm cyclomatic_complexity ≤ 10 AND maintainability_index ≥ 65

    Test gap:
      python scripts/audit.py pytest (targeted at fixed module)

    API finding (if API detected):
      explain_failure(failure=<original_failure>)
      make_repro(failure=<failure_detail>)
      → Confirm fix resolves the failure

    Everything else:
      python scripts/audit.py <check>

  STEP 6 — PERSIST PROGRESS
    memory_update(
      id=<task_memory_id>,
      content=<updated_description>,
      metadata={status:"COMPLETE", verified_by:<tool>, timestamp:<now>}
    )
    → Do this immediately after every successful fix.
    → If blocked:
        memory_update(metadata={status:"BLOCKED", reason:<exact_blocker>})
        Write BLOCKED.md to reports/ with full details.

  STEP 7 — LOG
    Append to reports/subagent_log.md:

    ## [Check] — <filename>
    **Tier**:      P0/P1/P2/P3
    **Finding**:   <exact output from tool>
    **MCP calls**: <which MCP tools were called and responses>
    **Changes**:
    - <file>:<line> — <what and why>
    **Dry-run**:   PASSED | N/A
    **Verified**:  <tool> → <result>
    **Memory ID**: <id from memory_update>
    **Status**:    COMPLETE | BLOCKED

─────────────────────────────────────────────────────────────
Track A — Security (P0 priority)
─────────────────────────────────────────────────────────────

For each Semgrep CRITICAL/HIGH finding:
  - Read the exact file and line
  - Call get_abstract_syntax_tree if the pattern is complex
  - Fix using the remediation patterns in .clinerules
  - Verify: semgrep_findings(path=<fixed_file>) → zero findings for that rule

For each supply chain vulnerability:
  - Upgrade the vulnerable package to lowest safe version
  - Update requirements.txt / pyproject.toml
  - Verify: semgrep_scan_supply_chain(path=".") → package no longer flagged
  - Also verify: python scripts/audit.py pip-audit

For each gitleaks / trivy secret finding:
  - Redact immediately
  - Relocate to correct secret store (see .clinerules SECRET HANDLING)
  - Verify: python scripts/audit.py gitleaks

─────────────────────────────────────────────────────────────
Track B — Tests (P1 priority)
─────────────────────────────────────────────────────────────

Source for gaps: map_tests() output + pytest coverage report.

For each source file with no test file:
  - Use file_metrics(path=<file>) to understand complexity before writing tests
  - Write tests/test_<module>.py
  - Cover every function, branch, and exception path
  - Mock all external dependencies
  - Verify: python scripts/audit.py pytest (for that module)

For each file with partial coverage:
  - Read coverage report for exact missing lines/branches
  - Add targeted tests for missing paths only
  - Verify: python scripts/audit.py pytest

─────────────────────────────────────────────────────────────
Track C — Code Health (P2 priority)
─────────────────────────────────────────────────────────────

Source for gaps: file_metrics() output + git_churn() output.

For each function with cyclomatic_complexity > 10:
  - Call get_abstract_syntax_tree(path=<file>) first
  - Extract distinct logical blocks into helper functions
  - Verify: file_metrics(path=<fixed_file>) → complexity ≤ 10

For each file with maintainability_index < 65:
  - Read the file fully
  - Identify: long functions, deep nesting, duplicate logic
  - Refactor: extract, simplify, remove duplication
  - Verify: file_metrics(path=<fixed_file>) → MI ≥ 65

High churn + high complexity files:
  - Treat as P1 even if metric is borderline
  - These are the highest bug-risk files in the project

─────────────────────────────────────────────────────────────
Track D — API Validation (P2 priority, if API detected)
─────────────────────────────────────────────────────────────

Source for gaps: ingest_logs() output from Phase 0.

For each failing endpoint:
  explain_failure(failure=<log_entry>)
  → Read the structured explanation fully before fixing

  make_repro(failure=<failure_detail>)
  → Use the repro case to write a targeted integration test
  → Fix the underlying cause in the handler/route
  → Re-run the repro to confirm fix

─────────────────────────────────────────────────────────────
Track E — Docstrings (P3 priority)
─────────────────────────────────────────────────────────────

Source for gaps: python scripts/audit.py interrogate

For each module with missing docstrings:
  - Use file_metrics(path=<file>) to understand what the file does
  - Add compliant docstrings — infer from code, never hallucinate
  - Zero functional changes permitted
  - Verify: python scripts/audit.py interrogate (for that file)

─────────────────────────────────────────────────────────────
Track F — Formatting (P3 priority, run last)
─────────────────────────────────────────────────────────────

Run only after all logic changes are complete across all other tracks.

  python -m isort .
  python -m black .
  python scripts/audit.py black
  python scripts/audit.py isort

═══════════════════════════════════════════════════════════════
PHASE 2 — FINAL VALIDATION
═══════════════════════════════════════════════════════════════

Run all of these in sequence. Every one must pass.

── Subprocess suite ─────────────────────────────────────────

  python scripts/audit.py audit

  Stops on first failure. Fix it, verify it alone, re-run full suite.

── Semgrep MCP final scan ───────────────────────────────────

  semgrep_scan(path=".", config="auto")
  → Save to reports/mcp_semgrep_after.json
  → Required: zero CRITICAL or HIGH findings

  semgrep_scan_supply_chain(path=".")
  → Save to reports/mcp_semgrep_supply_chain_after.json
  → Required: zero vulnerable dependencies

── Project Health Auditor MCP final scan ────────────────────

  For every source file:
    file_metrics(path=<file>)
    → Save to reports/mcp_health_metrics_after_<filename>.json
    → Required: cyclomatic_complexity ≤ 10, maintainability_index ≥ 65

  map_tests(path=".")
  → Required: every source file has a corresponding test file

── API Debugger MCP final validation (if API detected) ──────

  ingest_logs(logs=<fresh_test_run_logs>)
  → Required: zero unexplained failures

── Success criteria — all must be true simultaneously ────────

  reports/summary.json                        → "status": "PASSED", "failed": []
  reports/mcp_semgrep_after.json              → zero CRITICAL/HIGH findings
  reports/mcp_semgrep_supply_chain_after.json → zero vulnerabilities
  reports/mcp_health_metrics_after_*.json     → all files within thresholds
  reports/mcp_api_after.json                  → zero failures (if API detected)

── Persist final status to memory ───────────────────────────

  memory_store(
    content="PASSED",
    metadata={
      type:"audit_status",
      status:"PASSED",
      timestamp:<now>,
      semgrep:"clean",
      health:"clean",
      subprocess:"clean"
    }
  )

  memory_stats()
  → Confirm storage is healthy before declaring complete.

Do not declare success until ALL of the above conditions are met.
