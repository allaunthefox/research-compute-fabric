#!/usr/bin/env python3
"""ENE meta-autotype shim.

When ENE sees data without a defined ingestion surface, this module creates
contingent fields instead of pretending the schema is known. It is intentionally
deterministic: a tiny classifier/autotyper with receipts, not an external LLM.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Any


VERSION = "ene_meta_autotype_v1"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


@dataclass(frozen=True)
class ContingentField:
    name: str
    inferred_type: str
    confidence: float
    extraction_rule: str
    bind_class: str
    status: str = "contingent"


def scalar_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    text = str(value)
    if re.fullmatch(r"[0-9a-f]{64}", text):
        return "sha256_hex"
    if re.fullmatch(r"-?\d+", text):
        return "integer_string"
    if re.fullmatch(r"-?\d+\.\d+", text):
        return "float_string"
    if text.startswith(("http://", "https://")):
        return "url"
    return "string"


def bind_class_for(name: str, inferred_type: str) -> str:
    lower = name.lower()
    if inferred_type in {"sha256_hex"} or "hash" in lower or "receipt" in lower:
        return "attestation_bind"
    if any(token in lower for token in ("x", "y", "z", "coord", "manifold", "topology", "graph")):
        return "geometric_bind"
    if any(token in lower for token in ("policy", "allow", "deny", "risk", "security")):
        return "control_bind"
    return "informational_bind"


def surface_hint(text: str, parsed: Any | None) -> str:
    lower = text.lower()
    if isinstance(parsed, dict):
        keys = {str(key).lower() for key in parsed.keys()}
        if {"nodes", "edges"} & keys or "graphml" in lower:
            return "graph_concept_surface"
        if {"archive_id", "source_type", "raw_content"} <= keys:
            return "ene_archive_surface"
        if {"pkg", "tier", "domain"} <= keys:
            return "ene_package_surface"
    if "<graphml" in lower:
        return "graphml_surface"
    if "[[" in text and "]]" in text:
        return "wiki_surface"
    if re.fullmatch(r"[\sACGTUNRYSWKMBDHV]+", text.upper()) and len(text.strip()) >= 8:
        return "sequence_surface"
    return "unknown_surface"


def autotype_payload(data: bytes, name: str = "payload") -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace")
    parsed: Any | None = None
    fields: list[ContingentField] = []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        for key, value in sorted(parsed.items()):
            inferred = scalar_type(value)
            fields.append(
                ContingentField(
                    name=str(key),
                    inferred_type=inferred,
                    confidence=0.85,
                    extraction_rule=f"json_pointer:/{key}",
                    bind_class=bind_class_for(str(key), inferred),
                )
            )
    elif isinstance(parsed, list):
        fields.append(
            ContingentField(
                name="items",
                inferred_type="array",
                confidence=0.8,
                extraction_rule="json_root_array",
                bind_class="informational_bind",
            )
        )
    else:
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)
        for token in sorted(set(tokens[:64]))[:16]:
            fields.append(
                ContingentField(
                    name=token,
                    inferred_type="token",
                    confidence=0.45,
                    extraction_rule="regex_identifier_token",
                    bind_class=bind_class_for(token, "string"),
                )
            )

    hint = surface_hint(text, parsed)
    raw_content = {
        "kind": "ene_meta_autotype",
        "version": VERSION,
        "name": name,
        "surface_hint": hint,
        "byte_len": len(data),
        "contingent_fields": [asdict(field) for field in fields],
        "policy": {
            "defined_ingestion_surface": hint != "unknown_surface",
            "authority": "contingent_until_bound_by_ingestion_surface",
            "required_gate": ["OBSERVE", "BIND", "ROUTE", "POLICY_CHECK", "VERIFY", "RECEIPT"],
        },
    }
    content_hash = sha256_text(canonical_json(raw_content))
    receipt = sha256_text(canonical_json({"v": VERSION, "content_hash": content_hash, "name": name}))
    return {
        "ok": True,
        "op": "meta_autotype",
        "surface_hint": hint,
        "field_count": len(fields),
        "archive_record": {
            "archive_id": f"json_catalog_ene_meta_autotype_{content_hash[:16]}",
            "source_type": "json_catalog",
            "source_file": f"ene-meta-autotype://{content_hash[:16]}",
            "raw_content": raw_content,
            "extracted_text": text[:10000],
            "extracted_at": iso_utc(),
            "content_hash": content_hash,
            "extraction_version": VERSION,
        },
        "jsonl_event": {
            "src": "ene",
            "op": "upsert",
            "data": {
                "pkg": f"ene/meta-autotype/{content_hash[:16]}",
                "version": VERSION,
                "tier": "RESEARCH",
                "domain": "semantic",
                "archetype": "contingent_schema",
                "tags": ["ene", "meta_autotype", hint],
                "sha256": content_hash,
            },
            "bind": {
                "lawful": True,
                "class": "informational_bind",
                "invariant": "contingent_fields_are_not_authoritative",
            },
            "provenance": {"attestation_hash": f"sha256:{receipt}"},
        },
        "receipt": receipt,
    }


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    if "data_b64" in request:
        data = base64.b64decode(str(request["data_b64"]))
    else:
        data = str(request.get("text", "")).encode("utf-8")
    return autotype_payload(data, str(request.get("name", "payload")))


def main() -> int:
    parser = argparse.ArgumentParser(description="ENE meta-autotype shim")
    parser.add_argument("--name", default="cli")
    parser.add_argument("--text", default="")
    parser.add_argument("--file", type=argparse.FileType("rb"))
    args = parser.parse_args()
    data = args.file.read() if args.file else args.text.encode("utf-8")
    print(json.dumps(autotype_payload(data, args.name), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
