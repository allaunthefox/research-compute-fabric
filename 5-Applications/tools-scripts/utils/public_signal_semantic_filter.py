#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Bounded semantic filter for public promotional signal objects.

This module does not try to prove fraud, botting, or illegality.
It classifies public posts as signal objects using a staged sieve posture so
they can be routed away from technical evidence lanes.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STAGE_INGEST = "ingest_sieve"
STAGE_BREAKUP = "breakup_normalization"
STAGE_CLASSIFY = "classification_sieve"
STAGE_LIBERATE = "liberation_aggregation"
STAGE_HANDOFF = "recovery_handoff"

SAFE_LABELS = (
    "promotional_funnel",
    "engagement_bait",
    "copy_trading_sales_copy",
    "authority_laundering",
    "impossible_smoothness_claim",
    "not_technical_evidence",
)


@dataclass(frozen=True)
class SignalFeature:
    name: str
    pattern: re.Pattern[str]
    category: str
    weight: float
    rationale: str


FEATURES: Tuple[SignalFeature, ...] = (
    SignalFeature(
        "spouse_story_credibility",
        re.compile(r"\b(my wife|showed her the terminal|while she slept)\b", re.I),
        "promotional_funnel",
        1.8,
        "Domestic witness framing is being used as credibility theater.",
    ),
    SignalFeature(
        "micro_pnl_theater",
        re.compile(r"\+\$\d+(?:\.\d{1,2})?\s+captured", re.I),
        "promotional_funnel",
        2.0,
        "Tiny stepwise PnL increments are being presented as live proof.",
    ),
    SignalFeature(
        "wallet_copy_claim",
        re.compile(r"\b(scan(?:ned)?\s+\d[\d,]*\s+wallets|copies?\s+them|copy(?:ing)?\s+them)\b", re.I),
        "copy_trading_sales_copy",
        2.4,
        "The pitch centers on copying wallet behavior rather than bounded analysis.",
    ),
    SignalFeature(
        "impossible_consistency",
        re.compile(r"\b(never lose|never dips|asleep|it just keeps going)\b", re.I),
        "impossible_smoothness_claim",
        2.6,
        "The post implies implausibly smooth or one-directional returns.",
    ),
    SignalFeature(
        "ai_authority_name_drop",
        re.compile(r"\bclaude\b", re.I),
        "authority_laundering",
        1.6,
        "An AI system name is being used as an authority shortcut.",
    ),
    SignalFeature(
        "legal_reassurance_hook",
        re.compile(r"\b(that'?s legal|legal\?)\b", re.I),
        "promotional_funnel",
        1.2,
        "The copy anticipates legality concerns and converts them into persuasion.",
    ),
    SignalFeature(
        "institutional_analogy",
        re.compile(r"\b(citadel|nyse|400 engineers)\b", re.I),
        "authority_laundering",
        1.5,
        "Institutional references are being used to launder credibility.",
    ),
    SignalFeature(
        "scarcity_window",
        re.compile(r"\bfree\s+for\s+24\s+hours\b", re.I),
        "engagement_bait",
        2.2,
        "A short scarcity window is being used as a conversion lever.",
    ),
    SignalFeature(
        "engagement_cta_stack",
        re.compile(
            r"\b(comment\s+the\s+word|like\s+and\s+retweet|follow\s+me|so i can dm you)\b",
            re.I,
        ),
        "engagement_bait",
        2.8,
        "The post includes stacked engagement actions to unlock access.",
    ),
    SignalFeature(
        "effortless_automation_claim",
        re.compile(r"\b(1 hour/day|doing what\?\s*nothing)\b", re.I),
        "promotional_funnel",
        1.7,
        "The copy minimizes effort to increase conversion pressure.",
    ),
)


