#!/usr/bin/env python3
"""Lean QC Flagger — code quality inspection per Lean Expert Agent 5-point protocol."""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path


SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


class QCIssue:
    def __init__(self, check, message, line=0, severity=SEVERITY_WARNING):
        self.check = check
        self.message = message
        self.line = line
        self.severity = severity

    def to_dict(self):
        return {
            "check": self.check,
            "message": self.message,
            "line": self.line,
            "severity": self.severity,
        }


class FileResult:
    def __init__(self, path):
        self.path = str(path)
        self.issues = []
        self.structural = {}
        self.passed = True

    def add_issue(self, issue):
        self.issues.append(issue)
        if issue.severity == SEVERITY_ERROR:
            self.passed = False

    def to_dict(self):
        return {
            "path": self.path,
            "passed": self.passed,
            "issue_count": len(self.issues),
            "structural": self.structural,
            "issues": [i.to_dict() for i in self.issues],
        }


def _get_line(content, pos):
    return content[:pos].count("\n") + 1


def _def_names(content):
    return set(m.group(1) for m in re.finditer(r'\bdef\s+(\w+)', content))


def _theorem_names(content):
    return set(m.group(1) for m in re.finditer(r'\btheorem\s+(\w+)', content))


def _private_def_names(content):
    return set(m.group(1) for m in re.finditer(r'\bprivate\s+def\s+(\w+)', content))


def _get_imports(content):
    return re.findall(r'^import\s+(\S+)', content, re.MULTILINE)


def _get_opens(content):
    return re.findall(r'^open\s+(\S+)', content, re.MULTILINE)


def _normalize_path_sep(module_name):
    return module_name.replace("\\", "/")


def _get_code_lines(content):
    lines = content.split('\n')
    is_code = [True] * len(lines)
    in_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if in_block:
            is_code[i] = False
            if '-/' in stripped:
                in_block = False
                idx = stripped.index('-/')
                after = stripped[idx+2:]
                if after and not after.startswith('--'):
                    is_code[i] = True
            continue
        if stripped.startswith('/-') and '-/' in stripped:
            idx = stripped.index('-/')
            remainder = stripped[idx+2:].lstrip()
            if remainder.startswith('--') or not remainder:
                is_code[i] = False
                continue
            code_part = stripped[:idx].rstrip()
            if code_part:
                is_code[i] = True
            else:
                is_code[i] = 'partial'
            continue
        if stripped.startswith('/-'):
            is_code[i] = False
            in_block = True
            continue
        if stripped.startswith('--') or not stripped:
            is_code[i] = False
            continue
    return is_code


def _pos_is_code(content, pos, code_lines=None):
    if code_lines is None:
        code_lines = _get_code_lines(content)
    ln = _get_line(content, pos) - 1
    if ln < 0 or ln >= len(code_lines):
        return True
    return code_lines[ln] == True


def _is_data_def(content, def_name):
    pat = re.compile(
        r'def\s+' + re.escape(def_name) + r'\s*(:\s*\w+\s*)?:=\s*\{',
        re.DOTALL
    )
    if pat.search(content):
        return True
    pat2 = re.compile(
        r'def\s+' + re.escape(def_name) + r'\s*:\s*\w+\s*:=\s*-?\d+',
        re.MULTILINE
    )
    return bool(pat2.search(content))


