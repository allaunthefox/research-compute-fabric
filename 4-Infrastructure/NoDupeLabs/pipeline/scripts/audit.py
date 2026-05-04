#!/usr/bin/env python3
"""
audit.py — Universal self-configuring quality pipeline for Cline.

Detects the project stack and runs the appropriate checks via subprocess.
MCP servers (Semgrep, Project Health Auditor, API Debugger, memory) are
called directly by Cline — not from this script. This script handles
everything that is NOT covered by an MCP server.

Usage:
    python scripts/audit.py detect      # show detected stack + active checks
    python scripts/audit.py recon       # Phase 0 subprocess checks only
    python scripts/audit.py audit       # Phase 2 subprocess checks only
    python scripts/audit.py <check>     # single check

MCP servers Cline calls separately (not from this script):
    Semgrep MCP              → semgrep_scan, semgrep_scan_supply_chain,
                               semgrep_findings, semgrep_scan_with_custom_rule,
                               get_abstract_syntax_tree, get_supported_languages
    Project Health Auditor   → list_repo_files, file_metrics, git_churn, map_tests
    API Debugger MCP         → load_openapi, ingest_logs, explain_failure, make_repro
    memory MCP               → memory_store, memory_search, memory_update,
                               memory_list, memory_graph, memory_stats
"""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────

REPORTS = Path("reports")
ROOT    = Path(".")

# Checks handled by MCP servers — excluded from subprocess suite to avoid
# duplication. Cline calls these MCP tools directly at the appropriate phase.
MCP_OWNED_CHECKS = {
    "bandit",     # → Semgrep MCP (semgrep_scan)
    "pylint",     # → Project Health Auditor MCP (file_metrics)
    "flake8",     # → Project Health Auditor MCP (file_metrics)
    "radon-cc",   # → Project Health Auditor MCP (file_metrics)
    "radon-mi",   # → Project Health Auditor MCP (file_metrics)
    "vulture",    # → Project Health Auditor MCP (file_metrics)
}

MCP_SERVER_MAP = {
    "bandit":   "Semgrep MCP → semgrep_scan(path='.', config='auto')",
    "pylint":   "Project Health Auditor MCP → file_metrics(path=<file>)",
    "flake8":   "Project Health Auditor MCP → file_metrics(path=<file>)",
    "radon-cc": "Project Health Auditor MCP → file_metrics(path=<file>)",
    "radon-mi": "Project Health Auditor MCP → file_metrics(path=<file>)",
    "vulture":  "Project Health Auditor MCP → file_metrics(path=<file>)",
}

# ─── PROJECT DETECTION ───────────────────────────────────────────────────────

@dataclass
class ProjectProfile:
    """Detected project composition."""

    # Languages
    python:     bool = False
    node:       bool = False
    go:         bool = False
    java:       bool = False
    ruby:       bool = False
    rust:       bool = False

    # Infrastructure
    ansible:    bool = False
    docker:     bool = False
    podman:     bool = False
    helm:       bool = False
    kubernetes: bool = False
    terraform:  bool = False
    compose:    bool = False

    # API frameworks (triggers API Debugger MCP)
    has_api:       bool = False
    api_framework: str  = ""

    # Metadata
    detected: list[str] = field(default_factory=list)
    root:     Path      = ROOT

    def note(self, label: str) -> None:
        """Record a detected technology."""
        self.detected.append(label)


