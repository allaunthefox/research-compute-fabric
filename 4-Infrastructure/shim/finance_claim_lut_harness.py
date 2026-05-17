#!/usr/bin/env python3
"""Reversible FinancialClaimPacket LUT compression harness.

JSON is the human/audit envelope. The embedded candidate is a paired binary
surface:

  FCL1: compact field/value token tape
  FCS1: typed literal sidecar

Both must decode back to the canonical FinancialClaimPacket JSON bytes exactly.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
FIXTURE_DIR = SHIM / "finance_claim_lut_fixtures"
BUNDLE_DIR = SHIM / "finance_claim_remote_bundle"
REPORT_DIR = REPO / "6-Documentation" / "reports" / "typst"
LOCAL_TYPST = REPO / "5-Applications" / "tools-scripts" / "external" / "typst-cli" / "bin" / "typst"

FCL1_VERSION = 1
FCS1_VERSION = 1

VALUE_TAG_ENUM = 0
VALUE_TAG_SIDECAR = 1

TYPE_STRING = 1
TYPE_DECIMAL_STRING = 2
TYPE_DATE_STRING = 3
TYPE_RECEIPT_STRING = 4

TYPE_NAMES = {
    TYPE_STRING: "string",
    TYPE_DECIMAL_STRING: "decimal-string",
    TYPE_DATE_STRING: "date-string",
    TYPE_RECEIPT_STRING: "receipt-string",
}

DIRECTION_CODES = {
    "auto": 0,
    "ltr": 1,
    "rtl": 2,
    "bidi": 3,
}

CHIRALITY_CODES = {
    "none": 0,
    "left": 1,
    "right": 2,
    "ambidextrous": 3,
}

DIRECTION_NAMES = {value: key for key, value in DIRECTION_CODES.items()}
CHIRALITY_NAMES = {value: key for key, value in CHIRALITY_CODES.items()}

FIELD_ORDER = [
    "id",
    "claimant",
    "counterparty",
    "principal",
    "currency",
    "rate",
    "maturity",
    "collateral",
    "jurisdiction",
    "risk",
    "settlement_path",
    "receipt",
]

PROTO_SCHEMA = """syntax = "proto3";

package research_stack.finance;

message FinancialClaimPacket {
  string id = 1;
  string claimant = 2;
  string counterparty = 3;
  string principal = 4;
  string currency = 5;
  string rate = 6;
  string maturity = 7;
  string collateral = 8;
  string jurisdiction = 9;
  string risk = 10;
  string settlement_path = 11;
  string receipt = 12;
}
"""

NANOPB_OPTIONS = """research_stack.finance.FinancialClaimPacket.id max_size:64
research_stack.finance.FinancialClaimPacket.claimant max_size:128
research_stack.finance.FinancialClaimPacket.counterparty max_size:128
research_stack.finance.FinancialClaimPacket.principal max_size:32
research_stack.finance.FinancialClaimPacket.currency max_size:16
research_stack.finance.FinancialClaimPacket.rate max_size:32
research_stack.finance.FinancialClaimPacket.maturity max_size:32
research_stack.finance.FinancialClaimPacket.collateral max_size:160
research_stack.finance.FinancialClaimPacket.jurisdiction max_size:32
research_stack.finance.FinancialClaimPacket.risk max_size:32
research_stack.finance.FinancialClaimPacket.settlement_path max_size:32
research_stack.finance.FinancialClaimPacket.receipt max_size:160
"""

FLATBUFFERS_SCHEMA = """namespace ResearchStack.Finance;

table FinancialClaimPacket {
  id:string;
  claimant:string;
  counterparty:string;
  principal:string;
  currency:string;
  rate:string;
  maturity:string;
  collateral:string;
  jurisdiction:string;
  risk:string;
  settlement_path:string;
  receipt:string;
}