def check_structural_health(content, result):
    lines = content.split("\n")

    theorem_count = len(re.findall(r'\btheorem\s+\w+', content))
    def_count = len(re.findall(r'\bdef\s+\w+', content))
    eval_bang_count = len(re.findall(r'#eval!', content))
    eval_count = len(re.findall(r'#eval(?!\!)', content))

    sorry_matches = [m for m in re.finditer(r'\bsorry\b', content) if _pos_is_code(content, m.start())]
    sorry_count = len(sorry_matches)

    native_decide_count = len(re.findall(r'\bnative_decide\b', content))
    set_option_count = len(re.findall(r'\bset_option\s', content))

    empty_theorem_count = 0
    for m in re.finditer(r'theorem\s+\w+.*?:=\s*by', content):
        pos = m.end()
        rest = content[pos:].lstrip()
        if (not rest or
            rest.startswith('theorem ') or
            rest.startswith('def ') or
            rest.startswith('inductive ') or
            rest.startswith('structure ') or
            rest.startswith('end ') or
            rest.startswith('#eval') or
            rest.startswith('--')):
            empty_theorem_count += 1

    tautologies = []
    for m in re.finditer(r'theorem\s+\w+\s+(.*?)\s*:=', content):
        stmt = m.group(1)
        stmt_line = _get_line(content, m.start())
        for eq_m in re.finditer(r'(=+|≤|≥|<)', stmt):
            lhs = stmt[:eq_m.start()].strip()
            rhs = stmt[eq_m.end():].strip()
            lhs_simple = re.sub(r'\s+', ' ', lhs)
            rhs_simple = re.sub(r'\s+', ' ', rhs)
            if lhs_simple == rhs_simple and re.match(r'^[\w\s]+$', lhs_simple):
                tautologies.append((lhs_simple + " " + eq_m.group(0) + " " + rhs_simple, stmt_line))

    result.structural = {
        "theorems": theorem_count,
        "defs": def_count,
        "eval": eval_count,
        "eval_bang": eval_bang_count,
        "sorries": sorry_count,
        "native_decide": native_decide_count,
        "set_option_suppressions": set_option_count,
        "empty_theorems": empty_theorem_count,
        "tautologies": len(tautologies),
    }

    if sorry_count > 0:
        for m in sorry_matches:
            ln = _get_line(content, m.start())
            result.add_issue(QCIssue(
                "structural_health", f"sorry axiom at line {ln}",
                ln, SEVERITY_ERROR
            ))

    if empty_theorem_count > 0:
        result.add_issue(QCIssue(
            "structural_health",
            f"{empty_theorem_count} empty theorem body(s) found",
            0, SEVERITY_WARNING
        ))

    for taut, ln in tautologies:
        result.add_issue(QCIssue(
            "structural_health",
            f"Tautology '{taut}' at line {ln}",
            ln, SEVERITY_WARNING
        ))


def check_naming_conventions(content, result, file_path):
    stem = os.path.basename(file_path)
    if stem.endswith(".lean"):
        stem = stem[:-5]

    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', stem):
        result.add_issue(QCIssue(
            "naming_conventions",
            f"File name '{stem}.lean' is not PascalCase",
            0, SEVERITY_WARNING
        ))

    if "_" in stem:
        result.add_issue(QCIssue(
            "naming_conventions",
            f"File name '{stem}.lean' uses banned snake_case",
            0, SEVERITY_ERROR
        ))

    code_lines_info = _get_code_lines(content)

    for m in re.finditer(r'\b(inductive|structure|class)\s+(\w+)', content):
        if not _pos_is_code(content, m.start(), code_lines_info):
            continue
        name = m.group(2)
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
            ln = _get_line(content, m.start())
            result.add_issue(QCIssue(
                "naming_conventions",
                f"Type '{name}' is not PascalCase at line {ln}",
                ln, SEVERITY_WARNING
            ))

    for m in re.finditer(r'\bdef\s+(\w+)', content):
        if not _pos_is_code(content, m.start(), code_lines_info):
            continue
        name = m.group(1)
        if not re.match(r'^[a-z][a-zA-Z0-9]*$', name):
            ln = _get_line(content, m.start())
            result.add_issue(QCIssue(
                "naming_conventions",
                f"Function '{name}' is not camelCase at line {ln}",
                ln, SEVERITY_WARNING
            ))

    for m in re.finditer(r'\btheorem\s+(\w+)', content):
        if not _pos_is_code(content, m.start(), code_lines_info):
            continue
        name = m.group(1)
        if not re.match(r'^[a-z][a-zA-Z0-9]*$', name):
            ln = _get_line(content, m.start())
            result.add_issue(QCIssue(
                "naming_conventions",
                f"Theorem '{name}' is not camelCase at line {ln}",
                ln, SEVERITY_WARNING
            ))

    for m in re.finditer(r'\b(get|set|check)([A-Z]\w*)\b', content):
        if not _pos_is_code(content, m.start(), code_lines_info):
            continue
        name = m.group(0)
        ln = _get_line(content, m.start())
        result.add_issue(QCIssue(
            "naming_conventions",
            f"Banned prefix in '{name}' at line {ln}",
            ln, SEVERITY_WARNING
        ))

    for m in re.finditer(r'\b\w*(_v2|_final)\b', content):
        if not _pos_is_code(content, m.start(), code_lines_info):
            continue
        name = m.group(0)
        ln = _get_line(content, m.start())
        result.add_issue(QCIssue(
            "naming_conventions",
            f"Banned suffix in '{name}' at line {ln}",
            ln, SEVERITY_WARNING
        ))


def check_q16_compliance(content, result):
    code_lines_info = _get_code_lines(content)
    for m in re.finditer(r'\bFloat\b', content):
        if not _pos_is_code(content, m.start(), code_lines_info):
            continue
        ln = _get_line(content, m.start())
        result.add_issue(QCIssue(
            "q16_compliance",
            f"Float usage at line {ln} (prefer Q16_16)",
            ln, SEVERITY_WARNING
        ))