def detect_project(root: Path = ROOT) -> ProjectProfile:
    """
    Scan the project root and return a ProjectProfile.
    Uses file presence, directory structure, and content — never assumes.
    """
    p = ProjectProfile(root=root)

    def exists(*paths: str) -> bool:
        """Check if any of the given paths exist relative to root."""
        return any((root / path).exists() for path in paths)

    def glob_any(*patterns: str) -> bool:
        """Check if any files match the given glob patterns under root."""
        return any(list(root.rglob(pat)) for pat in patterns)

    def file_contains(path: str, *terms: str) -> bool:
        """Check if a file at the given path contains any of the search terms."""
        f = root / path
        if not f.exists():
            return False
        content = f.read_text(errors="ignore").lower()
        return any(t.lower() in content for t in terms)

    def any_py_contains(*terms: str) -> bool:
        """Check if any Python file in the project contains any of the search terms."""
        for pyfile in root.rglob("*.py"):
            if ".venv" in str(pyfile) or "build" in str(pyfile):
                continue
            try:
                content = pyfile.read_text(errors="ignore").lower()
                if any(t.lower() in content for t in terms):
                    return True
            except (OSError, PermissionError):
                continue
        return False

    # ── Python ───────────────────────────────────────────────────────────────
    if (
        exists("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")
        or glob_any("*.py")
    ):
        p.python = True
        p.note("Python")

    # ── API Framework Detection (triggers API Debugger MCP) ──────────────────
    if p.python:
        if any_py_contains("from fastapi", "import fastapi"):
            p.has_api = True
            p.api_framework = "FastAPI"
            p.note("FastAPI")
        elif any_py_contains("from flask", "import flask"):
            p.has_api = True
            p.api_framework = "Flask"
            p.note("Flask")
        elif any_py_contains("from django", "import django"):
            p.has_api = True
            p.api_framework = "Django"
            p.note("Django")
        elif any_py_contains("from aiohttp", "import aiohttp"):
            p.has_api = True
            p.api_framework = "aiohttp"
            p.note("aiohttp")

    # ── Node / JS / TS ───────────────────────────────────────────────────────
    if exists("package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
        p.node = True
        p.note("Node/JS")

    # ── Go ───────────────────────────────────────────────────────────────────
    if exists("go.mod", "go.sum") or glob_any("*.go"):
        p.go = True
        p.note("Go")

    # ── Java ─────────────────────────────────────────────────────────────────
    if exists("pom.xml", "build.gradle", "build.gradle.kts"):
        p.java = True
        p.note("Java")

    # ── Ruby ─────────────────────────────────────────────────────────────────
    if exists("Gemfile", "Gemfile.lock"):
        p.ruby = True
        p.note("Ruby")

    # ── Rust ─────────────────────────────────────────────────────────────────
    if exists("Cargo.toml", "Cargo.lock"):
        p.rust = True
        p.note("Rust")

    # ── Ansible ──────────────────────────────────────────────────────────────
    if (
        exists("ansible.cfg", "site.yml", "playbooks", "roles", "collections")
        or glob_any("*.ansible.yml", "*/tasks/main.yml")
        or file_contains("requirements.yml", "ansible", "galaxy")
    ):
        p.ansible = True
        p.note("Ansible")

    # ── Docker ───────────────────────────────────────────────────────────────
    if glob_any("Dockerfile", "Dockerfile.*", "*.dockerfile"):
        p.docker = True
        p.note("Docker")

    # ── Podman ───────────────────────────────────────────────────────────────
    if (
        glob_any("Containerfile", "Containerfile.*")
        or exists("podman-compose.yml", "podman-compose.yaml")
    ):
        p.podman = True
        p.note("Podman")
        if not p.docker:
            p.docker = True

    # ── Compose ──────────────────────────────────────────────────────────────
    if glob_any(
        "docker-compose.yml", "docker-compose.yaml",
        "compose.yml", "compose.yaml",
        "podman-compose.yml", "podman-compose.yaml",
    ):
        p.compose = True
        p.note("Compose")

    # ── Helm ─────────────────────────────────────────────────────────────────
    if glob_any("Chart.yaml", "Chart.yml"):
        p.helm = True
        p.note("Helm")

    # ── Kubernetes ───────────────────────────────────────────────────────────
    k8s_kinds = {
        "kind: Deployment", "kind: Service", "kind: ConfigMap",
        "kind: StatefulSet", "kind: DaemonSet", "kind: Ingress",
        "kind: Pod", "kind: Job", "kind: CronJob", "kind: Secret",
        "kind: PersistentVolumeClaim", "kind: ClusterRole",
        "kind: ServiceAccount", "kind: Namespace",
    }
    for yf in list(root.rglob("*.yaml")) + list(root.rglob("*.yml")):
        if ".git" in str(yf) or ".venv" in str(yf):
            continue
        try:
            content = yf.read_text(errors="ignore")
            if any(kind in content for kind in k8s_kinds):
                p.kubernetes = True
                p.note("Kubernetes")
                break
        except (OSError, PermissionError):
            continue

    # ── Terraform ────────────────────────────────────────────────────────────
    if glob_any("*.tf", "*.tfvars"):
        p.terraform = True
        p.note("Terraform")

    return p


# ─── CHECK DEFINITIONS ────────────────────────────────────────────────────────

def build_check_suite(p: ProjectProfile) -> dict[str, dict]:
    """
    Build subprocess check suite based on detected project profile.
    MCP_OWNED_CHECKS are registered but marked — Cline calls those MCPs directly.
    """
    available: dict[str, dict] = {}

    # Path to the project's virtual environment
    VENV_BIN = Path("/home/prod/Workspaces/repos/github/NoDupeLabs/.venv/bin")

    def tool_ok(name: str) -> bool:
        """Check if a tool is available in PATH or in the project's .venv."""
        # First check system PATH
        if shutil.which(name) is not None:
            return True
        # Then check in the project's .venv
        venv_tool = VENV_BIN / name
        if venv_tool.exists():
            return True
        # For Python modules, check if the module can be run via python -m
        venv_python = VENV_BIN / "python"
        if venv_python.exists():
            try:
                result = subprocess.run(
                    [str(venv_python), "-m", name, "--help"],
                    capture_output=True,
                    timeout=5
                )
                # If it doesn't return "No module named", the module exists
                if "No module named" not in result.stderr.decode():
                    return True
            except (subprocess.TimeoutExpired, Exception):
                pass
        # Special case: pip-audit may be installed but not in expected location
        # Try running it via the venv python directly
        if name == "pip-audit":
            try:
                result = subprocess.run(
                    [str(venv_python), "-c", "import pip_audit; print('ok')"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, Exception):
                pass
        return False

    def add(name: str, check: dict) -> None:
        """Add a check to the available suite, marking MCP-owned or missing tools."""
        if name in MCP_OWNED_CHECKS:
            available[name] = {
                **check,
                "_mcp_owned":  True,
                "_mcp_server": MCP_SERVER_MAP.get(name, "MCP"),
            }
            return
        tool = check.get("tool", name)
        if tool_ok(tool):
            available[name] = check
        else:
            available[name] = {**check, "_missing_tool": tool}

    # ── YAML ─────────────────────────────────────────────────────────────────
    has_yaml = (
        p.ansible or p.helm or p.kubernetes or p.compose
        or list(ROOT.rglob("*.yml")) or list(ROOT.rglob("*.yaml"))
    )
    if has_yaml:
        add("yamllint", {
            "tool": "yamllint", "tier": "P3_LOW",
            "label": "YAML Lint",
            "cmd":   ["yamllint", "-f", "parsable", "."],
            "docs":  "https://yamllint.readthedocs.io",
        })

    # ── Python ────────────────────────────────────────────────────────────────
    if p.python:
        add("pytest", {
            "tool": "pytest", "tier": "P1_HIGH",
            "label": "Tests + Coverage",
            "cmd": [
                "/home/prod/Workspaces/repos/github/NoDupeLabs/.venv/bin/python", "-m", "pytest",
                "--tb=short",
                "--cov=nodupe",
                "--cov-branch",
                "--cov-report=term-missing",
                f"--cov-report=html:{REPORTS}/coverage",
                f"--cov-report=xml:{REPORTS}/coverage.xml",
                "--cov-fail-under=80",
                "-q",
            ],
            "docs": "https://docs.pytest.org",
        })
        add("interrogate", {
            "tool": "interrogate", "tier": "P3_LOW",
            "label": "Docstring Coverage",
            "cmd":   ["/home/prod/Workspaces/repos/github/NoDupeLabs/.venv/bin/python", "-m", "interrogate", ".", "-v", "--fail-under", "100"],
            "docs":  "https://interrogate.readthedocs.io",
        })
        add("mypy", {
            "tool": "mypy", "tier": "P1_HIGH",
            "label": "Type Checking",
            "cmd":   ["/home/prod/Workspaces/repos/github/NoDupeLabs/.venv/bin/python", "-m", "mypy", ".", "--ignore-missing-imports"],
            "docs":  "https://mypy.readthedocs.io",
        })
        # MCP-owned — registered for visibility, Cline calls Semgrep MCP instead
        add("bandit", {
            "tool": "bandit", "tier": "P1_HIGH",
            "label": "Python SAST",
            "cmd":   ["python", "-m", "bandit", "-r", ".", "-ll",
                      "--exclude", ".venv,build,dist,docs,tests"],
            "docs":  "https://bandit.readthedocs.io",
        })
        add("pip-audit", {
            "tool": "pip-audit", "tier": "P0_CRITICAL",
            "label": "Python Dependency CVEs (pip-audit)",
            "cmd":   [str(VENV_BIN / "python"), "-m", "pip_audit", "--format=columns"],
            "docs":  "https://pypi.org/project/pip-audit",
        })
        add("safety", {
            "tool": "safety", "tier": "P0_CRITICAL",
            "label": "Python Dependency CVEs (safety)",
            "cmd":   ["/home/prod/Workspaces/repos/github/NoDupeLabs/.venv/bin/python", "-m", "safety", "check", "--ignore", "51457"],
            "docs":  "https://pyup.io/safety",
        })
        # MCP-owned health checks — Project Health Auditor MCP handles these
        for name, label in [
            ("pylint",   "Lint — pylint"),
            ("flake8",   "Lint — flake8"),
            ("radon-cc", "Complexity — radon cc"),
            ("radon-mi", "Maintainability — radon mi"),
            ("vulture",  "Dead Code — vulture"),
        ]:
            add(name, {
                "tool": name.split("-")[0], "tier": "P2_MEDIUM",
                "label": label,
                "cmd":   [],
                "docs":  "https://radon.readthedocs.io" if "radon" in name
                         else "https://pylint.readthedocs.io",
            })
        add("black", {
            "tool": "black", "tier": "P3_LOW",
            "label": "Format — black",
            "cmd":   ["python", "-m", "black", ".", "--check", "--diff",
                      "--exclude", r"/(\.venv|build|dist)/"],
            "docs":  "https://black.readthedocs.io",
        })
        add("isort", {
            "tool": "isort", "tier": "P3_LOW",
            "label": "Import Order — isort",
            "cmd":   ["python", "-m", "isort", ".", "--check-only", "--diff",
                      "--skip", ".venv", "--skip", "build", "--skip", "dist"],
            "docs":  "https://pycqa.github.io/isort",
        })

    # ── Node ─────────────────────────────────────────────────────────────────
    if p.node:
        add("npm-audit", {
            "tool": "npm", "tier": "P0_CRITICAL",
            "label": "Node Dependency CVEs",
            "cmd":   ["npm", "audit", "--audit-level=moderate"],
            "docs":  "https://docs.npmjs.com/cli/commands/npm-audit",
        })

    # ── Go ────────────────────────────────────────────────────────────────────
    if p.go:
        add("govulncheck", {
            "tool": "govulncheck", "tier": "P0_CRITICAL",
            "label": "Go Vulnerability Check",
            "cmd":   ["govulncheck", "./..."],
            "docs":  "https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck",
        })
        add("go-vet", {
            "tool": "go", "tier": "P1_HIGH",
            "label": "Go Vet",
            "cmd":   ["go", "vet", "./..."],
            "docs":  "https://pkg.go.dev/cmd/vet",
        })

    # ── Ansible ───────────────────────────────────────────────────────────────
    if p.ansible:
        add("ansible-lint", {
            "tool": "ansible-lint", "tier": "P2_MEDIUM",
            "label": "Ansible Lint",
            "cmd":   ["ansible-lint", "--format", "full", "--nocolor"],
            "docs":  "https://ansible-lint.readthedocs.io",
        })

    # ── Docker / Podman ───────────────────────────────────────────────────────
    if p.docker or p.podman:
        dockerfiles = (
            [str(f) for f in ROOT.rglob("Dockerfile*") if ".git" not in str(f)]
            + [str(f) for f in ROOT.rglob("Containerfile*") if ".git" not in str(f)]
        )
        if dockerfiles:
            add("hadolint", {
                "tool": "hadolint", "tier": "P1_HIGH",
                "label": "Dockerfile/Containerfile Lint",
                "cmd":   ["hadolint", "--no-color"] + dockerfiles,
                "docs":  "https://github.com/hadolint/hadolint",
            })

    # ── Helm ──────────────────────────────────────────────────────────────────
    if p.helm:
        charts = [
            str(f.parent) for f in ROOT.rglob("Chart.yaml")
            if ".git" not in str(f)
        ]
        if charts:
            add("helm-lint", {
                "tool": "helm", "tier": "P1_HIGH",
                "label": "Helm Chart Lint",
                "cmd":   ["sh", "-c",
                          " && ".join(f"helm lint {c} --strict" for c in charts)],
                "docs":  "https://helm.sh/docs/helm/helm_lint/",
            })

    # ── Kubernetes ────────────────────────────────────────────────────────────
    if p.kubernetes:
        manifests = [
            str(f) for f in list(ROOT.rglob("*.yaml")) + list(ROOT.rglob("*.yml"))
            if ".git" not in str(f) and "chart" not in str(f).lower()
        ]
        if manifests and tool_ok("kube-score"):
            add("kube-score", {
                "tool": "kube-score", "tier": "P2_MEDIUM",
                "label": "Kubernetes Manifest Quality",
                "cmd":   ["sh", "-c",
                          f"cat {' '.join(manifests[:50])} "
                          f"| kube-score score --output-format ci -"],
                "docs":  "https://github.com/zegl/kube-score",
            })
        if manifests and tool_ok("kubectl"):
            add("kubectl-dry-run", {
                "tool": "kubectl", "tier": "P1_HIGH",
                "label": "kubectl dry-run validation",
                "cmd":   ["sh", "-c",
                          " && ".join(
                              f"kubectl apply --dry-run=client -f {m}"
                              for m in manifests[:50]
                          )],
                "docs":  "https://kubernetes.io/docs/reference/kubectl/",
            })

    # ── Terraform ─────────────────────────────────────────────────────────────
    if p.terraform:
        add("terraform-validate", {
            "tool": "terraform", "tier": "P1_HIGH",
            "label": "Terraform Validate",
            "cmd":   ["terraform", "validate"],
            "docs":  "https://developer.hashicorp.com/terraform/cli/commands/validate",
        })
        add("tfsec", {
            "tool": "tfsec", "tier": "P1_HIGH",
            "label": "Terraform Security (tfsec)",
            "cmd":   ["tfsec", ".", "--no-color"],
            "docs":  "https://aquasecurity.github.io/tfsec",
        })

    # ── IaC — checkov ─────────────────────────────────────────────────────────
    has_infra = p.ansible or p.docker or p.podman or p.helm or p.kubernetes
    if has_infra:
        frameworks = ",".join(filter(None, [
            "ansible"    if p.ansible              else None,
            "dockerfile" if (p.docker or p.podman) else None,
            "helm"       if p.helm                 else None,
            "kubernetes" if p.kubernetes           else None,
        ]))
        add("checkov", {
            "tool": "checkov", "tier": "P1_HIGH",
            "label": f"IaC Security Scan — checkov ({frameworks})",
            "cmd":   ["checkov", "--directory", ".",
                      "--framework", frameworks,
                      "--compact", "--quiet", "--output", "cli"],
            "docs":  "https://www.checkov.io",
        })

    # ── Secrets + filesystem scan — always ────────────────────────────────────
    add("gitleaks", {
        "tool": "gitleaks", "tier": "P0_CRITICAL",
        "label": "Secret Scan (gitleaks)",
        "cmd":   ["gitleaks", "detect", "--source", ".", "--no-git"],
        "docs":  "https://github.com/gitleaks/gitleaks",
    })
    add("trivy", {
        "tool": "trivy", "tier": "P0_CRITICAL",
        "label": "Filesystem Vulnerability Scan (trivy)",
        "cmd":   ["trivy", "fs", ".",
                  "--scanners", "vuln,secret,config",
                  "--severity", "MEDIUM,HIGH,CRITICAL",
                  "--format", "table",
                  "--exit-code", "1"],
        "docs":  "https://aquasecurity.github.io/trivy",
    })

    return available


# ─── TIER ORDER ──────────────────────────────────────────────────────────────

TIER_ORDER = ["P0_CRITICAL", "P1_HIGH", "P2_MEDIUM", "P3_LOW"]


def ordered_checks(suite: dict[str, dict]) -> list[str]:
    """Return active subprocess checks sorted by tier. Skip MCP-owned + missing."""
    result = []
    for tier in TIER_ORDER:
        result += [
            name for name, check in suite.items()
            if check.get("tier") == tier
            and "_missing_tool" not in check
            and "_mcp_owned"    not in check
        ]
    return result


# ─── RUNNER ──────────────────────────────────────────────────────────────────

def run_check(name: str, check: dict, save_as: str | None = None) -> dict:
    """Run a single subprocess check and return structured result."""
    print(f"\n{'─'*60}")
    print(f"  {check['label']}")
    print(f"{'─'*60}")

    # For pytest, we need to run from NoDupeLabs root, not pipeline
    cwd = None
    if name == "pytest":
        cwd = Path("/home/prod/Workspaces/repos/github/NoDupeLabs")

    result = subprocess.run(check["cmd"], capture_output=True, text=True, cwd=cwd)
    output = result.stdout + result.stderr
    passed = result.returncode == 0

    print(output)

    REPORTS.mkdir(exist_ok=True)
    filename    = save_as or name
    report_path = REPORTS / f"{filename}.txt"
    report_path.write_text(
        f"# {check['label']}\n"
        f"# Docs:      {check.get('docs', 'n/a')}\n"
        f"# Tier:      {check.get('tier', 'n/a')}\n"
        f"# Run:       {datetime.now().isoformat()}\n"
        f"# Exit code: {result.returncode}\n"
        f"# Status:    {'PASSED' if passed else 'FAILED'}\n\n"
        + output
    )

    return {
        "name":      name,
        "label":     check["label"],
        "tier":      check.get("tier", "P3_LOW"),
        "passed":    passed,
        "exit_code": result.returncode,
        "output":    output,
        "report":    str(report_path),
        "docs":      check.get("docs", ""),
    }


def run_suite(
    suite:    dict[str, dict],
    names:    list[str],
    label:    str,
    baseline: bool = False,
) -> list[dict]:
    """Run an ordered suite of subprocess checks."""
    results = []
    suffix  = "baseline" if baseline else "audit"

    print(f"\n{'━'*60}")
    print(f"  {label}")
    print(f"{'━'*60}")
    print("  NOTE: Semgrep MCP, Project Health Auditor MCP, and")
    print("  API Debugger MCP are called by Cline separately.")
    print(f"{'━'*60}")

    for name in names:
        check   = suite[name]
        save_as = f"{suffix}_{name}"
        result  = run_check(name, check, save_as=save_as)
        results.append(result)

        if not baseline and not result["passed"]:
            write_summary(results, failed=True)
            print(f"\n  FAILED: {result['label']} [{result['tier']}]")
            print(f"  Report: {result['report']}")
            print(f"  Docs:   {result['docs']}")
            print(f"\n  Fix this check, then re-run:")
            print(f"    python scripts/audit.py {name}")
            sys.exit(1)

    return results


def write_summary(results: list[dict], failed: bool = False) -> None:
    """Write machine-readable JSON summary."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "status":    "FAILED" if failed else "PASSED",
        "mcp_note":  (
            "Semgrep MCP, Project Health Auditor MCP, and API Debugger MCP "
            "results are in reports/mcp_*.json — check those separately."
        ),
        "checks": [
            {
                "name":      r["name"],
                "label":     r["label"],
                "tier":      r["tier"],
                "passed":    r["passed"],
                "exit_code": r["exit_code"],
                "report":    r["report"],
            }
            for r in results
        ],
        "passed": [r["name"] for r in results if     r["passed"]],
        "failed": [r["name"] for r in results if not r["passed"]],
    }
    path = REPORTS / "summary.json"
    path.write_text(json.dumps(summary, indent=2))
    print(f"\n  Summary: {path}")


def write_gap_report(results: list[dict], profile: ProjectProfile) -> None:
    """Write severity-tiered gap report from baseline subprocess results."""

    def grep(output: str, *patterns: str) -> list[str]:
        """Filter output lines containing any of the given patterns (case-insensitive)."""
        return [
            line for line in output.splitlines()
            if any(p.lower() in line.lower() for p in patterns)
        ]

    findings: dict[str, list[str]] = {tier: [] for tier in TIER_ORDER}

    for r in results:
        out  = r["output"]
        name = r["name"]

        if name == "gitleaks":
            for line in grep(out, "finding", "secret", "token", "password", "key"):
                findings["P0_CRITICAL"].append(f"[gitleaks] {line.strip()}")
        elif name == "trivy":
            for line in grep(out, "critical"):
                findings["P0_CRITICAL"].append(f"[trivy] {line.strip()}")
            for line in grep(out, "high"):
                findings["P1_HIGH"].append(f"[trivy] {line.strip()}")
            for line in grep(out, "medium"):
                findings["P2_MEDIUM"].append(f"[trivy] {line.strip()}")
        elif name in ("pip-audit", "safety", "npm-audit", "govulncheck"):
            for line in grep(out, "critical", "high"):
                findings["P0_CRITICAL"].append(f"[{name}] {line.strip()}")
            for line in grep(out, "medium", "moderate"):
                findings["P1_HIGH"].append(f"[{name}] {line.strip()}")
        elif name == "pytest":
            for line in grep(out, "failed", "error"):
                findings["P1_HIGH"].append(f"[pytest] {line.strip()}")
            for line in grep(out, "missing", "%"):
                findings["P2_MEDIUM"].append(f"[coverage] {line.strip()}")
        elif name == "hadolint":
            for line in grep(out, "DL", "SC"):
                t = "P1_HIGH" if "error" in line.lower() else "P2_MEDIUM"
                findings[t].append(f"[hadolint] {line.strip()}")
        elif name in ("checkov", "tfsec"):
            for line in grep(out, "failed check", "error"):
                findings["P1_HIGH"].append(f"[{name}] {line.strip()}")
        elif name == "mypy":
            for line in grep(out, "error:"):
                findings["P1_HIGH"].append(f"[mypy] {line.strip()}")
        elif name in ("ansible-lint", "helm-lint", "terraform-validate",
                      "kubectl-dry-run"):
            for line in grep(out, "error"):
                findings["P1_HIGH"].append(f"[{name}] {line.strip()}")
            for line in grep(out, "warning"):
                findings["P2_MEDIUM"].append(f"[{name}] {line.strip()}")
        elif name == "kube-score":
            for line in grep(out, "critical"):
                findings["P1_HIGH"].append(f"[kube-score] {line.strip()}")
            for line in grep(out, "warning"):
                findings["P2_MEDIUM"].append(f"[kube-score] {line.strip()}")
        elif name == "yamllint":
            for line in grep(out, "error"):
                findings["P2_MEDIUM"].append(f"[yamllint] {line.strip()}")
            for line in grep(out, "warning"):
                findings["P3_LOW"].append(f"[yamllint] {line.strip()}")
        elif name == "interrogate":
            for line in grep(out, "result:", "%"):
                findings["P3_LOW"].append(f"[interrogate] {line.strip()}")
        elif name in ("black", "isort"):
            for line in grep(out, "would reformat", "ERROR"):
                findings["P3_LOW"].append(f"[{name}] {line.strip()}")

    # MCP placeholder entries — Cline appends real findings after MCP calls
    findings["P0_CRITICAL"].append(
        "[Semgrep MCP] → call semgrep_scan(path='.', config='auto') "
        "and semgrep_scan_supply_chain(path='.') — append findings here"
    )
    findings["P2_MEDIUM"].append(
        "[Project Health Auditor MCP] → call file_metrics(path=<file>) "
        "for each source file — append complexity/MI findings here"
    )
    if profile.has_api:
        findings["P2_MEDIUM"].append(
            f"[API Debugger MCP] → call load_openapi() then ingest_logs() "
            f"for {profile.api_framework} endpoints — append failures here"
        )

    tier_labels = {
        "P0_CRITICAL": "P0 — CRITICAL  fix before any other work",
        "P1_HIGH":     "P1 — HIGH      fix before P2 work begins",
        "P2_MEDIUM":   "P2 — MEDIUM    fix after P0/P1 are clear",
        "P3_LOW":      "P3 — LOW       parallelize freely",
    }

    lines = [
        "# Unified Gap Report — Phase 0 Baseline",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Sources",
        "- Subprocess checks: see individual reports/baseline_<check>.txt",
        "- Semgrep MCP:       reports/mcp_semgrep_baseline.json (Cline appends)",
        "- Health Auditor:    reports/mcp_health_*.json (Cline appends)",
        "- API Debugger:      reports/mcp_api_baseline.json (Cline appends, if API)",
        "",
        "## Severity Tiers",
        "",
    ]
    for tier, label in tier_labels.items():
        lines.append(f"### {label}")
        items = findings[tier]
        lines += [f"- {i}" for i in items] if items else ["- ✅ none found"]
        lines.append("")

    gap_path = REPORTS / "gap_report.md"
    gap_path.write_text("\n".join(lines))

    json_path = REPORTS / "gap_report.json"
    json_path.write_text(json.dumps(findings, indent=2))

    print(f"  Gap report:        {gap_path}")
    print(f"  Gap report (JSON): {json_path}")


def print_detect_report(p: ProjectProfile, suite: dict[str, dict]) -> None:
    """Print detection results and check routing table."""
    print(f"\n{'━'*60}")
    print("  PROJECT DETECTION REPORT")
    print(f"{'━'*60}")
    print(f"\n  Detected: {', '.join(p.detected) or 'nothing — run from project root'}")
    if p.has_api:
        print(f"  API:      {p.api_framework} → API Debugger MCP will be used")
    print(f"\n  {'Check':<22} {'Tier':<14} {'Handler':<35} Status")
    print(f"  {'─'*22} {'─'*14} {'─'*35} {'─'*10}")

    for name, check in suite.items():
        tier    = check.get("tier", "n/a")
        missing = check.get("_missing_tool")
        mcp     = check.get("_mcp_owned")
        handler = check.get("_mcp_server", "subprocess") if mcp else "subprocess"
        if missing:
            status = f"SKIPPED — install {missing}"
        elif mcp:
            status = "→ MCP"
        else:
            status = "ENABLED"
        print(f"  {name:<22} {tier:<14} {handler:<35} {status}")

    enabled   = [n for n, c in suite.items()
                 if "_missing_tool" not in c and "_mcp_owned" not in c]
    mcp_owned = [n for n, c in suite.items() if "_mcp_owned"    in c]
    skipped   = [n for n, c in suite.items() if "_missing_tool" in c]

    print(f"\n  Subprocess checks: {len(enabled)}")
    print(f"  MCP-handled:       {len(mcp_owned)}  ({', '.join(mcp_owned)})")
    if skipped:
        print(f"  Skipped:           {len(skipped)}  ({', '.join(skipped)})")
    print()


# ─── ENTRYPOINT ──────────────────────────────────────────────────────────────

def main() -> None:
    """Dispatch to detect, recon, audit, or single check."""
    mode    = sys.argv[1] if len(sys.argv) > 1 else "help"
    profile = detect_project()
    suite   = build_check_suite(profile)
    order   = ordered_checks(suite)

    if mode == "detect":
        print_detect_report(profile, suite)

    elif mode == "recon":
        print_detect_report(profile, suite)
        results = run_suite(
            suite, order,
            label="PHASE 0 — SUBPROCESS BASELINE (failures expected)",
            baseline=True,
        )
        write_summary(results)
        write_gap_report(results, profile)
        print("\n  Subprocess recon complete.")
        print("  Next steps for Cline:")
        print("    1. semgrep_scan(path='.', config='auto')")
        print("    2. semgrep_scan_supply_chain(path='.')")
        print("    3. list_repo_files() + map_tests('.') + git_churn('.')")
        print("    4. file_metrics(path=<file>) for each source file")
        if profile.has_api:
            print(f"    5. load_openapi() + ingest_logs() [{profile.api_framework}]")
        print("    6. Consolidate all findings into reports/gap_report.md")
        print("    7. memory_store(content=gap_report_json, metadata={type:'gap_report'})")

    elif mode == "audit":
        print_detect_report(profile, suite)
        results = run_suite(
            suite, order,
            label="PHASE 2 — SUBPROCESS VALIDATION (zero tolerance)",
            baseline=False,
        )
        write_summary(results)
        print("\n  Subprocess checks: PASSED")
        print("  Cline must also verify:")
        print("    semgrep_scan(path='.', config='auto')           → zero CRITICAL/HIGH")
        print("    semgrep_scan_supply_chain(path='.')             → zero vulnerabilities")
        print("    file_metrics(path=<file>) for all source files  → CC≤10, MI≥65")
        if profile.has_api:
            print(f"    ingest_logs(logs=<fresh_logs>)                  → zero failures")
        print("    memory_store(content='PASSED', metadata={type:'audit_status'})")

    elif mode in suite:
        REPORTS.mkdir(exist_ok=True)
        check = suite[mode]
        if "_mcp_owned" in check:
            print(f"\n  {check['label']} is handled by MCP:")
            print(f"  {check['_mcp_server']}")
            print("  Call that MCP tool directly from Cline.")
            sys.exit(0)
        result = run_check(mode, check)
        status = "PASSED" if result["passed"] else "FAILED"
        print(f"\n  {result['label']}: {status}")
        sys.exit(0 if result["passed"] else 1)

    else:
        print(__doc__)
        print(f"\n  Detected: {', '.join(profile.detected) or 'none'}")
        print(f"\n  Subprocess checks (this project):")
        for name in order:
            c = suite[name]
            print(f"    {name:<22} [{c.get('tier','?')}]  {c['label']}")
        print(f"\n  MCP-handled checks:")
        for name, c in suite.items():
            if "_mcp_owned" in c:
                print(f"    {name:<22} [{c.get('tier','?')}]  {c['_mcp_server']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
