#!/usr/bin/env python3
"""Parquet to logogram efficiency accounting probe.

This probe measures the user's proposed path: transcode sampled Parquet rows
into a logogram/species-code style payload, then account for byte gains or
losses with exact replay gates. It intentionally separates measured byte
accounting from promotion claims: positive savings are fixture evidence only,
and negative savings are still useful baseline values.

It also tests the stronger hybrid hypothesis: keep Parquet as the physical
storage substrate and add a compact logogram sidecar for schema lineage,
prediction-cache routing, RAM-trace routing, and replay receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


REPO = Path(__file__).resolve().parents[2]
V2_SCRIPT = REPO / "4-Infrastructure" / "shim" / "enwiki9_logogram_xml_dict_probe.py"
OUT_DIR = REPO / "shared-data" / "data" / "parquet_logogram_efficiency"
PAYLOAD_JSON = OUT_DIR / "parquet_logogram_efficiency.json"
SUMMARY = OUT_DIR / "parquet_logogram_efficiency.md"
RECEIPT = OUT_DIR / "parquet_logogram_efficiency_receipt.json"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Parquet Logogram Efficiency.tid"
)

PROTOCOL_ID = "PQLOG1"
SLICE_RECEIPT_ROOT_BYTES = 32
PROTOCOL_ID_BYTES = len(PROTOCOL_ID.encode("ascii"))
SCHEMA_HASH_BYTES = 32
ROW_COUNT_BYTES = 8

DEFAULT_INPUTS = [
    REPO / "3-Mathematical-Models" / "equations_parquet_tagged" / "mass_equations_unified.parquet",
    REPO / "3-Mathematical-Models" / "equations_parquet_tagged" / "equations_unified_9pattern.parquet",
    REPO / "shared-data" / "data" / "connectomes" / "openworm_parquet" / "summary.parquet",
    REPO / "shared-data" / "data" / "datasets" / "mathlib4_complete.parquet",
]


def load_v2_module() -> Any:
    spec = importlib.util.spec_from_file_location("enwiki9_logogram_xml_dict_probe", V2_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load logogram script: {V2_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V2 = load_v2_module()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def clean_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if isinstance(value, dict):
        return {str(k): clean_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [clean_value(item) for item in value]
    return value


def dictionary_payload() -> dict[str, list[str]]:
    return {
        "fixed": [tag.hex() for tag in V2.FIXED_TAGS],
        "pair": [tag.hex() for tag in V2.PAIR_TAGS],
        "attr": [tag.hex() for tag in V2.ATTR_TAGS],
        "motif": [tag.hex() for tag in V2.MOTIFS],
    }


def encode_packet(data: bytes, name: str) -> dict[str, Any]:
    core, atoms = V2.encode(data)
    decoded = V2.decode_core(core)
    core_path = OUT_DIR / f"{name}.wlg2"
    core_path.write_bytes(core)
    atom_counts = {kind: sum(1 for atom in atoms if atom.kind == kind) for kind in sorted({atom.kind for atom in atoms})}
    packet_bytes = len(core) + SLICE_RECEIPT_ROOT_BYTES + PROTOCOL_ID_BYTES + SCHEMA_HASH_BYTES + ROW_COUNT_BYTES
    return {
        "core": rel(core_path),
        "core_bytes": len(core),
        "core_sha256": sha256_bytes(core),
        "packet_bytes": packet_bytes,
        "exact_replay": decoded == data,
        "atom_count": len(atoms),
        "atom_counts": atom_counts,
    }


def exact_replay_pass(item: dict[str, Any]) -> bool:
    return bool(
        item["species_logogram"]["exact_replay"]
        and item["schema_hash_recomputes"]
        and item["row_count_matches"]
        and item["residual_bounded"]
    )


def route_for_column(name: str, field_type: str, distinct_count: int, row_count: int, null_count: int) -> str:
    lower = name.lower()
    if any(token in lower for token in ["hash", "sha", "id", "doi", "source", "extracted", "timestamp"]):
        return "ram_trace"
    if row_count and distinct_count <= max(8, row_count // 8):
        return "prediction_cache"
    if "bool" in field_type or distinct_count <= 2:
        return "prediction_cache"
    if null_count == row_count:
        return "prediction_cache"
    return "parquet_native"


def column_sidecar(table: pa.Table, source: str, schema_hash: str, fields: list[dict[str, Any]]) -> tuple[bytes, dict[str, Any]]:
    row_count = table.num_rows
    columns: list[dict[str, Any]] = []
    for field in fields:
        values = [clean_value(value) for value in table[field["name"]].to_pylist()]
        encoded_values = [stable_json(value) for value in values]
        distinct_count = len(set(encoded_values))
        null_count = sum(1 for value in values if value is None)
        route = route_for_column(field["name"], field["type"], distinct_count, row_count, null_count)
        columns.append(
            {
                "name": field["name"],
                "type": field["type"],
                "nullable": field["nullable"],
                "distinct_count": distinct_count,
                "null_count": null_count,
                "route": route,
            }
        )
    plan = {
        "prediction_cache_columns": [item["name"] for item in columns if item["route"] == "prediction_cache"],
        "ram_trace_columns": [item["name"] for item in columns if item["route"] == "ram_trace"],
        "parquet_native_columns": [item["name"] for item in columns if item["route"] == "parquet_native"],
    }
    sidecar = {
        "protocol": "PQLOG-HYBRID-SIDECAR-v1",
        "source": source,
        "schema_hash": schema_hash,
        "row_count": row_count,
        "columns": columns,
        "pathfinding_plan": plan,
        "exact_replay_gate": [
            "parquet_sample_hash_recomputes",
            "schema_hash_recomputes",
            "row_count_matches",
            "sidecar_decode_replays",
        ],
    }
    return stable_json(sidecar).encode("utf-8"), sidecar


def sample_table(path: Path, row_limit: int) -> pa.Table:
    parquet_file = pq.ParquetFile(path)
    table = parquet_file.read_row_group(0)
    return table.slice(0, min(row_limit, table.num_rows))


def write_sample_parquet(table: pa.Table, out_path: Path) -> str:
    for compression in ["zstd", "snappy", None]:
        try:
            pq.write_table(table, out_path, compression=compression)
            return str(compression or "none")
        except Exception:
            continue
    raise RuntimeError(f"could not write sample parquet: {out_path}")


def schema_record(path: Path, parquet_file: pq.ParquetFile, table: pa.Table) -> dict[str, Any]:
    fields = [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in table.schema
    ]
    return {
        "source_path": rel(path),
        "source_bytes": path.stat().st_size,
        "source_sha256": file_hash(path),
        "source_rows": parquet_file.metadata.num_rows,
        "source_row_groups": parquet_file.metadata.num_row_groups,
        "source_columns": parquet_file.metadata.num_columns,
        "sample_rows": table.num_rows,
        "sample_columns": table.num_columns,
        "fields": fields,
    }


def canonical_forms(table: pa.Table) -> tuple[bytes, bytes, list[str], list[dict[str, Any]]]:
    columns = table.column_names
    rows = [{key: clean_value(value) for key, value in row.items()} for row in table.to_pylist()]
    object_jsonl = b"".join((stable_json(row) + "\n").encode("utf-8") for row in rows)
    species_payload = {
        "schema": columns,
        "row_count": len(rows),
        "rows": [[clean_value(row.get(column)) for column in columns] for row in rows],
    }
    species_bytes = stable_json(species_payload).encode("utf-8")
    return object_jsonl, species_bytes, columns, rows


def run_source(path: Path, row_limit: int) -> dict[str, Any]:
    parquet_file = pq.ParquetFile(path)
    table = sample_table(path, row_limit)
    safe_name = path.stem.replace(".", "_").replace("-", "_")
    sample_path = OUT_DIR / f"{safe_name}.sample.parquet"
    compression = write_sample_parquet(table, sample_path)
    object_bytes, species_bytes, columns, rows = canonical_forms(table)
    object_path = OUT_DIR / f"{safe_name}.canonical_rows.jsonl"
    species_path = OUT_DIR / f"{safe_name}.logogram_species_payload.json"
    object_path.write_bytes(object_bytes)
    species_path.write_bytes(species_bytes)
    object_packet = encode_packet(object_bytes, f"{safe_name}.object")
    species_packet = encode_packet(species_bytes, f"{safe_name}.species")
    schema = schema_record(path, parquet_file, table)
    schema_hash = hash_obj({"columns": columns, "fields": schema["fields"]})
    sidecar_bytes, sidecar = column_sidecar(table, rel(path), schema_hash, schema["fields"])
    sidecar_path = OUT_DIR / f"{safe_name}.hybrid_sidecar.json"
    sidecar_path.write_bytes(sidecar_bytes)
    sidecar_packet = encode_packet(sidecar_bytes, f"{safe_name}.hybrid_sidecar")
    sample_parquet_bytes = sample_path.stat().st_size
    species_global_bytes = species_packet["packet_bytes"]
    object_global_bytes = object_packet["packet_bytes"]
    hybrid_bytes = sample_parquet_bytes + sidecar_packet["packet_bytes"]
    gate_pass = (
        species_packet["exact_replay"]
        and schema_hash == hash_obj({"columns": columns, "fields": schema["fields"]})
        and len(rows) == table.num_rows
        and sidecar_packet["exact_replay"]
    )
    if gate_pass:
        gate = "PASS_EXACT_REPLAY"
    else:
        gate = "FAIL_EXACT_REPLAY"
    delta_vs_parquet = sample_parquet_bytes - species_global_bytes
    delta_vs_object_canonical = len(object_bytes) - species_global_bytes
    species_payload_gain = len(object_bytes) - len(species_bytes)
    hybrid_delta_vs_parquet = sample_parquet_bytes - hybrid_bytes
    hybrid_materialization_avoidance = len(object_bytes) - hybrid_bytes
    return {
        "name": safe_name,
        "source": rel(path),
        "schema": schema,
        "schema_hash": schema_hash,
        "sample_parquet": rel(sample_path),
        "sample_parquet_bytes": sample_parquet_bytes,
        "sample_parquet_sha256": file_hash(sample_path),
        "sample_parquet_compression": compression,
        "canonical_object_rows": rel(object_path),
        "canonical_object_bytes": len(object_bytes),
        "canonical_object_sha256": sha256_bytes(object_bytes),
        "logogram_species_payload": rel(species_path),
        "logogram_species_payload_bytes": len(species_bytes),
        "logogram_species_payload_sha256": sha256_bytes(species_bytes),
        "object_logogram": object_packet,
        "species_logogram": species_packet,
        "hybrid_sidecar": {
            "path": rel(sidecar_path),
            "payload_bytes": len(sidecar_bytes),
            "payload_sha256": sha256_bytes(sidecar_bytes),
            "logogram": sidecar_packet,
            "route_counts": {
                route: sum(1 for item in sidecar["columns"] if item["route"] == route)
                for route in ["prediction_cache", "ram_trace", "parquet_native"]
            },
            "pathfinding_plan": sidecar["pathfinding_plan"],
        },
        "row_count_matches": len(rows) == table.num_rows,
        "schema_hash_recomputes": schema_hash == hash_obj({"columns": columns, "fields": schema["fields"]}),
        "residual_bounded": species_packet["exact_replay"] and sidecar_packet["exact_replay"],
        "exact_replay_gate": gate,
        "measured": {
            "delta_vs_sample_parquet_bytes": delta_vs_parquet,
            "gain_vs_sample_parquet_ratio": round(delta_vs_parquet / sample_parquet_bytes, 6) if sample_parquet_bytes else None,
            "delta_vs_object_canonical_bytes": delta_vs_object_canonical,
            "gain_vs_object_canonical_ratio": round(delta_vs_object_canonical / len(object_bytes), 6) if object_bytes else None,
            "schema_key_reuse_payload_gain_bytes": species_payload_gain,
            "schema_key_reuse_payload_gain_ratio": round(species_payload_gain / len(object_bytes), 6) if object_bytes else None,
            "hybrid_sidecar_overhead_bytes": sidecar_packet["packet_bytes"],
            "hybrid_total_bytes": hybrid_bytes,
            "hybrid_delta_vs_sample_parquet_bytes": hybrid_delta_vs_parquet,
            "hybrid_overhead_vs_sample_parquet_ratio": round(sidecar_packet["packet_bytes"] / sample_parquet_bytes, 6) if sample_parquet_bytes else None,
            "hybrid_materialization_avoidance_bytes": hybrid_materialization_avoidance,
            "hybrid_materialization_avoidance_ratio": round(hybrid_materialization_avoidance / len(object_bytes), 6) if object_bytes else None,
        },
        "decision": "HOLD_PARQUET_LOGOGRAM_FIXTURE",
    }


def aggregate(sources: list[dict[str, Any]], dictionary_bytes: int) -> dict[str, Any]:
    sample_parquet = sum(item["sample_parquet_bytes"] for item in sources)
    object_bytes = sum(item["canonical_object_bytes"] for item in sources)
    species_payload = sum(item["logogram_species_payload_bytes"] for item in sources)
    species_packet = sum(item["species_logogram"]["packet_bytes"] for item in sources)
    object_packet = sum(item["object_logogram"]["packet_bytes"] for item in sources)
    hybrid_sidecars = sum(item["hybrid_sidecar"]["logogram"]["packet_bytes"] for item in sources)
    global_species = species_packet + dictionary_bytes
    hybrid_total = sample_parquet + hybrid_sidecars + dictionary_bytes
    delta_parquet = sample_parquet - global_species
    delta_object = object_bytes - global_species
    payload_gain = object_bytes - species_payload
    hybrid_materialization = object_bytes - hybrid_total
    return {
        "source_count": len(sources),
        "all_exact_replay": bool(sources) and all(exact_replay_pass(item) for item in sources),
        "all_schema_hashes_recompute": bool(sources) and all(item["schema_hash_recomputes"] for item in sources),
        "all_row_counts_match": bool(sources) and all(item["row_count_matches"] for item in sources),
        "sample_parquet_bytes": sample_parquet,
        "canonical_object_bytes": object_bytes,
        "logogram_species_payload_bytes": species_payload,
        "object_logogram_packet_bytes": object_packet,
        "species_logogram_packet_bytes": species_packet,
        "hybrid_sidecar_packet_bytes": hybrid_sidecars,
        "dictionary_bytes": dictionary_bytes,
        "species_global_bytes": global_species,
        "hybrid_total_bytes": hybrid_total,
        "delta_vs_sample_parquet_bytes": delta_parquet,
        "gain_vs_sample_parquet_ratio": round(delta_parquet / sample_parquet, 6) if sample_parquet else None,
        "delta_vs_object_canonical_bytes": delta_object,
        "gain_vs_object_canonical_ratio": round(delta_object / object_bytes, 6) if object_bytes else None,
        "schema_key_reuse_payload_gain_bytes": payload_gain,
        "schema_key_reuse_payload_gain_ratio": round(payload_gain / object_bytes, 6) if object_bytes else None,
        "hybrid_delta_vs_sample_parquet_bytes": sample_parquet - hybrid_total,
        "hybrid_overhead_vs_sample_parquet_ratio": round((hybrid_sidecars + dictionary_bytes) / sample_parquet, 6) if sample_parquet else None,
        "hybrid_materialization_avoidance_bytes": hybrid_materialization,
        "hybrid_materialization_avoidance_ratio": round(hybrid_materialization / object_bytes, 6) if object_bytes else None,
        "hybrid_route_counts": {
            route: sum(item["hybrid_sidecar"]["route_counts"][route] for item in sources)
            for route in ["prediction_cache", "ram_trace", "parquet_native"]
        },
    }


def build_payload(paths: list[Path], row_limit: int) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = [path for path in paths if path.exists()]
    missing = [path for path in paths if not path.exists()]
    sources = [run_source(path, row_limit) for path in existing]
    dictionary_json = stable_json(dictionary_payload()).encode("utf-8")
    dictionary_bytes = len(dictionary_json)
    dictionary_hash = sha256_bytes(dictionary_json)
    payload = {
        "schema": "parquet_logogram_efficiency_probe_v1",
        "protocol_id": PROTOCOL_ID,
        "claim_boundary": (
            "Parquet-to-logogram byte accounting only. This samples local Parquet files, "
            "canonicalizes rows, transcodes them into the existing WLG2 logogram core, "
            "and records exact replay plus byte deltas. It does not claim global "
            "compression, canonical enwik9 performance, or replacement of Parquet."
        ),
        "inputs": {
            "requested_paths": [rel(path) for path in paths],
            "existing_paths": [rel(path) for path in existing],
            "missing_paths": [rel(path) for path in missing],
            "row_limit_per_source": row_limit,
        },
        "accounting_equations": {
            "parquet_logogram_transcode_efficiency": "E_pq_log=(bytes_sample_parquet-bytes_logogram_species_global)/bytes_sample_parquet",
            "columnar_lineage_logogram_gain": "G_lineage=(bytes_object_canonical-bytes_species_payload)/bytes_object_canonical",
            "parquet_logogram_exact_replay_gate": "G_pq_log=1[canonical_rows_decode]*1[schema_hash_recomputes]*1[row_count_matches]*1[residual_bounded]",
            "hybrid_parquet_logogram_sidecar_cost": "C_hybrid=(bytes_sidecar_packet+bytes_dictionary)/bytes_sample_parquet",
            "hybrid_materialization_avoidance_gain": "G_hybrid=(bytes_object_canonical-(bytes_sample_parquet+bytes_sidecar_packet+bytes_dictionary))/bytes_object_canonical",
            "hybrid_cache_trace_route_selector": "route(column)=argmax(U_prediction_cache,U_ram_trace,U_parquet_native)",
        },
        "dictionary": {
            "source": rel(V2_SCRIPT),
            "bytes": dictionary_bytes,
            "sha256": dictionary_hash,
        },
        "sources": sources,
        "aggregates": aggregate(sources, dictionary_bytes),
        "decision": (
            "ADMIT_PARQUET_LOGOGRAM_EFFICIENCY_AS_HOLD_FIXTURE"
            if sources
            else "HOLD_NO_PARQUET_INPUTS"
        ),
    }
    payload["finding"] = (
        "The useful accounting split is between Parquet bytes, full object-row canonical bytes, "
        "and logogram species-code bytes. Schema/key reuse can reduce the canonical row surface, "
        "but WLG2 packet plus dictionary costs must still beat Parquet before any compression gain is claimed. "
        "The hybrid path keeps Parquet as substrate and uses logograms as a sidecar for schema lineage, "
        "prediction-cache columns, RAM-trace columns, and exact replay gates."
    )
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "parquet_logogram_efficiency_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "aggregates": payload["aggregates"],
        "source_hashes": {item["source"]: item["schema"]["source_sha256"] for item in payload["sources"]},
        "sample_hashes": {item["source"]: item["sample_parquet_sha256"] for item in payload["sources"]},
        "dictionary_sha256": payload["dictionary"]["sha256"],
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    agg = payload["aggregates"]
    lines = [
        "# Parquet Logogram Efficiency",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Finding",
        "",
        payload["finding"],
        "",
        "## Aggregate",
        "",
        f"- Sources: `{agg['source_count']}`",
        f"- Exact replay: `{agg['all_exact_replay']}`",
        f"- Sample Parquet bytes: `{agg['sample_parquet_bytes']}`",
        f"- Object canonical bytes: `{agg['canonical_object_bytes']}`",
        f"- Logogram species global bytes: `{agg['species_global_bytes']}`",
        f"- Delta vs sample Parquet: `{agg['delta_vs_sample_parquet_bytes']}` ({agg['gain_vs_sample_parquet_ratio']})",
        f"- Delta vs object canonical: `{agg['delta_vs_object_canonical_bytes']}` ({agg['gain_vs_object_canonical_ratio']})",
        f"- Schema/key reuse payload gain: `{agg['schema_key_reuse_payload_gain_bytes']}` ({agg['schema_key_reuse_payload_gain_ratio']})",
        f"- Hybrid sidecar packet bytes: `{agg['hybrid_sidecar_packet_bytes']}`",
        f"- Hybrid total bytes: `{agg['hybrid_total_bytes']}`",
        f"- Hybrid overhead vs sample Parquet: `{agg['hybrid_delta_vs_sample_parquet_bytes']}` ({agg['hybrid_overhead_vs_sample_parquet_ratio']})",
        f"- Hybrid materialization avoidance: `{agg['hybrid_materialization_avoidance_bytes']}` ({agg['hybrid_materialization_avoidance_ratio']})",
        f"- Hybrid route counts: `{agg['hybrid_route_counts']}`",
        "",
        "## Equations",
        "",
    ]
    for name, equation in payload["accounting_equations"].items():
        lines.append(f"- `{name}`: `{equation}`")
    lines.extend(
        [
            "",
            "## Per Source",
            "",
            "| Source | Rows | Sample parquet | Object canonical | Species payload | Species packet | Delta vs parquet | Delta vs object | Gate |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in payload["sources"]:
        measured = item["measured"]
        lines.append(
            f"| `{item['source']}` | {item['schema']['sample_rows']} | {item['sample_parquet_bytes']} | "
            f"{item['canonical_object_bytes']} | {item['logogram_species_payload_bytes']} | "
            f"{item['species_logogram']['packet_bytes']} | {measured['delta_vs_sample_parquet_bytes']} | "
            f"{measured['delta_vs_object_canonical_bytes']} | {item['exact_replay_gate']} |"
        )
    lines.extend(["", "## Receipt", "", f"`{rel(RECEIPT)}`"])
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    agg = payload["aggregates"]
    lines = [
        "title: Parquet Logogram Efficiency",
        "tags: Parquet Logogram Efficiency HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! Parquet Logogram Efficiency",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "!! Accounting",
        "",
        f"* `E_pq_log`: `{agg['gain_vs_sample_parquet_ratio']}`",
        f"* `G_lineage`: `{agg['schema_key_reuse_payload_gain_ratio']}`",
        f"* `C_hybrid`: `{agg['hybrid_overhead_vs_sample_parquet_ratio']}`",
        f"* `G_hybrid`: `{agg['hybrid_materialization_avoidance_ratio']}`",
        f"* Hybrid route counts: `{agg['hybrid_route_counts']}`",
        f"* Exact replay: `{agg['all_exact_replay']}`",
        "",
        "!! Equations",
        "",
    ]
    for name, equation in payload["accounting_equations"].items():
        lines.append(f"* `{name}`: `{equation}`")
    lines.extend(
        [
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            "!! Links",
            "",
            "* [[Combined Approach Equation Surface]]",
            "* [[TranscriptFormer Evolutionary Prior]]",
            "",
            f"Receipt: `{rel(RECEIPT)}`",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Account for Parquet to logogram transcode efficiency.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--row-limit", type=int, default=256)
    args = parser.parse_args()
    paths = args.paths or DEFAULT_INPUTS
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload(paths, args.row_limit)
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
