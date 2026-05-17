#!/usr/bin/env python3
"""Extract equation-pattern features from a bounded arXiv source sample.

The extractor downloads source packages from arXiv e-print URLs into an external
cache, reads TeX files, and emits equation hashes plus structural features.  It
does not store equation text in the repo.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = Path("/home/allaun/Documents/ingest/kaggledataset.zip")
DEFAULT_CACHE = Path("/home/allaun/Documents/ingest/arxiv_sources")
OUT_DIR = REPO / "shared-data" / "data" / "math_research_databases"
EQUATION_JSONL = OUT_DIR / "arxiv_equation_pattern_records.jsonl"
PAPER_JSONL = OUT_DIR / "arxiv_equation_pattern_papers.jsonl"
COMMAND_CSV = OUT_DIR / "arxiv_equation_pattern_commands.csv"
SUMMARY = OUT_DIR / "arxiv_equation_pattern_summary.json"
RECEIPT = OUT_DIR / "arxiv_equation_pattern_receipt.json"


MATH_PREFIXES = (
    "math",
    "stat",
    "cs.",
    "nlin",
    "q-bio",
    "q-fin",
    "quant-ph",
    "hep-th",
    "math-ph",
)

DISPLAY_ENV_NAMES = (
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "eqnarray",
    "eqnarray*",
    "displaymath",
    "flalign",
    "flalign*",
    "alignat",
    "alignat*",
)
DISPLAY_ENV_RE = re.compile(
    r"\\begin\{(" + "|".join(re.escape(name) for name in DISPLAY_ENV_NAMES) + r")\}(.*?)\\end\{\1\}",
    re.DOTALL,
)
BRACKET_DISPLAY_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
DOUBLE_DOLLAR_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
INLINE_DOLLAR_RE = re.compile(r"(?<!\\)\$(?!\$)(.{1,500}?)(?<!\\)\$", re.DOTALL)
COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")
OPERATOR_RE = re.compile(r"(?:<=|>=|!=|:=|->|=>|[=<>+\-*/^_&|])")
GREEK_COMMANDS = {
    "\\alpha",
    "\\beta",
    "\\gamma",
    "\\delta",
    "\\epsilon",
    "\\varepsilon",
    "\\zeta",
    "\\eta",
    "\\theta",
    "\\vartheta",
    "\\iota",
    "\\kappa",
    "\\lambda",
    "\\mu",
    "\\nu",
    "\\xi",
    "\\pi",
    "\\rho",
    "\\sigma",
    "\\tau",
    "\\upsilon",
    "\\phi",
    "\\varphi",
    "\\chi",
    "\\psi",
    "\\omega",
    "\\Gamma",
    "\\Delta",
    "\\Theta",
    "\\Lambda",
    "\\Xi",
    "\\Pi",
    "\\Sigma",
    "\\Phi",
    "\\Psi",
    "\\Omega",
}
FAMILY_COMMANDS = {
    "fraction": {"\\frac", "\\dfrac", "\\tfrac"},
    "integral": {"\\int", "\\iint", "\\iiint", "\\oint"},
    "summation": {"\\sum", "\\prod", "\\coprod"},
    "limit": {"\\lim", "\\sup", "\\inf", "\\max", "\\min"},
    "set": {"\\in", "\\subset", "\\subseteq", "\\cup", "\\cap", "\\setminus", "\\emptyset"},
    "arrow": {"\\to", "\\rightarrow", "\\leftarrow", "\\mapsto", "\\Rightarrow", "\\Longrightarrow"},
    "inequality": {"\\le", "\\leq", "\\ge", "\\geq", "\\neq", "\\sim", "\\simeq", "\\approx"},
    "font": {"\\mathbb", "\\mathcal", "\\mathbf", "\\mathrm", "\\mathfrak", "\\operatorname"},
    "root": {"\\sqrt"},
    "matrix": {"\\matrix", "\\pmatrix", "\\bmatrix", "\\begin"},
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def categories_of(record: dict[str, Any]) -> list[str]:
    raw = record.get("categories")
    if not isinstance(raw, str):
        return []
    return [part for part in raw.split() if part]


def is_math_bearing(categories: list[str]) -> bool:
    return any(cat.startswith(MATH_PREFIXES) for cat in categories)


def text_field(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    return value if isinstance(value, str) else ""


def abstract_marker_score(record: dict[str, Any]) -> int:
    text = "\n".join([text_field(record, "title"), text_field(record, "abstract")])
    return len(COMMAND_RE.findall(text)) + len(INLINE_DOLLAR_RE.findall(text))


def iter_candidate_records(archive: Path, max_scan: int, max_papers: int, min_abstract_markers: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        json_members = [info for info in infos if info.filename.endswith(".json")]
        selected_member = json_members[0] if json_members else infos[0]
        with zf.open(selected_member) as handle:
            for seen, raw_line in enumerate(handle, start=1):
                if max_scan and seen > max_scan:
                    break
                record = json.loads(raw_line)
                cats = categories_of(record)
                if not is_math_bearing(cats):
                    continue
                score = abstract_marker_score(record)
                if score < min_abstract_markers:
                    continue
                candidates.append(
                    {
                        "id": record.get("id"),
                        "title": record.get("title"),
                        "categories": cats,
                        "primary_category": cats[0] if cats else "uncategorized",
                        "abstract_marker_score": score,
                    }
                )
                if len(candidates) >= max_papers:
                    break
    return candidates


def records_by_id(archive: Path, wanted_ids: set[str], max_scan: int) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        json_members = [info for info in infos if info.filename.endswith(".json")]
        selected_member = json_members[0] if json_members else infos[0]
        with zf.open(selected_member) as handle:
            for seen, raw_line in enumerate(handle, start=1):
                if max_scan and seen > max_scan:
                    break
                record = json.loads(raw_line)
                arxiv_id = str(record.get("id", ""))
                if arxiv_id not in wanted_ids:
                    continue
                cats = categories_of(record)
                found.append(
                    {
                        "id": arxiv_id,
                        "title": record.get("title"),
                        "categories": cats,
                        "primary_category": cats[0] if cats else "uncategorized",
                        "abstract_marker_score": abstract_marker_score(record),
                        "doi": record.get("doi"),
                        "versions": record.get("versions"),
                    }
                )
                if len(found) >= len(wanted_ids):
                    break
    missing = wanted_ids - {str(row["id"]) for row in found}
    for arxiv_id in sorted(missing):
        found.append(
            {
                "id": arxiv_id,
                "title": None,
                "categories": [],
                "primary_category": "uncategorized",
                "abstract_marker_score": 0,
                "metadata_missing": True,
            }
        )
    return found


def fetch_source(arxiv_id: str, cache_dir: Path, delay_seconds: float) -> tuple[Path | None, str | None]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_id = arxiv_id.replace("/", "_")
    cached = cache_dir / f"{safe_id}.src"
    if cached.exists() and cached.stat().st_size > 0:
        return cached, None
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    req = Request(url, headers={"User-Agent": "ResearchStack equation-pattern extractor (local bounded study)"})
    try:
        with urlopen(req, timeout=60) as response:
            data = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        return None, repr(exc)
    cached.write_bytes(data)
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    return cached, None


def strip_comments(tex: str) -> str:
    lines = []
    for line in tex.splitlines():
        out = []
        escaped = False
        for ch in line:
            if ch == "%" and not escaped:
                break
            out.append(ch)
            escaped = ch == "\\" and not escaped
        lines.append("".join(out))
    return "\n".join(lines)


def read_tex_sources(path: Path, max_tex_bytes: int) -> tuple[list[tuple[str, str]], str]:
    data = path.read_bytes()
    tex_files: list[tuple[str, str]] = []
    mode = "plain"
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
            mode = "tar"
            for member in tf.getmembers():
                if not member.isfile() or not member.name.lower().endswith((".tex", ".ltx")):
                    continue
                if member.size > max_tex_bytes:
                    continue
                extracted = tf.extractfile(member)
                if extracted is None:
                    continue
                text = extracted.read(max_tex_bytes).decode("utf-8", errors="replace")
                tex_files.append((member.name, text))
            return tex_files, mode
    except tarfile.TarError:
        pass
    try:
        text = gzip.decompress(data).decode("utf-8", errors="replace")
        mode = "gzip_plain"
    except OSError:
        text = data.decode("utf-8", errors="replace")
    if "\\documentclass" in text or "\\begin" in text:
        tex_files.append((path.name, text[:max_tex_bytes]))
    return tex_files, mode


def extract_equations(tex: str) -> list[tuple[str, str]]:
    clean = strip_comments(tex)
    equations: list[tuple[str, str]] = []
    for match in DISPLAY_ENV_RE.finditer(clean):
        equations.append((match.group(1), match.group(2)))
    for match in BRACKET_DISPLAY_RE.finditer(clean):
        equations.append(("bracket_display", match.group(1)))
    for match in DOUBLE_DOLLAR_RE.finditer(clean):
        equations.append(("double_dollar", match.group(1)))
    for match in INLINE_DOLLAR_RE.finditer(clean):
        equations.append(("inline_dollar", match.group(1)))
    return equations


def equation_features(equation: str) -> dict[str, Any]:
    normalized = " ".join(equation.split())
    commands = COMMAND_RE.findall(normalized)
    operators = OPERATOR_RE.findall(normalized)
    command_counts = Counter(commands)
    families = {
        family: sum(command_counts.get(cmd, 0) for cmd in cmds)
        for family, cmds in FAMILY_COMMANDS.items()
    }
    greek_count = sum(command_counts.get(cmd, 0) for cmd in GREEK_COMMANDS)
    signature_parts = []
    for family, count in sorted(families.items()):
        if count:
            signature_parts.append(f"{family}:{count}")
    if greek_count:
        signature_parts.append(f"greek:{greek_count}")
    signature_parts.append(f"cmds:{len(commands)}")
    signature_parts.append(f"ops:{len(operators)}")
    signature = "|".join(signature_parts)
    return {
        "equation_sha256": sha256_text(normalized),
        "char_length": len(normalized),
        "command_count": len(commands),
        "operator_count": len(operators),
        "greek_command_count": greek_count,
        "family_counts": families,
        "top_commands": command_counts.most_common(20),
        "signature": signature,
        "signature_hash": sha256_text(signature),
    }


def csv_escape(value: Any) -> str:
    text = str(value).replace('"', '""')
    return f'"{text}"'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE))
    parser.add_argument("--max-scan", type=int, default=5000)
    parser.add_argument("--max-papers", type=int, default=12)
    parser.add_argument("--min-abstract-markers", type=int, default=2)
    parser.add_argument("--delay-seconds", type=float, default=3.0)
    parser.add_argument("--max-tex-bytes", type=int, default=5_000_000)
    parser.add_argument("--max-equations-per-paper", type=int, default=1000)
    parser.add_argument("--ids", default="")
    args = parser.parse_args()

    archive = Path(args.archive).expanduser().resolve()
    cache_dir = Path(args.cache_dir).expanduser().resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wanted_ids = {part.strip() for part in args.ids.split(",") if part.strip()}
    if wanted_ids:
        candidates = records_by_id(archive=archive, wanted_ids=wanted_ids, max_scan=args.max_scan)
    else:
        candidates = iter_candidate_records(
            archive=archive,
            max_scan=args.max_scan,
            max_papers=args.max_papers,
            min_abstract_markers=args.min_abstract_markers,
        )

    equation_records: list[dict[str, Any]] = []
    paper_records: list[dict[str, Any]] = []
    command_totals: Counter[str] = Counter()
    signature_totals: Counter[str] = Counter()
    family_totals: Counter[str] = Counter()
    env_totals: Counter[str] = Counter()
    fetch_status: Counter[str] = Counter()

    for candidate in candidates:
        arxiv_id = str(candidate["id"])
        source_path, error = fetch_source(arxiv_id, cache_dir, args.delay_seconds)
        if source_path is None:
            fetch_status["fetch_error"] += 1
            paper_records.append({**candidate, "decision": "HOLD", "error": error})
            continue
        source_sha = sha256_bytes(source_path.read_bytes())
        tex_files, source_mode = read_tex_sources(source_path, args.max_tex_bytes)
        paper_eq_count = 0
        paper_command_count = 0
        for tex_name, tex in tex_files:
            for env, equation in extract_equations(tex)[: args.max_equations_per_paper]:
                features = equation_features(equation)
                record = {
                    "schema": "arxiv_equation_pattern_record_v1",
                    "arxiv_id": arxiv_id,
                    "primary_category": candidate["primary_category"],
                    "categories": candidate["categories"],
                    "source_sha256": source_sha,
                    "tex_file": tex_name,
                    "environment": env,
                    **features,
                }
                record["packet_hash"] = sha256_text(stable_json(record))
                equation_records.append(record)
                paper_eq_count += 1
                paper_command_count += features["command_count"]
                env_totals[env] += 1
                signature_totals[features["signature_hash"]] += 1
                for family, count in features["family_counts"].items():
                    family_totals[family] += count
                for command, count in features["top_commands"]:
                    command_totals[command] += count
        fetch_status["fetched"] += 1
        paper = {
            "schema": "arxiv_equation_pattern_paper_v1",
            **candidate,
            "source_cache_path": str(source_path),
            "source_sha256": source_sha,
            "source_mode": source_mode,
            "tex_file_count": len(tex_files),
            "equation_count": paper_eq_count,
            "equation_command_count": paper_command_count,
            "decision": "HOLD",
        }
        paper["packet_hash"] = sha256_text(stable_json(paper))
        paper_records.append(paper)

    EQUATION_JSONL.write_text("\n".join(stable_json(r) for r in equation_records) + "\n", encoding="utf-8")
    PAPER_JSONL.write_text("\n".join(stable_json(r) for r in paper_records) + "\n", encoding="utf-8")
    command_lines = ["command,count"]
    for command, count in command_totals.most_common(300):
        command_lines.append(f"{csv_escape(command)},{count}")
    COMMAND_CSV.write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    summary = {
        "schema": "arxiv_equation_pattern_summary_v1",
        "archive_path": str(archive),
        "source_cache_dir": str(cache_dir),
        "candidate_count": len(candidates),
        "paper_count": len(paper_records),
        "fetch_status": dict(fetch_status),
        "equation_count": len(equation_records),
        "unique_equation_hashes": len({r["equation_sha256"] for r in equation_records}),
        "unique_signature_hashes": len(signature_totals),
        "top_environments": env_totals.most_common(30),
        "top_commands": command_totals.most_common(80),
        "family_totals": dict(family_totals),
        "top_signature_hashes": signature_totals.most_common(40),
        "equation_records": str(EQUATION_JSONL.relative_to(REPO)),
        "paper_records": str(PAPER_JSONL.relative_to(REPO)),
        "command_csv": str(COMMAND_CSV.relative_to(REPO)),
        "decision": "HOLD",
        "claim_boundary": (
            "Bounded arXiv source sample. Repo stores equation hashes and structural "
            "features only, not equation text. This is compression-surface evidence, "
            "not theorem verification or full-corpus coverage."
        ),
    }
    summary["packet_hash"] = sha256_text(stable_json(summary))
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema": "arxiv_equation_pattern_receipt_v1",
        "summary": str(SUMMARY.relative_to(REPO)),
        "candidate_count": summary["candidate_count"],
        "paper_count": summary["paper_count"],
        "fetch_status": summary["fetch_status"],
        "equation_count": summary["equation_count"],
        "unique_equation_hashes": summary["unique_equation_hashes"],
        "unique_signature_hashes": summary["unique_signature_hashes"],
        "top_environments": summary["top_environments"][:10],
        "top_commands": summary["top_commands"][:20],
        "family_totals": summary["family_totals"],
        "packet_hash": summary["packet_hash"],
        "decision": summary["decision"],
        "claim_boundary": summary["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
