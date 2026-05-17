#!/usr/bin/env python3
"""Ingest a local arXiv Kaggle/Croissant metadata descriptor.

This does not download the Kaggle archive or arXiv bulk data.  It records the
descriptor as a receipted source surface for later lawful ingestion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = Path("/home/allaun/Documents/ingest/arxiv-metadata.json")
DEFAULT_ARCHIVE = Path("/home/allaun/Documents/ingest/kaggledataset.zip")
OUT_DIR = REPO / "shared-data" / "data" / "math_research_databases"
PACKET = OUT_DIR / "arxiv_metadata_descriptor_packet.json"
RECEIPT = OUT_DIR / "arxiv_metadata_descriptor_receipt.json"
ARCHIVE_PACKET = OUT_DIR / "arxiv_kaggle_archive_packet.json"
ARCHIVE_SAMPLE_JSONL = OUT_DIR / "arxiv_kaggle_archive_sample.jsonl"
ARCHIVE_SAMPLE_CSV = OUT_DIR / "arxiv_kaggle_archive_sample.csv"
ARCHIVE_RECEIPT = OUT_DIR / "arxiv_kaggle_archive_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def dist_summary(obj: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in as_list(obj.get("distribution")):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "id": item.get("@id"),
                "type": item.get("@type"),
                "name": item.get("name"),
                "encoding_format": item.get("encodingFormat"),
                "content_url": item.get("contentUrl"),
                "content_size": item.get("contentSize"),
                "md5": item.get("md5"),
                "includes": item.get("includes"),
                "contained_in": item.get("containedIn", {}).get("@id")
                if isinstance(item.get("containedIn"), dict)
                else None,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--sample-records", type=int, default=25)
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    raw = source.read_bytes()
    obj = json.loads(raw)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    license_obj = obj.get("license") if isinstance(obj.get("license"), dict) else {}
    creator_obj = obj.get("creator") if isinstance(obj.get("creator"), dict) else {}
    publisher_obj = obj.get("publisher") if isinstance(obj.get("publisher"), dict) else {}
    catalog_obj = obj.get("includedInDataCatalog") if isinstance(obj.get("includedInDataCatalog"), dict) else {}

    packet = {
        "schema": "arxiv_metadata_descriptor_packet_v1",
        "rrc_shape_hint": "ArxivMetadataDescriptorSurface",
        "source_path": str(source),
        "source_size_bytes": len(raw),
        "source_sha256": sha256_bytes(raw),
        "dataset_name": obj.get("name"),
        "alternate_name": obj.get("alternateName"),
        "dataset_type": obj.get("@type"),
        "version": obj.get("version"),
        "date_published": obj.get("datePublished"),
        "date_modified": obj.get("dateModified"),
        "url": obj.get("url"),
        "identifier": obj.get("identifier"),
        "cite_as": obj.get("citeAs"),
        "conforms_to": obj.get("conformsTo"),
        "is_accessible_for_free": obj.get("isAccessibleForFree"),
        "license_name": license_obj.get("name"),
        "license_url": license_obj.get("url"),
        "creator": creator_obj.get("name"),
        "publisher": publisher_obj.get("name"),
        "data_catalog": catalog_obj.get("name"),
        "distribution": dist_summary(obj),
        "keywords": as_list(obj.get("keywords")),
        "expected_article_fields": [
            "id",
            "submitter",
            "authors",
            "title",
            "comments",
            "journal-ref",
            "doi",
            "abstract",
            "categories",
            "versions",
        ],
        "bulk_surfaces_declared_in_descriptor": [
            "kaggle_metadata_archive",
            "google_cloud_storage_pdf_bucket",
            "google_cloud_storage_source_bucket",
            "arxiv_abs_url_template",
            "arxiv_pdf_url_template",
        ],
        "density_markers": [
            "croissant_dataset_descriptor",
            "kaggle_metadata_snapshot",
            "arxiv_category_graph",
            "paper_version_history",
            "abstract_text_surface",
            "latex_source_archive_pointer",
            "pdf_bulk_archive_pointer",
            "knowledge_graph_construction_surface",
        ],
        "access_boundary": (
            "Descriptor-only ingest. Metadata license is recorded from the descriptor; "
            "individual papers and full-text/source downloads still follow arXiv/Kaggle/GCS terms."
        ),
        "decision": "HOLD",
        "claim_boundary": (
            "This receipt proves local descriptor capture and hashing only. It is not a "
            "receipt for the 1.617 GB metadata archive, the GCS bucket contents, PDFs, "
            "source tarballs, or theorem validity."
        ),
    }
    packet["packet_hash"] = sha256_text(stable_json(packet))
    PACKET.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "arxiv_metadata_descriptor_receipt_v1",
        "packet": str(PACKET.relative_to(REPO)),
        "source_path": packet["source_path"],
        "source_size_bytes": packet["source_size_bytes"],
        "source_sha256": packet["source_sha256"],
        "packet_hash": packet["packet_hash"],
        "dataset_name": packet["dataset_name"],
        "version": packet["version"],
        "distribution_count": len(packet["distribution"]),
        "density_marker_count": len(packet["density_markers"]),
        "decision": packet["decision"],
        "claim_boundary": packet["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    archive = Path(args.archive).expanduser().resolve()
    archive_receipt: dict[str, Any] | None = None
    if archive.exists():
        archive_hash = sha256_file(archive)
        sample_records: list[dict[str, Any]] = []
        with zipfile.ZipFile(archive) as zf:
            infos = zf.infolist()
            members = [
                {
                    "filename": info.filename,
                    "compress_size": info.compress_size,
                    "file_size": info.file_size,
                    "date_time": list(info.date_time),
                    "crc": info.CRC,
                }
                for info in infos
            ]
            json_members = [info for info in infos if info.filename.endswith(".json")]
            selected = json_members[0] if json_members else infos[0]
            with zf.open(selected) as handle:
                for _ in range(args.sample_records):
                    line = handle.readline()
                    if not line:
                        break
                    rec = json.loads(line)
                    sample = {
                        "id": rec.get("id"),
                        "title": rec.get("title"),
                        "authors": rec.get("authors"),
                        "categories": rec.get("categories"),
                        "versions": rec.get("versions"),
                        "doi": rec.get("doi"),
                        "journal_ref": rec.get("journal-ref"),
                        "abstract_sha256": sha256_text(text(rec.get("abstract")) or ""),
                        "abstract_bytes": len((text(rec.get("abstract")) or "").encode("utf-8")),
                    }
                    sample["packet_hash"] = sha256_text(stable_json(sample))
                    sample_records.append(sample)

        ARCHIVE_SAMPLE_JSONL.write_text(
            "\n".join(stable_json(record) for record in sample_records) + "\n", encoding="utf-8"
        )
        csv_lines = [
            "id,title,authors,categories,version_count,doi,journal_ref,abstract_sha256,packet_hash"
        ]
        for record in sample_records:
            csv_lines.append(
                ",".join(
                    [
                        json.dumps(record.get("id") or ""),
                        json.dumps(record.get("title") or ""),
                        json.dumps(record.get("authors") or ""),
                        json.dumps(record.get("categories") or ""),
                        json.dumps(len(record.get("versions") or [])),
                        json.dumps(record.get("doi") or ""),
                        json.dumps(record.get("journal_ref") or ""),
                        json.dumps(record["abstract_sha256"]),
                        json.dumps(record["packet_hash"]),
                    ]
                )
            )
        ARCHIVE_SAMPLE_CSV.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

        archive_packet = {
            "schema": "arxiv_kaggle_archive_packet_v1",
            "rrc_shape_hint": "ArxivKaggleMetadataSnapshot",
            "archive_path": str(archive),
            "archive_size_bytes": archive.stat().st_size,
            "archive_sha256": archive_hash,
            "zip_member_count": len(members),
            "zip_members": members,
            "sample_record_count": len(sample_records),
            "sample_records_jsonl": str(ARCHIVE_SAMPLE_JSONL.relative_to(REPO)),
            "sample_records_csv": str(ARCHIVE_SAMPLE_CSV.relative_to(REPO)),
            "sample_policy": (
                "Stream first records from the JSON member inside the zip without extracting "
                "the 5GB snapshot. Store hashes and routing fields only."
            ),
            "density_markers": [
                "kaggle_metadata_archive_verified",
                "arxiv_jsonl_snapshot",
                "category_graph_sample",
                "version_history_sample",
                "abstract_hash_sample",
            ],
            "decision": "HOLD",
            "claim_boundary": (
                "Archive hash and bounded sample verified. The full JSONL corpus is not "
                "materialized into the repo, and per-paper full text/PDF/source replay is not claimed."
            ),
        }
        archive_packet["packet_hash"] = sha256_text(stable_json(archive_packet))
        ARCHIVE_PACKET.write_text(
            json.dumps(archive_packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        archive_receipt = {
            "schema": "arxiv_kaggle_archive_receipt_v1",
            "packet": str(ARCHIVE_PACKET.relative_to(REPO)),
            "archive_path": archive_packet["archive_path"],
            "archive_size_bytes": archive_packet["archive_size_bytes"],
            "archive_sha256": archive_packet["archive_sha256"],
            "zip_member_count": archive_packet["zip_member_count"],
            "sample_record_count": archive_packet["sample_record_count"],
            "packet_hash": archive_packet["packet_hash"],
            "decision": archive_packet["decision"],
            "claim_boundary": archive_packet["claim_boundary"],
        }
        archive_receipt["receipt_hash"] = sha256_text(stable_json(archive_receipt))
        ARCHIVE_RECEIPT.write_text(
            json.dumps(archive_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    out = {"descriptor_receipt": receipt, "archive_receipt": archive_receipt}
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
