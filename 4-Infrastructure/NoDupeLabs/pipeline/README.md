# Quality Pipeline

Universal self-configuring quality pipeline for Cline.
Auto-detects the project stack and runs the appropriate checks.

## MCP Servers Required

Configure these in your Cline MCP settings before running:

| Server | Key tools |
|--------|-----------|
| Semgrep | `semgrep_scan`, `semgrep_scan_supply_chain`, `semgrep_findings`, `get_abstract_syntax_tree` |
| Project Health Auditor | `list_repo_files`, `file_metrics`, `git_churn`, `map_tests` |
| API Debugger | `load_openapi`, `ingest_logs`, `explain_failure`, `make_repro` |
| memory | `memory_store`, `memory_search`, `memory_update`, `memory_graph` |

## Files

```
.clinerules                  ← Cline reads this automatically (per-project)
orchestrator_prompt.md       ← Paste into Cline task input to start pipeline
pyproject.toml               ← Tool configuration (single source of truth)
.flake8                      ← flake8 config (does not support pyproject.toml)
.gitignore                   ← Includes reports/ and secret file patterns
scripts/
  audit.py                   ← Universal pipeline runner (auto-detects stack)
  install_tools.sh           ← One-time tool installation
reports/                     ← Generated at runtime — gitignored
```

## Setup

```bash
# 1. Install tools (one time)
bash scripts/install_tools.sh

# 2. Update pyproject.toml — replace these values:
#    name, version, description
#    requires-python
#    python_version  (tool.mypy)
#    target-version  (tool.black)
#    known_first_party (tool.isort)
```

## Usage

```bash
# See what the pipeline detects in your project
python scripts/audit.py detect

# Phase 0 — baseline (run before starting Cline)
python scripts/audit.py recon

# Phase 2 — full validation (all checks must pass)
python scripts/audit.py audit

# Single check
python scripts/audit.py pytest
python scripts/audit.py mypy
python scripts/audit.py gitleaks
```

## Starting the Pipeline in Cline

1. Open this project as your Cline workspace root
2. Paste the contents of `orchestrator_prompt.md` as your task
3. Cline will read `.clinerules`, check memory MCP for prior state,
   and begin Phase 0 automatically

## Detected Technologies

The pipeline auto-detects and enables checks for:

- **Languages**: Python, Node/JS, Go, Java, Ruby, Rust
- **APIs**: FastAPI, Flask, Django, aiohttp (triggers API Debugger MCP)
- **Infrastructure**: Ansible, Docker, Podman, Helm, Kubernetes, Terraform
- **Always active**: gitleaks (secrets), trivy (filesystem vulns)

## MCP vs Subprocess

Some checks are handled by MCP servers and skipped in subprocess mode:

| Check | Handler |
|-------|---------|
| SAST (bandit) | Semgrep MCP → `semgrep_scan()` |
| Complexity (radon) | Project Health Auditor MCP → `file_metrics()` |
| Lint (pylint/flake8) | Project Health Auditor MCP → `file_metrics()` |
| Dead code (vulture) | Project Health Auditor MCP → `file_metrics()` |

Fallback subprocess tools remain installed for when MCP servers are unavailable.

## Success Criteria

All of the following must be true simultaneously:

- `reports/summary.json` → `"status": "PASSED"`, `"failed": []`
- `reports/mcp_semgrep_after.json` → zero CRITICAL/HIGH findings
- `reports/mcp_semgrep_supply_chain_after.json` → zero vulnerabilities
- `reports/mcp_health_metrics_after_*.json` → CC ≤ 10, MI ≥ 65 for all files
- `reports/mcp_api_after.json` → zero failures (if API detected)
- memory MCP → `last_audit_status = "PASSED"`