root_type FinancialClaimPacket;
"""

FIELD_SYMBOLS = {
    "id": ("FIN.FIELD.ID", "I", "#text([id])"),
    "claimant": ("FIN.FIELD.CLAIMANT", "C", "#text([claimant])"),
    "counterparty": ("FIN.FIELD.COUNTERPARTY", "P", "#text([counterparty])"),
    "principal": ("FIN.FIELD.PRINCIPAL", "$", "#text([principal])"),
    "currency": ("FIN.FIELD.CURRENCY", "U", "#text([currency/unit])"),
    "rate": ("FIN.FIELD.RATE", "r", "#text([rate])"),
    "maturity": ("FIN.FIELD.MATURITY", "T", "#text([maturity])"),
    "collateral": ("FIN.FIELD.COLLATERAL", "K", "#text([collateral])"),
    "jurisdiction": ("FIN.FIELD.JURISDICTION", "J", "#text([jurisdiction])"),
    "risk": ("FIN.FIELD.RISK", "R", "#text([risk])"),
    "settlement_path": ("FIN.FIELD.SETTLEMENT", "S", "#text([settlement])"),
    "receipt": ("FIN.FIELD.RECEIPT", "H", "#text([receipt/hash])"),
}

ENUM_SYMBOLS = {
    ("currency", "USD"): ("FIN.ENUM.CURRENCY.USD", "USD", "#text([USD])"),
    ("currency", "EUR"): ("FIN.ENUM.CURRENCY.EUR", "EUR", "#text([EUR])"),
    ("currency", "USDC"): ("FIN.ENUM.CURRENCY.USDC", "USDC", "#text([USDC])"),
    ("jurisdiction", "US-IL"): ("FIN.ENUM.JURISDICTION.US_IL", "IL", "#text([US-IL])"),
    ("jurisdiction", "US-DE"): ("FIN.ENUM.JURISDICTION.US_DE", "DE", "#text([US-DE])"),
    ("settlement_path", "wire"): ("FIN.ENUM.SETTLEMENT.WIRE", "WIRE", "#text([wire])"),
    ("settlement_path", "ach"): ("FIN.ENUM.SETTLEMENT.ACH", "ACH", "#text([ACH])"),
    ("settlement_path", "onchain"): ("FIN.ENUM.SETTLEMENT.ONCHAIN", "CHAIN", "#text([onchain])"),
    ("risk", "low"): ("FIN.ENUM.RISK.LOW", "LOW", "#text([low risk])"),
    ("risk", "medium"): ("FIN.ENUM.RISK.MEDIUM", "MED", "#text([medium risk])"),
    ("risk", "high"): ("FIN.ENUM.RISK.HIGH", "HIGH", "#text([high risk])"),
}

DEFAULT_SAMPLES = [
    {
        "id": "claim-0001",
        "claimant": "atelier-node",
        "counterparty": "counterparty-a",
        "principal": "12500.00",
        "currency": "USD",
        "rate": "0.0425",
        "maturity": "2026-12-31",
        "collateral": "invoice-pool-alpha",
        "jurisdiction": "US-IL",
        "risk": "medium",
        "settlement_path": "ach",
        "receipt": "ene:finance:claim-0001",
    },
    {
        "id": "claim-0002",
        "claimant": "research-stack",
        "counterparty": "lab-vendor",
        "principal": "2500.00",
        "currency": "USDC",
        "rate": "0.0000",
        "maturity": "2026-06-15",
        "collateral": "none",
        "jurisdiction": "US-DE",
        "risk": "low",
        "settlement_path": "onchain",
        "receipt": "ene:finance:claim-0002",
    },
    {
        "id": "claim-0003",
        "claimant": "municipal-surface",
        "counterparty": "service-provider",
        "principal": "88000.00",
        "currency": "USD",
        "rate": "0.0650",
        "maturity": "2028-05-07",
        "collateral": "tax-receivable-stream",
        "jurisdiction": "US-IL",
        "risk": "high",
        "settlement_path": "wire",
        "receipt": "ene:finance:claim-0003",
    },
    {
        "id": "claim-0004",
        "claimant": "field-lab",
        "counterparty": "instrument-lessor",
        "principal": "14250.75",
        "currency": "EUR",
        "rate": "0.0310",
        "maturity": "2027-01-20",
        "collateral": "spectrometer-lease-escrow",
        "jurisdiction": "US-DE",
        "risk": "medium",
        "settlement_path": "wire",
        "receipt": "ene:finance:claim-0004",
    },
    {
        "id": "claim-0005",
        "claimant": "openclaw-bus",
        "counterparty": "compute-provider",
        "principal": "640.00",
        "currency": "USDC",
        "rate": "0.0000",
        "maturity": "2026-05-31",
        "collateral": "prepaid-gpu-credit",
        "jurisdiction": "US-DE",
        "risk": "low",
        "settlement_path": "onchain",
        "receipt": "ene:finance:claim-0005",
    },
    {
        "id": "claim-0006",
        "claimant": "netcup-baseline",
        "counterparty": "remote-host",
        "principal": "18.95",
        "currency": "EUR",
        "rate": "0.0000",
        "maturity": "2026-06-07",
        "collateral": "controlled-remote-receipt",
        "jurisdiction": "US-IL",
        "risk": "low",
        "settlement_path": "ach",
        "receipt": "ene:finance:claim-0006",
    },
    {
        "id": "claim-0007",
        "claimant": "quandela-probe",
        "counterparty": "noisy-recovery-oracle",
        "principal": "1.00",
        "currency": "USD",
        "rate": "0.0000",
        "maturity": "2026-07-01",
        "collateral": "manual-submit-hold",
        "jurisdiction": "US-DE",
        "risk": "high",
        "settlement_path": "wire",
        "receipt": "ene:finance:claim-0007",
    },
    {
        "id": "claim-0008",
        "claimant": "h200-burst",
        "counterparty": "gpu-rental-provider",
        "principal": "75.00",
        "currency": "USD",
        "rate": "0.0000",
        "maturity": "2026-08-15",
        "collateral": "short-run-optimization-receipt",
        "jurisdiction": "US-DE",
        "risk": "medium",
        "settlement_path": "wire",
        "receipt": "ene:finance:claim-0008",
    },
    {
        "id": "claim-0009",
        "claimant": "committee-book",
        "counterparty": "review-surface",
        "principal": "0.00",
        "currency": "USD",
        "rate": "0.0000",
        "maturity": "2026-09-01",
        "collateral": "explanation-artifact",
        "jurisdiction": "US-IL",
        "risk": "low",
        "settlement_path": "ach",
        "receipt": "ene:finance:claim-0009",
    },
    {
        "id": "claim-0010",
        "claimant": "shockwave-modeling",
        "counterparty": "future-packet-family",
        "principal": "0.00",
        "currency": "USD",
        "rate": "0.0000",
        "maturity": "2027-05-07",
        "collateral": "swf1-sws1-design-hold",
        "jurisdiction": "US-DE",
        "risk": "medium",
        "settlement_path": "wire",
        "receipt": "ene:finance:claim-0010",
    },
    {
        "id": "claim-0011",
        "claimant": "sidecar-stress",
        "counterparty": "literal-heavy-counterparty",
        "principal": "999999.99",
        "currency": "USD",
        "rate": "0.1250",
        "maturity": "2031-12-31",
        "collateral": "long-literal-collateral-with-multiple-routing-hints",
        "jurisdiction": "US-IL",
        "risk": "high",
        "settlement_path": "onchain",
        "receipt": "ene:finance:claim-0011-sidecar-stress",
    },
    {
        "id": "claim-0012",
        "claimant": "unknown-enum-drill",
        "counterparty": "fallback-check",
        "principal": "321.09",
        "currency": "GBP",
        "rate": "0.0550",
        "maturity": "2026-10-10",
        "collateral": "typed-sidecar-required",
        "jurisdiction": "GB-LND",
        "risk": "medium",
        "settlement_path": "sepa",
        "receipt": "ene:finance:claim-0012",
    },
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def crc32_bytes(data: bytes) -> int:
    return binascii.crc32(data) & 0xFFFFFFFF


def canonical_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {field: packet[field] for field in FIELD_ORDER}


def canonical_bytes(packet: dict[str, Any]) -> bytes:
    return json.dumps(canonical_packet(packet), ensure_ascii=False, sort_keys=False, separators=(",", ":")).encode("utf-8")


def pack_orientation(direction: str = "ltr", chirality: str = "none", phase_bucket: int = 0) -> int:
    """Pack render/navigation orientation into one byte."""
    if direction not in DIRECTION_CODES:
        raise ValueError(f"unknown direction {direction}")
    if chirality not in CHIRALITY_CODES:
        raise ValueError(f"unknown chirality {chirality}")
    if not 0 <= phase_bucket <= 15:
        raise ValueError(f"phase bucket out of range: {phase_bucket}")
    return (phase_bucket << 4) | (CHIRALITY_CODES[chirality] << 2) | DIRECTION_CODES[direction]


def unpack_orientation(code: int) -> dict[str, Any]:
    if not 0 <= int(code) <= 255:
        raise ValueError(f"orientation code out of range: {code}")
    direction = int(code) & 0b00000011
    chirality = (int(code) >> 2) & 0b00000011
    phase_bucket = (int(code) >> 4) & 0b00001111
    return {
        "direction": DIRECTION_NAMES[direction],
        "chirality": CHIRALITY_NAMES[chirality],
        "phase_bucket": phase_bucket,
        "phase_degrees": phase_bucket * 22.5,
    }


def orientation_hint(symbol_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    field = entry.get("field")
    value = entry.get("canonical_payload")
    if entry["kind"] == "field":
        phase_bucket = FIELD_ORDER.index(value) % 16 if value in FIELD_ORDER else 0
        return {"direction": "ltr", "chirality": "none", "phase_bucket": phase_bucket}
    if field == "risk":
        risk_orientation = {
            "low": ("ltr", "left", 1),
            "medium": ("bidi", "ambidextrous", 2),
            "high": ("rtl", "right", 3),
        }
        direction, chirality, phase_bucket = risk_orientation.get(value, ("auto", "none", 0))
        return {"direction": direction, "chirality": chirality, "phase_bucket": phase_bucket}
    if field == "settlement_path":
        settlement_phase = {"ach": 4, "wire": 5, "onchain": 6}
        return {"direction": "ltr", "chirality": "none", "phase_bucket": settlement_phase.get(value, 0)}
    if field == "currency":
        currency_phase = {"USD": 7, "EUR": 8, "USDC": 9}
        return {"direction": "ltr", "chirality": "none", "phase_bucket": currency_phase.get(value, 0)}
    if field == "jurisdiction":
        return {"direction": "ltr", "chirality": "none", "phase_bucket": 10}
    return {"direction": "ltr", "chirality": "none", "phase_bucket": 0}


def build_symbol_lut() -> dict[str, Any]:
    entries = {}
    for field, (symbol_id, glyph, _) in FIELD_SYMBOLS.items():
        entries[symbol_id] = {
            "symbol_id": symbol_id,
            "kind": "field",
            "semantic_key": f"financial_claim_packet.{field}",
            "canonical_payload": field,
            "glyph": glyph,
            "inverse": field,
            "version": "0.2.0",
        }
    for (field, value), (symbol_id, glyph, _) in ENUM_SYMBOLS.items():
        entries[symbol_id] = {
            "symbol_id": symbol_id,
            "kind": "enum_value",
            "semantic_key": f"financial_claim_packet.{field}.{value}",
            "canonical_payload": value,
            "field": field,
            "glyph": glyph,
            "inverse": value,
            "version": "0.2.0",
        }
    return {"schema": "finance_claim_symbol_lut_v1", "version": "0.2.0", "inverse_required": True, "entries": entries}


def build_typesetting_lut(symbol_lut: dict[str, Any]) -> dict[str, Any]:
    render_sources = {sid: render for _, (sid, _, render) in FIELD_SYMBOLS.items()}
    render_sources.update({sid: render for _, (sid, _, render) in ENUM_SYMBOLS.items()})
    entries = {}
    for symbol_id, entry in symbol_lut["entries"].items():
        orientation = orientation_hint(symbol_id, entry)
        orientation_code = pack_orientation(**orientation)
        entries[symbol_id] = {
            "symbol_id": symbol_id,
            "glyph": entry["glyph"],
            "typst_render": render_sources.get(symbol_id, f"#text([{entry['glyph']}])"),
            "orientation_code": orientation_code,
            "orientation_hex": f"{orientation_code:02x}",
            "orientation": unpack_orientation(orientation_code),
            "tone": "witness" if entry["kind"] == "field" else "neutral",
            "rounding_rule": None,
            "residual_sidecar": None,
            "version": entry["version"],
            "source_hash": sha256_bytes(json.dumps(entry, sort_keys=True).encode("utf-8")),
        }
    return {"schema": "finance_claim_typesetting_lut_v1", "version": "0.2.0", "entries": entries}


def orientation_codec_receipt() -> dict[str, Any]:
    return {
        "schema": "orientation_codec_v1",
        "packed_bytes_per_symbol": 1,
        "bits_0_1": {"name": "direction", "codes": DIRECTION_CODES},
        "bits_2_3": {"name": "chirality", "codes": CHIRALITY_CODES},
        "bits_4_7": {"name": "phase_bucket", "buckets": 16, "degrees_per_bucket": 22.5},
        "claim_boundary": "orientation_code is a render/navigation LUT hint; exact continuous 360-degree values require sidecar promotion",
    }


def orientation_metrics(type_lut: dict[str, Any]) -> dict[str, Any]:
    entries = type_lut["entries"]
    verbose = [
        {
            "symbol_id": symbol_id,
            "direction": entry["orientation"]["direction"],
            "chirality": entry["orientation"]["chirality"],
            "phase_bucket": entry["orientation"]["phase_bucket"],
            "phase_degrees": entry["orientation"]["phase_degrees"],
        }
        for symbol_id, entry in sorted(entries.items())
    ]
    verbose_bytes = len(json.dumps(verbose, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    packed_bytes = len(entries)
    return {
        "symbol_entries": len(entries),
        "verbose_orientation_json_bytes": verbose_bytes,
        "packed_orientation_bytes": packed_bytes,
        "saved_bytes": verbose_bytes - packed_bytes,
        "saved_ratio": round((verbose_bytes - packed_bytes) / verbose_bytes, 6) if verbose_bytes else 0.0,
        "claim_boundary": "byte savings compare orientation metadata only, not full packet compression",
    }


def symbol_codebook(symbol_lut: dict[str, Any]) -> dict[str, int]:
    return {symbol_id: index for index, symbol_id in enumerate(sorted(symbol_lut["entries"]), start=1)}


def classify_literal(field: str, value: Any) -> int:
    if field in {"principal", "rate"}:
        return TYPE_DECIMAL_STRING
    if field == "maturity":
        return TYPE_DATE_STRING
    if field == "receipt":
        return TYPE_RECEIPT_STRING
    return TYPE_STRING


def encode_value(field: str, value: Any, sidecar: dict[int, dict[str, Any]]) -> dict[str, Any]:
    enum_key = (field, str(value))
    if enum_key in ENUM_SYMBOLS:
        return {"type": "enum_symbol", "symbol_id": ENUM_SYMBOLS[enum_key][0]}
    index = len(sidecar)
    value_json = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    sidecar[index] = {
        "index": index,
        "field": field,
        "type_code": classify_literal(field, value),
        "type": TYPE_NAMES[classify_literal(field, value)],
        "value_json": value_json,
        "sha256": sha256_bytes(value_json.encode("utf-8")),
    }
    return {"type": "literal_ref", "sidecar_index": index, "sha256": sidecar[index]["sha256"]}


def encode_packet(packet: dict[str, Any]) -> dict[str, Any]:
    sidecar: dict[int, dict[str, Any]] = {}
    fields = []
    for field in FIELD_ORDER:
        fields.append({"field_symbol_id": FIELD_SYMBOLS[field][0], "value": encode_value(field, packet[field], sidecar)})
    return {
        "compressed": {"schema": "financial_claim_packet_compressed_v1", "codec": "symbol_lut_plus_fcs1_sidecar", "fields": fields},
        "sidecar": sidecar,
    }


def json_sidecar(sidecar: dict[int, dict[str, Any]]) -> dict[str, Any]:
    return {f"sidecar.{item['field']}.{index:04d}": item for index, item in sidecar.items()}


def decode_packet(compressed: dict[str, Any], sidecar: dict[int, dict[str, Any]], symbol_lut: dict[str, Any]) -> dict[str, Any]:
    packet = {}
    entries = symbol_lut["entries"]
    for item in compressed["fields"]:
        field = entries[item["field_symbol_id"]]["inverse"]
        value_ref = item["value"]
        if value_ref["type"] == "enum_symbol":
            packet[field] = entries[value_ref["symbol_id"]]["inverse"]
        elif value_ref["type"] == "literal_ref":
            side = sidecar[int(value_ref["sidecar_index"])]
            if side["sha256"] != value_ref["sha256"]:
                raise ValueError(f"sidecar hash mismatch for index {value_ref['sidecar_index']}")
            packet[field] = json.loads(side["value_json"])
        else:
            raise ValueError(f"unknown value ref type: {value_ref['type']}")
    return canonical_packet(packet)


def encode_fcl1(compressed: dict[str, Any], codebook: dict[str, int]) -> bytes:
    out = bytearray(b"FCL1")
    out.append(FCL1_VERSION)
    fields = compressed["fields"]
    if len(fields) > 255:
        raise ValueError("too many fields for FCL1")
    out.append(len(fields))
    for item in fields:
        out.extend(codebook[item["field_symbol_id"]].to_bytes(2, "big"))
        value = item["value"]
        if value["type"] == "enum_symbol":
            out.append(VALUE_TAG_ENUM)
            out.extend(codebook[value["symbol_id"]].to_bytes(2, "big"))
        elif value["type"] == "literal_ref":
            out.append(VALUE_TAG_SIDECAR)
            out.extend(int(value["sidecar_index"]).to_bytes(2, "big"))
        else:
            raise ValueError(f"unknown value ref type: {value['type']}")
    out.extend(crc32_bytes(bytes(out)).to_bytes(4, "big"))
    return bytes(out)


def decode_fcl1(blob: bytes, sidecar: dict[int, dict[str, Any]], symbol_lut: dict[str, Any], codebook: dict[str, int]) -> dict[str, Any]:
    if len(blob) < 10 or not blob.startswith(b"FCL1"):
        raise ValueError("bad FCL1 magic")
    stored_crc = int.from_bytes(blob[-4:], "big")
    body = blob[:-4]
    if crc32_bytes(body) != stored_crc:
        raise ValueError("bad FCL1 checksum")
    if body[4] != FCL1_VERSION:
        raise ValueError(f"unsupported FCL1 version {body[4]}")
    inverse_codebook = {value: key for key, value in codebook.items()}
    count = body[5]
    offset = 6
    fields = []
    for _ in range(count):
        field_symbol_id = inverse_codebook[int.from_bytes(body[offset : offset + 2], "big")]
        offset += 2
        tag = body[offset]
        offset += 1
        value_code = int.from_bytes(body[offset : offset + 2], "big")
        offset += 2
        if tag == VALUE_TAG_ENUM:
            value = {"type": "enum_symbol", "symbol_id": inverse_codebook[value_code]}
        elif tag == VALUE_TAG_SIDECAR:
            if value_code not in sidecar:
                raise ValueError(f"missing FCS1 sidecar index {value_code}")
            value = {"type": "literal_ref", "sidecar_index": value_code, "sha256": sidecar[value_code]["sha256"]}
        else:
            raise ValueError(f"unknown FCL1 tag {tag}")
        fields.append({"field_symbol_id": field_symbol_id, "value": value})
    if offset != len(body):
        raise ValueError("trailing FCL1 bytes")
    return decode_packet({"schema": "financial_claim_packet_compressed_v1", "codec": "fcl1", "fields": fields}, sidecar, symbol_lut)


def encode_fcs1(sidecar: dict[int, dict[str, Any]]) -> bytes:
    out = bytearray(b"FCS1")
    out.append(FCS1_VERSION)
    if len(sidecar) > 255:
        raise ValueError("too many sidecar literals for FCS1")
    out.append(len(sidecar))
    for index in sorted(sidecar):
        item = sidecar[index]
        value = item["value_json"].encode("utf-8")
        if len(value) > 65535:
            raise ValueError("FCS1 literal too large")
        out.extend(index.to_bytes(2, "big"))
        out.append(int(item["type_code"]))
        out.extend(len(value).to_bytes(2, "big"))
        out.extend(value)
        out.extend(crc32_bytes(value).to_bytes(4, "big"))
    out.extend(crc32_bytes(bytes(out)).to_bytes(4, "big"))
    return bytes(out)


def decode_fcs1(blob: bytes) -> dict[int, dict[str, Any]]:
    if len(blob) < 10 or not blob.startswith(b"FCS1"):
        raise ValueError("bad FCS1 magic")
    stored_crc = int.from_bytes(blob[-4:], "big")
    body = blob[:-4]
    if crc32_bytes(body) != stored_crc:
        raise ValueError("bad FCS1 checksum")
    if body[4] != FCS1_VERSION:
        raise ValueError(f"unsupported FCS1 version {body[4]}")
    count = body[5]
    offset = 6
    sidecar: dict[int, dict[str, Any]] = {}
    for _ in range(count):
        index = int.from_bytes(body[offset : offset + 2], "big")
        offset += 2
        type_code = body[offset]
        offset += 1
        length = int.from_bytes(body[offset : offset + 2], "big")
        offset += 2
        value_bytes = body[offset : offset + length]
        offset += length
        value_crc = int.from_bytes(body[offset : offset + 4], "big")
        offset += 4
        if crc32_bytes(value_bytes) != value_crc:
            raise ValueError(f"bad FCS1 value checksum for index {index}")
        value_json = value_bytes.decode("utf-8")
        sidecar[index] = {
            "index": index,
            "field": None,
            "type_code": type_code,
            "type": TYPE_NAMES.get(type_code, "unknown"),
            "value_json": value_json,
            "sha256": sha256_bytes(value_bytes),
        }
    if offset != len(body):
        raise ValueError("trailing FCS1 bytes")
    return sidecar


def render_preview(compressed: dict[str, Any], type_lut: dict[str, Any]) -> str:
    parts = []
    for item in compressed["fields"]:
        field_glyph = type_lut["entries"][item["field_symbol_id"]]["glyph"]
        value_ref = item["value"]
        value_glyph = type_lut["entries"][value_ref["symbol_id"]]["glyph"] if value_ref["type"] == "enum_symbol" else "LIT"
        parts.append(f"{field_glyph}:{value_glyph}")
    return " ".join(parts)


def typst_render_source(samples: list[dict[str, Any]]) -> str:
    rows = []
    for sample in samples:
        rows.append(f'  [{sample["id"]}], [`{sample["render_preview"]}`], [`{sample["canonical_hash"][:12]}`],')
    return "\n".join(
        [
            '#set page(width: 8.5in, height: 11in, margin: 0.75in)',
            '#set text(size: 9pt)',
            '= Finance Claim LUT Render Preview',
            '',
            '#table(',
            '  columns: (1.1fr, 3fr, 1.2fr),',
            '  [Packet], [FCL1 Render Preview], [Hash],',
            *rows,
            ')',
            '',
        ]
    )


def compile_typst_render(samples: list[dict[str, Any]], fixture_dir: Path) -> dict[str, Any]:
    fixture_dir.mkdir(parents=True, exist_ok=True)
    source = typst_render_source(samples)
    source_path = fixture_dir / "finance_claim_lut_render.typ"
    pdf_path = fixture_dir / "finance_claim_lut_render.pdf"
    source_path.write_text(source, encoding="utf-8")
    typst = LOCAL_TYPST if LOCAL_TYPST.exists() else None
    result = {
        "typst_source": repo_path(source_path),
        "typst_source_hash": sha256_bytes(source.encode("utf-8")),
        "compiled": False,
        "pdf": repo_path(pdf_path),
        "pdf_hash": None,
        "stderr": "",
    }
    if not typst:
        result["stderr"] = "typst CLI not found"
        return result
    proc = subprocess.run([str(typst), "compile", "--root", str(REPO), repo_path(source_path), repo_path(pdf_path)], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    result["compiled"] = proc.returncode == 0
    result["stderr"] = proc.stderr[-2000:]
    if pdf_path.exists() and proc.returncode == 0:
        result["pdf_hash"] = sha256_bytes(pdf_path.read_bytes())
    return result


def optional_codec_size(module_name: str, encoder_name: str, packet: dict[str, Any]) -> dict[str, Any]:
    if importlib.util.find_spec(module_name) is None:
        return {"available": False, "status": "skipped", "bytes": None}
    module = __import__(module_name)
    try:
        if module_name == "cbor2":
            encoded = module.dumps(packet, canonical=True)
        elif module_name == "msgpack":
            encoded = module.packb(packet, use_bin_type=True)
        else:
            encoded = getattr(module, encoder_name)(packet)
        return {"available": True, "status": "ok", "bytes": len(encoded), "sha256": sha256_bytes(encoded)}
    except Exception as exc:
        return {"available": True, "status": f"error: {exc}", "bytes": None}


def protobuf_dynamic_bytes(packet: dict[str, Any]) -> dict[str, Any]:
    if importlib.util.find_spec("google.protobuf") is None:
        return {"available": False, "status": "skipped", "bytes": None}
    try:
        from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

        fd = descriptor_pb2.FileDescriptorProto()
        fd.name = "finance_claim_packet.proto"
        fd.package = "research_stack.finance"
        fd.syntax = "proto3"
        msg = fd.message_type.add()
        msg.name = "FinancialClaimPacket"
        for index, field in enumerate(FIELD_ORDER, start=1):
            f = msg.field.add()
            f.name = field
            f.number = index
            f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
            f.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
        pool = descriptor_pool.DescriptorPool()
        pool.Add(fd)
        klass = message_factory.GetMessageClass(pool.FindMessageTypeByName("research_stack.finance.FinancialClaimPacket"))
        encoded = klass(**canonical_packet(packet)).SerializeToString(deterministic=True)
        return {"available": True, "status": "ok", "bytes": len(encoded), "sha256": sha256_bytes(encoded), "encoded": encoded}
    except Exception as exc:
        return {"available": True, "status": f"error: {exc}", "bytes": None}


def write_schema_fixtures(fixture_dir: Path) -> dict[str, Any]:
    fixture_dir.mkdir(parents=True, exist_ok=True)
    schema_files = {
        "protobuf_schema": (fixture_dir / "finance_claim_packet.proto", PROTO_SCHEMA.encode("utf-8")),
        "nanopb_options": (fixture_dir / "finance_claim_packet.options", NANOPB_OPTIONS.encode("utf-8")),
        "flatbuffers_schema": (fixture_dir / "finance_claim_packet.fbs", FLATBUFFERS_SCHEMA.encode("utf-8")),
    }
    out = {}
    for key, (path, data) in schema_files.items():
        out[key] = write_fixture(path, data)
    return out


def metrics(raw: bytes, compressed: dict[str, Any], sidecar: dict[int, dict[str, Any]], fcl1: bytes, fcs1: bytes, packet: dict[str, Any]) -> dict[str, Any]:
    compressed_bytes = json.dumps(compressed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sidecar_json_bytes = json.dumps(json_sidecar(sidecar), sort_keys=True, separators=(",", ":")).encode("utf-8")
    proto = protobuf_dynamic_bytes(packet)
    proto_public = {key: value for key, value in proto.items() if key != "encoded"}
    return {
        "canonical_json_bytes": len(raw),
        "zlib_canonical_bytes": len(zlib.compress(raw, level=9)),
        "json_compressed_packet_bytes": len(compressed_bytes),
        "json_sidecar_bytes": len(sidecar_json_bytes),
        "combined_json_encoded_bytes": len(compressed_bytes) + len(sidecar_json_bytes),
        "fcl1_bytes": len(fcl1),
        "fcs1_bytes": len(fcs1),
        "combined_fcl1_fcs1_bytes": len(fcl1) + len(fcs1),
        "cbor": optional_codec_size("cbor2", "dumps", packet),
        "messagepack": optional_codec_size("msgpack", "packb", packet),
        "protobuf_dynamic": proto_public,
        "nanopb": {"available": importlib.util.find_spec("nanopb") is not None, "status": "schema_emitted_generator_pending", "bytes": proto_public.get("bytes")},
        "flatbuffers": {"available": importlib.util.find_spec("flatbuffers") is not None, "status": "schema_emitted_flatc_missing", "bytes": None},
        "claim_boundary": "codec comparison over tiny local samples only; not competitive compression evidence",
    }


def write_fixture(path: Path, data: bytes) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": repo_path(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def build_sample_receipt(sample: dict[str, Any], symbol_lut: dict[str, Any], type_lut: dict[str, Any], codebook: dict[str, int], fixture_dir: Path) -> dict[str, Any]:
    raw = canonical_bytes(sample)
    encoded = encode_packet(sample)
    fcl1 = encode_fcl1(encoded["compressed"], codebook)
    fcs1 = encode_fcs1(encoded["sidecar"])
    proto = protobuf_dynamic_bytes(canonical_packet(sample))
    decoded_json = decode_packet(encoded["compressed"], encoded["sidecar"], symbol_lut)
    decoded_binary = decode_fcl1(fcl1, decode_fcs1(fcs1), symbol_lut, codebook)
    decoded_json_raw = canonical_bytes(decoded_json)
    decoded_binary_raw = canonical_bytes(decoded_binary)
    sample_dir = fixture_dir / sample["id"]
    render = render_preview(encoded["compressed"], type_lut)
    return {
        "id": sample["id"],
        "canonical_hash": sha256_bytes(raw),
        "decoded_hash": sha256_bytes(decoded_json_raw),
        "fcl1_decoded_hash": sha256_bytes(decoded_binary_raw),
        "rehydrated_ok": decoded_json_raw == raw and decoded_binary_raw == raw,
        "fcl1_decode_ok": decoded_binary_raw == raw,
        "fcs1_decode_ok": decode_fcs1(fcs1) != {},
        "fcl1_binary_hex": fcl1.hex(),
        "fcl1_binary_hash": sha256_bytes(fcl1),
        "fcs1_binary_hex": fcs1.hex(),
        "fcs1_binary_hash": sha256_bytes(fcs1),
        "compressed_hash": sha256_bytes(json.dumps(encoded["compressed"], sort_keys=True).encode("utf-8")),
        "sidecar_hash": sha256_bytes(json.dumps(json_sidecar(encoded["sidecar"]), sort_keys=True).encode("utf-8")),
        "render_preview": render,
        "render_preview_hash": sha256_bytes(render.encode("utf-8")),
        "fixtures": {
            "canonical": write_fixture(sample_dir / "canonical.json", raw),
            "fcl1": write_fixture(sample_dir / "packet.fcl1", fcl1),
            "fcs1": write_fixture(sample_dir / "sidecar.fcs1", fcs1),
            "protobuf": write_fixture(sample_dir / "packet.pb", proto["encoded"]) if proto.get("status") == "ok" else None,
        },
        "compressed": encoded["compressed"],
        "sidecar": json_sidecar(encoded["sidecar"]),
        "metrics": metrics(raw, encoded["compressed"], encoded["sidecar"], fcl1, fcs1, canonical_packet(sample)),
    }


def corruption_tests(samples: list[dict[str, Any]], symbol_lut: dict[str, Any], codebook: dict[str, int]) -> dict[str, Any]:
    sample = samples[0]
    encoded = encode_packet(sample)
    fcl1 = bytearray(encode_fcl1(encoded["compressed"], codebook))
    fcs1 = bytearray(encode_fcs1(encoded["sidecar"]))
    unknown = dict(sample)
    unknown["currency"] = "ZZZ"
    unknown_encoded = encode_packet(unknown)
    tests = {}
    fcs1[-5] ^= 0x01
    try:
        decode_fcl1(bytes(encode_fcl1(encoded["compressed"], codebook)), decode_fcs1(bytes(fcs1)), symbol_lut, codebook)
        tests["corrupt_fcs1_rejected"] = False
    except Exception:
        tests["corrupt_fcs1_rejected"] = True
    fcl1[6] ^= 0x01
    try:
        decode_fcl1(bytes(fcl1), decode_fcs1(encode_fcs1(encoded["sidecar"])), symbol_lut, codebook)
        tests["corrupt_fcl1_rejected"] = False
    except Exception:
        tests["corrupt_fcl1_rejected"] = True
    tests["unknown_enum_falls_back_to_sidecar"] = any(
        item["field_symbol_id"] == FIELD_SYMBOLS["currency"][0] and item["value"]["type"] == "literal_ref"
        for item in unknown_encoded["compressed"]["fields"]
    )
    tests["field_order_canonical"] = list(canonical_packet(sample)) == FIELD_ORDER
    tests["lawful"] = all(tests.values())
    return tests


def build_receipt(samples: list[dict[str, Any]], fixture_dir: Path) -> dict[str, Any]:
    symbol_lut = build_symbol_lut()
    type_lut = build_typesetting_lut(symbol_lut)
    codebook = symbol_codebook(symbol_lut)
    sample_receipts = [build_sample_receipt(sample, symbol_lut, type_lut, codebook, fixture_dir) for sample in samples]
    schema_receipts = write_schema_fixtures(fixture_dir)
    render_receipt = compile_typst_render(sample_receipts, fixture_dir)
    symbol_lut_bytes = json.dumps(symbol_lut, sort_keys=True, ensure_ascii=False).encode("utf-8")
    type_lut_bytes = json.dumps(type_lut, sort_keys=True, ensure_ascii=False).encode("utf-8")
    tests = corruption_tests(samples, symbol_lut, codebook)
    return {
        "schema": "finance_claim_lut_harness_receipt_v2",
        "surface_id": "finance_claim_lut_harness",
        "claim_boundary": (
            "Harness demonstrates byte-for-byte FinancialClaimPacket rehydration through symbol/typesetting LUTs, "
            "FCL1 packets, and FCS1 sidecars. It is not financial advice, audit certification, settlement, or "
            "competitive compression evidence."
        ),
        "wire_formats": {
            "fcl1": "magic FCL1, version byte, field count, repeated u16/u8/u16 records, crc32 trailer",
            "fcs1": "magic FCS1, version byte, literal count, repeated typed literal records, crc32 trailer",
            "orientation_code": "one LUT byte: bits 0-1 direction, bits 2-3 chirality, bits 4-7 phase bucket",
            "json": "audit envelope only",
        },
        "orientation_codec": orientation_codec_receipt(),
        "orientation_metrics": orientation_metrics(type_lut),
        "canonical_field_order": FIELD_ORDER,
        "symbol_lut": symbol_lut,
        "symbol_lut_hash": sha256_bytes(symbol_lut_bytes),
        "symbol_codebook": codebook,
        "typesetting_lut": type_lut,
        "typesetting_lut_hash": sha256_bytes(type_lut_bytes),
        "fixture_dir": repo_path(fixture_dir),
        "schema_receipts": schema_receipts,
        "render_receipt": render_receipt,
        "test_receipts": tests,
        "sample_count": len(sample_receipts),
        "samples": sample_receipts,
        "lawful": all(item["rehydrated_ok"] and item["fcl1_decode_ok"] and item["fcs1_decode_ok"] for item in sample_receipts)
        and tests["lawful"]
        and bool(render_receipt.get("typst_source_hash")),
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a reversible finance-claim compression router. Return compact JSON and preserve claim boundaries."
    records = []
    for sample in receipt["samples"]:
        prompt = {
            "task": "verify_financial_claim_packet_lut_roundtrip",
            "id": sample["id"],
            "canonical_hash": sample["canonical_hash"],
            "fcl1_decoded_hash": sample["fcl1_decoded_hash"],
            "fcl1_bytes": sample["metrics"]["fcl1_bytes"],
            "fcs1_bytes": sample["metrics"]["fcs1_bytes"],
            "instruction": "Decide whether this binary LUT compression packet may promote to a reversible surface receipt.",
        }
        answer = {
            "selected": bool(sample["rehydrated_ok"]),
            "use_as": "reversible_binary_lut_surface_receipt",
            "claim_boundary": "json-audit-binary-wire-byte-roundtrip-only-not-financial-advice",
            "canonical_hash": sample["canonical_hash"],
            "fcl1_decoded_hash": sample["fcl1_decoded_hash"],
            "symbol_lut_hash": receipt["symbol_lut_hash"],
            "typesetting_lut_hash": receipt["typesetting_lut_hash"],
            "orientation_codec": receipt["orientation_codec"]["schema"],
            "orientation_metrics": receipt["orientation_metrics"],
            "fcl1_binary_hash": sample["fcl1_binary_hash"],
            "fcs1_binary_hash": sample["fcs1_binary_hash"],
            "rehydrated_ok": sample["rehydrated_ok"],
            "baseline_comparison": sample["metrics"],
        }
        records.append({"messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}, {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)}]})
    records.append(
        {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps({"task": "choose_embedded_codec", "available": ["FCL1/FCS1", "CBOR", "MessagePack", "Nanopb", "FlatBuffers"], "instruction": "Choose the current finance-claim wire path."}, ensure_ascii=False)},
                {"role": "assistant", "content": json.dumps({"selected": "FCL1/FCS1", "claim_boundary": "JSON remains audit envelope; binary wire remains local harness only.", "reason": "Both endpoints are controlled and exact byte rehydration is already receipt-backed.", "defer": ["Nanopb schema", "FlatBuffers schema"]}, ensure_ascii=False)},
            ]
        }
    )
    records.append(
        {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps({"task": "plan_rehydration_preload_buffer", "instruction": "Describe whether a multi-serial/parallel preload buffer helps FCL1/FCS1 rehydration."}, ensure_ascii=False)},
                {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "selected": True,
                            "use_as": "future_decoder_pipeline_hint",
                            "claim_boundary": "preload buffer is a local rehydration scheduling optimization, not a compression-ratio claim",
                            "borrows_from": ["delay_line_buffer_ram", "isa_hot_path", "isa_cold_path", "high_baud_stream_modem"],
                            "lanes": ["fcl1_token_tape", "fcs1_literal_stream", "crc_hash_witness", "orientation_lut"],
                            "hot_path": ["field_symbol_decode", "enum_symbol_decode", "orientation_byte_decode", "canonical_field_order_commit"],
                            "cold_path": ["typed_sidecar_literal_fetch", "unknown_enum_sidecar_fallback", "continuous_orientation_sidecar", "field_equation_static_target_rehydrator", "crc_hash_failure_route"],
                            "virtual_modem_decompressor": {
                                "selected": True,
                                "carrier_stream": "FCL1 token tape plus orientation bytes",
                                "sideband_stream": "FCS1 typed literal lane",
                                "control_bit_flow": {
                                    "carrier_lock": "symbol tape synchronized",
                                    "frame_sync": "FCL1 magic/version/count accepted",
                                    "lane_select": "enum hot path or sidecar cold path",
                                    "phase_lock": "orientation phase bucket decoded",
                                    "sidecar_request": "literal index queued for FCS1 fetch",
                                    "replay": "crc/hash failure routes to cold-path replay",
                                    "commit": "canonical hash gate passed",
                                },
                                "demodulator": ["symbol_lock", "phase_bucket_lock", "hot_path_commit", "cold_path_replay", "canonical_hash_check"],
                                "claim_boundary": "virtual modem framing is a decoder architecture metaphor backed by local byte receipts, not a measured baud-rate benchmark",
                            },
                            "static_target_mode": {
                                "selected": True,
                                "use_as": "field_equation_rehydration_candidate",
                                "basis": ["finance_math_stack", "symbol_lut", "typesetting_lut", "logogram_orientation", "canonical_hash_gate"],
                                "claim_boundary": "field-equation rehydration is permitted only when the final target object is static and byte-roundtrip receipts remain authoritative",
                            },
                            "reason": "Serial inputs remain canonical while parallel preload slots hide sidecar lookup, checksum, render-orientation, and static-target field-equation setup before final JSON commit.",
                        },
                        ensure_ascii=False,
                    ),
                },
            ]
        }
    )
    return records


def load_samples(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return DEFAULT_SAMPLES
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("samples", DEFAULT_SAMPLES)


def write_standard_artifacts(receipt: dict[str, Any], args: argparse.Namespace) -> None:
    for path in (args.receipt, args.symbol_lut, args.typesetting_lut, args.curriculum):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.symbol_lut.write_text(json.dumps(receipt["symbol_lut"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.typesetting_lut.write_text(json.dumps(receipt["typesetting_lut"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def manifest_for_dir(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name in {"bundle_manifest.json", "bundle_receipt.json"}:
            continue
        data = path.read_bytes()
        files.append({"path": str(path.relative_to(root)), "bytes": len(data), "sha256": sha256_bytes(data)})
    manifest_bytes = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema": "finance_claim_bundle_manifest_v1", "root": repo_path(root), "file_count": len(files), "manifest_hash": sha256_bytes(manifest_bytes), "files": files}


def write_corpus_bundle(samples: list[dict[str, Any]], bundle_dir: Path) -> dict[str, Any]:
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    samples_path = bundle_dir / "canonical_samples.json"
    samples_path.write_text(json.dumps([canonical_packet(sample) for sample in samples], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = build_receipt(samples, bundle_dir / "fixtures")
    (bundle_dir / "finance_claim_lut_harness_receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (bundle_dir / "finance_claim_symbol_lut.json").write_text(json.dumps(receipt["symbol_lut"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (bundle_dir / "finance_claim_typesetting_lut.json").write_text(json.dumps(receipt["typesetting_lut"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (bundle_dir / "finance_claim_lut_harness_curriculum.jsonl").open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    manifest = manifest_for_dir(bundle_dir)
    (bundle_dir / "bundle_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bundle_receipt = {
        "schema": "finance_claim_corpus_bundle_receipt_v1",
        "bundle_dir": repo_path(bundle_dir),
        "sample_count": len(samples),
        "samples_hash": sha256_bytes(samples_path.read_bytes()),
        "harness_receipt_hash": sha256_bytes((bundle_dir / "finance_claim_lut_harness_receipt.json").read_bytes()),
        "manifest_hash": manifest["manifest_hash"],
        "manifest_file_count": manifest["file_count"],
        "wire_boundary": "JSON files are audit fixtures; packet.fcl1 and sidecar.fcs1 are binary wire fixtures",
        "lawful": bool(receipt.get("lawful")) and all(item.get("rehydrated_ok") for item in receipt.get("samples", [])),
        "claim_boundary": "portable corpus bundle only; not provider execution, settlement, or competitive compression evidence",
    }
    (bundle_dir / "bundle_receipt.json").write_text(json.dumps(bundle_receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return bundle_receipt


def verify_receipt(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    ok = all(
        item.get("rehydrated_ok")
        and item.get("canonical_hash") == item.get("decoded_hash")
        and item.get("canonical_hash") == item.get("fcl1_decoded_hash")
        and item.get("fcl1_binary_hash")
        and item.get("fcs1_binary_hash")
        for item in samples
    )
    return {
        "schema": "finance_claim_lut_verify_v1",
        "receipt": str(path),
        "samples": len(samples),
        "verified": ok and bool(data.get("lawful")),
        "claim_boundary": "receipt verification only; not financial advice or compression certification",
    }


def decode_cli(fcl1_hex: str, sidecar_path: Path, out: Path | None) -> dict[str, Any]:
    symbol_lut = build_symbol_lut()
    codebook = symbol_codebook(symbol_lut)
    sidecar = decode_fcs1(sidecar_path.read_bytes())
    packet = decode_fcl1(bytes.fromhex(fcl1_hex), sidecar, symbol_lut, codebook)
    result = {
        "schema": "finance_claim_lut_decode_v1",
        "canonical": packet,
        "canonical_hash": sha256_bytes(canonical_bytes(packet)),
        "claim_boundary": "decode output only; not settlement or financial advice",
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--samples", type=Path)
    parser.add_argument("--receipt", "--out", dest="receipt", type=Path, default=SHIM / "finance_claim_lut_harness_receipt.json")
    parser.add_argument("--symbol-lut", type=Path, default=SHIM / "finance_claim_symbol_lut.json")
    parser.add_argument("--typesetting-lut", type=Path, default=SHIM / "finance_claim_typesetting_lut.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "finance_claim_lut_harness_curriculum.jsonl")
    parser.add_argument("--fixture-dir", type=Path, default=FIXTURE_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    encode_parser = subparsers.add_parser("encode")
    add_common_args(encode_parser)
    bench_parser = subparsers.add_parser("bench")
    add_common_args(bench_parser)
    bundle_parser = subparsers.add_parser("bundle")
    add_common_args(bundle_parser)
    bundle_parser.add_argument("--bundle-dir", type=Path, default=BUNDLE_DIR)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--receipt", type=Path, default=SHIM / "finance_claim_lut_harness_receipt.json")
    decode_parser = subparsers.add_parser("decode")
    decode_parser.add_argument("--fcl1", required=True)
    decode_parser.add_argument("--sidecar", type=Path, required=True)
    decode_parser.add_argument("--out", type=Path)
    add_common_args(parser)
    args = parser.parse_args()

    if args.command == "verify":
        print(json.dumps(verify_receipt(args.receipt), indent=2, ensure_ascii=False))
        return 0
    if args.command == "decode":
        print(json.dumps(decode_cli(args.fcl1, args.sidecar, args.out), indent=2, ensure_ascii=False))
        return 0

    samples = load_samples(args.samples)
    if args.command == "bundle":
        print(json.dumps(write_corpus_bundle(samples, args.bundle_dir), indent=2, ensure_ascii=False))
        return 0
    receipt = build_receipt(samples, args.fixture_dir)
    if args.command in {None, "encode"}:
        write_standard_artifacts(receipt, args)
    print(json.dumps(receipt if args.command != "bench" else {"schema": "finance_claim_lut_bench_v1", "samples": [{"id": s["id"], "metrics": s["metrics"]} for s in receipt["samples"]], "claim_boundary": receipt["claim_boundary"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
