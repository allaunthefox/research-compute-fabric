#!/usr/bin/env python3
"""
ENE Artifact Salvage Extractor
==============================

Purpose
-------
Extract useful, sanitized research artifacts from legacy ENE archive records
without carrying forward false claims, contaminated phrasing, or obsolete math.

Core rule
---------
Wrong math may still contain a valid artifact. Salvage the artifact, not the
false claim.

This tool is deliberately conservative. It does not emit the old claim body by
default. It emits sanitized receipts containing only:

- provenance pointers and hashes;
- classification of why the record is interesting;
- sanitized reusable core;
- failure/contamination flags;
- current-stack mapping hints;
- non-claims.

It is intended for legacy review passes where the operator does not want old
patterns to infect current reasoning.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


EXTRACTION_VERSION = "ene_artifact_salvage_extractor_v0.1"


@dataclasses.dataclass(frozen=True)
class SalvageConfig:
    max_records: Optional[int]
    min_score: int
    include_rejected: bool
    emit_legacy_snippets: bool


@dataclasses.dataclass
class SalvageReceipt:
    salvage_id: str
    source_archive_id: str
    source_type: str
    source_file: str
    source_hash: str
    extraction_version: str
    interest_score: int
    salvage_class: str
    interest_reasons: List[str]
    contamination_flags: List[str]
    sanitized_core: str
    current_stack_mapping: Dict[str, List[str]]
    recommended_next_action: str
    allowed_claims: List[str]
    non_claims: List[str]
    legacy_snippet: Optional[str] = None


def stable_hash(obj: Any, n: int = 32) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def load_archive(path: Path) -> List[Dict[str, Any]]:
    archive = json.loads(path.read_text(encoding="utf-8"))
    records = archive.get("records", archive)
    if isinstance(records, dict):
        return list(records.values())
    if isinstance(records, list):
        return records
    raise ValueError("Archive must contain records as a dict or list")


INTEREST_PATTERNS: Dict[str, List[str]] = {
    "compression_invariant": [
        r"compression", r"codec", r"entropy", r"hutter", r"canonical", r"precompression",
        r"arithmetic coding", r"log[- ]?loss", r"minimum description", r"md[l]",
    ],
    "manifold_topology": [
        r"manifold", r"topolog", r"torsion", r"curvature", r"ricci", r"fiber",
        r"bundle", r"geodesic", r"metric", r"basin", r"attractor",
    ],
    "avm_or_bytecode": [
        r"\bAVM\b", r"bytecode", r"stack", r"kernel", r"trace", r"q16", r"fixed[- ]?point",
        r"deterministic", r"golden trace",
    ],
    "nuvmap_addressing": [
        r"NUVMAP", r"address", r"projection", r"virtual memory", r"uv map", r"coordinate",
        r"spectral mode", r"witness", r"receipt",
    ],
    "s3c_sphinx_gcl": [
        r"S3C", r"AngrySphinx", r"sphinx", r"GCL", r"grammar", r"lawful", r"gate",
        r"quarantine", r"scar", r"throttle", r"shell",
    ],
    "photonic_witness": [
        r"photonic", r"photon", r"Quandela", r"Perceval", r"boson", r"HOM", r"linear optical",
        r"spectral witness", r"sampling",
    ],
    "lean_formalization": [
        r"Lean", r"theorem", r"proof", r"sorry", r"formal", r"lemma", r"lake build",
        r"Q16_16", r"Semantics\.",
    ],
    "hardware_loopback": [
        r"FPGA", r"Tang Nano", r"UART", r"loopback", r"hardware", r"synthesis", r"bit[- ]?exact",
        r"Verilog", r"RTL",
    ],
    "negative_control_or_failure": [
        r"failed", r"wrong", r"gap", r"limitation", r"counterexample", r"negative control",
        r"overclaim", r"not prove", r"boundary", r"quarantine",
    ],
    "cross_domain_adapter": [
        r"adapter", r"cross[- ]?domain", r"translation", r"mapping", r"homology", r"equivalence",
        r"route", r"bridge", r"workflow", r"process graph",
    ],
    "mass_number_diat": [
        r"DIAT", r"mass number", r"square", r"shell", r"gap", r"parity", r"mirror",
        r"codon", r"distance to", r"integer",
    ],
}


CONTAMINATION_PATTERNS: Dict[str, List[str]] = {
    "proof_inflation": [
        r"proved.*navier", r"proved.*millennium", r"solved.*burgers", r"solved.*navier",
        r"global regularity", r"proof of everything", r"final theorem",
    ],
    "physics_overclaim": [
        r"actual mass", r"semantic mass is physical", r"quantum advantage", r"photonic.*solve",
        r"violates", r"free energy", r"perpetual",
    ],
    "ai_as_validator": [
        r"LLM.*proved", r"AI.*validated", r"model agrees therefore", r"consensus of models",
    ],
    "float_hot_path": [
        r"float.*hot", r"f32", r"f64", r"floating point.*authoritative",
    ],
    "unsafe_or_sensitive": [
        r"credential", r"token", r"secret", r"private key", r"password", r"exploit", r"payload",
        r"dox", r"retaliat", r"malware",
    ],
    "medical_or_financial_overclaim": [
        r"cures", r"diagnoses", r"guaranteed profit", r"market oracle", r"investment advice",
    ],
}


STACK_MAPPING: Dict[str, List[Tuple[str, str]]] = {
    "nuvmap": [
        ("nuvmap_addressing", "Candidate for address/projection receipt or non-uniform routing surface"),
        ("photonic_witness", "Project witness statistics into addressable spectral coordinates"),
        ("hardware_loopback", "Project hardware trace locations into NUVMAP receipt space"),
    ],
    "avm": [
        ("avm_or_bytecode", "Candidate for deterministic Q16.16 scoring or trace replay"),
        ("compression_invariant", "Candidate for AVM kernel scoring/compression law test"),
        ("hardware_loopback", "Candidate for bit-exact replay target"),
    ],
    "s3c": [
        ("s3c_sphinx_gcl", "Candidate for shell/codon expansion gate"),
        ("mass_number_diat", "Candidate for shell pressure or square-gap codonization"),
        ("cross_domain_adapter", "Candidate route through compressed adapter space"),
    ],
    "metaprobe": [
        ("negative_control_or_failure", "Candidate failure surface / harder probe family"),
        ("cross_domain_adapter", "Candidate for adapter stress-test generation"),
    ],
    "gcl": [
        ("s3c_sphinx_gcl", "Candidate grammar/lawfulness boundary"),
        ("negative_control_or_failure", "Candidate claim-boundary rule or forbidden region"),
    ],
    "lean": [
        ("lean_formalization", "Candidate local theorem or proof-boundary target"),
        ("avm_or_bytecode", "Candidate bytecode correctness theorem"),
    ],
}


SAFE_WORD_REPLACEMENTS = [
    (re.compile(r"\bproved\b", re.I), "claimed"),
    (re.compile(r"\bsolved\b", re.I), "attempted"),
    (re.compile(r"\bguarantees?\b", re.I), "suggests"),
    (re.compile(r"\bquantum advantage\b", re.I), "photonic sampling behavior"),
    (re.compile(r"\bglobal regularity\b", re.I), "bounded formal target"),
]


def normalize_text(record: Dict[str, Any]) -> str:
    text = record.get("extracted_text")
    if not text:
        raw = record.get("raw_content", {})
        text = json.dumps(raw, ensure_ascii=False, default=str)
    text = str(text)
    # Remove obvious secret-like long tokens from any optional legacy snippet path.
    text = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s]+", r"\1: [REDACTED]", text)
    text = re.sub(r"[A-Za-z0-9_\-]{48,}", "[LONG_TOKEN_REDACTED]", text)
    return text


def match_categories(text: str, patterns: Dict[str, List[str]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for category, pats in patterns.items():
        count = 0
        for pat in pats:
            count += len(re.findall(pat, text, flags=re.I))
        if count:
            out[category] = count
    return out


def summarize_core(categories: Dict[str, int], contamination: Dict[str, int]) -> str:
    if not categories:
        return "No sanitized reusable core detected by the current rules."

    ordered = sorted(categories.items(), key=lambda kv: (-kv[1], kv[0]))
    top = [k for k, _ in ordered[:4]]

    phrases = []
    if "compression_invariant" in top:
        phrases.append("compression/invariant extraction candidate")
    if "manifold_topology" in top:
        phrases.append("manifold or topological structure candidate")
    if "avm_or_bytecode" in top:
        phrases.append("deterministic AVM/bytecode scoring candidate")
    if "nuvmap_addressing" in top:
        phrases.append("NUVMAP address/projection candidate")
    if "s3c_sphinx_gcl" in top:
        phrases.append("S3C/GCL/AngrySphinx routing candidate")
    if "photonic_witness" in top:
        phrases.append("photonic witness or sampling candidate")
    if "lean_formalization" in top:
        phrases.append("Lean/formalization target candidate")
    if "hardware_loopback" in top:
        phrases.append("hardware loopback or bit-exact replay candidate")
    if "negative_control_or_failure" in top:
        phrases.append("failure surface / negative-control candidate")
    if "cross_domain_adapter" in top:
        phrases.append("cross-domain adapter candidate")
    if "mass_number_diat" in top:
        phrases.append("DIAT/mass-number shell-pressure candidate")

    if not phrases:
        phrases = [k.replace("_", " ") for k in top]

    sentence = "Sanitized artifact core: " + "; ".join(phrases) + "."
    if contamination:
        sentence += " Original claim language requires quarantine before reuse."
    return sentence


def salvage_class(categories: Dict[str, int], contamination: Dict[str, int], score: int) -> str:
    if contamination.get("unsafe_or_sensitive"):
        return "QUARANTINE_ONLY"
    if contamination and categories:
        return "SALVAGEABLE_CORE_WITH_CLAIM_SCAR"
    if categories.get("negative_control_or_failure"):
        return "NEGATIVE_CONTROL_OR_FAILURE_SURFACE"
    if categories.get("cross_domain_adapter") or categories.get("mass_number_diat"):
        return "RECONTEXTUALIZE_WITH_CURRENT_STACK"
    if score >= 6:
        return "SALVAGEABLE_CORE"
    return "LOW_CONFIDENCE_REVIEW"


def build_stack_mapping(categories: Dict[str, int]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    for layer, rules in STACK_MAPPING.items():
        hits = [msg for category, msg in rules if category in categories]
        if hits:
            mapping[layer] = hits
    return mapping


def recommended_action(cls: str) -> str:
    return {
        "QUARANTINE_ONLY": "Do not reintroduce content. Preserve only hash/provenance and safety flag.",
        "SALVAGEABLE_CORE_WITH_CLAIM_SCAR": "Extract sanitized core, preserve old claim only as a non-authoritative scar, and require new evidence before reuse.",
        "NEGATIVE_CONTROL_OR_FAILURE_SURFACE": "Convert into a negative control, MetaProbe target, or GCL boundary test.",
        "RECONTEXTUALIZE_WITH_CURRENT_STACK": "Map into current NUVMAP/AVM/S3C vocabulary and discard obsolete derivation language.",
        "SALVAGEABLE_CORE": "Promote as sanitized candidate artifact with receipt and claim boundary.",
        "LOW_CONFIDENCE_REVIEW": "Keep only if a human or downstream model finds a concrete invariant.",
    }.get(cls, "Review conservatively.")


def sanitize_snippet(text: str, max_len: int = 700) -> str:
    snippet = re.sub(r"\s+", " ", text).strip()[:max_len]
    for pat, repl in SAFE_WORD_REPLACEMENTS:
        snippet = pat.sub(repl, snippet)
    return snippet


def score_record(categories: Dict[str, int], contamination: Dict[str, int]) -> int:
    score = 0
    for cat, count in categories.items():
        score += min(count, 5)
    # Failures can be interesting, but severe contamination suppresses promotion.
    if contamination.get("unsafe_or_sensitive"):
        score -= 999
    elif contamination:
        score -= min(sum(contamination.values()), 5)
    return score


def make_receipt(record: Dict[str, Any], cfg: SalvageConfig) -> Optional[SalvageReceipt]:
    text = normalize_text(record)
    categories = match_categories(text, INTEREST_PATTERNS)
    contamination = match_categories(text, CONTAMINATION_PATTERNS)
    score = score_record(categories, contamination)

    if score < cfg.min_score and not (cfg.include_rejected and categories):
        return None

    src_id = str(record.get("archive_id") or stable_hash(record))
    src_hash = str(record.get("content_hash") or stable_hash(record.get("raw_content", text)))
    cls = salvage_class(categories, contamination, score)
    sanitized_core = summarize_core(categories, contamination)
    mapping = build_stack_mapping(categories)

    receipt_obj = {
        "source_archive_id": src_id,
        "source_hash": src_hash,
        "categories": categories,
        "contamination": contamination,
        "version": EXTRACTION_VERSION,
    }
    salvage_id = "ene_salvage_" + stable_hash(receipt_obj, 24)

    return SalvageReceipt(
        salvage_id=salvage_id,
        source_archive_id=src_id,
        source_type=str(record.get("source_type", "unknown")),
        source_file=str(record.get("source_file", "unknown")),
        source_hash=src_hash,
        extraction_version=EXTRACTION_VERSION,
        interest_score=score,
        salvage_class=cls,
        interest_reasons=sorted(categories.keys()),
        contamination_flags=sorted(contamination.keys()),
        sanitized_core=sanitized_core,
        current_stack_mapping=mapping,
        recommended_next_action=recommended_action(cls),
        allowed_claims=[
            "This receipt identifies a sanitized reusable artifact candidate.",
            "This receipt may support recontextualization, negative-control generation, or theorem-target discovery.",
        ],
        non_claims=[
            "Does not validate the original math.",
            "Does not preserve original proof claims.",
            "Does not imply domain equivalence.",
            "Does not imply PDE proof, quantum advantage, market prediction, or hardware correctness.",
        ],
        legacy_snippet=sanitize_snippet(text) if cfg.emit_legacy_snippets else None,
    )


def extract(archive_path: Path, out_path: Path, cfg: SalvageConfig) -> Dict[str, Any]:
    records = load_archive(archive_path)
    receipts: List[SalvageReceipt] = []

    for i, record in enumerate(records):
        if cfg.max_records is not None and i >= cfg.max_records:
            break
        rec = make_receipt(record, cfg)
        if rec is not None:
            receipts.append(rec)

    receipts.sort(key=lambda r: (-r.interest_score, r.salvage_class, r.source_archive_id))

    payload = {
        "meta": {
            "extraction_version": EXTRACTION_VERSION,
            "source_archive": str(archive_path),
            "total_input_records": len(records),
            "total_salvage_receipts": len(receipts),
            "min_score": cfg.min_score,
            "legacy_snippets_emitted": cfg.emit_legacy_snippets,
            "policy": "sanitize_by_default_salvage_artifact_not_false_claim",
        },
        "receipts": [dataclasses.asdict(r) for r in receipts],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract sanitized salvage receipts from ENE archive")
    parser.add_argument("archive", type=Path, help="Path to ene_complete_archive.json")
    parser.add_argument("--out", type=Path, default=Path("shared-data/ene_salvage_receipts.json"))
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--min-score", type=int, default=2)
    parser.add_argument("--include-rejected", action="store_true")
    parser.add_argument("--emit-legacy-snippets", action="store_true", help="Unsafe for clean-room review; off by default")
    args = parser.parse_args()

    cfg = SalvageConfig(
        max_records=args.max_records,
        min_score=args.min_score,
        include_rejected=args.include_rejected,
        emit_legacy_snippets=args.emit_legacy_snippets,
    )
    payload = extract(args.archive, args.out, cfg)
    print(json.dumps(payload["meta"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
