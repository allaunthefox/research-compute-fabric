#!/usr/bin/env python3
"""Build a deterministic outside-review packet with copied files and a manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


DEFAULT_PACKET = [
    "PLAIN_LANGUAGE_OVERVIEW.md",
    "README.md",
    "DERIVATION_SPEC.md",
    "TERNARY_VM_SPEC.md",
    "AUDITABILITY_IP_BOUNDARY.md",
]


DEFAULT_REVIEW_QUESTIONS = [
    "Is the current technical claim legible?",
    "Is the current audit surface strong enough for the claim being made?",
    "Are there obvious cheating paths not yet closed?",
    "Are there obvious wording or trust problems that would confuse a careful reader?",
    "What is the next smallest artifact that would materially improve review?",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root used to resolve packet files. Defaults to the current directory.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Directory where the review packet should be created.",
    )
    parser.add_argument(
        "--label",
        default="default_review_packet",
        help="Short label for the packet manifest. Defaults to default_review_packet.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Extra relative file path to include in addition to the default packet.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    packet_files: list[str] = []
    for rel in DEFAULT_PACKET + args.include:
        if rel not in packet_files:
            packet_files.append(rel)

    copied = []
    packet_dir = out_dir / "packet"
    packet_dir.mkdir(parents=True, exist_ok=True)

    for rel in packet_files:
        source = root / rel
        if not source.is_file():
            raise FileNotFoundError(f"Packet source missing: {source}")
        destination = packet_dir / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(
            {
                "path": rel,
                "sha256": sha256_file(destination),
            }
        )

    packet_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "label": args.label,
                "packet_files": copied,
                "default_review_questions": DEFAULT_REVIEW_QUESTIONS,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    manifest = {
        "schema": "hutter_review_packet_manifest_v1",
        "label": args.label,
        "packet_dir_name": packet_dir.name,
        "packet_files": copied,
        "default_review_questions": DEFAULT_REVIEW_QUESTIONS,
        "packet_fingerprint": packet_fingerprint,
    }
    manifest_path = out_dir / "review_packet.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