def check_proof_quality(content, result):
    lines = content.split("\n")
    defs = _def_names(content)
    thms = _theorem_names(content)
    pdefs = _private_def_names(content)

    theorem_bodies = {}
    for m in re.finditer(r'theorem\s+(\w+)\s+(.*?)\s*:=', content, re.DOTALL):
        theorem_bodies[m.group(1)] = m.group(2)

    eval_refs = set()
    for m in re.finditer(r'#eval!?\s+(\S+)', content):
        eval_refs.add(m.group(1))

    for dn in sorted(defs):
        if dn in pdefs:
            continue
        if _is_data_def(content, dn):
            continue
        companion = False
        for tn, body in theorem_bodies.items():
            if dn in body:
                companion = True
                break
        if dn in eval_refs:
            companion = True
        if companion:
            continue
        for i, line in enumerate(lines, 1):
            m2 = re.match(r'^\s*def\s+' + re.escape(dn) + r'\b', line)
            if m2:
                result.add_issue(QCIssue(
                    "proof_quality",
                    f"def '{dn}' at line {i} has no companion theorem or #eval witness",
                    i, SEVERITY_WARNING
                ))
                break

    for m in re.finditer(r'(\w+)\.get!', content):
        var = m.group(1)
        is_some_found = False
        for tn, body in theorem_bodies.items():
            if var + ".isSome" in body or var + " " in body + ".isSome":
                is_some_found = True
                break
            if "isSome" in tn and var.lower() in tn.lower():
                is_some_found = True
                break
        if not is_some_found:
            ln = _get_line(content, m.start())
            result.add_issue(QCIssue(
                "proof_quality",
                f".get! call on '{var}' at line {ln} without companion .isSome theorem",
                ln, SEVERITY_WARNING
            ))


def check_dependency_analysis(content, result, file_path, all_files_imports=None):
    imports = _get_imports(content)
    opens = _get_opens(content)
    body = content

    for imp_line in re.finditer(r'^import\s+\S+', content, re.MULTILINE):
        body = body.replace(imp_line.group(0), "", 1)
    for open_line in re.finditer(r'^open\s+\S+', content, re.MULTILINE):
        body = body.replace(open_line.group(0), "", 1)
    body = re.sub(r'^namespace\s+\S+', '', body, flags=re.MULTILINE)
    body = re.sub(r'--.*$', '', body, flags=re.MULTILINE)
    body = re.sub(r'/\*[\s\S]*?\*/', '', body)

    for imp in imports:
        segments = imp.split(".")
        short = segments[-1]
        opened = any(imp in o or short in o for o in opens)
        used = opened or short in body or imp in body
        if not used:
            for i, line in enumerate(content.split("\n"), 1):
                if line.strip().startswith("import") and imp in line:
                    result.add_issue(QCIssue(
                        "dependency_analysis",
                        f"Unused import '{imp}' at line {i}",
                        i, SEVERITY_INFO
                    ))
                    break

    if all_files_imports is not None and file_path in all_files_imports:
        file_module = _normalize_path_sep(file_path)
        deps = all_files_imports.get(file_path, [])
        for dep in deps:
            dep_path = _normalize_path_sep(dep.replace(".", "/") + ".lean")
            if dep_path in all_files_imports:
                dep_deps = all_files_imports[dep_path]
                file_mod_short = (".").join(
                    _normalize_path_sep(file_path).replace(".lean", "").split("/")[-2:]
                ) if "/" in _normalize_path_sep(file_path) else _normalize_path_sep(file_path).replace(".lean", "")
                dep_short = dep
                if any(file_mod_short in d for d in dep_deps):
                    result.add_issue(QCIssue(
                        "dependency_analysis",
                        f"Circular dependency: {file_mod_short} <-> {dep_short}",
                        0, SEVERITY_ERROR
                    ))

        for dep in deps:
            dep_path = _normalize_path_sep(dep.replace(".", "/") + ".lean")
            if dep_path in all_files_imports:
                dep_transitives = set()
                _collect_transitives(dep_path, all_files_imports, dep_transitives, set())
                file_mod_short = _normalize_path_sep(file_path).replace(".lean", "").replace("/", ".")
                if any(file_mod_short in t for t in dep_transitives):
                    result.add_issue(QCIssue(
                        "dependency_analysis",
                        f"Transitive circular dependency involving {file_mod_short}",
                        0, SEVERITY_ERROR
                    ))