def normalize_text(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_features(text: str) -> List[Dict[str, object]]:
    findings: List[Dict[str, object]] = []
    normalized = normalize_text(text)
    for feature in FEATURES:
        matches = feature.pattern.findall(normalized)
        if not matches:
            continue
        findings.append(
            {
                "name": feature.name,
                "category": feature.category,
                "count": len(matches),
                "weight": feature.weight,
                "weighted_score": round(len(matches) * feature.weight, 4),
                "rationale": feature.rationale,
            }
        )
    return findings


def score_categories(findings: Sequence[Dict[str, object]]) -> Dict[str, float]:
    scores = {label: 0.0 for label in SAFE_LABELS}
    for finding in findings:
        category = str(finding["category"])
        scores[category] += float(finding["weighted_score"])
    if findings:
        scores["not_technical_evidence"] = round(sum(scores.values()) * 0.35, 4)
    return {key: round(value, 4) for key, value in scores.items()}


def select_labels(scores: Dict[str, float]) -> List[str]:
    # PSF-B: threshold 2.2 calibrated to the weighted_score scale produced by
    # score_categories(): each matching finding contributes finding["weighted_score"]
    # summed per category. A score of 2.2 requires multiple moderate-weight findings
    # or one strong finding to activate a label. If feature weights change, this
    # threshold must be recalibrated against the new score distribution.
    _LABEL_SCORE_THRESHOLD = 2.2
    labels = [name for name, value in scores.items() if value >= _LABEL_SCORE_THRESHOLD]
    if not labels:
        labels = ["not_technical_evidence"]
    return sorted(set(labels))


def stage_trace(text: str, findings: Sequence[Dict[str, object]], scores: Dict[str, float], labels: Sequence[str]) -> List[Dict[str, object]]:
    normalized = normalize_text(text)
    top_categories = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [
        {
            "stage": STAGE_INGEST,
            "summary": "Collected the public post as a signal object.",
            "metrics": {
                "char_count": len(text),
                "word_count": len(text.split()),
                "line_count": len([line for line in text.splitlines() if line.strip()]),
            },
        },
        {
            "stage": STAGE_BREAKUP,
            "summary": "Normalized whitespace and punctuation to compare the copy as one surface.",
            "metrics": {
                "normalized_char_count": len(normalized),
                "feature_candidates": len(FEATURES),
            },
        },
        {
            "stage": STAGE_CLASSIFY,
            "summary": "Matched bounded promotional and evidence-risk features.",
            "metrics": {
                "matched_features": len(findings),
                "labels": list(labels),
            },
        },
        {
            "stage": STAGE_LIBERATE,
            "summary": "Aggregated feature hits into bounded interpretive categories.",
            "metrics": {
                "top_category": top_categories[0][0] if top_categories else "not_technical_evidence",
                "top_score": top_categories[0][1] if top_categories else 0.0,
            },
        },
        {
            "stage": STAGE_HANDOFF,
            "summary": "Classified the post as a signal artifact rather than technical evidence.",
            "metrics": {
                "routing": "public_signal_review",
                "disposition": "do_not_treat_as_performance_evidence",
            },
        },
    ]


def analyze_public_signal_text(text: str) -> Dict[str, object]:
    findings = extract_features(text)
    scores = score_categories(findings)
    labels = select_labels(scores)
    primary_candidates = {key: value for key, value in scores.items() if key != "not_technical_evidence"}
    # PSF-A fix: when all primary scores are 0.0, max() returns the first dict key
    # ("promotional_funnel") because Python tie-breaks by insertion order, not by
    # semantic meaning.  Explicitly fall back to the correct neutral label.
    top_label = (
        max(primary_candidates.items(), key=lambda item: item[1])[0]
        if primary_candidates and max(primary_candidates.values()) > 0
        else "not_technical_evidence"
    )
    return {
        "safe_labels": list(SAFE_LABELS),
        "feature_findings": findings,
        "category_scores": scores,
        "labels": labels,
        "primary_label": top_label,
        "stage_trace": stage_trace(text, findings, scores, labels),
        "claim_boundary": (
            "This report classifies promotional structure. It does not prove botting, "
            "fraud, illegality, or trading performance."
        ),
    }


def load_fixture(path: Path) -> Dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "text" not in data:
        raise ValueError(f"{path} must be a JSON object with a 'text' field")
    return data


def markdown_report(fixture: Dict[str, object], analysis: Dict[str, object]) -> str:
    lines = [
        "# Public Signal Semantic Filter Report",
        "",
        f"**Fixture**: `{fixture.get('id', 'unknown')}`",
        f"**Primary label**: `{analysis['primary_label']}`",
        "",
        "## Labels",
        "",
    ]
    for label in analysis["labels"]:
        lines.append(f"- `{label}`")
    lines.extend(["", "## Feature Findings", ""])
    for finding in analysis["feature_findings"]:
        lines.append(
            "- "
            f"`{finding['name']}` -> `{finding['category']}` "
            f"(count={finding['count']}, weighted_score={finding['weighted_score']})"
        )
        lines.append(f"  {finding['rationale']}")
    lines.extend(["", "## Stage Trace", ""])
    for stage in analysis["stage_trace"]:
        lines.append(f"- `{stage['stage']}`: {stage['summary']}")
    lines.extend(["", "## Claim Boundary", "", analysis["claim_boundary"], ""])
    return "\n".join(lines)


def write_outputs(fixture_path: Path, fixture: Dict[str, object], analysis: Dict[str, object], out_dir: Path) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = fixture_path.stem
    json_path = out_dir / f"{stem}_report.json"
    md_path = out_dir / f"{stem}_report.md"
    payload = {
        "fixture": fixture,
        "analysis": analysis,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(markdown_report(fixture, analysis), encoding="utf-8")
    return json_path, md_path


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", help="Path to JSON fixture with a 'text' field.")
    parser.add_argument(
        "--out-dir",
        default="5-Applications/out/public_signal_filter",
        help="Directory for JSON/Markdown reports.",
    )
    return parser


def main() -> int:
    parser = build_argparser()
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    out_dir = Path(args.out_dir)

    fixture = load_fixture(fixture_path)
    analysis = analyze_public_signal_text(str(fixture["text"]))
    json_path, md_path = write_outputs(fixture_path, fixture, analysis, out_dir)

    print(f"Primary label: {analysis['primary_label']}")
    print("Labels:", ", ".join(analysis["labels"]))
    print(f"Feature hits: {len(analysis['feature_findings'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
