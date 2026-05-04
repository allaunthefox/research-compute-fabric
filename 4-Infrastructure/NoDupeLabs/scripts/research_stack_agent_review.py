#!/usr/bin/env python3
"""
Research Stack Agent Review Harness

Static + optional execution review for the current Research Stack.

Default mode is conservative: static checks only. Use --execute to run generators
and validators. This script is intentionally local-first; it does not call OpenAI,
Wolfram, GitHub, or external web APIs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "research-stack" / "agent-review"
JSON_REPORT = REPORT_DIR / "research_stack_agent_review.json"
MD_REPORT = REPORT_DIR / "research_stack_agent_review.md"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    severity: str = "info"  # info | warn | error


@dataclass
class CommandResult:
    command: str
    ran: bool
    ok: bool
    returncode: Optional[int] = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    skipped_reason: str = ""


@dataclass
class SubsystemReview:
    subsystem: str
    status: str
    maturity: List[str] = field(default_factory=list)
    checks: List[CheckResult] = field(default_factory=list)
    commands: List[CommandResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)

    def recompute_status(self) -> None:
        if self.status == "QUARANTINE":
            return
        if any(c.severity == "error" and not c.ok for c in self.checks):
            self.status = "SCAR"
            return
        if any(c.severity == "warn" and not c.ok for c in self.checks):
            self.status = "HOLD"
            return
        if self.commands and any(cmd.ran and not cmd.ok for cmd in self.commands):
            self.status = "SCAR"
            return
        if self.commands and any(not cmd.ran for cmd in self.commands):
            self.status = "HOLD"
            return
        if "VALIDATOR_PASSES" in self.maturity or "DOWNSTREAM_CONNECTED" in self.maturity:
            self.status = "PASS"
        elif self.maturity:
            self.status = "HOLD"
        else:
            self.status = "MISSING"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def file_check(path: str, severity: str = "warn") -> CheckResult:
    return CheckResult(name=f"file_exists:{path}", ok=exists(path), detail=path, severity=severity)


def read_text(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def run_command(command: List[str], execute: bool, timeout: int = 120) -> CommandResult:
    printable = " ".join(command)
    if not execute:
        return CommandResult(command=printable, ran=False, ok=False, skipped_reason="execution disabled; use --execute")
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return CommandResult(
            command=printable,
            ran=True,
            ok=completed.returncode == 0,
            returncode=completed.returncode,
            stdout_tail=completed.stdout[-2000:],
            stderr_tail=completed.stderr[-2000:],
        )
    except FileNotFoundError as exc:
        return CommandResult(command=printable, ran=True, ok=False, returncode=None, stderr_tail=str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(command=printable, ran=True, ok=False, returncode=None, stdout_tail=(exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "", stderr_tail="timeout")


def add_maturity(review: SubsystemReview, level: str, condition: bool) -> None:
    if condition and level not in review.maturity:
        review.maturity.append(level)


def review_measurement_registry(execute: bool) -> SubsystemReview:
    r = SubsystemReview("measurement_registry", "HOLD")
    required = [
        "research-stack/constants/si_2019_exact_constants_v0.json",
        "research-stack/constants/physical_constants_foundation_v0.json",
        "research-stack/constants/measurement_standards_source_catalog_v0.json",
        "research-stack/constants/README_MEASUREMENT_REGISTRY.md",
        "src/plumbing/constants_registry_builder.ts",
    ]
    for path in required:
        r.checks.append(file_check(path, "error"))
    add_maturity(r, "SPEC_EXISTS", all(exists(p) for p in required[:4]))
    add_maturity(r, "CODE_EXISTS", exists(required[-1]))
    cmd = run_command(["npx", "tsx", "src/plumbing/constants_registry_builder.ts"], execute, timeout=180)
    r.commands.append(cmd)
    registry_path = "research-stack/constants/constants_registry_v0.json"
    if execute:
        r.checks.append(file_check(registry_path, "error"))
        add_maturity(r, "RUNS_LOCALLY", cmd.ok)
        add_maturity(r, "EMITS_ARTIFACTS", exists(registry_path))
        if exists(registry_path):
            try:
                data = json.loads(read_text(registry_path))
                count = int(data.get("record_count", 0))
                r.checks.append(CheckResult("constants_registry_record_count_positive", count > 0, f"record_count={count}", "error"))
                r.checks.append(CheckResult("constants_registry_has_adapter_coverage", "adapter_coverage" in data, "adapter_coverage present", "warn"))
            except Exception as exc:
                r.checks.append(CheckResult("constants_registry_json_parse", False, str(exc), "error"))
    r.next_actions.append("Audit first imported upstream source beyond seed packs: CODATA/NIST constants adapter.")
    r.recompute_status()
    return r


def review_source_adapters() -> SubsystemReview:
    r = SubsystemReview("measurement_source_adapters", "HOLD")
    path = "src/plumbing/measurement_source_adapters.ts"
    r.checks.append(file_check(path, "error"))
    add_maturity(r, "CODE_EXISTS", exists(path))
    txt = read_text(path)
    for token in ["BIPM", "CODATA", "NIST", "UCUM", "QUDT", "NOAA", "PDG", "ISO"]:
        r.checks.append(CheckResult(f"adapter_mentions:{token}", token in txt, token, "warn"))
    r.notes.append("Adapter registry is source-boundary infrastructure; it does not imply data has been imported.")
    r.next_actions.append("Implement one real open adapter and mark licensed sources metadata-only until lawful access exists.")
    r.recompute_status()
    return r


def review_semantic_number_pattern_search(execute: bool) -> SubsystemReview:
    r = SubsystemReview("semantic_number_pattern_search", "HOLD")
    path = "src/plumbing/semantic_number_pattern_search.ts"
    r.checks.append(file_check(path, "error"))
    add_maturity(r, "CODE_EXISTS", exists(path))
    txt = read_text(path)
    r.checks.append(CheckResult("holds_results_not_basins", "outcome: \"hold\"" in txt or "Every result remains HOLD" in txt, "HOLD rule found", "warn"))
    r.checks.append(CheckResult("has_false_attractor_report", "false_attractor_report" in txt, "false-attractor output referenced", "warn"))
    cmd = run_command(["npx", "tsx", "src/plumbing/semantic_number_pattern_search.ts"], execute, timeout=240)
    r.commands.append(cmd)
    outputs = [
        "research-stack/semantic-number-patterns/numeric_motifs.json",
        "research-stack/semantic-number-patterns/numeric_pattern_roads.json",
        "research-stack/semantic-number-patterns/numeric_torsion_candidates.json",
        "research-stack/semantic-number-patterns/false_attractor_report.json",
    ]
    if execute:
        add_maturity(r, "RUNS_LOCALLY", cmd.ok)
        for out in outputs:
            r.checks.append(file_check(out, "error"))
        add_maturity(r, "EMITS_ARTIFACTS", all(exists(o) for o in outputs))
    r.next_actions.append("Add abstract_cot_equation_pack_v0.json to default equation pack set or CLI input.")
    r.recompute_status()
    return r


def review_abstract_cot() -> SubsystemReview:
    r = SubsystemReview("abstract_cot_integration", "HOLD")
    required = [
        "research-stack/models/abstract_cot_integration_v0.md",
        "research-stack/equation-packs/abstract_cot_equation_pack_v0.json",
        "research-stack/formal/abstract_cot_entropy_review_v0.md",
        "scripts/normalize_math_model_map.py",
        "research-stack/models/MATH_MODEL_MAP.abstract_cot.normalized.tsv",
    ]
    for path in required:
        r.checks.append(file_check(path, "warn"))
    add_maturity(r, "SPEC_EXISTS", exists(required[0]) and exists(required[2]))
    add_maturity(r, "CODE_EXISTS", exists(required[3]))
    add_maturity(r, "EMITS_ARTIFACTS", exists(required[4]))
    review_text = read_text("research-stack/formal/abstract_cot_entropy_review_v0.md")
    r.checks.append(CheckResult("lean_proxy_boundary_present", "not proof-complete" in review_text or "proxy" in review_text, "proxy/proof boundary documented", "error"))
    r.notes.append("Abstract-CoT equations are useful for compression/Hutter routing but remain HOLD until Lean assumptions are formalized.")
    r.next_actions.append("Create a real finite joint-distribution theorem scaffold for information bottleneck; keep Q16_16 as proxy.")
    r.recompute_status()
    return r


def review_chandelier_and_pulsar(execute: bool) -> List[SubsystemReview]:
    reviews: List[SubsystemReview] = []

    c = SubsystemReview("chandelier_genus3_model", "HOLD")
    for path in ["research-stack/models/chandelier_genus3_blueshift_model_v0.md", "scripts/chandelier_genus3_descent.py"]:
        c.checks.append(file_check(path, "warn"))
    add_maturity(c, "SPEC_EXISTS", exists("research-stack/models/chandelier_genus3_blueshift_model_v0.md"))
    add_maturity(c, "CODE_EXISTS", exists("scripts/chandelier_genus3_descent.py"))
    c.commands.append(run_command([sys.executable, "scripts/chandelier_genus3_descent.py"], execute, timeout=180))
    if execute:
        add_maturity(c, "RUNS_LOCALLY", c.commands[-1].ok)
        outputs = [
            "research-stack/models/chandelier_genus3_outputs/chandelier_genus3_descent_map.png",
            "research-stack/models/chandelier_genus3_outputs/chandelier_genus3_traces.png",
            "research-stack/models/chandelier_genus3_outputs/chandelier_genus3_report.json",
        ]
        for out in outputs:
            c.checks.append(file_check(out, "warn"))
        add_maturity(c, "EMITS_ARTIFACTS", all(exists(o) for o in outputs))
    c.notes.append("Chandelier is a coordinate projection of shrinking accessible phase volume, not proof.")
    c.next_actions.append("Add Doppler gradient trace fields to output report/CSV.")
    c.recompute_status()
    reviews.append(c)

    p = SubsystemReview("pulsar_genus3_model", "HOLD")
    for path in ["research-stack/models/pulsar_genus3_two_component_model_v0.md", "scripts/pulsar_genus3_two_component.py"]:
        p.checks.append(file_check(path, "warn"))
    add_maturity(p, "SPEC_EXISTS", exists("research-stack/models/pulsar_genus3_two_component_model_v0.md"))
    add_maturity(p, "CODE_EXISTS", exists("scripts/pulsar_genus3_two_component.py"))
    p.commands.append(run_command([sys.executable, "scripts/pulsar_genus3_two_component.py"], execute, timeout=180))
    if execute:
        add_maturity(p, "RUNS_LOCALLY", p.commands[-1].ok)
        out = "research-stack/models/pulsar_genus3_outputs/pulsar_genus3_report.json"
        p.checks.append(file_check(out, "warn"))
        add_maturity(p, "EMITS_ARTIFACTS", exists(out))
    p.notes.append("Genus-3 is reduced route topology, not literal neutron-star topology.")
    p.next_actions.append("Compare trace classes to pulsar glitch literature only after internal validator passes.")
    p.recompute_status()
    reviews.append(p)
    return reviews


def review_multiscale_pulsar(execute: bool) -> SubsystemReview:
    r = SubsystemReview("pulsar_marble_jar_multiscale", "HOLD")
    for path in ["scripts/pulsar_marble_jar_multiscale.py", "scripts/validate_pulsar_marble_jar_multiscale.py"]:
        r.checks.append(file_check(path, "error"))
    add_maturity(r, "CODE_EXISTS", exists("scripts/pulsar_marble_jar_multiscale.py"))
    add_maturity(r, "VALIDATOR_EXISTS", exists("scripts/validate_pulsar_marble_jar_multiscale.py"))
    sim = run_command([sys.executable, "scripts/pulsar_marble_jar_multiscale.py"], execute, timeout=240)
    val = run_command([sys.executable, "scripts/validate_pulsar_marble_jar_multiscale.py"], execute, timeout=300)
    r.commands.extend([sim, val])
    if execute:
        add_maturity(r, "RUNS_LOCALLY", sim.ok)
        add_maturity(r, "VALIDATOR_PASSES", val.ok)
        outputs = [
            "research-stack/models/pulsar_marble_jar_multiscale_outputs/pulsar_marble_jar_multiscale_report.json",
            "research-stack/models/pulsar_marble_jar_multiscale_outputs/pulsar_marble_jar_multiscale_validation.json",
            "research-stack/models/pulsar_marble_jar_multiscale_outputs/pulsar_marble_jar_multiscale_traces.csv",
        ]
        for out in outputs:
            r.checks.append(file_check(out, "error"))
        add_maturity(r, "EMITS_ARTIFACTS", all(exists(o) for o in outputs))
        if exists(outputs[1]):
            try:
                data = json.loads(read_text(outputs[1]))
                r.checks.append(CheckResult("validator_status_pass", data.get("status") == "PASS", str(data.get("status")), "error"))
            except Exception as exc:
                r.checks.append(CheckResult("validator_json_parse", False, str(exc), "error"))
    r.notes.append("This is the strongest simulation gate because it includes multiscale clocks and invariant checks.")
    r.next_actions.append("Patch Doppler trace schema fields into CSV/report and rerun validator.")
    r.recompute_status()
    return r


def review_doppler_gradient() -> SubsystemReview:
    r = SubsystemReview("doppler_gradient_instrumentation", "HOLD")
    path = "research-stack/gradient-models/doppler_gradient_integration_v0.md"
    r.checks.append(file_check(path, "error"))
    add_maturity(r, "SPEC_EXISTS", exists(path))
    txt = read_text(path)
    for token in ["beta_eff", "doppler_shift", "red_blue_label", "flash_event", "phase_boundary_id"]:
        r.checks.append(CheckResult(f"required_trace_field:{token}", token in txt, token, "warn"))
    simulation_files = [
        "scripts/chandelier_genus3_descent.py",
        "scripts/pulsar_genus3_two_component.py",
        "scripts/pulsar_marble_jar_multiscale.py",
    ]
    wired = 0
    for path2 in simulation_files:
        t = read_text(path2)
        has_fields = all(token in t for token in ["doppler", "flash"])
        wired += 1 if has_fields else 0
        r.checks.append(CheckResult(f"partial_doppler_wiring:{path2}", has_fields, "contains doppler + flash", "warn"))
    add_maturity(r, "DOWNSTREAM_CONNECTED", wired == len(simulation_files))
    r.next_actions.append("Standardize beta_eff / doppler_shift / red_blue_label / phase_boundary_id across all gradient simulations.")
    r.recompute_status()
    return r


def review_graph_and_famm() -> List[SubsystemReview]:
    reviews: List[SubsystemReview] = []
    g = SubsystemReview("graph_lean_canonical_layer", "HOLD")
    candidates = ["Graph.lean", "research-stack/Graph.lean", "ForestGradientRoads.lean", "SemanticNumberPatternSearch.lean"]
    any_exists = any(exists(p) for p in candidates)
    for p in candidates:
        g.checks.append(file_check(p, "warn"))
    add_maturity(g, "CODE_EXISTS", any_exists)
    g.notes.append("Graph.lean is declared canonical but appears underdeveloped relative to simulation/plumbing layers.")
    g.next_actions.append("Create canonical graph/outcome schema in Lean or explicitly mark Lean layer deferred.")
    g.recompute_status()
    reviews.append(g)

    f = SubsystemReview("famm_memory_layer", "HOLD")
    search_paths = ["research-stack", "src", "scripts"]
    found = []
    for base in search_paths:
        root = ROOT / base
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".ts", ".js", ".json", ".md", ".py", ".lean"}:
                    try:
                        if "FAMM" in path.read_text(encoding="utf-8", errors="ignore"):
                            found.append(rel(path))
                    except Exception:
                        pass
    f.checks.append(CheckResult("famm_mentions_found", bool(found), ", ".join(found[:10]), "warn"))
    add_maturity(f, "SPEC_EXISTS", bool(found))
    f.notes.append("FAMM is conceptually present but needs durable read/write implementation for route memory.")
    f.next_actions.append("Implement FAMM state file/store with basin/HOLD/scar write API and validator.")
    f.recompute_status()
    reviews.append(f)
    return reviews


def review_solar_quarantine() -> SubsystemReview:
    r = SubsystemReview("solar_system_quarantine", "QUARANTINE")
    recovery = read_text("research-stack/recovery/recovered_status_2026_04_29.md")
    policy = read_text("research-stack/weights/research_stack_weight_policy_v0.json")
    present = "solar-system" in recovery.lower() or "solar_system" in policy.lower()
    r.checks.append(CheckResult("quarantine_rule_present", present, "solar-system quarantine mention", "error"))
    r.notes.append("Solar-system region remains intentionally unavailable as validation partner until separate verification.")
    r.next_actions.append("Do not route simulation validation through solar-system observations until quarantine is explicitly lifted.")
    return r


def generate_report(reviews: List[SubsystemReview], execute: bool) -> Dict:
    status_counts: Dict[str, int] = {}
    for r in reviews:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    hard_failures = [r.subsystem for r in reviews if r.status == "SCAR"]
    holds = [r.subsystem for r in reviews if r.status == "HOLD"]
    return {
        "review_id": "research_stack_agent_review_v0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "execute_mode": execute,
        "status_counts": status_counts,
        "hard_failures": hard_failures,
        "holds": holds,
        "overall_status": "SCAR" if hard_failures else "HOLD" if holds else "PASS",
        "rule": "Agent review validates stack hygiene, execution, invariants, and authority boundaries. It does not prove scientific or mathematical truth.",
        "reviews": [asdict(r) for r in reviews],
    }


def write_markdown(report: Dict) -> str:
    lines: List[str] = []
    lines.append("# Research Stack Agent Review")
    lines.append("")
    lines.append(f"Generated: `{report['generated_utc']}`")
    lines.append(f"Execution mode: `{report['execute_mode']}`")
    lines.append(f"Overall status: **{report['overall_status']}**")
    lines.append("")
    lines.append("## Status counts")
    lines.append("")
    for status, count in sorted(report["status_counts"].items()):
        lines.append(f"- `{status}`: {count}")
    lines.append("")
    lines.append("## Subsystems")
    lines.append("")
    for r in report["reviews"]:
        lines.append(f"### {r['subsystem']} — {r['status']}")
        lines.append("")
        lines.append("Maturity: " + (", ".join(f"`{m}`" for m in r["maturity"]) if r["maturity"] else "`none`"))
        failed = [c for c in r["checks"] if not c["ok"]]
        if failed:
            lines.append("")
            lines.append("Failed / missing checks:")
            for c in failed:
                lines.append(f"- `{c['severity']}` `{c['name']}` — {c.get('detail','')}")
        cmds = r.get("commands", [])
        if cmds:
            lines.append("")
            lines.append("Commands:")
            for cmd in cmds:
                state = "PASS" if cmd["ok"] else "SKIP" if not cmd["ran"] else "FAIL"
                detail = cmd.get("skipped_reason") or f"returncode={cmd.get('returncode')}"
                lines.append(f"- `{state}` `{cmd['command']}` — {detail}")
        if r.get("notes"):
            lines.append("")
            lines.append("Notes:")
            for note in r["notes"]:
                lines.append(f"- {note}")
        if r.get("next_actions"):
            lines.append("")
            lines.append("Next actions:")
            for action in r["next_actions"]:
                lines.append(f"- {action}")
        lines.append("")
    lines.append("## Boundary reminder")
    lines.append("")
    lines.append("Passing this review does not prove the Research Stack. It only shows that files, runs, validators, and declared authority boundaries are visible enough to continue safely.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Run generators and validators.")
    parser.add_argument("--no-execute", action="store_true", help="Explicit static-only mode.")
    args = parser.parse_args()
    execute = bool(args.execute and not args.no_execute)

    reviews: List[SubsystemReview] = []
    reviews.append(review_measurement_registry(execute))
    reviews.append(review_source_adapters())
    reviews.append(review_semantic_number_pattern_search(execute))
    reviews.append(review_abstract_cot())
    reviews.extend(review_chandelier_and_pulsar(execute))
    reviews.append(review_multiscale_pulsar(execute))
    reviews.append(review_doppler_gradient())
    reviews.extend(review_graph_and_famm())
    reviews.append(review_solar_quarantine())

    report = generate_report(reviews, execute)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    MD_REPORT.write_text(write_markdown(report), encoding="utf-8")

    print(json.dumps({
        "overall_status": report["overall_status"],
        "status_counts": report["status_counts"],
        "json_report": rel(JSON_REPORT),
        "markdown_report": rel(MD_REPORT),
        "execute_mode": execute,
    }, indent=2))

    # Only fail the process on hard SCAR in execute mode. Static review should be usable as inventory.
    if execute and report["overall_status"] == "SCAR":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