def _collect_transitives(module_path, all_imports, visited, in_stack):
    if module_path in in_stack:
        visited.add(module_path)
        return
    if module_path in visited:
        return
    in_stack.add(module_path)
    for dep in all_imports.get(module_path, []):
        dep_path = _normalize_path_sep(dep.replace(".", "/") + ".lean")
        _collect_transitives(dep_path, all_imports, visited, in_stack)
    in_stack.discard(module_path)


def scan_file(file_path, all_files_imports=None):
    result = FileResult(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        result.add_issue(QCIssue(
            "io_error", f"Cannot read file: {e}", 0, SEVERITY_ERROR
        ))
        return result

    check_structural_health(content, result)
    check_naming_conventions(content, result, file_path)
    check_q16_compliance(content, result)
    check_proof_quality(content, result)
    check_dependency_analysis(content, result, file_path, all_files_imports)

    return result


def gather_imports(file_paths):
    all_imports = {}
    for fp in file_paths:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        all_imports[fp] = _get_imports(content)
    return all_imports


def find_lean_files(path):
    path = Path(path)
    if path.is_file():
        return [str(path)]
    elif path.is_dir():
        return [str(p) for p in path.rglob("*.lean")]
    return []


def generate_markdown_report(results, target_path):
    total_files = len(results)
    passed_files = sum(1 for r in results if r.passed)
    total_issues = sum(len(r.issues) for r in results)

    lines = []
    lines.append(f"# QC Flag Report — {target_path}")
    lines.append(f"**Date:** {date.today()}")
    lines.append(f"**Files scanned:** {total_files}")
    lines.append(f"**Files passed:** {passed_files}/{total_files}")
    lines.append(f"**Total issues:** {total_issues}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| File | Pass | Issues |")
    lines.append("|------|------|--------|")
    for r in sorted(results, key=lambda x: x.path):
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"| {r.path} | {status} | {len(r.issues)} |")
    lines.append("")

    for r in sorted(results, key=lambda x: x.path):
        if not r.issues:
            continue
        lines.append(f"## {r.path}")
        lines.append("")
        lines.append(f"**Verdict:** {'PASS' if r.passed else 'FAIL'}")
        lines.append("")
        if r.structural:
            lines.append("### Structural Counts")
            lines.append("")
            for k, v in r.structural.items():
                lines.append(f"- {k}: {v}")
            lines.append("")
        lines.append("### Issues")
        lines.append("")
        lines.append("| # | Line | Severity | Check | Message |")
        lines.append("|---|------|----------|-------|---------|")
        for i, issue in enumerate(r.issues, 1):
            sev_icon = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "ℹ️"}.get(issue.severity, "")
            line_str = str(issue.line) if issue.line > 0 else "-"
            lines.append(f"| {i} | {line_str} | {sev_icon} {issue.severity} | {issue.check} | {issue.message} |")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Lean QC Flagger - code quality inspection per Lean Expert Agent 5-point protocol"
    )
    parser.add_argument("target", help="Target Lean file or directory to scan")
    parser.add_argument("--json", "-j", help="Output JSON report to file")
    parser.add_argument("--markdown", "-m", help="Output Markdown report to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")

    args = parser.parse_args()

    target_path = args.target
    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    lean_files = find_lean_files(target_path)
    if not lean_files:
        print(f"Error: No .lean files found in '{target_path}'", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(lean_files)} Lean file(s) to scan")

    all_imports = gather_imports(lean_files)

    results = []
    for lf in lean_files:
        if args.verbose:
            print(f"  Scanning {lf}...")
        result = scan_file(lf, all_imports)
        results.append(result)

    json_output = json.dumps([r.to_dict() for r in results], indent=2)
    markdown_output = generate_markdown_report(results, target_path)

    if args.json:
        with open(args.json, "w") as f:
            f.write(json_output)
        print(f"JSON report written to {args.json}")

    if args.markdown:
        with open(args.markdown, "w") as f:
            f.write(markdown_output)
        print(f"Markdown report written to {args.markdown}")

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    issues = sum(len(r.issues) for r in results)

    print(f"\n{'='*60}")
    print(f"QC Flag Scan Complete")
    print(f"{'='*60}")
    print(f"Target:     {target_path}")
    print(f"Files:      {total}")
    print(f"Passed:     {passed}/{total}")
    print(f"Issues:     {issues}")
    print(f"{'='*60}")

    for r in sorted(results, key=lambda x: x.path):
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.path} ({len(r.issues)} issues)")

    if not args.json and not args.markdown:
        print("\n--- JSON Report ---")
        print(json_output)

    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
