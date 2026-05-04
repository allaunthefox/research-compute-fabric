#!/usr/bin/env python3
"""Normalize text and JSON into a lower-distinctiveness public-facing form."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00a0": " ",
}


@dataclass
class TextRiskMetrics:
    line_count: int
    blank_line_count: int
    repeated_space_runs: int
    repeated_punctuation_runs: int
    tab_count: int
    unicode_punctuation_count: int
    bullet_variants: int
    trailing_whitespace_lines: int
    uppercase_lines: int


def count_matches(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def text_risk_metrics(text: str) -> TextRiskMetrics:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    bullet_tokens = set()
    for line in lines:
        match = re.match(r"^\s*([\-\+\*])\s+", line)
        if match:
            bullet_tokens.add(match.group(1))

    uppercase_lines = 0
    for line in lines:
        stripped = line.strip()
        if stripped and any(ch.isalpha() for ch in stripped) and stripped == stripped.upper():
            uppercase_lines += 1

    return TextRiskMetrics(
        line_count=len(lines),
        blank_line_count=sum(1 for line in lines if not line.strip()),
        repeated_space_runs=count_matches(r" {2,}", text),
        repeated_punctuation_runs=count_matches(r"([!?.,:;])\1+", text),
        tab_count=text.count("\t"),
        unicode_punctuation_count=sum(text.count(ch) for ch in REPLACEMENTS if ord(ch) > 127),
        bullet_variants=len(bullet_tokens),
        trailing_whitespace_lines=count_matches(r"[ \t]+$", text),
        uppercase_lines=uppercase_lines,
    )


def summarize_text_risk(before: str, after: str) -> dict[str, object]:
    before_metrics = text_risk_metrics(before)
    after_metrics = text_risk_metrics(after)
    reduction = {
        key: getattr(before_metrics, key) - getattr(after_metrics, key)
        for key in asdict(before_metrics)
    }
    return {
        "schema": "hutter_smoothing_receipt_v1",
        "mode": "text",
        "before": asdict(before_metrics),
        "after": asdict(after_metrics),
        "reduction": reduction,
    }


def summarize_json_risk(before: str, after: str) -> dict[str, object]:
    before_lines = before.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    after_lines = after.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return {
        "schema": "hutter_smoothing_receipt_v1",
        "mode": "json",
        "before": {
            "line_count": len(before_lines),
            "unicode_punctuation_count": sum(before.count(ch) for ch in REPLACEMENTS if ord(ch) > 127),
        },
        "after": {
            "line_count": len(after_lines),
            "unicode_punctuation_count": sum(after.count(ch) for ch in REPLACEMENTS if ord(ch) > 127),
        },
        "reduction": {
            "unicode_punctuation_count": sum(before.count(ch) for ch in REPLACEMENTS if ord(ch) > 127)
            - sum(after.count(ch) for ch in REPLACEMENTS if ord(ch) > 127),
        },
        "normalized_json": True,
    }


def smooth_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for source, target in REPLACEMENTS.items():
        text = text.replace(source, target)

    lines = []
    for raw_line in text.split("\n"):
        line = raw_line.replace("\t", " ")
        line = re.sub(r"[ ]{2,}", " ", line)
        line = re.sub(r"\s+$", "", line)
        line = re.sub(r"^(\s*)[\*\+]\s+", r"\1- ", line)
        line = re.sub(r"([!?.,:;]){2,}", r"\1", line)
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +\n", "\n", text)
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def smooth_json(text: str) -> str:
    data = json.loads(text)
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input file to smooth.")
    parser.add_argument("--output", required=True, help="Path to write the smoothed artifact.")
    parser.add_argument(
        "--report",
        help="Optional path to write a machine-readable smoothing receipt.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "text", "json"),
        default="auto",
        help="Smoothing mode. Defaults to auto based on the input suffix.",
    )
    return parser.parse_args()


def detect_mode(path: Path, explicit_mode: str) -> str:
    if explicit_mode != "auto":
        return explicit_mode
    if path.suffix.lower() == ".json":
        return "json"
    return "text"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    mode = detect_mode(input_path, args.mode)

    raw = input_path.read_text(encoding="utf-8")
    if mode == "json":
        smoothed = smooth_json(raw)
        receipt = summarize_json_risk(raw, smoothed)
    else:
        smoothed = smooth_text(raw)
        receipt = summarize_text_risk(raw, smoothed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(smoothed, encoding="utf-8")
    if args.report:
        report_path = Path(args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "input_path": str(input_path),
                "output_path": str(output_path),
                "mode": mode,
                "report_path": str(Path(args.report).resolve()) if args.report else None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
